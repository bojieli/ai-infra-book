"""Regenerate only this independent candidate's reviewable artifacts."""

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
from infra_calc.topics import training_pipeline_schedule as m

scenes = []
for policy in ["gpipe", "1f1b"]:
    for M in [1, 4, 8, 16]:
        scenes.append(
            dict(id=f"training-pipeline-{policy}-m{M}", policy=policy, microbatches=M)
        )
    scenes.append(
        dict(
            id=f"training-pipeline-{policy}-slow-stage",
            policy=policy,
            microbatches=8,
            forward_seconds=[0.01, 0.035, 0.01, 0.01],
            backward_seconds=[0.02, 0.07, 0.02, 0.02],
        )
    )
    scenes.append(
        dict(
            id=f"training-pipeline-{policy}-shared-link",
            policy=policy,
            microbatches=8,
            activation_transfer_seconds=[0.02] * 3,
            gradient_transfer_seconds=[0.02] * 3,
            link_mode="shared_half_duplex",
        )
    )
    scenes.append(
        dict(
            id=f"training-pipeline-{policy}-recompute",
            policy=policy,
            microbatches=8,
            activation_policy="recompute_silu",
            backward_seconds=[0.025] * 4,
        )
    )
(PUBLIC / "book.append.json").write_text(json.dumps(scenes, indent=2) + "\n")
summary = []
for scene in scenes:
    result = m.calculate(**{k: v for k, v in scene.items() if k != "id"})
    assert result == m.calculate(**result["scenario"])
    path = PUBLIC / "results" / scene["id"]
    path.with_suffix(".json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    path.with_suffix(".md").write_text(m.markdown(result))
    summary.append(dict(id=scene["id"], **result["summary"]))
(HERE / "scenario-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
lock = json.loads((CALC / "configs/sources.lock.json").read_text())
subset = [r for r in lock["sources"] if r.get("model") == "qwen3-8b"]
(PUBLIC / "sources.lock.subset.json").write_text(
    json.dumps(dict(sources=subset), indent=2) + "\n"
)
dependencies = [
    CALC / "src/infra_calc" / name
    for name in [
        "topics/training_matrix.py",
        "topics/training_nonmatrix.py",
        "models/qwen3.py",
        "sources.py",
        "units.py",
    ]
]


def entry(path):
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
(HERE / "bindings.json").write_text(
    json.dumps(
        dict(
            status="frozen for independent review",
            artifacts=[entry(p) for p in sorted(artifacts)],
            dependencies=[entry(p) for p in dependencies],
        ),
        indent=2,
    )
    + "\n"
)
print(json.dumps(summary[:2], indent=2))
