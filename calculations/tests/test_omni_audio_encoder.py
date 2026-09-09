"""Independent chunk convolution and segment enumeration, including tails."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics.omni_audio_encoder import calculate, encoded_length


class OmniAudioEncoderTests(unittest.TestCase):
    def test_scenario_replays(self):
        result=calculate([100,1,101],element_bytes=4)
        self.assertEqual(calculate(**result['scenario']),result)
        for width in (True,2.0,3):
            with self.assertRaises(ValueError):calculate(element_bytes=width)

    def test_length_is_chunkwise_not_one_global_stride(self):
        for length in (1,7,8,9,99,100,101,799,800,801,30000):
            expected=0
            for start in range(0,length,100):
                n=min(100,length-start)
                for _ in range(3):
                    # Kernel3 padding1 stride2 output indices.
                    n=len(range(0,n,2))
                expected+=n
            self.assertEqual(encoded_length(length),expected)
        self.assertEqual(encoded_length(800),104)
        self.assertNotEqual(encoded_length(800),(800+7)//8)

    def test_padded_convolution_and_packed_attention_are_separate(self):
        r=calculate([100,1,101])
        self.assertEqual(r['summary']['output_embeddings_per_audio'],[13,1,14])
        self.assertEqual(r['summary']['padded_cnn_positions'],4*13)
        self.assertEqual(r['summary']['valid_encoder_positions'],28)
        self.assertEqual(r['summary']['segmented_bidirectional_pairs'],13**2+1+14**2)
        self.assertEqual(r['summary']['source_unmasked_eager_pairs'],28**2)
        conv=next(op for op in r['audio_encoder_operators'] if op['name']=='conv2d_1')
        self.assertEqual(conv['matrix_flops'],2*4*480*64*50*3*3)
        out=next(op for op in r['audio_encoder_operators'] if op['name']=='conv_out')
        self.assertEqual(out['shape']['input'],[52,7680])
        self.assertEqual(r['summary']['output_embedding_bytes'],28*2048*2)
        short=calculate([1,9])
        self.assertEqual(short['chunk_execution']['padded_mel_width'],9)
        self.assertEqual(short['chunk_execution']['attention_window_positions'],16)

    def test_encoder_parameters_and_eager_difference(self):
        r=calculate([801])
        # Independent official class inventory, including every bias and norm.
        conv=(480*1*9+480)+2*(480*480*9+480)
        per_layer=4*(1280*1280+1280)+(1280*5120+5120)+(5120*1280+1280)+4*1280
        global_weights=7680*1280+2*1280+(1280*1280+1280)+(1280*2048+2048)
        self.assertEqual(r['summary']['parameter_elements'],conv+32*per_layer+global_weights)
        self.assertEqual([x['length'] for x in r['audio_encoder_segments']],[104,1])
        eager=calculate([801],attention_path='source_unmasked_eager')
        self.assertEqual(eager['summary']['matrix_flops']-r['summary']['matrix_flops'],
                         4*32*20*64*(105**2-104**2-1))
        self.assertEqual(r['summary']['persistent_decode_kv_bytes'],0)
        self.assertIsNone(r['summary']['complete_runtime_peak_bytes'])

    def test_conv_group_limit_and_input_validation(self):
        r=calculate([30000,20100])
        self.assertEqual(len(r['audio_encoder_chunks']),501)
        self.assertEqual(r['chunk_execution']['convolution_groups'],2)
        conv=next(op for op in r['audio_encoder_operators'] if op['name']=='conv2d_2')
        self.assertEqual(conv['weight_interface_bytes'],2*conv['parameter_elements']*2)
        for kwargs in [dict(mel_lengths=[]),dict(mel_lengths=[0]),dict(mel_lengths=[True]),
                       dict(mel_lengths=[30001]),dict(element_bytes=1),dict(attention_path='causal')]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)
