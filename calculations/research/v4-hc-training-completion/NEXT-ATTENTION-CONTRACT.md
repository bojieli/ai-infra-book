# 下一有限计算契约：V4 tied-KV 稀疏注意力主损失 VJP

本条只规划下一项，不扩大此次 primitive+hc 合入范围。

固定原件：`sources/deepseek-v4-flash/inference/model.py:479-541` 和 `kernel.py:277-365`。源码令同一 KV 张量同时充当 key/value，sink 只进入 softmax 分母，索引可能含无效槽位。主损失对整数索引没有连续梯度，但这不消除被选 KV 的梯度，也不能代表 indexer 辅助训练目标不存在。

## 最小可验收输入

先单独完成一个 source-shaped sparse-attention core：Q[B,T,heads,d]、KV[B,K,d]、sink[heads]、indices[B,T,J]、scale，显式每个查询有效槽位。以小尺寸数值 fixture 验证；实际 V4 维度与 mask/selected slot 数量用于账。测试包含重复 ID、无效索引、一个有效位置、多个 heads 和共享 KV 归并。数值范围必须有至少一个有效键，避免把当前 kernel 的全无效数值边界擅自定义成另一实现。

数学式为 s_j=scale dot(q,kv_j)，分母 Z=Σ_j exp(s_j)+exp(sink)，p_j=exp(s_j)/Z，p_sink=exp(sink)/Z，o=Σ_j p_j kv_j。sink 是零 value 的额外分母项，不是额外可训练 value。

给定 g=do：

- dp_j=dot(g,kv_j)，δ=Σ_j p_j dp_j。
- ds_j=p_j(dp_j−δ)，dsink=−p_sink δ。
- dq=scale Σ_j ds_j kv_j。
- dkv_j=p_j g+scale ds_j q。

**同一 KV 的两项梯度必须相加，并对重复索引、查询与 head 做 scatter/reduction；不能返回两个独立 K/V 状态就认为完成。** 无效槽位不产生梯度。sink 梯度按 B/T 查询归并。

逐项列 QK/PV 的前后矩阵、softmax/sink 标量与特殊调用、gather/scatter 的整数及已知接口 bytes。采用明确的保存概率策略，保留重计算为另一路契约，不能直接取 inference FLOPs×3。

## 后续连接边界

core 通过后再接 Attention 外围 Wq_a、q_norm、Wq_b、逐 head RMS、RoPE、Wkv/kv_norm、inverse RoPE、grouped Wo_a/Wo_b。以 source start_pos=0 的无压缩窗口路径优先，免于先声称已处理原地缓存的训练历史。

压缩 ratio4/128 则必须先把 Compressor 的重叠窗口与状态更新写成可微函数式图。固定 top-k 的主损失参考不包含 indexer loss；必须继续保留该 objective 未实现字段。KV 非-RoPE 的 FP8 模拟转换需要明确训练 surrogate/量化策略；报告披露的专家 STE 不能无条件推广成所有 KV cast 的已证规则。

此后再与 hc 的 inner_vjp 接口组合；只有实际完成的子图进入累计账。完整层/模型训练、QAT 梯度实现与优化器仍各自独立验收。
