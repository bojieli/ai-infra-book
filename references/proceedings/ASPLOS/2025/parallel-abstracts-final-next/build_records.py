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

sources = []
for f in sorted(P.glob('*-jobs.json.results.json')):
    for row in json.loads(f.read_text()):
        row['file'] = str((P / Path(row['file']).name).relative_to(ROOT)); sources.append(row)

spec = {
    10: ('institution primary HTML abstract; formal publication 2025/03/30, portal online_date 2025/09/26', 'TFHE PIM 亲和性调度仅作搬移约束背景；4.24–209× 不是 AI 推理收益，不选正文。'),
    14: ('author-hosted publication-layout PDF, 17 pages; formal page range has 16 pages', '量子电路批模拟任务图仅作背景；三个速度比不能外推 LLM CUDA Graph 或推理服务，不选正文。'),
    16: ('author-hosted publication-layout PDF, 16 pages; revision unlabelled, bytes pinned by SHA256', '能量采集设备的充电/输入溢出调度仅备查；4.2× 指减少漏检事件，不是数据中心性能，不选正文。')
}
records = []
for n, (version, decision) in spec.items():
    e = entries[n]; authors = [a['given'] + ' ' + a['family'] for a in e['author_metadata']]
    if n == 10:
        f = P / '010-institution.html'; soup = BeautifulSoup(f.read_text(), 'html.parser')
        selector = '.rendering_researchoutput_abstractportal .textblock > p'
        abstract = ' '.join(soup.select_one(selector).get_text(' ', strip=True).split())
        extraction = {'kind': 'institution_html', 'selector': selector, 'normalization': 'get_text(" ",strip=True), collapse whitespace only; exclude duplicate BibTeX/RIS copies'}
        pdf = None; images = {}
    else:
        stem = f'{n:03d}-author-paper'; f = P / (stem + '.pdf')
        t = (P / (stem + '.first.txt')).read_text()
        abstract = ' '.join(t.split('Abstract', 1)[1].split('CCS Concepts:', 1)[0].split())
        extraction = {'kind': 'pdf_first_page', 'segments': [{'start': 'Abstract', 'end': 'CCS Concepts:', 'include_start': False, 'include_end': False}], 'command': 'pdftotext -f 1 -l 1 input.pdf - (default; no -raw/-layout)', 'normalization': 'Collapse whitespace only; do not repair hyphens, ligatures, punctuation, or citations.', 'excluded': 'No footer/intercolumn fragment within abstract. Right-column Introduction and copyright are outside selected span.'}
        pdf = pdfinfo(stem); images = {'1': {**proof(P / (stem + '.p1.png')), 'actually_viewed': True}}
    af = P / f'{n:03d}-abstract.txt'; af.write_text(abstract + '\n')
    identity = {'official_program_doi': e['doi'], 'program_order': n, 'presentation_year': 2025, 'formal_page_range': e.get('page'), 'publisher_title': e.get('publisher_title', e['title']), 'publisher_author_names': authors, 'author_aliases': {}, 'registry': proof(P / 'registry-original.json'), 'registry_selector': 'message.items exact DOI', 'pdf_title_authors_visually_verified': n != 10, 'pdf_official_doi_visually_verified': n != 10}
    if n == 10:
        identity['html_metadata'] = {'title': 'meta[name="citation_title"]', 'authors': 'meta[name="citation_author"] in original order', 'doi': 'meta[name="citation_doi"]', 'pages': ['citation_firstpage', 'citation_lastpage'], 'publication_date': '2025/03/30', 'online_date': '2025/09/26'}
    notes = {10: ['Original complete abstract from author institution record; no PDF retrieved. The portal online_date is not the conference date.'], 14: ['17 physical pages and first-page ACM Reference Format 17 pages differ from formal 79–94 (16 pages); no publisher-byte equivalence claimed.', 'Default extraction places two author names after footer; actual page image used to verify identity. Complete abstract itself contiguous.'], 16: ['16-page author-hosted publication-layout PDF matches formal page count; no publisher-byte equivalence asserted.', 'Original [23] citation and extracted endto-end retained without text repair.']}[n]
    records.append({'program_order': n, 'doi': e['doi'], 'title': e['title'], 'authors': authors,
        'source_file': str(f.relative_to(ROOT)), 'source_sha256': proof(f)['sha256'], 'source_url': next(s['url'] for s in sources if s['file'] == str(f.relative_to(ROOT))),
        'extraction_kind': extraction['kind'], 'extraction': extraction, 'version': version, 'history': None,
        'abstract': abstract, 'abstract_sha256': hashlib.sha256(abstract.encode()).hexdigest(), 'abstract_text_file': proof(af), 'reading_status': 'full_abstract_read', 'read_date': '2026-09-09', 'identity': identity, 'representative_pdf': pdf,
        'selected_reading': {'physical_pdf_pages': [], 'scope': 'Complete primary abstract and source identity only; PDF p1 images actually viewed for 14/16. No body reading; mechanically archived full text is not read-body evidence.', 'page_text': {}, 'viewed_page_images': images},
        'body_reading_candidate_priority': 'not_selected', 'editorial_decision': decision, 'version_notes': notes})

