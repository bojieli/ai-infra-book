"""Build the fourth batch's local records. No network or external code execution."""
from pathlib import Path
import datetime
import hashlib
import json
import re
from bs4 import BeautifulSoup

D = Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(f):
    return json.loads((D / f).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def save(f, value):
    (D / f).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


sources = {r["file"]: r for r in load("sources.json")}
manifest = {r["program_order"]: r for r in load("input-manifest.json")["papers"]}
details = {
    4: ("CamPU", "reference", "多相机投影/拼接与 DNN 吞吐不匹配，说明优化单一计算阶段不等于优化全系统；当前多媒体主线已有具体案例，不增加相机处理专节。", "campu-institution.html", "KAIST institution full abstract, matching title, Dongseok Im/Hoi Jun Yoo (metadata Hoi-Jun Yoo), DOI .00014 and pages 50–63. First-author publication page corroborates the work but links IEEE only; publisher request returned empty 202. No public PDF obtained."),
    5: ("AdapTiV", "reference", "token merging 自身的相似度计算/调度开销可能抵消减少 token 的收益，适合模型与硬件共同设计备查；这是特定 ViT 的硬件软件方案，不直接套到 LLM/MoE 或采用其硬件倍率。", "adaptiv-institution.html", "KAIST institution full abstract with matching three authors, DOI .00015 and pages 64–77. Institution spells Joo Young Kim, metadata Joo-Young Kim. Author lab's year listing corroborates title; linked entry returned navigation-only visible text and no public PDF link."),
    6: ("Fusion-3D", "reference", "NeRF 三阶段与跨芯片搬运的整体取舍可备查；书已限制多媒体篇幅，暂不增加 NeRF 贯穿案例。摘要明确区分芯片原型与基于测量的模拟，不能把模拟倍率当全部实芯片实测。", "paper-006.pdf", "14-page NSF public-access repository manuscript, title and nine authors match publisher identity (Yingyan (Celine) Lin spelling variant). Author lab publication entry independently corroborates same abstract and MICRO2024 identity. No publisher DOI/page footer claimed on checked first page. PDF text extraction mis-maps six math glyphs; original bytes preserved and corrections visually checked."),
    7: ("Secure Prefetching", "exclude", "针对 GhostMinion 等安全缓存的瞬态执行与预取交互；当前 AI Infra 主线未建立该威胁模型或专用缓存硬件，加入会展开旁支，不采用为本书正文候选。", "paper-007.pdf", "13-page coauthor Alberto Ros's university-hosted public manuscript. Title and all four authors match publisher metadata, with accent in Agustín. First page has manuscript page 1; publisher version equivalence not asserted."),
    8: ("HyperTEE", "reference", "将 enclave 管理迁入物理隔离子系统，可作隔离粒度背景；它是 FPGA 原型的 TEE 架构，不等于容器、microVM 或 Agent sandbox 已部署这种机制。不增加安全架构专节。", "paper-008.pdf", "16-page coauthor Fengwei Zhang's SUSTech-hosted PDF. Despite filename hypertee-micro25.pdf, first page says MICRO2024, DOI .00018 and printed page 105; title and all nine authors match publisher metadata. Download/license footer is source formatting, not an execution claim."),
    9: ("GECKO", "exclude", "面向能量采集、间歇供电 IoT 设备的 EMI 与 just-in-time checkpoint 防护，和本书训练 checkpoint/Agent 执行环境的约束不同；不展开为 AI Infra 章节内容。", "emi-institution.html", "ETRI author-institution full abstract with four matching authors and DOI .00019. Institution cites pp.1–15, publisher metadata pp.121–135; same 15-page length but different pagination retained. Author's GECKO PDF link returns 404. A search-returned NSF PDF was LightWSP instead and rejected, not counted as a GECKO manuscript."),
}
papers, images = [], []
for n, (short, decision, reason, source, version) in details.items():
    raw = manifest[n]
    prefix = f"paper-{n:03d}"
    is_pdf = source.endswith(".pdf")
    if is_pdf:
        txt = prefix + ("-left-column-corrected.txt" if n == 6 else "-left-column.txt")
        t = (D / txt).read_text()
        a = t.index("Abstract—") + len("Abstract—")
        z = t.index("Index Terms", a) if "Index Terms" in t[a:] else t.index("I. I NTRODUCTION", a)
        while t[z - 1].isspace():
            z -= 1
        pages = int(re.search(r"^Pages:\s+(\d+)", (D / (prefix + "-pdfinfo.txt")).read_text(), re.M).group(1))
        extraction = {"kind": "poppler_first_page_left_column_with_explicit_glyph_corrections" if n == 6 else "poppler_first_page_left_column", "source_text": prefix + "-left-column.txt", "command": ["pdftotext", "-f", "1", "-l", "1", "-x", "0", "-y", "0", "-W", "306", "-H", "792", source, "-"]}
        if n == 6:
            extraction["correction_file"] = "text-corrections.json"
        img = prefix + "-identity.png"
        images.append({"program_order": n, "file": img, "sha256": sha((D / img).read_bytes()), "physical_page": 1, "actually_viewed": True, "scope": "Full Abstract and bibliographic identity only; adjacent introduction/figures not body reading.", "render_command": ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-scale-to", "1500", "-png", source, prefix + "-identity"]})
    else:
        txt = source.replace(".html", ".txt")
        t = (D / txt).read_text()
        a = t.index("Abstract\n") + len("Abstract\n")
        marker = "\nKSP Keywords\n" if n == 9 else "\nOriginal language\n"
        z = t.index(marker, a)
        pages = 0
        extraction = {"kind": "html_visible_text", "source_text": txt, "method": "BeautifulSoup html.parser; remove script/style; newline-separated text with CRLF/CR normalization"}
    abstract = t[a:z]
    out = prefix + "-abstract.txt"
    (D / out).write_text(abstract + "\n")
    papers.append({"program_order": n, "doi": raw["doi"], "publisher_title": raw["publisher_title"], "program_title": raw["program_title"], "publisher_authors": raw["publisher_authors"], "publisher_pages": raw["page"], "publication_date_metadata": raw["publication_date"], "short_title": short, "previous_reading_status": raw["reading_status"], "reading_status": "abstract_screened", "read_scope": {"complete_abstract": True, "body_read": False, "scope": "Complete primary abstract and identity only."}, "screening": {"basis": "title_and_full_abstract", "decision": decision, "reason": reason, "outline_changed": False}, "version": version, "source_kind": "author_or_funder_public_pdf" if is_pdf else "author_institution_full_abstract", "source_file": source, "source_url": sources[source]["url"], "source_sha256": sources[source]["sha256"], "pdf_pages": pages, "abstract_physical_pages": [1] if is_pdf else [], "extraction": extraction, "abstract_text_file": txt, "abstract_text_sha256": sha((D / txt).read_bytes()), "abstract_char_range": [a, z], "abstract": abstract, "abstract_sha256": sha(abstract.encode()), "abstract_file": out})

aux = []
for name, marker in [("campu-author", "CamPU:"), ("adaptiv-author-year", "AdapTiV:"), ("hypertee-author-pubs", "HyperTEE"), ("emi-author", "Defending Against EMI")]:
    t = (D / (name + ".txt")).read_text()
    a = t.index(marker)
    if name == "campu-author":
        z = t.index("Paper Link", a) + len("Paper Link")
    elif name == "emi-author":
        z = t.index("2024", a) + len("2024")
    else:
        z = t.index("\n", a)
    aux.append({"source_file": name + ".html", "file": name + ".txt", "sha256": sha((D / (name + ".txt")).read_bytes()), "char_range": [a, z], "text": t[a:z], "scope": "corresponding_publication_identity_only", "adds_new_paper_count": False})
t = (D / "fusion-author-pubs.txt").read_text()
a = t.index("Recent breakthroughs in Neural Radiance Field")
z = t.index("in edge devices for off-chip communication.", a) + len("in edge devices for off-chip communication.")
aux.append({"source_file": "fusion-author-pubs.html", "file": "fusion-author-pubs.txt", "sha256": sha((D / "fusion-author-pubs.txt").read_bytes()), "char_range": [a, z], "text": t[a:z], "scope": "complete_same_paper_author_abstract_variant_with_correct_math_symbols", "adds_new_paper_count": False})
save("abstracts.json", {"recorded_at": NOW, "scope": "Fourth MICRO2024 batch, six frontmost unread targets after excluding delivered batches and unavailable orders 51/97. Six complete primary abstracts, body zero.", "input_manifest_sha256": sha((D / "input-manifest.json").read_bytes()), "input_reading_coverage_sha256": sha((D / "input-reading-coverage.json").read_bytes()), "third_batch_sha256": sha((D / "third-batch-abstracts.json").read_bytes()), "locked_program_orders": [4, 5, 6, 7, 8, 9], "downloaded_code_executed": False, "papers": papers, "unavailable": []})
save("reading.json", {"recorded_at": NOW, "full_primary_abstracts_read": 6, "matched_public_pdf_count": 3, "matched_public_pdf_pages": 43, "body_pages_read": 0, "images_actually_viewed": images, "auxiliary_text_scopes": aux, "identity_rejected_document": {"file": "identity-mismatch-nsf-10590071.pdf", "actual_title": "LightWSP: Whole-System Persistence on the Cheap", "actual_program_order": 16, "physical_pages": 16, "scope": "First-page text exposed during identity check, including its abstract, then rejected as a source for GECKO. No formal screening/adoption of off-target paper and no addition to this batch's paper counts.", "first_page_text": "identity-mismatch-first-page.txt", "first_page_image": "identity-mismatch-first-page.png", "image_actually_viewed": False, "counted_as_matched_pdf": False}, "scope_boundary": "Three matching PDF first-page Abstract/identity regions, three institution HTML abstracts. Downloaded/rendered off-target file is separately logged, not a seventh screened paper or fourth matching public PDF. No body/source-code reading or execution."})
save("acquisition-notes.json", {"recorded_at": NOW, "new_http_requests": 16, "http_200": 13, "http_202_empty_non_evidence": 2, "http_404": 1, "public_pdf_unavailable": [4, 5, 9], "full_primary_abstract_unavailable": [], "failed_sources": [{"file": "campu-publisher.response", "status": 202, "bytes": 0}, {"file": "emi-publisher.response", "status": 202, "bytes": 0}, {"file": "emi-author-pdf-404.response", "status": 404, "not_pdf": True}], "identity_mismatch": {"file": "identity-mismatch-nsf-10590071.pdf", "url": "https://par.nsf.gov/servlets/purl/10590071", "http_status": 200, "intended_target": 9, "actual_program_order": 16, "actual_title": "LightWSP: Whole-System Persistence on the Cheap", "matched_pdf_count_excluded": True, "notes": "Search hit was not paper9; metadata and extracted first page identify another paper. Original bytes retained, output files renamed to avoid pretending they are GECKO. No outline/coverage addition for paper16."}, "symbol_correction": "text-corrections.json; four multiplication and two inequality glyphs in Fusion-3D only, visually checked and also corroborated by author webpage.", "source_execution": False, "atomic_cache_or_blenda_retried": False})
print("Recorded six full abstracts; three matching PDFs/43 pages; one off-target PDF excluded.")
