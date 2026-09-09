"""Generate the full three-model/eight-card capacity grid independently."""

import json
from pathlib import Path
from dense_quantized_placement import MODELS, calculate, markdown

ROOT = Path(__file__).resolve().parent
(ROOT / "results").mkdir(exist_ok=True)
scenarios, summaries = [], []
for model in MODELS:
    for tp, pp in [(8, 1), (2, 4), (1, 8)]:
        for gb in (24, 48, 80):
            for length in (8192, 32768):
                identifier = f"dense-quant-{model}-tp{tp}-pp{pp}-{gb}gb-{length}"
                inputs = dict(
                    model=model, tp=tp, pp=pp, length=length, capacity_bytes=gb * 10**9
                )
                result = calculate(**inputs)
                scenarios.append(dict(id=identifier, **inputs))
                summaries.append(
                    dict(
                        id=identifier,
                        scenario=result["scenario"],
                        summary=result["summary"],
                        replicas=result["replicas"],
                        ranks=[
                            {k: v for k, v in rank.items() if k != "weights"}
                            for rank in result["ranks"]
                        ],
                    )
                )
                if gb == 24 and length == 8192:
                    (ROOT / "results" / f"{identifier}.json").write_text(
                        json.dumps(result, indent=2) + "\n"
                    )
(ROOT / "book.append.json").write_text(
    json.dumps(dict(dense_quantized_placement=scenarios), indent=2) + "\n"
)
(ROOT / "scenario-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
(ROOT / "example.md").write_text(markdown(calculate()))
print(f"{len(scenarios)} scenarios, each with BF16/8bit/4bit and all ranks")
