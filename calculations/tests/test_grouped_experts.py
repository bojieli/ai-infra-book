from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.grouped_experts import calculate


class GroupedExpertTests(unittest.TestCase):
    def test_independent_padding_and_weight_rereads(self):
        for tokens in (1,33,128,2048):
            r=calculate(tokens=tokens);s=r['summary']
            counts=[0]*128
            for i in range(tokens):
                for j in range(8):counts[(i*8+j)%128]+=1
            blocks=sum((m+63)//64 for m in counts)
            self.assertEqual(s['valid_matrix_flops'],tokens*8*6*4096*1536)
            self.assertEqual(s['padded_matrix_flops'],blocks*64*6*4096*1536)
            self.assertEqual(s['tile_schedule_weight_read_bytes'],blocks*36*1024**2)
            self.assertEqual(s['distinct_expert_weight_bytes'],sum(m>0 for m in counts)*36*1024**2)

    def test_same_routing_different_placement(self):
        contiguous=calculate(routing='concentrated')['summary']
        striped=calculate(routing='concentrated',placement='striped')['summary']
        for key in ('valid_matrix_flops','padded_matrix_flops','tile_schedule_next_level_bytes'):
            self.assertEqual(contiguous[key],striped[key])
        self.assertEqual(F(contiguous['valid_rank_imbalance_exact']),8)
        self.assertEqual(F(striped['valid_rank_imbalance_exact']),1)
        self.assertEqual(contiguous['max_rank_padded_flops'],8*striped['max_rank_padded_flops'])
        self.assertEqual(F(calculate()['summary']['padding_work_ratio_exact']),8)

    def test_nondivisible_k_n_and_empty_experts(self):
        r=calculate(tokens=1,tile_m=3,tile_k=100,tile_n=100)
        count=0;work=0
        for expert in r['grouped_expert_rows']:
            self.assertEqual(bool(expert['kernels']),expert['tokens']>0)
            for kernel in expert['kernels']:
                m,k,n=kernel['shape']
                blocks=((m+2)//3)*((k+99)//100)*((n+99)//100)
                work+=blocks*2*3*100*100;count+=1
        self.assertEqual(count,24)
        self.assertEqual(work,r['summary']['padded_matrix_flops'])
        with self.assertRaises(ValueError):calculate(participants=3)


class ExpertReplicaTests(unittest.TestCase):
    def test_logical_task_conservation_and_padding_cost(self):
        for tokens in (1,33,128):
            base=calculate(tokens=tokens,routing='concentrated')
            r=calculate(tokens=tokens,routing='concentrated',replicas=[dict(expert=0,rank=4)])
            counts={}
            for row in r['grouped_expert_rows']:
                counts[row['expert']]=counts.get(row['expert'],0)+row['tokens']
            self.assertEqual([counts[i] for i in range(128)],[tokens]*8+[0]*120)
            self.assertEqual(r['summary']['valid_matrix_flops'],base['summary']['valid_matrix_flops'])
            self.assertEqual(r['summary']['replica_weight_bytes'],36*1024**2)
            self.assertEqual(r['summary']['rerouted_token_expert_tasks'],tokens//2)
        # 33 splits into 17+16, both still execute a 64-row tile.
        s=calculate(tokens=33,routing='concentrated',replicas=[dict(expert=0,rank=4)])['summary']
        self.assertEqual(s['max_rank_padded_flops_reduction'],0)
        self.assertEqual(s['added_padded_flops'],64*6*4096*1536)

    def test_replica_capacity_and_hot_split(self):
        copies=[dict(expert=i,rank=i+1) for i in range(7)]
        s=calculate(routing='concentrated',replicas=copies)['summary']
        self.assertEqual(s['replica_weight_bytes_per_rank'],[0]+[36*1024**2]*7)
        self.assertEqual(s['equivalent_full_model_kv_tokens_per_rank_floor'],[0]+[196]*7)
        self.assertEqual(s['max_rank_padded_flops'],(7*64+128)*6*4096*1536)
        self.assertEqual(s['added_padded_flops'],0)
        for copies in ([dict(expert=0,rank=0)],[dict(expert=128,rank=1)],
                       [dict(expert=0,rank=1),dict(expert=0,rank=1)]):
            with self.assertRaises(ValueError):calculate(replicas=copies)
