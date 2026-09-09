"""Checkpoint byte coverage and independent context/attention work deltas."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.paths import PROJECT
from infra_calc.topics.dflash_work import calculate


class DFlashWorkTests(unittest.TestCase):
    def test_header_contiguous_payload_and_shared_head(self):
        header=json.loads((PROJECT/'sources/dflash-qwen3-8b/model.safetensors.header.json').read_text())
        offsets=sorted(t['data_offsets'] for k,t in header.items() if k!='__metadata__')
        cursor=0
        for start,end in offsets:
            self.assertEqual(start,cursor)
            cursor=end
        s=calculate()['summary']
        self.assertEqual(cursor,s['draft_weight_bytes'])
        self.assertEqual(s['draft_parameters'],1048626432)
        self.assertFalse(any('lm_head' in k or 'embed_tokens' in k for k in header))
        self.assertEqual(s['shared_head_weight_bytes'],4096*151936*2)

    def test_first_vs_incremental_features_at_same_total_history(self):
        a=calculate();b=calculate(cached_context=0,new_context=1024)
        # Only feature fusion and new-context K/V projection change; attention
        # and target verification see exactly the same total history.
        delta=1020*(2*20480*4096+5*2*2*4096*1024)
        self.assertEqual(b['summary']['draft_matrix_flops']-a['summary']['draft_matrix_flops'],delta)
        self.assertEqual(a['summary']['target_verify_matrix_flops'],b['summary']['target_verify_matrix_flops'])
        self.assertEqual(b['summary']['new_target_feature_bytes'],1024*5*4096*2)

    def test_full_attention_pairs_and_crop(self):
        for block in (2,4,16):
            r=calculate(cached_context=7,new_context=3,block_size=block)
            attention=sum(x['matrix_flops'] for x in r['draft_matrices'] if x['operator'].startswith('noncausal'))
            pairs=sum(1 for _ in range(block) for _ in range(10+block))
            self.assertEqual(attention,4*5*32*128*pairs)
            s=r['summary']
            self.assertEqual(s['draft_kv_peak_bytes']-s['draft_noise_kv_discarded_bytes'],s['draft_kv_after_crop_bytes'])
            self.assertEqual(s['draft_candidates'],block-1)
        with self.assertRaises(ValueError):calculate(block_size=1)
