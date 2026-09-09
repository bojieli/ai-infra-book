"""Offline evidence and independent arithmetic checks; executes no author code."""
from pathlib import Path
import datetime, hashlib, json, re, struct, subprocess

D = Path(__file__).resolve().parent
def load(f): return json.loads((D / f).read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def normalize(s): return re.sub(r'\s+', ' ', s)

inventory = load('files.json')
for r in inventory:
    raw = (D / r['file']).read_bytes()
    assert len(raw) == r['bytes'] and sha(raw) == r['sha256'], r['file']
for r in load('reused-sources.json'):
    raw = (D / r['file']).read_bytes()
    assert len(raw) == r['bytes'] and sha(raw) == r['sha256'], r['file']
assert load('sources.json') == []
paper = next(p for p in load('input-abstracts.json')['papers'] if p['program_order'] == 49)
source = next(r for r in load('input-sources.json') if r['file'] == 'paper-049.pdf')
assert source['status'] == 200 and source['bytes'] == 1379011
assert source['sha256'] == paper['source_sha256'] == sha((D / 'paper.pdf').read_bytes())
assert source['url'] == paper['source_url'] and source['retrieved_at'] == paper['source_retrieved_at']
assert paper['doi'].lower() == '10.1109/micro61859.2024.00055'
assert paper['page'] == '657-670'
info = subprocess.run(['pdfinfo', str(D / 'paper.pdf')], check=True, capture_output=True).stdout.decode()
assert re.search(r'^Pages:\s+14\s*$', info, re.M)
assert (D / 'paper.pdf').read_bytes().startswith(b'%PDF')

# Re-run text extraction only; do not run downloaded implementation or simulation.
flow = {4, 6, 7, 8, 9}
for page in range(1, 15):
    for is_flow in ([False, True] if page in flow else [False]):
        cmd = ['pdftotext', '-f', str(page), '-l', str(page)]
        if not is_flow: cmd += ['-layout']
        cmd += [str(D / 'paper.pdf'), '-']
        raw = subprocess.run(cmd, check=True, capture_output=True).stdout
        f = f'page-{page:02d}' + ('-flow' if is_flow else '') + '.txt'
        assert raw == (D / f).read_bytes(), f
assert all(r['returncode'] == 0 for r in load('extraction-log.json'))
selection = load('page-13-selection.json')
lines = (D / 'page-13.txt').read_text().splitlines()
a, z = selection['line_range_inclusive']; c, d = selection['columns_python_slice']
selected = '\n'.join(x[c:d].rstrip() for x in lines[a-1:z]).rstrip() + '\n'
assert selected == (D / selection['file']).read_text()
assert 'ACKNOWLEDGMENT' in lines[z] and 'ACKNOWLEDGMENT' not in selected

reading = load('reading.json')
assert reading['new_http_requests'] == reading['new_complete_abstracts'] == 0
assert reading['paper_sha256'] == source['sha256']
assert reading['full_body_text_pages'] == list(range(2, 13))
assert reading['partial_body_text_pages'] == [13] and reading['unread_body_pages'] == [1, 14]
for r in reading['text_reading']:
    raw = (D / r['file']).read_bytes(); text = raw.decode(); a, z = r['char_range']
    assert sha(raw) == r['sha256'] and a == 0 and z == len(text)
assert [r['physical_page'] for r in reading['images_actually_viewed']] == [4, 5, 6, 7, 9, 10, 11, 12]
for r in reading['images_actually_viewed']:
    raw = (D / r['file']).read_bytes()
    assert sha(raw) == r['sha256'] and raw.startswith(b'\x89PNG\r\n\x1a\n')
    assert max(struct.unpack('>II', raw[16:24])) == 1800 and r['actually_viewed']
assert reading['human_reading_declaration_not_machine_proof']
assert not reading['author_source_code_read'] and not reading['downloaded_code_executed']
assert not reading['framework_or_gpu_or_simulator_executed']
assert not reading['recommendation']['outline_changed'] and not reading['recommendation']['shared_indices_changed']
for r in load('context-snapshots.json'):
    assert sha((D / r['file']).read_bytes()) == r['snippet_sha256']
    assert re.fullmatch('[a-f0-9]{64}', r['source_sha256']) and r['captured_at']

# Presence checks help distinguish what the paper explicitly says from our inference.
p8 = normalize((D / 'page-08-flow.txt').read_text())
p9 = normalize((D / 'page-09-flow.txt').read_text())
p10 = normalize((D / 'page-10.txt').read_text())
p11 = normalize((D / 'page-11.txt').read_text())
p12 = normalize((D / 'page-12.txt').read_text())
for phrase in ['duplicated and occupies m different rows', 'does not need to replicate and shift', 'vector length']:
    assert phrase in p8, phrase
for phrase in ['5e+m2 +3m+13', '5m+2', '4 extra columns', 'two half-chains perform exactly the same operation']:
    assert phrase in p9, phrase
for phrase in ['We leave this to the future work', 'theoretical best performance', 'best throughput of the area-equivalent A100 GPU', '990MB', '80GB HBM2e, 2TB/s', '826 mm2', 'Cortex-A53']:
    assert phrase in p10, phrase
for phrase in ['batch size of 256', 'utilize sparse', 'both set to 1,024']:
    assert phrase in p11, phrase
for phrase in ['60% of the reported 400 W TDP', '62.4%', '2.4%']:
    assert phrase in p12, phrase

# Independent arithmetic: deliberately do not import or call the producer budget.py.
b = load('budget.json'); toy = b['toy']
assert toy['a'] == [1,2,3,4]*4 and toy['b'] == [5,6,7,8]*4
direct = sum(x*y for x,y in zip(toy['a'],toy['b']))
parts = [sum(x if y & (1<<j) else 0 for x,y in zip(toy['a'],toy['b'])) for j in range(4)]
assert direct == sum(v*2**j for j,v in enumerate(parts)) == 280
assert toy['direct_dot'] == toy['reordered_dot'] == direct and parts == toy['partials_lsb_first']
assert [toy[k] for k in ['unreplicated_a_bytes','replicated_a_lower_bits_bytes','available_a_lower_bits_bytes']] == [8,32,8]
assert [toy[k] for k in ['unreplicated_terms_per_residency','replicated_terms_per_residency','unreplicated_residencies_for_16_terms','replicated_residencies_for_16_terms']] == [16,4,1,4]
expected = {'FP32':[110,211,117,651], 'FP16':[55,108,52,168], 'BF16':[46,99,37,123]}
for f, cycles in expected.items():
    r = b['table_ii'][f]
    assert [r[k] for k in ['vfredsum_cycles','vfadd_cycles','vfmul_cycles','vfdot_cycles']] == cycles
assert b['capacity']['data_bytes_per_core'] == 2304*32*32*4 == 9437184
assert b['capacity']['aggregate_data_MiB'] == 990 and b['capacity']['nominal_13B_FP32_weight_bytes'] == 52_000_000_000
assert b['ideal_full_vector_vfdot_ratios']['FP16_over_FP32'] == 7.75
assert abs(b['energy_assumptions']['FP32_dot_TFLOPS_per_watt_ratio'] - 2.3706293706293704) < 1e-12
assert b['listing_2_literal_order_caveat']['final_iteration_add_then_double'] == 2

result = {'status':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'inventory_files_checked':len(inventory),'reused_raw_pdf_bytes':1379011,'new_http_requests':0,'new_complete_abstracts':0,
    'pdf_pages_available':14,'full_body_text_pages':list(range(2,13)),'partial_body_text_pages':[13],
    'images_human_view_declaration_checked':8,'downloaded_code_executed':False,
    'checks':['source identity/URL/status/time/hash bridge','byte-exact Poppler extraction for19 derivatives','partial left-column recipe',
              'reading/image declaration and file hashes; human reading cannot be machine-proved',
              'scoped context snapshots with original-file hash/time','explicit primary text anchors',
              'independent integer/capacity/cycle/energy arithmetic','no new abstract counting'],
    'limits':['No replication of author simulator, numerical correctness, physical implementation, A100 timing or ML quality.',
              'Current shared files may have changed after context snapshots; verifier does not assert otherwise.']}
(D / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False))
