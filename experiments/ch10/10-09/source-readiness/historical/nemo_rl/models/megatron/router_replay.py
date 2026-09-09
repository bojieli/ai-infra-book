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

from __future__ import annotations

import inspect
import os
from collections.abc import Iterable
from typing import Any, Optional

import torch

from nemo_rl.models.policy import PolicyConfig
from nemo_rl.utils.r3_trace import (
    trace_router_replay_action,
    trace_router_replay_assignment,
)

_ROUTER_REPLAY_VALIDATE_ENV = "NRL_ROUTER_REPLAY_VALIDATE"
_MISSING_ROUTE_SENTINEL = -1
_MISSING_ROUTE_FALLBACK_PATCH_ATTR = "_nrl_missing_route_fallback_patch"


def router_replay_enabled(config: PolicyConfig) -> bool:
    return bool((config.get("router_replay") or {}).get("enabled", False))


def configure_vllm_for_router_replay(config: PolicyConfig) -> None:
    """Apply vLLM settings required for Megatron router replay correctness."""
    if not router_replay_enabled(config):
        return

    generation = config.setdefault("generation", {})
    vllm_kwargs = generation.setdefault("vllm_kwargs", {})
    vllm_kwargs["enable_return_routed_experts"] = True


def validate_router_replay_config(config: PolicyConfig) -> None:
    if not router_replay_enabled(config):
        return

    generation = config.get("generation") or {}
    megatron_cfg = config.get("megatron_cfg") or {}

    if generation.get("backend") != "vllm":
        raise ValueError("router_replay.enabled requires vLLM generation.")
    if not megatron_cfg.get("enabled", False):
        raise ValueError("router_replay.enabled requires the Megatron policy backend.")

    vpp_size = megatron_cfg.get("virtual_pipeline_model_parallel_size")
    if vpp_size not in (None, 1):
        raise ValueError(
            "router_replay.enabled does not support virtual pipeline parallelism yet."
        )
    _install_missing_route_fallback_patch()


def _iter_model_modules(model: Any) -> Iterable[Any]:
    if isinstance(model, (list, tuple)):
        for item in model:
            yield from _iter_model_modules(item)
        return

    modules = getattr(model, "modules", None)
    if callable(modules):
        yield from modules()
    else:
        yield model


def _unwrap_model_config(model: Any) -> Optional[Any]:
    if isinstance(model, (list, tuple)):
        for item in model:
            cfg = _unwrap_model_config(item)
            if cfg is not None:
                return cfg
        return None

    current = model
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        cfg = getattr(current, "config", None)
        if cfg is not None:
            return cfg
        current = getattr(current, "module", None)
    return None


def _global_moe_layer_numbers(model_config: Any) -> list[int]:
    num_layers = int(getattr(model_config, "num_layers"))
    moe_layer_freq = getattr(model_config, "moe_layer_freq", 1)

    if isinstance(moe_layer_freq, int):
        if moe_layer_freq <= 0:
            raise ValueError(f"moe_layer_freq must be positive, got {moe_layer_freq}")
        pattern = [1 if i % moe_layer_freq == 0 else 0 for i in range(num_layers)]
    elif isinstance(moe_layer_freq, list):
        if len(moe_layer_freq) != num_layers:
            raise ValueError(
                f"moe_layer_freq has {len(moe_layer_freq)} entries but num_layers={num_layers}"
            )
        pattern = moe_layer_freq
    else:
        raise ValueError(f"Unsupported moe_layer_freq: {moe_layer_freq!r}")

    return [layer_idx + 1 for layer_idx, is_moe in enumerate(pattern) if is_moe]


def _router_replay_instances_for_model(model: Any) -> list[tuple[Any, int]]:
    instances: list[tuple[Any, int]] = []
    seen: set[int] = set()
    for module in _iter_model_modules(model):
        replay = getattr(module, "router_replay", None)
        layer_number = getattr(module, "layer_number", None)
        if replay is None or layer_number is None:
            continue
        if id(replay) in seen:
            continue
        seen.add(id(replay))
        instances.append((replay, int(layer_number)))
    return instances


def _local_layer_numbers_for_model(model: Any) -> set[int]:
    layer_numbers: set[int] = set()
    for module in _iter_model_modules(model):
        layer_number = getattr(module, "layer_number", None)
        if layer_number is None:
            continue
        layer_numbers.add(int(layer_number))
    return layer_numbers


