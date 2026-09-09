# C20 training_history 独立审查

审查日期：2026-09-09。对照原3.2.4、实验3-9/3-10、case-studies/scaling-history.md与configs/training-history.json/lock。只写本独立目录；未修改CLI交付原件或共享src/config。

结论：13行模型的既有数值代理、主要GPU小时和阶段分离正确；有三项需要在集成前补清的语义/覆盖问题。原交付12测试通过不代表这些原要求已覆盖。本目录修正提案另有3项测试通过。

## 已核正确的内容

- Llama1 v1表2/15：6.7B×1T与65.2B×1.4T；82,432与1,022,362 GPUh。65B按2048卡换算20.800008138天，与论文约21天相容；不得用21天倒算值覆盖表15。
- Llama2原报告2T；不能用后续报告回顾1.8T替换。7B/70B小时为184,320/1,720,320。
- Llama3.1模型卡1.46M、7M、30.84M GPUh；小模型15T是显式近似，family15T+不等于精确15T。405B论文15.6T与3.8×10^25 FLOPs独立保留。代理3.7908×10^25/报告3.8×10^25=9477/9500只比较规模，不是MFU。
- Qwen2.5 family18T、Qwen3 family约36T应用到显式7B/8B名义代理，不能宣称配置精确训练量或每个小模型的独立训练日志。未披露预训练GPU小时保持null。
- Qwen3表21的17920/1800 GPUh是后训练对照分支，不可相加或填作预训练总量；代码正确保留alternatives。
- DeepSeekV3预训练2.664M +上下文119K +后训练5K =2.788M GPUh，14.8T只与预训练相配。2048卡54.19921875天是恒定投入假设；既往研究/消融排除。
- V4 Flash32T、13B激活，Pro33T、49B激活与所锁报告对应；6ND只作代理。不能从部署规模推训练GPU小时。

## 必须补清的三项

### 1. MoE总参数与激活参数不能只剩后者

原实验3-9明确要求单列总参数与激活参数，用来区分容量和计算。现交付只有active_parameter_proxy，遗漏V3总671B、V4Flash总284B、V4Pro总1.6T这三个已在锁定原报告摘要/正文披露的字段。catalog-patches.json提供同revision、带field_source_ids的字段；修正模块以parameter_context单列，6ND仍使用原active proxy，不将总参数塞入6ND，也不把取整报告标签叫checkpoint精确参数。Qwen3.5发布HTML本轮未找到397/17参数数字；没有借此伪造字段或把Qwen3的36T继承过去。

### 2. GPU小时与最大卡数的阶段范围必须条件化

405B的30.84M来自官方模型卡“模型训练总GPU时间”，16384来自论文pretraining最大作业卡数/表4。两者相同scope不能只由同模型名证明。原模块虽然有通用assumption，但直接输出calendar_lower_bound_days_exact容易被下游当作无条件事实。

修正提案保留原计算值78.43017578125天，放入conditional_calendar_lower_bound_days_exact；只有明确gpu_hours_count_scope_match=true时才填calendar_lower_bound_days_exact。当前catalog保留该字段null，并按字段区分模型卡与论文来源。measured_calendar_days仍null。reported_maximum与reported_configuration不能混用，也不能换成整集群24K卡。

这不是说数学下界错误：GPUh/最大卡数在相同作业范围下成立；此处缺的是范围同一性的证据，而非除法。

### 3. MFU未知与官方阶段观测须分开

原mfu=null适用于未计算全程MFU，不能让报告显示成“官方从未披露”。Llama3表4明确三个配置：8192卡、8192序列、43%；16384卡、8192序列、41%；16384卡、131072序列、38%。报告同时给430/400/380 TFLOPs/GPU，都是该表阶段观测，不能取一个值覆盖30.84M小时。

catalog-patches.json追加独立reported_performance，保留TP/CP/PP/DP和sequence_length；不放进GPUh的parts/alternatives，避免误把性能百分比相加。代码的mfu仍null，reported_performance另列。三个观察的TP×CP×PP×DP均匹配GPU数量。

## 测试与实现问题

原test_training_history.py使用绝对路径`/Users/boj/book/ai-infra-book/calculations`，不能原样迁入共享tests。集成时改从infra_calc.paths导入PROJECT、从infra_calc.topics.training_history导入函数。原最大卡数测试应改断言conditional_calendar_lower_bound字段等于换算值，无scope证据时calendar_lower_bound为null。

本目录training_history.py是独立修正候选：保留API/既有计算，增加parameter_context、reported_performance、每字段来源校验和条件日历下界。不写共享文件；catalog-patches.json需人工审阅后合入共享catalog。test_independent_review.py在本目录临时fixture合并这些字段，用既有锁的实际官方原件验证，3项通过。原交付12项也已独立重跑通过。所有既有16条归档由代码核验SHA/bytes；无联网新取证或新官方版本替换。

## 最小集成步骤

1. 合入catalog补丁与本目录模块候选；模型参数/性能字段都来自已有锁，不需新增网络来源。官方历史值与caller情景不合并。
2. 搬原12项测试，修正导入/PROJECT路径及日历语义断言；增加本目录3项同义测试。不要把临时fixture的绝对锁路径写入共享catalog。
3. CLI用`training-history --inputs JSON --format json|md`，输入仅comparisons/duration_scenarios/lifecycle；不要向普通CLI开放任意project参数。默认无成本推断。`scenario`按现API可重放。
4. Markdown应显示每行parameter_context、proxy_kind、6ND/DN、GPUh硬件/来源、日期条件、阶段parts或alternatives、reported_performance及caller成本scope；通用summary只给13模型/16源数量是不够的。
5. reproduce读取独立场景组，至少默认历史表、7B增长、未知Qwen、已知/未知GPU小时条件区间、显式服务成本五类；manifest加入training-history.lock.json实际引用的16归档文件。生成结果索引与正文3.2.4链接。
6. 正文完整例采用Llama1 65B恒定2048卡的20.80天；未知对照采用Qwen3。405B只能作为“额外同scope条件下78.43天下界”，旁列表4阶段MFU。DeepSeek总/激活分列；成本仅caller声明范围，没有质量等价就不做效率排名。

## 验收边界

完成上述修正并接通CLI/reproduce/报告/正文后，可验收C20公开字段复算和条件预算；不要求补出官方未披露训练日志、商业价格或全程MFU。原图3-8/3-9还应按全书图形流程单独验证，不能把此纯计算模块称为图已完成。不同硬件小时不直接相加作算力排名，6ND不替代逐算子训练账；原3.2.4的质量/数据差异、MoE容量和历史阶段区别应在展示中可见。
