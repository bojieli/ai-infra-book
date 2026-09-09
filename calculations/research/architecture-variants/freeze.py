"""Generate standalone examples and bind the public dependencies read-only."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODULE = HERE / "src/infra_calc/topics/architecture_variants.py"
spec = importlib.util.spec_from_file_location("candidate", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
scenarios = [dict(id="architecture-decode"),
             dict(id="architecture-prefill", tokens=8192, history=0),
             dict(id="architecture-prefix", tokens=2048, history=6144),
             dict(id="architecture-single-device", tp=1)]
(HERE / "results").mkdir(exist_ok=True)
for row in scenarios:
    result = m.calculate(**{k: v for k, v in row.items() if k != "id"})
    (HERE / "results" / (row["id"] + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
(HERE / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n")
bindings = []
for relative in ["calculations/configs/models/qwen3-8b/config.json",
                 "calculations/src/infra_calc/models/qwen3.py",
                 "calculations/src/infra_calc/schema.py", "calculations/src/infra_calc/units.py"]:
    p = ROOT / relative
    bindings.append(dict(file=relative, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
summary = [{"name": r["name"], "parameters": r["actual_parameters"],
            "delta_parameters": r["parameter_delta"],
            **{k: r["work"][k] for k in ["matrix_flops", "kv_bytes_per_token_per_request",
                "per_rank_live_budget_bytes", "per_rank_ring_wire_bytes_exact", "sequential_decoder_layers"]}}
           for r in m.calculate()["variants"]]
(HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(HERE / "integration.json").write_text(json.dumps(dict(
    new_file="src/infra_calc/topics/architecture_variants.py",
    dependencies=bindings, source_records=m.provenance(m.MODEL),
    scope="Independent candidate only. No shared CLI/config/reproduce changes.",
    test_command="python -m unittest discover -s calculations/research/architecture-variants/tests -v",
    tests=7, scenarios=4), ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, indent=2))
