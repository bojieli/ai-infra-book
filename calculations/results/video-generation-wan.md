# video-generation — wan2.2-ti2v-5b

输入：`{"evaluations_per_step": 2, "frames": 121, "height": 768, "model": "wan2.2-ti2v-5b", "negative_text_tokens": 128, "positive_text_tokens": 256, "reference_audio_tokens": 0, "reference_video_tokens": 0, "regeneration_height": null, "regeneration_steps": 15, "regeneration_width": null, "steps": 30, "text_tokens": 512, "unique_timestep_values": 30, "width": 1344}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| requested_frames | 121 |
| resolved_frames | 121 |
| latent_frames | 31 |
| hidden_size | 3,072 |
| attention_inner_dim | 3,072 |
| layers | 30 |
| matrix_core_flops | 38,269,773,120,798,720 |
| stages | 1 |
| block_modulation_cache | `null` |
| matrix_core_plus_text_and_vae_flops | 40,583,391,656,312,832 |
| matrix_core_plus_text_encoder_flops | 38,279,462,567,018,496 |
| matrix_core_plus_conditioning_flops | `null` |

Wan VAE：首块、第二块与稳定缓存块分别展开；FLOPs已乘repeats。非矩阵及完整工作区另计。

| 阶段/算子 | 类型 | 输入或Q形状 | 输出或V形状 | repeats | 矩阵FLOPs | 逻辑接口bytes |
| --- | --- | --- | --- | --- | --- | --- |
| all_latents_projection/conv2 | CausalConv3d | [1, 48, 31, 48, 84] | [1, 48, 31, 48, 84] | 1 | 575963136 | 48006336 |
| first_chunk/decoder.conv1 | CausalConv3d | [1, 48, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 10701766656 | 22601728 |
| first_chunk/decoder.middle.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.middle.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.middle.1.to_qkv | Conv2d | [1, 1024, 48, 84] | [1, 3072, 48, 84] | 1 | 25367150592 | 78655488 |
| first_chunk/decoder.spatial_attention | attention | [1, 1, 4032, 1024] | [1, 1, 4032, 1024] | 1 | 66588770304 | 196116480 |
| first_chunk/decoder.middle.1.proj | Conv2d | [1, 1024, 48, 84] | [1, 1024, 48, 84] | 1 | 8455716864 | 37228544 |
| first_chunk/decoder.middle.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.middle.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 146280448 |
| first_chunk/decoder.upsamples.0.upsamples.3.resample.1 | Conv2d | [1, 1024, 96, 168] | [1, 1024, 96, 168] | 1 | 304405807104 | 169873408 |
| first_chunk/decoder.upsamples.1.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 1, 96, 168] | [1, 1024, 1, 96, 168] | 1 | 913217421312 | 245370880 |
| first_chunk/decoder.upsamples.1.upsamples.3.resample.1 | Conv2d | [1, 1024, 192, 336] | [1, 1024, 192, 336] | 1 | 1217623228416 | 566235136 |
| first_chunk/decoder.upsamples.2.upsamples.0.shortcut | CausalConv3d | [1, 1024, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 67645734912 | 398460928 |
| first_chunk/decoder.upsamples.2.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 1826434842624 | 452986880 |
| first_chunk/decoder.upsamples.2.upsamples.0.residual.6 | CausalConv3d | [1, 512, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 913217421312 | 292554752 |
| first_chunk/decoder.upsamples.2.upsamples.1.residual.2 | CausalConv3d | [1, 512, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 913217421312 | 292554752 |
| first_chunk/decoder.upsamples.2.upsamples.1.residual.6 | CausalConv3d | [1, 512, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 913217421312 | 292554752 |
| first_chunk/decoder.upsamples.2.upsamples.2.residual.2 | CausalConv3d | [1, 512, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 913217421312 | 292554752 |
| first_chunk/decoder.upsamples.2.upsamples.2.residual.6 | CausalConv3d | [1, 512, 1, 192, 336] | [1, 512, 1, 192, 336] | 1 | 913217421312 | 292554752 |
| first_chunk/decoder.upsamples.2.upsamples.3.resample.1 | Conv2d | [1, 512, 384, 672] | [1, 512, 384, 672] | 1 | 1217623228416 | 1066403840 |
| first_chunk/decoder.upsamples.3.upsamples.0.shortcut | CausalConv3d | [1, 512, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 67645734912 | 793248768 |
| first_chunk/decoder.upsamples.3.upsamples.0.residual.2 | CausalConv3d | [1, 512, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 1826434842624 | 806880256 |
| first_chunk/decoder.upsamples.3.upsamples.0.residual.6 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 913217421312 | 535561216 |
| first_chunk/decoder.upsamples.3.upsamples.1.residual.2 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 913217421312 | 535561216 |
| first_chunk/decoder.upsamples.3.upsamples.1.residual.6 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 913217421312 | 535561216 |
| first_chunk/decoder.upsamples.3.upsamples.2.residual.2 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 913217421312 | 535561216 |
| first_chunk/decoder.upsamples.3.upsamples.2.residual.6 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 256, 1, 384, 672] | 1 | 913217421312 | 535561216 |
| first_chunk/decoder.head.2 | CausalConv3d | [1, 256, 1, 384, 672] | [1, 12, 1, 384, 672] | 1 | 42807066624 | 276959280 |
| second_chunk/decoder.conv1 | CausalConv3d | [1, 48, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 10701766656 | 23375872 |
| second_chunk/decoder.middle.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.middle.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.middle.1.to_qkv | Conv2d | [1, 1024, 48, 84] | [1, 3072, 48, 84] | 1 | 25367150592 | 78655488 |
| second_chunk/decoder.spatial_attention | attention | [1, 1, 4032, 1024] | [1, 1, 4032, 1024] | 1 | 66588770304 | 196116480 |
| second_chunk/decoder.middle.1.proj | Conv2d | [1, 1024, 48, 84] | [1, 1024, 48, 84] | 1 | 8455716864 | 37228544 |
| second_chunk/decoder.middle.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.middle.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 1 | 228304355328 | 162795520 |
| second_chunk/decoder.upsamples.0.upsamples.3.time_conv | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 2048, 1, 48, 84] | 1 | 50734301184 | 74719232 |
| second_chunk/decoder.upsamples.0.upsamples.3.resample.1 | Conv2d | [2, 1024, 96, 168] | [2, 1024, 96, 168] | 1 | 608811614208 | 301993984 |
| second_chunk/decoder.upsamples.1.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 1 | 1826434842624 | 443551744 |
| second_chunk/decoder.upsamples.1.upsamples.3.time_conv | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 2048, 2, 96, 168] | 1 | 405874409472 | 421535744 |
| second_chunk/decoder.upsamples.1.upsamples.3.resample.1 | Conv2d | [4, 1024, 192, 336] | [4, 1024, 192, 336] | 1 | 4870492913664 | 2151682048 |
| second_chunk/decoder.upsamples.2.upsamples.0.shortcut | CausalConv3d | [1, 1024, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 270582939648 | 1587546112 |
| second_chunk/decoder.upsamples.2.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 7305739370496 | 1906313216 |
| second_chunk/decoder.upsamples.2.upsamples.0.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 3652869685248 | 1217398784 |
| second_chunk/decoder.upsamples.2.upsamples.1.residual.2 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 3652869685248 | 1217398784 |
| second_chunk/decoder.upsamples.2.upsamples.1.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 3652869685248 | 1217398784 |
| second_chunk/decoder.upsamples.2.upsamples.2.residual.2 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 3652869685248 | 1217398784 |
| second_chunk/decoder.upsamples.2.upsamples.2.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 1 | 3652869685248 | 1217398784 |
| second_chunk/decoder.upsamples.2.upsamples.3.resample.1 | Conv2d | [4, 512, 384, 672] | [4, 512, 384, 672] | 1 | 4870492913664 | 4237297664 |
| second_chunk/decoder.upsamples.3.upsamples.0.shortcut | CausalConv3d | [1, 512, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 270582939648 | 3171419136 |
| second_chunk/decoder.upsamples.3.upsamples.0.residual.2 | CausalConv3d | [1, 512, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 7305739370496 | 3713532928 |
| second_chunk/decoder.upsamples.3.upsamples.0.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 3652869685248 | 2385249280 |
| second_chunk/decoder.upsamples.3.upsamples.1.residual.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 3652869685248 | 2385249280 |
| second_chunk/decoder.upsamples.3.upsamples.1.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 3652869685248 | 2385249280 |
| second_chunk/decoder.upsamples.3.upsamples.2.residual.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 3652869685248 | 2385249280 |
| second_chunk/decoder.upsamples.3.upsamples.2.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 1 | 3652869685248 | 2385249280 |
| second_chunk/decoder.head.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 12, 4, 384, 672] | 1 | 171228266496 | 1371082800 |
| steady_chunk/decoder.conv1 | CausalConv3d | [1, 48, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 310351233024 | 700350464 |
| steady_chunk/decoder.middle.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.middle.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.middle.1.to_qkv | Conv2d | [1, 1024, 48, 84] | [1, 3072, 48, 84] | 29 | 735647367168 | 2281009152 |
| steady_chunk/decoder.spatial_attention | attention | [1, 1, 4032, 1024] | [1, 1, 4032, 1024] | 29 | 1931074338816 | 5687377920 |
| steady_chunk/decoder.middle.1.proj | Conv2d | [1, 1024, 48, 84] | [1, 1024, 48, 84] | 29 | 245215789056 | 1079627776 |
| steady_chunk/decoder.middle.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.middle.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 1024, 1, 48, 84] | 29 | 6620826304512 | 5200007168 |
| steady_chunk/decoder.upsamples.0.upsamples.3.time_conv | CausalConv3d | [1, 1024, 1, 48, 84] | [1, 2048, 1, 48, 84] | 29 | 1471294734336 | 3124731904 |
| steady_chunk/decoder.upsamples.0.upsamples.3.resample.1 | Conv2d | [2, 1024, 96, 168] | [2, 1024, 96, 168] | 29 | 17655536812032 | 8757825536 |
| steady_chunk/decoder.upsamples.1.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.0.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.1.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.1.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.2.residual.2 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.2.residual.6 | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 1024, 2, 96, 168] | 29 | 52966610436096 | 14778748928 |
| steady_chunk/decoder.upsamples.1.upsamples.3.time_conv | CausalConv3d | [1, 1024, 2, 96, 168] | [1, 2048, 2, 96, 168] | 29 | 11770357874688 | 16056033280 |
| steady_chunk/decoder.upsamples.1.upsamples.3.resample.1 | Conv2d | [4, 1024, 192, 336] | [4, 1024, 192, 336] | 29 | 141244294496256 | 62398779392 |
| steady_chunk/decoder.upsamples.2.upsamples.0.shortcut | CausalConv3d | [1, 1024, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 7846905249792 | 46038837248 |
| steady_chunk/decoder.upsamples.2.upsamples.0.residual.2 | CausalConv3d | [1, 1024, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 211866441744384 | 62946076672 |
| steady_chunk/decoder.upsamples.2.upsamples.0.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 105933220872192 | 39136061440 |
| steady_chunk/decoder.upsamples.2.upsamples.1.residual.2 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 105933220872192 | 39136061440 |
| steady_chunk/decoder.upsamples.2.upsamples.1.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 105933220872192 | 39136061440 |
| steady_chunk/decoder.upsamples.2.upsamples.2.residual.2 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 105933220872192 | 39136061440 |
| steady_chunk/decoder.upsamples.2.upsamples.2.residual.6 | CausalConv3d | [1, 512, 4, 192, 336] | [1, 512, 4, 192, 336] | 29 | 105933220872192 | 39136061440 |
| steady_chunk/decoder.upsamples.2.upsamples.3.resample.1 | Conv2d | [4, 512, 384, 672] | [4, 512, 384, 672] | 29 | 141244294496256 | 122881632256 |
| steady_chunk/decoder.upsamples.3.upsamples.0.shortcut | CausalConv3d | [1, 512, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 7846905249792 | 91971154944 |
| steady_chunk/decoder.upsamples.3.upsamples.0.residual.2 | CausalConv3d | [1, 512, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 211866441744384 | 123018441728 |
| steady_chunk/decoder.upsamples.3.upsamples.0.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 105933220872192 | 76835222528 |
| steady_chunk/decoder.upsamples.3.upsamples.1.residual.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 105933220872192 | 76835222528 |
| steady_chunk/decoder.upsamples.3.upsamples.1.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 105933220872192 | 76835222528 |
| steady_chunk/decoder.upsamples.3.upsamples.2.residual.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 105933220872192 | 76835222528 |
| steady_chunk/decoder.upsamples.3.upsamples.2.residual.6 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 256, 4, 384, 672] | 29 | 105933220872192 | 76835222528 |
| steady_chunk/decoder.head.2 | CausalConv3d | [1, 256, 4, 384, 672] | [1, 12, 4, 384, 672] | 29 | 4965619728384 | 47424394608 |

Wan VAE非矩阵边界：`{"scalar_arithmetic_ops": 1059495623424, "comparisons": 1525894272, "exp_evaluations": 99751292928, "sqrt_evaluations": 272680128, "logical_read_bytes": 5301722832000, "logical_write_bytes": 4268390542080}`

| 算子 | 源码行 | calls | 算术 | 比较 | exp | sqrt | 逻辑读/写bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aten._safe_softmax.default | 267 | 31 | 1511778240 | 503842752 | 503967744 | 0 | 2015870976/2015870976 |
| aten._upsample_nearest_exact2d.default | 68 | 93 | 0 | 0 | 0 | 0 | 99949215744/99949215744 |
| aten.add.Tensor | 235 | 434 | 39632044032 | 0 | 0 | 0 | 317056352256/158528176128 |
| aten.add.Tensor | 277 | 31 | 127991808 | 0 | 0 | 0 | 1023934464/511967232 |
| aten.add.Tensor | 495 | 93 | 24987303936 | 0 | 0 | 0 | 199898431488/99949215744 |
| aten.add.Tensor | 58 | 930 | 99375316992 | 0 | 0 | 0 | 397501267968/397501267968 |
| aten.add.Tensor | 815 | 1 | 5999616 | 0 | 0 | 0 | 23998656/23998464 |
| aten.cat.default | 125 | 29 | 0 | 0 | 0 | 0 | 957874176/957874176 |
| aten.cat.default | 135 | 1 | 0 | 0 | 0 | 0 | 33030144/33030144 |
| aten.cat.default | 222 | 300 | 0 | 0 | 0 | 0 | 9909043200/9909043200 |
| aten.cat.default | 38 | 958 | 0 | 0 | 0 | 0 | 614974574592/614974574592 |
| aten.cat.default | 677 | 30 | 0 | 0 | 0 | 0 | 46448640/46448640 |
| aten.cat.default | 836 | 30 | 0 | 0 | 0 | 0 | 23410114560/23410114560 |
| aten.clamp_.default | 0 | 1 | 0 | 749371392 | 0 | 0 | 1498742784/1498742784 |
| aten.clamp_min.default | 58 | 930 | 0 | 272680128 | 0 | 0 | 1090720512/1090720512 |
| aten.clone.default | 121 | 60 | 0 | 0 | 0 | 0 | 4459069440/4459069440 |
| aten.clone.default | 219 | 868 | 0 | 0 | 0 | 0 | 198544195584/198544195584 |
| aten.clone.default | 264 | 31 | 0 | 0 | 0 | 0 | 1535901696/1535901696 |
| aten.clone.default | 307 | 1 | 0 | 0 | 0 | 0 | 1498742784/1498742784 |
| aten.clone.default | 391 | 93 | 0 | 0 | 0 | 0 | 100279517184/100279517184 |
| aten.clone.default | 402 | 93 | 0 | 0 | 0 | 0 | 100279517184/100279517184 |
| aten.clone.default | 490 | 124 | 0 | 0 | 0 | 0 | 100461182976/100461182976 |
| aten.clone.default | 675 | 31 | 0 | 0 | 0 | 0 | 23998464/23998464 |
| aten.clone.default | 708 | 31 | 0 | 0 | 0 | 0 | 16118710272/16118710272 |
| aten.constant_pad_nd.default | 40 | 1053 | 0 | 0 | 0 | 0 | 714667806720/734223033600 |
| aten.div.Tensor | 58 | 930 | 99375316992 | 0 | 0 | 0 | 795002535936/397501267968 |
| aten.div.Tensor | 815 | 1 | 5999616 | 0 | 0 | 0 | 23998656/23998464 |
| aten.linalg_vector_norm.default | 58 | 930 | 198477953856 | 0 | 0 | 272680128 | 397501267968/1090720512 |
| aten.mul.Scalar | 267 | 62 | 255983616 | 0 | 0 | 0 | 1023934464/1023934464 |
| aten.mul.Tensor | 58 | 1860 | 198750633984 | 0 | 0 | 0 | 795005392896/795002535936 |
| aten.silu.default | 234 | 868 | 365016121344 | 0 | 91254030336 | 0 | 365016121344/365016121344 |
| aten.silu.default | 722 | 31 | 31973179392 | 0 | 7993294848 | 0 | 31973179392/31973179392 |
| aten.stack.default | 149 | 60 | 0 | 0 | 0 | 0 | 8918138880/8918138880 |
| aten.zeros_like.default | 137 | 1 | 0 | 0 | 0 | 0 | 0/16515072 |

形状计数依据与限制：`{"method": "fixed eager program polynomial shape counts, not runtime fit", "basis_samples": 36, "held_out_executions": 3, "temporal_branches": ["T=1", "T>=2"], "spatial_domain": "integer latent H>=2 and W>=2", "degree_per_axis": 2, "torch_version": "2.14.0"}`；原件和捕获记录见JSON sources。逻辑bytes与矩阵接口可能交叠，不相加冒充唯一HBM流量。

Wan文本encoder：每个分支独立一次完整padding forward，之后才裁有效hidden；不随去噪步数重复。

| 分支 | padding行 | 有效行 | 矩阵FLOPs | 返回hidden bytes |
| --- | --- | --- | --- | --- |
| positive | 512 | 256 | 4844723109888 | 2097152 |
| negative | 512 | 128 | 4844723109888 | 1048576 |

| 每次encoder矩阵 | A | B | copies | 汇总FLOPs |
| --- | --- | --- | --- | --- |
| encoder.qkv | [512, 4096] | [4096, 4096] | 72 | 1236950581248 |
| encoder.out | [512, 4096] | [4096, 4096] | 24 | 412316860416 |
| encoder.ffn_gate_and_up | [512, 4096] | [4096, 10240] | 48 | 2061584302080 |
| encoder.ffn_down | [512, 10240] | [10240, 4096] | 24 | 1030792151040 |
| encoder.qk | [512, 64] | [64, 512] | 1536 | 51539607552 |
| encoder.pv | [512, 512] | [512, 64] | 1536 | 51539607552 |

阶段：base；执行次数=60

| 矩阵 | A | B | C | copies | 每evaluation汇总FLOPs | 逻辑bytes |
| --- | --- | --- | --- | ---: | ---: | ---: |
| self.qkv | [31248, 3072] | [3072, 3072] | [31248, 3072] | 90 | 53080762613760 | 36256481280 |
| self.out | [31248, 3072] | [3072, 3072] | [31248, 3072] | 30 | 17693587537920 | 12085493760 |
| self.ffn_up | [31248, 3072] | [3072, 14336] | [31248, 14336] | 30 | 82570075176960 | 35280322560 |
| self.ffn_down | [31248, 14336] | [14336, 3072] | [31248, 3072] | 30 | 82570075176960 | 35280322560 |
| self.qk | [31248, 128] | [128, 31248] | [31248, 31248] | 720 | 179976960737280 | 1417589268480 |
| self.pv | [31248, 31248] | [31248, 128] | [31248, 128] | 720 | 179976960737280 | 1417589268480 |
| cross.q | [31248, 3072] | [3072, 3072] | [31248, 3072] | 30 | 17693587537920 | 12085493760 |
| cross.kv | [512, 3072] | [3072, 3072] | [512, 3072] | 60 | 579820584960 | 1509949440 |
| cross.out | [31248, 3072] | [3072, 3072] | [31248, 3072] | 30 | 17693587537920 | 12085493760 |
| cross.qk | [31248, 128] | [128, 512] | [31248, 512] | 720 | 2948931256320 | 28892528640 |
| cross.pv | [31248, 512] | [512, 128] | [31248, 128] | 720 | 2948931256320 | 28892528640 |
| video_patch | [31248, 192] | [192, 3072] | [31248, 3072] | 1 | 36861640704 | 205166592 |
| text_input_1 | [512, 4096] | [4096, 3072] | [512, 3072] | 1 | 12884901888 | 32505856 |
| text_input_2 | [512, 3072] | [3072, 3072] | [512, 3072] | 1 | 9663676416 | 25165824 |
| video_output | [31248, 3072] | [3072, 192] | [31248, 192] | 1 | 36861640704 | 205166592 |

计量条件：

- 旧matrix_core字段仅含原列出矩阵。新增Wan UMT5编码器、输出VAE矩阵与H3 scheduled_conditioning独立计入对应扩展合计，避免重算旧core。仍不等于完整模型FLOPs或实测时间：Qwen3-VL编码器、H3 VAE、Wan输入图像encode与未明确列出的scalar/调度/通信另核。
- H3帧严格采用锁定公开实现的17n+5与5n+2分块规则，不套理想时间压缩4倍；立体声音频为2×round(frames/24×40)行。Wan为4n+1帧、(F−1)//4+1 latent，text固定padding512。
- 矩阵输入/输出形状和逻辑操作数读写可复算；逻辑bytes不是HBM流量，物化score只说明朴素驻留，不表示FlashAttention实际分配。H3输出两head对全部联合行计算后才选模态。
- 默认Wan按官方入口每步conditional/unconditional两次forward，H3默认一次；显式evaluations_per_step覆盖用于声明对照。NFE=steps×evaluations_per_step。参考token为外部已编码token数；没有自动解码/重采样参考媒体。
- H3第二阶段是声明的regeneration几何场景：新canvas、原有参考加base视频tokens；真实托管Context-IR、参考预处理、音频策略与实际Regenerate-2K步表未重现。两阶段预算分开后相加。
- AdaLN表为固定权重、唯一噪声值集合和三模态的假设预计算预算，未从steps猜unique值；每模型/权重/噪声计划变化须重算。它不等于当前锁定forward已实现缓存，也不算实际显存节约。
- BF16逻辑元素2B；H3公开实现video/audio输入与输出projection保持FP32故这些行按4B，其余core按2B。峰值选择需匹配各算子精度，未引用GPU宣传算力。

固定来源：

- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/textimage2video.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/textimage2video.py)，SHA256 `228f2fabf23014ed41ec6b8cd713d5be7371bb558501c71a62a0258b491a877b`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/configs/wan_ti2v_5B.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/configs/wan_ti2v_5B.py)，SHA256 `26d9e7b9c555eb0900b13751267a596556f869e7aee2d1572afc2a0a4a76f4c7`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/modules/model.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/modules/model.py)，SHA256 `8b39115298ca7322806c19b3165b3f435a94fe4a58f0624aec24f8e7f4997432`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/modules/vae2_2.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/modules/vae2_2.py)，SHA256 `eab5ce4aa1ce03af2978f2a8e8364c419f5fbb8535d265ac86b0b02ddcf0c1f6`。
- [research/generative-media-candidates/Wan-AI--Wan2.2-TI2V-5B/README.md](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/921dbaf3f1674a56f47e83fb80a34bac8a8f203e/README.md)，SHA256 `e357cb3ac077f8739755b0fb38fe8424c76534b19b4a84f6138856abb00abf69`。
- [research/generative-media-candidates/Wan-AI--Wan2.2-TI2V-5B/config.json](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/921dbaf3f1674a56f47e83fb80a34bac8a8f203e/config.json)，SHA256 `d1fea36899d00c2501b836c13ad65af56e2f9529ba622e50886d3f5c3e6c02bc`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/modules/t5.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/modules/t5.py)，SHA256 `8b0cebf3192c542f92a344255a06c203df3ba24160715899a055cc8de0cd930f`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/modules/tokenizers.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/modules/tokenizers.py)，SHA256 `cf5b189c1ae017326efadab2fc6380ba223fa7a59d0be6464bd264db53c76934`。
- [research/generative-video-analysis/Wan-Video--Wan2.2/wan/configs/shared_config.py](https://raw.githubusercontent.com/Wan-Video/Wan2.2/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/configs/shared_config.py)，SHA256 `3ae102e029d4d0e3436ebbaa9f8fd32c10e8468ae8be07facdca2e20ec1858fe`。
- [research/generative-video-analysis/capture_wan_vae_shapes.py](../research/generative-video-analysis/capture_wan_vae_shapes.py)，SHA256 `f165c05ab273a52c42cc82e331e8e946d1757fb249226f5d695abb64d9a57704`。
- [research/generative-video-analysis/wan-vae-decode-meta.json](../research/generative-video-analysis/capture_wan_vae_shapes.py)，SHA256 `011980764a845f94891a0ef18ebe041d8052a19c652ce44e95a64b4956396705`。
- [research/generative-video-analysis/wan-vae-decode-validation.json](../research/generative-video-analysis/capture_wan_vae_shapes.py)，SHA256 `0d547cc163ffa6c7c61f347831864c55a73b12f488f90a55c7c3db1d673f5592`。
