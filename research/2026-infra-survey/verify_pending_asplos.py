"""Re-extract archived handoff abstracts; do not award reading/identity credit.

Uses local primary HTML/PDF bytes, never the delivered build scripts. PDF text
is regenerated with Poppler. Identity findings are evidence locators, not an
assertion that title, author list, and version have all been adjudicated.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unicodedata

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "references/proceedings/ASPLOS/2025/pending-077-110"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"[^a-z0-9]", "", value)


def pdf_text(path, raw=False):
    args = ["pdftotext", "-f", "1", "-l", "1"]
    if raw:
        args.append("-raw")
    return subprocess.check_output(args + [str(path), "-"], stderr=subprocess.PIPE).decode()


def extract(record, first_batch):
    n = record["program_order"]
    path = ROOT / record["source_file"]
    data = path.read_bytes()
    assert digest(data) == record["source_sha256"], (n, "source hash")
    if path.suffix == ".html":
        soup = BeautifulSoup(data, "html.parser")
        block = soup.select_one("blockquote.abstract")
        if block is not None:
            descriptor = block.select_one(".descriptor")
            if descriptor is not None:
                descriptor.extract()
        elif n == 89:
            block = soup.select_one("section.page__content > p")
        elif n in (102, 104):
            block = soup.select_one("div.textblock")
        elif n == 91:
            block = soup.select_one(".pub-abstract,.article-style,.textblock")
        elif n == 98:
            heading = next(t.parent for t in soup.find_all(string=True) if t.strip() == "Abstract")
            block = heading.find_next_sibling("div")
        else:
            heading = next(h for h in soup.find_all(["h2", "h3"]) if h.get_text(strip=True) == "Abstract")
            block = heading.find_next_sibling()
        assert block is not None, (n, "abstract element")
        abstract = block.get_text(" ", strip=True)
        identity_text = soup.get_text(" ", strip=True) + " " + " ".join(
            tag.get("content", "") for tag in soup.find_all("meta")
        ) + " " + " ".join(tag.get("href", "") for tag in soup.find_all("a"))
    else:
        identity_text = pdf_text(path, first_batch)
        a = identity_text.split("Abstract\n", 1)[1]
        if first_batch:
            abstract = a.split("CCS Concepts:", 1)[0]
            if n == 81:
                abstract = re.sub(
                    r"∗corresponding authors\nPermission.*?https://doi.org/10.1145/3669940.3707231\n",
                    "", abstract, flags=re.S,
                )
        elif n == 92:
            abstract = a.split("\n\nCXL + multi-hops", 1)[0]
        elif n in (99, 106):
            abstract = a.split("Permission to make digital", 1)[0]
        elif n == 100:
            abstract = a.split("\n\nFigure 1.", 1)[0]
        elif n == 103:
            continuation = "optimization interactions. Subsequently,"
            abstract = a.split("∗ National Engineering Research Center", 1)[0] + continuation + a.split(continuation, 1)[1].split("Keywords:", 1)[0]
        elif n == 108:
            abstract = a.split("ACM Reference Format:", 1)[0]
        elif n == 110:
            continuation = "the baseline on average."
            abstract = a.split("Permission to make digital", 1)[0] + continuation + a.split(continuation, 1)[1].split("CCS Concepts:", 1)[0]
        else:
            abstract = a.split("CCS Concepts:", 1)[0]
        abstract = abstract.strip()
    assert abstract == record["abstract"], (n, "re-extracted abstract differs")
    assert digest(abstract.encode()) == record["abstract_sha256"], (n, "abstract hash")
    assert (ROOT / record["abstract_text_file"]["file"]).read_text() == abstract + "\n", (n, "abstract file")
    return identity_text


def verify_bundle(bundle_path):
    bundle = json.loads(bundle_path.read_text())
    first_batch = bundle_path.parent.name == "077-090"
    file_objects = 0

    def verify_files(value):
        nonlocal file_objects
        if isinstance(value, dict):
            if all(key in value for key in ("file", "bytes", "sha256")):
                data = (ROOT / value["file"]).read_bytes()
                assert len(data) == value["bytes"], value["file"]
                assert digest(data) == value["sha256"], value["file"]
                file_objects += 1
            for child in value.values():
                verify_files(child)
        elif isinstance(value, list):
            for child in value:
                verify_files(child)

    verify_files(bundle)
    official = {p["program_order"]: p for p in json.loads((ARCHIVE.parent / "manifest.json").read_text())["papers"]}
    results = []
    for record in bundle["records"]:
        n = record["program_order"]
        primary_text = extract(record, first_batch)
        p = record.get("representative_pdf")
        representative_text = ""
        if p:
            path = ROOT / p["file"]
            info = subprocess.check_output(["pdfinfo", str(path)], stderr=subprocess.PIPE).decode()
            pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
            assert pages == p["pages"], (n, "PDF page count")
            regenerated = pdf_text(path, first_batch)
            representative_text = regenerated
            if p.get("abstract_physical_page", 1) != 1:
                page = str(p["abstract_physical_page"])
                representative_text = subprocess.check_output(
                    ["pdftotext", "-f", page, "-l", page, str(path), "-"], stderr=subprocess.PIPE,
                ).decode()
            assert regenerated == (ROOT / p["first_page_text"]["file"]).read_text(), (n, "PDF first-page text")
        alt = record.get("alternate_abstract")
        if alt:
            s = BeautifulSoup((ROOT / alt["source"]["file"]).read_bytes(), "html.parser")
            a = s.select_one("div.textblock").get_text(" ", strip=True)
            assert a == alt["abstract"] and digest(a.encode()) == alt["abstract_sha256"], (n, "alternate abstract")
        # Never rely on the handoff's unconditional author/title match booleans.
        source_norm = normalized(primary_text)
        paper = official[n]
        family_names = [a["family"] for a in paper["author_metadata"]]
        results.append({
            "program_order": n,
            "abstract_reextraction": "exact_match",
            "primary_title_normalized_substring": normalized(paper["title"]) in source_norm,
            "primary_doi_literal_present": paper["doi"].casefold() in primary_text.casefold(),
            "representative_pdf_doi_literal_present": paper["doi"].casefold() in representative_text.casefold() if p else None,
            "author_families_not_located_in_primary_text": [name for name in family_names if normalized(name) not in source_norm],
            "identity_status": "pending_editorial_review_even_if_text_locators_match",
        })
    assert len(results) == bundle["new_full_abstracts"]
    assert sum("representative_pdf" in r for r in bundle["records"]) == bundle["new_representative_pdfs"]
    assert sum(r["representative_pdf"]["pages"] for r in bundle["records"] if "representative_pdf" in r) == bundle["new_representative_pdf_pages"]
    responses = [s for s in bundle["sources"] if isinstance(s.get("status_code"), int)]
    return {
        "bundle": str(bundle_path.relative_to(ROOT)),
        "bundle_sha256": digest(bundle_path.read_bytes()),
        "verified_file_objects": file_objects,
        "abstracts_reextracted": len(results),
        "representative_pdfs_checked": bundle["new_representative_pdfs"],
        "representative_pdf_pages_checked": bundle["new_representative_pdf_pages"],
        "http_responses": len(responses),
        "transport_errors_separate_from_http": len(bundle["sources"]) - len(responses),
        "records": results,
    }


def main():
    paths = [ARCHIVE / batch / "bundle.json" for batch in ("077-090", "091-110")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        batches = list(pool.map(verify_bundle, paths))
    result = {
        "status": "abstract_reextraction_and_file_integrity_passed_identity_review_pending",
        "canonical_reading_counts_changed": False,
        "selected_body_reading_credit_added": 0,
        "batches": batches,
    }
    (ARCHIVE / "reextraction-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "abstracts": sum(b["abstracts_reextracted"] for b in batches), "pdfs": sum(b["representative_pdfs_checked"] for b in batches)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
