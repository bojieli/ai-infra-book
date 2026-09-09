"""Check static POD source provenance and declared partial reading ranges."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "references/framework-history/2026-09-09/pod-implementation"


def verify():
    sources = json.loads((D / "sources.json").read_text())
    for item in sources:
        data = (ROOT / item["file"]).read_bytes()
        assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
        assert item["status_code"] == 200
    reading = json.loads((D / "reading.json").read_text())
    for item in reading["records"]:
        data = (D / item["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        lines = data.splitlines(keepends=True)
        for span in item["ranges"]:
            assert 1 <= span["first"] <= span["last"] <= len(lines)
            assert hashlib.sha256(b"".join(lines[span["first"]-1:span["last"]])).hexdigest() == span["sha256"]
    assert json.loads((D / "vattention-commit.json").read_text())["sha"] == "71a0e91aa46ff8fa985bcca3327efe0ab9929a39"
    assert json.loads((D / "flashinfer-commit.json").read_text())["sha"] == "b6aed59786374d437b64b054488d0740ad5f5468"
    result = {"status": "passed", "source_responses": len(sources), "partial_source_files_read": len(reading["records"]), "read_ranges": sum(len(r["ranges"]) for r in reading["records"]), "downloaded_code_executed": False, "new_paper_reading_credit": 0}
    (D / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
