"""Read-only candidate overlay; executes portable public tests and frozen replay."""

import ast
import hashlib
import json
from pathlib import Path
import platform
import sys
import unittest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "calculations/src"))
import infra_calc.topics

infra_calc.topics.__path__.insert(0, str(BASE / "src/infra_calc/topics"))
from infra_calc.topics import v4_hc_training, v4_training_primitives


def calculate_ast(path):
    tree = ast.parse(path.read_text())
    return ast.dump(
        next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "calculate"
        ),
        include_attributes=False,
    )


def main():
    suite = unittest.defaultTestLoader.discover(str(BASE / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(
            "Numeric acceptance requires actual execution: failure or skip present"
        )
    modules = {
        "v4-training-primitives": v4_training_primitives,
        "v4-hc-training": v4_hc_training,
    }
    old = {
        "v4-training-primitives": ROOT
        / "calculations/research/v4-training-reference/src/infra_calc/topics/v4_training_primitives.py",
        "v4-hc-training": BASE.parent / "src/v4_hc_training.py",
    }
    scenarios = json.loads((BASE / "book.append.json").read_text())
    output = BASE / "results"
    output.mkdir(exist_ok=True)
    comparisons = []
    for topic, module in modules.items():
        assert calculate_ast(Path(module.__file__)) == calculate_ast(old[topic])
        old_results = (
            ROOT / "calculations/research/v4-training-reference/results"
            if topic == "v4-training-primitives"
            else BASE.parent / "results"
        )
        for scene, filename in zip(
            scenarios[topic],
            [
                "one-row",
                "128-tokens" if topic == "v4-training-primitives" else "default",
                "batch2",
            ],
        ):
            args = {k: v for k, v in scene.items() if k != "id"}
            calculated = module.calculate(**args)
            assert module.calculate(**calculated["scenario"]) == calculated
            assert calculated == json.loads(
                (old_results / (filename + ".json")).read_text()
            )
            report = module.markdown(calculated)
            leaves = list(v4_training_primitives._complete_fields(calculated))
            assert all(leaf in report for leaf in leaves)
            (output / (scene["id"] + ".json")).write_text(
                json.dumps(calculated, indent=2, ensure_ascii=False, allow_nan=False)
                + "\n"
            )
            (output / (scene["id"] + ".md")).write_text(report)
            comparisons.append(
                dict(
                    id=scene["id"],
                    exact_frozen_result=True,
                    scenario_replay=True,
                    all_recorded_fields_in_report=True,
                )
            )
    sources = json.loads((BASE / "sources.lock.subset.json").read_text())["sources"]
    for source in sources:
        data = (ROOT / "calculations" / source["file"]).read_bytes()
        assert len(data) == source["bytes"]
        assert hashlib.sha256(data).hexdigest() == source["sha256"]
    import torch

    files = [
        p
        for p in BASE.rglob("*")
        if p.is_file()
        and p.suffix in (".py", ".json", ".md")
        and p.name != "bindings.json"
    ]
    bind = lambda p: dict(
        file=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()
    )
    dependencies = [
        ROOT / "calculations/src/infra_calc" / name
        for name in ("sources.py", "units.py", "paths.py")
    ] + list(old.values())
    binding = dict(
        tests_passed=result.testsRun,
        tests_skipped=len(result.skipped),
        runtime=dict(
            executable=sys.executable,
            python=platform.python_version(),
            torch=torch.__version__,
        ),
        frozen_calculate_ast_equal=True,
        comparisons=comparisons,
        source_records_verified=len(sources),
        artifacts=[bind(p) for p in sorted(files)],
        dependencies=[bind(p) for p in dependencies],
    )
    (BASE / "bindings.json").write_text(json.dumps(binding, indent=2) + "\n")


if __name__ == "__main__":
    main()
