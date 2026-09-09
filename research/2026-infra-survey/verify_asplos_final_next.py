"""Verify the sealed three-abstract packet and adapt its formal DOI delta."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REL = Path('references/proceedings/ASPLOS/2025')
BASE = ROOT / REL
PACKET = 'parallel-abstracts-final-next'
P = BASE / PACKET


def _proof_tree():
    return {str(f.relative_to(P)): sha256(f.read_bytes()).hexdigest()
            for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts}


def verify():
    before = _proof_tree()
    manifest_bytes = (BASE / 'manifest.json').read_bytes()
    official = {p['doi']: p for p in json.loads(manifest_bytes)['papers']}
    packet = json.loads((P / 'reading-records.json').read_text())
    assert len(official) == 184
    # Its authored verifier writes validation.json, so run on an actual byte-copy
    # mirror. Preserve the original source-registry comparison without symlinks.
    with tempfile.TemporaryDirectory(prefix='asplos-final-next-verify-') as temp:
        root = Path(temp); base = root / REL
        base.mkdir(parents=True)
        (base / 'manifest.json').write_bytes(manifest_bytes)
        shutil.copyfile(BASE / 'asplos2024-vol4-title-query.json', base / 'asplos2024-vol4-title-query.json')
        shutil.copytree(P, base / PACKET, ignore=shutil.ignore_patterns('__pycache__'))
        run = subprocess.run([sys.executable, '-B', str(base / PACKET / 'verify.py')],
                             cwd=root, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stdout + run.stderr
        report = json.loads(run.stdout)
    assert report['status'] == 'pass'
    assert report['reextracted_orders'] == [10, 14, 16]
    assert report['full_primary_abstracts_reextracted'] == 3
    assert (report['representative_pdfs'], report['representative_pdf_pages'],
            report['selected_body_pages']) == (2, 33, 0)
    assert report['unresolved_original_abstracts'] == [1, 2, 5]
    assert report['http_responses'] == 25 and report['genuine_zero_byte_failed_responses'] == 4
    assert {r['program_order'] for r in packet['records']} == {10, 14, 16}
    assert {r['program_order'] for r in packet['gaps']} == {1, 2, 5}
    assert len({r['doi'] for r in packet['records'] + packet['gaps']}) == 6
    records = []; gaps = []
    for raw in packet['records'] + packet['gaps']:
        r = deepcopy(raw); formal = official[r['doi']]
        assert r['program_order'] == formal['program_order'] and r['title'] == formal['title']
        assert r['authors'] == [a['given'] + ' ' + a['family'] for a in formal['author_metadata']]
        r['formal_doi'] = r['doi']
        r['provenance'] = [str(REL / PACKET / 'reading-records.json')]
        r['formal_page_range'] = formal['page']
        if r['program_order'] in [10, 14, 16]:
            assert r['selected_reading']['physical_pdf_pages'] == []
            r['abstract_read'] = True
            r['abstract_identity_reading'] = r.pop('selected_reading')
            r['selected_reading'] = None
            r['adoption'] = {'decision': 'abstract_screening_only', 'reason': r['editorial_decision']}
            if r['program_order'] == 14:
                assert r['representative_pdf']['pages'] == 17 and formal['page'] == '79-94'
                r['pdf_relationship'] = 'Author publication-layout PDF has 17 pages; formal page range 79–94 has 16. Formal DOI/title/all authors verified on p1; publisher-byte equivalence not asserted.'
                r['identity_conditions'] = {'public_manuscript_pages': 17, 'formal_publication_pages': 16, 'publisher_byte_equivalence_verified': False}
            if r['program_order'] == 10:
                assert r['representative_pdf'] is None
            records.append(r)
        else:
            assert not r['full_abstract_read'] and r['representative_pdf'] is None and r['body_pages_read'] == []
            r['abstract_read'] = False
            r['selected_reading'] = None
            r['gap_reason'] = r['reason']
            gaps.append(r)
    assert before == _proof_tree(), 'Sealed packet changed during verification'
    assert manifest_bytes == (BASE / 'manifest.json').read_bytes()
    return {'status': 'passed_with_explicit_version_limits', 'sealed_packet_unchanged': True,
            'records': records, 'gaps': gaps, 'packet_verification': report,
            'counts': {'new_full_abstracts': 3, 'representative_pdfs': 2,
                       'representative_pdf_pages': 33, 'selected_body_reading_records': 0,
                       'selected_body_physical_pages': 0, 'unresolved_original_abstracts': 3}}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
