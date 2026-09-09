# Independent Qwen8 training nonmatrix accounting review

Verdict: no remaining mathematical blocker for the declared partial training graph after compact-gradient initialization and AdamW coefficient clarification. Final reviewed source/public module SHA is c43fd76439fc336def5d9b604413b34d52f3271321f0720fddf6aefbd41d3025; both files are byte-identical, and the final manifest verifies. The reviewer writes only this directory.

## Counts, not only derivatives

check.py supplies21 independent counted-algorithm/model/lifetime cases. count_ce.py adds6 explicitly instrumented forward/CE cases. The Scalar counter executes only the declared primitive formulas and records each add/subtract/multiply/divide separately; it does not trust finite-difference correctness as evidence of operation count.

- RMS forward is4D+1 ordinary operations and one rsqrt per row. Backward dx is6RD; gamma shared across R rows adds(2R-1)D, with independent reduction per layer's parameter copy. Hidden and Q/K shared-head forms were checked, including R1/D1.
- Scaled causal softmax backward is5K-1 per valid row, including score-scale multiplication. Saved probability forward ordinary work is4K-1. Q/KV query grouping does not multiply gamma parameter copies.
- SwiGLU backward is6 ordinary operations per element for du, da and dg. Recompute adds exactly one multiplication and one sigmoid per element; existing projection gradients are not multiplied again.
- Mean CE explicitly computes saved probabilities: S(3V+2) ordinary forward operations, including mean reduction, and S(V+1) backward operations with subtraction only at the target. Exp/log/max comparisons remain separate.
- AdamW is14P+6 ordinary operations, P sqrt and two pow operations. The shared complements/decay/bias-correction expressions now execute outside the numerical helper's parameter loop. FP32 master/grad/m/v reads16P bytes, updated master/m/v writes12P, BF16 model writes2P; the existing parameter-state capacity is retained without duplication.

The numerical helpers are value/gradient oracles, not literal instruction-count kernels: some use Python sum or subtraction of zero beyond the optimized declared reduction formula. Counts apply to the explicit CONTRACT algorithms, not Python execution. Fourteen author tests were rerun with zero skips, including FP64 autograd/finite differences and AdamW checks.

## Matrix boundary, mask and GQA

Twelve combinations of B/T/S, dense/compact head and save/recompute compare the entire training_matrix_original object to an independent public call and check all nonmatrix totals against fixed Qwen8 dimensions. Dense head retains allBT rows when S shrinks; compact reduces only head matrix rows. The original training_matrix already states GQA gradient reduction is outside its per-head GEMMs. The added2*L*B*T*K*D*(Q/K-1) is therefore consistent with the declared per-query-head dK/dV outputs followed by reduction; it must not be blindly added to a backend convention that already fuses grouped contractions.

The reviewer found missing compact hidden-gradient initialization in the first candidate. Author added compact_hidden_gradient_zero_fp32_bytes=4*BT*H for compact only, before scattering the selected S rows. B2/T3/H4096 independently gives98304 bytes while dense gives0. This closes the declared zero-on-unsupervised-rows path; label identities still are not fabricated. All other unenumerated casts/indices/backend traffic remain in explicit incomplete scope.

## Saved objects and remaining boundary

We reconstruct live objects by identity from every allocation/release event, verify no double allocation or unowned release, recompute the peak independently, and require an empty set at the end. SiLU recompute temporarily retains s/a together with saved g/u through the local backward. The saved subset excludes matrix inputs, Q/K/V necessities beyond listed objects, gradients, allocator and reduction temporaries. It is not a complete model activation peak or a universal lower bound for alternative algorithms.

Residual and branch merges are explicitly additive joins: two residual joins, one gate/up input join and two Q/K/V input joins per layer. Embedding scatter includes additive contributions to a separately zeroed dense gradient. No fresh scalar backward is inferred by multiplying the entire forward by three. Matrix-plus-scalar is an accounted subtotal; complete training FLOPs, HBM and step latency remain null. V4 training, full lifecycle, distributed work, clipping, accumulation and optimizer initialization remain outside this candidate, so original experiment3-6 is not closed.
