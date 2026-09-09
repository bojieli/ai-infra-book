# C52 重配置独立审查

2026-09-09，对照原9.6、PLAN C52和交付reconfiguration.py/11测试。原11测试重跑通过；独立修正候选加5项新测试共16通过。仅本目录修改，原交付与共享src/config未动。

## 所有权、形状与状态主体核验

权重所有权主体正确。普通矩阵按固定轴作区间：Q/K/V和gate/up沿输出，O/down沿输入，embedding/head按词表；norm/router复制。每个MoE expert只有指定EP rank的TP组持有；余数专家按连续区间分配，不丢失或平均分成分数专家。TP整除Q头、FFN与词表；KV按完整head归属，TP超过KV头时复制。Qwen adapter另外验证每层结构，未将V4等不同实现套入。

新增独立闭式验证覆盖Qwen30的(TP,EP)=(2,4),(8,3),(16,2)，既有不均匀EP也有TP>KV。设H/V/L/Q/K/D/E/F为官方配置，总物理权重参数：

`2 EP V H + EP TP H + L[EP H(2QD + 2 max(K,TP)D) + EP TP(2H+2D+EH) + 3EHF]`。

全部乘2得BF16bytes。总KV：`EP × 2 × L × batch × history × max(K,TP) × D × 2`。这是已声明同一请求KV在EP组复制，不是独立请求batch。结果与区间枚举一致。

transfer_plan切目标区间时优先同卡，再从一个有效源确定性单播；源复制不重复收费，目的复制仍必须付每份交付。source名字排序是教学发送策略，非最优流量调度。replay不搬旧KV，目标重建KV容量仍保留；词表/请求/token/position/version一致性是调用者断言，不是模块实际校验。

## 实际修正

1. **小辅助状态错误拒绝。** auxiliary_state_bytes=1、设备多于1时，复用checkpoint分片助手因空分片抛错。字节快照允许其他卡0bytes；候选改成商/余数连续分配，空区间无传输，保持总量1。
2. **形状类型错误。** 原PP/DP以`!=1`判断，True和1.0被接受。候选先严格integer再要求1，拒绝bool/float；仍不扩展PP/DP范围。
3. **资源下界不等于可达完成时间。** `max(total/fabric, max_sender/rate, max_receiver/rate)`只是必要下界，缺路由/调度/依赖保证。原直接加runtime并命名declared_serial_switch_seconds容易暗示可达。候选保留conditional_serial_switch_lower_bound_exact_seconds；新增可选scenario.network_transfer_seconds，必须不小于每个已知下界，只有提供该声明服务时间且runtime齐全时才填declared_serial_switch_seconds。零网络可用0，但仍需本地复制/其他runtime输入。两种值均非实测。
4. **同卡“local”不是零拷贝保留。** 原明确预算old+fully materialized target，故同卡数据也读旧写新；双份容量不是算错，而是保守复制方案。候选增加local_materialization_read_write_bytes=2×local_bytes，并要求runtime_seconds.local_materialization。完整不变buffer的alias/就地保留未实现，不能把local_bytes显示成“0成本复用”；部分切片甚至可能需要pack。默认不擅自删除旧副本。
5. **摊销与币种边界。** overhead0且负saving在0步仍打平，候选将break_even_steps改0，正步仍不可能更优；增加remaining_steps和strictly_better_within_horizon。非空成本账必须声明currency/unit，不能完整算出无币种总额。另输出三态all_declared_capacities_fit，任何卡false则false、容量未知则null。摊销saving/overhead来自调用者独立输入，不自动等于迁移时间，不得跳过容量/SLO校验。

## 可集成API与迁移影响

候选仍是`calculate(scenario: dict)`，保留深拷贝scenario、旧字段和BF16范围。CLI应调用`calculate(json.loads(inputs.read_text()))`；不能对scenario用`**`展开。重放方式`calculate(result['scenario'])`。

新增输入：`network_transfer_seconds`（精确数字/有理数字符串、可缺省）、`runtime_seconds.local_materialization`（未知留null，显式0表示本例排除）、`amortization.remaining_steps`（非负整数、可缺省）。原带宽仍仅用于下界。

新增输出：conditional_serial_switch_lower_bound_exact_seconds、supplied_network_transfer_seconds_exact、local_materialization_read_write_bytes、all_declared_capacities_fit和摊销的有限剩余步数判断。原declared_serial_switch_seconds_exact现在在没有声明网络服务时间时为null；这是纠正下界含义，不是丢失原有量。场景示例需补local_materialization:null，避免旧“全runtime齐全”暗示完整切换预算。

测试迁移：原test的绝对sys.path已改为目录相对路径；共享tests需直接import infra_calc.topics.reconfiguration。原replay测试改核lower_bound>=5并确认未提供network_transfer_seconds时实际声明switch为null。新增test_review_edges.py检查五个独立缺口及闭式所有权公式。

## 最小集成步骤

- 模块与测试合入后，将原场景数组包装到book.json的reconfiguration组，CLI提供`reconfiguration --inputs`，按上面单参数API调用。
- 加专用报告分支。顶层placement_cards是迁移容量行，不含通用dense-placement的replica/stage/layer_ids；直接落入现通用Markdown的placement_cards表会KeyError。专用分支需在该表之前返回，展示source/target、逐卡old/new/extra、local/network分项、三种下界、runtime未知项和摊销条件。
- reproduce保存JSON/Markdown并加入场景索引。模型/config来源继续使用现provenance；本模块没有独立未锁的设备峰值或实测来源。
- 正文9.6给权重/状态迁移子账链接，明确同卡复制方案、同请求跨EP复制和replay边界。不能将候选结果写成ArcticInference/SP×TP、vLLM或真实恢复测量。

## 原C52验收边界

当前可验收：声明TP×EP权重/KV/辅助快照的确定性单播迁移账、显式双缓冲容量、条件资源下界及可独立输入的有限寿命摊销/全分类费用账。对未披露运行时保持null是正确结果。

原9.6/C52还包含分流与恢复后的完整部署、实际请求分布、SLO有效产出、失败尝试和积压消退。这些在当前模块只接受调用者类别费用或时间，没有执行恢复DAG、验证可恢复token日志、追踪动态请求所有权，也未跑原文ArcticInference/vLLM输出一致性、PD/AF/共享KV组合。尤其EP中的同一请求完全复制是假设，不能替代真实服务rank请求布局。因此不能凭此模块单独勾选原C52完整完成；应先接为C52迁移子账，再由运行记录或明确请求/恢复阶段模型闭合完整部署。
