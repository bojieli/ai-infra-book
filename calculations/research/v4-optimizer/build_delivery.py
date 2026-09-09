import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
module_path = ROOT / "public/src/infra_calc/topics/v4_optimizer.py"
spec = importlib.util.spec_from_file_location("optimizer", module_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


scenarios = [
    dict(id="flash-base-unresolved", scenario={}),
    dict(
        id="flash-mtp-declared-row-muon",
        scenario=dict(
            include_mtp=True,
            sink_policy="row_muon",
            head_mixer_policy="adamw",
            norm_epsilon=1e-7,
        ),
    ),
    dict(
        id="flash-stored-matrices",
        scenario=dict(
            sink_policy="row_muon",
            head_mixer_policy="muon",
            wo_a_partition="stored_matrix",
        ),
    ),
    dict(
        id="pro-base-declared-row-muon",
        scenario=dict(
            model="deepseek-v4-pro",
            sink_policy="row_muon",
            head_mixer_policy="adamw",
            learning_rate=2e-4,
        ),
    ),
]
summary = []
for item in scenarios:
    result = m.calculate(**item["scenario"])
    item["scenario"] = result["scenario"]
    write(ROOT / "public/results" / f"{item['id']}.json", result)
    (ROOT / "public/results" / f"{item['id']}.md").write_text(m.markdown(result))
    summary.append(
        dict(id=item["id"], summary=result["summary"], inventory=result["inventory"])
    )
write(ROOT / "public/scenarios.json", scenarios)
write(ROOT / "scenario-summary.json", summary)
from infra_calc.sources import records

sources = [
    r
    for r in records()
    if r.get("model") in ("deepseek-v4-flash", "deepseek-v4-pro")
    and r.get("status") == "downloaded"
]
report = PROJECT.parent / "references/text/deepseek-v4.txt"
pdf = PROJECT.parent / "references/files/papers/deepseek-v4.pdf"
evidence = dict(
    report_text=dict(
        file=str(report.relative_to(PROJECT.parent)),
        sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
    ),
    report_pdf=dict(
        file=str(pdf.relative_to(PROJECT.parent)),
        sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
        url="https://arxiv.org/pdf/2606.19348",
        version="2606.19348v1",
    ),
    locators=[
        "report §2.4 Algorithm 1 Eq28",
        "report §3.4.1",
        "report §4.2.2",
        "inference/model.py attention wo_a reshape and tensor constructors",
    ],
    public_sources=sources,
)
write(ROOT / "source-evidence.json", evidence)
files = [
    p
    for p in ROOT.rglob("*")
    if p.is_file() and "__pycache__" not in str(p) and p.name != "bindings.json"
]
write(
    ROOT / "bindings.json",
    dict(
        files=[
            dict(
                file=str(p.relative_to(ROOT)),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                bytes=p.stat().st_size,
            )
            for p in sorted(files)
        ]
    ),
)
