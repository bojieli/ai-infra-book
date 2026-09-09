"""Synthetic GGUF reader boundaries and actual tensor/file byte partitions."""
import struct
from fractions import Fraction
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.gguf_header import parse,TruncatedHeader
from infra_calc.topics.gguf_layout import calculate


class GGUFLayoutTests(unittest.TestCase):
    def test_synthetic_header_and_all_truncations(self):
        # v3, one tensor, no metadata; name 'x', rank1 dimension256,
        # Q4_K enum12, first data offset0. No external implementation fixture.
        data=b'GGUF'+struct.pack('<IQQ',3,1,0)+struct.pack('<Q',1)+b'x'+struct.pack('<IQIQ',1,256,12,0)
        parsed=parse(data)
        self.assertEqual(parsed['header_bytes'],len(data))
        self.assertEqual(parsed['data_start_bytes']%32,0)
        self.assertEqual(parsed['tensors'],[dict(name='x',shape=[256],type_id=12,offset=0)])
        for end in range(len(data)):
            with self.assertRaises(TruncatedHeader):parse(data[:end])
        with self.assertRaises(ValueError):parse(b'BAD!'+data[4:])

    def test_actual_shard_payload_by_offset_differences(self):
        for variant in ('Q2_K','Q4_K_M'):
            r=calculate(variant)
            for i,shard in enumerate(r['gguf_shards'],1):
                tensors=sorted((t for t in r['gguf_tensors'] if t['shard']==i),key=lambda t:t['offset'])
                # Actual published tensors are contiguous in these shards.
                for a,b in zip(tensors,tensors[1:]):
                    self.assertEqual(b['offset']-a['offset'],a['payload_bytes'])
                self.assertEqual(shard['file_bytes'],shard['header_bytes']+shard['header_alignment_bytes']+shard['tensor_payload_bytes']+shard['tensor_padding_bytes'])
            self.assertEqual(r['summary']['parameters'],235093634560)
            self.assertEqual(r['summary']['tensors'],1131)

    def test_mixed_precision_and_scale_overhead(self):
        q2=calculate();q4=calculate('Q4_K_M')
        self.assertEqual(q2['summary']['storage_types'],['F32','Q2_K','Q3_K','Q4_K','Q6_K'])
        self.assertEqual(q4['summary']['storage_types'],['F32','Q4_K','Q6_K'])
        for r in (q2,q4):
            for t in r['gguf_types']:
                self.assertEqual(t['payload_bytes'],t['code_or_float_bytes']+t['scale_metadata_bytes'])
                if t['type']=='Q2_K':self.assertEqual(t['scale_metadata_bytes'],t['elements']//256*(16+2+2))
                if t['type']=='Q4_K':self.assertEqual(t['scale_metadata_bytes'],t['elements']//256*(12+2+2))
        self.assertGreater(Fraction(q2['summary']['file_bits_per_parameter_exact']),2)
        self.assertGreater(Fraction(q4['summary']['file_bits_per_parameter_exact']),4)
