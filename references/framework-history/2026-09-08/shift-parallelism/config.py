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

import logging

import vllm
from pydantic import ConfigDict
from vllm.config import ParallelConfig, SpeculativeConfig, VllmConfig
from vllm.config.utils import config
from vllm.transformers_utils.configs.mlp_speculator import MLPSpeculatorConfig

from arctic_inference.patching import ArcticPatch

logger = logging.getLogger(__name__)


@config(config=ConfigDict(extra="forbid"))
class ArcticParallelConfig(ParallelConfig):

    ulysses_sequence_parallel_size: int = 1
    enable_shift_parallel: bool = False
    shift_parallel_threshold: int = 512

    def __post_init__(self, *args, **kwargs):
        if (self.enable_shift_parallel
                and self.ulysses_sequence_parallel_size == 1):
            raise ValueError("ulysses_sequence_parallel_size must be > 1 "
                             "when enable_shift_parallel is True.")
        super().__post_init__(*args, **kwargs)
        # ParallelConfig.__post_init__ sets world_size to pipeline_parallel_size *
        # tensor_parallel_size; override to PP * TP * ulysses_sequence_parallel_size.
        self.world_size = (self.pipeline_parallel_size *
                           self.tensor_parallel_size *
                           self.ulysses_sequence_parallel_size)


@config(config=ConfigDict(extra="forbid"))
class ArcticSpeculativeConfig(SpeculativeConfig):

    method: str | None = None
    disable_by_batch_size: int | None = None
    hard_disable_by_batch_size: int | None = None
    enable_suffix_decoding: bool = False
    suffix_cache_max_depth: int = 64
    suffix_speculative_tokens: int = 0
    suffix_cache_max_requests: int = 100000
    suffix_max_spec_factor: float = 1.0
    suffix_max_spec_offset: float = 0.0
    suffix_min_token_prob: float = 0.1

    def effective_draft_limit(self, batch_size: int) -> int:
        """Number of requests permitted to draft this decode step.

        Both batch-size caps funnel through the single ``draft_limit`` the
        worker and scheduler already use, so they compose cleanly:

          * ``hard_disable_by_batch_size`` (HARD): once the running batch
            reaches this, *no* request drafts (returns 0). SD is effectively
            off, but the spec pipeline stays structurally alive (the worker
            still returns a zero-filled draft and the scheduler allocates no
            spec placeholders) -- this avoids the stale-data crash that fully
            skipping the spec path on a single step would cause.
          * ``disable_by_batch_size`` (SOFT): above this, only the first N
            requests draft (caps total draft tokens to N * width).

        Returning ``batch_size`` means everyone drafts (no cap active). The
        HARD cap is checked first so it always wins when both apply.
        """
        if (self.hard_disable_by_batch_size is not None
                and batch_size >= self.hard_disable_by_batch_size):
            return 0
        if (self.disable_by_batch_size is not None
                and batch_size > self.disable_by_batch_size):
            return self.disable_by_batch_size
        return batch_size


class ParallelConfigPatch(ArcticPatch[ParallelConfig]):

    def __new__(cls, *args, **kwargs):
        # Override __new__ to return an ArcticParallelConfig instead of a
        # ParallelConfig when creating a new instance of the class.
        if cls is ParallelConfig:
            return ArcticParallelConfig.__new__(ArcticParallelConfig, *args,
                                                **kwargs)
        return super(ParallelConfig, cls).__new__(cls)


