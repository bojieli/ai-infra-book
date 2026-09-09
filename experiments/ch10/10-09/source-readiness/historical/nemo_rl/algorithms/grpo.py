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
import gc
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from typing import Any, Callable, NotRequired, Optional, TypedDict, TypeVar, cast

import numpy as np
import ray
import torch
from pydantic import BaseModel
from torchdata.stateful_dataloader import StatefulDataLoader
from transformers import AutoProcessor
from transformers.tokenization_utils_base import PreTrainedTokenizerBase

from nemo_rl.algorithms.advantage_estimator import (
    GDPOAdvantageEstimator,
    GRPOAdvantageEstimator,
    ReinforcePlusPlusAdvantageEstimator,
)
from nemo_rl.algorithms.loss import (
    ClippedPGLossConfig,
    ClippedPGLossDataDict,
    ClippedPGLossFn,
)
from nemo_rl.algorithms.loss.interfaces import LossFunction
from nemo_rl.algorithms.reward_functions import (
    RewardShapingConfig,
    apply_reward_shaping,
)
from nemo_rl.algorithms.utils import (
    calculate_baseline_and_std_per_prompt,
    get_gdpo_reward_component_keys,
    log_generation_metrics_to_wandb,
    print_performance_metrics,
    set_seed,
)
from nemo_rl.data import DataConfig
from nemo_rl.data.collate_fn import rl_collate_fn
from nemo_rl.data.dataloader import MultipleDataloaderWrapper
from nemo_rl.data.datasets import AllTaskProcessedDataset
from nemo_rl.data.interfaces import DatumSpec, LLMMessageLogType, VLMMessageLogType
from nemo_rl.data.llm_message_utils import (
    batched_message_log_to_flat_message,
    get_keys_from_message_log,
)
from nemo_rl.data.utils import extract_necessary_env_names, load_dataloader_state
from nemo_rl.data_plane.interfaces import DataPlaneConfig
from nemo_rl.distributed.batched_data_dict import BatchedDataDict
from nemo_rl.distributed.ray_actor_environment_registry import get_actor_python_env
from nemo_rl.distributed.virtual_cluster import (
    ClusterConfig,
    RayVirtualCluster,
)
from nemo_rl.environments.interfaces import EnvironmentInterface
from nemo_rl.experience.rollouts import (
    run_async_multi_turn_rollout,
    run_async_nemo_gym_rollout,
    run_multi_turn_rollout,
)
from nemo_rl.models.generation.interfaces import GenerationInterface
from nemo_rl.models.generation.sglang import SGLangConfig, SGLangGeneration
from nemo_rl.models.generation.vllm import VllmConfig, VllmGeneration
from nemo_rl.models.megatron.router_replay import configure_vllm_for_router_replay
from nemo_rl.models.policy import PolicyConfig
from nemo_rl.models.policy.interfaces import ColocatablePolicyInterface
from nemo_rl.models.policy.lm_policy import Policy
from nemo_rl.utils.checkpoint import CheckpointingConfig, CheckpointManager
from nemo_rl.utils.logger import (
    Logger,
    LoggerConfig,
    print_message_log_samples,
)
from nemo_rl.utils.memory_tracker import MemoryTracker
from nemo_rl.utils.nsys import maybe_gpu_profile_step
from nemo_rl.utils.timer import TimeoutChecker, Timer
from nemo_rl.utils.venvs import create_local_venv_on_each_node

# ===============================================================================
# Configuration
# ===============================================================================
TokenizerType = TypeVar("TokenizerType", bound=PreTrainedTokenizerBase)


class RewardScalingConfig(TypedDict):
    """Configure linear reward scaling with clamping.

    When `enabled` is True, each reward is clamped to the source interval
    [source_min, source_max] and linearly mapped to the target interval
    [target_min, target_max]. Refer to the scale_rewards function for the implementation.

    Defaults:
        source_min=0.0, source_max=1.0, target_min=0.0, target_max=1.0
    """

    enabled: bool
    source_min: NotRequired[float]
    source_max: NotRequired[float]
    target_min: NotRequired[float]
    target_max: NotRequired[float]


class AsyncGRPOConfig(TypedDict):
    enabled: bool
    # Maximum trajectory age in training steps for samples drawn from the
    # async replay buffer. Trajectories older than this are excluded during
    # sampling; buffer sizing also scales with this value.
    max_trajectory_age_steps: int
    # Does the weight synchronization as soon as the training is done
    # without waiting for the pending generations to finish.
    in_flight_weight_updates: NotRequired[bool]
    # Recomputes the KV cache after the in-flight weight updates.
    recompute_kv_cache_after_weight_updates: NotRequired[bool]


class AdvEstimatorConfig(TypedDict):
    """Configuration for advantage estimator (GRPO, GDPO, or Reinforce++)."""

    name: str  # "grpo", "gdpo", or "reinforce_plus_plus"
    # GRPO specific
    normalize_rewards: NotRequired[bool]
    use_leave_one_out_baseline: NotRequired[bool]
    # Reinforce++ specific
    minus_baseline: NotRequired[bool]


class GRPOConfig(TypedDict):
    num_prompts_per_step: int
    num_generations_per_prompt: int
    max_num_epochs: int
    max_num_steps: int
    max_rollout_turns: int
    normalize_rewards: bool
    # Clipping bounds for normalized advantages to prevent extreme values
    # When set, advantages are clipped to [advantage_clip_low, advantage_clip_high] after normalization
    # Default: null (no clipping)
    advantage_clip_low: NotRequired[float | None]
    advantage_clip_high: NotRequired[float | None]
    use_leave_one_out_baseline: bool
    val_period: int
    val_batch_size: int | None  # None for NeMo-Gym compatibility
    val_at_start: bool
    # Whether to run validation on the last training step. Setting this to True ensures the
    # final checkpoint has validation metrics, which is required for get_best_checkpoint_path().
    val_at_end: bool
    max_val_samples: int | None  # None for NeMo-Gym compatibility
    skip_reference_policy_logprobs_calculation: NotRequired[bool]
    seed: int
    async_grpo: NotRequired[AsyncGRPOConfig]
    overlong_filtering: NotRequired[bool]
    # whether to enable dynamic sampling, i.e.
    # whether to discard prompts whose rewards have zero standard deviation
    use_dynamic_sampling: bool
    # When using dynamic sampling, the maximum number of batches to generate
    # before throwing an error
    dynamic_sampling_max_gen_batches: NotRequired[int]
    # When using dynamic sampling, generation prompt batch size will equal
    # num_prompts_per_step * batch_multiplier
    batch_multiplier: NotRequired[float]
    reward_shaping: RewardShapingConfig
    reward_scaling: RewardScalingConfig
    # By default advantages are calculated on CPU. Setting this flag to true leverages GPU for their computation.
    calculate_advantages_on_gpu: NotRequired[bool]
    # Sequence-level logprob error masking for training stability. If set, mask sequences with mult_prob_error exceeding this threshold (same scale as token_mult_prob_error metric, e.g., 1.5)
    # Note that this is slightly different than Masked Importance Sampling (MIS) because this uses the absolute value of the difference between the training and generation logprobs, whereas MIS just uses the difference between the training and generation logprobs.
    seq_logprob_error_threshold: float | None
    # Advantage value to assign to invalid tool call tokens. When set (e.g. -5.0), overwrites the
    # computed advantage for those tokens to penalize them; absent/None disables the penalty.
    invalid_tool_call_advantage: NotRequired[float | None]
    # Advantage value to assign to tokens with malformed <think>/</think> tags. When set (e.g. -5.0),
    # overwrites the computed advantage for those tokens; absent/None disables the penalty.
    malformed_thinking_advantage: NotRequired[float | None]
    # Advantage estimator configuration (grpo or reinforce_plus_plus)
    adv_estimator: NotRequired[AdvEstimatorConfig]


class GRPOSaveState(TypedDict):
    consumed_samples: int
    current_step: int
    current_epoch: int
    total_steps: int
    total_valid_tokens: int  # Track total number of non-padding tokens during training
    val_reward: NotRequired[
        float
    ]  # Optional field - may not be present during training


def _default_grpo_save_state() -> GRPOSaveState:
    return {
        "consumed_samples": 0,
        "current_step": 0,
        "current_epoch": 0,
        "total_steps": 0,
        "total_valid_tokens": 0,
        "val_reward": -99999999.0,
    }


class GRPOLoggerConfig(LoggerConfig):
    num_val_samples_to_print: int  # number of val samples to print to stdout


class MasterConfig(BaseModel, extra="allow"):
    policy: PolicyConfig
    loss_fn: ClippedPGLossConfig
    env: dict[str, Any]
    data: DataConfig
    grpo: GRPOConfig
    logger: GRPOLoggerConfig
    cluster: ClusterConfig
    checkpointing: CheckpointingConfig
    data_plane: Optional[DataPlaneConfig] = None


# ===============================================================================
# Setup & Initialization
# ===============================================================================


