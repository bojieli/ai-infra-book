"""Strict selection and all-attempt costs from archived experiment 3-3.

No model requests, posterior answer extraction, or inferred GPU timing.
"""
import hashlib
import json
from ..paths import PROJECT


def strict_value(text, thinking):
    if thinking:
        if "</think>" not in text:
            return None
        text = text.split("</think>", 1)[1]
    try:
        value = json.loads(text.strip())
    except (ValueError, TypeError):
        return None
    if isinstance(value, dict) and set(value) == {"count"} and type(value["count"]) is int:
        return value["count"]
    return None


def selected_index(values):
    """Majority among valid values, tied by first valid candidate index."""
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    winner = max(valid, key=valid.count)
    return values.index(winner)


def group_cost(row, truth, thinking):
    candidates = []
    for index, attempt in enumerate(row["candidates"]):
        if attempt["index"] != index:
            raise ValueError("Candidate order changed")
        value = strict_value(attempt["text"], thinking)
        if value != attempt["value"]:
            raise ValueError("Archived strict score differs from protocol replay")
        if not (row["start"] <= attempt["start"] <= attempt["end"] <=
                attempt["validation_start"] <= attempt["validation_end"] <=
                row["selection_start"] <= row["scored_at"]):
            raise ValueError("Invalid client interval order")
        candidates.append(dict(
            index=index, input_tokens=len(attempt["input_ids"]),
            returned_output_ids=len(attempt["output_ids"]),
            cached_tokens=attempt["cached_tokens"], finish_reason=attempt["finish_reason"],
            protocol_pass=value is not None, parsed_value=value,
            task_correct=value == truth, client_request_seconds=attempt["end"]-attempt["start"],
            validation_seconds=attempt["validation_end"]-attempt["validation_start"],
        ))
    selected = selected_index([candidate["parsed_value"] for candidate in candidates])
    value = candidates[selected]["parsed_value"] if selected is not None else None
    success = value == truth
    if row["selected"] != value or row["correct"] != success:
        raise ValueError("Archived selection differs from predeclared majority rule")
    return dict(
        trial=row["trial"], task=row["task"], strategy=row["policy"],
        candidates=candidates, selected_candidate_index=selected, success=success,
        input_tokens=sum(c["input_tokens"] for c in candidates),
        returned_output_ids=sum(c["returned_output_ids"] for c in candidates),
        cached_tokens=sum(c["cached_tokens"] for c in candidates),
        client_request_seconds_sum=sum(c["client_request_seconds"] for c in candidates),
        validation_seconds_sum=sum(c["validation_seconds"] for c in candidates),
        selection_and_scoring_seconds=row["scored_at"]-row["selection_start"],
        group_wall_seconds=row["scored_at"]-row["start"],
    )


