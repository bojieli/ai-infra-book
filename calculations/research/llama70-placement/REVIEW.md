# C13 public Llama70 BF16 per-rank placement candidate

冻结候选仅在research/llama70-placement。将src/infra_calc/topics/dense_placement.py按merge-guards替换现有模块，新增tests/test_llama70_placement.py；不改共享CLI/reproduce。模型固定deepseek-r1-distill-llama-70b，复用公共已核weights/config/provenance，无名义70B或单卡容量求和近似。

## 所有权

TP对64个query heads、28672 FFN中间维、128256词表行作可整除分区。Q和O对应输出/输入切片；K/V根据实际query头的GQA映射取完整128维KV头。TP8每rank一个KV头，TP16每个KV头在两rank复制。新增Llama专有ownership给出FFN/词表半开区间和投影轴定义，已有query_head_ids/kv_head_ids给出确切身份。

每层两个8192元素RMSNorm在拥有该层的TP ranks上完整复制；末层finalnorm也复制，没有Q/K norm。PP连续均分层（余数优先前stage），embedding只在首stage，独立lm_head和finalnorm只在末stage，两个词表矩阵分别按vocab行切。DP完整复制所声明TP×PP组织，每个副本服务batch_per_replica请求。拒绝不能整分头/FFN/vocab的TP、空PP和超config context；config pretraining_tp=1不是禁止部署TP。

## 独立守恒

令P=70,553,706,496；N=(2×80+1)×8192=1,318,912个norm参数；K=2×80×8192×8×128=1,342,177,280个K/V投影参数；r=max(1,TP/8)（此固定模型允许TP均为64的整除数）。

所有卡权重总字节：`2×DP×[P+(TP−1)N+(r−1)K]`。

所有卡KV总字节：`DP×r×2×80×batch×(history+tokens)×8×128×2`。每rank则使用本stage层数及实际拥有KV头数。独立测试还按每卡Q/K头集合、端点、norm和FFN维逐项核对权重、KV与resident，并在最大rank所需字节±1处验证fit。

有效矩阵包含实际本地线性、最后新增位置head与有效因果attention。TP16多出的K/V矩阵工作计两份；attention按query头切分不重复。三个投影/attention闭式对照包含batch2/tokens3/history7与DP2，避免只测decode1。

## 固定8卡结果

history8192、tokens1、batch_per_replica1；默认每卡24 decimal GB、workspace2GiB。缓存长度8193，不是容量模块仅驻留8192的场景。

| 组织 | 卡数 | 最大rank驻留 bytes | 所有卡满足预算 |
|---|---:|---:|---|
| TP8 | 8 | 20123803648 | 是 |
| TP4×PP2 | 8 | 20122492928 | 是 |
| TP2×PP4 | 8 | 20647174144 | 是 |
| PP8 | 8 | 21697519616 | 是 |
| TP4×DP2 | 8 | 38097485824 | 否 |
| TP16（复制反例） | 16 | 11472527360 | 是 |

前四组织logical forward矩阵皆160480886784 FLOPs；TP16为163165241344，增加2684354560 K/V投影FLOPs。前四KV物理总量2684682240字节，TP16翻倍5369364480。DP2也翻倍但原因是独立请求副本。等层数不意味着等rank驻留：PP首尾词表端点决定最大rank。

## 范围与验证

5项独立测试，包含6种权重守恒组织、额外PP3非均匀逐rank检查、±1byte容量、不可整除输入反例及矩阵闭式。另有4种原Qwen组织完整JSON逐值一致。实际现有dense-placement CLI/Markdown成功，见cli-example.md。重跑 `PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/llama70-placement/verify.py`，仅内存注入候选，无共享磁盘修改。

消息字段延用既有basic TP路径：每层两次输出归约、TP匹配rank之间全hidden PP载荷。它们是消息payload，不是拓扑链路流量；embedding归约/logits收集/采样等完整通信图尚未闭合。固定工作区非真实allocator峰值，scalar/cast、调度驻留/反压、量化分组重切及真实速度也未声称完成。此补项完成BF16逐rank权重/KV/声明workspace与主要矩阵放置，不能勾选整个C13。
