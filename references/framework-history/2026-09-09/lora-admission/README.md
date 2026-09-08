# 多 LoRA：从共享基座到请求准入

2026-09-09。围绕当前 8.2.2／实验 8-3，继续核对多 LoRA 服务的版本、分组执行、adapter 驻留与排队条件。十九份原始 HTTP 响应全部成功；[读取记录](reading.json)有三十七个明确范围，复用十四份已归档文件。未运行下载源码、模型或硬件实验。数学与部署选择收在[现有案例](../../../../case-studies/multi-lora-serving.md)。

## 代表性变化与适用范围

| 时间与来源 | 已核实的变化 | 本书采用的判断 |
| --- | --- | --- |
| vLLM [v0.6.0 文档](vllm-2024-lora.rst.txt)，发布于 2024-09-04 | 已有逐请求 adapter、共享基座及多 adapter 并发入口，受 `SupportsLoRA` 和服务配置限制 | 不能用 S-LoRA 论文中的旧引擎基线描述此后所有 vLLM |
| vLLM [v0.9.2 文档](vllm-2025-lora.md)，发布于 2025-07-07 | 所读动态配置节提供运行时加载、卸载 API | “服务时可加入新 adapter”与“GPU 当前已可执行该请求”分开 |
| SGLang [PR 7216](https://github.com/sgl-project/sglang/pull/7216)，2025-08-11 合入 | 前缀树区分 adapter 身份；该历史实现仍限制 page size、调度策略和 HiCache | 相同 prompt 不足以证明状态可共享；不把当年的限制写成当前限制 |
| SGLang [PR 10286](https://github.com/sgl-project/sglang/pull/10286)，2025-09-15 合入 | 按 adapter 收集 token，再切定长 chunk；针对长短 prefill 混合及 decode 小矩阵空槽 | 低秩 FLOPs 少，不等于启动、padding 和分组成本小 |
| SGLang [PR 15512](https://github.com/sgl-project/sglang/pull/15512)，2026-01-19 合入 | 锁页 adapter、独立复制流与逐请求加载就绪判断 | 异步加载改变可合批集合，需同时检查等待与重用 |
| SGLang [PR 17913](https://github.com/sgl-project/sglang/pull/17913)，2026-05-02 合入 | 对长时间未获准执行的冷 adapter 引入排空策略 | 保持热门 adapter 可省加载，但要计算冷请求等待及吞吐代价 |
| 固定 vLLM [2026 文档](vllm-current-lora.md) | 同名原位替换，以及显式区分 Megatron 风格 2D／PEFT 风格 3D MoE adapter 的入口 | 名称不等于版本，格式不等于只改文件扩展名；这些接口未被本次选读证明为完整 RL 一致性协议 |
| Ollama [2024](../../2026-09-08/overlap-placement/ollama-2024-scheduler.go)、[2025](../../2026-09-08/overlap-placement/ollama-2025-scheduler.go)、[2026](ollama-sched.go.txt) 的 `needsReload` | 三个固定样本都把 AdapterPaths 变化作为重载条件；当前调度入口据此将旧 runner 标记为待退出 | 这条服务路径与单 runner 内按请求切换 adapter 的多租户批处理不同 |

vLLM 样本分别固定于 `32e7db2…`、`a5dd03c…`、`537af2c…`；SGLang 当前路径固定于 `c99d906…`（2026-09-07）；Ollama 固定于 `abed273…`（2024-09-11）、`05d5345…`（2025-09-17）、`83ed7d9…`。完整 SHA、原始来源与叶文件身份在读取记录中；不是完整发布史，也不以文档缺项证明当年功能不存在。SGLang [文档路径历史](sglang-lora-history.json)返回十七条记录，旧目录经过迁移，不能据此认定 LoRA 始于 2025 年。

## 从参数进入执行

[vLLM 调度选读](vllm-current-scheduler.py.txt)先收集已调度运行请求的正 adapter ID；如果加入另一个 ID 会超过 `max_loras`，就暂时跳过该等待请求。此处的种类上限与 token budget、KV 空间、请求数并行存在，不能将注册 adapter 数直接当作并发数。完整 worker 的加载／淘汰、热更新时 KV 失效和全部 MoE 后端未在本次审计。

[SGLang manager](sglang-lora_manager.py.txt)校验批内 adapter 数及 pinned adapter 占用；不在当前批里的 pinned adapter 也占槽位。[overlap loader](sglang-lora_overlap_loader.py.txt)把运行中与尚未完成的加载一起计入容量，事件完成并等待后才返回就绪。[scheduler](sglang-scheduler-admission.py.txt)还先检查 drainer，再检查已运行或加载状态。把 CPU 注册、GPU 槽位、加载完成和当前批次分别画出，才能解释有空闲计算资源却仍在排队。

[drainer](sglang-lora_drainer.py.txt)的说明说排空期间不再接纳新请求，但 `can_schedule()` 实际允许 `max_new_tokens ≤ 1.2 × 当前最大剩余 token 数` 的请求。它用 token 上限估计，不预测真实秒数，也不取消已经在运行的请求。因而不能只凭这一启发式保证等待时间上限；准入、长度和到达条件仍须明确。功能只在所查调度入口的阈值大于零时建立。

[当前文档](sglang-lora.mdx)同时指出异步加载需要锁页内存，可能削弱多 adapter 的 prefill 合批，并非默认无代价。所述 `max_loaded_loras ≤ 2 × max_loras_per_batch` 是该文档的限制说明，本次未核到全部参数校验与后端分支，不将它写成所有版本的通用硬件定律。通用文档列 Triton／CSGMV，不代表当前仓库只有这两种专用实现。

## 评估条件与专用路径

PR 10286 的例子为 Llama-3.1-8B、特定 adapter、ShareGPT 与禁用 radix cache；正文没有给出该测试的 GPU 型号，不能补写。PR 15512 明确使用单 H200：一组把同一大于 1 GB 的 adapter 注册为十六个名称并刻意制造加载 miss，另一组才使用较小 adapters。两组收益不可混成“普遍加速”；链接中的 profiler 截图本次未查看。PR 17913 使用 A100-SXM4-80GB、六个 adapter、三个槽位及固定随机长度。其表格中 P99 TTFT 改善时，中位 TTFT 从 83.30 ms 升到 3728.36 ms，正好说明尾部与中位数要分别看。这里只分析原表条件，不作为本书测量结果。

[2026-07-15 Inkling 公告](https://www.lmsys.org/blog/2026-07-15-inkling-day0-support)的 LoRA Serving 节提供另一种专用实现：基座 GEMM 与低秩路径在两条流上运行，在激活等依赖处汇合；MoE 修正复用基座的专家路由。所读表格为 B200 W4A16、TP8、输入 8192／输出 1024、对称内存开启、关闭推测解码；它比较批内一个与四个 adapter，不能推广为任意模型或任意 LoRA 格式的结果。这里只读该节文字和表格，未查看图 5、未核完整定制内核，也未通读公告其他章节。[归档原件](sglang-inkling-2026.html)

Punica 与 S-LoRA 的已完成论文选读范围保留在旧笔记。本轮新增的是实际框架的准入、等待和专用模型边界，没有新增论文正文阅读或把所有 release notes 写进提纲。实验仍先用同一 Qwen3 算清容量和分组，再选择与实验条件相符的引擎路径。
