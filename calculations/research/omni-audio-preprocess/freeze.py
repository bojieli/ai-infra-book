from pathlib import Path
import json, hashlib
from omni_audio_preprocess import calculate, markdown

HERE = Path(__file__).resolve().parent
scenes = [
    dict(id="omni-pcm-1s", sample_lengths=[16000]),
    dict(id="omni-pcm-mixed", sample_lengths=[479, 800]),
    dict(id="omni-pcm-hop-tail", sample_lengths=[321]),
    dict(id="omni-pcm-serialized-limit", sample_lengths=[4800000]),
]
(HERE / "results").mkdir(exist_ok=True)
summary = []
for scene in scenes:
    r = calculate(**{k: v for k, v in scene.items() if k != "id"})
    p = HERE / "results" / scene["id"]
    p.with_suffix(".json").write_text(
        json.dumps(r, indent=2, ensure_ascii=False) + "\n"
    )
    p.with_suffix(".md").write_text(markdown(r))
    summary.append(dict(id=scene["id"], geometry=r["geometry"], summary=r["summary"]))
(HERE / "book.append.json").write_text(json.dumps(scenes, indent=2) + "\n")
(HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
files = [
    p
    for p in HERE.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
(HERE / "bindings.json").write_text(
    json.dumps(
        [
            dict(
                file=str(p.relative_to(HERE)),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            )
            for p in sorted(files)
        ],
        indent=2,
    )
    + "\n"
)
print(json.dumps(summary[0], indent=2))
