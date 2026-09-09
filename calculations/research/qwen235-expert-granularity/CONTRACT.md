# C13 expert granularity around Qwen235

Original scope: chapter 2.6.2 and Experiment 2-7 ask near-equal parameter depth/width/expert comparisons. Public architecture_variants implements Qwen8 dense depth/width/FFN alternatives and explicitly excludes EP. It does not already cover this MoE experiment. This candidate adds only changing E/F/K around Qwen235; it does not redo the dense study or complete all C13 hardware/quality experiments.

## Official baseline and hypothetical variants

Keep official Qwen3-235B-A22B hidden width H=4096, layers L=94, vocabulary, attention heads/KV, norms, embedding/head and their TP/EP/PP placement. Baseline is E0=128, F0=1536, K0=8. Only the baseline expert architecture belongs to the released checkpoint; changed E/F/K is an untrained design, not weights converted from the release.

Target expert parameters P*=3LHE0F0. For requested E, ideal F=E0F0/E exactly as Fraction, rounded to nearest positive alignment (ties upward) using the existing architecture_variants helper. The original E128 baseline retains its published F even if the caller requests another alignment. Require EP|E, TP|F and K<=E. Report signed expert budget difference, exact fractional difference and half-grid error bound. E160/align128 gives F1280 instead of ideal1228.8, an intentionally retained non-equal-budget example.

Total parameters are P_baseline−3LHE0F0−LHE0+3LHEF+LHE. Expert-budget equality therefore does not imply model-total equality: the full router changes with E. Active expert parameters per token are 3LHKF, reported specifically as expert parameters, not a whole-model marketing active count. Holding K/E while inversely scaling F preserves these active expert parameters; holding K fixed changes them. No trained quality, capability, convergence, or equal-quality conclusion follows.

## Per-matrix execution and routes

Use one explicit route record per layer/request/position with K distinct in-range experts and finite nonnegative weights summing to one. Public synthetic_routes supplies clearly labelled balanced or hot synthetic tables. Independently validate identities and derive exact histograms; public routing_counts verifies assignment conservation and the per-expert row cap. No production observations are inferred.

For each rank, layer and owned expert, derive n from that table. Gate/up matrices are [n,H] × [H,F/TP] → [n,F/TP], down is [n,F/TP] × [F/TP,H] → [n,H]. Every matrix reports actual input/weight/output shape and 2mnk FLOPs. All local expert work sums to 6LRKHF. Zero-row experts retain weights but execute zero matrix work. Router logical matrix is [R,H]×[H,E], counted separately as 2LRHE; the optional declared all-TP/EP-replica execution total is explicitly multiplied by TP×EP, never confused with independent cohorts. Softmax/selection kernels and real kernel tile efficiency are not estimated here.

## Placement and communication reuse

Call verified public qwen235_placement without altering its config or source checks. For each rank subtract only original expert and router weight terms, then insert BF16 2×local_layers×(E/EP)×3H(F/TP) expert bytes and 2×local_layers×EH replicated-router bytes. Attention, norm, embedding/head endpoints and BF16 KV remain byte-identical to baseline. Full model unique parameter budget and physical replicated rank storage are separate fields. Requests multiply the common per-request KV, not EP replicas as separate throughput. Capacity success is necessary-only with caller workspace; actual peak remains null.

Communication preserves public qwen235_execution's same-cohort ownership: X is already local, so dispatch=0. Send TP partial outputs to each EP's TP0 for its unique active token set; send EP>0 active contributions to EP0/TP0; broadcast complete cohort across EP roots and TP replicas. Each directed message contains the actual token IDs, payload H×wire_bytes_per_element per token and declared row metadata. Histograms alone are insufficient: equal expert counts can produce different token-to-EP destination sets. PP sends one complete hidden root-to-root tensor at each boundary and separately fans out on the next stage. Attention/residual/head computations producing or consuming these boundary states remain external to this expert subaccount.

This is a message/interface count, not rounded numerical equivalence or measured throughput. Scalar/cast/packing work, actual Tensor Core tiles/utilization, communication algorithm overhead, quality and runtime are not inferred.

## Tests and scenes

Five portable tests cover two baseline topologies against public execution (route tables, wire bytes, per-rank expert work/weights/KV), direct replay, exact expert budget with changed router total, constant-vs-reduced active parameters, each individual matrix hand FLOPs, non-exact alignment, equal histogram/different destination counterexample, worst-rank capacity ±1 byte and illegal E/K/alignment/routes. Six flat scenarios cover baseline, coarse64/K4, fine256/K16, fine256/K8, E160 alignment and hot routing. All public files stay untouched.
