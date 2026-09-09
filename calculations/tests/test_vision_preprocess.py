import json
from pathlib import Path
import unittest
import sys

HERE = Path(__file__).resolve().parent
for ancestor in HERE.parents:
    if (ancestor / "src/infra_calc/models").is_dir():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

candidate = HERE.parent
if (candidate / "src/infra_calc/topics/vision_preprocess.py").exists():
    topics.__path__.insert(0, str(candidate / "src/infra_calc/topics"))
from infra_calc.topics import vision_preprocess as module, vision_encoding

if (candidate / "configs/vision-preprocess.lock.json").exists():
    module.PROJECT = candidate
calculate, axis_weights = module.calculate, module.axis_weights


class PreprocessTests(unittest.TestCase):
    def test_identity_bytes_and_normalization(self):
        x = calculate(640, 640)
        s = x["summary"]
        st = {r["stage"]: r for r in x["stages"]}
        self.assertEqual(s["image_grid_thw"], [1, 40, 40])
        self.assertEqual(s["pixel_values_shape"], [1600, 1536])
        self.assertEqual(s["pixel_values_bytes"], 9830400)
        self.assertEqual(s["encoder_input_bytes"], 4915200)
        self.assertFalse(x["resize_axes"])
        self.assertEqual(st["HWC_to_CHW_contiguous"]["semantic_write_bytes"], 1228800)
        self.assertEqual(
            st["normalize_subtract"]["operations"]["fp32_subtract"], 1228800
        )
        self.assertEqual(
            st["normalize_divide_in_place"]["operations"]["fp32_divide"], 1228800
        )
        self.assertEqual(
            st["patch_flatten_materialization"]["unique_input_bytes"], 4915200
        )
        self.assertEqual(s["preprocessing_matrix_flops"], 0)

    def test_resize_integer_pass_counts(self):
        x = calculate(64, 256)
        st = {r["stage"]: r for r in x["stages"]}
        for axis, multiplicity in [("width", 3 * 64), ("height", 3 * 512)]:
            info = next(a for a in x["resize_axes"] if a["axis"] == axis)
            row = st[axis + "_uint8_separable_convolution"]
            mac = multiplicity * info["tap_count"]
            self.assertEqual(row["operations"]["int32_multiply"], mac)
            self.assertEqual(row["operations"]["int32_add"], mac)
            self.assertEqual(row["semantic_read_bytes"], 3 * mac)
            self.assertEqual(row["accumulator_dtype"], "int32")
            self.assertEqual(
                info["coefficient_buffer_allocated_bytes"],
                info["output_size"] * info["max_taps"] * 8,
            )
        # Source bounds at exact upscale2: edge has3 taps, inner has4 (including zero weights where present).
        a = axis_weights(4, 8)
        self.assertEqual([r["count"] for r in a["ranges"]], [2, 3, 3, 4, 4, 3, 3, 2])

    def test_area_branches_and_aspect_limit(self):
        self.assertEqual(calculate(32, 32)["summary"]["image_grid_thw"], [1, 16, 16])
        self.assertEqual(
            calculate(4608, 4608)["summary"]["image_grid_thw"], [1, 256, 256]
        )
        with self.assertRaises(ValueError):
            calculate(1, 201)
        for kw in [
            dict(height=True),
            dict(width=0),
            dict(encoder_dtype="fp16"),
            dict(normalization_cache="unknown"),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kw)

    def test_cache_and_boundary_cast_not_encoder_matrix(self):
        cold = calculate()
        warm = calculate(normalization_cache="warm")
        f = calculate(encoder_dtype="fp32")
        self.assertEqual(len(cold["stages"]) - len(warm["stages"]), 1)
        self.assertEqual(
            cold["summary"]["pixel_values_bytes"], f["summary"]["pixel_values_bytes"]
        )
        self.assertEqual(
            f["summary"]["encoder_input_bytes"],
            2 * cold["summary"]["encoder_input_bytes"],
        )
        self.assertEqual(cold, calculate(**cold["scenario"]))

    def test_existing_vision_input_contract_and_no_matrix_duplication(self):
        for h, w in [(640, 640), (257, 385)]:
            preprocessing = calculate(h, w)["summary"]
            vision = vision_encoding.calculate(
                preprocessing["resized_height"],
                preprocessing["resized_width"],
                1,
                0,
                "bf16",
            )["summary"]
            self.assertEqual(
                preprocessing["pixel_values_shape"], vision["patch_input_shape"]
            )
            self.assertEqual(
                preprocessing["encoder_input_bytes"],
                vision["patch_input_bytes_per_image"],
            )
            self.assertGreater(vision["matrix_flops_per_image"], 0)
            self.assertEqual(preprocessing["preprocessing_matrix_flops"], 0)


if __name__ == "__main__":
    unittest.main()
