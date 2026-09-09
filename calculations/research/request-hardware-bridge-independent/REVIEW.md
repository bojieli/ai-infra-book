# Request hardware bridge: finite independent review passed

Frozen SHA starts `293e8259`; the full SHA is bound in verification.json. All 26 candidate dependency bindings match current files. Four author tests pass with no skips. Independent review passes 1,086 comparisons, including all four frozen scene results and six complete V4 single-token forward recalculations. No public or author file was modified.

The four scene replays use their retained original_request as the immutable input contract, avoiding redundant checkpoint scans. JSON normalization only converts ordinary Python tuple shapes to arrays; no numeric tolerance is required. Every call preserves original matrices, ordinary scalar counts, each named special count and known-interface fields. Per-request sums conserve the complete original totals, and G1 produces one call rather than adding a decode.

## Precision classification and actual V4 records

Qwen PV is positive `matrix_pv_mixed_or_unresolved` with null rate. Independently, its useful work per call is `2×36×32×128×pairs`, with pairs=128×129/2 for prefill and 129,130,131 for the three decodes. No BF16 cast is silently inserted into the original FP32 P/BF16 V interface. Other admitted Qwen matrices retain the explicit uniform BF16 arithmetic interpretation, not an assertion of backend execution.

For each Flash and Pro decode at input positions 128,129,130, an independent full v4_forward call produced exactly the same individual matrix records as the candidate's static-base plus dynamic-attention composition. This includes names, source paths, layer_ids and amounts. Thus Pro is evaluated from its actual records, not a Flash scale factor, and the position-sensitive compression/index contributions agree with full calls. No sparse-kernel padded work is added to useful matrix totals.

The fixed Pro model source dispatches float4 weights via act_quant to fp4_gemm; its kernel explicitly casts FP4 weights through FP32 into FP8 shared operands before T.gemm (kernel.py around lines 492–514). The matrix_fp8 classification therefore does not confuse FP4 storage with FP4 execution. The indexer states BF16 current cache execution despite quantization simulation (model.py around 416–422), consistent with the BF16 index bucket. Float32 compressor linears are explicit in model.py:297–298. The same fixed model function source is shared by Flash and Pro; configuration and layer record multiplicities remain model-specific.

K3 admits only source-defined FP32 router arithmetic to matrix_fp32; every other matrix stays in unclassified_matrix, which remains positive. Matrix component subtraction removes the router exactly once. Its A_log shape-conflict admission remains explicit and no total K3 matrix rate is invented. FP32 matrix and ordinary-scalar providers are independent caller switches; enabling both adds their demands into one vector_fp32 resource, rather than creating two 66.9-TFLOP/s engines.

All selected hardware rows retain dense sparsity and FP32 nominal accumulation, with full supporting evidence. No matrix_fp4 rate appears. Structured sparsity, TF32 substitution, unknown special-operation rates and proof of H100 execution compatibility are not inferred. BF16/FP8 normalized budgets and their maximum remain a partial arithmetic bound; they do not establish independent simultaneously saturable physical Tensor engines or an achievable schedule.

## Capacity, interfaces and unknowns

Qwen necessary bytes equal resident uniform BF16 weights plus final logical state, without multiplying weights by call count. Independent exact/−1/+1-byte tests pass the necessary boundary correctly. Activations, allocator and workspace are still absent; necessary_only is not runtime admission.

V4 exposes checkpoint payload, final logical state and source cache allocation as separate representations. Its complete runtime necessary bytes remain null; only a source cache allocation exceeding the scenario limit may independently fail. The low-capacity scene exercises this condition. K3 retains checkpoint_shape_conflict and null runtime necessary bytes. Oversized storage comparisons do not manufacture a TP/EP/PP placement.

Every call's physical_hbm_bytes is null. Known overlapping/alternative interfaces remain verbatim and their denominator-normalized values explicitly say physical_resource unspecified. They are not summed into HBM traffic. S0 yields only prefix-restore payload zero; complete link bytes and seconds stay null without a placement/offload/topology contract. Full accounted serial-stage bounds and complete runtime remain null in all four scenes, even with vector providers enabled, because named special rates and physical work are still missing. No model ranking or quality equivalence is emitted.

No blocking mathematical, precision or admission issue was found within this finite bridge. This is a request resource classification and conditional arithmetic comparison, not completion of Experiment 2-9's quality-constrained hardware selection experiment.

Re-run `PYTHONDONTWRITEBYTECODE=1 python calculations/research/request-hardware-bridge-independent/check.py`. The verification file records all scene bucket summaries and each complete V4 decoder cross-check; source-verification.json records the 26 checked dependency bindings.
