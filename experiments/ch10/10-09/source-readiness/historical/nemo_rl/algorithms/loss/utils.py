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

from typing import Any, Optional

import torch

from nemo_rl.algorithms.logits_sampling_utils import (
    TrainingSamplingParams,
    need_top_k_or_top_p_filtering,
)
from nemo_rl.algorithms.loss.interfaces import LossFunction, LossInputType
from nemo_rl.algorithms.utils import mask_out_neg_inf_logprobs
from nemo_rl.distributed.batched_data_dict import BatchedDataDict
from nemo_rl.distributed.model_utils import (
    _get_packed_thd_tokens_on_this_cp_rank,
    from_parallel_logits_to_logprobs_packed_sequences,
    get_distillation_topk_logprobs_from_logits,
    get_next_token_logprobs_from_logits,
)


def prepare_loss_input(
    logits: torch.Tensor,
    data: BatchedDataDict[Any],
    loss_fn: LossFunction,
    vocab_parallel_rank: Optional[int] = None,
    vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    sampling_params: Optional[TrainingSamplingParams] = None,
    d2t: Optional[torch.Tensor] = None,
) -> tuple[dict[str, Any], BatchedDataDict[Any]]:
    """Prepare loss input for a loss function.

    Args:
        logits: Logits from the model.
        data: Microbatch data. Will be updated if sampling_params is not None.
        loss_fn: Loss function.
        vocab_parallel_rank: Vocab parallel rank.
        vocab_parallel_group: Vocab parallel group.
        context_parallel_group: Context parallel group.
        sampling_params: Sampling parameters.
        d2t: Draft to target token mapping.

    Notes:
        vocab_parallel_rank, vocab_parallel_group, context_parallel_group are only used for megatron policy worker.
        sampling_params is only used for LossInputType.LOGPROB, and currently only supported for ClippedPGLossFn.
        d2t is only used for LossInputType.DRAFT.

    Returns:
        tuple(loss_input, maybe_updated_data)
    """
    if loss_fn.input_type == LossInputType.LOGIT:
        loss_input = {"logits": logits}

    elif loss_fn.input_type == LossInputType.LOGPROB:
        # Linear CE fusion patch returns precomputed next-token logprobs (2D tensor).
        # Keep normal path unchanged for standard logits (3D tensor).
        if hasattr(loss_fn, "use_linear_ce_fusion") and loss_fn.use_linear_ce_fusion:
            logprobs = logits
            logprobs = logprobs.to(torch.float32)
            logprobs = logprobs[:, : data["input_ids"].shape[1] - 1]
        else:
            logprobs = get_next_token_logprobs_from_logits(
                input_ids=data["input_ids"],
                next_token_logits=logits,
                seq_index=data.get("seq_index", None),
                vocab_parallel_rank=vocab_parallel_rank,
                vocab_parallel_group=vocab_parallel_group,
                context_parallel_group=context_parallel_group,
                sampling_params=sampling_params,
                cu_seqlens_padded=data.get("_packed_cp_cu_seqlens_padded", None),
            )

        # handle top-k/top-p filtering for logprobs, only used for ClippedPGLossFn now
        if need_top_k_or_top_p_filtering(sampling_params):
            # mask out negative infinity logprobs
            # prev_logprobs is already masked out in the previous step
            mask = data["token_mask"] * data["sample_mask"].unsqueeze(-1)
            logprobs = mask_out_neg_inf_logprobs(logprobs, mask[:, 1:], "curr_logprobs")

            # compute unfiltered logprobs for reference policy KL penalty
            if (
                hasattr(loss_fn, "reference_policy_kl_penalty")
                and loss_fn.reference_policy_kl_penalty != 0
            ):
                data["curr_logprobs_unfiltered"] = get_next_token_logprobs_from_logits(
                    input_ids=data["input_ids"],
                    next_token_logits=logits,
                    seq_index=data.get("seq_index", None),
                    vocab_parallel_rank=vocab_parallel_rank,
                    vocab_parallel_group=vocab_parallel_group,
                    context_parallel_group=context_parallel_group,
                    sampling_params=None,  # no filtering
                    cu_seqlens_padded=data.get("_packed_cp_cu_seqlens_padded", None),
                )

        loss_input = {"next_token_logprobs": logprobs}

    elif loss_fn.input_type == LossInputType.DISTILLATION:
        calculate_entropy = loss_fn.zero_outside_topk and loss_fn.kl_type != "forward"
        student_topk_logprobs, teacher_topk_logprobs, H_all = (
            get_distillation_topk_logprobs_from_logits(
                student_logits=logits,
                teacher_topk_logits=data["teacher_topk_logits"],
                teacher_topk_indices=data["teacher_topk_indices"],
                zero_outside_topk=loss_fn.zero_outside_topk,
                calculate_entropy=calculate_entropy,
                vocab_parallel_rank=vocab_parallel_rank,
                vocab_parallel_group=vocab_parallel_group,
                context_parallel_group=context_parallel_group,
            )
        )

        loss_input = {
            "student_topk_logprobs": student_topk_logprobs,
            "teacher_topk_logprobs": teacher_topk_logprobs,
            "H_all": H_all,
        }
    elif loss_fn.input_type == LossInputType.DISTILLATION_CROSS_TOKENIZER:
        # Materialize the teacher-side loss input: rebuild the microbatch's
        # full-vocab teacher logits from the CUDA IPC handles shipped on the
        # data dict. The student logits pass straight through; the loss fn
        # does the projection / chunk-average / KL reductions on both.
        from nemo_rl.algorithms.x_token.loss_utils import (
            rebuild_teacher_full_logits_from_ipc,
        )

        loss_input = {
            "logits": logits,
            "teacher_full_logits": rebuild_teacher_full_logits_from_ipc(data),
        }
    elif loss_fn.input_type == LossInputType.DRAFT:
        from megatron.core.transformer.multi_token_prediction import roll_tensor

        teacher_logits = roll_tensor(
            logits.detach(),
            shifts=-1,
            dims=1,
            cp_group=context_parallel_group,
        )[0]
        token_mask = roll_tensor(
            data["token_mask"], shifts=-1, dims=1, cp_group=context_parallel_group
        )[0]
        if d2t is not None:
            reverse_mapping = (
                torch.arange(len(d2t), device=teacher_logits.device, dtype=d2t.dtype)
                + d2t
            )
            if vocab_parallel_group is not None:
                from megatron.core.tensor_parallel import (
                    gather_from_tensor_model_parallel_region,
                )

                teacher_logits = gather_from_tensor_model_parallel_region(
                    teacher_logits, vocab_parallel_group
                )
                tp_size = torch.distributed.get_world_size(vocab_parallel_group)
                local_draft_size = len(d2t) // tp_size
                assert vocab_parallel_rank is not None
                start_index = vocab_parallel_rank * local_draft_size
                end_index = (vocab_parallel_rank + 1) * local_draft_size
                reverse_mapping = reverse_mapping[start_index:end_index]
            teacher_logits = teacher_logits[:, :, reverse_mapping]
        loss_input = {
            "teacher_logits": teacher_logits,
            "student_logits": data["student_logits"],
            "token_mask": token_mask,
        }

    else:
        raise ValueError(f"Unknown loss function input type: {loss_fn.input_type}")

    return loss_input, data