def setup(
    master_config: MasterConfig,
    tokenizer: TokenizerType,
    dataset: AllTaskProcessedDataset | dict[str, AllTaskProcessedDataset],
    val_dataset: Optional[AllTaskProcessedDataset],
    processor: Optional[AutoProcessor] = None,
    policy_factory: Optional[Callable[..., ColocatablePolicyInterface]] = None,
) -> tuple[
    ColocatablePolicyInterface,
    Optional[GenerationInterface],
    tuple[RayVirtualCluster, RayVirtualCluster],
    StatefulDataLoader | MultipleDataloaderWrapper,
    Optional[StatefulDataLoader],
    ClippedPGLossFn,
    Logger,
    CheckpointManager,
    GRPOSaveState,
    MasterConfig,
]:
    """Main entry point for running GRPO algorithm.

    Returns:
        tuple of policy, cluster, dataloader, tokenizer, loss_fn, math_env, logger, master_config, val_dataloader
    """
    # Start timing the entire setup process
    setup_start_time = time.perf_counter()

    # Extract individual configs for easier access
    policy_config = master_config.policy
    generation_config = policy_config["generation"]
    loss_config: ClippedPGLossConfig = master_config.loss_fn
    env_configs = master_config.env
    data_config = master_config.data
    grpo_config = master_config.grpo
    logger_config = master_config.logger
    cluster_config = master_config.cluster
    checkpointing_config = master_config.checkpointing

    checkpointing_pretrained = checkpointing_config.get("pretrained_checkpoint")
    if checkpointing_pretrained is not None:
        policy_config["pretrained_checkpoint"] = checkpointing_pretrained

    assert generation_config is not None, (
        "A generation config in the PolicyConfig is required for GRPO"
    )

    # Set seed for all random number generators
    set_seed(grpo_config["seed"])

    # ==========================
    #         Logger
    # ==========================
    logger = Logger(logger_config)
    logger.log_hyperparams(master_config.model_dump())

    # ==========================
    #      Checkpointing
    # ==========================
    checkpointer = CheckpointManager(checkpointing_config)
    last_checkpoint_path = checkpointer.get_latest_checkpoint_path()
    grpo_save_state: Optional[GRPOSaveState] = cast(
        Optional[GRPOSaveState], checkpointer.load_training_info(last_checkpoint_path)
    )
    if grpo_save_state is None:
        grpo_save_state = _default_grpo_save_state()

    # ==========================
    #           Data
    # ==========================
    # num_prompts_per_step and dataloader_batch_size will be different when using multiple dataloaders
    num_prompts_per_step = grpo_config["num_prompts_per_step"]
    if data_config["use_multiple_dataloader"]:
        dataloader_batch_size = data_config["num_prompts_per_dataloader"]
    else:
        dataloader_batch_size = num_prompts_per_step

    # Validate batch_multiplier
    batch_multiplier = grpo_config["batch_multiplier"]
    if grpo_config["use_dynamic_sampling"]:
        num_prompts_per_step = int(num_prompts_per_step * batch_multiplier)
        dataloader_batch_size = int(dataloader_batch_size * batch_multiplier)
    else:
        assert batch_multiplier == 1, (
            "batch_multiplier>1 can only be used if use_dynamic_sampling=True"
        )

    # Validate number of prompts per step
    if data_config["use_multiple_dataloader"]:
        assert num_prompts_per_step % dataloader_batch_size == 0, (
            "Expected num_prompts_per_step to be a multiple of num_prompts_per_dataloader, "
            f"but got {num_prompts_per_step} and {dataloader_batch_size}. "
            "Please check the configuration of num_prompts_per_step and num_prompts_per_dataloader. "
            "If use_dynamic_sampling is enabled and batch_multiplier is used, please also check the configuration of batch_multiplier."
        )

    # Load train dataset
    def init_train_dataloader(dataset, suffix: str = ""):
        dataloader = StatefulDataLoader(
            dataset,
            batch_size=dataloader_batch_size,
            shuffle=data_config["shuffle"],
            collate_fn=rl_collate_fn,
            drop_last=True,
            num_workers=data_config["num_workers"],
        )
        if last_checkpoint_path is not None:
            load_dataloader_state(dataloader, last_checkpoint_path, data_config, suffix)
        return dataloader

    if data_config["use_multiple_dataloader"]:
        # Initialize dataloaders
        dataloaders = {}
        for task_name, task_dataset in dataset.items():
            dataloaders[task_name] = init_train_dataloader(
                task_dataset, f"_{task_name}"
            )
            print(
                f"  ✓ Training dataloader {task_name} loaded with {len(task_dataset)} samples",
                flush=True,
            )

        train_sample_count = sum(
            len(task_dataloader) for task_dataloader in dataloaders.values()
        )

        # Wrap dataloader
        dataloader = MultipleDataloaderWrapper(
            expected_num_prompts=num_prompts_per_step,
            data_config=data_config,
            dataloaders=dataloaders,
        )
    else:
        dataloader = init_train_dataloader(dataset)
        train_sample_count = len(dataloader)
        print(
            f"  ✓ Training dataloader loaded with {train_sample_count} samples",
            flush=True,
        )

    # Load validation dataset if provided
    val_dataloader: Optional[StatefulDataLoader] = None
    # If validation is enabled, load the validation dataloader
    if (
        grpo_config["val_period"] > 0
        or grpo_config["val_at_start"]
        or grpo_config["val_at_end"]
    ):
        assert val_dataset is not None, (
            "Validation dataset is required if validation is enabled"
        )
        val_dataloader = StatefulDataLoader(
            val_dataset,
            batch_size=grpo_config["val_batch_size"],
            shuffle=False,
            collate_fn=rl_collate_fn,
            num_workers=data_config["num_workers"],
        )
        print(
            f"  ✓ Validation dataloader loaded with {len(val_dataset)} samples",
            flush=True,
        )

    # ==========================
    #        Loss Function
    # ==========================
    loss_fn = ClippedPGLossFn(loss_config)

    # Validate force_on_policy_ratio
    if loss_config.force_on_policy_ratio:
        assert (
            grpo_config["num_prompts_per_step"]
            * grpo_config["num_generations_per_prompt"]
            == policy_config["train_global_batch_size"]
        ), (
            "force_on_policy_ratio requires train_global_batch_size == num_prompts_per_step * num_generations_per_prompt"
        )
        os.environ["NRL_IGNORE_TP_ACCURACY_CHECK"] = "1"
        print("  ✓ force_on_policy_ratio enabled")

    # Validate skip_reference_policy_logprobs_calculation
    if grpo_config.get("skip_reference_policy_logprobs_calculation"):
        assert loss_config.reference_policy_kl_penalty == 0, (
            "grpo.skip_reference_policy_logprobs_calculation=True requires "
            "loss_fn.reference_policy_kl_penalty == 0"
        )
        print(
            "Reference policy logprob calculation will be skipped since `grpo.skip_reference_policy_logprobs_calculation` is set to True and `loss_fn.reference_policy_kl_penalty` is 0."
        )

    # ==========================
    #          Cluster
    # ==========================
    print("\n▶ Setting up compute cluster...", flush=True)
    colocated_inference = generation_config["colocated"]["enabled"]

    env_name_list = extract_necessary_env_names(data_config)
    rm_env_enabled = "reward_model" in env_name_list

    total_nodes = cluster_config["num_nodes"]
    if rm_env_enabled:
        rm_resource = env_configs["reward_model"]["resources"]
        rm_nodes = rm_resource["num_nodes"]
        rm_gpus_per_node = rm_resource["gpus_per_node"]
    else:
        rm_nodes = 0
        rm_gpus_per_node = 0

    if total_nodes == 1:
        policy_nodes = total_nodes
    else:
        policy_nodes = total_nodes - rm_nodes
        assert policy_nodes > 0, (
            "policy_nodes must be > 0, but got "
            f"policy_nodes:{policy_nodes} + rm_nodes:{rm_nodes} = total_nodes:{total_nodes}"
        )

    if colocated_inference:
        if total_nodes == 1:
            policy_gpus_per_node = cluster_config["gpus_per_node"] - rm_gpus_per_node
            assert policy_gpus_per_node > 0, (
                "policy.generation.colocated.resources.gpus_per_node must be > 0 "
                "when cluster.num_nodes = 1, "
                f"but got {policy_gpus_per_node}."
            )
        else:
            policy_gpus_per_node = cluster_config["gpus_per_node"]

        cluster = RayVirtualCluster(
            name="grpo_policy_cluster",
            bundle_ct_per_node_list=[policy_gpus_per_node] * policy_nodes,
            use_gpus=True,
            num_gpus_per_node=policy_gpus_per_node,
            max_colocated_worker_groups=1
            if generation_config["backend"] == "megatron"
            else 2,
            port_range_low=cluster_config.get("master_port_range_low"),
            port_range_high=cluster_config.get("master_port_range_high"),
        )
        train_cluster = cluster
        inference_cluster = cluster
        print(
            f"  ✓ Ray cluster for policy initialized with {policy_nodes} nodes",
            flush=True,
        )

    else:
        assert generation_config["backend"] != "megatron", (
            "Non-colocated inference is not supported for Megatron generation backends. "
            "Please use vLLM backend for generation."
        )

        # train resources will be updated through overall and inference resources below
        train_gpus_per_node = cluster_config["gpus_per_node"]
        train_nodes = policy_nodes

        inference_resources = generation_config["colocated"]["resources"]
        inference_gpus_per_node = inference_resources["gpus_per_node"]
        inference_nodes = inference_resources["num_nodes"]

        # validate and configure resources
        if policy_nodes == 1:
            # When policy_nodes == 1, train and inference are on the same node
            assert (
                inference_gpus_per_node is not None and inference_gpus_per_node > 0
            ), (
                "policy.generation.colocated.resources.gpus_per_node must be explicitly set to a value > 0 "
                "when policy_nodes = 1 and inference is non-colocated, "
                f"but got {inference_gpus_per_node}."
            )
            assert inference_nodes is None or inference_nodes == 1, (
                "policy.generation.colocated.resources.num_nodes must be 1 or set to null "
                "when policy_nodes = 1 and inference is non-colocated, "
                f"but got {inference_nodes}."
            )

            inference_nodes = 1
            # If total_nodes == 1, reward model is also on the same node; otherwise it's on a different node
            reward_gpus_to_subtract = (
                rm_gpus_per_node if total_nodes == 1 and rm_env_enabled else 0
            )
            train_gpus_per_node -= inference_gpus_per_node + reward_gpus_to_subtract
            assert train_gpus_per_node > 0, (
                "No enough GPUs for training, "
                f"train_gpus_per_node:{train_gpus_per_node} = cluster_config['gpus_per_node']:{cluster_config['gpus_per_node']} - inference_gpus_per_node:{inference_gpus_per_node}"
                + (
                    f" - rm_gpus_per_node:{rm_gpus_per_node}"
                    if total_nodes == 1 and rm_env_enabled
                    else ""
                )
            )
        else:
            # train, inference, and reward model are all on different nodes
            assert inference_nodes > 0, (
                "policy.generation.colocated.resources.num_nodes must be > 0 "
                "when cluster.num_nodes > 1 and inference is non-colocated, "
                f"but got {inference_nodes}."
            )
            assert (
                inference_gpus_per_node is not None
                and inference_gpus_per_node == cluster_config["gpus_per_node"]
            ), (
                "policy.generation.colocated.resources.gpus_per_node must be explicitly set and equal to cluster.gpus_per_node "
                "when cluster.num_nodes > 1 and inference is non-colocated, "
                f"but got inference_gpus_per_node={inference_gpus_per_node}, cluster.gpus_per_node={cluster_config['gpus_per_node']}."
            )
            train_nodes -= inference_nodes

        # initialize train cluster
        train_cluster = RayVirtualCluster(
            name="grpo_train_cluster",
            bundle_ct_per_node_list=[train_gpus_per_node] * train_nodes,
            use_gpus=True,
            num_gpus_per_node=train_gpus_per_node,
            max_colocated_worker_groups=1,
            port_range_low=cluster_config.get("master_port_range_low"),
            port_range_high=cluster_config.get("master_port_range_high"),
        )
        print(
            f"  ✓ Ray train cluster initialized with {train_nodes} nodes with {train_gpus_per_node} GPUs per node",
            flush=True,
        )

        # initialize inference cluster
        inference_cluster = RayVirtualCluster(
            name="grpo_inference_cluster",
            bundle_ct_per_node_list=[inference_gpus_per_node] * inference_nodes,
            use_gpus=True,
            num_gpus_per_node=inference_gpus_per_node,
            max_colocated_worker_groups=1,
            port_range_low=cluster_config.get("master_port_range_low"),
            port_range_high=cluster_config.get("master_port_range_high"),
        )
        print(
            f"  ✓ Ray inference cluster initialized with {inference_nodes} nodes with {inference_gpus_per_node} GPUs per node",
            flush=True,
        )

    # ==========================
    #   Training and Inference
    # ==========================
    print("\n▶ Setting up model and training...", flush=True)

    # vllm model loading prefers clean environment, initialize policy_generation before policy in colocated mode
    backend = generation_config["backend"]
    generation_config["model_name"] = policy_config["model_name"]  # Needed for vLLM

    # Dictionary to store worker initialization timing stats for logging
    worker_init_timing_metrics = {}

    weights_path, optimizer_path = checkpointer.get_resume_paths(last_checkpoint_path)

    if policy_config.get("megatron_cfg", {}).get("enabled", False):
        ## NOTE: this is equal to the total number of scheduler steps
        total_train_iters = min(
            grpo_config["max_num_steps"],
            grpo_config["max_num_epochs"] * train_sample_count,
        )
        policy_config["megatron_cfg"]["train_iters"] = total_train_iters

    # Define initialization functions that will be used in all paths
    init_reference_model = loss_config.reference_policy_kl_penalty > 0

    # Auto-enable skip_reference_policy_logprobs_calculation when the reference model is not loaded.
    if not init_reference_model and not grpo_config.get(
        "skip_reference_policy_logprobs_calculation"
    ):
        grpo_config["skip_reference_policy_logprobs_calculation"] = True
        print(
            "Auto-enabling `grpo.skip_reference_policy_logprobs_calculation=True` "
            "because `loss_fn.reference_policy_kl_penalty == 0` "
            "(reference model is not loaded)."
        )

    # Caller-supplied factory lets the sync trainer swap in a TQ-mediated
    # Policy subclass without this shared setup needing to know the data
    # plane exists. Default is the plain Policy class — legacy behavior.
    _make_policy = policy_factory if policy_factory is not None else Policy

    def init_policy():
        """Initialize policy training workers."""
        t0 = time.perf_counter()
        p = _make_policy(
            cluster=train_cluster,
            config=policy_config,
            tokenizer=tokenizer,
            processor=processor,
            weights_path=weights_path,
            optimizer_path=optimizer_path,
            init_optimizer=True,
            init_reference_model=init_reference_model,
        )
        return p, time.perf_counter() - t0

    def init_vllm():
        """Initialize vLLM generation workers."""
        t0 = time.perf_counter()
        pg = VllmGeneration(cluster=inference_cluster, config=generation_config)
        pg.finish_generation()
        return pg, time.perf_counter() - t0

    def init_sglang():
        """Initialize SGLang generation workers."""
        t0 = time.perf_counter()
        pg = SGLangGeneration(cluster=inference_cluster, config=generation_config)
        pg.finish_generation()
        return pg, time.perf_counter() - t0

    def initialize_generation_with_policy(
        init_generation_fn,
        generation_name: str,
        init_time_key: str,
        colocated_inference: bool,
        worker_init_timing_metrics: dict,
    ):
        """Generic function to initialize a generation engine (vLLM or SGLang) along with policy.

        Args:
            init_generation_fn: Function that initializes the generation engine (init_vllm or init_sglang)
            generation_name: Name of the generation engine ("vLLM" or "SGLang")
            init_time_key: Key name for storing initialization time in metrics ("vllm_init_time_s" or "sglang_init_time_s")
            colocated_inference: Whether inference is colocated with training
            worker_init_timing_metrics: Dictionary to store timing metrics

        Returns:
            Tuple of (policy_generation, policy)
        """
        # Determine if parallel initialization is possible (non-colocated mode)
        use_parallel_init = not colocated_inference

        if use_parallel_init:
            # Parallel initialization: Generation engine and Policy can initialize simultaneously
            print(
                "  ⚡ Using parallel worker initialization (non-colocated mode)",
                flush=True,
            )

            # Execute both initializations in parallel
            parallel_start_time = time.perf_counter()
            with ThreadPoolExecutor(max_workers=2) as executor:
                generation_future = executor.submit(init_generation_fn)
                policy_future = executor.submit(init_policy)
                policy_generation, generation_time = generation_future.result()
                policy, policy_time = policy_future.result()
            parallel_wall_time = time.perf_counter() - parallel_start_time

            # Store timing metrics
            worker_init_timing_metrics[init_time_key] = generation_time
            worker_init_timing_metrics["policy_init_time_s"] = policy_time
            worker_init_timing_metrics["parallel_wall_time_s"] = parallel_wall_time
            worker_init_timing_metrics["parallel_init_enabled"] = True

        else:
            # Sequential initialization: colocated mode (GPU memory requires generation engine first)
            print(
                "  ⚙️  Using sequential worker initialization (colocated mode)",
                flush=True,
            )

            # Initialize generation engine first (clean GPU memory), then policy
            policy_generation, generation_time = init_generation_fn()
            worker_init_timing_metrics[init_time_key] = generation_time

            policy, policy_time = init_policy()
            worker_init_timing_metrics["policy_init_time_s"] = policy_time
            worker_init_timing_metrics["parallel_init_enabled"] = 0.0

        return policy_generation, policy

    # Handle generation-specific setup
    if backend == "megatron":
        # Megatron generation: policy_generation is None, only initialize policy
        policy_generation = None
        print(
            f"  ✓ Using {backend} backend for generation with {policy_config['model_name']}",
            flush=True,
        )

        policy, policy_time = init_policy()
        worker_init_timing_metrics["policy_init_time_s"] = policy_time

    elif backend == "vllm":
        # vLLM generation: setup config, then initialize with policy
        generation_config = cast(VllmConfig, generation_config)
        if generation_config["vllm_cfg"]["precision"] == "fp8":
            assert loss_config.use_importance_sampling_correction, (
                "Importance sampling must be enabled for vLLM FP8 generation for good convergence!"
            )
        if generation_config["vllm_cfg"]["kv_cache_dtype"].startswith("fp8"):
            # FP8 KV cache requires FP8 model precision
            assert generation_config["vllm_cfg"]["precision"] == "fp8", (
                f"kv_cache_dtype='{generation_config['vllm_cfg']['kv_cache_dtype']}' requires precision='fp8'. "
                "FP8 KV cache can only be used together with FP8 model weights."
            )
            # FP8 KV cache compatibility checks
            assert policy_config["dtensor_cfg"]["enabled"] == False, (
                "DTensor backend is not supported with kv cache fp8 enabled."
            )
            assert not _should_use_async_rollouts(master_config), (
                "Async rollouts is not supported with kv cache fp8 enabled."
            )
            assert policy_config["megatron_cfg"]["pipeline_model_parallel_size"] == 1, (
                "Currently when using FP8 KV cache in generation, then in megatron we only support pipeline_model_parallel_size=1. We will add more support in future."
            )

        configure_vllm_for_router_replay(policy_config)
        vllm_kwargs = generation_config.setdefault("vllm_kwargs", {})

        ## make vllm hf overrides match the training policy
        vllm_kwargs["hf_overrides"] = policy_config.get("hf_config_overrides", {})

        policy_generation, policy = initialize_generation_with_policy(
            init_generation_fn=init_vllm,
            generation_name="vLLM",
            init_time_key="vllm_init_time_s",
            colocated_inference=colocated_inference,
            worker_init_timing_metrics=worker_init_timing_metrics,
        )

        print(
            f"  ✓ Using vLLM backend for generation with {policy_config['model_name']}",
            flush=True,
        )

    elif backend == "sglang":
        generation_config = cast(SGLangConfig, generation_config)

        # Set model_path if not already set
        if "model_path" not in generation_config["sglang_cfg"]:
            generation_config["sglang_cfg"]["model_path"] = policy_config["model_name"]

        policy_generation, policy = initialize_generation_with_policy(
            init_generation_fn=init_sglang,
            generation_name="SGLang",
            init_time_key="sglang_init_time_s",
            colocated_inference=colocated_inference,
            worker_init_timing_metrics=worker_init_timing_metrics,
        )

        print(
            f"  ✓ Using SGLang backend for generation with {policy_config['model_name']}",
            flush=True,
        )

    # Record when worker initialization completes (for calculating other setup time)
    worker_init_complete_time = time.perf_counter() - setup_start_time

    # print the node IP and GPU ID of the policy workers for debugging
    policy.print_node_ip_and_gpu_id()

    # if it is not colocated inference, initialize collective communication for update weights
    if not colocated_inference:
        t0 = time.perf_counter()
        ip, port = train_cluster.get_master_address_and_port()
        print(f"Using ip: {ip}, port: {port} for collective communication", flush=True)
        # world includes all training workers and all inference workers
        train_world_size = train_cluster.world_size()
        inference_world_size = inference_nodes * inference_gpus_per_node
        world_size = train_world_size + inference_world_size
        # init collective
        futures_train = policy.init_collective(
            ip, port, world_size, train_world_size=train_world_size
        )
        futures_inference = policy_generation.init_collective(
            ip, port, world_size, train_world_size=train_world_size
        )  # type: ignore
        # wait for all futures to complete
        ray.get(futures_train + futures_inference)
        worker_init_timing_metrics["collective_init_time_s"] = time.perf_counter() - t0

    # prepare refit info
    state_dict_info = policy.prepare_refit_info()
    if policy_generation is not None:
        policy_generation.prepare_refit_info(state_dict_info)

    # Calculate total setup time
    total_setup_time = time.perf_counter() - setup_start_time
    worker_init_timing_metrics["total_setup_time_s"] = total_setup_time

    # Log worker initialization timing metrics to logger
    if worker_init_timing_metrics:
        print("\n▶ Worker Initialization Timing:")

        vllm_time = worker_init_timing_metrics.get("vllm_init_time_s", 0)
        policy_time = worker_init_timing_metrics.get("policy_init_time_s", 0)
        total_setup = worker_init_timing_metrics.get("total_setup_time_s", 0)

        if vllm_time:
            print(f"  vLLM init: {vllm_time:.1f}s")

        if policy_time:
            print(f"  Policy init: {policy_time:.1f}s")

        # Calculate "other" time (time after worker init completes)
        other_time = total_setup - worker_init_complete_time
        worker_init_timing_metrics["other_setup_time_s"] = other_time
        print(f"  Other setup: {other_time:.1f}s")

        print(f"  Total setup: {total_setup:.1f}s")

        # Log all metrics to the logger for analysis
        logger.log_metrics(worker_init_timing_metrics, step=0, prefix="timing/setup")

    print("\n" + "=" * 60)
    print(" " * 18 + "SETUP COMPLETE")
    print(f"  Total setup time: {total_setup_time:.1f}s")
    print("=" * 60 + "\n", flush=True)

    return (
        policy,
        policy_generation,
        (train_cluster, inference_cluster),
        dataloader,
        val_dataloader,
        loss_fn,
        logger,
        checkpointer,
        grpo_save_state,
        master_config,
    )


# ===============================================================================
# Core Algorithm Functions
# ===============================================================================


