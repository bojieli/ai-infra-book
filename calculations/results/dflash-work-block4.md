# dflash-work — 

输入：`{"block_size": 4, "cached_context": 1020, "new_context": 4}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| checkpoint | `"z-lab/Qwen3-8B-DFlash-b16"` |
| revision | `"9b41424b7109f9c5413454f481b09a82b85333f4"` |
| checkpoint_tensors | 58 |
| draft_parameters | 1,048,626,432 |
| draft_weight_bytes | 2,097,252,864 |
| target_feature_layers | `[1, 9, 17, 25, 33]` |
| new_target_feature_bytes | 163,840 |
| fused_target_feature_bytes | 32,768 |
| noise_embedding_bytes | 32,768 |
| shared_head_weight_bytes | 1,244,659,712 |
| draft_candidates | 3 |
| draft_matrix_flops | 12,794,986,496 |
| target_verify_matrix_flops | 62,966,595,584 |
| draft_kv_bytes_per_context_token | 20,480 |
| draft_kv_peak_bytes | 21,053,440 |
| draft_kv_after_crop_bytes | 20,971,520 |
| draft_noise_kv_discarded_bytes | 81,920 |
| target_verify_peak_kv_bytes | 151,584,768 |

| 算子 | M | K | N | 实例数 | 矩阵FLOPs | 每实例BF16逻辑operand bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| target_feature_fusion | 4 | 20480 | 4096 | 1 | 671088640 | 167968768 |
| draft_q | 4 | 4096 | 4096 | 5 | 671088640 | 33619968 |
| context_and_noise_kv | 8 | 4096 | 1024 | 10 | 671088640 | 8470528 |
| draft_o | 4 | 4096 | 4096 | 5 | 671088640 | 33619968 |
| draft_gate_up | 4 | 4096 | 12288 | 10 | 4026531840 | 100794368 |
| draft_down | 4 | 12288 | 4096 | 5 | 2013265920 | 100794368 |
| noncausal_qk | 4 | 128 | 1028 | 160 | 168427520 | 272416 |
| noncausal_pv | 4 | 1028 | 128 | 160 | 168427520 | 272416 |
| shared_target_head | 3 | 4096 | 151936 | 1 | 3733979136 | 1245595904 |

计量条件：

- 官方z-lab检查点固定revision；下载配置、源码和58个权重张量的safetensors头，未下载权重载荷、未执行远程代码或GPU推理。所有shape、BF16 dtype及payload区间长度逐项核对。
- 计量batch=1的一次草稿前向：cached_context为已有草稿KV，新目标特征new_context行融合后只投影K/V；block_size行噪声含已知首token，输出头只作用于后block_size-1行。
- 采用auto_map指定dflash.py路径，目标特征层按config显式[1,9,17,25,33]；不要改用旁置modeling_dflash.py中的默认层选择。草稿块全连接注意力，配对为block_size*(cached_context+new_context+block_size)。
- embedding与lm_head复用目标权重，不属于独立草稿checkpoint参数；共享不消除head矩阵工作或权重读取。特征字节为逻辑接口载荷，同设备部署不自动等于网络流量。
- 矩阵表FMA=2，operand字节为每实例BF16矩阵边界尺寸；注意力分数实际dtype、融合、GQA复用、缓存和工作区另计，不将这些尺寸之和称为HBM实测。RMSNorm、RoPE、SiLU、softmax及采样的非矩阵工作未计入矩阵FLOPs。
- 草稿forward后crop丢弃整块噪声KV，仅留已确认目标context；下一轮重新读取目标特征。目标验证按同start历史、block_size行计算，两个KV池分列，不把单池峰值相加声称全执行驻留峰值。
- 块长2..16为形状扫描，不声称偏离训练块长16仍有相同接受率、质量或速度；未测草稿成本与完整采样行为。

固定来源：

- [sources/dflash-qwen3-8b/config.json](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/config.json)，SHA256 `9834d608c9ca53d5548b415471ae9e8ebc9aab6cedfc2a7af95b6bd097373102`。
- [sources/dflash-qwen3-8b/modeling_dflash.py](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/modeling_dflash.py)，SHA256 `d2b61a1fa5d469830c2285b552d75773274943fae5ac66dc2713beddea338528`。
- [sources/dflash-qwen3-8b/dflash.py](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/dflash.py)，SHA256 `17ab761ba665a41965b27bdc3a1c6795d1b07b285ec1f0789ad146f2ee9c1cc5`。
- [sources/dflash-qwen3-8b/utils.py](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/utils.py)，SHA256 `00b91431932c94b87443d9e2c0cf4d743846bd6c9666c9c736008df7bbd0faf1`。
- [sources/dflash-qwen3-8b/README.md](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/README.md)，SHA256 `5aae3cb1633e80fea3578f7330776320409313a6aeb6d922750d833fc89aa647`。
- [sources/dflash-qwen3-8b/model.safetensors.header.json](https://huggingface.co/z-lab/Qwen3-8B-DFlash-b16/resolve/9b41424b7109f9c5413454f481b09a82b85333f4/model.safetensors)，SHA256 `6724cbb4ec77638c24d878ce60aa4fbf0505f9ad3bc2b00110176767baf50856`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
