from fractions import Fraction as F
from pathlib import Path
from math import exp
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.checkpoint_interval import calculate,renewal_seconds


class CheckpointIntervalTests(unittest.TestCase):
    def test_first_order_and_stationary_points(self):
        r=calculate();s=r['summary'];c=F(14*8190735360,8*10**9);rate=F(1024,365*86400)
        for row in r['checkpoint_interval_rows']:
            t=row['useful_interval_seconds']
            self.assertEqual(F(row['first_order_loss_exact']),c/t+rate*t/2+rate*120)
        t=s['first_order_optimal_useful_interval_seconds']
        self.assertAlmostEqual(float(c)/t**2,float(rate)/2,places=14)
        opt=s['poisson_optimal_useful_interval_seconds']
        middle=opt/renewal_seconds(F(opt),c,rate,F(120))
        for factor in (.99,1.01):
            x=opt*factor
            self.assertGreater(middle,x/renewal_seconds(F(x),c,rate,F(120)))

    def test_renewal_equation_independent_geometric_series(self):
        # Integrate a failed attempt by midpoint quadrature, sum failed retries explicitly.
        t,c,rate,recovery=F(10),F(2),F(1,100),F(3)
        length=float(t+c);p=exp(-float(rate)*length)
        bins=20000;dt=length/bins
        failed_duration=sum((i+.5)*dt*float(rate)*exp(-float(rate)*(i+.5)*dt)*dt for i in range(bins))
        one_attempt=p*length+failed_duration+(1-p)*float(recovery)
        expectation=sum((1-p)**k*one_attempt for k in range(100))
        self.assertAlmostEqual(expectation,renewal_seconds(t,c,rate,recovery),places=7)

    def test_common_shock_zero_and_high_failure(self):
        r=calculate(common_job_mtbf_seconds=86400)
        self.assertEqual(F(r['summary']['job_failure_rate_exact_per_second']),F(1024,365*86400)+F(1,86400))
        zero=calculate(failure_free=True)
        self.assertIsNone(zero['summary']['poisson_optimal_useful_interval_seconds'])
        self.assertEqual(zero['summary']['best_enumerated_poisson_intervals'],[3600])
        high=calculate(device_mtbf_seconds=86400,intervals_seconds=[60,120,300])
        self.assertTrue(any(not row['first_order_loss_below_one'] for row in high['checkpoint_interval_rows']))
        for row in high['checkpoint_interval_rows']:
            self.assertTrue(0<row['poisson_retained_useful_fraction']<1)
        changed=calculate(recovery_ns=500*10**9)
        self.assertEqual(changed['summary']['poisson_optimal_useful_interval_seconds'],calculate()['summary']['poisson_optimal_useful_interval_seconds'])
