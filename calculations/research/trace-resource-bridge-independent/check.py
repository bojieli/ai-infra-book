"""Independent sealed-source and every-forward replay; never runs a model."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
REPO=PROJECT.parent
AUTHOR=PROJECT/'research/trace-resource-bridge/public'
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.models import qwen3
from infra_calc.schema import Scenario
path=AUTHOR/'src/infra_calc/topics/trace_resource_bridge.py'
spec=importlib.util.spec_from_file_location('review_trace_bridge',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.SOURCE_ROOT=AUTHOR/'sources/trace-resource-bridge'
checks=0


def eq(a,b):
    global checks
    assert a==b, 'Independent comparison failed'
    checks+=1


def main():
    src=path.read_bytes();sha=hashlib.sha256(src).hexdigest()
    assert sha.startswith('966e154198')
    (HERE/'reviewed.snapshot.py').write_bytes(src)
    lock=json.loads((m.SOURCE_ROOT/'sources.lock.json').read_text())
    for row in lock:
        data=(m.SOURCE_ROOT/row['file']).read_bytes()
        eq(hashlib.sha256(data).hexdigest(),row['sha256'])
        eq(len(data),row['bytes'])
        eq(data,(REPO/row['origin']).read_bytes())
    prompts=json.loads((m.SOURCE_ROOT/'sources/chat/prompts.json').read_text())
    eq(sum(len(p['input_ids']) for p in prompts),753)
    eq(sum(p['response']['meta_info']['cached_tokens'] for p in prompts),489)
    eq(sum(len(p['response']['output_ids']) for p in prompts),79)
    results=[]
    for scene in json.loads((AUTHOR/'book.append.json').read_text()):
        args={k:v for k,v in scene.items() if k!='id'}
        r=m.calculate(**args)
        eq(json.loads(json.dumps(r)),json.loads((AUTHOR/'results'/f"{scene['id']}.json").read_text()))
        full=r['scenario']['generation_policy']=='returned_ids_serial_policy'
        sums=Counter();specials=Counter();interfaces=Counter()
        for call,p in zip(r['calls'],prompts):
            N=len(p['input_ids']);S=p['response']['meta_info']['cached_tokens'];P=N-S;G=len(p['response']['output_ids'])
            eq(call['mapping']['prefix_tokens'],S);eq(call['mapping']['new_tokens'],P)
            eq(call['mapping']['decode_forward_calls'],G-1 if full else None)
            eq(call['mapping']['observed_model_forward_calls'],None)
            eq(p['response']['output_ids'][-1],151645)
            eq(call['recorded']['application_wall_seconds'],p['end_s']-p['start_s'])
            eq(call['recorded']['engine_e2e_seconds'],p['response']['meta_info']['e2e_latency'])
            scenarios=[Scenario(batch=1,tokens=P,history=S,output_head='last')]
            if full: scenarios += [Scenario(batch=1,tokens=1,history=N+i,output_head='last') for i in range(G-1)]
            call_sums=Counter();call_specials=Counter();call_io=Counter()
            for index,scenario in enumerate(scenarios):
                ledger=qwen3.calculate('qwen3-8b',scenario);summary=ledger['summary']
                head=next(x for x in ledger['operators'] if x['name']=='lm_head')
                eq(head['shapes']['input'][0],1)
                if full and index:
                    step=call['resources']['decode']['rows'][index-1]
                    eq(step['matrix_flops'],summary['matrix_flops'])
                    eq(step['accounted_scalar_flops'],summary['scalar_flops'])
                    eq(step['special_ops'],summary['special_ops'])
                    eq(step['state_resident_after_bytes'],summary['kv_resident_after_bytes'])
                call_sums.update(matrix_flops=summary['matrix_flops'],accounted_scalar_flops=summary['scalar_flops'])
                call_specials.update(summary['special_ops'])
                keys=call['resources']['prefill']['totals']['known_interfaces']
                call_io.update({k:summary[k] for k in keys})
            totals=call['resources']['complete_logical_totals'] if full else call['resources']['prefill']['totals']
            eq({k:totals[k] for k in call_sums},dict(call_sums));eq(totals['special_ops'],dict(call_specials));eq(totals['known_interfaces'],dict(call_io))
            final_positions=N+G-1 if full else N
            eq(summary['kv_resident_after_bytes'],final_positions*36*2*8*128*2)
            eq(call['resources']['final_state_bytes'],summary['kv_resident_after_bytes'] if full else None)
            sums.update(call_sums);specials.update(call_specials);interfaces.update(call_io)
        total=r['summary']['conditional_complete_logical_totals'] if full else r['summary']['logical_prefill_totals']
        eq({k:total[k] for k in sums},dict(sums));eq(total['special_ops'],dict(specials));eq(total['known_interfaces'],dict(interfaces))
        eq(r['summary']['conditional_serial_forward_calls'],79 if full else None)
        for field in ('observed_model_forward_calls','tool_wait_sum_seconds','simultaneous_kv_peak_bytes','actual_hbm_bytes','actual_gpu_runtime_seconds'):
            eq(r['summary'][field],None)
        results.append(dict(id=scene['id'],summary=r['summary']))
    one=m.logical_call(3,2,1)
    eq(one['decode']['calls'],0);eq(one['final_state_bytes'],5*36*2*8*128*2)
    target=m.SOURCE_ROOT/lock[0]['file'];read=Path.read_bytes
    for missing in (False,True):
        def fake(p):
            if p==target:
                if missing: raise FileNotFoundError('independent missing-source probe')
                return read(p)+b'corruption'
            return read(p)
        with patch.object(Path,'read_bytes',fake):
            try: m.evidence()
            except (ValueError,FileNotFoundError): pass
            else: raise AssertionError('source gate accepted missing/changed content')
        checks_before=1
    (HERE/'verification.json').write_text(json.dumps(dict(status='pass',sha256=sha,python=sys.version,checks=checks,source_rows=len(lock),source_fault_probes=2,scenarios=results),indent=2)+'\n')
    print(json.dumps(dict(status='pass',checks=checks,source_rows=len(lock))))


if __name__=='__main__':main()
