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

import time
from collections.abc import Callable
from concurrent.futures import Future
from contextlib import contextmanager
from typing import Optional, cast

import torch
import vllm.distributed.parallel_state as parallel_state
from vllm.config import ModelConfig, ParallelConfig, CUDAGraphMode, VllmConfig
from vllm.config.compilation import CompilationConfig
from vllm.distributed.parallel_state import (init_model_parallel_group,
                                             get_world_group,
                                             destroy_model_parallel,
                                             destroy_distributed_environment)
from vllm.model_executor.layers.attention import Attention
from vllm.v1.cudagraph_dispatcher import CudagraphDispatcher
from vllm.v1.engine import EngineCoreOutputs
from vllm.v1.engine.core import EngineCore
from vllm.v1.executor.multiproc_executor import MultiprocExecutor, WorkerProc
from vllm.v1.outputs import ModelRunnerOutput


from arctic_inference.patching import ArcticPatch

# global variable to hack compilation config
_ulysses_sp_size = 1

def apply_shift_parallel_patches():
    UlyssesModelConfig.apply_patch()
    UlyssesParallelState.apply_patch()
    UlyssesWorkerProc.apply_patch()
    UlyssesMultiprocExecutor.apply_patch()
    UlyssesAttention.apply_patch()
    UlyssesCudagraphDispatcher.apply_patch()
    UlyssesCompilationConfig.apply_patch()
    UlyssesVllmConfig.apply_patch()
    UlyssesEngineCore.apply_patch()


