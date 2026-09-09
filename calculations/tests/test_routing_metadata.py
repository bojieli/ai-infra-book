from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.routing_metadata import calculate


class RoutingMetadataTests(unittest.TestCase):
    def test_official_geometries_and_shared_exclusion(self):
        for model,layers,experts,k in [('qwen3-30b-a3b',48,128,8),('qwen3-235b-a22b',94,128,8),('deepseek-v4-flash',43,256,6),('deepseek-v4-pro',61,384,6),('kimi-k3',92,896,16)]:
            r=calculate(model=model);s=r['summary']
            self.assertEqual(s['routed_id_bytes'],8192*layers*k*2)
            self.assertEqual(s['routed_experts'],experts)
        self.assertEqual(calculate()['summary']['routed_id_bytes'],6*1024**2)
        self.assertEqual(calculate(model='kimi-k3')['summary']['moe_layer_ids'],list(range(1,93)))

    def test_encoding_boundary_and_mask_tail(self):
        self.assertEqual(calculate(model='deepseek-v4-flash',encoding='uint8')['summary']['minimum_unsigned_bits_per_id'],8)
        for model in ('deepseek-v4-pro','kimi-k3'):
            with self.assertRaises(ValueError):calculate(model=model,encoding='uint8')
        r=calculate(tokens=9)
        self.assertEqual(r['routing_metadata_components']['validity_bitset_bytes'],2)
        self.assertEqual(r['summary']['complete_declared_payload_bytes'],9*48*8*2+9*24+2+128)

    def test_copies_and_transport_boundary(self):
        r=calculate(tokens=8,token_rate_per_second=8);size=r['summary']['complete_declared_payload_bytes']
        equal=calculate(tokens=8,token_rate_per_second=8,bandwidth_bytes_per_second=size,retained_copies=3)
        self.assertFalse(equal['summary']['transport_has_strict_slack'])
        self.assertEqual(equal['summary']['retained_payload_bytes'],3*size)
        self.assertEqual(F(equal['summary']['one_payload_transfer_exact_seconds']),1)
        self.assertTrue(calculate(tokens=8,token_rate_per_second=8,bandwidth_bytes_per_second=size+1)['summary']['transport_has_strict_slack'])
