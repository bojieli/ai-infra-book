"""Independent fixed-dimension per-tensor local storage and cohort bounds."""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = ROOT / "research/dense-quantized-placement/dense_quantized_placement.py"
spec = importlib.util.spec_from_file_location("densequant_review", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
DIMS = {
    "qwen3-8b": (4096, 12288, 36, 32, 8, 128, 151936, True),
    "qwen3-32b": (5120, 25600, 64, 64, 8, 128, 151936, True),
    "deepseek-r1-distill-llama-70b": (8192, 28672, 80, 64, 8, 128, 128256, False),
}
checks = []
for model, (h, f, l, q, k, d, v, hn) in DIMS.items():
    for tp, pp, dp in [(8, 1, 1), (2, 4, 1), (1, 8, 1), (16, 1, 1), (2, 2, 2)]:
        for group in [128, 1000, 32768]:
            r = m.calculate(model, tp=tp, pp=pp, dp=dp, group_size=group)
            for rank in r["ranks"]:
                stage = rank["stage"]
                count = l // pp + (stage < l % pp)
                qh = q // tp
                kh = max(1, k // tp)
                shapes = {
                    "self_attn.q_proj": (qh * d, h),
                    "self_attn.k_proj": (kh * d, h),
                    "self_attn.v_proj": (kh * d, h),
                    "self_attn.o_proj": (h, qh * d),
                    "mlp.gate_proj": (f // tp, h),
                    "mlp.up_proj": (f // tp, h),
                    "mlp.down_proj": (h, f // tp),
                    "input_layernorm": (h,),
                    "post_attention_layernorm": (h,),
                }
                if hn:
                    shapes.update({"self_attn.q_norm": (d,), "self_attn.k_norm": (d,)})
                expected = {
                    "model.layers.{layer}." + name + ".weight": (shape, count)
                    for name, shape in shapes.items()
                }
                if stage == 0:
                    expected["model.embed_tokens.weight"] = ((v // tp, h), 1)
                if stage == pp - 1:
                    expected.update(
                        {
                            "lm_head.weight": ((v // tp, h), 1),
                            "model.norm.weight": ((h,), 1),
                        }
                    )
                assert set(expected) == {w["name"] for w in rank["weights"]}
                for w in rank["weights"]:
                    shape, copies = expected[w["name"]]
                    assert tuple(w["shape"]) == shape and w["copies"] == copies
                    kept = len(shape) == 1 or w["name"] in (
                        "model.embed_tokens.weight",
                        "lm_head.weight",
                    )
                    assert w["low_bit_eligible"] == (not kept)
                    for fmt in w["storage"]:
                        if kept or fmt["bits"] == 16:
                            elements = shape[0] * (shape[1] if len(shape) == 2 else 1)
                            payload = 2 * elements * copies
                            metadata = 0
                        else:
                            rows, width = shape
                            payload = rows * ((width * fmt["bits"] + 7) // 8) * copies
                            metadata = rows * len(range(0, width, group)) * 2 * copies
                        assert (payload, metadata) == (
                            fmt["payload_bytes"],
                            fmt["scale_bytes"],
                        )
                assert set(rank["kv_head_ids"]) == {
                    head // (q // k) for head in rank["query_head_ids"]
                }
                kv = count * kh * d * 8192 * 4
                for fmt in rank["formats"]:
                    assert fmt["kv_bytes_per_request"] == kv
                    assert fmt["maximum_requests"] == max(
                        0, (24 * 10**9 - 2 * 2**30 - fmt["weight_bytes"]) // kv
                    )
            for i in range(3):
                cohort = []
                for rep in range(dp):
                    cohort.append(
                        min(
                            rank["formats"][i]["maximum_requests"]
                            for rank in r["ranks"]
                            if rank["replica"] == rep
                        )
                    )
                assert r["summary"][i]["maximum_global_requests"] == sum(cohort)
                assert len(set(cohort)) == 1
            checks.append(
                dict(
                    model=model, tp=tp, pp=pp, dp=dp, group=group, ranks=len(r["ranks"])
                )
            )
    # Uneven PP3 creates a genuine worst-stage budget in Qwen8/70.
    r = m.calculate(model, tp=1, pp=3, dp=2)
    threshold = max(
        rank["formats"][2]["weight_bytes"]
        + 2 * 2**30
        + rank["formats"][2]["kv_bytes_per_request"]
        for rank in r["ranks"]
    )
    for cap, expected_total in [(threshold - 1, 0), (threshold, 2), (threshold + 1, 2)]:
        a = m.calculate(model, tp=1, pp=3, dp=2, capacity_bytes=cap)
        assert a["summary"][2]["maximum_global_requests"] == expected_total
# Qwen8 TP8 down's localK1536/group1000=>2 groups, versus
# global K12288 ceil13 divided8=>1.625, which is not a local group count.
r = m.calculate("qwen3-8b", tp=8, group_size=1000)
down = next(
    w for w in r["ranks"][0]["weights"] if w["name"].endswith("mlp.down_proj.weight")
)
assert down["shape"] == [4096, 1536]
assert down["storage"][2]["groups"] == 36 * 4096 * 2
# Public packing row rounding counterexample independent of all even model widths.
assert m.packed_matrix((3, 5), 4, 4, 2) == dict(
    packed_bytes=9, scale_bytes=12, groups=6
)
assert "local K" in m.markdown(r)
(HERE / "dense_quantized_placement.snapshot.py").write_bytes(source.read_bytes())
(HERE / "results.json").write_text(
    json.dumps(
        dict(
            candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            topology_group_model_checks=len(checks),
            checks=checks,
            pp_worst_rank_dp_boundary_checks=9,
            localK_tail_and_odd_row_counterexamples=True,
        ),
        indent=2,
    )
    + "\n"
)
print("45model/topology/group cases and9 worst-rank DP boundaries passed")
