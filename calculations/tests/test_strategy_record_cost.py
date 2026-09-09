import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infra_calc.topics.strategy_record_cost import calculate, selected_index, strict_value


class StrategyRecordCostTests(unittest.TestCase):
    def test_strict_protocol_and_tie(self):
        self.assertEqual(strict_value('<think>x</think>{"count":3}', True), 3)
        for text in ['{"count":true}', 'answer: {"count":3}', '```json\n{"count":3}\n```', '{"count":3,"extra":0}']:
            self.assertIsNone(strict_value(text, False))
        self.assertIsNone(strict_value('{"count":3}', True))
        self.assertEqual(selected_index([None, 4, 3, 3, 4]), 1)
        self.assertEqual(selected_index([4, 3, 3]), 1)
        self.assertIsNone(selected_index([None, None]))

    def test_all_failures_and_intervals_preserved(self):
        result = calculate()
        strategies = [s for b in result['batches'] for s in b['strategies']]
        self.assertEqual(sum(s['attempts'] for s in strategies), 132)
        self.assertEqual(sum(s['groups'] for s in strategies), 72)
        self.assertEqual(sum(s['truncated_attempts'] for s in strategies), 88)
        for strategy in strategies:
            self.assertEqual(strategy['successes'], 0)
            self.assertEqual(strategy['failed_group_output_ids'], strategy['returned_output_ids'])
            self.assertIsNone(strategy['output_ids_per_success'])
            self.assertIsNone(strategy['gpu_seconds'])
        for batch in result['batches']:
            parallel = next(s for s in batch['strategies'] if s['strategy'] == 'parallel')
            self.assertGreater(parallel['client_request_seconds_sum'], parallel['group_wall_seconds_sum'])


if __name__ == '__main__':
    unittest.main()
