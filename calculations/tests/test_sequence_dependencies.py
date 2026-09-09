import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.sequence_dependencies import (calculate, transformer_full, transformer_step,
    rnn_step, embedding, weights, dependency_graph)


class SequenceDependencyTests(unittest.TestCase):
    def test_fixed_same_model_outputs_and_causality(self):
        result=calculate()
        self.assertEqual(len(result['sequence_checks']),10)
        self.assertTrue(all(r['passed'] for r in result['sequence_checks']))
        self.assertEqual(result['summary']['max_absolute_error'],0)
        params=weights()
        a=transformer_full([0,1,2,3],params)
        b=transformer_full([0,1,4,4],params)
        self.assertEqual(a[:2],b[:2])
        # Different teaching models are not being treated as interchangeable.
        rows=result['sequence_checks']
        self.assertNotEqual(rows[0]['recomputed_output'],rows[1]['recomputed_output'])

    def test_uniform_attention_and_rnn_against_independent_scalar_recurrence(self):
        identity=[[float(i==j) for j in range(4)] for i in range(4)]
        zeros=[[0.]*4 for _ in range(4)]
        params=[dict(q=zeros,k=zeros,v=identity,o=identity,
                     up=[[0.]*8 for _ in range(4)],down=[[0.]*4 for _ in range(8)]) for _ in range(3)]
        # Q=K=0 gives uniform causal attention; FF=0 leaves x + causal mean(x).
        expected=[embedding(t,t) for t in range(4)]
        for _ in range(3):
            expected=[[x[j]+sum(row[j] for row in expected[:i+1])/(i+1) for j in range(4)] for i,x in enumerate(expected)]
        actual=transformer_full([0,1,2,3],params)
        cache=[([],[]) for _ in range(3)]
        for t in range(4):
            streamed,cache=transformer_step(embedding(t,t),cache,params)
            for got,reference in zip(actual[t],expected[t]): self.assertAlmostEqual(got,reference,places=12)
            self.assertEqual(actual[t],streamed)
        rp=[dict(wx=identity,wh=[[.5*float(i==j) for j in range(4)] for i in range(4)]) for _ in range(3)]
        state=[[0.]*4 for _ in range(3)]; ref=[[0.]*4 for _ in range(3)]
        for t in range(4):
            x=embedding(t,t)
            for l in range(3):
                x=[math.tanh(x[j]+.5*ref[l][j]) for j in range(4)]
                ref[l]=x
            got,state=rnn_step(embedding(t,t),state,rp)
            self.assertEqual(got,x)

    def test_work_state_and_dependency_counts(self):
        result=calculate(); work={(r['model'],r['mode']):r['matrix_flops'] for r in result['sequence_work']}
        # Independent closed form: 2 RNN D*D projections; Transformer 4 D*D,
        # D*F and F*D per position, plus QK and AV for each causal pair.
        self.assertEqual(work['rnn','known_four_tokens'],3*4*2*(2*4*4))
        self.assertEqual(work['transformer','known_four_tokens'],3*(4*(4*2*4*4+2*2*4*8)+sum(range(1,5))*4*4))
        self.assertEqual(work['transformer','fifth_token_state_reused'],3*(4*2*4*4+2*2*4*8+5*4*4))
        states={(r['model'],r['after_tokens']):r for r in result['sequence_states']}
        self.assertEqual(states['rnn',4]['persistent_history_bytes'],96)
        self.assertEqual(states['transformer',4]['persistent_history_bytes'],768)
        self.assertEqual(states['transformer',5]['persistent_history_bytes'],960)
        rnn=dependency_graph('rnn'); tf=dependency_graph('transformer')
        self.assertEqual((len(rnn['edges']),rnn['unit_node_critical_path']),(17,6))
        self.assertEqual((len(tf['edges']),tf['unit_node_critical_path']),(20,3))
        cache=result['sequence_transformer_cache_graph']
        self.assertEqual(sum(e['kind']=='read_retained_kv' for e in cache['edges']),3*(0+1+2+3))
        self.assertEqual(sum(n['kind']=='new_kv_projection' for n in cache['nodes']),12)


if __name__=='__main__': unittest.main()
