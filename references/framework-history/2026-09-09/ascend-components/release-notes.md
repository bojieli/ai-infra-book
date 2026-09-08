# Release Notes

## v0.26.0rc1 - 2026.09.03

This is the first release candidate of v0.26.0 for vLLM Ascend, aligned with upstream vLLM v0.26.0. This release is a model‑restricted version. Fully validated models include Kimi K3, GLM‑5.2, DeepSeek V4 Flash 0731, DeepSeek V4 Pro 0813. Availability is not guaranteed for other models. For the full test report, see: [v0.26.0rc1 Test Conclusion](https://github.com/vllm-project/vllm-ascend/blob/releases/v0.26.0rc/tests/vllm_ascend_v0.26.0rc1_test_conclusion.md). Please follow the [official documentation](https://docs.vllm.ai/projects/ascend/en/v0.26.0rc1/) to get started.

### Highlights

- **Kimi K3 on Ascend**: Added end-to-end Kimi K3 support, including MLA DSpark speculative decoding, no-RoPE MLAPO on Ascend 950, fused QKV projections, fused norm gate and attention residual, and projector rotation. [#12950](https://github.com/vllm-project/vllm-ascend/pull/12950) [#13277](https://github.com/vllm-project/vllm-ascend/pull/13277) [#13507](https://github.com/vllm-project/vllm-ascend/pull/13507) [#13989](https://github.com/vllm-project/vllm-ascend/pull/13989) [#13509](https://github.com/vllm-project/vllm-ascend/pull/13509) [#14231](https://github.com/vllm-project/vllm-ascend/pull/14231)
- **GLM-5.2 / DeepSeek V4 Flash 0731 / DeepSeek V4 Pro 0813 accuracy and performance**: Resolved GLM-5.2 DSpark acceptance regressions and DeepSeek V4 Flash-0731 / Pro-0813 accuracy issues (reasoning-effort alignment, routed SwiGLU limit, and frontend behavior), and reused DSV4 compressor metadata across layers for better performance. [#12262](https://github.com/vllm-project/vllm-ascend/pull/12262) [#13531](https://github.com/vllm-project/vllm-ascend/pull/13531) [#13993](https://github.com/vllm-project/vllm-ascend/pull/13993) [#14074](https://github.com/vllm-project/vllm-ascend/pull/14074) [#14397](https://github.com/vllm-project/vllm-ascend/pull/14397) [#14624](https://github.com/vllm-project/vllm-ascend/pull/14624) [#14994](https://github.com/vllm-project/vllm-ascend/pull/14994)
- **DeepSeek V4 DSpark**: Refactored DSv4 DSpark speculative decoding with aligned SP handling and QuaRot weight support for Qwen3 DSpark. [#11431](https://github.com/vllm-project/vllm-ascend/pull/11431) [#12662](https://github.com/vllm-project/vllm-ascend/pull/12662)
- **Sparse-attention context parallelism**: Added SFA DCP with a replicated indexer, compact KV gather, and C8 support. Enabled P/D disaggregation for DCP with replicate-indexer. [#11443](https://github.com/vllm-project/vllm-ascend/pull/11443) [#11870](https://github.com/vllm-project/vllm-ascend/pull/11870) [#11980](https://github.com/vllm-project/vllm-ascend/pull/11980) [#11696](https://github.com/vllm-project/vllm-ascend/pull/11696)
- **Deprecation cleanup**: Removed layer sharding, FlashComm2, multistream overlap gate, dynamic-batch SLO, weight prefetch, matmul all-reduce fusions, and kv offload in KV Pool to streamline the codebase. [#11953](https://github.com/vllm-project/vllm-ascend/pull/11953) [#12117](https://github.com/vllm-project/vllm-ascend/pull/12117) [#11956](https://github.com/vllm-project/vllm-ascend/pull/11956) [#11933](https://github.com/vllm-project/vllm-ascend/pull/11933) [#11949](https://github.com/vllm-project/vllm-ascend/pull/11949) [#12119](https://github.com/vllm-project/vllm-ascend/pull/12119) [#11904](https://github.com/vllm-project/vllm-ascend/pull/11904)

### Features

- Added LoRA with unquantized MoE models and AlltoAll + EP + LoRA support. [#10977](https://github.com/vllm-project/vllm-ascend/pull/10977) [#12451](https://github.com/vllm-project/vllm-ascend/pull/12451)
- Added Gemma4 E2B and E4B model support with graph execution on A2/A3 and ModelSlim quantization. [#11536](https://github.com/vllm-project/vllm-ascend/pull/11536) [#11575](https://github.com/vllm-project/vllm-ascend/pull/11575) [#11791](https://github.com/vllm-project/vllm-ascend/pull/11791)
- Added Step3.5/3.7 Flash support for Ascend 950. [#10556](https://github.com/vllm-project/vllm-ascend/pull/10556)
- Added KV sliding window for Eagle3 and DFlash. [#10023](https://github.com/vllm-project/vllm-ascend/pull/10023)
- Added ShortRequestFirst scheduling and batch job aware scheduler. [#11576](https://github.com/vllm-project/vllm-ascend/pull/11576) [#12240](https://github.com/vllm-project/vllm-ascend/pull/12240) [#12719](https://github.com/vllm-project/vllm-ascend/pull/12719)
- Added NZ static buffers for prefetch offload. [#11945](https://github.com/vllm-project/vllm-ascend/pull/11945)
- Added update config and reload weights to NPU Worker. [#10126](https://github.com/vllm-project/vllm-ascend/pull/10126)
- Added SFA C8 support: unified packed KV cache layout on A3, and DCP replicated indexer for sparse‑attention paths. [#11228](https://github.com/vllm-project/vllm-ascend/pull/11228) [#11870](https://github.com/vllm-project/vllm-ascend/pull/11870)

### Hardware and Operator Support

- Expanded Ascend 950 supports: MXFP quant for token dispatch, and CPU binding with topo clusters. [#11614](https://github.com/vllm-project/vllm-ascend/pull/11614) [#11717](https://github.com/vllm-project/vllm-ascend/pull/11717)
- Expanded Atlas 300I DUO support: disabled npugraph_ex by default, added Qwen3.5-Dense documentation, and fixed 310P spec decoding accuracy. [#10874](https://github.com/vllm-project/vllm-ascend/pull/10874) [#12077](https://github.com/vllm-project/vllm-ascend/pull/12077) [#11918](https://github.com/vllm-project/vllm-ascend/pull/11918)
- Added operator supports: KV quant sparse flash attention, and Triton SwiGLuStep kernel (replaced AscendC‑based fused_gdn_gating). [#11626](https://github.com/vllm-project/vllm-ascend/pull/11626) [#11467](https://github.com/vllm-project/vllm-ascend/pull/11467) [#12035](https://github.com/vllm-project/vllm-ascend/pull/12035)

### Performance

Unless stated otherwise, these optimizations are selected automatically for the targeted path and need no additional configuration.

- Optimized PCP FA restore and output merge to reduce overhead. [#11586](https://github.com/vllm-project/vllm-ascend/pull/11586)
- Vectorized local sequence-length computation in SFA metadata to remove per-request NPU-to-CPU synchronization. [#11762](https://github.com/vllm-project/vllm-ascend/pull/11762)
- Avoided H2D synchronization in context-parallel speculative-proposer metadata. [#11496](https://github.com/vllm-project/vllm-ascend/pull/11496)
- Optimized DSA-CP local token metadata with a fused Triton kernel and caching. [#12193](https://github.com/vllm-project/vllm-ascend/pull/12193)
- Split mixed ChunkedPrefill into separate decode and prefill attention calls. [#11948](https://github.com/vllm-project/vllm-ascend/pull/11948)
- Optimized AscendStore key construction and miss-path handling. [#12814](https://github.com/vllm-project/vllm-ascend/pull/12814)
- Removed D2H sync in QLIMetadata builder for DSA-CP. [#12536](https://github.com/vllm-project/vllm-ascend/pull/12536)
- Bound Mooncake receiver threads to KV cache device. [#12126](https://github.com/vllm-project/vllm-ascend/pull/12126)
- Sharded DeepSeek V4 DSpark main projection across TP ranks for better parallelism. [#15144](https://github.com/vllm-project/vllm-ascend/pull/15144)
- Reused DeepSeek V4 compressor metadata across layers to avoid redundant computation. [#14994](https://github.com/vllm-project/vllm-ascend/pull/14994)

### Dependencies

- **Upstream vLLM**: v0.26.0.
- **Python**: >= 3.10, < 3.13.
- **CANN**: 9.1.0.
- **PyTorch / torch_npu**: 2.10.0 / 2.10.0.post4.
- **Triton Ascend**: 3.2.2 for A2, A3, and Ascend 950; Triton Ascend is not supported on Atlas 300I DUO.
- **Mooncake**: 0.3.11.post1 in the release images.

### Deprecation and Breaking Changes

- Removed layer sharding. [#11953](https://github.com/vllm-project/vllm-ascend/pull/11953)
- Removed FlashComm2 optimization techniques. [#12117](https://github.com/vllm-project/vllm-ascend/pull/12117)
- Removed multistream overlap gate. [#11956](https://github.com/vllm-project/vllm-ascend/pull/11956)
- Removed dynamic-batch SLO. [#11933](https://github.com/vllm-project/vllm-ascend/pull/11933)
- Removed weight prefetch config. [#11949](https://github.com/vllm-project/vllm-ascend/pull/11949)
- Removed matmul all-reduce and matmul all-reduce RMSNorm fusions. [#12119](https://github.com/vllm-project/vllm-ascend/pull/12119)
- Removed KV offload in KV Pool. [#11904](https://github.com/vllm-project/vllm-ascend/pull/11904)
- Removed `dp_allreduce_on_npu` additional config option. [#12496](https://github.com/vllm-project/vllm-ascend/pull/12496)
- Removed PCP from MRV1; use MRV2 for prefill context parallelism. [#12592](https://github.com/vllm-project/vllm-ascend/pull/12592)
- Removed custom top-k top-p AscendC implementation in favor of CANN operator. [#12232](https://github.com/vllm-project/vllm-ascend/pull/12232)
- Refactored hamming ops and removed sparse action. [#12049](https://github.com/vllm-project/vllm-ascend/pull/12049)
- Deprecated `ASCEND_BUFFER_POOL` environment variable; use `ASCEND_ENABLE_USE_FABRIC_MEM=1` or `HCCL_INTRA_ROCE_ENABLE=1`. [#13856](https://github.com/vllm-project/vllm-ascend/pull/13856)

### Ready to Deprecate

The following features are deprecated or subject to change:

- Added deprecation warnings for W4A8 linear, W4A8 MoE per-group, and W8A8 PDMix MoE quantization. These quantization paths will be removed in a future release. [#13850](https://github.com/vllm-project/vllm-ascend/pull/13850)
- The `mega_moe_max_tokens` and `enable_fused_mc2` configurations in `additional-config` will be moved into a new dedicated dict for centralized maintenance in the next release.
- DeepSeek-V3, DeepSeek-V3.1, and DeepSeek-R1 model support will be removed in v0.28.0.
- The `reduce sampling` feature is experimental and will be deprecated in future releases. We will follow the upstream vLLM community for the `batch-sharded sampling` feature.

### Documentation

- Added Kimi-K3 deployment guide on Ascend. [#14125](https://github.com/vllm-project/vllm-ascend/pull/14125)
- Refreshed DeepSeek-V4, GLM-5.2, Kimi-K2.x, and Gemma4 model deployment guides. [#11525](https://github.com/vllm-project/vllm-ascend/pull/11525) [#11534](https://github.com/vllm-project/vllm-ascend/pull/11534) [#11055](https://github.com/vllm-project/vllm-ascend/pull/11055)
- Added KV Pool and Memcache SSD cache configuration guides. [#12600](https://github.com/vllm-project/vllm-ascend/pull/12600) [#12670](https://github.com/vllm-project/vllm-ascend/pull/12670)
- Added RLHF LoRA HTTP API example and e2e RLHF async pause/resume example. [#14672](https://github.com/vllm-project/vllm-ascend/pull/14672) [#12300](https://github.com/vllm-project/vllm-ascend/pull/12300)

### Stability and Bug Fixes

- Fixed GDN state and graph-dispatch accuracy regressions across P/D, PCP, MTP, and DCP. [#11195](https://github.com/vllm-project/vllm-ascend/pull/11195) [#11893](https://github.com/vllm-project/vllm-ascend/pull/11893) [#12027](https://github.com/vllm-project/vllm-ascend/pull/12027)
- Fixed Qwen3.5 PCP + chunked prefill accuracy and small-chunk problems. [#11508](https://github.com/vllm-project/vllm-ascend/pull/11508) [#11807](https://github.com/vllm-project/vllm-ascend/pull/11807)
- Fixed DeepSeek V4 MXFP routing precision and W4A16MXFP communication accuracy. [#11663](https://github.com/vllm-project/vllm-ascend/pull/11663) [#12585](https://github.com/vllm-project/vllm-ascend/pull/12585)
- Fixed KV-transfer ordering, Mooncake grouping, and AscendStore hash/lease handling. [#11887](https://github.com/vllm-project/vllm-ascend/pull/11887) [#12252](https://github.com/vllm-project/vllm-ascend/pull/12252) [#12012](https://github.com/vllm-project/vllm-ascend/pull/12012)
- Fixed DCP/DP service hangs and restricted recompute scheduler to decode nodes. [#12036](https://github.com/vllm-project/vllm-ascend/pull/12036) [#11265](https://github.com/vllm-project/vllm-ascend/pull/11265) [#11537](https://github.com/vllm-project/vllm-ascend/pull/11537)
- Fixed 310P spec decoding accuracy, SDMA errors, and memory calculation. [#11918](https://github.com/vllm-project/vllm-ascend/pull/11918) [#11678](https://github.com/vllm-project/vllm-ascend/pull/11678) [#11959](https://github.com/vllm-project/vllm-ascend/pull/11959)
- Fixed DSpark multi-DP bugs and SP handling. [#12612](https://github.com/vllm-project/vllm-ascend/pull/12612) [#12777](https://github.com/vllm-project/vllm-ascend/pull/12777)
- Fixed GLM-5.2 DSpark W8A8 eager acceptance. [#12262](https://github.com/vllm-project/vllm-ascend/pull/12262)
- Fixed fused_infer_attention contiguous errors in MLA-CP and GQA paths. [#11986](https://github.com/vllm-project/vllm-ascend/pull/11986) [#12025](https://github.com/vllm-project/vllm-ascend/pull/12025)
- Fixed DSA-CP invalid local sequence lengths for graph padding. [#12840](https://github.com/vllm-project/vllm-ascend/pull/12840)
- Fixed invalid GVA handling in layerwise KV Pool. [#12705](https://github.com/vllm-project/vllm-ascend/pull/12705)
- Fixed AllGather MoE finalize order with DP and PCP. [#11921](https://github.com/vllm-project/vllm-ascend/pull/11921)
- Fixed batch invariance not taking effect. [#11818](https://github.com/vllm-project/vllm-ascend/pull/11818)
- Fixed Qwen3.x KV cache binding for multiple layers. [#11470](https://github.com/vllm-project/vllm-ascend/pull/11470)
- Fixed spec decode rejection sampling length-1 bug in Triton. [#11458](https://github.com/vllm-project/vllm-ascend/pull/11458)
- Fixed CPU binding device mapping. [#15518](https://github.com/vllm-project/vllm-ascend/pull/15518)
- Backported structured output fixes for vLLM 0.26. [#15433](https://github.com/vllm-project/vllm-ascend/pull/15433)
- Invalidated dummy slots before attention metadata build. [#15409](https://github.com/vllm-project/vllm-ascend/pull/15409)
- Skipped generate_mtp_attention_mask_for_decode with sparse attention to avoid hostbound. [#15130](https://github.com/vllm-project/vllm-ascend/pull/15130)
- Selected DeepSeek V4 effort mapping by checkpoint config. [#14952](https://github.com/vllm-project/vllm-ascend/pull/14952)

### Known Issues

- Kimi K3 DSpark speculative decoding has a low draft acceptance rate for long input sequences, reducing the expected performance benefit. [#15237](https://github.com/vllm-project/vllm-ascend/issues/15237)
- DeepSeek-V4-Flash may show a performance regression for 128K-input/1K-output workloads when pooling is enabled, especially for single-prefix requests. [#15649](https://github.com/vllm-project/vllm-ascend/issues/15649)
- Qwen3-32B W8A8/QuaRot may show a small performance regression in PD-disaggregated or pooling-enabled scenarios on v0.26.0rc. [#15295](https://github.com/vllm-project/vllm-ascend/issues/15295)
- DeepSeek-V3.1 may hang or fail during PD-disaggregated serving and high-concurrency PD-mixed inference. These scenarios are outside the supported export-model scope. [#14911](https://github.com/vllm-project/vllm-ascend/issues/14911)
- Qwen3-235B-A22B W8A8 and Qwen3-235B W4A8 may show lower performance than the baseline in some A3 PD-mixed aclgraph scenarios. [#15296](https://github.com/vllm-project/vllm-ascend/issues/15296)
- GLM5.1-W4A4C8-mxfp4 may show a performance regression on Ascend 950 due to CPU-binding and load-balancing effects. [#15268](https://github.com/vllm-project/vllm-ascend/issues/15268)
- Qwen3.6-27B DFlash with mixed sliding-window and full attention requires the V2 model runner. [#15650](https://github.com/vllm-project/vllm-ascend/issues/15650)
- DeepSeek-V3.2-W8A8 may show a partial performance regression in A3 single-node mixed deployment. [#15651](https://github.com/vllm-project/vllm-ascend/issues/15651)
- DeepSeek-V4 sleep mode with `sleep_mode_extra_cleanup` may fail to recover after wakeup. Sleep mode is mainly intended for training scenarios. [#15648](https://github.com/vllm-project/vllm-ascend/issues/15648)
- KV pooling may cause a small single-prefix performance regression in some long-context workloads, including DeepSeek-V4-Flash 128K-1K and Qwen3-32B A2 PD-mixed scenarios. Investigation is ongoing. [#15649](https://github.com/vllm-project/vllm-ascend/issues/15649) [#15295](https://github.com/vllm-project/vllm-ascend/issues/15295) [#12234](https://github.com/vllm-project/vllm-ascend/issues/12234)
- MiniMax-M2.7 W8A8 shows a performance regression in the A3 single-node scenario. The 128K-input/1K-output double-node result also fell below the baseline threshold, but more samples are needed to determine whether it is a persistent regression or normal performance variation. [#15658](https://github.com/vllm-project/vllm-ascend/issues/15658)

## v0.23.0 - 2026.08.16

We're excited to announce the official vLLM Ascend v0.23.0 release, aligned with upstream vLLM v0.23.0. This note summarizes the cumulative user-facing changes since the previous official release, v0.18.0, including the v0.19.1rc1, v0.20.2rc1, v0.21.0rc1, v0.22.1rc1, and v0.23.0rc1 development cycles. Please follow the [official documentation](https://docs.vllm.ai/projects/ascend/en/v0.23.0/) to get started.

PR references marked with **†** were merged into the v0.23.0 release branch after v0.23.0rc1.

### Highlights

- **Ascend 950 and DeepSeek V4**: Added end-to-end DeepSeek V4 support on Ascend 950, including DSA attention, MTP, piecewise graph execution, distributed inference, sparse attention, CPU binding, and MXFP quantization and communication paths. [#9757](https://github.com/vllm-project/vllm-ascend/pull/9757) [#9935](https://github.com/vllm-project/vllm-ascend/pull/9935) [#10236](https://github.com/vllm-project/vllm-ascend/pull/10236) [#11014](https://github.com/vllm-project/vllm-ascend/pull/11014)
- **Model and hardware coverage**: Expanded support and deployment guidance for GLM-5.2, GLM-4.7-Flash, Qwen3.5/Qwen3.6, Qwen3-ASR, Qwen3-Omni, Bailing MoE, Gemma4, Step3, and MiniMax 2.x models across A2, A3, Ascend 950, and Atlas 300I DUO. GLM-5.2 supports long-sequence inference up to 1M tokens on Atlas 800 A3. [#8657](https://github.com/vllm-project/vllm-ascend/pull/8657) [#9560](https://github.com/vllm-project/vllm-ascend/pull/9560) [#10441](https://github.com/vllm-project/vllm-ascend/pull/10441) [#10697](https://github.com/vllm-project/vllm-ascend/pull/10697) [#11091](https://github.com/vllm-project/vllm-ascend/pull/11091) [#11264](https://github.com/vllm-project/vllm-ascend/pull/11264) [#12115](https://github.com/vllm-project/vllm-ascend/pull/12115)
- **Context parallelism and sparse attention**: Added SFA DCP with a replicated indexer, compact KV gather, C8 support, and device-side metadata paths for long-context and P/D-disaggregated deployments. [#9638](https://github.com/vllm-project/vllm-ascend/pull/9638) [#9809](https://github.com/vllm-project/vllm-ascend/pull/9809) [#11819](https://github.com/vllm-project/vllm-ascend/pull/11819) [#11871](https://github.com/vllm-project/vllm-ascend/pull/11871) [#11981](https://github.com/vllm-project/vllm-ascend/pull/11981)
- **KV-cache lifecycle and offload**: Added hybrid/Mamba attention prefix caching; CPU and SSD offload in AscendStore that covers all backends. [#8743](https://github.com/vllm-project/vllm-ascend/pull/8743) [#9533](https://github.com/vllm-project/vllm-ascend/pull/9533) [#9731](https://github.com/vllm-project/vllm-ascend/pull/9731) [#10393](https://github.com/vllm-project/vllm-ascend/pull/10393)
- **Graph and speculative execution**: Added `FULL_AND_PIECEWISE` graph mode, which is enabled by default and requires no manual configuration; DFlash `FULL_DECODE_ONLY`; zero-bubble async scheduling; P-Eagle and PARD; and expanded MTP/Eagle3 support. [#7640](https://github.com/vllm-project/vllm-ascend/pull/7640) [#8118](https://github.com/vllm-project/vllm-ascend/pull/8118) [#9572](https://github.com/vllm-project/vllm-ascend/pull/9572) [#10042](https://github.com/vllm-project/vllm-ascend/pull/10042) [#10566](https://github.com/vllm-project/vllm-ascend/pull/10566)

### Features

- Added multimodal DFlash, FlashComm support for Qwen VL/MoE models, and PCP-aware multimodal reasoning. [#7486](https://github.com/vllm-project/vllm-ascend/pull/7486) [#7897](https://github.com/vllm-project/vllm-ascend/pull/7897) [#8038](https://github.com/vllm-project/vllm-ascend/pull/8038) [#9340](https://github.com/vllm-project/vllm-ascend/pull/9340)
- Added HCCL weight transfer for reinforcement-learning workloads and D2D NetLoader support for speculative draft models. [#9152](https://github.com/vllm-project/vllm-ascend/pull/9152) [#9893](https://github.com/vllm-project/vllm-ascend/pull/9893)
- Expanded Model Runner V2 with initial MoE and Eagle support. [#7885](https://github.com/vllm-project/vllm-ascend/pull/7885) [#7922](https://github.com/vllm-project/vllm-ascend/pull/7922)
- Expanded EPLB with additional observability and dynamic load-balancer examples. [#9536](https://github.com/vllm-project/vllm-ascend/pull/9536) [#10627](https://github.com/vllm-project/vllm-ascend/pull/10627)
- Extended C8 INT8 KV cache to sparse-attention paths with packed layouts and a DCP replicated indexer, and added W8A8FP8 and W4A16 MXFP quantization paths for Ascend 950. [#10236](https://github.com/vllm-project/vllm-ascend/pull/10236) [#11014](https://github.com/vllm-project/vllm-ascend/pull/11014) [#11846](https://github.com/vllm-project/vllm-ascend/pull/11846) [#11871](https://github.com/vllm-project/vllm-ascend/pull/11871)

### Hardware and Operator Support

- Added and optimized recurrent GDN, causal Conv1D, sparse-attention, LightningIndexer, compressor, and fused quantization operators. [#7798](https://github.com/vllm-project/vllm-ascend/pull/7798) [#7926](https://github.com/vllm-project/vllm-ascend/pull/7926) [#9382](https://github.com/vllm-project/vllm-ascend/pull/9382) [#9491](https://github.com/vllm-project/vllm-ascend/pull/9491) [#9825](https://github.com/vllm-project/vllm-ascend/pull/9825) [#10730](https://github.com/vllm-project/vllm-ascend/pull/10730)
- Expanded Atlas 300I DUO support for Qwen3.5, Qwen3.6, Qwen3-ASR, Qwen3-VL, quantized MoE paths, MTP, and graph execution. [#7674](https://github.com/vllm-project/vllm-ascend/pull/7674) [#7725](https://github.com/vllm-project/vllm-ascend/pull/7725) [#10309](https://github.com/vllm-project/vllm-ascend/pull/10309) [#12115](https://github.com/vllm-project/vllm-ascend/pull/12115) [#13262](https://github.com/vllm-project/vllm-ascend/pull/13262)†
- Added Python 3.12 support and moved release images to Python 3.12. [#9558](https://github.com/vllm-project/vllm-ascend/pull/9558)

### Performance

Unless stated otherwise, these optimizations are selected automatically for the targeted path and need no additional configuration.

- Replaced `npu_fusion_attention` with `_npu_flash_attention_unpad` for supported A2/A3 attention workloads. It is selected automatically; no manual setting is needed. [#8671](https://github.com/vllm-project/vllm-ascend/pull/8671)
- Avoided projecting unused tail KV tokens during MLA prefill with PCP. Enable PCP with `--prefill-context-parallel-size`; the optimization then applies automatically. [#8787](https://github.com/vllm-project/vllm-ascend/pull/8787)
- Reduced scheduler issuance bubbles for workloads using asynchronous scheduling. Enable it with `--async-scheduling`. [#8766](https://github.com/vllm-project/vllm-ascend/pull/8766)
- Added zero-bubble scheduling for asynchronous speculative decoding. Enable it with `--async-scheduling` together with a speculative decoding configuration. [#7640](https://github.com/vllm-project/vllm-ascend/pull/7640)
- Batched KV-cache offload copies with `aclrtMemcpyBatchAsync` for CPU-offload workloads. Configure KV cache CPU offload as documented; batching is automatic within that path. [#7819](https://github.com/vllm-project/vllm-ascend/pull/7819)
- Reduced PCP/DCP KV-cache all-gather traffic by selecting the required blocks before communication. Enable PCP or DCP with `--prefill-context-parallel-size` or `--decode-context-parallel-size`; no separate optimization switch is needed. [#8050](https://github.com/vllm-project/vllm-ascend/pull/8050)
- Optimized `split_qkv_tp_rmsnorm_rope` kernels for supported quantized model paths. Kernel selection is automatic; no manual setting is needed. [#8059](https://github.com/vllm-project/vllm-ascend/pull/8059) [#9830](https://github.com/vllm-project/vllm-ascend/pull/9830)
- Removed prefill host-device synchronization in Qwen3-Next and Qwen3.5 paths. It applies automatically to those models. [#7967](https://github.com/vllm-project/vllm-ascend/pull/7967)
- Reduced SFA prefill KV all-gather communication for PCP/DCP. Enable the corresponding context-parallel mode; the optimized communication path is automatic. [#8043](https://github.com/vllm-project/vllm-ascend/pull/8043)
- Added a Triton penalty kernel for requests using repetition, frequency, or presence penalties. It is selected automatically when penalties are requested. [#7569](https://github.com/vllm-project/vllm-ascend/pull/7569)
- Optimized Model Runner V2 temperature and top-k log-softmax kernels. They are selected automatically for sampling workloads on Model Runner V2. [#8083](https://github.com/vllm-project/vllm-ascend/pull/8083)
- Optimized the Model Runner V2 min-p kernel. It applies automatically when min-p sampling is requested. [#8243](https://github.com/vllm-project/vllm-ascend/pull/8243) [#7767](https://github.com/vllm-project/vllm-ascend/pull/7767)
- Added a Model Runner V2 Triton kernel for bad-word filtering. It applies automatically when `bad_words` is supplied. [#8030](https://github.com/vllm-project/vllm-ascend/pull/8030)
- Optimized the Model Runner V2 bincount kernel. It is selected automatically for sampling paths that require token counts. [#7757](https://github.com/vllm-project/vllm-ascend/pull/7757)
- Optimized the Model Runner V2 ranks kernel. It is selected automatically for the corresponding sampling path. [#7767](https://github.com/vllm-project/vllm-ascend/pull/7767)
- Reduced avoidable Triton recompilation caused by runtime function parameters. The cache-friendly path is automatic; no manual setting is needed. [#7481](https://github.com/vllm-project/vllm-ascend/pull/7481) [#7483](https://github.com/vllm-project/vllm-ascend/pull/7483)
- Reused equivalent HCCL process groups to reduce distributed initialization overhead. Reuse is automatic for matching groups. [#7654](https://github.com/vllm-project/vllm-ascend/pull/7654)
- Deferred CPU binding until worker warmup completes to avoid interfering with initialization. CPU binding is enabled by default on supported ARM servers; no manual setting is needed unless it was explicitly disabled. [#7829](https://github.com/vllm-project/vllm-ascend/pull/7829)
- Converted eligible Conv3D operations to linear operations when kernel size equals stride. Conversion is automatic for matching models. [#8318](https://github.com/vllm-project/vllm-ascend/pull/8318)
- Optimized MoE routing on Ascend 310P. It applies automatically to supported 310P MoE workloads. [#9105](https://github.com/vllm-project/vllm-ascend/pull/9105)
- Added NZ-format W4A8 MoE compressed tensors for supported quantized models. Load a compatible W4A8 checkpoint with Ascend quantization; format selection is automatic. [#9625](https://github.com/vllm-project/vllm-ascend/pull/9625)
- Optimized irregular-mask construction for PCP/DCP with speculative decoding. Enable context parallelism and speculative decoding; no separate optimization switch is needed. [#9678](https://github.com/vllm-project/vllm-ascend/pull/9678)
- Reworked reduce sampling for DFlash and MTP. This remains experimental and disabled by default; enable it with `additional_config.enable_reduce_sample=true` for distributed greedy, top-k/top-p, or rejection sampling. [#8308](https://github.com/vllm-project/vllm-ascend/pull/8308) [#9735](https://github.com/vllm-project/vllm-ascend/pull/9735)
- Added multistream compute-communication overlap for DeepSeek V4 DSA compressor, indexer-select, CV-parallel, and pure-prefill paths. Enable FlashComm1 and the applicable DSA-CP/overlap configuration; the optimized subpaths are then selected automatically. [#9433](https://github.com/vllm-project/vllm-ascend/pull/9433) [#9441](https://github.com/vllm-project/vllm-ascend/pull/9441) [#9450](https://github.com/vllm-project/vllm-ascend/pull/9450) [#9504](https://github.com/vllm-project/vllm-ascend/pull/9504) [#9530](https://github.com/vllm-project/vllm-ascend/pull/9530) [#10518](https://github.com/vllm-project/vllm-ascend/pull/10518)
- Reused DeepSeek V4 DSA `topk_indices` across decode steps through IndexCache. It applies automatically to eligible DSA decode workloads. [#9390](https://github.com/vllm-project/vllm-ascend/pull/9390)
- Removed a host-device synchronization point from PIECEWISE graph execution. `FULL_AND_PIECEWISE` is the default graph mode, so no manual configuration is needed. [#9025](https://github.com/vllm-project/vllm-ascend/pull/9025)
- Optimized shared-expert overlap timing in FusedMoE. Enable the supported shared-expert overlap configuration; timing optimization is automatic within that path. [#9413](https://github.com/vllm-project/vllm-ascend/pull/9413)
- Skipped unnecessary slot-mapping computation for Mamba groups in hybrid-cache models. It applies automatically when the model uses a Mamba cache group. [#10492](https://github.com/vllm-project/vllm-ascend/pull/10492)
- Built single-rank DSA compressor metadata on device to remove CPU construction and synchronization. It applies automatically to eligible non-CP DSA compressed-KV paths. [#10741](https://github.com/vllm-project/vllm-ascend/pull/10741)
- Vectorized SFA local-sequence-length computation to remove per-request NPU-to-CPU synchronization. It applies automatically to SFA workloads. [#11816](https://github.com/vllm-project/vllm-ascend/pull/11816)
- Replaced the SFA DSA-CP output merge's full all-gather with token-sharded all-to-all to reduce communication and peak receive-buffer use. Enable FlashComm1 and `additional_config.enable_dsa_cp=true`; no separate optimization switch is needed. [#12137](https://github.com/vllm-project/vllm-ascend/pull/12137)
- Reduced restore and output-merge overhead in the PCP FlashAttention path. Enable PCP with `--prefill-context-parallel-size`; the optimized restore path is automatic. [#11842](https://github.com/vllm-project/vllm-ascend/pull/11842)
- Avoided host-to-device synchronization while building context-parallel speculative-proposer metadata. Enable context parallelism and speculative decoding; the optimized metadata path is automatic. [#11862](https://github.com/vllm-project/vllm-ascend/pull/11862)
- Snapshotted query start locations before asynchronous host-to-device copies to preserve non-blocking metadata transfers. It applies automatically to asynchronous copy paths. [#12071](https://github.com/vllm-project/vllm-ascend/pull/12071)
- Added fused W4A8 MoE dispatch, FFN, and combine to overlap communication with computation. Load a supported W4A8 MoE checkpoint with Ascend quantization; fused-kernel selection is automatic. [#7779](https://github.com/vllm-project/vllm-ascend/pull/7779)
- Added asynchronous all-gather for DSA-CP output-projection TP weights. Enable FlashComm1 and `additional_config.enable_dsa_cp=true`; the asynchronous path is automatic. [#10694](https://github.com/vllm-project/vllm-ascend/pull/10694)
- Improved DeepSeek V4 prefix-cache hit rates when MTP is enabled. Prefix caching is enabled by default in vLLM V1; no flag is needed unless it was previously disabled. [#11107](https://github.com/vllm-project/vllm-ascend/pull/11107)
- Reused prebuilt chunk host metadata to reduce synchronization overhead for Qwen3.5 and MiniMax-M2.5 workloads. It applies automatically to the affected model paths. [#9310](https://github.com/vllm-project/vllm-ascend/pull/9310)
- Parallelized Mooncake KV receive handling for P/D-disaggregated deployments. Configure the Mooncake KV-transfer connector; receive parallelism is automatic. [#10548](https://github.com/vllm-project/vllm-ascend/pull/10548)
- Optimized AscendStore key construction and KV Pool miss handling to reduce host overhead. Configure `AscendStoreConnector`; the optimized paths are selected automatically. [#12783](https://github.com/vllm-project/vllm-ascend/pull/12783)†
- Reused grouped block hashes across AscendStore query, save, and load operations to reduce repeated host-side hashing. Configure `AscendStoreConnector`; reuse is automatic. [#13169](https://github.com/vllm-project/vllm-ascend/pull/13169)†

### Stability and Bug Fixes

- Fixed GDN state and graph-dispatch accuracy regressions across P/D, PCP, MTP, and DCP, including one-token stateful prefill handling. [#11195](https://github.com/vllm-project/vllm-ascend/pull/11195) [#11893](https://github.com/vllm-project/vllm-ascend/pull/11893) [#12027](https://github.com/vllm-project/vllm-ascend/pull/12027) [#12255](https://github.com/vllm-project/vllm-ascend/pull/12255)†
- Fixed Qwen3.5/Qwen3.6 speculative-decoding accuracy, Mamba prefix-cache corruption, block-table overflow, and Atlas 300I DUO graph failures. [#11337](https://github.com/vllm-project/vllm-ascend/pull/11337) [#11408](https://github.com/vllm-project/vllm-ascend/pull/11408) [#11353](https://github.com/vllm-project/vllm-ascend/pull/11353) [#11659](https://github.com/vllm-project/vllm-ascend/pull/11659) [#11920](https://github.com/vllm-project/vllm-ascend/pull/11920) [#12038](https://github.com/vllm-project/vllm-ascend/pull/12038)
- Fixed GLM-5.1 IndexCache weight loading and a GLM-4.7-Flash first-request `IndexError` with MTP and layerwise Memcache. [#11363](https://github.com/vllm-project/vllm-ascend/pull/11363) [#11829](https://github.com/vllm-project/vllm-ascend/pull/11829)
- Fixed Qwen MoE routing overflow and shared-expert gate failures, Qwen3-Omni ModelSlim W8A8 checkpoint loading, and Qwen3-VL rotary-embedding copy races on Atlas 300I DUO. [#11391](https://github.com/vllm-project/vllm-ascend/pull/11391) [#11730](https://github.com/vllm-project/vllm-ascend/pull/11730) [#12321](https://github.com/vllm-project/vllm-ascend/pull/12321) [#11679](https://github.com/vllm-project/vllm-ascend/pull/11679) [#12132](https://github.com/vllm-project/vllm-ascend/pull/12132)
- Fixed the DeepSeek-R1-0528 W8A8 shared-expert no-clamp accuracy path and malformed streamed tool calls or TP8+EP startup for MiniMax-M2/M2.5. [#11775](https://github.com/vllm-project/vllm-ascend/pull/11775) [#11505](https://github.com/vllm-project/vllm-ascend/pull/11505)
- Fixed DeepSeek V4 MXFP routing precision, W4A16MXFP communication accuracy, and eager draft compilation configuration isolation. [#11663](https://github.com/vllm-project/vllm-ascend/pull/11663) [#11718](https://github.com/vllm-project/vllm-ascend/pull/11718) [#12587](https://github.com/vllm-project/vllm-ascend/pull/12587)† [#12722](https://github.com/vllm-project/vllm-ascend/pull/12722)†
- Fixed KV-transfer ordering and TP-shard consistency, Mooncake grouping, AscendStore hash/lease/lookup handling, and layerwise KV Pool failures. [#11887](https://github.com/vllm-project/vllm-ascend/pull/11887) [#12252](https://github.com/vllm-project/vllm-ascend/pull/12252) [#12371](https://github.com/vllm-project/vllm-ascend/pull/12371)† [#12797](https://github.com/vllm-project/vllm-ascend/pull/12797)† [#12819](https://github.com/vllm-project/vllm-ascend/pull/12819)†
- Fixed DCP/DP service hangs, limited the recompute scheduler to decode nodes, and delayed AscendStore initialization until the first real decode request. [#12034](https://github.com/vllm-project/vllm-ascend/pull/12034) [#11490](https://github.com/vllm-project/vllm-ascend/pull/11490) [#11673](https://github.com/vllm-project/vllm-ascend/pull/11673)
- Disabled unsupported shared-expert multistream overlap with fused MC2 and fixed low MTP acceptance for SFA with DSA-CP and multiple speculative tokens. [#12245](https://github.com/vllm-project/vllm-ascend/pull/12245) [#10878](https://github.com/vllm-project/vllm-ascend/pull/10878)
- Fixed AscendStore compatibility with pipeline parallelism and surfaced backend failures. [#12762](https://github.com/vllm-project/vllm-ascend/pull/12762)†
- Fixed invalid-GVA handling for layerwise KV Pool transfers. [#12643](https://github.com/vllm-project/vllm-ascend/pull/12643)†
- Fixed A5 BF16 `mm_reduce_scatter` communication-mode selection and restricted FP8 quantization detection to A5 devices. [#12826](https://github.com/vllm-project/vllm-ascend/pull/12826)† [#12895](https://github.com/vllm-project/vllm-ascend/pull/12895)†
- Packed SFA DSA-CP KV tensors into one all-gather to correct and streamline the communication path. [#12867](https://github.com/vllm-project/vllm-ascend/pull/12867)†
- Disabled unsupported `npugraph_ex` compilation automatically on Atlas 300I DUO and fixed low-level rotary and sparse-attention tiling/metadata issues. [#12366](https://github.com/vllm-project/vllm-ascend/pull/12366)† [#12446](https://github.com/vllm-project/vllm-ascend/pull/12446)† [#12841](https://github.com/vllm-project/vllm-ascend/pull/12841)†
- Fixed `npu_dequant_swiglu_quant` precision for small token shapes and propagated `return_lse` to QuantSFA operators. [#12913](https://github.com/vllm-project/vllm-ascend/pull/12913)† [#13197](https://github.com/vllm-project/vllm-ascend/pull/13197)†
- Removed unnecessary Memcache lazy initialization and hardened AscendStore transfers by restoring synchronous saves, reporting asynchronous load failures to the scheduler, and using grouped block sizes in transfer threads. [#13028](https://github.com/vllm-project/vllm-ascend/pull/13028)† [#13024](https://github.com/vllm-project/vllm-ascend/pull/13024)† [#13099](https://github.com/vllm-project/vllm-ascend/pull/13099)† [#13110](https://github.com/vllm-project/vllm-ascend/pull/13110)†
- Removed `-Werror` from custom-operator CMake builds so compiler warnings do not fail release builds. [#13095](https://github.com/vllm-project/vllm-ascend/pull/13095)†

### Dependencies

- **Upstream vLLM**: v0.23.0.
- **Python**: >= 3.10, < 3.13.
- **CANN**: 9.1.0 for A2, A3, and Ascend 950; refer to the Atlas 300I DUO installation guide for its platform-specific CANN package. [#13421](https://github.com/vllm-project/vllm-ascend/pull/13421)†
- **PyTorch / torch_npu**: 2.10.0 / 2.10.0.post4.
- **Triton Ascend**: 3.2.2 for A2, A3, and Ascend 950; Triton Ascend is not supported on Atlas 300I DUO.
- **Mooncake**: 0.3.11.post1 in the release images.

### Deprecation and Configuration Changes

- The former `enable_sparse_c8` option was split into `enable_sparse_sfa_c8` and `enable_sparse_li_c8`; update `--additional-config` according to the sparse-attention components in use. [#12351](https://github.com/vllm-project/vllm-ascend/pull/12351)
- Migrate FlashComm1 deployments from `VLLM_ASCEND_ENABLE_FLASHCOMM1` to `additional_config.enable_flashcomm1`. [#9064](https://github.com/vllm-project/vllm-ascend/pull/9064)
- `VLLM_ASCEND_ENABLE_CONTEXT_PARALLEL` was removed during the `AscendConfig` migration. DSA-CP is now controlled by `additional_config.enable_dsa_cp`; deployments that previously relied on FlashComm1 implicitly enabling DSA-CP must explicitly enable both options. [#9668](https://github.com/vllm-project/vllm-ascend/pull/9668) [#9697](https://github.com/vllm-project/vllm-ascend/pull/9697) [#9910](https://github.com/vllm-project/vllm-ascend/pull/9910)
- Sequence Parallelism is marked unavailable for all current model categories in the v0.23.0 support matrix; deployments that used it in v0.18.0 should move to FlashComm1 where applicable. [#12860](https://github.com/vllm-project/vllm-ascend/pull/12860)†
- `ASCEND_BUFFER_POOL` was removed. Use `ASCEND_ENABLE_USE_FABRIC_MEM=1` or `HCCL_INTRA_ROCE_ENABLE=1` according to the hardware and deployment path. [#13834](https://github.com/vllm-project/vllm-ascend/pull/13834)†

### Ready to Deprecate

The following features and optimizations are planned for deprecation in a future release:

- Layer sharding.
- FlashComm2.
- The FlashComm3 multistream-overlap gate.
- Hamming sparse.
- Asynchronous exponential overlap.
- Matmul all-reduce and matmul all-reduce RMSNorm fusions.
- Weight prefetch.
- Dynamic-batch SLO.
- KV offload in KV Pool.
- Fused MC2 mode 2 (`enable_fused_mc2=2`).
- Paged attention and `pa_shape_list`.

### Documentation

- Refreshed Ascend 950 DeepSeek-V3.1/V3.2 and GLM-5.2 deployment guidance. [#12937](https://github.com/vllm-project/vllm-ascend/pull/12937)† [#13043](https://github.com/vllm-project/vllm-ascend/pull/13043)†

### Known Issues

- Pipeline parallelism (PP) combined with prefill context parallelism (PCP) is not supported in v0.23.0.
- Reduce sampling (`additional_config.enable_reduce_sample=true`) is experimental. It is incompatible with P/D-disaggregated serving and lmhead tensor parallelism, where it is automatically disabled. Do not enable it when sampling logprobs are requested because the logprob values and top-k rankings would be computed over partitioned logits and can be incorrect. [#13469](https://github.com/vllm-project/vllm-ascend/pull/13469)† [#13632](https://github.com/vllm-project/vllm-ascend/pull/13632)†
- GLM-5.2 1M-context deployments were validated only on Atlas 800 A3; the A2 series was not validated for 1M context.
- For P/D-disaggregated serving of models using Sparse Flash Attention (SFA), including DeepSeek-V3.2, GLM-5.1, and GLM-5.2, DCP must be enabled on both prefiller and decoder nodes or disabled on both. Asymmetric DCP configuration can cause accuracy issues. [#14322](https://github.com/vllm-project/vllm-ascend/pull/14322)†
- On Ascend 950, context parallelism is not supported with SFA; context-parallel MLA and GQA paths are experimental. [#13303](https://github.com/vllm-project/vllm-ascend/pull/13303)†
- In v0.23.0, combining GLM-5.2 DCP with Sparse Flash Attention C8 (`enable_sparse_sfa_c8`) has known issues, including performance degradation, and is not recommended. [#14011](https://github.com/vllm-project/vllm-ascend/pull/14011)†
- On Atlas 300I DUO or Atlas 200I Pro (310P), Qwen3.5-2B-W8A8 GSM8K accuracy can fluctuate by more than 1% compared with the floating-point model. [#14335](https://github.com/vllm-project/vllm-ascend/issues/14335)
- DeepSeek V4 on A2 or A3 can experience 1-2 second TPOT spikes under high concurrency when varying input shapes trigger Triton kernel recompilation. [#14324](https://github.com/vllm-project/vllm-ascend/issues/14324)
- DeepSeek V4 Flash and GLM-5.1 SWE benchmark results can vary because of intermittent evaluation failures, including container crashes, timeouts, dependency-download failures, and agent nondeterminism. [#14326](https://github.com/vllm-project/vllm-ascend/issues/14326)
- DeepSeek-V3.1 large-EP deployments have a reported 3%-5% performance gap from the target performance. [#14327](https://github.com/vllm-project/vllm-ascend/issues/14327)
- GLM-5.1 on an Ascend 950 single-node mixed P/D deployment can incur excessive P/D transfer overhead for a 64k-input/1k-output workload without a prefix-cache hit. [#14328](https://github.com/vllm-project/vllm-ascend/issues/14328)
- GLM-5.1 P/D-disaggregated serving with both `sfa_c8` and `li_c8` enabled has a reported performance regression for 64k-input/1k-output workloads. [#14329](https://github.com/vllm-project/vllm-ascend/issues/14329)
- In graph mode, `torch.ops._C_ascend.mla_preprocess` and `torch.ops._C_ascend.batch_matmul_transpose` can emit an `rtMemcpy` 107030 error in plog; the reported error does not affect inference. [#14347](https://github.com/vllm-project/vllm-ascend/issues/14347)
- GLM-5.2-W4A8C8 P/D-disaggregated serving with `enable_sparse_sfa_c8` can show GPQA accuracy fluctuations of approximately 2-3 percentage points across repeated runs. [#14378](https://github.com/vllm-project/vllm-ascend/issues/14378)
- DeepSeek-V3.1 2P1D throughput has a reported regression of about 15% compared with v0.18.0 in high-throughput deployments. [#12349](https://github.com/vllm-project/vllm-ascend/issues/12349)
- DeepSeek V4 Pro has an open long-running stability report involving increasing memory use. [#12345](https://github.com/vllm-project/vllm-ascend/issues/12345)
- Qwen3-30B-A3B floating-point serving has a reported single-batch performance regression. [#12337](https://github.com/vllm-project/vllm-ascend/issues/12337)
- AscendStore KV Pool has backend-specific constraints for layerwise Memcache, SSD offload, hybrid-attention load failures, and graph fallback behavior. [#12390](https://github.com/vllm-project/vllm-ascend/issues/12390)
- Ascend 950 graph capture is temporarily limited to a reduced set of stages because of HDK incompatibility, which avoids crashes but can reduce performance. [#12998](https://github.com/vllm-project/vllm-ascend/issues/12998)

## v0.23.0rc1 - 2026.07.20

We're excited to announce v0.23.0rc1, the first release candidate for the vLLM Ascend v0.23.0 release line. This release aligns the plugin with upstream vLLM v0.23.0 and expands model, context-parallel, KV-cache offload, and Ascend 950 support. Please follow the [official documentation](https://docs.vllm.ai/projects/ascend/en/v0.23.0/) to get started.

### Highlights

- **Expanded model support**: Added GLM-5.2 support on A2 and A3, and Ascend 310P support for Qwen3-ASR-1.7B, Qwen3.5, and Qwen3.6. [#10441](https://github.com/vllm-project/vllm-ascend/pull/10441) [#11264](https://github.com/vllm-project/vllm-ascend/pull/11264) [#10257](https://github.com/vllm-project/vllm-ascend/pull/10257) [#12115](https://github.com/vllm-project/vllm-ascend/pull/12115)
- **Sparse attention and context parallelism**: Added SFA DCP with a replicated indexer, compact KV gather, and C8 support. [#11819](https://github.com/vllm-project/vllm-ascend/pull/11819) [#11981](https://github.com/vllm-project/vllm-ascend/pull/11981) [#11846](https://github.com/vllm-project/vllm-ascend/pull/11846) [#11871](https://github.com/vllm-project/vllm-ascend/pull/11871)
- **KV-cache lifecycle and offload**: Added recompute KV-cache offload for P/D decoder nodes, AscendStore coordination, and layerwise KV Pooling with a Memcache backend. [#10742](https://github.com/vllm-project/vllm-ascend/pull/10742) [#10393](https://github.com/vllm-project/vllm-ascend/pull/10393) [#11585](https://github.com/vllm-project/vllm-ascend/pull/11585)
- **Ascend 950 quantization and communication**: Added W4A16 MXFP4, all-gather EP MXFP4, and low-accuracy token-dispatch paths. [#11014](https://github.com/vllm-project/vllm-ascend/pull/11014) [#11287](https://github.com/vllm-project/vllm-ascend/pull/11287) [#11718](https://github.com/vllm-project/vllm-ascend/pull/11718) [#11766](https://github.com/vllm-project/vllm-ascend/pull/11766)

### Features

- Added DeepSeek V4 MTP graph support. [#11062](https://github.com/vllm-project/vllm-ascend/pull/11062)
- Added Virtual Width Network Eagle3 and Eagle3 support with chunked pipeline parallelism. [#10042](https://github.com/vllm-project/vllm-ascend/pull/10042) [#10566](https://github.com/vllm-project/vllm-ascend/pull/10566)

### Experimental Features or Optimizations

- Added experimental Step3P7 and Step3P5 support, including Step3P5 MTP. [#10697](https://github.com/vllm-project/vllm-ascend/pull/10697)
- Added experimental Gemma4 support on A2 and Ascend 950. [#11091](https://github.com/vllm-project/vllm-ascend/pull/11091) [#10643](https://github.com/vllm-project/vllm-ascend/pull/10643)
- Improved the DeepSeek V4 prefix-cache hit rate. [#11107](https://github.com/vllm-project/vllm-ascend/pull/11107)

### Performance

- Optimized SFA DSA-CP output merge with All-to-All communication and PCP FlashAttention restore/output merge. [#12137](https://github.com/vllm-project/vllm-ascend/pull/12137) [#11842](https://github.com/vllm-project/vllm-ascend/pull/11842)
- Avoided H2D synchronization in context-parallel speculative decoding metadata and snapshotted query locations before asynchronous H2D copies. [#11862](https://github.com/vllm-project/vllm-ascend/pull/11862) [#12071](https://github.com/vllm-project/vllm-ascend/pull/12071)
- Parallelized KV-cache receive with a thread pool and enabled asynchronous all-gather for DSA-CP output-projection TP weights. [#10548](https://github.com/vllm-project/vllm-ascend/pull/10548) [#10694](https://github.com/vllm-project/vllm-ascend/pull/10694)
- Vectorized local sequence-length computation in SFA metadata. [#11816](https://github.com/vllm-project/vllm-ascend/pull/11816)

### Stability and Bug Fixes

- Fixed GLM-5.1 IndexCache weight loading and a GLM-4.7-Flash `IndexError` on the first request with MTP and layerwise MemCache. [#11363](https://github.com/vllm-project/vllm-ascend/pull/11363) [#11829](https://github.com/vllm-project/vllm-ascend/pull/11829)
- Fixed Qwen3.5 GDN accuracy regressions across PCP, MTP, and DCP graph replay, including a mixed-length PCP out-of-bounds crash, while restoring the previous model-runner dispatch behavior. [#11195](https://github.com/vllm-project/vllm-ascend/pull/11195) [#11893](https://github.com/vllm-project/vllm-ascend/pull/11893) [#12027](https://github.com/vllm-project/vllm-ascend/pull/12027) [#12283](https://github.com/vllm-project/vllm-ascend/pull/12283)
- Fixed Qwen3.5 speculative-decoding accuracy, garbled output, and out-of-bounds failures on Ascend 310P with MTP/EAGLE and full-graph execution. [#11337](https://github.com/vllm-project/vllm-ascend/pull/11337) [#11408](https://github.com/vllm-project/vllm-ascend/pull/11408) [#11920](https://github.com/vllm-project/vllm-ascend/pull/11920)
- Fixed Qwen MoE routing overflow and shared-expert gate matrix-multiplication failures on Ascend 310P. [#11391](https://github.com/vllm-project/vllm-ascend/pull/11391) [#11730](https://github.com/vllm-project/vllm-ascend/pull/11730)
- Fixed Qwen3-Omni ModelSlim W8A8 checkpoint loading failures caused by mismatched weight names and unquantized embedding metadata. [#12321](https://github.com/vllm-project/vllm-ascend/pull/12321)
- Fixed Qwen3-VL rotary-embedding copy races on Ascend 310P and restored the device-specific VisionTransformer patch. [#11679](https://github.com/vllm-project/vllm-ascend/pull/11679) [#12132](https://github.com/vllm-project/vllm-ascend/pull/12132)
- Fixed the DeepSeek-R1-0528 W8A8 shared-expert no-clamp accuracy path without regressing the clamped DeepSeek V4 path. [#11775](https://github.com/vllm-project/vllm-ascend/pull/11775)
- Fixed DeepSeek V4 Flash W4A8-MXFP4 all-gather EP inference on Ascend 950 by preserving routing-weight precision. [#11498](https://github.com/vllm-project/vllm-ascend/issues/11498) [#11663](https://github.com/vllm-project/vllm-ascend/pull/11663) [#11718](https://github.com/vllm-project/vllm-ascend/pull/11718)
- Fixed malformed streamed tool-call arguments and TP8+EP startup compatibility for MiniMax-M2 and MiniMax-M2.5. [#11505](https://github.com/vllm-project/vllm-ascend/pull/11505)
- Fixed silent prefix-cache output corruption and block-table overflow for Qwen3-Next, Qwen3.5, and other hybrid Mamba models using MTP/EAGLE, plus a 310P Mamba align-postprocess hang. [#11353](https://github.com/vllm-project/vllm-ascend/pull/11353) [#11659](https://github.com/vllm-project/vllm-ascend/pull/11659) [#12038](https://github.com/vllm-project/vllm-ascend/pull/12038)
- Fixed Mooncake KV-transfer grouping for Kimi-K2.7 Code with Kimi-K2.5-DFlash when P/D nodes use unequal TP sizes and target/draft models have different global KV-head counts. [#11887](https://github.com/vllm-project/vllm-ascend/pull/11887)
- Fixed the AscendStore parent-block hash chain when a KV block group is only partially missing. [#12252](https://github.com/vllm-project/vllm-ascend/pull/12252)
- Disabled shared-expert multistream overlap when fused MC2 is enabled to avoid an unsupported configuration. [#12245](https://github.com/vllm-project/vllm-ascend/pull/12245)
- Fixed DCP/DP service hangs and restricted the recompute scheduler to decode nodes. [#12034](https://github.com/vllm-project/vllm-ascend/pull/12034) [#11490](https://github.com/vllm-project/vllm-ascend/pull/11490)
- Delayed AscendStore initialization until the first real decode request. [#11673](https://github.com/vllm-project/vllm-ascend/pull/11673)
- Fixed low MTP acceptance rates for SFA with DSA-CP and multiple speculative tokens. [#10878](https://github.com/vllm-project/vllm-ascend/pull/10878)

### Dependencies

- **Upstream vLLM**: v0.23.0.
- **Python**: >= 3.10, < 3.13.
- **CANN**: 9.0.1 for A2, A3, and Ascend 950; refer to the 310P installation guide for its platform-specific CANN package.
- **PyTorch / torch_npu**: 2.10.0 / 2.10.0.post2.
- **Triton Ascend**: 3.2.1.
- **Mooncake**: 0.3.11.post1 in the release images.

### Ready to Deprecate

The following features and optimizations are planned for deprecation in a future release:

- Layer sharding.
- FlashComm2.
- The FlashComm3 multistream-overlap gate.
- Hamming sparse.
- Asynchronous exponential overlap.
- Matmul all-reduce and matmul all-reduce RMSNorm fusions.
- Weight prefetch.
- Dynamic-batch SLO.
- KV offload in KV Pool.
- Fused MC2 mode 2 (`enable_fused_mc2=2`).
- Paged attention and `pa_shape_list`.
- Selected plugin environment variables; their configuration will be migrated to equivalent `--additional-config` options.

### Known Issues

- The combination of pipeline parallelism (PP) and prefill context parallelism (PCP) is not supported in v0.23.0. Support for this combination is deferred to a later release.
- The former `enable_sparse_c8` option has been split into `enable_sparse_sfa_c8` and `enable_sparse_li_c8`. Existing `--additional-config` settings must use one or both new options depending on whether Sparse Flash Attention C8, LightningIndexer C8, or both are required. [#12351](https://github.com/vllm-project/vllm-ascend/pull/12351)
- The load-balance proxy can swallow decode errors and return an empty HTTP 200 response. [#12166](https://github.com/vllm-project/vllm-ascend/issues/12166)
- Qwen3-30B-A3B floating-point serving can show a 1-2 ms TPOT regression at batch size 1 in the reported TP4 full-graph configuration. [#12337](https://github.com/vllm-project/vllm-ascend/issues/12337)
- In the reported DeepSeek V4 Flash W8A8 MTP P/D-disaggregated deployment, the second aisbench round can cause a worker process from another card to appear on an NPU device. [#12338](https://github.com/vllm-project/vllm-ascend/issues/12338)
- On Ascend 950, Qwen3.5-397B-W8A8-MXFP8-FULL_QUANT in a P/D-disaggregated deployment without MTP can alternate between correct and incorrect outputs. [#12339](https://github.com/vllm-project/vllm-ascend/issues/12339)
- DeepSeek V4 Pro on A3 and Ascend 950 Products can show continuously increasing memory usage in both P/D-disaggregated and co-located deployments, eventually causing OOM or service instability. [#12345](https://github.com/vllm-project/vllm-ascend/issues/12345)
- DeepSeek-V3.1-Terminus can show about a 15% output-throughput regression against the reported v0.18.0 baseline in high-throughput P/D-disaggregated deployments; the regression was reported on an A3 four-node 2P1D setup and an A2 large-EP setup. [#12349](https://github.com/vllm-project/vllm-ascend/issues/12349)
- KV-cache transfer can produce precision issues and TP-shard inconsistencies when reformatting occurs before all pull tasks for a request have completed. [#12359](https://github.com/vllm-project/vllm-ascend/pull/12359)

## v0.22.1rc1 - 2026.06.30

We're excited to announce the release of v0.22.1rc1 for vLLM Ascend. This is the first release candidate for the v0.22.1 release line, building on v0.21.0rc1 and aligning the plugin with upstream vLLM v0.22.1. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.22.1rc) to get started.

### Highlights

- **Mooncake Connector for DeepSeek V4 / Hybrid KV Cache**: Mooncake connector now supports DeepSeek V4 and hybrid KV cache disaggregated prefill scenarios with correct block stride handling, compressed KV transfer calculation, and hybrid Mamba token alignment. [#10342](https://github.com/vllm-project/vllm-ascend/pull/10342)
- **HCCL Weight Transfer for RL Workloads**: Added an HCCL-based weight transfer backend for Ascend NPU so trainer and inference workers can synchronize weights in RL pipelines without a CUDA/NCCL dependency. [#9152](https://github.com/vllm-project/vllm-ascend/pull/9152)
- **Ascend 950 Expansion**: Extended Ascend 950 support with W8A8/W4A8 dynamic quantization and platform-specific CPU binding support. [#10236](https://github.com/vllm-project/vllm-ascend/pull/10236) [#10483](https://github.com/vllm-project/vllm-ascend/pull/10483)

### Features

- Added multimodal input support for DFlash workloads. [#9340](https://github.com/vllm-project/vllm-ascend/pull/9340)
- P-Eagle and PARD are now stable parallel speculative decoding methods and have passed validation testing.
- Added KV consumer partial-group caching for hybrid Mamba models. [#10009](https://github.com/vllm-project/vllm-ascend/pull/10009)
- Added MiniMax M2 C8 cache-scale support in GQA `load_weights`. [#10461](https://github.com/vllm-project/vllm-ascend/pull/10461)
- [Experimental] Added SSD support for multiple DP ranks on the same machine to avoid local-rank path collisions in Mooncake offload directories. [#10477](https://github.com/vllm-project/vllm-ascend/pull/10477)

### Hardware and Operator Support

- Added W8A8/W4A8 dynamic quantization support for Ascend 950. [#10236](https://github.com/vllm-project/vllm-ascend/pull/10236)
- Added Ascend 950 CPU binding support for Ascend 950 server topology and process layout. [#10483](https://github.com/vllm-project/vllm-ascend/pull/10483)

### Performance

- Optimized `split_qkv_tp_rmsnorm_rope` with grid-stride loading and host-side reciprocal precomputation; the PR reports about a 5x kernel speedup on the tested MiniMax-M2.5 W8A8 QuaRot prefill workload. [#9830](https://github.com/vllm-project/vllm-ascend/pull/9830)
- Reused prebuilt chunk host metadata for Ascend chunk ops to reduce host-device synchronization overhead on Qwen3.5 workloads. [#9310](https://github.com/vllm-project/vllm-ascend/pull/9310)
- Skipped `compute_slot_mapping` for Mamba groups to reduce unnecessary work in hybrid cache paths. [#10492](https://github.com/vllm-project/vllm-ascend/pull/10492)
- Enabled multistream DSV4 DSA overlap and removed redundant DSA v1 code paths. [#10518](https://github.com/vllm-project/vllm-ascend/pull/10518)

### Documentation

- Refreshed the context parallel, EPLB, and speculative decoding documentation. [#10332](https://github.com/vllm-project/vllm-ascend/pull/10332)
- Added Kimi 2.6 and GLM5.2 documentation. [#9969](https://github.com/vllm-project/vllm-ascend/pull/9969) [#10544](https://github.com/vllm-project/vllm-ascend/pull/10544)

### Known Issues

- MiniMax 2.7 dual-node 16-card deployments may hang or crash after 10-20 minutes under load. [#10591](https://github.com/vllm-project/vllm-ascend/issues/10591)
- Llama LoRA can still hit an einsum tensor-dimension mismatch on Ascend. [#10577](https://github.com/vllm-project/vllm-ascend/issues/10577)
- Qwen3.x with PD disaggregation plus MTP can still show precision issues because former KVCache blocks may remain dirty. [#10961](https://github.com/vllm-project/vllm-ascend/issues/10961)
- In A3 four-machine 2P1D deployments, Kimi-K2.6 can trigger `Error in KVCacheTransferThread. error=unhashable type: 'list'` on the D node under concurrent `terminal-bench2` testing. [#10962](https://github.com/vllm-project/vllm-ascend/issues/10962)
- With CANN 9.0.0, GLM5.1 1P1D four-machine deployments may hang during 140k-context performance tests, and Kimi-K2.5 with MC2 enabled may hit OOM on single-node A3. [#10963](https://github.com/vllm-project/vllm-ascend/issues/10963)
- Multi-level pooling remains an experimental feature and still has known issues, including DeepSeek-V4-Flash startup failures with Layerwise masks and service hangs in some Mooncake SSD scenarios. [#10964](https://github.com/vllm-project/vllm-ascend/issues/10964)

## v0.21.0rc1 - 2026.06.16

We're excited to announce the release of v0.21.0rc1 for vLLM Ascend. This is the first release candidate for the v0.21.0 release line, building on v0.20.2rc1. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- **DeepSeek-V4 for Ascend 950**: Full end-to-end support for DeepSeek-V4 on Ascend 950, including piecewise graph mode, DSA attention, KV cache management, and MTP. [#9757](https://github.com/vllm-project/vllm-ascend/pull/9757) [#9935](https://github.com/vllm-project/vllm-ascend/pull/9935)
- **Hybrid & Mamba Align Prefix Cache**: New alignment-based prefix caching mechanism for Hybrid and Mamba architectures, improving cache hit rates across related sequences. [#9533](https://github.com/vllm-project/vllm-ascend/pull/9533)
- **FULL_AND_PIECEWISE Graph Mode**: Introduced a hybrid graph compilation mode combining full-graph and piecewise strategies. **Requires HDK 25.5.1+ / CANN 8.5.0+** to remove the old stream-budget limitation, enabling up to ~32k graphs on A3 and ~64k on Ascend 950. [#9572](https://github.com/vllm-project/vllm-ascend/pull/9572) [#9962](https://github.com/vllm-project/vllm-ascend/pull/9962)
- **Python 3.12 Support**: Dockerfiles and setup.py now officially support Python 3.12, and all base images have been upgraded from `py3.11` to `py3.12`. [#9558](https://github.com/vllm-project/vllm-ascend/pull/9558)

### Features

- Added end-to-end support for DeepSeek-V4 on Ascend 950, including piecewise graph mode, DSA attention backend, KV cache management, distributed inference (with PP fixes), and MTP. [#9757](https://github.com/vllm-project/vllm-ascend/pull/9757) [#9473](https://github.com/vllm-project/vllm-ascend/pull/9473) [#9935](https://github.com/vllm-project/vllm-ascend/pull/9935)
- Added Hybrid & Mamba Align Prefix Cache for improved prefix cache reuse in Hybrid and Mamba architectures. [#9533](https://github.com/vllm-project/vllm-ascend/pull/9533)
- Added layerwise KV cache event callbacks for finer per-layer observability and control. [#9468](https://github.com/vllm-project/vllm-ascend/pull/9468)
- Added GLM4.7-Flash model support with Flash Attention backend. [#9560](https://github.com/vllm-project/vllm-ascend/pull/9560)
- Added `FULL_AND_PIECEWISE` graph mode, a hybrid compilation strategy mixing full-graph and piecewise approaches. **Requires HDK 25.5.1+ / CANN 8.5.0+** to remove the old stream-budget limitation, enabling significantly more graph captures — approximately 32k on A3 and 64k on Ascend 950. Legacy capture-size pruning has been cleaned up accordingly. [#9572](https://github.com/vllm-project/vllm-ascend/pull/9572) [#9962](https://github.com/vllm-project/vllm-ascend/pull/9962)
- Added W4A8 MXFP4 quantization support for Ascend 950. [#8265](https://github.com/vllm-project/vllm-ascend/pull/8265)
- Added MXFP8 FlashCommV3 support on Ascend 950. [#9671](https://github.com/vllm-project/vllm-ascend/pull/9671)
- Added NZ layout support for W4A8 MoE compressed tensors and C8 quantization (GQA). [#9625](https://github.com/vllm-project/vllm-ascend/pull/9625) [#9721](https://github.com/vllm-project/vllm-ascend/pull/9721)
- Added Mooncake Connector hybrid PCP/DCP support for QWen3.5. [#9809](https://github.com/vllm-project/vllm-ascend/pull/9809)
- Added D2D NetLoader weight loading for draft models in speculative decoding. [#9893](https://github.com/vllm-project/vllm-ascend/pull/9893)
- Added Mooncake Connector hybrid attention support. [#8850](https://github.com/vllm-project/vllm-ascend/pull/8850)
- Added Mooncake KV pool usage optimization. [#7820](https://github.com/vllm-project/vllm-ascend/pull/7820)
- Added KV Pool support for loading failure block IDs without hybrid recompute. [#9701](https://github.com/vllm-project/vllm-ascend/pull/9701)
- Added NPU storage metadata debug helpers for improved troubleshooting. [#9189](https://github.com/vllm-project/vllm-ascend/pull/9189)
- Added torch reserved/allocated memory profiling in `execute_model()`. [#9765](https://github.com/vllm-project/vllm-ascend/pull/9765)
- Added EPLB experts hotness metrics and EPLB time consumption data exposure. [#9536](https://github.com/vllm-project/vllm-ascend/pull/9536)
- Added `group_name` parameter when creating HCCL config for better group management. [#9667](https://github.com/vllm-project/vllm-ascend/pull/9667)
- Enabled prefix caching with PCP/DCP, allowing KV cache reuse across prefill and decode in disaggregated deployments. [#9638](https://github.com/vllm-project/vllm-ascend/pull/9638)
- Added simple yet general CPU KV Cache Offloading support. [#8743](https://github.com/vllm-project/vllm-ascend/pull/8743)
- Added Mooncake SSD offload with embedded client for large-scale KV cache storage. [#9731](https://github.com/vllm-project/vllm-ascend/pull/9731)
- Re-added code start compilation caching for npugraph_ex (previously reverted), improving warmup time. [#9914](https://github.com/vllm-project/vllm-ascend/pull/9914)
- Added ACL graph memory estimation before KV cache allocation to prevent OOM during graph capture. [#9865](https://github.com/vllm-project/vllm-ascend/pull/9865)
- Added DeepSeek-V4 compressor block size [32,64,128] support to improve automatic prefix cache hit rate. [#10354](https://github.com/vllm-project/vllm-ascend/pull/10354)
- Added batch_invariant_ops setup for reinforcement learning scenarios. [#10034](https://github.com/vllm-project/vllm-ascend/pull/10034)
- Adapted load balance proxy example to shared scheduler workers. [#9645](https://github.com/vllm-project/vllm-ascend/pull/9645)
- [310P] Added Qwen3.5 MTP and graph mode support. [#10309](https://github.com/vllm-project/vllm-ascend/pull/10309)

### Hardware and Operator Support

- Added custom GDN operator support for Ascend 950 with a new fused GDN gating AscendC operator (`fused_gdn_gating`). [#9382](https://github.com/vllm-project/vllm-ascend/pull/9382) [#9601](https://github.com/vllm-project/vllm-ascend/pull/9601)
- Added A2/A3 and Ascend 950 compressor operator paths. [#9350](https://github.com/vllm-project/vllm-ascend/pull/9350)
- Adapted GDN and Conv1D operators for the Ascend 950 platform. [#9224](https://github.com/vllm-project/vllm-ascend/pull/9224)
- Added Ascend 950 Dockerfiles and disaggregated PD endpoint configuration documentation. [#9723](https://github.com/vllm-project/vllm-ascend/pull/9723) [#9690](https://github.com/vllm-project/vllm-ascend/pull/9690)
- Removed unused MC2 prefill custom ops to streamline the operator surface. [#9919](https://github.com/vllm-project/vllm-ascend/pull/9919)
- Added Sparse Flash Attention support on Ascend 950 devices. [#9825](https://github.com/vllm-project/vllm-ascend/pull/9825)
- Added LightningIndexer and SparseFlashAttention ACLNN ops for improved sparse attention performance. [#9491](https://github.com/vllm-project/vllm-ascend/pull/9491)
- Added Rehash for AscendStore grouped keys to support DeepSeek V4 and compressed layouts. [#9789](https://github.com/vllm-project/vllm-ascend/pull/9789)

### Performance

- Optimized 310P MoE routing path for improved throughput. [#9105](https://github.com/vllm-project/vllm-ascend/pull/9105)
- Added NZ format support for W4A8 MoE compressed tensors, delivering better memory access patterns. [#9625](https://github.com/vllm-project/vllm-ascend/pull/9625)
- Added irregular mask build optimization for PCP/DCP with speculative decoding, improving efficiency. [#9678](https://github.com/vllm-project/vllm-ascend/pull/9678)
- Reconstructed reduce sampling to eliminate patch behaviors and support both DFlash and MTP. [#9735](https://github.com/vllm-project/vllm-ascend/pull/9735)

### Stability and Bug Fixes

- Fixed speculative decoding MLA shape mismatch with Eagle3 and added DeepSeek V2 Eagle3 support. [#9703](https://github.com/vllm-project/vllm-ascend/pull/9703)
- Fixed draft `lm_head` preservation for DFlash with reduced (draft-to-target) vocabulary. [#9795](https://github.com/vllm-project/vllm-ascend/pull/9795)
- Fixed a draft model index-out-of-range error caused by `token_indices_to_sample` on Ascend 950. [#9867](https://github.com/vllm-project/vllm-ascend/pull/9867)
- Added validation of DCP for draft models to catch configuration mismatches early. [#9717](https://github.com/vllm-project/vllm-ascend/pull/9717)
- Fixed multiple DeepSeek V4 PP issues. [#9473](https://github.com/vllm-project/vllm-ascend/pull/9473)
- Fixed DSA compressed idle dummy graph out-of-bounds issue. [#9818](https://github.com/vllm-project/vllm-ascend/pull/9818)
- Fixed HMA support in AscendMultiConnector. [#9782](https://github.com/vllm-project/vllm-ascend/pull/9782)
- Patched GLM47 inline zero-argument streaming tool calls. [#9901](https://github.com/vllm-project/vllm-ascend/pull/9901)
- Patched GLM tool-call final chunks for correct streaming termination. [#9787](https://github.com/vllm-project/vllm-ascend/pull/9787)
- Fixed empty `tool_calls` being emitted in OpenAI-format chat responses. [#9791](https://github.com/vllm-project/vllm-ascend/pull/9791)
- Backported MiniMax M2 tool call streaming support. [#9742](https://github.com/vllm-project/vllm-ascend/pull/9742)
- Repaired 310P Qwen3.5 ACLGraph precision. [#9727](https://github.com/vllm-project/vllm-ascend/pull/9727)
- Fixed precision of the `causal_conv1d_v310` operator on 310P. [#9720](https://github.com/vllm-project/vllm-ascend/pull/9720)
- Fixed ACL dtype mapping table for correct dtype conversions. [#9826](https://github.com/vllm-project/vllm-ascend/pull/9826)
- Chunked `wq_b` matmul to work around the NPU 65536 dimension limit. [#9780](https://github.com/vllm-project/vllm-ascend/pull/9780)
- Optimized router experts in eager mode and fixed communication handling. [#9728](https://github.com/vllm-project/vllm-ascend/pull/9728)
- Lazy initialization of KV store on `put` to avoid early resource allocation. [#9771](https://github.com/vllm-project/vllm-ascend/pull/9771)
- Fixed MTP placeholders exceeding max model length in P/D deployments. [#9749](https://github.com/vllm-project/vllm-ascend/pull/9749)
- Added compress ratio and block IDs cutting for Mooncake hybrid connector. [#9808](https://github.com/vllm-project/vllm-ascend/pull/9808)
- Fixed `qwen.png` FileNotFoundError in test assets. [#9907](https://github.com/vllm-project/vllm-ascend/pull/9907)
- Fixed backend unit test regressions. [#9805](https://github.com/vllm-project/vllm-ascend/pull/9805)
- Fixed PCP handshake port collision in Mooncake layerwise KV transfer connector. [#10019](https://github.com/vllm-project/vllm-ascend/pull/10019)
- Reduced Mooncake KV cache register regions for sparse C8 to avoid resource exhaustion. [#10102](https://github.com/vllm-project/vllm-ascend/pull/10102)
- Fixed W4A8 MXFP quantization in shared experts. [#10153](https://github.com/vllm-project/vllm-ascend/pull/10153)
- Fixed MoE hanging in multi-DP scenarios. [#10117](https://github.com/vllm-project/vllm-ascend/pull/10117)
- Fixed reduce sampling where `top_k` and `top_p` could be None. [#10004](https://github.com/vllm-project/vllm-ascend/pull/10004)
- Added environment variable to control DP metadata all_reduce communication. [#10046](https://github.com/vllm-project/vllm-ascend/pull/10046)
- Fixed `token_indices_to_sample` out-of-bounds index error. [#10080](https://github.com/vllm-project/vllm-ascend/pull/10080)
- Fixed `chunk_scaled_dot_kkt_fwd_kernel` accuracy issues. [#10033](https://github.com/vllm-project/vllm-ascend/pull/10033)
- Fixed DeepSeek-V4 compress attention groups prefix caching hit. [#9903](https://github.com/vllm-project/vllm-ascend/pull/9903)
- Fixed DSv4 piecewise graph scenario. [#10003](https://github.com/vllm-project/vllm-ascend/pull/10003)
- Fixed `split_qkv_rmsnorm_rope` Triton kernel accuracy on Ascend 950. [#9849](https://github.com/vllm-project/vllm-ascend/pull/9849)
- Fixed lm_head parallel feature assert and nightly test failures. [#10100](https://github.com/vllm-project/vllm-ascend/pull/10100)
- Fixed NPU MoE quantization methods to correctly support TP-only configurations. [#9908](https://github.com/vllm-project/vllm-ascend/pull/9908)
- Fixed stuck chunked pipeline parallelism by updating `discard_request_mask`. [#9843](https://github.com/vllm-project/vllm-ascend/pull/9843)
- Fixed `cudagraph_config` mode `FULL` corner case. [#9863](https://github.com/vllm-project/vllm-ascend/pull/9863)
- Fixed 310P Qwen3-Embedding and Qwen3-VL-Embedding run failures. [#9854](https://github.com/vllm-project/vllm-ascend/pull/9854)
- Removed legacy capture-size pruning in `update_aclgraph_sizes`. [#9962](https://github.com/vllm-project/vllm-ascend/pull/9962)
- Fixed `fused_gdn_gating` unavailability on Ascend 950 for Qwen3.5. [#10083](https://github.com/vllm-project/vllm-ascend/pull/10083)
- Fixed DSA v1 W8A8 dynamic conflict in attention. [#9476](https://github.com/vllm-project/vllm-ascend/pull/9476)
- Fixed DeepSeek-V4 compressed prefix lookup in prefix cache. [#10297](https://github.com/vllm-project/vllm-ascend/pull/10297)
- Fixed GLM streaming tool call name preservation. [#10361](https://github.com/vllm-project/vllm-ascend/pull/10361)
- Fixed GLM5.1-W8A8 MTP load weight error with vLLM v0.21.0. [#10317](https://github.com/vllm-project/vllm-ascend/pull/10317)
- Moved DeepSeek V4 cache hooks into model, removing legacy patch environment variables. [#10327](https://github.com/vllm-project/vllm-ascend/pull/10327) [#10333](https://github.com/vllm-project/vllm-ascend/pull/10333)
- Fixed FP32 MM encoder attention support. [#10200](https://github.com/vllm-project/vllm-ascend/pull/10200)
- Aligned vllm-ascend with upstream vLLM unit test expectations. [#10146](https://github.com/vllm-project/vllm-ascend/pull/10146)

### Dependencies

- **Python**: Python 3.12 is now officially supported and the default for all Docker images. Python 3.10 and 3.11 remain supported. [#9558](https://github.com/vllm-project/vllm-ascend/pull/9558)
- **Upstream vLLM**: Upgraded from v0.20.2 to v0.21.0. [#9835](https://github.com/vllm-project/vllm-ascend/pull/9835)
- **xlite**: Upgraded from `0.1.0rc9.dev210` to `0.1.0rc10.dev210`.
- **CANN**: 9.0.0 for A2/A3/Ascend 950 (unchanged from v0.20.2rc1); **310P uses CANN 9.1.0 beta**. **Note**: `FULL_AND_PIECEWISE` requires HDK 25.5.1+ / CANN 8.5.0+ for the stream-budget fix; older stacks are still limited by the legacy stream budget and may fall back to `PIECEWISE`.
- **PyTorch / torch_npu**: 2.10.0 (unchanged from v0.20.2rc1).
- **triton-ascend**: 3.2.1 (unchanged from v0.20.2rc1).
- **Mooncake**: Upgraded from v0.3.8.post1 to v0.3.9. [#10339](https://github.com/vllm-project/vllm-ascend/pull/10339)

### Breaking Changes and Migration Notes

- **`VLLM_ASCEND_ENABLE_CONTEXT_PARALLEL` Removed**: The environment variable `VLLM_ASCEND_ENABLE_CONTEXT_PARALLEL` has been removed as part of the migration to `AscendConfig`. Users should migrate any remaining uses to the equivalent AscendConfig option. [#9668](https://github.com/vllm-project/vllm-ascend/pull/9668)
- **DSA-CP Configuration Decoupling**: DSA-CP is now controlled via `additional_config.enable_dsa_cp`, decoupled from the FlashComm1 switch. Users who previously relied on FC1 implicitly enabling DSA-CP must now explicitly set both `enable_flashcomm1` and `enable_dsa_cp`. [#9697](https://github.com/vllm-project/vllm-ascend/pull/9697) [#9910](https://github.com/vllm-project/vllm-ascend/pull/9910)
- **Python 3.12 in Docker Images**: All Docker base images now use Python 3.12 (`py3.12`). If your deployment or custom images depend on `py3.11`, update your image tags accordingly. [#9558](https://github.com/vllm-project/vllm-ascend/pull/9558)

### Documentation

- Refreshed and optimized documentation for the current development branch. [#9606](https://github.com/vllm-project/vllm-ascend/pull/9606)
- Updated model-code converter writing guide. [#9881](https://github.com/vllm-project/vllm-ascend/pull/9881)
- Added DSA-CP configuration documentation for DeepSeek V3.2 and GLM5. [#9910](https://github.com/vllm-project/vllm-ascend/pull/9910)
- Added Ascend 950 disaggregated PD endpoint configuration documentation. [#9690](https://github.com/vllm-project/vllm-ascend/pull/9690)

### Known Issues

- **FULL_AND_PIECEWISE on older HDK/CANN**: HDK < 25.5.1 / CANN < 8.5.0 stacks still have the old stream-budget limitation, which may cause graph capture failures or fallback to `PIECEWISE` mode. Upgrade to HDK 25.5.1+ / CANN 8.5.0+ is recommended for full `FULL_AND_PIECEWISE` support.
- GLM5/GLM5.1 W4A8 deployments have known issues in some advanced configurations. CANN 9.0 with MC2 can return inaccurate output, FlashComm can fail during model startup, and MTP weight loading can fail in 1P1D A3 deployments. [#9395](https://github.com/vllm-project/vllm-ascend/issues/9395) [#9658](https://github.com/vllm-project/vllm-ascend/issues/9658) [#9655](https://github.com/vllm-project/vllm-ascend/issues/9655)
- GLM-5.1 deployments can hit `MoeDistributeDispatchV2`/NPU graph failures when Expert Parallel is used together with FULL graph mode. The reported workaround is to disable Expert Parallel for FULL graph mode, or use PIECEWISE/eager mode. [#9503](https://github.com/vllm-project/vllm-ascend/issues/9503)
- Qwen3.6-35B-A3B may shut down when MTP/speculative decoding is enabled, with `numAcceptedTokens[0]=4 exceeds varlen segment length=3` reported during shape/dtype processing. [#9956](https://github.com/vllm-project/vllm-ascend/issues/9956)
- GLM-5.1 can hang on the P node in 200k long-sequence 1P1D agent workloads after long-running service, with `MoeDistributeDispatchV2`/`aclnnMoeDistributeDispatchV4` reporting an AICore timeout. [#9958](https://github.com/vllm-project/vllm-ascend/issues/9958)
- GLM5 W4A8 deployments can see a significantly lower speculative decoding acceptance rate when MTP3 is used together with FlashComm. [#9803](https://github.com/vllm-project/vllm-ascend/issues/9803)
- **DeepSeek-V4 KV Pool**: When enabling KV Pool for DeepSeek-V4, the `--no-disable-hybrid-kv-cache-manager` flag must be added, otherwise the service will OOM at startup. Additionally, KV Pool for DSv4 stores all states for all compression ratio families — storing a sequence of 1M tokens takes approximately 300GB, which is the same behavior as upstream vLLM. [#9975](https://github.com/vllm-project/vllm-ascend/issues/9975)

## v0.20.2rc1 - 2026.06.03

We're excited to announce the release of v0.20.2rc1 for vLLM Ascend. This is the first release candidate for the v0.20.2 release line. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- **DeepSeek V4 Support**: Added end-to-end support for DeepSeek V4, including the model architecture, DSA attention backend, KV cache management, distributed inference, tool-call parser, MTP support, KV Pool adaptation, and custom operator enablement. [#9270](https://github.com/vllm-project/vllm-ascend/pull/9270) [#9385](https://github.com/vllm-project/vllm-ascend/pull/9385) [#9228](https://github.com/vllm-project/vllm-ascend/pull/9228)
- **Ascend 950 Products and XLite Quantization Expansion**: Added MXFP4 flatquant with row parallelism for Ascend 950 Products and expanded XLite support to GLM-4.7 W8A8 quantization. [#9391](https://github.com/vllm-project/vllm-ascend/pull/9391) [#9415](https://github.com/vllm-project/vllm-ascend/pull/9415)

### Features

- Added Flash Attention 3 support for training-inference consistency. The backend is ready in vLLM Ascend and will become directly usable once the FA3 package is publicly available. [#9060](https://github.com/vllm-project/vllm-ascend/pull/9060)
- Added DeepSeek-V3.1 PCP/DCP adaptation to improve support for disaggregated deployments on Ascend 950 Products. [#9058](https://github.com/vllm-project/vllm-ascend/pull/9058)
- Added a dedicated `additional_config.enable_dsa_cp` switch to decouple DSA-CP from FC1. DSA-CP now requires both FC1 and DSA-CP to be explicitly enabled, allowing FC1 to stay enabled while DSA-CP is disabled when needed. [#9878](https://github.com/vllm-project/vllm-ascend/pull/9878)
- Added merged graph support for DFlash workloads. [#9074](https://github.com/vllm-project/vllm-ascend/pull/9074)
- Added LoRA support for Qwen3.5 dense models. [#9023](https://github.com/vllm-project/vllm-ascend/pull/9023)
- Added KV pool adaptation for DeepSeek V4 and separated MTP-layer KV cache sharding for DeepSeek V4 speculative decoding. [#9385](https://github.com/vllm-project/vllm-ascend/pull/9385) [#9367](https://github.com/vllm-project/vllm-ascend/pull/9367)

### Hardware and Operator Support

- Added DeepSeek V4 custom operators required for the new model path, registered the operators for Ascend 910B, and switched the DeepSeek V4 `hc_pre` path to a fused operator. [#9228](https://github.com/vllm-project/vllm-ascend/pull/9228) [#9339](https://github.com/vllm-project/vllm-ascend/pull/9339) [#9396](https://github.com/vllm-project/vllm-ascend/pull/9396)
- Enabled MXFP4 flatquant and row parallel support on Ascend 950 Products. [#9391](https://github.com/vllm-project/vllm-ascend/pull/9391)
- Enabled MC2 dispatch and combine support for MXFP4/MXFP8 quantization on Ascend 950 Products. [#9365](https://github.com/vllm-project/vllm-ascend/pull/9365) [#9328](https://github.com/vllm-project/vllm-ascend/pull/9328)
- Improved 310P support by optimizing fused operators for Qwen3.5 Dense ACLGraph and simplifying the 310P RMSNormGated path. [#9104](https://github.com/vllm-project/vllm-ascend/pull/9104) [#9489](https://github.com/vllm-project/vllm-ascend/pull/9489)

### Performance

- Added DeepSeek V4 DSA multistream overlap optimizations across compressor, indexer-select, CV parallel, and pure-prefill compute-communication overlap paths. [#9450](https://github.com/vllm-project/vllm-ascend/pull/9450) [#9441](https://github.com/vllm-project/vllm-ascend/pull/9441) [#9433](https://github.com/vllm-project/vllm-ascend/pull/9433) [#9504](https://github.com/vllm-project/vllm-ascend/pull/9504)
- Reused DSA `topk_indices` across decode steps with IndexCache to reduce repeated DeepSeek V4 index computation. [#9390](https://github.com/vllm-project/vllm-ascend/pull/9390)
- Fixed the missing enablement for `cv_indexer_qkv_prepare` multistream parallelism in the new overlap path. [#9530](https://github.com/vllm-project/vllm-ascend/pull/9530)
- Reduced host-device synchronization overhead by removing the sync point in PIECEWISE mode. [#9025](https://github.com/vllm-project/vllm-ascend/pull/9025)
- Optimized shared expert overlap timing in FusedMoE. [#9413](https://github.com/vllm-project/vllm-ascend/pull/9413)
- [Experimental] Added reduce sampling with `enable_reduce_sample` to lower Tensor Parallel communication overhead in distributed greedy, top-k/top-p, and rejection sampling paths. [#8308](https://github.com/vllm-project/vllm-ascend/pull/8308)

### Stability and Bug Fixes

- Fixed DeepSeek V4 MTP, serial inference, FlashComm, A2 tensor-output all-reduce, and P/D disaggregation KV cache edge cases. [#9456](https://github.com/vllm-project/vllm-ascend/pull/9456) [#9487](https://github.com/vllm-project/vllm-ascend/pull/9487) [#9488](https://github.com/vllm-project/vllm-ascend/pull/9488) [#9389](https://github.com/vllm-project/vllm-ascend/pull/9389) [#9500](https://github.com/vllm-project/vllm-ascend/pull/9500)
- Fixed DeepSeek V4 `hc_pre` behavior and added a 4-card E2E regression test. [#9452](https://github.com/vllm-project/vllm-ascend/pull/9452)

### Dependencies

- Upgraded the matched upstream vLLM baseline to v0.20.2. [#9270](https://github.com/vllm-project/vllm-ascend/pull/9270)
- Upgraded CANN to 9.0.0 and triton-ascend to 3.2.1. [#9085](https://github.com/vllm-project/vllm-ascend/pull/9085)
- Upgraded PyTorch and TorchNPU to 2.10.0. [#9128](https://github.com/vllm-project/vllm-ascend/pull/9128)

### Breaking Changes and Migration Notes

- Migrated a set of runtime options from environment variables to `AscendConfig`, including the FC1/FlashComm1 switch from `VLLM_ASCEND_ENABLE_FLASHCOMM1` to `additional_config.enable_flashcomm1`. Please review configuration code and deployment manifests when upgrading. [#9064](https://github.com/vllm-project/vllm-ascend/pull/9064)
- Disabled SwiGLU clamp by default, which may slightly change behavior for workloads that previously relied on the old default. [#9438](https://github.com/vllm-project/vllm-ascend/pull/9438)

### Documentation

- Refreshed deployment and feature documentation for the current main branch release line. [#9309](https://github.com/vllm-project/vllm-ascend/pull/9309) [#8968](https://github.com/vllm-project/vllm-ascend/pull/8968)
- Added documentation for the `enable_dsa_cp` additional configuration option for DeepSeek V3.2 and GLM5. [#9910](https://github.com/vllm-project/vllm-ascend/pull/9910)

### Known Issues

- GLM5/GLM5.1 W4A8 deployments have known issues in some advanced configurations. [#9395](https://github.com/vllm-project/vllm-ascend/issues/9395)
- Qwen3.6-35B-A3B may shut down when MTP/speculative decoding is enabled, with `numAcceptedTokens[0]=4 exceeds varlen segment length=3` reported during shape/dtype processing. [#9956](https://github.com/vllm-project/vllm-ascend/issues/9956)
- GLM-5.1 can hang on the P node in 200k long-sequence 1P1D agent workloads after long-running service, with `MoeDistributeDispatchV2`/`aclnnMoeDistributeDispatchV4` reporting an AICore timeout. [#9958](https://github.com/vllm-project/vllm-ascend/issues/9958)
- GLM5 W4A8 deployments can see a significantly lower speculative decoding acceptance rate when MTP3 is used together with FlashComm. [#9803](https://github.com/vllm-project/vllm-ascend/issues/9803)
- MiniMax-M2.7 W8A8/QuaRot can show lower-than-expected GPQA accuracy in long-sequence deployments when PCP/DCP is combined with Eagle3 speculative decoding. [#9959](https://github.com/vllm-project/vllm-ascend/issues/9959)
- KV Pool feature for DeepSeek V4 now faces several known issues affecting user-friendliness and performance, including special startup parameter requirements, special key storing behaviors, etc. For details, please refer to issue [#9975](https://github.com/vllm-project/vllm-ascend/issues/9975).

## v0.18.0 - 2026.04.30

We're excited to announce the release of v0.18.0 for vLLM Ascend. This is the official release for v0.18.0. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.18.0) to get started.

### Highlights

**Model Support**

- **Kimi-K2.x Model Support**: [Experimental]Added support for Kimi-K2.x models. @aipaes @dragondream-chen @SparrowMu @LoganJane [#6755](https://github.com/vllm-project/vllm-ascend/pull/6755)
- **Minimax-m2.x Model Support**: [Experimental]Added support for Minimax-m2.x models with eagle3. @SparrowMu @GDzhu01 [#7105](https://github.com/vllm-project/vllm-ascend/pull/7105) [#7714](https://github.com/vllm-project/vllm-ascend/pull/7714)
- **GLM5 Support**: [Experimental]Added support for GLM5 models without any code modification!
- **Qwen3.x Support**: [Experimental]Added support for Qwen3.x models without any code modification!
- **DeepseekOCR Support**: [Experimental]Added support for DeepseekOCR model and optimize `RelPosAttention` and `CustomQwen2Decoder`. @Wangbei25 [#7737](https://github.com/vllm-project/vllm-ascend/pull/7737)

**Core Features**

- **EPLB (Expert Parallelism Load Balance)**: EPLB is more stable with many bug fixes, and has better performance now. EPLB now works in most cases and is recommended for use. [#6528](https://github.com/vllm-project/vllm-ascend/pull/6528) [#7344](https://github.com/vllm-project/vllm-ascend/pull/7344) [#7890](https://github.com/vllm-project/vllm-ascend/pull/7890) [#6477](https://github.com/vllm-project/vllm-ascend/pull/6477)
- **ACLGraph Enhancement**: ACLGraph now support capturing a single merged graph for multi-step drafts, which greatly reduce host bound in multi-step spec decoding case! [#5553](https://github.com/vllm-project/vllm-ascend/pull/5553) [#5940](https://github.com/vllm-project/vllm-ascend/pull/5940)
- **KV Pooling**: Enhanced KV pool with Mooncake connector now support sparse attention, and LMCacheAscendConnector is added as a new KV cache pooling solution for Ascend, and support FabricMem Mode for HIXL interconnect, support yuanrong as a backend for AscendStoreConnector, and now MooncakeLayerwiseConnector can be activated together with KV Pooling. Compared with previous versions, KV Pooling has a huge performance optimization on TTFT! [#6339](https://github.com/vllm-project/vllm-ascend/pull/6339) [#6882](https://github.com/vllm-project/vllm-ascend/pull/6882) [#6806](https://github.com/vllm-project/vllm-ascend/pull/6806) [#6869](https://github.com/vllm-project/vllm-ascend/pull/6869) [#7032](https://github.com/vllm-project/vllm-ascend/pull/7032)
- **PD disaggregation**: Mooncake layerwise connector now support hybrid attention manager and PCP feature. [#7022](https://github.com/vllm-project/vllm-ascend/pull/7022) [#6627](https://github.com/vllm-project/vllm-ascend/pull/6627)
- **NPU Graph EX (npugraph_ex) Enabled by Default**: The npugraph_ex feature is now enabled by default, providing better graph optimization with integrated inductor pass and MatmulAllReduceAddRMSNorm fusion. [#6354](https://github.com/vllm-project/vllm-ascend/pull/6354) [#6664](https://github.com/vllm-project/vllm-ascend/pull/6664) [#6006](https://github.com/vllm-project/vllm-ascend/pull/6006)
- **RL(Reinforcement learning)**: [Experimental]RL enhanced with implemented batch invariant feature with AscendC and triton op, and added routing replay feature. [#6590](https://github.com/vllm-project/vllm-ascend/pull/6590) [#6696](https://github.com/vllm-project/vllm-ascend/pull/6696)
- **CPU Binding Enabled by Default**: Enabled ARM-only CPU binding with global-slicing A3 policy, improving inference throughput in hostbound scenarios. [#6686](https://github.com/vllm-project/vllm-ascend/pull/6686)

### Features

- Prefix cache is now supported in hybrid model. [#7103](https://github.com/vllm-project/vllm-ascend/pull/7103)
- Flash Comm V1 now supports VL models with MLA, removing a previous limitation for multimodal serving. [#7390](https://github.com/vllm-project/vllm-ascend/pull/7390)
- VL MoE models now support SP, and `sp_threshold` is removed in favor of `sp_min_token_num` from vLLM. [#7044](https://github.com/vllm-project/vllm-ascend/pull/7044)
- [Experimental]Pipeline Parallel now supports async scheduling, improving throughput for PP deployments. [#7136](https://github.com/vllm-project/vllm-ascend/pull/7136)
- Eagle3 now supports QuaRot quantization without embedding. [#7038](https://github.com/vllm-project/vllm-ascend/pull/7038)
- Refactoring eagle3/mtp, eagle3 and mtp are now using the same proposer. [#6349](https://github.com/vllm-project/vllm-ascend/pull/6349) [#7033](https://github.com/vllm-project/vllm-ascend/pull/7033)

### Hardware and Operator Support

- **First time support 310P, with huge performance optimization!**:
    - support W8A8 quantization. [#6641](https://github.com/vllm-project/vllm-ascend/pull/6641) [#6454](https://github.com/vllm-project/vllm-ascend/pull/6454)
    - support weightNZ with quant and unquant case. [#6705](https://github.com/vllm-project/vllm-ascend/pull/6705)
    - support W8A8SC quantization. [#7075](https://github.com/vllm-project/vllm-ascend/pull/7075)
    - fix post-sampling not working in graph mode. [#8077](https://github.com/vllm-project/vllm-ascend/pull/8077)
    - Added addrmsnorm support for 300I DUO. [#6704](https://github.com/vllm-project/vllm-ascend/pull/6704)
    - Fix ngram graph replay accuracy error on 310P. [#7134](https://github.com/vllm-project/vllm-ascend/pull/7134)
- **Custom Operators**: Added multiple custom operators including:
    - Added AscendC casual_conv1d_fn operator for Qwen3-Next. [#6661](https://github.com/vllm-project/vllm-ascend/pull/6661)
    - Added Ascend Ops recurrent_gated_delta_rule operator. [#6725](https://github.com/vllm-project/vllm-ascend/pull/6725)
    - Added GMM custom operator for MoE models. [#7010](https://github.com/vllm-project/vllm-ascend/pull/7010)
    - Optimize split_qkv_rmsnorm_rope operator. [#6827](https://github.com/vllm-project/vllm-ascend/pull/6827)
    - Triton rope now supports index_selecting from cos_sin_cache. [#5450](https://github.com/vllm-project/vllm-ascend/pull/5450)
    - Added AscendC fused op transpose_kv_cache_by_block to speed up GQA transfer. [#6366](https://github.com/vllm-project/vllm-ascend/pull/6366)
    - Optimized `DispatchFFNCombine` kernel performance and resolved vector error caused by unaligned UB access. [#6468](https://github.com/vllm-project/vllm-ascend/pull/6468) [#6707](https://github.com/vllm-project/vllm-ascend/pull/6707)
    - Refactor and optimize CausalConv1d. [#7495](https://github.com/vllm-project/vllm-ascend/pull/7495)

### Performance

- **Initialize Performance**: Optimized Triton operator recompilation to reduce redundant rebuilds and unnecessary recompilation triggered by function parameter optimization. [#7647](https://github.com/vllm-project/vllm-ascend/pull/7647) [#7645](https://github.com/vllm-project/vllm-ascend/pull/7645)
- **Qwen3.x Performance**: [Experimental]Optimized the Qwen3.x and Qwen3-Next performance by supporting full graph mode, PD disaggregation, mamba prefill prefix-caching and flashcomm1, prebuilding chunk metadata to reducing host-device synchronization overhead, and multiple op performance optimization including `chunk_gated_delta_rule`, `chunk_fwd_kernel_o`, `solve_tril`, `recompute_w_u_fwd_kernel`, `split_qkv_rmsnorm_mrope`, etc. @LoganJane @shaopeng-666 @ppppeng @SunnyLee151064 @hust17yixuan @Toneymiller @linfeng-yuan [#7487](https://github.com/vllm-project/vllm-ascend/pull/7487) [#6830](https://github.com/vllm-project/vllm-ascend/pull/6830) [#7506](https://github.com/vllm-project/vllm-ascend/pull/7506) [#7796](https://github.com/vllm-project/vllm-ascend/pull/7796) [#7527](https://github.com/vllm-project/vllm-ascend/pull/7527) [#7529](https://github.com/vllm-project/vllm-ascend/pull/7529) [#7495](https://github.com/vllm-project/vllm-ascend/pull/7495) [#7368](https://github.com/vllm-project/vllm-ascend/pull/7368)
- **Kimi-K2.x Performance**: [Experimental]Optimized the Kimi-K2.x performance by supporting eagle3 and flashcomm1, and reducing d2h overhead. @aipaes @dragondream-chen @SparrowMu @LoganJane @GDzhu01 @Yaphets24 @hust17yixuan [#7342](https://github.com/vllm-project/vllm-ascend/pull/7342) [#7390](https://github.com/vllm-project/vllm-ascend/pull/7390) [#7521](https://github.com/vllm-project/vllm-ascend/pull/7521)
- **Qwen3-VL Performance**: Qwen3-VL gets stronger multimodal operator enablement with Flash Comm V1 and `qkv_rmsnorm_mrope` support, and enable 2.7x faster for convolution computation with aclnn BatchMatMulV2, support EAGLE speculative decoding. [#7893](https://github.com/vllm-project/vllm-ascend/pull/7893) [#7852](https://github.com/vllm-project/vllm-ascend/pull/7852) [#7017](https://github.com/vllm-project/vllm-ascend/pull/7017) [#6327](https://github.com/vllm-project/vllm-ascend/pull/6327)
- **Qwen3-Omni Performance**: Qwen3-Omni quantization adaptation and optimization is now available. [#6828](https://github.com/vllm-project/vllm-ascend/pull/6828)
- **DeepSeek-V3.2/GLM5 Performance**: Performance optimizations, support W8A8C8 quantization, and optimized KV cache usage. @yydyzr @ZYang6263 @rjg-lyh @Nagisa125 [#7029](https://github.com/vllm-project/vllm-ascend/pull/7029) [#6610](https://github.com/vllm-project/vllm-ascend/pull/6610)
- **GLM4.7-Flash Performance**: Added W8A8 quantization support for GLM4.7-Flash. @aipaes [#6492](https://github.com/vllm-project/vllm-ascend/pull/6492)

### Dependencies

- **vLLM**: Upgraded to 0.18.0 and dropped 0.17.0 support.
- **CANN**: Upgraded to 8.5.1. **PS:** AscendStoreConnector with FabricMem mode, 310P device supporting and Qwen3-Omni model need upgrades CANN version to 9.0.0, if you need these features, please upgrade manually.
- **TorchNPU**: Upgraded to 2.9.0.post1+git4c901a4 because of some known issue. This version can't install by default, please upgrade manually. We can get installation pkg from this link: <https://vllm-ascend.obs.cn-north-4.myhuaweicloud.com/vllm-ascend/torch_npu-2.9.0.post1%2Bgit4c901a4-${PYTHON_TAG}-${PYTHON_TAG}-manylinux_2_28_${ARCH}.whl>. **PS:** If CANN has been upgraded to version 9.0.0, please upgrade TorchNPU version to 2.9.0.post2 synchronously.
- **triton-ascend**: Upgraded to 3.2.0.dev20260322 because of some known issue. This version can't install by default, please upgrade manually. We can get installation pkg from this link: <https://vllm-ascend.obs.cn-north-4.myhuaweicloud.com/vllm-ascend/triton_ascend-3.2.0.dev20260322-${PYTHON_TAG}-${PYTHON_TAG}-manylinux_2_27_${ARCH}.manylinux_2_28_${ARCH}.whl>. **PS:** If CANN has been upgraded to version 9.0.0, please upgrade triton-ascend version to 3.2.1 synchronously.
- **Transformers**: Upgraded to >= 4.57.4.
- **Mooncake**: Upgraded to 3.9.0.

> \${PYTHON_TAG} is python version tag, and \${ARCH} is cpu architecture.
>
> For example: python3.11 and aarch64, \${PYTHON_TAG}=cp311, \${ARCH}=aarch64.

### Deprecation & Breaking Changes

- Cleaned up and deprecated ProfileExecuteDuration feature. [#6461](https://github.com/vllm-project/vllm-ascend/pull/6461)
- Removed custom rotary_embedding operator. [#6523](https://github.com/vllm-project/vllm-ascend/pull/6523)
- Cleaned up unused env `USE_OPTIMIZED_MODEL`. [#6618](https://github.com/vllm-project/vllm-ascend/pull/6618)
- `enable_flash_comm_v1` config option has been renamed back to `enable_sp`. [#6883](https://github.com/vllm-project/vllm-ascend/pull/6883)

### Documentation

- Add a new introduction for MiniMax-M2.5 and MiniMax-M2.7. [#8169](https://github.com/vllm-project/vllm-ascend/pull/8169)
- Add preemption guidance in FAQs. [#8136](https://github.com/vllm-project/vllm-ascend/pull/8136)
- Update the deployment and support documentation for GLM5, including parameter descriptions, best practices, and FAQs. [#7963](https://github.com/vllm-project/vllm-ascend/pull/7963) [#7909](https://github.com/vllm-project/vllm-ascend/pull/7909)
- Update the Qwen3.5 user guide. [#7934](https://github.com/vllm-project/vllm-ascend/pull/7934)
- Update the document configuration for DeepSeek-V3.2. [#7970](https://github.com/vllm-project/vllm-ascend/pull/7970)
- Clean up documentation wording and grammar. [#8073](https://github.com/vllm-project/vllm-ascend/pull/8073)
- Refreshed deployment and model docs for Kimi-K2.5, GLM-4.7, DeepSeek-V3.2, MiniMax-M2.5, and PD disaggregation guides. [#7371](https://github.com/vllm-project/vllm-ascend/pull/7371) [#7403](https://github.com/vllm-project/vllm-ascend/pull/7403) [#7292](https://github.com/vllm-project/vllm-ascend/pull/7292) [#7296](https://github.com/vllm-project/vllm-ascend/pull/7296) [#7300](https://github.com/vllm-project/vllm-ascend/pull/7300)
- Added user/developer guide for CPU binding. [#7045](https://github.com/vllm-project/vllm-ascend/pull/7045)
- Added Memcache Usage Guide. [#6476](https://github.com/vllm-project/vllm-ascend/pull/6476)
- Added Benchmark Tutorial for Suffix Speculative Decoding. [#6323](https://github.com/vllm-project/vllm-ascend/pull/6323)
- Added npugraph_ex introduction documentation. [#6306](https://github.com/vllm-project/vllm-ascend/pull/6306)

### Others

- Add async communication checks for capturing mode. [#8149](https://github.com/vllm-project/vllm-ascend/pull/8149)
- Fix KV Pool conflicts between pooling scenarios and fix missing KV cache placement on vLLM v0.18.0. [#8101](https://github.com/vllm-project/vllm-ascend/pull/8101) [#7874](https://github.com/vllm-project/vllm-ascend/pull/7874)
- Fix short-prompt forwarding by correcting attention state handling. [#8088](https://github.com/vllm-project/vllm-ascend/pull/8088)
- Restore `global_bs=0` and `mc2_mask` for uniform-token dispatching, and support inter-node RoCE hierarchical MC2 communication. [#8040](https://github.com/vllm-project/vllm-ascend/pull/8040)
- Fix the weights mapper bug of Qwen3-VL. [#7868](https://github.com/vllm-project/vllm-ascend/pull/7868)
- Fixed quantization config key mapping in `AscendModelSlimConfig` by switching from reverse mapping to forward mapping. [#7716](https://github.com/vllm-project/vllm-ascend/pull/7716)
- Fixed support for ALL D-Nodes in full graph when running MTP in PD deployment. [#5472](https://github.com/vllm-project/vllm-ascend/pull/5472)
- Layerwise connector now supports recompute scheduler. [#5900](https://github.com/vllm-project/vllm-ascend/pull/5900)
- Fixed pooling code issues and updated usage guide. [#6126](https://github.com/vllm-project/vllm-ascend/pull/6126)
- NPUWorker Profiler now supports profile_prefix for better profiling experience. [#6968](https://github.com/vllm-project/vllm-ascend/pull/6968)

### Known Issue

- Currently, `VLLM_ASCEND_ENABLE_FUSED_MC2` is not recommended for multi-DP and large number of tokens case(`kv_producer` or `kv_both`), this case may create large number of padded tokens across dp, which will be routed to certain experts, and make certain ranks receive tokens overload, resulting accuracy and performance issues. [#8320](https://github.com/vllm-project/vllm-ascend/issues/8320)
- Currently, EPLB cannot support `minimax_m2` model and W4A8 quantization. [#8341](https://github.com/vllm-project/vllm-ascend/issues/8341)
- PCP and eagle3 overlaying may generate error when a prefill req's scheduled token number is smaller than `1 + num_speculative_tokens`, which will make this prefill req be treated as a decode req, resulting in an error. [#8402](https://github.com/vllm-project/vllm-ascend/issues/8402)
- NPU soft partitioning + `CUDAGraphMode.PIECEWISE` is not supported. [#8585](https://github.com/vllm-project/vllm-ascend/issues/8585)
- Qwen3.x now has accuracy issue with PD disaggregation case. [#8421](https://github.com/vllm-project/vllm-ascend/issues/8421)
- Currently, there is a known issue on x86 arch, and this issue has been resolved with CANN 9.0.0, if you want to deploy vllm-ascend on x86, please upgrade CANN version manually. [#7993](https://github.com/vllm-project/vllm-ascend/issues/7993)
- P/D proxy may leak resources on recomputed retry and mask metaserver errors after. [#8852](https://github.com/vllm-project/vllm-ascend/issues/8852)
- When deploying GLM5 and Deepseek V3.2 separately via PD architecture, there is a probabilistic issue of empty output or garbled characters. [#8853](https://github.com/vllm-project/vllm-ascend/issues/8853)
- For GLM 5/5.1 under PD separation which D node setup with TP16 DP2 parallelism, the GPQA accuracy fell short of the standard. [#8844](https://github.com/vllm-project/vllm-ascend/issues/8844)

## v0.19.1rc1 - 2026.04.30

This is the first release candidate of v0.19.1 for vLLM Ascend, based on vLLM v0.19.1. This release includes significant performance optimizations, new model support, hardware expansion, and important bug fixes.

Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- **DFlash Attention Backend**: Added DFlash attention backend with FULL_DECODE_ONLY support for improved inference performance ([#8118](https://github.com/vllm-project/vllm-ascend/pull/8118), [#8516](https://github.com/vllm-project/vllm-ascend/pull/8516), [#8627](https://github.com/vllm-project/vllm-ascend/pull/8627))
- **Zero Bubble Async Scheduling**: Implemented zero bubble optimization for async scheduling and speculative decoding, significantly reducing scheduling overhead ([#7640](https://github.com/vllm-project/vllm-ascend/pull/7640))
- **A2/A3 Attention Operator Upgrade**: Replaced npu_fusion_attention with _npu_flash_attention_unpad operator for better performance on A2 and A3 hardware ([#8671](https://github.com/vllm-project/vllm-ascend/pull/8671))
- **Eagle3 + MiniMax-M2.5 Support**: Applied Eagle3 speculative decoding to MiniMax-M2.5 model for faster inference ([#7619](https://github.com/vllm-project/vllm-ascend/pull/7619))
- **C8 INT8 KV Cache for GQA**: Added C8 (INT8 KV cache) support for GQA attention models, including DeepSeek-V3.1 with PD disaggregation ([#7474](https://github.com/vllm-project/vllm-ascend/pull/7474), [#7222](https://github.com/vllm-project/vllm-ascend/pull/7222))
- **Bailing Model Support**: Full support for Bailing MoE model including linear adaptation and ModelSlim quantization ([#8657](https://github.com/vllm-project/vllm-ascend/pull/8657), [#8709](https://github.com/vllm-project/vllm-ascend/pull/8709))

### Features

- **Flash Comm V1 for Qwen3-VL**: Support Flash Comm V1 for Qwen3-VL multimodal models ([#7897](https://github.com/vllm-project/vllm-ascend/pull/7897))
- **Eagle + PCP + Full Graph Mode**: Support Eagle combined with PCP and full graph mode ([#7924](https://github.com/vllm-project/vllm-ascend/pull/7924))
- **Multimodal Reasoning with PCP**: Support multimodal reasoning when prefill context parallel feature is enabled ([#8038](https://github.com/vllm-project/vllm-ascend/pull/8038))
- **Dynamic Chunk for PP**: Support Dynamic Chunk for Chunked Pipeline Parallelism ([#7896](https://github.com/vllm-project/vllm-ascend/pull/7896))
- **Hamming-based Sparse Attention**: Added Hamming-based sparse attention inference framework and operators ([#8564](https://github.com/vllm-project/vllm-ascend/pull/8564), [#8346](https://github.com/vllm-project/vllm-ascend/pull/8346))
- **Optimized Causal Conv1d Operator**: Added optimized causal conv1d operator ([#8215](https://github.com/vllm-project/vllm-ascend/pull/8215))
- **Recurrent AscendC Operators**: Added recurrent AscendC operators for specific model architectures ([#8055](https://github.com/vllm-project/vllm-ascend/pull/8055))
- **GLM4.7 C8 Support**: Support GLM4.7 with C8 (INT8 KV cache) scenarios ([#8174](https://github.com/vllm-project/vllm-ascend/pull/8174))
- **Minitron-8B-Base Support**: Verified and supported nvidia/Minitron-8B-Base model ([#8157](https://github.com/vllm-project/vllm-ascend/pull/8157))
- **Bailing Model Support**: Full support for Bailing MoE model with linear adaptation and ModelSlim quantization configuration ([#8657](https://github.com/vllm-project/vllm-ascend/pull/8657), [#8709](https://github.com/vllm-project/vllm-ascend/pull/8709))
- **Qwen3.5 MoE Flash Comm**: Support Flash Comm for Qwen3.5 MoE models ([#7486](https://github.com/vllm-project/vllm-ascend/pull/7486))
- **Initial MoE Support for MRv2**: Add initial MoE models support for Model Runner V2 ([#7922](https://github.com/vllm-project/vllm-ascend/pull/7922))
- **Xlite Backend Expansion**:
    - XLite GLM-4.7 support ([#7935](https://github.com/vllm-project/vllm-ascend/pull/7935))
    - Support Qwen3VLMoeForConditionalGeneration in xlite backend ([#8046](https://github.com/vllm-project/vllm-ascend/pull/8046))
- **EPLB Enhancements**:
    - Swift balancer policy supports mix placement ([#8035](https://github.com/vllm-project/vllm-ascend/pull/8035))
    - EPLB adaptation to multimodal models ([#7743](https://github.com/vllm-project/vllm-ascend/pull/7743))
- **Eagle Improvements for model_runner_v2**:
    - Fixed Eagle's acceptance rate problem in graph mode ([#8365](https://github.com/vllm-project/vllm-ascend/pull/8365))
    - Fixed Eagle's precision problems ([#8230](https://github.com/vllm-project/vllm-ascend/pull/8230), [#8033](https://github.com/vllm-project/vllm-ascend/pull/8033))
    - Adapted Eagle for model_runner_v2 ([#7885](https://github.com/vllm-project/vllm-ascend/pull/7885))
- **MTP Merged Graph**: Support merged graph for MTP (Multi-Token Prediction) ([#6860](https://github.com/vllm-project/vllm-ascend/pull/6860))
- **Unified MoE Expert Placement**: Support unified placement for shared & router experts ([#7188](https://github.com/vllm-project/vllm-ascend/pull/7188))
- **Dispatch V2 Hierarchy Communication**: Support dispatch_v2/combine_v2 hierarchy communication for better MoE performance ([#7583](https://github.com/vllm-project/vllm-ascend/pull/7583))
- **Xmask for Dispatch FFN Combine**: Add xmask feature for dispatch_ffn_combine operator (w8a8 branch) ([#8560](https://github.com/vllm-project/vllm-ascend/pull/8560))
- **Fused W4A8 Kernel**: Fuse W4A8 dispatch + FFN + combine into a single fused kernel ([#7779](https://github.com/vllm-project/vllm-ascend/pull/7779))
- **KV Cache Memory Accounting**: Account for graph capture memory in KV cache planning ([#8289](https://github.com/vllm-project/vllm-ascend/pull/8289))
- **Qwen3-Next Hybrid Attention**: Support Qwen3-next hybrid attention in piecewise & full_decode_only modes ([#7422](https://github.com/vllm-project/vllm-ascend/pull/7422))
- **GDN Optimization**: Optimize GDN non-spec prefill fallback metadata ([#7756](https://github.com/vllm-project/vllm-ascend/pull/7756))
- **Qwen3-VL Support**: Support kv_rmsnorm_mrope for Qwen3-VL ([#7762](https://github.com/vllm-project/vllm-ascend/pull/7762))
- **Mamba Prefix Caching**: Layerwise connector supports Mamba prefill prefix caching ([#7814](https://github.com/vllm-project/vllm-ascend/pull/7814))
- **Yuanrong KV Pool Backend**: Add Yuanrong backend support to KV Pool ([#6869](https://github.com/vllm-project/vllm-ascend/pull/6869))

### Hardware and Operator Support

- **310P Enhancements**:
    - Qwen3.5 model adaptation synchronized with main ([#8009](https://github.com/vllm-project/vllm-ascend/pull/8009))
    - Support W8A8 dynamic linear method ([#7725](https://github.com/vllm-project/vllm-ascend/pull/7725))
    - Support shared experts path in fused MoE for Qwen3.5 ([#7674](https://github.com/vllm-project/vllm-ascend/pull/7674))
    - Add npu_causal_conv1d_310 AscendC Custom Op ([#7798](https://github.com/vllm-project/vllm-ascend/pull/7798))
    - Add recurrent_gated_delta_rule_310 AscendC Custom Op ([#7926](https://github.com/vllm-project/vllm-ascend/pull/7926))

### Performance

- **A2/A3 Attention**: Replace npu_fusion_attention with _npu_flash_attention_unpad operator for better performance ([#8671](https://github.com/vllm-project/vllm-ascend/pull/8671))
- **MLA PCP Prefill Optimization**: Optimize MLA PCP prefill attention by avoiding projecting unnecessary tail KV tokens ([#8787](https://github.com/vllm-project/vllm-ascend/pull/8787))
- **Async Scheduling Optimization**:
    - Asynchronous scheduling issuance bubble optimization ([#8766](https://github.com/vllm-project/vllm-ascend/pull/8766))
    - Zero bubble async scheduling and spec decoding ([#7640](https://github.com/vllm-project/vllm-ascend/pull/7640))
- **KV Cache Optimization**:
    - Batch KV cache offloading via aclrtMemcpyBatchAsync ([#7819](https://github.com/vllm-project/vllm-ascend/pull/7819))
    - Optimize KV cache gathering by selecting blocks before all-gather ([#8050](https://github.com/vllm-project/vllm-ascend/pull/8050))
- **Operator Optimizations**:
    - Optimize split_qkv_tp_rmsnorm_rope ops ([#8059](https://github.com/vllm-project/vllm-ascend/pull/8059))
    - Optimize host-device sync problem in prefill phase for Qwen3Next/Qwen3.5 ([#7967](https://github.com/vllm-project/vllm-ascend/pull/7967))
    - Reduce prefill KV all-gather communication for PCP/DCP (SFA) ([#8043](https://github.com/vllm-project/vllm-ascend/pull/8043))
    - Add penalty-related Triton kernel for better performance of penalties ([#7569](https://github.com/vllm-project/vllm-ascend/pull/7569))
- **Triton Kernel Optimizations (model_runner_v2)**:
    - Optimize _temperature_kernel and _topk_log_softmax_kernel ([#8083](https://github.com/vllm-project/vllm-ascend/pull/8083))
    - Optimize _min_p_kernel performance ([#8243](https://github.com/vllm-project/vllm-ascend/pull/8243), [#7767](https://github.com/vllm-project/vllm-ascend/pull/7767))
    - Add bad-words-kernel triton kernel ([#8030](https://github.com/vllm-project/vllm-ascend/pull/8030))
    - Optimize bincount_kernel performance ([#7757](https://github.com/vllm-project/vllm-ascend/pull/7757))
    - Optimize _ranks_kernel performance ([#7767](https://github.com/vllm-project/vllm-ascend/pull/7767))
    - Optimize triton recompilation triggered by function parameters ([#7480](https://github.com/vllm-project/vllm-ascend/pull/7480), [#7481](https://github.com/vllm-project/vllm-ascend/pull/7481), [#7483](https://github.com/vllm-project/vllm-ascend/pull/7483))
- **HCCL Process Group Reuse**: Reuse equivalent HCCL process groups on Ascend ([#7654](https://github.com/vllm-project/vllm-ascend/pull/7654))
- **CPU Binding Defer**: Defer CPU binding until worker warmup completes ([#7829](https://github.com/vllm-project/vllm-ascend/pull/7829))
- **Conv3d to Linear Conversion**: Convert conv3d to linear when kernel size equals stride ([#8318](https://github.com/vllm-project/vllm-ascend/pull/8318))

### Dependencies

- **vLLM**: Upgraded to vLLM v0.19.1 ([#8448](https://github.com/vllm-project/vllm-ascend/pull/8448))
- **Transformers**: Upgraded to transformers 5.5.3 (from 4.57.4), a major version upgrade with significant improvements and API changes ([#8448](https://github.com/vllm-project/vllm-ascend/pull/8448))
- **lm-eval**: Upgraded to lm-eval 0.4.11 for compatibility with transformers 5.5.3 ([#8448](https://github.com/vllm-project/vllm-ascend/pull/8448))
- **New Dependencies**: Added memcache and memfabric into requirements ([#8747](https://github.com/vllm-project/vllm-ascend/pull/8747))

### Documentation

- **PD Disaggregation Guides**:
    - PD Disaggregation with UCM and Mooncake ([#8338](https://github.com/vllm-project/vllm-ascend/pull/8338))
    - Dynamic chunked pipeline parallel guide ([#8728](https://github.com/vllm-project/vllm-ascend/pull/8728))
- **Model Documentation**:
    - GLM-5.1 model tutorial ([#8054](https://github.com/vllm-project/vllm-ascend/pull/8054))
    - GLM4.7 documentation update ([#8450](https://github.com/vllm-project/vllm-ascend/pull/8450))
    - GLM5 documentation with parameters and FAQs ([#7958](https://github.com/vllm-project/vllm-ascend/pull/7958), [#7850](https://github.com/vllm-project/vllm-ascend/pull/7850))
    - Qwen3.5 user guide update ([#7866](https://github.com/vllm-project/vllm-ascend/pull/7866))
    - Kimi-K2.5 documentation update ([#7901](https://github.com/vllm-project/vllm-ascend/pull/7901))
    - Qwen3-Omni-30B-A3B-Thinking documentation ([#8628](https://github.com/vllm-project/vllm-ascend/pull/8628))
    - DeepSeekOCR2 documentation ([#8573](https://github.com/vllm-project/vllm-ascend/pull/8573))
    - Hunyuan-A13B-Instruct verification and documentation ([#7381](https://github.com/vllm-project/vllm-ascend/pull/7381))
    - LLaVA-OneVision-Qwen2-0.5B-OV tutorial ([#7912](https://github.com/vllm-project/vllm-ascend/pull/7912))
- **Documentation Improvements**:
    - Enable MathJax rendering for Markdown formulas ([#8793](https://github.com/vllm-project/vllm-ascend/pull/8793))
    - Update version policy ([#8656](https://github.com/vllm-project/vllm-ascend/pull/8656))
    - Add preemption description in FAQs ([#8131](https://github.com/vllm-project/vllm-ascend/pull/8131))
    - Update supported vLLM versions ([#7923](https://github.com/vllm-project/vllm-ascend/pull/7923))
    - Parameterize versioning policy compatibility matrix ([#8002](https://github.com/vllm-project/vllm-ascend/pull/8002))
    - Avoid A2 CPU binding overlap from hidden NPUs and doc updates ([#8792](https://github.com/vllm-project/vllm-ascend/pull/8792))

### Others

**Important Bug Fixes:**

- **GQA C8 Fullgraph**: Fixed a bug in GQA C8 fullgraph mode ([#8779](https://github.com/vllm-project/vllm-ascend/pull/8779))
- **DSV3.1 W4A8 TTFT**: Revert change of `balance_flag` to fix DSV3.1 W4A8 TTFT degradation ([#8675](https://github.com/vllm-project/vllm-ascend/pull/8675))
- **DSV3.1 Service Startup**: Fix DeepSeek-V3.1 service failed to start ([#8208](https://github.com/vllm-project/vllm-ascend/pull/8208))
- **Qwen3.5 MoE High Concurrency**: Fix Qwen3.5 MoE FC1 error under high concurrency when dp>1 ([#8396](https://github.com/vllm-project/vllm-ascend/pull/8396))
- **Qwen3.5 MoE Flash Comm**: Fix Qwen3.5 MoE flash comm v1 shared expert shape error of mtp layer on A2 ([#7683](https://github.com/vllm-project/vllm-ascend/pull/7683))
- **Graph Capture OOM**: Fix the graph capturing OOM in model_runner_v2 ([#8111](https://github.com/vllm-project/vllm-ascend/pull/8111))
- **DeepSeek 3.2 C8 Precision**: Fix DeepSeek 3.2 C8 precision by reverting quantization layers ([#7628](https://github.com/vllm-project/vllm-ascend/pull/7628))
- **DeepSeek 3.2 DCP MTP**: Fix ds3.2 dcp mtp issues ([#7617](https://github.com/vllm-project/vllm-ascend/pull/7617))
- **MTP1 Concurrent Crash**: Fix MTP1 crashing in multiple concurrent scenarios ([#7459](https://github.com/vllm-project/vllm-ascend/pull/7459))
- **Spec Decode + Async**: Fix spec decode and async bugs ([#8461](https://github.com/vllm-project/vllm-ascend/pull/8461))
- **Spec Decode + Logprobs**: Fix spec decode + logprobs crash when async scheduling is disabled ([#7861](https://github.com/vllm-project/vllm-ascend/pull/7861))
- **Repetition Penalty**: Fix repetition_penalty not effective in asynchronous scheduling ([#7789](https://github.com/vllm-project/vllm-ascend/pull/7789))
- **P/D KV Cache**: Fix KV cache at MTP layer when TP is not equal in P/D scenarios ([#8540](https://github.com/vllm-project/vllm-ascend/pull/8540))
- **P/D Short Sequence**: Fix short sequence has no response in P/D mode ([#8104](https://github.com/vllm-project/vllm-ascend/pull/8104))
- **P/D Retry Mechanism**: Add retry mechanism to prevent packet loss in P/D ([#8166](https://github.com/vllm-project/vllm-ascend/pull/8166))
- **Layerwise Connector OOM**: Fix layerwise connector OOM during large buffer transfer ([#7834](https://github.com/vllm-project/vllm-ascend/pull/7834))
- **KV Pool Put Logic**: Fix KV Pool not putting KV cache and fix KV transfer Put Logic ([#7875](https://github.com/vllm-project/vllm-ascend/pull/7875), [#7717](https://github.com/vllm-project/vllm-ascend/pull/7717))
- **KV Pool PCP/DCP**: Fix PCP and DCP bugs for KV Pool ([#8099](https://github.com/vllm-project/vllm-ascend/pull/8099))
- **Mooncake Backend**: MooncakeBackend handles protocol besides Ascend ([#8514](https://github.com/vllm-project/vllm-ascend/pull/8514))
- **FlashComm Server Init**: Fix server init error when max_num_seqs not multiple of tp with FLASHCOMM ([#7801](https://github.com/vllm-project/vllm-ascend/pull/7801))
- **Triton Reinstall**: Reinstall triton-ascend after vllm-ascend install ([#7790](https://github.com/vllm-project/vllm-ascend/pull/7790))
- **DBO Compatibility**: Add compatibility guard for --enable-dbo on Ascend NPU ([#8507](https://github.com/vllm-project/vllm-ascend/pull/8507))
- **GPU Params on NPU**: Guard GPU-specific parallel config params on Ascend NPU ([#8703](https://github.com/vllm-project/vllm-ascend/pull/8703))
- **A2 CPU Binding**: Avoid A2 CPU binding overlap from hidden NPUs ([#8792](https://github.com/vllm-project/vllm-ascend/pull/8792))
- **FIA Pad Bug**: Fix FIA pad bug under max concurrency for EAGLE ([#7740](https://github.com/vllm-project/vllm-ascend/pull/7740))
- **MoE Load Precision**: Fix moe_load precision in allgather ([#7887](https://github.com/vllm-project/vllm-ascend/pull/7887))
- **FlashComm1 + DCP for Qwen**: Support FlashComm1 & DCP for Qwen models ([#7673](https://github.com/vllm-project/vllm-ascend/pull/7673))
- **Block Verify**: Disable block verify to avoid incorrect verification on NPU ([#7603](https://github.com/vllm-project/vllm-ascend/pull/7603))
- **Model Runner V2 Full Graph**: Fix model_runner_v2 in full graph mode ([#7945](https://github.com/vllm-project/vllm-ascend/pull/7945))
- **MRv2 Spec Decode**: Fix mrv2 runtime error with speculative decoding ([#8209](https://github.com/vllm-project/vllm-ascend/pull/8209))
- **GLM Tool Call Streaming**: Fix GLM tool call streaming issues ([#8832](https://github.com/vllm-project/vllm-ascend/pull/8832))
- **Forced Tool Choice**: Fix forced tool choice none-content handling ([#8833](https://github.com/vllm-project/vllm-ascend/pull/8833))
- **MiniMax Reasoning Usage**: Fix MiniMax reasoning usage accounting ([#8831](https://github.com/vllm-project/vllm-ascend/pull/8831))

**Other Bug Fixes:**

- MTP recurrent batch size after lmhead TP logits truncation ([#8718](https://github.com/vllm-project/vllm-ascend/pull/8718))
- EPLB topk_ids uses logical experts count ([#8501](https://github.com/vllm-project/vllm-ascend/pull/8501))
- EPLB validation logic optimization and MTP support redundant experts ([#8710](https://github.com/vllm-project/vllm-ascend/pull/8710))
- SP Preserve graph stringification in MoE sequence parallel ([#8780](https://github.com/vllm-project/vllm-ascend/pull/8780))
- SpecDecode Fix draft quarot model loading timeout ([#8736](https://github.com/vllm-project/vllm-ascend/pull/8736))
- Fix _dummy_run warmup mismatch with --language-model-only ([#8556](https://github.com/vllm-project/vllm-ascend/pull/8556))
- Fix AttributeError in AscendYaRNRotaryEmbedding ([#8734](https://github.com/vllm-project/vllm-ascend/pull/8734))
- Eagle3 Add fullgraph case and check mock function ([#8668](https://github.com/vllm-project/vllm-ascend/pull/8668))
- Fix atten_mask in npu_fused_infer_attention_score_v2 ([#8387](https://github.com/vllm-project/vllm-ascend/pull/8387))
- Fix conflicts between eagle and dflash about pcp ([#8598](https://github.com/vllm-project/vllm-ascend/pull/8598))
- Fix incorrect slot mapping for DeepSeek 3.2 PCP+MTP ([#8547](https://github.com/vllm-project/vllm-ascend/pull/8547))
- dispatch_ffn_combine kernel rollback ([#8539](https://github.com/vllm-project/vllm-ascend/pull/8539))
- Require kv producer for layer sharding ([#8562](https://github.com/vllm-project/vllm-ascend/pull/8562))
- 310P Use CPU generator cache for sampling ([#8495](https://github.com/vllm-project/vllm-ascend/pull/8495))
- Fix compute_slot_mapping triton for pcp+eagle3 ([#8435](https://github.com/vllm-project/vllm-ascend/pull/8435))
- Handle enum-based MoE activation in fuse_moe ([#8465](https://github.com/vllm-project/vllm-ascend/pull/8465))
- Gate recompute/balance/fused_mc2 by PD mode ([#8373](https://github.com/vllm-project/vllm-ascend/pull/8373))
- w8a8 dispatch ffn combine bias param adapt ([#8342](https://github.com/vllm-project/vllm-ascend/pull/8342))
- Fix quant_bias missing in w8a8_static for GLM-5 with flashcomm1 ([#8220](https://github.com/vllm-project/vllm-ascend/pull/8220))
- Fix DSA-CP PD role gating for deepseek v3.2 ([#8290](https://github.com/vllm-project/vllm-ascend/pull/8290))
- Require piecewise cudagraph for layerwise AscendStorConnector ([#8283](https://github.com/vllm-project/vllm-ascend/pull/8283))
- Fix remote KV waiting promotion in patch balance scheduler ([#8279](https://github.com/vllm-project/vllm-ascend/pull/8279))
- Enforce C locale for CPU binding subprocess parsing ([#8251](https://github.com/vllm-project/vllm-ascend/pull/8251))
- Add wait_for_kv_layer_from_connector in mlapo branch SFA ([#8195](https://github.com/vllm-project/vllm-ascend/pull/8195))
- Fix dimension mismatch when SP padding ([#7858](https://github.com/vllm-project/vllm-ascend/pull/7858))
- 310P Fixed Triton kernel block_table crash ([#8144](https://github.com/vllm-project/vllm-ascend/pull/8144))
- Fix attention state of short prompt ([#8029](https://github.com/vllm-project/vllm-ascend/pull/8029))
- 310P Fix post-sampling not working in graph mode ([#8017](https://github.com/vllm-project/vllm-ascend/pull/8017))
- 310P Align GDN state semantics with vLLM ([#7902](https://github.com/vllm-project/vllm-ascend/pull/7902))
- 310P Handle null quant config in ShardedStateLoader310 ([#7546](https://github.com/vllm-project/vllm-ascend/pull/7546))
- unpad block table when enable_sp and eagle3 in eager mode ([#7986](https://github.com/vllm-project/vllm-ascend/pull/7986))
- Fix qwen3-next compilation error ([#7936](https://github.com/vllm-project/vllm-ascend/pull/7936))
- Fix the weightsmapper bug of qwen3-vl ([#7869](https://github.com/vllm-project/vllm-ascend/pull/7869))
- Fix quant config attribute error ([#7736](https://github.com/vllm-project/vllm-ascend/pull/7736))
- Remove unnecessary weight_scale wrap behavior for eplb ([#7733](https://github.com/vllm-project/vllm-ascend/pull/7733))
- Adapt to main2main for model runnerv2 and add gc in sleep mode ([#7709](https://github.com/vllm-project/vllm-ascend/pull/7709))
- Fix prefix caching support for embedding models ([#7452](https://github.com/vllm-project/vllm-ascend/pull/7452))
- Reuse weight address in graph + RL scenario ([#7473](https://github.com/vllm-project/vllm-ascend/pull/7473))

### Known Issues

- When running GLM-5 / GLM-5.1 models in single-node (non-PD-disaggregated) scenarios, incorrect results or runtime errors may occur. See [#8843](https://github.com/vllm-project/vllm-ascend/issues/8843) for details and workarounds.
- triton-ascend may fail to compile with a g++ internal compiler error (Segmentation fault). Workaround: update to `triton-ascend==3.2.0.dev20260322` and clear the Triton cache (`rm -rf ~/.triton/cache/*`). [#7782](https://github.com/vllm-project/vllm-ascend/issues/7782)
- **TorchNPU**: Please upgrade to 2.9.0.post1+git4c901a4 because of some known issue. This version can't install by default, please upgrade manually. We can get installation pkg from this link: <https://vllm-ascend.obs.cn-north-4.myhuaweicloud.com/vllm-ascend/torch_npu-2.9.0.post1%2Bgit4c901a4-${PYTHON_TAG}-${PYTHON_TAG}-manylinux_2_28_${ARCH}.whl>. **PS:** If CANN has been upgraded to version 9.0.0, please upgrade TorchNPU version to 2.9.0.post2 synchronously.

## v0.18.0rc1 - 2026.04.01

This is the first release candidate of v0.18.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- C8(INT8 KV cache) is now supported for GQA attention models, and also supported on DeepSeek-V3.1 with PD disaggregation scenario. [#7474](https://github.com/vllm-project/vllm-ascend/pull/7474), [#7222](https://github.com/vllm-project/vllm-ascend/pull/7222)
- DeepSeek models are now supported on Ascend 950 Products through new MLA operators. [#7232](https://github.com/vllm-project/vllm-ascend/pull/7232)

### Features

- Flash Comm V1 now supports VL models with MLA, removing a previous limitation for multimodal serving. [#7390](https://github.com/vllm-project/vllm-ascend/pull/7390)
- Support separate attention backends for target and draft models in speculative decoding, allowing finer backend tuning per model. [#7342](https://github.com/vllm-project/vllm-ascend/pull/7342)
- VL MoE models now support SP, and `sp_threshold` is removed in favor of `sp_min_token_num` from vLLM. [#7044](https://github.com/vllm-project/vllm-ascend/pull/7044)
- Qwen VL models now support `w8a8_mxfp8` quantization. [#7417](https://github.com/vllm-project/vllm-ascend/pull/7417)

### Performance

- Optimized Triton operator recompilation to reduce redundant rebuilds and unnecessary recompilation triggered by function parameter optimization. [#7647](https://github.com/vllm-project/vllm-ascend/pull/7647) [#7645](https://github.com/vllm-project/vllm-ascend/pull/7645)
- Optimized the Qwen3.5 and Qwen3-Next GDN prefill path by prebuilding chunk metadata, reducing host-device synchronization overhead. [#7487](https://github.com/vllm-project/vllm-ascend/pull/7487)
- Simplified the FIA prefill context merge path for better runtime efficiency. [#7293](https://github.com/vllm-project/vllm-ascend/pull/7293)

### Documentation

- Refreshed deployment and model docs for Kimi-K2.5, GLM-4.7, DeepSeek-V3.2, MiniMax-M2.5, and PD disaggregation guides. [#7371](https://github.com/vllm-project/vllm-ascend/pull/7371) [#7403](https://github.com/vllm-project/vllm-ascend/pull/7403) [#7292](https://github.com/vllm-project/vllm-ascend/pull/7292) [#7296](https://github.com/vllm-project/vllm-ascend/pull/7296) [#7300](https://github.com/vllm-project/vllm-ascend/pull/7300)

### Others

- Fixed a PD Disaggregation issue where decode nodes could get stuck because shapes were not aligned across DP nodes. [#7534](https://github.com/vllm-project/vllm-ascend/pull/7534)
- Fixed a regression where hybrid attention plus mamba models on Ascend could start with an incorrect block size after the v0.18.0 upgrade. [#7528](https://github.com/vllm-project/vllm-ascend/pull/7528)
- Fixed multi-instance serving OOM calculation on single-card deployments. [#7427](https://github.com/vllm-project/vllm-ascend/pull/7427)
- Fixed DeepSeek v3.1 C8 when overlaying MTP with full decode and full graph modes. [#7571](https://github.com/vllm-project/vllm-ascend/pull/7571)
- Fixed quantization config key mapping in `AscendModelSlimConfig` by switching from reverse mapping to forward mapping. [#7716](https://github.com/vllm-project/vllm-ascend/pull/7716)

### Known Issue

- When running DeepSeek-R1 W8A8 with MTP and KV Pool enabled under high concurrency, a `ValueError: Counters can only be incremented by non-negative amounts` may occur. [#7489](https://github.com/vllm-project/vllm-ascend/issues/7489)
- triton-ascend may fail to compile with a g++ internal compiler error (Segmentation fault). Workaround: update to `triton-ascend==3.2.0.dev20260322` and clear the Triton cache (`rm -rf ~/.triton/cache/*`). [#7782](https://github.com/vllm-project/vllm-ascend/issues/7782)
- FIA does not support all MHA head dimensions when using tp-size >= 16 on Ascend. Affected models will fail with an error on unsupported head dimensions. This will be resolved in a future release when FIA supports more head dimensions. [#7729](https://github.com/vllm-project/vllm-ascend/pull/7729)
- While Minimax-2.5 now supports PD Disaggregation, internal testing has identified a 13% regression on the GPQA benchmark when this feature is enabled. We currently do not recommend enabling PD Disaggregation for this model and We are working on an optimization fix.

## v0.17.0rc1 - 2026.03.15

This is the first release candidate of v0.17.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- Ascend950 chip is now supported. [#7151](https://github.com/vllm-project/vllm-ascend/pull/7151)
- ACLGraph (graph mode) is now supported for Model Runner V2. [#7110](https://github.com/vllm-project/vllm-ascend/pull/7110)
- Unified parallelized speculative decoding is supported, enabling parallel draft inference schemes simultaneously. [#6766](https://github.com/vllm-project/vllm-ascend/pull/6766)

### Features

- Auto-detect quantization format from model files, and remote model IDs (e.g., `org/model-name`) are also supported. `--quantization ascend` is not required now. [#7111](https://github.com/vllm-project/vllm-ascend/pull/7111)
- Qwen3.5 is supported from this version on.
- FlashLB algorithm for EPLB: supports per-step heat collection and multi-stage load balancing for better expert parallelism efficiency. [#6477](https://github.com/vllm-project/vllm-ascend/pull/6477)
- LoRA with tensor parallel and `--fully-sharded-loras` is now fixed and working. [#6650](https://github.com/vllm-project/vllm-ascend/pull/6650)
- LMCacheAscendConnector is added as a new KV cache pooling solution for Ascend. [#6882](https://github.com/vllm-project/vllm-ascend/pull/6882)
- W8A8C8 quantization is now supported for DeepSeek-V3.2 in PD-mix scenario. [#7029](https://github.com/vllm-project/vllm-ascend/pull/7029)
- [Experimental] Minimax-m2.5 model is now supported on Ascend NPU. [#7105](https://github.com/vllm-project/vllm-ascend/pull/7105)
- [Experimental] Mooncake Layerwise Connector now supports hybrid attention manager with multiple KV cache groups. [#7022](https://github.com/vllm-project/vllm-ascend/pull/7022)
- [Experimental] Prefix cache is now supported in hybrid model. [#7103](https://github.com/vllm-project/vllm-ascend/pull/7103)

### Performance

- Pipeline Parallel now supports async scheduling, improving throughput for PP deployments. [#7136](https://github.com/vllm-project/vllm-ascend/pull/7136)
- Improved TTFT when using Mooncake connector by reducing log overhead. [#6125](https://github.com/vllm-project/vllm-ascend/pull/6125)
- KV Pool lookup is optimized for short sequences (token length < block_size). [#7146](https://github.com/vllm-project/vllm-ascend/pull/7146)
- Fix penalty ops in Model Runner V2, achieving ~10% performance improvement. [#7013](https://github.com/vllm-project/vllm-ascend/pull/7013)

### Documentation

- Added EPD (Encode-Prefill-Decode) documentation and load-balance proxy example. [#6221](https://github.com/vllm-project/vllm-ascend/pull/6221)
- Added Ascend PyTorch Profiler usage guide. [#7117](https://github.com/vllm-project/vllm-ascend/pull/7117)
- Fixed DSV3.1 PD configuration documentation. [#7187](https://github.com/vllm-project/vllm-ascend/pull/7187)

### Others

- Fix drafter crash in full graph mode for speculative decoding. [#7158](https://github.com/vllm-project/vllm-ascend/pull/7158) [#7148](https://github.com/vllm-project/vllm-ascend/pull/7148)
- Fix GLM5-W8A8 precision issues caused by rotary quant MTP weights. [#7139](https://github.com/vllm-project/vllm-ascend/pull/7139)
- Fix ngram graph replay accuracy error on 310P. [#7134](https://github.com/vllm-project/vllm-ascend/pull/7134)
- Fix FIA pad logic in graph mode after upstream vLLM change. [#7144](https://github.com/vllm-project/vllm-ascend/pull/7144)
- Fix a precision issue caused by wrong KV cache reshape on Qwen3.5. [#7209](https://github.com/vllm-project/vllm-ascend/pull/7209)
- Fix extra processes spawned on rank0 device. [#7107](https://github.com/vllm-project/vllm-ascend/pull/7107)
- Graph capture failures now properly raise exceptions for easier debugging. [#5644](https://github.com/vllm-project/vllm-ascend/pull/5644)
- Fix Qwen3.5 model by replacing torch_npu.npu_recurrent_gated_delta_rule by fused_recurrent_gated_delta_rule. [#7109](https://github.com/vllm-project/vllm-ascend/pull/7109)
- Fix the bug when running Qwen3-Reranker-0.6B with LoRA. [#7156](https://github.com/vllm-project/vllm-ascend/pull/7156)

### Known Issue

- GLM5 requires transformers==5.2.0, and this will be resolved by [vllm-project/vllm#30566](https://github.com/vllm-project/vllm/pull/30566), will not be included in v0.17.0.
- There is a precision issue with Qwen3-Next due to the changed tp weight split method. Will fix it in next release.
- In hybrid models, the minimum token count required for a prefix cache hit is currently large. The exact number is related to tp size, e.g., with tp 2, the block_size is adjusted to 2048, which means that any prefix shorter than 2048 will never be cached.
- GLM5 has an issue in the 2-node PD mixed deployment scenario where inference may hang when concurrency exceeds 8 (fixed in PR [#7235](https://github.com/vllm-project/vllm-ascend/pull/7235) [#7290](https://github.com/vllm-project/vllm-ascend/pull/7290)).

## v0.16.0rc1 - 2026.03.09

This is the first release candidate of v0.16.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- Qwen3-Omni quantization adaptation and optimization is now available. [#6828](https://github.com/vllm-project/vllm-ascend/pull/6828)
- GLM5-W8A8 quantization is now supported by parameterizing hardcoded MLA dimensions. [#6902](https://github.com/vllm-project/vllm-ascend/pull/6902)

### Features

- [Experimental] Support FabricMem Mode for ADXL/HIXL interconnect. [#6806](https://github.com/vllm-project/vllm-ascend/pull/6806)
- Qwen3-Next now supports FlashComm1. [#6830](https://github.com/vllm-project/vllm-ascend/pull/6830)
- NPUWorker Profiler now supports profile_prefix for better profiling experience. [#6968](https://github.com/vllm-project/vllm-ascend/pull/6968)
- EPLB profiling now displays expert hotness comparison and time required for eplb adjustment. [#6877](https://github.com/vllm-project/vllm-ascend/pull/6877) [#7001](https://github.com/vllm-project/vllm-ascend/pull/7001)
- Xlite Qwen3 MoE now supports Data Parallel. [#6715](https://github.com/vllm-project/vllm-ascend/pull/6715)
- Mooncake Layerwise Connector now supports kv_pool. [#7032](https://github.com/vllm-project/vllm-ascend/pull/7032)
- Eagle3 now supports QuaRot quantization without embedding. [#7038](https://github.com/vllm-project/vllm-ascend/pull/7038)

### Hardware and Operator Support

- 310P now supports w8a8sc quantization method. [#7075](https://github.com/vllm-project/vllm-ascend/pull/7075)
- Added AscendC casual_conv1d_fn operator for Qwen3-Next. [#6661](https://github.com/vllm-project/vllm-ascend/pull/6661)
- Added Ascend Ops recurrent_gated_delta_rule operator. [#6725](https://github.com/vllm-project/vllm-ascend/pull/6725)
- Added GMM custom operator for MoE models. [#7010](https://github.com/vllm-project/vllm-ascend/pull/7010)

### Performance

- Faster convolution computation improves TTFT by 0.95% and throughput by 0.59% for Qwen3-VL models. [#7017](https://github.com/vllm-project/vllm-ascend/pull/7017)
- Optimize split_qkv_rmsnorm_rope operator. [#6827](https://github.com/vllm-project/vllm-ascend/pull/6827)
- Implement global CPU slicing and improve IRQ binding for Ascend NPUs, ensuring non-overlapping CPU partitions and better resource management. [#6945](https://github.com/vllm-project/vllm-ascend/pull/6945)
- Optimize MTP execution by reordering state update operation. [#6844](https://github.com/vllm-project/vllm-ascend/pull/6844)
- Avoid CPU sync in mrope_positions copy by using full tensor copy. [#7014](https://github.com/vllm-project/vllm-ascend/pull/7014)
- Remove H2D synchronization for expert_map in MoE models. [#7000](https://github.com/vllm-project/vllm-ascend/pull/7000)

### Dependencies

- CANN is upgraded to 8.5.1, please remember to upgrade by hand if you're not using the official image. [#6897](https://github.com/vllm-project/vllm-ascend/pull/6897)

### Deprecation & Breaking Changes

- `enable_flash_comm_v1` config option has been renamed back to `enable_sp`. [#6883](https://github.com/vllm-project/vllm-ascend/pull/6883)
- The auto-detect quantization format from model files is reverted, in v0.16.0rc1, we still need to add `--quantization ascend` to serve a model quantized by modelslim. It will be added back in the next version after the bug with the remote model id is fixed. [#6873](https://github.com/vllm-project/vllm-ascend/pull/6873)

### Documentation

- Added user/developer guide for CPU binding. [#7045](https://github.com/vllm-project/vllm-ascend/pull/7045)
- Added metrics usage documentation and example. [#6962](https://github.com/vllm-project/vllm-ascend/pull/6962)
- Added llms.txt for LLM discovery. [#6886](https://github.com/vllm-project/vllm-ascend/pull/6886)
- Added GLM4.x multi-node deploy tutorial. [#6872](https://github.com/vllm-project/vllm-ascend/pull/6872)
- Added explanation of 310p special param: max-model-len. [#7065](https://github.com/vllm-project/vllm-ascend/pull/7065)

### Others

- Fix openEuler Dockerfile error. [#6871](https://github.com/vllm-project/vllm-ascend/pull/6871)
- Many bug fixes including:
    - Fix Eagle speculative decoding with Context Parallel enabled. [#6981](https://github.com/vllm-project/vllm-ascend/pull/6981) [#7079](https://github.com/vllm-project/vllm-ascend/pull/7079)
    - Fix LoRA accuracy issue introduced by upstream vLLM changes. [#6958](https://github.com/vllm-project/vllm-ascend/pull/6958)
    - Fix streaming content-type in load balance proxy server. [#6985](https://github.com/vllm-project/vllm-ascend/pull/6985)
    - Fix metadata execute error: integer modulo by zero. [#6521](https://github.com/vllm-project/vllm-ascend/pull/6521)
    - Fix triton rope_siso implementation bug. [#7082](https://github.com/vllm-project/vllm-ascend/pull/7082)
    - Fix incorrect layer count for MTP models in update_aclgraph_sizes. [#7064](https://github.com/vllm-project/vllm-ascend/pull/7064)
    - Fix compilation errors for CANN versions subsequent to b020. [#7059](https://github.com/vllm-project/vllm-ascend/pull/7059)
    - Fix quant config support in GLM4.6V. [#7062](https://github.com/vllm-project/vllm-ascend/pull/7062)
    - Fix parameter ordering bug in _merge_multimodal_embeddings. [#7068](https://github.com/vllm-project/vllm-ascend/pull/7068)
    - Fix fused mc2 bug in EPLB. [#6794](https://github.com/vllm-project/vllm-ascend/pull/6794)
    - Fix kernel block size for computing slot mapping. [#7019](https://github.com/vllm-project/vllm-ascend/pull/7019)
    - Fix layerwise stacking MTP error in P/D disaggregation. [#7036](https://github.com/vllm-project/vllm-ascend/pull/7036)
    - Fix RoPE dimension for npu_rotary_embedding. [#6880](https://github.com/vllm-project/vllm-ascend/pull/6880)
    - Fix Qwen-Omni quantization bugs. [#7042](https://github.com/vllm-project/vllm-ascend/pull/7042) [#7007](https://github.com/vllm-project/vllm-ascend/pull/7007)
    - Fix GDN layer accuracy in graph mode. [#6822](https://github.com/vllm-project/vllm-ascend/pull/6822)
    - Fix precision bugs for PCP/DCP in PD disaggregate. [#6876](https://github.com/vllm-project/vllm-ascend/pull/6876)
    - Fix MTP in PD disaggregation with full graph support for all D-Nodes. [#6948](https://github.com/vllm-project/vllm-ascend/pull/6948)
    - Fix GQA model error when enabling both DP and DCP. [#7012](https://github.com/vllm-project/vllm-ascend/pull/7012)
    - Fix MTP prefill misclassified as decode edge case. [#6835](https://github.com/vllm-project/vllm-ascend/pull/6835)
    - Fix Eagle3 acceptance rate for QuaRot quantized models. [#6914](https://github.com/vllm-project/vllm-ascend/pull/6914)
    - Fix RoPE shape mismatch for MTP models with FlashComm V1 enabled. [#6939](https://github.com/vllm-project/vllm-ascend/pull/6939)
    - Fix Qwen2.5VL accuracy issue. [#6975](https://github.com/vllm-project/vllm-ascend/pull/6975)
    - Fix MoE forward error with static kernel enabled. [#6964](https://github.com/vllm-project/vllm-ascend/pull/6964)
    - Fix muls_add fusion for GLM5 models. [#6928](https://github.com/vllm-project/vllm-ascend/pull/6928)
    - Fix GDN layer detection for multimodal models. [#6941](https://github.com/vllm-project/vllm-ascend/pull/6941)
    - Fix 300I unquant model weight nd2nz error. [#6851](https://github.com/vllm-project/vllm-ascend/pull/6851)
    - Fix CPU binding logic. [#6889](https://github.com/vllm-project/vllm-ascend/pull/6889)
    - Fix Eagle full graph shape capture. [#6846](https://github.com/vllm-project/vllm-ascend/pull/6846)

### Known Issue

- Currently, for DeepSeek v3.2, PCP & DCP do not yet work with FlashComm1 feature, which may cause serve errors or other unknown errors.
- In 4-node A3 PD disaggregation deployment with DeepSeek V3.2, the P-Node may hang when benchmarking in high concurrency scenario, e.g., 2k/2k tokens with 512 concurrent requests.
- MTP with large EP configurations may cause graph capture buffer overflow. This is a bug need to fix in vLLM, now there is a workaround to avoid it: explicitly set `--compilation-config '{"max_cudagraph_capture_size": N}'` where `N = max_concurrency * (1 + num_speculative_tokens)`.

## v0.15.0rc1 - 2026.02.27

This is the first release candidate of v0.15.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- **NPU Graph EX (npugraph_ex) Enabled by Default**: The npugraph_ex feature is now enabled by default, providing better graph optimization with integrated inductor pass and MatmulAllReduceAddRMSNorm fusion. [#6354](https://github.com/vllm-project/vllm-ascend/pull/6354) [#6664](https://github.com/vllm-project/vllm-ascend/pull/6664) [#6006](https://github.com/vllm-project/vllm-ascend/pull/6006)
- **310P MoE and W8A8 Support**[Experimental]: 310P now supports MoE models, W8A8 quantization, and weightNZ feature, significantly expanding hardware capabilities. [#6530](https://github.com/vllm-project/vllm-ascend/pull/6530) [#6641](https://github.com/vllm-project/vllm-ascend/pull/6641) [#6454](https://github.com/vllm-project/vllm-ascend/pull/6454) [#6705](https://github.com/vllm-project/vllm-ascend/pull/6705)
- **Qwen3-VL-MoE EAGLE Support**: Added EAGLE speculative decoding support for Qwen3-VL-MoE model. [#6327](https://github.com/vllm-project/vllm-ascend/pull/6327)
- **Kimi-K2.5 Model Support**: Added support for Kimi-K2.5 models. **Please note** that vLLM 0.15.0 has a known issue with Kimi-K2.5. To fix this, please apply the changes from the upstream `vllm-project/vllm` repository, specifically from pull requests [#33320](https://github.com/vllm-project/vllm/pull/33320) and [#34501](https://github.com/vllm-project/vllm/pull/34501). [#6755](https://github.com/vllm-project/vllm-ascend/pull/6755)

### Features

- **Auto-detect Quantization Format**: Quantization format can now be auto-detected from model files. [#6645](https://github.com/vllm-project/vllm-ascend/pull/6645)
- **GPT-OSS Attention Support**: Added GPT-OSS attention implementation. [#5901](https://github.com/vllm-project/vllm-ascend/pull/5901)
- **DCP Support for SFA**: Added Decode Context Parallel (DCP) support for SFA architecture. [#6563](https://github.com/vllm-project/vllm-ascend/pull/6563)
- **Mooncake Layerwise PCP Support**: Mooncake layerwise connector now supports PCP function. [#6627](https://github.com/vllm-project/vllm-ascend/pull/6627)
- **Mooncake Connector Remote PTP Size**: Mooncake connector can now get remote PTP size. [#5822](https://github.com/vllm-project/vllm-ascend/pull/5822)
- **KV Pool Sparse Attention**: KV pool now supports sparse attention. [#6339](https://github.com/vllm-project/vllm-ascend/pull/6339)
- **Batch Invariant with AscendC**: Implemented batch invariant feature with AscendC. [#6590](https://github.com/vllm-project/vllm-ascend/pull/6590)
- **Routing Replay**: Added routing replay feature. [#6696](https://github.com/vllm-project/vllm-ascend/pull/6696)
- **Compressed Tensors MoE W4A8 Dynamic Weight**: Added support for compressed tensors moe w4a8 dynamic weight quantization. [#5889](https://github.com/vllm-project/vllm-ascend/pull/5889)
- **GLM4.7-Flash W8A8 Quantization**: Added W8A8 quantization support for GLM4.7-Flash. [#6492](https://github.com/vllm-project/vllm-ascend/pull/6492)
- **DispatchGmmCombineDecode Enhancement**: DispatchGmmCombineDecode now supports bf16/float16 gmm1/gmm2 weight and ND format weight. [#6393](https://github.com/vllm-project/vllm-ascend/pull/6393)
- **RMSNorm Dynamic Quant Fusion**: Added rmsnorm dynamic quant fusion pass. [#6274](https://github.com/vllm-project/vllm-ascend/pull/6274)
- **Worker Health Check Interface**: Added `check_health` interface for worker. [#6681](https://github.com/vllm-project/vllm-ascend/pull/6681)

### Hardware and Operator Support

- **310P Support Expansion**: Multiple improvements for 310P hardware:
    - Fixed attention accuracy issue on 310P. [#6803](https://github.com/vllm-project/vllm-ascend/pull/6803)
    - Added weightNZ feature for 310P with quant or unquant support. [#6705](https://github.com/vllm-project/vllm-ascend/pull/6705)
    - Added addrmsnorm support for 300I DUO. [#6704](https://github.com/vllm-project/vllm-ascend/pull/6704)
    - 310P now supports PrefillCacheHit state. [#6756](https://github.com/vllm-project/vllm-ascend/pull/6756)
- **ARM-only CPU Binding**: Enabled ARM-only CPU binding with NUMA-balanced A3 policy. [#6686](https://github.com/vllm-project/vllm-ascend/pull/6686)
- **Triton Rope Enhancement**: Triton rope now supports index_selecting from cos_sin_cache. [#5450](https://github.com/vllm-project/vllm-ascend/pull/5450)
- **AscendC Fused Op**: Added AscendC fused op transpose_kv_cache_by_block to speed up GQA transfer. [#6366](https://github.com/vllm-project/vllm-ascend/pull/6366)
- **Rotary_dim Parameter**: Added support for rotary_dim parameter when using partial rope in rotary_embedding. [#6581](https://github.com/vllm-project/vllm-ascend/pull/6581)

### Performance

- **Multimodal seq_lens CPU Cache**: Use `seq_lens` CPU cache to avoid frequent D2H copy for better multimodal performance. [#6448](https://github.com/vllm-project/vllm-ascend/pull/6448)
- **DispatchFFNCombine Optimization**: Optimized DispatchFFNCombine kernel performance and resolved vector error caused by unaligned UB access. [#6468](https://github.com/vllm-project/vllm-ascend/pull/6468) [#6707](https://github.com/vllm-project/vllm-ascend/pull/6707)
- **DeepSeek V3.2 KVCache Optimization**: Optimized KV cache usage for DeepSeek V3.2. [#6610](https://github.com/vllm-project/vllm-ascend/pull/6610)
- **MLA/SFA Weight Prefetch**: Refactored MLA/SFA weight prefetch to be consistent with MoE weight prefetch. [#6629](https://github.com/vllm-project/vllm-ascend/pull/6629)
- **MLP Weight Prefetch**: Refactored MLP weight prefetch to be consistent with MoE model's prefetching. [#6442](https://github.com/vllm-project/vllm-ascend/pull/6442)
- **Adaptive Block Size Selection**: Added adaptive block size selection in linear_persistent kernel. [#6537](https://github.com/vllm-project/vllm-ascend/pull/6537)
- **EPLB Memory Optimization**: Reduced memory used for heat aggregation in EPLB. [#6729](https://github.com/vllm-project/vllm-ascend/pull/6729)
- **Memory Migration and Interrupt Core Binding**: Improved binding logic with memory migration and interrupt core binding functions. [#6785](https://github.com/vllm-project/vllm-ascend/pull/6785)
- **Triton Stability**: Improved Triton stability on Ascend for large grids. [#6301](https://github.com/vllm-project/vllm-ascend/pull/6301)

### Dependencies

- **Mooncake**: Upgraded to v0.3.8.post1. [#6428](https://github.com/vllm-project/vllm-ascend/pull/6428)

### Deprecation & Breaking Changes

- **ProfileExecuteDuration**: Cleaned up and deprecated ProfileExecuteDuration feature. [#6461](https://github.com/vllm-project/vllm-ascend/pull/6461)
- **Custom rotary_embedding Operator**: Removed custom rotary_embedding operator. [#6523](https://github.com/vllm-project/vllm-ascend/pull/6523)
- **USE_OPTIMIZED_MODEL**: Cleaned up unused env `USE_OPTIMIZED_MODEL`. [#6618](https://github.com/vllm-project/vllm-ascend/pull/6618)

### Documentation

- Added AI-assisted model-adaptation workflow documentation for vllm-ascend. [#6731](https://github.com/vllm-project/vllm-ascend/pull/6731)
- Added vLLM Ascend development guidelines (AGETNS.md). [#6797](https://github.com/vllm-project/vllm-ascend/pull/6797)
- Added GLM5 tutorial documentation. [#6709](https://github.com/vllm-project/vllm-ascend/pull/6709) [#6717](https://github.com/vllm-project/vllm-ascend/pull/6717)
- Added Memcache Usage Guide. [#6476](https://github.com/vllm-project/vllm-ascend/pull/6476)
- Added request forwarding documentation. [#6780](https://github.com/vllm-project/vllm-ascend/pull/6780)
- Added Benchmark Tutorial for Suffix Speculative Decoding. [#6323](https://github.com/vllm-project/vllm-ascend/pull/6323)
- Restructured tutorial documentation. [#6501](https://github.com/vllm-project/vllm-ascend/pull/6501)
- Added npugraph_ex introduction documentation. [#6306](https://github.com/vllm-project/vllm-ascend/pull/6306)

### Others

- **MTP in PD Full graph**: Fixed support for ALL D-Nodes in full graph when running MTP in PD deployment. [#5472](https://github.com/vllm-project/vllm-ascend/pull/5472)
- **DeepSeekV3.1 Accuracy**: Fixed DeepSeekV3.1 accuracy issue. [#6805](https://github.com/vllm-project/vllm-ascend/pull/6805)
- **EAGLE Refactor**: Routed MTP to EAGLE except for PCP/DCP+MTP cases. [#6349](https://github.com/vllm-project/vllm-ascend/pull/6349)
- **Speculative Decoding Accuracy**: Fixed spec acceptance rate problem in vLLM 0.15.0. [#6606](https://github.com/vllm-project/vllm-ascend/pull/6606)
- **PCP/DCP Accuracy**: Fixed accuracy issue in PCP/DCP with speculative decoding. [#6491](https://github.com/vllm-project/vllm-ascend/pull/6491)
- **Dynamic EPLB**: Fixed ineffective dynamic EPLB bug and EPLB no longer depends on a specified model. [#6653](https://github.com/vllm-project/vllm-ascend/pull/6653) [#6528](https://github.com/vllm-project/vllm-ascend/pull/6528)
- **KV Pool Mooncake Backend**: Correctly initialized head_or_tp_rank for mooncake backend. [#6498](https://github.com/vllm-project/vllm-ascend/pull/6498)
- **Layerwise Connector Recompute Scheduler**: Layerwise connector now supports recompute scheduler. [#5900](https://github.com/vllm-project/vllm-ascend/pull/5900)
- **Memcache Pool**: Fixed service startup failure when memcache pool is enabled. [#6229](https://github.com/vllm-project/vllm-ascend/pull/6229)
- **AddRMSNormQuant**: Fixed AddRMSNormQuant not taking effect. [#6620](https://github.com/vllm-project/vllm-ascend/pull/6620)
- **Pooling Code**: Fixed pooling code issues and updated usage guide. [#6126](https://github.com/vllm-project/vllm-ascend/pull/6126)
- **Context Parallel**: Fixed and unified the PD request discrimination logic. [#5939](https://github.com/vllm-project/vllm-ascend/pull/5939)
- **npugraph_ex**: Fixed duplicate pattern issue and added extra check for allreduce rmsnorm fusion pass. [#6513](https://github.com/vllm-project/vllm-ascend/pull/6513) [#6430](https://github.com/vllm-project/vllm-ascend/pull/6430)
- **RecomputeScheduler**: Fixed incompatibility of RecomputeScheduler with vLLM v0.14.1. [#6286](https://github.com/vllm-project/vllm-ascend/pull/6286)

## v0.13.0 - 2026.02.06

This is the final release of v0.13.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.13.0/) to get started.

### Highlights

**Model Support**

- **DeepSeek-R1 & DeepSeek-V3.2**: [Experimental]Performance optimizations, and async scheduling enhancements. [#3631](https://github.com/vllm-project/vllm-ascend/pull/3631) [#3900](https://github.com/vllm-project/vllm-ascend/pull/3900) [#3908](https://github.com/vllm-project/vllm-ascend/pull/3908) [#4191](https://github.com/vllm-project/vllm-ascend/pull/4191) [#4805](https://github.com/vllm-project/vllm-ascend/pull/4805)
- **Qwen3-Next**: [Experimental]Full support for Qwen3-Next series including 80B-A3B-Instruct with full graph mode, MTP, quantization (W8A8), NZ optimization, and chunked prefill. Fixed multiple accuracy and stability issues. [#3450](https://github.com/vllm-project/vllm-ascend/pull/3450) [#3572](https://github.com/vllm-project/vllm-ascend/pull/3572) [#3428](https://github.com/vllm-project/vllm-ascend/pull/3428) [#3918](https://github.com/vllm-project/vllm-ascend/pull/3918) [#4058](https://github.com/vllm-project/vllm-ascend/pull/4058) [#4245](https://github.com/vllm-project/vllm-ascend/pull/4245) [#4070](https://github.com/vllm-project/vllm-ascend/pull/4070) [#4477](https://github.com/vllm-project/vllm-ascend/pull/4477) [#4770](https://github.com/vllm-project/vllm-ascend/pull/4770)
- **InternVL**: Added support for InternVL models with comprehensive e2e tests and accuracy evaluation. [#3796](https://github.com/vllm-project/vllm-ascend/pull/3796) [#3964](https://github.com/vllm-project/vllm-ascend/pull/3964)
- **LongCat-Flash**: [Experimental]Added support for LongCat-Flash model. [#3833](https://github.com/vllm-project/vllm-ascend/pull/3833)
- **minimax_m2**: [Experimental]Added support for minimax_m2 model. [#5624](https://github.com/vllm-project/vllm-ascend/pull/5624)
- **Whisper & Cross-Attention**: [Experimental]Added support for cross-attention and Whisper models. [#5592](https://github.com/vllm-project/vllm-ascend/pull/5592)
- **Pooling Models**: [Experimental]Added support for pooling models with PCP adaptation and fixed multiple pooling-related bugs. [#3122](https://github.com/vllm-project/vllm-ascend/pull/3122) [#4143](https://github.com/vllm-project/vllm-ascend/pull/4143) [#6056](https://github.com/vllm-project/vllm-ascend/pull/6056) [#6057](https://github.com/vllm-project/vllm-ascend/pull/6057) [#6146](https://github.com/vllm-project/vllm-ascend/pull/6146)
- **PanguUltraMoE**: [Experimental]Added support for PanguUltraMoE model. [#4615](https://github.com/vllm-project/vllm-ascend/pull/4615)

**Core Features**

- **Context Parallel (PCP/DCP)**: [Experimental] Added comprehensive support for Prefill Context Parallel (PCP) and Decode Context Parallel (DCP) with ACLGraph, MTP, chunked prefill, MLAPO, and Mooncake connector integration. This is an experimental feature - feedback welcome. [#3260](https://github.com/vllm-project/vllm-ascend/pull/3260) [#3731](https://github.com/vllm-project/vllm-ascend/pull/3731) [#3801](https://github.com/vllm-project/vllm-ascend/pull/3801) [#3980](https://github.com/vllm-project/vllm-ascend/pull/3980) [#4066](https://github.com/vllm-project/vllm-ascend/pull/4066) [#4098](https://github.com/vllm-project/vllm-ascend/pull/4098) [#4183](https://github.com/vllm-project/vllm-ascend/pull/4183) [#5672](https://github.com/vllm-project/vllm-ascend/pull/5672)
- **Full Graph Mode (ACLGraph)**: [Experimental]Enhanced full graph mode with GQA support, memory optimizations, unified logic between ACLGraph and Torchair, and improved stability. [#3560](https://github.com/vllm-project/vllm-ascend/pull/3560) [#3970](https://github.com/vllm-project/vllm-ascend/pull/3970) [#3812](https://github.com/vllm-project/vllm-ascend/pull/3812) [#3879](https://github.com/vllm-project/vllm-ascend/pull/3879) [#3888](https://github.com/vllm-project/vllm-ascend/pull/3888) [#3894](https://github.com/vllm-project/vllm-ascend/pull/3894) [#5118](https://github.com/vllm-project/vllm-ascend/pull/5118)
- **Multi-Token Prediction (MTP)**: Significantly improved MTP support with chunked prefill for DeepSeek, quantization support, full graph mode, PCP/DCP integration, and async scheduling. MTP now works in most cases and is recommended for use. [#2711](https://github.com/vllm-project/vllm-ascend/pull/2711) [#2713](https://github.com/vllm-project/vllm-ascend/pull/2713) [#3620](https://github.com/vllm-project/vllm-ascend/pull/3620) [#3845](https://github.com/vllm-project/vllm-ascend/pull/3845) [#3910](https://github.com/vllm-project/vllm-ascend/pull/3910) [#3915](https://github.com/vllm-project/vllm-ascend/pull/3915) [#4102](https://github.com/vllm-project/vllm-ascend/pull/4102) [#4111](https://github.com/vllm-project/vllm-ascend/pull/4111) [#4770](https://github.com/vllm-project/vllm-ascend/pull/4770) [#5477](https://github.com/vllm-project/vllm-ascend/pull/5477)
- **Eagle Speculative Decoding**: Eagle spec decode now works with full graph mode and is more stable. [#5118](https://github.com/vllm-project/vllm-ascend/pull/5118) [#4893](https://github.com/vllm-project/vllm-ascend/pull/4893) [#5804](https://github.com/vllm-project/vllm-ascend/pull/5804)
- **PD Disaggregation**: Set ADXL engine as default backend for disaggregated prefill with improved performance and stability. Added support for KV NZ feature for DeepSeek decode node. [#3761](https://github.com/vllm-project/vllm-ascend/pull/3761) [#3950](https://github.com/vllm-project/vllm-ascend/pull/3950) [#5008](https://github.com/vllm-project/vllm-ascend/pull/5008) [#3072](https://github.com/vllm-project/vllm-ascend/pull/3072)
- **KV Pool & Mooncake**: Enhanced KV pool with Mooncake connector support for PCP/DCP, multiple input suffixes, and improved performance of Layerwise Connector. [#3690](https://github.com/vllm-project/vllm-ascend/pull/3690) [#3752](https://github.com/vllm-project/vllm-ascend/pull/3752) [#3849](https://github.com/vllm-project/vllm-ascend/pull/3849) [#4183](https://github.com/vllm-project/vllm-ascend/pull/4183) [#5303](https://github.com/vllm-project/vllm-ascend/pull/5303)
- **EPLB (Elastic Prefill Load Balancing)**: [Experimental]EPLB is now more stable with many bug fixes. Mix placement now works. [#6086](https://github.com/vllm-project/vllm-ascend/pull/6086)
- **Full Decode Only Mode**: Added support for Qwen3-Next and DeepSeekv32 in full_decode_only mode with bug fixes. [#3949](https://github.com/vllm-project/vllm-ascend/pull/3949) [#3986](https://github.com/vllm-project/vllm-ascend/pull/3986) [#3763](https://github.com/vllm-project/vllm-ascend/pull/3763)
- **Model Runner V2**: [Experimental]Added basic support for Model Runner V2, the next generation of vLLM. It will be used by default in future releases. [#5210](https://github.com/vllm-project/vllm-ascend/pull/5210)

### Features

- **W8A16 Quantization**: [Experimental]Added new W8A16 quantization method support. [#4541](https://github.com/vllm-project/vllm-ascend/pull/4541)
- **UCM Connector**: [Experimental]Added UCMConnector for KV Cache Offloading. [#4411](https://github.com/vllm-project/vllm-ascend/pull/4411)
- **Batch Invariant**: [Experimental]Implemented basic framework for batch invariant feature. [#5517](https://github.com/vllm-project/vllm-ascend/pull/5517)
- **Sampling**: Enhanced sampling with async_scheduler and disable_padded_drafter_batch support in Eagle. [#4893](https://github.com/vllm-project/vllm-ascend/pull/4893)

### Hardware and Operator Support

- **Custom Operators**: Added multiple custom operators including:
    - Fused matmul/reduce-scatter kernel [#3693](https://github.com/vllm-project/vllm-ascend/pull/3693)
    - mrope fusion op [#3708](https://github.com/vllm-project/vllm-ascend/pull/3708)
    - Triton chunk_gated_delta_rule ops for Qwen3-Next [#4070](https://github.com/vllm-project/vllm-ascend/pull/4070)
    - l2norm triton kernel [#4595](https://github.com/vllm-project/vllm-ascend/pull/4595)
    - RejectSampler, MoeInitRoutingCustom, DispatchFFNCombine custom ops
- **Operator Fusion**: Added AddRmsnormQuant fusion pattern with SP support and inductor fusion for quantization. [#5077](https://github.com/vllm-project/vllm-ascend/pull/5077) [#4168](https://github.com/vllm-project/vllm-ascend/pull/4168)
- **MLA/SFA**: Refactored SFA into MLA architecture for better maintainability. [#3769](https://github.com/vllm-project/vllm-ascend/pull/3769)
- **FIA Operator**: Adapted to npu_fused_infer_attention_score with flash decoding function. To optimize performance in small batch size scenarios, this attention operator is now available. Please refer to item 22 in [FAQs](https://docs.vllm.ai/projects/ascend/en/v0.13.0/faqs.html) to enable it. [#4025](https://github.com/vllm-project/vllm-ascend/pull/4025)
- **CANN 8.5 Support**: Removed CP redundant variables after FIA operator enables for CANN 8.5. [#6039](https://github.com/vllm-project/vllm-ascend/pull/6039)

### Performance

Many custom ops and triton kernels were added in this release to speed up model performance:

- **DeepSeek Performance**: [Experimental]Improved performance for DeepSeek V3.2 by eliminating HD synchronization in async scheduling and optimizing memory usage for MTP. [#4805](https://github.com/vllm-project/vllm-ascend/pull/4805) [#2713](https://github.com/vllm-project/vllm-ascend/pull/2713)
- **Qwen3-Next Performance**: [Experimental]Improved performance with Triton ops and optimizations. [#5664](https://github.com/vllm-project/vllm-ascend/pull/5664) [#5984](https://github.com/vllm-project/vllm-ascend/pull/5984) [#5765](https://github.com/vllm-project/vllm-ascend/pull/5765)
- **FlashComm**: Enhanced FlashComm v2 optimization with o_shared linear and communication domain fixes. [#3232](https://github.com/vllm-project/vllm-ascend/pull/3232) [#4188](https://github.com/vllm-project/vllm-ascend/pull/4188) [#4458](https://github.com/vllm-project/vllm-ascend/pull/4458) [#5848](https://github.com/vllm-project/vllm-ascend/pull/5848)
- **MoE Optimization**: Optimized all2allv for MoE models and enhanced all-reduce skipping logic. [#3738](https://github.com/vllm-project/vllm-ascend/pull/3738) [#5329](https://github.com/vllm-project/vllm-ascend/pull/5329)
- **Attention Optimization**: Moved attention update stream out of loop, converted BSND to TND format for long sequence optimization, and removed transpose step after attention switching to transpose_batchmatmul. [#3848](https://github.com/vllm-project/vllm-ascend/pull/3848) [#3778](https://github.com/vllm-project/vllm-ascend/pull/3778) [#5390](https://github.com/vllm-project/vllm-ascend/pull/5390)
- **Quantization Performance**: Moved quantization before allgather in Allgather EP. [#3420](https://github.com/vllm-project/vllm-ascend/pull/3420)
- **Layerwise Connector**: [Experimental]Improved performance of Layerwise Connector. [#5303](https://github.com/vllm-project/vllm-ascend/pull/5303)
- **Prefix Cache**: Improved performance of prefix cache features. [#4022](https://github.com/vllm-project/vllm-ascend/pull/4022)
- **Async Scheduling**: Fixed async copy and eliminated hangs in async scheduling. [#4113](https://github.com/vllm-project/vllm-ascend/pull/4113) [#4233](https://github.com/vllm-project/vllm-ascend/pull/4233)
- **Memory Operations**: Removed redundant D2H operations and deleted redundant operations in model_runner. [#4063](https://github.com/vllm-project/vllm-ascend/pull/4063) [#3677](https://github.com/vllm-project/vllm-ascend/pull/3677)
- **Rope Embedding**: Optimized rope embedding with triton kernel for huge performance gain. [#5918](https://github.com/vllm-project/vllm-ascend/pull/5918)
- **Sampling**: Added support for advanced apply_top_k_top_p without top_k constraint. [#6098](https://github.com/vllm-project/vllm-ascend/pull/6098)
- **Multimodal**: Parallelized Q/K/V padding in AscendMMEncoderAttention for better performance. [#6204](https://github.com/vllm-project/vllm-ascend/pull/6204)

### Dependencies

- **CANN**: Upgraded to 8.5.0 [#6112](https://github.com/vllm-project/vllm-ascend/pull/6112)
- **TorchNPU**: Upgraded to 2.8.0.post2. It's installed in the docker container by default.
- **triton-ascend**: Upgraded to 3.2.0 [#6105](https://github.com/vllm-project/vllm-ascend/pull/6105)
- **vLLM**: Upgraded to 0.13.0 and dropped 0.12.0 support. [#5146](https://github.com/vllm-project/vllm-ascend/pull/5146)
- **Transformers**: Upgraded to >= 4.57.4 [#5250](https://github.com/vllm-project/vllm-ascend/pull/5250)

### Deprecation & Breaking Changes

- **CPUOffloadingConnector** is deprecated. We'll remove it in the next release. It'll be replaced by CPUOffload feature from vLLM in the future.
- **ProfileExecuteDuration** [feature](https://docs.vllm.ai/projects/ascend/en/v0.13.0/developer_guide/performance_and_debug/profile_execute_duration.html) is deprecated.
- **Ascend Scheduler** has been dropped. [#4623](https://github.com/vllm-project/vllm-ascend/pull/4623)
- **Torchair** has been dropped. [#4814](https://github.com/vllm-project/vllm-ascend/pull/4814)
- **VLLM_ASCEND_ENABLE_DENSE_OPTIMIZE** is removed and `VLLM_ASCEND_ENABLE_PREFETCH_MLP` is recommended to replace as they were always enabled together. [#5272](https://github.com/vllm-project/vllm-ascend/pull/5272)
- **VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP** is dropped now. [#5270](https://github.com/vllm-project/vllm-ascend/pull/5270)
- **VLLM_ASCEND_ENABLE_NZ** is disabled for float weight case, since we noticed that the performance is not good in some float cases. Feel free to set it to 2 if you make sure it works for your case. [#4878](https://github.com/vllm-project/vllm-ascend/pull/4878)
- **chunked_prefill_for_mla** in `additional_config` is dropped now. [#5296](https://github.com/vllm-project/vllm-ascend/pull/5296)
- **dump_config** in `additional_config` is renamed to `dump_config_path` and the type is changed from `dict` to `string`. [#5296](https://github.com/vllm-project/vllm-ascend/pull/5296)
- **--task parameter** for embedding models is deprecated. [#5257](https://github.com/vllm-project/vllm-ascend/pull/5257)
- **The value of VLLM_ASCEND_ENABLE_MLAPO** env will be set to True by default in the next release. It'll be enabled in decode node by default. Please note that this feature will cost more memory. If you are memory sensitive, please set it to False.

### Documentation

- Added comprehensive developer guides for ACLGraph, MTP, KV Pool, EPLB, and PD disaggregation features
- Added tutorials for multiple models including DeepSeek-V3.2-Exp, Qwen3-Next, and various multimodal models
- Updated FAQ and configuration documentation

### Others

- **OOM Fix**: OOM error on VL models is fixed now. We're keeping observing it. If you hit OOM problem again, please submit an issue. [#5136](https://github.com/vllm-project/vllm-ascend/pull/5136)
- **Qwen3-Next-MTP Accuracy**: Fixed an accuracy bug of Qwen3-Next-MTP when batched inferring. [#4932](https://github.com/vllm-project/vllm-ascend/pull/4932)
- **ZMQ Bug Fix**: Fixed zmq send/receive failed bug. [#5503](https://github.com/vllm-project/vllm-ascend/pull/5503)
- **Weight Transpose**: Fixed weight transpose in RL scenarios. [#5567](https://github.com/vllm-project/vllm-ascend/pull/5567)
- **Eagle3 SP**: Adapted SP to eagle3. [#5562](https://github.com/vllm-project/vllm-ascend/pull/5562)
- **GLM4.6 MTP**: GLM4.6 now supports MTP with full graph. [#5460](https://github.com/vllm-project/vllm-ascend/pull/5460)
- **Fine-grained Shared Expert Overlap**: Support fine-grained shared expert overlap. [#5962](https://github.com/vllm-project/vllm-ascend/pull/5962)

### Known Issue

- Due to the upgrade of `transformers` package, some models quantization weight, such as `qwen2.5vl`, `gemma3`, `minimax`, may not work. We'll fix it in the next post release. [#6302](https://github.com/vllm-project/vllm-ascend/issues/6302)
- The performance of `Qwen3-32B` will not be good with 128k input case, it's suggested to enable pcp&dcp feature for this case. This will be improved in the next CANN release.
- The performance of `Qwen3-235B`, `Qwen3-480B` under prefill-decode scenario and EP=32 scenario is not good as expect. We'll improve it in the next post release.
- When deploy deepseek3.1 under prefill-decode scenario, please make sure the tp size for decode node is great than 1. `TP=1` doesn't work. This will be fixed in the next CANN release.

## v0.14.0rc1 - 2026.01.26

This is the first release candidate of v0.14.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started. This release includes all the changes in v0.13.0rc2. So We just list the differences from v0.13.0rc2. If you are upgrading from v0.13.0rc1, please read both v0.14.0rc1 and v0.13.0rc2 release notes.

### Highlights

- 310P support is back now. In this release, only basic dense and vl models are supported with eager mode. We'll keep improving and maintaining the support for 310P. [#5776](https://github.com/vllm-project/vllm-ascend/pull/5776)
- Support compressed tensors moe w8a8-int8 quantization. [#5718](https://github.com/vllm-project/vllm-ascend/pull/5718)
- Support Medusa speculative decoding. [#5668](https://github.com/vllm-project/vllm-ascend/pull/5668)
- Support Eagle3 speculative decoding for Qwen3vl. [#4848](https://github.com/vllm-project/vllm-ascend/pull/4848)

### Features

- Xlite Backend supports Qwen3 MoE now. [#5951](https://github.com/vllm-project/vllm-ascend/pull/5951)
- Support DSA-CP for PD-mix deployment case. [#5702](https://github.com/vllm-project/vllm-ascend/pull/5702)
- Add support of new W4A4_LAOS_DYNAMIC quantization method. [#5143](https://github.com/vllm-project/vllm-ascend/pull/5143)

### Performance

- The performance of Qwen3-next has been improved. [#5664](https://github.com/vllm-project/vllm-ascend/pull/5664) [#5984](https://github.com/vllm-project/vllm-ascend/pull/5984) [#5765](https://github.com/vllm-project/vllm-ascend/pull/5765)
- The CPU bind logic and performance has been improved. [#5555](https://github.com/vllm-project/vllm-ascend/pull/5555)
- Merge Q/K split to simplify AscendApplyRotaryEmb for better performance. [#5799](https://github.com/vllm-project/vllm-ascend/pull/5799)
- Add Matmul Allreduce Rmsnorm fusion Pass. It's disabled by default. Set `fuse_allreduce_rms=True` in `--additional_config` to enable it. [#5034](https://github.com/vllm-project/vllm-ascend/pull/5034)
- Optimize rope embedding with triton kernel for huge performance gain. [#5918](https://github.com/vllm-project/vllm-ascend/pull/5918)
- support advanced apply_top_k_top_p without top_k constraint. [#6098](https://github.com/vllm-project/vllm-ascend/pull/6098)
- Parallelize Q/K/V padding in AscendMMEncoderAttention for better performance. [#6204](https://github.com/vllm-project/vllm-ascend/pull/6204)

### Others

- model runner v2 support triton of penalty. [#5854](https://github.com/vllm-project/vllm-ascend/pull/5854)
- model runner v2 support eagle spec decoding. [#5840](https://github.com/vllm-project/vllm-ascend/pull/5840)
- Fix multimodal inference OOM issues by setting `expandable_segments:True` by default. [#5855](https://github.com/vllm-project/vllm-ascend/pull/5855)
- `VLLM_ASCEND_ENABLE_MLAPO` is set to `True` by default. It's enabled automatically on decode node in PD deployment case. Please note that this feature will cost more memory. If you are memory sensitive, please set it to False. [#5952](https://github.com/vllm-project/vllm-ascend/pull/5952)
- SSL config can be set to kv_extra_config for PD deployment with mooncake layerwise connector. [#5875](https://github.com/vllm-project/vllm-ascend/pull/5875)
- support `--max-model-len auto`. [#6193](https://github.com/vllm-project/vllm-ascend/pull/6193)

### Dependencies

- TorchNPU is upgraded to 2.9.0 [#6112](https://github.com/vllm-project/vllm-ascend/pull/6112)

### Deprecation & Breaking Changes

- EPLB config options is moved to `eplb_config` in [additional config](https://docs.vllm.ai/projects/ascend/en/latest/user_guide/configuration/additional_config.html). The old ones are removed in this release.
- The profiler envs, such as `VLLM_TORCH_PROFILER_DIR` and `VLLM_TORCH_PROFILER_WITH_PROFILE_MEMORY` do not work with vLLM Ascend now. Please use vLLM `--profiler-config` parameters instead. [#5928](https://github.com/vllm-project/vllm-ascend/pull/5928)

### Known Issues

- If you hit the pickle error from `EngineCore` process sometimes, please cherry-pick the [PR](https://github.com/vllm-project/vllm/pull/32022) into your local vLLM code. This known issue will be fixed in vLLM in the next release.

## v0.13.0rc2 - 2026.01.24

This is the second release candidate of v0.13.0 for vLLM Ascend. In this rc release, we fixed lots of bugs and improved the performance of many models. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.13.0/) to get started. Any feedback is welcome to help us to improve the final version of v0.13.0.

### Highlights

We mainly focus on quality and performance improvement in this release. The spec decode, graph mode, context parallel and EPLB have been improved significantly. A lot of bugs have been fixed and the performance has been improved for DeepSeek3.1/3.2, Qwen3 Dense/MOE models.

### Features

- implement basic framework for batch invariant [#5517](https://github.com/vllm-project/vllm-ascend/pull/5517)
- Eagle spec decode feature now works with full graph mode. [#5118](https://github.com/vllm-project/vllm-ascend/pull/5118)
- Context Parallel(PCP&DCP) feature is more stable now. And it works for most cases. Please try it out.
- MTP and eagle spec decode feature now works in most cases. And it's suggested to use them in most cases.
- EPLB feature more stable now. Many bugs have been fixed. Mix placement works now [#6086](https://github.com/vllm-project/vllm-ascend/pull/6086)
- Support kv nz feature for DeepSeek decode node in disagg-prefill scenario [#3072](https://github.com/vllm-project/vllm-ascend/pull/3072)

### Model Support

- LongCat-Flash is supported now.[#3833](https://github.com/vllm-project/vllm-ascend/pull/3833)
- minimax_m2 is supported now. [#5624](https://github.com/vllm-project/vllm-ascend/pull/5624)
- Support for cross-attention and whisper models [#5592](https://github.com/vllm-project/vllm-ascend/pull/5592)

### Performance

- Many custom ops and triton kernels are added in this release to speed up the performance of models. Such as `RejectSampler`, `MoeInitRoutingCustom`, `DispatchFFNCombine` and so on.
- Improved the performance of Layerwise Connector [#5303](https://github.com/vllm-project/vllm-ascend/pull/5303)

### Others

- Basic support Model Runner v2. Model Runner V2 is the next generation of vLLM. It will be used by default in the future release. [#5210](https://github.com/vllm-project/vllm-ascend/pull/5210)
- Fixed a bug that the zmq send/receive may failed [#5503](https://github.com/vllm-project/vllm-ascend/pull/5503)
- Supported to use full-graph with Qwen3-Next-MTP [#5477](https://github.com/vllm-project/vllm-ascend/pull/5477)
- Fix weight transpose in RL scenarios [#5567](https://github.com/vllm-project/vllm-ascend/pull/5567)
- Adapted SP to eagle3 [#5562](https://github.com/vllm-project/vllm-ascend/pull/5562)
- Context Parallel(PCP&DCP) support mlapo [#5672](https://github.com/vllm-project/vllm-ascend/pull/5672)
- GLM4.6 support mtp with full graph [#5460](https://github.com/vllm-project/vllm-ascend/pull/5460)
- Support setting tp=1 for the Eagle draft model [#5804](https://github.com/vllm-project/vllm-ascend/pull/5804)
- Flashcomm1 feature now works with qwen3-vl [#5848](https://github.com/vllm-project/vllm-ascend/pull/5848)
- Support fine-grained shared expert overlap [#5962](https://github.com/vllm-project/vllm-ascend/pull/5962)

### Dependencies

- CANN is upgraded to 8.5.0
- TorchNPU is upgraded to 2.8.0.post1. Please note that the post version will not be installed by default. Please install it by hand from [pypi mirror](https://mirrors.huaweicloud.com/ascend/repos/pypi/torch-npu/).
- triton-ascend is upgraded to 3.2.0

### Deprecation & Breaking Changes

- `CPUOffloadingConnector` is deprecated. We'll remove it in the next release. It'll be replaced by CPUOffload feature from vLLM in the future.
- eplb config options is moved to `eplb_config` in [additional config](https://docs.vllm.ai/projects/ascend/en/latest/user_guide/configuration/additional_config.html). The old ones will be removed in the next release.
- `ProfileExecuteDuration` [feature](https://github.com/vllm-project/vllm-ascend/blob/v0.13.0rc2/docs/source/developer_guide/performance_and_debug/profile_execute_duration.md) is deprecated. It's replaced by `ObservabilityConfig` from vLLM.
- The value of `VLLM_ASCEND_ENABLE_MLAPO` env will be set to True by default in the next release. It'll be enabled in decode node by default. Please note that this feature will cost more memory. If you are memory sensitive, please set it to False.

## v0.13.0rc1 - 2025.12.27

This is the first release candidate of v0.13.0 for vLLM Ascend. We landed lots of bug fix, performance improvement and feature support in this release. Any feedback is welcome to help us to improve vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- Improved the performance of DeepSeek V3.2, please refer to [tutorials](https://github.com/vllm-project/vllm-ascend/blob/v0.13.0rc1/docs/source/tutorials/DeepSeek-V3.2.md)
- Qwen3-Next MTP with chunked prefill is supported now [#4770](https://github.com/vllm-project/vllm-ascend/pull/4770), please refer to [tutorials](https://github.com/vllm-project/vllm-ascend/blob/v0.13.0rc1/docs/source/tutorials/Qwen3-Next.md)
- [Experimental] Prefill Context Parallel and Decode Context Parallel are supported, but notice that it is an experimental feature now, welcome any feedback. please refer to [context parallel feature guide](https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/context_parallel.html)

### Features

- Support openPangu Ultra MoE [4615](https://github.com/vllm-project/vllm-ascend/pull/4615)
- A new quantization method W8A16 is supported now. [#4541](https://github.com/vllm-project/vllm-ascend/pull/4541)
- Cross-machine Disaggregated Prefill is supported now. [#5008](https://github.com/vllm-project/vllm-ascend/pull/5008)
- Add UCMConnector for KV Cache Offloading. [#4411](https://github.com/vllm-project/vllm-ascend/pull/4411)
- Support async_scheduler and disable_padded_drafter_batch in eagle. [#4893](https://github.com/vllm-project/vllm-ascend/pull/4893)
- Support pcp + mtp in full graph mode. [#4572](https://github.com/vllm-project/vllm-ascend/pull/4572)
- Enhance all-reduce skipping logic for MoE models in NPUModelRunner [#5329](https://github.com/vllm-project/vllm-ascend/pull/5329)

### Performance

Some general performance improvement:

- Add l2norm triton kernel [#4595](https://github.com/vllm-project/vllm-ascend/pull/4595)
- Add new pattern for AddRmsnormQuant with SP, which could only take effect in graph mode. [#5077](https://github.com/vllm-project/vllm-ascend/pull/5077)
- Add async exponential while model executing. [#4501](https://github.com/vllm-project/vllm-ascend/pull/4501)
- Remove the transpose step after attention and switch to transpose_batchmatmul [#5390](https://github.com/vllm-project/vllm-ascend/pull/5390)
- To optimize the performance in small batch size scenario, an attention operator with flash decoding function is offered, please refer to item 22 in [Public FAQs](https://docs.vllm.ai/projects/ascend/en/latest/faqs.html) to enable it.

### Other

- OOM error on VL models is fixed now. We're keeping observing it, if you hit OOM problem again, please submit an issue. [#5136](https://github.com/vllm-project/vllm-ascend/pull/5136)
- Fixed an accuracy bug of Qwen3-Next-MTP when batched inferring. [#4932](https://github.com/vllm-project/vllm-ascend/pull/4932)
- Fix npu-cpu offloading interface change bug. [#5290](https://github.com/vllm-project/vllm-ascend/pull/5290)
- Fix MHA model runtime error in aclgraph mode [#5397](https://github.com/vllm-project/vllm-ascend/pull/5397)
- Fix unsuitable moe_comm_type under ep=1 scenario [#5388](https://github.com/vllm-project/vllm-ascend/pull/5388)

### Deprecation & Breaking Changes

- `VLLM_ASCEND_ENABLE_DENSE_OPTIMIZE` has been removed. `VLLM_ASCEND_ENABLE_PREFETCH_MLP` is recommended as a replacement, since they are always enabled together. [#5272](https://github.com/vllm-project/vllm-ascend/pull/5272)
- `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP` is dropped now. [#5270](https://github.com/vllm-project/vllm-ascend/pull/5270)
- `VLLM_ASCEND_ENABLE_NZ` is disabled for float weight case, since we notice that the performance is not good in some float case. Feel free to set it to 2 if you make sure it works for your case. [#4878](https://github.com/vllm-project/vllm-ascend/pull/4878)
- `chunked_prefill_for_mla` in `additional_config` is dropped now. [#5296](https://github.com/vllm-project/vllm-ascend/pull/5296)
- `dump_config` in `additional_config` is renamed to `dump_config_path` and the type is changed from `dict` to `string`. [#5296](https://github.com/vllm-project/vllm-ascend/pull/5296)

### Dependencies

- vLLM version has been upgraded to 0.13.0 and drop 0.12.0 support. [#5146](https://github.com/vllm-project/vllm-ascend/pull/5146)
- Transformer version has been upgraded >= 4.57.3 [#5250](https://github.com/vllm-project/vllm-ascend/pull/5250)

### Known Issues

- Qwen3-Next doesn't support long sequence scenario, and we should limit `gpu-memory-utilization` according to the doc to run Qwen3-Next. We'll improve it in the next release
- The functional break on Qwen3-Next when the input/output is around 3.5k/1.5k is fixed, but it introduces a regression on performance. We'll fix it in next release. [#5357](https://github.com/vllm-project/vllm-ascend/issues/5357)
- There is a precision issue with curl on ultra-short sequences in DeepSeek-V3.2. We'll fix it in next release. [#5370](https://github.com/vllm-project/vllm-ascend/issues/5370)

## v0.11.0 - 2025.12.16

We're excited to announce the release of v0.11.0 for vLLM Ascend. This is the official release for v0.11.0. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.11.0) to get started. We'll consider releasing post version in the future if needed. This release note will only contain the important change and note from v0.11.0rc3.

### Highlights

- Improved the performance for deepseek 3/3.1. [#3995](https://github.com/vllm-project/vllm-ascend/pull/3995)
- Fixed the accuracy bug for qwen3-vl. [#4811](https://github.com/vllm-project/vllm-ascend/pull/4811)
- Improved the performance of sample. [#4153](https://github.com/vllm-project/vllm-ascend/pull/4153)
- Eagle3 is back now. [#4721](https://github.com/vllm-project/vllm-ascend/pull/4721)

### Other

- Improved the performance for kimi-k2.  [#4555](https://github.com/vllm-project/vllm-ascend/pull/4555)
- Fixed a quantization bug for deepseek3.2-exp. [#4797](https://github.com/vllm-project/vllm-ascend/pull/4797)
- Fixed qwen3-vl-moe bug under high concurrency. [#4658](https://github.com/vllm-project/vllm-ascend/pull/4658)
- Fixed an accuracy bug for Prefill Decode disaggregation case. [#4437](https://github.com/vllm-project/vllm-ascend/pull/4437)
- Fixed some bugs for EPLB [#4576](https://github.com/vllm-project/vllm-ascend/pull/4576) [#4777](https://github.com/vllm-project/vllm-ascend/pull/4777)
- Fixed the version incompatibility issue for openEuler docker image. [#4745](https://github.com/vllm-project/vllm-ascend/pull/4745)

### Deprecation announcement

- LLMdatadist connector has been deprecated, it'll be removed in v0.12.0rc1
- Torchair graph has been deprecated, it'll be removed in v0.12.0rc1
- Ascend scheduler has been deprecated, it'll be removed in v0.12.0rc1

### Upgrade notice

- TorchNPU is upgraded to 2.7.1.post1. Please note that the package is pushed to [pypi mirror](https://mirrors.huaweicloud.com/ascend/repos/pypi/torch-npu/). So it's hard to add it to auto dependence. Please install it by yourself.
- CANN is upgraded to 8.3.rc2.

### Known Issues

- Qwen3-Next doesn't support expert parallel and MTP features in this release. And it'll be oom if the input is too long. We'll improve it in the next release
- Deepseek 3.2 only work with torchair graph mode in this release. We'll make it work with aclgraph mode in the next release.
- Qwen2-audio doesn't work by default. Temporary solution is to set `--gpu-memory-utilization` to a suitable value, such as 0.8.
- CPU bind feature doesn't work if more than one vLLM instance is running on the same node.

## v0.12.0rc1 - 2025.12.13

This is the first release candidate of v0.12.0 for vLLM Ascend. We landed lots of bug fix, performance improvement and feature support in this release. Any feedback is welcome to help us to improve vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest) to get started.

### Highlights

- DeepSeek 3.2 is stable and performance is improved. In this release, you don't need to install any other packages now. Following the [official tutorial](https://github.com/vllm-project/vllm-ascend/blob/v0.12.0rc1/docs/source/tutorials/DeepSeek-V3.2.md) to start using it.
- More new models, such as Qwen3-omni, DeepSeek OCR, PaddleOCR, OpenCUA are supported now.

### Core

- [Experimental] Full decode only graph mode is supported now. Although it is not enabled by default, we suggest to enable it by `--compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}'` in most cases. Let us know if you hit any error. We'll keep improve it and enable it by default in next few release.
- Lots of triton kernel are added. The performance of vLLM Ascend, especially Qwen3-Next and DeepSeek 3.2 is improved. Please note that triton is not installed and enabled by default, but we suggest to enable it in most cases. You can download and install it by hand from [package url](https://vllm-ascend.obs.cn-north-4.myhuaweicloud.com/vllm-ascend/triton_ascend-3.2.0.dev2025110717-cp311-cp311-manylinux_2_27_aarch64.whl). If you're running vLLM Ascend with X86, you need to build triton ascend by yourself from [source](https://gitcode.com/Ascend/triton-ascend)
- Lots of Ascend ops are added to improve the performance. It means that from this release vLLM Ascend only works with custom ops built. So we removed the env `COMPILE_CUSTOM_KERNELS`. You can not set it to 0 now.
- speculative decode method `MTP` is more stable now. It can be enabled with most cases and decode token number can be 1,2,3.
- speculative decode method `suffix` is supported now. Thanks for the contribution from China Merchants Bank.
- llm-compressor quantization tool with W8A8 works now. You can now deploy the model with W8A8 quantization from this tool directly.
- W4A4 quantization works now.
- Support features flashcomm1 and flashcomm2 in paper [flashcomm](https://arxiv.org/pdf/2412.04964) [#3004](https://github.com/vllm-project/vllm-ascend/pull/3004) [#3334](https://github.com/vllm-project/vllm-ascend/pull/3334)
- Pooling model, such as bge, reranker, etc. are supported now
- Official doc has been improved. we refactored the tutorial to make it more clear. The user guide and developer guide is more complete now. We'll keep improving it.

### Other

- [Experimental] Mooncake layerwise connector is supported now.
- [Experimental] [KV cache pool](https://docs.vllm.ai/projects/ascend/en/latest/developer_guide/Design_Documents/KV_Cache_Pool_Guide.html) feature is added
- [Experimental] A new graph mode `xlite` is introduced. It performs good with some models. Following the [official tutorial](https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/graph_mode.html#using-xlitegraph) to start using it.
- LLMdatadist kv connector is removed. Please use mooncake connector instead.
- Ascend scheduler is removed. `--additional-config {"ascend_scheduler": {"enabled": true}}` doesn't work anymore.
- Torchair graph mode is removed. `--additional-config {"torchair_graph_config": {"enabled": true}}` doesn't work anymore. Please use aclgraph instead.
- `VLLM_ASCEND_ENABLE_TOPK_TOPP_OPTIMIZATION` env is removed. This feature is stable enough. We enable it by default now.
- speculative decode method `Ngram` is back now.
- msprobe tool is added to help user to check the model accuracy. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest/developer_guide/performance_and_debug/msprobe_guide.html) to get started.
- msserviceprofiler tool is added to help user to profile the model performance. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/blob/v0.12.0rc1/docs/source/developer_guide/performance_and_debug/service_profiling_guide.md) to get started.

### Upgrade Note

- vLLM Ascend self maintained modeling file has been removed. The related python entrypoint is removed as well. So please uninstall the old version of vLLM Ascend in your env before upgrade.
- CANN is upgraded to 8.3.RC2, PyTorch and TorchNPU are upgraded to 2.8.0. Don't forget to install them.
- Python 3.9 support is dropped to keep the same with vLLM v0.12.0

### Known Issues

- DeepSeek 3/3.1 and Qwen3 doesn't work with FULL_DECODE_ONLY graph mode. We'll fix it in next release. [#4990](https://github.com/vllm-project/vllm-ascend/issues/4990)
- Hunyuan OCR doesn't work. We'll fix it in the next release. [#4989](https://github.com/vllm-project/vllm-ascend/issues/4989) [#4992](https://github.com/vllm-project/vllm-ascend/issues/4992)
- DeepSeek 3.2 doesn't work with chat template. It because that vLLM v0.12.0 doesn't support it. We'll support in the next v0.13.0rc1 version.
- DeepSeek 3.2 doesn't work with high concurrency in some case. We'll fix it in next release. [#4996](https://github.com/vllm-project/vllm-ascend/issues/4996)
- We notice that bf16/fp16 model doesn't perform well. This is mainly because `VLLM_ASCEND_ENABLE_NZ` is enabled by default. Please set `VLLM_ASCEND_ENABLE_NZ=0` to disable it. We'll add the auto detection mechanism in next release.
- speculative decode method `suffix` doesn't work. We'll fix it in next release. You can pick this commit to fix the issue: [#5010](https://github.com/vllm-project/vllm-ascend/issues/5010)

## v0.11.0rc3 - 2025.12.03

This is the third release candidate of v0.11.0 for vLLM Ascend. For quality reasons, we released a new rc before the official release. Thanks for all your feedback. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.11.0) to get started.

### Highlights

- TorchNPU is upgraded to 2.7.1.post1. Please note that the package is pushed to [pypi mirror](https://mirrors.huaweicloud.com/ascend/repos/pypi/torch-npu/). So it's hard to add it to auto dependence. Please install it by yourself.
- Disable NZ weight loader to speed up dense model. Please note that this is a temporary solution. If you find the performance becomes bad, please let us know. We'll keep improving it. [#4495](https://github.com/vllm-project/vllm-ascend/pull/4495)
- mooncake is installed in official docker image now. You can use it directly in container now. [#4506](https://github.com/vllm-project/vllm-ascend/pull/4506)

### Other

- Fix an OOM issue for moe models. [#4367](https://github.com/vllm-project/vllm-ascend/pull/4367)
- Fix hang issue of multimodal model when running with DP>1 [#4393](https://github.com/vllm-project/vllm-ascend/pull/4393)
- Fix some bugs for EPLB [#4416](https://github.com/vllm-project/vllm-ascend/pull/4416)
- Fix bug for mtp>1 + lm_head_tp>1 case [#4360](https://github.com/vllm-project/vllm-ascend/pull/4360)
- Fix a accuracy issue when running vLLM serve for long time. [#4117](https://github.com/vllm-project/vllm-ascend/pull/4117)
- Fix a functional bug when running qwen2.5 vl under high concurrency. [#4553](https://github.com/vllm-project/vllm-ascend/pull/4553)

## v0.11.0rc2 - 2025.11.21

This is the second release candidate of v0.11.0 for vLLM Ascend. In this release, we solved many bugs to improve the quality. Thanks for all your feedback. We'll keep working on bug fix and performance improvement. The v0.11.0 official release will come soon. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.11.0) to get started.

### Highlights

- CANN is upgraded to 8.3.RC2. [#4332](https://github.com/vllm-project/vllm-ascend/pull/4332)
- Ngram spec decode method is back now. [#4092](https://github.com/vllm-project/vllm-ascend/pull/4092)
- The performance of aclgraph is improved by updating default capture size. [#4205](https://github.com/vllm-project/vllm-ascend/pull/4205)

### Core

- Speed up vLLM startup time. [#4099](https://github.com/vllm-project/vllm-ascend/pull/4099)
- Kimi k2 with quantization works now. [#4190](https://github.com/vllm-project/vllm-ascend/pull/4190)
- Fix a bug for qwen3-next. It's more stable now. [#4025](https://github.com/vllm-project/vllm-ascend/pull/4025)

### Other

- Fix an issue for full decode only mode. Full graph mode is more stable now. [#4106](https://github.com/vllm-project/vllm-ascend/pull/4106) [#4282](https://github.com/vllm-project/vllm-ascend/pull/4282)
- Fix a allgather ops bug for DeepSeek V3 series models. [#3711](https://github.com/vllm-project/vllm-ascend/pull/3711)
- Fix some bugs for EPLB feature. [#4150](https://github.com/vllm-project/vllm-ascend/pull/4150) [#4334](https://github.com/vllm-project/vllm-ascend/pull/4334)
- Fix a bug that vl model doesn't work on x86 machine. [#4285](https://github.com/vllm-project/vllm-ascend/pull/4285)
- Support ipv6 for prefill disaggregation proxy. Please note that mooncake connector doesn't work with ipv6. We're working on it. [#4242](https://github.com/vllm-project/vllm-ascend/pull/4242)
- Add a check that to ensure EPLB only support w8a8 method for quantization case. [#4315](https://github.com/vllm-project/vllm-ascend/pull/4315)
- Add a check that to ensure FLASHCOMM feature doesn't work with vl model. It'll be supported in 2025 Q4 [#4222](https://github.com/vllm-project/vllm-ascend/pull/4222)
- Audio required library is installed in container. [#4324](https://github.com/vllm-project/vllm-ascend/pull/4324)

### Known Issues

- Ray + EP doesn't work, if you run vLLM Ascend with ray, please disable expert parallelism. [#4123](https://github.com/vllm-project/vllm-ascend/issues/4123)
- `response_format` parameter is not supported yet. We'll support it soon. [#4175](https://github.com/vllm-project/vllm-ascend/issues/4175)
- cpu bind feature doesn't work for multi instance case(Such as multi DP on one node). We'll fix it in the next release.

## v0.11.0rc1 - 2025.11.10

This is the first release candidate of v0.11.0 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.11.0) to get started.
v0.11.0 will be the next official release version of vLLM Ascend. We'll release it in the next few days. Any feedback is welcome to help us to improve v0.11.0.

### Highlights

- CANN is upgraded to 8.3.RC1. TorchNPU is upgraded to 2.7.1. [#3945](https://github.com/vllm-project/vllm-ascend/pull/3945) [#3896](https://github.com/vllm-project/vllm-ascend/pull/3896)
- PrefixCache and Chunked Prefill are enabled by default. [#3967](https://github.com/vllm-project/vllm-ascend/pull/3967)
- W4A4 quantization is supported now. [#3427](https://github.com/vllm-project/vllm-ascend/pull/3427) Official tutorial is available at [single_npu_qwen3_w4a4](https://github.com/vllm-project/vllm-ascend/pull/4076/files).

### Core

- Performance of Qwen3 and Deepseek V3 series models are improved.
- Mooncake layerwise connector is supported now [#2602](https://github.com/vllm-project/vllm-ascend/pull/2602). Find tutorial [pd_disaggregation_mooncake_multi_node](https://github.com/vllm-project/vllm-ascend/blob/v0.11.0rc1/docs/source/tutorials/multi_node_pd_disaggregation_mooncake.md).
- MTP > 1 is supported now. [#2708](https://github.com/vllm-project/vllm-ascend/pull/2708)
- [Experimental] Graph mode `FULL_DECODE_ONLY` is supported now! And `FULL` will be landing in the next few weeks. [#2128](https://github.com/vllm-project/vllm-ascend/pull/2128)
- Pooling models, such as bge-m3, are supported now. [#3171](https://github.com/vllm-project/vllm-ascend/pull/3171)

### Other

- Refactor the MOE module to make it clearer and easier to understand and the performance has improved in both quantitative and non-quantitative scenarios.
- Refactor model register module to make it easier to maintain. We'll remove this module in Q4 2025. [#3004](https://github.com/vllm-project/vllm-ascend/pull/3004)
- Torchair is deprecated. We'll remove it once the performance of ACL Graph is good enough. The deadline is Q1 2026.
- LLMDatadist KV Connector is deprecated. We'll remove it in Q1 2026.
- Refactor the linear module to support features flashcomm1 and flashcomm2 in paper [flashcomm](https://arxiv.org/pdf/2412.04964) [#3004](https://github.com/vllm-project/vllm-ascend/pull/3004) [#3334](https://github.com/vllm-project/vllm-ascend/pull/3334)

### Known issue

- The memory may be leaked and the service may be stuck after long time serving. This is a bug from TorchNPU, we'll upgrade and fix it soon.
- The accuracy of qwen2.5 VL is not very good. This is a bug caused by CANN, we will fix it soon.
- For long sequence input case, there is no response sometimes and the kv cache usage becomes higher. This is a bug for scheduler. We are working on it.
- Qwen2-audio doesn't work by default, we're fixing it. Temporary solution is to set `--gpu-memory-utilization` to a suitable value, such as 0.8.
- When running Qwen3-Next with expert parallel enabled, please set `HCCL_BUFFSIZE` environment variable to a suitable value, such as 1024.
- The accuracy of DeepSeek3.2 with aclgraph is not correct. Temporary solution is to set cudagraph_capture_sizes to a suitable value depending on the batch size for the input.

## v0.11.0rc0 - 2025.09.30

This is the special release candidate of v0.11.0 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.11.0rc0) to get started.

### Highlights

- DeepSeek V3.2 is supported now. [#3270](https://github.com/vllm-project/vllm-ascend/pull/3270)
- Qwen3-vl is supported now. [#3103](https://github.com/vllm-project/vllm-ascend/pull/3103)

### Core

- DeepSeek works with aclgraph now. [#2707](https://github.com/vllm-project/vllm-ascend/pull/2707)
- MTP works with aclgraph now. [#2932](https://github.com/vllm-project/vllm-ascend/pull/2932)
- EPLB is supported now. [#2956](https://github.com/vllm-project/vllm-ascend/pull/2956)
- Mooncake store kvcache connector is supported now. [#2913](https://github.com/vllm-project/vllm-ascend/pull/2913)
- CPU offload connector is supported now. [#1659](https://github.com/vllm-project/vllm-ascend/pull/1659)

### Others

- Qwen3-next is stable now. [#3007](https://github.com/vllm-project/vllm-ascend/pull/3007)
- Fixed a lot of bugs introduced in v0.10.2 by Qwen3-next. [#2964](https://github.com/vllm-project/vllm-ascend/pull/2964) [#2781](https://github.com/vllm-project/vllm-ascend/pull/2781) [#3070](https://github.com/vllm-project/vllm-ascend/pull/3070) [#3113](https://github.com/vllm-project/vllm-ascend/pull/3113)
- The LoRA feature is back now. [#3044](https://github.com/vllm-project/vllm-ascend/pull/3044)
- Eagle3 spec decode method is back now. [#2949](https://github.com/vllm-project/vllm-ascend/issues/2949)

## v0.10.2rc1 - 2025.09.16

This is the 1st release candidate of v0.10.2 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.10.2rc1) to get started.

### Highlights

- Added support for Qwen3-Next. Please note that the expert parallel and MTP features do not work with this release. We will be adding support for them soon. Follow the [official guide](https://github.com/vllm-project/vllm-ascend/blob/v0.10.2rc1/docs/source/tutorials/multi_npu_qwen3_next.md) to get started. [#2917](https://github.com/vllm-project/vllm-ascend/pull/2917)
- Added quantization support for aclgraph [#2841](https://github.com/vllm-project/vllm-ascend/pull/2841)

### Core

- Aclgraph now works with Ray backend. [#2589](https://github.com/vllm-project/vllm-ascend/pull/2589)
- MTP now works with the token > 1. [#2708](https://github.com/vllm-project/vllm-ascend/pull/2708)
- Qwen2.5 VL now works with quantization. [#2778](https://github.com/vllm-project/vllm-ascend/pull/2778)
- Improved the performance with async scheduler enabled. [#2783](https://github.com/vllm-project/vllm-ascend/pull/2783)
- Fixed the performance regression with non MLA model when using default scheduler. [#2894](https://github.com/vllm-project/vllm-ascend/pull/2894)

### Others

- The performance of W8A8 quantization is improved. [#2275](https://github.com/vllm-project/vllm-ascend/pull/2275)
- The performance is improved for moe models. [#2689](https://github.com/vllm-project/vllm-ascend/pull/2689) [#2842](https://github.com/vllm-project/vllm-ascend/pull/2842)
- Fixed resources limit error when apply speculative decoding and aclgraph. [#2472](https://github.com/vllm-project/vllm-ascend/pull/2472)
- Fixed the git config error in Docker images. [#2746](https://github.com/vllm-project/vllm-ascend/pull/2746)
- Fixed the sliding windows attention bug with prefill. [#2758](https://github.com/vllm-project/vllm-ascend/pull/2758)
- The official doc for Prefill-Decode Disaggregation with Qwen3 is added. [#2751](https://github.com/vllm-project/vllm-ascend/pull/2751)
- `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP` env works again. [#2740](https://github.com/vllm-project/vllm-ascend/pull/2740)
- A new improvement for oproj in deepseek is added. Set `oproj_tensor_parallel_size` to enable this feature. [#2167](https://github.com/vllm-project/vllm-ascend/pull/2167)
- Fix a bug that deepseek with torchair doesn't work as expect when `graph_batch_sizes` is set. [#2760](https://github.com/vllm-project/vllm-ascend/pull/2760)
- Avoid duplicate generation of sin_cos_cache in rope when kv_seqlen > 4k. [#2744](https://github.com/vllm-project/vllm-ascend/pull/2744)
- The performance of Qwen3 dense model is improved with flashcomm_v1. Set `VLLM_ASCEND_ENABLE_DENSE_OPTIMIZE=1` and `VLLM_ASCEND_ENABLE_FLASHCOMM=1` to enable it. [#2779](https://github.com/vllm-project/vllm-ascend/issues/2779)
- The performance of Qwen3 dense model is improved with prefetch feature. Set `VLLM_ASCEND_ENABLE_PREFETCH_MLP=1` to enable it. [#2816](https://github.com/vllm-project/vllm-ascend/pull/2816)
- The performance of Qwen3 MoE model is improved with rope ops update. [#2571](https://github.com/vllm-project/vllm-ascend/pull/2571)
- Fix the weight load error for RLHF case. [#2756](https://github.com/vllm-project/vllm-ascend/pull/2756)
- Add warm_up_atb step to speed up the inference. [#2823](https://github.com/vllm-project/vllm-ascend/pull/2823)
- Fixed the aclgraph steam error for moe model. [#2827](https://github.com/vllm-project/vllm-ascend/pull/2827)

### Known Issues

- The server will hang when running Prefill Decode Disaggregation with different TP size for P and D. It's fixed by [vLLM commit](https://github.com/vllm-project/vllm/pull/23917) which is not included in v0.10.2. You can pick this commit to fix the issue.
- The HBM usage of Qwen3-Next is higher than expected. It is a [known issue](https://github.com/vllm-project/vllm-ascend/issues/2884) and we are working on it. You can set `max_model_len` and `gpu_memory_utilization` to suitable value based on your parallel configuration to avoid oom error.
- We notice that LoRA does not work with this release due to the refactor of KV cache. We will fix it soon. [2941](https://github.com/vllm-project/vllm-ascend/issues/2941)
- Please do not enable chunked prefill with prefix cache when running with Ascend scheduler. The performance and accuracy is not good/correct. [#2943](https://github.com/vllm-project/vllm-ascend/issues/2943)

## v0.10.1rc1 - 2025.09.04

This is the 1st release candidate of v0.10.1 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.10.1rc1) to get started.

### Highlights

- LoRA Performance improved much through adding Custom Kernels by China Merchants Bank. [#2325](https://github.com/vllm-project/vllm-ascend/pull/2325)
- Support Mooncake TransferEngine for kv cache register and pull_blocks style disaggregate prefill implementation. [#1568](https://github.com/vllm-project/vllm-ascend/pull/1568)
- Support capture custom ops into aclgraph now. [#2113](https://github.com/vllm-project/vllm-ascend/pull/2113)

### Core

- Added MLP tensor parallel to improve performance, but note that this will increase memory usage. [#2120](https://github.com/vllm-project/vllm-ascend/pull/2120)
- openEuler is upgraded to 24.03. [#2631](https://github.com/vllm-project/vllm-ascend/pull/2631)
- Added custom lmhead tensor parallel to achieve reduced memory consumption and improved TPOT performance. [#2309](https://github.com/vllm-project/vllm-ascend/pull/2309)
- Qwen3 MoE/Qwen2.5 support torchair graph now. [#2403](https://github.com/vllm-project/vllm-ascend/pull/2403)
- Support Sliding Window Attention with AscendSceduler, thus fixing Gemma3 accuracy issue. [#2528](https://github.com/vllm-project/vllm-ascend/pull/2528)

### Others

- Bug fixes:
    - Updated the graph capture size calculation, somehow alleviated the problem that NPU stream not enough in some scenarios. [#2511](https://github.com/vllm-project/vllm-ascend/pull/2511)
    - Fixed bugs and refactor cached mask generation logic. [#2442](https://github.com/vllm-project/vllm-ascend/pull/2442)
    - Fixed the nz format does not work in quantization scenarios. [#2549](https://github.com/vllm-project/vllm-ascend/pull/2549)
    - Fixed the accuracy issue on Qwen series caused by enabling `enable_shared_pert_dp` by default. [#2457](https://github.com/vllm-project/vllm-ascend/pull/2457)
    - Fixed the accuracy issue on models whose rope dim is not equal to head dim, e.g., GLM4.5. [#2601](https://github.com/vllm-project/vllm-ascend/pull/2601)
- Performance improved through a lot of prs:
    - Removed torch.cat and replaced it with List[0]. [#2153](https://github.com/vllm-project/vllm-ascend/pull/2153)
    - Converted the format of gmm to nz. [#2474](https://github.com/vllm-project/vllm-ascend/pull/2474)
    - Optimized parallel strategies to reduce communication overhead. [#2198](https://github.com/vllm-project/vllm-ascend/pull/2198)
    - Optimized reject sampler in greedy situation. [#2137](https://github.com/vllm-project/vllm-ascend/pull/2137)
- A batch of refactoring PRs to enhance the code architecture:
    - Refactor on MLA. [#2465](https://github.com/vllm-project/vllm-ascend/pull/2465)
    - Refactor on torchair fused_moe. [#2438](https://github.com/vllm-project/vllm-ascend/pull/2438)
    - Refactor on allgather/mc2-related fused_experts. [#2369](https://github.com/vllm-project/vllm-ascend/pull/2369)
    - Refactor on torchair model runner. [#2208](https://github.com/vllm-project/vllm-ascend/pull/2208)
    - Refactor on CI. [#2276](https://github.com/vllm-project/vllm-ascend/pull/2276)
- Parameters changes:
    - Added `lmhead_tensor_parallel_size` in `additional_config`, set it to enable lmhead tensor parallel. [#2309](https://github.com/vllm-project/vllm-ascend/pull/2309)
    - Some unused environment variables `HCCN_PATH`, `PROMPT_DEVICE_ID`, `DECODE_DEVICE_ID`, `LLMDATADIST_COMM_PORT` and `LLMDATADIST_SYNC_CACHE_WAIT_TIME`  are removed. [#2448](https://github.com/vllm-project/vllm-ascend/pull/2448)
    - Environment variable `VLLM_LLMDD_RPC_PORT` is renamed to `VLLM_ASCEND_LLMDD_RPC_PORT` now. [#2450](https://github.com/vllm-project/vllm-ascend/pull/2450)
    - Added `VLLM_ASCEND_ENABLE_MLP_OPTIMIZE` in environment variables, Whether to enable mlp optimize when tensor parallel is enabled. This feature provides better performance in eager mode. [#2120](https://github.com/vllm-project/vllm-ascend/pull/2120)
    - Removed `MOE_ALL2ALL_BUFFER` and `VLLM_ASCEND_ENABLE_MOE_ALL2ALL_SEQ` in environment variables. [#2612](https://github.com/vllm-project/vllm-ascend/pull/2612)
    - Added `enable_prefetch` in `additional_config`, Whether to enable weight prefetch. [#2465](https://github.com/vllm-project/vllm-ascend/pull/2465)
    - Added `mode` in `additional_config.torchair_graph_config`, When using reduce-overhead mode for torchair, mode needs to be set. [#2461](https://github.com/vllm-project/vllm-ascend/pull/2461)
    - `enable_shared_expert_dp` in `additional_config` is disabled by default now, and it is recommended to be enabled when inferencing with deepseek. [#2457](https://github.com/vllm-project/vllm-ascend/pull/2457)

### Known Issues

- Sliding window attention not support chunked prefill currently, thus we could only enable AscendScheduler to run with it. [#2729](https://github.com/vllm-project/vllm-ascend/issues/2729)
- There is a bug with creating mc2_mask when MultiStream is enabled, will fix it in next release. [#2681](https://github.com/vllm-project/vllm-ascend/pull/2681)

## v0.9.1 - 2025.09.03

We are excited to announce the newest official release of vLLM Ascend. This release includes many feature supports, performance improvements and bug fixes. We recommend users to upgrade from 0.7.3 to this version. Please always set `VLLM_USE_V1=1` to use V1 engine.

In this release, we added many enhancements for large scale expert parallel case. It's recommended to follow the [official guide](https://github.com/vllm-project/vllm-ascend/blob/v0.9.1/docs/source/tutorials/large_scale_ep.md).

Please note that this release note will list all the important changes from last official release(v0.7.3)

### Highlights

- DeepSeek V3/R1 is supported with high quality and performance. MTP can work with DeepSeek as well. Please refer to [multi node tutorials](https://docs.vllm.ai/projects/ascend/en/v0.9.1/tutorials/multi_node.html) and [Large Scale Expert Parallelism](https://github.com/vllm-project/vllm-ascend/blob/v0.9.1/docs/source/tutorials/large_scale_ep.md).
- Qwen series models work with graph mode now. It works by default with V1 Engine. Please refer to [Qwen tutorials](https://docs.vllm.ai/projects/ascend/en/v0.9.1/tutorials/index.html).
- Disaggregated Prefilling support for V1 Engine. Please refer to [Large Scale Expert Parallelism](https://github.com/vllm-project/vllm-ascend/blob/v0.9.1/docs/source/tutorials/large_scale_ep.md) tutorials.
- Automatic prefix caching and chunked prefill feature is supported.
- Speculative decoding feature works with Ngram and MTP method.
- MOE and dense w4a8 quantization support now. Please refer to [quantization guide](https://docs.vllm.ai/projects/ascend/en/v0.9.1/user_guide/feature_guide/quantization.html).
- Sleep Mode feature is supported for V1 engine. Please refer to [Sleep mode tutorials](https://docs.vllm.ai/projects/ascend/en/v0.9.1/user_guide/feature_guide/sleep_mode.html).
- Dynamic and Static EPLB support is added. This feature is still experimental.

### Note

The following notes are especially for reference when upgrading from last final release (v0.7.3):

- V0 Engine is not supported from this release. Please always set `VLLM_USE_V1=1` to use V1 engine with vLLM Ascend.
- Mindie Turbo is not needed with this release. And the old version of Mindie Turbo is not compatible. Please do not install it. Currently all the function and enhancement is included in vLLM Ascend already. We'll consider adding it back in the future if needed.
- TorchNPU is upgraded to 2.5.1.post1. CANN is upgraded to 8.2.RC1. Don't forget to upgrade them.

### Core

- The Ascend scheduler is added for V1 engine. This scheduler is more affine with Ascend hardware.
- Structured output feature works now on V1 Engine.
- A batch of custom ops are added to improve the performance.

### Changes

- EPLB support for Qwen3-moe model. [#2000](https://github.com/vllm-project/vllm-ascend/pull/2000)
- Fix the bug that MTP doesn't work well with Prefill Decode Disaggregation. [#2610](https://github.com/vllm-project/vllm-ascend/pull/2610) [#2554](https://github.com/vllm-project/vllm-ascend/pull/2554) [#2531](https://github.com/vllm-project/vllm-ascend/pull/2531)
- Fix few bugs to make sure Prefill Decode Disaggregation works well. [#2538](https://github.com/vllm-project/vllm-ascend/pull/2538) [#2509](https://github.com/vllm-project/vllm-ascend/pull/2509) [#2502](https://github.com/vllm-project/vllm-ascend/pull/2502)
- Fix file not found error with shutil.rmtree in torchair mode. [#2506](https://github.com/vllm-project/vllm-ascend/pull/2506)

### Known Issues

- When running MoE model, Aclgraph mode only work with tensor parallel. DP/EP doesn't work in this release.
- Pipeline parallelism is not supported in this release for V1 engine.
- If you use w4a8 quantization with eager mode, please set `VLLM_ASCEND_MLA_PARALLEL=1` to avoid oom error.
- Accuracy test with some tools may not be correct. It doesn't affect the real user case. We'll fix it in the next post release. [#2654](https://github.com/vllm-project/vllm-ascend/pull/2654)
- We notice that there are still some problems when running vLLM Ascend with Prefill Decode Disaggregation. For example, the memory may be leaked and the service may be stuck. It's caused by known issue by vLLM and vLLM Ascend. We'll fix it in the next post release. [#2650](https://github.com/vllm-project/vllm-ascend/issues/2650) [#2604](https://github.com/vllm-project/vllm-ascend/issues/2604) [vLLM#22736](https://github.com/vllm-project/vllm/issues/22736) [vLLM#23554](https://github.com/vllm-project/vllm/issues/23554) [vLLM#23981](https://github.com/vllm-project/vllm/issues/23981)

## v0.9.1rc3 - 2025.08.22

This is the 3rd release candidate of v0.9.1 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.9.1/) to get started.

### Core

- MTP supports V1 scheduler [#2371](https://github.com/vllm-project/vllm-ascend/pull/2371)
- Add LMhead TP communication groups [#1956](https://github.com/vllm-project/vllm-ascend/pull/1956)
- Fix the bug that qwen3 moe doesn't work with aclgraph [#2478](https://github.com/vllm-project/vllm-ascend/pull/2478)
- Fix `grammar_bitmask` IndexError caused by outdated `apply_grammar_bitmask` method [#2314](https://github.com/vllm-project/vllm-ascend/pull/2314)
- Remove `chunked_prefill_for_mla` [#2177](https://github.com/vllm-project/vllm-ascend/pull/2177)
- Fix bugs and refactor cached mask generation logic [#2326](https://github.com/vllm-project/vllm-ascend/pull/2326)
- Fix configuration check logic about ascend scheduler [#2327](https://github.com/vllm-project/vllm-ascend/pull/2327)
- Cancel the verification between deepseek-mtp and non-ascend scheduler in disaggregated-prefill deployment [#2368](https://github.com/vllm-project/vllm-ascend/pull/2368)
- Fix issue that failed with ray distributed backend [#2306](https://github.com/vllm-project/vllm-ascend/pull/2306)
- Fix incorrect req block length in ascend scheduler [#2394](https://github.com/vllm-project/vllm-ascend/pull/2394)
- Fix header include issue in rope [#2398](https://github.com/vllm-project/vllm-ascend/pull/2398)
- Fix mtp config bug [#2412](https://github.com/vllm-project/vllm-ascend/pull/2412)
- Fix error info and adapt `attn_metadata` refactor [#2402](https://github.com/vllm-project/vllm-ascend/pull/2402)
- Fix torchair runtime error caused by configuration mismatches and `.kv_cache_bytes` file missing [#2312](https://github.com/vllm-project/vllm-ascend/pull/2312)
- Move `with_prefill` allreduce from cpu to npu [#2230](https://github.com/vllm-project/vllm-ascend/pull/2230)

### Docs

- Add document for deepseek large EP [#2339](https://github.com/vllm-project/vllm-ascend/pull/2339)

### Known Issues

- `test_aclgraph.py` failed with `"full_cuda_graph": True` on A2 (910B1) [#2182](https://github.com/vllm-project/vllm-ascend/issues/2182)

## v0.10.0rc1 - 2025.08.07

This is the 1st release candidate of v0.10.0 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.10.0rc1) to get started. V0 is completely removed from this version.

### Highlights

- Disaggregate prefill works with V1 engine now. You can take a try with DeepSeek model [#950](https://github.com/vllm-project/vllm-ascend/pull/950), following this [tutorial](https://github.com/vllm-project/vllm-ascend/blob/v0.10.0rc1/examples/disaggregated_prefill_v1/README.md).
- W4A8 quantization method is supported for dense and MoE model now. [#2060](https://github.com/vllm-project/vllm-ascend/pull/2060) [#2172](https://github.com/vllm-project/vllm-ascend/pull/2172)

### Core

- Ascend PyTorch adapter (torch_npu) has been upgraded to `2.7.1.dev20250724`. [#1562](https://github.com/vllm-project/vllm-ascend/pull/1562) And CANN has been upgraded to `8.2.RC1`. [#1653](https://github.com/vllm-project/vllm-ascend/pull/1653) Don't forget to update them in your environment or using the latest images.
- vLLM Ascend works on Atlas 800I A3 now, and the image on A3 will be released from this version on. [#1582](https://github.com/vllm-project/vllm-ascend/pull/1582)
- Kimi-K2 with w8a8 quantization, Qwen3-Coder and GLM-4.5 is supported in vLLM Ascend, please following this [tutorial](https://github.com/vllm-project/vllm-ascend/blob/v0.10.0rc1/docs/source/tutorials/multi_node_kimi.md) to have a try. [#2162](https://github.com/vllm-project/vllm-ascend/pull/2162)
- Pipeline Parallelism is supported in V1 now. [#1800](https://github.com/vllm-project/vllm-ascend/pull/1800)
- Prefix cache feature now work with the Ascend Scheduler. [#1446](https://github.com/vllm-project/vllm-ascend/pull/1446)
- Torchair graph mode works with tp > 4 now. [#1508](https://github.com/vllm-project/vllm-ascend/pull/1508)
- MTP support torchair graph mode now [#2145](https://github.com/vllm-project/vllm-ascend/pull/2145)

### Others

- Bug fixes:
    - Fix functional problem of multimodality models like Qwen2-audio with Aclgraph. [#1803](https://github.com/vllm-project/vllm-ascend/pull/1803)
    - Fix the process group creating error with external launch scenario. [#1681](https://github.com/vllm-project/vllm-ascend/pull/1681)
    - Fix the functional problem with guided decoding. [#2022](https://github.com/vllm-project/vllm-ascend/pull/2022)
    - Fix the accuracy issue with common MoE models in DP scenario. [#1856](https://github.com/vllm-project/vllm-ascend/pull/1856)
- Performance improved through a lot of prs:
    - Caching sin/cos instead of calculate it every layer. [#1890](https://github.com/vllm-project/vllm-ascend/pull/1890)
    - Improve shared expert multi-stream parallelism [#1891](https://github.com/vllm-project/vllm-ascend/pull/1891)
    - Implement the fusion of allreduce and matmul in prefill phase when tp is enabled. Enable this feature by setting `VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE` to `1`. [#1926](https://github.com/vllm-project/vllm-ascend/pull/1926)
    - Optimize Quantized MoE Performance by Reducing All2All Communication. [#2195](https://github.com/vllm-project/vllm-ascend/pull/2195)
    - Use AddRmsNormQuant ops in the custom model to optimize Qwen3's performance [#1806](https://github.com/vllm-project/vllm-ascend/pull/1806)
    - Use multicast to avoid padding decode request to prefill size [#1555](https://github.com/vllm-project/vllm-ascend/pull/1555)
    - The performance of LoRA has been improved. [#1884](https://github.com/vllm-project/vllm-ascend/pull/1884)
- A batch of refactoring prs to enhance the code architecture:
    - Torchair model runner refactor [#2205](https://github.com/vllm-project/vllm-ascend/pull/2205)
    - Refactoring forward_context and model_runner_v1. [#1979](https://github.com/vllm-project/vllm-ascend/pull/1979)
    - Refactor AscendMetaData Comments. [#1967](https://github.com/vllm-project/vllm-ascend/pull/1967)
    - Refactor torchair utils. [#1892](https://github.com/vllm-project/vllm-ascend/pull/1892)
    - Refactor torchair worker. [#1885](https://github.com/vllm-project/vllm-ascend/pull/1885)
    - Register activation customop instead of overwrite forward_oot. [#1841](https://github.com/vllm-project/vllm-ascend/pull/1841)
- Parameters changes:
    - `expert_tensor_parallel_size` in `additional_config` is removed now, and the EP and TP is aligned with vLLM now. [#1681](https://github.com/vllm-project/vllm-ascend/pull/1681)
    - Add `VLLM_ASCEND_MLA_PA` in environ variables, use this to enable mla paged attention operator for deepseek mla decode.
    - Add `VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE` in environ variables, enable `MatmulAllReduce` fusion kernel when tensor parallel is enabled. This feature is supported in A2, and eager mode will get better performance.
    - Add `VLLM_ASCEND_ENABLE_MOE_ALL2ALL_SEQ` in environ variables, Whether to enable moe all2all seq, this provides a basic framework on the basis of alltoall for easy expansion.

- UT coverage reached 76.34% after a batch of prs followed by this rfc: [#1298](https://github.com/vllm-project/vllm-ascend/issues/1298)
- Sequence Parallelism works for Qwen3 MoE. [#2209](https://github.com/vllm-project/vllm-ascend/pull/2209)
- Chinese online document is added now. [#1870](https://github.com/vllm-project/vllm-ascend/pull/1870)

### Known Issues

- Aclgraph could not work with DP + EP currently, the mainly gap is the number of npu stream that Aclgraph needed to capture graph is not enough. [#2229](https://github.com/vllm-project/vllm-ascend/issues/2229)
- There is an accuracy issue on W8A8 dynamic quantized DeepSeek with multistream enabled. This will be fixed in the next release. [#2232](https://github.com/vllm-project/vllm-ascend/issues/2232)
- In Qwen3 MoE, SP cannot be incorporated into the Aclgraph. [#2246](https://github.com/vllm-project/vllm-ascend/issues/2246)
- MTP not support V1 scheduler currently, will fix it in Q3. [#2254](https://github.com/vllm-project/vllm-ascend/issues/2254)
- When running MTP with DP > 1, we need to disable metrics logger due to some issue on vLLM. [#2254](https://github.com/vllm-project/vllm-ascend/issues/2254)

## v0.9.1rc2 - 2025.08.04

This is the 2nd release candidate of v0.9.1 for vLLM Ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.9.1/) to get started.

### Highlights

- MOE and dense w4a8 quantization support now: [#1320](https://github.com/vllm-project/vllm-ascend/pull/1320) [#1910](https://github.com/vllm-project/vllm-ascend/pull/1910) [#1275](https://github.com/vllm-project/vllm-ascend/pull/1275) [#1480](https://github.com/vllm-project/vllm-ascend/pull/1480)
- Dynamic EPLB support in [#1943](https://github.com/vllm-project/vllm-ascend/pull/1943)
- Disaggregated Prefilling support for V1 Engine and improvement, continued development and stabilization of the disaggregated prefill feature, including performance enhancements and bug fixes for single-machine setups:[#1953](https://github.com/vllm-project/vllm-ascend/pull/1953) [#1612](https://github.com/vllm-project/vllm-ascend/pull/1612) [#1361](https://github.com/vllm-project/vllm-ascend/pull/1361) [#1746](https://github.com/vllm-project/vllm-ascend/pull/1746) [#1552](https://github.com/vllm-project/vllm-ascend/pull/1552) [#1801](https://github.com/vllm-project/vllm-ascend/pull/1801) [#2083](https://github.com/vllm-project/vllm-ascend/pull/2083) [#1989](https://github.com/vllm-project/vllm-ascend/pull/1989)

### Model Improvement

- DeepSeek DeepSeek DBO support and improvement: [#1285](https://github.com/vllm-project/vllm-ascend/pull/1285) [#1291](https://github.com/vllm-project/vllm-ascend/pull/1291) [#1328](https://github.com/vllm-project/vllm-ascend/pull/1328) [#1420](https://github.com/vllm-project/vllm-ascend/pull/1420) [#1445](https://github.com/vllm-project/vllm-ascend/pull/1445) [#1589](https://github.com/vllm-project/vllm-ascend/pull/1589) [#1759](https://github.com/vllm-project/vllm-ascend/pull/1759) [#1827](https://github.com/vllm-project/vllm-ascend/pull/1827) [#2093](https://github.com/vllm-project/vllm-ascend/pull/2093)
- DeepSeek MTP improvement and bugfix: [#1214](https://github.com/vllm-project/vllm-ascend/pull/1214) [#943](https://github.com/vllm-project/vllm-ascend/pull/943) [#1584](https://github.com/vllm-project/vllm-ascend/pull/1584) [#1473](https://github.com/vllm-project/vllm-ascend/pull/1473) [#1294](https://github.com/vllm-project/vllm-ascend/pull/1294) [#1632](https://github.com/vllm-project/vllm-ascend/pull/1632) [#1694](https://github.com/vllm-project/vllm-ascend/pull/1694) [#1840](https://github.com/vllm-project/vllm-ascend/pull/1840) [#2076](https://github.com/vllm-project/vllm-ascend/pull/2076) [#1990](https://github.com/vllm-project/vllm-ascend/pull/1990) [#2019](https://github.com/vllm-project/vllm-ascend/pull/2019)
- Qwen3 MoE support improvement and bugfix around graph mode and DP:  [#1940](https://github.com/vllm-project/vllm-ascend/pull/1940) [#2006](https://github.com/vllm-project/vllm-ascend/pull/2006) [#1832](https://github.com/vllm-project/vllm-ascend/pull/1832)
- Qwen3 performance improvement around rmsnorm/rope/mlp ops: [#1545](https://github.com/vllm-project/vllm-ascend/pull/1545) [#1719](https://github.com/vllm-project/vllm-ascend/pull/1719) [#1726](https://github.com/vllm-project/vllm-ascend/pull/1726) [#1782](https://github.com/vllm-project/vllm-ascend/pull/1782) [#1745](https://github.com/vllm-project/vllm-ascend/pull/1745)
- DeepSeek MLA chunked prefill/graph mode/multistream improvement and bugfix: [#1240](https://github.com/vllm-project/vllm-ascend/pull/1240) [#933](https://github.com/vllm-project/vllm-ascend/pull/933) [#1135](https://github.com/vllm-project/vllm-ascend/pull/1135) [#1311](https://github.com/vllm-project/vllm-ascend/pull/1311) [#1750](https://github.com/vllm-project/vllm-ascend/pull/1750) [#1872](https://github.com/vllm-project/vllm-ascend/pull/1872) [#2170](https://github.com/vllm-project/vllm-ascend/pull/2170) [#1551](https://github.com/vllm-project/vllm-ascend/pull/1551)
- Qwen2.5 VL improvement via mrope/padding mechanism improvement: [#1261](https://github.com/vllm-project/vllm-ascend/pull/1261) [#1705](https://github.com/vllm-project/vllm-ascend/pull/1705) [#1929](https://github.com/vllm-project/vllm-ascend/pull/1929) [#2007](https://github.com/vllm-project/vllm-ascend/pull/2007)
- Ray: Fix the device error when using ray and add initialize_cache and improve warning info: [#1234](https://github.com/vllm-project/vllm-ascend/pull/1234) [#1501](https://github.com/vllm-project/vllm-ascend/pull/1501)

### Graph Mode Improvement

- Fix DeepSeek with deepseek with mc2 in [#1269](https://github.com/vllm-project/vllm-ascend/pull/1269)
- Fix accuracy problem for deepseek V3/R1 models with torchair graph in long sequence predictions in [#1332](https://github.com/vllm-project/vllm-ascend/pull/1332)
- Fix torchair_graph_batch_sizes bug in [#1570](https://github.com/vllm-project/vllm-ascend/pull/1570)
- Enable the limit of tp <= 4 for torchair graph mode in [#1404](https://github.com/vllm-project/vllm-ascend/pull/1404)
- Fix rope accuracy bug [#1887](https://github.com/vllm-project/vllm-ascend/pull/1887)
- Support multistream of shared experts in FusedMoE [#997](https://github.com/vllm-project/vllm-ascend/pull/997)
- Enable kvcache_nz for the decode process in torchair graph mode[#1098](https://github.com/vllm-project/vllm-ascend/pull/1098)
- Fix chunked-prefill with torchair case to resolve UnboundLocalError: local variable 'decode_hs_or_q_c' issue in [#1378](https://github.com/vllm-project/vllm-ascend/pull/1378)
- Improve shared experts multi-stream perf for w8a8 dynamic. in [#1561](https://github.com/vllm-project/vllm-ascend/pull/1561)
- Repair moe error when set multistream. in [#1882](https://github.com/vllm-project/vllm-ascend/pull/1882)
- Round up graph batch size to tp size in EP case [#1610](https://github.com/vllm-project/vllm-ascend/pull/1610)
- Fix torchair bug when DP is enabled in [#1727](https://github.com/vllm-project/vllm-ascend/pull/1727)
- Add extra checking to torchair_graph_config. in [#1675](https://github.com/vllm-project/vllm-ascend/pull/1675)
- Fix rope bug in torchair+chunk-prefill scenario in [#1693](https://github.com/vllm-project/vllm-ascend/pull/1693)
- torchair_graph bugfix when chunked_prefill is true in [#1748](https://github.com/vllm-project/vllm-ascend/pull/1748)
- Improve prefill optimization to support torchair graph mode in [#2090](https://github.com/vllm-project/vllm-ascend/pull/2090)
- Fix rank set in DP scenario [#1247](https://github.com/vllm-project/vllm-ascend/pull/1247)
- Reset all unused positions to prevent out-of-bounds to resolve GatherV3 bug in [#1397](https://github.com/vllm-project/vllm-ascend/pull/1397)
- Remove duplicate multimodal codes in ModelRunner in [#1393](https://github.com/vllm-project/vllm-ascend/pull/1393)
- Fix block table shape to resolve accuracy issue in [#1297](https://github.com/vllm-project/vllm-ascend/pull/1297)
- Implement primal full graph with limited scenario in [#1503](https://github.com/vllm-project/vllm-ascend/pull/1503)
- Restore paged attention kernel in Full Graph for performance in [#1677](https://github.com/vllm-project/vllm-ascend/pull/1677)
- Fix DeepSeek OOM issue in extreme `--gpu-memory-utilization` scenario in [#1829](https://github.com/vllm-project/vllm-ascend/pull/1829)
- Turn off aclgraph when enabling TorchAir in [#2154](https://github.com/vllm-project/vllm-ascend/pull/2154)

### Operator Improvement

- Added custom AscendC kernel `vocabparallelembedding` [#796](https://github.com/vllm-project/vllm-ascend/pull/796)
- Fixed rope sin/cos cache bug in [#1267](https://github.com/vllm-project/vllm-ascend/pull/1267)
- Refactored AscendFusedMoE (#1229) in [#1264](https://github.com/vllm-project/vllm-ascend/pull/1264)
- Used fused ops npu_top_k_top_p in sampler [#1920](https://github.com/vllm-project/vllm-ascend/pull/1920)

### Core

- Upgraded CANN to 8.2.rc1 in [#2036](https://github.com/vllm-project/vllm-ascend/pull/2036)
- Upgraded TorchNPU to 2.5.1.post1 in [#2135](https://github.com/vllm-project/vllm-ascend/pull/2135)
- Upgraded python to 3.11 in [#2136](https://github.com/vllm-project/vllm-ascend/pull/2136)
- Disabled quantization in mindie_turbo  in [#1749](https://github.com/vllm-project/vllm-ascend/pull/1749)
- Fixed v0 spec decode in [#1323](https://github.com/vllm-project/vllm-ascend/pull/1323)
- Enabled `ACL_OP_INIT_MODE=1` directly only when using V0 spec decode in [#1271](https://github.com/vllm-project/vllm-ascend/pull/1271)
- Refactoring forward_context and model_runner_v1 in [#1422](https://github.com/vllm-project/vllm-ascend/pull/1422)
- Fixed sampling params in [#1423](https://github.com/vllm-project/vllm-ascend/pull/1423)
- Added a switch for enabling NZ layout in weights and enable NZ for GMM. in [#1409](https://github.com/vllm-project/vllm-ascend/pull/1409)
- Resolved bug in ascend_forward_context in [#1449](https://github.com/vllm-project/vllm-ascend/pull/1449) [#1554](https://github.com/vllm-project/vllm-ascend/pull/1554) [#1598](https://github.com/vllm-project/vllm-ascend/pull/1598)
- Address PrefillCacheHit state to fix prefix cache accuracy bug in [#1492](https://github.com/vllm-project/vllm-ascend/pull/1492)
- Fixed load weight error and add new e2e case in [#1651](https://github.com/vllm-project/vllm-ascend/pull/1651)
- Optimized the number of rope-related index selections in deepseek. in [#1614](https://github.com/vllm-project/vllm-ascend/pull/1614)
- Added mc2 mask in [#1642](https://github.com/vllm-project/vllm-ascend/pull/1642)
- Fixed static EPLB log2phy condition and improve unit test in [#1667](https://github.com/vllm-project/vllm-ascend/pull/1667) [#1896](https://github.com/vllm-project/vllm-ascend/pull/1896) [#2003](https://github.com/vllm-project/vllm-ascend/pull/2003)
- Added chunk mc2 for prefill in [#1703](https://github.com/vllm-project/vllm-ascend/pull/1703)
- Fixed mc2 op GroupCoordinator bug in [#1711](https://github.com/vllm-project/vllm-ascend/pull/1711)
- Fixed the failure to recognize the actual type of quantization in [#1721](https://github.com/vllm-project/vllm-ascend/pull/1721)
- Fixed DeepSeek bug when tp_size == 1  in [#1755](https://github.com/vllm-project/vllm-ascend/pull/1755)
- Added support for delay-free blocks in prefill nodes in [#1691](https://github.com/vllm-project/vllm-ascend/pull/1691)
- MoE alltoallv communication optimization for unquantized RL training & alltoallv support dpo in [#1547](https://github.com/vllm-project/vllm-ascend/pull/1547)
- Adapted dispatchV2 interface in [#1822](https://github.com/vllm-project/vllm-ascend/pull/1822)
- Fixed disaggregate prefill hang issue in long output in [#1807](https://github.com/vllm-project/vllm-ascend/pull/1807)
- Fixed flashcomm_v1 when engine v0 in [#1859](https://github.com/vllm-project/vllm-ascend/pull/1859)
- ep_group is not equal to word_size in some cases in [#1862](https://github.com/vllm-project/vllm-ascend/pull/1862).
- Fixed wheel glibc version incompatibility in [#1808](https://github.com/vllm-project/vllm-ascend/pull/1808).
- Fixed mc2 process group to resolve self.cpu_group is None in [#1831](https://github.com/vllm-project/vllm-ascend/pull/1831).
- Pin vllm version to v0.9.1 to make mypy check passed  in [#1904](https://github.com/vllm-project/vllm-ascend/pull/1904).
- Applied npu_moe_gating_top_k_softmax for moe to improve perf in [#1902](https://github.com/vllm-project/vllm-ascend/pull/1902).
- Fixed bug in path_decorator when engine v0 in [#1919](https://github.com/vllm-project/vllm-ascend/pull/1919).
- Avoid performing cpu all_reduce in disaggregated-prefill scenario in [#1644](https://github.com/vllm-project/vllm-ascend/pull/1644).
- Added super kernel in decode MoE in [#1916](https://github.com/vllm-project/vllm-ascend/pull/1916)
- [Prefill Perf] Parallel Strategy Optimizations (VRAM-for-Speed Tradeoff) in [#1802](https://github.com/vllm-project/vllm-ascend/pull/1802).
- Removed unnecessary reduce_results access in shared_experts.down_proj in [#2016](https://github.com/vllm-project/vllm-ascend/pull/2016).
- Optimized greedy reject sampler with vectorization in [#2002](https://github.com/vllm-project/vllm-ascend/pull/2002).
- Made multiple Ps and Ds work on a single machine in [#1936](https://github.com/vllm-project/vllm-ascend/pull/1936).
- Fixed the shape conflicts between shared & routed experts for deepseek model when tp > 1 and multistream_moe enabled in [#2075](https://github.com/vllm-project/vllm-ascend/pull/2075).
- Added CPU binding support [#2031](https://github.com/vllm-project/vllm-ascend/pull/2031).
- Added with_prefill cpu allreduce to handle D-node recomputation in [#2129](https://github.com/vllm-project/vllm-ascend/pull/2129).
- Added D2H & initRoutingQuantV2 to improve prefill perf in [#2038](https://github.com/vllm-project/vllm-ascend/pull/2038).

### Docs

- Provide an e2e guide for execute duration profiling [#1113](https://github.com/vllm-project/vllm-ascend/pull/1113)
- Add Referer header for CANN package download url. [#1192](https://github.com/vllm-project/vllm-ascend/pull/1192)
- Add reinstall instructions doc [#1370](https://github.com/vllm-project/vllm-ascend/pull/1370)
- Update Disaggregate prefill README [#1379](https://github.com/vllm-project/vllm-ascend/pull/1379)
- Disaggregate prefill for kv cache register style  [#1296](https://github.com/vllm-project/vllm-ascend/pull/1296)
- Fix errors and non-standard parts in examples/disaggregate_prefill_v1/README.md in [#1965](https://github.com/vllm-project/vllm-ascend/pull/1965)

### Known Issues

- Full graph mode support are not yet available for specific hardware types with full_cuda_graphenable. [#2182](https://github.com/vllm-project/vllm-ascend/issues/2182)
- Qwen3 MoE aclgraph mode with tp failed when enable ep due to bincount error [#2226](https://github.com/vllm-project/vllm-ascend/issues/2226)
- As mentioned in the v0.9.1rc1 release note, Atlas 300I series support will NOT be included.

## v0.9.2rc1 - 2025.07.11

This is the 1st release candidate of v0.9.2 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.9.2rc1) to get started. From this release, V1 engine will be enabled by default, there is no need to set `VLLM_USE_V1=1` any more. And this release is the last version to support V0 engine, V0 code will be cleaned up in the future.

### Highlights

- Pooling model works with V1 engine now. You can take a try with Qwen3 embedding model [#1359](https://github.com/vllm-project/vllm-ascend/pull/1359).
- The performance on Atlas 300I series has been improved. [#1591](https://github.com/vllm-project/vllm-ascend/pull/1591)
- aclgraph mode works with Moe models now. Currently, only Qwen3 Moe is well tested. [#1381](https://github.com/vllm-project/vllm-ascend/pull/1381)

### Core

- Ascend PyTorch adapter (torch_npu) has been upgraded to `2.5.1.post1.dev20250619`. Don't forget to update it in your environment. [#1347](https://github.com/vllm-project/vllm-ascend/pull/1347)
- The GatherV3 error has been fixed with aclgraph mode. [#1416](https://github.com/vllm-project/vllm-ascend/pull/1416)
- W8A8 quantization works on Atlas 300I series now. [#1560](https://github.com/vllm-project/vllm-ascend/pull/1560)
- Fix the accuracy problem with deploy models with parallel parameters. [#1678](https://github.com/vllm-project/vllm-ascend/pull/1678)
- The pre-built wheel package now requires lower version of glibc. Users can use it by `pip install vllm-ascend` directly. [#1582](https://github.com/vllm-project/vllm-ascend/pull/1582)

### Others

- Official doc has been updated for better read experience. For example, more deployment tutorials are added, user/developer docs are updated. More guide will coming soon.
- Fix accuracy problem for Deepseek V3/R1 models with torchair graph in long sequence predictions. [#1331](https://github.com/vllm-project/vllm-ascend/pull/1331)
- A new env variable `VLLM_ENABLE_FUSED_EXPERTS_ALLGATHER_EP` has been added. It enables the fused allgather-experts kernel for Deepseek V3/R1 models. The default value is `0`. [#1335](https://github.com/vllm-project/vllm-ascend/pull/1335)
- A new env variable `VLLM_ASCEND_ENABLE_TOPK_TOPP_OPTIMIZATION` has been added to improve the performance of topk-topp sampling. The default value is 0, we'll consider enabling it by default in the future[#1732](https://github.com/vllm-project/vllm-ascend/pull/1732)
- A batch of bugs have been fixed for Data Parallelism case [#1273](https://github.com/vllm-project/vllm-ascend/pull/1273) [#1322](https://github.com/vllm-project/vllm-ascend/pull/1322) [#1275](https://github.com/vllm-project/vllm-ascend/pull/1275) [#1478](https://github.com/vllm-project/vllm-ascend/pull/1478)
- The DeepSeek performance has been improved. [#1194](https://github.com/vllm-project/vllm-ascend/pull/1194) [#1395](https://github.com/vllm-project/vllm-ascend/pull/1395) [#1380](https://github.com/vllm-project/vllm-ascend/pull/1380)
- Ascend scheduler works with prefix cache now. [#1446](https://github.com/vllm-project/vllm-ascend/pull/1446)
- DeepSeek now works with prefix cache now. [#1498](https://github.com/vllm-project/vllm-ascend/pull/1498)
- Support prompt logprobs to recover ceval accuracy in V1 [#1483](https://github.com/vllm-project/vllm-ascend/pull/1483)

### Known Issues

- Pipeline parallel does not work with ray and graph mode: <https://github.com/vllm-project/vllm-ascend/issues/1751> <https://github.com/vllm-project/vllm-ascend/issues/1754>

### New Contributors

- @xleoken made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1357>
- @lyj-jjj made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1335>
- @sharonyunyun made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1194>
- @Pr0Wh1teGivee made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1308>
- @leo-pony made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1374>
- @zeshengzong made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1452>
- @GDzhu01 made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1477>
- @Agonixiaoxiao made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1531>
- @zhanghw0354 made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1476>
- @farawayboat made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1591>
- @ZhengWG made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1196>
- @wm901115nwpu made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1654>

**Full Changelog**: <https://github.com/vllm-project/vllm-ascend/compare/v0.9.1rc1...v0.9.2rc1>

## v0.9.1rc1 - 2025.06.22

This is the 1st release candidate of v0.9.1 for vLLM Ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.9.1rc1) to get started.

### Experimental

- Atlas 300I series is experimental supported in this release (Functional test passed with Qwen2.5-7b-instruct/Qwen2.5-0.5b/Qwen3-0.6B/Qwen3-4B/Qwen3-8B). [#1333](https://github.com/vllm-project/vllm-ascend/pull/1333)
- Support EAGLE-3 for speculative decoding. [#1032](https://github.com/vllm-project/vllm-ascend/pull/1032)

After careful consideration, above features **will NOT be included in v0.9.1-dev branch (v0.9.1 final release)** taking into account the v0.9.1 release quality and the feature rapid iteration. We will improve this from 0.9.2rc1 and later.

### Core

- Ascend PyTorch adapter (torch_npu) has been upgraded to `2.5.1.post1.dev20250528`. Don't forget to update it in your environment. [#1235](https://github.com/vllm-project/vllm-ascend/pull/1235)
- Support Atlas 300I series container image. You can get it from [quay.io](https://quay.io/repository/vllm/vllm-ascend)
- Fix token-wise padding mechanism to make multi-card graph mode work. [#1300](https://github.com/vllm-project/vllm-ascend/pull/1300)
- Upgrade vLLM to 0.9.1 [#1165](https://github.com/vllm-project/vllm-ascend/pull/1165)

### Other Improvements

- Initial support Chunked Prefill for MLA. [#1172](https://github.com/vllm-project/vllm-ascend/pull/1172)
- An example of best practices to run DeepSeek with ETP has been added. [#1101](https://github.com/vllm-project/vllm-ascend/pull/1101)
- Performance improvements for DeepSeek using the TorchAir graph. [#1098](https://github.com/vllm-project/vllm-ascend/pull/1098), [#1131](https://github.com/vllm-project/vllm-ascend/pull/1131)
- Supports the speculative decoding feature with AscendScheduler. [#943](https://github.com/vllm-project/vllm-ascend/pull/943)
- Improve `VocabParallelEmbedding` custom op performance. It will be enabled in the next release. [#796](https://github.com/vllm-project/vllm-ascend/pull/796)
- Fixed a device discovery and setup bug when running vLLM Ascend on Ray [#884](https://github.com/vllm-project/vllm-ascend/pull/884)
- DeepSeek with [MC2](https://www.hiascend.com/document/detail/zh/canncommercial/81RC1/developmentguide/opdevg/ascendcbestP/atlas_ascendc_best_practices_10_0043.html) (Merged Compute and Communication) now works properly. [#1268](https://github.com/vllm-project/vllm-ascend/pull/1268)
- Fixed log2phy NoneType bug with static EPLB feature. [#1186](https://github.com/vllm-project/vllm-ascend/pull/1186)
- Improved performance for DeepSeek with DBO enabled. [#997](https://github.com/vllm-project/vllm-ascend/pull/997), [#1135](https://github.com/vllm-project/vllm-ascend/pull/1135)
- Refactoring AscendFusedMoE [#1229](https://github.com/vllm-project/vllm-ascend/pull/1229)
- Add initial user stories page (include LLaMA-Factory/TRL/verl/MindIE Turbo/GPUStack) [#1224](https://github.com/vllm-project/vllm-ascend/pull/1224)
- Add unit test framework [#1201](https://github.com/vllm-project/vllm-ascend/pull/1201)

### Known Issues

- In some cases, the vLLM process may crash with a **GatherV3** error when **aclgraph** is enabled. We are working on this issue and will fix it in the next release. [#1038](https://github.com/vllm-project/vllm-ascend/issues/1038)
- Prefix cache feature does not work with the Ascend Scheduler but without chunked prefill enabled. This will be fixed in the next release. [#1350](https://github.com/vllm-project/vllm-ascend/issues/1350)

### Full Changelog

<https://github.com/vllm-project/vllm-ascend/compare/v0.9.0rc2...v0.9.1rc1>

### New Contributors

- @farawayboat made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1333>
- @yzim made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1159>
- @chenwaner made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1098>
- @wangyanhui-cmss made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1184>
- @songshanhu07 made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1186>
- @yuancaoyaoHW made their first contribution in <https://github.com/vllm-project/vllm-ascend/pull/1032>

**Full Changelog**: <https://github.com/vllm-project/vllm-ascend/compare/v0.9.0rc2...v0.9.1rc1>

## v0.9.0rc2 - 2025.06.10

This release contains some quick fixes for v0.9.0rc1. Please use this release instead of v0.9.0rc1.

### Highlights

- Fix the import error when vllm-ascend is installed without editable way. [#1152](https://github.com/vllm-project/vllm-ascend/pull/1152)

## v0.9.0rc1 - 2025.06.09

This is the 1st release candidate of v0.9.0 for vllm-ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.9.0rc1) to start the journey. From this release, V1 Engine is recommended to use. The code of V0 Engine is frozen and will not be maintained any more. Please set environment `VLLM_USE_V1=1` to enable V1 Engine.

### Highlights

- DeepSeek works with graph mode now. Follow the [official doc](https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/graph_mode.html) to take a try. [#789](https://github.com/vllm-project/vllm-ascend/pull/789)
- Qwen series models work with graph mode now. It works by default with V1 Engine. Please note that in this release, only Qwen series models are well tested with graph mode. We'll make it stable and generalize in the next release. If you hit any issues, please feel free to open an issue on GitHub and fallback to eager mode temporarily by set `enforce_eager=True` when initializing the model.

### Core

- The performance of multi-step scheduler has been improved. Thanks for the contribution from China Merchants Bank. [#814](https://github.com/vllm-project/vllm-ascend/pull/814)
- LoRA,Multi-LoRA and Dynamic Serving are supported for V1 Engine now. Thanks for the contribution from China Merchants Bank. [#893](https://github.com/vllm-project/vllm-ascend/pull/893)
- Prefix cache and chunked prefill feature works now [#782](https://github.com/vllm-project/vllm-ascend/pull/782) [#844](https://github.com/vllm-project/vllm-ascend/pull/844)
- Spec decode and MTP features work with V1 Engine now. [#874](https://github.com/vllm-project/vllm-ascend/pull/874) [#890](https://github.com/vllm-project/vllm-ascend/pull/890)
- DP feature works with DeepSeek now. [#1012](https://github.com/vllm-project/vllm-ascend/pull/1012)
- Input embedding feature works with V0 Engine now. [#916](https://github.com/vllm-project/vllm-ascend/pull/916)
- Sleep mode feature works with V1 Engine now. [#1084](https://github.com/vllm-project/vllm-ascend/pull/1084)

### Models

- Qwen2.5 VL works with V1 Engine now. [#736](https://github.com/vllm-project/vllm-ascend/pull/736)
- Llama4 works now. [#740](https://github.com/vllm-project/vllm-ascend/pull/740)
- A new kind of DeepSeek model called dual-batch overlap(DBO) is added. Please set `VLLM_ASCEND_ENABLE_DBO=1` to use it. [#941](https://github.com/vllm-project/vllm-ascend/pull/941)

### Others

- online serve with ascend quantization works now. [#877](https://github.com/vllm-project/vllm-ascend/pull/877)
- A batch of bugs for graph mode and moe model have been fixed. [#773](https://github.com/vllm-project/vllm-ascend/pull/773) [#771](https://github.com/vllm-project/vllm-ascend/pull/771) [#774](https://github.com/vllm-project/vllm-ascend/pull/774) [#816](https://github.com/vllm-project/vllm-ascend/pull/816) [#817](https://github.com/vllm-project/vllm-ascend/pull/817) [#819](https://github.com/vllm-project/vllm-ascend/pull/819) [#912](https://github.com/vllm-project/vllm-ascend/pull/912) [#897](https://github.com/vllm-project/vllm-ascend/pull/897) [#961](https://github.com/vllm-project/vllm-ascend/pull/961) [#958](https://github.com/vllm-project/vllm-ascend/pull/958) [#913](https://github.com/vllm-project/vllm-ascend/pull/913) [#905](https://github.com/vllm-project/vllm-ascend/pull/905)
- A batch of performance improvement PRs have been merged. [#784](https://github.com/vllm-project/vllm-ascend/pull/784) [#803](https://github.com/vllm-project/vllm-ascend/pull/803) [#966](https://github.com/vllm-project/vllm-ascend/pull/966) [#839](https://github.com/vllm-project/vllm-ascend/pull/839) [#970](https://github.com/vllm-project/vllm-ascend/pull/970) [#947](https://github.com/vllm-project/vllm-ascend/pull/947) [#987](https://github.com/vllm-project/vllm-ascend/pull/987) [#1085](https://github.com/vllm-project/vllm-ascend/pull/1085)
- From this release, binary wheel package will be released as well. [#775](https://github.com/vllm-project/vllm-ascend/pull/775)
- The contributor doc site is [added](https://docs.vllm.ai/projects/ascend/en/latest/community/contributors.html)

### Known Issue

- In some case, vLLM process may be crashed with aclgraph enabled. We're working this issue and it'll be fixed in the next release.
- Multi node data-parallel doesn't work with this release. This is a known issue in vllm and has been fixed on main branch. [#18981](https://github.com/vllm-project/vllm/pull/18981)

## v0.7.3.post1 - 2025.05.29

This is the first post release of 0.7.3. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.3) to start the journey. It includes the following changes:

### Highlights

- Qwen3 and Qwen3MOE is supported now. The performance and accuracy of Qwen3 is well tested. You can try it now. Mindie Turbo is recommended to improve the performance of Qwen3. [#903](https://github.com/vllm-project/vllm-ascend/pull/903) [#915](https://github.com/vllm-project/vllm-ascend/pull/915)
- Added a new performance guide. The guide aims to help users to improve vllm-ascend performance on system level. It includes OS configuration, library optimization, deploy guide and so on. [#878](https://github.com/vllm-project/vllm-ascend/pull/878) [Doc Link](https://docs.vllm.ai/projects/ascend/en/v0.7.3/developer_guide/performance/optimization_and_tuning.html)

### Bug Fixes

- Qwen2.5-VL  works for RLHF scenarios now. [#928](https://github.com/vllm-project/vllm-ascend/pull/928)
- Users can launch the model from online weights now. e.g. from huggingface or modelscope directly [#858](https://github.com/vllm-project/vllm-ascend/pull/858) [#918](https://github.com/vllm-project/vllm-ascend/pull/918)
- The meaningless log info `UserWorkspaceSize0` has been cleaned. [#911](https://github.com/vllm-project/vllm-ascend/pull/911)
- The log level for `Failed to import vllm_ascend_C` has been changed to `warning` instead of `error`. [#956](https://github.com/vllm-project/vllm-ascend/pull/956)
- DeepSeek MLA now works with chunked prefill in V1 Engine. Please note that the V1 engine in 0.7.3 is just experimental and for testing only. [#849](https://github.com/vllm-project/vllm-ascend/pull/849) [#936](https://github.com/vllm-project/vllm-ascend/pull/936)

### Docs

- The benchmark doc is updated for Qwen2.5 and Qwen2.5-VL [#792](https://github.com/vllm-project/vllm-ascend/pull/792)
- Add the note to clear that only "modelscope<1.23.0" works with 0.7.3. [#954](https://github.com/vllm-project/vllm-ascend/pull/954)

## v0.7.3 - 2025.05.08

🎉 Hello, World!

We are excited to announce the release of 0.7.3 for vllm-ascend. This is the first official release. The functionality, performance, and stability of this release are fully tested and verified. We encourage you to try it out and provide feedback. We'll post bug fix versions in the future if needed. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.3) to start the journey.

### Highlights

- This release includes all features landed in the previous release candidates ([v0.7.1rc1](https://github.com/vllm-project/vllm-ascend/releases/tag/v0.7.1rc1), [v0.7.3rc1](https://github.com/vllm-project/vllm-ascend/releases/tag/v0.7.3rc1), [v0.7.3rc2](https://github.com/vllm-project/vllm-ascend/releases/tag/v0.7.3rc2)). And all the features are fully tested and verified. Visit the official doc to get the detail [feature](https://docs.vllm.ai/projects/ascend/en/v0.7.3/user_guide/suppoted_features.html) and [model](https://docs.vllm.ai/projects/ascend/en/v0.7.3/user_guide/supported_models.html) support matrix.
- Upgrade CANN to 8.1.RC1 to enable chunked prefill and automatic prefix caching features. You can now enable them now.
- Upgrade PyTorch to 2.5.1. vLLM Ascend no longer relies on the dev version of TorchNPU now. Now users don't need to install the TorchNPU by hand. The 2.5.1 version of TorchNPU will be installed automatically. [#662](https://github.com/vllm-project/vllm-ascend/pull/662)
- Integrate MindIE Turbo into vLLM Ascend to improve DeepSeek V3/R1, Qwen 2 series performance. [#708](https://github.com/vllm-project/vllm-ascend/pull/708)

### Core

- LoRA、Multi-LoRA And Dynamic Serving is supported now. The performance will be improved in the next release. Please follow the official doc for more usage information. Thanks for the contribution from China Merchants Bank. [#700](https://github.com/vllm-project/vllm-ascend/pull/700)

### Models

- The performance of Qwen2 vl and Qwen2.5 vl is improved. [#702](https://github.com/vllm-project/vllm-ascend/pull/702)
- The performance of `apply_penalties` and `topKtopP` ops are improved. [#525](https://github.com/vllm-project/vllm-ascend/pull/525)

### Others

- Fixed a issue that may lead CPU memory leak. [#691](https://github.com/vllm-project/vllm-ascend/pull/691) [#712](https://github.com/vllm-project/vllm-ascend/pull/712)
- A new environment `SOC_VERSION` is added. If you hit any soc detection error when building with custom ops enabled, please set `SOC_VERSION` to a suitable value. [#606](https://github.com/vllm-project/vllm-ascend/pull/606)
- openEuler container image supported with v0.7.3-openeuler tag. [#665](https://github.com/vllm-project/vllm-ascend/pull/665)
- Prefix cache feature works on V1 engine now. [#559](https://github.com/vllm-project/vllm-ascend/pull/559)

## v0.8.5rc1 - 2025.05.06

This is the 1st release candidate of v0.8.5 for vllm-ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.8.5rc1) to start the journey. Now you can enable V1 engine by setting the environment variable `VLLM_USE_V1=1`, see the feature support status of vLLM Ascend in [supported_features](https://github.com/vllm-project/vllm-ascend/blob/v0.8.5rc1/docs/source/user_guide/suppoted_features.md).

### Highlights

- Upgrade CANN version to 8.1.RC1 to support chunked prefill and automatic prefix caching (`--enable_prefix_caching`) when V1 is enabled [#747](https://github.com/vllm-project/vllm-ascend/pull/747)
- Optimize Qwen2 VL and Qwen 2.5 VL [#701](https://github.com/vllm-project/vllm-ascend/pull/701)
- Improve Deepseek V3 eager mode and graph mode performance, now you can use --additional_config={'enable_graph_mode': True} to enable graph mode. [#598](https://github.com/vllm-project/vllm-ascend/pull/598) [#719](https://github.com/vllm-project/vllm-ascend/pull/719)

### Core

- Upgrade vLLM to 0.8.5.post1 [#715](https://github.com/vllm-project/vllm-ascend/pull/715)
- Fix early return in CustomDeepseekV2MoE.forward during profile_run [#682](https://github.com/vllm-project/vllm-ascend/pull/682)
- Adapts for new quant model generated by modelslim [#719](https://github.com/vllm-project/vllm-ascend/pull/719)
- Initial support on P2P Disaggregated Prefill based on llm_datadist [#694](https://github.com/vllm-project/vllm-ascend/pull/694)
- Use `/vllm-workspace` as code path and include `.git` in container image to fix issue when start vllm under `/workspace` [#726](https://github.com/vllm-project/vllm-ascend/pull/726)
- Optimize NPU memory usage to make DeepSeek R1 W8A8 32k model len work. [#728](https://github.com/vllm-project/vllm-ascend/pull/728)
- Fix `PYTHON_INCLUDE_PATH` typo in setup.py [#762](https://github.com/vllm-project/vllm-ascend/pull/762)

### Others

- Add Qwen3-0.6B test [#717](https://github.com/vllm-project/vllm-ascend/pull/717)
- Add nightly CI [#668](https://github.com/vllm-project/vllm-ascend/pull/668)
- Add accuracy test report [#542](https://github.com/vllm-project/vllm-ascend/pull/542)

## v0.8.4rc2 - 2025.04.29

This is the second release candidate of v0.8.4 for vllm-ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.8.4rc2) to start the journey. Some experimental features are included in this version, such as W8A8 quantization and EP/DP support. We'll make them stable enough in the next release.

### Highlights

- Qwen3 and Qwen3MOE is supported now. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/blob/v0.8.4rc2/docs/source/tutorials/single_npu.md) to run the quick demo. [#709](https://github.com/vllm-project/vllm-ascend/pull/709)
- Ascend W8A8 quantization method is supported now. Please take the [official doc](https://github.com/vllm-project/vllm-ascend/blob/v0.8.4rc2/docs/source/tutorials/multi_npu_quantization.md) for example. Any [feedback](https://github.com/vllm-project/vllm-ascend/issues/619) is welcome. [#580](https://github.com/vllm-project/vllm-ascend/pull/580)
- DeepSeek V3/R1 works with DP, TP and MTP now. Please note that it's still in experimental status. Let us know if you hit any problem. [#429](https://github.com/vllm-project/vllm-ascend/pull/429) [#585](https://github.com/vllm-project/vllm-ascend/pull/585)  [#626](https://github.com/vllm-project/vllm-ascend/pull/626) [#636](https://github.com/vllm-project/vllm-ascend/pull/636) [#671](https://github.com/vllm-project/vllm-ascend/pull/671)

### Core

- ACLGraph feature is supported with V1 engine now. It's disabled by default because this feature rely on CANN 8.1 release. We'll make it available by default in the next release [#426](https://github.com/vllm-project/vllm-ascend/pull/426)
- Upgrade PyTorch to 2.5.1. vLLM Ascend no longer relies on the dev version of TorchNPU now. Now users don't need to install the TorchNPU by hand. The 2.5.1 version of TorchNPU will be installed automatically. [#661](https://github.com/vllm-project/vllm-ascend/pull/661)

### Others

- MiniCPM model works now. [#645](https://github.com/vllm-project/vllm-ascend/pull/645)
- openEuler container image supported with `v0.8.4-openeuler` tag and customs Ops build is enabled by default for openEuler OS. [#689](https://github.com/vllm-project/vllm-ascend/pull/689)
- Fix ModuleNotFoundError bug to make Lora work [#600](https://github.com/vllm-project/vllm-ascend/pull/600)
- Add "Using EvalScope evaluation" doc [#611](https://github.com/vllm-project/vllm-ascend/pull/611)
- Add a `VLLM_VERSION` environment to make vLLM version configurable to help developer set correct vLLM version if the code of vLLM is changed by hand locally. [#651](https://github.com/vllm-project/vllm-ascend/pull/651)

## v0.8.4rc1 - 2025.04.18

This is the first release candidate of v0.8.4 for vllm-ascend. Please follow the [official doc](https://github.com/vllm-project/vllm-ascend/tree/v0.8.4rc1) to start the journey. From this version, vllm-ascend will follow the newest version of vllm and release every two weeks. For example, if vllm releases v0.8.5 in the next two weeks, vllm-ascend will release v0.8.5rc1 instead of v0.8.4rc2. Please find the detail from the [official documentation](https://docs.vllm.ai/projects/ascend/en/latest/community/versioning_policy.html#release-window).

### Highlights

- vLLM V1 engine experimental support is included in this version. You can visit [official guide](https://docs.vllm.ai/en/v0.8.4/getting_started/v1_user_guide.html) to get more detail. By default, vLLM will fallback to V0 if V1 doesn't work, please set `VLLM_USE_V1=1` environment if you want to use V1 forcibly.
- LoRA、Multi-LoRA And Dynamic Serving is supported now. The performance will be improved in the next release. Please follow the [official doc](https://docs.vllm.ai/en/v0.8.4/features/lora.html) for more usage information. Thanks for the contribution from China Merchants Bank. [#521](https://github.com/vllm-project/vllm-ascend/pull/521).
- Sleep Mode feature is supported. Currently it only works on V0 engine. V1 engine support will come soon. [#513](https://github.com/vllm-project/vllm-ascend/pull/513)

### Core

- The Ascend scheduler is added for V1 engine. This scheduler is more affinity with Ascend hardware. More scheduler policy will be added in the future. [#543](https://github.com/vllm-project/vllm-ascend/pull/543)
- Disaggregated Prefill feature is supported. Currently only 1P1D works. NPND is under design by vllm team. vllm-ascend will support it once it's ready from vLLM. Follow the [official guide](https://docs.vllm.ai/en/v0.8.4/features/disagg_prefill.html) to use. [#432](https://github.com/vllm-project/vllm-ascend/pull/432)
- Spec decode feature works now. Currently it only works on V0 engine. V1 engine support will come soon. [#500](https://github.com/vllm-project/vllm-ascend/pull/500)
- Structured output feature works now on V1 Engine. Currently it only supports xgrammar backend while using guidance backend may get some errors. [#555](https://github.com/vllm-project/vllm-ascend/pull/555)

### Others

- A new communicator `pyhccl` is added. It's used for call CANN HCCL library directly instead of using `torch.distribute`. More usage of it will be added in the next release [#503](https://github.com/vllm-project/vllm-ascend/pull/503)
- The custom ops build is enabled by default. You should install the packages like `gcc`, `cmake` first to build `vllm-ascend` from source. Set `COMPILE_CUSTOM_KERNELS=0` environment to disable the compilation if you don't need it. [#466](https://github.com/vllm-project/vllm-ascend/pull/466)
- The custom op `rotary embedding` is enabled by default now to improve the performance. [#555](https://github.com/vllm-project/vllm-ascend/pull/555)

## v0.7.3rc2 - 2025.03.29

This is 2nd release candidate of v0.7.3 for vllm-ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.3) to start the journey.

- Quickstart with container: <https://docs.vllm.ai/projects/ascend/en/v0.7.3/quick_start.html>
- Installation: <https://docs.vllm.ai/projects/ascend/en/v0.7.3/installation.html>

### Highlights

- Add Ascend Custom Ops framework. Developers now can write customs ops using AscendC. An example ops `rotary_embedding` is added. More tutorials will come soon. The Custom Ops compilation is disabled by default when installing vllm-ascend. Set `COMPILE_CUSTOM_KERNELS=1` to enable it.  [#371](https://github.com/vllm-project/vllm-ascend/pull/371)
- V1 engine is basic supported in this release. The full support will be done in 0.8.X release. If you hit any issue or have any requirement of V1 engine. Please tell us [this issue](https://github.com/vllm-project/vllm-ascend/issues/414). [#376](https://github.com/vllm-project/vllm-ascend/pull/376)
- Prefix cache feature works now. You can set `enable_prefix_caching=True` to enable it. [#282](https://github.com/vllm-project/vllm-ascend/pull/282)

### Core

- Bump torch_npu version to dev20250320.3 to improve accuracy to fix `!!!` output problem. [#406](https://github.com/vllm-project/vllm-ascend/pull/406)

### Models

- The performance of Qwen2-vl is improved by optimizing patch embedding (Conv3D). [#398](https://github.com/vllm-project/vllm-ascend/pull/398)

### Others

- Fixed a bug to make sure multi step scheduler feature work. [#349](https://github.com/vllm-project/vllm-ascend/pull/349)
- Fixed a bug to make prefix cache feature works with correct accuracy. [#424](https://github.com/vllm-project/vllm-ascend/pull/424)

## v0.7.3rc1 - 2025.03.14

🎉 Hello, World! This is the first release candidate of v0.7.3 for vllm-ascend. Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.3) to start the journey.

- Quickstart with container: <https://docs.vllm.ai/projects/ascend/en/v0.7.3/quick_start.html>
- Installation: <https://docs.vllm.ai/projects/ascend/en/v0.7.3/installation.html>

### Highlights

- DeepSeek V3/R1 works well now. Read the [official guide](https://docs.vllm.ai/projects/ascend/en/v0.7.3/tutorials/multi_node.html) to start! [#242](https://github.com/vllm-project/vllm-ascend/pull/242)
- Speculative decoding feature is supported. [#252](https://github.com/vllm-project/vllm-ascend/pull/252)
- Multi step scheduler feature is supported. [#300](https://github.com/vllm-project/vllm-ascend/pull/300)

### Core

- Bump torch_npu version to dev20250308.3 to improve `_exponential` accuracy
- Added initial support for pooling models. Bert based model, such as `BAAI/bge-base-en-v1.5` and `BAAI/bge-reranker-v2-m3` works now. [#229](https://github.com/vllm-project/vllm-ascend/pull/229)

### Models

- The performance of Qwen2-VL is improved. [#241](https://github.com/vllm-project/vllm-ascend/pull/241)
- MiniCPM is now supported [#164](https://github.com/vllm-project/vllm-ascend/pull/164)

### Others

- Support MTP(Multi-Token Prediction) for DeepSeek V3/R1 [#236](https://github.com/vllm-project/vllm-ascend/pull/236)
- [Docs] Added more model tutorials, include DeepSeek, QwQ, Qwen and Qwen 2.5VL. See the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.3/tutorials/index.html) for detail
- Pin modelscope<1.23.0 on vLLM v0.7.3 to resolve: <https://github.com/vllm-project/vllm/pull/13807>

### Known Issues

- In [some cases](https://github.com/vllm-project/vllm-ascend/issues/324), especially when the input/output is very long, the accuracy of output may be incorrect. We are working on it. It'll be fixed in the next release.
- Improved and reduced the garbled code in model output. But if you still hit the issue, try to change the generation config value, such as `temperature`, and try again. There is also a known issue shown below. Any [feedback](https://github.com/vllm-project/vllm-ascend/issues/267) is welcome. [#277](https://github.com/vllm-project/vllm-ascend/pull/277)

## v0.7.1rc1 - 2025.02.19

🎉 Hello, World!

We are excited to announce the first release candidate of v0.7.1 for vllm-ascend.

vLLM Ascend Plugin (vllm-ascend) is a community maintained hardware plugin for running vLLM on the Ascend NPU. With this release, users can now enjoy the latest features and improvements of vLLM on the Ascend NPU.

Please follow the [official doc](https://docs.vllm.ai/projects/ascend/en/v0.7.1) to start the journey. Note that this is a release candidate, and there may be some bugs or issues. We appreciate your feedback and suggestions [this issue](https://github.com/vllm-project/vllm-ascend/issues/19)

### Highlights

- Initial supports for Ascend NPU on vLLM. [#3](https://github.com/vllm-project/vllm-ascend/pull/3)
- DeepSeek is now supported. [#88](https://github.com/vllm-project/vllm-ascend/pull/88) [#68](https://github.com/vllm-project/vllm-ascend/pull/68)
- Qwen, Llama series and other popular models are also supported, you can see more details in [supported_models](https://github.com/vllm-project/vllm-ascend/blob/v0.7.1rc1/docs/source/user_guide/supported_models.md).

### Core

- Added the Ascend quantization config option, the implementation will coming soon. [#7](https://github.com/vllm-project/vllm-ascend/pull/7) [#73](https://github.com/vllm-project/vllm-ascend/pull/73)
- Add silu_and_mul and rope ops and add mix ops into attention layer. [#18](https://github.com/vllm-project/vllm-ascend/pull/18)

### Others

- [CI] Enable Ascend CI to actively monitor and improve quality for vLLM on Ascend. [#3](https://github.com/vllm-project/vllm-ascend/pull/3)
- [Docker] Add vllm-ascend container image [#64](https://github.com/vllm-project/vllm-ascend/pull/64)
- [Docs] Add a [live doc](https://docs.vllm.ai/projects/ascend/en/latest/) [#55](https://github.com/vllm-project/vllm-ascend/pull/55)

### Known Issues

- This release relies on an unreleased torch_npu version. It has been installed within official container image already. Please [install](https://github.com/vllm-project/vllm-ascend/blob/v0.7.1rc1/docs/source/installation.md) it manually if you are using non-container environment.
- There are logs like `No platform detected, vLLM is running on UnspecifiedPlatform` or `Failed to import from vllm._C with ModuleNotFoundError("No module named 'vllm._C'")` shown when running vllm-ascend. It actually doesn't affect any functionality and performance. You can just ignore it. And it has been fixed in this [PR](https://github.com/vllm-project/vllm/pull/12432) which will be included in v0.7.3 soon.
- There are logs like `# CPU blocks: 35064, # CPU blocks: 2730` shown when running vllm-ascend which should be `# NPU blocks:` . It actually doesn't affect any functionality and performance. You can just ignore it. And it has been fixed in this [PR](https://github.com/vllm-project/vllm/pull/13378) which will be included in v0.7.3 soon.
