# Qwen3.6-35B-A3B official input audit

Observed 2026-09-09 UTC. Model revision is `995ad96eacd98c81ed38be0c5b274b04031597b0` from the official HF model API. Raw config, model card, index, processor and tokenizer metadata are in `model/`. The official card advertises 35B total / 3B activated; exact storage below includes the separate MTP branch and is not an activated-compute count.

The model specifies `Qwen3_5MoeForConditionalGeneration`, `qwen3_5_moe`, and text `qwen3_5_moe_text`. No modeling Python file is included in its model API tree. The card requests latest Transformers, without selecting an exact code commit. We independently pin official `huggingface/transformers` commit `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55` (committer timestamp 2026-09-08T18:58:00Z), reusing the previously audited implementation family only after the configuration and every base-text storage shape matched. This is not a claim that the model publisher selected this commit, or that runtime/numerical compatibility was tested.

## Config and implementation compatibility

40 layers: 30 linear attention and 10 full attention, one full layer after each three linear layers. Hidden size 2048; vocabulary 248320; untied embedding/head. MoE: 256 experts, top 8, intermediate 512, shared intermediate 512. Full attention: 16 query heads, 2 KV heads, explicit head_dim 256, with output gate. Linear attention: 16 key heads and 32 value heads, both dimension 128; convolution kernel 4. Context limit is 262144. Vision: 27 layers, hidden 1152, MLP 4304, 16 heads, patch16, temporal2, merge2, output2048; no deepstack indexes. MTP config records one layer.

The pinned implementation uses these actual config fields to construct the relevant modules: GatedDeltaNet begins at modeling source line504; attention at749; router at882. `A_log` and `dt_bias` use value-head count32 (lines533–537), q/k repeat twice at620–622. Their checkpoint storage is BF16 in this model, unlike the other model's FP32 entries; storage dtype must not be used as a runtime-state dtype assertion. Line619 explicitly computes `-A_log.float().exp() * softplus(a.float() + dt_bias)`. Fallback recurrence/chunk computation initializes or converts recurrent state to FP32; config also states `mamba_ssm_dtype=float32`. Full attention projects both Q and gate, so Q projection width is8192, distinct from actual attention width4096. MTP keys are explicitly ignored at model load (line1010); its stored parameters are counted separately and no MTP forward claim is made.

## Exact metadata result

All26 shards and1045 tensors checked. All stored tensors are BF16. All693 expected base-text tensors match config-derived names/shapes, with no missing tensors, extra base-text tensors, or conflicts. There is no A_log head-count mismatch.

| Storage group | Elements | Payload bytes |
| --- | ---: | ---: |
| Base text including embedding/head | 34,660,610,688 | 69,321,221,376 |
| Vision | 446,571,248 | 893,142,496 |
| MTP | 844,640,768 | 1,689,281,536 |
| Full checkpoint | 35,951,822,704 | 71,903,645,408 |

`audit.py` verifies all locked file SHA256 and byte lengths, header length-prefix agreement, tensor-name uniqueness, shard index membership, shape×dtype bytes, contiguous offsets, each full shard's Content-Range total length, and aggregate index total_size. The index stores total_size as a JSON floating-point literal; the audit reports its exactly integral value as an integer. Expected config-derived shape enumeration covers base text; vision/MTP have storage inventory validation only. No weight payload, runtime model load, or forward numerical execution was performed.

## Evidence and reproduction

`source-lock.patch.json` holds70 immutable original records totaling748379 bytes, with upstream URLs, revisions, SHA256, and lengths. `http-evidence.json` saves checked_at timestamps and response status/ranges. All52 accepted range requests were strict206: bytes0–7 for lengths, then bytes8–(7+length) for JSON headers. Curl is capped against oversized responses; Range failures raise, so full weight files are never downloaded. Redirect bodies require a2048-byte curl cap floor, while stdout reads remain bounded to the requested range plus one rejection byte.

`api-observation.lock.json` separates mutable API observations from immutable calculation sources; `api/model-main-discovery.json` is the initial current-model discovery. The downloader now pins the observed model revision and the selected Transformers commit. Reproduce metadata using `python3 calculations/research/qwen36-inputs/fetch.py`; check offline using `python3 calculations/research/qwen36-inputs/audit.py`. Downloader output/API observation order may vary from concurrency; immutable original hashes do not.

This delivery is confined to the research folder. Public adapter integration, model registry, chapter output, prefill/chunk execution account, vision forward, MTP forward, and numerical runtime validation are outside this input audit.

The official Apache-2.0 LICENSE and pinned Transformers masking_utils.py are included. All common implementation files are byte-identical to the previous Qwen3.5 research freeze; compatibility is established by matching model_type/config and all base-text checkpoint shapes, without claiming runtime validation.
