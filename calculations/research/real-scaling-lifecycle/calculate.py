"""Declared lifetime proxy attached to a real-data fit, not hardware pricing."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'calculations/src'))
from infra_calc.topics.scaling_law import lifecycle


def calculate():
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / 'fit-binding.json').read_text())
    raw = (ROOT / binding['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding['sha256']:
        raise ValueError('Real fit snapshot changed')
    fitted = json.loads(raw)
    scenario = json.loads((folder / 'inputs.json').read_text())
    if scenario['returned_tokens'] < 1:
        raise ValueError('At least one returned token required')
    rate = scenario['cost_per_proxy_flop']
    costs = dict(train_per_flop=rate, prefill_per_flop=rate, decode_per_flop=rate,
                 setup_cost=0, prefill_flops_per_parameter_token=2,
                 decode_flops_per_parameter_token=2)
    demand = dict(calls_per_day=0, lifetime_days=1, input_tokens=scenario['input_tokens'],
                  output_tokens=scenario['returned_tokens']-1)
    fits = dict(primary=fitted['primary'], **fitted['sensitivity'])
    results = []
    for name, fit in fits.items():
        if fit['status'] != 'fit':
            results.append(dict(variant=name, status=fit['status'], result=None))
            continue
        law = fit['result']['law']
        bounds = fit['result']['fit_bounds']
        result = lifecycle(law, scenario['candidate_sizes'], scenario['target_loss'], demand, costs)
        for row in result['rows']:
            if row['feasible']:
                row['outside_fit_box'] = any(not bounds[key][0] <= row[key] <= bounds[key][1] for key in ('N','D'))
                row['extrapolation_factors'] = {key: max(1, bounds[key][0]/row[key], row[key]/bounds[key][1]) for key in ('N','D')}
        curves = []
        for calls in scenario['calls']:
            feasible = [row for row in result['rows'] if row['feasible']]
            values = [dict(N=row['N'], total_cost_units=row['upfront_cost']+calls*row['cost_per_call']) for row in feasible]
            curves.append(dict(calls=calls, values=values,
                               minimizing_candidate_N=min(values, key=lambda x:x['total_cost_units'])['N'] if values else None))
        # Equality is independently checked from the two affine cost lines.
        crossing_checks = []
        for cross in result['crossovers']:
            if cross['calls'] is None:
                continue
            left = next(row for row in result['rows'] if row['N']==cross['left_N'])
            right = next(row for row in result['rows'] if row['N']==cross['right_N'])
            lcost = left['upfront_cost']+cross['calls']*left['cost_per_call']
            rcost = right['upfront_cost']+cross['calls']*right['cost_per_call']
            relative_error = abs(lcost-rcost)/max(1, abs(lcost), abs(rcost))
            if relative_error > 1e-12:
                raise ValueError('Crossover equality failed')
            crossing_checks.append(dict(cross, relative_cost_equality_error=relative_error))
        results.append(dict(variant=name, status='conditional_proxy', law=law, fit_bounds=bounds,
                            lifecycle=result, curves=curves, crossing_checks=crossing_checks))
    return dict(calculation='real-scaling-lifetime-proxy', scenario=scenario, fit_source=binding,
                variants=results, scope=[
                    'The fitted real C4 loss is a proxy target, not demonstrated equal task quality or a trained candidate architecture.',
                    'All costs use the same declared 1e-18 abstract cost units per proxy FLOP, not currency, official hardware price, or measured efficiency.',
                    'Training is 6ND. Input work is 2NP; additional decode is 2N(G-1), because the first output comes from the input phase. Attention, KV, sampling, actual heads and communication are not modeled.',
                    'Every candidate reports its N/D fit-box extrapolation. Formula feasibility does not establish a realizable data budget or reliable prediction.',
                    'Primary and four prespecified sensitivities are shown separately; held-out error does not select a cheaper law.',
                    'Setup is explicitly zero for this scenario; changing assumptions requires rerunning inputs. No deployment recommendation or universal optimum follows.'])


if __name__ == '__main__':
    print(json.dumps(calculate(), ensure_ascii=False, indent=2, allow_nan=False))
