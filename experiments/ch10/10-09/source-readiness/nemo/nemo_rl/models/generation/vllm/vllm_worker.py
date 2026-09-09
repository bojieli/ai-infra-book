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

import copy
import gc
import inspect
import logging
import os
import sys
from typing import Any, Optional, cast

import ray
import torch
from transformers import AutoConfig

from nemo_rl.distributed.batched_data_dict import BatchedDataDict
from nemo_rl.distributed.refit_watchdog import RefitAborted, is_refit_abort
from nemo_rl.distributed.virtual_cluster import (
    DEFAULT_VLLM_PORT_RANGE_LOW,
    DEFAULT_VLLM_PORTS_PER_ENGINE,
)
from nemo_rl.distributed.worker_group_utils import get_nsight_config_if_pattern_matches
from nemo_rl.models.generation.interfaces import (
    ROUTED_EXPERTS_FALLBACK_DTYPE,
    GenerationDatumSpec,
    GenerationOutputSpec,
    get_num_routed_experts,
    resolve_routed_experts_dtype,
    verify_right_padding,
)
from nemo_rl.models.generation.vllm.checkpoint_engine import (
    VllmCheckpointEngineRpcMixin,
)
from nemo_rl.models.generation.vllm.config import (
    VLLM_SPARSE_REFIT_TRANSPORTS,
    VllmConfig,
    resolve_vllm_video_config,
)
from nemo_rl.models.generation.vllm.patches import _apply_vllm_patches
from nemo_rl.models.generation.vllm.utils import (
    format_prompt_for_vllm_generation,
    pad_and_align_routed_expert_indices,
)
from nemo_rl.models.generation.vllm.video_utils import (
    register_torchcodec_vllm_video_loader,
)
from nemo_rl.models.generation.vllm.worker_utils import (
    find_tokenizer_required_architectures,
    resolve_data_parallel_local_rank,
    resolve_distributed_executor_backend,
)
from nemo_rl.models.huggingface.common import ModelFlag
from nemo_rl.models.policy.utils import is_vllm_v1_engine_enabled
from nemo_rl.telemetry.instrumentation import trace_fn
from nemo_rl.telemetry.setup import (
    init_telemetry_worker,
    shutdown_telemetry,
    telemetry_enabled_in_env,
    vllm_native_tracing_requested,
)
from nemo_rl.telemetry.span_groups import RLSpanGroup
from nemo_rl.utils.nsys import wrap_with_nvtx_name
from nemo_rl.utils.nvml import log_gpu_memory_diagnostics
from nemo_rl.weight_sync.checkpoint_engine_config import (
    checkpoint_engine_refit_config,
)

logger = logging.getLogger(__name__)


def _context_capped_max_new_tokens(
    *, configured_max_new_tokens: int, input_length: int, max_model_len: int
) -> int:
    """Cap generation so the training prompt and response fit the context."""
    remaining_context = max_model_len - input_length
    if remaining_context <= 0:
        raise ValueError(
            "Cannot generate from an input whose training length exhausts the "
            f"model context: input_length={input_length}, max_model_len={max_model_len}."
        )
    return min(configured_max_new_tokens, remaining_context)


def _maybe_enable_vllm_native_tracing(llm_kwargs: dict[str, Any]) -> None:
    """Optionally enable vLLM's native OpenTelemetry tracing on the engine.

    Requires both ``telemetry.enabled`` and ``telemetry.vllm_native_tracing``
    (plus an OTLP endpoint). vLLM's OTLP span exporter is gRPC-only, so the
    endpoint must speak OTLP/gRPC (e.g. a collector on ``:4317`` or a
    gRPC-capable backend) — it will not reach an ``http/protobuf`` OTLP
    endpoint. Degrades to a no-op if the installed vLLM lacks these engine args.
    """
    # The master switch is re-checked here because _config_to_env() exports
    # every field before init_telemetry_driver's `enabled` check, so
    # vllm_native_tracing would otherwise survive enabled=false and turn on
    # per-request tracing on exactly the runs that disabled telemetry.
    if not (telemetry_enabled_in_env() and vllm_native_tracing_requested()):
        return
    endpoint = (
        os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    )
    if not endpoint:
        logger.warning(
            "nemo-lens: NEMO_RL_OTEL_VLLM_NATIVE_TRACING is set but no OTLP "
            "endpoint is configured; skipping native vLLM tracing."
        )
        return
    # Narrow: this introspects a third-party surface that moves across vLLM
    # versions, which justifies tolerating a missing attribute or a moved
    # module -- but not swallowing every failure inside a vLLM worker.
    try:
        from vllm.engine.arg_utils import EngineArgs

        supported = set(getattr(EngineArgs, "__dataclass_fields__", {})) | set(
            inspect.signature(EngineArgs.__init__).parameters
        )
    except (ImportError, AttributeError, ValueError, TypeError):
        logger.warning(
            "nemo-lens: could not introspect vLLM EngineArgs; skipping native "
            "vLLM tracing.",
            exc_info=True,
        )
        return
    if "otlp_traces_endpoint" not in supported:
        logger.warning(
            "nemo-lens: installed vLLM does not support 'otlp_traces_endpoint'; "
            "skipping native vLLM tracing."
        )
        return
    llm_kwargs.setdefault("otlp_traces_endpoint", endpoint)
    if "collect_detailed_traces" in supported:
        llm_kwargs.setdefault("collect_detailed_traces", ["all"])
    logger.info("nemo-lens: enabled vLLM native OTLP tracing -> %s", endpoint)


def _resolve_enable_prefix_caching(vllm_cfg: dict[str, Any]) -> bool:
    enable_prefix_caching = vllm_cfg.get("enable_prefix_caching", None)
    if enable_prefix_caching is None:
        enable_prefix_caching = torch.cuda.get_device_capability()[0] >= 8
    return enable_prefix_caching


def _merge_fp8_kwargs(vllm_kwargs: dict[str, Any], fp8_kwargs: dict[str, Any]) -> None:
    """Merge fp8 init kwargs into ``vllm_kwargs`` in place, preserving user overrides.

    ``init_fp8`` returns a nested ``hf_overrides`` (holding ``quantization_config``),
    so a blanket ``vllm_kwargs.update(fp8_kwargs)`` would wholesale-replace any
    user-supplied ``hf_overrides``. We pop ``hf_overrides`` before the shallow
    update and merge it separately so that fp8's ``quantization_config`` is the
    base while user overrides (e.g. ``max_position_embeddings``) survive and take
    precedence. Required FP8 ignore entries are combined with user-provided ignore
    entries so generated safety exclusions cannot be removed. This regression was
    reintroduced once already; see #1413/#2904.
    """
    fp8_kwargs = dict(fp8_kwargs)
    fp8_hf_overrides = fp8_kwargs.pop("hf_overrides", {})
    vllm_kwargs.update(fp8_kwargs)
    existing_hf_overrides = vllm_kwargs.get("hf_overrides") or {}
    merged_hf_overrides = {**fp8_hf_overrides, **existing_hf_overrides}

    fp8_quantization_config = fp8_hf_overrides.get("quantization_config")
    existing_quantization_config = existing_hf_overrides.get("quantization_config")
    if existing_quantization_config is None:
        if fp8_quantization_config is not None:
            merged_hf_overrides["quantization_config"] = fp8_quantization_config
    elif not isinstance(existing_quantization_config, dict):
        raise ValueError("hf_overrides.quantization_config must be a mapping")
    elif isinstance(fp8_quantization_config, dict):
        merged_quantization_config = {
            **fp8_quantization_config,
            **existing_quantization_config,
        }
        for key in ("ignore", "ignored_layers"):
            generated_values = fp8_quantization_config.get(key, [])
            user_values = existing_quantization_config.get(key, [])
            if not isinstance(generated_values, list) or not isinstance(
                user_values, list
            ):
                raise ValueError(f"quantization_config.{key} must be a list")
            if generated_values or user_values:
                merged_quantization_config[key] = list(
                    dict.fromkeys([*generated_values, *user_values])
                )
        merged_hf_overrides["quantization_config"] = merged_quantization_config

    vllm_kwargs["hf_overrides"] = merged_hf_overrides


