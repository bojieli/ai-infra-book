"""Offline byte, identity, extraction, correction and counting checks."""
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
assert len(sources) == 16
assert sum(r["status"] == 200 for r in sources) == 13
assert sum(r["status"] == 202 for r in sources) == 2
assert sum(r["status"] == 404 for r in sources) == 1
assert (D / "campu-publisher.response").read_bytes() == (D / "emi-publisher.response").read_bytes() == b""
assert not (D / "emi-author-pdf-404.response").read_bytes().startswith(b"%PDF")

coverage = load("input-reading-coverage.json")
original = {r["program_order"]: r for r in load("input-manifest.json")["papers"]}
status = {r["program_order"]: r for r in coverage["records"]}
record = load("abstracts.json")
assert record["locked_program_orders"] == [4, 5, 6, 7, 8, 9]
assert all(status[n]["abstract_read"] is False for n in record["locked_program_orders"])
third = {r["program_order"] for r in load("third-batch-abstracts.json")["papers"]}
assert not third & set(record["locked_program_orders"])
for key, f in [("input_manifest_sha256", "input-manifest.json"), ("input_reading_coverage_sha256", "input-reading-coverage.json"), ("third_batch_sha256", "third-batch-abstracts.json")]:
    assert record[key] == sha((D / f).read_bytes())
papers = record["papers"]
assert [p["program_order"] for p in papers] == [4, 5, 6, 7, 8, 9]
assert len({p["doi"] for p in papers}) == 6
assert record["unavailable"] == []

for p in papers:
    n = p["program_order"]
    assert p["doi"] == original[n]["doi"] == status[n]["doi"]
    for k in ["publisher_title", "program_title", "publisher_authors"]:
        assert p[k] == original[n][k]
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
        assert extracted.stdout == (D / p["extraction"]["source_text"]).read_bytes()
        if n == 6:
            corrections = load(p["extraction"]["correction_file"])
            text = (D / corrections["raw_file"]).read_text()
            for change in corrections["corrections"]:
                assert text.count(change["before"]) == 1
                text = text.replace(change["before"], change["after"])
            assert text == (D / corrections["corrected_file"]).read_text()
            assert text == (D / p["abstract_text_file"]).read_text()
    else:
        assert html_text(p["source_file"]) == (D / p["abstract_text_file"]).read_text()
    raw = (D / p["abstract_text_file"]).read_bytes()
    assert sha(raw) == p["abstract_text_sha256"]
    a, z = p["abstract_char_range"]
    assert raw.decode()[a:z] == p["abstract"]
    assert sha(p["abstract"].encode()) == p["abstract_sha256"]
    assert (D / p["abstract_file"]).read_text() == p["abstract"] + "\n"
    assert len(p["abstract"].split()) > 90

reading = load("reading.json")
assert reading["body_pages_read"] == 0 and reading["full_primary_abstracts_read"] == 6
assert [i["program_order"] for i in reading["images_actually_viewed"]] == [6, 7, 8]
for image in reading["images_actually_viewed"]:
    assert image["actually_viewed"] is True and image["physical_page"] == 1
    assert sha((D / image["file"]).read_bytes()) == image["sha256"]
for item in reading["auxiliary_text_scopes"]:
    raw = (D / item["file"]).read_bytes()
    assert sha(raw) == item["sha256"]
    text = html_text(item["source_file"])
    assert text == raw.decode()
    a, z = item["char_range"]
    assert 0 <= a < z <= len(text) and text[a:z] == item["text"]
fusion_pdf = next(p["abstract"] for p in papers if p["program_order"] == 6)
fusion_html = next(x["text"] for x in reading["auxiliary_text_scopes"] if x["source_file"] == "fusion-author-pubs.html")
for term in ["2.5×", "6×", "7.3×", "6.5×", "≤ 2 seconds", "≥ 30 FPS"]:
    assert term in fusion_pdf and term in fusion_html
assert "MICRO61859.2024.00018" in (D / "paper-008-first-page.txt").read_text()
assert "hypertee-micro25.pdf" in next(r["url"] for r in sources if r["file"] == "paper-008.pdf")

wrong = reading["identity_rejected_document"]
assert wrong["counted_as_matched_pdf"] is False and wrong["image_actually_viewed"] is False
assert wrong["actual_program_order"] == 16
assert all(p["source_file"] != wrong["file"] for p in papers)
wrong_info = subprocess.run(["pdfinfo", str(D / wrong["file"])], capture_output=True, check=True).stdout.decode()
assert "LightWSP: Whole-System Persistence on the Cheap" in wrong_info
assert int(re.search(r"^Pages:\s+(\d+)", wrong_info, re.M).group(1)) == 16
assert sum(p["pdf_pages"] > 0 for p in papers) == 3
assert sum(p["pdf_pages"] for p in papers) == 43
assert sum(p["screening"]["decision"] == "candidate" for p in papers) == 0
assert sum(p["screening"]["decision"] == "reference" for p in papers) == 4
assert sum(p["screening"]["decision"] == "exclude" for p in papers) == 2
report = {"verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS", "locked_targets": 6, "new_full_primary_abstracts": 6, "unavailable_abstracts": 0, "matched_public_pdfs": 3, "matched_public_pdf_pages": 43, "identity_rejected_pdf_count": 1, "identity_rejected_pdf_pages": 16, "body_pages_read": 0, "viewed_images": 3, "new_http_requests": 16, "http_200": 13, "http_202_empty_non_evidence": 2, "http_404": 1, "candidate": 0, "reference": 4, "excluded": 2, "corrected_math_glyphs": 6, "downloaded_code_executed": False, "network_used_by_verifier": False, "verification_boundary": "Original bytes, snapshot/identity keys, extraction/ranges, explicit symbol correction and recorded image checks. Excludes off-target LightWSP from matched PDF/abstract counts; no body, performance or security-claim validation."}
(D / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
