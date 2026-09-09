"""Self-written offline packaging: complete abstracts only, no body claims."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,hashlib,datetime
D=Path(__file__).resolve().parent
load=lambda f:json.loads((D/f).read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
write=lambda f,x:(D/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def html_text(f):
 s=BeautifulSoup((D/f).read_bytes(),'html.parser')
 for x in s(['script','style']):x.decompose()
 t=s.get_text('\n',strip=True)+'\n';(D/(f+'.txt')).write_text(t);return t
m={r['program_order']:r for r in load('input-manifest.json')['papers']};sources=load('sources.json');logs=load('extraction-log.json');papers=[]
versions={98:'Tulika Mitra的NUS作者站点15页公开稿，PDF生成2024-08-16，正式页码1338–1352也是15页。首页题名DVFS匹配publisher；program题名DFVS原样保留。十名作者匹配；不是已证明与出版商字节相同的VoR。',102:'Rakesh Kumar的NTNU作者站点15页公开稿，PDF生成2024-09-16，正式1382–1396也是15页。首页Front-End及Roman Brunner匹配publisher；program写Frontend及Roman Kaspar Brunner。并非已证明与出版商字节相同的VoR。',106:'共同作者SangLyul Cho的publications页完整摘要，标题和五名作者对应MICRO2024，Paper链接10764661匹配正式记录。作者页把Jihoon Hong放在Hyunseung Lee之前，program/publisher次序相反，保留差异。网页页脚2025–2026不是论文日期；没有取得PDF，正式14页不计下载页数。',113:'SKKU Pure机构记录完整摘要，十名作者、DOI及1532–1547页匹配正式记录，标示Published 2024、会议2024-11-02至11-06。机构当前宿主页不等于所有作者发表时单位；无PDF，正式16页不计下载页数。'}
reasons={98:('reference','第4/5章备查：CGRA流水中非瓶颈阶段降频与电源岛粒度、映射协同。摘要支持先找吞吐瓶颈再分配能耗预算的教学方向；未读正文，不能把该CGRA结果当现有GPU框架已实现的自动DVFS。现有瓶颈分析主线够用，暂不增加正文。'),102:('reference','备查有效缓存容量与分配粒度的关系；摘要对象是大型指令足迹的通用服务器CPU前端，不是AI算子或KV缓存。32个百分点不能写成32%。没有真实AI主机瓶颈证据，不为此扩展第12章通用CPU细节。'),106:('reference','第2/4/5章备查：H3全局卷积的FFT及按需参数生成，显示替换attention后仍需检查计算利用率、片上带宽与SRAM容量。76x/48x是单个全局卷积算子的面积/功率效率比较，不能外推LLM端到端吞吐、当前Mamba或所有SSM。不额外加模型目录。'),113:('exclude','低温SFQ处理器及量子/天文/计量应用与本书既有AI负载案例关联弱。摘要4K是低温条件，不是token长度；与低温CMOS的功耗速度比较不能当常温AI数据中心收益，排除正文扩写。')}
for n in [98,102,106,113]:
 p={k:m[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']}
 if n in [98,102]:
  f=f'paper-{n:03d}.pdf';tf=f'paper-{n:03d}-left-column.txt';t=(D/tf).read_text();a=t.index('Abstract—')+len('Abstract—');end=t.index('I. I NTRODUCTION',a);abstract=t[a:end].rstrip();z=a+len(abstract)
  extraction={'command':next(r['command'] for r in logs if r['program_order']==n and '-x' in r['command']),'corrections':[]};kind='author-hosted PDF';pages=15
 else:
  f={106:'vga-publications.html',113:'supercore-institution.html'}[n];tf=f+'.txt';t=html_text(f)
  if n==106:a=t.index('Abstract:\n',t.index('VGA:'))+len('Abstract:\n');end=t.index('\n© ',a)
  else:a=t.index('Abstract\n')+len('Abstract\n');end=t.index('\nOriginal language',a)
  abstract=t[a:end].rstrip();z=a+len(abstract);extraction={'recipe':'BeautifulSoup html.parser; remove script/style; get_text(newline,strip=True)+newline; zero-based half-open Unicode character range','corrections':[]};kind='author publication HTML' if n==106 else 'institutional repository HTML';pages=0
 src=next(r for r in sources if r['file']==f);af=f'abstract-{n:03d}.txt';(D/af).write_text(abstract+'\n');decision,reason=reasons[n]
 p.update(source_file=f,source_sha256=src['sha256'],source_url=src['url'],source_retrieved_at=src['retrieved_at'],source_kind=kind,pdf_pages=pages,version_identity=versions[n],abstract_text_file=tf,abstract_text_sha256=sha((D/tf).read_bytes()),abstract_char_range=[a,z],abstract_line_range=[t.count('\n',0,a)+1,t.count('\n',0,z)+1],abstract=abstract,abstract_sha256=sha(abstract.encode()),abstract_file=af,extraction=extraction,read_scope={'complete_abstract':True,'body_read':False,'figures_read':False,'scope':'完整摘要与身份/版本标记；PDF仅首页摘要视读，正文0'},screening={'decision':decision,'reason':reason,'outline_changed':False,'body_reading_candidate':False});papers.append(p)
failed=[]
for n,files,reason in [(104,['sophgo-publisher.response'],'IEEE10764438一次GET返回202空响应。发现产品文档、LLM-TPU工程和第三方论文阅读文章，但它们不能替代本论文完整一手摘要，未纳入。'),(110,['ares-author.html','ares-computerorg.html','ares-group.html','ares-coauthor.html'],'第一作者目录只链接Computer Society，返回HTTP200静态网页外壳，无论文摘要；清华组目录href为空；共同作者目录PDF指向ACM出版商路径而非作者公开稿。已记录链接，本轮不再扩展获取或重试受限站点；书目及接收新闻不算摘要。')]:
 failed.append({'program_order':n,'doi':m[n]['doi'],'program_title':m[n]['program_title'],'abstract_read':False,'body_read':False,'pdf_pages':0,'reason':reason,'evidence_files':files,'next_action':'等待新的一手公开稿；不重复已知受限路径。'})
prior=[{'file':r['file'],'sha256':r['sha256']} for r in load('reused-sources.json') if r['file'].startswith('input-parallel-')]
write('abstracts.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'locked_program_orders':[98,102,104,106,110,113],'canonical_abstracts_at_snapshot':86,'input_manifest_sha256':sha((D/'input-manifest.json').read_bytes()),'input_reading_coverage_sha256':sha((D/'input-reading-coverage.json').read_bytes()),'prior_batch_snapshots':prior,'papers':papers,'unavailable':failed})
aux=[]
for f in ['ares-author.html','ares-group.html','ares-coauthor.html','vga-publications.html','supercore-institution.html']:
 t=html_text(f)
 if f=='ares-author.html':a=t.index('Ares-Flash:');z=t.index('\nPDF',a)+len('\nPDF')
 elif f=='ares-group.html':a=t.index('Ares-Flash:');z=t.index('\nMaxEmbed:',a)
 elif f=='ares-coauthor.html':a=t.index('Ares-Flash:',t.index('📝 Publications'));z=t.index('\nFull Lifecycle',a)
 elif f=='vga-publications.html':a=t.index('VGA:');z=t.index('\nAbstract:',a)
 else:a=t.index('Original language');z=t.index('\nPublication series',a)
 aux.append({'source_file':f,'file':f+'.txt','sha256':sha(t.encode()),'char_range':[a,z],'line_range':[t.count('\n',0,a)+1,t.count('\n',0,z)+1],'text':t[a:z],'scope':'selected identity/availability metadata only'})
links=[]
for f in ['ares-author.html','ares-group.html','ares-coauthor.html','vga-publications.html']:
 s=BeautifulSoup((D/f).read_bytes(),'html.parser');key='VGA:' if f.startswith('vga') else 'Ares-Flash:'
 for el in s.find_all(string=lambda x:x and key in x):
  parent=el.find_parent('li') if not f.startswith('vga') else el.parent.parent
  if parent is not None:
   links.append({'source_file':f,'selected_text':parent.get_text('\n',strip=True),'links':[{'text':a.get_text(' ',strip=True),'href':a.get('href')} for a in parent.find_all('a')]})
write('selected-links.json',links)
write('reading.json',{'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_primary_abstracts_read':4,'matching_pdf_documents':2,'matching_pdf_pages_available':30,'body_pages_read':0,'paper_figures_read':0,'source_code_read':False,'downloaded_code_executed':False,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-first-page.png','sha256':sha((D/f'paper-{n:03d}-first-page.png').read_bytes()),'actually_viewed':True,'scope':'identity and complete abstract only'} for n in [98,102]],'auxiliary_text_scopes':aux,'availability_checks':[{'file':'ares-computerorg.html','scope':'static HTML shell inspected; no paper title or abstract; embedded scripts not executed'},{'file':'vga-author.html','scope':'searched VGA, no match; not full site reading'},{'file':'selected-links.json','scope':'only target-paper author links; not other publications'}],'limits':'30 available PDF pages is not body reading; HTML-only papers add zero PDF pages. Two unavailable abstracts excluded. No current-hardware implementation or end-to-end model performance inferred.'})
print('Built complete-abstract and reading records')
