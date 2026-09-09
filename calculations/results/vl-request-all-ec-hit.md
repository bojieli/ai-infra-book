# vl-request — qwen3-vl-4b

输入：`{"dtype": "bf16", "encoder_cache_hits": 4, "images": null, "images_per_request": 4, "kv_dtype": "bf16", "output_tokens": 128, "preprocessed_height": 640, "preprocessed_width": 640, "text_tokens": 400}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| visual_positions | 1,600 |
| non_image_prompt_positions | 400 |
| prompt_positions | 2,000 |
| requested_output_tokens | 128 |
| decode_forward_calls | 127 |
| prefill_causal_pairs | 2,001,000 |
| decode_causal_pairs | 262,128 |
| vision_matrix_flops | 0 |
| language_matrix_flops | 16,890,545,569,792 |
| total_matrix_flops | 16,890,545,569,792 |
| language_scalar_flops | 18,148,708,647 |
| vision_scalar_counts | `{"add": 0, "multiply": 0, "cos": 0, "sin": 0, "rsqrt": 0, "negate": 0, "comparison": 0, "subtract": 0, "exp": 0, "divide": 0, "tanh": 0, "erf": 0}` |
| deepstack_language_layer_indices | `[0, 1, 2]` |
| deepstack_prefill_add_elements | 12,288,000 |
| language_parameters | 4,022,468,096 |
| language_weight_bytes | 8,044,936,192 |
| vision_weight_bytes | 830,695,424 |
| complete_encoder_bytes_per_request | 32,768,000 |
| kv_bytes_per_position | 147,456 |
| prefill_kv_bytes | 294,912,000 |
| final_kv_positions | 2,127 |
| final_kv_bytes | 313,638,912 |
| decode_kv_new_write_bytes | 18,726,912 |
| decode_kv_unique_payload_reads_bytes | 38,652,346,368 |
| output_head_evaluations | 128 |

| 请求阶段 | 执行次数 | 已汇总矩阵FLOPs |
| --- | ---: | ---: |
| vision_encode | 0 | 0 |
| language_prefill | 1 | 15714279096320 |
| language_decode | 127 | 1176266473472 |

language_prefill：每行成本乘repeats；完整decode等差和见JSON。

| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |
| --- | ---: | --- | ---: | ---: | --- |
| embedding | 1 | {'indices': [1, 2000], 'table': [151936, 2560], 'output': [2000, 2560]} | 0 | 10240000 | 16000/10240000 |
| mrope_table | 1 | {'position_ids': [3, 1, 2000], 'axis_frequencies': [3, 1, 2000, 64], 'cos_sin_each': [1, 2000, 128]} | 0 | 0 | 48256/1024000 |
| input_layernorm | 36 | {'input': [2000, 2560], 'weight': [2560], 'output': [2000, 2560]} | 0 | 5120 | 10240000/10240000 |
| q_proj | 36 | {'input': [2000, 2560], 'weight_math': [2560, 4096], 'weight_storage': [4096, 2560], 'output': [2000, 4096]} | 41943040000 | 20971520 | 10240000/16384000 |
| k_proj | 36 | {'input': [2000, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [2000, 1024]} | 10485760000 | 5242880 | 10240000/4096000 |
| v_proj | 36 | {'input': [2000, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [2000, 1024]} | 10485760000 | 5242880 | 10240000/4096000 |
| q_norm | 36 | {'input': [64000, 128], 'weight': [128], 'output': [64000, 128]} | 0 | 256 | 16384000/16384000 |
| k_norm | 36 | {'input': [16000, 128], 'weight': [128], 'output': [16000, 128]} | 0 | 256 | 4096000/4096000 |
| apply_rope | 36 | {'Q': [1, 32, 2000, 128], 'K': [1, 8, 2000, 128]} | 0 | 0 | 21504000/20480000 |
| kv_append | 36 | {'new_K_and_V_each': [1, 8, 2000, 128]} | 0 | 0 | 8192000/8192000 |
| qk | 36 | {'Q': [1, 32, 2000, 128], 'K_shared': [1, 8, 2000, 128], 'scores_rectangular': [1, 32, 2000, 2000]} | 16392192000 | 0 | 20480000/512000000 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 2000, 2000]} | 0 | 0 | 512000000/512000000 |
| pv | 36 | {'P': [1, 32, 2000, 2000], 'V_shared': [1, 8, 2000, 128], 'output': [1, 32, 2000, 128]} | 16392192000 | 0 | 516096000/16384000 |
| o_proj | 36 | {'input': [2000, 4096], 'weight_math': [4096, 2560], 'weight_storage': [2560, 4096], 'output': [2000, 2560]} | 41943040000 | 20971520 | 16384000/10240000 |
| attention_residual | 36 | {'inputs_each': [2000, 2560], 'output': [2000, 2560]} | 0 | 0 | 20480000/10240000 |
| post_attention_layernorm | 36 | {'input': [2000, 2560], 'weight': [2560], 'output': [2000, 2560]} | 0 | 5120 | 10240000/10240000 |
| gate_proj | 36 | {'input': [2000, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [2000, 9728]} | 99614720000 | 49807360 | 10240000/38912000 |
| up_proj | 36 | {'input': [2000, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [2000, 9728]} | 99614720000 | 49807360 | 10240000/38912000 |
| silu_mul | 36 | {'gate': [2000, 9728], 'up': [2000, 9728], 'output': [2000, 9728]} | 0 | 0 | 77824000/38912000 |
| down_proj | 36 | {'input': [2000, 9728], 'weight_math': [9728, 2560], 'weight_storage': [2560, 9728], 'output': [2000, 2560]} | 99614720000 | 49807360 | 38912000/10240000 |
| ffn_residual | 36 | {'inputs_each': [2000, 2560], 'output': [2000, 2560]} | 0 | 0 | 20480000/10240000 |
| final_norm | 1 | {'input': [2000, 2560], 'weight': [2560], 'output': [2000, 2560]} | 0 | 5120 | 10240000/10240000 |
| lm_head | 1 | {'input': [1, 2560], 'weight_math': [2560, 151936], 'weight_storage': [151936, 2560], 'output': [1, 151936]} | 777912320 | 777912320 | 5120/303872 |
| image_embedding_replace | 1 | {'prompt': [2000, 2560], 'image_embeddings': [1600, 2560]} | 0 | 0 | 18434000/10240000 |
| deepstack_prompt_clone | 3 | {'prompt': [2000, 2560]} | 0 | 0 | 10240000/10240000 |
| deepstack_visual_add | 3 | {'selected_hidden': [1600, 2560], 'deepstack_features': [1600, 2560]} | 0 | 0 | 16384000/8192000 |

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
| qk | 36 | {'Q': [1, 32, 1, 128], 'K_shared': [1, 8, 2001, 128], 'scores_rectangular': [1, 32, 1, 2001]} | 16392192 | 0 | 4106240/256128 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 1, 2001]} | 0 | 0 | 256128/256128 |
| pv | 36 | {'P': [1, 32, 1, 2001], 'V_shared': [1, 8, 2001, 128], 'output': [1, 32, 1, 128]} | 16392192 | 0 | 4354176/8192 |
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
| qk | 36 | {'Q': [1, 32, 1, 128], 'K_shared': [1, 8, 2127, 128], 'scores_rectangular': [1, 32, 1, 2127]} | 17424384 | 0 | 4364288/272256 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 1, 2127]} | 0 | 0 | 272256/272256 |
| pv | 36 | {'P': [1, 32, 1, 2127], 'V_shared': [1, 8, 2127, 128], 'output': [1, 32, 1, 128]} | 17424384 | 0 | 4628352/8192 |
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
