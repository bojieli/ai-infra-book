8-5 **第一轮真实对照已完成并交付，原题仍为部分覆盖**。未做跨 session 最终审计，也未修改正文、inventory 或总进展。

- 完成 **AR-V1、DFlash K7、DFlash K15**，各 8 次预热、16 次正式请求，共 48 次正式请求；覆盖短/长输入、计算/文档提取、并发 1/2。发现默认 AR 使用 V2 runner 后，保留原结果并补跑了同 V1 对照。
- **32 对正式输出 token 全部一致，但严格质量均为 8/16**：短算术题算对却违反输出格式；长算术题答成 709，正确答案为 719；提取题全部通过。所有输出自然停止，无上限截断。
- 真实接受统计：K7 为 **368/504 draft tokens**，K15 为 **376/840**，均不含 bonus。采样显存峰值分别为 AR **17,706 MiB**、K7 **20,894 MiB**、K15 **20,814 MiB**。
- 本 worker **41 项 QA 通过**，传输与源码 hash 已核验，图已检查；三次启动失败完整保留。所有实验进程正常退出，原有五个 GPU 服务保留。本地新增约 **126 MiB**，包含私有分析环境。

通过质量的短提取题在本轮明显变快；长输入双并发收益较小，且 DFlash 的 TTFT 更长。**CPU/GPU 共享，这些结果不代表隔离性能。**

交付入口：[中文 README](/Users/boj/book/ai-infra-book/experiments/ch08/08-05/README.md)、[固定协议](/Users/boj/book/ai-infra-book/experiments/ch08/08-05/PROTOCOL.md)、[验证与失败原文](/Users/boj/book/ai-infra-book/experiments/ch08/08-05/results/validation.json)、[worker 状态](/Users/boj/book/ai-infra-book/experiments/parallel-workers/speculative/status.md)。

仍未覆盖 kernel 级草稿/验证/回退分段、真实验证行与回退索引、动态预算/图档位、更广任务与并发、随机采样分布，以及 EAGLE 3.1／DFlash 2 公开记录复算；已在交接文档明确列出，供主 agent 统一回填。