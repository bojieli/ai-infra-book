# audio-generation-matrix-and-codebook-ledger — fish-audio-s2-pro

输入：`{"audio_history": 32, "batch": 1, "fish_prompt_tokens": 0, "frames": 128, "kv_element_bytes": 2, "operand_element_bytes": 2, "text_history": 128, "text_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| accounted_transformer_and_bridge_matrix_flops | 2,100,285,145,088 |
| full_model_parameters | `null` |
| full_generation_flops | `null` |
| full_codec_flops | `null` |
| predicted_latency_seconds | `null` |

音频阶段供给：`{"effective_rates": {"matrix": null, "interface": null, "scalar": null}, "accounted_work_totals": {"matrix_flops": 2966375890944, "accounted_interface_bytes": 2104046030532, "accounted_scalar_flops": 3482744672}, "accounted_serial_critical_path_lower_bound_seconds_exact": null, "full_request_latency_seconds": null, "first_audio_latency_seconds": null, "prompt_scope": "Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.", "duration_basis_seconds_exact": "65536/11025", "required_matrix_flops_per_second_exact": "499027926600", "required_accounted_interface_bytes_per_second_exact": "5799276871653825/16384", "required_accounted_scalar_flops_per_second_exact": "1199914375275/2048", "interpretation": "Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies."}`

| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |
| --- | --- | ---: | ---: | --- |
| semantic_index_clamp | index | 0 | 0 | 0/1024/1024 |
| semantic_book_0_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| semantic_book_0_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| semantic_book_0_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| semantic_book_0_accumulate | reduce | 0 | 131072 | 0/262144/262144 |
| semantic_unused_latent_cat | copy | 0 | 0 | 0/2048/2048 |
| residual_index_clamp | index | 0 | 0 | 0/9216/9216 |
| residual_book_0_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_0_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_0_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_0_accumulate | reduce | 0 | 131072 | 0/262144/262144 |
| residual_book_1_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_1_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_1_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_1_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_2_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_2_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_2_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_2_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_3_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_3_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_3_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_3_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_4_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_4_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_4_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_4_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_5_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_5_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_5_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_5_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_6_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_6_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_6_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_6_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_7_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_7_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_7_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_7_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_book_8_lookup | embedding | 0 | 0 | 2048/1024/2048 |
| residual_book_8_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_8_out_proj | conv1d | 2097152 | 131072 | 18432/2048/262144 |
| residual_book_8_accumulate | reduce | 0 | 131072 | 0/524288/262144 |
| residual_unused_latent_cat | copy | 0 | 0 | 0/18432/18432 |
| semantic_residual_add | residual | 0 | 131072 | 0/524288/262144 |
| rvq_post_transformer | transformer | 28187820032 | 29902976 | 218103808/395184128/0 |
| upsample_0 | conv_transpose1d | 536870912 | 262144 | 4196352/262144/524288 |
| upsample_0_crop_contiguous | copy | 0 | 0 | 0/524288/524288 |
| upsample_0_depthwise | causal_conv1d | 3670016 | 262144 | 16384/524288/524288 |
| upsample_0_layernorm | normalization | 0 | 1835264 | 4096/524288/524288 |
| upsample_0_pointwise1 | linear | 2147483648 | 1048576 | 8396800/524288/2097152 |
| upsample_0_gelu | activation | 0 | 0 | 0/2097152/2097152 |
| upsample_0_pointwise2 | linear | 2147483648 | 262144 | 8390656/2097152/524288 |
| upsample_0_gamma_residual | residual | 0 | 524288 | 2048/1048576/524288 |
| upsample_1 | conv_transpose1d | 1073741824 | 524288 | 4196352/524288/1048576 |
| upsample_1_crop_contiguous | copy | 0 | 0 | 0/1048576/1048576 |
| upsample_1_depthwise | causal_conv1d | 7340032 | 524288 | 16384/1048576/1048576 |
| upsample_1_layernorm | normalization | 0 | 3670528 | 4096/1048576/1048576 |
| upsample_1_pointwise1 | linear | 4294967296 | 2097152 | 8396800/1048576/4194304 |
| upsample_1_gelu | activation | 0 | 0 | 0/4194304/4194304 |
| upsample_1_pointwise2 | linear | 4294967296 | 524288 | 8390656/4194304/1048576 |
| upsample_1_gamma_residual | residual | 0 | 1048576 | 2048/2097152/1048576 |
| decoder_input_weight_norm | weight_normalization | 0 | 33030144 | 0/22023168/22020096 |
| decoder_input | causal_conv1d | 11274289152 | 786432 | 22023168/1048576/1572864 |
| decoder_0_snake | snake1d | 0 | 3148800 | 3072/1572864/1572864 |
| decoder_0_upsample_weight_norm | weight_normalization | 0 | 56623104 | 0/37751808/37748736 |
| decoder_0_upsample | conv_transpose1d | 19327352832 | 3151872 | 37750272/1572864/6303744 |
| decoder_0_upsample_crop_contiguous | copy | 0 | 0 | 0/6291456/6291456 |
| decoder_0_residual_d1_snake1 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d1_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d1_conv1 | causal_conv1d | 33822867456 | 3145728 | 8259072/6291456/6291456 |
| decoder_0_residual_d1_snake2 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d1_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d1_conv2 | causal_conv1d | 4831838208 | 3145728 | 1181184/6291456/6291456 |
| decoder_0_residual_d1_add | residual | 0 | 3145728 | 0/12582912/6291456 |
| decoder_0_residual_d3_snake1 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d3_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d3_conv1 | causal_conv1d | 33822867456 | 3145728 | 8259072/6291456/6291456 |
| decoder_0_residual_d3_snake2 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d3_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d3_conv2 | causal_conv1d | 4831838208 | 3145728 | 1181184/6291456/6291456 |
| decoder_0_residual_d3_add | residual | 0 | 3145728 | 0/12582912/6291456 |
| decoder_0_residual_d9_snake1 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d9_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d9_conv1 | causal_conv1d | 33822867456 | 3145728 | 8259072/6291456/6291456 |
| decoder_0_residual_d9_snake2 | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_0_residual_d9_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d9_conv2 | causal_conv1d | 4831838208 | 3145728 | 1181184/6291456/6291456 |
| decoder_0_residual_d9_add | residual | 0 | 3145728 | 0/12582912/6291456 |
| decoder_1_snake | snake1d | 0 | 12584448 | 1536/6291456/6291456 |
| decoder_1_upsample_weight_norm | weight_normalization | 0 | 14155776 | 0/9438720/9437184 |
| decoder_1_upsample | conv_transpose1d | 38654705664 | 12585984 | 9437952/6291456/25171968 |
| decoder_1_upsample_crop_contiguous | copy | 0 | 0 | 0/25165824/25165824 |
| decoder_1_residual_d1_snake1 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d1_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d1_conv1 | causal_conv1d | 67645734912 | 12582912 | 2065152/25165824/25165824 |
| decoder_1_residual_d1_snake2 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d1_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d1_conv2 | causal_conv1d | 9663676416 | 12582912 | 295680/25165824/25165824 |
| decoder_1_residual_d1_add | residual | 0 | 12582912 | 0/50331648/25165824 |
| decoder_1_residual_d3_snake1 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d3_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d3_conv1 | causal_conv1d | 67645734912 | 12582912 | 2065152/25165824/25165824 |
| decoder_1_residual_d3_snake2 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d3_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d3_conv2 | causal_conv1d | 9663676416 | 12582912 | 295680/25165824/25165824 |
| decoder_1_residual_d3_add | residual | 0 | 12582912 | 0/50331648/25165824 |
| decoder_1_residual_d9_snake1 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d9_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d9_conv1 | causal_conv1d | 67645734912 | 12582912 | 2065152/25165824/25165824 |
| decoder_1_residual_d9_snake2 | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_1_residual_d9_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d9_conv2 | causal_conv1d | 9663676416 | 12582912 | 295680/25165824/25165824 |
| decoder_1_residual_d9_add | residual | 0 | 12582912 | 0/50331648/25165824 |
| decoder_2_snake | snake1d | 0 | 50332416 | 768/25165824/25165824 |
| decoder_2_upsample_weight_norm | weight_normalization | 0 | 1769472 | 0/1180416/1179648 |
| decoder_2_upsample | conv_transpose1d | 38654705664 | 25166592 | 1180032/25165824/50333184 |
| decoder_2_upsample_crop_contiguous | copy | 0 | 0 | 0/50331648/50331648 |
| decoder_2_residual_d1_snake1 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d1_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d1_conv1 | causal_conv1d | 67645734912 | 25165824 | 516480/50331648/50331648 |
| decoder_2_residual_d1_snake2 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d1_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d1_conv2 | causal_conv1d | 9663676416 | 25165824 | 74112/50331648/50331648 |
| decoder_2_residual_d1_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| decoder_2_residual_d3_snake1 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d3_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d3_conv1 | causal_conv1d | 67645734912 | 25165824 | 516480/50331648/50331648 |
| decoder_2_residual_d3_snake2 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d3_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d3_conv2 | causal_conv1d | 9663676416 | 25165824 | 74112/50331648/50331648 |
| decoder_2_residual_d3_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| decoder_2_residual_d9_snake1 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d9_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d9_conv1 | causal_conv1d | 67645734912 | 25165824 | 516480/50331648/50331648 |
| decoder_2_residual_d9_snake2 | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_2_residual_d9_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d9_conv2 | causal_conv1d | 9663676416 | 25165824 | 74112/50331648/50331648 |
| decoder_2_residual_d9_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| decoder_3_snake | snake1d | 0 | 100663680 | 384/50331648/50331648 |
| decoder_3_upsample_weight_norm | weight_normalization | 0 | 221184 | 0/147840/147456 |
| decoder_3_upsample | conv_transpose1d | 19327352832 | 25166016 | 147648/50331648/50332032 |
| decoder_3_upsample_crop_contiguous | copy | 0 | 0 | 0/50331648/50331648 |
| decoder_3_residual_d1_snake1 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d1_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d1_conv1 | causal_conv1d | 33822867456 | 25165824 | 129216/50331648/50331648 |
| decoder_3_residual_d1_snake2 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d1_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d1_conv2 | causal_conv1d | 4831838208 | 25165824 | 18624/50331648/50331648 |
| decoder_3_residual_d1_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| decoder_3_residual_d3_snake1 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d3_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d3_conv1 | causal_conv1d | 33822867456 | 25165824 | 129216/50331648/50331648 |
| decoder_3_residual_d3_snake2 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d3_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d3_conv2 | causal_conv1d | 4831838208 | 25165824 | 18624/50331648/50331648 |
| decoder_3_residual_d3_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| decoder_3_residual_d9_snake1 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d9_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d9_conv1 | causal_conv1d | 33822867456 | 25165824 | 129216/50331648/50331648 |
| decoder_3_residual_d9_snake2 | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| decoder_3_residual_d9_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d9_conv2 | causal_conv1d | 4831838208 | 25165824 | 18624/50331648/50331648 |
| decoder_3_residual_d9_add | residual | 0 | 25165824 | 0/100663296/50331648 |
| output_snake | snake1d | 0 | 100663488 | 192/50331648/50331648 |
| output_conv_weight_norm | weight_normalization | 0 | 2016 | 0/1346/1344 |
| output_conv | causal_conv1d | 352321536 | 262144 | 1346/50331648/524288 |
| wave_tanh | activation | 0 | 0 | 0/524288/524288 |

阶段：slow_ar

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 128 | 2560 | 4096 | 36 | 96636764160 |
| k | 128 | 2560 | 1024 | 36 | 24159191040 |
| v | 128 | 2560 | 1024 | 36 | 24159191040 |
| o | 128 | 4096 | 2560 | 36 | 96636764160 |
| ffn_gate | 128 | 2560 | 9728 | 36 | 229512314880 |
| ffn_up | 128 | 2560 | 9728 | 36 | 229512314880 |
| ffn_down | 128 | 9728 | 2560 | 36 | 229512314880 |
| output_head | 128 | 2560 | 155776 | 1 | 102089359360 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 1032218214400, "qk_matrix_flops": 3642753024, "pv_matrix_flops": 3642753024, "matrix_flops": 1039503720448, "matrix_weight_elements": 4032102400, "kv_bytes_per_position_per_request": 147456, "kv_retained_logical_bytes": 23592960, "processed_rows": 128, "valid_attention_pairs_all_invocations": 12352, "invocations": 128, "accounted_scalar_flops": 431043712, "special_ops": {"rsqrt": 193664, "rope_sign_negation": 11796480, "attention_exp": 14229504, "attention_max_compare": 14082048, "sigmoid": 44826624}, "matrix_weight_interface_bytes": 1032218214400, "matrix_activation_read_bytes": 246022144, "matrix_activation_write_bytes": 322994176, "attention_logical_interface_bytes": 1953792000, "accounted_nonmatrix_interface_bytes": 983728128, "accounted_interface_bytes": 1035724750848}`

