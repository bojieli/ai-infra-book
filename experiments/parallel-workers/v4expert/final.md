已完成有界预检，产物与状态已同步远端，交主 agent 统一审核。**预设数值验收未全通过，不能据此为完整 V4 放行。**

- 使用 layer 0 的真实专家 **0/1/7/42/128/255**，确认原生 I8 packed 权重及 F8_E8M0 尺度布局；直接执行未修改的 SM120 Triton 函数。
- 真实切片 smoke、完整形状 M1、六个单专家选择及强制 clamp 测试通过。
- **M8 有 10/32768 个元素超出预设逐元素门槛**；relative-L2 为 **0.000392407**，虽低于 1%，仍按协议判定未通过。门槛未放宽，所有误差和失败坐标已保存。
- 零路由、invalid-slot 对照、路由置换、profiler 前后及官方 **OffloaderV1** 包装前后，均通过精确一致控制。
- 运行正常退出 **0**；采样 GPU 峰值 **1050 MiB**，进程树主存峰值约 **1.53 GiB**，CPU 限定 4 核/线程。本地目录总计 **319 MiB**。
- 退出后完成传输及 SHA 核验；本地从 packed 文件独立复算的全部 CPU FP64 参考阶段，与远端保存值逐位一致。

完整说明见 [README.md](/Users/boj/book/ai-infra-book/experiments/ch02/02-05/expert-preflight/README.md)，数值结果见 [summary.md](/Users/boj/book/ai-infra-book/experiments/ch02/02-05/expert-preflight/results/summary.md)，逐元素失败见 [failures.json](/Users/boj/book/ai-infra-book/experiments/ch02/02-05/expert-preflight/results/failures.json)，交接状态见 [status.md](/Users/boj/book/ai-infra-book/experiments/parallel-workers/v4expert/status.md)。

本结论仅覆盖六个真实专家与合成输入/路由；未验证完整 V4、真实 router/激活、检索质量或其他算子。