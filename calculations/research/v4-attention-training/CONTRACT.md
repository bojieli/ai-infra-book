# V4 tied-KV sparse attention 的有限训练反向

## 来源与数学边界

固定官方 `inference/kernel.py:277-365` 定义 q[B,T,H,D]、kv[B,K,D]、sink[H]、indices[B,T,J]；Q、KV、输出是 BF16，sink/分数/累加是 FP32。源码在 PV 之前把未归一化指数值 cast 为 BF16，再以 FP32 分母归一化。**这不是精确 softmax 概率参与 PV 的实数算法**。本候选明确去除这些舍入，不能用数值测试声称与量化内核逐值等价，也未替这些 cast 自行选择 STE。

冻结 `model.py:479-541` 使用一个 KV 张量同时做 key/value，窗口索引和压缩索引拼接。这里实现一个 core，不含外围投影、RMSNorm/RoPE、压缩器、indexer loss、量化训练策略，也没有乘 43 层。默认尺寸取固定 Flash 的 H=64、D=512、窗口128；可显式声明小尺寸测试图。配置与官方代码的完整锁记录在 public/sources.lock.subset.json，均为既有公共锁原件。

默认输入是 start_pos=0 的因果窗口有效 ID 集合；padding 顺序为本参考声明，不声称源码槽位逐字相同。可显式传一个矩形 indices[T,J]，B 个独立样本重复同一索引日程。只有 -1 是无效槽位，其他越界和 bool ID 拒绝。每查询必须有有效键；当前官方 online max 的全无效边界不在契约内。

重复 ID 保留为不同 softmax 项。去重会改变输出与梯度，不能以缓存去重语义替代算子数学。

## 前反向图

对每个 query/head 和其 v 个有效槽位：

- s_j=scale dot(q,kv_j)，sink 作为额外一项进入分母。
- p_j=exp(s_j)/Z，p_sink=exp(sink)/Z，o=Σ_j p_j kv_j。
- dp_j=dot(do,kv_j)，δ=Σ_j p_j dp_j。
- ds_j=p_j(dp_j−δ)，dsink=−p_sink δ。
- dq=scale Σ_j ds_j kv_j。
- dkv_j=p_j do+scale ds_j q。

局部 dKV 的 key/value 两路先相加，再按原索引累加到**同一个** dKV；重复槽位、多个 heads、多个 queries 全部归并。sink 按 B×T 行归并。固定索引没有连续梯度，仅说明该 core 主损失数学，不能据此说 indexer 不训练。

## 逐项工作量

令 A=B×H×Σ_t v_t，R=B×T×H，D=head_dim。

| 项 | FLOPs |
|---|---:|
| 前向 QK、PV | 各 2AD |
| 反向 dP、dQ、局部 dKV_key、局部 dKV_value | 各 2AD |
| 前向 scale、稳定 softmax | 4A+2R |
| 反向 softmax/sink 与 scale | 5A |
| dKV 两支路相加及逐槽 scatter-add | 2AD |
| sink 跨 query 归并 | H(BT−1) |

矩阵收缩均采用 2mnk，包括局部外积；不再另计矩阵归约。前向 softmax 每行 v+1 次减法、v 次求和、v+1 次除法，加 v 次 scale 乘法。exp 次数 A+R，max 比较 A，特殊调用不折算成 FLOPs。

反向 δ 每行 2v−1，ds 的 2v，dsink 的 1，scale 的 v，合计 5v。负号不计 FLOP。sink 归并按优化 reduce 的 BT−1 次加法；数值 helper 从零累加不是逐 Python 指令账。

所有工作只按有效逻辑槽位；源码 64-slot tile padding、head<16 wrapper padding、online softmax 的运行时顺序、实际 backward kernel 选择未估算。矩阵反向恰为四个矩阵不表示可以对其他推理模块统一乘固定倍数。

## 状态、bytes 与生命周期

声明 FP32 参考保存 Q、共享 KV、每有效槽概率、每 query/head 的 sink 概率，indices 用 int32。K/V 只保存一份，重复 ID 的概率仍按槽位分别保存。输出不是此 saved-P VJP 的必要保存量。

事件是 forward保存 → dP → softmax VJP → 四个局部矩阵梯度 → 两支路相加并scatter。dKV 先完整零初始化，然后每 head/有效槽按 FP32 read+write 更新：零初始化4BKD bytes，读写各4AD bytes。只是这项声明实现的数据操作，不是整算子的内存流量。模型源接口 BF16/FP32/int32 大小单列，不与参考 FP32 保存混同。

输入/参数所有权、输出/上游梯度、反向临时数组、workspace、allocator均不纳入保存子集；`actual_peak_bytes` 与实际 backward kernel 工作保持 unknown。

## 数值验收与接入

`public/src/infra_calc/topics/v4_attention_training.py` 正常依赖公共 sources/units；导出 calculate、reference、markdown。公共源码只读。portable 测试可以直接运行：

```sh
/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/research/v4-attention-training/public/tests -v
```

4 测试：双 query/head、重复 ID 的 Q/KV/sink FP64 自动微分；全部输入元素中心差分；padding 删除不改变输出而重复 ID 去重改变输出；单键 sink 的闭式梯度；计数/重放与非法输入。无 torch 时仅 autograd 用例显式跳过，数值验收要求实际环境 4pass/0skip。

下一步才接外围投影、RMSNorm、RoPE 和函数式 Compressor，再接 hc inner_vjp；当前不标完成完整 attention layer 或 V4 训练。
