# 950 PR／DT 完整计算能力档与未闭合产品映射

2026-09-09。本轮把计算能力列与真实可购买板卡区分，交付 [hardware-950-profiles-patch.json](hardware-950-profiles-patch.json)，构建及校验入口为 `python3 calculations/research/build_950_profiles.py`。未修改共享catalog或来源锁。

采用已经锁定、重新校验SHA的[官方950白皮书](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)表3-1物理13–14页，逐表头视觉复核。5个新增记录覆盖PR32/28 Cube、DT36/32/28 Cube，分别对应64/56及72/64/56 Vector。每档完整23条峰值，合计115条：Cube8条、Vector7条、相加宣传值8条。补齐此前max-spec没有逐列列全的Vector INT16/INT32/INT64，整数单位保持TOPS。

## 为什么单独记录为能力档

新记录采用现有 `single_device` 范围，但 `record_kind=chip_capability_profile`，名称、形态和配置状态均明确它只代表单芯片计算能力表的一列。它不是Atlas350实卡，也不是某个已下单950DT板卡。现有max-spec是系列上限的记录；新能力档则不把内存上限拼到计算核档，因此两者含义不同。

新档的主memory容量和带宽都留null；`family_memory_options`单列PR128/112GB及1.6/1.4TB/s、DT144/96GB及4TB/s，`profile_assignment=null`且`cross_product_validated=false`。尤其DT三个核档对两个容量选项不能按斜线位置一一匹配，也不能生成六种可交付SKU。只有实际板卡规格明确配对，才应进入普通板卡记录。

所有新峰值累加、稀疏仍unspecified，明确Cube/Vector也不能补出dense；A3新白皮书的dense证据不跨代移植。总算力保留官方独立取整，DT36的BF16 Cube486加Vector60得546，而宣传总值为547，不能覆盖原表。未声明执行指令/模式的字段保持未知，不以理论关系反推功耗、时钟或板卡bin。

## 官方板卡与950DT补查结果

本轮进一步按官方域限定查询Atlas350技术白皮书、950DT板卡/PCIe/功耗、Atlas950技术规格；没有取得比已归档Atlas350产品技术表更明确的板卡白皮书正文。检索未命中不是“官方不存在”的证明，所以此项保持**尚未找到可核公开板卡白皮书正文**。

当前已核实际板卡仍是[Atlas350](https://www.hiascend.com/hardware/accelerator-card)112GB/1.4TB/s/≤600W，且其宣传总数与PR28能力列吻合。此数值吻合不足以证明板卡的订货bin就是28 Cube，不将其写进板卡硬件事实。

[华为计算官方入口](https://e.huawei.com/cn/products/computing)当前出现2026展会展示Atlas950真机的新闻入口；展示新闻不提供950DT独立板卡料号、每板芯片数、绑定核数/内存/功耗表，也不是客户交付验证，故没有生成实际950DT板卡记录。已有950芯片白皮书与2025路线图是能力/规划证据，不能代替这个缺口。

验证已完成：5条新device全部通过当前validate_device，115个峰值单位分类无重复，5条指定FP16/FP32累加/Cube/dense选择均按预期拒绝，PDF与公共锁SHA一致。没有新增公共来源条目，补丁复用 `ascend-950-official`；`verified_source`给出本轮核验的完整锁快照供审阅。
