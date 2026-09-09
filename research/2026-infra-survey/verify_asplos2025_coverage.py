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
    # Preserve the original canonical page scope and attach later reading once.
    from verify_partir_expanded import verify as check_partir_expanded
    expanded = check_partir_expanded()
    entries[80]['supplemental_reading'] = {
        'proof_file': 'references/framework-history/2026-09-09/partir-shardy/expanded-reading/reading-proof.json',
        'full_physical_pdf_pages': expanded['full_pages'],
        'partial_page': expanded['partial_page'],
        'additional_full_pages_over_original': expanded['additional_full_pages'],
        'new_papers_with_selected_reading': 0,
    }
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
    from verify_asplos_compiler_memory import verify as check_compiler_memory
    assert check_compiler_memory()['passed']
    followup_path = D / 'parallel-followup/reading-records.json'
    followups = json.loads(followup_path.read_text())['records']
    assert {r['program_order'] for r in followups} == {151, 152, 182}
    followup_pages = 0
    for record in followups:
        n = record['program_order']
        entry = entries[n]
        assert record['doi'] == entry['doi'] and not entry['abstract_read']
        entry['abstract_read'] = True
        entry['representative_pdf'] = record['representative_pdf']
        entry['selected_reading'] = {
            **record['selected_reading'],
            'proof_file': str(followup_path.relative_to(ROOT)),
            'pdf_sha256': record['representative_pdf']['sha256'],
        }
        entry['version_notes'] = record['version_notes']
        entry['provenance'].append(str(followup_path.relative_to(ROOT)))
        entry['adoption'] = {'decision': 'existing_experiment_extension', 'reason': {151: 'Separate tuning overhead from resulting program speed; existing5.3.5.', 152: 'Include symbolic bounds and workspace in graph memory planning; existing5.4.4.', 182: 'Separate KV residency, reads and mapping work; existing8.2.1.'}[n]}
        followup_pages += len(record['selected_reading']['physical_pdf_pages'])
        additional.append(n)
    assert followup_pages == 16
    from verify_asplos_memory_pool import verify as check_memory_pool
    assert check_memory_pool()['status'] == 'pass'
    memory_path = D / 'parallel-next/reading-records.json'
    memory = json.loads(memory_path.read_text())
    assert {r['program_order'] for r in memory['records']} == {145, 175}
    memory_selected = 0
    memory_pages = 0
    for record in memory['records']:
        n = record['program_order']
        entry = entries[n]
        assert record['doi'] == entry['doi'] and not entry['abstract_read']
        entry['abstract_read'] = True
        entry['representative_pdf'] = record['representative_pdf']
        entry['version_notes'] = record['version_notes']
        entry['provenance'].append(str(memory_path.relative_to(ROOT)))
        entry['adoption'] = {'decision': 'existing_experiment_extension' if n == 175 else 'body_reading_candidate', 'reason': record['editorial_decision']}
        if record['selected_reading']['physical_pdf_pages']:
            entry['selected_reading'] = {**record['selected_reading'], 'proof_file': str(memory_path.relative_to(ROOT))}
            memory_selected += 1
            memory_pages += len(record['selected_reading']['physical_pdf_pages'])
        additional.append(n)
    for gap in memory['gaps']:
        entry = entries[gap['program_order']]
        assert gap['doi'] == entry['doi'] and not entry['abstract_read']
        entry['provenance'].append(str(memory_path.relative_to(ROOT)))
        entry['gap_reason'] = gap['gap_reason']
    assert memory_selected == 1 and memory_pages == 4
    from verify_asplos_adjacent_abstracts import verify as check_adjacent
    assert check_adjacent()['status'] == 'pass'
    adjacent_path = D / 'parallel-abstracts-next/reading-records.json'
    adjacent = json.loads(adjacent_path.read_text())
    assert {r['program_order'] for r in adjacent['records']} == {146, 147, 148, 149, 153}
    for record in adjacent['records']:
        n = record['program_order']
        entry = entries[n]
        assert record['doi'] == entry['doi'] and not entry['abstract_read']
        assert record['selected_reading']['physical_pdf_pages'] == []
        entry['abstract_read'] = True
        entry['representative_pdf'] = record['representative_pdf']
        entry['version_notes'] = record['version_notes']
        entry['provenance'].append(str(adjacent_path.relative_to(ROOT)))
        entry['adoption'] = {'decision': 'abstract_screening_only', 'reason': record['editorial_decision']}
        if n == 153:
            entry['pdf_relationship'] = 'Author-linked Teola v3 related preprint; formal Ayo abstract remains the institutional source. Not asserted identical to version of record.'
        additional.append(n)
    for gap in adjacent['gaps']:
        entry = entries[gap['program_order']]
        assert entry['doi'] == gap['doi'] and not entry['abstract_read']
        entry['provenance'].append(str(adjacent_path.relative_to(ROOT)))
        entry['gap_reason'] = gap['gap_reason']
    from verify_asplos_pim_serverless import verify as check_pim_serverless
    assert check_pim_serverless()['status'] == 'pass'
    pim_path = D / 'parallel-pim-serverless/reading-records.json'
    pim = json.loads(pim_path.read_text())
    assert {r['program_order'] for r in pim['records']} == {154, 156, 158, 170, 171, 172}
    for record in pim['records']:
        n = record['program_order']
        entry = entries[n]
        assert record['doi'] == entry['doi'] and not entry['abstract_read']
        assert record['selected_reading']['physical_pdf_pages'] == []
        entry['abstract_read'] = True
        entry['representative_pdf'] = record['representative_pdf']
        entry['version_notes'] = record['version_notes']
        entry['provenance'].append(str(pim_path.relative_to(ROOT)))
        entry['adoption'] = {'decision': 'abstract_screening_only', 'reason': record['editorial_decision']}
        additional.append(n)
    from verify_serverless_body import verify as check_serverless_body
    assert check_serverless_body()['status'] == 'pass'
    serverless_path = D / 'serverless-body-reading/reading-records.json'
    serverless = json.loads(serverless_path.read_text())
    for record in serverless['records']:
        entry = entries[record['program_order']]
        assert entry['doi'] == record['doi'] and entry['abstract_read'] and entry['selected_reading'] is None
        assert entry['representative_pdf']['sha256'] == record['existing_source_pdf']['sha256']
        entry['selected_reading'] = {'proof_file': str(serverless_path.relative_to(ROOT)), 'physical_pdf_pages': record['physical_pdf_pages'], 'scope': 'Selected full physical pages; Medusa p13 artifact appendix; not full paper.'}
        entry['provenance'].append(str(serverless_path.relative_to(ROOT)))
        entry['adoption'] = {'decision': 'existing_experiment_extension', 'reason': 'Existing11.3.1/11-3 compares resource-share adjustment with loading critical path and capacity invalidation.'}
    assert len(serverless['records']) == 2 and sum(len(r['physical_pdf_pages']) for r in serverless['records']) == 17
    assert sorted(additional) == [112, 114, 116, 117, 118, 120, 121, 122, 123, 128, 129, 130, 132, 133, 134, 145, 146, 147, 148, 149, 151, 152, 153, 154, 156, 158, 170, 171, 172, 175, 182]
    from verify_asplos_late_batches import verify as check_late_batches
    late = check_late_batches()
    assert late['status'] == 'passed_with_explicit_version_limits'
    assert late['sealed_packets_unchanged']
    assert (late['counts']['new_full_abstracts'], late['counts']['representative_pdfs'],
            late['counts']['representative_pdf_pages'], late['counts']['selected_body_physical_pages']) == (16, 15, 243, 0)
    assert late['counts']['selected_body_reading_records'] == 0
    assert {r['program_order'] for r in late['records']} == {157, 159, 160, 161, 162, 165, 167, 168, 173, 174, 176, 177, 178, 179, 183, 184}
    # This adapter already deduplicates its packets by formal DOI. Still require
    # an unread entry here so a later canonical integration cannot double count.
    for record in late['records']:
        n = record['program_order']
        entry = entries[n]
        assert record['doi'] == record['formal_doi'] == entry['doi'] and not entry['abstract_read']
        assert record['abstract_read'] and record['selected_reading'] is None
        assert record['abstract_identity_reading']['physical_pdf_pages'] == []
        entry['abstract_read'] = True
        for key in ('representative_pdf', 'selected_reading', 'version', 'version_notes',
                    'identity', 'adoption', 'abstract_identity_reading',
                    'formal_container_metadata', 'formal_page_range',
                    'pdf_relationship', 'identity_conditions'):
            if key in record:
                entry[key] = record[key]
        entry['abstract_source'] = {
            'file': record['source_file'], 'sha256': record['source_sha256'],
            'url': record['source_url'], 'extraction_kind': record['extraction_kind'],
            'abstract_sha256': record['abstract_sha256'],
        }
        entry['provenance'].extend(record['provenance'])
        additional.append(n)
    assert {r['program_order'] for r in late['gaps']} == {163, 166}
    for gap in late['gaps']:
        entry = entries[gap['program_order']]
        assert gap['doi'] == entry['doi'] and not entry['abstract_read']
        assert not gap['abstract_read'] and gap['representative_pdf'] is None and gap['selected_reading'] is None
        entry['provenance'].extend(gap['provenance'])
        entry['gap_reason'] = gap['gap_reason']
        entry['gap_evidence'] = {
            key: value for key, value in gap.items()
            if key not in ('program_order', 'doi', 'formal_doi', 'title', 'authors',
                           'abstract_read', 'representative_pdf', 'selected_reading',
                           'provenance', 'gap_reason')
        }
    assert len(additional) == len(set(additional)) == 47
    # The anonymous author-artifact manuscript remains a conditional association,
    # and its first-page abstract never becomes a selected-body-reading scope.
    assert entries[179]['identity_conditions']['anonymous_author_artifact_manuscript']
    assert not entries[179]['identity_conditions']['publisher_abstract_equivalence_verified']
    assert entries[179]['identity_conditions']['public_manuscript_pages'] == 14
    assert entries[179]['identity_conditions']['formal_publication_pages'] == 15
    assert entries[179]['selected_reading'] is None
    from verify_virgo_body import verify as check_virgo_body
    virgo = check_virgo_body()
    assert virgo['status'] == 'pass' and virgo['same_pdf_bytes_as_prior_abstract_packet']
    assert virgo['new_abstracts'] == virgo['new_pdfs'] == virgo['new_pdf_pages'] == 0
    assert virgo['new_body_reading_records'] == 1 and virgo['selected_body_physical_pages'] == 15
    entry = entries[virgo['program_order']]
    assert entry['doi'] == virgo['doi'] and entry['abstract_read'] and entry['selected_reading'] is None
    assert entry['representative_pdf']['sha256'] == virgo['existing_pdf']['sha256']
    entry['selected_reading'] = virgo['selected_reading']
    entry['provenance'].append(virgo['selected_reading']['proof_file'])
    entry['adoption'] = {
        'decision': 'existing_experiment_extension',
        'reason': 'Existing 4.3.1/4.4.3 uses a conditional capacity/operand-supply budget; the reading agent’s 15-page scope and root p10 Table 2 spot check remain distinct. No product-performance or reproduced-energy claim.',
    }
    from verify_asplos_final_next import verify as check_final_next
    final_next = check_final_next()
    assert final_next['status'] == 'passed_with_explicit_version_limits'
    assert final_next['sealed_packet_unchanged']
    assert (final_next['counts']['new_full_abstracts'], final_next['counts']['representative_pdfs'],
            final_next['counts']['representative_pdf_pages'], final_next['counts']['selected_body_physical_pages']) == (3, 2, 33, 0)
    for record in final_next['records']:
        n = record['program_order']; entry = entries[n]
        assert record['doi'] == record['formal_doi'] == entry['doi'] and not entry['abstract_read']
        assert record['abstract_read'] and record['selected_reading'] is None
        entry['abstract_read'] = True
        for key in ('representative_pdf', 'selected_reading', 'version', 'version_notes',
                    'identity', 'adoption', 'abstract_identity_reading', 'formal_page_range',
                    'pdf_relationship', 'identity_conditions'):
            if key in record:
                entry[key] = record[key]
        entry['abstract_source'] = {
            'file': record['source_file'], 'sha256': record['source_sha256'],
            'url': record['source_url'], 'extraction_kind': record['extraction_kind'],
            'abstract_sha256': record['abstract_sha256'],
        }
        entry['provenance'].extend(record['provenance'])
        additional.append(n)
    assert {r['program_order'] for r in final_next['gaps']} == {1, 2, 5}
    for gap in final_next['gaps']:
        entry = entries[gap['program_order']]
        assert gap['doi'] == entry['doi'] and not entry['abstract_read']
        assert not gap['abstract_read'] and gap['representative_pdf'] is None and gap['selected_reading'] is None
        entry['provenance'].extend(gap['provenance'])
        entry['gap_reason'] = gap['gap_reason']
        entry['gap_evidence'] = {key: value for key, value in gap.items()
                                 if key not in ('program_order', 'doi', 'formal_doi', 'title', 'authors',
                                                'abstract_read', 'representative_pdf', 'selected_reading',
                                                'provenance', 'gap_reason')}
    assert len(additional) == len(set(additional)) == 50
    assert entries[14]['identity_conditions'] == {
        'public_manuscript_pages': 17, 'formal_publication_pages': 16,
        'publisher_byte_equivalence_verified': False,
    }
    assert entries[14]['selected_reading'] is None
    from verify_asplos_fpga_edge import verify as check_fpga_edge
    fpga = check_fpga_edge()
    assert fpga['status'] == 'pass' and fpga['sealed_source_files_unchanged']
    fpga_proof = str((D / 'parallel-fpga-edge/reading-records.json').relative_to(ROOT))
    for record in fpga['records']:
        entry = entries[record['program_order']]
        assert entry['doi'] == record['doi'] and not entry['abstract_read']
        assert record['selected_reading']['physical_pdf_pages'] == []
        entry['abstract_read'] = True
        for key in ('representative_pdf', 'version', 'version_notes', 'identity'):
            entry[key] = record[key]
        entry['abstract_identity_reading'] = record['selected_reading']
        entry['selected_reading'] = None
        entry['provenance'].append(fpga_proof)
        entry['adoption'] = {'decision': 'abstract_screening_only', 'reason': record['editorial_decision']}
        additional.append(record['program_order'])
    for gap in fpga['gaps']:
        entry = entries[gap['program_order']]
        assert entry['doi'] == gap['doi'] and not entry['abstract_read']
        entry['gap_reason'] = gap['reason']
        entry['gap_evidence'] = gap
        entry['provenance'].append(fpga_proof)
    assert len(additional) == len(set(additional)) == 55
    summary = {
        'status': 'passed', 'scope': 'Unique ASPLOS 2025 presentation-program DOIs, including 2024-volume papers; selected scopes only, not full-paper reading.',
        'program_entries': len(entries),
        'primary_abstracts_screened': sum(e['abstract_read'] for e in entries.values()),
        'public_pdfs': sum(e['representative_pdf'] is not None for e in entries.values()),
        'public_pdf_pages': sum(e['representative_pdf']['pages'] for e in entries.values() if e['representative_pdf']),
        'selected_sections_read': sum(e['selected_reading'] is not None for e in entries.values()),
        'additional_abstracts_over_canonical': len(additional),
        'additional_selected_scopes_over_canonical': len(proof_names) + len(followups) + memory_selected + len(serverless['records']) + virgo['new_body_reading_records'],
        'remaining_abstract_orders': [n for n, e in entries.items() if not e['abstract_read']],
        'canonical_records_preserved': True,
    }
    assert (summary['primary_abstracts_screened'], summary['public_pdfs'], summary['public_pdf_pages'], summary['selected_sections_read']) == (153, 139, 2327, 29)
    summary['remaining_abstracts'] = len(summary['remaining_abstract_orders'])
    assert summary['remaining_abstracts'] == 31
    assert {1, 2, 5, 32, 163, 166} <= set(summary['remaining_abstract_orders'])
    summary['additional_selected_body_pages'] = sum(len(entries[n]['selected_reading']['physical_pdf_pages']) for n in proof_names) + followup_pages + memory_pages + 17 + virgo['selected_body_physical_pages']
    assert summary['additional_selected_body_pages'] == 89
    output = {'summary': summary, 'records': [entries[n] for n in sorted(entries)]}
    (D / 'reading-coverage.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
