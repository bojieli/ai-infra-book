#!/usr/bin/env python3
"""Re-extract original abstracts and identities offline; run only our code and Poppler."""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import unicodedata
from bs4 import BeautifulSoup

P=Path(__file__).resolve().parent
ROOT=P.parents[4]
data=json.loads((P/'reading-records.json').read_text())
manifest=json.loads((P.parent/'manifest.json').read_text())
official={p['program_order']:p for p in manifest['papers']}
seen=set()

def check(obj):
    p=(ROOT/obj['file']).resolve()
    assert p.is_relative_to(P), p
    b=p.read_bytes()
    assert len(b)==obj['bytes'] and hashlib.sha256(b).hexdigest()==obj['sha256'], p
    seen.add(obj['file'])
    return b

def walk(obj):
    if isinstance(obj,dict):
        if {'file','bytes','sha256'}<=obj.keys():check(obj)
        for value in obj.values():walk(value)
    elif isinstance(obj,list):
        for value in obj:walk(value)

def norm(s):
    s=unicodedata.normalize('NFKD',s)
    return re.sub(r'[^a-z0-9]','',s.lower())

def segment(t,start,end,include_start=False,include_end=False):
    pos=t.index(start);stop=t.index(end,pos+len(start))
    return t[pos if include_start else pos+len(start):stop+len(end) if include_end else stop]

walk(data)
selection=json.loads((P/'selection-snapshot.json').read_text())
assert {r['program_order'] for r in selection}=={157,159,160,161,162,163}
assert all(not r['abstract_read'] and r['representative_pdf'] is None for r in selection)
assert data['new_full_abstracts']==len(data['records'])==5
assert len(data['gaps'])==1 and data['gaps'][0]['program_order']==163
assert data['selected_body_reading_records']==data['selected_body_physical_pages']==0
assert data['actual_rendered_pages_viewed']==5 and not data['body_reading_is_full_paper']

