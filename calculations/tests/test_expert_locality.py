from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.expert_locality import calculate, reuse_regions


class ExpertLocalityTests(unittest.TestCase):
    def test_explicit_routes_and_weight_union(self):
        for tokens in (1,16,128,2048):
            result=calculate(tokens=tokens);s=result['summary']
            routes=[[(i*8+j)%128 for j in range(8)] for i in range(tokens)]
            assignments=[e for row in routes for e in row if e>=32]
            self.assertEqual(s['remote_token_expert_tasks'],len(assignments))
            self.assertEqual(s['remote_active_experts'],len(set(assignments)))
            self.assertEqual(s['remote_distinct_weight_bytes'],len(set(assignments))*36*1024**2)
            self.assertEqual(s['remote_matrix_flops'],len(assignments)*3*2*4096*1536)
            self.assertEqual(sum(row['matrix_flops'] for row in result['locality_experts']),tokens*8*3*2*4096*1536)

    def test_service_resources(self):
        s=calculate()['summary']
        tasks=768;weights=96*36*1024**2;flops=tasks*6*4096*1536
        cpu=F(2*tasks*4096*2,25)+2*96*5000+max(F(flops,2000),F(weights,200))
        copy=F(weights,25)+96*5000+max(F(flops,100000),F(weights,1000))
        self.assertEqual(F(s['cpu_service_ns_exact']),cpu)
        self.assertEqual(F(s['weight_copy_service_ns_exact']),copy)
        self.assertEqual(s['resident_expert_weight_bytes_all_layers'],32*36*1024**2*94)

    def test_resident_and_concentrated_edges(self):
        for args in ({'resident_experts':128},{'routing':'concentrated'}):
            s=calculate(**args)['summary']
            self.assertEqual(s['remote_active_experts'],0)
            self.assertEqual(F(s['cpu_service_ns_exact']),0)
        a=calculate(tokens=16,resident_experts=0,routing='concentrated')['summary']
        b=calculate(tokens=32,resident_experts=0,routing='concentrated')['summary']
        self.assertEqual(a['remote_distinct_weight_bytes'],b['remote_distinct_weight_bytes'])
        self.assertEqual(b['remote_matrix_flops'],2*a['remote_matrix_flops'])
        with self.assertRaises(ValueError):calculate(resident_experts=129)


class ReuseRegionTests(unittest.TestCase):
    def test_affine_regions_against_direct_integer_evaluation(self):
        # Includes different knee orderings, roots, ties, and final slopes.
        from itertools import product
        for a,c,x,y,z in product((1,4),(1,6),(0,2),(0,7),(0,9)):
            regions=reuse_regions(a,12,c,18,x,y,z)
            self.assertEqual(regions[0]['min_tokens_per_expert'],1)
            self.assertIsNone(regions[-1]['max_tokens_per_expert'])
            for left,right in zip(regions,regions[1:]):
                self.assertEqual(left['max_tokens_per_expert']+1,right['min_tokens_per_expert'])
            for m in [*range(1,100),10**6]:
                matches=[r for r in regions if r['min_tokens_per_expert']<=m and
                         (r['max_tokens_per_expert'] is None or m<=r['max_tokens_per_expert'])]
                self.assertEqual(len(matches),1)
                cpu=x*m+y+max(a*m,12);gpu=z+max(c*m,18)
                winner='cpu' if cpu<gpu else 'copy-to-gpu' if gpu<cpu else 'equal'
                self.assertEqual(matches[0]['winner'],winner)

    def test_default_exact_threshold(self):
        r=calculate()
        self.assertEqual(r['reuse_knees']['cpu_equal_compute_weight_tokens_exact'],'10')
        self.assertEqual(r['reuse_knees']['gpu_equal_compute_weight_tokens_exact'],'100')
        self.assertEqual(r['locality_reuse_regions'],[
            dict(min_tokens_per_expert=1,max_tokens_per_expert=78,winner='cpu'),
            dict(min_tokens_per_expert=79,max_tokens_per_expert=None,winner='copy-to-gpu')])
        for m in (78,79):
            s=calculate(tokens=m,resident_experts=0,routing='concentrated')['summary']
            self.assertEqual(s['cpu_lower_than_weight_copy_in_declared_model'],m==78)
