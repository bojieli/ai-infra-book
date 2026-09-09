"""Textbook constants and explicit tail-tile memory-event enumeration."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.gemm_tiles import account,calculate


class GemmTileTests(unittest.TestCase):
    def test_book_constants(self):
        r=calculate(); self.assertEqual(r['summary']['one_read_write_payload_bytes'],128*2**20)
        self.assertEqual(r['summary']['valid_matrix_flops'],103079215104)
        for row,capacity,traffic in zip(r['gemm_tile_rows'],[8,24,80],[6168,3096,1560]):
            self.assertEqual(row['reserved_working_bytes'],capacity*1024)
            self.assertEqual(row['next_level_bytes'],traffic*2**20)

    def test_explicit_load_store_enumeration_with_tail(self):
        m,k,n,tm,tk,tn=3,5,4,2,3,3
        for order in ['output-stationary','k-outer']:
            a=b=c=partial_load=partial_store=0
            for i in range(0,m,tm):
                for j in range(0,n,tn):
                    for q in range(0,k,tk):
                        a+=sum(2 for x in range(i,min(i+tm,m)) for z in range(q,min(q+tk,k)))
                        b+=sum(2 for z in range(q,min(q+tk,k)) for y in range(j,min(j+tn,n)))
                        for x in range(i,min(i+tm,m)):
                            for y in range(j,min(j+tn,n)):
                                if q+tk>=k: c+=2
                                elif order=='k-outer': partial_store+=4
                                if q and order=='k-outer': partial_load+=4
            r=account(m,k,n,tm,tk,tn,order)
            self.assertEqual([r[key] for key in ['a_read_bytes','b_read_bytes','output_write_bytes','partial_load_bytes','partial_store_bytes']], [a,b,c,partial_load,partial_store])
            self.assertEqual(r['valid_matrix_flops'],120)
            self.assertEqual(r['fully_padded_matrix_flops'],288)

    def test_capacity_and_double_buffer_are_not_speed_predictions(self):
        base=calculate(); doubled=calculate(input_buffers=2)
        self.assertEqual([r['next_level_bytes'] for r in base['gemm_tile_rows']],[r['next_level_bytes'] for r in doubled['gemm_tile_rows']])
        self.assertEqual(base['summary']['feasible_candidates'],3)
        self.assertEqual(doubled['summary']['feasible_candidates'],2)
        self.assertIsNone(calculate(capacity_bytes=1)['summary']['best_enumerated_tile'])
        with self.assertRaises(ValueError): calculate(model='qwen3-235b-a22b')
