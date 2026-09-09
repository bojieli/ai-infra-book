"""A checkpoint discrepancy must not silently become a runtime adapter."""
import unittest
from infra_calc.sources import model_config
from infra_calc.topics.k3_checkpoint import expected_unpacked_shapes,runtime_compatibility

class K3RuntimeContractTests(unittest.TestCase):
    def test_independent_parameter_geometry_rules_out_128_heads(self):
        c=model_config('kimi-k3')['text_config'];shapes=expected_unpacked_shapes(c)
        layers=c['linear_attn_config']['kda_layers'];self.assertEqual(len(layers),69)
        bad=[]
        for layer in layers:
            prefix=f'language_model.model.layers.{layer-1}.self_attn.'
            self.assertEqual(shapes[prefix+'A_log'],[96])
            self.assertEqual(shapes[prefix+'q_proj.weight'][0],96*128)
            self.assertEqual(shapes[prefix+'dt_bias'],[96*128])
            self.assertEqual(shapes[prefix+'b_proj.weight'][0],96)
            bad.append(dict(tensor=prefix+'A_log',config_shape=[96],checkpoint_shape=[128]))
        audit=runtime_compatibility(c,bad)
        self.assertFalse(audit['direct_load_supported_by_shapes'])
        self.assertFalse(audit['reference_gate_shape_supported'])
        self.assertFalse(audit['checkpoint_execution_verified'])
        self.assertEqual(set(audit['affected_layers']),{l-1 for l in layers})
        self.assertIn('explicitly translate',audit['runtime_paths']['state_layout'])

    def test_shape_agreement_alone_does_not_verify_execution(self):
        audit=runtime_compatibility(model_config('kimi-k3')['text_config'],[])
        self.assertTrue(audit['direct_load_supported_by_shapes'])
        self.assertFalse(audit['checkpoint_execution_verified'])

if __name__=='__main__':unittest.main()
