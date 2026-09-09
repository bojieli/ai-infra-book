"""Migration evidence only; production module does not import this script."""

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / "src/infra_calc/sources.py").is_file())
sys.path.insert(0, str(PROJECT / "src"))
module_file = HERE / "src/infra_calc/topics/omni_audio_preprocess.py"
spec = importlib.util.spec_from_file_location("candidate_pcm", module_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE / "sources/omni-audio-preprocess"
original = HERE.parent / "omni_audio_preprocess.py"


def functions(path):
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


old, new = functions(original), functions(module_file)
assert old == new
checks = []
for row in json.loads((HERE / "copy-manifest.json").read_text()):
    raw = (HERE / row["candidate_file"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
for scenario in json.loads((HERE / "book.append.json").read_text()):
    result = module.calculate(**{k: v for k, v in scenario.items() if k != "id"})
    stored = json.loads((HERE / "results" / f"{scenario['id']}.json").read_text())
    original_result = json.loads(
        (HERE.parent / "results" / f"{scenario['id']}.json").read_text()
    )
    assert result == stored == original_result
    assert result == module.calculate(**result["scenario"])
    assert (
        module.markdown(result)
        == (HERE / "results" / f"{scenario['id']}.md").read_text()
    )
    checks.append(
        dict(
            id=scenario["id"],
            all_result_fields_equal=True,
            replay_equal=True,
            markdown_equal=True,
        )
    )
evidence = dict(
    module_sha256=hashlib.sha256(module_file.read_bytes()).hexdigest(),
    all_function_asts_equal=sorted(new),
    scenarios=checks,
    copied_files=len(json.loads((HERE / "copy-manifest.json").read_text())),
    source_path_change="Only module global HERE: original local directory -> PROJECT/sources/omni-audio-preprocess. Nested sources/ preserves exact relative source locators and every function AST/result field.",
)
(HERE / "migration-verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
files = [
    p
    for p in HERE.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
(HERE / "bindings.json").write_text(
    json.dumps(
        [
            dict(
                file=str(p.relative_to(HERE)),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                bytes=p.stat().st_size,
            )
            for p in sorted(files)
        ],
        indent=2,
    )
    + "\n"
)
print(json.dumps(evidence, indent=2))
