"""Build only this independent abstract packet, never shared records."""
from pathlib import Path
import json,hashlib,re,datetime,subprocess
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parent;ROOT=P.parents[4]
def sha(b):return hashlib.sha256(b).hexdigest()
def proof(f):
 f=Path(f);b=f.read_bytes();return {'file':str(f.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b)}
def dump(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def soup(name):return BeautifulSoup((P/name).read_bytes(),'html.parser')
def arxiv(n):
 s=soup(f'{n}-arxiv.html');a=s.select_one('blockquote.abstract');a.select_one('.descriptor').decompose();return a.get_text(' ',strip=True),s
M={r['program_order']:r for r in json.loads((ROOT/'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']}
sources=[]
for f in sorted(P.glob('sources-*.json.results.json')):
 for r in json.loads(f.read_text()):
  r['file']=str(Path(r['file']).relative_to(ROOT))
  if r['id']=='153-author':r['disposition']='excluded_wrong_person_Hui_Xu_not_Hong_Xu_HTTP200'
  elif r['status_code']!=200:r['disposition']='retained_failed_http_response'
  elif r['id']=='147-author':r['disposition']='author_html_meta_refresh_locator_followed_without_execution'
  elif 'tree' in r['id']:r['disposition']='static_public_author_repository_tree_metadata_only'
  else:r['disposition']='primary_source_or_locator_identity_checked_for_use'
  sources.append(r)
records=[]
for n in [146,147,148,149,153]:
 m=M[n];authors=[' '.join([a.get('given',''),a.get('family','')]).strip() for a in m['author_metadata']];extra={};versionnotes=[]
 if n in [146,148]:
  abstract,s=arxiv(n);src=P/f'{n}-arxiv.html';method='arxiv_html';description='blockquote.abstract; remove .descriptor; BeautifulSoup get_text(" ",strip=True).'
  version='arXiv:2405.05529v5' if n==146 else 'arXiv:2502.05338v1';extra={'history':s.select_one('.submission-history').get_text(' ',strip=True)}
  sourceurl='https://arxiv.org/abs/'+version.split(':')[1]
  versionnotes=['Explicit HTML/PDF v5 uses Yala; older Tomur locator not used. PDF p1 has no official DOI; arXiv Related DOI bridges formal identity.'] if n==146 else ['arXiv title excludes formal subtitle; TUM publication-layout PDF p1 contains full title/subtitle, all authors and official DOI. Author PDF not asserted byte-identical to arXiv v1 PDF.']
 elif n==147:
  src=P/'147-author-paper.pdf';first=(P/'147-author-paper.first.txt').read_text();abstract=' '.join(first.split('Abstract',1)[1].split('CCS Concepts:',1)[0].split());method='pdf_first_page';description='Default pdftotext -f 1 -l 1; text between first Abstract and following CCS Concepts:; collapse whitespace only. No footer removal, manual completion or -raw.'
  tree=json.loads((P/'147-author-tree.html').read_text());version='Author PDF in Git tree '+tree['sha'];sourceurl=next(x['url'] for x in sources if x['id']=='147-author-paper')
  extra={'git_identity':{'tree_file':proof(P/'147-author-tree.html'),'commit':tree['sha'],'path':'papers/gigaflow-asplos2025.pdf','blob_sha1':next(x['sha'] for x in tree['tree'] if x['path']=='papers/gigaflow-asplos2025.pdf')}}
  versionnotes=['ASPLOS title/authors/DOI present on p1. NSDI extended abstract, poster and earlier differently titled paper not used as full abstract.']
 elif n==149:
  src=P/'149-app-component.html';raw=src.read_text();obj=raw.split('ps=[{id:1,',1)[1].split('},{id:2,',1)[0];abstract=json.loads(re.search(r'abstract:("(?:[^"\\]|\\.)*")',obj).group(1));method='static_js_literal';description='Archived Astro App component; ps first record id:1; JSON-decode abstract string literal. Never execute downloaded JS.'
  version='Author project static component App.zCov1AVQ.js retrieved 2026-09-09; source SHA-256 fixed';sourceurl='https://einsum.org/_astro/App.zCov1AVQ.js'
  extra={'static_identity':{'website_file':proof(P/'149-project.html'),'component_path':'/_astro/App.zCov1AVQ.js','record_id':1,'array_name':'ps'}}
  versionnotes=['Full author-supplied abstract in same static record as title/all authors/formal DOI. No public representative paper PDF obtained; abstract not a poster or search snippet.']
 else:
  src=P/'153-institution.html';s=soup(src.name);abstract=s.select_one('.rendering_abstractportal .textblock > p').get_text(' ',strip=True);method='institution_html';description='CUHK institution HTML .rendering_abstractportal .textblock > p; get_text(" ",strip=True).'
  version='Formal Ayo abstract in institutional record; author-linked related preprint arXiv:2407.00326v3 titled Teola';sourceurl='https://research.cuhk.edu.hk/en/publications/towards-end-to-end-optimization-of-llm-based-applications-with-ay/'
  pre,ps=arxiv(153);af=P/'153-related-preprint-abstract.txt';af.write_text(pre+'\n')
  extra={'related_preprint_abstract':{'source':proof(P/'153-arxiv.html'),'version':'arXiv:2407.00326v3','title':ps.select_one('h1.title').get_text(' ',strip=True).removeprefix('Title: '),'history':ps.select_one('.submission-history').get_text(' ',strip=True),'abstract':pre,'abstract_sha256':sha(pre.encode()),'abstract_text_file':proof(af),'count_as_additional_paper':False},'author_bridge':proof(P/'153-first-author.html')}
  versionnotes=['CUHK original abstract uses Ayo; author publication row links formal DOI to arXiv 2407.00326. Current v3 dated 2025-03-31 uses Teola in title/abstract; PDF p1 has no formal DOI.','Related preprint archived with explicit title difference, not asserted identical to version of record and not counted as second abstract DOI. Wrong-person initial Hui Xu homepage excluded.']
 af=P/f'{n}-abstract.txt';af.write_text(abstract+'\n')
 decisions={146:'候选：用多资源争用与流量属性说明共置性能预测；仅摘要，勿泛化 BlueField-2 实验。',147:'候选：用子路径共享说明有限 NIC 缓存的容量与复用取舍；命中率和覆盖率不等于应用加速。',148:'已筛选，暂不新增书中候选：Byzantine 信任架构与当前 AI 工作负载主线直接关系弱。',149:'候选：用全局张量布局说明局部优化的局限；摘要评测是 Arm/x86 CPU，不能写成 GPU 结果。',153:'候选：细粒度任务单元暴露跨模块流水与并行；最高加速数字不泛化到任意 Agent 应用。'}
 rec={'program_order':n,'doi':m['doi'],'title':m['title'],'authors':authors,'source_file':str(src.relative_to(ROOT)),'source_sha256':sha(src.read_bytes()),'source_url':sourceurl,'extraction_kind':method,'extraction':description,'version':version,'abstract':abstract,'abstract_sha256':sha(abstract.encode()),'abstract_text_file':proof(af),'reading_status':'full_abstract_read','read_date':datetime.date.today().isoformat(),'identity':{'official_program_doi':m['doi'],'publisher_title':m['publisher_title'],'publisher_author_names':authors,'pdf_title_authors_visually_verified':n!=149,'pdf_official_doi_visually_verified':n in [147,148]},'representative_pdf':None,'selected_reading':{'physical_pdf_pages':[],'scope':'Full primary abstract only; PDF p1 title/authors/identity if present. No body section read. Full text extracted mechanically for archive and verification only.','page_text':{},'viewed_page_images':{}},'version_notes':versionnotes,'editorial_decision':decisions[n],**extra}
 names={146:'146-arxiv-v5-paper',147:'147-author-paper',148:'148-author-pdf',153:'153-arxiv-v3-paper'}
 if n in names:
  f=P/(names[n]+'.pdf');pages=int(subprocess.check_output(['pdfinfo',str(f)],text=True).split('Pages:')[1].splitlines()[0])
  rec['representative_pdf']={**proof(f),'pages':pages,'text':proof(f.with_suffix('.txt')),'layout_text':proof(f.with_suffix('.layout.txt')),'first_page_text':proof(f.with_suffix('.first.txt')),'version_relation':'author-linked related renamed preprint; not asserted identical to formal Ayo paper' if n==153 else 'primary author/institution paper version identified in notes'}
  rec['selected_reading']['viewed_page_images']={'1':{**proof(f.with_suffix('.p1.png')),'actually_viewed':True}}
 records.append(rec)
m=M[150]
gap={'program_order':150,'doi':m['doi'],'title':m['title'],'authors':[' '.join([a.get('given',''),a.get('family','')]).strip() for a in m['author_metadata']],'abstract_read':False,'representative_pdf':None,'selected_reading':None,'reading_status':'primary_identity_only_abstract_gap','candidate_reason':'编译与分块依赖主题有关，先定位一手摘要；不从题名推测具体方法或结果。','gap_reason':'Author #BlockDepend has formal title/authors/DOI and ACM/slides links but no abstract; Crossref message.abstract absent; ACM PDF 403; public author tree has presentation but no identified paper PDF. Slides and secondary summaries not substituted.','identity_sources':[proof(P/'150-author-pubs.html'),proof(P/'150-crossref.html'),proof(P/'150-author-tree.html')],'failed_sources':[proof(P/'150-acm.html')]}
x={'scope':'Bounded six missing abstract candidates; five full primary abstracts, one explicit gap; no body reading, no outline/index/Git edits.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':proof(P/'selection-snapshot.json'),'sources':sources,'records':records,'gaps':[gap],'software_sources':[],'new_full_abstracts':5,'representative_pdfs':4,'representative_pdf_pages':65,'selected_body_reading_records':0,'selected_body_physical_pages':0,'abstract_identity_pages_read_separately':4,'actual_rendered_pages_viewed':4,'body_reading_is_full_paper':False,'notes':proof(P/'READINGS.md'),'handoff':proof(P/'HANDOFF.md'),'search_attempts':proof(P/'search-attempts.json'),'unresolved':['150 has no primary complete abstract in bounded search.','149 no representative paper PDF obtained.','153 related preprint changed name to Teola; do not equate with formal Ayo text.','All body-level evidence and present framework adoption left unread/unverified.']}
dump('reading-records.json',x);print('Built',len(records),'abstracts;',sum(r['representative_pdf']['pages'] for r in records if r['representative_pdf']),'PDF pages;',len(sources),'responses')
