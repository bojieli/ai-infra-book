已完成真实执行与封存，待主 agent 独立复核。**两臂各一次合格、一次失败，本次结果不支持退出码干预改善质量。**

| ABBA 顺序 | 轮数 | finish | 原六例 | 独立严格 holdout |
|---|---:|---|---:|---:|
| baseline | 12 | 否 | 2/6 | 283/1013 |
| proper-exit | 12 | 否 | 2/6 | 283/1013 |
| proper-exit | 9 | 是 | 6/6 | 1013/1013 |
| baseline | 9 | 是 | 6/6 | 1013/1013 |

共 **42 次真实 HTTP 请求**，16 次非 JSON 输出严格拒绝，无 length 输出；追加 alias 失败均为 0。四次正式运行完整保留，没有追加样本或重跑替换。相同初始请求在干预前已产生不同输出，这一限制已明确写入分析。

已验证原 checker 的 `passed=false / exit0`，以及新 wrapper 同 stdout/stderr 下真实退出 **0/1**。复用指定模型与原 PID 服务，未启动引擎、reset APC 或停止服务。模型阶段 **17.23 秒**；本任务 CPU 树采样 RSS 峰值 **65.75 MiB**，控制器正常退出。

交付：

- [README 与结论](/Users/boj/book/ai-infra-book/experiments/ch11/11-09/exit-status/README.md)
- [冻结协议](/Users/boj/book/ai-infra-book/experiments/ch11/11-09/exit-status/PROTOCOL.md)
- [analysis.json](/Users/boj/book/ai-infra-book/experiments/ch11/11-09/exit-status/analysis.json)
- [663 项审计检查](/Users/boj/book/ai-infra-book/experiments/ch11/11-09/exit-status/checks.json)
- [manifest：172 个文件，本地与 RTX 均校验通过](/Users/boj/book/ai-infra-book/experiments/ch11/11-09/exit-status/manifest.json)
- [worker 状态](/Users/boj/book/ai-infra-book/experiments/parallel-workers/agent_exit_status/status.md)

仅写授权目录；calculations、正文、inventory、PROGRESS 和共享环境均未改动。