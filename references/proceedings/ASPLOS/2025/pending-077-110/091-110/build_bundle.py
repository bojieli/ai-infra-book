from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,datetime,re,subprocess
p=Path('/tmp/ai-infra-parallel-asplos-91-110');repo=Path('/Users/boj/book/ai-infra-book');manifest=repo/'references/proceedings/ASPLOS/2025/manifest.json'
m={x['program_order']:x for x in json.loads(manifest.read_text())['papers']}
def sha(b):return hashlib.sha256(b).hexdigest()
def proof(f):
 f=Path(f);b=f.read_bytes();return {'file':str(f),'bytes':len(b),'sha256':sha(b)}
def soup(n):return BeautifulSoup((p/(n+'.html')).read_bytes(),'html.parser')
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
sources=sum((json.loads(x.read_text()) for x in sorted(p.glob('jobs*.json.results.json'))),[])
for x in sources:x['id']='asplos25-parallel-'+x['id']
src={x['file']:x for x in sources}
htmls={91:'paper-091-author',93:'paper-093-arxiv',96:'paper-096-arxiv',97:'paper-097-arxiv',98:'paper-098-author',101:'paper-101-arxiv',102:'paper-102-institution',104:'paper-104-institution',107:'paper-107-arxiv'}
decisions={
91:('候选待读','6、9、13','M5 将页迁移的计数和跟踪下沉到 CXL 控制器，适合追问搬一个 4KB 页实际搬了多少冷数据、识别热页本身花多少代价；需正文核对平台与迁移策略，不能把平均 14% 提升写成 KV 内存池收益。'),
92:('候选待读','1、6、9、13','Melody 对真实 CXL 设备、CPU、负载和延迟档位做系统测量，适合校准纸笔模型的访存延迟与带宽；140–410ns 是所测配置范围，不能当统一 CXL 常数，需正文核对尾延迟、MLP 与预取器的影响。'),
93:('候选待读','5、8、9','MoE-Lightning 的分层 Roofline 和 CPU/GPU/I/O 流水适合贯穿算容量、传输量与 batch 吞吐的案例；摘要明确为批处理推理，不能将单张 T4 的最高吞吐提升解释成 batch=1 的交互速度或总成本优势。'),
96:('候选待读','5、8、9','Klotski 直接说明 batch 增大还会激活更多专家、增加 I/O，适合反复推算计算覆盖搬运的条件；后续需读约束规划与预取命中率、真实硬件和基线，85.12 倍只是摘要特定实验上限。'),
97:('候选待读','10','MoC-System 的部分专家检查点、分片和两级异步持久化适合连接 MoE 总参数量与恢复成本；必须读正文确认未保存专家如何恢复、质量代价和状态一致性，不能把 comparable accuracy 写成精确恢复或 router replay。'),
98:('候选待读','5、7、10','Concerto 将通信拆解与调度从具体并行策略中分离，适合说明算完通信量之后还要看关键路径和可重叠窗口；作者摘要只给框架性结论，未获得 PDF，暂不采信求解器成本或 Megatron/DeepSpeed 集成成熟度。'),
99:('背景备查','11','SING 提供真实校园共享 GPU 集群的运营案例，可补充调度效率、公平性与有限运维人力之间的取舍；不直接照搬四层架构作为全书主线，也不将其等同已有生产 LLM 服务系统。'),
100:('候选待读','10','PCcheck 适合用 checkpoint 数据量、持久化带宽、故障频率推算训练有效产出，连接单机和分布式训练；每 10 步约 3% 开销需正文核对模型、存储和一致性范围，不作为通用常数。'),
101:('候选待读','5、11','Tally 将 GPU 共享落到 thread-block 级干扰控制，适合串起利用率与推理尾延迟；需正文核对支持的 kernel、设备、拦截机制和优先级前提，不能把摘要兼容性描述视为任意 CUDA Graph/协作 kernel 的保证。'),
102:('候选待读','4、11','Balance 是具体 CPU 推荐推理的调度案例：embedding table 的核分配、MLP 与 chiplet 负载不均衡可用带宽约束解释；与 LLM CPU/GPU 协同有方法联系，但不能直接套用其 DLRM 的提速数。'),
103:('不采用','—','MopFuzzer 聚焦 JVM 优化阶段交互的正确性模糊测试，缺少 AI 算子 profile 与自动调优的直接证据；保留筛选记录，不扩展成通用 JVM 编译器专题。'),
104:('不采用','—','利用 CFG 语法分解加速不允许 live-range splitting 的精确寄存器分配，偏向通用算法复杂度；不等同 GPU tile 的 occupancy 优化，也不为本书增加寄存器分配理论推导。'),
105:('不采用','—','SURI 研究现代 x86-64 二进制重汇编与符号化，和模型容量、带宽、通信及 Agent 环境调度没有直接量化联系，不补写二进制重写支线。'),
106:('背景备查','5','SmoothE 的可微 e-graph 提取可作为优化搜索空间与代价函数之间关系的背景；可微成本函数并不自动等于真实 kernel 时延，也不能代替 profiling feedback，暂不作为主实验。'),
107:('候选待读','5','Exo 2 以可信变换原语构建可扩展调度库，适合说明为何手工优化工作量需要被程序化复用；后续可与 TVM、polyhedral 和 Agent 优化对照，但需正文核对三平台与 80 多 kernel 的范围。'),
108:('不采用','—','Manta 面向 stripped binaries 的类型推断与漏洞检测，超出 AI Infra 的建模主线；机构 HTML 和作者 PDF 存在摘要数值差异，分开保留，不混合成一个性能结论。'),
109:('不采用','—','SURW 的均匀性针对并发程序测试的交错采样，不能解释模型请求公平调度或 EP 的负载均衡；保留筛选记录，不扩成通用并发验证专题。'),
110:('不采用','—','TaOPT 通过移动应用 UI 子空间划分提高并行测试覆盖效率；它不是大模型 computer-use 的截图传输或推理回合优化，不能因 UI 和并行关键词加入端边云案例。')}
records=[]
for n in [i for i in range(91,111) if i not in [94,95]]:
 x=m[n];officialauthors=[' '.join([a.get('given',''),a['family']]).strip() for a in x['author_metadata']]
 ident={'official_program_doi':x['doi'],'publisher_title':x['title'],'publisher_author_names':officialauthors,'scope':'Only complete abstract and title/author/version identity checked. No selected body-reading credit; no performance reproduction.'}
 history='Author-hosted PDF; exact title, complete author list and ACM DOI visually checked on physical page 1. No unrecorded revision date inferred.'
 if n in htmls:
  f=p/(htmls[n]+'.html');s=soup(htmls[n]);authors=officialauthors;title=x['title']
  if 'arxiv' in htmls[n]:
   e=s.select_one('blockquote.abstract');e.select_one('.descriptor').extract();abstract=e.get_text(' ',strip=True);extract='HTML blockquote.abstract; remove nested .descriptor, then get_text(" ", strip=True).';title=s.find('meta',attrs={'name':'citation_title'})['content'];authors=[a['content'] for a in s.find_all('meta',attrs={'name':'citation_author'})];history=s.select_one('div.submission-history').get_text(' ',strip=True)
  elif n in [102,104]:
   e=s.select_one('div.textblock');abstract=e.get_text(' ',strip=True);extract='HTML first div.textblock; get_text(" ", strip=True). Original inner HTML also preserved for superscripts and mathematical typography.';title=s.find('meta',attrs={'name':'citation_title'})['content'];authors=[a['content'] for a in s.find_all('meta',attrs={'name':'citation_author'})];ident['primary_html_doi']=s.find('meta',attrs={'name':'citation_doi'})['content'];(p/f'paper-{n:03}-abstract-fragment.html').write_text(str(e));history='Institution publication page; citation_title/citation_author/citation_doi checked against official manifest. Retrieval date is not paper revision date.'
  elif n==91:
   e=s.select_one('.pub-abstract,.article-style,.textblock');abstract=e.get_text(' ',strip=True);extract='HTML first match of .pub-abstract,.article-style,.textblock; get_text(" ", strip=True). PDF page 1 independently checked; HTML retains its tiered-Memory system wording.'
  elif n==98:
   h=next(t.parent for t in s.find_all(string=True) if t.strip()=='Abstract');e=h.find_next_sibling('div');abstract=e.get_text(' ',strip=True);extract='Find text node whose stripped text is Abstract; use parent div next sibling div, get_text(" ", strip=True).';history='Author Ziming Liu page displays ASPLOS 2025 and last updated 2024-10-27; linked cite.bib supplies all 11 authors but DOI/URL fields are empty, so date is not treated as publication date.';ident['author_list_source']=proof(p/'paper-098-cite.html');ident['doi_proof_boundary']='Author page and linked BibTeX match exact title and all 11 author names to formal manifest. Author DOI field empty; no independent DOI printed in this primary HTML, and publisher PDF returned 403.'
  ident['title_normalized_equal']=norm(title)==norm(x['title']);ident['author_check']='Complete source author list checked against formal manifest; spelling variants recorded below.'
 else:
  name='paper-105-alternate' if n==105 else f'paper-{n:03}';f=p/(name+'.pdf');raw=(p/(name+'.first.txt')).read_text();title=x['title'];authors=officialauthors
  a=raw.split('Abstract\n',1)[1]
  if n==92:abstract=a.split('\n\nCXL + multi-hops',1)[0];extract='pdftotext default reading order, first physical page: substring after Abstract\\n and before \\n\\nCXL + multi-hops (next-column figure label).'
  elif n in [99,106]:abstract=a.split('Permission to make digital',1)[0];extract='pdftotext default reading order, p1: substring after Abstract\\n and before Permission to make digital (footer after complete left-column abstract).'
  elif n==100:abstract=a.split('\n\nFigure 1.',1)[0];extract='pdftotext default reading order, p1: substring after Abstract\\n and before \\n\\nFigure 1. (right-column figure caption).'
  elif n==103:abstract=a.split('∗ National Engineering Research Center',1)[0]+a.split('optimization interactions. Subsequently,',1)[0][-0:] if False else a.split('∗ National Engineering Research Center',1)[0]+'optimization interactions. Subsequently,'+a.split('optimization interactions. Subsequently,',1)[1].split('Keywords:',1)[0];extract='pdftotext default reading order, p1: join Abstract\\n through before ∗ National Engineering Research Center, then optimization interactions. Subsequently, through before Keywords:. Removes affiliations, corresponding-author footnotes, copyright/DOI footer and stray Hai Jin affiliation between two abstract columns.'
  elif n==108:abstract=a.split('ACM Reference Format:',1)[0];extract='pdftotext default reading order, p1: substring after Abstract\\n and before ACM Reference Format:.'
  elif n==110:abstract=a.split('Permission to make digital',1)[0]+'the baseline on average.'+a.split('the baseline on average.',1)[1].split('CCS Concepts:',1)[0];extract='pdftotext default reading order, p1: join Abstract\\n through before Permission to make digital, then the baseline on average. through before CCS Concepts:. Removes copyright/ISBN/DOI footer interrupting left-to-right abstract flow.'
  else:abstract=a.split('CCS Concepts:',1)[0];extract='pdftotext default reading order, p1: substring after Abstract\\n and before CCS Concepts:.'
  abstract=abstract.strip();ident.update(title_normalized_equal=True,author_family_set_matches_publisher=True,pdf_title_author_doi_visually_verified=True)
 source=src[str(f)];abstract=abstract.strip();af=p/f'paper-{n:03}-abstract.txt';af.write_text(abstract+'\n');decision,ch,why=decisions[n]
 rec={'program_order':n,'source_id':source['id'],'source_file':str(f),'source_sha256':source['sha256'],'extraction':extract,'title':title,'authors':authors,'history':history,'abstract':abstract,'abstract_sha256':sha(abstract.encode()),'reading_status':'full_abstract_read','read_date':'2026-09-09','identity':ident,'abstract_text_file':proof(af),'screening':{'decision':decision,'chapters':ch,'rationale':why},'body_reading_status':'not_read','version_notes':[]}
 if n in [102,104]:rec['abstract_html_fragment']=proof(p/f'paper-{n:03}-abstract-fragment.html')
 if n in [98,102,104]:rec['full_text_gap']='ACM PDF returned HTTP 403 and response bytes are retained. Primary author/institution full abstract read; no representative PDF counted.'
 else:
  name='paper-105-alternate' if n==105 else f'paper-{n:03}';pf=p/(name+'.pdf');count=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(pf)],text=True,stderr=subprocess.DEVNULL),re.M).group(1));pdfproof=proof(pf);pdfproof.update(pages=count,text=proof(pf.with_suffix('.txt')),first_page_text=proof(pf.with_suffix('.first.txt')),reading_scope='Abstract and title/author/version identity only; body not read.',abstract_physical_page=1,view=proof(pf.with_suffix('.p1.png')),identity_doi_source='Official manifest DOI matched by exact title and all author names; DOI absent in preprint PDF and arXiv HTML' if n in [93,96] else 'PDF physical p1 printed ACM DOI');pdfproof['view']['actually_viewed']=True;rec['representative_pdf']=pdfproof
  ident['pdf_title_author_visually_checked']=True
 if n==91:rec['version_notes'].append('HTML says past tiered-Memory system; PDF says past tiered-memory systems. Canonical record preserves HTML verbatim after whitespace extraction. Default PDF extraction places right-column continuation before left-column beginning; do not use its naive Abstract-to-CCS slice. Complete two-column abstract visually read.')
 if n in [93,96]:rec['version_notes'].append('Author-submitted arXiv v1 preprint has exact formal title and complete matching author list, but no ACM DOI in PDF or arXiv citation metadata. Representative is explicitly an author preprint, not a publisher version of record.')
 if n==97:rec['version_notes'].append('arXiv v3 2025-04-09 PDF prints exact DOI and all three authors. Earlier v1/v2 were not downloaded or separately counted.')
 if n==98:rec['version_notes'].append('Author page rendered author header omits Wei Lin and Yang You, but its linked cite.bib contains all 11 formal authors and the full abstract. BibTeX DOI and URL blank, ISBN all zeros; these placeholders are not adopted as metadata.')
 if n==99:rec['version_notes'].append('Archived tacc-asplos25.pdf is the formal SING paper with matching 2025 title, all nine authors and DOI. Older TACC manuscript sharing historical arXiv 2110.01556 is not substituted or counted.')
 if n==101:rec['version_notes'].append('arXiv v3 2025-02-28 prints formal DOI. HTML abstract retains literal TeX emphasis and math delimiters; PDF renders percentages. Both preserved separately.')
 if n in [103,108]:rec['version_notes'].append('PDF imprint/reference says ASPLOS 2024 Volume 4 while this DOI appears in ASPLOS 2025 official program. Preserve both program membership and original imprint; do not relabel the source or infer a conflicting paper identity from year alone.')
 if n==104:
  rec['version_notes'].append('Institution metadata calls the third author Hitarth SINGH; formal manifest and first-author homepage use S. Hitarth. Exact DOI/title match, and author homepage supplies X. Cai, A.K. Goharshady, S. Hitarth, C.K. Lam. Preserve the institutional naming variant, not an exact author-string match. Institution abstract math contains typography/lost symbol issues; preserve raw div HTML and do not use its linearized exponents as a verified complexity formula.')
  ident['author_name_variant_proof']=proof(p/'paper-104-author.html');ident['author_family_set_matches_publisher']=False
 if n==105:rec['version_notes'].append('Initial softsec.kr request raised a connection error; successful same-author KAIST domain PDF retained separately, and failed-request bytes preserved.')
 if n==107:rec['version_notes'].append('arXiv v4 2025-01-30 PDF has 35 physical pages versus formal publisher pp426–444 (19 pages). It prints exact DOI and full author Gilbert Louis Bernstein, while HTML shortens this name to Gilbert Bernstein. Archive is extended author preprint; do not conflate its page count with proceedings span. PDF reference text also says 29th with ASPLOS 25; original source retained.')
 if n==108:
  rec['version_notes'].append('Canonical author PDF abstract reports 63.9% more pruned indirect-call targets; CityU institution HTML for the same DOI reports 81.3%. Both are read and archived independently. No body-based adjudication or averaging was performed; other quoted precision/recall figures match. Author-hosted PDF is from Anshunkang Zhou (seviezhou).')
  s=soup('paper-108-institution');other=s.select_one('div.textblock').get_text(' ',strip=True);vf=p/'paper-108-institution-abstract.txt';vf.write_text(other+'\n');rec['alternate_abstract']={'source':proof(p/'paper-108-institution.html'),'extraction':'HTML first div.textblock, get_text(" ", strip=True)','abstract':other,'abstract_sha256':sha(other.encode()),'text':proof(vf),'counted_as_additional_paper':False}
 if n==109:rec['version_notes'].append('Author PDF reference text says 29th while labeling ASPLOS 25; exact DOI, title and all four authors match. Retain original source wording instead of silently rewriting it.')
 if n==110:rec['version_notes'].append('Publisher/official title uses TAOPT; PDF renders TaOPT/small caps. DOI and all five authors match. Abstract continues from left column to top of right column, with footer removed only from extracted abstract, never from original PDF/text.')
 records.append(rec)