class SpeculativeConfigPatch(ArcticPatch[SpeculativeConfig]):

    _orig_post_init = SpeculativeConfig.__post_init__

    def __new__(cls, *args, **kwargs):
        if cls is SpeculativeConfig:
            return ArcticSpeculativeConfig.__new__(ArcticSpeculativeConfig,
                                                   *args, **kwargs)
        return super(SpeculativeConfig, cls).__new__(cls)

    def __post_init__(self):
        is_arctic_method = self.method in ("arctic", "mlp_speculator")
        use_suffix = (self.method == "suffix") or (self.method is None
                                                   and self.enable_suffix_decoding)
        use_hybrid = (self.method == "arctic" and self.enable_suffix_decoding)

        if (use_suffix or is_arctic_method) and self.disable_by_batch_size is None:
            logger.info("Defaulting disable_by_batch_size to 64")
            self.disable_by_batch_size = 64

        if self.hard_disable_by_batch_size is not None:
            logger.info(
                "Speculative decoding hard-disabled at running batch >= %d "
                "(soft first-N cap disable_by_batch_size=%s)",
                self.hard_disable_by_batch_size, self.disable_by_batch_size)
            if (self.disable_by_batch_size is not None
                    and self.hard_disable_by_batch_size
                    <= self.disable_by_batch_size):
                logger.warning(
                    "hard_disable_by_batch_size=%d <= disable_by_batch_size=%d:"
                    " the soft first-N cap never applies; SD goes straight from"
                    " full to off at batch %d.",
                    self.hard_disable_by_batch_size,
                    self.disable_by_batch_size,
                    self.hard_disable_by_batch_size)

        if use_hybrid:
            self.suffix_speculative_tokens = self.suffix_cache_max_depth

        if use_suffix:
            self.method = "suffix"
            self.enable_suffix_decoding = True
            # Use suffix_speculative_tokens if explicitly set, otherwise
            # default to 16 (not suffix_cache_max_depth which can be very
            # large and makes every step process 1+N tokens even when the
            # suffix cache has no matches).
            # NOTE: num_speculative_tokens defaults to None (not 0).
            if self.suffix_speculative_tokens > 0:
                self.num_speculative_tokens = self.suffix_speculative_tokens
            elif self.num_speculative_tokens is None:
                self.num_speculative_tokens = 16
            self._verify_args()
            return

        if is_arctic_method:
            # The Arctic speculator uses an MLPSpeculatorConfig-based model.
            # Upstream vLLM handles mlp_speculator correctly: creates
            # draft_model_config, detects TP=1, and sets draft_parallel_config.
            # Temporarily set method="mlp_speculator" to leverage this.
            saved_method = self.method
            self.method = "mlp_speculator"
            try:
                self._orig_post_init()
            finally:
                self.method = saved_method

            if self.num_speculative_tokens == 0:
                self.num_speculative_tokens = getattr(self, "num_lookahead_slots", 1)
        else:
            self._orig_post_init()


class VllmConfigPatch(ArcticPatch[VllmConfig]):

    _orig_str = VllmConfig.__str__
    _orig_post_init = VllmConfig.__post_init__

    from typing import Literal
    OldEagleModelTypes = vllm.config.speculative.EagleModelTypes
    NewEagleModelTypes = Literal["arctic", "mlp_speculator", "suffix", OldEagleModelTypes]

    def __str__(self, *args, **kwargs):
        string = self._orig_str(*args, **kwargs)
        string += f", ulysses_sequence_parallel_size={self.parallel_config.ulysses_sequence_parallel_size}"
        string += f", enable_shift_parallel={self.parallel_config.enable_shift_parallel}"
        string += f", shift_parallel_threshold={self.parallel_config.shift_parallel_threshold}"
        return string

    def __post_init__(self, *args, **kwargs):
        import sys
        from typing import Literal, get_args
        target_module = sys.modules[VllmConfig.__module__]
        original_types = getattr(target_module, "EagleModelTypes")
        NewEagleModelTypes = Literal["arctic", "mlp_speculator", "suffix", original_types]
        setattr(target_module, "EagleModelTypes", NewEagleModelTypes)
        try:
            self._orig_post_init(*args, **kwargs)
        finally:
            setattr(target_module, "EagleModelTypes", original_types)


class MLPSpeculatorConfigPatch(ArcticPatch[MLPSpeculatorConfig]):

    _orig_init = MLPSpeculatorConfig.__init__

    def __init__(self, *args, **kwargs):
        self.base_model_arch = kwargs.pop("base_model_arch", "")
        self._orig_init(*args, **kwargs)

        # Inject dummy attributes required by vLLM's ModelArchConfigConvertor
        # The convertor tries to calculate head_size = hidden_size // num_attention_heads
        if not hasattr(self, "num_attention_heads"):
            self.num_attention_heads = 1

        if not hasattr(self, "hidden_size"):
            # Fallback to n_embd if present, otherwise default to a safe dummy value
            self.hidden_size = getattr(self, "n_embd", 1024)

        # Ensure hidden_size is an integer to prevent TypeError during division
        if hasattr(self, "hidden_size"):
            self.hidden_size = int(self.hidden_size)
