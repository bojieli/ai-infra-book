# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
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

from typing import Any, NotRequired, Optional, TypedDict, TypeVar

import torch
from pydantic import BaseModel

from nemo_rl.algorithms.loss.interfaces import LossFunction, LossInputType, LossType
from nemo_rl.algorithms.utils import calculate_kl, masked_mean
from nemo_rl.algorithms.x_token.loss_utils import (
    Fp32SparseMM,
    alignment_from_flat_batch,
    build_exact_token_map,
    chunk_average_log_probs,
    dp_all_reduce_sum,
    get_sparse_projection_matrix,
    valid_chunk_mask,
)
from nemo_rl.distributed.batched_data_dict import BatchedDataDict
from nemo_rl.distributed.model_utils import DistributedCrossEntropy

Tensor = TypeVar("Tensor", bound=torch.Tensor)


class DraftCrossEntropyLossConfig(TypedDict):
    vocab_parallel_group: Optional[torch.distributed.ProcessGroup]


class DraftCrossEntropyLossDataDict(TypedDict):
    teacher_logits: Tensor
    student_logits: Tensor
    token_mask: Tensor
    sample_mask: Tensor
    student_vocab_indices: NotRequired[Tensor]


class DraftCrossEntropyLossFn(LossFunction):
    """Compute the auxiliary soft-target cross-entropy used for draft-model training."""

    loss_type = LossType.TOKEN_LEVEL
    input_type = LossInputType.DRAFT

    def __init__(
        self,
        vocab_parallel_group: Optional[torch.distributed.ProcessGroup] = None,
    ):
        self.vocab_parallel_group = vocab_parallel_group

    def __call__(
        self,
        teacher_logits: Tensor,
        student_logits: Tensor,
        token_mask: Tensor,
        data: BatchedDataDict[DraftCrossEntropyLossDataDict],
        global_valid_seqs: torch.Tensor,
        global_valid_toks: torch.Tensor,
    ) -> torch.Tensor:
        """Reduce the masked per-token draft loss to a scalar."""
        if self.vocab_parallel_group is not None:
            # Soft cross entropy matches the forward-KL student gradient.
            per_token_loss = DistributedCrossEntropy.apply(
                student_logits,
                teacher_logits,
                self.vocab_parallel_group,
                False,
            )
        else:
            teacher_probs = torch.nn.functional.softmax(teacher_logits, dim=-1)
            student_log_probs = torch.nn.functional.log_softmax(student_logits, dim=-1)
            per_token_loss = -(teacher_probs * student_log_probs).sum(dim=-1)

        mask = token_mask * data["sample_mask"].unsqueeze(-1)
        return masked_mean(
            per_token_loss,
            mask,
            global_normalization_factor=global_valid_toks,
        )


class ClippedPGLossConfig(BaseModel, extra="allow"):
    # --- Loss type ---
    disable_ppo_ratio: bool = False
    token_level_loss: bool = True
    # If True, apply the off-policy importance-sampling correction at the
    # sequence level (one weight per generated sample), as in GSPO.
    # If False (default), correction is applied at the token level as in the
    # original GRPO paper.
    sequence_level_importance_ratios: bool = False

    # --- Clipping ---
    ratio_clip_min: float = 0.2
    ratio_clip_max: float = 0.2
    # Dual-clipping value (should be >1 if enabled; usually set to 3 empirically). None to disable.
    ratio_clip_c: Optional[float] = None

    # --- KL regularization ---
    reference_policy_kl_penalty: float = 0.01
    # Can be set to k1, k2, k3
    # For more details, see http://joschu.net/blog/kl-approx.html
    reference_policy_kl_type: str = "k3"
    kl_input_clamp_value: Optional[float] = 20.0
    kl_output_clamp_value: Optional[float] = 10.0
    # If True, add KL penalty to reward instead of loss (used by Reinforce++)
    use_kl_in_reward: bool = False

    # --- Importance sampling correction ---
    # Async GRPO requires importance sampling correction enabled
    # Set to true when async_grpo.enabled is true
    use_importance_sampling_correction: bool = False
    # --- Truncated importance sampling ---
    # Type of truncated importance sampling:
    #   "tis"          – clamp IS weights to max
    #   "icepop"       – zero out tokens with IS weight outside [min, max]
    #   "seq-mask-tis" – zero out sequences by geometric-mean IS ratio, non-truncated token IS correction
    truncated_importance_sampling_type: Optional[str] = None
    truncated_importance_sampling_ratio: Optional[float] = None
    # Lower bound for ICE-POP / seq-mask-tis filtering
    truncated_importance_sampling_ratio_min: Optional[float] = None

    # --- On-policy ---
    # (default off) loss formulation improvements (docs/guides/grpo.md#loss)
    use_on_policy_kl_approximation: bool = False
    # If True, force the ratio to 1.0 for truly on-policy behavior,
    # eliminating any importance sampling effects.
    # NOTE: This should only be used when doing exactly one update per rollout
    # (i.e., num_prompts_per_step * num_generations_per_prompt == train_global_batch_size)
    force_on_policy_ratio: bool = False


class ClippedPGLossDataDict(TypedDict):
    """Required keys for the Clipped Policy Gradient loss function."""

    input_ids: torch.Tensor
    advantages: torch.Tensor
    prev_logprobs: torch.Tensor
    generation_logprobs: torch.Tensor
    reference_policy_logprobs: torch.Tensor
    token_mask: torch.Tensor
    sample_mask: torch.Tensor
    __extra__: Any


