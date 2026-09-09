import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
"""V3 independent parameter enumeration, causal sums and routing semantics."""
import math
import unittest

from infra_calc.sources import model_config
from infra_calc.topics.v3_forward import calculate, grouped_route, weights


class V3ForwardTests(unittest.TestCase):
    def test_all_base_parameters_from_explicit_layer_inventory(self):
        # Independent class-level expansion into every layer/expert tensor.
        shapes = [(129280,7168), (129280,7168), (7168,)]
        for layer in range(61):
            shapes += [(1536,7168),(1536,),(24576,1536),(576,7168),(512,),
                       (32768,512),(7168,16384),(7168,),(7168,)]
            if layer < 3:
                shapes += [(18432,7168),(18432,7168),(7168,18432)]
            else:
                shapes += [(256,7168),(256,)]
                for _ in range(257):  # 256 routed plus shared
                    shapes += [(2048,7168),(2048,7168),(7168,2048)]
        official = weights(model_config('deepseek-v3'))
        self.assertEqual(sum(math.prod(x) for x in shapes), 671026419200)
        self.assertEqual(sum(x.parameters for x in official), sum(math.prod(x) for x in shapes))
        self.assertEqual(sum(x.copies for x in official), len(shapes))
        self.assertEqual(len(shapes),45395)

    def test_prefill_decode_causal_work_and_reference_cache(self):
        for batch,tokens,history in [(1,5,0),(2,1,8),(2,3,4)]:
            valid=calculate(batch,tokens,history)
            eager=calculate(batch,tokens,history,attention_work='eager')
            pairs=sum(history+position+1 for _ in range(batch) for position in range(tokens))
            attention=61*128*pairs*2*(192+128)
            self.assertEqual(valid['summary']['valid_attention_matrix_flops'],attention)
            rectangle=batch*tokens*(history+tokens)
            extra=61*128*(rectangle-pairs)*2*320
            self.assertEqual(eager['summary']['matrix_flops']-valid['summary']['matrix_flops'],extra)
            unit=61*128*320*2
            self.assertEqual(valid['summary']['kv_resident_after_bytes'],batch*(history+tokens)*unit)
            self.assertEqual(valid['summary']['kv_resident_after_bytes'],
                             valid['summary']['history_unique_payload_bytes']+valid['summary']['kv_new_write_bytes'])
            ops={x['name']:x for x in valid['operators']}
            self.assertEqual(ops['rotary_q_and_shared_k']['scalar_flops'],3*batch*tokens*129*64)
            self.assertEqual(ops['lm_head']['matrix_flops'],2*batch*tokens*7168*129280)
        all_head=calculate(tokens=5)
        last=calculate(tokens=5,output_head='last')
        self.assertEqual(all_head['summary']['matrix_flops']-last['summary']['matrix_flops'],
                         2*4*7168*129280)

    def test_group_selection_uses_corrected_scores_but_original_weights(self):
        c=model_config('deepseek-v3')
        logits=[(i-128)/80 for i in range(256)]
        bias=[100+i/100 if i<8 else 0 for i in range(256)]
        ids,values=grouped_route(logits,bias,c)
        self.assertEqual(set(ids),set(range(8)))
        raw=[1/(1+math.exp(-logits[i])) for i in ids]
        for actual,score in zip(values,raw):
            self.assertAlmostEqual(actual,score/sum(raw)*2.5)
        self.assertAlmostEqual(sum(values),2.5)
        ids,_=grouped_route(logits,[0]*256,c)
        self.assertEqual(set(ids),set(range(248,256)))
        self.assertLessEqual(len({i//32 for i in ids}),4)
        with self.assertRaises(ValueError):
            grouped_route([math.nan]*256,[0]*256,c)

    def test_routing_work_conservation_and_rejected_scope(self):
        balanced=calculate(tokens=32)
        concentrated=calculate(tokens=32,routing='concentrated')
        self.assertEqual(balanced['summary']['matrix_flops'],concentrated['summary']['matrix_flops'])
        self.assertEqual(balanced['summary']['logical_base_parameters'],concentrated['summary']['logical_base_parameters'])
        self.assertEqual(balanced['summary']['expert_union_per_layer'],256)
        self.assertEqual(concentrated['summary']['expert_union_per_layer'],8)
        self.assertGreater(balanced['summary']['weight_read_bytes'],concentrated['summary']['weight_read_bytes'])
        for kwargs in [dict(tokens=0),dict(history=-1),dict(tokens=163841),dict(attention_work='compact'),
                       dict(counts=[0]*256),dict(output_head='bad')]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)
        self.assertFalse(balanced['coverage']['checkpoint_header_validation'])
        self.assertIsNone(balanced['summary']['complete_hbm_bytes'])


class V3CsvAccountingTests(unittest.TestCase):
    def test_mixed_layer_csv_preserves_repeat_counts(self):
        import csv
        import io
        from infra_calc.topics.v3_forward import calculate
        from infra_calc.report import operator_csv
        result = calculate(tokens=1, history=8)
        rows = list(csv.DictReader(io.StringIO(operator_csv(result))))
        for field in ('matrix_flops', 'scalar_flops', 'weight_read_bytes', 'activation_read_bytes', 'activation_write_bytes'):
            self.assertEqual(sum(int(row[field])*int(row['repeats']) for row in rows), result['summary'][field])
