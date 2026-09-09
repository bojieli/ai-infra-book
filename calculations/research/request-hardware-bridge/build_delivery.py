import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
spec = importlib.util.spec_from_file_location(
    "bridge", ROOT / "public/src/infra_calc/topics/request_hardware_bridge.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenes = [
    dict(id="request-h100-original"),
    dict(id="request-h100-first-output", output_tokens=1),
    dict(
        id="request-h100-vector-provider",
        scalar_vector_provider=True,
        fp32_matrix_vector_provider=True,
    ),
    dict(id="request-h100-low-capacity", capacity_bytes=1_000_000),
]
summary = []
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    write(ROOT / "public/results" / f"{scene['id']}.json", result)
    (ROOT / "public/results" / f"{scene['id']}.md").write_text(m.markdown(result))
    summary.append(
        dict(
            id=scene["id"],
            models=[
                dict(
                    model=row["model"],
                    matrix_buckets=row["matrix_buckets"],
                    capacity_status=row["capacity"]["status"],
                    known_serial_comparison_seconds=row["resource_bounds"][
                        "known_serial_stage_max_sum_seconds"
                    ],
                    complete_runtime_seconds=row["complete_runtime_seconds"],
                )
                for row in result["models"]
            ],
        )
    )
write(ROOT / "public/book.append.json", scenes)
write(ROOT / "scenario-summary.json", summary)
from infra_calc.sources import records

selected = [
    row
    for row in records()
    if row.get("model")
    in (
        "qwen3-8b",
        "qwen3",
        "deepseek-v4-flash",
        "deepseek-v4-pro",
        "kimi-k3",
        "flash-linear-attention",
    )
    and row.get("status") == "downloaded"
]
write(
    ROOT / "public/sources.lock.subset.json",
    dict(
        description="Existing model original locks; no append/new fetch",
        sources=selected,
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
        "request_model_comparison.py",
        "stage_resource_bounds.py",
        "v4_prefix_continuation.py",
    )
]
files += [
    PROJECT / "src/infra_calc/hardware.py",
    PROJECT / "src/infra_calc/models/qwen3.py",
    PROJECT / "configs/hardware.json",
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
