"""Resident state and selected-history payloads, without conflating the two.

Length N means the state after N tokens have been processed. Query payloads are
for the query at position N-1 (visible length N). Appends describe the next token.
This module is intentionally separate from full forward FLOPs and kernel IO.
"""
from collections import Counter

from ..sources import model_config, provenance
from ..units import positive_int


def calculate(model: str, length: int, batch: int = 1, element_bytes: int = 2,
              recurrent_bytes: int = 4, mla_path: str = "compact") -> dict:
    for key, value in (("length", length), ("batch", batch), ("element_bytes", element_bytes),
                       ("recurrent_bytes", recurrent_bytes)):
        positive_int(value, key)
    if mla_path not in ("compact", "expanded"):
        raise ValueError("mla_path must be compact or expanded")
    config = model_config(model)
    result = {"schema_version": 1, "calculation": "model-state", "model": model,
              "scenario": {"length": length, "batch": batch, "element_bytes": element_bytes,
                           "recurrent_bytes": recurrent_bytes, "mla_path": mla_path},
              "sources": provenance(model), "assumptions": [
                  "N 为已处理 token 数；读取对应可见长度 N 的最后一条查询，append 对应第 N+1 个 token。",
                  "字节为未切分、无前缀共享的逻辑载荷；KV 各记录一次复用不代表实测 HBM。",
                  "不包含权重、attention 临时工作区、分配器对齐、并行复制、前缀检查点副本。",
              ]}
    if config["model_type"] in ("qwen3", "qwen3_moe"):
        if config.get("use_sliding_window"):
            raise ValueError("Sliding-window Qwen requires a separate state path")
        if length > config["max_position_embeddings"]:
            raise ValueError("Length exceeds unscaled config context limit")
        per_token = 2 * config["num_hidden_layers"] * config["num_key_value_heads"] * config["head_dim"] * element_bytes
        result["components"] = {"kv_history_bytes": batch * length * per_token}
        result["summary"] = {
            "resident_bytes": batch * length * per_token,
            "selected_history_payload_bytes": batch * length * per_token,
            "next_token_append_bytes": batch * per_token,
            "kv_bytes_per_token_per_request": per_token,
        }
    elif model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        reference = model_config(model, reference=True)
        result.update(v4_state(reference, length, batch, element_bytes))
        result["assumptions"].append("V4 的缓存为共享单表示；不额外乘 K/V 的 2。压缩器 kv_state/score_state 为参考代码 FP32 分配。")
    elif model == "kimi-k3":
        result.update(k3_state(config["text_config"], length, batch, element_bytes, recurrent_bytes, mla_path))
        result["assumptions"].extend([
            "KDA recurrent dtype 由场景显式输入；模型 BF16 不证明 recurrent state 也是 BF16。",
            "compact 是保留潜变量与额外分支的教学路径；expanded 才是固定 HF 参考实现保存的 K/V。",
            "短卷积按每 Q/K/V 通道保留 kernel_size 个元素的状态槽计算；需与目标 FLA 版本核对实际分配。",
        ])
    else:
        raise ValueError(f"State adapter not yet implemented for {model}; config download alone is not calculation support")
    return result


