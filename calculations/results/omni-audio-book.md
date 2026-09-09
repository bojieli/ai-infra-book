# audio-generation-matrix-and-codebook-ledger — qwen3-omni-30b-a3b-instruct

输入：`{"audio_history": 32, "batch": 1, "fish_prompt_tokens": 0, "frames": 12, "kv_element_bytes": 2, "operand_element_bytes": 2, "text_history": 128, "text_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| accounted_transformer_and_bridge_matrix_flops | 140,161,941,504 |
| full_model_parameters | `null` |
| full_generation_flops | `null` |
| full_codec_flops | `null` |
| predicted_latency_seconds | `null` |

音频阶段供给：`{"effective_rates": {"matrix": null, "interface": null, "scalar": null}, "accounted_work_totals": {"matrix_flops": 197635415616, "accounted_interface_bytes": 134834833182, "accounted_scalar_flops": 316219557}, "accounted_serial_critical_path_lower_bound_seconds_exact": null, "full_request_latency_seconds": null, "first_audio_latency_seconds": null, "prompt_scope": "Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.", "duration_basis_seconds_exact": "1499/1600", "required_matrix_flops_per_second_exact": "316216664985600/1499", "required_accounted_interface_bytes_per_second_exact": "215735733091200/1499", "required_accounted_scalar_flops_per_second_exact": "505951291200/1499", "interpretation": "Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies."}`

| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |
| --- | --- | ---: | ---: | --- |
| code_embedding_lookup | embedding | 0 | 0 | 393216/1536/393216 |
| code_embedding_mean | embedding | 0 | 196608 | 0/393216/24576 |
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
| decoder_input | causal_conv1d | 1056964608 | 73728 | 22023168/98304/147456 |
| decoder_0_snake | snake_beta | 0 | 297984 | 6144/147456/147456 |
| decoder_0_upsample | conv_transpose1d | 1811939328 | 301056 | 37750272/147456/602112 |
| decoder_0_upsample_crop_contiguous | copy | 0 | 0 | 0/577536/577536 |
| decoder_0_residual_d1_snake1 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d1_conv1 | causal_conv1d | 3104833536 | 288768 | 8259072/577536/577536 |
| decoder_0_residual_d1_snake2 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d1_conv2 | causal_conv1d | 443547648 | 288768 | 1181184/577536/577536 |
| decoder_0_residual_d1_add | residual | 0 | 288768 | 0/1155072/577536 |
| decoder_0_residual_d3_snake1 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d3_conv1 | causal_conv1d | 3104833536 | 288768 | 8259072/577536/577536 |
| decoder_0_residual_d3_snake2 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d3_conv2 | causal_conv1d | 443547648 | 288768 | 1181184/577536/577536 |
| decoder_0_residual_d3_add | residual | 0 | 288768 | 0/1155072/577536 |
| decoder_0_residual_d9_snake1 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d9_conv1 | causal_conv1d | 3104833536 | 288768 | 8259072/577536/577536 |
| decoder_0_residual_d9_snake2 | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_0_residual_d9_conv2 | causal_conv1d | 443547648 | 288768 | 1181184/577536/577536 |
| decoder_0_residual_d9_add | residual | 0 | 288768 | 0/1155072/577536 |
| decoder_1_snake | snake_beta | 0 | 1156608 | 3072/577536/577536 |
| decoder_1_upsample | conv_transpose1d | 2217738240 | 723840 | 5899008/577536/1447680 |
| decoder_1_upsample_crop_contiguous | copy | 0 | 0 | 0/1440000/1440000 |
| decoder_1_residual_d1_snake1 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d1_conv1 | causal_conv1d | 3870720000 | 720000 | 2065152/1440000/1440000 |
| decoder_1_residual_d1_snake2 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d1_conv2 | causal_conv1d | 552960000 | 720000 | 295680/1440000/1440000 |
| decoder_1_residual_d1_add | residual | 0 | 720000 | 0/2880000/1440000 |
| decoder_1_residual_d3_snake1 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d3_conv1 | causal_conv1d | 3870720000 | 720000 | 2065152/1440000/1440000 |
| decoder_1_residual_d3_snake2 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d3_conv2 | causal_conv1d | 552960000 | 720000 | 295680/1440000/1440000 |
| decoder_1_residual_d3_add | residual | 0 | 720000 | 0/2880000/1440000 |
| decoder_1_residual_d9_snake1 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d9_conv1 | causal_conv1d | 3870720000 | 720000 | 2065152/1440000/1440000 |
| decoder_1_residual_d9_snake2 | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_1_residual_d9_conv2 | causal_conv1d | 552960000 | 720000 | 295680/1440000/1440000 |
| decoder_1_residual_d9_add | residual | 0 | 720000 | 0/2880000/1440000 |
| decoder_2_snake | snake_beta | 0 | 2880768 | 1536/1440000/1440000 |
| decoder_2_upsample | conv_transpose1d | 2211840000 | 1440768 | 1180032/1440000/2881536 |
| decoder_2_upsample_crop_contiguous | copy | 0 | 0 | 0/2878464/2878464 |
| decoder_2_residual_d1_snake1 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d1_conv1 | causal_conv1d | 3868655616 | 1439232 | 516480/2878464/2878464 |
| decoder_2_residual_d1_snake2 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d1_conv2 | causal_conv1d | 552665088 | 1439232 | 74112/2878464/2878464 |
| decoder_2_residual_d1_add | residual | 0 | 1439232 | 0/5756928/2878464 |
| decoder_2_residual_d3_snake1 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d3_conv1 | causal_conv1d | 3868655616 | 1439232 | 516480/2878464/2878464 |
| decoder_2_residual_d3_snake2 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d3_conv2 | causal_conv1d | 552665088 | 1439232 | 74112/2878464/2878464 |
| decoder_2_residual_d3_add | residual | 0 | 1439232 | 0/5756928/2878464 |
| decoder_2_residual_d9_snake1 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d9_conv1 | causal_conv1d | 3868655616 | 1439232 | 516480/2878464/2878464 |
| decoder_2_residual_d9_snake2 | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_2_residual_d9_conv2 | causal_conv1d | 552665088 | 1439232 | 74112/2878464/2878464 |
| decoder_2_residual_d9_add | residual | 0 | 1439232 | 0/5756928/2878464 |
| decoder_3_snake | snake_beta | 0 | 5757312 | 768/2878464/2878464 |
| decoder_3_upsample | conv_transpose1d | 1657995264 | 2159136 | 221376/2878464/4318272 |
| decoder_3_upsample_crop_contiguous | copy | 0 | 0 | 0/4317120/4317120 |
| decoder_3_residual_d1_snake1 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d1_conv1 | causal_conv1d | 2901104640 | 2158560 | 129216/4317120/4317120 |
| decoder_3_residual_d1_snake2 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d1_conv2 | causal_conv1d | 414443520 | 2158560 | 18624/4317120/4317120 |
| decoder_3_residual_d1_add | residual | 0 | 2158560 | 0/8634240/4317120 |
| decoder_3_residual_d3_snake1 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d3_conv1 | causal_conv1d | 2901104640 | 2158560 | 129216/4317120/4317120 |
| decoder_3_residual_d3_snake2 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d3_conv2 | causal_conv1d | 414443520 | 2158560 | 18624/4317120/4317120 |
| decoder_3_residual_d3_add | residual | 0 | 2158560 | 0/8634240/4317120 |
| decoder_3_residual_d9_snake1 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d9_conv1 | causal_conv1d | 2901104640 | 2158560 | 129216/4317120/4317120 |
| decoder_3_residual_d9_snake2 | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| decoder_3_residual_d9_conv2 | causal_conv1d | 414443520 | 2158560 | 18624/4317120/4317120 |
| decoder_3_residual_d9_add | residual | 0 | 2158560 | 0/8634240/4317120 |
| output_snake | snake_beta | 0 | 8634432 | 384/4317120/4317120 |
| output_conv | causal_conv1d | 30219840 | 22485 | 1346/4317120/44970 |
| wave_clamp | activation | 0 | 0 | 0/44970/44970 |

阶段：thinker_text

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 16 | 2048 | 4096 | 48 | 12884901888 |
| k | 16 | 2048 | 512 | 48 | 1610612736 |
| v | 16 | 2048 | 512 | 48 | 1610612736 |
| o | 16 | 4096 | 2048 | 48 | 12884901888 |
| router | 16 | 2048 | 128 | 48 | 402653184 |
| expert_gate | 128 | 2048 | 768 | 48 | 19327352832 |
| expert_up | 128 | 2048 | 768 | 48 | 19327352832 |
| expert_down | 128 | 768 | 2048 | 48 | 19327352832 |
| output_head | 16 | 2048 | 152064 | 1 | 9965666304 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 97341407232, "qk_matrix_flops": 858783744, "pv_matrix_flops": 858783744, "matrix_flops": 99058974720, "matrix_weight_elements": 30221008896, "kv_bytes_per_position_per_request": 98304, "kv_retained_logical_bytes": 14155776, "processed_rows": 16, "valid_attention_pairs_all_invocations": 2184, "invocations": 16, "accounted_scalar_flops": 87391248, "special_ops": {"rsqrt": 29200, "rope_sign_negation": 1769472, "attention_exp": 3354624, "attention_max_compare": 3330048, "sigmoid": 4718592, "router_exp": 98304, "router_max_compare": 97536}, "matrix_weight_interface_bytes": 97341407232, "matrix_activation_read_bytes": 78708736, "matrix_activation_write_bytes": 60112896, "attention_logical_interface_bytes": 240697344, "accounted_nonmatrix_interface_bytes": 127647744, "accounted_interface_bytes": 97848573952}`

