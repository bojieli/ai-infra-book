import unittest
from fractions import Fraction as F
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    if (parent / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(parent / "src"))
        break
else:
    raise RuntimeError("Cannot locate public infra_calc source tree")

import infra_calc.topics

candidate_topics = Path(__file__).resolve().parents[1] / "src/infra_calc/topics"
if candidate_topics.is_dir():
    infra_calc.topics.__path__.insert(0, str(candidate_topics))

from infra_calc.topics.training_input_supply import calculate


class SupplyTests(unittest.TestCase):
    def validate(self, r):
        events = {e["id"]: e for e in r["events"]}
        for e in events.values():
            a, b = F(e["start_exact"]), F(e["end_exact"])
            self.assertEqual(b - a, F(e["service_exact"]))
            for d in e["deps"]:
                self.assertLessEqual(F(events[d]["end_exact"]), a)
        for resource in {e["resource"] for e in events.values()}:
            jobs = sorted(
                (F(e["start_exact"]), F(e["end_exact"]))
                for e in events.values()
                if e["resource"] == resource and F(e["end_exact"]) > F(e["start_exact"])
            )
            for first, second in zip(jobs, jobs[1:]):
                self.assertLessEqual(first[1], second[0])
        for pool, slots in [
            ("host", r["scenario"]["host_slots"]),
            ("device", r["scenario"]["device_slots"]),
            ("snapshot", r["scenario"]["snapshot_slots"]),
        ]:
            rows = r["lifetimes"][pool]
            times = {F(x[k]) for x in rows for k in ("start_exact", "end_exact")}
            peak = 0
            for t in times:
                active = [
                    x for x in rows if F(x["start_exact"]) <= t < F(x["end_exact"])
                ]
                self.assertLessEqual(len(active), slots)
                peak = max(peak, sum(x["bytes"] for x in active))
            self.assertEqual(peak, r["buffers"][pool]["peak_reserved_bytes"])
        ids = [i for p in r["packs"] for i in p["samples"]]
        self.assertEqual(ids, list(range(len(r["scenario"]["samples"]))))
        self.assertEqual(
            r["summary"]["valid_tokens"] + r["summary"]["padding_tokens"],
            r["summary"]["packs"] * r["scenario"]["pack_tokens"],
        )
        self.assertGreaterEqual(F(r["summary"]["device_wait_exact"]), 0)

    def test_graph_and_lifetimes(self):
        for shared in [True, False]:
            for hs, ds in [(1, 1), (2, 1), (1, 3), (3, 2)]:
                for every in [0, 1, 2, 3]:
                    self.validate(
                        calculate(
                            host_slots=hs,
                            device_slots=ds,
                            checkpoint_every=every,
                            shared_storage=shared,
                        )
                    )

    def test_storage_starvation(self):
        samples = [
            dict(tokens=512, stored_bytes=8192, cpu_ns=100000) for _ in range(12)
        ]
        args = dict(
            samples=samples,
            host_slots=1,
            device_slots=1,
            checkpoint_every=2,
            snapshot_slots=8,
        )
        shared = calculate(**args)
        split = calculate(**args, shared_storage=False)
        none = calculate(**{**args, "checkpoint_every": 0})
        self.assertGreater(
            F(shared["summary"]["device_wait_exact"]),
            F(split["summary"]["device_wait_exact"]),
        )
        self.assertGreater(
            F(shared["summary"]["training_end_exact"]),
            F(none["summary"]["training_end_exact"]),
        )
        for r in [shared, split, none]:
            self.validate(r)

    def test_cpu_bottleneck_and_bytes(self):
        fast = calculate(checkpoint_every=0)
        samples = [{**s, "cpu_ns": 100000000} for s in fast["scenario"]["samples"]]
        slow = calculate(samples=samples, checkpoint_every=0)
        self.assertGreater(
            F(slow["summary"]["device_wait_exact"]),
            F(fast["summary"]["device_wait_exact"]),
        )
        self.assertEqual(
            slow["summary"]["h2d_bytes"], slow["summary"]["packs"] * 512 * 21
        )
        self.assertEqual(slow["summary"]["checkpoint_bytes_each"], 14 * 8190735360)
        self.validate(slow)

    def test_replay_and_zero_duration(self):
        r = calculate(packing_ns=0, consume_ns=0, snapshot_ns=0)
        self.assertEqual(r, calculate(**r["scenario"]))
        self.validate(r)

    def test_reject(self):
        for kw in [
            dict(host_slots=0),
            dict(shared_storage=1),
            dict(samples=[]),
            dict(samples=[dict(tokens=513, stored_bytes=1, cpu_ns=0)]),
            dict(consume_ns=-1),
        ]:
            with self.assertRaises(ValueError):
                calculate(**kw)


if __name__ == "__main__":
    unittest.main()
