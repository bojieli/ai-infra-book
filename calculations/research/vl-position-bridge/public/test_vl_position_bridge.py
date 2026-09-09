import unittest
import sys
from pathlib import Path

# Works after migration to calculations/tests and within the research delivery.
for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc").is_dir():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc.topics.vl_position_bridge import calculate, attach
from infra_calc.topics.vl_request import calculate as request_calculate


class Check(unittest.TestCase):
    def test_rectangular_image_coordinates(self):
        r = calculate(
            [
                dict(kind="text", tokens=2),
                dict(kind="image", preprocessed_height=64, preprocessed_width=96),
                dict(kind="text", tokens=1),
            ],
            3,
        )
        self.assertEqual(
            r["positions"],
            [
                [0, 1, 2, 2, 2, 2, 2, 2, 5],
                [0, 1, 2, 2, 2, 3, 3, 3, 5],
                [0, 1, 2, 3, 4, 2, 3, 4, 5],
            ],
        )
        self.assertEqual(r["summary"]["rope_delta"], -3)
        self.assertEqual(r["summary"]["decode_rotary_positions"], [6, 7])
        self.assertEqual(r["summary"]["final_kv_positions"], 11)

    def test_book_geometry(self):
        segments = []
        for _ in range(4):
            segments.extend(
                [
                    dict(kind="text", tokens=100),
                    dict(kind="image", preprocessed_height=640, preprocessed_width=640),
                ]
            )
        s = calculate(segments, 128)["summary"]
        self.assertEqual(
            (
                s["prompt_positions"],
                s["image_positions"],
                s["rope_delta"],
                s["next_rotary_position"],
            ),
            (2000, 1600, -1520, 480),
        )
        self.assertEqual(s["final_kv_positions"], 2127)

    def test_text_only(self):
        s = calculate([dict(kind="text", tokens=17)], 2)["summary"]
        self.assertEqual(s["rope_delta"], 0)
        self.assertEqual(s["decode_rotary_positions"], [17])

    def test_invalid(self):
        for seg in [
            [],
            [dict(kind="text", tokens=True)],
            [dict(kind="image", preprocessed_height=33, preprocessed_width=64)],
            [dict(kind="text", tokens=1), dict(kind="text", tokens=2)],
        ]:
            with self.assertRaises(ValueError):
                calculate(seg)

    def test_count_independent_coordinates(self):
        for h in range(1, 5):
            for w in range(1, 5):
                r = calculate(
                    [
                        dict(kind="text", tokens=3),
                        dict(
                            kind="image",
                            preprocessed_height=h * 32,
                            preprocessed_width=w * 32,
                        ),
                    ]
                )
                self.assertEqual(r["summary"]["rope_delta"], max(h, w) - h * w)
                for j in range(h * w):
                    self.assertEqual(
                        [a[j + 3] for a in r["positions"]], [3, 3 + j // w, 3 + j % w]
                    )


class Integration(unittest.TestCase):
    def test_cache_hit_invariant_and_no_double_count(self):
        segments = [
            dict(kind="text", tokens=13),
            dict(kind="image", preprocessed_height=256, preprocessed_width=384),
        ]
        previous = None
        for hit in (False, True):
            request = request_calculate(
                images=[dict(height=256, width=384, cache_hit=hit)],
                text_tokens=13,
                output_tokens=4,
            )
            joined = attach(request, segments)
            self.assertEqual(joined["summary"], request["summary"])
            self.assertNotIn("position_bridge", request)
            if previous:
                self.assertEqual(joined["position_bridge"], previous)
            previous = joined["position_bridge"]

    def test_direct_decode_setup_and_text_fallback(self):
        result = calculate(
            [
                dict(kind="text", tokens=13),
                dict(kind="image", preprocessed_height=256, preprocessed_width=384),
            ],
            4,
        )
        steps = {row["name"]: row for row in result["source_steps"]}
        self.assertEqual(
            steps["direct_model_decode_arange"]["materialized_output_bytes"], 24
        )
        self.assertEqual(
            steps["direct_model_decode_delta_repeat_interleave"][
                "materialized_output_bytes"
            ],
            24,
        )
        text = calculate([dict(kind="text", tokens=13)], 4)
        self.assertEqual(
            [row["name"] for row in text["source_steps"]],
            ["language_model_default_arange_add"],
        )
        self.assertFalse(text["summary"]["rope_delta_cached"])
        self.assertEqual(text["summary"]["rope_delta_bytes"], 0)
        self.assertEqual(text["source_steps"][0]["integer_additions"], 16)

    def test_uniform_default_four_images(self):
        request = request_calculate()
        segments = []
        for _ in range(4):
            segments.extend(
                [
                    dict(kind="text", tokens=100),
                    dict(kind="image", preprocessed_height=640, preprocessed_width=640),
                ]
            )
        joined = attach(request, segments)
        self.assertEqual(joined["summary"], request["summary"])
        self.assertEqual(joined["position_bridge"]["summary"]["prompt_positions"], 2000)
        self.assertEqual(joined["position_bridge"]["summary"]["rope_delta"], -1520)
        self.assertEqual(
            joined["position_bridge"]["summary"]["final_kv_positions"], 2127
        )

    def test_order_mismatch_rejected(self):
        request = request_calculate(
            images=[dict(height=256, width=384)], text_tokens=13
        )
        with self.assertRaises(ValueError):
            attach(
                request,
                [
                    dict(kind="text", tokens=13),
                    dict(kind="image", preprocessed_height=384, preprocessed_width=256),
                ],
            )

    def test_text_count_mismatch_rejected(self):
        request = request_calculate(
            images=[dict(height=256, width=384)], text_tokens=13
        )
        with self.assertRaises(ValueError):
            attach(
                request,
                [
                    dict(kind="text", tokens=12),
                    dict(kind="image", preprocessed_height=256, preprocessed_width=384),
                ],
            )


if __name__ == "__main__":
    unittest.main()
