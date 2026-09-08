#!/usr/bin/env python3
"""Check MICRO 2024 identities, primary abstract proofs and selected page scope."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from bs4 import BeautifulSoup
import csv, hashlib, json, math, re, subprocess, sys
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'references/proceedings/MICRO/2024'
sys.path.insert(0, str(ROOT / 'references'))
from reconcile_micro2024 import normalized


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    m = json.loads((DEST/'manifest.json').read_text())
    for key in ['program', 'query']:
        assert sha(ROOT/m[key+'_file']) == m[key+'_sha256']
    nodes = BeautifulSoup((ROOT/m['program_file']).read_text(), 'html.parser').select('.paper')
    assert len(nodes) == 123 and len(m['excluded_program_events']) == 10
    assert {x['program_order'] for x in m['excluded_program_events']} == {10,20,33,34,50,60,70,83,90,100}
    for x in m['excluded_program_events']:
        assert x['title'] == nodes[x['program_order']-1].select_one('.paper-title').get_text(' ', strip=True)
        assert 'Posters' in x['title'] or 'PhD Forum' in x['title']
    q = json.loads((ROOT/m['query_file']).read_text())['message']
    assert len(q['items']) == m['query_returned_items'] == 250
    assert q['total-results'] == m['query_reported_total']
    relevant = [x for x in q['items'] if x['DOI'].startswith(m['doi_prefix'])]
    assert len(relevant) == 124 and not any(x.get('abstract') for x in relevant)
    papers = {p['program_order']:p for p in m['papers']}
    assert len(papers) == len({p['doi'] for p in papers.values()}) == 113
    variants = json.loads((DEST/'title-variants.json').read_text())
    assert variants['program_sha256'] == m['program_sha256'] and variants['query_sha256'] == m['query_sha256']
    reviews = {x['program_order']:x for x in variants['records']}
    assert len(reviews) == 12
    for n,p in papers.items():
        x = q['items'][p['metadata_source_index']]
        assert p['doi'] == x['DOI'] and p['publisher_title'] == x['title'][0] and p['publisher_authors'] == x['author']
        assert p['program_title'] == nodes[n-1].select_one('.paper-title').get_text(' ', strip=True)
        if p['identity_method'] == 'normalized_title_exact':
            assert normalized(p['program_title']) == normalized(p['publisher_title']) and n not in reviews
        else:
            v = reviews[n]
            assert p['doi'] == v['doi'] and p['publisher_title'] == v['publisher_title'] and p['publisher_authors'] == v['publisher_authors']
            assert p['program_title'] == v['program_title'] and p['program_authors'] == v['program_authors']
    assert len(m['front_back_matter']) == 11
    assert {x['doi'] for x in m['front_back_matter']} | {p['doi'] for p in papers.values()} == {x['DOI'] for x in relevant}
    sources = json.loads((DEST/'sources.json').read_text())
    assert len(sources) == 53 and sum(s['status_code'] != 200 for s in sources) == 4
    for s in sources:
        path = ROOT/s['file']
        assert sha(path) == s['sha256'] and path.stat().st_size == s['bytes']
        assert (s['reading_status'] == 'failed_response_not_evidence') == (s['status_code'] != 200)
    locations = json.loads((DEST/'public-location-map.json').read_text())['papers']
    assert len(locations) == 113 and {x['doi'] for x in locations} == {p['doi'] for p in papers.values()}
    for x in locations:
        assert sha(ROOT/x['source_file']) == x['source_sha256']
        deposited = json.loads((ROOT/x['source_file']).read_text())['results'][x['source_index']]
        assert deposited['doi'].lower() == 'https://doi.org/'+x['doi']
        assert x['openalex_id'] == deposited['id'] and x['locations'] == deposited['locations']
        assert papers[x['program_order']]['doi'] == x['doi']
    proof = json.loads((DEST/'public-abstracts.json').read_text())
    readings = proof['papers']
    assert not proof['downloaded_code_executed']
    initial_orders = {1,11,12,29,30,43,45,47,54,64,74,99,105,107,112}
    expanded_orders = {14,15,22,23,25,27,31,42,46,55,59,66,67,68,69,71,78,81,92,93,101,103,108,109,117,120}
    assert len(readings) == 41 and {p['program_order'] for p in readings} == initial_orders | expanded_orders
    expanded = json.loads((DEST/'expanded-abstracts.json').read_text())
    assert not expanded['downloaded_code_executed']
    assert {p['program_order'] for p in expanded['papers']} == expanded_orders
    assert expanded['papers'] == [p for p in readings if p['program_order'] in expanded_orders]
    with (ROOT/'research/2026-infra-survey/screening-micro-2024.tsv').open() as f:
        rows = {int(x['program_order']):x for x in csv.DictReader(f,delimiter='\t')}
    assert set(rows) == initial_orders | expanded_orders
    images = 0
    for item in readings:
        n = item['program_order']; p = papers[n]
        assert (p['doi'],p['publisher_title'],p['abstract'],p['screening'],p['reading_status']) == (item['doi'],item['publisher_title'],item['abstract'],item['screening'],item['reading_status'])
        assert item['read_scope']['complete_abstract'] and not item['read_scope']['body_read']
        assert item['screening']['basis'] == 'title_and_full_abstract'
        assert rows[n]['doi'] == p['doi'] and rows[n]['decision'] == p['screening']['decision'] and rows[n]['reason'] == p['screening']['reason']
        if item['source_kind'] == 'public_pdf':
            screen_key = 'screen_text' if n in expanded_orders else 'first_page'
            for key in ['pdf','full_text',screen_key]:
                assert sha(ROOT/item[key+'_file']) == item[key+'_sha256']
            pdf = ROOT/item['pdf_file']
            assert pdf.read_bytes().startswith(b'%PDF-') and pdf.stat().st_size == item['pdf_bytes']
            info = subprocess.check_output(['pdfinfo',str(pdf)],text=True,stderr=subprocess.PIPE)
            assert int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1]) == item['pdf_pages'] == p['pdf_pages']
            t = subprocess.check_output(['pdftotext','-f','1','-l',('2' if n in expanded_orders else '1'),str(pdf),'-'],text=True,stderr=subprocess.PIPE)
            assert t == (ROOT/item[screen_key+'_file']).read_text()
            start,end = item['abstract_char_range']; a = t[start:end]
            assert item['abstract_physical_pages'] == [2 if n == 93 else 1]
            assert t[:start].count('\f')+1 == item['abstract_physical_pages'][0]
            if n in {68,71}:
                assert not item['abstract_heading_present']
                prefix = 'RowHammer is a major read disturbance mechanism in DRAM' if n == 68 else 'The memory controller is in charge of managing DRAM maintenance operations'
                assert a.startswith(prefix)
            else:
                assert 'Abstract' in t[max(0,start-15):start]
            if n in expanded_orders:
                assert normalized(item['public_copy_title']) in normalized(t)
                nonperson = item.get('publisher_nonperson_entries', [])
                if nonperson:
                    assert n == 71 and len(nonperson) == 1
                    assert nonperson[0]['record'] == p['publisher_authors'][nonperson[0]['index']]
                    assert nonperson[0]['record']['given'] == 'ETH' and nonperson[0]['record']['family'] == 'Zurich'
                omitted = {x['index'] for x in nonperson}
                authors = [' '.join(x.get(k,'') for k in ['given','family']).strip() for i,x in enumerate(p['publisher_authors']) if i not in omitted]
                variants = item.get('reviewed_author_variants', {})
                if variants:
                    assert n == 92 and variants == {'Qinze Yang':'Qize Yang'}
                assert item['public_copy_authors'] == [variants.get(x,x) for x in authors]
                assert all(normalized(x) in normalized(t) for x in item['public_copy_authors'])
            if n == 99:
                reused = next(x for x in json.loads((ROOT/item['reused_manifest']).read_text()) if x['id'] == item['source_id'])
                assert 'references/'+reused['file'] == item['pdf_file'] and reused['sha256'] == item['pdf_sha256']
        else:
            assert n in {30,31} and sha(ROOT/item['source_file']) == item['source_sha256']
            soup = BeautifulSoup((ROOT/item['source_file']).read_text(),'html.parser')
            if n == 30:
                a = next(x.get_text(' ',strip=True) for x in soup.select('p') if x.get_text(' ',strip=True).startswith('Domain-specific hardware, coupled with co-designed algorithmic optimizations,'))
                assert soup.select_one('a[href="'+item['publisher_identity_link']+'"]')
            else:
                a = soup.select_one(item['selector']).get_text(' ',strip=True)
                assert soup.select_one('meta[name="citation_doi"]')['content'] == item['citation_doi']
                assert item['citation_doi'].lower() == p['doi']
                assert normalized(item['public_copy_title']) == normalized(p['publisher_title'])
                assert all(normalized(x) in normalized(soup.get_text(' ',strip=True)) for x in item['public_copy_authors'])
        assert a == item['abstract'] and hashlib.sha256(a.encode()).hexdigest() == item['abstract_sha256']
        if 'visual_identity_check' in item:
            im = item['visual_identity_check']; assert im['actually_viewed'] and im['physical_page'] == (2 if n == 93 else 1) and sha(ROOT/im['file']) == im['sha256']; images += 1
        if 'additional_abstract_source' in item:
            extra = item['additional_abstract_source']
            assert n == 103 and extra['complete_abstract_read'] and extra['not_additional_paper']
            assert sha(ROOT/extra['file']) == extra['sha256']
            extra_text = BeautifulSoup((ROOT/extra['file']).read_text(),'html.parser').select_one(extra['selector']).get_text(' ',strip=True)
            assert extra_text == extra['abstract'] and hashlib.sha256(extra_text.encode()).hexdigest() == extra['abstract_sha256']
            assert normalized(extra_text) == normalized(a)
    assert images == 13 and sum(p.get('pdf_pages',0) for p in readings) == 602
    assert sum(p.get('pdf_pages',0) for p in expanded['papers']) == 381
    assert sum(p['source_kind'] == 'public_pdf' for p in expanded['papers']) == 25
    # A same-name search result is an actual archived response, not this conference paper.
    wrong = next(s for s in sources if s['id'] == 'micro24-paper-025')
    assert wrong['reading_status'] == 'different_paper_identity_checked' and wrong['not_counted_as_MICRO']
    wrong_text = (DEST/'paper-025-screen.txt').read_text()
    assert '10.1145/3627703.3650072' in wrong_text and 'Compressed Multi-attribute' in wrong_text
    correct = next(p for p in readings if p['program_order'] == 25)
    assert correct['source_id'] == 'micro24-paper-025-fhe' and correct['pdf_file'] != wrong['file']
    selected = [p for p in readings if 'selected_reading' in p]
    assert len(selected) == 1 and selected[0]['program_order'] == 11
    r = json.loads((DEST/'mess-reading.json').read_text())
    assert selected[0]['selected_reading'] == papers[11]['selected_reading'] == r
    assert r['physical_pages'] == [3,4,5,6] and r['pdf_sha256'] == selected[0]['pdf_sha256']
    combined = ''
    for row in r['page_texts']:
        t = subprocess.check_output(['pdftotext','-layout','-f',str(row['page']),'-l',str(row['page']),str(ROOT/r['pdf_file']),'-'],text=True,stderr=subprocess.PIPE)
        assert t == (ROOT/row['file']).read_text() and sha(ROOT/row['file']) == row['sha256']; combined += t
    assert combined == (ROOT/r['text_file']).read_text() and sha(ROOT/r['text_file']) == r['text_sha256']
    for im in r['viewed_pages']:
        assert im['actually_viewed'] and sha(ROOT/im['file']) == im['sha256']
    assert Counter(p['screening']['decision'] for p in readings) == dict(candidate=15,reference=15,exclude=10,include=1)
    a = json.loads((ROOT/'research/2026-infra-survey/arithmetic.json').read_text())['memory_concurrency_teaching']
    c = json.loads((ROOT/a['config']).read_text())
    size = c['num_hidden_layers']*2*c['num_key_value_heads']*c['head_dim']*2*a['history_tokens']
    assert size == a['kv_bytes'] == 1207959552
    for row in a['scenarios']:
        bound = min(row['bandwidth_cap_bytes_s'],row['outstanding_transactions']*a['transaction_bytes']/row['latency_s'])
        assert math.isclose(bound,row['throughput_upper_bound_bytes_s'],rel_tol=1e-12)
        assert math.isclose(size/bound*1000,row['kv_service_lower_bound_ms'],rel_tol=1e-12)
    assert a['transactions_required_for_1tb_s'] == math.ceil(1e12*500e-9/128) == 3907
    report = dict(verified_at=datetime.now(timezone.utc).isoformat(),program_items=123,matched_papers=113,excluded_events=10,metadata_front_back=11,exact_titles=101,reviewed_variants=12,source_responses=53,failed_responses=4,unrelated_pdf_responses=1,secondary_locations_mapped=113,primary_abstracts_screened=41,remaining_abstracts=72,public_pdfs=39,new_pdfs=38,pdf_pages=602,expanded_batch_abstracts=26,expanded_batch_matching_pdfs=25,expanded_batch_pdf_pages=381,abstract_identity_images_viewed=images,selected_sections_read=1,selected_physical_pages=4,screening_decisions=dict(Counter(p['screening']['decision'] for p in readings)),arithmetic='passed',errors=[])
    (ROOT/'research/2026-infra-survey/micro2024-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__ == '__main__':
    print(json.dumps(verify(),ensure_ascii=False,indent=2))
