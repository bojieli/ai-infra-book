#!/usr/bin/env python3
"""Offline, read-only verification. Run from repository root; no downloaded code is run."""
from __future__ import annotations
import argparse
import ast
import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from bs4 import BeautifulSoup

ORDERS = {151: '10.1145/3676641.3716269', 152: '10.1145/3676641.3716249', 182: '10.1145/3669940.3707256'}
PAGES = {151: [4, 5, 6, 7, 8], 152: [5, 9, 10, 11], 182: [5, 6, 7, 8, 9, 13, 14]}
PDF_PAGES = {151: 17, 152: 16, 182: 18}
PINS = {
    151: ('qiaolian9/Pruner', '0760c3f39d84b31b4b10c4d7971ff402f2c350ae', 'README.md'),
    152: ('apache/tvm', '40c2f54908e96875fa19e92db83f123854d97991', 'python/tvm/relax/transform/transform.py'),
    182: ('microsoft/vattention', '71a0e91aa46ff8fa985bcca3327efe0ab9929a39', 'README.md'),
}
EXPECTED_SOURCE_IDS = {
    'pruner-v3', 'pruner-v3-abstract', 'relax-author', 'relax-arxiv', 'vattention-abstract',
    'vattention', 'pruner-github', 'vattention-github', 'tvm-github', 'pruner-github-master',
    'vattention-source', 'tvm-source', 'pruner-source',
}
PREFIX = 'asplos25-followup-'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def normalized(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKC', text).lower())

def need(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, help='Override repository root for a relocated checkout.')
    parser.add_argument('--json', action='store_true', help='Emit the full machine-readable report to stdout.')
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    root = (args.repo_root or directory.parents[4]).resolve()
    checks, warnings, stats = [], [], {}

    def run(name, action):
        try:
            detail = action()
            checks.append({'name': name, 'passed': True, 'detail': detail})
        except Exception as exc:
            checks.append({'name': name, 'passed': False, 'error': f'{type(exc).__name__}: {exc}'})

    def local(name):
        f = (root / name).resolve()
        need(f.is_relative_to(directory), f'Artifact path outside this package: {name}')
        return f

    def proof(item):
        data = local(item['file']).read_bytes()
        need(len(data) == item['bytes'], f"Byte count mismatch: {item['file']}")
        need(digest(data) == item['sha256'], f"SHA256 mismatch: {item['file']}")
        return data

    try:
        bundle = json.loads((directory / 'reading-records.json').read_text())
        manifest = json.loads((root / 'references/proceedings/ASPLOS/2025/manifest.json').read_text())['papers']
        records = {r['program_order']: r for r in bundle['records']}
        sources = {s['id']: s for s in bundle['sources']}
    except Exception as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        return 1

    def all_proofs():
        count, paths = 0, set()
        def visit(value):
            nonlocal count
            if isinstance(value, dict):
                if {'file', 'bytes', 'sha256'} <= value.keys():
                    proof(value)
                    count += 1
                    paths.add(value['file'])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(bundle)
        stats.update(file_proofs=count, unique_artifact_paths=len(paths))
        return {'file_proofs': count, 'unique_paths': len(paths)}
    run('all_artifact_bytes_and_hashes', all_proofs)

    def source_states():
        need(len(sources) == len(bundle['sources']) == 13, 'Expected 13 unique captured sources')
        need(set(sources) == {PREFIX + i for i in EXPECTED_SOURCE_IDS}, 'Unexpected/missing source IDs')
        logs = {}
        for f in sorted(directory.glob('download*.json.results.json')):
            for entry in json.loads(f.read_text()):
                need(entry['id'] not in logs, 'Repeated download ID')
                logs[entry['id']] = entry
        need(set(logs) == EXPECTED_SOURCE_IDS, 'Raw download logs differ from source table')
        for sid, record in sources.items():
            key = sid.removeprefix(PREFIX)
            original = logs[key]
            for field in ['url', 'final_url', 'status_code', 'bytes', 'sha256', 'retrieved_at', 'program_order']:
                need(record[field] == original[field], f'{key}: raw log mismatch in {field}')
            # Old logs record the original absolute checkout. Validate the basename without trusting that path.
            need(Path(original['file']).name == Path(record['file']).name, f'{key}: filename mismatch')
            datetime.datetime.fromisoformat(record['retrieved_at'])
            data = proof(record)
            expected_status = 422 if key == 'pruner-github' else 200
            need(record['status_code'] == expected_status, f'{key}: unexpected HTTP status')
            if key == 'pruner-github':
                response = json.loads(data)
                need(response['status'] == '422' and response['message'] == 'No commit found for SHA: main', 'Failed branch lookup not retained')
            elif key in ['pruner-v3', 'relax-author', 'vattention']:
                need(data.startswith(b'%PDF-'), f'{key}: successful response is not a PDF')
            elif key in ['pruner-v3-abstract', 'relax-arxiv', 'vattention-abstract']:
                need(BeautifulSoup(data, 'html.parser').select_one('blockquote.abstract') is not None, f'{key}: missing actual abstract DOM')
            elif 'github' in key:
                need(re.fullmatch('[0-9a-f]{40}', json.loads(data)['sha']) is not None, f'{key}: invalid commit payload')
        stats.update(source_responses=13, successful_responses=12, retained_failed_responses=1)
        return 'Recorded response statuses/URLs/bytes agree with original download logs; offline consistency, not a fresh network attestation.'
    run('source_bytes_status_and_raw_capture_logs', source_states)

    def identities_and_abstracts():
        need(set(records) == set(ORDERS) and len(bundle['records']) == 3, 'Unexpected DOI/order set')
        details = []
        for order, doi in ORDERS.items():
            r = records[order]
            matches = [m for m in manifest if m['doi'].lower() == doi]
            need(len(matches) == 1, f'{doi}: formal manifest identity is not unique')
            formal = matches[0]
            need(formal['program_order'] == order == r['program_order'], f'{doi}: order mismatch')
            need(r['doi'] == r['identity']['official_program_doi'] == doi, f'{doi}: DOI mismatch')
            need(r['identity']['publisher_title'] == formal['title'], f'{doi}: formal title changed')
            names = [' '.join([a.get('given', ''), a['family']]).strip() for a in formal['author_metadata']]
            need(names == r['identity']['publisher_author_names'], f'{doi}: formal authors mismatch')
            raw = local(r['source_file']).read_bytes()
            need(digest(raw) == r['source_sha256'], f'{doi}: abstract-source hash mismatch')
            soup = BeautifulSoup(raw, 'html.parser')
            element = soup.select_one('blockquote.abstract')
            element.select_one('.descriptor').extract()
            abstract = element.get_text(' ', strip=True)
            need(abstract == r['abstract'], f'{doi}: freshly extracted full abstract differs')
            need(digest(abstract.encode()) == r['abstract_sha256'], f'{doi}: abstract-string hash differs')
            need(proof(r['abstract_text_file']) == (abstract + '\n').encode(), f'{doi}: abstract text file differs')
            need(soup.find('meta', attrs={'name': 'citation_title'})['content'] == r['title'], f'{doi}: HTML title mismatch')
            need([m['content'] for m in soup.find_all('meta', attrs={'name': 'citation_author'})] == r['authors'], f'{doi}: HTML author list mismatch')
            need(soup.select_one('div.submission-history').get_text(' ', strip=True) == r['history'], f'{doi}: version history mismatch')
            first = subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', str(local(r['representative_pdf']['file'])), '-'])
            need(first == proof(r['representative_pdf']['first_page_text']), f'{doi}: p1 re-extraction differs')
            text = normalized(first.decode())
            need(normalized(formal['title']) in text and normalized(doi) in text, f'{doi}: title/DOI absent in PDF')
            # Explicit documented PDF spelling variant; no fuzzy author matching.
            pdf_names = [n.replace('Ramachandran Ramjee', 'Ramchandran Ramjee') if order == 182 else n for n in names]
            need(all(normalized(n) in text for n in pdf_names), f'{doi}: complete PDF authors absent')
            details.append({'doi': doi, 'program_order': order, 'complete_abstract_reextracted': True})
        return details
    run('formal_manifest_identity_and_three_full_abstracts', identities_and_abstracts)

    def page_scopes():
        total = 0
        for order, wanted in PAGES.items():
            r = records[order]
            reading = r['selected_reading']
            need(reading['physical_pdf_pages'] == wanted, f'{order}: claimed body scope changed')
            need(set(reading['page_text']) == set(map(str, wanted)), f'{order}: body-page proofs differ')
            pdf = local(r['representative_pdf']['file'])
            count = int(re.search(r'^Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', str(pdf)], text=True), re.M).group(1))
            need(count == PDF_PAGES[order] == r['representative_pdf']['pages'], f'{order}: PDF page count changed')
            for page in wanted:
                data = subprocess.check_output(['pdftotext', '-f', str(page), '-l', str(page), str(pdf), '-'])
                need(data == proof(reading['page_text'][str(page)]), f'{order}: p{page} body re-extraction differs')
            for field, options in [('text', []), ('layout_text', ['-layout'])]:
                data = subprocess.check_output(['pdftotext', *options, str(pdf), '-'])
                need(data == proof(r['representative_pdf'][field]), f'{order}: archived {field} differs')
            total += len(wanted)
        need(total == bundle['selected_body_physical_pages'] == 16, 'Body page count is not 16')
        need(bundle['representative_pdf_pages'] == 51 and bundle['body_reading_is_full_paper'] is False, 'Archival/full-reading boundary changed')
        stats.update(selected_body_pages=16, abstract_identity_pages=3, archived_pdf_pages=51)
        return '16 declared body pages freshly extracted; p1 identity pages separate. A verifier cannot prove the human act of reading.'
    run('sixteen_body_pages_and_archival_scope', page_scopes)

    def fixed_software():
        need(len(bundle['software_sources']) == 3, 'Unexpected software source count')
        details = []
        for entry in bundle['software_sources']:
            order = entry['program_order']
            repo, revision, filepath = PINS[order]
            need((entry['repository'], entry['commit']) == (repo, revision), 'Fixed repository revision changed')
            commit = json.loads(proof(entry['commit_metadata']))
            need(commit['sha'] == revision and commit['commit']['committer']['date'] == entry['commit_date'], f'{repo}: commit metadata differs')
            need(commit['html_url'] == f'https://github.com/{repo}/commit/{revision}', f'{repo}: commit belongs to another repository')
            source = next(s for s in bundle['sources'] if s['file'] == entry['source']['file'])
            expected = f'https://raw.githubusercontent.com/{repo}/{revision}/{filepath}'
            need(source['url'] == source['final_url'] == expected and source['status_code'] == 200, f'{repo}: source URL is not pinned')
            text = proof(entry['source']).decode()
            if order == 152:
                # Parsing downloaded Python as syntax data is safe; never import or exec it.
                tree = ast.parse(text)
                funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
                need(set(entry['selected_source_lines']) == {'StaticPlanBlockMemory', 'FuseTIR', 'RewriteCUDAGraph', 'AllocateWorkspace'}, 'TVM inspected wrapper set changed')
                for name, lines in entry['selected_source_lines'].items():
                    node = funcs[name]
                    need([node.lineno, node.end_lineno] == lines and ast.get_docstring(node), f'TVM {name}: inspected lines changed')
                need('tir_var_upper_bound' in ast.get_docstring(funcs['StaticPlanBlockMemory']), 'TVM upper-bound evidence missing')
            elif order == 151:
                need(ORDERS[151] in text and 'fork of [Tenset]' in text, 'Pruner official/fork evidence missing')
            else:
                need('2405.04437' in text and 'research prototypes' in text and 'Sarathi-Serve' in text, 'vAttention prototype/integration evidence missing')
            details.append({'repository': repo, 'commit': revision, 'source_url_pinned': True})
        return details
    run('fixed_source_revisions_and_inspected_interfaces', fixed_software)

    def independent_arithmetic():
        data = json.loads(proof(bundle['calculations']))
        def page(order, number):
            return unicodedata.normalize('NFKC', proof(records[order]['selected_reading']['page_text'][str(number)]).decode())
        # Derive input observations from the original page table, not the output JSON.
        table = re.search(r'Exploration\s+Training\s+Measurement\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)', page(151, 4))
        need(table is not None, 'Pruner p4 table could not be re-extracted')
        search, train, measure = map(Fraction, table.groups())
        total = sum([search, train, measure])
        expected_pruner = {'exploration_minutes': search, 'training_minutes': train, 'measurement_minutes': measure, 'total_minutes': total, 'exploration_share': search / total, 'speedup_if_exploration_zero_other_costs_unchanged': total / (train + measure)}
        # Read matrix dimensions from the published signature, derive coefficients from n=1 and n=2.
        matrix = re.search(r'w:\s*Tensor\(\((\d+),\s*(\d+)\),\s*"f32"\)', page(152, 5))
        need(matrix is not None, 'Relax p5 signature absent')
        k, columns = map(int, matrix.groups())
        def matrix_bytes(n):
            return sum([n * k, k * columns, n * columns]) * 4
        coefficient = matrix_bytes(2) - matrix_bytes(1)
        expected_relax = {'flops_coefficient_n': sum(2 * k for _ in range(columns)), 'logical_bytes_constant_weights': matrix_bytes(1) - coefficient, 'logical_bytes_coefficient_n': coefficient, 'unfused_relu_extra_logical_bytes_coefficient_n': sum([columns * 4, columns * 4])}
        workspace = re.search(r'alloc_buffer\((\d+)\*(\d+)\*(\d+),"f32"', page(152, 9))
        need(workspace is not None, 'Relax workspace dimensions absent')
        workspace_elements = 1
        for v in workspace.groups():
            workspace_elements *= int(v)
        expected_relax['workspace_example_bytes'] = workspace_elements * 4
        params = re.search(r'N\s*=\s*(\d+),\s*H\s*=\s*(\d+),\s*D\s*=\s*(\d+),\s*P\s*=\s*(\d+)', page(182, 6))
        need(params is not None, 'vAttention p6 model parameters absent')
        layers, heads, dim, precision = map(int, params.groups())
        # Sum separate K and V buffers in each layer instead of repeating the producer's formula.
        per_token = sum(heads * dim * precision for _ in range(layers) for _ in ['K', 'V'])
        context, batch = 32768, 16  # Explicit editorial scenario, not a claimed experimental result.
        kv = per_token * context * batch
        rounded_weights = Fraction(34_000_000_000 * 2, 2)  # Explicit 34B rounded BF16/TP2 estimate.
        calls = re.search(r'(\d+)\s+calls to cuMemMap.*?about\s+(\d+)\s+microseconds', page(182, 8), re.S)
        need(calls is not None and int(calls[1]) == layers * 2, 'vAttention call-count/latency evidence absent')
        expected_vattention = {'kv_bytes_per_token_per_worker': per_token, 'kv_bytes_32k_per_request_per_worker': per_token * context, 'kv_bytes_32k_batch16_per_worker': kv, 'approx_weight_bytes_per_worker': rounded_weights, 'approx_weights_plus_kv_gib': (rounded_weights + kv) / (1024 ** 3), 'map_latency_example_ms': Fraction(int(calls[1]) * int(calls[2]), 1000), 'internal_fragmentation_upper_bound_per_request_2mib_bytes': sum(2 * 1024 ** 2 for _ in range(layers * 2)), 'internal_fragmentation_upper_bound_per_request_64kib_bytes': sum(64 * 1024 for _ in range(layers * 2))}
        count = 0
        for group, expected in [('pruner', expected_pruner), ('relax', expected_relax), ('vattention', expected_vattention)]:
            for key, value in expected.items():
                need(abs(float(data[group][key]) - float(value)) <= max(1e-12, abs(float(value)) * 1e-12), f'Independent arithmetic mismatch: {group}.{key}')
                count += 1
        stats['independently_recomputed_values'] = count
        return {'values': count, 'method': 'Inputs re-extracted from cited pages; Fraction arithmetic, matrix basis differences and per-layer K/V summation; educational assumptions explicitly separate.'}
    run('independent_source_based_calculations', independent_arithmetic)

    def proposal():
        f = directory / 'integration-proposal.json'
        if not f.exists():
            return 'No proposal present; core evidence verification completed independently.'
        prop = json.loads(f.read_text())
        need(prop['merge_key'] == 'doi', 'Proposal is not keyed by unique DOI')
        adapted = prop['coverage_adapters']
        need(len(adapted) == 3 and {r['doi'] for r in adapted} == set(ORDERS.values()), 'Proposal DOI set differs')
        coverage = json.loads((root / 'references/proceedings/ASPLOS/2025/reading-coverage.json').read_text())
        missing = 0
        for item in adapted:
            current = [r for r in coverage['records'] if r['doi'] == item['doi']]
            need(len(current) == 1 and current[0]['program_order'] == item['program_order'], 'Current coverage DOI identity differs')
            missing += not current[0]['abstract_read']
            need(item['adapted_record']['selected_reading']['physical_pdf_pages'] == PAGES[item['program_order']], 'Adapter body scope differs')
        suggestions = prop['short_outline_suggestions']
        need(len(suggestions) <= 3, 'More than three outline suggestions')
        for item in suggestions:
            text = (root / item['target_file']).read_text()
            need(item['target_heading'] in text and ('实验 ' + item['preserve_experiment_id']) in text, 'Outline heading/experiment no longer present')
            need(not item['renumber'] and not item['add_section'] and not item['add_experiment'], 'Proposal changes chapter/experiment structure')
        stats['fresh_coverage_missing_abstracts_for_this_package'] = missing
        return {'fresh_unique_doi_abstract_delta_if_integrated': missing, 'suggestions': len(suggestions), 'mutations_performed': 0}
    run('integration_proposal_unique_doi_and_existing_anchors', proposal)

    passed = all(c['passed'] for c in checks)
    report = {'passed': passed, 'mode': 'offline_read_only', 'stats': stats, 'checks': checks, 'warnings': warnings, 'limits': ['Recorded HTTP response consistency is verified; no new network request or live-source attestation.', 'Reading ranges are verified as declarations plus original page text; cognition and benchmark results are not certified.', 'No shared index, outline, downloaded program or output artifact is modified/executed.']}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(('PASS' if passed else 'FAIL') + ': ' + json.dumps(stats, ensure_ascii=False))
        for check in checks:
            if not check['passed']:
                print(check['name'] + ': ' + check['error'], file=sys.stderr)
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
