# 官方基线与声明架构变体

只有基线是已发布checkpoint；其余结构未训练，不假定质量相同。严格等参以实际标志和差额判定。

输入：`{"batch": 1, "history": 6144, "tokens": 2048, "tp": 2, "capacity_bytes": 24000000000, "workspace_bytes": 2147483648, "ffn_alignment": 128}`

| 结构 | L/H/FFN/KV头 | 参数 | 差额 | 严格等参 | 矩阵FLOPs | KV bytes/token | 每rank预算占用bytes |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| baseline | 36/4096/12288/8 | 8190735360 | 0 | True | 37110366076928 | 147456 | 10942507008 |
| shallower_same_width | 24/4096/20096/8 | 8178051072 | -12684288 | False | 34172407119872 | 98304 | 10728394752 |
| deeper_same_width | 48/4096/8320/8 | 8165670912 | -25064448 | False | 39893706211328 | 196608 | 11118870528 |
| narrower_same_depth | 36/3072/19328/6 | 8195641344 | 4905984 | False | 36240173039616 | 110592 | 10796343296 |
| shallower_wider | 24/5120/13952/8 | 8209296384 | 18561024 | False | 34469171691520 | 98304 | 10759690240 |
| less_kv_more_ffn_budget_match | 36/4096/12800/2 | 8190735360 | 0 | True | 37110366076928 | 36864 | 10489522176 |

## baseline

工作与TP预算：`{"matrix_flops": 37110366076928, "scalar_flops": 76971067392, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 147456, "per_rank_kv_bytes": 603979776, "per_rank_old_history_read_bytes": 452984832, "per_rank_kv_append_bytes": 150994944, "per_rank_new_kv_request_bytes": 603979776, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10942507008, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 22, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 16777216, "per_rank_ring_wire_bytes_exact": "1207959552", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 4096], "output": [2048, 4096]}` | 1 | 0/0 | 16777216/16384/16777216 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 36 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 36 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| k_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 36 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| v_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 36 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| q_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 36 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| k_norm | `{"input": [16384, 128], "weight": [128], "output": [16384, 128]}` | 36 | 0/8404992 | 256/4194304/4194304 | `{"rsqrt": 16384}` |
| apply_rope | `{"Q": [1, 32, 2048, 128], "K": [1, 8, 2048, 128]}` | 36 | 0/31457280 | 0/22020096/20971520 | `{"negate": 5242880}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 2048, 128]}` | 36 | 0/0 | 0/8388608/8388608 | `{}` |
| qk | `{"Q": [1, 32, 2048, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 2048, 8192]}` | 36 | 120267472896/0 | 0/33554432/2147483648 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 2048, 8192]}` | 36 | 0/1879113728 | 0/2147483648/2147483648 | `{"exp": 469794816, "compare_max": 469729280, "mask_decisions": 536870912}` |
| pv | `{"P": [1, 32, 2048, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 2048, 128]}` | 36 | 120267472896/0 | 0/2164260864/16777216 | `{}` |
| o_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 36 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| attention_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 36 | 0/8388608 | 0/33554432/16777216 | `{}` |
| post_attention_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 36 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [2048, 12288]}` | 36 | 206158430208/0 | 100663296/16777216/50331648 | `{}` |
| up_proj | `{"input": [2048, 4096], "weight_math": [4096, 12288], "weight_storage": [12288, 4096], "output": [2048, 12288]}` | 36 | 206158430208/0 | 100663296/16777216/50331648 | `{}` |
| silu_mul | `{"gate": [2048, 12288], "up": [2048, 12288], "output": [2048, 12288]}` | 36 | 0/100663296 | 0/100663296/50331648 | `{"exp": 25165824, "negate": 25165824}` |
| down_proj | `{"input": [2048, 12288], "weight_math": [12288, 4096], "weight_storage": [4096, 12288], "output": [2048, 4096]}` | 36 | 206158430208/0 | 100663296/50331648/16777216 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 36 | 0/8388608 | 0/33554432/16777216 | `{}` |
| final_norm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 1 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## shallower_same_width

