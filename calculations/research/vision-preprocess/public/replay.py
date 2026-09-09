"""Candidate migration replay; public topic has no research imports."""

import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for ancestor in HERE.parents:
    if (ancestor / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(0, str(HERE / "src/infra_calc/topics"))
from infra_calc.topics import vision_preprocess

vision_preprocess.PROJECT = HERE
for scenario in json.loads((HERE / "book.append.json").read_text()):
    ident = scenario["id"]
    result = vision_preprocess.calculate(
        **{k: v for k, v in scenario.items() if k != "id"}
    )
    original = json.loads((HERE.parent / (ident + ".json")).read_text())
    for key in ["scenario", "summary", "resize_axes", "scope"]:
        assert result[key] == original[key], key
    stages = copy.deepcopy(result["stages"])
    for stage in stages:
        for ref in stage["source_refs"]:
            ref["file"] = ref["file"].removeprefix("sources/vision-preprocess/")
    assert stages == original["stages"]
    (HERE / (ident + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    (HERE / (ident + ".md")).write_text(vision_preprocess.markdown(result))
files = []
for path in HERE.rglob("*"):
    if not path.is_file() or path.name == "bindings.json" or "__pycache__" in str(path):
        continue
    b = path.read_bytes()
    files.append(
        dict(
            file=str(path.relative_to(HERE)),
            sha256=hashlib.sha256(b).hexdigest(),
            bytes=len(b),
        )
    )
(HERE / "bindings.json").write_text(
    json.dumps(
        dict(
            files=files,
            portable_tests=5,
            all_four_scenarios_stage_math_bytes_exactly_equal=True,
            shared_modified=False,
        ),
        indent=2,
    )
    + "\n"
)
