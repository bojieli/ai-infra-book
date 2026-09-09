"""Build evidence records from saved primary bytes and explicit tool-only observations."""
from pathlib import Path
import datetime
import hashlib
import json
import re

D = Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def load(f):
    return json.loads((D / f).read_text())


def sha(f):
    return hashlib.sha256((D / f).read_bytes()).hexdigest()


def save(f, obj):
    (D / f).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


manifest = {r['program_order']: r for r in load('input-manifest.json')['papers']}
sources = {r['file']: r for r in load('sources.json')}
decisions = {
    28: ('reference', 'IMCompiler 用 segmented integer multiplication 的 IR 分离高层参数与设备优化，由 frontend 翻译、backend 为设备微调单个 GPU kernel 后生成代码。摘要还列出并行化、缓存、索引变换和延迟进位等优化。', '第 5 章可备查领域 IR 与设备特化之间的界限；本书已有 AI 编译实例，不因 crypto GPU kernel 的相似术语增加专题或正文补读。'),
    35: ('reference', 'EntropyIndex 在运行时估计地址位变化，动态挑选 cache index 位，目标是同时减少访问分布失衡与索引计算延迟。摘要包含 SPEC、PARSEC、GAP、CVP 以及有无 prefetch 的多组结果。', '第 4 章缓存有效容量与冲突失效的备查；未读配置与正文，不将 CPU IPC 变化外推为 GPU、LLM 或 KV cache 的收益。'),
    36: ('exclude', 'LLBP 通过大容量后备预测状态与小型核内缓冲分离容量和时延约束；根据程序上下文预取分支元数据，与既有 TAGE 并行访问。摘要报告的是 server CPU 的 branch prediction 与 MPKI。', '通用 CPU 分支预测与本书 AI Infra 主线距离较远；不与 LLM 推测解码混同，排除本轮正文补读。'),
    37: ('exclude', 'TEA 使用预计算结果提前触发 misprediction flush，放松必须赶在 Fetch 覆盖预测结果之前完成的时限，并复用核内执行与清空资源。', '改善乱序 CPU 的难预测分支，不是生成模型推测解码或分布式 prefill/decode 流水；排除本轮正文补读。'),
}
version = {
    28: 'PolyU Scholars Hub 作者机构记录的完整摘要，六名作者、会议、380–392 页、DOI .00036 匹配。公开 PDF 本次未取得；机构条目不是 PDF 或特定源码版本。',
    35: '共同作者 Texas A&M 目录公开稿，13 物理页；PDF 元数据生成日期 2024-09-16，首页题名与五名作者匹配。NSF 书目列 accepted manuscript、MICRO 日期 2024-11-02、451–463 页及 DOI .00041；未下载 NSF PDF，因此不声称本地字节就是 NSF 的 accepted manuscript。program 作者顺序为 Weston/Janfaza/Johnson/Mahmud/Muzahid，publisher 元数据、作者 PDF 与 NSF 顺序为 Weston/Johnson/Janfaza/Mahmud/Muzahid；保留此差异。',
    36: '第一作者公开 LLBP_MICRO24.pdf，16 物理页，首页印刷页 464、MICRO 2024 与 DOI .00042。当前主页同时列 HPCA 2026 的 The Last-Level Branch Predictor Revisited，该文未下载；本批只读 MICRO 2024 条目。无明确稿件版本号。',
    37: '作者 UT Austin HPS 实验室公开 TEA.pdf，13 物理页，首页印刷页 480、MICRO 2024 与 DOI .00043。PDF 元数据生成 2024-10-29。program 的 Pre-computation 与 publisher/作者稿 Precomputation，以及 Chester/Lingzhe 名字写法差异均保留，不改原 manifest。',
}
papers = []
for n in [28, 35, 36, 37]:
    p = {k: manifest[n][k] for k in ['program_order','doi','program_title','program_authors','publisher_title','publisher_authors','publication_date']}
    if n == 28:
        source = 'bigint-institution.html'
        textfile = 'bigint-institution.txt'
        text = (D / textfile).read_text()
        a = text.index('Abstract\n') + len('Abstract\n')
        z = text.index('\nOriginal language', a)
        pages = 0
        extraction = {'kind':'BeautifulSoup visible text','script_style_removed':True,'separator':'\n','newlines':'CRLF and CR normalized to LF'}
    else:
        source = f'paper-{n:03d}.pdf'
        textfile = f'paper-{n:03d}-left-column.txt'
        text = (D / textfile).read_text()
        a = text.index('Abstract—')
        z = text.index('\nI. I NTRODUCTION', a) if n == 36 else text.index('\nIndex Terms', a)
        while text[z-1].isspace():
            z -= 1
        pages = int(re.search(r'^Pages:\s+(\d+)', (D / f'paper-{n:03d}-info.txt').read_text(), re.M).group(1))
        extraction = {'kind':'pdftotext first physical page left-column crop','command':['pdftotext','-f','1','-l','1','-x','0','-y','0','-W','306','-H','792',source,'-'],'source_text':textfile,'corrections':[]}
    abstract = text[a:z]
    f = f'abstract-{n:03d}.txt'
    (D / f).write_text(abstract + '\n')
    decision, summary, reason = decisions[n]
    p.update(source_file=source,source_sha256=sha(source),source_url=sources[source]['url'],source_retrieved_at=sources[source]['retrieved_at'],source_kind='author PDF' if pages else 'author institutional publication record',pdf_pages=pages,version_identity=version[n],extraction=extraction,abstract_text_file=textfile,abstract_text_sha256=sha(textfile),abstract_char_range=[a,z],abstract=abstract,abstract_sha256=hashlib.sha256(abstract.encode()).hexdigest(),abstract_file=f,read_scope={'complete_abstract':True,'physical_page':1 if pages else None,'body_read':False,'figures_read':False,'pdf_identity_checked_by_image':bool(pages)},screening={'decision':decision,'summary_zh':summary,'reason_zh':reason,'outline_changed':False,'body_followup_recommended':False})
    papers.append(p)

