"""Official block-byte algebra, materialization and exact win intervals."""
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.kv_codec import calculate


class KVCodecTests(unittest.TestCase):
    def test_block_storage(self):
        rows=calculate()['kv_codec_rows']
        self.assertEqual([r['history_resident_bytes']//1024**2 for r in rows],[1152,612,324])
        blocks=2*36*8*8192*(128//32)
        for row,bytes_per_block in zip(rows,[64,34,18]):
            self.assertEqual(row['history_resident_bytes'],blocks*bytes_per_block)
            self.assertEqual(row['history_code_bytes']+row['history_scale_bytes'],row['history_resident_bytes'])
            self.assertEqual(row['next_token_append_bytes']*8192,row['history_resident_bytes'])

    def test_materialized_extra_io(self):
        r=calculate();base=r['summary']['bf16_history_bytes']
        for row in r['kv_codec_rows'][1:]:
            self.assertEqual(row['materialized_declared_traffic_bytes']-row['fused_declared_traffic_bytes'],2*base)
            self.assertEqual(F(row['materialized_ns_exact'])-F(row['fused_ns_exact']),F(2*base*10**9,10**12))
            self.assertFalse(row['materialized_wins'])

    def test_exact_winning_intervals(self):
        for rate,fixed,encode in [('1/1000',100000,20000),('1/10000',0,0),('1/500',0,0),('1',0,0)]:
            settings=dict(decode_ns_per_value=rate,decode_fixed_ns=fixed,append_encode_ns=encode)
            r=calculate(**settings)
            for index,row in enumerate(r['kv_codec_rows'][1:],1):
                lower,upper=row['winning_length_min'],row['winning_length_max']
                lengths={1,2,1024,8192}
                for boundary in (lower,upper):
                    if boundary is not None:lengths.update(n for n in (boundary-1,boundary,boundary+1) if 1<=n<=40960)
                for n in lengths:
                    actual=calculate(length=n,**settings)['kv_codec_rows'][index]
                    predicted=lower is not None and n>=lower and (upper is None or n<=upper)
                    self.assertEqual(actual['fused_wins'],predicted)
        q4=calculate()['kv_codec_rows'][2]
        self.assertEqual(q4['strict_fused_crossover_length'],3717)
