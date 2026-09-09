# Independent review of integrated C19 scaling-law calculator

Reviewed 2026-09-09. **The analytic budget optimum and lifecycle crossing equations are correct in ordinary finite arithmetic. All three integrated scenarios reproduce their archived JSON. Four robustness findings remain, reproduced by seven independent regression expectations.** No source changes are proposed as prerequisites for interpreting the supplied teaching scenarios; the findings matter when accepting other inputs through the same public functions.

Scope: `/Users/boj/book/ai-infra-book/calculations/src/infra_calc/topics/scaling_law.py`, integrated scenarios and results, integrated tests, units validators, CLI dispatch/error handling, README description, and the scenario generator read as provenance evidence. I did not rerun the generator or reproduce prior implementation work. The reviewed module SHA-256 is `882b7c8299f821899849e27fee8963434331c4b39f9d05fdb65e367b864e16e9`; other hashes, environment, commands and exit statuses are in [verification.json](verification.json).

I attempted to read the repository root `AGENTS.md`; it does not exist. A recursive search excluding `.git` found no `AGENTS.md` in the repository. Checked parent paths `/AGENTS.md`, `/Users/AGENTS.md`, `/Users/boj/AGENTS.md`, and `/Users/boj/book/AGENTS.md` also supplied no instructions. Your explicit read-only/output-directory constraints governed this work. All deliverables and process captures are in this review directory. Repository imports used `PYTHONDONTWRITEBYTECODE=1`; the independent test script also sets `sys.dont_write_bytecode=True`. No repository edits, git mutations, downloads, further workers, messages to others, or persistent goals were used.

## Findings requiring correction or an explicit narrower API contract

Line references below refer to the reviewed integrated module, not the research delivery copy.

| ID | Priority | Finding | Reproduction |
| --- | --- | --- | --- |
| B1 | Medium | Exact admissible zero-floor fits can be rejected due to roundoff | `test_B1_zero_floor_exact_fit_must_be_admissible` |
| B2 | Medium | One unusable exponent pair aborts a grid containing a usable fit | `test_B2_bad_grid_member_must_not_discard_good_fit` |
| B3 | Medium | Intermediate arithmetic loses representable answers, including silent loss-term erasure | Three `test_B3_*` tests |
| B4 | Medium for direct helpers; lower exposure through `calculate` | Non-finite derived costs can yield a false optimum and crossover status | Two `test_B4_*` tests |

**B1 — zero loss floor is allowed but numerically rejected (lines 81–88).** Keep the teaching N,D design and set every observed loss to `(N/N0)^(-0.5)+(D/D0)^(-0.5)` with grid `[[0.5,0.5]]`. The exact law has `E=0,A=B=1`, which `validate_law` explicitly allows. The conditional solver returns approximately `E=-3.552713678800501e-15,A=B=1.0000000000000024`; the strict `E<0` check discards the only candidate. `fit` raises “no positive admissible fit.” This is a boundary-roundoff defect, distinct from a deliberate rejection of a substantively negative unconstrained coefficient. Use a scale-aware boundary treatment and recompute the accepted fit error; do not indiscriminately clip truly negative estimates.

**B2 — rejection belongs to a candidate, but currently kills the whole search (lines 78–86).** The teaching records fit with `[[0.5,0.5]]`. Adding the valid positive pair `[1e-15,0.5]` makes the transformed N column effectively constant under the solver's conditioning threshold. `_linear` raises, and `fit` discards even the already computed good candidate. This happens regardless of which pair is first. Rejecting a singular transformed design is correct and is explicitly commented in the source; aborting every other fit is the robustness issue. Either skip/report unusable candidate pairs and fail only when none remain, or explicitly require that every declared pair be numerically identifiable. The current input validation only requires finite positive exponents. The test specifies the more useful candidate-local rejection contract. Do not loosen the rank threshold merely to make this case pass.

**B3 — finite input validation is not stable arithmetic (lines 33, 80, 106–107, 140).** Three concrete cases:

- `compute_optimum` with `E=A=B=1,alpha=beta=0.5,N0=D0=1e200,C=6e200,k=6` has the representable solution `N=D=1e100`, predicted loss approximately `2e50`. But `k*N0*D0` overflows, so `Q=0` and taking its logarithm raises `ValueError`.
- `loss` with the unit law except `N0=1e200`, evaluated at `N=1e-200,D=1`, should return approximately `1e200`. The ratio underflows to zero and raises `ZeroDivisionError` when raised to a negative exponent.
- `loss` with `E=0,A=1,B=1e-300,alpha=beta=0.5,N0=1e-200,D0=1`, evaluated at `N=1e200,D=1`, should return approximately `1e-200`. The N ratio overflows to infinity and its power becomes zero, silently returning `1e-300`. All input numbers and the true result are finite. A final `allow_nan=False` check cannot detect this finite but wrong result.

