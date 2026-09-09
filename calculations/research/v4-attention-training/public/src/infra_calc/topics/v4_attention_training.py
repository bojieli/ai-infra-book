"""Tied-KV sparse attention: explicit unrounded real-arithmetic reference VJP."""

import math
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


def reference(q, kv, sink, indices, upstream=None, scale=None):
    """One batch: Q[T,H,D], shared KV[K,D], index slots[T,J]. -1 is invalid."""
    tokens, heads, dim = len(q), len(sink), len(kv[0])
    factor = dim**-0.5 if scale is None else scale
    dq = [[[0.0] * dim for _ in range(heads)] for _ in range(tokens)]
    dkv = [[0.0] * dim for _ in kv]
    dsink = [0.0] * heads
    output = []
    for t in range(tokens):
        ids = [i for i in indices[t] if i != -1]
        if not ids or any(i < 0 or i >= len(kv) for i in ids):
            raise ValueError("Each query needs valid IDs; only -1 denotes padding")
        out_heads = []
        for h in range(heads):
            logits = [factor * sum(a * b for a, b in zip(q[t][h], kv[i])) for i in ids]
            maximum = max(logits + [sink[h]])
            weights = [math.exp(v - maximum) for v in logits + [sink[h]]]
            total = sum(weights)
            probabilities = [v / total for v in weights]
            p, ps = probabilities[:-1], probabilities[-1]
            out_heads.append(
                [sum(prob * kv[i][d] for prob, i in zip(p, ids)) for d in range(dim)]
            )
            if upstream is None:
                continue
            g = upstream[t][h]
            dp = [sum(a * b for a, b in zip(g, kv[i])) for i in ids]
            delta = sum(a * b for a, b in zip(p, dp))
            ds = [prob * (grad - delta) for prob, grad in zip(p, dp)]
            dsink[h] += -ps * delta
            for prob, score_grad, i in zip(p, ds, ids):
                scaled = score_grad * factor
                for d in range(dim):
                    dq[t][h][d] += scaled * kv[i][d]
                    dkv[i][d] += prob * g[d] + scaled * q[t][h][d]
        output.append(out_heads)
    return dict(output=output, dq=dq, dkv=dkv, dsink=dsink)


