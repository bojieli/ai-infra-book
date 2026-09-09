from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.cache_missing import calculate,compare_bf16


class MissingPageTests(unittest.TestCase):
    def test_bf16_layout_and_nonfinite(self):
        a=[0x3f80]*8;b=a.copy();b[0]=0x4000;b[6]=0x4040
        result=compare_bf16(struct.pack('<8H',*a),struct.pack('<8H',*b),layers=2,page_tokens=2,heads=1,head_dim=1)
        self.assertEqual(result['different_elements'],2)
        self.assertEqual(result['max_abs_difference'],2)
        self.assertEqual([r['different_elements'] for r in result['layers']],[1,1])
        b[0]=0x7f80
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            compare_bf16(struct.pack('<8H',*a),struct.pack('<8H',*b),layers=2,page_tokens=2,heads=1,head_dim=1)

    def test_actual_recovery_and_contiguous_prefix(self):
        r=calculate();a,b=r['missing_page_cases']
        self.assertEqual(a['different_bf16_elements'],0)
        self.assertEqual(b['different_bf16_elements'],995403)
        self.assertEqual(b['max_abs_difference'],26.75)
        self.assertEqual(b['get_file_bytes'],32*36*2*16*8*128*2)
        self.assertEqual(b['first_recomputed_tokens'],512)
        layers=[row for row in r['missing_page_layers'] if row['case']=='middle']
        self.assertEqual(layers[0]['different_elements'],0)
        self.assertEqual(sum(row['different_elements'] for row in layers),995403)

    def test_extra_recompute_matrix_closed_form(self):
        r=calculate();first=[row for row in r['missing_page_requests'] if row['index']==0]
        difference=first[0]['prefill_matrix_flops']-first[1]['prefill_matrix_flops']
        per_token=36*2*(4096*(32*128+2*8*128)+32*128*4096+3*4096*12288)
        self.assertEqual(difference,512*per_token+4*36*32*128*(512*513//2))

    def test_device_control_boundary_and_pairwise_counts(self):
        from array import array
        import json
        from infra_calc.paths import PROJECT
        r=calculate()
        self.assertEqual([row['cached_tokens'] for row in r['device_control_requests']],[512,1008,1008])
        prep=json.loads((PROJECT/'sources/cache-missing/preparation.json').read_text())
        name=next(case['omitted'] for case in prep['cases'] if case['case']=='middle')
        paths=[PROJECT/'sources/cache-restart/storage-v3'/name,
               PROJECT/'sources/cache-missing/restored-middle.bin',
               PROJECT/'sources/cache-missing/device-prefix-v2-page32.bin']
        words=[]
        for path in paths:
            a=array('H');a.frombytes(path.read_bytes());words.append(a)
        comparisons={row['comparison']:row for row in r['device_control_comparisons']}
        for label,left in [('full_vs_device',words[0]),('storage_vs_device',words[1])]:
            count=sum(a!=b for a,b in zip(left,words[2]))
            self.assertEqual(comparisons[label]['different_elements'],count)
            self.assertEqual(sum(layer['different_elements'] for layer in comparisons[label]['layers']),count)
        self.assertEqual(comparisons['full_vs_device']['different_elements'],1021226)
        self.assertEqual(comparisons['storage_vs_device']['different_elements'],992972)
