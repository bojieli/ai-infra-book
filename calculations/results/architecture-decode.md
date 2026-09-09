# 官方基线与声明架构变体

只有基线是已发布checkpoint；其余结构未训练，不假定质量相同。严格等参以实际标志和差额判定。

输入：`{"batch": 1, "history": 8192, "tokens": 1, "tp": 2, "capacity_bytes": 24000000000, "workspace_bytes": 2147483648, "ffn_alignment": 128}`

| 结构 | L/H/FFN/KV头 | 参数 | 差额 | 严格等参 | 矩阵FLOPs | KV bytes/token | 每rank预算占用bytes |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| baseline | 36/4096/12288/8 | 8190735360 | 0 | True | 19968622592 | 147456 | 10942580736 |
| shallower_same_width | 24/4096/20096/8 | 8178051072 | -12684288 | False | 18332647424 | 98304 | 10728443904 |
| deeper_same_width | 48/4096/8320/8 | 8165670912 | -25064448 | False | 21529100288 | 196608 | 11118968832 |
| narrower_same_depth | 36/3072/19328/6 | 8195641344 | 4905984 | False | 19081641984 | 110592 | 10796398592 |
| shallower_wider | 24/5120/13952/8 | 8209296384 | 18561024 | False | 18889277440 | 98304 | 10759739392 |
| less_kv_more_ffn_budget_match | 36/4096/12800/2 | 8190735360 | 0 | True | 19968622592 | 36864 | 10489540608 |

## baseline

工作与TP预算：`{"matrix_flops": 19968622592, "scalar_flops": 42304425, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 147456, "per_rank_kv_bytes": 604053504, "per_rank_old_history_read_bytes": 603979776, "per_rank_kv_append_bytes": 73728, "per_rank_new_kv_request_bytes": 604053504, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10942580736, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 22, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 8192, "per_rank_ring_wire_bytes_exact": "589824", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 4096], "output": [1, 4096]}` | 1 | 0/0 | 8192/8/8192 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 36 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 36 | 33554432/0 | 33554432/8192/8192 | `{}` |
| k_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 36 | 8388608/0 | 8388608/8192/2048 | `{}` |
| v_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 36 | 8388608/0 | 8388608/8192/2048 | `{}` |
| q_norm | `{"input": [32, 128], "weight": [128], "output": [32, 128]}` | 36 | 0/16416 | 256/8192/8192 | `{"rsqrt": 32}` |
| k_norm | `{"input": [8, 128], "weight": [128], "output": [8, 128]}` | 36 | 0/4104 | 256/2048/2048 | `{"rsqrt": 8}` |
| apply_rope | `{"Q": [1, 32, 1, 128], "K": [1, 8, 1, 128]}` | 36 | 0/15360 | 0/10752/10240 | `{"negate": 2560}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 1, 128]}` | 36 | 0/0 | 0/4096/4096 | `{}` |
| qk | `{"Q": [1, 32, 1, 128], "K_shared": [1, 8, 8193, 128], "scores_rectangular": [1, 32, 1, 8193]}` | 36 | 67117056/0 | 0/16787456/1048704 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 1, 8193]}` | 36 | 0/1048672 | 0/1048704/1048704 | `{"exp": 262176, "compare_max": 262144, "mask_decisions": 262176}` |
| pv | `{"P": [1, 32, 1, 8193], "V_shared": [1, 8, 8193, 128], "output": [1, 32, 1, 128]}` | 36 | 67117056/0 | 0/17827968/8192 | `{}` |
| o_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 36 | 33554432/0 | 33554432/8192/8192 | `{}` |
| attention_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 36 | 0/4096 | 0/16384/8192 | `{}` |
| post_attention_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 36 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [1, 12288]}` | 36 | 100663296/0 | 100663296/8192/24576 | `{}` |
| up_proj | `{"input": [1, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [1, 12288]}` | 36 | 100663296/0 | 100663296/8192/24576 | `{}` |
| silu_mul | `{"gate": [1, 12288], "up": [1, 12288], "output": [1, 12288]}` | 36 | 0/49152 | 0/49152/24576 | `{"exp": 12288, "negate": 12288}` |
| down_proj | `{"input": [1, 12288], "weight_math": [12288, 4096], "weight_storage": [4096, 12288], "output": [1, 4096]}` | 36 | 100663296/0 | 100663296/24576/8192 | `{}` |
| ffn_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 36 | 0/4096 | 0/16384/8192 | `{}` |
| final_norm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 1 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## shallower_same_width

