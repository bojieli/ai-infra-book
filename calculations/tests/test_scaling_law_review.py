"""Numeric range and admissibility regressions for the public C19 APIs."""
import json
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics import scaling_law as m
from infra_calc.paths import PROJECT
LAW=dict(E=1.,A=1.,B=1.,alpha=.5,beta=.5,N0=1.,D0=1.)
DEMAND=dict(calls_per_day=1,lifetime_days=1,input_tokens=2,output_tokens=3)
COSTS=dict(train_per_flop=.25,prefill_per_flop=.125,decode_per_flop=.5,setup_cost=7.,prefill_flops_per_parameter_token=2.,decode_flops_per_parameter_token=4.)
def scenario():
    return json.loads((PROJECT/'scenarios/scaling-law-teaching.json').read_text())
def do_fit(s,grid=None):
    return m.fit(s['records'],s['exponent_grid'] if grid is None else grid,s['N0'],s['D0'])

class KnownBugRegressions(unittest.TestCase):
    def test_B1_zero_floor_exact_fit_must_be_admissible(self):
        s=scenario()
        for row in s['records']:
            row['loss']=(row['N']/s['N0'])**-.5+(row['D']/s['D0'])**-.5
        r=do_fit(s,[[.5,.5]])
        self.assertGreaterEqual(r['law']['E'],0)
        self.assertLess(r['fit_sse'],1e-24)

    def test_B2_bad_grid_member_must_not_discard_good_fit(self):
        s=scenario(); expected=do_fit(s,[[.5,.5]])
        r=do_fit(s,[[.5,.5],[1e-15,.5]])
        self.assertEqual(r['law'],expected['law'])

    def test_B3_representable_optimum_despite_normalizer_overflow(self):
        r=m.compute_optimum(dict(LAW,N0=1e200,D0=1e200),6e200)
        self.assertAlmostEqual(r['N']/1e100,1,places=11)
        self.assertAlmostEqual(r['D']/1e100,1,places=11)

    def test_B3_representable_loss_despite_ratio_underflow(self):
        result=m.loss(dict(LAW,N0=1e200),1e-200,1)
        self.assertAlmostEqual(result/1e200,1,places=11)

    def test_B3_ratio_overflow_must_not_silently_erase_loss_term(self):
        result=m.loss(dict(LAW,E=0,N0=1e-200,B=1e-300),1e200,1)
        self.assertAlmostEqual(result/1e-200,1,places=11)

    def test_B4_loss_overflow_must_raise_value_error(self):
        with self.assertRaises(ValueError):
            m.loss(dict(LAW,E=1e308,A=1e308,B=1e308),1,1)

    def test_B4_lifecycle_overflow_must_not_select_infinite_cost(self):
        with self.assertRaises(ValueError):
            m.lifecycle(dict(LAW,alpha=1,beta=1),[3,4],1.5,DEMAND,
                        dict(COSTS,train_per_flop=1e308))


    def test_rejected_candidate_reason_and_invalid_input(self):
        s=scenario();r=do_fit(s,[[.5,.5],[1e-15,.5]])
        self.assertEqual(len(r['rejected_candidates']),1)
        self.assertIn('ill-conditioned',r['rejected_candidates'][0]['reason'])
        with self.assertRaises(ValueError): do_fit(s,[[.5,.5],[float('nan'),.5]])
        with self.assertRaises(ValueError): do_fit(s,[[1e-15,.5]])

    def test_material_negative_floor_is_not_clamped(self):
        s=scenario()
        for row in s['records']:
            row['loss']=-.01+(row['N']/s['N0'])**-.5+(row['D']/s['D0'])**-.5
        with self.assertRaises(ValueError): do_fit(s,[[.5,.5]])

    def test_coefficient_compensates_intermediate_power_overflow(self):
        actual=m.loss(dict(LAW,E=0,A=1e-200,N0=1e200,alpha=1,B=1e-300),1e-200,1)
        self.assertAlmostEqual(actual/1e200,1,places=11)
