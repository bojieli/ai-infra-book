# 实验 13-6：长上下文数字员工的自建 serving 成本

本次修订仅采用 **DeepSeek V4 Flash 与 Kimi K3**，两档分别核算。每名员工只有一条串行 Agent 轨迹，持续 24×7 decode；200K／1M 分别表示 **200,000／1,000,000 个实际已占用的历史 token**，包含保留的思考、工具调用和工具返回内容。不从空上下文开始取平均。生成计入所有 decode token，不只统计最终答案。

[RESULTS.md](RESULTS.md) 为简洁结果，[results.json](results.json) 保存全部 240 个情景及被容量排除的候选。它们是**资源模型计算结果，未租 GPU 实测**。旧的 8B 短上下文／API 价格算例已从当前版本移除，历史版本可从 Git 查阅。

最新扩展：[GPU 卡型与官方 API 对照](COMPARISON.md)按同样的持续 Agent 工作负载比较 H100、H200、B200、B300，并计官方 API 输入、缓存和输出账单。原文以下是可独立复现的 B200 基线。

## 复算与输入

从仓库根目录执行：

```sh
python3 experiments/ch13/13-06/single-agent-serving/run.py
python3 -m unittest discover -s experiments/ch13/13-06/single-agent-serving -p 'test_*.py'
```

只依赖 Python 标准库；所有输入冻结于 `long-context-sources`，来源与哈希见 [long-context-manifest.json](long-context-manifest.json)。不依赖仓库中其他尚未提交的 calculations／experiments 文件，也不在运行时访问网络。配置、checkpoint 审计和前向计算取自本书已有核算记录，脚本独立重算状态并与原 1,048,576-token 状态账本交叉检查。

