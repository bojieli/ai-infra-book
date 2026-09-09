# audio-generation-matrix-and-codebook-ledger — qwen3-omni-30b-a3b-instruct

输入：`{"audio_history": 32, "batch": 4, "fish_prompt_tokens": 0, "frames": 12, "kv_element_bytes": 2, "operand_element_bytes": 2, "text_history": 128, "text_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| accounted_transformer_and_bridge_matrix_flops | 560,647,766,016 |
| full_model_parameters | `null` |
| full_generation_flops | `null` |
| full_codec_flops | `null` |
| predicted_latency_seconds | `null` |

音频阶段供给：`{"effective_rates": {"matrix": null, "interface": null, "scalar": null}, "accounted_work_totals": {"matrix_flops": 790541662464, "accounted_interface_bytes": 322245340146, "accounted_scalar_flops": 1264808532}, "accounted_serial_critical_path_lower_bound_seconds_exact": null, "full_request_latency_seconds": null, "first_audio_latency_seconds": null, "prompt_scope": "Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.", "duration_basis_seconds_exact": "1499/1600", "required_matrix_flops_per_second_exact": "1264866659942400/1499", "required_accounted_interface_bytes_per_second_exact": "515592544233600/1499", "required_accounted_scalar_flops_per_second_exact": "2023693651200/1499", "interpretation": "Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies."}`

| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |
| --- | --- | ---: | ---: | --- |
| code_embedding_lookup | embedding | 0 | 0 | 1572864/6144/1572864 |
| code_embedding_mean | embedding | 0 | 786432 | 0/1572864/98304 |
| upsample_0 | conv_transpose1d | 201326592 | 98304 | 4196352/98304/196608 |
| upsample_0_crop_contiguous | copy | 0 | 0 | 0/196608/196608 |
| upsample_0_depthwise | causal_conv1d | 1376256 | 98304 | 16384/196608/196608 |
| upsample_0_layernorm | normalization | 0 | 688224 | 4096/196608/196608 |
| upsample_0_pointwise1 | linear | 805306368 | 393216 | 8396800/196608/786432 |
| upsample_0_gelu | activation | 0 | 0 | 0/786432/786432 |
| upsample_0_pointwise2 | linear | 805306368 | 98304 | 8390656/786432/196608 |
| upsample_0_gamma_residual | residual | 0 | 196608 | 2048/393216/196608 |
| upsample_1 | conv_transpose1d | 402653184 | 196608 | 4196352/196608/393216 |
| upsample_1_crop_contiguous | copy | 0 | 0 | 0/393216/393216 |
| upsample_1_depthwise | causal_conv1d | 2752512 | 196608 | 16384/393216/393216 |
| upsample_1_layernorm | normalization | 0 | 1376448 | 4096/393216/393216 |
| upsample_1_pointwise1 | linear | 1610612736 | 786432 | 8396800/393216/1572864 |
| upsample_1_gelu | activation | 0 | 0 | 0/1572864/1572864 |
| upsample_1_pointwise2 | linear | 1610612736 | 196608 | 8390656/1572864/393216 |
| upsample_1_gamma_residual | residual | 0 | 393216 | 2048/786432/393216 |
| decoder_input | causal_conv1d | 4227858432 | 294912 | 22023168/393216/589824 |
| decoder_0_snake | snake_beta | 0 | 1182720 | 6144/589824/589824 |
| decoder_0_upsample | conv_transpose1d | 7247757312 | 1204224 | 37750272/589824/2408448 |
| decoder_0_upsample_crop_contiguous | copy | 0 | 0 | 0/2310144/2310144 |
| decoder_0_residual_d1_snake1 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d1_conv1 | causal_conv1d | 12419334144 | 1155072 | 8259072/2310144/2310144 |
| decoder_0_residual_d1_snake2 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d1_conv2 | causal_conv1d | 1774190592 | 1155072 | 1181184/2310144/2310144 |
| decoder_0_residual_d1_add | residual | 0 | 1155072 | 0/4620288/2310144 |
| decoder_0_residual_d3_snake1 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d3_conv1 | causal_conv1d | 12419334144 | 1155072 | 8259072/2310144/2310144 |
| decoder_0_residual_d3_snake2 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d3_conv2 | causal_conv1d | 1774190592 | 1155072 | 1181184/2310144/2310144 |
| decoder_0_residual_d3_add | residual | 0 | 1155072 | 0/4620288/2310144 |
| decoder_0_residual_d9_snake1 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d9_conv1 | causal_conv1d | 12419334144 | 1155072 | 8259072/2310144/2310144 |
| decoder_0_residual_d9_snake2 | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_0_residual_d9_conv2 | causal_conv1d | 1774190592 | 1155072 | 1181184/2310144/2310144 |
| decoder_0_residual_d9_add | residual | 0 | 1155072 | 0/4620288/2310144 |
| decoder_1_snake | snake_beta | 0 | 4621824 | 3072/2310144/2310144 |
| decoder_1_upsample | conv_transpose1d | 8870952960 | 2895360 | 5899008/2310144/5790720 |
| decoder_1_upsample_crop_contiguous | copy | 0 | 0 | 0/5760000/5760000 |
| decoder_1_residual_d1_snake1 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d1_conv1 | causal_conv1d | 15482880000 | 2880000 | 2065152/5760000/5760000 |
| decoder_1_residual_d1_snake2 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d1_conv2 | causal_conv1d | 2211840000 | 2880000 | 295680/5760000/5760000 |
| decoder_1_residual_d1_add | residual | 0 | 2880000 | 0/11520000/5760000 |
| decoder_1_residual_d3_snake1 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d3_conv1 | causal_conv1d | 15482880000 | 2880000 | 2065152/5760000/5760000 |
| decoder_1_residual_d3_snake2 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d3_conv2 | causal_conv1d | 2211840000 | 2880000 | 295680/5760000/5760000 |
| decoder_1_residual_d3_add | residual | 0 | 2880000 | 0/11520000/5760000 |
| decoder_1_residual_d9_snake1 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d9_conv1 | causal_conv1d | 15482880000 | 2880000 | 2065152/5760000/5760000 |
| decoder_1_residual_d9_snake2 | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_1_residual_d9_conv2 | causal_conv1d | 2211840000 | 2880000 | 295680/5760000/5760000 |
| decoder_1_residual_d9_add | residual | 0 | 2880000 | 0/11520000/5760000 |
| decoder_2_snake | snake_beta | 0 | 11520768 | 1536/5760000/5760000 |
| decoder_2_upsample | conv_transpose1d | 8847360000 | 5763072 | 1180032/5760000/11526144 |
| decoder_2_upsample_crop_contiguous | copy | 0 | 0 | 0/11513856/11513856 |
| decoder_2_residual_d1_snake1 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d1_conv1 | causal_conv1d | 15474622464 | 5756928 | 516480/11513856/11513856 |
| decoder_2_residual_d1_snake2 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d1_conv2 | causal_conv1d | 2210660352 | 5756928 | 74112/11513856/11513856 |
| decoder_2_residual_d1_add | residual | 0 | 5756928 | 0/23027712/11513856 |
| decoder_2_residual_d3_snake1 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d3_conv1 | causal_conv1d | 15474622464 | 5756928 | 516480/11513856/11513856 |
| decoder_2_residual_d3_snake2 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d3_conv2 | causal_conv1d | 2210660352 | 5756928 | 74112/11513856/11513856 |
| decoder_2_residual_d3_add | residual | 0 | 5756928 | 0/23027712/11513856 |
| decoder_2_residual_d9_snake1 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d9_conv1 | causal_conv1d | 15474622464 | 5756928 | 516480/11513856/11513856 |
| decoder_2_residual_d9_snake2 | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_2_residual_d9_conv2 | causal_conv1d | 2210660352 | 5756928 | 74112/11513856/11513856 |
| decoder_2_residual_d9_add | residual | 0 | 5756928 | 0/23027712/11513856 |
| decoder_3_snake | snake_beta | 0 | 23028096 | 768/11513856/11513856 |
| decoder_3_upsample | conv_transpose1d | 6631981056 | 8636544 | 221376/11513856/17273088 |
| decoder_3_upsample_crop_contiguous | copy | 0 | 0 | 0/17268480/17268480 |
| decoder_3_residual_d1_snake1 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d1_conv1 | causal_conv1d | 11604418560 | 8634240 | 129216/17268480/17268480 |
| decoder_3_residual_d1_snake2 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d1_conv2 | causal_conv1d | 1657774080 | 8634240 | 18624/17268480/17268480 |
| decoder_3_residual_d1_add | residual | 0 | 8634240 | 0/34536960/17268480 |
| decoder_3_residual_d3_snake1 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d3_conv1 | causal_conv1d | 11604418560 | 8634240 | 129216/17268480/17268480 |
| decoder_3_residual_d3_snake2 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d3_conv2 | causal_conv1d | 1657774080 | 8634240 | 18624/17268480/17268480 |
| decoder_3_residual_d3_add | residual | 0 | 8634240 | 0/34536960/17268480 |
| decoder_3_residual_d9_snake1 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d9_conv1 | causal_conv1d | 11604418560 | 8634240 | 129216/17268480/17268480 |
| decoder_3_residual_d9_snake2 | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| decoder_3_residual_d9_conv2 | causal_conv1d | 1657774080 | 8634240 | 18624/17268480/17268480 |
| decoder_3_residual_d9_add | residual | 0 | 8634240 | 0/34536960/17268480 |
| output_snake | snake_beta | 0 | 34537152 | 384/17268480/17268480 |
| output_conv | causal_conv1d | 120879360 | 89940 | 1346/17268480/179880 |
| wave_clamp | activation | 0 | 0 | 0/179880/179880 |

阶段：thinker_text

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 64 | 2048 | 4096 | 48 | 51539607552 |
| k | 64 | 2048 | 512 | 48 | 6442450944 |
| v | 64 | 2048 | 512 | 48 | 6442450944 |
| o | 64 | 4096 | 2048 | 48 | 51539607552 |
| router | 64 | 2048 | 128 | 48 | 1610612736 |
| expert_gate | 512 | 2048 | 768 | 48 | 77309411328 |
| expert_up | 512 | 2048 | 768 | 48 | 77309411328 |
| expert_down | 512 | 768 | 2048 | 48 | 77309411328 |
| output_head | 64 | 2048 | 152064 | 1 | 39862665216 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 389365628928, "qk_matrix_flops": 3435134976, "pv_matrix_flops": 3435134976, "matrix_flops": 396235898880, "matrix_weight_elements": 30221008896, "kv_bytes_per_position_per_request": 98304, "kv_retained_logical_bytes": 56623104, "processed_rows": 64, "valid_attention_pairs_all_invocations": 8736, "invocations": 16, "accounted_scalar_flops": 349564992, "special_ops": {"rsqrt": 116800, "rope_sign_negation": 7077888, "attention_exp": 13418496, "attention_max_compare": 13320192, "sigmoid": 18874368, "router_exp": 393216, "router_max_compare": 390144}, "matrix_weight_interface_bytes": 271287582720, "matrix_activation_read_bytes": 314834944, "matrix_activation_write_bytes": 240451584, "attention_logical_interface_bytes": 962789376, "accounted_nonmatrix_interface_bytes": 490340352, "accounted_interface_bytes": 273295998976}`

