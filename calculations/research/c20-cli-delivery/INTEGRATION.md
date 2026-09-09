C20 historical training investment — standalone handoff

The implementation is [training_history.py](training_history.py). It follows the existing `infra_calc` envelope (`schema_version`, `calculation`, `model`, `scenario`, `sources`, `summary`, `assumptions`), uses exact rational strings for ratios/days/costs, and returns integer proxy FLOPs. It has no third-party dependencies, network access, model downloads, or write operations. Only the example runner and tests write files.

Run from this directory:

```sh
python3 -B -m unittest -v test_training_history
python3 -B run_example.py /Users/boj/book/ai-infra-book/calculations
```

The first command runs 12 independent tests. The second verifies all 16 archives before computing 13 model rows and writes `example-output.json`, `archive-verification.json`, and byte-identical catalog/lock snapshots beside the runner. `example-inputs.json` contains the complete scenario arguments; the `project` argument identifies the calculations directory. Paths in the existing lock resolve relative to that directory, not its `configs` subdirectory. Copied locks retain their original paths and need the original archive tree (or an equivalent layout) to resolve.

For future integration, copy this module into `calculations/src/infra_calc/topics/training_history.py`. The in-package call `calculate()` resolves `infra_calc.paths.PROJECT`; standalone calls use `calculate(project=...)`. Import it in a future CLI/reproduction change and forward `comparisons`, `duration_scenarios`, and `lifecycle` as structured JSON lists. The existing catalogs need no edits. To integrate the independent tests, change their module import to `from infra_calc.topics.training_history import calculate, verify_archives` and replace their absolute `PROJECT` with the existing test suite's repository-relative calculations path. No CLI, reproduction, configuration, outline, plan, or shared repository files were changed in this handoff.

The output preserves the entire catalog, each input row, stage report, source record, and scenario, including unknown nested fields. New calculations appear outside their input objects. Catalog and lock SHA-256 digests identify the exact inputs. Every archive is checked against both its expected digest and byte count; missing or altered evidence stops calculation. Repeated source IDs for PDF/text pairs are intentional and verified individually. Every model/stage source ID must resolve to verified evidence. All sources remain in the output, including the separately locked Llama 3.1 card that supplies the 405B GPU hours; no unsupported per-field source mapping is fabricated.

The accounting rules are explicit:

- `proxy_flops` is 6ND only for `nominal_dense_proxy` or `active_parameter_proxy`. `tokens_per_parameter_exact` uses that same N. Neither is a complete architecture-specific training operation count. Reported training FLOPs remain separate; their ratio to the proxy is a consistency comparison, never MFU.
- `conditional_constant_count_days_exact` is GPUh/count/24. A reported configuration requires constant allocation for this interpretation. A reported maximum additionally produces `calendar_lower_bound_days_exact`. `measured_calendar_days` is always null. No start/end dates are inferred. Caller count intervals yield conditional day intervals only when GPU hours are known.
- DeepSeek-V3's final-stage sum is 2,788,000 GPUh and is checked against its reported total. An unknown component produces a null sum; a mismatch returns `reported_total_matches=false` for review. Its 14.8T tokens remain paired only with 2,664,000 pretraining GPUh. Qwen3's 17,920 and 1,800 GPUh remain alternative experiment branches, without any additive total.
- Comparisons return parameter, token, and proxy-work growth for explicitly chosen pairs. They do not aggregate GPU hours across devices, fit scaling laws, attribute quality differences, or claim controlled experiments.
- Lifecycle scenarios use only the selected catalog row's GPU hours times a caller price, plus caller service usage times a price per declared unit, plus caller `other_cost`. Currency, service unit, and scope are mandatory. Prices and usage have no defaults; zero must be explicit. Even zero times an unknown input stays null. The result is a scoped scenario cost, not a complete historical training bill. Service work can use requests, tokens or another explicit unit, provided its price uses the same unit. No currency or unit conversion is performed.

`example-inputs.json` uses a fictitious SCENARIO_CREDIT and artificial prices solely to demonstrate exact arithmetic. It supplies no official commercial price or efficiency assumption. The unknown Qwen training hours keep its total unclosed. A caller needing additive-stage or alternative-branch financial scenarios should explicitly prepare a separate scoped extension; this module's lifecycle selector intentionally prices only catalog model rows.

Validation completed:

- `python3 -B -m unittest -v test_training_history`: 12 tests passed; the final run is captured in `test-results.txt`.
- `python3 -B run_example.py`: completed, all 16 archive SHA-256 and byte-count checks passed and all 13 catalog models processed.
- Tests cover fixed independent numerical expectations, growth, allocation intervals, maximum-count semantics, missing inputs, cost exactness, stage separation/mismatches, unknown-field preservation, malformed numbers/scenarios, corrupted/missing/unlinked evidence, and JSON serialization.

Unresolved limits: this is the bounded calculation handoff, not shared CLI/reproduction integration or book figure generation. Archived hashes prove byte identity against the prepared lock, not independent verification of the lock's trustworthiness or a fresh transcription audit of every report. Some locked URLs are mutable; the recorded archive SHA, snapshot and revision metadata identify the bytes used. No new raw evidence was fetched. Total MoE parameters absent from the prepared catalog are not inferred; the active proxy is not a capacity estimate. Hardware normalization, actual occupancy, elapsed dates, MFU, full training scope, quality equivalence, deployment behavior and commercial prices remain unmeasured or undisclosed. The repository's full test suite was not run because no repository integration was performed.
