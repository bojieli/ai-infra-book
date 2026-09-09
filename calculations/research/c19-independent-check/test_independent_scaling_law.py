"""Independent read-only audit. Standard library only; known bugs are expected failures.
Run: PYTHONDONTWRITEBYTECODE=1 python3 test_independent_scaling_law.py -v
Add --strict to make the seven known-bug regression expectations fail normally.
Override source location with AI_INFRA_BOOK (no source writes are performed).
"""
import sys
sys.dont_write_bytecode = True
import os
import copy
import json
import math
import random
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(os.environ.get('AI_INFRA_BOOK', '/Users/boj/book/ai-infra-book'))
PROJECT = ROOT / 'calculations'
sys.path.insert(0, str(PROJECT / 'src'))
from infra_calc.topics import scaling_law as m

LAW = dict(E=1., A=1., B=1., alpha=.5, beta=.5, N0=1., D0=1.)
DEMAND = dict(calls_per_day=1, lifetime_days=1, input_tokens=2, output_tokens=3)
COSTS = dict(train_per_flop=.25, prefill_per_flop=.125, decode_per_flop=.5,
             setup_cost=7., prefill_flops_per_parameter_token=2.,
             decode_flops_per_parameter_token=4.)

def scenario(name='teaching'):
    return json.loads((PROJECT / f'scenarios/scaling-law-{name}.json').read_text())

def do_fit(s, grid=None):
    return m.fit(s['records'], s['exponent_grid'] if grid is None else grid, s['N0'], s['D0'])

def root_optimum(law, C, k):
    # Independent root bracketing: equate marginal benefit per log-N on kND=C.
    def gradient(t):
        n = math.exp(t)
        d = C / k / n
        return (-law['alpha'] * law['A'] * (n / law['N0']) ** -law['alpha']
                + law['beta'] * law['B'] * (d / law['D0']) ** -law['beta'])
    lo, hi = -100., 100.
    assert gradient(lo) < 0 < gradient(hi)
    for _ in range(180):
        mid = (lo + hi) / 2
        if gradient(mid) < 0:
            lo = mid
        else:
            hi = mid
    return math.exp((lo + hi) / 2)

