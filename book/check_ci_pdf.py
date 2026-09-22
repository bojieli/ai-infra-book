#!/usr/bin/env python3
"""Check the newly built full PDF and render pages for CI visual diagnostics."""
from pathlib import Path
import argparse
import json
import fitz


EDITIONS = {
    'zh': dict(name='AI-Infra-Book', expected_text=('AI Infra', '端边云'),
               required_fonts=('Songti-SC-Regular', 'Menlo-Regular', 'SourceHanSansCN-Regular',
                               'SourceHanSansCN-Bold', 'LMRoman10-Regular', 'LatinModernMath-Regular')),
    'en': dict(name='AI-Infra-Book-EN', expected_text=('AI Infra', 'Edge-Cloud Coordination'),
               required_fonts=('Menlo-Regular', 'LMRoman10-Regular', 'LatinModernMath-Regular')),
    'zh-tw': dict(name='AI-Infra-Book-ZH-TW', expected_text=('AI Infra', '端邊雲協同'),
                  required_fonts=('Menlo-Regular', 'LMRoman10-Regular', 'LatinModernMath-Regular')),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--edition', choices=EDITIONS, default='zh')
    args = parser.parse_args()
    directory = args.directory
    edition = EDITIONS[args.edition]
    report = json.loads((directory / f"{edition['name']}-build.json").read_text())
    if report['chapters'] != list(range(1, 13)):
        raise SystemExit('Expected all 12 chapters')
    doc = fitz.open(directory / f"{edition['name']}.pdf")
    if len(doc) < 12:
        raise SystemExit('PDF is unexpectedly short')
    chapter_entries = [r for r in doc.get_toc() if r[0] == 1]
    if len(chapter_entries) < 12:
        raise SystemExit('PDF is missing chapter bookmarks')
    text = ''.join(page.get_text() for page in doc)
    if any(needle not in text for needle in edition['expected_text']) or '\ufffd' in text:
        raise SystemExit('PDF text/title/last chapter check failed')
    fatal = [w for w in report['warnings'] if 'Missing character:' in w or 'undefined references' in w]
    if fatal:
        raise SystemExit('Font/reference errors:\n' + '\n'.join(fatal))
    # Inspect fonts actually used by text, not just unused PDF resources.
    fonts = sorted({
        span['font']
        for page in doc
        for block in page.get_text('dict')['blocks']
        for line in block.get('lines', [])
        for span in line['spans']
    })
    missing = [font for font in edition['required_fonts'] if not any(font in actual for actual in fonts)]
    # Figure PDFs may intentionally contain DejaVu Sans mathematical glyphs.
    fallbacks = [font for font in fonts if 'NotoSansCJK' in font or 'DejaVuSansMono' in font]
    if missing or fallbacks:
        raise SystemExit(f'PDF font parity failed: missing={missing}, fallbacks={fallbacks}')
    pages = sorted({0, min(8, len(doc)-1), len(doc)//2, len(doc)-1})
    for number in pages:
        doc[number].get_pixmap(matrix=fitz.Matrix(1, 1)).save(directory / f'preview-{number+1:03}.png')
    result = dict(passed=True, pages=len(doc), chapters=report['chapters'],
                  figures=report['figure_count'], source_ref=report['source_ref'],
                  fonts=fonts,
                  layout_warnings=report['warnings'], preview_pages=[p+1 for p in pages])
    (directory / 'pdf-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(f'PASS: {len(doc)} pages, 12 chapters, readable text, fonts and references')


if __name__ == '__main__':
    main()
