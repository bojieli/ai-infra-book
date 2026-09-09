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

import math
import random
import re
import warnings
from functools import partial, wraps
from typing import Any, Optional

import numpy as np
import torch
from transformers import (
    AutoProcessor,
    AutoTokenizer,
    PreTrainedTokenizerBase,
)

from nemo_rl.data.chat_templates import COMMON_CHAT_TEMPLATES
from nemo_rl.models.policy import TokenizerConfig
from nemo_rl.utils.logger import Logger


def get_gdpo_reward_component_keys(batch) -> list:
    """Return batch keys that are reward components (reward1, reward2, ...) in sorted order."""
    keys = [k for k in batch.keys() if re.match(r"reward\d+$", str(k))]
    return sorted(keys, key=lambda k: int(re.search(r"\d+", str(k)).group()))


def calculate_kl(
    logprobs: torch.Tensor,
    logprobs_reference: torch.Tensor,
    kl_type: str = "k3",
    input_clamp_value: float | None = 20.0,
    output_clamp_value: float | None = 10.0,
) -> torch.Tensor:
    """Calculates a per-token estimate of the KL Divergence between two logprobs.

    From Schulman 2020, http://joschu.net/blog/kl-approx.html.

    Args:
        logprobs: torch.Tensor (b, s)
        logprobs_reference: torch.Tensor (b, s)
        kl_type: Type of KL approximation to use. Valid values: "k1", "k2", "k3".
        input_clamp_value: Optional clamping value for logr to prevent numerical instability.
                           If None, no clamping is applied.
        output_clamp_value: Optional clamping value for kl to prevent numerical instability.
                           If None, no clamping is applied.

    Returns:
        torch.Tensor: Per-token KL penalty values (b, s)
    """
    logr = logprobs_reference - logprobs
    if input_clamp_value is not None:
        logr = logr.clamp(min=-input_clamp_value, max=input_clamp_value)

    if kl_type == "k1":
        kl = -logr

    elif kl_type == "k2":
        kl = torch.square(logr) / 2

    elif kl_type == "k3":
        kl = torch.exp(logr) - 1 - logr

    else:
        raise ValueError(f"Invalid KL type: {kl_type}")

    if output_clamp_value is not None:
        kl = kl.clamp(min=-output_clamp_value, max=output_clamp_value)

    return kl


