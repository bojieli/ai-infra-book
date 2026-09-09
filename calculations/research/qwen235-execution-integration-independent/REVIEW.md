# C33 Qwen235 public integration acceptance

Public integration passes **33/33 independent wiring/equality assertions**. The public module is byte-identical to the independently reviewed candidate: `a4ee2e24fa01ea4854f974a26b8266c2d3c4bb37571ad9d418de58d33a7b48e2`. No new mathematical proof is inferred from integration checks; the existing route/ownership/byte/capacity review remains in `qwen235-execution-independent/REVIEW.md`.

All seven public flat scenarios equal the frozen scenario records exactly. Every public calculate result equals its complete frozen JSON object, and every actual `qwen235-execution --inputs ...` CLI JSON equals that same result. Dedicated Markdown dispatch matches the module renderer for all seven cases, and a real default CLI `--format md` call matches it too. No numeric tolerance or selected-summary-only comparison is used. Capacity-failure scenarios remain present.

The current public test file runs **5/5 tests with zero skips** under the available Conda Python/Torch environment, including the FP64 MoE TP/EP reconstruction oracle. Its optional missing-Torch skip does not alter the public mathematical module. The test output is preserved in `tests.log`.

Every scenario still reports full request runtime and actual peak as null, retains the expert-only scope, same-cohort/no-fabricated-dispatch premise, reference arithmetic versus wire dtype distinction, and necessary-only capacity. The phase-barrier budget is not converted into an end-to-end latency or measured hardware claim.

The public reproduction loop consumes `qwen235_execution`, removes only `id` from each flat scene, invokes calculate and saves both report forms; results-index enumeration is present. The chapter6 generator has the `C33-qwen235-execution` insertion. This finite inspection does not replace the parent's running full-book reproduction.

`verification.json` binds the candidate, public module, CLI, report, reproduction, test and book-scenario files. `checks.json` lists the assertions; `check.py` replays them and writes only this independent directory. Neither public nor candidate files were modified.

## Explicit cross-Python boundary

The exact integration comparisons above ran on Python3.11.4, matching the frozen candidate environment. A separate actual CLI replay under Python3.14.7 confirms that **only** `summary.conditional_phase_barrier_bound_seconds` differs in the seven scenarios, by at most1.0408340855860843e-17 seconds. Every per-phase bound, message, matrix/scalar count, capacity, route and other field remains exact. For this single final summed field the declared cross-version acceptance uses `math.isclose(rel_tol=1e-13, abs_tol=1e-16)`; no other field receives a tolerance. `check_python314.py` removes only that named field, requires exact equality of the remaining entire JSON, and then checks its tolerance. Detailed values are in `python314-verification.json`. This is a narrow interpreter summation difference, not a mathematical or source-input change; public code was not changed to hide it.
