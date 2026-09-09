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

import contextvars
import hashlib
import json
import os
import socket
import threading
import time
from collections import defaultdict
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, nullcontext
from functools import wraps
from pathlib import Path
from typing import Any, Optional

_TRACE_ENV = "NRL_R3_TRACE"
_TRACE_STEPS_ENV = "NRL_R3_TRACE_STEPS"
_TRACE_SAMPLES_ENV = "NRL_R3_TRACE_SAMPLES"
_TRACE_DIR_ENV = "NRL_R3_TRACE_DIR"
_TRACE_MICROBATCHES_ENV = "NRL_R3_TRACE_MICROBATCHES"
_TRACE_VERIFY_FORWARD_ENV = "NRL_R3_TRACE_VERIFY_FORWARD"

_DEFAULT_TRACE_DIR = "logs/r3_trace"
_DEFAULT_TRACE_STEPS = 1
_DEFAULT_TRACE_SAMPLES = 2
_DEFAULT_TRACE_MICROBATCHES = 2

_write_lock = threading.Lock()
_patch_lock = threading.Lock()
_router_replay_patch_depth = 0
_original_get_replay_topk: Optional[Any] = None
_event_counts: dict[str, int] = defaultdict(int)
_context: contextvars.ContextVar[Optional[dict[str, Any]]] = contextvars.ContextVar(
    "nrl_r3_trace_context",
    default=None,
)


def r3_trace_enabled() -> bool:
    return os.getenv(_TRACE_ENV, "0").lower() in {"1", "true", "yes", "on"}


def r3_trace_verify_forward_enabled() -> bool:
    return r3_trace_enabled() and os.getenv(_TRACE_VERIFY_FORWARD_ENV, "0").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _trace_steps() -> int:
    return max(0, _env_int(_TRACE_STEPS_ENV, _DEFAULT_TRACE_STEPS))


def _trace_samples() -> int:
    return max(0, _env_int(_TRACE_SAMPLES_ENV, _DEFAULT_TRACE_SAMPLES))


def _trace_microbatches() -> int:
    return max(0, _env_int(_TRACE_MICROBATCHES_ENV, _DEFAULT_TRACE_MICROBATCHES))


def _next_count(name: str) -> int:
    _event_counts[name] += 1
    return _event_counts[name]


def _should_trace_step(counter_name: str) -> tuple[bool, int]:
    if not r3_trace_enabled():
        return False, 0
    step = _next_count(counter_name)
    return step <= _trace_steps(), step


def _current_context() -> Optional[dict[str, Any]]:
    ctx = _context.get()
    if ctx and ctx.get("active"):
        return ctx
    return None


def _torch_rank_info() -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        import torch

        if torch.distributed.is_available() and torch.distributed.is_initialized():
            info["rank"] = int(torch.distributed.get_rank())
            info["world_size"] = int(torch.distributed.get_world_size())
    except (ImportError, RuntimeError):
        # Best-effort rank annotation for the (default-off) diagnostic traces:
        # torch may be absent (it is imported lazily so this module loads in
        # torch-free contexts), or the process group may be torn down between
        # the is_initialized() check and get_rank(). Trace writing must never
        # fail over optional metadata, so fall open.
        pass
    return info


def _trace_path() -> Path:
    trace_dir = Path(os.getenv(_TRACE_DIR_ENV, _DEFAULT_TRACE_DIR))
    trace_dir.mkdir(parents=True, exist_ok=True)
    host = socket.gethostname().split(".")[0]
    return trace_dir / f"r3_trace_{host}_pid{os.getpid()}.jsonl"


def _write_record(record: dict[str, Any]) -> None:
    if not r3_trace_enabled():
        return
    payload = {
        "time": time.time(),
        "host": socket.gethostname(),
        "pid": os.getpid(),
        **_torch_rank_info(),
        **record,
    }
    line = json.dumps(payload, sort_keys=True) + "\n"
    with _write_lock:
        with _trace_path().open("a", encoding="utf-8") as f:
            f.write(line)


