"""Capture every writing surface, rather than searching only for experiment labels.

This is a review inventory, not an automatic proof that all calculations have been
implemented. Changed content reopens its review; exact unchanged content retains it.
"""
import hashlib
import json
import re

from .paths import BOOK, PROJECT


def collect() -> dict:
    path = PROJECT / "inventory/sources.json"
    previous = json.loads(path.read_text()) if path.exists() else {"items": []}
    previous_items = {(item["file"], item["title"], item["sha256"]): item for item in previous["items"]}
    files, items = [], []
    surfaces = (sorted((BOOK / "outlines").glob("[0-9][0-9]-*.md"))
                + sorted((BOOK / "outlines/extensions").glob("[0-9][0-9]-*.md"))
                + sorted((BOOK / "case-studies").glob("*.md")))
    for source in surfaces:
        text = source.read_text()
        relative = str(source.relative_to(BOOK))
        surface = "extension" if "/extensions/" in relative else "outline" if relative.startswith("outlines/") else "case"
        files.append({"file": relative, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        offset = 0
        for index, chunk in enumerate(re.split(r"(?m)(?=^#{1,4} |^> \*\*实验 )", text)):
            if chunk.strip():
                title = chunk.splitlines()[0]
                section = re.match(r"### (\d+\.\d+\.\d+)", title)
                exercise = re.match(r"> \*\*实验 (\d+-\d+)", title)
                digest = hashlib.sha256(chunk.strip().encode()).hexdigest()
                old = previous_items.get((relative, title, digest), {})
                items.append({"id": f"{relative}::{index:03d}", "surface": surface, "file": relative,
                              "line": text.count("\n", 0, offset) + 1, "title": title,
                              "section": section[1] if section else None,
                              "exercise": exercise[1] if exercise else None,
                              "text": chunk.strip(), "sha256": digest,
                              "review_status": old.get("review_status", "pending"),
                              "work_packages": old.get("work_packages", [])})
            offset += len(chunk)
    return {"schema_version": 1, "files": files, "items": items}


def audit(refresh: bool = False) -> dict:
    current = collect()
    path = PROJECT / "inventory/sources.json"
    saved = json.loads(path.read_text()) if path.exists() else {"files": []}
    before = {row["file"]: row["sha256"] for row in saved["files"]}
    after = {row["file"]: row["sha256"] for row in current["files"]}
    changed = [name for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
    if refresh:
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    return {"files": len(current["files"]), "items": len(current["items"]),
            "main_subsections": sum(item["surface"] == "outline" and item["section"] is not None for item in current["items"]),
            "main_exercises": sum(item["surface"] == "outline" and item["exercise"] is not None for item in current["items"]),
            "pending_review": sum(item["review_status"] == "pending" for item in current["items"]),
            "changed_files": changed, "snapshot_refreshed": refresh,
            "scope_note": "Capturing source text is not implementation coverage; work-package review remains explicit."}
