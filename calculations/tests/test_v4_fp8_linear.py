import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
"""Independent tile enumeration and official projection selection checks."""
import unittest
from infra_calc.topics.v4_fp8_linear import account, calculate


class V4FP8LinearTests(unittest.TestCase):
    def test_tile_enumeration_and_scale_sharing(self):
        for m in (1, 31, 32, 33, 64):
            a = account(m, 256, 384)
            tiled = scale = 0
            for row in range(0, m, 32):
                for column in range(0, 384, 128):
                    for inner in range(0, 256, 128):
                        tiled += 2 * 32 * 128 * 128
                        scale += 32 + 2 * 32 * 128
            self.assertEqual(a['padded_tile_matrix_flops'], tiled)
            self.assertEqual(a['padded_scale_flops'], scale)
            self.assertEqual(a['logical_scale_flops'], m * 3 * 2 + 2 * m * 384 * 2)
            self.assertEqual(a['valid_matrix_flops'], 2 * m * 256 * 384)

    def test_interface_bytes_and_rejections(self):
        a = account(9, 128, 256)
        # Quant reads BF16, writes FP8 + E8M0; GEMM consumes these and weights/scales.
        self.assertEqual(a['total_interface_bytes'], 9*128*4 + 9*2 + 256*128 + 2 + 9*256*2)
        self.assertEqual(a['activation_max_comparisons'], 9 * (127 + 1))
        self.assertEqual(a['activation_quantization_scalar_flops'], 9 * 128 + 9)
        for dims in [(0, 128, 256), (True, 128, 256), (1, 129, 256), (1, 128, 255)]:
            with self.assertRaises(ValueError):
                account(*dims)

    def test_official_geometry_and_repeat_counts(self):
        for model, layers, width, qrank in [('deepseek-v4-flash', 43, 4096, 1024),
                                           ('deepseek-v4-pro', 61, 7168, 1536)]:
            r = calculate(model, tokens=1, history=8192)
            rows = {x['name']: x for x in r['v4_fp8_linear_rows']}
            self.assertEqual(set(rows), {'wq_a','wq_b','wkv_shared','wo_b','index_wq_b',
                                         'shared_gate','shared_up','shared_down'})
            self.assertEqual(rows['wq_a']['per_invocation']['weight_shape'], [qrank, width])
            self.assertEqual(rows['wq_a']['totals']['valid_matrix_flops'], 2 * layers * width * qrank)
            self.assertEqual(rows['shared_gate']['invocation_count'], layers)
            self.assertEqual(rows['shared_up']['invocation_count'], layers)
            self.assertEqual(r['summary']['padded_tile_matrix_flops'], 32 * r['summary']['valid_matrix_flops'])
        with self.assertRaises(ValueError):
            calculate(tokens=2, history=8192)
