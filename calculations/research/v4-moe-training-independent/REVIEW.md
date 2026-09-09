# Independent review: V4 fixed-selection MoE training

Accepted within the candidate's stated one-layer, unrounded, fixed-selection main-loss VJP contract. No mathematical blocker found. Candidate/public files were read only.

Frozen module SHA256: c2c3d15775a860b04a2ebc426af327094ea69d8186f586e831236c39bd7d3233.

## Independent numerical and count evidence

check.py passed 2,138 checks. Independent FP64 autograd uses 2/3/5 tokens, H4/F3/E4/K2, overlapping but distinct per-token selections, an entirely inactive expert, and limits 10/.06/.3. It builds a multi-token graph with shared parameter tensors, computes gradients once, and compares to the sum of candidate token VJPs. Input gradients, outputs, router/shared/expert weight gradients all agree. This checks the cross-token parameter reduction missing from single-token finite differences; maximum absolute error is 2.7755575615628914e−17.

Four actual-geometry scenarios independently sum each of 256 expert projection forward and dX/dW products, route-weight dot/reduction, input joins, resident and visited parameter counts, saved bytes, row-cap constraints and direct scenario replay. Author's four tests independently rerun: all pass, zero skipped. Their numerical tests additionally cover router-logit gradients and whole tiny graph finite differences.

76 artifact checks passed: 54 source records match exact local bytes and SHA; all artifact hashes match; four stored JSONs replay exactly and four Markdown reports match rendering. Results and module SHA are in results.json; binding checks in artifact-results.json.

## Source and formula review

Fixed official inference/model.py Gate/Expert/MoE confirms sqrt(softplus), selection-only bias, gathering original scores, normalized selected weights scaled by 1.5, and hash layers still computing differentiable routing weights. The primitive is included once for one layer; no 43-layer primitive total is added. Fixed selection excludes top-k boundary/ties and does not claim bias is never updated.

Expert gate is upper-clipped only; up is clipped on both sides. Route multiplies the F-wide unweighted SwiGLU product before W2. This is preserved in the VJP: droute is a length-F dot, dp has one route multiplication. No spurious H-wide route multiplication is added. SiLU/product backward uses six ordinary operations per F element under the declared saved a/s/u algorithm; clamp comparisons and mask selection are separate non-FLOP primitives.

Each expert input joins dW1-path and dW3-path; declared zero-based scatter then adds shared and router paths, yielding (2A+3R)H. Parameter dW GEMMs already reduce over assigned rows, so no redundant cross-row scalar parameter sum is charged. Empty expert arithmetic is zero while its stored weights remain counted.

Saved objects correctly distinguish routed unweighted product (droute input) and weighted down input (W2 dW input); shared product is not duplicated. Source hash IDs use int32 and top-k IDs int64; dispatch where token/slot indices are separately int64. Indexed access to retained X is a declared logical view, not proof that a backend allocates no gathered copies. The candidate explicitly excludes those materializations and full traffic/peak.

Report section 5.2.1 discloses FP32 master → FP4 → FP8 QAT and STE to master through the same FP8 weights. Candidate correctly calls its own full-precision oracle unrounded, not a quantization-equivalent training implementation. No unsupported router/shared cast STE is inferred.

## Acceptance boundary

This closes the declared fixed-selection single-layer MoE mathematical main-loss VJP, not complete V4 training. Actual QAT numerics, gradient precision, auxiliary balance/indexer/MTP objectives, optimizer update, inter-rank traffic, dispatch materialization and full activation peak remain outside. Layer hash scenarios use an explicitly conditional valid histogram rather than asserting checkpoint token IDs produced that histogram. The absence of those runtime inputs does not invalidate the proved conditional matrix/scalar ledger.
