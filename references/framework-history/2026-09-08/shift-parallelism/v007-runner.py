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

import contextlib
import copy
import time
from typing import Union, Optional, TYPE_CHECKING

import torch
import vllm.distributed.parallel_state as parallel_state
from vllm.attention.layer import Attention
from vllm.config import CompilationLevel
from vllm.distributed.parallel_state import get_pp_group
from vllm.forward_context import set_forward_context
from vllm.config import VllmConfig
from vllm.model_executor.model_loader import get_model
from vllm.sequence import IntermediateTensors
from vllm.v1.kv_cache_interface import KVCacheConfig
from vllm.v1.outputs import EMPTY_MODEL_RUNNER_OUTPUT, ModelRunnerOutput
from vllm.v1.sample.rejection_sampler import MAX_SPEC_LEN
from vllm.v1.spec_decode.eagle import EagleProposer
from vllm.v1.spec_decode.ngram_proposer import NgramProposer
from vllm.v1.worker.gpu_model_runner import GPUModelRunner, logger

if TYPE_CHECKING:
    from vllm.v1.core.sched.output import SchedulerOutput

from arctic_inference.common.suffix_cache import SuffixCache
from arctic_inference.patching import ArcticPatch
from arctic_inference.vllm.spec_dec.arctic_proposer import ArcticProposer
from arctic_inference.common.suffix_cache import SuffixSpecResult

SP_TP_MODE = None


@contextlib.contextmanager
def set_shift_parallel_mode(mode: Optional[bool]):
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

    parallel_state._TP = (parallel_state._SP_TP if mode
                          else parallel_state._ORIG_TP)

    try:
        yield
    finally:
        # restore the original state
        SP_TP_MODE = old_mode
        parallel_state._TP = old_tp_group


def is_shift_parallel_mode() -> bool:
    """Check if the shift parallel mode is enabled."""
    global SP_TP_MODE
    return SP_TP_MODE is True


