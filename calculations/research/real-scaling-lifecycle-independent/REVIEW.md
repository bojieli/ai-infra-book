# Real scaling lifecycle public review

Passed for the declared analytical lifecycle proxy. Public module SHA-256: `a235297fa5ad2837457764a0f29b7a19dac275f6dd4461618ee30dfaf10dc408`. No shared or author file changed.

`check.py` / `results.json` record 146 passing independent assertions. All five public variants are exactly value-equal to the original frozen result, including every law, target data budget, crossing and sampled cost curve. Scenario replay and all public delivery hashes also pass. The author's five tests were independently re-run and pass.

The independent budget check uses 60-digit Decimal arithmetic for D=D0*[B/(target-E-A*(N/N0)^(-alpha))]^(1/beta), rather than invoking the shared lifecycle helper. Each feasible candidate's training intercept agrees with 6ND*r; the per-call slope agrees with 2N*[P+(G-1)]*r. Every reported nonnegative crossing solves the difference of the two affine lines, and the difference changes sign across each positive root. Each sampled minimum is checked across the finite candidate set.

G=1 produces zero additional decode work. The allowed degenerate proxy case P=0/G=1 yields zero inference slopes and parallel/coincident lines, without invented crossing calls. It is only a zero-input work proxy; it is not proof that an actual model emits a first token without an initial state or input. An impossible target remains explicitly infeasible in all five variants, with no invented minimum. Fit-box flags agree with each law's fit N/D bounds, so small-model high-D and large-N extrapolation are retained.

The fixed abstract rate is not hardware pricing or measured efficiency. Training uses 6ND and inference uses the declared parameter-token proxy; actual attention, KV, heads, sampling and communication are explicitly excluded. Equal fitted C4 loss is not proven equal task quality. Primary and four prespecified sensitivities remain separate and are not selected by held-out residual or lifecycle cost. The output therefore supports conditional arithmetic comparison, not a deployment recommendation or universal optimum.

No blocker found for public integration within those limits. Keep the full scenario, fit provenance, extrapolation factors and stated proxy exclusions in the rendered report.
