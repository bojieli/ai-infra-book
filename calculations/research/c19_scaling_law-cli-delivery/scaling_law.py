"""C19 controlled dense teaching model. All counts use base units; FMA=2 FLOPs.

L=E+A*(N/N0)^(-alpha)+B*(D/D0)^(-beta). Fit by finite exponent
search and conditional linear least squares, never by held-out error.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

from infra_calc.units import positive_number, positive_int


def number(x, name, zero=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f'{name} must be a finite number')
    if zero and x == 0:
        return x
    return positive_number(x, name)


def validate_law(law):
    for k in ('A', 'B', 'alpha', 'beta', 'N0', 'D0'):
        number(law[k], k)
    number(law['E'], 'E', True)


def loss(law, N, D):
    validate_law(law)
    number(N, 'N'); number(D, 'D')
    return law['E'] + law['A']*(N/law['N0'])**(-law['alpha']) + law['B']*(D/law['D0'])**(-law['beta'])


def _linear(rows, targets):
    # Three-column modified Gram-Schmidt QR; reject a rank-deficient design.
    q, r = [], [[0.0]*3 for _ in range(3)]
    for j in range(3):
        v = [row[j] for row in rows]
        original = math.sqrt(sum(x*x for x in v))
        for i in range(j):
            r[i][j] = sum(x*y for x,y in zip(q[i], v))
            v = [x-r[i][j]*y for x,y in zip(v,q[i])]
        r[j][j] = math.sqrt(sum(x*x for x in v))
        if r[j][j] <= 1e-10*original:
            raise ValueError('rank-deficient or ill-conditioned fit design')
        q.append([x/r[j][j] for x in v])
    rhs = [sum(x*y for x,y in zip(col,targets)) for col in q]
    out = [0.0]*3
    for i in (2,1,0):
        out[i] = (rhs[i]-sum(r[i][j]*out[j] for j in range(i+1,3)))/r[i][i]
    return out


def fit(records, exponent_grid, N0, D0):
    number(N0,'N0'); number(D0,'D0')
    if not records or not exponent_grid:
        raise ValueError('records and exponent_grid must be nonempty')
    ids=set(); controls=set()
    for row in records:
        if not isinstance(row['id'],str) or not row['id'] or row['id'] in ids:
            raise ValueError('unique nonempty record ids required')
        ids.add(row['id'])
        if row['split'] not in ('fit','holdout'):
            raise ValueError('split must be fit or holdout')
        if not isinstance(row['control_id'],str) or not row['control_id']:
            raise ValueError('control_id required')
        controls.add(row['control_id'])
        for key in ('N','D','loss','C_flops'):
            number(row[key],key)
    if len(controls)!=1:
        raise ValueError('cannot pool different data/training/evaluation controls')
    train=[r for r in records if r['split']=='fit']
    if len(train)<4 or not any(r['split']=='holdout' for r in records):
        raise ValueError('need at least four fit records and one holdout')
    candidates=[]
    for alpha,beta in exponent_grid:
        number(alpha,'alpha'); number(beta,'beta')
        rows=[[1,(r['N']/N0)**-alpha,(r['D']/D0)**-beta] for r in train]
        E,A,B=_linear(rows,[r['loss'] for r in train])
        if E<0 or A<=0 or B<=0:
            continue
        law=dict(E=E,A=A,B=B,alpha=alpha,beta=beta,N0=N0,D0=D0)
        sse=sum((loss(law,r['N'],r['D'])-r['loss'])**2 for r in train)
        candidates.append(dict(law=law,fit_sse=sse))
    if not candidates:
        raise ValueError('no positive admissible fit; expand design/grid or revise model')
    best=min(candidates,key=lambda r:r['fit_sse'])
    bounds={k:[min(r[k] for r in train),max(r[k] for r in train)] for k in ('N','D')}
    predictions=[]
    for row in records:
        pred=loss(best['law'],row['N'],row['D'])
        predictions.append(dict(**deepcopy(row), predicted_loss=pred, residual=pred-row['loss'],
            outside_fit_box=any(not bounds[k][0]<=row[k]<=bounds[k][1] for k in bounds),
            extrapolation_factors={k:max(1,bounds[k][0]/row[k],row[k]/bounds[k][1]) for k in bounds}))
    return dict(law=best['law'],fit_sse=best['fit_sse'],fit_bounds=bounds,
                candidates=candidates,predictions=predictions,
                holdout_rmse=math.sqrt(sum(r['residual']**2 for r in predictions if r['split']=='holdout')/sum(r['split']=='holdout' for r in predictions)))


def compute_optimum(law, budget_flops, k=6, N_bounds=None, D_bounds=None):
    """Continuous optimum under kND=C, with optional closed feasible box."""
    validate_law(law); number(budget_flops,'budget_flops'); number(k,'k')
    a,b=law['alpha'],law['beta']
    Q=budget_flops/(k*law['N0']*law['D0'])
    x=math.exp((math.log(a*law['A']/(b*law['B']))+b*math.log(Q))/(a+b))
    N=x*law['N0']; lower=0.; upper=math.inf
    for bounds,name in ((N_bounds,'N'),(D_bounds,'D')):
        if bounds is not None:
            if len(bounds)!=2: raise ValueError('bounds need two values')
            number(bounds[0],name); number(bounds[1],name)
            if bounds[0]>bounds[1]: raise ValueError('reversed bounds')
    if N_bounds: lower,upper=N_bounds
    if D_bounds:
        lower=max(lower,budget_flops/(k*D_bounds[1]))
        upper=min(upper,budget_flops/(k*D_bounds[0]))
    if lower>upper: raise ValueError('no feasible full-budget allocation')
    N=min(max(N,lower),upper); D=budget_flops/(k*N)
    return dict(N=N,D=D,training_proxy_flops=k*N*D,predicted_loss=loss(law,N,D),
                boundary=N==lower or N==upper, continuous=True)


def lifecycle(law, sizes, target_loss, demand, costs, k=6):
    """Finite architecture enumeration, exact target-loss D within the model."""
    validate_law(law); number(target_loss,'target_loss'); number(k,'k')
    for key in ('calls_per_day','lifetime_days','input_tokens','output_tokens'):
        positive_int(demand[key],key,allow_zero=True)
    for key in ('train_per_flop','prefill_per_flop','decode_per_flop','setup_cost'):
        number(costs[key],key,True)
    for key in ('prefill_flops_per_parameter_token','decode_flops_per_parameter_token'):
        number(costs[key],key)
    if not sizes: raise ValueError('sizes must be nonempty')
    calls=demand['calls_per_day']*demand['lifetime_days']; rows=[]
    for N in sizes:
        number(N,'N')
        gap=target_loss-law['E']-law['A']*(N/law['N0'])**-law['alpha']
        if gap<=0:
            rows.append(dict(N=N,feasible=False,D=None,total_cost=None)); continue
        D=law['D0']*(law['B']/gap)**(1/law['beta'])
        train=k*N*D; pre=costs['prefill_flops_per_parameter_token']*N*demand['input_tokens']
        dec=costs['decode_flops_per_parameter_token']*N*demand['output_tokens']
        upfront=train*costs['train_per_flop']+costs['setup_cost']
        per=pre*costs['prefill_per_flop']+dec*costs['decode_per_flop']
        rows.append(dict(N=N,D=D,feasible=True,predicted_loss=loss(law,N,D),training_proxy_flops=train,
            prefill_proxy_flops_per_call=pre,decode_proxy_flops_per_call=dec,training_cost=train*costs['train_per_flop'],
            setup_cost=costs['setup_cost'],upfront_cost=upfront,cost_per_call=per,
            lifetime_inference_cost=calls*per,total_cost=upfront+calls*per))
    feasible=[r for r in rows if r['feasible']]; crosses=[]
    for i,left in enumerate(feasible):
        for right in feasible[i+1:]:
            diff=left['cost_per_call']-right['cost_per_call']
            cross=(right['upfront_cost']-left['upfront_cost'])/diff if diff else None
            crosses.append(dict(left_N=left['N'],right_N=right['N'],calls=cross if cross is not None and cross>=0 else None,
                status='coincident' if not diff and left['upfront_cost']==right['upfront_cost'] else 'parallel' if not diff else 'nonnegative_crossing' if cross>=0 else 'negative_crossing'))
    return dict(calls=calls,rows=rows,crossovers=crosses,
        optimal_N=min(feasible,key=lambda r:r['total_cost'])['N'] if feasible else None,
        status='finite_candidate_optimum' if feasible else 'no_feasible_candidate')


def calculate(inputs):
    s=deepcopy(inputs)
    if s['model_family']!='dense': raise ValueError('only dense proxy supported; MoE/hybrid need separate accounting')
    if s['data_kind'] not in ('synthetic_teaching','controlled_records'): raise ValueError('explicit data_kind required')
    f=fit(s['records'],s['exponent_grid'],s['N0'],s['D0'])
    k=number(s['training_flops_per_parameter_token'],'training multiplier')
    if not s['budgets_flops']: raise ValueError('budgets_flops must be nonempty')
    for r in f['predictions']:
        r['recorded_to_knd_ratio']=r['C_flops']/(k*r['N']*r['D'])
    budgets=[compute_optimum(f['law'],c,k,s.get('N_bounds'),s.get('D_bounds')) for c in s['budgets_flops']]
    life=lifecycle(f['law'],s['candidate_sizes'],s['target_loss'],s['demand'],s['costs'],k)
    sensitivity=[]
    # Refit E,A,B for every declared exponent pair; no holdout-based selection.
    for candidate in f['candidates']:
        law=candidate['law']
        sensitivity.append(dict(law=law,fit_sse=candidate['fit_sse'],
            optimum=compute_optimum(law,s['budgets_flops'][-1],k,s.get('N_bounds'),s.get('D_bounds')),
            predictions=[dict(N=p['N'],D=p['D'],loss=loss(law,p['N'],p['D'])) for p in s['extrapolation_points']]))
    policies=[]
    anchor=compute_optimum(f['law'],s['budgets_flops'][0],k)
    for policy in s.get('allocation_policies',[]):
        exponent=number(policy['N_compute_exponent'],'N_compute_exponent')
        if exponent>=1: raise ValueError('allocation exponent must be below one')
        for budget in s['budgets_flops']:
            N=anchor['N']*(budget/s['budgets_flops'][0])**exponent
            D=budget/(k*N)
            policies.append(dict(policy=policy['id'],budget_flops=budget,N=N,D=D,
                teaching_law_loss=loss(f['law'],N,D),source=policy.get('source'),
                status='common synthetic anchor; historical exponent illustration, not paper replication'))
    curves=[]
    for calls in s['call_counts']:
        positive_int(calls,'calls',allow_zero=True)
        curves.extend(dict(calls=calls,N=r['N'],total_cost=r['upfront_cost']+calls*r['cost_per_call']) for r in life['rows'] if r['feasible'])
    return dict(schema_version=1,calculation='scaling-law',scenario=s,sources=s.get('sources',[]),
        fit=f,budget_optima=budgets,allocation_policy_comparison=policies,lifecycle=life,lifetime_curves=curves,extrapolation_sensitivity=sensitivity,
        summary=dict(data_kind=s['data_kind'],fit_sse=f['fit_sse'],holdout_rmse=f['holdout_rmse'],
            lifetime_calls=life['calls'],optimal_candidate_N=life['optimal_N'],task_quality_prediction=None),
        assumptions=['Synthetic records are teaching inputs, not real model experiments; controls and split are explicit.',
            'Finite exponent search plus conditional least squares is not a global nonlinear fit or uncertainty interval.',
            'kND and per-token dense inference work are parameter-matrix proxies, not training_matrix full operator accounting.',
            'Equal predicted validation loss is only a quality proxy on the same data/tokenizer/evaluation; task equivalence is unknown.',
            'Costs are declared cost-unit/FLOP scenarios, not hardware prices or measured service rates. Setup may include separately supplied teacher/data costs.',
            'Inference excludes attention/KV, batching, communication, queueing and hardware efficiency changes. No MoE/RL/test-time scaling fit.',
            'Continuous N,D ignore architecture granularity and data supply beyond optional budget bounds; lifetime optimum is only over supplied sizes.',
            'Sensitivity envelope is deterministic model-assumption sensitivity, not a confidence interval; no paper-point reproduction claimed.'])


def markdown(result):
    lines=['# C19 scaling-law — '+result['scenario']['data_kind'],'',json.dumps(result['summary'],sort_keys=True),'',
        '| Budget FLOPs | N | D | Predicted loss |','| --- | --- | --- | --- |']
    for r in result['budget_optima']:
        lines.append(f"| {r['training_proxy_flops']:.6g} | {r['N']:.6g} | {r['D']:.6g} | {r['predicted_loss']:.6g} |")
    lines+=['','| N | D at target loss | Upfront cost | Lifetime inference | Total cost |','| --- | --- | --- | --- | --- |']
    for r in result['lifecycle']['rows']:
        lines.append('| '+ ' | '.join(f'{r[k]:.6g}' if r.get(k) is not None else 'infeasible' for k in ('N','D','upfront_cost','lifetime_inference_cost','total_cost'))+' |')
    lines+=['','| Record | Split | Observed loss | Predicted loss | Residual | Outside fit box |','| --- | --- | --- | --- | --- | --- |']
    for r in result['fit']['predictions']:
        lines.append(f"| {r['id']} | {r['split']} | {r['loss']:.8g} | {r['predicted_loss']:.8g} | {r['residual']:.4g} | {r['outside_fit_box']} |")
    lines+=['','| Allocation policy (common teaching anchor) | Budget FLOPs | N | D |','| --- | --- | --- | --- |']
    for r in result['allocation_policy_comparison']:
        lines.append(f"| {r['policy']} | {r['budget_flops']:.5g} | {r['N']:.5g} | {r['D']:.5g} |")
    lines+=['','| Size pair | Equal-cost call count | Status |','| --- | --- | --- |']
    for r in result['lifecycle']['crossovers']:
        lines.append(f"| {r['left_N']:.5g} / {r['right_N']:.5g} | {r['calls']} | {r['status']} |")
    lines+=['']+['- '+a for a in result['assumptions']]
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True); p.add_argument('--format',choices=('json','md'),default='json'); p.add_argument('--output',type=Path)
    args=p.parse_args(); result=calculate(json.loads(args.inputs.read_text()))
    output=json.dumps(result,indent=2,allow_nan=False)+'\n' if args.format=='json' else markdown(result)
    if args.output: args.output.write_text(output)
    else: print(output,end='')
