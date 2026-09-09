"""Independent stop/wait, ACK deadlines and physical byte conservation."""
import sys
from pathlib import Path
from fractions import Fraction as F
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.connection_window import calculate


class ConnectionWindowTests(unittest.TestCase):
    def inputs(self):
        return dict(input_bytes=10,output_bytes=1,segment_bytes=4,upload_bits_per_second=8,
            download_bits_per_second=8,forward_propagation_seconds=2,reverse_propagation_seconds=3,
            initial_window_bytes=4,max_window_bytes=4,receive_window_bytes=4,ack_growth_bytes=0,
            data_header_bytes=1,ack_bytes=1,rto_seconds=100,model_seconds=0)

    def test_stop_wait_partial_tail_shared_reverse(self):
        r=calculate(**self.inputs())
        self.assertEqual([F(x['time_seconds_exact']) for x in r['data_arrivals'] if x['transfer']=='upload'],[7,18,27])
        self.assertEqual(r['transfers']['upload']['all_unique_acked_seconds_exact'],'31')
        self.assertEqual(r['summary']['complete_final_image_seconds_exact'],'33')
        self.assertEqual(r['summary']['protocol_last_ack_seconds_exact'],'36')
        self.assertEqual(r['transfers']['upload']['data_wire_bytes'],13)
        self.assertEqual(r['transfers']['upload']['ack_wire_bytes'],3)
        for direction in ('c2s','s2c'):
            tx=sorted([x for x in r['transmissions'] if x['direction']==direction],key=lambda x:F(x['start_seconds_exact']))
            self.assertTrue(all(F(a['end_seconds_exact'])<=F(b['start_seconds_exact']) for a,b in zip(tx,tx[1:])))

    def test_exact_ack_deadline_and_one_loss(self):
        a=self.inputs();a.update(input_bytes=1,segment_bytes=1,initial_window_bytes=1,max_window_bytes=1,receive_window_bytes=1,data_header_bytes=0,rto_seconds=6)
        r=calculate(**a);self.assertEqual(r['summary']['recoveries'],0)
        a['drop_upload_packet']=0;r=calculate(**a)
        self.assertEqual(r['transfers']['upload']['complete_received_seconds_exact'],'10')
        self.assertEqual(r['transfers']['upload']['data_wire_bytes'],2)
        self.assertEqual(r['transfers']['upload']['unique_received_bytes'],1)
        a['rto_seconds']=5
        with self.assertRaises(ValueError):calculate(**a)

    def test_headers_and_ack_do_not_disappear(self):
        r=calculate(input_bytes=7,output_bytes=5,segment_bytes=4,initial_window_bytes=8,
                    max_window_bytes=8,receive_window_bytes=8,rto_seconds=10)
        for name,size in [('upload',7),('download',5)]:
            self.assertEqual(r['transfers'][name]['data_wire_bytes'],size+2*40)
            self.assertEqual(r['transfers'][name]['ack_wire_bytes'],2*40)
        self.assertEqual(sum(x['wire_bytes'] for x in r['links'].values()),12+8*40)

    def test_illegal_credit_and_recovery_contract(self):
        for args in [dict(initial_window_bytes=1),dict(drop_upload_packet=0,drop_download_packet=0),dict(ack_bytes=True),dict(rto_seconds=0),dict(max_total_packets=1),dict(handshake=[{'direction':'bad','bytes':4}])]:
            with self.subTest(args=args),self.assertRaises(ValueError):calculate(**args)


if __name__=='__main__':unittest.main()
