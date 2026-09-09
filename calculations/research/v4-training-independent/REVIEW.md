# V4 smooth primitives and mHC wrapper independent review

Status: passed for the declared mathematical subgraphs. This is not acceptance of complete V4 training, actual low-precision backward kernels, or whole-model activation memory.

Frozen primitive SHA: `d315315546bf49589563b9b0c56297d1800693e0d8acb52e4bd98f92606929bd`.
Frozen wrapper SHA: `6d7684ab552410f626cbc33fe2629b99896e8469fa969716a0031697987b8ff1`.

The reviewer edited only this independent directory. `check.py` / `results.json` bind both modules and the actual official model.py/kernel.py bytes, validate delivery bindings and replay all six frozen result files. The author's four primitive tests and three wrapper tests were independently re-run and pass without skips.

## Source order and mathematics

Official kernel.py lines 372–441 applies pre=sigmoid(scale0*mix+base)+eps, post=2*sigmoid(scale1*mix+base), and comb=row_softmax(scale2*mix+base)+eps. It then normalizes columns once, followed by nineteen row/column pairs. That is 39 epsilon-bearing normalization stages, not 20. Each normalization denominator includes epsilon; the initial softmax denominator does not. Neither implementation nor review assumes the resulting matrix is exactly doubly stochastic for nonzero epsilon.

The VJP `(g-dot(g,y))/denominator` is correct for `y=x/(sum(x)+epsilon)`. Initial softmax VJP and post/pre sigmoid derivatives are separate. The split's scale gradient sums all rows in each of three groups; base gradient sums rows for each of 24 coordinates. They are included once in the wrapper via the reused split.

Official model.py hc_post uses input-copy index i and output-copy index j: `O_jk=post_j*z_k+sum_i C_ij*X_ik`. The candidate uses this orientation. Four input-gradient branches are retained: direct residual, pre reduction, mix linear and inverse-RMS dependence. The RMS branch coefficient is `-dr*r^3/(cH)`, with neither an extra factor of two nor a detached normalization factor.

The independent FP64 tests use a dense nonlinear inner function `tanh(A y)`, rather than a diagonal elementwise function. Four cases cover c=2/4, one/two/twenty iterations, nonzero epsilon, and batches of two/three rows. Joint x gradients and shared W/base/scale gradients agree with an independent batched einsum/autograd implementation. Maximum absolute discrepancy is 1.4432899320127035e-15. This also validates cross-row parameter-gradient reduction and an inner VJP that mixes hidden dimensions.

Official Gate still evaluates router scores for fixed hash indices. Selected routing weights depend on those scores and their selected-score denominator. Independent tests confirm both selected-score gradients and zero inactive-score gradients in the fixed-selection branch. Selection bias has no continuous main-loss derivative through discrete indices; this statement does not eliminate the official separate bias update or auxiliary objectives.

## Accounting review

The independent checks expand each operation into multiplication, division and reduction lengths; they do not infer count correctness solely from gradient agreement. All scalar formulas pass at R=1,6,7,57.

For the split, forward counts consist of 2V affine operations, c pre epsilon additions, c post multiplications, row-softmax operations and 39 vector normalizations. Backward consists of separate pre/post sigmoid operations, each finite normalization VJP, initial softmax VJP, mix gradients and cross-row scale/base reductions. A length-c normalization VJP uses c products, c-1 sum additions, c subtractions and c divisions. These reproduce the declared count without counting a reduction twice.

For the outer wrapper, norm square/mean/epsilon uses 2N+1 ordinary operations per row, mix scaling adds V, and post multiplication/output addition adds 2N. Backward da/dr contributes 3V-1, RMS coefficient plus its vector contribution contributes 4+N, pre multiplication contributes N, and the four-way input join contributes 3N. Thus forward 4N+V+1 and backward 5N+3V+3 match the candidate. Each matrix contraction follows the declared 2mnk convention, including parameter-gradient reduction; its summation is not added again as scalar work.

The wrapper imports only the split account from the primitive result. It does not include the router subtotal or the inner RMSNorm/attention/MoE. Supplied inner VJP is an explicit interface, not an inferred identity or an assertion that real inner backward has zero cost. Numerical helpers recompute split values for validation; their incidental Python work is not a literal kernel execution count.

## Saved identities and acceptance limits

X and residual share one identity in the declared FP32 reference. Final comb is already the last saved normalized output, and is not charged again. Saved pre and post differ from sigmoid outputs because of +epsilon and ×2, so their additional identities are intentional. Linear output a and scaled mixes are both needed for distinct backward branches. The saved subset formula and 86-wrapper sum independently match every tested R.

The event order retains each required object until its last listed consumer. Inner saved tensors and y requirements, weights, gradients, dtype conversion buffers, backward temporaries and workspace are excluded explicitly. Consequently the sum is a forward retention subset, not a measured or complete peak. Source BF16 casts and quantization derivatives are not validated by the FP32 real-arithmetic reference.

No mathematical blocker was found in this bounded candidate. Keep `complete_v4_training=False` and unknown whole-model backward/optimizer/peak fields. Further work on attention/compressors, QAT runtime paths, head/auxiliary objectives and Muon remains outside this acceptance; the primitive and wrapper cannot close those gaps by multiplication of inference totals.

## Public migration review

The independent `public_check.py` / `public-results.json` add 1,988 passing checks. All original function ASTs, not only calculate, are unchanged. Both modules use normal public imports and share the same primitive module object. Six calculated JSONs exactly match the original frozen files and replay their scenarios. Every rendered leaf (including null and empty values) appears with its full path and value in the saved Markdown. All 54 source records are exact members of the shared source lock, and actual file byte counts/SHA-256 match. All public artifact/dependency hashes match.

One test-entry issue was found: direct unittest discovery in public/tests imported the incomplete public/src namespace, missing infra_calc.sources. The author's verify_public overlay masked this. Requested fix is limited to portable test bootstrap (find complete shared src, import topics, overlay candidate topic directory). It does not require changing the modules or accepted mathematics. Final direct discovery is pending that correction.

Public test bootstrap issue is resolved. Direct unittest discovery now passes all seven tests without skips; all 1,988 migration checks re-run successfully against refreshed bindings. Final public primitive SHA is `599f3b99a325af742dea50d9618605dd80ffdadf8fe6ab4795ace02814287afa`; final public HC SHA is `9e0a8459c6e1ea999d16b9e04546246cf7b4a2fd1da4becef9f4223821c9dd69`. No remaining public migration blocker.