工作与TP预算：`{"matrix_flops": 18332647424, "scalar_flops": 28958001, "all_unique_weight_bytes": 16356102144, "per_rank_weight_bytes": 8178257920, "aggregate_tp_weight_bytes": 16356515840, "norm_replication_extra_bytes": 413696, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402702336, "per_rank_old_history_read_bytes": 402653184, "per_rank_kv_append_bytes": 49152, "per_rank_new_kv_request_bytes": 402702336, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10728443904, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 8192, "per_rank_ring_wire_bytes_exact": "393216", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 4096], "output": [1, 4096]}` | 1 | 0/0 | 8192/8/8192 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 24 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 24 | 33554432/0 | 33554432/8192/8192 | `{}` |
| k_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 24 | 8388608/0 | 8388608/8192/2048 | `{}` |
| v_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 24 | 8388608/0 | 8388608/8192/2048 | `{}` |
| q_norm | `{"input": [32, 128], "weight": [128], "output": [32, 128]}` | 24 | 0/16416 | 256/8192/8192 | `{"rsqrt": 32}` |
| k_norm | `{"input": [8, 128], "weight": [128], "output": [8, 128]}` | 24 | 0/4104 | 256/2048/2048 | `{"rsqrt": 8}` |
| apply_rope | `{"Q": [1, 32, 1, 128], "K": [1, 8, 1, 128]}` | 24 | 0/15360 | 0/10752/10240 | `{"negate": 2560}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 1, 128]}` | 24 | 0/0 | 0/4096/4096 | `{}` |
| qk | `{"Q": [1, 32, 1, 128], "K_shared": [1, 8, 8193, 128], "scores_rectangular": [1, 32, 1, 8193]}` | 24 | 67117056/0 | 0/16787456/1048704 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 1, 8193]}` | 24 | 0/1048672 | 0/1048704/1048704 | `{"exp": 262176, "compare_max": 262144, "mask_decisions": 262176}` |
| pv | `{"P": [1, 32, 1, 8193], "V_shared": [1, 8, 8193, 128], "output": [1, 32, 1, 128]}` | 24 | 67117056/0 | 0/17827968/8192 | `{}` |
| o_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 24 | 33554432/0 | 33554432/8192/8192 | `{}` |
| attention_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 24 | 0/4096 | 0/16384/8192 | `{}` |
| post_attention_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 24 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [1, 20096]}` | 24 | 164626432/0 | 164626432/8192/40192 | `{}` |
| up_proj | `{"input": [1, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [1, 20096]}` | 24 | 164626432/0 | 164626432/8192/40192 | `{}` |
| silu_mul | `{"gate": [1, 20096], "up": [1, 20096], "output": [1, 20096]}` | 24 | 0/80384 | 0/80384/40192 | `{"exp": 20096, "negate": 20096}` |
| down_proj | `{"input": [1, 20096], "weight_math": [20096, 4096], "weight_storage": [4096, 20096], "output": [1, 4096]}` | 24 | 164626432/0 | 164626432/40192/8192 | `{}` |
| ffn_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 24 | 0/4096 | 0/16384/8192 | `{}` |
| final_norm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 1 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## deeper_same_width

