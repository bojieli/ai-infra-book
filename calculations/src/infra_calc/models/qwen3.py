"""Qwen3 Dense decoder accounting from the pinned official config and implementation.

The graph is counted analytically. It does not allocate model tensors or simulate a
particular CUDA/Metal attention kernel. A cost row describes one layer occurrence;
``repeats`` tells the reader exactly how often it occurs in the whole model.
"""
from collections import Counter
from dataclasses import asdict

from ..schema import Operator, Scenario, Weight, linear
from ..sources import model_config, provenance
from ..units import positive_int


def validate(config: dict) -> None:
    if config["model_type"] != "qwen3":
        raise ValueError("Dense adapter requires model_type=qwen3; MoE needs its own adapter")
    validate_common(config)


def validate_common(config: dict) -> None:
    for name in ("hidden_size", "intermediate_size", "num_hidden_layers", "num_attention_heads",
                 "num_key_value_heads", "head_dim", "vocab_size", "max_position_embeddings"):
        positive_int(config[name], name)
    if config["num_attention_heads"] % config["num_key_value_heads"]:
        raise ValueError("Query heads must be divisible by KV heads")
    if config["head_dim"] % 2:
        raise ValueError("RoPE requires an even head dimension")
    if config.get("attention_bias") or config.get("use_sliding_window") or config.get("rope_scaling"):
        raise ValueError("Bias, sliding-window or scaled-RoPE path is not implemented here")
    if config["hidden_act"] != "silu":
        raise ValueError("This adapter counts SwiGLU with SiLU")


def base_weights(config: dict) -> list[Weight]:
    """Embedding, attention, norms and head shared by the Qwen3 adapters."""
    hidden, ffn = config["hidden_size"], config["intermediate_size"]
    heads, kv_heads, dim = (config[k] for k in ("num_attention_heads", "num_key_value_heads", "head_dim"))
    layers, vocab = config["num_hidden_layers"], config["vocab_size"]
    rows = [Weight("model.embed_tokens.weight", (vocab, hidden))]
    for name, shape in [
        ("self_attn.q_proj", (heads * dim, hidden)),
        ("self_attn.k_proj", (kv_heads * dim, hidden)),
        ("self_attn.v_proj", (kv_heads * dim, hidden)),
        ("self_attn.o_proj", (hidden, heads * dim)),
        ("self_attn.q_norm", (dim,)), ("self_attn.k_norm", (dim,)),
        ("input_layernorm", (hidden,)), ("post_attention_layernorm", (hidden,)),
    ]:
        rows.append(Weight(f"model.layers.{{layer}}.{name}.weight", shape, layers))
    rows.append(Weight("model.norm.weight", (hidden,)))
    if not config["tie_word_embeddings"]:
        rows.append(Weight("lm_head.weight", (vocab, hidden)))
    return rows


def weights(config: dict) -> list[Weight]:
    validate(config)
    h, f, layers = config["hidden_size"], config["intermediate_size"], config["num_hidden_layers"]
    return base_weights(config) + [
        Weight(f"model.layers.{{layer}}.mlp.{name}.weight", shape, layers)
        for name, shape in (("gate_proj", (f, h)), ("up_proj", (f, h)), ("down_proj", (h, f)))
    ]


def rmsnorm(name: str, rows: int, dim: int, scenario: Scenario, repeats: int = 1) -> Operator:
    # square D + sum D-1 + mean 1 + epsilon 1 + normalize D + affine D.
    return Operator(
        name, "normalization", {"input": [rows, dim], "weight": [dim], "output": [rows, dim]},
        repeats=repeats, scalar_flops=rows * (4 * dim + 1), special_ops={"rsqrt": rows},
        weight_read_bytes=dim * scenario.weight_bytes,
        activation_read_bytes=rows * dim * scenario.activation_bytes,
        activation_write_bytes=rows * dim * scenario.activation_bytes,
        notes="按 FP32 行内归约的代数计数；rsqrt、类型转换与临时 FP32 张量分列／不推断 HBM spill。",
    )


