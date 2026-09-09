# qwen3-dense-forward — qwen3-8b

输入：`{"activation_bytes": 2, "batch": 1, "history": 8192, "kv_bytes": 2, "output_head": "last", "score_bytes": 4, "tokens": 1, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 8,190,735,360 |
| weight_resident_bytes | 16,381,470,720 |
| backbone_projection_ffn_flops | 13,891,534,848 |
| causal_attention_matrix_flops | 4,832,428,032 |
| rectangular_attention_matrix_flops | 4,832,428,032 |
| matrix_flops | 19,968,622,592 |
| scalar_flops | 42,304,425 |
| special_ops | `{"sin": 128, "cos": 128, "rsqrt": 1513, "negate": 534528, "exp": 9880704, "compare_max": 9437184, "mask_decisions": 9438336}` |
| weight_read_once_per_operator_bytes | 15,136,819,200 |
| activation_operand_read_bytes | 1,291,021,584 |
| activation_operand_write_bytes | 81,873,152 |
| kv_bytes_per_token_per_request | 147,456 |
| kv_resident_before_bytes | 1,207,959,552 |
| kv_resident_after_bytes | 1,208,107,008 |
| kv_new_write_bytes | 147,456 |
| kv_existing_history_unique_payload_bytes | 1,207,959,552 |
| kv_attention_unique_payload_bytes | 1,208,107,008 |
| kv_logical_query_head_operand_bytes | 4,832,428,032 |
| attention_score_tensor_per_layer_bytes | 1,048,704 |
| materialized_scores_probabilities_io_all_layers_bytes | 151,013,376 |
| minimum_required_weight_and_kv_bytes | 17,589,577,728 |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[1, 1]；table=[151936, 4096]；output=[1, 4096] | 0 | 0 | 8,192 | 8 | 8,192 |
| rope_table | 1 | frequencies=[1, 64]；cos_sin_each=[1, 128] | 0 | 64 | 0 | 264 | 512 |
| input_layernorm | 36 | input=[1, 4096]；weight=[4096]；output=[1, 4096] | 0 | 16,385 | 8,192 | 8,192 | 8,192 |
| q_proj | 36 | input=[1, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[1, 4096] | 33,554,432 | 0 | 33,554,432 | 8,192 | 8,192 |
| k_proj | 36 | input=[1, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[1, 1024] | 8,388,608 | 0 | 8,388,608 | 8,192 | 2,048 |
| v_proj | 36 | input=[1, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[1, 1024] | 8,388,608 | 0 | 8,388,608 | 8,192 | 2,048 |
| q_norm | 36 | input=[32, 128]；weight=[128]；output=[32, 128] | 0 | 16,416 | 256 | 8,192 | 8,192 |
| k_norm | 36 | input=[8, 128]；weight=[128]；output=[8, 128] | 0 | 4,104 | 256 | 2,048 | 2,048 |
| apply_rope | 36 | Q=[1, 32, 1, 128]；K=[1, 8, 1, 128] | 0 | 15,360 | 0 | 10,752 | 10,240 |
| kv_append | 36 | new_K_and_V_each=[1, 8, 1, 128] | 0 | 0 | 0 | 4,096 | 4,096 |
| qk | 36 | Q=[1, 32, 1, 128]；K_shared=[1, 8, 8193, 128]；scores_rectangular=[1, 32, 1, 8193] | 67,117,056 | 0 | 0 | 16,787,456 | 1,048,704 |
| score_scale_mask_softmax | 36 | scores=[1, 32, 1, 8193] | 0 | 1,048,672 | 0 | 1,048,704 | 1,048,704 |
| pv | 36 | P=[1, 32, 1, 8193]；V_shared=[1, 8, 8193, 128]；output=[1, 32, 1, 128] | 67,117,056 | 0 | 0 | 17,827,968 | 8,192 |
| o_proj | 36 | input=[1, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[1, 4096] | 33,554,432 | 0 | 33,554,432 | 8,192 | 8,192 |
| attention_residual | 36 | inputs_each=[1, 4096]；output=[1, 4096] | 0 | 4,096 | 0 | 16,384 | 8,192 |
| post_attention_layernorm | 36 | input=[1, 4096]；weight=[4096]；output=[1, 4096] | 0 | 16,385 | 8,192 | 8,192 | 8,192 |
| gate_proj | 36 | input=[1, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[1, 12288] | 100,663,296 | 0 | 100,663,296 | 8,192 | 24,576 |
| up_proj | 36 | input=[1, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[1, 12288] | 100,663,296 | 0 | 100,663,296 | 8,192 | 24,576 |
| silu_mul | 36 | gate=[1, 12288]；up=[1, 12288]；output=[1, 12288] | 0 | 49,152 | 0 | 49,152 | 24,576 |
| down_proj | 36 | input=[1, 12288]；weight_math=[12288, 4096]；weight_storage=[4096, 12288]；output=[1, 4096] | 100,663,296 | 0 | 100,663,296 | 24,576 | 8,192 |
| ffn_residual | 36 | inputs_each=[1, 4096]；output=[1, 4096] | 0 | 4,096 | 0 | 16,384 | 8,192 |
| final_norm | 1 | input=[1, 4096]；weight=[4096]；output=[1, 4096] | 0 | 16,385 | 8,192 | 8,192 | 8,192 |
| lm_head | 1 | input=[1, 4096]；weight_math=[4096, 151936]；weight_storage=[151936, 4096]；output=[1, 151936] | 1,244,659,712 | 0 | 1,244,659,712 | 8,192 | 303,872 |

计量条件：

- 所有请求等长、相同位置 ID、无跨请求前缀共享，无 TP/PP；dropout=0 推理。
- 全模型权重统一 weight_bytes 的教学格式；不由 torch_dtype 推断实际量化格式。
- 每行 operator 成本为一次出现，repeats 是层数；布局视图与 GQA repeat 不额外物化。
- FMA=2；matrix_flops 是有效因果矩阵工作，scalar_flops 是声明算法的普通算术；特殊函数另列。
- operator 读写是独立算子操作数载荷，分数／概率矩形物化；不是实测 HBM、不是全图流量下界。
- 标量行内中间量视为片上；矩形注意力同时报告，FlashAttention/tile/缓存流量由执行专题另算。
- 不计采样、tokenizer、kernel launch、分配器、KV 管理索引及后端工作区；不据此声称完整 token 时间。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
