# C19 scaling-law — synthetic_teaching

{"data_kind": "synthetic_teaching", "fit_sse": 1.2227344030925683e-29, "holdout_rmse": 3.2934537262255428e-15, "lifetime_calls": 365000000, "optimal_candidate_N": 4000000000.0, "task_quality_prediction": null}

| Budget FLOPs | N | D | Predicted loss |
| --- | --- | --- | --- |
| 6e+19 | 1e+09 | 1e+10 | 3 |
| 6e+20 | 3.16228e+09 | 3.16228e+10 | 2.12468 |
| 6e+21 | 1e+10 | 1e+11 | 1.63246 |
| 6e+22 | 3.16228e+10 | 3.16228e+11 | 1.35566 |

| N | D at target loss | Upfront cost | Lifetime inference | Total cost |
| --- | --- | --- | --- | --- |
| 1e+09 | infeasible | infeasible | infeasible | infeasible |
| 2e+09 | 1.15886e+12 | 13906.4 | 2429.44 | 16335.8 |
| 4e+09 | 1.11111e+11 | 2666.67 | 4858.88 | 7525.55 |
| 8e+09 | 5.01719e+10 | 2408.25 | 9717.76 | 12126 |
| 1.6e+10 | 3.30579e+10 | 3173.55 | 19435.5 | 22609.1 |

| Record | Split | Observed loss | Predicted loss | Residual | Outside fit box |
| --- | --- | --- | --- | --- | --- |
| fit-0 | fit | 3 | 3 | 1.776e-15 | False |
| fit-1 | fit | 2.7071068 | 2.7071068 | 4.441e-16 | False |
| fit-2 | fit | 2.5 | 2.5 | 0 | False |
| fit-3 | fit | 2.7071068 | 2.7071068 | 4.441e-16 | False |
| fit-4 | fit | 2.4142136 | 2.4142136 | -4.441e-16 | False |
| fit-5 | fit | 2.2071068 | 2.2071068 | -1.332e-15 | False |
| fit-6 | fit | 2.5 | 2.5 | 0 | False |
| fit-7 | fit | 2.2071068 | 2.2071068 | -1.332e-15 | False |
| fit-8 | fit | 2 | 2 | -2.22e-15 | False |
| holdout-9 | holdout | 2.1547005 | 2.1547005 | -1.776e-15 | False |
| holdout-10 | holdout | 1.7071068 | 1.7071068 | -3.109e-15 | True |
| holdout-11 | holdout | 1.5 | 1.5 | -4.441e-15 | True |

| Allocation policy (common teaching anchor) | Budget FLOPs | N | D |
| --- | --- | --- | --- |
| Kaplan-inspired | 6e+19 | 1e+09 | 1e+10 |
| Kaplan-inspired | 6e+20 | 5.3703e+09 | 1.8621e+10 |
| Kaplan-inspired | 6e+21 | 2.884e+10 | 3.4674e+10 |
| Kaplan-inspired | 6e+22 | 1.5488e+11 | 6.4565e+10 |
| Chinchilla-equal-scaling | 6e+19 | 1e+09 | 1e+10 |
| Chinchilla-equal-scaling | 6e+20 | 3.1623e+09 | 3.1623e+10 |
| Chinchilla-equal-scaling | 6e+21 | 1e+10 | 1e+11 |
| Chinchilla-equal-scaling | 6e+22 | 3.1623e+10 | 3.1623e+11 |

| Size pair | Equal-cost call count | Status |
| --- | --- | --- |
| 2e+09 / 4e+09 | 1688654668.8052943 | nonnegative_crossing |
| 2e+09 / 8e+09 | 575826259.8890545 | nonnegative_crossing |
| 2e+09 / 1.6e+10 | 230357109.01499015 | nonnegative_crossing |
| 4e+09 / 8e+09 | 19412055.43093473 | nonnegative_crossing |
| 4e+09 / 1.6e+10 | None | negative_crossing |
| 8e+09 / 1.6e+10 | None | negative_crossing |

- Synthetic records are teaching inputs, not real model experiments; controls and split are explicit.
- Finite exponent search plus conditional least squares is not a global nonlinear fit or uncertainty interval.
- kND and per-token dense inference work are parameter-matrix proxies, not training_matrix full operator accounting.
- Equal predicted validation loss is only a quality proxy on the same data/tokenizer/evaluation; task equivalence is unknown.
- Costs are declared cost-unit/FLOP scenarios, not hardware prices or measured service rates. Setup may include separately supplied teacher/data costs.
- Inference excludes attention/KV, batching, communication, queueing and hardware efficiency changes. No MoE/RL/test-time scaling fit.
- Continuous N,D ignore architecture granularity and data supply beyond optional budget bounds; lifetime optimum is only over supplied sizes.
- Sensitivity envelope is deterministic model-assumption sensitivity, not a confidence interval; no paper-point reproduction claimed.
