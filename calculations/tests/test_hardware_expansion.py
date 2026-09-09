"""Cross-field regressions for official SKU and resource-scope boundaries."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.hardware import catalog, select_peak, audit_catalog, validate_device


class HardwareExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = catalog()
        cls.devices = {d['id']: d for d in cls.data['devices']}

    def test_apple_memory_is_constrained_by_gpu_bin_and_host(self):
        ids = self.devices
        for valid in ('m2-max-38gpu-96gb', 'm3-ultra-80gpu-512gb',
                      'm4-pro-16gpu-64gb', 'm5-pro-16gpu-64gb'):
            self.assertIn(valid, ids)
        for invalid in ('m2-max-30gpu-96gb', 'm3-max-40gpu-96gb',
                        'm5-ultra-64gpu-512gb'):
            self.assertNotIn(invalid, ids)
        memory = ids['m3-ultra-80gpu-512gb']['memory']
        self.assertNotEqual(memory['source_id'], memory['capacity_evidence']['source_id'])
        self.assertEqual(ids['m5-ultra-80gpu-512gb']['availability']['status'], 'announced_not_yet_available')

    def test_availability_requires_a_traceable_device_source(self):
        for key, value in (("source_id", "unbound-announcement"), ("locator", "")):
            device = copy.deepcopy(self.devices['m5-ultra-80gpu-512gb'])
            device['availability'][key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                validate_device(device)

    def test_desktop_evidence_cannot_be_reassigned_to_another_memory_or_gpu_bin(self):
        original = self.devices['m4-8gpu-24gb']
        self.assertTrue(any('iMac' in row['host_model'] for row in original['configuration_evidence']))
        for field, value in (('capacity', 32), ('gpu', 10), ('bandwidth', 240000000000)):
            device = copy.deepcopy(original)
            if field == 'capacity':
                device['memory']['nominal_capacity'] = value
            elif field == 'gpu':
                device['gpu_cores'] = value
            else:
                device['memory']['bandwidth_bytes_per_second'] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_device(device)
        larger = self.devices['m4-8gpu-32gb']
        self.assertFalse(any('iMac' in row['host_model'] for row in larger.get('configuration_evidence', [])))
        self.assertTrue(any('iMac' in note for note in larger['notes']))

    def test_ascend_board_chip_and_superpod_do_not_share_resource_scope(self):
        card = self.devices['atlas-350-112gb']
        self.assertEqual(card['memory']['nominal_capacity'], 112)
        self.assertEqual(card['memory']['bandwidth_bytes_per_second'], 1400000000000)
        with self.assertRaises(ValueError):
            select_peak(card, 'BF16', 'FP32', 'cube', 'dense')
        chip = self.devices['ascend-910-2019-chip']
        self.assertFalse(chip['power_evidence']['maximum_power_explicitly_disclosed'])
        pod = self.devices['atlas-900-a3-superpod-384npu-max']
        self.assertEqual(pod['spec_scope'], 'npu_aggregate')
        self.assertEqual(pod['npu_count'], 384)
        self.assertEqual(pod['memory']['nominal_capacity'], 384 * 128)
        self.assertIsNone(pod['memory']['bandwidth_bytes_per_second'])

    def test_whitepaper_dense_does_not_imply_accumulator_or_single_processor_scope(self):
        a2 = self.devices['atlas-a2-processor-fp16-313']
        self.assertEqual(a2['peak_rates'][0]['sparsity'], 'dense')
        with self.assertRaises(ValueError):
            select_peak(a2, 'FP16', 'FP32', 'cube', 'dense')
        for tier in (626, 752, 800):
            node = self.devices[f'atlas-900-a3-node-fp16-{tier}']
            peak = next(p for p in node['peak_rates'] if p['input_precision'] == 'FP16')
            self.assertEqual(peak['tera_ops_per_second'], 8 * tier)
            self.assertEqual(node['spec_scope'], 'npu_aggregate')
        self.assertNotEqual(round(384 * 752 / 1000, 1), 288.7)

    def test_a100_40gb_form_factors_and_b200_per_gpu_power(self):
        pcie = self.devices['a100-40gb-pcie']
        sxm = self.devices['a100-40gb-sxm']
        self.assertEqual((pcie['power_watts'], sxm['power_watts']), (250, 400))
        for device in (pcie, sxm):
            self.assertEqual(device['memory']['nominal_capacity'], 40)
            self.assertEqual(device['memory']['bandwidth_bytes_per_second'], 1555000000000)
            self.assertEqual(select_peak(device, 'BF16', 'FP32', 'tensor', 'dense')['tera_ops_per_second'], 312)
        self.assertEqual(self.devices['b200-sxm']['power_watts'], 1000)
        self.assertEqual(self.devices['b200-sxm']['form_factor'], 'SXM6')

    def test_new_system_profiles_preserve_memory_and_sparse_boundaries(self):
        gb = self.devices['gb300-superchip']
        self.assertEqual((gb['spec_scope'], gb['gpu_count']), ('gpu_aggregate', 2))
        self.assertIsNone(gb['memory']['nominal_capacity'])
        self.assertEqual({p['sparsity']: p['tera_ops_per_second'] for p in gb['peak_rates']},
                         {'dense': 30000, 'structured': 40000})
        us = self.devices['rubin-nvl72-product-profile']
        uk = self.devices['rubin-22tb-uk-product-profile']
        self.assertEqual(us['memory']['bandwidth_bytes_per_second'], 19200000000000)
        self.assertEqual(uk['memory']['bandwidth_bytes_per_second'], 22000000000000)
        inference = [p for p in uk['peak_rates'] if p['tera_ops_per_second'] == 50000]
        self.assertTrue(inference)
        self.assertTrue(all(p['sparsity'] == 'unspecified' for p in inference))
        cts = self.devices['a100-80gb-sxm-cts-500w']
        original = self.devices['a100-80gb-sxm']
        self.assertEqual(cts['power_watts'], 500)
        for p in cts['peak_rates']:
            if p['operation_kind'] == 'floating_point':
                reference = select_peak(original, p['input_precision'], p['accumulator_precision'], p['execution_unit'], p['sparsity'])
                self.assertEqual(p['tera_ops_per_second'], reference['tera_ops_per_second'])

    def test_h100_clock_domains_do_not_spill_into_unspecified_operations(self):
        d = self.devices['h100-sxm']
        low = select_peak(d, 'BF16', 'FP32', 'tensor', 'dense')
        self.assertEqual(low['clock_evidence']['gpu_boost_mhz'], 1830)
        fp32 = select_peak(d, 'FP32', 'FP32', 'vector', 'dense')
        self.assertEqual(fp32['clock_evidence']['gpu_boost_mhz'], 1980)
        unsupported = [p for p in d['peak_rates'] if p['input_precision'] == 'INT8' or
                       (p['execution_unit'] == 'vector' and p['input_precision'] in ('FP16', 'BF16'))]
        self.assertEqual(len(unsupported), 4)
        self.assertTrue(all(not p.get('clock_evidence') for p in unsupported))

    def test_every_recorded_power_has_its_own_source_pointer(self):
        audit = audit_catalog(self.data)
        power_fields = [f for d in audit['devices'] for f in d['fields'] if f['field'] == 'reported_power']
        self.assertFalse(any(f['recording_status'] == 'value_without_field_source' for f in power_fields))


if __name__ == '__main__':
    unittest.main()
