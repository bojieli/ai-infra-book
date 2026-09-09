from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.replica_payback import calculate


class ReplicaPaybackTests(unittest.TestCase):
    def test_strict_threshold_and_serial_copy(self):
        r=calculate();s=r['summary'];n=s['algebraic_strict_payback_batches']
        self.assertEqual(F(s['serialized_copy_setup_ns_exact']),F(7*36*1024**2,25)+7*5000)
        old=F(s['baseline_batch_ns_exact']);new=F(s['replicated_batch_ns_exact']);setup=F(s['serialized_copy_setup_ns_exact'])
        self.assertGreaterEqual(setup+(n-1)*new,(n-1)*old)
        self.assertLess(setup+n*new,n*old)
        self.assertEqual(calculate(batches=n)['summary']['selected_deployment'],'replicated')
        self.assertEqual(calculate(batches=n-1)['summary']['selected_deployment'],'baseline')
        for name in ('baseline','replicated'):
            times=[max(F(row['compute_ns_exact']),F(row['interface_ns_exact']))
                   for row in r['replica_service_rows'] if row['deployment']==name]
            self.assertEqual(max(times),old if name=='baseline' else new)

    def test_incremental_capacity_exact_boundary(self):
        fit=calculate(extra_budget_bytes_per_rank=36*1024**2)['summary']
        fail=calculate(extra_budget_bytes_per_rank=36*1024**2-1)['summary']
        self.assertTrue(fit['capacity_feasible']);self.assertFalse(fail['capacity_feasible'])
        self.assertEqual(fail['over_budget_ranks'],list(range(1,8)))
        self.assertIsNone(fail['feasible_strict_payback_batches'])
        self.assertEqual(fail['selected_deployment'],'baseline')

    def test_padding_no_payback_and_no_replicas(self):
        s=calculate(workload=dict(tokens=33,routing='concentrated',replicas=[dict(expert=0,rank=4)]),interface_bytes_per_second=10**15)['summary']
        # With ample interface supply, unchanged compute work remains the bottleneck.
        self.assertEqual(F(s['per_batch_saving_ns_exact']),0)
        self.assertIsNone(s['algebraic_strict_payback_batches'])
        s=calculate(workload={})['summary']
        self.assertEqual(F(s['serialized_copy_setup_ns_exact']),0)
        self.assertEqual(s['selected_deployment'],'baseline')
