# vl-request — qwen3-vl-4b

输入：`{"dtype": "bf16", "images": [{"height": 320, "width": 512}, {"height": 320, "width": 512}], "kv_dtype": "bf16", "output_tokens": 128, "text_tokens": 400}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| visual_positions | 320 |
| non_image_prompt_positions | 400 |
| prompt_positions | 720 |
| requested_output_tokens | 128 |
| decode_forward_calls | 127 |
| prefill_causal_pairs | 259,560 |
| decode_causal_pairs | 99,568 |
| vision_matrix_flops | 927,444,500,480 |
| language_matrix_flops | 6,466,232,123,392 |
| total_matrix_flops | 7,393,676,623,872 |
| language_scalar_flops | 4,726,719,527 |
| vision_scalar_counts | `{"add": 1267566400, "multiply": 1421070720, "cos": 40960, "sin": 40960, "rsqrt": 63680, "negate": 31457280, "comparison": 314081280, "subtract": 314572800, "exp": 314572800, "divide": 314572800, "tanh": 125829120, "erf": 5242880}` |
| deepstack_language_layer_indices | `[0, 1, 2]` |
| deepstack_prefill_add_elements | 2,457,600 |
| language_parameters | 4,022,468,096 |
| language_weight_bytes | 8,044,936,192 |
| vision_weight_bytes | 830,695,424 |
| complete_encoder_bytes_per_request | 6,553,600 |
| kv_bytes_per_position | 147,456 |
| prefill_kv_bytes | 106,168,320 |
| final_kv_positions | 847 |
| final_kv_bytes | 124,895,232 |
| decode_kv_new_write_bytes | 18,726,912 |
| decode_kv_unique_payload_reads_bytes | 14,681,899,008 |
| output_head_evaluations | 128 |

| 图片 | 缓存命中 | grid THW | patch数 | 语言图像位置 | 本次编码矩阵FLOPs | 完整EC bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | False | [1, 20, 32] | 640 | 160 | 463722250240 | 3276800 |
| 1 | False | [1, 20, 32] | 640 | 160 | 463722250240 | 3276800 |

逐图视觉矩阵：本次工作已乘该图是否未命中；copies仍表示模型内部重复。

| 图片 | 算子 | A | B | copies | 本次矩阵FLOPs |
| --- | --- | --- | --- | --- | --- |
| 0 | patch_embedding | [640, 1536] | [1536, 1024] | 1 | 2013265920 |
| 0 | block.qkv | [640, 1024] | [1024, 3072] | 24 | 96636764160 |
| 0 | block.qk | [640, 64] | [64, 640] | 384 | 20132659200 |
| 0 | block.pv | [640, 640] | [640, 64] | 384 | 20132659200 |
| 0 | block.attention_output | [640, 1024] | [1024, 1024] | 24 | 32212254720 |
| 0 | block.mlp_up | [640, 1024] | [1024, 4096] | 24 | 128849018880 |
| 0 | block.mlp_down | [640, 4096] | [4096, 1024] | 24 | 128849018880 |
| 0 | merger_final.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 0 | merger_final.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 0 | merger_deepstack_5.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 0 | merger_deepstack_5.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 0 | merger_deepstack_11.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 0 | merger_deepstack_11.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 0 | merger_deepstack_17.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 0 | merger_deepstack_17.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 1 | patch_embedding | [640, 1536] | [1536, 1024] | 1 | 2013265920 |
| 1 | block.qkv | [640, 1024] | [1024, 3072] | 24 | 96636764160 |
| 1 | block.qk | [640, 64] | [64, 640] | 384 | 20132659200 |
| 1 | block.pv | [640, 640] | [640, 64] | 384 | 20132659200 |
| 1 | block.attention_output | [640, 1024] | [1024, 1024] | 24 | 32212254720 |
| 1 | block.mlp_up | [640, 1024] | [1024, 4096] | 24 | 128849018880 |
| 1 | block.mlp_down | [640, 4096] | [4096, 1024] | 24 | 128849018880 |
| 1 | merger_final.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 1 | merger_final.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 1 | merger_deepstack_5.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 1 | merger_deepstack_5.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 1 | merger_deepstack_11.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 1 | merger_deepstack_11.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |
| 1 | merger_deepstack_17.up | [160, 4096] | [4096, 4096] | 1 | 5368709120 |
| 1 | merger_deepstack_17.out | [160, 4096] | [4096, 2560] | 1 | 3355443200 |

| 请求阶段 | 执行次数 | 已汇总矩阵FLOPs |
| --- | ---: | ---: |
| vision_encode | 2 | 927444500480 |
| language_prefill | 1 | 5385847439360 |
| language_decode | 127 | 1080384684032 |

language_prefill：每行成本乘repeats；完整decode等差和见JSON。

| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |
| --- | ---: | --- | ---: | ---: | --- |
| embedding | 1 | {'indices': [1, 720], 'table': [151936, 2560], 'output': [720, 2560]} | 0 | 3686400 | 5760/3686400 |
| mrope_table | 1 | {'position_ids': [3, 1, 720], 'axis_frequencies': [3, 1, 720, 64], 'cos_sin_each': [1, 720, 128]} | 0 | 0 | 17536/368640 |
| input_layernorm | 36 | {'input': [720, 2560], 'weight': [2560], 'output': [720, 2560]} | 0 | 5120 | 3686400/3686400 |
| q_proj | 36 | {'input': [720, 2560], 'weight_math': [2560, 4096], 'weight_storage': [4096, 2560], 'output': [720, 4096]} | 15099494400 | 20971520 | 3686400/5898240 |
| k_proj | 36 | {'input': [720, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [720, 1024]} | 3774873600 | 5242880 | 3686400/1474560 |
| v_proj | 36 | {'input': [720, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [720, 1024]} | 3774873600 | 5242880 | 3686400/1474560 |
| q_norm | 36 | {'input': [23040, 128], 'weight': [128], 'output': [23040, 128]} | 0 | 256 | 5898240/5898240 |
| k_norm | 36 | {'input': [5760, 128], 'weight': [128], 'output': [5760, 128]} | 0 | 256 | 1474560/1474560 |
| apply_rope | 36 | {'Q': [1, 32, 720, 128], 'K': [1, 8, 720, 128]} | 0 | 0 | 7741440/7372800 |
| kv_append | 36 | {'new_K_and_V_each': [1, 8, 720, 128]} | 0 | 0 | 2949120/2949120 |
| qk | 36 | {'Q': [1, 32, 720, 128], 'K_shared': [1, 8, 720, 128], 'scores_rectangular': [1, 32, 720, 720]} | 2126315520 | 0 | 7372800/66355200 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 720, 720]} | 0 | 0 | 66355200/66355200 |
| pv | 36 | {'P': [1, 32, 720, 720], 'V_shared': [1, 8, 720, 128], 'output': [1, 32, 720, 128]} | 2126315520 | 0 | 67829760/5898240 |
| o_proj | 36 | {'input': [720, 4096], 'weight_math': [4096, 2560], 'weight_storage': [2560, 4096], 'output': [720, 2560]} | 15099494400 | 20971520 | 5898240/3686400 |
| attention_residual | 36 | {'inputs_each': [720, 2560], 'output': [720, 2560]} | 0 | 0 | 7372800/3686400 |
| post_attention_layernorm | 36 | {'input': [720, 2560], 'weight': [2560], 'output': [720, 2560]} | 0 | 5120 | 3686400/3686400 |
| gate_proj | 36 | {'input': [720, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [720, 9728]} | 35861299200 | 49807360 | 3686400/14008320 |
| up_proj | 36 | {'input': [720, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [720, 9728]} | 35861299200 | 49807360 | 3686400/14008320 |
| silu_mul | 36 | {'gate': [720, 9728], 'up': [720, 9728], 'output': [720, 9728]} | 0 | 0 | 28016640/14008320 |
| down_proj | 36 | {'input': [720, 9728], 'weight_math': [9728, 2560], 'weight_storage': [2560, 9728], 'output': [720, 2560]} | 35861299200 | 49807360 | 14008320/3686400 |
| ffn_residual | 36 | {'inputs_each': [720, 2560], 'output': [720, 2560]} | 0 | 0 | 7372800/3686400 |
| final_norm | 1 | {'input': [720, 2560], 'weight': [2560], 'output': [720, 2560]} | 0 | 5120 | 3686400/3686400 |
| lm_head | 1 | {'input': [1, 2560], 'weight_math': [2560, 151936], 'weight_storage': [151936, 2560], 'output': [1, 151936]} | 777912320 | 777912320 | 5120/303872 |
| image_embedding_replace | 1 | {'prompt': [720, 2560], 'image_embeddings': [320, 2560]} | 0 | 0 | 5325520/3686400 |
| deepstack_prompt_clone | 3 | {'prompt': [720, 2560]} | 0 | 0 | 3686400/3686400 |
| deepstack_visual_add | 3 | {'selected_hidden': [320, 2560], 'deepstack_features': [320, 2560]} | 0 | 0 | 3276800/1638400 |

language_decode_first：每行成本乘repeats；完整decode等差和见JSON。

| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |
| --- | ---: | --- | ---: | ---: | --- |
| embedding | 1 | {'indices': [1, 1], 'table': [151936, 2560], 'output': [1, 2560]} | 0 | 5120 | 8/5120 |
| mrope_table | 1 | {'position_ids': [3, 1, 1], 'axis_frequencies': [3, 1, 1, 64], 'cos_sin_each': [1, 1, 128]} | 0 | 0 | 280/512 |
| input_layernorm | 36 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| q_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 4096], 'weight_storage': [4096, 2560], 'output': [1, 4096]} | 20971520 | 20971520 | 5120/8192 |
| k_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [1, 1024]} | 5242880 | 5242880 | 5120/2048 |
| v_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [1, 1024]} | 5242880 | 5242880 | 5120/2048 |
| q_norm | 36 | {'input': [32, 128], 'weight': [128], 'output': [32, 128]} | 0 | 256 | 8192/8192 |
| k_norm | 36 | {'input': [8, 128], 'weight': [128], 'output': [8, 128]} | 0 | 256 | 2048/2048 |
| apply_rope | 36 | {'Q': [1, 32, 1, 128], 'K': [1, 8, 1, 128]} | 0 | 0 | 10752/10240 |
| kv_append | 36 | {'new_K_and_V_each': [1, 8, 1, 128]} | 0 | 0 | 4096/4096 |
| qk | 36 | {'Q': [1, 32, 1, 128], 'K_shared': [1, 8, 721, 128], 'scores_rectangular': [1, 32, 1, 721]} | 5906432 | 0 | 1484800/92288 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 1, 721]} | 0 | 0 | 92288/92288 |
| pv | 36 | {'P': [1, 32, 1, 721], 'V_shared': [1, 8, 721, 128], 'output': [1, 32, 1, 128]} | 5906432 | 0 | 1568896/8192 |
| o_proj | 36 | {'input': [1, 4096], 'weight_math': [4096, 2560], 'weight_storage': [2560, 4096], 'output': [1, 2560]} | 20971520 | 20971520 | 8192/5120 |
| attention_residual | 36 | {'inputs_each': [1, 2560], 'output': [1, 2560]} | 0 | 0 | 10240/5120 |
| post_attention_layernorm | 36 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| gate_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [1, 9728]} | 49807360 | 49807360 | 5120/19456 |
| up_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [1, 9728]} | 49807360 | 49807360 | 5120/19456 |
| silu_mul | 36 | {'gate': [1, 9728], 'up': [1, 9728], 'output': [1, 9728]} | 0 | 0 | 38912/19456 |
| down_proj | 36 | {'input': [1, 9728], 'weight_math': [9728, 2560], 'weight_storage': [2560, 9728], 'output': [1, 2560]} | 49807360 | 49807360 | 19456/5120 |
| ffn_residual | 36 | {'inputs_each': [1, 2560], 'output': [1, 2560]} | 0 | 0 | 10240/5120 |
| final_norm | 1 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| lm_head | 1 | {'input': [1, 2560], 'weight_math': [2560, 151936], 'weight_storage': [151936, 2560], 'output': [1, 151936]} | 777912320 | 777912320 | 5120/303872 |

language_decode_last：每行成本乘repeats；完整decode等差和见JSON。

| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |
| --- | ---: | --- | ---: | ---: | --- |
| embedding | 1 | {'indices': [1, 1], 'table': [151936, 2560], 'output': [1, 2560]} | 0 | 5120 | 8/5120 |
| mrope_table | 1 | {'position_ids': [3, 1, 1], 'axis_frequencies': [3, 1, 1, 64], 'cos_sin_each': [1, 1, 128]} | 0 | 0 | 280/512 |
| input_layernorm | 36 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| q_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 4096], 'weight_storage': [4096, 2560], 'output': [1, 4096]} | 20971520 | 20971520 | 5120/8192 |
| k_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [1, 1024]} | 5242880 | 5242880 | 5120/2048 |
| v_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [1, 1024]} | 5242880 | 5242880 | 5120/2048 |
| q_norm | 36 | {'input': [32, 128], 'weight': [128], 'output': [32, 128]} | 0 | 256 | 8192/8192 |
| k_norm | 36 | {'input': [8, 128], 'weight': [128], 'output': [8, 128]} | 0 | 256 | 2048/2048 |
| apply_rope | 36 | {'Q': [1, 32, 1, 128], 'K': [1, 8, 1, 128]} | 0 | 0 | 10752/10240 |
| kv_append | 36 | {'new_K_and_V_each': [1, 8, 1, 128]} | 0 | 0 | 4096/4096 |
| qk | 36 | {'Q': [1, 32, 1, 128], 'K_shared': [1, 8, 847, 128], 'scores_rectangular': [1, 32, 1, 847]} | 6938624 | 0 | 1742848/108416 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 1, 847]} | 0 | 0 | 108416/108416 |
| pv | 36 | {'P': [1, 32, 1, 847], 'V_shared': [1, 8, 847, 128], 'output': [1, 32, 1, 128]} | 6938624 | 0 | 1843072/8192 |
| o_proj | 36 | {'input': [1, 4096], 'weight_math': [4096, 2560], 'weight_storage': [2560, 4096], 'output': [1, 2560]} | 20971520 | 20971520 | 8192/5120 |
| attention_residual | 36 | {'inputs_each': [1, 2560], 'output': [1, 2560]} | 0 | 0 | 10240/5120 |
| post_attention_layernorm | 36 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| gate_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [1, 9728]} | 49807360 | 49807360 | 5120/19456 |
| up_proj | 36 | {'input': [1, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [1, 9728]} | 49807360 | 49807360 | 5120/19456 |
| silu_mul | 36 | {'gate': [1, 9728], 'up': [1, 9728], 'output': [1, 9728]} | 0 | 0 | 38912/19456 |
| down_proj | 36 | {'input': [1, 9728], 'weight_math': [9728, 2560], 'weight_storage': [2560, 9728], 'output': [1, 2560]} | 49807360 | 49807360 | 19456/5120 |
| ffn_residual | 36 | {'inputs_each': [1, 2560], 'output': [1, 2560]} | 0 | 0 | 10240/5120 |
| final_norm | 1 | {'input': [1, 2560], 'weight': [2560], 'output': [1, 2560]} | 0 | 5120 | 5120/5120 |
| lm_head | 1 | {'input': [1, 2560], 'weight_math': [2560, 151936], 'weight_storage': [151936, 2560], 'output': [1, 151936]} | 777912320 | 777912320 | 5120/303872 |

计量条件：

- 这是图像VL/ComputerUse请求的阶段账；图像来自预处理后静态尺寸，text_tokens包含真实模板、图像边界、工具说明和其他非图像位置，未执行tokenizer或屏幕截图/动作闭环。不是所有Omni音视频模型的通用执行器。
- vision_encoding复用完整视觉矩阵/scalar账且只计miss图；命中EC仍含final/DeepStack并被语言模型处理，不减少prompt位置、语言attention或KV。无语言prefix-cache命中。
- 视觉每图非因果P²与语言整个prompt因果S(S+1)/2分开。产生图像embedding不等于语言已处理其位置；语言QKV/MLP/attention覆盖图像与文字全部位置，不能再加一次独立图像语言prefill。
- DeepStack来自视觉层5/11/17，在语言0/1/2层之后相加；prefill三次clone和视觉行add单列，后续decode没有图像encoder或DeepStack执行。
- G个输出token由prefill最后一行logits产生第一个，再运行G−1次单token decode；最后输出token尚未写入KV，最终KV长度为S+G−1。EOS提前结束、采样与logit后处理未计。
- 语言有效因果矩阵工作与矩形分数物化预算分列，算子语义读写不是HBM实测。decode逐步历史增长用整数等差求和，未用平均长度近似代替。
- 语言KV保留完整层、GQA共享K/V，不重复乘query heads；kv_dtype只控制元素字节，未计页碎片、量化metadata、TP复制或分配器。权重容量分视觉/语言，不假设两阶段同时常驻同卡。
- 没有CPU图片解码/resize、网络、排队、特征传输/缓存读取计时、kernel launch或设备预测；矩阵和scalar工作不能直接推成完整请求延迟。M-RoPE位置值与布局构造由外部实际输入确定，当前只计确定形状的表计算。

固定来源：

- [configs/models/qwen3-vl-4b/config.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json)，SHA256 `edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/multimodal-cache/qwen3-vl4-preprocessor.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)，SHA256 `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [sources/multimodal-cache/vllm-qwen3-vl.py](https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/model_executor/models/qwen3_vl.py)，SHA256 `f5f45b9002b4a2cda4e0058da02e271841c6d2e619768d26140d144d85c4ef97`。
- [research/vision-encoding/modeling_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py)，SHA256 `b5aa46046548f75c4e7f77e7ccc6717a1a627bead388118844898cfbc94c8bc1`。
- [research/vision-encoding/vision_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py)，SHA256 `bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356`。
- [research/vision-encoding/configuration_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/configuration_qwen3_vl.py)，SHA256 `200b5e015b9e4b6e425122ac0359e3c6281e4a7638a00d8ebfbe853d61dc1bc7`。