工作与TP预算：`{"matrix_flops": 34172407119872, "scalar_flops": 52860389376, "all_unique_weight_bytes": 16356102144, "per_rank_weight_bytes": 8178257920, "aggregate_tp_weight_bytes": 16356515840, "norm_replication_extra_bytes": 413696, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402653184, "per_rank_old_history_read_bytes": 301989888, "per_rank_kv_append_bytes": 100663296, "per_rank_new_kv_request_bytes": 402653184, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10728394752, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 16777216, "per_rank_ring_wire_bytes_exact": "805306368", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 4096], "output": [2048, 4096]}` | 1 | 0/0 | 16777216/16384/16777216 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 24 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 24 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| k_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 24 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| v_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 24 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| q_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 24 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| k_norm | `{"input": [16384, 128], "weight": [128], "output": [16384, 128]}` | 24 | 0/8404992 | 256/4194304/4194304 | `{"rsqrt": 16384}` |
| apply_rope | `{"Q": [1, 32, 2048, 128], "K": [1, 8, 2048, 128]}` | 24 | 0/31457280 | 0/22020096/20971520 | `{"negate": 5242880}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 2048, 128]}` | 24 | 0/0 | 0/8388608/8388608 | `{}` |
| qk | `{"Q": [1, 32, 2048, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 2048, 8192]}` | 24 | 120267472896/0 | 0/33554432/2147483648 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 2048, 8192]}` | 24 | 0/1879113728 | 0/2147483648/2147483648 | `{"exp": 469794816, "compare_max": 469729280, "mask_decisions": 536870912}` |
| pv | `{"P": [1, 32, 2048, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 2048, 128]}` | 24 | 120267472896/0 | 0/2164260864/16777216 | `{}` |
| o_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 24 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| attention_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 24 | 0/8388608 | 0/33554432/16777216 | `{}` |
| post_attention_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 24 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [2048, 20096]}` | 24 | 337154932736/0 | 164626432/16777216/82313216 | `{}` |
| up_proj | `{"input": [2048, 4096], "weight_math": [4096, 20096], "weight_storage": [20096, 4096], "output": [2048, 20096]}` | 24 | 337154932736/0 | 164626432/16777216/82313216 | `{}` |
| silu_mul | `{"gate": [2048, 20096], "up": [2048, 20096], "output": [2048, 20096]}` | 24 | 0/164626432 | 0/164626432/82313216 | `{"exp": 41156608, "negate": 41156608}` |
| down_proj | `{"input": [2048, 20096], "weight_math": [20096, 4096], "weight_storage": [4096, 20096], "output": [2048, 4096]}` | 24 | 337154932736/0 | 164626432/82313216/16777216 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 24 | 0/8388608 | 0/33554432/16777216 | `{}` |
| final_norm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 1 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## deeper_same_width