def _log_effective_quantization_ignore_patterns(
    vllm_cfg: dict[str, Any], vllm_kwargs: dict[str, Any]
) -> None:
    if not vllm_cfg.get("quantization_ignore_patterns"):
        return

    effective_ignore = vllm_kwargs["hf_overrides"]["quantization_config"].get(
        "ignore", []
    )
    print(f"NRL_MXFP8_EFFECTIVE_IGNORE={effective_ignore}")


# Use a base class to share some functions to avoid code duplication.
class BaseVllmGenerationWorker:
    def __repr__(self) -> str:
        """Customizes the actor's prefix in the Ray logs.

        This makes it easier to identify which worker is producing specific log messages.
        """
        return f"{self.__class__.__name__}"

    @staticmethod
    def configure_worker(
        num_gpus: int | float,
        bundle_indices: Optional[tuple[int, list[int]]] = None,
        num_gpus_per_node: Optional[int] = None,
    ) -> tuple[dict[str, Any], dict[str, str], dict[str, Any], dict[str, Any]]:
        """Provides complete worker configuration for vLLM tensor and pipeline parallelism.

        This method configures the worker based on its role in tensor and pipeline parallelism,
        which is determined directly from the bundle_indices parameter.

        Args:
            num_gpus: Original GPU allocation for this worker based on the placement group
            bundle_indices: Tuple of (node_idx, local_bundle_indices) for parallelism (if applicable)
            num_gpus_per_node: Number of GPUs per node in the cluster. Used to map a
                bundle id to a node-local engine slot when deriving VLLM_PORT. When
                None, the original per-engine index is used unchanged.

        Returns:
            tuple with complete worker configuration:
              - 'resources': Resource allocation (e.g., num_gpus)
              - 'env_vars': Environment variables for this worker
              - 'init_kwargs': Parameters to pass to __init__ of the worker
              - 'runtime_env': Additional runtime_env options (e.g., nsight config)
        """
        # Initialize configuration
        resources: dict[str, Any] = {"num_gpus": num_gpus}
        init_kwargs: dict[str, Any] = {}
        env_vars: dict[str, str] = {}
        runtime_env: dict[str, Any] = {}

        local_bundle_indices = None
        if bundle_indices is not None:
            node_idx = bundle_indices[0]
            local_bundle_indices = bundle_indices[1]
            init_kwargs["bundle_indices"] = local_bundle_indices

            """
            compute a unique seed from the node_idx and bundle_indices:
            node_idx = 0, bundle_indices = [0, 1, 2, 3] -> seed = 0*1024 + 0
            node_idx = 0, bundle_indices = [4, 5, 6, 7] -> seed = 0*1024 + 1
            node_idx = 1, bundle_indices = [0, 1, 2, 3] -> seed = 1*1024 + 0
            node_idx = 1, bundle_indices = [4, 5, 6, 7] -> seed = 1*1024 + 1
            """
            # For single worker groups, use a simpler seed calculation
            if len(local_bundle_indices) == 1:
                seed = node_idx * 1024 + local_bundle_indices[0]
            else:
                # For parallel groups, use the original calculation
                bundle_id = local_bundle_indices[0] // len(local_bundle_indices)
                seed = node_idx * 1024 + bundle_id

            init_kwargs["seed"] = seed
            # Need to give each DP group its own vllm cache to address:
            # https://github.com/vllm-project/vllm/issues/18851
            env_vars["VLLM_CACHE_ROOT"] = (
                os.environ.get("VLLM_CACHE_ROOT", os.path.expanduser("~/.cache/vllm"))
                + f"_{seed}"
            )

            # Give each vLLM engine a deterministic starting VLLM_PORT for the
            # TP/DP rendezvous. vLLM's _get_open_port() reads VLLM_PORT and
            # increments it on collision, so spacing engines by
            # DEFAULT_VLLM_PORTS_PER_ENGINE leaves headroom. See the port layout
            # in virtual_cluster.py.
            #
            # The port offset must be a node-local slot. The first entry of
            # local_bundle_indices is a bundle id within the placement group.
            # When a single engine spans more than one node (model parallel size
            # larger than the per-node GPU count), that id can exceed the per-node
            # GPU count, so dividing it by mp_size gives an offset that grows with
            # the number of engines and can push VLLM_PORT into the OS ephemeral
            # range, causing address-in-use errors. When num_gpus_per_node is
            # known, reduce the id modulo the per-node GPU count to get a
            # node-local slot. When it is not provided, use the original index,
            # which is correct for engines that fit within one node.
            mp_size = len(local_bundle_indices)
            if num_gpus_per_node is None:
                engine_index_on_node = (
                    local_bundle_indices[0]
                    if mp_size == 1
                    else local_bundle_indices[0] // mp_size
                )
            elif mp_size > num_gpus_per_node:
                # The engine spans several nodes. Each engine's rank-0 process is
                # on a different node, so every such engine can use node-local
                # slot 0 without colliding.
                #
                # These engines are also the ones exposed to the vLLM 0.25
                # TCPStore/MessageQueue collision within a single engine's window
                # (see _patch_vllm_ray_executor_v2_tcpstore_port in patches.py).
                # That is fixed by offsetting the TCPStore search, deliberately
                # *not* by dropping VLLM_PORT: an unset VLLM_PORT sends vLLM to
                # kernel-ephemeral ports, which is the TOCTOU contention this port
                # layout exists to avoid (#2380, #3103).
                engine_index_on_node = 0
            elif mp_size == 1:
                engine_index_on_node = local_bundle_indices[0] % num_gpus_per_node
            else:
                engine_index_on_node = (
                    local_bundle_indices[0] % num_gpus_per_node
                ) // mp_size
            env_vars["VLLM_PORT"] = str(
                DEFAULT_VLLM_PORT_RANGE_LOW
                + engine_index_on_node * DEFAULT_VLLM_PORTS_PER_ENGINE
            )

        # Check if this worker is part of a parallel group (TP or TP+PP).
        # A worker is part of a parallel group if it's a secondary member (local_bundle_indices is None)
        # or if it's a primary member of a group with multiple workers.
        is_part_of_parallel_workers = (
            local_bundle_indices is not None and len(local_bundle_indices) > 1
        ) or local_bundle_indices is None

        if is_part_of_parallel_workers:
            # Ray + vllm likes to manage GPU assignment internally for parallel groups
            resources["num_gpus"] = 0
            env_vars["RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES"] = "1"
            init_kwargs["fraction_of_gpus"] = num_gpus
        else:
            # TP=1: profile the outer worker directly since it runs the engine in-process.
            # When TP>1, nsight is NOT applied here to avoid interfering with Ray's compiled
            # DAG used by the internal vLLM TP workers. Instead, ray_workers_use_nsight is
            # set in _create_engine_from_config to profile the internal workers.
            runtime_env = get_nsight_config_if_pattern_matches("vllm_generation_worker")

        env_vars["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
        # Skip vllm P2P check and rely on driver to report peer to peer capability.
        env_vars["VLLM_SKIP_P2P_CHECK"] = "1"

        return resources, env_vars, init_kwargs, runtime_env

    def __init__(
        self,
        config: VllmConfig,
        bundle_indices: Optional[list[int]] = None,
        fraction_of_gpus: float = 1.0,
        seed: Optional[int] = None,
        extra_env_vars: Optional[list[str]] = None,
        defer_model_load: bool = False,
    ):
        """Initialize a vLLM worker for distributed inference.

        Args:
            config: Configuration dictionary for the policy
            bundle_indices: List of local bundle indices within a node for parallelism.
                          Only needed for the first worker in each tied worker group.
            fraction_of_gpus: Fraction of GPUs to use for this worker
            seed: Random seed for initialization
            extra_env_vars: Additional environment variable names to forward into
                          the vLLM worker subprocess (e.g. for quantization configs).
            defer_model_load: If True, skip model loading during init. Call
                _load_model() later to perform the heavy model loading. This
                enables overlapping vLLM model loading with NeMo Gym init.
        """
        from nemo_rl.distributed.numa_utils import bind_to_gpu_numa

        # Only bind single-GPU workers to their GPU's NUMA node.
        # For TP>1 workers, the parent process spans multiple NUMA nodes;
        # binding it would incorrectly constrain the EngineCore subprocess
        # (which inherits sched_setaffinity + numa_set_membind via fork).
        # Individual TP workers get their own NUMA binding via collective_rpc
        # in post_init / post_init_async.
        # ray.get_gpu_ids()[0] is this worker's physical GPU index, which keys
        # the affinity file.
        if bundle_indices is not None and len(bundle_indices) == 1:
            bind_to_gpu_numa(int(ray.get_gpu_ids()[0]))

        # OTel providers are process-global, so the driver's setup does not
        # reach this actor. No-op unless telemetry is enabled.
        init_telemetry_worker()

        self._init_config(
            config, bundle_indices, fraction_of_gpus, seed, extra_env_vars
        )
        self._sparse_refit_receiver: Any = None
        if (
            self.is_model_owner
            and self.cfg.get("refit_transport") in VLLM_SPARSE_REFIT_TRANSPORTS
        ):
            # Keep sparse receiver dependencies and threads off other refit paths.
            from nemo_rl.models.generation.vllm.vllm_sparse_refit import (
                VllmSparseRefitReceiver,
            )

            self._sparse_refit_receiver = VllmSparseRefitReceiver(self)

        if not self.is_model_owner:
            return

        if not defer_model_load:
            self._load_model(bundle_indices, seed)

    def _init_config(
        self,
        config: VllmConfig,
        bundle_indices: Optional[list[int]],
        fraction_of_gpus: float,
        seed: Optional[int],
        extra_env_vars: Optional[list[str]],
    ):
        """Lightweight config setup. No model loading, no heavy imports."""
        self.cfg = config
        self.model_name = self.cfg["model_name"]
        # Refined from the model's expert count in _load_model.
        self.routed_experts_dtype = ROUTED_EXPERTS_FALLBACK_DTYPE
        self.tensor_parallel_size = self.cfg["vllm_cfg"]["tensor_parallel_size"]
        self.pipeline_parallel_size = self.cfg["vllm_cfg"]["pipeline_parallel_size"]
        self.expert_parallel_size = self.cfg["vllm_cfg"]["expert_parallel_size"]
        self.enable_expert_parallel = self.expert_parallel_size > 1
        self.gpu_memory_utilization = self.cfg["vllm_cfg"]["gpu_memory_utilization"]
        self.precision = self.cfg["vllm_cfg"]["precision"]
        self.fraction_of_gpus = fraction_of_gpus
        self.is_model_owner = bundle_indices is not None
        self._extra_env_vars = extra_env_vars

        # Store the Python executable being used by this worker
        self.py_executable = sys.executable

        _apply_vllm_patches(
            self.py_executable,
            extra_env_vars=extra_env_vars,
        )

        # Skip model loading if we're not the model owner
        if not self.is_model_owner:
            self.llm = None
            self.tokenizer = None
            self.rank = 0
            self.world_size = 1
            return

        # In Ray+vLLM setup, each worker process considers itself rank 0
        # vLLM handles the parallelism internally through Ray
        self.rank = 0
        self.world_size = 1

    def _refit_with_reload_api_enabled(self) -> bool:
        return bool(self.cfg["vllm_cfg"].get("refit_with_reload_api"))

    @trace_fn(RLSpanGroup.MODEL_INIT, "rl.vllm.load_model")
    def _load_model(self, bundle_indices, seed):
        """Perform the heavy model loading and engine creation.

        Split out from __init__ so it can be deferred (defer_model_load=True)
        and run after ports are reserved, overlapping with NeMo Gym init.
        """
        from vllm.logger import init_logger

        logger = init_logger("vllm_load_model")
        log_gpu_memory_diagnostics(
            label="load_model_start", worker_type="VllmGenerationWorker"
        )

        try:
            import vllm

            self.SamplingParams = vllm.SamplingParams
        except ImportError:
            raise ImportError(
                "vLLM is not installed. Please check that the py_executable in the runtime_env of VllmGenerationWorker "
                "covers the vllm dependency. You may have to update nemo_rl/distributed/ray_actor_environment_registry.py. "
                "This error can also happen if the venv creation was aborted or errored out in the middle. In that case, "
                "please run at least once with the environment variable NRL_FORCE_REBUILD_VENVS=true set to force the rebuild of the environment."
            )
        vllm_kwargs: dict[str, Any] = copy.deepcopy(self.cfg.get("vllm_kwargs", {}))
        checkpoint_engine_config = checkpoint_engine_refit_config(self.cfg)
        if checkpoint_engine_config is not None:
            from nemo_rl.models.generation.vllm.checkpoint_engine import (
                configure_nixl_worker,
            )

            configure_nixl_worker(self.cfg, vllm_kwargs)

        # A speculative_config with num_speculative_tokens == 0 is the supported
        # way to disable speculative decoding (e.g. MTP) from a launch script
        # without restructuring the config. Drop it so vLLM runs without a drafter.
        speculative_config = vllm_kwargs.get("speculative_config")
        if (
            isinstance(speculative_config, dict)
            and speculative_config.get("num_speculative_tokens") == 0
        ):
            vllm_kwargs["speculative_config"] = None
            if not _resolve_enable_prefix_caching(self.cfg["vllm_cfg"]):
                logger.warning(
                    "Speculative decoding is disabled (num_speculative_tokens=0); "
                    "consider enabling prefix caching for better generation performance."
                )

        # Calculate total parallel size (TP * PP)
        model_parallel_size = self.tensor_parallel_size * self.pipeline_parallel_size

        # Special handling for parallel case (either TP or PP or both)
        if model_parallel_size > 1:
            # Configure vLLM for tensor/pipeline parallelism within Ray
            # Reset CUDA_VISIBLE_DEVICES to allow vLLM to manage GPU assignment
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
            os.environ["VLLM_RAY_PER_WORKER_GPUS"] = str(
                self.fraction_of_gpus / model_parallel_size
            )

            # Set bundle indices for parallel workers
            bundle_indices_str = ",".join(map(str, bundle_indices))
            os.environ["VLLM_RAY_BUNDLE_INDICES"] = bundle_indices_str
            print(
                f"VLLM_RAY_BUNDLE_INDICES environment variable set to: {os.environ.get('VLLM_RAY_BUNDLE_INDICES')}"
            )

        executor_backend = resolve_distributed_executor_backend(
            self.tensor_parallel_size,
            self.pipeline_parallel_size,
            self.expert_parallel_size,
        )
        vllm_kwargs["distributed_executor_backend"] = executor_backend

        os.environ["VLLM_USE_V1"] = "1" if is_vllm_v1_engine_enabled() else "0"
        os.environ["VLLM_ALLOW_INSECURE_SERIALIZATION"] = "1"

        # We should use vLLM DP if ep_size > tp_size since EP_SIZE = DP_SIZE * TP_SIZE in vLLM.
        # See details in https://github.com/vllm-project/vllm/blob/main/examples/offline_inference/data_parallel.py
        if self.expert_parallel_size > self.tensor_parallel_size:
            # set vLLM DP rank
            world_size = int(os.environ["VLLM_DP_SIZE"]) * model_parallel_size
            rank = int(os.environ["RANK"]) % world_size
            os.environ["VLLM_DP_RANK"] = str(rank // model_parallel_size)
            os.environ["VLLM_DP_RANK_LOCAL"] = str(
                resolve_data_parallel_local_rank(
                    rank, model_parallel_size, executor_backend
                )
            )
            # set vLLM DP address and port
            leader_rank = int(os.environ["RANK"]) // world_size * world_size
            addr_list = eval(os.environ["AVAILABLE_ADDR_LIST"])
            port_list = eval(os.environ["AVAILABLE_PORT_LIST"])
            os.environ["VLLM_DP_MASTER_IP"] = addr_list[leader_rank]
            os.environ["VLLM_DP_MASTER_PORT"] = str(port_list[leader_rank])

        load_format = self.cfg["vllm_cfg"]["load_format"]
        if ModelFlag.VLLM_LOAD_FORMAT_AUTO.matches(self.model_name):
            load_format = "auto"

        # MTP speculative decoding with load_format="dummy" gets its policy
        # weights via refit, but the MTP draft layer is not covered by refit, so
        # those layers are loaded directly from the checkpoint after engine init
        # (see VllmInternalWorkerExtension.load_mtp_weights_from_disk).
        spec_cfg = vllm_kwargs.get("speculative_config")
        mtp_weights_from_refit = bool(self.cfg.get("_mtp_weights_from_refit"))
        self._mtp_load_from_disk: bool = (
            load_format == "dummy"
            and spec_cfg is not None
            and spec_cfg.get("method") in ("deepseek_mtp", "mtp")
            and not mtp_weights_from_refit
        )

        if (
            len(get_nsight_config_if_pattern_matches("vllm_generation_worker")) > 0
            and vllm_kwargs["distributed_executor_backend"] == "ray"
        ):
            logger.warning(
                "Nsight profiling is enabled for vllm internal TP workers via ray_workers_use_nsight. "
                "The outer VllmGenerationWorker is NOT profiled to avoid interfering with Ray's compiled DAG. "
                "vLLM's default nsight config is overridden with capture-range=cudaProfilerApi so that "
                "profiling is deferred until start_gpu_profiling() is called."
            )
            vllm_kwargs["ray_workers_use_nsight"] = True
            self._patch_vllm_nsight_config()

        # Call init_fp8 when precision is fp8
        # (kv_cache_dtype can be fp8/fp8_e4m3 or auto, validated in init_fp8)
        if self.cfg["vllm_cfg"]["precision"] == "fp8":
            from nemo_rl.models.generation.vllm.quantization.fp8 import init_fp8

            fp8_kwargs = init_fp8(
                self.cfg["vllm_cfg"], self.model_name, model_parallel_size
            )

            # Merge (rather than replace) so fp8's quantization_config coexists
            # with user-supplied hf_overrides, which take precedence.
            _merge_fp8_kwargs(vllm_kwargs, fp8_kwargs)
            # overriden by quant config, however vllm complains if this not passed
            self.precision = "bfloat16"

        if not isinstance(vllm_kwargs.get("hf_overrides"), dict):
            vllm_kwargs["hf_overrides"] = {}

        # Override HF config for gpt-oss models to ensure compatibility with megatron
        # The megatron --> hf export is done in bf16, so we disable quantization
        hf_config = AutoConfig.from_pretrained(self.model_name, trust_remote_code=True)
        self.routed_experts_dtype = resolve_routed_experts_dtype(
            get_num_routed_experts(hf_config)
        )
        if "GptOssForCausalLM" in getattr(hf_config, "architectures", []):
            if "quantization_config" in hf_config:
                assert load_format == "dummy", (
                    "Loading quantized GPT-OSS models is currently only supported with load_format='dummy'."
                )
                # disable quantization
                vllm_kwargs["hf_overrides"]["quantization_config"] = {}
        elif detected_arch := find_tokenizer_required_architectures(
            getattr(hf_config, "architectures", None)
        ):
            if self.cfg["vllm_cfg"]["skip_tokenizer_init"]:
                print(
                    f"Detected {detected_arch} which may crash when skip_tokenizer_init is True. "
                    "NeMo-RL is forcing it to False for this architecture. "
                    "See https://github.com/NVIDIA-NeMo/RL/issues/1681 for more details."
                )
            self.cfg["vllm_cfg"]["skip_tokenizer_init"] = False

        # Mistral 3.5 (Mistral3ForConditionalGeneration) integration.
        if "Mistral3ForConditionalGeneration" in getattr(
            hf_config, "architectures", []
        ):
            # Mistral 3.5 ships FP8 on disk, but NeMo-RL refits bf16 weights via
            # ZMQ (load_format='dummy'). Clear the auto-detected quantization_config
            # so vLLM allocates bf16 buffers instead of building Fp8Config.
            if hasattr(hf_config, "quantization_config"):
                assert load_format == "dummy", (
                    "Loading FP8-quantized Mistral3 in vLLM is only supported "
                    "with load_format='dummy' (NeMo-RL refits bf16 weights via "
                    "ZMQ). Got load_format=%r." % load_format
                )
                # NeMo-RL refits bf16 weights, so we intentionally clear any fp8
                # quantization here -- including the quantization="fp8" that
                # init_fp8 set above when precision == "fp8". Warn so a
                # precision: fp8 Mistral3 config isn't silently downgraded to bf16.
                if self.cfg["vllm_cfg"]["precision"] == "fp8":
                    print(
                        "Mistral3 refits bf16 weights via ZMQ; ignoring "
                        "precision='fp8' and running vLLM generation in bf16."
                    )
                vllm_kwargs["quantization"] = None
                vllm_kwargs["hf_overrides"]["quantization_config"] = {}

            # Force the HF config parser. Auto-detect picks Mistral-native format
            # and remaps architectures to Pixtral, whose weight loader is
            # incompatible with NeMo-RL's HF-format ZMQ refit keys.
            vllm_kwargs["config_format"] = "hf"

            # Text-only runs additionally set generation.vllm_kwargs.language_model_only
            # in the recipe YAML to skip vLLM's multimodal preflight.

        _log_effective_quantization_ignore_patterns(self.cfg["vllm_cfg"], vllm_kwargs)

        llm_kwargs = dict(
            model=self.model_name,
            served_model_name=self.model_name,
            load_format=load_format,
            # Set in nemo_rl.models.generation.configure_generation_config
            skip_tokenizer_init=self.cfg["vllm_cfg"]["skip_tokenizer_init"],
            tensor_parallel_size=self.tensor_parallel_size,
            pipeline_parallel_size=self.pipeline_parallel_size,
            enable_expert_parallel=self.enable_expert_parallel,
            gpu_memory_utilization=self.gpu_memory_utilization,
            enable_prefix_caching=_resolve_enable_prefix_caching(self.cfg["vllm_cfg"]),
            dtype=self.precision,
            seed=seed,
            enforce_eager=self.cfg["vllm_cfg"]["enforce_eager"],
            max_model_len=self.cfg["vllm_cfg"]["max_model_len"],
            trust_remote_code=True,
            worker_extension_cls=(
                "nemo_rl.models.generation.vllm.vllm_backend."
                "VllmInternalWorkerExtensionWithCheckpointEngine"
                if checkpoint_engine_config is not None
                else "nemo_rl.models.generation.vllm.vllm_backend."
                "VllmInternalWorkerExtension"
            ),
            enable_sleep_mode=True,
            # Set disable_log_stats=False so that self.llm.get_metrics() works.
            disable_log_stats=False,
            **vllm_kwargs,
        )

        logprobs_mode = self.cfg["vllm_cfg"].get("logprobs_mode")
        if logprobs_mode is not None:
            llm_kwargs["logprobs_mode"] = logprobs_mode

        video_config = resolve_vllm_video_config(self.cfg)
        if video_config is not None:
            register_torchcodec_vllm_video_loader(
                sampling_style=video_config.sampling_style,
                temporal_patch_size=video_config.temporal_patch_size,
            )

        _maybe_enable_vllm_native_tracing(llm_kwargs)

        self._create_engine(llm_kwargs)
        log_gpu_memory_diagnostics(
            label="after_engine_create", worker_type="VllmGenerationWorker", device_id=0
        )

        # will be initialized in post_init
        # used in update_weights_from_ipc_handles
        self.vllm_device_ids = None
        log_gpu_memory_diagnostics(
            label="load_model_complete", worker_type="VllmGenerationWorker", device_id=0
        )

    def llm(self):
        return self.llm

    def is_alive(self):
        """Check if the worker is alive."""
        return True

    def _merge_stop_strings(self, batch_stop_strings):
        stop_set: set[str] = set()

        if self.cfg.get("stop_strings"):
            stop_set.update(self.cfg["stop_strings"])

        if batch_stop_strings is not None:
            for sample_ss in batch_stop_strings:
                if sample_ss:
                    stop_set.update(sample_ss)

        return list(stop_set) if stop_set else None

    def _build_sampling_params(
        self,
        *,
        greedy: bool,
        stop_strings,
        max_new_tokens: Optional[int] = None,
    ):
        top_k_cfg = self.cfg["top_k"]
        top_k_val = 1 if greedy else (top_k_cfg if top_k_cfg is not None else -1)

        temperature = 0.0 if greedy else self.cfg["temperature"]

        max_tokens = (
            max_new_tokens if max_new_tokens is not None else self.cfg["max_new_tokens"]
        )

        return self.SamplingParams(
            temperature=temperature,
            top_p=self.cfg["top_p"],
            top_k=top_k_val,
            max_tokens=max_tokens,
            logprobs=0,
            stop_token_ids=self.cfg["stop_token_ids"],
            stop=stop_strings,
            include_stop_str_in_output=True,
            bad_words=self.cfg.get("bad_words"),
            ignore_eos=self.cfg.get("ignore_eos", False),
        )

    def start_gpu_profiling(self) -> None:
        """Start GPU profiling."""
        torch.cuda.profiler.start()
        if self.llm is not None:
            self.llm.collective_rpc("start_gpu_profiling", args=tuple())

    def stop_gpu_profiling(self) -> None:
        """Stop GPU profiling."""
        torch.cuda.profiler.stop()
        if self.llm is not None:
            self.llm.collective_rpc("stop_gpu_profiling", args=tuple())

    @staticmethod
    def _spec_decode_max_tokens(
        base_max_tokens: int,
        input_len: int,
        max_model_len: int,
        spec_lookahead: int,
    ) -> int:
        """Clamp max_tokens so speculative decoding never reads past max_model_len.

        The drafter looks `spec_lookahead` tokens ahead, so generation must stop
        at least `spec_lookahead + 1` tokens before the boundary.
        """
        return max(
            1, min(base_max_tokens, max_model_len - input_len - (spec_lookahead + 1))
        )

    @classmethod
    def _request_max_new_tokens(
        cls,
        *,
        configured_max_new_tokens: int,
        input_length: int,
        max_model_len: int,
        cap_to_context: bool,
        spec_lookahead: int,
    ) -> int:
        """Apply context and speculative-decoding limits to one request."""
        max_new_tokens = configured_max_new_tokens
        if cap_to_context:
            max_new_tokens = _context_capped_max_new_tokens(
                configured_max_new_tokens=max_new_tokens,
                input_length=input_length,
                max_model_len=max_model_len,
            )
        if spec_lookahead > 0:
            max_new_tokens = cls._spec_decode_max_tokens(
                max_new_tokens,
                input_length,
                max_model_len,
                spec_lookahead,
            )
        return max_new_tokens

    @staticmethod
    def _patch_vllm_nsight_config() -> None:
        """Override vLLM's nsight config for internal TP workers to use deferred capture.

        vLLM's default _configure_ray_workers_use_nsight applies an always-on nsight
        config (no capture-range, cuda-graph-trace=node) which causes significant
        overhead and hangs Ray's compiled DAG. This patch replaces it with NeMo RL's
        lighter config that uses capture-range=cudaProfilerApi, deferring actual
        tracing until start_gpu_profiling() triggers cudaProfilerStart() on each
        internal worker via collective_rpc.
        """
        from nemo_rl.utils.nsys import NRL_NSYS_PROFILE_STEP_RANGE

        nsight_config = {
            "t": "cuda,cudnn,cublas,nvtx",
            "o": f"'vllm_tp_worker_{NRL_NSYS_PROFILE_STEP_RANGE}_%p'",
            "stop-on-exit": "true",
            "s": "none",
            "capture-range": "cudaProfilerApi",
            "capture-range-end": "repeat",
            "cuda-graph-trace": "node",
        }

        try:
            from vllm.v1.executor.ray_executor import RayDistributedExecutor
        except ImportError:
            from vllm.executor.ray_distributed_executor import (
                RayDistributedExecutor,
            )

        def _patched_configure(self, ray_remote_kwargs):
            runtime_env = ray_remote_kwargs.setdefault("runtime_env", {})
            runtime_env.update({"nsight": nsight_config})
            return ray_remote_kwargs

        RayDistributedExecutor._configure_ray_workers_use_nsight = _patched_configure

    def _get_raw_spec_counters(self) -> dict[str, float | list[float]]:
        """Get speculative decoding metrics from the vLLM engine.

        Collects spec decode counters including number of drafts,
        draft tokens, and accepted tokens for monitoring acceptance rates.

        Returns:
            Dictionary mapping metric names to their values.
            Values may be floats or lists of floats (for per-position metrics).

        Raises:
            AssertionError: If called before vLLM engine is initialized.
        """
        metrics: dict[str, float | list[float]] = {}
        if self.llm is not None:
            if hasattr(self.llm, "get_metrics"):
                vllm_prom_metrics = self.llm.get_metrics()
            else:
                # The AsyncLLM API does not implement get_metrics so we need to call the prometheus API ourselves
                from vllm.v1.metrics.reader import get_metrics_snapshot

                vllm_prom_metrics = get_metrics_snapshot()
            for metric in vllm_prom_metrics:
                if hasattr(metric, "values"):
                    metrics[metric.name] = metric.values
                elif hasattr(metric, "value"):
                    metrics[metric.name] = metric.value
        return metrics

    def report_refit_server_base_url(self) -> str | None:
        receiver = self._sparse_refit_receiver
        return receiver.report_refit_server_base_url() if receiver is not None else None

    def start_zmq_sparse_refit_relay(self) -> str:
        receiver = self._sparse_refit_receiver
        if receiver is None:
            raise RuntimeError("Remote sparse refit is not enabled for this worker.")
        return receiver.start_zmq_sparse_refit_relay()

    def configure_zmq_sparse_refit_relay(self, relay_addresses: list[str]) -> None:
        receiver = self._sparse_refit_receiver
        if receiver is None:
            raise RuntimeError("Remote sparse refit is not enabled for this worker.")
        receiver.configure_zmq_sparse_refit_relay(relay_addresses)

    def stop_zmq_sparse_refit_relay(self) -> None:
        receiver = self._sparse_refit_receiver
        if receiver is not None:
            receiver.stop_zmq_sparse_refit_relay()


class VllmGenerationWorkerImpl(VllmCheckpointEngineRpcMixin, BaseVllmGenerationWorker):
    def _create_engine(self, llm_kwargs: dict[str, Any]) -> None:
        import vllm

        self.llm = vllm.LLM(**llm_kwargs)

    def post_init(self):
        if self.llm is not None:
            self.llm.collective_rpc("bind_numa", args=tuple())
        self.vllm_device_ids = self.report_device_id()
        if self._mtp_load_from_disk:
            self.llm.collective_rpc(
                "load_mtp_weights_from_disk", args=(self.model_name,)
            )
        if self._sparse_refit_receiver is not None:
            self._sparse_refit_receiver.start_sync_server()

    def init_collective(
        self,
        rank_prefix: int,
        ip: str,
        port: int,
        world_size: int,
        train_world_size: int,
    ) -> None:
        self.llm.collective_rpc(
            "init_collective",
            args=(
                rank_prefix,
                ip,
                port,
                world_size,
                train_world_size,
            ),
        )

    @wrap_with_nvtx_name("vllm_genertion_worker/generate")
    def generate(
        self, data: BatchedDataDict[GenerationDatumSpec], greedy: bool = False
    ) -> BatchedDataDict[GenerationOutputSpec]:
        """Generate a batch of data using vLLM generation.

        Args:
            data: BatchedDataDict containing input_ids and input_lengths tensors
            greedy: Whether to use greedy decoding instead of sampling

        Returns:
            BatchedDataDict conforming to GenerationOutputSpec:
                - ``output_ids``: input + generated token IDs with proper padding
                - ``logprobs``: Log probabilities for tokens
                - ``generation_lengths``: Lengths of each response
                - ``unpadded_sequence_lengths``: Lengths of each input + generated sequence
        """
        # Handle empty input case
        if len(data["input_ids"]) == 0:
            # Return empty BatchedDataDict with all required fields
            return BatchedDataDict[GenerationOutputSpec](
                {
                    "output_ids": torch.zeros((0, 0), dtype=torch.long),
                    "logprobs": torch.zeros((0, 0), dtype=torch.float),
                    "generation_lengths": torch.zeros(0, dtype=torch.long),
                    "unpadded_sequence_lengths": torch.zeros(0, dtype=torch.long),
                    "truncated": torch.zeros(0, dtype=torch.bool),
                }
            )

        input_ids = data["input_ids"]
        input_lengths = data["input_lengths"]
        batch_stop_strings: list[list[str]] = data.get("stop_strings", [])
        stop_strings = self._merge_stop_strings(batch_stop_strings)

        # vLLM Eagle3 spec decode hits a CUDA illegal memory access when a
        # request's total length reaches max_model_len (the drafter looks ahead
        # past the boundary). Clamp per-request max_tokens so speculative
        # requests stop short of the boundary by the drafter lookahead.
        spec_cfg = self.cfg.get("vllm_kwargs", {}).get("speculative_config") or {}
        spec_lookahead = int(spec_cfg.get("num_speculative_tokens", 0))
        # verify inputs have correct padding
        verify_right_padding(data, pad_value=self.cfg["_pad_token_id"])

        # Original input length with padding
        padded_input_length = input_ids.size(1)

        assert self.llm is not None, (
            "Attempting to generate with either an uninitialized vLLM or non-model-owner"
        )
        cap_to_context = bool(self.cfg["vllm_cfg"].get("cap_max_tokens_to_context"))
        if cap_to_context or spec_lookahead > 0:
            max_model_len = int(self.cfg["vllm_cfg"]["max_model_len"])
            configured_max_new_tokens = int(self.cfg["max_new_tokens"])
            per_request_max_new_tokens = []
            for input_length in input_lengths.tolist():
                per_request_max_new_tokens.append(
                    self._request_max_new_tokens(
                        configured_max_new_tokens=configured_max_new_tokens,
                        input_length=int(input_length),
                        max_model_len=max_model_len,
                        cap_to_context=cap_to_context,
                        spec_lookahead=spec_lookahead,
                    )
                )

            sampling_params = [
                self._build_sampling_params(
                    greedy=greedy,
                    stop_strings=stop_strings,
                    max_new_tokens=max_new_tokens,
                )
                for max_new_tokens in per_request_max_new_tokens
            ]
        else:
            sampling_params = self._build_sampling_params(
                greedy=greedy,
                stop_strings=stop_strings,
            )

        # Convert inputs to vLLM format and generate outputs.
        prompts = format_prompt_for_vllm_generation(data)
        use_tqdm = self.cfg["vllm_cfg"].get("use_tqdm", True)
        outputs = self.llm.generate(prompts, sampling_params, use_tqdm=use_tqdm)

        # Process the outputs - but preserve the original input padding structure
        output_ids_list = []
        logprobs_list = []
        routed_experts_list = []
        r3_missing_routes = []
        r3_expected_routes = []
        r3_actual_routes = []
        generation_lengths = []
        unpadded_sequence_lengths = []
        truncated_list = []  # Track if response was truncated (hit max_tokens)
        max_length = 0
        return_routed_experts = bool(
            self.cfg.get("vllm_kwargs", {}).get("enable_return_routed_experts", False)
        )
        for output in outputs:
            max_length = max(max_length, len(output.outputs[0].token_ids))

        for i, output in enumerate(outputs):
            # Extract generated tokens
            sequence_length = input_lengths[i]
            generation = output.outputs[0]
            generated_tokens = list(generation.token_ids)

            # Calculate total sequence length (original input length + generated tokens)
            total_length = padded_input_length + max_length

            # Create a new tensor with the right size and fill with padding token
            full_output = torch.full(
                (total_length,), self.cfg["_pad_token_id"], dtype=input_ids.dtype
            )

            # Copy original input (with padding) into the beginning
            full_output[:sequence_length] = input_ids[i][:sequence_length]

            # Add generated tokens after the original input
            full_output[sequence_length : sequence_length + len(generated_tokens)] = (
                torch.tensor(generated_tokens)
            )

            output_ids_list.append(full_output)
            full_logprobs = torch.zeros(total_length, dtype=torch.float32)
            if hasattr(generation, "logprobs") and generation.logprobs:
                try:
                    for idx, (token_id, logprob_dict) in enumerate(
                        zip(generated_tokens, generation.logprobs)
                    ):
                        if logprob_dict:
                            sampled_logprob = logprob_dict.get(token_id)
                            if sampled_logprob is not None:
                                full_logprobs[sequence_length + idx] = (
                                    sampled_logprob.logprob
                                )
                except Exception:
                    import traceback

                    traceback.print_exc()

            logprobs_list.append(full_logprobs)

            response_length = sequence_length + len(generated_tokens)
            full_routed_experts, r3_stats = pad_and_align_routed_expert_indices(
                output,
                generation,
                valid_length=response_length,
                padded_length=total_length,
                device=input_ids.device,
                require_complete_routed_experts=return_routed_experts,
                return_stats=True,
                routed_experts_dtype=self.routed_experts_dtype,
            )
            if return_routed_experts and full_routed_experts is None:
                raise RuntimeError(
                    "vLLM was asked to return routed experts but the generation output "
                    "did not include routed_experts."
                )
            if return_routed_experts:
                r3_missing_routes.append(r3_stats["missing_routes"])
                r3_expected_routes.append(r3_stats["expected_routes"])
                r3_actual_routes.append(r3_stats["actual_routes"])
            if full_routed_experts is not None:
                routed_experts_list.append(full_routed_experts)

            generation_lengths.append(len(generated_tokens))
            unpadded_sequence_lengths.append(response_length)

            # Check if response was truncated (hit max_tokens length limit)
            is_truncated = generation.finish_reason == "length"
            truncated_list.append(is_truncated)

            assert response_length <= self.llm.llm_engine.model_config.max_model_len, (
                f"response_length={response_length} > max_model_len={self.llm.llm_engine.model_config.max_model_len}, which should not happen. Please check this behavior in isolation by running `uv run --extra vllm tools/model_diagnostics/1.max_model_len_respected.py {self.llm.llm_engine.model_config.model}` and raise this issue with the vllm team."
            )

        # Create return data conforming to GenerationOutputSpec
        output_ids = torch.stack(output_ids_list)
        logprobs = torch.stack(logprobs_list)
        if r3_missing_routes and sum(r3_missing_routes) > 0:
            bad_samples = [
                f"{idx}:missing={missing},actual={actual},expected={expected}"
                for idx, (missing, actual, expected) in enumerate(
                    zip(r3_missing_routes, r3_actual_routes, r3_expected_routes)
                )
                if missing > 0
            ][:8]
            logger.warning(
                "R3 router replay fallback: vLLM returned incomplete routed_experts "
                "for %d/%d samples, missing_token_routes=%d. Megatron will use its "
                "own router for those missing token routes. samples=[%s]",
                sum(1 for missing in r3_missing_routes if missing > 0),
                len(r3_missing_routes),
                sum(r3_missing_routes),
                "; ".join(bad_samples),
            )

        return_data = BatchedDataDict[GenerationOutputSpec](
            {
                "output_ids": output_ids,
                "logprobs": logprobs,
                "generation_lengths": torch.tensor(
                    generation_lengths, dtype=torch.long
                ),
                "unpadded_sequence_lengths": torch.tensor(
                    unpadded_sequence_lengths, dtype=torch.long
                ),
                "truncated": torch.tensor(truncated_list, dtype=torch.bool),
            }
        )
        if routed_experts_list:
            return_data["routed_experts"] = torch.stack(routed_experts_list)
        if r3_missing_routes:
            return_data["r3_routed_experts_missing_routes"] = torch.tensor(
                r3_missing_routes, dtype=torch.long
            )
            return_data["r3_routed_experts_expected_routes"] = torch.tensor(
                r3_expected_routes, dtype=torch.long
            )
            return_data["r3_routed_experts_actual_routes"] = torch.tensor(
                r3_actual_routes, dtype=torch.long
            )

        return return_data

    @wrap_with_nvtx_name("vllm_genertion_worker/generate_text")
    def generate_text(
        self, data: BatchedDataDict[GenerationDatumSpec], greedy: bool = False
    ) -> BatchedDataDict[GenerationOutputSpec]:
        """Generate text responses using vLLM generation.

        Args:
            data: BatchedDataDict containing prompts with text strings
            greedy: Whether to use greedy decoding instead of sampling

        Returns:
            BatchedDataDict containing:
                - texts: List of generated text responses
        """
        # Check if async engine is enabled
        if self.cfg["vllm_cfg"]["async_engine"]:
            raise RuntimeError(
                "generate_text cannot be used with async_engine=True. Use generate_text_async instead."
            )

        # Extract stop_strings if provided, else use default from config
        batch_stop_strings: list[list[str] | None] = data.get(
            "stop_strings", [self.cfg.get("stop_strings")] * len(data["prompts"])
        )

        # This function requires all generations have the same stop strings, so we collect all here
        stop_strings: set[str] = set()
        for sample_stop_strings in batch_stop_strings:
            if sample_stop_strings:
                stop_strings.update(sample_stop_strings)

        # Add default stop strings from config
        if self.cfg.get("stop_strings", None):
            stop_strings.update(self.cfg["stop_strings"])

        stop_strings = list(stop_strings) if len(stop_strings) > 0 else None

        # Read generation parameters from config
        top_k = self.cfg["top_k"] if self.cfg["top_k"] is not None else -1
        sampling_params = self.SamplingParams(
            temperature=self.cfg["temperature"] if not greedy else 0,
            top_p=self.cfg["top_p"],
            top_k=top_k if not greedy else 1,
            max_tokens=self.cfg["max_new_tokens"],
            stop_token_ids=self.cfg["stop_token_ids"],
            stop=stop_strings,
            include_stop_str_in_output=True,  # returning stop strings like hf
        )

        # Generate outputs
        assert self.llm is not None, (
            "Attempting to generate with either an uninitialized vLLM or non-model-owner"
        )
        use_tqdm = self.cfg["vllm_cfg"].get("use_tqdm", True)
        outputs = self.llm.generate(data["prompts"], sampling_params, use_tqdm=use_tqdm)
        texts = [output.outputs[0].text for output in outputs]

        # Convert to BatchedDataDict
        return_data: BatchedDataDict[GenerationOutputSpec] = BatchedDataDict(
            {"texts": texts}
        )
        return return_data

    def report_device_id(self) -> list[str]:
        """Report device ID from the vLLM worker."""
        assert self.llm is not None, (
            "Attempting to report device id with either an uninitialized vLLM or non-model-owner"
        )

        if self.cfg["vllm_cfg"]["async_engine"]:
            raise RuntimeError(
                "report_device_id cannot be used with async_engine=True. Use report_device_id_async instead."
            )

        list_of_worker_results = self.llm.collective_rpc(
            "report_device_id", args=tuple()
        )
        return cast(list[str], list_of_worker_results)

    def prepare_refit_info(self, state_dict_info: dict[str, Any]) -> None:
        """Prepare the info for refit."""
        self.llm.collective_rpc("prepare_refit_info", args=(state_dict_info,))

    @wrap_with_nvtx_name("vllm_genertion_worker/update_weights_via_ipc_zmq")
    def update_weights_via_ipc_zmq(self) -> bool:
        """Update weights from IPC handles via ZMQ socket."""
        try:
            assert self.llm is not None, (
                "Attempting to update weights with either an uninitialized vLLM or non-model-owner"
            )

            if self.cfg["vllm_cfg"]["async_engine"]:
                raise RuntimeError(
                    "update_weights_via_ipc_zmq cannot be used with async_engine=True. Use update_weights_via_ipc_zmq_async instead."
                )

            result_or_coro = self.llm.collective_rpc(
                "update_weights_via_ipc_zmq",
                args=tuple(),
            )
            worker_results = cast(list[bool], result_or_coro)

            if not worker_results or not all(worker_results):
                print(
                    f"Error: Worker failed to update weights. Results: {worker_results}"
                )
                return False
            return True
        except Exception as e:
            print(f"Exception during collective_rpc for weight update: {e}")
            import traceback

            traceback.print_exc()
            return False

    @wrap_with_nvtx_name("vllm_genertion_worker/update_weights_from_collective")
    def update_weights_from_collective(
        self, refit_timeout_s: Optional[float] = None
    ) -> bool:
        """Update the model weights from collective communication."""
        try:
            assert self.llm is not None, (
                "Attempting to update weights with either an uninitialized vLLM or non-model-owner"
            )

            if self.cfg["vllm_cfg"]["async_engine"]:
                raise RuntimeError(
                    "update_weights_from_collective can only be used with async_engine=False. Use update_weights_from_collective_async instead."
                )

            result_or_coro = self.llm.collective_rpc(
                "update_weights_from_collective",
                args=(refit_timeout_s, self._refit_with_reload_api_enabled()),
            )
            worker_results = cast(list[bool], result_or_coro)

            if not worker_results or not all(worker_results):
                print(
                    f"Error: Worker failed to update weights. Results: {worker_results}"
                )
                return False
            return True
        except Exception as e:
            # Propagate a deliberate abort instead of folding it into `return False`. It
            # is the controller's signal to rebuild over the survivors and retry; reported
            # as a generic failure it just ends the run, which is the wedge this exists to
            # replace.
            #
            # Matched by message, not by type, and that is not belt-and-braces. vLLM's
            # EngineCore RPC stringifies the worker exception and re-raises it client-side
            # as a bare Exception, so the RefitAborted raised inside the engine arrives
            # here as Exception(str) and a plain `except RefitAborted` never fires. Job
            # 6484412 is the proof: the deadline fired, the abort was named in the log, and
            # the run still wedged at step 4 because this handler did not match.
            if is_refit_abort(e):
                raise RefitAborted(str(e)) from e
            print(f"Exception during collective_rpc for weight update: {e}")
            import traceback

            traceback.print_exc()
            return False

    def init_nccl_reshard_comm_group(
        self,
        rank_prefix: int,
        pp_ips: list[str],
        pp_ports: list[int],
        pp_size: int,
        train_ranks_per_stage: int,
        sub_world_size: int,
    ) -> None:
        """Forward nccl_reshard bulk-path comm group init to vLLM backend workers."""
        self.llm.collective_rpc(
            "init_nccl_reshard_comm_group",
            args=(
                rank_prefix,
                pp_ips,
                pp_ports,
                pp_size,
                train_ranks_per_stage,
                sub_world_size,
            ),
        )

    def prepare_nccl_reshard_refit_info(self, refit_info: dict) -> None:
        """Forward refit info to vLLM backend workers."""
        self.llm.collective_rpc("prepare_nccl_reshard_refit_info", args=(refit_info,))

    def nccl_reshard_refit(self, refit_timeout_s: Optional[float] = None) -> bool:
        """Receive weights from training workers via nccl_reshard (xferdtensor)."""
        try:
            assert self.llm is not None, (
                "Attempting to update weights with either an uninitialized vLLM or non-model-owner"
            )

            result_or_coro = self.llm.collective_rpc(
                "nccl_reshard_refit", args=(refit_timeout_s,)
            )
            worker_result = result_or_coro[0]

            if not worker_result:
                print(
                    f"Error: Worker failed nccl_reshard_refit. Result: {worker_result}"
                )
                return False
            return True
        except Exception as e:
            # Propagate a deliberate abort instead of folding it into `return False`. It
            # is the controller's signal to rebuild over the survivors and retry; reported
            # as a generic failure it just ends the run, which is the wedge this exists to
            # replace.
            #
            # Matched by message, not by type, and that is not belt-and-braces. vLLM's
            # EngineCore RPC stringifies the worker exception and re-raises it client-side
            # as a bare Exception, so the RefitAborted raised inside the engine arrives
            # here as Exception(str) and a plain `except RefitAborted` never fires. Job
            # 6484412 is the proof: the deadline fired, the abort was named in the log, and
            # the run still wedged at step 4 because this handler did not match.
            if is_refit_abort(e):
                raise RefitAborted(str(e)) from e
            print(f"Exception during nccl_reshard_refit: {e}")
            import traceback

            traceback.print_exc()
            return False

    def reset_prefix_cache(self):
        """Reset the prefix cache of vLLM engine."""
        assert self.llm is not None, (
            "Attempting to reset prefix cache with either an uninitialized vLLM or non-model-owner"
        )

        if self.cfg["vllm_cfg"]["async_engine"]:
            raise RuntimeError(
                "reset_prefix_cache can only be used with async_engine=False. Use reset_prefix_cache_async instead."
            )

        self.llm.llm_engine.reset_prefix_cache()
        gc.collect()
        torch.cuda.empty_cache()

    def sleep(self):
        """Put the vLLM engine to sleep."""
        assert self.llm is not None, (
            "Attempting to sleep with either an uninitialized vLLM or non-model-owner"
        )

        if self.cfg["vllm_cfg"]["async_engine"]:
            raise RuntimeError(
                "sleep cannot be used with async_engine=True. Use sleep_async instead."
            )

        # Reset the prefix cache to ensure that prefix cache is not reused after weights are updated
        self.llm.llm_engine.reset_prefix_cache()
        # Clear the renderer's multimodal processor cache (sender side) so it
        # stays in sync with the receiver cache that vLLM clears internally
        # during sleep.  Without this, the sender thinks images are already
        # cached on the receiver and sends data=None, causing an assertion
        # error.  We only clear the renderer (sender) cache here — the
        # receiver and worker-level caches are reset by sleep() internally.
        if hasattr(self.llm, "renderer") and hasattr(
            self.llm.renderer, "clear_mm_cache"
        ):
            self.llm.renderer.clear_mm_cache()
        self.llm.sleep(level=1)

        gc.collect()
        torch.cuda.empty_cache()

    def wake_up(self, **kwargs):
        """Wake up the vLLM engine."""
        assert self.llm is not None, (
            "Attempting to wake up with either an uninitialized vLLM or non-model-owner"
        )

        if self.cfg["vllm_cfg"]["async_engine"]:
            raise RuntimeError(
                "wake_up cannot be used with async_engine=True. Use wake_up_async instead."
            )

        tags = kwargs.get("tags")

        wake_up_args = {}
        if tags is not None:
            wake_up_args["tags"] = tags

        self.llm.wake_up(**wake_up_args)

    def shutdown(self) -> bool:
        """Clean up vLLM resources."""
        try:
            if self._sparse_refit_receiver is not None:
                self._sparse_refit_receiver.shutdown()

            if self.llm is not None:
                # Clean up extension resources (e.g., ZMQ sockets)
                self.llm.collective_rpc("cleanup", args=tuple())

                # Explicitly delete the engine. This may trigger its __del__ method.
                del self.llm

            self.llm = None
            self.tokenizer = None

            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache()

            return True
        except Exception as e:
            print(f"Error during vLLM shutdown: {e}")
            return False
        finally:
            # Flush buffered spans/metrics before the actor goes away.
            shutdown_telemetry()


@ray.remote(
    runtime_env={**get_nsight_config_if_pattern_matches("vllm_generation_worker")}
)  # pragma: no cover
class VllmGenerationWorker(VllmGenerationWorkerImpl):
    pass
