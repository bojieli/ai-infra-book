# 通信调优、计算争用与卸载

2026-09-08 的提纲研究笔记。已读 AutoCCL（NSDI 2025）物理页 2–14 的设计、评估和限制，13 页均与正式整卷核对；图注文和表格已读，曲线未独立量化。[论文记录](../research/2026-infra-survey/reading-nsdi-2025.md)与[框架原件](../references/framework-history/2026-09-08/communication-tuning/README.md)分别保存正文范围、发布日期、源码提交及失败响应。本轮只做来源研究和教学算术，没有运行通信库、模型或下载的代码。

## 从同一模型的两段工作判断配置

承接第 6.4.4，先用固定 Qwen3-8B 配置确定工作量：1024 个 token 的 BF16 `[1024,4096]` 输出是 8 MiB；TP=8 时，三个 FFN 投影在每卡合计约 38.65 GFLOPs。这里忽略激活函数等非矩阵操作，假定三块权重均匀切分。当前微批的 FFN 依赖其上游数据，不能凭空与同一条链上的依赖通信重叠；下面比较的是执行图已经允许重叠的两个微批片段。

给出两组**教学计时输入**，并非 A40、Qwen3 或 AutoCCL 的测量。通信 A／B 在独占时分别需 0.24／0.18 ms，单看通信会选 B。两段同时运行时，A 下的计算／通信为 0.44／0.26 ms，B 下为 0.62／0.20 ms；若同刻就绪、最后汇合，片段耗时分别为 0.44／0.62 ms。B 的通信独占速度高 33.3%，该并发片段却慢 40.9%。瓶颈从搬移转到了争用后的计算，不应只报告通信带宽。

如果搜索、插桩和配置切换相对于基线额外花了 12 ms，改回 A 每次省 0.18 ms，还需至少执行 67 次才严格回本；余下 50／100 次的净收益分别为 −3／6 ms。成本按整个搜索过程相对默认路径的额外时间计，不把在线试跑称为免费。完整步骤可能还有未受影响的计算、通信与等待，不能把片段的 1.41 倍差异写成全模型加速比。[输入与复算](../research/2026-infra-survey/arithmetic.json)

## AutoCCL 增加的判断与适用条件

论文先区分算法／协议／传输实现，再搜索通道、线程和 chunk 等资源分配；在训练重复调用中记录通信时间，让反馈包含实际并发干扰。配置按操作、消息大小、通信组区分，组内同步更新，避免各 rank 使用不相容的选择。其直接搜索目标仍是通信性能；整步训练收益由另一次评估给出，不是对所有 workload 的整体最优保证。[正式论文 §3–6](https://www.usenix.org/system/files/nsdi25-xu-guanbin.pdf)

采用其方法，保留其历史边界：基于 NCCL 2.18.3，训练使用 PyTorch 2.1／MegatronLM；两组平台为 16／32 张 A40。所谓 NVLink 组的八卡内部实际是四对 NVLink，不能画成全互联 NVSwitch；另一平台还存在部分 GPU 不可 P2P。模型为论文所列 Phi-2、Llama-3.1-8B、Yi-1.5-34B 和 VGG19，不能换名后当成 V4／K3 的结果。作者当前固定 README 仍要求其修改后的 NCCL 库和 tuner 一起加载，不证明可以把该插件直接插入任意新版 NCCL。

论文表 6 的 AllGather 在重计算干扰下为 18.26→32.44 GB/s；这是通信测量。整步图 11 报告约 1.07–1.32 倍训练速度，1.32 倍对应耗时下降约 24.2%，不能沿用正文“时间改善 32%”的含混口径。图 9 的 AG+I 标注与正文列出的倍率有差异，本书不采用该点的精确数值。§6.1 同列 CUDA 12.1 和驱动 470.63.01，未独立复现兼容环境；也不把论文模型规模标签当成官方参数清单。

§4 以定性模型和单变量实验支持单峰近似，这不证明任意硬件、离散候选与多维耦合下的全局最优。其串行阶段描述与 `min` 带宽表达需要流水条件才能相容，不照搬为本书通用算式。§8 还指出不当参数可能导致饱和或失败；这里只让实验搜索固定版本公开支持的小范围，保留正确性校验与回退。论文关于恢复成本可忽略的判断也不覆盖本书的长任务。

## 2025–2026 的库接口怎样改变实验

NVIDIA 2025-07-22 的调优说明把默认成本模型与动态 CTA／chunk 调度分开，建议针对具体操作局部覆盖。多给 CTA 可能改善独占 benchmark，却损害并发计算；固定环境变量也可能覆盖未来版本更合适的默认选择。实验要保留默认路径和升级后的复测。[官方说明](https://developer.nvidia.com/blog/understanding-nccl-tuning-to-accelerate-gpu-to-gpu-communication/)

2026-08-11 发布的 NCCL 2.31.2-1 已有逐 collective 配置接口；其固定提交的 tuner v6 头文件增加可选 `getChunkSize` 回调，并规定结果受缓冲上限约束。这与 2025 说明中的 2.27 接口范围不同。头文件还允许保留默认选择，并对失败回调回退；本轮只核接口声明，没有审全部调度实现，也不宣称该版本已有 AutoCCL 的在线搜索算法。[版本公告](https://github.com/NVIDIA/nccl/releases/tag/v2.31.2-1)、[固定接口](https://github.com/NVIDIA/nccl/blob/7b83616df3ae082a1f32bb74c27458bfe8153a13/src/include/plugin/tuner/tuner_v6.h)

第 6.4.5 再问能否减少通信占用的 SM。2025 年 NCCL 2.28 公告介绍设备端通信 API、对称窗口和 Copy Engine 搬移；设备 API、SM 执行的融合、CE 卸载是不同执行方式，不能因都与通信有关就混用名称。[2.28 官方公告](https://developer.nvidia.com/blog/fusing-communication-and-compute-with-new-device-api-and-copy-engine-collectives-in-nvidia-nccl-2-28/)

2.31.2 固定版本文档明确：NVLink 的零 CTA 路径自 2.28 支持；跨网络路径自 2.30.6 支持，使用节点内 CE 和节点间 CPU proxy。要求合适驱动、对称注册窗口和 ZERO CTA policy。文档所列网络操作是 AllGather／AlltoAll，单 NVL／MNNVL 范围还包括 Gather／Scatter，不能将 AllReduce 普遍描述成 CE 完成。减少 SM 使用后，显存带宽、互联、CE、CPU 和注册开销仍要入账。[固定版本条件](https://github.com/NVIDIA/nccl/blob/7b83616df3ae082a1f32bb74c27458bfe8153a13/docs/userguide/source/usage/bufferreg.rst)

vLLM／SGLang 的归约融合沿[已核分派与通信组](collective-paths-and-diagnosis.md)安排；这里介绍的是它们可能使用的底层库能力，不能从安装了新版 NCCL 就推断框架已选择 CE 或研究 tuner。升级后先查看实际分支、窗口与拓扑，再解释测量。

## 提纲采用

只深化第 6.4.4／6.4.5，扩展实验 6-5 和图 6-5：先算模型片段，再比较独占、并发和整步结果，最后判断调优／卸载是否值得。第 5 章的 Agent profiling 与第 11 章的训练时序通过交叉引用连接；I12 增加同一配置选择的追问，不新增题号或面试来源。NSDI 2026 本轮另筛读前 40 篇摘要，SYMI、DroidSpeak、Checkmate、HydraServe、PIPEMORPH 等仍是比较候选，尚未读正文或采用。
