from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,datetime,re,subprocess,unicodedata
p=Path('/tmp/ai-infra-parallel-asplos');repo=Path('/Users/boj/book/ai-infra-book');m={x['program_order']:x for x in json.loads((repo/'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']}
def sha(b):return hashlib.sha256(b).hexdigest()
def proof(f):
 f=Path(f);b=f.read_bytes();return {'file':str(f),'bytes':len(b),'sha256':sha(b)}
sources=sum((json.loads(x.read_text()) for x in sorted(p.glob('jobs*.json.results.json'))),[])
for x in sources:x['id']='asplos25-parallel-'+x['id']
src={x['file']:x for x in sources}
htmls={77:'paper-077-ibm',78:'paper-078-arxiv',80:'paper-080-arxiv',84:'paper-084-author',85:'paper-085-princeton',86:'paper-086-edinburgh',89:'paper-089-author-detail',90:'paper-090-arxiv'}
decisions={
77:('候选待读','7、10、11','KVM、SR-IOV 与 GPU Direct RoCE 的生产训练路径适合作为虚拟化边界案例；须读正文核对网络拓扑、模型切分和理想吞吐分母，摘要中的约 80% 不能当作 MFU。'),
78:('候选待读','1、4、5、13','NeuSight 将硬件约束与 tile 级学习预测组合，适合补充纸笔下界何时需要实测校准；先核对训练样本、GPU 与库版本，再决定是否采用，摘要误差不是通用精度保证。'),
80:('候选待读','5、6、10','PartIR 把模型与分片策略分开并允许渐进组合，适合连接矩阵切分、通信代价与编译器；须核对论文 API、公开实现和运行时集成之间的差距。'),
81:('候选待读','4、5、13','算子级 DVFS 与性能／功耗建模直接关联资源瓶颈，候选用于说明降频是否延长关键路径；仅摘要可知针对昇腾的毫秒级调频，不能推广成任意 GPU 能力或整机能耗结论。'),
82:('不采用','—','面向 HDC 分类器的统计早停，模型、误差结构与本书 Transformer 推理主线不同；不作为推测解码或 reasoning 提前停止的直接依据。'),
83:('不采用','—','BitSpec 针对小型处理器整数变量的位宽推测与纠错执行，不能等同 LLM 权重量化；保留筛选记录，避免编译章节扩成通用嵌入式处理器综述。'),
84:('不采用','—','研究 CPU 硬件预取器侧信道，超出本书 Agent 沙箱容量、启动和调度主线；不以此补充攻击实现细节。'),
85:('不采用','—','Skia 面向服务器 CPU 前端和分支目标缓冲，不直接解释 AI 算子或模型服务的关键瓶颈；保留记录，不增加通用 CPU 微架构支线。'),
86:('不采用','—','服务器指令预取与通用代码工作集优化，缺少本书模型资源计算的直接落点；不因涉及数据中心就加入 AI 网络或推理章节。'),
88:('背景备查','6、9、13','可用于核对 CXL.cache 一致性语义与协议证明边界，不能当作 CXL.mem 内存池带宽或 KV 共享性能的证据；无需展开数万条证明。'),
89:('背景备查','6、9、13','事务处理的选择性一致性说明一致性语义也有代价；目前不能把 OLTP 吞吐提升迁移为 KV 池收益，需独立核对 AI 对象的读写及可见性要求。'),
90:('背景备查','9、13','字节／块双接口、主机及设备缓存协调可供多级缓存写放大背景参考；ByteFS 的可编程 SSD 与仿真结果不等于真实 CXL KV 池实现。')}
records=[]
for n in [77,78,80,81,82,83,84,85,86,88,89,90]:
 x=m[n];identity={'official_program_doi':x['doi'],'publisher_title':x['title'],'publisher_author_names':[' '.join([a.get('given',''),a['family']]).strip() for a in x['author_metadata']],'scope':'Only complete abstract and title/author/version identity checked. No selected body-reading credit; no performance reproduction.'}
 if n in htmls:
  f=p/(htmls[n]+'.html');s=BeautifulSoup(f.read_bytes(),'html.parser')
  if 'arxiv' in f.name:
   e=s.select_one('blockquote.abstract');e.select_one('.descriptor').extract();abstract=e.get_text(' ',strip=True);extract='HTML blockquote.abstract without descriptor';title=s.find('meta',attrs={'name':'citation_title'})['content'];authors=[a['content'] for a in s.find_all('meta',attrs={'name':'citation_author'})];history=s.select_one('div.submission-history').get_text(' ',strip=True)
  elif n==89:
   abstract=s.select_one('section.page__content > p').get_text(' ',strip=True);extract='HTML section.page__content first p; subsequent ACM DOI link and BibTeX prove identity';title=s.select_one('h1.page__title').get_text(' ',strip=True);authors=identity['publisher_author_names'];history='Author page publication year 2025; site footer last updated 2026-04-08; not paper revision date.'
  else:
   h=next(h for h in s.find_all(['h2','h3']) if h.get_text(strip=True)=='Abstract');abstract=h.find_next_sibling().get_text(' ',strip=True);extract='HTML sibling after Abstract heading; contains full abstract only';cm=s.find('meta',attrs={'name':'citation_title'});title=cm['content'] if cm else s.select_one('h1').get_text(' ',strip=True);authors=[a['content'] for a in s.find_all('meta',attrs={'name':'citation_author'})] or identity['publisher_author_names'];history='Author/institution publication page retrieved 2026-09-09; paper version not inferred from page retrieval date.'
  identity['title_normalized_equal']=re.sub(r'[^a-z0-9]','',title.lower())==re.sub(r'[^a-z0-9]','',x['title'].lower())
  identity['author_family_set_matches_publisher']=True
  identity['author_check']='Checked HTML citation/BibTeX names; where missing, checked linked PDF title page against publisher list.'
  if n==77:identity['title_variant_note']='IBM title inserts "and" before RoCE; exact DOI and all 25 author names match publisher.'
 else:
  f=p/f'paper-{n:03}.pdf';raw=(p/f'paper-{n:03}.page1.txt').read_text();abstract=raw.split('Abstract\n',1)[1].split('CCS Concepts:',1)[0]
  if n==81:abstract=re.sub(r'∗corresponding authors\nPermission.*?https://doi.org/10.1145/3669940.3707231\n','',abstract,flags=re.S)
  abstract=abstract.strip();extract='pdftotext -f 1 -l 1 -raw: Abstract through before CCS Concepts; preserve extraction line breaks; rendering checked.'
  if n==81:extract+=' Remove inserted corresponding-author footnote and permission/DOI footer between left/right abstract columns.'
  title=x['title'];authors=identity['publisher_author_names'];history='Author/institution-hosted PDF with exact ACM DOI on page 1; do not assume unrecorded revision date.';identity.update(title_normalized_equal=True,author_family_set_matches_publisher=True,pdf_title_author_doi_visually_verified=True)
 source=src[str(f)];decision,ch,why=decisions[n];af=p/f'paper-{n:03}-abstract.txt';af.write_text(abstract+'\n')
 rec={'program_order':n,'source_id':source['id'],'source_file':str(f),'source_sha256':source['sha256'],'extraction':extract,'title':title,'authors':authors,'history':history,'abstract':abstract,'abstract_sha256':sha(abstract.encode()),'reading_status':'full_abstract_read','read_date':'2026-09-09','identity':identity,'abstract_text_file':proof(af),'screening':{'decision':decision,'chapters':ch,'rationale':why},'body_reading_status':'not_read','version_notes':[]}
 if n in [78,80]:rec['version_notes'].append('arXiv HTML abstract and latest linked PDF abstract are not text-identical; preserve HTML and PDF independently. This abstract record is explicitly the HTML text.')
 if n==80:rec['version_notes'].append('arXiv v4 2024-11-24 has 36 physical pages, rather than the publisher 17-page span; exact DOI appears in arXiv HTML metadata, not the preprint PDF. PDF author list includes Daniel Belov (older v2 search locator did not); old v2 was not adopted.')
 if n==83:rec['version_notes'].append('Author PDF and Northwestern institutional PDF both state 9.9% average energy reduction in their abstracts; bytes differ (institution copy adds ACM pagination/badge/watermark). Only one representative PDF counted. Zenodo search locator advertises a different 14.4% value; that search text is not adopted as a screened source.')
 if n==86:rec['version_notes'].append('17 physical PDF pages = institutional cover + 16-page publisher paper. Paper abstract/title at physical p2, printed p529; cover at p1 explicitly identifies version of record.')
 if n==89:rec['version_notes'].append('The author webpage gives the formal CTXNL title, all 9 authors and exact ACM DOI link. Related arXiv 2502.11046v2 uses title Enabling Efficient Transaction Processing on CXL-Based Memory Sharing; HTML metadata lists 8 authors while PDF lists all 9 including Yijin Guan. The related PDF lacks the formal DOI and is retained separately, not counted as the formal-paper representative PDF; abstract credit comes only from author webpage.')
 if n==90:rec['version_notes'].append('arXiv HTML preserves literal TeX macro \\pname{} and math delimiters; PDF renders ByteFS and multiplication signs. HTML and PDF retained separately; exact formal DOI appears on PDF p1.')
 if n==85:rec['version_notes'].append('PDF text extraction has ligature/glyph errors (e.g. Bu!er, unidenti"ed and arrow in place of approximate sign); paper p1 rendered and checked. Canonical abstract comes from Princeton institution HTML, avoiding corrupted glyphs.')
 if n in [77,89]:rec['full_text_gap']='Publisher PDF returned HTTP 403; retained error bytes. No formal representative PDF counted.'
 else:
  pf=p/f'paper-{n:03}.pdf';t=pf.with_suffix('.txt');info=subprocess.check_output(['pdfinfo',str(pf)],text=True);count=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1));pdfproof=proof(pf);pdfproof.update(pages=count,text=proof(t),first_page_text=proof(pf.with_suffix('.page1.txt')),reading_scope='Abstract and title/author/version identity only; body not read.',abstract_physical_page=2 if n==86 else 1)
  view=p/'views'/f'paper-{n:03}-p{2 if n==86 else 1:02}.png';pdfproof['view']=proof(view);pdfproof['view']['actually_viewed']=True;pdfproof['identity_doi_source']='arXiv HTML citation_doi' if n==80 else 'PDF title/abstract page DOI';rec['representative_pdf']=pdfproof
 records.append(rec)
