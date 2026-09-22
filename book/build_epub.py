#!/usr/bin/env python3
"""Build reflowable EPUB 3 editions from the same sources as the PDFs.

The PDF is typeset for a fixed page; on phones and e-ink readers readers need
text that reflows and follows their own font size. This script feeds the
Markdown the PDF builds use through Pandoc's EPUB writer instead of LaTeX:

- formulas become MathML, so they stay text and scale with the font;
- figures are rasterized from the same vector PDFs the PDF edition embeds
  (SVG text would depend on fonts the reader may not have);
- links into the repository become GitHub links, links between chapters
  become links inside the book.

Usage (from the repository root):
    python3 book/build_epub.py                 # Chinese edition
    python3 book/build_epub.py --edition en    # English edition
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANUSCRIPTS = ROOT / 'manuscripts'
BOOK_EN = ROOT / 'book-en'
REPO = 'https://github.com/bojieli/ai-infra-book'
LFS_POINTER = b'version https://git-lfs.github.com/spec/v1'
FIGURE_WIDTH = 1400  # pixels; sharp on a 300 ppi reader, small enough for phones

EDITIONS = {
    'zh': dict(name='AI-Infra-Book', lang='zh-Hans', author='李博杰',
               title='深入理解 AI Infra', subtitle='量化分析与系统设计',
               toc_title='目录', footnotes_title='注释'),
    'en': dict(name='AI-Infra-Book-EN', lang='en-US', author='Bojie Li',
               title='Understanding AI Infra', subtitle='Quantitative Analysis and System Design',
               toc_title='Contents', footnotes_title='Notes'),
    'zh-tw': dict(name='AI-Infra-Book-ZH-TW', lang='zh-Hant', author='李博杰',
                  title='深入理解 AI Infra', subtitle='量化分析與系統設計',
                  toc_title='目錄', footnotes_title='註釋'),
}


def sources(edition):
    """(number, path) for the preface (0) and chapters 1-12."""
    if edition == 'zh':
        return [(n, next(MANUSCRIPTS.glob(f'{n:02}-*.md'))) for n in range(13)]
    elif edition == 'zh-tw':
        book_tw = ROOT / 'book-zh-tw'
        return [(0, book_tw / 'introduction.md')] + [(n, book_tw / f'chapter{n:02}.md') for n in range(1, 13)]
    return [(0, BOOK_EN / 'introduction.md')] + [(n, BOOK_EN / f'chapter{n:02}.md') for n in range(1, 13)]


def prepared_name(edition, number):
    """File name of a chapter inside the build directory."""
    return dict(sources(edition))[number].stem + '.md'


def chapter_anchors():
    """Map each Chinese manuscript file name to its chapter anchor."""
    return {p.name: f'chapter-{int(p.name[:2])}' for p in MANUSCRIPTS.glob('[01][0-9]-*.md')}


def rasterize(pdf, cache):
    """Render one vector figure to PNG, cached by content hash."""
    data = pdf.read_bytes()
    if data.startswith(LFS_POINTER):
        raise ValueError(f'Figure is an LFS pointer; run git lfs pull: {pdf}')
    digest = hashlib.sha256(data).hexdigest()[:16]
    png = cache / f'{pdf.stem}-{digest}.png'
    if not png.exists():
        subprocess.run(['pdftoppm', '-png', '-singlefile', '-scale-to-x', str(FIGURE_WIDTH),
                        '-scale-to-y', '-1', str(pdf), str(png.with_suffix(''))], check=True)
    return png


def prepare(number, source, edition, source_ref, figures):
    text = source.read_text(encoding='utf-8')
    base = source.parent
    # Chapter titles keep their visible number ("第 2 章 …" / "Chapter 2 …") because
    # section headings carry manual numbers (2.1, 2.1.1) and EPUB does not number.
    if number == 0:
        text = re.sub(r'^# (.+?)\s*$', r'# \1 {#preface}', text, count=1, flags=re.M)
    elif edition == 'zh':
        text = re.sub(r'^# (第\s*\d+\s*章.*?)\s*$', rf'# \1 {{#chapter-{number}}}', text, count=1, flags=re.M)
    else:
        text = re.sub(r'^# (.+?)\s*$', rf'# Chapter {number}  \1 {{#chapter-{number}}}', text, count=1, flags=re.M)
    text = re.sub(r'<a id="([^"]+)"></a>\s*\n+(#{1,6} [^\n]+)',
                  lambda m: m[2] + ' {#' + m[1] + '}', text)
    # Manuscripts repeat image alt text as the following italic caption. Merge them.
    text = re.sub(r'!\[[^\n]*\]\(([^)]+)\)\s*\n\s*\*([^\n]+)\*',
                  lambda m: f'![{m[2]}]({m[1]})', text)

    def image(match):
        original = (base / unquote(match[2])).resolve()
        pdf = original.with_suffix('.pdf')
        if pdf.exists():
            figures.append(pdf)
        elif original.with_suffix('.png').exists():
            figures.append(original.with_suffix('.png'))
        else:
            raise FileNotFoundError(original)
        return f'![{match[1]}](figure:{len(figures) - 1})'
    text = re.sub(r'!\[([^\n]*)\]\(([^)]+)\)', image, text)

    anchors = chapter_anchors()
    ref = quote(source_ref or 'main', safe='')

    def link(match):
        label, target = match[1], match[2]
        if target.startswith('#'):
            return match[0]
        # The English edition already carries absolute links into the repository.
        target = re.sub(r'^https://github\.com/bojieli/ai-infra-book/blob/main/', '/', target)
        if re.match(r'[a-z]+:', target):
            return match[0]
        path, _, fragment = target.partition('#')
        if path.startswith('/'):
            resolved = (ROOT / unquote(path[1:])).resolve()
        else:
            resolved = (base / unquote(path)).resolve()
        if not resolved.is_relative_to(ROOT):
            return match[0]
        # Links between chapters stay inside the book.
        # Pandoc's --file-scope resolves "file.md#id" across the input files.
        if resolved.parent == MANUSCRIPTS and resolved.name in anchors:
            other = quote(prepared_name(edition, int(resolved.name[:2])))
            return f'[{label}]({other}#{fragment or anchors[resolved.name]})'
        relative = quote(resolved.relative_to(ROOT).as_posix(), safe='/')
        suffix = f'#{fragment}' if fragment else ''
        return f'[{label}]({REPO}/blob/{ref}/{relative}{suffix})'
    text = re.sub(r'(?<!!)\[([^\]]*)\]\(([^)]+)\)', link, text)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edition', choices=EDITIONS, default='zh')
    parser.add_argument('--output-dir', type=Path, default=None,
                        help='Output directory (default: book/ or book-en/)')
    parser.add_argument('--cover', type=Path, default=None,
                        help='Cover PNG (default: the one the PDF build exported, if present)')
    parser.add_argument('--source-ref', help='Git commit for GitHub links in released EPUBs')
    args = parser.parse_args()
    meta = EDITIONS[args.edition]
    home = HERE if args.edition == 'zh' else BOOK_EN
    output_dir = (args.output_dir or home).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work = HERE / 'build' / f'{meta["name"]}-epub'
    cache = HERE / 'build' / 'epub-figures'
    work.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    figures, prepared = [], []
    for number, source in sources(args.edition):
        prepared.append((number, source, prepare(number, source, args.edition, args.source_ref, figures)))
    with ThreadPoolExecutor() as pool:
        rendered = list(pool.map(lambda f: f if f.suffix == '.png' else rasterize(f, cache), figures))
    inputs = []
    for number, source, text in prepared:
        text = re.sub(r'\(figure:(\d+)\)', lambda m: f'({rendered[int(m[1])].as_posix()})', text)
        target = work / prepared_name(args.edition, number)
        target.write_text(text, encoding='utf-8')
        inputs.append(target.name)

    cover = args.cover or output_dir / f'{meta["name"]}-Cover.png'
    metadata = work / 'metadata.yaml'
    today = datetime.date.today().isoformat()
    metadata.write_text(json.dumps({
        'title': [{'type': 'main', 'text': meta['title']}, {'type': 'subtitle', 'text': meta['subtitle']}],
        'creator': [{'role': 'author', 'text': meta['author']}],
        'lang': meta['lang'], 'date': today, 'rights': 'CC BY-NC-SA 4.0',
        'identifier': [{'scheme': 'URI', 'text': f'{REPO}#{meta["name"]}'}],
        'toc-title': meta['toc_title'],
    }, ensure_ascii=False))
    output = output_dir / f'{meta["name"]}.epub'
    staged = output.with_suffix('.epub.tmp')
    command = ['pandoc', *inputs, '--from=markdown+lists_without_preceding_blankline',
               '--file-scope', '--to=epub3', '--metadata-file=' + str(metadata), '--mathml',
               '--toc', '--toc-depth=2', '--split-level=1',
               '--css=' + str(HERE / 'epub.css'), '--highlight-style=kate',
               '-o', str(staged)]
    if cover.exists():
        command.append('--epub-cover-image=' + str(cover))
    else:
        print(f'No cover at {cover}; building without one (run build_pdf.sh first to export it)')
    log = work / 'pandoc.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=work, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit(f'Build failed; see {log}\n' + log.read_text(errors='replace')[-6000:])
    staged.replace(output)
    warnings = [line for line in log.read_text(errors='replace').splitlines() if line.strip()]
    report = dict(output=str(output), source_ref=args.source_ref, edition=args.edition,
                  engine='Pandoc EPUB 3 (MathML)', cover=cover.exists(),
                  sources=[dict(path=str(s.relative_to(ROOT)), sha256=hashlib.sha256(s.read_bytes()).hexdigest())
                           for _, s, _ in prepared],
                  figure_count=len(figures), size_bytes=output.stat().st_size, warnings=warnings)
    (output_dir / f'{meta["name"]}-epub-build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(output)
    print(f'{len(inputs) - 1} chapters, {len(figures)} figures, {output.stat().st_size / 1e6:.1f} MB; '
          f'{len(warnings)} Pandoc warnings; details: {log}')


if __name__ == '__main__':
    main()
