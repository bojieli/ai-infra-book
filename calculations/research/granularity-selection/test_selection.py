import unittest
from fractions import Fraction as F
from calculate import calculate

class SelectionTests(unittest.TestCase):
    def test_work_and_capacity(self):
        r=calculate();a,b=r['variants']
        for row in (a,b):
            self.assertEqual(row['max_rank_expert_flops'],94*16*8*6*4096*1536//8)
            self.assertEqual(row['total_wire_bytes'],108017280)
        self.assertEqual(b['peak_necessary_capacity_bytes']-a['peak_necessary_capacity_bytes'],94*(256-64)*4096*2)
        for capacity,expected in ((a['peak_necessary_capacity_bytes']-1,[False,False]),(a['peak_necessary_capacity_bytes'],[True,False]),(b['peak_necessary_capacity_bytes'],[True,True])):
            self.assertEqual([x['necessary_capacity_fits'] for x in calculate(capacity_bytes=capacity)['variants']],expected)

    def test_threshold_and_common_wire(self):
        r=calculate();threshold=F(r['fine_strictly_faster_rate_threshold_exact'])
        floor=threshold.numerator//threshold.denominator
        for rate,wins in ((floor,False),(floor+1,True)):
            a,b=calculate(fine_flops_per_second=rate)['variants']
            self.assertEqual(F(b['conditional_subaccount_seconds_exact'])<F(a['conditional_subaccount_seconds_exact']),wins)
        self.assertEqual(calculate(wire_bytes_per_second=1_000_000)['fine_strictly_faster_rate_threshold_exact'],str(threshold))

    def test_router_replication_and_cost(self):
        r=calculate()
        for row,E,K in zip(r['variants'],(64,256),(4,16)):
            self.assertEqual(row['router_gemm_flops_per_rank'],2*94*16*4096*E)
            self.assertEqual(row['router_matrix_flops_all_replicas'],8*row['router_gemm_flops_per_rank'])
            expected=2*94*(16*4096+4096*E+16*E)
            self.assertEqual(row['router_gemm_operand_bytes_per_rank'],expected)
            self.assertEqual(row['router_selection_work_per_rank']['renormalize_scalar_flops'],94*16*(2*K-1))
            self.assertIsNone(row['router_selection_seconds'])
            self.assertEqual(F(row['serial_router_seconds_exact']),F(row['router_gemm_flops_per_rank'],100_000_000_000_000)+F(expected,3_000_000_000_000))
        self.assertNotEqual(calculate(router_flops_per_second=50_000_000_000_000)['fine_strictly_faster_rate_threshold_exact'],r['fine_strictly_faster_rate_threshold_exact'])

    def test_remaining_costs_and_admission(self):
        base=calculate(fine_flops_per_second=150_000_000_000_000)
        self.assertIsNone(base['conditional_capacity_eligible_fastest_variants'])
        slack=F(base['fine_remaining_minus_coarse_must_be_less_than_seconds_exact'])*10**9
        floor=slack.numerator//slack.denominator
        self.assertGreater(floor,0)
        for remaining,winner in ((floor,'fine256-k16'),(floor+1,'coarse64')):
            r=calculate(fine_flops_per_second=150_000_000_000_000,coarse_remaining_ns=0,fine_remaining_ns=remaining)
            self.assertEqual(r['conditional_capacity_eligible_fastest_variants'],[winner])
        self.assertIsNone(calculate(coarse_remaining_ns=0)['conditional_capacity_eligible_fastest_variants'])
        self.assertEqual(calculate(coarse_remaining_ns=0,fine_remaining_ns=0,capacity_bytes=1)['conditional_capacity_eligible_fastest_variants'],[])
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):calculate(fine_remaining_ns=bad)

    def test_replay_and_unknown(self):
        r=calculate();self.assertEqual(r,calculate(**r['scenario']))
        for x in r['variants']:
            self.assertIsNone(x['quality']);self.assertIsNone(x['full_runtime_seconds'])
        for kwargs in ({'capacity_bytes':True},{'fine_flops_per_second':0},{'operand_bytes_per_second':1.5}):
            with self.assertRaises(ValueError):calculate(**kwargs)

if __name__=='__main__':unittest.main()