class GPUModelRunnerPatch(ArcticPatch[GPUModelRunner]):

    _orig_initialize_kv_cache = GPUModelRunner.initialize_kv_cache
    _orig_prepare_inputs = GPUModelRunner._prepare_inputs
    _orig_profile_run = GPUModelRunner.profile_run
    _orig_load_model = GPUModelRunner.load_model
    _orig_init = GPUModelRunner.__init__

    def __init__(self: GPUModelRunner, vllm_config: VllmConfig,
                 *args, **kwargs):

        speculative_config = vllm_config.speculative_config

        # Delay the creation of the drafter until
        # after the child class has been initialized.
        vllm_config.speculative_config = None
        self._orig_init(vllm_config, *args, **kwargs)

        # Set up speculative decoding.
        self._suffix_cache = None
        if speculative_config:
            self.use_spec_decode = True
            self.speculative_config = speculative_config
            self.vllm_config.speculative_config = speculative_config

            from vllm.distributed.parallel_state import get_pp_group
            if get_pp_group().is_last_rank:
                if self.speculative_config.method == "ngram":
                    self.drafter = NgramProposer(self.vllm_config)
                elif self.speculative_config.method == "eagle":
                    self.drafter = EagleProposer(self.vllm_config,
                                                 self.device)  # type: ignore
                elif (self.speculative_config.method == "arctic" or
                      self.speculative_config.method == "mlp_speculator"):
                    self.drafter = ArcticProposer(self.vllm_config)
                elif self.speculative_config.method != "suffix":
                    raise ValueError("Unknown speculative decoding method: "
                                     f"{self.speculative_config.method}")
                
                from vllm.v1.sample.rejection_sampler import RejectionSampler
                self.rejection_sampler = RejectionSampler()

            if speculative_config.enable_suffix_decoding:
                self._suffix_cache = SuffixCache(
                    speculative_config.suffix_cache_max_depth)

        vllm_config.speculative_config = speculative_config

    def profile_run(self) -> None:
        self._orig_profile_run()
        if self.shift_model is not None:
            # Run the shift model to trigger compilation.
            orig_model, self.model = self.model, self.shift_model
            try:
                with set_shift_parallel_mode(True):
                    self._dummy_run(self.max_num_tokens)
            finally:
                self.model = orig_model

    def _prepare_inputs(self, *args, **kwargs):
        attn_metadata, logits_indices, *rest = (
            self._orig_prepare_inputs(*args, **kwargs))
        # SwiftKV requires knowing the logits indices from inside the model
        # definition in order to early-stop the prefill tokens.
        attn_metadata.swiftkv_logits_indices = logits_indices
        return attn_metadata, logits_indices, *rest

    def monkeypatch_forward(self: GPUModelRunner):
        sp_size = parallel_state._SP.world_size
        sp_rank = parallel_state._SP.rank_in_group
        device_group = parallel_state._SP.device_group
        model_forward = self.model.forward

        def ulysses_forward(*args, **kwargs):
            # update inputs
            input_ids = kwargs['input_ids']
            positions = kwargs['positions']
            # Ulysses parameters
            N = input_ids.shape[0]

            N_ulysses = N // sp_size
            N_offset = N_ulysses * sp_rank

            # narrow the input
            kwargs['input_ids'] = input_ids[N_offset:N_offset + N_ulysses]
            kwargs['positions'] = positions[N_offset:N_offset + N_ulysses]

            with set_shift_parallel_mode(False):
                output = model_forward(*args, **kwargs)

            if output.size(0) == N_ulysses:
                # all-gather model_output
                model_output = torch.empty((N, self.model.config.hidden_size),
                                        dtype=output.dtype,
                                        device=output.device)
                torch.distributed.all_gather_into_tensor(model_output,
                                                        output,
                                                        group=device_group)
            else:
                # SwiftKV models will already have all-gathered the output.
                assert output.size(0) == N
                model_output = output
            return model_output

        self.model.forward = ulysses_forward

    def load_model(self: GPUModelRunner, *args, **kwargs):
        load_shift_model = (
            self.vllm_config.parallel_config.enable_shift_parallel)

        if load_shift_model:
            # Make a deep copy of the config before loading the model.
            shift_config = copy.deepcopy(self.vllm_config)

        self._orig_load_model(*args, **kwargs)

        if self.parallel_config.ulysses_sequence_parallel_size > 1:
            self.monkeypatch_forward()

        if load_shift_model:
            shift_config.parallel_config.tensor_parallel_size *= (
                shift_config.parallel_config.ulysses_sequence_parallel_size)
            shift_config.parallel_config.ulysses_sequence_parallel_size = 1
            with set_shift_parallel_mode(True):
                self.shift_model = get_model(vllm_config=shift_config)
            self.shift_parallel_threshold = (
                shift_config.parallel_config.shift_parallel_threshold)
            if "SwiftKV" in self.model.__class__.__name__:
                # HACK: Replace the decode-runner since it always runs in full
                # TP, but the original model is captured using SP * BATCH_SIZE,
                # which does not cover all its cuda graph sizes. The shift-mode
                # model should have all its cuda graphs captured correctly.
                self.model.model.decode_runner = (
                    self.shift_model.model.decode_runner)
        else:
            self.shift_model = None
            self.shift_parallel_threshold = 0

    def initialize_kv_cache(self, kv_cache_config: "KVCacheConfig") -> None:
        self._orig_initialize_kv_cache(kv_cache_config)

        if self.shift_model is not None:
            # Bind the KV caches to the shift parallel model.
            forward_context = (
                self.vllm_config.compilation_config.static_forward_context)
            for mod in self.shift_model.modules():
                if isinstance(mod, Attention):
                    mod.kv_cache = forward_context[mod.layer_name].kv_cache

    @torch.inference_mode()
    def execute_model(
        self: GPUModelRunner,
        scheduler_output: "SchedulerOutput",
        intermediate_tensors: Optional[IntermediateTensors] = None,
    ) -> Union[ModelRunnerOutput, torch.Tensor]:
        self._update_states(scheduler_output)
        if not scheduler_output.total_num_scheduled_tokens:
            # Return empty ModelRunnerOutput if there's no work to do.
            return EMPTY_MODEL_RUNNER_OUTPUT

        if self.is_multimodal_model:
            # Run the multimodal encoder if any.
            self._execute_mm_encoder(scheduler_output)
            mm_embeds = self._gather_mm_embeddings(scheduler_output)
        else:
            mm_embeds = []

        # Prepare the decoder inputs.
        attn_metadata, logits_indices, spec_decode_metadata = (
            self._prepare_inputs(scheduler_output))
        num_scheduled_tokens = scheduler_output.total_num_scheduled_tokens
        use_shift_model = num_scheduled_tokens <= self.shift_parallel_threshold
        if use_shift_model:
            if (self.use_cuda_graph and num_scheduled_tokens
                    <= self.cudagraph_batch_sizes[-1]):
                # Use piecewise CUDA graphs.
                # Add padding to the batch size.
                num_input_tokens = self.vllm_config.pad_for_cudagraph(
                    num_scheduled_tokens)
            else:
                # Eager mode.
                num_input_tokens = num_scheduled_tokens
        else:
            # add padding to the batch size to make it a multiple of SP
            SP = self.parallel_config.ulysses_sequence_parallel_size
            num_input_tokens = (num_scheduled_tokens + SP - 1) // SP * SP
            if (self.use_cuda_graph and num_input_tokens // SP
                    <= self.cudagraph_batch_sizes[-1]):
                num_input_tokens = SP * self.vllm_config.pad_for_cudagraph(
                    num_input_tokens // SP)
            else:
                pass
        attn_metadata.num_input_tokens = num_input_tokens

        if self.is_multimodal_model:
            # NOTE(woosuk): To unify token ids and soft tokens (vision
            # embeddings), we always use embeddings (rather than token ids)
            # as input to the multimodal model, even when the input is text.
            input_ids = self.input_ids[:num_scheduled_tokens]
            if mm_embeds:
                inputs_embeds = self.model.get_input_embeddings(
                    input_ids, mm_embeds)
            else:
                inputs_embeds = self.model.get_input_embeddings(input_ids)
            # TODO(woosuk): Avoid the copy. Optimize.
            self.inputs_embeds[:num_scheduled_tokens].copy_(inputs_embeds)
            inputs_embeds = self.inputs_embeds[:num_input_tokens]
            input_ids = None
        else:
            # For text-only models, we use token ids as input.
            # While it is possible to use embeddings as input just like the
            # multimodal models, it is not desirable for performance since
            # then the embedding layer is not included in the CUDA graph.
            input_ids = self.input_ids[:num_input_tokens]
            inputs_embeds = None
        if self.uses_mrope:
            positions = self.mrope_positions[:, :num_input_tokens]
        else:
            positions = self.positions[:num_input_tokens]

        if get_pp_group().is_first_rank:
            intermediate_tensors = None
        else:
            assert intermediate_tensors is not None
            assert self.intermediate_tensors is not None
            for k, v in intermediate_tensors.items():
                self.intermediate_tensors[k][:num_input_tokens].copy_(
                    v[:num_input_tokens], non_blocking=True)
            intermediate_tensors = IntermediateTensors({
                k: v[:num_input_tokens]
                for k, v in self.intermediate_tensors.items()
            })

        # Run the decoder.
        # Use persistent buffers for CUDA graphs.
        with (set_forward_context(attn_metadata, self.vllm_config),
                set_shift_parallel_mode(use_shift_model)):
            if use_shift_model:
                hidden_states = self.shift_model(
                    input_ids=input_ids,
                    positions=positions,
                    intermediate_tensors=intermediate_tensors,
                    inputs_embeds=inputs_embeds,
                )
            else:
                hidden_states = self.model(
                    input_ids=input_ids,
                    positions=positions,
                    intermediate_tensors=intermediate_tensors,
                    inputs_embeds=inputs_embeds,
                )
        if not get_pp_group().is_last_rank:
            # For mid-pipeline stages, return the hidden states.
            return hidden_states

        hidden_states = hidden_states[:num_scheduled_tokens]
        sample_hidden_states = hidden_states[logits_indices]
        logits = self.model.compute_logits(sample_hidden_states, None)

        # Apply structured output bitmasks if present
        if scheduler_output.grammar_bitmask is not None:
            self.apply_grammar_bitmask(scheduler_output, logits)

        # Sample the next token and get logprobs if needed.
        sampling_metadata = self.input_batch.sampling_metadata
        if spec_decode_metadata is None:
            sampler_output = self.model.sample(
                logits=logits,
                sampling_metadata=sampling_metadata,
            )
        else:
            # When indexing with a tensor (bonus_logits_indices), PyTorch
            # creates a new tensor with separate storage from the original
            # logits tensor. This means any in-place operations on bonus_logits
            # won't affect the original logits tensor.
            bonus_logits = logits[spec_decode_metadata.bonus_logits_indices]
            sampler_output = self.model.sample(
                logits=bonus_logits,
                sampling_metadata=sampling_metadata,
            )
            bonus_token_ids = sampler_output.sampled_token_ids

            # Just like `bonus_logits`, `target_logits` is a new tensor with
            # separate storage from the original `logits` tensor. Therefore,
            # it is safe to update `target_logits` in place.
            target_logits = logits[spec_decode_metadata.target_logits_indices]
            output_token_ids = self.rejection_sampler(
                spec_decode_metadata,
                None,  # draft_probs
                target_logits,
                bonus_token_ids,
                sampling_metadata,
            )
            sampler_output.sampled_token_ids = output_token_ids

        # TODO(woosuk): The following loop can be slow since it iterates over
        # the requests one by one. Optimize.
        discard_sampled_tokens_req_indices = []
        for i, req_id in enumerate(self.input_batch.req_ids):
            req_state = self.requests[req_id]
            seq_len = (req_state.num_computed_tokens +
                       scheduler_output.num_scheduled_tokens[req_id])
            if seq_len < req_state.num_tokens:
                # Ignore the sampled token for partial prefills.
                # Rewind the generator state as if the token was not sampled.
                # This relies on cuda-specific torch-internal impl details
                generator = self.input_batch.generators.get(i)
                if generator is not None:
                    generator.set_offset(generator.get_offset() - 4)
                # Record the index of the request that should not be sampled,
                # so that we could clear the sampled tokens before returning.
                discard_sampled_tokens_req_indices.append(i)

        # NOTE: GPU -> CPU Sync happens here.
        # Move as many CPU operations as possible before this sync point.
        logprobs_tensors = sampler_output.logprobs_tensors
        logprobs_lists = logprobs_tensors.tolists() \
            if logprobs_tensors is not None else None

        # Compute prompt logprobs if needed.
        prompt_logprobs_dict = self._get_prompt_logprobs_dict(
            hidden_states,
            scheduler_output,
        )

        # Get the valid generated tokens.
        sampled_token_ids = sampler_output.sampled_token_ids
        max_gen_len = sampled_token_ids.shape[-1]
        if max_gen_len == 1:
            # No spec decode tokens.
            valid_sampled_token_ids = sampled_token_ids.tolist()
        else:
            # Includes spec decode tokens.
            valid_sampled_token_ids = self.rejection_sampler.parse_output(
                sampled_token_ids,
                self.input_batch.vocab_size,
            )
        # Mask out the sampled tokens that should not be sampled.
        for i in discard_sampled_tokens_req_indices:
            valid_sampled_token_ids[i].clear()

        disable_spec_decode = (
            self.speculative_config and
            self.speculative_config.disable_by_batch_size and
            len(self.input_batch.req_ids) > self.speculative_config.disable_by_batch_size
        )

        suffix_spec_token_ids = None
        orig_sampled_token_ids = valid_sampled_token_ids.copy()
        if self._suffix_cache is not None:
            self._update_suffix_cache(valid_sampled_token_ids)
            if not disable_spec_decode:
                results = self.generate_draft_token_ids_suffix(
                    valid_sampled_token_ids)
                suffix_spec_token_ids = []
                # The score is an estimate of the acceptance length. Thus, the
                # heuristic is to use the suffix decoded tokens if the score is
                # greater than the # of tokens we would speculate otherwise.
                min_score = (self.speculative_config.num_speculative_tokens
                             if self.speculative_config.method != "suffix"
                             else 0)
                min_score = (0 if self.speculative_config.method == "suffix"
                             else self.speculative_config.num_speculative_tokens)
                for i, result in enumerate(results):
                    if result.score >= min_score:
                        # Use suffix decoded tokens, disable other speculation
                        # methods for this request.
                        valid_sampled_token_ids[i] = []
                        suffix_spec_token_ids.append(result.token_ids)
                    else:
                        suffix_spec_token_ids.append([])

        spec_token_ids = None
        if not self.use_spec_decode or disable_spec_decode:
            # Speculative decoding is not enabled.
            pass
        elif self.speculative_config.method == "ngram":
            assert isinstance(self.drafter, NgramProposer)
            spec_token_ids = self.generate_draft_token_ids(
                valid_sampled_token_ids, sampling_metadata)
        elif (self.speculative_config.method == "arctic" or 
              self.speculative_config.method == "mlp_speculator"):
            assert isinstance(self.drafter, ArcticProposer)
            previous_hidden_states = self.drafter.prepare_hidden_states(
                sample_hidden_states=sample_hidden_states,
                sampled_token_ids=sampled_token_ids,
                spec_decode_metadata=spec_decode_metadata,
            )
            spec_token_ids = self.generate_draft_token_ids_arctic(
                valid_sampled_token_ids, 
                previous_hidden_states=previous_hidden_states)
        elif self.speculative_config.method == "eagle":
            assert isinstance(self.drafter, EagleProposer)
            # TODO(woosuk): Refactor the loop.
            next_token_ids: list[int] = []
            for i, token_ids in enumerate(valid_sampled_token_ids):
                if token_ids:
                    # Common case.
                    next_token_id = token_ids[-1]
                else:
                    # Partial prefill (rare case).
                    # Get the next token id from the request state.
                    req_id = self.input_batch.req_ids[i]
                    req_state = self.requests[req_id]
                    seq_len = (req_state.num_computed_tokens +
                               scheduler_output.num_scheduled_tokens[req_id])
                    next_token_id = req_state.get_token_id(seq_len)
                next_token_ids.append(next_token_id)
            next_token_ids = torch.tensor(next_token_ids,
                                          dtype=torch.int32,
                                          device=self.device)

            if spec_decode_metadata is None:
                # input_ids can be None for multimodal models.
                # We need to slice token_ids, positions, and hidden_states
                # because the eagle head does not use cuda graph and should
                # not include padding.
                target_token_ids = self.input_ids[:num_scheduled_tokens]
                target_positions = positions[:num_scheduled_tokens]
                target_hidden_states = hidden_states[:num_scheduled_tokens]
                target_slot_mapping = attn_metadata.slot_mapping
                cu_num_tokens = attn_metadata.query_start_loc
            else:
                # TODO(woosuk): Refactor this.
                num_draft_tokens = spec_decode_metadata.num_draft_tokens
                num_rejected_tokens = [
                    n + 1 - len(valid_sampled_token_ids[i]) if n > 0 else 0
                    for i, n in enumerate(num_draft_tokens)
                ]
                num_rejected_tokens = torch.tensor(
                    num_rejected_tokens,
                    dtype=torch.int32,
                    device=self.device,
                )
                cu_num_tokens, token_indices = self.drafter.prepare_inputs(
                    attn_metadata.query_start_loc,
                    num_rejected_tokens,
                )
                target_token_ids = self.input_ids[token_indices]
                target_positions = positions[token_indices]
                target_hidden_states = hidden_states[token_indices]
                target_slot_mapping = attn_metadata.slot_mapping[token_indices]

            draft_token_ids, draft_probs = self.drafter.propose(
                target_token_ids=target_token_ids,
                target_positions=target_positions,
                target_hidden_states=target_hidden_states,
                target_slot_mapping=target_slot_mapping,
                next_token_ids=next_token_ids,
                cu_num_tokens=cu_num_tokens,
                block_table=attn_metadata.block_table,
                sampling_metadata=sampling_metadata,
            )
            spec_token_ids = draft_token_ids.tolist()
            # TODO(woosuk): Cache draft_probs and use it for rejection sampling
            # in the next step.
            del draft_probs

        if spec_token_ids is None:
            spec_token_ids = suffix_spec_token_ids
        elif suffix_spec_token_ids is not None:
            spec_token_ids = [
                suffix_spec_token_ids[i] or spec_token_ids[i]
                for i in range(len(suffix_spec_token_ids))
            ]

        valid_sampled_token_ids = orig_sampled_token_ids

        return ModelRunnerOutput(
            req_ids=self.input_batch.req_ids,
            req_id_to_index=self.input_batch.req_id_to_index,
            sampled_token_ids=valid_sampled_token_ids,
            spec_token_ids=spec_token_ids,
            logprobs=logprobs_lists,
            prompt_logprobs_dict=prompt_logprobs_dict,
        )
    
    def generate_draft_token_ids_arctic(
        self,
        sampled_token_ids: list[list[int]],
        previous_hidden_states: Optional[torch.Tensor] = None,
    ) -> list[list[int]]:
        last_tokens : list[int] = []
        for i, sampled_ids in enumerate(sampled_token_ids):
            num_sampled_ids = len(sampled_ids)
            
            if (num_sampled_ids == 0):
                # uncommmon case
                return None

            # Add sampled_token_ids to token_ids_cpu.
            start_idx = self.input_batch.num_tokens_no_spec[i]
            end_idx = start_idx + num_sampled_ids
            self.input_batch.token_ids_cpu[i, start_idx:end_idx] = sampled_ids
            last_tokens.append(self.input_batch.token_ids_cpu[i, end_idx - 1])

        drafter_output = self.drafter.propose(
            last_tokens,
            previous_hidden_states=previous_hidden_states,
        )

        draft_token_ids = drafter_output.tolist()

        for i, sampled_ids in enumerate(sampled_token_ids):
            if not sampled_ids:
                draft_token_ids[i] = []

        return draft_token_ids

    def _update_suffix_cache(self, sampled_token_ids: list[list[int]]) -> None:
        seen_req_ids = set()
        for i, sampled_ids in enumerate(sampled_token_ids):
            req_id = self.input_batch.req_ids[i]
            seen_req_ids.add(req_id)

            if not sampled_ids:
                continue

            index = self.input_batch.req_id_to_index[req_id]
            if not self._suffix_cache.has_cached_prompt(req_id):
                num_prompt_tokens = self.input_batch.num_prompt_tokens[index]
                prompt_token_ids = (
                    self.input_batch.token_ids_cpu[index, :num_prompt_tokens])
                self._suffix_cache.cache_prompt(req_id, prompt_token_ids)

            self._suffix_cache.update_response(req_id, sampled_ids)

        # Evict prompts that are not seen
        for req_id in self._suffix_cache.cached_prompt_ids():
            if req_id not in seen_req_ids:
                self._suffix_cache.evict_prompt(req_id)

    def generate_draft_token_ids_suffix(
        self,
        sampled_token_ids: list[list[int]],
        spec_token_ids: Optional[list[list[int]]] = None,
    ) -> list[list[int]]:
        config = self.speculative_config
        results = []
        for i, sampled_ids in enumerate(sampled_token_ids):
            spec_ids = spec_token_ids[i] if spec_token_ids is not None else []
            num_sampled_ids = len(sampled_ids)
            if not num_sampled_ids:
                # Skip speculative decoding.
                results.append(SuffixSpecResult())
                continue

            req_id = self.input_batch.req_ids[i]

            # Add sampled_token_ids to token_ids_cpu.
            start_idx = self.input_batch.num_tokens_no_spec[i]
            end_idx = start_idx + len(sampled_ids)
            self.input_batch.token_ids_cpu[i, start_idx:end_idx] = sampled_ids

            size = min(end_idx, config.suffix_cache_max_depth)
            pattern = self.input_batch.token_ids_cpu[i, end_idx-size:end_idx]
            pattern = pattern.tolist() + spec_ids
            if len(pattern) > config.suffix_cache_max_depth:
                pattern = pattern[-config.suffix_cache_max_depth:]
            max_spec_tokens = min(MAX_SPEC_LEN - len(spec_ids),
                                  config.suffix_cache_max_depth,
                                  self.max_model_len - end_idx - 1)
            # max_spec_offset is modified to mimic the behavior of the original
            # max_spec_factor and max_spec_offset as if the speculative tokens
            # were generated by suffix decoding. For example, if:
            #   - max_spec_factor = 2
            #   - max_spec_offset = -1
            #   - we've already speculated 3 tokens
            #   - and the suffix match length is 6
            # Then:
            #   - The match length before the already-speculated tokens is 3
            #   - The original config allow up to 5 speculated tokens total
            #   - Already speculated 3 tokens, so should allow 2 more tokens
            # So the new config should map match length 6 to 2 max spec tokens.
            max_spec_factor = config.suffix_max_spec_factor
            max_spec_offset = (config.suffix_max_spec_offset -
                              len(spec_ids) * (max_spec_factor + 1))
            result = self._suffix_cache.speculate(
                req_id,
                pattern,
                max_spec_tokens=max_spec_tokens,
                max_spec_factor=max_spec_factor,
                max_spec_offset=max_spec_offset,
                min_token_prob=config.suffix_min_token_prob)

            results.append(result)

        return results

    def capture_model(self) -> None:
        if not self.use_cuda_graph:
            logger.warning(
                "Skipping CUDA graph capture. Please add "
                "-O %s to use CUDA graphs.", CompilationLevel.PIECEWISE)
            return

        start_time = time.perf_counter()
        start_free_gpu_memory = torch.cuda.mem_get_info()[0]

        # Trigger CUDA graph capture for specific shapes.
        # Capture the large shapes first so that the smaller shapes
        # can reuse the memory pool allocated for the large shapes.
        with parallel_state.graph_capture(device=self.device):
            sp_size = self.parallel_config.ulysses_sequence_parallel_size
            for num_tokens in reversed(self.cudagraph_batch_sizes):
                if (num_tokens * sp_size > self.shift_parallel_threshold and
                        num_tokens * sp_size <= self.max_num_tokens):
                    for _ in range(self.vllm_config.compilation_config.
                                   cudagraph_num_of_warmups):
                        self._dummy_run(num_tokens * sp_size)
                    self._dummy_run(num_tokens * sp_size)

            if self.shift_model is not None:
                orig_model, self.model = self.model, self.shift_model
                for num_tokens in reversed(self.cudagraph_batch_sizes):
                    with set_shift_parallel_mode(True):
                        for _ in range(self.vllm_config.compilation_config.
                                        cudagraph_num_of_warmups):
                            self._dummy_run(num_tokens)
                        self._dummy_run(num_tokens)
                self.model = orig_model

        end_time = time.perf_counter()
        end_free_gpu_memory = torch.cuda.mem_get_info()[0]
        elapsed_time = end_time - start_time
        cuda_graph_size = start_free_gpu_memory - end_free_gpu_memory
        # This usually takes 5~20 seconds.
        logger.info("Graph capturing finished in %.0f secs, took %.2f GiB",
                    elapsed_time, cuda_graph_size / (1 << 30))

