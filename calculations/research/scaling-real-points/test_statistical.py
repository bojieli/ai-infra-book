import copy
import unittest
from adapt_statistical import records,calculate,run_fit,GRID

class StatisticalTests(unittest.TestCase):
    def test_original_points_and_fixed_holdout(self):
        rows=records()
        self.assertEqual((len(rows),sum(r['split']=='fit' for r in rows)),(8,6))
        self.assertNotIn('146m14b14b',{r['id'] for r in rows})
        for r in rows:self.assertEqual(r['split']=='holdout',r['N']>=2e9)
        self.assertEqual({r['evaluation']['tokens'] for r in rows},{13107200,52428800,104857600})

    def test_holdout_cannot_select_fit(self):
        rows=records();before=run_fit(rows,GRID)['result']['law']
        for r in rows:
            if r['split']=='holdout':r['loss']*=100
        self.assertEqual(before,run_fit(rows,GRID)['result']['law'])

    def test_real_data_replay_and_coordinate_sensitivity(self):
        x=calculate()
        self.assertEqual(x['primary']['status'],'fit')
        self.assertAlmostEqual(x['primary']['result']['holdout_rmse'],0.019344538649002298)
        self.assertEqual(x['primary']['result']['law'],x['boundary_diagnostic']['law'])
        self.assertFalse(x['sampling_variance_known'])
        self.assertGreater(x['sensitivity']['declared_D']['result']['holdout_rmse'],0)
        for r in x['records']:
            if r['id']=='1b1100m100m':self.assertEqual(r['D_declared_budget'],99999744)

if __name__=='__main__':unittest.main()
