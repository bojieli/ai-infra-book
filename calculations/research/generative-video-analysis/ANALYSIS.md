# 视频算子预算：固定实现审计与短例

2026-09-09。实现已落盘于`src/infra_calc/topics/video_generation.py`，独立锁`configs/video-generation.lock.json`，3项测试通过。此处只覆盖显式列出的矩阵core，未声称完整生成pipeline可运行或端到端实测。

## 不能只按VAE压缩倍率推时间长度

H3使用[MiniMax与Hugging Face共同署名的公开实现](https://github.com/huggingface/diffusers/blob/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/modular_pipelines/minimax_h3/modular_pipeline.py)：

- `align_num_frames`向上调整至17n+5帧；`video_latent_num_frames`为5n+2。
- 请求120帧实际对齐124帧，得到37 latent frames。不是31，也不是ceil(120/4)。`vae_frames_per_chunk=17`来自clip_length，`vae_latents_per_chunk=5`来自tokens_chunk_size。
- 每声道音频长度为`round(resolved_frames / 24 × 40)`，两声道独立排成序列。因此124帧有414 audio tokens，不把32 audio latent channels当32声道。
- 空间VAE16倍，patch1×2×2再减2倍；画布严格要求32整除，本计算不伪装官方自动宽高比解析。768×1344共有37×24×42=37296 visual tokens。

Wan的[官方生成器](https://github.com/Wan-Video/Wan2.2/blob/42bf4cfaa384bc21833865abc2f9e6c0e67233dc/wan/textimage2video.py)则使用(F−1)//4+1；本计算要求4n+1，121帧得31 latent frames。该版本text context填充到512，因此不接受任意短text_tokens伪装实际cross-attention矩阵长度。

## H3 core矩阵

[Transformer实现](https://github.com/huggingface/diffusers/blob/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/transformers/transformer_minimax_h3.py)与固定HF配置一致：hidden5376、attention宽56×128=7168、FFN14336、50 joint blocks、2 text refiner blocks。每个block的三个QKV投影为[5376,7168]，输出为[7168,5376]，SwiGLU含两份up/gate和一份down。联合序列S上，单block矩阵work为8S×5376×7168 + 6S×5376×14336 + 4S²×7168。

更容易遗漏的是两个输出head：公开forward先对**所有joint行**分别做video和audio投影，再用index_select取各模态行；不能只按visual rows算video head、按audio rows算audio head。文本refiner在每次forward里执行，不能自动当跨去噪步缓存。公开实现输入video/audio与输出projection保持FP32，相关逻辑bytes用4，其他core使用BF16字节预算。

短例：120请求帧、768×1344、256文本tokens、无额外参考，得到总序列37966；单次所列core矩阵为3,529,945,164,218,368 FLOPs。30步×每步1 evaluation为105,898,354,926,551,040 FLOPs。这里步数和CFG/evaluation次数是输入，不代表官方默认完整服务。

## AdaLN不能混入“约20B执行模型”宣传

50个block的modulation Linear是[2688,18×5376]，含bias的参数总数为13,010,457,600；BF16权重为26,020,915,200 bytes。固定权重与噪声集合，声明U个唯一timestep，则输出表为U×50×18×5376×2 bytes；U=30为290,304,000 bytes，矩阵预计算为780,337,152,000 FLOPs。

这是独立的假设缓存预算。当前锁定forward仍逐次计算该projection；没有实现离线缓存，也没有证明整个噪声计划只有30个不同值。视频、音频与参考可能有不同噪声级，必须由真实scheduler生成集合后替换U。缓存表不包括最终norm_out、time embedder或其他状态；修改权重/LoRA/噪声表均需失效重算。core总FLOPs特意排除time/AdaLN，避免把假设缓存当实有执行。

## 两阶段与Wan对照

可选regeneration场景单列新分辨率和步数，将base visual tokens加入第二阶段参考长度，返回两份预算再相加。这只是声明几何：托管Context-IR、真实regeneration参考预处理/resize、声音策略和实际步表均未复现。因此结果叫`declared_regeneration`。

Wan5B保持独立video self-attention与text cross-attention，GELU FFN只有两层Linear，不能套H3 SwiGLU的三份矩阵。121帧、768×1344、512文本tokens时visual tokens为31248，单次core矩阵为637,829,552,013,312 FLOPs。对照只解释结构和长度，不据此推断两模型同质量速度。

朴素score元素大小只作为无融合实现的驻留对照；逻辑操作数bytes不是HBM观测。不含VAE编解码、文本编码器、完整模型所有层参数/工作、非矩阵、bias操作、调度器、通信和实际显存峰值。
