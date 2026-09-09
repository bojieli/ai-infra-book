# Qwen3.5 基础文本参考执行账：续补交付

本目录独立于共享CLI/config/reproduce。接口仍为 `qwen35_forward.calculate(batch=1, tokens=8192, history=0, output_head='all', routing_counts=None, chunk_size=64, record_past=False)`，没有新增必填输入，结果可 `calculate(**result['scenario'])` 重放。新增 `reference_execution_steps` 与summary的参考路径／整数操作计数；旧字段保留，但默认算术小计已经包含下文补齐项，旧结果必须重生成。

## 本轮落实的既有缺项

[qwen35_forward.py](qwen35_forward.py) 与 [reference_steps.py](reference_steps.py) 已共同覆盖选定的纯文本、无外部padding/custom mask、BF16、use-cache、非export PyTorch fallback路径。完整attention固定按eager矩形执行；DeltaNet按chunk64或带状态单步递推选择。不是根据目前默认安装后端猜测执行路径，也未声称hub替换kernel使用相同工作。

1. **Chunk准备与扫描。** 补FP32 cast、padding、beta K/V、cumsum、三角mask、pairwise差分／mask／exp、UT与intra衰减乘法、三次cum-decay转换、最终decay、两次unit-triangular求解接口、输出zero/赋值、state更新加法和最终cast。六类chunk GEMM与两次solve维度保留，前代替代算术属于scalar、不当GEMM。所有chunk head／block重复次数明确；65token确实用128个核心位置。Cumsum按数学prefix-add次数计，不能冒充并行scan内核指令数。
2. **卷积真实源码输出槽。** 先算Conv1d全部输出，再按源码裁切。冷T1且普通cache先pad到4，Conv1d实际产生7个位置，SiLU作用4个后最终留1；cached单步拼4+1，conv产生2位置后裁1；cached多token拼4+T，保留prefix参与重算。原有效tap小计与新增padding／弃置位置之和为该稠密卷积几何的FMA=2工作。未把padding的0乘法假装不存在。
3. **共享RoPE及mask构造。** RoPE每次forward只调用一次，三轴frequency outer-product、sin/cos、乘attention_scaling=1、21个H/W切片重组、duplicate、cast均列出；layer内rotate-half取负和concat另计。新增同commit固定 [masking_utils.py](reference_sources/masking_utils.py) 原件及hash，按eager非vmap纯causal路径计arange／offset、batch expand前T×(S+T)比较及最终BF16 where；linear attention mask在本输入下为None，不虚构逐元素mask乘法。inv_freq模型初始化单列，不反复按forward收费。
4. **Router与完整attention。** 增加FP32 router softmax／topk接口、selected renorm／cast、int64 one_hot清零和scatter、expert-hit reduce／compare／nonzero、逐激活专家where、hidden/probability gather、输出zero、index_add destination接口。Topk/where等以真实dtype、形状和调用次数表示，不猜其后端比较／扫描算法。完整attention补矩形masked槽、mask相加、矩形softmax以及KV concat／repeat、QK、PV和contiguous接口；有效causal矩阵仍单独输出供比较。
5. **Norm/gate内部接口。** 所有普通offset RMSNorm及gated RMSNorm补cast、square/mean/epsilon/rsqrt、权重cast/加一、乘法、输出cast；z→FP32 SiLU、decay与beta、L2norm、query scale、MoE/shared/output gate的内部接口逐项记录。FP32 A_log负号也从主账遗漏项补入。

## Record-past 与精确范围

Conv-update要求已有state、T1且 `record_past=False`；DeltaNet-recurrent只要求前两项。已有记录的 `record_past=True` 长度不能由history唯一推断，因此该情况的卷积额外执行及记录缓冲保持unknown。初始 `record_past=True` 已可确定：缓存赋值alias输入T个位置，无last4 copy；字段 `record_past_retained_conv_bytes` 给出实际T长度，lazy-initialized四槽临时buffer另列。

基础文本1038个tensor逐项匹配锁定原始header，参数396346350336、checkpoint bytes792692717952；全专家权重与active top10执行分开。vision、MTP保持排除，独立source存储账仍含它们。

三种口径必须分别使用：

- **算法算术：** GEMM/conv用FMA=2，逐元素加乘分别计，solve/cumsum/reduction用声明数学算法计。特殊exp、sigmoid、softplus、rsqrt、sin/cos及topk调用单列，不折算成Tensor Core FLOPs。
- **源码执行几何：** eager完整矩形、chunk padding和conv弃置输出确实纳入所选fallback的算术几何；不能拿valid-only公式替代，也不能声称等于每个实际kernel指令计数。
- **张量接口：** 原 `operators` 记录算子边界；新增90条（8192场景）`reference_execution_steps.steps` 记录补充语句接口。两者有重叠，**禁止把两个bytes总和相加**，也不能把它们叫HBM或peak allocation。view/alias、primitive内部workspace、融合及allocator需后端证据。

`full_forward_exact=false` 继续保留，因为其原意不能升级成真实整个运行时精确工作。此前点名的默认基础参考路径算术缺项已逐项落实；剩余是明确的primitive内部算法／alias／内存分配范围，以及未知历史记录长度、非本接口输入的packed/padded mask与export/hub kernel分支，不是再留一张模糊“以后补非矩阵”清单。

## 验证与场景

```bash
PYTHONPATH=calculations/src python -m unittest discover -s calculations/research/qwen35-adapter -p 'test_*.py'
python calculations/research/qwen35-adapter/run_scenarios.py
```

20项本地测试通过：独立参数闭式式、1038个raw-header形状、场景重放、KV追加／MoE assignment／矩阵汇总守恒、chunk边界、head范围、conv/Delta路径，以及新增短序列chunk两solve+scan对逐token递推的数值等价（有／无初态、尾块padding）、cold T1卷积手算、record-past alias、三轴RoPE和causal-mask batch-expand／router元数据手算。另有团队独立冻结快照审查，数值与核心矩阵未发现错误；其报告由独立代理交主线。

八个真实config场景在 [scenarios.json](scenarios.json)、[scenario-summary.json](scenario-summary.json) 和 results/：

| 场景 | 当前已计矩阵工作 | 路径 |
| --- | ---: | --- |
| cold单token | 59868938432 | chunk64；普通cache先pad4，conv7输出 |
| cold单token record_past | 59855667392 | chunk64；cache alias1，conv4输出 |
| 8192 prefill | 304038065373184 | 128 chunks；eager矩形attention |
| B1 decode，8192历史 | 36977377472 | recurrent；conv input5、output2 |
| B64 decode，8192历史 | 2366552158208 | 同上，batch64 |
| 6144+2048续算 | 76009543991296 | 32 chunks；卷积prefix重算 |
| 65token尾块 | 2179531092160 | 2 chunks，核心padding128 |
| cached单步record_past | 36972953792 | recurrent；卷积记录长未知，故只保留其已知部分 |

最后一行不可与默认decode当作完整性能比较，因为其卷积额外工作unknown。所有表值均是声明几何／算法口径，不是runtime预测。

## 主线集成注意

可在独立复核后将主模块和reference_steps并入同一topic，路径改用公共PROJECT、同revision来源用公共provenance；本目录mask辅助原件尚在独立lock，集成时需纳入来源/复现输入。新模块只读固定原件，不会自动联网或读取权重payload。共享CLI、book与outline的旧小计文案必须更新为当前参考路径口径；不要只把旧“valid logical”说明留着换数字。
