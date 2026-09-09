# Real held-out C4 scaling fit delivery

The statistical protocol admits eight source-matched real observations from the single Datablations paper: six fit points and the predeclared two N >= 2e9 holdout points. The original strict protocol and all 33 exclusions remain in adapted.json; this statistical protocol treats different evaluation budgets as estimates of the same official C4 validation population.

Official README and eight matching final logs establish GPT-2 BPE vocabulary/merges, C4 validation prefix and full validation split. Training uses the separately designated C4 training subsamples. This is documentary split separation, not an independent raw-document deduplication proof. The 146m14b14b point is excluded because its 11.3B launch budget conflicts with the 14B reported label. Other unavailable-log rows remain outside this source-verifiable subset.

Primary law: L = 1.2112421706 + 1.2512538553 (N/1e9)^(-0.10) + 0.5234301354 (D/1e10)^(-0.45). Fit selection uses only the six training rows. This is a finite-grid descriptive fit to a small subset, not reproduction of the full paper fit.

Training SSE: 0.000599723345; two-model held-out RMSE: 0.0193445386 nats/token.

| Held-out point | Observed | Predicted | Residual |
|---|---:|---:|---:|
| 2b855b55b | 2.574117 | 2.582723 | 0.008606 |
| 8b7178b178b | 2.336741 | 2.362710 | 0.025969 |

| Prespecified sensitivity | Held-out RMSE |
|---|---:|
| shape_N | 0.019172970 |
| declared_D | 0.022612448 |
| both | 0.022440654 |
| wider_grid | 0.019344539 |

N is the author-reported parameter estimate. Appendix S shape-derived N is a separate sensitivity, not an exact checkpoint parameter inventory. Script D is an intended budget, not an independently counted achieved token total. The two held-out models retain reported D where training-budget evidence is unavailable; the D sensitivity is therefore partial. C=6ND is an analytical proxy, not measured compute.

The primary alpha is at the declared grid lower edge; the prespecified wider grid retains the same solution. Six training observations cannot justify strong universal scaling or compute-optimum claims. Evaluation sampling variance is unavailable, same-model points and validation subsets can be correlated, and the holdout extrapolates N. No confidence interval, measured training speed, or unique globally optimal training allocation is claimed. The additional boundary module reports its finite-design identifiability separately.

Replay: `PYTHONDONTWRITEBYTECODE=1 python calculations/research/scaling-real-points/adapt_statistical.py`; tests: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s calculations/research/scaling-real-points -p "test_*.py" -v`. Six tests pass, including held-out perturbation independence. The adapter calls the unchanged public scaling_law.fit and the separately frozen research/scaling-boundary-fit/boundary_fit.py diagnostic. No shared source/config changes.

Pythia discovery remains under pythia/: its exact code path uses the same full document pool for train and logged validation. It is explicitly excluded from the held-out generalization objective. Its provisional local boundary implementation is superseded by the parent boundary_fit module; do not integrate that temporary implementation.
