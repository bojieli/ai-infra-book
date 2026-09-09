"""Independent integer replay and physical-resource accounting for C37 candidate.

Does not use candidate summaries as oracle; adapts exported records into a small
canonical message representation and replays simultaneous rounds independently.
"""
from __future__ import annotations
import collections
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replay(rounds, elements, ranks=8, ownership=None):
    """Canonical edges: sender,receiver,start,end,reduce,contributions optional.

    Sample every interval between ALL message endpoints. Every sampled position
    starts with different integer values and a singleton contribution identity.
    Tensor operations are uniform over these intervals, so replay covers each
    distinct message membership pattern without allocating the full gradient.
    """
    cuts = {elements*i//16 for i in range(17)}
    for row in rounds:
        for edge in row:
            cuts.update((edge['start'], edge['end']))
    cuts = sorted(cuts)
    assert cuts[0] == 0 and cuts[-1] == elements
    assert all(isinstance(x, int) and 0 <= x <= elements for x in cuts)
    points = cuts[:-1]
    values = [[(r + 1) * 101 + p * 7 for p in range(len(points))] for r in range(ranks)]
    identities = [[{r} for _ in points] for r in range(ranks)]
    adds = 0
    snapshots = []
    for round_number, row in enumerate(rounds, 1):
        old = [v[:] for v in values]
        old_ids = [[set(s) for s in v] for v in identities]
        writes = set()
        for edge in row:
            src, dst = edge['sender'], edge['receiver']
            assert 0 <= src < ranks and 0 <= dst < ranks and src != dst
            assert edge['start'] < edge['end']
            for pi, point in enumerate(points):
                if not edge['start'] <= point < edge['end']:
                    continue
                assert (dst, pi) not in writes, 'Conflicting same-round receiver writes'
                writes.add((dst, pi))
                if 'contributions' in edge:
                    assert set(edge['contributions']) == old_ids[src][pi]
                if edge['reduce']:
                    assert not (old_ids[src][pi] & old_ids[dst][pi]), 'Repeated contribution'
                    values[dst][pi] = old[dst][pi] + old[src][pi]
                    identities[dst][pi] = old_ids[dst][pi] | old_ids[src][pi]
                    adds += cuts[pi+1] - cuts[pi]
                else:
                    assert not old_ids[dst][pi], 'AG overwrites a still-owned chunk'
                    values[dst][pi] = old[src][pi]
                    identities[dst][pi] = set(old_ids[src][pi])
        if ownership and round_number in ownership:
            keep = ownership[round_number]
            for rank in range(ranks):
                for pi, point in enumerate(points):
                    if point//(elements//8) not in keep[rank]:
                        identities[rank][pi] = set()
                        values[rank][pi] = None
        snapshots.append([[sorted(x) for x in rank] for rank in identities])
    for r in range(ranks):
        for pi in range(len(points)):
            assert identities[r][pi] == set(range(ranks))
            assert values[r][pi] == sum((s+1)*101 + pi*7 for s in range(ranks))
    assert adds == (ranks-1)*elements
    return dict(sampled_intervals=len(points), scalar_additions=adds,
                rank_outputs_all_equal_eight_rank_sum=True, snapshots=snapshots)


def physical(rounds, rates, startup_ns):
    """Canonical edges additionally have bytes,stripes; stripes have bytes,path."""
    total = collections.Counter()
    sent = collections.Counter()
    received = collections.Counter()
    round_bounds = []
    for row in rounds:
        current = collections.Counter()
        for edge in row:
            sent[edge['sender']] += edge['bytes']
            received[edge['receiver']] += edge['bytes']
            assert sum(s['bytes'] for s in edge['stripes']) == edge['bytes']
            for stripe in edge['stripes']:
                assert stripe['bytes'] > 0 and stripe['path']
                for resource in stripe['path']:
                    assert resource in rates and rates[resource] > 0
                    current[resource] += stripe['bytes']
        total.update(current)
        round_bounds.append(max((n/rates[k] for k,n in current.items()),default=0))
    assert sum(sent.values()) == sum(received.values())
    aggregate=max((n/rates[k] for k,n in total.items()),default=0)
    barrier=sum(round_bounds)+len(rounds)*startup_ns/1e9
    assert barrier+1e-12 >= aggregate
    return dict(resource_bytes=dict(total),sent=dict(sent),received=dict(received),
                aggregate=aggregate,barrier=barrier,round_bounds=round_bounds)


def inspect(result):
    from fractions import Fraction
    gradient=result['gradient']; elements=12288*4096
    assert gradient['parameter']=='model.layers.0.mlp.gate_proj.weight'
    assert gradient['shape']==[12288,4096] and gradient['elements']==elements
    assert gradient['selected_parameter_copies']==1
    dtype=result['scenario']['gradient_dtype']; width={'FP32':4,'BF16':2}[dtype]
    assert gradient['bytes_per_element']==width
    payload=elements*width; algorithm=result['scenario']['algorithm']
    nics=result['scenario']['nics_per_server']; chunk=elements//8
    logical=[]; physical_rounds=[]
    for row in result['rounds']:
        replay_edges=[]; physical_edges=[]
        for msg in row['messages']:
            assert msg['operation'] in ('reduce','copy')
            assert (msg['operation']=='reduce')==(row['phase']=='reduce_scatter')
            start,stop=msg['element_start'],msg['element_stop']
            assert msg['bytes']==(stop-start)*width
            assert msg['chunks']==list(range(start//chunk,stop//chunk))
            assert msg['remote']==(msg['sender']//4!=msg['receiver']//4)
            assert len(msg['stripes'])==(nics if msg['remote'] else 1)
            cursor=start
            for stripe in msg['stripes']:
                assert stripe['element_start']==cursor
                cursor=stripe['element_stop']
                assert stripe['bytes']==(cursor-stripe['element_start'])*width
                path=stripe['path'];src=msg['sender'];dst=msg['receiver']
                assert path[0]==f'rank{src}.tx' and path[-1]==f'rank{dst}.rx'
                if msg['remote']:
                    nic=stripe['nic'];a=src//4;b=dst//4
                    for name in (f'server{a}.nic{nic}.tx',f'server{a}.egress',f'server{b}.ingress',f'server{b}.nic{nic}.rx'):
                        assert path.count(name)==1
                    assert path.count(f'cut.{a}->{b}')==1
                    assert path.count('shared_cut.bidirectional')==1
                else:
                    assert path==[f'rank{src}.tx',f'local.{src}->{dst}',f'rank{dst}.rx']
            assert cursor==stop
            for contribution in msg['contributions']:
                assert len(contribution['contributors'])==len(set(contribution['contributors']))
                c=contribution['chunk']
                replay_edges.append(dict(sender=msg['sender'],receiver=msg['receiver'],
                    start=c*chunk,end=(c+1)*chunk,reduce=msg['operation']=='reduce',
                    contributions=contribution['contributors']))
            assert len(msg['contributions'])==len(msg['chunks'])
            physical_edges.append(dict(sender=msg['sender'],receiver=msg['receiver'],bytes=msg['bytes'],
                                       stripes=msg['stripes']))
        assert row['edges']==[stripe for msg in row['messages'] for stripe in msg['stripes']]
        logical.append(replay_edges);physical_rounds.append(physical_edges)
    if algorithm=='hierarchical':
        local={r:{2*((r%4+1)%4),2*((r%4+1)%4)+1} for r in range(8)}
        half={r:{2*((r%4+1)%4)+(1 if r<4 else 0)} for r in range(8)}
        ownership={3:local,4:half,5:local,8:{r:set(range(8)) for r in range(8)}}
        expected_stages=[('local_reduce_scatter',3),('cross_server_allreduce',2),('local_all_gather',3)]
    else:
        order=list(range(8)) if algorithm=='flat_contiguous' else [0,4,1,5,2,6,3,7]
        ownership={7:{r:{(order.index(r)+1)%8} for r in order},14:{r:set(range(8)) for r in order}}
        expected_stages=[('flat',14)]
    integer=replay(logical,elements,ownership=ownership)
    for boundary in result['ownership_boundaries'][1:]:
        count=boundary['round_count'];expected=ownership[count]
        for r in boundary['ranks']:
            rank=r['rank'];assert {c['chunk'] for c in r['chunks']}==expected[rank]
            for c in r['chunks']:
                # Every chunk spans two independently replayed atomic intervals.
                assert integer['snapshots'][count-1][rank][c['chunk']*2]==c['contributors']
    rates={r['resource']:r['bandwidth_bytes_per_second'] for r in result['resources']}
    wire=physical(physical_rounds,rates,result['scenario']['startup_ns'])
    assert wire['resource_bytes']=={r['resource']:r['bytes'] for r in result['resources']}
    sends=sum(wire['sent'].values());remote=sum(m['bytes'] for row in result['rounds'] for m in row['messages'] if m['sender']//4!=m['receiver']//4)
    assert sends==14*payload
    assert remote=={'flat_contiguous':7*payload//2,'flat_interleaved':14*payload,'hierarchical':2*payload}[algorithm]
    summary=result['summary']
    assert summary['network_send_bytes']==sends and summary['remote_send_bytes']==remote
    assert summary['local_send_bytes']==sends-remote and summary['reduction_scalar_adds']==7*elements
    assert summary['final_gradient_bytes_per_rank']==[payload]*8
    exact=Fraction(0)
    for row in result['rounds']:
        demand=collections.Counter()
        for msg in row['messages']:
            for stripe in msg['stripes']:
                for resource in stripe['path']:demand[resource]+=stripe['bytes']
        assert dict(demand)==row['resource_bytes']
        bound=max(Fraction(n,rates[k]) for k,n in demand.items())
        assert Fraction(row['resource_lower_seconds_exact'])==bound
        assert Fraction(row['barrier_start_seconds_exact'])==exact
        exact+=bound+Fraction(result['scenario']['startup_ns'],10**9)
        assert Fraction(row['barrier_finish_seconds_exact'])==exact
    assert Fraction(summary['serial_barrier_lower_seconds_exact'])==exact
    aggregate=max(Fraction(n,rates[k]) for k,n in wire['resource_bytes'].items())
    assert Fraction(summary['aggregate_resource_lower_seconds_exact'])==aggregate
    assert exact>=aggregate
    assert summary['necessary_budget_not_excluded']==(exact<=Fraction(result['scenario']['budget_ns'],10**9))
    assert summary['actual_training_deadline_feasible'] is None
    assert [(s['stage'],s['rounds']) for s in result['stages']]==expected_stages
    return dict(integer_intervals=integer['sampled_intervals'],integer_replay='pass',
        sends=sends,remote_sends=remote,scalar_adds=integer['scalar_additions'],
        resource_count=len(rates),resource_conservation='pass',barrier_seconds_exact=str(exact))


def main():
    spec=importlib.util.spec_from_file_location('candidate',ROOT/'calculate.py')
    candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
    checks={};results={}
    for dtype in ('FP32','BF16'):
        for algorithm in ('flat_contiguous','flat_interleaved','hierarchical'):
            for nics in (1,2):
                name=f'{dtype}-{algorithm}-nic{nics}'
                result=candidate.calculate(gradient_dtype=dtype,algorithm=algorithm,nics_per_server=nics)
                results[name]=result;checks[name]=inspect(result)
    for algorithm in ('flat_contiguous','flat_interleaved','hierarchical'):
        for nics in (1,2):
            a=results[f'FP32-{algorithm}-nic{nics}'];b=results[f'BF16-{algorithm}-nic{nics}']
            assert {r['resource']:r['bytes'] for r in a['resources']}=={r['resource']:2*r['bytes'] for r in b['resources']}
    for key in ('server0.nic0.tx','server0.nic0.rx','rank0.rx'):
        result=candidate.calculate(bandwidth_overrides={key:1_000_000})
        checks['bottleneck-'+key]=inspect(result)
        assert result['summary']['largest_aggregate_resources']==[key]
    limited=[]
    for nics in (1,2):
        result=candidate.calculate(nics_per_server=nics,bandwidth_overrides={'server0.egress':1_000_000,'server1.egress':1_000_000})
        checks[f'shared-egress-nic{nics}']=inspect(result);limited.append(result)
    assert limited[0]['summary']['serial_barrier_lower_seconds_exact']==limited[1]['summary']['serial_barrier_lower_seconds_exact']
    invalid=[dict(model='qwen3-7b'),dict(gradient_dtype='FP16'),dict(algorithm='ar'),dict(nics_per_server=3),dict(nics_per_server=True),dict(startup_ns=-1),dict(budget_ns=-1),dict(bandwidth_overrides=[]),dict(bandwidth_overrides={'absent':1}),dict(bandwidth_overrides={'server0.egress':0}),dict(bandwidth_overrides={'server0.egress':None}),dict(bandwidth_overrides={'server0.egress':True})]
    rejected=0
    for arguments in invalid:
        try:candidate.calculate(**arguments)
        except (ValueError,TypeError):rejected+=1
        else:raise AssertionError(f'Invalid input accepted: {arguments}')
    # Dependency seam: missing declared rates/path must fail, not become infinite.
    good=results['FP32-hierarchical-nic1'];rounds=good['rounds']
    paths={(s['sender'],s['receiver']):s['path'] for row in rounds for s in row['edges']}
    rates={r['resource']:r['bandwidth_bytes_per_second'] for r in good['resources']}
    for kind in ('missing_rate','missing_path'):
        bad_rates=dict(rates);bad_paths=dict(paths)
        if kind=='missing_rate':bad_rates.pop('server0.egress')
        else:bad_paths.pop(next(iter(bad_paths)))
        try:candidate.account(rounds,bad_paths,bad_rates)
        except ValueError:checks[kind]='rejected'
        else:raise AssertionError(f'{kind} accepted')
    # Fixed tensor dimensions are not exposed as user input; inject one malformed
    # config only at this dependency seam to prove no silent element truncation.
    original=candidate.model_config
    def malformed(model):
        config=dict(original(model));config['hidden_size']=4097;config['intermediate_size']=12289;return config
    candidate.model_config=malformed
    try:
        try:candidate.calculate()
        except ValueError:checks['nondivisible_tensor']='rejected'
        else:raise AssertionError('Nondivisible tensor accepted')
    finally:candidate.model_config=original
    budget=candidate.calculate(budget_ns=0);assert not budget['summary']['necessary_budget_not_excluded']
    output=dict(status='pass',method='independent integer interval replay with duplicate contribution rejection; independent directed resource accumulation and exact Fraction barrier bounds',scenario_checks=checks,invalid_inputs_rejected=rejected,limitations=['No floating-point numerical equivalence or runtime execution asserted.','One fixed actual gradient tensor, not framework buckets or full training timing.'])
    (ROOT/'check-result.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(status='pass',checks=len(checks),invalid_inputs_rejected=rejected)))

if __name__=='__main__':main()