These are numerical range defects, not an objection to a dense teaching proxy. They involve deliberately extreme inputs; supplied scenarios are unaffected. Log differences and sums should precede multiplication/division/exponentiation, and truly unrepresentable final outputs should be rejected deliberately. The target-token power expression has the same structural exposure, but no additional target-token overflow regression was run; that part is a code-inspection concern.

**B4 — direct helpers return invalid derived values (lines 33, 140–158).** With `E=A=B=1e308`, otherwise unit law and `N=D=1`, `loss` returns `inf`. With `alpha=beta=1,E=A=B=N0=D0=1`, sizes `[3,4]`, target `1.5`, and finite `train_per_flop=1e308`, both lifecycle upfront costs overflow. The helper returns `optimal_N=3,status='finite_candidate_optimum'`. Its crossover numerator is `inf-inf=NaN`, but it labels the crossover `negative_crossing`. In exact arithmetic the training FLOPs are 108 versus 96; for the test demand, N=4 has lower total cost. Returning the first candidate after overflow is not a meaningful optimum.

There is an important containment boundary: **`calculate` does call `json.dumps(result, allow_nan=False)` and rejects the overflowing-cost scenario**. That protection passed an independent test. B4 affects exported direct helper calls and misleading intermediate classification, not successful serialization of this particular scenario through the integrated command. The current tests specify clear `ValueError` rejection when final quantities cannot be represented. The CLI catches `ValueError`, `KeyError`, and `OSError`, but not `ZeroDivisionError` or `OverflowError`; inspect this when standardizing numeric errors. No pathological CLI traceback test was run.

## Independent mathematics

Let `x=N/N0`, `y=D/D0`, `a=alpha>0`, `b=beta>0`, and `Q=C/(k*N0*D0)>0`. On the full-budget constraint, `xy=Q` and

`L-E = A*x^(-a) + B*Q^(-b)*x^b`.

Set `t=log(x)`. Differentiating with respect to t gives

`dL/dt = -a*A*exp(-a*t) + b*B*Q^(-b)*exp(b*t)`.

The second derivative is strictly positive: `a^2*A*exp(-a*t)+b^2*B*Q^(-b)*exp(b*t)>0`. The objective tends to infinity at both ends of the real t line. There is therefore one global minimum, with

`x* = [(a*A)/(b*B)]^(1/(a+b)) * Q^(b/(a+b))`,

`N*=N0*x*`, `D*=C/(k*N*)`.

This matches lines 105–108 algebraically. Consequently N scales with compute exponent `b/(a+b)` and D with `a/(a+b)`. Equal N,D scaling follows when a=b; a constant tokens-per-parameter ratio is not implied for arbitrary unequal exponents. E shifts loss but does not affect allocation.

For closed positive bounds, feasibility on `kND=C` reduces to

`N in [max(Nmin,C/(k*Dmax)), min(Nmax,C/(k*Dmin))]`,

omitting absent restrictions. Strict convexity in log N justifies clamping the unconstrained optimum to that interval. The implementation does this correctly. This is a **full-budget equality** problem. If a box has capacity below C, reporting no full-budget allocation follows the docstring, even though a separate `kND<=C` problem could use less than the available budget. I do not classify that documented distinction as a bug.

The test oracle independently brackets the derivative's root with 180 bisection steps, rather than copying the closed-form implementation. It checks 60 seeded asymmetric laws/budgets, both kinds of bounds, a singleton feasible point, normalization invariance, and the compute exponents.

For target loss T and a supplied size N, define `g(N)=T-E-A*(N/N0)^(-a)`. Since B>0, there is a finite positive solution only when g>0, and

`D(N)=D0*(B/g(N))^(1/b)`.

At g=0 the target is approached only as D tends to infinity; rejecting finite feasibility is correct. For a quality constraint `L<=T`, this D is minimal, and with nonnegative training cost it is a cost minimizer at fixed N (possibly non-unique when training cost is zero).

Write `U(N)=k*N*D(N)*train_rate+setup_cost` and

`v(N)=N*(prefill_multiplier*input_tokens*prefill_rate + decode_multiplier*output_tokens*decode_rate)`.

For H lifetime calls, `J_N(H)=U(N)+H*v(N)`. Thus pair i,j crosses at

`H*=(U_j-U_i)/(v_i-v_j)`.

Only H*>=0 is relevant to the modeled domain. Equal slopes give coincident lines if upfront costs also match, otherwise parallel lines. The implementation's signs and finite-arithmetic statuses are correct. These are continuous call counts; real integer call decisions change around floor/ceiling values, and an arbitrary pairwise crossing need not lie on the overall minimum-cost envelope.

The independent lifecycle oracle uses exact Python `Fraction` arithmetic for `L=1+2/(N/3)+3/(D/5)`, target 2, sizes 8,10,16,32, nonzero setup and unequal prefill/decode costs. Then `D=15/(1-6/N)`, `U=1.5*N*D+7`, and `v=6.5*N`. It checks costs and the selected size at five demands and all six pairwise crossings. Separate checks cover parallel/coincident costs and the immediately adjacent floating-point target above an asymptote.

## Fit, holdout, grids, and scenarios

