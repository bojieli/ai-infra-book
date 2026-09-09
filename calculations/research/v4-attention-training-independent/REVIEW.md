# V4 tied-KV attention reference independent review

Passed for the explicitly unrounded real-arithmetic core. Frozen public module SHA-256: `2f39e2ad020d54ee007c66c33f854a15887968ad1dd8b1e9b4ec8e0a83c8b200`.

`check.py` / `results.json` contain 124 passing checks. Four author tests were independently re-run: 4 pass, 0 skip. All three scenario JSON/Markdown files replay, dependencies and source hashes match, and all 54 source records are exact members of the shared lock. No author or shared file was modified.

## Independent numerical and count checks

Four separate FP64 batched autograd fixtures use a rectangular padded gather and einsum implementation, preserving duplicate index slots. They cover batches two/three, one/two/three queries and heads, single-key repetition, different valid counts and unselected KV rows. Q and shared-KV VJPs agree, including the joint key/value gradient, repeated indices and accumulation across heads/queries. Summing per-batch sink gradients agrees with one shared sink parameter's batched autograd gradient. Maximum absolute discrepancy is 8.881784197001252e-16.

The scalar ledger is independently reconstructed per query from primitive counts. For v valid slots, forward scale takes v operations; stable-softmax subtract/divide each take v+1, and the sum takes v: total 4v+2. Backward delta costs 2v-1; score adjoints cost 2v; sink adjoint costs one; scale costs v: total 5v. Two local KV branches require AD additions to join and AD additions for the declared noncoalesced scatter. Sink's cross-query/batch reduction contributes H(BT-1). Matrix work uses the declared 2mnk convention: two forward and four backward contractions, each 2AD. Local outer products deliberately follow that convention, rather than claiming a minimal scalar instruction count.

Window geometry is independently checked at T=1,127,128,129,257 using triangular-prefix plus fixed-window-tail sums. Default logical valid work is not T² after the window fills. Repeated IDs remain separate softmax entries and are not removed when calculating A or saved probabilities.

## Official source and dtype boundary

The locked kernel.py at lines 277–367 declares Q/KV/output BF16, sink FP32 and int32 IDs. It gathers one KV tensor for both QK and PV. Sink contributes only to the denominator. Thus its derivative is nonzero through the denominator, while no sink-value vector or corresponding numerator term should be added.

The source casts unnormalized exponent tiles from FP32 into `acc_s_cast` BF16 before PV, retains an FP32 denominator and performs online block rescaling. The reference instead uses exact real softmax probabilities and includes sink in its stable maximum. It correctly marks quantized kernel value equivalence false and leaves the cast surrogate gradient null. Autograd agreement therefore verifies the stated mathematical reference only; it cannot establish source BF16/online-order equivalence or STE policy.

The reference counts valid logical slots and rejects all-invalid queries; source 64-slot padding, head padding and online block behavior remain excluded. In particular, a reference padding order must not be treated as proof of identical online-kernel numerical execution. Fixed indices have no continuous derivative in this core; that does not eliminate an indexer training objective elsewhere.

## State and integration limits

Q and a single tied-KV buffer are saved in the declared FP32 reference; probabilities remain per slot, sink probabilities per query/head, and indices int32. There is one shared dKV buffer, initialized to zero, with the stated per-slot read/write scatter traffic. This is a partial data-operation account, not total HBM traffic. BF16 source-interface bytes are separate from reference saved bytes. Output/upstream, backward temporaries, owners and workspace are explicitly excluded from saved retention.

No mathematical or migration blocker was found for this core. Keep complete_attention_layer and complete_v4_training false, and actual backward kernel FLOPs/peak unknown. Projection, normalization/RoPE, compressor, indexer/auxiliary objectives, quantization training policy and distributed communication must be implemented separately before closing the original full-attention/training scope.
