# vision-encoding — qwen3-vl-4b

输入：`{"dtype": "bf16", "encoder_cache_hits": 4, "images_per_request": 4, "preprocessed_height": 640, "preprocessed_width": 640}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| preprocessed_grid_thw | `[1, 40, 40]` |
| patches_per_image | 1,600 |
| merged_positions_per_image | 400 |
| vision_layers | 24 |
| encoder_executions_per_request | 0 |
| encoder_cache_hits | 4 |
| patch_input_shape | `[1600, 1536]` |
| patch_input_bytes_per_image | 4,915,200 |
| matrix_flops_per_image | 1,310,300,569,600 |
| matrix_flops_per_request | 0 |
| scalar_counts_per_image | `{"add": 2174282000, "multiply": 2366162400, "cos": 51200, "sin": 51200, "rsqrt": 79600, "negate": 39321600, "comparison": 982425600, "subtract": 983040000, "exp": 983040000, "divide": 983040000, "tanh": 157286400, "erf": 6553600}` |
| scalar_counts_per_request | `{"add": 0, "multiply": 0, "cos": 0, "sin": 0, "rsqrt": 0, "negate": 0, "comparison": 0, "subtract": 0, "exp": 0, "divide": 0, "tanh": 0, "erf": 0}` |
| complete_vision_learned_parameters | 415,347,712 |
| vision_parameter_bytes_declared_dtype | 830,695,424 |
| one_image_one_layer_materialized_score_bytes | 81,920,000 |
| complete_encoder_bytes_per_image | 8,192,000 |
| complete_encoder_bytes_per_request | 32,768,000 |
| final_and_deepstack_components | `[{"name": "final_embedding", "vision_block": null, "shape": [400, 2560], "bytes": 2048000}, {"name": "deepstack_5", "vision_block": 5, "shape": [400, 2560], "bytes": 2048000}, {"name": "deepstack_11", "vision_block": 11, "shape": [400, 2560], "bytes": 2048000}, {"name": "deepstack_17", "vision_block": 17, "shape": [400, 2560], "bytes": 2048000}]` |
| semantic_read_bytes_per_image | 9,755,295,296 |
| semantic_write_bytes_per_image | 8,422,195,200 |

以下每项已经乘copies，均为每张未命中图片；请求总量再乘编码次数。

| 视觉矩阵 | A | B | copies | FLOPs/图 | 语义读bytes | 语义写bytes |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| patch_embedding | [1600, 1536] | [1536, 1024] | 1 | 5033164800 | 8060928 | 3276800 |
| block.qkv | [1600, 1024] | [1024, 3072] | 24 | 241591910400 | 229638144 | 235929600 |
| block.qk | [1600, 64] | [64, 1600] | 384 | 125829120000 | 157286400 | 1966080000 |
| block.pv | [1600, 1600] | [1600, 64] | 384 | 125829120000 | 2044723200 | 78643200 |
| block.attention_output | [1600, 1024] | [1024, 1024] | 24 | 80530636800 | 128974848 | 78643200 |
| block.mlp_up | [1600, 1024] | [1024, 4096] | 24 | 322122547200 | 279969792 | 314572800 |
| block.mlp_down | [1600, 4096] | [4096, 1024] | 24 | 322122547200 | 515899392 | 78643200 |
| merger_final.up | [400, 4096] | [4096, 4096] | 1 | 13421772800 | 36831232 | 3276800 |
| merger_final.out | [400, 4096] | [4096, 2560] | 1 | 8388608000 | 24248320 | 2048000 |
| merger_deepstack_5.up | [400, 4096] | [4096, 4096] | 1 | 13421772800 | 36831232 | 3276800 |
| merger_deepstack_5.out | [400, 4096] | [4096, 2560] | 1 | 8388608000 | 24248320 | 2048000 |
| merger_deepstack_11.up | [400, 4096] | [4096, 4096] | 1 | 13421772800 | 36831232 | 3276800 |
| merger_deepstack_11.out | [400, 4096] | [4096, 2560] | 1 | 8388608000 | 24248320 | 2048000 |
| merger_deepstack_17.up | [400, 4096] | [4096, 4096] | 1 | 13421772800 | 36831232 | 3276800 |
| merger_deepstack_17.out | [400, 4096] | [4096, 2560] | 1 | 8388608000 | 24248320 | 2048000 |

| 非矩阵步骤 | 形状 | 已汇总参考运算次数/图 | 语义读bytes | 语义写bytes |
| --- | --- | --- | ---: | ---: |
| patch_embedding.bias | [1600, 1024] | {'add': 1638400} | 3278848 | 3276800 |
| learned_position_interpolation | [1600, 1024] | {'multiply': 6553600, 'add': 4915200} | 13132800 | 6553600 |
| position_add | [1600, 1024] | {'add': 1638400} | 6553600 | 3276800 |
| rotary_table | [2, 1600, 16] | {'multiply': 153600, 'cos': 51200, 'sin': 51200} | 12864 | 819200 |
| block.norm1 | [1600, 1024] | {'add': 157248000, 'multiply': 118041600, 'rsqrt': 38400} | 78741504 | 78643200 |
| block.qkv.bias | [1600, 3072] | {'add': 117964800} | 236077056 | 235929600 |
| block.rope_qk | [2, 1600, 1024] | {'multiply': 157286400, 'add': 78643200, 'negate': 39321600} | 648806400 | 314572800 |
| block.score_scale | [16, 1600, 1600] | {'multiply': 983040000} | 1966080000 | 1966080000 |
| block.softmax | [16, 1600, 1600] | {'comparison': 982425600, 'subtract': 983040000, 'exp': 983040000, 'add': 982425600, 'divide': 983040000} | 1966080000 | 1966080000 |
| block.attention_output.bias | [1600, 1024] | {'add': 39321600} | 78692352 | 78643200 |
| block.residual1 | [1600, 1024] | {'add': 39321600} | 157286400 | 78643200 |
| block.norm2 | [1600, 1024] | {'add': 157248000, 'multiply': 118041600, 'rsqrt': 38400} | 78741504 | 78643200 |
| block.mlp_up.bias | [1600, 4096] | {'add': 157286400} | 314769408 | 314572800 |
| block.gelu_tanh | [6553600] | {'multiply': 943718400, 'add': 314572800, 'tanh': 157286400} | 314572800 | 314572800 |
| block.mlp_down.bias | [1600, 1024] | {'add': 39321600} | 78692352 | 78643200 |
| block.residual2 | [1600, 1024] | {'add': 39321600} | 157286400 | 78643200 |
| merger_final.norm | [1600, 1024] | {'add': 6552000, 'multiply': 4918400, 'rsqrt': 1600} | 3280896 | 3276800 |
| merger_final.up.bias | [400, 4096] | {'add': 1638400} | 3284992 | 3276800 |
| merger_final.gelu_exact | [1638400] | {'multiply': 4915200, 'add': 1638400, 'erf': 1638400} | 3276800 | 3276800 |
| merger_final.out.bias | [400, 2560] | {'add': 1024000} | 2053120 | 2048000 |
| merger_deepstack_5.norm | [400, 4096] | {'add': 6553200, 'multiply': 4916000, 'rsqrt': 400} | 3293184 | 3276800 |
| merger_deepstack_5.up.bias | [400, 4096] | {'add': 1638400} | 3284992 | 3276800 |
| merger_deepstack_5.gelu_exact | [1638400] | {'multiply': 4915200, 'add': 1638400, 'erf': 1638400} | 3276800 | 3276800 |
| merger_deepstack_5.out.bias | [400, 2560] | {'add': 1024000} | 2053120 | 2048000 |
| merger_deepstack_11.norm | [400, 4096] | {'add': 6553200, 'multiply': 4916000, 'rsqrt': 400} | 3293184 | 3276800 |
| merger_deepstack_11.up.bias | [400, 4096] | {'add': 1638400} | 3284992 | 3276800 |
| merger_deepstack_11.gelu_exact | [1638400] | {'multiply': 4915200, 'add': 1638400, 'erf': 1638400} | 3276800 | 3276800 |
| merger_deepstack_11.out.bias | [400, 2560] | {'add': 1024000} | 2053120 | 2048000 |
| merger_deepstack_17.norm | [400, 4096] | {'add': 6553200, 'multiply': 4916000, 'rsqrt': 400} | 3293184 | 3276800 |
| merger_deepstack_17.up.bias | [400, 4096] | {'add': 1638400} | 3284992 | 3276800 |
| merger_deepstack_17.gelu_exact | [1638400] | {'multiply': 4915200, 'add': 1638400, 'erf': 1638400} | 3276800 | 3276800 |
| merger_deepstack_17.out.bias | [400, 2560] | {'add': 1024000} | 2053120 | 2048000 |

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
