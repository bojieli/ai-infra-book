# audio-generation-matrix-and-codebook-ledger — qwen3-omni-30b-a3b-instruct

输入：`{"audio_history": 32, "batch": 1, "fish_prompt_tokens": 0, "frames": 1, "kv_element_bytes": 2, "operand_element_bytes": 2, "text_history": 128, "text_tokens": 16}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| accounted_transformer_and_bridge_matrix_flops | 102,852,239,360 |
| full_model_parameters | `null` |
| full_generation_flops | `null` |
| full_codec_flops | `null` |
| predicted_latency_seconds | `null` |

音频阶段供给：`{"effective_rates": {"matrix": null, "interface": null, "scalar": null}, "accounted_work_totals": {"matrix_flops": 106488704576, "accounted_interface_bytes": 101280721382, "accounted_scalar_flops": 102675589}, "accounted_serial_critical_path_lower_bound_seconds_exact": null, "full_request_latency_seconds": null, "first_audio_latency_seconds": null, "prompt_scope": "Fish optional already-tokenized text-only prompt included; text/audio tokenizer and reference-audio encoder excluded.", "duration_basis_seconds_exact": "91/1600", "required_matrix_flops_per_second_exact": "170381927321600/91", "required_accounted_interface_bytes_per_second_exact": "162049154211200/91", "required_accounted_scalar_flops_per_second_exact": "164280942400/91", "interpretation": "Necessary average aggregate supply to emit this batch within one request audio duration; not sufficient for latency. Node max(F/P,bytes/BW,scalar/S) uses only supplied rates and declared interfaces, permits within-node overlap, and excludes special-op/launch costs. Sum follows strict node dependencies."}`

| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |
| --- | --- | ---: | ---: | --- |
| code_embedding_lookup | embedding | 0 | 0 | 32768/128/32768 |
| code_embedding_mean | embedding | 0 | 16384 | 0/32768/2048 |
| upsample_0 | conv_transpose1d | 4194304 | 2048 | 4196352/2048/4096 |
| upsample_0_crop_contiguous | copy | 0 | 0 | 0/4096/4096 |
| upsample_0_depthwise | causal_conv1d | 28672 | 2048 | 16384/4096/4096 |
| upsample_0_layernorm | normalization | 0 | 14338 | 4096/4096/4096 |
| upsample_0_pointwise1 | linear | 16777216 | 8192 | 8396800/4096/16384 |
| upsample_0_gelu | activation | 0 | 0 | 0/16384/16384 |
| upsample_0_pointwise2 | linear | 16777216 | 2048 | 8390656/16384/4096 |
| upsample_0_gamma_residual | residual | 0 | 4096 | 2048/8192/4096 |
| upsample_1 | conv_transpose1d | 8388608 | 4096 | 4196352/4096/8192 |
| upsample_1_crop_contiguous | copy | 0 | 0 | 0/8192/8192 |
| upsample_1_depthwise | causal_conv1d | 57344 | 4096 | 16384/8192/8192 |
| upsample_1_layernorm | normalization | 0 | 28676 | 4096/8192/8192 |
| upsample_1_pointwise1 | linear | 33554432 | 16384 | 8396800/8192/32768 |
| upsample_1_gelu | activation | 0 | 0 | 0/32768/32768 |
| upsample_1_pointwise2 | linear | 33554432 | 4096 | 8390656/32768/8192 |
| upsample_1_gamma_residual | residual | 0 | 8192 | 2048/16384/8192 |
| decoder_input | causal_conv1d | 88080384 | 6144 | 22023168/8192/12288 |
| decoder_0_snake | snake_beta | 0 | 27648 | 6144/12288/12288 |
| decoder_0_upsample | conv_transpose1d | 150994944 | 30720 | 37750272/12288/61440 |
| decoder_0_upsample_crop_contiguous | copy | 0 | 0 | 0/36864/36864 |
| decoder_0_residual_d1_snake1 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d1_conv1 | causal_conv1d | 198180864 | 18432 | 8259072/36864/36864 |
| decoder_0_residual_d1_snake2 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d1_conv2 | causal_conv1d | 28311552 | 18432 | 1181184/36864/36864 |
| decoder_0_residual_d1_add | residual | 0 | 18432 | 0/73728/36864 |
| decoder_0_residual_d3_snake1 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d3_conv1 | causal_conv1d | 198180864 | 18432 | 8259072/36864/36864 |
| decoder_0_residual_d3_snake2 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d3_conv2 | causal_conv1d | 28311552 | 18432 | 1181184/36864/36864 |
| decoder_0_residual_d3_add | residual | 0 | 18432 | 0/73728/36864 |
| decoder_0_residual_d9_snake1 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d9_conv1 | causal_conv1d | 198180864 | 18432 | 8259072/36864/36864 |
| decoder_0_residual_d9_snake2 | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_0_residual_d9_conv2 | causal_conv1d | 28311552 | 18432 | 1181184/36864/36864 |
| decoder_0_residual_d9_add | residual | 0 | 18432 | 0/73728/36864 |
| decoder_1_snake | snake_beta | 0 | 75264 | 3072/36864/36864 |
| decoder_1_upsample | conv_transpose1d | 141557760 | 48000 | 5899008/36864/96000 |
| decoder_1_upsample_crop_contiguous | copy | 0 | 0 | 0/88320/88320 |
| decoder_1_residual_d1_snake1 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d1_conv1 | causal_conv1d | 237404160 | 44160 | 2065152/88320/88320 |
| decoder_1_residual_d1_snake2 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d1_conv2 | causal_conv1d | 33914880 | 44160 | 295680/88320/88320 |
| decoder_1_residual_d1_add | residual | 0 | 44160 | 0/176640/88320 |
| decoder_1_residual_d3_snake1 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d3_conv1 | causal_conv1d | 237404160 | 44160 | 2065152/88320/88320 |
| decoder_1_residual_d3_snake2 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d3_conv2 | causal_conv1d | 33914880 | 44160 | 295680/88320/88320 |
| decoder_1_residual_d3_add | residual | 0 | 44160 | 0/176640/88320 |
| decoder_1_residual_d9_snake1 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d9_conv1 | causal_conv1d | 237404160 | 44160 | 2065152/88320/88320 |
| decoder_1_residual_d9_snake2 | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_1_residual_d9_conv2 | causal_conv1d | 33914880 | 44160 | 295680/88320/88320 |
| decoder_1_residual_d9_add | residual | 0 | 44160 | 0/176640/88320 |
| decoder_2_snake | snake_beta | 0 | 177408 | 1536/88320/88320 |
| decoder_2_upsample | conv_transpose1d | 135659520 | 89088 | 1180032/88320/178176 |
| decoder_2_upsample_crop_contiguous | copy | 0 | 0 | 0/175104/175104 |
| decoder_2_residual_d1_snake1 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d1_conv1 | causal_conv1d | 235339776 | 87552 | 516480/175104/175104 |
| decoder_2_residual_d1_snake2 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d1_conv2 | causal_conv1d | 33619968 | 87552 | 74112/175104/175104 |
| decoder_2_residual_d1_add | residual | 0 | 87552 | 0/350208/175104 |
| decoder_2_residual_d3_snake1 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d3_conv1 | causal_conv1d | 235339776 | 87552 | 516480/175104/175104 |
| decoder_2_residual_d3_snake2 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d3_conv2 | causal_conv1d | 33619968 | 87552 | 74112/175104/175104 |
| decoder_2_residual_d3_add | residual | 0 | 87552 | 0/350208/175104 |
| decoder_2_residual_d9_snake1 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d9_conv1 | causal_conv1d | 235339776 | 87552 | 516480/175104/175104 |
| decoder_2_residual_d9_snake2 | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_2_residual_d9_conv2 | causal_conv1d | 33619968 | 87552 | 74112/175104/175104 |
| decoder_2_residual_d9_add | residual | 0 | 87552 | 0/350208/175104 |
| decoder_3_snake | snake_beta | 0 | 350592 | 768/175104/175104 |
| decoder_3_upsample | conv_transpose1d | 100859904 | 131616 | 221376/175104/263232 |
| decoder_3_upsample_crop_contiguous | copy | 0 | 0 | 0/262080/262080 |
| decoder_3_residual_d1_snake1 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d1_conv1 | causal_conv1d | 176117760 | 131040 | 129216/262080/262080 |
| decoder_3_residual_d1_snake2 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d1_conv2 | causal_conv1d | 25159680 | 131040 | 18624/262080/262080 |
| decoder_3_residual_d1_add | residual | 0 | 131040 | 0/524160/262080 |
| decoder_3_residual_d3_snake1 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d3_conv1 | causal_conv1d | 176117760 | 131040 | 129216/262080/262080 |
| decoder_3_residual_d3_snake2 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d3_conv2 | causal_conv1d | 25159680 | 131040 | 18624/262080/262080 |
| decoder_3_residual_d3_add | residual | 0 | 131040 | 0/524160/262080 |
| decoder_3_residual_d9_snake1 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d9_conv1 | causal_conv1d | 176117760 | 131040 | 129216/262080/262080 |
| decoder_3_residual_d9_snake2 | snake_beta | 0 | 524352 | 384/262080/262080 |
| decoder_3_residual_d9_conv2 | causal_conv1d | 25159680 | 131040 | 18624/262080/262080 |
| decoder_3_residual_d9_add | residual | 0 | 131040 | 0/524160/262080 |
| output_snake | snake_beta | 0 | 524352 | 384/262080/262080 |
| output_conv | causal_conv1d | 1834560 | 1365 | 1346/262080/2730 |
| wave_clamp | activation | 0 | 0 | 0/2730/2730 |

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
| q | 1 | 1024 | 2048 | 20 | 83886080 |
| k | 1 | 1024 | 256 | 20 | 10485760 |
| v | 1 | 1024 | 256 | 20 | 10485760 |
| o | 1 | 2048 | 1024 | 20 | 83886080 |
| router | 1 | 1024 | 128 | 20 | 5242880 |
| expert_gate | 6 | 1024 | 384 | 20 | 94371840 |
| expert_up | 6 | 1024 | 384 | 20 | 94371840 |
| expert_down | 6 | 384 | 1024 | 20 | 94371840 |
| shared_gate | 1 | 1024 | 768 | 20 | 31457280 |
| shared_up | 1 | 1024 | 768 | 20 | 31457280 |
| shared_down | 1 | 768 | 1024 | 20 | 31457280 |
| shared_expert_output_gate | 1 | 1024 | 1 | 20 | 40960 |
| output_head | 1 | 1024 | 3072 | 1 | 6291456 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 577806336, "qk_matrix_flops": 2703360, "pv_matrix_flops": 2703360, "matrix_flops": 583213056, "matrix_weight_elements": 3167244288, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 675840, "processed_rows": 1, "valid_attention_pairs_all_invocations": 33, "invocations": 1, "accounted_scalar_flops": 970777, "special_ops": {"rsqrt": 401, "rope_sign_negation": 23040, "attention_exp": 10560, "attention_max_compare": 10240, "sigmoid": 61460, "router_exp": 2560, "router_max_compare": 2540}, "matrix_weight_interface_bytes": 577806336, "matrix_activation_read_bytes": 985088, "matrix_activation_write_bytes": 687144, "attention_logical_interface_bytes": 881920, "accounted_nonmatrix_interface_bytes": 1543424, "accounted_interface_bytes": 581903912}`

