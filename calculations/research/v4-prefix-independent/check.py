"""Independent source-branch, allocation, finite sum and full-forward checks."""

from collections import Counter
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = (
    ROOT
    / "research/v4-prefix-continuation/src/infra_calc/topics/v4_prefix_continuation.py"
)
spec = importlib.util.spec_from_file_location("prefix_independent", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from infra_calc.topics import v4_forward
from infra_calc.sources import model_config


def floor_prefix(n, r):
    q, s = divmod(n, r)
    return r * q * (q - 1) // 2 + q * (s + 1)


def capped_floor_sum(lo, hi, r, cap):
    cutoff = min(hi, r * cap - 1)
    before = 0 if cutoff < lo else floor_prefix(cutoff, r) - floor_prefix(lo - 1, r)
    return before + max(0, hi - max(lo, r * cap) + 1) * cap


short = []
for model in ["deepseek-v4-flash", "deepseek-v4-pro"]:
    r = m.calculate(model, prefix_tokens=126, new_tokens=3, batch=2)
    totals = Counter()
    for step in r["steps"]:
        direct = v4_forward.calculate(
            model, batch=2, tokens=1, history=step["input_position"]
        )["summary"]
        for key in [
            "matrix_flops_effective_attention",
            "matrix_flops_with_reference_sparse_and_expert_tiles",
            "accounted_scalar_flops",
        ]:
            assert step[key] == direct[key]
            totals[key] += direct[key]
        assert Counter(step["accounted_special_ops"]) == Counter(
            direct["accounted_special_ops"]
        )
    for key, value in totals.items():
        assert r["summary"][key] == value
    short.append(dict(model=model, calls=3, public_forward_match=True))
r = m.calculate()
c = model_config("deepseek-v4-flash", reference=True)
lo, hi = 6145, 8192
n = 2048
ratios = Counter(c["compress_ratios"][: c["n_layers"]])
selected_sum = 0
index_sum = 0
for ratio, layers in ratios.items():
    window = n * c["window_size"]
    compressed = (
        0
        if ratio == 0
        else (
            capped_floor_sum(lo, hi, 4, c["index_topk"])
            if ratio == 4
            else floor_prefix(hi, ratio) - floor_prefix(lo - 1, ratio)
        )
    )
    selected_sum += layers * (window + compressed)
    if ratio == 4:
        index_sum += layers * (floor_prefix(hi, 4) - floor_prefix(lo - 1, 4))
attention = 4 * c["n_heads"] * c["head_dim"] * selected_sum
index = 2 * c["index_n_heads"] * c["index_head_dim"] * index_sum
projection = r["static_base_forward"]["components"]["attention"]["summary"][
    "projection_matrix_flops"
]
expected = (
    n * (r["static_partition"]["matrix_flops_per_call"] + projection)
    + attention
    + index
)
assert expected == r["summary"]["matrix_flops_effective_attention"]
head_per_step = 2 * c["dim"] * c["vocab_size"]
assert r["summary"]["vocabulary_head_matrix_flops"] == n * head_per_step
assert (
    r["summary"]["vocabulary_head_calls"] == 2048
    and r["summary"]["discarded_intermediate_vocabulary_heads"] == 2047
)
for ratio in [4, 128]:
    expected_count = hi // ratio - (lo - 1) // ratio
    assert len(r["compression_boundaries"][str(ratio)]) == expected_count
    assert r["compression_boundaries"][str(ratio)][0] == ((lo - 1) // ratio + 1) * ratio
    assert r["compression_boundaries"][str(ratio)][-1] == 8192
# Reconstruct source buffer shapes, including full window allocation even when
# maxseq is shorter than its window. No state helper used for this oracle.
allocations = []
for length, bmax in [(129, 4), (8192, 1), (8193, 4)]:
    a = m.calculate(
        prefix_tokens=127,
        new_tokens=2,
        batch=1,
        allocated_max_seq_len=length,
        allocated_max_batch_size=bmax,
    )
    size = 0
    for ratio in c["compress_ratios"][: c["n_layers"]]:
        size += (
            bmax
            * (c["window_size"] + (length // ratio if ratio else 0))
            * c["head_dim"]
            * 2
        )
        if ratio:
            coff = 2 if ratio == 4 else 1
            size += 2 * bmax * (coff * ratio) * (coff * c["head_dim"]) * 4
            if ratio == 4:
                size += bmax * (length // ratio) * c["index_head_dim"] * 2
                size += 2 * bmax * (coff * ratio) * (coff * c["index_head_dim"]) * 4
    assert (
        size == a["source_cache_allocation"]["bf16_history_and_fp32_compressor_bytes"]
    )
    allocations.append(dict(max_seq_len=length, max_batch_size=bmax, bytes=size))
for kwargs in [
    dict(allocated_max_seq_len=8191),
    dict(batch=2, allocated_max_batch_size=1),
    dict(prefix_tokens=0),
    dict(new_tokens=True),
]:
    try:
        m.calculate(**kwargs)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected scope rejection")
(HERE / "v4_prefix_continuation.snapshot.py").write_bytes(source.read_bytes())
(HERE / "results.json").write_text(
    json.dumps(
        dict(
            candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            short_public_forward_checks=short,
            book_closed_form_matrix_flops=expected,
            compression_counts={"4": 512, "128": 16},
            head_calls=2048,
            allocations=allocations,
        ),
        indent=2,
    )
    + "\n"
)
print("6 direct full-forward steps,2048 closed-form sum and3 allocation oracles passed")
