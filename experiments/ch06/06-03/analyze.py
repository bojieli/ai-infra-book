"""Offline integrity and descriptive route counts; no communication model."""
import argparse
from collections import Counter
import json
import math
import hashlib
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
o = a.out
source_base=Path(__file__).parent/'reference'
bindings=json.loads((source_base/'source-bindings.json').read_text())
scheduler_sha=hashlib.sha256((source_base/'scheduler.py').read_bytes()).hexdigest()
assert scheduler_sha==bindings['installed-source:sglang/srt/managers/scheduler.py']
supervisor=json.loads((o/'supervisor.json').read_text())
assert supervisor['exit_code']==0 and supervisor['reason'] is None and not supervisor['leftovers']
completion=json.loads((o/'completion.json').read_text())
assert completion['status']=='all_frozen_requests_returned' and completion['count']==4
assert json.loads((o/'ready.json').read_text())['scope']=='actual_43_layer_engine_constructor_returned'
reference = {r['case_id']:r for r in json.loads((o/'reference/requests.json').read_text())}
requests = json.loads((o/'requests.json').read_text())
cases = {r['id']:r for r in json.loads((o/'cases.json').read_text())['cases']}
assert len(requests) == len(cases) == 4
assert Counter(r['case_id'] for r in requests)==Counter({c:1 for c in cases})
matches = []
for r in requests:
    assert r['status'] == 'returned' and r['input_ids'] == cases[r['case_id']]['input_ids']
    ref = reference[r['case_id']]
    assert r['input_ids'] == ref['input_ids'] and r['sampling_params'] == ref['sampling_params']
    x, y = r['response'], ref['response']
    matches.append(dict(case_id=r['case_id'], ids_exact=x['output_ids']==y['output_ids'], text_exact=x['text']==y['text'], finish_exact=x['meta_info']['finish_reason']==y['meta_info']['finish_reason']))
rows=[]
counts={}
duplicates=Counter()
layer_valid=Counter()
layer_padding=Counter()
phase_by_mode={}
mapping={c:[] for c in cases}
decode_audits=[]
for p in sorted((o/'routes').glob('*-batches.jsonl')):
    for line in p.read_text().splitlines():
        batch=json.loads(line)
        routes=batch['routes']
        assert [r['layer_id'] for r in routes] == list(range(43))
        case=batch['request_phase'].get('case_id')
        assert case in cases
        request=next(r for r in requests if r['case_id']==case)
        assert request['sent_monotonic']<=batch['host_start']<=batch['observer_copy_end']<=request['sent_monotonic']+request['request_wall_s']
        valid=batch['num_token_non_padded_cpu']
        assert batch['batch_size']==1
        assert batch['num_token_non_padded_gpu'] in (None,valid)
        assert 0<=valid<=len(batch['input_ids'])==len(batch['positions'])
        assert all(r['mode']==batch['mode'] and r['tokens']==len(batch['input_ids']) and r['batch_size']==1 for r in routes)
        assert batch['is_decode'] != batch['is_extend'], 'only ordinary extend/decode allowed'
        phase='decode' if batch['is_decode'] else 'prefill'
        assert batch['mode'] not in phase_by_mode or phase_by_mode[batch['mode']]==phase
        phase_by_mode[batch['mode']]=phase
        mapping[case].append(dict(pid=batch['pid'],sequence=batch['sequence'],is_decode=batch['is_decode'],is_extend=batch['is_extend'],input_ids=batch['input_ids'][:valid],positions=batch['positions'][:valid]))
        for r in routes:
            layer=r['layer_id']; n=r['tokens']
            assert r['router_class']==('HashTopK' if layer<3 else 'TopK')
            assert len(r['ids'])==len(r['weights'])==n
            assert r['route_cuda_observed_ms']>=0
            key=(case,r['mode'],layer)
            count=counts.setdefault(key,Counter())
            layer_valid[key]+=valid
            layer_padding[key]+=n-valid
            for ids,weights in zip(r['ids'][:valid],r['weights'][:valid]):
                assert len(ids)==len(weights)==6
                duplicates[key]+=int(len(set(ids))!=6)
                assert all(0<=v<256 for v in ids)
                assert all(math.isfinite(w) and w>=0 for w in weights)
                assert abs(sum(weights)-r['expected_weight_sum'])<1e-4, (key,sum(weights))
                count.update(ids)
        rows.append(dict(pid=batch['pid'],sequence=batch['sequence'],case_id=case,mode=routes[0]['mode'],tokens=routes[0]['tokens'],valid_tokens=valid,padding_tokens=routes[0]['tokens']-valid))
