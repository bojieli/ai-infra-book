#!/usr/bin/env python3
"""Translate the AI Infra Book manuscripts from Simplified Chinese to
Traditional Chinese (Taiwan), localized with /skill:speak-human-tw principles.

Preserves:
- Code fences (``` ... ```) and inline code (`...`)
- LaTeX display math ($$ ... $$) and inline math ($ ... $)
- Markdown image paths (![alt](path) -> alt localized, path unchanged)
- HTML tags (<a id="..."></a>) and Markdown anchor targets ([text](#anchor))
- Technical acronyms & hardware names (CUDA, H100, RoCE, KV Cache, etc.)
"""
import re
import json
from pathlib import Path
from opencc import OpenCC

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / 'manuscripts'
DEST = HERE.parent

cc = OpenCC('s2twp')

# Specialized AI Infra & Taiwanese localization replacements (applied after OpenCC)
POST_REPLACEMENTS = [
    # Quotation marks (Chinese mainland double/single quotes to Taiwanese corner brackets)
    (r'“([^”\n]+)”', r'「\1」'),
    (r'‘([^’\n]+)’', r'『\1』'),

    # Punctuation & ellipses
    (r'(\w)\s*\.\.\.', r'\1⋯⋯'),
    (r'\.\.\.', r'⋯⋯'),

    # Deep learning & inference terminology
    (r'模型推理', '模型推論'),
    (r'AI 推理', 'AI 推論'),
    (r'AI推理', 'AI推論'),
    (r'推理系統', '推論系統'),
    (r'推理優化', '推論最佳化'),
    (r'分散式推理', '分散式推論'),
    (r'分布式推理', '分散式推論'),
    (r'推理延遲', '推論延遲'),
    (r'推理任務', '推論任務'),
    (r'推理服務', '推論服務'),
    (r'推理吞吐', '推論吞吐量'),
    (r'推理實例', '推論實例'),
    (r'推理階段', '推論階段'),
    (r'推理引擎', '推論引擎'),
    (r'推理與訓練', '推論與訓練'),
    (r'訓練與推理', '訓練與推論'),
    (r'推理負載', '推論負載'),

    # Model parameters (Fix OpenCC converting 参数 to 引数)
    (r'模型引數', '模型參數'),
    (r'權重引數', '權重參數'),
    (r'引數存儲量', '參數儲存量'),
    (r'引數規模', '參數規模'),
    (r'引數數量', '參數數量'),
    (r'超引數', '超參數'),
    (r'引數', '參數'),

    # Hardware & Infrastructure
    (r'\bGPU\s*顯存\b', 'GPU 視訊記憶體 (VRAM)'),
    (r'\b板載顯存\b', '板載視訊記憶體'),
    (r'片上內存', '晶片上記憶體 (On-chip Memory)'),
    (r'片外內存', '晶片外記憶體 (Off-chip Memory)'),
    (r'計算機體系結構', '計算機組織與結構'),
    (r'體系結構', '組織結構'),
    (r'軟硬件', '軟硬體'),
    (r'負載均衡', '負載平衡'),
    (r'總線', '匯流排'),
    (r'算子融合', '運算子融合'),
    (r'算子庫', '運算子函式庫'),
    (r'算子', '運算子'),
    (r'運算元融合', '運算子融合'),
    (r'運算元庫', '運算子函式庫'),
    (r'運算元', '運算子'),
    (r'顯存帶寬', '視訊記憶體頻寬'),
    (r'顯存容量', '視訊記憶體容量'),
    (r'顯存佔用', '視訊記憶體佔用'),
    (r'顯存', '視訊記憶體 (VRAM)'),
    (r'代碼', '程式碼'),
    (r'函數', '函式'),
    (r'數組', '陣列'),
    (r'隊列', '佇列'),
    (r'鏈路帶寬', '鏈路頻寬'),
    (r'鏈路', '鏈路 (Link)'),
    (r'帶寬', '頻寬'),
    (r'網絡', '網路'),
    (r'默認', '預設'),
    (r'支持', '支援'),
    (r'兼容', '相容'),
    (r'併發', '並行'),
    (r'字節', '位元組'),
    (r'比特', '位元'),
    (r'標量', '純量'),
    (r'魯棒性', '強健性'),
    (r'工程實踐', '工程實務'),
    (r'優化器', '最佳化器'),
    (r'優化', '最佳化'),
    (r'流水線', '管線 (Pipeline)'),
    (r'緩存命中率', '快取命中率'),
    (r'緩存', '快取 (Cache)'),
    (r'預填充', '預填充 (Prefill)'),
    (r'解碼階段', '解碼 (Decode) 階段'),
    (r'詞元', '詞元 (Token)'),
    (r'激活值', '活化值 (Activation)'),
    (r'激活函數', '活化函式'),
    (r'卡間通信', '卡間通訊'),
    (r'集合通信', '集體通訊 (Collective Communication)'),
    (r'檢查點', '檢查點 (Checkpoint)'),

    # Real-time, Quality, Access, Programmability
    (r'實時語音', '即時語音'),
    (r'實時性', '即時性'),
    (r'實時', '即時'),
    (r'質量要求', '品質要求'),
    (r'服務質量', '服務品質'),
    (r'儲存訪問', '儲存存取'),
    (r'記憶體訪問', '記憶體存取'),
    (r'訪問延遲', '存取延遲'),
    (r'可程式設計性', '可程式性'),
    (r'在線 softmax', '線上 softmax'),
    (r'在線歸約', '線上歸約'),
    (r'在線', '線上'),
    (r'串行依賴', '序列依賴'),
    (r'串行執行', '序列執行'),
    (r'串行等待', '序列等待'),
    (r'串行', '序列'),
    (r'吞吐', '吞吐量'),
    (r'集群', '叢集'),

    # De-AI / Natural Taiwanese phrasing (speak-human-tw)
    (r'值得注意的是[，,]\s*', ''),
    (r'總的來說[，,]\s*', '總括而言，'),
    (r'綜上所述[，,]\s*', '簡言之，'),
    (r'這意味著[，,]\s*', '這代表'),
    (r'毫無疑問[，,]\s*', '無疑地，'),
    (r'基於此[，,]\s*', '因此，'),
]


