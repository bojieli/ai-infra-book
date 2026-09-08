# 休眠、权重交接与分片传输

2026-09-08 共保存 [21 份响应](sources.json)：18 次成功，3 次路径错误返回 404。17 份来源有明确[读取范围](reading-proof.json)，一份 runner 源码仅下载；没有执行下载代码、启动服务或完成全部后端调用链审计。教学计算见[权重交接](../../../../case-studies/weight-handoff.md)。

vLLM 固定 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`；SGLang 固定 `c99d906effa8bd05573995127f0d4a0984c5a96a`；verl 固定 `d040717b21af2e23e8e789a3e354cff2394ae2de`，提交身份时间为 2026-09-07T13:33:39Z。文章日期不是特性首次合入日期，当前主线与不同后端的能力分别说明。

| 来源 | 已读范围与采用边界 |
| --- | --- |
| [SGLang 团队内存实践](sglang-memory-2025.html)、[正文](sglang-memory-2025.txt) | 2025-06-21 署名实践文章，抽取正文全文；图片未逐张核查。其 v0 是未实现的概念基线，历史 Qwen2.5／H200 数据不作本书实测。CUDA 虚拟内存 API 的逐项实现不照抄为当前代码 |
| [vLLM Sleep Mode 文章](vllm-sleep-2025.html)、[正文](vllm-sleep-2025.txt) | 抽取正文 1–100 行，2025-10-26、两种级别与保留进程／图准备的原因；没有读完性能表和所有场景，不采用其倍数 |
| [当前 Sleep Mode](vllm-sleep-current.md)、[权重传输](vllm-transfer-current.md)、[Sharded RDT](vllm-transfer-rdt.md) | 三份全文。区分广播路径 rank 0 发载荷与 RDT 各所有者供给；RDT 要求 Ray／NIXL 和受支持的 loader 操作，EPLB 被拒绝。最大原子切片、接收缓冲与 gather 窗口需独立预算 |
| [vLLM worker](vllm-worker-current.py)、[allocator](vllm-allocator-current.py) | worker 231–304、1346–1446；allocator 229–277、327–357。按标签恢复、buffers 保存与 update 会话；未读全套派生状态恢复、权重版本提交和异常回滚实现 |
| [Native RL APIs 文章](vllm-native-rl-2026-fixed.html)、[正文](vllm-native-rl-2026-fixed.txt) | 2026-05-28；重点正文 327–496 行，keep 与 DP／EP 两阶段暂停。API 背景另由原站查看，性能表及图片未核。历史每 32 步检查的描述不写成当前配置常量 |
| [RDT 文章](vllm-rdt-2026.html)、[正文](vllm-rdt-2026.txt) | 2026-08-22；1–165 行，布局记录、PP／EP 本地提取与流水、Qwen3 对照。Kimi 表只见开头，后续容错实验未读；不采用 7.53 秒作为本书或当前框架保证 |
| [SGLang RL guide](sglang-rl-guide-fixed.mdx) | 1–104、581–642 行，内存标签、token 版本与暂停模式；其他 refit 接口表未全部读。`in_place` 依赖旧 KV，不能与需要清空缓存的更新任意组合 |
| [SGLang scheduler](sglang-scheduler-weights.py)、[内存 adapter](sglang-memory-adapter.py) | scheduler 196–300 行、adapter 全文；idle 检查、静态状态和标签恢复。源码含 CUDA Graph 标签而上述指南表只列两项，保留差异；没有审计 torch_memory_saver 底层实现 |
| [verl V1 guide](verl-v1-async-fixed.md) | 1–110、118–158 行，部分轨迹、版本与旧策略恢复开销、实验性混合资源切换；不是完整异步 trainer 调度源码审计 |
| [verl vLLM server](verl-vllm-server.py) | 833–894、1244–1277 行，跨 DP 调用、缓存失效、MTP／LoRA sleep 选择；不声称所有外部 KV 后端均已验证 |
| [verl SGLang server](verl-sglang-server.py) | 374–386、480–544 行，CPU backup 配置、adapter 基座保留和模式分支。注释称与 vLLM 模式对应，但已读实际实现的保留策略不同；按代码区分 |

三个 404 分别为旧 SGLang 文档路径、错误的 verl `.rst` 路径和漏了复数的文章 URL；固定可用路径另存，没有覆盖失败原件。[SGLang runner updater](sglang-runner-weights.py)仍为 downloaded_not_read，不从其下载推出读取或验证结论。两份 GitHub 元数据只用于提交身份和路径发现。

正文只采用阶段峰值、复制是否必要、按分片传输和最大缓冲这几项判断。方案成功还需完整恢复所需状态、确认相关 rank 已可交接，并对齐策略版本；原稿或源码中的局部成功不被提升为任意组合的保证。
