# 模型与算子核对笔记

本笔记支持第 2 章的具体模型计算和第 5 章的算子／融合安排。核对日期为 2026-09-07；正式实验与完整算子表在扩写时制作。正文以 Qwen3 跟算，再沿 V4 与 Kimi K3 的真实路径比较，代码清单留在配套材料。

## 固定来源

- Qwen3-8B：[官方配置](../references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json)、[模型仓库 revision](../references/outline-checks/2026-09-07/scaling-history/qwen3-8b-revision.json)、[vLLM Qwen3 实现](../references/outline-checks/2026-09-07/scaling-history/vllm-qwen3.py)。
- DeepSeek-V4-Flash：[模型配置](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-config.json)、[参考实现配置](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-config.json)、[官方参考实现](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-model.py)、[revision](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-revision.json)。
- DeepSeek-V3：[技术报告](../references/files/papers/deepseek-v3.pdf)与[vLLM DeepSeek-V2／V3 路径](../references/outline-checks/2026-09-07/scaling-history/vllm-deepseek_v2.py)。
- 所有下载的 URL 与校验值见[来源记录](../references/outline-checks/2026-09-07/scaling-history/sources.json)；vLLM 提交另见[revision](../references/outline-checks/2026-09-07/scaling-history/vllm-revision.json)。该提交下请求 `models/deepseek_v4.py` 返回 404，模型目录树也未找到 `models/deepseek_v4*`，因此本轮 V4 以官方参考实现为具体依据，不能声称已完成对应 vLLM 后端追踪。

本轮主要比较 **DeepSeek-V4 与 Kimi K3**，状态、计算和访问的详细核对见[资源计算笔记](model-resource-accounting.md)。K3 的配置、NoPE 额外分支与参考缓存路径按固定代码解释；V3 原件保留作历史资料。

## Qwen3-8B 的代表层

固定 36 层，hidden size 4096，FFN intermediate size 12288，32 个 query 头、8 个 KV 头，head dim 128，词表 151936。按数学右乘写矩阵，实际框架权重常按 `[out,in]` 存储。

Q、K、V、O 四个投影共 `2×4096² + 2×4096×1024 = 41,943,040` 个参数；SwiGLU 的两个上投影与一个下投影共 `3×4096×12288 = 150,994,944`。按乘加算 2 FLOPs，投影和 FFN 合计约 `385,875,968m` FLOPs／层，不含注意力位置交互、归一化、激活、残差和输出头。

BF16 KV 每历史 token 为 `2×36×8×128×2=147,456 bytes=144 KiB`；8192 token 为 `1,207,959,552 bytes=1.125 GiB`。GQA 减少 KV 的头数，query 头数仍为 32。把 KV 容量减少倍数直接乘到 QK／AV 全部 FLOPs 上会算错。

已读 vLLM `Qwen3Attention` 的投影、拆头、QK Norm、RoPE、attention 和输出路径，以及 `Qwen3DecoderLayer` 的残差与归一化组织。MLP 复用[已核对的 Qwen2MLP](../references/outline-checks/2026-09-07/scaling-history/vllm-qwen2.py)，其路径为合并的 gate/up 投影、SiluAndMul、down 投影；融合投影在模型代码里可见，底层 attention 后端与实际 kernel launch 取决于设备和配置，仍需扩写时的 trace。

## V4-Flash 的代表层

正式名称为 **DeepSeek-V4-Flash**；DeepSeek-V3 是前一代的独立案例。本次固定的是 V4-Flash 仓库中的配置，不将 0731、Vision 或其他变体混用。

主干 43 层，dim 4096，64 个头，每头 512 维，Q 低秩维度 1024。Q 从 4096 投到 1024，再投到 `64×512=32768`；共享 KV 从 4096 投到 512。输出先按 8 组分别从 `8×512=4096` 投到 1024，再将 `8×1024=8192` 投回 4096。分组输出的第一段不是一块无结构的全连接矩阵，需按组计数。

窗口 128；主干压缩比序列的前两项为 0，之后有 21 层 ratio=4 的 CSA、20 层 ratio=128 的 HCA。配置的压缩比数组还有第 44 项，供主干之外的 MTP 使用，不能数成 44 个主干层。CSA 的 indexer 有 64 头、128 维，最多选择 512 个压缩条目；要分别计压缩器、索引、选择和最终注意力的工作。

每层 256 个路由专家、激活 6 个、1 个共享专家，专家维度 2048。每专家三矩阵共 `3×4096×2048=25,165,824` 参数；每 token 经过 7 个专家的矩阵前向约 `6×4096×2048×7=352,321,536` FLOPs。43 层合计约 15.15 GFLOPs／token，只是专家前向，不是整模型；前反向的专家近似见[训练笔记](training-compute.md)。

参考实现显式包含 RMSNorm、RoPE、量化／反量化、Compressor、Indexer、top-k、稀疏 attention、路由、专家 SwiGLU、共享专家、mHC 与输出头。mHC 保留 4 路残差，进入 attention／FFN 前汇合到 4096 维。参考实现为说明计算而保留的 BF16 缓存、Python 专家循环及简化路径，不能代表生产内核数量或实际部署吞吐。

## 第 5 章的表与实验怎样展开

模型序列采用小尺寸 RNN／Transformer、Qwen3 Dense、Qwen3 MoE、DeepSeek-V3、V4-Flash、Kimi K3。每个模型从一条实际 forward 路径识别逻辑算子，再带入固定形状；状态更新、路由和通信也记录，不能只数 GEMM。

正文拟列“模型—代表形状—逻辑算子—主要中间张量—融合机会”表，展开 Qwen3 与 V4 两条代表链。完整算子清单、实现类／函数定位、后端选择、编译日志和运行 trace 在实验材料中提供；未追踪到的实现保留待补，不从报告猜 kernel 名称与启动数。

对 k 个顺序算子，仅相邻边界保留／取消就有 `2^(k−1)` 种形式划分。这个数说明维护与搜索压力，不意味着所有划分都合法、都可融合或都需要实际枚举；图依赖、布局、片上容量和硬件支持会进一步约束选择。算子编译器以此为主要动机，模型和硬件更新再增加维护维度。

实验比较独立内核、局部融合和重新分块后的融合，计算中间写回、寄存器／共享内存占用及提交开销；用测量验证有争议的收益。原始 FLOPs 不变与实际读取减少分别呈现，编译器的开发效率和程序的运行效率也分别计量。
