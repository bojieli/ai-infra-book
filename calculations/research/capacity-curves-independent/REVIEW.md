# Capacity curves independent acceptance

Accepted within the declared capacity-only scope. Independent verification passes10363 finite assertions, covering12 frozen inputs, four panels/12 series, artifact hashes, complete data regeneration, integer thresholds and staircase evaluation, all24/48/80GB public saved limits, and a synthetic three-rank changing-limiter case. Author files and public files were not modified.

The mathematical oracle computes feasible cohort size at integer capacity directly as `max(0,min_rank floor((C-W-workspace)/KV))`, then compares that result with the rendered step-point representation. For every cohort threshold through the plotted maximum plus one, it checks threshold−1, threshold and threshold+1. At a threshold n fits, n−1 is the maximum one byte below, and n remains the maximum one byte above for these real KV sizes. All visible probe points agree with `where='post'` staircase semantics, including first/last plotted transitions. This tests the complete representation rather than only interior points.

`threshold` correctly takes a new maximum across ranks for each n. A separate fixture `(W,KV)=(200,1),(100,8),(0,12)` makes three different ranks become limiting across n=0..40; the candidate agrees at every n, including ties. It does not rely on a single preselected worst rank or average device memory.

The twelve input files match the SHA recorded by data.json, and five module/data/figure bindings in author verification match actual bytes. Regenerated calculate() exactly equals frozen data.json. This is provenance binding, not an assertion that calculate() authenticates an attacker-modified result file against an immutable external trust root: regeneration intentionally captures the current input result hashes. The audit binds the reviewed snapshot.

Visual inspection of the actual figure.png confirms four readable panels, visible three-format legends, decimal GB axes, explicit eight-device layout labels,8K BF16 KV and2GiB per-rank workspace. Dense models are TP8;235B is TP2/EP4, correctly not depicted as TP8. The zero line in235B includes a weights/workspace-not-fitting region; the bottom caption explicitly says zero includes weights not fitting, and data.json separately retains zero-request/first-request thresholds. Dense curves have many small steps and appear nearly linear at full-page scale, but the data and renderer use exact staircases;235B steps are clearly visible. No clipped titles, overlapping legends or unreadable scope caption was found.

Capacity budget is not a GPU SKU recommendation; the chart does not claim throughput, quality, allocator peak, dynamic workspace or low-bit kernel support. This completes only the capacity-curve portion of Figure2-7. The requested architecture-shape diagram remains a separate deliverable.

Audited module SHA `6876c918612b90b4939f02b8169aa98dd8cd49b28cfdd0077a441471907f8699`; data SHA `767fb3b7665d37775c85c253d1de555561dd55827b4ab2bd854dc5511329ec73`; PNG SHA `ca4f3bb95c86033406c46b7e3d1e16d59a0da5548b37afd356e10c8635e14504`.

Rerun `/Users/boj/miniconda3/bin/python calculations/research/capacity-curves-independent/check.py`. Exact source and artifact associations remain in the original data/verification documents, whose hashes are verified without writing them.
