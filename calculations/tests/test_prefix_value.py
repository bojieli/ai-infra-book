"""Exact selection checked against subsets and cached-prefix work identities."""
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.prefix_value import calculate,choose
from infra_calc.models import forward
from infra_calc.schema import Scenario


class PrefixValueTests(unittest.TestCase):
    def test_book_greedy_counterexample(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['optimal_selected'],['512','768'])
        self.assertEqual(s['density_greedy_selected'],['1024'])
        self.assertEqual(s['optimal_minus_greedy_flops_exact'],'3498326360064')
        for row in r['prefix_candidates']:
            prefix_work=forward('qwen3-8b',Scenario(tokens=row['prefix_tokens'],output_head='none'))['summary']['matrix_flops']
            self.assertEqual(row['saved_matrix_flops'],prefix_work)
            self.assertGreater(row['hit_matrix_flops'],0)

    def test_exact_choice_against_subset_enumeration(self):
        rows=[dict(id=str(i),resident_bytes=w,expected_saved_matrix_flops_exact=str(v)) for i,(w,v) in enumerate([(3,Fraction(7,3)),(5,4),(6,5),(2,0),(4,4)])]
        for budget in range(21):
            actual=choose(rows,budget)
            possibilities=[(0,Fraction(0))]
            for count in range(1,len(rows)+1):
                for group in combinations(rows,count):
                    weight=sum(row['resident_bytes'] for row in group)
                    if weight<=budget:possibilities.append((weight,sum(Fraction(row['expected_saved_matrix_flops_exact']) for row in group)))
            weight,value=max(possibilities,key=lambda row:(row[1],-row[0]))
            self.assertEqual(actual['resident_bytes'],weight)
            self.assertEqual(Fraction(actual['expected_saved_matrix_flops_exact']),value)

    def test_fractional_reuse_page_tail_and_zero_capacity(self):
        r=calculate(candidates=[dict(id='tail',prefix_tokens=17,suffix_tokens=5,expected_reuses='1/3')])
        row=r['prefix_candidates'][0]
        self.assertEqual(row['resident_bytes'],32*144*1024)
        self.assertEqual(Fraction(row['expected_saved_matrix_flops_exact']),Fraction(row['saved_matrix_flops'],3))
        self.assertEqual(calculate(budget_bytes=0)['summary']['optimal_selected'],[])
        with self.assertRaises(ValueError):calculate(candidates=[dict(id='bad',prefix_tokens=1,suffix_tokens=0,expected_reuses='1')])
