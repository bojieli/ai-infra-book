"""Generate evidence metadata from preserved source bytes, without running artifacts."""
from pathlib import Path
import datetime, hashlib, json, re

D=Path(__file__).resolve().parent
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(f): return json.loads((D/f).read_text())
def sha(f): return hashlib.sha256((D/f).read_bytes()).hexdigest()
def save(f,obj): (D/f).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
manifest={r['program_order']:r for r in load('input-manifest.json')['papers']}
sources={r['file']:r for r in load('sources.json')}
decisions={
39:('exclude','从 SystemVerilog、指令编码和设计元数据合成每条指令的多个微架构执行路径，并扩展符号信息流分析以验证 leakage contracts。摘要明确是在填补手工抽象模型与 RTL 的验证缺口。','硬件形式验证与本书模型—资源—性能主线距离较远，不因为含多个路径或安全术语就放入 Agent sandbox；本轮排除正文补读。'),
44:('reference','以消息传递 GNN 的图与神经算子为对象，利用共同的数据流结构、度数/顶点感知调度和类脉动阵列改善复用与负载平衡。摘要明确报告 simulation results。','第 4/5 章稀疏图计算的备查；GNN 顶点/边的不均衡不是自动适用于 MoE 路由的证据，不新增正文候选。'),
48:('reference','将稀疏迭代求解器数据保留在分布式片上 SRAM，通过跨 PE 的数据/计算映射避免片内通信瓶颈，并利用跨迭代复用提升算术强度。','与此前 Sparsepipe 的跨迭代复用主题重叠，第 4/5 章备查即可；不据摘要的 GPU 倍数外推 attention/MoE，暂不新增正文补读。'),
49:('candidate','浮点直接使用 AP 的 bit-serial 路径会吞吐不足；FloatAP 用位与分量并行的尾数对齐和既有 adder tree 改进浮点加法、归约、乘法与点积，摘要按精度分别与 area-equivalent A100 比较。','值得一个窄范围后续正文核对：CAM 内运算减少数据移动后，浮点对齐/归约及可用容量怎样成为新限制，以及面积归一化与设备/精度基线是否可比。仅可能补第 4 章既有 PIM/精度讨论的一处说明，不扩章。'),
}
versions={
39:'arXiv 2409.19478v1，提交 2024-09-28 23:01:48 UTC；作者声明 Authors version/to appear MICRO 2024。下载固定 v1 PDF，共 18 物理页，首页题名与七名作者匹配。PDF 生成元数据为 2024-10-01，不替代 arXiv 提交日期；正式页码 507–524 也对应 18 页，但页数相同不证明作者稿与出版商版本同字节。',
44:'共同作者 Hao Zheng 发表目录的 MICRO 2024 条目直接链接 assets/files/MICRO-2024.pdf；当前 14 页稿题名、四名作者及机构匹配。PDF 生成日期 2025-09-17，晚于会议；没有明确版本号，不称会议 camera-ready 或已证明与 VoR 同字节。',
48:'第一作者公开 micro24_iterative.pdf，共 14 页；首页 MICRO 2024、五名作者、印刷页 643、DOI .00054 匹配，带 IEEE 下载标记。该下载标记不是本轮获取日期；以 sources.json 的抓取时间和哈希固定本轮原字节。',
49:'Cornell 站点 CDN 公开文件 MICRO2024_FloatAP_Camera_Ready-3.pdf，共 14 页；首页题名与两名作者匹配，元数据生成 2024-09-30。文件名虽含 Camera_Ready-3，但不将后缀当作经过验证的 v3 或出版商 VoR；没有源码/框架集成核验。',
}
papers=[]
for n in [39,44,48,49]:
 p={k:manifest[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date','page']}
 source=f'paper-{n:03d}.pdf';textfile=f'paper-{n:03d}-left-column.txt';text=(D/textfile).read_text();a=text.index('Abstract—');z=text.index('\nIndex Terms',a) if n in [48,49] else text.index('\nI. I NTRODUCTION',a)
 while text[z-1].isspace():z-=1
 abstract=text[a:z];af=f'abstract-{n:03d}.txt';(D/af).write_text(abstract+'\n');pages=int(re.search(r'^Pages:\s+(\d+)',(D/f'paper-{n:03d}-info.txt').read_text(),re.M).group(1));decision,summary,reason=decisions[n]
 p.update(source_file=source,source_sha256=sha(source),source_url=sources[source]['url'],source_retrieved_at=sources[source]['retrieved_at'],source_kind='fixed arXiv author version' if n==39 else 'author-hosted PDF',pdf_pages=pages,version_identity=versions[n],extraction={'kind':'pdftotext physical p1 left-column crop','command':['pdftotext','-f','1','-l','1','-x','0','-y','0','-W','306','-H','792',source,'-'],'source_text':textfile,'corrections':[]},abstract_text_file=textfile,abstract_text_sha256=sha(textfile),abstract_char_range=[a,z],abstract=abstract,abstract_sha256=hashlib.sha256(abstract.encode()).hexdigest(),abstract_file=af,read_scope={'complete_abstract':True,'physical_page':1,'body_read':False,'figures_read':False,'pdf_identity_checked_by_image':True},screening={'decision':decision,'summary_zh':summary,'reason_zh':reason,'outline_changed':False,'body_followup_recommended':n==49})
 papers.append(p)
unavailable=[
 {'program_order':38,'doi':manifest[38]['doi'],'title':manifest[38]['program_title'],'abstract_read':False,'pdf_pages':0,'body_read':False,'reason':'共同作者 Nagoya 目录有题名、五名作者、会议、493–506 页，但该条目无摘要/PDF 链接；IEEE 10764527 返回 202 空响应。','evidence_files':['wakeup-coauthor-pubs.html','wakeup-publisher.response']},
 {'program_order':40,'doi':manifest[40]['doi'],'title':manifest[40]['program_title'],'abstract_read':False,'pdf_pages':0,'body_read':False,'reason':'第一作者和共同作者目录均有题名、七名作者与 MICRO 2024；共同作者 Paper/Code 链接只是 # 占位符，没有可下载文件。IEEE 10764630 返回 202 空响应。','evidence_files':['srender-author.html','srender-coauthor-pubs.html','srender-publisher.response']},
]
save('abstracts.json',{'generated_at':NOW,'scope':'MICRO2024 seventh earliest-unread batch, complete primary abstracts only, body0','locked_program_orders':[38,39,40,44,48,49],'input_manifest_sha256':sha('input-manifest.json'),'input_reading_coverage_sha256':sha('input-reading-coverage.json'),'prior_batch_snapshots':[{'file':f'input-batch-{i}.json','sha256':sha(f'input-batch-{i}.json')} for i in range(1,7)],'papers':papers,'unavailable':unavailable})
aux=[]
def scope(source,textfile,first,last,purpose,include_last=True):
 text=(D/textfile).read_text();a=text.index(first);z=text.index(last,a)+(len(last) if include_last else 0)
 aux.append({'source_file':source,'file':textfile,'sha256':sha(textfile),'char_range':[a,z],'line_range':[text.count('\n',0,a)+1,text.count('\n',0,z)+1],'text':text[a:z],'purpose':purpose,'range_text_normalization':'UTF-8 with CRLF/CR normalized to LF; hash remains original file hash'})
scope('rtl-arxiv.html','rtl-arxiv.txt','Comments:','(24,403 KB)','作者稿声明、类别、arXiv v1 身份与完整 submission history；网页 Abstract 已辅助浏览但不另计一篇。')
scope('wakeup-coauthor-pubs.html','wakeup-coauthor-pubs.txt','Kenichiro Mori, Sota Kosugi, Hiroto Yoshida, Hajime Shimada','493-506, Austin / USA, November 2024.','共同作者书目身份，无摘要或论文链接。')
scope('srender-author.html','srender-author.txt','[C31]','[J9]','第一作者 SRender 条目，无论文链接。',False)
scope('srender-coauthor-pubs.html','srender-coauthor-pubs.txt','SRender: Boosting','[TPDS','共同作者 SRender 条目；对应 HTML Paper/Code href 是 #。',False)
scope('scale-author-pubs.html','scale-author-pubs.txt',"[MICRO'24]",'[ICCAD','SCALE 题名、作者、MICRO 2024 和 PDF 链接身份。',False)
save('reading.json',{'recorded_at':NOW,'full_primary_abstracts_read':4,'body_pages_read':0,'paper_figures_read':0,'source_code_read':False,'downloaded_code_executed':False,'matching_pdf_documents':4,'matching_pdf_pages_available':60,'new_matching_pdf_downloads':4,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-p1.png','sha256':sha(f'paper-{n:03d}-p1.png'),'actually_viewed':True,'scope':'题名、作者、完整摘要和出版标识；图表或正文虽然可见但未分析，不计正文阅读。'} for n in [39,44,48,49]],'auxiliary_text_scopes':aux,'prior_topic_overlap':'Azul 与此前已读 Sparsepipe 的跨迭代复用主题重叠，本批不重复正文阅读。','counting_rule':'可用 PDF 页数、网页目录、# 占位链接与 202 空响应都不算完成正文或摘要阅读；arXiv HTML 与 PDF 是同一论文。'})
save('acquisition-notes.json',{'http_responses':11,'http_200':9,'http_202_empty':2,'reused_input_files':8,'failures':[{'file':'wakeup-publisher.response','status':202,'bytes':0},{'file':'srender-publisher.response','status':202,'bytes':0}],'version_cautions':versions,'not_downloaded':['研究源码、RTL、artifact、slides','任何自动渲染/网页脚本工件'],'no_secondary_substitute':'未用 ResearchGate、自动解读或搜索摘录代替 38/40 的完整一手摘要。','source_version_rule':'固定 arXiv v1 与可变作者路径分别标明；作者托管 PDF 的日期/文件名不自动等于会议正式版。','candidate_limit':'仅 FloatAP 为一个有界后续正文候选；本批没有实际正文阅读或大纲修改。'})
