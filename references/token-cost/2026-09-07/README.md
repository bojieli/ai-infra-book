# Token 成本调研：原始资料与阅读索引

对应[完整报告](../../../research/token-cost-2023-2026/report.md)，截止 2026-09-07。专题共 67 项一手来源：20 项新下载、47 项复用已保存且哈希核验通过的本地原件；其中 40 份 PDF。另存 18 幅关键网页原图。新增文献原件约 75.8 MB，复用原件不复制、不改写，也不重置其获取日期。

[来源表](sources.tsv) · [原件与文本校验清单](manifest.json) · [阅读记录](../../../research/token-cost-2023-2026/reading-notes.json) · [原图清单](figures.json)

所有来源均保留 URL、实际获取时间、字节数、SHA-256 和本地原件路径；PDF 提取文本只作检索辅助。可变网页按抓取快照引用，显示发布日期未必等于最后更新时间。旧原件的 arXiv 版本按 manifest 与正文记录，不将修订版全文当作首次发布版本。

本轮按问题定向阅读，范围逐项列在下方。没有逐页精读所有 PDF，也没有复现 GPU／模型测量；若表格与正文有差异，报告保留差异。网页 HTML 保留原始响应；研究所需的 vLLM、NVIDIA 与 InferenceX 关键原图另存，其他外链资源不保证完全离线。原图保存不意味着获得出版使用许可。

本目录独立维护来源表与 manifest，不改变主参考库的 230 项统计。重新获取新版本应另开日期目录；归档脚本重跑会验证旧文件哈希并保留旧快照。

## 逐项原件与采用范围

<a id="epoch-prices"></a>

### epoch-prices · LLM inference prices have fallen rapidly but unequally across tasks

