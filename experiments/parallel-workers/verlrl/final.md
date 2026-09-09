本批已封存，**实验 10-8 的真实 RL 闭环尚未完成，已验证 optimizer 更新为 0 次**。

已实际验证：

- 固定 verl `d040717…`，在私有环境安装官方锁定的 vLLM 0.24 / Torch 2.11 cu130 / Transformers 5.9。
- 下载并核验固定 revision 的 Qwen2.5-0.5B-Instruct，全模型留在远端。
- 单 GPU FSDP 初始化成功，world size 1 使用 `NO_SHARD`。
- 两次 BF16 尝试完成版本 0 的代表张量交接：原始模型独立读取、verl 发送端、vLLM 实际加载后接收端的 embedding SHA256 一致。这不构成更新后权重同步证据。

阻塞是进程 RSS：一次采样达到 **12.080 GiB** 后终止；降低内存保留、提前设置停止线后的重试在 **11.617 GiB** 退出。GPU 采样峰值为 **6.137 GiB**，但 backward/Adam 峰值尚未验证。所有本批子进程已清理，未停止其他服务。官方锁文件另有一项 NumPy／mistral-common 依赖声明冲突，已保留说明。

交付已在本地和远端核验 **476 个文件的 manifest**，本地约 3.8 MB、远端私有环境约 12.05 GiB：

- [中文 README 与后续条件](/Users/boj/book/ai-infra-book/experiments/ch10/10-08/README.md)
- [预登记协议](/Users/boj/book/ai-infra-book/experiments/ch10/10-08/PROTOCOL.md)
- [离线核验报告](/Users/boj/book/ai-infra-book/experiments/ch10/10-08/analysis/REPORT.md)
- [完整 manifest](/Users/boj/book/ai-infra-book/experiments/ch10/10-08/manifest.json)
- [最终 status](/Users/boj/book/ai-infra-book/experiments/parallel-workers/verlrl/status.md)

下一批需主agent明确调度 RSS 预算并评估依赖冲突，再验证两次真实更新及更新后 rollout；约 16 GiB RSS 只是待验证建议，并非已知充分条件。