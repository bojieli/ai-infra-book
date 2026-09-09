from test_reconfiguration import scenario
from infra_calc.topics.reconfiguration import calculate,amortization,deployment_cost,RUNTIME_TERMS
from fractions import Fraction
from infra_calc.sources import model_config
from infra_calc.topics.reconfiguration import intervals
import unittest

class ReviewEdges(unittest.TestCase):
    def test_moe_tp_ep_physical_replication_closed_form(self):
        c=model_config('qwen3-30b-a3b');H,V,L,Q,K,D,E,F=(c[k] for k in ('hidden_size','vocab_size','num_hidden_layers','num_attention_heads','num_key_value_heads','head_dim','num_experts','moe_intermediate_size'))
        for tp,ep in [(2,4),(8,3),(16,2)]:
            p=intervals(c,dict(tp=tp,ep=ep,devices=[f'g{i}' for i in range(tp*ep)]),2,17,0)
            totals={kind:sum(v['unit_bytes']*(o['stop']-o['start']) for v in p.values() if v['kind']==kind for o in v['owners']) for kind in ('weight','kv')}
            logical_physical=2*ep*V*H+ep*tp*H+L*(ep*H*(2*Q*D+2*max(K,tp)*D)+ep*tp*(2*H+2*D+E*H)+3*E*H*F)
            self.assertEqual(totals['weight'],2*logical_physical)
            self.assertEqual(totals['kv'],ep*2*L*2*17*max(K,tp)*D*2)

    def test_small_auxiliary_snapshot_allows_empty_owners(self):
        s=scenario();s['auxiliary_state_bytes']=1;r=calculate(s)
        self.assertEqual(sum(r['migration_totals']['auxiliary'].values()),1)

    def test_local_materialization_is_not_zero_copy(self):
        s=scenario(ttp=4);r=calculate(s)
        self.assertEqual(r['summary']['network_bytes'],0)
        self.assertGreater(r['summary']['local_materialization_read_write_bytes'],0)
        self.assertIn('local_materialization',r['summary']['missing_runtime_terms'])
        for card in r['placement_cards']:
            self.assertEqual(card['declared_copy_before_release_peak_bytes'],2*card['old_resident_bytes'])

    def test_resource_bound_is_not_an_achievable_transfer_time(self):
        s=scenario();s['runtime_seconds']={k:0 for k in RUNTIME_TERMS};r=calculate(s)
        self.assertIsNone(r['summary']['declared_serial_switch_seconds_exact'])
        bound=Fraction(r['summary']['transfer_lower_bound_exact_seconds'])
        s['network_transfer_seconds']=str(bound/2)
        with self.assertRaises(ValueError):calculate(s)
        s['network_transfer_seconds']=str(bound*2)
        self.assertEqual(Fraction(calculate(s)['summary']['declared_serial_switch_seconds_exact']),bound*2)

    def test_horizon_and_invalid_dimension_or_currency(self):
        s=scenario();s['amortization']=dict(extra_seconds=10,seconds_saved_per_step=2,remaining_steps=5)
        self.assertFalse(calculate(s)['amortization']['time']['strictly_better_within_horizon'])
        s['amortization']['remaining_steps']=6
        self.assertTrue(calculate(s)['amortization']['time']['strictly_better_within_horizon'])
        self.assertEqual(amortization(0,-1)['break_even_steps'],0)
        s['target']['pp']=True
        with self.assertRaises(ValueError):calculate(s)
        with self.assertRaises(ValueError):deployment_cost({'terms':{}})

if __name__=='__main__':unittest.main()
