from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
spec = importlib.util.spec_from_file_location(
    "bridge", ROOT / "public/src/infra_calc/topics/trace_resource_bridge.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.SOURCE_ROOT = ROOT / "public/sources/trace-resource-bridge"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenes = [
    dict(id="sealed-chat-known-prefill"),
    dict(
        id="sealed-chat-declared-serial", generation_policy="returned_ids_serial_policy"
    ),
]
summary = []
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    write(ROOT / "public/results" / f"{scene['id']}.json", result)
    (ROOT / "public/results" / f"{scene['id']}.md").write_text(m.markdown(result))
    summary.append(dict(id=scene["id"], summary=result["summary"]))
write(ROOT / "public/book.append.json", scenes)
write(ROOT / "scenario-summary.json", summary)
source_files = [p for p in (ROOT / "public/sources").rglob("*") if p.is_file()]
write(
    ROOT / "public/copy-manifest.json",
    [
        dict(
            candidate_file=str(p.relative_to(ROOT / "public")),
            project_target=str(p.relative_to(ROOT / "public")),
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        )
        for p in sorted(source_files)
    ],
)
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
files += [
    PROJECT / "src/infra_calc/topics" / name
    for name in ("request_model_comparison.py", "workload_profiles.py")
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
