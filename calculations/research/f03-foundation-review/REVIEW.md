# F03 公共基础独立审查

**当前不宜整项勾选，但缺口有限且有实际反例。** 本次限定公共数值/形状/读写记录、CLI输出、源文件重取、结果绑定，不要求完成尚未实现的模型或全部运行时。

`counterexamples.py` 仅在临时目录和mock HTTP中运行；未改共享文件，未下载来源。`counterexamples.json` 是实测结果。检查同时阅读公共代码，未把既有专题测试通过当作公共契约完备证明。

## 已成立的契约

Scenario拒绝布尔/非整数尺寸，区分有效因果对与矩形执行对；最后head/all/none明确。单位区分十进制GB/TB与GiB，FMA按2操作。linear明确逻辑操作数读一次写一次，不自动称HBM实测流量；traffic沿每条声明资源路径计费，重复资源计重复服务。严格硬件选择已区分输入/累加/单元/稀疏，未知拒绝，整数TOPS不当FLOPs，TF32不当IEEEFP32。

结果复验先调用verify_sources，再核inputs及产物SHA，因此模型config虽未全部直接列进input_hashes，已通过来源锁和原件哈希间接覆盖。不要误报“所有模型配置不受保护”。当前725条inputs无重复，包含CLI实现、全部计算源码、book场景、配置锁与硬件表。独立结果见dependency-coverage.json。

## 必须修正的实际反例

| 问题 | 实际结果 | 有限修正 |
|---|---|---|
| Weight未校验shape/copies/元素字节 | `(True,2)`当2参数；`(-2,3)`生成-12驻留bytes；bytes=True被当1 | 用公共整数校验；零维尺寸/零副本按明确空工作策略处理 |
| linear未校验矩阵维度 | rows=-1生成负FLOPs与负读写字节 | rows非负整数，K/N正整数，repeats非负整数 |
| Operator未校验工作字段 | scalar_flops=NaN可进入record，默认JSON会输出非标准NaN | 所声明工作/字节/次数为非负整数；若确需期望小数，另列字段/语义，不能混为实际整数字节 |
| positive_number输入类型 | 字符串返回TypeError而非公共ValueError | 先检查支持数值类型；CLI仍保持清晰错误出口 |
| 非Range重取无读取上限 | mock记录read()无参数 | 所有源按锁bytes+1最多读取，长度不等直接拒绝 |
| 本地/远端只核SHA不核锁bytes | 实际3字节、锁bytes=2但SHA正确时fetch和read_source均接受 | SHA与长度都核，拒绝相互矛盾的锁记录 |

`proposed-foundation.patch` 为前三个公共文件的独立候选diff，未应用。完成语法检查，需主线应用后运行公共边界测试及少量代表adapter，检查旧调用是否把期望值/特殊调用错误塞入整数计数字段。不要直接对全部专题扩展测试。

## 另外三项有限闭合

1. **输出JSON禁止非有限数。** CLI与reproduce写JSON使用`allow_nan=False`；公共record校验之外，专题字典也不能漏出NaN/Infinity。加入一个模拟结果含NaN的序列化拒绝测试即可，不必逐专题造测试。
2. **来源Range与临时文件。** 现代码在206且Content-Range前缀正确时有bytes+1上限，这一保护已成立；但应解析完整数值范围、总长度并核`end-start+1==锁bytes`，而不是只startswith。候选diff已将固定`.download`改为同目录唯一临时文件并finally清理，避免并发重取共享临时路径。增加错误206、错误范围、过长/过短、SHA失败均不替换原件的mock测试；无需真实下载全部原件。`fetch --model`目前是来源组过滤，不是自动递归模型依赖，需在CLI帮助中明确或复用F02依赖图，二选一即可。
3. **结果清单边界。** 当前空artifacts列表也会成功返回0验证；这不是抵御恶意修改的签名协议，但缺少基本清单完整性校验。应要求非空/唯一、所需字段及安全相对结果路径，至少保留不可为空的核心产物（如README/hardware）断言；已列产物逐一hash继续保留。任意被同时改写的manifest与内容不受密码学认证是正常信任边界，不声称能防篡改。公开入口`calc.py`当前不在inputs中，补入该文件；Python CLI模块已在，不能混淆两者。

## 验收步骤

应用数值/shape/字节边界修正和来源有界读取；加入有限反例回归；补JSON非有限拒绝、Range严格解析、入口绑定、结果清单形状校验及fetch组语义。跑公共单元/来源mock/CLI非法参数与一个dense及一个MoE合法输出检查，然后一次正常reproduce/verify-results形成新结果绑定。以上通过即可验收F03；模型forward完整性、实际硬件流量及硬件有效利用率留在原专题任务。
