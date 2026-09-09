# image-generation — qwen-image-2512

输入：`{"batch": 1, "decoded_dtype": "fp32", "dtype": "bf16", "effective_matrix_service": null, "guidance_scale": 1, "height": 1024, "model": "qwen-image-2512", "negative_prompt_present": true, "negative_text_tokens": 512, "output_type": "image", "qwen_shape_cache_warm": false, "steps": null, "text_tokens": 512, "width": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| vae_spatial_scale | 8 |
| raw_latent_channels | 16 |
| raw_latent_shape | `[1, 16, 128, 128]` |
| packed_latent_shape | `[1, 4096, 64]` |
| raw_latent_elements | 262,144 |
| packed_latent_elements | 262,144 |
| latent_bytes | 524,288 |
| image_tokens | 4,096 |
| hidden_size | 3,072 |
| dual_stream_blocks | 60 |
| single_stream_blocks | 0 |
| denoising_steps | 50 |
| true_cfg_enabled | `false` |
| is_step_distilled | `false` |
| supplied_guidance_ignored | `false` |
| transformer_invocations | 50 |
| branch_count | 1 |
| denoising_matrix_flops | 3,915,196,111,257,600 |
| matrix_weight_elements_excluding_bias_norm | 20,424,818,688 |
| matrix_weight_bytes_excluding_bias_norm | 40,849,637,376 |
| text_encoder_matrix_flops | 7,780,694,777,856 |
| vae_matrix_flops | 11,682,587,869,184 |
| text_encoder_dense_square_matrix_flops | 7,840,418,267,136 |
| vae_nonpadding_and_attention_flops | 4,694,839,773,440 |
| all_stage_dense_matrix_kernel_flops | 3,934,719,117,393,920 |
| all_stage_nonpadding_matrix_flops | 3,927,671,645,808,896 |
| text_encoder_return_live_lower_bytes | 310,861,824 |
| vae_first_frame_feature_cache_bytes | 2,416,443,392 |
| full_runtime_peak_bytes | `null` |
| complete_generation_flops | `null` |
| complete_generation_seconds | `null` |
| vae_decode_calls | 1 |
| decoded_rgb_tensor_bytes | 12,582,912 |
| encoded_image_file_bytes | `null` |
| reference_ordinary_arithmetic_ops | 9,239,333,559,281 |
| reference_comparisons | 1,528,892,876,304 |
| reference_special_calls | `{"rsqrt": 691461522, "exp": 1530725639986, "sqrt": 9486336, "tanh": 169869312000, "log": 50, "sin": 216064, "cos": 216064, "pow": 50}` |
| declared_boundary_graph_peak_bytes | 2,429,550,592 |
| declared_boundary_graph_final_live_bytes | 12,582,912 |
| declared_boundary_graph_final_live_objects | `["decoded_rgb"]` |
| complete_nonmatrix_coverage | `false` |

加入setup helper的声明存活图：`{"helper_invocations": 50, "helper_peak_bytes": 3072, "declared_expanded_graph_peak_bytes": 2429550592, "original_boundary_graph_peak_bytes": 2429550592, "peak_increment_bytes": 0, "final_live_bytes": 12582912, "final_live_objects": ["decoded_rgb"], "actual_allocator_peak_bytes": null, "scope": "Original boundary graph plus pinned sinusoidal timestep helper and immediate output cast only", "remaining": ["caller-owned timestep inputs and scheduler arrays", "text and DiT rotary-frequency construction lifetimes and persistent tables", "learned timestep projector activations and all other block internals", "actual backend fusion, storage reuse, allocator and device placement"]}`；逐事件见JSON，未覆盖完整allocator。

| 文本编码矩阵 | 左形状 | 权重形状 | 重复 | 矩阵FLOPs |
| --- | --- | --- | ---: | ---: |
| conditional/q | [1, 546, 3584] | [3584, 3584] | 28 | 392750432256 |
| conditional/k | [1, 546, 3584] | [512, 3584] | 28 | 56107204608 |
| conditional/v | [1, 546, 3584] | [512, 3584] | 28 | 56107204608 |
| conditional/o | [1, 546, 3584] | [3584, 3584] | 28 | 392750432256 |
| conditional/gate | [1, 546, 3584] | [18944, 3584] | 28 | 2075966570496 |
| conditional/up | [1, 546, 3584] | [18944, 3584] | 28 | 2075966570496 |
| conditional/down | [1, 546, 18944] | [3584, 18944] | 28 | 2075966570496 |
| conditional/unused_full_vocabulary_head | [1, 546, 3584] | [152064, 3584] | 1 | 595137134592 |

| VAE操作 | 输入 | 输出 | kernel | dense核FLOPs | nonpadding FLOPs |
| --- | --- | --- | --- | ---: | ---: |
| post_quant | [1, 16, 1, 128, 128] | [1, 16, 1, 128, 128] | [1, 1, 1] | 8388608 | 8388608 |
| decoder.input | [1, 16, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 5435817984 | 1793114112 |
| mid.residual0.conv1 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| mid.residual0.conv2 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| mid.attention.q | [1, 384, 128, 128] | [1, 384, 128, 128] | [1, 1, 1] | 4831838208 | 4831838208 |
| mid.attention.k | [1, 384, 128, 128] | [1, 384, 128, 128] | [1, 1, 1] | 4831838208 | 4831838208 |
| mid.attention.v | [1, 384, 128, 128] | [1, 384, 128, 128] | [1, 1, 1] | 4831838208 | 4831838208 |
| mid.attention.out | [1, 384, 128, 128] | [1, 384, 128, 128] | [1, 1, 1] | 4831838208 | 4831838208 |
| mid.residual1.conv1 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| mid.residual1.conv2 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual0.conv1 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual0.conv2 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual1.conv1 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual1.conv2 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual2.conv1 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.residual2.conv2 | [1, 384, 1, 128, 128] | [1, 384, 1, 128, 128] | [3, 3, 3] | 130459631616 | 43034738688 |
| up0.spatial_conv | [1, 384, 256, 256] | [1, 192, 256, 256] | [1, 3, 3] | 86973087744 | 86520692736 |
| up1.residual0.shortcut | [1, 192, 1, 256, 256] | [1, 384, 1, 256, 256] | [1, 1, 1] | 9663676416 | 9663676416 |
| up1.residual0.conv1 | [1, 192, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 260919263232 | 86520692736 |
| up1.residual0.conv2 | [1, 384, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 521838526464 | 173041385472 |
| up1.residual1.conv1 | [1, 384, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 521838526464 | 173041385472 |
| up1.residual1.conv2 | [1, 384, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 521838526464 | 173041385472 |
| up1.residual2.conv1 | [1, 384, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 521838526464 | 173041385472 |
| up1.residual2.conv2 | [1, 384, 1, 256, 256] | [1, 384, 1, 256, 256] | [3, 3, 3] | 521838526464 | 173041385472 |
| up1.spatial_conv | [1, 384, 512, 512] | [1, 192, 512, 512] | [1, 3, 3] | 347892350976 | 346986971136 |
| up2.residual0.conv1 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.residual0.conv2 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.residual1.conv1 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.residual1.conv2 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.residual2.conv1 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.residual2.conv2 | [1, 192, 1, 512, 512] | [1, 192, 1, 512, 512] | [3, 3, 3] | 521838526464 | 173493485568 |
| up2.spatial_conv | [1, 192, 1024, 1024] | [1, 96, 1024, 1024] | [1, 3, 3] | 347892350976 | 347439513600 |
| up3.residual0.conv1 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| up3.residual0.conv2 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| up3.residual1.conv1 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| up3.residual1.conv2 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| up3.residual2.conv1 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| up3.residual2.conv2 | [1, 96, 1, 1024, 1024] | [1, 96, 1, 1024, 1024] | [3, 3, 3] | 521838526464 | 173719756800 |
| decoder.output | [1, 96, 1, 1024, 1024] | [1, 3, 1, 1024, 1024] | [3, 3, 3] | 16307453952 | 5428742400 |

参考非矩阵运算（特殊函数单列）

| stage | operation | elements | vectors | vector_width | ordinary_arithmetic_ops | comparisons | special_calls | reference_accumulator_dtype |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "text_conditional" | "rmsnorm" | 111541248 | 31122 | 3584 | 446196114 | 0 | {"rsqrt": 31122} | "fp32" |
| "text_conditional" | "rope_apply" | 62619648 | 0 | 0 | 187858944 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "silu" | 289615872 | 0 | 0 | 1158463488 | 0 | {"exp": 289615872} | "declared_tensor_dtype" |
| "text_conditional" | "multiply" | 289615872 | 0 | 0 | 289615872 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "add" | 109584384 | 0 | 0 | 109584384 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "softmax" | 117075504 | 0 | 0 | 467873952 | 116647440 | {"exp": 117075504} | "fp32" |
| "text_conditional" | "add" | 70447104 | 0 | 0 | 70447104 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 262144 | 0 | 0 | 262144 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "softmax" | 268435456 | 0 | 0 | 1073725440 | 268419072 | {"exp": 268435456} | "fp32" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 6291456 | 16384 | 384 | 37732352 | 16384 | {"sqrt": 16384} | "fp32" |
| "vae" | "silu" | 6291456 | 0 | 0 | 25165824 | 0 | {"exp": 6291456} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 6291456 | 0 | 0 | 6291456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 25165824 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 12582912 | 0 | 0 | 12582912 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 12582912 | 65536 | 192 | 75431936 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 12582912 | 0 | 0 | 50331648 | 0 | {"exp": 12582912} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 100663296 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 50331648 | 0 | 0 | 50331648 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 201326592 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 1048576 | 96 | 602931200 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 3145728 | 0 | 0 | 3145728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "clip" | 3145728 | 0 | 0 | 0 | 6291456 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "layernorm" | 84934656000 | 27648000 | 3072 | 424700928000 | 0 | {"rsqrt": 27648000} | "fp32" |
| "dit_conditional" | "layernorm" | 629145600 | 204800 | 3072 | 3145932800 | 0 | {"rsqrt": 204800} | "fp32" |
| "dit_conditional" | "rmsnorm" | 84934656000 | 663552000 | 128 | 340402176000 | 0 | {"rsqrt": 663552000} | "fp32" |
| "dit_conditional" | "rmsnorm" | 91750400 | 25600 | 3584 | 367027200 | 0 | {"rsqrt": 25600} | "fp32" |
| "dit_conditional" | "rope_apply" | 84934656000 | 0 | 0 | 254803968000 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "softmax" | 1528823808000 | 0 | 0 | 6114963456000 | 1528492032000 | {"exp": 1528823808000} | "fp32" |
| "dit_conditional" | "multiply" | 170498457600 | 0 | 0 | 170498457600 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 170498457600 | 0 | 0 | 170498457600 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 37017600 | 0 | 0 | 37017600 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "gelu_tanh" | 169869312000 | 0 | 0 | 1358954496000 | 0 | {"tanh": 169869312000} | "declared_tensor_dtype" |
| "dit_conditional" | "silu" | 18739200 | 0 | 0 | 74956800 | 0 | {"exp": 18739200} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 383038054400 | 0 | 0 | 383038054400 | 0 | {} | "declared_tensor_dtype" |
| "scheduler" | "euler_update" | 13107200 | 0 | 0 | 26214450 | 0 | {} | "fp32" |
| "latent_denormalize" | "divide" | 262144 | 0 | 0 | 262144 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "add" | 262144 | 0 | 0 | 262144 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "divide" | 16 | 0 | 0 | 16 | 0 | {} | "declared_tensor_dtype" |
| "setup" | "timestep_sinusoidal_features" | null | null | null | 25650 | 0 | {"log": 50, "exp": 6400, "sin": 6400, "cos": 6400} | "fp32" |
| "setup" | "pipeline_transformer_timestep_rescale" | null | null | null | 50 | 0 | {} | "bf16" |
| "setup" | "text_conditional_rope_forward" | null | null | null | 524160 | 0 | {"sin": 209664, "cos": 209664} | "fp32" |
| "setup" | "scheduler_mu" | null | null | null | 6 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_sigma_endpoint" | null | null | null | 1 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_exponential_shift" | null | null | null | 200 | 0 | {"exp": 2, "pow": 50} | "fp32" |
| "setup" | "scheduler_terminal_stretch" | null | null | null | 152 | 0 | {} | "fp32" |
| "setup" | "scheduler_timestep_scale" | null | null | null | 50 | 0 | {} | "fp32" |

声明边界缓冲区生命周期（非运行时显存峰值）

| event | phase | action | object | bytes | live_bytes_after | live_objects |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | "text_conditional" | "allocate" | "conditional_lm_return" | 310861824 | 310861824 | ["conditional_lm_return"] |
| 1 | "text_conditional" | "allocate" | "conditional_embedding" | 3670016 | 314531840 | ["conditional_lm_return", "conditional_embedding"] |
| 2 | "text_conditional" | "release" | "conditional_lm_return" | 310861824 | 3670016 | ["conditional_embedding"] |
| 3 | "noise_init" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 4 | "step_0_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 5 | "step_0_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 6 | "step_0_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 7 | "step_0_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 8 | "step_0_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 9 | "step_0_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 10 | "step_0_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 11 | "step_0_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 12 | "step_0_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 13 | "step_0_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 14 | "step_1_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 15 | "step_1_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 16 | "step_1_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 17 | "step_1_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 18 | "step_1_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 19 | "step_1_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 20 | "step_1_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 21 | "step_1_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 22 | "step_1_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 23 | "step_1_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 24 | "step_2_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 25 | "step_2_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 26 | "step_2_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 27 | "step_2_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 28 | "step_2_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 29 | "step_2_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 30 | "step_2_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 31 | "step_2_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 32 | "step_2_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 33 | "step_2_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 34 | "step_3_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 35 | "step_3_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 36 | "step_3_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 37 | "step_3_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 38 | "step_3_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 39 | "step_3_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 40 | "step_3_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 41 | "step_3_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 42 | "step_3_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 43 | "step_3_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 44 | "step_4_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 45 | "step_4_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 46 | "step_4_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 47 | "step_4_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 48 | "step_4_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 49 | "step_4_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 50 | "step_4_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 51 | "step_4_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 52 | "step_4_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 53 | "step_4_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 54 | "step_5_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 55 | "step_5_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 56 | "step_5_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 57 | "step_5_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 58 | "step_5_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 59 | "step_5_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 60 | "step_5_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 61 | "step_5_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 62 | "step_5_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 63 | "step_5_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 64 | "step_6_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 65 | "step_6_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 66 | "step_6_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 67 | "step_6_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 68 | "step_6_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 69 | "step_6_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 70 | "step_6_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 71 | "step_6_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 72 | "step_6_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 73 | "step_6_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 74 | "step_7_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 75 | "step_7_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 76 | "step_7_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 77 | "step_7_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 78 | "step_7_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 79 | "step_7_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 80 | "step_7_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 81 | "step_7_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 82 | "step_7_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 83 | "step_7_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 84 | "step_8_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 85 | "step_8_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 86 | "step_8_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 87 | "step_8_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 88 | "step_8_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 89 | "step_8_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 90 | "step_8_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 91 | "step_8_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 92 | "step_8_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 93 | "step_8_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 94 | "step_9_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 95 | "step_9_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 96 | "step_9_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 97 | "step_9_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 98 | "step_9_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 99 | "step_9_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 100 | "step_9_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 101 | "step_9_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 102 | "step_9_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 103 | "step_9_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 104 | "step_10_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 105 | "step_10_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 106 | "step_10_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 107 | "step_10_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 108 | "step_10_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 109 | "step_10_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 110 | "step_10_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 111 | "step_10_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 112 | "step_10_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 113 | "step_10_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 114 | "step_11_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 115 | "step_11_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 116 | "step_11_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 117 | "step_11_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 118 | "step_11_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 119 | "step_11_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 120 | "step_11_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 121 | "step_11_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 122 | "step_11_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 123 | "step_11_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 124 | "step_12_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 125 | "step_12_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 126 | "step_12_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 127 | "step_12_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 128 | "step_12_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 129 | "step_12_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 130 | "step_12_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 131 | "step_12_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 132 | "step_12_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 133 | "step_12_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 134 | "step_13_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 135 | "step_13_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 136 | "step_13_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 137 | "step_13_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 138 | "step_13_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 139 | "step_13_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 140 | "step_13_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 141 | "step_13_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 142 | "step_13_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 143 | "step_13_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 144 | "step_14_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 145 | "step_14_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 146 | "step_14_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 147 | "step_14_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 148 | "step_14_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 149 | "step_14_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 150 | "step_14_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 151 | "step_14_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 152 | "step_14_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 153 | "step_14_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 154 | "step_15_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 155 | "step_15_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 156 | "step_15_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 157 | "step_15_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 158 | "step_15_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 159 | "step_15_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 160 | "step_15_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 161 | "step_15_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 162 | "step_15_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 163 | "step_15_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 164 | "step_16_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 165 | "step_16_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 166 | "step_16_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 167 | "step_16_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 168 | "step_16_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 169 | "step_16_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 170 | "step_16_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 171 | "step_16_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 172 | "step_16_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 173 | "step_16_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 174 | "step_17_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 175 | "step_17_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 176 | "step_17_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 177 | "step_17_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 178 | "step_17_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 179 | "step_17_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 180 | "step_17_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 181 | "step_17_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 182 | "step_17_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 183 | "step_17_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 184 | "step_18_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 185 | "step_18_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 186 | "step_18_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 187 | "step_18_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 188 | "step_18_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 189 | "step_18_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 190 | "step_18_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 191 | "step_18_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 192 | "step_18_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 193 | "step_18_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 194 | "step_19_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 195 | "step_19_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 196 | "step_19_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 197 | "step_19_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 198 | "step_19_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 199 | "step_19_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 200 | "step_19_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 201 | "step_19_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 202 | "step_19_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 203 | "step_19_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 204 | "step_20_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 205 | "step_20_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 206 | "step_20_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 207 | "step_20_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 208 | "step_20_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 209 | "step_20_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 210 | "step_20_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 211 | "step_20_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 212 | "step_20_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 213 | "step_20_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 214 | "step_21_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 215 | "step_21_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 216 | "step_21_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 217 | "step_21_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 218 | "step_21_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 219 | "step_21_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 220 | "step_21_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 221 | "step_21_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 222 | "step_21_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 223 | "step_21_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 224 | "step_22_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 225 | "step_22_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 226 | "step_22_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 227 | "step_22_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 228 | "step_22_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 229 | "step_22_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 230 | "step_22_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 231 | "step_22_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 232 | "step_22_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 233 | "step_22_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 234 | "step_23_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 235 | "step_23_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 236 | "step_23_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 237 | "step_23_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 238 | "step_23_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 239 | "step_23_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 240 | "step_23_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 241 | "step_23_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 242 | "step_23_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 243 | "step_23_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 244 | "step_24_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 245 | "step_24_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 246 | "step_24_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 247 | "step_24_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 248 | "step_24_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 249 | "step_24_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 250 | "step_24_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 251 | "step_24_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 252 | "step_24_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 253 | "step_24_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 254 | "step_25_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 255 | "step_25_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 256 | "step_25_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 257 | "step_25_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 258 | "step_25_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 259 | "step_25_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 260 | "step_25_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 261 | "step_25_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 262 | "step_25_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 263 | "step_25_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 264 | "step_26_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 265 | "step_26_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 266 | "step_26_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 267 | "step_26_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 268 | "step_26_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 269 | "step_26_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 270 | "step_26_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 271 | "step_26_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 272 | "step_26_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 273 | "step_26_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 274 | "step_27_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 275 | "step_27_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 276 | "step_27_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 277 | "step_27_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 278 | "step_27_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 279 | "step_27_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 280 | "step_27_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 281 | "step_27_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 282 | "step_27_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 283 | "step_27_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 284 | "step_28_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 285 | "step_28_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 286 | "step_28_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 287 | "step_28_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 288 | "step_28_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 289 | "step_28_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 290 | "step_28_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 291 | "step_28_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 292 | "step_28_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 293 | "step_28_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 294 | "step_29_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 295 | "step_29_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 296 | "step_29_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 297 | "step_29_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 298 | "step_29_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 299 | "step_29_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 300 | "step_29_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 301 | "step_29_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 302 | "step_29_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 303 | "step_29_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 304 | "step_30_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 305 | "step_30_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 306 | "step_30_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 307 | "step_30_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 308 | "step_30_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 309 | "step_30_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 310 | "step_30_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 311 | "step_30_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 312 | "step_30_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 313 | "step_30_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 314 | "step_31_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 315 | "step_31_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 316 | "step_31_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 317 | "step_31_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 318 | "step_31_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 319 | "step_31_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 320 | "step_31_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 321 | "step_31_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 322 | "step_31_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 323 | "step_31_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 324 | "step_32_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 325 | "step_32_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 326 | "step_32_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 327 | "step_32_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 328 | "step_32_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 329 | "step_32_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 330 | "step_32_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 331 | "step_32_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 332 | "step_32_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 333 | "step_32_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 334 | "step_33_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 335 | "step_33_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 336 | "step_33_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 337 | "step_33_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 338 | "step_33_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 339 | "step_33_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 340 | "step_33_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 341 | "step_33_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 342 | "step_33_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 343 | "step_33_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 344 | "step_34_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 345 | "step_34_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 346 | "step_34_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 347 | "step_34_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 348 | "step_34_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 349 | "step_34_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 350 | "step_34_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 351 | "step_34_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 352 | "step_34_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 353 | "step_34_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 354 | "step_35_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 355 | "step_35_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 356 | "step_35_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 357 | "step_35_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 358 | "step_35_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 359 | "step_35_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 360 | "step_35_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 361 | "step_35_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 362 | "step_35_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 363 | "step_35_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 364 | "step_36_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 365 | "step_36_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 366 | "step_36_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 367 | "step_36_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 368 | "step_36_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 369 | "step_36_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 370 | "step_36_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 371 | "step_36_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 372 | "step_36_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 373 | "step_36_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 374 | "step_37_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 375 | "step_37_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 376 | "step_37_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 377 | "step_37_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 378 | "step_37_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 379 | "step_37_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 380 | "step_37_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 381 | "step_37_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 382 | "step_37_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 383 | "step_37_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 384 | "step_38_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 385 | "step_38_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 386 | "step_38_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 387 | "step_38_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 388 | "step_38_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 389 | "step_38_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 390 | "step_38_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 391 | "step_38_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 392 | "step_38_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 393 | "step_38_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 394 | "step_39_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 395 | "step_39_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 396 | "step_39_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 397 | "step_39_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 398 | "step_39_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 399 | "step_39_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 400 | "step_39_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 401 | "step_39_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 402 | "step_39_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 403 | "step_39_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 404 | "step_40_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 405 | "step_40_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 406 | "step_40_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 407 | "step_40_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 408 | "step_40_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 409 | "step_40_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 410 | "step_40_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 411 | "step_40_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 412 | "step_40_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 413 | "step_40_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 414 | "step_41_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 415 | "step_41_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 416 | "step_41_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 417 | "step_41_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 418 | "step_41_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 419 | "step_41_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 420 | "step_41_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 421 | "step_41_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 422 | "step_41_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 423 | "step_41_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 424 | "step_42_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 425 | "step_42_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 426 | "step_42_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 427 | "step_42_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 428 | "step_42_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 429 | "step_42_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 430 | "step_42_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 431 | "step_42_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 432 | "step_42_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 433 | "step_42_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 434 | "step_43_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 435 | "step_43_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 436 | "step_43_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 437 | "step_43_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 438 | "step_43_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 439 | "step_43_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 440 | "step_43_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 441 | "step_43_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 442 | "step_43_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 443 | "step_43_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 444 | "step_44_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 445 | "step_44_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 446 | "step_44_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 447 | "step_44_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 448 | "step_44_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 449 | "step_44_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 450 | "step_44_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 451 | "step_44_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 452 | "step_44_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 453 | "step_44_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 454 | "step_45_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 455 | "step_45_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 456 | "step_45_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 457 | "step_45_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 458 | "step_45_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 459 | "step_45_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 460 | "step_45_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 461 | "step_45_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 462 | "step_45_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 463 | "step_45_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 464 | "step_46_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 465 | "step_46_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 466 | "step_46_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 467 | "step_46_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 468 | "step_46_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 469 | "step_46_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 470 | "step_46_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 471 | "step_46_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 472 | "step_46_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 473 | "step_46_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 474 | "step_47_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 475 | "step_47_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 476 | "step_47_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 477 | "step_47_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 478 | "step_47_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 479 | "step_47_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 480 | "step_47_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 481 | "step_47_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 482 | "step_47_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 483 | "step_47_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 484 | "step_48_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 485 | "step_48_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 486 | "step_48_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 487 | "step_48_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 488 | "step_48_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 489 | "step_48_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 490 | "step_48_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 491 | "step_48_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 492 | "step_48_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 493 | "step_48_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 494 | "step_49_conditional" | "allocate" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "prediction"] |
| 495 | "step_49_scheduler" | "allocate" | "scheduler_input_fp32" | 1048576 | 5767168 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 496 | "step_49_scheduler" | "allocate" | "scheduler_output_fp32" | 1048576 | 6815744 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 497 | "step_49_scheduler_cast" | "allocate" | "next_latent" | 524288 | 7340032 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 498 | "step_49_scheduler" | "release" | "scheduler_input_fp32" | 1048576 | 6291456 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 499 | "step_49_scheduler" | "release" | "scheduler_output_fp32" | 1048576 | 5242880 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 500 | "step_49_scheduler" | "release" | "prediction" | 524288 | 4718592 | ["conditional_embedding", "latent", "next_latent"] |
| 501 | "step_49_scheduler" | "release" | "latent" | 524288 | 4194304 | ["conditional_embedding", "next_latent"] |
| 502 | "step_49_scheduler_commit" | "release" | "next_latent" | 524288 | 3670016 | ["conditional_embedding"] |
| 503 | "step_49_scheduler_commit" | "allocate" | "latent" | 524288 | 4194304 | ["conditional_embedding", "latent"] |
| 504 | "denoising_complete" | "release" | "conditional_embedding" | 3670016 | 524288 | ["latent"] |
| 505 | "vae_decoder.input" | "allocate" | "vae_cache_decoder.input" | 524288 | 1048576 | ["latent", "vae_cache_decoder.input"] |
| 506 | "vae_mid.residual0.conv1" | "allocate" | "vae_cache_mid.residual0.conv1" | 12582912 | 13631488 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1"] |
| 507 | "vae_mid.residual0.conv2" | "allocate" | "vae_cache_mid.residual0.conv2" | 12582912 | 26214400 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2"] |
| 508 | "vae_mid.residual1.conv1" | "allocate" | "vae_cache_mid.residual1.conv1" | 12582912 | 38797312 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1"] |
| 509 | "vae_mid.residual1.conv2" | "allocate" | "vae_cache_mid.residual1.conv2" | 12582912 | 51380224 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2"] |
| 510 | "vae_up0.residual0.conv1" | "allocate" | "vae_cache_up0.residual0.conv1" | 12582912 | 63963136 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1"] |
| 511 | "vae_up0.residual0.conv2" | "allocate" | "vae_cache_up0.residual0.conv2" | 12582912 | 76546048 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2"] |
| 512 | "vae_up0.residual1.conv1" | "allocate" | "vae_cache_up0.residual1.conv1" | 12582912 | 89128960 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1"] |
| 513 | "vae_up0.residual1.conv2" | "allocate" | "vae_cache_up0.residual1.conv2" | 12582912 | 101711872 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2"] |
| 514 | "vae_up0.residual2.conv1" | "allocate" | "vae_cache_up0.residual2.conv1" | 12582912 | 114294784 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1"] |
| 515 | "vae_up0.residual2.conv2" | "allocate" | "vae_cache_up0.residual2.conv2" | 12582912 | 126877696 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2"] |
| 516 | "vae_up1.residual0.conv1" | "allocate" | "vae_cache_up1.residual0.conv1" | 25165824 | 152043520 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1"] |
| 517 | "vae_up1.residual0.conv2" | "allocate" | "vae_cache_up1.residual0.conv2" | 50331648 | 202375168 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2"] |
| 518 | "vae_up1.residual1.conv1" | "allocate" | "vae_cache_up1.residual1.conv1" | 50331648 | 252706816 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1"] |
| 519 | "vae_up1.residual1.conv2" | "allocate" | "vae_cache_up1.residual1.conv2" | 50331648 | 303038464 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2"] |
| 520 | "vae_up1.residual2.conv1" | "allocate" | "vae_cache_up1.residual2.conv1" | 50331648 | 353370112 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1"] |
| 521 | "vae_up1.residual2.conv2" | "allocate" | "vae_cache_up1.residual2.conv2" | 50331648 | 403701760 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2"] |
| 522 | "vae_up2.residual0.conv1" | "allocate" | "vae_cache_up2.residual0.conv1" | 100663296 | 504365056 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1"] |
| 523 | "vae_up2.residual0.conv2" | "allocate" | "vae_cache_up2.residual0.conv2" | 100663296 | 605028352 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2"] |
| 524 | "vae_up2.residual1.conv1" | "allocate" | "vae_cache_up2.residual1.conv1" | 100663296 | 705691648 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1"] |
| 525 | "vae_up2.residual1.conv2" | "allocate" | "vae_cache_up2.residual1.conv2" | 100663296 | 806354944 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2"] |
| 526 | "vae_up2.residual2.conv1" | "allocate" | "vae_cache_up2.residual2.conv1" | 100663296 | 907018240 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1"] |
| 527 | "vae_up2.residual2.conv2" | "allocate" | "vae_cache_up2.residual2.conv2" | 100663296 | 1007681536 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2"] |
| 528 | "vae_up3.residual0.conv1" | "allocate" | "vae_cache_up3.residual0.conv1" | 201326592 | 1209008128 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1"] |
| 529 | "vae_up3.residual0.conv2" | "allocate" | "vae_cache_up3.residual0.conv2" | 201326592 | 1410334720 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2"] |
| 530 | "vae_up3.residual1.conv1" | "allocate" | "vae_cache_up3.residual1.conv1" | 201326592 | 1611661312 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1"] |
| 531 | "vae_up3.residual1.conv2" | "allocate" | "vae_cache_up3.residual1.conv2" | 201326592 | 1812987904 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2"] |
| 532 | "vae_up3.residual2.conv1" | "allocate" | "vae_cache_up3.residual2.conv1" | 201326592 | 2014314496 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1"] |
| 533 | "vae_up3.residual2.conv2" | "allocate" | "vae_cache_up3.residual2.conv2" | 201326592 | 2215641088 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2"] |
| 534 | "vae_decoder.output" | "allocate" | "vae_cache_decoder.output" | 201326592 | 2416967680 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output"] |
| 535 | "vae_output" | "allocate" | "decoded_rgb" | 12582912 | 2429550592 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 536 | "vae_clear_cache" | "release" | "vae_cache_decoder.input" | 524288 | 2429026304 | ["latent", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 537 | "vae_clear_cache" | "release" | "vae_cache_mid.residual0.conv1" | 12582912 | 2416443392 | ["latent", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 538 | "vae_clear_cache" | "release" | "vae_cache_mid.residual0.conv2" | 12582912 | 2403860480 | ["latent", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 539 | "vae_clear_cache" | "release" | "vae_cache_mid.residual1.conv1" | 12582912 | 2391277568 | ["latent", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 540 | "vae_clear_cache" | "release" | "vae_cache_mid.residual1.conv2" | 12582912 | 2378694656 | ["latent", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 541 | "vae_clear_cache" | "release" | "vae_cache_up0.residual0.conv1" | 12582912 | 2366111744 | ["latent", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 542 | "vae_clear_cache" | "release" | "vae_cache_up0.residual0.conv2" | 12582912 | 2353528832 | ["latent", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 543 | "vae_clear_cache" | "release" | "vae_cache_up0.residual1.conv1" | 12582912 | 2340945920 | ["latent", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 544 | "vae_clear_cache" | "release" | "vae_cache_up0.residual1.conv2" | 12582912 | 2328363008 | ["latent", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 545 | "vae_clear_cache" | "release" | "vae_cache_up0.residual2.conv1" | 12582912 | 2315780096 | ["latent", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 546 | "vae_clear_cache" | "release" | "vae_cache_up0.residual2.conv2" | 12582912 | 2303197184 | ["latent", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 547 | "vae_clear_cache" | "release" | "vae_cache_up1.residual0.conv1" | 25165824 | 2278031360 | ["latent", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 548 | "vae_clear_cache" | "release" | "vae_cache_up1.residual0.conv2" | 50331648 | 2227699712 | ["latent", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 549 | "vae_clear_cache" | "release" | "vae_cache_up1.residual1.conv1" | 50331648 | 2177368064 | ["latent", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 550 | "vae_clear_cache" | "release" | "vae_cache_up1.residual1.conv2" | 50331648 | 2127036416 | ["latent", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 551 | "vae_clear_cache" | "release" | "vae_cache_up1.residual2.conv1" | 50331648 | 2076704768 | ["latent", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 552 | "vae_clear_cache" | "release" | "vae_cache_up1.residual2.conv2" | 50331648 | 2026373120 | ["latent", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 553 | "vae_clear_cache" | "release" | "vae_cache_up2.residual0.conv1" | 100663296 | 1925709824 | ["latent", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 554 | "vae_clear_cache" | "release" | "vae_cache_up2.residual0.conv2" | 100663296 | 1825046528 | ["latent", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 555 | "vae_clear_cache" | "release" | "vae_cache_up2.residual1.conv1" | 100663296 | 1724383232 | ["latent", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 556 | "vae_clear_cache" | "release" | "vae_cache_up2.residual1.conv2" | 100663296 | 1623719936 | ["latent", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 557 | "vae_clear_cache" | "release" | "vae_cache_up2.residual2.conv1" | 100663296 | 1523056640 | ["latent", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 558 | "vae_clear_cache" | "release" | "vae_cache_up2.residual2.conv2" | 100663296 | 1422393344 | ["latent", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 559 | "vae_clear_cache" | "release" | "vae_cache_up3.residual0.conv1" | 201326592 | 1221066752 | ["latent", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 560 | "vae_clear_cache" | "release" | "vae_cache_up3.residual0.conv2" | 201326592 | 1019740160 | ["latent", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 561 | "vae_clear_cache" | "release" | "vae_cache_up3.residual1.conv1" | 201326592 | 818413568 | ["latent", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 562 | "vae_clear_cache" | "release" | "vae_cache_up3.residual1.conv2" | 201326592 | 617086976 | ["latent", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 563 | "vae_clear_cache" | "release" | "vae_cache_up3.residual2.conv1" | 201326592 | 415760384 | ["latent", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 564 | "vae_clear_cache" | "release" | "vae_cache_up3.residual2.conv2" | 201326592 | 214433792 | ["latent", "vae_cache_decoder.output", "decoded_rgb"] |
| 565 | "vae_clear_cache" | "release" | "vae_cache_decoder.output" | 201326592 | 13107200 | ["latent", "decoded_rgb"] |
| 566 | "vae_complete" | "release" | "latent" | 524288 | 12582912 | ["decoded_rgb"] |

条件式矩阵供给下界：`{"available": false, "declared_serial_matrix_lower_exact_seconds": null, "complete_request_seconds": null, "reason": "No effective matrix service supplied"}`

| 分支/矩阵 | 左形状 | 右形状 | 重复 | 矩阵FLOPs | 左/右/输出逻辑bytes |
| --- | --- | --- | ---: | ---: | --- |
| conditional/image_input | [1, 4096, 64] | [64, 3072] | 1 | 1610612736 | 524288/393216/25165824 |
| conditional/text_input | [1, 512, 3584] | [3584, 3072] | 1 | 11274289152 | 3670016/22020096/3145728 |
| conditional/timestep_1 | [1, 1, 256] | [256, 3072] | 1 | 1572864 | 512/1572864/6144 |
| conditional/timestep_2 | [1, 1, 3072] | [3072, 3072] | 1 | 18874368 | 6144/18874368/6144 |
| conditional/double_image_q | [1, 4096, 3072] | [3072, 3072] | 60 | 4638564679680 | 1509949440/1132462080/1509949440 |
| conditional/double_image_k | [1, 4096, 3072] | [3072, 3072] | 60 | 4638564679680 | 1509949440/1132462080/1509949440 |
| conditional/double_image_v | [1, 4096, 3072] | [3072, 3072] | 60 | 4638564679680 | 1509949440/1132462080/1509949440 |
| conditional/double_image_out | [1, 4096, 3072] | [3072, 3072] | 60 | 4638564679680 | 1509949440/1132462080/1509949440 |
| conditional/double_image_ff_in | [1, 4096, 3072] | [3072, 12288] | 60 | 18554258718720 | 1509949440/4529848320/6039797760 |
| conditional/double_image_ff_out | [1, 4096, 12288] | [12288, 3072] | 60 | 18554258718720 | 6039797760/4529848320/1509949440 |
| conditional/double_image_modulation | [1, 1, 3072] | [3072, 18432] | 60 | 6794772480 | 368640/6794772480/2211840 |
| conditional/double_text_q | [1, 512, 3072] | [3072, 3072] | 60 | 579820584960 | 188743680/1132462080/188743680 |
| conditional/double_text_k | [1, 512, 3072] | [3072, 3072] | 60 | 579820584960 | 188743680/1132462080/188743680 |
| conditional/double_text_v | [1, 512, 3072] | [3072, 3072] | 60 | 579820584960 | 188743680/1132462080/188743680 |
| conditional/double_text_out | [1, 512, 3072] | [3072, 3072] | 60 | 579820584960 | 188743680/1132462080/188743680 |
| conditional/double_text_ff_in | [1, 512, 3072] | [3072, 12288] | 60 | 2319282339840 | 188743680/4529848320/754974720 |
| conditional/double_text_ff_out | [1, 512, 12288] | [12288, 3072] | 60 | 2319282339840 | 754974720/4529848320/188743680 |
| conditional/double_text_modulation | [1, 1, 3072] | [3072, 18432] | 60 | 6794772480 | 368640/6794772480/2211840 |
| conditional/joint_attention_qk | [24, 4608, 128] | [128, 4608] | 60 | 7827577896960 | 1698693120/1698693120/61152952320 |
| conditional/joint_attention_pv | [24, 4608, 4608] | [4608, 128] | 60 | 7827577896960 | 61152952320/1698693120/1698693120 |
| conditional/output_adaln_modulation | [1, 1, 3072] | [3072, 6144] | 1 | 37748736 | 6144/37748736/12288 |
| conditional/image_output | [1, 4096, 3072] | [3072, 64] | 1 | 1610612736 | 25165824/393216/524288 |

模型初始化与请求setup运算：

- `{"stage": "setup", "operation": "timestep_sinusoidal_features", "scope": "request", "invocations": 50, "ordinary_arithmetic_ops": 25650, "comparisons": 0, "special_calls": {"log": 50, "exp": 6400, "sin": 6400, "cos": 6400}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "pipeline_transformer_timestep_rescale", "scope": "request", "invocations": 50, "ordinary_arithmetic_ops": 50, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "bf16"}`
- `{"stage": "setup", "operation": "text_conditional_rope_forward", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 524160, "comparisons": 0, "special_calls": {"sin": 209664, "cos": 209664}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "qwen_rope_constructor_tables", "scope": "model_initialization", "invocations": 1, "ordinary_arithmetic_ops": 524544, "comparisons": 0, "special_calls": {"pow": 128, "polar": 524288}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_mu", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 6, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_sigma_endpoint", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 1, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_exponential_shift", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 200, "comparisons": 0, "special_calls": {"exp": 2, "pow": 50}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_terminal_stretch", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 152, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_timestep_scale", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 50, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "fp32"}`

setup转换、索引与随机数（非FLOPs）：

- `{"operation": "pipeline_timestep_to_latent_dtype", "scope": "request", "invocations": 50, "elements_per_invocation": 1, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 50, "logical_input_bytes": 200, "logical_output_bytes": 100, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_to_fp32", "scope": "request", "invocations": 50, "elements_per_invocation": 1, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 50, "logical_input_bytes": 100, "logical_output_bytes": 200, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_features_to_model_dtype", "scope": "request", "invocations": 50, "elements_per_invocation": 256, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 12800, "logical_input_bytes": 51200, "logical_output_bytes": 25600, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_frequency_index_setup", "scope": "request", "invocations": 50, "integer_arange_elements_per_invocation": 128, "integer_denominator_subtractions_per_invocation": 1}`
- `{"operation": "timestep_sin_cos_concat_and_flip", "scope": "request", "invocations": 50, "output_elements_per_invocation": 512, "nonflops_kind": "tensor materialization", "logical_output_bytes": 102400}`
- `{"operation": "text_conditional_position_ids_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 1638, "source_dtype": "int64", "target_dtype": "fp32", "conversion_elements": 1638, "logical_input_bytes": 13104, "logical_output_bytes": 6552, "actual_device_transfer_bytes": null}`
- `{"operation": "text_conditional_rope_output_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 419328, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 419328, "logical_input_bytes": 1677312, "logical_output_bytes": 838656, "actual_device_transfer_bytes": null}`
- `{"operation": "qwen_rope_constructor_tables", "scope": "model_initialization", "invocations": 1, "integer_arange_elements": 8320, "integer_negate_subtract_ops": 8192, "persistent_table_bytes": 4194304, "output_dtype": "complex64"}`
- `{"operation": "qwen_cached_image_frequency_build", "scope": "request", "invocations": 1, "output_dtype": "complex64", "axes_concat_elements": 3584, "full_image_concat_and_clone_elements": 524288, "logical_output_bytes": 4222976}`
- `{"operation": "qwen_image_rope_cache_and_forward", "scope": "request", "invocations": 50, "cold_unique_keys": 1, "cache_hits": 49, "text_slice_start": 32, "outer_image_concat_output_bytes": 104857600, "tensor_views_are_not_copies": true}`
- `{"operation": "scheduler_mu_branch_and_index_arithmetic", "scope": "request", "integer_subtractions": 1, "integer_comparisons": 0}`
- `{"operation": "scheduler_linspace", "scope": "request", "invocations": 1, "output_elements": 50, "output_dtype": "numpy_fp64", "ordinary_arithmetic_ops": null, "nonflops_kind": "numpy implementation-dependent construction"}`
- `{"operation": "scheduler_sigmas_fp64_to_fp32", "scope": "request", "invocations": 1, "elements_per_invocation": 50, "source_dtype": "fp64", "target_dtype": "fp32", "conversion_elements": 50, "logical_input_bytes": 400, "logical_output_bytes": 200, "actual_device_transfer_bytes": null}`
- `{"operation": "scheduler_append_terminal_zero", "scope": "request", "invocations": 1, "output_elements": 51, "logical_output_bytes": 204, "nonflops_kind": "concat/fill; not step evaluation"}`
- `{"operation": "initial_noise", "scope": "request", "invocations": 1, "normal_samples": 262144, "output_dtype": "bf16", "logical_output_bytes": 524288, "rng_algorithm": null}`
- `{"operation": "euler_sample_upcast", "scope": "request", "invocations": 50, "elements_per_invocation": 262144, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 13107200, "logical_input_bytes": 26214400, "logical_output_bytes": 52428800, "actual_device_transfer_bytes": null}`
- `{"operation": "euler_result_downcast", "scope": "request", "invocations": 50, "elements_per_invocation": 262144, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 13107200, "logical_input_bytes": 52428800, "logical_output_bytes": 26214400, "actual_device_transfer_bytes": null}`

计量条件：

- 新增text阶段按B个独立同长prompt，无额外num_images_per_prompt复制；Qwen输入含34模板位置再截取，FLUX使用声明的max-length文本位置。两个完整LM wrapper即使只消费hidden仍执行全部层与全词表head，FLUX取9/18/27层不跳过后续层。固定transformers实现是声明的配套版本，不声称所有已发布运行环境都固定这个依赖。
- text的all_hidden/logits/临时KV集合按声明dtype计必要同时存活张量，不含权重或workspace；FLUX显式use_cache=False，Qwen按config开启。返回对象与临时KV仅属于text阶段，不保留到每个去噪步；阶段表不得乘steps。
- VAE固定use_tiling=False/use_slicing=False、单静态帧、inference模式；Qwen首帧time-upsample仅留Rep哨兵不执行time_conv，但普通causal Conv3d仍使用3x3x3及两帧零padding。dense kernel乘加和nonpadding有效乘加分列，均不承诺后端实际执行相同量。FLUX普通2D decoder四级各3resnet、三次空间上采样；mid attention均为单头非因果，不因Qwen类注释写causal而裁成三角。
- Qwen首帧feature_cache逐causal conv保存独立输入clone直到decode末尾clear_cache；报告其必要保留容量和关键对象释放边界，不是完整显存峰值。VAE Norm、SiLU、bias、residual、softmax与nearest另列元素/向量次数；归一化FP32临时、kernel workspace、fused allocator及后处理仍未给完整生命周期峰值。
- 官方模型component config及固定diffusers源码；纯text-to-image、无参考图/编辑/LoRA/缓存跳层，尺寸限定VAE scale×2整除，不模仿原pipeline静默取整。DiT、纯文本encoder和非分块静态VAE内部已分别计矩阵/卷积子账，完整非矩阵算术和执行时间仍未全计。
- Qwen raw16通道经2×2 packing变64，FLUX raw32变128；in_channels已经是packed宽度。Qwen输出patch²×16=64，FLUX patch1×128=128，不再对输入乘patch²。静态Qwen VAE的单帧维省略显示，不应用视频时间压缩。
- 每个流的Q/K/V/out独立，joint attention包含全部图像+文本位置的非因果QK与PV。Qwen GELU FFN宽4D；FLUX SwiGLU宽3D且输入为2×3D，单流将QKV+gate/up和attention/FF输出分别融合，仍列真实矩阵形状。
- Qwen各双流块各有两套D→6D调制；FLUX双流/单流调制跨块共享，每次forward各算一次。时间MLP和输出AdaLN投影计入矩阵账；bias、norm、激活、RoPE、Softmax、CFG的norm重缩放和scheduler更新均未计，不能拿此参数小计作完整checkpoint容量。
- text_tokens/negative_text_tokens是传入DiT的实际embedding长度，默认512为显式场景。FLUX默认text encoder把512位置及9/18/27层特征拼成7680维；Qwen最终hidden为3584维、模板截取/批内padding须另记录。正负长度不同分别计算，不假定CFG总工作恰好翻倍。
- Qwen true CFG条件为scale>1且提供negative prompt，两次顺序transformer调用；FLUX klein 4B的model_index is_distilled=true强制单分支，guidance_embeds=false本身不足以判断CFG。50/4步是题设采用的官方模型卡示例，不是质量等价、全球最佳步数或隐藏的1000训练timesteps。
- 每步一次Euler更新，无自定义timesteps/sigmas、中断、回调改步或附加corrector。transformer_invocations与batch中处理样本数分开；文本编码在循环前，VAE在最终后各按条件执行，不乘去噪步数。text/VAE内部新增逐矩阵/卷积账，text使用有效因果边与另列dense square、VAE分别列dense kernel与nonpadding；非矩阵另列元素/向量/特殊函数次数，未把这些不同单位混成完整FLOPs。
- GEMM逻辑A/B/C字节按逐矩阵一次接口读取/写入列出，权重在batch内理想复用；QK/PV的右操作数为激活，不计参数。全score输出是未融合数学接口量，不代表FlashAttention物化、实际HBM流量、工作区或显存峰值。CFG两分支共享权重，小计容量不乘NFE。
- 解码RGB张量使用显式decoded_dtype字节预算，不据force_upcast猜实际执行dtype；JPEG/PNG/RAW文件字节未知。VAE转换、权重加载/offload、随机数、网络与图片编码仍需补齐；不同模型相同分辨率/步数不证明同质量。
- 参考非矩阵算法单列ordinary arithmetic、comparison和exp/sqrt/rsqrt/tanh，特殊函数不是1 FLOP。LayerNorm用中心方差，RMS用平方均值，Softmax用全行max/shift/exp/sum/div并计一次score scale；SiLU采用sigmoid再乘，GELU为tanh三次多项式。它们是声明算法计数，不是torch融合指令或逐位结果保证。
- reference_accumulator_dtype=fp32是归约参考方案；不声称所有硬件/后端内部执行同dtype。Euler源码明确把sample转FP32、更新后转回prediction dtype；图采用无alias的显式FP32输入/输出及回转缓冲，表达一种参考执行组织，不冒称实际scalar promotion或allocator布局。
- boundary graph逐事件安排text返回/抽取、跨step embedding、CFG负分支期间cond预测、scheduler转换与Qwen VAE feature-cache；其峰值仅为声明的边界缓冲图。权重、block/conv内部live tensor、完整CFG norm scratch、VAE计算workspace、分配器和postprocess均不在图内，不能据此给硬件可装入结论或称全系统显存峰值。
- setup选择标准非Neuron/NPU/MPS频率路径；FLUX按源码FP64频率、FP32 cos/sin输出参考，未知实际后端不隐式套此dtype。Qwen初始化正负4096表为complex64；shape cache默认冷，重复step命中LRU，warm输入省形状构造但不省timestep。转换行只计明确请求的元素/语义读写，same-dtype为零转换，设备迁移与alias未知。索引/arange/cartesian/concat/fill和随机样本数不作为FLOPs。
- 可选effective_matrix_service必须匹配input_dtype、FP32 accumulation及dense口径；给定值是该场景有效供给而非自动硬件峰值。串行下界按固定text→各去噪分支/步→VAE的直接矩阵/卷积算法，采用有效因果/nonpadding工作；未计非矩阵、IO和排队，不是可达时间或质量/SLO承诺，不能把它当完整CPU/GPU利用率。
- 新增setup账已覆盖固定标准路径的DiT/text RoPE forward、timestep sin/cos和scheduler动态shift/terminal stretch，构造期Qwen表单列不混入请求。仍未完整计价text-RoPE初始化helper、NumPy linspace内部、全部dtype转换、随机数算法、tokenizer/图片编码以及实际融合下的归约重算；完整非矩阵覆盖标志为false，完整生成FLOPs/时间保持null。已列text/VAE操作只执行该阶段次数，DiT/CFG/update操作才随步骤变化。

固定来源：

- [sources/qwen-image-2512/README.md](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/README.md)，SHA256 `db371596007403d9588e0d78d9798ecafa59bf7772fbdc12952e581b1562920b`。
- [configs/models/qwen-image-2512/transformer/config.json](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/transformer/config.json)，SHA256 `247c94f9b923a7d6b6035ca76d27b556bd0efd1a8c7672f31f037644fcce340e`。
- [configs/models/qwen-image-2512/text_encoder/config.json](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/text_encoder/config.json)，SHA256 `4a49f14a1594fd988ab301e491ac522cd9b0e8fd1c9232b806c54568f348c1fb`。
- [configs/models/qwen-image-2512/vae/config.json](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/vae/config.json)，SHA256 `c448160dba5ce79c965cb075ee02e18d1c42eb6424f787e5869790d577b56a65`。
- [configs/models/qwen-image-2512/scheduler/scheduler_config.json](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/scheduler/scheduler_config.json)，SHA256 `7ee767e37bae4af31d4eb935e125bb20a2237eeecafd22af6610093865c6f587`。
- [sources/image-generation/pipeline_qwenimage.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/pipelines/qwenimage/pipeline_qwenimage.py)，SHA256 `e811b4379675fec4e39a777134a49926bde5644ace8d5c30136be7a4778bd74f`。
- [sources/image-generation/transformer_qwenimage.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/transformers/transformer_qwenimage.py)，SHA256 `cea921e2dd8bba5fcd86ae99054d7320b2773cc653c04c218983d54e737e2cc5`。
- [sources/image-generation/pipeline_flux2_klein.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py)，SHA256 `8a57a8a7f1c22fc0c5bc5d3fd1bd9bc76c17c1f4d6644cc73370651dd955358e`。
- [sources/image-generation/transformer_flux2.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/transformers/transformer_flux2.py)，SHA256 `88cbc0569409698efbdaa5cd25403b78fb6607b9cf1b15855bc392b2ad0c1607`。
- [sources/image-generation/autoencoder_kl_flux2.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/autoencoder_kl_flux2.py)，SHA256 `7d9a976c1e4f42615e8c422f1643d86b49c4339221bd04b67f518b718ebd6c2d`。
- [sources/image-generation/autoencoder_kl_qwenimage.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/autoencoder_kl_qwenimage.py)，SHA256 `db8b9869c16b6e5274b5c4db20b488cf68a2f6a78bc1bee08936f2ae65fb8042`。
- [sources/image-generation/attention.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/attention.py)，SHA256 `3c61df6cc4832149eb654c1e82220f4a6b91daca13741c957c4e0faff7810adf`。
- [sources/image-generation/embeddings.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/embeddings.py)，SHA256 `4eb810f715786eb1f24f2a4641e529817f7c951b9caf2f7925811329a03ec796`。
- [sources/image-generation/normalization.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/normalization.py)，SHA256 `e92ebbb130082578f3cff3361891a1adaa32331347e7bb09e4c70b208a0a6059`。
- [sources/image-generation/flux2-model_index.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/model_index.json)，SHA256 `51a76cb1cf3ed37423a1128c79c22faee8e6fbe7f5aaeb737f0a258930dbaac0`。
- [sources/image-generation/qwenimage-model_index.json](https://huggingface.co/Qwen/Qwen-Image-2512/resolve/25468b98e3276ca6700de15c6628e51b7de54a26/model_index.json)，SHA256 `caf5f49ee3d897fff6a8e8d6353b084c8d1da3e40ba2f32e9bc554eb0ee4b4e9`。
- [sources/image-generation/attention_processor.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/attention_processor.py)，SHA256 `7158a23bff0ce5bb1c03d66e2441dfd8d169b3598b2d494d32c6f88a3301ea01`。
- [sources/image-generation/modeling_qwen2_5_vl.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen2_5_vl/modeling_qwen2_5_vl.py)，SHA256 `72bdd5615b7527543ea7e6d69fbe194c40bddd94cab13e2e83696ff1cfb10719`。
- [sources/image-generation/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/image-generation/vae.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/vae.py)，SHA256 `8e6abad3bd7b7806dd9c6c451b2438641ef728d7884e6bfed37b867f719b98fc`。
- [sources/image-generation/unet_2d_blocks.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/unets/unet_2d_blocks.py)，SHA256 `545d158c9d98fb8971c501303117fd3e32d27ae28506b89005c65548404f7437`。
- [sources/image-generation/resnet.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/resnet.py)，SHA256 `329975c03ddf3baa5528ace0e2be62f4224746700be4fda57dcbabb209569e9c`。
- [sources/image-generation/upsampling.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/upsampling.py)，SHA256 `d6410c71fa01c5363c6130784a709eb13b5be7e6b401dba7fa930f59b5e5559d`。
- [sources/image-generation/scheduling_flow_match_euler_discrete.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/schedulers/scheduling_flow_match_euler_discrete.py)，SHA256 `1af27be5b2f92b7d139d3c50239be5ce3eafc4a7eddf59c2d30689f8ec31e93d`。
