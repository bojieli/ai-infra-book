from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

P=Path(__file__).resolve().parent
ROOT=P.parents[4]
manifest=json.loads((P.parent/'manifest.json').read_text())
entries={r['program_order']:r for r in manifest['papers']}

def proof(f):
    f=Path(f); b=f.read_bytes()
    return {'file':str(f.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def pdfinfo(stem):
    f=P/(stem+'.pdf')
    n=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(f)],text=True),re.M).group(1))
    return {**proof(f),'pages':n,'text':proof(P/(stem+'.txt')),'layout_text':proof(P/(stem+'.layout.txt')),'first_page_text':proof(P/(stem+'.first.txt'))}

sources=[]
for f in sorted(P.glob('*-jobs.json.results.json')):
    for row in json.loads(f.read_text()):
        row['file']=str((P/Path(row['file']).name).relative_to(ROOT));sources.append(row)

spec={
157:('157-arxiv-paper','2410.12749v1','可信内存池的 freshness 元数据开销可作背景；当前不选正文，不与 KV cache 更新混同。'),
159:('159-arxiv-paper','2407.12232v1','通用 OoO RTL 投机安全验证，与 LLM 推测解码无关；不选正文。'),
160:('160-institution-paper','EPFL publication-layout PDF','HLS dataflow 电路等价重写验证，不能直接当模型图融合实证；不选正文。'),
161:('161-author-paper','author publication-layout PDF','PMVerify 检查 NVM 程序 robustness；非分布式训练 checkpoint 或 persistent KV 验证；不选正文。'),
162:('162-funder-paper','NSF public-access manuscript, ASPLOS 2024 Volume 4','Vega 的老化测试在 RISC-V ALU/FPU 上评估；仅可靠性背景，不外推 GPU，不设正文候选。')
}
records=[]
for n,(stem,version,decision) in spec.items():
    e=entries[n]; authors=[a['given']+' '+a['family'] for a in e['author_metadata']]
    aliases={}
    if n==160:
        aliases={'Lana Josipovi?':'Lana Josipović'};authors=[aliases.get(a,a) for a in authors]
    h=None
    if n in [157,159]:
        f=P/f'{n}-arxiv.html';s=BeautifulSoup(f.read_text(),'html.parser');a=s.select_one('blockquote.abstract');a.select_one('.descriptor').decompose();abstract=a.get_text(' ',strip=True)
        extraction={'kind':'arxiv_html','selector':'blockquote.abstract','remove_selector':'.descriptor','normalization':'get_text(" ",strip=True); no paraphrase or punctuation repair'}
        source_url='https://arxiv.org/abs/'+version
        h=s.select_one('.submission-history').get_text(' ',strip=True)
    else:
        f=P/(stem+'.pdf');t=(P/(stem+'.first.txt')).read_text();source_url=next(s['url'] for s in sources if s['file']==str(f.relative_to(ROOT)))
        if n==160:
            start='Dataflow circuits have been studied';end='building formally verified dataflow HLS compilers.'
            startpos=t.index(start); endpos=t.index(end,startpos)+len(end);abstract=' '.join(t[startpos:endpos].split())
            extraction={'kind':'pdf_first_page','segments':[{'start':start,'end':end,'include_start':True,'include_end':True}], 'excluded':'Citation continuation after Abstract heading, before actual abstract first sentence; selection verified visually.'}
        elif n==161:
            abstract=' '.join(t.split('Abstract',1)[1].split('CCS Concepts:',1)[0].split())
            extraction={'kind':'pdf_first_page','segments':[{'start':'Abstract','end':'CCS Concepts:','include_start':False,'include_end':False}],'excluded':'No footer or intercolumn fragment within abstract.'}
        else:
            first=t.split('Abstract',1)[1].split('Permission to make digital',1)[0]
            second='our proposed techniques'+t.split('our proposed techniques',1)[1].split('ACM Reference Format:',1)[0]
            abstract=' '.join((first+' '+second).split())
            extraction={'kind':'pdf_first_page','segments':[{'start':'Abstract','end':'Permission to make digital','include_start':False,'include_end':False},{'start':'our proposed techniques','end':'ACM Reference Format:','include_start':True,'include_end':False}], 'excluded':'Copyright/license/venue/DOI footer between left-column abstract and right-column continuation; all abstract words preserved, image checked.'}
        extraction['command']='pdftotext -f 1 -l 1 input.pdf - (default; no -raw/-layout)'
        extraction['normalization']='Collapse whitespace only after explicit source-span extraction.'
    af=P/f'{n}-abstract.txt';af.write_text(abstract+'\n')
    r={'program_order':n,'doi':e['doi'],'title':e['title'],'authors':authors,
       'source_file':str(f.relative_to(ROOT)),'source_sha256':proof(f)['sha256'],'source_url':source_url,
       'extraction_kind':extraction['kind'],'extraction':extraction,'version':version,'history':h,
       'abstract':abstract,'abstract_sha256':hashlib.sha256(abstract.encode()).hexdigest(),'abstract_text_file':proof(af),
       'reading_status':'full_abstract_read','read_date':'2026-09-09',
       'identity':{'official_program_doi':e['doi'],'program_order':n,'presentation_year':2025,'formal_page_range':e.get('page'),
          'publisher_title':e.get('publisher_title',e['title']),'publisher_author_names':[a['given']+' '+a['family'] for a in e['author_metadata']],
          'author_aliases':aliases,'pdf_title_authors_visually_verified':True,'pdf_official_doi_visually_verified':n in [160,161,162]},
       'representative_pdf':pdfinfo(stem),
       'selected_reading':{'physical_pdf_pages':[],'scope':'Complete primary abstract and p1 identity only; no body reading. Mechanically archived full text is not read-body evidence.','page_text':{},'viewed_page_images':{'1':{**proof(P/(stem+'.p1.png')),'actually_viewed':True}}},
       'body_reading_candidate_priority':'not_selected','editorial_decision':decision,'version_notes':[]}
    if n==157:
        r['identity']['author_publication_page']=proof(P/'157-author-home.html')
        r['identity']['association']='Author homepage same publication row has formal DOI/title/three authors; arXiv title and all authors match. Homepage news explicitly records ASPLOS24 acceptance and ASPLOS25 delayed presentation.'
        r['version_notes']=['arXiv v1 2024-10-16, 16 pages; no formal DOI printed on PDF; formal ASPLOS2024 Volume4 identity and 2025 presentation kept distinct.']
    if n==159:
        r['identity']['crossref']=proof(P/'159-crossref.html')
        r['identity']['association']='Same title/all five authors as formal DOI metadata; arXiv comments explicitly state acceptance to ASPLOS2025. Preprint not asserted identical to formal version.'
        r['version_notes']=['arXiv v1 2024-07-17, 15 pages; official page range is 17 pages. EPFL formal PDF request HTTP429 retained, no formal PDF archived.']
    if n==160:r['version_notes']=['16-page publication-layout PDF carries formal DOI and all authors. Formal metadata surname Josipovi? mapped explicitly to PDF Josipović.']
    if n==161:r['version_notes']=['15-page author publication-layout PDF carries formal DOI and both authors.']
    if n==162:r['version_notes']=['16-page NSF archive PDF carries ASPLOS2024 Volume4 DOI and seven authors; 2025 program appearance does not change version year. Abstract crosses columns around copyright footer.']
    records.append(r)

