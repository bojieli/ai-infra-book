# v4-attention-matrices — deepseek-v4-pro

输入：`{"batch": 64, "history": 8192, "tokens": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| projection_matrix_flops | 2,491,232,026,624 |
| effective_qk_pv_matrix_flops | 679,678,574,592 |
| reference_index_matrix_flops | 64,424,509,440 |
| matrix_flops | 3,235,335,110,656 |
| reference_with_sparse_tiles_matrix_flops | 3,235,335,110,656 |
| accounted_scalar_flops | 5,598,402,880 |
| matrix_parameters | 19,462,750,208 |
| causal_index_matrix_flops | 64,424,509,440 |

矩阵台账按列出的层求和；routed 行的 M 是所有专家的行数之和，各专家尺寸另见下表。

| 矩阵 | 层编号 | 合计 M×K×N／层 | 存储／访问份数每层 | 矩阵 FLOPs | 统一格式权重载荷 bytes |
| --- | --- | --- | --- | ---: | ---: |
| wq_a | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60] | 64×7168×1536 | 1／1 | 85,966,454,784 | 1,343,225,856 |
| wq_b | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60] | 64×1536×65536 | 1／1 | 785,979,015,168 | 12,280,922,112 |
| wkv_shared | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60] | 64×7168×512 | 1／1 | 28,655,484,928 | 447,741,952 |
| wo_a_grouped | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60] | 1024×4096×1024 | 16／16 | 523,986,010,112 | 8,187,281,408 |
| wo_b | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60] | 64×16384×7168 | 1／1 | 916,975,517,696 | 14,327,742,464 |
| compress_r4_wkv | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×7168×1024 | 1／1 | 28,185,722,880 | 440,401,920 |
| compress_r4_wgate | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×7168×1024 | 1／1 | 28,185,722,880 | 440,401,920 |
| index_wq_b | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×1536×8192 | 1／1 | 48,318,382,080 | 754,974,720 |
| index_weights_proj | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×7168×64 | 1／1 | 1,761,607,680 | 27,525,120 |
| index_compress_wkv | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×7168×256 | 1／1 | 7,046,430,720 | 110,100,480 |
| index_compress_wgate | [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60] | 64×7168×256 | 1／1 | 7,046,430,720 | 110,100,480 |
| compress_r128_wkv | [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 57, 59] | 64×7168×512 | 1／1 | 14,562,623,488 | 227,540,992 |
| compress_r128_wgate | [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 57, 59] | 64×7168×512 | 1／1 | 14,562,623,488 | 227,540,992 |

非矩阵算术：表中总数已乘对应层数；特殊函数保持独立原语，不能按 Tensor Core FLOPs 折算。

| 运算 | 层数 | 每层形状 | 普通 FLOPs 合计 | 特殊原语合计 | 计量依据 |
| --- | ---: | --- | ---: | --- | --- |
| q_lowrank_norm | 61 | [64, 1536] | 23,990,080 | {'rsqrt': 3904} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| q_head_norm | 61 | [8192, 512] | 768,057,344 | {'rsqrt': 499712} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| window_kv_norm | 61 | [64, 512] | 7,999,296 | {'rsqrt': 3904} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| query_rope | 61 | [8192, 64] | 95,944,704 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| window_kv_rope | 61 | [64, 64] | 749,568 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| output_inverse_rope | 61 | [8192, 64] | 95,944,704 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| window_kv_quantization | 61 | [64, 448] | 3,525,312 | {'abs': 1748992, 'amax_compare': 1721664, 'scale_floor_compare': 27328, 'clamp_bound_compare': 3497984, 'power_of_two_scale_bit_round': 27328, 'fp8_encode': 1748992, 'fp8_decode': 1748992} | QAT simulation returns activation dtype, not FP8-resident cache; arithmetic is expanded below. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r4_main_ape | 30 | [64, 1024] | 1,966,080 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r4_main_pool_softmax | 30 | [0, 8, 512] | 0 | {'exp': 0, 'compare_max': 0} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r4_main_weighted_pool | 30 | [0, 8, 512] | 0 | {} |  |
| compress_r4_main_norm | 30 | [0, 512] | 0 | {'rsqrt': 0} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r4_main_rope | 30 | [0, 64] | 0 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r4_main_quantize | 30 | [0, 448] | 0 | {'abs': 0, 'amax_compare': 0, 'scale_floor_compare': 0, 'clamp_bound_compare': 0, 'power_of_two_scale_bit_round': 0, 'fp8_encode': 0, 'fp8_decode': 0} |  FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r4_index_ape | 30 | [64, 256] | 491,520 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r4_index_pool_softmax | 30 | [0, 8, 128] | 0 | {'exp': 0, 'compare_max': 0} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r4_index_weighted_pool | 30 | [0, 8, 128] | 0 | {} |  |
| compress_r4_index_norm | 30 | [0, 128] | 0 | {'rsqrt': 0} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r4_index_rope | 30 | [0, 64] | 0 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r4_index_rotate_quantize | 30 | [0, 128] | 0 | {'abs': 0, 'amax_compare': 0, 'scale_floor_compare': 0, 'clamp_bound_compare': 0, 'power_of_two_scale_bit_round': 0, 'fp4_encode': 0, 'fp4_decode': 0} | Hadamard butterfly and FP4 simulation arithmetic are expanded below; no inferred CUDA instruction or traffic count. N log2(N) butterfly add/subtract plus N output scale multiplies per row; CUDA sign/shuffle instructions not inferred. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| compress_r128_main_ape | 31 | [64, 512] | 1,015,808 | {} | Includes duplicate APE addition when prefill saves the last full overlap block for subsequent decode. |
| compress_r128_main_pool_softmax | 31 | [0, 128, 512] | 0 | {'exp': 0, 'compare_max': 0} | Softmax across the pooled token axis, independently for every channel. First overlap block includes padded slots. |
| compress_r128_main_weighted_pool | 31 | [0, 128, 512] | 0 | {} |  |
| compress_r128_main_norm | 31 | [0, 512] | 0 | {'rsqrt': 0} | Square, n-1 sum, mean division, epsilon, normalization multiply, and learned scale if present. |
| compress_r128_main_rope | 31 | [0, 64] | 0 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| compress_r128_main_quantize | 31 | [0, 448] | 0 | {'abs': 0, 'amax_compare': 0, 'scale_floor_compare': 0, 'clamp_bound_compare': 0, 'power_of_two_scale_bit_round': 0, 'fp8_encode': 0, 'fp8_decode': 0} |  FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| index_query_rope | 30 | [4096, 64] | 23,592,960 | {} | Complex multiply: four multiplies and two add/subtract per pair; excludes frequency-table construction and casts. |
| index_query_rotate_quantize | 30 | [64, 64, 128] | 157,777,920 | {'abs': 15728640, 'amax_compare': 15237120, 'scale_floor_compare': 491520, 'clamp_bound_compare': 31457280, 'power_of_two_scale_bit_round': 491520, 'fp4_encode': 15728640, 'fp4_decode': 15728640} |  N log2(N) butterfly add/subtract plus N output scale multiplies per row; CUDA sign/shuffle instructions not inferred. FP32 divide, quantized encode/decode, rescale multiply; one amax scale multiply per group. Bitwise exponent rounding, comparisons and format conversions are separate. |
| index_head_weight_scale | 30 | [64, 64] | 122,880 | {} |  |
| index_relu_weight_reduce | 30 | [64, 64, 2048] | 499,384,320 | {'relu_compare': 251658240} | Reference scores all rectangular columns before prefill masking. |
| index_topk | 30 | [64, 2048] | 0 | {'topk_rows': 1920, 'topk_candidates': 3932160} | Selection primitive; no assumed comparison algorithm. |

Attention normalization/rotary, compressor pooling and index scoring only. Sparse-attention online softmax is in sparse_kernel_summary, not this subtotal. Includes mathematical Hadamard butterfly/scale and quantize-dequantize arithmetic; excludes compiler-specific shuffle/sign instructions, frequency table construction, data movement and external sublayer norms. Special functions are not Tensor FLOPs.

稀疏注意力参考 kernel（固定 64-slot tile）：

| 项目 | 值 |
| --- | ---: |
| matrix_flops | 679,678,574,592 |
| effective_matrix_flops | 679,678,574,592 |
| online_softmax_scalar_flops | 3,917,840,384 |
| exp_ops | 337,559,552 |
| max_comparisons | 331,874,304 |
| gathered_kv_bytes | 2,654,994,432 |
| query_read_bytes | 511,705,088 |
| output_write_bytes | 511,705,088 |
| index_read_bytes | 10,371,072 |
| sink_read_bytes | 1,998,848 |
| source_declared_shared_bytes_per_cta | 344,064 |
| source_declared_fragment_bytes_per_cta | 297,728 |

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

- [configs/models/deepseek-v4-pro/config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json)，SHA256 `5fe4568daee51c208cb8a79538eaeda090ae011ade1dee2c386aa95f569c810e`。
- [configs/models/deepseek-v4-pro/inference/config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/config.json)，SHA256 `a6aded1806a2dbacbbab89bae2380d0422a6d0dcc55c946b421c7f5e06ef6094`。
- [sources/deepseek-v4-pro/inference/model.py](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/model.py)，SHA256 `ce962f1face79d4f633d36436576214057a7e11443c9789935e1deb5c6cd1d71`。
- [sources/deepseek-v4-pro/inference/kernel.py](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/inference/kernel.py)，SHA256 `59b325083d7103975cba025bd0d60ea343bb82d8fff53088afb7c04bd380c0c2`。
- [sources/fast-hadamard-transform/README.md](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/README.md)，SHA256 `e9d1a782e751104628590c481ba325bc436292254aaefe4cfa39ee3c0b1eb00e`。
- [sources/fast-hadamard-transform/csrc/fast_hadamard_transform_common.h](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/csrc/fast_hadamard_transform_common.h)，SHA256 `e51345eb6be7b43cb657d73b8db9b2debcb4060de2266c7b42fc45bb3b86b473`。
- [sources/fast-hadamard-transform/fast_hadamard_transform/fast_hadamard_transform_interface.py](https://raw.githubusercontent.com/Dao-AILab/fast-hadamard-transform/e7706faf8d1c3b9f241e36860640ad1dac644ede/fast_hadamard_transform/fast_hadamard_transform_interface.py)，SHA256 `a2f32a615b03c83d075fd49eba266c9f6c13df790cbe549db3bf8c0c1f3e8877`。
- [sources/deepseek-v4-pro/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model.safetensors.index.json)，SHA256 `a3a39b9ccb4e729851922fc9c770f5c5755e7b9d7e96cd02c23f0e12b5e25cb9`。
- [sources/deepseek-v4-pro/headers/model-00001-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00001-of-00064.safetensors?header=1)，SHA256 `f62844ce4c4d47bc40696a831380bb1464ae9717480bb30251ad05fe87b12fbd`。
- [sources/deepseek-v4-pro/headers/model-00002-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00002-of-00064.safetensors?header=1)，SHA256 `09c84dc7e7d800b1b7eda5f950488a4edde5058dece58842155a2d2c19d38dfa`。
- [sources/deepseek-v4-pro/headers/model-00003-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00003-of-00064.safetensors?header=1)，SHA256 `a0f61998df192ab90954d0a00a1ccf5166153a66899d6849741d09e38ab4f7a9`。
- [sources/deepseek-v4-pro/headers/model-00004-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00004-of-00064.safetensors?header=1)，SHA256 `5ad3452b1f4668d7917a18b085a8c5f2767100fd3f36ff7686061eaa810321a0`。
- [sources/deepseek-v4-pro/headers/model-00005-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00005-of-00064.safetensors?header=1)，SHA256 `9817aa67c797eb172e6c0ae9e84823ea54b04afb41e2e189c3cc7bedd547fff9`。
- [sources/deepseek-v4-pro/headers/model-00006-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00006-of-00064.safetensors?header=1)，SHA256 `f012bb8296655c4449c76cfb0c78b2e367c0706f5548a64c180a47f9e8835db1`。
- [sources/deepseek-v4-pro/headers/model-00007-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00007-of-00064.safetensors?header=1)，SHA256 `c48667932097f3843857a56a36870c2ba5a44149c47a8df7c76a4d0a9a7c0409`。
- [sources/deepseek-v4-pro/headers/model-00008-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00008-of-00064.safetensors?header=1)，SHA256 `366ab679ecbe8e4dcc8809e7caf6432f11329c84363da64eca6459073142226e`。
- [sources/deepseek-v4-pro/headers/model-00009-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00009-of-00064.safetensors?header=1)，SHA256 `972018fc9cfab2cefa9db1738e7dc52da0220d16552d944e8de9ff57b2f52e0a`。
- [sources/deepseek-v4-pro/headers/model-00010-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00010-of-00064.safetensors?header=1)，SHA256 `764ed6d21313964fe00dae095c6afe2d75565bf9fe3ecbf87e09e6d83d093e1f`。
- [sources/deepseek-v4-pro/headers/model-00011-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00011-of-00064.safetensors?header=1)，SHA256 `01db80934aa5584438318e4fdca952fb91afe58ad05d5332026d637cdc8db877`。
- [sources/deepseek-v4-pro/headers/model-00012-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00012-of-00064.safetensors?header=1)，SHA256 `773af1e79c9f0ec3d1505fa049e80b4ffb670796b4e024951a4f64fb1342bef7`。
- [sources/deepseek-v4-pro/headers/model-00013-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00013-of-00064.safetensors?header=1)，SHA256 `1c0343aa40c2392238fca1831246f13562779ddfde10d2ccf9a3a22ad701ddf6`。
- [sources/deepseek-v4-pro/headers/model-00014-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00014-of-00064.safetensors?header=1)，SHA256 `5eb8c0502dc4385719778971d965cca146f76b9348177b6207e8d252c353f171`。
- [sources/deepseek-v4-pro/headers/model-00015-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00015-of-00064.safetensors?header=1)，SHA256 `94a9511cae977b5916462e10f46fa6cdd7470414b407e6a9fc7f654d2da4e9d0`。
- [sources/deepseek-v4-pro/headers/model-00016-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00016-of-00064.safetensors?header=1)，SHA256 `893a168b5ff71d4dff9c88f6ba0a6419b2c4cfca1327faa8f475deb9b6c7784b`。
- [sources/deepseek-v4-pro/headers/model-00017-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00017-of-00064.safetensors?header=1)，SHA256 `c9368805fe734f1654f7e74f22070c19d13e5c3ce0d61d7563960252898725fc`。
- [sources/deepseek-v4-pro/headers/model-00018-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00018-of-00064.safetensors?header=1)，SHA256 `42b4f2cf60eebbbc77e9765e5f034bf4dacd83f7fcd81edaab18935123ec0aaa`。
- [sources/deepseek-v4-pro/headers/model-00019-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00019-of-00064.safetensors?header=1)，SHA256 `6c1ba9cd1ffd09fbbec7283b0b5830721eab9fb3048a56f70451cf4089fa6691`。
- [sources/deepseek-v4-pro/headers/model-00020-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00020-of-00064.safetensors?header=1)，SHA256 `00d744b2ef8dcf64083fbd4c1fa57d88a8beed492d2ad9feb0abb084c324514d`。
- [sources/deepseek-v4-pro/headers/model-00021-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00021-of-00064.safetensors?header=1)，SHA256 `08005b0a277f86b5d379be73d6c044e61e73a1cb748364487bd83eeae1f19b24`。
- [sources/deepseek-v4-pro/headers/model-00022-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00022-of-00064.safetensors?header=1)，SHA256 `2096dd2862f84ed281004ede6d700f8c422ac9f5f6708fa4e622e78c089a3360`。
- [sources/deepseek-v4-pro/headers/model-00023-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00023-of-00064.safetensors?header=1)，SHA256 `46a697dc52e865034ed8d910ede0f222900b3ea8c944a5cb500f72e939b04da3`。
- [sources/deepseek-v4-pro/headers/model-00024-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00024-of-00064.safetensors?header=1)，SHA256 `e2b9c7a6e404a9d741f6f134c5453b556ba2a1d7a7c24a2ac7d3ed89e1aa2d22`。
- [sources/deepseek-v4-pro/headers/model-00025-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00025-of-00064.safetensors?header=1)，SHA256 `5b301d2e50951f2cac98ffdcba8f251cd21ee06f9ee9b06c3a10281749b4a8e1`。
- [sources/deepseek-v4-pro/headers/model-00026-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00026-of-00064.safetensors?header=1)，SHA256 `8d971ac61f41bbb56bae9300470f8fd6a0353125b3408b287ead3b17677fce3b`。
- [sources/deepseek-v4-pro/headers/model-00027-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00027-of-00064.safetensors?header=1)，SHA256 `65ee01c2da71bd59d980cb77281ef274e7e28f39d5c3c6000355ed5d9f2d901d`。
- [sources/deepseek-v4-pro/headers/model-00028-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00028-of-00064.safetensors?header=1)，SHA256 `32873d82bb2169171ada203db4fb6e156baa38e43ee4dec54b2135f45bb46372`。
- [sources/deepseek-v4-pro/headers/model-00029-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00029-of-00064.safetensors?header=1)，SHA256 `6d896e9661a66563808d89ab2d175ca42ae4f454d12240fce5d01d6639f3b830`。
- [sources/deepseek-v4-pro/headers/model-00030-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00030-of-00064.safetensors?header=1)，SHA256 `7d37c8cb35b4491a885dd93f5af70ab7207cbab58a6395a1ec0e3acda6070245`。
- [sources/deepseek-v4-pro/headers/model-00031-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00031-of-00064.safetensors?header=1)，SHA256 `af3aa1bc6590a624d28dea59ff01851124e611b1f75d2bf93c82a533b999f063`。
- [sources/deepseek-v4-pro/headers/model-00032-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00032-of-00064.safetensors?header=1)，SHA256 `111af8344c0da52f7086873f06977dadf4f0a93f2d5a6ba694373dcf0bacb497`。
- [sources/deepseek-v4-pro/headers/model-00033-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00033-of-00064.safetensors?header=1)，SHA256 `2e27cd1549eb4cce96dd7a2d3c4326bc9b8369bf8ff3f0c0f502c1fd5981a751`。
- [sources/deepseek-v4-pro/headers/model-00034-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00034-of-00064.safetensors?header=1)，SHA256 `fde9380f0ac661c616d4ca856591ecf953f384d004c5e3e725b4acf098c09c39`。
- [sources/deepseek-v4-pro/headers/model-00035-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00035-of-00064.safetensors?header=1)，SHA256 `b444ab6670871e112d2f925a4037aec0fb48c236616b9861bde6da1b076b62a8`。
- [sources/deepseek-v4-pro/headers/model-00036-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00036-of-00064.safetensors?header=1)，SHA256 `260f19fd3091cf5f1e1e02627b21d0ed3699c815ac7645d0bc7f6878b2ec85a9`。
- [sources/deepseek-v4-pro/headers/model-00037-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00037-of-00064.safetensors?header=1)，SHA256 `ada278d9a5d040f4198791954d2120fa1234736a90082a5694ec920e638733c7`。
- [sources/deepseek-v4-pro/headers/model-00038-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00038-of-00064.safetensors?header=1)，SHA256 `20636aa9b7a63fbf8bc48536c668720ca283cd6fbef63a94b912ff0a93e683a9`。
- [sources/deepseek-v4-pro/headers/model-00039-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00039-of-00064.safetensors?header=1)，SHA256 `cdffc26189719dabd1301e040f1158a2d69ab5e88a7eb2247aa89c949f6f8437`。
- [sources/deepseek-v4-pro/headers/model-00040-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00040-of-00064.safetensors?header=1)，SHA256 `ae12150988f04ff7a3c64ad20742c0b2039eb2003d271833b9ecce22872e9d98`。
- [sources/deepseek-v4-pro/headers/model-00041-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00041-of-00064.safetensors?header=1)，SHA256 `4d1f15d8c4588f0735028cb6d2b9d308b9a8baf80e4a65d2565e53e71272decf`。
- [sources/deepseek-v4-pro/headers/model-00042-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00042-of-00064.safetensors?header=1)，SHA256 `78245a3e3a163146cb8640ee7249e43baacbd6b0c1294f7f0b86f2c3a2ee262a`。
- [sources/deepseek-v4-pro/headers/model-00043-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00043-of-00064.safetensors?header=1)，SHA256 `bcf24f2bd0eb8d597e3b3cca50941e34cc317b0a0aafeaa809941ba55ae65de4`。
- [sources/deepseek-v4-pro/headers/model-00044-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00044-of-00064.safetensors?header=1)，SHA256 `9a0112e1ab9bd7cc7989e71e65b33b541180697794cd8aa328694d94f9b5fa5c`。
- [sources/deepseek-v4-pro/headers/model-00045-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00045-of-00064.safetensors?header=1)，SHA256 `5024100086c9989a18c0d867643cb2058d954266686b979b0c1ca98132927830`。
- [sources/deepseek-v4-pro/headers/model-00046-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00046-of-00064.safetensors?header=1)，SHA256 `123e4096f27146b8d7209e1f78b808025ec238ee719147eb5c375914f199b1de`。
- [sources/deepseek-v4-pro/headers/model-00047-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00047-of-00064.safetensors?header=1)，SHA256 `f78fb5091fa057f1b09e034d0a66e5ca6c4ec444c0689d0928ff86247e7b3845`。
- [sources/deepseek-v4-pro/headers/model-00048-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00048-of-00064.safetensors?header=1)，SHA256 `ff75f7a6cbe6b0558a94a304d4470c840db4e9b69de4143d555c28a85dafc1ef`。
- [sources/deepseek-v4-pro/headers/model-00049-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00049-of-00064.safetensors?header=1)，SHA256 `f745de46aaea647f5b966cc61e6bf9f26643f7780b547f1206afa6b88b527cfd`。
- [sources/deepseek-v4-pro/headers/model-00050-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00050-of-00064.safetensors?header=1)，SHA256 `d4b43bcc44eccceebb30a8d07ba7ec1bf626771a49007bc7ac4407f4d9a82b3b`。
- [sources/deepseek-v4-pro/headers/model-00051-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00051-of-00064.safetensors?header=1)，SHA256 `d01cf662b54ab837ec7de7399d182f372d30bad1a1cf20a0e922918e662fc34c`。
- [sources/deepseek-v4-pro/headers/model-00052-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00052-of-00064.safetensors?header=1)，SHA256 `8fd10a263f7d795c5fdae4cef849153ab1f4fc5cbe08c4f6f46fb57592fcb557`。
- [sources/deepseek-v4-pro/headers/model-00053-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00053-of-00064.safetensors?header=1)，SHA256 `530bd227b6a95c4998bfe4539e32bbb68ca927487b2de154ff1d55f121402984`。
- [sources/deepseek-v4-pro/headers/model-00054-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00054-of-00064.safetensors?header=1)，SHA256 `377c88b1ddd5ed0d29dd5fc0e1dc801c003773dbb6ff4cee594ec5c3572a3cf8`。
- [sources/deepseek-v4-pro/headers/model-00055-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00055-of-00064.safetensors?header=1)，SHA256 `7f4fbfd6bd08895ae4f4f553af562e0977eb1ded070bb6fff6b585e54a5dced4`。
- [sources/deepseek-v4-pro/headers/model-00056-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00056-of-00064.safetensors?header=1)，SHA256 `ce3736415591d513968768ab86dd164333b4d0a1a6491b846c8af0fbc1573ede`。
- [sources/deepseek-v4-pro/headers/model-00057-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00057-of-00064.safetensors?header=1)，SHA256 `804da0c9349206088b99f94ea81b57845cca54d1eaeb30603675906d326f0e4b`。
- [sources/deepseek-v4-pro/headers/model-00058-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00058-of-00064.safetensors?header=1)，SHA256 `7ccc9e5f5419659d4baa12760c05fa1fb3da4fe9d581060b219b4124c84d509f`。
- [sources/deepseek-v4-pro/headers/model-00059-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00059-of-00064.safetensors?header=1)，SHA256 `e88377ef55fa69722cc08e7fc4720ce21e6c39000104bc7d05ce9e915391b87b`。
- [sources/deepseek-v4-pro/headers/model-00060-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00060-of-00064.safetensors?header=1)，SHA256 `1af641c19db47af20c62850890c45ed4daaeb2035d311c4866b253a4cf20d3d9`。
- [sources/deepseek-v4-pro/headers/model-00061-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00061-of-00064.safetensors?header=1)，SHA256 `e5e13b5c696c3f3c6306fde2be41f45111635ddb5f51bff597826f02ac59a78a`。
- [sources/deepseek-v4-pro/headers/model-00062-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00062-of-00064.safetensors?header=1)，SHA256 `7258653c3c98ca6615f76c0eda6d6283222424370e9dd58758d6b1e80e19d8e3`。
- [sources/deepseek-v4-pro/headers/model-00063-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00063-of-00064.safetensors?header=1)，SHA256 `711b38904bc397fca30cddf887b2c6581a48ffcf868fe258c3369af68147366f`。
- [sources/deepseek-v4-pro/headers/model-00064-of-00064.safetensors.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/b5968e9190ef611bbf34a7229255be88a0e937c1/model-00064-of-00064.safetensors?header=1)，SHA256 `14a863bf950f74e19fdcaa16ebbdc192e125e9a7972fbc3f6a9985d100a3a6bb`。
