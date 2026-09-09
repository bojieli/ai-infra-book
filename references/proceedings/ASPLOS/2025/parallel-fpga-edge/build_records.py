from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
from bs4 import BeautifulSoup

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
entries = {r['program_order']: r for r in json.loads((P.parent / 'manifest.json').read_text())['papers']}

def proof(f):
    f = Path(f); b = f.read_bytes()
    return {'file': str(f.relative_to(ROOT)), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def pdfinfo(stem):
    f = P / (stem + '.pdf')
    n = int(re.search(r'^Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', str(f)], text=True), re.M).group(1))
    return {**proof(f), 'pages': n, 'text': proof(P / (stem + '.txt')), 'layout_text': proof(P / (stem + '.layout.txt')), 'first_page_text': proof(P / (stem + '.first.txt'))}

def segment(t, start, end, include_start=False, include_end=False):
    a = t.index(start); b = t.index(end, a + len(start))
    return t[a if include_start else a + len(start):b + len(end) if include_end else b]

sources = []
for f in sorted(P.glob('*-jobs.json.results.json')):
    for row in json.loads(f.read_text()):
        row['file'] = str((P / Path(row['file']).name).relative_to(ROOT)); sources.append(row)

spans = {
    29: [{'start': 'CPU-FPGA heterogeneous architectures', 'end': 'ACM Reference Format:', 'include_start': True}, {'start': 'IP, Salus presents', 'end': 'CPU-FPGA heterogeneous architectures', 'include_start': True}],
    30: [{'start': 'Abstract', 'end': 'Permission to make digital'}, {'start': 'hardware differences and a platform-independent layer', 'end': 'CCS Concepts:', 'include_start': True}],
    31: [{'start': 'Cloud FPGAs, with their scalable and flexible nature,', 'end': '13× faster, and costs 92% less than the state-of-the-art.', 'include_start': True, 'include_end': True}],
}
spec = {
    19: ('institution primary HTML record, formal 2025 publication', '立体 VR 的压缩/重建取舍仅作背景；90FPS 和20%–40%带宽收益不能外推 computer-use 截图或模型推理，不选正文。'),
    25: ('SFU institution research-output API, exact DOI object, source section Scopus Publications', '动态数据结构的 key-range 同步背景；2kb/256kb 单位照原文，6.6%是能量需求比例，不能当作 KV cache 或 attention 收益，不选正文。'),
    29: ('author camera-ready publication-layout PDF, ASPLOS2024 Volume4, 15 pages; presented in2025 program', 'CPU–FPGA TEE 的 bitstream 保护背景；不是 Agent sandbox，摘要无性能数字，不选正文。'),
    30: ('author-hosted ASPLOS2025 publication-layout PDF,17 pages; webpage month August2024 retained separately', '异构 FPGA 的 shell/role/host 软件适配背景；开发量、资源量与配置量减少不能混同运行速度，不选正文。'),
    31: ('Virginia Tech institution-hosted publication-layout PDF,14 pages', '云 FPGA 指纹识别与安全背景，分类准确率和13×识别速度不是 LLM 服务收益；仅存档排除，不选正文。'),
}
records = []
for n, (version, decision) in spec.items():
    e = entries[n]; authors = [a['given'] + ' ' + a['family'] for a in e['author_metadata']]
    pdf = None; images = {}
    if n == 19:
        f = P / '019-institution.html'; soup = BeautifulSoup(f.read_text(), 'html.parser')
        selector = '.rendering_researchoutput_abstractportal .textblock > p'
        abstract = ' '.join(soup.select_one(selector).get_text(' ', strip=True).split())
        extraction = {'kind': 'institution_html', 'selector': selector, 'normalization': 'get_text(" ",strip=True), collapse whitespace only; exclude duplicate citation fields'}
    elif n == 25:
        f = P / '025-institution-api-filtered.html'; data = json.loads(f.read_text())
        obj = next(r for r in data['results'] if r['DOI'] == e['doi'])
        abstract = obj['abstract']
        extraction = {'kind': 'institution_json', 'selector': 'results[DOI == "10.1145/3669940.3707225"].abstract', 'normalization': 'Exact decoded JSON string; no whitespace, word, unit or punctuation repair.', 'source_field_label': 'Scopus Publications on the author institution research-output page', 'route_evidence': proof(P / '025-institution-script.html')}
    else:
        stem = f'{n:03d}-' + ('institution-paper' if n == 31 else 'author-paper')
        f = P / (stem + '.pdf'); t = (P / (stem + '.first.txt')).read_text()
        abstract = ' '.join(' '.join(segment(t, **s) for s in spans[n]).split())
        extraction = {'kind': 'pdf_first_page', 'segments': spans[n], 'command': 'pdftotext -f 1 -l 1 input.pdf - (default; no -raw/-layout)', 'normalization': 'Collapse whitespace only after explicit span ordering.', 'excluded': {29: 'Move right-column two-line ending from before abstract main text to after it; exclude ACM citation, author footnote and copyright.', 30: 'Exclude copyright/footer block inserted between left and right abstract columns; keep both complete text spans.', 31: 'Exclude right-column CCS text inserted after Abstract heading; start at complete first sentence and stop at complete final sentence.'}[n]}
        pdf = pdfinfo(stem); images = {'1': {**proof(P / (stem + '.p1.png')), 'actually_viewed': True}}
    af = P / f'{n:03d}-abstract.txt'; af.write_text(abstract + '\n')
    identity = {'official_program_doi': e['doi'], 'program_order': n, 'presentation_year': 2025, 'formal_page_range': e['page'], 'formal_volume_title': e['volume_title'], 'formal_publication_date': e['volume_publication_date'], 'publisher_title': e.get('publisher_title', e['title']), 'publisher_author_names': authors, 'author_aliases': {}, 'registry': proof(P / 'registry-original.json'), 'registry_selector': 'message.items exact DOI', 'pdf_title_authors_visually_verified': n in [29,30,31], 'pdf_official_doi_visually_verified': n in [29,30,31]}
    notes = []
    if n == 19:
        identity['html_author_aliases_to_formal'] = {'Mahmut Kandemir': 'Mahmut T. Kandemir', 'Chitaranjan Das': 'Chita R. Das'}
        identity['author_home'] = proof(P / '019-author-home.html')
        notes = ['Institution complete original abstract only, no PDF. Two institution author spellings differ from formal names; ordered alias mapping explicit.', 'Author publication row PDF URL is https://todo.pdf placeholder, not requested. ACM PDF403 retained.']
    elif n == 25:
        identity['institution_page'] = proof(P / '025-institution.html')
        identity['institution_author_initials'] = ['Kumar A.M.A.', 'Prasanna A.', 'Shriraman A.']
        identity['institution_faculty_uuid'] = '709feea8-933d-44c0-b8f5-455897edbb45'
        notes = ['Primary complete abstract is the exact institution-hosted API abstract field; formal author full names/DOI supplied by primary registry. No PDF.', 'Static app HTML has no abstract. Static JS inspected only to locate public API; no JS executed.', 'First unrecognized sfu_authors filter returned unrelated HTTP200 results without target DOI; retained but excluded. Correct sfu_authors__random_id response has exact target; other returned papers not read.', 'Original neces- sary, 2kb, 256kb and require6.6% preserved without repair.']
    elif n == 29:
        notes = ['Formal ASPLOS2024 Volume4 identity preserved separately from2025 presentation program. Author camera-ready15-page PDF matches formal252–266; no publisher-byte equivalence claimed.', 'Complete abstract assembled left-column body then right-column two-line ending, based on actual page-image review.']
    elif n == 30:
        identity['author_page'] = proof(P / '030-author-page.html')
        notes = ['17-page author publication-layout PDF matches formal498–514; exact title/all12authors/DOI p1. No publisher-byte equivalence claim.', 'Author page labels August2024, PDF labels ASPLOS2025; do not substitute page date for formal publication date.', 'Canonical PDF abstract excludes intervening copyright block. Author HTML abstract also retained/read; it spells final multiplier15-23x versus PDF15-23×.']
    else:
        notes = ['14-page institution PDF matches formal831–844 with exact p1 title,bothauthors,DOI; no publisher-byte equivalence claim.', 'Complete left-column abstract selected with sentence anchors; right-column CCS/citation not included.']
    records.append({'program_order': n, 'doi': e['doi'], 'title': e['title'], 'authors': authors, 'source_file': str(f.relative_to(ROOT)), 'source_sha256': proof(f)['sha256'], 'source_url': next(s['url'] for s in sources if s['file'] == str(f.relative_to(ROOT))), 'extraction_kind': extraction['kind'], 'extraction': extraction, 'version': version, 'history': None, 'abstract': abstract, 'abstract_sha256': hashlib.sha256(abstract.encode()).hexdigest(), 'abstract_text_file': proof(af), 'reading_status': 'full_abstract_read', 'read_date': '2026-09-09', 'identity': identity, 'representative_pdf': pdf, 'selected_reading': {'physical_pdf_pages': [], 'scope': 'Complete primary abstract/source identity only. For29/30/31 actual p1 image review; full text mechanically archived but not body-read.', 'page_text': {}, 'viewed_page_images': images}, 'body_reading_candidate_priority': 'not_selected', 'editorial_decision': decision, 'version_notes': notes})

