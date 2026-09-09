# Admitted arithmetic names and evidence

The public candidate invokes request_model_comparison once, retaining original_request in full. No changes to its scores, cache or heads are made. Every mapped call asserts classified+unclassified matrix sum equals the corresponding original call. Per-request scalar and named-special counts also conserve exactly.

| Model and original path/name | Resource bucket | Evidence/admission boundary |
|---|---|---|
| Qwen operators linear/QK except PV | matrix_bf16 | Original Scenario uniform BF16 inputs/weights, explicit FP32-acc Tensor interpretation; not actual backend evidence |
| Qwen operators[name=pv] | matrix_pv_mixed_or_unresolved | P=FP32 default score_bytes4, V=BF16; positive work, no rate; no implicit cast |
| V4 attention matrices wq_a/wq_b/wkv_shared/wo_b/index_wq_b | matrix_fp8 | model.py Linear selected default dtype/config; linear weight FP8 → act_quant + fp8_gemm |
| V4 attention wo_a_grouped/index_weights_proj | matrix_bf16 | model.py explicit BF16 wo_a; index weights projection BF16 selected source |
| V4 attention compress_r4/r128_wgate/wkv, index_compress_wgate/wkv | matrix_fp32 | explicit FP32 compressor linears |
| V4 attention group qk_and_pv_matrix_flops / actual_index_rectangular_matrix_flops | matrix_bf16 | sparse/index kernels selected input arithmetic; effective work only, no duplicate padded kernel total |
| V4 expert routed_gate/up/down/shared_gate/up/down | matrix_fp8 | Selected Linear/kernel; routed FP4 unpack converts to FP8 GEMM, not FP4 compute peak |
| V4 expert router, hyper_connections residual_operations, last_logits | matrix_fp32 | FP32 explicit source arithmetic; IEEE vector provider remains caller switch, no TF32 inference |
| K3 expert matrices[name=router] | matrix_fp32 | modeling_kimi_linear.py KimiMoEGate F.linear inputs/weight dtype float32 |
| K3 matrix_components (expert component minus above router) | unclassified_matrix | Declared uniform storage is not sufficient runtime input/accumulator evidence; keep every other positive matrix amount unclassified |

Both fixed V4 Flash and Pro inference/model.py files are byte-identical SHA ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71. Their configurations and actual matrix records differ and are read independently. No Flash multiplier estimates Pro. The mapper enumerates each model's real names/shapes and layer_ids; an unrecognized attention/expert matrix becomes unclassified, not automatically admitted FP8.

V4 decode uses its original static_base_forward matrix records and v4_prefix_continuation.attention_step with the actual per-call input position. Only dynamic selected-attention/index groups are substituted; their layer IDs and compression ratios come from the original template. The complete original decode/compression/cache allocation record is retained. K3 decode uses original first-call matrix_components; the already declared historical slope belongs to MLA, so the other components stay fixed and the residual MLA total is explicitly checked nonnegative. All those nonrouter matrices remain unclassified.

FP32 arithmetic and scalar ordinary FLOPs are separately labeled. With both vector-provider switches enabled, they share one vector resource; they are not two independent66.9TF/s engines. Named exp/sigmoid/rsqrt/compare/mask etc remain separate unknown-rate resources. No fake special provider is offered. Physical HBM work is null regardless of interface-normalized numbers; the interface views overlap and cannot be summed into HBM.

H100 selection uses hardware.select_peak(BF16,FP32,tensor,dense), FP8 counterpart and (FP32,FP32,vector,dense), retaining the full selected records/supporting evidence. Nominal capacity remains separate from the explicit scenario override. V4 cache allocation may independently exceed that limit, while checkpoint-storage size is not a proved runtime minimum. K3 A_log mismatch prevents checkpoint execution admission. No complete runtime/quality ranking is returned.
