import csv
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import qwen36_forward, qwen36_capacity, qwen35_forward
from infra_calc import report


class Qwen36Tests(unittest.TestCase):
    def test_independent_parameter_inventory(self):
        # Published dimensions, independently grouped by mathematical parameter role.
        global_parameters = 2 * 248320 * 2048 + 2048
        common = 40 * (2 * 2048 + 256 * 2048 + 3 * 256 * 2048 * 512
                       + 3 * 2048 * 512 + 2048)
        attention = 10 * (2048 * (3 * 16 * 256 + 2 * 2 * 256) + 2 * 256)
        recurrent = 30 * (2048 * (2 * 16 * 128 + 3 * 32 * 128 + 2 * 32)
                          + (2 * 16 * 128 + 32 * 128) * 4 + 2 * 32 + 128)
        result = qwen36_forward.calculate(tokens=1, history=1)
        self.assertEqual(global_parameters + common + attention + recurrent, 34660610688)
        self.assertEqual(result['summary']['base_text_parameters'], 34660610688)
        self.assertEqual(result['summary']['base_checkpoint_bytes'], 69321221376)
        self.assertEqual(len(result['weights']), 693)
        self.assertEqual({w['storage_dtype'] for w in result['weights']}, {'BF16'})

    def test_expert_work_vs_distinct_weight_reads(self):
        balanced = qwen36_forward.calculate(batch=64, tokens=1, history=8192)
        concentrated = qwen36_forward.calculate(batch=64, tokens=1, history=8192,
                                                routing_counts=[64]*8 + [0]*248)
        expected_work = 40 * 64 * 8 * 6 * 2048 * 512
        for result, distinct in ((balanced, 256), (concentrated, 8)):
            expert_ops = [o for o in result['operators'] if o['name'].startswith('moe.expert')]
            self.assertEqual(sum(o['matrix_flops']*o['repeats'] for o in expert_ops), expected_work)
            self.assertEqual(sum(o['weight_read_bytes']*o['repeats'] for o in expert_ops),
                             40 * distinct * 3 * 2048 * 512 * 2)
        self.assertEqual(balanced['summary']['matrix_flops'], concentrated['summary']['matrix_flops'])
        self.assertEqual(balanced['summary']['base_checkpoint_bytes'], concentrated['summary']['base_checkpoint_bytes'])

    def test_hybrid_state_and_projection_shapes(self):
        result = qwen36_forward.calculate(batch=3, tokens=1, history=8192)
        state = result['state']
        self.assertEqual(state['full_kv_before_bytes'], 3 * 8192 * 20480)
        self.assertEqual(state['full_kv_append_bytes'], 3 * 20480)
        self.assertEqual(state['linear_recurrent_fp32_bytes'], 3 * 62914560)
        self.assertEqual(state['linear_conv_slot_bytes'], 3 * 1966080)
        byname = {o['name']: o for o in result['operators']}
        self.assertEqual(byname['full.q_and_gate']['matrix_flops'], 2*3*2048*8192)
        self.assertEqual(byname['linear.qkv']['matrix_flops'], 2*3*2048*8192)
        self.assertEqual(byname['full.QK']['repeats'], 10)
        self.assertEqual(byname['linear.qkv']['repeats'], 30)

    def test_tail_padding_head_and_csv_conservation(self):
        result = qwen36_forward.calculate(tokens=65)
        self.assertEqual(result['execution']['linear_path']['padded_tokens'], 128)
        last = qwen36_forward.calculate(tokens=65, output_head='last')
        self.assertEqual(result['summary']['matrix_flops']-last['summary']['matrix_flops'],
                         64 * 2 * 2048 * 248320)
        rows = list(csv.DictReader(io.StringIO(report.operator_csv(result))))
        self.assertEqual(sum(int(r['matrix_flops'])*int(r['repeats']) for r in rows),
                         result['summary']['matrix_flops'])
        self.assertEqual(qwen36_forward.calculate(**result['scenario']), result)

    def test_capacity_exact_boundary_and_auxiliary(self):
        base = qwen36_capacity.calculate()
        self.assertEqual(base['summary']['necessary_budget_bytes'], 71701357824)
        complete = qwen36_capacity.calculate(include_auxiliary_weights=True)
        self.assertEqual(complete['summary']['entire_checkpoint_bytes'], 71903645408)
        self.assertEqual(complete['summary']['necessary_budget_bytes']-base['summary']['necessary_budget_bytes'], 2582424032)
        without_reserve = qwen36_capacity.calculate(reserve_bytes=0)['summary']['necessary_budget_bytes']
        for delta in (0, 1):
            result = qwen36_capacity.calculate(reserve_bytes=80000000000-without_reserve+delta)
            h100 = next(d for d in result['devices'] if d['device']=='h100-sxm')
            self.assertEqual(h100['necessary_budget_fits'], delta==0)
            self.assertIsNone(h100['runtime_feasibility'])

    def test_reject_invalid_and_dtype_correction(self):
        for kwargs in ({'routing_counts':[1]*256}, {'tokens':0}, {'record_past':1}, {'chunk_size':32}):
            with self.assertRaises(ValueError): qwen36_forward.calculate(**kwargs)
        with self.assertRaises(ValueError): qwen36_capacity.calculate(include_auxiliary_weights=1)
        old = qwen35_forward.calculate(tokens=1, history=1)
        decay = next(o for o in old['operators'] if o['name']=='linear.decay_and_beta')
        self.assertEqual(decay['weight_read_bytes'], 64*(4+2))
        new = qwen36_forward.calculate(tokens=1, history=1)
        decay = next(o for o in new['operators'] if o['name']=='linear.decay_and_beta')
        self.assertEqual(decay['weight_read_bytes'], 32*(2+2))


if __name__ == '__main__':
    unittest.main()
