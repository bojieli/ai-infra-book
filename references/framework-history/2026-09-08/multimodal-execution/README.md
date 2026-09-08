# 多模态阶段执行：2024–2026 版本与读取范围

2026-09-08 归档 17 份成功响应。[sources.json](sources.json)记录 URL、提交、响应字节、哈希和逐项读取范围。静态阅读，不安装或执行下载的框架代码。

- vLLM [v0.6.0 视觉指南](vllm-mm-2024.md)全文：当时的单图限制和 embedding 输入；不能视为分布式服务。[2025 EPD 文章](vllm-epd-2025.html)正文、文字表与说明已读，曲线未数字化；[PR #25233](vllm-epd-pr25233.json)身份及开头、§1–3 已读，未审 diff。合入 2025-11-12，[v0.11.1](vllm-v0111-release.json)发布 11-18，公告 12-15；release 仅核身份与 EC 条目。
- 当前 vLLM 沿用已核身份 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`：[EPD 指南](vllm-epd-current.md)、[ExampleConnector](vllm-ec-example.py)全文；后者是写 CPU safetensors 再加载到设备的调试路径，不当作 RDMA 实测。
- [Qwen3-VL-4B 身份](qwen3-vl4-identity.json)仅核 SHA；[模型配置](qwen3-vl4-config.json)、[预处理配置](qwen3-vl4-preprocessor.json)全文，固定 `ebb281ec70b05090aa6165b016eac8ec08e71b17`。[vLLM 模型](vllm-qwen3-vl.py)只读 570–605、830–897、941–1000、2290–2320、2918–2959：grid、DeepStack 特征拼接与拆分；不登记完整模型审查或任意后端 EPD 支持。
- SGLang [2026-01 EPD 文章](sglang-epd-2026.html)全文与命令、文字表已读，图片曲线未数字化。4／5／6 卡配置分开，不能把增加卡数后的收益全部归给分离；公告关于 ZMQ／RDMA 的简述不代替实际数据路径核查。
- SGLang 固定 `c99d906effa8bd05573995127f0d4a0984c5a96a`：[EPD 指南](sglang-epd-current.mdx)全文，明确传输后端与 global embedding cache 为两个选项；[identity helper](sglang-mm-identity.py)仅 305 行至文件末尾，核内容／预处理／版本身份结构，未审全部调用方。[runtime](sglang-encoder-runtime.py)仅 1–95、1160–1245，核协议分工与取消前完成 encode 的接口；MMEncoder 内部缓存实现不在本轮读取范围。[目录树](sglang-tree.json)仅定位文件。
- [vLLM-Omni 固定树](omni-tree.json)仅定位路径；[DLO backend](omni-dlo-backend.py)只读 194–282、310–393、1698–1766，固定先前 PR #5864 合入 SHA `44e38d7b3879107e501acfd833765ef07c60ace6`。核按 dtype 分片、H2D→AllGather→compute 依赖、完整与分片双缓冲；其余模型加载、topology 与 runner 未作完整审查。

复用既有原件并扩大已读范围：[Ollama 2025 多模态文章](../../../outline-checks/2026-09-07/framework-evolution/ollama-multimodal.html)本轮全文重读；[DLO 文章](../offload-execution/vllm-omni-dlo-2026.html)本轮正文、文字表和评估限制读完；[PR #5864](../offload-execution/vllm-omni-pr5864.json)完整描述已读，diff 未审。DLO 在研究笔记中保留，不新增生成模型教学章节。

与 TriInfer 的比较、模型字节和既有实验变体见[阶段放置案例](../../../../case-studies/multimodal-stage-placement.md)。三篇框架文章的模型、卡数、SLO、图／缓存选项以及测量版本分别保留，没有把历史基线限制扩写为当前框架的普遍不足。
