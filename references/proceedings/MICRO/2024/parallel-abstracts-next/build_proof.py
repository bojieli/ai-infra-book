"""Build local reading records from already archived bytes; no network."""
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
    2: {
        "short_title": "Elastic Translations",
        "decision": "reference",
        "reason": "OS 的翻译粒度与 TLB 开销可作内存管理背景；当前摘要是 ARMv8-A Linux/KVM 的 CPU 虚拟内存工作，不直接证明 GPU HBM 或 KV cache 的分页行为，暂不扩张本书案例。",
        "version": "First-author-hosted file named preprint; 19 physical pages. First-page title and all eight authors match publisher metadata; no publisher DOI/page footer on checked first page. Coauthor publication entry corroborates MICRO 2024, but links publisher rather than this PDF. Not asserted byte-identical to version of record.",
        "identity_note": "PDF and publisher spell Dimitrios Siakavaras; coauthor webpage uses Dimitris. Same surrounding author list/title/venue; webpage spelling is preserved, not silently substituted into publisher metadata.",
        "identity_end": "Section II discusses them",
        "possible_chapters": [4],
    },
    3: {
        "short_title": "Distributed Page Table",
        "decision": "reference",
        "reason": "把散列表扩容问题转为与数据页的地址冲突处理，可作元数据与容量取舍的背景；DPT 的 distributed 指 PTE 分散在物理内存地址空间，不是跨节点分布式页表或 KV cache 系统。暂不引入通用页表新专题。",
        "version": "Coauthor publication page directly links this 14-page public PDF. Checked first page has MICRO 2024 header, DOI 10.1109/MICRO61859.2024.00013 and printed page 36; title and all six authors match publisher metadata. Author-hosted publisher-formatted copy; exact publisher byte identity not asserted.",
        "identity_note": "First two authors have equal-contribution marks; marks do not add authors. Capitalization of An in PDF title is immaterial.",
        "identity_end": "enhance this process",
        "possible_chapters": [4],
    },
    52: {
        "short_title": "CARS",
        "decision": "reference",
        "reason": "函数 ABI 的 spill/fill 把寄存器容量与并发隐藏延迟联系起来，适合架构取舍备查；这是需要硬件支持的寄存器栈方案，不是今天框架的开关或一般算子自动优化。摘要不足以把 22 个函数调用程序的结果外推到 LLM。",
        "version": "Coauthor Purdue publication page directly links this 14-page public PDF. Title and four authors match publisher metadata, with webpage Tim Rogers versus PDF/publisher Timothy G. Rogers. First-page PDF and webpage abstract have conflicting performance/energy percentages; neither is declared authoritative final revision.",
        "identity_note": "Mengchi Zhang footnote says work at Purdue, currently Meta. PDF abstract says 26%/28%; author webpage says 25%/30%. Preserve both variants; do not adopt either performance figure in book.",
        "identity_end": "Abstract—",
        "possible_chapters": [4, 5],
    },
    75: {
        "short_title": "ThreadFuser",
        "decision": "reference",
        "reason": "用 CPU 动态执行轨迹分析分支发散和同步，再接 GPU 模拟器，适合先判断迁移风险的方法备查；它不是把任意 MIMD 程序自动编译成最优 GPU 内核。当前书强调先做简单推算，暂不为此增加复杂模拟器实验。",
        "version": "Coauthor Purdue publication page directly links this 14-page public PDF. First-page title and all four authors match publisher metadata; webpage uses Tim Rogers. Abstract also present in author webpage, with minor text wrapping/spelling differences retained.",
        "identity_note": "Mahmoud Khairy footnote says work at Purdue, currently AMD. Framework accuracy and applicability beyond the abstract's 36 CPU workloads remain unread body questions.",
        "identity_end": "I. I NTRODUCTION",
        "possible_chapters": [4, 5],
    },
    121: {
        "short_title": "NDPExt",
        "decision": "candidate",
        "reason": "扩容以后，带宽与元数据开销仍可能成为约束：可备选说明粗粒度流、缓存容量分配、位置与复制如何一起取舍。若后续现有内存池段落需要这个反例，再读正文核对 NDP/CXL 模型、工作负载和基线；当前不新增大纲。",
        "version": "Coauthor Tsinghua-hosted 15-page public PDF. Checked first page has MICRO 2024 header, DOI 10.1109/MICRO61859.2024.00120 and printed page 1648; title and four authors match publisher metadata. Author-hosted publisher-formatted copy; exact publisher byte identity not asserted.",
        "identity_note": "Mingyu Gao also lists Shanghai Qi Zhi Institute on PDF. Architecture direction is 3D NDP-stack DRAM as cache of CXL extended memory, not the reverse, and not a claim that ordinary serving frameworks implement NDPExt.",
        "identity_end": "across the logic dies",
        "possible_chapters": [4, 9],
    },
}

