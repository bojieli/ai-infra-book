import sys
import unittest
from fractions import Fraction
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.image_execution import reference_operation
from infra_calc.topics.image_generation import calculate


class ImageExecutionTests(unittest.TestCase):
    def test_reference_scalar_counts_and_special_units(self):
        # Two independent 3-element vectors: explicit mean, centered variance,
        # reciprocal sqrt and normalization with no learned affine.
        per_vector = (3-1)+1 + 3 + 3 + (3-1)+1 + 1 + 3
        row = reference_operation('test','layernorm',vectors=2,width=3)
        self.assertEqual(row['ordinary_arithmetic_ops'],2*per_vector)
        self.assertEqual(row['special_calls'],{'rsqrt':2})
        # Causal rows of lengths 1,2,3: scale, shift, sum, divide separately.
        row = reference_operation('test','softmax',elements=6,rows=3)
        self.assertEqual(row['ordinary_arithmetic_ops'],sum(3*n+(n-1) for n in [1,2,3]))
        self.assertEqual(row['comparisons'],sum(n-1 for n in [1,2,3]))
        self.assertEqual(row['special_calls'],{'exp':6})
        self.assertEqual(reference_operation('test','silu',elements=5)['special_calls'],{'exp':5})

    def test_declared_lifetimes_by_independent_interval_intersection(self):
        result = calculate(height=32,width=32,text_tokens=8,negative_text_tokens=2,steps=2)
        events = result['image_boundary_memory_events']; intervals=[]; starts={}
        for e in events:
            if e['action']=='allocate':
                self.assertNotIn(e['object'],starts)
                starts[e['object']] = (e['event'],e['bytes'])
            else:
                at,size = starts.pop(e['object']); intervals.append((at,e['event'],size))
        intervals += [(at,len(events),size) for at,size in starts.values()]
        point_totals = [sum(size for start,end,size in intervals if start<=point<end) for point in range(len(events))]
        self.assertEqual(max(point_totals),result['summary']['declared_boundary_graph_peak_bytes'])
        self.assertEqual(point_totals,[e['live_bytes_after'] for e in events])
        negative = next(e for e in events if e['phase']=='step_0_negative')
        self.assertIn('prediction',negative['live_objects'])
        self.assertIn('negative_prediction',negative['live_objects'])
        vae_output = next(e for e in events if e['phase']=='vae_output')
        self.assertEqual(sum(name.startswith('vae_cache_') for name in vae_output['live_objects']),30)
        self.assertEqual(result['summary']['declared_boundary_graph_final_live_objects'],['decoded_rgb'])
        self.assertIsNone(result['summary']['full_runtime_peak_bytes'])

    def test_stage_work_repetition_and_precision_matched_service(self):
        service=dict(input_dtype='bf16',accumulator_dtype='fp32',sparsity='dense',flops_per_second=10**12)
        one=calculate(height=32,width=32,text_tokens=8,steps=1,effective_matrix_service=service)
        three=calculate(height=32,width=32,text_tokens=8,steps=3,effective_matrix_service=service)
        for stage in ['text_conditional','text_unconditional','vae']:
            a=sum(r['ordinary_arithmetic_ops'] for r in one['image_reference_operations'] if r['stage']==stage)
            b=sum(r['ordinary_arithmetic_ops'] for r in three['image_reference_operations'] if r['stage']==stage)
            self.assertEqual(a,b)
        for stage in ['dit_conditional','dit_unconditional','cfg','scheduler']:
            a=sum(r['ordinary_arithmetic_ops'] for r in one['image_reference_operations'] if r['stage']==stage)
            b=sum(r['ordinary_arithmetic_ops'] for r in three['image_reference_operations'] if r['stage']==stage)
            self.assertEqual(3*a,b)
        self.assertFalse(any(r['operation']=='multiply' for r in one['image_reference_operations'] if r['stage']=='latent_denormalize'))
        bound=one['image_matrix_service_bound']
        self.assertEqual(Fraction(bound['declared_serial_matrix_lower_exact_seconds']),
                         Fraction(one['summary']['all_stage_nonpadding_matrix_flops'],10**12))
        self.assertIsNone(bound['complete_request_seconds'])
        with self.assertRaises(ValueError):
            calculate(effective_matrix_service=dict(service,sparsity='2:4'))
        with self.assertRaises(ValueError):
            calculate(effective_matrix_service=dict(service,input_dtype='fp16'))


if __name__=='__main__':unittest.main()
