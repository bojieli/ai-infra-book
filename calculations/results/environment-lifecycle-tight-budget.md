# environment-lifecycle — declared-environment-budget

输入：`{"dirty_bytes": 134217728, "effective_transfer_bytes_per_second": 1073741824, "environments": 32, "hot_readonly_bytes": 268435456, "lead_seconds": "1", "local_budget_bytes": 8589934592, "prediction_hit_probability": "3/4", "preparation_seconds": "2", "private_overhead_bytes": 4194304, "snapshot_delta_bytes": 134217728, "template_bytes": 2147483648, "touched_bytes": 536870912, "warm_environment_bytes": 2147483648, "wrong_prediction_timeout_seconds": "3"}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| evidence_scope | `"Teaching capacity/expectation inputs plus separate archived local process measurements"` |
| measured_prewarm_trials | 12 |
| e2b_four_path_runtime_measured | `false` |
| complete_environment_memory_peak_bytes | `null` |
| complete_environment_startup_seconds | `null` |

clone_placements

| placement | per_environment_local_bytes | total_local_bytes | separately_retained_shared_template_bytes | total_bytes_across_declared_pools | memory_only_environment_upper_bound | initial_local_data_install_bytes | aggregate_serial_transfer_lower_exact_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| "full_copy" | 2151677952 | 68853694464 | 2147483648 | 71001178112 | 3 | 68719476736 | "64" |
| "install_touched" | 541065216 | 17314086912 | 2147483648 | 19461570560 | 15 | 17179869184 | "16" |
| "share_readonly_copy_dirty" | 138412032 | 4429185024 | 2147483648 | 6576668672 | 62 | 4294967296 | "4" |
| "localize_hot_readonly" | 406847488 | 13019119616 | 2147483648 | 15166603264 | 21 | 12884901888 | "12" |

creation_paths

| path | declared_source_fetch_bytes | declared_local_install_bytes | serial_byte_service_lower_exact_seconds | create_api_seconds | first_tool_complete_seconds | reconnect_seconds | measured |
| --- | --- | --- | --- | --- | --- | --- | --- |
| "cold_template" | 2147483648 | 536870912 | "5/2" | null | null | null | false |
| "warm_template" | 0 | 536870912 | "1/2" | null | null | null | false |
| "pause_resume" | 536870912 | 536870912 | "1" | null | null | null | false |
| "snapshot_clone" | 536870912 | 536870912 | "1" | null | null | null | false |
| "clean_rebuild" | 2147483648 | 2147483648 | "4" | null | null | null | false |

measured_prewarm_trials

| trial | policy | rounds | launches | prediction_hits | unused_preparations | unused_ready_seconds | unused_allocated_lifecycle_seconds | launch_to_ready_seconds | call_to_tool_reply_seconds | completion_seconds | measured_unused_physical_memory_byte_seconds | sample_count | sampled_rss_peak_bytes | sampled_rss_byte_seconds | sampled_rss_byte_seconds_recorded_decimal_exact | rss_sample_window_seconds | max_sample_gap_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | "predict-fullgap" | 12 | 14 | 10 | 2 | 2.197153708 | 2.261670417 | [0.032703333, 0.031613125, 0.032550584, 0.032903584, 0.032568916, 0.031708625, 0.030236916, 0.031171875, 0.031978, 0.031917792, 0.032512, 0.033121042, 0.033367792, 0.033920041] | 0.240823708 | 13.595991042 | null | 224 | 38338560 | 502510185.8196521 | "981465206679008/1953125" | 13.553940229 | 0.064357542 |
| 0 | "predict-50ms" | 12 | 14 | 10 | 2 | 0.04354675 | 0.107993208 | [0.033017584, 0.032416083, 0.035153291, 0.032030375, 0.032794667, 0.033278833, 0.035826625, 0.036124625, 0.033713625, 0.034965083, 0.034946667, 0.033092042, 0.033207875, 0.033568041] | 0.260324624 | 13.636556667 | null | 237 | 38191104 | 20731371.98596096 | "8098192182016/390625" | 13.637224979 | 0.0647381875 |
| 2 | "demand" | 12 | 12 | null | 0 | 0.0 | 0.0 | [0.034070583, 0.033391792, 0.033341291, 0.033164375, 0.033114667, 0.033006708, 0.032940958, 0.033159375, 0.033440375, 0.0324025, 0.032230583, 0.034627875] | 0.563512376 | 13.865871416 | null | 243 | 38109184 | 12205649.745006591 | "23839159658216/1953125" | 13.841483833 | 0.0617958335 |
| 2 | "predict-50ms" | 12 | 14 | 10 | 2 | 0.023078583 | 0.089935917 | [0.033368375, 0.032780584, 0.032012791, 0.03407675, 0.033843958, 0.031013917, 0.03178125, 0.032477875, 0.031903958, 0.034503666, 0.033171083, 0.032422125, 0.031384792, 0.032750208] | 0.24718775 | 13.569942333 | null | 239 | 38191104 | 21707147.584618498 | "42396772626208/1953125" | 13.5369762705 | 0.0633301665 |
| 2 | "resident" | 12 | 2 | null | 0 | 0.0 | 0.0 | [0.031350458, 0.030862208] | 0.164953247 | 13.409907833 | null | 133 | 76234752 | 1018683204.8187925 | "1989615634411704/1953125" | 13.418538313 | 0.1051078125 |
| 1 | "resident" | 12 | 2 | null | 0 | 0.0 | 0.0 | [0.03254975, 0.03077575] | 0.16529479 | 13.413397125 | null | 133 | 76611584 | 1023855417.3405266 | "1999717611993216/1953125" | 13.4401376455 | 0.105597375 |
| 0 | "demand" | 12 | 12 | null | 0 | 0.0 | 0.0 | [0.03266075, 0.032771417, 0.043821416, 0.041149083, 0.044225958, 0.044991125, 0.047202041, 0.042022375, 0.038479333, 0.043440125, 0.033757375, 0.0437945] | 0.666949957 | 13.979325208 | null | 258 | 38158336 | 11798375.516524544 | "23043702180712/1953125" | 13.952087396 | 0.0579073335 |
| 2 | "predict-fullgap" | 12 | 14 | 10 | 2 | 2.178383416 | 2.2516965 | [0.032823083, 0.039972834, 0.040841583, 0.03334025, 0.037389583, 0.032429916, 0.033917167, 0.0430295, 0.034025667, 0.043126375, 0.036325083, 0.044782833, 0.033065375, 0.032155542] | 0.310039706 | 13.628454791 | null | 230 | 38158336 | 499849361.976107 | "976268285109584/1953125" | 13.595808021 | 0.0618039795 |
| 0 | "resident" | 12 | 2 | null | 0 | 0.0 | 0.0 | [0.032997125, 0.032169] | 0.16923592 | 13.415211375 | null | 133 | 76414976 | 1021463203.3442652 | "1995045319031768/1953125" | 13.4422989785 | 0.105160521 |
| 1 | "demand" | 12 | 12 | null | 0 | 0.0 | 0.0 | [0.038387416, 0.036908041, 0.041023375, 0.04283275, 0.043928958, 0.041926833, 0.045979, 0.043805708, 0.038271583, 0.037415292, 0.0412095, 0.043074417] | 0.667723291 | 13.968175333 | null | 258 | 38240256 | 12288130.23295488 | "4800050872248/390625" | 13.93016625 | 0.058571646 |
| 1 | "predict-50ms" | 12 | 14 | 10 | 2 | 0.020857457 | 0.099724666 | [0.041711458, 0.039500417, 0.031358125, 0.039366792, 0.03170325, 0.044734291, 0.042893083, 0.042248792, 0.039109542, 0.043946167, 0.042882333, 0.043602, 0.039239917, 0.040006542] | 0.256214459 | 13.567460541 | null | 251 | 38223872 | 20373057.76772301 | "39791128452584/1953125" | 13.558774396 | 0.0594260625 |
| 1 | "predict-fullgap" | 12 | 14 | 10 | 2 | 2.18232375 | 2.250489958 | [0.031045166, 0.036757333, 0.033865, 0.031408875, 0.03579775, 0.03272175, 0.032852292, 0.037109208, 0.034964125, 0.040757666, 0.032927208, 0.032383542, 0.032494417, 0.032825667] | 0.274754041 | 13.592056083 | null | 232 | 38223872 | 501725932.09391516 | "979933461120928/1953125" | 13.5694500415 | 0.061241958 |

snapshot_budget：`{"shared_base_bytes": 2147483648, "branch_delta_bytes": 134217728, "branches": 32, "total_base_plus_private_deltas_bytes": 6442450944, "full_independent_snapshots_bytes": 68719476736, "one_delta_upload_lower_exact_seconds": "1/8", "incremental_format_supported_by_measured_platform": null}`

prewarm_budget：`{"expected_call_preparation_wait_exact_seconds": "5/4", "expected_avoided_wait_exact_seconds": "3/4", "expected_allocated_pretool_environment_seconds": "3", "expected_unused_environment_seconds": "1", "expected_pretool_memory_byte_seconds": "6442450944", "expected_extra_pretool_memory_byte_seconds_vs_demand": "2147483648", "expected_unused_memory_byte_seconds": "2147483648", "cpu_core_seconds": null}`

本地进程记录不代表云端microVM创建实测；创建API、首工具完成、重连、真实增量格式与完整物理内存峰值仍未核实。

计量条件：

- Clone placement inputs reproduce the separate 2 GiB/100 environment teaching case; no E2B/CXLfork benchmark values are inferred.
- Touched includes dirty and disjoint hot read-only bytes. Shared checkpoint remains separate from the local budget. Capacity is memory-only and logical, not sum-of-RSS physical measurement.
- Creation byte paths are a declared serial two-hop staging scenario: cold fetches full template then installs touched pages; warm has source cached but still installs touched; resume/clone fetch and install touched; clean rebuild fetches and installs full template. One shared effective byte service is assumed. Control, init, first-tool execution and reconnect remain unknown, so these are not startup times.
- Base-plus-deltas assumes a declared deduplicated incremental format and independent branch deltas; actual E2B persistence/storage dedup is unknown. Delta upload is byte/service lower bound, not snapshot completion.
- Prewarm begins lead seconds before the call. A correct environment survives until max(call,ready); a wrong one is canceled timeout seconds after call, even if preparation is unfinished. Wrong calls additionally start on-demand preparation.
- Full configured environment bytes are charged from preparation launch to first usability or cancellation. Ready idle plus all unused wrong preparations are separated; CPU work and actual allocated RSS are unknown.
- Expected wait presumes no contention, instantaneous cancellation and the same preparation duration for demanded/predicted environments; correctness hit is not an observed ready-at-call rate.
- Measured prewarm records are local process fixture replays with actual gap waits, not E2B microVM, live prediction-model quality or cold/resume benchmarks. They are never used to calibrate teaching preparation_seconds.
- RSS is trapezoidal interpolation of aggregate observed worker samples only, with no tails. Shared pages may be counted more than once; unused lifecycle time is not measured unused physical GiB-seconds.
- Official E2B documentation contracts are retained with measured timing null: file/process state, instance identity and reconnection are distinct; snapshots do not undo external effects.

固定来源：

- [sources/environment-lifecycle/11-02/summary.json](../../experiments/ch11/11-02/summary.json)，SHA256 `8192d6d1d960cc18aae498206d9c14a73f5cd82f94d2a74abddb384295781c0d`。
- [sources/environment-lifecycle/11-02/sources.json](../../experiments/ch11/11-02/sources.json)，SHA256 `2757a173c7283148234fe89cbccab3dd1d80b67c5a7aea34e5322c1da24ec82d`。
- [sources/environment-lifecycle/11-02/sources/persistence.md](../../experiments/ch11/11-02/sources/persistence.md)，SHA256 `d735b9dfc08b5c4c8978c6d75eb2af994ac754f56bedbacff4b05efaf51ceb43`。
- [sources/environment-lifecycle/11-02/sources/snapshots.md](../../experiments/ch11/11-02/sources/snapshots.md)，SHA256 `ff8e3469e58c65c70276e4a4e1ca84f5367264b75155aa51cf137b75cb546f7c`。
- [sources/environment-lifecycle/11-06/manifest.json](../../experiments/ch11/11-06/manifest.json)，SHA256 `e104d8e5b6826efe2263d2e1bdf90c7e1aa99ce965a63565a2ff9aaf8ad3d993`。
- [sources/environment-lifecycle/11-06/run.py](../../experiments/ch11/11-06/run.py)，SHA256 `107526daff239b2a2be6a560e4dcab416a3213f551a95094888470ff07d1a39c`。
- [sources/environment-lifecycle/11-06/worker.py](../../experiments/ch11/11-06/worker.py)，SHA256 `76e89d034bcbe84793db2f6836720cc928d05736fb127691271a5d10012936c6`。
- [sources/environment-lifecycle/11-06/tools.py](../../experiments/ch11/11-06/tools.py)，SHA256 `0d858bdd7ce767881adcf67a2466d0cb558969221145f0a0644aebdcef084b4e`。
- [sources/environment-lifecycle/11-06/fixture.json](../../experiments/ch11/11-06/fixture.json)，SHA256 `b4b04cad658cb46aefb5ac748f19b14cbeefa7b68fe2f0970182579dfcdb7fcc`。
- [sources/environment-lifecycle/11-06/results/environment.json](../../experiments/ch11/11-06/results/environment.json)，SHA256 `8a7795501f31daad3df9935f8e29e4262164b0794c5af22c4238d1484080502d`。
- [sources/environment-lifecycle/11-06/results/completion.json](../../experiments/ch11/11-06/results/completion.json)，SHA256 `e4e4418bad0db88a1a618e56c1af0bbd21b0ef37a7ca2b65aeb5ceb273d69023`。
- [sources/environment-lifecycle/11-06/results/0-demand/raw.json](../../experiments/ch11/11-06/results/0-demand/raw.json)，SHA256 `c82b8043e6f2fb5428693fd2760b0558c929cd34eb965ec53b4afdab744df743`。
- [sources/environment-lifecycle/11-06/results/0-predict-50ms/raw.json](../../experiments/ch11/11-06/results/0-predict-50ms/raw.json)，SHA256 `ed72edb6f068bc2018c7f92935d1d21a3a2e47ed4c8a131ae9d5252d7f9fc7e4`。
- [sources/environment-lifecycle/11-06/results/0-predict-fullgap/raw.json](../../experiments/ch11/11-06/results/0-predict-fullgap/raw.json)，SHA256 `187617e262ce8ae52972bdc8415115c2ee29e90435a67569198261a93a8383a6`。
- [sources/environment-lifecycle/11-06/results/0-resident/raw.json](../../experiments/ch11/11-06/results/0-resident/raw.json)，SHA256 `0cbacffeaf7a3caf9f7918756bfb4b69fc026106e8a3d8ac2b8cebe9424f2543`。
- [sources/environment-lifecycle/11-06/results/1-demand/raw.json](../../experiments/ch11/11-06/results/1-demand/raw.json)，SHA256 `9114f92dd489f2645c3c9ee64a9923e4f6cb042527516ebf571d5c158767678d`。
- [sources/environment-lifecycle/11-06/results/1-predict-50ms/raw.json](../../experiments/ch11/11-06/results/1-predict-50ms/raw.json)，SHA256 `71b2249ef09f7242292953bc0e9649f7e0ae087875ec395d16cdb7be50f9cbf8`。
- [sources/environment-lifecycle/11-06/results/1-predict-fullgap/raw.json](../../experiments/ch11/11-06/results/1-predict-fullgap/raw.json)，SHA256 `3f8c11d5864bf864c2e146b6f6ca44ae54180b022d72454ef9cff6f8f2739e9e`。
- [sources/environment-lifecycle/11-06/results/1-resident/raw.json](../../experiments/ch11/11-06/results/1-resident/raw.json)，SHA256 `6fc1a1c2336057d4a3b1ab2a337be1b7bba27e07e637bdccff3217dbc23f401d`。
- [sources/environment-lifecycle/11-06/results/2-demand/raw.json](../../experiments/ch11/11-06/results/2-demand/raw.json)，SHA256 `e86bcb67c21c7ef023a0d4f40522693f178ee1b9bf59516160388ecdf9913192`。
- [sources/environment-lifecycle/11-06/results/2-predict-50ms/raw.json](../../experiments/ch11/11-06/results/2-predict-50ms/raw.json)，SHA256 `bd2cbf77303aeb9e3d66d6b07d5f677d8536678342edc133b4254f7d717aed9c`。
- [sources/environment-lifecycle/11-06/results/2-predict-fullgap/raw.json](../../experiments/ch11/11-06/results/2-predict-fullgap/raw.json)，SHA256 `27b8e5a036319c37c4aa5f6af5fbcde707c3fbd90c26a59ae6453590b069f747`。
- [sources/environment-lifecycle/11-06/results/2-resident/raw.json](../../experiments/ch11/11-06/results/2-resident/raw.json)，SHA256 `51535d756f8132c10087cab2485a3b198a6f264accfe71bb3d7271d8335b8e83`。
