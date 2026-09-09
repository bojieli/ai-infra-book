import sys
import unittest
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.growing_remote_kv import calculate

class GrowingKVTests(unittest.TestCase):
    def test_history_current_and_replica_conservation(self):
        for model,unit in [('qwen3-8b',147456),('qwen3.6-35b-a3b',20480)]:
            for policy in ('remote_all','remote_prefix_local_tail'):
                r=calculate(model=model,batch=2,prompt=7,steps=5,copies=3,placement=policy)
                s=r['summary'];u=2*unit
                self.assertEqual(s['prior_history_logical_read_bytes'],u*sum(range(7,12)))
                self.assertEqual(s['remote_prior_read_bytes']+s['local_prior_read_bytes'],s['prior_history_logical_read_bytes'])
                self.assertEqual(s['current_kv_operand_bytes'],5*u)
                self.assertEqual(s['append_replica_network_bytes'],15*u if policy=='remote_all' else 0)
                self.assertEqual(s['initial_copy_network_bytes'],3*7*u)
                self.assertEqual(s['remote_final_bytes_per_replica']+s['local_tail_final_bytes'],12*u)
                self.assertEqual(s['local_fixed_state_bytes'],0 if model=='qwen3-8b' else 2*64880640)
    def test_epoch_and_shared_sender_schedule(self):
        r=calculate(prompt=3,steps=4,copies=3,bandwidth_bytes_per_second=10**9,startup_ns=7)
        lengths=[3]*3;cursor=Fraction(r['summary']['initial_copy_seconds_exact'])
        for row in r['steps']:
            self.assertEqual(lengths,[row['required_remote_epoch']]*3)
            self.assertEqual(Fraction(row['read_start_seconds_exact']),cursor)
            cursor+=Fraction(7+row['remote_prior_read_bytes'],10**9)
            for write in row['replica_writes']:
                self.assertEqual(Fraction(write['start_seconds_exact']),cursor)
                self.assertEqual(write['position'],lengths[write['replica']])
                lengths[write['replica']]+=1
                cursor+=Fraction(7+write['bytes'],10**9)
                self.assertEqual(Fraction(write['commit_seconds_exact']),cursor)
            self.assertEqual(row['remote_lengths_after'],lengths)
        self.assertEqual(Fraction(r['summary']['communication_skeleton_seconds_exact']),cursor)
    def test_prefix_tradeoff_and_budget_boundary(self):
        all_remote=calculate(prompt=7,steps=5,copies=2)
        prefix=calculate(prompt=7,steps=5,copies=2,placement='remote_prefix_local_tail')
        self.assertEqual(all_remote['summary']['remote_prior_read_bytes']-prefix['summary']['remote_prior_read_bytes'],147456*10)
        for budget,fits in [(5*147456,True),(5*147456-1,False)]:
            r=calculate(prompt=7,steps=5,placement='remote_prefix_local_tail',local_tail_budget_bytes=budget)
            self.assertEqual(r['summary']['local_tail_budget_fits'],fits)
            self.assertIsNone(r['summary']['actual_decode_seconds'])
            self.assertIsNone(r['summary']['actual_task_feasible'])
    def test_zero_append_and_replay(self):
        r=calculate(prompt=7,steps=0,copies=2)
        self.assertEqual(r['steps'],[])
        self.assertEqual(r['summary']['total_network_bytes'],2*7*147456)
        self.assertEqual(r['summary']['token_communication_seconds_exact'],'0')
        self.assertEqual(r,calculate(**r['scenario']))
    def test_reject_invalid(self):
        for args in ({'steps':True},{'steps':-1},{'copies':4},{'placement':'quorum'},
                     {'model':'qwen3-235b-a22b'},{'startup_ns':1.5},{'local_tail_budget_bytes':-1},
                     {'prompt':262144,'steps':1}):
            with self.assertRaises(ValueError):calculate(**args)

if __name__=='__main__':unittest.main()
