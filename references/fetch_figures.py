#!/usr/bin/env python3
"""Archive figures from explicitly selected, already archived HTML documents."""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent


class Figures(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            values = dict(attrs)
            url = values.get("src") or values.get("data-src")
            if url:
                self.images.append((url, values.get("alt", "")))


def retrieve(item):
    try:
        request = urllib.request.Request(item["url"], headers={"User-Agent": "AI-Infra-Book-Reference-Archive/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
            mime = response.headers.get("Content-Type", "").split(";")[0]
            resolved = response.url
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
                  "image/svg+xml": ".svg"}.get(mime)
        if not suffix:
            raise ValueError(f"Expected an image, received {mime}")
        name = item["source_id"] + "-" + hashlib.sha256(item["url"].encode()).hexdigest()[:12] + suffix
        dest = ROOT / "figures" / name
        dest.write_bytes(data)
        item.update(status="downloaded", file=str(dest.relative_to(ROOT)), sha256=hashlib.sha256(data).hexdigest(),
                    bytes=len(data), content_type=mime, resolved_url=resolved,
                    retrieved_at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        item.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="+", help="Source IDs from manifest.json")
    args = parser.parse_args()
    docs = {r["id"]: r for r in json.loads((ROOT / "manifest.json").read_text())}
    output = ROOT / "figures"
    output.mkdir(exist_ok=True)
    manifest = output / "manifest.json"
    old = json.loads(manifest.read_text()) if manifest.exists() else []
    known = {(r["source_id"], r["url"]): r for r in old}
    pending = {}
    for ident in args.ids:
        doc = docs[ident]
        if not doc["file"].endswith(".html"):
            raise ValueError(f"{ident} is not an HTML source")
        reader = Figures()
        reader.feed((ROOT / doc["file"]).read_text())
        for raw_url, alt in reader.images:
            url = urllib.parse.urljoin(doc.get("resolved_url", doc["url"]), raw_url)
            if ident == "google-tpu8":
                include = "storage.googleapis.com/gweb-cloudblog-publish/images/" in url and url.endswith(".png")
            else:
                include = "/_images/" in url
            if not include or urllib.parse.urlsplit(url).scheme != "https":
                continue
            key = (ident, url)
            previous = known.get(key)
            if previous and previous["status"] == "downloaded" and previous.get("source_sha256") == doc["sha256"]:
                cached = ROOT / previous["file"]
                if cached.is_file() and hashlib.sha256(cached.read_bytes()).hexdigest() == previous["sha256"]:
                    continue
            pending[key] = dict(source_id=ident, source_sha256=doc["sha256"], source_page=doc["source_page"],
                                url=url, alt=alt)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for item in pool.map(retrieve, pending.values()):
            known[(item["source_id"], item["url"])] = item
            print(item["source_id"], item["status"], flush=True)
    items = list(known.values())
    manifest.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 网页配图原件", "", "从明确选取的官方网页下载配图，保留原始图像，不重绘或修改。来源网页快照与每幅图的校验值见 [manifest.json](manifest.json)。这些配图不另计作论文或规格文档。", "", "维护命令：`python3 references/fetch_figures.py 资料ID ...`。仅处理指定的已归档网页，不递归抓取站点；已有且校验通过的图片不重复下载。", ""]
    for ident in dict.fromkeys(r["source_id"] for r in items):
        lines += [f"## {docs[ident]['title']}", "", f"[本地正文](../{docs[ident]['file']}) · [官方来源]({docs[ident]['source_page']})", ""]
        for r in items:
            if r["source_id"] == ident:
                if r["status"] == "downloaded":
                    caption = r["alt"] if r["alt"] and not r["alt"].startswith("http") else Path(urllib.parse.urlsplit(r["url"]).path).name
                    lines.append(f"- [{caption}]({Path(r['file']).name})")
                else:
                    lines.append(f"- 未获取：{r['url']}；{r['error']}")
        lines.append("")
    (output / "README.md").write_text("\n".join(lines))
    print("Indexed", len(items), "figures", flush=True)


if __name__ == "__main__":
    main()
