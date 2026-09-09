# Independent boundary fitter and eight-point statistical adapter review

Status: real eight-point adapter passes this review. Boundary solver passes the ordinary-domain mathematical checks but needs the finite-range changes below before a general public API is accepted. No shared or author file was edited.

## Evidence and completed checks

`check.py` and `results.json` bind the exact boundary and adapter SHA-256. All 266 assertions pass: 80 independent SciPy NNLS objective comparisons (including dependent columns and constant columns), feasible nonnegative coefficients, exact frozen statistical-output replay, six-fit/two-holdout split, actual evaluation-log hashes, delivery bindings, primary and boundary holdout-loss perturbation invariance, and every row of all three coordinate sensitivities. Different valid coefficients on a rank-deficient design are not treated as failures when their fitted objective agrees.

The finite-grid selection only uses fit loss. Zero A or B correctly disables the corresponding exponent's identifiability; the compute-optimum flag is expressly formula-domain eligibility, not statistical identification. The grid and N >= 2e9 split remain unchanged. No holdout residual is used to replace the primary fit with a sensitivity run.

## Required numeric boundary fixes

1. A nonrepresentable grid candidate currently aborts all later candidates. Construct five records with N=(i+1)*1e-300, D=(i+1)*1e10, loss=3, unique string IDs, one control, first four split=fit and last split=holdout. Grid [(2,.3),(.2,.3)] raises OverflowError. Grid [(.2,.3)] alone returns E=3, A=B=0, SSE=0. Classify the bad candidate and continue; if all fail, raise a descriptive ValueError. Invalid input such as a negative exponent is a separate input error and need not be silently skipped.
2. QR uses sqrt(sum(x*x)); a single column [1e200,2e200,3e200,4e200] and target [1,2,3,4] incorrectly raises dependent-column ValueError, although the coefficient 1e-200 is representable and the one-column design is well-conditioned. Use a scaled norm (math.hypot), column/target scaling as needed, and distinguish numerical range failure from rank deficiency. Evaluate power features through log-coordinate differences to avoid intermediate ratio under/overflow.
3. Finite positive loss=1e308 in five otherwise ordinary records raises raw OverflowError; nonnegative_fit with infinite targets instead returns infinite SSE. Validate public helper dimensions/finiteness, check coefficients/residual/objective/output are finite, and reject an actually unrepresentable objective explicitly. Do not let inf participate in min-selection. For a mathematically representable RMSE use scaled norm rather than residual**2; if the declared SSE field cannot be represented, classify that explicitly.

The frozen eight-point dataset does not trigger these ranges. These are public numerical-contract issues, not a reason to exclude real data or raise source comparability requirements.

## Statistical adapter and source semantics

The eight records are the nine archived final-log matches minus 146m14b14b, whose launch budget is 11.3B versus the reported 14B coordinate. This is a source/budget exclusion, not loss-based selection. The two held-out IDs are 2b855b55b and 8b7178b178b. The other six are fit observations. Primary output replays exactly with alpha=.1, beta=.45 and held-out RMSE=.019344538649 (rounded display).

Each included log confirms GPT2BPETokenizer, the same vocabulary/merges paths, C4 validation dataset prefix and full 0:1 validation split. As established in ../scaling-real-points-independent/STATISTICAL-C4-REVIEW.md, this supports the same documented held-out C4 population; different finite evaluation sample counts are noisy estimates, not identical deterministic evaluation or known independent errors. Neither local paths nor this source review prove independently deduplicated raw documents; the adapter does not claim that.

N is the author's reported PARAMS_MAP estimate, including embeddings by the paper's Appendix S convention, not a checkpoint-exact inventory. The N sensitivity correctly uses 12*l*h²+13*l*h+(50257+2048)*h from logged h/l. Primary D is the reported coordinate. Available declared launch-token budgets are used only in the D sensitivity; absent budgets for the two held-out points retain reported D explicitly. No achieved-token count is invented. All three coordinate sensitivity predictions preserve the predeclared IDs and splits.

C_flops=6ND is an analytical coordinate normalization, not measured training work; public presentation must keep this qualification. The wider-grid and coordinate alternatives must remain sensitivity outputs. Correlated same-model points, unknown evaluation variance, sparse coordinates and edge-grid solutions remain limitations, not grounds for silently changing the sample or split.

## Integration boundary

After numeric range fixes, re-run the independent script against the new boundary snapshot and regenerate the adapter's boundary result and delivery bindings if its source hash/result changes. Preserve primary numerical results. Public migration must carry all referenced source/data hashes (not merely the adapter Python file), actual matching logs, reported coordinates, control evidence and protocol. Parent owns public migration; this directory supplies review and reproducible checks only.

## Public migration follow-up

`public_check.py` / `public-results.json` add 398 passing checks against the frozen `scaling-real-points/public` delivery. Primary and all four sensitivity laws, fit SSE, holdout RMSE, candidate/rejection inventories, fit bounds and every prediction/residual match the independent research result exactly. All portable delivery bindings match. Every selected evaluation log and available budget script appears in the direct public source lock; data.json and the original notebook are also locked. The public module re-parses notebook literals and raw-log controls/geometry/shape/budgets instead of trusting derived coordinates alone. No additional migration math or provenance blocker was found. The generic boundary numeric-range findings above still await the parent's fix.

## Final numeric fix review — resolved

Final boundary SHA-256: `aa0b7af7e43c9c61688785996ea34381569653035cfa6d5ea25e6824fddf33b8`. All original numeric issues above are now resolved. Re-run: 270 independent assertions plus six explicit range probes; author's eight tests also pass. The previously failing constant 1e308 loss fits E=1e308/SSE=0, the nonrepresentable grid point is classified and a later valid candidate selected, the large single column returns coefficient 1e-200, and infinite targets are explicitly rejected. A further independently found representable four-heldout-residual RMSE case is fixed with max-scaled RMS: four residuals of magnitude 1e308 now report finite RMSE 1e308. Rank deficiency and numerical range errors are distinct. Final JSON finiteness is checked.

Primary and all four real-data sensitivities remain exactly unchanged. The revised boundary diagnostic still selects alpha=.1/beta=.45. Only ordinary floating-point rounding changed: E=1.2112421705646341, A=1.251253855283189, B=.5234301353650039; SSE=.0005997233448120859; holdout RMSE=.01934453864899902. These match the original positive-law solution within 4e-14 absolute in coefficients. Public tests should compare these distinct solvers with a numerical tolerance rather than dictionary equality.

The old adapter delivery binding for its boundary dependency is necessarily stale and deliberately excluded from the final 270-check rerun; the final independent result binds the new SHA directly. Parent must regenerate the dependency binding and boundary diagnostic artifact when migrating. No remaining blocker was found within the declared finite-grid numerical/statistical scope.
