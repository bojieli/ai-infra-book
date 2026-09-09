"""Verify three sealed ASPLOS packets and return a DOI-deduplicated coverage delta.

Only this adapter is new. Packet verifiers run in temporary mirrors because two
write validation.json; the sealed packets, shared coverage, and archive verifier
are never modified. Returned selected_reading is None: p1 abstract/identity review
is preserved separately and must not become a selected-body-reading count.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata


ROOT = Path(__file__).resolve().parents[2]
RELATIVE_BASE = Path('references/proceedings/ASPLOS/2025')
BASE = ROOT / RELATIVE_BASE
PACKAGES = {
    'parallel-gpu-storage': {
        'orders': {173, 174, 176, 177, 178, 179},
        'gap_orders': set(), 'abstracts': 6, 'pdfs': 5, 'pdf_pages': 76,
    },
    'parallel-reliability': {
        'orders': {157, 159, 160, 161, 162},
        'gap_orders': {163}, 'abstracts': 5, 'pdfs': 5, 'pdf_pages': 78,
    },
    'parallel-zk-memory': {
        'orders': {165, 167, 168, 183, 184},
        'gap_orders': {166}, 'abstracts': 5, 'pdfs': 5, 'pdf_pages': 89,
    },
}
ANONYMOUS_ARTIFACT_COMMIT = '30b997ad3b42fb8c02f344b08ae716d119f87042'


def _require(condition, message):
    if not condition:
        raise AssertionError(message)


def _doi(value):
    result = value.strip().lower()
    _require(result.startswith('10.') and '/' in result, f'Not a formal DOI: {value}')
    return result


def _norm(value):
    value = unicodedata.normalize('NFKD', value).lower()
    return ''.join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def _tree_proof(directory):
    """Detect changes to any sealed file, including existing validation reports."""
    return {
        str(path.relative_to(directory)): (path.stat().st_size, sha256(path.read_bytes()).hexdigest())
        for path in sorted(directory.rglob('*'))
        if path.is_file() and '__pycache__' not in path.parts
    }


def _run_packet_verifier(mirror_root, package):
    path = mirror_root / RELATIVE_BASE / package / 'verify.py'
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    # These are locally authored packet verifiers, never downloaded artifact code.
    completed = subprocess.run(
        [sys.executable, '-B', str(path)], cwd=mirror_root, env=env,
        capture_output=True, text=True, timeout=60,
    )
    _require(completed.returncode == 0,
             f'{package} verifier failed:\n{completed.stdout}\n{completed.stderr}')
    report = json.loads(completed.stdout)
    allowed = {'pass', 'passed_with_explicit_version_limits'}
    _require(report.get('status') in allowed, f'{package}: {report.get("status")}')
    return package, report


def _manifest_identity(record, official_by_doi):
    doi = _doi(record['doi'])
    _require(doi in official_by_doi, f'DOI absent from current manifest: {doi}')
    official = official_by_doi[doi]
    _require(record['program_order'] == official['program_order'], f'Program mismatch: {doi}')
    _require(_norm(record['title']) == _norm(official['title']), f'Title mismatch: {doi}')
    authors = [a.get('given', '') + ' ' + a['family'] for a in official['author_metadata']]
    aliases = record.get('identity', {}).get('author_aliases', {})
    # This explicit source discrepancy is already documented and checked by its packet.
    allowed_aliases = {'Lana Josipovi?': 'Lana Josipović'} if record['program_order'] == 160 else {}
    _require(aliases == allowed_aliases, f'Unexpected author alias mapping: {doi}')
    mapped = [aliases.get(name, name) for name in authors]
    _require(mapped == record['authors'], f'Ordered author mismatch: {doi}')
    return doi, official


def _pdf_pages(record):
    pdf = record.get('representative_pdf')
    if pdf is None:
        return 0
    path = (ROOT / pdf['file']).resolve()
    _require(path.is_relative_to(BASE), f'PDF outside ASPLOS source tree: {path}')
    raw = path.read_bytes()
    _require(len(raw) == pdf['bytes'] and sha256(raw).hexdigest() == pdf['sha256'],
             f'PDF source proof mismatch: {path}')
    info = subprocess.check_output(['pdfinfo', str(path)], text=True)
    match = re.search(r'^Pages:\s+(\d+)', info, re.M)
    _require(match is not None, f'No physical page count: {path}')
    pages = int(match.group(1))
    _require(pages == pdf['pages'], f'PDF page-count mismatch: {path}')
    return pages


def _record_for_coverage(record, package, official):
    result = deepcopy(record)
    result['doi'] = _doi(record['doi'])
    result['formal_doi'] = result['doi']
    result['abstract_read'] = True
    result['provenance'] = [str(RELATIVE_BASE / package / 'reading-records.json')]
    result['abstract_identity_reading'] = result.pop('selected_reading')
    result['selected_reading'] = None
    result['adoption'] = {
        'decision': 'abstract_screening_only',
        'reason': record['editorial_decision'],
    }
    result['formal_page_range'] = official['page']
    # Formal year/container and public-manuscript version remain distinct.
    result['formal_container_metadata'] = {
        key: official.get(key)
        for key in ('volume_doi', 'volume_title', 'volume_publication_date')
    }
    if record['program_order'] == 179:
        identity = record['identity']
        _require(record['representative_pdf']['pages'] == 14, '179 public manuscript must remain 14 pages')
        first, last = map(int, official['page'].split('-'))
        _require(last - first + 1 == 15, '179 formal page range must remain 15 pages')
        _require(identity['pdf_title_authors'] is False and identity['pdf_official_doi'] is False,
                 '179 must not claim authors or DOI on anonymous PDF')
        _require(identity['publisher_abstract_equivalence_verified'] is False,
                 '179 must not claim publisher-abstract equivalence')
        _require(ANONYMOUS_ARTIFACT_COMMIT in record['version'], '179 fixed artifact commit lost')
        result['pdf_relationship'] = identity['version_caveat']
        result['identity_conditions'] = {
            'anonymous_author_artifact_manuscript': True,
            'fixed_official_lab_artifact_commit': ANONYMOUS_ARTIFACT_COMMIT,
            'fixed_readme_file': str(RELATIVE_BASE / package / '179-artifact-fixed-README.md'),
            'fixed_tree_file': str(RELATIVE_BASE / package / '179-artifact-tree.json'),
            'pdf_title_verified': True,
            'pdf_authors_present': False,
            'pdf_official_doi_present': False,
            'public_manuscript_pages': 14,
            'formal_publication_pages': 15,
            'publisher_abstract_equivalence_verified': False,
            'association': 'Same title and PDF linked by fixed official lab README; formal authors/DOI come from registry identity, not anonymous PDF.',
        }
    return result


def _insert_unique(target, record, duplicates):
    doi = record['doi']
    if doi not in target:
        target[doi] = record
        return
    previous = target[doi]
    # Never silently choose between distinct versions under one formal identity.
    comparable = {k: v for k, v in record.items() if k != 'provenance'}
    old_comparable = {k: v for k, v in previous.items() if k != 'provenance'}
    _require(comparable == old_comparable, f'Conflicting records for {doi}; reconcile versions explicitly')
    previous['provenance'] = sorted(set(previous['provenance'] + record['provenance']))
    duplicates.append(doi)


def verify():
    """Return records/gaps/counts for these packets, not totals from live coverage.

    Counts deduplicate the three packets by formal DOI. The caller reconciles this
    delta with its existing coverage; this function neither reads nor writes that
    shared index. Full abstracts, original identity caveats and version notes stay
    in returned records; their empty body scopes never become selected readings.
    """
    manifest_bytes = (BASE / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    official_by_doi = {_doi(p['doi']): p for p in manifest['papers']}
    _require(len(official_by_doi) == len(manifest['papers']) == 184, 'Current manifest DOI uniqueness mismatch')
    originals = {name: _tree_proof(BASE / name) for name in PACKAGES}
    bundles = {name: json.loads((BASE / name / 'reading-records.json').read_text()) for name in PACKAGES}

    # The mirror preserves repository-relative paths expected by each independent
    # verifier. All source bytes are copied; no symlink can redirect a report write
    # to the sealed packet. Temporary validation writes disappear with the mirror.
    with tempfile.TemporaryDirectory(prefix='asplos-late-verify-') as temp:
        mirror_root = Path(temp)
        mirror_base = mirror_root / RELATIVE_BASE
        mirror_base.mkdir(parents=True)
        (mirror_base / 'manifest.json').write_bytes(manifest_bytes)
        for name in PACKAGES:
            shutil.copytree(BASE / name, mirror_base / name, ignore=shutil.ignore_patterns('__pycache__'))
        with ThreadPoolExecutor(max_workers=3) as pool:
            reports = dict(pool.map(lambda name: _run_packet_verifier(mirror_root, name), PACKAGES))

    records_by_doi = {}
    gaps_by_doi = {}
    duplicates = []
    per_package = {}
    for name, expected in PACKAGES.items():
        packet = bundles[name]
        records, gaps = packet['records'], packet['gaps']
        _require({r['program_order'] for r in records} == expected['orders'], f'{name}: abstract selection mismatch')
        _require({r['program_order'] for r in gaps} == expected['gap_orders'], f'{name}: gap selection mismatch')
        _require(packet['selected_body_physical_pages'] == packet['selected_body_reading_records'] == 0,
                 f'{name}: unexpected body reading')
        _require(packet['body_reading_is_full_paper'] is False, f'{name}: full-paper claim')
        pages = 0
        pdf_count = 0
        image_count = 0
        for record in records:
            doi, official = _manifest_identity(record, official_by_doi)
            _require(record['reading_status'] == 'full_abstract_read', f'{doi}: abstract not read')
            _require(bool(record['abstract'].strip()), f'{doi}: empty abstract')
            _require(sha256(record['abstract'].encode()).hexdigest() == record['abstract_sha256'],
                     f'{doi}: abstract digest mismatch')
            scope = record['selected_reading']
            _require(scope['physical_pdf_pages'] == [], f'{doi}: unexpected selected body pages')
            images = scope.get('viewed_page_images', {})
            _require(all(k == '1' and v['actually_viewed'] for k, v in images.items()),
                     f'{doi}: unexpected abstract/identity image scope')
            image_count += len(images)
            pages += _pdf_pages(record)
            pdf_count += record.get('representative_pdf') is not None
            _insert_unique(records_by_doi, _record_for_coverage(record, name, official), duplicates)
        for gap in gaps:
            doi, _ = _manifest_identity(gap, official_by_doi)
            _require(gap['full_abstract_read'] is False and gap['representative_pdf'] is None,
                     f'{doi}: gap incorrectly counted as read')
            _require(gap['body_pages_read'] == [], f'{doi}: gap has body scope')
            item = deepcopy(gap)
            item.update(doi=doi, formal_doi=doi, abstract_read=False, selected_reading=None,
                        gap_reason=gap['reason'],
                        provenance=[str(RELATIVE_BASE / name / 'reading-records.json')])
            _insert_unique(gaps_by_doi, item, duplicates)
        actual = (len(records), pdf_count, pages, image_count)
        wanted = (expected['abstracts'], expected['pdfs'], expected['pdf_pages'], 5)
        _require(actual == wanted, f'{name}: independently counted {actual}, expected {wanted}')
        _require((packet['new_full_abstracts'], packet['representative_pdfs'], packet['representative_pdf_pages']) == actual[:3],
                 f'{name}: packet aggregate mismatch')
        _require(packet['actual_rendered_pages_viewed'] == packet['abstract_identity_pages_read_separately'] == image_count,
                 f'{name}: image count mismatch')
        report = reports[name]
        reported_abstracts = report.get('full_abstracts', report.get('full_primary_abstracts_reextracted'))
        reported_body = report.get('body_pages_read', report.get('selected_body_pages'))
        _require((reported_abstracts, report['representative_pdfs'], report['representative_pdf_pages'], reported_body)
                 == (expected['abstracts'], expected['pdfs'], expected['pdf_pages'], 0), f'{name}: child verifier count mismatch')
        per_package[name] = {
            'full_primary_abstracts': len(records), 'representative_pdfs': pdf_count,
            'representative_pdf_pages': pages, 'abstract_identity_pages': image_count,
            'selected_body_pages': 0, 'unresolved_primary_abstracts': len(gaps),
        }

    _require(not (records_by_doi.keys() & gaps_by_doi.keys()), 'A DOI is both read and an unresolved gap')
    records = sorted(records_by_doi.values(), key=lambda r: r['program_order'])
    gaps = sorted(gaps_by_doi.values(), key=lambda r: r['program_order'])
    counts = {
        'unique_formal_dois': len(records) + len(gaps),
        'new_full_abstracts': len(records),
        'representative_pdfs': sum(r['representative_pdf'] is not None for r in records),
        'representative_pdf_pages': sum(r['representative_pdf']['pages'] for r in records if r['representative_pdf']),
        'selected_body_reading_records': sum(r['selected_reading'] is not None for r in records),
        'selected_body_physical_pages': 0,
        'abstract_identity_pages_read_separately': sum(len(r['abstract_identity_reading']['viewed_page_images']) for r in records),
        'unresolved_primary_abstracts': len(gaps),
    }
    _require(counts == {
        'unique_formal_dois': 18, 'new_full_abstracts': 16, 'representative_pdfs': 15,
        'representative_pdf_pages': 243, 'selected_body_reading_records': 0,
        'selected_body_physical_pages': 0, 'abstract_identity_pages_read_separately': 15,
        'unresolved_primary_abstracts': 2,
    }, f'DOI-deduplicated aggregate mismatch: {counts}')
    _require([r['program_order'] for r in gaps] == [163, 166], 'Expected gaps lost')
    _require((BASE / 'manifest.json').read_bytes() == manifest_bytes, 'Manifest changed during verification; retry')
    _require(all(_tree_proof(BASE / name) == originals[name] for name in PACKAGES),
             'Sealed packet bytes changed during verification; retry/reconcile')
    return {
        'status': 'passed_with_explicit_version_limits',
        'scope': 'Three-packet incremental coverage, deduplicated by formal DOI; not live coverage totals or full-paper reading.',
        'manifest_sha256': sha256(manifest_bytes).hexdigest(),
        'records': records, 'gaps': gaps, 'counts': counts,
        'per_package_counts': per_package, 'duplicate_dois_suppressed': sorted(set(duplicates)),
        'independent_packet_verifications': reports,
        'unresolved_primary_abstract_dois': [r['doi'] for r in gaps],
        'sealed_packets_unchanged': True,
        'validation_execution': 'Three locally authored verifiers executed in parallel temporary byte-copy mirrors; stdout parsed; original packets/shared coverage untouched.',
        'limitations': [
            '179 is a fixed official-artifact-linked anonymous14-page manuscript; formal publication has15 pages; no PDF authors/DOI or publisher equivalence claimed.',
            '176/159/167 public preprints differ in length from formal publications; all original version notes and identity caveats retained.',
            '183 complete arXiv v2 PDF abstract is used; different/malformed HTML abstract remains a separate source condition.',
            'An abstract screen and p1 identity image are never counted as selected body reading; child verifiers validate evidence, not the act of reading.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
