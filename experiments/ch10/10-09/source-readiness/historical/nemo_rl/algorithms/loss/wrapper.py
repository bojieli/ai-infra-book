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

import math
from typing import Any, Callable, Optional, TypeVar

import torch
import torch.distributed

from nemo_rl.algorithms.loss.interfaces import LossFunction
from nemo_rl.algorithms.loss.loss_functions import DraftCrossEntropyLossFn
from nemo_rl.distributed.batched_data_dict import BatchedDataDict

Tensor = TypeVar("Tensor", bound=torch.Tensor)


class SequencePackingLossWrapper:
    def __init__(
        self,
        loss_fn: LossFunction,
        prepare_fn: Callable[Any, Any],
        cu_seqlens_q: Tensor,
        cu_seqlens_q_padded: Optional[Tensor] = None,
        vocab_parallel_rank: Optional[int] = None,
        vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
        context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    ):
        """Wrap a loss function to handle sequence packing.

        Args:
            loss_fn: Loss function.
            prepare_fn: Prepare function.
            cu_seqlens_q: Unpadded cu seqlens q.
            cu_seqlens_q_padded: Padded cu seqlens q.
            vocab_parallel_rank: Vocab parallel rank.
            vocab_parallel_group: Vocab parallel group.
            context_parallel_group: Context parallel group.

            vocab_parallel_rank, vocab_parallel_group, context_parallel_group are only used for megatron policy worker.

        Returns:
            Sequence packing loss wrapper.
        """
        self.loss_fn = loss_fn
        self.prepare_fn = prepare_fn
        self.cu_seqlens_q = cu_seqlens_q
        self.cu_seqlens_q_padded = cu_seqlens_q_padded
        self.vocab_parallel_rank = vocab_parallel_rank
        self.vocab_parallel_group = vocab_parallel_group
        self.context_parallel_group = context_parallel_group

    def __call__(
        self,
        next_token_logits: Tensor,
        data: BatchedDataDict[Any],
        global_valid_seqs: Tensor | None,
        global_valid_toks: Tensor | None,
    ) -> tuple[Tensor, dict[str, Any]]:
        """Wraps a loss function to handle sequence packing by doing one sequence at a time to avoid excessive padding."""
        unpadded_cu_seqlens = self.cu_seqlens_q
        unpadded_seq_lengths = self.cu_seqlens_q[1:] - self.cu_seqlens_q[:-1]
        if self.cu_seqlens_q_padded is not None:
            padded_cu_seqlens = self.cu_seqlens_q_padded
            padded_seq_lengths = (
                self.cu_seqlens_q_padded[1:] - self.cu_seqlens_q_padded[:-1]
            )
        else:
            padded_cu_seqlens = unpadded_cu_seqlens
            padded_seq_lengths = unpadded_seq_lengths
        seq_starts = padded_cu_seqlens[:-1]
        seq_ends = padded_cu_seqlens[1:]

        loss_accum = 0
        metrics_accum = {}
        for seq_idx in range(len(seq_starts)):
            seq_start = seq_starts[seq_idx].item()
            seq_end = seq_ends[seq_idx].item()

            # get sequence and unpad all 'data' tensors. The data dict is a BatchedDataDict of unpacked tensors
            seq_data = data.slice(seq_idx, seq_idx + 1)
            unpadded_seq_data = {}
            for k, v in seq_data.items():
                if isinstance(v, torch.Tensor) and v.ndim > 1 and v.shape[1] > 1:
                    unpadded_seq_data[k] = v[:, : unpadded_seq_lengths[seq_idx]]
                else:
                    unpadded_seq_data[k] = v

            cp_size = (
                1
                if self.context_parallel_group is None
                else torch.distributed.get_world_size(self.context_parallel_group)
            )
            if cp_size > 1 and self.cu_seqlens_q_padded is not None:
                unpadded_seq_data["_packed_cp_cu_seqlens_padded"] = torch.tensor(
                    [0, int(padded_seq_lengths[seq_idx].item())],
                    dtype=torch.int32,
                    device=next_token_logits.device,
                )
            # prepare data for loss function
            if (
                hasattr(self.loss_fn, "use_linear_ce_fusion")
                and self.loss_fn.use_linear_ce_fusion
            ):
                # Linear CE fusion returns precomputed token logprobs where shape
                # can be shorter by 1 token than padded sequence metadata.
                # Use slicing (clamped end) to avoid narrow() OOB on packed tails.
                logit_start = seq_start // cp_size
                logit_end = min(
                    (seq_start + padded_seq_lengths[seq_idx]) // cp_size,
                    next_token_logits.shape[1],
                )
                logit_slice_idxs = slice(logit_start, logit_end)
                next_token_logits_slice = next_token_logits[:, logit_slice_idxs]
            else:
                logit_start = seq_start // cp_size
                logit_end = (seq_start + padded_seq_lengths[seq_idx]) // cp_size
                logit_length = logit_end - logit_start
                next_token_logits_slice = next_token_logits.narrow(
                    1, logit_start, logit_length
                )
            loss_input, unpadded_seq_data = self.prepare_fn(
                logits=next_token_logits_slice,
                data=unpadded_seq_data,
                loss_fn=self.loss_fn,
                vocab_parallel_rank=self.vocab_parallel_rank,
                vocab_parallel_group=self.vocab_parallel_group,
                context_parallel_group=self.context_parallel_group,
            )

            # call loss function
            loss, metrics = self.loss_fn(
                data=unpadded_seq_data,
                global_valid_seqs=global_valid_seqs,
                global_valid_toks=global_valid_toks,
                **loss_input,
            )

            # aggregate loss and metrics
            loss_accum += loss
            for k, v in metrics.items():
                if k not in metrics_accum:
                    if k in {"probs_ratio_min", "probs_ratio_clamped_min"}:
                        metrics_accum[k] = float("inf")
                    elif k in {"probs_ratio_max", "probs_ratio_clamped_max"}:
                        metrics_accum[k] = float("-inf")
                    else:
                        metrics_accum[k] = 0

                val = v.item() if isinstance(v, torch.Tensor) and v.ndim == 0 else v

                # Skip inf/-inf sentinel values (from sequences with no valid tokens)
                if k in {"probs_ratio_min", "probs_ratio_clamped_min"}:
                    if not math.isinf(val):
                        metrics_accum[k] = min(metrics_accum[k], val)
                elif k in {"probs_ratio_max", "probs_ratio_clamped_max"}:
                    if not math.isinf(val):
                        metrics_accum[k] = max(metrics_accum[k], val)
                else:
                    metrics_accum[k] += val

        return loss_accum, metrics_accum


