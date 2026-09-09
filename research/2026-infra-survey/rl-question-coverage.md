# RL Infra 问题到章节的逐项检查

2026-09-09。按已归档 Xiuyu Li 问题汇总的 Infrastructure 顺序检查 16 个题位；以下只概括主题，不复制原题。原文、日期和镜像一致性见[第三批寻源记录](../../references/interviews/2026-09-08/third-pass/README.md)。它是作者整理的题目，没有逐题公司归属，不能称为公司认证题库。本表不新增本书 I01–I21 题号。

“已有入口”表示章节及案例已经处理相应问题，不等于全部答案或实验已验收。“待补”限定所缺证据，不把所有相关框架功能都扩成新任务。

| 原题位／主题 | 回答入口 | 本轮判断 |
| --- | --- | --- |
| 1 模型副本与容量 | 10.1、10.5；[阶段容量](../../case-studies/weight-handoff.md) | 已有入口。按角色、更新方式和共享关系计量；不能给所有 GRPO 配方一个固定副本数。 |
| 2 KV 交接与多卡通信 | 6、7、9.2、9.5；[MoE 同一布局](parallel-moe-ownership/NOTES.md) | 已有入口。逐卡状态、发送方向与恢复边界必须来自同一方案。 |
| 3 精度取舍 | 4.2、8.4、10.1 | 已有入口。存储、计算和累加格式分开，不能只按位宽推荐训练精度。 |
| 4 rollout 长尾 | 10.5；[选择与迁移](../../case-studies/rollout-tail-and-sampling.md) | 已有入口。时间、槽位占用、保留样本分布分别比较。 |
| 5 连续批处理的 RL 影响 | 8.1→10.5；[数值与概率身份](../../case-studies/rl-state-and-reproducibility.md) | 已有入口。不能用固定 seed 代替跨形状、跨引擎验证。 |
| 6 利用率与 KV 使用 | 8.2、10.6、13.1；[有效进展](../../case-studies/kernel-and-fleet-efficiency.md) | 已有入口。池预留、有效页、前缀命中、设备活动和学习进展不是一个比值。 |
| 7 多机反向 | 10.2–10.3 | 有基础入口；本轮没有完整核对一个 RL 配方的全部训练通信与梯度归约。 |
| 8 异步训练的同步限制 | 10.5、11.3；[阶段调度](../../case-studies/rl-scheduling-and-recovery.md) | 已有入口。比较阶段能力和必要依赖，不增加异步框架名称清单。 |
| 9 旧策略 KV | 10.5；[状态版本](../../case-studies/rl-state-and-reproducibility.md) | 已有入口。保留轨迹、重建 KV、保留旧策略三者分别计量。 |
| 10 EP 吞吐 | 6.3→9.4；[专家工作](../../case-studies/moe-and-startup.md) | 已有入口。活跃专家并集、热点、padding 与复制一起计量。 |
| 11 长上下文的并行与重叠 | 10.2–10.3；[长度与通信](../../case-studies/training-compute.md) | 已有入口。Megatron SP、CP 与 Ulysses 的词义按实现区分。 |
| 12 确定性 | 5.1→8.1→10.5；[数值案例](../../case-studies/rl-state-and-reproducibility.md) | 已有入口。atomic add 不是唯一来源，确定性条件不能外推全部版本。 |
| 13 AReaL 与 slime 的瓶颈判断 | 10.5；[slime 补读](../../references/framework-history/2026-09-09/slime-dataflow/NOTES.md) | 待补同任务对照。已读普通同步入口，不足以代表 slime 的所有异步模式。 |
| 14 样本滞后 | 10.5；[状态与准入](../../case-studies/rl-state-and-reproducibility.md) | 原理已有入口；没有足够依据给统一“典型值”。实际阈值应绑定算法、版本和质量目标。 |
| 15 slime 数据流与 loss | 10.2、10.5；[固定源码](../../references/framework-history/2026-09-09/slime-dataflow/NOTES.md) | 部分闭合。已读同步入口、局部 reducer 和训练交接；外部 Megatron 缩放及数据分派尚未完整核对。 |
| 16 训练框架选择 | 10.1、10.5 的任务与后端选择 | 待补简短选型依据。TRL、Unsloth 等不能仅因都支持后训练就当作相同规模和角色的替代品；本次不提供未验证排名。 |

## 下一步的有限范围

先补第 15 项的一条固定 Megatron 依赖路径，再用相同任务比较第 13 项的阶段同步与状态成本；第 16 项只需核对角色、训练范围和已支持的执行后端，放入既有扩写资料。无需为此扩展三章或新增一套框架横向评测。

本表把缺口具体化，不证明本书已经覆盖所有 2026 年真实面试。算法部分的完整推导、未公开面试原题、特定公司的内部系统都不能靠题目名称补造。会议筛读与原始面试寻源仍按原目标继续。
