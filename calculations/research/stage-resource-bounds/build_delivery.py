"""Generate independent scenarios; preserve official unknown denominators."""

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CALC = HERE.parents[1]
PUBLIC = HERE / "public"
sys.path.insert(0, str(CALC / "src"))
from infra_calc import topics

topics.__path__.insert(0, str(PUBLIC / "src/infra_calc/topics"))
from infra_calc.topics import stage_resource_bounds as m

scenes = []
for model, short in [("qwen3-8b", "qwen8"), ("deepseek-v4-flash", "v4flash")]:
    for batch in [1, 8]:
        for phase, tokens, history in [
            ("prefill128", 128, 0),
            ("prefill512", 512, 0),
            ("decode8k", 1, 8192),
            ("decode32k", 1, 32768),
        ]:
            scenes.append(
                dict(
                    id=f"stage-resources-{short}-b{batch}-{phase}",
                    model=model,
                    batch=batch,
                    tokens=tokens,
                    history=history,
                )
            )
    for device in ["m4-max-40gpu-128gb", "atlas-300i-a2-64gb"]:
        scenes.append(
            dict(
                id=f"stage-resources-{short}-{device}",
                model=model,
                device=device,
                tokens=1,
                history=8192,
            )
        )
base = m.calculate(tokens=128)
assumed = {
    k: 1e10
    for stage in base["stages"]
    for k in stage["work"]
    if k.startswith("special:")
}
scenes.append(
    dict(id="stage-resources-qwen8-assumed-special-baseline", assumed_rates=assumed)
)
for resource in ["matrix_bf16", "vector_fp32", "interface_bytes", "special:exp"]:
    scenes.append(
        dict(
            id="stage-resources-qwen8-double-" + resource.replace(":", "-"),
            assumed_rates=assumed,
            rate_multipliers={resource: 2},
        )
    )
(PUBLIC / "book.append.json").write_text(json.dumps(scenes, indent=2) + "\n")
(PUBLIC / "results").mkdir(exist_ok=True)
summary = []
sources = {}
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    assert result == m.calculate(**result["scenario"])
    path = PUBLIC / "results" / scene["id"]
    path.with_suffix(".json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    path.with_suffix(".md").write_text(m.markdown(result))
    summary.append(
        dict(
            id=scene["id"],
            **result["summary"],
            missing=result["resource_bounds"]["missing_resources"],
            capacity_status=result["capacity"]["runtime_status"],
        )
    )
    for entry in result["sources"]:
        sources[entry["file"]] = entry
(HERE / "scenario-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
locks = json.loads((CALC / "configs/sources.lock.json").read_text())["sources"]
selected = []
for entry in locks:
    if entry["file"] in sources:
        raw = (CALC / entry["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        selected.append(entry)
(PUBLIC / "sources.lock.subset.json").write_text(
    json.dumps(dict(sources=selected), indent=2) + "\n"
)


def bind(path):
    raw = path.read_bytes()
    return dict(
        file=str(path.relative_to(CALC.parent)),
        sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw),
    )


artifacts = [
    p
    for p in HERE.rglob("*")
    if p.is_file() and p.suffix in (".py", ".json", ".md") and p.name != "bindings.json"
]
dependencies = [
    CALC / "src/infra_calc" / p
    for p in [
        "hardware.py",
        "schema.py",
        "sources.py",
        "models/qwen3.py",
        "topics/v4_forward.py",
        "topics/v4_attention.py",
        "topics/experts.py",
        "topics/hyper_connections.py",
        "topics/v4_fp8_linear.py",
    ]
]
(HERE / "bindings.json").write_text(
    json.dumps(
        dict(
            status="frozen for independent review",
            tests_passed=7,
            scenarios=len(scenes),
            artifacts=[bind(p) for p in sorted(artifacts)],
            dependencies=[bind(p) for p in dependencies],
        ),
        indent=2,
    )
    + "\n"
)
print(len(scenes), "scenarios", len(selected), "source records")
