from pathlib import Path
from fractions import Fraction as F
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.dense_training_scale import calculate


class DenseScaleTests(unittest.TestCase):
    def test_official_dense_rates_and_size_scaling(self):
        fixed=calculate(efficiencies=['1/2']);quad=calculate(efficiencies=['1/2'],data_rule='proportional')
        for device,peak in [('a100-80gb-sxm',312),('h100-sxm',F('989.4')),('b200-sxm',2250)]:
            rows=[r for r in fixed['dense_scale_rows'] if r['device']==device]
            expected=F(6*10**12*20*10**12,16384*peak*10**12)*2/86400
            self.assertEqual(F(rows[0]['training_days_exact']),expected)
            self.assertEqual(F(rows[1]['training_days_exact']),5*expected)
            q=[r for r in quad['dense_scale_rows'] if r['device']==device]
            self.assertEqual(F(q[1]['training_days_exact']),25*expected)

    def test_exact_parameter_and_card_boundaries(self):
        for rule in ('fixed','proportional'):
            r=calculate(data_rule=rule,unavailable_days=10)
            for bound in r['dense_scale_bounds']:
                peak=next(x['peak_bf16_fp32_dense_tflops'] for x in r['dense_scale_rows'] if x['device']==bound['device'])
                supply=16384*F(str(peak))*10**12*F(bound['efficiency_exact'])*(bound['deadline_days']-10)*86400
                n=bound['max_parameters_compute']
                def work(p):return 6*p*(20*10**12 if rule=='fixed' else 20*p)
                self.assertLessEqual(work(n),supply);self.assertGreater(work(n+1),supply)
            for row in r['dense_scale_rows']:
                for d in row['deadline_requirements']:
                    per_card=(d['deadline_days']-10)*86400*F(str(row['peak_bf16_fp32_dense_tflops']))*10**12*F(row['efficiency_exact'])
                    n=d['compute_card_count']
                    self.assertGreaterEqual(n*per_card,row['algorithm_flops']);self.assertLess((n-1)*per_card,row['algorithm_flops'])

    def test_scope_and_inputs(self):
        for kwargs in ({'efficiencies':[.5]},{'data_rule':'moe'},{'devices':['gb200-superchip']},{'unavailable_days':90}):
            with self.assertRaises(ValueError):calculate(**kwargs)
