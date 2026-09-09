"""Primary title/author/DOI checks for the preserved 77–110 deliveries."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "references/proceedings/ASPLOS/2025"


def norm(text):
    return re.sub("[^a-z0-9]", "", unicodedata.normalize("NFKD", text).casefold())


def verify():
    from verify_pending_asplos import verify_bundle
    papers = {p["program_order"]: p for p in json.loads((D / "manifest.json").read_text())["papers"]}
    output = []
    for batch in ("077-090", "091-110"):
        path = D / "pending-077-110" / batch / "bundle.json"
        verify_bundle(path)
        bundle = json.loads(path.read_text())
        for record in bundle["records"]:
            n = record["program_order"]
            paper = papers[n]
            texts, evidence = [], []
            source = ROOT / record["source_file"]
            if source.suffix == ".html":
                soup = BeautifulSoup(source.read_bytes(), "html.parser")
                texts.append(soup.get_text(" ", strip=True) + " " + " ".join(t.get("content", "") for t in soup.select("meta")) + " " + " ".join(t.get("href", "") for t in soup.select("a")))
                evidence.append({"file": str(source.relative_to(ROOT)), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
            if "representative_pdf" in record:
                pdf = record["representative_pdf"]
                page = str(pdf.get("abstract_physical_page", 1))
                texts.append(subprocess.check_output(["pdftotext", "-f", page, "-l", page, str(ROOT / pdf["file"]), "-"], stderr=subprocess.PIPE).decode())
                evidence.append({"file": pdf["file"], "sha256": pdf["sha256"], "physical_page": int(page)})
            if n == 98:
                cite = path.parent / "paper-098-cite.html"
                texts.append(cite.read_text())
                evidence.append({"file": str(cite.relative_to(ROOT)), "sha256": hashlib.sha256(cite.read_bytes()).hexdigest()})
            combined = " ".join(texts)
            normalized = norm(combined)
            expected_title = paper["title"]
            if n == 77:
                assert norm(record["title"]) in normalized
                assert norm(record["title"].replace("GPU Direct and RoCE", "GPU Direct RoCE")) == norm(expected_title)
            else:
                assert norm(expected_title) in normalized, (n, "title")
            for author in paper["author_metadata"]:
                first, last = author.get("given", ""), author["family"]
                assert norm(first + " " + last) in normalized or norm(last + " " + first) in normalized, (n, first, last)
            doi_present = paper["doi"].casefold() in combined.casefold()
            assert doi_present or n in {93, 96, 98}, (n, "DOI")
            output.append({
                "program_order": n,
                "official_doi": paper["doi"],
                "complete_author_names_located": True,
                "primary_doi_present": doi_present,
                "identity_basis": "primary_title_complete_authors_and_doi" if doi_present else "author_version_title_and_complete_authors_only_no_primary_doi",
                "title_variant": "IBM inserts and before RoCE" if n == 77 else None,
                "source_evidence": evidence,
                "version_notes": record["version_notes"],
                "publisher_byte_identity_claimed": False,
            })
    assert len(output) == 30
    result = {"status": "qualified_primary_identity_checks_passed", "scope": "Paper association, not proof that preprints equal publisher versions. Full abstract re-extraction checked separately. No performance claims validated.", "records": output}
    (D / "pending-077-110/identity-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = verify()
    print(result["status"], len(result["records"]))
