import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'calculations/src'))
name = 'infra_calc.topics.v4_prefix_continuation'
spec = importlib.util.spec_from_file_location(name, HERE / 'v4_prefix_continuation.py')
m = importlib.util.module_from_spec(spec)
sys.modules[name] = m
spec.loader.exec_module(m)
suite = unittest.defaultTestLoader.discover(str(HERE / 'tests'))
r = unittest.TextTestRunner(verbosity=2).run(suite)
if not r.wasSuccessful():
    raise SystemExit(1)
result = m.calculate()
(HERE / 'v4-prefix-book.md').write_text(m.markdown(result))
(HERE / 'validation.json').write_text(json.dumps(dict(
    tests_run=r.testsRun,
    module_sha256=hashlib.sha256((HERE / 'v4_prefix_continuation.py').read_bytes()).hexdigest(),
    test_sha256=hashlib.sha256((HERE / 'tests/test_v4_prefix_continuation.py').read_bytes()).hexdigest(),
    changes='markdown plus fixed execution metadata moved out of replayable scenario; frozen arithmetic unchanged'), indent=2) + '\n')
