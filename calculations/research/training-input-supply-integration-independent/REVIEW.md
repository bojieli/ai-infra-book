# Training input supply public integration acceptance

Public integration passes77 checks and5 installed public tests, zero skipped. Public module SHA is `b8d3a9796cac527b789f9530be247f93aeca50ba98021e078b6ac61dfb239d07`; it is byte-identical to the frozen migration candidate.

The entire `calculate` and `schedule` function ASTs agree with original SHA `c431fc0f37221bd92e18f3b9f2fa63122476493c266eebda58955f53fc17ba1e`, previously independently reviewed by hardware_audit. That review's configuration, qwen3 model and pipeline_schedule dependency hashes still match. Both original and migration artifact manifests pass. This audit verifies integration against that reviewed mathematics; the auditor prepared the migration and does not present this as a second independent derivation of the scheduler.

Five public scenario objects exactly match every field of their original frozen results, including rational event times, dependency edges, resource labels, source evidence, buffer lifetimes, checkpoint14P bytes and all scope exclusions. Their result.scenario values replay exactly. For every result, the dedicated Markdown JSON block parses back to the entire result object, confirming no fields are omitted.

Actual `calculations/calc.py training-input-supply --inputs ...` was executed in ten subprocesses, JSON and Markdown for each of five scenarios. All exit successfully; JSON matches original frozen results and Markdown matches the complete renderer. The five installed `test_training_input_supply.py` tests pass without skips. Commands used `/Users/boj/miniconda3/bin/python`.

The finite semantics remain those reviewed: next-fit packing without sample splitting, one CPU worker, caller-provided service/bandwidth assumptions, bounded host/device/snapshot reservations, exact rational list scheduling and whole-write storage contention. A completed modelled write is the declared durability boundary, not proof of a particular filesystem's persistence guarantees. No allocator peak or measured training throughput is inferred. No remaining integration discrepancy was found.

Reproduce this audit with `check.py`. Evidence lives in `results.json` and `tests.log`. Public files and source originals were never modified; execution began after the parent declared the public module/CLI/scenarios stable.
