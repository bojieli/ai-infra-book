"""Build local reading records from preserved bytes; no downloaded code is run."""
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
    (D / f).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


original = {p['program_order']: p for p in load('input-manifest.json')['papers']}
sources = {p['file']: p for p in load('sources.json')}
light = next(p for p in load('fourth-batch-sources.json') if p['file'] == 'identity-mismatch-nsf-10590071.pdf')
sources['paper-016.pdf'] = light
description = {
    16: ('exclude', 'WSP 以编译器恢复区域、寄存器检查点与电池支持的 WPQ 保证断电一致性；摘要报告 38 个应用、平均 9.0% 运行开销与 0.5 B/core 额外硬件状态。它处理持久内存中的整机状态，不能拿来证明 GPU 训练检查点或 KV cache 持久化成本。', '与本书主要模型—硬件约束主线距离较远，本轮排除正文补读。'),
    17: ('reference', '将小延迟故障与粒子撞击故障分开，提出 DelayAVF，并在开源 RISC-V 核上分析；摘要明确传统 AVF 不足以描述新增电路时序与状态依赖。', '只作为第 4 章硬件可靠性的备查；不把 RISC-V 核的结果外推为 GPU 集群故障率，不新增章节或实验。'),
    18: ('exclude', '复用同一冗余信息对多种物理故障模型迭代纠错，并将 MAC 与 cache line 内联；摘要设定包括 64 B cache line、标准 40-bit DDR5 channel 与至多 60-bit MAC。', '物理内存纠错不是模型量化误差；本书不展开 ECC 编码细节，本轮排除正文补读。'),
    24: ('reference', 'GDDR 的 in-band ECC 额外访问会消耗有效带宽；CacheCraft 调整 cache sector 表示，使数据与其冗余信息能够一次访问取得。摘要中的平均额外带宽需求由 41.9% 到 21.9% 是作者评估口径，尚未读正文基线和配置。', '第 4 章有效内存带宽的备查，不视为 HBM、所有 GPU 或现售芯片的通用开销，也不据摘要增加性能算例。'),
}
versions = {
    16: 'NSF 公共归档 PDF，16 物理页，首页 MICRO 2024、印刷页 215、DOI .00025；PDF 生成日期为 2025-05-14，不能当成会议日期。上批因误匹配 GECKO 下载并暴露过首页文字，本批正式核对正确身份、看首页并筛读摘要；复用原字节，未重复下载。',
    17: 'Mengjia Yan 的 MIT 个人目录公开稿，15 物理页。首页题名和六名作者匹配；PDFExpress 元数据标记 2024-09-20，文件 CreationDate 为 2024-09-21 +08。没有声明版本号，不称 publisher VoR。',
    18: '第一作者公开 pec-preprint.pdf，17 物理页；首页题名与两名作者匹配。作者首页记录 2024-10-09 发布 preprint/artifact，当前 PDF 元数据生成于 2024-10-17；公告日期不能作为当前字节版本日期，无显式版本号。',
    24: '作者所属 Sungkyunkwan University 的机构记录：完整 Abstract、五名作者、会议、324–337 页及 DOI .00032 相符。该记录不是公开 PDF；作者实验室 Paper 指向 IEEE，另有 slides，未把 slides 算作论文。',
}
papers = []
for n in [16, 17, 18, 24]:
    p = {k: original[n][k] for k in ['program_order', 'doi', 'program_title', 'publisher_title', 'publisher_authors', 'publication_date']}
    if n == 24:
        source = 'cachecraft-institution.html'
        textfile = 'cachecraft-institution.txt'
        text = (D / textfile).read_text()
        start = text.index('Abstract\n') + len('Abstract\n')
        end = text.index('\nOriginal language', start)
        pages = 0
        extraction = {'kind': 'BeautifulSoup visible text', 'script_style_removed': True, 'separator': '\n', 'newlines': 'CRLF and CR normalized to LF'}
    else:
        source = f'paper-{n:03d}.pdf'
        textfile = f'paper-{n:03d}-left-column.txt'
        text = (D / textfile).read_text()
        start = text.index('Abstract—')
        end = text.index('\nIndex Terms', start) if n == 18 else text.index('\nI. I NTRODUCTION', start)
        while text[end - 1].isspace():
            end -= 1
        pages = int(re.search(r'^Pages:\s+(\d+)', (D / f'paper-{n:03d}-info.txt').read_text(), re.M).group(1))
        extraction = {'kind': 'pdftotext first physical page left-column crop', 'command': ['pdftotext', '-f', '1', '-l', '1', '-x', '0', '-y', '0', '-W', '306', '-H', '792', source, '-'], 'source_text': textfile, 'corrections': []}
    abstract = text[start:end]
    abstract_file = f'abstract-{n:03d}.txt'
    (D / abstract_file).write_text(abstract + '\n')
    decision, summary, reason = description[n]
    p.update(source_file=source, source_sha256=sha(source), source_url=sources[source]['url'], source_retrieved_at=sources[source]['retrieved_at'], source_kind='author/institution-hosted PDF' if pages else 'author institutional publication record', pdf_pages=pages, version_identity=versions[n], extraction=extraction, abstract_text_file=textfile, abstract_text_sha256=sha(textfile), abstract_char_range=[start, end], abstract=abstract, abstract_sha256=hashlib.sha256(abstract.encode()).hexdigest(), abstract_file=abstract_file, read_scope={'complete_abstract': True, 'physical_page': 1 if pages else None, 'body_read': False, 'figures_read': False, 'pdf_identity_checked_by_image': bool(pages)}, screening={'decision': decision, 'summary_zh': summary, 'reason_zh': reason, 'outline_changed': False, 'body_followup_recommended': False})
    papers.append(p)

