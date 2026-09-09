"""Check exact book times, resource exclusion and separate buffer ownership."""
from pathlib import Path
from fractions import Fraction
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.host_transfer import calculate


class HostTransferTests(unittest.TestCase):
    def test_book_and_single_device(self):
        s=calculate()['summary']
        self.assertEqual(s['block_bytes'],64*2**20)
        self.assertEqual(Fraction(s['copy_exact_seconds']),Fraction(1,384))
        self.assertEqual(Fraction(s['scheduled_finish_exact_seconds']),Fraction(1,1000)+Fraction(1,384)+8*Fraction(4,1000))
        single=calculate(device_slots=1)['summary']
        self.assertEqual(Fraction(single['scheduled_finish_exact_seconds']),Fraction(1,1000)+8*(Fraction(1,384)+Fraction(4,1000)))
        slow=calculate(bandwidth_bytes_per_second=12*2**30)['summary']
        self.assertEqual(Fraction(slow['scheduled_finish_exact_seconds']),Fraction(1,1000)+8*Fraction(1,192)+Fraction(4,1000))
        self.assertEqual(s['total_h2d_bytes'],single['total_h2d_bytes'])
        self.assertEqual(s['total_h2d_bytes'],slow['total_h2d_bytes'])

    def test_resource_and_lifetime_constraints(self):
        for host in (1,2,3):
            for device in (1,2,3):
                for prep,consume in ((1,9),(9,1),(4,4)):
                    r=calculate(blocks=9,host_slots=host,device_slots=device,prepare_ns=prep*10**6,consume_ns=consume*10**6)
                    host_free={};device_free={};last={}
                    for row in r['transfer_blocks']:
                        t={k:Fraction(v) for k,v in row['exact_seconds'].items()}
                        self.assertGreaterEqual(t['prepare_start'],host_free.get(row['host_slot'],0))
                        self.assertGreaterEqual(t['copy_start'],device_free.get(row['device_slot'],0))
                        self.assertGreaterEqual(t['copy_start'],t['prepare_end'])
                        self.assertGreaterEqual(t['consume_start'],t['copy_end'])
                        for stage in ('prepare','copy','consume'):
                            self.assertGreaterEqual(t[stage+'_start'],last.get(stage,0))
                            last[stage]=t[stage+'_end']
                        host_free[row['host_slot']]=t['copy_end']
                        device_free[row['device_slot']]=t['consume_end']
                    s=r['summary']
                    for pool in ('host','device'):
                        self.assertLessEqual(s[pool+'_live_peak_bytes'],s[pool+'_reserved_pool_bytes'])
                    self.assertLessEqual(s['scheduled_finish_seconds'],s['serial_seconds']+1e-12)
                    self.assertGreaterEqual(s['scheduled_finish_seconds']+1e-12,s['ideal_unconstrained_pipeline_seconds'])

    def test_one_block_and_invalid_inputs(self):
        s=calculate(blocks=1,host_slots=1,device_slots=1)['summary']
        self.assertEqual(s['serial_seconds'],s['scheduled_finish_seconds'])
        for kwargs in ({'host_slots':0},{'device_slots':True},{'prepare_ns':-1},{'bandwidth_bytes_per_second':0}):
            with self.assertRaises(ValueError):calculate(**kwargs)
