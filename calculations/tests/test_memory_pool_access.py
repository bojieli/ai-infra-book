import sys
import unittest
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.memory_pool_access import calculate,layout_svg

class PoolTests(unittest.TestCase):
    def test_unique_data_replication_and_failures(self):
        for copies in (1,2,3):
            r=calculate(copies); c=r['capacity']
            self.assertEqual(c['total_physical_used_bytes'],(192+16*(copies-1))*2**30)
            self.assertEqual(c['whole_job_migration_feasible_assignments'],[])
            failure=next(f for f in r['failure_sets'] if f['failed_nodes']==[1])
            self.assertEqual(failure['unavailable_job_owners'],[0,1] if copies==1 else [1])
            self.assertEqual(sum(c['physical_free_after_pool_bytes'])+c['total_physical_used_bytes'],256*2**30)
    def test_periodic_backlog_independently(self):
        for row in calculate()['access_scenarios']:
            service=Fraction(row['serialized_read_service_seconds_exact'])
            period=Fraction(row['period_seconds_exact']);finish=Fraction(0);waits=[]
            for n in range(20):
                start=max(n*period,finish);waits.append(start-n*period);finish=start+service
            self.assertEqual(row['deterministic_serial_queue_bounded'],all(w==0 for w in waits))
            self.assertEqual(waits[-1],19*max(0,service-period))
        self.assertEqual(calculate(1)['access_scenarios'],calculate(3)['access_scenarios'])
    def test_reject_and_diagram(self):
        for bad in (0,4,True,1.0,'1'):
            with self.assertRaises(ValueError):calculate(bad)
        root=ElementTree.fromstring(layout_svg(calculate()))
        self.assertEqual(root.attrib['viewBox'],'0 0 1200 650')
        with self.assertRaises(ValueError):layout_svg(calculate(2))