阶段：talker_temporal

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 12 | 1024 | 2048 | 20 | 1006632960 |
| k | 12 | 1024 | 256 | 20 | 125829120 |
| v | 12 | 1024 | 256 | 20 | 125829120 |
| o | 12 | 2048 | 1024 | 20 | 1006632960 |
| router | 12 | 1024 | 128 | 20 | 62914560 |
| expert_gate | 72 | 1024 | 384 | 20 | 1132462080 |
| expert_up | 72 | 1024 | 384 | 20 | 1132462080 |
| expert_down | 72 | 384 | 1024 | 20 | 1132462080 |
| shared_gate | 12 | 1024 | 768 | 20 | 377487360 |
| shared_up | 12 | 1024 | 768 | 20 | 377487360 |
| shared_down | 12 | 768 | 1024 | 20 | 377487360 |
| shared_expert_output_gate | 12 | 1024 | 1 | 20 | 491520 |
| output_head | 12 | 1024 | 3072 | 1 | 75497472 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 6933676032, "qk_matrix_flops": 37847040, "pv_matrix_flops": 37847040, "matrix_flops": 7009370112, "matrix_weight_elements": 3167244288, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 901120, "processed_rows": 12, "valid_attention_pairs_all_invocations": 462, "invocations": 12, "accounted_scalar_flops": 11733804, "special_ops": {"rsqrt": 4812, "rope_sign_negation": 276480, "attention_exp": 147840, "attention_max_compare": 144000, "sigmoid": 737520, "router_exp": 30720, "router_max_compare": 30480}, "matrix_weight_interface_bytes": 6933676032, "matrix_activation_read_bytes": 11821056, "matrix_activation_write_bytes": 8245728, "attention_logical_interface_bytes": 12019200, "accounted_nonmatrix_interface_bytes": 18605568, "accounted_interface_bytes": 6984367584}`

阶段：code_predictor_reset_each_frame

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 192 | 1024 | 2048 | 5 | 4026531840 |
| k | 192 | 1024 | 1024 | 5 | 2013265920 |
| v | 192 | 1024 | 1024 | 5 | 2013265920 |
| o | 192 | 2048 | 1024 | 5 | 4026531840 |
| ffn_gate | 192 | 1024 | 3072 | 5 | 6039797760 |
| ffn_up | 192 | 1024 | 3072 | 5 | 6039797760 |
| ffn_down | 192 | 3072 | 1024 | 5 | 6039797760 |
| output_head | 192 | 1024 | 2048 | 1 | 805306368 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 31004295168, "qk_matrix_flops": 33423360, "pv_matrix_flops": 33423360, "matrix_flops": 31071141888, "matrix_weight_elements": 110100480, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 327680, "processed_rows": 192, "valid_attention_pairs_all_invocations": 1632, "invocations": 180, "accounted_scalar_flops": 37690944, "special_ops": {"rsqrt": 25152, "rope_sign_negation": 1474560, "attention_exp": 130560, "attention_max_compare": 115200, "sigmoid": 2949120}, "matrix_weight_interface_bytes": 29066526720, "matrix_activation_read_bytes": 20054016, "matrix_activation_write_bytes": 24379392, "attention_logical_interface_bytes": 41809920, "accounted_nonmatrix_interface_bytes": 79060992, "accounted_interface_bytes": 29231831040}`