unavailable = []
for n, why, files in [
    (13, '作者目录列题名、作者、会议、页码，Paper 指向 IEEE 10764651；IEEE 返回 HTTP 202 空响应。Zenodo 是 Software v1.1.4，不含论文完整摘要；README 的 Paper Details 只有题名与会议。未取得可核验一手完整摘要或 PDF。', ['hyfiss-author.html', 'hyfiss-publisher.response', 'hyfiss-record.json', 'hyfiss-readme.md']),
    (19, '作者实验室 publication.md 的 DRCTL 条目匹配题名、七名作者和 MICRO 2024，唯一论文链接为 IEEE 10764631，返回 HTTP 202 空响应。未取得一手完整摘要或公开 PDF。', ['drctl-author-pubs.md', 'drctl-publisher.response']),
]:
    unavailable.append({'program_order': n, 'doi': original[n]['doi'], 'title': original[n]['program_title'], 'abstract_read': False, 'pdf_pages': 0, 'body_read': False, 'reason': why, 'evidence_files': files, 'relevance': '未读完整摘要，不根据题名或二手自动摘要作技术候选判断。'})

save('abstracts.json', {'generated_at': NOW, 'scope': 'MICRO2024 fifth batch; complete primary abstracts only; no body reading', 'locked_program_orders': [13, 16, 17, 18, 19, 24], 'input_manifest_sha256': sha('input-manifest.json'), 'input_reading_coverage_sha256': sha('input-reading-coverage.json'), 'prior_batch_snapshots': [{'file': f'input-batch-{i}.json', 'sha256': sha(f'input-batch-{i}.json')} for i in range(1, 5)], 'papers': papers, 'unavailable': unavailable})

aux = []
def scope(source, textfile, first, last, reason, include_last=True):
    text = (D / textfile).read_text()
    a = text.index(first)
    z = text.index(last, a) + (len(last) if include_last else 0)
    aux.append({'source_file': source, 'file': textfile, 'sha256': sha(textfile), 'char_range': [a, z], 'line_range': [text.count('\n', 0, a) + 1, text.count('\n', 0, z) + 1], 'text': text[a:z], 'purpose': reason})

