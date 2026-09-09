"""Standalone migration equivalence check; the topic itself imports public code."""

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for parent in HERE.parents:
    if (parent / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break
from infra_calc import topics

topics.__path__.insert(0, str(HERE / "src/infra_calc/topics"))
from infra_calc.topics import real_scaling_lifecycle

result = real_scaling_lifecycle.calculate()
original = json.loads((HERE.parent / "result.json").read_text())
assert result["scenario"] == original["scenario"]
assert result["variants"] == original["variants"]
(HERE / "example.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n"
)
(HERE / "example.md").write_text(real_scaling_lifecycle.markdown(result))
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
        dict(
            files=files,
            portable_tests=5,
            all_five_variant_ledgers_exactly_equal=True,
            shared_modified=False,
        ),
        indent=2,
    )
    + "\n"
)
