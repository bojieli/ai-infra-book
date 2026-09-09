import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.topics.workload_profiles import calculate, distribution, markdown


class ProfileTests(unittest.TestCase):
    def test_empirical_rank_boundary(self):
        self.assertEqual(distribution(list(range(1, 20)))["p95"], 19)
        self.assertEqual(distribution(list(range(1, 21)))["p95"], 19)
        self.assertEqual(distribution(list(range(1, 22)))["p95"], 20)
        self.assertIsNone(distribution([])["p95"])

    def test_archived_groups_and_missing_tools(self):
        result = calculate()
        self.assertEqual(sum(g["requests"] for g in result["profile_groups"]), result["summary"]["requests"])
        chat = next(g for g in result["profile_groups"] if g["group"] == "chat_capture")
        self.assertEqual(chat["requests"], 4)
        tool = next(r for r in chat["distributions"] if r["metric"] == "tool_s")
        self.assertEqual((tool["count"], tool["missing"], tool["p95"]), (0, 4, None))
        for row in chat["distributions"]:
            if row["count"]:
                self.assertEqual(row["p95"], row["max"])
        self.assertIn("p95", markdown(result))
        self.assertEqual(result["summary"]["new_requests_executed"], 0)
