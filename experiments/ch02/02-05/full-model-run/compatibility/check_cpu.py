"""CPU-only alias regression, same values baseline and distinct-state control."""
import json
from types import SimpleNamespace
import torch
from torch.func import functional_call
from offload_alias import adapt_functional_call


class TopK(torch.nn.Module):
    def __init__(self, bias):
        super().__init__()
        self.topk_config = SimpleNamespace(correction_bias=bias)

    def forward(self, x):
        return x + self.topk_config.correction_bias


# Exercise the production adapter's deliberately narrow type predicate without
# importing or claiming to execute the actual CUDA TopK implementation.
TopK.__module__ = 'sglang.srt.layers.moe.topk'


class Layer(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.gate = torch.nn.Module()
        self.gate.e_score_correction_bias = torch.nn.Parameter(torch.arange(256, dtype=torch.float32), requires_grad=False)
        self.topk = TopK(self.gate.e_score_correction_bias)
        self.fail = False
        self.observed = None

    def forward(self, x):
        self.observed = (self.gate.e_score_correction_bias, self.topk.topk_config.correction_bias)
        if self.fail:
            raise ValueError('deliberate exception')
        return self.topk(x)


torch.set_num_threads(1)
m = Layer()
old = m.gate.e_score_correction_bias
x = torch.arange(256, dtype=torch.float32) / 16
base = m(x)
same = {k: v.clone() for k, v in m.state_dict().items()}
adapted = adapt_functional_call(functional_call)
assert torch.equal(adapted(m, same, (x,)), base)
assert m.observed[0] is m.observed[1] is same['gate.e_score_correction_bias']
assert m.gate.e_score_correction_bias is m.topk.topk_config.correction_bias is old
different = {k: v + 1024 for k, v in same.items()}
unpatched = functional_call(m, different, (x,))
assert m.observed[0] is different['gate.e_score_correction_bias']
assert m.observed[1] is old
assert torch.equal(unpatched, base)
patched = adapted(m, different, (x,))
assert torch.equal(patched, x + different['gate.e_score_correction_bias'])
assert m.observed[0] is m.observed[1] is different['gate.e_score_correction_bias']
assert m.gate.e_score_correction_bias is m.topk.topk_config.correction_bias is old
m.fail = True
try:
    adapted(m, same, (x,))
    raise AssertionError('exception lost')
except ValueError as e:
    assert str(e) == 'deliberate exception'
assert m.gate.e_score_correction_bias is m.topk.topk_config.correction_bias is old
assert torch.equal(old, torch.arange(256, dtype=torch.float32))
print(json.dumps({'torch': torch.__version__, 'device': 'cpu', 'entries':256,
 'same_values_bitexact':True, 'unpatched_alias_stale':True,
 'distinct_state_exact':True, 'parameter_and_alias_restored_after_success_and_error':True,
 'original_weight_unchanged':True, 'actual_sglang_topk_executed':False}, indent=2))
