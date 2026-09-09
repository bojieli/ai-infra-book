import unittest, sys
from pathlib import Path

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

candidate = Path(__file__).resolve().parents[1]
topics.__path__.insert(0, str(candidate / "src/infra_calc/topics"))
from infra_calc.topics import omni_audio_preprocess as module

# Isolated migration tests use identical staged raw files until public installation.
if (candidate / "sources/omni-audio-preprocess/sources.lock.json").is_file():
    module.HERE = candidate / "sources/omni-audio-preprocess"
calculate, reference_fft_work = module.calculate, module.reference_fft_work


class FrontendTests(unittest.TestCase):
    def test_stft_and_mel_closed_form(self):
        r = calculate([16000])
        s = {x["id"]: x for x in r["stages"]}
        self.assertEqual(r["geometry"]["stft_frames_per_audio"], 101)
        self.assertEqual(r["geometry"]["valid_mel_lengths"], [100])
        self.assertEqual(s["mel_projection"]["matrix_flops"], 2 * 128 * 201 * 100)
        self.assertEqual(s["window_multiply"]["scalar_flops"], 101 * 400)
        self.assertEqual(s["rfft_400"]["write_bytes"], 101 * 201 * 8)
        self.assertEqual(s["complex_abs"]["special_ops"]["complex_abs"], 201 * 100)
        self.assertEqual(s["hann_window_per_call"]["special_ops"]["cos"], 401)
        self.assertEqual(s["hann_window_per_call"]["allocated_bytes"], 1604)
        self.assertIsNone(r["summary"]["source_complete_arithmetic"])
        for batch in (1, 2, 3):
            result = calculate([16000] * batch)
            stages = {stage["id"]: stage for stage in result["stages"]}
            time_max, mel_max = (
                stages["per_audio_time_max"],
                stages["per_audio_mel_max"],
            )
            self.assertEqual(time_max["index_output_bytes"], 8 * batch * 128)
            self.assertEqual(mel_max["index_output_bytes"], 8 * batch)
            self.assertEqual(
                time_max["write_bytes"] + mel_max["write_bytes"], 12 * batch * 129
            )
            self.assertEqual(time_max["read_bytes"], 4 * batch * 128 * 100)
            self.assertEqual(mel_max["read_bytes"], 4 * batch * 128)
        self.assertEqual(r["summary"]["source_operand_write_bytes"], 1277400)

    def test_padding_mask_and_effective_config(self):
        r = calculate([479, 800])
        self.assertEqual(r["geometry"]["valid_mel_lengths"], [3, 5])
        self.assertEqual(calculate([479])["geometry"]["valid_mel_lengths"], [2])
        r = calculate([4800000])
        self.assertEqual(r["geometry"]["serialized_max_samples"], 4800000)
        self.assertEqual(r["geometry"]["retained_samples"], [480000])
        self.assertEqual(r["geometry"]["valid_mel_lengths"], [3000])

    def test_input_bridge_and_no_encoder_duplicate(self):
        a, b = calculate([16000]), calculate([16000], encoder_element_bytes=2)
        self.assertEqual(a["summary"]["matrix_flops"], b["summary"]["matrix_flops"])
        self.assertEqual(
            a["summary"]["encoder_input_bytes"], 2 * b["summary"]["encoder_input_bytes"]
        )
        self.assertFalse(a["encoder_bridge"]["encoder_work_included"])
        self.assertEqual(a["geometry"]["encoded_positions"], [13])

    def test_fft_reference_count(self):
        self.assertEqual(
            reference_fft_work(),
            dict(
                real_multiplications=28800, real_additions=24000, complex_products=7200
            ),
        )
        # All butterflies retained including trivial twiddles: radix2 size2 has four products.
        self.assertEqual(
            reference_fft_work(2),
            dict(real_multiplications=16, real_additions=12, complex_products=4),
        )

    def test_invalid(self):
        for kw in [
            dict(sample_lengths=[200]),
            dict(sample_lengths=[True]),
            dict(sample_lengths=[]),
            dict(sampling_rate=48000),
            dict(encoder_element_bytes=3),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kw)
        r = calculate([1, 320])
        self.assertEqual(r["geometry"]["valid_mel_lengths"], [1, 2])

    def test_replay(self):
        r = calculate([321, 481])
        self.assertEqual(r, calculate(**r["scenario"]))


if __name__ == "__main__":
    unittest.main()
