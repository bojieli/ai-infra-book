import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
spec = importlib.util.spec_from_file_location(
    "tiles", ROOT / "public/src/infra_calc/topics/architecture_tile_work.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenes = [
    dict(id="architecture-tile-tail129"),
    dict(id="architecture-tile-aligned128", tokens=128),
    dict(id="architecture-tile-decode8k", tokens=1, history=8192),
    dict(
        id="architecture-tile-custom-rate",
        tile_m=96,
        tile_n=160,
        tile_k=80,
        variant_rates={"shallower_wider": 70e12},
    ),
]
summary = []
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    write(ROOT / "public/results" / f"{scene['id']}.json", result)
    (ROOT / "public/results" / f"{scene['id']}.md").write_text(m.markdown(result))
    summary.append(
        dict(
            id=scene["id"],
            variants=[
                {k: v for k, v in row.items() if k != "matrices"}
                for row in result["variants"]
            ],
            comparison=result["comparison"],
        )
    )
write(ROOT / "public/book.append.json", scenes)
write(ROOT / "scenario-summary.json", summary)
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
files += [
    PROJECT / "src/infra_calc/topics" / name
    for name in ("architecture_variants.py", "gemm_tiles.py", "quantized_gemm.py")
]
files += [
    PROJECT / "src/infra_calc/models/qwen3.py",
    PROJECT / "src/infra_calc/schema.py",
]
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
