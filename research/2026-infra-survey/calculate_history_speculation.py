#!/usr/bin/env python3
"""Exact teaching example; no model, framework or downloaded code is executed.

The target is an IID binary source after all sampling constraints. A deterministic
draft proposes only one symbol. This is a counterexample about draft selection,
not a simulation of RhymeRL, Arctic Inference or an autoregressive language model.
"""
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from pathlib import Path
import json
import math


def round_outcomes(prob_a, symbol, draft_length):
    """Accepted prefix + rejection replacement, or full prefix + target bonus."""
    assert 0 <= prob_a <= 1 and symbol in ('A', 'B') and draft_length >= 0
    target = {'A': prob_a, 'B': 1 - prob_a}
    accept = target[symbol]
    other = 'B' if symbol == 'A' else 'A'
    outcomes = defaultdict(F)
    for accepted in range(draft_length):
        outcomes[(symbol,) * accepted + (other,)] += accept**accepted * (1 - accept)
    for bonus, probability in target.items():
        outcomes[(symbol,) * draft_length + (bonus,)] += accept**draft_length * probability
    return {sequence: probability for sequence, probability in outcomes.items() if probability}


def delivered_distribution(prob_a, symbol, draft_length, output_length):
    """Enumerate successive rounds; truncate only at the declared output cap."""
    outcomes = round_outcomes(prob_a, symbol, draft_length)

    @lru_cache(None)
    def suffix(length):
        result = defaultdict(F)
        if length == 0:
            return {(): F(1)}
        for chunk, probability in outcomes.items():
            if len(chunk) >= length:
                result[chunk[:length]] += probability
            else:
                for tail, tail_probability in suffix(length - len(chunk)).items():
                    result[chunk + tail] += probability * tail_probability
        return dict(result)

    return suffix(output_length)


def verify_distribution():
    checked = 0
    for prob_a in [F(0), F(1, 4), F(1, 2), F(3, 4), F(1)]:
        for symbol in ['A', 'B']:
            for draft_length in [0, 1, 2, 4]:
                actual = delivered_distribution(prob_a, symbol, draft_length, 6)
                expected = {}
                for seq in product('AB', repeat=6):
                    p = prob_a**seq.count('A') * (1 - prob_a)**seq.count('B')
                    if p:
                        expected[seq] = p
                assert actual == expected
                assert sum(actual.values()) == 1
                events = round_outcomes(prob_a, symbol, draft_length)
                accept = prob_a if symbol == 'A' else 1 - prob_a
                enumerated_mean = sum(len(seq) * p for seq, p in events.items())
                closed_mean = 1 + sum(accept**i for i in range(1, draft_length + 1))
                assert enumerated_mean == closed_mean
                checked += 1
    return checked


def calculate():
    checked = verify_distribution()
    # All times below are invented teaching inputs, never measured device results.
    baseline_ms = F(1)
    verify_ms, lookup_ms = F(7, 5), F(1, 10)
    exposed_setup_ms = F(2000)
    rows = []
    for symbol in ['A', 'B']:
        events = round_outcomes(F(1, 4), symbol, 4)
        output = sum(len(seq) * p for seq, p in events.items())
        per_token_ms = (verify_ms + lookup_ms) / output
        saving = baseline_ms - per_token_ms
        rows.append(dict(
            draft=symbol * 4,
            conditional_acceptance=str(F(1, 4) if symbol == 'A' else F(3, 4)),
            expected_output_tokens=str(output),
            ms_per_output_token_exact=str(per_token_ms),
            ms_per_output_token=float(per_token_ms),
            relative_throughput=float(baseline_ms / per_token_ms),
            # This is a long-run amortization estimate, not a finite-request SLA.
            setup_amortization_token_estimate=math.ceil(exposed_setup_ms / saving) if saving > 0 else None,
            max_lookup_ms_for_steady_gain=float(baseline_ms * output - verify_ms),
        ))
    assert [r['expected_output_tokens'] for r in rows] == ['341/256', '781/256']
    # Completed-output oracle coverage does not specify the online selected branch.
    history = set(product('AB', repeat=4))
    assert len(history) == 16
    assert all(seq in history for seq in product('AB', repeat=4))
    total_tokens = 1024 * 8 * 4096
    # Assumed complete representation, including IDs; do not add raw IDs again.
    index_bytes = total_tokens * 32
    return dict(
        status='teaching_arithmetic_verified',
        scope='Independent IID binary example; not a RhymeRL or framework reproduction.',
        exact_distribution_checks=checked,
        output_cap_for_distribution_checks=6,
        target_probabilities={'A': '1/4', 'B': '3/4'},
        draft_length=4,
        timing_assumptions_ms=dict(baseline_per_token=1, verify_per_round=1.4,
                                   history_lookup_per_round=0.1, exposed_setup=2000),
        cost_scope='Steady rounds without EOS or output truncation; setup is only the unhidden critical-path part. Verification includes assumed proposal-dependent work except the separate host lookup.',
        candidates=rows,
        oracle_counterexample=dict(historical_four_token_strings=16, offline_coverage=1,
                                   online_branch_still_requires_current_target_validation=True),
        host_index=dict(prompts=1024, responses_per_prompt=8, tokens_per_response=4096,
                        total_tokens=total_tokens, raw_token_id_bytes=4,
                        raw_token_ids_MiB=total_tokens * 4 / 2**20,
                        assumed_total_index_bytes_per_token=32,
                        index_GiB=index_bytes / 2**30,
                        old_and_new_indices_GiB=2 * index_bytes / 2**30,
                        exclusions='Tree-construction temporaries, transport buffers, allocator overhead and other processes require separate budgets. Not a measured RhymeRL index size.'),
        hardware_experiments_run=False,
        downloaded_code_executed=False,
    )


if __name__ == '__main__':
    result = calculate()
    Path(__file__).with_name('history-speculation-arithmetic.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
