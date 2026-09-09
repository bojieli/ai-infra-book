"""Keep failed paper retrieval distinct from one institutional abstract."""
from pathlib import Path
import hashlib
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'references/proceedings/ASPLOS/2025/frugal-discovery'


def verify():
    sources = json.loads((D/'sources.json').read_text())
    for r in sources:
        data = (ROOT/r['file']).read_bytes()
        assert len(data) == r['bytes'] and hashlib.sha256(data).hexdigest() == r['sha256']
    assert len(sources) == 7
    assert sorted(r['status_code'] for r in sources) == [200, 200, 200, 200, 403, 403, 404]
    records = json.loads((D/'screening.json').read_text())['records']
    assert len(records) == 1
    r = records[0]
    formal = next(p for p in json.loads((D.parent/'manifest.json').read_text())['papers'] if p['program_order'] == 130)
    assert r['title'] == formal['title'] and r['doi'] == formal['doi']
    soup = BeautifulSoup((ROOT/r['source_file']).read_text(), 'html.parser')
    assert r['title'] in soup.get_text(' ', strip=True)
    assert any(r['doi'] in a['href'] for a in soup.select('a[href]'))
    block = soup.select_one('#abstract-head').parent
    block.select_one('#abstract-head').decompose()
    text = block.get_text(' ', strip=True) + '\n'
    assert text == (ROOT/r['abstract']['file']).read_text()
    assert hashlib.sha256(text.encode()).hexdigest() == r['abstract']['sha256']
    assert r['reading_status'] == 'full_abstract_read' and r['body_reading_status'] == 'not_read'
    for name in ('gsw.html', 'shaoxun.html'):
        soup = BeautifulSoup((D/name).read_text(), 'html.parser')
        assert any('10.1145/3669940.3707245' in a['href'] for a in soup.select('a[href]'))
    assert not (D/'frugal-acm-pdf.response').read_bytes().startswith(b'%PDF-')
    result = dict(status='passed', source_responses=7, failed_responses=3,
                  primary_abstracts_screened=1, representative_pdfs=0,
                  frugal_paper_unavailable=True, body_reading_credit=0,
                  downloaded_code_executed=False)
    (D/'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    print(json.dumps(verify()))
