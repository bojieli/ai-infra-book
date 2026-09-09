# 第 2 章：四模型同请求累计逻辑账

候选仅在本目录；入口 `src/infra_calc/topics/request_model_comparison.py:calculate`，另有 `markdown(result)`。原文2-9的四个模型保持为 Qwen3-8B、DeepSeek-V4-Flash、DeepSeek-V4-Pro、Kimi K3。

统一输入：`prefix_tokens=S≥0` 为已恢复的同模型前缀、`new_tokens=P≥1` 为本次新输入、`output_tokens=G≥1` 为声明返回长度、`batch=B≥1`。另显式选择 K3 expanded/compact 和教学路由分布。

最后一个输入位置的logits产生首输出；因此只再执行 `D=G−1` 次单token前向。最后状态位置数是 `S+P+G−1`，而不是 `S+P+G`。最后返回的token还没有重新送入模型。G=1没有decode前向。sampling、EOS提前终止、工具调用、tokenizer及真实选择的token IDs未推算；相同token数不保证不同模型看到同一文本或具有相同质量。

## 路径与调用

Qwen使用公共完整逻辑前向。K3输入使用chunk/recurrent的已声明路径；固定源码把恢复的recurrent_state传给chunk_kda，卷积缓存也需匹配前缀。A_log的checkpoint128与config/source96冲突在各模型总汇coverage保留，不能称可直接加载运行。compact是代数替代，默认expanded才对应固定HF缓存表示。

V4在S=0走一次完整输入前向，在S>0用新公共顺序prefix入口，P个已知后缀逐token运行，包括P次实际词表头。中间head虽丢弃仍计工作；它不等价于一次并行chunk。decode同样逐位置枚举compressor与index/sparse-tile边界。源cache分配以最终长度和batch显式声明（覆盖ModelArgs默认值），FP32槽与BF16缓存总预算另列，频率表、权重和其它临时不包含。

Qwen/K3的decode全历史贡献对已处理长度是仿射函数，其他单步子图固定。Qwen取相邻历史两次完整逻辑账构造差分；用前一位置取差，避免在40960上下文上界为了估斜率访问越界位置。K3直接由24层、heads和qk/pv维度算增量：每增加一个历史位置，矩阵增加 `2×B×L_MLA×heads×(qk_dim+pv_dim)`，softmax普通算术增加 `4×B×L_MLA×heads`，exp与compare各增加 `B×L_MLA×heads`。KDA状态本身不随历史增长。

K3每模型只有输入阶段与首decode两个checkpoint核验；两个V4模型各两个静态阶段。读取次数不随D增长。不是缓存掉每次专家/mHC/head实际计算；静态工作仍计入每步。G1无需第二阶段核验。

## 默认小例

S=0、P=128、G=4、B=1，D=3，K3 expanded，最后保留131位置：

| 模型 | 全请求矩阵 FLOPs | 末状态 bytes |
|---|---:|---:|
| Qwen3-8B | 1,829,869,322,240 | 19,316,736 |
| V4-Flash | 3,397,735,284,736 | 18,722,816 |
| V4-Pro | 12,719,961,440,256 | 27,966,464 |
| Kimi K3 | 27,127,913,615,360 | 647,626,752 |

这些是各声明路径的有效逻辑矩阵总数，不是同质量性能排名。K3末状态含固定递推/短卷积；V4有效状态含FP32 compressor槽；不能只按末历史长度横比缓存宽度。

四个结果场景还包括S0/P1/G1、125+3跨128边界及6144+2048前缀。每个JSON保留输入阶段源子账、逐decode矩阵/scalar/special、已知接口和末状态，及全段合计。完整HBM、runtime峰值、完整scalar、延迟和质量等价都保持unknown。词表头次数、V4序列输入次数与输出数量不混淆。

## 如何接硬件与原实验剩余

当前闭合的是共同输入下的四模型逻辑累计入口。权重BF16是比较格式；V4实际专家packed+scale与BF16专家列互为替代，不可相加。不同模型interface覆盖程度不同：Qwen逐算子操作数较全，K3和V4仅列已有审定子项。因此不能对混合接口列直接做一个GPU时延排名。基础runtime转换/allocator、prefix取回、实际路由与固定任务质量记录仍是原实验2-9剩余范围。

后续只能对已匹配precision/unit/dense或sparse的单项工作，连接硬件审定分母与对应资源；完整源范围unknown保留。不要将未知流量填零以完成Roofline。

```sh
python -m unittest discover -s calculations/research/request-model-comparison/tests -v
PYTHONPATH=calculations/src python calculations/research/request-model-comparison/freeze.py
```

9项回归覆盖原名单、G−1/head差异、12个逐步完整forward对照、cold P1/G1、K3 compact、checkpoint常量次数、B2状态和源分配、scenario完整重放、上下文边界以及unknown/冲突传播。公共迁移时只需新增topic/CLI与四个book场景；测试的候选动态导入换成正常topic import。共享目录没有修改。
