"""Local-shard grouped storage over the existing BF16 dense placement graph."""

from infra_calc.topics import dense_placement
from infra_calc.topics.capacity_scan import packed_matrix
from infra_calc.units import positive_int

MODELS = ("qwen3-8b", "qwen3-32b", "deepseek-r1-distill-llama-70b")


def calculate(
    model="qwen3-8b",
    tp=8,
    pp=1,
    dp=1,
    length=8192,
    capacity_bytes=24 * 10**9,
    workspace_bytes=2 * 2**30,
    group_size=128,
    scale_bytes=2,
):
    if model not in MODELS:
        raise ValueError("This storage adapter covers pinned Dense8B/32B/Llama70 only")
    positive_int(length, "length")
    positive_int(group_size, "group_size")
    positive_int(scale_bytes, "scale_bytes")
    # Existing BF16 contract retains history + tokens. Fix one new token and
    # batch one so its KV bytes become the exact per-request coefficient.
    base = dense_placement.calculate(
        model=model,
        tp=tp,
        pp=pp,
        dp=dp,
        batch_per_replica=1,
        history=length - 1,
        tokens=1,
        capacity_bytes=capacity_bytes,
        workspace_bytes=workspace_bytes,
    )
    ranks = []
    for rank_id, card in enumerate(base["placement_cards"]):
        tensors = []
        for weight in card["weights"]:
            eligible = len(weight["shape"]) == 2 and weight["name"] not in (
                "model.embed_tokens.weight",
                "lm_head.weight",
            )
            formats = []
            for bits in (16, 8, 4):
                if eligible and bits != 16:
                    packed = packed_matrix(
                        tuple(weight["shape"]), bits, group_size, scale_bytes
                    )
                    payload = packed["packed_bytes"] * weight["copies"]
                    metadata = packed["scale_bytes"] * weight["copies"]
                    groups = packed["groups"] * weight["copies"]
                else:
                    payload, metadata, groups = weight["bytes"], 0, 0
                formats.append(
                    dict(
                        bits=bits,
                        payload_bytes=payload,
                        scale_bytes=metadata,
                        groups=groups,
                        total_bytes=payload + metadata,
                    )
                )
            tensors.append(dict(**weight, low_bit_eligible=eligible, storage=formats))
        formats = []
        for index, bits in enumerate((16, 8, 4)):
            payload = sum(row["storage"][index]["payload_bytes"] for row in tensors)
            metadata = sum(row["storage"][index]["scale_bytes"] for row in tensors)
            weight_bytes = payload + metadata
            available = capacity_bytes - workspace_bytes - weight_bytes
            maximum = max(0, available // card["kv_bytes"])
            formats.append(
                dict(
                    bits=bits,
                    payload_bytes=payload,
                    scale_bytes=metadata,
                    weight_bytes=weight_bytes,
                    kv_bytes_per_request=card["kv_bytes"],
                    weights_workspace_fit=available >= 0,
                    available_for_kv_bytes=available,
                    maximum_requests=maximum,
                    resident_at_maximum_bytes=weight_bytes
                    + workspace_bytes
                    + maximum * card["kv_bytes"],
                    next_request_bytes=weight_bytes
                    + workspace_bytes
                    + (maximum + 1) * card["kv_bytes"],
                )
            )
        ranks.append(
            dict(
                rank=rank_id,
                replica=card["replica"],
                stage=card["stage"],
                tp_rank=card["tp_rank"],
                layer_ids=card["layer_ids"],
                query_head_ids=card["query_head_ids"],
                kv_head_ids=card["kv_head_ids"],
                weights=tensors,
                formats=formats,
                original_bf16_resident_one_request_bytes=card["resident_bytes"],
            )
        )
    replicas = []
    for replica in range(dp):
        cards = [rank for rank in ranks if rank["replica"] == replica]
        formats = []
        for i, bits in enumerate((16, 8, 4)):
            maximum = min(rank["formats"][i]["maximum_requests"] for rank in cards)
            formats.append(
                dict(
                    bits=bits,
                    maximum_requests=maximum,
                    weights_workspace_fit=all(
                        rank["formats"][i]["weights_workspace_fit"] for rank in cards
                    ),
                    limiting_ranks=[
                        rank["rank"]
                        for rank in cards
                        if rank["formats"][i]["maximum_requests"] == maximum
                    ],
                )
            )
        replicas.append(dict(replica=replica, formats=formats))
    summary = []
    for i, bits in enumerate((16, 8, 4)):
        summary.append(
            dict(
                bits=bits,
                physical_weight_bytes=sum(
                    rank["formats"][i]["weight_bytes"] for rank in ranks
                ),
                maximum_global_requests=sum(
                    row["formats"][i]["maximum_requests"] for row in replicas
                ),
                all_weights_workspace_fit=all(
                    row["formats"][i]["weights_workspace_fit"] for row in replicas
                ),
            )
        )
    return dict(
        calculation="dense-quantized-placement",
        model=model,
        scenario=dict(
            model=model,
            tp=tp,
            pp=pp,
            dp=dp,
            length=length,
            capacity_bytes=capacity_bytes,
            workspace_bytes=workspace_bytes,
            group_size=group_size,
            scale_bytes=scale_bytes,
        ),
        sources=base["sources"],
        ranks=ranks,
        replicas=replicas,
        summary=summary,
        bf16_reference_summary=base["summary"],
        actual_runtime_peak_bytes=None,
        scope=[
            "Reuses the public dense_placement local tensor shapes/copies, KV-head identity and pipeline ownership unchanged. BF16 weights and one-request residency exactly match the base graph.",
            "Retained length includes the last new token: base history=length-1, tokens=1, batch_per_replica=1. KV remains BF16 for every weight format; no fractional KV-head saving.",
            "8/4bit symmetric teaching storage quantizes local 2D projections only, independently per output row and local K group, with ceil tail groups and per-row packed-byte rounding. Embedding, head and all norms stay BF16; no zero points.",
            "All three models use actual config-derived weights. Storage is not a released quantized checkpoint, quality result, or supported kernel claim.",
            "Each independent DP replica is limited by its worst rank. TP/PP ranks share a cohort; free bytes on another rank cannot cover a failing rank. DP global request capacities sum independent replica cohorts.",
            "Workspace is a fixed supplied per-rank reserve, not inferred peak. Activation, routing, dequantization, collective, allocator and batch-dependent workspace may exceed it; conditional maximum requests is not measured runtime capacity.",
            "Base BF16 placement arithmetic/communication summaries are reference values only; quantization does not establish kernel arithmetic or traffic savings. C13 remains broader than this declared storage model.",
        ],
    )


def markdown(result):
    """Dedicated per-rank local-shard storage and conditional capacity report."""
    s = result["scenario"]
    lines = [
        f"# {result['model']} Dense 分片量化容量",
        "",
        f"TP={s['tp']} / PP={s['pp']} / DP={s['dp']}；保留长度 {s['length']:,} "
        f"（含最后新 token）；每卡 {s['capacity_bytes']:,} bytes，"
        f"workspace 条件预算 {s['workspace_bytes']:,} bytes。",
        "",
        "全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；"
        "条件并发受每副本最差 rank 限制，不是实际运行峰值保证。",
        "",
        "| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |",
        "|---:|---:|---:|---|",
    ]
    for row in result["summary"]:
        lines.append(
            f"| {row['bits']} | {row['physical_weight_bytes']:,} | {row['maximum_global_requests']} | {row['all_weights_workspace_fit']} |"
        )
    lines += [
        "",
        "| 副本 | bits | 同副本最大请求 | 限制 ranks |",
        "|---:|---:|---:|---|",
    ]
    for replica in result["replicas"]:
        for row in replica["formats"]:
            lines.append(
                f"| {replica['replica']} | {row['bits']} | {row['maximum_requests']} | {row['limiting_ranks']} |"
            )
    lines += [
        "",
        f"分组按 local K 重新计算：group_size={s['group_size']}，scale={s['scale_bytes']} bytes；"
        "最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。"
        "embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。",
    ]
    for rank in result["ranks"]:
        lines += [
            "",
            f"## Rank {rank['rank']}（DP {rank['replica']} / PP {rank['stage']} / TP {rank['tp_rank']}）",
            "",
            f"层 IDs {rank['layer_ids']}；Q heads {rank['query_head_ids']}；KV heads {rank['kv_head_ids']}。"
            "其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。",
            "",
            "| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |",
            "|---:|---:|---:|---:|---:|---:|---|---:|---:|",
        ]
        for row in rank["formats"]:
            lines.append(
                f"| {row['bits']} | {row['payload_bytes']:,} | {row['scale_bytes']:,} | {row['kv_bytes_per_request']:,} | {row['available_for_kv_bytes']:,} | {row['maximum_requests']} | {row['weights_workspace_fit']} | {row['resident_at_maximum_bytes']:,} | {row['next_request_bytes']:,} |"
            )
        lines += [
            "",
            "| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |",
            "|---|---|---:|---|---:|---:|---:|",
        ]
        for weight in rank["weights"]:
            storage = " | ".join(
                f"{row['payload_bytes']:,} / {row['scale_bytes']:,}"
                for row in weight["storage"]
            )
            lines.append(
                f"| {weight['name']} | {weight['shape']} | {weight['copies']} | {weight['low_bit_eligible']} | {storage} |"
            )
    lines += ["", "## 范围", ""]
    lines.extend(f"- {item}" for item in result["scope"])
    lines += ["", "## 固定来源", ""]
    lines.extend(
        f"- [{row['file']}]({row['url']})；SHA256 `{row['sha256']}`。"
        for row in result["sources"]
    )
    return "\n".join(lines) + "\n"
