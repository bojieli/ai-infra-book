import sys
from pathlib import Path
from fractions import Fraction
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.training_history import calculate

class IndependentHistoricalReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = calculate()

    def test_math_scopes_and_moe_capacity(self):
        rows={r['input']['id']:r for r in self.result['training_history_rows']}
        for id,n,d in [('deepseek-v3-pretraining',37*10**9,148*10**11),('deepseek-v4-flash',13*10**9,32*10**12),('deepseek-v4-pro',49*10**9,33*10**12)]:
            self.assertEqual(rows[id]['proxy_flops'],6*n*d)
            self.assertGreater(rows[id]['parameter_context']['total_reported'],n)
        self.assertEqual(self.result['stage_reports'][0]['summed_gpu_hours_exact'],'2788000')
        self.assertIsNone(self.result['stage_reports'][1]['summed_gpu_hours_exact'])

    def test_conditional_maximum_scope_not_actual_dates(self):
        row=next(r for r in self.result['training_history_rows'] if r['input']['id']=='llama31-405b')
        d=row['duration'];self.assertEqual(Fraction(d['conditional_calendar_lower_bound_days_exact']),Fraction(30840000,16384*24))
        self.assertIsNone(d['calendar_lower_bound_days_exact']);self.assertIsNone(d['measured_calendar_days'])
        self.assertEqual(row['input']['field_source_ids']['gpu_hours'],'llama31-card')

    def test_reported_mfu_distinct_from_inferred(self):
        obs=self.result['reported_performance'];self.assertEqual(len(obs),3)
        self.assertEqual([r['reported_bf16_mfu_fraction'] for r in obs],['43/100','41/100','38/100'])
        for r in obs:self.assertEqual(r['tp']*r['cp']*r['pp']*r['dp'],r['gpu_count'])
        self.assertTrue(all(r['mfu'] is None for r in self.result['training_history_rows']))

