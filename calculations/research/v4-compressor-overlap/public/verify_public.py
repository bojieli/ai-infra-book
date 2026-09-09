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
infra_calc.topics.__path__.insert(
    0, str(BASE.parents[1] / "v4-attention-projections/public/src/infra_calc/topics")
)
from infra_calc.topics import v4_compressor_overlap as module


def main():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.discover(str(BASE / "tests"))
    )
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit("Numerical acceptance requires all tests to execute")
    scenes = json.loads((BASE / "book.append.json").read_text())
    output = BASE / "results"
    output.mkdir(exist_ok=True)
    comparisons = []
    source_files = set()
    for scene in scenes:
        result_data = module.calculate(**{k: v for k, v in scene.items() if k != "id"})
        assert module.calculate(**result_data["scenario"]) == result_data
        source_files.update(r["file"] for r in result_data["sources"])
        report = module.markdown(result_data)
        assert "unknown (null)" in report
        (output / (scene["id"] + ".json")).write_text(
            json.dumps(result_data, indent=2, ensure_ascii=False, allow_nan=False)
            + "\n"
        )
        (output / (scene["id"] + ".md")).write_text(report)
        comparisons.append(dict(id=scene["id"], replay_equal=True))
    public_lock = json.loads(
        (ROOT / "calculations/configs/sources.lock.json").read_text()
    )["sources"]
    subset = [r for r in public_lock if r["file"] in source_files]
    for source in subset:
        data = (ROOT / "calculations" / source["file"]).read_bytes()
        assert (
            len(data) == source["bytes"]
            and hashlib.sha256(data).hexdigest() == source["sha256"]
        )
    (BASE / "sources.lock.subset.json").write_text(
        json.dumps(
            {"description": "Existing records, not an append patch", "sources": subset},
            indent=2,
        )
        + "\n"
    )
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
    deps = [
        ROOT / "calculations/src/infra_calc" / n
        for n in ("sources.py", "units.py", "paths.py")
    ] + [BASE.parent / "CONTRACT.md"]
    deps += [
        BASE.parents[1]
        / "v4-attention-projections/public/src/infra_calc/topics/v4_attention_projections.py",
        ROOT / "references/text/deepseek-v4.txt",
    ]
    import torch

    binding = dict(
        status="frozen for independent review",
        tests_passed=result.testsRun,
        tests_skipped=len(result.skipped),
        runtime=dict(
            executable=sys.executable,
            python=platform.python_version(),
            torch=torch.__version__,
        ),
        scenarios=comparisons,
        source_records_verified=len(subset),
        artifacts=[bind(p) for p in sorted(files)],
        dependencies=[bind(p) for p in deps],
    )
    (BASE / "bindings.json").write_text(json.dumps(binding, indent=2) + "\n")


if __name__ == "__main__":
    main()
