# C33 Qwen235 placement-to-expert execution contract

This is one concrete joint ownership account, not completion of the broader multi-model C33 experiment. It consumes public qwen235_placement with identical TP/EP/PP (exactly eight ranks), BF16 weight storage, sequence length, request count and caller workspace reserve. No public files change.

## Cohort, geometry and input

Qwen3-235B-A22B official config/index supplies H/F/E/K/layers. All EP replicas contain the same cohort's attention output, and TP down projections are row-parallel. Every expert resides on one EP owner and spans the TP ranks there; local gate/up rows and down columns have width F/TP. No token-dispatch transfer is needed: each owner already holds X. EP is not an independent data-parallel request replica.

A complete route record for each layer/request/position carries K distinct expert IDs and finite nonnegative normalized weights. Every identity must appear exactly once, and every ID must be in range. The output includes the actual synthetic/input route table and logical token identity map; a histogram alone is never treated as a destination map. Default balanced routes are (row*K+j)%E, hot routes use first K. Both are declared synthetic, not checkpoint observations. Caller histograms cannot replace the table.

For each rank/expert/layer with n assigned tokens, gate/up matrices are [n,H]@[H,F/TP]; down is [n,F/TP]@[F/TP,H]. Combined matrix FLOPs are 6nHF/TP. Empty experts execute no GEMM while all their weights remain resident. Work over all ranks conserves 6LRKHF, without multiplying by EP replicas. SiLU and product use 2nF/TP scalar operations plus nF/TP sigmoid calls. Qwen route scaling occurs after down: each partial H-wide output is scaled and accumulated from zero, charging 2nH per TP shard. This is a declared real-arithmetic transformation; it does not assert floating-point rounding equals scaling after a TP reduction.

## Message graph and exact consumers

Within each layer:

1. TP ranks 1..TP−1 send partial token outputs only for tokens active in that EP, to its TP0 root. TP root sums (TP−1)H values for each active token.
2. Each EP>0 root sends only its active token set to EP0/TP0; that root sums H values per received token. Inactive contributions are mathematical zeros, not fake sends.
3. EP0/TP0 broadcasts the complete cohort output to all other EP roots. This includes tokens that had no local expert contribution: next attention needs the complete cohort.
4. Each EP root broadcasts complete values to its other TP ranks.

Messages are batched per directed edge and phase, with an explicit token list, H×wire_element_bytes payload and row_metadata_bytes per token. All message producers/consumers are concrete ranks. No token-expert-pair dispatch is fabricated. Equal expert histograms can have different active-token-per-EP sets, and therefore different wire totals.

At each PP boundary a single complete block hidden tensor is sent from stage root to next stage root. A distinct phase replicates it to the other ranks of that next stage. This is one inter-stage transfer plus necessary receiving-stage fanout, not eight independent DP cohort transfers. Block attention/residual/norm operations are outside this expert subaccount; they produce the complete hidden values transported at the boundary. Embeddings are present only on first placement stage, head/final norm only on last. The final output is ready for head computation; logits/head TP collectives are not silently counted or claimed.

## Interfaces, capacity and resource assumptions

Per-expert GEMM operand interfaces report BF16 weight reads and declared FP32 mathematical activation reads/writes per operand role. They are conditional materialized interfaces, not measured HBM. Repeated X reads in gate/up are both represented. Wire dtype is explicit and does not determine arithmetic precision; cast/rounding work and actual collectives are not simulated.

Each rank reuses exact placement BF16 weights and per-request KV, multiplied by the common request count. Its necessary resident budget is weights + requests×KV + declared workspace. A rank over nominal capacity fails the necessary check. Passing is necessary-only: message/route staging and activation allocator requirements have not proved the reserve sufficient. Actual peak stays null. Logical route records use three int64 identity fields plus int32 ID/FP32 weight per selection; actual GPU residency/replication is unspecified.

Resource input defaults (100e12 matrix FLOPs/s/rank, 100e9 bytes/s, 1e−6 startup) are teaching assumptions, not hardware specs or measurements. Matrix service uses busiest rank per layer. Each communication phase has full-duplex per-rank send and receive service; its lower bound is max(total send service per rank,total receive service per rank), with one startup per edge message. PP root fanout shares source injection and serializes those service demands. The named phases and layers are sequential barriers. Their sum is a conditional expert/communication subaccount bound, excluding scalar rates, attention/router, index formation, packing and casts; full request runtime remains null.

## Validation

Five portable tests cover exact assignment and matrix conservation, direct scenario replay, BF16 residency and worst-rank ±1 byte, equal-histogram/different-destination counterexample, PP endpoint/fanout uniqueness, message consumers, invalid route/resource inputs, and small FP64 direct MoE versus TP/EP reconstructed outputs for three topologies. Synthetic tables and capacity failures are retained in scenarios; none are removed to improve apparent fit.
