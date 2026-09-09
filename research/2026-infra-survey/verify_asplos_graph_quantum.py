"""Verify four full abstracts and explicit author/version differences."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/screening-129-135'


def norm(s):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s).casefold())


def check(s):
    b = (ROOT / s['file']).read_bytes()
    assert len(b) == s['bytes'] and hashlib.sha256(b).hexdigest() == s['sha256']
    return b


def verify():
    sources = json.loads((D / 'sources.json').read_text())
    for s in sources:
        check(s)
        assert s['status_code'] == 200
    records = json.loads((D / 'screening.json').read_text())['records']
    papers = {p['program_order']: p for p in json.loads((D.parent / 'manifest.json').read_text())['papers']}
    assert [r['program_order'] for r in records] == [129, 132, 133, 134]
    for r in records:
        n = r['program_order']
        for field in ('pdf', 'abstract', 'first_page', 'full_text', 'view'):
            check(r[field])
        raw = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '1', str(ROOT/r['pdf']['file']), '-'])
        assert raw == check(r['first_page'])
        text = raw.decode()
        formal = papers[n]
        assert formal['doi'] == r['doi'] and formal['title'] == r['title']
        expected_title = r['title']
        if n == 129:
            expected_title = expected_title.replace('Sparse Architectures', 'Sparse Hardware Architectures')
        elif n == 134:
            expected_title += 's'
        assert norm(expected_title) == norm(r['source_title']) and norm(r['source_title']) in norm(text)
        authors = [a.get('given', '') + ' ' + a['family'] for a in formal['author_metadata']]
        if n == 129:
            assert authors[4] == 'Travis S. Humble'
            authors[4] = 'Travis Humble'
        assert authors == r['pdf_authors'] and all(norm(a) in norm(text) for a in authors)
        if n == 134:
            abstract = text.split('Abstract\n', 1)[1].split('CCS Concepts:', 1)[0].strip()
        else:
            soup = BeautifulSoup((D/f'{n}-arxiv.html').read_text(), 'html.parser')
            block = soup.select_one('blockquote.abstract')
            block.select_one('.descriptor').decompose()
            abstract = block.get_text(' ', strip=True)
            assert soup.select_one('meta[name=citation_title]')['content'] == r['source_title']
            assert [' '.join(reversed(x['content'].split(', ', 1))) for x in soup.select('meta[name=citation_author]')] == authors
            assert soup.select_one('.submission-history').get_text(' ', strip=True) == r['history']
            assert 'arXiv:' + r['arxiv_version'] in text
        assert (abstract + '\n').encode() == check(r['abstract'])
        assert (r['doi'] in text) == (n in (132, 134))
        info = subprocess.check_output(['pdfinfo', str(ROOT/r['pdf']['file'])], text=True)
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1]) == r['pdf']['pages']
        assert r['view']['actually_viewed'] and r['body_reading_status'] == 'not_read'
    result = dict(status='passed', primary_abstracts_screened=4, representative_pdfs=4,
                  representative_pdf_pages=59, body_candidates=[133], selected_sections_read=0,
                  first_pages_viewed=4, source_responses=len(sources), new_outline_sections=0)
    assert sum(r['pdf']['pages'] for r in records) == 59
    (D/'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
