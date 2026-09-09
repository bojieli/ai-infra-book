"""Independent source-ledger classification and resource-admission checks."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
AUTHOR=PROJECT/'research/request-hardware-bridge/public'
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc.topics import v4_forward
path=AUTHOR/'src/infra_calc/topics/request_hardware_bridge.py'
spec=importlib.util.spec_from_file_location('review_hardware_bridge',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=0


def eq(a,b):
    global checks
    assert a==b,'Independent equality failure'
    checks+=1


def main():
    source=path.read_bytes();sha=hashlib.sha256(source).hexdigest()
    assert sha.startswith('293e8259')
    (HERE/'reviewed.snapshot.py').write_bytes(source)
    scenes=json.loads((AUTHOR/'book.append.json').read_text())
    summaries=[]
    for scene in scenes:
        frozen=json.loads((AUTHOR/'results'/f"{scene['id']}.json").read_text())
        # Frozen original request is the input contract; avoid repeated checkpoint header scans.
        with patch.object(m.request_model_comparison,'calculate',return_value=frozen['original_request']):
            r=m.calculate(**{k:v for k,v in scene.items() if k!='id'})
        eq(json.loads(json.dumps(r)),frozen)
        for out,original in zip(r['models'],r['original_request']['comparisons']):
            totals=Counter();scalars=0;special=Counter()
            for j,call in enumerate(out['calls']):
                orig=original['prefill']['totals'] if j==0 else original['decode']['rows'][j-1]
                eq(sum(call['matrix_buckets'].values()),orig['matrix_flops'])
                eq(call['ordinary_scalar_flops'],orig['accounted_scalar_flops'])
                eq(call['special_ops'],orig['special_ops'])
                eq(call['known_interfaces'],orig.get('known_interfaces',{}))
                totals.update(call['matrix_buckets']);scalars+=call['ordinary_scalar_flops'];special.update(call['special_ops'])
                eq(call['work']['physical_hbm_bytes'],None)
                eq(sum(row['matrix_flops'] for row in call['matrix_records']),orig['matrix_flops'])
                if out['model']=='qwen3-8b':
                    pairs=128*129//2 if j==0 else 128+j
                    eq(call['matrix_buckets']['matrix_pv_mixed_or_unresolved'],2*36*32*128*pairs)
                    eq(r['rates']['matrix_pv_mixed_or_unresolved'],None)
                if out['model']=='kimi-k3':
                    eq(set(call['matrix_buckets']),{'matrix_fp32','unclassified_matrix'})
                    assert call['matrix_buckets']['unclassified_matrix']>0
                if r['scenario']['scalar_vector_provider'] and r['scenario']['fp32_matrix_vector_provider']:
                    eq(call['work']['vector_fp32'],call['matrix_buckets'].get('matrix_fp32',0)+orig['accounted_scalar_flops'])
                for key,value in call['interface_normalized_seconds'].items():
                    eq(value['bytes'],call['known_interfaces'][key])
                    assert 'unspecified' in value['physical_resource']
            eq(sum(totals.values()),original['summary']['matrix_flops'])
            eq(scalars,original['summary']['accounted_scalar_flops']);eq(dict(special),original['summary']['special_ops'])
            eq(len(out['calls']),r['scenario']['output_tokens'])
            eq(out['resource_bounds']['accounted_serial_stage_lower_bound_seconds'],None)
            eq(out['complete_runtime_seconds'],None);eq(out['links']['complete_link_bytes'],None)
            eq(out['links']['prefix_restore_payload_bytes'],0)
            eq(out['quality_equivalence'],None)
            if out['model']=='qwen3-8b':
                expected=original['summary']['uniform_bf16_weight_comparison_bytes']+original['summary']['final_state_resident_bytes']
                eq(out['capacity']['necessary_resident_bytes'],expected)
                eq(out['capacity']['status'],'necessary_failure' if expected>out['capacity']['scenario_limit_bytes'] else 'necessary_only')
            else: eq(out['capacity']['necessary_resident_bytes'],None)
        for peak in r['official_dense_peaks'].values():
            eq(peak['sparsity'],'dense');eq(peak['accumulator_precision'],'FP32')
        assert 'matrix_fp4' not in r['rates']
        summaries.append(dict(id=scene['id'],buckets=[{'model':x['model'],'matrix_buckets':x['matrix_buckets'],'capacity_status':x['capacity']['status']} for x in r['models']]))
    default=json.loads((AUTHOR/'results/request-h100-original.json').read_text())
    # Compare each decoder's individual static/dynamic records to a fresh complete forward.
    full_steps=[]
    for model in ('deepseek-v4-flash','deepseek-v4-pro'):
        output=next(x for x in default['models'] if x['model']==model)
        for position in (128,129,130):
            step=v4_forward.calculate(model,batch=1,tokens=1,history=position,routing='balanced')
            expected=m.v4_matrices(step)
            observed=output['calls'][position-127]['matrix_records']
            eq(expected,observed)
            eq(sum(x['matrix_flops'] for x in expected),step['summary']['matrix_flops_effective_attention'])
            full_steps.append({'model':model,'position':position,'matrix_records':len(expected),'flops':sum(x['matrix_flops'] for x in expected)})
    original=default['original_request']
    qwen=default['models'][0]['capacity']['necessary_resident_bytes']
    with patch.object(m.request_model_comparison,'calculate',return_value=original):
        for delta in (-1,0,1):
            result=m.calculate(capacity_bytes=qwen+delta)
            eq(result['models'][0]['capacity']['status'],'necessary_failure' if delta<0 else 'necessary_only')
    report={'status':'pass','checks':checks,'sha256':sha,'python':sys.version,'scenarios':summaries,'full_forward_decode_crosschecks':full_steps,'scope':'Frozen original requests replayed without changing their source ledgers; six actual full V4 decoder forward ledgers recalculated independently of prefix-continuation composition.'}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'pass','checks':checks,'full_v4_steps':len(full_steps)}))


if __name__=='__main__':main()