def dynamic_sampling(
    repeated_batch: BatchedDataDict[DatumSpec],
    std: torch.Tensor,
    baseline: torch.Tensor,
    dynamic_sampling_num_gen_batches: int,
    master_config: MasterConfig,
    timer: Timer,
    batch_cache: BatchedDataDict[DatumSpec] = None,
) -> BatchedDataDict[DatumSpec]:
    """Implements the dynamic sampling algorithm to select prompts with non-zero standard deviation.

    This function filters the current batch to retain only those prompts that have a non-zero standard deviation.
    If the current batch has fewer number of prompts with non-zero standard deviation than the required batch size, defined as num_prompts_per_step * num_generations_per_prompt,
    we store it in the batch_cache to be used in later iterations.
    If the current batch has more number of prompts with non-zero standard deviation than the required batch size, defined as num_prompts_per_step * num_generations_per_prompt,
    the batch is sliced to ensure batch size is num_prompts_per_step * num_generations_per_prompt.
    is_batch_complete is set to False to indicate that the current batch is not enough to meet the required batch size. This is used as a signal in the GRPO training loop
    to continue sampling or proceed to training.
    This approach is based on the dynamic sampling algorithm from the DAPO paper:
    https://arxiv.org/pdf/2503.14476.

    Args:
        repeated_batch (BatchedDataDict[DatumSpec]): The current batch of data containing prompts, responses, rewards, baselines, and std.
        std (torch.Tensor): Tensor representing the standard deviation for each prompt group.
        baseline (torch.Tensor): Baseline values for each prompt group.
        dynamic_sampling_num_gen_batches (int): Number of generation batches processed at the current step.
        master_config (MasterConfig): Configuration containing GRPO and policy settings.
        batch_cache (BatchedDataDict[DatumSpec], optional): Cache storing previously selected prompts with non-zero std.

    Returns:
        tuple: A tuple containing:
            - repeated_batch (BatchedDataDict[DatumSpec]): Updated batch with selected prompts.
            - is_batch_complete (bool): Indicates if the batch has enough samples with non-zero std for training.
            - batch_cache (BatchedDataDict[DatumSpec]): Updated cache for future iterations.
    """
    # is_batch_complete is used to indicate if the current batch was able to generate enough prompts with non-zero std.
    is_batch_complete = True

    # Required batch size for training
    train_prompts_size = (
        master_config.grpo["num_prompts_per_step"]
        * master_config.grpo["num_generations_per_prompt"]
    )
    # Store the baseline, std and total_reward for the current unfiltered batch.
    repeated_batch["baseline"] = baseline
    repeated_batch["std"] = std
    total_rewards = repeated_batch["total_reward"]
    dynamic_sampling_metrics = {}

    # Dynamic sampling algorithm (used in DAPO algorithm)
    # This block implements dynamic sampling by selecting prompt groups with non-zero std.
    # If sampled prompts (with non-zero std) are fewer than num_prompts_per_step * num_generations_per_prompt, continue sampling until dynamic_sampling_max_gen_batches is reached.
    if master_config.grpo["use_dynamic_sampling"]:
        with timer.time("dynamic_sampling"):
            # Get the prompt indices with non-zero std
            non_zero_std_mask = std != 0.0

            keep_prompt_indices = torch.arange(
                len(non_zero_std_mask), device=std.device
            )[non_zero_std_mask].tolist()

            # Only select the inputs that have non-zero std
            # total_reward is already a part of repeated_batch so we don't need to add it again
            filtered_repeated_batch = repeated_batch.select_indices(keep_prompt_indices)
            filtered_repeated_batch["std"] = std[keep_prompt_indices]
            filtered_repeated_batch["baseline"] = baseline[keep_prompt_indices]

            # Store filtered and total rewards to track them separately
            filtered_rewards = filtered_repeated_batch["total_reward"]
            filtered_repeated_batch["total_reward"] = total_rewards
            filtered_repeated_batch["filtered_reward"] = filtered_rewards

            # Store the total_reward for the current filtered batch.
            # If none of the prompts in current batch have non-zero std, filtered_repeated_batch.size will be 0.
            # In this case, the current batch will be ignored and the next batch will be processed and we generate responses for it.
            if filtered_repeated_batch.size > 0:
                # Concatenate the previous partially filled batch with the current batch. This serves as a cache to store and collect the prompts with non-zero std.
                # This is used in the next iteration when the current batch is not enough to fill the buffer.
                batch_cache = (
                    filtered_repeated_batch
                    if batch_cache is None
                    else BatchedDataDict.from_batches(
                        [batch_cache, filtered_repeated_batch]
                    )
                )
                filtered_repeated_batch = batch_cache

            filtered_prompts_size = filtered_repeated_batch.size
            print(
                f"Detected {filtered_prompts_size} prompts with non-zero std; "
                f"{train_prompts_size} are required and used for training."
            )

            # If the generation samples size is smaller than a fixed threshold (train_prompts_size), keep generating by processing the next batch
            if filtered_prompts_size < train_prompts_size:
                dynamic_sampling_max_gen_batches = master_config.grpo[
                    "dynamic_sampling_max_gen_batches"
                ]
                assert dynamic_sampling_max_gen_batches > 0, (
                    "When using grpo.use_dynamic_sampling, grpo.dynamic_sampling_max_gen_batches must be > 0"
                )
                if dynamic_sampling_num_gen_batches <= dynamic_sampling_max_gen_batches:
                    print(
                        f"Generation sample buffer size: {filtered_prompts_size} is smaller than train_prompts_size: {train_prompts_size}. Processed {dynamic_sampling_num_gen_batches} batches so far out of {dynamic_sampling_max_gen_batches}."
                    )
                    is_batch_complete = False
                else:
                    raise ValueError(
                        f"Dynamic sampling has reached the maximum allowed number of batches ({dynamic_sampling_max_gen_batches}). Consider evaluating the complexity of your data or adjusting the num_prompts_per_step or num_generations_per_prompt parameters to enhance the diversity of the samples."
                    )
            else:
                num_discarded_valid_samples = filtered_prompts_size - train_prompts_size
                dynamic_sampling_metrics[
                    "dynamic_sampling_num_discarded_valid_samples"
                ] = num_discarded_valid_samples

                #  Slice the batch, rewards, baselines and std to ensure batch size is train_prompts_size
                filtered_repeated_batch = filtered_repeated_batch.slice(
                    0, train_prompts_size
                )

    batch_to_return = (
        filtered_repeated_batch
        if master_config.grpo["use_dynamic_sampling"]
        else repeated_batch
    )
    return batch_to_return, is_batch_complete, batch_cache, dynamic_sampling_metrics


def scale_rewards(
    repeated_batch: BatchedDataDict[DatumSpec], reward_scaling_cfg: RewardScalingConfig
) -> BatchedDataDict[DatumSpec]:
    """Linearly scales rewards from a source range to a target range.

    If `reward_scaling.enabled` is True, each reward in `repeated_batch["total_reward"]`
    is clamped to the configured source interval [source_min, source_max] and then
    rescaled to the target interval [target_min, target_max].

    Default configuration:
        source_min = 0.0
        source_max = 1.0
        target_min = 0.0
        target_max = 1.0
    """
    if reward_scaling_cfg["enabled"]:
        rewards = repeated_batch["total_reward"]
        source_min = float(reward_scaling_cfg["source_min"])
        source_max = float(reward_scaling_cfg["source_max"])
        target_min = float(reward_scaling_cfg["target_min"])
        target_max = float(reward_scaling_cfg["target_max"])

        # Detect out-of-range values
        out_of_range_mask = (rewards < source_min) | (rewards > source_max)
        if torch.any(out_of_range_mask):
            print(
                f"[reward_scaling] WARNING: {int(out_of_range_mask.sum())} rewards "
                f"are outside the configured source range [{source_min}, {source_max}]. "
                f"Values will be clipped before scaling."
            )

        # Clamp and scale
        def _scale(reward_tensor: torch.Tensor) -> torch.Tensor:
            r = torch.clamp(reward_tensor, min=source_min, max=source_max)
            return target_min + (r - source_min) / (source_max - source_min) * (
                target_max - target_min
            )

        scaled_rewards = _scale(rewards)
        repeated_batch["total_reward"] = scaled_rewards
        for key in get_gdpo_reward_component_keys(repeated_batch):
            repeated_batch[key] = _scale(repeated_batch[key])

    return repeated_batch


def extract_initial_prompt_messages(
    message_logs: list,
    original_prompt_lengths: torch.Tensor,
) -> list:
    """Extract the original prompt messages from message logs using token length.

    This function correctly identifies original prompt messages even when the prompt
    contains assistant messages (e.g., multi-turn conversation history).

    Args:
        message_logs: List of message logs, where each log is a list of messages.
        original_prompt_lengths: Tensor of original prompt token lengths per sample.

    Returns:
        List of message logs containing only the original prompt messages.
    """
    initial_prompt_message_logs = []
    for i, message_log in enumerate(message_logs):
        initial_prompt_log = []
        cumulative_length = 0
        target_length = original_prompt_lengths[i].item()

        for message in message_log:
            if cumulative_length >= target_length:
                break
            initial_prompt_log.append(message)
            cumulative_length += len(message["token_ids"])

        initial_prompt_message_logs.append(initial_prompt_log)

    return initial_prompt_message_logs


def add_grpo_token_loss_masks_and_generation_logprobs(
    message_logs: list[LLMMessageLogType | VLMMessageLogType],
) -> None:
    """Add GRPO loss masks and ensure generation logprobs exist in message logs.

    Assistant messages can be part of the original multi-turn prompt history. Only
    generated assistant messages have generation_logprobs, so use that field as the
    trainable-token marker. This function mutates each message in-place by adding a
    token_loss_mask and, when missing, a zero-valued generation_logprobs tensor.

    Args:
        message_logs: Batch of tokenized message logs. Each message must contain a
            ``role`` and ``token_ids`` field. Messages that already contain
            ``generation_logprobs`` are treated as rollout-generated messages.
    """
    for message_log in message_logs:
        for message in message_log:
            role = cast(str, message["role"])
            token_ids = cast(torch.Tensor, message["token_ids"])

            if role == "assistant" and "generation_logprobs" in message:
                message["token_loss_mask"] = torch.ones_like(token_ids)
            else:
                message["token_loss_mask"] = torch.zeros_like(token_ids)

            if "generation_logprobs" not in message:
                message["generation_logprobs"] = torch.zeros_like(
                    token_ids, dtype=torch.float32
                )


def _resolve_message_level_advantage_penalties(
    master_config: MasterConfig,
) -> tuple[float | None, float | None]:
    """Return configured message-level penalties and validate feature support."""
    invalid_tool_call_advantage = master_config.grpo.get("invalid_tool_call_advantage")
    malformed_thinking_advantage = master_config.grpo.get(
        "malformed_thinking_advantage"
    )
    if invalid_tool_call_advantage is None and malformed_thinking_advantage is None:
        return invalid_tool_call_advantage, malformed_thinking_advantage

    # The is_invalid_tool_call / has_malformed_thinking flags these penalties rely on
    # are only populated by the NeMo-Gym environment. Without that path the penalties
    # would silently no-op, so fail loudly instead.
    assert _should_use_nemo_gym(master_config), (
        "grpo.invalid_tool_call_advantage / grpo.malformed_thinking_advantage require "
        "the NeMo-Gym path (env.should_use_nemo_gym=true); they are not supported with "
        "the native generation path."
    )
    return invalid_tool_call_advantage, malformed_thinking_advantage


def _apply_message_level_advantage_penalties(
    train_data: BatchedDataDict[ClippedPGLossDataDict],
    message_logs: list[LLMMessageLogType | VLMMessageLogType],
    invalid_tool_call_advantage: float | None,
    malformed_thinking_advantage: float | None,
    log_config: bool = False,
) -> None:
    """Overwrite advantages for flagged assistant-message token spans.

    For each assistant message flagged by the NeMo-Gym detector as an invalid
    tool call or malformed thinking, overwrite that message's advantage span in
    ``train_data["advantages"]`` with the configured negative value. No-op when
    neither ``grpo.invalid_tool_call_advantage`` nor
    ``grpo.malformed_thinking_advantage`` is set.

    Args:
        train_data: Training batch; ``advantages`` is modified in place.
        message_logs: Batch of message logs with per-message flags.
        invalid_tool_call_advantage: Advantage value assigned to invalid tool calls.
        malformed_thinking_advantage: Advantage value assigned to malformed thinking.
        log_config: If True, print the configured penalty values once.
    """
    invalid_neg_adv = invalid_tool_call_advantage
    malformed_neg_adv = malformed_thinking_advantage
    if invalid_neg_adv is None and malformed_neg_adv is None:
        return

    if log_config:
        print(
            f"Invalid tool call advantage: {invalid_neg_adv}",
            flush=True,
        )
        print(
            f"Malformed thinking advantage: {malformed_neg_adv}",
            flush=True,
        )

    for i, message_log in enumerate(message_logs):
        token_offset = 0
        for j, message in enumerate(message_log):
            token_ids = cast(torch.Tensor, message["token_ids"])
            msg_len = len(token_ids)
            is_assistant = (
                message["role"] == "assistant" and "generation_logprobs" in message
            )
            is_invalid = (
                is_assistant
                and invalid_neg_adv is not None
                and message.get("is_invalid_tool_call", False)
            )
            is_malformed_thinking = (
                is_assistant
                and malformed_neg_adv is not None
                and message.get("has_malformed_thinking", False)
            )
            if is_invalid:
                print(
                    f"Setting negative advantage ({invalid_neg_adv}) for invalid tool call in assistant message {i} {j}",
                    flush=True,
                )
                train_data["advantages"][i, token_offset : token_offset + msg_len] = (
                    invalid_neg_adv
                )
            elif is_malformed_thinking:
                print(
                    f"Setting negative advantage ({malformed_neg_adv}) for malformed thinking in assistant message {i} {j}",
                    flush=True,
                )
                train_data["advantages"][i, token_offset : token_offset + msg_len] = (
                    malformed_neg_adv
                )
            token_offset += msg_len


def _apply_configured_message_level_advantage_penalties(
    train_data: BatchedDataDict[ClippedPGLossDataDict],
    message_logs: list[LLMMessageLogType | VLMMessageLogType],
    master_config: MasterConfig,
    log_config: bool = False,
) -> None:
    """Resolve config and apply message-level advantage penalties."""
    (
        invalid_tool_call_advantage,
        malformed_thinking_advantage,
    ) = _resolve_message_level_advantage_penalties(master_config)
    _apply_message_level_advantage_penalties(
        train_data=train_data,
        message_logs=message_logs,
        invalid_tool_call_advantage=invalid_tool_call_advantage,
        malformed_thinking_advantage=malformed_thinking_advantage,
        log_config=log_config,
    )


def _should_use_async_rollouts(master_config: MasterConfig) -> bool:
    """Determine if async rollouts should be used based on the configuration.

    Returns True if vLLM backend is used with async_engine enabled.
    """
    generation_config = master_config.policy["generation"]
    if generation_config is None:
        return False

    backend = generation_config.get("backend", "")
    if backend != "vllm":
        return False

    vllm_cfg = generation_config.get("vllm_cfg", {})
    return vllm_cfg.get("async_engine", False)


def _should_use_nemo_gym(master_config: MasterConfig) -> bool:
    """Determine if NeMo-Gym should be used for rollouts and validation based on the configuration."""
    env_config = master_config.env
    should_use_nemo_gym = bool(env_config.get("should_use_nemo_gym"))
    if not should_use_nemo_gym:
        return should_use_nemo_gym

    # Validate the setup for training with NeMo-Gym
    assert _should_use_async_rollouts(master_config), (
        "❌ Error: In order to use NeMo-Gym, you must use vllm generation backend with `async_engine: true`!"
    )

    # We piggyback off of `_should_use_async_rollouts` to guarantee the existence of these configs.
    generation_config = master_config.policy["generation"]
    should_expose_http_server = generation_config["vllm_cfg"].get("expose_http_server")
    assert should_expose_http_server, (
        "In order to use NeMo-Gym, you must expose the vllm server via `expose_http_server: true`!"
    )

    return should_use_nemo_gym


def _should_log_nemo_gym_responses(master_config: MasterConfig) -> bool:
    env_config = master_config.env
    should_log_nemo_gym_responses = bool(
        env_config.get("should_log_nemo_gym_responses")
    )

    return should_log_nemo_gym_responses


def _create_advantage_estimator(master_config: MasterConfig):
    """Create and return an advantage estimator based on configuration.

    Args:
        master_config: The master configuration dictionary.

    Returns:
        An advantage estimator instance (GRPO, GDPO, or ReinforcePlusPlus).

    Raises:
        ValueError: If the advantage estimator name is not recognized.
    """
    grpo_config = master_config.grpo
    loss_config = master_config.loss_fn

    # Provide backward-compatible defaults when adv_estimator is not in config.
    # Fall back to top-level grpo.normalize_rewards / grpo.use_leave_one_out_baseline
    # which older configs still use.
    adv_estimator_config = grpo_config.get(
        "adv_estimator",
        {
            "name": "grpo",
            "normalize_rewards": grpo_config.get("normalize_rewards", True),
            "use_leave_one_out_baseline": grpo_config.get(
                "use_leave_one_out_baseline", False
            ),
            "minus_baseline": True,
        },
    )

    adv_estimator_name = adv_estimator_config["name"]
    if adv_estimator_name == "gdpo":
        adv_estimator = GDPOAdvantageEstimator(adv_estimator_config, loss_config)
        print("  ✓ Using GDPO advantage estimator (multi-reward)")
    elif adv_estimator_name == "grpo":
        adv_estimator = GRPOAdvantageEstimator(adv_estimator_config, loss_config)
        print("  ✓ Using GRPO advantage estimator")
    elif adv_estimator_name == "reinforce_plus_plus":
        adv_estimator = ReinforcePlusPlusAdvantageEstimator(
            adv_estimator_config, loss_config
        )
        print("  ✓ Using Reinforce++ advantage estimator")
    else:
        raise ValueError(f"Invalid adv_estimator name: {adv_estimator_name}")

    return adv_estimator


def _clip_grpo_advantages(
    advantages: torch.Tensor,
    grpo_config: dict[str, Any],
) -> torch.Tensor:
    """Clamp normalized advantages when clip bounds are configured."""
    clip_low = grpo_config.get("advantage_clip_low", None)
    clip_high = grpo_config.get("advantage_clip_high", None)
    if clip_low is not None:
        advantages = advantages.clamp(min=clip_low)
    if clip_high is not None:
        advantages = advantages.clamp(max=clip_high)
    return advantages


