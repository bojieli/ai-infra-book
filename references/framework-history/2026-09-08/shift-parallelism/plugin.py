# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

import vllm
from vllm.platforms import current_platform

import arctic_inference.envs as envs
from arctic_inference.utils import (get_compatible_vllm_version,
                                    plugin_version_compatible)


def arctic_inference_plugin():
    if not envs.ARCTIC_INFERENCE_ENABLED:
        return

    if not envs.ARCTIC_INFERENCE_SKIP_PLATFORM_CHECK:
        if not current_platform.is_cuda():
            raise RuntimeError(
                "Arctic Inference plugin requires the cuda platform!")

    # The patches below are version-specific. Enabling Arctic Inference is an
    # explicit request for acceleration, so if the installed vLLM does not match
    # the version the patches target we fail loudly rather than silently running
    # unpatched. To run unmodified vLLM instead, leave ARCTIC_INFERENCE_ENABLED
    # unset; ARCTIC_INFERENCE_SKIP_VERSION_CHECK forces patching regardless.
    if (not envs.ARCTIC_INFERENCE_SKIP_VERSION_CHECK
            and not plugin_version_compatible()):
        raise RuntimeError(
            f"Arctic Inference is enabled (ARCTIC_INFERENCE_ENABLED=1) but the installed "
            f"vllm=={vllm.__version__} does not match the version its patches require: "
            f"(vllm=={get_compatible_vllm_version()}). Either install the matching vLLM "
            f"(`pip install vllm=={get_compatible_vllm_version()}`) or unset "
            f"ARCTIC_INFERENCE_ENABLED to run unmodified vLLM. To bypass this check at "
            f"your own risk, set ARCTIC_INFERENCE_SKIP_VERSION_CHECK=1. "
            f"If you did not enable Arctic Inference yourself, turn off FCA in your "
            f"framework's config.")

    # Applying the (version-dependent) plugin from here on.
    # TODO: port ArcticInference patches to the V2 model runner and drop this.
    os.environ["VLLM_USE_V2_MODEL_RUNNER"] = "0"

    print("\x1b[36;1mArctic Inference plugin is enabled!\x1b[0m",
          file=sys.stderr)

    # Lazy import to avoid potential errors when the plugin is disabled.
    from .patches import apply_arctic_patches
    apply_arctic_patches()
