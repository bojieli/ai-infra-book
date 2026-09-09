# 第 2 章等参数结构变体：独立候选

入口 `src/infra_calc/topics/architecture_variants.py:calculate`，只读公共 Qwen3-8B 配置、来源和逻辑算子实现。候选与 7 项独立回归、4 个 JSON 场景均在本目录，未改公共目录。`integration.json` 绑定基线 config 和复用模块 SHA；`summary.json` 给出默认简表。它补实验 2-7 的结构变体计算，不把整个多模型/多格式八卡实验标为完成。

只有 baseline 是已发布模型。其余为未训练、未测质量的明确结构变化，不声称能加载原权重、保持原输出或实现相同质量。

令 L/H/Q/K/D/F/V 分别为层数、隐藏维、query/KV 头、head_dim、FFN 与词表。保留官方无 bias、非共享词表头、Q/K Norm 和两个层 RMSNorm，参数数为：

`P = 2VH + H + L(2HQD + 2HKD + 3HF + 2H + 2D)`。

每个变体指定 L/H/Q/K，保持 D=128、V 与上下文，解出理想有理数 F，再就近按128对齐。实际参数不相等时保留精确差额；上界为 `3LH×128/2`。不增加未使用“填充参数”来伪造等参。baseline 始终采用原 F，其他 alignment 输入也不改变基线身份。

默认 B=1、已有8192历史、一次新token、TP=2、每卡24 decimal GB、每卡2GiB工作区保留量：

| 结构 | 参数数 | 矩阵 FLOPs | 每历史token KV bytes | 每rank声明存活预算 bytes | 串行decoder层 |
|---|---:|---:|---:|---:|---:|
| 基线36层/H4096 | 8,190,735,360 | 19,968,622,592 | 147,456 | 10,942,580,736 | 36 |
| 24层/H4096 | 8,178,051,072 | 18,332,647,424 | 98,304 | 10,728,443,904 | 24 |
| 48层/H4096 | 8,165,670,912 | 21,529,100,288 | 196,608 | 11,118,968,832 | 48 |
| 36层/H3072 | 8,195,641,344 | 19,081,641,984 | 110,592 | 10,796,398,592 | 36 |
| 24层/H5120 | 8,209,296,384 | 18,889,277,440 | 98,304 | 10,759,739,392 | 24 |
| 36层/H4096、KV2、FF12800 | 8,190,735,360 | 19,968,622,592 | 36,864 | 10,489,540,608 | 36 |

精确等参例减少6个KV头，把释放的 K/V projection 参数用于增大FFN512；原有 QK/PV query heads 不减少。因投影参数总量守恒，矩阵 FLOPs 相等，而历史容量与每步旧历史读取降至1/4。其 ordinary scalar 与activation接口因形状改变不宣称相等。默认场景单rank预算在 `[10,489,540,608, 10,942,580,735]` bytes 时，该变体能容题设batch而基线不能。阈值前后1byte已真实调用验证；没有把预算优势推成质量或吞吐优势。

TP限定完整可整分 Q/KV heads、FF与词表，矩阵权重沿声明轴切，norm复制；不把KV复制悄悄补进去。`TP=8`对整组变体会拒绝，因为KV2与KV6不能这样无复制分。单卡场景单独输出。norm复制、每rank权重、旧历史读/append/末状态分别守恒。

通信子账只包含每层attention output和FFN down的两次all-reduce。一次payload为 `B×P×H×2`，ring每rank线字节为 `2(TP−1)/TP×payload`；总调用数 `N=2L`。若同一有效链路速率 `R>0` 和每次启动 `a≥0`，这个明确子路径比较满足：

`T_variant − T_base = Δwire_bytes/R + ΔN×a`。

结果直接保留 Δwire 和 ΔN，可代入测得速率。默认24层/H5120相对基线少98,304线字节、少24次collective；48层/H4096多196,608线字节、多24次collective。没有伪造硬件速率。词表/embedding通信、实际调度重叠、latency与带宽争用仍不在该子账；不能据此算完整请求时间。矩阵工作、权重/历史读取、串行层深与这些通信条件必须分别评估。

算子表复用公共固定 Qwen 逻辑实现，涵盖矩阵、普通标量、特殊调用和逻辑操作数读写。prefill、6144+2048 prefix、B64 decode 的 FLOPs另由独立闭式公式核验，而非测试复述实现循环。分数精度遵从 `Scenario`，BF16 weights/KV与FP32分数临时不能混同。工作区是固定保留输入，完整生命周期peak与后端HBM未推断。

复核：

```sh
python -m unittest discover -s calculations/research/architecture-variants/tests -v
PYTHONPATH=calculations/src python calculations/research/architecture-variants/freeze.py
```

7项测试覆盖：参数枚举与独立式及误差界、精确等参/缓存变化、三种请求形状矩阵闭式、TP复制和状态守恒、真实容量翻转±1byte、ring公式和单卡零通信、非法形状/布尔/上下文拒绝。测试结果与产物均不是运行模型的质量证据。后续接CLI仅需新增独立topic入口及book四场景；公共测试迁入时应将候选动态导入改成正常topic import。
