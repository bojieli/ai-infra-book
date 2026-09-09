import unittest
import compare
import run


class CompareChecks(unittest.TestCase):
    def test_calendar_peak_is_not_all_month(self):
        self.assertEqual(compare.PEAK_HOURS,22*7)
        self.assertAlmostEqual(compare.PRICES['DeepSeek-V4-Flash']['output'],(.66*566+1.32*154)/720)

    def test_complete_prompt_billing(self):
        x=compare.billing('Kimi-K3',200000)
        self.assertEqual(x['hit_tokens_per_turn']+x['miss_tokens_per_turn'],200000)
        expected=15+(x['hit_tokens_per_turn']*.3+x['miss_tokens_per_turn']*3)/4096
        self.assertAlmostEqual(x['api_usd_per_million_output'],expected)
        self.assertGreater(x['miss_tokens_per_turn'],4096+1024)

    def test_cache_all_miss_and_no_rebuild_endpoints(self):
        x=compare.billing('Kimi-K3',1000000,hit_fraction=0)
        self.assertEqual(x['hit_tokens_per_turn'],0)
        self.assertAlmostEqual(x['api_usd_per_million_output'],15+1000000/4096*3)
        y=compare.billing('Kimi-K3',1000000,rebuild=False)
        self.assertEqual(y['miss_tokens_per_turn'],5120)

    def test_price_scales_bill_not_speed(self):
        m=run.model('DeepSeek-V4-Flash');h=compare.GPUS['H200-SXM']
        a=run.estimate(m,200000,8,1,'central',hardware=h)
        b=run.estimate(m,200000,8,1,'central',hardware=dict(h,gpu_usd_hour=h['gpu_usd_hour']*2))
        self.assertEqual(a['decode_tokens_s'],b['decode_tokens_s'])
        self.assertEqual(a['usd_month_per_worker']*2,b['usd_month_per_worker'])

    def test_fp8_does_not_halve_kda(self):
        m=run.model('Kimi-K3');h=compare.GPUS['B200']
        a=run.estimate(m,200000,4,8,'central',hardware=h,kv_bytes=2)
        b=run.estimate(m,200000,4,8,'central',hardware=h,kv_bytes=1)
        self.assertGreater(b['rank_state_gib'],a['rank_state_gib']/2)
        self.assertLess(b['rank_state_gib'],a['rank_state_gib'])

    def test_same_output_and_price_crossing(self):
        m=run.model('DeepSeek-V4-Flash');h=compare.GPUS['B200']
        a=run.estimate(m,200000,8,1,'central',hardware=h)
        x=compare.workflow_adjust(a,m,h)
        self.assertAlmostEqual(x['api_same_output_usd_month'],x['workflow_monthly_output_million']*x['api_usd_per_million_output'])
        at_cross=dict(h,gpu_usd_hour=x['gpu_price_break_even_usd_hour'])
        y=compare.workflow_adjust(run.estimate(m,200000,8,1,'central',hardware=at_cross),m,at_cross)
        self.assertAlmostEqual(y['usd_month_per_worker'],y['api_same_output_usd_month'])
        self.assertLess(x['workflow_tokens_s'],x['decode_tokens_s'])


if __name__=='__main__':unittest.main()
