import unittest
import json
import math
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from infra_calc.topics import scaling_law as m
from infra_calc.paths import PROJECT

LAW=dict(E=1.,A=1.,B=1.,alpha=.5,beta=.5,N0=1.,D0=1.)
class ScalingTests(unittest.TestCase):
 def setUp(self): self.s=json.loads((PROJECT/'scenarios/scaling-law-teaching.json').read_text())
 def test_exact_recovery_and_holdouts(self):
  f=m.calculate(self.s)['fit']
  for key in ('E','A','B'): self.assertAlmostEqual(f['law'][key],1,places=10)
  self.assertEqual((f['law']['alpha'],f['law']['beta']),(.5,.5))
  self.assertLess(f['holdout_rmse'],1e-12)
  self.assertEqual([r['outside_fit_box'] for r in f['predictions'] if r['split']=='holdout'],[False,True,True])
 def test_holdout_never_trains(self):
  original=m.calculate(self.s)['fit']['law']
  for r in self.s['records']:
   if r['split']=='holdout': r['loss']=100
  self.assertEqual(m.calculate(self.s)['fit']['law'],original)
 def test_analytic_symmetric_optimum(self):
  # ND=100; AM-GM on 1/sqrt(N)+1/sqrt(D) gives N=D=10.
  r=m.compute_optimum(LAW,600)
  self.assertAlmostEqual(r['N'],10); self.assertAlmostEqual(r['D'],10)
  self.assertAlmostEqual(r['predicted_loss'],1+2/math.sqrt(10))
 def test_independent_integer_enumeration(self):
  # alpha=beta=1, A=4 B=1; ND=144 optimum N=24 D=6.
  law=dict(LAW,alpha=1,beta=1,A=4)
  pairs=[(1+4/n+1/d,n,d) for n in range(1,145) for d in range(1,145) if n*d<=144]
  best=min(pairs); r=m.compute_optimum(law,864)
  self.assertAlmostEqual(r['predicted_loss'],best[0]); self.assertAlmostEqual(r['N'],best[1])
 def test_dense_log_enumeration(self):
  law=dict(LAW,A=2,alpha=.3,beta=.7)
  r=m.compute_optimum(law,600)
  vals=[1+2/n**.3+(n/100)**.7 for n in [math.exp(-8+i*16/10000) for i in range(10001)]]
  self.assertLessEqual(r['predicted_loss'],min(vals)+1e-12)
  self.assertLess(min(vals)-r['predicted_loss'],1e-6)
 def test_bounds_and_infeasible(self):
  r=m.compute_optimum(LAW,600,N_bounds=[1,5]); self.assertEqual(r['N'],5); self.assertTrue(r['boundary'])
  r=m.compute_optimum(LAW,600,D_bounds=[1,5]); self.assertEqual(r['D'],5)
  with self.assertRaises(ValueError): m.compute_optimum(LAW,600,N_bounds=[1,2],D_bounds=[1,2])
 def test_lifetime_analytic_and_crossover(self):
  # L=1+1/N+1/D=1.5: (N,D)=(3,6),(4,4); upfront=108,96.
  # per-call=2N: 6,8, so equality at six calls.
  c=dict(train_per_flop=1,prefill_per_flop=1,decode_per_flop=1,setup_cost=0,prefill_flops_per_parameter_token=2,decode_flops_per_parameter_token=2)
  d=dict(calls_per_day=6,lifetime_days=1,input_tokens=1,output_tokens=0)
  law=dict(LAW,alpha=1,beta=1)
  r=m.lifecycle(law,[2,3,4],1.5,d,c)
  self.assertFalse(r['rows'][0]['feasible'])
  self.assertAlmostEqual(r['crossovers'][0]['calls'],6)
  for row in r['rows'][1:]: self.assertAlmostEqual(row['total_cost'],144)
  # Independent finite enumeration at target quality: minimum D for each N.
  for calls in (0,5,7,100):
   d['calls_per_day']=calls
   result=m.lifecycle(law,[3,4],1.5,d,c)
   brute=min((6*n*t+2*n*calls,n) for n in (3,4) for t in range(1,101) if 1+1/n+1/t<=1.5)
   self.assertEqual(result['optimal_N'],brute[1])
 def test_zero_and_infeasible(self):
  self.s['demand']['calls_per_day']=0; r=m.calculate(self.s)
  self.assertTrue(all(x['lifetime_inference_cost']==0 for x in r['lifecycle']['rows'] if x['feasible']))
  self.s['target_loss']=.5
  self.assertIsNone(m.calculate(self.s)['lifecycle']['optimal_N'])
 def test_unknown_fields_preserved_and_no_mutation(self):
  self.s['future']={'unknown':None}; self.s['records'][0]['extra']='keep'
  original=deepcopy(self.s); r=m.calculate(self.s)
  self.assertEqual(self.s,original); self.assertEqual(r['scenario'],original)
  self.assertEqual(r['fit']['predictions'][0]['extra'],'keep')
  json.dumps(r,allow_nan=False)
 def test_validation(self):
  for key,value in [('model_family','moe'),('data_kind','product_history')]:
   s=deepcopy(self.s); s[key]=value
   with self.assertRaises(ValueError): m.calculate(s)
  for value in (True,-1,float('inf'),float('nan'),'1'):
   with self.assertRaises(ValueError): m.loss(LAW,value,1)
  self.s['records'][0]['control_id']='different'
  with self.assertRaises(ValueError): m.calculate(self.s)
 def test_rank_deficient(self):
  for r in self.s['records']: r['N']=1e9; r['D']=1e10
  with self.assertRaises(ValueError): m.calculate(self.s)
 def test_policy_budget_conservation(self):
  result=m.calculate(self.s)
  for r in result['allocation_policy_comparison']:
   self.assertAlmostEqual(6*r['N']*r['D']/r['budget_flops'],1)
  self.assertEqual(len(result['allocation_policy_comparison']),8)
 def test_sensitivity(self):
  r=m.calculate(self.s)
  self.assertGreater(len(r['extrapolation_sensitivity']),1)
  values=[x['predictions'][-1]['loss'] for x in r['extrapolation_sensitivity']]
  self.assertGreater(max(values)-min(values),.01)
if __name__=='__main__': unittest.main()
