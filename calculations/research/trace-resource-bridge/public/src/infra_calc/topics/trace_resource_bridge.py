"""Sealed four-call Chat lengths joined to Qwen8 logical operator accounts."""

import hashlib
import json
from pathlib import Path

from infra_calc.paths import PROJECT
from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.sources import model_config
from infra_calc.topics import request_model_comparison as request_math

SOURCE_ROOT = PROJECT / "sources/trace-resource-bridge"


def evidence():
    rows = json.loads((SOURCE_ROOT / "sources.lock.json").read_text())
    for row in rows:
        data = (SOURCE_ROOT / row["file"]).read_bytes()
        if (
            len(data) != row["bytes"]
            or hashlib.sha256(data).hexdigest() != row["sha256"]
        ):
            raise ValueError("Sealed trace source mismatch: " + row["file"])
    return rows


def logical_call(prefix, new, outputs=None):
    """Declared serial generation, last-position head, no final emitted-token append."""
    prefill = qwen3.calculate(
        "qwen3-8b", Scenario(batch=1, tokens=new, history=prefix, output_head="last")
    )
    row = dict(
        request_math.base_row(prefill),
        known_interfaces=request_math.qwen_interfaces(prefill),
    )
    result = dict(
        prefill=dict(
            logical_forward_calls=1,
            totals=request_math.add_rows([row]),
            source_ledger=prefill,
            state_after_bytes=prefill["summary"]["kv_resident_after_bytes"],
        ),
        decode=None,
        complete_logical_totals=None,
        final_state_bytes=None,
    )
    if outputs is not None:
        if type(outputs) is not int or outputs < 1:
            raise ValueError("Serial policy requires at least one sampled output step")
        history = prefix + new
        if history + outputs - 1 > model_config("qwen3-8b")["max_position_embeddings"]:
            raise ValueError("Serial policy exceeds model context")
        if outputs == 1:
            decode = dict(
                calls=0,
                rows=[],
                totals=request_math.add_rows([]),
                final_state_resident_bytes=result["prefill"]["state_after_bytes"],
            )
            combined = request_math.add_rows([row])
        else:
            decode = request_math.linear_decode(
                "qwen3-8b", 1, history, outputs - 1, "expanded", "balanced"
            )
            combined = request_math.add_rows([row] + decode["rows"])
        result.update(
            decode=decode,
            complete_logical_totals=combined,
            final_state_bytes=decode["final_state_resident_bytes"],
        )
    return result


