# 成本下降调研的章节落点

本轮只在既有小节中插入 18 条简短占位，覆盖 9 章；没有扩写正文，没有新增小节、实验或配图编号。完整内容保存在[研究报告](report.md)，占位指向具体报告段落。

| 占位 | 大纲位置 | 报告位置 | 放在此处的理由 |
|---|---|---|---|
| TC-01 | [1.1.3](../../outlines/01-初识 AI Infra.md) | [findings](report.md#findings) | 章首全景之后提出问题，不展开机制或把千倍写成定论。 |
| TC-02 | [2.6.1](../../outlines/02-模型架构.md) | [density](report.md#density) | 参数与设备容量之后，解释为何同等能力所需规模会变化。 |
| TC-03 | [2.5.3](../../outlines/02-模型架构.md) | [architecture](report.md#architecture) | 将模型架构变化接到容量、访问和通信，不新增架构清单。 |
| TC-04 | [2.6.3](../../outlines/02-模型架构.md) | [speculation](report.md#speculation) | 本章只定位模型机制，执行收支留给推理章。 |
| TC-05 | [3.1.2](../../outlines/03-推理与训练负载.md) | [economics](report.md#economics) | 放在 reasoning 负载内，避免只用可见输出估算。 |
| TC-06 | [3.2.3](../../outlines/03-推理与训练负载.md) | [density](report.md#density) | 承接已有 scaling law 与生命周期讨论。 |
| TC-07 | [4.3.3](../../outlines/04-加速器架构.md) | [hardware](report.md#hardware) | 按资源约束解释代际进步，不单列芯片年表。 |
| TC-08 | [4.2.5](../../outlines/04-加速器架构.md) | [quantization](report.md#quantization) | 让低精度峰值与可用推理收益建立联系。 |
| TC-09 | [5.2.2](../../outlines/05-算子与运行时.md) | [quantization](report.md#quantization) | 沿现有 FlashAttention 推导补历史背景。 |
| TC-10 | [5.4.3](../../outlines/05-算子与运行时.md) | [runtime](report.md#runtime) | 作为主机开销暴露的具体例子，不把全部收益归给 GIL。 |
| TC-11 | [9.2.1](../../outlines/08-单实例推理.md) | [runtime](report.md#runtime) | 与已有连续批处理互相回指，不重复讲分页机制。 |
| TC-12 | [9.3.4](../../outlines/08-单实例推理.md) | [speculation](report.md#speculation) | 用已有推测解码收支位置承接模型章。 |
| TC-13 | [9.5.1](../../outlines/08-单实例推理.md) | [measurement](report.md#measurement) | 作为引擎与设备比较的统一口径。 |
| TC-14 | [10.2.3](../../outlines/09-分布式推理.md) | [serving](report.md#serving) | 沿现有收益边界计算解释跨层优化。 |
| TC-15 | [10.5.3](../../outlines/09-分布式推理.md) | [serving](report.md#serving) | 结合已有 PD／AF／内存池组合讨论。 |
| TC-16 | [12.3.5](../../outlines/11-资源调度与运行环境.md) | [economics](report.md#economics) | 将服务选择与底层成本分开核算。 |
| TC-17 | [12.5.2](../../outlines/11-资源调度与运行环境.md) | [economics](report.md#economics) | 沿现有任务费用汇总，回收章首的成本问题。 |
| TC-18 | [13.2.2](../../outlines/13-架构协同设计.md) | [attribution](report.md#attribution) | 用完整系统解释各项倍率为何不能任意相乘。 |

第 1 章 1.1.3 是引子；第 13 章 13.2.2 回收全线。模型、芯片、运行时与服务各自只承接适合自身的问题。第 6、7 章已有并行和通信推算，第 8 章已有端侧案例，第 11 章已有训练系统，本轮不为覆盖章号而添加重复占位。

扩写时按报告与原件逐项补齐；若价格或系统版本更新，另存新快照并保留旧值。报告中的教学算例不能改标为本书实测。