def build_operators(config: dict, scenario: Scenario, mlp_ops: list[Operator] | None = None) -> list[Operator]:
    """Common attention/residual graph; adapters supply their own MLP operators."""
    if scenario.history + scenario.tokens > config["max_position_embeddings"]:
        raise ValueError("Requested length exceeds the pinned unscaled config context limit")
    b, p, s, m = scenario.batch, scenario.tokens, scenario.history, scenario.rows
    h, f, layers = config["hidden_size"], config["intermediate_size"], config["num_hidden_layers"]
    qh, kh, d, vocab = (config[k] for k in ("num_attention_heads", "num_key_value_heads", "head_dim", "vocab_size"))
    a, k, score = scenario.activation_bytes, scenario.kv_bytes, scenario.score_bytes
    q_width, kv_width = qh * d, kh * d
    valid_scores = qh * scenario.pairs
    rectangular_scores = qh * scenario.rectangular_pairs
    score_tensor_bytes = rectangular_scores * score

    ops = [Operator(
        "embedding", "embedding", {"indices": [b, p], "table": [vocab, h], "output": [m, h]},
        weight_read_bytes=m * h * scenario.weight_bytes, activation_read_bytes=m * 8,
        activation_write_bytes=m * h * a,
        notes="每 token 一次行查找，不读取整个词表；重复 token 是否缓存未假定。int64 输入索引。",
    )]
    # Reference shares position tables across decoder layers. With equal-length
    # requests and equal position IDs, this teaching path constructs one table.
    ops.append(Operator(
        "rope_table", "position", {"frequencies": [p, d // 2], "cos_sin_each": [p, d]},
        scalar_flops=p * d // 2, special_ops={"sin": p * d, "cos": p * d},
        activation_read_bytes=d // 2 * 4 + p * 8, activation_write_bytes=2 * p * d * a,
        notes="同位置 ID 批共享，所有层复用；inv_freq 固定不计初始化。参考路径复制频率后求 sin/cos；转换另计。",
    ))
    ops.append(rmsnorm("input_layernorm", m, h, scenario, layers))
    for name, width in (("q_proj", q_width), ("k_proj", kv_width), ("v_proj", kv_width)):
        ops.append(linear(name, m, h, width, scenario, repeats=layers))
    ops.extend((rmsnorm("q_norm", m * qh, d, scenario, layers),
                rmsnorm("k_norm", m * kh, d, scenario, layers)))
    rope_elements = m * (q_width + kv_width)
    ops.append(Operator(
        "apply_rope", "position", {"Q": [b, qh, p, d], "K": [b, kh, p, d]},
        repeats=layers, scalar_flops=3 * rope_elements,
        special_ops={"negate": rope_elements // 2},
        activation_read_bytes=rope_elements * a + 2 * p * d * a,
        activation_write_bytes=rope_elements * a,
        notes="2 multiply + 1 add/元素，rotate_half 符号翻转分列；表按批／头理想复用。",
    ))
    ops.append(Operator(
        "kv_append", "state", {"new_K_and_V_each": [b, kh, p, d]}, repeats=layers,
        activation_read_bytes=2 * m * kv_width * a,
        activation_write_bytes=2 * m * kv_width * k,
        notes="原位／分页 append 载荷；不假定动态 torch.cat 对旧缓存整段复制。",
    ))
    ops.append(Operator(
        "qk", "attention", {"Q": [b, qh, p, d], "K_shared": [b, kh, s + p, d],
                               "scores_rectangular": [b, qh, p, s + p]},
        repeats=layers, matrix_flops=2 * valid_scores * d,
        activation_read_bytes=m * q_width * a + b * (s + p) * kv_width * k,
        activation_write_bytes=score_tensor_bytes,
        notes="FLOPs 仅有效因果位置；载荷是假定 Q/K 各读一次、GQA 头共享，完整分数矩阵物化。",
    ))
    ops.append(Operator(
        "score_scale_mask_softmax", "softmax", {"scores": [b, qh, p, s + p]},
        repeats=layers,
        # scale + subtract max + sum + divide (one fewer sum per row)
        scalar_flops=4 * valid_scores - m * qh,
        special_ops={"exp": valid_scores, "compare_max": valid_scores - m * qh,
                     "mask_decisions": rectangular_scores},
        activation_read_bytes=score_tensor_bytes, activation_write_bytes=score_tensor_bytes,
        notes="选择的融合 scale/mask/softmax 代数工作；屏蔽点不计 exp。物化 FP32 默认概率；非具体 eager trace。",
    ))
    ops.append(Operator(
        "pv", "attention", {"P": [b, qh, p, s + p], "V_shared": [b, kh, s + p, d],
                               "output": [b, qh, p, d]},
        repeats=layers, matrix_flops=2 * valid_scores * d,
        activation_read_bytes=score_tensor_bytes + b * (s + p) * kv_width * k,
        activation_write_bytes=m * q_width * a,
        notes="PV/AV：各 Q 头仍计算；V 容量不乘 GQA 复制数。载荷假定 V 在头／查询之间理想复用。",
    ))
    ops.append(linear("o_proj", m, q_width, h, scenario, repeats=layers))

    def residual(name: str) -> Operator:
        return Operator(name, "residual", {"inputs_each": [m, h], "output": [m, h]},
                        repeats=layers, scalar_flops=m * h,
                        activation_read_bytes=2 * m * h * a, activation_write_bytes=m * h * a)

    ops.append(residual("attention_residual"))
    ops.append(rmsnorm("post_attention_layernorm", m, h, scenario, layers))
    if mlp_ops is None:
        ops.extend((linear("gate_proj", m, h, f, scenario, repeats=layers),
                    linear("up_proj", m, h, f, scenario, repeats=layers)))
        ops.append(Operator(
            "silu_mul", "activation", {"gate": [m, f], "up": [m, f], "output": [m, f]},
            repeats=layers, scalar_flops=4 * m * f,
            special_ops={"exp": m * f, "negate": m * f},
            activation_read_bytes=2 * m * f * a, activation_write_bytes=m * f * a,
            notes="sigmoid: exp(-x), +1, reciprocal；再乘 x 和 up。exp 与取负分列。",
        ))
        ops.append(linear("down_proj", m, f, h, scenario, repeats=layers))
    else:
        ops.extend(mlp_ops)
    ops.append(residual("ffn_residual"))
    ops.append(rmsnorm("final_norm", m, h, scenario))
    if scenario.head_rows:
        ops.append(linear("lm_head", scenario.head_rows, h, vocab, scenario))

    return ops


def calculate(model: str, scenario: Scenario) -> dict:
    config = model_config(model)
    validate(config)
    return summarize(model, config, scenario, build_operators(config, scenario), weights(config))


def summarize(model: str, config: dict, scenario: Scenario, ops: list[Operator], tensors: list[Weight]) -> dict:
    """Aggregate an already validated graph without selecting an architecture."""
    b, p, s = scenario.batch, scenario.tokens, scenario.history
    layers, d = config["num_hidden_layers"], config["head_dim"]
    kv_width = config["num_key_value_heads"] * d
    valid_scores = config["num_attention_heads"] * scenario.pairs
    rectangular_scores = config["num_attention_heads"] * scenario.rectangular_pairs
    score_tensor_bytes = rectangular_scores * scenario.score_bytes
    k = scenario.kv_bytes
    parameters = sum(weight.parameters for weight in tensors)
    special = Counter()
    for op in ops:
        special.update({key: count * op.repeats for key, count in op.special_ops.items()})
    kv_per_token = 2 * layers * kv_width * k
    backbone = sum(op.matrix_flops * op.repeats for op in ops if op.category == "linear" and op.name != "lm_head")
    return {
        "schema_version": 1, "calculation": "qwen3-dense-forward", "model": model,
        "scenario": asdict(scenario), "sources": provenance(model),
        "dimensions": {key: config[key] for key in (
            "num_hidden_layers", "hidden_size", "intermediate_size", "num_attention_heads",
            "num_key_value_heads", "head_dim", "vocab_size", "tie_word_embeddings")},
        "assumptions": [
            "所有请求等长、相同位置 ID、无跨请求前缀共享，无 TP/PP；dropout=0 推理。",
            "全模型权重统一 weight_bytes 的教学格式；不由 torch_dtype 推断实际量化格式。",
            "每行 operator 成本为一次出现，repeats 是层数；布局视图与 GQA repeat 不额外物化。",
            "FMA=2；matrix_flops 是有效因果矩阵工作，scalar_flops 是声明算法的普通算术；特殊函数另列。",
            "operator 读写是独立算子操作数载荷，分数／概率矩形物化；不是实测 HBM、不是全图流量下界。",
            "标量行内中间量视为片上；矩形注意力同时报告，FlashAttention/tile/缓存流量由执行专题另算。",
            "不计采样、tokenizer、kernel launch、分配器、KV 管理索引及后端工作区；不据此声称完整 token 时间。",
        ],
        "weights": [tensor.record(scenario.weight_bytes) for tensor in tensors],
        "operators": [op.record() for op in ops],
        "summary": {
            "parameters": parameters, "weight_resident_bytes": parameters * scenario.weight_bytes,
            "backbone_projection_ffn_flops": backbone,
            "causal_attention_matrix_flops": 4 * valid_scores * d * layers,
            "rectangular_attention_matrix_flops": 4 * rectangular_scores * d * layers,
            "matrix_flops": sum(op.matrix_flops * op.repeats for op in ops),
            "scalar_flops": sum(op.scalar_flops * op.repeats for op in ops),
            "special_ops": dict(special),
            "weight_read_once_per_operator_bytes": sum(op.weight_read_bytes * op.repeats for op in ops),
            "activation_operand_read_bytes": sum(op.activation_read_bytes * op.repeats for op in ops),
            "activation_operand_write_bytes": sum(op.activation_write_bytes * op.repeats for op in ops),
            "kv_bytes_per_token_per_request": kv_per_token,
            "kv_resident_before_bytes": b * s * kv_per_token,
            "kv_resident_after_bytes": b * (s + p) * kv_per_token,
            "kv_new_write_bytes": b * p * kv_per_token,
            "kv_existing_history_unique_payload_bytes": b * s * kv_per_token,
            "kv_attention_unique_payload_bytes": b * (s + p) * kv_per_token,
            "kv_logical_query_head_operand_bytes": 2 * valid_scores * d * k * layers,
            "attention_score_tensor_per_layer_bytes": score_tensor_bytes,
            "materialized_scores_probabilities_io_all_layers_bytes": 4 * score_tensor_bytes * layers,
            "minimum_required_weight_and_kv_bytes": parameters * scenario.weight_bytes + b * (s + p) * kv_per_token,
        },
    }


def generation(model: str, batch: int, history: int, steps: int, kv_bytes: int = 2) -> dict:
    """Sum G forward decode steps; prompt prefill is not included.

    In a normal generation API the prompt's last logits already generate one
    token. Here G counts *subsequent model calls that each append one KV token*,
    avoiding the common off-by-one ambiguity about emitted tokens.
    """
    positive_int(steps, "steps")
    first = calculate(model, Scenario(batch=batch, history=history, tokens=1, kv_bytes=kv_bytes))
    last = calculate(model, Scenario(batch=batch, history=history + steps - 1, tokens=1, kv_bytes=kv_bytes))
    per_token = first["summary"]["kv_bytes_per_token_per_request"]
    return {
        "schema_version": 1, "calculation": "decode-sequence", "model": model,
        "scenario": {"batch": batch, "history": history, "forward_steps": steps, "kv_bytes": kv_bytes},
        "sources": first["sources"],
        "assumptions": ["G 表示 G 次追加 KV 的 decode forward，不包括 prompt prefill；不等同于 API 的 G 个输出 token。",
                        "每步权重按批内一次复用，步间从该接口重取；历史载荷为每步各历史记录读取一次。"],
        "summary": {
            "kv_existing_history_read_bytes": batch * per_token * (steps * history + steps * (steps - 1) // 2),
            "kv_current_token_attention_payload_bytes": batch * steps * per_token,
            "kv_new_write_bytes": batch * steps * per_token,
            "kv_final_resident_bytes": batch * (history + steps) * per_token,
            "matrix_flops": (first["summary"]["matrix_flops"] + last["summary"]["matrix_flops"]) * steps // 2,
            "weight_read_once_per_step_bytes": steps * first["summary"]["weight_read_once_per_operator_bytes"],
        },
    }
