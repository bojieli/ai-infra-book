"""Portable candidate replay. After installation use the ordinary topic module."""

from pathlib import Path
import sys
import json
import hashlib

HERE = Path(__file__).resolve().parent
for ancestor in HERE.parents:
    if (ancestor / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(0, str(HERE / "src/infra_calc/topics"))
from infra_calc.topics import real_scaling_fit

real_scaling_fit.PROJECT = HERE
result = real_scaling_fit.calculate()
(HERE / "example.json").write_text(json.dumps(result, indent=2) + "\n")
(HERE / "example.md").write_text(real_scaling_fit.markdown(result))
original = json.loads((HERE.parent / "statistical-fit.json").read_text())
assert result["primary"]["result"]["law"] == original["primary"]["result"]["law"]
assert (
    result["primary"]["result"]["fit_sse"] == original["primary"]["result"]["fit_sse"]
)
for name in result["sensitivity"]:
    assert (
        result["sensitivity"][name]["result"]["law"]
        == original["sensitivity"][name]["result"]["law"]
    )
files = []
for path in HERE.rglob("*"):
    if not path.is_file() or path.name == "bindings.json" or "__pycache__" in str(path):
        continue
    raw = path.read_bytes()
    files.append(
        dict(
            file=str(path.relative_to(HERE)),
            sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),
        )
    )
(HERE / "bindings.json").write_text(
    json.dumps(
        dict(files=files, public_research_math_equal=True, portable_tests=3), indent=2
    )
    + "\n"
)
