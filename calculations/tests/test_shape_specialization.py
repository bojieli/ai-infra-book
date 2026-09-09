"""Actual FFN dimensions, shared artifact costs and affine crossing checks."""
from pathlib import Path
from fractions import Fraction
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.shape_specialization import calculate


class SpecializationTests(unittest.TestCase):
    def test_book_work_and_lifetime_switch(self):
        r=calculate();rows={x['policy']:x for x in r['specialization_policies']}
        self.assertEqual(r['summary']['cohort_real_matrix_flops'],1700807049216)
        self.assertEqual(rows['bucket']['cohort_padding_flops'],773094113280)
        self.assertEqual([rows[k]['prepare_ns'] for k in ('generic','bucket','specialized')],[100000000,400000000,900000000])
        for repetitions,winner in ((1,'generic'),(70,'bucket'),(1000,'specialized')):
            self.assertEqual(calculate(repetitions=repetitions)['summary']['selected_policy'],winner)
        for row in rows.values():
            expanded=0
            for mapping in row['shape_mapping']:
                for _ in range(mapping['count']):
                    expanded+=2*mapping['executed_tokens']*(4096*12288+4096*12288+12288*4096)
            self.assertEqual(row['cohort_matrix_flops'],expanded)

    def test_fallback_and_shared_compile(self):
        r=calculate(buckets=[512],specialized_tokens=[256])
        for row in r['specialization_policies'][1:]:
            self.assertEqual(row['fallback_calls'],2)
            self.assertEqual(len(row['artifacts']),2)
            self.assertEqual(row['artifacts']['generic'],100000000)
        cached=calculate(repetitions=1,cached_artifacts=['specialized:256','specialized:1536','specialized:2048'])
        self.assertEqual(cached['specialization_policies'][2]['prepare_ns'],0)
        self.assertEqual(cached['summary']['selected_policy'],'specialized')
        empty=calculate(buckets=[],specialized_tokens=[])
        self.assertEqual(len({x['lifetime_exact_ns'] for x in empty['specialization_policies']}),1)

    def test_crossings_and_rejected_shape(self):
        r=calculate();rows={x['policy']:x for x in r['specialization_policies']}
        for cross in r['specialization_crossings']:
            root=Fraction(cross['equality_repetitions_exact'])
            a,b=rows[cross['policy_a']],rows[cross['policy_b']]
            for n in (root-1,root,root+1):
                difference=(a['prepare_ns']+n*Fraction(a['cohort_execution_exact_ns']))-(b['prepare_ns']+n*Fraction(b['cohort_execution_exact_ns']))
                self.assertEqual(difference,cross['difference_intercept_ns']+n*Fraction(cross['difference_slope_exact_ns']))
                if n==root:self.assertEqual(difference,0)
        with self.assertRaises(ValueError):calculate(buckets=[512,512])
        with self.assertRaises(ValueError):calculate(cached_artifacts=['unknown'])
        with self.assertRaises(ValueError):calculate(shapes=[dict(tokens=999999,count=1)])
