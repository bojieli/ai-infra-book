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

# The exact vLLM version this branch's patches target. This is the single source
# of truth for the plugin's version check and is intentionally decoupled from the
# install extras: the `vllm` extra is left unpinned so users can resolve vLLM
# against their own torch. Arctic patches are only applied when the *installed*
# vLLM matches this version; on any other version the plugin skips patching and
# vLLM runs unmodified (no acceleration).
VLLM_PATCH_VERSION = "0.26.0"


def get_compatible_vllm_version():
    """The exact vLLM version the plugin's patches are written against."""
    return VLLM_PATCH_VERSION


def plugin_version_compatible() -> bool:
    """True iff the installed vLLM exactly matches the plugin's supported pin."""
    import vllm
    want = get_compatible_vllm_version()
    return want is not None and vllm.__version__ == want


# For debugging
def print0(*args, **kwargs):
    from vllm.distributed.parallel_state import get_tp_group
    if get_tp_group().is_first_rank:
        print(*args, **kwargs)
