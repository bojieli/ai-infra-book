"""One explicit Flash MTPBlock, reusing isolated single-layer ledger functions."""

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from math import prod
from pathlib import Path
from types import FunctionType
import json
import ast
import sys

for ancestor in Path(__file__).resolve().parents:
    if (ancestor / "src/infra_calc/sources.py").is_file():
        sys.path.insert(0, str(ancestor / "src"))
        break
from infra_calc.sources import model_config, provenance, read_source
from infra_calc.units import positive_int
from infra_calc.topics import v4_attention, experts, hyper_connections, v4_fp8_linear

MODEL = "deepseek-v4-flash"


def isolated(function, **replacements):
    """Copy globals, never mutate imported module or its config cache."""
    return FunctionType(
        function.__code__,
        {**function.__globals__, **replacements},
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )


@lru_cache(None)
def checkpoint():
    c = model_config(MODEL, reference=True)
    h = c["dim"]
    d = c["head_dim"]
    q = c["q_lora_rank"]
    heads = c["n_heads"]
    g = c["o_groups"]
    o = c["o_lora_rank"]
    f = c["moe_inter_dim"]
    e = c["n_routed_experts"]
    hc = c["hc_mult"]
    mix = (hc + 2) * hc
    expected = {}

    def matrix(name, shape, scale=None):
        expected["mtp.0." + name + ".weight"] = shape
        if scale:
            expected["mtp.0." + name + ".scale"] = scale

    def fp8(name, n, k):
        matrix(name, [n, k], [(n + 127) // 128, (k + 127) // 128])

    for name, n, k in [
        ("attn.wq_a", q, h),
        ("attn.wq_b", heads * d, q),
        ("attn.wkv", d, h),
        ("attn.wo_a", g * o, heads * d // g),
        ("attn.wo_b", h, g * o),
        ("e_proj", h, h),
        ("h_proj", h, h),
        ("ffn.shared_experts.w1", f, h),
        ("ffn.shared_experts.w3", f, h),
        ("ffn.shared_experts.w2", h, f),
    ]:
        fp8(name, n, k)
    matrix("ffn.gate", [e, h])
    expected["mtp.0.ffn.gate.bias"] = [e]
    for i in range(e):
        for name, n, k in [("w1", f, h), ("w3", f, h), ("w2", h, f)]:
            matrix(f"ffn.experts.{i}.{name}", [n, k // 2], [n, k // 32])
    for name, width in [
        ("attn.q_norm", q),
        ("attn.kv_norm", d),
        ("attn_norm", h),
        ("ffn_norm", h),
        ("enorm", h),
        ("hnorm", h),
        ("norm", h),
    ]:
        expected["mtp.0." + name + ".weight"] = [width]
    expected["mtp.0.attn.attn_sink"] = [heads]
    for branch in ("attn", "ffn"):
        for suffix, shape in [("fn", [mix, hc * h]), ("base", [mix]), ("scale", [3])]:
            expected[f"mtp.0.hc_{branch}_{suffix}"] = shape
    for suffix, shape in [("fn", [hc, hc * h]), ("base", [hc]), ("scale", [1])]:
        expected["mtp.0.hc_head_" + suffix] = shape
    index = json.loads(read_source(f"sources/{MODEL}/model.safetensors.index.json"))
    selected = {k: v for k, v in index["weight_map"].items() if k.startswith("mtp.")}
    if set(selected) != set(expected):
        raise ValueError("MTP expected key coverage mismatch")
    tensors = []
    seen = set()
    sizes = {"F32": 4, "BF16": 2, "F8_E4M3": 1, "F8_E8M0": 1, "I8": 1}
    for shard in sorted(set(selected.values())):
        header = json.loads(read_source(f"sources/{MODEL}/headers/{shard}.json"))
        for name in selected:
            if selected[name] != shard:
                continue
            x = header[name]
            shape = x["shape"]
            dtype = x["dtype"]
            size = x["data_offsets"][1] - x["data_offsets"][0]
            if shape != expected[name] or size != prod(shape) * sizes[dtype]:
                raise ValueError("MTP header shape/dtype-byte mismatch:" + name)
            logical = (
                0
                if name.endswith(".scale")
                else prod(shape) * (2 if dtype == "I8" else 1)
            )
            if dtype == "I8" and ".ffn.experts." not in name:
                raise ValueError("Unknown packed interpretation")
            tensors.append(
                dict(
                    name=name,
                    shape=shape,
                    dtype=dtype,
                    payload_bytes=size,
                    logical_parameters=logical,
                )
            )
            seen.add(name)
    assert seen == set(expected)
    return dict(
        tensors=tensors,
        verified_keys=len(seen),
        logical_parameters=sum(x["logical_parameters"] for x in tensors),
        own_checkpoint_bytes=sum(x["payload_bytes"] for x in tensors),
        shared_embedding_head_not_duplicated=True,
        scope="Header payload only; shared head/embedding excluded; wo_a checkpoint FP8+scale but source constructor requests BF16, load conversion/residency not resolved",
    )


def calculate(batch=1, tokens=1, start_pos=0, routing="balanced"):
    for k, v in [("batch", batch), ("tokens", tokens), ("start_pos", start_pos)]:
        positive_int(v, k, allow_zero=k == "start_pos")
    c = model_config(MODEL, reference=True)
    tree = ast.parse(read_source(f"sources/{MODEL}/inference/model.py"))
    args = next(
        x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "ModelArgs"
    )
    for item in args.body:
        if isinstance(item, ast.AnnAssign) and item.target.id in (
            "max_seq_len",
            "max_batch_size",
        ):
            c.setdefault(item.target.id, ast.literal_eval(item.value))
    L = c["n_layers"]
    h = c["dim"]
    hc = c["hc_mult"]
    v = c["vocab_size"]
    m = batch * tokens
    if start_pos and tokens != 1:
        raise ValueError("Positive start requires one-token MTP call")
    if start_pos + tokens > c["max_seq_len"] or batch > c["max_batch_size"]:
        raise ValueError("Reference allocation limit")
    if L != 43 or c["compress_ratios"][L] != 0:
        raise ValueError("Fixed MTP layer43 ratio0 expected")
    single = {**deepcopy(c), "n_layers": 1, "n_hash_layers": 0, "compress_ratios": [0]}
    cfg = lambda *args, **kwargs: (
        deepcopy(single) if kwargs.get("reference") else model_config(MODEL)
    )
    attn = isolated(v4_attention.calculate, model_config=cfg)(
        MODEL, batch, tokens, start_pos
    )
    geom = isolated(experts.geometry, model_config=cfg)(MODEL)
    expert = isolated(experts.calculate, geometry=lambda _: deepcopy(geom))(
        MODEL, batch, tokens, routing
    )
    residual = isolated(hyper_connections.calculate, model_config=cfg)(
        MODEL, batch, tokens
    )
    residual["summary"].pop("embedding_repeat_output_bytes")

    # Helpers label their sole virtual layer0; preserve one-layer provenance explicitly.
    def remap(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in (
                    "layer_ids",
                    "moe_layers",
                    "router_bias_layers",
                ) and item == [0]:
                    value[key] = [L]
                elif isinstance(item, (dict, list)):
                    remap(item)
        elif isinstance(value, list):
            for item in value:
                remap(item)

    for component in (attn, expert, residual):
        remap(component)
        component["source_layer_mapping"] = {
            "virtual_helper_layer": 0,
            "official_layer": L,
            "scope": "Single MTP-owned layer, not a base model invocation",
        }
        component["assumptions"] = [
            x.replace(
                "No MTP, expert or mHC work in this subledger.",
                "Attention-only subledger for the selected MTP layer; expert/mHC counted separately.",
            )
            .replace(
                "vocabulary projection, MTP and communication.",
                "vocabulary projection and communication.",
            )
            .replace(
                "Embedding repeat materializes the c copies in the reference.",
                "MTP does not use base embedding repeat; its size field was removed.",
            )
            for x in component.get("assumptions", [])
        ]
    outer = [
        dict(
            id="enorm",
            rows=m,
            width=h,
            scalar_flops=m * (4 * h + 1),
            special_ops={"rsqrt": m},
        ),
        dict(
            id="hnorm_four_streams",
            rows=m * hc,
            width=h,
            scalar_flops=m * hc * (4 * h + 1),
            special_ops={"rsqrt": m * hc},
        ),
        dict(
            id="block_attn_ffn_and_final_norm",
            rows=3 * m,
            width=h,
            scalar_flops=3 * m * (4 * h + 1),
            special_ops={"rsqrt": 3 * m},
        ),
        dict(
            id="broadcast_e_plus_h",
            shape=[batch, tokens, hc, h],
            scalar_flops=m * hc * h,
            special_ops={},
        ),
    ]
    projection = [
        dict(
            id="e_proj",
            rows=m,
            input_width=h,
            output_width=h,
            matrix_flops=2 * m * h * h,
        ),
        dict(
            id="h_proj",
            rows=m * hc,
            input_width=h,
            output_width=h,
            matrix_flops=2 * m * hc * h * h,
        ),
        dict(
            id="shared_last_vocabulary",
            rows=batch,
            input_width=h,
            output_width=v,
            matrix_flops=2 * batch * h * v,
        ),
    ]
    fp8 = []
    for row in projection[:2]:
        fp8.append(dict(id=row["id"], **v4_fp8_linear.account(row["rows"], h, h)))
    for row in attn["matrices"]:
        if row["name"] != "wo_a_grouped":
            fp8.append(
                dict(
                    id=row["name"],
                    **v4_fp8_linear.account(
                        row["rows_summed_per_layer"],
                        row["input_width"],
                        row["output_width"],
                    ),
                )
            )
    for row in expert["matrices"]:
        if row["category"] == "shared":
            fp8.append(
                dict(
                    id=row["name"],
                    **v4_fp8_linear.account(
                        row["rows_summed_per_layer"],
                        row["input_width"],
                        row["output_width"],
                    ),
                )
            )
    a = attn["summary"]
    e = expert["summary"]
    r = residual["summary"]
    fmt = expert["routed_expert_format"]["summary"]
    matrix = (
        a["matrix_flops"]
        + e["ffn_matrix_flops"]
        + r["matrix_flops"]
        + sum(x["matrix_flops"] for x in projection)
    )
    scalar = (
        a["accounted_scalar_flops"]
        + expert["non_matrix_summary"]["scalar_flops"]
        + r["scalar_flops"]
        + sum(x["scalar_flops"] for x in outer)
        + fmt["logical_scale_accumulation_flops"]
        + fmt["activation_quantization_scalar_flops"]
        + sum(
            x["activation_quantization_scalar_flops"] + x["logical_scale_flops"]
            for x in fp8
        )
    )
    special = Counter(attn["non_matrix_summary"]["special_ops"])
    special.update(expert["non_matrix_summary"]["special_ops"])
    special.update(r["special_ops"])
    special.update(
        {
            "exp": attn["sparse_kernel_summary"]["exp_ops"],
            "compare_max": attn["sparse_kernel_summary"]["max_comparisons"],
        }
    )
    for x in outer:
        special.update(x["special_ops"])
    for x in fp8:
        special.update(
            {
                k: x[k]
                for k in (
                    "activation_abs_ops",
                    "activation_max_comparisons",
                    "activation_clamp_comparisons",
                    "activation_round_scale_calls",
                    "activation_fp8_cast_elements",
                    "activation_e8m0_cast_elements",
                )
            }
        )
    # Routed Linear calls use the same act_quant kernel, but FP4 GEMM scale
    # application is already owned by the routed format ledger above.
    # Count valid elements/groups; do not infer padded backend instructions.
    routed_quantization_special = {}
    cells = fmt["activation_fp8_output_bytes"]  # one byte per valid FP8 cell
    groups = fmt["activation_e8m0_scale_bytes"]  # one byte per scale group
    routed_quantization_special.update(
        activation_abs_ops=cells,
        activation_max_comparisons=cells,  # 127 reduction + 1 floor per group
        activation_clamp_comparisons=2 * cells,
        activation_round_scale_calls=groups,
        activation_fp8_cast_elements=cells,
        activation_e8m0_cast_elements=groups,
    )
    special.update(routed_quantization_special)
    params = (
        a["matrix_parameters"]
        + e["ffn_matrix_parameters"]
        + r["hc_parameters"]
        + 2 * h * h
        + 5 * h
        + c["q_lora_rank"]
        + c["head_dim"]
        + c["n_heads"]
        + c["n_routed_experts"]
    )
    headers = checkpoint()
    if params != headers["logical_parameters"]:
        raise ValueError("MTP parameter conservation failure")
    kv_before = batch * min(start_pos, c["window_size"]) * c["head_dim"] * 2
    kv_after = batch * min(start_pos + tokens, c["window_size"]) * c["head_dim"] * 2
    return dict(
        calculation="v4-flash-mtp-single-call",
        scenario=dict(batch=batch, tokens=tokens, start_pos=start_pos, routing=routing),
        sources=provenance(MODEL),
        source_layer_id=L,
        source_ratio=0,
        checkpoint=headers,
        outer_projections=projection,
        outer_nonmatrix=outer,
        components=dict(attention=attn, experts=expert, hyper_connections=residual),
        fp8_linear_calls=fp8,
        routed_activation_quantization_special_ops=routed_quantization_special,
        summary=dict(
            matrix_flops=matrix,
            accounted_scalar_flops=scalar,
            special_ops=dict(special),
            own_logical_parameters=params,
            own_checkpoint_payload_bytes=headers["own_checkpoint_bytes"],
            shared_last_head_flops=2 * batch * h * v,
            complete_hbm_bytes=None,
            actual_runtime_peak_bytes=None,
            latency=None,
        ),
        interfaces=dict(
            supplied_target_hidden_bf16_bytes=2 * m * hc * h,
            input_ids_int64_bytes=8 * m,
            shared_embedding_lookup_bytes=2 * m * h,
            broadcast_input_unique_bytes=2 * m * h + 2 * m * hc * h,
            broadcast_output_bytes=2 * m * hc * h,
            fp8_quant_and_gemm_operand_bytes=sum(
                x["total_interface_bytes"] for x in fp8
            ),
            routed_visited_packed_scale_bytes=fmt[
                "visited_weight_and_scale_payload_bytes"
            ],
            shared_head_weight_fp32_bytes=4 * v * h,
            logits_fp32_bytes=4 * batch * v,
        ),
        state=dict(
            cache_write_bytes=batch
            * (1 if start_pos else min(tokens, c["window_size"]))
            * c["head_dim"]
            * 2,
            fresh_attention_KV_source=(
                "new full token KV tensor"
                if start_pos == 0
                else "independent registered MTP ring"
            ),
            caller_hidden_origin="base Block42 output before base HC-head and final RMSNorm; position correspondence explicitly supplied, not inferred",
            owner="mtp.0.attn independent from all base layers",
            valid_window_before_bytes=kv_before,
            valid_window_after_bytes=kv_after,
            registered_cache_bf16_bytes=c["max_batch_size"]
            * c["window_size"]
            * c["head_dim"]
            * 2,
            frequency_table_complex64_bytes=c["max_seq_len"]
            * (c["rope_head_dim"] // 2)
            * 8,
            compressor_bytes=0,
            indexer_bytes=0,
        ),
        scope=[
            "Explicit supplied h is base Block42 output before base hc_head/finalnorm; no base forward performed or charged. IDs/feature token alignment is a caller contract, not observed draft execution.",
            "Exactly one MTP layer43 ratio0, scoring MoE not hash. Isolated copies of helper function globals select virtual one-layer config and remap ownership without shared mutations.",
            "Fresh start0 or positive-start one token with valid independent MTP cache. No actual generated-token count, sampling, acceptance, verification or rollback claim.",
            "HC helper includes own head once and no embedding-repeat work. Shared vocabulary head executes last row only; shared weight residency excluded from own parameters.",
            "FP8 Linear and routed FP4-to-FP8 effective work/scale calls counted without adding GEMMs twice. wo_a is BF16 in source but checkpoint is FP8; loading conversion unresolved.",
            "Interfaces are partial named operands, not complete traffic. Unexpanded norm/HC casts, frequency/setup/index metadata, temporaries and compiled kernel details remain unknown. No manufactured STE or inference from hardware peak.",
        ],
    )


def markdown(result):
    """Readable stage account, with the complete machine ledger retained below."""
    summary = result["summary"]
    lines = [
        "# V4 Flash：一次 MTPBlock 调用", "",
        "输入是调用方提供的 token IDs 与主干 Block42 输出特征。这里只计算一层 MTP；实际草稿对齐、接受率与验证调用次数未知。", "",
        "| 项目 | 数值 |", "|---|---:|",
        f"| 有效矩阵 FLOPs | {summary['matrix_flops']:,} |",
        f"| 已计标量 FLOPs | {summary['accounted_scalar_flops']:,} |",
        f"| MTP 自有逻辑参数 | {summary['own_logical_parameters']:,} |",
        f"| MTP checkpoint payload bytes | {summary['own_checkpoint_payload_bytes']:,} |", "",
        "共享 embedding/head 权重不重复计入 MTP 自有参数；共享词表投影的本次算术仍计入。checkpoint payload 不等于运行时峰值。", "",
        "## 外层矩阵", "",
        "| 投影 | 行数 M | 输入 K | 输出 N | 2MKN FLOPs |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["outer_projections"]:
        lines.append(f"| {row['id']} | {row['rows']:,} | {row['input_width']:,} | {row['output_width']:,} | {row['matrix_flops']:,} |")
    lines += ["", "内部 attention、MoE 与 mHC 的逐矩阵形状、路由和工作量保存在下面完整明细的 components 字段。", "",
              "## 特殊操作", "", "abs/max/clamp、取整和 cast 单独统计，不能用 Tensor FLOPS 峰值统一换算。量化按有效元素计数；比较数包含每组 127 次归约与 1 次最小值约束。", "",
              "| 操作 | 次数或元素数 |", "|---|---:|"]
    # Insert projection/expert rows before the special-operation section.
    section = lines.index("## 特殊操作")
    matrix_lines = ["## 内部投影与专家矩阵", "",
        "M 为该层汇总的实际调用行数；路由专家按实际选中行累计，权重副本数另列。注意力 QK/PV 与 mHC 不在此投影表内，仍单独保存在完整明细中。", "",
        "| 部分/矩阵 | 汇总 M | K | N | 访问权重副本 | 矩阵 FLOPs |",
        "|---|---:|---:|---:|---:|---:|"]
    for component in ("attention", "experts"):
        for row in result["components"][component]["matrices"]:
            matrix_lines.append(f"| {component}/{row['name']} | {row['rows_summed_per_layer']:,} | {row['input_width']:,} | {row['output_width']:,} | {row['visited_copies_per_layer']:,} | {row['matrix_flops']:,} |")
    matrix_lines += ["", "## mHC 操作", "",
        "| 操作 | 矩阵 FLOPs | 标量 FLOPs |", "|---|---:|---:|"]
    for row in result["components"]["hyper_connections"]["residual_operations"]:
        matrix_lines.append(f"| {row['name']} | {row['matrix_flops']:,} | {row['scalar_flops']:,} |")
    matrix_lines.append("")
    lines[section:section] = matrix_lines
    for key, value in sorted(summary["special_ops"].items()):
        lines.append(f"| {key} | {value:,} |")
    lines += ["", "## 独立缓存与访存边界", "",
              f"有效 KV：调用前 {result['state']['valid_window_before_bytes']:,} bytes，调用后 {result['state']['valid_window_after_bytes']:,} bytes；本次 ring 写入 {result['state']['cache_write_bytes']:,} bytes。", "",
              "MTP 的 ring 与主干各层分开。接口字节仅覆盖指定操作数，完整 HBM 流量、运行时峰值和延迟保留未知。", "",
              "## 完整计算明细", "", "```json", json.dumps(result, indent=2, allow_nan=False), "```", ""]
    return "\n".join(lines)
