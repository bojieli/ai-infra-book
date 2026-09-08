# KV 量化：格式与执行路径的版本证据

获取、核读日期：2026-09-08。[sources.json](sources.json)保存 30 份响应原件、URL、时间与哈希；26 份成功，4 份失败。14 份资料有明确的[文本读取范围](reading-proof.json)，其余为定位、身份或未采用的查阅，不等于全部实现已审查。没有运行下载代码或模型。

## vLLM：容量选项逐渐进入 Attention 执行

[v0.5.5 E4M3](vllm-055-e4m3.txt)和 [E5M2](vllm-055-e5m2.txt)文档已读；[发布元数据](vllm-055-release.json)给出 2024-08-23。当时 E4M3 文档只支持 per-tensor scale，通过 JSON 提供，缺省为 1.0。文档的格式动态范围和“有硬件转换便能大幅加速”等概括不作本书定量依据。

[v0.18.0 文档](vllm-018-kv-raw.txt)与[当前固定文档](vllm-current-kv.txt)作完整文本及差异比较：支持静态 per-head 校准，但后端有限制；当前文档删除 warmup 随机 token 校准示例，增加跳过指定层。这里仅描述文档变化，不据此断言所有旧代码已经删除。当前文本仍写“三种”校准方式而实际列两种，这一编辑残留没有沿用。

[2026-04-22 官方文章](vllm-2026-blog.html)的正文、文本表和图注已读，图像未独立查看／数字化。它比较 v0.10.2 与 v0.19.1，讨论 FA3 两级累加的精度／寄存器压力、查询量化融合、tile 调整和跳过短窗口层；FA3 路径还量化 Q 并做低精度 Attention，不能泛指所有 FP8 KV 后端。长 head 的 prefill、短窗口和不同硬件后端分别看。

文章的单并发 H100／Llama 拟合用于解释固定开销与斜率，不推广约 7k 的交点。吞吐实验固定并发 8，不能将收益归因于实际并发翻倍。未校准结果不是所有校准方案的数学下界，聚合 AUC 接近也不证明每个任务无损。历史模型保留原名，未替换为 V4／K3。

当前 SHA `5133e1d28594d5939552003f32b55a3fb18556a1`；[身份响应](vllm-commit.json)只核 SHA 和时间。两次 docs.vllm.ai 的 429 原件保留，后用 GitHub 固定版本文本取得内容。

## SGLang：分开存储配方与每阶段访问

[MLA PR #10078](sglang-fp4-mla-pr.json)合入 2025-11-02，[MHA PR #12612](sglang-fp4-mha-pr.json)合入 2025-11-15。读取身份与声明的正文范围，未读完整 diff／评论。早期 MLA 的 B200／TP4／R1 结果中，FP4 比 FP8 路径快，但二者都比直接使用 BF16 KV 慢，并在给定 SLO 下 goodput 为零。MHA 的 torch_native 对照和其他后端不同，不能推广为最快生产路径；Qwen3 的 AIME25 下降也不能用 GSM8K 近似持平掩盖。

[当前指南](sglang-current-kv.txt)完整文本与表已读，FP4 仍标实验性。它将块 16 的实现放在 MXFP4 说明下，而[固定配方源码](sglang-fp4-recipe.txt)明确区分 `fp4_mx_block16` 与标准块 32，拒绝旧 `fp4_e2m1`／含混 `mxfp4` 名称。本书按实际配方核算，不从“FP4”推断 scale 格式、后端或统一吞吐。

源码读取范围包括存储 dtype、两种配方的分配与容量计算、每阶段访问注册和名称校验；[缓存池](sglang-memory-pool.txt)只核已登记范围的分配、scale 搬移、字节统计与工作区访问。NVFP4 每 16 值一个字节的 scale，另带全局 FP32 scale；该规则中的 FlashInfer prefill 有跨层复用的 FP8 工作区，TRTLLM MHA decode 可消费原生 FP4。block-16 配方走另一套读回规则，不能写成二者都原生执行。新增页、临时张量与模型后端选择仍须实验核验；没有完成量化 kernel／全部模型调用链审查。

当前 SHA `5aab054ec8ce6b6100fbfb7aafe67d632a7df3aa`。整仓库树查询 504、旧文档路径 404 保留，随后由固定 docs 子目录定位新路径。这一轮补 2025→2026 的选择，未声称完成 SGLang 全部 2024 发布史。

## Ollama：相同接口背后的块与后端

[v0.5.0 FAQ](ollama-050-faq.txt)只读第 290–312 行；[发布身份](ollama-050-release.json)为 2024-12-04。它已提供 f16／q8_0／q4_0，要求 Flash Attention。2025 的 [v0.9.6 GGML](ollama-096-blocks.txt)只读 half 类型与两种 block 声明：每 32 个值额外 2 B scale，对应 8.5／4.5 bit/value。

[当前 FAQ](ollama-faq.html)只取 Flash Attention 与 KV 类型两节；相容设备与后端可自动启用 Flash Attention。[当前客户端](ollama-llama-server.txt)只读说明与启动参数：将同一种缓存类型传给 llama-server 的 K、V 选项，按上下文和并行槽位组织启动。固定 Ollama SHA 为 `83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8`，但没有核完该二进制内的全部上游实现；历史 GGML block 定义只支持格式计算，不能冒充当前实测内存，也不能推广到 MLX。

正文与实验落点见[Qwen3 算例](../../../../case-studies/kv-quantization-and-execution.md)。本轮只深化 9.4.4、实验 9-8 与图 9-7，不增加章节或要求读者安装所有框架。