工作与TP预算：`{"matrix_flops": 39893706211328, "scalar_flops": 101056579584, "all_unique_weight_bytes": 16331341824, "per_rank_weight_bytes": 8166080512, "aggregate_tp_weight_bytes": 16332161024, "norm_replication_extra_bytes": 819200, "kv_bytes_per_token_per_request": 196608, "per_rank_kv_bytes": 805306368, "per_rank_old_history_read_bytes": 603979776, "per_rank_kv_append_bytes": 201326592, "per_rank_new_kv_request_bytes": 805306368, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 11118870528, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 16, "batch_fits": true, "sequential_decoder_layers": 48, "sequential_collectives": 96, "per_collective_activation_payload_bytes": 16777216, "per_rank_ring_wire_bytes_exact": "1610612736", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 4096], "output": [2048, 4096]}` | 1 | 0/0 | 16777216/16384/16777216 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 48 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 48 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| k_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 48 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| v_proj | `{"input": [2048, 4096], "weight_math": [4096, 1024], "weight_storage": [1024, 4096], "output": [2048, 1024]}` | 48 | 17179869184/0 | 8388608/16777216/4194304 | `{}` |
| q_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 48 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| k_norm | `{"input": [16384, 128], "weight": [128], "output": [16384, 128]}` | 48 | 0/8404992 | 256/4194304/4194304 | `{"rsqrt": 16384}` |
| apply_rope | `{"Q": [1, 32, 2048, 128], "K": [1, 8, 2048, 128]}` | 48 | 0/31457280 | 0/22020096/20971520 | `{"negate": 5242880}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 2048, 128]}` | 48 | 0/0 | 0/8388608/8388608 | `{}` |
| qk | `{"Q": [1, 32, 2048, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 32, 2048, 8192]}` | 48 | 120267472896/0 | 0/33554432/2147483648 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 2048, 8192]}` | 48 | 0/1879113728 | 0/2147483648/2147483648 | `{"exp": 469794816, "compare_max": 469729280, "mask_decisions": 536870912}` |
| pv | `{"P": [1, 32, 2048, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 32, 2048, 128]}` | 48 | 120267472896/0 | 0/2164260864/16777216 | `{}` |
| o_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 48 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| attention_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 48 | 0/8388608 | 0/33554432/16777216 | `{}` |
| post_attention_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 48 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [2048, 8320]}` | 48 | 139586437120/0 | 68157440/16777216/34078720 | `{}` |
| up_proj | `{"input": [2048, 4096], "weight_math": [4096, 8320], "weight_storage": [8320, 4096], "output": [2048, 8320]}` | 48 | 139586437120/0 | 68157440/16777216/34078720 | `{}` |
| silu_mul | `{"gate": [2048, 8320], "up": [2048, 8320], "output": [2048, 8320]}` | 48 | 0/68157440 | 0/68157440/34078720 | `{"exp": 17039360, "negate": 17039360}` |
| down_proj | `{"input": [2048, 8320], "weight_math": [8320, 4096], "weight_storage": [4096, 8320], "output": [2048, 4096]}` | 48 | 139586437120/0 | 68157440/34078720/16777216 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 48 | 0/8388608 | 0/33554432/16777216 | `{}` |
| final_norm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 1 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## narrower_same_depth

