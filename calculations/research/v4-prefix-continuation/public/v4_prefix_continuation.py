"""Sequential known-token V4 prefix continuation; not parallel chunk prefill."""
from collections import Counter
from copy import deepcopy

from infra_calc.sources import model_config
from infra_calc.units import positive_int
from infra_calc.topics import state, v4_attention_arithmetic
from infra_calc.topics import v4_forward, v4_sparse_kernel


def attention_step(config, batch, history, template):
    """Dynamic one-token work using already-loaded config and static projections."""
    end = history + 1
    groups = deepcopy(template["attention_layer_groups"])
    for row in groups:
        ratio = row["compress_ratio"]
        layers = len(row["layer_ids"])
        selected = min(end, config["window_size"])
        if ratio:
            selected += min(config["index_topk"], end // ratio) if ratio == 4 else end // ratio
        row["selected_attention_pairs_per_layer"] = batch * selected
        row["qk_and_pv_matrix_flops"] = 4 * layers * config["n_heads"] * config["head_dim"] * batch * selected
        index = 2 * layers * config["index_n_heads"] * config["index_head_dim"] * batch * (end // 4) if ratio == 4 else 0
        row["actual_index_rectangular_matrix_flops"] = index
        row["causal_index_matrix_flops"] = index
        row["completed_compressed_rows_per_request"] = int(bool(ratio and end % ratio == 0))
    arithmetic = v4_attention_arithmetic.calculate(config, batch, 1, history)
    kernel = v4_sparse_kernel.calculate(config, batch, 1, history, groups)
    projection = template["summary"]["projection_matrix_flops"]
    index = sum(x["actual_index_rectangular_matrix_flops"] for x in groups)
    effective = projection + index + sum(x["qk_and_pv_matrix_flops"] for x in groups)
    scalar = arithmetic["non_matrix_summary"]["scalar_flops"] + kernel["sparse_kernel_summary"]["online_softmax_scalar_flops"]
    special = Counter(arithmetic["non_matrix_summary"]["special_ops"])
    special.update(exp=kernel["sparse_kernel_summary"]["exp_ops"],
                   compare_max=kernel["sparse_kernel_summary"]["max_comparisons"])
    return dict(matrix=effective, tiles=projection + index + kernel["sparse_kernel_summary"]["matrix_flops"],
                scalar=scalar, special=special, groups=groups,
                arithmetic=arithmetic, kernel=kernel)


def calculate(model="deepseek-v4-flash", prefix_tokens=6144, new_tokens=2048,
              batch=1, routing="balanced", counts=None,
              allocated_max_seq_len=None, allocated_max_batch_size=None):
    for key, value in (("prefix tokens", prefix_tokens), ("new tokens", new_tokens), ("batch", batch)):
        positive_int(value, key)
    allocated_max_seq_len = prefix_tokens + new_tokens if allocated_max_seq_len is None else allocated_max_seq_len
    allocated_max_batch_size = batch if allocated_max_batch_size is None else allocated_max_batch_size
    positive_int(allocated_max_seq_len, "allocated max sequence length")
    positive_int(allocated_max_batch_size, "allocated max batch size")
    if allocated_max_seq_len < prefix_tokens + new_tokens or allocated_max_batch_size < batch:
        raise ValueError("Declared source cache allocation cannot contain this continuation")
    # Exactly one full ledger call: large checkpoint headers/index are never
    # reopened per continuation token. Static expert routing is a declared fixture.
    initial = v4_forward.calculate(model, batch, 1, prefix_tokens, routing, counts)
    c = model_config(model, reference=True)
    template = initial["components"]["attention"]
    first = attention_step(c, batch, prefix_tokens, template)
    static_matrix = initial["summary"]["matrix_flops_effective_attention"] - first["matrix"]
    static_tiles = initial["summary"]["matrix_flops_with_reference_sparse_and_expert_tiles"] - first["tiles"]
    static_scalar = initial["summary"]["accounted_scalar_flops"] - first["scalar"]
    static_special = Counter(initial["summary"]["accounted_special_ops"])
    static_special.subtract(first["special"])
    if min(static_special.values(), default=0) < 0:
        raise AssertionError("Static/dynamic special-function partition is inconsistent")
    steps = []
    totals = Counter()
    special_total = Counter()
    interface_total = Counter()
    boundary_lists = {ratio: [] for ratio in sorted(set(c["compress_ratios"][:c["n_layers"]])) if ratio}
    for offset in range(new_tokens):
        history = prefix_tokens + offset
        end = history + 1
        attention = first if offset == 0 else attention_step(c, batch, history, template)
        before = state.v4_state(c, history, batch, 2)
        after = state.v4_state(c, end, batch, 2)
        special = attention["special"] + static_special
        matrix = static_matrix + attention["matrix"]
        tiles = static_tiles + attention["tiles"]
        scalar = static_scalar + attention["scalar"]
        totals.update(matrix_flops_effective_attention=matrix,
                      matrix_flops_with_reference_sparse_and_expert_tiles=tiles,
                      accounted_scalar_flops=scalar,
                      vocabulary_head_matrix_flops=initial["summary"]["vocabulary_head_matrix_flops"])
        special_total.update(special)
        interfaces = {key: value for key, value in attention["kernel"]["sparse_kernel_summary"].items()
                      if key in ("gathered_kv_bytes", "query_read_bytes", "output_write_bytes", "index_read_bytes", "sink_read_bytes")}
        interfaces.update(
            embedding_lookup_payload_bytes=initial["summary"]["embedding_lookup_payload_bytes"],
            attention_uniform_bf16_matrix_weight_payload_bytes=2 * template["summary"]["matrix_parameters"],
            expert_uniform_bf16_matrix_weight_payload_bytes=initial["components"]["experts"]["summary"]["uniform_matrix_weight_payload_bytes"],
            routed_expert_actual_packed_and_scale_payload_bytes=initial["components"]["experts"]["routed_expert_format"]["summary"]["visited_weight_and_scale_payload_bytes"],
            hc_fp32_parameter_payload_bytes=initial["components"]["hyper_connections"]["summary"]["hc_fp32_parameter_bytes"],
            vocabulary_head_uniform_bf16_weight_payload_bytes=2 * c["dim"] * c["vocab_size"],
            window_slot_write_bytes=before["components"]["next_token_window_write_bytes"],
            completed_cache_entry_write_bytes=before["components"]["next_token_completed_entry_write_bytes"],
            index_scan_payload_bytes=after["components"]["index_scan_payload_bytes"],
        )
        slot_writes = 0
        overlap_copy = 0
        for ratio in c["compress_ratios"][:c["n_layers"]]:
            if ratio:
                coff = 2 if ratio == 4 else 1
                widths = c["head_dim"] + (c["index_head_dim"] if ratio == 4 else 0)
                slot_writes += 2 * batch * coff * widths * 4
                if ratio == 4 and end % ratio == 0:
                    overlap_copy += 2 * batch * ratio * coff * widths * 4
        interfaces.update(compressor_fp32_slot_write_bytes=slot_writes,
                          overlap_roll_fp32_read_bytes=overlap_copy,
                          overlap_roll_fp32_write_bytes=overlap_copy)
        interface_total.update(interfaces)
        completed = []
        for ratio in boundary_lists:
            if end % ratio == 0:
                boundary_lists[ratio].append(end)
                completed.append(ratio)
        steps.append(dict(step=offset, input_position=history, end_position=end,
                          completed_ratios=completed,
                          matrix_flops_effective_attention=matrix,
                          matrix_flops_with_reference_sparse_and_expert_tiles=tiles,
                          accounted_scalar_flops=scalar,
                          accounted_special_ops=dict(special),
                          known_interfaces=interfaces,
                          state_resident_after_bytes=after["summary"]["resident_bytes"]))
    before = state.v4_state(c, prefix_tokens, batch, 2)
    after = state.v4_state(c, prefix_tokens + new_tokens, batch, 2)
    allocation = state.v4_state(c, allocated_max_seq_len, allocated_max_batch_size, 2)
    allocated_cache_bytes = allocation["summary"]["resident_bytes"]
    allocated_cache_bytes += c["n_layers"] * max(0, c["window_size"] - allocated_max_seq_len) * allocated_max_batch_size * c["head_dim"] * 2
    return dict(schema_version=1, calculation="v4-sequential-prefix-continuation", model=model,
                scenario=dict(prefix_tokens=prefix_tokens, new_tokens=new_tokens, batch=batch,
                              routing=routing, counts=counts,
                              allocated_max_seq_len=allocated_max_seq_len,
                              allocated_max_batch_size=allocated_max_batch_size),
                execution=dict(output_head="each sequential call", parallel_cached_chunk=False),
                sources=initial["sources"], static_base_forward=initial,
                static_partition=dict(matrix_flops_per_call=static_matrix,
                                      matrix_flops_with_known_tiles_per_call=static_tiles,
                                      scalar_flops_per_call=static_scalar,
                                      special_ops_per_call=dict(static_special)),
                steps=steps, compression_boundaries={str(k): v for k, v in boundary_lists.items()},
                initial_state=before, final_state=after,
                source_cache_allocation=dict(max_seq_len=allocated_max_seq_len,
                                             max_batch_size=allocated_max_batch_size,
                                             bf16_history_and_fp32_compressor_bytes=allocated_cache_bytes,
                                             scope="Full reference cache/compressor buffers only; frequency tables, weights and other temporaries excluded"),
                summary=dict(totals, accounted_special_ops=dict(special_total),
                             known_interface_totals=dict(interface_total),
                             forward_calls=new_tokens, vocabulary_head_calls=new_tokens,
                             useful_final_vocabulary_heads=1,
                             discarded_intermediate_vocabulary_heads=new_tokens - 1,
                             initial_state_resident_bytes=before["summary"]["resident_bytes"],
                             final_state_resident_bytes=after["summary"]["resident_bytes"],
                             state_growth_bytes=after["summary"]["resident_bytes"] - before["summary"]["resident_bytes"],
                             complete_hbm_traffic_bytes=None, complete_runtime_resident_bytes=None,
                             complete_scalar_flops=None, predicted_latency_seconds=None),
                coverage=dict(full_base_matrix_graph=True, parallel_cached_chunk=False,
                              unknown=[x for x in initial["coverage"]["missing"] if x != "MTP separate forward and multi-token cached-prefix execution path"] + [
                                  "MTP separate forward; parallel multi-token cached-prefix execution remains unsupported",
                                  "prefix snapshot creation/lookup/transfer/restoration work",
                                  "actual token-dependent expert histogram: declared per-step fixture only",
                                  "complete source data movement, transient allocation and physical runtime traffic"]),
                assumptions=[
                    "Declared max_seq_len/max_batch_size override ModelArgs defaults (4096/4) as needed; the default book request explicitly budgets allocation to 8192/1. Sufficient allocation and device capacity must be established before source execution.",
                    "Prefix state must already be materialized at the exact boundary, including window ring layout, compressed/index caches, FP32 compressor kv/score slots and overlap carry. Prefix length alone cannot reconstruct it.",
                    "Known suffix input tokens run one at a time at positions prefix..prefix+new_tokens-1; no generated-token sampling or parallel chunk claim. All layers and head execute each call as in the pinned base Transformer.forward.",
                    "Each intermediate vocabulary head is real reference work even though its logits are discarded. The final head can supply the first future output token; that subsequent output generation is not included.",
                    "Routing histogram and dtype/tile assumptions are identical on every step, expressly a workload fixture. Real hash/scoring routing can differ across input tokens and requires recorded per-step counts for exact expert reuse.",
                    "Dynamic attention includes compressor boundaries and changing scan lengths; expert/mHC/external norm/head work is reused as a per-call static budget, not treated as zero. Checkpoint parsing occurs once.",
                    "Uniform BF16 matrix weight columns are comparison-format reads; routed actual packed+scale is an alternative subset, not additive with the uniform expert column. Norm-vector and all runtime conversions are not a complete weight-read ledger.",
                    "Known interface columns belong to distinct semantic operations; gathered KV includes currently visible entries, not only prior history. Do not call their sum HBM or subtract it from final state.",
                    "FP32 compressor slots and BF16 reference cache are retained-state accounting, not actual FP8/FP4 resident cache, maximum preallocation or allocator peak. State growth excludes overwrite writes.",
                    "Existing base-forward partial scalar/format coverage is preserved; this continuation schedule does not magically close its unknown fields.",
                ])


def markdown(result):
    """Lossless readable rendering; repeated per-step vectors use explicit IDs."""
    import json

    def cell(value):
        if value is None:
            return "unknown"
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    def table(headers, rows):
        return ["| " + " | ".join(headers) + " |",
                "| " + " | ".join("---" for _ in headers) + " |",
                *("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)]

    def pairs(mapping):
        return list(mapping.items())

    lines = [f"# {result['model']}：顺序前缀延续", "",
             "已知后缀逐 token 执行完整基础 forward；不是并行 cached chunk。所有数值沿 JSON 的声明口径，无实际 HBM 或延迟推断。", "",
             "## 请求与源分配条件", ""]
    lines += table(["输入", "值"], pairs(result["scenario"]))
    lines += ["", "源 ModelArgs 默认 max_seq_len=4096/max_batch_size=4；此场景明确覆盖分配参数。完整前缀快照必须包含 window 环形布局、压缩/index cache、FP32 kv/score 槽和重叠 carry。", ""]
    lines += table(["源分配字段", "值"], pairs(result["source_cache_allocation"]))
    lines += [""]
    lines += table(["固定执行方式", "值"], pairs(result["execution"]))
    summary = result["summary"]
    lines += ["", "## 汇总", ""]
    lines += table(["指标", "值"], [(k, v) for k, v in summary.items() if not isinstance(v, dict)])
    lines += ["", "## 全段特殊调用与非 FLOPs 操作", "",
              "名称表示各自运算/候选/编码/比较次数，不能作为统一 Tensor FLOPs 相加。", ""]
    lines += table(["操作", "次数"], pairs(summary["accounted_special_ops"]))
    lines += ["", "## 已知接口总量", "",
              "各字段单位为 bytes。uniform BF16 专家列与 routed actual packed+scale 是替代口径，不得相加。gather 包含当前可见记录；FP32 slot/roll、状态增长和最终驻留均是不同量。", ""]
    lines += table(["接口字段", "bytes"], pairs(summary["known_interface_totals"]))
    lines += ["", "## 静态每调用分区与基础权重", ""]
    lines += table(["分区", "值"], pairs(result["static_partition"]))
    base = result["static_base_forward"]
    lines += ["", "静态分区每一步都执行，checkpoint 只解析一次。以下保留完整基础参数分项，未把基础 checkpoint 载荷当运行时实际常驻。", ""]
    lines += table(["基础参数分项", "参数数"], pairs(base["parameter_components"]))
    lines += ["", "## 压缩完成边界", "",
              "位置均为处理后的 end_position=input_position+1。列表完整，无省略。", ""]
    lines += table(["ratio", "完成次数", "全部结束位置"],
                   [(k, len(v), v) for k, v in result["compression_boundaries"].items()])
    lines += ["", "## 初始与最终有效状态", ""]
    for label, state_result in (("初始", result["initial_state"]), ("最终", result["final_state"])):
        lines += ["", f"### {label}", ""]
        lines += table(["summary 字段", "值"], pairs(state_result["summary"]))
        lines += [""]
        lines += table(["component 字段", "值"], pairs(state_result["components"]))
        layers = state_result["layers"]
        lines += [""]
        lines += table(list(layers[0]), [[row[k] for k in layers[0]] for row in layers])
    # Vectors repeat across steps; retain a bijective ID map rather than truncate.
    registries = {"special": {}, "interface": {}}
    vectors = {"special": [], "interface": []}
    step_rows = []
    for row in result["steps"]:
        ids = {}
        for kind, field in (("special", "accounted_special_ops"), ("interface", "known_interfaces")):
            key = json.dumps(row[field], sort_keys=True)
            if key not in registries[kind]:
                identifier = f"{kind}-{len(vectors[kind])}"
                registries[kind][key] = identifier
                vectors[kind].append((identifier, row[field]))
            ids[kind] = registries[kind][key]
        step_rows.append([row["step"], row["input_position"], row["end_position"], row["completed_ratios"],
                          row["matrix_flops_effective_attention"], row["matrix_flops_with_reference_sparse_and_expert_tiles"],
                          row["accounted_scalar_flops"], row["state_resident_after_bytes"], ids["special"], ids["interface"]])
    lines += ["", "## 每一步工作与状态", "",
              "special/interface ID 指向下方完整字典；相同向量复用 ID，逐步映射和所有字段保留。矩阵/scalar 单位 FLOPs，状态单位 bytes。", ""]
    lines += table(["step", "输入位置", "结束位置", "完成ratio", "有效矩阵", "已知tile矩阵", "已计scalar", "末状态bytes", "特殊操作ID", "接口ID"], step_rows)
    for kind in ("special", "interface"):
        lines += ["", f"## {kind} 完整向量定义", ""]
        definitions = [[identifier, name, count] for identifier, vector in vectors[kind] for name, count in vector.items()]
        lines += table(["ID", "操作/字段", "次数" if kind == "special" else "bytes"], definitions)
    lines += ["", "## 覆盖范围与 unknown", ""]
    lines += table(["字段", "值"], [(k, v) for k, v in result["coverage"].items() if k != "unknown"])
    lines += ["", *("- " + item for item in result["coverage"]["unknown"]), "",
              "## 假设", "", *("- " + item for item in result["assumptions"]), "",
              "## 固定来源", ""]
    lines += table(["来源记录", "值"], [(str(i), item) for i, item in enumerate(result["sources"])])
    return "\n".join(lines) + "\n"
