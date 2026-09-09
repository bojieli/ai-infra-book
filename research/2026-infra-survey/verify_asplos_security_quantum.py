"""Verify two abstract-only records, including the split-column abstract."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/screening-111-128'


def norm(text):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', text).casefold())


def check(record):
    data = (ROOT / record['file']).read_bytes()
    assert len(data) == record['bytes']
    assert hashlib.sha256(data).hexdigest() == record['sha256']
    return data


def verify():
    sources = json.loads((D / 'sources.json').read_text())
    for source in sources:
        check(source)
        assert source['status_code'] == 200
    records = json.loads((D / 'screening.json').read_text())['records']
    papers = {p['program_order']: p for p in json.loads((D.parent / 'manifest.json').read_text())['papers']}
    assert [r['program_order'] for r in records] == [123, 128]
    for r in records:
        for field in ('pdf', 'first_page', 'abstract', 'full_text', 'view'):
            check(r[field])
        pdf = ROOT / r['pdf']['file']
        raw = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '1', str(pdf), '-'])
        assert raw == check(r['first_page'])
        text = raw.decode()
        spans = r['abstract_character_spans']
        assert all(0 <= a < b <= len(text) for a, b in spans)
        abstract = ' '.join(' '.join(text[a:b] for a, b in spans).split())
        assert (abstract + '\n').encode() == check(r['abstract'])
        assert 'Permission to make' not in abstract
        formal = papers[r['program_order']]
        assert formal['title'] == r['title'] and formal['doi'] == r['doi']
        assert norm(r['title']) in norm(text)
        authors = [a.get('given', '') + ' ' + a['family'] for a in formal['author_metadata']]
        assert authors == r['pdf_authors'] and all(norm(a) in norm(text) for a in authors)
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == r['pdf']['pages']
        assert r['reading_status'] == 'full_abstract_read' and r['body_reading_status'] == 'not_read'
        assert r['view']['actually_viewed'] and r['decision'] == 'archive_only'
        if r['program_order'] == 123:
            assert r['doi'] in text and abstract.endswith('threads).')
        else:
            assert 'arXiv:2406.15721v1' in text and r['doi'] not in text
            soup = BeautifulSoup((D / '128-arxiv.html').read_text(), 'html.parser')
            assert norm(soup.select_one('meta[name=citation_title]')['content']) == norm(r['title'])
            html_authors = [x['content'].split(', ', 1) for x in soup.select('meta[name=citation_author]')]
            assert set(norm(given + ' ' + family) for family, given in html_authors) == set(map(norm, authors))
            assert 'Sat, 22 Jun 2024 03:33:30 UTC' in soup.select_one('.submission-history').get_text(' ', strip=True)
    result = dict(status='passed', primary_abstracts_screened=2, representative_pdfs=2,
                  representative_pdf_pages=31, selected_sections_read=0, first_pages_viewed=2,
                  source_responses=len(sources), new_outline_sections=0, downloaded_code_executed=False)
    (D / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
