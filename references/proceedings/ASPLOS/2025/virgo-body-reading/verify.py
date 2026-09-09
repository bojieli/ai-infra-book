#!/usr/bin/env python3
"""Read-only evidence checks for this bounded Virgo reading bundle.

Requires Python standard library and Poppler pdfinfo/pdftotext on PATH.
Does not run third-party code, a simulator, an artifact, or a GPU workload.
Prints JSON to stdout; caller may explicitly redirect it to a result file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_bundle(root=None, bundle_path=None):
    root = Path(root or ".").resolve()
    bundle = Path(bundle_path).expanduser() if bundle_path else Path(__file__).resolve().parent
    if not bundle.is_absolute():
        bundle = root / bundle
    bundle = bundle.resolve()
    failures = []
    checks = []
    warnings = []

    def check(name, condition, detail=None):
        record = {"check": name, "ok": bool(condition)}
        if detail is not None:
            record["detail"] = detail
        checks.append(record)
        if not condition:
            failures.append(name)

    manifest = json.loads((bundle / "FOLDER-MANIFEST.json").read_text())
    for item in manifest["files"]:
        path = bundle / item["file"]
        data = path.read_bytes() if path.is_file() else b""
        check("file:" + item["file"], path.is_file() and len(data) == item["bytes"] and digest(data) == item["sha256"])

    pdf = bundle / "virgo-v2.pdf"
    inherited = json.loads((bundle / "inherited-identity-provenance.json").read_text())
    check("original_download_bytes", digest(pdf.read_bytes()) == inherited["selected_source"]["sha256"])
    check("fixed_version_url", inherited["selected_source"]["url"] == "https://arxiv.org/pdf/2408.12073v2")
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True)
    check("pdfinfo_exit", info.returncode == 0)
    counts = [line.split(":", 1)[1].strip() for line in info.stdout.decode().splitlines() if line.startswith("Pages:")]
    check("physical_page_count", counts == ["18"])

    page_sets = {}
    for mode, flags, textfile in [("default", [], "virgo-v2.txt"), ("layout", ["-layout"], "virgo-v2.layout.txt")]:
        result = subprocess.run(["pdftotext", *flags, str(pdf), "-"], capture_output=True)
        check("extract_exit:" + mode, result.returncode == 0)
        check("extract_bytes:" + mode, result.stdout == (bundle / textfile).read_bytes())
        if result.stderr:
            warnings.append({"command": "pdftotext " + mode, "stderr": result.stderr.decode(errors="replace"), "scope": "Warning retained; no assertion of lossless extraction of unviewed material."})
        check("extract_warning_record:" + mode, result.stderr == (bundle / ("extract-" + mode + ".stderr.txt")).read_bytes())
        pages = result.stdout.decode().split("\f")
        check("page_chunks:" + mode, len(pages) == 19 and not pages[-1].strip())
        page_sets[mode] = pages
        for number, content in enumerate(pages[:18], 1):
            check("derived_page:%02d:%s" % (number, mode), content == (bundle / ("page-%02d.%s.txt" % (number, mode))).read_text())

    first = " ".join(page_sets["default"][0].split())
    check("pdf_doi_identity", "10.1145/3676641.3716281" in first)
    check("pdf_arxiv_v2_identity", "2408.12073v2" in first)
    check("pdf_title_identity", inherited["prior_identity"]["title"] in first)
    for author in inherited["prior_identity"]["authors"]:
        check("pdf_author:" + author, author in first)

    proof = json.loads((bundle / "reading-proof.json").read_text())
    check("declared_partial_scope", proof["full_pdf_read"] is False and proof["main_body_physical_pages"] == list(range(2, 15)) and proof["appendix_physical_pages"] == [15, 16])
    for item in proof["page_reading"]:
        data = (bundle / item["default_text"]).read_bytes()
        check("reading_page_hash:%02d" % item["physical_pdf_page"], digest(data) == item["default_sha256"])
        check("reading_line_range:%02d" % item["physical_pdf_page"], item["default_lines_read"] == [1, len(data.decode().splitlines())])
    viewed = {item["physical_page"]: item for item in proof["actually_viewed_full_page_images"]}
    check("declared_viewed_pages", sorted(viewed) == [2, 4, 5, 8, 10, 11, 12, 13, 14])
    for item in json.loads((bundle / "figures.json").read_text()):
        check("figure_image:" + item["id"], digest((bundle / item["file"]).read_bytes()) == item["sha256"])
        check("figure_page_image:" + item["id"], digest((bundle / item["source_page_image"]).read_bytes()) == item["source_page_sha256"])
        check("figure_view_scope:" + item["id"], item["physical_pdf_page"] in viewed and item["verified_visually_in_full_page"] and item["crop_separately_viewed"] is False)

    arithmetic = subprocess.run([sys.executable, str(bundle / "check_budget.py")], capture_output=True)
    check("own_budget_script_exit", arithmetic.returncode == 0)
    check("own_budget_result", arithmetic.returncode == 0 and json.loads(arithmetic.stdout) == json.loads((bundle / "budget-results.json").read_text()))
    return {
        "status": "passed_with_explicit_scope_limits" if not failures else "failed",
        "bundle": str(bundle),
        "checked_manifest_files": len(manifest["files"]),
        "check_count": len(checks),
        "failures": failures,
        "warnings": warnings,
        "limits": [
            "Hash and extraction checks prove evidence integrity, not that unselected pages were read.",
            "Visual reading is an agent-declared scope, supported by archived original PDF and page/figure images.",
            "No third-party source, RTL simulation, GPU kernel, framework or model was executed.",
            "FP32 total MAC configuration and Virgo kernel accumulator type remain unverified source-level conditions.",
            "Published power/area estimates cannot be independently regenerated from the supplied public artifact description alone."
        ],
        "checks": checks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", nargs="?", help="Bundle directory; defaults to this script's directory")
    args = parser.parse_args()
    output = verify_bundle(bundle_path=args.bundle)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    raise SystemExit(1 if output["failures"] else 0)