def refit_policy_generation(
    policy: ColocatablePolicyInterface,
    policy_generation: GenerationInterface,
    colocated_inference: bool,
    _refit_buffer_size_gb: Optional[int] = None,
    timer: Optional[Timer] = None,
    kv_scales: Optional[dict[str, float]] = None,
) -> None:
    """Refit the policy generation interface with the latest policy weights.

    Args:
        policy: The policy to provide weights to the inference engine.
        policy_generation: The inference engine to refit.
        _refit_buffer_size_gb: The size of the buffer to use for refitting.
            If it is None, the buffer size will be computed by the remaining memory.
            This parameter is primarily used for testing.
        timer: Optional Timer used to time the prepare/transfer/update phase
        kv_scales: Optional dictionary of KV cache scales for FP8 quantization.
    """
    if colocated_inference:
        policy.offload_before_refit()
        policy_generation.prepare_for_generation(tags=["weights"])

    # Create a context manager that does nothing when timer is None
    timer_context = (
        timer.time("prepare_for_generation/transfer_and_update_weights")
        if timer is not None
        else nullcontext()
    )
    with timer_context:
        # update weights
        update_success = False
        if colocated_inference:
            # get model param keys, which is grouped by size
            if _refit_buffer_size_gb is not None:
                buffer_size_bytes = _refit_buffer_size_gb * (1024**3)
            else:
                # Empirically sets ratio as 30% to maximize efficiency.
                # The remaining 70% is a necessary buffer reserved for the parameter all-gathering across the expert-parallelism dimension.
                memory_ratio = os.getenv("NRL_REFIT_BUFFER_MEMORY_RATIO", "0.3")
                buffer_size_bytes = int(
                    policy.get_free_memory_bytes() * float(memory_ratio)
                )

            if isinstance(policy_generation, SGLangGeneration):
                sglang_url_to_gpu_uuids = (
                    policy_generation.get_sglang_url_to_gpu_uuids()
                )
                # Stream weights via HTTP
                flush_success = policy_generation.invalidate_kv_cache()
                if not flush_success:
                    print("SGLang KV cache invalidation failed before weight update. ")
                futures_train = policy.stream_weights_via_http(
                    sglang_url_to_gpu_uuids=sglang_url_to_gpu_uuids,
                )
                # Wait for all workers to complete
                ray.get(futures_train)
                update_success = True
            else:
                # Original ZMQ IPC path for vLLM
                futures_train = policy.stream_weights_via_ipc_zmq(
                    buffer_size_bytes=buffer_size_bytes
                )
                futures_inference = policy_generation.update_weights_via_ipc_zmq()
                # wait for all futures to complete
                ray.get(futures_train)
                results = ray.get(futures_inference)
                update_success = all(result for result in results if result is not None)
        else:
            # update weights through nccl
            # SGLang haven't implemented non-colocated inference mode.
            if isinstance(policy_generation, SGLangGeneration):
                raise NotImplementedError(
                    "SGLang haven't implemented non-colocated inference mode. "
                )
            policy.offload_before_refit()
            futures_train = policy.broadcast_weights_for_collective(kv_scales=kv_scales)
            futures_inference = policy_generation.update_weights_from_collective()
            # wait for all futures to complete
            ray.get(futures_train)
            results = ray.get(futures_inference)
            update_success = all(result for result in results if result is not None)
            policy.prepare_for_training()

        # check if update is successful
        if not update_success:
            error_tag = "cuda-ipc" if colocated_inference else "nccl"
            error_message = (
                "❌ Error: Updating weights for the generation policy failed during refit.\n"
                f"This often indicates an issue with {error_tag} or "
                "a problem within the generation backend (e.g., vLLM worker).\n"
            )
            raise RuntimeError(error_message)

    if colocated_inference:
        policy.offload_after_refit()
        policy_generation.prepare_for_generation(tags=["kv_cache"])


def _log_mixed_rewards_and_advantages_information(
    logger: Logger,
    total_steps: int,
    metrics: dict[str, Any],
    baseline: torch.Tensor,
    advantages: torch.Tensor,
) -> None:
    # The histograms that are logged are logged with a prefix "train/" to the name, since that is what the remaining metrics will be logged with.
    logger.log_histogram(
        baseline.numpy(), total_steps + 1, "train/baseline_reward/histogram"
    )
    metrics["baseline_reward/pct_0"] = 100 * (baseline == 0).float().mean().item()
    metrics["baseline_reward/pct_1"] = 100 * (baseline == 1).float().mean().item()
    metrics["baseline_reward/pct_mixed"] = (
        100 - metrics["baseline_reward/pct_0"] - metrics["baseline_reward/pct_1"]
    )

    logger.log_histogram(
        advantages.numpy(), total_steps + 1, "train/advantages/histogram"
    )
    metrics["advantages/sum"] = advantages.float().sum().item()
    metrics["advantages/mean"] = advantages.float().mean().item()


def compute_and_apply_seq_logprob_error_masking(
    train_data: BatchedDataDict,
    rewards: torch.Tensor,
    seq_logprob_error_threshold: Optional[float],
) -> dict:
    """Compute sequence-level logprob error metrics and optionally mask high-error sequences.

    This function computes the multiplicative probability error per sequence
    (same calculation as token_mult_prob_error but aggregated per-sequence) and
    optionally masks sequences that exceed the configured threshold.

    Args:
        train_data: Training data dict containing token_mask, sample_mask,
                   prev_logprobs, and generation_logprobs. If masking is applied,
                   sample_mask will be updated in-place.
        rewards: Reward tensor for computing statistics on masked sequences.
        seq_logprob_error_threshold: If set, mask sequences with mult_prob_error
                                    exceeding this threshold. If None, only compute metrics.

    Returns:
        Dict with keys: max_seq_mult_prob_error, mean_seq_mult_prob_error,
        min_seq_mult_prob_error, max/mean/min_seq_mult_prob_error_after_mask,
        num_masked_seqs, masked_correct_pct
    """
    # Compute sequence-level logprob error metrics (always)
    token_mask = train_data["token_mask"][:, 1:]
    sample_mask = train_data["sample_mask"]
    prev_logprobs = train_data["prev_logprobs"][:, 1:]
    generation_logprobs = train_data["generation_logprobs"][:, 1:]
    lp_error = torch.abs(generation_logprobs - prev_logprobs)

    # Use combined mask exactly as in loss function
    mask = token_mask * sample_mask.unsqueeze(-1)

    # Calculate sequence-level multiplicative prob error.
    #
    # NOTE: When a sequence is fully masked (mask.sum == 0), it should not contribute to
    # min/mean/max statistics; otherwise, it would yield a spurious 0 due to denominator
    # clamping and incorrectly drag min_seq_mult_prob_error to 0.
    denom = mask.sum(dim=-1)
    valid_seq_mask = denom > 0

    # EXACT same calculation as token_mult_prob_error but per-sequence (for valid sequences)
    seq_mult_prob_error = torch.zeros_like(denom, dtype=lp_error.dtype)
    if valid_seq_mask.any():
        num = (torch.exp(lp_error * mask) * mask).sum(dim=-1)
        seq_mult_prob_error[valid_seq_mask] = num[valid_seq_mask] / denom[
            valid_seq_mask
        ].clamp(min=1)

        valid_errors = seq_mult_prob_error[valid_seq_mask]
        max_seq_mult_prob_error = valid_errors.max().item()
        mean_seq_mult_prob_error = valid_errors.mean().item()
        min_seq_mult_prob_error = valid_errors.min().item()
    else:
        max_seq_mult_prob_error = 0.0
        mean_seq_mult_prob_error = 0.0
        min_seq_mult_prob_error = 0.0

    # Apply sequence-level masking if configured
    num_masked_seqs = 0
    masked_correct_pct = 0.0

    # After-mask metrics (same as before if no threshold)
    max_seq_mult_prob_error_after_mask = max_seq_mult_prob_error
    mean_seq_mult_prob_error_after_mask = mean_seq_mult_prob_error
    min_seq_mult_prob_error_after_mask = min_seq_mult_prob_error

    if seq_logprob_error_threshold is not None:
        print(
            f"▶ Applying sequence-level logprob error masking (threshold={seq_logprob_error_threshold})...",
            flush=True,
        )

        original_sample_mask = sample_mask.clone()

        # Create mask for sequences below threshold
        seq_error_mask = (
            seq_mult_prob_error <= seq_logprob_error_threshold
        ).float() * original_sample_mask

        diff_mask = original_sample_mask - seq_error_mask
        num_masked_seqs = int(diff_mask.sum().item())

        if num_masked_seqs > 0:
            diff_mask_bool = diff_mask.bool()
            masked_correct_count = int(
                (rewards.view(-1)[diff_mask_bool] == 1).sum().item()
            )
            masked_correct_pct = masked_correct_count / num_masked_seqs

        # Compute after-mask metrics (only for sequences that passed the threshold)
        kept_mask = seq_error_mask.bool() & valid_seq_mask
        if kept_mask.sum() > 0:
            kept_errors = seq_mult_prob_error[kept_mask]
            max_seq_mult_prob_error_after_mask = kept_errors.max().item()
            mean_seq_mult_prob_error_after_mask = kept_errors.mean().item()
            min_seq_mult_prob_error_after_mask = kept_errors.min().item()
        else:
            # All sequences were masked
            max_seq_mult_prob_error_after_mask = 0.0
            mean_seq_mult_prob_error_after_mask = 0.0
            min_seq_mult_prob_error_after_mask = 0.0

        # Update sample_mask in train_data
        train_data["sample_mask"] = seq_error_mask

        print(
            f"  Masked {num_masked_seqs} sequences with mult_prob_error > {seq_logprob_error_threshold}",
            flush=True,
        )
        if num_masked_seqs > 0:
            print(
                f"  • {masked_correct_count}/{num_masked_seqs} masked sequences were correct (reward=1)"
                f" → {masked_correct_pct:.2%}",
                flush=True,
            )

    return {
        "max_seq_mult_prob_error": max_seq_mult_prob_error,
        "mean_seq_mult_prob_error": mean_seq_mult_prob_error,
        "min_seq_mult_prob_error": min_seq_mult_prob_error,
        "max_seq_mult_prob_error_after_mask": max_seq_mult_prob_error_after_mask,
        "mean_seq_mult_prob_error_after_mask": mean_seq_mult_prob_error_after_mask,
        "min_seq_mult_prob_error_after_mask": min_seq_mult_prob_error_after_mask,
        "num_masked_seqs": num_masked_seqs,
        "masked_correct_pct": masked_correct_pct,
    }


# ===============================================================================
# Training & Validation
# ===============================================================================


