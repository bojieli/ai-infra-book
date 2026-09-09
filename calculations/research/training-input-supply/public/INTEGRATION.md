# Public migration candidate

Copy `src/infra_calc/topics/training_input_supply.py` and `tests/test_training_input_supply.py` into their corresponding calculations directories. The module uses normal infra_calc imports; no research path is needed. `scenarios.json` contains five flat scenario records with id plus calculate keyword inputs; the CLI/reproduce dispatcher chooses the calculation type. Keep the existing calculation identity `qwen8-training-input-supply` unless the dispatcher deliberately supplies an alias.

`calculate` and `schedule` function ASTs are exactly unchanged from the independently reviewed original. Only research import bootstrapping was removed, formatting expanded for readability, and a complete `markdown(result)` renderer added. All five frozen JSON results and result.scenario replays agree exactly. The new renderer includes every result field, exact rational time, buffer lifetime, source and conditional scope. The copied existing result Markdown files remain the original complete leaf tables.

Direct portable tests: `/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/research/training-input-supply/public/tests -v` (5 pass, 0 skip). Migration evidence: run `verify_migration.py`. Portable tests locate real infra_calc dependencies and overlay candidate topics when running before integration.

No new sources are required. Existing `sources.lock.subset.json` is copied unchanged. For any subsequent public source-lock expansion, frozen result provenance must be regenerated deliberately; do not alter historical author results to conceal a changed dependency set.

Finite contract remains unchanged: caller-supplied preparation/consumption service and bandwidth, next-fit packing, exact logical wire bytes, declared14P checkpoint state, whole-write shared-storage contention, bounded host/device/snapshot reservations. Durability means completion of the modelled write. No allocator peak, actual filesystem durability guarantees, measured Qwen throughput or distributed filesystem implementation is inferred.

No shared src/config/scenarios/CLI/reproduce/PLAN files were modified by this migration.
