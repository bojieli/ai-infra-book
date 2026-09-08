# 多 LoRA 服务：共享权重之后还要算什么

2026-09-07 阅读与推算笔记，对应第 5.1、9.2 和 12.3；当前是大纲扩写依据，没有运行多 adapter 性能实验。

## 从论文到当前框架

2024 年 MLSys 的 [Punica](../references/proceedings/MLSys/2024/papers/mlsys2024-054de805fcceb78a201f5e9d53c85908.pdf) 与 [S-LoRA](../references/proceedings/MLSys/2024/papers/mlsys2024-906419cd502575b617cc489a1a696a67.pdf) 都围绕共享基座的多租户服务：普通 GEMM 批量计算 `XW`，不同 adapter 的低秩修正 `X A_i B_i` 分组计算。它们是同期研究；不能仅凭会议年份确定谁先实现。Punica 的 SGMV 与 S-LoRA 的异构 rank、非连续页及统一内存管理各有侧重。

当年的对照包含合并权重后的多进程服务。S-LoRA 的旧基线说明不代表当前 vLLM；当前 [vLLM 固定提交的文档](../references/framework-history/2026-09-07/lora/vllm-lora.md)已描述按请求选择 adapter、并发服务和动态加载。[SGLang 文档](../references/framework-history/2026-09-07/lora/sglang-lora.html)明确引用两篇工作，并讨论加载与执行重叠、热 adapter 固定、排队过久时腾出槽位。这条演进说明瓶颈从“重复存整个模型”移到“低秩执行、状态容量和调度公平性”，并非参数小就没有成本。

[Ollama 的 ADAPTER](../references/framework-history/2026-09-07/lora/ollama-modelfile.html)描述给指定基座构建适配模型；这个入口本身不能证明具有上述异构请求合批能力。接口、真实 runner 和调度方式仍须分别验证。文档原件及 vLLM 提交见[来源清单](../references/framework-history/2026-09-07/lora/sources.json)；vLLM 网页下载遇到 429 后改取上游固定提交文档，未把失败响应归档成正文。

本轮仍需继续核对 2024–2026 各版本的具体进入时间；上面的演进只证明论文设计与当前能力之间的关系，不声称完成逐版本考证。

## 一个可跟算的容量例子

使用第二章固定的 Qwen3-8B 配置：36 层，隐藏宽 4096，Q 投影输出 4096，V 投影输出 1024。教学假设仅在 Q、V 上使用 rank 16 的 BF16 LoRA，无 bias、额外训练模块或量化元数据。

- 每层 Q adapter 参数：`16 × (4096 + 4096) = 131,072`。
- 每层 V adapter 参数：`16 × (4096 + 1024) = 81,920`。
- 每套 adapter：`36 × (131,072 + 81,920) × 2 = 15,335,424 byte = 14.625 MiB`。
- 100 套 adapter：约 `1.428 GiB`。共享一份基座可避免保存 100 份合并权重；是否能全部留在 GPU 还要加入基座、KV、图缓冲和工作区。

同一模型的 BF16 KV 是每历史 token 144 KiB。若 100 个请求各自需要 8,192 token 的独立状态，KV 本身为 `100 × 8192 × 144 KiB = 112.5 GiB`。所以“可提供 100 个 adapter”与“100 个长请求同时运行”完全是两项容量问题。只有满足模型、adapter 版本、位置和状态兼容条件的共同前缀才可能复用；不同 adapter 通常改变隐藏状态，不能仅凭 prompt 相同共享 KV。

对当前批次的某个投影，base 工作约为 `2 B d_in d_out`，LoRA 工作为 `Σ_i 2 B_i r_i (d_in + d_out)`，其中 `Σ_i B_i = B`。FLOPs 很小仍可能出现小矩阵、分组元数据、额外启动与权重搬入；按实际 trace 判断，不能由 FLOPs 比直接计算请求加速比。

## 实验与证据范围

实验 9-3 保留分页基础路径，增加一个多 adapter 变体：固定受支持的 vLLM／SGLang 模型和已验证 adapters，扫描活跃 adapter 数、rank、请求长度和热度倾斜；比较合并后各自服务与共享基座、加载等待及每租户尾延迟。基线须在等资源、等输入与同一数值目标下明确部署方式，不直接采用论文旧版 vLLM 的倍数。

Punica 所读范围为 PDF 第 3–6 页，其评估采用 Llama-2、rank 16、随机 adapter 权重及指定负载。S-LoRA 所读范围为第 3–5、7 页；其 70B 配置脚注说明未采用官方 GQA。书中的 Qwen3 算例独立按配置复算，论文结果只作其自身条件下的机制证据。完整吞吐曲线、张量并行实现与各版本支持矩阵仍待后续核对。
