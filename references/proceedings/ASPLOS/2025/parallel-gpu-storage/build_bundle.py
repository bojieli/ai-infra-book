"""Build this local handoff; no network and no shared-index writes."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, re
from bundle_lib import ORDERS, PDFS, html, extract, identities, verify_identities, record_file, whitespace

base = Path(__file__).resolve().parent
repo = base.parents[4]
relative = Path('references/proceedings/ASPLOS/2025/parallel-gpu-storage')
def f(name):
    d = record_file(base, name); d['file'] = str(relative / name); return d

sources = []
for path in sorted(base.glob('sources-*.json.results.json')):
    for x in json.loads(path.read_text()):
        sources.append({**x, 'file': str(relative / x['file']),
                        'disposition': 'retained_failed_http_response' if x['status'] != 200 else 'primary_source_or_locator'})
by_name = {Path(s['file']).name: s for s in sources}
official = identities(base); checks = {x['program_order']: x for x in verify_identities(base)}
decisions = {
 173: '后续正文候选，仅限4.3.1/4.4.3：核矩阵单元与SIMT解耦如何改变寄存器访问、粒度及控制功耗。未核正文，不采用论文百分比作产品结论。',
 174: '本轮不增正文。与5.3.5正确性验证、5.4.5设备侧同步相关，但不是性能收益证据；保留延伸来源。',
 176: '不采用。Datalog静态分析/关系运算不同于本书学习模型负载，不把GPU数据结构性能移作LLM算子证据。',
 177: '后续正文候选，仅限9.5.2：比较多放副本如何减少物理页读取，强调DLRM embedding与LLM KV状态不是同类对象。',
 178: '不采用。键值SSD元数据随key/value尺寸变化的问题尚无直接AI工作负载证据，KV-SSD不等于LLM KV cache。',
 179: '不采用。RAM受限MCU的NOR文件系统与当前AI Infra主线距离较远；匿名工件稿不冒充出版版。'
}
versions = {
 173: 'arXiv:2408.12073v2; p1 carries official DOI and authors',
 174: 'Author-hosted 16-page manuscript; p1 carries official ASPLOS 2024 Vol.4 DOI and authors; presented in 2025 program',
 176: 'arXiv:2311.02206v5; 13-page preprint, formal paper is 15 pages; p1 no DOI; author publication links this arXiv paper under ASPLOS 2025',
 177: 'Author-hosted 15-page manuscript; p1 carries official ASPLOS 2024 Vol.4 DOI and authors; presented in 2025 program',
 178: 'Author institution ScholarlyArticle JSON-LD with formal DOI/title/full ordered authors and complete abstract',
 179: 'Anonymous 14-page author-artifact manuscript at fixed commit 30b997ad3b42fb8c02f344b08ae716d119f87042; formal publication is 15 pages; p1 no authors or DOI'
}
records = []
for order in ORDERS:
    x = official[order]; text, source, rule = extract(base, order)
    abstract_file = f'{order}-abstract.txt'; (base / abstract_file).write_text(text + '\n')
    row = {'program_order': order, 'doi': x['DOI'], 'title': x['title'][0],
      'authors': [a.get('given', '') + ' ' + a['family'] for a in x['author']],
      'source_file': str(relative / source), 'source_sha256': f(source)['sha256'],
      'source_url': by_name[source]['url'], 'extraction_kind': rule['kind'], 'extraction': rule,
      'version': versions[order], 'abstract': text, 'abstract_sha256': sha256(text.encode()).hexdigest(),
      'abstract_text_file': f(abstract_file), 'reading_status': 'full_abstract_read', 'read_date': '2026-09-09',
      'identity': checks[order], 'editorial_decision': decisions[order],
      'selected_reading': {'physical_pdf_pages': [], 'scope': 'Complete primary abstract and p1 identity only; no body section, no code or artifact evaluation.',
                           'page_text': {}, 'viewed_page_images': {}},
      'representative_pdf': None, 'version_notes': [versions[order]],
      'formal_container': x.get('container-title'), 'formal_page_range': x.get('page')}
    if order in PDFS:
        prefix = PDFS[order]; info = (base / (prefix + '.pdfinfo.txt')).read_text()
        pdf = {**f(prefix + '.pdf'), 'pages': int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1)),
          'first_page_text': {**f(prefix + '.first.txt'), 'pdftotext_mode': 'default'},
          'first_page_layout_text': {**f(prefix + '.first-layout.txt'), 'pdftotext_mode': 'layout'},
          'version_relation': versions[order], 'body_not_extracted': True}
        if order in [174, 179]: pdf['first_page_raw_text'] = {**f(prefix + '.first-raw.txt'), 'pdftotext_mode': 'raw'}
        row['representative_pdf'] = pdf
        row['selected_reading']['viewed_page_images']['1'] = {**f(prefix + '.p1.png'), 'actually_viewed': True,
          'scope': 'Title/authors/DOI if present and full abstract; other p1 material was not selected for body reading'}
    if order in [173, 176]:
        source_text = (base / source).read_text()
        hist = re.search(r'<div class="submission-history".*?</div>', source_text, re.S).group()
        row['submission_history_html'] = hist
    records.append(row)
old = whitespace(''.join(html(base, '173-arxiv-v1.html').abstract))
(base / '173-v1-abstract.txt').write_text(old + '\n')
bundle = {'scope': 'Six previously unread program identities; six primary full abstracts including one anonymous official-artifact draft; body reading remains zero.',
 'created_at': datetime.now(timezone.utc).isoformat(), 'selection': f('selection-snapshot.json'),
 'sources': sources, 'records': records, 'gaps': [], 'new_full_abstracts': 6,
 'representative_pdfs': 5, 'representative_pdf_pages': sum(r['representative_pdf']['pages'] for r in records if r['representative_pdf']),
 'selected_body_reading_records': 0, 'selected_body_physical_pages': 0,
 'abstract_identity_pages_read_separately': 5, 'actual_rendered_pages_viewed': 5, 'body_reading_is_full_paper': False,
 'additional_version_abstracts': [{'program_order': 173, 'version': 'arXiv:2408.12073v1',
   'source': f('173-arxiv-v1.html'), 'abstract_text_file': f('173-v1-abstract.txt'),
   'abstract_sha256': sha256(old.encode()).hexdigest(), 'adds_unique_paper_count': False}],
 'unresolved': [
   'All six publisher landing pages returned 403; none of these archived abstracts has been compared byte-for-byte with the publisher full abstract.',
   '179 anonymous artifact PDF p1 lacks authors/DOI and is 14 pages versus formal 15; explicit fixed README links the same title and file, but publisher equivalence is unverified.',
   '176 preprint is 13 pages versus formal 15 and HTML reverses last two authors; preserved as a version variant, not silently corrected.',
   'Four DOI endpoint requests returned 429. Formal identity is rechecked against a byte-identical archived original Crossref work-list; failed responses retained.'
 ]}
(base / 'reading-records.json').write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'records': len(records), 'pdfs': 5, 'pdf_pages': bundle['representative_pdf_pages'], 'body_pages': 0}))
