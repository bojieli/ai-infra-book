"""Validate Virgo's selected reading and reuse its existing PDF/abstract identity.

The reading agent declares pp.2–14 main text and pp.15–16 artifact appendix.
Root accepted the notes/verifier and visually checked p10 Table 2 only; that review
is not another claim to have read all 15 selected pages. No sealed file is written.
"""
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
RELATIVE_BASE = Path('references/proceedings/ASPLOS/2025/virgo-body-reading')
BASE = ROOT / RELATIVE_BASE
DOI = '10.1145/3676641.3716281'


def _proof(path):
    raw = path.read_bytes()
    return {'file': str(path.relative_to(ROOT)), 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def verify():
    proof_path = BASE / 'reading-proof.json'
    proof_bytes = proof_path.read_bytes()
    proof = json.loads(proof_bytes)
    before = _proof(BASE / 'FOLDER-MANIFEST.json')
    completed = subprocess.run(
        [sys.executable, '-B', str(BASE / 'verify.py')], cwd=ROOT,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True, text=True, check=True, timeout=60,
    )
    report = json.loads(completed.stdout)
    assert report['status'] == 'passed_with_explicit_scope_limits'
    assert report['failures'] == [] and report['check_count'] == 232
    assert len(report['checks']) == 232 and all(c['ok'] for c in report['checks'])
    assert report['checked_manifest_files'] == 103
    assert _proof(BASE / 'FOLDER-MANIFEST.json') == before
    assert proof_path.read_bytes() == proof_bytes

    manifest = json.loads((BASE.parent / 'manifest.json').read_text())
    formal = next(p for p in manifest['papers'] if p['program_order'] == 173)
    assert formal['doi'] == DOI == proof['doi']
    packet = json.loads((BASE.parent / 'parallel-gpu-storage/reading-records.json').read_text())
    existing = next(r for r in packet['records'] if r['program_order'] == 173)
    assert existing['doi'] == DOI and existing['title'] == formal['title']
    assert existing['authors'] == [a.get('given', '') + ' ' + a['family'] for a in formal['author_metadata']]
    assert existing['reading_status'] == 'full_abstract_read'
    assert existing['selected_reading']['physical_pdf_pages'] == []
    old_pdf = existing['representative_pdf']
    body_pdf = BASE / proof['pdf_file']
    old_bytes = (ROOT / old_pdf['file']).read_bytes()
    body_bytes = body_pdf.read_bytes()
    assert old_bytes == body_bytes
    assert len(body_bytes) == old_pdf['bytes']
    assert sha256(body_bytes).hexdigest() == old_pdf['sha256'] == proof['pdf_sha256']
    assert old_pdf['pages'] == proof['pdf_pages'] == 18
    assert proof['paper_version'] == 'arXiv:2408.12073v2'
    source = json.loads((BASE / 'source-provenance.json').read_text())
    assert source['source'] == old_pdf['file'] and source['source_sha256'] == old_pdf['sha256']
    assert source['url'] == 'https://arxiv.org/pdf/2408.12073v2'
    assert source['paper_doi'] == DOI and source['version'] == proof['paper_version']

    main = list(range(2, 15))
    appendix = [15, 16]
    selected = main + appendix
    assert proof['main_body_physical_pages'] == main
    assert proof['appendix_physical_pages'] == appendix
    assert proof['body_and_appendix_unique_pages'] == len(set(selected)) == 15
    assert [p['physical_pdf_page'] for p in proof['page_reading']] == selected
    assert all(p['content_type'] == ('main_body' if p['physical_pdf_page'] in main else 'artifact_appendix')
               for p in proof['page_reading'])
    assert proof['full_pdf_read'] is False and proof['full_pdf_extracted'] is True
    assert proof['new_unique_paper_identity'] is False and proof['new_body_reading_record'] is True
    assert set(proof['unread_physical_pages']) == {'1', '17-18'}
    visual = [p['physical_page'] for p in proof['actually_viewed_full_page_images']]
    assert visual == [2, 4, 5, 8, 10, 11, 12, 13, 14]
    for key in ('source_code_read', 'artifact_downloaded', 'third_party_code_executed', 'gpu_or_simulation_executed'):
        assert proof[key] is False

    selected_reading = {
        'proof_file': str(proof_path.relative_to(ROOT)),
        'proof_sha256': sha256(proof_bytes).hexdigest(),
        'pdf_sha256': proof['pdf_sha256'],
        'paper_version': proof['paper_version'],
        'physical_pdf_pages': selected,
        'main_body_physical_pages': main,
        'appendix_physical_pages': appendix,
        'scope': 'Reading agent: full extracted text of physical pp.2–14 main body and pp.15–16 artifact appendix (15 pages); p1 remaining introduction and pp.17–18 references not read. Not a full-paper reading.',
        'full_paper_read': False,
        'reading_attribution': {
            'agent_text_reading_physical_pages': selected,
            'agent_actually_viewed_full_page_images': visual,
            'root_acceptance_review': {
                'basis': 'Root agent acceptance handoff on 2026-09-09: NOTES.md and verifier reviewed; p10 Table 2 visually checked.',
                'physical_pdf_pages_visually_spot_checked': [10],
                'focus': 'Table 2',
                'page_image': _proof(BASE / 'page-10.png'),
                'all_selected_body_pages_read_by_root': False,
            },
        },
        'execution_scope': {key: proof[key] for key in (
            'source_code_read', 'artifact_downloaded', 'third_party_code_executed', 'gpu_or_simulation_executed')},
    }
    return {
        'status': 'pass', 'program_order': 173, 'doi': DOI,
        'new_abstracts': 0, 'new_pdfs': 0, 'new_pdf_pages': 0,
        'new_body_reading_records': 1,
        'selected_main_body_pages': 13, 'selected_artifact_appendix_pages': 2,
        'selected_body_physical_pages': 15,
        'full_pdf_pages_mechanically_reextracted': 18,
        'existing_pdf': old_pdf,
        'same_pdf_bytes_as_prior_abstract_packet': True,
        'selected_reading': selected_reading,
        'notes': _proof(BASE / 'NOTES.md'),
        'own_budget_result': _proof(BASE / 'budget-results.json'),
        'independent_verifier': {
            'file': str((BASE / 'verify.py').relative_to(ROOT)),
            'status': report['status'], 'check_count': report['check_count'],
            'checked_manifest_files': report['checked_manifest_files'],
            'warnings': report['warnings'], 'limits': report['limits'],
        },
    }


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
