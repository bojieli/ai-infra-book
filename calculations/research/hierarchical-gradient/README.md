# C37 candidate: one real gradient through flat and hierarchical all-reduce

This finite experiment implements the scope in `research/supernode-integration/next-scope.md`. It does not close the remaining C37 framework buckets, full training schedules, or distributed inference work.

Run from repository root:

```sh
python calculations/research/hierarchical-gradient/calculate.py
```

The output `result.json` contains12 cases: FP32/BF16 ×flat contiguous/flat interleaved/hierarchical ×one/two NICs per server. Only research files are produced.

## Tensor and ownership

Official Qwen3-8B config and `qwen3.weights` select exactly `model.layers.0.mlp.gate_proj.weight`, shape[12288,4096],50,331,648 elements. FP32 gradient payload is201,326,592bytes (192MiB) per rank; BF16 is100,663,296bytes (96MiB). The adapter's36 layer copies are recorded as provenance of the template but are not multiplied into this one first-layer tensor. Each rank contributes different sample data to the same coordinates; the collective forms the sum, not the average.

There are8 fixed physical ranks, server0 ranks0..3 and server1 ranks4..7. Eight contiguous elementary chunks cover the flattened tensor exactly without padding. Every message lists original physical sender/receiver, reduction or copy operation, elementary chunk IDs, element start/stop and byte payload, and the sender's per-chunk contributor identities before that round. Receives are applied only after all sends for the round have been snapshotted.

Flat contiguous order is0,1,2,3,4,5,6,7. Interleaved is0,4,1,5,2,6,3,7. Both reuse all14 RS/AG rounds from `ring_collective.schedule`. RS leaves logical rankr owning chunk(r+1) modulo8; AG restores all eight chunks.

The hierarchy has3 stages and8 rounds:

1. Each server performs4-rank local RS,3 rounds, with each coarse chunk holding two elementary chunks. Coarse chunkc is owned by local rank(c−1) modulo4.
2. Four pairs of corresponding owners perform2-rank cross-server AR. Each pair splits its coarse chunk into its two elementary chunks for1 RS and1 AG round. This is actual all-reduce of corresponding intervals, not exchange of unrelated chunks.
3. Each server performs local AG,3 rounds, restoring all8 elementary chunks to each rank.

`ownership_boundaries` records retained chunks after each phase; RS explicitly discards non-owned scratch copies. At the end, all8 ranks own all8 chunks with contributor set0..7. Scalar reduction additions are7×50,331,648 =352,321,536, independent of organization or gradient width. Integer contribution identities establish algebraic coverage, not floating-point numerical equivalence.

## Physical paths and declared rates

Every stripe path counts sender rank.tx and receiver rank.rx separately. Local messages also traverse a distinct directed local.sender→receiver resource, all declared200GB/s. Remote messages traverse source server NIC.tx, shared server egress, a directed cut.0→1 or cut.1→0, an additional shared bidirectional cut, destination server ingress, destination NIC.rx, and the endpoint resources. Each NIC direction is25GB/s; each server shared egress/ingress and each directed cut is40GB/s; the common bidirectional cut is80GB/s. These are explicit teaching inputs, not vendor capabilities or measurements.

With two NICs, every remote message splits into two disjoint equal whole-element intervals. Their payloads sum to the original message; the data is never copied twice. NIC0/1 have distinct resources, while both stripes still consume the same server edges and common cut. `traffic.account` receives the stripes using virtual endpoints to distinguish these physical paths. Its resource counters are independently recounted in the candidate; exact rational summaries accompany its floating-point presentation fields.

`bandwidth_overrides` maps an existing used resource ID to a positive integer bytes/s rate. Unknown names and nonpositive rates reject. Examples include `server0.nic0.tx`, `server0.nic0.rx`, `server0.egress`, `server1.ingress`, `cut.0->1`, `cut.1->0`, and `shared_cut.bidirectional`. The physical graph is fixed for this finite task; arbitrary graph construction is not implied by these overrides.

Each round's declared communication lower bound is max(resource bytes/rate)+2us startup. Sum of round maxima respects the serial phase barriers and is no smaller than the maximum full-run resource demand. Reduction compute, propagation, buffers, transport protocol and real interference remain unmodeled. Passing `budget_ns` means only that this bound has not excluded the candidate; actual training feasibility and measured runtime remainnull.

## Hand-check identities and results

WritingM for the per-rank full tensor bytes, all algorithms send14M. Flat contiguous remote sends3.5M; interleaved remote sends14M; hierarchy remote sends2M. Hierarchical local RS and AG each send6M. Sending and receiving endpoint counters are separate resource demands; they are not added into twice the network payload, and aggregate path counters are not labeled HBM traffic.

Default FP32 values:

| Organization | Remote send bytes | One NIC lower ms | Two NIC lower ms |
|---|---:|---:|---:|
| Flat contiguous |704,643,072|14.12086144|8.8360384|
| Flat interleaved |2,818,572,288|56.39944576|35.2601536|
| Hierarchical |402,653,184|9.57901312|6.55911424|

All send2,818,572,288bytes. Two NICs move the bottleneck to the fixed server ingress/egress and cut. Increasing both NIC rates to100GB/s leaves the two-NIC hierarchical bound unchanged. Independently slowing only server0 NIC0.tx or NIC0.rx to1GB/s makes the respective sender or receiver resource the unique largest aggregate resource, confirming both endpoints are counted.

BF16 halves byte-dependent work while retaining startup: bounds are7.07443072/4.4320192ms contiguous,28.21372288/17.6440768ms interleaved, and4.79750656/3.28755712ms hierarchical for one/two NICs. These results compare declared communication organizations for the same real tensor; none is a measured all-reduce or complete training step.

## Interface and self-checks

`calculate(model='qwen3-8b', gradient_dtype='FP32', algorithm='hierarchical', nics_per_server=1, bandwidth_overrides=None, startup_ns=2000, budget_ns=40000000)` returns gradient metadata and verified sources; rank mapping; round messages/stripes; phase ownership; per-resource counters/rates/exact service; stage rounds/payload/lower bounds; public traffic accounting; and necessary-budget result.

Generation passes contribution disjointness, no AG overwrite, exact final ownership,14M sends, algorithm-specific remote sends,7E reductions, stripe/send conservation and rational lower-bound ordering checks for all12 cases. Additional local checks verified independent source/destination NIC bottlenecks, shared-cap saturation and rejection of unsupported dtype, invalid NIC count, negative startup, nonexistent resource and zero rate. Independent reviewer artifacts, if added alongside this candidate, remain separate from these self-checks.
