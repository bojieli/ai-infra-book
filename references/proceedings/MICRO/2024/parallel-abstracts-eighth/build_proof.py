"""Self-written archive manifest generator; no paper code is loaded or executed."""
from pathlib import Path
import json,hashlib,datetime,re
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda f:json.loads((D/f).read_text())
write=lambda f,x:(D/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
manifest={p['program_order']:p for p in load('input-manifest.json')['papers']};sources=load('sources.json');logs=load('extraction-log.json')
versions={
56:'固定 arXiv:2405.06941v3，修订时间2024-09-16，PDF生成2024-09-17，共16物理页；正式会议750–764为15页，未认作出版商VoR。arXiv HTML作者顺序将Yunong Shi列第三，PDF将其列第五，与正式记录相符；同一六人，顺序差异保留。program将Xiang Fang标UCSB，PDF标UCSD，亦不强行统一。',
58:'研究组 publication 页面在MICRO2024项链接 /akitartm.pdf；PDF题名、三名作者匹配，13物理页，元数据生成2025-05-13，正式780–794为15页。仅认作作者现行公开稿，不宣称camera-ready/VoR或2024原始字节。',
61:'作者University of Murcia站点公开PDF，13物理页；生成2024-09-09。题名与三名作者匹配，正式810–822也是13页；无独立出版商字节相等证明。',
62:'作者IIT Kanpur站点公开17页PDF；首页显示MICRO2024、正式页码823及 DOI10.1109/MICRO61859.2024.00066，生成2024-10-29。匹配正式823–839页，原始字节留存；不由作者托管自动推出使用许可。',
63:'作者University of Murcia站点16页公开稿，生成2024-12-04 UTC（pdfinfo本地2024-12-05），晚于会议；题名与五名作者匹配，正式840–855也是16页。未证明逐字节等于出版商版。'}
screen={
56:('exclude','量子表面码动态缺陷与QEC资源，不直接回答本书AI模型的计算、容量、带宽或调度问题，不建议继续正文。'),
58:('reference','保留研究工具可观察性的备查。摘要支持“运行中发现模拟问题”的方法讨论，但本书先算数再选工具，不需要新增模拟器教程或正文阅读候选。'),
61:('reference','store buffer受长延迟阻塞、复用已有结构隐藏等待是容量/依赖的传统CPU例子；摘要没有AI服务负载证据，先备查，不据此替换GPU推理主线或增加协议细节。'),
62:('reference','硬件MESI扩展检测并缓解false sharing，可备查主机性能分析；不是现成软件profile工具，模拟1.39X不可移作AI框架性能。无实际AI瓶颈案例前不建议正文。'),
63:('exclude','通用硬件事务内存的冲突推测与提交次序，摘要没有AI Infra具体负载，继续阅读会扩展到与主线距离较远的HTM专题。')}
papers=[]
for n in [56,58,61,62,63]:
 p={k:manifest[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']}
 f=f'paper-{n:03d}.pdf';src=next(s for s in sources if s['file']==f);txt=f'paper-{n:03d}-left-column.txt';t=(D/txt).read_text();a=t.index('Abstract—')+len('Abstract—');abstract=(D/f'abstract-{n:03d}.txt').read_text()[:-1];z=a+len(abstract);assert t[a:z]==abstract
 pages=int(re.search(r'^Pages:\s+(\d+)',(D/f'paper-{n:03d}-info.txt').read_text(),re.M).group(1))
 p.update(source_file=f,source_sha256=src['sha256'],source_url=src['url'],source_retrieved_at=src['retrieved_at'],source_kind='fixed author arXiv PDF' if n==56 else 'author-hosted PDF',pdf_pages=pages,version_identity=versions[n],abstract_text_file=txt,abstract_text_sha256=sha((D/txt).read_bytes()),abstract_char_range=[a,z],abstract=abstract,abstract_sha256=sha(abstract.encode()),abstract_file=f'abstract-{n:03d}.txt',extraction={'command':next(r['command'] for r in logs if r['program_order']==n and '-x' in r['command']),'corrections':[]},read_scope={'complete_abstract':True,'body_read':False,'figures_read':False,'scope':'只读首页题名作者、完整摘要与版本标记；首页出现正文/图并不算正文或图机制阅读'},screening={'decision':screen[n][0],'reason':screen[n][1],'outline_changed':False,'body_reading_candidate':False})
 papers.append(p)
prior=[{'file':r['file'],'sha256':r['sha256']} for r in load('reused-sources.json') if r['file'].startswith('input-parallel-')]
failed={'program_order':57,'doi':manifest[57]['doi'],'program_title':manifest[57]['program_title'],'abstract_read':False,'body_read':False,'pdf_pages':0,'reason':'作者HLS页仅给DOI与Code；IEEE GET返回418。作者项目README提供重复Introduction及工件入口，但不是标明的完整论文摘要，且Citing块有55th与Yanwen元数据错误。未将介绍、代码存在或工具搜索片段当完整摘要。','evidence_files':['hestia-author-hls.html','hestia-publisher.response','hestia-repo-contents.json','hestia-readme-blob.json','hestia-readme.md'],'next_action':'若后续出现作者公开稿再处理；本批不重复尝试受限服务，不执行工件。'}
record={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'locked_program_orders':[56,57,58,61,62,63],'canonical_abstracts_at_snapshot':75,'input_manifest_sha256':sha((D/'input-manifest.json').read_bytes()),'input_reading_coverage_sha256':sha((D/'input-reading-coverage.json').read_bytes()),'prior_batch_snapshots':prior,'papers':papers,'unavailable':[failed]};write('abstracts.json',record)
aux=[]
for name,selector in [('surf-arxiv.html','blockquote.abstract'),('hestia-author-hls.html',None),('akitartm-author-publications.html',None)]:
 s=BeautifulSoup((D/name).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 t=s.get_text('\n',strip=True)+'\n';fn=name+'.txt';(D/fn).write_text(t)
 if name=='surf-arxiv.html':
  keys=['Surf-Deformer: Mitigating Dynamic Defects on Surface Code via Adaptive Deformation','Authors:','Submission history']
  a=t.index('Title:');z=t.index('Subjects:',a)
 elif name=='hestia-author-hls.html':
  a=t.index('Hestia: An Efficient Cross-Level Debugger for High-Level Synthesis');z=t.index('Code',a)+4
 else:
  a=t.index('Looking into the Black Box: Monitoring Computer Architecture Simulations in Real-Time with AkitaRTM');a=t.rfind('MICRO 2024',0,a);z=t.index('PDF',a)+3
 aux.append({'source_file':name,'file':fn,'sha256':sha(t.encode()),'char_range':[a,z],'line_range':[t.count('\n',0,a)+1,t.count('\n',0,z)+1],'text':t[a:z],'scope':'identity/version/author-link or available abstract; not extra paper count'})
# The arXiv revision history was separately read to distinguish metadata dates.
t=(D/'surf-arxiv.html.txt').read_text();a=t.index('Submission history');z=t.index('Full-text links:',a)
aux.append({'source_file':'surf-arxiv.html','file':'surf-arxiv.html.txt','sha256':sha(t.encode()),'char_range':[a,z],'line_range':[t.count('\n',0,a)+1,t.count('\n',0,z)+1],'text':t[a:z],'scope':'actual arXiv v1/v2/v3 submission history, not additional paper'})
# Fixed blob README declaration ends before setup; no commands or implementation executed.
t=(D/'hestia-readme.md').read_text();a=0;z=t.index('# Setup');aux.append({'source_file':'hestia-readme-blob.json','file':'hestia-readme.md','sha256':sha(t.encode()),'char_range':[a,z],'line_range':[1,t.count('\n',0,z)+1],'text':t[:z],'scope':'README Introduction, Artifact link, Citing and repeated Introduction only; not paper abstract or source implementation'})
reading={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_primary_abstracts_read':5,'matching_pdf_documents':5,'matching_pdf_pages_available':75,'body_pages_read':0,'paper_figures_read':0,'source_code_read':False,'repository_readme_and_metadata_read':True,'downloaded_code_executed':False,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-first-page.png','sha256':sha((D/f'paper-{n:03d}-first-page.png').read_bytes()),'actually_viewed':True,'scope':'title/authors/complete abstract/version marks only; figures and body not interpreted'} for n in [56,58,61,62,63]],'auxiliary_text_scopes':aux,'limits':'5 PDFs totaling75 available pages do not imply body reading; Hestia README is not counted as full abstract.'};write('reading.json',reading)
print('Built abstracts.json and reading.json')