def _normalize_routed_experts_for_mcore(routed_experts: torch.Tensor) -> torch.Tensor:
    if routed_experts.dim() == 4:
        if routed_experts.shape[0] == 1:
            return routed_experts.squeeze(0)
        return routed_experts.transpose(0, 1).reshape(
            routed_experts.shape[0] * routed_experts.shape[1],
            routed_experts.shape[2],
            routed_experts.shape[3],
        )
    if routed_experts.dim() == 3:
        return routed_experts
    raise ValueError(
        "routed_experts must have shape [1, T, L, K], [B, S, L, K], or [T, L, K]; "
        f"got {tuple(routed_experts.shape)}"
    )


def _payload_indices_for_moe_layers(
    *,
    global_moe_layers: list[int],
    num_payload_layers: int,
    total_num_layers: int,
) -> dict[int, int]:
    if num_payload_layers == len(global_moe_layers):
        return {
            layer_number: payload_idx
            for payload_idx, layer_number in enumerate(global_moe_layers)
        }

    if num_payload_layers == total_num_layers:
        return {layer_number: layer_number - 1 for layer_number in global_moe_layers}

    raise ValueError(
        "routed_experts layer axis does not match a supported payload layout: "
        f"payload={num_payload_layers}, moe_layers={len(global_moe_layers)}, "
        f"total_layers={total_num_layers}. Expected exactly "
        f"{len(global_moe_layers)} layers for compressed MoE-layer layout or "
        f"{total_num_layers} layers for vLLM full-transformer-layer layout."
    )


def _router_replay_validation_enabled() -> bool:
    return os.getenv(_ROUTER_REPLAY_VALIDATE_ENV, "0").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _validate_replay_tensor(
    replay_tensor: torch.Tensor,
    model_config: Any,
    *,
    layer_number: int,
    payload_idx: int,
) -> None:
    if replay_tensor.numel() == 0 or not _router_replay_validation_enabled():
        return

    missing_route_mask = replay_tensor.eq(_MISSING_ROUTE_SENTINEL).all(dim=-1)
    partial_missing_mask = replay_tensor.lt(0).any(dim=-1) & ~missing_route_mask
    if bool(partial_missing_mask.any().item()):
        bad_row = int(partial_missing_mask.nonzero()[0].item())
        bad_sample = replay_tensor[bad_row].detach().cpu().tolist()
        raise ValueError(
            "routed_experts fallback rows must use the all--1 sentinel. "
            f"layer_number={layer_number}, payload_idx={payload_idx}, "
            f"row={bad_row}, sample={bad_sample}, shape={tuple(replay_tensor.shape)}"
        )

    replay_tensor = replay_tensor[~missing_route_mask]
    if replay_tensor.numel() == 0:
        return

    sorted_indices = replay_tensor.sort(dim=-1).values
    duplicate_mask = sorted_indices[..., 1:] == sorted_indices[..., :-1]
    has_duplicate_topk = duplicate_mask.any()
    if bool(has_duplicate_topk.item()):
        duplicate_row = int(duplicate_mask.any(dim=-1).nonzero()[0].item())
        duplicate_sample = replay_tensor[duplicate_row].detach().cpu().tolist()
        raise ValueError(
            "routed_experts contains duplicate expert ids within a token's top-k "
            "selection. Missing or padded routed_experts rows must use a valid "
            "dummy top-k route, not repeated zeros. "
            f"layer_number={layer_number}, payload_idx={payload_idx}, "
            f"row={duplicate_row}, sample={duplicate_sample}, "
            f"shape={tuple(replay_tensor.shape)}"
        )

    num_moe_experts = getattr(model_config, "num_moe_experts", None)
    if num_moe_experts is None:
        return

    min_expert = int(replay_tensor.min().item())
    max_expert = int(replay_tensor.max().item())
    if min_expert < 0 or max_expert >= int(num_moe_experts):
        raise ValueError(
            "routed_experts contains expert ids outside Megatron's expert range: "
            f"min={min_expert}, max={max_expert}, num_moe_experts={num_moe_experts}, "
            f"layer_number={layer_number}, payload_idx={payload_idx}, "
            f"shape={tuple(replay_tensor.shape)}"
        )