def _tensor_sha256(tensor: Any) -> str:
    t = tensor.detach()
    if getattr(t, "device", None) is not None and t.device.type != "cpu":
        t = t.cpu()
    t = t.contiguous()
    return hashlib.sha256(t.numpy().tobytes()).hexdigest()


def _tensor_preview(tensor: Any, limit: int = 16) -> list[Any]:
    t = tensor.detach()
    if getattr(t, "device", None) is not None and t.device.type != "cpu":
        t = t.cpu()
    return t.reshape(-1)[:limit].tolist()


def _tensor_record(tensor: Any, *, preview_limit: int = 16) -> dict[str, Any]:
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "sha256": _tensor_sha256(tensor),
        "preview": _tensor_preview(tensor, preview_limit),
    }


def _shape(tensor: Optional[Any]) -> Optional[list[int]]:
    if tensor is None:
        return None
    return list(tensor.shape)


def _valid_sample_record(
    tensor: Any,
    *,
    sample_idx: int,
    valid_length: int,
    preview_limit: int = 16,
) -> dict[str, Any]:
    sample = tensor[sample_idx, :valid_length]
    return {
        "full_shape": list(tensor.shape),
        "valid_shape": list(sample.shape),
        "dtype": str(tensor.dtype),
        "valid_sha256": _tensor_sha256(sample),
        "valid_preview": _tensor_preview(sample, preview_limit),
    }


def _length_at(lengths: Any, sample_idx: int) -> int:
    value = lengths[sample_idx]
    if hasattr(value, "item"):
        return int(value.item())
    return int(value)


def _tensors_equal(lhs: Any, rhs: Any) -> bool:
    import torch

    return bool(torch.equal(lhs, rhs.to(device=lhs.device, dtype=lhs.dtype)))


def _expected_with_missing_route_fallback(
    expected: Any, actual: Any
) -> tuple[Any, int]:
    if expected is None or actual is None:
        return expected, 0
    if not hasattr(expected, "shape") or list(expected.shape) != list(actual.shape):
        return expected, 0

    expected = expected.to(device=actual.device, dtype=actual.dtype)
    fallback_mask = expected.eq(-1).all(dim=-1)
    fallback_rows = int(fallback_mask.sum().item())
    if fallback_rows == 0:
        return expected, 0

    patched = expected.clone()
    patched[fallback_mask] = actual[fallback_mask]
    return patched, fallback_rows


def _router_replay_action_name(action: Any) -> str:
    value = getattr(action, "value", None)
    if value is not None:
        return str(value)
    return str(action)


def _trace_router_replay_topk_use(
    *,
    replay_instance: Any,
    action: Any,
    scores: Any,
    topk: int,
    expected: Optional[Any],
    actual: Any,
    backward_list_len_before: Optional[int],
    backward_list_len_after: Optional[int],
) -> None:
    ctx = _current_context()
    if ctx is None:
        return

    action_name = _router_replay_action_name(action)
    expected_for_match, fallback_rows = _expected_with_missing_route_fallback(
        expected, actual
    )
    matches = expected_for_match is not None and _tensors_equal(
        actual, expected_for_match
    )
    record: dict[str, Any] = {
        "event": "router_replay_forward_verify",
        "stage": ctx["stage"],
        "trace_step": ctx["trace_step"],
        "action": action_name,
        "layer_number": getattr(replay_instance, "_nrl_layer_number", None),
        "topk": int(topk),
        "scores_shape": _shape(scores),
        "actual": _tensor_record(actual),
        "matches_expected": matches,
        "fallback_rows": fallback_rows,
    }
    if backward_list_len_before is not None:
        record["replay_backward_list_len_before"] = int(backward_list_len_before)
    if backward_list_len_after is not None:
        record["replay_backward_list_len_after"] = int(backward_list_len_after)
    if expected is not None:
        record["expected"] = _tensor_record(expected)
    _write_record(record)

    if not matches:
        layer_number = getattr(replay_instance, "_nrl_layer_number", None)
        raise RuntimeError(
            "RouterReplay forward verifier saw replayed top-k indices that do "
            f"not match the installed tensor: stage={ctx['stage']} "
            f"action={action_name} layer={layer_number} "
            f"expected_shape={_shape(expected)} actual_shape={_shape(actual)}"
        )


