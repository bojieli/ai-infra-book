#
# Copyright (c) 2025 Huawei Technologies Co., Ltd. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# This file is a part of the vllm-ascend project.
#

import torch
import torch_npu
from vllm.model_executor.layers.activation import (
    QuickGELU,
    SiluAndMul,
    SiluAndMulWithClamp,
    SwigluOAIAndMul,
    SwigluStepAndMul,
)


class AscendQuickGELU(QuickGELU):
    def forward_oot(self, x: torch.tensor) -> torch.Tensor:
        out = torch_npu.npu_fast_gelu(x)
        return out


class AscendSiluAndMul(SiluAndMul):
    def forward_oot(self, x: torch.Tensor) -> torch.Tensor:
        out = torch_npu.npu_swiglu(x)
        return out


class AscendSiluAndMulWithClamp(SiluAndMulWithClamp):
    def forward_oot(self, x: torch.Tensor) -> torch.Tensor:
        d = x.shape[-1] // 2
        gate = torch.clamp(x[..., :d], max=self.swiglu_limit)
        up = torch.clamp(x[..., d:], min=-self.swiglu_limit, max=self.swiglu_limit)
        x = torch.cat([gate, up], dim=-1)
        out = torch_npu.npu_swiglu(x)
        return out


class AscendSwigluOAIAndMul:
    def swiglu_oai_forward(x: torch.Tensor, alpha: float = 1.702, limit: float = 7.0) -> torch.Tensor:
        class MinimalSwigluOAIAndMul:
            def __init__(self):
                self.alpha = alpha
                self.limit = limit

        layer = MinimalSwigluOAIAndMul()
        return SwigluOAIAndMul.forward_native(layer, x)


class AscendSwigluStepAndMul:
    def swiglustep_forward(x: torch.Tensor, limit: float = 7.0) -> torch.Tensor:
        if limit is None:
            raise ValueError("SwigluStepAndMul requires limit to be set.")

        # Triton fused path: 1D-grid row-loop kernel that fuses
        # silu + clamp + mul into a single launch (see
        # vllm_ascend/ops/triton/activation/swiglustep.py). Numerically
        # equivalent to forward_native below.
        from vllm.triton_utils import HAS_TRITON

        if HAS_TRITON:
            from vllm_ascend.ops.triton.activation.swiglustep import (
                swiglustep_forward_triton,
            )

            return swiglustep_forward_triton(x, limit)

        # Fallback when triton is unavailable: vllm's native silu+clamp+mul.
        class MinimalSwigluStepAndMul:
            def __init__(self):
                self.limit = limit

        layer = MinimalSwigluStepAndMul()
        return SwigluStepAndMul.forward_native(layer, x)
