"""Record the completed third abstract batch, using local archived bytes only."""
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


def save(f, data):
    (D / f).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


sources = {r["file"]: r for r in load("sources.json")}
manifest = {r["program_order"]: r for r in load("input-manifest.json")["papers"]}
details = {
    21: ("Avatar", "reference", "地址预测隐藏 page-walk 等待，还需要快速验证才能消费数据；可作 GPU 访存延迟背景，但属于 CAST/CAVA 硬件提案，不能写成现有 GPU 或框架已具备的能力。", [4], "First-author publication list directly links this 15-page PDF. First page has MICRO 2024 header, DOI .00029 and printed page 278. Title and all eight authors match metadata; author-hosted publisher-formatted copy, not asserted byte-identical to publisher file."),
    72: ("Memory Allocation Under Hardware Compression", "reference", "硬件压缩后 OS 的物理页数不等于实际 DRAM 占用，容量隔离需要新的分配接口；适合资源容量计量背景，不能把硬件内存压缩等同于模型权重量化或现有软件内存池功能。", [4], "First-author page directly links this 17-page public PDF; first page prints DOI .00075 and page 966, with ten matching authors (Kirk Cameron versus metadata Kirk W. Cameron). MSR supplies a differently worded complete abstract with consistent headline variation ranges. Poppler reports xref num 4 reconstruction, returns success; original PDF bytes unchanged and first page visually checked."),
    73: ("Genie Cache", "reference", "页表中放 cache tag 可以省元数据访问，但 miss/eviction 的 OS 延迟仍需处理；DCMU 与提前写回是特定 DRAM-cache 架构机制，不能直接当成 KV cache 的软件实现。", [4], "Full abstract from author institution Yonsei's publication record, with matching title, two authors, DOI and pages 983–996. Institution uses William Song versus metadata William J. Song. Institution date 2024-11-06 differs from Crossref's 2024-11-02; neither is treated as a new revision. Author lab links DOI only; no public PDF obtained."),
    89: ("DNN Recommendation Inference on GPUs", "candidate", "embedding 内核 occupancy 改善后仍有访存延迟停顿，可作第 5 章 profile 驱动优化的现有实验变体：先找瓶颈，再区分并发、预取和 L2 驻留。摘要限定 A100/DLRM；继续读前不采用倍率，不推广成 LLM attention 优化。", [5], "Author-deposited arXiv:2410.22249v1, submitted 2024-10-29 17:13:54 UTC. Version fixed PDF has 16 physical pages; first-page title and all six authors match MICRO publisher metadata. arXiv date/version not conflated with conference date or publisher version of record."),
    94: ("Leviathan", "reference", "near-cache 计算除了搬少数据还要表达何时、何处执行，可作架构与编程接口取舍备查；摘要未验证任意程序或 LLM 能获益，不新增通用 NDC 专题。", [4], "17-page public manuscript under coauthor Nathan Beckmann's CMU publications directory. Title and two authors match publisher metadata. First author lists Samsung with footnote that work was completed at CMU; no publisher DOI/page footer claimed on checked first page."),
}
papers, images, identity_scopes = [], [], []
for n, (short, decision, reason, chapters, version) in details.items():
    raw = manifest[n]
    base = {"program_order": n, "doi": raw["doi"], "publisher_title": raw["publisher_title"], "program_title": raw["program_title"], "publisher_authors": raw["publisher_authors"], "publisher_pages": raw["page"], "publication_date_metadata": raw["publication_date"], "short_title": short, "previous_reading_status": raw["reading_status"], "reading_status": "abstract_screened", "version": version, "read_scope": {"complete_abstract": True, "body_read": False, "scope": "Complete primary abstract and bibliographic identity only; adjacent intro/figures are not body reading."}, "screening": {"basis": "title_and_full_abstract", "decision": decision, "reason": reason, "possible_chapters_if_later_justified": chapters, "outline_changed": False}}
    prefix = f"paper-{n:03d}"
    if n == 73:
        source = "genie-institution.html"
        txt = "genie-institution.txt"
        t = (D / txt).read_text()
        a = t.index("Abstract\n") + len("Abstract\n")
        z = t.index("\nOriginal language\n", a)
        base.update({"source_kind": "author_institution_full_abstract", "pdf_pages": 0, "pdf_file": None, "extraction": {"kind": "html_visible_text", "source_text": txt, "method": "BeautifulSoup html.parser; remove script/style; get_text newline strip; normalize CRLF/CR"}})
    else:
        source = prefix + ".pdf"
        txt = prefix + "-left-column.txt"
        t = (D / txt).read_text()
        a = t.index("Abstract—") + len("Abstract—")
        while t[a].isspace():
            a += 1
        z = t.index("Index Terms", a)
        while t[z - 1].isspace():
            z -= 1
        pages = int(re.search(r"^Pages:\s+(\d+)", (D / (prefix + "-pdfinfo.txt")).read_text(), re.M).group(1))
        img = prefix + "-identity.png"
        images.append({"program_order": n, "file": img, "sha256": sha((D / img).read_bytes()), "physical_page": 1, "actually_viewed": True, "scope": "Title/authors and complete Abstract region only; adjacent body/chart not counted as body reading.", "render_command": ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-scale-to", "1500", "-png", source, prefix + "-identity"]})
        first = prefix + "-first-page.txt"
        ft = (D / first).read_text()
        identity_scopes.append({"program_order": n, "file": first, "sha256": sha((D / first).read_bytes()), "scope": "Title/author/affiliation block visually checked from first-page image; first-page extracted text preserved as identity aid, not all text before Abstract is body reading."})
        base.update({"source_kind": "author_public_pdf", "pdf_pages": pages, "abstract_physical_pages": [1], "identity_viewed_image": img, "extraction": {"kind": "poppler_first_page_left_column", "source_text": txt, "command": ["pdftotext", "-f", "1", "-l", "1", "-x", "0", "-y", "0", "-W", "306", "-H", "792", source, "-"]}})
    abstract = t[a:z]
    abstract_file = prefix + "-abstract.txt"
    (D / abstract_file).write_text(abstract + "\n")
    base.update({"source_file": source, "source_url": sources[source]["url"], "source_sha256": sources[source]["sha256"], "abstract_text_file": txt, "abstract_text_sha256": sha((D / txt).read_bytes()), "abstract_char_range": [a, z], "abstract": abstract, "abstract_sha256": sha(abstract.encode()), "abstract_file": abstract_file})
    papers.append(base)

aux = []
for name in ["avatar-author-pubs", "compression-author", "compression-msr", "genie-author-pubs", "recommendation-arxiv", "blenda-author"]:
    t = (D / (name + ".txt")).read_text()
    if name == "avatar-author-pubs":
        a = t.index("A Case for Speculative Address Translation")
        z = t.index("Distributed Page Table", a)
    elif name == "compression-author":
        title = t.index("Memory Allocation under Hardware Compression")
        a = t.rfind("Muhammad Laghari", 0, title)
        z = t.index("[PDF]", title) + len("[PDF]")
    elif name == "compression-msr":
        a = t.index("As the scaling of DRAM density")
        z = t.index("\nOpens in a new tab", a)
    elif name == "genie-author-pubs":
        title = t.index("Genie Cache:")
        a = t.rfind("Youngin Kim", 0, title)
        z = t.index("Paper", title) + len("Paper")
    elif name == "recommendation-arxiv":
        a = t.index("Abstract:\n") + len("Abstract:\n")
        z = t.index("\nComments:", a)
    else:
        title = t.index("Blenda:")
        a = t.rfind("Mohammad Bakhshalipour", 0, title)
        z = t.index("Farid Samandi\n, Tianchu", title)
    aux.append({"source_file": name + ".html", "file": name + ".txt", "sha256": sha((D / (name + ".txt")).read_bytes()), "char_range": [a, z], "text": t[a:z], "scope": "complete_abstract_variant" if name in ["compression-msr", "recommendation-arxiv"] else "corresponding_publication_identity_entry_only", "adds_new_paper_count": False})

arxiv = (D / "recommendation-arxiv.txt").read_text()
a = arxiv.index("Submission history")
z = arxiv.index("Full-text links:", a) if "Full-text links:" in arxiv[a:] else min(len(arxiv), a + 550)
aux.append({"source_file": "recommendation-arxiv.html", "file": "recommendation-arxiv.txt", "sha256": sha((D / "recommendation-arxiv.txt").read_bytes()), "char_range": [a, z], "text": arxiv[a:z], "scope": "arxiv_submission_version_identity", "adds_new_paper_count": False})
blocked = manifest[97]
save("abstracts.json", {"recorded_at": NOW, "scope": "Third MICRO2024 independent batch; six false targets from current reading-coverage snapshot, five complete primary abstracts and one unavailable.", "input_manifest_sha256": sha((D / "input-manifest.json").read_bytes()), "input_reading_coverage_sha256": sha((D / "input-reading-coverage.json").read_bytes()), "locked_program_orders": [21, 72, 73, 89, 94, 97], "downloaded_code_executed": False, "papers": papers, "unavailable": [{"program_order": 97, "doi": blocked["doi"], "publisher_title": blocked["publisher_title"], "publisher_authors": blocked["publisher_authors"], "reading_status": "metadata_matched_not_screened", "complete_abstract": False, "body_read": False, "screening_decision": None, "reason": "Author page has corresponding title/author/venue entry but no paper link or full abstract; DOI resolves to publisher HTTP 202 with zero bytes. No primary full abstract or public paper obtained; secondary summaries not substituted.", "attempt_files": ["blenda-author.html", "blenda-publisher.response"]}]})
save("reading.json", {"recorded_at": NOW, "full_primary_abstracts_read": 5, "public_pdf_count": 4, "archived_pdf_pages": 65, "body_pages_read": 0, "images_actually_viewed": images, "identity_text_scopes": identity_scopes, "auxiliary_text_scopes": aux, "scope_boundary": "PDF physical page 1 Abstract/identity only; university HTML abstract/identity for Genie. No body pages, no source-code read/execution. Variants do not add unique paper counts."})
save("acquisition-notes.json", {"recorded_at": NOW, "new_http_requests": 11, "http_200": 10, "http_202_empty_non_evidence": 1, "full_abstract_unavailable": [97], "public_pdf_unavailable": [73, 97], "failures": [{"file": "blenda-publisher.response", "status": 202, "bytes": 0, "reason": "No publisher document body returned; empty response not usable primary evidence."}], "extraction_warning": {"program_order": 72, "message": "Internal Error: xref num 4 not found but needed, try to reconstruct", "details": "pdfinfo and both pdftotext methods reproduced warning with exit code 0. Original PDF bytes untouched; first page visually inspected. Stderr files and extraction-log.json preserve reproducible observations."}, "version_notes": ["Genie institution publication date 2024-11-06 vs Crossref 2024-11-02; retain both, no inferred revision.", "Recommendation arXiv fixed v1 dated 2024-10-29, separate from conference identity.", "Compression MSR abstract wording differs from public PDF, same reported performance-variation intervals; preserve variants without implying one is final."], "not_used": ["Blenda secondary abstract summaries", "Search snippets as substitute for full raw primary abstracts", "Paper performance numbers without body conditions", "Source-code links or artifact badges as evidence of execution"], "atomic_cache_retried": False})
print("Recorded five full primary abstracts, one unavailable, four PDFs/65 pages, body zero.")
