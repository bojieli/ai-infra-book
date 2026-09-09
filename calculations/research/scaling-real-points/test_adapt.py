import unittest
from unittest.mock import patch
import adapt

class RealRecords(unittest.TestCase):
    def test_original_records_and_fixed_split(self):
        r=adapt.calculate()
        self.assertEqual(len(r['records']),33)
        self.assertEqual(len({x['record_id'] for x in r['records']}),33)
        for x in r['records']:
            self.assertEqual(x['split'],'holdout' if x['N']>=2e9 else 'fit')
            self.assertGreater(x['loss'],0)
            self.assertEqual(x['D'],x['U'])
    def test_no_fit_without_complete_control_evidence(self):
        with patch.object(adapt.scaling_law,'fit',side_effect=AssertionError('Unverified points reached fitter')):
            r=adapt.calculate()
        self.assertEqual(r['fit']['status'],'no_verified_fit_group')
        self.assertEqual(r['fit']['synthetic_rows_added'],0)
    def test_explicit_log_conflict_and_budget(self):
        r=adapt.calculate();by={x['record_id']:x for x in r['records']}
        self.assertEqual(by['14m100m100m']['evaluation']['tokens'],13107200)
        self.assertEqual(by['1b112b12b']['evaluation']['tokens'],52428800)
        self.assertEqual(by['2b855b55b']['evaluation']['tokens'],104857600)
        self.assertEqual(by['146m14b14b']['training_budget']['declared_target_tokens'],5517578*2048)
        self.assertNotEqual(by['146m14b14b']['training_budget']['declared_target_tokens'],by['146m14b14b']['D'])

if __name__=='__main__':unittest.main()
