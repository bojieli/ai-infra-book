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
    for folder in ('parallel-abstracts', 'parallel-abstracts-next', 'parallel-abstracts-third', 'parallel-abstracts-fourth', 'parallel-abstracts-fifth', 'parallel-abstracts-sixth', 'parallel-abstracts-seventh', 'parallel-abstracts-eighth', 'parallel-abstracts-ninth'):
        packet = D / folder
        subprocess.run([sys.executable, str(packet / 'verify.py')], check=True, capture_output=True)
        handoff = json.loads((packet / 'verification.json').read_text())
        assert handoff['status'] == 'PASS' and handoff['body_pages_read'] == 0
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
        for gap in json.loads(path.read_text()).get('unavailable', []):
            e = entries[gap['program_order']]
            assert e['doi'] == gap['doi'] and not e['abstract_read']
            e['provenance'].append(str(path.relative_to(ROOT)))
            e['unavailable'] = gap
    from verify_sparsepipe_body import verify as check_sparsepipe_body
    sparse = check_sparsepipe_body()
    entry = entries[88]
    assert entry['doi'].lower() == '10.1109/micro61859.2024.00090' and entry['abstract_read'] and entry['selected_reading'] is None
    scope_path = D / 'sparsepipe-body-reading/reading.json'
    entry['selected_reading'] = {'proof_file': str(scope_path.relative_to(ROOT)), 'physical_pdf_pages': sparse['full_page_text_read_pages'], 'partial_physical_pages': sparse['partial_page_text_read_pages'], 'scope': 'Full text of p3–13 and two partial p14 ranges; no new abstract/PDF.'}
    entry['provenance'].append(str(scope_path.relative_to(ROOT)))
    entry['adoption'] = {'decision': 'existing_experiment_extension', 'reason': 'Existing5.3.1 distinguishes intermediate-vector traffic from same-matrix reuse; ideal byte example, not current GPU framework implementation.'}
    from verify_floatap_body import verify as check_floatap_body
    floatap = check_floatap_body()
    entry = entries[49]
    assert entry['doi'].lower() == '10.1109/micro61859.2024.00055'
    assert entry['abstract_read'] and entry['selected_reading'] is None
    floatap_path = D / 'floatap-body-reading/reading.json'
    entry['selected_reading'] = {'proof_file': str(floatap_path.relative_to(ROOT)),
        'physical_pdf_pages': floatap['full_body_text_pages'], 'partial_physical_pages': [13],
        'scope': 'Reading agent full p2–12, p13 left-column related work/conclusion; root visually checked p9. Not full paper.'}
    entry['provenance'].append(str(floatap_path.relative_to(ROOT)))
    entry['adoption'] = {'decision': 'existing_experiment_optional_variant',
        'reason': 'Existing5.2.1/5-2 separates replicated operand slots from instruction cycles; no framework performance or full-workset claim.'}
    summary = {
        'status': 'passed', 'scope': 'Unique MICRO2024 DOIs; original archive preserved; abstract batches add no body scope; separately verified Sparsepipe reading is counted once.',
        'matched_papers': len(entries),
        'primary_abstracts_screened': sum(e['abstract_read'] for e in entries.values()),
        'public_pdfs': sum(e['representative_pdf'] is not None for e in entries.values()),
        'pdf_pages': sum(e['representative_pdf']['pages'] for e in entries.values() if e['representative_pdf']),
        'selected_sections_read': sum(e['selected_reading'] is not None for e in entries.values()),
        'remaining_abstract_orders': [n for n, e in entries.items() if not e['abstract_read']],
        'additional_full_primary_abstracts': 43, 'errors': [],
    }
    summary['remaining_abstracts'] = len(summary['remaining_abstract_orders'])
    assert (summary['primary_abstracts_screened'], summary['public_pdfs'], summary['pdf_pages'], summary['selected_sections_read']) == (84, 72, 1106, 3)
    (D / 'reading-coverage.json').write_text(json.dumps({'summary': summary, 'records': list(entries.values())}, ensure_ascii=False, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