identity_checks=[]
pages=0
for r in data['records']:
    n=r['program_order']; e=official[n]
    assert e['doi']==r['doi'] and norm(e['title'])==norm(r['title'])
    assert e['page']==r['identity']['formal_page_range']
    names=[a['given']+' '+a['family'] for a in e['author_metadata']]
    names=[r['identity']['author_aliases'].get(a,a) for a in names]
    assert names==r['authors']
    pdf=r['representative_pdf'];f=ROOT/pdf['file']
    pi=subprocess.check_output(['pdfinfo',str(f)],text=True)
    count=int(re.search(r'^Pages:\s+(\d+)',pi,re.M).group(1));assert count==pdf['pages'];pages+=count
    first=subprocess.check_output(['pdftotext','-f','1','-l','1',str(f),'-'])
    assert first==check(pdf['first_page_text'])
    first=first.decode()
    assert norm(r['title']) in norm(first)
    for name in names:assert norm(name) in norm(first), name
    if n in [160,161,162]:assert norm(r['doi']) in norm(first)
    assert r['selected_reading']['physical_pdf_pages']==[]
    png=r['selected_reading']['viewed_page_images']['1'];b=check(png)
    assert b[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',b[16:24]))>=1000
    assert png['actually_viewed']
    if n in [157,159]:
        soup=BeautifulSoup((ROOT/r['source_file']).read_text(),'html.parser')
        a=soup.select_one('blockquote.abstract');a.select_one('.descriptor').decompose()
        abstract=a.get_text(' ',strip=True)
        assert norm(soup.select_one('meta[name="citation_title"]')['content'])==norm(r['title'])
        aauthors=[]
        for m in soup.select('meta[name="citation_author"]'):
            last,given=m['content'].split(', ',1);aauthors.append(given+' '+last)
        assert aauthors==names
        assert 'arXiv:'+r['version'] in first
        assert r['version'] in soup.get_text(' ',strip=True)
        assert norm(abstract)==norm(first.split('Abstract',1)[1].split('\n1\n',1)[0])
        if n==157:
            home=BeautifulSoup(check(r['identity']['author_publication_page']).decode(),'html.parser')
            link=home.select_one('a[href="https://dl.acm.org/doi/'+r['doi']+'"]')
            assert link and norm(link.get_text())==norm(r['title'])
            row=link.find_parent(class_='single-experience')
            assert row and all(norm(x) in norm(row.get_text()) for x in names)
            assert 'presentation is delayed' in home.get_text(' ',strip=True)
        else:
            assert 'accepted to ASPLOS 2025' in soup.select_one('.comments').get_text()
            cr=json.loads(check(r['identity']['crossref']))['message'];assert cr['DOI']==r['doi']
            assert norm(cr['title'][0])==norm(r['title'])
            assert cr['page']=='970-986' and count==15
    else:
        if n==160:
            text=segment(first,'Dataflow circuits have been studied','building formally verified dataflow HLS compilers.',True,True)
        elif n==161:
            text=segment(first,'Abstract','CCS Concepts:')
        else:
            left=segment(first,'Abstract','Permission to make digital')
            right=segment(first,'our proposed techniques','ACM Reference Format:',True)
            text=left+' '+right
            assert 'We demonstrate' in left and right.startswith('our proposed techniques')
            assert '0.8% performance overhead.' in right
        abstract=' '.join(text.split())
    assert abstract==r['abstract']
    assert hashlib.sha256(abstract.encode()).hexdigest()==r['abstract_sha256']
    assert check(r['abstract_text_file'])==(abstract+'\n').encode()
    identity_checks.append({'program_order':n,'doi':r['doi'],'authors_checked':len(names),'pdf_pages':count,'abstract_reextraction':'pass'})
assert pages==data['representative_pdf_pages']==78
assert data['representative_pdfs']==5

sources={s['id']:s for s in data['sources']}
assert len(sources)==18
statuses={}
for s in sources.values():
    assert s['retrieved_at'] and s['url'] and s['final_url']
    statuses[s['status_code']]=statuses.get(s['status_code'],0)+1
    if s['file'].endswith('.pdf'):
        assert s['status_code']==200 and check(s).startswith(b'%PDF')
for logpath in P.glob('*-jobs.json.results.json'):
    for log in json.loads(logpath.read_text()):
        s=sources[log['id']]
        for k in ['url','final_url','status_code','bytes','sha256','retrieved_at']:assert s[k]==log[k]
        assert Path(s['file']).name==Path(log['file']).name
assert statuses=={200:12,429:4,403:2},statuses
assert sum(1 for s in sources.values() if s['bytes']==0)==3

gap=data['gaps'][0];e=official[163];assert e['doi']==gap['doi'] and e['title']==gap['title']
cr=json.loads(check(gap['identity_source']))['message']
assert cr['DOI']==gap['doi'] and norm(cr['title'][0])==norm(gap['title']) and not cr.get('abstract')
assert [a['given']+' '+a['family'] for a in cr['author']]==gap['authors']
blog=BeautifulSoup(check(gap['related_primary_context']).decode(),'html.parser')
assert blog.select_one('a[href="https://dl.acm.org/doi/abs/'+gap['doi']+'"]')
failure=json.loads(check(gap['tool_failure']))
assert '403' in failure and 'Failed to fetch' in failure
assert gap['full_abstract_read'] is False and gap['representative_pdf'] is None and gap['body_pages_read']==[]
identity_checks.append({'program_order':163,'doi':gap['doi'],'authors_checked':len(gap['authors']),'abstract_reextraction':'gap_not_counted'})

result={'status':'pass','file_proofs_checked':len(seen),'formal_identity_checks':identity_checks,
        'full_primary_abstracts_reextracted':5,'representative_pdfs':5,'representative_pdf_pages':78,
        'actual_viewed_first_page_images_verified':5,'selected_body_pages':0,
        'http_responses':18,'http_statuses':statuses,'genuine_zero_byte_failed_responses':3,
        'additional_failed_web_open':1,'unresolved_original_abstracts':[163],
        'version_limits':['157/162 belong to ASPLOS2024 Volume4, appear in 2025 program.','159 is 15-page arXiv v1; formal 17-page PDF request429.'],
        'verification_limits':'Hash/PNG/record verification cannot independently prove visual reading; actual five-page image review recorded. No downloaded code executed.'}
(P/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
