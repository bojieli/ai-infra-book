"""Merge separately reviewed MICRO batches by DOI, preserving the original archive."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/MICRO/2024'


def verify(base=None):
    if base is None:
        from verify_micro2024 import verify as check_base
        base = check_base()
    assert not base['errors']
    packet = D / 'parallel-abstracts'
    subprocess.run([sys.executable, str(packet / 'verify.py')], check=True, capture_output=True)
    handoff = json.loads((packet / 'verification.json').read_text())
    assert handoff['status'] == 'PASS' and handoff['body_pages_read'] == 0
    manifest = json.loads((D / 'manifest.json').read_text())
    papers = {p['program_order']: p for p in manifest['papers']}
    canonical = json.loads((D / 'public-abstracts.json').read_text())['papers']
    entries = {n: {'program_order': n, 'doi': p['doi'], 'title': p['publisher_title'],
                   'abstract_read': False, 'representative_pdf': None,
                   'selected_reading': None, 'provenance': []} for n, p in papers.items()}
    assert len(entries) == len({p['doi'] for p in entries.values()}) == 113
    for r in canonical:
        e = entries[r['program_order']]
        assert r['doi'] == e['doi'] and not e['abstract_read']
        e['abstract_read'] = True
        e['provenance'].append(str((D / 'public-abstracts.json').relative_to(ROOT)))
        e['selected_reading'] = r.get('selected_reading')
        if r.get('pdf_pages'):
            e['representative_pdf'] = {'file': r['pdf_file'], 'sha256': r['pdf_sha256'], 'pages': r['pdf_pages']}
    assert sum(e['abstract_read'] for e in entries.values()) == base['primary_abstracts_screened']
    path = packet / 'abstracts.json'
    for r in json.loads(path.read_text())['papers']:
        n = r['program_order']
        e = entries[n]
        assert r['doi'] == e['doi'] and not e['abstract_read']
        assert r['publisher_title'] == papers[n]['publisher_title']
        assert r['publisher_authors'] == papers[n]['publisher_authors']
        e['abstract_read'] = True
        e['provenance'].append(str(path.relative_to(ROOT)))
        e['adoption'] = r['screening']
        if r['pdf_pages']:
            e['representative_pdf'] = {'file': str((packet / r['source_file']).relative_to(ROOT)),
                                       'sha256': r['source_sha256'], 'pages': r['pdf_pages']}
    summary = {
        'status': 'passed', 'scope': 'Unique MICRO2024 DOIs; original archive preserved; abstract-only additions add no body scope.',
        'matched_papers': len(entries),
        'primary_abstracts_screened': sum(e['abstract_read'] for e in entries.values()),
        'public_pdfs': sum(e['representative_pdf'] is not None for e in entries.values()),
        'pdf_pages': sum(e['representative_pdf']['pages'] for e in entries.values() if e['representative_pdf']),
        'selected_sections_read': sum(e['selected_reading'] is not None for e in entries.values()),
        'remaining_abstract_orders': [n for n, e in entries.items() if not e['abstract_read']],
        'additional_full_primary_abstracts': 6, 'errors': [],
    }
    summary['remaining_abstracts'] = len(summary['remaining_abstract_orders'])
    assert (summary['primary_abstracts_screened'], summary['public_pdfs'], summary['pdf_pages'], summary['selected_sections_read']) == (47, 43, 666, 1)
    (D / 'reading-coverage.json').write_text(json.dumps({'summary': summary, 'records': list(entries.values())}, ensure_ascii=False, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