工作与TP预算：`{"matrix_flops": 36240173039616, "scalar_flops": 60710520832, "all_unique_weight_bytes": 16391282688, "per_rank_weight_bytes": 8195874816, "aggregate_tp_weight_bytes": 16391749632, "norm_replication_extra_bytes": 466944, "kv_bytes_per_token_per_request": 110592, "per_rank_kv_bytes": 452984832, "per_rank_old_history_read_bytes": 339738624, "per_rank_kv_append_bytes": 113246208, "per_rank_new_kv_request_bytes": 452984832, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10796343296, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 30, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 12582912, "per_rank_ring_wire_bytes_exact": "905969664", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 3072], "output": [2048, 3072]}` | 1 | 0/0 | 12582912/16384/12582912 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 3072], "weight": [3072], "output": [2048, 3072]}` | 36 | 0/25167872 | 6144/12582912/12582912 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [2048, 3072]}` | 36 | 38654705664/0 | 18874368/12582912/12582912 | `{}` |
| k_proj | `{"input": [2048, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [2048, 768]}` | 36 | 9663676416/0 | 4718592/12582912/3145728 | `{}` |
| v_proj | `{"input": [2048, 3072], "weight_math": [3072, 768], "weight_storage": [768, 3072], "output": [2048, 768]}` | 36 | 9663676416/0 | 4718592/12582912/3145728 | `{}` |
| q_norm | `{"input": [49152, 128], "weight": [128], "output": [49152, 128]}` | 36 | 0/25214976 | 256/12582912/12582912 | `{"rsqrt": 49152}` |
| k_norm | `{"input": [12288, 128], "weight": [128], "output": [12288, 128]}` | 36 | 0/6303744 | 256/3145728/3145728 | `{"rsqrt": 12288}` |
| apply_rope | `{"Q": [1, 24, 2048, 128], "K": [1, 6, 2048, 128]}` | 36 | 0/23592960 | 0/16777216/15728640 | `{"negate": 3932160}` |
| kv_append | `{"new_K_and_V_each": [1, 6, 2048, 128]}` | 36 | 0/0 | 0/6291456/6291456 | `{}` |
| qk | `{"Q": [1, 24, 2048, 128], "K_shared": [1, 6, 8192, 128], "scores_rectangular": [1, 24, 2048, 8192]}` | 36 | 90200604672/0 | 0/25165824/1610612736 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 24, 2048, 8192]}` | 36 | 0/1409335296 | 0/1610612736/1610612736 | `{"exp": 352346112, "compare_max": 352296960, "mask_decisions": 402653184}` |
| pv | `{"P": [1, 24, 2048, 8192], "V_shared": [1, 6, 8192, 128], "output": [1, 24, 2048, 128]}` | 36 | 90200604672/0 | 0/1623195648/12582912 | `{}` |
| o_proj | `{"input": [2048, 3072], "weight_math": [3072, 3072], "weight_storage": [3072, 3072], "output": [2048, 3072]}` | 36 | 38654705664/0 | 18874368/12582912/12582912 | `{}` |
| attention_residual | `{"inputs_each": [2048, 3072], "output": [2048, 3072]}` | 36 | 0/6291456 | 0/25165824/12582912 | `{}` |
| post_attention_layernorm | `{"input": [2048, 3072], "weight": [3072], "output": [2048, 3072]}` | 36 | 0/25167872 | 6144/12582912/12582912 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [2048, 19328]}` | 36 | 243202523136/0 | 118751232/12582912/79167488 | `{}` |
| up_proj | `{"input": [2048, 3072], "weight_math": [3072, 19328], "weight_storage": [19328, 3072], "output": [2048, 19328]}` | 36 | 243202523136/0 | 118751232/12582912/79167488 | `{}` |
| silu_mul | `{"gate": [2048, 19328], "up": [2048, 19328], "output": [2048, 19328]}` | 36 | 0/158334976 | 0/158334976/79167488 | `{"exp": 39583744, "negate": 39583744}` |
| down_proj | `{"input": [2048, 19328], "weight_math": [19328, 3072], "weight_storage": [3072, 19328], "output": [2048, 3072]}` | 36 | 243202523136/0 | 118751232/79167488/12582912 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 3072], "output": [2048, 3072]}` | 36 | 0/6291456 | 0/25165824/12582912 | `{}` |
| final_norm | `{"input": [2048, 3072], "weight": [3072], "output": [2048, 3072]}` | 1 | 0/25167872 | 6144/12582912/12582912 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 3072], "weight_math": [3072, 151936], "weight_storage": [151936, 3072], "output": [1, 151936]}` | 1 | 933494784/0 | 933494784/6144/303872 | `{}` |

## shallower_wider