papers = []
images = []
identities = []
for n, d in details.items():
    raw = manifest[n]
    prefix = f"paper-{n:03d}"
    pdf = prefix + ".pdf"
    txt = prefix + "-left-column.txt"
    t = (D / txt).read_text()
    a = t.index("Abstract—") + len("Abstract—")
    z = t.index("Index Terms", a)
    while t[z - 1].isspace():
        z -= 1
    abstract = t[a:z]
    abstract_file = prefix + "-abstract.txt"
    (D / abstract_file).write_text(abstract + "\n")
    info = (D / (prefix + "-pdfinfo.txt")).read_text()
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    first = prefix + "-first-page.txt"
    first_text = (D / first).read_text()
    identities.append({"program_order": n, "file": first, "sha256": sha((D / first).read_bytes()), "char_range": [0, first_text.index(d["identity_end"])], "scope": "Title, author block, affiliation identity only; first-page DOI/footer also visually inspected where present."})
    img = prefix + "-identity.png"
    images.append({"program_order": n, "file": img, "sha256": sha((D / img).read_bytes()), "physical_page": 1, "actually_viewed": True, "scope": "Title/authors and complete Abstract region only; adjacent body/figures not counted as body reading.", "render_command": ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-scale-to", "1400", "-png", pdf, prefix + "-identity"]})
    papers.append({
        "program_order": n, "doi": raw["doi"], "publisher_title": raw["publisher_title"], "program_title": raw["program_title"], "publisher_authors": raw["publisher_authors"], "publisher_pages": raw["page"], "publication_date_metadata": raw["publication_date"],
        "short_title": d["short_title"], "previous_reading_status": raw["reading_status"], "reading_status": "abstract_screened",
        "read_scope": {"complete_abstract": True, "body_read": False, "scope": "Full primary abstract plus first-page bibliographic identity only. Adjacent body/figures may occur in extraction/render but were not used for substantive body conclusions."},
        "screening": {"basis": "title_and_full_abstract", "decision": d["decision"], "reason": d["reason"], "possible_chapters_if_later_justified": d["possible_chapters"], "outline_changed": False},
        "version": d["version"], "identity_note": d["identity_note"], "source_kind": "author_public_pdf", "source_file": pdf, "source_url": sources[pdf]["url"], "source_sha256": sources[pdf]["sha256"], "pdf_pages": pages, "abstract_physical_pages": [1], "identity_viewed_image": img,
        "extraction": {"kind": "poppler_first_page_left_column", "command": ["pdftotext", "-f", "1", "-l", "1", "-x", "0", "-y", "0", "-W", "306", "-H", "792", pdf, "-"], "source_text": txt},
        "abstract_text_file": txt, "abstract_text_sha256": sha((D / txt).read_bytes()), "abstract_char_range": [a, z], "abstract_file": abstract_file, "abstract": abstract, "abstract_sha256": sha(abstract.encode()),
    })

aux = []
for name in ["cars-author", "threadfuser-author", "dpt-author-pubs", "elastic-author-pubs"]:
    soup = BeautifulSoup((D / (name + ".html")).read_bytes(), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    t = (soup.get_text("\n", strip=True) + "\n").replace("\r\n", "\n").replace("\r", "\n")
    textfile = name + ".txt"
    (D / textfile).write_text(t)
    if name in ["cars-author", "threadfuser-author"]:
        a = t.index("Abstract\n") + len("Abstract\n")
        z = t.index("\nType\n", a)
        kind = "complete_author_webpage_abstract_variant"
    else:
        start, end = {"dpt-author-pubs": ("Distributed Page Table", "\nPACT\n"), "elastic-author-pubs": ("Elastic Translations", "\nFaaSRail:")}[name]
        a = t.index(start)
        z = t.index(end, a)
        kind = "one_publication_identity_entry_only"
    aux.append({"source_file": name + ".html", "file": textfile, "sha256": sha((D / textfile).read_bytes()), "char_range": [a, z], "scope": kind, "text": t[a:z], "adds_new_paper_count": False})

blocked = manifest[51]
save("abstracts.json", {"recorded_at": NOW, "scope": "MICRO 2024 second independent batch: six locked targets, five complete primary abstracts, one unavailable. Body zero.", "input_manifest_sha256": sha((D / "input-manifest.json").read_bytes()), "input_abstracts_sha256": sha((D / "input-public-abstracts.json").read_bytes()), "previous_batch_sha256": sha((D / "previous-batch-abstracts.json").read_bytes()), "locked_program_orders": [2, 3, 51, 52, 75, 121], "downloaded_code_executed": False, "papers": papers, "unavailable": [{"program_order": 51, "doi": blocked["doi"], "publisher_title": blocked["publisher_title"], "publisher_authors": blocked["publisher_authors"], "reading_status": "metadata_matched_not_screened", "complete_abstract": False, "body_read": False, "screening_decision": None, "reason": "Author institution HTTP 403; publisher HTTP 202 with zero response bytes. No full primary abstract or public PDF obtained. Do not replace with lecture/news/repost summaries.", "attempt_files": ["atomic-cache-author.html", "atomic-cache-publisher.response"]}]})
save("reading.json", {"recorded_at": NOW, "body_pages_read": 0, "full_primary_abstracts_read": 5, "public_pdf_count": 5, "archived_pdf_pages": 76, "images_actually_viewed": images, "identity_text_scopes": identities, "auxiliary_text_scopes": aux, "scope_boundary": "Only Abstract plus bibliographic identity on physical page 1. Downloaded PDF pages are not pages read; author webpage variants do not add paper counts. No source code inspected or run."})
save("acquisition-notes.json", {"recorded_at": NOW, "locked_program_orders": [2, 3, 51, 52, 75, 121], "http_requests": 11, "http_200": 9, "http_403": 1, "http_202_empty_non_evidence": 1, "unavailable_program_orders": [51], "separate_tool_observation": {"url": "https://ieeexplore.ieee.org/document/10764542/", "method": "web.open", "observed": "JavaScript/robot verification challenge; no usable full abstract.", "raw_response_archived": False, "counted_as_raw_http_source": False}, "not_used_as_evidence": ["Secondary lecture report or ResearchGate no-full-text page for Atomic Cache", "Unfetched source-code links on author pages", "Performance numbers without body evaluation context"], "version_conflicts": [{"program_order": 52, "pdf": "26% performance and 28% energy-efficiency improvement", "author_html": "25% performance and 30% energy-efficiency improvement", "resolution": "Unresolved author-page/PDF abstract variation; preserve both, do not harmonize or use performance numbers in book."}], "public_pdf_absent": [51], "source_authenticity_boundary": "Public author/institution hosts and matching title/author/DOI identity; no claim of cryptographic equivalence to publisher version or artifact validation."})
print("Built five complete abstracts and one explicit unavailable record.")
