# qwen3-dense-forward — qwen3-8b

输入：`{"activation_bytes": 2, "batch": 64, "history": 8192, "kv_bytes": 2, "output_head": "last", "score_bytes": 4, "tokens": 1, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 8,190,735,360 |
| weight_resident_bytes | 16,381,470,720 |
| backbone_projection_ffn_flops | 889,058,230,272 |
| causal_attention_matrix_flops | 309,275,394,048 |
| rectangular_attention_matrix_flops | 309,275,394,048 |
| matrix_flops | 1,277,991,845,888 |
| scalar_flops | 2,707,479,168 |
| special_ops | `{"sin": 128, "cos": 128, "rsqrt": 96832, "negate": 34209792, "exp": 632365056, "compare_max": 603979776, "mask_decisions": 604053504}` |
| weight_read_once_per_operator_bytes | 15,137,335,296 |
| activation_operand_read_bytes | 82,624,203,528 |
| activation_operand_write_bytes | 5,239,849,472 |
| kv_bytes_per_token_per_request | 147,456 |
| kv_resident_before_bytes | 77,309,411,328 |
| kv_resident_after_bytes | 77,318,848,512 |
| kv_new_write_bytes | 9,437,184 |
| kv_existing_history_unique_payload_bytes | 77,309,411,328 |
| kv_attention_unique_payload_bytes | 77,318,848,512 |
| kv_logical_query_head_operand_bytes | 309,275,394,048 |
| attention_score_tensor_per_layer_bytes | 67,117,056 |
| materialized_scores_probabilities_io_all_layers_bytes | 9,664,856,064 |
| minimum_required_weight_and_kv_bytes | 93,700,319,232 |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[64, 1]；table=[151936, 4096]；output=[64, 4096] | 0 | 0 | 524,288 | 512 | 524,288 |
| rope_table | 1 | frequencies=[1, 64]；cos_sin_each=[1, 128] | 0 | 64 | 0 | 264 | 512 |
| input_layernorm | 36 | input=[64, 4096]；weight=[4096]；output=[64, 4096] | 0 | 1,048,640 | 8,192 | 524,288 | 524,288 |
| q_proj | 36 | input=[64, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[64, 4096] | 2,147,483,648 | 0 | 33,554,432 | 524,288 | 524,288 |
| k_proj | 36 | input=[64, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[64, 1024] | 536,870,912 | 0 | 8,388,608 | 524,288 | 131,072 |
| v_proj | 36 | input=[64, 4096]；weight_math=[4096, 1024]；weight_storage=[1024, 4096]；output=[64, 1024] | 536,870,912 | 0 | 8,388,608 | 524,288 | 131,072 |
| q_norm | 36 | input=[2048, 128]；weight=[128]；output=[2048, 128] | 0 | 1,050,624 | 256 | 524,288 | 524,288 |
| k_norm | 36 | input=[512, 128]；weight=[128]；output=[512, 128] | 0 | 262,656 | 256 | 131,072 | 131,072 |
| apply_rope | 36 | Q=[64, 32, 1, 128]；K=[64, 8, 1, 128] | 0 | 983,040 | 0 | 655,872 | 655,360 |
| kv_append | 36 | new_K_and_V_each=[64, 8, 1, 128] | 0 | 0 | 0 | 262,144 | 262,144 |
| qk | 36 | Q=[64, 32, 1, 128]；K_shared=[64, 8, 8193, 128]；scores_rectangular=[64, 32, 1, 8193] | 4,295,491,584 | 0 | 0 | 1,074,397,184 | 67,117,056 |
| score_scale_mask_softmax | 36 | scores=[64, 32, 1, 8193] | 0 | 67,115,008 | 0 | 67,117,056 | 67,117,056 |
| pv | 36 | P=[64, 32, 1, 8193]；V_shared=[64, 8, 8193, 128]；output=[64, 32, 1, 128] | 4,295,491,584 | 0 | 0 | 1,140,989,952 | 524,288 |
| o_proj | 36 | input=[64, 4096]；weight_math=[4096, 4096]；weight_storage=[4096, 4096]；output=[64, 4096] | 2,147,483,648 | 0 | 33,554,432 | 524,288 | 524,288 |
| attention_residual | 36 | inputs_each=[64, 4096]；output=[64, 4096] | 0 | 262,144 | 0 | 1,048,576 | 524,288 |
| post_attention_layernorm | 36 | input=[64, 4096]；weight=[4096]；output=[64, 4096] | 0 | 1,048,640 | 8,192 | 524,288 | 524,288 |
| gate_proj | 36 | input=[64, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[64, 12288] | 6,442,450,944 | 0 | 100,663,296 | 524,288 | 1,572,864 |
| up_proj | 36 | input=[64, 4096]；weight_math=[4096, 12288]；weight_storage=[12288, 4096]；output=[64, 12288] | 6,442,450,944 | 0 | 100,663,296 | 524,288 | 1,572,864 |
| silu_mul | 36 | gate=[64, 12288]；up=[64, 12288]；output=[64, 12288] | 0 | 3,145,728 | 0 | 3,145,728 | 1,572,864 |
| down_proj | 36 | input=[64, 12288]；weight_math=[12288, 4096]；weight_storage=[4096, 12288]；output=[64, 4096] | 6,442,450,944 | 0 | 100,663,296 | 1,572,864 | 524,288 |
| ffn_residual | 36 | inputs_each=[64, 4096]；output=[64, 4096] | 0 | 262,144 | 0 | 1,048,576 | 524,288 |
| final_norm | 1 | input=[64, 4096]；weight=[4096]；output=[64, 4096] | 0 | 1,048,640 | 8,192 | 524,288 | 524,288 |
| lm_head | 1 | input=[64, 4096]；weight_math=[4096, 151936]；weight_storage=[151936, 4096]；output=[64, 151936] | 79,658,221,568 | 0 | 1,244,659,712 | 524,288 | 19,447,808 |

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