assert rows
for case in cases:
    assert any(r['case_id']==case for r in rows)
    mapped=sorted(mapping[case],key=lambda b:b['sequence'])
    assert len({b['pid'] for b in mapped})==1
    prompt=cases[case]['input_ids']
    output=next(r['response']['output_ids'] for r in requests if r['case_id']==case)
    prefill=[t for b in mapped if b['is_extend'] for t in b['input_ids']]
    decode=[t for b in mapped if b['is_decode'] for t in b['input_ids']]
    assert prefill==prompt, 'observed prefill IDs must cover original prompt exactly'
    assert decode==output, 'this captured overlap run consumes every returned ID including terminal EOS'
    req=next(r for r in requests if r['case_id']==case)
    finish=req['response']['meta_info']['finish_reason']
    assert finish=={'type':'stop','matched':1} and output[-1]==1
    decode_batches=[b for b in mapped if b['is_decode']]
    assert len(decode_batches)==len(output) and all(len(b['input_ids'])==1 for b in decode_batches)
    assert decode_batches[-1]['input_ids']==[1]
    decode_audits.append(dict(case_id=case,returned_output_ids=output,observed_decode_ids=decode,
        decode_for_visible_continuation=len(output)-1,terminal_eos_extra_forward=1,
        terminal_eos_sequence=decode_batches[-1]['sequence'],terminal_eos_position=decode_batches[-1]['positions'][0],
        next_token_after_eos_returned=False,next_token_after_eos_value_observed=False,
        explanation='Overlap scheduler launches current batch before processing previous result; raw records show terminal EOS consumed, but no later output token is returned or captured by route-only observer.'))
    positions=[t for b in mapped for t in b['positions']]
    assert positions==list(range(len(prompt)+len(output))), 'every actually consumed position exactly once, including terminal EOS'
    for phase, expected in [('prefill',len(prompt)),('decode',len(output))]:
        for layer in range(43):
            keys=[k for k in counts if k[0]==case and phase_by_mode[k[1]]==phase and k[2]==layer]
            assert sum(layer_valid[k] for k in keys)==expected, (case,phase,layer,expected)
            assert sum(sum(counts[k].values()) for k in keys)==expected*6
summary=dict(status='observed_routes_validated', scheduler_source_sha256=scheduler_sha, request_boundaries_verified=True, output_matches=matches, all_outputs_exact=all(all(r[k] for k in ['ids_exact','text_exact','finish_exact']) for r in matches), batches=rows,
    token_mapping=mapping, decode_audits=decode_audits, total_batch_padding_tokens=sum(r['padding_tokens'] for r in rows),
    total_layer_rows_with_repeated_expert=sum(duplicates.values()),
    counts=[dict(case_id=k[0],mode=k[1],phase=phase_by_mode[k[1]],layer_id=k[2],valid_tokens=layer_valid[k],padding_tokens=layer_padding[k],assignments=sum(v.values()),rows_with_repeated_expert=duplicates[k],expert_counts=[v[i] for i in range(256)]) for k,v in sorted(counts.items())],
    scope='Actual selected expert IDs, no expert-parallel dispatch or communication measurements; observer perturbs execution')
(o/'route-analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(batches=len(rows),route_rows=len(rows)*43,all_outputs_exact=summary['all_outputs_exact'])))
