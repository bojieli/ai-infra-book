from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
spec = importlib.util.spec_from_file_location(
    "granularity", ROOT / "public/src/infra_calc/topics/qwen235_expert_granularity.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenes = [
    dict(id="qwen235-granularity-baseline"),
    dict(id="qwen235-granularity-coarse64", experts=64, top_k=4),
    dict(id="qwen235-granularity-fine256-k16", experts=256, top_k=16),
    dict(id="qwen235-granularity-fine256-k8", experts=256, top_k=8),
    dict(id="qwen235-granularity-aligned160", experts=160, top_k=10),
    dict(id="qwen235-granularity-hot", route_policy="hot"),
]
summary = []
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    write(ROOT / "public/results" / f"{scene['id']}.json", result)
    (ROOT / "public/results" / f"{scene['id']}.md").write_text(m.markdown(result))
    summary.append(
        dict(
            id=scene["id"],
            geometry=result["geometry"],
            parameters=result["parameters"],
            summary=result["summary"],
        )
    )
write(ROOT / "public/book.append.json", scenes)
write(ROOT / "scenario-summary.json", summary)
from infra_calc.sources import records

write(
    ROOT / "public/sources.lock.subset.json",
    dict(
        sources=[
            row
            for row in records()
            if row.get("model") in ("qwen3", "qwen3-235b-a22b")
            and row.get("status") == "downloaded"
        ]
    ),
)
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
files += [
    PROJECT / "src/infra_calc/topics" / name
    for name in (
        "architecture_variants.py",
        "qwen235_execution.py",
        "qwen235_placement.py",
    )
]
files += [PROJECT / "src/infra_calc/models/qwen3_moe.py"]
write(
    ROOT / "bindings.json",
    dict(
        files=[
            dict(
                file=str(p.relative_to(PROJECT)),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            )
            for p in sorted(files)
        ]
    ),
)
