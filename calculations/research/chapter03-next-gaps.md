# 第 3 章：下一批三个明确计算缺口

本次只核第3章正文及相应扩写的原定量要求，并检查直接相关实现/原记录；不是全书关键词清单。已有的FIFO/p95/准入、实际Agent主链、教学音频、训练矩阵、RL有效样本供给和合成Scaling Law不重复列为全缺失。近期第2章四模型累计账可复用，但不自动完成本章质量、训练或实际供给要求。

## 1. 实验3-8：用真实公开训练点替换“仅合成点”的有限证据缺口

原句：`outlines/03-推理与训练负载.md:157`附近实验3-8：“用论文公开实验点拟合 N、D 与损失，留出点验证外推；比较 Kaplan／Chinchilla 假设，再加入调用次数得到训练与推理费用交叉曲线。可选小模型实验只检验局部范围。”对应扩写同名实验保留原要求。

现有证据：`src/infra_calc/topics/scaling_law.py:calculate`、`scenarios/scaling-law-teaching.json`、`results/scaling-law-teaching.json`；9个合成训练点和3个留出点，有限指数网格、条件最小二乘、生命周期与敏感性已实现。模块明确“historical exponent illustration, not paper replication”，非合成记录的controls真实性仍是调用方声明。不能把现有拟合测试通过当作论文训练点复现。

具体缺口：未接一组来源明确、训练条件可比、N/D/验证loss语义一致的真实公开点；当前Kaplan/Chinchilla对照只共用教学锚点。相同预测loss到实际任务质量也尚无校准。

下一计算契约：新增独立数据适配，不先重写拟合器。每行 `{record_id, source_id, locator, N_definition, N, D_definition, D, loss_definition, loss, control_id, split, extraction_method, uncertainty}`。先选择单论文/单数据tokenizer/同评估条件的有限组；缺关键字段不得混入可拟合集。预先指定留出规则，留出不参与指数选择。产出原始点、预测/残差、拟合范围外标记、同控制条件的N/D预算及调用量交叉曲线。若只能从官方图提取，保存图页、坐标变换和读数误差，不能将读图近似写成精确实验日志。

验收：来源行逐项复核；拟合集与留出集ID不相交；能逐点重建已声明单位；同loss生命周期曲线保留费用假设。下游质量没有数据时维持unknown，不能通过扩大任务范围或用合成点替代来勾完整3-8。此项优先，因为是正文标注的核心实验，现有算法基本可复用。

## 2. 实验3-6：训练矩阵之外的反向/更新，以及原题V4分支

原句：`outlines/03-推理与训练负载.md:121`附近实验3-6：“对固定 dense 和 V4-Flash 配置，从前向、反向与状态计数开始，比较预训练、长上下文中期训练与 SFT；逐项指出 6ND 漏掉的工作，并给出影响预算的范围。”

现有证据：`topics/training_matrix.py:calculate`通过Qwen Dense/MoE验证器，从双线性矩阵计算前向与两个梯度；`training-qwen3-8b-t8192`、`mask-half`、`compact-half`及235B专家矩阵结果存在。实现遍历时 `if not op.matrix_flops: continue`，因此非矩阵forward/backward不是已计零工作。该函数实际不支持V4模型；`training_state.py`、`gradient_cast.py`和checkpoint专题提供部分状态/转换，不能替代本训练路径的梯度运算。

具体缺口：RMSNorm、SiLU/SwiGLU、softmax及loss的反向、明确优化器更新、保存/重计算激活的生命周期尚未连接到训练矩阵总账；V4参考推理前向不是公开训练实现，不能直接把推理FLOPs乘3冒称全部V4训练（router/index选择、mHC和QAT尤其需要说明）。

下一计算契约分两级但保留完整原题：先固定官方Qwen8层，输入 `{B,T,supervised_token_mask,head_strategy,checkpoint_policy,weight/grad/master/moment_dtypes,optimizer_variant}`，逐元素/归约/特殊函数展开Dense可微路径和AdamW实际声明式，训练标签mask不能凭空跳过主干计算。用独立小张量自动微分核梯度与保存集合，算子与编译融合/allocator分开。随后V4另列已证可微图与未知训练策略；需明确所取训练/数学参考及路由选择的梯度规则，不能悄悄假定选中专家固定、忽略mHC后宣称完成原题。

