"""Count ordinary arithmetic in the actual declared scalar reference."""
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'calculations/src'))
path = ROOT / 'calculations/research/training-nonmatrix-completion/src/infra_calc/topics/training_nonmatrix.py'
spec = importlib.util.spec_from_file_location('audited', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
counts = Counter()

class Counted(float):
    def operation(self, other, name, function):
        counts[name] += 1
        return Counted(function(float(self), float(other)))
    def __add__(self, other): return self.operation(other, 'ordinary', lambda a, b: a+b)
    __radd__ = __add__
    def __sub__(self, other): return self.operation(other, 'ordinary', lambda a, b: a-b)
    def __rsub__(self, other): return self.operation(other, 'ordinary', lambda a, b: b-a)
    def __mul__(self, other): return self.operation(other, 'ordinary', lambda a, b: a*b)
    __rmul__ = __mul__
    def __truediv__(self, other): return self.operation(other, 'ordinary', lambda a, b: a/b)
    def __pow__(self, other): return self.operation(other, 'pow', lambda a, b: a**b)

def sqrt(value):
    counts['sqrt'] += 1
    return Counted(math.sqrt(value))

m.math = SimpleNamespace(sqrt=sqrt)
results = []
for n in (1, 4, 17):
    counts.clear()
    m.adamw_update(*[[Counted(.2)]*n for _ in range(4)], step=2,
                   learning_rate=Counted(.001), beta1=Counted(.9), beta2=Counted(.999),
                   epsilon=Counted(1e-8), weight_decay=Counted(.01))
    expected = dict(ordinary=14*n+6, pow=2, sqrt=n)
    results.append(dict(parameters=n, actual=dict(counts), expected=expected, matches=dict(counts)==expected))
print(json.dumps(results, indent=2))
