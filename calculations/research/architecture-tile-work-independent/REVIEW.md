# Architecture tile-work finite review

The original four portable tests pass. Independent checks passed for all four frozen full JSON scenes, plus four additional batch/token/history combinations and non-aligned tile dimensions 3×5×7. The independent check derives matrix dimensions from architecture geometry, rather than copying the candidate operator rows.

One documentation issue was reported: the original scope describes an “all-position vocabulary head”, but public architecture_variants uses Scenario.output_head='last'. Its actual lm_head M is batch, including prefill; this is the intended reused computation. The statement must say last-position vocabulary head per sequence. No matrix correction is necessary. Final amendment status is recorded below once the author freezes the single-string repair.

## Independent accounting

For each variant, with B batch, T current tokens, S history, L layers, A query heads and d head dimension:

- Projection/MLP matrices have M=BT and repeat L times. Q has N=Ad, K/V have N=8d, O reduces Ad to H; gate/up use F and down reduces F to H. The vocabulary head is M=B, K=H, N=151936, once.
- QK is [T,d]×[d,S+T] and PV is [T,S+T]×[S+T,d], each repeated B×A×L. Both valid FLOP counts per head/layer are `2d(TS+T(T+1)/2)`. GQA's eight KV heads do not replace A query heads in this product count.
- Every rectangular GEMM is `2MNK`; fully padded work is `2 ceil(M/tm)tm ceil(N/tn)tn ceil(K/tk)tk`. These are the arithmetic-only outputs of gemm_tiles.account, whose signature orders arguments M,K,N and tm,tk,tn. Its BF16 traffic assumptions are not transferred into this adapter.
- `valid + causal rectangle excess + tile padding excess = fully padded`, at both per-row and model totals. The nested tile_blocks.valid_matrix_flops means valid rectangular GEMM work, while the outer valid_flops means causal useful work for QK/PV; the explicit rectangular naming prevents these being added twice.

The additional cases B3/T1/S0, B2/T3/S2, B3/T7/S11 and B1/T65/S0 validate multi-batch counts, history and odd tails. Explicit enumeration of permitted (query,key) pairs agrees with the triangular formula. The T1 path has no causal rectangle excess; padding can still be large.

## Conditional rate threshold

For deep and wide variants with padded totals Pd/Pw and caller rates Rd/Rw, service is Pd/Rd versus Pw/Rw. Therefore wide is strictly faster only when Rw/Rd > Pw/Pd. Tests assign rates proportional to integer padded totals and exercise threshold multipliers 0.999, 1, and 1.001 for all four extra cases; the exact tie is not reported as faster. No rate is inferred from effective valid/padded arithmetic fractions.

The adapter remains a fully padded rectangular algorithm selected by the caller. It is not a claim that a particular backend materializes all masked scores or uses these tile dimensions, and it does not implement a triangular tile-skipping backend. Non-matrix work, memory limits, bytes, launch dependencies, communication, occupancy and measured Tensor Core utilization remain outside this account. The output retains actual_tensor_core_utilization and full_forward_runtime_seconds as null. Both architectures remain untrained parameter-budget designs.

Re-run `PYTHONDONTWRITEBYTECODE=1 python calculations/research/architecture-tile-work-independent/check.py`. The finite audit records 2,044 expanded assertions; this is not a completion percentage. Original snapshots and results are preserved separately for the documentation repair.

## Final amendment accepted

The author corrected only the module phrase to “last-position vocabulary head per sequence” and synchronized the contract. New SHA is `610f147095b2f95cb3170fed62316a9673e67cab8d555e410bf327f6b21d1e2e`. Independently reversing this single replacement exactly recovers the original snapshot SHA `094944e41b2f2e83e77b203e4b3345e8a7151fa0cb8bc1a802fc625306c0a664`. The full 2,044-check audit passed again; all four regenerated full scene JSONs match, and their mathematical summaries are identical to the original review. No remaining blocking issue was found. No public or author file was modified by this reviewer.
