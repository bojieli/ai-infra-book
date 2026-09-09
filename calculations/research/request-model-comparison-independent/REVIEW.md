# Independent review: four-model request accounting

Verdict: no new arithmetic, request-boundary or source-propagation blocker found in the frozen candidate. It can be integrated as the declared logical request comparison, retaining unknown runtime/quality quantities and the unresolved K3 checkpoint conflict. This does not close original experiment2-9 hardware/quality comparison or C11/C14.

Reviewed module SHA256: `a20d806be0886cded5b72160601297447ae379f584509529c205732a8435a5c1`. All18 candidate manifest files and five listed public dependency hashes verify; see manifest-review.json. The review only writes this directory, with no author/shared modifications.

## Original requirement and contract

`outlines/02-模型架构.md` experiment2-9 explicitly names Qwen3-8B, DeepSeek-V4-Flash/Pro and Kimi K3 and asks for input/decode/cumulative work, weights/state and interfaces. The candidate keeps all four identities. Common S/P/G/B is a geometry comparison; it does not assert equal tokenization, semantic task or quality.

P>=1 and G>=1. The final input logits produce the first output; D=G-1 subsequent forwards append D state positions. The final returned token has not been fed back, so final retention is S+P+G-1. G1 correctly has no decode forward, including coldP1. Input-stage head work is retained once for ordinary multi-token input, but V4 S>0 is explicitly P sequential forwards and charges every intermediate discarded head. It is not called parallel cached prefill. Restored prefix states must be compatible model-specific snapshots, and retrieval/restoration cost remains unknown.

## Independent calculations

`check.py` passes105 assertions. It avoids reimplementing the author's generation loop as its long-run oracle:

- S125/P3/G3/B2 short comparison: every decode row and every V4 sequential input row is compared to a separate public full-forward call for matrix, scalar and special counts. State is independently obtained from public state accounting at the actual processed length, explicitly selecting expanded MLA. Initial/final growth is verified.
- G1 verifies no decode, unchanged post-input state and exactly one cold input call for all models.
- Qwen and K3 expanded/compact: history111, D257, B2. Independent public endpoint/midpoint forwards establish the affine relation; cumulative arithmetic is D*(first+last)/2, including every special counter. Final state matches the last full public forward. This does not use the candidate's affine_proof or per-step loop as oracle.
- V4 Flash/Pro: history1019, D261, B2, crossing window/compression boundaries. Matrix totals use closed quotient-block sums of floor(n/r), capped floor(n/4) and min(n,window), plus the separately isolated constant projection/expert/head work. No token loop is used in this expected total. All261 heads remain charged.
- Qwen's last legal decode position is accepted; a request exceeding configured context is rejected before model work. Backward differencing does not probe an illegal future context.
- K3 config_checkpoint_shape_match=false and A_log missing evidence survive aggregation; compact remains declared algebraic alternative.

`check_artifacts.py` passes16 model-artifact groups across all four frozen scenarios. It derives V4 cache allocation directly from the fixed source buffer expressions: full window plus floor(maxlen/ratio) compressed slots, optional index slots, and both FP32 compressor buffers with coff dimensions. ColdG1, ordinary input, prefix-boundary and6144+2048 cases all match. Input heads are checked against2*B*hidden*vocabulary, multiplied by P only for the declared sequential V4 input. Matrix/scalar/special/known-interface phase sums match every summary. Complete scalar/HBM/runtime peak/latency/quality fields remain null.

The first draft of our independent state check used state.calculate's compact default against the candidate's expanded default. This was a reviewer harness mismatch, not a candidate defect; the final check explicitly supplies expanded, and compact is separately checked in the long-run branch.

## Limits retained for integration

K3 A_log128-versus96 conflict still prevents claiming that these config/source dimensions form an unmodified runnable checkpoint. Known source coverage/assumptions must remain visible. V4 source-cache allocation is a declared maxlen/maxbatch budget separate from effective state; neither is a complete runtime peak. Input and decode interfaces differ in coverage and storage format across models: packed expert payload and uniform BF16 comparison payload are alternatives, not values to add into a physical traffic total. No hardware ranking follows from these partial logical interfaces.

The author reports9 passing regression tests; this review independently ran the105 arithmetic/boundary checks and16 artifact groups instead of repeating that same test suite. Public integration should preserve the dedicated renderer, complete sources and assumptions, and scenario replay fields.
