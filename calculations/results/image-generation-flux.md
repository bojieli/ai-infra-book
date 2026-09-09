# image-generation — flux2-klein-4b

输入：`{"batch": 1, "decoded_dtype": "fp32", "dtype": "bf16", "effective_matrix_service": null, "guidance_scale": null, "height": 1024, "model": "flux2-klein-4b", "negative_prompt_present": true, "negative_text_tokens": 512, "output_type": "image", "qwen_shape_cache_warm": false, "steps": null, "text_tokens": 512, "width": 1024}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| vae_spatial_scale | 8 |
| raw_latent_channels | 32 |
| raw_latent_shape | `[1, 32, 128, 128]` |
| packed_latent_shape | `[1, 4096, 128]` |
| raw_latent_elements | 524,288 |
| packed_latent_elements | 524,288 |
| latent_bytes | 1,048,576 |
| image_tokens | 4,096 |
| hidden_size | 3,072 |
| dual_stream_blocks | 5 |
| single_stream_blocks | 20 |
| denoising_steps | 4 |
| true_cfg_enabled | `false` |
| is_step_distilled | `true` |
| supplied_guidance_ignored | `false` |
| transformer_invocations | 4 |
| branch_count | 1 |
| denoising_matrix_flops | 139,280,712,204,288 |
| matrix_weight_elements_excluding_bias_norm | 3,875,536,896 |
| matrix_weight_bytes_excluding_bias_norm | 7,751,073,792 |
| text_encoder_matrix_flops | 4,196,266,934,272 |
| vae_matrix_flops | 10,474,653,483,008 |
| text_encoder_dense_square_matrix_flops | 4,273,425,350,656 |
| vae_nonpadding_and_attention_flops | 10,442,021,800,960 |
| all_stage_dense_matrix_kernel_flops | 154,028,791,037,952 |
| all_stage_nonpadding_matrix_flops | 153,919,000,939,520 |
| text_encoder_return_live_lower_bytes | 252,575,744 |
| vae_first_frame_feature_cache_bytes | 0 |
| full_runtime_peak_bytes | `null` |
| complete_generation_flops | `null` |
| complete_generation_seconds | `null` |
| vae_decode_calls | 1 |
| decoded_rgb_tensor_bytes | 12,582,912 |
| encoded_image_file_bytes | `null` |
| reference_ordinary_arithmetic_ops | 287,373,657,231 |
| reference_comparisons | 51,368,853,504 |
| reference_special_calls | `{"rsqrt": 23463360, "exp": 57635336706, "sqrt": 128, "log": 4, "sin": 1245696, "cos": 1245696, "pow": 516}` |
| declared_boundary_graph_peak_bytes | 260,440,064 |
| declared_boundary_graph_final_live_bytes | 12,582,912 |
| declared_boundary_graph_final_live_objects | `["decoded_rgb"]` |
| complete_nonmatrix_coverage | `false` |

加入setup helper的声明存活图：`{"helper_invocations": 4, "helper_peak_bytes": 3072, "declared_expanded_graph_peak_bytes": 260440064, "original_boundary_graph_peak_bytes": 260440064, "peak_increment_bytes": 0, "final_live_bytes": 12582912, "final_live_objects": ["decoded_rgb"], "actual_allocator_peak_bytes": null, "scope": "Original boundary graph plus pinned sinusoidal timestep helper and immediate output cast only", "remaining": ["caller-owned timestep inputs and scheduler arrays", "text and DiT rotary-frequency construction lifetimes and persistent tables", "learned timestep projector activations and all other block internals", "actual backend fusion, storage reuse, allocator and device placement"]}`；逐事件见JSON，未覆盖完整allocator。

| 文本编码矩阵 | 左形状 | 权重形状 | 重复 | 矩阵FLOPs |
| --- | --- | --- | ---: | ---: |
| conditional/q | [1, 512, 2560] | [4096, 2560] | 36 | 386547056640 |
| conditional/k | [1, 512, 2560] | [1024, 2560] | 36 | 96636764160 |
| conditional/v | [1, 512, 2560] | [1024, 2560] | 36 | 96636764160 |
| conditional/o | [1, 512, 4096] | [2560, 4096] | 36 | 386547056640 |
| conditional/gate | [1, 512, 2560] | [9728, 2560] | 36 | 918049259520 |
| conditional/up | [1, 512, 2560] | [9728, 2560] | 36 | 918049259520 |
| conditional/down | [1, 512, 9728] | [2560, 9728] | 36 | 918049259520 |
| conditional/unused_full_vocabulary_head | [1, 512, 2560] | [151936, 2560] | 1 | 398291107840 |

| VAE操作 | 输入 | 输出 | kernel | dense核FLOPs | nonpadding FLOPs |
| --- | --- | --- | --- | ---: | ---: |
| post_quant | [1, 32, 128, 128] | [1, 32, 128, 128] | [1, 1, 1] | 33554432 | 33554432 |
| decoder.input | [1, 32, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 4831838208 | 4781637632 |
| mid.residual0.conv1 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| mid.residual0.conv2 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| mid.attention.q | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 1, 1] | 8589934592 | 8589934592 |
| mid.attention.k | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 1, 1] | 8589934592 | 8589934592 |
| mid.attention.v | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 1, 1] | 8589934592 | 8589934592 |
| mid.attention.out | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 1, 1] | 8589934592 | 8589934592 |
| mid.residual1.conv1 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| mid.residual1.conv2 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual0.conv1 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual0.conv2 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual1.conv1 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual1.conv2 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual2.conv1 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.residual2.conv2 | [1, 512, 128, 128] | [1, 512, 128, 128] | [1, 3, 3] | 77309411328 | 76506202112 |
| up0.spatial_conv | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual0.conv1 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual0.conv2 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual1.conv1 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual1.conv2 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual2.conv1 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.residual2.conv2 | [1, 512, 256, 256] | [1, 512, 256, 256] | [1, 3, 3] | 309237645312 | 307629129728 |
| up1.spatial_conv | [1, 512, 512, 512] | [1, 512, 512, 512] | [1, 3, 3] | 1236950581248 | 1233731452928 |
| up2.residual0.shortcut | [1, 512, 512, 512] | [1, 256, 512, 512] | [1, 1, 1] | 68719476736 | 68719476736 |
| up2.residual0.conv1 | [1, 512, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 618475290624 | 616865726464 |
| up2.residual0.conv2 | [1, 256, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 309237645312 | 308432863232 |
| up2.residual1.conv1 | [1, 256, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 309237645312 | 308432863232 |
| up2.residual1.conv2 | [1, 256, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 309237645312 | 308432863232 |
| up2.residual2.conv1 | [1, 256, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 309237645312 | 308432863232 |
| up2.residual2.conv2 | [1, 256, 512, 512] | [1, 256, 512, 512] | [1, 3, 3] | 309237645312 | 308432863232 |
| up2.spatial_conv | [1, 256, 1024, 1024] | [1, 256, 1024, 1024] | [1, 3, 3] | 1236950581248 | 1235340492800 |
| up3.residual0.shortcut | [1, 256, 1024, 1024] | [1, 128, 1024, 1024] | [1, 1, 1] | 68719476736 | 68719476736 |
| up3.residual0.conv1 | [1, 256, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 618475290624 | 617670246400 |
| up3.residual0.conv2 | [1, 128, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 309237645312 | 308835123200 |
| up3.residual1.conv1 | [1, 128, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 309237645312 | 308835123200 |
| up3.residual1.conv2 | [1, 128, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 309237645312 | 308835123200 |
| up3.residual2.conv1 | [1, 128, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 309237645312 | 308835123200 |
| up3.residual2.conv2 | [1, 128, 1024, 1024] | [1, 128, 1024, 1024] | [1, 3, 3] | 309237645312 | 308835123200 |
| decoder.output | [1, 128, 1024, 1024] | [1, 3, 1024, 1024] | [1, 3, 3] | 7247757312 | 7238323200 |

参考非矩阵运算（特殊函数单列）

| stage | operation | elements | vectors | vector_width | ordinary_arithmetic_ops | comparisons | special_calls | reference_accumulator_dtype |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "text_conditional" | "rmsnorm" | 95682560 | 37376 | 2560 | 382767616 | 0 | {"rsqrt": 37376} | "fp32" |
| "text_conditional" | "rope_apply" | 94371840 | 0 | 0 | 283115520 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "silu" | 179306496 | 0 | 0 | 717225984 | 0 | {"exp": 179306496} | "declared_tensor_dtype" |
| "text_conditional" | "multiply" | 179306496 | 0 | 0 | 179306496 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "add" | 94371840 | 0 | 0 | 94371840 | 0 | {} | "declared_tensor_dtype" |
| "text_conditional" | "softmax" | 151289856 | 0 | 0 | 604569600 | 150700032 | {"exp": 151289856} | "fp32" |
| "text_conditional" | "rmsnorm" | 94371840 | 737280 | 128 | 378224640 | 0 | {"rsqrt": 737280} | "fp32" |
| "vae" | "add" | 524288 | 0 | 0 | 524288 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "softmax" | 268435456 | 0 | 0 | 1073725440 | 268419072 | {"exp": 268435456} | "fp32" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 8388608 | 32 | 262144 | 58720288 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 8388608 | 0 | 0 | 33554432 | 0 | {"exp": 8388608} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 8388608 | 0 | 0 | 8388608 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 33554432 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 33554432 | 32 | 1048576 | 234881056 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 33554432 | 0 | 0 | 134217728 | 0 | {"exp": 33554432} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 33554432 | 0 | 0 | 33554432 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 134217728 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 67108864 | 32 | 2097152 | 469762080 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 67108864 | 0 | 0 | 268435456 | 0 | {"exp": 67108864} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 67108864 | 32 | 2097152 | 469762080 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 67108864 | 0 | 0 | 268435456 | 0 | {"exp": 67108864} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 67108864 | 32 | 2097152 | 469762080 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 67108864 | 0 | 0 | 268435456 | 0 | {"exp": 67108864} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 67108864 | 32 | 2097152 | 469762080 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 67108864 | 0 | 0 | 268435456 | 0 | {"exp": 67108864} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 67108864 | 32 | 2097152 | 469762080 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 67108864 | 0 | 0 | 268435456 | 0 | {"exp": 67108864} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 67108864 | 0 | 0 | 67108864 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "nearest_copy" | 268435456 | 0 | 0 | 0 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 268435456 | 0 | 0 | 268435456 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 268435456 | 32 | 8388608 | 1879048224 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 268435456 | 0 | 0 | 1073741824 | 0 | {"exp": 268435456} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "add" | 134217728 | 0 | 0 | 134217728 | 0 | {} | "declared_tensor_dtype" |
| "vae" | "groupnorm" | 134217728 | 32 | 4194304 | 939524128 | 0 | {"rsqrt": 32} | "fp32" |
| "vae" | "silu" | 134217728 | 0 | 0 | 536870912 | 0 | {"exp": 134217728} | "declared_tensor_dtype" |
| "vae" | "add" | 3145728 | 0 | 0 | 3145728 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "layernorm" | 1698693120 | 552960 | 3072 | 8494018560 | 0 | {"rsqrt": 552960} | "fp32" |
| "dit_conditional" | "layernorm" | 50331648 | 16384 | 3072 | 251674624 | 0 | {"rsqrt": 16384} | "fp32" |
| "dit_conditional" | "rmsnorm" | 2831155200 | 22118400 | 128 | 11346739200 | 0 | {"rsqrt": 22118400} | "fp32" |
| "dit_conditional" | "rope_apply" | 2831155200 | 0 | 0 | 8493465600 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "softmax" | 50960793600 | 0 | 0 | 203832115200 | 50949734400 | {"exp": 50960793600} | "fp32" |
| "dit_conditional" | "multiply" | 3447717888 | 0 | 0 | 3447717888 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 3447717888 | 0 | 0 | 3447717888 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "add" | 503808 | 0 | 0 | 503808 | 0 | {} | "declared_tensor_dtype" |
| "dit_conditional" | "silu" | 4246794240 | 0 | 0 | 16987176960 | 0 | {"exp": 4246794240} | "declared_tensor_dtype" |
| "dit_conditional" | "multiply" | 4246732800 | 0 | 0 | 4246732800 | 0 | {} | "declared_tensor_dtype" |
| "scheduler" | "euler_update" | 2097152 | 0 | 0 | 4194308 | 0 | {} | "fp32" |
| "latent_denormalize" | "multiply" | 524288 | 0 | 0 | 524288 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "add" | 524288 | 0 | 0 | 524288 | 0 | {} | "declared_tensor_dtype" |
| "latent_denormalize" | "bn_std" | 128 | 0 | 0 | 128 | 0 | {"sqrt": 128} | "declared_tensor_dtype" |
| "setup" | "timestep_sinusoidal_features" | null | null | null | 2052 | 0 | {"log": 4, "exp": 512, "sin": 512, "cos": 512} | "fp32" |
| "setup" | "pipeline_transformer_timestep_rescale" | null | null | null | 8 | 0 | {} | "bf16" |
| "setup" | "text_conditional_rope_forward" | null | null | null | 163840 | 0 | {"sin": 65536, "cos": 65536} | "fp32" |
| "setup" | "flux_rope_conditional" | null | null | null | 1181216 | 0 | {"pow": 512, "sin": 1179648, "cos": 1179648} | "fp64_standard_reference" |
| "setup" | "scheduler_mu" | null | null | null | 10 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_sigma_endpoint" | null | null | null | 1 | 0 | {} | "python_scalar" |
| "setup" | "scheduler_exponential_shift" | null | null | null | 16 | 0 | {"exp": 2, "pow": 4} | "fp32" |
| "setup" | "scheduler_timestep_scale" | null | null | null | 4 | 0 | {} | "fp32" |

声明边界缓冲区生命周期（非运行时显存峰值）

| event | phase | action | object | bytes | live_bytes_after | live_objects |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | "text_conditional" | "allocate" | "conditional_lm_return" | 252575744 | 252575744 | ["conditional_lm_return"] |
| 1 | "text_conditional" | "allocate" | "conditional_embedding" | 7864320 | 260440064 | ["conditional_lm_return", "conditional_embedding"] |
| 2 | "text_conditional" | "release" | "conditional_lm_return" | 252575744 | 7864320 | ["conditional_embedding"] |
| 3 | "noise_init" | "allocate" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "latent"] |
| 4 | "step_0_conditional" | "allocate" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "prediction"] |
| 5 | "step_0_scheduler" | "allocate" | "scheduler_input_fp32" | 2097152 | 12058624 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 6 | "step_0_scheduler" | "allocate" | "scheduler_output_fp32" | 2097152 | 14155776 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 7 | "step_0_scheduler_cast" | "allocate" | "next_latent" | 1048576 | 15204352 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 8 | "step_0_scheduler" | "release" | "scheduler_input_fp32" | 2097152 | 13107200 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 9 | "step_0_scheduler" | "release" | "scheduler_output_fp32" | 2097152 | 11010048 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 10 | "step_0_scheduler" | "release" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "next_latent"] |
| 11 | "step_0_scheduler" | "release" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "next_latent"] |
| 12 | "step_0_scheduler_commit" | "release" | "next_latent" | 1048576 | 7864320 | ["conditional_embedding"] |
| 13 | "step_0_scheduler_commit" | "allocate" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "latent"] |
| 14 | "step_1_conditional" | "allocate" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "prediction"] |
| 15 | "step_1_scheduler" | "allocate" | "scheduler_input_fp32" | 2097152 | 12058624 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 16 | "step_1_scheduler" | "allocate" | "scheduler_output_fp32" | 2097152 | 14155776 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 17 | "step_1_scheduler_cast" | "allocate" | "next_latent" | 1048576 | 15204352 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 18 | "step_1_scheduler" | "release" | "scheduler_input_fp32" | 2097152 | 13107200 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 19 | "step_1_scheduler" | "release" | "scheduler_output_fp32" | 2097152 | 11010048 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 20 | "step_1_scheduler" | "release" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "next_latent"] |
| 21 | "step_1_scheduler" | "release" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "next_latent"] |
| 22 | "step_1_scheduler_commit" | "release" | "next_latent" | 1048576 | 7864320 | ["conditional_embedding"] |
| 23 | "step_1_scheduler_commit" | "allocate" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "latent"] |
| 24 | "step_2_conditional" | "allocate" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "prediction"] |
| 25 | "step_2_scheduler" | "allocate" | "scheduler_input_fp32" | 2097152 | 12058624 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 26 | "step_2_scheduler" | "allocate" | "scheduler_output_fp32" | 2097152 | 14155776 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 27 | "step_2_scheduler_cast" | "allocate" | "next_latent" | 1048576 | 15204352 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 28 | "step_2_scheduler" | "release" | "scheduler_input_fp32" | 2097152 | 13107200 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 29 | "step_2_scheduler" | "release" | "scheduler_output_fp32" | 2097152 | 11010048 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 30 | "step_2_scheduler" | "release" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "next_latent"] |
| 31 | "step_2_scheduler" | "release" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "next_latent"] |
| 32 | "step_2_scheduler_commit" | "release" | "next_latent" | 1048576 | 7864320 | ["conditional_embedding"] |
| 33 | "step_2_scheduler_commit" | "allocate" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "latent"] |
| 34 | "step_3_conditional" | "allocate" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "prediction"] |
| 35 | "step_3_scheduler" | "allocate" | "scheduler_input_fp32" | 2097152 | 12058624 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32"] |
| 36 | "step_3_scheduler" | "allocate" | "scheduler_output_fp32" | 2097152 | 14155776 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32"] |
| 37 | "step_3_scheduler_cast" | "allocate" | "next_latent" | 1048576 | 15204352 | ["conditional_embedding", "latent", "prediction", "scheduler_input_fp32", "scheduler_output_fp32", "next_latent"] |
| 38 | "step_3_scheduler" | "release" | "scheduler_input_fp32" | 2097152 | 13107200 | ["conditional_embedding", "latent", "prediction", "scheduler_output_fp32", "next_latent"] |
| 39 | "step_3_scheduler" | "release" | "scheduler_output_fp32" | 2097152 | 11010048 | ["conditional_embedding", "latent", "prediction", "next_latent"] |
| 40 | "step_3_scheduler" | "release" | "prediction" | 1048576 | 9961472 | ["conditional_embedding", "latent", "next_latent"] |
| 41 | "step_3_scheduler" | "release" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "next_latent"] |
| 42 | "step_3_scheduler_commit" | "release" | "next_latent" | 1048576 | 7864320 | ["conditional_embedding"] |
| 43 | "step_3_scheduler_commit" | "allocate" | "latent" | 1048576 | 8912896 | ["conditional_embedding", "latent"] |
| 44 | "denoising_complete" | "release" | "conditional_embedding" | 7864320 | 1048576 | ["latent"] |
| 45 | "vae_output" | "allocate" | "decoded_rgb" | 12582912 | 13631488 | ["latent", "decoded_rgb"] |
| 46 | "vae_complete" | "release" | "latent" | 1048576 | 12582912 | ["decoded_rgb"] |

条件式矩阵供给下界：`{"available": false, "declared_serial_matrix_lower_exact_seconds": null, "complete_request_seconds": null, "reason": "No effective matrix service supplied"}`

| 分支/矩阵 | 左形状 | 右形状 | 重复 | 矩阵FLOPs | 左/右/输出逻辑bytes |
| --- | --- | --- | ---: | ---: | --- |
| conditional/image_input | [1, 4096, 128] | [128, 3072] | 1 | 3221225472 | 1048576/786432/25165824 |
| conditional/text_input | [1, 512, 7680] | [7680, 3072] | 1 | 24159191040 | 7864320/47185920/3145728 |
| conditional/timestep_1 | [1, 1, 256] | [256, 3072] | 1 | 1572864 | 512/1572864/6144 |
| conditional/timestep_2 | [1, 1, 3072] | [3072, 3072] | 1 | 18874368 | 6144/18874368/6144 |
| conditional/double_image_q | [1, 4096, 3072] | [3072, 3072] | 5 | 386547056640 | 125829120/94371840/125829120 |
| conditional/double_image_k | [1, 4096, 3072] | [3072, 3072] | 5 | 386547056640 | 125829120/94371840/125829120 |
| conditional/double_image_v | [1, 4096, 3072] | [3072, 3072] | 5 | 386547056640 | 125829120/94371840/125829120 |
| conditional/double_image_out | [1, 4096, 3072] | [3072, 3072] | 5 | 386547056640 | 125829120/94371840/125829120 |
| conditional/double_image_ff_gate_up | [1, 4096, 3072] | [3072, 18432] | 5 | 2319282339840 | 125829120/566231040/754974720 |
| conditional/double_image_ff_down | [1, 4096, 9216] | [9216, 3072] | 5 | 1159641169920 | 377487360/283115520/125829120 |
| conditional/shared_double_image_modulation | [1, 1, 3072] | [3072, 18432] | 1 | 113246208 | 6144/113246208/36864 |
| conditional/double_text_q | [1, 512, 3072] | [3072, 3072] | 5 | 48318382080 | 15728640/94371840/15728640 |
| conditional/double_text_k | [1, 512, 3072] | [3072, 3072] | 5 | 48318382080 | 15728640/94371840/15728640 |
| conditional/double_text_v | [1, 512, 3072] | [3072, 3072] | 5 | 48318382080 | 15728640/94371840/15728640 |
| conditional/double_text_out | [1, 512, 3072] | [3072, 3072] | 5 | 48318382080 | 15728640/94371840/15728640 |
| conditional/double_text_ff_gate_up | [1, 512, 3072] | [3072, 18432] | 5 | 289910292480 | 15728640/566231040/94371840 |
| conditional/double_text_ff_down | [1, 512, 9216] | [9216, 3072] | 5 | 144955146240 | 47185920/283115520/15728640 |
| conditional/shared_double_text_modulation | [1, 1, 3072] | [3072, 18432] | 1 | 113246208 | 6144/113246208/36864 |
| conditional/single_qkv_and_gate_up | [1, 4608, 3072] | [3072, 27648] | 20 | 15655155793920 | 566231040/3397386240/5096079360 |
| conditional/single_attention_and_ff_out | [1, 4608, 12288] | [12288, 3072] | 20 | 6957847019520 | 2264924160/1509949440/566231040 |
| conditional/shared_single_modulation | [1, 1, 3072] | [3072, 9216] | 1 | 56623104 | 6144/56623104/18432 |
| conditional/joint_attention_qk | [24, 4608, 128] | [128, 4608] | 25 | 3261490790400 | 707788800/707788800/25480396800 |
| conditional/joint_attention_pv | [24, 4608, 4608] | [4608, 128] | 25 | 3261490790400 | 25480396800/707788800/707788800 |
| conditional/output_adaln_modulation | [1, 1, 3072] | [3072, 6144] | 1 | 37748736 | 6144/37748736/12288 |
| conditional/image_output | [1, 4096, 3072] | [3072, 128] | 1 | 3221225472 | 25165824/786432/1048576 |

模型初始化与请求setup运算：

- `{"stage": "setup", "operation": "timestep_sinusoidal_features", "scope": "request", "invocations": 4, "ordinary_arithmetic_ops": 2052, "comparisons": 0, "special_calls": {"log": 4, "exp": 512, "sin": 512, "cos": 512}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "pipeline_transformer_timestep_rescale", "scope": "request", "invocations": 4, "ordinary_arithmetic_ops": 8, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "bf16"}`
- `{"stage": "setup", "operation": "text_conditional_rope_forward", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 163840, "comparisons": 0, "special_calls": {"sin": 65536, "cos": 65536}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "flux_rope_conditional", "scope": "request", "invocations": 4, "ordinary_arithmetic_ops": 1181216, "comparisons": 0, "special_calls": {"pow": 512, "sin": 1179648, "cos": 1179648}, "reference_accumulator_dtype": "fp64_standard_reference"}`
- `{"stage": "setup", "operation": "scheduler_mu", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 10, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_sigma_endpoint", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 1, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "python_scalar"}`
- `{"stage": "setup", "operation": "scheduler_exponential_shift", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 16, "comparisons": 0, "special_calls": {"exp": 2, "pow": 4}, "reference_accumulator_dtype": "fp32"}`
- `{"stage": "setup", "operation": "scheduler_timestep_scale", "scope": "request", "invocations": 1, "ordinary_arithmetic_ops": 4, "comparisons": 0, "special_calls": {}, "reference_accumulator_dtype": "fp32"}`

setup转换、索引与随机数（非FLOPs）：

- `{"operation": "pipeline_timestep_to_latent_dtype", "scope": "request", "invocations": 4, "elements_per_invocation": 1, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 4, "logical_input_bytes": 16, "logical_output_bytes": 8, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_to_fp32", "scope": "request", "invocations": 4, "elements_per_invocation": 1, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 4, "logical_input_bytes": 8, "logical_output_bytes": 16, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_features_to_model_dtype", "scope": "request", "invocations": 4, "elements_per_invocation": 256, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 1024, "logical_input_bytes": 4096, "logical_output_bytes": 2048, "actual_device_transfer_bytes": null}`
- `{"operation": "timestep_frequency_index_setup", "scope": "request", "invocations": 4, "integer_arange_elements_per_invocation": 128, "integer_denominator_subtractions_per_invocation": 1}`
- `{"operation": "timestep_sin_cos_concat_and_flip", "scope": "request", "invocations": 4, "output_elements_per_invocation": 512, "nonflops_kind": "tensor materialization", "logical_output_bytes": 8192}`
- `{"operation": "text_conditional_position_ids_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 512, "source_dtype": "int64", "target_dtype": "fp32", "conversion_elements": 512, "logical_input_bytes": 4096, "logical_output_bytes": 2048, "actual_device_transfer_bytes": null}`
- `{"operation": "text_conditional_rope_output_cast", "scope": "request", "invocations": 1, "elements_per_invocation": 131072, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 131072, "logical_input_bytes": 524288, "logical_output_bytes": 262144, "actual_device_transfer_bytes": null}`
- `{"operation": "flux_position_ids_cast", "scope": "request", "invocations": 4, "elements_per_invocation": 18432, "source_dtype": "int64", "target_dtype": "fp32", "conversion_elements": 73728, "logical_input_bytes": 589824, "logical_output_bytes": 294912, "actual_device_transfer_bytes": null}`
- `{"operation": "flux_repeated_cos_sin_cast", "scope": "request", "invocations": 4, "elements_per_invocation": 1179648, "source_dtype": "fp64", "target_dtype": "fp32", "conversion_elements": 4718592, "logical_input_bytes": 37748736, "logical_output_bytes": 18874368, "actual_device_transfer_bytes": null}`
- `{"operation": "flux_rope_repeat_and_concat", "scope": "request", "invocations": 4, "repeat_output_elements_per_invocation": 1179648, "axis_concat_output_elements_per_invocation": 1179648, "joint_concat_output_elements_per_invocation": 1179648, "nonflops_kind": "repeat_interleave and concatenation"}`
- `{"operation": "flux_input_position_ids", "scope": "request", "invocations": 1, "image_cartesian_product_elements": 16384, "image_batch_expand_is_view": true, "text_cartesian_product_and_stack_elements": 4096, "integer_dtype": "int64", "nonflops_kind": "arange/cartesian_prod/stack"}`
- `{"operation": "scheduler_mu_branch_and_index_arithmetic", "scope": "request", "integer_subtractions": 0, "integer_comparisons": 1}`
- `{"operation": "scheduler_linspace", "scope": "request", "invocations": 1, "output_elements": 4, "output_dtype": "numpy_fp64", "ordinary_arithmetic_ops": null, "nonflops_kind": "numpy implementation-dependent construction"}`
- `{"operation": "scheduler_sigmas_fp64_to_fp32", "scope": "request", "invocations": 1, "elements_per_invocation": 4, "source_dtype": "fp64", "target_dtype": "fp32", "conversion_elements": 4, "logical_input_bytes": 32, "logical_output_bytes": 16, "actual_device_transfer_bytes": null}`
- `{"operation": "scheduler_append_terminal_zero", "scope": "request", "invocations": 1, "output_elements": 5, "logical_output_bytes": 20, "nonflops_kind": "concat/fill; not step evaluation"}`
- `{"operation": "initial_noise", "scope": "request", "invocations": 1, "normal_samples": 524288, "output_dtype": "bf16", "logical_output_bytes": 1048576, "rng_algorithm": null}`
- `{"operation": "euler_sample_upcast", "scope": "request", "invocations": 4, "elements_per_invocation": 524288, "source_dtype": "bf16", "target_dtype": "fp32", "conversion_elements": 2097152, "logical_input_bytes": 4194304, "logical_output_bytes": 8388608, "actual_device_transfer_bytes": null}`
- `{"operation": "euler_result_downcast", "scope": "request", "invocations": 4, "elements_per_invocation": 524288, "source_dtype": "fp32", "target_dtype": "bf16", "conversion_elements": 2097152, "logical_input_bytes": 8388608, "logical_output_bytes": 4194304, "actual_device_transfer_bytes": null}`

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

- [sources/flux2-klein-4b/README.md](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/README.md)，SHA256 `bd447051cf2db4bf67b992e563d89c35ebf1123f009c063361a222ab14e1c4f7`。
- [sources/flux2-klein-4b/LICENSE.md](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/LICENSE.md)，SHA256 `ca02bc51900ab07789d1b70283329e7137f5af98f5161c23a1c81fc38a4af1fe`。
- [configs/models/flux2-klein-4b/transformer/config.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/transformer/config.json)，SHA256 `09733c74a3da6d17dd0a0472a091a8950c7c6935889c32c16cc800ede05029de`。
- [configs/models/flux2-klein-4b/vae/config.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/vae/config.json)，SHA256 `0d6dfb69ae95a5e2ac9836284bbb63d8b38ce67b25ba2dff380752b2a10ab948`。
- [configs/models/flux2-klein-4b/text_encoder/config.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/text_encoder/config.json)，SHA256 `214b4c29a0d975e9fddf9994a5673f22cb2c4c5750352f9227c2c3251ebeab40`。
- [configs/models/flux2-klein-4b/scheduler/scheduler_config.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/scheduler/scheduler_config.json)，SHA256 `067afb012cef64553a763447d1efd93daeffcc0123ca7e25b09f8de20b90762e`。
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
