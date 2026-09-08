import torch
import torch.nn.functional as F
from torch import nn

FLOAT4_E2M1_MAX = 6.0


@torch.no_grad()
def fp16(tensor_value: torch.Tensor, group_size: int):
    return tensor_value


def float_value(exp_bit, man_bit):
    bias = 0
    values = []
    min_to_zero = True
    subnormal = True
    for i in range(2**exp_bit):
        for j in range(2**man_bit):
            if min_to_zero:
                values.append(0.0)
                min_to_zero = False
            else:
                if subnormal:
                    values.append((2 ** (i - bias)) * (j * 2 ** (-man_bit)))
                else:
                    values.append((2 ** (i - 1 - bias)) * (1 + j * 2 ** (-man_bit)))

        subnormal = False

    return values


FP4_E2M1_GRID = torch.tensor(float_value(2, 1), device="cuda")
FP6_E2M3_GRID = torch.tensor(float_value(2, 3), device="cuda")


def quantize_to_grid(x: torch.Tensor, levels: torch.Tensor) -> torch.Tensor:
    levels = levels.to(x.device)
    boundaries = (levels[:-1] + levels[1:]) / 2.0
    odd_boundaries = boundaries[1::2]
    mask = torch.isin(x, odd_boundaries)
    x = x + 0.0000005 * mask  # round to even
    indices = torch.bucketize(x, boundaries)
    indices.clamp_(0, len(levels) - 1)

    quantized = levels[indices]
    return quantized, indices


def cast_to_fp4(x: torch.Tensor):
    sign = torch.sign(x)
    x_abs = torch.abs(x)
    x_quant, _ = quantize_to_grid(x_abs, FP4_E2M1_GRID)
    return x_quant * sign


def cast_to_fp4_em(x: torch.Tensor):
    sign = torch.sign(x)
    x_abs = torch.abs(x)
    fp4, fp4_index = quantize_to_grid(x_abs, FP4_E2M1_GRID)
    _, fp6_index = quantize_to_grid(x_abs, FP6_E2M3_GRID)
    fp6_index.clamp_(min=fp4_index * 4 - 1, max=fp4_index * 4 + 2)
    fp6 = FP6_E2M3_GRID.to(x.device)[fp6_index]

    return fp4 * sign, fp6 * sign


@torch.no_grad()
def get_quant_mxfp(tensor_value: torch.Tensor, group_size: int):

    org_shape = tensor_value.shape
    org_dtype = tensor_value.dtype

    tensor_value = tensor_value.float()
    if group_size > 0:
        assert org_shape[-1] % group_size == 0
        tensor_value = tensor_value.reshape(-1, group_size)

    max_val = tensor_value.abs().amax(dim=1, keepdim=True)
    # avoid divide a too small value
    max_val = max_val.clamp(min=1e-8)

    max_quant_val = torch.tensor(FLOAT4_E2M1_MAX, device=tensor_value.device)

    # Compute the scaling factor
    exp = torch.floor(torch.log2(max_val)) - torch.floor(torch.log2(max_quant_val))
    scales = torch.pow(2, exp)
    tensor_quant = cast_to_fp4(tensor_value / scales) * scales

    return tensor_quant.reshape(org_shape).to(org_dtype)




