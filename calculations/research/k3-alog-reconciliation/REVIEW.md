# C11 Kimi K3 A_log reconciliation

The fixed official checkpoint and fixed official model constructor conflict. This is a **specific vector parameter-shape discrepancy**, with a precisely known parameter/storage delta. It is not evidence that KDA has 128 heads, not MXFP4 packing, and not resolved by the FLA state-layout keyword alias. No official conversion or checkpoint-loading repair was found in the inspected fixed sources. Shared code/configuration were not changed.

## Evidence and bounded freshness

All model/config/index/header files use Moonshot's Kimi-K3 revision `f831ab66814297da540d832a5235f8e904f29d06`. The audit re-verified all 96 shard headers and all 497,220 index names, then ran the public full checkpoint validator (shape/dtype/offset/packed-expert/index-total checks). Each of the 69 KDA layers has its actual A_log header and neighbouring projection geometry listed in reconciliation.json. Every input SHA is bound in source-bindings.json.

The existing official Hub API observation at 2026-09-09 03:51:53 UTC reports the same revision. Its saved API bytes and SHA were independently checked, so no changed revision required new config/header downloads. This establishes freshness at that recorded observation, not a promise that main can never change. A new web-tool API open during this task was blocked as unsafe; it is not used as affirmative evidence. No additional sources or weight payloads were downloaded.

## What exactly differs

| Quantity | Fixed config/constructor | Actual fixed checkpoint |
|---|---:|---:|
| KDA heads | 96 | Neighbouring Q/K/V/beta/dt_bias shapes support 96 |
| Per-head channel dimension | 128 | Q/K/V width 12,288 = 96×128 |
| A_log per KDA layer | FP32 [96] | FP32 [128] |
| All 69 A_log elements | 6,624 | 8,832 |
| Extra checkpoint elements | — | 2,208 |
| Extra checkpoint FP32 payload | — | 8,832 bytes |

`modeling_kimi_linear.py:485–521` constructs `self.num_heads` from config and allocates A_log with exactly that many entries. Every affected layer independently has Q/K/V and full-rank gate shapes [12,288,7,168], beta projection [96,7,168], f_b [12,288,128], output [7,168,12,288] and dt_bias [12,288]. A_log's stored length happens to equal the channel dimension 128; this coincidence is not proof of intended channelwise semantics.

Config logical text parameters are 2,779,484,476,000. The unpacked checkpoint text parameters excluding quantization scales are 2,779,484,478,208. The exact difference is explained by these 69 vectors alone. A_log is F32, so routed-expert U8/MXFP4 packing does not explain its length. Entire checkpoint payload accounting remains exact regardless of the loadability conflict.

## Runtime and backend boundaries

1. `use_cache = cache_params is not None`; one query token with cache chooses fused_recurrent. Without cache, including one token, the configured chunk path is used. Training asserts chunk mode. Existing forward auto selection is explicitly a mathematical comparison rule, not a promise that T=1 always dispatches recurrent at runtime.
2. Pinned FLA's public gate reference uses `A_log.view(H,1)` with H inferred from g's head dimension. Extracting that exact official function and passing synthetic g [1,1,96,128] succeeds with a 96-vector and fails with a 128-vector. reference-probe.json records the actual Torch 2.7.0 errors. An ordinary parameter load likewise rejects [128] into [96] even with strict=False; this is a small loader-contract probe, not an attempted full K3/HuggingFace load.
3. Fused gate/recurrent kernels load A_log by head index (`A_log+i_h` / `A_log+i_hv`). A buffer with at least 96 entries may therefore be addressable on a forward path. This proves neither a legal loader nor that the extra 32 entries are padding or semantically discardable. Payload values were not read. Backward gate reduces H gradients and then `view_as(A_log)`, so forward addressability does not establish gradient-shape compatibility.
4. Both pinned chunk and recurrent wrappers explicitly map deprecated `transpose_state_layout` to `state_v_first`. This keyword/layout alias is known, and cannot reconcile 128 parameter elements with 96. The chosen FLA commit remains an explicitly selected dependency source, not proof of the actual installed K3 release environment or CUDA/Triton behavior.

## Calculations that remain valid

* Checkpoint tensor payload, dtype groups, quantized expert geometry and component storage are independently valid header/index facts.
* Config-defined projections, 96-head recurrent/chunk mathematical work, convolution geometry and state are valid declared logical calculations. All 69 KDA states use 69×B×96×128×128×4 bytes; B=1 is 434,110,464 bytes. Increasing head count to128 would incorrectly increase state and most KDA work by one third.
* The A_log parameter difference changes checkpoint count/bytes, not the config-derived active-head arithmetic. Its unknown intended values prevent a verified numerical checkpoint execution claim.
* Current k3_forward correctly propagates mismatch and exposes separate config/checkpoint parameter totals, with actual runtime/traffic/latency unknown. This audit does not override that protection.

## Finite recommendations

1. Keep the 69 explicit mismatches and exact 2,208/8,832 deltas. Do not slice/reinitialize/broadcast A_log, change heads, or call tail entries padding without an official loader/conversion contract and numerical evidence.
2. Update only the stale k3_kda assumption claiming the state-layout API differs without compatibility: the pinned alias has now been verified. Suggested exact wording is in recommendations.json. This is a documentation correction, not a shape fix or proof of the full runtime dependency.
3. If C11 later adds a runnable checkpoint backend, require either a subsequent fixed official source/checkpoint revision that matches or an explicitly documented converter. Validate all 69 resulting parameter shapes and a source-prescribed numerical transition before claiming compatibility. Existing inspection contains no such fix, so the loadability gate remains false.
4. Do not mark the whole C11 complete: mixed-format conversion, backend/tile work and full runtime allocation are independent remaining scope. Conversely, do not mark the already exact checkpoint storage or config mathematical account invalid merely because loading is unresolved.

This is a completed bounded source reconciliation with an unresolved official conflict, not a guessed repair.
