# 多级 KV 缓存与路由：框架读取范围

本批 [sources.json](sources.json) 归档 8 份成功响应；[reading-proof.json](reading-proof.json) 记录正文、选读段和两份复用历史文章。没有执行下载的代码、安装推理栈或运行性能测试。采用位置与教学计算见[缓存取回和路由](../../../../case-studies/cache-tiers-and-routing.md)。

固定 vLLM `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`、SGLang `c99d906effa8bd05573995127f0d4a0984c5a96a`，复用此前的 [vLLM tree](../speculative-execution/vllm-tree.json) 和 [SGLang tree](../overlap-placement/sglang-current-tree.json) 身份记录。固定当前实现不代表所有已安装版本，也不用于断言特性的首次发布日期。

| 来源 | 实际读取与采用范围 |
| --- | --- |
| [vLLM 2026-01-08 文章](vllm-kv-offload-2026.html)、[抽取正文](vllm-kv-offload-2026.txt) | 完整抽取正文及标题／日期元数据；异步 connector、CPU offload 与物理布局演进。未看图像或读取外部 benchmark 代码。文章采用的补丁与已发布版本分开 |
| [vLLM 当前 KV guide](vllm-current-kv-guide.md) | 1–81、112–188、297–330 行：CPU 中转、参数作用域、FS／OBJ 的命名和共享、事件边界、选择性写入；P2P 协议未读 |
| [HiCache 入口](sglang-current-hicache.mdx) | 8 行导航页；不能将它作为系统正文已经读过的证据 |
| [HiCache 设计](sglang-current-hicache-design.mdx) | 完整文本 216 行：实例私有 L2、条件式共享 L3、预取、各 rank 一致前缀、布局和 PD；外链图未查看，不采用性能倍数 |
| [HiCache 配置实践](sglang-current-hicache-practices.mdx) | 1–129 行：共享范围、布局条件、异构 TP、三种预取策略与 P／D 入口；示例未执行 |
| [Model Gateway guide](sglang-current-gateway.mdx) | 848–944 行：策略与调优；不是整份 2,816 行文档阅读 |
| [cache_aware 实现](sglang-current-cache-aware.rs) | 1–60、310–550 行：头部说明及实际选择分支；未读完整调用链／测试。采用实际最低负载分支，保留过期说明差异 |
| [Ollama FAQ](ollama-current-faq.html)、[抽取文本](ollama-current-faq.txt) | 抽取文本 338–407 行：模型 preload／keep_alive 的语义；不从驻留推断前缀或重启持久化 |

复用 [SGLang v0.4](../../../outline-checks/2026-09-07/framework-evolution/sglang-v04.txt) 的缓存路由段和 [2025 HiCache 文章](../../../outline-checks/2026-09-07/framework-evolution/sglang-hicache.txt) 的层次／数据面／控制面段。2024 的近似树、2025 的存储扩展与当前配置构成时点对照；完整逐版本 release history 仍未完成。

三个判断保留在研究笔记中：vLLM 文章的 Qwen3-8B 块尺寸不能由本书固定 BF16 配置复得，故不采用该行；SGLang `cache_aware` 头部的低匹配分支说明与正文实现不同，采用源码分支；KV 事件可见不意味着某个外部 router 已正确索引、路由并取回相应层级。当前文档自身声明的支持边界，不替代完整 runner 或 CUDA 内核审计。
