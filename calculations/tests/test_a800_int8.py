import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.hardware import select_device, select_peak
from infra_calc.paths import PROJECT


class A800Int8Tests(unittest.TestCase):
    def test_evidence_and_precision_separation(self):
        device = select_device('a800-40gb-active')
        peak = next(p for p in device['peak_rates'] if p['input_precision'] == 'INT8')
        self.assertEqual(peak['tera_ops_per_second'], 1247)
        self.assertEqual((peak['sparsity'], peak['operation_kind'], peak['accumulator_precision']),
                         ('structured', 'integer', 'unspecified'))
        raw = (PROJECT / 'sources/hardware/nvidia-a800-active-page.html').read_text()
        self.assertIn('Theoretical INT8 TOPS using sparsity', raw)
        self.assertIn('structural sparsity', raw)
        for precision, accumulator, sparsity in (('INT8','unspecified','structured'),
                                                ('INT8','INT32','structured'),
                                                ('BF16','FP32','dense')):
            with self.assertRaises(ValueError):
                select_peak(device, precision, accumulator, 'tensor', sparsity)
