"""Independent Omni geometry, packed segmentation and delivery invariants."""
import unittest
from infra_calc.topics.omni_vision_encoding import calculate


class OmniVisionEncodingTests(unittest.TestCase):
    def test_static_geometry_and_full_parameter_inventory(self):
        r=calculate();s=r['summary'];h=1152;f=4304;o=2048;p=1600;m=400;w=4*h
        self.assertEqual(s['matrix_flops'],2*p*1536*h+27*(8*p*h*h+4*p*h*f+4*p*p*h)+4*(2*m*w*w+2*m*w*o))
        params=(1536*h+h+2304*h+27*(4*h*h+2*h*f+(3*h+h+f+h)+4*h)+
                (w*w+w+w*o+o+2*h)+3*(w*w+w+w*o+o+2*w))
        self.assertEqual(s['logical_vision_parameters'],params)
        self.assertEqual(s['complete_encoder_feature_bytes'],6553600)
        self.assertEqual(r['official_default']['value'],2304)
        self.assertIn('__init__ default',r['official_default']['origin'])
        self.assertEqual(calculate(**r['scenario']),r)

    def test_mixed_video_grids_no_cross_frame_square(self):
        r=calculate([[1,4,6],[3,2,8]],seconds_per_grid=[None,'1/2'])
        expected=24**2+3*16**2
        self.assertEqual(r['summary']['executed_bidirectional_pairs'],expected)
        self.assertNotEqual(expected,(24+3*16)**2)
        self.assertEqual(r['omni_vision_items'][1]['temporal_position_ids'],[0,6,13])
        self.assertEqual(r['summary']['delivered_visual_positions'],(24+48)//4)
        matrix=sum(x['matrix_flops'] for x in r['omni_vision_matrices'] if x['name'].endswith(('_qk','_pv')))
        self.assertEqual(matrix,4*27*1152*expected)

    def test_cache_hits_skip_encoder_but_keep_all_feature_delivery(self):
        grids=[[1,4,4],[2,2,4]]
        a=calculate(grids);b=calculate(grids,[True,False]);c=calculate(grids,[True,True])
        self.assertEqual(a['summary']['complete_encoder_feature_bytes'],b['summary']['complete_encoder_feature_bytes'])
        self.assertEqual(a['summary']['logical_vision_parameters'],c['summary']['logical_vision_parameters'])
        self.assertEqual(c['summary']['matrix_flops'],0)
        self.assertEqual(c['summary']['scalar_flops'],0)
        self.assertEqual(c['summary']['interface_read_bytes'],0)
        self.assertEqual(b['summary']['executed_patches'],16)
        self.assertEqual(c['deepstack_delivery']['injection_adds'],3*8*2048)
        self.assertEqual(c['deepstack_delivery']['injection_gather_clone_add_scatter_interface_bytes'],9*3*8*2048*2)

    def test_interpolation_dtype_temporal_reuse_and_bad_inputs(self):
        a=calculate([[3,4,4]],dtype='bf16');b=calculate([[3,4,4]],dtype='fp32')
        row=next(x for x in a['omni_vision_scalars'] if x['name']=='position_interpolate')
        self.assertEqual(row['interface_read_bytes'],(4*16*1152+4*16)*2)
        self.assertEqual(row['scalar_flops'],7*16*1152)
        row4=next(x for x in b['omni_vision_scalars'] if x['name']=='position_interpolate')
        self.assertEqual(row4['interface_read_bytes'],2*row['interface_read_bytes'])
        rope2=next(x for x in a['omni_vision_scalars'] if x['name']=='block_rope_qk')
        rope4=next(x for x in b['omni_vision_scalars'] if x['name']=='block_rope_qk')
        self.assertEqual(rope2['interface_read_bytes'],rope4['interface_read_bytes'])
        for kwargs in [dict(grid_thw=[]),dict(grid_thw=[[1,3,4]]),dict(grid_thw=[[True,4,4]]),
                       dict(cache_hits=[1]),dict(seconds_per_grid=[0]),dict(dtype='fp8')]:
            with self.assertRaises(ValueError):calculate(**kwargs)
