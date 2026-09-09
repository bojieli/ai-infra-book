"""Finite decision-policy enumeration and deterministic horizon boundaries."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.speculative_budget import calculate


class BudgetTests(unittest.TestCase):
    def test_all_small_policies(self):
        # Enumerate all mappings of 6 nonterminal states to two actions,
        # then expand each policy's probabilistic event tree independently.
        option = dict(id='draft', accepted_counts=[1,2], draft_ns=1, verify_ns=3)
        states = list(product(range(1,4), (False,True)))
        for setup in (0,1,5,20):
            times = []
            for bits in product((0,1), repeat=len(states)):
                policy = dict(zip(states,bits))
                def expand(remaining,warm):
                    if remaining <= 0: return F(0)
                    if policy[remaining,warm] == 0:
                        return 3 + expand(remaining-1,warm)
                    return 4 + (0 if warm else setup) + (expand(remaining-1,True)+2*expand(remaining-2,True))/3
                times.append(expand(3,False))
            result = calculate(output_tokens=3, baseline_token_ns=3, setup_ns=setup, options=[option])
            self.assertEqual(F(result['summary']['optimal_expected_ns_exact']),min(times))

    def test_deterministic_fixed_policy_clipping_and_setup(self):
        option = dict(id='draft', accepted_counts=[0,0,1], draft_ns=1, verify_ns=4)
        for tokens in range(13):
            r=calculate(output_tokens=tokens,baseline_token_ns=4,setup_ns=7,options=[option])
            fixed = next(p for p in r['budget_policies'] if p['policy']=='draft')
            rounds=(tokens+2)//3
            self.assertEqual(F(fixed['expected_ns_exact']),rounds*5+(7 if tokens else 0))
            self.assertEqual(F(fixed['expected_clipped_tokens_exact']),rounds*3-tokens)
            self.assertEqual(F(fixed['expected_drafted_tokens_exact']),rounds*2)
            self.assertEqual(F(fixed['preparation_probability_exact']),int(tokens>0))
            self.assertLessEqual(F(r['summary']['optimal_expected_ns_exact']),min(tokens*4,rounds*5+(7 if tokens else 0)))

    def test_short_request_avoids_setup_and_can_switch_to_baseline(self):
        r=calculate(output_tokens=1)
        self.assertEqual(r['summary']['first_action'],'baseline')
        self.assertEqual(r['summary']['preparation_probability_exact'],'0')
        r=calculate()
        self.assertEqual(next(s for s in r['budget_states'] if s['remaining_tokens']==1 and s['prepared'])['selected'],'baseline')
        self.assertGreater(F(r['summary']['expected_speedup_exact']),1)
        for kw in ({'output_tokens':-1},{'setup_ns':-1},{'options':[]},
                   {'options':[dict(id='baseline',accepted_counts=[1,1],draft_ns=0,verify_ns=1)]},
                   {'options':[dict(id='bad',accepted_counts=[0,0],draft_ns=0,verify_ns=1)]}):
            with self.assertRaises(ValueError): calculate(**kw)
