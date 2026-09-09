import unittest
from fish_wave_export import calculate


class WaveExport(unittest.TestCase):
    def test_merged_once_and_exact_sample_clock(self):
        r = calculate([21, 22])
        s = r["summary"]
        self.assertEqual(s["codec_decode_calls"], 1)
        self.assertEqual(s["output_samples"], 43 * 2048)
        self.assertEqual(s["code_device_to_host_bytes"], 2 * 43 * 10 * 8)
        self.assertEqual(s["waveform_device_to_host_bytes"], 43 * 2048 * 2)
        self.assertEqual(
            s["standalone_dac_cli_wave_device_to_host_bytes"], 43 * 2048 * 4
        )
        self.assertEqual(r["codec_operations"], calculate([43])["codec_operations"])

    def test_host_cast_not_device_fp32_transfer(self):
        b = calculate([1])
        f = calculate([1], waveform_dtype="fp32")
        self.assertEqual(b["wrapper_stages"][-1]["host_cast_write_bytes"], 2048 * 4)
        self.assertEqual(f["wrapper_stages"][-1]["host_cast_write_bytes"], 0)
        self.assertEqual(f["summary"]["waveform_device_to_host_bytes"], 2048 * 4)
        self.assertIsNone(f["summary"]["first_audio_latency_seconds"])
        self.assertIsNone(f["summary"]["output_file_bytes"])

    def test_code_width_and_hold(self):
        r = calculate([2, 3], code_element_bytes=4)
        self.assertEqual(
            r["wrapper_stages"][1]["held_code_list_device_bytes"], 5 * 10 * 4
        )
        self.assertEqual(
            r["wrapper_stages"][2]["code_list_plus_merged_device_bytes"], 2 * 5 * 10 * 4
        )
        self.assertEqual(r["summary"]["code_device_to_host_bytes"], 2 * 5 * 10 * 4)

    def test_invalid(self):
        for kwargs in [
            dict(chunk_frames=[]),
            dict(chunk_frames=[True]),
            dict(code_element_bytes=True),
            dict(code_element_bytes=3),
            dict(chunk_frames=[32769]),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kwargs)


if __name__ == "__main__":
    unittest.main()
