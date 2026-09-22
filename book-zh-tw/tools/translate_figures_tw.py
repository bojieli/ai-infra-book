#!/usr/bin/env python3
"""Translate figure labels from Simplified Chinese to Traditional Chinese (Taiwan),
preserving code AST structure, and render localized vector figures.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from opencc import OpenCC

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / 'manuscripts'
CATALOG_EN = ROOT / 'book-en' / 'tools' / 'figure-strings.json'
CATALOG_TW = HERE / 'figure-strings-tw.json'
BOOK_TW = ROOT / 'book-zh-tw'

cc = OpenCC('s2twp')

FIGURE_REPLACEMENTS = [
    (r'平臺', '平台'),
    (r'例項', '實例'),
    (r'推理', '推論'),
    (r'排隊', '佇列'),
    (r'工藝', '製程'),
    (r'運算元', '運算子'),
    (r'顯存', '視訊記憶體 (VRAM)'),
    (r'內存', '記憶體'),
    (r'帶寬', '頻寬'),
    (r'網絡', '網路'),
    (r'緩存', '快取'),
    (r'代碼', '程式碼'),
    (r'函數', '函式'),
    (r'數組', '陣列'),
    (r'隊列', '佇列'),
    (r'調度', '排程'),
    (r'並發', '並行'),
    (r'流水線', '管線 (Pipeline)'),
    (r'負載均衡', '負載平衡'),
    (r'總線', '匯流排'),
    (r'引數', '參數'),
    (r'預填充', '預填充 (Prefill)'),
    (r'解碼', '解碼 (Decode)'),
    (r'詞元', '詞元 (Token)'),
    (r'激活值', '活化值 (Activation)'),
    (r'實時', '即時'),
    (r'“([^”\n]+)”', r'「\1」'),
    (r'‘([^’\n]+)’', r'『\1』'),
]

def convert_fig_text(text: str) -> str:
    res = cc.convert(text)
    for p, r in FIGURE_REPLACEMENTS:
        res = re.sub(p, r, res)
    res = res.replace('視訊記憶體 (VRAM) (VRAM)', '視訊記憶體 (VRAM)')
    res = res.replace('快取 (Cache) (Cache)', '快取 (Cache)')
    return res

FILE_EXT = ('.md', '.json', '.py', '.pdf', '.png', '.svg', '.csv', '.txt',
            '.jsonl', '.yaml', '.yml', '.ttf', '.otf', '.npz', '.npy')

def _disk_names() -> set[str]:
    try:
        return {p.name for p in SRC.rglob('*') if p.is_file()}
    except OSError:
        return set()

_NAMES: set[str] | None = None

def looks_like_path(s: str) -> bool:
    global _NAMES
    t = s.strip()
    if t.endswith(FILE_EXT):
        return True
    if len(t) < 2:
        return False
    if _NAMES is None:
        _NAMES = _disk_names()
    stem = re.compile(r'^\d+[-_]' + re.escape(t) + r'\.[A-Za-z0-9]+$')
    return any(stem.match(name) for name in _NAMES)

def _path_context_nodes(tree: ast.AST) -> set:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            literal = ''.join(v.value for v in node.values
                              if isinstance(v, ast.Constant) and isinstance(v.value, str))
            if re.search(r'\.[A-Za-z0-9]{1,6}$', literal.strip()):
                for v in ast.walk(node):
                    if isinstance(v, ast.Constant):
                        out.add(id(v))
        if isinstance(node, ast.Call):
            name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
            if name in {'Path', 'open', 'glob', 'rglob', 'read_text', 'read_bytes',
                        'write_text', 'joinpath'}:
                for v in ast.walk(node):
                    if isinstance(v, ast.Constant):
                        out.add(id(v))
        if isinstance(node, ast.Compare):
            for v in ast.walk(node):
                if isinstance(v, ast.Constant):
                    out.add(id(v))
    return out

CHECKERS = ('verify', 'check', 'browser', 'book_assets', 'math_style', 'teaching_reading')
CJK = re.compile(r'[\u4e00-\u9fff]')

def scripts(only: str | None = None) -> list[Path]:
    candidates = list(SRC.glob('ch[0-9][0-9]/*.py')) + list(SRC.glob('*.py'))
    return sorted(
        p for p in candidates
        if CJK.search(p.read_text(encoding='utf-8'))
        and not p.name.endswith('.en.py')
        and not p.name.endswith('.tw.py')
        and not any(x in p.name for x in CHECKERS)
        and (only is None or only in str(p.parent.name))
    )

def cjk_constants(tree: ast.AST):
    protected = _path_context_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in protected:
                continue
            if looks_like_path(node.value):
                continue
            if CJK.search(node.value):
                yield node

def build_catalog():
    en_cat = json.loads(CATALOG_EN.read_text(encoding='utf-8'))
    tw_cat = {}
    for zh, data in en_cat.items():
        if looks_like_path(zh):
            continue
        tw_cat[zh] = {
            'zh_tw': convert_fig_text(zh),
            'files': data.get('files', [])
        }
    CATALOG_TW.write_text(json.dumps(tw_cat, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(tw_cat)} terms to {CATALOG_TW}')
    return tw_cat

def apply_to(path: Path, catalog: dict) -> tuple[str, int]:
    raw = path.read_bytes()
    source = raw.decode('utf-8')
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line.encode('utf-8')))

    tree = ast.parse(source)
    in_fstring = {id(c) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr)
                  for c in ast.walk(n) if isinstance(c, ast.Constant)}

    edits = []
    for node in cjk_constants(tree):
        val = node.value
        entry = catalog.get(val)
        tw = entry['zh_tw'] if entry else convert_fig_text(val)
        if not tw or tw == val:
            continue
        start = offsets[node.lineno - 1] + node.col_offset
        end = offsets[node.end_lineno - 1] + node.end_col_offset
        if id(node) in in_fstring:
            rep = (tw.replace('{', '{{').replace('}', '}}')
                     .replace('\n', '\\n').replace('\r', '\\r')
                     .replace('\t', '\\t')).encode('utf-8')
        else:
            rep = json.dumps(tw, ensure_ascii=False).encode('utf-8')
        edits.append((start, end, rep))

    out = raw
    for start, end, rep in sorted(edits, reverse=True):
        out = out[:start] + rep + out[end:]
    return out.decode('utf-8'), len(edits)

def main():
    catalog = build_catalog()
    for s in scripts():
        translated, n = apply_to(s, catalog)
        out_path = s.with_suffix('.tw.py')
        out_path.write_text(translated, encoding='utf-8')
        print(f'{str(s.relative_to(SRC)):35s} -> {out_path.name} ({n} edits)')

if __name__ == '__main__':
    main()
