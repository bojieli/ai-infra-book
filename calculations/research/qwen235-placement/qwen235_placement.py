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
