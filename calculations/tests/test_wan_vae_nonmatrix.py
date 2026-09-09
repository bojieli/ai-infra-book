import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.wan_vae_nonmatrix import calculate,read_trace,interpolate_rows
from infra_calc.topics.wan_vae_decode import calculate as decode


class WanVAENonmatrixTests(unittest.TestCase):
    def test_all_primitive_counters_match_held_out_official_executions(self):
        trace=read_trace()
        for sample in trace['validation']:
            self.assertEqual(interpolate_rows(trace,*sample['shape']),sample['rows'])
        r=calculate()
        self.assertEqual(r['status'],'known_scalar_and_copy_boundaries_accounted')
        self.assertEqual(r['unclassified_dispatch'],[])
        self.assertTrue(any(x['operator']=='aten.bmm.default' for x in r['excluded_dispatch']))
        self.assertFalse(any('sdpa.' in x['operator'] for x in r['operators']))

    def test_destandardization_softmax_clamp_and_growing_concat(self):
        t,h,w=7,5,6
        rows=calculate(t,h,w)['operators']
        stage=lambda s:[r for r in rows if r['stage']==s]
        self.assertEqual(sum(r['scalar_arithmetic_ops'] for r in stage('latent_destandardization')),2*48*t*h*w)
        self.assertEqual(stage('output_wrapper')[0]['comparisons'],2*3*(4*t-3)*256*h*w)
        cat=stage('growing_output_concat')[0]
        self.assertEqual(cat['calls'],t-1)
        self.assertEqual(cat['output_elements'],768*h*w*(t-1)*(2*t+1))
        softmax=next(r for r in rows if r['operator']=='aten._safe_softmax.default')
        self.assertEqual(softmax['exp_evaluations'],t*(h*w)**2)
        nearest=stage('nearest_spatial_upsample')[0]
        self.assertEqual(nearest['logical_read_bytes'],nearest['logical_write_bytes'])
        self.assertEqual(nearest['calls'],3*t)
        self.assertEqual(stage('temporal_channel_shuffle')[0]['operator'],'aten.stack.default')

    def test_storage_sensitivity_and_matrix_compatibility(self):
        a=calculate(3,2,3,4);b=calculate(3,2,3,2)
        self.assertEqual(a['summary']['scalar_arithmetic_ops'],b['summary']['scalar_arithmetic_ops'])
        self.assertEqual(a['summary']['logical_read_bytes'],2*b['summary']['logical_read_bytes'])
        self.assertEqual(decode(3,2,3)['nonmatrix_work'],a)
        self.assertEqual(calculate(2,1,3)['status'],'unavailable_degenerate_spatial_layout')
        for invalid in (True,3,0):
            with self.assertRaises(ValueError):calculate(dtype_bytes=invalid)


if __name__=='__main__':unittest.main()
