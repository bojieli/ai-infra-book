"""Direct independent softmax reference, masked identity and merge-tree checks."""
import math
import random
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.online_softmax import calculate,block_state,merge,finish,tree_merge


class OnlineSoftmaxTests(unittest.TestCase):
    def test_book_example_rejects_equal_weight_average(self):
        s=calculate()['summary']
        self.assertAlmostEqual(s['direct_output'][0],-1/7,places=14)
        self.assertAlmostEqual(s['sequential_output'][0],-1/7,places=14)
        self.assertAlmostEqual(s['naive_mean_of_block_outputs'][0],1/6,places=14)
        self.assertEqual(s['merge_exp_calls'],2)
        self.assertEqual(s['merge_weighted_sum_flops'],6)

    def test_masked_and_empty_identity(self):
        state=block_state([1000],[[2,3]])
        self.assertEqual(merge(None,state),state)
        self.assertEqual(merge(state,None),state)
        self.assertIsNone(block_state([-math.inf,None],[[1],[2]]))
        self.assertIsNone(finish(tree_merge([None,None])))
        s=calculate(scores=[None,None],values=[[1],[2]],block_sizes=[0,1,1])['summary']
        self.assertIsNone(s['direct_output']);self.assertEqual(s['nontrivial_merges'],0)

    def test_random_vector_partitions_against_independent_reference(self):
        rng=random.Random(529)
        for length in [1,3,17,33]:
            scores=[rng.uniform(990,1010) for _ in range(length)]
            values=[[rng.uniform(-3,3) for _ in range(5)] for _ in scores]
            maximum=max(scores);weights=[math.exp(s-maximum) for s in scores]
            expected=[sum(w*v[j] for w,v in zip(weights,values))/sum(weights) for j in range(5)]
            states=[block_state(scores[i:i+4],values[i:i+4]) for i in range(0,length,4)]
            states.insert(1,None)
            sequential=None
            for state in states:sequential=merge(sequential,state)
            for result in [finish(sequential),finish(tree_merge(states)),finish(tree_merge(states[::-1]))]:
                for a,b in zip(result,expected):self.assertAlmostEqual(a,b,places=12)
        with self.assertRaises(ValueError):block_state([math.inf],[[1]])
