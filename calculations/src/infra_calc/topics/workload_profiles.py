"""Offline distributions from the sealed 02-08 request analysis, without new runs."""
import hashlib
import json
import statistics

from ..paths import PROJECT
from .request_trace import percentile95


def distribution(values):
    """Nearest-rank empirical p95; no interpolation or population-tail claim."""
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None,
                "p95": None, "max": None}
    return {"count": len(values), "min": min(values),
            "median": statistics.median(values), "mean": statistics.mean(values),
            "p95": percentile95(values), "max": max(values)}


def calculate():
    sources = json.loads((PROJECT / "configs/workload-profiles.lock.json").read_text())
    for source in sources:
        data = (PROJECT / source["file"]).read_bytes()
        if len(data) != source["bytes"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("Workload profile source changed: " + source["file"])
    recorded = json.loads((PROJECT / "sources/workload-profiles/summary.json").read_text())
    requests = recorded["requests"]
    metrics = {"input_tokens": "tokens", "output_id_tokens": "returned token IDs",
               "cached_tokens": "tokens", "previous_same_worker_completion_gap_s": "seconds",
               "model_s": "seconds", "tool_s": "seconds"}
    groups = []
    for name in dict.fromkeys(row["group"] for row in requests):
        selected = [row for row in requests if row["group"] == name]
        rows = []
        for metric, unit in metrics.items():
            values = [row[metric] for row in selected if row[metric] is not None]
            rows.append({"metric": metric, "unit": unit, **distribution(values),
                         "missing": len(selected) - len(values)})
        groups.append({"group": name, "requests": len(selected), "distributions": rows})
    return {"schema_version": 1, "calculation": "recorded-workload-profiles",
            "scenario": {"experiment": "02-08", "percentile": "nearest-rank ceil(0.95*n)"},
            "sources": sources, "profile_groups": groups,
            "summary": {"groups": len(groups), "requests": len(requests), "new_requests_executed": 0},
            "assumptions": [
                "Rows come from the hash-locked derived analysis of the archived 02-08 captures; no new model execution or timing measurement.",
                "p95 is sorted_values[ceil(0.95*n)-1]; for at most 19 observations it equals the maximum. Empty metrics retain null, not zero.",
                "Returned output IDs include EOS when recorded. These counts are not silently converted into decode calls or useful answer tokens.",
                "The completion-to-next-send gap includes controller/tool behavior; it is not human think time, exact block reuse distance or KV residency.",
                "Recorded model/tool seconds describe these captures only; they are not GPU predictions or throughput comparisons across groups."]}


def markdown(result):
    lines = ["# 封存请求画像与 p95", "", "p95 使用 nearest-rank；空指标保留 null，小样本不能代表总体尾部。", ""]
    for group in result["profile_groups"]:
        lines.extend(["## " + group["group"], "", "| 指标 | 单位 | 样本/缺失 | min | median | mean | p95 | max |",
                      "| --- | --- | --- | --- | --- | --- | --- | --- |"])
        for row in group["distributions"]:
            values = " | ".join(str(row[key]) for key in ("min", "median", "mean", "p95", "max"))
            lines.append(f"| {row['metric']} | {row['unit']} | {row['count']}/{row['missing']} | {values} |")
        lines.append("")
    lines.extend(["## 范围", ""] + ["- " + note for note in result["assumptions"]])
    lines.extend(["", "## 封存来源", ""] + [f"- [{s['origin']}]({s['url']}) SHA256 `{s['sha256']}`" for s in result["sources"]])
    return "\n".join(lines) + "\n"