工作与TP预算：`{"matrix_flops": 21529100288, "scalar_flops": 55638561, "all_unique_weight_bytes": 16331341824, "per_rank_weight_bytes": 8166080512, "aggregate_tp_weight_bytes": 16332161024, "norm_replication_extra_bytes": 819200, "kv_bytes_per_token_per_request": 196608, "per_rank_kv_bytes": 805404672, "per_rank_old_history_read_bytes": 805306368, "per_rank_kv_append_bytes": 98304, "per_rank_new_kv_request_bytes": 805404672, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 11118968832, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 16, "batch_fits": true, "sequential_decoder_layers": 48, "sequential_collectives": 96, "per_collective_activation_payload_bytes": 8192, "per_rank_ring_wire_bytes_exact": "786432", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 4096], "output": [1, 4096]}` | 1 | 0/0 | 8192/8/8192 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 48 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 48 | 33554432/0 | 33554432/8192/8192 | `{}` |
| k_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 48 | 8388608/0 | 8388608/8192/2048 | `{}` |
| v_proj | `{"input": [1, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [1, 1024]}` | 48 | 8388608/0 | 8388608/8192/2048 | `{}` |
| q_norm | `{"input": [32, 128], "weight": [128], "output": [32, 128]}` | 48 | 0/16416 | 256/8192/8192 | `{"rsqrt": 32}` |
| k_norm | `{"input": [8, 128], "weight": [128], "output": [8, 128]}` | 48 | 0/4104 | 256/2048/2048 | `{"rsqrt": 8}` |
| apply_rope | `{"Q": [1, 32, 1, 128], "K": [1, 8, 1, 128]}` | 48 | 0/15360 | 0/10752/10240 | `{"negate": 2560}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 1, 128]}` | 48 | 0/0 | 0/4096/4096 | `{}` |
| qk | `{"Q": [1, 32, 1, 128], "K_shared": [1, 8, 8193, 128], "scores_rectangular": [1, 32, 1, 8193]}` | 48 | 67117056/0 | 0/16787456/1048704 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 1, 8193]}` | 48 | 0/1048672 | 0/1048704/1048704 | `{"exp": 262176, "compare_max": 262144, "mask_decisions": 262176}` |
| pv | `{"P": [1, 32, 1, 8193], "V_shared": [1, 8, 8193, 128], "output": [1, 32, 1, 128]}` | 48 | 67117056/0 | 0/17827968/8192 | `{}` |
| o_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 48 | 33554432/0 | 33554432/8192/8192 | `{}` |
| attention_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 48 | 0/4096 | 0/16384/8192 | `{}` |
| post_attention_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 48 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [1, 8320]}` | 48 | 68157440/0 | 68157440/8192/16640 | `{}` |
| up_proj | `{"input": [1, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [1, 8320]}` | 48 | 68157440/0 | 68157440/8192/16640 | `{}` |
| silu_mul | `{"gate": [1, 8320], "up": [1, 8320], "output": [1, 8320]}` | 48 | 0/33280 | 0/33280/16640 | `{"exp": 8320, "negate": 8320}` |
| down_proj | `{"input": [1, 8320], "weight_math": [8320, 4096], "weight_storage": [4096, 8320], "output": [1, 4096]}` | 48 | 68157440/0 | 68157440/16640/8192 | `{}` |
| ffn_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 48 | 0/4096 | 0/16384/8192 | `{}` |
| final_norm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 1 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## narrower_same_depth

