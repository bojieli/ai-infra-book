"""Self-written manifests for primary abstract reading, not downloaded implementation."""
from pathlib import Path
import json,hashlib,datetime,re
from bs4 import BeautifulSoup
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
write=lambda f,x:(D/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
manifest={r['program_order']:r for r in load('input-manifest.json')['papers']};sources=load('sources.json');logs=load('extraction-log.json')
versions={76:'第一作者Aaron Barnes个人站点公开14页稿，PDF生成2024-09-25 UTC（本地pdfinfo显示09-26）；题名及三名作者匹配，正式1027–1040同为14页，无出版商字节相等证明。',77:'共同作者Tor Aamodt在UBC站点公开17页稿，PDF生成2024-09-13；题名及七名作者匹配，正式1041–1057为17页，但公开稿自第1页编号，不当作出版商VoR。',79:'SNU机构研究成果记录的完整Abstract，citation_doi与五名作者匹配正式记录；正式1073–1089为17页，未取得PDF，不把17计作可用页数。页面metadata第一作者Hanyang与program的SNU单位不同，原样保存。',80:'CRAFT作者实验室成果页的完整Abstract，题名、五名作者与MICRO24出版说明匹配。页面显示July2024，article:published_time为2024-07-02，modified_time为2025-08-11；正式出版为2024-11-02，日期不混作会议事件或全文修订号。未取得PDF。'}
choices={76:('reference','HSU从光追单元扩展到层次化近邻搜索，体现分支、专用数据通路与接口限制；可为第4章备查，但硬件扩展的摘要结果不是当前GPU/向量检索框架已有功能，不新开正文。'),77:('reference','TTA与TTA+对照固定运算和可编程性，涉及不规则树遍历；与第4章取舍有关，先备查，不把B-tree/N-body性能移作LLM或默认支持任意树。'),79:('exclude','NeuroLobe面向脑机接口的脉冲事件处理，虽含同步、负载平衡和多任务，但与本书当前贯穿模型及业务距离较远；不扩展BCI背景或正文。'),80:('reference','ActiveN以active-message和稀疏转发缓解存储延迟，使SNN突触可用片外容量；作为第4章容量/执行组织的备查。摘要中96.6x A100限于所述SNN比较，不外推到Transformer。')}
papers=[]
for n in [76,77,79,80]:
 p={k:manifest[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']}
 if n in [76,77]:
  source=f'paper-{n:03d}.pdf';txt=f'paper-{n:03d}-left-column.txt';kind='author-hosted PDF';pages=int(re.search(r'^Pages:\s+(\d+)',(D/f'paper-{n:03d}-info.txt').read_text(),re.M).group(1));ex={'kind':'pdftotext_left_column','command':next(r['command'] for r in logs if r['program_order']==n and '-x' in r['command']),'corrections':[]};t=(D/txt).read_text();a=t.index('Abstract—')+len('Abstract—')
 else:
  source={79:'bci-institution.html',80:'activen-lab.html'}[n];txt=source+'.txt';kind='institutional research record HTML' if n==79 else 'author laboratory publication HTML';pages=0;ex={'kind':'bs4_visible_text','remove_tags':['script','style'],'get_text_separator':'\n','strip':True,'append_final_newline':True,'corrections':[]};t=(D/txt).read_text();a=t.index('Abstract\n')+len('Abstract\n')
 src=next(s for s in sources if s['file']==source);abstract=(D/f'abstract-{n:03d}.txt').read_text()[:-1];z=a+len(abstract);assert t[a:z]==abstract
 p.update(source_file=source,source_sha256=src['sha256'],source_url=src['url'],source_retrieved_at=src['retrieved_at'],source_kind=kind,pdf_pages=pages,version_identity=versions[n],abstract_text_file=txt,abstract_text_sha256=sha((D/txt).read_bytes()),abstract_char_range=[a,z],abstract=abstract,abstract_sha256=sha(abstract.encode()),abstract_file=f'abstract-{n:03d}.txt',extraction=ex,read_scope={'complete_abstract':True,'body_read':False,'figures_read':False,'scope':'完整摘要与身份/版本；不读正文，首页可见图不算图机制阅读'},screening={'decision':choices[n][0],'reason':choices[n][1],'outline_changed':False,'body_reading_candidate':False})
 papers.append(p)
failures=[]
for n in [65,82]:
 files=['ringroad-author.html','ringroad-publisher.response'] if n==65 else ['compass-jiang-author.html','compass-liu-author.html','compass-publisher.response']
 reason='作者页仅给IEEE链接，IEEE202空响应；搜索另见中文介绍文件，未将标题/介绍材料代替正式完整摘要。' if n==65 else '两名作者页面只给书目信息，一页Paper/Code/BibTeX均为#占位；IEEE202空响应。没有将第三方片段或占位链接当完整摘要。'
 failures.append({'program_order':n,'doi':manifest[n]['doi'],'program_title':manifest[n]['program_title'],'abstract_read':False,'body_read':False,'pdf_pages':0,'reason':reason,'evidence_files':files,'next_action':'等待可用作者公开稿；本批不重复尝试限制服务。'})
prior=[{'file':r['file'],'sha256':r['sha256']} for r in load('reused-sources.json') if r['file'].startswith('input-parallel-')]
write('abstracts.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'locked_program_orders':[65,76,77,79,80,82],'canonical_abstracts_at_snapshot':80,'input_manifest_sha256':sha((D/'input-manifest.json').read_bytes()),'input_reading_coverage_sha256':sha((D/'input-reading-coverage.json').read_bytes()),'prior_batch_snapshots':prior,'papers':papers,'unavailable':failures})
aux=[]
for f,key in [('ringroad-author.html','Ring Road:'),('bci-author.html','Rearchitecting a Neuromorphic'),('compass-jiang-author.html','COMPASS:'),('compass-liu-author.html','COMPASS:')]:
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for tag in s(['script','style']):tag.decompose()
 t=s.get_text('\n',strip=True)+'\n';(D/(f+'.txt')).write_text(t)
 if f=='ringroad-author.html':a=t.rfind('Yinxiao Feng*',0,t.index(key));z=t.index('2024.',t.index(key,a))+5
 elif f=='bci-author.html':a=t.index(key);z=t.index('Neuromorphic',t.index('Code',a))+len('Neuromorphic')
 elif f=='compass-jiang-author.html':a=t.index(key);z=t.index('Li Jiang',a)+len('Li Jiang');z=t.index('\n',z)
 else:a=t.index(key);z=t.index('[BibTeX]',a)+len('[BibTeX]')
 aux.append({'source_file':f,'file':f+'.txt','sha256':sha(t.encode()),'char_range':[a,z],'line_range':[t.count('\n',0,a)+1,t.count('\n',0,z)+1],'text':t[a:z],'scope':'selected author publication entry only; not a full abstract'})
for f in ['activen-lab.html','bci-institution.html']:
 t=(D/(f+'.txt')).read_text();z=t.index('Abstract\n')
 aux.append({'source_file':f,'file':f+'.txt','sha256':sha(t.encode()),'char_range':[0,z],'line_range':[1,t.count('\n',0,z)+1],'text':t[:z],'scope':'title/authors and visible page date before abstract'})
 s=BeautifulSoup((D/f).read_bytes(),'html.parser');rows=[]
 for tag in s.find_all('meta'):
  key=tag.get('name') or tag.get('property') or ''
  if key.startswith('citation_') or key in ['article:published_time','article:modified_time']:rows.append({'key':key,'value':tag.get('content')})
 write(f+'-metadata.json',rows)
write('reading.json',{'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_primary_abstracts_read':4,'matching_pdf_documents':2,'matching_pdf_pages_available':31,'html_complete_abstracts':2,'body_pages_read':0,'paper_figures_read':0,'source_code_read':False,'downloaded_code_executed':False,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-first-page.png','sha256':sha((D/f'paper-{n:03d}-first-page.png').read_bytes()),'actually_viewed':True,'scope':'title/authors/complete abstract only; body and figure mechanism not read'} for n in [76,77]],'auxiliary_text_scopes':aux,'metadata_scopes':['activen-lab.html-metadata.json','bci-institution.html-metadata.json'],'limits':'可用PDF31页不等于正文阅读；HTML页数0；65/82未得完整摘要不计数。'})
print('Built mixed PDF/HTML records')
