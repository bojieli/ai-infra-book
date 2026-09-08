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
import torch.nn.functional as F
import torch_npu

from vllm_ascend.ops.activation import AscendSiluAndMul


class AscendSiluAndMul310(AscendSiluAndMul):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.shape[-1] % 32 == 0:
            out = torch_npu.npu_swiglu(x)
        else:
            h = x.shape[-1] // 2
            out = F.silu(x[..., :h]) * x[..., h:]
        return out
