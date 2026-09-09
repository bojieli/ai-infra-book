"""Independent actual-Llama70 single-device storage/capacity oracles."""

import unittest
from copy import deepcopy
from infra_calc.topics import capacity_scan
from infra_calc.models import llama70
from infra_calc.sources import model_config

MODEL = llama70.MODEL
H, V, L, F, Q, KV, D = 8192, 128256, 80, 28672, 64, 8, 128
MATRICES = L * (2 * H * H + 2 * H * KV * D + 3 * H * F)
KEPT = 2 * V * H + (2 * L + 1) * H
PARAMETERS = MATRICES + KEPT


def oracle(bits, group):
    # Enumerate only seven linear matrices per layer with an independent formula.
    dimensions = [
        (Q * D, H),
        (KV * D, H),
        (KV * D, H),
        (H, Q * D),
        (F, H),
        (F, H),
        (H, F),
    ]
    payload = 2 * KEPT + L * sum(n * ((k * bits + 7) // 8) for n, k in dimensions)
    scale = (
        0
        if bits == 16
        else 2 * L * sum(n * ((k + group - 1) // group) for n, k in dimensions)
    )
    return payload, scale


class Llama70CapacityTests(unittest.TestCase):
    def test_exact_model_not_nominal_70b(self):
        r = capacity_scan.calculate(MODEL)
        self.assertEqual(PARAMETERS, 70553706496)
        self.assertEqual(r["summary"]["logical_parameters"], PARAMETERS)
        self.assertEqual(r["summary"]["bf16_weight_bytes"], 2 * PARAMETERS)
        self.assertNotEqual(r["summary"]["logical_parameters"], 70_000_000_000)
        self.assertFalse(
            any(
                ".q_norm." in x["name"] or ".k_norm." in x["name"]
                for x in r["storage_formats"][0]["tensors"]
            )
        )

    def test_formats_with_embeddings_head_norm_excluded(self):
        r = capacity_scan.calculate(MODEL)
        for fmt in r["storage_formats"]:
            payload, scales = oracle(fmt["matrix_bits"], 128)
            self.assertEqual(
                (fmt["payload_bytes"], fmt["scale_bytes"]), (payload, scales)
            )
            for t in fmt["tensors"]:
                if len(t["shape"]) == 1 or t["name"] in (
                    "model.embed_tokens.weight",
                    "lm_head.weight",
                ):
                    self.assertFalse(t["low_bit_eligible"])
                    self.assertEqual(t["payload_bytes"], 2 * t["parameters"])
                    self.assertEqual(t["scale_bytes"], 0)

    def test_nondividing_group_size_tail(self):
        r = capacity_scan.calculate(MODEL, group_size=1000)
        for fmt in r["storage_formats"]:
            self.assertEqual(
                (fmt["payload_bytes"], fmt["scale_bytes"]),
                oracle(fmt["matrix_bits"], 1000),
            )

    def test_kv_and_decimal_capacity_hand_floor(self):
        r = capacity_scan.calculate(MODEL, length=8192)
        kv = 2 * 80 * 8 * 128 * 8192 * 2
        self.assertEqual(kv, 2684354560)
        for row in r["capacity_comparisons"]:
            p, s = oracle(row["matrix_bits"], 128)
            remain = row["capacity_bytes"] - p - s - 2 * 2**30
            self.assertEqual(row["available_for_kv_bytes"], remain)
            self.assertEqual(row["maximum_requests"], max(0, remain // kv))
            self.assertEqual(row["weights_and_workspace_fit"], remain >= 0)

    def test_exact_plus_minus_one_capacity_boundary(self):
        p, s = oracle(4, 128)
        kv = 2684354560
        workspace = 2 * 2**30
        budget = p + s + workspace + 3 * kv
        r = capacity_scan.calculate(MODEL, capacities=[budget - 1, budget, budget + 1])
        self.assertEqual(
            [
                x["maximum_requests"]
                for x in r["capacity_comparisons"]
                if x["matrix_bits"] == 4
            ],
            [2, 3, 3],
        )

    def test_zero_requests_distinguishes_overweight(self):
        p, s = oracle(4, 128)
        base = p + s + 2 * 2**30
        r = capacity_scan.calculate(MODEL, capacities=[base - 1, base])
        rows = [x for x in r["capacity_comparisons"] if x["matrix_bits"] == 4]
        self.assertEqual([x["maximum_requests"] for x in rows], [0, 0])
        self.assertEqual([x["weights_and_workspace_fit"] for x in rows], [False, True])

    def test_model_shape_and_tp_contract(self):
        c = model_config(MODEL)
        bad = deepcopy(c)
        bad["pretraining_tp"] = 2
        with self.assertRaises(ValueError):
            llama70.weights(bad)
        # The existing API has no TP keyword. It must not silently divide a model
        # or interpret a capacity vector as eight aggregated devices.
        with self.assertRaises(TypeError):
            capacity_scan.calculate(MODEL, tp=8)
        rows = capacity_scan.calculate(MODEL, capacities=[24_000_000_000] * 8)[
            "capacity_comparisons"
        ]
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(x["maximum_requests"] == 0 for x in rows))

    def test_context_and_quantization_input_bounds(self):
        for kwargs in [
            dict(length=0),
            dict(length=True),
            dict(length=131073),
            dict(group_size=0),
            dict(scale_bytes=True),
            dict(capacities=[]),
        ]:
            with self.assertRaises(ValueError):
                capacity_scan.calculate(MODEL, **kwargs)
        self.assertEqual(
            capacity_scan.calculate(MODEL, length=131072)["summary"][
                "bf16_kv_bytes_per_request"
            ],
            42949672960,
        )
