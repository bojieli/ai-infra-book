# sequence-dependencies — fixed-teaching-rnn-and-causal-transformer

输入：`{"dtype": "fp64", "ff_width": 8, "heads": 1, "layers": 3, "next_supplied_token": 4, "tokens": [0, 1, 2, 3], "width": 4}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| all_same_model_cache_checks_pass | `true` |
| max_absolute_error | 0.0 |
| rnn_weight_parameters | 96 |
| transformer_weight_parameters | 384 |
| shared_input_table_parameters | 20 |
| complete_runtime_peak_bytes | `null` |
| complete_runtime_seconds | `null` |

同模型执行路径工作

| model | mode | matrix_flops | weight_matrix_flops | attention_matrix_flops |
| --- | --- | --- | --- | --- |
| "rnn" | "known_four_tokens" | 768 | 768 | 0 |
| "rnn" | "four_prefixes_recomputed" | 1920 | 1920 | 0 |
| "rnn" | "four_tokens_state_reused" | 768 | 768 | 0 |
| "rnn" | "fifth_token_prefix_recomputed" | 960 | 960 | 0 |
| "rnn" | "fifth_token_state_reused" | 192 | 192 | 0 |
| "transformer" | "known_four_tokens" | 3552 | 3072 | 480 |
| "transformer" | "four_prefixes_recomputed" | 8640 | 7680 | 960 |
| "transformer" | "four_tokens_state_reused" | 3552 | 3072 | 480 |
| "transformer" | "fifth_token_prefix_recomputed" | 4560 | 3840 | 720 |
| "transformer" | "fifth_token_state_reused" | 1008 | 768 | 240 |

历史状态与下一token读写

| model | after_tokens | persistent_history_elements | persistent_history_bytes | newly_written_state_bytes | capacity_growth_bytes | next_token_prior_history_read_bytes | next_token_current_kv_attention_read_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| "rnn" | 1 | 12 | 96 | 96 | 0 | 96 | 0 |
| "rnn" | 2 | 12 | 96 | 96 | 0 | 96 | 0 |
| "rnn" | 3 | 12 | 96 | 96 | 0 | 96 | 0 |
| "rnn" | 4 | 12 | 96 | 96 | 0 | 96 | 0 |
| "rnn" | 5 | 12 | 96 | 96 | 0 | 96 | 0 |
| "transformer" | 1 | 24 | 192 | 192 | 192 | 192 | 192 |
| "transformer" | 2 | 48 | 384 | 192 | 192 | 384 | 192 |
| "transformer" | 3 | 72 | 576 | 192 | 192 | 576 | 192 |
| "transformer" | 4 | 96 | 768 | 192 | 192 | 768 | 192 |
| "transformer" | 5 | 120 | 960 | 192 | 192 | 960 | 192 |

同模型缓存/重算输出核验

| model | prefix_tokens | recomputed_output | reused_output | max_absolute_error | absolute_tolerance | passed |
| --- | --- | --- | --- | --- | --- | --- |
| "rnn" | 1 | [-0.0025052397646709006, 0.004113485857802942, -0.0007001301464467371, 0.007369769977568105] | [-0.0025052397646709006, 0.004113485857802942, -0.0007001301464467371, 0.007369769977568105] | 0.0 | 1e-12 | true |
| "transformer" | 1 | [0.28652640759322645, -0.05041098058430378, -0.24976725026504282, 0.19969914438262273] | [0.28652640759322645, -0.05041098058430378, -0.24976725026504282, 0.19969914438262273] | 0.0 | 1e-12 | true |
| "rnn" | 2 | [0.006853216890058965, -0.010031954172117993, 0.003588594193303938, -0.005984333412015839] | [0.006853216890058965, -0.010031954172117993, 0.003588594193303938, -0.005984333412015839] | 0.0 | 1e-12 | true |
| "transformer" | 2 | [0.16743128428092363, -0.028415975337990063, 0.27158773328706365, 0.18367252252190205] | [0.16743128428092363, -0.028415975337990063, 0.27158773328706365, 0.18367252252190205] | 0.0 | 1e-12 | true |
| "rnn" | 3 | [0.008276957542629176, -0.008773592049013217, 0.002724191870486338, 0.001010586407981906] | [0.008276957542629176, -0.008773592049013217, 0.002724191870486338, 0.001010586407981906] | 0.0 | 1e-12 | true |
| "transformer" | 3 | [0.11264699074410363, -0.05319587785317624, 0.25605455497609597, 0.17235233359707394] | [0.11264699074410363, -0.05319587785317624, 0.25605455497609597, 0.17235233359707394] | 0.0 | 1e-12 | true |
| "rnn" | 4 | [0.007156686260174058, -0.008349401570473697, 0.003452133957952543, -0.0014427824587598759] | [0.007156686260174058, -0.008349401570473697, 0.003452133957952543, -0.0014427824587598759] | 0.0 | 1e-12 | true |
| "transformer" | 4 | [0.06577565690280879, -0.08417530745899202, 0.2424791623216661, 0.1640866194943946] | [0.06577565690280879, -0.08417530745899202, 0.2424791623216661, 0.1640866194943946] | 0.0 | 1e-12 | true |
| "rnn" | 5 | [0.0049255405694181905, -0.005570781202941996, 0.0021951564686026825, -0.0013359845077077343] | [0.0049255405694181905, -0.005570781202941996, 0.0021951564686026825, -0.0013359845077077343] | 0.0 | 1e-12 | true |
| "transformer" | 5 | [0.02213231253366481, -0.11766357930193837, 0.2297412618750263, 0.15702929194960807] | [0.02213231253366481, -0.11766357930193837, 0.2297412618750263, 0.15702929194960807] | 0.0 | 1e-12 | true |

完整逐矩阵形状和接口

| model | invocation | layer | operation | lhs_shape | rhs_shape | output_shape | flops | rhs_kind | logical_lhs_bytes | logical_rhs_bytes | logical_output_bytes | mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "rnn" | 0 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 1 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 2 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "known_four_tokens" |
| "rnn" | 0 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 1 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 0 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 1 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 2 | 2 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 0 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 1 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 3 | 2 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 1 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 0 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 0 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 1 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 1 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 2 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 2 | 2 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 0 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 0 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 1 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 1 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 2 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 3 | 2 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "rnn" | 0 | 0 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 1 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t0" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t1" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t2" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 2 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "rnn" | 0 | 0 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "rnn" | 0 | 0 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "rnn" | 0 | 1 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "rnn" | 0 | 1 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "rnn" | 0 | 2 | "input_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "rnn" | 0 | 2 | "state_projection_t4" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 0 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 0 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 0 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 0 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "known_four_tokens" |
| "transformer" | 0 | 0 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "known_four_tokens" |
| "transformer" | 0 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "known_four_tokens" |
| "transformer" | 0 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "known_four_tokens" |
| "transformer" | 0 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "known_four_tokens" |
| "transformer" | 0 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "known_four_tokens" |
| "transformer" | 0 | 0 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "known_four_tokens" |
| "transformer" | 0 | 0 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "known_four_tokens" |
| "transformer" | 0 | 0 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 0 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 1 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 1 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 1 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 1 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 1 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "known_four_tokens" |
| "transformer" | 0 | 1 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "known_four_tokens" |
| "transformer" | 0 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "known_four_tokens" |
| "transformer" | 0 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "known_four_tokens" |
| "transformer" | 0 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "known_four_tokens" |
| "transformer" | 0 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "known_four_tokens" |
| "transformer" | 0 | 1 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "known_four_tokens" |
| "transformer" | 0 | 1 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "known_four_tokens" |
| "transformer" | 0 | 1 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 1 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 2 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 2 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 2 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 2 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "known_four_tokens" |
| "transformer" | 0 | 2 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "known_four_tokens" |
| "transformer" | 0 | 2 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "known_four_tokens" |
| "transformer" | 0 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "known_four_tokens" |
| "transformer" | 0 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "known_four_tokens" |
| "transformer" | 0 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "known_four_tokens" |
| "transformer" | 0 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "known_four_tokens" |
| "transformer" | 0 | 2 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "known_four_tokens" |
| "transformer" | 0 | 2 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "known_four_tokens" |
| "transformer" | 0 | 2 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 2 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "known_four_tokens" |
| "transformer" | 0 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 0 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 0 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "q" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "k" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "v" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "o" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "ff_up" | [2, 4] | [4, 8] | [2, 8] | 128 | "weight" | 64 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "ff_down" | [2, 8] | [8, 4] | [2, 4] | 128 | "weight" | 128 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 1 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "q" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "k" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "v" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "o" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "ff_up" | [2, 4] | [4, 8] | [2, 8] | 128 | "weight" | 64 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "ff_down" | [2, 8] | [8, 4] | [2, 4] | 128 | "weight" | 128 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 1 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "q" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "k" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "v" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "o" | [2, 4] | [4, 4] | [2, 4] | 64 | "weight" | 64 | 128 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "ff_up" | [2, 4] | [4, 8] | [2, 8] | 128 | "weight" | 64 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "ff_down" | [2, 8] | [8, 4] | [2, 4] | 128 | "weight" | 128 | 256 | 64 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 1 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "q" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "k" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "v" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "o" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "ff_up" | [3, 4] | [4, 8] | [3, 8] | 192 | "weight" | 96 | 256 | 192 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "ff_down" | [3, 8] | [8, 4] | [3, 4] | 192 | "weight" | 192 | 256 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 2 | 0 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "q" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "k" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "v" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "o" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "ff_up" | [3, 4] | [4, 8] | [3, 8] | 192 | "weight" | 96 | 256 | 192 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "ff_down" | [3, 8] | [8, 4] | [3, 4] | 192 | "weight" | 192 | 256 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 2 | 1 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "q" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "k" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "v" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "o" | [3, 4] | [4, 4] | [3, 4] | 96 | "weight" | 96 | 128 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "ff_up" | [3, 4] | [4, 8] | [3, 8] | 192 | "weight" | 96 | 256 | 192 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "ff_down" | [3, 8] | [8, 4] | [3, 4] | 192 | "weight" | 192 | 256 | 96 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 2 | 2 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 0 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 1 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "q" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "k" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "v" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "o" | [4, 4] | [4, 4] | [4, 4] | 128 | "weight" | 128 | 128 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "ff_up" | [4, 4] | [4, 8] | [4, 8] | 256 | "weight" | 128 | 256 | 256 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "ff_down" | [4, 8] | [8, 4] | [4, 4] | 256 | "weight" | 256 | 256 | 128 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 3 | 2 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_prefixes_recomputed" |
| "transformer" | 0 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_tokens_state_reused" |
| "transformer" | 0 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "four_tokens_state_reused" |
| "transformer" | 0 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_tokens_state_reused" |
| "transformer" | 1 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_tokens_state_reused" |
| "transformer" | 1 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "four_tokens_state_reused" |
| "transformer" | 1 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_tokens_state_reused" |
| "transformer" | 2 | 0 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_tokens_state_reused" |
| "transformer" | 2 | 1 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "four_tokens_state_reused" |
| "transformer" | 2 | 2 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 0 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 1 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 3 | 2 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "four_tokens_state_reused" |
| "transformer" | 0 | 0 | "q" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "k" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "v" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "o" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "ff_up" | [5, 4] | [4, 8] | [5, 8] | 320 | "weight" | 160 | 256 | 320 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "ff_down" | [5, 8] | [8, 4] | [5, 4] | 320 | "weight" | 320 | 256 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "q" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "k" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "v" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "o" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "ff_up" | [5, 4] | [4, 8] | [5, 8] | 320 | "weight" | 160 | 256 | 320 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "ff_down" | [5, 8] | [8, 4] | [5, 4] | 320 | "weight" | 320 | 256 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 1 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "q" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "k" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "v" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "o" | [5, 4] | [4, 4] | [5, 4] | 160 | "weight" | 160 | 128 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "ff_up" | [5, 4] | [4, 8] | [5, 8] | 320 | "weight" | 160 | 256 | 320 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "ff_down" | [5, 8] | [8, 4] | [5, 4] | 320 | "weight" | 320 | 256 | 160 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "qk_t0" | [1, 4] | [4, 1] | [1, 1] | 8 | "activation" | 32 | 32 | 8 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "av_t0" | [1, 1] | [1, 4] | [1, 4] | 8 | "activation" | 8 | 32 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "qk_t1" | [1, 4] | [4, 2] | [1, 2] | 16 | "activation" | 32 | 64 | 16 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "av_t1" | [1, 2] | [2, 4] | [1, 4] | 16 | "activation" | 16 | 64 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "qk_t2" | [1, 4] | [4, 3] | [1, 3] | 24 | "activation" | 32 | 96 | 24 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "av_t2" | [1, 3] | [3, 4] | [1, 4] | 24 | "activation" | 24 | 96 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "qk_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "av_t3" | [1, 4] | [4, 4] | [1, 4] | 32 | "activation" | 32 | 128 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 2 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_prefix_recomputed" |
| "transformer" | 0 | 0 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_state_reused" |
| "transformer" | 0 | 0 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_state_reused" |
| "transformer" | 0 | 1 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "q" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "k" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "v" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "o" | [1, 4] | [4, 4] | [1, 4] | 32 | "weight" | 32 | 128 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "ff_up" | [1, 4] | [4, 8] | [1, 8] | 64 | "weight" | 32 | 256 | 64 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "ff_down" | [1, 8] | [8, 4] | [1, 4] | 64 | "weight" | 64 | 256 | 32 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "qk_t4" | [1, 4] | [4, 5] | [1, 5] | 40 | "activation" | 32 | 160 | 40 | "fifth_token_state_reused" |
| "transformer" | 0 | 2 | "av_t4" | [1, 5] | [5, 4] | [1, 4] | 40 | "activation" | 40 | 160 | 32 | "fifth_token_state_reused" |

逐节点/边依赖图、实际教学权重和输入保留于同名JSON；单位节点关键路径不是硬件时延。

计量条件：

- Fixed pedagogical weights: ((17(i+1)+11(j+1)+7seed)%19-9)/32; distinct layer seeds, weights shared over time.
- RNN is h=tanh(xWx+h_previousWh), zero initial states; no bias, gate, residual or output head.
- Transformer is one-head scaled causal softmax attention, output projection and residual, tanh FFN and residual; no norm, bias, dropout or output head.
- Four known tokens and supplied fifth token use fixed additive positional signals. No sampling, tokenizer, vocabulary logits or checkpoint claim.
- Only outputs of the same model are compared. Prefix recomputation and cache/state reuse include the same entire three-layer model.
- Python float is binary64; 2mnk is the declared matrix FLOPs convention. tanh/exp/sqrt, reductions outside GEMM, residuals and softmax are excluded from matrix totals.
- Ragged attention rows count only valid causal pairs, not dense masked upper triangle execution. Logical operand bytes do not claim HBM transfers.
- State bytes include persistent per-layer hidden vectors or K/V only, not weights, current temporary activations or allocator peak. Initial RNN zeros are retained capacity, not prior token history.
- Graph unit-node critical path compares dependencies under equal cell costs; actual transformer attention cell work grows with position. Cached generation additionally requires each supplied next input.

固定来源：

