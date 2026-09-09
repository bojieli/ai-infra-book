"""Hand timing with an out-of-order chunk and fixed versus shifted playback."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.audio_timing import calculate


class AudioTimingTests(unittest.TestCase):
    def small(self,**kw):
        return calculate(frame_ns=10,model_ns=[2]*3,network_delay_ns=[0,20,0],send_ns=0,
                         sample_rate=100000000,jitter_buffer_ns=0,**kw)

    def test_reorder_stall_is_not_counted_twice(self):
        r=self.small(); s=r['summary']
        self.assertEqual([row['arrival_ns'] for row in r['audio_chunks']],[12,42,32])
        self.assertEqual([row['playback_start_ns'] for row in r['audio_chunks']],[12,42,52])
        self.assertEqual(s['deadline_misses'],1)
        self.assertEqual(s['total_playback_stall_ns'],20)
        self.assertEqual(s['baseline_playback_finish_ns']-s['first_playback_from_time_zero_ns'],s['source_audio_duration_ns']+s['total_playback_stall_ns'])
        self.assertEqual(s['baseline_ready_queue_peak_bytes'],2)

    def test_mute_response_and_audible_tail(self):
        s=self.small(interrupt_ns=45,control_delay_ns=3,device_quantum_ns=10)['summary']
        self.assertEqual((s['mute_effective_ns'],s['interrupt_to_mute_ns'],s['audible_after_interrupt_ns']),(50,5,5))
        gap=self.small(interrupt_ns=25,control_delay_ns=3,device_quantum_ns=10)['summary']
        self.assertEqual(gap['audible_after_interrupt_ns'],0)
        self.assertEqual(gap['interrupt_to_mute_ns'],5)
        self.assertIsNone(s['cancelled_gpu_work'])

    def test_buffer_tradeoff_and_invalid_inputs(self):
        base=calculate()['summary']; large=calculate(jitter_buffer_ns=60000000)['summary']
        self.assertGreater(large['first_playback_from_time_zero_ns'],base['first_playback_from_time_zero_ns'])
        self.assertEqual(large['total_playback_stall_ns'],0)
        self.assertGreater(base['total_playback_stall_ns'],0)
        for kw in [dict(model_ns=[]),dict(frame_ns=1),dict(network_delay_ns=[1]),dict(send_ns=-1)]:
            with self.assertRaises(ValueError): calculate(**kw)
