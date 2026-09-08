# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
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

import contextlib
import copy
import gc
import time
from dataclasses import replace
from typing import Any, Optional, TYPE_CHECKING, Union

import numpy as np
import torch
from tqdm import tqdm

import vllm.distributed.parallel_state as parallel_state
import vllm.envs as envs
from vllm.compilation.counter import compilation_counter
from vllm.compilation.monitor import set_cudagraph_capturing_enabled
from vllm.config import CUDAGraphMode, VllmConfig
from vllm.distributed.kv_transfer import (get_kv_transfer_group,
                                          has_kv_transfer_group)
from vllm.distributed.parallel_state import (get_pp_group, get_tp_group,
                                             is_global_first_rank)
from vllm.forward_context import BatchDescriptor, set_forward_context
from vllm.model_executor.model_loader import get_model
from vllm.sequence import IntermediateTensors
from vllm.utils.math_utils import round_up, cdiv
from vllm.utils.torch_utils import PIN_MEMORY
from vllm.v1.attention.backend import CommonAttentionMetadata
from vllm.v1.outputs import (EMPTY_MODEL_RUNNER_OUTPUT, ModelRunnerOutput,
                              SamplerOutput, AsyncModelRunnerOutput)
from vllm.v1.sample.metadata import SamplingMetadata
from vllm.v1.sample.rejection_sampler import MAX_SPEC_LEN, RejectionSampler
from vllm.v1.spec_decode.metadata import SpecDecodeMetadata
from vllm.v1.utils import record_function_or_nullcontext
from vllm.v1.worker.gpu_model_runner import (
    GPUModelRunner,
    logger,
    AsyncGPUModelRunnerOutput,
)
from vllm.v1.structured_output.utils import apply_grammar_bitmask

if TYPE_CHECKING:
    from vllm.v1.core.sched.output import SchedulerOutput

from arctic_inference.patching import ArcticPatch
from arctic_inference.suffix_decoding import (SuffixDecodingCache,
                                              SuffixDecodingDraft)
from arctic_inference.vllm.spec_dec.arctic_proposer import (ArcticProposer,
                                                            SuffixProposer)

SP_TP_MODE = None


@contextlib.contextmanager
def set_shift_parallel_mode(mode: Optional[bool]):
    """
    Swap the tensor-parallel group to an SP-compatible variant when 'mode' is True.
    """
    if mode is None:
        yield
        return

    global SP_TP_MODE

    if not is_shift_parallel_mode():
        assert not parallel_state._TP_STATE_PATCHED
        parallel_state._ORIG_TP = parallel_state._TP

    old_mode = SP_TP_MODE
    old_tp_group = parallel_state.get_tp_group()
    SP_TP_MODE = mode

    parallel_state._TP = (parallel_state._SP_TP
                          if mode else parallel_state._ORIG_TP)

    try:
        yield
    finally:
        SP_TP_MODE = old_mode
        parallel_state._TP = old_tp_group


def is_shift_parallel_mode() -> bool:
    """Check if the shift parallel mode is enabled."""
    global SP_TP_MODE
    return SP_TP_MODE is True


