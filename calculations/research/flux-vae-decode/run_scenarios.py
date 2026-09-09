"""Write independent VAE decoder scenarios; never touches shared results."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / "src"))
from flux_vae_decode import calculate

rows = [
    dict(id="flux-vae-1024-bf16-sdpa", inputs={}),
    dict(id="flux-vae-1024-bf16-eager", inputs=dict(attention="eager")),
    dict(
        id="flux-vae-rectangular-b2",
        inputs=dict(height=512, width=768, batch=2, workspace_bytes=536870912),
    ),
    dict(
        id="flux-vae-512-fp32-eager",
        inputs=dict(height=512, width=512, dtype="fp32", attention="eager"),
    ),
]
(ROOT / "scenarios.json").write_text(json.dumps(rows, indent=2) + "\n")
(ROOT / "results").mkdir(exist_ok=True)
summary = []
for row in rows:
    result = calculate(**row["inputs"])
    (ROOT / "results" / f"{row['id']}.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    summary.append(
        dict(
            id=row["id"],
            input=result["latent_shape"],
            output=result["output_shape"],
            **result["summary"],
        )
    )
(ROOT / "scenario-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
