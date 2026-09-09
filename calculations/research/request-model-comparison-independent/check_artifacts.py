"""Inspect frozen artifacts and direct source allocation/last-head formulas."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from infra_calc.sources import model_config

checks = []
for path in sorted((ROOT / "research/request-model-comparison/results").glob("*.json")):
    result = json.loads(path.read_text())
    geometry = result["contract"]
    for row in result["comparisons"]:
        model = row["model"]
        s, p, g, b = (geometry[key] for key in ("S", "P", "G", "B"))
        assert geometry["final_retained_positions"] == s + p + g - 1
        assert row["decode"]["calls"] == g - 1
        for key in ("matrix_flops", "accounted_scalar_flops"):
            assert row["summary"][key] == row["prefill"]["totals"][key] + row["decode"]["totals"][key]
        for key in ("special_ops", "known_interfaces"):
            a = Counter(row["prefill"]["totals"][key]);a.update(row["decode"]["totals"][key])
            assert a == Counter(row["summary"][key])
        config = model_config(model, reference=model.startswith("deepseek-v4"))
        if model.startswith("deepseek-v4"):
            # Actual registered buffers: window plus compressed cache, optional
            # index cache, and the two FP32 compressor slots for each branch.
            end = s + p + g - 1
            expected = 0
            for ratio in config["compress_ratios"][:config["n_layers"]]:
                expected += 2 * b * config["head_dim"] * (config["window_size"] + (end // ratio if ratio else 0))
                if ratio:
                    coff = 2 if ratio == 4 else 1
                    expected += 2 * b * coff * ratio * coff * config["head_dim"] * 4
                if ratio == 4:
                    expected += 2 * b * (end // 4) * config["index_head_dim"]
                    expected += 2 * b * 2 * 4 * 2 * config["index_head_dim"] * 4
            assert row["source_cache_allocation"]["bf16_cache_and_fp32_compressor_bytes"] == expected
            ledger = row["prefill"]["source_ledger"]
            head = 2 * b * config["dim"] * config["vocab_size"]
            if s:
                assert ledger["summary"]["vocabulary_head_matrix_flops"] == p * head
                assert ledger["summary"]["discarded_intermediate_vocabulary_heads"] == p - 1
            else:
                assert ledger["summary"]["vocabulary_head_matrix_flops"] == head
        elif model == "kimi-k3":
            c = config["text_config"]
            assert row["prefill"]["source_ledger"]["summary"]["vocabulary_head_matrix_flops"] == 2 * b * c["hidden_size"] * c["vocab_size"]
            assert row["source_coverage"]["config_checkpoint_shape_match"] is False
        else:
            op = next(op for op in row["prefill"]["source_ledger"]["operators"] if op["name"] == "lm_head")
            assert op["matrix_flops"] * op["repeats"] == 2 * b * config["hidden_size"] * config["vocab_size"]
        for field in ("complete_hbm_traffic_bytes", "complete_runtime_peak_bytes", "complete_scalar_flops", "predicted_latency_seconds", "quality_equivalence"):
            assert row["summary"][field] is None
        checks.append(f"{path.name}: {model}: source allocations/heads/counters/unknowns")
(Path(__file__).resolve().parent / "artifact-results.json").write_text(json.dumps(dict(checks=checks, count=len(checks)), indent=2) + "\n")
print(f"PASS {len(checks)} model-artifact groups")
