"""Critical-path switch, explicit contention and independent path enumeration."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.request_dag import calculate


class RequestDagTests(unittest.TestCase):
    def test_path_switch_and_no_gain(self):
        s=calculate()['summary']
        self.assertEqual(s['baseline_finish_ns'],80000)
        self.assertEqual(s['modified_finish_ns'],60000)
        self.assertEqual(s['frozen_old_path_ns'],35000)
        self.assertEqual(s['modified_critical_path'],['prepare','parallel','finish'])
        self.assertEqual(s['serial_equivalent_speedup'],1.6)
        self.assertEqual(calculate(duration_overrides={'parallel':10000})['summary']['modified_finish_ns'],80000)
        self.assertEqual(calculate(duration_overrides={'hotspot':15000,'parallel':90000})['summary']['modified_finish_ns'],110000)

    def test_resource_edges_and_mutual_exclusion(self):
        r=calculate(resource_overrides={'parallel':'compute'})
        modified=r['request_schedules']['modified']
        self.assertEqual(modified['finish_ns'],75000)
        self.assertEqual(modified['critical_path'],['prepare','hotspot','parallel','finish'])
        by_id={row['id']:row for row in modified['tasks']}
        for row in modified['tasks']:
            for pred in row['scheduled_predecessors']:
                self.assertGreaterEqual(row['start_ns'],by_id[pred]['end_ns'])
        for a in modified['tasks']:
            for b in modified['tasks']:
                if a['id']!=b['id'] and a['resource']==b['resource'] and a['resource'] is not None:
                    self.assertTrue(a['end_ns']<=b['start_ns'] or b['end_ns']<=a['start_ns'])

    def test_unconstrained_longest_paths_and_invalid_graph(self):
        tasks=[dict(id='a',duration_ns=2,deps=[]),dict(id='b',duration_ns=7,deps=['a']),
               dict(id='c',duration_ns=3,deps=['a']),dict(id='d',duration_ns=4,deps=['b','c']),
               dict(id='e',duration_ns=9,deps=['c'])]
        r=calculate(tasks=list(reversed(tasks)))
        self.assertEqual(r['summary']['baseline_finish_ns'],max(2+7+4,2+3+4,2+3+9))
        self.assertEqual(r['summary']['modified_finish_ns'],r['summary']['baseline_finish_ns'])
        with self.assertRaises(ValueError):calculate(tasks=[dict(id='a',duration_ns=1,deps=['a'])])
        with self.assertRaises(ValueError):calculate(tasks=[dict(id='a',duration_ns=1,deps=['missing'])])
        with self.assertRaises(ValueError):calculate(duration_overrides={'hotspot':-1})
        zero=calculate(tasks=[dict(id='z',duration_ns=0,deps=[])])
        self.assertEqual(zero['summary']['baseline_finish_ns'],0)
        self.assertIsNone(zero['summary']['request_speedup'])