def grpo_train(
    policy: ColocatablePolicyInterface,
    policy_generation: Optional[GenerationInterface],
    wrapped_dataloader: StatefulDataLoader | MultipleDataloaderWrapper,
    val_dataloader: Optional[StatefulDataLoader],
    tokenizer: TokenizerType,
    loss_fn: LossFunction,
    task_to_env: dict[str, EnvironmentInterface],
    val_task_to_env: Optional[dict[str, EnvironmentInterface]],
    logger: Logger,
    checkpointer: CheckpointManager,
    grpo_save_state: GRPOSaveState,
    master_config: MasterConfig,
) -> None:
    """Run GRPO training algorithm."""
    timer = Timer()
    timeout = TimeoutChecker(
        timeout=master_config.checkpointing["checkpoint_must_save_by"],
        fit_last_save_time=True,
    )
    timeout.start_iterations()
    memory_tracker = MemoryTracker()

    kv_scales_cache = None  # Cache reused for computed kv scales

    NEED_REFIT = True
    # If policy_generation is None, use the policy as the generation interface (megatron framework backend)
    if policy_generation is None:
        policy_generation = policy  # type: ignore
        NEED_REFIT = False
    POLICY_GENERATION_STALE = True  # tracks if generation needs a refit before running
    assert policy_generation is not None

    # Check if we need to sync KV cache scales
    # When fallback to policy as the policy_generation, we use getattr to check.
    sync_kv_scales = getattr(policy_generation, "requires_kv_scale_sync", False)

    # common config/state times
    current_step = grpo_save_state["current_step"]  # current step within an epoch
    total_steps = grpo_save_state["total_steps"]  # total steps across all epochs
    max_num_steps = master_config.grpo[
        "max_num_steps"
    ]  # max number of steps to train for
    current_epoch = grpo_save_state["current_epoch"]  # current epoch
    max_num_epochs = master_config.grpo[
        "max_num_epochs"
    ]  # max number of epochs to train for
    consumed_samples = grpo_save_state[
        "consumed_samples"
    ]  # total samples consumed across all epochs
    total_valid_tokens = grpo_save_state.get(
        "total_valid_tokens", 0
    )  # total valid tokens processed across all epochs; default to 0 for backward compatibility with older checkpoints
    val_at_start = master_config.grpo["val_at_start"]
    val_at_end = master_config.grpo["val_at_end"]
    val_period = master_config.grpo["val_period"]
    colocated_inference = master_config.policy["generation"]["colocated"]["enabled"]

    # Initialize advantage estimator
    adv_estimator = _create_advantage_estimator(master_config)

    # Run validation at the start if configured
    # TODO: Add validation with kv scales if needed
    if val_at_start and current_step == 0:
        print("\n🔍 Running initial validation...", flush=True)
        memory_tracker.snapshot_start_of_stage("Initial validation", dir())

        if NEED_REFIT and POLICY_GENERATION_STALE:
            refit_policy_generation(policy, policy_generation, colocated_inference)
            POLICY_GENERATION_STALE = False
        else:
            policy_generation.prepare_for_generation()
        val_metrics, validation_timings = validate(
            policy_generation,
            val_dataloader,
            tokenizer,
            val_task_to_env,
            step=0,
            master_config=master_config,
            logger=logger,
        )
        policy_generation.finish_generation()
        logger.log_metrics(val_metrics, current_step, prefix="validation")
        logger.log_metrics(validation_timings, current_step, prefix="timing/validation")

    if master_config.data["use_multiple_dataloader"]:
        warnings.warn(
            "When using multiple dataloaders, MultipleDataloaderWrapper operates as an infinite iterator. "
            "As a result, grpo.max_num_epochs will be ignored, and only grpo.max_num_steps will be used. "
            "See https://github.com/NVIDIA-NeMo/RL/blob/main/docs/guides/grpo.md#multiple-dataloaders for more details."
        )

    while current_epoch < max_num_epochs and total_steps < max_num_steps:
        memory_tracker.snapshot_start_of_stage("Preparing batch", dir())
        print(f"\n{'=' * 25} Epoch {current_epoch + 1}/{max_num_epochs} {'=' * 25}")
        # batch cache is used for DAPO. We store prompts with non-zero standard deviation in this cache.
        batch_cache: BatchedDataDict[DatumSpec] = None
        # This is the number of batches we processed so far at each step to generate responses whose std is non-zero. Maximum threshold is set by dynamic_sampling_max_gen_batches. Used in the case of dynamic sampling.
        dynamic_sampling_num_gen_batches = 0

        # Run grpo/dapo training loop (single-turn)
        for batch in wrapped_dataloader:
            # A central place to store logging data that won't be deleted until the loop ends
            metrics_logging_data = dict()
            metrics = dict()

            if master_config.data["use_multiple_dataloader"]:
                print(
                    f"\n{'=' * 25} Step {current_step + 1}/{max_num_steps} {'=' * 25}",
                    flush=True,
                )
            else:
                print(
                    f"\n{'=' * 25} Step {current_step + 1}/{min(len(wrapped_dataloader), max_num_steps)} {'=' * 25}",
                    flush=True,
                )

            maybe_gpu_profile_step(policy, total_steps + 1)
            if policy != policy_generation:
                maybe_gpu_profile_step(policy_generation, total_steps + 1)
            val_metrics, validation_timings = None, None

            with timer.time("total_step_time"):
                # Prepare batch
                print("▶ Preparing batch...", flush=True)
                with timer.time("data_processing"):
                    # Repeat batch items
                    repeated_batch: BatchedDataDict[DatumSpec] = (
                        batch.repeat_interleave(
                            master_config.grpo["num_generations_per_prompt"]
                        )
                    )
                    # Convert LLMMessageLogType to FlatMessagesType for generation
                    batched_flat, input_lengths = batched_message_log_to_flat_message(
                        repeated_batch["message_log"],
                        pad_value_dict={"token_ids": tokenizer.pad_token_id},
                    )
                    input_ids = batched_flat["token_ids"]

                # Generate responses - this updates the LLMMessageLogType in repeated_batch
                memory_tracker.snapshot_start_of_stage("Generation", dir())
                print(
                    f"▶ Generating responses for batch of size {repeated_batch.size}...",
                    flush=True,
                )
                with timer.time("prepare_for_generation/total"):
                    if NEED_REFIT and POLICY_GENERATION_STALE:
                        # Compute KV scales if needed for FP8 quantization
                        if sync_kv_scales and kv_scales_cache is None:
                            print("▶ Computing KV cache scales...", flush=True)
                            policy.prepare_for_lp_inference()
                            # Align with training data processing to ensure parallel training compatibility
                            calib_flat, calib_input_lengths = (
                                batched_message_log_to_flat_message(
                                    repeated_batch["message_log"],
                                    pad_value_dict={
                                        "token_ids": tokenizer.pad_token_id
                                    },
                                    make_sequence_length_divisible_by=master_config.policy[
                                        "make_sequence_length_divisible_by"
                                    ],
                                )
                            )
                            # Create calibration data from flattened messages
                            calibration_data = BatchedDataDict[ClippedPGLossDataDict](
                                {
                                    "input_ids": calib_flat["token_ids"],
                                    "input_lengths": calib_input_lengths,
                                }
                            )
                            calibration_data.update(
                                calib_flat.get_multimodal_dict(as_tensors=False)
                            )
                            calibration_data.to("cpu")
                            kv_scales_cache = policy.calibrate_qkv_fp8_scales(
                                calibration_data, include_q=True
                            )["layers"]

                        refit_policy_generation(
                            policy,
                            policy_generation,
                            colocated_inference,
                            timer=timer,
                            kv_scales=kv_scales_cache if sync_kv_scales else None,
                        )
                        POLICY_GENERATION_STALE = False
                    else:
                        if colocated_inference:
                            policy.offload_after_refit()  # unload optimizer to make space for generation
                        policy_generation.prepare_for_generation()

                dynamic_sampling_num_gen_batches += 1
                if dynamic_sampling_num_gen_batches == 1 and hasattr(
                    policy_generation, "snapshot_step_metrics"
                ):
                    policy_generation.snapshot_step_metrics()
                with timer.time("generation"):
                    # Clear logger metrics for each generation step
                    if policy_generation is not None:
                        policy_generation.clear_logger_metrics()
                    # Use NeMo-Gym rollouts if enabled. We cascade NeMo-Gym first since NeMo-Gym requires async rollouts.
                    if _should_use_nemo_gym(master_config):
                        generation_config = master_config.policy["generation"]
                        nemo_gym_rollout_result = run_async_nemo_gym_rollout(
                            policy_generation=policy_generation,
                            input_batch=repeated_batch,
                            tokenizer=tokenizer,
                            task_to_env=task_to_env,
                            max_seq_len=master_config.policy[
                                "max_total_sequence_length"
                            ],
                            generation_config=generation_config,
                            max_rollout_turns=None,
                            greedy=False,
                        )
                        input_ids = nemo_gym_rollout_result.input_ids
                        repeated_batch = nemo_gym_rollout_result.final_batch
                        rollout_metrics = nemo_gym_rollout_result.rollout_metrics
                        del nemo_gym_rollout_result

                        # NeMo Gym responses can be very large and expensive to log. Here we have logic to opt-in to logging.
                        if not _should_log_nemo_gym_responses(master_config):
                            for key in list(rollout_metrics):
                                if "full_result" in key:
                                    rollout_metrics.pop(key)

                    # Use async rollouts if vLLM async engine is enabled
                    elif _should_use_async_rollouts(master_config):
                        (
                            repeated_batch,
                            rollout_metrics,
                        ) = run_async_multi_turn_rollout(
                            policy_generation=policy_generation,
                            input_batch=repeated_batch,
                            tokenizer=tokenizer,
                            task_to_env=task_to_env,
                            max_seq_len=master_config.policy[
                                "max_total_sequence_length"
                            ],
                            max_rollout_turns=master_config.grpo["max_rollout_turns"],
                            greedy=False,
                        )
                    else:
                        repeated_batch, rollout_metrics = run_multi_turn_rollout(
                            policy_generation=policy_generation,
                            input_batch=repeated_batch,
                            tokenizer=tokenizer,
                            task_to_env=task_to_env,
                            max_seq_len=master_config.policy[
                                "max_total_sequence_length"
                            ],
                            max_rollout_turns=master_config.grpo["max_rollout_turns"],
                            greedy=False,
                        )
                    policy_generation.finish_generation()
                    # Collect generation logger metrics for performance reporting after each generation step
                    # inflight batch sizes and num pending samples are collected from each worker
                    if policy_generation is not None:
                        generation_logger_metrics = (
                            policy_generation.get_logger_metrics()
                        )

                    metrics_logging_data["mean_gen_tokens_per_sample"] = (
                        rollout_metrics["mean_gen_tokens_per_sample"]
                    )
                    logger.log_metrics(rollout_metrics, total_steps + 1, prefix="train")

                repeated_batch = scale_rewards(
                    repeated_batch, master_config.grpo["reward_scaling"]
                )
                # Process rewards with custom reward function
                if master_config.grpo["reward_shaping"]["enabled"]:
                    repeated_batch = apply_reward_shaping(
                        repeated_batch, master_config.grpo["reward_shaping"]
                    )

                # Calculate rewards & advantages
                memory_tracker.snapshot_start_of_stage("Processing rewards", dir())
                print("▶ Processing rewards...,", flush=True)
                with timer.time("reward_calculation"):
                    # Extract rewards from final_batch
                    rewards = repeated_batch["total_reward"]

                    print("▶ Computing advantages...", flush=True)
                    # For DAPO with reward shaping, compute std on the raw
                    # pre-shaping reward so dynamic sampling filters prompt
                    # groups on the raw task metric (e.g. acc) instead of on
                    # length-dependent shaped reward variance. Baseline
                    # (which drives advantages) stays on the shaped reward.
                    std_rewards = (
                        repeated_batch["unshaped_total_reward"]
                        if master_config.grpo["use_dynamic_sampling"]
                        and "unshaped_total_reward" in repeated_batch
                        else None
                    )
                    if master_config.grpo.get("calculate_advantages_on_gpu"):
                        print("Computing advantages on GPU!")
                        # Just fix the device id for now
                        device_id = 0
                        baseline, std = calculate_baseline_and_std_per_prompt(
                            input_ids.cuda(device_id),
                            rewards.cuda(device_id),
                            torch.ones_like(rewards).cuda(device_id),
                            leave_one_out_baseline=master_config.grpo[
                                "use_leave_one_out_baseline"
                            ],
                            std_rewards=(
                                std_rewards.cuda(device_id)
                                if std_rewards is not None
                                else None
                            ),
                        )
                        baseline = baseline.cpu()
                        std = std.cpu()
                    else:
                        baseline, std = calculate_baseline_and_std_per_prompt(
                            input_ids,
                            rewards,
                            torch.ones_like(rewards),
                            leave_one_out_baseline=master_config.grpo[
                                "use_leave_one_out_baseline"
                            ],
                            std_rewards=std_rewards,
                        )

                    # Apply dynamic sampling to filter prompts with non-zero std (DAPO algorithm)
                    repeated_batch, is_batch_complete, batch_cache, ds_metrics = (
                        dynamic_sampling(
                            repeated_batch,
                            std,
                            baseline,
                            dynamic_sampling_num_gen_batches,
                            master_config,
                            timer,
                            batch_cache,
                        )
                    )
                    if ds_metrics:
                        ds_metrics["dynamic_sampling_num_gen_batches"] = (
                            dynamic_sampling_num_gen_batches
                        )
                    # Get the updated rewards and baselines. For DAPO, these rewards and baselines only correspond to the prompts with non-zero std.
                    rewards = (
                        repeated_batch["total_reward"]
                        if not master_config.grpo["use_dynamic_sampling"]
                        else repeated_batch["filtered_reward"]
                    )
                    baseline = repeated_batch["baseline"]
                    std = repeated_batch["std"]

                    # If the current batch is not enough to fill the buffer during dynamic sampling, we update the cache and process the next batch.
                    if not is_batch_complete:
                        continue

                    gen_step_metrics = {}
                    if hasattr(policy_generation, "get_step_metrics"):
                        gen_step_metrics = policy_generation.get_step_metrics()

                    # Save baseline for logging (before deletion)
                    baseline_for_log = baseline.clone()

                    # Extract original prompt messages using the length field
                    # This correctly handles multi-turn prompts that contain assistant messages
                    initial_prompt_message_logs = extract_initial_prompt_messages(
                        repeated_batch["message_log"],
                        repeated_batch["length"],
                    )
                    prompt_batched_flat, _ = batched_message_log_to_flat_message(
                        initial_prompt_message_logs,
                        pad_value_dict={"token_ids": tokenizer.pad_token_id},
                    )
                    prompt_ids_for_adv = prompt_batched_flat["token_ids"]
                    del initial_prompt_message_logs
                    del prompt_batched_flat
                    del input_ids
                    del baseline
                    del std

                with timer.time("data_processing"):
                    use_overlong_filtering = master_config.grpo["overlong_filtering"]
                    if use_overlong_filtering:
                        loss_multiplier = repeated_batch["loss_multiplier"].clone()
                        truncated = repeated_batch["truncated"]

                        if isinstance(truncated, list):
                            truncated = torch.tensor(truncated, dtype=torch.bool)

                        loss_multiplier[truncated] = 0
                        repeated_batch["loss_multiplier"] = loss_multiplier
                    add_grpo_token_loss_masks_and_generation_logprobs(
                        repeated_batch["message_log"]
                    )

                    # Convert updated LLMMessageLogType to FlatMessagesType for training
                    flat_messages, input_lengths = batched_message_log_to_flat_message(
                        repeated_batch["message_log"],
                        pad_value_dict={"token_ids": tokenizer.pad_token_id},
                        make_sequence_length_divisible_by=master_config.policy[
                            "make_sequence_length_divisible_by"
                        ],
                    )

                    # Create training data from flattened messages
                    # Note: advantages will be computed and added after logprobs are available
                    train_data = BatchedDataDict[ClippedPGLossDataDict](
                        {
                            "input_ids": flat_messages["token_ids"],
                            "input_lengths": input_lengths,
                            "generation_logprobs": flat_messages["generation_logprobs"],
                            "token_mask": flat_messages["token_loss_mask"],
                            "sample_mask": repeated_batch["loss_multiplier"],
                        }
                    )
                    # this will be mini-batched inside the policy, so maintain the packed multimodal structure
                    # This is also used to populate part of the downstream logprob calculation data
                    extra_multimodal_data = flat_messages.get_multimodal_dict(
                        as_tensors=False
                    )
                    train_data.update(extra_multimodal_data)
                    train_data.to("cpu")

                    metrics_logging_data["content"] = flat_messages["content"]

                memory_tracker.snapshot_start_of_stage("Computing logprobs", dir())
                # Skip prev_logprobs computation when force_on_policy_ratio=True
                # unless seq_logprob_error_threshold is set (which requires prev_logprobs)
                seq_logprob_error_threshold = master_config.grpo.get(
                    "seq_logprob_error_threshold", None
                )
                force_on_policy_ratio = master_config.loss_fn.force_on_policy_ratio
                skip_prev_logprobs = (
                    force_on_policy_ratio and seq_logprob_error_threshold is None
                )
                # todo @jiaqi: is there a better way to skip prev_logprobs computation while still computing the seq-level error metrics?
                if force_on_policy_ratio and seq_logprob_error_threshold is not None:
                    warnings.warn(
                        "force_on_policy_ratio=True but seq_logprob_error_threshold is set. "
                        "Computing prev_logprobs anyway for seq-level error masking."
                    )

                # Skip reference_policy_logprobs computation when skip_reference_policy_logprobs_calculation=True
                skip_reference_logprobs = master_config.grpo.get(
                    "skip_reference_policy_logprobs_calculation"
                )

                if not (skip_prev_logprobs and skip_reference_logprobs):
                    print("▶ Preparing for logprob inference...", flush=True)
                    with timer.time("logprob_inference_prep"):
                        policy.prepare_for_lp_inference()

                print("▶ Computing logprobs...", flush=True)
                with timer.time("policy_and_reference_logprobs"):
                    # Custom create this logprob_data so we avoid Ray comm overheads sending unused data to workers.
                    logprob_data = BatchedDataDict[ClippedPGLossDataDict](
                        {
                            "input_ids": train_data["input_ids"],
                            "input_lengths": train_data["input_lengths"],
                            "token_mask": flat_messages["token_loss_mask"],
                            "sample_mask": repeated_batch["loss_multiplier"],
                            **extra_multimodal_data,
                        }
                    )

                    if not skip_prev_logprobs:
                        train_data["prev_logprobs"] = policy.get_logprobs(
                            logprob_data, timer=timer
                        )["logprobs"]
                    else:
                        print(
                            "▶ Skipping prev_logprobs (force_on_policy_ratio=True)...",
                            flush=True,
                        )
                        train_data["prev_logprobs"] = torch.zeros_like(
                            train_data["generation_logprobs"]
                        )

                    if not skip_reference_logprobs:
                        train_data["reference_policy_logprobs"] = (
                            policy.get_reference_policy_logprobs(
                                logprob_data,
                                timer=timer,
                            )["reference_logprobs"]
                        )
                    else:
                        print(
                            "▶ Skipping reference_logprobs (skip_reference_policy_logprobs_calculation=True)...",
                            flush=True,
                        )
                        train_data["reference_policy_logprobs"] = torch.zeros_like(
                            train_data["prev_logprobs"]
                        )

                    del logprob_data
                    del extra_multimodal_data

                # Seq-level logprob error metrics/masking require real prev_logprobs
                if skip_prev_logprobs:
                    # Cannot compute seq-level metrics with placeholder prev_logprobs
                    seq_logprob_error_metrics = {
                        "max_seq_mult_prob_error": 0.0,
                        "mean_seq_mult_prob_error": 0.0,
                        "min_seq_mult_prob_error": 0.0,
                        "max_seq_mult_prob_error_after_mask": 0.0,
                        "mean_seq_mult_prob_error_after_mask": 0.0,
                        "min_seq_mult_prob_error_after_mask": 0.0,
                        "num_masked_seqs_by_logprob_error": 0,
                        "masked_correct_pct": 0.0,
                    }
                else:
                    seq_error_result = compute_and_apply_seq_logprob_error_masking(
                        train_data=train_data,
                        rewards=rewards,
                        seq_logprob_error_threshold=seq_logprob_error_threshold,
                    )
                    seq_logprob_error_metrics = seq_error_result
                    if "num_masked_seqs" in seq_logprob_error_metrics:
                        seq_logprob_error_metrics[
                            "num_masked_seqs_by_logprob_error"
                        ] = seq_logprob_error_metrics.pop("num_masked_seqs")

                # Compute advantages with adv_estimator using correct mask and logprobs
                with timer.time("advantage_calculation"):
                    print("▶ Computing advantages...", flush=True)
                    # Get token-level mask: token_mask * sample_mask
                    token_mask = train_data["token_mask"]
                    sample_mask = train_data["sample_mask"]
                    mask = token_mask * sample_mask.unsqueeze(-1)

                    train_data["advantages"] = adv_estimator.compute_advantage(
                        prompt_ids=prompt_ids_for_adv,
                        rewards=rewards,
                        mask=mask,
                        repeated_batch=repeated_batch,
                        logprobs_policy=train_data["prev_logprobs"],
                        logprobs_reference=train_data.get("reference_policy_logprobs"),
                    )
                    del prompt_ids_for_adv

                    # Log rewards and advantages information
                    _log_mixed_rewards_and_advantages_information(
                        logger=logger,
                        total_steps=total_steps,
                        metrics=metrics,
                        baseline=baseline_for_log,
                        advantages=train_data["advantages"],
                    )
                    del baseline_for_log

                    _apply_configured_message_level_advantage_penalties(
                        train_data, repeated_batch["message_log"], master_config
                    )

                    # Clip advantages to prevent extreme values from small std normalization
                    train_data["advantages"] = _clip_grpo_advantages(
                        train_data["advantages"], master_config.grpo
                    )

                memory_tracker.snapshot_start_of_stage("Policy train", dir())
                print("▶ Preparing for training...", flush=True)
                with timer.time("training_prep"):
                    policy.prepare_for_training()  # set model train and reload optim to GPU
                    POLICY_GENERATION_STALE = True

                print("▶ Training policy...", flush=True)
                with timer.time("policy_training"):
                    train_results = policy.train(
                        train_data,
                        loss_fn,
                        timer=timer,
                    )

                # Recompute KV scales after policy training if needed
                if sync_kv_scales:
                    with timer.time("recompute_kv_scales"):
                        print(
                            "▶ Recomputing KV cache scales after policy update...",
                            flush=True,
                        )
                        kv_scales_cache = policy.calibrate_qkv_fp8_scales(
                            train_data, include_q=True
                        )["layers"]
                        # Set generation as stale to force refit with new scales
                        POLICY_GENERATION_STALE = True

                is_last_step = total_steps + 1 >= max_num_steps
                if not master_config.data["use_multiple_dataloader"]:
                    is_last_step = is_last_step or (
                        (current_epoch + 1 == max_num_epochs)
                        and (current_step + 1 == len(wrapped_dataloader))
                    )

                # Run validation if it's a validation step or last step with val_at_end
                if (val_period > 0 and (total_steps + 1) % val_period == 0) or (
                    val_at_end and is_last_step
                ):
                    memory_tracker.snapshot_start_of_stage("Validation", dir())
                    if NEED_REFIT and POLICY_GENERATION_STALE:
                        refit_policy_generation(
                            policy,
                            policy_generation,
                            colocated_inference,
                            kv_scales=kv_scales_cache if sync_kv_scales else None,
                        )
                        POLICY_GENERATION_STALE = False
                    else:
                        if colocated_inference:
                            policy.offload_after_refit()  # unload optimizer to make space for generation
                        policy_generation.prepare_for_generation()
                    val_metrics, validation_timings = validate(
                        policy_generation,
                        val_dataloader,
                        tokenizer,
                        val_task_to_env,
                        step=total_steps + 1,
                        master_config=master_config,
                        logger=logger,
                    )
                    policy_generation.finish_generation()
                    logger.log_metrics(
                        validation_timings, total_steps + 1, prefix="timing/validation"
                    )
                    logger.log_metrics(
                        val_metrics, total_steps + 1, prefix="validation"
                    )

                # Get flat advantages and token mask for masked metrics computation
                flat_advantages = train_data["advantages"]
                flat_token_mask = flat_messages["token_loss_mask"]

                # Filter advantages using token mask (only valid response tokens)
                response_advantages = torch.masked_select(
                    flat_advantages, flat_token_mask.bool()
                )

                memory_tracker.snapshot_start_of_stage("Metrics", dir())
                metrics = {
                    **metrics,
                    "loss": train_results["loss"].numpy(),
                    "grad_norm": train_results["grad_norm"].numpy(),
                    "reward": rewards.numpy(),
                    "mean_prompt_length": repeated_batch["length"].numpy(),
                    "total_num_tokens": input_lengths.numpy(),
                    # Add masked advantages tracking metrics (only for valid response tokens)
                    "advantages/mean": torch.mean(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                    "advantages/max": torch.max(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                    "advantages/min": torch.min(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                    **ds_metrics,
                }
                if "moe_metrics" in train_results:
                    metrics.update(
                        {f"moe/{k}": v for k, v in train_results["moe_metrics"].items()}
                    )
                if master_config.grpo["use_dynamic_sampling"]:
                    metrics["filtered_reward"] = rewards.numpy()
                    metrics["reward"] = repeated_batch["total_reward"].numpy()

                metrics.update(train_results["all_mb_metrics"])
                metrics.update(gen_step_metrics)
                for k, v in metrics.items():
                    if k in {"probs_ratio_min", "probs_ratio_clamped_min"}:
                        valid_values = [x for x in v if not np.isinf(x)]
                        metrics[k] = (
                            np.min(valid_values).item() if valid_values else -1.0
                        )
                    elif k in {"probs_ratio_max", "probs_ratio_clamped_max"}:
                        valid_values = [x for x in v if not np.isinf(x)]
                        metrics[k] = (
                            np.max(valid_values).item() if valid_values else -1.0
                        )
                    elif k in {
                        "lr",
                        "wd",
                        "reward",
                        "filtered_reward",
                        "global_valid_seqs",
                        "global_valid_toks",
                        "mean_prompt_length",
                    }:
                        metrics[k] = np.mean(v).item()
                    elif isinstance(v, (np.ndarray, list)):
                        metrics[k] = np.sum(v).item()
                    else:
                        print(f"Skipping aggregation for {k} ({type(v)})")

                metrics.update(rollout_metrics)
                metrics["generation_logger_metrics"] = generation_logger_metrics
                total_valid_tokens += metrics["global_valid_toks"]

                # Always log sequence-level error metrics (useful for deciding threshold)
                metrics.update(seq_logprob_error_metrics)

                ## Checkpointing
                consumed_samples += master_config.grpo["num_prompts_per_step"]
                timeout.mark_iteration()

                should_save_by_step = (
                    is_last_step
                    or (total_steps + 1) % master_config.checkpointing["save_period"]
                    == 0
                )
                # +1 because step is 0-indexed
                # Check if timeout-based checkpointing is enabled in config.
                should_save_by_timeout = timeout.check_save()

                memory_tracker.snapshot_start_of_stage("Checkpointing", dir())
                if master_config.checkpointing["enabled"] and (
                    should_save_by_step or should_save_by_timeout
                ):
                    policy.prepare_for_training()

                    # +1 because step is 0-indexed
                    grpo_save_state["current_step"] = current_step + 1
                    grpo_save_state["total_steps"] = total_steps + 1
                    grpo_save_state["current_epoch"] = current_epoch
                    grpo_save_state["total_valid_tokens"] = total_valid_tokens
                    if val_metrics is not None:
                        grpo_save_state["val_reward"] = val_metrics["accuracy"]
                    elif "val_reward" in grpo_save_state:
                        del grpo_save_state["val_reward"]
                    grpo_save_state["consumed_samples"] = consumed_samples

                    full_metric_name = master_config.checkpointing["metric_name"]
                    if full_metric_name is not None:
                        assert full_metric_name.startswith(
                            "train:"
                        ) or full_metric_name.startswith("val:"), (
                            f"metric_name={full_metric_name} must start with 'val:' or 'train:',\n"
                            f'followed by the corresponding name in the "val" or "train" metrics dictionary.'
                            f"  If you are using an old config, please updated checkpointing.metric_name to the new format, "
                            f" e.g. 'val_reward --> 'val:reward'"
                        )
                        prefix, metric_name = full_metric_name.split(":", 1)
                        metrics_source = metrics if prefix == "train" else val_metrics
                        if not metrics_source:
                            warnings.warn(
                                f"You asked to save checkpoints based on {metric_name} but no {prefix} metrics were collected. "
                                "This checkpoint will not be saved as top-k.",
                                stacklevel=2,
                            )
                            if full_metric_name in grpo_save_state:
                                del grpo_save_state[full_metric_name]
                        elif metric_name not in metrics_source:
                            raise ValueError(
                                f"Metric {metric_name} not found in {prefix} metrics"
                            )
                        else:
                            grpo_save_state[full_metric_name] = metrics_source[
                                metric_name
                            ]

                    with timer.time("checkpointing"):
                        print(
                            f"Saving checkpoint for step {total_steps + 1}...",
                            flush=True,
                        )
                        checkpoint_path = checkpointer.init_tmp_checkpoint(
                            total_steps + 1, grpo_save_state, master_config
                        )
                        policy.save_checkpoint(
                            weights_path=os.path.join(
                                checkpoint_path, "policy", "weights"
                            ),
                            optimizer_path=os.path.join(
                                checkpoint_path, "policy", "optimizer"
                            )
                            if checkpointer.save_optimizer
                            else None,
                            tokenizer_path=os.path.join(
                                checkpoint_path, "policy", "tokenizer"
                            ),
                            checkpointing_cfg=master_config.checkpointing,
                        )
                        if master_config.data["use_multiple_dataloader"]:
                            for (
                                task_name,
                                task_dataloader,
                            ) in wrapped_dataloader.dataloaders.items():
                                torch.save(
                                    task_dataloader.state_dict(),
                                    os.path.join(
                                        checkpoint_path,
                                        f"train_dataloader_{task_name}.pt",
                                    ),
                                )
                        else:
                            torch.save(
                                wrapped_dataloader.state_dict(),
                                os.path.join(checkpoint_path, "train_dataloader.pt"),
                            )
                        checkpointer.finalize_checkpoint(checkpoint_path)

            # Logging
            # Log training data
            memory_tracker.snapshot_start_of_stage("Logging", dir())
            if not _should_log_nemo_gym_responses(master_config):
                log_data = {}
                if "agent_ref" in repeated_batch:
                    log_data["agent_ref"] = repeated_batch["agent_ref"]
                log_data["content"] = flat_messages["content"]
                log_data["rewards"] = rewards.tolist()
                if master_config.grpo["use_dynamic_sampling"]:
                    log_data["filtered_rewards"] = rewards.tolist()
                    log_data["rewards"] = repeated_batch["total_reward"].tolist()
                log_data["input_lengths"] = input_lengths.tolist()
                log_data["token_ids"] = train_data["input_ids"].tolist()
                log_data["token_loss_mask"] = train_data["token_mask"].tolist()
                log_data["sample_loss_mask"] = train_data["sample_mask"].tolist()
                log_data["advantages"] = train_data["advantages"].tolist()
                log_data["generation_logprobs"] = train_data[
                    "generation_logprobs"
                ].tolist()
                log_data["prev_logprobs"] = train_data["prev_logprobs"].tolist()

                logger.log_batched_dict_as_jsonl(
                    log_data, f"train_data_step{total_steps + 1}.jsonl"
                )
                del log_data
            del flat_messages

            timing_metrics: dict[str, float] = timer.get_timing_metrics(
                reduction_op="sum"
            )  # type: ignore
            # track example with high token mult prob error above 1.05
            if metrics["token_mult_prob_error"] > 1.05:
                logger.log_plot_token_mult_prob_error(
                    {
                        "prompt_lengths": repeated_batch["length"],
                        "full_lengths": input_lengths,
                        "generation_logprobs": train_data["generation_logprobs"],
                        "prev_logprobs": train_data["prev_logprobs"],
                        "token_mask": train_data["token_mask"],
                        "sample_mask": train_data["sample_mask"],
                    },
                    total_steps + 1,
                    name="train/token_mult_prob_error_plot_sample",
                )
            del train_data
            if (
                master_config.policy["generation"]
                .get("vllm_cfg", {})
                .get("enable_vllm_metrics_logger", False)
                and master_config.logger["wandb_enabled"]
            ):
                log_generation_metrics_to_wandb(
                    generation_logger_metrics,
                    total_steps + 1,
                    master_config.policy["generation"]["vllm_cfg"][
                        "vllm_metrics_logger_interval"
                    ],
                    logger,
                )

            # Plot ISL/OSL/ISL+OSL histograms to wandb
            if (
                master_config.policy["generation"]
                .get("vllm_cfg", {})
                .get("async_engine", False)
            ):
                for metric_name in metrics.keys():
                    if metric_name.startswith("histogram/"):
                        logger.log_histogram(
                            metrics[metric_name],
                            total_steps + 1,
                            f"generation_metrics/{metric_name}",
                        )

            print("\n📊 Training Results:")

            print(f"  • Loss: {metrics['loss']:.4f}")
            if "draft_loss" in metrics:
                print(f"  • Draft Loss: {metrics['draft_loss']:.4f}")
            print(f"  • Generation KL Error: {metrics['gen_kl_error']:.4f}")
            if master_config.grpo["use_dynamic_sampling"]:
                print(f"  • Avg Filtered Reward: {np.mean(rewards.numpy()):.4f}")
                print(
                    f"  • Avg Total Reward: {np.mean(repeated_batch['total_reward'].numpy()):.4f}"
                )
            else:
                print(f"  • Avg Reward: {np.mean(rewards.numpy()):.4f}")
            print(
                f"  • Mean Generation Length: {metrics_logging_data['mean_gen_tokens_per_sample']:.4f}",
                flush=True,
            )

            print("\n⏱️  Timing:", flush=True)
            # Display total time first, separately
            total_time = timing_metrics.get("total_step_time", 0)

            number_of_samples_per_step = (
                master_config.grpo["num_prompts_per_step"]
                * master_config.grpo["num_generations_per_prompt"]
            )
            total_num_gpus = (
                master_config.cluster["num_nodes"]
                * master_config.cluster["gpus_per_node"]
            )

            print(f"  • Total step time: {total_time:.2f}s", flush=True)

            # Display all other timing metrics
            for k, v in sorted(
                timing_metrics.items(), key=lambda item: item[1], reverse=True
            ):
                if k != "total_step_time":
                    percent = (v / total_time * 100) if total_time > 0 else 0
                    print(f"  • {k}: {v:.2f}s ({percent:.1f}%)", flush=True)

            timing_metrics["valid_tokens_per_sec_per_gpu"] = (
                metrics["global_valid_toks"] / total_time / total_num_gpus
            )
            performance_metrics = print_performance_metrics(
                train_results, metrics, timing_metrics, master_config
            )

            logger.log_metrics(metrics, total_steps + 1, prefix="train")
            logger.log_metrics(
                performance_metrics, total_steps + 1, prefix="performance"
            )
            # step_finished=True here since this is the final log of our current step.
            logger.log_metrics(
                timing_metrics,
                total_steps + 1,
                prefix="timing/train",
                step_finished=True,
            )

            # Reset the batch and set dynamic_sampling_num_gen_batches to 0
            batch_cache = None
            dynamic_sampling_num_gen_batches = 0

            # Clear mem
            memory_tracker.snapshot_start_of_stage("After CPU memory clear", dir())

            # processing rewards
            del repeated_batch
            del rewards
            # train_data already deleted after logging above
            # logging
            del metrics
            if "val_metrics" in dir():
                del val_metrics

            timer.reset()
            current_step += 1
            total_steps += 1
            if should_save_by_timeout:
                memory_tracker.snapshot_start_of_stage("", dir())
                print("Timeout has been reached, stopping training early", flush=True)
                return
            if total_steps >= max_num_steps:
                memory_tracker.snapshot_start_of_stage("", dir())
                print(
                    "Max number of steps has been reached, stopping training early",
                    flush=True,
                )
                return

        current_epoch += 1
        current_step = 0  # Reset step counter for new epoch


def validate(
    policy_generation: GenerationInterface,
    val_dataloader: Optional[StatefulDataLoader],
    tokenizer,
    val_task_to_env: Optional[dict[str, EnvironmentInterface]],
    step: int,
    master_config: MasterConfig,
    logger: Optional[Logger] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run validation on the validation dataset."""
    if val_dataloader is None:
        assert val_dataloader is not None or master_config.grpo["val_period"] == 0, (
            "val_dataloader is None, so grpo.val_period must be 0"
        )
        print("  ⚠️ No validation dataloader provided, skipping validation", flush=True)
        return {}, {}

    timer = Timer()
    with timer.time("total_validation_time"):
        print(f"▶ Starting validation at step {step}...", flush=True)

        total_rewards = []
        total_lengths = []
        all_message_logs = []  # Collect all message logs

        max_batches = (
            master_config.grpo["max_val_samples"]
            // master_config.grpo["val_batch_size"]
        )
        for batch_idx, val_batch in enumerate(val_dataloader):
            if batch_idx >= max_batches:
                break

            additional_metrics_to_report = dict()
            # Generate responses (updates the LLMMessageLogType in batch_with_msg_logs)
            # Use async rollouts if vLLM async engine is enabled
            # We cascade NeMo-Gym first since NeMo-Gym also uses async rollouts.
            if _should_use_nemo_gym(master_config):
                generation_config = master_config.policy["generation"]
                nemo_gym_rollout_result = run_async_nemo_gym_rollout(
                    policy_generation=policy_generation,
                    input_batch=val_batch,
                    tokenizer=tokenizer,
                    task_to_env=val_task_to_env,
                    max_seq_len=master_config.policy["max_total_sequence_length"],
                    generation_config=generation_config,
                    max_rollout_turns=None,
                    greedy=False,
                )
                val_batch = nemo_gym_rollout_result.final_batch
                gen_metrics = nemo_gym_rollout_result.rollout_metrics
                additional_metrics_to_report = gen_metrics
            elif _should_use_async_rollouts(master_config):
                val_batch, gen_metrics = run_async_multi_turn_rollout(
                    policy_generation,
                    val_batch,
                    tokenizer,
                    val_task_to_env,
                    max_seq_len=master_config.policy["max_total_sequence_length"],
                    max_rollout_turns=master_config.grpo["max_rollout_turns"],
                    greedy=False,
                )
            else:
                val_batch, gen_metrics = run_multi_turn_rollout(
                    policy_generation,
                    val_batch,
                    tokenizer,
                    val_task_to_env,
                    max_seq_len=master_config.policy["max_total_sequence_length"],
                    max_rollout_turns=master_config.grpo["max_rollout_turns"],
                    greedy=False,
                )

            total_rewards.extend(val_batch["total_reward"].tolist())
            total_lengths.append(gen_metrics["mean_gen_tokens_per_sample"])

            # Collect message logs for later display
            to_env = [
                get_keys_from_message_log(
                    val_batch["message_log"][i], ["role", "content"]
                )
                for i in range(len(val_batch["message_log"]))
            ]

            all_message_logs.extend(to_env)

        # Calculate validation metrics
        num_samples = len(total_rewards)
        if num_samples > 0:
            rewards_t = torch.tensor(total_rewards, dtype=torch.float32)
            accuracy = rewards_t.mean().item()
        else:
            accuracy = 0.0

        avg_length = (
            sum(total_lengths) / len(total_lengths) if len(total_lengths) > 0 else 0.0
        )

        val_metrics = {
            "accuracy": accuracy,
            "avg_length": avg_length,
            **additional_metrics_to_report,
        }

        # Print sample conversations only once at the end of validation
        try:
            print_message_log_samples(
                all_message_logs,
                total_rewards,
                num_samples=min(
                    master_config.logger["num_val_samples_to_print"],
                    len(all_message_logs),
                ),
                step=step,
            )
        except Exception as e:
            print(f"\n  ⚠️ Error displaying message samples: {str(e)}")
            print("  ⚠️ Continuing validation without displaying samples...", flush=True)

    # Get timing metrics
    timing_metrics = timer.get_timing_metrics(reduction_op="sum")
    validation_time = timing_metrics.get("total_validation_time", 0)

    # Print summary of validation results
    print("\n📊 Validation Results:")
    print(f"    • Accuracy: {accuracy:.4f}")
    print(f"    • Average response length: {avg_length:.1f} tokens")
    print(f"    • Samples processed: {len(total_rewards)}", flush=True)

    # Print timing information
    print("\n  ⏱️  Validation Timing:")
    validation_time = timing_metrics.get("total_validation_time", 0)
    print(f"    • Total validation time: {validation_time:.2f}s", flush=True)

    # Log validation data to JSONL file
    if logger is not None:
        val_log_data = {
            "content": all_message_logs,
            "rewards": total_rewards,
        }
        logger.log_batched_dict_as_jsonl(val_log_data, f"val_data_step{step}.jsonl")

    # Make sure to reset the timer after validation
    timer.reset()

    # Explicit GPU memory cleanup after validation
    gc.collect()
    torch.cuda.empty_cache()

    return val_metrics, timing_metrics


def aggregate_rollout_metrics(
    per_group_metrics: dict[str, list],
) -> dict[str, Any]:
    """Aggregate rollout metrics from multiple trajectory groups.

    Different metric types are aggregated according to their semantics:
    - Metrics ending with "/min" or starting with "min_" (excluding "_rate" suffix): take the minimum
    - Metrics ending with "/max" or starting with "max_" (excluding "_rate" suffix): take the maximum
    - "total_turns": summed
    - Non-numeric values: passed through as-is
    - All other numeric metrics: averaged

    Args:
        per_group_metrics: A dict mapping metric names to lists of per-group values.

    Returns:
        A dict mapping metric names to their aggregated scalar values.
    """
    aggregated = {}
    for k, v in per_group_metrics.items():
        if not isinstance(v[0], (int, float)):
            aggregated[k] = v
        elif k.endswith("/min") or (k.startswith("min_") and not k.endswith("_rate")):
            aggregated[k] = min(v)
        elif k.endswith("/max") or (k.startswith("max_") and not k.endswith("_rate")):
            aggregated[k] = max(v)
        elif k == "total_turns":
            aggregated[k] = sum(v)
        else:
            aggregated[k] = sum(v) / len(v)
    return aggregated


def async_grpo_train(
    policy: ColocatablePolicyInterface,
    policy_generation: Optional[GenerationInterface],
    dataloader: StatefulDataLoader,
    val_dataloader: Optional[StatefulDataLoader],
    tokenizer: TokenizerType,
    loss_fn: LossFunction,
    task_to_env: dict[str, EnvironmentInterface],
    val_task_to_env: Optional[dict[str, EnvironmentInterface]],
    logger: Logger,
    checkpointer: CheckpointManager,
    grpo_save_state: GRPOSaveState,
    master_config: MasterConfig,
    max_trajectory_age_steps: int = 1,
) -> None:
    """Run asynchronous GRPO training with replay buffer.

    Args:
        policy: Training policy
        policy_generation: Generation interface
        dataloader: Training data loader
        val_dataloader: Validation data loader
        tokenizer: Tokenizer
        loss_fn: Loss function
        task_to_env: Training environments
        val_task_to_env: Validation environments
        logger: Logger
        checkpointer: Checkpoint manager
        grpo_save_state: Training state
        master_config: Master configuration
        max_trajectory_age_steps: Maximum age (in training steps) for trajectories to be used in training
    """
    # Ensure we are running with a compatible async generation backend
    assert _should_use_async_rollouts(master_config), (
        "Async GRPO requires vLLM backend with vllm_cfg.async_engine=True. "
        "Set policy.generation.vllm_cfg.async_engine to true in your config."
    )
    assert master_config.loss_fn.use_importance_sampling_correction, (
        "Importance sampling correction must be enabled for async GRPO for good convergence due to off-policy samples!"
    )

    if master_config.grpo["async_grpo"]["max_trajectory_age_steps"] > 1:
        if not master_config.grpo["async_grpo"].get("in_flight_weight_updates", False):
            print(
                "⚠️ WARNING: In-flight weight updates must be enabled for async GRPO with max_trajectory_age_steps > 1. "
                "Without in-flight weight updates, having more max_trajectory_age_steps will not give any performance benefit."
            )

    # Import async utilities only when needed
    from nemo_rl.algorithms.async_utils import AsyncTrajectoryCollector, ReplayBuffer

    timer = Timer()
    timeout = TimeoutChecker(
        timeout=master_config.checkpointing["checkpoint_must_save_by"],
        fit_last_save_time=True,
    )
    timeout.start_iterations()
    NEED_REFIT = True

    # Setup generation interface
    if policy_generation is None:
        policy_generation = policy
        NEED_REFIT = False
    POLICY_GENERATION_STALE = True
    assert policy_generation is not None

    # Training state
    step = grpo_save_state["current_step"]
    weight_version = step  # Tracks refitted weight versions
    consumed_samples = grpo_save_state["consumed_samples"]
    total_valid_tokens = grpo_save_state.get(
        "total_valid_tokens", 0
    )  # Default to 0 for backward compatibility with older checkpoints
    val_period = master_config.grpo["val_period"]
    val_at_start = master_config.grpo["val_at_start"]
    val_at_end = master_config.grpo["val_at_end"]
    colocated_inference = master_config.policy["generation"]["colocated"]["enabled"]

    # Initialize advantage estimator
    adv_estimator = _create_advantage_estimator(master_config)

    assert not colocated_inference, (
        "Colocated inference is not supported for async GRPO. Please use non-colocated inference."
    )

    # Calculate minimum buffer size from training requirements
    # In per-prompt buffer mode, one buffer entry is 1 prompt * num_generations_per_prompt
    num_prompts_per_step = master_config.grpo["num_prompts_per_step"]
    samples_per_prompt_group = master_config.grpo["num_generations_per_prompt"]
    train_gbs = master_config.policy["train_global_batch_size"]

    # Ensure the buffer has at least one step worth of prompt-groups before training
    min_trajectories_needed = num_prompts_per_step

    print("📊 Buffer requirements calculation:")
    print(f"   - num_prompts_per_step: {num_prompts_per_step}")
    print(f"   - num_generations_per_prompt: {samples_per_prompt_group}")
    print(f"   - samples_per_prompt_group: {samples_per_prompt_group}")
    print(f"   - train_global_batch_size: {train_gbs}")
    print(f"   - min_trajectories_needed: {min_trajectories_needed} (async mode)")

    _replay_py_exec = get_actor_python_env(
        "nemo_rl.algorithms.async_utils.ReplayBuffer"
    )
    if _replay_py_exec.startswith("uv"):
        # Lazily build a dedicated venv across all Ray nodes on-demand.
        _replay_py_exec = create_local_venv_on_each_node(
            _replay_py_exec,
            "nemo_rl.algorithms.async_utils.ReplayBuffer",
        )

    _replay_py_venv = os.path.dirname(
        os.path.dirname(_replay_py_exec)
    )  # to remove the "bin/python" suffix

    _replay_runtime_env = {
        "py_executable": _replay_py_exec,
        "env_vars": {
            **os.environ,
            "VIRTUAL_ENV": _replay_py_venv,
            "UV_PROJECT_ENVIRONMENT": _replay_py_venv,
        },
    }

    # Calculate optimal buffer size based on generation limits to prevent length bias
    # Each weight version generates exactly num_prompts_per_step trajectories
    # With max_age_steps, we keep trajectories from multiple weight versions
    num_prompts_per_step = master_config.grpo["num_prompts_per_step"]
    late_arrival_slack = 2
    optimal_buffer_size = (
        num_prompts_per_step * max_trajectory_age_steps * late_arrival_slack
    )

    replay_buffer = ReplayBuffer.options(runtime_env=_replay_runtime_env).remote(
        max_size=optimal_buffer_size
    )

    _tc_py_exec = get_actor_python_env(
        "nemo_rl.algorithms.async_utils.AsyncTrajectoryCollector"
    )
    if _tc_py_exec.startswith("uv"):
        _tc_py_exec = create_local_venv_on_each_node(
            _tc_py_exec,
            "nemo_rl.algorithms.async_utils.AsyncTrajectoryCollector",
        )

    _tc_py_venv = os.path.dirname(
        os.path.dirname(_tc_py_exec)
    )  # to remove the "bin/python" suffix

    _tc_runtime_env = {
        "py_executable": _tc_py_exec,
        "env_vars": {
            **os.environ,
            "VIRTUAL_ENV": _tc_py_venv,
            "UV_PROJECT_ENVIRONMENT": _tc_py_venv,
        },
    }

    # Initialize trajectory collector with synchronized collection
    trajectory_collector = AsyncTrajectoryCollector.options(
        runtime_env=_tc_runtime_env
    ).remote(
        policy_generation=policy_generation,
        tokenizer=tokenizer,
        task_to_env=task_to_env,
        master_config=master_config,
        replay_buffer=replay_buffer,
        start_step=step,
    )

    # Start trajectory collection in background
    collection_task = trajectory_collector.start_collection.remote(dataloader)

    # Ensure collector knows initial weight version
    trajectory_collector.set_weight_version.remote(weight_version)

    print("📦 Started continuous background trajectory collection")

    print(
        f"🚀 Starting async GRPO training with buffer_size={optimal_buffer_size}, max_age={max_trajectory_age_steps} steps"
    )

    print("⏳ Preparing policy generation for training...")
    if NEED_REFIT and POLICY_GENERATION_STALE:
        print("🔄 Refitting policy generation with actual model weights...")
        try:
            refit_policy_generation(policy, policy_generation, colocated_inference)
            print("✅ Policy generation refit completed successfully")
            POLICY_GENERATION_STALE = False
        except Exception as e:
            print(f"❌ Policy generation refit failed: {e}")
            import traceback

            traceback.print_exc()
            return
    else:
        print("🔄 Preparing policy generation for inference...")
        try:
            policy_generation.prepare_for_generation()
            print("✅ Policy generation preparation completed successfully")
        except Exception as e:
            print(f"❌ Policy generation preparation failed: {e}")
            import traceback

            traceback.print_exc()
            return

    print("✅ Policy generation setup complete, proceeding to validation...")

    # Run validation at start if configured
    if val_at_start and step == 0:
        print("\n🔍 Running initial validation...")
        # Pause trajectory collection during initial validation
        trajectory_collector.pause.remote()

        try:
            val_metrics, validation_timings = validate(
                policy_generation,
                val_dataloader,
                tokenizer,
                val_task_to_env,
                step=0,
                master_config=master_config,
                logger=logger,
            )
            policy_generation.finish_generation()
            logger.log_metrics(val_metrics, step, prefix="validation")
            logger.log_metrics(validation_timings, step, prefix="timing/validation")
            print("✅ Initial validation completed successfully")
        except Exception as e:
            print(f"❌ Initial validation failed: {e}")
            import traceback

            traceback.print_exc()
            # Continue anyway since validation is optional
        finally:
            # Resume trajectory collection after initial validation
            trajectory_collector.resume.remote()

    print("✅ All setup complete, starting buffer wait...")
    # Clear logger metrics at start of training
    if policy_generation is not None:
        policy_generation.clear_logger_metrics()

    # Wait for initial buffer fill
    print(
        f"⏳ Waiting for replay buffer to have sufficient trajectories ({min_trajectories_needed} trajectories)..."
    )
    wait_iterations = 0
    while True:
        buffer_size_current = ray.get(replay_buffer.size.remote())

        print(
            f"  Wait iteration {wait_iterations}: buffer_filled_ratio={buffer_size_current}/{min_trajectories_needed}"
        )

        if buffer_size_current >= min_trajectories_needed:
            break

        time.sleep(1.0)

    print("✅ Buffer ready! Starting training loop...")

    # Main training loop
    try:
        while step < master_config.grpo["max_num_steps"]:
            print(
                f"\n{'=' * 25} Step {step + 1}/{master_config.grpo['max_num_steps']} {'=' * 25}"
            )
            maybe_gpu_profile_step(policy, step + 1)
            if policy != policy_generation:
                maybe_gpu_profile_step(policy_generation, step + 1)

            with timer.time("total_step_time"):
                # Sample trajectories from replay buffer
                print("📦 Sampling from replay buffer...")
                with timer.time("exposed_generation"):
                    buffer_size_current = ray.get(replay_buffer.size.remote())
                    print(
                        f"📊 Step coordination: training_step={step}, max_age={max_trajectory_age_steps}, buffer_size={buffer_size_current}"
                    )

                    # Sample the required number of per-prompt groups.
                    num_prompt_groups_needed = master_config.grpo[
                        "num_prompts_per_step"
                    ]
                    sample_result = ray.get(
                        replay_buffer.sample.remote(
                            num_prompt_groups=num_prompt_groups_needed,
                            current_weight_version=weight_version,
                            max_age_steps=max_trajectory_age_steps,
                        )
                    )

                    if (
                        sample_result is None
                        or len(sample_result["trajectories"])
                        != num_prompt_groups_needed
                    ):
                        print(
                            "⏳ Buffer empty or not enough groups to form a full step, waiting..."
                        )

                        # Get buffer debug info to help diagnose the issue
                        buffer_debug = ray.get(replay_buffer.get_debug_info.remote())
                        buffer_size = buffer_debug["total_trajectories"]

                        if buffer_size > 0:
                            print(
                                f"🔍 Debug: Buffer has {buffer_size} trajectories but sampling requires exactly {num_prompt_groups_needed}."
                            )
                            print(f"   Current weight version: {weight_version}")
                            print(f"   Max trajectory age: {max_trajectory_age_steps}")
                            print(
                                f"   Trajectory versions in buffer: {buffer_debug['trajectory_versions']}"
                            )

                        time.sleep(0.5)
                        continue

                    # Extract trajectories and metadata from sample result
                    trajectories = sample_result["trajectories"]
                    avg_trajectory_age = sample_result["avg_trajectory_age"]

                    print(
                        f"✅ Sampled {len(trajectories)} trajectory groups from buffer (avg age: {avg_trajectory_age:.2f} steps)"
                    )

                    # Concatenate per-prompt groups into a single training batch
                    per_prompt_batches = [t["batch"] for t in trajectories]
                    repeated_batch = BatchedDataDict.from_batches(per_prompt_batches)
                    # Aggregate rollout metrics across groups with proper aggregation per metric type
                    per_group_metrics = {}
                    for t in trajectories:
                        for k, v in t["rollout_metrics"].items():
                            per_group_metrics.setdefault(k, []).append(v)
                    rollout_metrics = aggregate_rollout_metrics(per_group_metrics)

                # Enforce fixed training batch: num_prompts_per_step * num_generations_per_prompt
                expected_batch_size = (
                    master_config.grpo["num_prompts_per_step"]
                    * master_config.grpo["num_generations_per_prompt"]
                )
                if repeated_batch.size != expected_batch_size:
                    print(
                        f"❌ Unexpected training batch size: got {repeated_batch.size}, expected {expected_batch_size}. Skipping step and waiting for correct buffer content."
                    )
                    time.sleep(0.5)
                    continue

                # Optional sanity: ensure DP divisibility to avoid sharding issues
                dp_size = policy.sharding_annotations.get_axis_size("data_parallel")
                if expected_batch_size % dp_size != 0:
                    raise AssertionError(
                        f"Configuration error: (num_prompts_per_step * num_generations_per_prompt) = {expected_batch_size} must be divisible by data_parallel size {dp_size}."
                    )

                print(f"Got trajectory batch (size: {repeated_batch.size})")

                print("▶ Processing rewards...")
                with timer.time("reward_calculation"):
                    # Extract original prompt messages using the length field
                    # This correctly handles multi-turn prompts that contain assistant messages
                    initial_prompt_message_logs = extract_initial_prompt_messages(
                        repeated_batch["message_log"],
                        repeated_batch["length"],
                    )

                    prompt_batched_flat, _ = batched_message_log_to_flat_message(
                        initial_prompt_message_logs,
                        pad_value_dict={"token_ids": tokenizer.pad_token_id},
                    )
                    prompt_ids_for_adv = prompt_batched_flat["token_ids"]
                    del initial_prompt_message_logs
                    del prompt_batched_flat

                    rewards = repeated_batch["total_reward"]

                    print(
                        f"  📊 Rewards stats: min={rewards.min():.4f}, max={rewards.max():.4f}, mean={rewards.mean():.4f}, std={rewards.std():.4f}"
                    )

                # Prepare training data (same as sync version)
                with timer.time("data_processing"):
                    # Apply overlong filtering - mask out truncated sequences from loss computation
                    with timer.time("overlong_filter"):
                        use_overlong_filtering = master_config.grpo[
                            "overlong_filtering"
                        ]
                        if use_overlong_filtering:
                            loss_multiplier = repeated_batch["loss_multiplier"].clone()
                            truncated = repeated_batch["truncated"]

                            if isinstance(truncated, list):
                                truncated = torch.tensor(truncated, dtype=torch.bool)

                            loss_multiplier[truncated] = 0
                            repeated_batch["loss_multiplier"] = loss_multiplier

                    # Add loss mask to each message
                    # Only unmask assistant messages that were actually generated (have generation_logprobs),
                    # not assistant messages that were part of the prompt history
                    add_grpo_token_loss_masks_and_generation_logprobs(
                        repeated_batch["message_log"]
                    )

                    # Convert to flat format for training
                    flat_messages, input_lengths = batched_message_log_to_flat_message(
                        repeated_batch["message_log"],
                        pad_value_dict={"token_ids": tokenizer.pad_token_id},
                        make_sequence_length_divisible_by=master_config.policy[
                            "make_sequence_length_divisible_by"
                        ],
                    )

                    # Create training data
                    # Note: advantages will be computed and added after logprobs are available
                    train_data = BatchedDataDict[ClippedPGLossDataDict](
                        {
                            "input_ids": flat_messages["token_ids"],
                            "input_lengths": input_lengths,
                            "generation_logprobs": flat_messages["generation_logprobs"],
                            "token_mask": flat_messages["token_loss_mask"],
                            "sample_mask": repeated_batch["loss_multiplier"],
                        }
                    )
                    train_data.to("cpu")

                # Training phase (same as sync version)
                # Skip prev_logprobs computation when force_on_policy_ratio=True
                # unless seq_logprob_error_threshold is set (which requires prev_logprobs)
                seq_logprob_error_threshold = master_config.grpo.get(
                    "seq_logprob_error_threshold", None
                )
                force_on_policy_ratio = master_config.loss_fn.force_on_policy_ratio
                skip_prev_logprobs = (
                    force_on_policy_ratio and seq_logprob_error_threshold is None
                )

                # todo @jiaqi: is there a better way to skip prev_logprobs computation while still computing the seq-level error metrics?
                if force_on_policy_ratio and seq_logprob_error_threshold is not None:
                    warnings.warn(
                        "force_on_policy_ratio=True but seq_logprob_error_threshold is set. "
                        "Computing prev_logprobs anyway for seq-level error masking."
                    )

                # Skip reference_policy_logprobs computation when skip_reference_policy_logprobs_calculation=True
                skip_reference_logprobs = master_config.grpo.get(
                    "skip_reference_policy_logprobs_calculation"
                )

                if not (skip_prev_logprobs and skip_reference_logprobs):
                    print("▶ Preparing for logprob inference...", flush=True)
                    with timer.time("logprob_inference_prep"):
                        policy.prepare_for_lp_inference()

                print("▶ Computing logprobs...", flush=True)
                with timer.time("policy_and_reference_logprobs"):
                    if not skip_prev_logprobs:
                        train_data["prev_logprobs"] = policy.get_logprobs(
                            train_data, timer=timer
                        )["logprobs"]
                    else:
                        train_data["prev_logprobs"] = torch.zeros_like(
                            train_data["generation_logprobs"]
                        )

                    if not skip_reference_logprobs:
                        train_data["reference_policy_logprobs"] = (
                            policy.get_reference_policy_logprobs(
                                train_data,
                                timer=timer,
                            )["reference_logprobs"]
                        )
                    else:
                        print(
                            "▶ Skipping reference_logprobs (skip_reference_policy_logprobs_calculation=True)...",
                            flush=True,
                        )
                        train_data["reference_policy_logprobs"] = torch.zeros_like(
                            train_data["prev_logprobs"]
                        )

                # Seq-level logprob error metrics/masking require real prev_logprobs
                if skip_prev_logprobs:
                    # Cannot compute seq-level metrics with placeholder prev_logprobs
                    seq_logprob_error_metrics = {
                        "max_seq_mult_prob_error": 0.0,
                        "mean_seq_mult_prob_error": 0.0,
                        "min_seq_mult_prob_error": 0.0,
                        "max_seq_mult_prob_error_after_mask": 0.0,
                        "mean_seq_mult_prob_error_after_mask": 0.0,
                        "min_seq_mult_prob_error_after_mask": 0.0,
                        "num_masked_seqs_by_logprob_error": 0,
                        "masked_correct_pct": 0.0,
                    }
                else:
                    seq_error_result = compute_and_apply_seq_logprob_error_masking(
                        train_data=train_data,
                        rewards=rewards,
                        seq_logprob_error_threshold=seq_logprob_error_threshold,
                    )
                    seq_logprob_error_metrics = seq_error_result
                    if "num_masked_seqs" in seq_logprob_error_metrics:
                        seq_logprob_error_metrics[
                            "num_masked_seqs_by_logprob_error"
                        ] = seq_logprob_error_metrics.pop("num_masked_seqs")

                # Compute advantages with adv_estimator using correct mask and logprobs
                with timer.time("advantage_calculation"):
                    print("▶ Computing advantages...", flush=True)
                    # Get token-level mask: token_mask * sample_mask
                    token_mask = train_data["token_mask"]
                    sample_mask = train_data["sample_mask"]
                    mask = token_mask * sample_mask.unsqueeze(-1)

                    train_data["advantages"] = adv_estimator.compute_advantage(
                        prompt_ids=prompt_ids_for_adv,
                        rewards=rewards,
                        mask=mask,
                        repeated_batch=repeated_batch,
                        logprobs_policy=train_data["prev_logprobs"],
                        logprobs_reference=train_data.get("reference_policy_logprobs"),
                    )
                    del prompt_ids_for_adv

                    # Log advantages stats
                    # Note: For GRPOAdvantageEstimator with normalize_rewards=True, these are
                    # already normalized advantages (equivalent to "Normalized advantages stats"
                    # in older versions). For ReinforcePlusPlusAdvantageEstimator, advantages
                    # are globally normalized across valid tokens.
                    advantages = train_data["advantages"]
                    print(
                        f"  📊 Advantages stats: min={advantages.min():.4f}, max={advantages.max():.4f}, mean={advantages.mean():.4f}, std={advantages.std():.4f}"
                    )

                    _apply_configured_message_level_advantage_penalties(
                        train_data,
                        repeated_batch["message_log"],
                        master_config,
                        log_config=True,
                    )

                    # Clip advantages to prevent extreme values from small std normalization
                    train_data["advantages"] = _clip_grpo_advantages(
                        train_data["advantages"], master_config.grpo
                    )

                print("▶ Preparing for training...")
                with timer.time("training_prep"):
                    policy.prepare_for_training()
                    POLICY_GENERATION_STALE = True

                print("▶ Training policy...")
                with timer.time("policy_training"):
                    train_results = policy.train(
                        train_data,
                        loss_fn,
                        timer=timer,
                    )

                print("🔄 Synchronizing policy weights to trajectory collector…")
                generation_logger_metrics = None
                if NEED_REFIT:
                    # Measure pending-generation wait as exposed_generation time
                    print("🔄 Coordinating with trajectory collector before refit...")
                    with timer.time("exposed_generation"):
                        ray.get(trajectory_collector.prepare_for_refit.remote())

                    # Collect generation logger metrics for performance reporting
                    # inflight batch sizes and num pending samples are collected from each worker
                    if policy_generation is not None:
                        generation_logger_metrics = (
                            policy_generation.get_logger_metrics()
                        )

                    # Only the actual refit/weight transfer should be counted as weight_sync
                    print("🔄 Performing policy generation refit...")
                    with timer.time("weight_sync"):
                        refit_policy_generation(
                            policy, policy_generation, colocated_inference
                        )
                        POLICY_GENERATION_STALE = False

                        # Update weight version before resuming trajectory collection so that all trajectories are updated with the new correct weight version
                        weight_version += 1
                        trajectory_collector.set_weight_version.remote(weight_version)
                        trajectory_collector.resume_after_refit.remote()

                # Clear logger metrics after each refit (weight sync), starting a new logging cycle
                if policy_generation is not None:
                    policy_generation.clear_logger_metrics()

                # Validation
                val_metrics, validation_timings = None, None
                is_last_step = step + 1 == master_config.grpo["max_num_steps"]

                # Run validation if it's a validation step or last step with val_at_end
                if (val_period > 0 and (step + 1) % val_period == 0) or (
                    val_at_end and is_last_step
                ):
                    # Pause trajectory collection during validation to reduce memory pressure
                    trajectory_collector.pause.remote()

                    if NEED_REFIT and POLICY_GENERATION_STALE:
                        refit_policy_generation(
                            policy, policy_generation, colocated_inference
                        )
                        POLICY_GENERATION_STALE = False
                    else:
                        policy_generation.prepare_for_generation()
                    val_metrics, validation_timings = validate(
                        policy_generation,
                        val_dataloader,
                        tokenizer,
                        val_task_to_env,
                        step=step + 1,
                        master_config=master_config,
                        logger=logger,
                    )
                    policy_generation.finish_generation()
                    logger.log_metrics(
                        validation_timings, step + 1, prefix="timing/validation"
                    )
                    logger.log_metrics(val_metrics, step + 1, prefix="validation")

                    # Explicit GPU memory cleanup after validation in async mode
                    import gc

                    gc.collect()
                    torch.cuda.empty_cache()

                    # Resume trajectory collection after validation
                    trajectory_collector.resume.remote()
                # Get flat advantages and token mask for masked metrics computation
                flat_advantages = train_data["advantages"]
                flat_token_mask = flat_messages["token_loss_mask"]
                # Save content for logging before deleting flat_messages
                flat_messages_content = flat_messages.get("content", [])
                del flat_messages

                # Filter advantages using token mask (only valid response tokens)
                response_advantages = torch.masked_select(
                    flat_advantages, flat_token_mask.bool()
                )

                metrics = {
                    "loss": train_results["loss"].numpy(),
                    "reward": rewards.numpy(),
                    "grad_norm": train_results["grad_norm"].numpy(),
                    "mean_prompt_length": repeated_batch["length"].numpy(),
                    "total_num_tokens": input_lengths.numpy(),
                    # Add masked advantages tracking metrics (only for valid response tokens)
                    "advantages/mean": torch.mean(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                    "advantages/max": torch.max(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                    "advantages/min": torch.min(response_advantages).detach().item()
                    if response_advantages.numel() > 0
                    else 0.0,
                }
                if "moe_metrics" in train_results:
                    metrics.update(
                        {f"moe/{k}": v for k, v in train_results["moe_metrics"].items()}
                    )
                metrics.update(train_results["all_mb_metrics"])
                for k, v in metrics.items():
                    if k in {"probs_ratio_min", "probs_ratio_clamped_min"}:
                        valid_values = [x for x in v if not np.isinf(x)]
                        metrics[k] = (
                            np.min(valid_values).item() if valid_values else -1.0
                        )
                    elif k in {"probs_ratio_max", "probs_ratio_clamped_max"}:
                        valid_values = [x for x in v if not np.isinf(x)]
                        metrics[k] = (
                            np.max(valid_values).item() if valid_values else -1.0
                        )
                    elif k in {
                        "lr",
                        "wd",
                        "reward",
                        "global_valid_seqs",
                        "global_valid_toks",
                        "mean_prompt_length",
                    }:
                        metrics[k] = np.mean(v).item()
                    else:
                        metrics[k] = np.sum(v).item()
                metrics.update(rollout_metrics)
                if generation_logger_metrics is not None:
                    metrics["generation_logger_metrics"] = generation_logger_metrics
                total_valid_tokens += metrics["global_valid_toks"]

                # Always log sequence-level error metrics (useful for deciding threshold)
                metrics.update(seq_logprob_error_metrics)

                # Checkpointing (same as sync version)
                consumed_samples += master_config.grpo["num_prompts_per_step"]
                timeout.mark_iteration()

                should_save_by_step = (
                    is_last_step
                    or (step + 1) % master_config.checkpointing["save_period"] == 0
                )
                # +1 because step is 0-indexed
                # Check if timeout-based checkpointing is enabled in config.
                should_save_by_timeout = timeout.check_save()

                if master_config.checkpointing["enabled"] and (
                    should_save_by_step or should_save_by_timeout
                ):
                    grpo_save_state["current_step"] = step + 1
                    grpo_save_state["total_valid_tokens"] = total_valid_tokens
                    if val_metrics is not None:
                        grpo_save_state["val_reward"] = val_metrics["accuracy"]
                    elif "val_reward" in grpo_save_state:
                        del grpo_save_state["val_reward"]
                    grpo_save_state["consumed_samples"] = consumed_samples

                    full_metric_name = master_config.checkpointing["metric_name"]
                    if full_metric_name is not None:
                        assert full_metric_name.startswith(
                            "train:"
                        ) or full_metric_name.startswith("val:"), (
                            f"metric_name={full_metric_name} must start with 'val:' or 'train:',\n"
                            f'followed by the corresponding name in the "val" or "train" metrics dictionary.'
                            f"  If you are using an old config, please updated checkpointing.metric_name to the new format, "
                            f" e.g. 'val_reward --> 'val:accuracy'"
                        )
                        prefix, metric_name = full_metric_name.split(":", 1)
                        metrics_source = metrics if prefix == "train" else val_metrics
                        if not metrics_source:
                            warnings.warn(
                                f"You asked to save checkpoints based on {metric_name} but no {prefix} metrics were collected. "
                                "This checkpoint will not be saved as top-k.",
                                stacklevel=2,
                            )
                            if full_metric_name in grpo_save_state:
                                del grpo_save_state[full_metric_name]
                        elif metric_name not in metrics_source:
                            raise ValueError(
                                f"Metric {metric_name} not found in {prefix} metrics"
                            )
                        else:
                            grpo_save_state[full_metric_name] = metrics_source[
                                metric_name
                            ]

                    with timer.time("checkpointing"):
                        print(f"Saving checkpoint for step {step + 1}...")
                        checkpoint_path = checkpointer.init_tmp_checkpoint(
                            step + 1, grpo_save_state, master_config
                        )
                        policy.save_checkpoint(
                            weights_path=os.path.join(
                                checkpoint_path, "policy", "weights"
                            ),
                            optimizer_path=os.path.join(
                                checkpoint_path, "policy", "optimizer"
                            )
                            if checkpointer.save_optimizer
                            else None,
                            tokenizer_path=os.path.join(
                                checkpoint_path, "policy", "tokenizer"
                            ),
                            checkpointing_cfg=master_config.checkpointing,
                        )
                        # Get dataloader state from trajectory collector
                        actual_dataloader_state = ray.get(
                            trajectory_collector.get_dataloader_state.remote()
                        )
                        torch.save(
                            actual_dataloader_state,
                            os.path.join(checkpoint_path, "train_dataloader.pt"),
                        )
                        checkpointer.finalize_checkpoint(checkpoint_path)

            # Logging
            # Log training data (match sync GRPO logging payload for parity)
            log_data = {}
            if "agent_ref" in repeated_batch:
                log_data["agent_ref"] = repeated_batch["agent_ref"]
            log_data["content"] = flat_messages_content
            log_data["rewards"] = rewards.tolist()
            if master_config.grpo["use_dynamic_sampling"]:
                # In dynamic sampling, `rewards` corresponds to filtered rewards
                log_data["filtered_rewards"] = rewards.tolist()
                log_data["rewards"] = repeated_batch["total_reward"].tolist()
            log_data["input_lengths"] = input_lengths.tolist()
            log_data["token_ids"] = train_data["input_ids"].tolist()
            log_data["token_loss_mask"] = train_data["token_mask"].tolist()
            log_data["sample_loss_mask"] = train_data["sample_mask"].tolist()
            log_data["advantages"] = train_data["advantages"].tolist()
            log_data["generation_logprobs"] = train_data["generation_logprobs"].tolist()
            log_data["prev_logprobs"] = train_data["prev_logprobs"].tolist()
            logger.log_batched_dict_as_jsonl(
                log_data, f"train_data_step{step + 1}.jsonl"
            )
            del train_data
            del flat_messages_content

            timing_metrics: dict[str, float] = timer.get_timing_metrics(
                reduction_op="sum"
            )

            # Add buffer stats
            buffer_size_current = ray.get(replay_buffer.size.remote())
            metrics["buffer_size"] = buffer_size_current
            metrics["avg_trajectory_age"] = avg_trajectory_age

            if (
                master_config.policy["generation"]
                .get("vllm_cfg", {})
                .get("enable_vllm_metrics_logger", False)
                and master_config.logger["wandb_enabled"]
            ):
                log_generation_metrics_to_wandb(
                    generation_logger_metrics,
                    step + 1,
                    master_config.policy["generation"]["vllm_cfg"][
                        "vllm_metrics_logger_interval"
                    ],
                    logger,
                )

            # Plot ISL/OSL/ISL+OSL histograms to wandb
            if (
                master_config.policy["generation"]
                .get("vllm_cfg", {})
                .get("async_engine", False)
            ):
                for metric_name in metrics.keys():
                    if metric_name.startswith("histogram/"):
                        logger.log_histogram(
                            metrics[metric_name],
                            step + 1,
                            f"generation_metrics/{metric_name}",
                        )

            print("\n📊 Training Results:")
            print(f"  • Loss: {metrics['loss']:.4f}")
            if "draft_loss" in metrics:
                print(f"  • Draft Loss: {metrics['draft_loss']:.4f}")
            print(f"  • Generation KL Error: {metrics['gen_kl_error']:.4f}")
            print(f"  • Avg Reward: {np.mean(rewards.numpy()):.4f}")
            print(f"  • Buffer Size: {buffer_size_current}")
            print(f"  • Avg Trajectory Age: {avg_trajectory_age:.2f} steps")

            print("\n⏱️  Timing:")
            total_time = timing_metrics.get("total_step_time", 0)
            print(f"  • Total step time: {total_time:.2f}s")
            for k, v in sorted(
                timing_metrics.items(), key=lambda item: item[1], reverse=True
            ):
                if k != "total_step_time":
                    percent = (v / total_time * 100) if total_time > 0 else 0
                    print(f"  • {k}: {v:.2f}s ({percent:.1f}%)")

            total_num_gpus = (
                master_config.cluster["num_nodes"]
                * master_config.cluster["gpus_per_node"]
            )
            timing_metrics["valid_tokens_per_sec_per_gpu"] = (
                metrics["global_valid_toks"] / total_time / total_num_gpus
            )
            performance_metrics = print_performance_metrics(
                train_results, metrics, timing_metrics, master_config
            )

            logger.log_metrics(performance_metrics, step + 1, prefix="performance")
            logger.log_metrics(metrics, step + 1, prefix="train")
            logger.log_metrics(timing_metrics, step + 1, prefix="timing/train")

            timer.reset()
            step += 1
            if should_save_by_timeout:
                print("Timeout has been reached, stopping training early", flush=True)
                return
            if step >= master_config.grpo["max_num_steps"]:
                print(
                    "Max number of steps has been reached, stopping training early",
                    flush=True,
                )
                return

    except Exception as e:
        print(f"❌ Error in async loop: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        print("🛑 Stopping trajectory collection...")
        try:
            ray.kill(trajectory_collector)
        except Exception as e:
            print(f"Error stopping trajectory collector: {e}")

        try:
            ray.kill(replay_buffer)
        except Exception as e:
            print(f"Error stopping replay buffer: {e}")

        print("Async GRPO training complete!")
