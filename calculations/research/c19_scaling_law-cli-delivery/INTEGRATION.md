# C19 independent delivery

Original repository was read only. No commits, resets, configuration changes, model weights, or additional workers were used. Everything delivered here is staged for the owner to review and integrate; original C19 remains unchecked.

## Contract and coverage

Read exact `outlines/03-推理与训练负载.md` §3.2.3, its extension, `case-studies/scaling-history.md`, the capability-density section in `research/token-cost-2023-2026/report.md`, and original PLAN C19. Input hashes are in `sources/repository-inputs.json`. No AGENTS.md was found in the inspected repository or ancestor locations.

| Original requirement | Delivered | Remaining scope |
| --- | --- | --- |
| Controlled N,D,C,loss fit | Nine fixed teaching fit records; three held-out records; explicit shared control ID; conditional QR least squares over declared alpha/beta grid | Import and audit actual paper experiment points; this is not a paper reproduction |
| Holdout and extrapolation | One interpolation and two extrapolation holdouts; signed residuals/RMSE, fit box/factors; refit exponent sensitivity predictions | Statistical uncertainty, repeat-run noise, independent recipe/data shifts |
| Compute-budget optimum | Analytic continuous solution, optional N/D box, infeasibility check; independent finite enumeration | Architecture rounding, constrained data supply and deadlines beyond the box |
| Kaplan/Chinchilla assumptions | Common-anchor allocation comparison: N grows as C^.73 or C^.5; D determined by kND=C | Full Kaplan loss/learning-curve fit and separate paper datasets are not implemented |
| Training + lifetime inference | Target-loss D for each candidate N; prefill/decode proxies and cost rates; calls/day × lifetime; setup cost; pairwise crossings and sampled cost curves | Real service rates, equivalent downstream task quality, detailed distillation/teacher ledger |
| Figure 3-7 | Deterministic JSON contains fit, holdouts, cost-curve and sensitivity points; Markdown tables | Render and review the publication figure; no plotted artifact claimed |
| Llama 3 two-stage method | Task-quality prediction explicitly null | Actual validation-loss-to-task-performance calibration |
| Optional local model training | Not run | Optional GPU experiment remains optional; no fabricated measurements |

## Formulas and units

`L = E + A (N/N0)^(-alpha) + B (D/D0)^(-beta)`, with positive A,B,alpha,beta and nonnegative E. N is a declared dense parameter proxy and D counts processed training tokens. N0,D0 only normalize coordinates. The sample generator uses E=A=B=1 and alpha=beta=0.5, not coefficients attributed to any published experiment.

With `Q=C/(k N0 D0)`, stationary `x=N/N0` obeys `x^(alpha+beta) = alpha A Q^beta / (beta B)`. Positive exponents give a unique minimum in log N. Clamp to the feasible N interval implied by supplied N/D bounds. This solver uses a full-budget equality; it rejects boxes that cannot spend the budget exactly. The box is not a general inequality-constrained solver with unspent compute.

For target loss L*, `D=D0 [B/(L*-E-A(N/N0)^(-alpha))]^(1/beta)` where the denominator is positive; otherwise that size is infeasible. Lifetime cost is `kND × train_rate + setup_cost + calls × (prefill_proxy × prefill_rate + decode_proxy × decode_rate)`. Rates are hypothetical cost units per FLOP, not dollars or observed GPU rates. Pairwise cost equality solves two affine curves; a nonnegative pair crossing need not lie on the lower envelope of all candidates.

`units.positive_int/positive_number` are reused. `training_matrix.py` was read to retain FMA=2 and its distinction between 6ND and actual operator work. No artificial scaling-law model is passed to Qwen's model adapter. Actual C records are retained and recorded/kND ratios reported; they are not silently replaced or fitted as an independent variable. The fit predicts N,D loss under controls; budget optimization separately assumes kND.

The finite exponent search only selects by training SSE. Holdouts never choose coefficients or exponents. Admissible alternatives are refitted on training points and displayed as a deterministic sensitivity sweep, not a confidence region or all-equally-plausible models. Nonpositive conditional coefficients are excluded; this is not constrained global nonlinear regression. QR rejects numerically rank-deficient designs. Extreme inputs can still overflow floating-point arithmetic and should be rescaled; JSON output disallows NaN/Infinity.

Unknown input fields are preserved by deep copy in `scenario`; unknown per-record fields survive prediction output. Required computational fields are validated. Controlled-record imports must supply IDs, splits, shared control IDs, positive N,D,C_flops,loss, explicit sources and a suitable exponent grid. A shared ID is an assertion by the caller, not independent proof of identical data, tokenizer, optimizer, or evaluation.

## Run and integration

Run from this task directory:

```sh
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/Users/boj/book/ai-infra-book/calculations/src:.
python3 make_scenarios.py
python3 scaling_law.py --inputs scenarios/teaching.json --output results/teaching.json
python3 scaling_law.py --inputs scenarios/teaching.json --format md --output results/teaching.md
python3 -m unittest discover -s tests -v
```

Also supplied: perturbed and zero-demand scenarios and their JSON/Markdown outputs. The generator is only for teaching inputs; do not run it over an imported real dataset. No third-party numerical dependency is required. For integration, copy `scaling_law.py` into `calculations/src/infra_calc/topics/`, change its absolute `infra_calc.units` import to `..units` if desired, add a CLI `scaling-law --inputs --format --output` branch, and route its Markdown through this module's renderer. Preserve the surrounding CLI, source lock, scenarios and report unknown fields. Add the tests after adapting the module import and fixture path to repository conventions. Do not replace the original PLAN or rewrite existing unrelated work.

Suggested §3.2.3 addition after experiment 3-8: “C19 教学计算提供受控合成点拟合、独立留出误差、预算最优和相同预测验证损失下的生命周期费用。合成点不代表论文实验；Kaplan／Chinchilla 的分配指数仅作同锚点假设对照。实际论文点复现、任务质量映射与图3-7仍待补，C19暂不整项勾选。” Link to the integrated scenarios/results and add the actual CLI command once wired. Outline and skeleton regeneration are owner-side work; neither was changed here.

## Evidence and limitations

Official [Kaplan paper](https://arxiv.org/html/2001.08361v1), §6.1/table 6, supplies the .73 model-size allocation exponent; its non-embedding and batch-adjusted compute convention differs from a generic dense proxy. The [Chinchilla abstract](https://arxiv.org/abs/2203.15556v1) supports equal scaling of parameters and training tokens. Their shared anchor here is synthetic and does not reproduce either original frontier or compare real model quality.

[Beyond Chinchilla-Optimal](https://proceedings.mlr.press/v235/sardana24a.html) motivates including lifetime inference demand. The supplied analytical cost model is an independently derived teaching simplification. Sources are archived with SHA256 and dates in `sources/manifest.json`: original raw PDFs copied from the read-only repository plus unmodified browser-tool response JSON. Direct shell downloads failed DNS. Browser output is extracted tool evidence, not original HTML bytes; copied Kaplan/Chinchilla PDFs have a copy date but their original download date/version was not independently established. No new raw HTML download is claimed. `sources/scaling-laws.txt` is a derived pdftotext view used to check .73/.27; the PDF is the raw artifact.

The implementation task is complete within this staged teaching scope, while original C19/experiment 3-8 retains the explicit gaps above. No actual experiments, model performance, prices or hardware calibration were fabricated.