class GPUModelRunnerPatch(ArcticPatch[GPUModelRunner]):
    """
    Rebased GPUModelRunnerPatch for vLLM v0.18.
    """

    _orig_capture_cudagraphs = GPUModelRunner._capture_cudagraphs
    _orig_profile_run = GPUModelRunner.profile_run
    _orig_load_model = GPUModelRunner.load_model
    _orig_propose_draft_token_ids = GPUModelRunner.propose_draft_token_ids
    _orig_dummy_run = GPUModelRunner._dummy_run
    _orig_init = GPUModelRunner.__init__
    _orig_build_attention_metadata = GPUModelRunner._build_attention_metadata
    _orig_execute_model = GPUModelRunner.execute_model
    _orig_bookkeeping_sync = GPUModelRunner._bookkeeping_sync
    _orig_sample_tokens = GPUModelRunner.sample_tokens
    _orig_initialize_kv_cache = GPUModelRunner.initialize_kv_cache
    _orig_reload_weights = GPUModelRunner.reload_weights

    def __init__(
        self,
        vllm_config: VllmConfig,
        device: torch.device,
    ):
        if vllm_config.parallel_config.ulysses_sequence_parallel_size > 1:
            self.use_ulysses = True
            pass_config = vllm_config.compilation_config.pass_config
            if pass_config.enable_sp:
                raise ValueError(
                    "Ulysses sequence parallelism is incompatible with native "
                    "sequence parallelism. Set enable_sequence_parallelism "
                    "to False in the pass config to use Ulysses."
                )
        else:
            self.use_ulysses = False

        arctic_methods = ("arctic", "suffix", "mlp_speculator")
        is_arctic_spec = (vllm_config.speculative_config is not None and
                          vllm_config.speculative_config.method in arctic_methods)

        arctic_speculative_config = None
        if is_arctic_spec:
            arctic_speculative_config = vllm_config.speculative_config
            vllm_config.speculative_config = None

        self._orig_init(vllm_config, device)

        self._suffix_cache: Optional[SuffixDecodingCache] = None

        if is_arctic_spec:
            self.vllm_config.speculative_config = arctic_speculative_config
            self.speculative_config = arctic_speculative_config
            self.num_spec_tokens = getattr(self.speculative_config,
                                           "num_speculative_tokens", 0)
            self.uniform_decode_query_len = 1 + self.num_spec_tokens

            if not hasattr(self, "draft_token_ids_cpu") or self.draft_token_ids_cpu is None:
                self.draft_token_ids_event = torch.Event()
                self.draft_token_ids_copy_stream = torch.cuda.Stream()
                self.draft_token_ids_cpu = torch.empty(
                    (self.max_num_reqs, self.num_spec_tokens),
                    dtype=torch.int64,
                    device="cpu",
                    pin_memory=PIN_MEMORY,
                )

            if (self.use_async_scheduling
                    and self.speculative_config.method in ("arctic", "mlp_speculator", "suffix")):
                if not hasattr(self, "valid_sampled_token_count_cpu") or self.valid_sampled_token_count_cpu is None:
                    self.valid_sampled_token_count_event = torch.Event()
                    self.valid_sampled_token_count_copy_stream = torch.cuda.Stream()
                    self.valid_sampled_token_count_cpu = torch.empty(
                        self.max_num_reqs,
                        dtype=torch.int64,
                        device="cpu",
                        pin_memory=PIN_MEMORY,
                    )

            if get_pp_group().is_last_rank:
                if self.speculative_config.method in ("arctic", "mlp_speculator"):
                    self.drafter = ArcticProposer(self.vllm_config)
                elif self.speculative_config.method == "suffix":
                    self.drafter = SuffixProposer()
                else:
                    raise ValueError(f"Unknown speculative decoding method: {self.speculative_config.method}")

                self.rejection_sampler = RejectionSampler(self.sampler)

        if (self.speculative_config is not None and
                getattr(self.speculative_config, "enable_suffix_decoding", False)):

            if self.speculative_config.method not in arctic_methods:
                raise ValueError(
                    "Suffix decoding is only supported with the 'arctic', "
                    "'mlp_speculator' or 'suffix' spec decoding methods."
                )
            spec_cfg = self.speculative_config
            self._suffix_cache = SuffixDecodingCache(
                max_tree_depth=spec_cfg.suffix_cache_max_depth,
                max_cached_requests=spec_cfg.suffix_cache_max_requests
            )

        # Async suffix decoding infrastructure: a dedicated CUDA stream and
        # pinned buffer for copying sampled token IDs to CPU *without*
        # serialising behind Arctic GPU drafting work on the default stream.
        if self._suffix_cache is not None and self.use_async_scheduling:
            self.suffix_copy_stream = torch.cuda.Stream()
            self.suffix_copy_done_event = torch.Event()
            max_gen_len = 1 + self.num_spec_tokens
            self.suffix_sampled_ids_pinned = torch.empty(
                (self.max_num_reqs, max_gen_len),
                dtype=torch.int64,
                device="cpu",
                pin_memory=PIN_MEMORY,
            )
            # Pinned buffer for suffix merge results.  Using pinned memory
            # for H2C copies avoids the implicit default-stream
            # synchronisation that cudaMemcpyAsync performs with pageable
            # (non-pinned) source memory.  Without this, the merge step
            # blocks the CPU until ALL pending GPU work (including Arctic
            # drafting) completes, destroying the async overlap.
            self._suffix_merge_pinned = torch.zeros(
                (self.max_num_reqs, self.num_spec_tokens),
                dtype=torch.int64,
                device="cpu",
                pin_memory=PIN_MEMORY,
            )

        # Pre-allocated GPU buffer for the merged draft tensor.
        # Avoids per-step F.pad / torch.zeros allocations in the async
        # Arctic drafting path (propose_draft_token_ids + suffix merge).
        # Shape: [max_num_reqs, num_spec_tokens], int64 (matches
        # draft_token_ids_cpu for zero-cost _copy_draft_token_ids_to_cpu).
        if (self.speculative_config is not None
                and self.use_async_scheduling
                and self.speculative_config.method
                    in ("arctic", "mlp_speculator")):
            self._draft_merged_gpu = torch.zeros(
                (self.max_num_reqs, self.num_spec_tokens),
                dtype=torch.int64, device=self.device,
            )

        # Pre-allocated pinned index buffer for suffix merge overlay.
        # Avoids per-step torch.tensor(...).pin_memory() allocations.
        if self._suffix_cache is not None and self.use_async_scheduling:
            self._suffix_index_pinned = torch.empty(
                self.max_num_reqs, dtype=torch.long,
                device="cpu", pin_memory=PIN_MEMORY,
            )

        # Per-request response tokens for suffix pattern building in async
        # mode.  In async scheduling, _bookkeeping_sync writes -1 placeholders
        # to token_ids_cpu instead of real values, corrupting the pattern that
        # propose_suffix_draft_token_ids reads.  We keep a clean copy here.
        self._suffix_response_tokens: dict[str, list[int]] = {}

        # Actual draft lengths per request from the previous step.  Used
        # by execute_model to trim the scheduler's spec token allocation
        # down to the real draft width, and communicated back to the
        # scheduler (via scheduler_output._actual_draft_lens) so
        # _update_after_schedule can set dynamic placeholder counts.
        self._prev_actual_draft_lens: dict[str, int] = {}

        # Backup-token buffer used by suffix-only async rejection sampling.
        # The arctic proposer has its own buffer; this one covers the case
        # where no arctic drafter is present.
        self._suffix_backup_tokens_gpu: Optional[torch.Tensor] = None
        if (self._suffix_cache is not None
                and self.use_async_scheduling
                and self.speculative_config.method not in ("arctic",
                                                           "mlp_speculator")):
            self._suffix_backup_tokens_gpu = torch.zeros(
                self.max_num_reqs, dtype=torch.int32, device=self.device,
            )

    def _suffix_only_rejection_sample(
        self,
        sampled_token_ids: torch.Tensor,
        common_attn_metadata: "CommonAttentionMetadata",
    ) -> None:
        """Rejection-sample accepted tokens for suffix-only async scheduling.

        EAGLE / arctic do this inside propose_draft_token_ids via
        prepare_next_token_ids_padded.  For suffix-only there is no
        drafter with that method, so we call the same Triton kernel
        directly and feed the results into _copy_valid_sampled_token_count.
        """
        from vllm.triton_utils import triton
        from vllm.v1.spec_decode.utils import (
            eagle_prepare_next_token_padded_kernel,
        )

        num_reqs = self.input_batch.num_reqs
        batch_size, num_tokens = sampled_token_ids.shape
        device = sampled_token_ids.device

        # Compute backup tokens (last accepted token per request) on CPU,
        # then copy to GPU in one shot to avoid per-element synchronisation.
        backup = self._suffix_backup_tokens_gpu
        assert backup is not None
        backup_np = np.empty(num_reqs, dtype=np.int32)
        for i in range(num_reqs):
            req_id = self.input_batch.req_ids[i]
            seq_len = int(common_attn_metadata.seq_lens_cpu[i].item())
            backup_np[i] = self.requests[req_id].get_token_id(seq_len)
        # Copy directly from CPU numpy-backed tensor to GPU; avoids
        # creating an intermediate GPU tensor via .to(device).
        backup[:num_reqs].copy_(
            torch.from_numpy(backup_np), non_blocking=True,
        )

        next_token_ids = torch.empty(batch_size, dtype=torch.int32,
                                     device=device)
        valid_counts = torch.empty(batch_size, dtype=torch.int32,
                                   device=device)

        BLOCK_SIZE_TOKENS = triton.next_power_of_2(num_tokens)
        eagle_prepare_next_token_padded_kernel[(batch_size,)](
            sampled_token_ids,
            self.discard_request_mask.gpu,
            backup,
            next_token_ids,
            valid_counts,
            self.model_config.get_vocab_size(),
            num_tokens,
            batch_size,
            sampled_token_ids.stride(0),
            BLOCK_SIZE_TOKENS=BLOCK_SIZE_TOKENS,
        )

        self._copy_valid_sampled_token_count(next_token_ids, valid_counts)

    def _build_attention_metadata(self, *args, **kwargs):
        attn_metadata, spec_decode_common_attn_metadata = \
            self._orig_build_attention_metadata(*args, **kwargs)

        logits_indices = kwargs.get("logits_indices", None)
        if logits_indices is not None:
            if isinstance(attn_metadata, list):
                for ub in attn_metadata:
                    for meta in ub.values():
                        meta.swiftkv_logits_indices = logits_indices
            else:
                for meta in attn_metadata.values():
                    meta.swiftkv_logits_indices = logits_indices

        return attn_metadata, spec_decode_common_attn_metadata

    # set padding for SP here
    def _pad_for_sequence_parallelism(self, num_scheduled_tokens: int) -> int:
        sp_size = self.parallel_config.ulysses_sequence_parallel_size
        num_input_tokens = round_up(num_scheduled_tokens, sp_size)
        return num_input_tokens

    def profile_run(self) -> None:
        self._orig_profile_run()
        if getattr(self, "shift_model", None) is not None:
            torch.distributed.barrier()
            orig_model, self.model = self.model, self.shift_model
            cc = self.vllm_config.compilation_config
            base_ctx = cc.static_forward_context
            shift_ctx = getattr(self, 'shift_forward_context', None)
            try:
                if shift_ctx is not None:
                    cc.static_forward_context = shift_ctx
                torch._dynamo.reset()
                with set_shift_parallel_mode(True):
                    self._dummy_run(self.max_num_tokens, is_profile=True)
            finally:
                self.model = orig_model
                cc.static_forward_context = base_ctx
            torch.distributed.barrier()

    def monkeypatch_forward(self: GPUModelRunner):
        """
        Slice the batch across Ulysses SP ranks for forward, then all-gather.
        """
        sp_size = parallel_state._SP.world_size
        sp_rank = parallel_state._SP.rank_in_group
        device_group = parallel_state._SP.device_group
        model_forward = self.model.forward
        input_key = 'inputs_embeds' if self.supports_mm_inputs else 'input_ids'

        @torch._dynamo.disable
        def ulysses_forward(*args, **kwargs):
            input_tensor = kwargs[input_key]
            positions = kwargs['positions']

            N = input_tensor.shape[0]
            N_ulysses = N // sp_size
            N_offset = N_ulysses * sp_rank

            kwargs[input_key] = input_tensor[N_offset:N_offset + N_ulysses]
            kwargs['positions'] = positions[N_offset:N_offset + N_ulysses]

            with set_shift_parallel_mode(False):
                output = model_forward(*args, **kwargs)

            if output.size(0) == N_ulysses:
                model_output = torch.empty((N, output.shape[1]),
                                           dtype=output.dtype,
                                           device=output.device)
                torch.distributed.all_gather_into_tensor(model_output,
                                                         output,
                                                         group=device_group)
            else:
                assert output.size(0) == N
                model_output = output
            return model_output

        self.get_model().forward = ulysses_forward

    @torch.inference_mode()
    def _dummy_run(
        self,
        num_tokens: int,
        cudagraph_runtime_mode: CUDAGraphMode | None = None,
        force_attention: bool = False,
        uniform_decode: bool = False,
        allow_microbatching: bool = True,
        skip_eplb: bool = False,
        is_profile: bool = False,
        create_mixed_batch: bool = False,
        remove_lora: bool = True,
        is_graph_capturing: bool = False,
        num_active_loras: int = 0,
        profile_seq_lens: int | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:

        mm_config = self.vllm_config.model_config.multimodal_config
        if mm_config and mm_config.mm_encoder_only:
            return torch.tensor([]), torch.tensor([])

        max_query_len = self.uniform_decode_query_len if uniform_decode else num_tokens
        max_num_reqs = self.scheduler_config.max_num_seqs

        if create_mixed_batch:
            num_decode_tokens = min(max_num_reqs - 1, num_tokens // 2)
            num_prefill_tokens = num_tokens - num_decode_tokens
            num_reqs = num_decode_tokens + 1
            num_scheduled_tokens_list = [1] * num_decode_tokens + [num_prefill_tokens]
            max_query_len = num_prefill_tokens
        elif uniform_decode:
            num_reqs = min(max_num_reqs, cdiv(num_tokens, max_query_len))
            num_scheduled_tokens_list = [max_query_len] * num_reqs
            if num_tokens % max_query_len != 0:
                num_scheduled_tokens_list[-1] = num_tokens % max_query_len
        else:
            num_reqs = min(num_tokens, max_num_reqs)
            min_tokens_per_req = num_tokens // num_reqs
            num_scheduled_tokens_list = [min_tokens_per_req] * num_reqs
            num_scheduled_tokens_list[-1] += num_tokens % num_reqs

        num_scheduled_tokens = np.array(num_scheduled_tokens_list, dtype=np.int32)
        num_tokens_unpadded = int(num_scheduled_tokens.sum())
        num_sampled_tokens = np.ones(num_reqs, dtype=np.int32)

        if torch.distributed.get_rank() == 0:
            print(f"num_tokens_unpadded: {num_tokens_unpadded}, num_reqs: {num_reqs}")

        _cg_mode, batch_desc, should_ubatch, num_tokens_across_dp, _ = (
            self._determine_batch_execution_and_padding(
                num_tokens=num_tokens_unpadded,
                num_reqs=num_reqs,
                num_scheduled_tokens_np=num_scheduled_tokens,
                max_num_scheduled_tokens=max_query_len,
                use_cascade_attn=False,
                allow_microbatching=allow_microbatching,
                force_eager=is_profile or (cudagraph_runtime_mode == CUDAGraphMode.NONE),
                force_uniform_decode=uniform_decode,
                force_has_lora=False,
            )
        )

        if cudagraph_runtime_mode is None:
            cudagraph_runtime_mode = _cg_mode

        num_tokens_padded = batch_desc.num_tokens
        num_reqs_padded = batch_desc.num_reqs if batch_desc.num_reqs is not None else num_reqs

        from vllm.v1.worker.gpu_model_runner import maybe_create_ubatch_slices
        ubatch_slices, ubatch_slices_padded = maybe_create_ubatch_slices(
            should_ubatch,
            num_scheduled_tokens,
            num_tokens_padded,
            num_reqs_padded,
            self.vllm_config.parallel_config.num_ubatches,
        )

        logits_indices_cpu = np.cumsum(num_scheduled_tokens) - 1
        logits_indices = torch.from_numpy(logits_indices_cpu).to(self.device)

        attn_metadata = None

        slot_mappings_by_group, slot_mappings = self._get_slot_mappings(
            num_tokens_padded=num_tokens_padded,
            num_reqs_padded=num_reqs_padded,
            num_tokens_unpadded=num_tokens_unpadded,
            ubatch_slices=ubatch_slices_padded,
        )

        if force_attention or cudagraph_runtime_mode == CUDAGraphMode.FULL:
            if create_mixed_batch:
                seq_lens = torch.tensor(
                    [1] * num_decode_tokens + [num_prefill_tokens + 1],
                    dtype=torch.int,
                )
            else:
                seq_lens = max_query_len

            # v0.24: self.seq_lens is now a plain GPU tensor staged through
            # self.optimistic_seq_lens_cpu (the .np/.copy_to_gpu buffer wrapper
            # was removed for seq_lens).
            self.optimistic_seq_lens_cpu[:num_reqs] = seq_lens
            self.optimistic_seq_lens_cpu[num_reqs:].fill_(0)
            self.seq_lens.copy_(self.optimistic_seq_lens_cpu, non_blocking=True)

            # v0.24: _get_cumsum_and_arange now requires an arange_out buffer
            # (writes the batched arange into it) and returns only the cumsum
            # (previously a (cumsum, arange) tuple).
            cum_num_tokens = self._get_cumsum_and_arange(
                num_scheduled_tokens, self.query_pos.np)
            self.query_start_loc.np[1 : num_reqs + 1] = cum_num_tokens
            self.query_start_loc.np[num_reqs + 1 : num_reqs_padded + 1].fill(
                cum_num_tokens[-1])
            self.query_start_loc.copy_to_gpu()

            pad_attn = (cudagraph_runtime_mode == CUDAGraphMode.FULL)
            attn_metadata, _ = self._build_attention_metadata(
                num_tokens=num_tokens_unpadded,
                num_tokens_padded=num_tokens_padded if pad_attn else None,
                num_reqs=num_reqs_padded,
                max_query_len=max_query_len,
                ubatch_slices=ubatch_slices_padded if pad_attn else ubatch_slices,
                for_cudagraph_capture=is_graph_capturing,
                slot_mappings=slot_mappings_by_group,
                use_spec_decode=self.speculative_config is not None,
            )

        if attn_metadata is not None:
            if isinstance(attn_metadata, list):
                for ub_meta in attn_metadata:
                    for meta in ub_meta.values():
                        meta.swiftkv_logits_indices = logits_indices
            else:
                for meta in attn_metadata.values():
                    meta.swiftkv_logits_indices = logits_indices

        with self.maybe_dummy_run_with_lora(self.lora_config, num_scheduled_tokens,
                                            num_sampled_tokens, False, remove_lora):

            model_kwargs = self._init_model_kwargs()
            if self.supports_mm_inputs and not self.model_config.is_encoder_decoder:
                input_ids, inputs_embeds = self._prepare_mm_inputs(num_tokens_padded)
                model_kwargs.update(self._dummy_mm_kwargs(num_reqs))
            elif self.enable_prompt_embeds:
                input_ids = None
                inputs_embeds = self.inputs_embeds.gpu[:num_tokens_padded]
            else:
                input_ids = self.input_ids.gpu[:num_tokens_padded]
                inputs_embeds = None

            positions = self.positions[:num_tokens_padded]  # v0.24: plain tensor
            if self.uses_mrope:
                positions = self.mrope_positions.gpu[:, :num_tokens_padded]

            intermediate_tensors = None
            if not get_pp_group().is_first_rank:
                if self.intermediate_tensors is None:
                    self.intermediate_tensors = self.model.make_empty_intermediate_tensors(
                        batch_size=self.max_num_tokens, dtype=self.model_config.dtype, device=self.device)
                intermediate_tensors = self.sync_and_gather_intermediate_tensors(num_tokens_padded, None, False)

            target_num_tokens = num_tokens_padded
            if ubatch_slices_padded is not None:
                target_num_tokens = ubatch_slices_padded[0].num_tokens
                if num_tokens_across_dp is not None:
                    num_tokens_across_dp[:] = target_num_tokens

            with self.maybe_randomize_inputs(input_ids, inputs_embeds), set_forward_context(
                attn_metadata, self.vllm_config, num_tokens=target_num_tokens,
                num_tokens_across_dp=num_tokens_across_dp, cudagraph_runtime_mode=cudagraph_runtime_mode,
                batch_descriptor=batch_desc, ubatch_slices=ubatch_slices_padded,
                slot_mapping=slot_mappings):

                outputs = self.model(input_ids=input_ids, positions=positions,
                                     intermediate_tensors=intermediate_tensors,
                                     inputs_embeds=inputs_embeds, **model_kwargs)

            hidden_states = outputs[0] if self.use_aux_hidden_state_outputs else outputs

            if self.speculative_config and self.speculative_config.use_eagle():
                self.drafter.dummy_run(num_tokens, use_cudagraphs=False, is_graph_capturing=is_graph_capturing)

        if not skip_eplb:
            self.eplb_step(is_dummy=True, is_profile=is_profile)

        if torch.cuda.current_device() != self.device.index:
            torch.cuda.set_device(self.device)

        return hidden_states, hidden_states[logits_indices]

    # ------------------------------------------------------------------
    # _sample: inline the base GPUModelRunner._sample logic here because
    # the class is monkey-patched at runtime, making both super() and
    # GPUModelRunner._sample(self, ...) resolve back to this method.
    # ------------------------------------------------------------------
    def _sample(
        self,
        logits: torch.Tensor | None,
        spec_decode_metadata: SpecDecodeMetadata | None,
    ) -> SamplerOutput:
        sampling_metadata = self.input_batch.sampling_metadata
        self.input_batch.update_async_output_token_ids()
        if spec_decode_metadata is None:
            return self.sampler(
                logits=logits, sampling_metadata=sampling_metadata)

        if (self.use_async_scheduling
                and self._draft_token_req_ids is not None):
            draft_token_ids_cpu, _ = self._get_draft_token_ids_cpu()
            self.input_batch.update_async_spec_token_ids(
                draft_token_ids_cpu)

        sampler_output = self.rejection_sampler(
            spec_decode_metadata,
            None,  # draft_probs
            logits,
            sampling_metadata,
        )
        return sampler_output

    @torch.inference_mode()
    def execute_model(
        self,
        scheduler_output: "SchedulerOutput",
        intermediate_tensors: Optional[IntermediateTensors] = None,
    ) -> Union[
        ModelRunnerOutput, AsyncGPUModelRunnerOutput, IntermediateTensors, None
    ]:
        num_scheduled_tokens = getattr(scheduler_output, "total_num_scheduled_tokens", None)
        if num_scheduled_tokens is None:
            try:
                num_scheduled_tokens = int(
                    sum(scheduler_output.num_scheduled_tokens.values())
                )
            except Exception:
                num_scheduled_tokens = 0

        use_shift_model = (
            getattr(self, "use_ulysses", False)
            and getattr(self, "shift_model", None) is not None
            and num_scheduled_tokens <= int(getattr(self, "shift_parallel_threshold", 0))
        )

        # Remember which model ran this step so sample_tokens -- where the final
        # ModelRunnerOutput / CUDAGraphStat is actually built -- can tag it.
        # (execute_model only returns an ExecuteModelState here.)
        self._arctic_shift_enabled = (
            getattr(self, "use_ulysses", False)
            and getattr(self, "shift_model", None) is not None
        )
        self._arctic_used_shift_model = use_shift_model

        if not use_shift_model:
            return self._orig_execute_model(scheduler_output, intermediate_tensors)

        orig_model = self.model
        cc = self.vllm_config.compilation_config
        base_ctx = cc.static_forward_context
        shift_ctx = getattr(self, 'shift_forward_context', None)
        try:
            self.model = self.shift_model
            if shift_ctx is not None:
                cc.static_forward_context = shift_ctx
            with set_shift_parallel_mode(True), \
                 self._use_shift_cudagraph_tables():
                result = self._orig_execute_model(scheduler_output, intermediate_tensors)
        finally:
            self.model = orig_model
            cc.static_forward_context = base_ctx

        self._fix_shift_logits_ordering()

        return result

    def _tag_cudagraph_stat_model(self, cudagraph_stats):
        """Return a copy of ``cudagraph_stats`` whose ``runtime_mode`` is
        annotated with which model (``base`` / ``shift``) executed this step,
        so per-step cudagraph metrics show it (e.g. ``PIECEWISE shift``).

        No-op (returns the input unchanged) when shift parallelism is disabled,
        no stat was produced (cudagraph metrics off), or the per-step flag was
        never stashed. ``CUDAGraphStat`` is frozen, hence the replaced copy.
        """
        if cudagraph_stats is None or not getattr(
                self, "_arctic_shift_enabled", False):
            return cudagraph_stats
        tag = "shift" if getattr(self, "_arctic_used_shift_model",
                                 False) else "base"
        try:
            return replace(
                cudagraph_stats,
                runtime_mode=f"{cudagraph_stats.runtime_mode} {tag}",
            )
        except Exception:
            return cudagraph_stats

    def _compute_shift_logits_perm(self):
        """Compute permutation to fix logits after all-gather for the shift model.

        NCCL all_gather_into_tensor outputs chunks in sorted global-rank order,
        but vLLM's GroupCoordinator assigns rank_in_group (and thus weight shards)
        based on the unsorted rank list.  When _SP_TP has non-trivial ordering
        (e.g. [0,2,1,3]), the vocabulary shards in the gathered logits are
        scrambled.  This method returns the permutation that restores correct
        vocabulary order, or None if no reordering is needed.
        """
        sp_tp = parallel_state._SP_TP
        if sp_tp is None:
            return None
        ranks = sp_tp.ranks
        sorted_ranks = sorted(ranks)
        if ranks == sorted_ranks:
            return None
        nccl_to_shard = [ranks.index(r) for r in sorted_ranks]
        perm = sorted(range(len(nccl_to_shard)), key=lambda i: nccl_to_shard[i])
        return perm

    def _fix_shift_logits_ordering(self):
        """Reorder logits vocabulary dimension to fix NCCL rank-sort mismatch."""
        perm = getattr(self, '_shift_logits_perm', None)
        if perm is None:
            return
        state = self.execute_model_state
        if state is None or state.logits is None:
            return
        logits = state.logits
        tp_size = len(perm)
        vocab_size = logits.shape[-1]
        if vocab_size % tp_size != 0:
            return
        shard_size = vocab_size // tp_size
        fixed = logits.view(-1, tp_size, shard_size)[:, perm, :].reshape_as(logits)
        logits.copy_(fixed)

    @torch.inference_mode
    def sample_tokens(self, grammar_output):
        """Wrapper around base sample_tokens for arctic async spec decode.

        Saves execute_model_state before the base clears it, then handles
        the 'not-fits-in-drafter' case that the base only handles for Eagle.
        """
        _arctic_saved_state = None
        if (self.execute_model_state is not None
                and self.speculative_config is not None
                and self.speculative_config.method
                    in ("arctic", "mlp_speculator", "suffix")
                and self.use_async_scheduling):
            _arctic_saved_state = (
                self.execute_model_state.scheduler_output,
                self.execute_model_state.spec_decode_common_attn_metadata,
            )

        result = self._orig_sample_tokens(grammar_output)

        # If _arctic_async_sampled_tensor was stashed by _bookkeeping_sync
        # but never consumed by propose_draft_token_ids, this is the
        # not-fits-in-drafter case.  Mirror Eagle's handling: call
        # _copy_valid_sampled_token_count and set draft tokens to zeros.
        stashed = getattr(self, '_arctic_async_sampled_tensor', None)
        if stashed is not None:
            del self._arctic_async_sampled_tensor
            if _arctic_saved_state is not None:
                scheduler_output, common_attn_meta = _arctic_saved_state
                self._arctic_handle_not_fits(
                    stashed, scheduler_output, common_attn_meta)

        return result

    def _arctic_handle_not_fits(
        self,
        sampled_token_ids: torch.Tensor,
        scheduler_output: "SchedulerOutput",
        common_attn_metadata,
    ) -> None:
        """Mirror Eagle's not-fits-in-drafter path for arctic async.

        When the input is too long for the drafter but spec decode is
        active, Eagle still calls prepare_next_token_ids_padded /
        _copy_valid_sampled_token_count and sets draft tokens to zeros.
        Without this, _get_valid_sampled_token_count returns stale counts
        and _prepare_input_ids scatters -1 placeholders into the
        embedding layer.
        """
        if (hasattr(self, 'drafter')
                and hasattr(self.drafter, 'prepare_next_token_ids_padded')
                and common_attn_metadata is not None):
            next_token_ids, valid_sampled_tokens_count = (
                self.drafter.prepare_next_token_ids_padded(
                    common_attn_metadata,
                    sampled_token_ids,
                    self.requests,
                    self.input_batch,
                    self.discard_request_mask.gpu,
                )
            )
            self._copy_valid_sampled_token_count(
                next_token_ids, valid_sampled_tokens_count)
        else:
            # Fallback for drafters without prepare_next_token_ids_padded
            # (e.g. suffix-only).  Compute valid counts with PyTorch ops.
            mask = sampled_token_ids != -1
            valid_counts = mask.sum(dim=1)
            batch_size = sampled_token_ids.shape[0]
            col_indices = torch.arange(
                sampled_token_ids.shape[1],
                device=sampled_token_ids.device,
            ).unsqueeze(0).expand_as(sampled_token_ids)
            last_valid_col = (
                col_indices.masked_fill(~mask, -1).max(dim=1).values)
            last_valid_col = last_valid_col.clamp(min=0)
            next_token_ids = sampled_token_ids[
                torch.arange(batch_size,
                             device=sampled_token_ids.device),
                last_valid_col,
            ]
            self._copy_valid_sampled_token_count(
                next_token_ids, valid_counts)

        # Zero draft tokens -- same as Eagle's not-fits path.
        self._draft_token_ids = torch.zeros(
            1, device=self.device, dtype=torch.int32,
        ).expand(len(self.input_batch.req_ids), self.num_spec_tokens)
        self._copy_draft_token_ids_to_cpu(
            scheduler_output, zeros_only=True)

    def _bookkeeping_sync(
        self,
        scheduler_output: "SchedulerOutput",
        sampler_output: SamplerOutput,
        logits: torch.Tensor | None,
        hidden_states: torch.Tensor,
        num_scheduled_tokens: int,
    ):
        """Wrap base _bookkeeping_sync to handle arctic async spec decode.

        In the base vLLM code, only Eagle-style drafters run *before*
        bookkeeping (setting prev_sampled_token_ids via
        _copy_valid_sampled_token_count).  Arctic/suffix drafting runs
        *after* bookkeeping, so prev_sampled_token_ids is still None
        when bookkeeping checks ``assert sampled_token_ids.shape[-1] == 1``.

        We fix this by:
          1. Saving the GPU sampled tensor for propose_draft_token_ids.
          2. Setting prev_sampled_token_ids to a placeholder so the
             assertion is skipped.  The real value will be written by
             _copy_valid_sampled_token_count inside propose_draft_token_ids
             (fits case) or sample_tokens (not-fits case).

        v0.24: ``spec_decode_metadata`` is no longer passed as an argument
        (the base signature dropped it and the return became a 7-tuple).
        We read it from the value stashed by our ``sample_tokens`` override.
        """
        spec_decode_metadata = getattr(
            self, "_arctic_spec_decode_metadata", None)
        sampled_token_ids = sampler_output.sampled_token_ids
        if (self.use_async_scheduling
                and self.speculative_config is not None
                and self.speculative_config.method
                    in ("arctic", "mlp_speculator", "suffix")
                and spec_decode_metadata is not None
                and sampled_token_ids.shape[-1] > 1
                and self.input_batch.prev_sampled_token_ids is None):
            # Stash the full GPU tensor so propose_draft_token_ids can
            # pick it up later (it normally only receives an empty list
            # in the post-bookkeeping path).
            self._arctic_async_sampled_tensor = sampled_token_ids
            # Placeholder: first column only (bonus token per request).
            # Prevents the assertion from firing; the correct value will
            # be overwritten by _copy_valid_sampled_token_count shortly.
            self.input_batch.prev_sampled_token_ids = (
                sampled_token_ids[:, :1])

        return self._orig_bookkeeping_sync(
            scheduler_output, sampler_output, logits, hidden_states,
            num_scheduled_tokens)

    def propose_draft_token_ids(
        self,
        scheduler_output: "SchedulerOutput",
        sampled_token_ids: torch.Tensor | list[list[int]],
        sampling_metadata: SamplingMetadata,
        hidden_states: torch.Tensor,
        sample_hidden_states: torch.Tensor,
        aux_hidden_states: list[torch.Tensor] | None,
        spec_decode_metadata: SpecDecodeMetadata | None,
        common_attn_metadata: CommonAttentionMetadata,
        slot_mappings=None,
    ) -> list[list[int]] | torch.Tensor:
        # In async mode, the base vLLM dispatches arctic to the
        # post-bookkeeping path which passes valid_sampled_token_ids
        # (an empty list for async).  Recover the stashed GPU tensor
        # so the fast async drafting path below can activate.
        if (isinstance(sampled_token_ids, list)
                and len(sampled_token_ids) == 0
                and hasattr(self, '_arctic_async_sampled_tensor')):
            sampled_token_ids = self._arctic_async_sampled_tensor
            del self._arctic_async_sampled_tensor

        # Compute the maximum number of requests to draft for.
        # When disable_by_batch_size is set and the batch exceeds it,
        # we still draft for the first N requests instead of disabling
        # entirely.  This avoids the stale-data crash that occurs when
        # drafting is fully disabled one step and re-enabled the next.
        batch_size = len(self.input_batch.req_ids)
        draft_limit = batch_size  # default: draft for all
        if self.speculative_config is not None:
            # Unified soft (disable_by_batch_size) + hard
            # (hard_disable_by_batch_size) caps. draft_limit==0 means SD is
            # hard-gated off this step: we still keep the spec pipeline alive
            # below and return a zero-filled draft.
            draft_limit = self.speculative_config.effective_draft_limit(
                batch_size)

        use_async_path = (
            self.speculative_config.method in ("arctic", "mlp_speculator")
            and isinstance(sampled_token_ids, torch.Tensor)
            and self.use_async_scheduling
            and common_attn_metadata is not None
        )

        if use_async_path:
            assert isinstance(sampled_token_ids, torch.Tensor)

            next_token_ids, valid_sampled_tokens_count = (
                self.drafter.prepare_next_token_ids_padded(
                    common_attn_metadata,
                    sampled_token_ids,
                    self.requests,
                    self.input_batch,
                    self.discard_request_mask.gpu,
                )
            )
            self._copy_valid_sampled_token_count(
                next_token_ids, valid_sampled_tokens_count
            )

            target_hidden_states = self.drafter.prepare_hidden_states(
                sample_hidden_states=sample_hidden_states,
                sampled_token_ids=sampled_token_ids,
                spec_decode_metadata=spec_decode_metadata,
            )

            # Hard gate: nobody drafts this step. Return an all-zeros draft
            # (the scheduler allocates no spec placeholders to match) without
            # invoking the drafter on an empty [:0] slice, which can choke
            # cudagraph replay / kernels. The prep calls above still run so
            # the async one-step-delayed verification state stays consistent.
            if draft_limit == 0:
                merged_buf = getattr(self, '_draft_merged_gpu', None)
                if merged_buf is not None:
                    draft = merged_buf[:batch_size]
                    draft.zero_()
                    return draft
                return torch.zeros(
                    batch_size, self.num_spec_tokens,
                    dtype=next_token_ids.dtype, device=next_token_ids.device,
                )

            # Only draft for the first draft_limit requests.
            raw_draft = self.drafter.propose(
                context_token_ids=next_token_ids[:draft_limit],
                previous_hidden_states=target_hidden_states[:draft_limit],
                num_predict_tokens=self.drafter.model.n_predict,
            )

            # Use pre-allocated GPU buffer when available.  This avoids
            # per-step F.pad + torch.zeros allocations.  The buffer is
            # [max_num_reqs, num_spec_tokens] so a single zero_() +
            # copy_() handles both width and batch padding in one shot.
            merged_buf = getattr(self, '_draft_merged_gpu', None)
            if merged_buf is not None:
                draft = merged_buf[:batch_size]
                draft.zero_()
                rd_rows, rd_cols = raw_draft.shape
                draft[:rd_rows, :rd_cols].copy_(raw_draft)
            else:
                draft = raw_draft
                if draft.shape[1] < self.num_spec_tokens:
                    draft = torch.nn.functional.pad(
                        draft,
                        (0, self.num_spec_tokens - draft.shape[1]),
                        value=0,
                    )
                if draft_limit < batch_size:
                    full_draft = torch.zeros(
                        batch_size, draft.shape[1],
                        dtype=draft.dtype, device=draft.device,
                    )
                    full_draft[:draft_limit] = draft
                    draft = full_draft
            return draft

        if isinstance(sampled_token_ids, torch.Tensor):
            vocab_size = self.model_config.get_vocab_size()
            sampled_token_ids_list = [
                [t for t in seq if t != -1 and t < vocab_size]
                for seq in sampled_token_ids.tolist()
            ]
            sampled_token_ids_tensor = sampled_token_ids
        else:
            sampled_token_ids_list = sampled_token_ids
            sampled_token_ids_tensor = None

        arctic_spec_token_ids = None
        suffix_spec_token_ids = None

        if self.speculative_config.method in ("arctic", "mlp_speculator"):
            if sampled_token_ids_tensor is None:
                sampled_token_ids_tensor = torch.tensor(sampled_token_ids_list, device=self.device)

            previous_hidden_states = self.drafter.prepare_hidden_states(
                sample_hidden_states=sample_hidden_states,
                sampled_token_ids=sampled_token_ids_tensor,
                spec_decode_metadata=spec_decode_metadata,
            )

            next_token_ids = self.drafter.prepare_next_token_ids_cpu(
                sampled_token_ids_list,
                self.requests,
                self.input_batch,
                scheduler_output.num_scheduled_tokens,
            )

            if draft_limit == 0:
                # Hard gate: no request drafts this step.
                arctic_spec_token_ids = [[] for _ in range(batch_size)]
            else:
                # Only draft for the first draft_limit requests.
                arctic_output_tensor = self.drafter.propose(
                    context_token_ids=next_token_ids[:draft_limit],
                    previous_hidden_states=previous_hidden_states[:draft_limit],
                    num_predict_tokens=self.drafter.model.n_predict,
                )

                arctic_spec_token_ids = arctic_output_tensor.tolist()
                # Pad with empty lists for requests beyond draft_limit.
                if draft_limit < batch_size:
                    arctic_spec_token_ids.extend(
                        [] for _ in range(batch_size - draft_limit)
                    )

        if self._suffix_cache is not None:
            self._update_suffix_cache(sampled_token_ids_list)
            results = self.propose_suffix_draft_token_ids(sampled_token_ids_list)

            suffix_spec_token_ids = []
            min_score = 0 if self.speculative_config.method == "suffix" \
                else self.drafter.model.n_predict

            for result in results:
                if result.score >= min_score:
                    suffix_spec_token_ids.append(result.token_ids)
                else:
                    suffix_spec_token_ids.append([])

        spec_token_ids = None
        if suffix_spec_token_ids is not None and arctic_spec_token_ids is not None:
            spec_token_ids = [
                s_tokens if s_tokens else a_tokens
                for s_tokens, a_tokens in zip(suffix_spec_token_ids, arctic_spec_token_ids)
            ]
        elif suffix_spec_token_ids is not None:
            spec_token_ids = suffix_spec_token_ids
        elif arctic_spec_token_ids is not None:
            spec_token_ids = arctic_spec_token_ids
        else:
            spec_token_ids = self._orig_propose_draft_token_ids(
                scheduler_output,
                sampled_token_ids_list,
                sampling_metadata,
                hidden_states,
                sample_hidden_states,
                aux_hidden_states,
                spec_decode_metadata,
                common_attn_metadata,
                slot_mappings,
            )

        if spec_token_ids is None:
             spec_token_ids = [[] for _ in range(len(self.input_batch.req_ids))]

        # For async scheduling the base _prepare_input_ids asserts that
        # _draft_token_ids is a torch.Tensor and uses it to scatter draft
        # tokens into the input.  If we reached here (non-async code path)
        # while async scheduling is active we must:
        #   1. Convert the list-of-lists draft tokens to a padded tensor.
        #   2. Call _copy_valid_sampled_token_count so the next step's
        #      _get_valid_sampled_token_count returns correct counts.
        if (self.use_async_scheduling
                and isinstance(spec_token_ids, list)
                and isinstance(sampled_token_ids, torch.Tensor)):
            # --- _copy_valid_sampled_token_count ---
            if (hasattr(self, 'drafter')
                    and hasattr(self.drafter, 'prepare_next_token_ids_padded')
                    and common_attn_metadata is not None):
                next_tok, valid_cnt = (
                    self.drafter.prepare_next_token_ids_padded(
                        common_attn_metadata,
                        sampled_token_ids,
                        self.requests,
                        self.input_batch,
                        self.discard_request_mask.gpu,
                    ))
                self._copy_valid_sampled_token_count(next_tok, valid_cnt)
            else:
                # Manual fallback (suffix-only drafter).
                mask = sampled_token_ids != -1
                valid_cnt = mask.sum(dim=1)
                _bs = sampled_token_ids.shape[0]
                cols = torch.arange(
                    sampled_token_ids.shape[1],
                    device=sampled_token_ids.device,
                ).unsqueeze(0).expand_as(sampled_token_ids)
                last_col = cols.masked_fill(~mask, -1).max(dim=1).values
                last_col = last_col.clamp(min=0)
                next_tok = sampled_token_ids[
                    torch.arange(_bs, device=sampled_token_ids.device),
                    last_col,
                ]
                self._copy_valid_sampled_token_count(next_tok, valid_cnt)

            # --- Convert list[list[int]] -> padded tensor ---
            padded = torch.zeros(
                batch_size, self.num_spec_tokens,
                dtype=torch.int32, device=self.device,
            )
            for i, tokens in enumerate(spec_token_ids):
                length = min(len(tokens), self.num_spec_tokens)
                if length > 0:
                    padded[i, :length] = torch.tensor(
                        tokens[:length], dtype=torch.int32,
                        device=self.device)
            spec_token_ids = padded

        return spec_token_ids

    def _update_suffix_cache(self, sampled_token_ids: list[list[int]]) -> None:
        seen_req_ids = set()
        for i, sampled_ids in enumerate(sampled_token_ids):
            req_id = self.input_batch.req_ids[i]
            seen_req_ids.add(req_id)

            if not sampled_ids:
                continue

            index = self.input_batch.req_id_to_index[req_id]
            is_new = req_id not in self._suffix_cache.active_requests
            if is_new:
                if req_id in self._suffix_cache.cached_requests:
                    self._suffix_cache.evict_cached_response(req_id)
                num_prompt_tokens = self.input_batch.num_prompt_tokens[index]
                prompt_token_ids = self.input_batch.token_ids_cpu[index, :num_prompt_tokens]
                self._suffix_cache.start_request(req_id, prompt_token_ids.tolist())
                self._suffix_response_tokens[req_id] = []

            self._suffix_cache.add_active_response(req_id, sampled_ids)
            self._suffix_response_tokens[req_id].extend(sampled_ids)

        stopped_ids = []
        for req_id in list(self._suffix_cache.active_requests):
            if req_id not in seen_req_ids:
                self._suffix_cache.stop_request(req_id)
                self._suffix_response_tokens.pop(req_id, None)
                stopped_ids.append(req_id)

    def propose_suffix_draft_token_ids(
        self,
        sampled_token_ids: list[list[int]],
    ) -> list[SuffixDecodingDraft]:
        config = self.speculative_config
        results = []
        for i, sampled_ids in enumerate(sampled_token_ids):
            num_sampled_ids = len(sampled_ids)
            if not num_sampled_ids:
                results.append(SuffixDecodingDraft())
                continue

            req_id = self.input_batch.req_ids[i]
            index = self.input_batch.req_id_to_index[req_id]

            # In async mode, token_ids_cpu contains -1 placeholders at
            # decoded positions (written by _bookkeeping_sync).  Build the
            # pattern from the clean _suffix_response_tokens instead.
            if (self.use_async_scheduling
                    and req_id in self._suffix_response_tokens):
                response = self._suffix_response_tokens[req_id]
                num_prompt = int(
                    self.input_batch.num_prompt_tokens[index])
                num_tokens = num_prompt + len(response)
                if num_tokens >= self.max_model_len:
                    results.append(SuffixDecodingDraft())
                    continue
                # Take up to suffix_cache_max_depth tokens from the tail.
                depth = config.suffix_cache_max_depth
                if len(response) >= depth:
                    pattern = response[-depth:]
                else:
                    need = depth - len(response)
                    prompt_start = max(0, num_prompt - need)
                    prompt_part = self.input_batch.token_ids_cpu[
                        index, prompt_start:num_prompt].tolist()
                    pattern = prompt_part + response
            else:
                num_tokens = self.input_batch.num_tokens_no_spec[i]
                if num_tokens >= self.max_model_len:
                    results.append(SuffixDecodingDraft())
                    continue
                start = max(0, num_tokens - config.suffix_cache_max_depth)
                pattern = self.input_batch.token_ids_cpu[
                    i, start:num_tokens].tolist()

            max_spec = min(
                MAX_SPEC_LEN, self.max_model_len - num_tokens - 1
            )
            result = self._suffix_cache.speculate(
                req_id,
                pattern,
                max_spec_tokens=max_spec,
                max_spec_factor=config.suffix_max_spec_factor,
                max_spec_offset=config.suffix_max_spec_offset,
                min_token_prob=config.suffix_min_token_prob,
            )

            results.append(result)

        return results

    def _start_suffix_copy(
        self,
        sampled_token_ids: torch.Tensor,
    ) -> None:
        """Initiate an async D2H copy of sampled token IDs for suffix decoding.

        Copies ``sampled_token_ids`` to a pinned CPU buffer on a dedicated
        CUDA stream (``suffix_copy_stream``) that only waits for prior work
        on the default stream (i.e. sampling).

        **This MUST be called BEFORE launching Arctic GPU work on the default
        stream** so that the copy is not ordered behind Arctic kernels.  The
        resulting timeline is::

            Default stream:  [sample] -> [arctic prepare / propose  ...]
            Suffix stream :  [sample] -> [D2H copy] -> [event]
            CPU            :                            wait -> suffix logic

        The companion ``_finish_suffix_copy`` synchronises on the copy event
        and returns the materialised CPU list.
        """
        n_rows = sampled_token_ids.shape[0]
        n_cols = sampled_token_ids.shape[-1]
        default_stream = torch.cuda.current_stream()
        with torch.cuda.stream(self.suffix_copy_stream):
            self.suffix_copy_stream.wait_stream(default_stream)
            self.suffix_sampled_ids_pinned[:n_rows, :n_cols].copy_(
                sampled_token_ids, non_blocking=True,
            )
            self.suffix_copy_done_event.record()
        self._suffix_copy_shape = (n_rows, n_cols)

    def _finish_suffix_copy(self) -> list[list[int]]:
        """Wait for the suffix copy and return sampled token IDs as CPU lists.

        Synchronises on the copy event recorded by ``_start_suffix_copy``,
        then parses the pinned buffer into ``list[list[int]]``, applying
        rejection-sampling for spec-decode batches and masking discarded
        (still-in-prefill) requests.
        """
        self.suffix_copy_done_event.synchronize()
        n_rows, n_cols = self._suffix_copy_shape
        pinned = self.suffix_sampled_ids_pinned[:n_rows, :n_cols]

        num_reqs = self.input_batch.num_reqs
        discard_indices = np.nonzero(
            self.discard_request_mask.np[:num_reqs]
        )[0]

        if n_cols == 1:
            result = pinned.tolist()
            for i in discard_indices:
                result[int(i)].clear()
        else:
            result, _ = RejectionSampler.parse_output(
                pinned,
                self.input_batch.vocab_size,
                discard_indices,
            )

        return result

    @torch.inference_mode
    def sample_tokens(
        self, grammar_output: "GrammarOutput | None"
    ) -> Union[ModelRunnerOutput, AsyncGPUModelRunnerOutput, IntermediateTensors]:
        kv_connector_output = self.kv_connector_output
        self.kv_connector_output = None

        if self.execute_model_state is None:
            # Nothing to do (PP non-final rank case), output isn't used.
            if not kv_connector_output:
                return None  # noqa

            # In case of PP with kv transfer, we need to pass through the
            # kv_connector_output
            if kv_connector_output.is_empty():
                return EMPTY_MODEL_RUNNER_OUTPUT

            output = copy.copy(EMPTY_MODEL_RUNNER_OUTPUT)
            output.kv_connector_output = kv_connector_output
            return output

        # Unpack ephemeral state -- v0.18 has 10 items including slot_mappings.
        (
            scheduler_output,
            logits,
            spec_decode_metadata,
            spec_decode_common_attn_metadata,
            hidden_states,
            sample_hidden_states,
            aux_hidden_states,
            ec_connector_output,
            cudagraph_stats,
            slot_mappings,
        ) = self.execute_model_state
        # Clear ephemeral state.
        self.execute_model_state = None

        # Tag the step's cudagraph stat with base/shift (set in execute_model)
        # so the per-step metrics line shows which model ran.
        cudagraph_stats = self._tag_cudagraph_stat_model(cudagraph_stats)

        # v0.24: the base ``_bookkeeping_sync`` no longer accepts
        # ``spec_decode_metadata`` as an argument.  Stash it on ``self`` so
        # our ``_bookkeeping_sync`` override can still gate the arctic async
        # spec-decode path on it.
        self._arctic_spec_decode_metadata = spec_decode_metadata

        # Apply structured output bitmasks if present.
        if grammar_output is not None:
            apply_grammar_bitmask(
                scheduler_output, grammar_output, self.input_batch, logits
            )

        with record_function_or_nullcontext("gpu_model_runner: sample"):
            sampler_output = self._sample(logits, spec_decode_metadata)

        self._update_states_after_model_execute(
            sampler_output.sampled_token_ids, scheduler_output)

        self._draft_token_ids = None
        self._draft_token_req_ids = None
        self.input_batch.prev_sampled_token_ids = None

        def propose_draft_token_ids(
            sampled_token_ids: torch.Tensor | list[np.ndarray],
        ) -> None:
            assert spec_decode_common_attn_metadata is not None
            with record_function_or_nullcontext("gpu_model_runner: draft"):
                self._draft_token_ids = self.propose_draft_token_ids(
                    scheduler_output,
                    sampled_token_ids,
                    self.input_batch.sampling_metadata,
                    hidden_states,
                    sample_hidden_states,
                    aux_hidden_states,
                    spec_decode_metadata,
                    spec_decode_common_attn_metadata,
                    slot_mappings,
                )
            self._copy_draft_token_ids_to_cpu(scheduler_output)

        # --- Draft proposal orchestration ---
        #
        # There are three drafting modes depending on async scheduling and
        # which drafters are active:
        #
        # A) Arctic-only + async:
        #      Pre-bookkeeping.  Arctic runs entirely on GPU tensors
        #      (the existing EAGLE-like async path).
        #
        # B) Suffix (with or without arctic) + async:
        #      Pre-bookkeeping.  Uses a *dedicated* suffix_copy_stream so
        #      that the D2H transfer of sampled token IDs only waits on
        #      "sampling complete" -- NOT on Arctic GPU work.  Timeline:
        #
        #        Default stream:  [sample] -> [arctic GPU work ----------->]
        #        Suffix  stream:  [sample] -> [D2H copy] -> [event]
        #        CPU            :                           wait -> suffix
        #
        #      At merge time, if any requests need arctic fallback, we
        #      sync on the arctic result (.tolist()); by then the GPU
        #      kernels have had the full suffix-CPU window to finish.
        #
        # C) Non-async (any combination):
        #      Post-bookkeeping.  propose_draft_token_ids handles everything
        #      using CPU valid_sampled_token_ids from bookkeeping.

        has_suffix = self._suffix_cache is not None
        is_arctic_method = (
            self.speculative_config is not None
            and self.speculative_config.method in ("arctic", "mlp_speculator")
        )
        input_fits_in_drafter = spec_decode_common_attn_metadata is not None
        sampled_token_ids = sampler_output.sampled_token_ids

        # Determine if we should use async pre-bookkeeping drafting.
        use_async_spec = (
            self.use_async_scheduling
            and self.speculative_config is not None
            and (is_arctic_method or has_suffix)
            and input_fits_in_drafter
        )

        if use_async_spec:
            if is_arctic_method and not has_suffix:
                # (A) Arctic-only async: use existing closure which calls
                #     propose_draft_token_ids (the method) with a GPU tensor
                #     and triggers the async GPU path internally.
                propose_draft_token_ids(sampled_token_ids)

                # Track actual draft lengths for next step's allocation.
                _n_predict = self.drafter.model.n_predict
                _batch_size = len(self.input_batch.req_ids)
                _draft_limit = (
                    self.speculative_config.effective_draft_limit(_batch_size)
                    if self.speculative_config else _batch_size
                )
                self._prev_actual_draft_lens = {
                    req_id: _n_predict if i < _draft_limit else 0
                    for i, req_id in enumerate(self.input_batch.req_ids)
                }
                scheduler_output._actual_draft_lens = (
                    self._prev_actual_draft_lens
                )

            elif is_arctic_method:
                # (B) Arctic + suffix async.
                #     D2H copy of sampled tokens runs on a dedicated
                #     suffix_copy_stream that only waits for sampling,
                #     NOT for Arctic GPU kernels enqueued afterwards.
                #     Suffix CPU work then overlaps with Arctic GPU.

                # Step 1: Initiate async D2H copy before Arctic GPU work.
                self._start_suffix_copy(sampled_token_ids)

                # Step 2: Launch arctic on the default stream.
                with record_function_or_nullcontext(
                    "gpu_model_runner: draft (arctic)"
                ):
                    arctic_draft = self.propose_draft_token_ids(
                        scheduler_output,
                        sampled_token_ids,
                        self.input_batch.sampling_metadata,
                        hidden_states,
                        sample_hidden_states,
                        aux_hidden_states,
                        spec_decode_metadata,
                        spec_decode_common_attn_metadata,
                        slot_mappings,
                    )

                # Step 3: Wait for D2H copy, then run suffix on CPU.
                #         This overlaps with remaining Arctic GPU work.
                with record_function_or_nullcontext(
                    "gpu_model_runner: draft (suffix)"
                ):
                    sampled_cpu = self._finish_suffix_copy()
                    self._update_suffix_cache(sampled_cpu)
                    suffix_results = self.propose_suffix_draft_token_ids(
                        sampled_cpu
                    )

                    min_score = self.drafter.model.n_predict
                    suffix_draft = [
                        result.token_ids if result.score >= min_score
                        else []
                        for result in suffix_results
                    ]

                # Step 4: Merge arctic + suffix results.
                #         Suffix takes priority when available.
                #
                #         The merged result MUST be a torch.Tensor on GPU
                #         because upstream _prepare_input_ids (next iteration)
                #         asserts isinstance(self._draft_token_ids, torch.Tensor)
                #         and uses it for on-device scatter.

                # Collect suffix rows that have results.
                suffix_indices = [
                    i for i, s in enumerate(suffix_draft) if s
                ]

                # arctic_draft is already a [batch, num_spec_tokens]
                # GPU tensor (from the pre-allocated _draft_merged_gpu
                # buffer when available, or F.pad fallback).
                if isinstance(arctic_draft, torch.Tensor):
                    merged = arctic_draft
                else:
                    # Shouldn't happen in async path, but handle
                    # gracefully.
                    k = self.num_spec_tokens
                    n = len(arctic_draft)
                    pin = self._suffix_merge_pinned[:n, :k]
                    pin_np = pin.numpy()
                    pin_np[:] = 0
                    for i, row in enumerate(arctic_draft):
                        t = row[:k]
                        if t:
                            pin_np[i, :len(t)] = t
                    merged = pin.to(
                        device=self.device, non_blocking=True)

                if merged.shape[1] < self.num_spec_tokens:
                    merged = torch.nn.functional.pad(
                        merged,
                        (0, self.num_spec_tokens - merged.shape[1]),
                        value=0,
                    )

                # Batch-overwrite rows that have suffix results.
                # CRITICAL: use the pre-allocated *pinned* merge
                # buffer so that cudaMemcpyAsync does NOT synchronise
                # the default stream.  With pageable (non-pinned)
                # memory CUDA must sync the stream first, blocking the
                # CPU until Arctic GPU work finishes -- destroying
                # the async overlap.
                width = merged.shape[1]
                if suffix_indices:
                    n_sfx = len(suffix_indices)
                    overlay_pin = \
                        self._suffix_merge_pinned[:n_sfx, :width]
                    overlay_np = overlay_pin.numpy()
                    overlay_np[:] = 0
                    for j, idx in enumerate(suffix_indices):
                        s = suffix_draft[idx]
                        slen = min(len(s), width)
                        overlay_np[j, :slen] = s[:slen]
                    # Pinned H2C -- truly non-blocking.
                    overlay_t = overlay_pin.to(
                        device=self.device, non_blocking=True)
                    # Use pre-allocated pinned index buffer when
                    # available to avoid per-step allocation.
                    idx_pinned = getattr(
                        self, '_suffix_index_pinned', None)
                    if idx_pinned is not None:
                        idx_pin = idx_pinned[:n_sfx]
                        idx_pin[:] = torch.tensor(
                            suffix_indices, dtype=torch.long)
                    else:
                        idx_pin = torch.tensor(
                            suffix_indices, dtype=torch.long
                        ).pin_memory()
                    idx_t = idx_pin.to(
                        device=self.device, non_blocking=True)
                    merged.index_copy_(0, idx_t, overlay_t)

                self._draft_token_ids = merged
                self._copy_draft_token_ids_to_cpu(scheduler_output)

                # Track actual draft lengths for next step's allocation.
                _n_predict = self.drafter.model.n_predict
                _batch_size = len(self.input_batch.req_ids)
                _draft_limit = (
                    self.speculative_config.effective_draft_limit(_batch_size)
                    if self.speculative_config else _batch_size
                )
                _actual_lens: dict[str, int] = {}
                for _i, _req_id in enumerate(self.input_batch.req_ids):
                    _s = (len(suffix_draft[_i])
                          if _i < len(suffix_draft) else 0)
                    _a = _n_predict if _i < _draft_limit else 0
                    # Suffix takes priority when available.
                    _actual_lens[_req_id] = _s if _s > 0 else _a
                self._prev_actual_draft_lens = _actual_lens
                scheduler_output._actual_draft_lens = _actual_lens

            else:
                # (B2) Suffix-only async.
                #      No Arctic GPU work to overlap with, so skip the
                #      copy stream (its overhead exceeds the marginal
                #      overlap with the lightweight rejection kernel).
                #      Instead: rejection sample → parse tokens directly
                #      → suffix CPU work → build GPU tensor via pinned buf.
                self._suffix_only_rejection_sample(
                    sampled_token_ids,
                    spec_decode_common_attn_metadata,
                )

                # Parse sampled tokens to CPU lists.  .cpu() syncs the
                # default stream (waits for the rejection kernel, which
                # is lightweight), then parse_output performs CPU-side
                # rejection to extract accepted token IDs.
                with record_function_or_nullcontext(
                    "gpu_model_runner: draft (suffix)"
                ):
                    num_reqs = self.input_batch.num_reqs
                    discard_indices = np.nonzero(
                        self.discard_request_mask.np[:num_reqs]
                    )[0]
                    n_cols = sampled_token_ids.shape[-1]
                    if n_cols == 1:
                        sampled_cpu = sampled_token_ids.tolist()
                        for idx in discard_indices:
                            sampled_cpu[int(idx)].clear()
                    else:
                        sampled_cpu, _ = RejectionSampler.parse_output(
                            sampled_token_ids.cpu(),
                            self.input_batch.vocab_size,
                            discard_indices,
                        )

                    self._update_suffix_cache(sampled_cpu)
                    suffix_results = self.propose_suffix_draft_token_ids(
                        sampled_cpu
                    )
                    suffix_draft = [
                        result.token_ids if result.score >= 0
                        else []
                        for result in suffix_results
                    ]

                # Build GPU tensor from suffix lists via pinned buffer.
                k = self.num_spec_tokens
                n = len(suffix_draft)
                pin = self._suffix_merge_pinned[:n, :k]
                pin_np = pin.numpy()
                pin_np[:] = 0
                for i, s in enumerate(suffix_draft):
                    if s:
                        slen = min(len(s), k)
                        pin_np[i, :slen] = s[:slen]
                self._draft_token_ids = pin.to(
                    device=self.device, non_blocking=True)
                self._copy_draft_token_ids_to_cpu(scheduler_output)

                # Track actual draft lengths for next step's allocation.
                _actual_lens_b2: dict[str, int] = {}
                for _i, _req_id in enumerate(self.input_batch.req_ids):
                    _s = (len(suffix_draft[_i])
                          if _i < len(suffix_draft) else 0)
                    _actual_lens_b2[_req_id] = _s
                self._prev_actual_draft_lens = _actual_lens_b2
                scheduler_output._actual_draft_lens = _actual_lens_b2

        # --- Bookkeeping ---
        with record_function_or_nullcontext("gpu_model_runner: bookkeep"):
            (
                num_nans_in_logits,
                logprobs_lists,
                valid_sampled_token_ids,
                prompt_logprobs_dict,
                req_ids_output_copy,
                req_id_to_index_output_copy,
                invalid_req_indices,
            ) = self._bookkeeping_sync(
                scheduler_output,
                sampler_output,
                logits,
                hidden_states,
                scheduler_output.total_num_scheduled_tokens,
            )

        # (C) Non-async drafting: run after bookkeeping.
        # Pass the raw GPU sampled_token_ids tensor (not the cleaned
        # valid_sampled_token_ids list) so that propose_draft_token_ids
        # gets a properly shaped 2-D tensor with -1 markers for rejected
        # tokens.  The method already handles tensors correctly: it
        # filters out -1 to build the CPU list for
        # prepare_next_token_ids_cpu and keeps the raw tensor for
        # prepare_hidden_states.
        if (
            self.speculative_config is not None
            and not use_async_spec
            and input_fits_in_drafter
        ):
            propose_draft_token_ids(sampled_token_ids)

        with record_function_or_nullcontext("gpu_model_runner: eplb"):
            self.eplb_step()

        with record_function_or_nullcontext("gpu_model_runner: ModelRunnerOutput"):
            if self.model_config.enable_return_routed_experts:
                capturer = RoutedExpertsCapturer.get_instance()
                if capturer is not None:
                    capturer.save_captured_experts(indices=self.slot_mapping)  # noqa
                else:
                    logger.error("RoutedExpertsCapturer not initialized.")

            output = ModelRunnerOutput(
                req_ids=req_ids_output_copy,
                req_id_to_index=req_id_to_index_output_copy,
                sampled_token_ids=valid_sampled_token_ids,
                logprobs=logprobs_lists,
                prompt_logprobs_dict=prompt_logprobs_dict,
                kv_connector_output=kv_connector_output,
                ec_connector_output=ec_connector_output
                if self.supports_mm_inputs
                else None,
                num_nans_in_logits=num_nans_in_logits,
                cudagraph_stats=cudagraph_stats,
            )
            # Attach actual draft lengths to the ModelRunnerOutput so the
            # scheduler can read them reliably in update_from_output.
            # This survives the async pipeline (scheduler_output attrs
            # may not due to object lifecycle in the batch queue).
            output._actual_draft_lens = getattr(
                scheduler_output, '_actual_draft_lens', None)

        if not self.use_async_scheduling:
            return output

        with record_function_or_nullcontext(
            "gpu_model_runner: AsyncGPUModelRunnerOutput"
        ):
            async_output = AsyncGPUModelRunnerOutput(
                model_runner_output=output,
                sampled_token_ids=sampler_output.sampled_token_ids,
                logprobs_tensors=sampler_output.logprobs_tensors,
                invalid_req_indices=invalid_req_indices,
                async_output_copy_stream=self.async_output_copy_stream,
                vocab_size=self.input_batch.vocab_size,
            )
        with record_function_or_nullcontext(
            "gpu_model_runner: set_async_sampled_token_ids"
        ):
            # Save ref of sampled_token_ids CPU tensor if the batch contains
            # any requests with sampling params that require output ids.
            self.input_batch.set_async_sampled_token_ids(
                async_output.sampled_token_ids_cpu,
                async_output.async_copy_ready_event,
            )

        return async_output

    def load_model(self, load_dummy_weights: bool = False) -> None:
        load_shift_model = (
            self.vllm_config.parallel_config.enable_shift_parallel
        )

        if load_shift_model:
            shift_config = copy.deepcopy(self.vllm_config)

        self._orig_load_model(load_dummy_weights)

        if self.parallel_config.ulysses_sequence_parallel_size > 1:
            self.monkeypatch_forward()

        if load_shift_model:
            shift_config.parallel_config.tensor_parallel_size *= (
                shift_config.parallel_config.ulysses_sequence_parallel_size
            )
            shift_config.parallel_config.ulysses_sequence_parallel_size = 1
            shift_config.compilation_config.pass_config.fuse_allreduce_rms = False
            with set_shift_parallel_mode(True):
                self.shift_model = get_model(vllm_config=shift_config)
            torch.cuda.set_device(self.device)
            self.shift_parallel_threshold = (
                shift_config.parallel_config.shift_parallel_threshold
            )
            self.shift_forward_context = (
                shift_config.compilation_config.static_forward_context
            )

            from vllm.distributed.device_communicators.cuda_communicator import (
                CudaCommunicator,
            )
            sp_tp = parallel_state._SP_TP
            if (sp_tp is not None
                    and sp_tp.device_communicator is not None
                    and isinstance(sp_tp.device_communicator, CudaCommunicator)
                    and sp_tp.device_communicator.ca_comm is not None):
                sp_tp.device_communicator.ca_comm.disabled = True

            self._shift_logits_perm = self._compute_shift_logits_perm()

            if "SwiftKV" in self.model.__class__.__name__:
                if hasattr(self.model, "model") and hasattr(self.model.model, "decode_runner"):
                    self.model.model.decode_runner = self.shift_model.model.decode_runner
                else:
                    logger.warning("Could not apply SwiftKV HACK: "
                                   "model.model.decode_runner not found.")

            cudagraph_mode = self.compilation_config.cudagraph_mode
            if (cudagraph_mode is not None
                    and cudagraph_mode.has_full_cudagraphs()
                    and not self.parallel_config.use_ubatching):
                from vllm.compilation.cuda_graph import CUDAGraphWrapper
                self.shift_model = CUDAGraphWrapper(
                    self.shift_model, self.vllm_config,
                    runtime_mode=CUDAGraphMode.FULL,
                )
        else:
            self.shift_model = None
            self.shift_parallel_threshold = 0
            self.shift_forward_context = None
            self._shift_logits_perm = None

    def reload_weights(self, *args, **kwargs) -> None:
        self._orig_reload_weights(*args, **kwargs)

        drafter = getattr(self, "drafter", None)
        if drafter is not None and getattr(drafter, "model", None) is not None:
            logger.info("Reloading drafter (spec model) weights...")
            drafter.load_model(self.model)

    def initialize_kv_cache(
        self, kv_cache_config, is_profiling: bool = False
    ) -> None:
        self._orig_initialize_kv_cache(kv_cache_config, is_profiling)
        shift_ctx = getattr(self, 'shift_forward_context', None)
        if shift_ctx is None:
            return
        base_ctx = self.compilation_config.static_forward_context
        bound = 0
        for name, shift_attn in shift_ctx.items():
            base_attn = base_ctx.get(name)
            if base_attn is not None and hasattr(base_attn, 'kv_cache'):
                shift_attn.kv_cache = base_attn.kv_cache
                bound += 1
        if is_global_first_rank():
            logger.info("Bound KV cache to %d shift model attention layers",
                        bound)

    from vllm.forward_context import BatchDescriptor
    def _case_bs(self, case) -> int:
        # vLLM can pass ints, tuples, or sometimes BatchDescriptor-like objects
        if isinstance(case, int):
            return case
        if isinstance(case, BatchDescriptor):
            return int(case.num_tokens)
        if isinstance(case, tuple):
            return int(case[0])
        # last resort
        return int(getattr(case, "num_tokens"))

    def _with_bs(self, case, new_bs: int):
        if isinstance(case, tuple):
            return (new_bs, *case[1:])
        if isinstance(case, BatchDescriptor):
            # Best-effort reconstruction; adjust if your BatchDescriptor signature differs.
            return BatchDescriptor(
                num_tokens=new_bs,
                num_reqs=case.num_reqs,
                uniform=case.uniform,
                has_lora=case.has_lora,
            )
        return new_bs

    @contextlib.contextmanager
    def _shift_graph_capture_context(self):
        """Disable custom all-reduce on _TP and _SP_TP during shift model graph
        capture so collectives fall back to pynccl (NCCL), which handles graph
        capture natively.  Custom all-reduce communicators were not set up through
        the normal vLLM graph_capture() path, so using them inside a CUDA graph
        would crash."""
        from vllm.distributed.device_communicators.cuda_communicator import (
            CudaCommunicator,
        )

        def _get_ca_comm(group):
            if (group is not None
                    and group.device_communicator is not None
                    and isinstance(group.device_communicator, CudaCommunicator)):
                return group.device_communicator.ca_comm
            return None

        tp_ca = _get_ca_comm(parallel_state._TP)
        sp_tp_ca = _get_ca_comm(parallel_state._SP_TP)

        saved_tp = tp_ca.disabled if tp_ca is not None else None
        saved_sp_tp = sp_tp_ca.disabled if sp_tp_ca is not None else None
        if tp_ca is not None:
            tp_ca.disabled = True
        if sp_tp_ca is not None:
            sp_tp_ca.disabled = True
        try:
            yield
        finally:
            if tp_ca is not None and saved_tp is not None:
                tp_ca.disabled = saved_tp
            if sp_tp_ca is not None and saved_sp_tp is not None:
                sp_tp_ca.disabled = saved_sp_tp

    @contextlib.contextmanager
    def _use_shift_cudagraph_tables(self):
        """Temporarily swap compilation_config sizes and the cudagraph
        dispatcher's padded-size lookup table to the shift (unscaled) values so
        vLLM internals (dispatcher, pad_for_cudagraph, bounds checks) all see the
        shift model's sizes."""
        disp = getattr(self, 'cudagraph_dispatcher', None)
        if disp is None or not hasattr(disp, '_bs_to_padded_graph_size'):
            yield
            return

        cc = self.compilation_config
        saved_sizes = cc.cudagraph_capture_sizes
        saved_max = cc.max_cudagraph_capture_size

        saved_table = disp._bs_to_padded_graph_size

        shift_sizes = self.vllm_config._shift_cudagraph_capture_sizes
        shift_max = self.vllm_config._shift_max_cudagraph_capture_size
        shift_table = self.vllm_config._shift_bs_to_padded_graph_size

        cc.cudagraph_capture_sizes = shift_sizes
        cc.max_cudagraph_capture_size = shift_max
        disp._bs_to_padded_graph_size = shift_table
        try:
            yield
        finally:
            cc.cudagraph_capture_sizes = saved_sizes
            cc.max_cudagraph_capture_size = saved_max
            disp._bs_to_padded_graph_size = saved_table

    def _shift_capture_descriptors(self, cudagraph_runtime_mode):
        """Build the shift model's cudagraph batch descriptors for a given
        runtime mode, matching exactly what runtime ``dispatch()`` and key
        registration produce.

        Must be called inside ``_use_shift_cudagraph_tables()`` so that
        ``_create_padded_batch_descriptor`` pads using the shift (unscaled)
        size table.  Descriptors are returned largest-first for capture memory
        efficiency (large shapes reuse the memory pool for smaller ones).

        - PIECEWISE: relaxed keys (``num_reqs=None, uniform=False``) over all
          shift capture sizes, mirroring the mixed-mode branch of base
          ``CudagraphDispatcher.initialize_cudagraph_keys``.
        - FULL: exact uniform-decode keys, restricted to the decode-eligible
          size subset (``uniform_decode_query_len <= bs <=
          uniform_decode_query_len * max_num_seqs``), mirroring base's
          ``cudagraph_capture_sizes_for_decode``.
        """
        disp = getattr(self, 'cudagraph_dispatcher', None)
        if disp is None or cudagraph_runtime_mode not in (
                CUDAGraphMode.PIECEWISE, CUDAGraphMode.FULL):
            return []

        shift_sizes = self.vllm_config._shift_cudagraph_capture_sizes or []
        sizes = sorted({int(bs) for bs in shift_sizes}, reverse=True)

        if cudagraph_runtime_mode == CUDAGraphMode.FULL:
            max_decode_tokens = (self.uniform_decode_query_len
                                 * self.scheduler_config.max_num_seqs)
            sizes = [bs for bs in sizes
                     if self.uniform_decode_query_len <= bs <= max_decode_tokens]

        lora_cases = disp._get_lora_cases()
        descriptors = []
        for bs in sizes:
            for num_active_loras in lora_cases:
                if cudagraph_runtime_mode == CUDAGraphMode.PIECEWISE:
                    desc = disp._create_padded_batch_descriptor(
                        bs, False, num_active_loras > 0, num_active_loras
                    )
                    desc = replace(desc, num_reqs=None, uniform=False)
                else:  # FULL (uniform decode) — exact match required.
                    desc = disp._create_padded_batch_descriptor(
                        bs, True, num_active_loras > 0, num_active_loras
                    )
                descriptors.append(desc)
        return descriptors

    def _register_shift_cudagraph_keys(self, batch_descriptors,
                                       cudagraph_runtime_mode):
        """Register cudagraph dispatch keys for the shift model so runtime
        dispatch finds the graphs captured for the shift model.

        Base vLLM only registers keys for the base (scaled) capture sizes in
        ``CudagraphDispatcher.initialize_cudagraph_keys``. The shift model
        captures a separate, unscaled size table, so those keys must be added
        explicitly.

        ``batch_descriptors`` must be the final descriptors produced by
        ``_shift_capture_descriptors`` (the same list passed to
        ``_orig_capture_cudagraphs``), so capture-key == registered-key ==
        runtime-dispatch-key.  Must run inside ``_use_shift_cudagraph_tables()``
        so the dispatcher's padded-size lookup matches what ``dispatch()``
        computes for shift batches at runtime.
        """
        disp = getattr(self, 'cudagraph_dispatcher', None)
        # add_cudagraph_key only accepts PIECEWISE / FULL.
        if disp is None or cudagraph_runtime_mode not in (
                CUDAGraphMode.PIECEWISE, CUDAGraphMode.FULL):
            return
        for desc in batch_descriptors:
            disp.add_cudagraph_key(cudagraph_runtime_mode, desc)

    def _capture_cudagraphs(
        self,
        batch_descriptors: list[BatchDescriptor],
        cudagraph_runtime_mode: CUDAGraphMode,
        profiler: Optional[contextlib.AbstractContextManager] = None,
    ):
        """
        Capture CUDA graphs for both base (Ulysses SP) and shift (TP-fused)
        variants, splitting shapes by threshold so both models have required
        graphs captured.  The shift path may profile-warmup with _dummy_run and
        capture at a possibly different runtime mode than the base model.
        """
        assert cudagraph_runtime_mode != CUDAGraphMode.NONE and \
            cudagraph_runtime_mode.is_valid_runtime_mode()

        sp_size = parallel_state._SP.world_size
        tp_size = parallel_state._TP.world_size
        threshold = int(getattr(self, "shift_parallel_threshold", 0))
        has_shift = getattr(self, "shift_model", None) is not None
        is_swiftkv = "SwiftKV" in self.model.__class__.__name__

        # --- Base model (Ulysses SP): uses the scaled lookup table (default) ---
        # Exclude sizes at or below the shift threshold -- those batches
        # are routed to the shift model at runtime.  Capturing them for the
        # base model would deadlock because the Ulysses all-to-all collectives
        # diverge across ranks at small batch sizes.
        if has_shift and not is_swiftkv:
            batch_descriptors_base = [
                case for case in batch_descriptors
                if self._case_bs(case) > threshold
            ]
        else:
            batch_descriptors_base = list(batch_descriptors)

        if is_global_first_rank():
            logger.info(
                "base model (SP=%s, TP=%s) cudagraph mode %s shapes %s",
                sp_size, tp_size, cudagraph_runtime_mode,
                [self._case_bs(c) for c in batch_descriptors_base],
            )

        if batch_descriptors_base:
            self._orig_capture_cudagraphs(
                batch_descriptors_base, cudagraph_runtime_mode, profiler=profiler
            )

        # --- Shift model (SP*TP fused as TP-only): uses the unscaled lookup table ---
        # The shift model captures its own *unscaled* sizes (e.g. [1, 2, ...,
        # 512]) from _shift_cudagraph_capture_sizes.  Descriptors are built via
        # _shift_capture_descriptors under _use_shift_cudagraph_tables() so the
        # padded sizes/keys exactly match what dispatch() computes for shift
        # batches at runtime.  The shift model is captured with the *same*
        # runtime mode as this pass (no downgrade): PIECEWISE in the piecewise
        # pass and FULL (decode-eligible sizes only) in the full pass.  FCA
        # never reaches the full pass because it forces cudagraph_mode to
        # PIECEWISE at engine-config creation (see args.py).
        if has_shift:
            torch.distributed.barrier()
            orig_model, self.model = self.model, self.shift_model
            cc = self.vllm_config.compilation_config
            base_ctx = cc.static_forward_context
            shift_ctx = getattr(self, 'shift_forward_context', None)
            batch_descriptors_shift = []
            try:
                if shift_ctx is not None:
                    cc.static_forward_context = shift_ctx
                torch._dynamo.reset()
                with set_shift_parallel_mode(True), \
                     self._use_shift_cudagraph_tables():
                    batch_descriptors_shift = self._shift_capture_descriptors(
                        cudagraph_runtime_mode
                    )
                    if is_global_first_rank():
                        logger.info(
                            "shift model (SPxTP=%s) cudagraph mode %s shapes %s",
                            sp_size * tp_size, cudagraph_runtime_mode,
                            [self._case_bs(c) for c in batch_descriptors_shift],
                        )
                    if batch_descriptors_shift:
                        max_shift = max(self._case_bs(c)
                                        for c in batch_descriptors_shift)
                        self._dummy_run(max_shift, is_profile=True)
                        torch.distributed.barrier()
                if batch_descriptors_shift:
                    with set_shift_parallel_mode(True), \
                         self._use_shift_cudagraph_tables(), \
                         self._shift_graph_capture_context():
                        self._register_shift_cudagraph_keys(
                            batch_descriptors_shift,
                            cudagraph_runtime_mode,
                        )
                        self._orig_capture_cudagraphs(
                            batch_descriptors_shift,
                            cudagraph_runtime_mode,
                            profiler=profiler,
                        )
            finally:
                self.model = orig_model
                cc.static_forward_context = base_ctx

        # Front-load the Arctic speculator's own CUDA graph cache (separate
        # from the base/shift graphs above) so it does not capture lazily
        # mid-run.  Runs after base+shift capture, with self.model restored
        # to the base model and outside shift-parallel mode.
        self._capture_arctic_speculator_cudagraphs()

    def _capture_arctic_speculator_cudagraphs(self) -> None:
        """
        Pre-capture the Arctic speculator's CUDA graphs over all request-count
        buckets during startup.

        The speculator keeps its own ``torch.cuda.CUDAGraph`` cache, separate
        from vLLM's base/shift graphs and captured lazily on first use of each
        padded request-count bucket inside ``generate_proposals``.  Left lazy,
        that capture happens mid-run whenever the running batch size steps into
        a not-yet-seen bucket, causing a one-step latency blip each time.
        Driving one dummy ``generate_proposals`` per bucket here front-loads
        every capture so runtime only ever replays.
        """
        drafter = getattr(self, "drafter", None)
        model = getattr(drafter, "model", None)
        # Skips SuffixProposer (no .model) and enforce_eager (cuda_graph_mode
        # is False).
        if model is None or not getattr(model, "cuda_graph_mode", False):
            return
        if (self.speculative_config is None
                or self.speculative_config.method
                not in ("arctic", "mlp_speculator")):
            return

        from arctic_inference.vllm.spec_dec.arctic_speculator import (
            padding_size)

        max_bs = int(getattr(model, "cuda_graph_max_batch_size", 0))
        if max_bs <= 0:
            return

        # Distinct padded request-count buckets, ascending.  padding_size is
        # idempotent on its own outputs, so these match the runtime cg_keys.
        buckets = sorted({padding_size(bs) for bs in range(1, max_bs + 1)})

        # Derive dummy-input width/dtype/device from the drafter's own static
        # buffer so this stays correct across the MLP and LSTM speculator
        # variants (they differ in hidden width and dtype).
        hidden = model.static_cuda_buffers["previous_hidden_states"]
        hidden_dim = hidden.shape[-1]
        device = hidden.device
        dtype = hidden.dtype
        n_predict = model.n_predict

        try:
            with torch.inference_mode():
                for bs in buckets:
                    input_ids = torch.zeros(bs, dtype=torch.long,
                                            device=device)
                    previous_hidden_states = torch.zeros(
                        bs, hidden_dim, dtype=dtype, device=device)
                    model.generate_proposals(
                        input_ids=input_ids,
                        previous_hidden_states=previous_hidden_states,
                        num_predict_tokens=n_predict,
                    )
            if is_global_first_rank():
                logger.info(
                    "arctic speculator pre-captured %d cudagraph buckets %s",
                    len(buckets), buckets,
                )
        except Exception as e:
            # A warmup failure must never crash engine init; fall back to the
            # existing lazy capture path.
            logger.warning(
                "arctic speculator cudagraph pre-capture skipped due to "
                "error: %s", e,
            )
