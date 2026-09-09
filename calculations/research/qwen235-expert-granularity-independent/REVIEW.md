# Qwen235 expert-granularity candidate: finite review passed

Reviewed frozen SHA `97a7afb05e333a7fade68f79696fc120ca2550c4e2e4d06bcea205fd2ac8d478`. No blocking mathematical or scope issue was found. This review did not modify the candidate or public files. The five portable author tests pass with no skips; all six frozen scene results equal independent re-execution under Python 3.11.4. The local official source subset hashes also match.

## Independent parameter and placement checks

Dimensions were read directly from the fixed official config: H=4096, L=94, Q=64, KV=4, head dimension d=128, V=151936, E0=128, F0=1536, K0=8. The unique-parameter closed form is

`2VH + H + L(2HQd + 2HKVd + 2H + 2d + HE + 3HEF)`.

It yields the actual baseline 235,093,634,560. The full-model change is `LH(E−128)+3LH(EF−128×1536)`; the first term is the router and must remain even when expert budget is exact. Active expert parameters are `3LHKF`, excluding attention, norms, endpoints, and router. F uses a rational ideal and a positive alignment grid; the half-grid error bound passed all selected variants. A below-half-grid counterexample E4096/alignment128 is rejected rather than falsely reporting a positive aligned width inside that bound.

For a rank holding n layers, the unchanged non-expert/non-router parameter count was independently reconstructed as

`n(2H(Q/TP)d + 2H max(1,KV/TP)d + 2H + 2d) + (V/TP)H[first stage + last stage] + H[last stage]`.

Doubling gives BF16 bytes. This exactly matches every rank in nine checked organizations/scenarios; no subtraction of the candidate's own expert/router rows was needed in the independent formula. New expert bytes are `2n(E/EP)3H(F/TP)`; replicated router bytes are `2nEH`. KV bytes are `4n length max(1,KV/TP)d requests`, preserving complete KV heads and TP8 replication. There are no quantization scales in this BF16 subaccount; the expert width and router changes are applied to parameter counts and payload bytes, without importing low-bit scale metadata. All-resident totals include the declared workspace once per rank.

Additional organizations TP8/EP1/PP1, TP1/EP2/PP4, and TP2/EP2/PP2 used two requests and two tokens. They agree with public execution for baseline matrix work, wire bytes, rank BF16 weights, and KV. The PP4 case exercises unequal layer counts and endpoint ownership; its worst-rank capacity boundary passes at exact and +1 byte and fails at −1 byte. A successful check remains necessary-only, not observed runtime capacity.

## Actual routes, local matrices and communication

For every owned expert, local M was independently rebuilt by counting the explicit route records. Gate/up shapes `[M,H] × [F/TP,H]^T` and down `[M,F/TP] × [H,F/TP]^T` match; each costs `2MHF/TP`. Counts conserve `LRK`, and all rank matrix work conserves `6LRKHF`. Zero-row experts retain storage and zero matrix work. The logical router GEMM is `2LRHE`; the explicitly hypothetical all-replica router execution is this value times TP×EP, not additional independent cohorts.

Every directed message and its token IDs were reconstructed from the route-derived EP destination sets. TP partial reduction and EP reduction use active token sets; broadcast uses the entire cohort; each PP boundary has one root transfer and the destination-stage fanout. Each row costs `H×wire_element_bytes + row_metadata_bytes`. The exact message maps and summed byte counts match. Author tests additionally verify equal histograms with different token destinations produce different communication volumes. Inputs are already replicated within the cohort, so zero dispatch is correctly limited to that ownership premise.

## Six scenario evidence

All default scenes use one request and 16 token positions.

| Scene | Model parameter delta | Active expert parameters/token, all layers | Expert matrix FLOPs | Wire bytes |
|---|---:|---:|---:|---:|
| E128/K8 baseline | 0 | 14,193,524,736 | 454,192,791,552 | 108,017,280 |
| E64/K4 | −24,641,536 | 14,193,524,736 | 454,192,791,552 | 108,017,280 |
| E256/K16 | 49,283,072 | 14,193,524,736 | 454,192,791,552 | 108,017,280 |
| E256/K8 | 49,283,072 | 7,096,762,368 | 227,096,395,776 | 104,931,072 |
| E160/K10, F1280 | 9,474,670,592 | 14,784,921,600 | 473,117,491,200 | 108,017,280 |
| E128/K8 hot routes | 0 | 14,193,524,736 | 454,192,791,552 | 98,758,656 |

These are an expert-matrix and message subaccount, not complete requests. Only E128/F1536/K8 is the released architecture; changed variants are untrained designs. Scalar activation and combine work, router softmax/top-k, cast/packing, physical tile padding, actual peak, latency, Tensor Core utilization, and trained quality remain uncomputed or null as declared. They cannot be inferred from equal expert parameters or lower message bytes. No complete C13 closure is implied.

Re-run with `PYTHONDONTWRITEBYTECODE=1 python calculations/research/qwen235-expert-granularity-independent/check.py`. `verification.json` contains exact formulas' checks, six scene summaries, Python version and candidate SHA; the high repeated assertion count is per-matrix expansion, not a completion metric.
