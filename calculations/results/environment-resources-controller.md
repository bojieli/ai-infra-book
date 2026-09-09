# environment-resources — 

输入：`{"condition": "all", "dataset": "controller"}`

CPU/RSS来自封存实际进程记录；采样积分与有限窗恒等式不代表生产稳态或物理内存。

| 结果 | 值 |
| --- | ---: |
| dataset | `"controller"` |
| rounds | 12 |
| observation_window_seconds | 9.357788530178368 |
| model_wall_seconds | 8.995476951589808 |
| tool_wall_seconds | 0.2755274493247271 |
| other_loop_wall_seconds | 0.08678412926383319 |
| model_controller_cpu_seconds | 0.1571458099999994 |
| tool_controller_cpu_seconds | 0.07564741499999705 |
| reaped_tool_cpu_seconds | 0.17906399999999997 |
| sampled_controller_cpu_delta_seconds | 0.2859690000000005 |
| sampled_controller_cpu_average_cores | 0.030747522372801827 |
| rss_unobserved_prefix_seconds | 0.010436633136123419 |
| rss_unobserved_suffix_seconds | 0.046797643182799 |
| agent_reported_finished | `false` |
| quality_passed | `false` |
| visible_cases_passed | 2 |
| visible_cases | 6 |
| whole_environment_memory_bytes | `null` |
| scheduler_queue_wait_seconds | `null` |
| environment_arrival_rate_per_second | `null` |
| sample_count | 186 |
| sampled_rss_peak_bytes | 1,361,543,168 |
| sampled_rss_byte_seconds | 12,660,634,418.19639 |
| sampled_rss_byte_seconds_recorded_decimal_exact | `"6181950399509955981348259/488281250000000"` |
| rss_sample_window_seconds | 9.300554253859445 |
| max_sample_gap_seconds | 0.061933307209984 |

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

- [sources/environment-resources/controller/run.py](../../experiments/ch11/11-01/run.py)，SHA256 `b4a88d38827345732faee19b1883f7a101607bd9550591332d4e7aa77dfb5765`。
- [sources/environment-resources/controller/PROTOCOL.md](../../experiments/ch11/11-01/PROTOCOL.md)，SHA256 `fdaf60e015bfb284dc9e0175285185fc2ff45f3721992391483f3c7f185ad7b9`。
- [sources/environment-resources/controller/results/environment.json](../../experiments/ch11/11-01/results/environment.json)，SHA256 `a8ff6eb66ccebdf3aba2c433d8c5038a43beb21854b9472541f00e41d97f796c`。
- [sources/environment-resources/controller/results/rounds.jsonl](../../experiments/ch11/11-01/results/rounds.jsonl)，SHA256 `21933a3f0da15fdec804226458219fe04f286516f55000a4da15991f11aaa443`。
- [sources/environment-resources/controller/results/resource-samples.json](../../experiments/ch11/11-01/results/resource-samples.json)，SHA256 `52adc9decff32f1564c1cb08d86c509c0a044486ae42659870437c555e096e16`。
- [sources/environment-resources/controller/results/final.json](../../experiments/ch11/11-01/results/final.json)，SHA256 `c7c406c05a695349765a90694f8834d39e64112b83f0dfb53200ff95a680cd21`。
- [sources/environment-resources/controller/results/workspace/intervals.py](../../experiments/ch11/11-01/results/workspace/intervals.py)，SHA256 `90917de33474da18a4d29b7a33e51a355d024a7126069b7f75a8f0f6775f2afe`。
- [sources/environment-resources/controller/manifest.json](../../experiments/ch11/11-01/manifest.json)，SHA256 `2d2bed210f8af3f421300c7e214a4cdd50dcd10c2602bf0fcf96872e849ebedf`。