def calculate():
    root = PROJECT
    sources = json.loads((PROJECT / "configs/strategy-record-cost.lock.json").read_text())
    for source in sources:
        data = (root / source["file"]).read_bytes()
        if len(data) != source["bytes"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("Archived source changed: " + source["file"])
    batches = []
    for batch in dict.fromkeys(source["batch"] for source in sources):
        paths = {source["kind"]: root / source["file"] for source in sources if source["batch"] == batch}
        tasks = json.loads(paths["results/tasks.json"].read_text())
        # Independently recompute ground truth; no archived answer trusted alone.
        for task in tasks["tasks"]:
            ways = {0: 1}
            for value in task["values"]:
                for total, count in list(ways.items()):
                    ways[total + value] = ways.get(total + value, 0) + count
            if ways.get(task["target"], 0) != tasks["answers"][task["id"]]:
                raise ValueError("Task truth mismatch")
        raw = [json.loads(line) for line in paths["results/raw.jsonl"].read_text().splitlines()]
        groups = [group_cost(row, tasks["answers"][row["task"]], not batch.startswith("no-thinking")) for row in raw]
        archived = json.loads(paths["summary.json"].read_text())
        strategies = []
        for strategy in ("serial", "parallel", "adaptive"):
            selected = [group for group in groups if group["strategy"] == strategy]
            attempts = [candidate for group in selected for candidate in group["candidates"]]
            success = sum(group["success"] for group in selected)
            output = sum(group["returned_output_ids"] for group in selected)
            inputs = sum(group["input_tokens"] for group in selected)
            wall = sum(group["group_wall_seconds"] for group in selected)
            record = archived[strategy]
            if (len(selected), len(attempts), success, inputs, output) != (
                record["groups"], record["requests"], record["correct"], record["input_tokens"], record["output_tokens"]):
                raise ValueError("Archived aggregate conservation failed")
            strategies.append(dict(
                strategy=strategy, groups=len(selected), attempts=len(attempts), successes=success,
                protocol_pass_attempts=sum(a["protocol_pass"] for a in attempts),
                truncated_attempts=sum(a["finish_reason"] == "length" for a in attempts),
                input_tokens=inputs, returned_output_ids=output, group_wall_seconds_sum=wall,
                failed_group_output_ids=sum(g["returned_output_ids"] for g in selected if not g["success"]),
                client_request_seconds_sum=sum(g["client_request_seconds_sum"] for g in selected),
                validation_seconds_sum=sum(g["validation_seconds_sum"] for g in selected),
                selection_and_scoring_seconds_sum=sum(g["selection_and_scoring_seconds"] for g in selected),
                output_ids_per_success=output/success if success else None,
                group_wall_seconds_per_success=wall/success if success else None,
                fee=None, gpu_seconds=None, actual_kv_peak_bytes=None,
            ))
        batches.append(dict(batch=batch, groups=groups, strategies=strategies))
    return dict(schema_version=1, calculation="archived-strategy-record-cost", scenario={}, batches=batches, sources=sources,
                summary=dict(batches=len(batches), groups=sum(len(b["groups"]) for b in batches),
                             attempts=sum(s["attempts"] for b in batches for s in b["strategies"]),
                             successes=sum(s["successes"] for b in batches for s in b["strategies"]), new_requests_executed=0),
                scope=["All attempts including failures and truncations are retained; strict predeclared parser and selection are replayed.",
                       "Returned IDs are not automatically useful answer tokens or decode calls; no posterior scoring is substituted.",
                       "Client request intervals overlap under parallel strategy; their sum is not group wall time or GPU device time.",
                       "Validation and selection are already inside group wall time; do not add them again.",
                       "Batches have different generation protocols and resource conditions; no equal-quality speed ranking follows.",
                       "Zero successes leave cost-per-success undefined. Fee rates, actual KV lifetime and GPU time are unrecorded."])


if __name__ == "__main__":
    print(json.dumps(calculate(), ensure_ascii=False, indent=2, allow_nan=False))


def markdown(result):
    lines = ["# 实验3-3全候选严格消耗", "", "| 批次 | 策略 | 候选 | 成功任务 | 截断 | 输入token | 返回ID | 组墙钟秒 |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for batch in result["batches"]:
        for row in batch["strategies"]:
            values = [batch["batch"], row["strategy"], row["attempts"], row["successes"], row["truncated_attempts"], row["input_tokens"], row["returned_output_ids"], row["group_wall_seconds_sum"]]
            lines.append("| " + " | ".join(str(value) for value in values) + " |")
    lines += ["", "## 时间与质量口径", "", *("- " + note for note in result["scope"])]
    for batch in result["batches"]:
        lines += ["", "## " + batch["batch"] + "：逐候选与逐组", "", "```json", json.dumps(batch, ensure_ascii=False, indent=2, allow_nan=False), "```"]
    lines += ["", "## 封存来源", "", *("- " + source["origin"] + "；SHA256 `" + source["sha256"] + "`" for source in result["sources"])]
    return "\n".join(lines) + "\n"
