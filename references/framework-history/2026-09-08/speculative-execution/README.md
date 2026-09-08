# 推测解码的版本与实现资料

2026-09-08 获取。[sources.json](sources.json)保存 20 份成功响应：七篇官方文章、五份固定文档、三份源码和五份身份／目录元数据。下载的源码未导入或执行，没有运行 GPU、模型或训练。

## 历史文章

- [vLLM 2024](vllm-2024.html)：全部正文、示例与图注已读；动态调节当时列为未来工作，性能随 QPS 改变。
- [Speculators 2025](vllm-speculators-2025.html)：全部正文及附录已读；离线特征、目标／草稿绑定、训练与推理职责分开。
- [P-EAGLE 2026](vllm-peagle-2026.html)：全部正文、表格与复现条件已读；曲线未独立数字化。另核对 [PR 32887](vllm-peagle-pr.json) 的 02-05 合入及 [v0.16.0](vllm-v016-release.json) 的 02-25 发布，仅核身份字段，未审阅全部 PR 或 release 内容。
- [SGLang MTP 2025](sglang-mtp-2025.html)、[DFlash／Spec V2 2026](sglang-specv2-2026.html)、[DSpark 2026](sglang-dspark-2026.html)：全部文字、表格、图注及复现设置已读，未独立提取曲线。MTP 表格百分比疑点、Spec V2 重叠条件、DSpark 图档位与成本限制另记案例。DSpark [PR 身份](sglang-dspark-pr.json)显示 07-12 合入，不能将 07-06 文章日期直接作为主线合入日期；没有审阅全部 84 个改动文件。
- [Ollama MLX 2026](ollama-mlx-performance-2026.html)：全部正文已读。选择性快照与 GPU 采样／融合用于补已有本地例子；先前的 [MTP 公告](../../../outline-checks/2026-09-07/framework-evolution/ollama-mtp.html)复读，未重复下载。

## 固定实现与范围

vLLM 提交 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`，提交时间 2026-09-07，见[身份](vllm-head.json)与[目录](vllm-tree.json)。完整阅读[动态长度](vllm-dynamic_speculative_decoding.md)、[自适应验证](vllm-adaptive_verification.md)、[逐请求接受指标](vllm-acceptance_metrics.md)三份文档；只读 [config](vllm-spec-config.py) 第 370–400、450–541 行和 [metrics](vllm-spec-metrics.py) 第 82–140 行。当前主线不等于每个已发布安装版本，配置定义和指南也不证明整条执行路径已审计。

SGLang 提交 `c99d906effa8bd05573995127f0d4a0984c5a96a`，沿用已归档[目录身份](../overlap-placement/sglang-current-tree.json)。完整阅读[自适应步数文档](sglang-adaptive-guide.mdx)与[DSpark 成本表源码](sglang-dspark-sps.py)；[推测解码指南](sglang-spec-guide.mdx)只读第 528–598 行 DFlash 和 683–725 行 Spec V2。按 batch 的 EAGLE 档位、按请求的 DSpark 预算与不同框架的 DP 限制分别记录。

采用位置为第 9.2.4、9.3 与原实验 9-4／9-5／9-6，详细的 Qwen3 矩阵、计数和时间计算见[扩写笔记](../../../../case-studies/speculative-execution.md)。这轮没有新增会议论文全文阅读或面试证据样本。

后续历史草稿核对：SGLang 同一固定指南的第 725–789 行 NGRAM 说明已读取；对应 vLLM suffix 与 Arctic 源码、独立采样／成本推算见[RhymeRL 交叉核对](../../../proceedings/ASPLOS/2026/rhymerl-crosschecks/README.md)。此项落在当前 8.3.1→10.5.3、实验 8-5／10-8；上文第 9 章等采用位置保留此前阶段的编号背景。
