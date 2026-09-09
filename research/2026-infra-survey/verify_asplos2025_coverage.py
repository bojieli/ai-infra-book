"""Reconcile canonical and subsequent reviewed batches by program DOI.

This is a derived coverage index, not a replacement for original batch records.
Verification establishes provenance and declared scopes, not human reading itself.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025'


def verify(base=None, serving=None, testing=None):
    if base is None:
        from verify_asplos2025_public import verify as check
        base = check()
    if serving is None:
        from verify_serving_batch import verify as check
        serving = check()
    if testing is None:
        from verify_asplos_testing_batch import verify as check
        testing = check()
    assert all(x['status'] == 'passed' for x in (base, serving, testing))
    from verify_asplos_security_quantum import verify as check_security_quantum
    assert check_security_quantum()['status'] == 'passed'
    from verify_asplos_graph_quantum import verify as check_graph_quantum
    assert check_graph_quantum()['status'] == 'passed'
    from verify_frugal_discovery import verify as check_frugal_discovery
    assert check_frugal_discovery()['status'] == 'passed'
    manifest = json.loads((D / 'manifest.json').read_text())
    papers = {p['program_order']: p for p in manifest['papers']}
    assert len(papers) == len({p['doi'] for p in papers.values()}) == 184
    canonical = json.loads((D / 'public-abstracts.json').read_text())['records']
    entries = {
        n: {'program_order': n, 'doi': p['doi'], 'title': p['title'],
            'abstract_read': False, 'representative_pdf': None,
            'selected_reading': None, 'provenance': []}
        for n, p in papers.items()
    }
    for record in canonical:
        n = record['program_order']
        p, entry = papers[n], entries[n]
        entry['abstract_read'] = True
        entry['provenance'].append(str((D / 'public-abstracts.json').relative_to(ROOT)))
        if 'pdf' in p:
            entry['representative_pdf'] = {**p['pdf'], 'pages': p['pages']}
        if p['reading_status'] == 'selected_sections_read':
            entry['selected_reading'] = p['selected_reading']
    assert sum(e['abstract_read'] for e in entries.values()) == base['primary_abstracts_screened']
    proof_names = {114: 'comet', 116: 'pod', 117: 'tapas', 120: 'ratte', 133: 'graphpipe'}
    additional = []
    for folder in ('serving-113-117', 'screening-111-123', 'screening-111-128', 'screening-129-135', 'frugal-discovery'):
        path = D / folder / 'screening.json'
        for record in json.loads(path.read_text())['records']:
            n = record['program_order']
            entry = entries[n]
            assert record.get('formal_doi', record.get('doi')) == entry['doi']
            # Prevent silent double counting or replacement of a later canonical scope.
            assert not entry['abstract_read'], f'Already canonical: {n}; reconcile this adapter'
            entry['abstract_read'] = True
            entry['representative_pdf'] = record.get('pdf')
            entry['provenance'].append(str(path.relative_to(ROOT)))
            entry['version_notes'] = record['version_notes']
            entry['adoption'] = {'decision': record['decision'], 'reason': record['reason']}
            if n in proof_names:
                proof_path = path.parent / (proof_names[n] + '-reading.json')
                proof = json.loads(proof_path.read_text())
                assert proof['pdf']['sha256'] == record['pdf']['sha256']
                entry['selected_reading'] = {
                    'proof_file': str(proof_path.relative_to(ROOT)),
                    'scope': proof['scope'],
                    'physical_pdf_pages': [p['physical_page'] for p in proof['pages']],
                }
                assert record['body_reading_status'] == ('selected_sections_read' if n == 116 else 'selected_pages_read')
            else:
                assert record['body_reading_status'] == 'not_read'
            additional.append(n)
    assert sorted(additional) == [112, 114, 116, 117, 118, 120, 121, 122, 123, 128, 129, 130, 132, 133, 134]
    summary = {
        'status': 'passed', 'scope': 'Unique ASPLOS 2025 presentation-program DOIs, including 2024-volume papers; selected scopes only, not full-paper reading.',
        'program_entries': len(entries),
        'primary_abstracts_screened': sum(e['abstract_read'] for e in entries.values()),
        'public_pdfs': sum(e['representative_pdf'] is not None for e in entries.values()),
        'public_pdf_pages': sum(e['representative_pdf']['pages'] for e in entries.values() if e['representative_pdf']),
        'selected_sections_read': sum(e['selected_reading'] is not None for e in entries.values()),
        'additional_abstracts_over_canonical': len(additional),
        'additional_selected_scopes_over_canonical': len(proof_names),
        'remaining_abstract_orders': [n for n, e in entries.items() if not e['abstract_read']],
        'canonical_records_preserved': True,
    }
    assert (summary['primary_abstracts_screened'], summary['public_pdfs'], summary['public_pdf_pages'], summary['selected_sections_read']) == (113, 104, 1765, 22)
    summary['remaining_abstracts'] = len(summary['remaining_abstract_orders'])
    summary['additional_selected_body_pages'] = sum(len(entries[n]['selected_reading']['physical_pdf_pages']) for n in proof_names)
    assert summary['additional_selected_body_pages'] == 37
    output = {'summary': summary, 'records': [entries[n] for n in sorted(entries)]}
    (D / 'reading-coverage.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
