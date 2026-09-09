# 11-9 Collector队列、重试与任务记录故障实测

状态：记录故障变体部分完成；11-9整体仍为partial。Mac本地运行官方OpenTelemetry Collector contrib **0.133.0 Darwin arm64**，不是自写队列模拟。发布包SHA核对官方checksums，二进制和环境SHA记录于environment.json；下载信息和同tag源码说明保留在sources。

## 方法

每个条件实际执行5个小型CPU任务，发送5条OTLP日志，Collector接收端均HTTP200；后端为本实验的HTTP服务器和SQLite。每个条件再真实执行task0的一次新尝试，使用不同event_id与attempt_id，用作恢复通路探针并保留CPU时间。共两轮三条件、36次真实工具执行。

- 内存队列：后端返回503，观察到至少一次真实导出尝试后SIGKILL Collector，再在后端恢复后启动同配置。
- 文件队列：同上，但sending_queue配置file_storage、fsync=true，重启复用相同目录；杀进程后复制实际存储文件保留证据。
- 提交后非成功确认：文件队列，后端先提交SQLite再返回503，后续请求返回200。它模拟“提交已发生但成功确认未到达”的重传条件，**并未注入网络丢包或连接断开**。

队列容量100，版本默认按请求计，不能解读为100字节或MiB；一个消费者，重试初始200ms、最大1s、总重试时长不设上限。没有batch processor，没有诊断采样。后端按event_id的SQLite唯一键去重；Collector自身不承担业务去重。

## 实际结果

两轮结果相同，下表每格为每轮实际计数：

| 条件 | 崩溃前5事件恢复 | 加新尝试后的唯一记录 | 全部投递尝试 | 重复的已提交投递 |
|---|---:|---:|---:|---:|
| 内存队列＋SIGKILL | 0 | 1 | 2 | 0 |
| 文件队列＋SIGKILL | 5 | 6 | 7 | 0 |
| 文件队列＋提交后503 | 5（无崩溃） | 6 | 7 | 1 |

内存队列重启后观察2秒未见旧事件，新的探针成功抵达；这是有限观察窗口，不作无限未来断言。文件队列两轮均恢复所有旧事件，杀进程时数据库文件各131072字节；文件尺寸不是有效载荷或32/64MiB容量测量。确认失败时一条事件实际投递两次，唯一记录只增加一次。

每条件确实执行六次工具工作、对应五个逻辑任务；task0的两个attempt都保留独立身份。CPU时间保留在record.json，重复传输不重新执行工具，真实重执行则额外消耗工作。没有价格依据，不填金额。完整模型任务、环境恢复与模型升级的成本比较仍待，不能用这组微型工具替代。

## 可复现与边界

官方固定源码说明：[exporterhelper队列与重试](https://github.com/open-telemetry/opentelemetry-collector/blob/v0.133.0/exporter/exporterhelper/README.md)、[file_storage](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/v0.133.0/extension/storage/filestorage/README.md)。本次实测仅覆盖本地进程SIGKILL、原文件可用、接收端可重试HTTP错误；不证明断电、磁盘损坏、队列满或重试到期下无损。Collector接收HTTP200也不等于最终后端提交。

将官方相同版本二进制放在experiments/tools/otelcol-0133/otelcol-contrib，或修改独立副本run.py的BIN路径。确保31331/31332/31333空闲，在没有results的独立副本运行 `python3 run.py`；脚本拒绝覆盖已有结果。所有输出和SQLite文件位于该实验目录。重现现有数据用 `python3 analyze.py`，核验接收状态、工作结果、任务/尝试身份、实际投递与SQLite数据、崩溃退出码和落盘文件。

results保留六个完整条件的配置、Collector日志、每次后端尝试、工作时间、接收响应、生命周期、实际SQLite数据库及杀进程时文件副本。run.log、environment.json、cleanup-check.json与manifest.json记录版本、执行及封存信息；自建Collector及后端均已退出。失败事件、重传和重执行均不丢弃。

未使用GPU、未修改calculations。32/64MiB容量和排空推算仍由另一任务负责；持续流量下排空与其他模型任务对照尚待。最终跨session实验及论文复核仍待首轮全部实验完成。
