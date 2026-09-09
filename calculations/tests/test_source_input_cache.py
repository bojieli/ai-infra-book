import ast
import unittest
from pathlib import Path

class SourceInputCacheTests(unittest.TestCase):
    def test_only_runtime_cache_is_excluded(self):
        source = Path(__file__).resolve().parents[1] / "src/infra_calc/reproduce.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "is_source_input")
        namespace = {}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        accepts = namespace["is_source_input"]
        for name in ["sources/__pycache__/run.cpython-314.pyc", "sources/run.pyc", "sources/run.pyo"]:
            self.assertFalse(accepts(Path(name)))
        for name in ["sources/run.py", "sources/cache/evidence.bin", "sources/checkpoint/model.distcp", "sources/model.safetensors.index.json"]:
            self.assertTrue(accepts(Path(name)))

if __name__ == "__main__":
    unittest.main()
