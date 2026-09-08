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

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, fields

from vllm.config import ParallelConfig
from vllm.config.compilation import CUDAGraphMode
from vllm.config.utils import is_init_field
from vllm.engine.arg_utils import AsyncEngineArgs, EngineArgs
from vllm.logger import init_logger
from vllm.utils.argparse_utils import FlexibleArgumentParser

from arctic_inference.patching import ArcticPatch
from arctic_inference.vllm.config import ArcticParallelConfig

logger = init_logger(__name__)


def _maybe_force_piecewise_for_fca(vllm_config) -> None:
    """Force cudagraph_mode down to PIECEWISE when Forest Cascade Attention is
    configured.

    FCA only fires under piecewise cudagraphs -- its per-batch gate requires
    ``not use_full_cuda_graph`` -- so any full-cudagraph mode would silently
    disable FCA. With shift parallelism it would also dispatch full graphs the
    shift model never captured. Downgrading here (base + shift, at engine-config
    creation) keeps the behavior correct and crash-free. An explicit NONE or
    PIECEWISE mode is preserved; only full modes are downgraded.
    """
    if getattr(vllm_config, "_forest_cascade_attn_config", None) is None:
        return
    cc = vllm_config.compilation_config
    cg = cc.cudagraph_mode
    if cg is not None and cg.has_full_cudagraphs():
        logger.warning(
            "Forest Cascade Attention is configured; forcing cudagraph_mode "
            "%s -> PIECEWISE so FCA can fire (FCA is disabled under full "
            "cudagraphs).", cg,
        )
        cc.cudagraph_mode = CUDAGraphMode.PIECEWISE


@dataclass
class ArcticArgs:

    ulysses_sequence_parallel_size: int = 1
    enable_shift_parallel: bool = False
    shift_parallel_threshold: int = 512
    forest_cascade_attn_configs: str | None = None
    fp32_lm_head: bool = False


def _ensure_arctic_fields(engine_args) -> None:
    """Backfill ArcticArgs defaults onto a plain ``EngineArgs`` instance.

    v0.26 plugin-load timing (runtime-only drift): both 0.24 and 0.26 load
    general plugins from ``EngineArgs.__post_init__`` -> the *first*
    ``EngineArgs(...)`` (e.g. ``LLM.__init__`` building it directly) is
    constructed *before* Arctic's patches are applied, so ``EngineArgsPatch.
    __new__`` never upgrades it to ``ArcticEngineArgs`` and it lacks the
    ArcticArgs fields. By the time the (now-patched) ``create_engine_config``
    runs on that instance, reading ``self.ulysses_sequence_parallel_size``
    raises ``AttributeError``. On this path the Arctic args can only ever be
    their defaults (a base ``EngineArgs.__init__`` would reject them as unknown
    kwargs), so backfilling the dataclass defaults is exact, not a papering-over
    shim. The CLI path (``from_cli_args`` -> ``ArcticEngineArgs``) already has
    them and is unaffected.
    """
    for f in fields(ArcticArgs):
        if not hasattr(engine_args, f.name):
            setattr(engine_args, f.name, f.default)


@dataclass
class ArcticEngineArgs(EngineArgs, ArcticArgs):
    pass


@dataclass
class ArcticAsyncEngineArgs(AsyncEngineArgs, ArcticArgs):
    pass


