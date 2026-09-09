Implemented the standalone C20 calculation and deliverables in the task directory. The original repository was left unchanged.

- [Module](training_history.py): explicit nominal/active 6ND proxies, D/N and growth ratios, conditional GPU-hour durations, maximum-count lower bounds, separate additive stages and alternative branches, and caller-supplied lifecycle costs. Unknown inputs remain null.
- [Independent tests](test_training_history.py): **12 tests passed**, covering numerical results, scope distinctions, missing inputs, validation, field preservation, and evidence failures. [Test log](test-results.txt).
- [Example inputs](example-inputs.json), [runner](run_example.py), and [computed output](example-output.json).
- [Archive verification](archive-verification.json): **all 16 archived files passed SHA-256 and byte-count checks**.
- [Integration instructions and limitations](INTEGRATION.md).

The example runner also completed successfully for all 13 catalog models. No new evidence, official prices, hardware efficiency assumptions, or model weights were fetched. CLI/reproduction integration and the full repository test suite remain outside this handoff; archive verification establishes byte identity against the prepared lock, not a fresh audit of every report.