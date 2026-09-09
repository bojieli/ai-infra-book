# image-generation — qwen-image-2512

输入：`{"batch": 4, "decoded_dtype": "fp32", "dtype": "bf16", "effective_matrix_service": null, "guidance_scale": null, "height": 1024, "model": "qwen-image-2512", "negative_prompt_present": true, "negative_text_tokens": 512, "output_type": "image", "qwen_shape_cache_warm": false, "steps": null, "text_tokens": 512, "width": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| vae_spatial_scale | 8 |
| raw_latent_channels | 16 |
| raw_latent_shape | `[4, 16, 128, 128]` |
| packed_latent_shape | `[4, 4096, 64]` |
| raw_latent_elements | 1,048,576 |
| packed_latent_elements | 1,048,576 |
| latent_bytes | 2,097,152 |
| image_tokens | 4,096 |
| hidden_size | 3,072 |
| dual_stream_blocks | 60 |
| single_stream_blocks | 0 |
| denoising_steps | 50 |
| true_cfg_enabled | `true` |
| is_step_distilled | `false` |
| supplied_guidance_ignored | `false` |
| transformer_invocations | 100 |
| branch_count | 2 |
| denoising_matrix_flops | 31,321,568,890,060,800 |
| matrix_weight_elements_excluding_bias_norm | 20,424,818,688 |
| matrix_weight_bytes_excluding_bias_norm | 40,849,637,376 |
| text_encoder_matrix_flops | 62,245,558,222,848 |
| vae_matrix_flops | 46,730,351,476,736 |
| text_encoder_dense_square_matrix_flops | 62,723,346,137,088 |
| vae_nonpadding_and_attention_flops | 18,779,359,093,760 |
| all_stage_dense_matrix_kernel_flops | 31,431,022,587,674,624 |
| all_stage_nonpadding_matrix_flops | 31,402,593,807,377,408 |
| text_encoder_return_live_lower_bytes | 1,243,447,296 |
| vae_first_frame_feature_cache_bytes | 9,665,773,568 |
| full_runtime_peak_bytes | `null` |
| complete_generation_flops | `null` |
| complete_generation_seconds | `null` |
| vae_decode_calls | 1 |
| decoded_rgb_tensor_bytes | 50,331,648 |
| encoded_image_file_bytes | `null` |
| reference_ordinary_arithmetic_ops | 73,854,614,840,671 |
| reference_comparisons | 12,230,006,222,976 |
| reference_special_calls | `{"rsqrt": 5531692176, "exp": 12239899501442, "sqrt": 39583744, "tanh": 1358954496000, "log": 100, "sin": 1728512, "cos": 1728512, "pow": 50}` |
| declared_boundary_graph_peak_bytes | 9,718,202,368 |
| declared_boundary_graph_final_live_bytes | 50,331,648 |
| declared_boundary_graph_final_live_objects | `["decoded_rgb"]` |
| complete_nonmatrix_coverage | `false` |

加入setup helper的声明存活图：`{"helper_invocations": 100, "helper_peak_bytes": 10752, "declared_expanded_graph_peak_bytes": 9718202368, "original_boundary_graph_peak_bytes": 9718202368, "peak_increment_bytes": 0, "final_live_bytes": 50331648, "final_live_objects": ["decoded_rgb"], "actual_allocator_peak_bytes": null, "scope": "Original boundary graph plus pinned sinusoidal timestep helper and immediate output cast only", "remaining": ["caller-owned timestep inputs and scheduler arrays", "text and DiT rotary-frequency construction lifetimes and persistent tables", "learned timestep projector activations and all other block internals", "actual backend fusion, storage reuse, allocator and device placement"]}`；逐事件见JSON，未覆盖完整allocator。

| 文本编码矩阵 | 左形状 | 权重形状 | 重复 | 矩阵FLOPs |
| --- | --- | --- | ---: | ---: |
| conditional/q | [4, 546, 3584] | [3584, 3584] | 28 | 1571001729024 |
| conditional/k | [4, 546, 3584] | [512, 3584] | 28 | 224428818432 |
| conditional/v | [4, 546, 3584] | [512, 3584] | 28 | 224428818432 |
| conditional/o | [4, 546, 3584] | [3584, 3584] | 28 | 1571001729024 |
| conditional/gate | [4, 546, 3584] | [18944, 3584] | 28 | 8303866281984 |
| conditional/up | [4, 546, 3584] | [18944, 3584] | 28 | 8303866281984 |
| conditional/down | [4, 546, 18944] | [3584, 18944] | 28 | 8303866281984 |
| conditional/unused_full_vocabulary_head | [4, 546, 3584] | [152064, 3584] | 1 | 2380548538368 |
| unconditional/q | [4, 546, 3584] | [3584, 3584] | 28 | 1571001729024 |
| unconditional/k | [4, 546, 3584] | [512, 3584] | 28 | 224428818432 |
| unconditional/v | [4, 546, 3584] | [512, 3584] | 28 | 224428818432 |
| unconditional/o | [4, 546, 3584] | [3584, 3584] | 28 | 1571001729024 |
| unconditional/gate | [4, 546, 3584] | [18944, 3584] | 28 | 8303866281984 |
| unconditional/up | [4, 546, 3584] | [18944, 3584] | 28 | 8303866281984 |
| unconditional/down | [4, 546, 18944] | [3584, 18944] | 28 | 8303866281984 |
| unconditional/unused_full_vocabulary_head | [4, 546, 3584] | [152064, 3584] | 1 | 2380548538368 |

| VAE操作 | 输入 | 输出 | kernel | dense核FLOPs | nonpadding FLOPs |
| --- | --- | --- | --- | ---: | ---: |
| post_quant | [4, 16, 1, 128, 128] | [4, 16, 1, 128, 128] | [1, 1, 1] | 33554432 | 33554432 |
| decoder.input | [4, 16, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 21743271936 | 7172456448 |
| mid.residual0.conv1 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| mid.residual0.conv2 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| mid.attention.q | [4, 384, 128, 128] | [4, 384, 128, 128] | [1, 1, 1] | 19327352832 | 19327352832 |
| mid.attention.k | [4, 384, 128, 128] | [4, 384, 128, 128] | [1, 1, 1] | 19327352832 | 19327352832 |
| mid.attention.v | [4, 384, 128, 128] | [4, 384, 128, 128] | [1, 1, 1] | 19327352832 | 19327352832 |
| mid.attention.out | [4, 384, 128, 128] | [4, 384, 128, 128] | [1, 1, 1] | 19327352832 | 19327352832 |
| mid.residual1.conv1 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| mid.residual1.conv2 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual0.conv1 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual0.conv2 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual1.conv1 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual1.conv2 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual2.conv1 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.residual2.conv2 | [4, 384, 1, 128, 128] | [4, 384, 1, 128, 128] | [3, 3, 3] | 521838526464 | 172138954752 |
| up0.spatial_conv | [4, 384, 256, 256] | [4, 192, 256, 256] | [1, 3, 3] | 347892350976 | 346082770944 |
| up1.residual0.shortcut | [4, 192, 1, 256, 256] | [4, 384, 1, 256, 256] | [1, 1, 1] | 38654705664 | 38654705664 |
| up1.residual0.conv1 | [4, 192, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 1043677052928 | 346082770944 |
| up1.residual0.conv2 | [4, 384, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 2087354105856 | 692165541888 |
| up1.residual1.conv1 | [4, 384, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 2087354105856 | 692165541888 |
| up1.residual1.conv2 | [4, 384, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 2087354105856 | 692165541888 |
| up1.residual2.conv1 | [4, 384, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 2087354105856 | 692165541888 |
| up1.residual2.conv2 | [4, 384, 1, 256, 256] | [4, 384, 1, 256, 256] | [3, 3, 3] | 2087354105856 | 692165541888 |
| up1.spatial_conv | [4, 384, 512, 512] | [4, 192, 512, 512] | [1, 3, 3] | 1391569403904 | 1387947884544 |
| up2.residual0.conv1 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.residual0.conv2 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.residual1.conv1 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.residual1.conv2 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.residual2.conv1 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.residual2.conv2 | [4, 192, 1, 512, 512] | [4, 192, 1, 512, 512] | [3, 3, 3] | 2087354105856 | 693973942272 |
| up2.spatial_conv | [4, 192, 1024, 1024] | [4, 96, 1024, 1024] | [1, 3, 3] | 1391569403904 | 1389758054400 |
| up3.residual0.conv1 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| up3.residual0.conv2 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| up3.residual1.conv1 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| up3.residual1.conv2 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| up3.residual2.conv1 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| up3.residual2.conv2 | [4, 96, 1, 1024, 1024] | [4, 96, 1, 1024, 1024] | [3, 3, 3] | 2087354105856 | 694879027200 |
| decoder.output | [4, 96, 1, 1024, 1024] | [4, 3, 1, 1024, 1024] | [3, 3, 3] | 65229815808 | 21714969600 |

参考非矩阵运算（特殊函数单列）

| stage | operation | elements | vectors | vector_width | ordinary_arithmetic_ops | comparisons | special_calls | reference_accumulator_dtype |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "text_conditional" | "rmsnorm" | 446164992 | 124488 | 3584 | 1784784456 | 0 | {"rsqrt": 124488} | "fp32" |
| "text_conditional" | "rope_apply" | 250478592 | 0 | 0 | 751435776 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "silu" | 1158463488 | 0 | 0 | 4633853952 | 0 | {"exp": 1158463488} | "declared_tensor_dtype" |
| "text_conditional" | "multiply" | 1158463488 | 0 | 0 | 1158463488 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "add" | 438337536 | 0 | 0 | 438337536 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "softmax" | 468302016 | 0 | 0 | 1871495808 | 466589760 | {"exp": 468302016} | "fp32" |
| "text_conditional" | "add" | 281788416 | 0 | 0 | 281788416 | 0 | {} | "declared_tensor_dtype" |
| "text_unconditional" | "rmsnorm" | 446164992 | 124488 | 3584 | 1784784456 | 0 | {"rsqrt": 124488} | "fp32" |
| "text_unconditional" | "rope_apply" | 250478592 | 0 | 0 | 751435776 | 0 | {} | "declared_tensor_dtype" |
| "text_unconditional" | "silu" | 1158463488 | 0 | 0 | 4633853952 | 0 | {"exp": 1158463488} | "declared_tensor_dtype" |
| "text_unconditional" | "multiply" | 1158463488 | 0 | 0 | 1158463488 | 0 | {} | "declared_tensor_dtype" |
| "text_unconditional" | "add" | 438337536 | 0 | 0 | 438337536 | 0 | {} | "declared_tensor_dtype" |
| "text_unconditional" | "softmax" | 468302016 | 0 | 0 | 1871495808 | 466589760 | {"exp": 468302016} | "fp32" |
| "text_unconditional" | "add" | 281788416 | 0 | 0 | 281788416 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 1048576 | 0 | 0 | 1048576 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "silu" | 25165824 | 0 | 0 | 100663296 | 0 | {"exp": 25165824} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 25165824 | 65536 | 384 | 150929408 | 65536 | {"sqrt": 65536} | "fp32" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 25165824 | 0 | 0 | 25165824 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "softmax" | 1073741824 | 0 | 0 | 4294901760 | 1073676288 | {"exp": 1073741824} | "fp32" |
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
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 50331648 | 262144 | 192 | 301727744 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 50331648 | 0 | 0 | 201326592 | 0 | {"exp": 50331648} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 262144 | 384 | 603717632 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 262144 | 384 | 603717632 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 262144 | 384 | 603717632 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 262144 | 384 | 603717632 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 100663296 | 262144 | 384 | 603717632 | 262144 | {"sqrt": 262144} | "fp32" |
| "vae" | "silu" | 100663296 | 0 | 0 | 402653184 | 0 | {"exp": 100663296} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 100663296 | 0 | 0 | 100663296 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 402653184 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 201326592 | 1048576 | 192 | 1206910976 | 1048576 | {"sqrt": 1048576} | "fp32" |
| "vae" | "silu" | 201326592 | 0 | 0 | 805306368 | 0 | {"exp": 201326592} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 201326592 | 0 | 0 | 201326592 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 805306368 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 402653184 | 0 | 0 | 402653184 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "l2_normalize_scale" | 402653184 | 4194304 | 96 | 2411724800 | 4194304 | {"sqrt": 4194304} | "fp32" |
| "vae" | "silu" | 402653184 | 0 | 0 | 1610612736 | 0 | {"exp": 402653184} | "declared_tensor_dtype" |
| "vae" | "add" | 12582912 | 0 | 0 | 12582912 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "clip" | 12582912 | 0 | 0 | 0 | 25165824 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "layernorm" | 339738624000 | 110592000 | 3072 | 1698803712000 | 0 | {"rsqrt": 110592000} | "fp32" |
| "dit_conditional" | "layernorm" | 2516582400 | 819200 | 3072 | 12583731200 | 0 | {"rsqrt": 819200} | "fp32" |
| "dit_conditional" | "rmsnorm" | 339738624000 | 2654208000 | 128 | 1361608704000 | 0 | {"rsqrt": 2654208000} | "fp32" |
| "dit_conditional" | "rmsnorm" | 367001600 | 102400 | 3584 | 1468108800 | 0 | {"rsqrt": 102400} | "fp32" |
| "dit_conditional" | "rope_apply" | 339738624000 | 0 | 0 | 1019215872000 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "softmax" | 6115295232000 | 0 | 0 | 24459853824000 | 6113968128000 | {"exp": 6115295232000} | "fp32" |
| "dit_conditional" | "multiply" | 681993830400 | 0 | 0 | 681993830400 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 681993830400 | 0 | 0 | 681993830400 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 148070400 | 0 | 0 | 148070400 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "gelu_tanh" | 679477248000 | 0 | 0 | 5435817984000 | 0 | {"tanh": 679477248000} | "declared_tensor_dtype" |
| "dit_conditional" | "silu" | 74956800 | 0 | 0 | 299827200 | 0 | {"exp": 74956800} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 1532152217600 | 0 | 0 | 1532152217600 | 0 | {} | "declared_tensor_dtype" |
| "dit_unconditional" | "layernorm" | 339738624000 | 110592000 | 3072 | 1698803712000 | 0 | {"rsqrt": 110592000} | "fp32" |
| "dit_unconditional" | "layernorm" | 2516582400 | 819200 | 3072 | 12583731200 | 0 | {"rsqrt": 819200} | "fp32" |
| "dit_unconditional" | "rmsnorm" | 339738624000 | 2654208000 | 128 | 1361608704000 | 0 | {"rsqrt": 2654208000} | "fp32" |
| "dit_unconditional" | "rmsnorm" | 367001600 | 102400 | 3584 | 1468108800 | 0 | {"rsqrt": 102400} | "fp32" |
| "dit_unconditional" | "rope_apply" | 339738624000 | 0 | 0 | 1019215872000 | 0 | {} | "declared_tensor_dtype" |
| "dit_unconditional" | "softmax" | 6115295232000 | 0 | 0 | 24459853824000 | 6113968128000 | {"exp": 6115295232000} | "fp32" |
| "dit_unconditional" | "multiply" | 681993830400 | 0 | 0 | 681993830400 | 0 | {} | "declared_tensor_dtype" |
| "dit_unconditional" | "add" | 681993830400 | 0 | 0 | 681993830400 | 0 | {} | "declared_tensor_dtype" |
| "dit_unconditional" | "add" | 148070400 | 0 | 0 | 148070400 | 0 | {} | "declared_tensor_dtype" |
| "dit_unconditional" | "gelu_tanh" | 679477248000 | 0 | 0 | 5435817984000 | 0 | {"tanh": 679477248000} | "declared_tensor_dtype" |
| "dit_unconditional" | "silu" | 74956800 | 0 | 0 | 299827200 | 0 | {"exp": 74956800} | "declared_tensor_dtype" |
| "dit_unconditional" | "add" | 1532152217600 | 0 | 0 | 1532152217600 | 0 | {} | "declared_tensor_dtype" |
| "cfg" | "reference_cfg_with_two_vector_norms" | 52428800 | 819200 | 64 | 418611200 | 0 | {"sqrt": 1638400} | "fp32" |
| "scheduler" | "euler_update" | 52428800 | 0 | 0 | 104857650 | 0 | {} | "fp32" |
| "latent_denormalize" | "divide" | 1048576 | 0 | 0 | 1048576 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "add" | 1048576 | 0 | 0 | 1048576 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "divide" | 16 | 0 | 0 | 16 | 0 | {} | "declared_tensor_dtype" |
| "setup" | "timestep_sinusoidal_features" | null | null | null | 128100 | 0 | {"log": 100, "exp": 12800, "sin": 51200, "cos": 51200} | "fp32" |
| "setup" | "pipeline_transformer_timestep_rescale" | null | null | null | 400 | 0 | {} | "bf16" |
| "setup" | "text_conditional_rope_forward" | null | null | null | 2096640 | 0 | {"sin": 838656, "cos": 838656} | "fp32" |
| "setup" | "text_unconditional_rope_forward" | null | null | null | 2096640 | 0 | {"sin": 838656, "cos": 838656} | "fp32" |
| "setup" | "scheduler_mu" | null | null | null | 6 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_sigma_endpoint" | null | null | null | 1 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_exponential_shift" | null | null | null | 200 | 0 | {"exp": 2, "pow": 50} | "fp32" |
| "setup" | "scheduler_terminal_stretch" | null | null | null | 152 | 0 | {} | "fp32" |
| "setup" | "scheduler_timestep_scale" | null | null | null | 50 | 0 | {} | "fp32" |

声明边界缓冲区生命周期（非运行时显存峰值）

| event | phase | action | object | bytes | live_bytes_after | live_objects |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | "text_conditional" | "allocate" | "conditional_lm_return" | 1243447296 | 1243447296 | ["conditional_lm_return"] |
| 1 | "text_conditional" | "allocate" | "conditional_embedding" | 14680064 | 1258127360 | ["conditional_lm_return", "conditional_embedding"] |
| 2 | "text_conditional" | "release" | "conditional_lm_return" | 1243447296 | 14680064 | ["conditional_embedding"] |
| 3 | "text_unconditional" | "allocate" | "unconditional_lm_return" | 1243447296 | 1258127360 | ["conditional_embedding", "unconditional_lm_return"] |
| 4 | "text_unconditional" | "allocate" | "unconditional_embedding" | 14680064 | 1272807424 | ["conditional_embedding", "unconditional_lm_return", "unconditional_embedding"] |
| 5 | "text_unconditional" | "release" | "unconditional_lm_return" | 1243447296 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 6 | "noise_init" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 7 | "step_0_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 8 | "step_0_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 9 | "step_0_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 10 | "step_0_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 11 | "step_0_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 12 | "step_0_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 13 | "step_0_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 14 | "step_0_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 15 | "step_0_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 16 | "step_0_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 17 | "step_0_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 18 | "step_0_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 19 | "step_0_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 20 | "step_0_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 21 | "step_0_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 22 | "step_0_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 23 | "step_1_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 24 | "step_1_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 25 | "step_1_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 26 | "step_1_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 27 | "step_1_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 28 | "step_1_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 29 | "step_1_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 30 | "step_1_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 31 | "step_1_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 32 | "step_1_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 33 | "step_1_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 34 | "step_1_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 35 | "step_1_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 36 | "step_1_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 37 | "step_1_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 38 | "step_1_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 39 | "step_2_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 40 | "step_2_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 41 | "step_2_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 42 | "step_2_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 43 | "step_2_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 44 | "step_2_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 45 | "step_2_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 46 | "step_2_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 47 | "step_2_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 48 | "step_2_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 49 | "step_2_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 50 | "step_2_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 51 | "step_2_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 52 | "step_2_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 53 | "step_2_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 54 | "step_2_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 55 | "step_3_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 56 | "step_3_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 57 | "step_3_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 58 | "step_3_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 59 | "step_3_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 60 | "step_3_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 61 | "step_3_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 62 | "step_3_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 63 | "step_3_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 64 | "step_3_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 65 | "step_3_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 66 | "step_3_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 67 | "step_3_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 68 | "step_3_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 69 | "step_3_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 70 | "step_3_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 71 | "step_4_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 72 | "step_4_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 73 | "step_4_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 74 | "step_4_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 75 | "step_4_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 76 | "step_4_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 77 | "step_4_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 78 | "step_4_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 79 | "step_4_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 80 | "step_4_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 81 | "step_4_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 82 | "step_4_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 83 | "step_4_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 84 | "step_4_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 85 | "step_4_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 86 | "step_4_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 87 | "step_5_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 88 | "step_5_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 89 | "step_5_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 90 | "step_5_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 91 | "step_5_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 92 | "step_5_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 93 | "step_5_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 94 | "step_5_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 95 | "step_5_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 96 | "step_5_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 97 | "step_5_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 98 | "step_5_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 99 | "step_5_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 100 | "step_5_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 101 | "step_5_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 102 | "step_5_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 103 | "step_6_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 104 | "step_6_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 105 | "step_6_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 106 | "step_6_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 107 | "step_6_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 108 | "step_6_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 109 | "step_6_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 110 | "step_6_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 111 | "step_6_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 112 | "step_6_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 113 | "step_6_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 114 | "step_6_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 115 | "step_6_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 116 | "step_6_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 117 | "step_6_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 118 | "step_6_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 119 | "step_7_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 120 | "step_7_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 121 | "step_7_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 122 | "step_7_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 123 | "step_7_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 124 | "step_7_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 125 | "step_7_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 126 | "step_7_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 127 | "step_7_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 128 | "step_7_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 129 | "step_7_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 130 | "step_7_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 131 | "step_7_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 132 | "step_7_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 133 | "step_7_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 134 | "step_7_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 135 | "step_8_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 136 | "step_8_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 137 | "step_8_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 138 | "step_8_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 139 | "step_8_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 140 | "step_8_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 141 | "step_8_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 142 | "step_8_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 143 | "step_8_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 144 | "step_8_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 145 | "step_8_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 146 | "step_8_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 147 | "step_8_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 148 | "step_8_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 149 | "step_8_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 150 | "step_8_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 151 | "step_9_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 152 | "step_9_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 153 | "step_9_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 154 | "step_9_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 155 | "step_9_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 156 | "step_9_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 157 | "step_9_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 158 | "step_9_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 159 | "step_9_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 160 | "step_9_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 161 | "step_9_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 162 | "step_9_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 163 | "step_9_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 164 | "step_9_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 165 | "step_9_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 166 | "step_9_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 167 | "step_10_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 168 | "step_10_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 169 | "step_10_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 170 | "step_10_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 171 | "step_10_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 172 | "step_10_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 173 | "step_10_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 174 | "step_10_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 175 | "step_10_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 176 | "step_10_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 177 | "step_10_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 178 | "step_10_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 179 | "step_10_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 180 | "step_10_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 181 | "step_10_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 182 | "step_10_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 183 | "step_11_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 184 | "step_11_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 185 | "step_11_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 186 | "step_11_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 187 | "step_11_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 188 | "step_11_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 189 | "step_11_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 190 | "step_11_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 191 | "step_11_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 192 | "step_11_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 193 | "step_11_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 194 | "step_11_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 195 | "step_11_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 196 | "step_11_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 197 | "step_11_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 198 | "step_11_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 199 | "step_12_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 200 | "step_12_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 201 | "step_12_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 202 | "step_12_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 203 | "step_12_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 204 | "step_12_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 205 | "step_12_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 206 | "step_12_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 207 | "step_12_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 208 | "step_12_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 209 | "step_12_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 210 | "step_12_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 211 | "step_12_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 212 | "step_12_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 213 | "step_12_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 214 | "step_12_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 215 | "step_13_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 216 | "step_13_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 217 | "step_13_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 218 | "step_13_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 219 | "step_13_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 220 | "step_13_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 221 | "step_13_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 222 | "step_13_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 223 | "step_13_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 224 | "step_13_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 225 | "step_13_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 226 | "step_13_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 227 | "step_13_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 228 | "step_13_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 229 | "step_13_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 230 | "step_13_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 231 | "step_14_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 232 | "step_14_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 233 | "step_14_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 234 | "step_14_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 235 | "step_14_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 236 | "step_14_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 237 | "step_14_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 238 | "step_14_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 239 | "step_14_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 240 | "step_14_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 241 | "step_14_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 242 | "step_14_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 243 | "step_14_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 244 | "step_14_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 245 | "step_14_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 246 | "step_14_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 247 | "step_15_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 248 | "step_15_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 249 | "step_15_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 250 | "step_15_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 251 | "step_15_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 252 | "step_15_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 253 | "step_15_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 254 | "step_15_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 255 | "step_15_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 256 | "step_15_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 257 | "step_15_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 258 | "step_15_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 259 | "step_15_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 260 | "step_15_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 261 | "step_15_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 262 | "step_15_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 263 | "step_16_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 264 | "step_16_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 265 | "step_16_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 266 | "step_16_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 267 | "step_16_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 268 | "step_16_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 269 | "step_16_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 270 | "step_16_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 271 | "step_16_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 272 | "step_16_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 273 | "step_16_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 274 | "step_16_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 275 | "step_16_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 276 | "step_16_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 277 | "step_16_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 278 | "step_16_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 279 | "step_17_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 280 | "step_17_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 281 | "step_17_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 282 | "step_17_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 283 | "step_17_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 284 | "step_17_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 285 | "step_17_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 286 | "step_17_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 287 | "step_17_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 288 | "step_17_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 289 | "step_17_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 290 | "step_17_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 291 | "step_17_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 292 | "step_17_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 293 | "step_17_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 294 | "step_17_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 295 | "step_18_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 296 | "step_18_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 297 | "step_18_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 298 | "step_18_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 299 | "step_18_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 300 | "step_18_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 301 | "step_18_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 302 | "step_18_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 303 | "step_18_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 304 | "step_18_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 305 | "step_18_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 306 | "step_18_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 307 | "step_18_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 308 | "step_18_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 309 | "step_18_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 310 | "step_18_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 311 | "step_19_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 312 | "step_19_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 313 | "step_19_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 314 | "step_19_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 315 | "step_19_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 316 | "step_19_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 317 | "step_19_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 318 | "step_19_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 319 | "step_19_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 320 | "step_19_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 321 | "step_19_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 322 | "step_19_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 323 | "step_19_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 324 | "step_19_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 325 | "step_19_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 326 | "step_19_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 327 | "step_20_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 328 | "step_20_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 329 | "step_20_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 330 | "step_20_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 331 | "step_20_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 332 | "step_20_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 333 | "step_20_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 334 | "step_20_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 335 | "step_20_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 336 | "step_20_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 337 | "step_20_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 338 | "step_20_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 339 | "step_20_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 340 | "step_20_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 341 | "step_20_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 342 | "step_20_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 343 | "step_21_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 344 | "step_21_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 345 | "step_21_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 346 | "step_21_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 347 | "step_21_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 348 | "step_21_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 349 | "step_21_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 350 | "step_21_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 351 | "step_21_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 352 | "step_21_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 353 | "step_21_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 354 | "step_21_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 355 | "step_21_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 356 | "step_21_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 357 | "step_21_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 358 | "step_21_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 359 | "step_22_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 360 | "step_22_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 361 | "step_22_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 362 | "step_22_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 363 | "step_22_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 364 | "step_22_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 365 | "step_22_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 366 | "step_22_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 367 | "step_22_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 368 | "step_22_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 369 | "step_22_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 370 | "step_22_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 371 | "step_22_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 372 | "step_22_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 373 | "step_22_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 374 | "step_22_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 375 | "step_23_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 376 | "step_23_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 377 | "step_23_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 378 | "step_23_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 379 | "step_23_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 380 | "step_23_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 381 | "step_23_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 382 | "step_23_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 383 | "step_23_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 384 | "step_23_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 385 | "step_23_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 386 | "step_23_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 387 | "step_23_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 388 | "step_23_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 389 | "step_23_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 390 | "step_23_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 391 | "step_24_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 392 | "step_24_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 393 | "step_24_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 394 | "step_24_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 395 | "step_24_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 396 | "step_24_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 397 | "step_24_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 398 | "step_24_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 399 | "step_24_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 400 | "step_24_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 401 | "step_24_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 402 | "step_24_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 403 | "step_24_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 404 | "step_24_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 405 | "step_24_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 406 | "step_24_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 407 | "step_25_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 408 | "step_25_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 409 | "step_25_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 410 | "step_25_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 411 | "step_25_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 412 | "step_25_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 413 | "step_25_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 414 | "step_25_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 415 | "step_25_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 416 | "step_25_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 417 | "step_25_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 418 | "step_25_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 419 | "step_25_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 420 | "step_25_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 421 | "step_25_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 422 | "step_25_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 423 | "step_26_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 424 | "step_26_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 425 | "step_26_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 426 | "step_26_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 427 | "step_26_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 428 | "step_26_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 429 | "step_26_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 430 | "step_26_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 431 | "step_26_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 432 | "step_26_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 433 | "step_26_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 434 | "step_26_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 435 | "step_26_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 436 | "step_26_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 437 | "step_26_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 438 | "step_26_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 439 | "step_27_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 440 | "step_27_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 441 | "step_27_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 442 | "step_27_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 443 | "step_27_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 444 | "step_27_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 445 | "step_27_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 446 | "step_27_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 447 | "step_27_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 448 | "step_27_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 449 | "step_27_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 450 | "step_27_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 451 | "step_27_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 452 | "step_27_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 453 | "step_27_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 454 | "step_27_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 455 | "step_28_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 456 | "step_28_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 457 | "step_28_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 458 | "step_28_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 459 | "step_28_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 460 | "step_28_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 461 | "step_28_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 462 | "step_28_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 463 | "step_28_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 464 | "step_28_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 465 | "step_28_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 466 | "step_28_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 467 | "step_28_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 468 | "step_28_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 469 | "step_28_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 470 | "step_28_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 471 | "step_29_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 472 | "step_29_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 473 | "step_29_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 474 | "step_29_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 475 | "step_29_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 476 | "step_29_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 477 | "step_29_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 478 | "step_29_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 479 | "step_29_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 480 | "step_29_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 481 | "step_29_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 482 | "step_29_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 483 | "step_29_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 484 | "step_29_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 485 | "step_29_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 486 | "step_29_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 487 | "step_30_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 488 | "step_30_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 489 | "step_30_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 490 | "step_30_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 491 | "step_30_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 492 | "step_30_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 493 | "step_30_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 494 | "step_30_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 495 | "step_30_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 496 | "step_30_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 497 | "step_30_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 498 | "step_30_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 499 | "step_30_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 500 | "step_30_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 501 | "step_30_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 502 | "step_30_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 503 | "step_31_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 504 | "step_31_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 505 | "step_31_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 506 | "step_31_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 507 | "step_31_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 508 | "step_31_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 509 | "step_31_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 510 | "step_31_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 511 | "step_31_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 512 | "step_31_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 513 | "step_31_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 514 | "step_31_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 515 | "step_31_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 516 | "step_31_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 517 | "step_31_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 518 | "step_31_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 519 | "step_32_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 520 | "step_32_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 521 | "step_32_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 522 | "step_32_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 523 | "step_32_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 524 | "step_32_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 525 | "step_32_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 526 | "step_32_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 527 | "step_32_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 528 | "step_32_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 529 | "step_32_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 530 | "step_32_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 531 | "step_32_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 532 | "step_32_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 533 | "step_32_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 534 | "step_32_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 535 | "step_33_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 536 | "step_33_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 537 | "step_33_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 538 | "step_33_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 539 | "step_33_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 540 | "step_33_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 541 | "step_33_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 542 | "step_33_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 543 | "step_33_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 544 | "step_33_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 545 | "step_33_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 546 | "step_33_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 547 | "step_33_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 548 | "step_33_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 549 | "step_33_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 550 | "step_33_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 551 | "step_34_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 552 | "step_34_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 553 | "step_34_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 554 | "step_34_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 555 | "step_34_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 556 | "step_34_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 557 | "step_34_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 558 | "step_34_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 559 | "step_34_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 560 | "step_34_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 561 | "step_34_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 562 | "step_34_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 563 | "step_34_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 564 | "step_34_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 565 | "step_34_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 566 | "step_34_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 567 | "step_35_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 568 | "step_35_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 569 | "step_35_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 570 | "step_35_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 571 | "step_35_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 572 | "step_35_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 573 | "step_35_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 574 | "step_35_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 575 | "step_35_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 576 | "step_35_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 577 | "step_35_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 578 | "step_35_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 579 | "step_35_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 580 | "step_35_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 581 | "step_35_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 582 | "step_35_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 583 | "step_36_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 584 | "step_36_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 585 | "step_36_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 586 | "step_36_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 587 | "step_36_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 588 | "step_36_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 589 | "step_36_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 590 | "step_36_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 591 | "step_36_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 592 | "step_36_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 593 | "step_36_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 594 | "step_36_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 595 | "step_36_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 596 | "step_36_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 597 | "step_36_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 598 | "step_36_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 599 | "step_37_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 600 | "step_37_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 601 | "step_37_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 602 | "step_37_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 603 | "step_37_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 604 | "step_37_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 605 | "step_37_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 606 | "step_37_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 607 | "step_37_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 608 | "step_37_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 609 | "step_37_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 610 | "step_37_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 611 | "step_37_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 612 | "step_37_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 613 | "step_37_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 614 | "step_37_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 615 | "step_38_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 616 | "step_38_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 617 | "step_38_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 618 | "step_38_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 619 | "step_38_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 620 | "step_38_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 621 | "step_38_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 622 | "step_38_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 623 | "step_38_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 624 | "step_38_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 625 | "step_38_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 626 | "step_38_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 627 | "step_38_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 628 | "step_38_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 629 | "step_38_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 630 | "step_38_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 631 | "step_39_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 632 | "step_39_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 633 | "step_39_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 634 | "step_39_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 635 | "step_39_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 636 | "step_39_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 637 | "step_39_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 638 | "step_39_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 639 | "step_39_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 640 | "step_39_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 641 | "step_39_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 642 | "step_39_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 643 | "step_39_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 644 | "step_39_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 645 | "step_39_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 646 | "step_39_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 647 | "step_40_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 648 | "step_40_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 649 | "step_40_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 650 | "step_40_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 651 | "step_40_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 652 | "step_40_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 653 | "step_40_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 654 | "step_40_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 655 | "step_40_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 656 | "step_40_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 657 | "step_40_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 658 | "step_40_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 659 | "step_40_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 660 | "step_40_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 661 | "step_40_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 662 | "step_40_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 663 | "step_41_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 664 | "step_41_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 665 | "step_41_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 666 | "step_41_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 667 | "step_41_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 668 | "step_41_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 669 | "step_41_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 670 | "step_41_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 671 | "step_41_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 672 | "step_41_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 673 | "step_41_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 674 | "step_41_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 675 | "step_41_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 676 | "step_41_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 677 | "step_41_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 678 | "step_41_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 679 | "step_42_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 680 | "step_42_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 681 | "step_42_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 682 | "step_42_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 683 | "step_42_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 684 | "step_42_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 685 | "step_42_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 686 | "step_42_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 687 | "step_42_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 688 | "step_42_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 689 | "step_42_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 690 | "step_42_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 691 | "step_42_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 692 | "step_42_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 693 | "step_42_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 694 | "step_42_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 695 | "step_43_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 696 | "step_43_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 697 | "step_43_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 698 | "step_43_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 699 | "step_43_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 700 | "step_43_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 701 | "step_43_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 702 | "step_43_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 703 | "step_43_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 704 | "step_43_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 705 | "step_43_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 706 | "step_43_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 707 | "step_43_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 708 | "step_43_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 709 | "step_43_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 710 | "step_43_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 711 | "step_44_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 712 | "step_44_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 713 | "step_44_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 714 | "step_44_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 715 | "step_44_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 716 | "step_44_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 717 | "step_44_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 718 | "step_44_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 719 | "step_44_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 720 | "step_44_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 721 | "step_44_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 722 | "step_44_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 723 | "step_44_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 724 | "step_44_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 725 | "step_44_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 726 | "step_44_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 727 | "step_45_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 728 | "step_45_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 729 | "step_45_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 730 | "step_45_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 731 | "step_45_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 732 | "step_45_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 733 | "step_45_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 734 | "step_45_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 735 | "step_45_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 736 | "step_45_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 737 | "step_45_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 738 | "step_45_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 739 | "step_45_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 740 | "step_45_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 741 | "step_45_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 742 | "step_45_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 743 | "step_46_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 744 | "step_46_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 745 | "step_46_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 746 | "step_46_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 747 | "step_46_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 748 | "step_46_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 749 | "step_46_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 750 | "step_46_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 751 | "step_46_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 752 | "step_46_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 753 | "step_46_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 754 | "step_46_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 755 | "step_46_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 756 | "step_46_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 757 | "step_46_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 758 | "step_46_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 759 | "step_47_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 760 | "step_47_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 761 | "step_47_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 762 | "step_47_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 763 | "step_47_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 764 | "step_47_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 765 | "step_47_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 766 | "step_47_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 767 | "step_47_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 768 | "step_47_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 769 | "step_47_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 770 | "step_47_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 771 | "step_47_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 772 | "step_47_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 773 | "step_47_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 774 | "step_47_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 775 | "step_48_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 776 | "step_48_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 777 | "step_48_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 778 | "step_48_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 779 | "step_48_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 780 | "step_48_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 781 | "step_48_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 782 | "step_48_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 783 | "step_48_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 784 | "step_48_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 785 | "step_48_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 786 | "step_48_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 787 | "step_48_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 788 | "step_48_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 789 | "step_48_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 790 | "step_48_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 791 | "step_49_conditional" | "allocate" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 792 | "step_49_negative" | "allocate" | "negative_prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction"] |
| 793 | "step_49_cfg" | "allocate" | "cfg_output" | 2097152 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "negative_prediction", "cfg_output"] |
| 794 | "step_49_cfg" | "release" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "negative_prediction", "cfg_output"] |
| 795 | "step_49_cfg" | "release" | "negative_prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output"] |
| 796 | "step_49_cfg_cast" | "allocate" | "prediction" | 2097152 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "cfg_output", "prediction"] |
| 797 | "step_49_cfg_cast" | "release" | "cfg_output" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction"] |
| 798 | "step_49_scheduler" | "allocate" | "scheduler_input_fp32" | 4194304 | 37748736 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 799 | "step_49_scheduler" | "allocate" | "scheduler_output_fp32" | 4194304 | 41943040 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 800 | "step_49_scheduler_cast" | "allocate" | "next_latent" | 2097152 | 44040192 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 801 | "step_49_scheduler" | "release" | "scheduler_input_fp32" | 4194304 | 39845888 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 802 | "step_49_scheduler" | "release" | "scheduler_output_fp32" | 4194304 | 35651584 | ["conditional_embedding", "unconditional_embedding", "latent", "prediction", "next_latent"] |
| 803 | "step_49_scheduler" | "release" | "prediction" | 2097152 | 33554432 | ["conditional_embedding", "unconditional_embedding", "latent", "next_latent"] |
| 804 | "step_49_scheduler" | "release" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "next_latent"] |
| 805 | "step_49_scheduler_commit" | "release" | "next_latent" | 2097152 | 29360128 | ["conditional_embedding", "unconditional_embedding"] |
| 806 | "step_49_scheduler_commit" | "allocate" | "latent" | 2097152 | 31457280 | ["conditional_embedding", "unconditional_embedding", "latent"] |
| 807 | "denoising_complete" | "release" | "conditional_embedding" | 14680064 | 16777216 | ["unconditional_embedding", "latent"] |
| 808 | "denoising_complete" | "release" | "unconditional_embedding" | 14680064 | 2097152 | ["latent"] |
| 809 | "vae_decoder.input" | "allocate" | "vae_cache_decoder.input" | 2097152 | 4194304 | ["latent", "vae_cache_decoder.input"] |
| 810 | "vae_mid.residual0.conv1" | "allocate" | "vae_cache_mid.residual0.conv1" | 50331648 | 54525952 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1"] |
| 811 | "vae_mid.residual0.conv2" | "allocate" | "vae_cache_mid.residual0.conv2" | 50331648 | 104857600 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2"] |
| 812 | "vae_mid.residual1.conv1" | "allocate" | "vae_cache_mid.residual1.conv1" | 50331648 | 155189248 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1"] |
| 813 | "vae_mid.residual1.conv2" | "allocate" | "vae_cache_mid.residual1.conv2" | 50331648 | 205520896 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2"] |
| 814 | "vae_up0.residual0.conv1" | "allocate" | "vae_cache_up0.residual0.conv1" | 50331648 | 255852544 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1"] |
| 815 | "vae_up0.residual0.conv2" | "allocate" | "vae_cache_up0.residual0.conv2" | 50331648 | 306184192 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2"] |
| 816 | "vae_up0.residual1.conv1" | "allocate" | "vae_cache_up0.residual1.conv1" | 50331648 | 356515840 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1"] |
| 817 | "vae_up0.residual1.conv2" | "allocate" | "vae_cache_up0.residual1.conv2" | 50331648 | 406847488 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2"] |
| 818 | "vae_up0.residual2.conv1" | "allocate" | "vae_cache_up0.residual2.conv1" | 50331648 | 457179136 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1"] |
| 819 | "vae_up0.residual2.conv2" | "allocate" | "vae_cache_up0.residual2.conv2" | 50331648 | 507510784 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2"] |
| 820 | "vae_up1.residual0.conv1" | "allocate" | "vae_cache_up1.residual0.conv1" | 100663296 | 608174080 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1"] |
| 821 | "vae_up1.residual0.conv2" | "allocate" | "vae_cache_up1.residual0.conv2" | 201326592 | 809500672 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2"] |
| 822 | "vae_up1.residual1.conv1" | "allocate" | "vae_cache_up1.residual1.conv1" | 201326592 | 1010827264 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1"] |
| 823 | "vae_up1.residual1.conv2" | "allocate" | "vae_cache_up1.residual1.conv2" | 201326592 | 1212153856 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2"] |
| 824 | "vae_up1.residual2.conv1" | "allocate" | "vae_cache_up1.residual2.conv1" | 201326592 | 1413480448 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1"] |
| 825 | "vae_up1.residual2.conv2" | "allocate" | "vae_cache_up1.residual2.conv2" | 201326592 | 1614807040 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2"] |
| 826 | "vae_up2.residual0.conv1" | "allocate" | "vae_cache_up2.residual0.conv1" | 402653184 | 2017460224 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1"] |
| 827 | "vae_up2.residual0.conv2" | "allocate" | "vae_cache_up2.residual0.conv2" | 402653184 | 2420113408 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2"] |
| 828 | "vae_up2.residual1.conv1" | "allocate" | "vae_cache_up2.residual1.conv1" | 402653184 | 2822766592 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1"] |
| 829 | "vae_up2.residual1.conv2" | "allocate" | "vae_cache_up2.residual1.conv2" | 402653184 | 3225419776 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2"] |
| 830 | "vae_up2.residual2.conv1" | "allocate" | "vae_cache_up2.residual2.conv1" | 402653184 | 3628072960 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1"] |
| 831 | "vae_up2.residual2.conv2" | "allocate" | "vae_cache_up2.residual2.conv2" | 402653184 | 4030726144 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2"] |
| 832 | "vae_up3.residual0.conv1" | "allocate" | "vae_cache_up3.residual0.conv1" | 805306368 | 4836032512 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1"] |
| 833 | "vae_up3.residual0.conv2" | "allocate" | "vae_cache_up3.residual0.conv2" | 805306368 | 5641338880 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2"] |
| 834 | "vae_up3.residual1.conv1" | "allocate" | "vae_cache_up3.residual1.conv1" | 805306368 | 6446645248 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1"] |
| 835 | "vae_up3.residual1.conv2" | "allocate" | "vae_cache_up3.residual1.conv2" | 805306368 | 7251951616 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2"] |
| 836 | "vae_up3.residual2.conv1" | "allocate" | "vae_cache_up3.residual2.conv1" | 805306368 | 8057257984 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1"] |
| 837 | "vae_up3.residual2.conv2" | "allocate" | "vae_cache_up3.residual2.conv2" | 805306368 | 8862564352 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2"] |
| 838 | "vae_decoder.output" | "allocate" | "vae_cache_decoder.output" | 805306368 | 9667870720 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output"] |
| 839 | "vae_output" | "allocate" | "decoded_rgb" | 50331648 | 9718202368 | ["latent", "vae_cache_decoder.input", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 840 | "vae_clear_cache" | "release" | "vae_cache_decoder.input" | 2097152 | 9716105216 | ["latent", "vae_cache_mid.residual0.conv1", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 841 | "vae_clear_cache" | "release" | "vae_cache_mid.residual0.conv1" | 50331648 | 9665773568 | ["latent", "vae_cache_mid.residual0.conv2", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 842 | "vae_clear_cache" | "release" | "vae_cache_mid.residual0.conv2" | 50331648 | 9615441920 | ["latent", "vae_cache_mid.residual1.conv1", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 843 | "vae_clear_cache" | "release" | "vae_cache_mid.residual1.conv1" | 50331648 | 9565110272 | ["latent", "vae_cache_mid.residual1.conv2", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 844 | "vae_clear_cache" | "release" | "vae_cache_mid.residual1.conv2" | 50331648 | 9514778624 | ["latent", "vae_cache_up0.residual0.conv1", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 845 | "vae_clear_cache" | "release" | "vae_cache_up0.residual0.conv1" | 50331648 | 9464446976 | ["latent", "vae_cache_up0.residual0.conv2", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 846 | "vae_clear_cache" | "release" | "vae_cache_up0.residual0.conv2" | 50331648 | 9414115328 | ["latent", "vae_cache_up0.residual1.conv1", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 847 | "vae_clear_cache" | "release" | "vae_cache_up0.residual1.conv1" | 50331648 | 9363783680 | ["latent", "vae_cache_up0.residual1.conv2", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 848 | "vae_clear_cache" | "release" | "vae_cache_up0.residual1.conv2" | 50331648 | 9313452032 | ["latent", "vae_cache_up0.residual2.conv1", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 849 | "vae_clear_cache" | "release" | "vae_cache_up0.residual2.conv1" | 50331648 | 9263120384 | ["latent", "vae_cache_up0.residual2.conv2", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 850 | "vae_clear_cache" | "release" | "vae_cache_up0.residual2.conv2" | 50331648 | 9212788736 | ["latent", "vae_cache_up1.residual0.conv1", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 851 | "vae_clear_cache" | "release" | "vae_cache_up1.residual0.conv1" | 100663296 | 9112125440 | ["latent", "vae_cache_up1.residual0.conv2", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 852 | "vae_clear_cache" | "release" | "vae_cache_up1.residual0.conv2" | 201326592 | 8910798848 | ["latent", "vae_cache_up1.residual1.conv1", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 853 | "vae_clear_cache" | "release" | "vae_cache_up1.residual1.conv1" | 201326592 | 8709472256 | ["latent", "vae_cache_up1.residual1.conv2", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 854 | "vae_clear_cache" | "release" | "vae_cache_up1.residual1.conv2" | 201326592 | 8508145664 | ["latent", "vae_cache_up1.residual2.conv1", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 855 | "vae_clear_cache" | "release" | "vae_cache_up1.residual2.conv1" | 201326592 | 8306819072 | ["latent", "vae_cache_up1.residual2.conv2", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 856 | "vae_clear_cache" | "release" | "vae_cache_up1.residual2.conv2" | 201326592 | 8105492480 | ["latent", "vae_cache_up2.residual0.conv1", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 857 | "vae_clear_cache" | "release" | "vae_cache_up2.residual0.conv1" | 402653184 | 7702839296 | ["latent", "vae_cache_up2.residual0.conv2", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 858 | "vae_clear_cache" | "release" | "vae_cache_up2.residual0.conv2" | 402653184 | 7300186112 | ["latent", "vae_cache_up2.residual1.conv1", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 859 | "vae_clear_cache" | "release" | "vae_cache_up2.residual1.conv1" | 402653184 | 6897532928 | ["latent", "vae_cache_up2.residual1.conv2", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 860 | "vae_clear_cache" | "release" | "vae_cache_up2.residual1.conv2" | 402653184 | 6494879744 | ["latent", "vae_cache_up2.residual2.conv1", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 861 | "vae_clear_cache" | "release" | "vae_cache_up2.residual2.conv1" | 402653184 | 6092226560 | ["latent", "vae_cache_up2.residual2.conv2", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 862 | "vae_clear_cache" | "release" | "vae_cache_up2.residual2.conv2" | 402653184 | 5689573376 | ["latent", "vae_cache_up3.residual0.conv1", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 863 | "vae_clear_cache" | "release" | "vae_cache_up3.residual0.conv1" | 805306368 | 4884267008 | ["latent", "vae_cache_up3.residual0.conv2", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 864 | "vae_clear_cache" | "release" | "vae_cache_up3.residual0.conv2" | 805306368 | 4078960640 | ["latent", "vae_cache_up3.residual1.conv1", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 865 | "vae_clear_cache" | "release" | "vae_cache_up3.residual1.conv1" | 805306368 | 3273654272 | ["latent", "vae_cache_up3.residual1.conv2", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 866 | "vae_clear_cache" | "release" | "vae_cache_up3.residual1.conv2" | 805306368 | 2468347904 | ["latent", "vae_cache_up3.residual2.conv1", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 867 | "vae_clear_cache" | "release" | "vae_cache_up3.residual2.conv1" | 805306368 | 1663041536 | ["latent", "vae_cache_up3.residual2.conv2", "vae_cache_decoder.output", "decoded_rgb"] |
| 868 | "vae_clear_cache" | "release" | "vae_cache_up3.residual2.conv2" | 805306368 | 857735168 | ["latent", "vae_cache_decoder.output", "decoded_rgb"] |
| 869 | "vae_clear_cache" | "release" | "vae_cache_decoder.output" | 805306368 | 52428800 | ["latent", "decoded_rgb"] |
| 870 | "vae_complete" | "release" | "latent" | 2097152 | 50331648 | ["decoded_rgb"] |

条件式矩阵供给下界：`{"available": false, "declared_serial_matrix_lower_exact_seconds": null, "complete_request_seconds": null, "reason": "No effective matrix service supplied"}`

| 分支/矩阵 | 左形状 | 右形状 | 重复 | 矩阵FLOPs | 左/右/输出逻辑bytes |
| --- | --- | --- | ---: | ---: | --- |
| conditional/image_input | [4, 4096, 64] | [64, 3072] | 1 | 6442450944 | 2097152/393216/100663296 |
| conditional/text_input | [4, 512, 3584] | [3584, 3072] | 1 | 45097156608 | 14680064/22020096/12582912 |
| conditional/timestep_1 | [4, 1, 256] | [256, 3072] | 1 | 6291456 | 2048/1572864/24576 |
| conditional/timestep_2 | [4, 1, 3072] | [3072, 3072] | 1 | 75497472 | 24576/18874368/24576 |
| conditional/double_image_q | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| conditional/double_image_k | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| conditional/double_image_v | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| conditional/double_image_out | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| conditional/double_image_ff_in | [4, 4096, 3072] | [3072, 12288] | 60 | 74217034874880 | 6039797760/4529848320/24159191040 |
| conditional/double_image_ff_out | [4, 4096, 12288] | [12288, 3072] | 60 | 74217034874880 | 24159191040/4529848320/6039797760 |
| conditional/double_image_modulation | [4, 1, 3072] | [3072, 18432] | 60 | 27179089920 | 1474560/6794772480/8847360 |
| conditional/double_text_q | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| conditional/double_text_k | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| conditional/double_text_v | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| conditional/double_text_out | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| conditional/double_text_ff_in | [4, 512, 3072] | [3072, 12288] | 60 | 9277129359360 | 754974720/4529848320/3019898880 |
| conditional/double_text_ff_out | [4, 512, 12288] | [12288, 3072] | 60 | 9277129359360 | 3019898880/4529848320/754974720 |
| conditional/double_text_modulation | [4, 1, 3072] | [3072, 18432] | 60 | 27179089920 | 1474560/6794772480/8847360 |
| conditional/joint_attention_qk | [96, 4608, 128] | [128, 4608] | 60 | 31310311587840 | 6794772480/6794772480/244611809280 |
| conditional/joint_attention_pv | [96, 4608, 4608] | [4608, 128] | 60 | 31310311587840 | 244611809280/6794772480/6794772480 |
| conditional/output_adaln_modulation | [4, 1, 3072] | [3072, 6144] | 1 | 150994944 | 24576/37748736/49152 |
| conditional/image_output | [4, 4096, 3072] | [3072, 64] | 1 | 6442450944 | 100663296/393216/2097152 |
| unconditional/image_input | [4, 4096, 64] | [64, 3072] | 1 | 6442450944 | 2097152/393216/100663296 |
| unconditional/text_input | [4, 512, 3584] | [3584, 3072] | 1 | 45097156608 | 14680064/22020096/12582912 |
| unconditional/timestep_1 | [4, 1, 256] | [256, 3072] | 1 | 6291456 | 2048/1572864/24576 |
| unconditional/timestep_2 | [4, 1, 3072] | [3072, 3072] | 1 | 75497472 | 24576/18874368/24576 |
| unconditional/double_image_q | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| unconditional/double_image_k | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| unconditional/double_image_v | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| unconditional/double_image_out | [4, 4096, 3072] | [3072, 3072] | 60 | 18554258718720 | 6039797760/1132462080/6039797760 |
| unconditional/double_image_ff_in | [4, 4096, 3072] | [3072, 12288] | 60 | 74217034874880 | 6039797760/4529848320/24159191040 |
| unconditional/double_image_ff_out | [4, 4096, 12288] | [12288, 3072] | 60 | 74217034874880 | 24159191040/4529848320/6039797760 |
| unconditional/double_image_modulation | [4, 1, 3072] | [3072, 18432] | 60 | 27179089920 | 1474560/6794772480/8847360 |
| unconditional/double_text_q | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| unconditional/double_text_k | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| unconditional/double_text_v | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| unconditional/double_text_out | [4, 512, 3072] | [3072, 3072] | 60 | 2319282339840 | 754974720/1132462080/754974720 |
| unconditional/double_text_ff_in | [4, 512, 3072] | [3072, 12288] | 60 | 9277129359360 | 754974720/4529848320/3019898880 |
| unconditional/double_text_ff_out | [4, 512, 12288] | [12288, 3072] | 60 | 9277129359360 | 3019898880/4529848320/754974720 |
| unconditional/double_text_modulation | [4, 1, 3072] | [3072, 18432] | 60 | 27179089920 | 1474560/6794772480/8847360 |
| unconditional/joint_attention_qk | [96, 4608, 128] | [128, 4608] | 60 | 31310311587840 | 6794772480/6794772480/244611809280 |
| unconditional/joint_attention_pv | [96, 4608, 4608] | [4608, 128] | 60 | 31310311587840 | 244611809280/6794772480/6794772480 |
| unconditional/output_adaln_modulation | [4, 1, 3072] | [3072, 6144] | 1 | 150994944 | 24576/37748736/49152 |
| unconditional/image_output | [4, 4096, 3072] | [3072, 64] | 1 | 6442450944 | 100663296/393216/2097152 |

模型初始化与请求setup运算：

- `{"stage": "setup", "operation": "timestep_sinusoidal_features", "scope": "request", "invocations": 100, "ordinary_arithmetic_ops": 128100, "comparisons": 0, "special_calls": {"log": 100, "exp": 12800, "sin": 51200, "cos": 51200}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "pipeline_transformer_timestep_rescale", "scope": "request", "invocations": 100, "ordinary_arithmetic_ops": 400, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "bf16"}`
- `{"stage": "setup", "operation": "text_conditional_rope_forward", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 2096640, "comparisons": 0, "special_calls": {"sin": 838656, "cos": 838656}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "text_unconditional_rope_forward", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 2096640, "comparisons": 0, "special_calls": {"sin": 838656, "cos": 838656}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "qwen_rope_constructor_tables", "scope": "model_initialization", "invocations": 1, "ordinary_arithmetic_ops": 524544, "comparisons": 0, "special_calls": {"pow": 128, "polar": 524288}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_mu", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 6, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_sigma_endpoint", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 1, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_exponential_shift", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 200, "comparisons": 0, "special_calls": {"exp": 2, "pow": 50}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_terminal_stretch", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 152, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_timestep_scale", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 50, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "fp32"}`

setup转换、索引与随机数（非FLOPs）：

- `{"operation": "pipeline_timestep_to_latent_dtype", "scope": "request", "invocations": 50, "elements_per_invocation": 4, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 200, "logical_input_bytes": 800, "logical_output_bytes": 400, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_to_fp32", "scope": "request", "invocations": 100, "elements_per_invocation": 4, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 400, "logical_input_bytes": 800, "logical_output_bytes": 1600, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_features_to_model_dtype", "scope": "request", "invocations": 100, "elements_per_invocation": 1024, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 102400, "logical_input_bytes": 409600, "logical_output_bytes": 204800, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_frequency_index_setup", "scope": "request", "invocations": 100, "integer_arange_elements_per_invocation": 128, "integer_denominator_subtractions_per_invocation": 1}`
- `{"operation": "timestep_sin_cos_concat_and_flip", "scope": "request", "invocations": 100, "output_elements_per_invocation": 2048, "nonflops_kind": "tensor materialization", "logical_output_bytes": 819200}`
- `{"operation": "text_conditional_position_ids_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 6552, "source_dtype": "int64", "target_dtype": "fp32", "conversion_elements": 6552, "logical_input_bytes": 52416, "logical_output_bytes": 26208, "actual_device_transfer_bytes": null}`
- `{"operation": "text_conditional_rope_output_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 1677312, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 1677312, "logical_input_bytes": 6709248, "logical_output_bytes": 3354624, "actual_device_transfer_bytes": null}`
- `{"operation": "text_unconditional_position_ids_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 6552, "source_dtype": "int64", "target_dtype": "fp32", "conversion_elements": 6552, "logical_input_bytes": 52416, "logical_output_bytes": 26208, "actual_device_transfer_bytes": null}`
- `{"operation": "text_unconditional_rope_output_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 1677312, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 1677312, "logical_input_bytes": 6709248, "logical_output_bytes": 3354624, "actual_device_transfer_bytes": null}`
- `{"operation": "qwen_rope_constructor_tables", "scope": "model_initialization", "invocations": 1, "integer_arange_elements": 8320, "integer_negate_subtract_ops": 8192, "persistent_table_bytes": 4194304, "output_dtype": "complex64"}`
- `{"operation": "qwen_cached_image_frequency_build", "scope": "request", "invocations": 1, "output_dtype": "complex64", "axes_concat_elements": 3584, "full_image_concat_and_clone_elements": 524288, "logical_output_bytes": 4222976}`
- `{"operation": "qwen_image_rope_cache_and_forward", "scope": "request", "invocations": 100, "cold_unique_keys": 1, "cache_hits": 99, "text_slice_start": 32, "outer_image_concat_output_bytes": 209715200, "tensor_views_are_not_copies": true}`
- `{"operation": "scheduler_mu_branch_and_index_arithmetic", "scope": "request", "integer_subtractions": 1, "integer_comparisons": 0}`
- `{"operation": "scheduler_linspace", "scope": "request", "invocations": 1, "output_elements": 50, "output_dtype": "numpy_fp64", "ordinary_arithmetic_ops": null, "nonflops_kind": "numpy implementation-dependent construction"}`
- `{"operation": "scheduler_sigmas_fp64_to_fp32", "scope": "request", "invocations": 1, "elements_per_invocation": 50, "source_dtype": "fp64", "target_dtype": "fp32", "conversion_elements": 50, "logical_input_bytes": 400, "logical_output_bytes": 200, "actual_device_transfer_bytes": null}`
- `{"operation": "scheduler_append_terminal_zero", "scope": "request", "invocations": 1, "output_elements": 51, "logical_output_bytes": 204, "nonflops_kind": "concat/fill; not step evaluation"}`
- `{"operation": "initial_noise", "scope": "request", "invocations": 1, "normal_samples": 1048576, "output_dtype": "bf16", "logical_output_bytes": 2097152, "rng_algorithm": null}`
- `{"operation": "euler_sample_upcast", "scope": "request", "invocations": 50, "elements_per_invocation": 1048576, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 52428800, "logical_input_bytes": 104857600, "logical_output_bytes": 209715200, "actual_device_transfer_bytes": null}`
- `{"operation": "euler_result_downcast", "scope": "request", "invocations": 50, "elements_per_invocation": 1048576, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 52428800, "logical_input_bytes": 209715200, "logical_output_bytes": 104857600, "actual_device_transfer_bytes": null}`

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
