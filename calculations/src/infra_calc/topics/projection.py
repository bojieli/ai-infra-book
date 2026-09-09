"""Cold-memory lower bounds for a real Qwen3 attention Q projection.

This is one GEMM, not a full forward or a measured kernel. A, W, and Y cross
the selected memory interface once; beta=0 and there is no old Y operand.
"""
from .. import hardware
from ..sources import model_config, provenance, records
from ..units import positive_int


def calculate(model: str, device: str, batch: int = 1, tokens: int = 1) -> dict:
    positive_int(batch, "batch")
    positive_int(tokens, "tokens")
    config = model_config(model)
    if config["model_type"] not in ("qwen3", "qwen3_moe"):
        raise ValueError("Q projection shapes currently support Qwen3 Dense/MoE only")
    if config.get("attention_bias", False):
        raise ValueError("Biased projections need a separate epilogue accounting")
    if tokens > config["max_position_embeddings"]:
        raise ValueError("Token count exceeds the pinned model context configuration")
    m, k = batch * tokens, config["hidden_size"]
    n = config["num_attention_heads"] * config["head_dim"]
    input_bytes, weight_bytes, output_bytes = 2 * m * k, 2 * k * n, 2 * m * n
    traffic = input_bytes + weight_bytes + output_bytes
    flops = 2 * m * k * n
    selected = hardware.select_device(device)
    execution_unit = "cube" if selected["vendor"] == "Huawei" else "tensor"
    bandwidth = selected["memory"]["bandwidth_bytes_per_second"]
    memory_seconds = traffic / bandwidth if bandwidth is not None else None
    try:
        peak = hardware.select_peak(selected, "BF16", "FP32", execution_unit, "dense")
    except ValueError as error:
        peak, reason = None, str(error)
    else:
        reason = None
    compute = peak["tera_ops_per_second"] * 10**12 if peak else None
    compute_seconds = flops / compute if compute else None
    # A system aggregate does not identify a placement for one projection.
    if selected["spec_scope"] != "single_device":
        raise ValueError("Q projection device mapping requires a single-device profile; distributed GEMMs need explicit sharding")
    roofline_seconds = max(memory_seconds, compute_seconds) if (
        memory_seconds is not None and compute_seconds is not None) else None
    sources = provenance(model) + [
        {key: row[key] for key in ("file", "url", "revision", "sha256")}
        for row in records() if row.get("id") in selected["source_ids"]]
    return {
        "schema_version": 1, "calculation": "q_projection_resource_bound", "model": model,
        "scenario": {"device": device, "batch": batch, "tokens": tokens,
                     "input_precision": "BF16", "accumulator_precision": "FP32",
                     "output_precision": "BF16", "execution_unit": execution_unit,
                     "sparsity": "dense", "beta": 0},
        "shapes": {"A": [m, k], "W_math": [k, n], "W_storage": [n, k], "Y": [m, n]},
        "selected_peak": peak, "unavailable_compute_reason": reason,
        "summary": {"matrix_flops": flops, "input_read_bytes": input_bytes,
                    "weight_read_bytes": weight_bytes, "output_write_bytes": output_bytes,
                    "cold_memory_payload_bytes": traffic,
                    "arithmetic_intensity_flops_per_byte": flops / traffic,
                    "compute_service_seconds": compute_seconds,
                    "memory_service_seconds": memory_seconds,
                    "roofline_lower_bound_seconds": roofline_seconds,
                    "ridge_point_flops_per_byte": compute / bandwidth if compute and bandwidth else None},
        "assumptions": [
            "仅一层 Q 投影 GEMM，M=B×T、K=hidden_size、N=query_heads×head_dim；Q width 不假定等于 hidden_size。",
            "A/W/Y 按 BF16 计、FP32 累加在片上、beta=0；不计 QK Norm、RoPE、其余层与输出头。",
            "冷内存情景：A/W 起始于所选显存/统一内存接口外侧，Y 最终写回该接口；各传一次是此情景的服务量下界。跨调用缓存命中不适用此输入。",
            "tile 重读、布局、量化、片上约束、启动、依赖和实际有效供给另算；本结果不是已实现 kernel 的预测。",
            "缺失匹配算力时只保留已知的 memory_service_seconds，roofline_lower_bound_seconds=null；不能称为完整 Roofline 或 GPU 性能。",
            "只使用单设备规格。名义容量、可分配空间和整模型驻留可行性不由此单 GEMM 验证。",
        ] + selected["notes"],
        "sources": sources,
    }