@contextmanager
def _verify_router_replay_forward_context() -> Iterator[None]:
    global _original_get_replay_topk, _router_replay_patch_depth

    if not r3_trace_verify_forward_enabled():
        yield
        return

    from megatron.core.transformer.moe.router_replay import (
        RouterReplay,
        RouterReplayAction,
    )

    with _patch_lock:
        if _router_replay_patch_depth == 0:
            original_get_replay_topk = RouterReplay.get_replay_topk
            _original_get_replay_topk = original_get_replay_topk

            @wraps(original_get_replay_topk)
            def wrapped_get_replay_topk(
                replay_instance: Any,
                scores: Any,
                topk: int,
                num_groups: Optional[int] = None,
                group_topk: Optional[int] = None,
                default_compute_topk: Optional[Any] = None,
            ) -> tuple[Any, Any]:
                action = getattr(replay_instance, "router_replay_action", None)
                backward_list = getattr(replay_instance, "replay_backward_list", [])
                backward_len_before = len(backward_list)
                expected = None
                if action == RouterReplayAction.REPLAY_FORWARD:
                    expected = getattr(replay_instance, "target_topk_idx", None)
                elif action == RouterReplayAction.REPLAY_BACKWARD:
                    expected = backward_list[0] if backward_list else None

                assert _original_get_replay_topk is not None
                probs, top_indices = _original_get_replay_topk(
                    replay_instance,
                    scores,
                    topk,
                    num_groups,
                    group_topk,
                    default_compute_topk,
                )

                if action in {
                    RouterReplayAction.REPLAY_FORWARD,
                    RouterReplayAction.REPLAY_BACKWARD,
                }:
                    _trace_router_replay_topk_use(
                        replay_instance=replay_instance,
                        action=action,
                        scores=scores,
                        topk=topk,
                        expected=expected,
                        actual=top_indices,
                        backward_list_len_before=backward_len_before,
                        backward_list_len_after=len(
                            getattr(replay_instance, "replay_backward_list", [])
                        ),
                    )
                return probs, top_indices

            RouterReplay.get_replay_topk = wrapped_get_replay_topk
        _router_replay_patch_depth += 1

    try:
        yield
    finally:
        with _patch_lock:
            _router_replay_patch_depth -= 1
            if (
                _router_replay_patch_depth == 0
                and _original_get_replay_topk is not None
            ):
                RouterReplay.get_replay_topk = _original_get_replay_topk
                _original_get_replay_topk = None


def trace_rollout_payload(
    *,
    keys: Sequence[str],
    data: Any,
) -> None:
    active, step = _should_trace_step("rollout_payload")
    if not active or "routed_experts" not in data or "input_lengths" not in data:
        return

    routed_experts = data["routed_experts"]
    input_lengths = data["input_lengths"]
    input_ids = data.get("input_ids")
    sample_count = min(len(keys), int(routed_experts.shape[0]))
    preview_samples = _trace_samples()

    for sample_idx in range(sample_count):
        valid_length = _length_at(input_lengths, sample_idx)
        preview_limit = 16 if sample_idx < preview_samples else 0
        record = {
            "event": "rollout_payload_sample",
            "trace_step": step,
            "sample_idx": sample_idx,
            "key": keys[sample_idx],
            "valid_length": valid_length,
            "routed_experts": _valid_sample_record(
                routed_experts,
                sample_idx=sample_idx,
                valid_length=valid_length,
                preview_limit=preview_limit,
            ),
        }
        if input_ids is not None:
            record["input_ids"] = _valid_sample_record(
                input_ids,
                sample_idx=sample_idx,
                valid_length=valid_length,
                preview_limit=preview_limit,
            )
        _write_record(record)


