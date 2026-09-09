import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.hardware import catalog, markdown_catalog, select_device, select_peak, validate_device
from infra_calc.topics.training_deadline import calculate


class NpuAggregateTests(unittest.TestCase):
    def test_official_scope_and_missing_conditions(self):
        for identifier, fp16, int8 in (('atlas-800i-a3-8npu',4480,8960),('atlas-800t-a3-8npu',6000,12000)):
            d = select_device(identifier)
            self.assertEqual(d['spec_scope'], 'npu_aggregate')
            self.assertEqual(d['npu_count'], 8)
            self.assertNotIn('gpu_count', d)
            self.assertEqual(d['memory']['nominal_capacity'], 8*128)
            self.assertIsNone(d['memory']['bandwidth_bytes_per_second'])
            self.assertEqual([p['tera_ops_per_second'] for p in d['peak_rates']], [fp16,int8])
            with self.assertRaises(ValueError): select_peak(d,'FP16','FP32','cube','dense')
        self.assertIn('8 NPU aggregate', markdown_catalog(catalog()))

    def test_invalid_aggregate_counts(self):
        original = select_device('atlas-800i-a3-8npu')
        for mutation in ({'npu_count':1},{'npu_count':True},{'gpu_count':8}):
            d=copy.deepcopy(original);d.update(mutation)
            with self.assertRaises(ValueError): validate_device(d)
