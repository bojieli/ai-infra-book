"""Independent offline byte/extraction/identity/scope checks. No network."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

D = Path(__file__).resolve().parent


def load(f):
    return json.loads((D / f).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def html_text(f):
    soup = BeautifulSoup((D / f).read_bytes(), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return (soup.get_text("\n", strip=True) + "\n").replace("\r\n", "\n").replace("\r", "\n")


sources = load("sources.json")
for rows in [sources, load("reused-sources.json")]:
    for row in rows:
        raw = (D / row["file"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], row["file"]
assert len(sources) == 11
assert sum(s["status"] == 200 for s in sources) == 10
assert sum(s["status"] == 202 for s in sources) == 1
assert (D / "blenda-publisher.response").read_bytes() == b""
coverage = load("input-reading-coverage.json")
status = {r["program_order"]: r for r in coverage["records"]}
record = load("abstracts.json")
assert record["locked_program_orders"] == [21, 72, 73, 89, 94, 97]
assert coverage["summary"]["primary_abstracts_screened"] == 52
assert status[11]["abstract_read"] is True
assert all(status[n]["abstract_read"] is False for n in record["locked_program_orders"])
assert record["input_reading_coverage_sha256"] == sha((D / "input-reading-coverage.json").read_bytes())
assert record["input_manifest_sha256"] == sha((D / "input-manifest.json").read_bytes())
original = {r["program_order"]: r for r in load("input-manifest.json")["papers"]}
papers = record["papers"]
assert [p["program_order"] for p in papers] == [21, 72, 73, 89, 94]
assert len({p["doi"] for p in papers}) == 5
for p in papers:
    n = p["program_order"]
    assert p["doi"] == status[n]["doi"] == original[n]["doi"]
    for key in ["publisher_title", "publisher_authors", "program_title"]:
        assert p[key] == original[n][key]
    assert p["read_scope"]["complete_abstract"] is True and p["read_scope"]["body_read"] is False
    assert p["screening"]["outline_changed"] is False
    assert sha((D / p["source_file"]).read_bytes()) == p["source_sha256"]
    if p["pdf_pages"]:
        pdf = D / p["source_file"]
        assert pdf.read_bytes().startswith(b"%PDF")
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, check=True)
        assert int(re.search(r"^Pages:\s+(\d+)", info.stdout.decode(), re.M).group(1)) == p["pdf_pages"]
        cmd = p["extraction"]["command"][:]
        cmd[-2] = str(pdf)
        extracted = subprocess.run(cmd, capture_output=True, check=True)
        assert extracted.stdout == (D / p["abstract_text_file"]).read_bytes()
        if n == 72:
            assert b"xref num 4" in extracted.stderr
    else:
        assert n == 73 and html_text(p["source_file"]) == (D / p["abstract_text_file"]).read_text()
    raw = (D / p["abstract_text_file"]).read_bytes()
    assert sha(raw) == p["abstract_text_sha256"]
    a, z = p["abstract_char_range"]
    assert raw.decode()[a:z] == p["abstract"]
    assert (D / p["abstract_file"]).read_text() == p["abstract"] + "\n"
    assert sha(p["abstract"].encode()) == p["abstract_sha256"]
    assert len(p["abstract"].split()) > 100

blocked = record["unavailable"]
assert len(blocked) == 1 and blocked[0]["program_order"] == 97
assert blocked[0]["complete_abstract"] is False and blocked[0]["screening_decision"] is None
assert blocked[0]["doi"] == original[97]["doi"]
reading = load("reading.json")
assert reading["body_pages_read"] == 0 and reading["full_primary_abstracts_read"] == 5
assert len(reading["images_actually_viewed"]) == 4
for image in reading["images_actually_viewed"]:
    assert image["actually_viewed"] is True and image["physical_page"] == 1
    assert sha((D / image["file"]).read_bytes()) == image["sha256"]
for item in reading["identity_text_scopes"] + reading["auxiliary_text_scopes"]:
    raw = (D / item["file"]).read_bytes()
    assert sha(raw) == item["sha256"]
    if "source_file" in item:
        text = html_text(item["source_file"])
        assert text == raw.decode()
        a, z = item["char_range"]
        assert 0 <= a < z <= len(text) and text[a:z] == item["text"]
arxiv = (D / "recommendation-arxiv.txt").read_text()
assert "[v1]" in arxiv and "29 Oct 2024 17:13:54 UTC" in arxiv
assert "2024 Nov 6" in (D / "genie-institution.txt").read_text()
logs = load("extraction-log.json")
assert len(logs) == 12
for row in logs:
    assert row["returncode"] == 0
    assert (D / row["stderr_file"]).read_text() == row["stderr"]
assert sum(bool(r["stderr"]) for r in logs) == 3
assert all(r["program_order"] == 72 for r in logs if r["stderr"])
assert sum(p["pdf_pages"] for p in papers) == 65
assert sum(p["screening"]["decision"] == "candidate" for p in papers) == 1
assert sum(p["screening"]["decision"] == "reference" for p in papers) == 4
report = {"verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS", "locked_targets": 6, "new_full_primary_abstracts": 5, "unavailable_abstracts": 1, "public_pdfs": 4, "archived_pdf_pages": 65, "body_pages_read": 0, "viewed_images": 4, "new_http_requests": 11, "http_200": 10, "http_202_empty_non_evidence": 1, "candidate": 1, "reference": 4, "excluded": 0, "pdf_with_recorded_reconstruction_warning": 72, "downloaded_code_executed": False, "network_used_by_verifier": False, "verification_boundary": "Bytes, false coverage snapshot, identity keys, complete extraction/ranges and recorded visual checks; no body/performance validation or proof of publisher version equivalence."}
(D / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