class EngineArgsPatch(ArcticPatch[EngineArgs]):

    _orig_post_init = EngineArgs.__post_init__
    _orig_add_cli_args = EngineArgs.add_cli_args
    # Classmethod from vLLM; call via __func__ in from_cli_args so the parsed
    # namespace is applied to ArcticEngineArgs / ArcticAsyncEngineArgs (v0.18
    # exposes from_cli_args as a normal classmethod, not __wrapped__).
    _orig_from_cli_args = EngineArgs.from_cli_args
    _orig_create_engine_config = EngineArgs.create_engine_config

    def __new__(cls, *args, **kwargs):
        # Construct ArcticEngineArgs so ArcticArgs fields are initialized.
        if cls is EngineArgs:
            return ArcticEngineArgs(*args, **kwargs)
        return super(EngineArgs, cls).__new__(cls)

    def __post_init__(self):
        # Explicitly set the distributed executor backend if ulysses is enabled
        # since the ulysses parameter is not passed to ParallelConfig.__init__,
        # which leads to the backend being defaulted incorrectly to "uni".
        if (self.ulysses_sequence_parallel_size > 1 and
                self.distributed_executor_backend is None):
            self.distributed_executor_backend = "mp"

        # Propagate --fp32-lm-head to worker processes via the env var.
        # arctic_inference's plugin runs in every process and reads this
        # var when applying patches, so this needs to be set before the
        # workers are spawned (i.e. here in the parent EngineArgs).
        if self.fp32_lm_head:
            import os
            os.environ["ARCTIC_FP32_LM_HEAD"] = "1"

        self._orig_post_init()

    @staticmethod
    def add_cli_args(parser: FlexibleArgumentParser) -> FlexibleArgumentParser:
        parser = EngineArgsPatch._orig_add_cli_args(parser)
        arctic_group = parser.add_argument_group(
            title="Arctic Inference",
            description="Arctic Inference configuration.",
        )
        arctic_group.add_argument(
            "--ulysses-sequence-parallel-size",
            type=int,
            default=ArcticEngineArgs.ulysses_sequence_parallel_size,
            help="Number of Ulysses sequence parallel replicas",
        )
        arctic_group.add_argument(
            "--enable-shift-parallel",
            action='store_true',
            help='If True, enable shift parallelism.')
        arctic_group.add_argument(
            "--shift-parallel-threshold",
            type=int,
            default=ArcticEngineArgs.shift_parallel_threshold,
            help=("Ulysses sequence parallel if batch size > threshold, "
                  "otherwise tensor parallel across the whole world size"),
        )
        arctic_group.add_argument(
            "--forest-cascade-attn-configs",
            type=str,
            default=None,
            help=('Enable Forest Cascade Attention with a JSON config. '
                  'Example: \'{"max_query_len": 16, "min_group_size": 2, '
                  '"min_additional_prefix_blocks": 1, '
                  '"min_non_singleton_fraction": 0.25, '
                  '"max_non_singleton_groups": 256}\'. '
                  'Pass \'{}\' to enable with all defaults.'),
        )
        arctic_group.add_argument(
            "--fp32-lm-head",
            action='store_true',
            help=('Run the lm_head matmul in fp32 (weights stay in their '
                  'native dtype; the operands are upcast on the fly). '
                  'vLLM\'s V1 sampler already runs softmax in fp32, so '
                  'this gives precise log-probs end-to-end. Needed for '
                  'RL workloads. Equivalent to ARCTIC_FP32_LM_HEAD=1.'),
        )
        return parser

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace):
        if cls is EngineArgs:
            return EngineArgsPatch._orig_from_cli_args.__func__(
                ArcticEngineArgs, args)
        if cls is AsyncEngineArgs:
            return EngineArgsPatch._orig_from_cli_args.__func__(
                ArcticAsyncEngineArgs, args)
        return EngineArgsPatch._orig_from_cli_args.__func__(cls, args)

    def create_engine_config(self, *args, **kwargs):
        _ensure_arctic_fields(self)
        if (self.ulysses_sequence_parallel_size > 1 and
                self.distributed_executor_backend is None):
            self.distributed_executor_backend = "mp"

        # Store ulysses_sequence_parallel_size for access during config initialization
        from arctic_inference.vllm import ulysses
        ulysses._ulysses_sp_size = self.ulysses_sequence_parallel_size

        vllm_config = self._orig_create_engine_config(*args, **kwargs)
        # Recreate the parallel config with Arctic parameters since they might
        # not be passed to the parallel config __init__ when first initialized.
        pc_cls = type(vllm_config.parallel_config)
        kwargs_pc = {f.name: getattr(vllm_config.parallel_config, f.name)
                     for f in fields(vllm_config.parallel_config)
                     if is_init_field(pc_cls, f.name)}
        kwargs_pc["ulysses_sequence_parallel_size"] = (
            self.ulysses_sequence_parallel_size)
        kwargs_pc["enable_shift_parallel"] = self.enable_shift_parallel
        kwargs_pc["shift_parallel_threshold"] = self.shift_parallel_threshold
        vllm_config.parallel_config = ArcticParallelConfig(**kwargs_pc)

        if self.forest_cascade_attn_configs is not None:
            try:
                fca_cfg = json.loads(self.forest_cascade_attn_configs)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"--forest-cascade-attn-configs must be valid JSON: {e}"
                ) from e
            if not isinstance(fca_cfg, dict):
                raise ValueError(
                    "--forest-cascade-attn-configs must be a JSON object"
                )
            vllm_config._forest_cascade_attn_config = fca_cfg
        else:
            vllm_config._forest_cascade_attn_config = None

        _maybe_force_piecewise_for_fca(vllm_config)

        return vllm_config


class AsyncEngineArgsPatch(ArcticPatch[AsyncEngineArgs]):

    _orig_post_init = AsyncEngineArgs.__post_init__
    _orig_create_engine_config = AsyncEngineArgs.create_engine_config

    def __new__(cls, *args, **kwargs):
        # Construct ArcticAsyncEngineArgs so ArcticArgs fields are initialized.
        if cls is AsyncEngineArgs:
            return ArcticAsyncEngineArgs(*args, **kwargs)
        return super(AsyncEngineArgs, cls).__new__(cls)

    def __post_init__(self):
        if (self.ulysses_sequence_parallel_size > 1 and
                self.distributed_executor_backend is None):
            self.distributed_executor_backend = "mp"
        self._orig_post_init()

    def create_engine_config(self, *args, **kwargs):
        _ensure_arctic_fields(self)
        if (self.ulysses_sequence_parallel_size > 1 and
                self.distributed_executor_backend is None):
            self.distributed_executor_backend = "mp"

        from arctic_inference.vllm import ulysses
        ulysses._ulysses_sp_size = self.ulysses_sequence_parallel_size

        vllm_config = self._orig_create_engine_config(*args, **kwargs)
        # Recreate the parallel config with Arctic parameters since they might
        # not be passed to the parallel config __init__ when first initialized.
        pc_cls = type(vllm_config.parallel_config)
        kwargs_pc = {f.name: getattr(vllm_config.parallel_config, f.name)
                     for f in fields(vllm_config.parallel_config)
                     if is_init_field(pc_cls, f.name)}
        kwargs_pc["ulysses_sequence_parallel_size"] = (
            self.ulysses_sequence_parallel_size)
        kwargs_pc["enable_shift_parallel"] = self.enable_shift_parallel
        kwargs_pc["shift_parallel_threshold"] = self.shift_parallel_threshold
        vllm_config.parallel_config = ArcticParallelConfig(**kwargs_pc)

        if self.forest_cascade_attn_configs is not None:
            try:
                fca_cfg = json.loads(self.forest_cascade_attn_configs)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"--forest-cascade-attn-configs must be valid JSON: {e}"
                ) from e
            if not isinstance(fca_cfg, dict):
                raise ValueError(
                    "--forest-cascade-attn-configs must be a JSON object"
                )
            vllm_config._forest_cascade_attn_config = fca_cfg
        else:
            vllm_config._forest_cascade_attn_config = None

        _maybe_force_piecewise_for_fca(vllm_config)

        return vllm_config
