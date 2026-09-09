# environment-resources — 

输入：`{"condition": "cpu-burst", "dataset": "processes"}`

CPU/RSS来自封存实际进程记录；采样积分与有限窗恒等式不代表生产稳态或物理内存。

| 结果 | 值 |
| --- | ---: |
| dataset | `"processes"` |
| condition | `"cpu-burst"` |
| verified_runs | 9 |
| verified_processes | 36 |
| reported_runs | 3 |
| reported_processes | 12 |
| all_finite_cohort_identities_verified | `true` |
| scheduler_queue_wait_seconds | `null` |
| whole_environment_memory_bytes | `null` |
| production_arrival_rate_per_second | `null` |
| physical_core_utilization | `null` |

| 条件中位数 | 窗口秒 | CPU核秒 | 采样RSS峰值和bytes | RSS bytes·s |
| --- | ---: | ---: | ---: | ---: |
| cpu-burst | 0.103272168 | 0.2907 | 335130624 | 15166256.02009088 |

计量条件：

- 本书实验11-1两批真实Linux记录逐文件校验原manifest和独立锁哈希，源码身份绑定environment；CLI仅离线重算，不执行工具、模型或/proc采样。控制器与工具子进程补实验是不同运行，不跨运行相加。
- 控制器CPU/RSS仅含控制器与监测、tokenizer、引擎前端；不含活GPU worker或工具子进程RSS。阶段CPU来自process_time边界，回收工具CPU来自RUSAGE_CHILDREN差，样本CPU窗口不同，不要求它们直接相加相等。失败任务照常保留资源量。
- 工具补实验9组、每组三轮条件之一和4真实进程；wait是人工sleep，cpu是固定SHA256工作。退出前RUSAGE_SELF总CPU包含启动/导入/分配触页但未涵盖之后打印/退出；不是纯业务CPU或整组所有进程完整CPU。
- RSS只对实际采样点按梯形插值，首样本前与末样本后不补值；峰值只是观测峰值。工具RSS和重复计算共享页，不是PSS/cgroup/整机物理内存；稀疏采样可能漏瞬态。decimal_exact仅保存记录数字的有理算术，不表示时钟或内存测量精确。
- 工具生命周期定义为父进程记录launch至观察reaped，包含启动和回收观察延迟；不等于内存真实驻留边界。完整4进程队列用有限窗面积积分核对L=(完成数/窗口)×平均生命周期，所有对象在窗内进入并完成；不从这9组短测量外推稳态Little容量。
- 计划提交至实际launch只表示这份脚本的提交延迟，launch至worker_start也包含进程启动，均不能等同OS调度队列等待。真正scheduler queue wait、生产到达率、物理核利用率与完整环境容量没有记录，保留null。
- 工具组观察窗含最后监测sleep；CPU核秒除观察墙钟是平均占用核数，不是除以未知核数后的利用率。三次中位数是描述摘要，保留全部run与worker；wait与cpu不同工作，不把其CPU差归因同一优化。
- 只有独立CPU工具的实际launch/reaped支持完成队列恒等式；控制器记录没有独立环境队列到达/创建/销毁，未制造环境并发或队列容量。任何真实扩容、预热、暂停恢复与SLO判断均需额外观测。

固定来源：

- [sources/environment-resources/processes/run.py](../../experiments/ch11/11-01/process-resources/run.py)，SHA256 `97292a4655c20c806537b4f8d00125a6fe35a363a6da2ef66ead74bf9dceb12f`。
- [sources/environment-resources/processes/PROTOCOL.md](../../experiments/ch11/11-01/process-resources/PROTOCOL.md)，SHA256 `37f45044948c0a8b4ffb637cb0a910f170590289ea02ad8e87015072b66bd142`。
- [sources/environment-resources/processes/results/environment.json](../../experiments/ch11/11-01/process-resources/results/environment.json)，SHA256 `3715c67cd184c5089b1223049f8f6e080ab1b2f16e641bb77f4c2aa8fe476e84`。
- [sources/environment-resources/processes/results/order.json](../../experiments/ch11/11-01/process-resources/results/order.json)，SHA256 `0e58c7c074abfc35976ccae4e4fe4c3cef839656ba7809c152bc5bf958ccbe1f`。
- [sources/environment-resources/processes/results/case0.json](../../experiments/ch11/11-01/process-resources/results/case0.json)，SHA256 `9f276b3e5f828e5b75e73181eea9b56ed34e7c023e4fea0215d7f90f9a0d18b7`。
- [sources/environment-resources/processes/results/case1.json](../../experiments/ch11/11-01/process-resources/results/case1.json)，SHA256 `1c6bb5e468aceb697479984a9880217ab2c84be2995aa8f263fb7ebd0a766676`。
- [sources/environment-resources/processes/results/case2.json](../../experiments/ch11/11-01/process-resources/results/case2.json)，SHA256 `9ccc914028a0fb51f920eb0b9670270a117a4f942a328d4fb99aaac025f7b19e`。
- [sources/environment-resources/processes/results/case3.json](../../experiments/ch11/11-01/process-resources/results/case3.json)，SHA256 `c9bf8a4ea752987bea7cbf3afff339c0ba8b60bce43761600be7f013df9e7078`。
- [sources/environment-resources/processes/results/case4.json](../../experiments/ch11/11-01/process-resources/results/case4.json)，SHA256 `8d4ae6ad35ec9aa44d67407df9e233ab934a8641bfbeab12a78c1266953de15e`。
- [sources/environment-resources/processes/results/case5.json](../../experiments/ch11/11-01/process-resources/results/case5.json)，SHA256 `df9d2e41799b8f1bb3a91537db516fd3628ca9d9f32f7d3b595cfa1ca67e181e`。
- [sources/environment-resources/processes/results/case6.json](../../experiments/ch11/11-01/process-resources/results/case6.json)，SHA256 `36f8c9ef5e09c25e27add135b194405477ca7fc4470479d3ebe5a2ae1e39b1bc`。
- [sources/environment-resources/processes/results/case7.json](../../experiments/ch11/11-01/process-resources/results/case7.json)，SHA256 `b3d28b22fc448a85463bf869bfc6576b0d22a3c5311fac73016175b978de3f92`。
- [sources/environment-resources/processes/results/case8.json](../../experiments/ch11/11-01/process-resources/results/case8.json)，SHA256 `62d616bf5b581b5c10dbd0492ac9617142c647874287107cd8f77decde8f644d`。
- [sources/environment-resources/processes/manifest.json](../../experiments/ch11/11-01/process-resources/manifest.json)，SHA256 `ddea1a8b9837a084d4126cb80a4dbdb37207cecd0fb849e027447ee484480d99`。
