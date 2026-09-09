# v4-attention-matrices — deepseek-v4-flash

输入：`{"batch": 1, "history": 0, "tokens": 8192}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| projection_matrix_flops | 83,309,480,640,512 |
| effective_qk_pv_matrix_flops | 16,641,043,726,336 |
| reference_index_matrix_flops | 5,772,436,045,824 |
| matrix_flops | 105,722,960,412,672 |
| reference_with_sparse_tiles_matrix_flops | 107,911,053,312,000 |
| accounted_scalar_flops | 222,218,679,296 |
| matrix_parameters | 5,084,807,168 |
| causal_index_matrix_flops | 2,885,513,379,840 |

矩阵台账按列出的层求和；routed 行的 M 是所有专家的行数之和，各专家尺寸另见下表。

| 矩阵 | 层编号 | 合计 M×K×N／层 | 存储／访问份数每层 | 矩阵 FLOPs | 统一格式权重载荷 bytes |
| --- | --- | --- | --- | ---: | ---: |
| wq_a | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42] | 8192×4096×1024 | 1／1 | 2,954,937,499,648 | 360,710,144 |
| wq_b | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42] | 8192×1024×32768 | 1／1 | 23,639,499,997,184 | 2,885,681,152 |
| wkv_shared | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42] | 8192×4096×512 | 1／1 | 1,477,468,749,824 | 180,355,072 |
| wo_a_grouped | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42] | 65536×4096×1024 | 8／8 | 23,639,499,997,184 | 2,885,681,152 |
| wo_b | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42] | 8192×8192×4096 | 1／1 | 23,639,499,997,184 | 2,885,681,152 |
| compress_r4_wkv | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×4096×1024 | 1／1 | 1,443,109,011,456 | 176,160,768 |
| compress_r4_wgate | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×4096×1024 | 1／1 | 1,443,109,011,456 | 176,160,768 |
| index_wq_b | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×1024×8192 | 1／1 | 2,886,218,022,912 | 352,321,536 |
| index_weights_proj | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×4096×64 | 1／1 | 90,194,313,216 | 11,010,048 |
| index_compress_wkv | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×4096×256 | 1／1 | 360,777,252,864 | 44,040,192 |
| index_compress_wgate | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42] | 8192×4096×256 | 1／1 | 360,777,252,864 | 44,040,192 |
| compress_r128_wkv | [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41] | 8192×4096×512 | 1／1 | 687,194,767,360 | 83,886,080 |
| compress_r128_wgate | [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41] | 8192×4096×512 | 1／1 | 687,194,767,360 | 83,886,080 |

非矩阵算术：表中总数已乘对应层数；特殊函数保持独立原语，不能按 Tensor Core FLOPs 折算。

| 运算 | 层数 | 每层形状 | 普通 FLOPs 合计 | 特殊原语合计 | 计量依据 |
| --- | ---: | --- | ---: | --- | --- |
| q_lowrank_norm | 43 | [8192, 1024] | 1,443,192,832 | {'rsqrt': 352256} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| q_head_norm | 43 | [524288, 512] | 34,650,718,208 | {'rsqrt': 22544384} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| window_kv_norm | 43 | [8192, 512] | 721,772,544 | {'rsqrt': 352256} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| query_rope | 43 | [524288, 64] | 4,328,521,728 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| window_kv_rope | 43 | [8192, 64] | 67,633,152 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| output_inverse_rope | 43 | [524288, 64] | 4,328,521,728 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| window_kv_quantization | 43 | [8192, 448] | 318,087,168 | {'abs': 157810688, 'amax_compare': 155344896, 'scale_floor_compare': 2465792, 'clamp_bound_compare': 315621376, 'power_of_two_scale_bit_round': 2465792, 'fp8_encode': 157810688, 'fp8_decode': 157810688} | QAT simulation returns activation dtype, not FP8-resident cache; arithmetic is expanded below. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r4_main_ape | 21 | [8192, 1024] | 176,246,784 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r4_main_pool_softmax | 21 | [2048, 8, 512] | 506,462,208 | {'exp': 176160768, 'compare_max': 154140672} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r4_main_weighted_pool | 21 | [2048, 8, 512] | 330,301,440 | {} |  |
| compress_r4_main_norm | 21 | [2048, 512] | 88,123,392 | {'rsqrt': 43008} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r4_main_rope | 21 | [2048, 64] | 8,257,536 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r4_main_quantize | 21 | [2048, 448] | 38,836,224 | {'abs': 19267584, 'amax_compare': 18966528, 'scale_floor_compare': 301056, 'clamp_bound_compare': 38535168, 'power_of_two_scale_bit_round': 301056, 'fp8_encode': 19267584, 'fp8_decode': 19267584} |  FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r4_index_ape | 21 | [8192, 256] | 44,061,696 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r4_index_pool_softmax | 21 | [2048, 8, 128] | 126,615,552 | {'exp': 44040192, 'compare_max': 38535168} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r4_index_weighted_pool | 21 | [2048, 8, 128] | 82,575,360 | {} |  |
| compress_r4_index_norm | 21 | [2048, 128] | 22,063,104 | {'rsqrt': 43008} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r4_index_rope | 21 | [2048, 64] | 8,257,536 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r4_index_rotate_quantize | 21 | [2048, 128] | 55,222,272 | {'abs': 5505024, 'amax_compare': 5332992, 'scale_floor_compare': 172032, 'clamp_bound_compare': 11010048, 'power_of_two_scale_bit_round': 172032, 'fp4_encode': 5505024, 'fp4_decode': 5505024} | Hadamard butterfly and FP4 simulation arithmetic are expanded below; no inferred CUDA instruction or traffic count. N log2(N) butterfly add/subtract plus N output scale multiplies per row; CUDA sign/shuffle instructions not inferred. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r128_main_ape | 20 | [8192, 512] | 83,886,080 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r128_main_pool_softmax | 20 | [64, 128, 512] | 251,002,880 | {'exp': 83886080, 'compare_max': 83230720} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r128_main_weighted_pool | 20 | [64, 128, 512] | 167,116,800 | {} |  |
| compress_r128_main_norm | 20 | [64, 512] | 2,622,720 | {'rsqrt': 1280} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r128_main_rope | 20 | [64, 64] | 245,760 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r128_main_quantize | 20 | [64, 448] | 1,155,840 | {'abs': 573440, 'amax_compare': 564480, 'scale_floor_compare': 8960, 'clamp_bound_compare': 1146880, 'power_of_two_scale_bit_round': 8960, 'fp8_encode': 573440, 'fp8_decode': 573440} |  FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| index_query_rope | 21 | [524288, 64] | 2,113,929,216 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| index_query_rotate_quantize | 21 | [8192, 64, 128] | 14,136,901,632 | {'abs': 1409286144, 'amax_compare': 1365245952, 'scale_floor_compare': 44040192, 'clamp_bound_compare': 2818572288, 'power_of_two_scale_bit_round': 44040192, 'fp4_encode': 1409286144, 'fp4_decode': 1409286144} |  N log2(N) butterfly add/subtract plus N output scale multiplies per row; CUDA sign/shuffle instructions not inferred. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| index_head_weight_scale | 21 | [8192, 64] | 11,010,048 | {} |  |
| index_relu_weight_reduce | 21 | [8192, 64, 2048] | 44,744,835,072 | {'relu_compare': 22548578304} | Reference scores all rectangular columns before prefill masking. |
| index_causal_mask_add | 21 | [8192, 2048] | 352,321,536 | {} |  |
| index_topk | 21 | [8192, 2048] | 0 | {'topk_rows': 172032, 'topk_candidates': 352321536} | Selection primitive; no assumed comparison algorithm. |

Attention normalization/rotary, compressor pooling and index scoring only. Sparse-attention online softmax is in sparse_kernel_summary, not this subtotal. Includes mathematical Hadamard butterfly/scale and quantize-dequantize arithmetic; excludes compiler-specific shuffle/sign instructions, frequency table construction, data movement and external sublayer norms. Special functions are not Tensor FLOPs.

稀疏注意力参考 kernel（固定 64-slot tile）：

| 项目 | 值 |
| --- | ---: |
| matrix_flops | 18,829,136,625,664 |
| effective_matrix_flops | 16,641,043,726,336 |
| online_softmax_scalar_flops | 113,008,181,248 |
| exp_ops | 9,360,113,664 |
| max_comparisons | 9,193,914,368 |
| gathered_kv_bytes | 130,008,154,112 |
| query_read_bytes | 23,085,449,216 |
| output_write_bytes | 23,085,449,216 |
| index_read_bytes | 574,619,648 |
| sink_read_bytes | 90,177,536 |
| source_declared_shared_bytes_per_cta | 204,800 |
| source_declared_fragment_bytes_per_cta | 148,992 |

- BF16 Q/KV/probability GEMMs, FP32 score/output accumulators. Two GEMMs execute each padded 64-slot tile even when indices are -1.
- Per head and tile: score scale/subtract/reduce, running-max rescale, denominator update, and D output rescale multiplies; final learned sink exponential and D divisions included.
- Index array width is fixed across queries in prefill; valid historical entries grow per query. Invalid slots do not load KV, but GEMM and online-softmax tile work remain.
- Gathered KV read once per valid index and reused by QK/PV within a tile. No extra K/V factor of two: the shared representation serves both.
- Q, output, indices and sinks use logical per-CTA operands; cache reuse, transactions, spills and allocator traffic are not inferred.
- Shared/fragment sizes sum explicit source declarations only. Compiler pipeline buffering, alignment, register mapping and feasibility must be checked on the target; this is not a measured launch footprint.

计量条件：

- Initial prefill or one-token incremental decode, single-device logical model. No MTP, expert or mHC work in this subledger.
- wo_a consists of independent per-group matrices. Its flattened checkpoint storage is not a dense mixing across all query heads.
- Both compressor projections execute on every new token, including decode steps that do not complete a compressed record.
- Indexer computes all end_pos//4 columns before masking in prefill. Causal index work is a counterfactual lower work count, not the reference GEMM.
- QK/PV count valid selected entries only. Padding, sparse-kernel tile work and attention sink softmax are separate in sparse_kernel_summary. Pooling, norms and RoPE are in non_matrix_operations; Hadamard butterfly and simulation quantization arithmetic are expanded there; bitwise rounding and format casts remain separate primitives.
- Matrix parameters exclude norm scales, attention sinks and compressor APE. Uniform two-byte matrix payload is a teaching comparison, not actual FP8/FP4/FP32 checkpoint storage or HBM.

固定来源：

- [configs/models/deepseek-v4-flash/config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/config.json)，SHA256 `b628e63398a645abc711d92207f8737dd8140f7a4ef1e0a5b3616019e0ddd818`。
- [configs/models/deepseek-v4-flash/inference/config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/config.json)，SHA256 `6cc6f816ca73a8d38750194e330398e4f6955b4b45f674f7d29c96da14ccb733`。
- [sources/deepseek-v4-flash/inference/model.py](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/model.py)，SHA256 `ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71`。
- [sources/deepseek-v4-flash/inference/kernel.py](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/inference/kernel.py)，SHA256 `59b325083d7103975cba025bd0d60ea343bb82d8fff53088afb7c04bd380c0c2`。
- [sources/fast-hadamard-transform/README.md](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/README.md)，SHA256 `e9d1a782e751104628590c481ba325bc436292254aaefe4cfa39ee3c0b1eb00e`。
- [sources/fast-hadamard-transform/csrc/fast_hadamard_transform_common.h](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/csrc/fast_hadamard_transform_common.h)，SHA256 `e51345eb6be7b43cb657d73b8db9b2debcb4060de2266c7b42fc45bb3b86b473`。
- [sources/fast-hadamard-transform/fast_hadamard_transform/fast_hadamard_transform_interface.py](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/fast_hadamard_transform/fast_hadamard_transform_interface.py)，SHA256 `a2f32a615b03c83d075fd49eba266c9f6c13df790cbe549db3bf8c0c1f3e8877`。
- [sources/deepseek-v4-flash/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model.safetensors.index.json)，SHA256 `7e975ba3bef8947a94e7da0abd60888375b232b4dfad883d59653e65c6ba522a`。
- [sources/deepseek-v4-flash/headers/model-00001-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00001-of-00046.safetensors?header=1)，SHA256 `7bdd252c75d1e8975a69b8399b226f0129ce119b23da7bd68deac4ba4b1a4a40`。
- [sources/deepseek-v4-flash/headers/model-00002-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00002-of-00046.safetensors?header=1)，SHA256 `adbe0338649aec4a8099bd12e7f99b18b3497f73b38345f84ecb1c46eca9d992`。
- [sources/deepseek-v4-flash/headers/model-00003-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00003-of-00046.safetensors?header=1)，SHA256 `066ac29abaa9071fd8af1166d76c411844336d778eea985781354b0a651bfd5f`。
- [sources/deepseek-v4-flash/headers/model-00004-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00004-of-00046.safetensors?header=1)，SHA256 `739266275c9abeafe21fcf8def381588c2a556bae0206d42659789ab603c997e`。
- [sources/deepseek-v4-flash/headers/model-00005-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00005-of-00046.safetensors?header=1)，SHA256 `00bf95ba015a6cb4f02c3bd6bab53b2bf12def11ed1201ac8e6b4e8e380299bb`。
- [sources/deepseek-v4-flash/headers/model-00006-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00006-of-00046.safetensors?header=1)，SHA256 `c3fdf86122ab5d53a8c4d08eba13aaf8063e87cc475dc67072cb7a88106c6eac`。
- [sources/deepseek-v4-flash/headers/model-00007-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00007-of-00046.safetensors?header=1)，SHA256 `2bb96fe9673587075839f4f38a6758a00c655d1386d93937ecb31a8fae7aa4e4`。
- [sources/deepseek-v4-flash/headers/model-00008-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00008-of-00046.safetensors?header=1)，SHA256 `0f2cd169dd987424c04f4c04090b72f8ad780e1069fb9a49fd29340434bc0db7`。
- [sources/deepseek-v4-flash/headers/model-00009-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00009-of-00046.safetensors?header=1)，SHA256 `c42b8df2eb4810f731edf8a646f61ba54226f66de484faa12df306e2bfbc18df`。
- [sources/deepseek-v4-flash/headers/model-00010-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00010-of-00046.safetensors?header=1)，SHA256 `4ddfce5b94da6cf104f0c569357107d75466f57896eea5913f14bf2d9d669df8`。
- [sources/deepseek-v4-flash/headers/model-00011-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00011-of-00046.safetensors?header=1)，SHA256 `a166d9008aebc86ffa5292305b5cd47b0ebfab13e59d2e9727bdff64f2273cf6`。
- [sources/deepseek-v4-flash/headers/model-00012-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00012-of-00046.safetensors?header=1)，SHA256 `817002743a975c90a12ba1305d7a1cb31e2c1e3aee54fe7ecb1c01f052ace3c8`。
- [sources/deepseek-v4-flash/headers/model-00013-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00013-of-00046.safetensors?header=1)，SHA256 `d2ca46ad597b90fbf32413a3f722a20d965500556d18c1a8c3d7fd362e7162d0`。
- [sources/deepseek-v4-flash/headers/model-00014-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00014-of-00046.safetensors?header=1)，SHA256 `96a3457df88bcb76bd021b88abc4affa414a7337959ba53483474a8dc3c87325`。
- [sources/deepseek-v4-flash/headers/model-00015-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00015-of-00046.safetensors?header=1)，SHA256 `cf8bce7b372e692d908185249a2f2405432b21f7e7d209fa701d13934e599ad0`。
- [sources/deepseek-v4-flash/headers/model-00016-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00016-of-00046.safetensors?header=1)，SHA256 `758a06cf96357bcc35172bb569673cf3da9a49a7b7c0196d700734fe3ed6ceef`。
- [sources/deepseek-v4-flash/headers/model-00017-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00017-of-00046.safetensors?header=1)，SHA256 `bef71dd20ade402de29a55026e7ca4239286c1e17767a5a06a6985888ad00b77`。
- [sources/deepseek-v4-flash/headers/model-00018-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00018-of-00046.safetensors?header=1)，SHA256 `d752870f40b3db91c87e95dd9e4264ea1df5cad65d48365d1559d62bf6074b57`。
- [sources/deepseek-v4-flash/headers/model-00019-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00019-of-00046.safetensors?header=1)，SHA256 `9c59b39cf7e4411fd6be6cef6be84d9505479e7c74cd6a6aed31e4acbbbfe4db`。
- [sources/deepseek-v4-flash/headers/model-00020-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00020-of-00046.safetensors?header=1)，SHA256 `b78c94a19d78e815a59e381c070f9bb71c80afca32fb65b8cf3ddd4869f76a40`。
- [sources/deepseek-v4-flash/headers/model-00021-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00021-of-00046.safetensors?header=1)，SHA256 `f4eae632cce4ebb4c7d6604a26b4404bbe0ed780b85309d370789901773f8865`。
- [sources/deepseek-v4-flash/headers/model-00022-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00022-of-00046.safetensors?header=1)，SHA256 `e51e7f6ee11a7398e16082d2c821302cafb272a0f6760b848eba4457ed33091e`。
- [sources/deepseek-v4-flash/headers/model-00023-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00023-of-00046.safetensors?header=1)，SHA256 `c834cc39b1bfab2222a6e61d61cd897012694f46b395cbb8c5dcee273667e875`。
- [sources/deepseek-v4-flash/headers/model-00024-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00024-of-00046.safetensors?header=1)，SHA256 `bce06d093a55e7549d1c7828dde524d0274e08fd2b0906459b5df8311a728344`。
- [sources/deepseek-v4-flash/headers/model-00025-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00025-of-00046.safetensors?header=1)，SHA256 `bcd896440e657458ffc1a03748c740c8da52d6a8792279d96a1aa30785ee0211`。
- [sources/deepseek-v4-flash/headers/model-00026-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00026-of-00046.safetensors?header=1)，SHA256 `a8ccf8bfe0299db51fe7ba2a372be4e8b216b8e757e1f28376aeabe520f79b71`。
- [sources/deepseek-v4-flash/headers/model-00027-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00027-of-00046.safetensors?header=1)，SHA256 `9761e7cdccbac4388df634eeb6135335742fb57c0a2291b49545d5846dc5d59c`。
- [sources/deepseek-v4-flash/headers/model-00028-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00028-of-00046.safetensors?header=1)，SHA256 `ed35c3458805563571cc084014f95b1b520ddb2f720dc7be313fb36e85c2b631`。
- [sources/deepseek-v4-flash/headers/model-00029-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00029-of-00046.safetensors?header=1)，SHA256 `df0037d7d7b0c8c3533ba7d8017b080ba628141ceb432046c18b7b80c7641ee8`。
- [sources/deepseek-v4-flash/headers/model-00030-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00030-of-00046.safetensors?header=1)，SHA256 `f10b48bae9465a0ecf009b78e2602988dcce8f11efcb8ecf39be8eb60c3de41c`。
- [sources/deepseek-v4-flash/headers/model-00031-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00031-of-00046.safetensors?header=1)，SHA256 `5b9ba12c0356d38bb4be66ef38feed3f7dd5ae558e39e8da6190396bba2bb129`。
- [sources/deepseek-v4-flash/headers/model-00032-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00032-of-00046.safetensors?header=1)，SHA256 `03874e0e912e3639adea07b51aeafe9ab3eb84d5715defbace83a6ed0a002a95`。
- [sources/deepseek-v4-flash/headers/model-00033-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00033-of-00046.safetensors?header=1)，SHA256 `13ef931a9fcd6bca4ffabdbbeccefbb7b4fa014facde32eeaeeb6e3bed6453ce`。
- [sources/deepseek-v4-flash/headers/model-00034-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00034-of-00046.safetensors?header=1)，SHA256 `61c718832c85e4673c46a50b910e0c9ea0aeadd9f12a7131f1f40157d020c6de`。
- [sources/deepseek-v4-flash/headers/model-00035-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00035-of-00046.safetensors?header=1)，SHA256 `22a3adf08b435595c3862f5289bf2797ff7157258c7cfa24ff1b0313aeae8bd0`。
- [sources/deepseek-v4-flash/headers/model-00036-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00036-of-00046.safetensors?header=1)，SHA256 `359e010953a51169166f7140842b149e9f236c942cb99b2dc6082d7961011e16`。
- [sources/deepseek-v4-flash/headers/model-00037-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00037-of-00046.safetensors?header=1)，SHA256 `8b228cfe5f5f6d5f5834046d5f7cd0045410b6f20048adf533170e3d23071b9a`。
- [sources/deepseek-v4-flash/headers/model-00038-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00038-of-00046.safetensors?header=1)，SHA256 `deff29eb762eae6765766f6f2b1888cd7f627effd297bc4675d150d55171c425`。
- [sources/deepseek-v4-flash/headers/model-00039-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00039-of-00046.safetensors?header=1)，SHA256 `44b9d5cec4550fd656c9da02bd51fde182812350601b9415e05210efe16b23bd`。
- [sources/deepseek-v4-flash/headers/model-00040-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00040-of-00046.safetensors?header=1)，SHA256 `9f4e9b51b358e7f49827305e1b2e8fd1bffcb27567aebee96b5382a58a5a76a8`。
- [sources/deepseek-v4-flash/headers/model-00041-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00041-of-00046.safetensors?header=1)，SHA256 `3cbe8dd9615eb0f1579a0bf83ab8885859348eaab555ce1fa43453fe78a9d3da`。
- [sources/deepseek-v4-flash/headers/model-00042-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00042-of-00046.safetensors?header=1)，SHA256 `590483059c64c03a3c140b8a4c692441bda09e1c8d3c8a50e0f3b9e5bdb6569d`。
- [sources/deepseek-v4-flash/headers/model-00043-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00043-of-00046.safetensors?header=1)，SHA256 `da9f9b7994e40f1b7e34416856e3f0927884cc5adf6ded630a4ce1cfb576fb82`。
- [sources/deepseek-v4-flash/headers/model-00044-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00044-of-00046.safetensors?header=1)，SHA256 `a95f8067ab7db45ecb0118b4207aa68ed1b270c41e23849b48244c1d78799396`。
- [sources/deepseek-v4-flash/headers/model-00045-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00045-of-00046.safetensors?header=1)，SHA256 `76d10bb3b022bad26446539ebaf16c9245fdcf835b28fd55a75052e0b0bb60b8`。
- [sources/deepseek-v4-flash/headers/model-00046-of-00046.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/resolve/60d8d70770c6776ff598c94bb586a859a38244f1/model-00046-of-00046.safetensors?header=1)，SHA256 `10f90b036e608fabcf2c781dd5274a0fbc262f7aeaf959218ff1ccb829903981`。
