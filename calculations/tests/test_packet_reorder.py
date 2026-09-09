"""Independent prefix-delivery oracle and payload conservation."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.packet_reorder import calculate


class PacketReorderTests(unittest.TestCase):
    def test_book_cases(self):
        balanced=calculate(path_delays_ns=[1000,1000],lost_packets=[])['summary']
        self.assertEqual(balanced['completion_exact_ns'],'5096')
        self.assertEqual(balanced['peak_retained_reorder_bytes'],0)
        skewed=calculate(lost_packets=[])['summary']
        self.assertEqual(skewed['completion_exact_ns'],'13096')
        self.assertEqual(skewed['peak_retained_reorder_bytes'],3072)
        loss=calculate()['summary']
        self.assertEqual(loss['completion_exact_ns'],'23048')
        self.assertEqual(loss['peak_retained_reorder_bytes'],7168)
        self.assertEqual(loss['retransmitted_bytes'],1024)
        self.assertEqual(loss['suffix_replay_counterfactual_bytes'],8192)
        self.assertEqual(calculate(recovery_delay_ns=40000)['summary']['completion_exact_ns'],'43048')

    def test_prefix_oracle_tail_and_path_exclusion(self):
        for packet_size in (1000,1024,8192):
            for losses in ([],[0]):
                r=calculate(packet_bytes=packet_size,lost_packets=losses,path_bytes_per_second=3*10**9)
                transmissions=r['transmissions'];s=r['summary']
                arrivals={row['sequence']:Fraction(row['arrival_exact_ns']) for row in transmissions if not row['lost']}
                sizes={row['sequence']:row['bytes'] for row in transmissions}
                prefix=Fraction(0)
                delivered={}
                for row in r['delivery']:
                    seq=row['sequence'];prefix=max(prefix,arrivals[seq]);delivered[seq]=prefix
                    self.assertEqual(Fraction(row['delivery_exact_ns']),prefix)
                peak=max(sum(sizes[seq] for seq in arrivals if arrivals[seq]<=time<delivered[seq]) for time in arrivals.values())
                area=sum(sizes[seq]*(delivered[seq]-arrivals[seq]) for seq in arrivals)
                self.assertEqual(s['peak_retained_reorder_bytes'],peak)
                self.assertEqual(Fraction(s['reorder_area_exact_byte_ns']),area)
                self.assertEqual(sum(row['bytes'] for row in transmissions),s['sent_bytes'])
                self.assertEqual(s['sent_bytes'],s['received_bytes']+s['declared_lost_bytes'])
                self.assertEqual(sum(sizes.values()),8192)
                for path in (0,1):
                    rows=[row for row in transmissions if row['path']==path]
                    for left,right in zip(rows,rows[1:]):
                        self.assertLessEqual(Fraction(left['end_exact_ns']),Fraction(right['start_exact_ns']))

    def test_multiple_losses_and_validation(self):
        r=calculate(lost_packets=[0,3,7],recovery_delay_ns=0)
        self.assertEqual(len(r['delivery']),8)
        self.assertEqual(r['summary']['retransmitted_bytes'],3072)
        for kwargs in (dict(lost_packets=[8]),dict(lost_packets=[0,0]),dict(path_delays_ns=[]),dict(packet_bytes=0)):
            with self.assertRaises(ValueError):calculate(**kwargs)