def _pack_input_ids(
    input_ids: torch.Tensor,
    cu_seqlens_q: torch.Tensor,
    cu_seqlens_q_padded: torch.Tensor,
    cp_rank: int = 0,
    cp_size: int = 1,
    roll_shift: int = 0,
) -> torch.Tensor:
    """Pack input_ids from [B, S] to [1, T_packed // CP] using sequence boundaries.

    Each sequence is individually padded to its padded length (from
    cu_seqlens_q_padded), optionally rolled, and CP-sharded at that padded
    length before being placed into the packed output.  This matches how
    Megatron packs and CP-shards sequences in _pack_sequences_for_megatron.

    Args:
        input_ids: Unpacked input IDs [B, S].
        cu_seqlens_q: Unpadded cumulative sequence lengths [B+1].
        cu_seqlens_q_padded: Padded cumulative sequence lengths [B+1].
        cp_rank: Context parallelism rank.
        cp_size: Context parallelism size.
        roll_shift: If non-zero, roll each padded sequence by this amount
            before CP-sharding.  Use -1 to build shifted targets for
            next-token prediction.
    """
    batch_size = input_ids.shape[0]
    total_packed_len = int(cu_seqlens_q_padded[-1].item())
    packed = torch.zeros(
        total_packed_len, dtype=input_ids.dtype, device=input_ids.device
    )
    for i in range(batch_size):
        actual_len = int((cu_seqlens_q[i + 1] - cu_seqlens_q[i]).item())
        padded_len = int((cu_seqlens_q_padded[i + 1] - cu_seqlens_q_padded[i]).item())
        packed_start = int(cu_seqlens_q_padded[i].item())
        seq = torch.zeros(padded_len, dtype=input_ids.dtype, device=input_ids.device)
        seq[:actual_len] = input_ids[i, :actual_len]
        if roll_shift != 0:
            seq = seq.roll(shifts=roll_shift, dims=0)
        packed[packed_start : packed_start + padded_len] = seq

    return _get_packed_thd_tokens_on_this_cp_rank(
        packed.unsqueeze(0),
        cu_seqlens_q_padded,
        cp_rank,
        cp_size,
        seq_dim=1,
    )