def v4_state(config: dict, length: int, batch: int, element_bytes: int) -> dict:
    layer_ratios = config["compress_ratios"][:config["n_layers"]]
    if len(layer_ratios) != config["n_layers"] or any(r not in (0, 4, 128) for r in layer_ratios):
        raise ValueError("Unsupported V4 layer/compressor configuration")
    width, window = config["head_dim"], config["window_size"]
    index_width, topk = config["index_head_dim"], config["index_topk"]
    rows = []
    for layer, ratio in enumerate(layer_ratios):
        compressed = length // ratio if ratio else 0
        indexed = compressed if ratio == 4 else 0
        selected = min(compressed, topk) if ratio == 4 else compressed
        window_entries = min(window, length)
        # Both FP32 state buffers have shape [B, coff*r, coff*d].
        coff = 2 if ratio == 4 else 1
        compressor_bytes = 2 * batch * (coff * ratio) * (coff * width) * 4
        index_compressor = 2 * batch * (coff * ratio) * (coff * index_width) * 4 if ratio == 4 else 0
        completes_next = bool(ratio and (length + 1) % ratio == 0)
        rows.append({
            "layer": layer, "kind": {0: "window", 4: "CSA", 128: "HCA"}[ratio], "ratio": ratio,
            "window_history_bytes": batch * window_entries * width * element_bytes,
            "compressed_history_bytes": batch * compressed * width * element_bytes,
            "index_history_bytes": batch * indexed * index_width * element_bytes,
            "main_compressor_buffer_bytes": compressor_bytes,
            "index_compressor_buffer_bytes": index_compressor,
            "main_selected_payload_bytes": batch * (window_entries + selected) * width * element_bytes,
            "index_scan_payload_bytes": batch * indexed * index_width * element_bytes,
            "last_query_main_qk_pv_flops": 4 * batch * config["n_heads"] * width * (window_entries + selected),
            "last_query_index_dot_flops": 2 * batch * config["index_n_heads"] * index_width * indexed,
            "next_token_window_write_bytes": batch * width * element_bytes,
            "next_token_completed_entry_write_bytes": batch * (width + (index_width if ratio == 4 else 0)) * element_bytes if completes_next else 0,
            "next_token_completes_compression": completes_next,
        })
    totals = {key: sum(row[key] for row in rows) for key in rows[0]
              if key.endswith(("bytes", "flops"))}
    history = sum(totals[key] for key in ("window_history_bytes", "compressed_history_bytes", "index_history_bytes"))
    buffers = totals["main_compressor_buffer_bytes"] + totals["index_compressor_buffer_bytes"]
    return {"layers": rows, "layer_counts": dict(Counter(row["kind"] for row in rows)),
            "components": totals,
            "summary": {"history_resident_bytes": history, "compressor_buffer_bytes": buffers,
                        "resident_bytes": history + buffers,
                        "selected_history_payload_bytes": totals["main_selected_payload_bytes"] + totals["index_scan_payload_bytes"]},
            "scope": "主干 0..n_layers-1；MTP 单列待算。窗口按有效内容，压缩器按完整槽分配；内部更新读写另算，非全部 decode IO/FLOPs。"}


def k3_state(config: dict, length: int, batch: int, element_bytes: int,
             recurrent_bytes: int, mla_path: str) -> dict:
    linear = config["linear_attn_config"]
    kda, mla = linear["kda_layers"], linear["full_attn_layers"]
    if sorted(kda + mla) != list(range(1, config["num_hidden_layers"] + 1)):
        raise ValueError("KDA/MLA lists must partition the actual layer indices")
    if length > config["max_position_embeddings"]:
        raise ValueError("Length exceeds pinned K3 context limit")
    dim, heads = linear["head_dim"], linear["num_heads"]
    recurrent = batch * len(kda) * heads * dim * dim * recurrent_bytes
    convolution = batch * len(kda) * 3 * heads * dim * linear["short_conv_kernel_size"] * element_bytes
    compact_width = config["kv_lora_rank"] + config["qk_rope_head_dim"]
    expanded_width = config["num_attention_heads"] * (config["qk_nope_head_dim"] + config["qk_rope_head_dim"] + config["v_head_dim"])
    width = compact_width if mla_path == "compact" else expanded_width
    per_token = batch * len(mla) * width * element_bytes
    return {
        "layer_counts": {"KDA": len(kda), "MLA": len(mla)},
        "components": {"kda_recurrent_bytes": recurrent, "short_conv_slots_bytes": convolution,
                       "mla_history_bytes": length * per_token},
        "summary": {"resident_bytes": recurrent + convolution + length * per_token,
                    "selected_history_payload_bytes": length * per_token,
                    "recurrent_read_once_write_once_bytes": 2 * recurrent,
                    "next_token_mla_append_bytes": per_token},
        "scope": "仅 text_config 的当前推理状态；不含视觉、AttnRes 激活、短卷积更新细节、MTP 或 prefix checkpoint 副本。",
    }
