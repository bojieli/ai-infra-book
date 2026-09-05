#!/usr/bin/env python3
"""Download the explicitly listed primary sources and build an offline index."""
import argparse
import concurrent.futures
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import urllib.request
from urllib.parse import quote
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CHAPTERS = ["认识 AI 基础设施", "模型架构", "训练与推理负载", "加速器", "超节点",
            "数据中心网络", "端边云协同", "单实例推理", "分布式推理", "训练系统",
            "任务调度与运行", "架构协同设计"]


class ReadableText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        if tag in ("p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        if tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def result(self):
        return "\n".join(line for line in
                         (re.sub(r"\s+", " ", x).strip() for x in "".join(self.parts).splitlines())
                         if line)


def fetch(row):
    item = dict(row)
    item["chapters"] = [int(c) for c in row["chapters"].split(",")]
    item["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    for attempt in range(2):
        try:
            supplied = row["url"].startswith("local:")
            if supplied:
                source = (ROOT / row["url"][6:]).resolve()
                source.relative_to(ROOT)
                data = source.read_bytes()
                item["acquisition"] = "user_provided"
                item["content_type"] = "application/pdf" if data.startswith(b"%PDF-") else "text/plain"
            else:
                request = urllib.request.Request(row["url"], headers={"User-Agent": "AI-Infra-Book-Reference-Archive/1.0"})
                with urllib.request.urlopen(request, timeout=35) as response:
                    data = response.read()
                    item["resolved_url"] = response.url
                    item["content_type"] = response.headers.get("Content-Type", "")
            if data.startswith(b"%PDF-"):
                suffix = ".pdf"
            elif "pdf" in item["content_type"].lower() or "/pdf/" in row["url"] or row["url"].endswith(".pdf"):
                raise ValueError("Expected a PDF; response has no PDF signature")
            elif "html" in item["content_type"].lower() or b"<html" in data[:5000].lower():
                suffix = ".html"
            elif row["url"].endswith(".json"):
                json.loads(data)
                suffix = ".json"
            elif row["url"].endswith(".md"):
                suffix = ".md"
            else:
                suffix = ".txt"
            dest = source if supplied else ROOT / "files" / row["category"] / (row["id"] + suffix)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not supplied:
                dest.write_bytes(data)
            plain = ROOT / "text" / (row["id"] + ".txt")
            plain.parent.mkdir(exist_ok=True)
            if suffix == ".pdf":
                subprocess.run(["pdftotext", "-layout", str(dest), str(plain)], check=True, capture_output=True)
                body = plain.read_text(errors="replace")
                info = subprocess.run(["pdfinfo", str(dest)], check=True, capture_output=True, text=True).stdout
                pages = re.search(r"^Pages:\s+(\d+)", info, re.M)
                item["pages"] = int(pages.group(1)) if pages else None
                version = re.search(r"arXiv:\s*([0-9.]+v\d+)", body[:12000])
                item["version_in_text"] = version.group(1) if version else None
                item["first_page_excerpt"] = body.split("\f")[0][:1800]
            else:
                body = data.decode("utf-8", errors="replace")
                if suffix == ".html":
                    parser = ReadableText()
                    parser.feed(body)
                    body = parser.result()
                plain.write_text(body)
            item.update(file=str(dest.relative_to(ROOT)), text=str(plain.relative_to(ROOT)),
                        sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), text_chars=len(body),
                        status="user_provided" if supplied else "downloaded")
            item.pop("error", None)
            if row["id"].endswith("-entry"):
                item["status"] = "landing_only"
            elif len(body.strip()) < 600:
                item["status"] = "incomplete_text"
            if row["id"] == "ascend-c-architecture" and "Cube" not in body:
                item["status"] = "incomplete_text"
                item["error"] = "动态文档页未包含硬件架构正文；另有完整 Ascend C PDF"
            if row["id"] == "rdma-guide" and "RDMA" not in body:
                item["status"] = "incomplete_text"
                item["error"] = "官方入口响应未包含 RDMA 文档正文"
            return item
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
    item["status"] = "failed"
    return item


def index(items):
    ok = [r for r in items if r["status"] in ("downloaded", "local_snapshot", "user_provided")]
    pdfs = [r for r in ok if r.get("file", "").endswith(".pdf")]
    lines = ["# 本地参考资料库", "",
             "对应当前三部分、十二章蓝图。收录原始论文、作者报告、芯片与系统规格、协议以及官方软件文档。资料选取以章节中的具体论证为依据；历史论文与近期报告同时保留。",
             "", f"当前清单 {len(items)} 项：已保存正文 {len(ok)} 项，其中 PDF {len(pdfs)} 份。其余项目的获取状态见文末。",
             "", "[浏览本地索引](index.html) · [来源清单](sources.tsv) · [下载与校验记录](manifest.json) · [证据缺口](GAPS.md)",
             "", "作者补充的 UB 正式规范、操作系统参考设计和昇腾 950 白皮书，见 [三份文档的核对笔记](UB-ASCEND-NOTES.md)。",
             "", "PDF 原件位于 `files/`，可搜索文本位于 `text/`；官方网页同时保存原始 HTML 与离线文本，外部图片、脚本和站内链接不保证离线可用。不得把网页入口记作规范全文。",
             "", "`manifest.json` 记录实际获取时间、下载与来源地址、内容校验值、字节数、PDF 页数及能从正文识别出的 arXiv 版本。网页和可变分支按本地文件的 SHA-256 固定快照；下载完成不代表已经逐页审阅。",
             "", "`local_snapshot` 表示从作者本地仓库的指定提交归档，记录仓库路径与提交号，不计作网络下载。`landing_only` 是索引入口，`incomplete_text` 表示未取得完整正文，`access_required` 表示来源要求额外的访问条件。",
             "", "`user_provided` 表示作者提供的原件，保留原文件名并记录校验值。清单中的 `local:` 地址只用于读取本资料库内的文件，不发起网络请求；其中的登记时间不是原始下载时间。",
             "", "写作时先查本地资料，引用具体页码、节号、版本及适用条件。规格、实现和测量分别取证；新证据改变参数时新增或明确更新快照，保留变更原因。", ""]
    for number, title in enumerate(CHAPTERS, 1):
        lines += [f"## 第 {number} 章 {title}", "", "| 资料 | 本地文件 | 用途 |", "| --- | --- | --- |"]
        for r in items:
            if number not in r["chapters"]:
                continue
            local = (f"[原件]({quote(r['file'])}) · [文本]({quote(r['text'])})" if r.get("file") else "未获取")
            if r["status"] != "downloaded":
                local += f"（{r['status']}）"
            lines.append(f"| [{r['title']}]({r['source_page']}) | {local} | {r['note']} |")
        lines.append("")
    lines += ["## 获取记录", "", "以下条目不能作为已经取得的完整资料：", ""]
    gaps = [r for r in items if r["status"] not in ("downloaded", "local_snapshot", "user_provided")]
    for r in gaps:
        lines.append(f"- **{r['id']}**：{r['status']}；{r.get('error', r['note'])}。")
    if not gaps:
        lines.append("当前清单中的资料均已取得正文；清单之外的证据缺口仍见 GAPS.md。")
    lines += ["", "维护命令：`python3 references/fetch.py --only 资料ID` 下载指定条目；`--reindex` 只更新索引。直接运行会补齐失败或未获取的项目，保留已经下载的快照。需要 Python 3 和 Poppler 的 `pdftotext`、`pdfinfo`。", ""]
    (ROOT / "README.md").write_text("\n".join(lines))
    rows = []
    for r in items:
        link = f"<a href='{html.escape(r['file'])}'>原件</a> · <a href='{html.escape(r['text'])}'>离线文本</a>" if r.get("file") else "未获取"
        rows.append(f"<tr><td>{','.join(map(str,r['chapters']))}</td><td>{html.escape(r['category'])}</td><td><a href='{html.escape(r['source_page'])}'>{html.escape(r['title'])}</a></td><td>{link}</td><td>{html.escape(r['status'])}</td></tr>")
    (ROOT / "index.html").write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>AI Infra 参考资料</title><style>body{font:16px/1.6 system-ui;margin:2rem;color:#24352f}table{border-collapse:collapse;width:100%}td,th{padding:.6rem;border-bottom:1px solid #ddd;text-align:left}a{color:#14674c}input{font:inherit;padding:.5rem;width:60%}</style><h1>AI Infra 本地参考资料</h1><p>按标题、章号、类型或状态筛选。原件和文本均指向本地文件。</p><input id='q' placeholder='筛选资料'><table><thead><tr><th>章节</th><th>类型</th><th>资料</th><th>本地文件</th><th>状态</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table><script>document.querySelector('#q').oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script></html>")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--reindex", action="store_true")
    args = parser.parse_args()
    with (ROOT / "sources.tsv").open() as stream:
        sources = list(csv.DictReader(stream, delimiter="\t"))
    manifest = ROOT / "manifest.json"
    known = {r["id"]: r for r in json.loads(manifest.read_text())} if manifest.exists() else {}
    for row in sources:
        if row["id"] in known:
            known[row["id"]]["title"] = row["title"]
            known[row["id"]]["note"] = row["note"]
            known[row["id"]]["chapters"] = [int(c) for c in row["chapters"].split(",")]
    pending = [r for r in sources if not args.reindex and
               (r["id"] in args.only if args.only else r["id"] not in known or known[r["id"]]["status"] == "failed")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(fetch, row): row["id"] for row in pending}
        for job in concurrent.futures.as_completed(jobs):
            result = job.result()
            known[result["id"]] = result
            print(result["id"], result["status"], result.get("bytes", 0), flush=True)
            manifest.write_text(json.dumps(list(known.values()), ensure_ascii=False, indent=2) + "\n")
    items = [known[r["id"]] for r in sources if r["id"] in known]
    manifest.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    index(items)
    print("Indexed", len(items), "items", flush=True)


if __name__ == "__main__":
    main()
