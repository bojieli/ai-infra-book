# weight-offload — 

输入：`{"bandwidth_bytes_per_second": 25769803776, "batch": 1, "buffer_slots": 2, "history": 8192, "kv_length": 8192, "layer_compute_ns": 1000000, "model": "qwen3-8b", "offloaded_layers": [3, 7, 11, 15, 19, 23, 27, 31, 35], "passes": 1, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| ffn_parameters_per_layer | 150,994,944 |
| ffn_bytes_per_layer | 301,989,888 |
| offloaded_unique_weight_bytes | 2,717,908,992 |
| host_weight_bytes | 2,717,908,992 |
| gpu_buffer_bytes | 603,979,776 |
| net_gpu_weight_bytes_saved | 2,113,929,216 |
| equivalent_independent_kv_requests | 1 |
| kv_bytes_per_independent_request | 1,207,959,552 |
| remaining_saved_bytes | 905,969,664 |
| per_forward_h2d_bytes | 2,717,908,992 |
| total_h2d_bytes | 2,717,908,992 |
| per_forward_copy_service_ns_exact | `"105468750"` |
| copy_service_per_input_token_ns_exact | `"105468750"` |
| copy_only_decode_throughput_upper_tokens_per_s | 9.481481481481481 |
| baseline_compute_ns | 36,000,000 |
| scheduled_finish_ns_exact | `"106468750"` |
| exposed_wait_ns_exact | `"70468750"` |
| selected_ffn_matrix_flops_per_forward | 2,717,908,992 |
| target_matrix_flops_per_forward | 19,968,622,592 |

| pass／层 | 槽 | 复制开始ns | 复制结束ns | 消费开始ns | 消费结束ns |
| --- | ---: | --- | --- | --- | --- |
| 0/3 | 0 | 0 | 11718750 | 11718750 | 12718750 |
| 0/7 | 1 | 11718750 | 23437500 | 23437500 | 24437500 |
| 0/11 | 0 | 23437500 | 35156250 | 35156250 | 36156250 |
| 0/15 | 1 | 35156250 | 46875000 | 46875000 | 47875000 |
| 0/19 | 0 | 46875000 | 58593750 | 58593750 | 59593750 |
| 0/23 | 1 | 58593750 | 70312500 | 70312500 | 71312500 |
| 0/27 | 0 | 70312500 | 82031250 | 82031250 | 83031250 |
| 0/31 | 1 | 82031250 | 93750000 | 93750000 | 94750000 |
| 0/35 | 0 | 93750000 | 105468750 | 105468750 | 106468750 |

计量条件：

- 官方Dense Qwen各层SwiGLU三矩阵BF16相同shape，显式选中层卸载FFN。默认36层每四层选最后一层共9份；主存保存全部卸载权重，GPU静态槽每槽可放一份。未执行真实引擎。
- 独立H2D串行资源与GPU逐层串行资源，所有主存权重从时刻0可读；复制按层／pass顺序尽早排队，消费者等待当前权重。槽从复制开始到消费层结束不可覆盖，同槽下次复制依赖上次消费者结束。
- 每次pass完整重新搬入选中权重，包含首次填充、跨pass环回及最后消费；即使最终槽内容碰巧可复用也不跳过复制。层时长为显式教学输入，不能从Async、UVA或预取名称推断这种重叠已实现。
- layer_compute_ns计完整层且各层相同，包括其中未单列算术；copy带宽为有效单向教学速率，未套双向链路宣传峰值，未模拟H2D／GPU对主存和HBM的竞争。缓冲延迟释放到层末是保守约定。
- 容量净节省=卸载BF16权重-静态GPU槽，另比独立BF16 KV；未计pinning副本、页／图／工作区与其他模型权重。更多槽不改变每pass复制字节，会减少KV可用空间。
- batch/tokens用于一次固定形状forward的矩阵工作与流量摊销；多个pass是重复该形状的执行调度，不是历史增长的完整生成请求。copy-only吞吐上限仅对decode(tokens=1)，不将每token摊销时间当单请求步延迟。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
