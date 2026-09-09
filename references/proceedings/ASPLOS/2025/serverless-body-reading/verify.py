#!/usr/bin/env python3
"""Offline independent verification. No downloaded module is imported or run."""
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import subprocess
import tempfile

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
data = json.loads((P / "reading-records.json").read_text())
manifest = json.loads((P.parent / "manifest.json").read_text())
seen = set()

def check_proof(item):
    path = (ROOT / item["file"]).resolve()
    assert path.is_relative_to(ROOT), path
    raw = path.read_bytes()
    assert len(raw) == item["bytes"], item["file"]
    assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["file"]
    seen.add(item["file"])
    return raw

def walk(obj):
    if isinstance(obj, dict):
        if {"file", "bytes", "sha256"} <= obj.keys():
            check_proof(obj)
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)

def normalize(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

walk(data)
assert data["new_full_abstracts"] == data["new_representative_pdfs"] == data["new_pdf_pages"] == 0
assert {r["program_order"] for r in data["records"]} == {171, 172}
assert len({r["doi"] for r in data["records"]}) == 2
assert data["selected_physical_pages"] == 17
assert data["main_text_pages"] + data["artifact_appendix_pages"] == 17

pages_checked = 0
images_checked = 0
pdf_identity_checks = []
for record in data["records"]:
    entry = next(p for p in manifest["papers"] if p["program_order"] == record["program_order"])
    assert entry["doi"] == record["doi"]
    assert normalize(entry["title"]) == normalize(record["title"])
    pdf = ROOT / record["existing_source_pdf"]["file"]
    response = record["existing_pdf_response"]
    assert response["status_code"] == 200
    assert response["file"] == record["existing_source_pdf"]["file"]
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    assert int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1)) == record["existing_source_pdf"]["pages"]
    first = subprocess.check_output(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"], text=True)
    normalized = normalize(first)
    assert normalize(record["doi"]) in normalized
    assert normalize(record["title"]) in normalized
    for name in record["authors"]:
        assert normalize(name) in normalized, name
    assert record["full_paper_read"] is False
    assert set(map(int, record["page_text"])) == set(record["physical_pdf_pages"])
    for page, item in record["page_text"].items():
        # Re-extract from the independently hash-checked original PDF, without reusing full-text archives.
        extracted = subprocess.check_output(["pdftotext", "-f", page, "-l", page, str(pdf), "-"])
        assert extracted == check_proof(item), (record["program_order"], page)
        pages_checked += 1
    for page, item in record["viewed_page_images"].items():
        png = check_proof(item)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", png[16:24])
        assert min(width, height) >= 1000
        assert item["actually_viewed"] and item["observation"]
        assert int(page) in record["physical_pdf_pages"]
        images_checked += 1
    pdf_identity_checks.append({"program_order": record["program_order"], "doi": record["doi"], "authors_checked": len(record["authors"]), "status": "pass"})
assert pages_checked == 17 and images_checked == 9

sources = {s["id"]: s for s in data["sources"]}
assert len(sources) == 6
for s in sources.values():
    assert s["status_code"] in [200, 404]
    assert s["retrieved_at"] and s["url"] and s["final_url"]
assert sources["dilu-vertical-readme"]["status_code"] == 404
assert check_proof(sources["dilu-vertical-readme"]) == b"404: Not Found"
for record in data["records"]:
    label = "dilu" if record["program_order"] == 171 else "medusa"
    head = json.loads(check_proof(sources[label + "-github-head"]))
    assert head["sha"] == record["framework_commit"]
    readme = sources[label + "-readme"]
    assert readme["status_code"] == 200 and readme["commit"] == head["sha"]
    assert f"/{head['sha']}/README.md" in readme["url"]
    assert readme["repo"] == record["framework_repo"]
    if label == "dilu":
        assert "simplified reference implementation" in check_proof(readme).decode()
    else:
        text = check_proof(readme).decode()
        assert "PyTorch-Medusa" in text and "SPDK" in text and "550.54.14" in text
        init = sources["medusa-vllm-init"]
        assert f"/{head['sha']}/vllm/__init__.py" in init["url"]
        assert re.search(r'__version__\s*=\s*"0\.3\.1"', check_proof(init).decode())

# Compare retained HTTP logs with the normalized packet, including the failed response.
for filename in ["source-jobs.json.results.json", "pinned-jobs.json.results.json", "detail-jobs.json.results.json"]:
    for log in json.loads((P / filename).read_text()):
        source = sources[log["id"]]
        for key in ["url", "final_url", "status_code", "bytes", "sha256", "retrieved_at"]:
            assert source[key] == log[key]
        assert Path(log["file"]).name == Path(source["file"]).name

c = json.loads((P / "calculations.json").read_text())
page = (P / "172-author-paper.p10.txt").read_text()
for anchor in ["0.85s", "0.39s", "0.21s", "0.50s", "0.90s", "0.47s", "0.52s", "0.23s", "0.02s", "0.31s", "0.42s", "0.26s", "2.85s", "2.48s", "1.67s"]:
    assert anchor in page, anchor
v, a, m = [c["inputs"][key] for key in ["vanilla", "async", "medusa"]]
vanilla = sum(v.values())
asynchronous = a["structure"] + max(a["weights"], a["tokenizer"] + a["kv"]) + a["capture"]
branch = max(m["weights"], m["tokenizer"] + m["kv"] + m["warmup"])
materialized = m["structure"] + branch + m["restore"]
computed = {
    "vanilla_loading_s": vanilla,
    "async_loading_s": asynchronous,
    "async_bubble_s": max(0, a["tokenizer"] + a["kv"] - a["weights"]),
    "async_weights_interference_s": a["weights"] - v["weights"],
    "medusa_loading_s": materialized,
    "medusa_post_structure_branch_s": branch,
    "kv_initialization_saving_s": v["kv"] - m["kv"],
    "graph_work_saving_before_overlap_s": v["capture"] - m["warmup"] - m["restore"],
    "medusa_loading_saving_s": vanilla - materialized,
    "medusa_reduction_vs_vanilla_fraction": 1 - materialized / vanilla,
    "medusa_reduction_vs_async_fraction": 1 - materialized / asynchronous,
    "async_reduction_vs_vanilla_fraction": 1 - asynchronous / vanilla,
}
assert set(computed) == set(c["expected"])
for key, value in computed.items():
    assert math.isclose(value, c["expected"][key], rel_tol=1e-12, abs_tol=1e-12), key

result = {
    "status": "pass", "file_proofs_checked": len(seen), "formal_identity_checks": pdf_identity_checks,
    "original_pdf_pages_reextracted": pages_checked, "viewed_png_files_verified": images_checked,
    "visual_review_limit": "The verifier checks images and recorded human/model observations; actual visual review is not machine-proven.",
    "new_source_responses": 6, "http_200": 5, "http_404": 1,
    "existing_pdf_responses_verified": 2, "pinned_repositories": 2,
    "static_medusa_fork_version": "0.3.1", "independent_calculations": computed,
    "new_abstracts": 0, "new_pdfs": 0,
    "scope_limit": "17 selected pages (16 main text + one appendix), not full papers; static metadata/source read only, no third-party execution or runtime reproduction."
}
(P / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
