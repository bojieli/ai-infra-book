#!/usr/bin/env python3
"""Reconcile cached ASPLOS 2025 program DOIs with publisher-deposited metadata.

Does not fetch papers or mark abstracts read. The search result is checked against
the actual program, never treated as an exhaustive publisher volume listing.
"""
from pathlib import Path
import collections
import html
import json
import re
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'references/proceedings/ASPLOS/2025'


def normalized(text):
    text = BeautifulSoup(text, 'html.parser').get_text(' ') if '<' in text else html.unescape(text)
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', text).casefold())


def main():
    source = ROOT / 'references/proceedings/discovery/2026-09-08/program-index.json'
    program = next(p for p in json.loads(source.read_text())['programs']
                   if p['source_id'] == 'asplos2025-program')
    assert len(program['entries']) == program['count'] == 184
    metadata = {}
    locations = collections.defaultdict(list)
    for name in ['asplos2025-title-query.json', 'asplos2024-vol4-title-query.json']:
        path = DEST / name
        payload = json.loads(path.read_text())['message']
        for index, item in enumerate(payload['items']):
            doi = item['DOI'].lower()
            if doi in metadata:
                assert metadata[doi] == item, doi
            metadata[doi] = item
            locations[doi].append({'file': str(path.relative_to(ROOT)), 'item_index': index})
    output = DEST / 'manifest.json'
    previous = {p['doi']: p for p in json.loads(output.read_text())['papers']} if output.exists() else {}
    papers = []
    for entry in program['entries']:
        dois = {link['url'].removeprefix('https://doi.org/').lower()
                for link in entry['links'] if link['url'].startswith('https://doi.org/')}
        assert len(dois) == 1, entry['title']
        doi = dois.pop()
        item = metadata[doi]
        volume = doi.split('/')[1].split('.')[0]
        volume_meta = json.loads((DEST / f'volume-{volume}.json').read_text())['message']
        publisher_title = item['title'][0]
        matches = normalized(publisher_title) == normalized(entry['title'])
        title = entry['title'] if matches else ' '.join(BeautifulSoup(publisher_title, 'html.parser').get_text(' ').split())
        row = dict(id='asplos2025-' + doi.split('/')[-1], doi=doi,
                   program_order=entry['program_order'], presentation_year=2025,
                   program_title=entry['title'], title=title, publisher_title=publisher_title,
                   title_matches_normalized=matches,
                   author_metadata=item.get('author', []), publication_date=item.get('published'),
                   container_title=item.get('container-title', []), page=item.get('page'),
                   volume_doi='10.1145/' + volume, volume_title=volume_meta['title'][0],
                   volume_publication_date=volume_meta.get('published'),
                   publisher_links=item.get('link', []), metadata_sources=locations[doi],
                   abstract=item.get('abstract'), reading_status='metadata_matched_not_screened',
                   full_text_status='not_archived')
        if not row['title_matches_normalized']:
            row['title_note'] = 'Matched by the exact DOI linked in the official program; title variant retained.'
        for key in ['screening', 'reading_status', 'selected_reading', 'full_text_status', 'pdf', 'text', 'pages', 'public_version_note', 'public_abstract', 'source_followup']:
            if key in previous.get(doi, {}):
                row[key] = previous[doi][key]
        papers.append(row)
    assert len({p['doi'] for p in papers}) == 184
    counts = dict(collections.Counter(p['volume_doi'] for p in papers))
    assert counts == {'10.1145/3676641': 88, '10.1145/3669940': 72, '10.1145/3622781': 24}
    manifest = dict(scope='184 official ASPLOS 2025 program entries matched to publisher-deposited Crossref metadata; not full-text or abstract-reading completion.',
                    source_program=dict(file=program['source_file'], sha256=program['source_sha256']),
                    program_entries=184, metadata_matched=184, volume_counts=counts,
                    abstract_metadata_available=sum(bool(p['abstract']) for p in papers),
                    public_abstracts_available=sum('public_abstract' in p for p in papers),
                    abstracts_screened=sum('screening' in p for p in papers),
                    selected_sections_read=sum(p['reading_status']=='selected_sections_read' for p in papers),
                    public_pdfs_archived=sum('pdf' in p for p in papers),
                    title_variants=sum(not p['title_matches_normalized'] for p in papers),
                    query_exhaustive=False, papers=papers)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'papers'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
