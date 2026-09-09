from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.training_deadline import calculate


class TrainingDeadlineTests(unittest.TestCase):
    def test_independent_matrix_geometry_and_tail(self):
        lengths=[8192,8192,123]
        h,l,q,kv,d,ffn,v=4096,36,32,8,128,12288,151936
        linear_per_token=l*(2*h*q*d+4*h*kv*d+2*h*q*d+6*h*ffn)+2*h*v
        expected=sum(3*(n*linear_per_token+4*l*q*d*n*(n+1)//2) for n in lengths)
        r=calculate(task_tokens=sum(lengths),devices=['a100-80gb-sxm'])
        self.assertEqual(r['summary']['task_training_matrix_flops'],expected)
        naive=F(r['summary']['full_sequence_matrix_flops']*sum(lengths),8192)
        self.assertGreater(naive,expected)

    def test_integer_count_bounds_and_calendar(self):
        r=calculate(unavailable_seconds=5*86400)
        s=r['summary'];work=s['task_training_matrix_flops'];time=s['available_training_seconds']
        self.assertEqual(time,25*86400)
        for row in r['training_deadline_rows']:
            rate=F(row['bf16_fp32_dense_peak_flops_exact'])*F(row['matrix_work_efficiency_exact'])
            n=row['compute_count_bound']
            self.assertGreaterEqual(n*time*rate,work);self.assertLess((n-1)*time*rate,work)
            cap=row['nominal_capacity_bytes'];m=row['persistent_capacity_count_bound']
            self.assertGreaterEqual(m*cap,s['persistent_state_bytes']);self.assertLess((m-1)*cap,s['persistent_state_bytes'])
            self.assertLessEqual(F(row['conditional_calendar_seconds_exact']),30*86400)

    def test_precision_scope_and_moe_state(self):
        r=calculate(devices=['a800-40gb-active','h20','gb200-superchip'])
        self.assertEqual(r['training_deadline_rows'],[])
        self.assertEqual(r['training_deadline_devices'][0]['capacity_bound_devices'],4)
        moe=calculate(model='qwen3-235b-a22b',devices=['h100-sxm'])
        self.assertEqual(moe['summary']['persistent_state_bytes'],16*235093634560)
        for kw in ({'efficiencies':[.4]},{'efficiencies':['0']},{'unavailable_seconds':30*86400}):
            with self.assertRaises(ValueError):calculate(**kw)
