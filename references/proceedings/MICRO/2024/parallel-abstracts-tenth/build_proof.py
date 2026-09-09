"""Create explicit abstract-only evidence records; self-written, offline."""
from pathlib import Path
import json,hashlib,datetime,re
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
write=lambda f,x:(D/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
m={r['program_order']:r for r in load('input-manifest.json')['papers']};sources=load('sources.json');logs=load('extraction-log.json');papers=[]
for n in [85,86]:
 p={k:m[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']};f=f'paper-{n:03d}.pdf';src=next(r for r in sources if r['file']==f);txt=f'paper-{n:03d}-left-column.txt';t=(D/txt).read_text();a=t.index('Abstract—')+len('Abstract—');abstract=(D/f'abstract-{n:03d}.txt').read_text()[:-1];z=a+len(abstract);assert t[a:z]==abstract
 version=('第一作者个人站点16页公开稿，生成2024-10-28，题名和两名作者匹配正式1153–1168页。原稿作者名为Chowdhuryy，摘要缺词的we IvLeague-Invert原样保留；不证明等同出版商字节。' if n==85 else '共同作者Dinghao Wu的PSU站点15页公开稿，生成2024-11-21，晚于会议；题名及七名作者匹配正式1169–1183页。公开稿自第1页编号，不当作会议当时VoR字节。')
 reason=('备查隔离元数据与容量动态分配的关系；对象为安全处理器完整性树，不是现成Agent沙箱功能，没有对应AI负载前不加正文。' if n==85 else '备查第1章系统边界及GPU共享资源的讨论。摘要可提示核心/显存分区之外还有uncore共享路径；2024特定实验不能直接代表当前所有MPS/MIG设备，也不能由泄漏结论推成吞吐干扰数值。需要具体章节问题才补正文，暂不新增。')
 p.update(source_file=f,source_sha256=src['sha256'],source_url=src['url'],source_retrieved_at=src['retrieved_at'],source_kind='author-hosted PDF',pdf_pages={85:16,86:15}[n],version_identity=version,abstract_text_file=txt,abstract_text_sha256=sha((D/txt).read_bytes()),abstract_char_range=[a,z],abstract=abstract,abstract_sha256=sha(abstract.encode()),abstract_file=f'abstract-{n:03d}.txt',extraction={'command':next(r['command'] for r in logs if r['program_order']==n and '-x' in r['command']),'corrections':[]},read_scope={'complete_abstract':True,'body_read':False,'figures_read':False,'scope':'首页身份、完整摘要与版本标記；正文0，不读取攻击方法或运行源码'},screening={'decision':'reference','reason':reason,'outline_changed':False,'body_reading_candidate':False});papers.append(p)
failed=[]
for n,files,reason in [(84,['ghost-author-publications.html','ghost-publisher.response'],'作者目录只给书目，无论文链接；IEEE202空响应。作者目录和publisher题名有in GPU，program无该后缀；Hans Kasan和program Hans Kason差异保留。'),(91,['terminus-author.html','terminus-publisher.response'],'作者目录含to appear的2024旧条目，无PDF；IEEE202空响应。不把博士答辩简介当正式论文摘要。'),(95,['tminer-institution-news.html','tminer-publisher.response'],'ICT新闻GET在TLS证书验证阶段失败，未取得HTTP响应；IEEE202空响应。保留错误，不绕过验证或重试。'),(96,['pointcim-institution.html','pointcim-angular-state.json','pointcim-abstract-key-search.json','pointcim-publisher.response'],'NTU机构页只有题名作者DOI等书目；公开嵌入状态的23个abstract键都属于NGX_TRANSLATE_STATE界面翻译，没有论文摘要。IEEE202空响应。不将14页正式页码当成已获PDF。')]:
 failed.append({'program_order':n,'doi':m[n]['doi'],'program_title':m[n]['program_title'],'abstract_read':False,'body_read':False,'pdf_pages':0,'reason':reason,'evidence_files':files,'next_action':'等待新增的一手公开稿；不重试已知受限路径。'})
prior=[{'file':r['file'],'sha256':r['sha256']} for r in load('reused-sources.json') if r['file'].startswith('input-parallel-')]
write('abstracts.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'locked_program_orders':[84,85,86,91,95,96],'canonical_abstracts_at_snapshot':84,'input_manifest_sha256':sha((D/'input-manifest.json').read_bytes()),'input_reading_coverage_sha256':sha((D/'input-reading-coverage.json').read_bytes()),'prior_batch_snapshots':prior,'papers':papers,'unavailable':failed})
aux=[]
for f,key in [('ghost-author-publications.html','Ghost Arbitration:'),('terminus-author.html','Terminus:'),('pointcim-institution.html','Details')]:
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 t=s.get_text('\n',strip=True)+'\n';(D/(f+'.txt')).write_text(t);a=t.index(key)
 if f.startswith('ghost'):z=t.index('Nov. 2024',a)+len('Nov. 2024')
 elif f.startswith('terminus'):z=t.index('(to appear)',a)+len('(to appear)')
 else:z=t.index('關於 (About)',a)
 aux.append({'source_file':f,'file':f+'.txt','sha256':sha(t.encode()),'char_range':[a,z],'line_range':[t.count('\n',0,a)+1,t.count('\n',0,z)+1],'text':t[a:z],'scope':'selected identity/availability metadata, not complete abstract'})
write('reading.json',{'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_primary_abstracts_read':2,'matching_pdf_documents':2,'matching_pdf_pages_available':31,'body_pages_read':0,'paper_figures_read':0,'source_code_read':False,'downloaded_code_executed':False,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-first-page.png','sha256':sha((D/f'paper-{n:03d}-first-page.png').read_bytes()),'actually_viewed':True,'scope':'identity and complete abstract only'} for n in [85,86]],'auxiliary_text_scopes':aux,'pointcim_state_scope':{'decoded_as_data_not_executed':True,'entire_state_read':False,'inspected_file':'pointcim-abstract-key-search.json','matched_keys':23,'all_matched_paths_under':'NGX_TRANSLATE_STATE','finding':'界面翻译标签，无论文摘要'},'limits':'31 available PDF pages does not imply body reading; four unavailable abstracts not counted; no present-day GPU security conclusion.'})
print('Built records')
