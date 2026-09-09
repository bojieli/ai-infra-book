Delivered the C19 teaching calculation package entirely within the task directory. The original repository was not modified.

- [scaling_law.py](/tmp/aiinfra-codex-parallel-20260909/c19_scaling_law/scaling_law.py): controlled synthetic fit, held-out errors, analytic compute-budget optimum, matched-loss lifetime costs and crossover counts, and extrapolation sensitivity.
- [Scenario inputs](/tmp/aiinfra-codex-parallel-20260909/c19_scaling_law/scenarios/teaching.json): baseline, perturbed-data, and zero-demand variants, with generated JSON and Markdown results.
- [Independent tests](/tmp/aiinfra-codex-parallel-20260909/c19_scaling_law/tests/test_scaling_law.py): **13 passed**, covering analytic solutions, finite enumeration, budget conservation, holdout isolation, validation, and unknown-field preservation.
- [Integration notes](/tmp/aiinfra-codex-parallel-20260909/c19_scaling_law/INTEGRATION.md): formulas, reproduction commands, original-scope coverage, proposed outline wording, and unresolved gaps.
- [Verification record](/tmp/aiinfra-codex-parallel-20260909/c19_scaling_law/results/verification.json): all three scenarios reproduced deterministically in JSON and Markdown; four archived evidence hashes verified.

In the synthetic example, the cheapest supplied size changes from **8B with zero inference demand to 4B at 365 million lifetime calls**, at equal predicted validation loss.

Original C19 should remain unchecked pending actual paper-point reproduction, downstream task-quality calibration, the rendered publication figure, and repository integration. No real model experiments or measured costs are claimed. Direct downloads failed DNS; the evidence manifest distinguishes copied official PDFs from archived browser-tool output.