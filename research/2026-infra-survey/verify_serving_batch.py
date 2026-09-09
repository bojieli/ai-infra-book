"""Verify primary sources and exact limited POD reading; no model execution."""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import unicodedata
from bs4 import BeautifulSoup
from verify_comet_reading import verify as verify_comet
from verify_tapas_reading import verify as verify_tapas

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "references/proceedings/ASPLOS/2025/serving-113-117"


def norm(s):
    return re.sub("[^a-z0-9]", "", unicodedata.normalize("NFKD", s).casefold())


def check(item):
    data = (ROOT / item["file"]).read_bytes()
    assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]


def verify():
    comet = verify_comet()
    tapas = verify_tapas()
    sources = json.loads((D / "sources.json").read_text())
    for s in sources:
        check(s)
    batch = json.loads((D / "screening.json").read_text())
    papers = {p["program_order"]: p for p in json.loads((D.parent / "manifest.json").read_text())["papers"]}
    for r in batch["records"]:
        soup = BeautifulSoup((ROOT / r["source"]["file"]).read_bytes(), "html.parser")
        block = soup.select_one("blockquote.abstract")
        block.select_one(".descriptor").decompose()
        text = block.get_text(" ", strip=True)
        assert text == r["abstract"] and hashlib.sha256(text.encode()).hexdigest() == r["abstract_sha256"]
        assert soup.select_one("meta[name=citation_title]")["content"] == r["source_title"]
        assert [m["content"] for m in soup.select("meta[name=citation_author]")] == r["source_authors"]
        assert soup.select_one(".submission-history").get_text(" ", strip=True) == r["history"]
        for key in ("source", "abstract_file", "pdf", "view"):
            check(r[key])
        assert (ROOT / r["abstract_file"]["file"]).read_text() == text + "\n"
        pdf = ROOT / r["pdf"]["file"]
        page = subprocess.check_output(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"], stderr=subprocess.PIPE)
        assert page == (ROOT / r["pdf"]["first_page_text"]["file"]).read_bytes()
        info = subprocess.check_output(["pdfinfo", str(pdf)], stderr=subprocess.PIPE).decode()
        assert int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1)) == r["pdf"]["pages"]
        check(r["pdf"]["text"])
        assert norm(r["formal_title"]) in norm(page.decode())
        paper = papers[r["program_order"]]
        assert paper["title"] == r["formal_title"] and paper["doi"] == r["formal_doi"]
        for author in paper["author_metadata"]:
            assert norm(author.get("given", "") + " " + author["family"]) in norm(page.decode())
        assert (paper["doi"] in page.decode()) == r["identity"]["formal_doi_printed_on_page1"]
    proof = json.loads((D / "pod-reading.json").read_text())
    check(proof["pdf"])
    for p in proof["pages"]:
        check(p)
        n = str(p["physical_page"])
        data = subprocess.check_output(["pdftotext", "-f", n, "-l", n, str(ROOT / proof["pdf"]["file"]), "-"], stderr=subprocess.PIPE)
        assert data == (ROOT / p["file"]).read_bytes()
    for p in proof["figures"]:
        check(p)
        assert p["actually_viewed"]
    assert [p["physical_page"] for p in proof["pages"]] == [4, 5, 6, 7, 8]
    assert [p["physical_page"] for p in proof["figures"]] == [5, 6, 7]
    ctas = [batch_size * 4 for batch_size in (54, 55)]
    waves = [math.ceil(n / 108) for n in ctas]
    assert ctas == [216, 220] and waves == [2, 3] and ctas[1] % 108 == 4
    serial = max(100, 10) + max(10, 100)
    concurrent_lower_bound = max(100 + 10, 10 + 100)
    assert serial == 200 and concurrent_lower_bound == 110
    result = {"status": "passed", "responses": len(sources), "failed_responses": sum(s["status_code"] != 200 for s in sources), "abstracts": 3, "representative_pdf_pages": 44, "pod_selected_pages": 5, "canonical_merge_pending": True, "arithmetic": {"ctas": ctas, "simplified_waves": waves, "toy_serial_time": serial, "toy_concurrent_resource_lower_bound": concurrent_lower_bound, "not_measured_latency": True}}
    result["comet_selected_pages"] = comet["selected_body_pages"]
    result["tapas_selected_pages"] = tapas["selected_body_pages"]
    (D / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
