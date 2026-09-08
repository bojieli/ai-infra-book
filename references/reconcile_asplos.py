#!/usr/bin/env python3
"""Reconcile archived program HTML; never treat extraction as paper reading."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import unicodedata

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / 'references/proceedings/discovery/2026-09-08'
CATALOG = ROOT / 'references/proceedings/catalog-review/2026-09-08'


def normalized_title(value):
    # Crossref titles may contain embedded XML typography and whitespace inside words.
    if '<' in value or '&' in value:
        value = BeautifulSoup(value, 'html.parser').get_text()
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())


def program_2024_titles(path):
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    result = {}
    for a in soup.select('td a[href]'):
        match = re.search(r'(10\.1145/\d+\.\d+)', a['href'])
        if not match:
            continue
        td = a.find_parent('td')
        for strong in td.find_all('strong'):
            title = re.sub(r'^(?:\s*\[[^]]+\]\s*)+', '', strong.get_text(' ', strip=True)).strip()
            if len(title) > 3:
                result[match[1]] = title
                break
    return result


def abstracts_2024(path):
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    result = []
    for marker in soup.find_all(['strong', 'b']):
        if marker.get_text(' ', strip=True).lower().rstrip(':') != 'abstract':
            continue
        td = marker.find_parent('td')
        if td is None:
            continue
        figure = td.find_parent('figure')
        title = td.find('strong').get_text(' ', strip=True)
        abstract = re.split(r'Abstract\s*:', td.get_text(' ', strip=True), maxsplit=1)[1].strip()
        result.append({'title': title, 'abstract': abstract,
                       'section': figure.get('id') if figure else None})
    return result


def main():
    index_path = DISCOVERY / 'program-index.json'
    index = json.loads(index_path.read_text())
    old_proof_path = CATALOG / 'extraction-corrections.json'
    proof = json.loads(old_proof_path.read_text()) if old_proof_path.exists() else {'title_corrections': [], 'excluded_slots': []}
    titles = program_2024_titles(DISCOVERY / 'asplos2024-program.html')
    assert len(titles) == 193
    program = next(p for p in index['programs'] if p['source_id'] == 'asplos2024-program')
    program['current_reading_record'] = 'references/proceedings/ASPLOS/2024/manifest.json'
    index['reading_status_scope'] = 'Entry reading_status retains the initial discovery state; subsequent reading is recorded in the linked venue manifest.'
    for entry in program['entries']:
        actual = titles[entry['doi']]
        if entry['title'] != actual:
            proof['title_corrections'].append({'source_id': program['source_id'], 'program_order': entry['program_order'],
                                             'doi': entry['doi'], 'before': entry['title'], 'after': actual,
                                             'reason': 'Leading award label was incorrectly selected as all or part of the title.'})
            entry['original_extracted_title'] = entry['title']
            entry['title'] = actual
    isca = next(p for p in index['programs'] if p['source_id'] == 'isca2026-program')
    empty = [p for p in isca['entries'] if not p['title'].strip()]
    if empty:
        assert len(empty) == 1 and empty[0]['program_order'] == 158
        isca['original_extracted_count'] = isca['count']
        for entry in empty:
            proof['excluded_slots'].append({'source_id': isca['source_id'], **entry,
                                           'reason': 'Official HTML contains a time slot with empty title and authors; not a paper entry.'})
        isca['entries'] = [p for p in isca['entries'] if p['title'].strip()]
        isca['count'] = len(isca['entries'])
    assert len(proof['title_corrections']) == 16 and isca['count'] == 172
    proof['scope'] = 'Title/slot extraction corrections only; original HTTP bodies and program order retained.'
    proof['corrected_program_entries'] = sum(p['count'] for p in index['programs'])
    index['reconciled_at'] = datetime.now(timezone.utc).isoformat()
    index['correction_record'] = str(old_proof_path.relative_to(ROOT))
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    old_proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')

    abstract_path = DISCOVERY / 'asplos2024-abstracts.html'
    abstracts = abstracts_2024(abstract_path)
    by_title = {normalized_title(p['title']): p for p in abstracts}
    assert len(abstracts) == len(by_title) == 193
    out = ROOT / 'references/proceedings/ASPLOS/2024/manifest.json'
    previous = {p['doi']: p for p in json.loads(out.read_text())['papers']} if out.exists() else {}
    papers = []
    for entry in program['entries']:
        abstract = by_title[normalized_title(entry['title'])]
        paper = dict(number=entry['program_order'], doi=entry['doi'], title=entry['title'],
                     abstract_title=abstract['title'], abstract=abstract['abstract'], abstract_section=abstract['section'],
                     abstract_sha256=hashlib.sha256(abstract['abstract'].encode()).hexdigest(),
                     reading_status='abstract_extracted_not_screened', full_text_status='not_archived_in_this_collection')
        if paper['number'] == 7:
            paper['source_note'] = 'Official abstract body includes Figure 1 text; preserve it without treating it as a clean abstract transcription.'
        if paper['number'] == 18:
            paper['source_note'] = 'Official abstract renders speedup symbols as question marks; no numerical repair inferred.'
        old = previous.get(entry['doi'], {})
        for key in ['screening', 'reading_status', 'selected_reading', 'full_text_status', 'pdf', 'source_followup']:
            if key in old:
                paper[key] = old[key]
        papers.append(paper)
    manifest = {'venue': 'ASPLOS', 'year': 2024,
                'scope': '193 official program DOI entries joined one-to-one to official abstract bodies. Not a formal three-volume/full-text archive.',
                'program_file': str((DISCOVERY / 'asplos2024-program.html').relative_to(ROOT)),
                'abstract_file': str(abstract_path.relative_to(ROOT)),
                'abstract_file_sha256': hashlib.sha256(abstract_path.read_bytes()).hexdigest(),
                'expected_program_entries': 193,
                'abstracts_screened': sum('screening' in p for p in papers),
                'selected_sections_read': sum('selected_reading' in p for p in papers), 'papers': papers}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'title_corrections': len(proof['title_corrections']), 'excluded_slots': len(proof['excluded_slots']),
                      'corrected_program_entries': proof['corrected_program_entries'], 'abstract_bodies': len(papers)}))


def reconcile_2026():
    """Match all detailed-program papers without assuming presentation year = publication year."""
    source = CATALOG / 'asplos2026-no-year-query.json'
    response = json.loads(source.read_text())['message']
    by_doi = {p['DOI']: p for p in response['items']}
    by_title = {normalized_title(p['title'][0]): p for p in response['items']}
    index = json.loads((DISCOVERY / 'program-index.json').read_text())
    program = next(p for p in index['programs'] if p['source_id'] == 'asplos2026-program')
    # Manually compared publication titles and author lists against the archived official program.
    variants = {
        36: ('10.1145/3779212.3790213', 'Errors becomes Attacks; same author list.'),
        70: ('10.1145/3779212.3790229', 'Program becomes Programs; same author list.'),
        94: ('10.1145/3779212.3790195', 'Once-for-All becomes Once4All; same author list.'),
        101: ('10.1145/3779212.3790172', 'HistoRL becomes RhymeRL; same author list.'),
        112: ('10.1145/3676642.3736126', 'Published title adds Hopps; same author list.'),
        138: ('10.1145/3760250.3762234', 'GPGPUs becomes GPUs; Simon Moore is Simon W. Moore in publication metadata.'),
        141: ('10.1145/3676642.3736129', 'Lambda-trim becomes λ-trim and subtitle changes; same four authors, first two appear in reversed order.'),
        150: ('10.1145/3779212.3790238', 'Transforming becomes Reconfigurable and Efficient is omitted; same five authors.'),
        165: ('10.1145/3760250.3762224', 'CPU becomes CPUs; program Nan Sung Kim is publication Nam Sung Kim. Other four authors match.'),
    }
    papers = []
    for entry in program['entries']:
        order = entry['program_order']
        record = by_doi[variants[order][0]] if order in variants else by_title[normalized_title(entry['title'])]
        papers.append({'program_order': order, 'program_title': entry['title'], 'program_authors': entry['authors'],
                       'doi': record['DOI'], 'published_title_raw': record['title'][0],
                       'published_title_text': ' '.join((BeautifulSoup(record['title'][0], 'html.parser').get_text(' ', strip=True) if '<' in record['title'][0] or '&' in record['title'][0] else record['title'][0]).split()),
                       'published_authors': record.get('author', []), 'container_title': record['container-title'][0],
                       'published_date': record['published']['date-parts'][0], 'pages': record.get('page'),
                       'match': 'manually_checked_title_and_author_variant' if order in variants else 'normalized_title',
                       'match_note': variants[order][1] if order in variants else 'HTML typography, Unicode and whitespace normalized; original title retained.',
                       'reading_status': 'bibliographic_metadata_checked_not_abstract_screened'})
    assert len(papers) == len({p['doi'] for p in papers}) == 168
    selected = {p['doi'] for p in papers}
    keynotes = [p for p in response['items'] if p['DOI'].startswith('10.1145/3779212.') and p['DOI'] not in selected]
    assert len(keynotes) == 3
    from collections import Counter
    counts = Counter(p['doi'].rsplit('.', 1)[0] for p in papers)
    assert dict(counts) == {'10.1145/3779212': 132, '10.1145/3760250': 20, '10.1145/3676642': 16}
    result = {'scope': 'Every detailed ASPLOS 2026 program paper matched to distinct publisher-deposited Crossref metadata. This is not a complete-volume query or abstract/full-paper reading.',
              'query_file': str(source.relative_to(ROOT)), 'query_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'query_total_results': response['total-results'], 'query_returned_items': len(response['items']),
              'query_is_exhaustive': False, 'program_header_count': 167, 'program_detail_count': 168,
              'distinct_matched_dois': 168, 'normalized_title_matches': 159, 'manually_checked_title_variants': 9,
              'matched_papers_by_volume_doi': dict(counts),
              'count_resolution': 'All 168 detailed titles have distinct publication DOI matches. Retain the conflicting header value 167 as an official-page discrepancy; no evidence supports deleting a detailed entry or assigning a reason for the inconsistent header.',
              'keynotes_excluded_from_paper_count': [{'doi': p['DOI'], 'title': p['title'][0], 'authors': p.get('author', []), 'pages': p.get('page')} for p in keynotes],
              'papers': papers}
    (CATALOG / 'asplos2026-program-doi-map.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'asplos2026_papers_with_doi': len(papers), 'title_variants': len(variants), 'keynotes_excluded': len(keynotes)}))


if __name__ == '__main__':
    main()
    reconcile_2026()
