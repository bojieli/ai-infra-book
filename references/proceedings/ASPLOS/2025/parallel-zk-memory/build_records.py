from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

P=Path(__file__).resolve().parent
ROOT=P.parents[4]
entries={r['program_order']:r for r in json.loads((P.parent/'manifest.json').read_text())['papers']}

def proof(f):
    f=Path(f);b=f.read_bytes()
    return {'file':str(f.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def pdfinfo(stem):
    f=P/(stem+'.pdf')
    n=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(f)],text=True),re.M).group(1))
    return {**proof(f),'pages':n,'text':proof(P/(stem+'.txt')),'layout_text':proof(P/(stem+'.layout.txt')),'first_page_text':proof(P/(stem+'.first.txt'))}

def segment(t,start,end,include_start=False,include_end=False):
    pos=t.index(start);stop=t.index(end,pos+len(start))
    return t[pos if include_start else pos+len(start):stop+len(end) if include_end else stop]

sources=[]
for f in sorted(P.glob('*-jobs.json.results.json')):
    for row in json.loads(f.read_text()):
        row['file']=str((P/Path(row['file']).name).relative_to(ROOT));sources.append(row)

spec={
165:('165-author-paper','author publication-layout PDF, 17 pages','SGX MDU 控制流侧信道与防护，非 AI 性能主线；仅备查，不选正文。'),
167:('167-iacr-paper','IACR ePrint 2024/1862, PDF update 20241114:104207','ZKP 批量证明流水线仅作吞吐/延迟口径备查；verifiable ML proof throughput 不是模型推理速度，不选正文。'),
168:('168-author-paper','author publication-layout PDF, 17 pages','ZKP 内核统一硬件/映射设计背景；不把密码计算 systolic array 和不同协议收益当成神经网络加速，不选正文。'),
183:('183-arxiv-paper','arXiv:2403.04635v2, 2025-03-27','虚拟内存 OS/HW 仿真方法备查，VM 非 Agent sandbox；不把模拟准确度当业务性能提升，不选正文。'),
184:('184-author-paper','explicit author version, 18 pages','CPU 指令翻译与 L2 替换策略备查，不能外推 GPU KV cache 命中率或 LLM 服务吞吐，不选正文。')
}
records=[]
for n,(stem,version,decision) in spec.items():
    e=entries[n];authors=[a['given']+' '+a['family'] for a in e['author_metadata']]
    t=(P/(stem+'.first.txt')).read_text();h=None
    if n==167:
        f=P/'167-iacr.html';s=BeautifulSoup(f.read_text(),'html.parser')
        abstract=' '.join(s.select_one('p[style="white-space: pre-wrap;"]').get_text(' ',strip=True).split())
        extraction={'kind':'iacr_html','selector':'p[style="white-space: pre-wrap;"]','normalization':'get_text(" ",strip=True), collapse whitespace only; no word/punctuation repair','pdf_crosscheck_segments':[{'start':'Zero-knowledge proof (ZKP) is a cryptographic primitive','end':'second proof generation for the first time in this field.','include_start':True,'include_end':True}],'pdf_excluded':'Default extraction places right-column introduction between Abstract heading and actual left-column abstract; explicit beginning/end selects only the complete abstract.'}
        source_url='https://eprint.iacr.org/2024/1862'
        h='PDF update 20241114:104207 (only listed PDF version); received 2024-11-14, approved 2024-11-15.'
    else:
        f=P/(stem+'.pdf');source_url=next(s['url'] for s in sources if s['file']==str(f.relative_to(ROOT)))
        if n in [165,184]:
            spans=[{'start':'Abstract','end':'CCS Concepts:','include_start':False,'include_end':False}]
            excluded='No footer/intercolumn fragment inside selected abstract.'
        elif n==168:
            spans=[{'start':'Zero-knowledge proof (ZKP) is an important cryptographic','end':'than previous ZKP accelerators using different protocols.','include_start':True,'include_end':True}]
            excluded='ACM citation between Abstract heading and actual left-column abstract; title/first sentence anchors preserve full abstract.'
        else:
            spans=[{'start':'Abstract','end':'Virtuoso’s accuracy benefits incur an average','include_start':False,'include_end':True},{'start':'simulation time overhead of only 20%,','end':'Abstract','include_start':True,'include_end':False}]
            excluded='Default extraction puts right-column abstract continuation above Abstract heading. Reorder complete left-column abstract then right-column three-line continuation; exclude Introduction.'
            soup=BeautifulSoup((P/'183-arxiv.html').read_text(),'html.parser')
            h=soup.select_one('.submission-history').get_text(' ',strip=True)
        abstract=' '.join((' '.join(segment(t,**span) for span in spans)).split())
        extraction={'kind':'pdf_first_page','segments':spans,'excluded':excluded,'command':'pdftotext -f 1 -l 1 input.pdf - (default; no -raw/-layout)','normalization':'Collapse whitespace only after explicit source-span extraction; do not repair words.'}
    af=P/f'{n}-abstract.txt';af.write_text(abstract+'\n')
    r={'program_order':n,'doi':e['doi'],'title':e['title'],'authors':authors,
       'source_file':str(f.relative_to(ROOT)),'source_sha256':proof(f)['sha256'],'source_url':source_url,
       'extraction_kind':extraction['kind'],'extraction':extraction,'version':version,'history':h,
       'abstract':abstract,'abstract_sha256':hashlib.sha256(abstract.encode()).hexdigest(),'abstract_text_file':proof(af),
       'reading_status':'full_abstract_read','read_date':'2026-09-09',
       'identity':{'official_program_doi':e['doi'],'program_order':n,'presentation_year':2025,'formal_page_range':e.get('page'),
          'publisher_title':e.get('publisher_title',e['title']),'publisher_author_names':authors,'author_aliases':{},
          'pdf_title_authors_visually_verified':True,'pdf_official_doi_visually_verified':n in [165,168,184]},
       'representative_pdf':pdfinfo(stem),
       'selected_reading':{'physical_pdf_pages':[],'scope':'Complete primary abstract and p1 identity only; no body reading. Mechanically archived full text is not read-body evidence.','page_text':{},'viewed_page_images':{'1':{**proof(P/(stem+'.p1.png')),'actually_viewed':True}}},
       'body_reading_candidate_priority':'not_selected','editorial_decision':decision,'version_notes':[]}
    if n==165:r['version_notes']=['17-page author-hosted publication-layout PDF, exact title, all seven authors and formal DOI on first page; not asserted byte-identical to publisher download.']
    if n==167:
        r['identity']['crossref']=proof(P/'167-crossref.html');r['identity']['version_page']=proof(P/'167-iacr-versions.html')
        r['identity']['association']='IACR exact title/all six authors and ASPLOS2025 publication note match formal Crossref DOI; public PDF p1 exact title and all authors. Formal 16-page version not fetched.'
        r['version_notes']=['IACR version history lists only 20241114:104207. Archived 15-page public preprint differs in length from formal 16 pages; no formal PDF or body comparison claimed.','Canonical abstract from original IACR paragraph checked against complete left-column PDF abstract; no introduction text included.']
    if n==168:r['version_notes']=['17-page author-hosted publication-layout PDF carries formal DOI and both authors; no publisher byte-equivalence assertion.']
    if n==183:
        r['identity']['crossref']=proof(P/'183-crossref.html');r['identity']['arxiv_metadata']=proof(P/'183-arxiv.html')
        r['identity']['association']='Formal Crossref exact title and all ten authors match arXiv v2 PDF; PDF has arXiv version/date but no formal DOI; no exact formal-version equivalence asserted.'
        r['version_notes']=['arXiv v1 2024-03-07, v2 2025-03-27; fixed v2 URL, 22-page PDF.','arXiv HTML abstract differs from PDF, contains malformed auto-link VM this http URL and an incomplete MMU/page-fault sentence, and omits some PDF statements. HTML retained untouched; complete PDF abstract is canonical.','PDF abstract crosses from left-column end to right-column first three lines; both spans physically viewed.']
    if n==184:
        r['identity']['author_home']=proof(P/'184-author-home.html');r['identity']['author_bsc']=proof(P/'184-author-bsc.html')
        r['version_notes']=['PDF first page explicitly labels author’s version and states formal DOI; archived18 pages equal official page count, not a publisher byte-equivalence claim.','Author homepage reverses the two equal-contribution authors (Vavouliotis/Chasapis). PDF, manifest and BSC author page put Chasapis first; canonical formal order retained with source discrepancy recorded.']
    records.append(r)

