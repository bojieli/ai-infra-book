"""C52 public entry points and reproducible scenario/report contract."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.paths import PROJECT
from infra_calc.report import markdown
from infra_calc.topics.reconfiguration import calculate


class ReconfigurationIntegration(unittest.TestCase):
    def test_book_scenarios_replay_and_specialized_report(self):
        rows = json.loads((PROJECT / 'scenarios/book.json').read_text())['reconfiguration']
        self.assertEqual(len(rows), 9)
        for row in rows:
            with self.subTest(row=row['id']):
                result = calculate(row['inputs'])
                self.assertEqual(result, calculate(result['scenario']))
                report = markdown(result)
                self.assertIn('资源下界不是实际运行时间', report)
                self.assertIn('declared_serial_switch_seconds_exact', report)
                self.assertIn('local_materialization_read_write_bytes', report)
                self.assertIn('保留旧缓冲时峰值', report)
                if row['id'].endswith('declared-serial'):
                    self.assertEqual(result['summary']['declared_serial_switch_seconds_exact'], '109')
                    self.assertFalse(result['amortization']['time']['strictly_better_within_horizon'])
                if row['id'].endswith('same-card-materialization'):
                    self.assertEqual(result['summary']['network_bytes'], 0)
                    self.assertTrue(result['amortization']['time']['strictly_better_within_horizon'])

    def test_default_cli_json_and_markdown(self):
        command = [sys.executable, str(PROJECT / 'calc.py'), 'reconfiguration']
        result = json.loads(subprocess.check_output(command, text=True))
        expected = calculate(json.loads((PROJECT / 'scenarios/reconfiguration-example.json').read_text()))
        self.assertEqual(result, expected)
        report = subprocess.check_output(command + ['--format', 'md'], text=True)
        self.assertEqual(report.rstrip(), markdown(expected).rstrip())
