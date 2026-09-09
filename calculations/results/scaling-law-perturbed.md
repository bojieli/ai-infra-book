# C19 scaling-law — synthetic_teaching

{"data_kind": "synthetic_teaching", "fit_sse": 2.3320966169329546e-07, "holdout_rmse": 0.002779212196743132, "lifetime_calls": 365000000, "optimal_candidate_N": 4000000000.0, "task_quality_prediction": null}

| Budget FLOPs | N | D | Predicted loss |
| --- | --- | --- | --- |
| 6e+19 | 1.00799e+09 | 9.92078e+09 | 2.99789 |
| 6e+20 | 3.18753e+09 | 3.13723e+10 | 2.12605 |
| 6e+21 | 1.00799e+10 | 9.92078e+10 | 1.63577 |
| 6e+22 | 3.18753e+10 | 3.13723e+11 | 1.36007 |

| N | D at target loss | Upfront cost | Lifetime inference | Total cost |
| --- | --- | --- | --- | --- |
| 1e+09 | infeasible | infeasible | infeasible | infeasible |
| 2e+09 | 1.29839e+12 | 15580.7 | 2429.44 | 18010.2 |
| 4e+09 | 1.13734e+11 | 2729.61 | 4858.88 | 7588.49 |
| 8e+09 | 5.06952e+10 | 2433.37 | 9717.76 | 12151.1 |
| 1.6e+10 | 3.32368e+10 | 3190.74 | 19435.5 | 22626.3 |

| Record | Split | Observed loss | Predicted loss | Residual | Outside fit box |
| --- | --- | --- | --- | --- | --- |
| fit-0 | fit | 2.998 | 2.9979062 | -9.384e-05 | False |
| fit-1 | fit | 2.7071068 | 2.7073333 | 0.0002265 | False |
| fit-2 | fit | 2.502 | 2.5018673 | -0.0001327 | False |
| fit-3 | fit | 2.7051068 | 2.7050129 | -9.384e-05 | False |
| fit-4 | fit | 2.4142136 | 2.4144401 | 0.0002265 | False |
| fit-5 | fit | 2.2091068 | 2.2089741 | -0.0001327 | False |
| fit-6 | fit | 2.498 | 2.4979062 | -9.384e-05 | False |
| fit-7 | fit | 2.2071068 | 2.2073333 | 0.0002265 | False |
| fit-8 | fit | 2.002 | 2.0018673 | -0.0001327 | False |
| holdout-9 | holdout | 2.1527005 | 2.155955 | 0.003255 | False |
| holdout-10 | holdout | 1.7071068 | 1.7101343 | 0.003027 | True |
| holdout-11 | holdout | 1.502 | 1.5038479 | 0.001848 | True |

| Allocation policy (common teaching anchor) | Budget FLOPs | N | D |
| --- | --- | --- | --- |
| Kaplan-inspired | 6e+19 | 1.008e+09 | 9.9208e+09 |
| Kaplan-inspired | 6e+20 | 5.4132e+09 | 1.8473e+10 |
| Kaplan-inspired | 6e+21 | 2.9071e+10 | 3.4399e+10 |
| Kaplan-inspired | 6e+22 | 1.5612e+11 | 6.4054e+10 |
| Chinchilla-equal-scaling | 6e+19 | 1.008e+09 | 9.9208e+09 |
| Chinchilla-equal-scaling | 6e+20 | 3.1875e+09 | 3.1372e+10 |
| Chinchilla-equal-scaling | 6e+21 | 1.008e+10 | 9.9208e+10 |
| Chinchilla-equal-scaling | 6e+22 | 3.1875e+10 | 3.1372e+11 |

| Size pair | Equal-cost call count | Status |
| --- | --- | --- |
| 2e+09 / 4e+09 | 1930755100.7993648 | nonnegative_crossing |
| 2e+09 / 8e+09 | 658421066.9494942 | nonnegative_crossing |
| 2e+09 / 1.6e+10 | 265925126.77361095 | nonnegative_crossing |
| 4e+09 / 8e+09 | 22254050.024559036 | nonnegative_crossing |
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

固定来源（工具提取文本与原始PDF分开）：
- [lifetime-paper](https://proceedings.mlr.press/v235/sardana24a/sardana24a.pdf)：official_pdf；existing official raw snapshot, not newly downloaded；SHA `cd66b62454f51dcee723ba98746f7ae37e5ff0c7dce2441b9fe3d6decd188952`
- [browser-retrieval](https://arxiv.org/abs/2203.15556v1)：tool_response；raw browser-tool response, extracted text not original HTML; direct shell retrieval failed DNS；SHA `8a5bb1869d10f1faefcc58174c56dd474401af3c3098099221605879ff2788bc`
- [kaplan-paper](https://arxiv.org/pdf/2001.08361)：official_pdf；existing official paper raw snapshot; original retrieval date/version not independently established；SHA `a41bd7877fd1a6bcbba096b2619618bd2f90e02488f2365644903eb2f7c6a494`
- [chinchilla-paper](https://arxiv.org/pdf/2203.15556)：official_pdf；existing official paper raw snapshot; original retrieval date/version not independently established；SHA `3fd3632a8ef48171bd25282990221d49535d75356192f068b3b2ebe08f2aedd4`
