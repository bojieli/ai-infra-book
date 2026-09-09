"""Book counterexample, real fallback cost and explicit expanded-call totals."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.optimization_deployment import calculate


class DeploymentTests(unittest.TestCase):
    def test_book_scores_and_thresholds(self):
        r=calculate();s=r['summary'];rows={x['candidate']:x for x in r['deployment_candidates']}
        self.assertEqual(rows['A']['shape_mean_ratio_exact'],'21/4')
        self.assertEqual(rows['A']['cohort_execution_ns'],210000)
        self.assertEqual(rows['B']['cohort_execution_ns'],100000)
        self.assertEqual(s['mixed_mean_ns'],30000)
        self.assertEqual(s['break_even_calls'],30000000)
        self.assertEqual(s['strictly_faster_calls'],30000001)
        self.assertEqual(s['whole_cohort_thresholds']['strictly_faster_calls'],15000001)
        self.assertEqual(r['crossover']['equality_first_shape_fraction'],'15/19')
        self.assertIsNone(calculate(dispatch_ns=20000)['summary']['break_even_calls'])
        tied=calculate(dispatch_ns=20000,extra_setup_ns=0)['summary']
        self.assertEqual(tied['break_even_calls'],1)
        self.assertIsNone(tied['strictly_faster_calls'])

    def test_frequency_changes_choice_not_score(self):
        shapes=calculate()['scenario']['shapes'];shapes[0]['count']=9
        r=calculate(shapes=shapes)
        rows={x['candidate']:x for x in r['deployment_candidates']}
        self.assertEqual(rows['A']['mean_execution_ns'],29000)
        self.assertEqual(rows['A']['shape_mean_ratio'],5.25)
        self.assertEqual(r['summary']['best_uniform'],'A')
        for row in r['deployment_candidates']:
            total=0
            for shape in shapes:
                for _ in range(shape['count']):
                    candidate=shape['candidates'].get(row['candidate'])
                    total+=candidate['ns'] if candidate and candidate['valid'] else shape['baseline_ns']
            self.assertEqual(total,row['cohort_execution_ns'])

    def test_failed_missing_and_invalid(self):
        shapes=calculate()['scenario']['shapes']
        shapes[0]['candidates']['A']['valid']=False
        del shapes[1]['candidates']['A']
        r=calculate(shapes=shapes)
        a=next(x for x in r['deployment_candidates'] if x['candidate']=='A')
        self.assertEqual(a['shape_mean_ratio'],0)
        self.assertEqual(a['cohort_execution_ns'],200000)
        self.assertEqual(a['fallback_calls'],2)
        self.assertTrue(all(x['selected']=='B' for x in r['deployment_selections']))
        with self.assertRaises(ValueError):calculate(dispatch_ns=True)
        shapes[0]['count']=shapes[1]['count']=0
        with self.assertRaises(ValueError):calculate(shapes=shapes)
