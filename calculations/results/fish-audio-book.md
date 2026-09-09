# audio-generation-matrix-and-codebook-ledger — fish-audio-s2-pro

输入：`{"audio_history": 32, "batch": 1, "fish_prompt_tokens": 0, "frames": 12, "kv_element_bytes": 2, "operand_element_bytes": 2, "text_history": 128, "text_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| accounted_transformer_and_bridge_matrix_flops | 196,491,214,848 |
| full_model_parameters | `null` |
| full_generation_flops | `null` |
| full_codec_flops | `null` |
| predicted_latency_seconds | `null` |

音频阶段供给：`{"effective_rates": {"matrix": null, "interface": null, "scalar": null}, "accounted_work_totals": {"matrix_flops": 277664415744, "accounted_interface_bytes": 197652105060, "accounted_scalar_flops": 470193816}, "accounted_serial_critical_path_lower_bound_seconds_exact": null, "full_request_latency_seconds": null, "first_audio_latency_seconds": null, "prompt_scope": "Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.", "duration_basis_seconds_exact": "2048/3675", "required_matrix_flops_per_second_exact": "498250355400", "required_accounted_interface_bytes_per_second_exact": "181592871523875/512", "required_accounted_scalar_flops_per_second_exact": "215995284225/256", "interpretation": "Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies."}`

| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |
| --- | --- | ---: | ---: | --- |
| semantic_index_clamp | index | 0 | 0 | 0/96/96 |
| semantic_book_0_lookup | embedding | 0 | 0 | 192/96/192 |
| semantic_book_0_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| semantic_book_0_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| semantic_book_0_accumulate | reduce | 0 | 12288 | 0/24576/24576 |
| semantic_unused_latent_cat | copy | 0 | 0 | 0/192/192 |
| residual_index_clamp | index | 0 | 0 | 0/864/864 |
| residual_book_0_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_0_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_0_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_0_accumulate | reduce | 0 | 12288 | 0/24576/24576 |
| residual_book_1_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_1_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_1_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_1_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_2_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_2_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_2_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_2_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_3_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_3_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_3_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_3_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_4_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_4_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_4_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_4_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_5_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_5_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_5_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_5_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_6_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_6_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_6_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_6_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_7_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_7_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_7_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_7_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_book_8_lookup | embedding | 0 | 0 | 192/96/192 |
| residual_book_8_out_proj_weight_norm | weight_normalization | 0 | 24576 | 0/18432/16384 |
| residual_book_8_out_proj | conv1d | 196608 | 12288 | 18432/192/24576 |
| residual_book_8_accumulate | reduce | 0 | 12288 | 0/49152/24576 |
| residual_unused_latent_cat | copy | 0 | 0 | 0/1728/1728 |
| semantic_residual_add | residual | 0 | 12288 | 0/49152/24576 |
| rvq_post_transformer | transformer | 2619801600 | 2447052 | 218103808/13590528/0 |
| upsample_0 | conv_transpose1d | 50331648 | 24576 | 4196352/24576/49152 |
| upsample_0_crop_contiguous | copy | 0 | 0 | 0/49152/49152 |
| upsample_0_depthwise | causal_conv1d | 344064 | 24576 | 16384/49152/49152 |
| upsample_0_layernorm | normalization | 0 | 172056 | 4096/49152/49152 |
| upsample_0_pointwise1 | linear | 201326592 | 98304 | 8396800/49152/196608 |
| upsample_0_gelu | activation | 0 | 0 | 0/196608/196608 |
| upsample_0_pointwise2 | linear | 201326592 | 24576 | 8390656/196608/49152 |
| upsample_0_gamma_residual | residual | 0 | 49152 | 2048/98304/49152 |
| upsample_1 | conv_transpose1d | 100663296 | 49152 | 4196352/49152/98304 |
| upsample_1_crop_contiguous | copy | 0 | 0 | 0/98304/98304 |
| upsample_1_depthwise | causal_conv1d | 688128 | 49152 | 16384/98304/98304 |
| upsample_1_layernorm | normalization | 0 | 344112 | 4096/98304/98304 |
| upsample_1_pointwise1 | linear | 402653184 | 196608 | 8396800/98304/393216 |
| upsample_1_gelu | activation | 0 | 0 | 0/393216/393216 |
| upsample_1_pointwise2 | linear | 402653184 | 49152 | 8390656/393216/98304 |
| upsample_1_gamma_residual | residual | 0 | 98304 | 2048/196608/98304 |
| decoder_input_weight_norm | weight_normalization | 0 | 33030144 | 0/22023168/22020096 |
| decoder_input | causal_conv1d | 1056964608 | 73728 | 22023168/98304/147456 |
| decoder_0_snake | snake1d | 0 | 297984 | 3072/147456/147456 |
| decoder_0_upsample_weight_norm | weight_normalization | 0 | 56623104 | 0/37751808/37748736 |
| decoder_0_upsample | conv_transpose1d | 1811939328 | 301056 | 37750272/147456/602112 |
| decoder_0_upsample_crop_contiguous | copy | 0 | 0 | 0/589824/589824 |
| decoder_0_residual_d1_snake1 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d1_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d1_conv1 | causal_conv1d | 3170893824 | 294912 | 8259072/589824/589824 |
| decoder_0_residual_d1_snake2 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d1_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d1_conv2 | causal_conv1d | 452984832 | 294912 | 1181184/589824/589824 |
| decoder_0_residual_d1_add | residual | 0 | 294912 | 0/1179648/589824 |
| decoder_0_residual_d3_snake1 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d3_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d3_conv1 | causal_conv1d | 3170893824 | 294912 | 8259072/589824/589824 |
| decoder_0_residual_d3_snake2 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d3_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d3_conv2 | causal_conv1d | 452984832 | 294912 | 1181184/589824/589824 |
| decoder_0_residual_d3_add | residual | 0 | 294912 | 0/1179648/589824 |
| decoder_0_residual_d9_snake1 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d9_conv1_weight_norm | weight_normalization | 0 | 12386304 | 0/8259072/8257536 |
| decoder_0_residual_d9_conv1 | causal_conv1d | 3170893824 | 294912 | 8259072/589824/589824 |
| decoder_0_residual_d9_snake2 | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_0_residual_d9_conv2_weight_norm | weight_normalization | 0 | 1769472 | 0/1181184/1179648 |
| decoder_0_residual_d9_conv2 | causal_conv1d | 452984832 | 294912 | 1181184/589824/589824 |
| decoder_0_residual_d9_add | residual | 0 | 294912 | 0/1179648/589824 |
| decoder_1_snake | snake1d | 0 | 1181184 | 1536/589824/589824 |
| decoder_1_upsample_weight_norm | weight_normalization | 0 | 14155776 | 0/9438720/9437184 |
| decoder_1_upsample | conv_transpose1d | 3623878656 | 1182720 | 9437952/589824/2365440 |
| decoder_1_upsample_crop_contiguous | copy | 0 | 0 | 0/2359296/2359296 |
| decoder_1_residual_d1_snake1 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d1_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d1_conv1 | causal_conv1d | 6341787648 | 1179648 | 2065152/2359296/2359296 |
| decoder_1_residual_d1_snake2 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d1_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d1_conv2 | causal_conv1d | 905969664 | 1179648 | 295680/2359296/2359296 |
| decoder_1_residual_d1_add | residual | 0 | 1179648 | 0/4718592/2359296 |
| decoder_1_residual_d3_snake1 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d3_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d3_conv1 | causal_conv1d | 6341787648 | 1179648 | 2065152/2359296/2359296 |
| decoder_1_residual_d3_snake2 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d3_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d3_conv2 | causal_conv1d | 905969664 | 1179648 | 295680/2359296/2359296 |
| decoder_1_residual_d3_add | residual | 0 | 1179648 | 0/4718592/2359296 |
| decoder_1_residual_d9_snake1 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d9_conv1_weight_norm | weight_normalization | 0 | 3096576 | 0/2065152/2064384 |
| decoder_1_residual_d9_conv1 | causal_conv1d | 6341787648 | 1179648 | 2065152/2359296/2359296 |
| decoder_1_residual_d9_snake2 | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_1_residual_d9_conv2_weight_norm | weight_normalization | 0 | 442368 | 0/295680/294912 |
| decoder_1_residual_d9_conv2 | causal_conv1d | 905969664 | 1179648 | 295680/2359296/2359296 |
| decoder_1_residual_d9_add | residual | 0 | 1179648 | 0/4718592/2359296 |
| decoder_2_snake | snake1d | 0 | 4719360 | 768/2359296/2359296 |
| decoder_2_upsample_weight_norm | weight_normalization | 0 | 1769472 | 0/1180416/1179648 |
| decoder_2_upsample | conv_transpose1d | 3623878656 | 2360064 | 1180032/2359296/4720128 |
| decoder_2_upsample_crop_contiguous | copy | 0 | 0 | 0/4718592/4718592 |
| decoder_2_residual_d1_snake1 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d1_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d1_conv1 | causal_conv1d | 6341787648 | 2359296 | 516480/4718592/4718592 |
| decoder_2_residual_d1_snake2 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d1_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d1_conv2 | causal_conv1d | 905969664 | 2359296 | 74112/4718592/4718592 |
| decoder_2_residual_d1_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| decoder_2_residual_d3_snake1 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d3_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d3_conv1 | causal_conv1d | 6341787648 | 2359296 | 516480/4718592/4718592 |
| decoder_2_residual_d3_snake2 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d3_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d3_conv2 | causal_conv1d | 905969664 | 2359296 | 74112/4718592/4718592 |
| decoder_2_residual_d3_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| decoder_2_residual_d9_snake1 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d9_conv1_weight_norm | weight_normalization | 0 | 774144 | 0/516480/516096 |
| decoder_2_residual_d9_conv1 | causal_conv1d | 6341787648 | 2359296 | 516480/4718592/4718592 |
| decoder_2_residual_d9_snake2 | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_2_residual_d9_conv2_weight_norm | weight_normalization | 0 | 110592 | 0/74112/73728 |
| decoder_2_residual_d9_conv2 | causal_conv1d | 905969664 | 2359296 | 74112/4718592/4718592 |
| decoder_2_residual_d9_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| decoder_3_snake | snake1d | 0 | 9437568 | 384/4718592/4718592 |
| decoder_3_upsample_weight_norm | weight_normalization | 0 | 221184 | 0/147840/147456 |
| decoder_3_upsample | conv_transpose1d | 1811939328 | 2359488 | 147648/4718592/4718976 |
| decoder_3_upsample_crop_contiguous | copy | 0 | 0 | 0/4718592/4718592 |
| decoder_3_residual_d1_snake1 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d1_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d1_conv1 | causal_conv1d | 3170893824 | 2359296 | 129216/4718592/4718592 |
| decoder_3_residual_d1_snake2 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d1_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d1_conv2 | causal_conv1d | 452984832 | 2359296 | 18624/4718592/4718592 |
| decoder_3_residual_d1_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| decoder_3_residual_d3_snake1 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d3_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d3_conv1 | causal_conv1d | 3170893824 | 2359296 | 129216/4718592/4718592 |
| decoder_3_residual_d3_snake2 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d3_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d3_conv2 | causal_conv1d | 452984832 | 2359296 | 18624/4718592/4718592 |
| decoder_3_residual_d3_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| decoder_3_residual_d9_snake1 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d9_conv1_weight_norm | weight_normalization | 0 | 193536 | 0/129216/129024 |
| decoder_3_residual_d9_conv1 | causal_conv1d | 3170893824 | 2359296 | 129216/4718592/4718592 |
| decoder_3_residual_d9_snake2 | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| decoder_3_residual_d9_conv2_weight_norm | weight_normalization | 0 | 27648 | 0/18624/18432 |
| decoder_3_residual_d9_conv2 | causal_conv1d | 452984832 | 2359296 | 18624/4718592/4718592 |
| decoder_3_residual_d9_add | residual | 0 | 2359296 | 0/9437184/4718592 |
| output_snake | snake1d | 0 | 9437376 | 192/4718592/4718592 |
| output_conv_weight_norm | weight_normalization | 0 | 2016 | 0/1346/1344 |
| output_conv | causal_conv1d | 33030144 | 24576 | 1346/4718592/49152 |
| wave_tanh | activation | 0 | 0 | 0/49152/49152 |

阶段：slow_ar

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 12 | 2560 | 4096 | 36 | 9059696640 |
| k | 12 | 2560 | 1024 | 36 | 2264924160 |
| v | 12 | 2560 | 1024 | 36 | 2264924160 |
| o | 12 | 4096 | 2560 | 36 | 9059696640 |
| ffn_gate | 12 | 2560 | 9728 | 36 | 21516779520 |
| ffn_up | 12 | 2560 | 9728 | 36 | 21516779520 |
| ffn_down | 12 | 9728 | 2560 | 36 | 21516779520 |
| output_head | 12 | 2560 | 155776 | 1 | 9570877440 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 96770457600, "qk_matrix_flops": 136249344, "pv_matrix_flops": 136249344, "matrix_flops": 97042956288, "matrix_weight_elements": 4032102400, "kv_bytes_per_position_per_request": 147456, "kv_retained_logical_bytes": 6488064, "processed_rows": 12, "valid_attention_pairs_all_invocations": 462, "invocations": 12, "accounted_scalar_flops": 37203180, "special_ops": {"rsqrt": 18156, "rope_sign_negation": 1105920, "attention_exp": 532224, "attention_max_compare": 518400, "sigmoid": 4202496}, "matrix_weight_interface_bytes": 96770457600, "matrix_activation_read_bytes": 23064576, "matrix_activation_write_bytes": 30280704, "attention_logical_interface_bytes": 77331456, "accounted_nonmatrix_interface_bytes": 89017344, "accounted_interface_bytes": 96990151680}`

