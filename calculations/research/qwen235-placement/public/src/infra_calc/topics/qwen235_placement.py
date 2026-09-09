"""Declared eight-rank Qwen3-235B TP/EP/PP storage; no runtime fit guarantee."""

import json
from math import prod

from infra_calc.models import qwen3_moe
from infra_calc.sources import model_config, provenance, read_source
from infra_calc.topics.capacity_scan import packed_matrix
from infra_calc.units import positive_int

MODEL = "qwen3-235b-a22b"


def calculate(
    tp=2,
    ep=4,
    pp=1,
    length=8192,
    capacity_bytes=80 * 10**9,
    workspace_bytes=2 * 2**30,
    group_size=128,
    scale_bytes=2,
):
    for name, value in dict(
        tp=tp,
        ep=ep,
        pp=pp,
        length=length,
        capacity_bytes=capacity_bytes,
        group_size=group_size,
        scale_bytes=scale_bytes,
    ).items():
        positive_int(value, name)
    positive_int(workspace_bytes, "workspace_bytes", allow_zero=True)
    if tp * ep * pp != 8:
        raise ValueError("Exactly eight ranks: TP * EP * PP must equal eight")
    config = model_config(MODEL)
    if length > config["max_position_embeddings"]:
        raise ValueError("Length exceeds pinned context limit")
    h, f, layers, experts, heads, kv_heads, dim, vocab = (
        config[key]
        for key in (
            "hidden_size",
            "moe_intermediate_size",
            "num_hidden_layers",
            "num_experts",
            "num_attention_heads",
            "num_key_value_heads",
            "head_dim",
            "vocab_size",
        )
    )
    if any(n % d for n, d in [(f, tp), (heads, tp), (vocab, tp), (experts, ep)]):
        raise ValueError("TP/EP must divide the declared matrix/head partitions")
    if not (kv_heads % tp == 0 or tp % kv_heads == 0):
        raise ValueError("KV heads must partition or replicate evenly")
    weights = qwen3_moe.weights(config)
    index = json.loads(read_source(f"sources/{MODEL}/model.safetensors.index.json"))
    expanded = {
        weight.name.format(layer=layer)
        for weight in weights
        for layer in (range(weight.copies) if "{layer}" in weight.name else [0])
    }
    unique_parameters = sum(weight.parameters for weight in weights)
    if expanded != set(index["weight_map"]):
        raise ValueError(
            "Config/implementation tensor names differ from official index"
        )
    if 2 * unique_parameters != index["metadata"]["total_size"]:
        raise ValueError("BF16 shape total differs from official checkpoint index")
    ranks = []
    layer_start = 0
    for pipeline in range(pp):
        layer_count = layers // pp + (pipeline < layers % pp)
        layer_end = layer_start + layer_count
        for expert_rank in range(ep):
            expert_start = expert_rank * (experts // ep)
            expert_end = expert_start + experts // ep
            for tensor_rank in range(tp):
                local_kv_heads = max(1, kv_heads // tp)
                kv_start = (
                    tensor_rank * local_kv_heads
                    if tp <= kv_heads
                    else tensor_rank // (tp // kv_heads)
                )
                rows = []
                for weight in weights:
                    name = weight.name
                    layered = "{layer}" in name
                    copies = layer_count if layered else 1
                    if name == "model.embed_tokens.weight" and pipeline != 0:
                        continue
                    if (
                        name in ("lm_head.weight", "model.norm.weight")
                        and pipeline != pp - 1
                    ):
                        continue
                    shape = list(weight.shape)
                    axis, start, end, category = None, None, None, "norm"
                    if ".mlp.experts." in name:
                        expert_id = int(name.split(".experts.")[1].split(".")[0])
                        if not expert_start <= expert_id < expert_end:
                            continue
                        category = "expert"
                        axis = 1 if ".down_proj." in name else 0
                        start = tensor_rank * (shape[axis] // tp)
                        end = start + shape[axis] // tp
                    elif name in ("model.embed_tokens.weight", "lm_head.weight"):
                        category, axis = "vocabulary", 0
                        start, end = tensor_rank * (vocab // tp), (tensor_rank + 1) * (
                            vocab // tp
                        )
                    elif ".mlp.gate.weight" in name:
                        category = "router"
                    elif ".self_attn." in name and len(shape) == 2:
                        category = "attention"
                        axis = 1 if ".o_proj." in name else 0
                        if ".k_proj." in name or ".v_proj." in name:
                            start, end = (
                                kv_start * dim,
                                (kv_start + local_kv_heads) * dim,
                            )
                        else:
                            start = tensor_rank * (shape[axis] // tp)
                            end = start + shape[axis] // tp
                    if axis is not None:
                        shape[axis] = end - start
                    eligible = category in ("attention", "expert")
                    storage = []
                    for bits in (16, 8, 4):
                        if bits != 16 and eligible:
                            packed = packed_matrix(
                                tuple(shape), bits, group_size, scale_bytes
                            )
                            payload = packed["packed_bytes"] * copies
                            metadata = packed["scale_bytes"] * copies
                            groups = packed["groups"] * copies
                        else:
                            payload, metadata, groups = 2 * prod(shape) * copies, 0, 0
                        storage.append(
                            dict(
                                bits=bits,
                                payload_bytes=payload,
                                scale_bytes=metadata,
                                groups=groups,
                                total_bytes=payload + metadata,
                            )
                        )
                    rows.append(
                        dict(
                            name=name,
                            category=category,
                            global_shape=list(weight.shape),
                            local_shape=shape,
                            shard_axis=axis,
                            shard_start=start,
                            shard_end=end,
                            layers=[layer_start, layer_end] if layered else None,
                            copies=copies,
                            parameters=prod(shape) * copies,
                            low_bit_eligible=eligible,
                            storage=storage,
                        )
                    )
                kv = 2 * layer_count * local_kv_heads * dim * length * 2
                formats = []
                for index_bits, bits in enumerate((16, 8, 4)):
                    payload = sum(
                        row["storage"][index_bits]["payload_bytes"] for row in rows
                    )
                    metadata = sum(
                        row["storage"][index_bits]["scale_bytes"] for row in rows
                    )
                    weight_bytes = payload + metadata
                    available = capacity_bytes - weight_bytes - workspace_bytes
                    fits = available >= 0
                    maximum = max(0, available // kv)
                    formats.append(
                        dict(
                            bits=bits,
                            payload_bytes=payload,
                            scale_bytes=metadata,
                            weight_bytes=weight_bytes,
                            weights_workspace_fit=fits,
                            kv_bytes_per_request=kv,
                            available_for_kv_bytes=available,
                            maximum_requests=maximum,
                            resident_at_maximum_bytes=weight_bytes
                            + workspace_bytes
                            + maximum * kv,
                            next_request_bytes=weight_bytes
                            + workspace_bytes
                            + (maximum + 1) * kv,
                        )
                    )
                ranks.append(
                    dict(
                        rank=len(ranks),
                        pipeline_stage=pipeline,
                        expert_rank=expert_rank,
                        tensor_rank=tensor_rank,
                        layer_range=[layer_start, layer_end],
                        expert_range=[expert_start, expert_end],
                        q_head_range=[
                            tensor_rank * (heads // tp),
                            (tensor_rank + 1) * (heads // tp),
                        ],
                        kv_head_range=[kv_start, kv_start + local_kv_heads],
                        tensors=rows,
                        formats=formats,
                    )
                )
        layer_start = layer_end
    cohort = []
    for i, bits in enumerate((16, 8, 4)):
        maximum = min(rank["formats"][i]["maximum_requests"] for rank in ranks)
        cohort.append(
            dict(
                bits=bits,
                maximum_requests=maximum,
                all_weights_workspace_fit=all(
                    rank["formats"][i]["weights_workspace_fit"] for rank in ranks
                ),
                limiting_ranks=[
                    rank["rank"]
                    for rank in ranks
                    if rank["formats"][i]["maximum_requests"] == maximum
                ],
                physical_weight_bytes=sum(
                    rank["formats"][i]["weight_bytes"] for rank in ranks
                ),
            )
        )
    return dict(
        calculation="qwen235-placement-capacity",
        model=MODEL,
        scenario=dict(
            tp=tp,
            ep=ep,
            pp=pp,
            length=length,
            capacity_bytes=capacity_bytes,
            workspace_bytes=workspace_bytes,
            group_size=group_size,
            scale_bytes=scale_bytes,
        ),
        sources=provenance(MODEL),
        evidence=dict(
            index_tensor_count=len(expanded),
            unique_parameters=unique_parameters,
            official_index_bf16_bytes=index["metadata"]["total_size"],
            shape_basis="Locked config and implementation; index verifies keys and aggregate bytes, not per-tensor headers",
        ),
        ranks=ranks,
        cohort=cohort,
        runtime=dict(
            actual_peak_bytes=None,
            routing_temporary_bytes=None,
            workspace_reserved_per_rank_bytes=workspace_bytes,
            ownership_records_device_bytes=None,
        ),
        scope=[
            "Exactly eight ranks, no DP. EP replicas process the same request cohort; attention and KV replicate across EP, never divide KV by EP.",
            "All 128 experts remain resident. Each EP owns a disjoint expert range; expert intermediate channels partition across TP. Router and all norms replicate on TP/EP.",
            "TP8 replicates each of four KV heads twice; Q head slices match corresponding GQA KV head. Other TP sizes partition KV heads.",
            "Contiguous balanced pipeline layers; embeddings only first stage, final norm/head only last stage. Vocabulary rows partition TP and replicate EP.",
            "Eligible attention/expert local shards use teaching symmetric rowwise grouped 8/4bit storage; scale groups recomputed after sharding. No runtime kernel or quality claim.",
            "Router weights are BF16 resident; token routing/dispatch, collective, dequantization and allocator buffers are not persistent weights and remain within an explicitly supplied conditional workspace reserve.",
            "Ownership records are descriptive host-side metadata, not inferred GPU allocations. KV is BF16 K+V with retained length, no page padding/prefix sharing/offload.",
            "Capacity limits the common cohort by the worst rank. This is conditional storage accounting, not measured runtime capacity or communication performance; C13 remains broader.",
        ],
    )


def markdown(result):
    """Render full rank ownership/storage without the generic report schema."""
    scenario, evidence = result["scenario"], result["evidence"]
    tp, ep, pp = (scenario[key] for key in ("tp", "ep", "pp"))
    lines = [
        "# Qwen3-235B 八卡权重所有权与条件容量",
        "",
        f"TP={tp}，EP={ep}，PP={pp}；同一请求 cohort，EP 不是独立 DP。"
        f"每卡 {scenario['capacity_bytes']:,} bytes，保留长度 {scenario['length']:,}，"
        f"每卡 workspace 预算 {scenario['workspace_bytes']:,} bytes。",
        "",
        f"官方索引 {evidence['index_tensor_count']:,} 个名称；唯一参数 "
        f"{evidence['unique_parameters']:,}；索引 BF16 总量 "
        f"{evidence['official_index_bf16_bytes']:,} bytes。形状依据：{evidence['shape_basis']}。",
        "",
        "容量受最差 rank 限制。以下是条件存储预算，不是运行峰值保证；"
        "路由临时量、激活、collective、反量化及分配器需求尚未由本账求出。",
        "",
        "| 格式 bits | 物理权重 bytes（含复制） | 全 rank 权重+workspace 可放入 | 最大同 cohort 请求 | 限制 ranks |",
        "|---:|---:|---|---:|---|",
    ]
    for row in result["cohort"]:
        lines.append(
            f"| {row['bits']} | {row['physical_weight_bytes']:,} | "
            f"{row['all_weights_workspace_fit']} | {row['maximum_requests']} | {row['limiting_ranks']} |"
        )
    lines += [
        "",
        "区间均为左闭右开；分片轴为原始张量轴。层模板的 copies 是本 rank 层数。"
        "复制倍数表示同一逻辑权重元素在八卡内的副本数，不是对 payload 再乘一次的指令。"
        "表中 payload/scale 已包含本 rank 的 copies。",
        "",
        f"教学低比特仅适用于 attention/expert 矩阵；每行按 local K 分组，"
        f"group_size={scenario['group_size']}，每组 scale={scenario['scale_bytes']} bytes，"
        "无 zero point。词嵌入/输出头、router 和 norm 保持 BF16。",
    ]
    for rank in result["ranks"]:
        lines += [
            "",
            f"## Rank {rank['rank']}（PP {rank['pipeline_stage']} / EP {rank['expert_rank']} / TP {rank['tensor_rank']}）",
            "",
            f"层 {rank['layer_range']}；专家 {rank['expert_range']}；"
            f"Q heads {rank['q_head_range']}；KV heads {rank['kv_head_range']}。",
            "",
            "| bits | payload bytes | scale bytes | 权重 bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 当前最大请求常驻 bytes | 下一请求 bytes |",
            "|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
        ]
        for row in rank["formats"]:
            lines.append(
                f"| {row['bits']} | {row['payload_bytes']:,} | {row['scale_bytes']:,} | "
                f"{row['weight_bytes']:,} | {row['kv_bytes_per_request']:,} | "
                f"{row['available_for_kv_bytes']:,} | {row['maximum_requests']} | "
                f"{row['weights_workspace_fit']} | {row['resident_at_maximum_bytes']:,} | "
                f"{row['next_request_bytes']:,} |"
            )
        lines += [
            "",
            "| 权重模板 | 类别 | 全局 → 局部 shape | 分片轴/区间 | copies | 元素副本数 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |",
            "|---|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for tensor in rank["tensors"]:
            category, name = tensor["category"], tensor["name"]
            if category == "expert":
                replication = 1
            elif category in ("router", "norm"):
                replication = tp * ep
            elif category == "attention" and any(
                part in name for part in (".k_proj.", ".v_proj.")
            ):
                replication = ep * max(1, tp // 4)
            else:
                replication = ep
            shard = (
                "完整"
                if tensor["shard_axis"] is None
                else (
                    f"{tensor['shard_axis']} / [{tensor['shard_start']},{tensor['shard_end']})"
                )
            )
            storage = " | ".join(
                f"{row['payload_bytes']:,} / {row['scale_bytes']:,}"
                for row in tensor["storage"]
            )
            lines.append(
                f"| {name} | {category} | {tensor['global_shape']} → {tensor['local_shape']} | "
                f"{shard} | {tensor['copies']} | {replication} | {storage} |"
            )
    lines += ["", "## 范围与未知接口", ""]
    lines.extend(f"- {item}" for item in result["scope"])
    lines += [
        "",
        "实际运行峰值、路由临时 bytes 和所有权描述对应的设备存储均未推定。"
        "所有权记录是报告元数据，不自动作为 GPU 常驻分配计入。",
        "",
        "## 固定来源",
        "",
    ]
    lines.extend(
        f"- [{row['file']}]({row['url']})；revision `{row['revision']}`；SHA256 `{row['sha256']}`。"
        for row in result["sources"]
    )
    return "\n".join(lines) + "\n"
