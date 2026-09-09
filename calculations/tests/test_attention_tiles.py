"""Book constants and explicit causal query/key tile enumeration."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.attention_tiles import calculate


class AttentionTileTests(unittest.TestCase):
    def test_book_capacity_and_traffic(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['one_read_write_qkvo_bytes'],8*2**20)
        self.assertEqual(s['separate_score_probability_read_write_bytes'],2**30)
        self.assertEqual(s['valid_matrix_flops'],34359738368)
        for row,a,mib,pairs in zip(r['attention_tile_rows'],[166,110,76],[204,304,436],[409600,9600,6912]):
            self.assertEqual(row['query_block'],a)
            self.assertEqual(row['interface_bytes'],mib*2**20)
            self.assertEqual(row['kv_block_pairs'],pairs)
            self.assertLessEqual(row['reserved_working_bytes'],131072)
            self.assertGreater(row['reserved_working_bytes']+6*128+4*row['kv_block']+12,131072)
            self.assertEqual(row['old_output_scale_multiplications'],8192*128*((8192+row['kv_block']-1)//row['kv_block']-1))

    def test_causal_boundary_and_row_updates(self):
        row=calculate(tokens=7,capacity_bytes=4096,kv_blocks=[3],causal=True)['attention_tile_rows'][0]
        a=row['query_block'];rectangular=valid=updates=0
        for qs in range(0,7,a):
            qe=min(qs+a,7)
            for ks in range(0,qe,3):
                ke=min(ks+3,7)
                for q in range(qs,qe):
                    visible=False
                    for k in range(ks,ke):
                        rectangular+=1
                        if k<=q:valid+=1;visible=True
                    updates+=visible
        self.assertEqual(row['rectangular_visited_tile_matrix_flops'],4*128*rectangular)
        self.assertEqual(row['valid_matrix_flops'],4*128*valid)
        self.assertEqual(valid,28)
        self.assertEqual(row['row_state_updates'],updates)
        self.assertEqual(row['old_output_scale_multiplications'],(updates-7)*128)

    def test_second_slot_recounts_capacity(self):
        a=calculate()['attention_tile_rows'];b=calculate(kv_slots=2)['attention_tile_rows']
        self.assertLess(b[1]['query_block'],a[1]['query_block'])
        self.assertGreater(b[1]['interface_bytes'],a[1]['interface_bytes'])
        self.assertIsNone(calculate(capacity_bytes=1)['summary']['best_enumerated_interface_bytes'])
