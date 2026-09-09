# Dense local-shard quantized placement independent review

结论：冻结calculate数学通过，可按声明的存储/条件并发范围合入，无阻塞发现。源码快照与SHA见results.json；shared及作者目录未改。

## 三模型真实维度

独立使用官方配置常数：Qwen8 H4096/F12288/L36/Q32/KV8/D128/V151936；Qwen32 H5120/F25600/L64/Q64/KV8/D128/V151936；公开DeepSeek Distill Llama70 H8192/F28672/L80/Q64/KV8/D128/V128256。Qwen32的Q投影宽8192不等于H5120。Qwen各层Q/K norm各128元素保留，Llama无此二norm；全部层hidden norm与最后norm正确复制。

对45个模型×拓扑×group组合，独立构造每rank全部权重名称、本地形状和copies，逐tensor三格式payload/scale均匹配。拓扑包括TP8、TP2/PP4、PP8、TP16及TP2/PP2/DP2；group128/1000/32768。词表首尾PP放置、norm和独立head的BF16例外均逐项检查，未只比较汇总总数。

## 分片后量化

gate/up按FF输出行分片，down按FF输入列，O按Q投影输入列。每个本地矩阵按每行ceil(localK×bits/8)字节和ceil(localK/group) scale计量，再乘拥有的层数；不能先算全局scale再除TP。

真实反例：Qwen8 TP8 down本地4096×1536，group1000每行2个scale；全局K12288的13组除8仅1.625组，不合法。独立oddK例3×5矩阵4bit每行3B总9B，而全局nibble打包8B不能替代逐行9B。group32768超过所有localK时仍每行一组。scale为声明metadata字节，不声称某量化checkpoint格式或kernel质量。

## KV、DP cohort与最差rank

length含末新增token，底层history=length−1/tokens1，独立KV公式`4×localLayers×localKVHeads×128×length`不随权重位数减少。TP16以完整GQA身份验证每query头映射；每KV头跨两rank复制，不能再按总KV/16虚构半头。base BF16驻留语义保持。

DP每副本拥有完整TP/PP共同请求cohort，容量先在该副本rank中取min，再跨独立副本相加。全部45组合验证此守恒；另外三模型PP3/DP2最坏rank恰好1请求预算±1字节，共9项检查，得到全局0/2/2请求，未用总空闲显存代替最差rank条件。

## 边界与公共接入

低位只改变声明存储，不借base BF16矩阵/通信参考值暗示低位kernel吞吐。workspace是每rank固定reserve；临时反量化、activation、collective和allocator可能额外需要空间，actual_runtime_peak保持null。router临时这一通用文案对Dense无新增常驻量，不误增权重。

作者8项测试重跑通过。markdown确有逐rank/per-tensor三格式及范围说明，按storage payload/scale列显示；weight记录继承的bytes仍是BF16参考，不能与低位storage再相加。公共CLI/reproduce仍由主线集成后验证，本审查不替代它。

重跑：`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/dense-quantized-placement-independent/check.py`。检查45组合、9个边界、localK/奇数行反例；作者测试8项独立重跑已通过。