def _install_missing_route_fallback_patch() -> None:
    from megatron.core.transformer.moe.router_replay import (
        RouterReplay,
        RouterReplayAction,
    )

    if getattr(RouterReplay.get_replay_topk, _MISSING_ROUTE_FALLBACK_PATCH_ATTR, False):
        return

    original_get_replay_topk = RouterReplay.get_replay_topk
    expected_params = [
        "self",
        "scores",
        "topk",
        "num_groups",
        "group_topk",
        "default_compute_topk",
    ]
    actual_params = list(inspect.signature(original_get_replay_topk).parameters)
    if actual_params != expected_params:
        raise RuntimeError(
            "Unsupported Megatron RouterReplay.get_replay_topk signature for "
            "NeMo RL missing-route fallback patch: "
            f"expected={expected_params}, actual={actual_params}. "
            "Update nemo_rl.models.megatron.router_replay before enabling "
            "policy.router_replay.enabled."
        )

    def wrapped_get_replay_topk(
        replay_instance: Any,
        scores: torch.Tensor,
        topk: int,
        num_groups: Optional[int] = None,
        group_topk: Optional[int] = None,
        default_compute_topk: Optional[Any] = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        action = getattr(replay_instance, "router_replay_action", None)
        if action not in {
            RouterReplayAction.REPLAY_FORWARD,
            RouterReplayAction.REPLAY_BACKWARD,
        }:
            return original_get_replay_topk(
                replay_instance,
                scores,
                topk,
                num_groups,
                group_topk,
                default_compute_topk,
            )

        if action == RouterReplayAction.REPLAY_FORWARD:
            target_topk_idx = getattr(replay_instance, "target_topk_idx", None)
        else:
            replay_backward_list = getattr(replay_instance, "replay_backward_list", [])
            target_topk_idx = replay_backward_list[0] if replay_backward_list else None

        if target_topk_idx is None:
            return original_get_replay_topk(
                replay_instance,
                scores,
                topk,
                num_groups,
                group_topk,
                default_compute_topk,
            )

        target_topk_idx = target_topk_idx.to(scores.device)
        fallback_mask = target_topk_idx.eq(_MISSING_ROUTE_SENTINEL).all(dim=-1)
        if not bool(fallback_mask.any().item()):
            setattr(replay_instance, "_nrl_last_router_replay_fallback_mask", None)
            setattr(replay_instance, "_nrl_last_router_replay_effective_topk_idx", None)
            return original_get_replay_topk(
                replay_instance,
                scores,
                topk,
                num_groups,
                group_topk,
                default_compute_topk,
            )

        if default_compute_topk is None:
            raise RuntimeError(
                "RouterReplay missing-route fallback requires default_compute_topk."
            )

        _, default_indices = default_compute_topk(
            scores,
            topk,
            num_groups=num_groups,
            group_topk=group_topk,
        )
        effective_topk_idx = target_topk_idx.clone()
        effective_topk_idx[fallback_mask] = default_indices[fallback_mask]
        probs = scores.gather(1, effective_topk_idx)

        if action == RouterReplayAction.REPLAY_FORWARD:
            replay_backward_list = getattr(replay_instance, "replay_backward_list", [])
            if replay_backward_list:
                replay_backward_list[-1] = effective_topk_idx.detach()
        else:
            getattr(replay_instance, "replay_backward_list").pop(0)

        setattr(
            replay_instance,
            "_nrl_last_router_replay_fallback_mask",
            fallback_mask.detach(),
        )
        setattr(
            replay_instance,
            "_nrl_last_router_replay_effective_topk_idx",
            effective_topk_idx.detach(),
        )
        return probs, effective_topk_idx

    setattr(wrapped_get_replay_topk, _MISSING_ROUTE_FALLBACK_PATCH_ATTR, True)
    RouterReplay.get_replay_topk = wrapped_get_replay_topk


def _get_tensor_model_parallel_world_size() -> int:
    from megatron.core import parallel_state

    return int(parallel_state.get_tensor_model_parallel_world_size())


def _get_tensor_model_parallel_rank() -> int:
    from megatron.core import parallel_state

    return int(parallel_state.get_tensor_model_parallel_rank())


def _split_for_sequence_parallel(
    model_config: Any, routed_experts: torch.Tensor
) -> torch.Tensor:
    if not getattr(model_config, "sequence_parallel", False):
        return routed_experts

    tp_size = _get_tensor_model_parallel_world_size()
    if tp_size == 1:
        return routed_experts
    if routed_experts.shape[0] % tp_size != 0:
        raise ValueError(
            "routed_experts token axis must be divisible by tensor parallel size "
            "when sequence_parallel is enabled: "
            f"tokens={routed_experts.shape[0]}, tp_size={tp_size}"
        )

    tp_rank = _get_tensor_model_parallel_rank()
    token_chunk = routed_experts.shape[0] // tp_size
    token_start = tp_rank * token_chunk
    token_end = token_start + token_chunk
    return routed_experts[token_start:token_end].contiguous()


def build_router_replay_tensors(
    model: Any,
    routed_experts: torch.Tensor,
) -> list[torch.Tensor]:
    """Build MCore RouterReplay tensors in model-local router order."""
    return [
        replay_tensor
        for _, replay_tensor in build_router_replay_assignments(model, routed_experts)
    ]


def build_router_replay_assignments(
    model: Any,
    routed_experts: torch.Tensor,
) -> list[tuple[Any, torch.Tensor]]:
    """Pair model-owned MCore RouterReplay instances with their replay tensors."""
    local_routed_experts = _normalize_routed_experts_for_mcore(routed_experts)
    if local_routed_experts.dim() != 3:
        raise ValueError(
            "normalized routed_experts must have shape [T, num_moe_layers, topk]"
        )

    model_config = _unwrap_model_config(model)
    if model_config is None:
        raise ValueError("Could not locate Megatron model config for router replay.")

    local_routed_experts = _split_for_sequence_parallel(
        model_config, local_routed_experts
    )
    global_moe_layers = _global_moe_layer_numbers(model_config)
    total_num_layers = int(getattr(model_config, "num_layers"))
    num_payload_layers = local_routed_experts.shape[1]
    moe_layer_to_payload_idx = _payload_indices_for_moe_layers(
        global_moe_layers=global_moe_layers,
        num_payload_layers=num_payload_layers,
        total_num_layers=total_num_layers,
    )
    model_instances = _router_replay_instances_for_model(model)
    if len(model_instances) == 0:
        local_moe_layers = _local_layer_numbers_for_model(model).intersection(
            global_moe_layers
        )
        if not local_moe_layers:
            return []
        raise ValueError(
            "Could not find any model-owned RouterReplay instances for local MoE "
            f"layers {sorted(local_moe_layers)}. Ensure Megatron was initialized "
            "with moe_enable_routing_replay=True."
        )

    replay_assignments = []
    for replay_instance, layer_number in model_instances:
        if layer_number not in moe_layer_to_payload_idx:
            raise ValueError(
                f"Router layer {layer_number} is not present in MoE layer pattern "
                f"{global_moe_layers}."
            )
        payload_idx = moe_layer_to_payload_idx[layer_number]
        replay_tensor = (
            local_routed_experts[:, payload_idx, :].to(dtype=torch.long).contiguous()
        )
        setattr(replay_instance, "_nrl_layer_number", layer_number)
        _validate_replay_tensor(
            replay_tensor,
            model_config,
            layer_number=layer_number,
            payload_idx=payload_idx,
        )
        trace_router_replay_assignment(
            layer_number=layer_number,
            payload_idx=payload_idx,
            replay_tensor=replay_tensor,
        )
        replay_assignments.append(
            (
                replay_instance,
                replay_tensor,
            )
        )

    return replay_assignments


def set_router_replay_forward(model: Any, routed_experts: torch.Tensor) -> None:
    from megatron.core.transformer.moe.router_replay import RouterReplayAction

    _install_missing_route_fallback_patch()
    for replay_instance, replay_tensor in build_router_replay_assignments(
        model, routed_experts
    ):
        replay_instance.set_target_indices(replay_tensor)
        trace_router_replay_action(
            action="replay_forward",
            layer_number=getattr(replay_instance, "_nrl_layer_number", None),
            replay_tensor=replay_tensor,
            replay_backward_list_len=len(
                getattr(replay_instance, "replay_backward_list", [])
            ),
        )
        replay_instance.set_router_replay_action(RouterReplayAction.REPLAY_FORWARD)


def set_router_replay_backward(model: Any) -> None:
    from megatron.core.transformer.moe.router_replay import RouterReplayAction

    for replay_instance, _ in _router_replay_instances_for_model(model):
        replay_backward_list = getattr(replay_instance, "replay_backward_list", [])
        next_replay_tensor = replay_backward_list[0] if replay_backward_list else None
        trace_router_replay_action(
            action="replay_backward",
            layer_number=getattr(replay_instance, "_nrl_layer_number", None),
            replay_tensor=next_replay_tensor,
            replay_backward_list_len=len(replay_backward_list),
        )
        replay_instance.set_router_replay_action(RouterReplayAction.REPLAY_BACKWARD)


def clear_router_replay(model: Optional[Any] = None) -> None:
    from megatron.core.transformer.moe.router_replay import RouterReplay

    if model is None:
        RouterReplay.clear_global_router_replay_action()
        RouterReplay.clear_global_indices()
        return

    for replay_instance, _ in _router_replay_instances_for_model(model):
        replay_instance.clear_router_replay_action()
        replay_instance.clear_indices()


def clear_global_router_replay_instances() -> None:
    from megatron.core.transformer.moe.router_replay import RouterReplay

    RouterReplay.clear_global_router_replay_instances()