gaps = []
for n in [1, 2, 5]:
    e = entries[n]
    gap = {'program_order': n, 'doi': e['doi'], 'title': e['title'], 'authors': [a['given'] + ' ' + a['family'] for a in e['author_metadata']], 'reading_status': 'primary_abstract_unavailable', 'full_abstract_read': False, 'representative_pdf': None, 'body_pages_read': [], 'identity_source': proof(P / 'registry-original.json'), 'identity_selector': 'message.items exact DOI; no abstract field', 'failed_source_ids': [s['id'] for s in sources if s['id'].startswith(f'{n:03d}-') and s['status_code'] != 200], 'body_reading_candidate_priority': 'undetermined_until_primary_abstract', 'editorial_decision': '原始完整摘要缺口；不得据题名、README 或搜索片段设正文候选。'}
    if n == 1:
        gap.update({'author_publication_pages': [proof(P / '001-author-home.html'), proof(P / '001-author-publications.html')], 'single_crossref': proof(P / '001-crossref.html'), 'reason': 'Crossref has no abstract; author pages locate title/authors but no original abstract or this paper PDF; ACM landing and PDF HTTP403. Formal Crossref author name Jiang Jie retained.'})
    else:
        commit = json.loads((P / f'{n:03d}-artifact-commit.html').read_text())['sha']
        gap.update({'artifact_locator': {'repository': 'coralabo/DynaX' if n == 2 else 'gt-tinker/RASSM', 'commit': commit, 'commit_metadata': proof(P / f'{n:03d}-artifact-commit.html'), 'tree': proof(P / f'{n:03d}-artifact-tree.html'), 'readme': proof(P / f'{n:03d}-artifact-readme.html'), 'read_scope': 'Static README and recursive tree for locating paper; no source code downloaded or executed; README not counted as paper abstract.'}, 'reason': 'Single Crossref HTTP429 zero-byte; archived primary registry verifies identity and no abstract. ACM landing/PDF HTTP403. Fixed artifact README is not original abstract; complete tree snapshot contains no PDF.'})
    gaps.append(gap)

out = {'scope': 'Assigned unread orders 1,2,5,10,14,16; complete primary abstracts and identity only. No body reading, shared index, outline or Git changes.', 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'selection': proof(P / 'selection-snapshot.json'), 'sources': sources, 'local_copy_provenance': proof(P / 'local-copy-provenance.json'), 'records': records, 'gaps': gaps, 'new_full_abstracts': 3, 'representative_pdfs': 2, 'representative_pdf_pages': 33, 'selected_body_reading_records': 0, 'selected_body_physical_pages': 0, 'abstract_identity_pages_read_separately': 2, 'actual_rendered_pages_viewed': 2, 'body_reading_is_full_paper': False, 'notes': proof(P / 'READINGS.md'), 'unresolved': ['Original complete abstracts remain unavailable for 1,2,5; failed responses and static author locators retained.', '10 has institution abstract only, no PDF.', '14 author PDF has 17 pages while formal range has 16; no exact publisher equivalence.', 'Four genuine zero-byte Crossref429 and seven ACM403 responses retained; no failure text accepted as abstract.']}
(P / 'reading-records.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print('Packaged 3 abstracts, 2 PDFs, 33 archived pages, 0 body pages, 3 gaps.')
