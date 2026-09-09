from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.cache_residency import calculate


class ResidencyTests(unittest.TestCase):
    def test_independent_page_sets_each_second(self):
        r=calculate();intervals=r['scenario']['intervals'];page=r['summary']['kv_page_bytes']
        areas={tier:0 for tier in r['scenario']['capacities']};peaks={tier:0 for tier in areas}
        global_area=0
        for second in range(60):
            union=set()
            for tier in areas:
                pages=set()
                for row in intervals:
                    if row['tier']==tier and row['start_ns']<=second*10**9<row['end_ns']:
                        pages.update((row['prefix_identity'],i) for i in range(row['tokens']//16))
                areas[tier]+=len(pages)*page;peaks[tier]=max(peaks[tier],len(pages)*page);union|=pages
            global_area+=len(union)*page
        for row in r['residency_tiers']:
            self.assertEqual(F(row['physical_byte_seconds_exact']),areas[row['tier']])
            self.assertEqual(row['peak_bytes'],peaks[row['tier']])
        self.assertEqual(F(r['summary']['globally_unique_byte_seconds_exact']),global_area)
        self.assertEqual(peaks['HBM'],360*1024**2)

    def test_capacity_exact_and_half_open(self):
        r=calculate(capacities=dict(HBM=360*1024**2-1,DRAM=1024**3,SSD=4*1024**3))
        self.assertFalse(r['summary']['all_tiers_capacity_feasible'])
        self.assertEqual(r['residency_tiers'][0]['over_capacity_nanoseconds'],10**9)
        rows=[dict(id='a',tier='H',prefix_identity='a',tokens=16,start_ns=0,end_ns=1),
              dict(id='b',tier='H',prefix_identity='b',tokens=16,start_ns=1,end_ns=2)]
        s=calculate(intervals=rows,capacities={'H':16*147456})['summary']
        self.assertTrue(s['all_tiers_capacity_feasible'])
        self.assertEqual(s['all_tier_peak_physical_bytes'],16*147456)

    def test_identity_and_complete_pages(self):
        row=dict(id='a',tier='H',prefix_identity='a',tokens=16,start_ns=0,end_ns=10)
        same=dict(row,id='b');different=dict(same,prefix_identity='b')
        a=calculate(intervals=[row,same],capacities={'H':10**9})
        b=calculate(intervals=[row,different],capacities={'H':10**9})
        self.assertEqual(b['summary']['all_tier_peak_physical_bytes'],2*a['summary']['all_tier_peak_physical_bytes'])
        with self.assertRaises(ValueError):calculate(intervals=[dict(row,tokens=17)],capacities={'H':10**9})
