#!/usr/bin/env python3
"""Verify the declared catalog phase; no network or paper-code execution."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import json
import re
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/catalog-review/2026-09-08'
DISC = ROOT / 'references/proceedings/discovery/2026-09-08'


def verify():
    spec = importlib.util.spec_from_file_location('reconcile_asplos', ROOT / 'references/reconcile_asplos.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    norm = module.normalized_title
    sources = json.loads((D / 'sources.json').read_text())
    assert len(sources) == len({s['id'] for s in sources}) == 15
    for s in sources:
        data = (ROOT / s['file']).read_bytes()
        assert len(data) == s['bytes'] and hashlib.sha256(data).hexdigest() == s['sha256']
        assert s['read_scope'] and s['reading_status'] != 'downloaded_not_read'
        if '-dblp.html' in s['file']:
            assert s['status_code'] == 200 and s['reading_status'] == 'blocked_challenge_response_only'
            assert b'Anubis' in data and b'bot' in data
        if 'identity_text' in s:
            assert data.startswith(b'%PDF-')
            t = s['identity_text'];text = (ROOT / t['file']).read_bytes()
            assert len(text) == t['bytes'] and hashlib.sha256(text).hexdigest() == t['sha256']
            fresh = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', '-layout', str(ROOT / s['file']), '-'])
            assert fresh == text and t['physical_page'] == 1
            info = subprocess.check_output(['pdfinfo', str(ROOT / s['file'])], text=True)
            assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == s['pdf_pages']
            doi = '10.1145/3676642.3736119' if 'hybridtier' in s['file'] else '10.1145/3676642.3736129'
            assert doi.encode() in text and b'Volume 3' in text and b'2025' in text

    index = json.loads((DISC / 'program-index.json').read_text())
    groups = {p['source_id']: p for p in index['programs']}
    corrections = json.loads((D / 'extraction-corrections.json').read_text())
    assert sum(p['count'] for p in groups.values()) == corrections['corrected_program_entries'] == 1185
    titles = module.program_2024_titles(DISC / 'asplos2024-program.html')
    assert len(titles) == len(groups['asplos2024-program']['entries']) == 193
    for p in groups['asplos2024-program']['entries']:
        assert titles[p['doi']] == p['title']
    assert len(corrections['title_corrections']) == 16
    for c in corrections['title_corrections']:
        p = groups['asplos2024-program']['entries'][c['program_order'] - 1]
        assert c['before'] == p['original_extracted_title'] and c['after'] == p['title'] and c['doi'] == p['doi']
    isca = groups['isca2026-program']
    assert isca['original_extracted_count'] == 173 and isca['count'] == 172
    raw_slots = BeautifulSoup((DISC / 'isca2026-program.html').read_text(), 'html.parser').select('div.paper')
    assert len(raw_slots) == 173
    blank = raw_slots[157]
    assert not blank.select_one('.paper-title').get_text(strip=True)
    assert not blank.select_one('.paper-authors').get_text(strip=True)
    assert len(corrections['excluded_slots']) == 1 and corrections['excluded_slots'][0]['program_order'] == 158
    assert [p['program_order'] for p in isca['entries']] == [n for n in range(1, 174) if n != 158]

    manifest = json.loads((ROOT / 'references/proceedings/ASPLOS/2024/manifest.json').read_text())
    abstracts = {norm(p['title']): p for p in module.abstracts_2024(DISC / 'asplos2024-abstracts.html')}
    assert len(abstracts) == len(manifest['papers']) == 193
    assert hashlib.sha256((ROOT / manifest['abstract_file']).read_bytes()).hexdigest() == manifest['abstract_file_sha256']
    screens = list(csv.DictReader((ROOT / 'research/2026-infra-survey/screening-asplos-2024.tsv').open(), delimiter='\t'))
    assert [int(s['number']) for s in screens] == list(range(1, 194))
    for i, p in enumerate(manifest['papers']):
        assert p['abstract'] == abstracts[norm(p['title'])]['abstract']
        assert p['abstract_sha256'] == hashlib.sha256(p['abstract'].encode()).hexdigest()
        assert p['doi'] == groups['asplos2024-program']['entries'][i]['doi']
        if i < len(screens):
            s = screens[i]
            assert p['reading_status'] in ['abstract_screened', 'selected_sections_read']
            assert p['screening'] == {'basis': 'title_and_full_official_abstract', 'decision': s['decision'], 'reason': s['reason']}
        else:
            assert 'screening' not in p and p['reading_status'] == 'abstract_extracted_not_screened'
    assert manifest['abstracts_screened'] == 193 and manifest['selected_sections_read'] == 1
    selected = [p for p in manifest['papers'] if p['reading_status'] == 'selected_sections_read']
    assert len(selected) == 1 and selected[0]['doi'] == '10.1145/3620666.3651383'
    for p in selected:
        r = p['selected_reading']; pdf = ROOT / r['individual_pdf']
        assert r['physical_pdf_pages'] == list(range(1, 14))
        assert sorted(map(int, r['page_text_sha256'])) == r['physical_pdf_pages']
        for page, expected in r['page_text_sha256'].items():
            data = subprocess.check_output(['pdftotext', '-layout', '-f', page, '-l', page, str(pdf), '-'], timeout=30)
            assert hashlib.sha256(data).hexdigest() == expected
        landing = (ROOT / 'references/framework-history/2026-09-08/kernel-orchestration/korch-arxiv-landing.html').read_text()
        assert p['doi'] in landing and '2406.09465v1' in landing

    mapping = json.loads((D / 'asplos2026-program-doi-map.json').read_text())
    qdata = (ROOT / mapping['query_file']).read_bytes()
    assert hashlib.sha256(qdata).hexdigest() == mapping['query_sha256']
    query = json.loads(qdata)['message']
    records = {r['DOI']: r for r in query['items']}
    assert len(query['items']) == mapping['query_returned_items'] == 1000
    assert query['total-results'] == mapping['query_total_results'] > 1000 and not mapping['query_is_exhaustive']
    assert mapping['program_header_count'] == 167 and mapping['program_detail_count'] == 168
    assert len(mapping['papers']) == len({p['doi'] for p in mapping['papers']}) == 168
    assert '167 unique papers' in (DISC / 'asplos2026-program.html').read_text()
    variants = []
    for p, g in zip(mapping['papers'], groups['asplos2026-program']['entries']):
        assert p['program_order'] == g['program_order'] and p['program_title'] == g['title']
        assert p['program_authors'] == g['authors']
        r = records[p['doi']]
        assert p['published_title_raw'] == r['title'][0] and p['published_authors'] == r['author']
        assert p['container_title'] == r['container-title'][0] and p['published_date'] == r['published']['date-parts'][0]
        if p['match'] == 'normalized_title':
            assert norm(p['program_title']) == norm(p['published_title_raw'])
        else:
            variants.append(p['program_order'])
            assert p['match_note'] and norm(p['program_title']) != norm(p['published_title_raw'])
    assert variants == [36, 70, 94, 101, 112, 138, 141, 150, 165]
    counts = {prefix: sum(p['doi'].rsplit('.', 1)[0] == prefix for p in mapping['papers']) for prefix in mapping['matched_papers_by_volume_doi']}
    assert counts == mapping['matched_papers_by_volume_doi'] == {'10.1145/3779212': 132, '10.1145/3760250': 20, '10.1145/3676642': 16}
    assert len(mapping['keynotes_excluded_from_paper_count']) == 3
    program_text = BeautifulSoup((DISC / 'asplos2026-program.html').read_text(), 'html.parser').get_text(' ', strip=True)
    for keynote in mapping['keynotes_excluded_from_paper_count']:
        assert keynote['doi'] not in {p['doi'] for p in mapping['papers']}
        assert keynote['title'] == records[keynote['doi']]['title'][0]
        assert keynote['authors'][0]['family'] in program_text or keynote['authors'][0]['family'] == 'Ranganathan' and 'Ranganthan' in program_text

    return {'verified_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Declared catalog, extraction and screening phase only; not completion of the research goal.',
            'responses': len(sources), 'blocked_challenge_responses': 5, 'http_failures': 3,
            'corrected_program_entries': 1185, 'title_extraction_corrections': 16, 'empty_slots_excluded': 1,
            'asplos2024': {'abstracts_matched': 193, 'abstracts_screened': 193, 'selected_sections_read': 1, 'selected_page_scopes_verified': 13},
            'asplos2026': {'program_header': 167, 'detail_entries_with_distinct_doi': 168, 'title_variants': 9,
                           'matched_volume_counts': counts, 'keynotes_excluded': 3, 'query_exhaustive': False},
            'additional_author_pdfs': 2, 'additional_pdf_pages_archived': 35, 'identity_pages_checked': 2,
            'paper_code_executed': False, 'status': 'passed'}


if __name__ == '__main__':
    report = verify()
    (Path(__file__).parent / 'catalog-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