阶段：fast_ar_reset_each_frame

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 120 | 2560 | 4096 | 4 | 10066329600 |
| k | 120 | 2560 | 1024 | 4 | 2516582400 |
| v | 120 | 2560 | 1024 | 4 | 2516582400 |
| o | 120 | 4096 | 2560 | 4 | 10066329600 |
| ffn_gate | 120 | 2560 | 9728 | 4 | 23907532800 |
| ffn_up | 120 | 2560 | 9728 | 4 | 23907532800 |
| ffn_down | 120 | 9728 | 2560 | 4 | 23907532800 |
| output_head | 120 | 2560 | 4096 | 1 | 2516582400 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 99405004800, "qk_matrix_flops": 21626880, "pv_matrix_flops": 21626880, "matrix_flops": 99448258560, "matrix_weight_elements": 414187520, "kv_bytes_per_position_per_request": 16384, "kv_retained_logical_bytes": 163840, "processed_rows": 120, "valid_attention_pairs_all_invocations": 660, "invocations": 120, "accounted_scalar_flops": 30552120, "special_ops": {"rsqrt": 1080, "rope_sign_negation": 1228800, "attention_exp": 84480, "attention_max_compare": 69120, "sigmoid": 4669440}, "matrix_weight_interface_bytes": 99405004800, "matrix_activation_read_bytes": 26173440, "matrix_activation_write_bytes": 30474240, "attention_logical_interface_bytes": 19015680, "accounted_nonmatrix_interface_bytes": 88442880, "accounted_interface_bytes": 99569111040}`

码本循环：`{"primary_audio_codes": 12, "residual_codes": 108, "fast_calls": 120, "fast_discarded_priming_heads": 12, "fast_sampled_residual_heads": 108, "fast_cache_reset_per_frame": true}`

codec时间轴：`{"sample_rate": 44100, "nominal_samples_per_frame": 2048, "nominal_frames_per_second_exact": "11025/512", "nominal_output_samples": 24576, "nominal_output_seconds_exact": "2048/3675", "source_output_samples": 24576, "evidence": "Locked Fish right-only ConvTranspose crops preserve each stride; source decoder produces exactly 2048*frames samples.", "source_output_seconds_exact": "2048/3675"}`

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