tooltext = (D / 'ufc-search-tool-output.txt').read_text()
start = tooltext.index('Fully homomorphic encryption (FHE) is crucial', tooltext.index('## Metadata'))
end = tooltext.index('\n\nPublished in:', start)
ufc_observation = {'program_order':26,'doi':manifest[26]['doi'],'title':manifest[26]['publisher_title'],'observation_kind':'search tool representation of IEEE-indexed abstract; not archived publisher HTTP body','source_file':'ufc-search-tool-output.txt','source_sha256':sha('ufc-search-tool-output.txt'),'char_range':[start,end],'observed_abstract_text':tooltext[start:end],'publisher_url':'https://ieeexplore.ieee.org/document/10764649/','complete_looking_abstract_observed':True,'counted_as_primary_abstract_read':False,'reason':'工具搜索结果显示了一个连续完整摘要段落，但不能把它冒充本地已归档的一手网页字节。两个直接 GET 均 202 空响应；web open 返回需要机器人验证的页面。完整摘要覆盖计数暂保持未完成。','technical_use':'不据此提出数值或正文候选；保留实际观察，避免宣称完全没有见过其摘要。'}
save('tool-observations.json', {'recorded_at':NOW,'observations':[ufc_observation],'tool_outputs':[{'file':'ufc-search-tool-output.txt','sha256':sha('ufc-search-tool-output.txt'),'bytes':(D/'ufc-search-tool-output.txt').stat().st_size,'tool':'web.search_query','request':{'q':'"UFC: A Unified Accelerator for Fully Homomorphic Encryption"'},'http_status_available':False,'is_original_http_response':False},{'file':'ufc-open-tool-output.txt','sha256':sha('ufc-open-tool-output.txt'),'bytes':(D/'ufc-open-tool-output.txt').stat().st_size,'tool':'web.open','request':{'url':'https://ieeexplore.ieee.org/document/10764649/'},'http_status_available':False,'is_original_http_response':False}]})
unavailable = [
    {'program_order':26,'doi':manifest[26]['doi'],'title':manifest[26]['program_title'],'abstract_read':False,'indexed_abstract_observed':True,'pdf_pages':0,'body_read':False,'reason':ufc_observation['reason'],'evidence_files':['ufc-author-pubs.html','ufc-author-paper.html','ufc-publisher.response','ufc-publisher-slash.response','tool-observations.json']},
    {'program_order':32,'doi':manifest[32]['doi'],'title':manifest[32]['program_title'],'abstract_read':False,'indexed_abstract_observed':False,'pdf_pages':0,'body_read':False,'reason':'第一作者网页的静态脚本书目对象、共同作者 UNSW 目录只有题名/作者/会议/DOI；IEEE 10764626 返回 202 空响应。DBLP 发现请求虽 200，但正文为机器人验证 HTML，没有取得其 XML 或公开稿链接。未取得完整一手摘要或公开 PDF。','evidence_files':['fpga-author.html','fpga-author-data.js','fpga-coauthor-pubs.html','fpga-publisher.response','fpga-discovery-dblp-challenge.html']},
]
save('abstracts.json',{'generated_at':NOW,'scope':'MICRO2024 sixth batch; four complete primary abstracts, two incomplete archival paths; no body reading','locked_program_orders':[26,28,32,35,36,37],'input_manifest_sha256':sha('input-manifest.json'),'input_reading_coverage_sha256':sha('input-reading-coverage.json'),'prior_batch_snapshots':[{'file':f'input-batch-{i}.json','sha256':sha(f'input-batch-{i}.json')} for i in range(1,6)],'papers':papers,'unavailable':unavailable})