阶段：talker_temporal

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 48 | 1024 | 2048 | 20 | 4026531840 |
| k | 48 | 1024 | 256 | 20 | 503316480 |
| v | 48 | 1024 | 256 | 20 | 503316480 |
| o | 48 | 2048 | 1024 | 20 | 4026531840 |
| router | 48 | 1024 | 128 | 20 | 251658240 |
| expert_gate | 288 | 1024 | 384 | 20 | 4529848320 |
| expert_up | 288 | 1024 | 384 | 20 | 4529848320 |
| expert_down | 288 | 384 | 1024 | 20 | 4529848320 |
| shared_gate | 48 | 1024 | 768 | 20 | 1509949440 |
| shared_up | 48 | 1024 | 768 | 20 | 1509949440 |
| shared_down | 48 | 768 | 1024 | 20 | 1509949440 |
| shared_expert_output_gate | 48 | 1024 | 1 | 20 | 1966080 |
| output_head | 48 | 1024 | 3072 | 1 | 301989888 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 27734704128, "qk_matrix_flops": 151388160, "pv_matrix_flops": 151388160, "matrix_flops": 28037480448, "matrix_weight_elements": 3167244288, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 3604480, "processed_rows": 48, "valid_attention_pairs_all_invocations": 1848, "invocations": 12, "accounted_scalar_flops": 46935216, "special_ops": {"rsqrt": 19248, "rope_sign_negation": 1105920, "attention_exp": 591360, "attention_max_compare": 576000, "sigmoid": 2950080, "router_exp": 122880, "router_max_compare": 121920}, "matrix_weight_interface_bytes": 17125834752, "matrix_activation_read_bytes": 47284224, "matrix_activation_write_bytes": 32982912, "attention_logical_interface_bytes": 48076800, "accounted_nonmatrix_interface_bytes": 71030784, "accounted_interface_bytes": 17325209472}`

阶段：code_predictor_reset_each_frame

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 768 | 1024 | 2048 | 5 | 16106127360 |
| k | 768 | 1024 | 1024 | 5 | 8053063680 |
| v | 768 | 1024 | 1024 | 5 | 8053063680 |
| o | 768 | 2048 | 1024 | 5 | 16106127360 |
| ffn_gate | 768 | 1024 | 3072 | 5 | 24159191040 |
| ffn_up | 768 | 1024 | 3072 | 5 | 24159191040 |
| ffn_down | 768 | 3072 | 1024 | 5 | 24159191040 |
| output_head | 768 | 1024 | 2048 | 1 | 3221225472 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 124017180672, "qk_matrix_flops": 133693440, "pv_matrix_flops": 133693440, "matrix_flops": 124284567552, "matrix_weight_elements": 110100480, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 1310720, "processed_rows": 768, "valid_attention_pairs_all_invocations": 6528, "invocations": 180, "accounted_scalar_flops": 150763776, "special_ops": {"rsqrt": 100608, "rope_sign_negation": 5898240, "attention_exp": 522240, "attention_max_compare": 460800, "sigmoid": 11796480}, "matrix_weight_interface_bytes": 29066526720, "matrix_activation_read_bytes": 80216064, "matrix_activation_write_bytes": 97517568, "attention_logical_interface_bytes": 167239680, "accounted_nonmatrix_interface_bytes": 302696448, "accounted_interface_bytes": 29714196480}`

