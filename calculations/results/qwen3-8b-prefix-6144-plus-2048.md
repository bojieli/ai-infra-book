# qwen3-dense-forward — qwen3-8b

输入：`{"activation_bytes": 2, "batch": 1, "history": 6144, "kv_bytes": 2, "output_head": "last", "score_bytes": 4, "tokens": 2048, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 8,190,735,360 |
| weight_resident_bytes | 16,381,470,720 |
| backbone_projection_ffn_flops | 28,449,863,368,704 |
| causal_attention_matrix_flops | 8,659,258,048,512 |
| rectangular_attention_matrix_flops | 9,895,604,649,984 |
| matrix_flops | 37,110,366,076,928 |
| scalar_flops | 76,971,067,392 |
| special_ops | `{"sin": 262144, "cos": 262144, "rsqrt": 3098624, "negate": 1094713344, "exp": 17818583040, "compare_max": 16910254080, "mask_decisions": 19327352832}` |
| weight_read_once_per_operator_bytes | 15,153,588,224 |
| activation_operand_read_bytes | 170,980,843,776 |
| activation_operand_write_bytes | 167,035,314,944 |
| kv_bytes_per_token_per_request | 147,456 |
| kv_resident_before_bytes | 905,969,664 |
| kv_resident_after_bytes | 1,207,959,552 |
| kv_new_write_bytes | 301,989,888 |
| kv_existing_history_unique_payload_bytes | 905,969,664 |
| kv_attention_unique_payload_bytes | 1,207,959,552 |
| kv_logical_query_head_operand_bytes | 8,659,258,048,512 |
| attention_score_tensor_per_layer_bytes | 2,147,483,648 |
| materialized_scores_probabilities_io_all_layers_bytes | 309,237,645,312 |
| minimum_required_weight_and_kv_bytes | 17,589,430,272 |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[1, 2048]；table=[151936, 4096]；output=[2048, 4096] | 0 | 0 | 16,777,216 | 16,384 | 16,777,216 |
| rope_table | 1 | frequencies=[2048, 64]；cos_sin_each=[2048, 128] | 0 | 131,072 | 0 | 16,640 | 1,048,576 |
| input_layernorm | 36 | input=[2048, 4096]；weight=[4096]；output=[2048, 4096] | 0 | 33,556,480 | 8,192 | 16,777,216 | 16,777,216 |
| q_proj | 36 | input=[2048, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[2048, 4096] | 68,719,476,736 | 0 | 33,554,432 | 16,777,216 | 16,777,216 |
| k_proj | 36 | input=[2048, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[2048, 1024] | 17,179,869,184 | 0 | 8,388,608 | 16,777,216 | 4,194,304 |
| v_proj | 36 | input=[2048, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[2048, 1024] | 17,179,869,184 | 0 | 8,388,608 | 16,777,216 | 4,194,304 |
| q_norm | 36 | input=[65536, 128]；weight=[128]；output=[65536, 128] | 0 | 33,619,968 | 256 | 16,777,216 | 16,777,216 |
| k_norm | 36 | input=[16384, 128]；weight=[128]；output=[16384, 128] | 0 | 8,404,992 | 256 | 4,194,304 | 4,194,304 |
| apply_rope | 36 | Q=[1, 32, 2048, 128]；K=[1, 8, 2048, 128] | 0 | 31,457,280 | 0 | 22,020,096 | 20,971,520 |
| kv_append | 36 | new_K_and_V_each=[1, 8, 2048, 128] | 0 | 0 | 0 | 8,388,608 | 8,388,608 |
| qk | 36 | Q=[1, 32, 2048, 128]；K_shared=[1, 8, 8192, 128]；scores_rectangular=[1, 32, 2048, 8192] | 120,267,472,896 | 0 | 0 | 33,554,432 | 2,147,483,648 |
| score_scale_mask_softmax | 36 | scores=[1, 32, 2048, 8192] | 0 | 1,879,113,728 | 0 | 2,147,483,648 | 2,147,483,648 |
| pv | 36 | P=[1, 32, 2048, 8192]；V_shared=[1, 8, 8192, 128]；output=[1, 32, 2048, 128] | 120,267,472,896 | 0 | 0 | 2,164,260,864 | 16,777,216 |
| o_proj | 36 | input=[2048, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[2048, 4096] | 68,719,476,736 | 0 | 33,554,432 | 16,777,216 | 16,777,216 |
| attention_residual | 36 | inputs_each=[2048, 4096]；output=[2048, 4096] | 0 | 8,388,608 | 0 | 33,554,432 | 16,777,216 |
| post_attention_layernorm | 36 | input=[2048, 4096]；weight=[4096]；output=[2048, 4096] | 0 | 33,556,480 | 8,192 | 16,777,216 | 16,777,216 |
| gate_proj | 36 | input=[2048, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[2048, 12288] | 206,158,430,208 | 0 | 100,663,296 | 16,777,216 | 50,331,648 |
| up_proj | 36 | input=[2048, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[2048, 12288] | 206,158,430,208 | 0 | 100,663,296 | 16,777,216 | 50,331,648 |
| silu_mul | 36 | gate=[2048, 12288]；up=[2048, 12288]；output=[2048, 12288] | 0 | 100,663,296 | 0 | 100,663,296 | 50,331,648 |
| down_proj | 36 | input=[2048, 12288]；weight_math=[12288, 4096]；weight_storage=[4096, 12288]；output=[2048, 4096] | 206,158,430,208 | 0 | 100,663,296 | 50,331,648 | 16,777,216 |
| ffn_residual | 36 | inputs_each=[2048, 4096]；output=[2048, 4096] | 0 | 8,388,608 | 0 | 33,554,432 | 16,777,216 |
| final_norm | 1 | input=[2048, 4096]；weight=[4096]；output=[2048, 4096] | 0 | 33,556,480 | 8,192 | 16,777,216 | 16,777,216 |
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
