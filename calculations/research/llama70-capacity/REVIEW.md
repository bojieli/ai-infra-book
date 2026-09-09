# C13 真实70B单设备容量扫描候选

只读共享项目，候选在本目录。复用已集成 `infra_calc.models.llama70.weights/validate`，身份固定为 `deepseek-r1-distill-llama-70b`，不使用名义70e9，不替换旧Meta401身份。只完成原C13中的真实70B单设备扫描接入，不勾选整个C13。

## 合入文件及公共契约

- [capacity_scan.py候选](src/infra_calc/topics/capacity_scan.py)：增加Llama70分派与BF16 full-history GQA KV几何，其他格式／容量算法不变。
- [8项独立测试](tests/test_llama70_capacity.py)。
- [merge-guards.json](merge-guards.json)：共享capacity_scan before SHA与候选SHA，测试要求目标不存在。
- [4个场景](scenarios.json) 与 results/ 对应独立计算输出。

公共函数签名不变。调用：`capacity_scan.calculate(model='deepseek-r1-distill-llama-70b', length=8192, ...)`。新计算标识为 `llama70-single-device-capacity-scan`；其余模型保留原标识、完整JSON和原参数。已有CLI的`capacity-scan --model`可直接复用，不需要增加新命令。返回保留公共capacity/storage格式schema；现有scenario中kv_element_bytes是输出口径字段，不是新增输入参数，本候选未借机更改该旧契约。

state.py尚无Llama分派，故本候选仅在容量模块按该固定config计算KV，没有扩张共享state或新开计算专题。长度必须为正整数且≤131072；Llama adapter继续校验bias-free、untied head、GQA、完整RoPE及pretraining_tp=1等固定模型契约。

## 独立参数与量化手算

H8192、F28672、L80、Q64、KV8、D128、V128256。

可量化矩阵元素：

`L × [2H² + 2H(KV×D) + 3HF] = 68451041280`。

保持BF16的两个词表矩阵与norm：

`2VH + (2L+1)H = 2102665216`。

两者合计 **70553706496 参数**，BF16字节 **141107412992**。Llama没有Qwen的Q/K head norm；不是把Qwen总参数直接套过来。

教学低位格式只压缩7类每层二维linear：Q/K/V/O与gate/up/down。Embedding、lm_head及全部一维norm保留BF16；Llama没有MoE router，但原Qwen router例外继续保留。

每个输出行独立打包 `ceil(K*bits/8)` bytes，metadata为 `ceil(K/group_size)*scale_bytes`。默认group128／scale2，所有实际K维均整除128；两种低位格式metadata均 **1069547520 bytes**：

| 格式 | payload bytes | scale bytes | 合计 weight bytes |
| --- | ---: | ---: | ---: |
| BF16 | 141107412992 | 0 | 141107412992 |
| 8-bit教学方案 | 72656371712 | 1069547520 | 73725919232 |
| 4-bit教学方案 | 38430851072 | 1069547520 | 39500398592 |

非整除group1000场景明确验证K8192的9组与K28672的29组：metadata为 `2*80*(75776*9+8192*29)=147128320` bytes，4-bit合计 **38577979392**。它只是另一分组教学方案，不暗示与group128具有相同误差、同一量化checkpoint或某设备支持该kernel。

未计zero point（声明对称方案）、codebook、重排tile padding、运行时反量化展开、kernel workspace及质量；不能把bits字段当下载到的真实checkpoint dtype。

## 四个代表场景与容量边界

BF16 GQA每请求每token：`2 × 80 × 8 × 128 × 2 = 327680` bytes。8K为 **2684354560 bytes（2.5 GiB）**，32K为 **10737418240 bytes（10 GiB）**。低位权重不改变此BF16 KV。

单设备预算 `C`、固定workspace `W=2147483648` 时：

`available=C-weight-W`；`max_requests=max(0,floor(available/KV))`。

| 场景 | 24 GB | 48 GB | 80 GB |
| --- | --- | --- | --- |
| 8K，BF16权重 | 权重／workspace不fit | 不fit | 不fit |
| 8K，8-bit | 不fit | 不fit | 1请求 |
| 8K，4-bit | 不fit | 2请求 | 14请求 |
| 32K，4-bit | 不fit | 权重fit但0请求 | 3请求 |

容量是decimal GB，workspace是2 GiB，不能混用单位。group1000是第三个场景，按完整逐矩阵公式对照；第四个场景使用4-bit、8K的精确3请求阈值 **49700945920 bytes**：预算减1为2请求，等于或加1为3请求。另有独立测试覆盖恰好装下权重+workspace但无KV，与权重本身不fit，两者不能用“0请求”混为一谈。

## TP／八卡约束

本模块明确是 **TP=PP=DP=1的完整模型单设备驻留**，函数不接受tp参数；传tp=8会拒绝，8项24GB budgets会生成8个独立比较，不会求和成192GB。config的pretraining_tp=1是固定参考实现校验，不是声称该模型不支持分布式部署。

后续真正TP放置必须另做逐张量所有权：Q头、F及词表行的可分性；KV按完整头保留（TP>8时KV头会复制，不能再按总KV/TP）；norm复制；embedding/head端点放置；K向切分后量化分组边界和scale重新计算。当前已有dense_placement专为Qwen，不能仅传model名字并宣称完成70B八卡容量。故本候选不提供假TP总容量结论，C13其余八卡、工作区、结构扫描仍未完成。

## 验证与集成边界

隔离公共src覆盖本候选后：**8项新测试 + 3项现有CapacityScanAccounting测试通过**。Qwen3-8B／30B-A3B／235B-A22B默认完整JSON与共享当前实现精确相等，见 qwen-exact-equivalence.txt。4场景已生成。

合入只需校验beforeSHA后替换capacity_scan、增加测试，将scenarios.json行按现有capacity_scan book组结构并入；公共CLI本来已接受model。report通用capacity表适用，主线可再做CLI/报告与全量reproduce。来源继续公共provenance，不新增官方下载，不改PLAN完成状态。

现有book的capacity_scan是扁平行（非inputs包裹）；已额外生成可直接追加的 [book-group.append.json](book-group.append.json)。隔离现有CLI运行 `capacity-scan --model deepseek-r1-distill-llama-70b --format md` 成功，输出见 cli-example.md。主线可将CLI help中的“Actual Qwen shapes”增量改成“Actual Qwen/Llama70 shapes”，无需改dispatch或report；该文案修改未写共享。