阶段：code_predictor_reset_each_frame

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 16 | 1024 | 2048 | 5 | 335544320 |
| k | 16 | 1024 | 1024 | 5 | 167772160 |
| v | 16 | 1024 | 1024 | 5 | 167772160 |
| o | 16 | 2048 | 1024 | 5 | 335544320 |
| ffn_gate | 16 | 1024 | 3072 | 5 | 503316480 |
| ffn_up | 16 | 1024 | 3072 | 5 | 503316480 |
| ffn_down | 16 | 3072 | 1024 | 5 | 503316480 |
| output_head | 16 | 1024 | 2048 | 1 | 67108864 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 2583691264, "qk_matrix_flops": 2785280, "pv_matrix_flops": 2785280, "matrix_flops": 2589261824, "matrix_weight_elements": 110100480, "kv_bytes_per_position_per_request": 20480, "kv_retained_logical_bytes": 327680, "processed_rows": 16, "valid_attention_pairs_all_invocations": 136, "invocations": 15, "accounted_scalar_flops": 3140912, "special_ops": {"rsqrt": 2096, "rope_sign_negation": 122880, "attention_exp": 10880, "attention_max_compare": 9600, "sigmoid": 245760}, "matrix_weight_interface_bytes": 2422210560, "matrix_activation_read_bytes": 1671168, "matrix_activation_write_bytes": 2031616, "attention_logical_interface_bytes": 3484160, "accounted_nonmatrix_interface_bytes": 6588416, "accounted_interface_bytes": 2435985920}`

阶段：code2wav_pre_transformer

| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| q | 1 | 1024 | 1024 | 8 | 16777216 |
| k | 1 | 1024 | 1024 | 8 | 16777216 |
| v | 1 | 1024 | 1024 | 8 | 16777216 |
| o | 1 | 1024 | 1024 | 8 | 16777216 |
| ffn_gate | 1 | 1024 | 3072 | 8 | 50331648 |
| ffn_up | 1 | 1024 | 3072 | 8 | 50331648 |
| ffn_down | 1 | 3072 | 1024 | 8 | 50331648 |

本阶段QK/PV与KV：`{"projection_and_ffn_matrix_flops": 218103808, "qk_matrix_flops": 16384, "pv_matrix_flops": 16384, "matrix_flops": 218136576, "matrix_weight_elements": 109051904, "kv_bytes_per_position_per_request": 32768, "kv_retained_logical_bytes": 0, "processed_rows": 1, "valid_attention_pairs_all_invocations": 1, "invocations": 1, "accounted_scalar_flops": 201105, "special_ops": {"rsqrt": 17, "rope_sign_negation": 8192, "attention_exp": 128, "attention_max_compare": 0, "sigmoid": 24576}, "matrix_weight_interface_bytes": 218103808, "matrix_activation_read_bytes": 147456, "matrix_activation_write_bytes": 180224, "attention_logical_interface_bytes": 66048, "accounted_nonmatrix_interface_bytes": 614912, "accounted_interface_bytes": 219112448}`

码本循环：`{"primary_audio_codes": 1, "residual_codes": 15, "predictor_calls": 15, "predictor_processed_positions": 16, "predictor_prefill_positions": 2, "predictor_single_position_calls_per_frame": 14, "predictor_cache_reset_per_frame": true}`

codec时间轴：`{"sample_rate": 24000, "nominal_samples_per_frame": 1920, "nominal_frames_per_second_exact": "25/2", "source_output_samples": 1365, "nominal_output_samples": 1920, "source_output_seconds_exact": "91/1600", "nominal_output_seconds_exact": "2/25", "crop_length_discrepancy_samples": 555, "convtranspose_lengths": [{"input_length": 1, "stride": 2, "kernel": 2, "raw_length": 2, "crop_each_side": 0, "output_length": 2}, {"input_length": 2, "stride": 2, "kernel": 2, "raw_length": 4, "crop_each_side": 0, "output_length": 4}, {"input_length": 4, "stride": 8, "kernel": 16, "raw_length": 40, "crop_each_side": 8, "output_length": 24}, {"input_length": 24, "stride": 5, "kernel": 10, "raw_length": 125, "crop_each_side": 5, "output_length": 115}, {"input_length": 115, "stride": 4, "kernel": 8, "raw_length": 464, "crop_each_side": 4, "output_length": 456}, {"input_length": 456, "stride": 3, "kernel": 6, "raw_length": 1371, "crop_each_side": 3, "output_length": 1365}], "code2wav_chunk_calls": 1}`

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
