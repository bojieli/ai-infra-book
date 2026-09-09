# Real C4 scaling fit

Held-out C4 population token loss, variable finite evaluation samples

Eight official source-matched observations; six fit, two fixed N >= 2e9 holdout. Different evaluation budgets estimate the same validation population, with unknown variance and potentially correlated errors. Reported N/D are estimates; this subset does not reproduce the full paper fit.

| Point | Split | N | D | Observed loss | Eval tokens |
|---|---|---:|---:|---:|---:|
| 2b855b55b | holdout | 2810000000 | 55000000000 | 2.574117 | 104857600 |
| 8b7178b178b | holdout | 8670000000 | 178000000000 | 2.336741 | 104857600 |
| 1b1100m100m | fit | 1096300000 | 100000000 | 6.611002 | 13107200 |
| 14m100m100m | fit | 14100000 | 100000000 | 7.278144 | 13107200 |
| 196m1b51b5 | fit | 201236224 | 1500000000 | 3.929866 | 13107200 |
| 1b11b51b5 | fit | 1096300000 | 1500000000 | 3.680017 | 52428800 |
| 1b112b12b | fit | 1096300000 | 12000000000 | 2.925644 | 52428800 |
| 1b191b91b | fit | 1096300000 | 91000000000 | 2.636805 | 52428800 |

L = 1.2112421706 + 1.2512538553 (N/1e9)^(-0.1) + 0.5234301354 (D/1e10)^(-0.45).

Fit SSE 0.000599723345; fixed holdout RMSE 0.0193445386 nats/token.

| Point | Predicted loss | Residual | Outside fit N/D box |
|---|---:|---:|---|
| 2b855b55b | 2.582723 | 0.008606 | True |
| 8b7178b178b | 2.362710 | 0.025969 | True |
| 1b1100m100m | 6.608798 | -0.002204 | False |
| 14m100m100m | 7.285119 | 0.006975 | False |
| 196m1b51b5 | 3.909269 | -0.020597 | False |
| 1b11b51b5 | 3.680231 | 0.000214 | False |
| 1b112b12b | 2.933245 | 0.007601 | False |
| 1b191b91b | 2.644816 | 0.008011 | False |

| Prespecified sensitivity | Status | Holdout RMSE |
|---|---|---:|
| shape_N | fit | 0.0191729701704482 |
| declared_D | fit | 0.02261244803056678 |
| both | fit | 0.022440654230306577 |
| wider_grid | fit | 0.019344538649002794 |

The shape-N sensitivity uses Appendix S estimates; declared-D uses available launch budgets and retains reported D where unavailable. Neither establishes exact checkpoint parameters or achieved token counters. The wider predetermined exponent grid is not selected by held-out error. C=6ND is analytical proxy compute.

The boundary diagnostic permits zero coefficients and reports rank/identifiability; it does not replace the positive-law fit or establish a universal optimum. No confidence interval, independent error model, or measured runtime is asserted. Official train/validation split separation is documentary evidence, not independent document deduplication proof.

Excluded explicit conflict: 146m14b14b has an 11.3B declared launch budget versus a 14B reported label. Other original rows lack matching archived final logs in this delivery. Pythia logged validation is excluded because its source path evaluates the training document pool.

## Boundary diagnostic

```json
{
  "law": {
    "E": 1.2112421705646341,
    "A": 1.251253855283189,
    "B": 0.5234301353650039,
    "alpha": 0.1,
    "beta": 0.45,
    "N0": 1000000000.0,
    "D0": 10000000000.0
  },
  "fit_sse": 0.0005997233448120859,
  "holdout_rmse": 0.01934453864899902,
  "rejected_candidates": [],
  "zero_coefficients": [],
  "compute_optimum_eligible": true,
  "full_design_rank_deficient": false,
  "exponent_identifiability": {
    "alpha": null,
    "beta": null
  },
  "fit_coordinate_counts": {
    "N": 3,
    "D": 4
  },
  "scope": [
    "Finite-grid constrained regression diagnostic, not proof of a universal scaling law or generalization.",
    "Zero A or B removes dependence on its exponent; a grid tie does not identify that exponent.",
    "Same control is an input assertion; a held-out model split is not evidence that evaluation documents were held out of training.",
    "compute_optimum_eligible only checks positive A/B formula domain; it does not establish reliable exponents, extrapolation, or fit identifiability.",
    "No confidence interval, noise weighting, or synthetic observations are inferred. All real residuals remain visible."
  ]
}
```

## Evidence