class ClippedPGLossFn(LossFunction):
    """Generalized Clipped Policy Gradient loss function w/ KL regularization.

    This implements:

    - PPO (Clipped) - https://arxiv.org/abs/1707.06347
    - GRPO - https://arxiv.org/abs/2402.03300
    - REINFORCE/RLOO (set disable_ppo_ratio = True and ignores ratio_clip_min/ratio_clip_max) - https://arxiv.org/abs/2402.14740
    - GSPO (set sequence_level_importance_ratios = True and token_level_loss = False) - https://arxiv.org/abs/2507.18071
    - Truly on-policy (set force_on_policy_ratio = True to force ratio = 1.0, requires one update per rollout)

    Formula:
    L(θ) = E_t [ min(r_t(θ) * A_t, clip(r_t(θ), 1-ε, 1+ε) * A_t) ] - β * KL(π_θ || π_ref)

    where:
    - r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t) is the probability ratio
    - A_t is the advantage estimate
    - ε is the clip parameter (ratio_clip_min/ratio_clip_max)
        - As proposed in the DAPO paper (https://arxiv.org/pdf/2503.14476),
          we allow setting a distinct minimum and maximum value for the clip parameter (set to the same value for PPO/GRPO/etc.)
            - ratio_clip_min: minimum value for the clip parameter
            - ratio_clip_max: maximum value for the clip parameter
    - β is the KL penalty coefficient (reference_policy_kl_penalty)
    - KL(π_θ || π_ref) is the KL divergence between the current policy and reference policy (Schulman Approx.)

    For REINFORCE/RLOO (when disable_ppo_ratio=True), the formula simplifies to:
    L(θ) = E_t [ π_θ(a_t|s_t) * A_t ] - β * KL(π_θ || π_ref)

    Also supports "Dual-Clipping" from https://arxiv.org/pdf/1912.09729, which
    imposes an additional upper bound on the probability ratio when advantages are negative.
    This prevents excessive policy updates. $rA << 0$ -> $cA$(clipped)
    The loss function is modified to the following when A_t < 0:
    L(θ) = E_t [ max(min(r_t(θ) * A_t, clip(r_t(θ), 1-ε, 1+ε) * A_t), c * A_t) ] - β * KL(π_θ || π_ref)

    where:
    - c is the dual-clip parameter (ratio_clip_c), which must be greater than 1 and is
      usually set as 3 empirically.

    Due to potential numerical instability, we cast the logits to float32 before computing the loss.
    """

    input_type = LossInputType.LOGPROB

    def __init__(self, cfg: ClippedPGLossConfig):
        self.disable_ppo_ratio = cfg.disable_ppo_ratio
        self.ratio_clip_min = cfg.ratio_clip_min
        self.ratio_clip_max = cfg.ratio_clip_max
        self.ratio_clip_c = cfg.ratio_clip_c  # set to None to disable dual-clipping
        self.reference_policy_kl_penalty = cfg.reference_policy_kl_penalty
        self.reference_policy_kl_type = cfg.reference_policy_kl_type
        self.kl_input_clamp_value = cfg.kl_input_clamp_value
        self.kl_output_clamp_value = cfg.kl_output_clamp_value
        self.use_importance_sampling_correction = cfg.use_importance_sampling_correction
        # Type of truncated importance sampling: "tis" | "icepop" | "seq-mask-tis"
        self.truncated_importance_sampling_type = cfg.truncated_importance_sampling_type
        self.truncated_importance_sampling_ratio = (
            cfg.truncated_importance_sampling_ratio
        )
        # Lower bound for ICE-POP / seq-mask-tis filtering
        self.truncated_importance_sampling_ratio_min = (
            cfg.truncated_importance_sampling_ratio_min
        )
        self.use_on_policy_kl_approximation = cfg.use_on_policy_kl_approximation
        self.force_on_policy_ratio = cfg.force_on_policy_ratio  # Force ratio to 1.0

        # Whether to compute importance weights per-sequence instead of per-token.
        self.sequence_level_importance_ratios = cfg.sequence_level_importance_ratios
        self.loss_type = (
            LossType.TOKEN_LEVEL if cfg.token_level_loss else LossType.SEQUENCE_LEVEL
        )
        if self.sequence_level_importance_ratios:
            assert self.loss_type == LossType.SEQUENCE_LEVEL, (
                "sequence-level importance sampling (e.g. GSPO) is mutually exclusive with token-level loss"
            )

        if self.truncated_importance_sampling_type is not None:
            assert self.use_importance_sampling_correction, (
                "truncated importance sampling is only supported when use_importance_sampling_correction is True"
            )
            assert self.truncated_importance_sampling_type in (
                "tis",
                "icepop",
                "seq-mask-tis",
            ), (
                f"truncated_importance_sampling_type must be 'tis', 'icepop', or 'seq-mask-tis', "
                f"got {self.truncated_importance_sampling_type}"
            )
            assert (
                self.truncated_importance_sampling_ratio is not None
                and self.truncated_importance_sampling_ratio > 0
            ), "truncated_importance_sampling_ratio should be positive"
            if self.truncated_importance_sampling_type in ("icepop", "seq-mask-tis"):
                assert self.truncated_importance_sampling_ratio_min is not None, (
                    "truncated_importance_sampling_ratio_min should be set when truncated_importance_sampling_type is 'icepop' or 'seq-mask-tis'"
                )
            if self.truncated_importance_sampling_type == "seq-mask-tis":
                assert not self.sequence_level_importance_ratios, (
                    "seq-mask-tis uses token-level IS correction with sequence-level masking, "
                    "and is incompatible with sequence_level_importance_ratios=True"
                )

    def __call__(
        self,
        next_token_logprobs: Tensor,
        data: BatchedDataDict[ClippedPGLossDataDict],
        global_valid_seqs: torch.Tensor,
        global_valid_toks: torch.Tensor,
    ) -> tuple[torch.Tensor, dict]:
        """Clipped Policy Gradient RL loss function."""
        curr_logprobs = next_token_logprobs
        token_mask = data["token_mask"][:, 1:]
        sample_mask = data["sample_mask"]
        advantages = data["advantages"][:, 1:]
        # Skip loading prev_logprobs when force_on_policy_ratio=True (will use curr_logprobs instead)
        prev_logprobs = (
            None if self.force_on_policy_ratio else data["prev_logprobs"][:, 1:]
        )
        generation_logprobs = data["generation_logprobs"][:, 1:]
        if self.reference_policy_kl_penalty != 0:
            reference_policy_logprobs = data["reference_policy_logprobs"][:, 1:]
            curr_logprobs_unfiltered = data.get(
                "curr_logprobs_unfiltered", curr_logprobs
            )

        mask = token_mask * sample_mask.unsqueeze(-1)

        # For truly on-policy training, use curr_logprobs as prev_logprobs
        # This avoids computing prev_logprobs upstream
        if self.force_on_policy_ratio:
            prev_logprobs = curr_logprobs.detach()

        # token_mult_prob_error
        # See more details and other metrics in docs/guides/grpo.md#metrics
        lp_error = torch.abs(generation_logprobs - prev_logprobs)  # noqa: F841  (precommit ignore for now)
        # average over all tokens in the microbatch
        mult_prob_error = masked_mean(
            torch.exp(lp_error * mask),
            mask,
            global_normalization_factor=global_valid_toks,
        ).item()

        # gen-kl: kl(P_gen || P_train)
        # where log_ratio = prev_logprobs - generation_logprobs
        gen_kl_error = calculate_kl(
            logprobs=generation_logprobs,
            logprobs_reference=prev_logprobs,
            kl_type=self.reference_policy_kl_type,
            input_clamp_value=None,
            output_clamp_value=None,
        )
        gen_kl_error = masked_mean(
            gen_kl_error,
            mask,
            global_normalization_factor=global_valid_toks,
        ).item()

        # policy-kl: kl(P_train || P_gen)
        # where log_ratio = generation_logprobs - prev_logprobs
        policy_kl_error = calculate_kl(
            logprobs=prev_logprobs,
            logprobs_reference=generation_logprobs,
            kl_type=self.reference_policy_kl_type,
            input_clamp_value=None,
            output_clamp_value=None,
        )
        policy_kl_error = masked_mean(
            policy_kl_error,
            mask,
            global_normalization_factor=global_valid_toks,
        ).item()

        # Jensen-Shannon divergence
        # M = 0.5 * (P_train + P_gen)
        # JSD = 0.5 * KL(P_train || M) + 0.5 * KL(P_gen || M)
        log_mixture = torch.log(
            0.5 * torch.exp(prev_logprobs) + 0.5 * torch.exp(generation_logprobs)
        )
        # KL(P_train || M)
        kl_prev_to_mixture = (
            torch.exp(prev_logprobs - log_mixture) - (prev_logprobs - log_mixture) - 1
        )

        # KL(P_gen || M)
        kl_gen_to_mixture = (
            torch.exp(generation_logprobs - log_mixture)
            - (generation_logprobs - log_mixture)
            - 1
        )

        js_divergence_error = masked_mean(
            0.5 * kl_prev_to_mixture + 0.5 * kl_gen_to_mixture,
            mask,
            global_normalization_factor=global_valid_toks,
        ).item()

        # Calculate KL regularization.
        if self.reference_policy_kl_penalty != 0:
            # When top-k/top-p filtering is enabled, we need special handling for KL:
            # - reference_policy_logprobs is computed **without** filtering (see use_reference_model)
            # - curr_logprobs/prev_logprobs are computed **with** filtering (for actor loss compatibility)
            # - For KL, we need curr_logprobs **without** filtering to be consistent with ref logprobs
            # - For importance weights, we also use unfiltered curr_logprobs_unfiltered since we're
            #   reweighting samples from π_gen_filtered to π_curr_unfiltered

            # On-policy KL approximation
            if self.use_on_policy_kl_approximation:
                # See: docs/guides/grpo.md#on-policy-kl-approximation
                kl_importance_weights = torch.exp(
                    curr_logprobs_unfiltered - generation_logprobs
                ).detach()
                kl_importance_weights = torch.nan_to_num(
                    kl_importance_weights, nan=0.0, posinf=0.0, neginf=0.0
                )
            else:
                kl_importance_weights = torch.ones_like(curr_logprobs_unfiltered)

            # Compute KL loss
            kl = (
                kl_importance_weights
                * self.reference_policy_kl_penalty
                * calculate_kl(
                    logprobs=curr_logprobs_unfiltered,
                    logprobs_reference=reference_policy_logprobs,
                    kl_type=self.reference_policy_kl_type,
                    input_clamp_value=self.kl_input_clamp_value,
                    output_clamp_value=self.kl_output_clamp_value,
                )
            )

            # Reduce KL loss
            if self.loss_type == LossType.TOKEN_LEVEL:
                kl = masked_mean(
                    kl, mask, global_normalization_factor=global_valid_toks
                )
            else:
                kl = masked_mean(
                    masked_mean(kl, token_mask, dim=-1),
                    sample_mask,
                    global_normalization_factor=global_valid_seqs,
                )
        else:
            kl = torch.tensor(0.0)

        # Calculate clipped loss function if ppo ratio is enabled.
        if self.force_on_policy_ratio:
            # Force ratio to 1.0 for truly on-policy behavior
            # Use curr_logprobs twice so ratio=1 but gradients still flow
            log_ratios = curr_logprobs - curr_logprobs.detach()
            ratios = log_ratios.exp()  # = exp(0) = 1.0, but depends on curr_logprobs
            ratios_clamped = ratios
        elif not self.disable_ppo_ratio:
            log_ratios = curr_logprobs - prev_logprobs
            if self.sequence_level_importance_ratios:
                seq_log_ratio_mean = masked_mean(
                    log_ratios,
                    token_mask,
                    dim=-1,
                ).unsqueeze(-1)
                seq_ratio = seq_log_ratio_mean.exp()
                ratios = seq_ratio.repeat(1, advantages.shape[1])
            else:
                ratios = log_ratios.exp()
            ratios_clamped = ratios.clamp(
                1.0 - self.ratio_clip_min, 1.0 + self.ratio_clip_max
            )
        else:
            ratios = curr_logprobs
            ratios_clamped = curr_logprobs

        loss1 = -advantages * ratios
        loss2 = -advantages * ratios_clamped

        # Determine which value to use for clipping (max for pessimistic estimate)
        clip_loss = torch.max(loss1, loss2)

        # Dual-clipping see https://arxiv.org/pdf/1912.09729
        if self.ratio_clip_c is not None:
            assert self.ratio_clip_c > 1, (
                f"ratio_clip_c must exceed 1 representing a lower bound of the ratios, got {self.ratio_clip_c}."
            )
            loss3 = -advantages * self.ratio_clip_c
            clip_loss = torch.where(
                advantages < 0, torch.min(clip_loss, loss3), clip_loss
            )

        # -------------------------------------------------------------
        # Off-policy (actor) importance-sampling correction
        # -------------------------------------------------------------
        _is_filter_metrics: dict = {}  # populated for icepop / seq-mask-tis
        # See: docs/guides/grpo.md#importance-sampling-correction
        if self.sequence_level_importance_ratios:
            # importance weight w_i = exp(Σ_t (log π_actor − log π_behaviour))
            seq_lp_diff = ((prev_logprobs - generation_logprobs) * mask).sum(dim=-1)
            actor_importance_weights = torch.exp(seq_lp_diff).detach()
            actor_importance_weights = torch.nan_to_num(
                actor_importance_weights, nan=0.0, posinf=0.0, neginf=0.0
            )
            # Broadcast to token dimension so we can reuse existing reduction
            actor_importance_weights_expanded = actor_importance_weights.unsqueeze(-1)
        else:
            # Token-level correction
            actor_importance_weights_expanded = torch.exp(
                prev_logprobs - generation_logprobs
            )
            actor_importance_weights_expanded = torch.nan_to_num(
                actor_importance_weights_expanded, nan=0.0, posinf=0.0, neginf=0.0
            )
        # ---- Truncated Importance Sampling ----
        # "tis"          – clamp IS weights to [0, max]
        # "icepop"       – zero out tokens whose IS weight ∉ [min, max]   (ref bounds: 0.5–5)
        # "seq-mask-tis" – zero out entire sequences whose geometric-mean
        #                  IS ratio ∉ [min, max]; retained sequences keep
        #                  raw (non-truncated) token-level IS weights      (ref bounds: 0.999–1.002)
        #   Blog: https://yingru.notion.site/When-Speed-Kills-Stability-Demystifying-RL-Collapse-from-the-Training-Inference-Mismatch-271211a558b7808d8b12d403fd15edda
        # is_oob_ratio: fraction of tokens (tis/icepop) or sequences (seq-mask-tis)
        # whose importance weight falls outside the truncation bounds. Each microbatch
        # contributes its out-of-bounds count divided by the *global* valid token/seq
        # count, so the np.sum aggregation in grpo.py recovers the correct global fraction.
        if self.truncated_importance_sampling_ratio is not None:
            if self.truncated_importance_sampling_type == "tis":
                token_oob_mask = (
                    actor_importance_weights_expanded
                    > self.truncated_importance_sampling_ratio
                )
                _is_filter_metrics = {
                    "is_oob_ratio": masked_mean(
                        token_oob_mask.float(),
                        mask,
                        global_normalization_factor=global_valid_toks,
                    ).item(),
                }
                actor_importance_weights_expanded = torch.clamp(
                    actor_importance_weights_expanded,
                    max=self.truncated_importance_sampling_ratio,
                )
            elif self.truncated_importance_sampling_type == "icepop":
                token_kept_mask = (
                    actor_importance_weights_expanded
                    >= self.truncated_importance_sampling_ratio_min
                ) & (
                    actor_importance_weights_expanded
                    <= self.truncated_importance_sampling_ratio
                )
                _is_filter_metrics = {
                    "is_oob_ratio": masked_mean(
                        (~token_kept_mask).float(),
                        mask,
                        global_normalization_factor=global_valid_toks,
                    ).item(),
                }
                actor_importance_weights_expanded = torch.where(
                    token_kept_mask,
                    actor_importance_weights_expanded,
                    torch.zeros_like(actor_importance_weights_expanded),
                )
            elif self.truncated_importance_sampling_type == "seq-mask-tis":
                # geo_mean_i = exp( mean_t( log(π_prev / π_gen) ) )
                log_is_ratio = torch.nan_to_num(
                    prev_logprobs - generation_logprobs,
                    nan=0.0,
                    posinf=0.0,
                    neginf=0.0,
                )
                seq_log_is_ratio_mean = masked_mean(
                    log_is_ratio, token_mask, dim=-1
                )  # [B]
                seq_geomean_is_ratio = torch.exp(seq_log_is_ratio_mean).detach()  # [B]
                seq_kept_mask = (
                    (
                        seq_geomean_is_ratio
                        >= self.truncated_importance_sampling_ratio_min
                    )
                    & (seq_geomean_is_ratio <= self.truncated_importance_sampling_ratio)
                ).float()  # [B]
                _is_filter_metrics = {
                    "is_oob_ratio": masked_mean(
                        1.0 - seq_kept_mask,
                        sample_mask,
                        global_normalization_factor=global_valid_seqs,
                    ).item(),
                }
                actor_importance_weights_expanded = (
                    actor_importance_weights_expanded * seq_kept_mask.unsqueeze(-1)
                )
            else:
                raise ValueError(
                    f"Invalid truncated importance sampling type: {self.truncated_importance_sampling_type}"
                )

        actor_importance_weights = actor_importance_weights_expanded
        del actor_importance_weights_expanded
        if self.use_importance_sampling_correction:
            importance_weights_to_use = actor_importance_weights
        else:
            importance_weights_to_use = torch.ones_like(prev_logprobs)

        if self.loss_type == LossType.TOKEN_LEVEL:
            actor_loss = masked_mean(
                importance_weights_to_use * clip_loss,
                mask,
                global_normalization_factor=global_valid_toks,
            )
        else:
            actor_loss = masked_mean(
                masked_mean(
                    importance_weights_to_use * clip_loss,
                    token_mask,
                    dim=-1,
                ),
                sample_mask,
                global_normalization_factor=global_valid_seqs,
            )

        # Metric: sampling importance ratio (mean over samples)
        # See: docs/guides/grpo.md#sampling-importance-ratio
        if self.sequence_level_importance_ratios:
            sample_importance_ratio = masked_mean(
                actor_importance_weights,
                sample_mask,
                global_normalization_factor=global_valid_seqs,
            )
        else:
            sample_importance_ratio = masked_mean(
                actor_importance_weights,
                mask,
                global_normalization_factor=global_valid_toks,
            )

        # Approximating entropy as E_{s ~ \pi_{gen}(s)}[-(\pi_{curr}/\pi_{gen})log(\pi_{curr}(s))]
        # See more details and other metrics in docs/guides/grpo.md#metrics
        with torch.no_grad():
            seq_entropy_approx = -masked_mean(
                torch.exp(curr_logprobs - generation_logprobs) * curr_logprobs,
                mask,
                global_normalization_factor=global_valid_toks,
            )

        loss = actor_loss + kl
        with torch.no_grad():
            probs_ratio = masked_mean(
                ratios.detach(),
                mask,
                global_normalization_factor=global_valid_toks,
            ).item()
            probs_ratio_clamped = masked_mean(
                ratios_clamped.detach(),
                mask,
                global_normalization_factor=global_valid_toks,
            ).item()

            # Calculate min/max values for ratios (only for valid tokens)
            masked_ratios = ratios.detach()[mask.bool()]
            masked_ratios_clamped = ratios_clamped.detach()[mask.bool()]

            # Handle edge case where there might be no valid tokens
            if masked_ratios.numel() > 0:
                probs_ratio_min = masked_ratios.min().item()
                probs_ratio_max = masked_ratios.max().item()
                probs_ratio_clamped_min = masked_ratios_clamped.min().item()
                probs_ratio_clamped_max = masked_ratios_clamped.max().item()
            else:
                probs_ratio_min = float("inf")
                probs_ratio_max = float("-inf")
                probs_ratio_clamped_min = float("inf")
                probs_ratio_clamped_max = float("-inf")

        # If you provided a global_valid_{seqs/toks}, all metrics here are globally normalized
        # by either sequence or token count, depending on particular metric.
        # To get the true metric, you'll need to sum over the microbatch.
        return (
            loss,
            {
                "loss": loss.item(),
                "probs_ratio": probs_ratio,
                "probs_ratio_clamped": probs_ratio_clamped,
                "probs_ratio_min": probs_ratio_min,
                "probs_ratio_max": probs_ratio_max,
                "probs_ratio_clamped_min": probs_ratio_clamped_min,
                "probs_ratio_clamped_max": probs_ratio_clamped_max,
                "kl_penalty": kl.item() / self.reference_policy_kl_penalty if kl else 0,
                "token_mult_prob_error": mult_prob_error,
                "gen_kl_error": gen_kl_error,
                "policy_kl_error": policy_kl_error,
                "js_divergence_error": js_divergence_error,
                "sampling_importance_ratio": sample_importance_ratio.item(),
                "num_valid_samples": sample_mask.sum().item(),
                "approx_entropy": seq_entropy_approx.item(),
                **_is_filter_metrics,
            },
        )


