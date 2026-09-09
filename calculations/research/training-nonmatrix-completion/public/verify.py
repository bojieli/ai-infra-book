import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'calculations/src'))
module = HERE / 'src/infra_calc/topics/training_nonmatrix.py'
name = 'infra_calc.topics.training_nonmatrix'
spec = importlib.util.spec_from_file_location(name, module)
m = importlib.util.module_from_spec(spec)
sys.modules[name] = m
spec.loader.exec_module(m)
r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(HERE / 'tests')))
if not r.wasSuccessful():
    raise SystemExit(1)
assert module.read_bytes() == (HERE.parent / 'src/infra_calc/topics/training_nonmatrix.py').read_bytes()
(HERE / 'bindings.json').write_text(json.dumps(dict(
    tests_passed=r.testsRun - len(r.skipped), tests_skipped=len(r.skipped),
    module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
    test_sha256=hashlib.sha256((HERE / 'tests/test_training_nonmatrix.py').read_bytes()).hexdigest(),
    book_sha256=hashlib.sha256((HERE / 'book.append.json').read_bytes()).hexdigest(),
    frozen_calculate_unchanged=True,
    source_bindings=json.loads((HERE.parent / 'source-bindings.json').read_text())), ensure_ascii=False, indent=2) + '\n')
