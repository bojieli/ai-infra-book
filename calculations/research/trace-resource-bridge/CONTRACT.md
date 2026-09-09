# T05 sealed Chat capture → Qwen8 logical resources

Select only the four original chat_capture records in experiments/ch02/02-08, not its 24 routing replays or synthetic request_trace. These captures used Qwen3-8B snapshot b968826d9c46dd6066d109eabc6255188de91218, SGLang BF16, temperature0/max_new_tokens96. The captured HTTP calls and source execution arguments are evidence; they are not a per-kernel trace.

| Mapping | Sealed evidence | Interpretation |
|---|---|---|
| Input length N | prompts.json input_ids length equals response.meta_info.prompt_tokens | Recorded tokenized input count |
| S | response.meta_info.cached_tokens | Reported cached input count; using it as logical retained prefix is explicit accounting mapping, not verified GPU KV page identity |
| P | N−S | Logical uncached-input token count |
| Returned IDs | response.output_ids | Raw returned stream, includes EOS |
| Completion metric | meta_info.completion_tokens | Cross-check equals returned IDs; not independent proof of scheduler/model forward invocations |
| Application calls | Four prompt records plus received/finished worker records | Four archived HTTP generation requests, not four model forwards |
| G / decode calls | Not directly recorded per forward | Default unknown. Optional returned_ids_serial_policy assumes one sampled step per returned ID, then D=G−1; explicitly conditional, never observed runtime calls |
| Useful answer tokens | Returned IDs except EOS/markers | Do not use for G or remove EOS from resource demand |
| Model seconds | end_s−start_s and engine meta latency | Recorded walls, separate from calculated resource volume |
| Tool waiting | Chat source has no tools; profile tool_s=null | Remains null; no invented zero-duration tool observation |
| Cross-request reuse | Worker/completion/send evidence | Preserve observed gap; no block lifetime or shared-KV peak inferred |

Compute Qwen8 per-call logical prefill from S/P with generation-mode last-position head using public qwen3.calculate. No prefix warmup is added to a cached-prefix request. Known prefill matrix, accounted scalar/special, operator-interface bytes and post-prefill BF16 KV state are always provided. Default complete-generation work remains null because returned IDs do not establish actual sampling/model invocation counts. A separate explicit serial policy supplies conventional G=returned IDs and D=G−1; each decode consumes previous token at growing history. The final emitted token (including EOS) is not automatically processed into KV. This is a reproducible policy substitution on real recorded lengths, not replacement of the sealed trace with a teaching trace.

The conditional per-forward sequence reuses request_model_comparison helpers but limits calculation to Qwen8. Aggregate matrix/interfaces sum per request/call; state bytes are endpoint values and their sums are not called simultaneous peak. Scalar/backend coverage stays as the public model contract, interfaces are not HBM, and recorded timing is never divided into a GPU throughput claim. Full kernel work/runtime remains unknown under both policies.

Minimum additional logging for actual runtime reconstruction: admitted prefix token IDs/page mapping and per-scheduled-step input token positions; sampled IDs and acceptance/retraction events; generated-token/EOS processing boundary; prefill chunks and logits-row selection; speculative/MTP/beam paths; KV allocation/eviction timeline. No new model run is required for this candidate, and none is performed.
