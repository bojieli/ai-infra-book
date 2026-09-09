# C52 independent deliverable

Implemented analytical TP/EP reconfiguration, state migration, amortization and a full **declared** deployment-cost ledger for chapter 9.6. No original repository file or shared entrypoint was modified. No GPU/model execution, engine support validation, current vendor price lookup, weight download, or performance measurement was performed.

Files:

- `reconfiguration.py`: independent calculation module using existing `infra_calc` interfaces.
- `test_reconfiguration.py`: 11 standard-library tests, including 49 small reconstruction combinations and comparisons against existing Dense/EP placement accounting.
- `scenarios.json`: seven complete input records; unknown fields are preserved by deep copy.
- `run_scenarios.py`: local runner and evidence archiver; writes only beside itself.
- `results/`: per-scenario JSON with transfer pieces, physical-device capacity, lower bounds, runtime gaps, amortization and deployment ledger; `summary.json` is a compact index.
- `evidence/sources.json`: original official configuration lock records, including URL, immutable revision, SHA-256, original download date and local copy timestamp. Raw config files are copied without modification and verified against the original lock. No new upstream claims or evidence were fetched.
- `evidence/dependency_hashes.json` and `evidence/reading_manifest.json`: read-only source and chapter/experiment inputs fingerprinted for integration review.
- `test-results.txt`: final passing test output. `test-results-initial.txt` preserves the first failed run, which found an adapter field mismatch (`Weight.copies`, not `repeats`). The mismatch was corrected before the passing runs.