@torch.no_grad()
def get_quant_mxes(tensor_value: torch.Tensor, group_size: int):

    sub_group_size = 8  # extra 2 bit for scale in subgroup
    assert group_size % sub_group_size == 0

    org_shape = tensor_value.shape
    org_dtype = tensor_value.dtype

    tensor_value = tensor_value.float()

    if group_size > 0:
        assert org_shape[-1] % group_size == 0
        tensor_value = tensor_value.reshape(-1, group_size)

    max_val = tensor_value.abs().amax(dim=1, keepdim=True)
    # avoid divide a too small value
    max_val = max_val.clamp(min=1e-8)

    max_quant_val = torch.tensor(FLOAT4_E2M1_MAX, device=tensor_value.device)

    tensor_value = tensor_value.reshape(-1, sub_group_size)
    # Compute the scaling factor
    exp = torch.floor(torch.log2(max_val)) - torch.floor(torch.log2(max_quant_val))
    bias_mse = {}
    range_ = range(-1, 2)
    for bias in range_:
        scales = torch.pow(2, exp + bias)
        sub_groups_per_group = group_size // sub_group_size
        scales = scales.expand(-1, sub_groups_per_group).reshape(-1, 1)
        ratios = torch.tensor(
            [1.0, 1.25, 1.5, 1.75], dtype=tensor_value.dtype, device=tensor_value.device
        )
        x_expanded = tensor_value.unsqueeze(2)
        scales_expanded = scales.unsqueeze(2)

        cand_scales = scales_expanded * ratios.view(1, 1, -1)
        cand_qval = cast_to_fp4(x_expanded / cand_scales) * cand_scales
        mse_per_ratio = (cand_qval - x_expanded).pow(2).mean(dim=1)
        best_ratio_idx = mse_per_ratio.argmin(dim=1)
        row_idx = torch.arange(tensor_value.size(0), device=tensor_value.device)
        best_dqval = cand_qval[row_idx, :, best_ratio_idx]
        quant_mse_per_subgrp = mse_per_ratio[row_idx, best_ratio_idx]
        tensor_deq = best_dqval.reshape(-1, group_size)
        quant_mse_sum = quant_mse_per_subgrp.view(-1, sub_groups_per_group).mean(
            dim=1, keepdim=True
        )
        bias_mse[bias] = (tensor_deq, quant_mse_sum)
    all_mse = torch.cat([bias_mse[b][1] for b in range_], dim=1)
    best_bias_idx = all_mse.argmin(dim=1)
    all_deq = torch.stack([bias_mse[b][0] for b in range_], dim=0)
    all_deq = all_deq.view(len(range_), -1, group_size)
    idx_expanded = best_bias_idx.view(1, -1, 1).expand(1, -1, group_size)
    final_deq = torch.gather(all_deq, dim=0, index=idx_expanded).squeeze(0)
    tensor_deq = final_deq.reshape(org_shape).to(org_dtype)
    return tensor_deq


@torch.no_grad()
def get_quant_mxem(tensor_value: torch.Tensor, group_size: int):

    sub_group_size = 8  # extra 2 bit for mantissa in subgroup
    assert group_size % sub_group_size == 0

    org_shape = tensor_value.shape
    org_dtype = tensor_value.dtype

    tensor_value = tensor_value.float()

    if group_size > 0:
        assert org_shape[-1] % group_size == 0
        tensor_value = tensor_value.reshape(-1, group_size)

    max_val = tensor_value.abs().amax(dim=1, keepdim=True)
    # avoid divide a too small value
    max_val = max_val.clamp(min=1e-8)

    max_quant_val = torch.tensor(FLOAT4_E2M1_MAX, device=tensor_value.device)

    # Compute the scaling factor
    exp = torch.floor(torch.log2(max_val)) - torch.floor(torch.log2(max_quant_val))
    scales = torch.pow(2, exp)

    fp4, fp6 = cast_to_fp4_em(tensor_value / scales)

    tmp = fp4.reshape(-1, sub_group_size)
    outlier_mask = torch.zeros_like(tmp, dtype=tensor_value.dtype).to(
        tensor_value.device
    )

    _, indices = torch.topk(tmp.abs(), 1)
    outlier_mask.scatter_(1, indices, 1)
    outlier_group_mask = outlier_mask.reshape(-1, group_size)
    tensor_quant = (fp4 * (1 - outlier_group_mask) + fp6 * outlier_group_mask) * scales

    return tensor_quant.reshape(org_shape).to(org_dtype)


QUANT_METHOD_MAP = {
    "mxfp": get_quant_mxfp,
    "mxes": get_quant_mxes,
    "mxem": get_quant_mxem,
}


class QuantUnit:
    def __init__(self, bit: int, mode: str, group_size: int):
        self.bit = bit
        self.mode = mode
        self.group_size = group_size

        if self.bit == 16:
            self.quant_func = fp16
        elif self.bit == 4:
            assert mode in QUANT_METHOD_MAP
            self.quant_func = QUANT_METHOD_MAP[mode]

            assert self.group_size == 32
        else:
            raise NotImplementedError

    def forward(self, x):
        return self.quant_func(x, self.group_size)


class QuantConfig:
    def __init__(
        self, w_bit: int, w_mode: str, a_bit: int, a_mode: str, group_size: int
    ):
        self.w_unit = QuantUnit(w_bit, w_mode, group_size)
        self.a_unit = QuantUnit(a_bit, a_mode, group_size)

    def weight(self, weight):
        return self.w_unit.forward(weight)

    def activation(self, acitivation):
        return self.a_unit.forward(acitivation)