class SequencePackingFusionLossWrapper:
    """Fused sequence packing loss wrapper that processes all sequences in one forward pass.

    Unlike SequencePackingLossWrapper which iterates over sequences one at a time,
    this wrapper calls prepare_fn once on the packed logits to compute log
    probabilities in a single shot, then calls the loss function once with the
    pre-computed result.

    This avoids per-sequence kernel launches and TP/CP communication overhead while
    producing numerically identical results.

    The prepare_fn should be prepare_packed_loss_input (from nemo_rl.algorithms.loss.utils),
    which currently only supports LossInputType.LOGPROB.
    """

    def __init__(
        self,
        loss_fn: LossFunction,
        prepare_fn: Callable[..., Any],
        cu_seqlens_q: Tensor,
        cu_seqlens_q_padded: Optional[Tensor] = None,
        vocab_parallel_rank: Optional[int] = None,
        vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
        context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    ):
        self.loss_fn = loss_fn
        self.prepare_fn = prepare_fn
        self.cu_seqlens_q = cu_seqlens_q
        self.cu_seqlens_q_padded = (
            cu_seqlens_q_padded if cu_seqlens_q_padded is not None else cu_seqlens_q
        )
        self.vocab_parallel_rank = vocab_parallel_rank
        self.vocab_parallel_group = vocab_parallel_group
        self.context_parallel_group = context_parallel_group

    def __call__(
        self,
        next_token_logits: Tensor,
        data: BatchedDataDict[Any],
        global_valid_seqs: Tensor | None,
        global_valid_toks: Tensor | None,
    ) -> tuple[Tensor, dict[str, Any]]:
        """Compute loss for all packed sequences in one forward pass."""
        loss_input, prepared_data = self.prepare_fn(
            logits=next_token_logits,
            data=data,
            loss_fn=self.loss_fn,
            cu_seqlens_q=self.cu_seqlens_q,
            cu_seqlens_q_padded=self.cu_seqlens_q_padded,
            vocab_parallel_rank=self.vocab_parallel_rank,
            vocab_parallel_group=self.vocab_parallel_group,
            context_parallel_group=self.context_parallel_group,
        )

        return self.loss_fn(
            data=prepared_data,
            global_valid_seqs=global_valid_seqs,
            global_valid_toks=global_valid_toks,
            **loss_input,
        )