def prepare_packed_loss_input(
    logits: torch.Tensor,
    data: BatchedDataDict[Any],
    loss_fn: LossFunction,
    cu_seqlens_q: torch.Tensor,
    cu_seqlens_q_padded: torch.Tensor,
    vocab_parallel_rank: Optional[int] = None,
    vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    sampling_params: Optional[TrainingSamplingParams] = None,
) -> tuple[dict[str, Any], BatchedDataDict[Any]]:
    """Prepare loss input from packed logits in a single fused pass.

    Unlike prepare_loss_input which operates on a single (unpacked) sequence,
    this function computes log probabilities from packed logits across all
    sequences at once using from_parallel_logits_to_logprobs_packed_sequences.

    Currently only supports LossInputType.LOGPROB.

    Args:
        logits: Packed logits from the model [1, T_packed // CP, V // TP].
        data: Microbatch data (unpacked, [B, S]).
        loss_fn: Loss function (must have input_type == LossInputType.LOGPROB).
        cu_seqlens_q: Unpadded cumulative sequence lengths [B+1].
        cu_seqlens_q_padded: Padded cumulative sequence lengths [B+1].
        vocab_parallel_rank: Vocab parallel rank.
        vocab_parallel_group: Vocab parallel group.
        context_parallel_group: Context parallel group.
        sampling_params: Sampling parameters.

    Returns:
        tuple(loss_input, maybe_updated_data)
    """
    if loss_fn.input_type != LossInputType.LOGPROB:
        raise ValueError(
            f"prepare_packed_loss_input only supports LossInputType.LOGPROB, "
            f"got {loss_fn.input_type}. Use SequencePackingLossWrapper with "
            f"prepare_loss_input for other types."
        )
    assert vocab_parallel_group is not None, (
        "prepare_packed_loss_input requires vocab_parallel_group (Megatron TP)."
    )
    assert vocab_parallel_rank is not None, (
        "vocab_parallel_rank must be provided with vocab_parallel_group."
    )

    input_ids = data["input_ids"]
    unpacked_seqlen = input_ids.shape[1]
    cp_size = (
        1
        if context_parallel_group is None
        else torch.distributed.get_world_size(context_parallel_group)
    )
    cp_rank = (
        0
        if context_parallel_group is None
        else torch.distributed.get_rank(context_parallel_group)
    )

    packed_rolled_targets = _pack_input_ids(
        input_ids,
        cu_seqlens_q,
        cu_seqlens_q_padded,
        cp_rank=cp_rank,
        cp_size=cp_size,
        roll_shift=-1,
    )

    logprobs = from_parallel_logits_to_logprobs_packed_sequences(
        logits.to(torch.float32),
        packed_rolled_targets,
        cu_seqlens_q_padded,
        unpacked_seqlen,
        vocab_start_index=vocab_parallel_rank * logits.shape[-1],
        vocab_end_index=(vocab_parallel_rank + 1) * logits.shape[-1],
        group=vocab_parallel_group,
        inference_only=False,
        cp_group=context_parallel_group,
        sampling_params=sampling_params,
        target_is_pre_rolled=True,
    )

    # Match prepare_loss_input behavior for top-k/top-p filtered training:
    # use filtered curr_logprobs for actor loss, but keep unfiltered values for KL.
    if need_top_k_or_top_p_filtering(sampling_params):
        mask = data["token_mask"] * data["sample_mask"].unsqueeze(-1)
        logprobs = mask_out_neg_inf_logprobs(logprobs, mask[:, 1:], "curr_logprobs")

        if (
            hasattr(loss_fn, "reference_policy_kl_penalty")
            and loss_fn.reference_policy_kl_penalty != 0
        ):
            data["curr_logprobs_unfiltered"] = (
                from_parallel_logits_to_logprobs_packed_sequences(
                    logits.to(torch.float32),
                    packed_rolled_targets,
                    cu_seqlens_q_padded,
                    unpacked_seqlen,
                    vocab_start_index=vocab_parallel_rank * logits.shape[-1],
                    vocab_end_index=(vocab_parallel_rank + 1) * logits.shape[-1],
                    group=vocab_parallel_group,
                    inference_only=False,
                    cp_group=context_parallel_group,
                    sampling_params=None,
                    target_is_pre_rolled=True,
                )
            )

    return {"next_token_logprobs": logprobs}, data
