"""Published book constants and output-tile enumeration independent of formula."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.quantized_gemm import calculate


class QuantizedGemmTests(unittest.TestCase):
    def test_book_constants_and_full_row_requirement(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['matrix_flops'],51539607552)
        self.assertEqual([x['main_tensor_interface_bytes']//2**20 for x in r['quantization_schedules']],[444,620,588])
        self.assertEqual(s['retained_fp16_input_per_quantization_row_bytes'],8192)
        self.assertFalse(r['quantization_schedules'][2]['uses_final_full_row_scale'])
        self.assertEqual(s['full_scale_fusion_extra_main_bytes'],176*2**20)

    def test_reread_cost_vanishes_at_one_output_column_block(self):
        r=calculate(tile_n=1536)
        self.assertEqual(r['summary']['full_scale_fusion_extra_main_bytes'],0)
        self.assertEqual(r['summary']['global_fp32_row_scales_bytes'],4*4096)

    def test_tail_tiles_explicit_effective_elements(self):
        r=calculate(tokens=129,tile_m=128,tile_n=127)
        m,k=r['shapes']['A'];n=r['shapes']['Y'][1]
        activation=weight=output=scale_reads=0
        for i in range(0,m,128):
            for j in range(0,n,127):
                height=min(128,m-i);width=min(127,n-j)
                activation+=2*height*k
                weight+=k*width
                output+=2*height*width
                scale_reads+=4*height
        row=r['quantization_schedules'][1]
        self.assertEqual(row['gemm_activation_read_bytes'],activation)
        self.assertEqual(row['gemm_weight_read_bytes'],weight)
        self.assertEqual(row['output_write_bytes'],output)
        self.assertEqual(row['scale_read_bytes'],scale_reads)
        with self.assertRaises(ValueError):calculate(model='qwen3-8b')
