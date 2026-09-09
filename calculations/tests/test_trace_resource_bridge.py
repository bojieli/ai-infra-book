import sys
import unittest
from pathlib import Path

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc import topics

topics.__path__.insert(
    0, str(Path(__file__).resolve().parents[1] / "src/infra_calc/topics")
)
from infra_calc.topics import trace_resource_bridge as m
from infra_calc.models import qwen3
from infra_calc.schema import Scenario

candidate = Path(__file__).resolve().parents[1] / "sources/trace-resource-bridge"
if candidate.is_dir():
    m.SOURCE_ROOT = candidate


class TraceTests(unittest.TestCase):
    def test_recorded_fields_and_unknowns(self):
        r = m.calculate()
        self.assertEqual(
            (
                r["summary"]["recorded_application_calls"],
                r["summary"]["recorded_input_tokens"],
                r["summary"]["recorded_cached_tokens"],
                r["summary"]["recorded_returned_ids"],
            ),
            (4, 753, 489, 79),
        )
        self.assertIsNone(r["summary"]["conditional_complete_logical_totals"])
        self.assertIsNone(r["summary"]["observed_model_forward_calls"])
        self.assertIsNone(r["summary"]["tool_wait_sum_seconds"])
        self.assertEqual(
            [c["mapping"]["new_tokens"] for c in r["calls"]], [116, 56, 53, 39]
        )
        self.assertEqual(r, m.calculate(**r["scenario"]))

    def test_conditional_every_forward_independent_sum(self):
        r = m.calculate("returned_ids_serial_policy")
        self.assertEqual(r["summary"]["conditional_serial_forward_calls"], 79)
        for call in r["calls"]:
            mapping = call["mapping"]
            s, p, g = [
                mapping[k] for k in ("prefix_tokens", "new_tokens", "sampled_steps")
            ]
            ledgers = [
                qwen3.calculate(
                    "qwen3-8b",
                    Scenario(batch=1, tokens=p, history=s, output_head="last"),
                )
            ]
            ledgers += [
                qwen3.calculate(
                    "qwen3-8b",
                    Scenario(batch=1, tokens=1, history=s + p + i, output_head="last"),
                )
                for i in range(g - 1)
            ]
            resource = call["resources"]
            self.assertEqual(
                resource["complete_logical_totals"]["matrix_flops"],
                sum(x["summary"]["matrix_flops"] for x in ledgers),
            )
            for key, value in resource["complete_logical_totals"][
                "known_interfaces"
            ].items():
                self.assertEqual(value, sum(x["summary"][key] for x in ledgers))
            self.assertEqual(
                resource["final_state_bytes"],
                ledgers[-1]["summary"]["kv_resident_after_bytes"],
            )
            self.assertEqual(resource["decode"]["calls"], g - 1)
            self.assertEqual(call["recorded"]["output_parts"]["termination"], 1)

    def test_g1_no_decode_final_id_not_appended(self):
        r = m.logical_call(3, 2, 1)
        self.assertEqual(r["decode"]["calls"], 0)
        self.assertEqual(r["final_state_bytes"], r["prefill"]["state_after_bytes"])
        head = [
            op
            for op in r["prefill"]["source_ledger"]["operators"]
            if op["name"] == "lm_head"
        ][0]
        self.assertEqual(head["shapes"]["input"][0], 1)

    def test_invalid_and_report(self):
        with self.assertRaises(ValueError):
            m.calculate("actual_runtime")
        with self.assertRaises(ValueError):
            m.logical_call(0, 2, 0)
        r = m.calculate()
        text = m.markdown(r)
        self.assertIn("observed_model_forward_calls", text)
        self.assertIn("actual_hbm_bytes", text)


if __name__ == "__main__":
    unittest.main()
