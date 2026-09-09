import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.vl_request import calculate
from infra_calc.vl_plot import chart_data


class VlPlotTests(unittest.TestCase):
    def test_same_request_stage_work_and_invalid_comparison(self):
        cold, warm = calculate(), calculate(encoder_cache_hits=4)
        data = chart_data(cold, warm)
        self.assertEqual(data['rows'][0]['total_matrix_flops']-data['rows'][1]['total_matrix_flops'], cold['summary']['vision_matrix_flops'])
        self.assertEqual(data['prompt_positions'], 2000)
        bad = copy.deepcopy(warm)
        bad['scenario']['output_tokens'] = 1
        with self.assertRaises(ValueError): chart_data(cold,bad)
        bad = copy.deepcopy(warm)
        bad['vl_request_stages'][1]['matrix_flops'] += 1
        with self.assertRaises(ValueError): chart_data(cold,bad)