scope('hyfiss-author.html', 'hyfiss-author.txt', 'HyFiSS: A Hybrid Fidelity', '168-185.', '作者条目与出版身份，非完整摘要。')
scope('hyfiss-readme.md', 'hyfiss-readme.md', 'The source code', '## Prerequisites', '只读简介与 Paper Details；未读/执行构建说明或源码。', False)
scope('drctl-author-pubs.md', 'drctl-author-pubs.md', '- **[MICRO]** **[DRCTL', 'Taoming Lei, Dan Feng, Wei Tong.', '实验室目录的题名、作者、会议与唯一论文链接。')
scope('pec-author.html', 'pec-author.txt', '2024\nOct 09', "was accepted to MICRO-2024!", 'preprint 公告与 MICRO 接收身份。')
text = (D / 'cachecraft-author-pubs.txt').read_text()
a = text.index('[C25]'); z = text.index('Nov. 2024', a) + len('Nov. 2024')
aux.append({'source_file': 'cachecraft-author-pubs.html', 'file': 'cachecraft-author-pubs.txt', 'sha256': sha('cachecraft-author-pubs.txt'), 'char_range': [a,z], 'line_range': [text.count('\n',0,a)+1,text.count('\n',0,z)+1], 'text':text[a:z], 'purpose':'作者实验室 C25 条目身份；附近链接只定位 IEEE 与 slides，不读 slides。'})
for item in aux:
    item['range_text_normalization'] = 'UTF-8 decoded with CRLF and CR normalized to LF; byte hash remains original file hash'

save('reading.json', {'recorded_at': NOW, 'full_primary_abstracts_read': 4, 'body_pages_read': 0, 'source_code_read': False, 'downloaded_code_executed': False, 'matching_pdf_documents': 3, 'matching_pdf_pages_available': 48, 'new_matching_pdf_downloads': 2, 'reused_matching_pdf_documents': 1, 'images_actually_viewed': [{'program_order':n,'physical_page':1,'file':f'paper-{n:03d}-p1.png','sha256':sha(f'paper-{n:03d}-p1.png'),'actually_viewed':True,'scope':'题名、作者、完整 Abstract 与可见出版标识；未分析正文或图'} for n in [16,17,18]], 'auxiliary_text_scopes':aux, 'metadata_fields_read':[{'file':f,'sha256':sha(f),'fields':['metadata.title','metadata.doi','metadata.publication_date','metadata.version if present','metadata.description if present','metadata.creators','metadata.resource_type','metadata.custom.code:codeRepository','files key/size'],'not_paper_abstract':True} for f in ['hyfiss-record.json','delayavf-record.json']], 'prior_exposure': {'program_order':16,'previous_batch_role':'错误匹配 GECKO 时暴露过首页提取文字并用于身份拒绝，未正式筛读/未计数。','current_role':'正确条目正式摘要筛读与实际首页看图；复用字节并保留原来源桥接。'}, 'counting_rule':'未取得的 13/19、artifact 元数据、README、404/202 响应以及 PDF 正文可用页数均不算完成摘要或正文阅读。'})
save('acquisition-notes.json', {'http_responses':13,'http_200':10,'http_202_empty':2,'http_404':1,'reused_input_files':8,'failures':[{'file':'delayavf-author-404.response','status':404,'resolution':'保留 HTML 原响应；随后从另一共同作者 MIT 目录取得 paper-017.pdf。'},{'file':'drctl-publisher.response','status':202,'bytes':0,'resolution':'保留空响应，摘要未读。'},{'file':'hyfiss-publisher.response','status':202,'bytes':0,'resolution':'保留空响应，摘要未读。'}],'version_cautions':versions,'not_downloaded':['HyFiSS Zenodo 的 15.3 GB micro57.tar.gz、562 MB results、790 MB simulator-apps','DelayAVF artifact ZIP','CacheCraft slides；slides 不代替论文完整摘要'],'no_secondary_substitute':'搜索结果出现 ResearchGate/J-GLOBAL 等，但未用二手或机器翻译记录填入摘要。','mutable_pages':'作者主页、README 和实验室目录仅以本包 URL、抓取时间及原字节 hash 固定本次观察，不声称固定 Git commit。'})