class IndependentChecks(unittest.TestCase):
    def test_asymmetric_optima_against_bracketed_derivative(self):
        rng = random.Random(1909)
        for _ in range(60):
            law = dict(E=rng.random(), A=10**rng.uniform(-2,2), B=10**rng.uniform(-2,2),
                       alpha=rng.uniform(.1,1.4), beta=rng.uniform(.1,1.4),
                       N0=10**rng.uniform(-2,3), D0=10**rng.uniform(-2,3))
            C, k = 10**rng.uniform(-2,8), rng.uniform(.5,12)
            r = m.compute_optimum(law,C,k)
            self.assertAlmostEqual(r['N']/root_optimum(law,C,k),1,places=11)
            self.assertAlmostEqual(k*r['N']*r['D']/C,1,places=13)

    def test_both_bounds_endpoint_and_singleton(self):
        law = dict(LAW,A=2.3,B=.7,alpha=.3,beta=.8,N0=3,D0=7)
        for nb,db in (([1,2],[1,200]),([30,40],[1,200]),([1,100],[5,6]),([10,10],[10,10])):
            r=m.compute_optimum(law,600,N_bounds=nb,D_bounds=db)
            lower=max(nb[0],100/db[1]); upper=min(nb[1],100/db[0])
            expected=min(max(root_optimum(law,600,6),lower),upper)
            self.assertAlmostEqual(r['N'],expected,places=11)
            self.assertTrue(nb[0]<=r['N']<=nb[1]); self.assertTrue(db[0]<=r['D']<=db[1])

    def test_reference_unit_invariance(self):
        law=dict(LAW,A=2,B=3,alpha=.3,beta=.7,N0=11,D0=13)
        changed=dict(law,N0=law['N0']*100,D0=law['D0']*.01,
                     A=law['A']/100**law['alpha'],B=law['B']/.01**law['beta'])
        a=m.compute_optimum(law,600); b=m.compute_optimum(changed,600)
        for key in ('N','D','predicted_loss'):
            self.assertAlmostEqual(a[key]/b[key],1,places=12)

    def test_budget_scaling_exponents(self):
        law=dict(LAW,A=3,B=7,alpha=.2,beta=.6)
        a=m.compute_optimum(law,60); b=m.compute_optimum(law,60000)
        self.assertAlmostEqual(b['N']/a['N'],1000**.75,places=10)
        self.assertAlmostEqual(b['D']/a['D'],1000**.25,places=10)

    def test_lifecycle_against_exact_rational_cost_lines(self):
        # Independent rational oracle: L=1+2/(N/3)+3/(D/5), target 2.
        # Therefore D=15/(1-6/N). All selected Ns are feasible.
        law=dict(LAW,A=2,B=3,N0=3,D0=5,alpha=1,beta=1)
        sizes=[8,10,16,32]
        exact={n:(F(6)*n*(F(15)/(1-F(6,n)))*F(1,4)+7,F(13,2)*n) for n in sizes}
        for calls in (0,1,5,20,1000):
            r=m.lifecycle(law,sizes,2,dict(DEMAND,calls_per_day=calls),COSTS)
            expected=min(sizes,key=lambda n: exact[n][0]+calls*exact[n][1])
            self.assertEqual(r['optimal_N'],expected)
            for row in r['rows']:
                n=row['N']; self.assertAlmostEqual(row['total_cost'],float(exact[n][0]+calls*exact[n][1]))
            for cross in r['crossovers']:
                u,v=cross['left_N'],cross['right_N']
                q=(exact[v][0]-exact[u][0])/(exact[u][1]-exact[v][1])
                self.assertEqual(cross['status'],'nonnegative_crossing' if q>=0 else 'negative_crossing')
                if q>=0: self.assertAlmostEqual(cross['calls'],float(q))
                else: self.assertIsNone(cross['calls'])

    def test_parallel_and_coincident_costs(self):
        costs=dict(COSTS,prefill_per_flop=0,decode_per_flop=0)
        law=dict(LAW,alpha=1,beta=1)
        r=m.lifecycle(law,[3,4],1.5,DEMAND,costs)
        self.assertEqual(r['crossovers'][0]['status'],'parallel')
        r=m.lifecycle(law,[3,4],1.5,DEMAND,dict(costs,train_per_flop=0))
        self.assertEqual(r['crossovers'][0]['status'],'coincident')
        self.assertIsNone(r['crossovers'][0]['calls'])

    def test_target_at_asymptote_and_next_float(self):
        law=dict(LAW,alpha=1,beta=1)
        r=m.lifecycle(law,[2],1.5,DEMAND,COSTS)
        self.assertFalse(r['rows'][0]['feasible'])
        r=m.lifecycle(law,[2],math.nextafter(1.5,math.inf),DEMAND,COSTS)
        self.assertTrue(r['rows'][0]['feasible'])
        self.assertTrue(math.isfinite(r['rows'][0]['D']))
        self.assertGreater(r['rows'][0]['D'],1e15)

    def test_holdout_coordinates_counts_and_labels_do_not_select(self):
        s=scenario(); before=do_fit(s)
        for row in s['records']:
            if row['split']=='holdout':
                row.update(N=1e15,D=1e16,loss=1000,C_flops=1,id='changed-'+row['id'])
        s['records'].append(dict(s['records'][-1],id='extra-holdout',loss=2000))
        after=do_fit(s)
        for key in ('law','fit_sse','candidates','fit_bounds'):
            self.assertEqual(before[key],after[key])
        self.assertNotEqual(before['holdout_rmse'],after['holdout_rmse'])

    def test_metadata_and_recorded_compute_do_not_fit(self):
        s=scenario(); before=m.calculate(s)
        s['generator']={'E':100,'alpha':.9}; s['control_id']='metadata-only'
        for row in s['records']: row['C_flops']=1
        after=m.calculate(s)
        self.assertEqual(before['fit']['law'],after['fit']['law'])
        self.assertNotEqual(before['fit']['predictions'][0]['recorded_to_knd_ratio'],after['fit']['predictions'][0]['recorded_to_knd_ratio'])

    def test_grid_order_and_duplicate_pairs(self):
        s=scenario(); before=do_fit(s)
        after=do_fit(s,list(reversed(s['exponent_grid']))+[s['exponent_grid'][4]])
        self.assertEqual(before['law'],after['law'])
        self.assertEqual(len(after['candidates']),len(before['candidates'])+1)

    def test_off_grid_truth_is_not_silently_added(self):
        s=scenario(); grid=[[.4,.6],[.6,.4]]
        r=do_fit(s,grid)
        self.assertIn([r['law']['alpha'],r['law']['beta']],grid)
        self.assertGreater(r['fit_sse'],1e-8)
        self.assertEqual(len(r['candidates']),2)

    def test_two_level_design_selection_matches_reported_sse(self):
        # Two levels per axis permit both exponent pairs to interpolate exactly.
        records=[]
        for i,(n,d) in enumerate(((1,1),(1,4),(4,1),(4,4),(2,2))):
            records.append(dict(id=str(i),N=n,D=d,loss=10+1/n+1/d,C_flops=6*n*d,
                                split='fit' if i<4 else 'holdout',control_id='c'))
        # Do not assert rounding-sensitive exact ties; verify declared SSE ordering.
        r=m.fit(records,[[1,1],[.5,.5]],1,1)
        self.assertEqual(r['fit_sse'],min(c['fit_sse'] for c in r['candidates']))

    def test_duplicate_physical_holdout_is_caller_assertion(self):
        s=scenario(); s['records'].append(dict(s['records'][0],id='duplicate-run-new-id',split='holdout'))
        r=do_fit(s)
        self.assertEqual(len(r['predictions']),13)  # Characterize lack of provenance deduplication.

    def test_nonfinite_inputs_are_rejected(self):
        for value in (float('nan'),float('inf'),-float('inf')):
            for key in LAW:
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    m.loss(dict(LAW,**{key:value}),1,1)
            s=scenario(); s['records'][0]['loss']=value
            with self.assertRaises(ValueError): do_fit(s)
            with self.assertRaises(ValueError): do_fit(s,[[value,.5]])

    def test_degenerate_design_still_rejected(self):
        s=scenario()
        for row in s['records']: row.update(N=1,D=1)
        with self.assertRaises(ValueError): do_fit(s)

    def test_full_calculation_rejects_nonfinite_cost_output(self):
        s=scenario(); s['costs']['train_per_flop']=1e308
        with self.assertRaises(ValueError): m.calculate(s)

    def test_all_integrated_scenarios_match_archived_results(self):
        for name in ('teaching','perturbed','zero-demand'):
            with self.subTest(name=name):
                s=scenario(name); original=copy.deepcopy(s); result=m.calculate(s)
                self.assertEqual(s,original)
                self.assertEqual(result,json.loads((PROJECT/f'results/scaling-law-{name}.json').read_text()))
                json.dumps(result,allow_nan=False)

