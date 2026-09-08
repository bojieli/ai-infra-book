# 集合通信的实际路径与等待来源

2026-09-08 调研笔记，供提纲扩写和实验制作使用。NSDI 2024 本轮筛读前 42 篇完整摘要，选读 rPCIeBench 与 MegaScale 的设计、评估及限制；[阅读记录](../research/2026-infra-survey/reading-nsdi-2024.md)标明页码。另对照八份[框架源码与文档](../references/framework-history/2026-09-08/collective-paths/README.md)。没有运行 GPU、模型或下载的程序。

## 先分清链路上界与实际分配

rPCIeBench 在 GigaIO FabreX、PCIe Gen3 主机和 Alveo U55C 上分别测事务、DMA 操作及竞争路径。它观察到两种不同的分配：同一路径中两个流的带宽与在途字节相关；不同入口竞争通信端口时接近按入口做 max-min 分配。因此，“两项任务平分 PCIe”不能直接作为预算。方向相反或路径正交时干扰很小，也是该实验的观察，需要核对实际端点和共享资源。[正式论文 §4–5](https://www.usenix.org/system/files/nsdi24-hou.pdf)

其模型先输入单流实测带宽、拓扑与边容量，再估共享流量。表 2 的三个验证场景平均误差分别为 2.94%、5.15%、11.32%；最后一组中，预计各 4.37 GB/s 的两条流实际为 3.58／3.59 GB/s，作者怀疑是 MMIO 竞争降低了有效容量。采用的是“先算上界，再测遗漏资源”的方法；不把论文算法当成所有 PCIe／CXL／UB 的精确预测器，也不将平均误差当成每条流的保证。[正式论文 §6.4](https://www.usenix.org/system/files/nsdi24-hou.pdf)

第 7.3.2 节已有 `在途数 ≈ 带宽 × 完成时延 / 每次返回字节`。增加一个与 KV／专家数据读取有关的教学输入：目标有效单向 40 GB/s，每个独立读事务返回 256 B，完成时延 2 μs，则至少约 313 个在途事务；只允许 128 个时，窗口上界为 16.384 GB/s。若完成时延升到 4 μs，需要约 625 个。这里用完整读取等待时间；增加并发可能引起排队，不能用原时延保证达到目标。合并大块 DMA、增加在途读取和提高线速解决的限制不同。

这些数是本书教学输入，未从 Gen3 测点外推当前设备。第 7.2.3 节多 NIC 算例继续用两端共享路径与割集约束；本次补充说明即使总量未越界，也不能凭空指定每个任务所得带宽。

## 从归约消息到框架选择

Qwen3-8B 隐藏维度 4096，BF16 的每 token 行为 8 KiB。简单 TP 输出归约在 1、4、16 个 token 时分别有 8、32、128 KiB 输入，8192-token prefill 则为 64 MiB。输入大小不是每条物理链路的实际字节，后者仍由算法计算。

沿第 6.4.3 节的 ring 教学假设，8 个参与者、每轮启动 2 μs、有效单向 50 GB/s，对 8 KiB 输入估得每次约 28.287 μs。若采用每层 attention／MLP 各一次归约的普通 TP 执行，36 层合计约 2.037 ms。将带宽翻倍仅省约 10.32 μs；将每轮启动项减半省约 1.008 ms。两项都只计这 72 次归约，未包含模型计算、KV 读取、框架提交或融合；实际库也未必选 ring。这使小 batch 的执行优化有了明确理由，而非把标称链路带宽直接当成 decode 延迟。

vLLM v0.6.0（2024-09）与 v0.9.2（2025-07）选读源码都使用同节点 custom all-reduce、P2P／NVLink 和输入条件检查；eager 输入先复制到已注册缓冲，图捕获可注册所用地址。不能将旧注释中“复制通常不足 1%”当作所有形状的实测。两版发布日期已在[图执行来源](../references/framework-history/2026-09-08/graph-selection/README.md)核对。

2026 固定提交则有多条分派路径。只看 `should_nccl_symm_mem_allreduce`：在 symmetric memory 已启用、batch invariance 未启用等条件下，8 个参与者对 ≤16 KiB 和 ≥128 KiB 的输入允许该路径，中间区间偏向 custom AR；前述三种 Qwen 消息就可能跨过边界。完整 dispatcher 还要检查 FlashInfer 等优先路径，不能将这个 helper 的返回值当作最终执行证明。表中的 H100／GB200 历史测点也不是通用性能曲线。[固定 helper](https://github.com/vllm-project/vllm/blob/51da0ca66c8065619c79e35dff97aa99aeaf5644/vllm/distributed/device_communicators/all_reduce_utils.py)、[dispatcher](https://github.com/vllm-project/vllm/blob/51da0ca66c8065619c79e35dff97aa99aeaf5644/vllm/distributed/device_communicators/cuda_communicator.py)

另一个边界是参与者和操作：当前 `CustomAllreduce` 类名单含 16，但 `should_custom_ar` 仍拒绝超过 8 个参与者；新 AG／RS 的 16 参与者路径另受跨节点 MNNVL、组级 rendezvous、multicast、dtype、形状和容量检查约束。该类的旧同节点说明尚在，必须看具体分支。MNNVL 也不等于任意 InfiniBand／以太网跨机组都可用；这些源码不证明整套模型配置必然支持或更快。[固定实现](https://github.com/vllm-project/vllm/blob/51da0ca66c8065619c79e35dff97aa99aeaf5644/vllm/distributed/device_communicators/custom_all_reduce.py)

## 融合要保持通信组和数据含义

在第 5 章片内融合之后，第 6 章用真实框架解释跨卡边界：归约结果还要加残差、做 RMSNorm，可能继续量化。融合有机会减少中间张量搬运和 kernel 启动，但必须覆盖原有参与者，并保留后续需要的残差。

vLLM 当前融合文档将小 token 数的 AllReduce＋RMSNorm 与大 token 数的 SP／AsyncTP 分开；后者先改变布局，再让 GEMM 与 AG／RS 重叠。文档的 TP＋DP／PP 问题、架构条件和自动阈值须在实验提交重核，不当作永恒限制；特别不能假设 Qwen3-8B 自动进入文档所述 `hidden_size >= 8192` 的 SP 路径。[固定文档对应原件](../references/framework-history/2026-09-08/collective-paths/vllm-current-fusions.md)

SGLang 当前选读实现也检查硬件、token 数、DP attention、散布布局和是否最后一层。MoE 的 EP 与专家内 TP 同时大于 1 时，不能用只覆盖一个通信组的融合替掉原来两个组的归约；代码因此关闭这一跨层融合。此例直接接回第 6.3 节的分组与数据所有权。[固定层间实现](https://github.com/sgl-project/sglang/blob/c99d906effa8bd05573995127f0d4a0984c5a96a/python/sglang/srt/layers/communicator.py)

实验 6-5 用公开 fused collective benchmark 的真实接口作为制作参照：先比较等 dtype、等 residual 语义的普通与融合路径，保留 graph、workspace、oneshot／twoshot 和基线是否编译的条件，再放回 TP 模型看逐 token 延迟。README 的示例表不当本书实测，也不把混合精度收益单独归给融合。[benchmark 说明](../references/framework-history/2026-09-08/collective-paths/sglang-current-fused-collective-readme.md)

## 等通信，也可能是在等更晚到达的计算

MegaScale 的 §3.2 按 DP／PP／TP 依赖安排重叠：梯度或参数分块有首尾暴露；PP 发送和接收不必总是绑定等待；TP／SP 可分块流水 FFN GEMM 与通信。采用的是依赖分析，不能将所有通信时间直接从步时减去。其 §6.3 又发现网络带宽稳定时 reduce-scatter 等待逐步增加，最终追到 rank 进入通信的时间偏差，包括前向路径中的垃圾回收和部分 PyTorch 操作。[正式论文](https://www.usenix.org/system/files/nsdi24-jiang-ziheng.pdf)

为实验 7-10 增加一个故意简化的同步例子：四个 rank 在 0、0、0、2 ms 时准备好，假定全部就绪后还有 0.4 ms 交换，则最早等待者看到 2.4 ms，最后到达者只看到 0.4 ms。把交换减半只省 0.2 ms；消除就绪偏差则省 2 ms。真实集合操作可以分块提前推进，所以这个例子用于区分等待来源，不能替代逐 rank 的时间线。跨机时间轴需要对齐误差说明。

MegaScale 的规模和基线保持历史条件：集群叙述截至 2023-09，使用 NVIDIA Ampere GPUs；论文未在所读实验段给出具体 A100／A800 型号，不能自行补齐。Megatron-LM 基线是 2023-01-11 的 `285068c8`，模型为 175B／530B，序列长 2048。它也不是 2025 年的 MegaScale-Infer。

表 2 中，175B、TP=8、PP=8、固定全局 batch 6144，从 3072 卡的 23.66 s 到 12288 卡的 6.34 s：卡数四倍，步时加速约 3.732，扩展效率约 93.30%；每个 DP 副本的序列数从 128 降到 32，按论文报告吞吐估算 300B token 的纯训练用时约 1.75 天。这个数不包含完整项目的数据准备、失败和评估，也不能再把不同 batch 的 256 卡行接成同一条强扩展曲线。

表 3 的消融则同时引入 PTB、SWA、重叠、算子及 LAMB，最后 batch 从 256 到 768；网络优化对双方已开启。其增量不能解释为“网络单项带来全部 MFU 改善”。13B 的收敛微实验和另一个未公开细节的生产训练也不能代替当前 V4／K3 的等质量验证。初始化的 1047→361→不足 5 秒是旧栈在 2048 卡上的工程记录，说明恢复不仅是读检查点；不是当前 PyTorch 初始化性能声明。[正式论文 §3.5、§6](https://www.usenix.org/system/files/nsdi24-jiang-ziheng.pdf)

本次只深化 6.4.4、7.3.2、7.6.3、11.3.2／11.4.3，修改现有实验 6-5、7-5、7-10 与对应配图，并为 I12 加追问。论文阅读、框架源文件选读和教学算式分开留证；章节数、实验数和精选题数保持。
