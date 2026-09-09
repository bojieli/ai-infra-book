"""Independent local checks. No network, model, simulator, or downloaded code."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

D = Path(__file__).resolve().parent


def load(name):
    return json.loads((D/name).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


sources = load("sources.json")
for manifest in [sources, load("reused-sources.json")]:
    for row in manifest:
        b=(D/row["file"]).read_bytes()
        assert len(b)==row["bytes"] and sha(b)==row["sha256"], row["file"]
assert len(sources)==12
assert sum(r["status"]==200 for r in sources)==11
assert sum(r["status"]==418 for r in sources)==1
assert not (D/"cxl2-publisher-pdf.response").read_bytes().startswith(b"%PDF")

manifest=load("input-manifest.json")
previous=load("input-public-abstracts.json")
original={p["program_order"]:p for p in manifest["papers"]}
seen={p["program_order"] for p in previous["papers"]}
record=load("abstracts.json")
assert record["input_manifest_sha256"]==sha((D/"input-manifest.json").read_bytes())
assert record["input_abstracts_sha256"]==sha((D/"input-public-abstracts.json").read_bytes())
papers=record["papers"]
assert [p["program_order"] for p in papers]==[41,53,87,88,111,119]
assert len({p["doi"].lower() for p in papers})==6
assert not {p["program_order"] for p in papers}&seen

for p in papers:
    n=p["program_order"]
    assert p["doi"]==original[n]["doi"]
    assert p["publisher_title"]==original[n]["publisher_title"]
    assert p["publisher_authors"]==original[n]["publisher_authors"]
    assert p["previous_reading_status"]=="metadata_matched_not_screened"
    assert p["read_scope"]["complete_abstract"] is True and p["read_scope"]["body_read"] is False
    assert p["screening"]["outline_changed"] is False
    assert sha((D/p["source_file"]).read_bytes())==p["source_sha256"]
    method=p["extraction"]
    if p["pdf_pages"]:
        pdf=D/p["source_file"]
        assert pdf.read_bytes().startswith(b"%PDF")
        info=subprocess.check_output(["pdfinfo",str(pdf)],text=True)
        assert int(re.search(r"^Pages:\s+(\d+)",info,re.M).group(1))==p["pdf_pages"]
        if n!=41:
            cmd=method["command"][:]
            cmd[-2]=str(pdf)
            regenerated=subprocess.check_output(cmd)
            assert regenerated==(D/method["source_text"]).read_bytes()
        else:
            ordinary=subprocess.check_output(["pdftotext","-f","1","-l","1",str(pdf),"-"])
            assert ordinary==(D/"paper-041-first-page.txt").read_bytes()==b"\x0c"
            correction=load("ocr-correction.json")
            text=(D/correction["raw_file"]).read_text()
            for c in correction["corrections"]:
                assert text.count(c["before"])==1
                text=text.replace(c["before"],c["after"])
            assert text==(D/correction["corrected_file"]).read_text()
    else:
        soup=BeautifulSoup((D/p["source_file"]).read_bytes(),"html.parser")
        for x in soup(["script","style"]):x.decompose()
        regenerated=(soup.get_text("\n",strip=True)+"\n").replace("\r\n","\n").replace("\r","\n")
        assert regenerated==(D/p["abstract_text_file"]).read_text()
    text=(D/p["abstract_text_file"]).read_text()
    assert sha((D/p["abstract_text_file"]).read_bytes())==p["abstract_text_sha256"]
    start,end=p["abstract_char_range"]
    assert 0<=start<end<=len(text)
    assert text[start:end]==p["abstract"]
    assert sha(p["abstract"].encode())==p["abstract_sha256"]
    assert (D/p["abstract_file"]).read_text()==p["abstract"]+"\n"
    assert len(p["abstract"].split())>100

reading=load("reading.json")
for r in reading["images_actually_viewed"]:
    assert sha((D/r["file"]).read_bytes())==r["sha256"]
for r in reading["auxiliary_text_scopes"]:
    b=(D/r["file"]).read_bytes()
    assert sha(b)==r["sha256"]
    a,z=r["char_range"]
    assert 0<=a<z<=len(b.decode())
assert reading["body_pages_read"]==0
assert sum(p["pdf_pages"] for p in papers)==64
assert sum(p["screening"]["decision"]=="candidate" for p in papers)==2
assert sum(p["screening"]["decision"]=="reference" for p in papers)==4

report={"verified_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":"PASS","new_full_primary_abstracts":6,"public_pdfs":4,"archived_pdf_pages":64,"body_pages_read":0,"viewed_images":5,"new_http_requests":12,"successful_http_responses":11,"failed_http_responses":1,"candidate":2,"reference":4,"excluded":0,"downloaded_code_executed":False,"network_used_by_verifier":False,"verification_boundary":"Byte/range/extraction/identity-key consistency plus manually recorded visual checks; does not independently prove image transcription semantics or paper performance claims."}
(D/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False))
