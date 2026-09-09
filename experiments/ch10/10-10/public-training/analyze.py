"""Offline audit of author-published training records; no scale extrapolation."""
import collections, hashlib, json, math, re, statistics, sys
from pathlib import Path

B = Path(__file__).absolute().parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else B / 'results'
out.mkdir(parents=True, exist_ok=True)
checks = 0
def check(value):
    global checks
    assert value
    checks += 1
def read(path):
    return json.loads((B / path).read_text())

for meta in B.rglob('*.source.json'):
    j = json.loads(meta.read_text())
    raw = meta.with_name(meta.name.removesuffix('.source.json')).read_bytes()
    check(hashlib.sha256(raw).hexdigest() == j['sha256'])
    check(len(raw) == j['bytes'])
    check(j['status'] == 200)
runs = read('wandb/runs.json')['data']['project']['runs']
check(not runs['pageInfo']['hasNextPage'])
nodes = {e['node']['name']: e['node'] for e in runs['edges']}
rows = []
for name, n in nodes.items():
    cfg = json.loads(n['config'])['nanotron_config']['value']
    p, t = cfg['parallelism'], cfg['tokens']
    ranks = math.prod(p[k] for k in ['dp', 'tp', 'pp', 'context_parallel_size', 'expert_parallel_size'])
    batch = p['dp'] * t['micro_batch_size'] * t['batch_accumulation_per_replica'] * t['sequence_length']
    s = json.loads(n['summaryMetrics'])
    if s.get('tokens_per_sec_per_gpu'):
        check(math.isclose(s['tokens_per_sec']/s['tokens_per_sec_per_gpu'], ranks, rel_tol=1e-10))
    rows.append(dict(name=name, state=n['state'], configured_ranks=ranks, tokens_per_step=batch,
                     final_global_step=s.get('iteration_step'), final_global_consumed_tokens=s.get('consumed_tokens'),
                     reported_runtime_seconds=s.get('_runtime')))
histories = []
for filename, name in [('final-history-sampled10000.json','n4jn9hla'), ('history-uliytlp7.json','uliytlp7'),
                       ('history-28jt9vhg.json','28jt9vhg'), ('history-8ey7uow0.json','8ey7uow0')]:
    h = read('wandb/'+filename)['data']['project']['run']['sampledHistory'][0]
    r = next(r for r in rows if r['name'] == name)
    steps = [int(x['iteration_step']) for x in h]
    check(steps == sorted(set(steps)))
    for x in h:
        check(x['_step'] == x['iteration_step'])
        check(x['consumed_tokens'] == x['iteration_step'] * r['tokens_per_step'])
        check(math.isclose(x['tokens_per_sec']/x['tokens_per_sec_per_gpu'], r['configured_ranks'], rel_tol=1e-10))
        check(math.isclose(x['tokens_per_sec'] * x['time_per_iteration_ms']/1000, r['tokens_per_step'], rel_tol=1e-10))
    histories.append(dict(name=name, configured_ranks=r['configured_ranks'], samples=len(h),
                          first_sample_step=min(steps), last_sample_step=max(steps),
                          unsampled_steps_inside_range=max(steps)-min(steps)+1-len(h),
                          sampled_median_iteration_ms=statistics.median(x['time_per_iteration_ms'] for x in h)))
log = (B/'final-run/output.log').read_text()
steps = [int(x) for x in re.findall(r'iteration: (\d+) / 4720000', log)]
check(steps == list(range(4706001, 4720001)))
final = next(r for r in rows if r['name']=='n4jn9hla')
check(final['final_global_step'] == steps[-1])
report = dict(source='author public records, not a local training run',
              states=dict(collections.Counter(n['state'] for n in nodes.values())), runs=rows, sampled_histories=histories,
              final_console=dict(first_step=steps[0], last_step=steps[-1], contiguous_iterations=len(steps),
                                 values_are_human_rounded=True, tokens_in_this_segment=len(steps)*final['tokens_per_step']),
              limitations=['Sampled history is not complete, including the request for 20000 samples.',
                           'Global counters include earlier resumed runs; do not divide them by final run runtime.',
                           'States do not identify hardware faults; stage and device-count changes prevent matched scaling claims.',
                           'No per-run physical device inventory, full allocation timeline, fault classification, quality target or cost evidence.',
                           'No Qwen/V4 or trillion-parameter extrapolation; calculation work belongs to separate owner.'], checks=checks)
(out/'analysis.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'checks':checks,'histories':histories,'final_console':report['final_console']}))
