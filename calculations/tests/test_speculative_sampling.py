"""Exhaustive probability grid, independently enumerated random-choice oracle."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.speculative_sampling import calculate


class SamplingTests(unittest.TestCase):
    def test_exhaustive_three_token_grid(self):
        distributions = [[F(a, 4), F(b, 4), F(4-a-b, 4)]
                         for a in range(5) for b in range(5-a)]
        for p, q in product(distributions, repeat=2):
            r = calculate(list(map(str, p)), list(map(str, q)))
            self.assertEqual([F(v['output_exact']) for v in r['sampling_tokens']], p)
            self.assertEqual(r['summary']['total_variation_exact'], '0')
            self.assertEqual(F(r['summary']['rejection_exact']), sum(abs(a-b) for a,b in zip(p,q))/2)
            accepted = sum(F(v['accepted_mass_exact']) for v in r['sampling_tokens'])
            rejected = sum(F(v['corrected_mass_exact']) for v in r['rejection_branches'])
            self.assertEqual(accepted + rejected, 1)

    def test_independent_uniform_draw_enumeration(self):
        # q=[1/4,3/4], p=[3/4,1/4]. Four equiprobable proposal
        # tickets and three acceptance tickets: accept all token-0 tickets,
        # accept one third of token-1 tickets; rejection always replaces by 0.
        counts = [0, 0]
        for proposal, accept_ticket in product([0, 1, 1, 1], range(3)):
            emitted = proposal if proposal == 0 or accept_ticket == 0 else 0
            counts[emitted] += 1
        rows = calculate(['3/4','1/4'], ['1/4','3/4'])['sampling_tokens']
        self.assertEqual([F(v['output_exact']) for v in rows], [F(v,12) for v in counts])
        book = calculate()
        self.assertEqual([r['wrong_output_exact'] for r in book['sampling_tokens']], ['1/3','4/9','2/9'])
        self.assertEqual(book['summary']['wrong_total_variation_exact'], '1/6')

    def test_unreachable_branches_and_invalid_inputs(self):
        equal = calculate([0,1], [0,1])
        self.assertEqual(equal['rejection_branches'], [])
        self.assertTrue(all(row['residual_exact'] is None for row in equal['sampling_tokens']))
        self.assertIsNone(equal['sampling_tokens'][0]['conditional_accept_exact'])
        disjoint = calculate([1,0], [0,1])
        self.assertEqual(disjoint['summary']['rejection_exact'], '1')
        for p,q in [([],[]), ([1],[0,1]), (['1/3','1/3'],[0,1]),
                    ([-1,2],[0,1]), ([True,0],[1,0]), ([0.5,0.5],[0,1]), (['1/0'],[1])]:
            with self.assertRaises(ValueError): calculate(p,q)
