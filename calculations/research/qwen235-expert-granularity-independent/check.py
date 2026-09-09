"""Independent dimensions, rank ownership and message-set audit."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from collections import Counter
from fractions import Fraction

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
AUTHOR = PROJECT / 'research/qwen235-expert-granularity/public'
sys.path.insert(0, str(PROJECT / 'src'))
from infra_calc.topics import qwen235_execution

path = AUTHOR / 'src/infra_calc/topics/qwen235_expert_granularity.py'
spec = importlib.util.spec_from_file_location('reviewed_granularity', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks = Counter()


def equal(a, b, category):
    assert a == b, (category, a, b)
    checks[category] += 1


def verify(out):
    c = json.loads((PROJECT / 'configs/models/qwen3-235b-a22b/config.json').read_text())
    H, L, Q, KV, D, V = [c[k] for k in ('hidden_size', 'num_hidden_layers', 'num_attention_heads', 'num_key_value_heads', 'head_dim', 'vocab_size')]
    g, s = out['geometry'], out['scenario']
    E, F, K = g['experts'], g['intermediate'], g['top_k']
    tp, ep, pp = s['tp'], s['ep'], s['pp']
    R = s['requests'] * s['tokens']
    base = 2*V*H + H + L*(2*H*Q*D + 2*H*KV*D + 2*H + 2*D + H*128 + 3*H*128*1536)
    total = 2*V*H + H + L*(2*H*Q*D + 2*H*KV*D + 2*H + 2*D + H*E + 3*H*E*F)
    equal(out['parameters']['baseline_total'], base, 'unique_parameters')
    equal(out['parameters']['variant_total'], total, 'unique_parameters')
    equal(out['parameters']['total_delta'], L*H*(E-128)+3*L*H*(E*F-128*1536), 'router_delta')
    equal(out['parameters']['active_expert_parameters_per_token_all_layers'], 3*L*H*K*F, 'active_parameters')
    equal(abs(out['parameters']['expert_delta']) <= Fraction(out['parameters']['expert_alignment_error_bound_exact']), True, 'alignment_bound')
    counts = Counter()
    destinations = {}
    for row in out['route_table']:
        layer = row['layer']
        token = row['request_id']*s['tokens']+row['position']
        destinations[layer, token] = set(e*ep//E for e in row['experts'])
        for e in row['experts']:
            counts[layer, e] += 1
    equal(sum(counts.values()), L*R*K, 'route_conservation')
    layers_to_stage = {}
    for rr in out['ranks']:
        a,b = rr['layer_range']
        n = b-a
        stage = rr['pipeline_stage']
        for layer in range(a,b):
            layers_to_stage[layer] = stage
        # Q/O split; complete K/V heads (replicated for TP8); all four norms replicated.
        local_non = n*(2*H*(Q//tp)*D+2*H*max(1,KV//tp)*D+2*H+2*D)
        local_non += (V//tp)*H*(int(stage==0)+int(stage==pp-1))
        local_non += H*int(stage==pp-1)
        equal(rr['unchanged_weight_bytes'], 2*local_non, 'nonexpert_independent')
        equal(rr['expert_weight_bytes'], 2*n*(E//ep)*3*H*(F//tp), 'expert_storage')
        equal(rr['replicated_router_weight_bytes'], 2*n*E*H, 'router_storage')
        equal(rr['bf16_kv_bytes'], 4*n*s['length']*max(1,KV//tp)*D*s['requests'], 'kv_complete_heads')
        equal(rr['conditional_resident_bytes'], 2*local_non+2*n*(E//ep)*3*H*(F//tp)+2*n*E*H+4*n*s['length']*max(1,KV//tp)*D*s['requests']+s['workspace_bytes'], 'resident')
        expected_rank = 0
        for row in rr['expert_matrices']:
            rows = counts[row['layer'],row['expert']]
            equal(row['token_rows'], rows, 'actual_matrix_rows')
            for name in ('gate','up','down'):
                op = row[name]
                expected_shapes = ([rows,H],[F//tp,H],[rows,F//tp]) if name!='down' else ([rows,F//tp],[H,F//tp],[rows,H])
                equal((op['input'],op['weight'],op['output']), expected_shapes, 'matrix_shapes')
                equal(op['flops'], 2*rows*H*(F//tp), 'matrix_flops')
                expected_rank += 2*rows*H*(F//tp)
        equal(rr['expert_matrix_flops'], expected_rank, 'rank_work')
    equal(sum(x['expert_matrix_flops'] for x in out['ranks']),6*L*R*K*H*F,'global_work')
    equal(out['summary']['router_matrix_flops_per_logical_cohort'],2*L*R*H*E,'router_work')
    equal(out['summary']['router_matrix_flops_if_executed_on_all_tp_ep_replicas'],2*L*R*H*E*tp*ep,'router_replica_work')
    expected = {}
    def edge(layer,phase,src,dst,tokens):
        tokens = sorted(tokens)
        if tokens and src != dst:
            expected[layer,phase,src,dst]=tokens
    def rank(stage,owner,tensor):
        return stage*ep*tp+owner*tp+tensor
    for layer in range(L):
        stage = layers_to_stage[layer]
        active = [{t for t in range(R) if owner in destinations[layer,t]} for owner in range(ep)]
        for owner in range(ep):
            for tensor in range(1,tp):
                edge(layer,'tp_reduce',rank(stage,owner,tensor),rank(stage,owner,0),active[owner])
                edge(layer,'tp_broadcast',rank(stage,owner,0),rank(stage,owner,tensor),range(R))
            if owner:
                edge(layer,'ep_reduce',rank(stage,owner,0),rank(stage,0,0),active[owner])
                edge(layer,'ep_broadcast',rank(stage,0,0),rank(stage,owner,0),range(R))
        if layer+1<L and layers_to_stage[layer+1]!=stage:
            edge(layer,'pp_transfer',rank(stage,0,0),rank(stage+1,0,0),range(R))
            for target in range(rank(stage+1,0,0)+1,rank(stage+1,0,0)+ep*tp):
                edge(layer,'pp_replicate',rank(stage+1,0,0),target,range(R))
    actual = {(x['layer'],x['phase'],x['source'],x['target']):x['token_ids'] for x in out['messages']}
    equal(actual,expected,'exact_message_destinations')
    wire = sum(len(v) for v in expected.values())*(H*s['wire_element_bytes']+s['row_metadata_bytes'])
    equal(out['summary']['total_wire_bytes'],wire,'message_wire')
    for msg in out['messages']:
        equal(msg['wire_bytes'],len(msg['token_ids'])*(H*s['wire_element_bytes']+s['row_metadata_bytes']),'each_message_wire')
    for name in ('actual_runtime_seconds','actual_peak_bytes','trained_quality','tensor_core_utilization'):
        equal(out['summary'][name],None,'unknown_boundaries')


def main():
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    equal(sha,'97a7afb05e333a7fade68f79696fc120ca2550c4e2e4d06bcea205fd2ac8d478','frozen_sha')
    (HERE/'reviewed.snapshot.py').write_bytes(path.read_bytes())
    scenes = json.loads((AUTHOR/'book.append.json').read_text())
    summaries=[]
    for scene in scenes:
        args={k:v for k,v in scene.items() if k!='id'}
        out=m.calculate(**args)
        equal(out,json.loads((AUTHOR/'results'/f"{scene['id']}.json").read_text()),'frozen_scene_replay')
        verify(out)
        summaries.append(dict(id=scene['id'],parameters=out['parameters'],summary=out['summary']))
    for tp,ep,pp in ((8,1,1),(1,2,4),(2,2,2)):
        out=m.calculate(tp=tp,ep=ep,pp=pp,requests=2,tokens=2)
        verify(out)
        baseline=qwen235_execution.calculate(tp=tp,ep=ep,pp=pp,requests=2,tokens=2)
        equal(out['summary']['total_wire_bytes'],baseline['summary']['total_wire_bytes'],'baseline_execution')
        equal(out['summary']['expert_matrix_flops'],baseline['summary']['expert_matrix_flops'],'baseline_execution')
        for a,b in zip(out['ranks'],baseline['ranks']):
            equal(a['total_bf16_weight_bytes'],b['bf16_weight_bytes'],'baseline_execution')
            equal(a['bf16_kv_bytes'],b['bf16_kv_bytes'],'baseline_execution')
        if pp==4:
            worst=max(x['conditional_resident_bytes'] for x in out['ranks'])
            for delta in (-1,0,1):
                result=m.calculate(tp=tp,ep=ep,pp=pp,requests=2,tokens=2,capacity_bytes=worst+delta)
                equal(result['summary']['all_necessary_capacity_fits'],delta>=0,'worst_rank_boundary')
    # Positive-grid boundary: below half an alignment must be rejected, not claim false error bound.
    try:
        m.calculate(experts=4096,top_k=8,tokens=1)
    except ValueError:
        checks['positive_grid_rejection']+=1
    else:
        raise AssertionError('Expected positive aligned F rejection')
    (HERE/'verification.json').write_text(json.dumps(dict(status='pass',sha256=sha,python=sys.version,checks=dict(checks),scenarios=summaries),indent=2)+'\n')
    print(json.dumps(dict(status='pass',checks=dict(checks))))


if __name__=='__main__':
    main()
