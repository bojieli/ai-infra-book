"""Independent local byte, extraction, identity-key and scope checks. No network."""
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


sources = load("sources.json")
for rows in [sources, load("reused-sources.json")]:
    for r in rows:
        b = (D / r["file"]).read_bytes()
        assert len(b) == r["bytes"] and sha(b) == r["sha256"], r["file"]
assert len(sources) == 11
assert sum(r["status"] == 200 for r in sources) == 9
assert sum(r["status"] == 403 for r in sources) == 1
assert sum(r["status"] == 202 for r in sources) == 1
assert (D / "atomic-cache-publisher.response").read_bytes() == b""
assert not (D / "atomic-cache-author.html").read_bytes().startswith(b"%PDF")

original = {r["program_order"]: r for r in load("input-manifest.json")["papers"]}
seen = {r["program_order"] for r in load("input-public-abstracts.json")["papers"]}
previous = {r["program_order"] for r in load("previous-batch-abstracts.json")["papers"]}
assert len(seen) == 41 and previous == {41, 53, 87, 88, 111, 119}
record = load("abstracts.json")
for key, filename in [("input_manifest_sha256", "input-manifest.json"), ("input_abstracts_sha256", "input-public-abstracts.json"), ("previous_batch_sha256", "previous-batch-abstracts.json")]:
    assert record[key] == sha((D / filename).read_bytes())
assert record["locked_program_orders"] == [2, 3, 51, 52, 75, 121]
assert not set(record["locked_program_orders"]) & (seen | previous)
papers = record["papers"]
assert [p["program_order"] for p in papers] == [2, 3, 52, 75, 121]
assert len({p["doi"].lower() for p in papers}) == 5

for p in papers:
    n = p["program_order"]
    for k in ["doi", "publisher_title", "publisher_authors", "program_title"]:
        assert p[k] == original[n][k]
    assert p["previous_reading_status"] == "metadata_matched_not_screened"
    assert p["read_scope"]["complete_abstract"] is True
    assert p["read_scope"]["body_read"] is False
    assert p["screening"]["outline_changed"] is False
    pdf = D / p["source_file"]
    assert pdf.read_bytes().startswith(b"%PDF")
    assert sha(pdf.read_bytes()) == p["source_sha256"]
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    assert int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1)) == p["pdf_pages"]
    cmd = p["extraction"]["command"][:]
    cmd[-2] = str(pdf)
    assert subprocess.check_output(cmd) == (D / p["abstract_text_file"]).read_bytes()
    t = (D / p["abstract_text_file"]).read_text()
    assert sha((D / p["abstract_text_file"]).read_bytes()) == p["abstract_text_sha256"]
    a, z = p["abstract_char_range"]
    assert t[a:z] == p["abstract"]
    assert sha(p["abstract"].encode()) == p["abstract_sha256"]
    assert (D / p["abstract_file"]).read_text() == p["abstract"] + "\n"
    assert len(p["abstract"].split()) > 100

blocked = record["unavailable"]
assert len(blocked) == 1 and blocked[0]["program_order"] == 51
assert blocked[0]["doi"] == original[51]["doi"]
assert blocked[0]["complete_abstract"] is False
assert blocked[0]["screening_decision"] is None

reading = load("reading.json")
for r in reading["images_actually_viewed"]:
    assert r["actually_viewed"] is True and r["physical_page"] == 1
    assert sha((D / r["file"]).read_bytes()) == r["sha256"]
for r in reading["identity_text_scopes"] + reading["auxiliary_text_scopes"]:
    b = (D / r["file"]).read_bytes()
    assert sha(b) == r["sha256"]
    a, z = r["char_range"]
    assert 0 <= a < z <= len(b.decode())
    if "source_file" in r:
        soup = BeautifulSoup((D / r["source_file"]).read_bytes(), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        regenerated = (soup.get_text("\n", strip=True) + "\n").replace("\r\n", "\n").replace("\r", "\n")
        assert regenerated == b.decode()
        assert regenerated[a:z] == r["text"]

pdf_cars = next(p["abstract"] for p in papers if p["program_order"] == 52)
html_cars = next(r["text"] for r in reading["auxiliary_text_scopes"] if r["source_file"] == "cars-author.html")
assert "26% and 28%" in pdf_cars
assert "25% and 30%" in html_cars
assert reading["body_pages_read"] == 0
assert reading["full_primary_abstracts_read"] == 5
assert len(reading["images_actually_viewed"]) == 5
assert sum(p["pdf_pages"] for p in papers) == 76
assert sum(p["screening"]["decision"] == "candidate" for p in papers) == 1
assert sum(p["screening"]["decision"] == "reference" for p in papers) == 4
report = {"verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS", "locked_targets": 6, "new_full_primary_abstracts": 5, "unavailable_abstracts": 1, "public_pdfs": 5, "archived_pdf_pages": 76, "body_pages_read": 0, "viewed_images": 5, "new_http_requests": 11, "http_200": 9, "http_403": 1, "http_202_empty_non_evidence": 1, "candidate": 1, "reference": 4, "excluded": 0, "downloaded_code_executed": False, "network_used_by_verifier": False, "verification_boundary": "Byte/range/Poppler extraction/identity-key consistency plus manually recorded image checks; no independent validation of paper claims, abstract version preference or body evaluation."}
(D / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
