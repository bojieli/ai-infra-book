# C33 minimal public wiring after mathematical review

No repeat of the frozen mathematical review is required unless the module changes. Its reviewed SHA is `a4ee2e24fa01ea4854f974a26b8266c2d3c4bb37571ad9d418de58d33a7b48e2`.

1. Copy `research/qwen235-execution/public/src/infra_calc/topics/qwen235_execution.py` to the matching public topic path, and its portable test to public tests. Normal infra_calc imports already work. The existing Qwen235 placement/config/index provenance is reused; `sources.lock.subset.json` is a subset reference, not a patch that should duplicate source rows.
2. Add `qwen235-execution` CLI with `--inputs` JSON, `--format json|md`, and `--output` using the established dedicated-topic pattern. Call `calculate(**inputs)` directly; do not coerce this mixed phase result through a dense Scenario.
3. Route report schema `qwen235-cohort-execution-v1` to the module's `markdown`. Preserve complete route tables, token identities, per-rank experts, messages and explicit unknown fields. A generic dense-model table would discard essential ownership information.
4. Add the **seven flat scenario records** from `public/book.append.json` under one reproduction group, stripping only `id` before calling calculate. Save JSON/MD and link them in the results index. Retain the explicit capacity-failure cases; do not remove failing configurations to imply all deployments fit.
5. Add one compact chapter6.3 result paragraph with a valid existing anchor, CLI example, zero-dispatch premise and conditional scope. Update C33's candidate-pending phrase only after public integration succeeds; keep C33 unchecked. The automatic source/code/config manifest should include the public module and scenarios; no research-Python dynamic import is required.
6. Integration-only acceptance: module SHA/AST unchanged; seven candidate/public JSON objects equal; one CLI JSON and Markdown report dispatch; all seven scene IDs visible; existing source subset verified. The prior mathematical/route/±1B review remains referenced rather than rerun as a new independent proof.

## Limits that must survive CLI, report and chapter wording

- **Same cohort:** EP is not DP. Replicated attention outputs already provide every owner's X, so no additional token dispatch occurs. This cannot be applied to sharded-token attention or another placement without rebuilding the ownership graph.
- **Expert subaccount:** the result does not include attention/router/embedding/head computation or their collectives, scalar service, index formation, packing or casts. PP messages represent externally completed block hidden values. Output is ready for the head, not a completed request or logits.
- **Arithmetic versus transport:** BF16 parameter storage and configurable wire bytes do not make the reference expert arithmetic a BF16 backend. FP32 real-arithmetic partial weighting is not a claim of bitwise equivalence to weighting after reduction.
- **Conditional schedule:** supplied rates/startups are teaching assumptions. The named layer/communication barriers and full-duplex per-rank service define a conditional subaccount bound, not measured GPU/network performance or a whole-request latency prediction. Preserve `full_request_runtime_seconds=null`.
- **Capacity:** same-layout BF16 weights + requests×KV + declared workspace is only the necessary reservation contract. A pass does not prove workspace suffices; message/route allocations are not inferred. Preserve actual peak null and failed capacity scenarios.
- **Route evidence:** keep synthetic balanced/hot labels and complete caller routes. Expert histograms cannot establish destination-token sets; logical route metadata is not an assumed resident GPU copy.

The public result must not sum the old independent all-to-all/dedup traffic on top of this graph. Their distinct token-source premises would double-count or invent dispatch. A later four-model C33 extension and calibrated runtime remain separate work.
