# v4-fp8-linear — deepseek-v4-flash

输入：`{"accumulator_dtype": "FP32", "batch": 1, "history": 0, "input_dtype": "BF16", "scale_dtype": "E8M0", "sparsity": "dense", "tokens": 8192, "weight_dtype": "FP8 E4M3", "world_size": 1}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| valid_matrix_flops | 72,327,249,264,640 |
| padded_tile_matrix_flops | 72,327,249,264,640 |
| activation_quantization_scalar_flops | 9,992,798,208 |
| activation_abs_ops | 9,915,334,656 |
| activation_max_comparisons | 9,915,334,656 |
| activation_clamp_comparisons | 19,830,669,312 |
| activation_round_scale_calls | 77,463,552 |
| activation_fp8_cast_elements | 9,915,334,656 |
| activation_e8m0_cast_elements | 77,463,552 |
| scale_product_flops | 2,207,252,480 |
| scale_corrected_accumulation_flops | 565,056,634,880 |
| logical_scale_flops | 567,263,887,360 |
| padded_scale_flops | 567,263,887,360 |
| quantization_interface_bytes | 29,823,467,520 |
| gemm_interface_bytes | 50,050,768,000 |
| total_interface_bytes | 79,874,235,520 |
| resident_weight_bytes | 4,414,504,960 |
| resident_weight_scale_bytes | 269,440 |
| activation_fp8_bytes | 9,915,334,656 |
| activation_scale_bytes | 77,463,552 |
| output_bf16_bytes | 35,643,195,392 |
| linear_invocations | 322 |

| Linear | 调用数 | 权重shape | 有效矩阵FLOPs | tile矩阵FLOPs | scale FLOPs |
| --- | ---: | --- | ---: | ---: | ---: |
| wq_a | 43 | [1024, 4096] | 2954937499648 | 2954937499648 | 23175626752 |
| wq_b | 43 | [32768, 1024] | 23639499997184 | 23639499997184 | 185405014016 |
| wkv_shared | 43 | [512, 4096] | 1477468749824 | 1477468749824 | 11587813376 |
| wo_b | 43 | [4096, 8192] | 23639499997184 | 23639499997184 | 185405014016 |
| index_wq_b | 21 | [8192, 1024] | 2886218022912 | 2886218022912 | 22636658688 |
| shared_gate | 43 | [2048, 4096] | 5909874999296 | 5909874999296 | 46351253504 |
| shared_up | 43 | [2048, 4096] | 5909874999296 | 5909874999296 | 46351253504 |
| shared_down | 43 | [4096, 2048] | 5909874999296 | 5909874999296 | 46351253504 |

计量条件：

- Pinned model.py Linear dispatch, default dtype FP8 and ModelArgs.scale_dtype=fp8. Explicit FP32 compressors/router/head and BF16 grouped output/index weights projection are excluded; routed FP4 experts have their own ledger. MTP is excluded.
- Each shared gate/up/down and each selected attention projection calls act_quant separately. No cross-call input quantization reuse is assumed, even where w1 and w3 receive the same input.
- Valid matrix work already belongs to v4_forward: replace it with padded work for a tile comparison, never add both. Kernel tiles are 32 by 128 by 128, with FP8 inputs and FP32 accumulation; no structured sparsity.
- Scale_A times Scale_B costs one multiply per row/output-block/K-block; scale-corrected C uses multiply plus add per output cell/K-block. This is not three FLOPs per cell because Scale_C is shared over 128 columns.
- Quantization counts valid cells: absmax reduction K/128 groups of 128, clamp-min once per group, scale multiply and division, clamp and casts. Power-of-two bit manipulation is counted as fast_round_scale calls, not floating log/exp FLOPs. Padded quantization instructions and compiler effects are not claimed.
- API operand bytes sum act_quant BF16 read, FP8/scales write, then GEMM FP8/scales/weight read and BF16 output write. Intermediates appear once per interface. These are not physical HBM bytes; cache reuse, repeated tile loads, contiguous copies, workspace and tensor lifetimes remain separate.
- Resident weights/scales describe these reference Linear objects only, not complete checkpoint/runtime allocations. Contiguous BF16 input and single-device execution are explicit assumptions; no hardware time or executable model claim.

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
