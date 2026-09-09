"""Validate static NeuSight evidence and independently authored arithmetic only."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "references/framework-history/2026-09-09/neusight-calibration"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    inventory = json.loads((BASE / "inventory.json").read_text())
    for item in inventory["files"]:
        data = (BASE / item["file"]).read_bytes()
        assert len(data) == item["bytes"] and sha(data) == item["sha256"], item["file"]
    sources = json.loads((BASE / "sources.json").read_text())
    for item in sources:
        data = (BASE / item["file"]).read_bytes()
        assert len(data) == item["bytes"] and sha(data) == item["sha256"], item["file"]
    reading = json.loads((BASE / "reading.json").read_text())
    for item in reading["source_reading"]:
        data = (BASE / item["file"]).read_bytes()
        lines = data.splitlines(keepends=True)
        assert sha(data) == item["sha256"] and len(lines) == item["total_lines"]
        for span in item["range_sha256"]:
            assert sha(b"".join(lines[span["first"] - 1:span["last"]])) == span["sha256"], item["file"]
    proof = json.loads((BASE / "neusight-reading.json").read_text())
    pdf = ROOT / proof["paper"]["pdf"]["file"]
    assert sha(pdf.read_bytes()) == proof["paper"]["pdf"]["sha256"]
    assert pdf.read_bytes() == (BASE / "sources/neusight-paper.pdf").read_bytes()
    for page, expected in proof["reading"]["page_text_sha256"].items():
        data = subprocess.check_output(["pdftotext", "-f", page, "-l", page, str(pdf), "-"], stderr=subprocess.PIPE)
        assert sha(data) == expected, page
    for figure in proof["figures"]:
        data = (ROOT / figure["file"]).read_bytes()
        assert len(data) == figure["bytes"] and sha(data) == figure["sha256"]
    commit = json.loads((BASE / "sources/neusight-main-commit.json").read_text())
    assert commit["sha"] == "6945927d9afcca2b9daf021f8395e53edc5b4eef"
    arithmetic = json.loads((BASE / "arithmetic.json").read_text())
    pred, actual = arithmetic["predicted_stage_ms"], arithmetic["actual_stage_ms"]
    assert pred == [8, 2] and actual == [6, 4]
    assert sum(pred) == sum(actual) == 10
    assert [abs(Fraction(p - a, a)) for p, a in zip(pred, actual)] == [Fraction(1, 3), Fraction(1, 2)]
    assert pred[0] / 2 + pred[1] == arithmetic["first_stage_halving_predicted_total_ms"] == 6
    assert actual[0] / 2 + actual[1] == arithmetic["first_stage_halving_actual_total_ms"] == 7
    output = {
        "status": "passed",
        "scope": "Static evidence integrity, worker page/source range proofs, and independent arithmetic. No predictor execution or new full-paper reading claim.",
        "inventory_files": len(inventory["files"]),
        "worker_selected_pages_verified": len(proof["reading"]["physical_pdf_pages"]),
        "worker_source_scopes_verified": len(reading["source_reading"]),
        "worker_figure_files_verified": len(proof["figures"]),
        "canonical_proceedings_counts_changed": False,
    }
    (BASE / "integration-validation.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    return output


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