e=entries[166]
gap={'program_order':166,'doi':e['doi'],'title':e['title'],'authors':[a['given']+' '+a['family'] for a in e['author_metadata']],
     'reading_status':'primary_abstract_unavailable','full_abstract_read':False,'representative_pdf':None,'body_pages_read':[],
     'identity_source':proof(P/'166-crossref.html'),'author_publication_page':proof(P/'166-author-home.html'),
     'misleading_http_success':proof(P/'166-author-news.html'),'tool_failure':proof(P/'166-publisher-web-open.json'),
     'reason':'Crossref has no abstract; ACM landing/PDF HTTP403 and web.run.open403; author homepage only publication metadata; SDU news HTTP200 is an error page. Search result text not accepted as full original abstract.',
     'body_reading_candidate_priority':'undetermined_until_primary_abstract','editorial_decision':'保留原始摘要缺口，未据搜索摘要或标题设正文候选。'}
out={'scope':'Assigned program orders 165–168,183–184; full abstracts/identity only, no body, shared index, outline or Git mutations.',
     'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':proof(P/'selection-snapshot.json'),
     'sources':sources,'records':records,'gaps':[gap],'new_full_abstracts':5,'representative_pdfs':5,'representative_pdf_pages':89,
     'selected_body_reading_records':0,'selected_body_physical_pages':0,'abstract_identity_pages_read_separately':5,'actual_rendered_pages_viewed':5,'body_reading_is_full_paper':False,
     'notes':proof(P/'READINGS.md'),'unresolved':['166 UniNTT original abstract/PDF unavailable in this bounded search.','BatchZK formal16-page version not read; public IACR15-page preprint explicit.','Virtuoso arXiv HTML abstract differs/is malformed; full v2 PDF abstract used, formal DOI linked by identity only.','184 co-first-author order differs on one personal homepage; formal/PDF/BSC order retained.','Three zero-byte Crossref429 responses and three ACM403 responses retained; SDU HTTP200 error not accepted as source.']}
(P/'reading-records.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Packaged5 abstracts,5 PDFs,89 pages,0 body pages,1 gap.')
