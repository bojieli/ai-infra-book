"""Unknown evidence must stay unknown, including when a number is present."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.hardware import audit_catalog, select_peak


class HardwareAudit(unittest.TestCase):
    def fixture(self):
        return {'pending_families': ['unreviewed SKU'], 'devices': [{
            'id': 'example', 'vendor': 'teaching', 'spec_scope': 'single_device',
            'memory': {'nominal_capacity': 80, 'bandwidth_bytes_per_second': None,
                       'source_id': 'official', 'locator': 'table 1'},
            'power_watts': 400, 'notes': ['Two official revisions disagree.'],
            'peak_rates': [{'input_precision': 'BF16', 'accumulator_precision': 'FP32',
                            'execution_unit': 'tensor', 'sparsity': 'dense',
                            'operation_kind': 'floating_point', 'source_id': 'official',
                            'locator': 'table 2'}]}]}

    def test_missing_values_and_untraced_numbers_do_not_establish_non_disclosure(self):
        result = audit_catalog(self.fixture())
        fields = result['devices'][0]['fields']
        self.assertEqual([f['recording_status'] for f in fields],
                         ['value_and_source_pointer', 'value_not_recorded', 'value_without_field_source'])
        self.assertTrue(all(f['official_disclosure_status'] == 'not_determined_by_structural_audit' for f in fields))
        self.assertEqual(result['summary']['values_without_field_source'], 1)
        self.assertEqual(result['devices'][0]['source_claim_review'], 'not_performed_by_structural_audit')
        self.assertIn('disagree', result['devices'][0]['notes_requiring_source_review'][0])

    def test_python_api_cannot_select_an_unknown_unit_or_input_format(self):
        for field in ('execution_unit', 'input_precision'):
            device = self.fixture()['devices'][0]
            peak = device['peak_rates'][0]
            peak[field] = 'unspecified'
            with self.subTest(field=field), self.assertRaises(ValueError):
                select_peak(device, peak['input_precision'], peak['accumulator_precision'],
                            peak['execution_unit'], peak['sparsity'])

    def test_integer_and_underspecified_peaks_have_separate_rejection_reasons(self):
        data = self.fixture()
        peaks = data['devices'][0]['peak_rates']
        integer = copy.deepcopy(peaks[0])
        integer.update(input_precision='INT8', accumulator_precision='unspecified', operation_kind='integer')
        peaks.append(integer)
        unknown = copy.deepcopy(peaks[0])
        unknown.update(sparsity='unspecified', execution_unit='unspecified')
        peaks.append(unknown)
        result = audit_catalog(data)
        self.assertEqual(result['summary']['eligible_floating_point_peaks'], 1)
        self.assertEqual(result['devices'][0]['peaks'][1]['exclusion_reasons'],
                         ['unspecified_accumulator_precision', 'not_floating_point'])
        self.assertEqual(result['devices'][0]['peaks'][2]['exclusion_reasons'],
                         ['unspecified_execution_unit', 'unspecified_sparsity'])


if __name__ == '__main__':
    unittest.main()