No automatic fit/holdout selection leakage was found. Rows used by `_linear`, candidate SSE selection, and fit-box bounds are exclusively `split='fit'`. Changing holdout coordinates, losses, IDs, C_flops, and count leaves the fitted law, every candidate, SSE, and bounds unchanged in the independent test. Holdout RMSE changes as expected. Generator metadata is not used to recover coefficients, and recorded C_flops is diagnostic rather than a fit weight or consistency constraint.

Limits of that result: holdouts are still validated and required. Malformed or numerically extreme holdouts can prevent an overall result; this is not evidence that they trained the law. Repeated physical records under different IDs can be labeled holdout and accepted, and the calculator cannot establish independence of evaluation data or whether a human chose the grid after looking at holdout errors. The `controlled_records` assumption explicitly calls provenance a caller assertion. The top-level control_id is metadata; consistency is checked among record control_id values. These are provenance limitations, not an observed hidden fit pathway.

The exponent grid is a list of explicit pairs, not a requested continuous search or an automatically generated Cartesian product. All nine supplied pairs are admissible. Reversing them preserves the teaching winner; duplicate pairs produce duplicate candidates. Excluding the generating pair selects a declared alternative with nonzero SSE, as expected. In exact ties Python `min` preserves the first candidate; floating-point near-ties need not be exact ties. A four-fit-record design with only two levels on each axis can fit multiple exponent pairs closely, so “at least four” is a validation minimum, not identifiability evidence for all five free model parameters. Conditional unconstrained least squares followed by positivity filtering is also not a global constrained nonlinear optimizer. These limits are consistent with the published assumptions. B1 is the narrower numerical boundary defect within that algorithm.

| Scenario | Fit SSE | Holdout RMSE | Optimal supplied lifetime size |
| --- | --- | --- | --- |
| teaching | 1.2227344030925683e-29 | 3.2934537262255428e-15 | 4e9 |
| perturbed | 2.3320966169329546e-7 | 0.002779212196743132 | 4e9 |
| zero-demand | 1.2227344030925683e-29 | 3.2934537262255428e-15 | 8e9 |

All select `(alpha,beta)=(0.5,0.5)`. The exact scenario's generator uses that same equation and includes that pair in the grid, so near-perfect recovery is a software control, not independent empirical confirmation. The perturbed scenario adds the repeating `[-0.002,0,0.002]` pattern to records. In the fit design this is aligned with D levels; it is structured perturbation, not random noise or statistical validation. This matches its explicit deterministic/no-uncertainty label. Zero demand changes calls_per_day only; its larger selected size is the discrete training-cost optimum. Its separately supplied `call_counts` still draw nonzero-demand curves, which are a sensitivity sweep rather than a contradiction.

The code clearly labels kND and inference work as dense parameter-matrix proxies; excludes attention/KV, batching, queueing, communication and changing hardware efficiency; distinguishes predicted validation loss from task equivalence; treats rates as scenario cost units; limits lifetime optimization to supplied sizes; and calls exponent sensitivity deterministic rather than a confidence interval. These are **documented teaching limits**, not findings that the implementation has violated its stated model. Historical allocation policies share a synthetic anchor and are explicitly not paper replications. Optional N,D bounds apply to budget optima, not to lifecycle data supply or those illustrative policy curves.

## Tests actually run and remaining unknowns

- Integrated suite: **13/13 passed**, [integrated-tests.txt](integrated-tests.txt).
- Independent suite: **24 cases: 17 passed, 7 expected failures**, [independent-tests.txt](independent-tests.txt). The expected-failure wrappers make this audit runnable without concealing that the seven proposed requirements are unmet.
- Strict known-bug run: **7/7 unsuccessful, 3 assertion failures and 4 errors; exit 1**, [strict-regressions.txt](strict-regressions.txt). This supplies actual traces for B1–B4, not speculative failing tests.
- Integrated CLI: teaching, perturbed and zero-demand JSON all exit 0 and match stored parsed JSON exactly. Teaching Markdown exits 0. Captured outputs are `cli-*.txt`; exit statuses and commands are in [verification.json](verification.json).
- Every scenario calculation traversed the archive size/SHA checks successfully. This verifies bytes against the lock, not scientific correctness or source version provenance.

To rerun from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 test_independent_scaling_law.py -v
PYTHONDONTWRITEBYTECODE=1 python3 test_independent_scaling_law.py --strict KnownBugRegressions -v
```

The script accepts `AI_INFRA_BOOK` to change the read-only repository root. It requires only Python's standard library. Tests ran on Python 3.14.7/macOS arm64; other supported Python versions were not tested. No full repository suite, real training experiment, external paper verification, hardware measurement, randomized adversarial fit survey, or comprehensive malformed-schema fuzzing was performed. I did not test all underdetermined/correlated designs or quantify QR error near its rank threshold. No patch has been implemented or validated; focused proposals are in [PATCH_PROPOSALS.md](PATCH_PROPOSALS.md). Shared source may change after the recorded hashes; these conclusions apply to the observed version.