工作与TP预算：`{"matrix_flops": 34469171691520, "scalar_flops": 63791532032, "all_unique_weight_bytes": 16418592768, "per_rank_weight_bytes": 8209553408, "aggregate_tp_weight_bytes": 16419106816, "norm_replication_extra_bytes": 514048, "kv_bytes_per_token_per_request": 98304, "per_rank_kv_bytes": 402653184, "per_rank_old_history_read_bytes": 301989888, "per_rank_kv_append_bytes": 100663296, "per_rank_new_kv_request_bytes": 402653184, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10759690240, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 33, "batch_fits": true, "sequential_decoder_layers": 24, "sequential_collectives": 48, "per_collective_activation_payload_bytes": 20971520, "per_rank_ring_wire_bytes_exact": "1006632960", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 5120], "output": [2048, 5120]}` | 1 | 0/0 | 20971520/16384/20971520 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 5120], "weight": [5120], "output": [2048, 5120]}` | 24 | 0/41945088 | 10240/20971520/20971520 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [2048, 5120]}` | 24 | 107374182400/0 | 52428800/20971520/20971520 | `{}` |
| k_proj | `{"input": [2048, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [2048, 1024]}` | 24 | 21474836480/0 | 10485760/20971520/4194304 | `{}` |
| v_proj | `{"input": [2048, 5120], "weight_math": [5120, 1024], "weight_storage": [1024, 5120], "output": [2048, 1024]}` | 24 | 21474836480/0 | 10485760/20971520/4194304 | `{}` |
| q_norm | `{"input": [81920, 128], "weight": [128], "output": [81920, 128]}` | 24 | 0/42024960 | 256/20971520/20971520 | `{"rsqrt": 81920}` |
| k_norm | `{"input": [16384, 128], "weight": [128], "output": [16384, 128]}` | 24 | 0/8404992 | 256/4194304/4194304 | `{"rsqrt": 16384}` |
| apply_rope | `{"Q": [1, 40, 2048, 128], "K": [1, 8, 2048, 128]}` | 24 | 0/37748736 | 0/26214400/25165824 | `{"negate": 6291456}` |
| kv_append | `{"new_K_and_V_each": [1, 8, 2048, 128]}` | 24 | 0/0 | 0/8388608/8388608 | `{}` |
| qk | `{"Q": [1, 40, 2048, 128], "K_shared": [1, 8, 8192, 128], "scores_rectangular": [1, 40, 2048, 8192]}` | 24 | 150334341120/0 | 0/37748736/2684354560 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 40, 2048, 8192]}` | 24 | 0/2348892160 | 0/2684354560/2684354560 | `{"exp": 587243520, "compare_max": 587161600, "mask_decisions": 671088640}` |
| pv | `{"P": [1, 40, 2048, 8192], "V_shared": [1, 8, 8192, 128], "output": [1, 40, 2048, 128]}` | 24 | 150334341120/0 | 0/2701131776/20971520 | `{}` |
| o_proj | `{"input": [2048, 5120], "weight_math": [5120, 5120], "weight_storage": [5120, 5120], "output": [2048, 5120]}` | 24 | 107374182400/0 | 52428800/20971520/20971520 | `{}` |
| attention_residual | `{"inputs_each": [2048, 5120], "output": [2048, 5120]}` | 24 | 0/10485760 | 0/41943040/20971520 | `{}` |
| post_attention_layernorm | `{"input": [2048, 5120], "weight": [5120], "output": [2048, 5120]}` | 24 | 0/41945088 | 10240/20971520/20971520 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [2048, 13952]}` | 24 | 292594647040/0 | 142868480/20971520/57147392 | `{}` |
| up_proj | `{"input": [2048, 5120], "weight_math": [5120, 13952], "weight_storage": [13952, 5120], "output": [2048, 13952]}` | 24 | 292594647040/0 | 142868480/20971520/57147392 | `{}` |
| silu_mul | `{"gate": [2048, 13952], "up": [2048, 13952], "output": [2048, 13952]}` | 24 | 0/114294784 | 0/114294784/57147392 | `{"exp": 28573696, "negate": 28573696}` |
| down_proj | `{"input": [2048, 13952], "weight_math": [13952, 5120], "weight_storage": [5120, 13952], "output": [2048, 5120]}` | 24 | 292594647040/0 | 142868480/57147392/20971520 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 5120], "output": [2048, 5120]}` | 24 | 0/10485760 | 0/41943040/20971520 | `{}` |
| final_norm | `{"input": [2048, 5120], "weight": [5120], "output": [2048, 5120]}` | 1 | 0/41945088 | 10240/20971520/20971520 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 5120], "weight_math": [5120, 151936], "weight_storage": [151936, 5120], "output": [1, 151936]}` | 1 | 1555824640/0 | 1555824640/10240/303872 | `{}` |

