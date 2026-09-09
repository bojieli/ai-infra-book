# vision-encoding — qwen3-vl-4b

输入：`{"dtype": "bf16", "encoder_cache_hits": 0, "images_per_request": 4, "preprocessed_height": 640, "preprocessed_width": 672}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| preprocessed_grid_thw | `[1, 40, 42]` |
| patches_per_image | 1,680 |
| merged_positions_per_image | 420 |
| vision_layers | 24 |
| encoder_executions_per_request | 4 |
| encoder_cache_hits | 0 |
| patch_input_shape | `[1680, 1536]` |
| patch_input_bytes_per_image | 5,160,960 |
| matrix_flops_per_image | 1,389,027,655,680 |
| matrix_flops_per_request | 5,556,110,622,720 |
| scalar_counts_per_image | `{"add": 2334605700, "multiply": 2536080120, "cos": 53760, "sin": 53760, "rsqrt": 83580, "negate": 41287680, "comparison": 1083156480, "subtract": 1083801600, "exp": 1083801600, "divide": 1083801600, "tanh": 165150720, "erf": 6881280}` |
| scalar_counts_per_request | `{"add": 9338422800, "multiply": 10144320480, "cos": 215040, "sin": 215040, "rsqrt": 334320, "negate": 165150720, "comparison": 4332625920, "subtract": 4335206400, "exp": 4335206400, "divide": 4335206400, "tanh": 660602880, "erf": 27525120}` |
| complete_vision_learned_parameters | 415,347,712 |
| vision_parameter_bytes_declared_dtype | 830,695,424 |
| one_image_one_layer_materialized_score_bytes | 90,316,800 |
| complete_encoder_bytes_per_image | 8,601,600 |
| complete_encoder_bytes_per_request | 34,406,400 |
| final_and_deepstack_components | `[{"name": "final_embedding", "vision_block": null, "shape": [420, 2560], "bytes": 2150400}, {"name": "deepstack_5", "vision_block": 5, "shape": [420, 2560], "bytes": 2150400}, {"name": "deepstack_11", "vision_block": 11, "shape": [420, 2560], "bytes": 2150400}, {"name": "deepstack_17", "vision_block": 17, "shape": [420, 2560], "bytes": 2150400}]` |
| semantic_read_bytes_per_image | 10,511,418,816 |
| semantic_write_bytes_per_image | 9,152,962,560 |

以下每项已经乘copies，均为每张未命中图片；请求总量再乘编码次数。

| 视觉矩阵 | A | B | copies | FLOPs/图 | 语义读bytes | 语义写bytes |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| patch_embedding | [1680, 1536] | [1536, 1024] | 1 | 5284823040 | 8306688 | 3440640 |
| block.qkv | [1680, 1024] | [1024, 3072] | 24 | 253671505920 | 233570304 | 247726080 |
| block.qk | [1680, 64] | [64, 1680] | 384 | 138726604800 | 165150720 | 2167603200 |
| block.pv | [1680, 1680] | [1680, 64] | 384 | 138726604800 | 2250178560 | 82575360 |
| block.attention_output | [1680, 1024] | [1024, 1024] | 24 | 84557168640 | 132907008 | 82575360 |
| block.mlp_up | [1680, 1024] | [1024, 4096] | 24 | 338228674560 | 283901952 | 330301440 |
| block.mlp_down | [1680, 4096] | [4096, 1024] | 24 | 338228674560 | 531628032 | 82575360 |
| merger_final.up | [420, 4096] | [4096, 4096] | 1 | 14092861440 | 36995072 | 3440640 |
| merger_final.out | [420, 4096] | [4096, 2560] | 1 | 8808038400 | 24412160 | 2150400 |
| merger_deepstack_5.up | [420, 4096] | [4096, 4096] | 1 | 14092861440 | 36995072 | 3440640 |
| merger_deepstack_5.out | [420, 4096] | [4096, 2560] | 1 | 8808038400 | 24412160 | 2150400 |
| merger_deepstack_11.up | [420, 4096] | [4096, 4096] | 1 | 14092861440 | 36995072 | 3440640 |
| merger_deepstack_11.out | [420, 4096] | [4096, 2560] | 1 | 8808038400 | 24412160 | 2150400 |
| merger_deepstack_17.up | [420, 4096] | [4096, 4096] | 1 | 14092861440 | 36995072 | 3440640 |
| merger_deepstack_17.out | [420, 4096] | [4096, 2560] | 1 | 8808038400 | 24412160 | 2150400 |

| 非矩阵步骤 | 形状 | 已汇总参考运算次数/图 | 语义读bytes | 语义写bytes |
| --- | --- | --- | ---: | ---: |
| patch_embedding.bias | [1680, 1024] | {'add': 1720320} | 3442688 | 3440640 |
| learned_position_interpolation | [1680, 1024] | {'multiply': 6881280, 'add': 5160960} | 13789440 | 6881280 |
| position_add | [1680, 1024] | {'add': 1720320} | 6881280 | 3440640 |
| rotary_table | [2, 1680, 16] | {'multiply': 161280, 'cos': 53760, 'sin': 53760} | 13504 | 860160 |
| block.norm1 | [1680, 1024] | {'add': 165110400, 'multiply': 123943680, 'rsqrt': 40320} | 82673664 | 82575360 |
| block.qkv.bias | [1680, 3072] | {'add': 123863040} | 247873536 | 247726080 |
| block.rope_qk | [2, 1680, 1024] | {'multiply': 165150720, 'add': 82575360, 'negate': 41287680} | 681246720 | 330301440 |
| block.score_scale | [16, 1680, 1680] | {'multiply': 1083801600} | 2167603200 | 2167603200 |
| block.softmax | [16, 1680, 1680] | {'comparison': 1083156480, 'subtract': 1083801600, 'exp': 1083801600, 'add': 1083156480, 'divide': 1083801600} | 2167603200 | 2167603200 |
| block.attention_output.bias | [1680, 1024] | {'add': 41287680} | 82624512 | 82575360 |
| block.residual1 | [1680, 1024] | {'add': 41287680} | 165150720 | 82575360 |
| block.norm2 | [1680, 1024] | {'add': 165110400, 'multiply': 123943680, 'rsqrt': 40320} | 82673664 | 82575360 |
| block.mlp_up.bias | [1680, 4096] | {'add': 165150720} | 330498048 | 330301440 |
| block.gelu_tanh | [6881280] | {'multiply': 990904320, 'add': 330301440, 'tanh': 165150720} | 330301440 | 330301440 |
| block.mlp_down.bias | [1680, 1024] | {'add': 41287680} | 82624512 | 82575360 |
| block.residual2 | [1680, 1024] | {'add': 41287680} | 165150720 | 82575360 |
| merger_final.norm | [1680, 1024] | {'add': 6879600, 'multiply': 5164320, 'rsqrt': 1680} | 3444736 | 3440640 |
| merger_final.up.bias | [420, 4096] | {'add': 1720320} | 3448832 | 3440640 |
| merger_final.gelu_exact | [1720320] | {'multiply': 5160960, 'add': 1720320, 'erf': 1720320} | 3440640 | 3440640 |
| merger_final.out.bias | [420, 2560] | {'add': 1075200} | 2155520 | 2150400 |
| merger_deepstack_5.norm | [420, 4096] | {'add': 6880860, 'multiply': 5161800, 'rsqrt': 420} | 3457024 | 3440640 |
| merger_deepstack_5.up.bias | [420, 4096] | {'add': 1720320} | 3448832 | 3440640 |
| merger_deepstack_5.gelu_exact | [1720320] | {'multiply': 5160960, 'add': 1720320, 'erf': 1720320} | 3440640 | 3440640 |
| merger_deepstack_5.out.bias | [420, 2560] | {'add': 1075200} | 2155520 | 2150400 |
| merger_deepstack_11.norm | [420, 4096] | {'add': 6880860, 'multiply': 5161800, 'rsqrt': 420} | 3457024 | 3440640 |
| merger_deepstack_11.up.bias | [420, 4096] | {'add': 1720320} | 3448832 | 3440640 |
| merger_deepstack_11.gelu_exact | [1720320] | {'multiply': 5160960, 'add': 1720320, 'erf': 1720320} | 3440640 | 3440640 |
| merger_deepstack_11.out.bias | [420, 2560] | {'add': 1075200} | 2155520 | 2150400 |
| merger_deepstack_17.norm | [420, 4096] | {'add': 6880860, 'multiply': 5161800, 'rsqrt': 420} | 3457024 | 3440640 |
| merger_deepstack_17.up.bias | [420, 4096] | {'add': 1720320} | 3448832 | 3440640 |
| merger_deepstack_17.gelu_exact | [1720320] | {'multiply': 5160960, 'add': 1720320, 'erf': 1720320} | 3440640 | 3440640 |
| merger_deepstack_17.out.bias | [420, 2560] | {'add': 1075200} | 2155520 | 2150400 |

计量条件：

- 输入为已预处理静态图，复用multimodal_cache官方patch/merge/面积校验；不计JPEG/PNG解码、resize、像素标准化、CPU调度。temporal patch复制已体现在1536输入宽，不把静态图token翻倍。
- 逐图独立非因果视觉attention；N张同尺寸图的QK/PV为N×P²，不是(NP)²。24个视觉block、final merger和3个DeepStack分别计一次，完全不包含语言prefill或语言KV写入，避免与语言预算重复。
- 矩阵按2MNK统计，bias和所有列出的norm/activation/softmax/RoPE/残差单列；exp/tanh/erf/rsqrt等调用数不等同一个FLOP。LayerNorm为明确两遍参考算术分解，实际kernel可融合/改变归约次序。
- 逻辑tensor读写表示逐算子语义操作数，参数可重复读；不是HBM访存实测。dtype控制声明模型边界操作数存储字节；位置插值权重/输出与RoPE显式FP32操作数按4B保留。LayerNorm/softmax内部FP32中间量、casts与实际工作区另计，不据此套统一低精度峰值。
- learned position四邻点加权与rotary table主体已计；位置index/grid构造、插值权重计算、rope inv_freq初始化和数据搬运未计，故scalar清单是声明参考工作而非所有系统指令。
- final norm在[P,1024]上执行，DeepStack norm在[P/4,4096]上执行；merger使用erf GELU，block使用tanh GELU。DeepStack扩展EC特征维，不增加语言图像位置数。
- encoder_cache_hits为整数已验证命中图数；命中跳过所有视觉工作，但仍返回所有图EC字节。缓存查找/读取/身份校验和E/PD传输不在本编码工作内，没有据此推断命中延迟或吞吐。
- 参数数目包含patch/position embedding/全部block与merger的Linear bias和LayerNorm affine，不含非持久rope buffer、语言模型；假设所选dtype统一保存参数，实际checkpoint混合精度及并行复制需要另核。

固定来源：

- [configs/models/qwen3-vl-4b/config.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json)，SHA256 `edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/multimodal-cache/qwen3-vl4-preprocessor.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)，SHA256 `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [sources/multimodal-cache/vllm-qwen3-vl.py](https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/model_executor/models/qwen3_vl.py)，SHA256 `f5f45b9002b4a2cda4e0058da02e271841c6d2e619768d26140d144d85c4ef97`。
- [research/vision-encoding/modeling_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py)，SHA256 `b5aa46046548f75c4e7f77e7ccc6717a1a627bead388118844898cfbc94c8bc1`。
- [research/vision-encoding/vision_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py)，SHA256 `bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356`。
- [research/vision-encoding/configuration_qwen3_vl.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/configuration_qwen3_vl.py)，SHA256 `200b5e015b9e4b6e425122ac0359e3c6281e4a7638a00d8ebfbe853d61dc1bc7`。
