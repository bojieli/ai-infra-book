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
                              routing=routing, counts=counts, output_head="each sequential call",
                              allocated_max_seq_len=allocated_max_seq_len,
                              allocated_max_batch_size=allocated_max_batch_size),
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
