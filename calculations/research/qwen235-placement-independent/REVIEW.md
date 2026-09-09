# Qwen235 eight-rank placement independent review

结论：冻结候选与CONTRACT一致，可按声明的TP/EP/PP存储组织集成；无数学或逐rank容量阻塞。共享文件和作者目录未改。结果与源码快照SHA见results.json。

## 官方身份与参数

固定config：H4096、Q64、KV4、D128、F1536、L94、E128、V151936，全部94层为MoE、top8激活、无shared expert。注意Q投影宽8192，不等于hidden4096，不能沿用QH×D=H的Llama公式。

独立构造每层384专家矩阵+9非专家tensor，加3端点，共36945名称，逐名匹配官方index。独立参数合计235093634560，BF16总470187269120B与index metadata一致。索引是名称和总字节证据，不冒充逐tensor header形状证据；形状仍来自config/implementation。

## 所有权和共同cohort

EP分128 experts的互斥连续区间，TP对每expert gate/up行和down列分片；全部专家驻留，top8不减少权重容量。attention及同一请求KV跨EP复制，EP不是另一个DP请求批次。TP切Q头及O列，KV完整头对齐其query GQA组：TP8每两rank共享同一个KV头，必须两份K/V投影及缓存。norm/router跨TP/EP完整复制，词表TP分片但EP复制。

PP分94层的连续范围，PP8为12/12/12/12/12/12/11/11；词表embedding首stage，head和finalnorm末stage。分配和worst rank保持该不对称。该所有权图只是明确声明的可执行组织，未证明特定引擎采用它；缺失dispatch/汇聚通信不被容量表掩盖。

独立总权重守恒：令A为全attention参数、X为全部专家、N为所有norm、R为router、V为两个词表，r=max(1,TP/4)，Kp为全K/V投影参数。全物理BF16字节为 `2×[X+EP(A+V)+EP(r−1)Kp+TP×EP(N+R)]`。12种topology/group组合均符合，不能将这些复制后的总字节误叫原模型参数。

## Local K metadata与容量

6种拓扑×group128/1000=12组合，96rank×三格式逐项用独立固定维度列表核对payload/scale。只量化attention和expert；norm/router/embedding/head维持BF16。每个local矩阵每行ceil(localK/group)个scale。TP8 expert down本地shape4096×192、group128为每行2组；全局1536有12组，除8得1.5不是合法组数，候选正确重新分组。scale为声明metadata字节，不是实际已发布quant checkpoint/质量保证。

每rank BF16 KV=`4×local_layers×local_KV_heads×128×length`，不除EP。容量余量先减实际local权重/scale与每卡workspace，再除该请求KV。共同cohort最大请求数取所有rank最小值。独立PP8最坏rank的恰好1请求预算±1字节验证0/1/1请求；不能把其余rank空余汇总弥补瓶颈rank。

## 验证与范围

check.py验证36945索引名、精确参数、12组合96rank×3格式、TP8头映射、物理复制守恒、localK尾组反例与worst-rank边界。作者7测试另行重跑通过。源码/结果绑定供主线合入后再做CLI/report/reproduce，未声称研究测试即公共验收。

权重是持久量，router临时概率/dispatch索引/反量化scratch不作为每层常驻权重；它们归于未知实际workspace。ownership记录是说明性host metadata，不编造GPU存储量。actual_peak与routing_temporary保持null。此结果不提供时延、带宽或实测部署保证，C13更大范围仍由主线另核。

运行：`PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/qwen235-placement-independent/check.py`。
