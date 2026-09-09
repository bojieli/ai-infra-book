#!/usr/bin/env python3
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

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

FETCH_STAGE_TO_REPLAY_STAGE = {
    "prev_lp": "prev-logprob",
    "train": "train",
}
REQUIRED_FETCH_STAGES = ("prev_lp", "train")
REQUIRED_REPLAY_STAGES = ("prev-logprob", "train")


def _iter_records(trace_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(trace_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
                record["_trace_file"] = str(path)
                record["_trace_line"] = line_no
                records.append(record)
    return records


def _hashes(record: dict[str, Any]) -> tuple[str, str]:
    input_hash = record.get("input_ids", {}).get("valid_sha256", "")
    routed_hash = record.get("routed_experts", {}).get("valid_sha256", "")
    return input_hash, routed_hash


def _failures_for_fetch_matches(
    producer_by_key: dict[str, dict[str, Any]],
    fetch_by_stage_key: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[str]:
    failures = []
    for key, producer in producer_by_key.items():
        producer_input_hash, producer_routed_hash = _hashes(producer)
        for stage in REQUIRED_FETCH_STAGES:
            fetch_records = fetch_by_stage_key.get((stage, key), [])
            if not fetch_records:
                failures.append(f"missing TQ fetch record for stage={stage} key={key}")
                continue
            for fetch_record in fetch_records:
                fetch_input_hash, fetch_routed_hash = _hashes(fetch_record)
                if fetch_input_hash and producer_input_hash != fetch_input_hash:
                    failures.append(
                        "input_ids hash mismatch "
                        f"stage={stage} key={key} rank={fetch_record.get('rank')}: "
                        f"producer={producer_input_hash} fetch={fetch_input_hash}"
                    )
                if producer_routed_hash != fetch_routed_hash:
                    failures.append(
                        "routed_experts hash mismatch "
                        f"stage={stage} key={key} rank={fetch_record.get('rank')}: "
                        f"producer={producer_routed_hash} fetch={fetch_routed_hash}"
                    )
    return failures


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    events = Counter(record.get("event", "<missing>") for record in records)
    producer_by_key: dict[str, dict[str, Any]] = {}
    fetch_by_stage_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    replay_assignments_by_stage = Counter()
    replay_actions_by_stage_action = Counter()
    replay_forward_verify_by_stage_action = Counter()
    cp_identity_verified_counts = []
    ranks_by_event: dict[str, set[int]] = defaultdict(set)

    for record in records:
        event = record.get("event")
        rank = record.get("rank")
        if isinstance(rank, int):
            ranks_by_event[event].add(rank)
        if event == "rollout_payload_sample":
            key = record["key"]
            producer_by_key.setdefault(key, record)
        elif event == "tq_fetch_sample":
            fetch_by_stage_key[(record["stage"], record["key"])].append(record)
        elif event == "router_replay_assignment":
            replay_assignments_by_stage[record["stage"]] += 1
        elif event == "router_replay_action":
            replay_actions_by_stage_action[(record["stage"], record["action"])] += 1
        elif event == "router_replay_forward_verify":
            replay_forward_verify_by_stage_action[
                (record["stage"], record["action"])
            ] += 1
        elif event == "cp_routed_experts":
            verified_count = record.get("cp_token_identity_verified_count")
            if verified_count is not None:
                cp_identity_verified_counts.append(int(verified_count))

    return {
        "events": events,
        "producer_by_key": producer_by_key,
        "fetch_by_stage_key": fetch_by_stage_key,
        "replay_assignments_by_stage": replay_assignments_by_stage,
        "replay_actions_by_stage_action": replay_actions_by_stage_action,
        "replay_forward_verify_by_stage_action": replay_forward_verify_by_stage_action,
        "cp_identity_verified_counts": cp_identity_verified_counts,
        "ranks_by_event": ranks_by_event,
    }


def check_trace(
    trace_dir: Path,
    *,
    require_forward_verify: bool = False,
    require_cp_identity: bool = False,
) -> int:
    records = _iter_records(trace_dir)
    summary = _summarize(records)
    failures: list[str] = []

    producer_by_key = summary["producer_by_key"]
    if not producer_by_key:
        failures.append("no rollout_payload_sample records found")

    failures.extend(
        _failures_for_fetch_matches(
            producer_by_key,
            summary["fetch_by_stage_key"],
        )
    )

    replay_assignments_by_stage = summary["replay_assignments_by_stage"]
    for stage in REQUIRED_REPLAY_STAGES:
        if replay_assignments_by_stage[stage] == 0:
            failures.append(f"no router_replay_assignment records for stage={stage}")

    replay_actions_by_stage_action = summary["replay_actions_by_stage_action"]
    for stage in REQUIRED_REPLAY_STAGES:
        if replay_actions_by_stage_action[(stage, "replay_forward")] == 0:
            failures.append(f"no replay_forward action records for stage={stage}")
    if replay_actions_by_stage_action[("train", "replay_backward")] == 0:
        failures.append("no replay_backward action records for stage=train")

    replay_forward_verify_records = [
        record
        for record in records
        if record.get("event") == "router_replay_forward_verify"
    ]
    if require_forward_verify and not replay_forward_verify_records:
        failures.append("no router_replay_forward_verify records found")
    for record in replay_forward_verify_records:
        if not record.get("matches_expected"):
            failures.append(
                "router replay forward verifier mismatch "
                f"stage={record.get('stage')} action={record.get('action')} "
                f"layer={record.get('layer_number')} rank={record.get('rank')}"
            )

    cp_identity_verified_counts = summary["cp_identity_verified_counts"]
    if require_cp_identity and not cp_identity_verified_counts:
        failures.append("no CP token-identity verification records found")

    print(f"Trace dir: {trace_dir}")
    print(f"Records: {len(records)}")
    print("Events:")
    for event, count in sorted(summary["events"].items()):
        ranks = sorted(summary["ranks_by_event"].get(event, set()))
        rank_text = (
            f" ranks={ranks[:8]}{'...' if len(ranks) > 8 else ''}" if ranks else ""
        )
        print(f"  {event}: {count}{rank_text}")
    print("Producer keys:")
    for key, record in sorted(producer_by_key.items()):
        print(
            "  "
            f"{key}: len={record.get('valid_length')} "
            f"routed={record['routed_experts']['valid_sha256'][:12]}"
        )
    print("Replay assignments:")
    for stage, count in sorted(replay_assignments_by_stage.items()):
        print(f"  {stage}: {count}")
    print("Replay actions:")
    for (stage, action), count in sorted(replay_actions_by_stage_action.items()):
        print(f"  {stage}/{action}: {count}")
    replay_forward_verify_by_stage_action = summary[
        "replay_forward_verify_by_stage_action"
    ]
    if replay_forward_verify_by_stage_action:
        print("RouterReplay forward verifier:")
        for (stage, action), count in sorted(
            replay_forward_verify_by_stage_action.items()
        ):
            print(f"  {stage}/{action}: {count}")
    if cp_identity_verified_counts:
        print(
            "CP token identity verifier: "
            f"{len(cp_identity_verified_counts)} records, "
            f"{sum(cp_identity_verified_counts)} checked token rows"
        )

    if failures:
        print("\nFAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nPASS: producer routed_experts matched TQ fetches, and replay was set.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an env-gated NeMo-RL R3 route trace."
    )
    parser.add_argument(
        "trace_dir", type=Path, help="Directory containing r3_trace_*.jsonl"
    )
    parser.add_argument(
        "--require-forward-verify",
        action="store_true",
        help="Require RouterReplay.get_replay_topk verifier records.",
    )
    parser.add_argument(
        "--require-cp-identity",
        action="store_true",
        help="Require CP token identity verifier records.",
    )
    args = parser.parse_args()
    if not args.trace_dir.is_dir():
        print(f"trace_dir is not a directory: {args.trace_dir}", file=sys.stderr)
        return 2
    return check_trace(
        args.trace_dir,
        require_forward_verify=args.require_forward_verify,
        require_cp_identity=args.require_cp_identity,
    )


if __name__ == "__main__":
    raise SystemExit(main())
