# video-generation — minimax-h3

输入：`{"evaluations_per_step": 1, "frames": 120, "height": 768, "model": "minimax-h3", "negative_text_tokens": 128, "positive_text_tokens": 256, "reference_audio_tokens": 0, "reference_video_tokens": 0, "regeneration_height": null, "regeneration_steps": 15, "regeneration_width": null, "steps": 30, "text_tokens": 256, "unique_timestep_values": 30, "width": 1344}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| requested_frames | 120 |
| resolved_frames | 124 |
| latent_frames | 37 |
| hidden_size | 5,376 |
| attention_inner_dim | 7,168 |
| layers | 50 |
| matrix_core_flops | 105,898,354,926,551,040 |
| stages | 1 |
| block_modulation_cache | `{"block_modulation_weight_parameters": 13010457600, "block_modulation_weight_bf16_bytes": 26020915200, "declared_unique_timestep_values": 30, "cache_table_bf16_bytes": 290304000, "one_cache_precompute_matrix_flops": 780337152000, "status": "hypothetical explicit cache; pinned forward recomputes these projections"}` |
| matrix_core_plus_text_and_vae_flops | `null` |
| matrix_core_plus_text_encoder_flops | `null` |
| matrix_core_plus_conditioning_flops | 105,899,894,867,558,400 |

阶段：base；执行次数=30

| 矩阵 | A | B | C | copies | 每evaluation汇总FLOPs | 逻辑bytes |
| --- | --- | --- | --- | ---: | ---: | ---: |

实际调度条件化（完整逐步矩阵及缓存账见同名JSON）：`{"status": "accounted", "scheduler_grid_points": 31, "forward_evaluations": 30, "schedule_capture_torch_version": "2.14.0", "executed_conditioning_matrix_flops": 1539941007360, "executed_scalar_counts": {"ordinary_arithmetic": 5554129756212, "exp": 8405376, "negate": 8405376, "rsqrt": 115036980, "sinusoid_multiply": 18944, "sinusoid_divide": 3840, "sinusoid_exp": 3840, "sinusoid_log": 30, "sin": 7552, "cos": 7552}, "actual_unique_timestep_values": [0.0, 0.0028653740882873535, 0.0059171319007873535, 0.009174346923828125, 0.011363685131072998, 0.012658298015594482, 0.01639336347579956, 0.020408153533935547, 0.023255884647369385, 0.02473503351211548, 0.029411733150482178, 0.03448277711868286, 0.03571432828903198, 0.04000002145767212, 0.046025097370147705, 0.04878050088882446, 0.05263155698776245, 0.05990779399871826, 0.062499940395355225, 0.06796115636825562, 0.07692301273345947, 0.07692307233810425, 0.08695650100708008, 0.09210526943206787, 0.0982658863067627, 0.10810810327529907, 0.11111116409301758, 0.12500005960464478, 0.12582778930664062, 0.14285719394683838, 0.16176468133926392, 0.1627907156944275, 0.1818181276321411, 0.18644064664840698, 0.20312494039535522, 0.2149532437324524, 0.22580647468566895, 0.25, 0.2500000596046448, 0.27586203813552856, 0.29411768913269043, 0.3035714626312256, 0.3333333134651184, 0.3513513207435608, 0.365384578704834, 0.40000003576278687, 0.4285714626312256, 0.4375, 0.4782608151435852, 0.5227272510528564, 0.5384615063667297, 0.5714285969734192, 0.625, 0.684210479259491, 0.707317054271698, 0.75, 0.8235293626785278, 0.90625], "hypothetical_cache": {"unique_timestep_count": 58, "table_bytes": 562501632, "precompute_matrix_flops": 1513840312320, "precompute_silu_elements": 8262912, "precompute_sinusoid_counts": {"multiply": 14976, "divide": 128, "exp": 128, "log": 1, "sin": 7424, "cos": 7424}, "precompute_bias_adds": 281718528, "matrix_work_saved_after_precompute": 26100695040, "table_write_bytes": 562501632, "table_reads_per_forward_sum_bytes": 572199936, "row_modulation_reads_sum_bytes": 3698386513920, "note": "Hypothetical persistent modulation cache: precompute and table IO are charged; per-token RMSNorm/modulation/gates remain. Pinned forward does not implement this cache."}, "assumptions": ["steps仍指旧core字段声明的forward次数；实际scheduler传入steps+1网格点，终点zero不forward。CPU float32原方法执行结果已封存；1..128范围外明确unavailable，不伪装理论数列等于真实舍入。", "每step distinct值严格由video/audio与存在的参考噪声集合构成：visual max(t,0.999)、audio1.0，再按FP32归并；文本沿video timestep。", "本项覆盖时间MLP、每block与final AdaLN投影、SiLU/bias、关联RMSNorm及逐token调制/gated残差。其他attention/FFN内部scalar、VAE和文本编码器不因本项自动完成。", "缓存单独收费整个unique集合的时间MLP和modulation投影、表写读；不会消除按token的norm/scale/shift/gate，也不代表当前代码已有缓存。跨stage缓存复用未假定。"]}`

| step | video time | audio time | distinct times | 每evaluation条件化矩阵FLOPs |
| --- | --- | --- | --- | --- |
| 0 | 0.0 | 0.0 | 1 | 26100695040 |
| 1 | 0.0028653740882873535 | 0.011363685131072998 | 2 | 52201390080 |
| 2 | 0.0059171319007873535 | 0.023255884647369385 | 2 | 52201390080 |
| 3 | 0.009174346923828125 | 0.03571432828903198 | 2 | 52201390080 |
| 4 | 0.012658298015594482 | 0.04878050088882446 | 2 | 52201390080 |
| 5 | 0.01639336347579956 | 0.062499940395355225 | 2 | 52201390080 |
| 6 | 0.020408153533935547 | 0.07692301273345947 | 2 | 52201390080 |
| 7 | 0.02473503351211548 | 0.09210526943206787 | 2 | 52201390080 |
| 8 | 0.029411733150482178 | 0.10810810327529907 | 2 | 52201390080 |
| 9 | 0.03448277711868286 | 0.12500005960464478 | 2 | 52201390080 |
| 10 | 0.04000002145767212 | 0.14285719394683838 | 2 | 52201390080 |
| 11 | 0.046025097370147705 | 0.16176468133926392 | 2 | 52201390080 |
| 12 | 0.05263155698776245 | 0.1818181276321411 | 2 | 52201390080 |
| 13 | 0.05990779399871826 | 0.20312494039535522 | 2 | 52201390080 |
| 14 | 0.06796115636825562 | 0.22580647468566895 | 2 | 52201390080 |
| 15 | 0.07692307233810425 | 0.25 | 2 | 52201390080 |
| 16 | 0.08695650100708008 | 0.27586203813552856 | 2 | 52201390080 |
| 17 | 0.0982658863067627 | 0.3035714626312256 | 2 | 52201390080 |
| 18 | 0.11111116409301758 | 0.3333333134651184 | 2 | 52201390080 |
| 19 | 0.12582778930664062 | 0.365384578704834 | 2 | 52201390080 |
| 20 | 0.14285719394683838 | 0.40000003576278687 | 2 | 52201390080 |
| 21 | 0.1627907156944275 | 0.4375 | 2 | 52201390080 |
| 22 | 0.18644064664840698 | 0.4782608151435852 | 2 | 52201390080 |
| 23 | 0.2149532437324524 | 0.5227272510528564 | 2 | 52201390080 |
| 24 | 0.2500000596046448 | 0.5714285969734192 | 2 | 52201390080 |
| 25 | 0.29411768913269043 | 0.625 | 2 | 52201390080 |
| 26 | 0.3513513207435608 | 0.684210479259491 | 2 | 52201390080 |
| 27 | 0.4285714626312256 | 0.75 | 2 | 52201390080 |
| 28 | 0.5384615063667297 | 0.8235293626785278 | 2 | 52201390080 |
| 29 | 0.707317054271698 | 0.90625 | 2 | 52201390080 |
| joint.qkv | [37966, 5376] | [5376, 7168] | [37966, 7168] | 150 | 438907856486400 | 154434201600 |
| joint.out | [37966, 7168] | [7168, 5376] | [37966, 5376] | 50 | 146302618828800 | 51478067200 |
| joint.ffn_up | [37966, 5376] | [5376, 14336] | [37966, 14336] | 100 | 585210475315200 | 165091225600 |
| joint.ffn_down | [37966, 14336] | [14336, 5376] | [37966, 5376] | 50 | 292605237657600 | 82545612800 |
| joint.qk | [37966, 128] | [128, 37966] | [37966, 37966] | 2800 | 1033207817420800 | 8126364131200 |
| joint.pv | [37966, 37966] | [37966, 128] | [37966, 128] | 2800 | 1033207817420800 | 8126364131200 |
| text_refiner.qkv | [256, 5376] | [5376, 7168] | [256, 7168] | 6 | 118380036096 | 500957184 |
| text_refiner.out | [256, 7168] | [7168, 5376] | [256, 5376] | 2 | 39460012032 | 166985728 |
| text_refiner.ffn_up | [256, 5376] | [5376, 14336] | [256, 14336] | 4 | 157840048128 | 656932864 |
| text_refiner.ffn_down | [256, 14336] | [14336, 5376] | [256, 5376] | 2 | 78920024064 | 328466432 |
| text_refiner.qk | [256, 128] | [128, 256] | [256, 256] | 112 | 1879048192 | 29360128 |
| text_refiner.pv | [256, 256] | [256, 128] | [256, 128] | 112 | 1879048192 | 29360128 |
| video_input | [37296, 96] | [96, 5376] | [37296, 5376] | 1 | 38496632832 | 818399232 |
| audio_input | [414, 32] | [32, 5376] | [414, 5376] | 1 | 142442496 | 9643776 |
| text_input | [256, 5120] | [5120, 5376] | [256, 5376] | 1 | 14092861440 | 60424192 |
| video_output_all_rows | [37966, 5376] | [5376, 96] | [37966, 96] | 1 | 39188201472 | 833064192 |
| audio_output_all_rows | [37966, 5376] | [5376, 32] | [37966, 32] | 1 | 13062733824 | 821968640 |

计量条件：

- 旧matrix_core字段仅含原列出矩阵。新增Wan UMT5编码器、输出VAE矩阵与H3 scheduled_conditioning独立计入对应扩展合计，避免重算旧core。仍不等于完整模型FLOPs或实测时间：Qwen3-VL编码器、H3 VAE、Wan输入图像encode与未明确列出的scalar/调度/通信另核。
- H3帧严格采用锁定公开实现的17n+5与5n+2分块规则，不套理想时间压缩4倍；立体声音频为2×round(frames/24×40)行。Wan为4n+1帧、(F−1)//4+1 latent，text固定padding512。
- 矩阵输入/输出形状和逻辑操作数读写可复算；逻辑bytes不是HBM流量，物化score只说明朴素驻留，不表示FlashAttention实际分配。H3输出两head对全部联合行计算后才选模态。
- 默认Wan按官方入口每步conditional/unconditional两次forward，H3默认一次；显式evaluations_per_step覆盖用于声明对照。NFE=steps×evaluations_per_step。参考token为外部已编码token数；没有自动解码/重采样参考媒体。
- H3第二阶段是声明的regeneration几何场景：新canvas、原有参考加base视频tokens；真实托管Context-IR、参考预处理、音频策略与实际Regenerate-2K步表未重现。两阶段预算分开后相加。
- AdaLN表为固定权重、唯一噪声值集合和三模态的假设预计算预算，未从steps猜unique值；每模型/权重/噪声计划变化须重算。它不等于当前锁定forward已实现缓存，也不算实际显存节约。
- BF16逻辑元素2B；H3公开实现video/audio输入与输出projection保持FP32故这些行按4B，其余core按2B。峰值选择需匹配各算子精度，未引用GPU宣传算力。

固定来源：

- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/models/transformers/transformer_minimax_h3.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/transformers/transformer_minimax_h3.py)，SHA256 `1926b1bc15a5bebda05e3dc8cde1b3955d56641ba7f8f9d6e90c8f78c66ae30c`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/before_denoise.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/before_denoise.py)，SHA256 `530b007c1d689c3ee1fc1690527f5253522d2da6b44dd326bec99faaf9f72fff`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/before_encoder.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/before_encoder.py)，SHA256 `03612baa8b983d058884d2c1740e57342279a1124002553f78cec98abcfc7c28`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/denoise.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/denoise.py)，SHA256 `bf0224f3ac8f3bba8366599143f60d78bd14e9faf77cdb207a844549bb8c1dc4`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/encoders.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/encoders.py)，SHA256 `fea751a889752ba58f1528acbc23b223e827ea707a75e2ae0c43d4a53ce758af`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/references.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/references.py)，SHA256 `9d20d0031ca1bc98b4556c73845601f3f69f995d702a954c160265303da160cb`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/models/autoencoders/autoencoder_kl_minimax_h3.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/autoencoder_kl_minimax_h3.py)，SHA256 `4c3c9745ee27d16ff343c4998244bad41cd8f4213f0029cf7ce11ebb6d72ca1b`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/modular_pipelines/minimax_h3/modular_pipeline.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/modular_pipeline.py)，SHA256 `9d5284ac8390f97d3e5eb3e0a50eddf25e04e7a12ff7fe063409b3cbd333b0ff`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/models/attention.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/attention.py)，SHA256 `3c61df6cc4832149eb654c1e82220f4a6b91daca13741c957c4e0faff7810adf`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/models/activations.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/activations.py)，SHA256 `ab1767e8e44e7d4bf1cb18299ba33654329e2711fa983b1423fc4fe12de2c3ab`。
- [research/generative-media-candidates/MiniMaxAI--MiniMax-H3/README.md](https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/42ed227ee7df40d41602854ae760620d6eb651fe/README.md)，SHA256 `f0116a90332496bdfcc827320c603a26b849c73bf804f2674d03682fbbd2334a`。
- [research/generative-media-candidates/MiniMaxAI--MiniMax-H3/transformer/config.json](https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/42ed227ee7df40d41602854ae760620d6eb651fe/transformer/config.json)，SHA256 `74c11bff524336576096993cbfcdcdc2ef4fa2fa4409df693bdcbc6c666282ae`。
- [research/generative-media-candidates/MiniMaxAI--MiniMax-H3/vae/config.json](https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/42ed227ee7df40d41602854ae760620d6eb651fe/vae/config.json)，SHA256 `78f67deec3d63aae807f2bfe7154bc1e26f6372cb20b63265fcbae1b62bb5745`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/schedulers/scheduling_minimax_h3.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/schedulers/scheduling_minimax_h3.py)，SHA256 `307d5bf755337ef00c47237f9ac8be116e627d26e1df3b5f0bd504a80f9de8dd`。
- [research/generative-media-candidates/MiniMaxAI--MiniMax-H3/scheduler/scheduler_config.json](https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/42ed227ee7df40d41602854ae760620d6eb651fe/scheduler/scheduler_config.json)，SHA256 `8fa6c3aa70dc9e691e1a6df899fd1b6f75f70481a27cee6e18a303817075c304`。
- [research/generative-media-candidates/MiniMaxAI--MiniMax-H3/audio_scheduler/scheduler_config.json](https://huggingface.co/MiniMaxAI/MiniMax-H3/resolve/42ed227ee7df40d41602854ae760620d6eb651fe/audio_scheduler/scheduler_config.json)，SHA256 `804780f7133477067bd6bbfbc02dc8b3cf9feeb400f97c08f5b1d5f6cbab3840`。
- [research/generative-video-analysis/capture_h3_schedules.py](../research/generative-video-analysis/capture_h3_schedules.py)，SHA256 `65175bc7668b81e7a633e316d8ab96243414ab9a49d7136df78bd1255d67596e`。
- [research/generative-video-analysis/h3-schedules-fp32.json](../research/generative-video-analysis/capture_h3_schedules.py)，SHA256 `8bcc0f0264addd1d7abfe0a3ce5652013860be9dcbe07f2dc9dcf35ba591f645`。
- [research/generative-video-analysis/huggingface--diffusers/src/diffusers/models/embeddings.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/embeddings.py)，SHA256 `4eb810f715786eb1f24f2a4641e529817f7c951b9caf2f7925811329a03ec796`。
