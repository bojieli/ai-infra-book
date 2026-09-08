#!/usr/bin/env python3
"""Fictional billing exercise; exact arithmetic, no API calls or model execution."""
from fractions import Fraction as F
import json
from pathlib import Path


def calculate():
    n, prefix, fresh = 1000, 19000, 1000
    candidates = {
        'A': dict(input_price=F(1), cache_price=F(1, 10), output_price=F(4),
                  reasoning=1800, visible=200, success=F(4, 5)),
        'B': dict(input_price=F(2), cache_price=F(1, 5), output_price=F(8),
                  reasoning=100, visible=200, success=F(49, 50)),
    }
    costs = {}
    for name, p in candidates.items():
        output = (p['reasoning'] + p['visible']) * p['output_price'] / 10**6
        costs[name] = {
            'hit': (fresh * p['input_price'] + prefix * p['cache_price']) / 10**6 + output,
            'miss': (fresh + prefix) * p['input_price'] / 10**6 + output,
        }
    a = costs['A']['hit'] / candidates['A']['success']
    b = costs['B']
    threshold = (b['miss'] - a * candidates['B']['success']) / (b['miss'] - b['hit'])
    scenarios = []
    for h in [F(0), F(1, 2), threshold, F(1)]:
        attempt = h * b['hit'] + (1-h) * b['miss']
        scenarios.append(dict(hit_fraction=float(h), request_cost=float(attempt),
                              total_cost=float(n * attempt),
                              quality_successes=n * float(candidates['B']['success']),
                              cost_per_quality_success=float(attempt / candidates['B']['success'])))
    return {
        'kind': 'synthetic_teaching_inputs_not_provider_prices_or_measurements',
        'tasks_per_candidate': n, 'prefix_tokens': prefix, 'new_tokens': fresh,
        'prices_unit': 'fictional_cost_units_per_million_tokens',
        'candidates': {name: {k: float(v) if isinstance(v, F) else v for k, v in p.items()}
                       for name, p in candidates.items()},
        'cache_creation_storage_tools_cost': 0,
        'cost_per_request': {k: {mode: float(v) for mode, v in p.items()} for k, p in costs.items()},
        'a_assumed_hit_fraction': 1, 'a_total_cost': float(n * costs['A']['hit']),
        'a_quality_successes': 800, 'a_cost_per_quality_success': float(a),
        'b_scenarios': scenarios,
        'cost_break_even_hit_fraction': float(threshold),
        'cost_break_even_exact': str(threshold),
        'latency_followup': dict(a_finish_seconds=10, b_hit_finish_seconds=4,
                                 b_miss_finish_seconds=12, deadline_seconds=6,
                                 target_joint_quality_and_deadline_fraction=.9,
                                 b_min_hit_fraction=float(F(9, 10) / candidates['B']['success']),
                                 assumptions='Given complete request times; quality independent of hit status. No percentile guarantee.'),
        'denominator': 'All submitted-attempt costs / quality-passing tasks; no automatic retry assumption.',
    }


if __name__ == '__main__':
    p = Path(__file__).with_name('routing-cost-arithmetic.json')
    p.write_text(json.dumps(calculate(), ensure_ascii=False, indent=2) + '\n')
    print(p.name)