class DraftLossWrapper:
    """Combine policy loss with draft soft cross-entropy loss."""

    def __init__(
        self,
        loss_fn: Callable[..., tuple[torch.Tensor, dict[str, Any]]],
        prepare_fn: Callable[Any, Any],
        data_dict: BatchedDataDict[Any],
        loss_weight: float = 1.0,
        vocab_parallel_rank: Optional[int] = None,
        vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
        context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    ):
        self.loss_fn = loss_fn
        self.prepare_fn = prepare_fn
        self.data_dict = data_dict
        self.loss_weight = loss_weight
        self.vocab_parallel_rank = vocab_parallel_rank
        self.vocab_parallel_group = vocab_parallel_group
        self.context_parallel_group = context_parallel_group
        self.draft_loss_fn = DraftCrossEntropyLossFn(
            vocab_parallel_group=vocab_parallel_group,
        )

    def __call__(
        self,
        next_token_logits: torch.Tensor,
        data: BatchedDataDict[Any],
        global_valid_seqs: torch.Tensor | None,
        global_valid_toks: torch.Tensor | None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        if global_valid_toks is None:
            raise ValueError("global_valid_toks is required for DraftLossWrapper.")
        policy_loss, metrics = self.loss_fn(
            next_token_logits,
            data,
            global_valid_seqs,
            global_valid_toks,
            **kwargs,
        )

        loss_input, data = self.prepare_fn(
            logits=next_token_logits,
            data=data,
            loss_fn=self.draft_loss_fn,
            vocab_parallel_rank=self.vocab_parallel_rank,
            vocab_parallel_group=self.vocab_parallel_group,
            context_parallel_group=self.context_parallel_group,
        )
        draft_loss = self.draft_loss_fn(
            data=data,
            global_valid_seqs=global_valid_seqs,
            global_valid_toks=global_valid_toks,
            **loss_input,
        )
        combined_loss = policy_loss + self.loss_weight * draft_loss
        metrics["draft_loss"] = float(draft_loss.detach().item())
        return combined_loss, metrics


def wrap_loss_fn_with_input_preparation(
    next_token_logits: Tensor,
    data: BatchedDataDict[Any],
    global_valid_seqs: Tensor | None,
    global_valid_toks: Tensor | None,
    loss_fn: LossFunction,
    prepare_fn: Callable[Any, Any],
    vocab_parallel_rank: Optional[int] = None,
    vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    context_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
) -> tuple[Tensor, dict[str, Any]]:
    """Wraps a loss function to handle input preparation for megatron policy worker."""
    # prepare loss input
    loss_input, data = prepare_fn(
        logits=next_token_logits,
        data=data,
        loss_fn=loss_fn,
        vocab_parallel_rank=vocab_parallel_rank,
        vocab_parallel_group=vocab_parallel_group,
        context_parallel_group=context_parallel_group,
    )

    # call loss function
    loss, loss_metrics = loss_fn(
        data=data,
        global_valid_seqs=global_valid_seqs,
        global_valid_toks=global_valid_toks,
        **loss_input,
    )

    return loss, loss_metrics