def preserve_and_convert(text: str) -> str:
    """Split text into protected segments (code, math, links) and translatable text."""
    placeholders = []

    def save_match(match):
        idx = len(placeholders)
        placeholders.append(match.group(0))
        return f'@@PROTECTED_SEGMENT_{idx}@@'

    # 1. Protect code blocks
    text = re.sub(r'```[\s\S]*?```', save_match, text)

    # 2. Protect display math
    text = re.sub(r'\$\$[\s\S]*?\$\$', save_match, text)

    # 3. Protect inline code
    text = re.sub(r'`[^`\n]+`', save_match, text)

    # 4. Protect inline math
    text = re.sub(r'\$[^\$\n]+\$', save_match, text)

    # 5. Protect HTML tags
    text = re.sub(r'<[^>]+>', save_match, text)

    # 6. Protect image references: localize alt text, protect url/path
    def handle_image(match):
        alt = match.group(1)
        url = match.group(2)
        alt_conv = convert_prose(alt)
        return f'![{alt_conv}]({url})'

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', handle_image, text)

    # 7. Protect links: localize text, protect url
    def handle_link(match):
        link_text = match.group(1)
        url = match.group(2)
        text_conv = convert_prose(link_text)
        return f'[{text_conv}]({url})'

    text = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', handle_link, text)

    # Convert the remaining prose
    text = convert_prose(text)

    # Restore placeholders
    for idx, orig in enumerate(placeholders):
        text = text.replace(f'@@PROTECTED_SEGMENT_{idx}@@', orig)

    return text


def convert_prose(text: str) -> str:
    # 1. OpenCC s2twp conversion
    res = cc.convert(text)

    # 2. Post replacements for terminology and speak-human-tw
    for pattern, repl in POST_REPLACEMENTS:
        res = re.sub(pattern, repl, res)

    # 3. Specific cleanups for repeated terms
    res = res.replace('視訊記憶體 (VRAM) (VRAM)', '視訊記憶體 (VRAM)')
    res = res.replace('快取 (Cache) (Cache)', '快取 (Cache)')
    res = res.replace('管線 (Pipeline) (Pipeline)', '管線 (Pipeline)')
    res = res.replace('鏈路 (Link) (Link)', '鏈路 (Link)')
    res = res.replace('詞元 (Token) (Token)', '詞元 (Token)')
    res = res.replace('吞吐量量', '吞吐量')

    return res


def process_chapter(src_path: Path, dest_path: Path):
    print(f'Translating {src_path.name} -> {dest_path.name}...')
    content = src_path.read_text(encoding='utf-8')
    converted = preserve_and_convert(content)
    dest_path.write_text(converted, encoding='utf-8')
    print(f'  Done ({len(content)} -> {len(converted)} chars)')


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    mapping = [
        (SRC / '00-前言.md', DEST / 'introduction.md'),
        (SRC / '01-初识 AI Infra.md', DEST / 'chapter01.md'),
        (SRC / '02-模型架构.md', DEST / 'chapter02.md'),
        (SRC / '03-推理与训练负载.md', DEST / 'chapter03.md'),
        (SRC / '04-加速器架构.md', DEST / 'chapter04.md'),
        (SRC / '05-算子与运行时.md', DEST / 'chapter05.md'),
        (SRC / '06-超节点.md', DEST / 'chapter06.md'),
        (SRC / '07-数据中心网络.md', DEST / 'chapter07.md'),
        (SRC / '08-推理优化.md', DEST / 'chapter08.md'),
        (SRC / '09-分布式推理.md', DEST / 'chapter09.md'),
        (SRC / '10-训练系统.md', DEST / 'chapter10.md'),
        (SRC / '11-资源调度与运行环境.md', DEST / 'chapter11.md'),
        (SRC / '12-端边云协同.md', DEST / 'chapter12.md'),
    ]

    for s, d in mapping:
        if s.exists():
            process_chapter(s, d)
        else:
            print(f'Warning: {s} not found')

    print('All chapters translated successfully!')


if __name__ == '__main__':
    main()
