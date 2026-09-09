"""Book constants, threshold inequalities and finite two-resource simulation."""
from pathlib import Path
from fractions import Fraction
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.graph_execution import calculate, amortization


class GraphExecutionTests(unittest.TestCase):
    def test_shapes_and_path_selection(self):
        small=calculate();large=calculate(input_tokens=2048)
        self.assertEqual(small['summary']['extra_copy_interface_bytes'],4*2**20)
        self.assertEqual(large['summary']['extra_copy_interface_bytes'],32*2**20)
        self.assertEqual(small['summary']['layer_ffn_matrix_parameters'],150994944)
        self.assertEqual(small['summary']['padding_ffn_matrix_flops'],154618822656)
        self.assertEqual(small['summary']['padding_over_real_fraction'],'1/3')
        self.assertEqual(small['summary']['minimum_serial_steady_external_input_path'],'copy')
        self.assertEqual(large['summary']['minimum_serial_steady_external_input_path'],'indirect')
        self.assertEqual(large['summary']['minimum_lifetime_external_input_path'],'eager')
        self.assertEqual(calculate(input_tokens=2048,calls=1000000)['summary']['minimum_lifetime_external_input_path'],'indirect')
        paths={r['path']:r for r in large['graph_paths']}
        self.assertEqual(paths['indirect']['strictly_faster_calls'],111112)
        self.assertIsNone(paths['copy']['strictly_faster_calls'])
        self.assertEqual(calculate(real_tokens=2048)['summary']['padding_ffn_matrix_flops'],0)

    def test_exact_amortization_boundaries(self):
        for setup in (1,6,1000000000):
            for saving in (Fraction(2),Fraction(3,7),Fraction(9000)):
                r=amortization(setup,saving)
                n=r['break_even_calls'];strict=r['strictly_faster_calls']
                self.assertGreaterEqual(n*saving,setup)
                self.assertLess((n-1)*saving,setup)
                self.assertGreater(strict*saving,setup)
                self.assertLessEqual((strict-1)*saving,setup)
        self.assertEqual(amortization(6,Fraction(2)),dict(break_even_calls=3,strictly_faster_calls=4))
        self.assertIsNone(amortization(1,Fraction(0))['break_even_calls'])
        self.assertIsNone(amortization(1,Fraction(-1))['strictly_faster_calls'])

    def test_pipeline_by_dependency_replay(self):
        for segments in (1,3,100):
            result=calculate(segments=segments)
            for row in result['configuration_pipeline']:
                host_end=gpu_end=Fraction(0)
                for _ in range(segments):
                    host_end+=Fraction(row['config_ns'])
                    gpu_end=max(host_end,gpu_end)+Fraction(row['device_ns'])
                self.assertEqual(Fraction(row['overlapped_total_exact_ns']),gpu_end)
        rows=calculate()['configuration_pipeline']
        self.assertEqual([r['overlapped_total_ns'] for r in rows],[2020000,2005000,505000])
        with self.assertRaises(ValueError):calculate(real_tokens=2049)