Run from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_reconfiguration
PYTHONDONTWRITEBYTECODE=1 python3 run_scenarios.py
```

Python imports the existing checkout at `/Users/boj/book/ai-infra-book/calculations/src` read-only. The runner sets `sys.dont_write_bytecode` before importing it. No dependency installation is needed. This deliverable depends on that checkout's existing model adapters and locked sources; it is not a separately packaged replacement for `infra_calc`.

## Accounting contract

One model, one inference group, BF16 weights and BF16 KV, PP=DP=1. Physical IDs are explicit and ordered EP-major then TP-major. Layout `pp`/`dp` values other than 1 are rejected. Dense requires EP=1. MoE experts use the same contiguous quotient/remainder ownership as `weight_handoff`; nonexpert weights replicate across EP. TP uses the same query, FFN and vocabulary axes as `dense_placement`. GQA heads are indivisible and replicate when required. Every routed expert is counted; top-k active parameter labels never replace full weight bytes.

In this declared TP×EP topology, the same request batch and KV replicate across EP groups. This is a placement model, not a claim about an actual engine's DP/EP attention groups. Independent EP request batches or a different expert-TP topology require a different state mapping.

For each weight template, an invariant sharding axis defines integer intervals. Other dimensions, dtype width and layer copies become `unit_bytes`. A down/output projection slice is a logical rectangle across rows, **not** a contiguous checkpoint file range. Packing, strides, fusion, transposition, padding and physical file reads remain runtime terms. Layer templates combine equal placements arithmetically; layer identities remain distinct.

For each target interval, intersect source boundaries and choose a valid local copy first, then a source by device-name order. Each destination byte is assigned exactly once even when source weights/KV replicate. Network bytes count direct unicast sends once; matching receive totals are not added again. This is a deterministic plan, not a minimum-traffic or optimal-bandwidth schedule. In particular, contiguous ownership changes can migrate experts between old devices as well as onto new devices.

`state_identity_verified=true` asserts that layer, KV-head, token, position, format and model version match. The module does not perform that verification. `same_weight_version=false` is rejected. Auxiliary state is an explicit immutable flat byte snapshot, partitioned with `checkpoint_reshard.partition_ranges`; its size is not inferred from a model. Supply token logs, RNG/sampling state, scheduler state, request metadata and checkpoint state through a separately validated serialization contract. It is not a training optimizer model.

`state_policy=migrate` transfers old KV; `replay` transfers no KV but reserves the rebuilt target KV and leaves replay time explicit. Both require a quiescent consistent snapshot. No online pre-copy/dirty-state loop or recovery from unavailable source devices is implemented. Replay is not resampling: preserving already delivered token IDs and sampling state is an external correctness requirement.

## Bounds, capacity and deployment costs

The transfer lower bound is

`max(total network bytes / aggregate fabric rate, maximum device sends / sender rate, maximum device receives / receiver rate)`.

Each bandwidth is a hypothetical effective bytes/s input. Missing rates leave the complete bound null; any known partial bound is separately labeled. A no-network plan has zero transfer time bound even without rates. Link-hop traffic, congestion, source choice optimization, protocol startup and memory-copy costs are not inferred.

The declared serial switch subtotal adds that transfer bound to explicitly supplied drain, group setup, repacking, validation, compilation/graph, cutover, replay and queue-clearance seconds. Extra runtime fields are included; a supplied unknown extra term keeps the complete subtotal null. This is an assumed serial schedule built on a necessary transfer bound, not a predicted engine-ready time. It must not be read as TTFT, ITL or SLO output. Overlapping measured phases need a dependency DAG instead of entering them twice here.

Capacity is checked for each physical device as `old resident + full target resident + declared extra live bytes` before releasing old allocations. Local retained payload still gets a new materialized target buffer in this policy; it is not assumed to alias. This deliberately includes double buffers even for a no-op layout. Old-only devices retain their old allocations during the handoff. Caller-supplied extras cover workspace, graphs, transfer scratch and other allocations. Missing capacity stays null; a declared fit does not prove backend feasibility or full actual peak.

The cost ledger requires ten named categories: startup, steady service, routing/cache, migration, warm overlap, recovery/replay, failed attempts, backlog clearance, network/storage and host/control plane. Each category contains disjoint `quantity × rate` charge rows in one common declared currency. Use `[]` for an explicit zero, `null` for unknown. Extra categories are included. Quantities can be GPU-seconds, CPU-seconds, GB, request attempts or another documented billing unit. The caller must account for both simultaneously retained pools, failed work, cache preparation and teardown as applicable, and avoid charging the same resource-time interval in two categories.

Missing categories/row inputs prevent a full declared cost or cost-per-SLO-valid-request result. The known subtotal includes complete categories only; an incomplete category is excluded as a whole. The denominator is explicitly supplied SLO-valid completed requests, never all attempts; zero/unknown yields null. These are arithmetic contracts, not real prices, performance predictions or automatic estimates from migration bytes.

Time and money amortization are independent inputs. For nonnegative incremental overhead H and positive per-step saving s, break-even is `ceil(H/s)` and strict benefit is `floor(H/s)+1`. Zero or negative savings have no positive benefit threshold. Missing overhead/savings remain null. Savings must describe the same scheduled-token workload, model/quality, output policy and complete cost boundary. The thresholds do not establish that savings exist. Runtime gaps are never silently substituted with transfer lower bounds in amortization.

## Scenarios and example results

All scenario bandwidths, 80 GB capacities, 2 GiB extras, state bytes, durations and charges are teaching inputs. The results include:

| Scenario | Network bytes, weights + migrated state |
|---|---:|
| Qwen3-8B TP4 → TP8 | 16,449,646,080 |
| Qwen3-8B TP8 → TP16, GQA replication | 20,458,065,664 |
| Qwen3-235B EP8 → EP16 | 578,994,499,328 |
| Qwen3-235B EP16 → EP8 | 425,805,745,920 |
| Qwen3-30B EP7 → EP5 | 42,127,592,418 |
| Qwen3-30B TP2×EP4 → TP4×EP2 | 48,153,755,648 |
| Qwen3-8B disjoint TP4 replay | 16,383,324,160 |

For Qwen235 EP8→16, the routed expert bytes received by the eight new devices equal half the full routed weight bytes. **Total** migration is larger: old-device reassignment, nonexpert replication, KV and auxiliary state also count. Contraction does not imply zero migration, and missing/failed sources cannot be treated as retained copies.

The disjoint replay scenario alone supplies all runtime and cost terms as a worked arithmetic example. Its full declared cost is `1921/125 = 15.368` hypothetical credits and cost per 1,000 declared SLO-valid requests is `1921/125000 = 0.015368`. This scenario does not establish actual SLO validity; its denominator is an assumption. The six other ledgers intentionally remain incomplete.

## Integration notes and remaining C52 work

Reviewed PLAN C52, chapter 9.6 and its extension, `parallel-switching-and-state.md`, and the 9-10 startup/cache-mechanism experiment notes. Experiment 9-10 has no `09-06` directory; chapter numbering and experiment numbering differ. Existing startup measurements were read for scope and were not imported as reconfiguration timings. The existing observations explicitly distinguish successful storage reads from useful KV reuse, so the module does not infer a cache hit from a transfer.

A maintainer can place this module under `infra_calc/topics/` and change the absolute package imports to relative imports if desired; keep `calculate(scenario)` or add an adapter that passes the whole dictionary to preserve unknown fields. Add scenarios/report dispatch through normal repository integration, with current file rereads and local patches. No registry/CLI/report/PLAN/chapter edit was made here. Do not mark C52 or experimental 9-10 fully complete solely from this deliverable.

Suggested chapter insertion: “完整Qwen权重按TP轴与EP专家所有权求交，目标每字节只分配一个来源；同设备内容可免网络传送，但额外目标缓冲仍占容量。Qwen235 EP8→16新八卡接收一半routed权重，并不等于完整迁移量：旧卡重新分配、非专家复制、KV与辅助状态另计。新增准备10秒、同负载每步省0.2ms的教学交点为50,000步，50,001步才严格获益；建组、重打包、图准备、回放与积压未知时，不据带宽下界声称服务收益。部署账须包含热副本重叠、失败尝试、路由/缓存与恢复，并以SLO内有效完成数作分母。”

Unresolved: actual engine topology/support, kernel/graph format, source packing, live migration consistency and pause, KV/RNG/token identity validation, failed-source recovery, WAL durability, replay compute, queues/arrival traces, heterogeneous PD/AF/shared-KV combinations, real billing/resource lifetimes, success/quality/SLO evidence, PP/DP/SP support, overlap DAG, allocator/activation peaks, and measured reconfiguration performance. Full deployment comparison across these candidates remains an integration and experimental task.

## Validation actually run

- First local `unittest` run: 10 tests, 7 errors due to the `Weight.repeats` field mismatch; retained in the initial log.
- After correcting to `Weight.copies`: 10 tests passed; rerun after initial scenario generation also passed.
- Final expanded suite: 11 tests passed, including Dense TP1/4/8/16/32 and MoE EP1/7/8/16 comparisons, 49 reconstruction combinations, mixed TP×EP plus auxiliary conservation, source holes, unsupported scope, unknown-field preservation, missing runtime/cost, exact rounding and capacity ±1-byte checks.
- Seven scenarios executed and regenerated after the final runtime-null handling change; three pinned official configs verified by the existing source loader and copied with provenance.
- No full repository test suite, GPU test, numerical model-output test or actual deployment test was run.
