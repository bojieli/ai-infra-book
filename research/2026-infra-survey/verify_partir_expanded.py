"""Check the supplemental PartIR reading proof against archived primary bytes.

Reading is attested by the named worker; extraction/integrity checks alone do
not establish human reading, compiler correctness, or measured performance.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'references/framework-history/2026-09-09/partir-shardy'
EXTRA = BASE / 'expanded-reading'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    proof = json.loads((EXTRA / 'reading-proof.json').read_text())
    mapping = json.loads((EXTRA / 'file-map.json').read_text())['files']
    sources = json.loads((EXTRA / 'sources.json').read_text())

    def data(name):
        path = (ROOT / mapping[name]).resolve()
        assert path.is_relative_to(BASE.resolve()), name
        return path.read_bytes()

    for item in sources:
        raw = data(item['file'])
        assert sha(raw) == item['sha256'] and len(raw) == item['bytes']
    commit = json.loads(data('shardy-commit.json'))
    assert commit['sha'] == proof['fixed_source_commit'] == 'a72dc82ce730c55be36a409945f4224181d050fc'
    pdf = ROOT / mapping['partir-v4.pdf']
    assert pdf.read_bytes() == (BASE / 'partir-v4.pdf').read_bytes()
    page_numbers = []
    for item in proof['read_selections']:
        raw = data(item['file'])
        assert sha(raw) == item['sha256'], item['file']
        lines = raw.splitlines()
        for first, last in item['line_ranges']:
            assert 1 <= first <= last <= len(lines), item['file']
        if 'physical_page' in item:
            page = item['physical_page']
            regenerated = subprocess.check_output(
                ['pdftotext', '-layout', '-f', str(page), '-l', str(page), str(pdf), '-'],
                stderr=subprocess.PIPE,
            )
            assert regenerated == raw + b'\f', page
            if item['scope'] == 'full extracted page text':
                assert item['line_ranges'] == [[1, len(lines)]]
                page_numbers.append(page)
            else:
                assert page == 33 and item['line_ranges'] == [[40, 59]]
    assert page_numbers == proof['paper']['full_text_pages_read']
    assert page_numbers == list(range(1, 14)) + list(range(17, 24))
    for item in proof['viewed_images']:
        assert sha(data(item['file'])) == item['sha256']
        assert item['viewed'] is True
    for item in proof['book_snapshots']:
        raw = data(item['snapshot'])
        assert sha(raw) == item['sha256'] and len(raw) == item['bytes']
    original = data('root-reading-before-integration.json')
    assert sha(original) == proof['integration_delta']['comparison_sha256']
    assert original == (BASE / 'reading.json').read_bytes()
    previous = json.loads(original)
    old_pages = {item['physical_page'] for item in previous['pages']}
    delta = sorted(set(page_numbers) - old_pages)
    assert delta == proof['integration_delta']['new_full_paper_pages']
    result = {
        'status': 'passed',
        'scope': 'Supplemental worker-attested reading; independent primary-byte, extraction and delta validation. No compiler tests or performance reproduction.',
        'read_selections': len(proof['read_selections']),
        'full_pages': page_numbers,
        'partial_page': {'physical_page': 33, 'lines': [40, 59]},
        'additional_full_pages': delta,
        'viewed_pages_attested': [x['physical_page'] for x in proof['viewed_images']],
        'source_entries': len(sources),
        'new_abstracts': 0, 'new_pdfs': 0, 'new_papers_with_selected_reading': 0,
        'downloaded_code_executed': False,
    }
    (EXTRA / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
