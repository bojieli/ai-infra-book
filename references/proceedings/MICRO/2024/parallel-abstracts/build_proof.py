"""Self-written evidence bookkeeping; downloaded code is never executed."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess

D = Path(__file__).resolve().parent
now = datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_json(name, value):
    (D / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


manifest = json.loads((D / "input-manifest.json").read_text())
original = {p["program_order"]: p for p in manifest["papers"]}
seen = {p["program_order"] for p in json.loads((D / "input-public-abstracts.json").read_text())["papers"]}
selection = [41, 53, 87, 88, 111, 119]
assert not set(selection) & seen
source_rows = json.loads((D / "sources.json").read_text())
source_by_file = {r["file"]: r for r in source_rows}

# Retain the unmodified OCR, and make the sole image-checked correction explicit.
ocr = (D / "paper-041-abstract-ocr.txt").read_text()
assert ocr.count("1.95 energy") == 1
corrected = ocr.replace("1.95 energy", "1.95× energy")
(D / "paper-041-abstract-transcription.txt").write_text(corrected)
correction = {"raw_file": "paper-041-abstract-ocr.txt", "corrected_file": "paper-041-abstract-transcription.txt", "corrections": [{"before": "1.95 energy", "after": "1.95× energy", "basis": "Visual check against paper-041-abstract-crop.png; missing multiplication sign only"}], "ocr_is_not_primary_bytes": True}
write_json("ocr-correction.json", correction)

decisions = {
    41: ("candidate", "低位宽值组合重复是否值得由计数合并；待读计数、转换与搬运成本、等资源基线和质量条件，不当作现有 GPU 能力。", "4"),
    53: ("reference", "依赖信息驱动多 chiplet 隐式同步可作背景，但需要 CP／硬件配合；现有同步与 NoC 案例优先，不扩展一致性专题。", "4/5"),
    87: ("reference", "并行度与活跃状态的约束有启发；通用无序数据流／仿真不等同 GPU occupancy 或模型 token 调度，现有容量—并发推导优先。", "4/5"),
    88: ("candidate", "生产者—消费者与跨迭代稀疏数据复用可深化跨算子减少搬运；待读表示、依赖、缓冲和专用数据流，不把 STA 性能套到 attention／MoE。", "5"),
    111: ("reference", "区分三种异构访存路径可作 CXL 背景；摘要应用是 zswap／ksm／Redis，不能直接用作 LLM KV 池评估。", "4/9"),
    119: ("reference", "LNS 与 outlier 的格式—执行匹配可作量化背景；摘要未给四模型具体口径，不采用精度百分比或下一代芯片预测。", "4/8"),
}
versions = {
    41: "Author-hosted 13-page image PDF linked alongside DOI by coauthor; no publisher DOI/page footer on checked first page; not asserted version of record.",
    53: "18-page author prepublication copy; first page explicitly says To Appear in 57th IEEE/ACM International Symposium on Microarchitecture.",
    87: "17-page coauthor-hosted manuscript; publisher title differs from earlier program; CMU institution abstract corroborates MICRO 2024. Brian Schwedock Samsung affiliation/work-at-CMU footnote preserved.",
    88: "16-page author-hosted manuscript; title and three authors match publisher identity. Not 2020 SparsePipe point-cloud paper; no final publisher page footer claimed.",
    111: "Coauthor full abstract page marked November 2024, matching 11 publisher authors; PDF unavailable in this bounded pass (publisher HTTP 418).",
    119: "PNNL institution full abstract/citation; page published 2025-01-08, conference/citation 2024. No public PDF obtained; original 'bright this gap' wording preserved.",
}
pdf_methods = {
    41: {"kind": "image_ocr_with_manual_check", "source_text": "paper-041-abstract-transcription.txt", "first_page_text": "paper-041-first-page.txt", "render_command": ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-r", "300", "-x", "190", "-y", "1310", "-W", "1035", "-H", "670", "-png", "paper-041.pdf", "paper-041-abstract-crop"], "ocr_command": ["tesseract", "paper-041-abstract-crop.png", "paper-041-abstract-ocr", "-l", "eng", "--psm", "6"], "correction_file": "ocr-correction.json"},
}
papers = []
for n in selection:
    p = original[n]
    decision, reason, chapters = decisions[n]
    entry = {"program_order": n, "doi": p["doi"], "publisher_title": p["publisher_title"], "program_title": p["program_title"], "publisher_authors": p["publisher_authors"], "publisher_pages": p["page"], "previous_reading_status": p["reading_status"], "reading_status": "abstract_screened", "read_scope": {"complete_abstract": True, "body_read": False, "scope": "Full primary abstract and bibliographic identity only; adjacent introduction/figures are not body reading."}, "screening": {"basis": "title_and_full_abstract", "decision": decision, "reason": reason, "possible_chapters_if_later_justified": chapters, "outline_changed": False}, "version": versions[n]}
    if n in [41, 53, 87, 88]:
        pdf = f"paper-{n:03d}.pdf"
        info = subprocess.check_output(["pdfinfo", str(D / pdf)], text=True)
        (D / f"paper-{n:03d}-pdfinfo.txt").write_text(info)
        pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
        entry.update({"source_kind": "author_public_pdf", "source_file": pdf, "source_url": source_by_file[pdf]["url"], "source_sha256": sha((D / pdf).read_bytes()), "pdf_pages": pages, "abstract_physical_pages": [1], "identity_viewed_image": f"paper-{n:03d}-identity.png", "identity_note": "Full first-page title and author block visually checked against input publisher metadata; no body claim."})
        if n == 41:
            method = pdf_methods[41]
        else:
            method = {"kind": "poppler_left_half_first_page", "source_text": f"paper-{n:03d}-left-column.txt", "command": ["pdftotext", "-f", "1", "-l", "1", "-x", "0", "-y", "0", "-W", "306", "-H", "792", pdf, "-"], "first_page_text": f"paper-{n:03d}-first-page.txt"}
        entry["extraction"] = method
        text_file = method["source_text"]
        text = (D / text_file).read_text()
        match = re.search(r"(?i)(?:A BSTRACT|Abstract)[—\s]*", text)
        start = match.end()
        end = len(text) if n == 41 else start + re.search(r"(?i)(?:Index Terms|Keywords)", text[start:]).start()
    else:
        raw = "cxl2-author.html" if n == 111 else "lns-institution.html"
        text_file = raw.replace(".html", ".txt")
        text = (D / text_file).read_text()
        start = text.index("Abstract\n") + len("Abstract\n")
        end = text.index("Type\n", start) if n == 111 else text.index("Published:", start)
        entry.update({"source_kind": "author_html" if n == 111 else "institution_html", "source_file": raw, "source_url": source_by_file[raw]["url"], "source_sha256": sha((D / raw).read_bytes()), "pdf_pages": 0, "abstract_physical_pages": [], "extraction": {"kind": "beautifulsoup_html_text", "remove_tags": ["script", "style"], "separator": "\n", "strip": True, "trailing_newline": True, "newline_normalization": "CRLF/CR to LF"}})
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end-1].isspace():
        end -= 1
    abstract = text[start:end]
    name = f"paper-{n:03d}-abstract.txt"
    (D / name).write_text(abstract + "\n")
    entry.update({"abstract_text_file": text_file, "abstract_text_sha256": sha((D / text_file).read_bytes()), "abstract_char_range": [start, end], "abstract_file": name, "abstract": abstract, "abstract_sha256": sha(abstract.encode()), "abstract_complete_boundary": "Abstract heading through final abstract sentence before keywords/next field; visually checked for PDFs or checked against full HTML field"})
    papers.append(entry)
write_json("abstracts.json", {"recorded_at": now, "scope": "Six new complete primary abstracts only; four public PDFs totaling 64 pages are archived, not read as full bodies", "input_manifest_sha256": sha((D / "input-manifest.json").read_bytes()), "input_abstracts_sha256": sha((D / "input-public-abstracts.json").read_bytes()), "downloaded_code_executed": False, "papers": papers})

# Explicitly record only selected identity/full-abstract scopes for corroborating HTML.
aux = []
for name, anchor, end_anchor in [
    ("tyr-institution.txt", "The TYR Dataflow Architecture", "KEYWORDS:"),
    ("cambricon-c-author.txt", "Published at MICRO 2024.", None),
    ("lns-author-lab.txt", '"Bridging the Gap Between LLMs and LNS', None),
    ("lns-coauthor.txt", "Bridging the Gap Between LLMs and LNS", None),
    ("cxl2-first-author.txt", "Demystifying a CXL Type-2 Device", None),
]:
    text = (D / name).read_text()
    start = text.find(anchor)
    if start < 0 and name == "lns-author-lab.txt":
        start = text.index("Bridging the Gap Between LLMs and LNS")
    assert start >= 0, name
    end = text.index(end_anchor, start) if end_anchor else min(len(text), start + 650)
    aux.append({"file": name, "sha256": sha((D / name).read_bytes()), "char_range": [start, end], "scope": "Institution full abstract and identity corroboration; same paper not counted twice" if name.startswith("tyr") else "Title/venue/link locator only; nearby homepage text is not additional reading"})
write_json("reading.json", {"recorded_at": now, "selected_papers": selection, "pdf_identity_and_abstract_pages": {str(n): [1] for n in [41,53,87,88]}, "images_actually_viewed": [{"file": name, "sha256": sha((D/name).read_bytes()), "purpose": "First-page identity and abstract boundary" if "identity" in name else "Cambricon-C abstract OCR verification"} for name in ["paper-041-identity.png", "paper-053-identity.png", "paper-087-identity.png", "paper-088-identity.png", "paper-041-abstract-crop.png"]], "auxiliary_text_scopes": aux, "body_pages_read": 0, "not_claimed": ["PDF metadata page count is not body reading", "Search-result snippets only locate primary sources", "Unselected abstracts and papers are not added", "No model/hardware claims beyond screened primary abstracts are adopted"]})
write_json("acquisition-notes.json", {"recorded_at": now, "failures": [{"file": "cxl2-publisher-pdf.response", "http_status": 418, "counted_as_pdf": False, "action": "Preserved response; no retry/bypass; coauthor primary abstract retained"}], "pdf_not_obtained": [{"program_order": 111, "reason": "Both checked author pages link IEEE; ordinary public PDF endpoint returned 418"}, {"program_order": 119, "reason": "PNNL full abstract, author laboratory and coauthor publication entries checked; no public PDF link obtained in bounded pass"}], "identity_cautions": [{"program_order": 87, "note": "CMU full-paper href points to ACMToS-0920.pdf; target not retrieved or asserted to be this paper; matched coauthor manuscript used"}, {"program_order": 88, "note": "2020 point-cloud SparsePipe is a distinct paper and not fetched or counted"}, {"program_order": 41, "note": "Image PDF: default extraction yields only a form feed; first OCR contains layout artifacts and is preserved unused; cropped OCR is image-checked with one declared correction"}, {"program_order": 119, "note": "Institution webpage date 2025-01-08 differs from 2024 conference date; original wording preserved"}], "retrieval_count": len(source_rows), "http_status_counts": {str(k): sum(r["status"]==k for r in source_rows) for k in sorted({r["status"] for r in source_rows})}})
print(json.dumps({"papers": len(papers), "pdfs": sum(p["pdf_pages"]>0 for p in papers), "pdf_pages_archived": sum(p["pdf_pages"] for p in papers), "body_pages_read": 0, "candidates": sum(p["screening"]["decision"]=="candidate" for p in papers), "references": sum(p["screening"]["decision"]=="reference" for p in papers)}))
