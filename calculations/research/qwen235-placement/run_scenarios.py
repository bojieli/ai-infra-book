"""Independent scenario grid; full detail for four hand-checked organizations."""
import json
from pathlib import Path
from qwen235_placement import calculate

ROOT = Path(__file__).resolve().parent
rows, summaries = [], []
(ROOT / "results").mkdir(exist_ok=True)
for tp, ep, pp in [(2, 4, 1), (4, 2, 1), (2, 2, 2), (1, 1, 8)]:
    for capacity_gb in (24, 48, 80):
        for length in (8192, 32768):
            identifier = f"tp{tp}-ep{ep}-pp{pp}-{capacity_gb}gb-{length}"
            inputs = dict(tp=tp, ep=ep, pp=pp, length=length, capacity_bytes=capacity_gb * 10**9)
            result = calculate(**inputs)
            rows.append(dict(id=identifier, inputs=inputs))
            summaries.append(dict(id=identifier, scenario=result["scenario"], cohort=result["cohort"],
                                  ranks=[{k: v for k, v in rank.items() if k != "tensors"} for rank in result["ranks"]]))
            if capacity_gb == 80 and length == 8192:
                (ROOT / "results" / f"{identifier}.json").write_text(json.dumps(result, indent=2) + "\n")
(ROOT / "scenarios.json").write_text(json.dumps(rows, indent=2) + "\n")
(ROOT / "scenario-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
for row in summaries:
    print(row["id"], [entry["maximum_requests"] for entry in row["cohort"]])
