"""Load delivery modules without writing anything into the public source tree."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
import infra_calc.paths
import infra_calc.sources
import infra_calc.topics.vl_request

spec = importlib.util.spec_from_file_location(
    "infra_calc.topics.vl_position_bridge", HERE / "public/vl_position_bridge.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as temp:
    staged = Path(temp)
    (staged / "configs").mkdir()
    (staged / "configs/vl-position-bridge.lock.json").write_bytes(
        (HERE / "public/vl-position-bridge.lock.json").read_bytes()
    )
    (staged / "research").symlink_to(PROJECT / "research", target_is_directory=True)
    with patch.object(infra_calc.paths, "PROJECT", staged):
        suite = unittest.defaultTestLoader.discover(
            str(HERE / "public"), pattern="test_*.py"
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