def calculate_baseline_and_std_per_prompt(
    prompts: torch.Tensor,
    rewards: torch.Tensor,
    valid_mask: torch.Tensor,
    leave_one_out_baseline: bool = True,
    std_rewards: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Function to compute a baseline for each (prompt, response) pair in the batch.

    The same baseline is calculated for each prompt. Samples set to 0 in 'valid_mask'
    are not included in the baseline calculation.

    prompts:    tensor (b, s)     Tensor of prompts the model used. May be on any device
    rewards:    tensor (b,)       Float-valued rewards. May be on any device
    valid_mask: tensor (b,)       Vector of 0/1, where 0 is to ignore and 1 is to keep
    leave_one_out_baseline: bool  Compute an unbiased baseline by leaving out the sample that
                                  the baseline is for (from RLOO https://arxiv.org/abs/2402.14740)
    std_rewards: tensor (b,)      Optional separate reward tensor used only for the std
                                  calculation. Defaults to `rewards`. Useful for DAPO,
                                  which needs std on the raw task metric for dynamic
                                  sampling filtering while keeping baseline on the
                                  shaped reward.

    Returns:
    tensor (b,), tensor (b,) of baselines and std on the same device as 'rewards'
    """
    if std_rewards is None:
        std_rewards = rewards
    unique_prompts = torch.unique(prompts, dim=0)

    baseline = torch.zeros_like(rewards)
    sq_baseline = torch.zeros_like(rewards)
    std = torch.zeros_like(rewards)
    device_ordinal = rewards.get_device()
    if device_ordinal == -1:
        reward_device = torch.device("cpu")
    else:
        reward_device = torch.device(f"cuda:{device_ordinal}")

    for i in range(len(unique_prompts)):
        is_matching_prompt = (prompts == unique_prompts[i]).all(1)
        prompt_idx = torch.arange(len(prompts), device=reward_device)[
            is_matching_prompt
        ]

        if leave_one_out_baseline:
            baseline_mask_matrix = (1 - torch.eye(len(prompt_idx))).to(reward_device)
        else:
            baseline_mask_matrix = torch.ones((len(prompt_idx), len(prompt_idx))).to(
                reward_device
            )

        if valid_mask[prompt_idx].sum() <= 1:
            # Ignore sample: there are no valid responses, so set baseline equal to reward
            # to ignore it in the loss computation
            baseline[prompt_idx] = rewards[prompt_idx]
        else:
            num_valid = valid_mask[prompt_idx].float().sum() - int(
                leave_one_out_baseline
            )
            prompt_baseline = (
                torch.matmul(
                    baseline_mask_matrix, rewards[prompt_idx] * valid_mask[prompt_idx]
                )
                / num_valid
            )
            std_prompt_baseline = (
                prompt_baseline
                if std_rewards is rewards
                else torch.matmul(
                    baseline_mask_matrix,
                    std_rewards[prompt_idx] * valid_mask[prompt_idx],
                )
                / num_valid
            )
            std_prompt_baseline_square = (
                torch.matmul(
                    baseline_mask_matrix,
                    torch.pow(std_rewards[prompt_idx], 2) * valid_mask[prompt_idx],
                )
                / num_valid
            )

            baseline[prompt_idx] = prompt_baseline
            sq_baseline[prompt_idx] = std_prompt_baseline_square
            std[prompt_idx] = (
                (
                    (std_prompt_baseline_square - std_prompt_baseline.square())
                    * (num_valid / (num_valid - 1))
                )
                .sqrt()
                .nan_to_num(0)
            )

    return baseline, std


def surpress_user_warnings(f):  # type: ignore
    @wraps(f)
    def wrapper(*args, **kwargs):  # type: ignore
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            output = f(*args, **kwargs)
        return output

    return wrapper


def masked_mean(
    values: torch.Tensor,
    mask: torch.Tensor,
    dim: Optional[int] = None,
    global_normalization_factor: Optional[torch.Tensor | float] = None,
):
    """Computes the mean of a microbatch, using a global statistic as the normalization factor."""
    normalization_factor = (
        torch.sum(mask, dim=dim)
        if global_normalization_factor is None
        else global_normalization_factor
    )
    return torch.sum(values * mask, dim=dim) / (normalization_factor + 1e-8)


def mask_out_neg_inf_logprobs(
    logprobs: torch.Tensor, mask: torch.Tensor, logprobs_name: str
) -> torch.Tensor:
    """Mask out negative infinity log probabilities.

    Handling sampling mask mismatch:
    vLLM samples token X from top-k/p filtered distribution -> generation_logprobs[X] is always finite (e.g., -5.41)
    during training: policy computes logprobs with same top-k/p settings, but the distribution can be slightly different
    token X may fall outside the training policy's top-k/p set -> curr_logprobs[X] = -inf, prev_logprobs[X] = -inf
    Detect positions with -inf in any logprobs (generation_logprobs is always finite for valid tokens)

    Args:
        logprobs: Log probabilities.
        mask: Mask.
        logprobs_name: Name of the logprobs tensor. Used for printing warning messages.

    Returns:
        Masked log probabilities.
    """
    is_neginf = torch.isinf(logprobs)
    neginf_count = (is_neginf & mask.bool()).sum().item()
    if neginf_count > 0:
        print(
            f"[WARNING]: {neginf_count}/{int(mask.sum().item())} valid tokens have -inf in {logprobs_name} "
            "(policy top-k/top-p mismatch). Masking out these positions."
        )

    mask = mask * (~is_neginf).float()
    logprobs = torch.where(mask.bool(), logprobs, 0.0)

    return logprobs


def set_seed(seed: int) -> None:
    """Sets the seed for python, numpy, and pytorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_tokenizer(
    tokenizer_config: TokenizerConfig, get_processor: bool = False
) -> PreTrainedTokenizerBase:
    """Get the tokenizer and set pad token to eos token if it is not already set.

    This function initializes a tokenizer from the Hugging Face transformers library
    and configures it with appropriate chat templates and padding tokens.

    Args:
        tokenizer_config: A dictionary containing tokenizer configuration.
            Required keys:
                - name: The name or path of the pretrained tokenizer
            Optional keys:
                - chat_template: The chat template to use. Can be:
                    - None: Uses a passthrough template that just returns message content
                    - "default": Uses the tokenizer's default template
                    - A custom jinja2 template string
                    If not specified, the tokenizer's default template will be used.
        get_processor: Whether to return a processor (via AutoProcessor) instead of a tokenizer.

    Returns:
        PreTrainedTokenizerBase: The configured tokenizer instance

    Examples:
        ```{doctest}
        >>> from transformers import AutoTokenizer
        >>> from nemo_rl.algorithms.utils import get_tokenizer
        >>> # not specifying a chat template uses the tokenizer's default
        >>> config = {"name": "meta-llama/Llama-3.2-1B-Instruct"}
        >>> tokenizer = get_tokenizer(config)
        No chat template provided, using tokenizer's default
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful AI assistant."},
        ...     {"role": "user", "content": "Hello!"}
        ... ]
        >>> formatted = tokenizer.apply_chat_template(messages, tokenize=False)
        >>> assert formatted == AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B-Instruct").apply_chat_template(messages, tokenize=False)

        >>> # Using a passthrough template
        >>> config = {
        ...     "name": "meta-llama/Llama-3.2-1B-Instruct",
        ...     "chat_template": None
        ... }
        >>> tokenizer = get_tokenizer(config)
        Using passthrough chat template
        >>> formatted = tokenizer.apply_chat_template(messages, tokenize=False)
        >>> assert formatted == "".join(msg["content"] for msg in messages)

        >>> # Using a custom template
        >>> config = {
        ...     "name": "meta-llama/Llama-3.2-1B-Instruct",
        ...     "chat_template": "{% for message in messages %}{{ ' START: ' + message['content'] + ' END.' }}{% endfor %}"
        ... }
        >>> tokenizer = get_tokenizer(config)
        Using custom chat template
        >>> formatted = tokenizer.apply_chat_template(messages, tokenize=False)
        >>> assert formatted == " START: You are a helpful AI assistant. END. START: Hello! END."

        >>> # Requesting a processor (for multimodal models like Qwen-VL)
        >>> config = {"name": "Qwen/Qwen2.5-VL-3B-Instruct"}
        >>> processor = get_tokenizer(config, get_processor=True)
        No chat template provided, using tokenizer's default
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful AI assistant."},
        ...     {"role": "user", "content": "Hello!"}
        ... ]
        >>> formatted = processor.tokenizer.apply_chat_template(messages, tokenize=False)
        >>> assert formatted == AutoTokenizer.from_pretrained(
        ...     "Qwen/Qwen2.5-VL-3B-Instruct", trust_remote_code=True
        ... ).apply_chat_template(messages, tokenize=False)
        >>> assert processor.pad_token_id == processor.tokenizer.pad_token_id
        >>>
        ```
    """
    processor = None

    if get_processor:
        processor = AutoProcessor.from_pretrained(
            tokenizer_config["name"], trust_remote_code=True, use_fast=True
        )
        tokenizer = processor.tokenizer
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_config["name"], trust_remote_code=True
        )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if "chat_template" in tokenizer_config:
        if tokenizer_config["chat_template"] is None:
            print("Using passthrough chat template")
            tokenizer.chat_template = COMMON_CHAT_TEMPLATES.passthrough_prompt_response
        elif tokenizer_config["chat_template"].lower() == "default":
            print("Using tokenizer's default chat template")
        elif tokenizer_config["chat_template"].endswith(".jinja"):
            # Load template from file
            template_path = tokenizer_config["chat_template"]
            print(f"Loading chat template from file: {template_path}")
            with open(template_path, "r") as f:
                tokenizer.chat_template = f.read()
        else:
            print("Using custom chat template")
            tokenizer.chat_template = tokenizer_config["chat_template"]
    else:
        print("No chat template provided, using tokenizer's default")

    if (
        "chat_template_kwargs" in tokenizer_config
        and tokenizer_config["chat_template_kwargs"] is not None
    ):
        assert isinstance(tokenizer_config["chat_template_kwargs"], dict), (
            "chat_template_kwargs should be a dictionary"
        )
        tokenizer.apply_chat_template = partial(
            tokenizer.apply_chat_template, **tokenizer_config["chat_template_kwargs"]
        )

    # The "tokenizer" is passed to the policy workers only to use the pad/eos/bos tokens for extra padding and processing of the tokenized messages. That is the only reason it is needed.
    # However, the dataloader needs the processor for multimodal data preprocessing, so the processor is needed for the dataloader (only tokenizer is NOT enough).
    # Inheriting special keys from the tokenizer is a minimal change that doesn't disturb the rest of the SFT pipeline
    if processor is not None:
        processor.pad_token = tokenizer.pad_token
        processor.eos_token = tokenizer.eos_token
        processor.bos_token = tokenizer.bos_token
        processor.pad_token_id = tokenizer.pad_token_id
        processor.eos_token_id = tokenizer.eos_token_id
        processor.bos_token_id = tokenizer.bos_token_id
        # copy name_or_path from tokenizer to processor for logging
        processor.name_or_path = tokenizer.name_or_path
        # copy chat_template so processor.apply_chat_template() works for
        # models whose processor doesn't ship its own template (e.g. Qwen3.5)
        if not getattr(processor, "chat_template", None) and getattr(
            tokenizer, "chat_template", None
        ):
            processor.chat_template = tokenizer.chat_template
        if hasattr(processor, "feature_extractor") and "audio" in tokenizer_config:
            if (
                "sampling_rate" in tokenizer_config["audio"]
                and tokenizer_config["audio"]["sampling_rate"]
                != processor.feature_extractor.sampling_rate
            ):
                new_sampling_rate = tokenizer_config["audio"]["sampling_rate"]
                warnings.warn(
                    f"Overriding audio sampling rate from {processor.feature_extractor.sampling_rate} to {new_sampling_rate}"
                )
                processor.feature_extractor.sampling_rate = new_sampling_rate
        if hasattr(processor, "video_processor") and "video" in tokenizer_config:
            if (
                "fps" in tokenizer_config["video"]
                and tokenizer_config["video"]["fps"] != processor.video_processor.fps
            ):
                # override the video loading fps
                new_fps = tokenizer_config["video"]["fps"]
                warnings.warn(
                    f"Overriding video fps from {processor.video_processor.fps} to {new_fps}"
                )
                processor.video_processor.fps = new_fps
            # fps and num_frames cannot co-exist, but let it crash later
            if (
                "num_frames" in tokenizer_config["video"]
                and tokenizer_config["video"]["num_frames"]
                != processor.video_processor.num_frames
            ):
                new_num_frames = tokenizer_config["video"]["num_frames"]
                warnings.warn(
                    f"Overriding video num_frames from {processor.video_processor.num_frames} to {new_num_frames}"
                )
                processor.video_processor.num_frames = new_num_frames

    return tokenizer if processor is None else processor


def maybe_pad_last_batch(batch: dict, dp_size: int, mbs: int) -> dict:
    """Pads the given batch so that its size is divisible by (mbs * dp_size).

    Args:
        batch (dict): The batch to pad.
        dp_size (int): Data parallel size.
        mbs (int): Micro batch size.

    Returns:
        dict: The padded batch.
    """
    min_padding = (math.ceil(batch.size / (mbs * dp_size)) * mbs * dp_size) - batch.size
    if min_padding > 0:
        print(f"Padding last validation batch with {min_padding} padding samples")
        # Pad input_ids
        batch["input_ids"] = torch.cat(
            [
                batch["input_ids"],
                batch["input_ids"][-1].unsqueeze(0).repeat(min_padding, 1),
            ]
        )
        # Pad input_lengths
        batch["input_lengths"] = torch.cat(
            [
                batch["input_lengths"],
                batch["input_lengths"][-1].unsqueeze(0).repeat(min_padding),
            ]
        )
        if "token_mask" in batch:
            # Pad token_mask
            batch["token_mask"] = torch.cat(
                [
                    batch["token_mask"],
                    batch["token_mask"][-1].unsqueeze(0).repeat(min_padding, 1),
                ]
            )
        # Pad sample_mask
        batch["sample_mask"] = torch.cat(
            [
                batch["sample_mask"],
                torch.zeros_like(batch["sample_mask"][-1])
                .unsqueeze(0)
                .repeat(min_padding),
            ]
        )

        if "reference_policy_logprobs" in batch:
            # Pad reference_policy_logprobs
            batch["reference_policy_logprobs"] = torch.cat(
                [
                    batch["reference_policy_logprobs"],
                    batch["reference_policy_logprobs"][-1]
                    .unsqueeze(0)
                    .repeat(min_padding, 1),
                ]
            )
    return batch


def print_performance_metrics(
    train_results: dict[str, float],
    metrics: dict[str, Any],
    timing_metrics: dict[str, float],
    master_config: dict,
) -> dict[str, float]:
    """Print performance metrics for GRPO."""

    # =====================================================
    # Generate Token Imbalance Visualization
    # =====================================================
    def visualize_per_worker_load(per_worker_token_counts: dict[int, int]) -> float:
        per_worker_token_counts_list = [
            v for k, v in sorted(per_worker_token_counts.items())
        ]
        per_worker_load_ratio = [
            v / max(per_worker_token_counts_list) for v in per_worker_token_counts_list
        ]
        max_rows_to_print = 1000
        bar_length = 20
        print("  • Visualizing Token Imbalance per Generation Worker:")
        for i in range(min(len(per_worker_token_counts_list), max_rows_to_print)):
            print(
                f"    - Generated Tokens from Worker {i:3.0f}:"
                f"{'■' * int(per_worker_load_ratio[i] * bar_length)}"
                f"{'□' * (bar_length - int(per_worker_load_ratio[i] * bar_length))}"
                f" Count: {per_worker_token_counts_list[i] / 1000:.1f}K"
            )
        estimated_idle_ratio = 1 - sum(per_worker_load_ratio) / len(
            per_worker_load_ratio
        )
        print(f"  • Average Token Imbalance: {100 * estimated_idle_ratio:.2f}%")
        return estimated_idle_ratio

    print("\n🔍 Performance Metrics:")
    performance_metrics = {}

    if "per_worker_token_counts" in metrics:
        # Can be a list of each trajectory
        if isinstance(metrics["per_worker_token_counts"], list):
            per_worker_token_counts = {}
            for trajectory_metrics in metrics["per_worker_token_counts"]:
                for worker_idx, token_count in trajectory_metrics.items():
                    per_worker_token_counts[worker_idx] = (
                        per_worker_token_counts.get(worker_idx, 0) + token_count
                    )
        elif isinstance(metrics["per_worker_token_counts"], dict):
            per_worker_token_counts = metrics["per_worker_token_counts"]
        else:
            per_worker_token_counts = None

        if per_worker_token_counts is not None:
            average_token_imbalance = visualize_per_worker_load(per_worker_token_counts)
            performance_metrics["average_token_imbalance"] = average_token_imbalance

    if "mean_total_tokens_per_sample" in metrics:
        print(
            f"  • Mean Total Tokens per Sample: {metrics['mean_total_tokens_per_sample']:.2f}"
        )

    # =====================================================
    # vLLM Logger Metrics (inflight batch sizes, num pending samples, etc.)
    # =====================================================
    def resize_timeline(data, new_size):
        old_size = len(data)
        x_old = np.linspace(0, 1, old_size)
        x_new = np.linspace(0, 1, new_size)
        return np.interp(x_new, x_old, data)

    def get_min_idle_time(
        metric_dict: dict[int, list[int]], timeline_interval: float
    ) -> float:
        min_idle_time = float("inf")
        for _, metric_values in metric_dict.items():
            count_zeros = lambda x: sum(v == 0 for v in x)
            idle_time = count_zeros(metric_values) * timeline_interval
            min_idle_time = min(min_idle_time, idle_time)
        return min_idle_time

    def visualize_per_worker_timeline(
        metric_dict: dict[int, list[int]],
        metric_name: str,
        timeline_interval: float | None,
    ) -> None:
        dp_ranks = list(metric_dict.keys())
        max_rows_to_print = 1000
        max_timeline_length = 50
        marker = {0: "▃", 1: "▅", 2: "▆", 3: "▉"}
        zero_marker = "▁"

        max_value = max((max(v) if v else 0) for v in metric_dict.values())
        bin_width = (max_value + 1) / len(marker)

        print(f"  - {metric_name}:")
        print(f"    - Max value: {max_value}")
        if timeline_interval is not None:
            print(
                f"    - Min idle time: {get_min_idle_time(metric_dict, timeline_interval)} s"
            )
        print(
            f"    - Timeline (0: {zero_marker}, {', '.join(f'{1.0 if k == 0 else k * (max_value / len(marker))}-{(k + 1) * (max_value / len(marker))}: {marker[k]}' for k in marker.keys())}):"
        )
        for dp_idx, metric_values in metric_dict.items():
            if dp_idx > max_rows_to_print:
                break
            timeline = []
            length = len(metric_values)
            if timeline_interval is not None:
                count_zeros = lambda x: sum(v == 0 for v in x)
                idle = count_zeros(metric_values) * timeline_interval
                active = length * timeline_interval - idle
            if length > max_timeline_length:
                resized_metric_values = resize_timeline(
                    metric_values, max_timeline_length
                )
            else:
                resized_metric_values = metric_values

            for i, value in enumerate(resized_metric_values):
                m = (
                    zero_marker
                    if value == 0
                    else marker[min(int(value // bin_width), len(marker) - 1)]
                )
                timeline.append(m)
            if timeline_interval is not None:
                print(
                    f"    - Generation Worker {dp_idx:3.0f}: {''.join(timeline)} (Active: {active:.2f} s, Idle: {idle:.2f} s)"
                )
            else:
                print(f"    - Generation Worker {dp_idx:3.0f}: {''.join(timeline)}")

    is_vllm_metrics_logger_enabled = master_config.policy["generation"].get(
        "vllm_cfg", {}
    ).get("enable_vllm_metrics_logger", False) and master_config.policy[
        "generation"
    ].get("vllm_cfg", {}).get("async_engine", False)
    generation_logger_metrics = metrics.get("generation_logger_metrics", {})
    if is_vllm_metrics_logger_enabled and generation_logger_metrics:
        vllm_logger_metrics = generation_logger_metrics
        # vllm_logger_metrics: dict[str (metric_name), dict[int (dp_idx), list[int] (metric_values)]]
        # metric_name: "inflight_batch_sizes" or "num_pending_samples"

        assert "inflight_batch_sizes" in vllm_logger_metrics, (
            "inflight_batch_sizes not found in vllm_logger_metrics"
        )
        assert "num_pending_samples" in vllm_logger_metrics, (
            "num_pending_samples not found in vllm_logger_metrics"
        )
        assert isinstance(vllm_logger_metrics["inflight_batch_sizes"], dict), (
            "inflight_batch_sizes must be a dictionary"
        )
        assert isinstance(vllm_logger_metrics["num_pending_samples"], dict), (
            "num_pending_samples must be a dictionary"
        )

        vllm_metrics_logger_interval = master_config.policy["generation"]["vllm_cfg"][
            "vllm_metrics_logger_interval"
        ]
        print("  • vLLM Logger Metrics:")
        # Visualize the inflight batch sizes timeline
        if len(vllm_logger_metrics["inflight_batch_sizes"].values()) > 0:
            visualize_per_worker_timeline(
                vllm_logger_metrics["inflight_batch_sizes"],
                "Inflight Batch Sizes",
                vllm_metrics_logger_interval,
            )
        if len(vllm_logger_metrics["num_pending_samples"].values()) > 0:
            max_num_pending_samples = max(
                (max(v) if v else 0)
                for v in vllm_logger_metrics["num_pending_samples"].values()
            )
            # If there is at least one pending sample, visualize the timeline
            if max_num_pending_samples > 0:
                visualize_per_worker_timeline(
                    vllm_logger_metrics["num_pending_samples"],
                    "Num Pending Samples",
                    None,
                )

    # =====================================================
    # Throughputs
    # =====================================================

    policy_and_reference_logprobs_time = timing_metrics["policy_and_reference_logprobs"]
    policy_training_time = timing_metrics["policy_training"]
    total_time = timing_metrics["total_step_time"]
    refit_time = (
        timing_metrics["weight_sync"]
        if "weight_sync" in timing_metrics
        else timing_metrics["prepare_for_generation/total"]
    )
    if "generation" in timing_metrics:  # Sync GRPO
        generation_time = timing_metrics["generation"]
    else:  # Async GRPO
        # If the training time is greater than the generation time, we include the idle time caused by training as part of the generation time.
        # if training time > generation time, generation time = training time
        # if training time < generation time, generation time = training time + exposed generation time
        generation_time = (
            timing_metrics["exposed_generation"]
            + timing_metrics["policy_and_reference_logprobs"]
            + timing_metrics["policy_training"]
        )

    num_nodes = master_config.cluster["num_nodes"]
    gpus_per_node = master_config.cluster["gpus_per_node"]
    total_num_gpus = num_nodes * gpus_per_node
    colocated_inference = master_config.policy["generation"]["colocated"]["enabled"]

    # Idle Time from Training Worker (Async GRPO only)
    grpo_config = master_config.grpo
    if (
        "async_grpo" in grpo_config and grpo_config["async_grpo"]["enabled"]
    ) and not colocated_inference:
        # async grpo
        exposed_generation_time = timing_metrics["exposed_generation"]
        training_worker_idle_time_ratio = (
            0
            if exposed_generation_time > 0.1
            else exposed_generation_time
            / (
                policy_training_time
                + policy_and_reference_logprobs_time
                + exposed_generation_time
                + refit_time
            )
        )
        print(
            f"  • Training Worker Idle Time Ratio: {100 * training_worker_idle_time_ratio:.2f}%"
        )
        performance_metrics["training_worker_idle_time_ratio"] = (
            training_worker_idle_time_ratio
        )

    number_of_samples_per_step = (
        grpo_config["num_prompts_per_step"] * grpo_config["num_generations_per_prompt"]
    )

    if colocated_inference:
        training_num_gpus = total_num_gpus
        generation_num_gpus = total_num_gpus
    else:
        generation_num_nodes = (
            master_config.policy["generation"]["colocated"]["resources"]["num_nodes"]
            or 1
        )
        generation_num_gpus = (
            master_config.policy["generation"]["colocated"]["resources"][
                "gpus_per_node"
            ]
            * generation_num_nodes
        )
        training_num_gpus = total_num_gpus - generation_num_gpus

    e2e_samples_per_sec_per_gpu = (
        number_of_samples_per_step / total_time / total_num_gpus
    )

    e2e_tokens_per_sec_per_gpu = (
        metrics["total_num_tokens"] / total_time / total_num_gpus
    )
    policy_training_tokens_per_sec_per_gpu = (
        metrics["total_num_tokens"] / policy_training_time / training_num_gpus
    )
    policy_and_reference_logprobs_tokens_per_sec_per_gpu = (
        metrics["total_num_tokens"]
        / policy_and_reference_logprobs_time
        / training_num_gpus
    )
    training_worker_group_tokens_per_sec_per_gpu = (
        metrics["total_num_tokens"]
        / (policy_training_time + policy_and_reference_logprobs_time)
        / training_num_gpus
    )
    generation_tokens_per_sec_per_gpu = (
        metrics["total_num_tokens"] / generation_time / generation_num_gpus
    )

    print("  • Throughputs (per GPU):")
    print(f"    - E2E (Samples/sec/gpu): {e2e_samples_per_sec_per_gpu:.2f}")
    print(f"    - E2E (Tokens/sec/gpu): {e2e_tokens_per_sec_per_gpu:.2f}")
    print(
        f"    - Policy Training (Tokens/sec/gpu): {policy_training_tokens_per_sec_per_gpu:.2f}"
    )
    print(
        f"    - Policy and Reference Logprobs (Tokens/sec/gpu): {policy_and_reference_logprobs_tokens_per_sec_per_gpu:.2f}"
    )
    print(
        f"    - Training Worker Group (Tokens/sec/gpu): {training_worker_group_tokens_per_sec_per_gpu:.2f}"
    )
    print(
        f"    - Generation Worker Group (Tokens/sec/gpu): {generation_tokens_per_sec_per_gpu:.2f}"
    )

    print("  • Throughputs (per Group):")
    print(
        f"    - E2E (Samples/sec): {(e2e_samples_per_sec_per_gpu * total_num_gpus):.2f}"
    )
    print(
        f"    - E2E (Tokens/sec): {(e2e_tokens_per_sec_per_gpu * total_num_gpus):.2f}"
    )
    print(
        f"    - Training Worker Group (Tokens/sec): {(training_worker_group_tokens_per_sec_per_gpu * training_num_gpus):.2f}"
    )
    print(
        f"    - Generation Worker Group (Tokens/sec): {(generation_tokens_per_sec_per_gpu * generation_num_gpus):.2f}"
    )

    # =====================================================
    # FLOPS
    # =====================================================

    if "total_flops" in train_results:
        total_tflops = (
            train_results["total_flops"] / timing_metrics["policy_training"] / 1e12
        )
        num_ranks = train_results["num_ranks"]
        print(
            f"  • Training FLOPS: {total_tflops:.2f} TFLOPS ({total_tflops / num_ranks:.2f} TFLOPS per rank)",
            flush=True,
        )
        performance_metrics["train_flops_per_gpu"] = total_tflops / num_ranks
        if "theoretical_tflops" in train_results:
            theoretical_tflops = train_results["theoretical_tflops"]
            print(
                f"  • Training Model Floating Point Utilization: {100 * total_tflops / theoretical_tflops:.2f}%",
                flush=True,
            )
            performance_metrics["train_fp_utilization"] = (
                total_tflops / theoretical_tflops
            )

    # =====================================================
    # Clean up metrics
    # =====================================================

    # Clean up metrics to avoid wandb logging errors
    # Dict structures cannot be logged to wandb
    if "per_worker_token_counts" in metrics:
        del metrics["per_worker_token_counts"]

    # =====================================================
    # Logging
    # =====================================================

    performance_metrics.update(
        {
            "samples_per_sec": e2e_samples_per_sec_per_gpu * total_num_gpus,
            "tokens_per_sec": e2e_tokens_per_sec_per_gpu * total_num_gpus,
            "samples_per_sec_per_gpu": e2e_samples_per_sec_per_gpu,
            "tokens_per_sec_per_gpu": e2e_tokens_per_sec_per_gpu,
            "policy_training_tokens_per_sec_per_gpu": policy_training_tokens_per_sec_per_gpu,
            "policy_and_reference_logprobs_tokens_per_sec_per_gpu": policy_and_reference_logprobs_tokens_per_sec_per_gpu,
            "training_worker_group_tokens_per_sec_per_gpu": training_worker_group_tokens_per_sec_per_gpu,
            "generation_tokens_per_sec_per_gpu": generation_tokens_per_sec_per_gpu,
            "training_worker_group_tokens_per_sec": training_worker_group_tokens_per_sec_per_gpu
            * training_num_gpus,
            "generation_tokens_per_sec": generation_tokens_per_sec_per_gpu
            * generation_num_gpus,
        }
    )

    return performance_metrics


def log_generation_metrics_to_wandb(
    generation_logger_metrics: dict[str, dict[int, list[Any]]],
    step: int,
    timeline_interval: float,
    logger: Logger,
) -> None:
    """Log generation metrics to wandb.

    Args:
        generation_logger_metrics: Dictionary of generation logger metrics
        step: Global step value
        timeline_interval: Interval between timeline points (in seconds)
        logger: Logger instance
    """
    for generation_metric in generation_logger_metrics.keys():
        logger.log_plot_per_worker_timeline_metrics(
            generation_logger_metrics[generation_metric],
            step=step,
            prefix="generation_metrics",
            name=generation_metric,
            timeline_interval=timeline_interval,
        )
