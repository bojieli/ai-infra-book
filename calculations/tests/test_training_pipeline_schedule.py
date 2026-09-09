import math
from pathlib import Path
import sys
import unittest

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import training_pipeline_schedule as m
from infra_calc.topics import training_nonmatrix


class PipelineTests(unittest.TestCase):
    def zero_links(self, **kwargs):
        return m.calculate(
            forward_seconds=[1] * 4,
            backward_seconds=[1] * 4,
            activation_transfer_seconds=[0] * 3,
            gradient_transfer_seconds=[0] * 3,
            optimizer_seconds=[0] * 4,
            **kwargs,
        )

    def invariant(self, r):
        M = r["scenario"]["microbatches"]
        events = {e["id"]: e for e in r["events"]}
        self.assertEqual(sum(e["kind"] == "F" for e in events.values()), 4 * M)
        self.assertEqual(sum(e["kind"] == "B" for e in events.values()), 4 * M)
        for event in events.values():
            self.assertTrue(
                all(
                    events[d]["end"] <= event["start"] + 1e-12
                    for d in event["dependencies"]
                )
            )
        resources = {e["resource"] for e in events.values()}
        for resource in resources:
            sequence = sorted(
                (
                    e
                    for e in events.values()
                    if e["resource"] == resource and e["duration"] > 0
                ),
                key=lambda e: e["start"],
            )
            self.assertTrue(
                all(
                    a["end"] <= b["start"] + 1e-12
                    for a, b in zip(sequence, sequence[1:])
                )
            )
        for s in range(4):
            for mb in range(M):
                self.assertLessEqual(
                    events[f"F:{s}:{mb}"]["end"], events[f"B:{s}:{mb}"]["start"] + 1e-12
                )
            self.assertGreaterEqual(
                events[f"U:{s}"]["start"] + 1e-12,
                r["summary"]["gradient_ready_seconds"],
            )
        for timeline in r["activation_timelines"]:
            if timeline["events"]:
                self.assertEqual(timeline["events"][-1]["live_bytes"], 0)
            self.assertTrue(all(x["live_bytes"] >= 0 for x in timeline["events"]))
        for interval in r["activation_intervals"]:
            if interval["kind"] == "declared_saved_reservation":
                _, s, mb = interval["id"].split(":")
                self.assertEqual(interval["start"], events[f"F:{s}:{mb}"]["start"])
                self.assertEqual(interval["end"], events[f"B:{s}:{mb}"]["end"])

    def test_balanced_closed_makespan_and_memory(self):
        for M in [1, 4, 8, 16]:
            a = self.zero_links(microbatches=M, policy="gpipe", tokens=2)
            b = self.zero_links(microbatches=M, policy="1f1b", tokens=2)
            for r in [a, b]:
                self.invariant(r)
                self.assertEqual(r["summary"]["step_makespan_seconds"], 2 * (M + 3))
            for s in range(4):
                size = a["work"]["per_microbatch_stages"][s][
                    "nonlinear_saved_bytes_per_microbatch"
                ]
                saved_a = m._peaks(
                    [
                        i
                        for i in a["activation_intervals"]
                        if i["kind"] == "declared_saved_reservation"
                    ]
                )
                saved_b = m._peaks(
                    [
                        i
                        for i in b["activation_intervals"]
                        if i["kind"] == "declared_saved_reservation"
                    ]
                )
                self.assertEqual(saved_a[s]["peak_declared_reserved_bytes"], M * size)
                self.assertEqual(
                    saved_b[s]["peak_declared_reserved_bytes"], min(M, 4 - s) * size
                )

    def test_m1_same_policies_unequal_and_links(self):
        base = dict(
            microbatches=1,
            tokens=2,
            forward_seconds=[0.01, 0.03, 0.02, 0.04],
            backward_seconds=[0.02, 0.06, 0.04, 0.08],
            link_mode="shared_half_duplex",
        )
        a = m.calculate(policy="gpipe", **base)
        b = m.calculate(policy="1f1b", **base)
        self.assertEqual(a["summary"], b["summary"])
        for r in [a, b]:
            self.invariant(r)

    def test_imbalance_and_shared_links(self):
        for policy in ["gpipe", "1f1b"]:
            for link in ["independent_directional", "shared_half_duplex"]:
                r = m.calculate(
                    microbatches=8,
                    tokens=3,
                    policy=policy,
                    forward_seconds=[0.01, 0.04, 0.01, 0.01],
                    backward_seconds=[0.02, 0.08, 0.02, 0.02],
                    activation_transfer_seconds=[0.03] * 3,
                    gradient_transfer_seconds=[0.03] * 3,
                    link_mode=link,
                )
                self.invariant(r)
                self.assertGreater(
                    r["summary"]["exposed_transfer_makespan_delta_seconds"], 0
                )
                if link == "shared_half_duplex":
                    links = [e for e in r["events"] if e["kind"] in ("A", "G")]
                    self.assertEqual({e["resource"] for e in links}, {"link:shared"})
                    self.assertEqual(len(links), 48)

    def test_real_work_conservation_and_optimizer_once(self):
        for policy in ["save_nonlinear", "recompute_silu"]:
            r = m.calculate(
                microbatches=4, microbatch_size=2, tokens=3, activation_policy=policy
            )
            self.invariant(r)
            original = training_nonmatrix.calculate(
                batch=2, tokens=3, activation_policy=policy
            )
            stages = r["work"]["per_microbatch_stages"]
            for kind in ["forward", "backward"]:
                self.assertEqual(
                    sum(s[kind + "_matrix_flops"] for s in stages),
                    original["training_matrix_original"]["summary"][
                        kind + "_matrix_flops"
                    ],
                )
                self.assertEqual(
                    sum(s[kind + "_scalar_flops"] for s in stages)
                    + sum(
                        s[kind + "_scalar_flops"]
                        for s in r["work"]["once_per_step_rotary_setup"]
                    ),
                    original["summary"][kind + "_scalar_flops"],
                )
            self.assertEqual(
                sum(s["parameters"] for s in stages),
                original["optimizer"]["parameters"],
            )
            self.assertEqual(
                sum(s["nonlinear_saved_bytes_per_microbatch"] for s in stages),
                original["summary"]["nonlinear_saved_at_forward_end_bytes"],
            )
            self.assertEqual(
                sum(s["optimizer_parameter_scalar_flops"] for s in stages),
                original["optimizer"]["parameter_scalar_flops"],
            )
            self.assertEqual(
                sum(s["microbatch_gradient_accumulation_additions"] for s in stages),
                3 * original["optimizer"]["parameters"],
            )
            self.assertEqual(r, m.calculate(**r["scenario"]))
            self.assertIsNone(r["summary"]["complete_training_activation_peak_bytes"])

    def test_invalid_inputs(self):
        for kw in [
            dict(microbatches=0),
            dict(microbatches=True),
            dict(forward_seconds=[1]),
            dict(backward_seconds=[math.inf] * 4),
            dict(additional_saved_bytes=[0.5] * 4),
            dict(link_mode="infinite"),
            dict(policy="async"),
        ]:
            with self.assertRaises(ValueError):
                m.calculate(**kw)


if __name__ == "__main__":
    unittest.main()
