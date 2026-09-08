from generated_redfuser_ptpc_quant_gemm import redfuser_ptpc_quant_gemm

import torch
import torch.nn.functional as F

FP8_MAX = 448.0
FP8_TYPE = "float8_e4m3fn"

def per_token_quant_fp8(x):
  x_fp32 = x.to(torch.float32)
  per_token_amax, _ = torch.max(torch.abs(x_fp32), dim=-1, keepdim=True)
  per_token_scale = per_token_amax / FP8_MAX

  # quant hidden_states
  y = (x_fp32 / per_token_scale).to(dtype=getattr(torch, FP8_TYPE))
  y_scale = per_token_scale
  return y, y_scale


def ref_program(x: torch.Tensor, w_fp8: torch.Tensor, w_scales: torch.Tensor):
  x_fp8, x_scale = per_token_quant_fp8(x)
  x_ = x_fp8.to(torch.float32) * x_scale
  w_ = w_fp8.to(torch.float32) * w_scales
  y_ref = F.linear(x_, w_)
  return y_ref

def test_ptpc_quant_gemm():
    A = 0.01 * torch.randn((4096, 4096), device="cuda", dtype=torch.float16)
    W = 0.01 * torch.randn((4096, 4096), device="cuda", dtype=torch.float16)
    W_fp8, W_scales = per_token_quant_fp8(W)

    kernel = redfuser_ptpc_quant_gemm()
    output = kernel(A, W_fp8, W_scales.squeeze())
    ref_output = ref_program(A, W_fp8, W_scales)
    torch.testing.assert_close(output, ref_output.to(torch.float16), rtol=1e-2, atol=1e-1)
    print("All checks passed.✅")

if __name__ == "__main__":
    test_ptpc_quant_gemm()