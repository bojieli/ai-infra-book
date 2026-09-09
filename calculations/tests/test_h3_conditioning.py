import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.video_generation import calculate


class H3ConditioningTests(unittest.TestCase):
    def test_actual_schedule_grid_terminal_and_projection_shapes(self):
        r=calculate(steps=2,height=64,width=64,frames=5)
        stage=r['video_generation_stages'][0];c=stage['scheduled_conditioning'];a,b=c['step_rows']
        self.assertEqual(c['scheduler_grid_points'],3)
        self.assertEqual(c['forward_evaluations'],2)
        self.assertEqual(a['distinct_timestep_values'],[0.0])
        self.assertEqual(b['unique_timestep_count'],2)
        self.assertAlmostEqual(b['video_timestep'],1-12*.5/(1+11*.5),places=6)
        self.assertEqual(b['audio_timestep'],.25)
        matrices={x['operator']:x for x in b['matrices']}
        self.assertEqual(matrices['time_linear1']['weight_shape'],[256,5376])
        self.assertEqual(matrices['block_adaln']['weight_shape'],[2688,96768])
        self.assertEqual(matrices['final_adaln']['weight_shape'],[2688,10752])
        per_value=2*(256*5376+5376*2688+50*2688*96768+2688*10752)
        self.assertEqual(c['executed_conditioning_matrix_flops'],3*per_value)
        self.assertEqual(stage['matrix_core_plus_conditioning_flops'],stage['matrix_core_flops_all_evaluations']+3*per_value)

    def test_reference_noise_unique_sets_and_cache_charges(self):
        r=calculate(steps=2,evaluations_per_step=2,reference_video_tokens=3,reference_audio_tokens=2)
        stage=r['video_generation_stages'][0];c=stage['scheduled_conditioning']
        self.assertEqual([x['unique_timestep_count'] for x in c['step_rows']],[3,4])
        cache=c['hypothetical_cache'];self.assertEqual(cache['unique_timestep_count'],5)
        per_value=2*(256*5376+5376*2688+50*2688*96768+2688*10752)
        self.assertEqual(cache['precompute_matrix_flops'],5*per_value)
        self.assertEqual(c['executed_conditioning_matrix_flops'],14*per_value)
        self.assertEqual(cache['matrix_work_saved_after_precompute'],9*per_value)
        self.assertEqual(cache['table_write_bytes'],5*(50*18*5376+2*5376)*2)
        self.assertGreater(cache['row_modulation_reads_sum_bytes'],0)
        self.assertEqual(c['executed_scalar_counts']['rsqrt'],(2*50+1)*stage['attention_tokens']*4)

    def test_existing_core_preserved_and_uncaptured_plan_explicit(self):
        a=calculate(steps=1);b=calculate(steps=2)
        self.assertEqual(b['summary']['matrix_core_flops'],2*a['summary']['matrix_core_flops'])
        self.assertIsNotNone(a['summary']['matrix_core_plus_conditioning_flops'])
        c=calculate(steps=129)
        self.assertEqual(c['video_generation_stages'][0]['scheduled_conditioning']['status'],'unavailable')
        self.assertIsNone(c['summary']['matrix_core_plus_conditioning_flops'])
        self.assertGreater(c['summary']['matrix_core_flops'],0)


if __name__=='__main__':unittest.main()
