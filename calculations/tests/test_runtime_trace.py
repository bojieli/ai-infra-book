"""Recorded launch distinctions, memory ledger and interval union witness."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.runtime_trace import calculate,union_ns


class RuntimeTraceTests(unittest.TestCase):
    def test_recorded_submission_and_microbatches(self):
        r=calculate();traces={x['label']:x for x in r['runtime_ranges']}
        self.assertEqual((traces['eager']['launch_api_count'],traces['eager']['kernel_count']),(18,18))
        self.assertEqual((traces['graph']['launch_api_count'],traces['graph']['kernel_count']),(3,18))
        self.assertEqual((traces['fused_graph']['launch_api_count'],traces['fused_graph']['kernel_count']),(3,15))
        self.assertEqual((traces['fused_graph_micro8']['graph_launch_count'],traces['fused_graph_micro8']['kernel_count']),(24,168))
        self.assertEqual(traces['fused_graph_copy']['copy_payload_bytes'],3*32*4096*2)
        rows={x['label']:x for x in r['runtime_timings']}
        for label in ('eager_micro4','eager_micro8','fused_graph_micro4','fused_graph_micro8'):
            self.assertEqual(rows[label]['matrix_flops'],rows['eager']['matrix_flops'])
        self.assertEqual(rows['fused_graph']['live_io_intermediate_bytes'],int(2.75*2**20))
        self.assertGreater(rows['fused_graph_micro8']['measured_median_us'],7*rows['fused_graph']['measured_median_us'])
        self.assertEqual(r['paper_comparison']['reported_latency_ratio_exact'],'29/25')

    def test_padding_and_recorded_scope(self):
        r=calculate(tokens=257);self.assertEqual(r['runtime_ranges'],[])
        rows={x['label']:x for x in r['runtime_timings']}
        padded=rows['fused_graph_pad512'];exact=rows['fused_graph']
        self.assertEqual(padded['matrix_flops']-exact['matrix_flops'],6*255*4096*12288)
        self.assertEqual(padded['live_io_intermediate_bytes'],44*2**20)
        self.assertEqual(r['summary']['weight_bytes'],288*2**20)
        for row in rows.values():
            self.assertLessEqual(row['measured_min_us'],row['measured_median_us'])
            self.assertGreaterEqual(row['measured_max_us'],row['measured_median_us'])
        with self.assertRaises(ValueError):calculate(tokens=256)

    def test_union_by_discrete_occupied_ticks(self):
        intervals=[(2,7),(3,4),(5,10),(10,11),(15,19),(19,19)]
        occupied={t for a,b in intervals for t in range(a,b)}
        self.assertEqual(union_ns(intervals),len(occupied))
        self.assertEqual(union_ns([]),0)
        with self.assertRaises(ValueError):union_ns([(4,3)])
