"""Independent publisher tree sums and exact memory-budget edges."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.paths import PROJECT
from infra_calc.topics.gguf_inventory import calculate


class GGUFInventoryTests(unittest.TestCase):
    def test_direct_tree_sums(self):
        raw=json.loads((PROJECT/'sources/gguf-qwen235/tree.json').read_text())
        totals={}
        for entry in raw:
            if entry['path'].endswith('.gguf'):
                key=entry['path'].split('/')[0];totals[key]=totals.get(key,0)+entry['size']
        r=calculate()
        self.assertEqual(r['summary']['all_variant_file_totals'],totals)
        self.assertEqual(r['summary']['complete_gguf_files'],72)
        self.assertEqual(totals['Q4_K_M'],49944699648+49930349824+42279026016)
        self.assertEqual(totals['Q2_K'],49906752544+35784249568)

    def test_one_kv_exact_budget_boundary(self):
        r=calculate(variants=['Q2_K']);size=r['gguf_variants'][0]['file_bytes'];kv=r['summary']['bf16_kv_bytes_per_independent_request']
        for delta,count in [(-1,0),(0,1),(kv-1,1),(kv,2)]:
            row=calculate(memory_budget_bytes=size+kv+delta,reserved_bytes=0,variants=['Q2_K'])['gguf_variants'][0]
            self.assertEqual(row['max_independent_bf16_kv_requests'],count)
        self.assertEqual(r['summary']['bf16_kv_bytes_per_token'],2*94*4*128*2)

    def test_context_and_reservation_change_capacity(self):
        short=calculate();long=calculate(context_tokens=32768)
        self.assertEqual(short['gguf_variants'][0]['max_independent_bf16_kv_requests'],1)
        self.assertEqual(long['gguf_variants'][0]['max_independent_bf16_kv_requests'],0)
        self.assertEqual(long['summary']['bf16_kv_bytes_per_independent_request'],4*short['summary']['bf16_kv_bytes_per_independent_request'])
        with self.assertRaises(ValueError):calculate(variants=['not-a-variant'])
        with self.assertRaises(ValueError):calculate(memory_budget_bytes=1,reserved_bytes=2)
