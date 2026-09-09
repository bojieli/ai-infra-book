# V4 attention periphery independent review

Passed for the declared single-layer, ratio=0 unrounded mathematical periphery. Public module SHA-256: `cc8e8d7509523328239b3e46e6cc7e738119b184bf8d3dbf876a5aae4b232161`.

`check.py` / `results.json` contain 164 passing assertions, including all 54 official source records as exact members of the public lock with matching bytes/hash, frozen artifact/dependency bindings, and three scenario/Markdown replays. The author's three tests were independently re-run: 3 pass, 0 skip. No shared or author file was changed.

## Source shape and scope

Locked model.py Attention constructs wq_a as [q_rank,hidden], wq_b as [heads*head_dim,q_rank], wkv as [head_dim,hidden], grouped wo_a as [groups,o_rank,heads*head_dim/groups], and wo_b as [hidden,groups*o_rank]. The candidate matches these global shapes. It is a global mathematical layer account, not an individual TP rank's placement or communication account.

The source applies learned RMSNorm at q_rank, unweighted per-head RMS after wq_b, learned RMSNorm after wkv, forward RoPE on Q and KV, and inverse/conjugate RoPE on the core output before grouped wo_a. The candidate follows this order and rotates only the final rope_dim adjacent real/imaginary coordinates, matching source view_as_complex. Gradients apply the transpose rotation, including the reversal of the output's conjugate direction.

For ratio=0 there is no compressor or indexer branch. For other layers, qr is also consumed by the indexer and x by the compressor; the candidate explicitly excludes those extra gradients. It does not silently claim that this two-branch dX sum covers those layers.

## Independent numerical and accounting checks

Three FP64 batched fixtures test batches two/three, groups one/two and heads two/four. They use two complex RoPE pairs (four rotated coordinates) and a real one-key tied attention plus sink callback. This callback couples all coordinates through q·kv and shares KV across heads, rather than acting as an identity. Joint x, all five projection weights and both learned normalization weights agree with independently constructed batched PyTorch autograd. Shared parameter gradients are compared after summing the manual per-row results. Maximum absolute discrepancy is 1.1102230246251565e-15.

Matrix shapes and all forward/dX/dW contractions independently match 2mnk at R=1,6,129. For weighted RMS of width d, forward is 4d+1 per row; backward includes gamma multiplication, mean-dot, input VJP, gamma product and cross-row gamma reduction: 7Rd+d(R-1). The unweighted per-head case has forward 3d+1 and backward 5d per row. Scalar counts were expanded by reduction length, independently of the numerical helper's Python loop operations.

RoPE uses six real operations per pair for Q, KV and inverse output, and the same count for their adjoints. Frequency construction is expressly excluded; the FP32 real/imag constant table is 4*T*rope_dim bytes, without batch/head replication. The final dX join contributes R*hidden additions. Core forward/backward matrices, softmax and its state are absent from this subtotal.

## Saved identities and numerical limits

The saved set retains X once for q and KV branches; weighted-normalized q_rank output is distinct from its pre-gamma normalized value; inverse RMS values are separate. Normalized head values before RoPE are distinct from the core-owned rotated Q in this declared functional reference. The core-owned Q/KV/probability state is excluded here. Derotated output and grouped projection output are retained for their parameter gradients. Independent byte accounting agrees for all tested R, with no duplicate key/value copies or core probabilities.

This is a declared FP32 retention subset, not a proof of actual low-precision aliasing or allocator peak. In-place source RoPE/casts and FP8 projection quantizers are not assigned a surrogate gradient, and the candidate retains quantized equivalence false. Frequencies are fixed constants supplied by the caller, not trained quantities or per-step sin/cos work.

No blocker was found in the frozen scope or public migration. Keep the core, indexer and compressor work exclusions and complete-training=false boundaries. Joining this account to the existing core still requires an explicit request/sequence state contract; it does not by itself close compressor, QAT, full attention training or actual runtime memory.
