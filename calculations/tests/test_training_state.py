from pathlib import Path
import sys
import unittest
from math import prod
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.training_state import calculate


class TrainingStateTests(unittest.TestCase):
    def test_qwen8_independent_geometry_and_stage_formulas(self):
        # Embedding/head, 36 attention + MLP + norm blocks, and final norm.
        n=2*151936*4096+36*(2*4096**2+2*4096*1024+3*4096*12288+2*128+2*4096)+4096
        r=calculate()
        self.assertEqual(r['summary']['parameters'],n)
        for row,coefficient in zip(r['training_state_stages'],(16,4+12/8,2+14/8,16/8)):
            self.assertEqual(row['persistent_bytes_per_rank'],int(n*coefficient))
            for item in row['components']:
                self.assertEqual(item['cluster_bytes'],item['unique_payload_bytes']+item['partition_padding_bytes']+item['replicated_extra_bytes'])
        fp32=calculate(gradient_bytes=4)
        for stage in range(4):
            delta=fp32['training_state_stages'][stage]['persistent_bytes_per_rank']-r['training_state_stages'][stage]['persistent_bytes_per_rank']
            self.assertEqual(delta,2*n//(8 if stage>=2 else 1))

    def test_per_tensor_padding_and_exact_capacity(self):
        r=calculate(participants=7,partition='per_tensor')
        # Enumerate strided assignments of each physical tensor, including its padding.
        shard=sum(len(range(0,prod(t['shape']),7))*t['copies'] for t in r['training_state_tensors'])
        self.assertEqual(r['summary']['padded_shard_elements_per_rank'],shard)
        flat=calculate(participants=7)
        self.assertGreaterEqual(shard,flat['summary']['padded_shard_elements_per_rank'])
        need=r['training_state_stages'][3]['persistent_bytes_per_rank']
        for delta,expected in ((0,True),(-1,False)):
            x=calculate(participants=7,partition='per_tensor',extra_live_bytes=123,capacity_bytes=need+123+delta)
            self.assertEqual(x['training_state_stages'][3]['specified_allocations_fit'],expected)

    def test_moe_all_experts_and_dp_one(self):
        r=calculate(model='qwen3-235b-a22b',participants=1)
        self.assertEqual(r['summary']['parameters'],235093634560)
        self.assertEqual(len(set(row['persistent_bytes_per_rank'] for row in r['training_state_stages'])),1)
        expert_parameters=sum(t['parameters'] for t in r['training_state_tensors'] if '.experts.' in t['name'])
        self.assertEqual(expert_parameters,94*128*3*4096*1536)
        for kwargs in ({'participants':True},{'gradient_bytes':1},{'partition':'backend_default'}):
            with self.assertRaises(ValueError):calculate(**kwargs)
