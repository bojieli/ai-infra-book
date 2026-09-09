"""Independent re-extraction from raw originals. Python stdlib + Poppler only."""
from pathlib import Path
from hashlib import sha256
import json, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bundle_lib import ORDERS, PDFS, extract, identities, verify_identities, first_page, html, whitespace

def verify_bundle(root, bundle_path):
    base = Path(bundle_path)
    if not base.is_absolute(): base = Path(root) / base
    records = json.loads((base / 'reading-records.json').read_text())
    def local(path): return base / Path(path).name
    hashes = 0
    def walk(x):
        nonlocal hashes
        if isinstance(x, dict):
            if 'file' in x and 'sha256' in x:
                b = local(x['file']).read_bytes()
                assert sha256(b).hexdigest() == x['sha256'], x['file']
                if 'bytes' in x: assert len(b) == x['bytes'], x['file']
                hashes += 1
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(records)
    for x in json.loads((base / 'local-copy-provenance.json').read_text()):
        b = (base / x['destination']).read_bytes()
        assert sha256(b).hexdigest() == x['sha256'] and len(b) == x['bytes']
    identity = verify_identities(base)
    official = identities(base)
    assert [r['program_order'] for r in records['records']] == ORDERS
    for r in records['records']:
        x = official[r['program_order']]
        assert r['doi'] == x['DOI'] and r['title'] == x['title'][0]
        assert r['authors'] == [a.get('given', '') + ' ' + a['family'] for a in x['author']]
        text, source, rule = extract(base, r['program_order'])
        assert text == r['abstract'] and sha256(text.encode()).hexdigest() == r['abstract_sha256']
        assert local(r['abstract_text_file']['file']).read_text() == text + '\n'
        assert rule == r['extraction'] and Path(r['source_file']).name == source
        assert r['selected_reading']['physical_pdf_pages'] == []
        if r['program_order'] in PDFS:
            prefix = PDFS[r['program_order']]
            for suffix, mode in [('first.txt','default'), ('first-layout.txt','layout')]:
                assert first_page(base, prefix, mode) == (base / (prefix + '.' + suffix)).read_bytes()
            if r['program_order'] in [174,179]:
                assert first_page(base,prefix,'raw') == (base / (prefix + '.first-raw.txt')).read_bytes()
    for order in [176,177]:
        current = json.loads((base / f'{order}-crossref.json').read_text())['message']
        old = official[order]
        assert current['DOI'] == old['DOI'] and current['title'] == old['title']
        assert [(a.get('given'),a['family']) for a in current['author']] == [(a.get('given'),a['family']) for a in old['author']]
    old = whitespace(''.join(html(base, '173-arxiv-v1.html').abstract))
    assert (base / '173-v1-abstract.txt').read_text() == old + '\n'
    assert '66.3%' in old and '77.2%' in old
    assert '67.3%' in records['records'][0]['abstract'] and '24.2%' in records['records'][0]['abstract']
    assert records['selected_body_physical_pages'] == records['selected_body_reading_records'] == 0
    return {'status': 'passed_with_explicit_version_limits', 'full_abstracts': 6,
      'representative_pdfs': 5, 'representative_pdf_pages': 76, 'body_pages_read': 0,
      'abstract_identity_pages': 5, 'hash_records_checked': hashes,
      'identity_reextraction': identity, 'unresolved': records['unresolved']}

if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    print(json.dumps(verify_bundle(Path.cwd(), path), ensure_ascii=False, indent=2))
