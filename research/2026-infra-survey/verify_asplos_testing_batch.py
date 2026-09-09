"""Verify five complete author-PDF abstracts; no body-reading inference."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/screening-111-123'


def norm(text):
    text = unicodedata.normalize('NFKD', text.replace('ı', 'i')).casefold()
    return re.sub('[^a-z0-9]', '', text)


def check(record):
    b = (ROOT / record['file']).read_bytes()
    assert len(b) == record['bytes']
    assert hashlib.sha256(b).hexdigest() == record['sha256']
    return b


def verify():
    sources = json.loads((D / 'sources.json').read_text())
    for source in sources:
        check(source)
        assert source['status_code'] == 200
    records = json.loads((D / 'screening.json').read_text())['records']
    manifest = {r['program_order']: r for r in json.loads((D.parent/'manifest.json').read_text())['papers']}
    assert [r['program_order'] for r in records] == [112, 118, 120, 121, 122]
    for record in records:
        for field in ('pdf', 'first_page', 'abstract', 'view'):
            check(record[field])
        pdf = ROOT / record['pdf']['file']
        first = subprocess.check_output(['pdftotext', '-raw', '-f', '1', '-l', '1', str(pdf), '-'])
        assert first == check(record['first_page'])
        text = first.decode()
        extraction = record['abstract_extraction']
        abstract = text.split(extraction['start'], 1)[1].split(extraction['end'], 1)[0].strip()
        assert (abstract+'\n').encode() == check(record['abstract'])
        info = subprocess.check_output(['pdfinfo', str(pdf)]).decode()
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1)) == record['pdf']['pages']
        formal = manifest[record['program_order']]
        assert record['doi'] == formal['doi'] and record['title'] == formal['title']
        assert norm(record['doi']) in norm(text) and norm(record['title']) in norm(text)
        assert len(record['pdf_authors']) == len(formal['author_metadata'])
        for pdf_name, author in zip(record['pdf_authors'], formal['author_metadata']):
            assert norm(pdf_name) in norm(text)
            forward = norm(author.get('given', '')+' '+author['family'])
            reverse = norm(author['family']+' '+author.get('given', ''))
            assert norm(pdf_name) in (forward, reverse)
        assert record['view']['actually_viewed'] is True
        assert record['body_reading_status'] == 'not_read'
        if record['program_order'] == 118:
            assert 'ASPLOS ’24' in text and '2024' in text
    result = dict(status='passed', source_responses=len(sources), complete_abstracts=5,
                  representative_pdfs=5, archived_pdf_pages=sum(r['pdf']['pages'] for r in records),
                  first_pages_viewed=5, selected_body_scopes=0, canonical_merge_pending=True,
                  outline_additions=0, version_year_exceptions=[118], author_metadata_variants=[121])
    (D/'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
