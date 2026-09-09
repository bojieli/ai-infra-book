"""Check independent resource identities and deployment rejection boundaries."""
import unittest
import run


class ServingChecks(unittest.TestCase):
    def test_mla_history_growth(self):
        # 24 layers, BF16 latent 512 + extra 64; KDA size must stay constant.
        a,b=run.k3_state(200000),run.k3_state(1000000)
        self.assertEqual(b['resident_bytes']-a['resident_bytes'],24*800000*576*2)
        self.assertEqual(a['recurrent_bytes'],b['recurrent_bytes'])

    def test_one_token_expert_selection(self):
        # One employee cannot select more experts merely because E is large.
        for k,e in [(6,256),(16,896)]:
            union,padded=run.expected_tiles(1,k,e)
            self.assertAlmostEqual(union,k)
            self.assertAlmostEqual(padded,32*k)

    def test_replication_capacity_cliff(self):
        m=run.model('Kimi-K3')
        copied=run.estimate(m,1000000,4,1,'central')
        sharded=run.estimate(m,1000000,4,8,'central')
        self.assertFalse(copied['capacity_feasible'])
        self.assertTrue(sharded['capacity_feasible'])
        self.assertLess(sharded['rank_state_gib'],copied['rank_state_gib'])

    def test_pool_pays_every_workers_rebuild(self):
        x=run.estimate(run.model('Kimi-K3'),1000000,4,8,'central')
        generated_per_cycle=100000
        wall=generated_per_cycle/x['decode_tokens_s']+4*x['rebuild_compute_seconds']
        self.assertAlmostEqual(x['sustained_tokens_s'],generated_per_cycle/wall)
        self.assertAlmostEqual(x['usd_month_per_worker']*4,720*16*6.79)
        self.assertAlmostEqual(x['usd_per_million']*x['monthly_output_million'],x['usd_month_per_worker'])

    def test_executed_time_is_serial_sum(self):
        x=run.estimate(run.model('Kimi-K3'),200000,8,8,'central')
        self.assertAlmostEqual(1000/x['decode_tokens_s'],sum(x['ms'].values()))
        self.assertLess(x['sustained_tokens_s'],x['decode_tokens_s'])


if __name__=='__main__':
    unittest.main()
