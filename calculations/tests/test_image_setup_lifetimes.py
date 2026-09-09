import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.image_generation import calculate
from infra_calc.topics.image_setup_lifetimes import timestep_temporary_events, setup_boundary_graph


class ImageSetupLifetimeTests(unittest.TestCase):
    def test_timestep_helper_eager_peak_and_same_dtype_alias(self):
        for batch in (1,3):
            for dtype in ('bf16','fp16','fp32'):
                rows=timestep_temporary_events(batch,dtype); live={}; peak=0
                for row in rows:
                    if row['action']=='allocate':
                        self.assertNotIn(row['object'],live)
                        live[row['object']]=row['bytes']
                    else: live.pop(row['object'])
                    peak=max(peak,sum(live.values()))
                self.assertEqual(live,{})
                # At torch.cat's RHS: the named exponent persists, scaled emb
                # plus sin and cos operands coexist with the 2-width output.
                self.assertEqual(peak,128*4 + 5*batch*128*4)
                allocated={r['object']:r for r in rows if r['action']=='allocate'}
                self.assertEqual('setup_timestep_input_upcast' in allocated,dtype!='fp32')
                self.assertEqual('setup_timestep_model_features' in allocated,dtype!='fp32')
                if dtype!='fp32':
                    self.assertEqual(allocated['setup_timestep_model_features']['bytes'],batch*256*2)
        with self.assertRaises(ValueError): timestep_temporary_events(True,'bf16')

    def test_augmented_graph_preserves_original_objects_and_cfg_overlap(self):
        result=calculate(height=32,width=32,text_tokens=8,negative_text_tokens=2,steps=2,output_type='latent')
        rows=result['image_setup_boundary_memory_events']
        original=result['image_boundary_memory_events']
        projected=[(r['action'],r['object'],r['bytes'],r['phase']) for r in rows if r['scope']=='original_boundary']
        self.assertEqual(projected,[(r['action'],r['object'],r['bytes'],r['phase']) for r in original])
        negative=next(r for r in rows if r['phase']=='step_0_negative_timestep_setup')
        self.assertIn('prediction',negative['live_objects'])
        self.assertNotIn('negative_prediction',negative['live_objects'])
        allocations=[r for r in rows if r['action']=='allocate' and r['object']=='setup_timestep_arange']
        self.assertEqual(len(allocations),4)
        self.assertEqual(result['image_setup_boundary_memory_summary']['final_live_objects'],['latent'])
        self.assertIsNone(result['image_setup_boundary_memory_summary']['actual_allocator_peak_bytes'])
        self.assertFalse(any('setup_' in obj for obj in rows[-1]['live_objects']))

    def test_peak_is_overlap_max_not_sum_of_unrelated_phase_peaks(self):
        # Deliberately small baseline permits an independent exact overlap result.
        baseline=[dict(action='allocate',object='latent',bytes=20,phase='noise_init',live_bytes_after=20),
                  dict(action='allocate',object='prediction',bytes=20,phase='step_0_conditional',live_bytes_after=40)]
        result=dict(scenario=dict(batch=1,dtype='bf16'),summary=dict(transformer_invocations=1))
        graph=setup_boundary_graph(result,baseline)
        self.assertEqual(graph['declared_expanded_graph_peak_bytes'],20+3072)
        self.assertEqual(graph['peak_increment_bytes'],20+3072-40)
        self.assertNotEqual(graph['declared_expanded_graph_peak_bytes'],40+3072)
        live={}
        for row in graph['events']:
            if row['action']=='allocate': live[row['object']]=row['bytes']
            else: live.pop(row['object'])
            self.assertEqual(sum(live.values()),row['live_bytes_after'])
            self.assertEqual(list(live),row['live_objects'])


if __name__=='__main__': unittest.main()