阶段：fast_ar_reset_each_frame

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 1280 | 2560 | 4096 | 4 | 107374182400 |
| k | 1280 | 2560 | 1024 | 4 | 26843545600 |
| v | 1280 | 2560 | 1024 | 4 | 26843545600 |
| o | 1280 | 4096 | 2560 | 4 | 107374182400 |
| ffn_gate | 1280 | 2560 | 9728 | 4 | 255013683200 |
| ffn_up | 1280 | 2560 | 9728 | 4 | 255013683200 |
| ffn_down | 1280 | 9728 | 2560 | 4 | 255013683200 |
| output_head | 1280 | 2560 | 4096 | 1 | 26843545600 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 1060320051200, "qk_matrix_flops": 230686720, "pv_matrix_flops": 230686720, "matrix_flops": 1060781424640, "matrix_weight_elements": 414187520, "kv_bytes_per_position_per_request": 16384, "kv_retained_logical_bytes": 163840, "processed_rows": 1280, "valid_attention_pairs_all_invocations": 7040, "invocations": 1280, "accounted_scalar_flops": 325889280, "special_ops": {"rsqrt": 11520, "rope_sign_negation": 13107200, "attention_exp": 901120, "attention_max_compare": 737280, "sigmoid": 49807360}, "matrix_weight_interface_bytes": 1060320051200, "matrix_activation_read_bytes": 279183360, "matrix_activation_write_bytes": 325058560, "attention_logical_interface_bytes": 202833920, "accounted_nonmatrix_interface_bytes": 943390720, "accounted_interface_bytes": 1062070517760}`

码本循环：`{"primary_audio_codes": 128, "residual_codes": 1152, "fast_calls": 1280, "fast_discarded_priming_heads": 128, "fast_sampled_residual_heads": 1152, "fast_cache_reset_per_frame": true}`

codec时间轴：`{"sample_rate": 44100, "nominal_samples_per_frame": 2048, "nominal_frames_per_second_exact": "11025/512", "nominal_output_samples": 262144, "nominal_output_seconds_exact": "65536/11025", "source_output_samples": 262144, "evidence": "Locked Fish right-only ConvTranspose crops preserve each stride; source decoder produces exactly 2048*frames samples.", "source_output_seconds_exact": "65536/11025"}`

计量条件：

- The legacy stage matrix subtotal is preserved; audio_supply includes the unfolded stages and added Omni codec graph. This is not a runnable-model/full-request total. Matrix weight elements exclude embeddings, norms and biases and do not replace complete model parameters. element_bytes is a uniform operand/KV comparison precision, not an assertion of every runtime dtype.
- Transformer causal work uses valid pairs; logical KV uses explicit bytes per element, not a claim about backend accumulation, cache allocation, FP8 support or HBM. MoE uses top-k selected row totals; resident expert matrix count uses all experts.
- Text-token and acoustic-frame axes are independent. Omni code predictor is reset each frame, 2-token prefill then 14 singleton calls: 15 residual outputs but 16 processed positions and 16 output-head rows. Fish primes fast AR once with slow hidden and discards its logits, then executes 9 sampled residual steps: 10 fast calls, not 9.
- Omni Talker includes shared SwiGLU and its scalar output gate projection. ResizeMLP matrix work is counted for the declared text rows; actual special-token packing, speaker/tts prompts and termination are not simulated.
- Omni code2wav pre-transformer uses a 72-position causal window. Its ConvTranspose crop formula is audited separately: both pinned v4.57.1 and inspected current official source crop kernel-stride from both ends. For this config each whole chunk yields 1920*frames-555 samples, unlike nominal 1920*frames; this is source geometry, not a measured waveform or corrected implementation.
- Fish codec uses 44100/(512*4)=21.533203125 frames/s, not exactly 21. The official codec YAML has one semantic codebook of 4096 and nine residual codebooks of 1024, while Fast AR logits have width 4096; logits vocabulary width must not be silently changed to codec size. The locked RVQ.decode clamps residual indices to 1023 and semantic indices to 4095; integer clamp and lookup are included separately.
- Updated execution ledger adds declared Transformer scalar work, full Omni non-transformer codec conv/Snake/ConvNeXt operations, operator interfaces and ordered frame/codebook DAG. Missing remain uncounted token preparation and sampling, multi-chunk execution, complete runtime conversions/allocator/placement and measured latency/quality. No marketing parameter label is used as an exact parameter count.

固定来源：

- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)，SHA256 `809eaeb4d40cb0e59965a85b5f85ddc07e9ab7b6cdae84972c711f8cdadec296`。
- [research/generative-audio-analysis/transformers/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/configuration_qwen3_omni_moe.py)，SHA256 `779bf4b816425448d5d3a2ffa57928d1c7b7c10e2d66b09371fceaee62bcbf89`。
- [research/generative-audio-analysis/fish/fish_speech/models/text2semantic/llama.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/text2semantic/llama.py)，SHA256 `b7dc3c039ddcbc05e445293e5d4babb1e80340b8a2944747fab0cf44c0919852`。
- [research/generative-audio-analysis/fish/fish_speech/models/text2semantic/inference.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/text2semantic/inference.py)，SHA256 `9c85ce70e93dd990ac53a0831bf6d909d74eb434de5608f54fe00bfc129d4cae`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/modded_dac.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/modded_dac.py)，SHA256 `a08407421ee85d8af28377d6a14d989b5a17a985c9719f8b5701cd0a845840c0`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/inference.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/inference.py)，SHA256 `a34210e04904a2be93eb09c46878e740837661318a40ee0e9070148ce1401e60`。
- [research/generative-audio-analysis/fish/fish_speech/models/dac/rvq.py](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/models/dac/rvq.py)，SHA256 `a4d38e529846473c712dd1b2f5eaa889eb0233fd56228799c168060f335c0246`。
- [research/generative-audio-analysis/fish/fish_speech/configs/modded_dac_vq.yaml](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/fish_speech/configs/modded_dac_vq.yaml)，SHA256 `73321408579c372149620d877f0dfb841cf70465758a535f7243e1cb6553d56a`。
- [research/generative-audio-analysis/transformers-current/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py)，SHA256 `0ec28dd7714f09de8749edc958c25c0ebcc0628c9c2a0dca3abd905e7cddab04`。
- [research/generative-audio-analysis/fish/pyproject.toml](https://raw.githubusercontent.com/fishaudio/fish-speech/befe4001745417f8c42131739d862b8a6fdbd15a/pyproject.toml)，SHA256 `7fdd2e4f01746b884b368b7003c315d285cf86a36031035b3f28d7aafe68ea15`。
- [research/generative-audio-analysis/descript/dac/nn/quantize.py](https://raw.githubusercontent.com/descriptinc/descript-audio-codec/c7cfc5d2647e26471dc394f95846a0830e7bec34/dac/nn/quantize.py)，SHA256 `e2dc61f32f6123aa48a0aeb934a0d9a41ea29a5eae8db28119c791885c9f1b07`。
- [research/generative-audio-analysis/descript/dac/nn/layers.py](https://raw.githubusercontent.com/descriptinc/descript-audio-codec/c7cfc5d2647e26471dc394f95846a0830e7bec34/dac/nn/layers.py)，SHA256 `ec2649649d787b166a138d5ad9dcd585aeabbcd93670771b30cbbbab731c4b63`。
- [sources/fish-audio-s2-pro/LICENSE.md](https://huggingface.co/fishaudio/s2-pro/resolve/1de9996b6be38b745688de084d87a5633f714e4e/LICENSE.md)，SHA256 `aa7d9206e9d710590987a3636934f643529c00cd490323594e6206aaa0c32d80`。
- [sources/fish-audio-s2-pro/README.md](https://huggingface.co/fishaudio/s2-pro/resolve/1de9996b6be38b745688de084d87a5633f714e4e/README.md)，SHA256 `3c2d78af0f3991ef6047272d4df18f204b4340e1e5fcc975d0e720d4312c4b29`。
- [configs/models/fish-audio-s2-pro/config.json](https://huggingface.co/fishaudio/s2-pro/resolve/1de9996b6be38b745688de084d87a5633f714e4e/config.json)，SHA256 `261b519a2a9576710fc8533a77297fae007f0e7b3aa28a217f8352b7f32fe993`。
- [sources/fish-audio-s2-pro/tokenizer_config.json](https://huggingface.co/fishaudio/s2-pro/resolve/1de9996b6be38b745688de084d87a5633f714e4e/tokenizer_config.json)，SHA256 `b8d149343ae425b0da67e6708686aceb51be7815d9792f265fc12ff04d5e9856`。
