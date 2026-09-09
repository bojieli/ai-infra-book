import unittest
from fractions import Fraction
from calculate import calculate

class LifecycleTests(unittest.TestCase):
    def test_prefix_bytes_and_conservation(self):
        r=calculate()
        self.assertEqual(r['kv_bytes_per_token'],36*2*8*128*2)
        self.assertEqual([x['longest_common_token_prefix'] for x in r['transitions']],[112,164,213])
        total=Fraction(0)
        for x in r['transitions']:
            size=x['reported_cached_tokens']*36*2*8*128*2
            self.assertEqual(x['conditional_bf16_prefix_payload_bytes'],size)
            total+=size*Fraction(x['recorded_application_gap_seconds_exact'])
            self.assertIsNone(x['observed_page_lifetime'])
            self.assertIsNone(x['actual_restore_seconds'])
        self.assertEqual(Fraction(r['conditional_prefix_gap_byte_seconds_exact']),total)

    def test_bandwidth_changes_only_counterfactual(self):
        a,b=calculate(),calculate(host_bytes_per_second=50_000_000_000)
        for x,y in zip(a['transitions'],b['transitions']):
            self.assertEqual(Fraction(x['counterfactual_host_restore_seconds_exact']),2*Fraction(y['counterfactual_host_restore_seconds_exact']))
            for key in ('cold_prefill_totals','warm_prefill_totals','reported_cached_tokens','conditional_retain_through_gap_byte_seconds_exact'):
                self.assertEqual(x[key],y[key])

    def test_invalid_and_replay(self):
        r=calculate()
        self.assertEqual(r,calculate(**r['scenario']))
        for inputs in ({'lookup_ns':-1},{'lookup_ns':True},{'host_bytes_per_second':0},{'remote_bytes_per_second':1.5}):
            with self.assertRaises(ValueError):
                calculate(**inputs)

if __name__=='__main__':
    unittest.main()