[原始网址](https://epoch.ai/data-insights/llm-inference-price-trends) · [本地原件](epoch-prices.html) · [提取文本](text/epoch-prices.txt)

版本／时点：2025-03-12；获取时间：2026-09-07T15:25:59.786383+00:00。

阅读范围：固定门槛表、Methodology、Limitations；提取第一份完整表。采用与边界：报告 §2—3；保留 3:1、排除 reasoning、服务商选择与四舍五入口径。

<a id="ai-index-2025"></a>

### ai-index-2025 · Artificial Intelligence Index Report 2025

[原始网址](https://hai.stanford.edu/assets/files/hai_ai_index_report_2025.pdf) · [本地原件](ai-index-2025.pdf) · [提取文本](text/ai-index-2025.txt)

版本／时点：2025-04；获取时间：2026-09-07T15:26:04.851778+00:00。

阅读范围：Executive Summary 的推理价格条目及 Hardware／Inference cost 图表定位。采用与边界：报告 §1、§3；280 倍起点是 2022 年，非 2023 年 Turbo。

<a id="ai-index-2026"></a>

### ai-index-2026 · Artificial Intelligence Index Report 2026

[原始网址](https://hai.stanford.edu/assets/files/ai_index_report_2026.pdf) · [本地原件](ai-index-2026.pdf) · [提取文本](text/ai-index-2026.txt)

版本／时点：2026-04；获取时间：2026-09-07T15:26:05.264396+00:00。

阅读范围：目录与技术表现／硬件相关部分定向检查；全文价格术语检索。采用与边界：时点交叉检查；没有从报告年份推导截至 9 月的价格倍率。

<a id="price-progress"></a>

### price-progress · The Price of Progress: Algorithmic Efficiency and the Falling Cost of AI Inference

[原始网址](https://arxiv.org/pdf/2511.23455v1) · [本地原件](price-progress-v1.pdf) · [提取文本](text/price-progress.txt)

版本／时点：2025-11-28；获取时间：2026-09-07T15:26:01.230542+00:00。

阅读范围：摘要、§1—4 的方法、结果与局限；附录数据入口。采用与边界：报告 §3、§11—12；benchmark 费用与每 token 价格分开，统计估计不冒充因果消融。

<a id="densing-law"></a>

### densing-law · Densing Law of LLMs

[原始网址](https://arxiv.org/pdf/2412.04315v2) · [本地原件](densing-law-v2.pdf) · [提取文本](text/densing-law.txt)

版本／时点：2024-12-06；获取时间：2026-09-07T15:26:00.841401+00:00。

阅读范围：§1—3、29 模型和五 benchmark 范围、能力密度定义。采用与边界：报告 §4；3.3 个月翻倍是样本内上沿拟合，不作通用外推。

<a id="mtp-meta"></a>

### mtp-meta · Better & Faster Large Language Models via Multi-token Prediction

[原始网址](https://arxiv.org/pdf/2404.19737v1) · [本地原件](mtp-meta-v1.pdf) · [提取文本](text/mtp-meta.txt)

版本／时点：2024-04-30；获取时间：2026-09-07T15:27:28.202795+00:00。

阅读范围：摘要、训练目标与 self-speculative inference 机制定向阅读。采用与边界：报告 §4、§9；训练收益与推理收益分开，不挪用最大加速数。

<a id="llama3-card"></a>

### llama3-card · Meta Llama 3 Model Card

[原始网址](https://raw.githubusercontent.com/meta-llama/llama3/main/MODEL_CARD.md) · [本地原件](llama3-card.md) · [提取文本](text/llama3-card.txt)

版本／时点：2024-04-18 (retrieved main snapshot)；获取时间：2026-09-07T15:26:00.529387+00:00。

阅读范围：base／instruct 两张评测表及模型信息。采用与边界：报告 §4；三项 base 表数值同源，不能用 instruct 分数替换。

<a id="vllm-060"></a>

### vllm-060 · vLLM v0.6.0: 2.7x Throughput Improvement and 5x Latency Reduction

[原始网址](https://vllm-project.github.io/2024/09/05/perf-update.html) · [本地原件](vllm-060.html) · [提取文本](text/vllm-060.txt)

版本／时点：2024-09-05；获取时间：2026-09-07T15:26:00.657213+00:00。

阅读范围：Performance Diagnosis、Enhancements、Benchmarks、Limitations；原图归档。采用与边界：报告 §1、§8；2.7 倍是版本总吞吐，保留 baseline、参数和请求到达条件。

<a id="vllm-v1-launch"></a>

### vllm-v1-launch · vLLM V1: A Major Upgrade to vLLM Core Architecture

[原始网址](https://vllm.ai/blog/2025-01-27-v1-alpha-release) · [本地原件](vllm-v1-launch.html) · [提取文本](text/vllm-v1-launch.txt)

版本／时点：2025-01-27；获取时间：2026-09-07T15:26:01.194837+00:00。

阅读范围：CPU 架构、scheduler、cache 与图执行设计。采用与边界：报告 §8；2025 年 V1 发布，不与 2024 多步调度混同。

<a id="vllm-pr6883"></a>

### vllm-pr6883 · vLLM PR 6883: separate API server and engine

[原始网址](https://api.github.com/repos/vllm-project/vllm/pulls/6883) · [本地原件](vllm-pr6883.json) · [提取文本](text/vllm-pr6883.txt)

版本／时点：2024 (merge date in JSON)；获取时间：2026-09-07T15:26:01.674957+00:00。

阅读范围：PR 正文、merged_at、merge_commit_sha。采用与边界：报告 §8；2024-08-03 合入，分进程不等于修改 CPython。

<a id="vllm-pr7000"></a>

### vllm-pr7000 · vLLM PR 7000: multi-step scheduling

[原始网址](https://api.github.com/repos/vllm-project/vllm/pulls/7000) · [本地原件](vllm-pr7000.json) · [提取文本](text/vllm-pr7000.txt)

版本／时点：2024 (merge date in JSON)；获取时间：2026-09-07T15:26:01.910499+00:00。

阅读范围：PR 正文、merged_at、merge_commit_sha。采用与边界：报告 §8；2024-08-19 合入，多步调度不等于 MTP。

<a id="qwen3-launch"></a>

### qwen3-launch · Qwen3: Think Deeper, Act Faster

[原始网址](https://qwenlm.github.io/blog/qwen3/) · [本地原件](qwen3-launch.html) · [提取文本](text/qwen3-launch.txt)

版本／时点：2025-04-29；获取时间：2026-09-07T15:26:02.005709+00:00。

阅读范围：Introduction、thinking 模式与模型表。采用与边界：报告 §4；小模型对比必须保留思考预算。

<a id="blackwell-inferencex"></a>

### blackwell-inferencex · New SemiAnalysis InferenceX Data: Blackwell Ultra Performance and Cost

[原始网址](https://blogs.nvidia.com/blog/data-blackwell-ultra-performance-lower-cost-agentic-ai/) · [本地原件](blackwell-inferencex.html) · [提取文本](text/blackwell-inferencex.txt)

版本／时点：2026-02-16; living page may be updated；获取时间：2026-09-07T15:26:02.384168+00:00。

阅读范围：低延迟／长上下文条件、软件改进与 Rubin 前景段；原图归档。采用与边界：报告 §6；35 倍是系统条件结果，含软件，不归给单芯片。

<a id="mlperf-60"></a>

### mlperf-60 · MLCommons Releases MLPerf Inference v6.0 Benchmark Results

[原始网址](https://mlcommons.org/2026/04/mlperf-inference-v6-0-results/) · [本地原件](mlperf-60.html) · [提取文本](text/mlperf-60.txt)

版本／时点：2026-04；获取时间：2026-09-07T15:26:02.454990+00:00。

阅读范围：版本发布与基准覆盖说明。采用与边界：方法参照；不将新旧版不同模型结果连成单一历史曲线。

<a id="mlperf-60-reasoning"></a>

### mlperf-60-reasoning · A new GPT-OSS benchmark and DeepSeek R1 updates for latency-optimized reasoning

[原始网址](https://mlcommons.org/2026/03/mlperf-inference-gpt-oss/) · [本地原件](mlperf-60-reasoning.html) · [提取文本](text/mlperf-60-reasoning.txt)

版本／时点：2026-03-24；获取时间：2026-09-07T15:26:02.750953+00:00。

阅读范围：质量评测数据、reasoning effort、TTFT／TPOT 条件。采用与边界：方法参照；保留准确性与性能测量的具体合同，不采用跨版倍率。

<a id="gemini31-lite"></a>

### gemini31-lite · Gemini 3.1 Flash-Lite release

[原始网址](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/) · [本地原件](gemini31-lite.html) · [提取文本](text/gemini31-lite.txt)

版本／时点：2026-03-03；获取时间：2026-09-07T15:26:02.932610+00:00。

阅读范围：发布正文中的价格与 thinking 控制。采用与边界：报告 §3；采用公告价格，不宣称今日最低可购价。

<a id="gemini35-lite"></a>

### gemini35-lite · Gemini 3.6 Flash, 3.5 Flash-Lite, and 3.5 Flash Cyber

[原始网址](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-6-flash-3-5-flash-lite-3-5-flash-cyber/) · [本地原件](gemini35-lite.html) · [提取文本](text/gemini35-lite.txt)

版本／时点：2026-07-21；获取时间：2026-09-07T15:26:03.306651+00:00。

阅读范围：3.5 Flash-Lite 段落价格、速度与质量说明。采用与边界：报告 §3；价格上升不能证明固定能力前沿上涨。

<a id="gqa"></a>

### gqa · GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints

[原始网址](https://arxiv.org/pdf/2305.13245) · [本地原件](../../files/papers/gqa.pdf) · [提取文本](text/gqa.txt)

版本／时点：2305.13245v3；获取时间：2026-09-05T13:28:52.264062+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用GQA／MQA 的 KV 头共享与质量权衡；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="deepseek-v2"></a>

### deepseek-v2 · DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model

[原始网址](https://arxiv.org/pdf/2405.04434) · [本地原件](../../files/papers/deepseek-v2.pdf) · [提取文本](text/deepseek-v2.txt)

版本／时点：2405.04434v5；获取时间：2026-09-05T13:28:52.264531+00:00。

阅读范围：摘要、MLA 机制及与 DeepSeek 67B 的比较。采用与边界：报告 §5；93.3% KV 与 5.76 倍吞吐是不同量，不相乘。

<a id="deepseek-v3"></a>

### deepseek-v3 · DeepSeek-V3 Technical Report

[原始网址](https://arxiv.org/pdf/2412.19437) · [本地原件](../../files/papers/deepseek-v3.pdf) · [提取文本](text/deepseek-v3.txt)

版本／时点：2412.19437v2；获取时间：2026-09-05T13:28:52.264730+00:00。

阅读范围：架构、MTP 机制、§5.4.3；PDF 第 35 页目视核对。采用与边界：报告 §5、§9；671B／37B、85%—90% 和 1.8 TPS 倍率保留范围。

<a id="deepseek-v32"></a>

### deepseek-v32 · DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models

[原始网址](https://arxiv.org/pdf/2512.02556) · [本地原件](../../files/papers/deepseek-v32.pdf) · [提取文本](text/deepseek-v32.txt)

版本／时点：2512.02556v1；获取时间：2026-09-05T13:28:53.061184+00:00。

阅读范围：摘要与 DSA 设计定位。采用与边界：报告 §5；区分 DSA 与 V4 新状态结构，不采用新倍率。

<a id="deepseek-v4"></a>

### deepseek-v4 · DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence

[原始网址](https://arxiv.org/pdf/2606.19348) · [本地原件](../../files/papers/deepseek-v4.pdf) · [提取文本](text/deepseek-v4.txt)

版本／时点：2606.19348v1；获取时间：2026-09-05T13:28:53.405169+00:00。

阅读范围：摘要、图 1 与长上下文资源说明。采用与边界：报告 §5；27% FLOPs 和 10% KV 严格限定于 1M 上下文。

<a id="flashattention2"></a>

### flashattention2 · FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning

[原始网址](https://arxiv.org/pdf/2307.08691) · [本地原件](../../files/papers/flashattention2.pdf) · [提取文本](text/flashattention2.txt)

版本／时点：2307.08691v1；获取时间：2026-09-05T13:28:58.026866+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用工作划分与 IO 优化；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="flashattention3"></a>

### flashattention3 · FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision

[原始网址](https://arxiv.org/pdf/2407.08608) · [本地原件](../../files/papers/flashattention3.pdf) · [提取文本](text/flashattention3.txt)

版本／时点：2407.08608v2；获取时间：2026-09-05T13:28:58.065149+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用Hopper TMA／Tensor Core 异步与低精度；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="vllm"></a>

### vllm · Efficient Memory Management for Large Language Model Serving with PagedAttention

[原始网址](https://arxiv.org/pdf/2309.06180) · [本地原件](../../files/papers/vllm.pdf) · [提取文本](text/vllm.txt)

版本／时点：2309.06180v1；获取时间：2026-09-05T13:29:36.283317+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用PagedAttention 的块管理、碎片和并发；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="sarathi-serve"></a>

### sarathi-serve · Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve

[原始网址](https://arxiv.org/pdf/2403.02310) · [本地原件](../../files/papers/sarathi-serve.pdf) · [提取文本](text/sarathi-serve.txt)

版本／时点：2403.02310v3；获取时间：2026-09-05T13:29:39.624609+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用chunked prefill 与 decode 干扰；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="sglang"></a>

### sglang · SGLang: Efficient Execution of Structured Language Model Programs

[原始网址](https://arxiv.org/pdf/2312.07104) · [本地原件](../../files/papers/sglang.pdf) · [提取文本](text/sglang.txt)

版本／时点：2312.07104v2；获取时间：2026-09-05T13:29:39.842753+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用RadixAttention 与结构化程序执行；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="speculative-decoding"></a>

### speculative-decoding · Fast Inference from Transformers via Speculative Decoding

[原始网址](https://arxiv.org/pdf/2211.17192) · [本地原件](../../files/papers/speculative-decoding.pdf) · [提取文本](text/speculative-decoding.txt)

版本／时点：2211.17192v2；获取时间：2026-09-05T13:29:40.278797+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用并行验证、接受过程与输出分布；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="speculative-sampling"></a>

### speculative-sampling · Accelerating Large Language Model Decoding with Speculative Sampling

[原始网址](https://arxiv.org/pdf/2302.01318v1) · [本地原件](../../files/papers/speculative-sampling.pdf) · [提取文本](text/speculative-sampling.txt)

版本／时点：2302.01318v1；获取时间：2026-09-06T02:53:08.248247+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用修正拒绝采样与目标分布；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="distserve"></a>

### distserve · DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving

[原始网址](https://arxiv.org/pdf/2401.09670) · [本地原件](../../files/papers/distserve.pdf) · [提取文本](text/distserve.txt)

版本／时点：2401.09670v3；获取时间：2026-09-05T13:29:43.063365+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用PD 分离、TTFT／TPOT 与 goodput；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="splitwise"></a>

### splitwise · Splitwise: Efficient Generative LLM Inference Using Phase Splitting

[原始网址](https://arxiv.org/pdf/2311.18677) · [本地原件](../../files/papers/splitwise.pdf) · [提取文本](text/splitwise.txt)

版本／时点：2311.18677v2；获取时间：2026-09-05T13:29:43.728240+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用阶段资源区别与异构放置；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="gptq"></a>

### gptq · GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers

[原始网址](https://arxiv.org/pdf/2210.17323) · [本地原件](../../files/papers/gptq.pdf) · [提取文本](text/gptq.txt)

版本／时点：2210.17323v2；获取时间：2026-09-05T13:40:43.921991+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用训练后权重量化；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="awq"></a>

### awq · AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration

[原始网址](https://arxiv.org/pdf/2306.00978) · [本地原件](../../files/papers/awq.pdf) · [提取文本](text/awq.txt)

版本／时点：2306.00978v6；获取时间：2026-09-05T13:40:43.922244+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用激活感知的权重量化；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="smoothquant"></a>

### smoothquant · SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models

[原始网址](https://arxiv.org/pdf/2211.10438) · [本地原件](../../files/papers/smoothquant.pdf) · [提取文本](text/smoothquant.txt)

版本／时点：2211.10438v7；获取时间：2026-09-05T13:40:44.893534+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用激活异常值迁移与 W8A8；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="llama3"></a>

### llama3 · The Llama 3 Herd of Models

[原始网址](https://arxiv.org/pdf/2407.21783) · [本地原件](../../files/papers/llama3.pdf) · [提取文本](text/llama3.txt)

版本／时点：2407.21783v3；获取时间：2026-09-05T13:40:46.080082+00:00。

阅读范围：训练／数据与模型规模相关章节定向阅读。采用与边界：报告 §4；作为更充分训练与数据配方证据，不估计单项贡献。

<a id="qwen3"></a>

### qwen3 · Qwen3 Technical Report

[原始网址](https://arxiv.org/pdf/2505.09388v1) · [本地原件](../../files/papers/qwen3.pdf) · [提取文本](text/qwen3.txt)

版本／时点：2505.09388v1；获取时间：2026-09-06T02:53:10.070029+00:00。

阅读范围：训练与 thinking budget 相关内容定向阅读。采用与边界：报告 §4；任务成本不能仅按参数量比例计算。

<a id="deepseek-r1"></a>

### deepseek-r1 · DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning

[原始网址](https://arxiv.org/pdf/2501.12948v2) · [本地原件](../../files/papers/deepseek-r1.pdf) · [提取文本](text/deepseek-r1.txt)

版本／时点：2501.12948v2；获取时间：2026-09-06T02:53:10.361309+00:00。

阅读范围：蒸馏描述与小模型对比部分。采用与边界：报告 §4；蒸馏推理能力的代表路径，不当作无代价压缩。

<a id="deepseek-infra"></a>

### deepseek-infra · Insights into DeepSeek-V3: Scaling Challenges and Reflections on Hardware for AI Architectures

[原始网址](https://arxiv.org/pdf/2505.09343v2) · [本地原件](../../files/papers/deepseek-infra.pdf) · [提取文本](text/deepseek-infra.txt)

版本／时点：2505.09343v2；获取时间：2026-09-06T02:53:11.584410+00:00。

阅读范围：摘要、生产部署／并行与通信机制。采用与边界：报告 §5、§10；组合系统设计，未复现吞吐。

<a id="deepseek-serving-report"></a>

### deepseek-serving-report · Day 6: DeepSeek-V3/R1 Inference System Overview

[原始网址](https://raw.githubusercontent.com/deepseek-ai/open-infra-index/56d86855fcf6e08fdfd45ce6280bd24322c93351/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) · [本地原件](../../files/documents/deepseek-serving-report.md) · [提取文本](text/deepseek-serving-report.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-06T02:53:11.765800+00:00。

阅读范围：公开服务概述全文。采用与边界：报告 §10；架构与运行情况，不用理论收入推实际利润。

<a id="nvidia-a100-80-spec"></a>

### nvidia-a100-80-spec · NVIDIA A100 80GB datasheet — December 2020

[原始网址](https://www.nvidia.cn/content/dam/en-zz/zh_cn/Solutions/Data-Center/a100/pdf/a100-80gb-datasheet-update-a4-nvidia-1485612-r13-web_zhCN.pdf) · [本地原件](../../files/specs/nvidia-a100-80-spec.pdf) · [提取文本](text/nvidia-a100-80-spec.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-05T15:47:49.864715+00:00。

阅读范围：第 1 页规格表，区分 SXM／PCIe 和稀疏峰值。采用与边界：报告 §6；80GB SXM、2039GB/s。

<a id="nvidia-h100-spec"></a>

### nvidia-h100-spec · NVIDIA H100 Product Specifications

[原始网址](https://www.nvidia.com/en-us/data-center/h100/) · [本地原件](../../files/specs/nvidia-h100-spec.html) · [提取文本](text/nvidia-h100-spec.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-05T13:29:02.884939+00:00。

阅读范围：SXM 规格表。采用与边界：报告 §6；80GB、3.35TB/s，未把稀疏峰值当稠密。

<a id="nvidia-blackwell-brief"></a>

### nvidia-blackwell-brief · NVIDIA Blackwell Architecture Technical Brief

[原始网址](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf) · [本地原件](../../files/specs/nvidia-blackwell-brief.pdf) · [提取文本](text/nvidia-blackwell-brief.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-05T13:34:58.563659+00:00。

阅读范围：晶体管、工艺、双芯粒、低精度与系统规格相关段落。采用与边界：报告 §6—7；形态和历史频点不混用。

<a id="nvidia-rubin-arch"></a>

### nvidia-rubin-arch · Inside NVIDIA Rubin GPU Architecture

[原始网址](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/) · [本地原件](../../files/documents/nvidia-rubin-arch.html) · [提取文本](text/nvidia-rubin-arch.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-05T14:25:18.330692+00:00。

阅读范围：架构说明、精度、数据通路与发布状态定位。采用与边界：报告 §6；不把预期十倍收益当已实测的历史降幅。

<a id="eagle3"></a>

### eagle3 · EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test

[原始网址](https://arxiv.org/pdf/2503.01840v3) · [本地原件](../../files/papers/eagle3.pdf) · [提取文本](text/eagle3.txt)

版本／时点：2503.01840v3；获取时间：2026-09-06T02:53:08.475124+00:00。

阅读范围：摘要、草稿特征与训练设计、batch 相关结果定位。采用与边界：报告 §9；仅采用机制，未搬用最大速度作为普遍结果。

<a id="sglang-v04-2024"></a>

### sglang-v04-2024 · SGLang v0.4，2024-12

[原始网址](https://www.lmsys.org/blog/2024-12-04-sglang-v0-4/) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/sglang-v04.html) · [提取文本](text/sglang-v04-2024.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:52.041349+00:00。

阅读范围：scheduler 与 cache-aware routing 设计说明。采用与边界：报告 §8；异步重叠与缓存路由的历史定位。

<a id="sglang-hicache-2025"></a>

### sglang-hicache-2025 · SGLang HiCache，2025-09

[原始网址](https://www.lmsys.org/blog/2025-09-10-sglang-hicache/) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/sglang-hicache.html) · [提取文本](text/sglang-hicache-2025.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:51.766325+00:00。

阅读范围：缓存层次、取回与 benchmark 条件。采用与边界：报告 §10；只采用多层缓存机制。

<a id="sglang-hisparse-2026"></a>

### sglang-hisparse-2026 · SGLang HiSparse，2026-04

[原始网址](https://www.lmsys.org/blog/2026-04-10-sglang-hisparse/) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/sglang-hisparse.html) · [提取文本](text/sglang-hisparse-2026.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:52.371282+00:00。

阅读范围：Why sparse attention、Design、Swap-in 说明。采用与边界：报告 §5、§10；稀疏访问和总历史状态分别核算。

<a id="sglang-unified-cache-2026"></a>

### sglang-unified-cache-2026 · SGLang Unified Radix Cache，2026-08

[原始网址](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/sglang-unified-cache.html) · [提取文本](text/sglang-unified-cache-2026.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:52.538370+00:00。

阅读范围：Introduction、safe reuse boundary、组件与 HiCache。采用与边界：报告 §8、§10；混合模型的前缀复用需语义兼容。

<a id="sglang-graph-2026"></a>

### sglang-graph-2026 · SGLang Advanced CUDA Graph，2026-08

[原始网址](https://www.lmsys.org/blog/2026-08-17-advanced-cuda-graph/) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/sglang-graphs.html) · [提取文本](text/sglang-graph-2026.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:52.549779+00:00。

阅读范围：图捕获、Breakable CUDA Graph 与回退说明。采用与边界：报告 §7；可捕获区段与 eager 分开。

<a id="vllm-afd-2026"></a>

### vllm-afd-2026 · vLLM AFD Plugin，2026-07

[原始网址](https://vllm-project.github.io/2026/07/23/vllm-afd-plugin.html) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/vllm-afd.html) · [提取文本](text/vllm-afd-2026.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:51.215203+00:00。

阅读范围：插件架构、通信与限制。采用与边界：报告 §8、§10；实验性 AFD 与传统 PD 不混同。

<a id="ollama-mtp-2026"></a>

### ollama-mtp-2026 · Ollama MLX 多 token 预测，2026-06

[原始网址](https://ollama.com/blog/faster-gemma-4-mlx-mtp) · [本地原件](../../outline-checks/2026-09-07/framework-evolution/ollama-mtp.html) · [提取文本](text/ollama-mtp-2026.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T14:29:53.068904+00:00。

阅读范围：草稿／验证、动态长度、状态恢复与版本说明。采用与边界：报告 §9；本地 MLX 的工程案例，未复现性能。

<a id="dflash-paper"></a>

### dflash-paper · DFlash paper v1

[原始网址](https://arxiv.org/pdf/2602.06036v1) · [本地原件](../../outline-checks/2026-09-07/systems-cases/dflash-paper.pdf) · [提取文本](text/dflash-paper.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T13:01:03.029850+00:00。

阅读范围：摘要与并行扩散草稿机制。采用与边界：报告 §9；草稿来源变化，不声称任意场景的加速。

<a id="eagle31"></a>

### eagle31 · EAGLE 3.1 — EAGLE, vLLM, TorchSpec teams

[原始网址](https://vllm.ai/blog/2026-05-26-eagle-3-1) · [本地原件](../../outline-checks/2026-09-07/systems-cases/eagle31.html) · [提取文本](text/eagle31.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T13:01:02.701449+00:00。

阅读范围：Innovations 与实际 batch／部署条件。采用与边界：报告 §9；2026 草稿工程持续改进。

<a id="nvidia-h200-systems"></a>

### nvidia-h200-systems · NVIDIA H200 official specifications

[原始网址](https://www.nvidia.com/en-us/data-center/h200/) · [本地原件](../../outline-checks/2026-09-07/systems-cases/nvidia-h200-systems.html) · [提取文本](text/nvidia-h200-systems.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T13:12:46.457251+00:00。

阅读范围：产品正文与规格表。采用与边界：报告 §6；141GB、4.8TB/s。

<a id="llama1-v1"></a>

### llama1-v1 · LLaMA 原始技术报告 v1

[原始网址](https://arxiv.org/pdf/2302.13971v1) · [本地原件](../../outline-checks/2026-09-07/scaling-history/llama1-v1.pdf) · [提取文本](text/llama1-v1.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T11:46:39.256356+00:00。

阅读范围：训练目标与推理预算的背景定位。采用与边界：历史参照；未新增直接定量引用。

<a id="llama31-card"></a>

### llama31-card · Llama 3.1 官方模型卡

[原始网址](https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama3_1/MODEL_CARD.md) · [本地原件](../../outline-checks/2026-09-07/scaling-history/llama31-card.md) · [提取文本](text/llama31-card.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T11:46:38.826636+00:00。

阅读范围：模型类型与评测表交叉检查。采用与边界：历史参照；报告使用 Llama 3 同源 base 对照，未混入此表。

<a id="gemma2"></a>

### gemma2 · Gemma 2: Improving Open Language Models at a Practical Size

[原始网址](https://arxiv.org/pdf/2408.00118v3) · [本地原件](gemma2-v3.pdf) · [提取文本](text/gemma2.txt)

版本／时点：2024-10-02 (v3); first report 2024-07-31；获取时间：2026-09-07T15:27:30.150315+00:00。

阅读范围：§3、§5 与表 13；PDF 第 7 页目视核对。采用与边界：报告 §4；蒸馏路径与 MMLU 71.3，保留表注中的评测差异。

<a id="mooncake"></a>

### mooncake · Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving

[原始网址](https://arxiv.org/pdf/2407.00079) · [本地原件](../../files/papers/mooncake.pdf) · [提取文本](text/mooncake.txt)

版本／时点：2407.00079v4；获取时间：2026-09-05T13:29:44.031033+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用KV 中心化分离与多层存储；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="routellm"></a>

### routellm · RouteLLM: Learning to Route LLMs from Preference Data

[原始网址](https://arxiv.org/pdf/2406.18665) · [本地原件](../../files/papers/routellm.pdf) · [提取文本](text/routellm.txt)

版本／时点：2406.18665v4；获取时间：2026-09-05T13:29:49.901835+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用基于偏好的强弱模型路由；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="frugalgpt"></a>

### frugalgpt · FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance

[原始网址](https://arxiv.org/pdf/2305.05176) · [本地原件](../../files/papers/frugalgpt.pdf) · [提取文本](text/frugalgpt.txt)

版本／时点：2305.05176v1；获取时间：2026-09-05T13:29:50.150368+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用模型级联与质量费用权衡；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="flashinfer"></a>

### flashinfer · FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving

[原始网址](https://arxiv.org/pdf/2501.01005v2) · [本地原件](../../files/papers/flashinfer.pdf) · [提取文本](text/flashinfer.txt)

版本／时点：2501.01005v2；获取时间：2026-09-06T02:53:06.812280+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用服务 attention 的布局、调度与内核定制；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="s-lora"></a>

### s-lora · S-LoRA: Serving Thousands of Concurrent LoRA Adapters

[原始网址](https://arxiv.org/pdf/2311.03285v3) · [本地原件](../../files/papers/s-lora.pdf) · [提取文本](text/s-lora.txt)

版本／时点：2311.03285v3；获取时间：2026-09-06T02:53:09.250586+00:00。

阅读范围：摘要与机制相关段落定向查阅。采用与边界：采用共享基座、多 adapter 与状态管理；不声称全文逐页精读或复现实验，不搬用最大加速数。

<a id="amd-mi350x"></a>

### amd-mi350x · AMD Instinct MI350X GPU Datasheet

[原始网址](https://www.amd.com/content/dam/amd/en/documents/instinct-tech-docs/product-briefs/amd-instinct-mi350x-gpu-brochure.pdf) · [本地原件](../../files/specs/amd-mi350x.pdf) · [提取文本](text/amd-mi350x.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-05T14:20:44.788713+00:00。

阅读范围：官方产品规格与低精度支持。采用与边界：报告 §6；补充非 NVIDIA 路径，不作跨平台成本排名。

<a id="beyond-chinchilla-icml24"></a>

### beyond-chinchilla-icml24 · Beyond Chinchilla-Optimal，ICML 2024 正式全文

[原始网址](https://raw.githubusercontent.com/mlresearch/v235/main/assets/sardana24a/sardana24a.pdf) · [本地原件](../../outline-checks/2026-09-07/beyond-chinchilla-icml24.pdf) · [提取文本](text/beyond-chinchilla-icml24.txt)

版本／时点：版本／日期见原件与 manifest；获取时间：2026-09-07T11:17:12.227041+00:00。

阅读范围：推理成本目标、§4—5 的实验范围与外推限制。采用与边界：报告 §4、§11；47 模型／150M—6B，10,000 token/参数仅150M，不泛化到所有规模。

<a id="inferencex-gb300"></a>

### inferencex-gb300 · InferenceX: GB300 vs GB200 on DeepSeek-V4-Pro

[原始网址](https://inferencex.semianalysis.com/blog/gb300-nvl72-vs-gb200-nvl72-dsv4-pro-vllm-fp4) · [本地原件](inferencex-gb300.html) · [提取文本](text/inferencex-gb300.txt)

版本／时点：2026-05-27；获取时间：2026-09-07T15:28:50.868254+00:00。

阅读范围：全文的模型、ISL／OSL、配置、TCO 与原始显示表；数值复算；原图归档。采用与边界：报告 §6；显示值复算约2.36，保留文中2.31的差异；未取得完全匹配插值轨迹。

<a id="inferencex-v4-evolution"></a>

### inferencex-v4-evolution · InferenceX: DeepSeek-V4 Day 0 to Day 43

[原始网址](https://inferencex.semianalysis.com/blog/deepseekv4-16t-day-0-to-day-43-performance) · [本地原件](inferencex-v4-evolution.html) · [提取文本](text/inferencex-v4-evolution.txt)

版本／时点：2026-06-09；获取时间：2026-09-07T15:28:49.454750+00:00。

阅读范围：Day 0、单序列 KV、fallback 和多周优化段落。采用与边界：报告 §8；初始支持与成熟基线分开，不采用100倍为普遍结论。


<a id="kimi-linear"></a>

### kimi-linear · Kimi Linear: An Expressive, Efficient Attention Architecture

[原始网址](https://arxiv.org/pdf/2510.26692) · [本地原件](../../files/papers/kimi-linear.pdf) · [提取文本](text/kimi-linear.txt)

版本／时点：2510.26692v2；获取时间：2026-09-05T13:28:54.844191+00:00。

阅读范围：摘要、KDA 与混合注意力架构说明。采用与边界：有限递推状态与混合全注意力分别核算，不采用最大解码倍率。