工作与TP预算：`{"matrix_flops": 19081641984, "scalar_flops": 33184481, "all_unique_weight_bytes": 16391282688, "per_rank_weight_bytes": 8195874816, "aggregate_tp_weight_bytes": 16391749632, "norm_replication_extra_bytes": 466944, "kv_bytes_per_token_per_request": 110592, "per_rank_kv_bytes": 453040128, "per_rank_old_history_read_bytes": 452984832, "per_rank_kv_append_bytes": 55296, "per_rank_new_kv_request_bytes": 453040128, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10796398592, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 30, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 6144, "per_rank_ring_wire_bytes_exact": "442368", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 3072], "output": [1, 3072]}` | 1 | 0/0 | 6144/8/6144 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 3072], "weight": [3072], "output": [1, 3072]}` | 36 | 0/12289 | 6144/6144/6144 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [1, 3072]}` | 36 | 18874368/0 | 18874368/6144/6144 | `{}` |
| k_proj | `{"input": [1, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [1, 768]}` | 36 | 4718592/0 | 4718592/6144/1536 | `{}` |
| v_proj | `{"input": [1, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [1, 768]}` | 36 | 4718592/0 | 4718592/6144/1536 | `{}` |
| q_norm | `{"input": [24, 128], "weight": [128], "output": [24, 128]}` | 36 | 0/12312 | 256/6144/6144 | `{"rsqrt": 24}` |
| k_norm | `{"input": [6, 128], "weight": [128], "output": [6, 128]}` | 36 | 0/3078 | 256/1536/1536 | `{"rsqrt": 6}` |
| apply_rope | `{"Q": [1, 24, 1, 128], "K": [1, 6, 1, 128]}` | 36 | 0/11520 | 0/8192/7680 | `{"negate": 1920}` |
| kv_append | `{"new_K_and_V_each": [1, 6, 1, 128]}` | 36 | 0/0 | 0/3072/3072 | `{}` |
| qk | `{"Q": [1, 24, 1, 128], "K_shared": [1, 6, 8193, 128], "scores_rectangular": [1, 24, 1, 8193]}` | 36 | 50337792/0 | 0/12590592/786528 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 24, 1, 8193]}` | 36 | 0/786504 | 0/786528/786528 | `{"exp": 196632, "compare_max": 196608, "mask_decisions": 196632}` |
| pv | `{"P": [1, 24, 1, 8193], "V_shared": [1, 6, 8193, 128], "output": [1, 24, 1, 128]}` | 36 | 50337792/0 | 0/13370976/6144 | `{}` |
| o_proj | `{"input": [1, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [1, 3072]}` | 36 | 18874368/0 | 18874368/6144/6144 | `{}` |
| attention_residual | `{"inputs_each": [1, 3072], "output": [1, 3072]}` | 36 | 0/3072 | 0/12288/6144 | `{}` |
| post_attention_layernorm | `{"input": [1, 3072], "weight": [3072], "output": [1, 3072]}` | 36 | 0/12289 | 6144/6144/6144 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [1, 19328]}` | 36 | 118751232/0 | 118751232/6144/38656 | `{}` |
| up_proj | `{"input": [1, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [1, 19328]}` | 36 | 118751232/0 | 118751232/6144/38656 | `{}` |
| silu_mul | `{"gate": [1, 19328], "up": [1, 19328], "output": [1, 19328]}` | 36 | 0/77312 | 0/77312/38656 | `{"exp": 19328, "negate": 19328}` |
| down_proj | `{"input": [1, 19328], "weight_math": [19328, 3072], "weight_storage": [3072, 19328], "output": [1, 3072]}` | 36 | 118751232/0 | 118751232/38656/6144 | `{}` |
| ffn_residual | `{"inputs_each": [1, 3072], "output": [1, 3072]}` | 36 | 0/3072 | 0/12288/6144 | `{}` |
| final_norm | `{"input": [1, 3072], "weight": [3072], "output": [1, 3072]}` | 1 | 0/12289 | 6144/6144/6144 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 3072], "weight_math": [3072, 151936], "weight_storage": [151936, 3072], "output": [1, 151936]}` | 1 | 933494784/0 | 933494784/6144/303872 | `{}` |

## shallower_wider

工作与TP预算：`{"matrix_flops": 18889277440, "scalar_flops": 35082289, "all_unique_weight_bytes": 16418592768, "per_rank_weight_bytes": 8209553408, "aggregate_tp_weight_bytes": 16419106816, "norm_replication_extra_bytes": 514048, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402702336, "per_rank_old_history_read_bytes": 402653184, "per_rank_kv_append_bytes": 49152, "per_rank_new_kv_request_bytes": 402702336, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10759739392, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 10240, "per_rank_ring_wire_bytes_exact": "491520", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 5120], "output": [1, 5120]}` | 1 | 0/0 | 10240/8/10240 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 5120], "weight": [5120], "output": [1, 5120]}` | 24 | 0/20481 | 10240/10240/10240 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [1, 5120]}` | 24 | 52428800/0 | 52428800/10240/10240 | `{}` |
| k_proj | `{"input": [1, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [1, 1024]}` | 24 | 10485760/0 | 10485760/10240/2048 | `{}` |
| v_proj | `{"input": [1, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [1, 1024]}` | 24 | 10485760/0 | 10485760/10240/2048 | `{}` |
| q_norm | `{"input": [40, 128], "weight": [128], "output": [40, 128]}` | 24 | 0/20520 | 256/10240/10240 | `{"rsqrt": 40}` |
| k_norm | `{"input": [8, 128], "weight": [128], "output": [8, 128]}` | 24 | 0/4104 | 256/2048/2048 | `{"rsqrt": 8}` |
| apply_rope | `{"Q": [1, 40, 1, 128], "K": [1, 8, 1, 128]}` | 24 | 0/18432 | 0/12800/12288 | `{"negate": 3072}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 1, 128]}` | 24 | 0/0 | 0/4096/4096 | `{}` |
| qk | `{"Q": [1, 40, 1, 128], "K_shared": [1, 8, 8193, 128], "scores_rectangular": [1, 40, 1, 8193]}` | 24 | 83896320/0 | 0/16789504/1310880 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 40, 1, 8193]}` | 24 | 0/1310840 | 0/1310880/1310880 | `{"exp": 327720, "compare_max": 327680, "mask_decisions": 327720}` |
| pv | `{"P": [1, 40, 1, 8193], "V_shared": [1, 8, 8193, 128], "output": [1, 40, 1, 128]}` | 24 | 83896320/0 | 0/18090144/10240 | `{}` |
| o_proj | `{"input": [1, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [1, 5120]}` | 24 | 52428800/0 | 52428800/10240/10240 | `{}` |
| attention_residual | `{"inputs_each": [1, 5120], "output": [1, 5120]}` | 24 | 0/5120 | 0/20480/10240 | `{}` |
| post_attention_layernorm | `{"input": [1, 5120], "weight": [5120], "output": [1, 5120]}` | 24 | 0/20481 | 10240/10240/10240 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [1, 13952]}` | 24 | 142868480/0 | 142868480/10240/27904 | `{}` |
| up_proj | `{"input": [1, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [1, 13952]}` | 24 | 142868480/0 | 142868480/10240/27904 | `{}` |
| silu_mul | `{"gate": [1, 13952], "up": [1, 13952], "output": [1, 13952]}` | 24 | 0/55808 | 0/55808/27904 | `{"exp": 13952, "negate": 13952}` |
| down_proj | `{"input": [1, 13952], "weight_math": [13952, 5120], "weight_storage": [5120, 13952], "output": [1, 5120]}` | 24 | 142868480/0 | 142868480/27904/10240 | `{}` |
| ffn_residual | `{"inputs_each": [1, 5120], "output": [1, 5120]}` | 24 | 0/5120 | 0/20480/10240 | `{}` |
| final_norm | `{"input": [1, 5120], "weight": [5120], "output": [1, 5120]}` | 1 | 0/20481 | 10240/10240/10240 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 5120], "weight_math": [5120, 151936], "weight_storage": [151936, 5120], "output": [1, 151936]}` | 1 | 1555824640/0 | 1555824640/10240/303872 | `{}` |

## less_kv_more_ffn_budget_match

工作与TP预算：`{"matrix_flops": 19968622592, "scalar_flops": 42184401, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 36864, "per_rank_kv_bytes": 151013376, "per_rank_old_history_read_bytes": 150994944, "per_rank_kv_append_bytes": 18432, "per_rank_new_kv_request_bytes": 151013376, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10489540608, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 90, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 8192, "per_rank_ring_wire_bytes_exact": "589824", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 1], "table": [151936, 4096], "output": [1, 4096]}` | 1 | 0/0 | 8192/8/8192 | `{}` |
| rope_table | `{"frequencies": [1, 64], "cos_sin_each": [1, 128]}` | 1 | 0/64 | 0/264/512 | `{"sin": 128, "cos": 128}` |
| input_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 36 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| q_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 36 | 33554432/0 | 33554432/8192/8192 | `{}` |
| k_proj | `{"input": [1, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [1, 256]}` | 36 | 2097152/0 | 2097152/8192/512 | `{}` |
| v_proj | `{"input": [1, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [1, 256]}` | 36 | 2097152/0 | 2097152/8192/512 | `{}` |
| q_norm | `{"input": [32, 128], "weight": [128], "output": [32, 128]}` | 36 | 0/16416 | 256/8192/8192 | `{"rsqrt": 32}` |
| k_norm | `{"input": [2, 128], "weight": [128], "output": [2, 128]}` | 36 | 0/1026 | 256/512/512 | `{"rsqrt": 2}` |
| apply_rope | `{"Q": [1, 32, 1, 128], "K": [1, 2, 1, 128]}` | 36 | 0/13056 | 0/9216/8704 | `{"negate": 2176}` |
| kv_append | `{"new_K_and_V_each": [1, 2, 1, 128]}` | 36 | 0/0 | 0/1024/1024 | `{}` |
| qk | `{"Q": [1, 32, 1, 128], "K_shared": [1, 2, 8193, 128], "scores_rectangular": [1, 32, 1, 8193]}` | 36 | 67117056/0 | 0/4203008/1048704 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 1, 8193]}` | 36 | 0/1048672 | 0/1048704/1048704 | `{"exp": 262176, "compare_max": 262144, "mask_decisions": 262176}` |
| pv | `{"P": [1, 32, 1, 8193], "V_shared": [1, 2, 8193, 128], "output": [1, 32, 1, 128]}` | 36 | 67117056/0 | 0/5243520/8192 | `{}` |
| o_proj | `{"input": [1, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [1, 4096]}` | 36 | 33554432/0 | 33554432/8192/8192 | `{}` |
| attention_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 36 | 0/4096 | 0/16384/8192 | `{}` |
| post_attention_layernorm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 36 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| gate_proj | `{"input": [1, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [1, 12800]}` | 36 | 104857600/0 | 104857600/8192/25600 | `{}` |
| up_proj | `{"input": [1, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [1, 12800]}` | 36 | 104857600/0 | 104857600/8192/25600 | `{}` |
| silu_mul | `{"gate": [1, 12800], "up": [1, 12800], "output": [1, 12800]}` | 36 | 0/51200 | 0/51200/25600 | `{"exp": 12800, "negate": 12800}` |
| down_proj | `{"input": [1, 12800], "weight_math": [12800, 4096], "weight_storage": [4096, 12800], "output": [1, 4096]}` | 36 | 104857600/0 | 104857600/25600/8192 | `{}` |
| ffn_residual | `{"inputs_each": [1, 4096], "output": [1, 4096]}` | 36 | 0/4096 | 0/16384/8192 | `{}` |
| final_norm | `{"input": [1, 4096], "weight": [4096], "output": [1, 4096]}` | 1 | 0/16385 | 8192/8192/8192 | `{"rsqrt": 1}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## 容量与通信切换条件

容量区间含两端；通信只覆盖声明的两类decoder collective，不代表完整请求时间。
- `{"variant": "shallower_same_width", "matrix_flops_delta": -1635975168, "per_rank_weights_delta": -12785664, "per_rank_kv_delta": -201351168, "per_rank_live_budget_delta": -214136832, "capacity_interval_where_only_smaller_fits_bytes": [10728443904, 10942580735], "per_rank_ring_wire_delta_exact": "-196608", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "deeper_same_width", "matrix_flops_delta": 1560477696, "per_rank_weights_delta": -24963072, "per_rank_kv_delta": 201351168, "per_rank_live_budget_delta": 176388096, "capacity_interval_where_only_smaller_fits_bytes": [10942580736, 11118968831], "per_rank_ring_wire_delta_exact": "196608", "sequential_collectives_delta": 24, "sequential_layers_delta": 12}`
- `{"variant": "narrower_same_depth", "matrix_flops_delta": -886980608, "per_rank_weights_delta": 4831232, "per_rank_kv_delta": -151013376, "per_rank_live_budget_delta": -146182144, "capacity_interval_where_only_smaller_fits_bytes": [10796398592, 10942580735], "per_rank_ring_wire_delta_exact": "-147456", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`
- `{"variant": "shallower_wider", "matrix_flops_delta": -1079345152, "per_rank_weights_delta": 18509824, "per_rank_kv_delta": -201351168, "per_rank_live_budget_delta": -182841344, "capacity_interval_where_only_smaller_fits_bytes": [10759739392, 10942580735], "per_rank_ring_wire_delta_exact": "-98304", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "less_kv_more_ffn_budget_match", "matrix_flops_delta": 0, "per_rank_weights_delta": 0, "per_rank_kv_delta": -453040128, "per_rank_live_budget_delta": -453040128, "capacity_interval_where_only_smaller_fits_bytes": [10489540608, 10942580735], "per_rank_ring_wire_delta_exact": "0", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`

## 范围

- Only baseline is a released checkpoint. Variants are declared untrained architectures; no equal quality or numerical equivalence is asserted.
- Untied embedding/head, no biases, fixed head_dim=128, vocabulary/context and Q/K norms retained from official Qwen3-8B config.
- FFN is nearest positive aligned solution to the same parameter target; exact signed error and half-grid bound are reported. Exact equality depends on alignment; use the reported exact_equal_parameters flag.
- FMA=2, effective causal attention and source logical scalar counts. Operator reads/writes are semantic operands, not measured HBM.
- BF16 weights/activations/KV; score and scalar intermediate precision remains Scenario contract. No low-bit checkpoint claim.
- TP uses complete divisible KV heads; normalization parameters replicate. Uniform equal-length requests, no prefix sharing, no PP/EP. Workspace is a fixed per-rank input budget, not a derived peak.
- Ring bytes and sequential collectives quantify only two decoder collectives per layer. For that subpath declared service is bytes/effective_link_rate + collectives/startup_rate; no hardware rates are invented or whole-request latency inferred.
- Capacity flip interval is inclusive and applies to the declared batch and workspace. Matrix FLOPs, serial depth and communication changes cannot establish a quality-constrained winner alone.

## 固定基线来源

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json) SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json) SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py) SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py) SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`
