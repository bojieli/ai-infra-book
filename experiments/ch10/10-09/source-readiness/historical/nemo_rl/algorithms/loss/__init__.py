# Copyright (c) 2026, NVIDIA CORPORATION.  All rights reserved.
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

from nemo_rl.algorithms.loss.loss_functions import (
    ClippedPGLossConfig,
    ClippedPGLossDataDict,
    ClippedPGLossFn,
    DistillationLossConfig,
    DistillationLossDataDict,
    DistillationLossFn,
    DPOLossConfig,
    DPOLossDataDict,
    DPOLossFn,
    DraftCrossEntropyLossFn,
    NLLLossFn,
    PreferenceLossDataDict,
    PreferenceLossFn,
)
from nemo_rl.algorithms.loss.utils import (
    prepare_loss_input,
    prepare_packed_loss_input,
)
from nemo_rl.algorithms.loss.wrapper import (
    DraftLossWrapper,
    SequencePackingFusionLossWrapper,
    SequencePackingLossWrapper,
    wrap_loss_fn_with_input_preparation,
)

__all__ = [
    "ClippedPGLossConfig",
    "ClippedPGLossDataDict",
    "ClippedPGLossFn",
    "DistillationLossConfig",
    "DistillationLossDataDict",
    "DistillationLossFn",
    "DPOLossConfig",
    "DPOLossDataDict",
    "DPOLossFn",
    "NLLLossFn",
    "PreferenceLossDataDict",
    "PreferenceLossFn",
    "prepare_loss_input",
    "prepare_packed_loss_input",
    "SequencePackingFusionLossWrapper",
    "SequencePackingLossWrapper",
    "DraftLossWrapper",
    "wrap_loss_fn_with_input_preparation",
]
