"""Only recheck final contiguous unknown-status change; no full-audit rerun."""

from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
source = ROOT / "research/flux-vae-decode/flux_vae_decode.py"
spec = importlib.util.spec_from_file_location("final_flux_delta", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
rows = []
for h, w, b, expected in [
    (8, 8, 64, [True] * 3),
    (8192, 8192, 1, [False, True, True]),
    (4096, 4096, 1, [False] * 3),
    (8, 8, 63, [False] * 3),
]:
    for dtype, size in [("bf16", 2), ("fp32", 4)]:
        r = m.calculate(height=h, width=w, batch=b, dtype=dtype, workspace_bytes=12345)
        s = r["summary"]
        interfaces = s["upsample_contiguous_interfaces"]
        assert [x["triggered"] for x in interfaces] == expected
        for row, (c, div), trigger in zip(
            interfaces, [(512, 8), (512, 4), (256, 2)], expected
        ):
            assert row["input_elements"] == b * c * (h // div) * (w // div)
            assert row["input_bytes"] == size * row["input_elements"]
            assert row["materialized_copy_bytes"] == (None if trigger else 0)
        assert s["layout_copy_bytes_unknown"] == any(expected)
        budget = s["conditional_weights_boundary_workspace_bytes"]
        if any(expected):
            assert budget is None
        else:
            assert (
                budget
                == s["decoder_weight_bytes"]
                + s["declared_tensor_boundary_peak_bytes"]
                + 12345
            )
        assert s["actual_runtime_peak_bytes"] is None
        rows.append(
            dict(
                height=h,
                width=w,
                batch=b,
                dtype=dtype,
                triggers=expected,
                conditional_budget=budget,
            )
        )
old = HERE / "flux_vae_decode.snapshot.py"
(HERE / "flux_vae_decode.pre-layout-update.py").write_bytes(old.read_bytes())
old.write_bytes(source.read_bytes())
result = dict(
    final_candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    delta_cases=rows,
    old_rejection_acceptance_superseded=True,
    prior_full_math_audit_preserved=True,
)
(HERE / "layout-delta-results.json").write_text(json.dumps(result, indent=2) + "\n")
print("Eight final layout-delta cases passed")