def calculate(
    batch=1, tokens=128, kv_tokens=None, heads=None, head_dim=None, indices=None
):
    cfg = model_config("deepseek-v4-flash", reference=True)
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    kv_tokens = tokens if kv_tokens is None else positive_int(kv_tokens, "kv_tokens")
    heads = cfg["n_heads"] if heads is None else positive_int(heads, "heads")
    head_dim = (
        cfg["head_dim"] if head_dim is None else positive_int(head_dim, "head_dim")
    )
    if indices is None:
        if kv_tokens != tokens:
            raise ValueError("Default causal window requires kv_tokens == tokens")
        window = cfg["window_size"]
        indices = [
            [-1] * max(0, window - t - 1) + list(range(max(0, t - window + 1), t + 1))
            for t in range(tokens)
        ]
    if len(indices) != tokens or not indices or not indices[0]:
        raise ValueError("indices must give a nonempty row per query")
    slots = len(indices[0])
    valid = []
    unique = []
    for row in indices:
        if len(row) != slots:
            raise ValueError("Source indices tensor has a rectangular slot dimension")
        for i in row:
            if (
                isinstance(i, bool)
                or not isinstance(i, int)
                or i < -1
                or i >= kv_tokens
            ):
                raise ValueError(
                    "Only -1 padding or valid integer KV IDs are supported"
                )
        ids = [i for i in row if i != -1]
        if not ids:
            raise ValueError(
                "All-invalid query is outside the source numerical contract"
            )
        valid.append(len(ids))
        unique.append(len(set(ids)))
    rows = batch * tokens * heads
    a = batch * heads * sum(valid)
    d = head_dim
    matrices = [
        dict(
            name=name,
            phase=phase,
            flops=2 * a * d,
            formula="2 * batch * heads * sum(valid_slots) * head_dim",
        )
        for name, phase in [
            ("QK", "forward"),
            ("PV", "forward"),
            ("dP", "backward"),
            ("dQ", "backward"),
            ("dKV_key_local", "backward"),
            ("dKV_value_local", "backward"),
        ]
    ]
    saved = dict(
        q_fp32=4 * batch * tokens * heads * d,
        kv_fp32_shared_key_value=4 * batch * kv_tokens * d,
        probabilities_valid_slots_fp32=4 * a,
        sink_probability_fp32=4 * rows,
        indices_int32=4 * batch * tokens * slots,
    )
    return dict(
        schema_version=1,
        calculation="v4-tied-kv-attention-training-reference",
        model="deepseek-v4-flash",
        scenario=dict(
            batch=batch,
            tokens=tokens,
            kv_tokens=kv_tokens,
            heads=heads,
            head_dim=head_dim,
            indices=indices,
        ),
        sources=provenance("deepseek-v4-flash"),
        schedule=dict(
            valid_slots_per_query=valid,
            unique_kv_ids_per_query=unique,
            valid_head_slots=a,
            query_head_rows=rows,
            duplicates_per_batch=sum(v - u for v, u in zip(valid, unique)),
            schedule_shared_across_batch=True,
            scale=d**-0.5,
            scope="one attention core, not 43 layers; explicit indices, no indexer training objective",
        ),
        dtype_contract=dict(
            source_q_kv_output="BF16",
            source_sink_score_accumulation="FP32",
            source_pv_exponent_operand="BF16 cast of unnormalized exponent; not exact saved probabilities",
            reference="unrounded real arithmetic, FP32 saved-state contract, FP64 numerical oracle",
            cast_surrogate_gradient=None,
        ),
        source_semantic_tensor_bytes=dict(
            q=2 * batch * tokens * heads * d,
            kv_shared_key_value=2 * batch * kv_tokens * d,
            output=2 * batch * tokens * heads * d,
            sink=4 * heads,
            indices=4 * batch * tokens * slots,
            scope="logical source interface tensor sizes; not total transfer traffic or backward buffer dtype",
        ),
        matrices=matrices,
        scalar=dict(
            forward_scale_and_softmax_flops=4 * a + 2 * rows,
            backward_softmax_and_scale_flops=5 * a,
            backward_kv_branch_join_and_scatter_flops=2 * a * d,
            backward_sink_reduce_flops=heads * (batch * tokens - 1),
        ),
        special_ops=dict(
            forward_exp_calls=a + rows,
            forward_max_comparisons=a,
            backward_special_calls=0,
        ),
        integer_actions=dict(
            slot_validity_checks=batch * tokens * slots,
            valid_gather_ids=batch * sum(valid),
            logical_gradient_scatter_vectors=a,
            duplicate_selected_ids_preserved=True,
        ),
        reference_data_ops=dict(
            dkv_zero_initialization_bytes=4 * batch * kv_tokens * d,
            dkv_scatter_read_bytes=4 * a * d,
            dkv_scatter_write_bytes=4 * a * d,
            scope="FP32 reference dKV += joined local gradient per head slot; no coalescing assumed; not complete memory traffic",
        ),
        saved_forward_boundary=dict(
            buffers=saved,
            total_bytes=sum(saved.values()),
            aliases=[
                "K and V are one shared KV identity, with one joined dKV",
                "probabilities are saved per slot, repeated IDs are distinct softmax entries",
            ],
            scope="saved forward subset; excludes parameter/input owners, output/upstream, backward temporaries and allocator workspace",
        ),
        lifecycle=[
            dict(
                event="forward",
                retains=list(saved),
                note="output is not required by this saved-P VJP",
            ),
            dict(event="backward_dP", reads=["kv_fp32_shared_key_value", "upstream"]),
            dict(
                event="softmax_vjp",
                reads=["probabilities_valid_slots_fp32", "sink_probability_fp32"],
                creates=["dscore", "dsink"],
            ),
            dict(
                event="local_matrix_vjps",
                reads=["q_fp32", "kv_fp32_shared_key_value", "dscore", "upstream"],
                creates=["dQ", "dKV_key_local", "dKV_value_local"],
            ),
            dict(
                event="join_and_scatter",
                reads=["indices_int32"],
                creates=["dKV_shared"],
                note="join both local KV paths, then accumulate every repeated index across queries/heads",
            ),
        ],
        totals=dict(
            forward_matrix_flops=4 * a * d,
            backward_matrix_flops=8 * a * d,
            forward_scalar_flops=4 * a + 2 * rows,
            backward_scalar_flops=5 * a + 2 * a * d + heads * (batch * tokens - 1),
        ),
        coverage=dict(
            tied_kv_main_loss_vjp=True,
            sink_gradient=True,
            index_selection_gradient=False,
            quantized_kernel_value_equivalence=False,
            complete_attention_layer=False,
            complete_v4_training=False,
            actual_backward_kernel_flops=None,
            actual_peak_bytes=None,
        ),
        assumptions=[
            "Real-arithmetic reference evaluated with FP64; source BF16 Q/KV/output and BF16 exponent cast before PV are not reproduced. No STE is asserted for that cast.",
            "Softmax includes sink in stable max for real-math equivalence; source online max is over ordinary scores and adds sink only to denominator. Floating-point ordering differs.",
            "Only -1 padding is supported; out-of-range IDs and all-invalid rows rejected. Repeated valid IDs remain separate probability entries with scatter-add gradients.",
            "Matrix contractions use 2mnk including local outer products; scalar work never repeats their reductions. Reference scalar algorithm is declared, not Python helper instruction counts.",
            "Valid logical slots only. Source 64-slot tile padding, wrapper head padding, online-softmax work and unknown backward launch strategy are outside this ledger.",
            "The indexer training loss, compressor, projections, RMSNorm/RoPE, QAT and distributed communication remain outside this core.",
        ],
    )


def markdown(result):
    lines = [
        "# V4 tied-KV 稀疏注意力训练参考",
        "",
        "仅一个 attention core 的去舍入数学图；包含 sink 梯度、共享 KV 两支路与重复 ID 归并。",
        "",
        "官方 BF16 中间转换未复现；不是量化内核逐值等价、完整层训练或实际峰值。",
        "",
        "| 字段 | 值 |",
        "|---|---|",
    ]

    def visit(value, path):
        if isinstance(value, dict) and value:
            for k, v in value.items():
                visit(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list) and value:
            for i, v in enumerate(value):
                visit(v, f"{path}[{i}]")
        else:
            text = "unknown (null)" if value is None else str(value)
            lines.append(
                f'| {path} | {text.replace(chr(10),"<br>").replace("|","&#124;")} |'
            )

    visit(result, "")
    return "\n".join(lines) + "\n"