阶段：code2wav_pre_transformer

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 48 | 1024 | 1024 | 8 | 805306368 |
| k | 48 | 1024 | 1024 | 8 | 805306368 |
| v | 48 | 1024 | 1024 | 8 | 805306368 |
| o | 48 | 1024 | 1024 | 8 | 805306368 |
| ffn_gate | 48 | 1024 | 3072 | 8 | 2415919104 |
| ffn_up | 48 | 1024 | 3072 | 8 | 2415919104 |
| ffn_down | 48 | 3072 | 1024 | 8 | 2415919104 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 10468982784, "qk_matrix_flops": 5111808, "pv_matrix_flops": 5111808, "matrix_flops": 10479206400, "matrix_weight_elements": 109051904, "kv_bytes_per_position_per_request": 32768, "kv_retained_logical_bytes": 0, "processed_rows": 48, "valid_attention_pairs_all_invocations": 312, "invocations": 1, "accounted_scalar_flops": 9788208, "special_ops": {"rsqrt": 816, "rope_sign_negation": 393216, "attention_exp": 39936, "attention_max_compare": 33792, "sigmoid": 1179648}, "matrix_weight_interface_bytes": 218103808, "matrix_activation_read_bytes": 7077888, "matrix_activation_write_bytes": 8650752, "attention_logical_interface_bytes": 11956224, "accounted_nonmatrix_interface_bytes": 26474496, "accounted_interface_bytes": 272263168}`

码本循环：`{"primary_audio_codes": 12, "residual_codes": 180, "predictor_calls": 180, "predictor_processed_positions": 192, "predictor_prefill_positions": 2, "predictor_single_position_calls_per_frame": 14, "predictor_cache_reset_per_frame": true}`

codec时间轴：`{"sample_rate": 24000, "nominal_samples_per_frame": 1920, "nominal_frames_per_second_exact": "25/2", "source_output_samples": 22485, "nominal_output_samples": 23040, "source_output_seconds_exact": "1499/1600", "nominal_output_seconds_exact": "24/25", "crop_length_discrepancy_samples": 555, "convtranspose_lengths": [{"input_length": 12, "stride": 2, "kernel": 2, "raw_length": 24, "crop_each_side": 0, "output_length": 24}, {"input_length": 24, "stride": 2, "kernel": 2, "raw_length": 48, "crop_each_side": 0, "output_length": 48}, {"input_length": 48, "stride": 8, "kernel": 16, "raw_length": 392, "crop_each_side": 8, "output_length": 376}, {"input_length": 376, "stride": 5, "kernel": 10, "raw_length": 1885, "crop_each_side": 5, "output_length": 1875}, {"input_length": 1875, "stride": 4, "kernel": 8, "raw_length": 7504, "crop_each_side": 4, "output_length": 7496}, {"input_length": 7496, "stride": 3, "kernel": 6, "raw_length": 22491, "crop_each_side": 3, "output_length": 22485}], "code2wav_chunk_calls": 1}`

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
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/qwen3-omni-30b-a3b-instruct/README.md](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/README.md)，SHA256 `0e44065c4c4a27071f7239afd5b5a33af5bc2e437dd7ea9950e51aafabfde3df`。
- [configs/models/qwen3-omni-30b-a3b-instruct/config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/config.json)，SHA256 `eab5093d47807aaf894119506b238b2b1cee70d08456e894fee9a012d88f2e0d`。
- [sources/qwen3-omni-30b-a3b-instruct/generation_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/generation_config.json)，SHA256 `7fa40989be8e43c078907810c41c25d33747523afce3d5a34d5850f930c886cb`。
- [sources/qwen3-omni-30b-a3b-instruct/preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/preprocessor_config.json)，SHA256 `b10e27fd4542cf89ec7145942b87f3e65408d4e9f9d031a29acdd293c15fb3fc`。
- [sources/qwen3-omni-30b-a3b-instruct/tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/tokenizer_config.json)，SHA256 `dc3c31c3bdaedd5016382bb3cbe07323026775ad51f5a4fb564505992ae4a670`。
