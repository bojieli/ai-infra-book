# Blackwell BF16 累加类型独立裁决

结论：**可用官方 tcgen05 明确类型组合表与对应SKU的BF16峰值作联合证据，保留BF16/FP32分母。无需因PTX Table45同时列F16/F32而降级这10条记录。** 不能把这条结论扩展到其他格式，不能把FP32类型接口当作每个内部部分和严格按IEEE单精度舍入的证明。

本次只审此问题，未改共享目录，也未应用旧102条降级方案。

## 1. PTX Table45到底说明什么

已锁PTX9.3 §9.7.17.4.2 Table45给.kind::f16的描述符：dtype可以编码F16/F32，A/B可以编码F16/BF16。这个表在说明字段编码，而非逐输入格式穷举所有合法交叉组合。

§9.7.17.10说明D=A*B+D；§9.7.17.10.8.1 `tcgen05.mma` 的d-tmem描述明确D兼作destination与accumulation matrix。因此D的F16/F32并非只指最终epilogue输出转换。**但由此不能反向断言BF16有F16累加选项**；这一交叉组合需另查完整类型约束。

旧mma BF16只能F32的语义本身也不足以证明新tcgen05必须相同。此前两条极端推断——“只是输出格式”与“BF16肯定存在两种累加”——都不成立。

## 2. 新找到的直接官方类型组合证据

[NVIDIA CUTLASS 固定提交147295a3d4b75f3aeff247c25b8927cea9a7006a的tcgen05 mma.py](https://github.com/NVIDIA/cutlass/blob/147295a3d4b75f3aeff247c25b8927cea9a7006a/python/CuTeDSL/cutlass/cute/nvgpu/tcgen05/mma.py)明确分别给出：

| 官方类 | 源码起始行 | BF16输入所列Acc类型 | F16输入所列Acc类型 |
|---|---:|---|---|
| MmaF16BF16Op | 1417 | F32 | F16、F32 |
| MmaF16BF16SparseOp | 1558 | F32 | F16、F32 |

两表均明确适用sm100、sm103及sm110；分别对应dense和sparse tcgen05，直接消除当前Blackwell BF16问题中的组合歧义。原件不是搜索摘要，已下载并按完整commit重新获取，字节与初始main快照一致；来源与SHA/长度见 `source.json`。`verification.json`通过AST读取两类docstring核验组合和架构，不声称运行GPU指令。

Python `_verify()`只分别检查输入类型集合和累加类型集合，没有在该层拒绝BF16/F16，不能把这个宽松前端检查解释成硬件支持证明；其明确supported-combinations表是本次采用的规范性声明。原C++包装器和functionality文档只传descriptor或说明kind，不能单独排除组合歧义，因此新的明确组合表有实际增量。

## 3. 联合证据准入边界

Blackwell官方技术简报及具体HGX/GB产品规格确定对应SKU/系统范围、BF16数值与dense/sparse条件；本次明确的tcgen05组合表确定该格式的FP32累加接口。两者可以组成“格式峰值+适用架构唯一公开累加类型”的证据链，不必要求每份产品广告表再重复写出累加位宽，也不必把所有产品峰值按SM数量和时钟重建一遍。

这是一项有来源的联合推断：具体数值仍必须来自原SKU，不能由指令支持表或跨SKU倍率生成。需保留峰值的舍入、功率/时钟条件及系统聚合范围；有效吞吐和每个内部中间值的精确舍入行为仍不在此声明中。也不把SM100/103的tcgen05证据机械移到RTX SM120路径。

给主线的可执行建议：将 `source.json` 原件转为公共来源锁，并在原10条Blackwell BF16记录的supporting_evidence增加对应dense/sparse类定位；保留其原FP32接口标签和SKU峰值，不运行旧降级补丁。hardware_audit已收到独立证据并同意撤回这10条降级提案。