def trace_tq_fetch_payload(
    *,
    stage: str,
    keys: Sequence[str],
    data: Any,
) -> None:
    active, step = _should_trace_step(f"tq_fetch:{stage}")
    if not active or "routed_experts" not in data or "input_lengths" not in data:
        return

    routed_experts = data["routed_experts"]
    input_lengths = data["input_lengths"]
    input_ids = data.get("input_ids")
    sample_count = min(len(keys), int(routed_experts.shape[0]))
    preview_samples = _trace_samples()

    for sample_idx in range(sample_count):
        valid_length = _length_at(input_lengths, sample_idx)
        preview_limit = 16 if sample_idx < preview_samples else 0
        record = {
            "event": "tq_fetch_sample",
            "stage": stage,
            "trace_step": step,
            "sample_idx": sample_idx,
            "key": keys[sample_idx],
            "valid_length": valid_length,
            "routed_experts": _valid_sample_record(
                routed_experts,
                sample_idx=sample_idx,
                valid_length=valid_length,
                preview_limit=preview_limit,
            ),
        }
        if input_ids is not None:
            record["input_ids"] = _valid_sample_record(
                input_ids,
                sample_idx=sample_idx,
                valid_length=valid_length,
                preview_limit=preview_limit,
            )
        _write_record(record)


@contextmanager
def r3_trace_stage(stage: str) -> Iterator[None]:
    active, step = _should_trace_step(f"stage:{stage}")
    token = _context.set(
        {
            "active": active,
            "stage": stage,
            "trace_step": step,
            "microbatch_counts": defaultdict(int),
        }
    )
    try:
        with _verify_router_replay_forward_context():
            yield
    finally:
        _context.reset(token)


def maybe_r3_trace_stage(stage: str, *, enabled: bool) -> Any:
    if not enabled or not r3_trace_enabled():
        return nullcontext()
    return r3_trace_stage(stage)


def trace_cp_routed_experts(
    *,
    routed_experts_cp_sharded: Any,
    token_identity_cp_sharded: Optional[Any] = None,
    input_ids_cp_sharded: Optional[Any] = None,
    cp_token_identity_verified_count: Optional[int] = None,
    cp_rank: int,
    cp_size: int,
) -> None:
    ctx = _current_context()
    if ctx is None or routed_experts_cp_sharded is None:
        return

    counter = ctx["microbatch_counts"]
    counter["cp_routed_experts"] += 1
    microbatch_idx = int(counter["cp_routed_experts"])
    if microbatch_idx > _trace_microbatches():
        return

    _write_record(
        {
            "event": "cp_routed_experts",
            "stage": ctx["stage"],
            "trace_step": ctx["trace_step"],
            "microbatch_idx": microbatch_idx,
            "cp_rank": cp_rank,
            "cp_size": cp_size,
            "tensor": _tensor_record(routed_experts_cp_sharded),
            "token_identity": (
                _tensor_record(token_identity_cp_sharded)
                if token_identity_cp_sharded is not None
                else None
            ),
            "input_ids": (
                _tensor_record(input_ids_cp_sharded)
                if input_ids_cp_sharded is not None
                else None
            ),
            "cp_token_identity_verified_count": cp_token_identity_verified_count,
        }
    )


def trace_router_replay_assignment(
    *,
    layer_number: int,
    payload_idx: int,
    replay_tensor: Any,
) -> None:
    ctx = _current_context()
    if ctx is None:
        return
    _write_record(
        {
            "event": "router_replay_assignment",
            "stage": ctx["stage"],
            "trace_step": ctx["trace_step"],
            "layer_number": int(layer_number),
            "payload_idx": int(payload_idx),
            "tensor": _tensor_record(replay_tensor),
        }
    )


def trace_router_replay_action(
    *,
    action: str,
    layer_number: Optional[int],
    replay_tensor: Optional[Any] = None,
    replay_backward_list_len: Optional[int] = None,
) -> None:
    ctx = _current_context()
    if ctx is None:
        return
    record: dict[str, Any] = {
        "event": "router_replay_action",
        "stage": ctx["stage"],
        "trace_step": ctx["trace_step"],
        "action": action,
    }
    if layer_number is not None:
        record["layer_number"] = int(layer_number)
    if replay_backward_list_len is not None:
        record["replay_backward_list_len"] = int(replay_backward_list_len)
    if replay_tensor is not None:
        record["tensor"] = _tensor_record(replay_tensor)
    _write_record(record)