aux=[]
def scope(source, textfile, first, last, purpose, include_last=True):
    text=(D/textfile).read_text(); a=text.index(first);z=text.index(last,a)+(len(last) if include_last else 0)
    aux.append({'source_file':source,'file':textfile,'sha256':sha(textfile),'char_range':[a,z],'line_range':[text.count('\n',0,a)+1,text.count('\n',0,z)+1],'text':text[a:z],'purpose':purpose,'range_text_normalization':'UTF-8 with CRLF/CR normalized to LF; byte hash covers original file'})

scope('ufc-author-pubs.html','ufc-author-pubs.txt','UFC: A Unified Accelerator','Multi-Objective Software-Hardware','作者发表目录的 UFC 身份条目。',False)
scope('ufc-author-paper.html','ufc-author-paper.txt','UFC: A Unified Accelerator','Categories:','作者 UFC 独立页只有出版信息，没有摘要/PDF。',False)
scope('fpga-author-data.js','fpga-author-data.js','{title:"A Scalable, Efficient','selected:!0}','仅将脚本当原始文本读取这一条论文元数据对象，未执行 JS 或阅读其 React 逻辑。')
scope('fpga-coauthor-pubs.html','fpga-coauthor-pubs.txt','Qinggang Wang, Long Zheng,  Zhaozeng An','437 -- 450, 2024.','共同作者目录书目信息，没有摘要或论文链接。')
scope('cache-index-nsf.html','cache-index-nsf.txt','Citation Details','Conference Paper:','NSF 的作者顺序、日期、页码与 accepted-manuscript 元数据；不等同于本地作者 PDF 版本。')
scope('llbp-author.html','llbp-author.txt','The Last-Level Branch Predictor\n','Warming Up a Cold Front-End','只读 MICRO 2024 条目和相邻边界，排除 HPCA 2026 Revisited。',False)
save('reading.json',{'recorded_at':NOW,'full_primary_abstracts_read':4,'body_pages_read':0,'paper_figures_read':0,'research_source_code_read':False,'author_site_metadata_js_read':True,'downloaded_code_executed':False,'matching_pdf_documents':3,'matching_pdf_pages_available':42,'new_matching_pdf_downloads':3,'images_actually_viewed':[{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-p1.png','sha256':sha(f'paper-{n:03d}-p1.png'),'actually_viewed':True,'scope':'题名、作者、完整摘要与出版标识；没有分析正文或图'} for n in [35,36,37]],'auxiliary_text_scopes':aux,'tool_only_observations':'UFC 搜索工具返回的完整形态摘要已观察但不计入原始一手归档完成数，详见 tool-observations.json。','counting_rule':'匹配 PDF 的全部可用页数、作者目录、脚本书目对象、索引摘要与 HTTP 200 验证页都不自动算完成正文/一手摘要阅读。'})
save('acquisition-notes.json',{'http_responses':16,'http_200':12,'http_202_empty':3,'http_504':1,'http_200_challenge_documents':1,'reused_input_files':7,'failures':[{'file':'llbp-record-504.response','status':504,'resolution':'保留原响应；已有作者 MICRO 2024 PDF，不重试 artifact。'},{'file':'ufc-publisher.response','status':202,'bytes':0},{'file':'ufc-publisher-slash.response','status':202,'bytes':0},{'file':'fpga-publisher.response','status':202,'bytes':0},{'file':'fpga-discovery-dblp-challenge.html','status':200,'resolution':'响应实际上是机器人验证 HTML，非请求的 XML；仅作失败发现路径，不算书目或摘要证据。'}],'version_cautions':version,'not_downloaded':['LLBP 代码、artifact 和 slides','HPCA 2026 的 LLBP Revisited','密码学编译框架的第三方实现或解读'],'no_secondary_substitute':'不使用 ResearchGate、J-GLOBAL、EurekaMag 摘录作为完整摘要。UFC 的搜索工具索引文本另记，不伪造 HTTP 状态或原始网页。','mutable_pages':'作者主页、JS bundle 和机构记录以保存字节、URL、抓取时间与 SHA 固定本次观察，没有声称 Git commit 固定。'})