class UlyssesModelConfig(ArcticPatch[ModelConfig]):

    _orig_get_num_kv_heads = ModelConfig.get_num_kv_heads
    _orig_get_num_attention_heads = ModelConfig.get_num_attention_heads

    def get_num_kv_heads(self: ModelConfig,
                         parallel_config: ParallelConfig) -> int:
        num_kv_heads = self._orig_get_num_kv_heads(parallel_config)
        sp_size = parallel_config.ulysses_sequence_parallel_size
        return max(1, num_kv_heads // sp_size)

    def get_num_attention_heads(self: ModelConfig,
                                parallel_config: ParallelConfig) -> int:
        num_heads = self._orig_get_num_attention_heads(parallel_config)
        sp_size = parallel_config.ulysses_sequence_parallel_size
        return max(1, num_heads // sp_size)

    def get_layers_start_end_indices(
            self, parallel_config: "ParallelConfig") -> tuple[int, int]:
        from vllm.distributed.utils import get_pp_indices
        if (self.hf_text_config.model_type == "deepseek_mtp"
                or self.hf_config.model_type == "mimo_mtp"
                or self.hf_config.model_type == "glm4_moe_mtp"):
            total_num_hidden_layers = getattr(self.hf_text_config,
                                              "num_nextn_predict_layers", 0)
        else:
            total_num_hidden_layers = getattr(self.hf_text_config,
                                              "num_hidden_layers", 0)
        # the layout order is: DP x PP x SP x TP
        pp_rank = (parallel_config.rank //
                   (parallel_config.tensor_parallel_size *
                    parallel_config.ulysses_sequence_parallel_size)
                   ) % parallel_config.pipeline_parallel_size
        pp_size = parallel_config.pipeline_parallel_size
        start, end = get_pp_indices(total_num_hidden_layers, pp_rank, pp_size)
        return start, end


class UlyssesParallelState(ArcticPatch[parallel_state]):

    _SP = None
    _SP_TP = None

    def initialize_model_parallel(
        tensor_model_parallel_size: int = 1,
        pipeline_model_parallel_size: int = 1,
        prefill_context_model_parallel_size: int = 1,
        decode_context_model_parallel_size: Optional[int] = 1,
        backend: Optional[str] = None,
    ) -> None:

        from vllm.distributed.parallel_state import _DP, _EP, _PP, _TP, _DCP, _PCP

        assert torch.distributed.is_initialized()
        world_size: int = torch.distributed.get_world_size()
        rank = torch.distributed.get_rank()
        backend = backend or torch.distributed.get_backend(
            get_world_group().device_group
        )

        data_parallel_size = 1
        from vllm.config import get_current_vllm_config
        config = get_current_vllm_config()
        if config is not None:
            data_parallel_size = config.parallel_config.data_parallel_size

        sequence_parallel_size = config.parallel_config.ulysses_sequence_parallel_size

        # vLLM types allow None, but group building needs an int
        if decode_context_model_parallel_size is None:
            # treat "no DCP" as DCP==TP (common interpretation)
            decode_context_model_parallel_size = tensor_model_parallel_size

        # Layout order (extended from vLLM's): ExternalDP x DP x PP x PCP x SP x TP
        all_ranks = torch.arange(world_size).reshape(
            -1,
            data_parallel_size,
            pipeline_model_parallel_size,
            prefill_context_model_parallel_size,
            sequence_parallel_size,
            tensor_model_parallel_size,
        )

        assert _TP is None, "tensor model parallel group is already initialized"
        group_ranks = all_ranks.view(-1, tensor_model_parallel_size).unbind(0)
        group_ranks = [x.tolist() for x in group_ranks]
        TP_group_ranks = group_ranks
        _TP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            use_message_queue_broadcaster=True,
            group_name="tp",
        )

        assert _DCP is None, "decode context model parallel group is already initialized"
        group_ranks = all_ranks.reshape(-1, decode_context_model_parallel_size).unbind(0)
        group_ranks = [x.tolist() for x in group_ranks]
        DCP_group_ranks = group_ranks
        _DCP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            use_message_queue_broadcaster=True,
            group_name="dcp",
        )

        assert _PCP is None, "prefill context parallel group is already initialized"
        group_ranks = (
            all_ranks.transpose(3, 5) 
            .reshape(-1, prefill_context_model_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        PCP_group_ranks = group_ranks
        _PCP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="pcp",
        )

        assert _PP is None, "pipeline model parallel group is already initialized"
        group_ranks = (
            all_ranks.transpose(2, 5)  
            .reshape(-1, pipeline_model_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        PP_group_ranks = group_ranks
        _PP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="pp",
        )

        assert _DP is None, "data parallel group is already initialized"
        group_ranks = (
            all_ranks.transpose(1, 5) 
            .reshape(-1, data_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        DP_group_ranks = group_ranks
        _DP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="dp",
        )

        assert _EP is None, "expert parallel group is already initialized"
        group_ranks = (
            all_ranks.permute(0, 4, 2, 1, 3, 5)  # ExternalDP, SP, PP, DP, PCP, TP
            .reshape(-1, data_parallel_size * prefill_context_model_parallel_size * tensor_model_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        EP_group_ranks = group_ranks
        _EP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="ep",
        )

        assert parallel_state._SP is None, "sequence parallel group is already initialized"
        group_ranks = (
            all_ranks.transpose(4, 5)
            .reshape(-1, sequence_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        SP_group_ranks = group_ranks
        _SP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="sp",
        )

        shift_parallel_size = tensor_model_parallel_size * sequence_parallel_size
        assert parallel_state._SP_TP is None, "full-TP group is already initialized"
        group_ranks = (
            all_ranks.transpose(4, 5)  # head-order trick
            .reshape(-1, shift_parallel_size)
            .unbind(0)
        )
        group_ranks = [x.tolist() for x in group_ranks]
        SP_TP_group_ranks = group_ranks
        _SP_TP = init_model_parallel_group(
            group_ranks,
            get_world_group().local_rank,
            backend,
            group_name="sp_tp",
        )

        parallel_state.logger.info(
            "rank %s in world size %s is assigned as DP rank %s, PP rank %s, "
            "PCP rank %s, TP rank %s, DCP rank %s, EP rank %s, SP rank %s, SP_TP rank %s",
            rank,
            world_size,
            _DP.rank_in_group,
            _PP.rank_in_group,
            _PCP.rank_in_group,
            _TP.rank_in_group,
            _DCP.rank_in_group,
            _EP.rank_in_group,
            _SP.rank_in_group,
            _SP_TP.rank_in_group,
        )

        parallel_state._TP = _TP
        parallel_state._DCP = _DCP
        parallel_state._PCP = _PCP
        parallel_state._PP = _PP
        parallel_state._DP = _DP
        parallel_state._EP = _EP
        parallel_state._SP = _SP
        parallel_state._SP_TP = _SP_TP

        if get_world_group().local_rank == 0:
            parallel_state.logger.info(
                "UlyssesParallelState initialized:\n"
                f"  PP {_PP.world_size} ranks {PP_group_ranks}\n"
                f"  TP {_TP.world_size} ranks {TP_group_ranks}\n"
                f"  DCP {_DCP.world_size} ranks {DCP_group_ranks}\n"
                f"  PCP {_PCP.world_size} ranks {PCP_group_ranks}\n"
                f"  SP {_SP.world_size} ranks {SP_group_ranks}\n"
                f"  DP {_DP.world_size} ranks {DP_group_ranks}\n"
                f"  EP {_EP.world_size} ranks {EP_group_ranks}\n"
                f"  SP_TP {_SP_TP.world_size} ranks {SP_TP_group_ranks}"
            )

        num_kv_heads = config.model_config._orig_get_num_kv_heads(config.parallel_config)
        if get_world_group().local_rank == 0 and num_kv_heads < sequence_parallel_size:
            parallel_state.logger.info(
                f"KV cache is replicated by factor {sequence_parallel_size // num_kv_heads}"
            )

    @contextmanager
    def graph_capture(device: torch.device, graph_capture_context=None):
        """
        `graph_capture` is a context manager which should surround the code that
        is capturing the CUDA graph. Its main purpose is to ensure that the
        some operations will be run after the graph is captured, before the graph
        is replayed. It returns a `GraphCaptureContext` object which contains the
        necessary data for the graph capture. Currently, it only contains the
        stream that the graph capture is running on. This stream is set to the
        current CUDA stream when the context manager is entered and reset to the
        default stream when the context manager is exited. This is to ensure that
        the graph capture is running on a separate stream from the default stream,
        in order to explicitly distinguish the kernels to capture
        from other kernels possibly launched on background in the default stream.

        v0.26: upstream added an optional ``graph_capture_context`` arg (the
        caller in ``profile_cudagraph_memory`` / cudagraph capture passes one);
        honor it when provided, mirroring base ``graph_capture``.
        """
        from vllm.distributed.parallel_state import GraphCaptureContext
        from vllm.distributed.device_communicators.cuda_communicator import (
            CudaCommunicator,
        )
        context = graph_capture_context or GraphCaptureContext(
            torch.cuda.Stream(device=device))

        def _get_ca(group):
            if (group is not None
                    and group.device_communicator is not None
                    and isinstance(group.device_communicator, CudaCommunicator)):
                return group.device_communicator.ca_comm
            return None

        tp_ca = _get_ca(parallel_state._TP)
        sp_tp_ca = _get_ca(parallel_state._SP_TP)

        saved_tp = tp_ca.disabled if tp_ca is not None else None
        saved_sp_tp = sp_tp_ca.disabled if sp_tp_ca is not None else None
        if tp_ca is not None:
            tp_ca.disabled = True
        if sp_tp_ca is not None:
            sp_tp_ca.disabled = True

        try:
            with parallel_state._TP.graph_capture(context), \
                 parallel_state._PP.graph_capture(context), \
                 parallel_state._SP_TP.graph_capture(context):
                yield context
        finally:
            if tp_ca is not None and saved_tp is not None:
                tp_ca.disabled = saved_tp
            if sp_tp_ca is not None and saved_sp_tp is not None:
                sp_tp_ca.disabled = saved_sp_tp


class UlyssesWorkerProc(ArcticPatch[WorkerProc]):

    @staticmethod
    def _destroy_ulysses_parallel():
        sp = getattr(parallel_state, '_SP', None)
        if sp is not None:
            sp.destroy()
        parallel_state._SP = None
        sp_tp = getattr(parallel_state, '_SP_TP', None)
        if sp_tp is not None:
            sp_tp.destroy()
        parallel_state._SP_TP = None

    def shutdown(self):
        if self.rpc_broadcast_mq is not None:
            self.rpc_broadcast_mq.shutdown()
        if self.worker_response_mq is not None:
            self.worker_response_mq.shutdown()
        self.worker.shutdown()
        self.rpc_broadcast_mq = None
        self.worker_response_mq = None
        destroy_model_parallel()
        UlyssesWorkerProc._destroy_ulysses_parallel()
        destroy_distributed_environment()


class UlyssesMultiprocExecutor(ArcticPatch[MultiprocExecutor]):

    def _get_parallel_sizes(self) -> tuple[int, int, int]:
        self.world_size = self.parallel_config.world_size
        assert self.world_size % self.parallel_config.nnodes_within_dp == 0, (
            f"global world_size ({self.parallel_config.world_size}) must be "
            f"divisible by nnodes_within_dp "
            f"({self.parallel_config.nnodes_within_dp}). "
        )
        self.local_world_size = self.parallel_config.local_world_size
        tp_size = self.parallel_config.tensor_parallel_size
        pp_size = self.parallel_config.pipeline_parallel_size
        pcp_size = self.parallel_config.prefill_context_parallel_size
        sp_size = self.parallel_config.ulysses_sequence_parallel_size

        assert self.world_size == tp_size * pp_size * pcp_size * sp_size, (
            f"world_size ({self.world_size}) must be equal to the "
            f"tensor_parallel_size ({tp_size}) x pipeline"
            f"_parallel_size ({pp_size}) x prefill_context"
            f"_parallel_size ({pcp_size}) x ulysses_sequence_parallel"
            f"_size ({sp_size})."
        )
        return tp_size * sp_size, pp_size, pcp_size


class UlyssesAttention(ArcticPatch[Attention]):

    _orig_init = Attention.__init__
    _orig_forward = Attention.forward

    def __init__(self, num_heads, *args, **kwargs):
        from .model_runner import is_shift_parallel_mode
        self.sp_size = parallel_state._SP.world_size
        self.sp_device_group = parallel_state._SP.device_group
        if not is_shift_parallel_mode():
            num_heads //= self.sp_size
            num_kv_heads = kwargs["num_kv_heads"]
            self.is_kv_replicated = True if num_kv_heads < self.sp_size else False
            if self.is_kv_replicated:
                self.replication_factor = self.sp_size // num_kv_heads
                num_kv_heads = 1
            else:
                num_kv_heads //= self.sp_size
            kwargs["num_kv_heads"] = num_kv_heads
        return self._orig_init(num_heads, *args, **kwargs)

    def forward(self, query, key, value, **kwargs):
        from .model_runner import is_shift_parallel_mode
        if self.sp_size == 1 or is_shift_parallel_mode():
            return self._orig_forward(query, key, value, **kwargs)

        # prepare
        q = query.view(-1, self.sp_size, self.num_heads * self.head_size)
        if self.is_kv_replicated:
            k = key.view(-1, self.sp_size // self.replication_factor, self.head_size).repeat_interleave(self.replication_factor, dim=1)
            v = value.view(-1, self.sp_size // self.replication_factor, self.head_size).repeat_interleave(self.replication_factor, dim=1)
        else:
            k = key.view(-1, self.sp_size, self.num_kv_heads * self.head_size)
            v = value.view(-1, self.sp_size, self.num_kv_heads * self.head_size)

        # pack
        qkv = torch.cat((q, k, v), dim=-1).transpose(0, 1).reshape(
            -1, (self.num_heads + 2 * self.num_kv_heads) * self.head_size)
        
        # Ulysses all-to-all 1/2
        qkv_ = torch.empty_like(qkv)
        torch.distributed.all_to_all_single(qkv_, qkv, group=self.sp_device_group)

        # unpack
        q_, k_, v_ = qkv_.split([
            self.num_heads * self.head_size, 
            self.num_kv_heads * self.head_size, 
            self.num_kv_heads * self.head_size
        ], dim=-1)

        # original attention
        c_ = self._orig_forward(q_, k_, v_, **kwargs)

        # Ulysses all-to-all 2/2
        c = torch.empty_like(c_)
        torch.distributed.all_to_all_single(c, c_, group=self.sp_device_group)
        output = (c.view(self.sp_size, -1, self.num_heads * self.head_size)
                  .transpose(0, 1)
                  .reshape(-1, self.num_heads * self.sp_size * self.head_size))
        
        return output


class UlyssesCudagraphDispatcher(ArcticPatch[CudagraphDispatcher]):

    _orig_initialize_cudagraph_keys = CudagraphDispatcher.initialize_cudagraph_keys

    def initialize_cudagraph_keys(self, cudagraph_mode: CUDAGraphMode,
                                  uniform_decode_query_len: int = 1):
        self._orig_initialize_cudagraph_keys(cudagraph_mode, uniform_decode_query_len)

        # sp_group = getattr(parallel_state, "_SP", None)
        # sp_size = sp_group.world_size if sp_group is not None else 1
        # if sp_size <= 1:
        #     return

        # if self.vllm_config.lora_config:
        #     if self.compilation_config.cudagraph_specialize_lora:
        #         lora_cases = [True, False]
        #     else:
        #         lora_cases = [True]
        # else:
        #     lora_cases = [False]

        # if cudagraph_mode.mixed_mode() != CUDAGraphMode.NONE:
        #     for bs, has_lora in product(
        #         self.compilation_config.cudagraph_capture_sizes, lora_cases
        #     ):
        #         bd = self._create_padded_batch_descriptor(
        #             num_tokens=bs, #  * sp_size,
        #             uniform_decode=False,
        #             has_lora=has_lora,
        #         ).relax_for_mixed_batch_cudagraphs()

        #         self.add_cudagraph_key(cudagraph_mode.mixed_mode(), bd)

        # if (cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
        #         and cudagraph_mode.separate_routine()):
        #     max_num_tokens = (
        #         uniform_decode_query_len
        #         * self.vllm_config.scheduler_config.max_num_seqs
        #     )
        #     cudagraph_capture_sizes_for_decode = [
        #         x for x in self.compilation_config.cudagraph_capture_sizes
        #         if uniform_decode_query_len <= x <= max_num_tokens
        #     ]
        #     for bs, has_lora in product(cudagraph_capture_sizes_for_decode, lora_cases):
        #         bd = self._create_padded_batch_descriptor(
        #             num_tokens=bs, #  * sp_size,
        #             uniform_decode=True,
        #             has_lora=has_lora,
        #         )
        #         self.add_cudagraph_key(CUDAGraphMode.FULL, bd)


class UlyssesCompilationConfig(ArcticPatch[CompilationConfig]):

    _orig_post_init_cudagraph_sizes = CompilationConfig.post_init_cudagraph_sizes

    def post_init_cudagraph_sizes(self) -> None:

#         # print(f"Before post_init_cudagraph_sizes: max_cudagraph_capture_size={self.max_cudagraph_capture_size}, cudagraph_capture_sizes={self.cudagraph_capture_sizes}")

#         # Access the module-level variable set during engine config creation
#         sp_size = _ulysses_sp_size

#         # scale sizes by Ulysses sequence parallel size
#         self.max_cudagraph_capture_size *= sp_size
#         self.cudagraph_capture_sizes = [size * sp_size for size in self.cudagraph_capture_sizes]

#         # print(f"After scaling for SP size {sp_size}: max_cudagraph_capture_size={self.max_cudagraph_capture_size}, cudagraph_capture_sizes={self.cudagraph_capture_sizes}")

        self._orig_post_init_cudagraph_sizes()

#         # revert back to original shapes
#         self.max_cudagraph_capture_size //= sp_size
#         self.cudagraph_capture_sizes = [size // sp_size for size in self.cudagraph_capture_sizes]

#         # print(f"self.bs_to_padded_graph_size {self.bs_to_padded_graph_size}")

#         # import traceback
#         # traceback.print_stack()

class UlyssesVllmConfig(ArcticPatch[VllmConfig]):

    _orig_set_cudagraph_sizes = VllmConfig._set_cudagraph_sizes

    @staticmethod
    def _generate_capture_sizes(max_size: int) -> list[int]:
        sizes = [i for i in [1, 2, 4] if i <= max_size]
        if max_size >= 8:
            sizes += list(range(8, min(max_size + 1, 256), 8))
        if max_size >= 256:
            sizes += list(range(256, min(max_size + 1, 512), 16))
        if max_size >= 512:
            sizes += list(range(512, max_size + 1, 32))
        return sizes

    @staticmethod
    def _build_bs_to_padded(capture_sizes: list[int],
                            max_capture_size: int) -> list[int]:
        table = [0] * (max_capture_size + 1)
        for end, start in zip(
            capture_sizes + [max_capture_size + 1],
            [0] + capture_sizes,
        ):
            for bs in range(start, end):
                table[bs] = start if bs == start else end
        return table

    def _set_cudagraph_sizes(self):
        sp_size = _ulysses_sp_size

        max_cudagraph_capture_size = self.compilation_config.max_cudagraph_capture_size
        cudagraph_capture_sizes = self.compilation_config.cudagraph_capture_sizes

        if cudagraph_capture_sizes is None:
            if max_cudagraph_capture_size is None:
                max_cudagraph_capture_size = 512
            # Canonical (unscaled) sizes: [1, 2, 4, 8, ..., 512]
            canonical_sizes = self._generate_capture_sizes(
                max_cudagraph_capture_size)

            # Base model (Ulysses): scale by sp_size
            self.compilation_config.cudagraph_capture_sizes = [
                s * sp_size for s in canonical_sizes
            ]
            self.compilation_config.max_cudagraph_capture_size = (
                max_cudagraph_capture_size * sp_size
            )

            # Shift model: scale by 1 (use canonical sizes as-is)
            shift_sizes = list(canonical_sizes)
            shift_max = max_cudagraph_capture_size
        else:
            shift_sizes = list(cudagraph_capture_sizes)
            shift_max = max(shift_sizes) if shift_sizes else 0

        self._shift_cudagraph_capture_sizes = shift_sizes
        self._shift_max_cudagraph_capture_size = shift_max
        self._shift_bs_to_padded_graph_size = self._build_bs_to_padded(
            shift_sizes, shift_max) if shift_sizes else []

        print(
            f"UlyssesVllmConfig: base max_cudagraph_capture_size="
            f"{self.compilation_config.max_cudagraph_capture_size}, "
            f"base sizes={self.compilation_config.cudagraph_capture_sizes}, "
            f"shift max={shift_max}, shift sizes={shift_sizes}"
        )

        self._orig_set_cudagraph_sizes()

        base_sizes = self.compilation_config.cudagraph_capture_sizes
        base_max = self.compilation_config.max_cudagraph_capture_size
        self._base_bs_to_padded_graph_size = self._build_bs_to_padded(
            base_sizes, base_max) if base_sizes else []

    def pad_for_cudagraph(self, batch_size: int) -> int:
        from .model_runner import is_shift_parallel_mode
        if is_shift_parallel_mode() and self._shift_bs_to_padded_graph_size:
            return self._shift_bs_to_padded_graph_size[batch_size]
        return self._base_bs_to_padded_graph_size[batch_size]


class UlyssesEngineCore(ArcticPatch[EngineCore]):

    iteration = 0

    _orig_post_step = EngineCore.post_step

    def _sd_hardoff_threshold(self):
        """Running-batch size at/above which SD is hard-disabled, or None.

        Matches the worker's ``effective_draft_limit() == 0`` condition: the
        hard cap is the only thing that drives the draft limit to exactly 0.
        """
        spec = self.vllm_config.speculative_config
        if spec is None:
            return None
        return getattr(spec, "hard_disable_by_batch_size", None)

    def post_step(self, model_executed: bool) -> None:
        """Skip the per-step draft-fetch RPC when SD is hard-off.

        In the sync spec-decode path the base ``post_step`` always issues a
        ``take_draft_token_ids()`` collective RPC (~3.4 ms/step). At hard-off
        (running batch >= ``hard_disable_by_batch_size``) the workers produced
        only zero-filled drafts and the scheduler already cleared
        ``request.spec_token_ids`` when it consumed the prior step's drafts, so
        fetching + applying them is a no-op. Skipping the RPC is therefore
        output-identical and recovers the full hard-off TPOT tax. Outside the
        hard-off regime behavior is exactly the base method.
        """
        # Only the sync spec-decode path runs take_draft_token_ids() here.
        if (self.async_scheduling or not self.use_spec_decode
                or not model_executed):
            return self._orig_post_step(model_executed)

        thr = self._sd_hardoff_threshold()
        if thr is not None:
            try:
                running, _ = self.scheduler.get_request_counts()
            except Exception:
                # On any failure, fall back to exact base behavior.
                running = None
            # At running >= hard_disable_by_batch_size the worker's
            # effective_draft_limit() == 0, so it produced only zero-filled
            # drafts this step; the scheduler already cleared
            # request.spec_token_ids when it consumed the prior step's
            # drafts, so the take + update round-trip is pure waste.
            if running is not None and running >= thr:
                return

        return self._orig_post_step(model_executed)

    def step_with_batch_queue(
        self,
    ) -> tuple[dict[int, EngineCoreOutputs] | None, bool]:
        """Schedule and execute batches with the batch queue.
        Note that if nothing to output in this step, None is returned.

        The execution flow is as follows:
        1. Try to schedule a new batch if the batch queue is not full.
        If a new batch is scheduled, directly return an empty engine core
        output. In other words, fulfilling the batch queue has a higher priority
        than getting model outputs.
        2. If there is no new scheduled batch, meaning that the batch queue
        is full or no other requests can be scheduled, we block until the first
        batch in the job queue is finished.
        3. Update the scheduler from the output.
        """
        batch_queue = self.batch_queue
        assert batch_queue is not None

        # Try to schedule a new batch if the batch queue is not full, but
        # the scheduler may return an empty batch if all requests are scheduled.
        # Note that this is not blocking.
        assert len(batch_queue) < self.batch_queue_size

        step_start_time = time.monotonic()

        model_executed = False
        deferred_scheduler_output = None
        if self.scheduler.has_requests():
            # v0.26: schedule() takes the prefill-throttle flag; execute_model
            # is now wrapped in log_error_detail.
            scheduler_output = self.scheduler.schedule(
                self._should_throttle_prefills()
            )
            with self.log_error_detail(scheduler_output):
                exec_future = self.model_executor.execute_model(
                    scheduler_output, non_block=True
                )
            if self.is_ec_consumer:
                model_executed = scheduler_output.total_num_scheduled_tokens > 0

            if self.is_pooling_model or not model_executed:
                # No sampling required (no requests scheduled).
                future = cast(Future[ModelRunnerOutput], exec_future)
            else:
                if not scheduler_output.pending_structured_output_tokens:
                    # We aren't waiting for any tokens, get any grammar output
                    # and sample immediately.
                    grammar_output = self.scheduler.get_grammar_bitmask(
                        scheduler_output
                    )
                    future = self.model_executor.sample_tokens(
                        grammar_output, non_block=True
                    )
                else:
                    # We need to defer sampling until we have processed the model output
                    # from the prior step.
                    deferred_scheduler_output = scheduler_output

            if not deferred_scheduler_output:
                # Add this step's future to the queue.
                batch_queue.appendleft((future, scheduler_output, exec_future))
                # v0.26: return `model_executed` (not a bare True), and gate on
                # `model_executed or scheduler.has_requests()`.
                if len(batch_queue) < self.batch_queue_size and (
                    model_executed or self.scheduler.has_requests()
                ):
                    # Don't block on next worker response unless the queue is full
                    # or there are no more requests to schedule.
                    return None, model_executed

        elif not batch_queue:
            # Queue is empty. We should not reach here since this method should
            # only be called when the scheduler contains requests or the queue
            # is non-empty.
            return None, False

        # Block until the next result is available.
        future, scheduler_output, exec_model_fut = batch_queue.pop()
        # v0.26: log_iteration_details context manager was replaced by
        # capture_iteration_details(...) + a post-hoc _attach_iteration_details.
        with (
            self.capture_iteration_details(scheduler_output) as iteration_details,
            self.log_error_detail(scheduler_output),
        ):
            model_output = future.result()
            if model_output is None:
                # None from sample_tokens() implies that the original execute_model()
                # call failed - raise that exception.
                exec_model_fut.result()
                raise RuntimeError("unexpected error")

        # Before processing the model output, process any aborts that happened
        # during the model execution.
        self._process_aborts_queue()
        engine_core_outputs = self.scheduler.update_from_output(
            scheduler_output, model_output
        )
        self._attach_iteration_details(engine_core_outputs, iteration_details)

        # NOTE(nick): We can either handle the deferred tasks here or save
        # in a field and do it immediately once step_with_batch_queue is
        # re-called. The latter slightly favors TTFT over TPOT/throughput.
        if deferred_scheduler_output:
            # v0.26: gate on check_for_draft_tokens and tolerate a None result
            # (was `use_spec_decode` + an unconditional assert).
            if self.check_for_draft_tokens:
                draft_token_ids = self.model_executor.take_draft_token_ids()
                if draft_token_ids is not None:
                    # Update the draft token ids in the scheduler output to
                    # filter out the invalid spec tokens, which will be padded
                    # with -1 and skipped by the grammar bitmask computation.
                    self.scheduler.update_draft_token_ids_in_output(
                        draft_token_ids, deferred_scheduler_output
                    )
            # We now have the tokens needed to compute the bitmask for the
            # deferred request. Get the bitmask and call sample tokens.
            grammar_output = self.scheduler.get_grammar_bitmask(
                deferred_scheduler_output
            )
            future = self.model_executor.sample_tokens(grammar_output, non_block=True)
            batch_queue.appendleft((future, deferred_scheduler_output, exec_future))

        total_time_ms = (time.monotonic() - step_start_time) * 1000

        running, waiting = self.scheduler.get_request_counts()
        scheduled_tokens = scheduler_output.total_num_scheduled_tokens
        concurrency = len(scheduler_output.num_scheduled_tokens.keys())
        # print(f"iteration {self.iteration}, running: {running}, waiting: {waiting}, scheduled tokens: {scheduled_tokens}, concurrency: {concurrency}, total_time_ms: {total_time_ms:.2f}")
        self.iteration += 1

        return engine_core_outputs, model_executed