## less_kv_more_ffn_budget_match

工作与TP预算：`{"matrix_flops": 37110366076928, "scalar_flops": 76725258240, "all_unique_weight_bytes": 16381470720, "per_rank_weight_bytes": 8191043584, "aggregate_tp_weight_bytes": 16382087168, "norm_replication_extra_bytes": 616448, "kv_bytes_per_token_per_request": 36864, "per_rank_kv_bytes": 150994944, "per_rank_old_history_read_bytes": 113246208, "per_rank_kv_append_bytes": 37748736, "per_rank_new_kv_request_bytes": 150994944, "per_rank_workspace_reserved_bytes": 2147483648, "per_rank_live_budget_bytes": 10489522176, "per_rank_capacity_bytes": 24000000000, "max_equal_length_requests": 90, "batch_fits": true, "sequential_decoder_layers": 36, "sequential_collectives": 72, "per_collective_activation_payload_bytes": 16777216, "per_rank_ring_wire_bytes_exact": "1207959552", "collective_scope": "TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim"}`

| 算子 | 形状 | repeats | 单次矩阵/标量 | 单次权重读/激活读/写bytes | 特殊函数 |
| --- | --- | ---: | --- | --- | --- |
| embedding | `{"indices": [1, 2048], "table": [151936, 4096], "output": [2048, 4096]}` | 1 | 0/0 | 16777216/16384/16777216 | `{}` |
| rope_table | `{"frequencies": [2048, 64], "cos_sin_each": [2048, 128]}` | 1 | 0/131072 | 0/16640/1048576 | `{"sin": 262144, "cos": 262144}` |
| input_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 36 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| q_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 36 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| k_proj | `{"input": [2048, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [2048, 256]}` | 36 | 4294967296/0 | 2097152/16777216/1048576 | `{}` |
| v_proj | `{"input": [2048, 4096], "weight_math": [4096, 256], "weight_storage": [256, 4096], "output": [2048, 256]}` | 36 | 4294967296/0 | 2097152/16777216/1048576 | `{}` |
| q_norm | `{"input": [65536, 128], "weight": [128], "output": [65536, 128]}` | 36 | 0/33619968 | 256/16777216/16777216 | `{"rsqrt": 65536}` |
| k_norm | `{"input": [4096, 128], "weight": [128], "output": [4096, 128]}` | 36 | 0/2101248 | 256/1048576/1048576 | `{"rsqrt": 4096}` |
| apply_rope | `{"Q": [1, 32, 2048, 128], "K": [1, 2, 2048, 128]}` | 36 | 0/26738688 | 0/18874368/17825792 | `{"negate": 4456448}` |
| kv_append | `{"new_K_and_V_each": [1, 2, 2048, 128]}` | 36 | 0/0 | 0/2097152/2097152 | `{}` |
| qk | `{"Q": [1, 32, 2048, 128], "K_shared": [1, 2, 8192, 128], "scores_rectangular": [1, 32, 2048, 8192]}` | 36 | 120267472896/0 | 0/20971520/2147483648 | `{}` |
| score_scale_mask_softmax | `{"scores": [1, 32, 2048, 8192]}` | 36 | 0/1879113728 | 0/2147483648/2147483648 | `{"exp": 469794816, "compare_max": 469729280, "mask_decisions": 536870912}` |
| pv | `{"P": [1, 32, 2048, 8192], "V_shared": [1, 2, 8192, 128], "output": [1, 32, 2048, 128]}` | 36 | 120267472896/0 | 0/2151677952/16777216 | `{}` |
| o_proj | `{"input": [2048, 4096], "weight_math": [4096, 4096], "weight_storage": [4096, 4096], "output": [2048, 4096]}` | 36 | 68719476736/0 | 33554432/16777216/16777216 | `{}` |
| attention_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 36 | 0/8388608 | 0/33554432/16777216 | `{}` |
| post_attention_layernorm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 36 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| gate_proj | `{"input": [2048, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [2048, 12800]}` | 36 | 214748364800/0 | 104857600/16777216/52428800 | `{}` |
| up_proj | `{"input": [2048, 4096], "weight_math": [4096, 12800], "weight_storage": [12800, 4096], "output": [2048, 12800]}` | 36 | 214748364800/0 | 104857600/16777216/52428800 | `{}` |
| silu_mul | `{"gate": [2048, 12800], "up": [2048, 12800], "output": [2048, 12800]}` | 36 | 0/104857600 | 0/104857600/52428800 | `{"exp": 26214400, "negate": 26214400}` |
| down_proj | `{"input": [2048, 12800], "weight_math": [12800, 4096], "weight_storage": [4096, 12800], "output": [2048, 4096]}` | 36 | 214748364800/0 | 104857600/52428800/16777216 | `{}` |
| ffn_residual | `{"inputs_each": [2048, 4096], "output": [2048, 4096]}` | 36 | 0/8388608 | 0/33554432/16777216 | `{}` |
| final_norm | `{"input": [2048, 4096], "weight": [4096], "output": [2048, 4096]}` | 1 | 0/33556480 | 8192/16777216/16777216 | `{"rsqrt": 2048}` |
| lm_head | `{"input": [1, 4096], "weight_math": [4096, 151936], "weight_storage": [151936, 4096], "output": [1, 151936]}` | 1 | 1244659712/0 | 1244659712/8192/303872 | `{}` |

