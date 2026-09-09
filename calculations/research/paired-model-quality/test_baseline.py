import unittest
from baseline import calculate

class BaselineTests(unittest.TestCase):
    def test_trials_and_score(self):
        r=calculate()
        self.assertEqual((r['distinct_tasks'],r['natural_executions'],r['correct_executions']),(8,32,28))
        self.assertEqual(len({x['request_id'] for x in r['calls']}),32)
        self.assertEqual([x['task_id'] for x in r['per_task'] if x['correct']==0],['n512-r0'])
        self.assertTrue(all(x['trials']==4 for x in r['per_task']))
        self.assertIsNone(r['paired_second_model'])
        self.assertIsNone(r['quality_equivalence'])
        self.assertIsNone(r['economic_winner'])

    def test_declared_state_boundary(self):
        for x in calculate()['calls']:
            self.assertEqual(x['declared_final_kv_bytes'],(x['input_tokens']+x['returned_ids']-1)*36*2*8*128*2)
            self.assertGreater(x['declared_cold_serial_matrix_flops'],0)
            self.assertIsNone(x['observed_model_calls'])

if __name__=='__main__':unittest.main()
