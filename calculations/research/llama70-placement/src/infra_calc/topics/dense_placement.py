"""Explicit BF16 Qwen Dense / public Llama70 TP/PP/DP weight, head and state placement.

No aggregate-memory shortcut: inspect each stage/rank, including replicated KV
heads/norms and pipeline endpoint parameters. This is a declared basic TP path.
"""

from math import prod
from ..models import qwen3, llama70
from ..schema import Scenario
from ..sources import model_config, provenance
from ..units import positive_int


def calculate(
    model: str = "qwen3-8b",
    tp: int = 8,
    pp: int = 1,
    dp: int = 1,
    batch_per_replica: int = 1,
    history: int = 8192,
    tokens: int = 1,
    capacity_bytes: int = 24_000_000_000,
    workspace_bytes: int = 2 * 2**30,
) -> dict:
    for key, value in (
        ("tp", tp),
        ("pp", pp),
        ("dp", dp),
        ("capacity_bytes", capacity_bytes),
    ):
        positive_int(value, key)
    positive_int(workspace_bytes, "workspace_bytes", allow_zero=True)
    s = Scenario(batch=batch_per_replica, history=history, tokens=tokens)
    c = model_config(model)
    is_llama = model == llama70.MODEL
    weights = llama70.weights(c) if is_llama else qwen3.weights(c)
    h, f, layers, qh, kh, d, vocab = (
        c[key]
        for key in (
            "hidden_size",
            "intermediate_size",
            "num_hidden_layers",
            "num_attention_heads",
            "num_key_value_heads",
            "head_dim",
            "vocab_size",
        )
    )
    if c["tie_word_embeddings"]:
        raise ValueError(
            "Tied pipeline endpoint weights require explicit replica accounting"
        )
    if pp > layers or any(width % tp for width in (qh, f, vocab)):
        raise ValueError(
            "Nonempty PP stages and divisible query/FFN/vocabulary TP partitions are required"
        )
    if history + tokens > c["max_position_embeddings"]:
        raise ValueError("Sequence exceeds pinned configured context limit")
    stage_counts = [layers // pp + (i < layers % pp) for i in range(pp)]
    cards = []
    start = 0
    for stage, count in enumerate(stage_counts):
        layer_ids = list(range(start, start + count))
        start += count
        for rank in range(tp):
            query_ids = list(range(rank * (qh // tp), (rank + 1) * (qh // tp)))
            kv_ids = sorted({head // (qh // kh) for head in query_ids})
            tensors = []
            matrix_flops = 0
            for weight in weights:
                name, shape = weight.name, list(weight.shape)
                per_layer = "{layer}" in name
                copies = count if per_layer else 1
                if name == "model.embed_tokens.weight" and stage != 0:
                    continue
                if name in ("model.norm.weight", "lm_head.weight") and stage != pp - 1:
                    continue
                if name in ("model.embed_tokens.weight", "lm_head.weight"):
                    shape[0] //= tp
                elif ".q_proj." in name:
                    shape[0] = len(query_ids) * d
                elif ".k_proj." in name or ".v_proj." in name:
                    shape[0] = len(kv_ids) * d
                elif ".o_proj." in name:
                    shape[1] = len(query_ids) * d
                elif ".mlp.gate_proj." in name or ".mlp.up_proj." in name:
                    shape[0] //= tp
                elif ".mlp.down_proj." in name:
                    shape[1] //= tp
                parameters = copies * prod(shape)
                if len(shape) == 2 and name != "model.embed_tokens.weight":
                    rows = batch_per_replica if name == "lm_head.weight" else s.rows
                    matrix_flops += 2 * rows * parameters
                tensors.append(
                    dict(
                        name=name,
                        shape=shape,
                        copies=copies,
                        layer_ids=layer_ids if per_layer else [],
                        parameters=parameters,
                        bytes=2 * parameters,
                    )
                )
            weight_bytes = sum(row["bytes"] for row in tensors)
            kv_bytes = (
                2 * count * batch_per_replica * (history + tokens) * len(kv_ids) * d * 2
            )
            attention = 4 * count * len(query_ids) * d * s.pairs
            for replica in range(dp):
                resident = weight_bytes + kv_bytes + workspace_bytes
                cards.append(
                    dict(
                        replica=replica,
                        stage=stage,
                        tp_rank=rank,
                        layer_ids=layer_ids,
                        query_head_ids=query_ids,
                        kv_head_ids=kv_ids,
                        weights=tensors,
                        weight_bytes=weight_bytes,
                        kv_bytes=kv_bytes,
                        workspace_bytes=workspace_bytes,
                        resident_bytes=resident,
                        headroom_bytes=capacity_bytes - resident,
                        fits_declared_budget=resident <= capacity_bytes,
                        projection_and_head_matrix_flops=matrix_flops,
                        valid_attention_matrix_flops=attention,
                        matrix_flops=matrix_flops + attention,
                        per_layer_output_all_reduce_message_bytes=2 * s.rows * h
                        if tp > 1
                        else 0,
                        output_all_reduce_calls=2 * count if tp > 1 else 0,
                        incoming_pipeline_payload_bytes=2 * s.rows * h
                        if stage > 0
                        else 0,
                        outgoing_pipeline_payload_bytes=2 * s.rows * h
                        if stage < pp - 1
                        else 0,
                    )
                )
    if is_llama:
        for card in cards:
            rank = card["tp_rank"]
            card["ownership"] = {
                "ffn_intermediate_range": [rank * (f // tp), (rank + 1) * (f // tp)],
                "vocabulary_row_range": [
                    rank * (vocab // tp),
                    (rank + 1) * (vocab // tp),
                ],
                "hidden_norm_placement": "replicated whole H vector on each owning-stage TP rank",
                "query_projection_output": "query_head_ids times full head_dim",
                "key_value_projection_output": "kv_head_ids times full head_dim; duplicate IDs on other ranks are physical replicas",
                "output_projection_input": "query_head_ids times full head_dim",
                "mlp_gate_up_output_and_down_input": "ffn_intermediate_range",
                "embedding_present": card["stage"] == 0,
                "head_and_final_norm_present": card["stage"] == pp - 1,
                "range_convention": "half-open [start, stop)",
            }
    logical_parameters = sum(weight.parameters for weight in weights)
    return dict(
        schema_version=1,
        calculation=(
            "llama70-parallel-placement"
            if is_llama
            else "qwen-dense-parallel-placement"
        ),
        model=model,
        scenario=dict(
            tp=tp,
            pp=pp,
            dp=dp,
            batch_per_replica=batch_per_replica,
            history=history,
            tokens=tokens,
            capacity_bytes=capacity_bytes,
            workspace_bytes=workspace_bytes,
            weight_dtype="BF16",
            kv_dtype="BF16",
        ),
        sources=provenance(model),
        placement_cards=cards,
        summary=dict(
            cards=tp * pp * dp,
            global_requests=batch_per_replica * dp,
            logical_parameters_per_replica=logical_parameters,
            physical_weight_bytes=sum(row["weight_bytes"] for row in cards),
            excess_weight_bytes_over_unsharded_replicas=sum(
                row["weight_bytes"] for row in cards
            )
            - 2 * logical_parameters * dp,
            physical_kv_bytes=sum(row["kv_bytes"] for row in cards),
            maximum_card_resident_bytes=max(row["resident_bytes"] for row in cards),
            all_cards_fit_declared_budget=all(
                row["fits_declared_budget"] for row in cards
            ),
            physical_matrix_flops=sum(row["matrix_flops"] for row in cards),
            pipeline_network_send_payload_bytes=sum(
                row["outgoing_pipeline_payload_bytes"] for row in cards
            ),
            predicted_iteration_seconds=None,
        ),
        assumptions=[
            (
                "Public DeepSeek R1 Distill Llama70 BF16 inference: TP splits query heads, FFN intermediate width and vocabulary rows; output/down projections split input axes. Hidden norms replicate; there are no Q/K head norms. pretraining_tp=1 fixes the source model reference, not the declared deployment TP degree."
                if is_llama
                else "Basic BF16 Qwen3 Dense inference: TP splits query heads, FFN intermediate width and vocabulary rows. Output/down projections split their input axes. Per-head and hidden norm scales replicate on TP ranks."
            ),
            "KV head identities follow each rank query heads and the official GQA grouping. A KV head crossing multiple TP ranks is physically replicated, including its K/V projection weights and work; it is never divided into fractional heads.",
            "PP uses contiguous nearly equal layer counts; embedding exists only on the first stage, final norm and untied vocabulary head only on the last. Head runs on the last new position; no tied endpoint handling is inferred.",
            "DP means independent inference replicas, each with batch_per_replica requests and its own weights/cache. No training gradient synchronization is added.",
            "Capacity is checked per physical card with an explicit workspace reservation. BF16 state is retained through history+tokens. Quantization, allocator peaks, activation lifetimes and real backend feasibility remain separate.",
            "Matrix work includes local projections/head and valid causal attention only, not scalar operations. Replicated K/V projection work is counted on every executing rank; DP increases aggregate work with aggregate requests.",
            "Two output all-reduces per local layer is the declared basic TP graph; message bytes are full activation, not link traffic. Vocabulary-parallel embedding reduction, logits collection/sampling, norm/cast communication require a fuller execution graph.",
            "PP transfers full replicated hidden activation from each TP rank to its matching next-stage rank. Payload totals therefore include TP copies; alternate sharded pipeline interfaces need different placement. No overlap, bubbles, bandwidth or latency prediction is claimed.",
        ],
    )