e=entries[163]
gap={'program_order':163,'doi':e['doi'],'title':e['title'],'authors':[a['given']+' '+a['family'] for a in e['author_metadata']],
     'reading_status':'primary_abstract_unavailable','full_abstract_read':False,'representative_pdf':None,'body_pages_read':[],
     'identity_source':proof(P/'163-crossref.html'),'related_primary_context':proof(P/'163-meta-blog.html'),
     'tool_failure':proof(P/'163-publisher-web-open.json'),
     'reason':'Crossref has no abstract; ACM landing/PDF HTTP403 and web abstract open 403; Meta blog links paper but is not original abstract. Secondary copies/search snippets excluded.',
     'body_reading_candidate_priority':'undetermined_until_primary_abstract','editorial_decision':'保留原始摘要缺口，未按标题或转载摘要设正文候选。'}
out={'scope':'Assigned program orders 157,159–163; full abstracts/identity only, no body, shared index, outline or Git mutations.',
     'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':proof(P/'selection-snapshot.json'),
     'sources':sources,'records':records,'gaps':[gap],'new_full_abstracts':5,'representative_pdfs':5,'representative_pdf_pages':78,
     'selected_body_reading_records':0,'selected_body_physical_pages':0,'abstract_identity_pages_read_separately':5,'actual_rendered_pages_viewed':5,'body_reading_is_full_paper':False,
     'notes':proof(P/'READINGS.md'),'unresolved':['Hardware Sentinel original abstract/PDF unavailable in this bounded search.','Contract Shadow Logic formal 17-page version request failed; using explicit 15-page preprint.','Three Crossref queries and one institutional PDF returned 429; all failed bodies retained, including three genuine zero-byte bodies.']}
(P/'reading-records.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Packaged 5 abstracts, 5 PDFs, 78 pages, 0 body pages, 1 gap.')
