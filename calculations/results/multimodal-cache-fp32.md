# multimodal-cache — qwen3-vl-4b

输入：`{"arrival_requests_per_second": "0", "compressed_image_bytes": 800000, "dtype": "fp32", "encoder_cache_hit_fraction": "0", "encoder_images_per_second": "12", "images_per_request": 4, "kv_dtype": "bf16", "network_bytes_per_second": 300000000, "pd_requests_per_second": "4", "preprocessed_height": 640, "preprocessed_width": 640, "text_tokens": 400, "total_workers": 4, "uplink_bits_per_second": 6400000}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| preprocessed_grid_thw | `[1, 40, 40]` |
| pre_merge_patch_count | 1,600 |
| image_visual_positions | 400 |
| deepstack_visual_blocks | `[5, 11, 17]` |
| final_embedding_shape | `[400, 2560]` |
| complete_encoder_shape | `[400, 10240]` |
| final_embedding_bytes_per_image | 4,096,000 |
| deepstack_bytes_per_image | 12,288,000 |
| complete_encoder_bytes_per_image | 16,384,000 |
| complete_encoder_bytes_per_request | 65,536,000 |
| visual_positions_per_request | 1,600 |
| declared_input_positions | 2,000 |
| kv_bytes_per_position | 147,456 |
| visual_kv_bytes_per_image | 58,982,400 |
| visual_kv_bytes_per_request | 235,929,600 |
| text_kv_bytes_per_request | 58,982,400 |
| declared_input_kv_bytes | 294,912,000 |
| compressed_image_uplink_exact_seconds | `"1"` |
| complete_encoder_uplink_exact_seconds | `"512/25"` |
| encoder_to_compressed_bytes_ratio_exact | `"512/25"` |
| one_image_ec_network_exact_seconds | `"512/9375"` |
| one_request_ec_network_exact_seconds | `"2048/9375"` |
| ec_transfer_bytes_per_request | 65,536,000 |
| uncached_images_per_request_exact | `"4"` |
| best_known_bound_requests_per_second_exact | `"9375/2048"` |
| best_pool_splits | `[{"encoder_workers": 2, "pd_workers": 2}]` |
| arrival_strictly_below_best_known_bound | `true` |
| encoder_cache_service_capacity_known | `false` |

| E workers | PD workers | 编码上界req/s | PD上界req/s | 网络上界req/s | 已知最小界req/s |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 3 | 3 | 12 | 9375/2048 | 3 |
| 2 | 2 | 6 | 8 | 9375/2048 | 9375/2048 |
| 3 | 1 | 9 | 4 | 9375/2048 | 4 |

计量条件：

- 锁定官方Qwen3-VL-4B配置与预处理配置、固定vLLM输出布局；这里只接受预处理后的单一静态图片尺寸，重复images_per_request次。每边须为patch×merge整数倍且面积在默认预算内；未运行resize、像素归一化、tokenizer、视频采样或视觉剪枝，不能把任意原图尺寸直接代入。
- 静态图片只形成一个temporal grid；temporal_patch_size=2不使位置数翻倍。完整EC沿特征维拼接最终embedding及每个DeepStack输出，消费者再拆分，不把DeepStack维度扩展误算成更多语言token。
- text_tokens是调用者已经计数的其余输入位置，应包含实际模板/特殊token；默认400是教学题设。不自动增加图片边界token，也不冒称完整文本tokenizer输出。KV仅为声明输入位置的完整层逻辑K/V，不含生成增长、页碎片、并行复制、工作区或HBM流量。
- EC和KV精度各自仅决定元素字节；没有量化metadata、误差或转换计时。完整EC不是图片原件、RAW精修输入或语言KV的等价替代，跨问题EC复用与顺序相关KV复用须分别验证身份。
- 压缩图片字节、上行与E/PD/网络能力均为教学输入；时间只算单向payload/BW，不计本地编码、RTT、排队、D2H/H2D、序列化或接收就绪，不是完整请求时间或官方硬件性能。
- E卡12 images/s和PD卡4 requests/s须按给定相同图像/请求形状校准。改变图数、分辨率或dtype而保留速率只是敏感性假设。worker假定能容纳相应模型与状态，未核设备内存、并行组或资源混用。
- cache命中位于E侧；所有图像不论命中仍发送完整EC，命中只减少未缓存编码工作。查询、cache读取/写回与服务槽能力未定价，至少保留一个E worker；h=1的编码约束null表示该工作为零，不表示缓存服务无限快。
- 固定整数E/PD分配穷举所有正池组合，独立已知资源取min，所有并列最优均保留；网络是共享有效单向字节率，不把收发两端相加。到达率严格低于这些上界仍不证明真实稳定性或SLO，缺失缓存服务约束、突发与尾部需另核。

固定来源：

- [configs/models/qwen3-vl-4b/config.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json)，SHA256 `edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/multimodal-cache/qwen3-vl4-preprocessor.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)，SHA256 `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [sources/multimodal-cache/vllm-qwen3-vl.py](https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/model_executor/models/qwen3_vl.py)，SHA256 `f5f45b9002b4a2cda4e0058da02e271841c6d2e619768d26140d144d85c4ef97`。