## 容量与通信切换条件

容量区间含两端；通信只覆盖声明的两类decoder collective，不代表完整请求时间。
- `{"variant": "shallower_same_width", "matrix_flops_delta": -2937958957056, "per_rank_weights_delta": -12785664, "per_rank_kv_delta": -201326592, "per_rank_live_budget_delta": -214112256, "capacity_interval_where_only_smaller_fits_bytes": [10728394752, 10942507007], "per_rank_ring_wire_delta_exact": "-402653184", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "deeper_same_width", "matrix_flops_delta": 2783340134400, "per_rank_weights_delta": -24963072, "per_rank_kv_delta": 201326592, "per_rank_live_budget_delta": 176363520, "capacity_interval_where_only_smaller_fits_bytes": [10942507008, 11118870527], "per_rank_ring_wire_delta_exact": "402653184", "sequential_collectives_delta": 24, "sequential_layers_delta": 12}`
- `{"variant": "narrower_same_depth", "matrix_flops_delta": -870193037312, "per_rank_weights_delta": 4831232, "per_rank_kv_delta": -150994944, "per_rank_live_budget_delta": -146163712, "capacity_interval_where_only_smaller_fits_bytes": [10796343296, 10942507007], "per_rank_ring_wire_delta_exact": "-301989888", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`
- `{"variant": "shallower_wider", "matrix_flops_delta": -2641194385408, "per_rank_weights_delta": 18509824, "per_rank_kv_delta": -201326592, "per_rank_live_budget_delta": -182816768, "capacity_interval_where_only_smaller_fits_bytes": [10759690240, 10942507007], "per_rank_ring_wire_delta_exact": "-201326592", "sequential_collectives_delta": -24, "sequential_layers_delta": -12}`
- `{"variant": "less_kv_more_ffn_budget_match", "matrix_flops_delta": 0, "per_rank_weights_delta": 0, "per_rank_kv_delta": -452984832, "per_rank_live_budget_delta": -452984832, "capacity_interval_where_only_smaller_fits_bytes": [10489522176, 10942507007], "per_rank_ring_wire_delta_exact": "0", "sequential_collectives_delta": 0, "sequential_layers_delta": 0}`

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
