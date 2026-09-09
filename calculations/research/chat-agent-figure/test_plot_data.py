import unittest
from plot import calculate

class FigureDataTests(unittest.TestCase):
    def test_lengths_and_state(self):
        d=calculate()
        self.assertEqual(sum(r['input_tokens'] for r in d['chat']),753)
        self.assertEqual(sum(r['cached_tokens'] for r in d['chat']),489)
        self.assertEqual(sum(r['output_tokens'] for r in d['agent']),2733)
        for r in d['agent']:
            self.assertEqual(r['hypothetical_retained_kv_bytes'],(r['input_tokens']+r['output_tokens']-1)*36*2*8*128*2)
            self.assertLessEqual(r['model_end'],r['tool_start'])
            self.assertLessEqual(r['tool_start'],r['tool_end'])

    def test_missing_reasoning_boundary(self):
        rows=calculate()['agent']
        self.assertIsNone(rows[0]['reasoning_boundary_count'])
        self.assertIsNone(rows[0]['reasoning_boundary_observed_seconds'])
        self.assertEqual(rows[0]['finish_reason'],'length')
        for r in rows[1:]:
            self.assertLessEqual(r['reasoning_boundary_count'],r['output_tokens'])
            self.assertLessEqual(r['model_start'],r['reasoning_boundary_observed_seconds'])
            self.assertLessEqual(r['reasoning_boundary_observed_seconds'],r['model_end'])

if __name__=='__main__':unittest.main()
