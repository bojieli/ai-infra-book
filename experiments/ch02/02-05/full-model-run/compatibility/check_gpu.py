"""Root-scheduled tiny CUDA test: no real model parameters or Engine.

Uses actual OffloaderV1 and actual fused gate kernel. Actual TopK object serves
as the configuration holder; call the same biased_topk_jit_kernel_impl directly
to avoid unrelated TP process-group setup. Does not test full TopK dispatch.
"""
import argparse
import json
from pathlib import Path
import torch
from sglang.srt.layers.moe.topk import TopK, TopKConfig, biased_topk_jit_kernel_impl
from sglang.srt.utils.offloader import OffloaderV1
from offload_alias import install

ap = argparse.ArgumentParser()
ap.add_argument('--config', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
c = json.loads(a.config.read_text())
assert c['n_routed_experts'] == 256 and c['scoring_func'] == 'sqrtsoftplus'
torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(0.009)


class Layer(torch.nn.Module):
    def __init__(self, bias, scale):
        super().__init__()
        self.gate = torch.nn.Module()
        self.gate.e_score_correction_bias = torch.nn.Parameter(bias.clone(), requires_grad=False)
        self.topk = TopK.__new__(TopK)
        torch.nn.Module.__init__(self.topk)
        self.topk.topk_config = TopKConfig(top_k=c['num_experts_per_tok'],
            use_grouped_topk=False, renormalize=c['norm_topk_prob'],
            correction_bias=self.gate.e_score_correction_bias,
            scoring_func=c['scoring_func'], routed_scaling_factor=c['routed_scaling_factor'],
            apply_routed_scaling_factor_on_output=scale)
        self.fail = False
        self.seen = None

    def forward(self, hidden, logits):
        cfg = self.topk.topk_config
        self.seen = (self.gate.e_score_correction_bias is cfg.correction_bias,
                     str(self.gate.e_score_correction_bias.device), str(cfg.correction_bias.device))
        if self.fail:
            raise ValueError('deliberate exception')
        return biased_topk_jit_kernel_impl(hidden_states=hidden, gating_output=logits,
            correction_bias=cfg.correction_bias, topk=cfg.top_k,
            renormalize=cfg.renormalize, scoring_func=cfg.scoring_func,
            num_fused_shared_experts=0, routed_scaling_factor=cfg.routed_scaling_factor,
            num_token_non_padded=None, expert_location_dispatch_info=None,
            apply_routed_scaling_factor_on_output=cfg.apply_routed_scaling_factor_on_output)


rows = []
for scale in (False, True):
    for n in (4, 8):
        g = torch.Generator(device='cpu').manual_seed(205000+n)
        bias = (torch.rand(256, generator=g) * .2 - .1).cuda()
        logits = (torch.randn(n, 256, generator=g) * 1.7).cuda()
        hidden = torch.zeros(n, 4096, device='cuda', dtype=torch.bfloat16)
        reference = Layer(bias, scale)
        expected = reference(hidden, logits)
        subject = Layer(bias, scale)
        original_bias = subject.gate.e_score_correction_bias
        subject = OffloaderV1(cpu_offload_max_bytes=4096).maybe_offload_to_cpu(subject)
        if not rows:
            try:
                subject(hidden, logits)
                raise AssertionError('unadapted call unexpectedly succeeded')
            except Exception as e:
                error = str(e)
                assert 'Device mismatch' in error and 'cpu' in error, error
                assert subject.seen == (False, 'cuda:0', 'cpu')
            # Native V1 does not restore module.forward after an exception;
            # construct a fresh instance for the patched test.
            subject = Layer(bias, scale)
            original_bias = subject.gate.e_score_correction_bias
            subject = OffloaderV1(cpu_offload_max_bytes=4096).maybe_offload_to_cpu(subject)
            install()
        result = subject(hidden, logits)
        torch.cuda.synchronize()
        assert all(torch.equal(x,y) for x,y in zip(result, expected))
        assert subject.seen == (True, 'cuda:0', 'cuda:0')
        assert subject.gate.e_score_correction_bias is subject.topk.topk_config.correction_bias is original_bias
        assert original_bias.device.type == 'cpu' and torch.equal(original_bias, bias.cpu())
        subject.fail = True
        try:
            subject(hidden, logits)
            raise AssertionError('exception lost')
        except ValueError as e:
            assert str(e) == 'deliberate exception'
        assert subject.gate.e_score_correction_bias is subject.topk.topk_config.correction_bias is original_bias
        rows.append(dict(tokens=n, scale_in_topk=scale, ids_exact=True, weights_exact=True,
            restored_success_and_exception=True, ids=result[1].cpu().tolist(), weights=result[0].cpu().tolist()))
peak = torch.cuda.max_memory_reserved()
assert peak < 1024**3
a.out.write_text(json.dumps(dict(torch=torch.__version__, peak_reserved_bytes=peak,
    negative_control=error, actual_offloader_v1=True, actual_fused_gate=True,
    full_topk_dispatch=False, model_payloads=False, results=rows), indent=2))