- [DeepSeek V4 Flash 官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)：固定 revision `60d8d70770c6776ff598c94bb586a859a38244f1`；43 层，284B 总参数档，FP4 专家与其他格式混合，1,048,576 上下文上限。以 checkpoint 主干的 **156.016 GB** 载荷核算，排除单独的 MTP。
- [Kimi K3 官方模型卡](https://huggingface.co/moonshotai/Kimi-K3)：固定 revision `f831ab66814297da540d832a5235f8e904f29d06`；93 层，其中 69 层 KDA、24 层 MLA，896 个路由专家每 token 选 16 个，另有共享专家。文本主干 checkpoint 载荷 **1,559.966 GB**。视觉编码／投影不在本题文本 decode 成本内。
- [SGLang K3 serving 文档](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3)：支持用 PP2×TP8 描述 16 张 B200 的布局，区分 DCP 分片与 TP 复制 MLA 缓存。文档本身将部分配置列为待验证起点；这里没有把它们当作匹配本负载的实测部署。
- [Runpod GPU 租金](https://www.runpod.io/pricing)：2026-09-09 公开 B200 Pod 基准为 **$6.79/GPU·h**，用于统一价格归一化；B200 多节点 Cluster 页面要求询价，不能声称该单价已保证 16 卡网络、库存或 SLA。按完整预留 GPU 组支付 720 小时；另购磁盘、网络、控制器、故障冗余和运维未计入。GPU 租金已包含的电力不重复加。
- [NVIDIA DGX B200 规格](https://www.nvidia.com/en-us/data-center/dgx-b200/)：8 卡共 1,440 GB、64 TB/s HBM；模型取每卡 180 GB、8 TB/s。矩阵运算使用 FP8／BF16 效率情景，**不直接把 FP4 存储除以原生 FP4 峰值**。

## 先算放置，不能只加总显存

V4 枚举 TP2／4／8。所有路由专家仍需驻留，不能以 13B 活跃参数代替总权重。主干权重按 TP 切分，窗口、压缩历史和索引历史按共享单表示在各 TP rank 复制。每张卡满足：`权重/TP + B × 每人状态 ≤ 180 GB × 80%`。

V4 每层的压缩倍率为 0／4／128。状态分别包含 128-token 窗口、`floor(L/r) × 512 × 2` 字节的压缩历史；CSA 还保存 `floor(L/4) × 128 × 2` 字节索引。另计 FP32 压缩器缓冲。decode 主 attention 读取窗口与选中压缩条目；**CSA 选择最多 512 条并不免除对全部压缩索引的扫描**。这些缓存没有传统独立 K/V 的额外倍数。

K3 固定比较 PP2×TP8 的 TP 复制与 DCP8 分片布局。93 层按 47／46 切开，逐阶段分别数 MLA／KDA 层。MLA 保留 512+64 维潜变量，BF16 时每层每 token 为 1,152 字节；DCP1 在 TP rank 复制，DCP8 将历史分成八份。KDA 当前 FP32 状态每层 `96×128×128×4` 字节，另计短卷积槽；容量按 **每请求五份 KDA 状态槽** 预留多轮复用所需状态，decode 只读取并更新当前一份。KDA 头在 TP 维切分。

K3 每 rank 权重取 `总载荷/16 × 1.05`，5% 用于层／端点分配不均匀的估算余量；逐阶段状态取较大者。两模型都另留 20% 卡容量作激活、图、通信、分配器和重建暂存余量。没有逐 rank 实际分配记录，不能将这一容量筛选等同于已启动成功。

## 再算每步：内存、矩阵工作和串行开销

专家来自相互独立的员工，不假设共享业务前缀。每个 token 从 E 个专家选 k 个，均匀独立路由情景下，batch B 的预期专家并集为 `U=E×[1−(1−k/E)^B]`。权重读量为路由专家载荷乘 U/E，加非路由载荷；group-32 FP4 权重含量化尺度，实际是 **17/32 字节／参数**。没有把多员工的专家权重完全复用，也没有每人重复读完所有专家。

执行时间按顺序求和：`路由专家 + 其他矩阵/权重 + 长历史 attention + 通信 + 每层其余执行开销`。前三项分别取自身的带宽时间与矩阵时间较大值。路由专家以 32 行 tile 的尾部填充计工作；对每个专家按 `X~Binomial(B,k/E)` 计算 `E[32×ceil(X/32)]`，再加 20% 非均匀／尾部余量。V4 的 32 行来自固定参考 kernel；K3 是需要用所选后端校准的统一执行情景，不声称所有 K3 kernel 都使用该 tile。

非路由部分保守地读完整非路由载荷，含少量不必逐 token 全读的 embedding。attention 计 V4 主 attention 和索引点积，或 K3 compact MLA 的 QK/PV 与当前 KDA 状态读写。K3 MLA 计算每 token 为 `2×24×96×L×(576+512)` FLOPs；KDA／投影／FFN 等固定矩阵工作从冻结的前向账本剥离历史 attention 后复用。softmax、SiTU、mHC、AttnRes、量化转换等非矩阵执行由每层开销近似覆盖，没有宣称完整 kernel 级预测。

**PP 的两个阶段对同一条轨迹是串行的**：decode 时间仅除以 TP，不能再除以 PP。此实现采用同步批次，不给没有调度模型支持的 pipeline 重叠收益。DCP 只分摊缓存和 attention 工作，不重复乘一遍算力。

| 效率情景 | 有效 HBM/规格 | 有效矩阵/所设密集峰值 | 每层其余执行开销 | 每 collective 启动 |
| --- | ---: | ---: | ---: | ---: |
| slow | 35% | 10% | 250 µs | 10 µs |
| central | 50% | 20% | 150 µs | 5 µs |
| fast | 65% | 30% | 75 µs | 3 µs |

计算以每卡密集 FP8 4.5 PFLOPS、BF16 2.25 PFLOPS 为规格基准；central 实际代入 900／450 TFLOPS。这些效率和固定开销**没有由目标模型实测拟合**，三档不是置信区间。通信取每层两次 collective，K3 DCP 再计每 MLA 层两次；使用环式载荷因子 `2(TP−1)/TP`、有效组内带宽 450 GB/s，跨 PP 阶段带宽 25 GB/s 与启动 20 µs。均是待校准的拓扑情景，不把整机 NVLink 总带宽用于每条链路。

## 月费用、产出与 Agent 周期重建

纯 decode 速度 `r=1/t_step`。每人月输出 `2.592r` 百万 token；每人月租 `720×GPU数×6.79/B`。B 是**实际持续在场的独立员工**；单员工没有开 B 个子 Agent。空闲池不能按名义最大 batch 分账。完整账本枚举 20／30 token/s 门槛；正文主情景用 30，未通过的候选保留拒绝原因。不同模型的质量不视为相等。

“持续 decode、prefill 较少”是主表理想基线。真实长期运行不能永远追加同一历史，所以另算重建压力：每生成窗口 10% 的 token，将历史压回约 90% 并重建，decode 按满窗口估算。重建按整个 L 的矩阵工作预算，略高于重建 0.9L；V4 含参考实现的矩形索引扫描，K3 用同一 compact MLA 算法的因果 attention。假定 chunked prefill 能使用整组 GPU，其时间为各类 FLOPs 除以整组有效算力。它不是测量的 TTFT。

**每个员工都要重建**：每轮池内的重建时间为 `B×t_prefill`，周期输出仍是每人 `G=0.1L`；可用于 decode 的比例为 `G×t_step/(G×t_step+B×t_prefill)`。同样的月租除以折损后的输出才得到该情景的单位成本。工具返回的新增 prefill、摘要生成、视觉编码及排队另计，当前重建修正对总开销仍可能偏乐观。此敏感性说明为什么接近满载的 Agent 历史不能总按免费前缀处理。

## 适用边界

K3 紧凑 MLA 是 serving 算法路径，不能直接套到保存展开 K/V 的原始 HF 实现；旧固定 checkpoint 头与参考代码还存在 69 个 A_log 向量 128／96 形状差异，原审计未证明加载／数值兼容。这里使用实际头部字节做容量、配置做逻辑运算，未声称解决运行时加载问题。

本题完成的是有来源、可复算的成本估算。若要把候选变成采购或部署结论，最能改变结果的补测是：固定 backend、TP/PP/DCP、200K／1M 满历史下的每人 decode 间隔、逐 rank 内存和周期重建时间。本轮没有发起收费租卡，也没有推断 API 售价就是自建成本。
