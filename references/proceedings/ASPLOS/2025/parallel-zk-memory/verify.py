#!/usr/bin/env python3
"""Offline primary-source re-extraction/identity verification. No network or third-party code execution."""
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
official={p['program_order']:p for p in json.loads((P.parent/'manifest.json').read_text())['papers']}
seen=set()

def check(obj):
    p=(ROOT/obj['file']).resolve()
    assert p.is_relative_to(P),p
    b=p.read_bytes()
    assert len(b)==obj['bytes'] and hashlib.sha256(b).hexdigest()==obj['sha256'],p
    seen.add(obj['file']);return b

def walk(obj):
    if isinstance(obj,dict):
        if {'file','bytes','sha256'}<=obj.keys():check(obj)
        for v in obj.values():walk(v)
    elif isinstance(obj,list):
        for v in obj:walk(v)

def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).lower())

def segment(t,start,end,include_start=False,include_end=False):
    pos=t.index(start);stop=t.index(end,pos+len(start))
    return t[pos if include_start else pos+len(start):stop+len(end) if include_end else stop]

def check_crossref(proof,record):
    cr=json.loads(check(proof))['message']
    assert cr['DOI']==record['doi'] and norm(cr['title'][0])==norm(record['title'])
    assert [a['given']+' '+a['family'] for a in cr['author']]==record['authors']
    return cr

walk(data)
selection=json.loads(check(data['selection']))
assert {r['program_order'] for r in selection}=={165,166,167,168,183,184}
assert all(not r['abstract_read'] and r['representative_pdf'] is None for r in selection)
assert {r['program_order'] for r in data['records']}=={165,167,168,183,184}
assert data['new_full_abstracts']==len(data['records'])==5
assert len(data['gaps'])==1 and data['gaps'][0]['program_order']==166
assert data['selected_body_reading_records']==data['selected_body_physical_pages']==0
assert data['actual_rendered_pages_viewed']==data['abstract_identity_pages_read_separately']==5
assert not data['body_reading_is_full_paper']
assert len({r['doi'] for r in data['records']+data['gaps']})==6

identity_checks=[];pages=0
for r in data['records']:
    n=r['program_order'];e=official[n]
    assert e['doi']==r['doi'] and norm(e['title'])==norm(r['title'])
    assert e['page']==r['identity']['formal_page_range']
    names=[a['given']+' '+a['family'] for a in e['author_metadata']]
    assert names==r['authors']==r['identity']['publisher_author_names']
    assert r['identity']['official_program_doi']==r['doi']
    pdf=r['representative_pdf'];f=ROOT/pdf['file']
    pi=subprocess.check_output(['pdfinfo',str(f)],text=True)
    count=int(re.search(r'^Pages:\s+(\d+)',pi,re.M).group(1));assert count==pdf['pages'];pages+=count
    first_bytes=subprocess.check_output(['pdftotext','-f','1','-l','1',str(f),'-'])
    assert first_bytes==check(pdf['first_page_text']);first=first_bytes.decode()
    assert norm(r['title']) in norm(first)
    for name in names:assert norm(name) in norm(first),(n,name)
    if n in [165,168,184]:assert norm(r['doi']) in norm(first)
    assert r['identity']['pdf_title_authors_visually_verified']
    assert r['identity']['pdf_official_doi_visually_verified']==(n in [165,168,184])
    assert r['selected_reading']['physical_pdf_pages']==[]
    assert r['body_reading_candidate_priority']=='not_selected'
    png=r['selected_reading']['viewed_page_images']['1'];b=check(png)
    assert b[:8]==b'\x89PNG\r\n\x1a\n' and min(struct.unpack('>II',b[16:24]))>=1000
    assert png['actually_viewed']
    sf=ROOT/r['source_file'];assert hashlib.sha256(sf.read_bytes()).hexdigest()==r['source_sha256']
    if n==167:
        soup=BeautifulSoup(sf.read_text(),'html.parser')
        abstract=' '.join(soup.select_one('p[style="white-space: pre-wrap;"]').get_text(' ',strip=True).split())
        assert len(soup.select('p[style="white-space: pre-wrap;"]'))==1
        assert norm(soup.select_one('meta[name="citation_title"]')['content'])==norm(r['title'])
        assert [m['content'] for m in soup.select('meta[name="citation_author"]')]==names
        assert 'Published elsewhere. Minor revision. ASPLOS 2025' in soup.get_text(' ',strip=True)
        v=BeautifulSoup(check(r['identity']['version_page']).decode(),'html.parser')
        updates=v.select('a[href^="/archive/2024/1862/"]')
        assert len(updates)==1 and updates[0].get_text()=='20241114:104207'
        assert '2024-11-14: received' in soup.get_text(' ',strip=True)
        cr=check_crossref(r['identity']['crossref'],r);assert cr['page']=='100-115' and count==15
        pdf_abstract=segment(first,'Zero-knowledge proof (ZKP) is a cryptographic primitive','second proof generation for the first time in this field.',True,True)
        assert norm(abstract)==norm(pdf_abstract)
    else:
        if n in [165,184]:
            text=segment(first,'Abstract','CCS Concepts:')
        elif n==168:
            text=segment(first,'Zero-knowledge proof (ZKP) is an important cryptographic','than previous ZKP accelerators using different protocols.',True,True)
        else:
            left=segment(first,'Abstract','Virtuoso’s accuracy benefits incur an average',False,True)
            right=segment(first,'simulation time overhead of only 20%,','Abstract',True,False)
            assert left.strip().startswith('The unprecedented growth')
            assert right.strip().endswith('https://github.com/CMU-SAFARI/Virtuoso.')
            assert '82% accuracy' in left and '79% accuracy' in left
            text=left+' '+right
            assert 'arXiv:2403.04635v2 [cs.AR] 27 Mar 2025' in first
            soup=BeautifulSoup(check(r['identity']['arxiv_metadata']).decode(),'html.parser')
            assert norm(soup.select_one('meta[name="citation_title"]')['content'])==norm(r['title'])
            aauthors=[]
            for m in soup.select('meta[name="citation_author"]'):
                last,given=m['content'].split(', ',1);aauthors.append(given+' '+last)
            assert aauthors==names
            assert '27 Mar 2025' in soup.select_one('.submission-history').get_text(' ',strip=True)
            assert '[v2]' in soup.select_one('.submission-history').get_text(' ',strip=True)
            html_abstract=soup.select_one('blockquote.abstract').get_text(' ',strip=True)
            assert 'VM this http URL' in html_abstract
            assert 'server-grade page fault latency' in html_abstract
            assert '82% accuracy' not in html_abstract and '79% accuracy' not in html_abstract
            cr=check_crossref(r['identity']['crossref'],r);assert cr['page']=='1400-1421' and count==22
        abstract=' '.join(text.split())
    if n==184:
        assert 'This is the author’s version of the work.' in first
        home=BeautifulSoup(check(r['identity']['author_home']).decode(),'html.parser')
        cards=home.select('.paper-card')
        card=next(c for c in cards if c.select_one('a[href="https://dl.acm.org/doi/'+r['doi']+'"]'))
        homeauthors=card.select_one('.paper-authors').get_text(' ',strip=True)
        assert homeauthors.index('Georgios Vavouliotis')<homeauthors.index('Dimitrios Chasapis')
        bsc=BeautifulSoup(check(r['identity']['author_bsc']).decode(),'html.parser')
        a=bsc.select_one('a[href="https://gvavou5.github.io/Documents/Vavouliotis_ASPLOS25.pdf"]')
        row=a.find_parent('li').get_text(' ',strip=True)
        assert norm(r['title']) in norm(row) and all(norm(name) in norm(row) for name in names)
        assert row.index('Dimitrios Chasapis')<row.index('Georgios Vavouliotis')
    assert abstract==r['abstract']
    assert hashlib.sha256(abstract.encode()).hexdigest()==r['abstract_sha256']
    assert check(r['abstract_text_file'])==(abstract+'\n').encode()
    identity_checks.append({'program_order':n,'doi':r['doi'],'authors_checked':len(names),'pdf_pages':count,'abstract_reextraction':'pass'})