class KnownBugRegressions(unittest.TestCase):
    @unittest.expectedFailure
    def test_B1_zero_floor_exact_fit_must_be_admissible(self):
        s=scenario()
        for row in s['records']:
            row['loss']=(row['N']/s['N0'])**-.5+(row['D']/s['D0'])**-.5
        r=do_fit(s,[[.5,.5]])
        self.assertGreaterEqual(r['law']['E'],0)
        self.assertLess(r['fit_sse'],1e-24)

    @unittest.expectedFailure
    def test_B2_bad_grid_member_must_not_discard_good_fit(self):
        s=scenario(); expected=do_fit(s,[[.5,.5]])
        r=do_fit(s,[[.5,.5],[1e-15,.5]])
        self.assertEqual(r['law'],expected['law'])

    @unittest.expectedFailure
    def test_B3_representable_optimum_despite_normalizer_overflow(self):
        r=m.compute_optimum(dict(LAW,N0=1e200,D0=1e200),6e200)
        self.assertAlmostEqual(r['N']/1e100,1,places=11)
        self.assertAlmostEqual(r['D']/1e100,1,places=11)

    @unittest.expectedFailure
    def test_B3_representable_loss_despite_ratio_underflow(self):
        result=m.loss(dict(LAW,N0=1e200),1e-200,1)
        self.assertAlmostEqual(result/1e200,1,places=11)

    @unittest.expectedFailure
    def test_B3_ratio_overflow_must_not_silently_erase_loss_term(self):
        result=m.loss(dict(LAW,E=0,N0=1e-200,B=1e-300),1e200,1)
        self.assertAlmostEqual(result/1e-200,1,places=11)

    @unittest.expectedFailure
    def test_B4_loss_overflow_must_raise_value_error(self):
        with self.assertRaises(ValueError):
            m.loss(dict(LAW,E=1e308,A=1e308,B=1e308),1,1)

    @unittest.expectedFailure
    def test_B4_lifecycle_overflow_must_not_select_infinite_cost(self):
        with self.assertRaises(ValueError):
            m.lifecycle(dict(LAW,alpha=1,beta=1),[3,4],1.5,DEMAND,
                        dict(COSTS,train_per_flop=1e308))

if __name__=='__main__':
    if '--strict' in sys.argv:
        sys.argv.remove('--strict')
        for name in dir(KnownBugRegressions):
            method=getattr(KnownBugRegressions,name)
            if getattr(method,'__unittest_expecting_failure__',False):
                method.__unittest_expecting_failure__=False
    unittest.main()