bundle={'scope':'ASPLOS 2025 independent parallel screening program orders 91–110; merge serially only after root review. No repository edits were made.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_manifest_sha256':sha(manifest.read_bytes()),'requested_orders':list(range(91,111)),'already_screened_skipped':[94,95],'new_full_abstracts':len(records),'new_representative_pdfs':sum('representative_pdf'in x for x in records),'new_representative_pdf_pages':sum(x['representative_pdf']['pages'] for x in records if 'representative_pdf'in x),'selected_body_readings_added':0,'actual_rendered_pages_viewed':15,'sources':sources,'records':records,'alternate_or_related_pdfs':[],'integration_notes':['Absolute /tmp paths can be remapped while preserving bytes and hashes. Previous 77–90 bundle untouched.','18 new abstracts, 15 representative PDFs; abstract-only gaps 98/102/104. Existing 94/95 skipped.','No selected body-reading or reproduced-performance credit from PDF archival and complete abstract screening.','PDF extraction uses pdftotext default order without -raw or -layout; command and all fragment rules recorded in HANDOFF and build_bundle.py.','Do not use headline ratios as transferable performance facts before body-reading hardware, baselines, workload, batch, quality and latency constraints.']}
(p/'merge-ready.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:bundle[k] for k in ['new_full_abstracts','new_representative_pdfs','new_representative_pdf_pages','selected_body_readings_added','actual_rendered_pages_viewed']},ensure_ascii=False));print('sources',len(sources))
