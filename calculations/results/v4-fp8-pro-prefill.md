# v4-fp8-linear — deepseek-v4-pro

输入：`{"accumulator_dtype": "FP32", "batch": 1, "history": 0, "input_dtype": "BF16", "scale_dtype": "E8M0", "sparsity": "dense", "tokens": 8192, "weight_dtype": "FP8 E4M3", "world_size": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| valid_matrix_flops | 304,856,778,670,080 |
| padded_tile_matrix_flops | 304,856,778,670,080 |
| activation_quantization_scalar_flops | 25,392,021,504 |
| activation_abs_ops | 25,195,184,128 |
| activation_max_comparisons | 25,195,184,128 |
| activation_clamp_comparisons | 50,390,368,256 |
| activation_round_scale_calls | 196,837,376 |
| activation_fp8_cast_elements | 25,195,184,128 |
| activation_e8m0_cast_elements | 196,837,376 |
| scale_product_flops | 9,303,490,560 |
| scale_corrected_accumulation_flops | 2,381,693,583,360 |
| logical_scale_flops | 2,390,997,073,920 |
| padded_scale_flops | 2,390,997,073,920 |
| quantization_interface_bytes | 75,782,389,760 |
| gemm_interface_bytes | 136,039,945,280 |
| total_interface_bytes | 211,822,335,040 |
| resident_weight_bytes | 18,606,981,120 |
| resident_weight_scale_bytes | 1,135,680 |
| activation_fp8_bytes | 25,195,184,128 |
| activation_scale_bytes | 196,837,376 |
| output_bf16_bytes | 92,039,806,976 |
| linear_invocations | 457 |

| Linear | 调用数 | 权重shape | 有效矩阵FLOPs | tile矩阵FLOPs | scale FLOPs |
| --- | ---: | --- | ---: | ---: | ---: |
| wq_a | 61 | [1536, 7168] | 11003706212352 | 11003706212352 | 86302261248 |
| wq_b | 61 | [65536, 1536] | 100605313941504 | 100605313941504 | 789049245696 |
| wkv_shared | 61 | [512, 7168] | 3667902070784 | 3667902070784 | 28767420416 |
| wo_b | 61 | [7168, 16384] | 117372866265088 | 117372866265088 | 920557453312 |
| index_wq_b | 30 | [8192, 1536] | 6184752906240 | 6184752906240 | 48507125760 |
| shared_gate | 61 | [3072, 7168] | 22007412424704 | 22007412424704 | 172604522496 |
| shared_up | 61 | [3072, 7168] | 22007412424704 | 22007412424704 | 172604522496 |
| shared_down | 61 | [7168, 3072] | 22007412424704 | 22007412424704 | 172604522496 |

计量条件：

- Pinned model.py Linear dispatch, default dtype FP8 and ModelArgs.scale_dtype=fp8. Explicit FP32 compressors/router/head and BF16 grouped output/index weights projection are excluded; routed FP4 experts have their own ledger. MTP is excluded.
- Each shared gate/up/down and each selected attention projection calls act_quant separately. No cross-call input quantization reuse is assumed, even where w1 and w3 receive the same input.
- Valid matrix work already belongs to v4_forward: replace it with padded work for a tile comparison, never add both. Kernel tiles are 32 by 128 by 128, with FP8 inputs and FP32 accumulation; no structured sparsity.
- Scale_A times Scale_B costs one multiply per row/output-block/K-block; scale-corrected C uses multiply plus add per output cell/K-block. This is not three FLOPs per cell because Scale_C is shared over 128 columns.
- Quantization counts valid cells: absmax reduction K/128 groups of 128, clamp-min once per group, scale multiply and division, clamp and casts. Power-of-two bit manipulation is counted as fast_round_scale calls, not floating log/exp FLOPs. Padded quantization instructions and compiler effects are not claimed.
- API operand bytes sum act_quant BF16 read, FP8/scales write, then GEMM FP8/scales/weight read and BF16 output write. Intermediates appear once per interface. These are not physical HBM bytes; cache reuse, repeated tile loads, contiguous copies, workspace and tensor lifetimes remain separate.
- Resident weights/scales describe these reference Linear objects only, not complete checkpoint/runtime allocations. Contiguous BF16 input and single-device execution are explicit assumptions; no hardware time or executable model claim.

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
