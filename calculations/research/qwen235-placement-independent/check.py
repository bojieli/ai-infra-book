"""Independent per-rank storage/metadata and replicated-cohort conservation."""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = ROOT / "research/qwen235-placement/qwen235_placement.py"
spec = importlib.util.spec_from_file_location("qwen235_candidate", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
H, F, L, Q, K, D, E, V = 4096, 1536, 94, 64, 4, 128, 128, 151936
# 64Q heads =>8192 projection width, distinct from4096 hidden.
ATTN = L * (2 * H * Q * D + 2 * H * K * D)
EXPERT = L * E * 3 * H * F
NORMS = L * (2 * H + 2 * D) + H
ROUTER = L * E * H
VOCAB = 2 * V * H
assert ATTN + EXPERT + NORMS + ROUTER + VOCAB == 235093634560


def local_expected(rank, tp, ep, bits, group, scale):
    lo, hi = rank["layer_range"]
    n = hi - lo
    kheads = max(1, K // tp)
    matrices = [(Q // tp * D, H), (kheads * D, H), (kheads * D, H), (H, Q // tp * D)]
    matrices += [(F // tp, H), (F // tp, H), (H, F // tp)] * (E // ep)
    kept = n * (2 * H + 2 * D + E * H)
    if lo == 0:
        kept += V // tp * H
    if hi == L:
        kept += V // tp * H + H
    payload = 2 * kept
    metadata = 0
    for rows, k in matrices:
        payload += n * rows * ((k * bits + 7) // 8)
        if bits < 16:
            metadata += n * rows * len(range(0, k, group)) * scale
    return payload, metadata


index = json.loads(
    (ROOT / "sources/qwen3-235b-a22b/model.safetensors.index.json").read_text()
)
names = {"model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"}
for layer in range(94):
    prefix = f"model.layers.{layer}."
    names.update(
        prefix + x + ".weight"
        for x in [
            "self_attn.q_proj",
            "self_attn.k_proj",
            "self_attn.v_proj",
            "self_attn.o_proj",
            "self_attn.q_norm",
            "self_attn.k_norm",
            "input_layernorm",
            "post_attention_layernorm",
            "mlp.gate",
        ]
    )
    for expert in range(128):
        names.update(
            prefix + f"mlp.experts.{expert}." + x + ".weight"
            for x in ["gate_proj", "up_proj", "down_proj"]
        )
assert names == set(index["weight_map"]) and len(names) == 36945
assert index["metadata"]["total_size"] == 2 * (ATTN + EXPERT + NORMS + ROUTER + VOCAB)
checks = []
for tp, ep, pp in [(2, 4, 1), (4, 2, 1), (2, 2, 2), (1, 1, 8), (8, 1, 1), (1, 8, 1)]:
    for group in [128, 1000]:
        r = m.calculate(tp=tp, ep=ep, pp=pp, group_size=group)
        total16 = 0
        for rank in r["ranks"]:
            qlo, qhi = rank["q_head_range"]
            klo, khi = rank["kv_head_range"]
            assert set(range(klo, khi)) == {
                head // (Q // K) for head in range(qlo, qhi)
            }
            n = rank["layer_range"][1] - rank["layer_range"][0]
            for fmt in rank["formats"]:
                p, s = local_expected(rank, tp, ep, fmt["bits"], group, 2)
                assert (p, s) == (fmt["payload_bytes"], fmt["scale_bytes"])
                assert fmt["kv_bytes_per_request"] == n * (khi - klo) * 128 * 8192 * 4
                assert fmt["maximum_requests"] == max(
                    0, (80 * 10**9 - p - s - 2 * 2**30) // fmt["kv_bytes_per_request"]
                )
            total16 += rank["formats"][0]["weight_bytes"]
        ratio = max(1, tp // K)
        replicated = 2 * (
            EXPERT
            + ep * (ATTN + VOCAB)
            + ep * (ratio - 1) * L * 2 * H * K * D
            + tp * ep * (NORMS + ROUTER)
        )
        assert total16 == replicated
        for i in range(3):
            assert r["cohort"][i]["maximum_requests"] == min(
                rank["formats"][i]["maximum_requests"] for rank in r["ranks"]
            )
        checks.append(
            dict(tp=tp, ep=ep, pp=pp, group=group, physical_bf16_bytes=total16)
        )
# A localK192 down shard atTP8/group128 has2scales per output row;
# dividing the original K1536's12 groups by8 would give a wrong1.5groups.
r = m.calculate(tp=8, ep=1, group_size=128)
down = next(
    t
    for t in r["ranks"][0]["tensors"]
    if t["name"].endswith("experts.0.down_proj.weight")
)
assert down["local_shape"] == [4096, 192]
assert down["storage"][2]["groups"] == 94 * 4096 * 2
# Worst-rank exact one-request budget; PP8 uneven12/11layers+endpoints.
r = m.calculate(tp=1, ep=1, pp=8)
base = max(
    rank["formats"][2]["weight_bytes"]
    + 2 * 2**30
    + rank["formats"][2]["kv_bytes_per_request"]
    for rank in r["ranks"]
)
for budget, expected in [(base - 1, 0), (base, 1), (base + 1, 1)]:
    out = m.calculate(tp=1, ep=1, pp=8, capacity_bytes=budget)
    assert out["cohort"][2]["maximum_requests"] == expected
(HERE / "qwen235_placement.snapshot.py").write_bytes(source.read_bytes())
(HERE / "results.json").write_text(
    json.dumps(
        dict(
            candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            topology_group_checks=checks,
            local_tail_group_counterexample_pass=True,
            worst_rank_boundary_bytes=base,
            unique_parameters=235093634560,
        ),
        indent=2,
    )
    + "\n"
)
print("12 topology/group cases,96 ranks×3formats,exact worst-rank boundaries passed")