e = entries[32]
gap = {'program_order': 32, 'doi': e['doi'], 'title': e['title'], 'authors': [a['given'] + ' ' + a['family'] for a in e['author_metadata']], 'reading_status': 'primary_abstract_unavailable', 'full_abstract_read': False, 'representative_pdf': None, 'body_pages_read': [], 'identity_source': proof(P / 'registry-original.json'), 'identity_selector': 'message.items exact DOI; no abstract field', 'author_publication_page': proof(P / '032-author-publications.html'), 'different_event_source': proof(P / '032-different-event.html'), 'different_event_exclusion': {'heading_selector': 'h3#P2\\.1\\.01-Wed', 'title': 'Hassert: Hardware Assertion-Based Agile Verification Framework with FPGA Acceleration', 'authors': ['Ziqing Zhang','Weijie Weng','Yungang Bao','Kan Shi'], 'event': 'RISC-V Summit Europe2025', 'not_original_asplos_abstract': True, 'pdf_downloaded': False}, 'failed_source_ids': ['032-publisher', '032-publisher-paper'], 'reason': 'Primary registry has no abstract; author list is metadata only with no per-paper link. ACM landing/PDF403. RISC-V Summit item is a different Agile title/four-author extended abstract, not the original eight-author ASPLOS abstract.', 'body_reading_candidate_priority': 'undetermined_until_primary_abstract', 'editorial_decision': '保留 ASPLOS 原始摘要缺口；不将另一会议四作者扩展摘要代替八作者原文。'}
out = {'scope': 'Assigned unread orders19,25,29,30,31,32; complete primary abstracts and identity only, no body/shared-index/outline/Git changes.', 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'selection': proof(P / 'selection-snapshot.json'), 'sources': sources, 'local_copy_provenance': proof(P / 'local-copy-provenance.json'), 'records': records, 'gaps': [gap], 'new_full_abstracts': 5, 'representative_pdfs': 3, 'representative_pdf_pages': 46, 'selected_body_reading_records': 0, 'selected_body_physical_pages': 0, 'abstract_identity_pages_read_separately': 3, 'actual_rendered_pages_viewed': 3, 'body_reading_is_full_paper': False, 'notes': proof(P / 'READINGS.md'), 'unresolved': ['32 original ASPLOS abstract/PDF remains unavailable; different-event extended abstract excluded.', '19/25 original institution abstracts only, no PDF;19 author PDF link placeholder not requested.', '25 initial incorrect filter HTTP200 source has no target DOI; not read/count evidence.', '29 and32 formal ASPLOS2024 Volume4 identities preserved within2025 presentation program.']}
(P / 'reading-records.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print('Packaged5 full abstracts,3 PDFs,46 archived pages,0 body pages,1 gap.')