related=[]
for name,kind in [('paper-083-institution','alternate_of_83_not_extra_paper'),('paper-089-preprint','related_version_identity_gap_not_formal_representative')]:
 f=p/(name+'.pdf');d=proof(f);d.update(kind=kind,pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(f)],text=True),re.M).group(1)),text=proof(f.with_suffix('.txt')),first_page_text=proof(f.with_suffix('.page1.txt')),view=proof(p/'views'/(name+'-p01.png')),reading_scope='Only title/authors/abstract physical p1; no body reading');d['view']['actually_viewed']=True;related.append(d)
bundle={'scope':'ASPLOS 2025 independent parallel screening program orders 77–90; merge serially only after root review. No repository edits were made.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_manifest_sha256':sha((repo/'references/proceedings/ASPLOS/2025/manifest.json').read_bytes()),'requested_orders':list(range(77,91)),'already_screened_skipped':[79,87],'new_full_abstracts':len(records),'new_representative_pdfs':sum('representative_pdf'in x for x in records),'new_representative_pdf_pages':sum(x['representative_pdf']['pages'] for x in records if 'representative_pdf'in x),'selected_body_readings_added':0,'actual_rendered_pages_viewed':12,'sources':sources,'records':records,'alternate_or_related_pdfs':related,'integration_notes':['Source paths are absolute /tmp paths; root may remap to repository archive while preserving bytes/hashes.','12 abstract records count separately from 10 representative PDFs; related CtXnL preprint and alternate BitSpec PDF are not added to representative counts.','Do not retroactively claim full-paper or selected-body reading from these abstract and identity checks.','Preserve failed ACM responses for 77,85,89 even though a later primary PDF source succeeded for 85.','Screening recommendations are editorial judgments from full abstracts, not validation of numerical headline performance.']}
(p/'merge-ready.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:bundle[k] for k in ['new_full_abstracts','new_representative_pdfs','new_representative_pdf_pages','selected_body_readings_added','actual_rendered_pages_viewed']},ensure_ascii=False));print('sources',len(sources))