assert pages==data['representative_pdf_pages']==89
assert data['representative_pdfs']==5

sources={s['id']:s for s in data['sources']};assert len(sources)==21
statuses={}
for s in sources.values():
    assert s['retrieved_at'] and s['url'] and s['final_url']
    statuses[s['status_code']]=statuses.get(s['status_code'],0)+1
    if s['file'].endswith('.pdf'):assert s['status_code']==200 and check(s).startswith(b'%PDF')
for logpath in P.glob('*-jobs.json.results.json'):
    for log in json.loads(logpath.read_text()):
        s=sources[log['id']]
        for k in ['url','final_url','status_code','bytes','sha256','retrieved_at']:assert s[k]==log[k]
        assert Path(s['file']).name==Path(log['file']).name
assert statuses=={200:15,429:3,403:3},statuses
assert sum(s['bytes']==0 for s in sources.values())==3

gap=data['gaps'][0];e=official[166]
assert e['doi']==gap['doi'] and e['title']==gap['title']
assert [a['given']+' '+a['family'] for a in e['author_metadata']]==gap['authors']
cr=check_crossref(gap['identity_source'],gap);assert not cr.get('abstract')
home=BeautifulSoup(check(gap['author_publication_page']).decode(),'html.parser')
row=next(li.get_text(' ',strip=True) for li in home.select('li') if gap['title'] in li.get_text(' ',strip=True))
assert all(name in row for name in gap['authors']) and '2025' in row
news=BeautifulSoup(check(gap['misleading_http_success']).decode(),'html.parser')
assert news.title.get_text().lower()=='error' and '你访问的主页不存在或没有上线发布' in news.get_text()
assert sources['166-author-news']['status_code']==200
failure=json.loads(check(gap['tool_failure']))
assert failure['url']=='https://doi.org/'+gap['doi']
assert '403' in str(failure['result']) and 'Failed to fetch' in str(failure['result'])
assert gap['full_abstract_read'] is False and gap['representative_pdf'] is None and gap['body_pages_read']==[]
identity_checks.append({'program_order':166,'doi':gap['doi'],'authors_checked':len(gap['authors']),'abstract_reextraction':'gap_not_counted'})

result={'status':'pass','file_proofs_checked':len(seen),'formal_identity_checks':identity_checks,
        'full_primary_abstracts_reextracted':5,'representative_pdfs':5,'representative_pdf_pages':89,
        'actual_viewed_first_page_images_verified':5,'selected_body_pages':0,'body_candidates':0,
        'http_responses':21,'http_statuses':statuses,'genuine_zero_byte_failed_responses':3,
        'additional_failed_web_open':1,'http200_error_pages_excluded':1,'unresolved_original_abstracts':[166],
        'version_limits':['167 IACR 20241114:104207 public15-page preprint; formal16-page version not read.','183 fixed arXiv v2 PDF used; malformed/different HTML abstract retained and excluded as canonical.','184 PDF explicitly author version; personal homepage co-first-author order differs from PDF/manifest/BSC.'],
        'verification_limits':'Offline source/identity/abstract re-extraction; no downloaded code executed. PNG/record checks cannot independently prove reading; actual five-page visual review recorded. No body reading counted.'}
(P/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
