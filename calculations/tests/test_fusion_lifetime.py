"""Boundary 2X savings and allocation-before-release lifetime checks."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.fusion_lifetime import calculate,ledger


class FusionLifetimeTests(unittest.TestCase):
    def test_qwen_intermediate_and_materialization(self):
        r=calculate();s=r['summary']
        self.assertEqual(s['bf16_intermediate_bytes'],24*2**20)
        self.assertEqual(s['separate_interface_bytes'],156*2**20)
        self.assertEqual(s['fused_interface_bytes'],60*2**20)
        self.assertEqual(s['separate_tensor_peak_bytes'],72*2**20)
        self.assertEqual(s['fused_tensor_peak_bytes'],60*2**20)
        for row in r['fusion_variants']:
            self.assertEqual(row['saved_interface_bytes'],(2-len(row['boundaries']))*48*2**20)
            self.assertEqual(row['final_live'],['quantized'])

    def test_layout_copy_and_peak_are_different_quantities(self):
        r=calculate(layout_copy=True);s=r['summary']
        self.assertEqual(s['contiguous_partitions'],8)
        self.assertEqual(s['standalone_layout_read_write_bytes'],48*2**20)
        self.assertEqual(s['separate_interface_bytes'],204*2**20)
        self.assertEqual(s['separate_tensor_peak_bytes'],72*2**20)
        self.assertLess(s['separate_tensor_peak_bytes'],sum(r['tensor_sizes'].values()))

    def test_allocate_before_release(self):
        sizes={'a':8,'b':12,'c':4}
        ops=[dict(name='first',inputs=['a'],output='b'),dict(name='second',inputs=['b'],output='c')]
        separate=ledger(sizes,ops,[0]);fused=ledger(sizes,ops,[])
        self.assertEqual(separate['declared_tensor_peak_bytes'],20)
        self.assertEqual(separate['stages'][0]['released_after'],['a'])
        self.assertEqual(fused['declared_tensor_peak_bytes'],12)
        self.assertEqual(separate['interface_bytes']-fused['interface_bytes'],24)
        with self.assertRaises(ValueError): ledger(sizes,ops,[1])