class NLLLossFn(LossFunction):
    """Negative Log Likelihood Loss function."""

    loss_type = LossType.TOKEN_LEVEL
    input_type = LossInputType.LOGPROB

    def __init__(self, use_linear_ce_fusion: bool = False):
        self.use_linear_ce_fusion = use_linear_ce_fusion

    def __call__(
        self,
        next_token_logprobs: Tensor,
        data: BatchedDataDict[Any],
        global_valid_seqs: Tensor | None,
        global_valid_toks: Tensor,
        dpo_loss: bool = False,
        dpo_average_log_probs: bool = False,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        # logits shape: [batch_size, seq_len, vocab_size]
        # Get the next token logits for each position
        token_mask = data["token_mask"][:, 1:]
        sample_mask = data["sample_mask"]
        mask = token_mask * sample_mask.unsqueeze(-1)

        if dpo_loss:
            ## shape: [batch_size]
            num_unmasked_tokens = torch.sum(mask, -1)
            ## multiply by sample_mask to zero out invalid samples
            loss = -torch.sum(next_token_logprobs * mask, dim=-1)
            if dpo_average_log_probs:
                loss = loss / num_unmasked_tokens.clamp(min=1)
        else:
            ## single scalar loss
            ## scale by the total number of tokens in the batch
            loss = -masked_mean(
                next_token_logprobs,
                mask,
                global_normalization_factor=global_valid_toks,
            )

        return loss, {
            "loss": loss.item() if loss.ndim == 0 else loss,
            "num_unmasked_tokens": mask.sum().item(),
            "num_valid_samples": sample_mask.sum().item(),
        }


class PreferenceLossDataDict(TypedDict):
    """Required keys for the preference loss function."""

    input_ids: torch.Tensor
    token_mask: torch.Tensor
    sample_mask: torch.Tensor


class PreferenceLossFn(LossFunction):
    """Preference Loss function.

    Optimizes the model to prefer chosen responses over rejected ones

    The preference loss is computed as:
    L_pref(θ) = -E[log(σ(β * (r_chosen - r_rejected)))]

    where:
    - σ is the sigmoid function
    - β is a scaling factor (ex: `reference_policy_kl_penalty` in DPO)
    - r_chosen and r_rejected are the rewards for chosen and rejected responses

    Returns:
        tuple[torch.Tensor, dict]: A tuple containing:
            - The preference loss value
            - A dictionary with metrics including:
                - loss: Preference loss
                - accuracy: Fraction of examples where chosen response has higher reward
    """

    loss_type = LossType.SEQUENCE_LEVEL
    input_type = LossInputType.LOGIT

    def split_output_tensor(self, tensor: Tensor) -> tuple[Tensor, Tensor]:
        # tensor is of shape (2*micro_batch_size,)
        return tensor[::2], tensor[1::2]

    def _preference_loss(
        self,
        rewards: Tensor,
        sample_mask: Tensor,
        global_valid_seqs: Tensor,
        beta: float = 1.0,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        rewards_chosen, rewards_rejected = self.split_output_tensor(rewards)
        rewards_delta = rewards_chosen - rewards_rejected

        per_sample_loss = (
            -torch.nn.functional.logsigmoid(beta * rewards_delta) * sample_mask[::2]
        )  ## zero out invalid samples

        ## divide by 2 because each preference example corresponds to 2 samples (chosen, rejected)
        return (
            masked_mean(
                per_sample_loss,
                sample_mask[::2],
                global_normalization_factor=global_valid_seqs / 2,
            ),
            masked_mean(
                rewards_chosen > rewards_rejected,
                sample_mask[::2],
                global_normalization_factor=global_valid_seqs / 2,
            ),
            masked_mean(
                rewards_chosen,
                sample_mask[::2],
                global_normalization_factor=global_valid_seqs / 2,
            ),
            masked_mean(
                rewards_rejected,
                sample_mask[1::2],
                global_normalization_factor=global_valid_seqs / 2,
            ),
        )

    def __call__(
        self,
        logits: Tensor,
        data: BatchedDataDict[PreferenceLossDataDict],
        global_valid_seqs: Tensor,
        global_valid_toks: Tensor | None,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        sample_mask = data["sample_mask"]

        rewards = logits.squeeze(-1)

        (
            preference_loss,
            accuracy,
            rewards_chosen_mean,
            rewards_rejected_mean,
        ) = self._preference_loss(rewards, sample_mask, global_valid_seqs)

        ## divide by 2 because we're summing over (chosen, rejected) pairs
        num_valid_samples = sample_mask.sum() / 2

        return preference_loss, {
            "loss": preference_loss.item(),
            "accuracy": accuracy.item(),
            "rewards_chosen_mean": rewards_chosen_mean.item(),
            "rewards_rejected_mean": rewards_rejected_mean.item(),
            "num_valid_samples": num_valid_samples.item(),
        }


class DPOLossConfig(TypedDict):
    reference_policy_kl_penalty: float
    preference_loss_weight: float
    sft_loss_weight: float
    preference_average_log_probs: bool
    sft_average_log_probs: bool


class DPOLossDataDict(TypedDict):
    """Required keys for the DPO loss function."""

    input_ids: torch.Tensor
    reference_policy_logprobs: torch.Tensor
    token_mask: torch.Tensor
    sample_mask: torch.Tensor


class DPOLossFn(PreferenceLossFn):
    """Direct Preference Optimization (DPO) loss function.

    This loss function implements the DPO algorithm as described in:
    "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
    (https://arxiv.org/abs/2305.18290)

    The loss combines two main components:
    1. Preference Loss: Optimizes the model to prefer chosen responses over rejected ones
    2. SFT Loss (optional): Auxiliary supervised fine-tuning loss on chosen responses

    The total loss is computed as:
    L(θ) = w_p * L_pref(θ) + w_s * L_sft(θ)

    where:
    - w_p is the preference_loss_weight
    - w_s is the sft_loss_weight
    - L_pref(θ) is the preference loss term
    - L_sft(θ) is the supervised fine-tuning loss term

    The preference loss term is computed as:
    L_pref(θ) = -E[log(σ(β * (r_chosen - r_rejected)))]

    where:
    - σ is the sigmoid function
    - β is the reference_policy_kl_penalty
    - r_chosen and r_rejected are the rewards for chosen and rejected responses
    - The rewards are computed as the sum of log probability differences between
      the current policy and reference policy

    If preference_average_log_probs is True, the rewards are averaged over tokens:
    r = (1/n) * Σ_t (log π_θ(a_t|s_t) - log π_ref(a_t|s_t))

    Otherwise, the rewards are summed over tokens.

    The SFT loss term is a standard negative log likelihood loss on the chosen responses.
    If sft_average_log_probs is True, the loss is averaged over tokens.

    Args:
        cfg (DPOLossConfig): Configuration dictionary containing:
            - reference_policy_kl_penalty (float): Strength of the KL penalty term (β)
            - preference_loss_weight (float): Weight for the preference loss term (w_p)
            - sft_loss_weight (float): Weight for the SFT loss term (w_s)
            - preference_average_log_probs (bool): Whether to average log probs across tokens in preference loss
            - sft_average_log_probs (bool): Whether to average log probs across tokens in SFT loss

    Returns:
        tuple[torch.Tensor, dict]: A tuple containing:
            - The total loss value
            - A dictionary with metrics including:
                - loss: Total loss value
                - sft_loss: SFT loss component
                - preference_loss: Preference loss component
                - accuracy: Fraction of examples where chosen response has higher reward
    """

    loss_type = LossType.SEQUENCE_LEVEL
    input_type = LossInputType.LOGPROB

    def __init__(self, cfg: DPOLossConfig, use_linear_ce_fusion: bool = False):
        self.reference_policy_kl_penalty = cfg["reference_policy_kl_penalty"]
        self.preference_loss_weight = cfg["preference_loss_weight"]
        self.sft_loss_weight = cfg["sft_loss_weight"]
        self.preference_average_log_probs = cfg["preference_average_log_probs"]
        self.sft_average_log_probs = cfg["sft_average_log_probs"]
        self.use_linear_ce_fusion = use_linear_ce_fusion
        self.sft_loss = NLLLossFn(use_linear_ce_fusion=use_linear_ce_fusion)

    def _dpo_loss(
        self,
        next_token_logprobs: Tensor,
        data: BatchedDataDict[DPOLossDataDict],
        global_valid_seqs: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        ## TODO(@ashors): there's some duplicate code here with the NLLLossFn function. We should refactor
        token_mask = data["token_mask"][:, 1:]
        sample_mask = data["sample_mask"]

        ref_logprobs = data["reference_policy_logprobs"][:, :-1]
        diff = (next_token_logprobs - ref_logprobs) * token_mask

        rewards = diff.sum(-1)
        if self.preference_average_log_probs:
            rewards = rewards / token_mask.sum(-1).clamp(min=1)

        return self._preference_loss(
            rewards, sample_mask, global_valid_seqs, self.reference_policy_kl_penalty
        )

    # TODO a cleaner typing fix would be required (probably that DPOLossFn should not inherit from PreferenceLossFn)
    def __call__(  # type: ignore
        self,
        next_token_logprobs: Tensor,
        data: BatchedDataDict[DPOLossDataDict],
        global_valid_seqs: Tensor,
        global_valid_toks: Tensor | None,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        sft_loss_chosen = torch.tensor(0.0)
        if self.sft_loss_weight > 0:
            assert global_valid_toks is not None, (
                "global_valid_toks must be provided for SFT loss"
            )
            sft_loss, _ = self.sft_loss(
                next_token_logprobs,
                data,
                global_valid_seqs=global_valid_seqs,
                global_valid_toks=global_valid_toks,  ## unused because sft loss returned is at the sample level
                dpo_loss=True,
                dpo_average_log_probs=self.sft_average_log_probs,
            )
            sft_loss_chosen, sft_loss_rejected = self.split_output_tensor(sft_loss)
            sft_loss_chosen = masked_mean(
                sft_loss_chosen,
                data["sample_mask"][::2],
                global_normalization_factor=global_valid_seqs / 2,
            )

        (
            preference_loss,
            accuracy,
            rewards_chosen_mean,
            rewards_rejected_mean,
        ) = self._dpo_loss(next_token_logprobs, data, global_valid_seqs)

        dpo_loss = (
            self.sft_loss_weight * sft_loss_chosen
            + self.preference_loss_weight * preference_loss
        )

        ## divide by 2 because we're summing over (chosen, rejected) pairs
        num_valid_samples = data["sample_mask"].sum() / 2

        return dpo_loss, {
            "loss": dpo_loss.item(),
            "sft_loss": sft_loss_chosen.item(),
            "preference_loss": preference_loss.item(),
            "accuracy": accuracy.item(),
            "rewards_chosen_mean": rewards_chosen_mean.item(),
            "rewards_rejected_mean": rewards_rejected_mean.item(),
            "num_valid_samples": num_valid_samples.item(),
        }


class DistillationLossConfig(TypedDict):
    kl_type: str
    mixed_kl_weight: float
    zero_outside_topk: bool


class DistillationLossDataDict(TypedDict):
    input_ids: torch.Tensor
    input_lengths: torch.Tensor
    token_mask: torch.Tensor
    sample_mask: torch.Tensor
    teacher_topk_logits: torch.Tensor
    teacher_topk_indices: torch.Tensor


class DistillationLossFn(LossFunction):
    """Distillation loss function."""

    loss_type = LossType.TOKEN_LEVEL
    input_type = LossInputType.DISTILLATION

    def __init__(self, cfg: DistillationLossConfig):
        self.kl_type = cfg["kl_type"]
        self.mixed_kl_weight = cfg["mixed_kl_weight"]
        self.zero_outside_topk = cfg["zero_outside_topk"]
        self.log_infinitesimal = -100

        assert self.kl_type in ["forward", "reverse", "mixed"], "Invalid KL type"
        assert self.mixed_kl_weight >= 0 and self.mixed_kl_weight <= 1, (
            "Invalid mixed KL weight"
        )

    def __call__(
        self,
        student_topk_logprobs: torch.Tensor,
        teacher_topk_logprobs: torch.Tensor,
        H_all: torch.Tensor | None,
        data: DistillationLossDataDict,
        global_valid_seqs: torch.Tensor,
        global_valid_toks: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Compute distillation loss between teacher and student logits."""
        student_probs = student_topk_logprobs.exp()  # [B, S-1, k]
        teacher_probs = teacher_topk_logprobs.exp()  # [B, S-1, k]

        loss_correction_term = torch.zeros_like(student_probs[..., 0])  # [B, S-1]
        if self.zero_outside_topk and self.kl_type != "forward":
            H_rest = H_all - (student_probs * student_topk_logprobs).sum(-1)
            P_rest = 1 - (student_probs.sum(-1))
            # The entropy and prob of the rest of the tokens [B, S-1]
            loss_correction_term = H_rest - self.log_infinitesimal * P_rest  # [B, S-1]
            if self.kl_type == "mixed":
                loss_correction_term = loss_correction_term * (
                    1.0 - self.mixed_kl_weight
                )

        if self.kl_type == "forward":
            per_token_kl = teacher_probs * (
                teacher_topk_logprobs - student_topk_logprobs
            )
        elif self.kl_type == "reverse":
            per_token_kl = student_probs * (
                student_topk_logprobs - teacher_topk_logprobs
            )
        else:
            # mixed KL
            kl_forward = teacher_probs * (teacher_topk_logprobs - student_topk_logprobs)
            kl_reverse = student_probs * (student_topk_logprobs - teacher_topk_logprobs)
            per_token_kl = (
                self.mixed_kl_weight * kl_forward
                + (1.0 - self.mixed_kl_weight) * kl_reverse
            )

        per_token_kl = per_token_kl.sum(dim=-1) + loss_correction_term  # [B, S-1]

        # Masking and reduction
        if "token_mask" in data and "sample_mask" in data:
            token_mask = data["token_mask"][:, 1:]
            sample_mask = data["sample_mask"]
            # Align mask length to current per_token_kl
            max_len = per_token_kl.shape[1]
            token_mask = token_mask[:, :max_len]
            mask = token_mask * sample_mask.unsqueeze(-1)  # [B, S-1]
            # align mask shape to per_token_kl
            kl_loss = masked_mean(
                per_token_kl,
                mask,
                global_normalization_factor=global_valid_toks,
            )
        else:
            kl_loss = per_token_kl.mean()

        metrics = {
            "loss": float(kl_loss.item()) if kl_loss.ndim == 0 else kl_loss,
            "num_valid_samples": data["input_ids"].shape[0],
        }

        return kl_loss, metrics


# =====================================================================
# Cross-tokenizer distillation
# =====================================================================


class CrossTokenizerDistillationLossConfig(TypedDict):
    """Config for cross-tokenizer distillation loss.

    Attributes:
        projection_matrix_path: Filesystem path to the .pt file containing
            either the dense top-k projection (dict with 'indices' and
            'likelihoods' tensors of shape [V_student, top_k]) or the sparse
            multi-token format (dict[(student_id, teacher_id)] -> count).
            Loaded lazily on first call by each worker process.
        gold_loss: If True, switch to the gold-loss formulation: split the
            vocab into an exact-token-mapped *common* set (KL) and an
            *uncommon* set (sorted L1).
        xtoken_loss: Modifier inside the gold-loss path. If True, relaxes
            the exact-map threshold to ``>= 0.6`` (vs ``== 1.0``) and adds
            a collision-replacement rule so multi-token projections can
            still contribute exact maps. Requires ``gold_loss=True``.
        temperature: Softmax temperature applied symmetrically to student
            and teacher logits before KL.
        vocab_topk: Microbatch-global top-k size used by the P-KL path
            (``gold_loss=False``). Computed inside the loss fn from full
            teacher logits. Inert when ``gold_loss=True``.
        uncommon_topk: Cap on the L1 uncommon-tail sort in the gold path.
            Defaults to 8192. Inert when ``gold_loss=False``.
        reverse_kl: If True, compute KL(student || teacher) instead of
            KL(teacher || student).
        exact_token_match_only: If True, only aligned pairs flagged as
            'is_correct' contribute to KL; mismatched pairs are masked out.
            Used by the P-KL path only.
        kl_loss_weight: Scalar multiplier on the KL term (P-KL path).
        ce_loss_scale: Scalar multiplier on the CE term (P-KL path).
        dynamic_loss_scaling: If True, rescale KL each step so its detached
            magnitude matches CE (P-KL path).
        student_vocab_size: Full student tokenizer vocab size, used to size
            the projection matrix's student-side (V_s) axis. Runtime-injected
            by ``xtoken_off_policy_distillation.setup`` from ``len(student_tokenizer)``;
            not a user knob in YAML. Sizing V_s from the configured tokenizer
            vocab (rather than ``max(observed student_id) + 1`` from the
            sparse projection file) keeps V_s in lockstep with
            ``logits.shape[-1]`` when the file's highest student ids happen
            to be absent.
        teacher_vocab_size: Full teacher tokenizer vocab size, used to size
            the projection matrix's teacher-side (V_t) axis. Runtime-injected
            symmetrically to ``student_vocab_size`` from
            ``len(teacher_tokenizer)``; not a user knob in YAML.
    """

    projection_matrix_path: Optional[
        str
    ]  # null in the exemplar YAML; set per-run via Hydra CLI, required at runtime
    gold_loss: bool
    xtoken_loss: bool
    temperature: float
    vocab_topk: int
    uncommon_topk: int
    reverse_kl: bool
    exact_token_match_only: bool
    kl_loss_weight: float
    ce_loss_scale: float
    dynamic_loss_scaling: bool
    student_vocab_size: NotRequired[int]
    teacher_vocab_size: NotRequired[int]


class CrossTokenizerDistillationLossDataDict(TypedDict):
    input_ids: torch.Tensor
    input_lengths: torch.Tensor
    token_mask: torch.Tensor
    sample_mask: torch.Tensor
    # Full-vocab teacher logits shipped via CUDA IPC. List[B] of dicts; every
    # entry within one DP rank carries the same ``rank_logits_ipc`` handle
    # (taken on the producer's ``[B_r, T_t, V_t]`` tray) plus its own
    # ``sample_idx_within_rank``. The consumer rebuilds the single rank-level
    # handle and slices ``[mb_start:mb_end]`` for a contiguous view — no
    # ``torch.stack``. Produced by ``Policy.get_full_logits_ipc``. The loss
    # fn either derives a microbatch-global top-k subset internally (P-KL
    # path) or uses full vocab end-to-end (gold-loss path).
    teacher_full_logits_ipc: list[dict[str, Any]]
    alignment_pair_valid: torch.Tensor  # [B, max_pairs]
    alignment_pair_is_correct: torch.Tensor  # [B, max_pairs]
    alignment_student_exact_partition_mask: torch.Tensor
    alignment_teacher_exact_partition_mask: torch.Tensor
    alignment_student_chunk_id: torch.Tensor  # [B, T_s], -1 = no chunk
    alignment_teacher_chunk_id: torch.Tensor  # [B, T_t]
    alignment_num_chunks: torch.Tensor


class CrossTokenizerDistillationLossFn(LossFunction):
    """Cross-tokenizer distillation loss.

    Mode is selected by the ``(gold_loss, xtoken_loss)`` flags:

    - ``(False, False)`` -> P-KL: full-vocab projection KL (student logits
      mapped through the projection matrix M) plus a standard next-token
      student CE term, combined as ``kl_loss_weight * kl + ce_loss_scale * ce``
      — or, when ``dynamic_loss_scaling`` is set, with the KL term rescaled
      each step to match the detached CE magnitude.
    - ``(True, False)`` -> gold-loss: ``(kl_common + l1_uncommon) * T**2``,
      i.e. KL on the exact-mapped *common* partition plus a sorted-L1 term on
      the *uncommon* tail. No CE term.
    - ``(True, True)`` -> gold-loss with the xtoken modifier: same objective,
      but the exact-map threshold is relaxed (``>= 0.6`` instead of ``== 1.0``)
      and a collision-replacement rule lets multi-token projections still
      contribute exact maps.

    ``(False, True)`` is rejected in ``__init__``: xtoken_loss is a modifier
    inside the gold path and is undefined for P-KL.

    Inputs (via ``LossInputType.DISTILLATION_CROSS_TOKENIZER``):
        logits: ``[B, T_s, V_s]`` raw student logits from the worker forward.
        teacher_full_logits: ``[B, T_t, V_t]`` full-vocab teacher logits,
            rebuilt from the CUDA IPC handles by ``prepare_loss_input`` (see
            :func:`nemo_rl.algorithms.x_token.loss_utils.rebuild_teacher_full_logits_from_ipc`).

    Inputs (via ``data: BatchedDataDict``):
        See :class:`CrossTokenizerDistillationLossDataDict`.

    Returns:
        ``(loss, metrics)``. The P-KL path reports ``loss``, ``kl_loss``,
        ``ce_loss``, ``kl_loss_scale``, ``accuracy``, ``proj_accuracy``,
        ``num_valid_samples``, ``num_valid_pairs``. The gold path reports
        ``loss``, ``kl_common``, ``l1_uncommon``, ``accuracy``,
        ``num_valid_samples``, ``num_valid_chunks``.
    """

    loss_type = LossType.TOKEN_LEVEL
    input_type = LossInputType.DISTILLATION_CROSS_TOKENIZER

    def __init__(self, cfg: CrossTokenizerDistillationLossConfig):
        if cfg["xtoken_loss"] and not cfg["gold_loss"]:
            raise ValueError(
                "xtoken_loss=True requires gold_loss=True; xtoken_loss is "
                "a modifier inside the gold path (relaxes the exact-map "
                "threshold and adds collision resolution) and is undefined "
                "in the P-KL path."
            )
        self.projection_matrix_path = cfg["projection_matrix_path"]
        self.gold_loss = cfg["gold_loss"]
        self.xtoken_loss = cfg["xtoken_loss"]
        self.temperature = cfg["temperature"]
        self.vocab_topk = cfg["vocab_topk"]
        self.uncommon_topk = cfg["uncommon_topk"]
        self.reverse_kl = cfg["reverse_kl"]
        self.exact_token_match_only = cfg["exact_token_match_only"]
        self.kl_loss_weight = cfg["kl_loss_weight"]
        self.ce_loss_scale = cfg["ce_loss_scale"]
        self.dynamic_loss_scaling = cfg["dynamic_loss_scaling"]
        self.student_vocab_size = cfg["student_vocab_size"]
        self.teacher_vocab_size = cfg["teacher_vocab_size"]
        # The materialized projection matrix and the derived exact-map
        # partition both live in process-local caches in
        # ``x_token.loss_utils`` (see ``get_sparse_projection_matrix``,
        # ``get_topk_projection``, ``build_exact_token_map``), not on
        # this instance. That keeps the driver-side ``loss_fn`` free of
        # any large CUDA tensors and lets multiple loss instances on
        # the same worker share one load.

    def __call__(
        self,
        data: BatchedDataDict[CrossTokenizerDistillationLossDataDict],
        global_valid_seqs: torch.Tensor,
        global_valid_toks: torch.Tensor,
        logits: torch.Tensor,
        teacher_full_logits: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Compute the cross-tokenizer distillation loss for one microbatch."""
        if self.gold_loss:
            loss, kl_common, l1_uncommon, num_valid_chunks, top1_acc = (
                self._compute_gold(logits, data, teacher_full_logits)
            )
            metrics = {
                "loss": loss.item(),
                "kl_common": kl_common.item(),
                "l1_uncommon": l1_uncommon.item(),
                "accuracy": top1_acc.item(),
                "num_valid_samples": data["input_ids"].shape[0],
                "num_valid_chunks": int(num_valid_chunks.item()),
            }
            return loss, metrics

        kl_loss, num_valid_pairs, proj_acc = self._compute_p_kl(
            logits, data, teacher_full_logits
        )
        ce_loss = self._compute_ce(logits, data, global_valid_toks)

        # Next-token accuracy on the student side, masked to valid tokens.
        # Quick per-step signal on the student's next-token prediction
        # quality.
        with torch.no_grad():
            student_argmax = logits[:, :-1].argmax(dim=-1)
            shift_labels = data["input_ids"][:, 1:]
            acc_mask = (
                data["token_mask"][:, 1:].float()
                * data["sample_mask"].unsqueeze(-1).float()
            )
            denom = acc_mask.sum().clamp(min=1.0)
            accuracy = (
                (student_argmax == shift_labels).float() * acc_mask
            ).sum() / denom

        if self.dynamic_loss_scaling:
            # Dynamic loss scaling:
            #   dls_scale = ce_loss.item() / kl_loss.item()
            #   loss = kl_loss * dls_scale + ce_loss
            # User-supplied `kl_loss_weight` / `ce_loss_scale` are
            # intentionally ignored in this branch.
            kl_detached = kl_loss.detach().abs()
            ce_detached = ce_loss.detach().abs()
            kl_scale = torch.where(
                kl_detached > 0,
                ce_detached / kl_detached,
                torch.ones_like(kl_detached),
            )
            loss = kl_scale * kl_loss + ce_loss
        else:
            kl_scale = torch.tensor(1.0, device=kl_loss.device, dtype=kl_loss.dtype)
            loss = self.kl_loss_weight * kl_loss + self.ce_loss_scale * ce_loss

        metrics = {
            "loss": loss.item(),
            "kl_loss": kl_loss.item(),
            "ce_loss": ce_loss.item(),
            "kl_loss_scale": kl_scale.item(),
            "accuracy": accuracy.item(),
            "proj_accuracy": proj_acc.item(),
            "num_valid_samples": data["input_ids"].shape[0],
            "num_valid_pairs": int(num_valid_pairs.item()),
        }
        return loss, metrics

    # ------------------------------------------------------------------ #
    # Loss-mode implementations
    # ------------------------------------------------------------------ #
    def _compute_p_kl(
        self,
        logits: torch.Tensor,
        data: BatchedDataDict[CrossTokenizerDistillationLossDataDict],
        teacher_full_logits: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """P-KL: chunk-averaged KL over a microbatch-global top-k teacher subset.

        Steps:

        1. Project full-vocab student probs through ``M`` to teacher vocab.
        2. Use the full teacher logits materialized by ``prepare_loss_input``.
        3. Align each predictor with the token it predicts by shifting the
           per-position tensors and chunk ids by one (drop the last
           predictor position and the first chunk label), symmetrically on
           student and teacher. Matches the next-token shift already used by
           the CE term.
        4. Compute one ``global_top_indices [k]`` per microbatch from the
           teacher's importance: ``max`` over flat ``(B*T_t)``, ``topk``
           over ``V_t``. Same vocab subset across every sample/position —
           keeps chunk-averaged KL well-defined.
        5. Slice both the projected student probs and the teacher logits
           to those ``k`` columns.
        6. Build per-token chunk masks from ``alignment_*_chunk_id`` and
           chunk-average via ``bmm`` (shared helper).
        7. Renormalize student chunk distributions inside the top-k subset
           (avg-then-renormalize, log).
        8. Forward (or reverse) KL between chunk distributions.
        """
        T = self.temperature
        device = logits.device
        eps = 1e-10

        b, t_s, v_s = logits.shape
        student_log_probs = torch.log_softmax(logits.float() / T, dim=-1)
        student_probs = student_log_probs.exp()  # [B, T_s, V_s]

        # Project to full teacher vocab. Sparse matmul via M.T trick.
        # `Fp32SparseMM` keeps the op in FP32 on both forward and backward;
        # `torch.sparse.mm` has no BF16 kernel and the worker's autocast(BF16)
        # context wraps loss.backward(), so a plain `.float()` cast isn't
        # enough — the backward kernel is still dispatched as BF16.
        M = get_sparse_projection_matrix(
            self.projection_matrix_path,
            device,
            student_vocab_size=self.student_vocab_size,
            teacher_vocab_size=self.teacher_vocab_size,
        )  # [V_s, V_t] sparse COO, fp32
        flat = student_probs.reshape(b * t_s, v_s)
        # Fp32SparseMM internally computes M.t() @ dense; passing M (not
        # M.t()) avoids a sparse `.t()` on a saved tensor in backward.
        projected_full = Fp32SparseMM.apply(M, flat.t()).t()  # [B*T_s, V_t]
        v_t = projected_full.shape[-1]
        projected_full = projected_full.reshape(b, t_s, v_t)  # [B, T_s, V_t]

        # `teacher_full_logits` [B, T_t, V_t_model] is materialized by
        # `prepare_loss_input` (rebuilt from the IPC handles). Same transport
        # as the gold path consumes; here we additionally compute a
        # microbatch-global top-k inline.
        # HF models commonly pad lm_head out_features beyond len(tokenizer)
        # for embedding/FFN alignment (e.g. Qwen3: tokenizer 151669,
        # lm_head 151936). The projection matrix is sized to the real
        # tokenizer vocab (`self.teacher_vocab_size`); the padded
        # columns aren't real tokens and the projection has no entries
        # there. Slice to the projection's V_t to keep the projected
        # student probs and the teacher logits on the same vocab axis.
        if teacher_full_logits.shape[-1] > v_t:
            teacher_full_logits = teacher_full_logits[..., :v_t]

        # Chunk-alignment data.
        alignment = alignment_from_flat_batch(data)
        student_chunk_id = alignment.student_chunk_id  # [B, T_s] long
        teacher_chunk_id = alignment.teacher_chunk_id  # [B, T_t] long
        pair_valid = alignment.pair_valid  # [B, max_pairs]
        if self.exact_token_match_only:
            pair_valid = pair_valid & alignment.pair_is_correct
        max_chunks = pair_valid.shape[1]

        # A model's distribution at position t predicts the token at t+1, so
        # align each predictor with the token it predicts: drop the last
        # predictor position (nothing past the sequence to predict) and the
        # first chunk label (no predictor precedes it). Applied symmetrically
        # to student and teacher. Same next-token convention the CE term uses.
        projected_full = projected_full[:, :-1, :]
        teacher_full_logits = teacher_full_logits[:, :-1, :]
        student_chunk_id = student_chunk_id[:, 1:]
        teacher_chunk_id = teacher_chunk_id[:, 1:]

        # global_top_indices: max over flat (B*T_t) → [V_t] → topk → [k].
        vocab_topk = min(self.vocab_topk, v_t)
        with torch.no_grad():
            # reshape (not view): the shift above leaves teacher_full_logits
            # non-contiguous.
            teacher_flat = teacher_full_logits.reshape(-1, v_t)
            global_importance = teacher_flat.max(dim=0).values
            global_top_indices = torch.topk(
                global_importance, k=vocab_topk, dim=-1
            ).indices
            global_top_indices = global_top_indices.sort().values  # [k]

        # Slice both sides to the shared [k] columns.
        projected_topk = projected_full[..., global_top_indices]  # [B, T_s-1, k]
        teacher_topk_logits = teacher_full_logits[
            ..., global_top_indices
        ]  # [B, T_t-1, k]
        target_log_probs = torch.log_softmax(
            teacher_topk_logits / T, dim=-1
        )  # [B, T_t-1, k] (renormalized within the [k] subset).

        # Chunk-average both sides via the shared helper.
        proj_chunks, proj_sizes = chunk_average_log_probs(
            projected_topk, student_chunk_id, max_chunks
        )  # [B, C, k] / [B, C]
        tgt_log_chunks, tgt_sizes = chunk_average_log_probs(
            target_log_probs, teacher_chunk_id, max_chunks
        )  # [B, C, k] / [B, C]

        # Renormalize the projected chunk distribution within the top-k
        # subset, then take log. Teacher side is already log-probs (avg of
        # log_softmaxes; not a true log of mean).
        proj_chunks = proj_chunks / (proj_chunks.sum(dim=-1, keepdim=True) + eps)
        proj_log_chunks = (proj_chunks + eps).log()

        chunk_mask = valid_chunk_mask(proj_sizes, tgt_sizes, pair_valid)
        # Compute the DP-global valid-chunk count BEFORE the early
        # return so the collective fires on every rank (a local-only
        # `chunk_mask.any()` check would deadlock when one rank skips
        # and others do not). The reduction at the bottom uses this
        # global count so the KL is normalized by
        # `sum(global_valid_chunks)` rather than a per-rank mean —
        # mirrors the `global_valid_toks` convention used by CE.
        sample_mask_bool = data["sample_mask"].bool()
        valid_bool = chunk_mask & sample_mask_bool.unsqueeze(-1)
        global_valid_chunks = dp_all_reduce_sum(valid_bool.sum())
        if global_valid_chunks.item() == 0:
            zero = torch.zeros((), device=device, dtype=proj_log_chunks.dtype)
            return (
                zero,
                torch.zeros((), device=device, dtype=torch.long),
                zero.detach(),
            )

        # Projection top-1 accuracy: per-chunk argmax of the student-side
        # projected distribution vs the teacher's argmax over the same
        # top-k subset.
        with torch.no_grad():
            proj_top1 = proj_chunks.argmax(dim=-1)  # [B, C]
            tgt_top1 = torch.exp(tgt_log_chunks).argmax(dim=-1)  # [B, C]
            proj_matches = (proj_top1 == tgt_top1) & chunk_mask
            proj_acc = proj_matches.sum().float() / chunk_mask.sum().float().clamp(
                min=1.0
            )

        # KL between chunk-averaged distributions.
        if self.reverse_kl:
            # KL(student || teacher)
            per_chunk_kl = torch.nn.functional.kl_div(
                tgt_log_chunks, proj_log_chunks, reduction="none", log_target=True
            ).sum(dim=-1)
        else:
            # Forward KL(teacher || student)
            per_chunk_kl = torch.nn.functional.kl_div(
                proj_log_chunks, tgt_log_chunks, reduction="none", log_target=True
            ).sum(dim=-1)

        sample_mask = data["sample_mask"].to(per_chunk_kl.dtype)  # [B]
        valid = chunk_mask.to(per_chunk_kl.dtype) * sample_mask.unsqueeze(-1)
        denom = global_valid_chunks.to(per_chunk_kl.dtype).clamp(min=1.0)
        kl_loss = (per_chunk_kl * valid).sum() / denom * (T * T)
        return kl_loss, valid.sum().detach(), proj_acc.detach()

    def _compute_gold(
        self,
        logits: torch.Tensor,
        data: BatchedDataDict[CrossTokenizerDistillationLossDataDict],
        teacher_full_logits: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Gold-loss path: KL on common (exact-mapped) vocab + L1 on uncommon.

        1. Lazy-build the exact-token map (cached per device).
        2. Use the full teacher logits materialized by ``prepare_loss_input``.
        3. ``log_softmax`` on full vocab both sides; shift each predictor to
           the token it predicts (drop the last predictor position, first
           chunk label); chunk-average via the shared helper.
        4. Slice each chunk-averaged tensor to ``common_*`` indices and
           compute (forward or reverse) KL, reduced as
           ``sum / valid_chunk.sum()`` where ``valid_chunk`` is the
           geometric chunk mask AND'd with ``sample_mask`` (mirrors the
           P-KL path).
        5. Slice to ``uncommon_*`` indices, ``.exp()`` to probs, sort/topk
           descending (capped at ``self.uncommon_topk``), truncate to
           ``min(student_len, teacher_len)``, L1 with ``reduction="none"``
           summed over vocab and meaned across valid chunks.
        6. Combine: ``loss = (kl_common + l1_uncommon) * T**2``.
        7. Top-1 accuracy on the common slice over valid chunks.

        Returns ``(loss, kl_common, l1_uncommon, num_valid_chunks, top1_acc)``.
        Components other than ``loss`` are detached.
        """
        T = self.temperature
        device = logits.device

        exact_map = build_exact_token_map(
            self.projection_matrix_path,
            device,
            xtoken_loss=self.xtoken_loss,
            teacher_vocab_size=self.teacher_vocab_size,
        )
        common_s = exact_map["common_student"]
        common_t = exact_map["common_teacher"]
        uncommon_s = exact_map["uncommon_student"]
        uncommon_t = exact_map["uncommon_teacher"]
        v_teacher = self.teacher_vocab_size

        # `teacher_full_logits` [B, T_t, V_t_model] is materialized by
        # `prepare_loss_input` (rebuilt from the IPC handles).
        # Drop any padded lm_head vocab beyond the real tokenizer vocab —
        # the exact-token map's t-axis is bounded by `teacher_vocab_size`,
        # so chunked teacher log-probs must use the same axis. See the
        # matching note in `_compute_p_kl` for why the model vocab can
        # exceed `len(tokenizer)`.
        if teacher_full_logits.shape[-1] > v_teacher:
            teacher_full_logits = teacher_full_logits[..., :v_teacher]

        student_log_probs = torch.log_softmax(
            logits.float() / T, dim=-1
        )  # [B, T_s, V_s]
        teacher_log_probs = torch.log_softmax(
            teacher_full_logits / T, dim=-1
        )  # [B, T_t, V_t]

        alignment = alignment_from_flat_batch(data)
        student_chunk_id = alignment.student_chunk_id
        teacher_chunk_id = alignment.teacher_chunk_id
        pair_valid = alignment.pair_valid
        max_chunks = pair_valid.shape[1]

        # A model's distribution at position t predicts the token at t+1, so
        # align each predictor with the token it predicts: drop the last
        # predictor position and the first chunk label, symmetrically on
        # student and teacher. See the matching note in `_compute_p_kl`.
        student_log_probs = student_log_probs[:, :-1, :]
        teacher_log_probs = teacher_log_probs[:, :-1, :]
        student_chunk_id = student_chunk_id[:, 1:]
        teacher_chunk_id = teacher_chunk_id[:, 1:]

        student_chunks, s_sizes = chunk_average_log_probs(
            student_log_probs, student_chunk_id, max_chunks
        )  # [B, C, V_s] / [B, C]
        teacher_chunks, t_sizes = chunk_average_log_probs(
            teacher_log_probs, teacher_chunk_id, max_chunks
        )  # [B, C, V_t] / [B, C]

        chunk_mask = valid_chunk_mask(s_sizes, t_sizes, pair_valid)
        # Match the P-KL path: a chunk only contributes if its alignment is
        # geometrically valid AND its sample isn't masked out by sample_mask.
        sample_mask = data["sample_mask"]  # [B]
        valid_chunk = chunk_mask & sample_mask.bool().unsqueeze(-1)
        zero_dtype = student_log_probs.dtype
        # Compute the DP-global valid-chunk count BEFORE any potentially
        # divergent early return so the collective fires on every rank;
        # both `kl_common` and `l1_uncommon` use this as their denom so
        # the loss is normalized by `sum(global_valid_chunks)`, not a
        # per-rank mean.
        global_valid_chunks = dp_all_reduce_sum(valid_chunk.sum())
        if global_valid_chunks.item() == 0:
            zero = torch.zeros((), device=device, dtype=zero_dtype)
            return (
                zero,
                zero.detach(),
                zero.detach(),
                torch.zeros((), device=device, dtype=torch.long),
                zero.detach(),
            )

        # ---------------------- KL on common ----------------------
        if common_s.numel() > 0:
            student_common = student_chunks[:, :, common_s]  # [B, C, N_common]
            teacher_common = teacher_chunks[:, :, common_t]  # [B, C, N_common]
            if self.reverse_kl:
                kl_per_elem = torch.nn.functional.kl_div(
                    teacher_common,
                    student_common,
                    reduction="none",
                    log_target=True,
                )
            else:
                kl_per_elem = torch.nn.functional.kl_div(
                    student_common,
                    teacher_common,
                    reduction="none",
                    log_target=True,
                )
            kl_per_chunk = kl_per_elem.sum(dim=-1) * valid_chunk  # [B, C]
            kl_common = kl_per_chunk.sum() / global_valid_chunks.to(
                kl_per_chunk.dtype
            ).clamp(min=1.0)
        else:
            kl_common = torch.zeros(
                (), device=device, dtype=zero_dtype, requires_grad=True
            )
            student_common = None
            teacher_common = None

        # -------------------- L1 on uncommon ----------------------
        uncommon_topk = self.uncommon_topk
        if uncommon_s.numel() > 0 or uncommon_t.numel() > 0:
            student_unc = student_chunks[:, :, uncommon_s][
                valid_chunk
            ]  # [N_valid, N_u_s]
            teacher_unc = teacher_chunks[:, :, uncommon_t][
                valid_chunk
            ]  # [N_valid, N_u_t]
            n_valid = student_unc.shape[0]
            max_uncommon = min(
                student_unc.shape[-1],
                teacher_unc.shape[-1],
                uncommon_topk,
            )
            if n_valid > 0 and max_uncommon > 0:
                student_unc_probs = student_unc.exp()
                teacher_unc_probs = teacher_unc.exp()
                if student_unc_probs.shape[-1] > max_uncommon:
                    student_sorted = torch.topk(
                        student_unc_probs, k=max_uncommon, dim=-1, largest=True
                    ).values
                else:
                    student_sorted = student_unc_probs.sort(
                        dim=-1, descending=True
                    ).values
                if teacher_unc_probs.shape[-1] > max_uncommon:
                    teacher_sorted = torch.topk(
                        teacher_unc_probs, k=max_uncommon, dim=-1, largest=True
                    ).values
                else:
                    teacher_sorted = teacher_unc_probs.sort(
                        dim=-1, descending=True
                    ).values
                min_len = min(student_sorted.shape[-1], teacher_sorted.shape[-1])
                student_sorted = student_sorted[:, :min_len]
                teacher_sorted = teacher_sorted[:, :min_len]
                l1_per_chunk = torch.nn.functional.l1_loss(
                    student_sorted, teacher_sorted, reduction="none"
                ).sum(dim=-1)
                l1_uncommon = l1_per_chunk.sum() / global_valid_chunks.to(
                    l1_per_chunk.dtype
                ).clamp(min=1.0)
            else:
                l1_uncommon = torch.zeros(
                    (), device=device, dtype=zero_dtype, requires_grad=True
                )
        else:
            l1_uncommon = torch.zeros(
                (), device=device, dtype=zero_dtype, requires_grad=True
            )

        # -------------------- Top-1 accuracy ----------------------
        with torch.no_grad():
            if student_common is not None:
                s_common_valid = student_common[valid_chunk]
                t_common_valid = teacher_common[valid_chunk]
                matches = (
                    (s_common_valid.argmax(dim=-1) == t_common_valid.argmax(dim=-1))
                    .sum()
                    .float()
                )
                top1_acc = matches / valid_chunk.sum().float().clamp(min=1.0)
            else:
                top1_acc = torch.zeros((), device=device, dtype=zero_dtype)

        loss = (kl_common + l1_uncommon) * (T * T)
        return (
            loss,
            kl_common.detach(),
            l1_uncommon.detach(),
            valid_chunk.sum().detach(),
            top1_acc.detach(),
        )

    def _compute_ce(
        self,
        logits: torch.Tensor,
        data: BatchedDataDict[CrossTokenizerDistillationLossDataDict],
        global_valid_toks: torch.Tensor,
    ) -> torch.Tensor:
        """Standard next-token CE on the student side.

        Uses ``token_mask[:, 1:]`` so padded tokens don't contribute.
        """
        input_ids = data["input_ids"]
        token_mask = data["token_mask"][:, 1:]
        sample_mask = data["sample_mask"]

        shift_logits = logits[:, :-1].contiguous()
        shift_labels = input_ids[:, 1:].contiguous()

        per_token_ce = torch.nn.functional.cross_entropy(
            shift_logits.reshape(-1, shift_logits.shape[-1]).float(),
            shift_labels.reshape(-1),
            reduction="none",
        ).reshape(shift_labels.shape)

        mask = token_mask.float() * sample_mask.unsqueeze(-1).float()
        return masked_mean(
            per_token_ce, mask, global_normalization_factor=global_valid_toks
        )