| File | SHA256 | Source |
|---|---|---|
| sources/scaling-real-points/README.md | 122f89e4e3987acf6191db35631795e567f9a79815ea98f0557709e816471b7b | https://raw.githubusercontent.com/huggingface/datablations/13701315b163f1c54642b94ad237b2699187c3ee/README.md |
| sources/scaling-real-points/hub/lm1-2b8-55b-c4-repetitions/2b855b55bc4/3431998.out | 0d25cd8e1a124d1ccb5cd1cc0965707645161c57bcea67a90d101d60e2dd8bce | https://huggingface.co/datablations/lm1-2b8-55b-c4-repetitions/resolve/e4c25f9f9ffb88c4ca9750167078b23f62708e64/2b855b55bc4/3431998.out |
| sources/scaling-real-points/hub/lm1-8b7-178b-c4-repetitions/8b7178b178b/3430821.out | e87423b94776d752571a5ca59183110e5c2e0a43d6f9a28e533403b7fb05be69 | https://huggingface.co/datablations/lm1-8b7-178b-c4-repetitions/resolve/b52a3bc845b34002d16fa597bc69004a6162e77b/8b7178b178b/3430821.out |
| sources/scaling-real-points/hub/lm1-misc/14m100m100m/logs/3163413.out | f48ea24d544feb59e27ee9eb23ef43d7617c4673cb6f4f7fe13cf3ab48ec7e50 | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/14m100m100m/logs/3163413.out |
| sources/scaling-real-points/hub/lm1-misc/14m100m100m/sbatch_14m100m100m.sh | b5d8ae2e78e17de7e3470ab60149766346e32abf6eee2fcb0884861238cbaa2c | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/14m100m100m/sbatch_14m100m100m.sh |
| sources/scaling-real-points/hub/lm1-misc/196m1b51b5/logs/3163481.out | e779a9e84551753deb738842cd90ffd6876ffbb73fbf0f2e21f5bfe7b15f0d46 | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/196m1b51b5/logs/3163481.out |
| sources/scaling-real-points/hub/lm1-misc/196m1b51b5/sbatch_196m1b51b5.sh | 23325c1e51fe35e70c017514c5ea25a928288f0f06d5078686b0e4c0e26556d3 | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/196m1b51b5/sbatch_196m1b51b5.sh |
| sources/scaling-real-points/hub/lm1-misc/1b1100m100m/3324218.out | 63ed0dda91136068abdffe287579cde4be96f5293b8c119b1937f0e641ca409f | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b1100m100m/3324218.out |
| sources/scaling-real-points/hub/lm1-misc/1b1100m100m/sbatch_1b1100m100m.sh | a9c30c85bd4f1fb51afd04bc8e23839b58f38850d749ddae806c53eb87f358af | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b1100m100m/sbatch_1b1100m100m.sh |
| sources/scaling-real-points/hub/lm1-misc/1b112b12b/2820797.out | 729ed7c037d714775c03a90e91cb6876738810b8cbe7a7d344d86f881601d1df | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b112b12b/2820797.out |
| sources/scaling-real-points/hub/lm1-misc/1b112b12b/sbatch_1b112b12b.sh | 656ac35c5429ced88899098933aa994654d898a8ca82bda69b9361848fbf29fa | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b112b12b/sbatch_1b112b12b.sh |
| sources/scaling-real-points/hub/lm1-misc/1b11b51b5/logs/2809896.out | 02eb3e6900d7771d3ba74e1d521f7599163e484ea3793c40c57f5c2ccc43c59c | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b11b51b5/logs/2809896.out |
| sources/scaling-real-points/hub/lm1-misc/1b11b51b5/sbatch_1b11b51b5.sh | 73d3eb3edeb0c1210c2dd85b93899ac0f5271eca0ec37a27d1471a960b85cb8d | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b11b51b5/sbatch_1b11b51b5.sh |
| sources/scaling-real-points/hub/lm1-misc/1b191b91b/logs/2833162.out | 1d72b2653f06c40ea18f44d6a22c5c125c75ad659f151daebd9478672ff876db | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b191b91b/logs/2833162.out |
| sources/scaling-real-points/hub/lm1-misc/1b191b91b/sbatch_1b191b91b.sh | d0513f76c3c18c72b821a7e71efe6ce8de8d1ba98f76e19ed279487b7a41a32a | https://huggingface.co/datablations/lm1-misc/resolve/ddd985fd2b46aba0b83b0e6a2c6f2af1511c66f0/1b191b91b/sbatch_1b191b91b.sh |
| sources/scaling-real-points/utils/parametric_fit.ipynb | 6c65d270e70c944a9ac90f5f1213a4584e1ff9d6d2781cd86900663f4ab17db9 | https://raw.githubusercontent.com/huggingface/datablations/13701315b163f1c54642b94ad237b2699187c3ee/utils/parametric_fit.ipynb |
| sources/scaling-real-points/independent/supplement.pdf | 86e21e48a1f9eb6aa09d8bf07c8ffe99e947ae06adf0fc050a6bbd44e026db0f | Independent extraction/review; official supplement URL in n-loss-sources.lock.json |
| sources/scaling-real-points/independent/supplement.txt | 7407f4d52df1d445a7d1705154107b3f6c7f2f0044730d31deb5dad490ae2dc7 | Independent extraction/review; official supplement URL in n-loss-sources.lock.json |
| sources/scaling-real-points/independent/STATISTICAL-C4-REVIEW.md | 4e5de5804332791c1443646ca88b08b56b048bde5ccb3ccd8d8ca063f7580054 | Independent extraction/review; official supplement URL in n-loss-sources.lock.json |
| sources/scaling-real-points/independent/statistical-C4-eight-point-evidence.json | 397623fc5e8b2a77ee602acb561543be19967bfb4b1a810ee770d109b5ac5df2 | Independent extraction/review; official supplement URL in n-loss-sources.lock.json |
| sources/scaling-real-points/independent/n-loss-sources.lock.json | e5cd8aa964f262b11e96c2d3eb0021c4fdce5ae7fb63d747bdb078fb8bbd7889 | Independent extraction/review; official supplement URL in n-loss-sources.lock.json |
| configs/scaling-real-points/data.json | fb134f0ee5f54ae2812e64d28878f7f0a9865e9a554c0fe559219e4f1ea9b77f | Derived eight rows; public records() verifies notebook and logs |
