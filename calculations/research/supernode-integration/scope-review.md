# C36 original-scope acceptance mapping

This review uses chapter 6.6 and its extension, including experiments 6-9/6-10 and figures 6-8/6-9. It does not treat a passing calculation suite as whole-book coverage.

- Four 64 GiB nodes and 80/48/32/32 GiB demands: memory_pool_access enumerates local expansion, impossible whole-job migration, conditional splittable placement, and 16 GiB borrowing.
- Fixed-workset access frequency: exact 16 GiB reads, declared rates, latency/concurrency-window supply, and periodic backlog condition. Runtime queues are outside the fixed-service assumption.
- Copies and failure domains: one/two/three copies, physical capacity and 45 deterministic failure sets; no statistical reliability claim.
- Growing KV: growing_remote_kv supplies official Qwen8/Qwen3.6 position accounting, initialization, append replication and explicit commit epochs. The original fixed-workset exercise delegates complete KV service benefits to section 9.5.
- Experiment 6-10: two official dense models, cohorts 1/4/8, deadlines 80/250/600 ms, three recovery profiles; capacity rejection, restart traces, inclusive deadlines, ceil minimum valid count, all-reserved-card cost divided by SLO-valid completions, ties and empty selection.
- Physical interpretation is explicit in both original chapter and extension: each TP group occupies one independent physical supernode (1x8, 2x4, 4x2 cards), hosts one service replica, with no cross-group request dependency. Failure of card 0 takes its group out of service. This is a teaching placement/failure assumption, not a consequence of TP alone.
- Figure 6-8: the caption now explicitly defines “KV fetch” as reading remote data, not migrating the whole snapshot back into an already full local node. The three diagram states preserve local shortage, borrowing and fetch, with remote access frequencies.
- Figure 6-9: public exact deadline staircases from the same completed-request traces; gaps indicate capacity/SLO ineligibility. PNG/SVG/data matched audited candidate bytes on first render.

Service milliseconds, recovery duration and fees are declared independent inputs, not inferred hardware benchmarks or prices. Actual partial-stage FLOPs remain unknown; completed abandoned stages are counted separately. Real transfer/state recovery protocols, runtime feasibility and quality experiments are not claimed.

C36 can close for this finite teaching calculation scope once public reproduction, figure validation, tests and outline verification pass. This does not close C32 placement/runtime gaps, section 9.5 complete KV service, or the overall book goal.
