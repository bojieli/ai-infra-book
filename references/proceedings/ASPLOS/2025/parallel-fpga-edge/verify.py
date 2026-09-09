#!/usr/bin/env python3
"""Offline source bytes, formal DOI identities and five original abstracts. No network."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import unicodedata
from bs4 import BeautifulSoup

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
data = json.loads((P / 'reading-records.json').read_text())
official = {p['program_order']: p for p in json.loads((P.parent / 'manifest.json').read_text())['papers']}
seen = set()

def check(obj):
    f = (ROOT / obj['file']).resolve()
    assert f.is_relative_to(P), f
    b = f.read_bytes()
    assert len(b) == obj['bytes'] and hashlib.sha256(b).hexdigest() == obj['sha256'], f
    seen.add(obj['file']); return b

def walk(obj):
    if isinstance(obj, dict):
        if {'file', 'bytes', 'sha256'} <= obj.keys(): check(obj)
        for v in obj.values(): walk(v)
    elif isinstance(obj, list):
        for v in obj: walk(v)

def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s).lower())

def span(t, start, end, include_start=False, include_end=False):
    a = t.index(start); b = t.index(end, a + len(start))
    return t[a if include_start else a + len(start):b + len(end) if include_end else b]

walk(data)
selection = json.loads(check(data['selection']))
assert {r['program_order'] for r in selection} == {19,25,29,30,31,32}
assert all(not r['abstract_read'] and r['representative_pdf'] is None for r in selection)
assert {r['program_order'] for r in data['records']} == {19,25,29,30,31}
assert len(data['gaps']) == 1 and data['gaps'][0]['program_order'] == 32
assert len({r['doi'] for r in data['records'] + data['gaps']}) == 6
assert data['new_full_abstracts'] == len(data['records']) == 5
assert data['selected_body_reading_records'] == data['selected_body_physical_pages'] == 0
assert data['actual_rendered_pages_viewed'] == data['abstract_identity_pages_read_separately'] == 3
assert not data['body_reading_is_full_paper']

prov = json.loads(check(data['local_copy_provenance']))
rb = (P / 'registry-original.json').read_bytes()
assert len(rb) == prov['bytes'] == 2011764
assert hashlib.sha256(rb).hexdigest() == prov['sha256'] == '0443b8c7f441a3390c5b68300ee9474b7dc5f84517656c65ca77efb21a567553'
assert rb == (ROOT / prov['source_archive_path']).read_bytes()
assert prov['status_code'] == 200 and prov['url'].startswith('https://api.crossref.org/works?')
registry = json.loads(rb)['message']['items']
assert len(registry) == 1000
identities = []
for r in data['records'] + data['gaps']:
    n = r['program_order']; e = official[n]
    assert e['doi'] == r['doi'] and e['title'] == r['title']
    authors = [a['given'] + ' ' + a['family'] for a in e['author_metadata']]
    assert authors == r['authors']
    rows = [row for row in registry if row['DOI'] == r['doi']]
    assert len(rows) == 1; row = rows[0]
    # Crossref preserves italic markup in PhasePrint's title; compare visible text.
    source_title = BeautifulSoup(row['title'][0], 'html.parser').get_text()
    assert norm(source_title) == norm(r['title']) and row['page'] == e['page']
    assert [a['given'] + ' ' + a['family'] for a in row['author']] == authors
    assert not row.get('abstract')
    year = e['volume_publication_date']['date-parts'][0][0]
    assert year == (2024 if n in [29,32] else 2025)
    identities.append({'program_order':n,'doi':r['doi'],'ordered_formal_authors_checked':len(authors),'formal_publication_year':year,'presentation_program_year':2025})

pages = 0; reextracted = []
for r in data['records']:
    n = r['program_order']; names = r['authors']; identity = r['identity']
    assert identity['official_program_doi'] == r['doi']
    assert identity['publisher_author_names'] == names and identity['author_aliases'] == {}
    assert identity['formal_page_range'] == official[n]['page']
    assert identity['formal_volume_title'] == official[n]['volume_title']
    assert identity['formal_publication_date'] == official[n]['volume_publication_date']
    assert r['selected_reading']['physical_pdf_pages'] == [] and r['selected_reading']['page_text'] == {}
    assert r['body_reading_candidate_priority'] == 'not_selected'
    sf = ROOT / r['source_file']
    assert hashlib.sha256(sf.read_bytes()).hexdigest() == r['source_sha256']
    if n in [19,25]:
        assert r['representative_pdf'] is None and r['selected_reading']['viewed_page_images'] == {}
        assert not identity['pdf_title_authors_visually_verified'] and not identity['pdf_official_doi_visually_verified']
        if n == 19:
            soup = BeautifulSoup(sf.read_text(), 'html.parser')
            nodes = soup.select('.rendering_researchoutput_abstractportal .textblock > p'); assert len(nodes) == 1
            abstract = ' '.join(nodes[0].get_text(' ', strip=True).split())
            assert soup.select_one('meta[name="citation_title"]')['content'] == r['title']
            assert soup.select_one('meta[name="citation_doi"]')['content'] == r['doi']
            assert soup.select_one('meta[name="citation_firstpage"]')['content'] == '882'
            assert soup.select_one('meta[name="citation_lastpage"]')['content'] == '896'
            aliases = identity['html_author_aliases_to_formal']
            assert aliases == {'Mahmut Kandemir':'Mahmut T. Kandemir','Chitaranjan Das':'Chita R. Das'}
            assert [aliases.get(m['content'],m['content']) for m in soup.select('meta[name="citation_author"]')] == names
            home = BeautifulSoup(check(identity['author_home']).decode(), 'html.parser')
            b = home.find('b', string=r['title']); assert b is not None
            assert b.parent.parent.select_one('a[href="https://todo.pdf"]')
            assert abstract.startswith('Due to the limited compute power') and abstract.endswith('similar superior quality standards.')
        else:
            js = check(r['extraction']['route_evidence']).decode()
            assert 'api/public/' in js and 'sfu_authors__random_id=' in js and 'v2/publications/?page=' in js
            shell = BeautifulSoup(check(identity['institution_page']).decode(), 'html.parser')
            assert not r['title'] in shell.get_text()
            assert shell.select_one('script[src="/research/expertise-engine/static/js/main.cb5b4d5f.chunk.js"]')
            api = json.loads(sf.read_text()); assert api['total_result'] == 47 and api['response_result'] == 10
            matches = [o for o in api['results'] if o['DOI'] == r['doi']]; assert len(matches) == 1
            obj = matches[0]; abstract = obj['abstract']
            assert obj['title'] == r['title'] and obj['authorsCnt'] == 3
            assert obj['all_authors'].split(', ') == identity['institution_author_initials'] == ['Kumar A.M.A.','Prasanna A.','Shriraman A.']
            assert obj['sfu_authors'] == [{'random_id':identity['institution_faculty_uuid'],'preferred_first_name':'Arrvindh','preferred_last_name':'Shriraman'}]
            assert obj['date'] == '2025-03-30'
            assert abstract.startswith('Current domain-specific architectures (DSAs)')
            assert 'neces- sary' in abstract and '(2kb)' in abstract and '(256kb)' in abstract
            assert abstract.endswith('require 6.6% of on-chip energy.')
            bad = json.loads((P/'025-institution-api.html').read_text())
            assert bad['total_result'] == 55242 and not any(o['DOI'] == r['doi'] for o in bad['results'])
    else:
        pdf = r['representative_pdf']; f = ROOT / pdf['file']
        count = int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(f)],text=True),re.M).group(1))
        assert count == pdf['pages'] == {29:15,30:17,31:14}[n]; pages += count
        firstb = subprocess.check_output(['pdftotext','-f','1','-l','1',str(f),'-'])
        assert firstb == check(pdf['first_page_text']); first = firstb.decode()
        assert subprocess.check_output(['pdftotext',str(f),'-']) == check(pdf['text'])
        assert subprocess.check_output(['pdftotext','-layout',str(f),'-']) == check(pdf['layout_text'])
        assert norm(r['title']) in norm(first) and norm(r['doi']) in norm(first)
        for name in names: assert norm(name) in norm(first),(n,name)
        assert identity['pdf_title_authors_visually_verified'] and identity['pdf_official_doi_visually_verified']
        png = r['selected_reading']['viewed_page_images']['1']; b = check(png)
        assert b[:8] == b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',b[16:24])) >= 1000 and png['actually_viewed']
        if n == 29:
            left = span(first,'CPU-FPGA heterogeneous architectures','ACM Reference Format:',True)
            right = span(first,'IP, Salus presents','CPU-FPGA heterogeneous architectures',True)
            assert left.strip().endswith('security-enhanced FPGA')
            assert right.strip().endswith('minor efforts required.')
            abstract = ' '.join((left+' '+right).split())
            assert 'ASPLOS ’24' in first
        elif n == 30:
            left = span(first,'Abstract','Permission to make digital')
            right = span(first,'hardware differences and a platform-independent layer','CCS Concepts:',True)
            assert left.strip().endswith('a platform-specific layer that abstracts')
            abstract = ' '.join((left+' '+right).split())
            assert abstract.endswith('while maintaining comparable performance.')
            home = BeautifulSoup(check(identity['author_page']).decode(),'html.parser')
            assert home.select_one('a[href="/uploads/2025/harmonia-asplos25.pdf"]')
            assert 'August, 2024' in home.get_text(' ',strip=True)
            other = home.select_one('p.pub-abstract').get_text(' ',strip=True)
            assert norm(other) == norm(abstract.replace('×','x'))
            assert '15-23x' in other and '15-23×' in abstract
        else:
            abstract = ' '.join(span(first,'Cloud FPGAs, with their scalable and flexible nature,','13× faster, and costs 92% less than the state-of-the-art.',True,True).split())
            assert 'However, their increasing adoption introduces unique security challenges.' in abstract
            assert '300 unique FPGAs' in abstract and 'four AWS geographic regions' in abstract
            assert 'CCS Concepts' not in abstract
    assert abstract == r['abstract']
    assert hashlib.sha256(abstract.encode()).hexdigest() == r['abstract_sha256']
    assert check(r['abstract_text_file']) == (abstract+'\n').encode()
    reextracted.append(n)
assert pages == data['representative_pdf_pages'] == 46
assert sum(r['representative_pdf'] is not None for r in data['records']) == data['representative_pdfs'] == 3

sources = {s['id']:s for s in data['sources']}; assert len(sources) == len(data['sources']) == 17
statuses = {}
for s in sources.values():
    assert s['retrieved_at'] and s['url'] and s['final_url']
    statuses[s['status_code']] = statuses.get(s['status_code'],0)+1
    if s['file'].endswith('.pdf'): assert s['status_code'] == 200 and check(s).startswith(b'%PDF')
    assert 'todo.pdf' not in s['url']
for logpath in P.glob('*-jobs.json.results.json'):
    logs = json.loads(logpath.read_text()); jobs = json.loads((P/logpath.name.removesuffix('.results.json')).read_text())
    assert {x['id'] for x in logs} == {x['id'] for x in jobs}
    for log in logs:
        s = sources[log['id']]
        for k in ['url','final_url','status_code','bytes','sha256','retrieved_at']: assert s[k] == log[k]
        assert Path(s['file']).name == Path(log['file']).name
assert statuses == {200:12,403:5},statuses

gap = data['gaps'][0]
assert gap['full_abstract_read'] is False and gap['representative_pdf'] is None and gap['body_pages_read'] == []
home = BeautifulSoup(check(gap['author_publication_page']).decode(),'html.parser')
li = next(li for li in home.select('li') if li.find('strong',string=gap['title']))
assert not li.select('a')
for author in gap['authors']:
    given,family = author.rsplit(' ',1)
    assert family+', '+given in li.get_text(' ',strip=True)
assert 'ASPLOS) · 2024' in li.get_text(' ',strip=True)
other = BeautifulSoup(check(gap['different_event_source']).decode(),'html.parser')
heading = other.find(id='P2.1.01-Wed')
assert heading.get_text(' ',strip=True) == gap['different_event_exclusion']['title']
assert heading.get_text(' ',strip=True) != gap['title']
nextp = heading.find_next_siblings('p',limit=3)
assert [b.get_text() for b in nextp[1].select('strong')] == gap['different_event_exclusion']['authors']
assert len(gap['authors']) == 8 and len(gap['different_event_exclusion']['authors']) == 4
assert gap['different_event_exclusion']['not_original_asplos_abstract']
assert not gap['different_event_exclusion']['pdf_downloaded']
assert all(sources[sid]['status_code'] == 403 for sid in gap['failed_source_ids'])

result = {'status':'pass','file_proofs_checked':len(seen),'formal_identity_checks':identities,
          'full_primary_abstracts_reextracted':5,'reextracted_orders':reextracted,
          'representative_pdfs':3,'representative_pdf_pages':46,
          'actual_viewed_first_page_images_verified':3,'selected_body_pages':0,'body_candidates':0,
          'http_responses':17,'http_statuses':statuses,'unresolved_original_abstracts':[32],
          'http200_unrelated_api_response_excluded':True,'author_pdf_placeholder_not_requested':True,
          'static_js_route_inspected_not_executed':True,'different_event_abstract_excluded':True,
          'local_primary_registry_copy':'byte-identical previous archive; no new HTTP',
          'version_limits':['19 institution author spellings differ explicitly from formal names; original HTML abstract only.',
                            '25 exact institutional API abstract field, source section Scopus Publications; no PDF.',
                            '29/32 formal ASPLOS2024 Volume4 identities preserved in2025 program.',
                            '30 author webpage August2024 vs PDF ASPLOS2025; canonical complete PDF abstract.',
                            '32 RISC-V Summit Agile/four-author extended abstract is not original eight-author ASPLOS abstract.'],
          'verification_limits':'Offline primary re-extraction and source/identity/status checks; mechanically re-extracted full PDF text is not body-reading evidence. PNG checks cannot independently prove reading; actual three-page visual review recorded. No third-party code executed.'}
(P/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
