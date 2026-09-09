import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
spec = importlib.util.spec_from_file_location(
    "execution", ROOT / "public/src/infra_calc/topics/qwen235_execution.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenarios = [
    dict(id="qwen235-ep4-tp2-balanced-80gb", tokens=16),
    dict(id="qwen235-ep4-tp2-hot-80gb", tokens=16, route_policy="hot"),
    dict(
        id="qwen235-ep4-pp2-48gb",
        tp=1,
        ep=4,
        pp=2,
        tokens=16,
        capacity_bytes=48 * 10**9,
    ),
    dict(
        id="qwen235-ep4-tp2-24gb-32k",
        tokens=16,
        capacity_bytes=24 * 10**9,
        length=32768,
    ),
    dict(id="qwen235-ep4-tp2-two-requests", requests=2, tokens=16, length=32768),
]
base = m.calculate(tokens=2)
pure = base["route_table"]
for row in pure:
    top = len(row["experts"])
    row["experts"] = (
        list(range(top)) if row["position"] == 0 else list(range(32, 32 + top))
    )
import copy

mixed = copy.deepcopy(pure)
for row in mixed:
    top = len(row["experts"])
    offset = 0 if row["position"] == 0 else top // 2
    row["experts"] = list(range(offset, offset + top // 2)) + list(
        range(32 + offset, 32 + offset + top // 2)
    )
scenarios += [
    dict(id="qwen235-equal-hist-pure", tokens=2, routes=pure),
    dict(id="qwen235-equal-hist-mixed", tokens=2, routes=mixed),
]
summary = []
for item in scenarios:
    result = m.calculate(**{k: v for k, v in item.items() if k != "id"})
    write(ROOT / "public/results" / f"{item['id']}.json", result)
    (ROOT / "public/results" / f"{item['id']}.md").write_text(m.markdown(result))
    summary.append(dict(id=item["id"], summary=result["summary"]))
write(ROOT / "public/book.append.json", scenarios)
write(ROOT / "scenario-summary.json", summary)
from infra_calc.sources import records

sources = [
    row
    for row in records()
    if row.get("model") in ("qwen3-235b-a22b", "qwen3")
    and row.get("status") == "downloaded"
]
write(
    ROOT / "public/sources.lock.subset.json",
    dict(description="existing public records; not new sources", sources=sources),
)
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
bindings = [
    dict(
        file=str(p.relative_to(PROJECT)),
        sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
    )
    for p in files
]
for relative in (
    "src/infra_calc/topics/qwen235_placement.py",
    "src/infra_calc/models/qwen3_moe.py",
):
    p = PROJECT / relative
    bindings.append(
        dict(file=relative, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    )
write(ROOT / "bindings.json", dict(files=bindings))
