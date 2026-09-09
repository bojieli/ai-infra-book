import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.outline import insert_evidence

class OutlineEvidenceTests(unittest.TestCase):
    def test_sync_preserves_editorial_text_and_moved_owner(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outlines = root / "outlines"
            ext = outlines / "extensions"
            ext.mkdir(parents=True)
            main = outlines / "06-example.md"
            main.write_text("# Chapter\n\nKeep this argument and 16 GiB.\n\n**已复算（C36-growing-kv）：** old\n\n> exercise\n")
            (ext / main.name).write_text("# Original companion\n")
            moved = ext / "09-serving.md"
            moved.write_text("# Serving\n\n**已复算（C36-growing-kv）：** old\n")
            insert_evidence(root, main.name, "C36-growing-kv", "[result](../calculations/a.md) updated", "> exercise")
            self.assertIn("Keep this argument and 16 GiB.", main.read_text())
            self.assertNotIn("已复算", main.read_text())
            self.assertIn("](../../calculations/a.md)", moved.read_text())
            self.assertNotIn("已复算", (ext / main.name).read_text())
            snapshot = (main.read_bytes(), moved.read_bytes())
            insert_evidence(root, main.name, "C36-growing-kv", "[result](../calculations/a.md) updated", "> exercise")
            self.assertEqual(snapshot, (main.read_bytes(), moved.read_bytes()))

    def test_new_record_uses_companion_without_changing_exercise(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ext = root / "outlines/extensions"
            ext.mkdir(parents=True)
            main = root / "outlines/05-kernels.md"
            main.write_text("# Main\n\n> exercise\n")
            companion = ext / main.name
            companion.write_text("# Detail\n\n> exercise\n")
            original = main.read_bytes()
            insert_evidence(root, main.name, "new", "[data](../calculations/a.md)", "> exercise")
            self.assertEqual(original, main.read_bytes())
            self.assertLess(companion.read_text().index("已复算"), companion.read_text().index("> exercise"))

if __name__ == "__main__":
    unittest.main()