阶段：code2wav_pre_transformer

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 12 | 1024 | 1024 | 8 | 201326592 |
| k | 12 | 1024 | 1024 | 8 | 201326592 |
| v | 12 | 1024 | 1024 | 8 | 201326592 |
| o | 12 | 1024 | 1024 | 8 | 201326592 |
| ffn_gate | 12 | 1024 | 3072 | 8 | 603979776 |
| ffn_up | 12 | 1024 | 3072 | 8 | 603979776 |
| ffn_down | 12 | 3072 | 1024 | 8 | 603979776 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 2617245696, "qk_matrix_flops": 1277952, "pv_matrix_flops": 1277952, "matrix_flops": 2619801600, "matrix_weight_elements": 109051904, "kv_bytes_per_position_per_request": 32768, "kv_retained_logical_bytes": 0, "processed_rows": 12, "valid_attention_pairs_all_invocations": 78, "invocations": 1, "accounted_scalar_flops": 2447052, "special_ops": {"rsqrt": 204, "rope_sign_negation": 98304, "attention_exp": 9984, "attention_max_compare": 8448, "sigmoid": 294912}, "matrix_weight_interface_bytes": 218103808, "matrix_activation_read_bytes": 1769472, "matrix_activation_write_bytes": 2162688, "attention_logical_interface_bytes": 2989056, "accounted_nonmatrix_interface_bytes": 6669312, "accounted_interface_bytes": 231694336}`

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