验收：同一形状的矩阵总数保持现有账不重复相加；逐算子反向有公式及数值梯度对照；激活存活/重计算只在真实执行位置计入，AdamW状态更新按声明dtype。阶段差异由T、数据/标签、执行head策略等输入体现。完成Dense新增子账后仍保留V4分支未完成，避免缩小3-6范围。

## 3. 实验3-3：成功任务成本的共同质量门槛与失败预算

原句：`outlines/03-推理与训练负载.md:53`：“用可验证题集或固定公开记录，比较串行、并行与按难度分配；计入验证、状态和最终输出，在相同质量要求下求代价。”

现有证据：`experiments/ch03/03-03/README.md`及`wide-budget/`、`no-thinking/`保存固定Qwen8、三策略、每批44候选的真实记录和原协议。1024/4096上限均未给出完成思考后的合法答案；关闭thinking虽自然结束，严格JSON仍全部失败。后验提取的1/8、2/8、1/8不能替换事前评分。主记录已正确保留成功成本null；不能为计算一个比率而把null变0。`agent_trace.py`是两条完整Agent轨迹，`rl_cycle.py`是有效样本教学预算，也不能冒充本题三策略同质量比较。

具体缺口：没有在同一事前接口和质量要求下达到可用质量的三策略记录，故无法得出成功任务成本排序；候选生成、验证、选择和共享前缀/分支状态尚未形成同一成本账。原no-thinking运行还存在其它服务启动，墙钟不满足独占解释。

下一计算契约：先实现严格原记录导入 `{task_id, strategy, attempt_id, parent/shared_prefix_id, input_ids_count, cached_tokens, output_ids_count, reasoning/final partition, selected_candidate_id, protocol_pass, task_correct, verification_interval, model_interval, resource_condition}`。任务成功以“事前规则选择后的合规正确结果”为准，不把任一候选正确当任务成功。输出每策略全部失败/成功消耗、选择/验证成本、token与已知时间、质量门槛是否满足；零成功返回unknown的每成功结果成本并说明分母为0。历史记录不能自动增加真实GPU核时或KV驻留；若用逻辑保留策略，须独立标为教学状态预算。

验收：原132个候选（三批44）不漏失败/截断，严格主评分与后验诊断分开；费用率/状态生命周期缺失不填零。只在有同协议且达到相同质量阈值的真实新记录或固定公开记录时计算可比较成本。下一次实测先固定可执行接口与任务协议，不能用事后放宽评分“修复”既有失败，也不能仅增大token上限就声称质量问题已解。

## 不应重复或扩大

实验3-2已有同均值、关联/到达、FIFO准入和p95逻辑账及真实回放，不应重新做一个平均值算例作为主要交付。实验3-4已有完整主链关键路径替换，真正剩余是分支/真实缓存生命周期；3-5有教学播放时序，真实取消/flush仍缺，本次未把这两项伪称完成，也未把它们加入前三以启动所有任务。原章节图3-7仍需随真实Scaling点产物生成；源码数据完成与图完成分别验收。

## 本次读取快照

| 文件 | SHA256 |
|---|---|
| outlines/03-推理与训练负载.md | 84e8436311451b4ebbea735e9442000b9f9951465fa0fdb67450656c50b29bd6 |
| outlines/extensions/03-推理与训练负载.md | 0fef201016d0714c2860060d3e48b5657198eff2605295548255cd696fe2502b |
| calculations/src/infra_calc/topics/scaling_law.py | 918feb4b3ac87a9cb94b185aabe3d4922217614512283b4ffaf44410590ba47b |
| calculations/src/infra_calc/topics/training_matrix.py | d48eee8e03c8a7d886242bb61058dfd40f361ca86859b4ef406997fac4b53437 |
| experiments/ch03/03-03/README.md | f62282d94b2d9a4cea86aea92aef07caba63c5efaabf2dee70f1fb5fe1bff018 |
| experiments/ch03/03-03/wide-budget/README.md | 451b9cfb2ed0b446d91fbca4c252a49962ce22de04911e075b67be874138f4bc |
| experiments/ch03/03-03/no-thinking/README.md | a84d38bcbd779b288ed10adab1b0c23c6d720c294c85ef56b7a2bddebf03fab3 |
