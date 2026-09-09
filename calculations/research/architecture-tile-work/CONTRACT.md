# S09 existing architecture variants → declared tile work

The coverage audit identifies a missing connection from existing near-budget shapes to declared tile work/service, not missing model parameter formulas. Public architecture_variants already constructs 48×4096 deeper_same_width and 24×5120 shallower_wider around the real Qwen8 parameter target. The former is deeper/narrower relative to the latter. Both are untrained alternatives and retain their original exact parameter deviations. This candidate calls that module rather than solving or inventing new architectures.

Public gemm_tiles.account provides the fully padded rule 2 ceil(M/tm)ceil(N/tn)ceil(K/tk)tm tn tk. Public quantized_gemm uses the same ceil geometry for its single expert projection, but its FP8 quantization schedules are outside this BF16-derived architecture comparison. No official kernel configuration has been asserted: tile M/N/K are explicit caller inputs.

## Every matrix

Use logical tp=1 matrices; this is not a TP-sharded performance prediction. Enumerate every public operator with matrix_flops>0: Q/K/V/O projections, gate/up/down, last-position vocabulary head per sequence, QK and PV. Linear M/K/N come directly from operator input/output shapes, with source layer multiplicity retained.

Attention uses one explicitly rectangular GEMM per batch/query-head/layer. QK dimensions M=T,N=S+T,K=D; PV dimensions M=T,N=D,K=S+T. Multiplicity is B×query_heads×layers. Source valid causal work per instance is 2D[T S+T(T+1)/2]; rectangular work is 2T(S+T)D; fully padded work follows the selected tile grid. Preserve these separately:

padded = valid + (rectangle−valid) + (padded−rectangle).

Thus causal masking overhead is not mislabeled tile-tail overhead. GQA reuses K/V data but still computes each query-head product; the candidate does not derive byte savings or HBM from this arithmetic. Existing gemm_tiles BF16 interface fields are intentionally not forwarded to attention probabilities, whose public default precision is different.

For each matrix report M/N/K, multiplicity, valid/rectangle/padded FLOPs and exact valid/padded fraction. Summed valid work must equal the existing architecture matrix ledger. Effective fraction describes arithmetic coverage, not actual Tensor Core occupancy, instructions, achieved device efficiency or trained quality.

## Conditional service

An explicit positive caller rate R means padded matrix arithmetic per second under this aggregate service model. Conditional matrix service is F_padded/R; effective valid arithmetic rate is F_valid divided by that service. Common rate defaults to an educational100e12, not an official hardware peak. Optional per-variant rates expose assumptions. For shallow S and deep D:

service_S < service_D iff R_S/R_D > F_padded,S/F_padded,D.

The threshold and actual supplied ratio are exact rational strings; float service must be finite. Scalars/special operations, launches, dependency stalls, memory/capacity, collectives and actual kernel dispatch are excluded, so full-forward runtime and actual utilization remain null. This cannot select an economic/quality-constrained winner or close all C13.

## Acceptance

Four portable tests: independent small tile triple enumeration (including divisible and tails), causal attention coordinate enumeration and valid/rectangle/padded conservation, whole-scenario replay, decode's zero causal-rectangle surplus, both sides of the service-rate threshold and invalid arguments. Four scenarios: default129-token tail, aligned128-token prefill, one-token8192-history decode, and nonstandard96/160/80 tiles with explicit variant-rate perturbation. Dedicated Markdown contains every matrix plus complete result fields; sources and dependency SHAs are bound. Shared files unchanged.
