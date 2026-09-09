"""Validate candidate in memory; preserve all public files."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from infra_calc.topics import dense_placement as old

spec = importlib.util.spec_from_file_location(
    "infra_calc.topics.dense_placement",
    HERE / "src/infra_calc/topics/dense_placement.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for args in [dict(), dict(tp=4, pp=2), dict(tp=16, dp=2), dict(tp=1, pp=3)]:
    assert old.calculate(**args) == module.calculate(**args)
sys.modules[spec.name] = module
import infra_calc.topics

infra_calc.topics.dense_placement = module
suite = unittest.defaultTestLoader.discover(str(HERE / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
model = "deepseek-r1-distill-llama-70b"
scenarios = []
summary = []
(HERE / "results").mkdir(exist_ok=True)
for name, tp, pp, dp in [
    ("tp8", 8, 1, 1),
    ("tp4-pp2", 4, 2, 1),
    ("tp2-pp4", 2, 4, 1),
    ("pp8", 1, 8, 1),
    ("tp4-dp2", 4, 1, 2),
    ("tp16-kv-replica", 16, 1, 1),
]:
    inputs = dict(model=model, tp=tp, pp=pp, dp=dp)
    r = module.calculate(**inputs)
    (HERE / "results" / f"{name}.json").write_text(json.dumps(r, indent=2) + "\n")
    scenarios.append(dict(id="llama70-placement-" + name, inputs=inputs))
    summary.append(dict(id=name, **r["summary"]))
(HERE / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n")
(HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
from infra_calc import cli

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cli.main(["dense-placement", "--model", model, "--format", "md"])
(HERE / "cli-example.md").write_text(buf.getvalue())
files = ["src/infra_calc/topics/dense_placement.py", "tests/test_llama70_placement.py"]
guards = [
    dict(
        file=f,
        before_sha256=hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
        if (ROOT / f).exists()
        else None,
        candidate_sha256=hashlib.sha256((HERE / f).read_bytes()).hexdigest(),
    )
    for f in files
]
(HERE / "merge-guards.json").write_text(json.dumps(guards, indent=2) + "\n")
(HERE / "validation.json").write_text(
    json.dumps(
        dict(
            tests_passed=result.testsRun,
            qwen_complete_equivalence_scenarios=4,
            llama_scenarios=6,
            cli_report_pass=True,
            shared_modified=False,
        ),
        indent=2,
    )
    + "\n"
)
print(json.dumps(summary, indent=2))