def calculate(generation_policy="unknown_steps"):
    if generation_policy not in ("unknown_steps", "returned_ids_serial_policy"):
        raise ValueError("Unknown generation policy")
    sources = evidence()
    prompts = json.loads((SOURCE_ROOT / "sources/chat/prompts.json").read_text())
    captures = [
        json.loads(line)
        for line in (SOURCE_ROOT / "sources/chat/capture.jsonl")
        .read_text()
        .splitlines()
    ]
    profiles = json.loads((SOURCE_ROOT / "summary.json").read_text())
    profiles = {
        row["request"]: row
        for row in profiles["requests"]
        if row["group"] == "chat_capture"
    }
    commands = json.loads((SOURCE_ROOT / "sources/chat/execution.json").read_text())[
        "commands"
    ]
    servers = [cmd for cmd in commands if "sglang.launch_server" in cmd]
    if len(prompts) != 4 or len(captures) != 4 or len(servers) != 2:
        raise ValueError("Unexpected sealed Chat scope")
    for cmd in servers:
        if (
            "b968826d9c46dd6066d109eabc6255188de91218"
            not in cmd[cmd.index("--model-path") + 1]
            or cmd[cmd.index("--dtype") + 1] != "bfloat16"
        ):
            raise ValueError("Changed captured model identity")
    received, finished = {}, set()
    for path in (SOURCE_ROOT / "sources/chat").glob("worker*-requests/*.log"):
        for line in path.read_text().splitlines():
            if "{" not in line:
                continue
            event = json.loads(line[line.index("{") :])
            rid = event.get("rid", "")
            if event.get("event") == "request.received":
                received[rid] = path.parent.name
            if event.get("event") == "request.finished":
                finished.add(rid)
    calls = []
    for i, prompt in enumerate(prompts):
        if captures[i]["prompt"] != prompt or prompt["id"] != i:
            raise ValueError("Capture identity mismatch")
        response = prompt["response"]
        meta = response["meta_info"]
        profile = profiles[i]
        n = len(prompt["input_ids"])
        cached = meta["cached_tokens"]
        returned = len(response["output_ids"])
        if (
            n != meta["prompt_tokens"]
            or returned != meta["completion_tokens"]
            or not 0 <= cached < n
        ):
            raise ValueError("Recorded token counters inconsistent")
        if (
            meta["id"] not in received
            or meta["id"] not in finished
            or received[meta["id"]] != profile["worker"]
        ):
            raise ValueError("Missing native application-call identity")
        if (n, cached, returned) != (
            profile["input_tokens"],
            profile["cached_tokens"],
            profile["output_id_tokens"],
        ):
            raise ValueError("Derived profile differs from raw source")
        if response["output_ids"][-1] != 151645 or meta["finish_reason"] != {
            "type": "stop",
            "matched": 151645,
        }:
            raise ValueError("Changed sealed EOS boundary")
        outputs = (
            returned if generation_policy == "returned_ids_serial_policy" else None
        )
        work = logical_call(cached, n - cached, outputs)
        calls.append(
            dict(
                request=i,
                application_request_id=meta["id"],
                recorded=dict(
                    input_tokens=n,
                    cached_tokens=cached,
                    returned_id_tokens=returned,
                    engine_completion_tokens=meta["completion_tokens"],
                    output_parts=profile["output_parts"],
                    finish_reason=meta["finish_reason"],
                    worker=profile["worker"],
                    application_wall_seconds=prompt["end_s"] - prompt["start_s"],
                    engine_e2e_seconds=meta["e2e_latency"],
                    tool_wait_seconds=profile["tool_s"],
                    previous_same_worker_completion_gap_seconds=profile[
                        "previous_same_worker_completion_gap_s"
                    ],
                ),
                mapping=dict(
                    prefix_tokens=cached,
                    new_tokens=n - cached,
                    batch=1,
                    output_head="last",
                    sampled_steps=outputs,
                    decode_forward_calls=None if outputs is None else outputs - 1,
                    observed_model_forward_calls=None,
                ),
                resources=work,
            )
        )
    prefill_total = request_math.add_rows(
        [call["resources"]["prefill"]["totals"] for call in calls]
    )
    full = None
    if generation_policy == "returned_ids_serial_policy":
        full = request_math.add_rows(
            [call["resources"]["complete_logical_totals"] for call in calls]
        )
    return dict(
        schema="trace-resource-bridge-v1",
        scenario=dict(generation_policy=generation_policy),
        trace_sources=sources,
        model_sources=calls[0]["resources"]["prefill"]["source_ledger"]["sources"],
        calls=calls,
        summary=dict(
            recorded_application_calls=len(calls),
            recorded_input_tokens=sum(row["recorded"]["input_tokens"] for row in calls),
            recorded_cached_tokens=sum(
                row["recorded"]["cached_tokens"] for row in calls
            ),
            recorded_returned_ids=sum(
                row["recorded"]["returned_id_tokens"] for row in calls
            ),
            logical_prefill_totals=prefill_total,
            conditional_complete_logical_totals=full,
            observed_model_forward_calls=None,
            conditional_serial_forward_calls=(
                sum(row["mapping"]["sampled_steps"] for row in calls)
                if full is not None
                else None
            ),
            recorded_application_wall_sum_seconds=sum(
                row["recorded"]["application_wall_seconds"] for row in calls
            ),
            tool_wait_sum_seconds=None,
            simultaneous_kv_peak_bytes=None,
            actual_hbm_bytes=None,
            actual_gpu_runtime_seconds=None,
        ),
        scope=[
            "Four original sealed Chat captures only. No routing replay is a new natural request, and no model execution occurred during this calculation.",
            "S is recorded cached-token count interpreted as a logical retained prefix, P=N-S. This does not prove KV page identity, actual prefill chunks or backend matrix scheduling. Original model snapshot and BF16 arguments are checked.",
            "Returned IDs and completion counters include EOS. unknown_steps preserves sampled/model-step counts as null. returned_ids_serial_policy explicitly assumes one serial sampled step per returned ID, G outputs from one logical prefill and G-1 single-token decodes.",
            "Last-position generation head is explicit in every forward. The final emitted ID has no additional forward/KV append. EOS is not subtracted from sampled steps in the conditional policy.",
            "Operator interfaces and scalar/special work retain public Qwen8 logical assumptions, not measured HBM or instruction counts. State is per-call endpoint, not summed into a simultaneous residency peak.",
            "Recorded request and engine walls remain separate from resources and tool nulls. Completion-to-send gaps are not per-block reuse distance or human think time. No throughput or GPU latency is derived.",
            "To reconstruct observed model calls, log admitted prefix/pages, each scheduled forward input, prefill chunks, sampled/accepted/retracted IDs, speculative/beam mode, logits rows, final-ID processing, and KV lifetime. The archived application records alone do not provide that trace.",
        ],
    )


def markdown(result):
    return (
        "# Sealed Chat trace to Qwen8 resources\n\nActual recorded lengths; explicitly conditional model-step mapping.\n\n```json\n"
        + json.dumps(result, indent=2, allow_nan=False)
        + "\n```\n"
    )
