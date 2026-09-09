# vl-request — qwen3-vl-4b

输入：`{"dtype": "bf16", "images": [{"cache_hit": false, "height": 256, "width": 384}], "kv_dtype": "bf16", "output_tokens": 1, "position_segments": [{"kind": "text", "tokens": 13}, {"kind": "image", "preprocessed_height": 256, "preprocessed_width": 384}], "text_tokens": 13}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| visual_positions | 96 |
| non_image_prompt_positions | 13 |
| prompt_positions | 109 |
| requested_output_tokens | 1 |
| decode_forward_calls | 0 |
| prefill_causal_pairs | 5,995 |
| decode_causal_pairs | 0 |
| vision_matrix_flops | 268,569,673,728 |
| language_matrix_flops | 796,376,760,320 |
| total_matrix_flops | 1,064,946,434,048 |
| language_scalar_flops | 423,361,781 |
| vision_scalar_counts | `{"add": 342521184, "multiply": 388572480, "cos": 12288, "sin": 12288, "rsqrt": 19104, "negate": 9437184, "comparison": 56475648, "subtract": 56623104, "exp": 56623104, "divide": 56623104, "tanh": 37748736, "erf": 1572864}` |
| deepstack_language_layer_indices | `[0, 1, 2]` |
| deepstack_prefill_add_elements | 737,280 |
| language_parameters | 4,022,468,096 |
| language_weight_bytes | 8,044,936,192 |
| vision_weight_bytes | 830,695,424 |
| complete_encoder_bytes_per_request | 1,966,080 |
| kv_bytes_per_position | 147,456 |
| prefill_kv_bytes | 16,072,704 |
| final_kv_positions | 109 |
| final_kv_bytes | 16,072,704 |
| decode_kv_new_write_bytes | 0 |
| decode_kv_unique_payload_reads_bytes | 0 |
| output_head_evaluations | 1 |

| 图片 | 缓存命中 | grid THW | patch数 | 语言图像位置 | 本次编码矩阵FLOPs | 完整EC bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | False | [1, 16, 24] | 384 | 96 | 268569673728 | 1966080 |

逐图视觉矩阵：本次工作已乘该图是否未命中；copies仍表示模型内部重复。

| 图片 | 算子 | A | B | copies | 本次矩阵FLOPs |
| --- | --- | --- | --- | --- | --- |
| 0 | patch_embedding | [384, 1536] | [1536, 1024] | 1 | 1207959552 |
| 0 | block.qkv | [384, 1024] | [1024, 3072] | 24 | 57982058496 |
| 0 | block.qk | [384, 64] | [64, 384] | 384 | 7247757312 |
| 0 | block.pv | [384, 384] | [384, 64] | 384 | 7247757312 |
| 0 | block.attention_output | [384, 1024] | [1024, 1024] | 24 | 19327352832 |
| 0 | block.mlp_up | [384, 1024] | [1024, 4096] | 24 | 77309411328 |
| 0 | block.mlp_down | [384, 4096] | [4096, 1024] | 24 | 77309411328 |
| 0 | merger_final.up | [96, 4096] | [4096, 4096] | 1 | 3221225472 |
| 0 | merger_final.out | [96, 4096] | [4096, 2560] | 1 | 2013265920 |
| 0 | merger_deepstack_5.up | [96, 4096] | [4096, 4096] | 1 | 3221225472 |
| 0 | merger_deepstack_5.out | [96, 4096] | [4096, 2560] | 1 | 2013265920 |
| 0 | merger_deepstack_11.up | [96, 4096] | [4096, 4096] | 1 | 3221225472 |
| 0 | merger_deepstack_11.out | [96, 4096] | [4096, 2560] | 1 | 2013265920 |
| 0 | merger_deepstack_17.up | [96, 4096] | [4096, 4096] | 1 | 3221225472 |
| 0 | merger_deepstack_17.out | [96, 4096] | [4096, 2560] | 1 | 2013265920 |

## 静态图像位置构造

旋转坐标跨度与实际KV位置数分开；以下整数/张量接口不重复加入视觉或语言矩阵，也不是HBM测量。

| 指标 | 值 |
| --- | --- |
| prompt_positions | `109` |
| image_positions | `96` |
| next_rotary_position | `25` |
| rope_delta | `-84` |
| decode_rotary_positions | `[]` |
| final_kv_positions | `109` |
| position_ids_bytes | `2616` |
| rope_delta_bytes | `8` |
| rope_delta_cached | `true` |

| 源码步骤 | 声明工作与接口 |
| --- | --- |
| text_arange_expand_add | `{"integer_additions": 39, "materialized_output_bytes": 312, "arange_output_bytes": 104}` |
| image_arange_meshgrid_stack_offset | `{"integer_additions": 116, "integer_multiplications": 1, "materialized_output_bytes": 2304, "arange_output_bytes": 168, "grid_offset_output_bytes": 168, "temporal_inplace_read_write_bytes": 1536, "note": "meshgrid/reshape are views; stack materializes; scalar grid/control operations excluded"}` |
| position_ids_zero_init | `{"materialized_output_bytes": 2616}` |
| segment_cat | `{"operand_read_bytes": 2616, "materialized_output_bytes": 2616}` |
| position_ids_assign | `{"operand_read_bytes": 2616, "materialized_output_bytes": 2616}` |
| position_max_and_delta | `{"reduction_input_elements": 327, "logical_reduction_comparisons": 326, "integer_additions": 1, "integer_subtractions": 1, "materialized_output_bytes": 8, "note": "logical comparisons, not a backend reduction instruction count"}` |
| direct_model_decode_position_add | `{"integer_additions": 0, "materialized_output_bytes": 0, "note": "explicit no-mask direct-model path; generation wrapper preparation separate"}` |
| direct_model_decode_arange | `{"executions": 0, "materialized_output_bytes": 0, "note": "One int64 arange element per decode call; internal arange algorithm unspecified."}` |
| direct_model_decode_delta_repeat_interleave | `{"executions": 0, "operand_read_bytes": 0, "materialized_output_bytes": 0, "note": "Batch1 repeat_interleave(1) materializes the saved int64 delta before broadcast addition."}` |

- Already-tokenized maximal modality runs; image controls belong in text runs.
- No image encoder or language forward work is added here; existing vl_request owns it.
- Position compression never compresses language attention or KV positions.
- Cache hits do not change this result. Feature reuse still requires this request-specific position bridge.
- Source .tolist()/Python grouping and device synchronization latency uncalibrated.
- Logical interfaces are not additive HBM traffic or peak liveness. Arange implementation unspecified.
- Generation wrapper four-plane concatenation and superclass position setup not included; direct model path selected.

| 请求阶段 | 执行次数 | 已汇总矩阵FLOPs |
| --- | ---: | ---: |
| vision_encode | 1 | 268569673728 |
| language_prefill | 1 | 796376760320 |
| language_decode | 0 | 0 |

language_prefill：每行成本乘repeats；完整decode等差和见JSON。

| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |
| --- | ---: | --- | ---: | ---: | --- |
| embedding | 1 | {'indices': [1, 109], 'table': [151936, 2560], 'output': [109, 2560]} | 0 | 558080 | 872/558080 |
| mrope_table | 1 | {'position_ids': [3, 1, 109], 'axis_frequencies': [3, 1, 109, 64], 'cos_sin_each': [1, 109, 128]} | 0 | 0 | 2872/55808 |
| input_layernorm | 36 | {'input': [109, 2560], 'weight': [2560], 'output': [109, 2560]} | 0 | 5120 | 558080/558080 |
| q_proj | 36 | {'input': [109, 2560], 'weight_math': [2560, 4096], 'weight_storage': [4096, 2560], 'output': [109, 4096]} | 2285895680 | 20971520 | 558080/892928 |
| k_proj | 36 | {'input': [109, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [109, 1024]} | 571473920 | 5242880 | 558080/223232 |
| v_proj | 36 | {'input': [109, 2560], 'weight_math': [2560, 1024], 'weight_storage': [1024, 2560], 'output': [109, 1024]} | 571473920 | 5242880 | 558080/223232 |
| q_norm | 36 | {'input': [3488, 128], 'weight': [128], 'output': [3488, 128]} | 0 | 256 | 892928/892928 |
| k_norm | 36 | {'input': [872, 128], 'weight': [128], 'output': [872, 128]} | 0 | 256 | 223232/223232 |
| apply_rope | 36 | {'Q': [1, 32, 109, 128], 'K': [1, 8, 109, 128]} | 0 | 0 | 1171968/1116160 |
| kv_append | 36 | {'new_K_and_V_each': [1, 8, 109, 128]} | 0 | 0 | 446464/446464 |
| qk | 36 | {'Q': [1, 32, 109, 128], 'K_shared': [1, 8, 109, 128], 'scores_rectangular': [1, 32, 109, 109]} | 49111040 | 0 | 1116160/1520768 |
| score_scale_mask_softmax | 36 | {'scores': [1, 32, 109, 109]} | 0 | 0 | 1520768/1520768 |
| pv | 36 | {'P': [1, 32, 109, 109], 'V_shared': [1, 8, 109, 128], 'output': [1, 32, 109, 128]} | 49111040 | 0 | 1744000/892928 |
| o_proj | 36 | {'input': [109, 4096], 'weight_math': [4096, 2560], 'weight_storage': [2560, 4096], 'output': [109, 2560]} | 2285895680 | 20971520 | 892928/558080 |
| attention_residual | 36 | {'inputs_each': [109, 2560], 'output': [109, 2560]} | 0 | 0 | 1116160/558080 |
| post_attention_layernorm | 36 | {'input': [109, 2560], 'weight': [2560], 'output': [109, 2560]} | 0 | 5120 | 558080/558080 |
| gate_proj | 36 | {'input': [109, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [109, 9728]} | 5429002240 | 49807360 | 558080/2120704 |
| up_proj | 36 | {'input': [109, 2560], 'weight_math': [2560, 9728], 'weight_storage': [9728, 2560], 'output': [109, 9728]} | 5429002240 | 49807360 | 558080/2120704 |
| silu_mul | 36 | {'gate': [109, 9728], 'up': [109, 9728], 'output': [109, 9728]} | 0 | 0 | 4241408/2120704 |
| down_proj | 36 | {'input': [109, 9728], 'weight_math': [9728, 2560], 'weight_storage': [2560, 9728], 'output': [109, 2560]} | 5429002240 | 49807360 | 2120704/558080 |
| ffn_residual | 36 | {'inputs_each': [109, 2560], 'output': [109, 2560]} | 0 | 0 | 1116160/558080 |
| final_norm | 1 | {'input': [109, 2560], 'weight': [2560], 'output': [109, 2560]} | 0 | 5120 | 558080/558080 |
| lm_head | 1 | {'input': [1, 2560], 'weight_math': [2560, 151936], 'weight_storage': [151936, 2560], 'output': [1, 151936]} | 777912320 | 777912320 | 5120/303872 |
| image_embedding_replace | 1 | {'prompt': [109, 2560], 'image_embeddings': [96, 2560]} | 0 | 0 | 1049709/558080 |
| deepstack_prompt_clone | 3 | {'prompt': [109, 2560]} | 0 | 0 | 558080/558080 |
| deepstack_visual_add | 3 | {'selected_hidden': [96, 2560], 'deepstack_features': [96, 2560]} | 0 | 0 | 983040/491520 |

计量条件：

- 这是图像VL/ComputerUse请求的阶段账；图像来自预处理后静态尺寸，text_tokens包含真实模板、图像边界、工具说明和其他非图像位置，未执行tokenizer或屏幕截图/动作闭环。不是所有Omni音视频模型的通用执行器。
- vision_encoding复用完整视觉矩阵/scalar账且只计miss图；命中EC仍含final/DeepStack并被语言模型处理，不减少prompt位置、语言attention或KV。无语言prefix-cache命中。
- 视觉每图非因果P²与语言整个prompt因果S(S+1)/2分开。产生图像embedding不等于语言已处理其位置；语言QKV/MLP/attention覆盖图像与文字全部位置，不能再加一次独立图像语言prefill。
- DeepStack来自视觉层5/11/17，在语言0/1/2层之后相加；prefill三次clone和视觉行add单列，后续decode没有图像encoder或DeepStack执行。
- G个输出token由prefill最后一行logits产生第一个，再运行G−1次单token decode；最后输出token尚未写入KV，最终KV长度为S+G−1。EOS提前结束、采样与logit后处理未计。
- 语言有效因果矩阵工作与矩形分数物化预算分列，算子语义读写不是HBM实测。decode逐步历史增长用整数等差求和，未用平均长度近似代替。
- 语言KV保留完整层、GQA共享K/V，不重复乘query heads；kv_dtype只控制元素字节，未计页碎片、量化metadata、TP复制或分配器。权重容量分视觉/语言，不假设两阶段同时常驻同卡。
- 没有CPU图片解码/resize、网络、排队、特征传输/缓存读取计时、kernel launch或设备预测；矩阵和scalar工作不能直接推成完整请求延迟。M-RoPE位置值由position_segments生成；整数与接口工作单列，频率表不重复计算。
- position_bridge supplies explicit static-image index values and separate integer/interface work; existing language mrope_table remains counted exactly once.
- Index construction can overlap image encoding once processed grids are known; the separate position stages do not impose a measured serial latency.

固定来源：

- [configs/models/qwen3-vl-4b/config.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json)，SHA256 `edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/multimodal-cache/qwen3-vl4-preprocessor.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)，SHA256 `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [sources/multimodal-cache/vllm-qwen3-vl.py](https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/model_executor/models/qwen3_vl.py)，SHA256 `f5f45b9002b4a2cda4e0058da02e271841c6d2e619768d26140d144d85c4ef97`。
- [research/vision-encoding/modeling_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py)，SHA256 `b5aa46046548f75c4e7f77e7ccc6717a1a627bead388118844898cfbc94c8bc1`。
- [research/vision-encoding/vision_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py)，SHA256 `bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356`。
- [research/vision-encoding/configuration_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/configuration_qwen3_vl.py)，SHA256 `200b5e015b9e4b6e425122ac0359e3c6281e4a7638a00d8ebfbe853d61dc1bc7`。
