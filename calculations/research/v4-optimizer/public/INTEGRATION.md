# Public integration candidate

Copy src/infra_calc/topics/v4_optimizer.py and tests/test_v4_optimizer.py to their corresponding public locations; imports already use infra_calc. Five portable tests locate calculations/src and overlay the candidate only. No shared changes were made.

calculate accepts model, include_mtp, orientation, wo_a_partition, sink_policy, head_mixer_policy, learning_rate, norm_epsilon, adam_step; its returned scenario can be replayed directly. The four flat scenarios are in scenarios.json. Use dedicated markdown(result), which retains all groups, per-matrix formulas/interfaces, state and provenance; no generic report schema is required.

Report evidence is archived at references/text/deepseek-v4.txt (SHA explicitly returned by calculate), with original PDF SHA and public config/header/source locks in ../source-evidence.json. Header data are read through public read_source and verified against the index through v4_checkpoint. No new weights or sources were downloaded. A production integration should retain this report evidence binding alongside public model provenance.

The default is deliberately an unresolved-group reference, with explicit row-Muon/head-AdamW scenarios supplying conditional totals. Do not describe this as the published training runtime, full optimizer implementation, or completed V4 training calculation. In particular bias load observations, distribution, precision conversion and actual allocations are absent; all are visible in scope/state.
