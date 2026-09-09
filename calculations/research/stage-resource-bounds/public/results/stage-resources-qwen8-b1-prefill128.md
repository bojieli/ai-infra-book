# Serial-stage resource bounds

Conditional known-work service bounds; full runtime remains unknown.

| Field | Value |
|---|---|
| calculation | stage-resource-bounds |
| schema_version | 1 |
| scenario.model | qwen3-8b |
| scenario.device | h100-sxm |
| scenario.batch | 1 |
| scenario.tokens | 128 |
| scenario.history | 0 |
| scenario.routing | balanced |
| scenario.assumed_rates | {} |
| scenario.rate_multipliers | {} |
| scenario.stage_interface_bytes | unknown (null) |
| sources[0].file | configs/models/qwen3-8b/config.json |
| sources[0].url | https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json |
| sources[0].revision | b968826d9c46dd6066d109eabc6255188de91218 |
| sources[0].sha256 | f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30 |
| sources[1].file | sources/qwen3-8b/model.safetensors.index.json |
| sources[1].url | https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json |
| sources[1].revision | b968826d9c46dd6066d109eabc6255188de91218 |
| sources[1].sha256 | f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc |
| sources[2].file | sources/qwen3/modeling_qwen3.py |
| sources[2].url | https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py |
| sources[2].revision | 0720e206c6ba28887e4d60ef60a6a089f6c1cc76 |
| sources[2].sha256 | 704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2 |
| sources[3].file | sources/qwen3/modeling_qwen3_moe.py |
| sources[3].url | https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py |
| sources[3].revision | 0720e206c6ba28887e4d60ef60a6a089f6c1cc76 |
| sources[3].sha256 | 3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8 |
| sources[4].file | sources/hardware/nvidia-h100-page.html |
| sources[4].url | https://www.nvidia.com/en-us/data-center/h100/ |
| sources[4].revision | snapshot-2026-09-08 |
| sources[4].sha256 | 8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681 |
| sources[5].file | ../references/files/specs/nvidia-h100.pdf |
| sources[5].url | https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf |
| sources[5].revision | book-official-archive-2026-09-06 |
| sources[5].sha256 | 3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27 |
| sources[6].file | sources/hardware/nvidia-ptx-isa-9-3.html |
| sources[6].url | https://docs.nvidia.com/cuda/parallel-thread-execution/index.html |
| sources[6].revision | snapshot-2026-09-08 |
| sources[6].sha256 | 940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413 |
| sources[7].file | research/h05-next-review/cuda-programming-guide-12.8.1.html |
| sources[7].url | https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html |
| sources[7].revision | CUDA12.8.1 archive |
| sources[7].sha256 | cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce |
| device.id | h100-sxm |
| device.vendor | NVIDIA |
| device.memory.nominal_capacity | 80 |
| device.memory.capacity_unit | GB |
| device.memory.bandwidth_bytes_per_second | 3350000000000.0 |
| device.memory.source_id | nvidia-h100-page |
| device.memory.locator | Product Specifications, H100 SXM |
| device.memory.capacity_note | 厂商 GB 标签；不是运行时可分配 bytes。统一内存还由 CPU/OS 共享。 |
| stages[0].id | input |
| stages[0].work.vector_fp32 | 8192 |
| stages[0].work.interface_bytes | 2164992 |
| stages[0].work.special:sin | 16384 |
| stages[0].work.special:cos | 16384 |
| stages[0].operations[0].name | embedding |
| stages[0].operations[0].matrix_flops | 0 |
| stages[0].operations[0].input_precision | unknown (null) |
| stages[0].operations[0].accumulator_precision | unknown (null) |
| stages[0].operations[0].sparsity | unknown (null) |
| stages[0].operations[0].scalar_flops | 0 |
| stages[0].operations[0].special_ops | {} |
| stages[0].operations[0].source_detail.indices[0] | 1 |
| stages[0].operations[0].source_detail.indices[1] | 128 |
| stages[0].operations[0].source_detail.table[0] | 151936 |
| stages[0].operations[0].source_detail.table[1] | 4096 |
| stages[0].operations[0].source_detail.output[0] | 128 |
| stages[0].operations[0].source_detail.output[1] | 4096 |
| stages[0].operations[1].name | rope_table |
| stages[0].operations[1].matrix_flops | 0 |
| stages[0].operations[1].input_precision | unknown (null) |
| stages[0].operations[1].accumulator_precision | unknown (null) |
| stages[0].operations[1].sparsity | unknown (null) |
| stages[0].operations[1].scalar_flops | 8192 |
| stages[0].operations[1].special_ops.sin | 16384 |
| stages[0].operations[1].special_ops.cos | 16384 |
| stages[0].operations[1].source_detail.frequencies[0] | 128 |
| stages[0].operations[1].source_detail.frequencies[1] | 64 |
| stages[0].operations[1].source_detail.cos_sin_each[0] | 128 |
| stages[0].operations[1].source_detail.cos_sin_each[1] | 128 |
| stages[1].id | layer:0 |
| stages[1].work.vector_fp32 | 17179904 |
| stages[1].work.special:rsqrt | 5376 |
| stages[1].work.interface_bytes | 438387200 |
| stages[1].work.matrix_bf16 | 49527390208 |
| stages[1].work.special:negate | 1900544 |
| stages[1].work.special:exp | 1837056 |
| stages[1].work.special:compare_max | 260096 |
| stages[1].work.special:mask_decisions | 524288 |
| stages[1].operations[0].name | input_layernorm |
| stages[1].operations[0].matrix_flops | 0 |
| stages[1].operations[0].input_precision | unknown (null) |
| stages[1].operations[0].accumulator_precision | unknown (null) |
| stages[1].operations[0].sparsity | unknown (null) |
| stages[1].operations[0].scalar_flops | 2097280 |
| stages[1].operations[0].special_ops.rsqrt | 128 |
| stages[1].operations[0].source_detail.input[0] | 128 |
| stages[1].operations[0].source_detail.input[1] | 4096 |
| stages[1].operations[0].source_detail.weight[0] | 4096 |
| stages[1].operations[0].source_detail.output[0] | 128 |
| stages[1].operations[0].source_detail.output[1] | 4096 |
| stages[1].operations[1].name | q_proj |
| stages[1].operations[1].matrix_flops | 4294967296 |
| stages[1].operations[1].input_precision | BF16 |
| stages[1].operations[1].accumulator_precision | FP32 |
| stages[1].operations[1].sparsity | dense |
| stages[1].operations[1].scalar_flops | 0 |
| stages[1].operations[1].special_ops | {} |
| stages[1].operations[1].source_detail.input[0] | 128 |
| stages[1].operations[1].source_detail.input[1] | 4096 |
| stages[1].operations[1].source_detail.weight_math[0] | 4096 |
| stages[1].operations[1].source_detail.weight_math[1] | 4096 |
| stages[1].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[1].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[1].source_detail.output[0] | 128 |
| stages[1].operations[1].source_detail.output[1] | 4096 |
| stages[1].operations[2].name | k_proj |
| stages[1].operations[2].matrix_flops | 1073741824 |
| stages[1].operations[2].input_precision | BF16 |
| stages[1].operations[2].accumulator_precision | FP32 |
| stages[1].operations[2].sparsity | dense |
| stages[1].operations[2].scalar_flops | 0 |
| stages[1].operations[2].special_ops | {} |
| stages[1].operations[2].source_detail.input[0] | 128 |
| stages[1].operations[2].source_detail.input[1] | 4096 |
| stages[1].operations[2].source_detail.weight_math[0] | 4096 |
| stages[1].operations[2].source_detail.weight_math[1] | 1024 |
| stages[1].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[1].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[2].source_detail.output[0] | 128 |
| stages[1].operations[2].source_detail.output[1] | 1024 |
| stages[1].operations[3].name | v_proj |
| stages[1].operations[3].matrix_flops | 1073741824 |
| stages[1].operations[3].input_precision | BF16 |
| stages[1].operations[3].accumulator_precision | FP32 |
| stages[1].operations[3].sparsity | dense |
| stages[1].operations[3].scalar_flops | 0 |
| stages[1].operations[3].special_ops | {} |
| stages[1].operations[3].source_detail.input[0] | 128 |
| stages[1].operations[3].source_detail.input[1] | 4096 |
| stages[1].operations[3].source_detail.weight_math[0] | 4096 |
| stages[1].operations[3].source_detail.weight_math[1] | 1024 |
| stages[1].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[1].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[3].source_detail.output[0] | 128 |
| stages[1].operations[3].source_detail.output[1] | 1024 |
| stages[1].operations[4].name | q_norm |
| stages[1].operations[4].matrix_flops | 0 |
| stages[1].operations[4].input_precision | unknown (null) |
| stages[1].operations[4].accumulator_precision | unknown (null) |
| stages[1].operations[4].sparsity | unknown (null) |
| stages[1].operations[4].scalar_flops | 2101248 |
| stages[1].operations[4].special_ops.rsqrt | 4096 |
| stages[1].operations[4].source_detail.input[0] | 4096 |
| stages[1].operations[4].source_detail.input[1] | 128 |
| stages[1].operations[4].source_detail.weight[0] | 128 |
| stages[1].operations[4].source_detail.output[0] | 4096 |
| stages[1].operations[4].source_detail.output[1] | 128 |
| stages[1].operations[5].name | k_norm |
| stages[1].operations[5].matrix_flops | 0 |
| stages[1].operations[5].input_precision | unknown (null) |
| stages[1].operations[5].accumulator_precision | unknown (null) |
| stages[1].operations[5].sparsity | unknown (null) |
| stages[1].operations[5].scalar_flops | 525312 |
| stages[1].operations[5].special_ops.rsqrt | 1024 |
| stages[1].operations[5].source_detail.input[0] | 1024 |
| stages[1].operations[5].source_detail.input[1] | 128 |
| stages[1].operations[5].source_detail.weight[0] | 128 |
| stages[1].operations[5].source_detail.output[0] | 1024 |
| stages[1].operations[5].source_detail.output[1] | 128 |
| stages[1].operations[6].name | apply_rope |
| stages[1].operations[6].matrix_flops | 0 |
| stages[1].operations[6].input_precision | unknown (null) |
| stages[1].operations[6].accumulator_precision | unknown (null) |
| stages[1].operations[6].sparsity | unknown (null) |
| stages[1].operations[6].scalar_flops | 1966080 |
| stages[1].operations[6].special_ops.negate | 327680 |
| stages[1].operations[6].source_detail.Q[0] | 1 |
| stages[1].operations[6].source_detail.Q[1] | 32 |
| stages[1].operations[6].source_detail.Q[2] | 128 |
| stages[1].operations[6].source_detail.Q[3] | 128 |
| stages[1].operations[6].source_detail.K[0] | 1 |
| stages[1].operations[6].source_detail.K[1] | 8 |
| stages[1].operations[6].source_detail.K[2] | 128 |
| stages[1].operations[6].source_detail.K[3] | 128 |
| stages[1].operations[7].name | kv_append |
| stages[1].operations[7].matrix_flops | 0 |
| stages[1].operations[7].input_precision | unknown (null) |
| stages[1].operations[7].accumulator_precision | unknown (null) |
| stages[1].operations[7].sparsity | unknown (null) |
| stages[1].operations[7].scalar_flops | 0 |
| stages[1].operations[7].special_ops | {} |
| stages[1].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[1].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[1].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[1].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[1].operations[8].name | qk |
| stages[1].operations[8].matrix_flops | 67633152 |
| stages[1].operations[8].input_precision | BF16 |
| stages[1].operations[8].accumulator_precision | FP32 |
| stages[1].operations[8].sparsity | dense |
| stages[1].operations[8].scalar_flops | 0 |
| stages[1].operations[8].special_ops | {} |
| stages[1].operations[8].source_detail.Q[0] | 1 |
| stages[1].operations[8].source_detail.Q[1] | 32 |
| stages[1].operations[8].source_detail.Q[2] | 128 |
| stages[1].operations[8].source_detail.Q[3] | 128 |
| stages[1].operations[8].source_detail.K_shared[0] | 1 |
| stages[1].operations[8].source_detail.K_shared[1] | 8 |
| stages[1].operations[8].source_detail.K_shared[2] | 128 |
| stages[1].operations[8].source_detail.K_shared[3] | 128 |
| stages[1].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[1].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[1].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[1].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[1].operations[9].name | score_scale_mask_softmax |
| stages[1].operations[9].matrix_flops | 0 |
| stages[1].operations[9].input_precision | unknown (null) |
| stages[1].operations[9].accumulator_precision | unknown (null) |
| stages[1].operations[9].sparsity | unknown (null) |
| stages[1].operations[9].scalar_flops | 1052672 |
| stages[1].operations[9].special_ops.exp | 264192 |
| stages[1].operations[9].special_ops.compare_max | 260096 |
| stages[1].operations[9].special_ops.mask_decisions | 524288 |
| stages[1].operations[9].source_detail.scores[0] | 1 |
| stages[1].operations[9].source_detail.scores[1] | 32 |
| stages[1].operations[9].source_detail.scores[2] | 128 |
| stages[1].operations[9].source_detail.scores[3] | 128 |
| stages[1].operations[10].name | pv |
| stages[1].operations[10].matrix_flops | 67633152 |
| stages[1].operations[10].input_precision | BF16 |
| stages[1].operations[10].accumulator_precision | FP32 |
| stages[1].operations[10].sparsity | dense |
| stages[1].operations[10].scalar_flops | 0 |
| stages[1].operations[10].special_ops | {} |
| stages[1].operations[10].source_detail.P[0] | 1 |
| stages[1].operations[10].source_detail.P[1] | 32 |
| stages[1].operations[10].source_detail.P[2] | 128 |
| stages[1].operations[10].source_detail.P[3] | 128 |
| stages[1].operations[10].source_detail.V_shared[0] | 1 |
| stages[1].operations[10].source_detail.V_shared[1] | 8 |
| stages[1].operations[10].source_detail.V_shared[2] | 128 |
| stages[1].operations[10].source_detail.V_shared[3] | 128 |
| stages[1].operations[10].source_detail.output[0] | 1 |
| stages[1].operations[10].source_detail.output[1] | 32 |
| stages[1].operations[10].source_detail.output[2] | 128 |
| stages[1].operations[10].source_detail.output[3] | 128 |
| stages[1].operations[11].name | o_proj |
| stages[1].operations[11].matrix_flops | 4294967296 |
| stages[1].operations[11].input_precision | BF16 |
| stages[1].operations[11].accumulator_precision | FP32 |
| stages[1].operations[11].sparsity | dense |
| stages[1].operations[11].scalar_flops | 0 |
| stages[1].operations[11].special_ops | {} |
| stages[1].operations[11].source_detail.input[0] | 128 |
| stages[1].operations[11].source_detail.input[1] | 4096 |
| stages[1].operations[11].source_detail.weight_math[0] | 4096 |
| stages[1].operations[11].source_detail.weight_math[1] | 4096 |
| stages[1].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[1].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[11].source_detail.output[0] | 128 |
| stages[1].operations[11].source_detail.output[1] | 4096 |
| stages[1].operations[12].name | attention_residual |
| stages[1].operations[12].matrix_flops | 0 |
| stages[1].operations[12].input_precision | unknown (null) |
| stages[1].operations[12].accumulator_precision | unknown (null) |
| stages[1].operations[12].sparsity | unknown (null) |
| stages[1].operations[12].scalar_flops | 524288 |
| stages[1].operations[12].special_ops | {} |
| stages[1].operations[12].source_detail.inputs_each[0] | 128 |
| stages[1].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[1].operations[12].source_detail.output[0] | 128 |
| stages[1].operations[12].source_detail.output[1] | 4096 |
| stages[1].operations[13].name | post_attention_layernorm |
| stages[1].operations[13].matrix_flops | 0 |
| stages[1].operations[13].input_precision | unknown (null) |
| stages[1].operations[13].accumulator_precision | unknown (null) |
| stages[1].operations[13].sparsity | unknown (null) |
| stages[1].operations[13].scalar_flops | 2097280 |
| stages[1].operations[13].special_ops.rsqrt | 128 |
| stages[1].operations[13].source_detail.input[0] | 128 |
| stages[1].operations[13].source_detail.input[1] | 4096 |
| stages[1].operations[13].source_detail.weight[0] | 4096 |
| stages[1].operations[13].source_detail.output[0] | 128 |
| stages[1].operations[13].source_detail.output[1] | 4096 |
| stages[1].operations[14].name | gate_proj |
| stages[1].operations[14].matrix_flops | 12884901888 |
| stages[1].operations[14].input_precision | BF16 |
| stages[1].operations[14].accumulator_precision | FP32 |
| stages[1].operations[14].sparsity | dense |
| stages[1].operations[14].scalar_flops | 0 |
| stages[1].operations[14].special_ops | {} |
| stages[1].operations[14].source_detail.input[0] | 128 |
| stages[1].operations[14].source_detail.input[1] | 4096 |
| stages[1].operations[14].source_detail.weight_math[0] | 4096 |
| stages[1].operations[14].source_detail.weight_math[1] | 12288 |
| stages[1].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[1].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[14].source_detail.output[0] | 128 |
| stages[1].operations[14].source_detail.output[1] | 12288 |
| stages[1].operations[15].name | up_proj |
| stages[1].operations[15].matrix_flops | 12884901888 |
| stages[1].operations[15].input_precision | BF16 |
| stages[1].operations[15].accumulator_precision | FP32 |
| stages[1].operations[15].sparsity | dense |
| stages[1].operations[15].scalar_flops | 0 |
| stages[1].operations[15].special_ops | {} |
| stages[1].operations[15].source_detail.input[0] | 128 |
| stages[1].operations[15].source_detail.input[1] | 4096 |
| stages[1].operations[15].source_detail.weight_math[0] | 4096 |
| stages[1].operations[15].source_detail.weight_math[1] | 12288 |
| stages[1].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[1].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[1].operations[15].source_detail.output[0] | 128 |
| stages[1].operations[15].source_detail.output[1] | 12288 |
| stages[1].operations[16].name | silu_mul |
| stages[1].operations[16].matrix_flops | 0 |
| stages[1].operations[16].input_precision | unknown (null) |
| stages[1].operations[16].accumulator_precision | unknown (null) |
| stages[1].operations[16].sparsity | unknown (null) |
| stages[1].operations[16].scalar_flops | 6291456 |
| stages[1].operations[16].special_ops.exp | 1572864 |
| stages[1].operations[16].special_ops.negate | 1572864 |
| stages[1].operations[16].source_detail.gate[0] | 128 |
| stages[1].operations[16].source_detail.gate[1] | 12288 |
| stages[1].operations[16].source_detail.up[0] | 128 |
| stages[1].operations[16].source_detail.up[1] | 12288 |
| stages[1].operations[16].source_detail.output[0] | 128 |
| stages[1].operations[16].source_detail.output[1] | 12288 |
| stages[1].operations[17].name | down_proj |
| stages[1].operations[17].matrix_flops | 12884901888 |
| stages[1].operations[17].input_precision | BF16 |
| stages[1].operations[17].accumulator_precision | FP32 |
| stages[1].operations[17].sparsity | dense |
| stages[1].operations[17].scalar_flops | 0 |
| stages[1].operations[17].special_ops | {} |
| stages[1].operations[17].source_detail.input[0] | 128 |
| stages[1].operations[17].source_detail.input[1] | 12288 |
| stages[1].operations[17].source_detail.weight_math[0] | 12288 |
| stages[1].operations[17].source_detail.weight_math[1] | 4096 |
| stages[1].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[1].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[1].operations[17].source_detail.output[0] | 128 |
| stages[1].operations[17].source_detail.output[1] | 4096 |
| stages[1].operations[18].name | ffn_residual |
| stages[1].operations[18].matrix_flops | 0 |
| stages[1].operations[18].input_precision | unknown (null) |
| stages[1].operations[18].accumulator_precision | unknown (null) |
| stages[1].operations[18].sparsity | unknown (null) |
| stages[1].operations[18].scalar_flops | 524288 |
| stages[1].operations[18].special_ops | {} |
| stages[1].operations[18].source_detail.inputs_each[0] | 128 |
| stages[1].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[1].operations[18].source_detail.output[0] | 128 |
| stages[1].operations[18].source_detail.output[1] | 4096 |
| stages[2].id | layer:1 |
| stages[2].work.vector_fp32 | 17179904 |
| stages[2].work.special:rsqrt | 5376 |
| stages[2].work.interface_bytes | 438387200 |
| stages[2].work.matrix_bf16 | 49527390208 |
| stages[2].work.special:negate | 1900544 |
| stages[2].work.special:exp | 1837056 |
| stages[2].work.special:compare_max | 260096 |
| stages[2].work.special:mask_decisions | 524288 |
| stages[2].operations[0].name | input_layernorm |
| stages[2].operations[0].matrix_flops | 0 |
| stages[2].operations[0].input_precision | unknown (null) |
| stages[2].operations[0].accumulator_precision | unknown (null) |
| stages[2].operations[0].sparsity | unknown (null) |
| stages[2].operations[0].scalar_flops | 2097280 |
| stages[2].operations[0].special_ops.rsqrt | 128 |
| stages[2].operations[0].source_detail.input[0] | 128 |
| stages[2].operations[0].source_detail.input[1] | 4096 |
| stages[2].operations[0].source_detail.weight[0] | 4096 |
| stages[2].operations[0].source_detail.output[0] | 128 |
| stages[2].operations[0].source_detail.output[1] | 4096 |
| stages[2].operations[1].name | q_proj |
| stages[2].operations[1].matrix_flops | 4294967296 |
| stages[2].operations[1].input_precision | BF16 |
| stages[2].operations[1].accumulator_precision | FP32 |
| stages[2].operations[1].sparsity | dense |
| stages[2].operations[1].scalar_flops | 0 |
| stages[2].operations[1].special_ops | {} |
| stages[2].operations[1].source_detail.input[0] | 128 |
| stages[2].operations[1].source_detail.input[1] | 4096 |
| stages[2].operations[1].source_detail.weight_math[0] | 4096 |
| stages[2].operations[1].source_detail.weight_math[1] | 4096 |
| stages[2].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[2].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[1].source_detail.output[0] | 128 |
| stages[2].operations[1].source_detail.output[1] | 4096 |
| stages[2].operations[2].name | k_proj |
| stages[2].operations[2].matrix_flops | 1073741824 |
| stages[2].operations[2].input_precision | BF16 |
| stages[2].operations[2].accumulator_precision | FP32 |
| stages[2].operations[2].sparsity | dense |
| stages[2].operations[2].scalar_flops | 0 |
| stages[2].operations[2].special_ops | {} |
| stages[2].operations[2].source_detail.input[0] | 128 |
| stages[2].operations[2].source_detail.input[1] | 4096 |
| stages[2].operations[2].source_detail.weight_math[0] | 4096 |
| stages[2].operations[2].source_detail.weight_math[1] | 1024 |
| stages[2].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[2].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[2].source_detail.output[0] | 128 |
| stages[2].operations[2].source_detail.output[1] | 1024 |
| stages[2].operations[3].name | v_proj |
| stages[2].operations[3].matrix_flops | 1073741824 |
| stages[2].operations[3].input_precision | BF16 |
| stages[2].operations[3].accumulator_precision | FP32 |
| stages[2].operations[3].sparsity | dense |
| stages[2].operations[3].scalar_flops | 0 |
| stages[2].operations[3].special_ops | {} |
| stages[2].operations[3].source_detail.input[0] | 128 |
| stages[2].operations[3].source_detail.input[1] | 4096 |
| stages[2].operations[3].source_detail.weight_math[0] | 4096 |
| stages[2].operations[3].source_detail.weight_math[1] | 1024 |
| stages[2].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[2].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[3].source_detail.output[0] | 128 |
| stages[2].operations[3].source_detail.output[1] | 1024 |
| stages[2].operations[4].name | q_norm |
| stages[2].operations[4].matrix_flops | 0 |
| stages[2].operations[4].input_precision | unknown (null) |
| stages[2].operations[4].accumulator_precision | unknown (null) |
| stages[2].operations[4].sparsity | unknown (null) |
| stages[2].operations[4].scalar_flops | 2101248 |
| stages[2].operations[4].special_ops.rsqrt | 4096 |
| stages[2].operations[4].source_detail.input[0] | 4096 |
| stages[2].operations[4].source_detail.input[1] | 128 |
| stages[2].operations[4].source_detail.weight[0] | 128 |
| stages[2].operations[4].source_detail.output[0] | 4096 |
| stages[2].operations[4].source_detail.output[1] | 128 |
| stages[2].operations[5].name | k_norm |
| stages[2].operations[5].matrix_flops | 0 |
| stages[2].operations[5].input_precision | unknown (null) |
| stages[2].operations[5].accumulator_precision | unknown (null) |
| stages[2].operations[5].sparsity | unknown (null) |
| stages[2].operations[5].scalar_flops | 525312 |
| stages[2].operations[5].special_ops.rsqrt | 1024 |
| stages[2].operations[5].source_detail.input[0] | 1024 |
| stages[2].operations[5].source_detail.input[1] | 128 |
| stages[2].operations[5].source_detail.weight[0] | 128 |
| stages[2].operations[5].source_detail.output[0] | 1024 |
| stages[2].operations[5].source_detail.output[1] | 128 |
| stages[2].operations[6].name | apply_rope |
| stages[2].operations[6].matrix_flops | 0 |
| stages[2].operations[6].input_precision | unknown (null) |
| stages[2].operations[6].accumulator_precision | unknown (null) |
| stages[2].operations[6].sparsity | unknown (null) |
| stages[2].operations[6].scalar_flops | 1966080 |
| stages[2].operations[6].special_ops.negate | 327680 |
| stages[2].operations[6].source_detail.Q[0] | 1 |
| stages[2].operations[6].source_detail.Q[1] | 32 |
| stages[2].operations[6].source_detail.Q[2] | 128 |
| stages[2].operations[6].source_detail.Q[3] | 128 |
| stages[2].operations[6].source_detail.K[0] | 1 |
| stages[2].operations[6].source_detail.K[1] | 8 |
| stages[2].operations[6].source_detail.K[2] | 128 |
| stages[2].operations[6].source_detail.K[3] | 128 |
| stages[2].operations[7].name | kv_append |
| stages[2].operations[7].matrix_flops | 0 |
| stages[2].operations[7].input_precision | unknown (null) |
| stages[2].operations[7].accumulator_precision | unknown (null) |
| stages[2].operations[7].sparsity | unknown (null) |
| stages[2].operations[7].scalar_flops | 0 |
| stages[2].operations[7].special_ops | {} |
| stages[2].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[2].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[2].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[2].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[2].operations[8].name | qk |
| stages[2].operations[8].matrix_flops | 67633152 |
| stages[2].operations[8].input_precision | BF16 |
| stages[2].operations[8].accumulator_precision | FP32 |
| stages[2].operations[8].sparsity | dense |
| stages[2].operations[8].scalar_flops | 0 |
| stages[2].operations[8].special_ops | {} |
| stages[2].operations[8].source_detail.Q[0] | 1 |
| stages[2].operations[8].source_detail.Q[1] | 32 |
| stages[2].operations[8].source_detail.Q[2] | 128 |
| stages[2].operations[8].source_detail.Q[3] | 128 |
| stages[2].operations[8].source_detail.K_shared[0] | 1 |
| stages[2].operations[8].source_detail.K_shared[1] | 8 |
| stages[2].operations[8].source_detail.K_shared[2] | 128 |
| stages[2].operations[8].source_detail.K_shared[3] | 128 |
| stages[2].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[2].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[2].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[2].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[2].operations[9].name | score_scale_mask_softmax |
| stages[2].operations[9].matrix_flops | 0 |
| stages[2].operations[9].input_precision | unknown (null) |
| stages[2].operations[9].accumulator_precision | unknown (null) |
| stages[2].operations[9].sparsity | unknown (null) |
| stages[2].operations[9].scalar_flops | 1052672 |
| stages[2].operations[9].special_ops.exp | 264192 |
| stages[2].operations[9].special_ops.compare_max | 260096 |
| stages[2].operations[9].special_ops.mask_decisions | 524288 |
| stages[2].operations[9].source_detail.scores[0] | 1 |
| stages[2].operations[9].source_detail.scores[1] | 32 |
| stages[2].operations[9].source_detail.scores[2] | 128 |
| stages[2].operations[9].source_detail.scores[3] | 128 |
| stages[2].operations[10].name | pv |
| stages[2].operations[10].matrix_flops | 67633152 |
| stages[2].operations[10].input_precision | BF16 |
| stages[2].operations[10].accumulator_precision | FP32 |
| stages[2].operations[10].sparsity | dense |
| stages[2].operations[10].scalar_flops | 0 |
| stages[2].operations[10].special_ops | {} |
| stages[2].operations[10].source_detail.P[0] | 1 |
| stages[2].operations[10].source_detail.P[1] | 32 |
| stages[2].operations[10].source_detail.P[2] | 128 |
| stages[2].operations[10].source_detail.P[3] | 128 |
| stages[2].operations[10].source_detail.V_shared[0] | 1 |
| stages[2].operations[10].source_detail.V_shared[1] | 8 |
| stages[2].operations[10].source_detail.V_shared[2] | 128 |
| stages[2].operations[10].source_detail.V_shared[3] | 128 |
| stages[2].operations[10].source_detail.output[0] | 1 |
| stages[2].operations[10].source_detail.output[1] | 32 |
| stages[2].operations[10].source_detail.output[2] | 128 |
| stages[2].operations[10].source_detail.output[3] | 128 |
| stages[2].operations[11].name | o_proj |
| stages[2].operations[11].matrix_flops | 4294967296 |
| stages[2].operations[11].input_precision | BF16 |
| stages[2].operations[11].accumulator_precision | FP32 |
| stages[2].operations[11].sparsity | dense |
| stages[2].operations[11].scalar_flops | 0 |
| stages[2].operations[11].special_ops | {} |
| stages[2].operations[11].source_detail.input[0] | 128 |
| stages[2].operations[11].source_detail.input[1] | 4096 |
| stages[2].operations[11].source_detail.weight_math[0] | 4096 |
| stages[2].operations[11].source_detail.weight_math[1] | 4096 |
| stages[2].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[2].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[11].source_detail.output[0] | 128 |
| stages[2].operations[11].source_detail.output[1] | 4096 |
| stages[2].operations[12].name | attention_residual |
| stages[2].operations[12].matrix_flops | 0 |
| stages[2].operations[12].input_precision | unknown (null) |
| stages[2].operations[12].accumulator_precision | unknown (null) |
| stages[2].operations[12].sparsity | unknown (null) |
| stages[2].operations[12].scalar_flops | 524288 |
| stages[2].operations[12].special_ops | {} |
| stages[2].operations[12].source_detail.inputs_each[0] | 128 |
| stages[2].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[2].operations[12].source_detail.output[0] | 128 |
| stages[2].operations[12].source_detail.output[1] | 4096 |
| stages[2].operations[13].name | post_attention_layernorm |
| stages[2].operations[13].matrix_flops | 0 |
| stages[2].operations[13].input_precision | unknown (null) |
| stages[2].operations[13].accumulator_precision | unknown (null) |
| stages[2].operations[13].sparsity | unknown (null) |
| stages[2].operations[13].scalar_flops | 2097280 |
| stages[2].operations[13].special_ops.rsqrt | 128 |
| stages[2].operations[13].source_detail.input[0] | 128 |
| stages[2].operations[13].source_detail.input[1] | 4096 |
| stages[2].operations[13].source_detail.weight[0] | 4096 |
| stages[2].operations[13].source_detail.output[0] | 128 |
| stages[2].operations[13].source_detail.output[1] | 4096 |
| stages[2].operations[14].name | gate_proj |
| stages[2].operations[14].matrix_flops | 12884901888 |
| stages[2].operations[14].input_precision | BF16 |
| stages[2].operations[14].accumulator_precision | FP32 |
| stages[2].operations[14].sparsity | dense |
| stages[2].operations[14].scalar_flops | 0 |
| stages[2].operations[14].special_ops | {} |
| stages[2].operations[14].source_detail.input[0] | 128 |
| stages[2].operations[14].source_detail.input[1] | 4096 |
| stages[2].operations[14].source_detail.weight_math[0] | 4096 |
| stages[2].operations[14].source_detail.weight_math[1] | 12288 |
| stages[2].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[2].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[14].source_detail.output[0] | 128 |
| stages[2].operations[14].source_detail.output[1] | 12288 |
| stages[2].operations[15].name | up_proj |
| stages[2].operations[15].matrix_flops | 12884901888 |
| stages[2].operations[15].input_precision | BF16 |
| stages[2].operations[15].accumulator_precision | FP32 |
| stages[2].operations[15].sparsity | dense |
| stages[2].operations[15].scalar_flops | 0 |
| stages[2].operations[15].special_ops | {} |
| stages[2].operations[15].source_detail.input[0] | 128 |
| stages[2].operations[15].source_detail.input[1] | 4096 |
| stages[2].operations[15].source_detail.weight_math[0] | 4096 |
| stages[2].operations[15].source_detail.weight_math[1] | 12288 |
| stages[2].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[2].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[2].operations[15].source_detail.output[0] | 128 |
| stages[2].operations[15].source_detail.output[1] | 12288 |
| stages[2].operations[16].name | silu_mul |
| stages[2].operations[16].matrix_flops | 0 |
| stages[2].operations[16].input_precision | unknown (null) |
| stages[2].operations[16].accumulator_precision | unknown (null) |
| stages[2].operations[16].sparsity | unknown (null) |
| stages[2].operations[16].scalar_flops | 6291456 |
| stages[2].operations[16].special_ops.exp | 1572864 |
| stages[2].operations[16].special_ops.negate | 1572864 |
| stages[2].operations[16].source_detail.gate[0] | 128 |
| stages[2].operations[16].source_detail.gate[1] | 12288 |
| stages[2].operations[16].source_detail.up[0] | 128 |
| stages[2].operations[16].source_detail.up[1] | 12288 |
| stages[2].operations[16].source_detail.output[0] | 128 |
| stages[2].operations[16].source_detail.output[1] | 12288 |
| stages[2].operations[17].name | down_proj |
| stages[2].operations[17].matrix_flops | 12884901888 |
| stages[2].operations[17].input_precision | BF16 |
| stages[2].operations[17].accumulator_precision | FP32 |
| stages[2].operations[17].sparsity | dense |
| stages[2].operations[17].scalar_flops | 0 |
| stages[2].operations[17].special_ops | {} |
| stages[2].operations[17].source_detail.input[0] | 128 |
| stages[2].operations[17].source_detail.input[1] | 12288 |
| stages[2].operations[17].source_detail.weight_math[0] | 12288 |
| stages[2].operations[17].source_detail.weight_math[1] | 4096 |
| stages[2].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[2].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[2].operations[17].source_detail.output[0] | 128 |
| stages[2].operations[17].source_detail.output[1] | 4096 |
| stages[2].operations[18].name | ffn_residual |
| stages[2].operations[18].matrix_flops | 0 |
| stages[2].operations[18].input_precision | unknown (null) |
| stages[2].operations[18].accumulator_precision | unknown (null) |
| stages[2].operations[18].sparsity | unknown (null) |
| stages[2].operations[18].scalar_flops | 524288 |
| stages[2].operations[18].special_ops | {} |
| stages[2].operations[18].source_detail.inputs_each[0] | 128 |
| stages[2].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[2].operations[18].source_detail.output[0] | 128 |
| stages[2].operations[18].source_detail.output[1] | 4096 |
| stages[3].id | layer:2 |
| stages[3].work.vector_fp32 | 17179904 |
| stages[3].work.special:rsqrt | 5376 |
| stages[3].work.interface_bytes | 438387200 |
| stages[3].work.matrix_bf16 | 49527390208 |
| stages[3].work.special:negate | 1900544 |
| stages[3].work.special:exp | 1837056 |
| stages[3].work.special:compare_max | 260096 |
| stages[3].work.special:mask_decisions | 524288 |
| stages[3].operations[0].name | input_layernorm |
| stages[3].operations[0].matrix_flops | 0 |
| stages[3].operations[0].input_precision | unknown (null) |
| stages[3].operations[0].accumulator_precision | unknown (null) |
| stages[3].operations[0].sparsity | unknown (null) |
| stages[3].operations[0].scalar_flops | 2097280 |
| stages[3].operations[0].special_ops.rsqrt | 128 |
| stages[3].operations[0].source_detail.input[0] | 128 |
| stages[3].operations[0].source_detail.input[1] | 4096 |
| stages[3].operations[0].source_detail.weight[0] | 4096 |
| stages[3].operations[0].source_detail.output[0] | 128 |
| stages[3].operations[0].source_detail.output[1] | 4096 |
| stages[3].operations[1].name | q_proj |
| stages[3].operations[1].matrix_flops | 4294967296 |
| stages[3].operations[1].input_precision | BF16 |
| stages[3].operations[1].accumulator_precision | FP32 |
| stages[3].operations[1].sparsity | dense |
| stages[3].operations[1].scalar_flops | 0 |
| stages[3].operations[1].special_ops | {} |
| stages[3].operations[1].source_detail.input[0] | 128 |
| stages[3].operations[1].source_detail.input[1] | 4096 |
| stages[3].operations[1].source_detail.weight_math[0] | 4096 |
| stages[3].operations[1].source_detail.weight_math[1] | 4096 |
| stages[3].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[3].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[1].source_detail.output[0] | 128 |
| stages[3].operations[1].source_detail.output[1] | 4096 |
| stages[3].operations[2].name | k_proj |
| stages[3].operations[2].matrix_flops | 1073741824 |
| stages[3].operations[2].input_precision | BF16 |
| stages[3].operations[2].accumulator_precision | FP32 |
| stages[3].operations[2].sparsity | dense |
| stages[3].operations[2].scalar_flops | 0 |
| stages[3].operations[2].special_ops | {} |
| stages[3].operations[2].source_detail.input[0] | 128 |
| stages[3].operations[2].source_detail.input[1] | 4096 |
| stages[3].operations[2].source_detail.weight_math[0] | 4096 |
| stages[3].operations[2].source_detail.weight_math[1] | 1024 |
| stages[3].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[3].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[2].source_detail.output[0] | 128 |
| stages[3].operations[2].source_detail.output[1] | 1024 |
| stages[3].operations[3].name | v_proj |
| stages[3].operations[3].matrix_flops | 1073741824 |
| stages[3].operations[3].input_precision | BF16 |
| stages[3].operations[3].accumulator_precision | FP32 |
| stages[3].operations[3].sparsity | dense |
| stages[3].operations[3].scalar_flops | 0 |
| stages[3].operations[3].special_ops | {} |
| stages[3].operations[3].source_detail.input[0] | 128 |
| stages[3].operations[3].source_detail.input[1] | 4096 |
| stages[3].operations[3].source_detail.weight_math[0] | 4096 |
| stages[3].operations[3].source_detail.weight_math[1] | 1024 |
| stages[3].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[3].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[3].source_detail.output[0] | 128 |
| stages[3].operations[3].source_detail.output[1] | 1024 |
| stages[3].operations[4].name | q_norm |
| stages[3].operations[4].matrix_flops | 0 |
| stages[3].operations[4].input_precision | unknown (null) |
| stages[3].operations[4].accumulator_precision | unknown (null) |
| stages[3].operations[4].sparsity | unknown (null) |
| stages[3].operations[4].scalar_flops | 2101248 |
| stages[3].operations[4].special_ops.rsqrt | 4096 |
| stages[3].operations[4].source_detail.input[0] | 4096 |
| stages[3].operations[4].source_detail.input[1] | 128 |
| stages[3].operations[4].source_detail.weight[0] | 128 |
| stages[3].operations[4].source_detail.output[0] | 4096 |
| stages[3].operations[4].source_detail.output[1] | 128 |
| stages[3].operations[5].name | k_norm |
| stages[3].operations[5].matrix_flops | 0 |
| stages[3].operations[5].input_precision | unknown (null) |
| stages[3].operations[5].accumulator_precision | unknown (null) |
| stages[3].operations[5].sparsity | unknown (null) |
| stages[3].operations[5].scalar_flops | 525312 |
| stages[3].operations[5].special_ops.rsqrt | 1024 |
| stages[3].operations[5].source_detail.input[0] | 1024 |
| stages[3].operations[5].source_detail.input[1] | 128 |
| stages[3].operations[5].source_detail.weight[0] | 128 |
| stages[3].operations[5].source_detail.output[0] | 1024 |
| stages[3].operations[5].source_detail.output[1] | 128 |
| stages[3].operations[6].name | apply_rope |
| stages[3].operations[6].matrix_flops | 0 |
| stages[3].operations[6].input_precision | unknown (null) |
| stages[3].operations[6].accumulator_precision | unknown (null) |
| stages[3].operations[6].sparsity | unknown (null) |
| stages[3].operations[6].scalar_flops | 1966080 |
| stages[3].operations[6].special_ops.negate | 327680 |
| stages[3].operations[6].source_detail.Q[0] | 1 |
| stages[3].operations[6].source_detail.Q[1] | 32 |
| stages[3].operations[6].source_detail.Q[2] | 128 |
| stages[3].operations[6].source_detail.Q[3] | 128 |
| stages[3].operations[6].source_detail.K[0] | 1 |
| stages[3].operations[6].source_detail.K[1] | 8 |
| stages[3].operations[6].source_detail.K[2] | 128 |
| stages[3].operations[6].source_detail.K[3] | 128 |
| stages[3].operations[7].name | kv_append |
| stages[3].operations[7].matrix_flops | 0 |
| stages[3].operations[7].input_precision | unknown (null) |
| stages[3].operations[7].accumulator_precision | unknown (null) |
| stages[3].operations[7].sparsity | unknown (null) |
| stages[3].operations[7].scalar_flops | 0 |
| stages[3].operations[7].special_ops | {} |
| stages[3].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[3].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[3].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[3].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[3].operations[8].name | qk |
| stages[3].operations[8].matrix_flops | 67633152 |
| stages[3].operations[8].input_precision | BF16 |
| stages[3].operations[8].accumulator_precision | FP32 |
| stages[3].operations[8].sparsity | dense |
| stages[3].operations[8].scalar_flops | 0 |
| stages[3].operations[8].special_ops | {} |
| stages[3].operations[8].source_detail.Q[0] | 1 |
| stages[3].operations[8].source_detail.Q[1] | 32 |
| stages[3].operations[8].source_detail.Q[2] | 128 |
| stages[3].operations[8].source_detail.Q[3] | 128 |
| stages[3].operations[8].source_detail.K_shared[0] | 1 |
| stages[3].operations[8].source_detail.K_shared[1] | 8 |
| stages[3].operations[8].source_detail.K_shared[2] | 128 |
| stages[3].operations[8].source_detail.K_shared[3] | 128 |
| stages[3].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[3].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[3].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[3].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[3].operations[9].name | score_scale_mask_softmax |
| stages[3].operations[9].matrix_flops | 0 |
| stages[3].operations[9].input_precision | unknown (null) |
| stages[3].operations[9].accumulator_precision | unknown (null) |
| stages[3].operations[9].sparsity | unknown (null) |
| stages[3].operations[9].scalar_flops | 1052672 |
| stages[3].operations[9].special_ops.exp | 264192 |
| stages[3].operations[9].special_ops.compare_max | 260096 |
| stages[3].operations[9].special_ops.mask_decisions | 524288 |
| stages[3].operations[9].source_detail.scores[0] | 1 |
| stages[3].operations[9].source_detail.scores[1] | 32 |
| stages[3].operations[9].source_detail.scores[2] | 128 |
| stages[3].operations[9].source_detail.scores[3] | 128 |
| stages[3].operations[10].name | pv |
| stages[3].operations[10].matrix_flops | 67633152 |
| stages[3].operations[10].input_precision | BF16 |
| stages[3].operations[10].accumulator_precision | FP32 |
| stages[3].operations[10].sparsity | dense |
| stages[3].operations[10].scalar_flops | 0 |
| stages[3].operations[10].special_ops | {} |
| stages[3].operations[10].source_detail.P[0] | 1 |
| stages[3].operations[10].source_detail.P[1] | 32 |
| stages[3].operations[10].source_detail.P[2] | 128 |
| stages[3].operations[10].source_detail.P[3] | 128 |
| stages[3].operations[10].source_detail.V_shared[0] | 1 |
| stages[3].operations[10].source_detail.V_shared[1] | 8 |
| stages[3].operations[10].source_detail.V_shared[2] | 128 |
| stages[3].operations[10].source_detail.V_shared[3] | 128 |
| stages[3].operations[10].source_detail.output[0] | 1 |
| stages[3].operations[10].source_detail.output[1] | 32 |
| stages[3].operations[10].source_detail.output[2] | 128 |
| stages[3].operations[10].source_detail.output[3] | 128 |
| stages[3].operations[11].name | o_proj |
| stages[3].operations[11].matrix_flops | 4294967296 |
| stages[3].operations[11].input_precision | BF16 |
| stages[3].operations[11].accumulator_precision | FP32 |
| stages[3].operations[11].sparsity | dense |
| stages[3].operations[11].scalar_flops | 0 |
| stages[3].operations[11].special_ops | {} |
| stages[3].operations[11].source_detail.input[0] | 128 |
| stages[3].operations[11].source_detail.input[1] | 4096 |
| stages[3].operations[11].source_detail.weight_math[0] | 4096 |
| stages[3].operations[11].source_detail.weight_math[1] | 4096 |
| stages[3].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[3].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[11].source_detail.output[0] | 128 |
| stages[3].operations[11].source_detail.output[1] | 4096 |
| stages[3].operations[12].name | attention_residual |
| stages[3].operations[12].matrix_flops | 0 |
| stages[3].operations[12].input_precision | unknown (null) |
| stages[3].operations[12].accumulator_precision | unknown (null) |
| stages[3].operations[12].sparsity | unknown (null) |
| stages[3].operations[12].scalar_flops | 524288 |
| stages[3].operations[12].special_ops | {} |
| stages[3].operations[12].source_detail.inputs_each[0] | 128 |
| stages[3].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[3].operations[12].source_detail.output[0] | 128 |
| stages[3].operations[12].source_detail.output[1] | 4096 |
| stages[3].operations[13].name | post_attention_layernorm |
| stages[3].operations[13].matrix_flops | 0 |
| stages[3].operations[13].input_precision | unknown (null) |
| stages[3].operations[13].accumulator_precision | unknown (null) |
| stages[3].operations[13].sparsity | unknown (null) |
| stages[3].operations[13].scalar_flops | 2097280 |
| stages[3].operations[13].special_ops.rsqrt | 128 |
| stages[3].operations[13].source_detail.input[0] | 128 |
| stages[3].operations[13].source_detail.input[1] | 4096 |
| stages[3].operations[13].source_detail.weight[0] | 4096 |
| stages[3].operations[13].source_detail.output[0] | 128 |
| stages[3].operations[13].source_detail.output[1] | 4096 |
| stages[3].operations[14].name | gate_proj |
| stages[3].operations[14].matrix_flops | 12884901888 |
| stages[3].operations[14].input_precision | BF16 |
| stages[3].operations[14].accumulator_precision | FP32 |
| stages[3].operations[14].sparsity | dense |
| stages[3].operations[14].scalar_flops | 0 |
| stages[3].operations[14].special_ops | {} |
| stages[3].operations[14].source_detail.input[0] | 128 |
| stages[3].operations[14].source_detail.input[1] | 4096 |
| stages[3].operations[14].source_detail.weight_math[0] | 4096 |
| stages[3].operations[14].source_detail.weight_math[1] | 12288 |
| stages[3].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[3].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[14].source_detail.output[0] | 128 |
| stages[3].operations[14].source_detail.output[1] | 12288 |
| stages[3].operations[15].name | up_proj |
| stages[3].operations[15].matrix_flops | 12884901888 |
| stages[3].operations[15].input_precision | BF16 |
| stages[3].operations[15].accumulator_precision | FP32 |
| stages[3].operations[15].sparsity | dense |
| stages[3].operations[15].scalar_flops | 0 |
| stages[3].operations[15].special_ops | {} |
| stages[3].operations[15].source_detail.input[0] | 128 |
| stages[3].operations[15].source_detail.input[1] | 4096 |
| stages[3].operations[15].source_detail.weight_math[0] | 4096 |
| stages[3].operations[15].source_detail.weight_math[1] | 12288 |
| stages[3].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[3].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[3].operations[15].source_detail.output[0] | 128 |
| stages[3].operations[15].source_detail.output[1] | 12288 |
| stages[3].operations[16].name | silu_mul |
| stages[3].operations[16].matrix_flops | 0 |
| stages[3].operations[16].input_precision | unknown (null) |
| stages[3].operations[16].accumulator_precision | unknown (null) |
| stages[3].operations[16].sparsity | unknown (null) |
| stages[3].operations[16].scalar_flops | 6291456 |
| stages[3].operations[16].special_ops.exp | 1572864 |
| stages[3].operations[16].special_ops.negate | 1572864 |
| stages[3].operations[16].source_detail.gate[0] | 128 |
| stages[3].operations[16].source_detail.gate[1] | 12288 |
| stages[3].operations[16].source_detail.up[0] | 128 |
| stages[3].operations[16].source_detail.up[1] | 12288 |
| stages[3].operations[16].source_detail.output[0] | 128 |
| stages[3].operations[16].source_detail.output[1] | 12288 |
| stages[3].operations[17].name | down_proj |
| stages[3].operations[17].matrix_flops | 12884901888 |
| stages[3].operations[17].input_precision | BF16 |
| stages[3].operations[17].accumulator_precision | FP32 |
| stages[3].operations[17].sparsity | dense |
| stages[3].operations[17].scalar_flops | 0 |
| stages[3].operations[17].special_ops | {} |
| stages[3].operations[17].source_detail.input[0] | 128 |
| stages[3].operations[17].source_detail.input[1] | 12288 |
| stages[3].operations[17].source_detail.weight_math[0] | 12288 |
| stages[3].operations[17].source_detail.weight_math[1] | 4096 |
| stages[3].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[3].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[3].operations[17].source_detail.output[0] | 128 |
| stages[3].operations[17].source_detail.output[1] | 4096 |
| stages[3].operations[18].name | ffn_residual |
| stages[3].operations[18].matrix_flops | 0 |
| stages[3].operations[18].input_precision | unknown (null) |
| stages[3].operations[18].accumulator_precision | unknown (null) |
| stages[3].operations[18].sparsity | unknown (null) |
| stages[3].operations[18].scalar_flops | 524288 |
| stages[3].operations[18].special_ops | {} |
| stages[3].operations[18].source_detail.inputs_each[0] | 128 |
| stages[3].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[3].operations[18].source_detail.output[0] | 128 |
| stages[3].operations[18].source_detail.output[1] | 4096 |
| stages[4].id | layer:3 |
| stages[4].work.vector_fp32 | 17179904 |
| stages[4].work.special:rsqrt | 5376 |
| stages[4].work.interface_bytes | 438387200 |
| stages[4].work.matrix_bf16 | 49527390208 |
| stages[4].work.special:negate | 1900544 |
| stages[4].work.special:exp | 1837056 |
| stages[4].work.special:compare_max | 260096 |
| stages[4].work.special:mask_decisions | 524288 |
| stages[4].operations[0].name | input_layernorm |
| stages[4].operations[0].matrix_flops | 0 |
| stages[4].operations[0].input_precision | unknown (null) |
| stages[4].operations[0].accumulator_precision | unknown (null) |
| stages[4].operations[0].sparsity | unknown (null) |
| stages[4].operations[0].scalar_flops | 2097280 |
| stages[4].operations[0].special_ops.rsqrt | 128 |
| stages[4].operations[0].source_detail.input[0] | 128 |
| stages[4].operations[0].source_detail.input[1] | 4096 |
| stages[4].operations[0].source_detail.weight[0] | 4096 |
| stages[4].operations[0].source_detail.output[0] | 128 |
| stages[4].operations[0].source_detail.output[1] | 4096 |
| stages[4].operations[1].name | q_proj |
| stages[4].operations[1].matrix_flops | 4294967296 |
| stages[4].operations[1].input_precision | BF16 |
| stages[4].operations[1].accumulator_precision | FP32 |
| stages[4].operations[1].sparsity | dense |
| stages[4].operations[1].scalar_flops | 0 |
| stages[4].operations[1].special_ops | {} |
| stages[4].operations[1].source_detail.input[0] | 128 |
| stages[4].operations[1].source_detail.input[1] | 4096 |
| stages[4].operations[1].source_detail.weight_math[0] | 4096 |
| stages[4].operations[1].source_detail.weight_math[1] | 4096 |
| stages[4].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[4].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[1].source_detail.output[0] | 128 |
| stages[4].operations[1].source_detail.output[1] | 4096 |
| stages[4].operations[2].name | k_proj |
| stages[4].operations[2].matrix_flops | 1073741824 |
| stages[4].operations[2].input_precision | BF16 |
| stages[4].operations[2].accumulator_precision | FP32 |
| stages[4].operations[2].sparsity | dense |
| stages[4].operations[2].scalar_flops | 0 |
| stages[4].operations[2].special_ops | {} |
| stages[4].operations[2].source_detail.input[0] | 128 |
| stages[4].operations[2].source_detail.input[1] | 4096 |
| stages[4].operations[2].source_detail.weight_math[0] | 4096 |
| stages[4].operations[2].source_detail.weight_math[1] | 1024 |
| stages[4].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[4].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[2].source_detail.output[0] | 128 |
| stages[4].operations[2].source_detail.output[1] | 1024 |
| stages[4].operations[3].name | v_proj |
| stages[4].operations[3].matrix_flops | 1073741824 |
| stages[4].operations[3].input_precision | BF16 |
| stages[4].operations[3].accumulator_precision | FP32 |
| stages[4].operations[3].sparsity | dense |
| stages[4].operations[3].scalar_flops | 0 |
| stages[4].operations[3].special_ops | {} |
| stages[4].operations[3].source_detail.input[0] | 128 |
| stages[4].operations[3].source_detail.input[1] | 4096 |
| stages[4].operations[3].source_detail.weight_math[0] | 4096 |
| stages[4].operations[3].source_detail.weight_math[1] | 1024 |
| stages[4].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[4].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[3].source_detail.output[0] | 128 |
| stages[4].operations[3].source_detail.output[1] | 1024 |
| stages[4].operations[4].name | q_norm |
| stages[4].operations[4].matrix_flops | 0 |
| stages[4].operations[4].input_precision | unknown (null) |
| stages[4].operations[4].accumulator_precision | unknown (null) |
| stages[4].operations[4].sparsity | unknown (null) |
| stages[4].operations[4].scalar_flops | 2101248 |
| stages[4].operations[4].special_ops.rsqrt | 4096 |
| stages[4].operations[4].source_detail.input[0] | 4096 |
| stages[4].operations[4].source_detail.input[1] | 128 |
| stages[4].operations[4].source_detail.weight[0] | 128 |
| stages[4].operations[4].source_detail.output[0] | 4096 |
| stages[4].operations[4].source_detail.output[1] | 128 |
| stages[4].operations[5].name | k_norm |
| stages[4].operations[5].matrix_flops | 0 |
| stages[4].operations[5].input_precision | unknown (null) |
| stages[4].operations[5].accumulator_precision | unknown (null) |
| stages[4].operations[5].sparsity | unknown (null) |
| stages[4].operations[5].scalar_flops | 525312 |
| stages[4].operations[5].special_ops.rsqrt | 1024 |
| stages[4].operations[5].source_detail.input[0] | 1024 |
| stages[4].operations[5].source_detail.input[1] | 128 |
| stages[4].operations[5].source_detail.weight[0] | 128 |
| stages[4].operations[5].source_detail.output[0] | 1024 |
| stages[4].operations[5].source_detail.output[1] | 128 |
| stages[4].operations[6].name | apply_rope |
| stages[4].operations[6].matrix_flops | 0 |
| stages[4].operations[6].input_precision | unknown (null) |
| stages[4].operations[6].accumulator_precision | unknown (null) |
| stages[4].operations[6].sparsity | unknown (null) |
| stages[4].operations[6].scalar_flops | 1966080 |
| stages[4].operations[6].special_ops.negate | 327680 |
| stages[4].operations[6].source_detail.Q[0] | 1 |
| stages[4].operations[6].source_detail.Q[1] | 32 |
| stages[4].operations[6].source_detail.Q[2] | 128 |
| stages[4].operations[6].source_detail.Q[3] | 128 |
| stages[4].operations[6].source_detail.K[0] | 1 |
| stages[4].operations[6].source_detail.K[1] | 8 |
| stages[4].operations[6].source_detail.K[2] | 128 |
| stages[4].operations[6].source_detail.K[3] | 128 |
| stages[4].operations[7].name | kv_append |
| stages[4].operations[7].matrix_flops | 0 |
| stages[4].operations[7].input_precision | unknown (null) |
| stages[4].operations[7].accumulator_precision | unknown (null) |
| stages[4].operations[7].sparsity | unknown (null) |
| stages[4].operations[7].scalar_flops | 0 |
| stages[4].operations[7].special_ops | {} |
| stages[4].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[4].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[4].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[4].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[4].operations[8].name | qk |
| stages[4].operations[8].matrix_flops | 67633152 |
| stages[4].operations[8].input_precision | BF16 |
| stages[4].operations[8].accumulator_precision | FP32 |
| stages[4].operations[8].sparsity | dense |
| stages[4].operations[8].scalar_flops | 0 |
| stages[4].operations[8].special_ops | {} |
| stages[4].operations[8].source_detail.Q[0] | 1 |
| stages[4].operations[8].source_detail.Q[1] | 32 |
| stages[4].operations[8].source_detail.Q[2] | 128 |
| stages[4].operations[8].source_detail.Q[3] | 128 |
| stages[4].operations[8].source_detail.K_shared[0] | 1 |
| stages[4].operations[8].source_detail.K_shared[1] | 8 |
| stages[4].operations[8].source_detail.K_shared[2] | 128 |
| stages[4].operations[8].source_detail.K_shared[3] | 128 |
| stages[4].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[4].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[4].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[4].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[4].operations[9].name | score_scale_mask_softmax |
| stages[4].operations[9].matrix_flops | 0 |
| stages[4].operations[9].input_precision | unknown (null) |
| stages[4].operations[9].accumulator_precision | unknown (null) |
| stages[4].operations[9].sparsity | unknown (null) |
| stages[4].operations[9].scalar_flops | 1052672 |
| stages[4].operations[9].special_ops.exp | 264192 |
| stages[4].operations[9].special_ops.compare_max | 260096 |
| stages[4].operations[9].special_ops.mask_decisions | 524288 |
| stages[4].operations[9].source_detail.scores[0] | 1 |
| stages[4].operations[9].source_detail.scores[1] | 32 |
| stages[4].operations[9].source_detail.scores[2] | 128 |
| stages[4].operations[9].source_detail.scores[3] | 128 |
| stages[4].operations[10].name | pv |
| stages[4].operations[10].matrix_flops | 67633152 |
| stages[4].operations[10].input_precision | BF16 |
| stages[4].operations[10].accumulator_precision | FP32 |
| stages[4].operations[10].sparsity | dense |
| stages[4].operations[10].scalar_flops | 0 |
| stages[4].operations[10].special_ops | {} |
| stages[4].operations[10].source_detail.P[0] | 1 |
| stages[4].operations[10].source_detail.P[1] | 32 |
| stages[4].operations[10].source_detail.P[2] | 128 |
| stages[4].operations[10].source_detail.P[3] | 128 |
| stages[4].operations[10].source_detail.V_shared[0] | 1 |
| stages[4].operations[10].source_detail.V_shared[1] | 8 |
| stages[4].operations[10].source_detail.V_shared[2] | 128 |
| stages[4].operations[10].source_detail.V_shared[3] | 128 |
| stages[4].operations[10].source_detail.output[0] | 1 |
| stages[4].operations[10].source_detail.output[1] | 32 |
| stages[4].operations[10].source_detail.output[2] | 128 |
| stages[4].operations[10].source_detail.output[3] | 128 |
| stages[4].operations[11].name | o_proj |
| stages[4].operations[11].matrix_flops | 4294967296 |
| stages[4].operations[11].input_precision | BF16 |
| stages[4].operations[11].accumulator_precision | FP32 |
| stages[4].operations[11].sparsity | dense |
| stages[4].operations[11].scalar_flops | 0 |
| stages[4].operations[11].special_ops | {} |
| stages[4].operations[11].source_detail.input[0] | 128 |
| stages[4].operations[11].source_detail.input[1] | 4096 |
| stages[4].operations[11].source_detail.weight_math[0] | 4096 |
| stages[4].operations[11].source_detail.weight_math[1] | 4096 |
| stages[4].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[4].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[11].source_detail.output[0] | 128 |
| stages[4].operations[11].source_detail.output[1] | 4096 |
| stages[4].operations[12].name | attention_residual |
| stages[4].operations[12].matrix_flops | 0 |
| stages[4].operations[12].input_precision | unknown (null) |
| stages[4].operations[12].accumulator_precision | unknown (null) |
| stages[4].operations[12].sparsity | unknown (null) |
| stages[4].operations[12].scalar_flops | 524288 |
| stages[4].operations[12].special_ops | {} |
| stages[4].operations[12].source_detail.inputs_each[0] | 128 |
| stages[4].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[4].operations[12].source_detail.output[0] | 128 |
| stages[4].operations[12].source_detail.output[1] | 4096 |
| stages[4].operations[13].name | post_attention_layernorm |
| stages[4].operations[13].matrix_flops | 0 |
| stages[4].operations[13].input_precision | unknown (null) |
| stages[4].operations[13].accumulator_precision | unknown (null) |
| stages[4].operations[13].sparsity | unknown (null) |
| stages[4].operations[13].scalar_flops | 2097280 |
| stages[4].operations[13].special_ops.rsqrt | 128 |
| stages[4].operations[13].source_detail.input[0] | 128 |
| stages[4].operations[13].source_detail.input[1] | 4096 |
| stages[4].operations[13].source_detail.weight[0] | 4096 |
| stages[4].operations[13].source_detail.output[0] | 128 |
| stages[4].operations[13].source_detail.output[1] | 4096 |
| stages[4].operations[14].name | gate_proj |
| stages[4].operations[14].matrix_flops | 12884901888 |
| stages[4].operations[14].input_precision | BF16 |
| stages[4].operations[14].accumulator_precision | FP32 |
| stages[4].operations[14].sparsity | dense |
| stages[4].operations[14].scalar_flops | 0 |
| stages[4].operations[14].special_ops | {} |
| stages[4].operations[14].source_detail.input[0] | 128 |
| stages[4].operations[14].source_detail.input[1] | 4096 |
| stages[4].operations[14].source_detail.weight_math[0] | 4096 |
| stages[4].operations[14].source_detail.weight_math[1] | 12288 |
| stages[4].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[4].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[14].source_detail.output[0] | 128 |
| stages[4].operations[14].source_detail.output[1] | 12288 |
| stages[4].operations[15].name | up_proj |
| stages[4].operations[15].matrix_flops | 12884901888 |
| stages[4].operations[15].input_precision | BF16 |
| stages[4].operations[15].accumulator_precision | FP32 |
| stages[4].operations[15].sparsity | dense |
| stages[4].operations[15].scalar_flops | 0 |
| stages[4].operations[15].special_ops | {} |
| stages[4].operations[15].source_detail.input[0] | 128 |
| stages[4].operations[15].source_detail.input[1] | 4096 |
| stages[4].operations[15].source_detail.weight_math[0] | 4096 |
| stages[4].operations[15].source_detail.weight_math[1] | 12288 |
| stages[4].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[4].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[4].operations[15].source_detail.output[0] | 128 |
| stages[4].operations[15].source_detail.output[1] | 12288 |
| stages[4].operations[16].name | silu_mul |
| stages[4].operations[16].matrix_flops | 0 |
| stages[4].operations[16].input_precision | unknown (null) |
| stages[4].operations[16].accumulator_precision | unknown (null) |
| stages[4].operations[16].sparsity | unknown (null) |
| stages[4].operations[16].scalar_flops | 6291456 |
| stages[4].operations[16].special_ops.exp | 1572864 |
| stages[4].operations[16].special_ops.negate | 1572864 |
| stages[4].operations[16].source_detail.gate[0] | 128 |
| stages[4].operations[16].source_detail.gate[1] | 12288 |
| stages[4].operations[16].source_detail.up[0] | 128 |
| stages[4].operations[16].source_detail.up[1] | 12288 |
| stages[4].operations[16].source_detail.output[0] | 128 |
| stages[4].operations[16].source_detail.output[1] | 12288 |
| stages[4].operations[17].name | down_proj |
| stages[4].operations[17].matrix_flops | 12884901888 |
| stages[4].operations[17].input_precision | BF16 |
| stages[4].operations[17].accumulator_precision | FP32 |
| stages[4].operations[17].sparsity | dense |
| stages[4].operations[17].scalar_flops | 0 |
| stages[4].operations[17].special_ops | {} |
| stages[4].operations[17].source_detail.input[0] | 128 |
| stages[4].operations[17].source_detail.input[1] | 12288 |
| stages[4].operations[17].source_detail.weight_math[0] | 12288 |
| stages[4].operations[17].source_detail.weight_math[1] | 4096 |
| stages[4].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[4].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[4].operations[17].source_detail.output[0] | 128 |
| stages[4].operations[17].source_detail.output[1] | 4096 |
| stages[4].operations[18].name | ffn_residual |
| stages[4].operations[18].matrix_flops | 0 |
| stages[4].operations[18].input_precision | unknown (null) |
| stages[4].operations[18].accumulator_precision | unknown (null) |
| stages[4].operations[18].sparsity | unknown (null) |
| stages[4].operations[18].scalar_flops | 524288 |
| stages[4].operations[18].special_ops | {} |
| stages[4].operations[18].source_detail.inputs_each[0] | 128 |
| stages[4].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[4].operations[18].source_detail.output[0] | 128 |
| stages[4].operations[18].source_detail.output[1] | 4096 |
| stages[5].id | layer:4 |
| stages[5].work.vector_fp32 | 17179904 |
| stages[5].work.special:rsqrt | 5376 |
| stages[5].work.interface_bytes | 438387200 |
| stages[5].work.matrix_bf16 | 49527390208 |
| stages[5].work.special:negate | 1900544 |
| stages[5].work.special:exp | 1837056 |
| stages[5].work.special:compare_max | 260096 |
| stages[5].work.special:mask_decisions | 524288 |
| stages[5].operations[0].name | input_layernorm |
| stages[5].operations[0].matrix_flops | 0 |
| stages[5].operations[0].input_precision | unknown (null) |
| stages[5].operations[0].accumulator_precision | unknown (null) |
| stages[5].operations[0].sparsity | unknown (null) |
| stages[5].operations[0].scalar_flops | 2097280 |
| stages[5].operations[0].special_ops.rsqrt | 128 |
| stages[5].operations[0].source_detail.input[0] | 128 |
| stages[5].operations[0].source_detail.input[1] | 4096 |
| stages[5].operations[0].source_detail.weight[0] | 4096 |
| stages[5].operations[0].source_detail.output[0] | 128 |
| stages[5].operations[0].source_detail.output[1] | 4096 |
| stages[5].operations[1].name | q_proj |
| stages[5].operations[1].matrix_flops | 4294967296 |
| stages[5].operations[1].input_precision | BF16 |
| stages[5].operations[1].accumulator_precision | FP32 |
| stages[5].operations[1].sparsity | dense |
| stages[5].operations[1].scalar_flops | 0 |
| stages[5].operations[1].special_ops | {} |
| stages[5].operations[1].source_detail.input[0] | 128 |
| stages[5].operations[1].source_detail.input[1] | 4096 |
| stages[5].operations[1].source_detail.weight_math[0] | 4096 |
| stages[5].operations[1].source_detail.weight_math[1] | 4096 |
| stages[5].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[5].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[1].source_detail.output[0] | 128 |
| stages[5].operations[1].source_detail.output[1] | 4096 |
| stages[5].operations[2].name | k_proj |
| stages[5].operations[2].matrix_flops | 1073741824 |
| stages[5].operations[2].input_precision | BF16 |
| stages[5].operations[2].accumulator_precision | FP32 |
| stages[5].operations[2].sparsity | dense |
| stages[5].operations[2].scalar_flops | 0 |
| stages[5].operations[2].special_ops | {} |
| stages[5].operations[2].source_detail.input[0] | 128 |
| stages[5].operations[2].source_detail.input[1] | 4096 |
| stages[5].operations[2].source_detail.weight_math[0] | 4096 |
| stages[5].operations[2].source_detail.weight_math[1] | 1024 |
| stages[5].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[5].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[2].source_detail.output[0] | 128 |
| stages[5].operations[2].source_detail.output[1] | 1024 |
| stages[5].operations[3].name | v_proj |
| stages[5].operations[3].matrix_flops | 1073741824 |
| stages[5].operations[3].input_precision | BF16 |
| stages[5].operations[3].accumulator_precision | FP32 |
| stages[5].operations[3].sparsity | dense |
| stages[5].operations[3].scalar_flops | 0 |
| stages[5].operations[3].special_ops | {} |
| stages[5].operations[3].source_detail.input[0] | 128 |
| stages[5].operations[3].source_detail.input[1] | 4096 |
| stages[5].operations[3].source_detail.weight_math[0] | 4096 |
| stages[5].operations[3].source_detail.weight_math[1] | 1024 |
| stages[5].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[5].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[3].source_detail.output[0] | 128 |
| stages[5].operations[3].source_detail.output[1] | 1024 |
| stages[5].operations[4].name | q_norm |
| stages[5].operations[4].matrix_flops | 0 |
| stages[5].operations[4].input_precision | unknown (null) |
| stages[5].operations[4].accumulator_precision | unknown (null) |
| stages[5].operations[4].sparsity | unknown (null) |
| stages[5].operations[4].scalar_flops | 2101248 |
| stages[5].operations[4].special_ops.rsqrt | 4096 |
| stages[5].operations[4].source_detail.input[0] | 4096 |
| stages[5].operations[4].source_detail.input[1] | 128 |
| stages[5].operations[4].source_detail.weight[0] | 128 |
| stages[5].operations[4].source_detail.output[0] | 4096 |
| stages[5].operations[4].source_detail.output[1] | 128 |
| stages[5].operations[5].name | k_norm |
| stages[5].operations[5].matrix_flops | 0 |
| stages[5].operations[5].input_precision | unknown (null) |
| stages[5].operations[5].accumulator_precision | unknown (null) |
| stages[5].operations[5].sparsity | unknown (null) |
| stages[5].operations[5].scalar_flops | 525312 |
| stages[5].operations[5].special_ops.rsqrt | 1024 |
| stages[5].operations[5].source_detail.input[0] | 1024 |
| stages[5].operations[5].source_detail.input[1] | 128 |
| stages[5].operations[5].source_detail.weight[0] | 128 |
| stages[5].operations[5].source_detail.output[0] | 1024 |
| stages[5].operations[5].source_detail.output[1] | 128 |
| stages[5].operations[6].name | apply_rope |
| stages[5].operations[6].matrix_flops | 0 |
| stages[5].operations[6].input_precision | unknown (null) |
| stages[5].operations[6].accumulator_precision | unknown (null) |
| stages[5].operations[6].sparsity | unknown (null) |
| stages[5].operations[6].scalar_flops | 1966080 |
| stages[5].operations[6].special_ops.negate | 327680 |
| stages[5].operations[6].source_detail.Q[0] | 1 |
| stages[5].operations[6].source_detail.Q[1] | 32 |
| stages[5].operations[6].source_detail.Q[2] | 128 |
| stages[5].operations[6].source_detail.Q[3] | 128 |
| stages[5].operations[6].source_detail.K[0] | 1 |
| stages[5].operations[6].source_detail.K[1] | 8 |
| stages[5].operations[6].source_detail.K[2] | 128 |
| stages[5].operations[6].source_detail.K[3] | 128 |
| stages[5].operations[7].name | kv_append |
| stages[5].operations[7].matrix_flops | 0 |
| stages[5].operations[7].input_precision | unknown (null) |
| stages[5].operations[7].accumulator_precision | unknown (null) |
| stages[5].operations[7].sparsity | unknown (null) |
| stages[5].operations[7].scalar_flops | 0 |
| stages[5].operations[7].special_ops | {} |
| stages[5].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[5].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[5].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[5].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[5].operations[8].name | qk |
| stages[5].operations[8].matrix_flops | 67633152 |
| stages[5].operations[8].input_precision | BF16 |
| stages[5].operations[8].accumulator_precision | FP32 |
| stages[5].operations[8].sparsity | dense |
| stages[5].operations[8].scalar_flops | 0 |
| stages[5].operations[8].special_ops | {} |
| stages[5].operations[8].source_detail.Q[0] | 1 |
| stages[5].operations[8].source_detail.Q[1] | 32 |
| stages[5].operations[8].source_detail.Q[2] | 128 |
| stages[5].operations[8].source_detail.Q[3] | 128 |
| stages[5].operations[8].source_detail.K_shared[0] | 1 |
| stages[5].operations[8].source_detail.K_shared[1] | 8 |
| stages[5].operations[8].source_detail.K_shared[2] | 128 |
| stages[5].operations[8].source_detail.K_shared[3] | 128 |
| stages[5].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[5].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[5].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[5].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[5].operations[9].name | score_scale_mask_softmax |
| stages[5].operations[9].matrix_flops | 0 |
| stages[5].operations[9].input_precision | unknown (null) |
| stages[5].operations[9].accumulator_precision | unknown (null) |
| stages[5].operations[9].sparsity | unknown (null) |
| stages[5].operations[9].scalar_flops | 1052672 |
| stages[5].operations[9].special_ops.exp | 264192 |
| stages[5].operations[9].special_ops.compare_max | 260096 |
| stages[5].operations[9].special_ops.mask_decisions | 524288 |
| stages[5].operations[9].source_detail.scores[0] | 1 |
| stages[5].operations[9].source_detail.scores[1] | 32 |
| stages[5].operations[9].source_detail.scores[2] | 128 |
| stages[5].operations[9].source_detail.scores[3] | 128 |
| stages[5].operations[10].name | pv |
| stages[5].operations[10].matrix_flops | 67633152 |
| stages[5].operations[10].input_precision | BF16 |
| stages[5].operations[10].accumulator_precision | FP32 |
| stages[5].operations[10].sparsity | dense |
| stages[5].operations[10].scalar_flops | 0 |
| stages[5].operations[10].special_ops | {} |
| stages[5].operations[10].source_detail.P[0] | 1 |
| stages[5].operations[10].source_detail.P[1] | 32 |
| stages[5].operations[10].source_detail.P[2] | 128 |
| stages[5].operations[10].source_detail.P[3] | 128 |
| stages[5].operations[10].source_detail.V_shared[0] | 1 |
| stages[5].operations[10].source_detail.V_shared[1] | 8 |
| stages[5].operations[10].source_detail.V_shared[2] | 128 |
| stages[5].operations[10].source_detail.V_shared[3] | 128 |
| stages[5].operations[10].source_detail.output[0] | 1 |
| stages[5].operations[10].source_detail.output[1] | 32 |
| stages[5].operations[10].source_detail.output[2] | 128 |
| stages[5].operations[10].source_detail.output[3] | 128 |
| stages[5].operations[11].name | o_proj |
| stages[5].operations[11].matrix_flops | 4294967296 |
| stages[5].operations[11].input_precision | BF16 |
| stages[5].operations[11].accumulator_precision | FP32 |
| stages[5].operations[11].sparsity | dense |
| stages[5].operations[11].scalar_flops | 0 |
| stages[5].operations[11].special_ops | {} |
| stages[5].operations[11].source_detail.input[0] | 128 |
| stages[5].operations[11].source_detail.input[1] | 4096 |
| stages[5].operations[11].source_detail.weight_math[0] | 4096 |
| stages[5].operations[11].source_detail.weight_math[1] | 4096 |
| stages[5].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[5].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[11].source_detail.output[0] | 128 |
| stages[5].operations[11].source_detail.output[1] | 4096 |
| stages[5].operations[12].name | attention_residual |
| stages[5].operations[12].matrix_flops | 0 |
| stages[5].operations[12].input_precision | unknown (null) |
| stages[5].operations[12].accumulator_precision | unknown (null) |
| stages[5].operations[12].sparsity | unknown (null) |
| stages[5].operations[12].scalar_flops | 524288 |
| stages[5].operations[12].special_ops | {} |
| stages[5].operations[12].source_detail.inputs_each[0] | 128 |
| stages[5].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[5].operations[12].source_detail.output[0] | 128 |
| stages[5].operations[12].source_detail.output[1] | 4096 |
| stages[5].operations[13].name | post_attention_layernorm |
| stages[5].operations[13].matrix_flops | 0 |
| stages[5].operations[13].input_precision | unknown (null) |
| stages[5].operations[13].accumulator_precision | unknown (null) |
| stages[5].operations[13].sparsity | unknown (null) |
| stages[5].operations[13].scalar_flops | 2097280 |
| stages[5].operations[13].special_ops.rsqrt | 128 |
| stages[5].operations[13].source_detail.input[0] | 128 |
| stages[5].operations[13].source_detail.input[1] | 4096 |
| stages[5].operations[13].source_detail.weight[0] | 4096 |
| stages[5].operations[13].source_detail.output[0] | 128 |
| stages[5].operations[13].source_detail.output[1] | 4096 |
| stages[5].operations[14].name | gate_proj |
| stages[5].operations[14].matrix_flops | 12884901888 |
| stages[5].operations[14].input_precision | BF16 |
| stages[5].operations[14].accumulator_precision | FP32 |
| stages[5].operations[14].sparsity | dense |
| stages[5].operations[14].scalar_flops | 0 |
| stages[5].operations[14].special_ops | {} |
| stages[5].operations[14].source_detail.input[0] | 128 |
| stages[5].operations[14].source_detail.input[1] | 4096 |
| stages[5].operations[14].source_detail.weight_math[0] | 4096 |
| stages[5].operations[14].source_detail.weight_math[1] | 12288 |
| stages[5].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[5].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[14].source_detail.output[0] | 128 |
| stages[5].operations[14].source_detail.output[1] | 12288 |
| stages[5].operations[15].name | up_proj |
| stages[5].operations[15].matrix_flops | 12884901888 |
| stages[5].operations[15].input_precision | BF16 |
| stages[5].operations[15].accumulator_precision | FP32 |
| stages[5].operations[15].sparsity | dense |
| stages[5].operations[15].scalar_flops | 0 |
| stages[5].operations[15].special_ops | {} |
| stages[5].operations[15].source_detail.input[0] | 128 |
| stages[5].operations[15].source_detail.input[1] | 4096 |
| stages[5].operations[15].source_detail.weight_math[0] | 4096 |
| stages[5].operations[15].source_detail.weight_math[1] | 12288 |
| stages[5].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[5].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[5].operations[15].source_detail.output[0] | 128 |
| stages[5].operations[15].source_detail.output[1] | 12288 |
| stages[5].operations[16].name | silu_mul |
| stages[5].operations[16].matrix_flops | 0 |
| stages[5].operations[16].input_precision | unknown (null) |
| stages[5].operations[16].accumulator_precision | unknown (null) |
| stages[5].operations[16].sparsity | unknown (null) |
| stages[5].operations[16].scalar_flops | 6291456 |
| stages[5].operations[16].special_ops.exp | 1572864 |
| stages[5].operations[16].special_ops.negate | 1572864 |
| stages[5].operations[16].source_detail.gate[0] | 128 |
| stages[5].operations[16].source_detail.gate[1] | 12288 |
| stages[5].operations[16].source_detail.up[0] | 128 |
| stages[5].operations[16].source_detail.up[1] | 12288 |
| stages[5].operations[16].source_detail.output[0] | 128 |
| stages[5].operations[16].source_detail.output[1] | 12288 |
| stages[5].operations[17].name | down_proj |
| stages[5].operations[17].matrix_flops | 12884901888 |
| stages[5].operations[17].input_precision | BF16 |
| stages[5].operations[17].accumulator_precision | FP32 |
| stages[5].operations[17].sparsity | dense |
| stages[5].operations[17].scalar_flops | 0 |
| stages[5].operations[17].special_ops | {} |
| stages[5].operations[17].source_detail.input[0] | 128 |
| stages[5].operations[17].source_detail.input[1] | 12288 |
| stages[5].operations[17].source_detail.weight_math[0] | 12288 |
| stages[5].operations[17].source_detail.weight_math[1] | 4096 |
| stages[5].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[5].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[5].operations[17].source_detail.output[0] | 128 |
| stages[5].operations[17].source_detail.output[1] | 4096 |
| stages[5].operations[18].name | ffn_residual |
| stages[5].operations[18].matrix_flops | 0 |
| stages[5].operations[18].input_precision | unknown (null) |
| stages[5].operations[18].accumulator_precision | unknown (null) |
| stages[5].operations[18].sparsity | unknown (null) |
| stages[5].operations[18].scalar_flops | 524288 |
| stages[5].operations[18].special_ops | {} |
| stages[5].operations[18].source_detail.inputs_each[0] | 128 |
| stages[5].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[5].operations[18].source_detail.output[0] | 128 |
| stages[5].operations[18].source_detail.output[1] | 4096 |
| stages[6].id | layer:5 |
| stages[6].work.vector_fp32 | 17179904 |
| stages[6].work.special:rsqrt | 5376 |
| stages[6].work.interface_bytes | 438387200 |
| stages[6].work.matrix_bf16 | 49527390208 |
| stages[6].work.special:negate | 1900544 |
| stages[6].work.special:exp | 1837056 |
| stages[6].work.special:compare_max | 260096 |
| stages[6].work.special:mask_decisions | 524288 |
| stages[6].operations[0].name | input_layernorm |
| stages[6].operations[0].matrix_flops | 0 |
| stages[6].operations[0].input_precision | unknown (null) |
| stages[6].operations[0].accumulator_precision | unknown (null) |
| stages[6].operations[0].sparsity | unknown (null) |
| stages[6].operations[0].scalar_flops | 2097280 |
| stages[6].operations[0].special_ops.rsqrt | 128 |
| stages[6].operations[0].source_detail.input[0] | 128 |
| stages[6].operations[0].source_detail.input[1] | 4096 |
| stages[6].operations[0].source_detail.weight[0] | 4096 |
| stages[6].operations[0].source_detail.output[0] | 128 |
| stages[6].operations[0].source_detail.output[1] | 4096 |
| stages[6].operations[1].name | q_proj |
| stages[6].operations[1].matrix_flops | 4294967296 |
| stages[6].operations[1].input_precision | BF16 |
| stages[6].operations[1].accumulator_precision | FP32 |
| stages[6].operations[1].sparsity | dense |
| stages[6].operations[1].scalar_flops | 0 |
| stages[6].operations[1].special_ops | {} |
| stages[6].operations[1].source_detail.input[0] | 128 |
| stages[6].operations[1].source_detail.input[1] | 4096 |
| stages[6].operations[1].source_detail.weight_math[0] | 4096 |
| stages[6].operations[1].source_detail.weight_math[1] | 4096 |
| stages[6].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[6].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[1].source_detail.output[0] | 128 |
| stages[6].operations[1].source_detail.output[1] | 4096 |
| stages[6].operations[2].name | k_proj |
| stages[6].operations[2].matrix_flops | 1073741824 |
| stages[6].operations[2].input_precision | BF16 |
| stages[6].operations[2].accumulator_precision | FP32 |
| stages[6].operations[2].sparsity | dense |
| stages[6].operations[2].scalar_flops | 0 |
| stages[6].operations[2].special_ops | {} |
| stages[6].operations[2].source_detail.input[0] | 128 |
| stages[6].operations[2].source_detail.input[1] | 4096 |
| stages[6].operations[2].source_detail.weight_math[0] | 4096 |
| stages[6].operations[2].source_detail.weight_math[1] | 1024 |
| stages[6].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[6].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[2].source_detail.output[0] | 128 |
| stages[6].operations[2].source_detail.output[1] | 1024 |
| stages[6].operations[3].name | v_proj |
| stages[6].operations[3].matrix_flops | 1073741824 |
| stages[6].operations[3].input_precision | BF16 |
| stages[6].operations[3].accumulator_precision | FP32 |
| stages[6].operations[3].sparsity | dense |
| stages[6].operations[3].scalar_flops | 0 |
| stages[6].operations[3].special_ops | {} |
| stages[6].operations[3].source_detail.input[0] | 128 |
| stages[6].operations[3].source_detail.input[1] | 4096 |
| stages[6].operations[3].source_detail.weight_math[0] | 4096 |
| stages[6].operations[3].source_detail.weight_math[1] | 1024 |
| stages[6].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[6].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[3].source_detail.output[0] | 128 |
| stages[6].operations[3].source_detail.output[1] | 1024 |
| stages[6].operations[4].name | q_norm |
| stages[6].operations[4].matrix_flops | 0 |
| stages[6].operations[4].input_precision | unknown (null) |
| stages[6].operations[4].accumulator_precision | unknown (null) |
| stages[6].operations[4].sparsity | unknown (null) |
| stages[6].operations[4].scalar_flops | 2101248 |
| stages[6].operations[4].special_ops.rsqrt | 4096 |
| stages[6].operations[4].source_detail.input[0] | 4096 |
| stages[6].operations[4].source_detail.input[1] | 128 |
| stages[6].operations[4].source_detail.weight[0] | 128 |
| stages[6].operations[4].source_detail.output[0] | 4096 |
| stages[6].operations[4].source_detail.output[1] | 128 |
| stages[6].operations[5].name | k_norm |
| stages[6].operations[5].matrix_flops | 0 |
| stages[6].operations[5].input_precision | unknown (null) |
| stages[6].operations[5].accumulator_precision | unknown (null) |
| stages[6].operations[5].sparsity | unknown (null) |
| stages[6].operations[5].scalar_flops | 525312 |
| stages[6].operations[5].special_ops.rsqrt | 1024 |
| stages[6].operations[5].source_detail.input[0] | 1024 |
| stages[6].operations[5].source_detail.input[1] | 128 |
| stages[6].operations[5].source_detail.weight[0] | 128 |
| stages[6].operations[5].source_detail.output[0] | 1024 |
| stages[6].operations[5].source_detail.output[1] | 128 |
| stages[6].operations[6].name | apply_rope |
| stages[6].operations[6].matrix_flops | 0 |
| stages[6].operations[6].input_precision | unknown (null) |
| stages[6].operations[6].accumulator_precision | unknown (null) |
| stages[6].operations[6].sparsity | unknown (null) |
| stages[6].operations[6].scalar_flops | 1966080 |
| stages[6].operations[6].special_ops.negate | 327680 |
| stages[6].operations[6].source_detail.Q[0] | 1 |
| stages[6].operations[6].source_detail.Q[1] | 32 |
| stages[6].operations[6].source_detail.Q[2] | 128 |
| stages[6].operations[6].source_detail.Q[3] | 128 |
| stages[6].operations[6].source_detail.K[0] | 1 |
| stages[6].operations[6].source_detail.K[1] | 8 |
| stages[6].operations[6].source_detail.K[2] | 128 |
| stages[6].operations[6].source_detail.K[3] | 128 |
| stages[6].operations[7].name | kv_append |
| stages[6].operations[7].matrix_flops | 0 |
| stages[6].operations[7].input_precision | unknown (null) |
| stages[6].operations[7].accumulator_precision | unknown (null) |
| stages[6].operations[7].sparsity | unknown (null) |
| stages[6].operations[7].scalar_flops | 0 |
| stages[6].operations[7].special_ops | {} |
| stages[6].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[6].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[6].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[6].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[6].operations[8].name | qk |
| stages[6].operations[8].matrix_flops | 67633152 |
| stages[6].operations[8].input_precision | BF16 |
| stages[6].operations[8].accumulator_precision | FP32 |
| stages[6].operations[8].sparsity | dense |
| stages[6].operations[8].scalar_flops | 0 |
| stages[6].operations[8].special_ops | {} |
| stages[6].operations[8].source_detail.Q[0] | 1 |
| stages[6].operations[8].source_detail.Q[1] | 32 |
| stages[6].operations[8].source_detail.Q[2] | 128 |
| stages[6].operations[8].source_detail.Q[3] | 128 |
| stages[6].operations[8].source_detail.K_shared[0] | 1 |
| stages[6].operations[8].source_detail.K_shared[1] | 8 |
| stages[6].operations[8].source_detail.K_shared[2] | 128 |
| stages[6].operations[8].source_detail.K_shared[3] | 128 |
| stages[6].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[6].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[6].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[6].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[6].operations[9].name | score_scale_mask_softmax |
| stages[6].operations[9].matrix_flops | 0 |
| stages[6].operations[9].input_precision | unknown (null) |
| stages[6].operations[9].accumulator_precision | unknown (null) |
| stages[6].operations[9].sparsity | unknown (null) |
| stages[6].operations[9].scalar_flops | 1052672 |
| stages[6].operations[9].special_ops.exp | 264192 |
| stages[6].operations[9].special_ops.compare_max | 260096 |
| stages[6].operations[9].special_ops.mask_decisions | 524288 |
| stages[6].operations[9].source_detail.scores[0] | 1 |
| stages[6].operations[9].source_detail.scores[1] | 32 |
| stages[6].operations[9].source_detail.scores[2] | 128 |
| stages[6].operations[9].source_detail.scores[3] | 128 |
| stages[6].operations[10].name | pv |
| stages[6].operations[10].matrix_flops | 67633152 |
| stages[6].operations[10].input_precision | BF16 |
| stages[6].operations[10].accumulator_precision | FP32 |
| stages[6].operations[10].sparsity | dense |
| stages[6].operations[10].scalar_flops | 0 |
| stages[6].operations[10].special_ops | {} |
| stages[6].operations[10].source_detail.P[0] | 1 |
| stages[6].operations[10].source_detail.P[1] | 32 |
| stages[6].operations[10].source_detail.P[2] | 128 |
| stages[6].operations[10].source_detail.P[3] | 128 |
| stages[6].operations[10].source_detail.V_shared[0] | 1 |
| stages[6].operations[10].source_detail.V_shared[1] | 8 |
| stages[6].operations[10].source_detail.V_shared[2] | 128 |
| stages[6].operations[10].source_detail.V_shared[3] | 128 |
| stages[6].operations[10].source_detail.output[0] | 1 |
| stages[6].operations[10].source_detail.output[1] | 32 |
| stages[6].operations[10].source_detail.output[2] | 128 |
| stages[6].operations[10].source_detail.output[3] | 128 |
| stages[6].operations[11].name | o_proj |
| stages[6].operations[11].matrix_flops | 4294967296 |
| stages[6].operations[11].input_precision | BF16 |
| stages[6].operations[11].accumulator_precision | FP32 |
| stages[6].operations[11].sparsity | dense |
| stages[6].operations[11].scalar_flops | 0 |
| stages[6].operations[11].special_ops | {} |
| stages[6].operations[11].source_detail.input[0] | 128 |
| stages[6].operations[11].source_detail.input[1] | 4096 |
| stages[6].operations[11].source_detail.weight_math[0] | 4096 |
| stages[6].operations[11].source_detail.weight_math[1] | 4096 |
| stages[6].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[6].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[11].source_detail.output[0] | 128 |
| stages[6].operations[11].source_detail.output[1] | 4096 |
| stages[6].operations[12].name | attention_residual |
| stages[6].operations[12].matrix_flops | 0 |
| stages[6].operations[12].input_precision | unknown (null) |
| stages[6].operations[12].accumulator_precision | unknown (null) |
| stages[6].operations[12].sparsity | unknown (null) |
| stages[6].operations[12].scalar_flops | 524288 |
| stages[6].operations[12].special_ops | {} |
| stages[6].operations[12].source_detail.inputs_each[0] | 128 |
| stages[6].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[6].operations[12].source_detail.output[0] | 128 |
| stages[6].operations[12].source_detail.output[1] | 4096 |
| stages[6].operations[13].name | post_attention_layernorm |
| stages[6].operations[13].matrix_flops | 0 |
| stages[6].operations[13].input_precision | unknown (null) |
| stages[6].operations[13].accumulator_precision | unknown (null) |
| stages[6].operations[13].sparsity | unknown (null) |
| stages[6].operations[13].scalar_flops | 2097280 |
| stages[6].operations[13].special_ops.rsqrt | 128 |
| stages[6].operations[13].source_detail.input[0] | 128 |
| stages[6].operations[13].source_detail.input[1] | 4096 |
| stages[6].operations[13].source_detail.weight[0] | 4096 |
| stages[6].operations[13].source_detail.output[0] | 128 |
| stages[6].operations[13].source_detail.output[1] | 4096 |
| stages[6].operations[14].name | gate_proj |
| stages[6].operations[14].matrix_flops | 12884901888 |
| stages[6].operations[14].input_precision | BF16 |
| stages[6].operations[14].accumulator_precision | FP32 |
| stages[6].operations[14].sparsity | dense |
| stages[6].operations[14].scalar_flops | 0 |
| stages[6].operations[14].special_ops | {} |
| stages[6].operations[14].source_detail.input[0] | 128 |
| stages[6].operations[14].source_detail.input[1] | 4096 |
| stages[6].operations[14].source_detail.weight_math[0] | 4096 |
| stages[6].operations[14].source_detail.weight_math[1] | 12288 |
| stages[6].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[6].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[14].source_detail.output[0] | 128 |
| stages[6].operations[14].source_detail.output[1] | 12288 |
| stages[6].operations[15].name | up_proj |
| stages[6].operations[15].matrix_flops | 12884901888 |
| stages[6].operations[15].input_precision | BF16 |
| stages[6].operations[15].accumulator_precision | FP32 |
| stages[6].operations[15].sparsity | dense |
| stages[6].operations[15].scalar_flops | 0 |
| stages[6].operations[15].special_ops | {} |
| stages[6].operations[15].source_detail.input[0] | 128 |
| stages[6].operations[15].source_detail.input[1] | 4096 |
| stages[6].operations[15].source_detail.weight_math[0] | 4096 |
| stages[6].operations[15].source_detail.weight_math[1] | 12288 |
| stages[6].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[6].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[6].operations[15].source_detail.output[0] | 128 |
| stages[6].operations[15].source_detail.output[1] | 12288 |
| stages[6].operations[16].name | silu_mul |
| stages[6].operations[16].matrix_flops | 0 |
| stages[6].operations[16].input_precision | unknown (null) |
| stages[6].operations[16].accumulator_precision | unknown (null) |
| stages[6].operations[16].sparsity | unknown (null) |
| stages[6].operations[16].scalar_flops | 6291456 |
| stages[6].operations[16].special_ops.exp | 1572864 |
| stages[6].operations[16].special_ops.negate | 1572864 |
| stages[6].operations[16].source_detail.gate[0] | 128 |
| stages[6].operations[16].source_detail.gate[1] | 12288 |
| stages[6].operations[16].source_detail.up[0] | 128 |
| stages[6].operations[16].source_detail.up[1] | 12288 |
| stages[6].operations[16].source_detail.output[0] | 128 |
| stages[6].operations[16].source_detail.output[1] | 12288 |
| stages[6].operations[17].name | down_proj |
| stages[6].operations[17].matrix_flops | 12884901888 |
| stages[6].operations[17].input_precision | BF16 |
| stages[6].operations[17].accumulator_precision | FP32 |
| stages[6].operations[17].sparsity | dense |
| stages[6].operations[17].scalar_flops | 0 |
| stages[6].operations[17].special_ops | {} |
| stages[6].operations[17].source_detail.input[0] | 128 |
| stages[6].operations[17].source_detail.input[1] | 12288 |
| stages[6].operations[17].source_detail.weight_math[0] | 12288 |
| stages[6].operations[17].source_detail.weight_math[1] | 4096 |
| stages[6].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[6].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[6].operations[17].source_detail.output[0] | 128 |
| stages[6].operations[17].source_detail.output[1] | 4096 |
| stages[6].operations[18].name | ffn_residual |
| stages[6].operations[18].matrix_flops | 0 |
| stages[6].operations[18].input_precision | unknown (null) |
| stages[6].operations[18].accumulator_precision | unknown (null) |
| stages[6].operations[18].sparsity | unknown (null) |
| stages[6].operations[18].scalar_flops | 524288 |
| stages[6].operations[18].special_ops | {} |
| stages[6].operations[18].source_detail.inputs_each[0] | 128 |
| stages[6].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[6].operations[18].source_detail.output[0] | 128 |
| stages[6].operations[18].source_detail.output[1] | 4096 |
| stages[7].id | layer:6 |
| stages[7].work.vector_fp32 | 17179904 |
| stages[7].work.special:rsqrt | 5376 |
| stages[7].work.interface_bytes | 438387200 |
| stages[7].work.matrix_bf16 | 49527390208 |
| stages[7].work.special:negate | 1900544 |
| stages[7].work.special:exp | 1837056 |
| stages[7].work.special:compare_max | 260096 |
| stages[7].work.special:mask_decisions | 524288 |
| stages[7].operations[0].name | input_layernorm |
| stages[7].operations[0].matrix_flops | 0 |
| stages[7].operations[0].input_precision | unknown (null) |
| stages[7].operations[0].accumulator_precision | unknown (null) |
| stages[7].operations[0].sparsity | unknown (null) |
| stages[7].operations[0].scalar_flops | 2097280 |
| stages[7].operations[0].special_ops.rsqrt | 128 |
| stages[7].operations[0].source_detail.input[0] | 128 |
| stages[7].operations[0].source_detail.input[1] | 4096 |
| stages[7].operations[0].source_detail.weight[0] | 4096 |
| stages[7].operations[0].source_detail.output[0] | 128 |
| stages[7].operations[0].source_detail.output[1] | 4096 |
| stages[7].operations[1].name | q_proj |
| stages[7].operations[1].matrix_flops | 4294967296 |
| stages[7].operations[1].input_precision | BF16 |
| stages[7].operations[1].accumulator_precision | FP32 |
| stages[7].operations[1].sparsity | dense |
| stages[7].operations[1].scalar_flops | 0 |
| stages[7].operations[1].special_ops | {} |
| stages[7].operations[1].source_detail.input[0] | 128 |
| stages[7].operations[1].source_detail.input[1] | 4096 |
| stages[7].operations[1].source_detail.weight_math[0] | 4096 |
| stages[7].operations[1].source_detail.weight_math[1] | 4096 |
| stages[7].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[7].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[1].source_detail.output[0] | 128 |
| stages[7].operations[1].source_detail.output[1] | 4096 |
| stages[7].operations[2].name | k_proj |
| stages[7].operations[2].matrix_flops | 1073741824 |
| stages[7].operations[2].input_precision | BF16 |
| stages[7].operations[2].accumulator_precision | FP32 |
| stages[7].operations[2].sparsity | dense |
| stages[7].operations[2].scalar_flops | 0 |
| stages[7].operations[2].special_ops | {} |
| stages[7].operations[2].source_detail.input[0] | 128 |
| stages[7].operations[2].source_detail.input[1] | 4096 |
| stages[7].operations[2].source_detail.weight_math[0] | 4096 |
| stages[7].operations[2].source_detail.weight_math[1] | 1024 |
| stages[7].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[7].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[2].source_detail.output[0] | 128 |
| stages[7].operations[2].source_detail.output[1] | 1024 |
| stages[7].operations[3].name | v_proj |
| stages[7].operations[3].matrix_flops | 1073741824 |
| stages[7].operations[3].input_precision | BF16 |
| stages[7].operations[3].accumulator_precision | FP32 |
| stages[7].operations[3].sparsity | dense |
| stages[7].operations[3].scalar_flops | 0 |
| stages[7].operations[3].special_ops | {} |
| stages[7].operations[3].source_detail.input[0] | 128 |
| stages[7].operations[3].source_detail.input[1] | 4096 |
| stages[7].operations[3].source_detail.weight_math[0] | 4096 |
| stages[7].operations[3].source_detail.weight_math[1] | 1024 |
| stages[7].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[7].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[3].source_detail.output[0] | 128 |
| stages[7].operations[3].source_detail.output[1] | 1024 |
| stages[7].operations[4].name | q_norm |
| stages[7].operations[4].matrix_flops | 0 |
| stages[7].operations[4].input_precision | unknown (null) |
| stages[7].operations[4].accumulator_precision | unknown (null) |
| stages[7].operations[4].sparsity | unknown (null) |
| stages[7].operations[4].scalar_flops | 2101248 |
| stages[7].operations[4].special_ops.rsqrt | 4096 |
| stages[7].operations[4].source_detail.input[0] | 4096 |
| stages[7].operations[4].source_detail.input[1] | 128 |
| stages[7].operations[4].source_detail.weight[0] | 128 |
| stages[7].operations[4].source_detail.output[0] | 4096 |
| stages[7].operations[4].source_detail.output[1] | 128 |
| stages[7].operations[5].name | k_norm |
| stages[7].operations[5].matrix_flops | 0 |
| stages[7].operations[5].input_precision | unknown (null) |
| stages[7].operations[5].accumulator_precision | unknown (null) |
| stages[7].operations[5].sparsity | unknown (null) |
| stages[7].operations[5].scalar_flops | 525312 |
| stages[7].operations[5].special_ops.rsqrt | 1024 |
| stages[7].operations[5].source_detail.input[0] | 1024 |
| stages[7].operations[5].source_detail.input[1] | 128 |
| stages[7].operations[5].source_detail.weight[0] | 128 |
| stages[7].operations[5].source_detail.output[0] | 1024 |
| stages[7].operations[5].source_detail.output[1] | 128 |
| stages[7].operations[6].name | apply_rope |
| stages[7].operations[6].matrix_flops | 0 |
| stages[7].operations[6].input_precision | unknown (null) |
| stages[7].operations[6].accumulator_precision | unknown (null) |
| stages[7].operations[6].sparsity | unknown (null) |
| stages[7].operations[6].scalar_flops | 1966080 |
| stages[7].operations[6].special_ops.negate | 327680 |
| stages[7].operations[6].source_detail.Q[0] | 1 |
| stages[7].operations[6].source_detail.Q[1] | 32 |
| stages[7].operations[6].source_detail.Q[2] | 128 |
| stages[7].operations[6].source_detail.Q[3] | 128 |
| stages[7].operations[6].source_detail.K[0] | 1 |
| stages[7].operations[6].source_detail.K[1] | 8 |
| stages[7].operations[6].source_detail.K[2] | 128 |
| stages[7].operations[6].source_detail.K[3] | 128 |
| stages[7].operations[7].name | kv_append |
| stages[7].operations[7].matrix_flops | 0 |
| stages[7].operations[7].input_precision | unknown (null) |
| stages[7].operations[7].accumulator_precision | unknown (null) |
| stages[7].operations[7].sparsity | unknown (null) |
| stages[7].operations[7].scalar_flops | 0 |
| stages[7].operations[7].special_ops | {} |
| stages[7].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[7].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[7].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[7].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[7].operations[8].name | qk |
| stages[7].operations[8].matrix_flops | 67633152 |
| stages[7].operations[8].input_precision | BF16 |
| stages[7].operations[8].accumulator_precision | FP32 |
| stages[7].operations[8].sparsity | dense |
| stages[7].operations[8].scalar_flops | 0 |
| stages[7].operations[8].special_ops | {} |
| stages[7].operations[8].source_detail.Q[0] | 1 |
| stages[7].operations[8].source_detail.Q[1] | 32 |
| stages[7].operations[8].source_detail.Q[2] | 128 |
| stages[7].operations[8].source_detail.Q[3] | 128 |
| stages[7].operations[8].source_detail.K_shared[0] | 1 |
| stages[7].operations[8].source_detail.K_shared[1] | 8 |
| stages[7].operations[8].source_detail.K_shared[2] | 128 |
| stages[7].operations[8].source_detail.K_shared[3] | 128 |
| stages[7].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[7].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[7].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[7].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[7].operations[9].name | score_scale_mask_softmax |
| stages[7].operations[9].matrix_flops | 0 |
| stages[7].operations[9].input_precision | unknown (null) |
| stages[7].operations[9].accumulator_precision | unknown (null) |
| stages[7].operations[9].sparsity | unknown (null) |
| stages[7].operations[9].scalar_flops | 1052672 |
| stages[7].operations[9].special_ops.exp | 264192 |
| stages[7].operations[9].special_ops.compare_max | 260096 |
| stages[7].operations[9].special_ops.mask_decisions | 524288 |
| stages[7].operations[9].source_detail.scores[0] | 1 |
| stages[7].operations[9].source_detail.scores[1] | 32 |
| stages[7].operations[9].source_detail.scores[2] | 128 |
| stages[7].operations[9].source_detail.scores[3] | 128 |
| stages[7].operations[10].name | pv |
| stages[7].operations[10].matrix_flops | 67633152 |
| stages[7].operations[10].input_precision | BF16 |
| stages[7].operations[10].accumulator_precision | FP32 |
| stages[7].operations[10].sparsity | dense |
| stages[7].operations[10].scalar_flops | 0 |
| stages[7].operations[10].special_ops | {} |
| stages[7].operations[10].source_detail.P[0] | 1 |
| stages[7].operations[10].source_detail.P[1] | 32 |
| stages[7].operations[10].source_detail.P[2] | 128 |
| stages[7].operations[10].source_detail.P[3] | 128 |
| stages[7].operations[10].source_detail.V_shared[0] | 1 |
| stages[7].operations[10].source_detail.V_shared[1] | 8 |
| stages[7].operations[10].source_detail.V_shared[2] | 128 |
| stages[7].operations[10].source_detail.V_shared[3] | 128 |
| stages[7].operations[10].source_detail.output[0] | 1 |
| stages[7].operations[10].source_detail.output[1] | 32 |
| stages[7].operations[10].source_detail.output[2] | 128 |
| stages[7].operations[10].source_detail.output[3] | 128 |
| stages[7].operations[11].name | o_proj |
| stages[7].operations[11].matrix_flops | 4294967296 |
| stages[7].operations[11].input_precision | BF16 |
| stages[7].operations[11].accumulator_precision | FP32 |
| stages[7].operations[11].sparsity | dense |
| stages[7].operations[11].scalar_flops | 0 |
| stages[7].operations[11].special_ops | {} |
| stages[7].operations[11].source_detail.input[0] | 128 |
| stages[7].operations[11].source_detail.input[1] | 4096 |
| stages[7].operations[11].source_detail.weight_math[0] | 4096 |
| stages[7].operations[11].source_detail.weight_math[1] | 4096 |
| stages[7].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[7].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[11].source_detail.output[0] | 128 |
| stages[7].operations[11].source_detail.output[1] | 4096 |
| stages[7].operations[12].name | attention_residual |
| stages[7].operations[12].matrix_flops | 0 |
| stages[7].operations[12].input_precision | unknown (null) |
| stages[7].operations[12].accumulator_precision | unknown (null) |
| stages[7].operations[12].sparsity | unknown (null) |
| stages[7].operations[12].scalar_flops | 524288 |
| stages[7].operations[12].special_ops | {} |
| stages[7].operations[12].source_detail.inputs_each[0] | 128 |
| stages[7].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[7].operations[12].source_detail.output[0] | 128 |
| stages[7].operations[12].source_detail.output[1] | 4096 |
| stages[7].operations[13].name | post_attention_layernorm |
| stages[7].operations[13].matrix_flops | 0 |
| stages[7].operations[13].input_precision | unknown (null) |
| stages[7].operations[13].accumulator_precision | unknown (null) |
| stages[7].operations[13].sparsity | unknown (null) |
| stages[7].operations[13].scalar_flops | 2097280 |
| stages[7].operations[13].special_ops.rsqrt | 128 |
| stages[7].operations[13].source_detail.input[0] | 128 |
| stages[7].operations[13].source_detail.input[1] | 4096 |
| stages[7].operations[13].source_detail.weight[0] | 4096 |
| stages[7].operations[13].source_detail.output[0] | 128 |
| stages[7].operations[13].source_detail.output[1] | 4096 |
| stages[7].operations[14].name | gate_proj |
| stages[7].operations[14].matrix_flops | 12884901888 |
| stages[7].operations[14].input_precision | BF16 |
| stages[7].operations[14].accumulator_precision | FP32 |
| stages[7].operations[14].sparsity | dense |
| stages[7].operations[14].scalar_flops | 0 |
| stages[7].operations[14].special_ops | {} |
| stages[7].operations[14].source_detail.input[0] | 128 |
| stages[7].operations[14].source_detail.input[1] | 4096 |
| stages[7].operations[14].source_detail.weight_math[0] | 4096 |
| stages[7].operations[14].source_detail.weight_math[1] | 12288 |
| stages[7].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[7].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[14].source_detail.output[0] | 128 |
| stages[7].operations[14].source_detail.output[1] | 12288 |
| stages[7].operations[15].name | up_proj |
| stages[7].operations[15].matrix_flops | 12884901888 |
| stages[7].operations[15].input_precision | BF16 |
| stages[7].operations[15].accumulator_precision | FP32 |
| stages[7].operations[15].sparsity | dense |
| stages[7].operations[15].scalar_flops | 0 |
| stages[7].operations[15].special_ops | {} |
| stages[7].operations[15].source_detail.input[0] | 128 |
| stages[7].operations[15].source_detail.input[1] | 4096 |
| stages[7].operations[15].source_detail.weight_math[0] | 4096 |
| stages[7].operations[15].source_detail.weight_math[1] | 12288 |
| stages[7].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[7].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[7].operations[15].source_detail.output[0] | 128 |
| stages[7].operations[15].source_detail.output[1] | 12288 |
| stages[7].operations[16].name | silu_mul |
| stages[7].operations[16].matrix_flops | 0 |
| stages[7].operations[16].input_precision | unknown (null) |
| stages[7].operations[16].accumulator_precision | unknown (null) |
| stages[7].operations[16].sparsity | unknown (null) |
| stages[7].operations[16].scalar_flops | 6291456 |
| stages[7].operations[16].special_ops.exp | 1572864 |
| stages[7].operations[16].special_ops.negate | 1572864 |
| stages[7].operations[16].source_detail.gate[0] | 128 |
| stages[7].operations[16].source_detail.gate[1] | 12288 |
| stages[7].operations[16].source_detail.up[0] | 128 |
| stages[7].operations[16].source_detail.up[1] | 12288 |
| stages[7].operations[16].source_detail.output[0] | 128 |
| stages[7].operations[16].source_detail.output[1] | 12288 |
| stages[7].operations[17].name | down_proj |
| stages[7].operations[17].matrix_flops | 12884901888 |
| stages[7].operations[17].input_precision | BF16 |
| stages[7].operations[17].accumulator_precision | FP32 |
| stages[7].operations[17].sparsity | dense |
| stages[7].operations[17].scalar_flops | 0 |
| stages[7].operations[17].special_ops | {} |
| stages[7].operations[17].source_detail.input[0] | 128 |
| stages[7].operations[17].source_detail.input[1] | 12288 |
| stages[7].operations[17].source_detail.weight_math[0] | 12288 |
| stages[7].operations[17].source_detail.weight_math[1] | 4096 |
| stages[7].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[7].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[7].operations[17].source_detail.output[0] | 128 |
| stages[7].operations[17].source_detail.output[1] | 4096 |
| stages[7].operations[18].name | ffn_residual |
| stages[7].operations[18].matrix_flops | 0 |
| stages[7].operations[18].input_precision | unknown (null) |
| stages[7].operations[18].accumulator_precision | unknown (null) |
| stages[7].operations[18].sparsity | unknown (null) |
| stages[7].operations[18].scalar_flops | 524288 |
| stages[7].operations[18].special_ops | {} |
| stages[7].operations[18].source_detail.inputs_each[0] | 128 |
| stages[7].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[7].operations[18].source_detail.output[0] | 128 |
| stages[7].operations[18].source_detail.output[1] | 4096 |
| stages[8].id | layer:7 |
| stages[8].work.vector_fp32 | 17179904 |
| stages[8].work.special:rsqrt | 5376 |
| stages[8].work.interface_bytes | 438387200 |
| stages[8].work.matrix_bf16 | 49527390208 |
| stages[8].work.special:negate | 1900544 |
| stages[8].work.special:exp | 1837056 |
| stages[8].work.special:compare_max | 260096 |
| stages[8].work.special:mask_decisions | 524288 |
| stages[8].operations[0].name | input_layernorm |
| stages[8].operations[0].matrix_flops | 0 |
| stages[8].operations[0].input_precision | unknown (null) |
| stages[8].operations[0].accumulator_precision | unknown (null) |
| stages[8].operations[0].sparsity | unknown (null) |
| stages[8].operations[0].scalar_flops | 2097280 |
| stages[8].operations[0].special_ops.rsqrt | 128 |
| stages[8].operations[0].source_detail.input[0] | 128 |
| stages[8].operations[0].source_detail.input[1] | 4096 |
| stages[8].operations[0].source_detail.weight[0] | 4096 |
| stages[8].operations[0].source_detail.output[0] | 128 |
| stages[8].operations[0].source_detail.output[1] | 4096 |
| stages[8].operations[1].name | q_proj |
| stages[8].operations[1].matrix_flops | 4294967296 |
| stages[8].operations[1].input_precision | BF16 |
| stages[8].operations[1].accumulator_precision | FP32 |
| stages[8].operations[1].sparsity | dense |
| stages[8].operations[1].scalar_flops | 0 |
| stages[8].operations[1].special_ops | {} |
| stages[8].operations[1].source_detail.input[0] | 128 |
| stages[8].operations[1].source_detail.input[1] | 4096 |
| stages[8].operations[1].source_detail.weight_math[0] | 4096 |
| stages[8].operations[1].source_detail.weight_math[1] | 4096 |
| stages[8].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[8].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[1].source_detail.output[0] | 128 |
| stages[8].operations[1].source_detail.output[1] | 4096 |
| stages[8].operations[2].name | k_proj |
| stages[8].operations[2].matrix_flops | 1073741824 |
| stages[8].operations[2].input_precision | BF16 |
| stages[8].operations[2].accumulator_precision | FP32 |
| stages[8].operations[2].sparsity | dense |
| stages[8].operations[2].scalar_flops | 0 |
| stages[8].operations[2].special_ops | {} |
| stages[8].operations[2].source_detail.input[0] | 128 |
| stages[8].operations[2].source_detail.input[1] | 4096 |
| stages[8].operations[2].source_detail.weight_math[0] | 4096 |
| stages[8].operations[2].source_detail.weight_math[1] | 1024 |
| stages[8].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[8].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[2].source_detail.output[0] | 128 |
| stages[8].operations[2].source_detail.output[1] | 1024 |
| stages[8].operations[3].name | v_proj |
| stages[8].operations[3].matrix_flops | 1073741824 |
| stages[8].operations[3].input_precision | BF16 |
| stages[8].operations[3].accumulator_precision | FP32 |
| stages[8].operations[3].sparsity | dense |
| stages[8].operations[3].scalar_flops | 0 |
| stages[8].operations[3].special_ops | {} |
| stages[8].operations[3].source_detail.input[0] | 128 |
| stages[8].operations[3].source_detail.input[1] | 4096 |
| stages[8].operations[3].source_detail.weight_math[0] | 4096 |
| stages[8].operations[3].source_detail.weight_math[1] | 1024 |
| stages[8].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[8].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[3].source_detail.output[0] | 128 |
| stages[8].operations[3].source_detail.output[1] | 1024 |
| stages[8].operations[4].name | q_norm |
| stages[8].operations[4].matrix_flops | 0 |
| stages[8].operations[4].input_precision | unknown (null) |
| stages[8].operations[4].accumulator_precision | unknown (null) |
| stages[8].operations[4].sparsity | unknown (null) |
| stages[8].operations[4].scalar_flops | 2101248 |
| stages[8].operations[4].special_ops.rsqrt | 4096 |
| stages[8].operations[4].source_detail.input[0] | 4096 |
| stages[8].operations[4].source_detail.input[1] | 128 |
| stages[8].operations[4].source_detail.weight[0] | 128 |
| stages[8].operations[4].source_detail.output[0] | 4096 |
| stages[8].operations[4].source_detail.output[1] | 128 |
| stages[8].operations[5].name | k_norm |
| stages[8].operations[5].matrix_flops | 0 |
| stages[8].operations[5].input_precision | unknown (null) |
| stages[8].operations[5].accumulator_precision | unknown (null) |
| stages[8].operations[5].sparsity | unknown (null) |
| stages[8].operations[5].scalar_flops | 525312 |
| stages[8].operations[5].special_ops.rsqrt | 1024 |
| stages[8].operations[5].source_detail.input[0] | 1024 |
| stages[8].operations[5].source_detail.input[1] | 128 |
| stages[8].operations[5].source_detail.weight[0] | 128 |
| stages[8].operations[5].source_detail.output[0] | 1024 |
| stages[8].operations[5].source_detail.output[1] | 128 |
| stages[8].operations[6].name | apply_rope |
| stages[8].operations[6].matrix_flops | 0 |
| stages[8].operations[6].input_precision | unknown (null) |
| stages[8].operations[6].accumulator_precision | unknown (null) |
| stages[8].operations[6].sparsity | unknown (null) |
| stages[8].operations[6].scalar_flops | 1966080 |
| stages[8].operations[6].special_ops.negate | 327680 |
| stages[8].operations[6].source_detail.Q[0] | 1 |
| stages[8].operations[6].source_detail.Q[1] | 32 |
| stages[8].operations[6].source_detail.Q[2] | 128 |
| stages[8].operations[6].source_detail.Q[3] | 128 |
| stages[8].operations[6].source_detail.K[0] | 1 |
| stages[8].operations[6].source_detail.K[1] | 8 |
| stages[8].operations[6].source_detail.K[2] | 128 |
| stages[8].operations[6].source_detail.K[3] | 128 |
| stages[8].operations[7].name | kv_append |
| stages[8].operations[7].matrix_flops | 0 |
| stages[8].operations[7].input_precision | unknown (null) |
| stages[8].operations[7].accumulator_precision | unknown (null) |
| stages[8].operations[7].sparsity | unknown (null) |
| stages[8].operations[7].scalar_flops | 0 |
| stages[8].operations[7].special_ops | {} |
| stages[8].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[8].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[8].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[8].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[8].operations[8].name | qk |
| stages[8].operations[8].matrix_flops | 67633152 |
| stages[8].operations[8].input_precision | BF16 |
| stages[8].operations[8].accumulator_precision | FP32 |
| stages[8].operations[8].sparsity | dense |
| stages[8].operations[8].scalar_flops | 0 |
| stages[8].operations[8].special_ops | {} |
| stages[8].operations[8].source_detail.Q[0] | 1 |
| stages[8].operations[8].source_detail.Q[1] | 32 |
| stages[8].operations[8].source_detail.Q[2] | 128 |
| stages[8].operations[8].source_detail.Q[3] | 128 |
| stages[8].operations[8].source_detail.K_shared[0] | 1 |
| stages[8].operations[8].source_detail.K_shared[1] | 8 |
| stages[8].operations[8].source_detail.K_shared[2] | 128 |
| stages[8].operations[8].source_detail.K_shared[3] | 128 |
| stages[8].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[8].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[8].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[8].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[8].operations[9].name | score_scale_mask_softmax |
| stages[8].operations[9].matrix_flops | 0 |
| stages[8].operations[9].input_precision | unknown (null) |
| stages[8].operations[9].accumulator_precision | unknown (null) |
| stages[8].operations[9].sparsity | unknown (null) |
| stages[8].operations[9].scalar_flops | 1052672 |
| stages[8].operations[9].special_ops.exp | 264192 |
| stages[8].operations[9].special_ops.compare_max | 260096 |
| stages[8].operations[9].special_ops.mask_decisions | 524288 |
| stages[8].operations[9].source_detail.scores[0] | 1 |
| stages[8].operations[9].source_detail.scores[1] | 32 |
| stages[8].operations[9].source_detail.scores[2] | 128 |
| stages[8].operations[9].source_detail.scores[3] | 128 |
| stages[8].operations[10].name | pv |
| stages[8].operations[10].matrix_flops | 67633152 |
| stages[8].operations[10].input_precision | BF16 |
| stages[8].operations[10].accumulator_precision | FP32 |
| stages[8].operations[10].sparsity | dense |
| stages[8].operations[10].scalar_flops | 0 |
| stages[8].operations[10].special_ops | {} |
| stages[8].operations[10].source_detail.P[0] | 1 |
| stages[8].operations[10].source_detail.P[1] | 32 |
| stages[8].operations[10].source_detail.P[2] | 128 |
| stages[8].operations[10].source_detail.P[3] | 128 |
| stages[8].operations[10].source_detail.V_shared[0] | 1 |
| stages[8].operations[10].source_detail.V_shared[1] | 8 |
| stages[8].operations[10].source_detail.V_shared[2] | 128 |
| stages[8].operations[10].source_detail.V_shared[3] | 128 |
| stages[8].operations[10].source_detail.output[0] | 1 |
| stages[8].operations[10].source_detail.output[1] | 32 |
| stages[8].operations[10].source_detail.output[2] | 128 |
| stages[8].operations[10].source_detail.output[3] | 128 |
| stages[8].operations[11].name | o_proj |
| stages[8].operations[11].matrix_flops | 4294967296 |
| stages[8].operations[11].input_precision | BF16 |
| stages[8].operations[11].accumulator_precision | FP32 |
| stages[8].operations[11].sparsity | dense |
| stages[8].operations[11].scalar_flops | 0 |
| stages[8].operations[11].special_ops | {} |
| stages[8].operations[11].source_detail.input[0] | 128 |
| stages[8].operations[11].source_detail.input[1] | 4096 |
| stages[8].operations[11].source_detail.weight_math[0] | 4096 |
| stages[8].operations[11].source_detail.weight_math[1] | 4096 |
| stages[8].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[8].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[11].source_detail.output[0] | 128 |
| stages[8].operations[11].source_detail.output[1] | 4096 |
| stages[8].operations[12].name | attention_residual |
| stages[8].operations[12].matrix_flops | 0 |
| stages[8].operations[12].input_precision | unknown (null) |
| stages[8].operations[12].accumulator_precision | unknown (null) |
| stages[8].operations[12].sparsity | unknown (null) |
| stages[8].operations[12].scalar_flops | 524288 |
| stages[8].operations[12].special_ops | {} |
| stages[8].operations[12].source_detail.inputs_each[0] | 128 |
| stages[8].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[8].operations[12].source_detail.output[0] | 128 |
| stages[8].operations[12].source_detail.output[1] | 4096 |
| stages[8].operations[13].name | post_attention_layernorm |
| stages[8].operations[13].matrix_flops | 0 |
| stages[8].operations[13].input_precision | unknown (null) |
| stages[8].operations[13].accumulator_precision | unknown (null) |
| stages[8].operations[13].sparsity | unknown (null) |
| stages[8].operations[13].scalar_flops | 2097280 |
| stages[8].operations[13].special_ops.rsqrt | 128 |
| stages[8].operations[13].source_detail.input[0] | 128 |
| stages[8].operations[13].source_detail.input[1] | 4096 |
| stages[8].operations[13].source_detail.weight[0] | 4096 |
| stages[8].operations[13].source_detail.output[0] | 128 |
| stages[8].operations[13].source_detail.output[1] | 4096 |
| stages[8].operations[14].name | gate_proj |
| stages[8].operations[14].matrix_flops | 12884901888 |
| stages[8].operations[14].input_precision | BF16 |
| stages[8].operations[14].accumulator_precision | FP32 |
| stages[8].operations[14].sparsity | dense |
| stages[8].operations[14].scalar_flops | 0 |
| stages[8].operations[14].special_ops | {} |
| stages[8].operations[14].source_detail.input[0] | 128 |
| stages[8].operations[14].source_detail.input[1] | 4096 |
| stages[8].operations[14].source_detail.weight_math[0] | 4096 |
| stages[8].operations[14].source_detail.weight_math[1] | 12288 |
| stages[8].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[8].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[14].source_detail.output[0] | 128 |
| stages[8].operations[14].source_detail.output[1] | 12288 |
| stages[8].operations[15].name | up_proj |
| stages[8].operations[15].matrix_flops | 12884901888 |
| stages[8].operations[15].input_precision | BF16 |
| stages[8].operations[15].accumulator_precision | FP32 |
| stages[8].operations[15].sparsity | dense |
| stages[8].operations[15].scalar_flops | 0 |
| stages[8].operations[15].special_ops | {} |
| stages[8].operations[15].source_detail.input[0] | 128 |
| stages[8].operations[15].source_detail.input[1] | 4096 |
| stages[8].operations[15].source_detail.weight_math[0] | 4096 |
| stages[8].operations[15].source_detail.weight_math[1] | 12288 |
| stages[8].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[8].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[8].operations[15].source_detail.output[0] | 128 |
| stages[8].operations[15].source_detail.output[1] | 12288 |
| stages[8].operations[16].name | silu_mul |
| stages[8].operations[16].matrix_flops | 0 |
| stages[8].operations[16].input_precision | unknown (null) |
| stages[8].operations[16].accumulator_precision | unknown (null) |
| stages[8].operations[16].sparsity | unknown (null) |
| stages[8].operations[16].scalar_flops | 6291456 |
| stages[8].operations[16].special_ops.exp | 1572864 |
| stages[8].operations[16].special_ops.negate | 1572864 |
| stages[8].operations[16].source_detail.gate[0] | 128 |
| stages[8].operations[16].source_detail.gate[1] | 12288 |
| stages[8].operations[16].source_detail.up[0] | 128 |
| stages[8].operations[16].source_detail.up[1] | 12288 |
| stages[8].operations[16].source_detail.output[0] | 128 |
| stages[8].operations[16].source_detail.output[1] | 12288 |
| stages[8].operations[17].name | down_proj |
| stages[8].operations[17].matrix_flops | 12884901888 |
| stages[8].operations[17].input_precision | BF16 |
| stages[8].operations[17].accumulator_precision | FP32 |
| stages[8].operations[17].sparsity | dense |
| stages[8].operations[17].scalar_flops | 0 |
| stages[8].operations[17].special_ops | {} |
| stages[8].operations[17].source_detail.input[0] | 128 |
| stages[8].operations[17].source_detail.input[1] | 12288 |
| stages[8].operations[17].source_detail.weight_math[0] | 12288 |
| stages[8].operations[17].source_detail.weight_math[1] | 4096 |
| stages[8].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[8].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[8].operations[17].source_detail.output[0] | 128 |
| stages[8].operations[17].source_detail.output[1] | 4096 |
| stages[8].operations[18].name | ffn_residual |
| stages[8].operations[18].matrix_flops | 0 |
| stages[8].operations[18].input_precision | unknown (null) |
| stages[8].operations[18].accumulator_precision | unknown (null) |
| stages[8].operations[18].sparsity | unknown (null) |
| stages[8].operations[18].scalar_flops | 524288 |
| stages[8].operations[18].special_ops | {} |
| stages[8].operations[18].source_detail.inputs_each[0] | 128 |
| stages[8].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[8].operations[18].source_detail.output[0] | 128 |
| stages[8].operations[18].source_detail.output[1] | 4096 |
| stages[9].id | layer:8 |
| stages[9].work.vector_fp32 | 17179904 |
| stages[9].work.special:rsqrt | 5376 |
| stages[9].work.interface_bytes | 438387200 |
| stages[9].work.matrix_bf16 | 49527390208 |
| stages[9].work.special:negate | 1900544 |
| stages[9].work.special:exp | 1837056 |
| stages[9].work.special:compare_max | 260096 |
| stages[9].work.special:mask_decisions | 524288 |
| stages[9].operations[0].name | input_layernorm |
| stages[9].operations[0].matrix_flops | 0 |
| stages[9].operations[0].input_precision | unknown (null) |
| stages[9].operations[0].accumulator_precision | unknown (null) |
| stages[9].operations[0].sparsity | unknown (null) |
| stages[9].operations[0].scalar_flops | 2097280 |
| stages[9].operations[0].special_ops.rsqrt | 128 |
| stages[9].operations[0].source_detail.input[0] | 128 |
| stages[9].operations[0].source_detail.input[1] | 4096 |
| stages[9].operations[0].source_detail.weight[0] | 4096 |
| stages[9].operations[0].source_detail.output[0] | 128 |
| stages[9].operations[0].source_detail.output[1] | 4096 |
| stages[9].operations[1].name | q_proj |
| stages[9].operations[1].matrix_flops | 4294967296 |
| stages[9].operations[1].input_precision | BF16 |
| stages[9].operations[1].accumulator_precision | FP32 |
| stages[9].operations[1].sparsity | dense |
| stages[9].operations[1].scalar_flops | 0 |
| stages[9].operations[1].special_ops | {} |
| stages[9].operations[1].source_detail.input[0] | 128 |
| stages[9].operations[1].source_detail.input[1] | 4096 |
| stages[9].operations[1].source_detail.weight_math[0] | 4096 |
| stages[9].operations[1].source_detail.weight_math[1] | 4096 |
| stages[9].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[9].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[1].source_detail.output[0] | 128 |
| stages[9].operations[1].source_detail.output[1] | 4096 |
| stages[9].operations[2].name | k_proj |
| stages[9].operations[2].matrix_flops | 1073741824 |
| stages[9].operations[2].input_precision | BF16 |
| stages[9].operations[2].accumulator_precision | FP32 |
| stages[9].operations[2].sparsity | dense |
| stages[9].operations[2].scalar_flops | 0 |
| stages[9].operations[2].special_ops | {} |
| stages[9].operations[2].source_detail.input[0] | 128 |
| stages[9].operations[2].source_detail.input[1] | 4096 |
| stages[9].operations[2].source_detail.weight_math[0] | 4096 |
| stages[9].operations[2].source_detail.weight_math[1] | 1024 |
| stages[9].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[9].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[2].source_detail.output[0] | 128 |
| stages[9].operations[2].source_detail.output[1] | 1024 |
| stages[9].operations[3].name | v_proj |
| stages[9].operations[3].matrix_flops | 1073741824 |
| stages[9].operations[3].input_precision | BF16 |
| stages[9].operations[3].accumulator_precision | FP32 |
| stages[9].operations[3].sparsity | dense |
| stages[9].operations[3].scalar_flops | 0 |
| stages[9].operations[3].special_ops | {} |
| stages[9].operations[3].source_detail.input[0] | 128 |
| stages[9].operations[3].source_detail.input[1] | 4096 |
| stages[9].operations[3].source_detail.weight_math[0] | 4096 |
| stages[9].operations[3].source_detail.weight_math[1] | 1024 |
| stages[9].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[9].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[3].source_detail.output[0] | 128 |
| stages[9].operations[3].source_detail.output[1] | 1024 |
| stages[9].operations[4].name | q_norm |
| stages[9].operations[4].matrix_flops | 0 |
| stages[9].operations[4].input_precision | unknown (null) |
| stages[9].operations[4].accumulator_precision | unknown (null) |
| stages[9].operations[4].sparsity | unknown (null) |
| stages[9].operations[4].scalar_flops | 2101248 |
| stages[9].operations[4].special_ops.rsqrt | 4096 |
| stages[9].operations[4].source_detail.input[0] | 4096 |
| stages[9].operations[4].source_detail.input[1] | 128 |
| stages[9].operations[4].source_detail.weight[0] | 128 |
| stages[9].operations[4].source_detail.output[0] | 4096 |
| stages[9].operations[4].source_detail.output[1] | 128 |
| stages[9].operations[5].name | k_norm |
| stages[9].operations[5].matrix_flops | 0 |
| stages[9].operations[5].input_precision | unknown (null) |
| stages[9].operations[5].accumulator_precision | unknown (null) |
| stages[9].operations[5].sparsity | unknown (null) |
| stages[9].operations[5].scalar_flops | 525312 |
| stages[9].operations[5].special_ops.rsqrt | 1024 |
| stages[9].operations[5].source_detail.input[0] | 1024 |
| stages[9].operations[5].source_detail.input[1] | 128 |
| stages[9].operations[5].source_detail.weight[0] | 128 |
| stages[9].operations[5].source_detail.output[0] | 1024 |
| stages[9].operations[5].source_detail.output[1] | 128 |
| stages[9].operations[6].name | apply_rope |
| stages[9].operations[6].matrix_flops | 0 |
| stages[9].operations[6].input_precision | unknown (null) |
| stages[9].operations[6].accumulator_precision | unknown (null) |
| stages[9].operations[6].sparsity | unknown (null) |
| stages[9].operations[6].scalar_flops | 1966080 |
| stages[9].operations[6].special_ops.negate | 327680 |
| stages[9].operations[6].source_detail.Q[0] | 1 |
| stages[9].operations[6].source_detail.Q[1] | 32 |
| stages[9].operations[6].source_detail.Q[2] | 128 |
| stages[9].operations[6].source_detail.Q[3] | 128 |
| stages[9].operations[6].source_detail.K[0] | 1 |
| stages[9].operations[6].source_detail.K[1] | 8 |
| stages[9].operations[6].source_detail.K[2] | 128 |
| stages[9].operations[6].source_detail.K[3] | 128 |
| stages[9].operations[7].name | kv_append |
| stages[9].operations[7].matrix_flops | 0 |
| stages[9].operations[7].input_precision | unknown (null) |
| stages[9].operations[7].accumulator_precision | unknown (null) |
| stages[9].operations[7].sparsity | unknown (null) |
| stages[9].operations[7].scalar_flops | 0 |
| stages[9].operations[7].special_ops | {} |
| stages[9].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[9].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[9].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[9].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[9].operations[8].name | qk |
| stages[9].operations[8].matrix_flops | 67633152 |
| stages[9].operations[8].input_precision | BF16 |
| stages[9].operations[8].accumulator_precision | FP32 |
| stages[9].operations[8].sparsity | dense |
| stages[9].operations[8].scalar_flops | 0 |
| stages[9].operations[8].special_ops | {} |
| stages[9].operations[8].source_detail.Q[0] | 1 |
| stages[9].operations[8].source_detail.Q[1] | 32 |
| stages[9].operations[8].source_detail.Q[2] | 128 |
| stages[9].operations[8].source_detail.Q[3] | 128 |
| stages[9].operations[8].source_detail.K_shared[0] | 1 |
| stages[9].operations[8].source_detail.K_shared[1] | 8 |
| stages[9].operations[8].source_detail.K_shared[2] | 128 |
| stages[9].operations[8].source_detail.K_shared[3] | 128 |
| stages[9].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[9].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[9].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[9].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[9].operations[9].name | score_scale_mask_softmax |
| stages[9].operations[9].matrix_flops | 0 |
| stages[9].operations[9].input_precision | unknown (null) |
| stages[9].operations[9].accumulator_precision | unknown (null) |
| stages[9].operations[9].sparsity | unknown (null) |
| stages[9].operations[9].scalar_flops | 1052672 |
| stages[9].operations[9].special_ops.exp | 264192 |
| stages[9].operations[9].special_ops.compare_max | 260096 |
| stages[9].operations[9].special_ops.mask_decisions | 524288 |
| stages[9].operations[9].source_detail.scores[0] | 1 |
| stages[9].operations[9].source_detail.scores[1] | 32 |
| stages[9].operations[9].source_detail.scores[2] | 128 |
| stages[9].operations[9].source_detail.scores[3] | 128 |
| stages[9].operations[10].name | pv |
| stages[9].operations[10].matrix_flops | 67633152 |
| stages[9].operations[10].input_precision | BF16 |
| stages[9].operations[10].accumulator_precision | FP32 |
| stages[9].operations[10].sparsity | dense |
| stages[9].operations[10].scalar_flops | 0 |
| stages[9].operations[10].special_ops | {} |
| stages[9].operations[10].source_detail.P[0] | 1 |
| stages[9].operations[10].source_detail.P[1] | 32 |
| stages[9].operations[10].source_detail.P[2] | 128 |
| stages[9].operations[10].source_detail.P[3] | 128 |
| stages[9].operations[10].source_detail.V_shared[0] | 1 |
| stages[9].operations[10].source_detail.V_shared[1] | 8 |
| stages[9].operations[10].source_detail.V_shared[2] | 128 |
| stages[9].operations[10].source_detail.V_shared[3] | 128 |
| stages[9].operations[10].source_detail.output[0] | 1 |
| stages[9].operations[10].source_detail.output[1] | 32 |
| stages[9].operations[10].source_detail.output[2] | 128 |
| stages[9].operations[10].source_detail.output[3] | 128 |
| stages[9].operations[11].name | o_proj |
| stages[9].operations[11].matrix_flops | 4294967296 |
| stages[9].operations[11].input_precision | BF16 |
| stages[9].operations[11].accumulator_precision | FP32 |
| stages[9].operations[11].sparsity | dense |
| stages[9].operations[11].scalar_flops | 0 |
| stages[9].operations[11].special_ops | {} |
| stages[9].operations[11].source_detail.input[0] | 128 |
| stages[9].operations[11].source_detail.input[1] | 4096 |
| stages[9].operations[11].source_detail.weight_math[0] | 4096 |
| stages[9].operations[11].source_detail.weight_math[1] | 4096 |
| stages[9].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[9].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[11].source_detail.output[0] | 128 |
| stages[9].operations[11].source_detail.output[1] | 4096 |
| stages[9].operations[12].name | attention_residual |
| stages[9].operations[12].matrix_flops | 0 |
| stages[9].operations[12].input_precision | unknown (null) |
| stages[9].operations[12].accumulator_precision | unknown (null) |
| stages[9].operations[12].sparsity | unknown (null) |
| stages[9].operations[12].scalar_flops | 524288 |
| stages[9].operations[12].special_ops | {} |
| stages[9].operations[12].source_detail.inputs_each[0] | 128 |
| stages[9].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[9].operations[12].source_detail.output[0] | 128 |
| stages[9].operations[12].source_detail.output[1] | 4096 |
| stages[9].operations[13].name | post_attention_layernorm |
| stages[9].operations[13].matrix_flops | 0 |
| stages[9].operations[13].input_precision | unknown (null) |
| stages[9].operations[13].accumulator_precision | unknown (null) |
| stages[9].operations[13].sparsity | unknown (null) |
| stages[9].operations[13].scalar_flops | 2097280 |
| stages[9].operations[13].special_ops.rsqrt | 128 |
| stages[9].operations[13].source_detail.input[0] | 128 |
| stages[9].operations[13].source_detail.input[1] | 4096 |
| stages[9].operations[13].source_detail.weight[0] | 4096 |
| stages[9].operations[13].source_detail.output[0] | 128 |
| stages[9].operations[13].source_detail.output[1] | 4096 |
| stages[9].operations[14].name | gate_proj |
| stages[9].operations[14].matrix_flops | 12884901888 |
| stages[9].operations[14].input_precision | BF16 |
| stages[9].operations[14].accumulator_precision | FP32 |
| stages[9].operations[14].sparsity | dense |
| stages[9].operations[14].scalar_flops | 0 |
| stages[9].operations[14].special_ops | {} |
| stages[9].operations[14].source_detail.input[0] | 128 |
| stages[9].operations[14].source_detail.input[1] | 4096 |
| stages[9].operations[14].source_detail.weight_math[0] | 4096 |
| stages[9].operations[14].source_detail.weight_math[1] | 12288 |
| stages[9].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[9].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[14].source_detail.output[0] | 128 |
| stages[9].operations[14].source_detail.output[1] | 12288 |
| stages[9].operations[15].name | up_proj |
| stages[9].operations[15].matrix_flops | 12884901888 |
| stages[9].operations[15].input_precision | BF16 |
| stages[9].operations[15].accumulator_precision | FP32 |
| stages[9].operations[15].sparsity | dense |
| stages[9].operations[15].scalar_flops | 0 |
| stages[9].operations[15].special_ops | {} |
| stages[9].operations[15].source_detail.input[0] | 128 |
| stages[9].operations[15].source_detail.input[1] | 4096 |
| stages[9].operations[15].source_detail.weight_math[0] | 4096 |
| stages[9].operations[15].source_detail.weight_math[1] | 12288 |
| stages[9].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[9].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[9].operations[15].source_detail.output[0] | 128 |
| stages[9].operations[15].source_detail.output[1] | 12288 |
| stages[9].operations[16].name | silu_mul |
| stages[9].operations[16].matrix_flops | 0 |
| stages[9].operations[16].input_precision | unknown (null) |
| stages[9].operations[16].accumulator_precision | unknown (null) |
| stages[9].operations[16].sparsity | unknown (null) |
| stages[9].operations[16].scalar_flops | 6291456 |
| stages[9].operations[16].special_ops.exp | 1572864 |
| stages[9].operations[16].special_ops.negate | 1572864 |
| stages[9].operations[16].source_detail.gate[0] | 128 |
| stages[9].operations[16].source_detail.gate[1] | 12288 |
| stages[9].operations[16].source_detail.up[0] | 128 |
| stages[9].operations[16].source_detail.up[1] | 12288 |
| stages[9].operations[16].source_detail.output[0] | 128 |
| stages[9].operations[16].source_detail.output[1] | 12288 |
| stages[9].operations[17].name | down_proj |
| stages[9].operations[17].matrix_flops | 12884901888 |
| stages[9].operations[17].input_precision | BF16 |
| stages[9].operations[17].accumulator_precision | FP32 |
| stages[9].operations[17].sparsity | dense |
| stages[9].operations[17].scalar_flops | 0 |
| stages[9].operations[17].special_ops | {} |
| stages[9].operations[17].source_detail.input[0] | 128 |
| stages[9].operations[17].source_detail.input[1] | 12288 |
| stages[9].operations[17].source_detail.weight_math[0] | 12288 |
| stages[9].operations[17].source_detail.weight_math[1] | 4096 |
| stages[9].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[9].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[9].operations[17].source_detail.output[0] | 128 |
| stages[9].operations[17].source_detail.output[1] | 4096 |
| stages[9].operations[18].name | ffn_residual |
| stages[9].operations[18].matrix_flops | 0 |
| stages[9].operations[18].input_precision | unknown (null) |
| stages[9].operations[18].accumulator_precision | unknown (null) |
| stages[9].operations[18].sparsity | unknown (null) |
| stages[9].operations[18].scalar_flops | 524288 |
| stages[9].operations[18].special_ops | {} |
| stages[9].operations[18].source_detail.inputs_each[0] | 128 |
| stages[9].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[9].operations[18].source_detail.output[0] | 128 |
| stages[9].operations[18].source_detail.output[1] | 4096 |
| stages[10].id | layer:9 |
| stages[10].work.vector_fp32 | 17179904 |
| stages[10].work.special:rsqrt | 5376 |
| stages[10].work.interface_bytes | 438387200 |
| stages[10].work.matrix_bf16 | 49527390208 |
| stages[10].work.special:negate | 1900544 |
| stages[10].work.special:exp | 1837056 |
| stages[10].work.special:compare_max | 260096 |
| stages[10].work.special:mask_decisions | 524288 |
| stages[10].operations[0].name | input_layernorm |
| stages[10].operations[0].matrix_flops | 0 |
| stages[10].operations[0].input_precision | unknown (null) |
| stages[10].operations[0].accumulator_precision | unknown (null) |
| stages[10].operations[0].sparsity | unknown (null) |
| stages[10].operations[0].scalar_flops | 2097280 |
| stages[10].operations[0].special_ops.rsqrt | 128 |
| stages[10].operations[0].source_detail.input[0] | 128 |
| stages[10].operations[0].source_detail.input[1] | 4096 |
| stages[10].operations[0].source_detail.weight[0] | 4096 |
| stages[10].operations[0].source_detail.output[0] | 128 |
| stages[10].operations[0].source_detail.output[1] | 4096 |
| stages[10].operations[1].name | q_proj |
| stages[10].operations[1].matrix_flops | 4294967296 |
| stages[10].operations[1].input_precision | BF16 |
| stages[10].operations[1].accumulator_precision | FP32 |
| stages[10].operations[1].sparsity | dense |
| stages[10].operations[1].scalar_flops | 0 |
| stages[10].operations[1].special_ops | {} |
| stages[10].operations[1].source_detail.input[0] | 128 |
| stages[10].operations[1].source_detail.input[1] | 4096 |
| stages[10].operations[1].source_detail.weight_math[0] | 4096 |
| stages[10].operations[1].source_detail.weight_math[1] | 4096 |
| stages[10].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[10].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[1].source_detail.output[0] | 128 |
| stages[10].operations[1].source_detail.output[1] | 4096 |
| stages[10].operations[2].name | k_proj |
| stages[10].operations[2].matrix_flops | 1073741824 |
| stages[10].operations[2].input_precision | BF16 |
| stages[10].operations[2].accumulator_precision | FP32 |
| stages[10].operations[2].sparsity | dense |
| stages[10].operations[2].scalar_flops | 0 |
| stages[10].operations[2].special_ops | {} |
| stages[10].operations[2].source_detail.input[0] | 128 |
| stages[10].operations[2].source_detail.input[1] | 4096 |
| stages[10].operations[2].source_detail.weight_math[0] | 4096 |
| stages[10].operations[2].source_detail.weight_math[1] | 1024 |
| stages[10].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[10].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[2].source_detail.output[0] | 128 |
| stages[10].operations[2].source_detail.output[1] | 1024 |
| stages[10].operations[3].name | v_proj |
| stages[10].operations[3].matrix_flops | 1073741824 |
| stages[10].operations[3].input_precision | BF16 |
| stages[10].operations[3].accumulator_precision | FP32 |
| stages[10].operations[3].sparsity | dense |
| stages[10].operations[3].scalar_flops | 0 |
| stages[10].operations[3].special_ops | {} |
| stages[10].operations[3].source_detail.input[0] | 128 |
| stages[10].operations[3].source_detail.input[1] | 4096 |
| stages[10].operations[3].source_detail.weight_math[0] | 4096 |
| stages[10].operations[3].source_detail.weight_math[1] | 1024 |
| stages[10].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[10].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[3].source_detail.output[0] | 128 |
| stages[10].operations[3].source_detail.output[1] | 1024 |
| stages[10].operations[4].name | q_norm |
| stages[10].operations[4].matrix_flops | 0 |
| stages[10].operations[4].input_precision | unknown (null) |
| stages[10].operations[4].accumulator_precision | unknown (null) |
| stages[10].operations[4].sparsity | unknown (null) |
| stages[10].operations[4].scalar_flops | 2101248 |
| stages[10].operations[4].special_ops.rsqrt | 4096 |
| stages[10].operations[4].source_detail.input[0] | 4096 |
| stages[10].operations[4].source_detail.input[1] | 128 |
| stages[10].operations[4].source_detail.weight[0] | 128 |
| stages[10].operations[4].source_detail.output[0] | 4096 |
| stages[10].operations[4].source_detail.output[1] | 128 |
| stages[10].operations[5].name | k_norm |
| stages[10].operations[5].matrix_flops | 0 |
| stages[10].operations[5].input_precision | unknown (null) |
| stages[10].operations[5].accumulator_precision | unknown (null) |
| stages[10].operations[5].sparsity | unknown (null) |
| stages[10].operations[5].scalar_flops | 525312 |
| stages[10].operations[5].special_ops.rsqrt | 1024 |
| stages[10].operations[5].source_detail.input[0] | 1024 |
| stages[10].operations[5].source_detail.input[1] | 128 |
| stages[10].operations[5].source_detail.weight[0] | 128 |
| stages[10].operations[5].source_detail.output[0] | 1024 |
| stages[10].operations[5].source_detail.output[1] | 128 |
| stages[10].operations[6].name | apply_rope |
| stages[10].operations[6].matrix_flops | 0 |
| stages[10].operations[6].input_precision | unknown (null) |
| stages[10].operations[6].accumulator_precision | unknown (null) |
| stages[10].operations[6].sparsity | unknown (null) |
| stages[10].operations[6].scalar_flops | 1966080 |
| stages[10].operations[6].special_ops.negate | 327680 |
| stages[10].operations[6].source_detail.Q[0] | 1 |
| stages[10].operations[6].source_detail.Q[1] | 32 |
| stages[10].operations[6].source_detail.Q[2] | 128 |
| stages[10].operations[6].source_detail.Q[3] | 128 |
| stages[10].operations[6].source_detail.K[0] | 1 |
| stages[10].operations[6].source_detail.K[1] | 8 |
| stages[10].operations[6].source_detail.K[2] | 128 |
| stages[10].operations[6].source_detail.K[3] | 128 |
| stages[10].operations[7].name | kv_append |
| stages[10].operations[7].matrix_flops | 0 |
| stages[10].operations[7].input_precision | unknown (null) |
| stages[10].operations[7].accumulator_precision | unknown (null) |
| stages[10].operations[7].sparsity | unknown (null) |
| stages[10].operations[7].scalar_flops | 0 |
| stages[10].operations[7].special_ops | {} |
| stages[10].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[10].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[10].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[10].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[10].operations[8].name | qk |
| stages[10].operations[8].matrix_flops | 67633152 |
| stages[10].operations[8].input_precision | BF16 |
| stages[10].operations[8].accumulator_precision | FP32 |
| stages[10].operations[8].sparsity | dense |
| stages[10].operations[8].scalar_flops | 0 |
| stages[10].operations[8].special_ops | {} |
| stages[10].operations[8].source_detail.Q[0] | 1 |
| stages[10].operations[8].source_detail.Q[1] | 32 |
| stages[10].operations[8].source_detail.Q[2] | 128 |
| stages[10].operations[8].source_detail.Q[3] | 128 |
| stages[10].operations[8].source_detail.K_shared[0] | 1 |
| stages[10].operations[8].source_detail.K_shared[1] | 8 |
| stages[10].operations[8].source_detail.K_shared[2] | 128 |
| stages[10].operations[8].source_detail.K_shared[3] | 128 |
| stages[10].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[10].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[10].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[10].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[10].operations[9].name | score_scale_mask_softmax |
| stages[10].operations[9].matrix_flops | 0 |
| stages[10].operations[9].input_precision | unknown (null) |
| stages[10].operations[9].accumulator_precision | unknown (null) |
| stages[10].operations[9].sparsity | unknown (null) |
| stages[10].operations[9].scalar_flops | 1052672 |
| stages[10].operations[9].special_ops.exp | 264192 |
| stages[10].operations[9].special_ops.compare_max | 260096 |
| stages[10].operations[9].special_ops.mask_decisions | 524288 |
| stages[10].operations[9].source_detail.scores[0] | 1 |
| stages[10].operations[9].source_detail.scores[1] | 32 |
| stages[10].operations[9].source_detail.scores[2] | 128 |
| stages[10].operations[9].source_detail.scores[3] | 128 |
| stages[10].operations[10].name | pv |
| stages[10].operations[10].matrix_flops | 67633152 |
| stages[10].operations[10].input_precision | BF16 |
| stages[10].operations[10].accumulator_precision | FP32 |
| stages[10].operations[10].sparsity | dense |
| stages[10].operations[10].scalar_flops | 0 |
| stages[10].operations[10].special_ops | {} |
| stages[10].operations[10].source_detail.P[0] | 1 |
| stages[10].operations[10].source_detail.P[1] | 32 |
| stages[10].operations[10].source_detail.P[2] | 128 |
| stages[10].operations[10].source_detail.P[3] | 128 |
| stages[10].operations[10].source_detail.V_shared[0] | 1 |
| stages[10].operations[10].source_detail.V_shared[1] | 8 |
| stages[10].operations[10].source_detail.V_shared[2] | 128 |
| stages[10].operations[10].source_detail.V_shared[3] | 128 |
| stages[10].operations[10].source_detail.output[0] | 1 |
| stages[10].operations[10].source_detail.output[1] | 32 |
| stages[10].operations[10].source_detail.output[2] | 128 |
| stages[10].operations[10].source_detail.output[3] | 128 |
| stages[10].operations[11].name | o_proj |
| stages[10].operations[11].matrix_flops | 4294967296 |
| stages[10].operations[11].input_precision | BF16 |
| stages[10].operations[11].accumulator_precision | FP32 |
| stages[10].operations[11].sparsity | dense |
| stages[10].operations[11].scalar_flops | 0 |
| stages[10].operations[11].special_ops | {} |
| stages[10].operations[11].source_detail.input[0] | 128 |
| stages[10].operations[11].source_detail.input[1] | 4096 |
| stages[10].operations[11].source_detail.weight_math[0] | 4096 |
| stages[10].operations[11].source_detail.weight_math[1] | 4096 |
| stages[10].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[10].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[11].source_detail.output[0] | 128 |
| stages[10].operations[11].source_detail.output[1] | 4096 |
| stages[10].operations[12].name | attention_residual |
| stages[10].operations[12].matrix_flops | 0 |
| stages[10].operations[12].input_precision | unknown (null) |
| stages[10].operations[12].accumulator_precision | unknown (null) |
| stages[10].operations[12].sparsity | unknown (null) |
| stages[10].operations[12].scalar_flops | 524288 |
| stages[10].operations[12].special_ops | {} |
| stages[10].operations[12].source_detail.inputs_each[0] | 128 |
| stages[10].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[10].operations[12].source_detail.output[0] | 128 |
| stages[10].operations[12].source_detail.output[1] | 4096 |
| stages[10].operations[13].name | post_attention_layernorm |
| stages[10].operations[13].matrix_flops | 0 |
| stages[10].operations[13].input_precision | unknown (null) |
| stages[10].operations[13].accumulator_precision | unknown (null) |
| stages[10].operations[13].sparsity | unknown (null) |
| stages[10].operations[13].scalar_flops | 2097280 |
| stages[10].operations[13].special_ops.rsqrt | 128 |
| stages[10].operations[13].source_detail.input[0] | 128 |
| stages[10].operations[13].source_detail.input[1] | 4096 |
| stages[10].operations[13].source_detail.weight[0] | 4096 |
| stages[10].operations[13].source_detail.output[0] | 128 |
| stages[10].operations[13].source_detail.output[1] | 4096 |
| stages[10].operations[14].name | gate_proj |
| stages[10].operations[14].matrix_flops | 12884901888 |
| stages[10].operations[14].input_precision | BF16 |
| stages[10].operations[14].accumulator_precision | FP32 |
| stages[10].operations[14].sparsity | dense |
| stages[10].operations[14].scalar_flops | 0 |
| stages[10].operations[14].special_ops | {} |
| stages[10].operations[14].source_detail.input[0] | 128 |
| stages[10].operations[14].source_detail.input[1] | 4096 |
| stages[10].operations[14].source_detail.weight_math[0] | 4096 |
| stages[10].operations[14].source_detail.weight_math[1] | 12288 |
| stages[10].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[10].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[14].source_detail.output[0] | 128 |
| stages[10].operations[14].source_detail.output[1] | 12288 |
| stages[10].operations[15].name | up_proj |
| stages[10].operations[15].matrix_flops | 12884901888 |
| stages[10].operations[15].input_precision | BF16 |
| stages[10].operations[15].accumulator_precision | FP32 |
| stages[10].operations[15].sparsity | dense |
| stages[10].operations[15].scalar_flops | 0 |
| stages[10].operations[15].special_ops | {} |
| stages[10].operations[15].source_detail.input[0] | 128 |
| stages[10].operations[15].source_detail.input[1] | 4096 |
| stages[10].operations[15].source_detail.weight_math[0] | 4096 |
| stages[10].operations[15].source_detail.weight_math[1] | 12288 |
| stages[10].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[10].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[10].operations[15].source_detail.output[0] | 128 |
| stages[10].operations[15].source_detail.output[1] | 12288 |
| stages[10].operations[16].name | silu_mul |
| stages[10].operations[16].matrix_flops | 0 |
| stages[10].operations[16].input_precision | unknown (null) |
| stages[10].operations[16].accumulator_precision | unknown (null) |
| stages[10].operations[16].sparsity | unknown (null) |
| stages[10].operations[16].scalar_flops | 6291456 |
| stages[10].operations[16].special_ops.exp | 1572864 |
| stages[10].operations[16].special_ops.negate | 1572864 |
| stages[10].operations[16].source_detail.gate[0] | 128 |
| stages[10].operations[16].source_detail.gate[1] | 12288 |
| stages[10].operations[16].source_detail.up[0] | 128 |
| stages[10].operations[16].source_detail.up[1] | 12288 |
| stages[10].operations[16].source_detail.output[0] | 128 |
| stages[10].operations[16].source_detail.output[1] | 12288 |
| stages[10].operations[17].name | down_proj |
| stages[10].operations[17].matrix_flops | 12884901888 |
| stages[10].operations[17].input_precision | BF16 |
| stages[10].operations[17].accumulator_precision | FP32 |
| stages[10].operations[17].sparsity | dense |
| stages[10].operations[17].scalar_flops | 0 |
| stages[10].operations[17].special_ops | {} |
| stages[10].operations[17].source_detail.input[0] | 128 |
| stages[10].operations[17].source_detail.input[1] | 12288 |
| stages[10].operations[17].source_detail.weight_math[0] | 12288 |
| stages[10].operations[17].source_detail.weight_math[1] | 4096 |
| stages[10].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[10].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[10].operations[17].source_detail.output[0] | 128 |
| stages[10].operations[17].source_detail.output[1] | 4096 |
| stages[10].operations[18].name | ffn_residual |
| stages[10].operations[18].matrix_flops | 0 |
| stages[10].operations[18].input_precision | unknown (null) |
| stages[10].operations[18].accumulator_precision | unknown (null) |
| stages[10].operations[18].sparsity | unknown (null) |
| stages[10].operations[18].scalar_flops | 524288 |
| stages[10].operations[18].special_ops | {} |
| stages[10].operations[18].source_detail.inputs_each[0] | 128 |
| stages[10].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[10].operations[18].source_detail.output[0] | 128 |
| stages[10].operations[18].source_detail.output[1] | 4096 |
| stages[11].id | layer:10 |
| stages[11].work.vector_fp32 | 17179904 |
| stages[11].work.special:rsqrt | 5376 |
| stages[11].work.interface_bytes | 438387200 |
| stages[11].work.matrix_bf16 | 49527390208 |
| stages[11].work.special:negate | 1900544 |
| stages[11].work.special:exp | 1837056 |
| stages[11].work.special:compare_max | 260096 |
| stages[11].work.special:mask_decisions | 524288 |
| stages[11].operations[0].name | input_layernorm |
| stages[11].operations[0].matrix_flops | 0 |
| stages[11].operations[0].input_precision | unknown (null) |
| stages[11].operations[0].accumulator_precision | unknown (null) |
| stages[11].operations[0].sparsity | unknown (null) |
| stages[11].operations[0].scalar_flops | 2097280 |
| stages[11].operations[0].special_ops.rsqrt | 128 |
| stages[11].operations[0].source_detail.input[0] | 128 |
| stages[11].operations[0].source_detail.input[1] | 4096 |
| stages[11].operations[0].source_detail.weight[0] | 4096 |
| stages[11].operations[0].source_detail.output[0] | 128 |
| stages[11].operations[0].source_detail.output[1] | 4096 |
| stages[11].operations[1].name | q_proj |
| stages[11].operations[1].matrix_flops | 4294967296 |
| stages[11].operations[1].input_precision | BF16 |
| stages[11].operations[1].accumulator_precision | FP32 |
| stages[11].operations[1].sparsity | dense |
| stages[11].operations[1].scalar_flops | 0 |
| stages[11].operations[1].special_ops | {} |
| stages[11].operations[1].source_detail.input[0] | 128 |
| stages[11].operations[1].source_detail.input[1] | 4096 |
| stages[11].operations[1].source_detail.weight_math[0] | 4096 |
| stages[11].operations[1].source_detail.weight_math[1] | 4096 |
| stages[11].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[11].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[1].source_detail.output[0] | 128 |
| stages[11].operations[1].source_detail.output[1] | 4096 |
| stages[11].operations[2].name | k_proj |
| stages[11].operations[2].matrix_flops | 1073741824 |
| stages[11].operations[2].input_precision | BF16 |
| stages[11].operations[2].accumulator_precision | FP32 |
| stages[11].operations[2].sparsity | dense |
| stages[11].operations[2].scalar_flops | 0 |
| stages[11].operations[2].special_ops | {} |
| stages[11].operations[2].source_detail.input[0] | 128 |
| stages[11].operations[2].source_detail.input[1] | 4096 |
| stages[11].operations[2].source_detail.weight_math[0] | 4096 |
| stages[11].operations[2].source_detail.weight_math[1] | 1024 |
| stages[11].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[11].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[2].source_detail.output[0] | 128 |
| stages[11].operations[2].source_detail.output[1] | 1024 |
| stages[11].operations[3].name | v_proj |
| stages[11].operations[3].matrix_flops | 1073741824 |
| stages[11].operations[3].input_precision | BF16 |
| stages[11].operations[3].accumulator_precision | FP32 |
| stages[11].operations[3].sparsity | dense |
| stages[11].operations[3].scalar_flops | 0 |
| stages[11].operations[3].special_ops | {} |
| stages[11].operations[3].source_detail.input[0] | 128 |
| stages[11].operations[3].source_detail.input[1] | 4096 |
| stages[11].operations[3].source_detail.weight_math[0] | 4096 |
| stages[11].operations[3].source_detail.weight_math[1] | 1024 |
| stages[11].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[11].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[3].source_detail.output[0] | 128 |
| stages[11].operations[3].source_detail.output[1] | 1024 |
| stages[11].operations[4].name | q_norm |
| stages[11].operations[4].matrix_flops | 0 |
| stages[11].operations[4].input_precision | unknown (null) |
| stages[11].operations[4].accumulator_precision | unknown (null) |
| stages[11].operations[4].sparsity | unknown (null) |
| stages[11].operations[4].scalar_flops | 2101248 |
| stages[11].operations[4].special_ops.rsqrt | 4096 |
| stages[11].operations[4].source_detail.input[0] | 4096 |
| stages[11].operations[4].source_detail.input[1] | 128 |
| stages[11].operations[4].source_detail.weight[0] | 128 |
| stages[11].operations[4].source_detail.output[0] | 4096 |
| stages[11].operations[4].source_detail.output[1] | 128 |
| stages[11].operations[5].name | k_norm |
| stages[11].operations[5].matrix_flops | 0 |
| stages[11].operations[5].input_precision | unknown (null) |
| stages[11].operations[5].accumulator_precision | unknown (null) |
| stages[11].operations[5].sparsity | unknown (null) |
| stages[11].operations[5].scalar_flops | 525312 |
| stages[11].operations[5].special_ops.rsqrt | 1024 |
| stages[11].operations[5].source_detail.input[0] | 1024 |
| stages[11].operations[5].source_detail.input[1] | 128 |
| stages[11].operations[5].source_detail.weight[0] | 128 |
| stages[11].operations[5].source_detail.output[0] | 1024 |
| stages[11].operations[5].source_detail.output[1] | 128 |
| stages[11].operations[6].name | apply_rope |
| stages[11].operations[6].matrix_flops | 0 |
| stages[11].operations[6].input_precision | unknown (null) |
| stages[11].operations[6].accumulator_precision | unknown (null) |
| stages[11].operations[6].sparsity | unknown (null) |
| stages[11].operations[6].scalar_flops | 1966080 |
| stages[11].operations[6].special_ops.negate | 327680 |
| stages[11].operations[6].source_detail.Q[0] | 1 |
| stages[11].operations[6].source_detail.Q[1] | 32 |
| stages[11].operations[6].source_detail.Q[2] | 128 |
| stages[11].operations[6].source_detail.Q[3] | 128 |
| stages[11].operations[6].source_detail.K[0] | 1 |
| stages[11].operations[6].source_detail.K[1] | 8 |
| stages[11].operations[6].source_detail.K[2] | 128 |
| stages[11].operations[6].source_detail.K[3] | 128 |
| stages[11].operations[7].name | kv_append |
| stages[11].operations[7].matrix_flops | 0 |
| stages[11].operations[7].input_precision | unknown (null) |
| stages[11].operations[7].accumulator_precision | unknown (null) |
| stages[11].operations[7].sparsity | unknown (null) |
| stages[11].operations[7].scalar_flops | 0 |
| stages[11].operations[7].special_ops | {} |
| stages[11].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[11].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[11].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[11].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[11].operations[8].name | qk |
| stages[11].operations[8].matrix_flops | 67633152 |
| stages[11].operations[8].input_precision | BF16 |
| stages[11].operations[8].accumulator_precision | FP32 |
| stages[11].operations[8].sparsity | dense |
| stages[11].operations[8].scalar_flops | 0 |
| stages[11].operations[8].special_ops | {} |
| stages[11].operations[8].source_detail.Q[0] | 1 |
| stages[11].operations[8].source_detail.Q[1] | 32 |
| stages[11].operations[8].source_detail.Q[2] | 128 |
| stages[11].operations[8].source_detail.Q[3] | 128 |
| stages[11].operations[8].source_detail.K_shared[0] | 1 |
| stages[11].operations[8].source_detail.K_shared[1] | 8 |
| stages[11].operations[8].source_detail.K_shared[2] | 128 |
| stages[11].operations[8].source_detail.K_shared[3] | 128 |
| stages[11].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[11].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[11].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[11].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[11].operations[9].name | score_scale_mask_softmax |
| stages[11].operations[9].matrix_flops | 0 |
| stages[11].operations[9].input_precision | unknown (null) |
| stages[11].operations[9].accumulator_precision | unknown (null) |
| stages[11].operations[9].sparsity | unknown (null) |
| stages[11].operations[9].scalar_flops | 1052672 |
| stages[11].operations[9].special_ops.exp | 264192 |
| stages[11].operations[9].special_ops.compare_max | 260096 |
| stages[11].operations[9].special_ops.mask_decisions | 524288 |
| stages[11].operations[9].source_detail.scores[0] | 1 |
| stages[11].operations[9].source_detail.scores[1] | 32 |
| stages[11].operations[9].source_detail.scores[2] | 128 |
| stages[11].operations[9].source_detail.scores[3] | 128 |
| stages[11].operations[10].name | pv |
| stages[11].operations[10].matrix_flops | 67633152 |
| stages[11].operations[10].input_precision | BF16 |
| stages[11].operations[10].accumulator_precision | FP32 |
| stages[11].operations[10].sparsity | dense |
| stages[11].operations[10].scalar_flops | 0 |
| stages[11].operations[10].special_ops | {} |
| stages[11].operations[10].source_detail.P[0] | 1 |
| stages[11].operations[10].source_detail.P[1] | 32 |
| stages[11].operations[10].source_detail.P[2] | 128 |
| stages[11].operations[10].source_detail.P[3] | 128 |
| stages[11].operations[10].source_detail.V_shared[0] | 1 |
| stages[11].operations[10].source_detail.V_shared[1] | 8 |
| stages[11].operations[10].source_detail.V_shared[2] | 128 |
| stages[11].operations[10].source_detail.V_shared[3] | 128 |
| stages[11].operations[10].source_detail.output[0] | 1 |
| stages[11].operations[10].source_detail.output[1] | 32 |
| stages[11].operations[10].source_detail.output[2] | 128 |
| stages[11].operations[10].source_detail.output[3] | 128 |
| stages[11].operations[11].name | o_proj |
| stages[11].operations[11].matrix_flops | 4294967296 |
| stages[11].operations[11].input_precision | BF16 |
| stages[11].operations[11].accumulator_precision | FP32 |
| stages[11].operations[11].sparsity | dense |
| stages[11].operations[11].scalar_flops | 0 |
| stages[11].operations[11].special_ops | {} |
| stages[11].operations[11].source_detail.input[0] | 128 |
| stages[11].operations[11].source_detail.input[1] | 4096 |
| stages[11].operations[11].source_detail.weight_math[0] | 4096 |
| stages[11].operations[11].source_detail.weight_math[1] | 4096 |
| stages[11].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[11].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[11].source_detail.output[0] | 128 |
| stages[11].operations[11].source_detail.output[1] | 4096 |
| stages[11].operations[12].name | attention_residual |
| stages[11].operations[12].matrix_flops | 0 |
| stages[11].operations[12].input_precision | unknown (null) |
| stages[11].operations[12].accumulator_precision | unknown (null) |
| stages[11].operations[12].sparsity | unknown (null) |
| stages[11].operations[12].scalar_flops | 524288 |
| stages[11].operations[12].special_ops | {} |
| stages[11].operations[12].source_detail.inputs_each[0] | 128 |
| stages[11].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[11].operations[12].source_detail.output[0] | 128 |
| stages[11].operations[12].source_detail.output[1] | 4096 |
| stages[11].operations[13].name | post_attention_layernorm |
| stages[11].operations[13].matrix_flops | 0 |
| stages[11].operations[13].input_precision | unknown (null) |
| stages[11].operations[13].accumulator_precision | unknown (null) |
| stages[11].operations[13].sparsity | unknown (null) |
| stages[11].operations[13].scalar_flops | 2097280 |
| stages[11].operations[13].special_ops.rsqrt | 128 |
| stages[11].operations[13].source_detail.input[0] | 128 |
| stages[11].operations[13].source_detail.input[1] | 4096 |
| stages[11].operations[13].source_detail.weight[0] | 4096 |
| stages[11].operations[13].source_detail.output[0] | 128 |
| stages[11].operations[13].source_detail.output[1] | 4096 |
| stages[11].operations[14].name | gate_proj |
| stages[11].operations[14].matrix_flops | 12884901888 |
| stages[11].operations[14].input_precision | BF16 |
| stages[11].operations[14].accumulator_precision | FP32 |
| stages[11].operations[14].sparsity | dense |
| stages[11].operations[14].scalar_flops | 0 |
| stages[11].operations[14].special_ops | {} |
| stages[11].operations[14].source_detail.input[0] | 128 |
| stages[11].operations[14].source_detail.input[1] | 4096 |
| stages[11].operations[14].source_detail.weight_math[0] | 4096 |
| stages[11].operations[14].source_detail.weight_math[1] | 12288 |
| stages[11].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[11].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[14].source_detail.output[0] | 128 |
| stages[11].operations[14].source_detail.output[1] | 12288 |
| stages[11].operations[15].name | up_proj |
| stages[11].operations[15].matrix_flops | 12884901888 |
| stages[11].operations[15].input_precision | BF16 |
| stages[11].operations[15].accumulator_precision | FP32 |
| stages[11].operations[15].sparsity | dense |
| stages[11].operations[15].scalar_flops | 0 |
| stages[11].operations[15].special_ops | {} |
| stages[11].operations[15].source_detail.input[0] | 128 |
| stages[11].operations[15].source_detail.input[1] | 4096 |
| stages[11].operations[15].source_detail.weight_math[0] | 4096 |
| stages[11].operations[15].source_detail.weight_math[1] | 12288 |
| stages[11].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[11].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[11].operations[15].source_detail.output[0] | 128 |
| stages[11].operations[15].source_detail.output[1] | 12288 |
| stages[11].operations[16].name | silu_mul |
| stages[11].operations[16].matrix_flops | 0 |
| stages[11].operations[16].input_precision | unknown (null) |
| stages[11].operations[16].accumulator_precision | unknown (null) |
| stages[11].operations[16].sparsity | unknown (null) |
| stages[11].operations[16].scalar_flops | 6291456 |
| stages[11].operations[16].special_ops.exp | 1572864 |
| stages[11].operations[16].special_ops.negate | 1572864 |
| stages[11].operations[16].source_detail.gate[0] | 128 |
| stages[11].operations[16].source_detail.gate[1] | 12288 |
| stages[11].operations[16].source_detail.up[0] | 128 |
| stages[11].operations[16].source_detail.up[1] | 12288 |
| stages[11].operations[16].source_detail.output[0] | 128 |
| stages[11].operations[16].source_detail.output[1] | 12288 |
| stages[11].operations[17].name | down_proj |
| stages[11].operations[17].matrix_flops | 12884901888 |
| stages[11].operations[17].input_precision | BF16 |
| stages[11].operations[17].accumulator_precision | FP32 |
| stages[11].operations[17].sparsity | dense |
| stages[11].operations[17].scalar_flops | 0 |
| stages[11].operations[17].special_ops | {} |
| stages[11].operations[17].source_detail.input[0] | 128 |
| stages[11].operations[17].source_detail.input[1] | 12288 |
| stages[11].operations[17].source_detail.weight_math[0] | 12288 |
| stages[11].operations[17].source_detail.weight_math[1] | 4096 |
| stages[11].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[11].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[11].operations[17].source_detail.output[0] | 128 |
| stages[11].operations[17].source_detail.output[1] | 4096 |
| stages[11].operations[18].name | ffn_residual |
| stages[11].operations[18].matrix_flops | 0 |
| stages[11].operations[18].input_precision | unknown (null) |
| stages[11].operations[18].accumulator_precision | unknown (null) |
| stages[11].operations[18].sparsity | unknown (null) |
| stages[11].operations[18].scalar_flops | 524288 |
| stages[11].operations[18].special_ops | {} |
| stages[11].operations[18].source_detail.inputs_each[0] | 128 |
| stages[11].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[11].operations[18].source_detail.output[0] | 128 |
| stages[11].operations[18].source_detail.output[1] | 4096 |
| stages[12].id | layer:11 |
| stages[12].work.vector_fp32 | 17179904 |
| stages[12].work.special:rsqrt | 5376 |
| stages[12].work.interface_bytes | 438387200 |
| stages[12].work.matrix_bf16 | 49527390208 |
| stages[12].work.special:negate | 1900544 |
| stages[12].work.special:exp | 1837056 |
| stages[12].work.special:compare_max | 260096 |
| stages[12].work.special:mask_decisions | 524288 |
| stages[12].operations[0].name | input_layernorm |
| stages[12].operations[0].matrix_flops | 0 |
| stages[12].operations[0].input_precision | unknown (null) |
| stages[12].operations[0].accumulator_precision | unknown (null) |
| stages[12].operations[0].sparsity | unknown (null) |
| stages[12].operations[0].scalar_flops | 2097280 |
| stages[12].operations[0].special_ops.rsqrt | 128 |
| stages[12].operations[0].source_detail.input[0] | 128 |
| stages[12].operations[0].source_detail.input[1] | 4096 |
| stages[12].operations[0].source_detail.weight[0] | 4096 |
| stages[12].operations[0].source_detail.output[0] | 128 |
| stages[12].operations[0].source_detail.output[1] | 4096 |
| stages[12].operations[1].name | q_proj |
| stages[12].operations[1].matrix_flops | 4294967296 |
| stages[12].operations[1].input_precision | BF16 |
| stages[12].operations[1].accumulator_precision | FP32 |
| stages[12].operations[1].sparsity | dense |
| stages[12].operations[1].scalar_flops | 0 |
| stages[12].operations[1].special_ops | {} |
| stages[12].operations[1].source_detail.input[0] | 128 |
| stages[12].operations[1].source_detail.input[1] | 4096 |
| stages[12].operations[1].source_detail.weight_math[0] | 4096 |
| stages[12].operations[1].source_detail.weight_math[1] | 4096 |
| stages[12].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[12].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[1].source_detail.output[0] | 128 |
| stages[12].operations[1].source_detail.output[1] | 4096 |
| stages[12].operations[2].name | k_proj |
| stages[12].operations[2].matrix_flops | 1073741824 |
| stages[12].operations[2].input_precision | BF16 |
| stages[12].operations[2].accumulator_precision | FP32 |
| stages[12].operations[2].sparsity | dense |
| stages[12].operations[2].scalar_flops | 0 |
| stages[12].operations[2].special_ops | {} |
| stages[12].operations[2].source_detail.input[0] | 128 |
| stages[12].operations[2].source_detail.input[1] | 4096 |
| stages[12].operations[2].source_detail.weight_math[0] | 4096 |
| stages[12].operations[2].source_detail.weight_math[1] | 1024 |
| stages[12].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[12].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[2].source_detail.output[0] | 128 |
| stages[12].operations[2].source_detail.output[1] | 1024 |
| stages[12].operations[3].name | v_proj |
| stages[12].operations[3].matrix_flops | 1073741824 |
| stages[12].operations[3].input_precision | BF16 |
| stages[12].operations[3].accumulator_precision | FP32 |
| stages[12].operations[3].sparsity | dense |
| stages[12].operations[3].scalar_flops | 0 |
| stages[12].operations[3].special_ops | {} |
| stages[12].operations[3].source_detail.input[0] | 128 |
| stages[12].operations[3].source_detail.input[1] | 4096 |
| stages[12].operations[3].source_detail.weight_math[0] | 4096 |
| stages[12].operations[3].source_detail.weight_math[1] | 1024 |
| stages[12].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[12].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[3].source_detail.output[0] | 128 |
| stages[12].operations[3].source_detail.output[1] | 1024 |
| stages[12].operations[4].name | q_norm |
| stages[12].operations[4].matrix_flops | 0 |
| stages[12].operations[4].input_precision | unknown (null) |
| stages[12].operations[4].accumulator_precision | unknown (null) |
| stages[12].operations[4].sparsity | unknown (null) |
| stages[12].operations[4].scalar_flops | 2101248 |
| stages[12].operations[4].special_ops.rsqrt | 4096 |
| stages[12].operations[4].source_detail.input[0] | 4096 |
| stages[12].operations[4].source_detail.input[1] | 128 |
| stages[12].operations[4].source_detail.weight[0] | 128 |
| stages[12].operations[4].source_detail.output[0] | 4096 |
| stages[12].operations[4].source_detail.output[1] | 128 |
| stages[12].operations[5].name | k_norm |
| stages[12].operations[5].matrix_flops | 0 |
| stages[12].operations[5].input_precision | unknown (null) |
| stages[12].operations[5].accumulator_precision | unknown (null) |
| stages[12].operations[5].sparsity | unknown (null) |
| stages[12].operations[5].scalar_flops | 525312 |
| stages[12].operations[5].special_ops.rsqrt | 1024 |
| stages[12].operations[5].source_detail.input[0] | 1024 |
| stages[12].operations[5].source_detail.input[1] | 128 |
| stages[12].operations[5].source_detail.weight[0] | 128 |
| stages[12].operations[5].source_detail.output[0] | 1024 |
| stages[12].operations[5].source_detail.output[1] | 128 |
| stages[12].operations[6].name | apply_rope |
| stages[12].operations[6].matrix_flops | 0 |
| stages[12].operations[6].input_precision | unknown (null) |
| stages[12].operations[6].accumulator_precision | unknown (null) |
| stages[12].operations[6].sparsity | unknown (null) |
| stages[12].operations[6].scalar_flops | 1966080 |
| stages[12].operations[6].special_ops.negate | 327680 |
| stages[12].operations[6].source_detail.Q[0] | 1 |
| stages[12].operations[6].source_detail.Q[1] | 32 |
| stages[12].operations[6].source_detail.Q[2] | 128 |
| stages[12].operations[6].source_detail.Q[3] | 128 |
| stages[12].operations[6].source_detail.K[0] | 1 |
| stages[12].operations[6].source_detail.K[1] | 8 |
| stages[12].operations[6].source_detail.K[2] | 128 |
| stages[12].operations[6].source_detail.K[3] | 128 |
| stages[12].operations[7].name | kv_append |
| stages[12].operations[7].matrix_flops | 0 |
| stages[12].operations[7].input_precision | unknown (null) |
| stages[12].operations[7].accumulator_precision | unknown (null) |
| stages[12].operations[7].sparsity | unknown (null) |
| stages[12].operations[7].scalar_flops | 0 |
| stages[12].operations[7].special_ops | {} |
| stages[12].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[12].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[12].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[12].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[12].operations[8].name | qk |
| stages[12].operations[8].matrix_flops | 67633152 |
| stages[12].operations[8].input_precision | BF16 |
| stages[12].operations[8].accumulator_precision | FP32 |
| stages[12].operations[8].sparsity | dense |
| stages[12].operations[8].scalar_flops | 0 |
| stages[12].operations[8].special_ops | {} |
| stages[12].operations[8].source_detail.Q[0] | 1 |
| stages[12].operations[8].source_detail.Q[1] | 32 |
| stages[12].operations[8].source_detail.Q[2] | 128 |
| stages[12].operations[8].source_detail.Q[3] | 128 |
| stages[12].operations[8].source_detail.K_shared[0] | 1 |
| stages[12].operations[8].source_detail.K_shared[1] | 8 |
| stages[12].operations[8].source_detail.K_shared[2] | 128 |
| stages[12].operations[8].source_detail.K_shared[3] | 128 |
| stages[12].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[12].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[12].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[12].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[12].operations[9].name | score_scale_mask_softmax |
| stages[12].operations[9].matrix_flops | 0 |
| stages[12].operations[9].input_precision | unknown (null) |
| stages[12].operations[9].accumulator_precision | unknown (null) |
| stages[12].operations[9].sparsity | unknown (null) |
| stages[12].operations[9].scalar_flops | 1052672 |
| stages[12].operations[9].special_ops.exp | 264192 |
| stages[12].operations[9].special_ops.compare_max | 260096 |
| stages[12].operations[9].special_ops.mask_decisions | 524288 |
| stages[12].operations[9].source_detail.scores[0] | 1 |
| stages[12].operations[9].source_detail.scores[1] | 32 |
| stages[12].operations[9].source_detail.scores[2] | 128 |
| stages[12].operations[9].source_detail.scores[3] | 128 |
| stages[12].operations[10].name | pv |
| stages[12].operations[10].matrix_flops | 67633152 |
| stages[12].operations[10].input_precision | BF16 |
| stages[12].operations[10].accumulator_precision | FP32 |
| stages[12].operations[10].sparsity | dense |
| stages[12].operations[10].scalar_flops | 0 |
| stages[12].operations[10].special_ops | {} |
| stages[12].operations[10].source_detail.P[0] | 1 |
| stages[12].operations[10].source_detail.P[1] | 32 |
| stages[12].operations[10].source_detail.P[2] | 128 |
| stages[12].operations[10].source_detail.P[3] | 128 |
| stages[12].operations[10].source_detail.V_shared[0] | 1 |
| stages[12].operations[10].source_detail.V_shared[1] | 8 |
| stages[12].operations[10].source_detail.V_shared[2] | 128 |
| stages[12].operations[10].source_detail.V_shared[3] | 128 |
| stages[12].operations[10].source_detail.output[0] | 1 |
| stages[12].operations[10].source_detail.output[1] | 32 |
| stages[12].operations[10].source_detail.output[2] | 128 |
| stages[12].operations[10].source_detail.output[3] | 128 |
| stages[12].operations[11].name | o_proj |
| stages[12].operations[11].matrix_flops | 4294967296 |
| stages[12].operations[11].input_precision | BF16 |
| stages[12].operations[11].accumulator_precision | FP32 |
| stages[12].operations[11].sparsity | dense |
| stages[12].operations[11].scalar_flops | 0 |
| stages[12].operations[11].special_ops | {} |
| stages[12].operations[11].source_detail.input[0] | 128 |
| stages[12].operations[11].source_detail.input[1] | 4096 |
| stages[12].operations[11].source_detail.weight_math[0] | 4096 |
| stages[12].operations[11].source_detail.weight_math[1] | 4096 |
| stages[12].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[12].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[11].source_detail.output[0] | 128 |
| stages[12].operations[11].source_detail.output[1] | 4096 |
| stages[12].operations[12].name | attention_residual |
| stages[12].operations[12].matrix_flops | 0 |
| stages[12].operations[12].input_precision | unknown (null) |
| stages[12].operations[12].accumulator_precision | unknown (null) |
| stages[12].operations[12].sparsity | unknown (null) |
| stages[12].operations[12].scalar_flops | 524288 |
| stages[12].operations[12].special_ops | {} |
| stages[12].operations[12].source_detail.inputs_each[0] | 128 |
| stages[12].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[12].operations[12].source_detail.output[0] | 128 |
| stages[12].operations[12].source_detail.output[1] | 4096 |
| stages[12].operations[13].name | post_attention_layernorm |
| stages[12].operations[13].matrix_flops | 0 |
| stages[12].operations[13].input_precision | unknown (null) |
| stages[12].operations[13].accumulator_precision | unknown (null) |
| stages[12].operations[13].sparsity | unknown (null) |
| stages[12].operations[13].scalar_flops | 2097280 |
| stages[12].operations[13].special_ops.rsqrt | 128 |
| stages[12].operations[13].source_detail.input[0] | 128 |
| stages[12].operations[13].source_detail.input[1] | 4096 |
| stages[12].operations[13].source_detail.weight[0] | 4096 |
| stages[12].operations[13].source_detail.output[0] | 128 |
| stages[12].operations[13].source_detail.output[1] | 4096 |
| stages[12].operations[14].name | gate_proj |
| stages[12].operations[14].matrix_flops | 12884901888 |
| stages[12].operations[14].input_precision | BF16 |
| stages[12].operations[14].accumulator_precision | FP32 |
| stages[12].operations[14].sparsity | dense |
| stages[12].operations[14].scalar_flops | 0 |
| stages[12].operations[14].special_ops | {} |
| stages[12].operations[14].source_detail.input[0] | 128 |
| stages[12].operations[14].source_detail.input[1] | 4096 |
| stages[12].operations[14].source_detail.weight_math[0] | 4096 |
| stages[12].operations[14].source_detail.weight_math[1] | 12288 |
| stages[12].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[12].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[14].source_detail.output[0] | 128 |
| stages[12].operations[14].source_detail.output[1] | 12288 |
| stages[12].operations[15].name | up_proj |
| stages[12].operations[15].matrix_flops | 12884901888 |
| stages[12].operations[15].input_precision | BF16 |
| stages[12].operations[15].accumulator_precision | FP32 |
| stages[12].operations[15].sparsity | dense |
| stages[12].operations[15].scalar_flops | 0 |
| stages[12].operations[15].special_ops | {} |
| stages[12].operations[15].source_detail.input[0] | 128 |
| stages[12].operations[15].source_detail.input[1] | 4096 |
| stages[12].operations[15].source_detail.weight_math[0] | 4096 |
| stages[12].operations[15].source_detail.weight_math[1] | 12288 |
| stages[12].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[12].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[12].operations[15].source_detail.output[0] | 128 |
| stages[12].operations[15].source_detail.output[1] | 12288 |
| stages[12].operations[16].name | silu_mul |
| stages[12].operations[16].matrix_flops | 0 |
| stages[12].operations[16].input_precision | unknown (null) |
| stages[12].operations[16].accumulator_precision | unknown (null) |
| stages[12].operations[16].sparsity | unknown (null) |
| stages[12].operations[16].scalar_flops | 6291456 |
| stages[12].operations[16].special_ops.exp | 1572864 |
| stages[12].operations[16].special_ops.negate | 1572864 |
| stages[12].operations[16].source_detail.gate[0] | 128 |
| stages[12].operations[16].source_detail.gate[1] | 12288 |
| stages[12].operations[16].source_detail.up[0] | 128 |
| stages[12].operations[16].source_detail.up[1] | 12288 |
| stages[12].operations[16].source_detail.output[0] | 128 |
| stages[12].operations[16].source_detail.output[1] | 12288 |
| stages[12].operations[17].name | down_proj |
| stages[12].operations[17].matrix_flops | 12884901888 |
| stages[12].operations[17].input_precision | BF16 |
| stages[12].operations[17].accumulator_precision | FP32 |
| stages[12].operations[17].sparsity | dense |
| stages[12].operations[17].scalar_flops | 0 |
| stages[12].operations[17].special_ops | {} |
| stages[12].operations[17].source_detail.input[0] | 128 |
| stages[12].operations[17].source_detail.input[1] | 12288 |
| stages[12].operations[17].source_detail.weight_math[0] | 12288 |
| stages[12].operations[17].source_detail.weight_math[1] | 4096 |
| stages[12].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[12].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[12].operations[17].source_detail.output[0] | 128 |
| stages[12].operations[17].source_detail.output[1] | 4096 |
| stages[12].operations[18].name | ffn_residual |
| stages[12].operations[18].matrix_flops | 0 |
| stages[12].operations[18].input_precision | unknown (null) |
| stages[12].operations[18].accumulator_precision | unknown (null) |
| stages[12].operations[18].sparsity | unknown (null) |
| stages[12].operations[18].scalar_flops | 524288 |
| stages[12].operations[18].special_ops | {} |
| stages[12].operations[18].source_detail.inputs_each[0] | 128 |
| stages[12].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[12].operations[18].source_detail.output[0] | 128 |
| stages[12].operations[18].source_detail.output[1] | 4096 |
| stages[13].id | layer:12 |
| stages[13].work.vector_fp32 | 17179904 |
| stages[13].work.special:rsqrt | 5376 |
| stages[13].work.interface_bytes | 438387200 |
| stages[13].work.matrix_bf16 | 49527390208 |
| stages[13].work.special:negate | 1900544 |
| stages[13].work.special:exp | 1837056 |
| stages[13].work.special:compare_max | 260096 |
| stages[13].work.special:mask_decisions | 524288 |
| stages[13].operations[0].name | input_layernorm |
| stages[13].operations[0].matrix_flops | 0 |
| stages[13].operations[0].input_precision | unknown (null) |
| stages[13].operations[0].accumulator_precision | unknown (null) |
| stages[13].operations[0].sparsity | unknown (null) |
| stages[13].operations[0].scalar_flops | 2097280 |
| stages[13].operations[0].special_ops.rsqrt | 128 |
| stages[13].operations[0].source_detail.input[0] | 128 |
| stages[13].operations[0].source_detail.input[1] | 4096 |
| stages[13].operations[0].source_detail.weight[0] | 4096 |
| stages[13].operations[0].source_detail.output[0] | 128 |
| stages[13].operations[0].source_detail.output[1] | 4096 |
| stages[13].operations[1].name | q_proj |
| stages[13].operations[1].matrix_flops | 4294967296 |
| stages[13].operations[1].input_precision | BF16 |
| stages[13].operations[1].accumulator_precision | FP32 |
| stages[13].operations[1].sparsity | dense |
| stages[13].operations[1].scalar_flops | 0 |
| stages[13].operations[1].special_ops | {} |
| stages[13].operations[1].source_detail.input[0] | 128 |
| stages[13].operations[1].source_detail.input[1] | 4096 |
| stages[13].operations[1].source_detail.weight_math[0] | 4096 |
| stages[13].operations[1].source_detail.weight_math[1] | 4096 |
| stages[13].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[13].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[1].source_detail.output[0] | 128 |
| stages[13].operations[1].source_detail.output[1] | 4096 |
| stages[13].operations[2].name | k_proj |
| stages[13].operations[2].matrix_flops | 1073741824 |
| stages[13].operations[2].input_precision | BF16 |
| stages[13].operations[2].accumulator_precision | FP32 |
| stages[13].operations[2].sparsity | dense |
| stages[13].operations[2].scalar_flops | 0 |
| stages[13].operations[2].special_ops | {} |
| stages[13].operations[2].source_detail.input[0] | 128 |
| stages[13].operations[2].source_detail.input[1] | 4096 |
| stages[13].operations[2].source_detail.weight_math[0] | 4096 |
| stages[13].operations[2].source_detail.weight_math[1] | 1024 |
| stages[13].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[13].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[2].source_detail.output[0] | 128 |
| stages[13].operations[2].source_detail.output[1] | 1024 |
| stages[13].operations[3].name | v_proj |
| stages[13].operations[3].matrix_flops | 1073741824 |
| stages[13].operations[3].input_precision | BF16 |
| stages[13].operations[3].accumulator_precision | FP32 |
| stages[13].operations[3].sparsity | dense |
| stages[13].operations[3].scalar_flops | 0 |
| stages[13].operations[3].special_ops | {} |
| stages[13].operations[3].source_detail.input[0] | 128 |
| stages[13].operations[3].source_detail.input[1] | 4096 |
| stages[13].operations[3].source_detail.weight_math[0] | 4096 |
| stages[13].operations[3].source_detail.weight_math[1] | 1024 |
| stages[13].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[13].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[3].source_detail.output[0] | 128 |
| stages[13].operations[3].source_detail.output[1] | 1024 |
| stages[13].operations[4].name | q_norm |
| stages[13].operations[4].matrix_flops | 0 |
| stages[13].operations[4].input_precision | unknown (null) |
| stages[13].operations[4].accumulator_precision | unknown (null) |
| stages[13].operations[4].sparsity | unknown (null) |
| stages[13].operations[4].scalar_flops | 2101248 |
| stages[13].operations[4].special_ops.rsqrt | 4096 |
| stages[13].operations[4].source_detail.input[0] | 4096 |
| stages[13].operations[4].source_detail.input[1] | 128 |
| stages[13].operations[4].source_detail.weight[0] | 128 |
| stages[13].operations[4].source_detail.output[0] | 4096 |
| stages[13].operations[4].source_detail.output[1] | 128 |
| stages[13].operations[5].name | k_norm |
| stages[13].operations[5].matrix_flops | 0 |
| stages[13].operations[5].input_precision | unknown (null) |
| stages[13].operations[5].accumulator_precision | unknown (null) |
| stages[13].operations[5].sparsity | unknown (null) |
| stages[13].operations[5].scalar_flops | 525312 |
| stages[13].operations[5].special_ops.rsqrt | 1024 |
| stages[13].operations[5].source_detail.input[0] | 1024 |
| stages[13].operations[5].source_detail.input[1] | 128 |
| stages[13].operations[5].source_detail.weight[0] | 128 |
| stages[13].operations[5].source_detail.output[0] | 1024 |
| stages[13].operations[5].source_detail.output[1] | 128 |
| stages[13].operations[6].name | apply_rope |
| stages[13].operations[6].matrix_flops | 0 |
| stages[13].operations[6].input_precision | unknown (null) |
| stages[13].operations[6].accumulator_precision | unknown (null) |
| stages[13].operations[6].sparsity | unknown (null) |
| stages[13].operations[6].scalar_flops | 1966080 |
| stages[13].operations[6].special_ops.negate | 327680 |
| stages[13].operations[6].source_detail.Q[0] | 1 |
| stages[13].operations[6].source_detail.Q[1] | 32 |
| stages[13].operations[6].source_detail.Q[2] | 128 |
| stages[13].operations[6].source_detail.Q[3] | 128 |
| stages[13].operations[6].source_detail.K[0] | 1 |
| stages[13].operations[6].source_detail.K[1] | 8 |
| stages[13].operations[6].source_detail.K[2] | 128 |
| stages[13].operations[6].source_detail.K[3] | 128 |
| stages[13].operations[7].name | kv_append |
| stages[13].operations[7].matrix_flops | 0 |
| stages[13].operations[7].input_precision | unknown (null) |
| stages[13].operations[7].accumulator_precision | unknown (null) |
| stages[13].operations[7].sparsity | unknown (null) |
| stages[13].operations[7].scalar_flops | 0 |
| stages[13].operations[7].special_ops | {} |
| stages[13].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[13].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[13].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[13].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[13].operations[8].name | qk |
| stages[13].operations[8].matrix_flops | 67633152 |
| stages[13].operations[8].input_precision | BF16 |
| stages[13].operations[8].accumulator_precision | FP32 |
| stages[13].operations[8].sparsity | dense |
| stages[13].operations[8].scalar_flops | 0 |
| stages[13].operations[8].special_ops | {} |
| stages[13].operations[8].source_detail.Q[0] | 1 |
| stages[13].operations[8].source_detail.Q[1] | 32 |
| stages[13].operations[8].source_detail.Q[2] | 128 |
| stages[13].operations[8].source_detail.Q[3] | 128 |
| stages[13].operations[8].source_detail.K_shared[0] | 1 |
| stages[13].operations[8].source_detail.K_shared[1] | 8 |
| stages[13].operations[8].source_detail.K_shared[2] | 128 |
| stages[13].operations[8].source_detail.K_shared[3] | 128 |
| stages[13].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[13].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[13].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[13].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[13].operations[9].name | score_scale_mask_softmax |
| stages[13].operations[9].matrix_flops | 0 |
| stages[13].operations[9].input_precision | unknown (null) |
| stages[13].operations[9].accumulator_precision | unknown (null) |
| stages[13].operations[9].sparsity | unknown (null) |
| stages[13].operations[9].scalar_flops | 1052672 |
| stages[13].operations[9].special_ops.exp | 264192 |
| stages[13].operations[9].special_ops.compare_max | 260096 |
| stages[13].operations[9].special_ops.mask_decisions | 524288 |
| stages[13].operations[9].source_detail.scores[0] | 1 |
| stages[13].operations[9].source_detail.scores[1] | 32 |
| stages[13].operations[9].source_detail.scores[2] | 128 |
| stages[13].operations[9].source_detail.scores[3] | 128 |
| stages[13].operations[10].name | pv |
| stages[13].operations[10].matrix_flops | 67633152 |
| stages[13].operations[10].input_precision | BF16 |
| stages[13].operations[10].accumulator_precision | FP32 |
| stages[13].operations[10].sparsity | dense |
| stages[13].operations[10].scalar_flops | 0 |
| stages[13].operations[10].special_ops | {} |
| stages[13].operations[10].source_detail.P[0] | 1 |
| stages[13].operations[10].source_detail.P[1] | 32 |
| stages[13].operations[10].source_detail.P[2] | 128 |
| stages[13].operations[10].source_detail.P[3] | 128 |
| stages[13].operations[10].source_detail.V_shared[0] | 1 |
| stages[13].operations[10].source_detail.V_shared[1] | 8 |
| stages[13].operations[10].source_detail.V_shared[2] | 128 |
| stages[13].operations[10].source_detail.V_shared[3] | 128 |
| stages[13].operations[10].source_detail.output[0] | 1 |
| stages[13].operations[10].source_detail.output[1] | 32 |
| stages[13].operations[10].source_detail.output[2] | 128 |
| stages[13].operations[10].source_detail.output[3] | 128 |
| stages[13].operations[11].name | o_proj |
| stages[13].operations[11].matrix_flops | 4294967296 |
| stages[13].operations[11].input_precision | BF16 |
| stages[13].operations[11].accumulator_precision | FP32 |
| stages[13].operations[11].sparsity | dense |
| stages[13].operations[11].scalar_flops | 0 |
| stages[13].operations[11].special_ops | {} |
| stages[13].operations[11].source_detail.input[0] | 128 |
| stages[13].operations[11].source_detail.input[1] | 4096 |
| stages[13].operations[11].source_detail.weight_math[0] | 4096 |
| stages[13].operations[11].source_detail.weight_math[1] | 4096 |
| stages[13].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[13].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[11].source_detail.output[0] | 128 |
| stages[13].operations[11].source_detail.output[1] | 4096 |
| stages[13].operations[12].name | attention_residual |
| stages[13].operations[12].matrix_flops | 0 |
| stages[13].operations[12].input_precision | unknown (null) |
| stages[13].operations[12].accumulator_precision | unknown (null) |
| stages[13].operations[12].sparsity | unknown (null) |
| stages[13].operations[12].scalar_flops | 524288 |
| stages[13].operations[12].special_ops | {} |
| stages[13].operations[12].source_detail.inputs_each[0] | 128 |
| stages[13].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[13].operations[12].source_detail.output[0] | 128 |
| stages[13].operations[12].source_detail.output[1] | 4096 |
| stages[13].operations[13].name | post_attention_layernorm |
| stages[13].operations[13].matrix_flops | 0 |
| stages[13].operations[13].input_precision | unknown (null) |
| stages[13].operations[13].accumulator_precision | unknown (null) |
| stages[13].operations[13].sparsity | unknown (null) |
| stages[13].operations[13].scalar_flops | 2097280 |
| stages[13].operations[13].special_ops.rsqrt | 128 |
| stages[13].operations[13].source_detail.input[0] | 128 |
| stages[13].operations[13].source_detail.input[1] | 4096 |
| stages[13].operations[13].source_detail.weight[0] | 4096 |
| stages[13].operations[13].source_detail.output[0] | 128 |
| stages[13].operations[13].source_detail.output[1] | 4096 |
| stages[13].operations[14].name | gate_proj |
| stages[13].operations[14].matrix_flops | 12884901888 |
| stages[13].operations[14].input_precision | BF16 |
| stages[13].operations[14].accumulator_precision | FP32 |
| stages[13].operations[14].sparsity | dense |
| stages[13].operations[14].scalar_flops | 0 |
| stages[13].operations[14].special_ops | {} |
| stages[13].operations[14].source_detail.input[0] | 128 |
| stages[13].operations[14].source_detail.input[1] | 4096 |
| stages[13].operations[14].source_detail.weight_math[0] | 4096 |
| stages[13].operations[14].source_detail.weight_math[1] | 12288 |
| stages[13].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[13].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[14].source_detail.output[0] | 128 |
| stages[13].operations[14].source_detail.output[1] | 12288 |
| stages[13].operations[15].name | up_proj |
| stages[13].operations[15].matrix_flops | 12884901888 |
| stages[13].operations[15].input_precision | BF16 |
| stages[13].operations[15].accumulator_precision | FP32 |
| stages[13].operations[15].sparsity | dense |
| stages[13].operations[15].scalar_flops | 0 |
| stages[13].operations[15].special_ops | {} |
| stages[13].operations[15].source_detail.input[0] | 128 |
| stages[13].operations[15].source_detail.input[1] | 4096 |
| stages[13].operations[15].source_detail.weight_math[0] | 4096 |
| stages[13].operations[15].source_detail.weight_math[1] | 12288 |
| stages[13].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[13].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[13].operations[15].source_detail.output[0] | 128 |
| stages[13].operations[15].source_detail.output[1] | 12288 |
| stages[13].operations[16].name | silu_mul |
| stages[13].operations[16].matrix_flops | 0 |
| stages[13].operations[16].input_precision | unknown (null) |
| stages[13].operations[16].accumulator_precision | unknown (null) |
| stages[13].operations[16].sparsity | unknown (null) |
| stages[13].operations[16].scalar_flops | 6291456 |
| stages[13].operations[16].special_ops.exp | 1572864 |
| stages[13].operations[16].special_ops.negate | 1572864 |
| stages[13].operations[16].source_detail.gate[0] | 128 |
| stages[13].operations[16].source_detail.gate[1] | 12288 |
| stages[13].operations[16].source_detail.up[0] | 128 |
| stages[13].operations[16].source_detail.up[1] | 12288 |
| stages[13].operations[16].source_detail.output[0] | 128 |
| stages[13].operations[16].source_detail.output[1] | 12288 |
| stages[13].operations[17].name | down_proj |
| stages[13].operations[17].matrix_flops | 12884901888 |
| stages[13].operations[17].input_precision | BF16 |
| stages[13].operations[17].accumulator_precision | FP32 |
| stages[13].operations[17].sparsity | dense |
| stages[13].operations[17].scalar_flops | 0 |
| stages[13].operations[17].special_ops | {} |
| stages[13].operations[17].source_detail.input[0] | 128 |
| stages[13].operations[17].source_detail.input[1] | 12288 |
| stages[13].operations[17].source_detail.weight_math[0] | 12288 |
| stages[13].operations[17].source_detail.weight_math[1] | 4096 |
| stages[13].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[13].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[13].operations[17].source_detail.output[0] | 128 |
| stages[13].operations[17].source_detail.output[1] | 4096 |
| stages[13].operations[18].name | ffn_residual |
| stages[13].operations[18].matrix_flops | 0 |
| stages[13].operations[18].input_precision | unknown (null) |
| stages[13].operations[18].accumulator_precision | unknown (null) |
| stages[13].operations[18].sparsity | unknown (null) |
| stages[13].operations[18].scalar_flops | 524288 |
| stages[13].operations[18].special_ops | {} |
| stages[13].operations[18].source_detail.inputs_each[0] | 128 |
| stages[13].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[13].operations[18].source_detail.output[0] | 128 |
| stages[13].operations[18].source_detail.output[1] | 4096 |
| stages[14].id | layer:13 |
| stages[14].work.vector_fp32 | 17179904 |
| stages[14].work.special:rsqrt | 5376 |
| stages[14].work.interface_bytes | 438387200 |
| stages[14].work.matrix_bf16 | 49527390208 |
| stages[14].work.special:negate | 1900544 |
| stages[14].work.special:exp | 1837056 |
| stages[14].work.special:compare_max | 260096 |
| stages[14].work.special:mask_decisions | 524288 |
| stages[14].operations[0].name | input_layernorm |
| stages[14].operations[0].matrix_flops | 0 |
| stages[14].operations[0].input_precision | unknown (null) |
| stages[14].operations[0].accumulator_precision | unknown (null) |
| stages[14].operations[0].sparsity | unknown (null) |
| stages[14].operations[0].scalar_flops | 2097280 |
| stages[14].operations[0].special_ops.rsqrt | 128 |
| stages[14].operations[0].source_detail.input[0] | 128 |
| stages[14].operations[0].source_detail.input[1] | 4096 |
| stages[14].operations[0].source_detail.weight[0] | 4096 |
| stages[14].operations[0].source_detail.output[0] | 128 |
| stages[14].operations[0].source_detail.output[1] | 4096 |
| stages[14].operations[1].name | q_proj |
| stages[14].operations[1].matrix_flops | 4294967296 |
| stages[14].operations[1].input_precision | BF16 |
| stages[14].operations[1].accumulator_precision | FP32 |
| stages[14].operations[1].sparsity | dense |
| stages[14].operations[1].scalar_flops | 0 |
| stages[14].operations[1].special_ops | {} |
| stages[14].operations[1].source_detail.input[0] | 128 |
| stages[14].operations[1].source_detail.input[1] | 4096 |
| stages[14].operations[1].source_detail.weight_math[0] | 4096 |
| stages[14].operations[1].source_detail.weight_math[1] | 4096 |
| stages[14].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[14].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[1].source_detail.output[0] | 128 |
| stages[14].operations[1].source_detail.output[1] | 4096 |
| stages[14].operations[2].name | k_proj |
| stages[14].operations[2].matrix_flops | 1073741824 |
| stages[14].operations[2].input_precision | BF16 |
| stages[14].operations[2].accumulator_precision | FP32 |
| stages[14].operations[2].sparsity | dense |
| stages[14].operations[2].scalar_flops | 0 |
| stages[14].operations[2].special_ops | {} |
| stages[14].operations[2].source_detail.input[0] | 128 |
| stages[14].operations[2].source_detail.input[1] | 4096 |
| stages[14].operations[2].source_detail.weight_math[0] | 4096 |
| stages[14].operations[2].source_detail.weight_math[1] | 1024 |
| stages[14].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[14].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[2].source_detail.output[0] | 128 |
| stages[14].operations[2].source_detail.output[1] | 1024 |
| stages[14].operations[3].name | v_proj |
| stages[14].operations[3].matrix_flops | 1073741824 |
| stages[14].operations[3].input_precision | BF16 |
| stages[14].operations[3].accumulator_precision | FP32 |
| stages[14].operations[3].sparsity | dense |
| stages[14].operations[3].scalar_flops | 0 |
| stages[14].operations[3].special_ops | {} |
| stages[14].operations[3].source_detail.input[0] | 128 |
| stages[14].operations[3].source_detail.input[1] | 4096 |
| stages[14].operations[3].source_detail.weight_math[0] | 4096 |
| stages[14].operations[3].source_detail.weight_math[1] | 1024 |
| stages[14].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[14].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[3].source_detail.output[0] | 128 |
| stages[14].operations[3].source_detail.output[1] | 1024 |
| stages[14].operations[4].name | q_norm |
| stages[14].operations[4].matrix_flops | 0 |
| stages[14].operations[4].input_precision | unknown (null) |
| stages[14].operations[4].accumulator_precision | unknown (null) |
| stages[14].operations[4].sparsity | unknown (null) |
| stages[14].operations[4].scalar_flops | 2101248 |
| stages[14].operations[4].special_ops.rsqrt | 4096 |
| stages[14].operations[4].source_detail.input[0] | 4096 |
| stages[14].operations[4].source_detail.input[1] | 128 |
| stages[14].operations[4].source_detail.weight[0] | 128 |
| stages[14].operations[4].source_detail.output[0] | 4096 |
| stages[14].operations[4].source_detail.output[1] | 128 |
| stages[14].operations[5].name | k_norm |
| stages[14].operations[5].matrix_flops | 0 |
| stages[14].operations[5].input_precision | unknown (null) |
| stages[14].operations[5].accumulator_precision | unknown (null) |
| stages[14].operations[5].sparsity | unknown (null) |
| stages[14].operations[5].scalar_flops | 525312 |
| stages[14].operations[5].special_ops.rsqrt | 1024 |
| stages[14].operations[5].source_detail.input[0] | 1024 |
| stages[14].operations[5].source_detail.input[1] | 128 |
| stages[14].operations[5].source_detail.weight[0] | 128 |
| stages[14].operations[5].source_detail.output[0] | 1024 |
| stages[14].operations[5].source_detail.output[1] | 128 |
| stages[14].operations[6].name | apply_rope |
| stages[14].operations[6].matrix_flops | 0 |
| stages[14].operations[6].input_precision | unknown (null) |
| stages[14].operations[6].accumulator_precision | unknown (null) |
| stages[14].operations[6].sparsity | unknown (null) |
| stages[14].operations[6].scalar_flops | 1966080 |
| stages[14].operations[6].special_ops.negate | 327680 |
| stages[14].operations[6].source_detail.Q[0] | 1 |
| stages[14].operations[6].source_detail.Q[1] | 32 |
| stages[14].operations[6].source_detail.Q[2] | 128 |
| stages[14].operations[6].source_detail.Q[3] | 128 |
| stages[14].operations[6].source_detail.K[0] | 1 |
| stages[14].operations[6].source_detail.K[1] | 8 |
| stages[14].operations[6].source_detail.K[2] | 128 |
| stages[14].operations[6].source_detail.K[3] | 128 |
| stages[14].operations[7].name | kv_append |
| stages[14].operations[7].matrix_flops | 0 |
| stages[14].operations[7].input_precision | unknown (null) |
| stages[14].operations[7].accumulator_precision | unknown (null) |
| stages[14].operations[7].sparsity | unknown (null) |
| stages[14].operations[7].scalar_flops | 0 |
| stages[14].operations[7].special_ops | {} |
| stages[14].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[14].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[14].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[14].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[14].operations[8].name | qk |
| stages[14].operations[8].matrix_flops | 67633152 |
| stages[14].operations[8].input_precision | BF16 |
| stages[14].operations[8].accumulator_precision | FP32 |
| stages[14].operations[8].sparsity | dense |
| stages[14].operations[8].scalar_flops | 0 |
| stages[14].operations[8].special_ops | {} |
| stages[14].operations[8].source_detail.Q[0] | 1 |
| stages[14].operations[8].source_detail.Q[1] | 32 |
| stages[14].operations[8].source_detail.Q[2] | 128 |
| stages[14].operations[8].source_detail.Q[3] | 128 |
| stages[14].operations[8].source_detail.K_shared[0] | 1 |
| stages[14].operations[8].source_detail.K_shared[1] | 8 |
| stages[14].operations[8].source_detail.K_shared[2] | 128 |
| stages[14].operations[8].source_detail.K_shared[3] | 128 |
| stages[14].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[14].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[14].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[14].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[14].operations[9].name | score_scale_mask_softmax |
| stages[14].operations[9].matrix_flops | 0 |
| stages[14].operations[9].input_precision | unknown (null) |
| stages[14].operations[9].accumulator_precision | unknown (null) |
| stages[14].operations[9].sparsity | unknown (null) |
| stages[14].operations[9].scalar_flops | 1052672 |
| stages[14].operations[9].special_ops.exp | 264192 |
| stages[14].operations[9].special_ops.compare_max | 260096 |
| stages[14].operations[9].special_ops.mask_decisions | 524288 |
| stages[14].operations[9].source_detail.scores[0] | 1 |
| stages[14].operations[9].source_detail.scores[1] | 32 |
| stages[14].operations[9].source_detail.scores[2] | 128 |
| stages[14].operations[9].source_detail.scores[3] | 128 |
| stages[14].operations[10].name | pv |
| stages[14].operations[10].matrix_flops | 67633152 |
| stages[14].operations[10].input_precision | BF16 |
| stages[14].operations[10].accumulator_precision | FP32 |
| stages[14].operations[10].sparsity | dense |
| stages[14].operations[10].scalar_flops | 0 |
| stages[14].operations[10].special_ops | {} |
| stages[14].operations[10].source_detail.P[0] | 1 |
| stages[14].operations[10].source_detail.P[1] | 32 |
| stages[14].operations[10].source_detail.P[2] | 128 |
| stages[14].operations[10].source_detail.P[3] | 128 |
| stages[14].operations[10].source_detail.V_shared[0] | 1 |
| stages[14].operations[10].source_detail.V_shared[1] | 8 |
| stages[14].operations[10].source_detail.V_shared[2] | 128 |
| stages[14].operations[10].source_detail.V_shared[3] | 128 |
| stages[14].operations[10].source_detail.output[0] | 1 |
| stages[14].operations[10].source_detail.output[1] | 32 |
| stages[14].operations[10].source_detail.output[2] | 128 |
| stages[14].operations[10].source_detail.output[3] | 128 |
| stages[14].operations[11].name | o_proj |
| stages[14].operations[11].matrix_flops | 4294967296 |
| stages[14].operations[11].input_precision | BF16 |
| stages[14].operations[11].accumulator_precision | FP32 |
| stages[14].operations[11].sparsity | dense |
| stages[14].operations[11].scalar_flops | 0 |
| stages[14].operations[11].special_ops | {} |
| stages[14].operations[11].source_detail.input[0] | 128 |
| stages[14].operations[11].source_detail.input[1] | 4096 |
| stages[14].operations[11].source_detail.weight_math[0] | 4096 |
| stages[14].operations[11].source_detail.weight_math[1] | 4096 |
| stages[14].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[14].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[11].source_detail.output[0] | 128 |
| stages[14].operations[11].source_detail.output[1] | 4096 |
| stages[14].operations[12].name | attention_residual |
| stages[14].operations[12].matrix_flops | 0 |
| stages[14].operations[12].input_precision | unknown (null) |
| stages[14].operations[12].accumulator_precision | unknown (null) |
| stages[14].operations[12].sparsity | unknown (null) |
| stages[14].operations[12].scalar_flops | 524288 |
| stages[14].operations[12].special_ops | {} |
| stages[14].operations[12].source_detail.inputs_each[0] | 128 |
| stages[14].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[14].operations[12].source_detail.output[0] | 128 |
| stages[14].operations[12].source_detail.output[1] | 4096 |
| stages[14].operations[13].name | post_attention_layernorm |
| stages[14].operations[13].matrix_flops | 0 |
| stages[14].operations[13].input_precision | unknown (null) |
| stages[14].operations[13].accumulator_precision | unknown (null) |
| stages[14].operations[13].sparsity | unknown (null) |
| stages[14].operations[13].scalar_flops | 2097280 |
| stages[14].operations[13].special_ops.rsqrt | 128 |
| stages[14].operations[13].source_detail.input[0] | 128 |
| stages[14].operations[13].source_detail.input[1] | 4096 |
| stages[14].operations[13].source_detail.weight[0] | 4096 |
| stages[14].operations[13].source_detail.output[0] | 128 |
| stages[14].operations[13].source_detail.output[1] | 4096 |
| stages[14].operations[14].name | gate_proj |
| stages[14].operations[14].matrix_flops | 12884901888 |
| stages[14].operations[14].input_precision | BF16 |
| stages[14].operations[14].accumulator_precision | FP32 |
| stages[14].operations[14].sparsity | dense |
| stages[14].operations[14].scalar_flops | 0 |
| stages[14].operations[14].special_ops | {} |
| stages[14].operations[14].source_detail.input[0] | 128 |
| stages[14].operations[14].source_detail.input[1] | 4096 |
| stages[14].operations[14].source_detail.weight_math[0] | 4096 |
| stages[14].operations[14].source_detail.weight_math[1] | 12288 |
| stages[14].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[14].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[14].source_detail.output[0] | 128 |
| stages[14].operations[14].source_detail.output[1] | 12288 |
| stages[14].operations[15].name | up_proj |
| stages[14].operations[15].matrix_flops | 12884901888 |
| stages[14].operations[15].input_precision | BF16 |
| stages[14].operations[15].accumulator_precision | FP32 |
| stages[14].operations[15].sparsity | dense |
| stages[14].operations[15].scalar_flops | 0 |
| stages[14].operations[15].special_ops | {} |
| stages[14].operations[15].source_detail.input[0] | 128 |
| stages[14].operations[15].source_detail.input[1] | 4096 |
| stages[14].operations[15].source_detail.weight_math[0] | 4096 |
| stages[14].operations[15].source_detail.weight_math[1] | 12288 |
| stages[14].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[14].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[14].operations[15].source_detail.output[0] | 128 |
| stages[14].operations[15].source_detail.output[1] | 12288 |
| stages[14].operations[16].name | silu_mul |
| stages[14].operations[16].matrix_flops | 0 |
| stages[14].operations[16].input_precision | unknown (null) |
| stages[14].operations[16].accumulator_precision | unknown (null) |
| stages[14].operations[16].sparsity | unknown (null) |
| stages[14].operations[16].scalar_flops | 6291456 |
| stages[14].operations[16].special_ops.exp | 1572864 |
| stages[14].operations[16].special_ops.negate | 1572864 |
| stages[14].operations[16].source_detail.gate[0] | 128 |
| stages[14].operations[16].source_detail.gate[1] | 12288 |
| stages[14].operations[16].source_detail.up[0] | 128 |
| stages[14].operations[16].source_detail.up[1] | 12288 |
| stages[14].operations[16].source_detail.output[0] | 128 |
| stages[14].operations[16].source_detail.output[1] | 12288 |
| stages[14].operations[17].name | down_proj |
| stages[14].operations[17].matrix_flops | 12884901888 |
| stages[14].operations[17].input_precision | BF16 |
| stages[14].operations[17].accumulator_precision | FP32 |
| stages[14].operations[17].sparsity | dense |
| stages[14].operations[17].scalar_flops | 0 |
| stages[14].operations[17].special_ops | {} |
| stages[14].operations[17].source_detail.input[0] | 128 |
| stages[14].operations[17].source_detail.input[1] | 12288 |
| stages[14].operations[17].source_detail.weight_math[0] | 12288 |
| stages[14].operations[17].source_detail.weight_math[1] | 4096 |
| stages[14].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[14].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[14].operations[17].source_detail.output[0] | 128 |
| stages[14].operations[17].source_detail.output[1] | 4096 |
| stages[14].operations[18].name | ffn_residual |
| stages[14].operations[18].matrix_flops | 0 |
| stages[14].operations[18].input_precision | unknown (null) |
| stages[14].operations[18].accumulator_precision | unknown (null) |
| stages[14].operations[18].sparsity | unknown (null) |
| stages[14].operations[18].scalar_flops | 524288 |
| stages[14].operations[18].special_ops | {} |
| stages[14].operations[18].source_detail.inputs_each[0] | 128 |
| stages[14].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[14].operations[18].source_detail.output[0] | 128 |
| stages[14].operations[18].source_detail.output[1] | 4096 |
| stages[15].id | layer:14 |
| stages[15].work.vector_fp32 | 17179904 |
| stages[15].work.special:rsqrt | 5376 |
| stages[15].work.interface_bytes | 438387200 |
| stages[15].work.matrix_bf16 | 49527390208 |
| stages[15].work.special:negate | 1900544 |
| stages[15].work.special:exp | 1837056 |
| stages[15].work.special:compare_max | 260096 |
| stages[15].work.special:mask_decisions | 524288 |
| stages[15].operations[0].name | input_layernorm |
| stages[15].operations[0].matrix_flops | 0 |
| stages[15].operations[0].input_precision | unknown (null) |
| stages[15].operations[0].accumulator_precision | unknown (null) |
| stages[15].operations[0].sparsity | unknown (null) |
| stages[15].operations[0].scalar_flops | 2097280 |
| stages[15].operations[0].special_ops.rsqrt | 128 |
| stages[15].operations[0].source_detail.input[0] | 128 |
| stages[15].operations[0].source_detail.input[1] | 4096 |
| stages[15].operations[0].source_detail.weight[0] | 4096 |
| stages[15].operations[0].source_detail.output[0] | 128 |
| stages[15].operations[0].source_detail.output[1] | 4096 |
| stages[15].operations[1].name | q_proj |
| stages[15].operations[1].matrix_flops | 4294967296 |
| stages[15].operations[1].input_precision | BF16 |
| stages[15].operations[1].accumulator_precision | FP32 |
| stages[15].operations[1].sparsity | dense |
| stages[15].operations[1].scalar_flops | 0 |
| stages[15].operations[1].special_ops | {} |
| stages[15].operations[1].source_detail.input[0] | 128 |
| stages[15].operations[1].source_detail.input[1] | 4096 |
| stages[15].operations[1].source_detail.weight_math[0] | 4096 |
| stages[15].operations[1].source_detail.weight_math[1] | 4096 |
| stages[15].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[15].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[1].source_detail.output[0] | 128 |
| stages[15].operations[1].source_detail.output[1] | 4096 |
| stages[15].operations[2].name | k_proj |
| stages[15].operations[2].matrix_flops | 1073741824 |
| stages[15].operations[2].input_precision | BF16 |
| stages[15].operations[2].accumulator_precision | FP32 |
| stages[15].operations[2].sparsity | dense |
| stages[15].operations[2].scalar_flops | 0 |
| stages[15].operations[2].special_ops | {} |
| stages[15].operations[2].source_detail.input[0] | 128 |
| stages[15].operations[2].source_detail.input[1] | 4096 |
| stages[15].operations[2].source_detail.weight_math[0] | 4096 |
| stages[15].operations[2].source_detail.weight_math[1] | 1024 |
| stages[15].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[15].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[2].source_detail.output[0] | 128 |
| stages[15].operations[2].source_detail.output[1] | 1024 |
| stages[15].operations[3].name | v_proj |
| stages[15].operations[3].matrix_flops | 1073741824 |
| stages[15].operations[3].input_precision | BF16 |
| stages[15].operations[3].accumulator_precision | FP32 |
| stages[15].operations[3].sparsity | dense |
| stages[15].operations[3].scalar_flops | 0 |
| stages[15].operations[3].special_ops | {} |
| stages[15].operations[3].source_detail.input[0] | 128 |
| stages[15].operations[3].source_detail.input[1] | 4096 |
| stages[15].operations[3].source_detail.weight_math[0] | 4096 |
| stages[15].operations[3].source_detail.weight_math[1] | 1024 |
| stages[15].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[15].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[3].source_detail.output[0] | 128 |
| stages[15].operations[3].source_detail.output[1] | 1024 |
| stages[15].operations[4].name | q_norm |
| stages[15].operations[4].matrix_flops | 0 |
| stages[15].operations[4].input_precision | unknown (null) |
| stages[15].operations[4].accumulator_precision | unknown (null) |
| stages[15].operations[4].sparsity | unknown (null) |
| stages[15].operations[4].scalar_flops | 2101248 |
| stages[15].operations[4].special_ops.rsqrt | 4096 |
| stages[15].operations[4].source_detail.input[0] | 4096 |
| stages[15].operations[4].source_detail.input[1] | 128 |
| stages[15].operations[4].source_detail.weight[0] | 128 |
| stages[15].operations[4].source_detail.output[0] | 4096 |
| stages[15].operations[4].source_detail.output[1] | 128 |
| stages[15].operations[5].name | k_norm |
| stages[15].operations[5].matrix_flops | 0 |
| stages[15].operations[5].input_precision | unknown (null) |
| stages[15].operations[5].accumulator_precision | unknown (null) |
| stages[15].operations[5].sparsity | unknown (null) |
| stages[15].operations[5].scalar_flops | 525312 |
| stages[15].operations[5].special_ops.rsqrt | 1024 |
| stages[15].operations[5].source_detail.input[0] | 1024 |
| stages[15].operations[5].source_detail.input[1] | 128 |
| stages[15].operations[5].source_detail.weight[0] | 128 |
| stages[15].operations[5].source_detail.output[0] | 1024 |
| stages[15].operations[5].source_detail.output[1] | 128 |
| stages[15].operations[6].name | apply_rope |
| stages[15].operations[6].matrix_flops | 0 |
| stages[15].operations[6].input_precision | unknown (null) |
| stages[15].operations[6].accumulator_precision | unknown (null) |
| stages[15].operations[6].sparsity | unknown (null) |
| stages[15].operations[6].scalar_flops | 1966080 |
| stages[15].operations[6].special_ops.negate | 327680 |
| stages[15].operations[6].source_detail.Q[0] | 1 |
| stages[15].operations[6].source_detail.Q[1] | 32 |
| stages[15].operations[6].source_detail.Q[2] | 128 |
| stages[15].operations[6].source_detail.Q[3] | 128 |
| stages[15].operations[6].source_detail.K[0] | 1 |
| stages[15].operations[6].source_detail.K[1] | 8 |
| stages[15].operations[6].source_detail.K[2] | 128 |
| stages[15].operations[6].source_detail.K[3] | 128 |
| stages[15].operations[7].name | kv_append |
| stages[15].operations[7].matrix_flops | 0 |
| stages[15].operations[7].input_precision | unknown (null) |
| stages[15].operations[7].accumulator_precision | unknown (null) |
| stages[15].operations[7].sparsity | unknown (null) |
| stages[15].operations[7].scalar_flops | 0 |
| stages[15].operations[7].special_ops | {} |
| stages[15].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[15].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[15].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[15].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[15].operations[8].name | qk |
| stages[15].operations[8].matrix_flops | 67633152 |
| stages[15].operations[8].input_precision | BF16 |
| stages[15].operations[8].accumulator_precision | FP32 |
| stages[15].operations[8].sparsity | dense |
| stages[15].operations[8].scalar_flops | 0 |
| stages[15].operations[8].special_ops | {} |
| stages[15].operations[8].source_detail.Q[0] | 1 |
| stages[15].operations[8].source_detail.Q[1] | 32 |
| stages[15].operations[8].source_detail.Q[2] | 128 |
| stages[15].operations[8].source_detail.Q[3] | 128 |
| stages[15].operations[8].source_detail.K_shared[0] | 1 |
| stages[15].operations[8].source_detail.K_shared[1] | 8 |
| stages[15].operations[8].source_detail.K_shared[2] | 128 |
| stages[15].operations[8].source_detail.K_shared[3] | 128 |
| stages[15].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[15].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[15].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[15].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[15].operations[9].name | score_scale_mask_softmax |
| stages[15].operations[9].matrix_flops | 0 |
| stages[15].operations[9].input_precision | unknown (null) |
| stages[15].operations[9].accumulator_precision | unknown (null) |
| stages[15].operations[9].sparsity | unknown (null) |
| stages[15].operations[9].scalar_flops | 1052672 |
| stages[15].operations[9].special_ops.exp | 264192 |
| stages[15].operations[9].special_ops.compare_max | 260096 |
| stages[15].operations[9].special_ops.mask_decisions | 524288 |
| stages[15].operations[9].source_detail.scores[0] | 1 |
| stages[15].operations[9].source_detail.scores[1] | 32 |
| stages[15].operations[9].source_detail.scores[2] | 128 |
| stages[15].operations[9].source_detail.scores[3] | 128 |
| stages[15].operations[10].name | pv |
| stages[15].operations[10].matrix_flops | 67633152 |
| stages[15].operations[10].input_precision | BF16 |
| stages[15].operations[10].accumulator_precision | FP32 |
| stages[15].operations[10].sparsity | dense |
| stages[15].operations[10].scalar_flops | 0 |
| stages[15].operations[10].special_ops | {} |
| stages[15].operations[10].source_detail.P[0] | 1 |
| stages[15].operations[10].source_detail.P[1] | 32 |
| stages[15].operations[10].source_detail.P[2] | 128 |
| stages[15].operations[10].source_detail.P[3] | 128 |
| stages[15].operations[10].source_detail.V_shared[0] | 1 |
| stages[15].operations[10].source_detail.V_shared[1] | 8 |
| stages[15].operations[10].source_detail.V_shared[2] | 128 |
| stages[15].operations[10].source_detail.V_shared[3] | 128 |
| stages[15].operations[10].source_detail.output[0] | 1 |
| stages[15].operations[10].source_detail.output[1] | 32 |
| stages[15].operations[10].source_detail.output[2] | 128 |
| stages[15].operations[10].source_detail.output[3] | 128 |
| stages[15].operations[11].name | o_proj |
| stages[15].operations[11].matrix_flops | 4294967296 |
| stages[15].operations[11].input_precision | BF16 |
| stages[15].operations[11].accumulator_precision | FP32 |
| stages[15].operations[11].sparsity | dense |
| stages[15].operations[11].scalar_flops | 0 |
| stages[15].operations[11].special_ops | {} |
| stages[15].operations[11].source_detail.input[0] | 128 |
| stages[15].operations[11].source_detail.input[1] | 4096 |
| stages[15].operations[11].source_detail.weight_math[0] | 4096 |
| stages[15].operations[11].source_detail.weight_math[1] | 4096 |
| stages[15].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[15].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[11].source_detail.output[0] | 128 |
| stages[15].operations[11].source_detail.output[1] | 4096 |
| stages[15].operations[12].name | attention_residual |
| stages[15].operations[12].matrix_flops | 0 |
| stages[15].operations[12].input_precision | unknown (null) |
| stages[15].operations[12].accumulator_precision | unknown (null) |
| stages[15].operations[12].sparsity | unknown (null) |
| stages[15].operations[12].scalar_flops | 524288 |
| stages[15].operations[12].special_ops | {} |
| stages[15].operations[12].source_detail.inputs_each[0] | 128 |
| stages[15].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[15].operations[12].source_detail.output[0] | 128 |
| stages[15].operations[12].source_detail.output[1] | 4096 |
| stages[15].operations[13].name | post_attention_layernorm |
| stages[15].operations[13].matrix_flops | 0 |
| stages[15].operations[13].input_precision | unknown (null) |
| stages[15].operations[13].accumulator_precision | unknown (null) |
| stages[15].operations[13].sparsity | unknown (null) |
| stages[15].operations[13].scalar_flops | 2097280 |
| stages[15].operations[13].special_ops.rsqrt | 128 |
| stages[15].operations[13].source_detail.input[0] | 128 |
| stages[15].operations[13].source_detail.input[1] | 4096 |
| stages[15].operations[13].source_detail.weight[0] | 4096 |
| stages[15].operations[13].source_detail.output[0] | 128 |
| stages[15].operations[13].source_detail.output[1] | 4096 |
| stages[15].operations[14].name | gate_proj |
| stages[15].operations[14].matrix_flops | 12884901888 |
| stages[15].operations[14].input_precision | BF16 |
| stages[15].operations[14].accumulator_precision | FP32 |
| stages[15].operations[14].sparsity | dense |
| stages[15].operations[14].scalar_flops | 0 |
| stages[15].operations[14].special_ops | {} |
| stages[15].operations[14].source_detail.input[0] | 128 |
| stages[15].operations[14].source_detail.input[1] | 4096 |
| stages[15].operations[14].source_detail.weight_math[0] | 4096 |
| stages[15].operations[14].source_detail.weight_math[1] | 12288 |
| stages[15].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[15].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[14].source_detail.output[0] | 128 |
| stages[15].operations[14].source_detail.output[1] | 12288 |
| stages[15].operations[15].name | up_proj |
| stages[15].operations[15].matrix_flops | 12884901888 |
| stages[15].operations[15].input_precision | BF16 |
| stages[15].operations[15].accumulator_precision | FP32 |
| stages[15].operations[15].sparsity | dense |
| stages[15].operations[15].scalar_flops | 0 |
| stages[15].operations[15].special_ops | {} |
| stages[15].operations[15].source_detail.input[0] | 128 |
| stages[15].operations[15].source_detail.input[1] | 4096 |
| stages[15].operations[15].source_detail.weight_math[0] | 4096 |
| stages[15].operations[15].source_detail.weight_math[1] | 12288 |
| stages[15].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[15].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[15].operations[15].source_detail.output[0] | 128 |
| stages[15].operations[15].source_detail.output[1] | 12288 |
| stages[15].operations[16].name | silu_mul |
| stages[15].operations[16].matrix_flops | 0 |
| stages[15].operations[16].input_precision | unknown (null) |
| stages[15].operations[16].accumulator_precision | unknown (null) |
| stages[15].operations[16].sparsity | unknown (null) |
| stages[15].operations[16].scalar_flops | 6291456 |
| stages[15].operations[16].special_ops.exp | 1572864 |
| stages[15].operations[16].special_ops.negate | 1572864 |
| stages[15].operations[16].source_detail.gate[0] | 128 |
| stages[15].operations[16].source_detail.gate[1] | 12288 |
| stages[15].operations[16].source_detail.up[0] | 128 |
| stages[15].operations[16].source_detail.up[1] | 12288 |
| stages[15].operations[16].source_detail.output[0] | 128 |
| stages[15].operations[16].source_detail.output[1] | 12288 |
| stages[15].operations[17].name | down_proj |
| stages[15].operations[17].matrix_flops | 12884901888 |
| stages[15].operations[17].input_precision | BF16 |
| stages[15].operations[17].accumulator_precision | FP32 |
| stages[15].operations[17].sparsity | dense |
| stages[15].operations[17].scalar_flops | 0 |
| stages[15].operations[17].special_ops | {} |
| stages[15].operations[17].source_detail.input[0] | 128 |
| stages[15].operations[17].source_detail.input[1] | 12288 |
| stages[15].operations[17].source_detail.weight_math[0] | 12288 |
| stages[15].operations[17].source_detail.weight_math[1] | 4096 |
| stages[15].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[15].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[15].operations[17].source_detail.output[0] | 128 |
| stages[15].operations[17].source_detail.output[1] | 4096 |
| stages[15].operations[18].name | ffn_residual |
| stages[15].operations[18].matrix_flops | 0 |
| stages[15].operations[18].input_precision | unknown (null) |
| stages[15].operations[18].accumulator_precision | unknown (null) |
| stages[15].operations[18].sparsity | unknown (null) |
| stages[15].operations[18].scalar_flops | 524288 |
| stages[15].operations[18].special_ops | {} |
| stages[15].operations[18].source_detail.inputs_each[0] | 128 |
| stages[15].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[15].operations[18].source_detail.output[0] | 128 |
| stages[15].operations[18].source_detail.output[1] | 4096 |
| stages[16].id | layer:15 |
| stages[16].work.vector_fp32 | 17179904 |
| stages[16].work.special:rsqrt | 5376 |
| stages[16].work.interface_bytes | 438387200 |
| stages[16].work.matrix_bf16 | 49527390208 |
| stages[16].work.special:negate | 1900544 |
| stages[16].work.special:exp | 1837056 |
| stages[16].work.special:compare_max | 260096 |
| stages[16].work.special:mask_decisions | 524288 |
| stages[16].operations[0].name | input_layernorm |
| stages[16].operations[0].matrix_flops | 0 |
| stages[16].operations[0].input_precision | unknown (null) |
| stages[16].operations[0].accumulator_precision | unknown (null) |
| stages[16].operations[0].sparsity | unknown (null) |
| stages[16].operations[0].scalar_flops | 2097280 |
| stages[16].operations[0].special_ops.rsqrt | 128 |
| stages[16].operations[0].source_detail.input[0] | 128 |
| stages[16].operations[0].source_detail.input[1] | 4096 |
| stages[16].operations[0].source_detail.weight[0] | 4096 |
| stages[16].operations[0].source_detail.output[0] | 128 |
| stages[16].operations[0].source_detail.output[1] | 4096 |
| stages[16].operations[1].name | q_proj |
| stages[16].operations[1].matrix_flops | 4294967296 |
| stages[16].operations[1].input_precision | BF16 |
| stages[16].operations[1].accumulator_precision | FP32 |
| stages[16].operations[1].sparsity | dense |
| stages[16].operations[1].scalar_flops | 0 |
| stages[16].operations[1].special_ops | {} |
| stages[16].operations[1].source_detail.input[0] | 128 |
| stages[16].operations[1].source_detail.input[1] | 4096 |
| stages[16].operations[1].source_detail.weight_math[0] | 4096 |
| stages[16].operations[1].source_detail.weight_math[1] | 4096 |
| stages[16].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[16].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[1].source_detail.output[0] | 128 |
| stages[16].operations[1].source_detail.output[1] | 4096 |
| stages[16].operations[2].name | k_proj |
| stages[16].operations[2].matrix_flops | 1073741824 |
| stages[16].operations[2].input_precision | BF16 |
| stages[16].operations[2].accumulator_precision | FP32 |
| stages[16].operations[2].sparsity | dense |
| stages[16].operations[2].scalar_flops | 0 |
| stages[16].operations[2].special_ops | {} |
| stages[16].operations[2].source_detail.input[0] | 128 |
| stages[16].operations[2].source_detail.input[1] | 4096 |
| stages[16].operations[2].source_detail.weight_math[0] | 4096 |
| stages[16].operations[2].source_detail.weight_math[1] | 1024 |
| stages[16].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[16].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[2].source_detail.output[0] | 128 |
| stages[16].operations[2].source_detail.output[1] | 1024 |
| stages[16].operations[3].name | v_proj |
| stages[16].operations[3].matrix_flops | 1073741824 |
| stages[16].operations[3].input_precision | BF16 |
| stages[16].operations[3].accumulator_precision | FP32 |
| stages[16].operations[3].sparsity | dense |
| stages[16].operations[3].scalar_flops | 0 |
| stages[16].operations[3].special_ops | {} |
| stages[16].operations[3].source_detail.input[0] | 128 |
| stages[16].operations[3].source_detail.input[1] | 4096 |
| stages[16].operations[3].source_detail.weight_math[0] | 4096 |
| stages[16].operations[3].source_detail.weight_math[1] | 1024 |
| stages[16].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[16].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[3].source_detail.output[0] | 128 |
| stages[16].operations[3].source_detail.output[1] | 1024 |
| stages[16].operations[4].name | q_norm |
| stages[16].operations[4].matrix_flops | 0 |
| stages[16].operations[4].input_precision | unknown (null) |
| stages[16].operations[4].accumulator_precision | unknown (null) |
| stages[16].operations[4].sparsity | unknown (null) |
| stages[16].operations[4].scalar_flops | 2101248 |
| stages[16].operations[4].special_ops.rsqrt | 4096 |
| stages[16].operations[4].source_detail.input[0] | 4096 |
| stages[16].operations[4].source_detail.input[1] | 128 |
| stages[16].operations[4].source_detail.weight[0] | 128 |
| stages[16].operations[4].source_detail.output[0] | 4096 |
| stages[16].operations[4].source_detail.output[1] | 128 |
| stages[16].operations[5].name | k_norm |
| stages[16].operations[5].matrix_flops | 0 |
| stages[16].operations[5].input_precision | unknown (null) |
| stages[16].operations[5].accumulator_precision | unknown (null) |
| stages[16].operations[5].sparsity | unknown (null) |
| stages[16].operations[5].scalar_flops | 525312 |
| stages[16].operations[5].special_ops.rsqrt | 1024 |
| stages[16].operations[5].source_detail.input[0] | 1024 |
| stages[16].operations[5].source_detail.input[1] | 128 |
| stages[16].operations[5].source_detail.weight[0] | 128 |
| stages[16].operations[5].source_detail.output[0] | 1024 |
| stages[16].operations[5].source_detail.output[1] | 128 |
| stages[16].operations[6].name | apply_rope |
| stages[16].operations[6].matrix_flops | 0 |
| stages[16].operations[6].input_precision | unknown (null) |
| stages[16].operations[6].accumulator_precision | unknown (null) |
| stages[16].operations[6].sparsity | unknown (null) |
| stages[16].operations[6].scalar_flops | 1966080 |
| stages[16].operations[6].special_ops.negate | 327680 |
| stages[16].operations[6].source_detail.Q[0] | 1 |
| stages[16].operations[6].source_detail.Q[1] | 32 |
| stages[16].operations[6].source_detail.Q[2] | 128 |
| stages[16].operations[6].source_detail.Q[3] | 128 |
| stages[16].operations[6].source_detail.K[0] | 1 |
| stages[16].operations[6].source_detail.K[1] | 8 |
| stages[16].operations[6].source_detail.K[2] | 128 |
| stages[16].operations[6].source_detail.K[3] | 128 |
| stages[16].operations[7].name | kv_append |
| stages[16].operations[7].matrix_flops | 0 |
| stages[16].operations[7].input_precision | unknown (null) |
| stages[16].operations[7].accumulator_precision | unknown (null) |
| stages[16].operations[7].sparsity | unknown (null) |
| stages[16].operations[7].scalar_flops | 0 |
| stages[16].operations[7].special_ops | {} |
| stages[16].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[16].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[16].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[16].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[16].operations[8].name | qk |
| stages[16].operations[8].matrix_flops | 67633152 |
| stages[16].operations[8].input_precision | BF16 |
| stages[16].operations[8].accumulator_precision | FP32 |
| stages[16].operations[8].sparsity | dense |
| stages[16].operations[8].scalar_flops | 0 |
| stages[16].operations[8].special_ops | {} |
| stages[16].operations[8].source_detail.Q[0] | 1 |
| stages[16].operations[8].source_detail.Q[1] | 32 |
| stages[16].operations[8].source_detail.Q[2] | 128 |
| stages[16].operations[8].source_detail.Q[3] | 128 |
| stages[16].operations[8].source_detail.K_shared[0] | 1 |
| stages[16].operations[8].source_detail.K_shared[1] | 8 |
| stages[16].operations[8].source_detail.K_shared[2] | 128 |
| stages[16].operations[8].source_detail.K_shared[3] | 128 |
| stages[16].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[16].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[16].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[16].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[16].operations[9].name | score_scale_mask_softmax |
| stages[16].operations[9].matrix_flops | 0 |
| stages[16].operations[9].input_precision | unknown (null) |
| stages[16].operations[9].accumulator_precision | unknown (null) |
| stages[16].operations[9].sparsity | unknown (null) |
| stages[16].operations[9].scalar_flops | 1052672 |
| stages[16].operations[9].special_ops.exp | 264192 |
| stages[16].operations[9].special_ops.compare_max | 260096 |
| stages[16].operations[9].special_ops.mask_decisions | 524288 |
| stages[16].operations[9].source_detail.scores[0] | 1 |
| stages[16].operations[9].source_detail.scores[1] | 32 |
| stages[16].operations[9].source_detail.scores[2] | 128 |
| stages[16].operations[9].source_detail.scores[3] | 128 |
| stages[16].operations[10].name | pv |
| stages[16].operations[10].matrix_flops | 67633152 |
| stages[16].operations[10].input_precision | BF16 |
| stages[16].operations[10].accumulator_precision | FP32 |
| stages[16].operations[10].sparsity | dense |
| stages[16].operations[10].scalar_flops | 0 |
| stages[16].operations[10].special_ops | {} |
| stages[16].operations[10].source_detail.P[0] | 1 |
| stages[16].operations[10].source_detail.P[1] | 32 |
| stages[16].operations[10].source_detail.P[2] | 128 |
| stages[16].operations[10].source_detail.P[3] | 128 |
| stages[16].operations[10].source_detail.V_shared[0] | 1 |
| stages[16].operations[10].source_detail.V_shared[1] | 8 |
| stages[16].operations[10].source_detail.V_shared[2] | 128 |
| stages[16].operations[10].source_detail.V_shared[3] | 128 |
| stages[16].operations[10].source_detail.output[0] | 1 |
| stages[16].operations[10].source_detail.output[1] | 32 |
| stages[16].operations[10].source_detail.output[2] | 128 |
| stages[16].operations[10].source_detail.output[3] | 128 |
| stages[16].operations[11].name | o_proj |
| stages[16].operations[11].matrix_flops | 4294967296 |
| stages[16].operations[11].input_precision | BF16 |
| stages[16].operations[11].accumulator_precision | FP32 |
| stages[16].operations[11].sparsity | dense |
| stages[16].operations[11].scalar_flops | 0 |
| stages[16].operations[11].special_ops | {} |
| stages[16].operations[11].source_detail.input[0] | 128 |
| stages[16].operations[11].source_detail.input[1] | 4096 |
| stages[16].operations[11].source_detail.weight_math[0] | 4096 |
| stages[16].operations[11].source_detail.weight_math[1] | 4096 |
| stages[16].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[16].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[11].source_detail.output[0] | 128 |
| stages[16].operations[11].source_detail.output[1] | 4096 |
| stages[16].operations[12].name | attention_residual |
| stages[16].operations[12].matrix_flops | 0 |
| stages[16].operations[12].input_precision | unknown (null) |
| stages[16].operations[12].accumulator_precision | unknown (null) |
| stages[16].operations[12].sparsity | unknown (null) |
| stages[16].operations[12].scalar_flops | 524288 |
| stages[16].operations[12].special_ops | {} |
| stages[16].operations[12].source_detail.inputs_each[0] | 128 |
| stages[16].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[16].operations[12].source_detail.output[0] | 128 |
| stages[16].operations[12].source_detail.output[1] | 4096 |
| stages[16].operations[13].name | post_attention_layernorm |
| stages[16].operations[13].matrix_flops | 0 |
| stages[16].operations[13].input_precision | unknown (null) |
| stages[16].operations[13].accumulator_precision | unknown (null) |
| stages[16].operations[13].sparsity | unknown (null) |
| stages[16].operations[13].scalar_flops | 2097280 |
| stages[16].operations[13].special_ops.rsqrt | 128 |
| stages[16].operations[13].source_detail.input[0] | 128 |
| stages[16].operations[13].source_detail.input[1] | 4096 |
| stages[16].operations[13].source_detail.weight[0] | 4096 |
| stages[16].operations[13].source_detail.output[0] | 128 |
| stages[16].operations[13].source_detail.output[1] | 4096 |
| stages[16].operations[14].name | gate_proj |
| stages[16].operations[14].matrix_flops | 12884901888 |
| stages[16].operations[14].input_precision | BF16 |
| stages[16].operations[14].accumulator_precision | FP32 |
| stages[16].operations[14].sparsity | dense |
| stages[16].operations[14].scalar_flops | 0 |
| stages[16].operations[14].special_ops | {} |
| stages[16].operations[14].source_detail.input[0] | 128 |
| stages[16].operations[14].source_detail.input[1] | 4096 |
| stages[16].operations[14].source_detail.weight_math[0] | 4096 |
| stages[16].operations[14].source_detail.weight_math[1] | 12288 |
| stages[16].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[16].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[14].source_detail.output[0] | 128 |
| stages[16].operations[14].source_detail.output[1] | 12288 |
| stages[16].operations[15].name | up_proj |
| stages[16].operations[15].matrix_flops | 12884901888 |
| stages[16].operations[15].input_precision | BF16 |
| stages[16].operations[15].accumulator_precision | FP32 |
| stages[16].operations[15].sparsity | dense |
| stages[16].operations[15].scalar_flops | 0 |
| stages[16].operations[15].special_ops | {} |
| stages[16].operations[15].source_detail.input[0] | 128 |
| stages[16].operations[15].source_detail.input[1] | 4096 |
| stages[16].operations[15].source_detail.weight_math[0] | 4096 |
| stages[16].operations[15].source_detail.weight_math[1] | 12288 |
| stages[16].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[16].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[16].operations[15].source_detail.output[0] | 128 |
| stages[16].operations[15].source_detail.output[1] | 12288 |
| stages[16].operations[16].name | silu_mul |
| stages[16].operations[16].matrix_flops | 0 |
| stages[16].operations[16].input_precision | unknown (null) |
| stages[16].operations[16].accumulator_precision | unknown (null) |
| stages[16].operations[16].sparsity | unknown (null) |
| stages[16].operations[16].scalar_flops | 6291456 |
| stages[16].operations[16].special_ops.exp | 1572864 |
| stages[16].operations[16].special_ops.negate | 1572864 |
| stages[16].operations[16].source_detail.gate[0] | 128 |
| stages[16].operations[16].source_detail.gate[1] | 12288 |
| stages[16].operations[16].source_detail.up[0] | 128 |
| stages[16].operations[16].source_detail.up[1] | 12288 |
| stages[16].operations[16].source_detail.output[0] | 128 |
| stages[16].operations[16].source_detail.output[1] | 12288 |
| stages[16].operations[17].name | down_proj |
| stages[16].operations[17].matrix_flops | 12884901888 |
| stages[16].operations[17].input_precision | BF16 |
| stages[16].operations[17].accumulator_precision | FP32 |
| stages[16].operations[17].sparsity | dense |
| stages[16].operations[17].scalar_flops | 0 |
| stages[16].operations[17].special_ops | {} |
| stages[16].operations[17].source_detail.input[0] | 128 |
| stages[16].operations[17].source_detail.input[1] | 12288 |
| stages[16].operations[17].source_detail.weight_math[0] | 12288 |
| stages[16].operations[17].source_detail.weight_math[1] | 4096 |
| stages[16].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[16].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[16].operations[17].source_detail.output[0] | 128 |
| stages[16].operations[17].source_detail.output[1] | 4096 |
| stages[16].operations[18].name | ffn_residual |
| stages[16].operations[18].matrix_flops | 0 |
| stages[16].operations[18].input_precision | unknown (null) |
| stages[16].operations[18].accumulator_precision | unknown (null) |
| stages[16].operations[18].sparsity | unknown (null) |
| stages[16].operations[18].scalar_flops | 524288 |
| stages[16].operations[18].special_ops | {} |
| stages[16].operations[18].source_detail.inputs_each[0] | 128 |
| stages[16].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[16].operations[18].source_detail.output[0] | 128 |
| stages[16].operations[18].source_detail.output[1] | 4096 |
| stages[17].id | layer:16 |
| stages[17].work.vector_fp32 | 17179904 |
| stages[17].work.special:rsqrt | 5376 |
| stages[17].work.interface_bytes | 438387200 |
| stages[17].work.matrix_bf16 | 49527390208 |
| stages[17].work.special:negate | 1900544 |
| stages[17].work.special:exp | 1837056 |
| stages[17].work.special:compare_max | 260096 |
| stages[17].work.special:mask_decisions | 524288 |
| stages[17].operations[0].name | input_layernorm |
| stages[17].operations[0].matrix_flops | 0 |
| stages[17].operations[0].input_precision | unknown (null) |
| stages[17].operations[0].accumulator_precision | unknown (null) |
| stages[17].operations[0].sparsity | unknown (null) |
| stages[17].operations[0].scalar_flops | 2097280 |
| stages[17].operations[0].special_ops.rsqrt | 128 |
| stages[17].operations[0].source_detail.input[0] | 128 |
| stages[17].operations[0].source_detail.input[1] | 4096 |
| stages[17].operations[0].source_detail.weight[0] | 4096 |
| stages[17].operations[0].source_detail.output[0] | 128 |
| stages[17].operations[0].source_detail.output[1] | 4096 |
| stages[17].operations[1].name | q_proj |
| stages[17].operations[1].matrix_flops | 4294967296 |
| stages[17].operations[1].input_precision | BF16 |
| stages[17].operations[1].accumulator_precision | FP32 |
| stages[17].operations[1].sparsity | dense |
| stages[17].operations[1].scalar_flops | 0 |
| stages[17].operations[1].special_ops | {} |
| stages[17].operations[1].source_detail.input[0] | 128 |
| stages[17].operations[1].source_detail.input[1] | 4096 |
| stages[17].operations[1].source_detail.weight_math[0] | 4096 |
| stages[17].operations[1].source_detail.weight_math[1] | 4096 |
| stages[17].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[17].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[1].source_detail.output[0] | 128 |
| stages[17].operations[1].source_detail.output[1] | 4096 |
| stages[17].operations[2].name | k_proj |
| stages[17].operations[2].matrix_flops | 1073741824 |
| stages[17].operations[2].input_precision | BF16 |
| stages[17].operations[2].accumulator_precision | FP32 |
| stages[17].operations[2].sparsity | dense |
| stages[17].operations[2].scalar_flops | 0 |
| stages[17].operations[2].special_ops | {} |
| stages[17].operations[2].source_detail.input[0] | 128 |
| stages[17].operations[2].source_detail.input[1] | 4096 |
| stages[17].operations[2].source_detail.weight_math[0] | 4096 |
| stages[17].operations[2].source_detail.weight_math[1] | 1024 |
| stages[17].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[17].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[2].source_detail.output[0] | 128 |
| stages[17].operations[2].source_detail.output[1] | 1024 |
| stages[17].operations[3].name | v_proj |
| stages[17].operations[3].matrix_flops | 1073741824 |
| stages[17].operations[3].input_precision | BF16 |
| stages[17].operations[3].accumulator_precision | FP32 |
| stages[17].operations[3].sparsity | dense |
| stages[17].operations[3].scalar_flops | 0 |
| stages[17].operations[3].special_ops | {} |
| stages[17].operations[3].source_detail.input[0] | 128 |
| stages[17].operations[3].source_detail.input[1] | 4096 |
| stages[17].operations[3].source_detail.weight_math[0] | 4096 |
| stages[17].operations[3].source_detail.weight_math[1] | 1024 |
| stages[17].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[17].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[3].source_detail.output[0] | 128 |
| stages[17].operations[3].source_detail.output[1] | 1024 |
| stages[17].operations[4].name | q_norm |
| stages[17].operations[4].matrix_flops | 0 |
| stages[17].operations[4].input_precision | unknown (null) |
| stages[17].operations[4].accumulator_precision | unknown (null) |
| stages[17].operations[4].sparsity | unknown (null) |
| stages[17].operations[4].scalar_flops | 2101248 |
| stages[17].operations[4].special_ops.rsqrt | 4096 |
| stages[17].operations[4].source_detail.input[0] | 4096 |
| stages[17].operations[4].source_detail.input[1] | 128 |
| stages[17].operations[4].source_detail.weight[0] | 128 |
| stages[17].operations[4].source_detail.output[0] | 4096 |
| stages[17].operations[4].source_detail.output[1] | 128 |
| stages[17].operations[5].name | k_norm |
| stages[17].operations[5].matrix_flops | 0 |
| stages[17].operations[5].input_precision | unknown (null) |
| stages[17].operations[5].accumulator_precision | unknown (null) |
| stages[17].operations[5].sparsity | unknown (null) |
| stages[17].operations[5].scalar_flops | 525312 |
| stages[17].operations[5].special_ops.rsqrt | 1024 |
| stages[17].operations[5].source_detail.input[0] | 1024 |
| stages[17].operations[5].source_detail.input[1] | 128 |
| stages[17].operations[5].source_detail.weight[0] | 128 |
| stages[17].operations[5].source_detail.output[0] | 1024 |
| stages[17].operations[5].source_detail.output[1] | 128 |
| stages[17].operations[6].name | apply_rope |
| stages[17].operations[6].matrix_flops | 0 |
| stages[17].operations[6].input_precision | unknown (null) |
| stages[17].operations[6].accumulator_precision | unknown (null) |
| stages[17].operations[6].sparsity | unknown (null) |
| stages[17].operations[6].scalar_flops | 1966080 |
| stages[17].operations[6].special_ops.negate | 327680 |
| stages[17].operations[6].source_detail.Q[0] | 1 |
| stages[17].operations[6].source_detail.Q[1] | 32 |
| stages[17].operations[6].source_detail.Q[2] | 128 |
| stages[17].operations[6].source_detail.Q[3] | 128 |
| stages[17].operations[6].source_detail.K[0] | 1 |
| stages[17].operations[6].source_detail.K[1] | 8 |
| stages[17].operations[6].source_detail.K[2] | 128 |
| stages[17].operations[6].source_detail.K[3] | 128 |
| stages[17].operations[7].name | kv_append |
| stages[17].operations[7].matrix_flops | 0 |
| stages[17].operations[7].input_precision | unknown (null) |
| stages[17].operations[7].accumulator_precision | unknown (null) |
| stages[17].operations[7].sparsity | unknown (null) |
| stages[17].operations[7].scalar_flops | 0 |
| stages[17].operations[7].special_ops | {} |
| stages[17].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[17].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[17].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[17].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[17].operations[8].name | qk |
| stages[17].operations[8].matrix_flops | 67633152 |
| stages[17].operations[8].input_precision | BF16 |
| stages[17].operations[8].accumulator_precision | FP32 |
| stages[17].operations[8].sparsity | dense |
| stages[17].operations[8].scalar_flops | 0 |
| stages[17].operations[8].special_ops | {} |
| stages[17].operations[8].source_detail.Q[0] | 1 |
| stages[17].operations[8].source_detail.Q[1] | 32 |
| stages[17].operations[8].source_detail.Q[2] | 128 |
| stages[17].operations[8].source_detail.Q[3] | 128 |
| stages[17].operations[8].source_detail.K_shared[0] | 1 |
| stages[17].operations[8].source_detail.K_shared[1] | 8 |
| stages[17].operations[8].source_detail.K_shared[2] | 128 |
| stages[17].operations[8].source_detail.K_shared[3] | 128 |
| stages[17].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[17].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[17].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[17].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[17].operations[9].name | score_scale_mask_softmax |
| stages[17].operations[9].matrix_flops | 0 |
| stages[17].operations[9].input_precision | unknown (null) |
| stages[17].operations[9].accumulator_precision | unknown (null) |
| stages[17].operations[9].sparsity | unknown (null) |
| stages[17].operations[9].scalar_flops | 1052672 |
| stages[17].operations[9].special_ops.exp | 264192 |
| stages[17].operations[9].special_ops.compare_max | 260096 |
| stages[17].operations[9].special_ops.mask_decisions | 524288 |
| stages[17].operations[9].source_detail.scores[0] | 1 |
| stages[17].operations[9].source_detail.scores[1] | 32 |
| stages[17].operations[9].source_detail.scores[2] | 128 |
| stages[17].operations[9].source_detail.scores[3] | 128 |
| stages[17].operations[10].name | pv |
| stages[17].operations[10].matrix_flops | 67633152 |
| stages[17].operations[10].input_precision | BF16 |
| stages[17].operations[10].accumulator_precision | FP32 |
| stages[17].operations[10].sparsity | dense |
| stages[17].operations[10].scalar_flops | 0 |
| stages[17].operations[10].special_ops | {} |
| stages[17].operations[10].source_detail.P[0] | 1 |
| stages[17].operations[10].source_detail.P[1] | 32 |
| stages[17].operations[10].source_detail.P[2] | 128 |
| stages[17].operations[10].source_detail.P[3] | 128 |
| stages[17].operations[10].source_detail.V_shared[0] | 1 |
| stages[17].operations[10].source_detail.V_shared[1] | 8 |
| stages[17].operations[10].source_detail.V_shared[2] | 128 |
| stages[17].operations[10].source_detail.V_shared[3] | 128 |
| stages[17].operations[10].source_detail.output[0] | 1 |
| stages[17].operations[10].source_detail.output[1] | 32 |
| stages[17].operations[10].source_detail.output[2] | 128 |
| stages[17].operations[10].source_detail.output[3] | 128 |
| stages[17].operations[11].name | o_proj |
| stages[17].operations[11].matrix_flops | 4294967296 |
| stages[17].operations[11].input_precision | BF16 |
| stages[17].operations[11].accumulator_precision | FP32 |
| stages[17].operations[11].sparsity | dense |
| stages[17].operations[11].scalar_flops | 0 |
| stages[17].operations[11].special_ops | {} |
| stages[17].operations[11].source_detail.input[0] | 128 |
| stages[17].operations[11].source_detail.input[1] | 4096 |
| stages[17].operations[11].source_detail.weight_math[0] | 4096 |
| stages[17].operations[11].source_detail.weight_math[1] | 4096 |
| stages[17].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[17].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[11].source_detail.output[0] | 128 |
| stages[17].operations[11].source_detail.output[1] | 4096 |
| stages[17].operations[12].name | attention_residual |
| stages[17].operations[12].matrix_flops | 0 |
| stages[17].operations[12].input_precision | unknown (null) |
| stages[17].operations[12].accumulator_precision | unknown (null) |
| stages[17].operations[12].sparsity | unknown (null) |
| stages[17].operations[12].scalar_flops | 524288 |
| stages[17].operations[12].special_ops | {} |
| stages[17].operations[12].source_detail.inputs_each[0] | 128 |
| stages[17].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[17].operations[12].source_detail.output[0] | 128 |
| stages[17].operations[12].source_detail.output[1] | 4096 |
| stages[17].operations[13].name | post_attention_layernorm |
| stages[17].operations[13].matrix_flops | 0 |
| stages[17].operations[13].input_precision | unknown (null) |
| stages[17].operations[13].accumulator_precision | unknown (null) |
| stages[17].operations[13].sparsity | unknown (null) |
| stages[17].operations[13].scalar_flops | 2097280 |
| stages[17].operations[13].special_ops.rsqrt | 128 |
| stages[17].operations[13].source_detail.input[0] | 128 |
| stages[17].operations[13].source_detail.input[1] | 4096 |
| stages[17].operations[13].source_detail.weight[0] | 4096 |
| stages[17].operations[13].source_detail.output[0] | 128 |
| stages[17].operations[13].source_detail.output[1] | 4096 |
| stages[17].operations[14].name | gate_proj |
| stages[17].operations[14].matrix_flops | 12884901888 |
| stages[17].operations[14].input_precision | BF16 |
| stages[17].operations[14].accumulator_precision | FP32 |
| stages[17].operations[14].sparsity | dense |
| stages[17].operations[14].scalar_flops | 0 |
| stages[17].operations[14].special_ops | {} |
| stages[17].operations[14].source_detail.input[0] | 128 |
| stages[17].operations[14].source_detail.input[1] | 4096 |
| stages[17].operations[14].source_detail.weight_math[0] | 4096 |
| stages[17].operations[14].source_detail.weight_math[1] | 12288 |
| stages[17].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[17].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[14].source_detail.output[0] | 128 |
| stages[17].operations[14].source_detail.output[1] | 12288 |
| stages[17].operations[15].name | up_proj |
| stages[17].operations[15].matrix_flops | 12884901888 |
| stages[17].operations[15].input_precision | BF16 |
| stages[17].operations[15].accumulator_precision | FP32 |
| stages[17].operations[15].sparsity | dense |
| stages[17].operations[15].scalar_flops | 0 |
| stages[17].operations[15].special_ops | {} |
| stages[17].operations[15].source_detail.input[0] | 128 |
| stages[17].operations[15].source_detail.input[1] | 4096 |
| stages[17].operations[15].source_detail.weight_math[0] | 4096 |
| stages[17].operations[15].source_detail.weight_math[1] | 12288 |
| stages[17].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[17].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[17].operations[15].source_detail.output[0] | 128 |
| stages[17].operations[15].source_detail.output[1] | 12288 |
| stages[17].operations[16].name | silu_mul |
| stages[17].operations[16].matrix_flops | 0 |
| stages[17].operations[16].input_precision | unknown (null) |
| stages[17].operations[16].accumulator_precision | unknown (null) |
| stages[17].operations[16].sparsity | unknown (null) |
| stages[17].operations[16].scalar_flops | 6291456 |
| stages[17].operations[16].special_ops.exp | 1572864 |
| stages[17].operations[16].special_ops.negate | 1572864 |
| stages[17].operations[16].source_detail.gate[0] | 128 |
| stages[17].operations[16].source_detail.gate[1] | 12288 |
| stages[17].operations[16].source_detail.up[0] | 128 |
| stages[17].operations[16].source_detail.up[1] | 12288 |
| stages[17].operations[16].source_detail.output[0] | 128 |
| stages[17].operations[16].source_detail.output[1] | 12288 |
| stages[17].operations[17].name | down_proj |
| stages[17].operations[17].matrix_flops | 12884901888 |
| stages[17].operations[17].input_precision | BF16 |
| stages[17].operations[17].accumulator_precision | FP32 |
| stages[17].operations[17].sparsity | dense |
| stages[17].operations[17].scalar_flops | 0 |
| stages[17].operations[17].special_ops | {} |
| stages[17].operations[17].source_detail.input[0] | 128 |
| stages[17].operations[17].source_detail.input[1] | 12288 |
| stages[17].operations[17].source_detail.weight_math[0] | 12288 |
| stages[17].operations[17].source_detail.weight_math[1] | 4096 |
| stages[17].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[17].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[17].operations[17].source_detail.output[0] | 128 |
| stages[17].operations[17].source_detail.output[1] | 4096 |
| stages[17].operations[18].name | ffn_residual |
| stages[17].operations[18].matrix_flops | 0 |
| stages[17].operations[18].input_precision | unknown (null) |
| stages[17].operations[18].accumulator_precision | unknown (null) |
| stages[17].operations[18].sparsity | unknown (null) |
| stages[17].operations[18].scalar_flops | 524288 |
| stages[17].operations[18].special_ops | {} |
| stages[17].operations[18].source_detail.inputs_each[0] | 128 |
| stages[17].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[17].operations[18].source_detail.output[0] | 128 |
| stages[17].operations[18].source_detail.output[1] | 4096 |
| stages[18].id | layer:17 |
| stages[18].work.vector_fp32 | 17179904 |
| stages[18].work.special:rsqrt | 5376 |
| stages[18].work.interface_bytes | 438387200 |
| stages[18].work.matrix_bf16 | 49527390208 |
| stages[18].work.special:negate | 1900544 |
| stages[18].work.special:exp | 1837056 |
| stages[18].work.special:compare_max | 260096 |
| stages[18].work.special:mask_decisions | 524288 |
| stages[18].operations[0].name | input_layernorm |
| stages[18].operations[0].matrix_flops | 0 |
| stages[18].operations[0].input_precision | unknown (null) |
| stages[18].operations[0].accumulator_precision | unknown (null) |
| stages[18].operations[0].sparsity | unknown (null) |
| stages[18].operations[0].scalar_flops | 2097280 |
| stages[18].operations[0].special_ops.rsqrt | 128 |
| stages[18].operations[0].source_detail.input[0] | 128 |
| stages[18].operations[0].source_detail.input[1] | 4096 |
| stages[18].operations[0].source_detail.weight[0] | 4096 |
| stages[18].operations[0].source_detail.output[0] | 128 |
| stages[18].operations[0].source_detail.output[1] | 4096 |
| stages[18].operations[1].name | q_proj |
| stages[18].operations[1].matrix_flops | 4294967296 |
| stages[18].operations[1].input_precision | BF16 |
| stages[18].operations[1].accumulator_precision | FP32 |
| stages[18].operations[1].sparsity | dense |
| stages[18].operations[1].scalar_flops | 0 |
| stages[18].operations[1].special_ops | {} |
| stages[18].operations[1].source_detail.input[0] | 128 |
| stages[18].operations[1].source_detail.input[1] | 4096 |
| stages[18].operations[1].source_detail.weight_math[0] | 4096 |
| stages[18].operations[1].source_detail.weight_math[1] | 4096 |
| stages[18].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[18].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[1].source_detail.output[0] | 128 |
| stages[18].operations[1].source_detail.output[1] | 4096 |
| stages[18].operations[2].name | k_proj |
| stages[18].operations[2].matrix_flops | 1073741824 |
| stages[18].operations[2].input_precision | BF16 |
| stages[18].operations[2].accumulator_precision | FP32 |
| stages[18].operations[2].sparsity | dense |
| stages[18].operations[2].scalar_flops | 0 |
| stages[18].operations[2].special_ops | {} |
| stages[18].operations[2].source_detail.input[0] | 128 |
| stages[18].operations[2].source_detail.input[1] | 4096 |
| stages[18].operations[2].source_detail.weight_math[0] | 4096 |
| stages[18].operations[2].source_detail.weight_math[1] | 1024 |
| stages[18].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[18].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[2].source_detail.output[0] | 128 |
| stages[18].operations[2].source_detail.output[1] | 1024 |
| stages[18].operations[3].name | v_proj |
| stages[18].operations[3].matrix_flops | 1073741824 |
| stages[18].operations[3].input_precision | BF16 |
| stages[18].operations[3].accumulator_precision | FP32 |
| stages[18].operations[3].sparsity | dense |
| stages[18].operations[3].scalar_flops | 0 |
| stages[18].operations[3].special_ops | {} |
| stages[18].operations[3].source_detail.input[0] | 128 |
| stages[18].operations[3].source_detail.input[1] | 4096 |
| stages[18].operations[3].source_detail.weight_math[0] | 4096 |
| stages[18].operations[3].source_detail.weight_math[1] | 1024 |
| stages[18].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[18].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[3].source_detail.output[0] | 128 |
| stages[18].operations[3].source_detail.output[1] | 1024 |
| stages[18].operations[4].name | q_norm |
| stages[18].operations[4].matrix_flops | 0 |
| stages[18].operations[4].input_precision | unknown (null) |
| stages[18].operations[4].accumulator_precision | unknown (null) |
| stages[18].operations[4].sparsity | unknown (null) |
| stages[18].operations[4].scalar_flops | 2101248 |
| stages[18].operations[4].special_ops.rsqrt | 4096 |
| stages[18].operations[4].source_detail.input[0] | 4096 |
| stages[18].operations[4].source_detail.input[1] | 128 |
| stages[18].operations[4].source_detail.weight[0] | 128 |
| stages[18].operations[4].source_detail.output[0] | 4096 |
| stages[18].operations[4].source_detail.output[1] | 128 |
| stages[18].operations[5].name | k_norm |
| stages[18].operations[5].matrix_flops | 0 |
| stages[18].operations[5].input_precision | unknown (null) |
| stages[18].operations[5].accumulator_precision | unknown (null) |
| stages[18].operations[5].sparsity | unknown (null) |
| stages[18].operations[5].scalar_flops | 525312 |
| stages[18].operations[5].special_ops.rsqrt | 1024 |
| stages[18].operations[5].source_detail.input[0] | 1024 |
| stages[18].operations[5].source_detail.input[1] | 128 |
| stages[18].operations[5].source_detail.weight[0] | 128 |
| stages[18].operations[5].source_detail.output[0] | 1024 |
| stages[18].operations[5].source_detail.output[1] | 128 |
| stages[18].operations[6].name | apply_rope |
| stages[18].operations[6].matrix_flops | 0 |
| stages[18].operations[6].input_precision | unknown (null) |
| stages[18].operations[6].accumulator_precision | unknown (null) |
| stages[18].operations[6].sparsity | unknown (null) |
| stages[18].operations[6].scalar_flops | 1966080 |
| stages[18].operations[6].special_ops.negate | 327680 |
| stages[18].operations[6].source_detail.Q[0] | 1 |
| stages[18].operations[6].source_detail.Q[1] | 32 |
| stages[18].operations[6].source_detail.Q[2] | 128 |
| stages[18].operations[6].source_detail.Q[3] | 128 |
| stages[18].operations[6].source_detail.K[0] | 1 |
| stages[18].operations[6].source_detail.K[1] | 8 |
| stages[18].operations[6].source_detail.K[2] | 128 |
| stages[18].operations[6].source_detail.K[3] | 128 |
| stages[18].operations[7].name | kv_append |
| stages[18].operations[7].matrix_flops | 0 |
| stages[18].operations[7].input_precision | unknown (null) |
| stages[18].operations[7].accumulator_precision | unknown (null) |
| stages[18].operations[7].sparsity | unknown (null) |
| stages[18].operations[7].scalar_flops | 0 |
| stages[18].operations[7].special_ops | {} |
| stages[18].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[18].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[18].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[18].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[18].operations[8].name | qk |
| stages[18].operations[8].matrix_flops | 67633152 |
| stages[18].operations[8].input_precision | BF16 |
| stages[18].operations[8].accumulator_precision | FP32 |
| stages[18].operations[8].sparsity | dense |
| stages[18].operations[8].scalar_flops | 0 |
| stages[18].operations[8].special_ops | {} |
| stages[18].operations[8].source_detail.Q[0] | 1 |
| stages[18].operations[8].source_detail.Q[1] | 32 |
| stages[18].operations[8].source_detail.Q[2] | 128 |
| stages[18].operations[8].source_detail.Q[3] | 128 |
| stages[18].operations[8].source_detail.K_shared[0] | 1 |
| stages[18].operations[8].source_detail.K_shared[1] | 8 |
| stages[18].operations[8].source_detail.K_shared[2] | 128 |
| stages[18].operations[8].source_detail.K_shared[3] | 128 |
| stages[18].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[18].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[18].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[18].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[18].operations[9].name | score_scale_mask_softmax |
| stages[18].operations[9].matrix_flops | 0 |
| stages[18].operations[9].input_precision | unknown (null) |
| stages[18].operations[9].accumulator_precision | unknown (null) |
| stages[18].operations[9].sparsity | unknown (null) |
| stages[18].operations[9].scalar_flops | 1052672 |
| stages[18].operations[9].special_ops.exp | 264192 |
| stages[18].operations[9].special_ops.compare_max | 260096 |
| stages[18].operations[9].special_ops.mask_decisions | 524288 |
| stages[18].operations[9].source_detail.scores[0] | 1 |
| stages[18].operations[9].source_detail.scores[1] | 32 |
| stages[18].operations[9].source_detail.scores[2] | 128 |
| stages[18].operations[9].source_detail.scores[3] | 128 |
| stages[18].operations[10].name | pv |
| stages[18].operations[10].matrix_flops | 67633152 |
| stages[18].operations[10].input_precision | BF16 |
| stages[18].operations[10].accumulator_precision | FP32 |
| stages[18].operations[10].sparsity | dense |
| stages[18].operations[10].scalar_flops | 0 |
| stages[18].operations[10].special_ops | {} |
| stages[18].operations[10].source_detail.P[0] | 1 |
| stages[18].operations[10].source_detail.P[1] | 32 |
| stages[18].operations[10].source_detail.P[2] | 128 |
| stages[18].operations[10].source_detail.P[3] | 128 |
| stages[18].operations[10].source_detail.V_shared[0] | 1 |
| stages[18].operations[10].source_detail.V_shared[1] | 8 |
| stages[18].operations[10].source_detail.V_shared[2] | 128 |
| stages[18].operations[10].source_detail.V_shared[3] | 128 |
| stages[18].operations[10].source_detail.output[0] | 1 |
| stages[18].operations[10].source_detail.output[1] | 32 |
| stages[18].operations[10].source_detail.output[2] | 128 |
| stages[18].operations[10].source_detail.output[3] | 128 |
| stages[18].operations[11].name | o_proj |
| stages[18].operations[11].matrix_flops | 4294967296 |
| stages[18].operations[11].input_precision | BF16 |
| stages[18].operations[11].accumulator_precision | FP32 |
| stages[18].operations[11].sparsity | dense |
| stages[18].operations[11].scalar_flops | 0 |
| stages[18].operations[11].special_ops | {} |
| stages[18].operations[11].source_detail.input[0] | 128 |
| stages[18].operations[11].source_detail.input[1] | 4096 |
| stages[18].operations[11].source_detail.weight_math[0] | 4096 |
| stages[18].operations[11].source_detail.weight_math[1] | 4096 |
| stages[18].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[18].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[11].source_detail.output[0] | 128 |
| stages[18].operations[11].source_detail.output[1] | 4096 |
| stages[18].operations[12].name | attention_residual |
| stages[18].operations[12].matrix_flops | 0 |
| stages[18].operations[12].input_precision | unknown (null) |
| stages[18].operations[12].accumulator_precision | unknown (null) |
| stages[18].operations[12].sparsity | unknown (null) |
| stages[18].operations[12].scalar_flops | 524288 |
| stages[18].operations[12].special_ops | {} |
| stages[18].operations[12].source_detail.inputs_each[0] | 128 |
| stages[18].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[18].operations[12].source_detail.output[0] | 128 |
| stages[18].operations[12].source_detail.output[1] | 4096 |
| stages[18].operations[13].name | post_attention_layernorm |
| stages[18].operations[13].matrix_flops | 0 |
| stages[18].operations[13].input_precision | unknown (null) |
| stages[18].operations[13].accumulator_precision | unknown (null) |
| stages[18].operations[13].sparsity | unknown (null) |
| stages[18].operations[13].scalar_flops | 2097280 |
| stages[18].operations[13].special_ops.rsqrt | 128 |
| stages[18].operations[13].source_detail.input[0] | 128 |
| stages[18].operations[13].source_detail.input[1] | 4096 |
| stages[18].operations[13].source_detail.weight[0] | 4096 |
| stages[18].operations[13].source_detail.output[0] | 128 |
| stages[18].operations[13].source_detail.output[1] | 4096 |
| stages[18].operations[14].name | gate_proj |
| stages[18].operations[14].matrix_flops | 12884901888 |
| stages[18].operations[14].input_precision | BF16 |
| stages[18].operations[14].accumulator_precision | FP32 |
| stages[18].operations[14].sparsity | dense |
| stages[18].operations[14].scalar_flops | 0 |
| stages[18].operations[14].special_ops | {} |
| stages[18].operations[14].source_detail.input[0] | 128 |
| stages[18].operations[14].source_detail.input[1] | 4096 |
| stages[18].operations[14].source_detail.weight_math[0] | 4096 |
| stages[18].operations[14].source_detail.weight_math[1] | 12288 |
| stages[18].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[18].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[14].source_detail.output[0] | 128 |
| stages[18].operations[14].source_detail.output[1] | 12288 |
| stages[18].operations[15].name | up_proj |
| stages[18].operations[15].matrix_flops | 12884901888 |
| stages[18].operations[15].input_precision | BF16 |
| stages[18].operations[15].accumulator_precision | FP32 |
| stages[18].operations[15].sparsity | dense |
| stages[18].operations[15].scalar_flops | 0 |
| stages[18].operations[15].special_ops | {} |
| stages[18].operations[15].source_detail.input[0] | 128 |
| stages[18].operations[15].source_detail.input[1] | 4096 |
| stages[18].operations[15].source_detail.weight_math[0] | 4096 |
| stages[18].operations[15].source_detail.weight_math[1] | 12288 |
| stages[18].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[18].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[18].operations[15].source_detail.output[0] | 128 |
| stages[18].operations[15].source_detail.output[1] | 12288 |
| stages[18].operations[16].name | silu_mul |
| stages[18].operations[16].matrix_flops | 0 |
| stages[18].operations[16].input_precision | unknown (null) |
| stages[18].operations[16].accumulator_precision | unknown (null) |
| stages[18].operations[16].sparsity | unknown (null) |
| stages[18].operations[16].scalar_flops | 6291456 |
| stages[18].operations[16].special_ops.exp | 1572864 |
| stages[18].operations[16].special_ops.negate | 1572864 |
| stages[18].operations[16].source_detail.gate[0] | 128 |
| stages[18].operations[16].source_detail.gate[1] | 12288 |
| stages[18].operations[16].source_detail.up[0] | 128 |
| stages[18].operations[16].source_detail.up[1] | 12288 |
| stages[18].operations[16].source_detail.output[0] | 128 |
| stages[18].operations[16].source_detail.output[1] | 12288 |
| stages[18].operations[17].name | down_proj |
| stages[18].operations[17].matrix_flops | 12884901888 |
| stages[18].operations[17].input_precision | BF16 |
| stages[18].operations[17].accumulator_precision | FP32 |
| stages[18].operations[17].sparsity | dense |
| stages[18].operations[17].scalar_flops | 0 |
| stages[18].operations[17].special_ops | {} |
| stages[18].operations[17].source_detail.input[0] | 128 |
| stages[18].operations[17].source_detail.input[1] | 12288 |
| stages[18].operations[17].source_detail.weight_math[0] | 12288 |
| stages[18].operations[17].source_detail.weight_math[1] | 4096 |
| stages[18].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[18].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[18].operations[17].source_detail.output[0] | 128 |
| stages[18].operations[17].source_detail.output[1] | 4096 |
| stages[18].operations[18].name | ffn_residual |
| stages[18].operations[18].matrix_flops | 0 |
| stages[18].operations[18].input_precision | unknown (null) |
| stages[18].operations[18].accumulator_precision | unknown (null) |
| stages[18].operations[18].sparsity | unknown (null) |
| stages[18].operations[18].scalar_flops | 524288 |
| stages[18].operations[18].special_ops | {} |
| stages[18].operations[18].source_detail.inputs_each[0] | 128 |
| stages[18].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[18].operations[18].source_detail.output[0] | 128 |
| stages[18].operations[18].source_detail.output[1] | 4096 |
| stages[19].id | layer:18 |
| stages[19].work.vector_fp32 | 17179904 |
| stages[19].work.special:rsqrt | 5376 |
| stages[19].work.interface_bytes | 438387200 |
| stages[19].work.matrix_bf16 | 49527390208 |
| stages[19].work.special:negate | 1900544 |
| stages[19].work.special:exp | 1837056 |
| stages[19].work.special:compare_max | 260096 |
| stages[19].work.special:mask_decisions | 524288 |
| stages[19].operations[0].name | input_layernorm |
| stages[19].operations[0].matrix_flops | 0 |
| stages[19].operations[0].input_precision | unknown (null) |
| stages[19].operations[0].accumulator_precision | unknown (null) |
| stages[19].operations[0].sparsity | unknown (null) |
| stages[19].operations[0].scalar_flops | 2097280 |
| stages[19].operations[0].special_ops.rsqrt | 128 |
| stages[19].operations[0].source_detail.input[0] | 128 |
| stages[19].operations[0].source_detail.input[1] | 4096 |
| stages[19].operations[0].source_detail.weight[0] | 4096 |
| stages[19].operations[0].source_detail.output[0] | 128 |
| stages[19].operations[0].source_detail.output[1] | 4096 |
| stages[19].operations[1].name | q_proj |
| stages[19].operations[1].matrix_flops | 4294967296 |
| stages[19].operations[1].input_precision | BF16 |
| stages[19].operations[1].accumulator_precision | FP32 |
| stages[19].operations[1].sparsity | dense |
| stages[19].operations[1].scalar_flops | 0 |
| stages[19].operations[1].special_ops | {} |
| stages[19].operations[1].source_detail.input[0] | 128 |
| stages[19].operations[1].source_detail.input[1] | 4096 |
| stages[19].operations[1].source_detail.weight_math[0] | 4096 |
| stages[19].operations[1].source_detail.weight_math[1] | 4096 |
| stages[19].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[19].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[1].source_detail.output[0] | 128 |
| stages[19].operations[1].source_detail.output[1] | 4096 |
| stages[19].operations[2].name | k_proj |
| stages[19].operations[2].matrix_flops | 1073741824 |
| stages[19].operations[2].input_precision | BF16 |
| stages[19].operations[2].accumulator_precision | FP32 |
| stages[19].operations[2].sparsity | dense |
| stages[19].operations[2].scalar_flops | 0 |
| stages[19].operations[2].special_ops | {} |
| stages[19].operations[2].source_detail.input[0] | 128 |
| stages[19].operations[2].source_detail.input[1] | 4096 |
| stages[19].operations[2].source_detail.weight_math[0] | 4096 |
| stages[19].operations[2].source_detail.weight_math[1] | 1024 |
| stages[19].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[19].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[2].source_detail.output[0] | 128 |
| stages[19].operations[2].source_detail.output[1] | 1024 |
| stages[19].operations[3].name | v_proj |
| stages[19].operations[3].matrix_flops | 1073741824 |
| stages[19].operations[3].input_precision | BF16 |
| stages[19].operations[3].accumulator_precision | FP32 |
| stages[19].operations[3].sparsity | dense |
| stages[19].operations[3].scalar_flops | 0 |
| stages[19].operations[3].special_ops | {} |
| stages[19].operations[3].source_detail.input[0] | 128 |
| stages[19].operations[3].source_detail.input[1] | 4096 |
| stages[19].operations[3].source_detail.weight_math[0] | 4096 |
| stages[19].operations[3].source_detail.weight_math[1] | 1024 |
| stages[19].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[19].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[3].source_detail.output[0] | 128 |
| stages[19].operations[3].source_detail.output[1] | 1024 |
| stages[19].operations[4].name | q_norm |
| stages[19].operations[4].matrix_flops | 0 |
| stages[19].operations[4].input_precision | unknown (null) |
| stages[19].operations[4].accumulator_precision | unknown (null) |
| stages[19].operations[4].sparsity | unknown (null) |
| stages[19].operations[4].scalar_flops | 2101248 |
| stages[19].operations[4].special_ops.rsqrt | 4096 |
| stages[19].operations[4].source_detail.input[0] | 4096 |
| stages[19].operations[4].source_detail.input[1] | 128 |
| stages[19].operations[4].source_detail.weight[0] | 128 |
| stages[19].operations[4].source_detail.output[0] | 4096 |
| stages[19].operations[4].source_detail.output[1] | 128 |
| stages[19].operations[5].name | k_norm |
| stages[19].operations[5].matrix_flops | 0 |
| stages[19].operations[5].input_precision | unknown (null) |
| stages[19].operations[5].accumulator_precision | unknown (null) |
| stages[19].operations[5].sparsity | unknown (null) |
| stages[19].operations[5].scalar_flops | 525312 |
| stages[19].operations[5].special_ops.rsqrt | 1024 |
| stages[19].operations[5].source_detail.input[0] | 1024 |
| stages[19].operations[5].source_detail.input[1] | 128 |
| stages[19].operations[5].source_detail.weight[0] | 128 |
| stages[19].operations[5].source_detail.output[0] | 1024 |
| stages[19].operations[5].source_detail.output[1] | 128 |
| stages[19].operations[6].name | apply_rope |
| stages[19].operations[6].matrix_flops | 0 |
| stages[19].operations[6].input_precision | unknown (null) |
| stages[19].operations[6].accumulator_precision | unknown (null) |
| stages[19].operations[6].sparsity | unknown (null) |
| stages[19].operations[6].scalar_flops | 1966080 |
| stages[19].operations[6].special_ops.negate | 327680 |
| stages[19].operations[6].source_detail.Q[0] | 1 |
| stages[19].operations[6].source_detail.Q[1] | 32 |
| stages[19].operations[6].source_detail.Q[2] | 128 |
| stages[19].operations[6].source_detail.Q[3] | 128 |
| stages[19].operations[6].source_detail.K[0] | 1 |
| stages[19].operations[6].source_detail.K[1] | 8 |
| stages[19].operations[6].source_detail.K[2] | 128 |
| stages[19].operations[6].source_detail.K[3] | 128 |
| stages[19].operations[7].name | kv_append |
| stages[19].operations[7].matrix_flops | 0 |
| stages[19].operations[7].input_precision | unknown (null) |
| stages[19].operations[7].accumulator_precision | unknown (null) |
| stages[19].operations[7].sparsity | unknown (null) |
| stages[19].operations[7].scalar_flops | 0 |
| stages[19].operations[7].special_ops | {} |
| stages[19].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[19].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[19].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[19].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[19].operations[8].name | qk |
| stages[19].operations[8].matrix_flops | 67633152 |
| stages[19].operations[8].input_precision | BF16 |
| stages[19].operations[8].accumulator_precision | FP32 |
| stages[19].operations[8].sparsity | dense |
| stages[19].operations[8].scalar_flops | 0 |
| stages[19].operations[8].special_ops | {} |
| stages[19].operations[8].source_detail.Q[0] | 1 |
| stages[19].operations[8].source_detail.Q[1] | 32 |
| stages[19].operations[8].source_detail.Q[2] | 128 |
| stages[19].operations[8].source_detail.Q[3] | 128 |
| stages[19].operations[8].source_detail.K_shared[0] | 1 |
| stages[19].operations[8].source_detail.K_shared[1] | 8 |
| stages[19].operations[8].source_detail.K_shared[2] | 128 |
| stages[19].operations[8].source_detail.K_shared[3] | 128 |
| stages[19].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[19].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[19].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[19].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[19].operations[9].name | score_scale_mask_softmax |
| stages[19].operations[9].matrix_flops | 0 |
| stages[19].operations[9].input_precision | unknown (null) |
| stages[19].operations[9].accumulator_precision | unknown (null) |
| stages[19].operations[9].sparsity | unknown (null) |
| stages[19].operations[9].scalar_flops | 1052672 |
| stages[19].operations[9].special_ops.exp | 264192 |
| stages[19].operations[9].special_ops.compare_max | 260096 |
| stages[19].operations[9].special_ops.mask_decisions | 524288 |
| stages[19].operations[9].source_detail.scores[0] | 1 |
| stages[19].operations[9].source_detail.scores[1] | 32 |
| stages[19].operations[9].source_detail.scores[2] | 128 |
| stages[19].operations[9].source_detail.scores[3] | 128 |
| stages[19].operations[10].name | pv |
| stages[19].operations[10].matrix_flops | 67633152 |
| stages[19].operations[10].input_precision | BF16 |
| stages[19].operations[10].accumulator_precision | FP32 |
| stages[19].operations[10].sparsity | dense |
| stages[19].operations[10].scalar_flops | 0 |
| stages[19].operations[10].special_ops | {} |
| stages[19].operations[10].source_detail.P[0] | 1 |
| stages[19].operations[10].source_detail.P[1] | 32 |
| stages[19].operations[10].source_detail.P[2] | 128 |
| stages[19].operations[10].source_detail.P[3] | 128 |
| stages[19].operations[10].source_detail.V_shared[0] | 1 |
| stages[19].operations[10].source_detail.V_shared[1] | 8 |
| stages[19].operations[10].source_detail.V_shared[2] | 128 |
| stages[19].operations[10].source_detail.V_shared[3] | 128 |
| stages[19].operations[10].source_detail.output[0] | 1 |
| stages[19].operations[10].source_detail.output[1] | 32 |
| stages[19].operations[10].source_detail.output[2] | 128 |
| stages[19].operations[10].source_detail.output[3] | 128 |
| stages[19].operations[11].name | o_proj |
| stages[19].operations[11].matrix_flops | 4294967296 |
| stages[19].operations[11].input_precision | BF16 |
| stages[19].operations[11].accumulator_precision | FP32 |
| stages[19].operations[11].sparsity | dense |
| stages[19].operations[11].scalar_flops | 0 |
| stages[19].operations[11].special_ops | {} |
| stages[19].operations[11].source_detail.input[0] | 128 |
| stages[19].operations[11].source_detail.input[1] | 4096 |
| stages[19].operations[11].source_detail.weight_math[0] | 4096 |
| stages[19].operations[11].source_detail.weight_math[1] | 4096 |
| stages[19].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[19].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[11].source_detail.output[0] | 128 |
| stages[19].operations[11].source_detail.output[1] | 4096 |
| stages[19].operations[12].name | attention_residual |
| stages[19].operations[12].matrix_flops | 0 |
| stages[19].operations[12].input_precision | unknown (null) |
| stages[19].operations[12].accumulator_precision | unknown (null) |
| stages[19].operations[12].sparsity | unknown (null) |
| stages[19].operations[12].scalar_flops | 524288 |
| stages[19].operations[12].special_ops | {} |
| stages[19].operations[12].source_detail.inputs_each[0] | 128 |
| stages[19].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[19].operations[12].source_detail.output[0] | 128 |
| stages[19].operations[12].source_detail.output[1] | 4096 |
| stages[19].operations[13].name | post_attention_layernorm |
| stages[19].operations[13].matrix_flops | 0 |
| stages[19].operations[13].input_precision | unknown (null) |
| stages[19].operations[13].accumulator_precision | unknown (null) |
| stages[19].operations[13].sparsity | unknown (null) |
| stages[19].operations[13].scalar_flops | 2097280 |
| stages[19].operations[13].special_ops.rsqrt | 128 |
| stages[19].operations[13].source_detail.input[0] | 128 |
| stages[19].operations[13].source_detail.input[1] | 4096 |
| stages[19].operations[13].source_detail.weight[0] | 4096 |
| stages[19].operations[13].source_detail.output[0] | 128 |
| stages[19].operations[13].source_detail.output[1] | 4096 |
| stages[19].operations[14].name | gate_proj |
| stages[19].operations[14].matrix_flops | 12884901888 |
| stages[19].operations[14].input_precision | BF16 |
| stages[19].operations[14].accumulator_precision | FP32 |
| stages[19].operations[14].sparsity | dense |
| stages[19].operations[14].scalar_flops | 0 |
| stages[19].operations[14].special_ops | {} |
| stages[19].operations[14].source_detail.input[0] | 128 |
| stages[19].operations[14].source_detail.input[1] | 4096 |
| stages[19].operations[14].source_detail.weight_math[0] | 4096 |
| stages[19].operations[14].source_detail.weight_math[1] | 12288 |
| stages[19].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[19].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[14].source_detail.output[0] | 128 |
| stages[19].operations[14].source_detail.output[1] | 12288 |
| stages[19].operations[15].name | up_proj |
| stages[19].operations[15].matrix_flops | 12884901888 |
| stages[19].operations[15].input_precision | BF16 |
| stages[19].operations[15].accumulator_precision | FP32 |
| stages[19].operations[15].sparsity | dense |
| stages[19].operations[15].scalar_flops | 0 |
| stages[19].operations[15].special_ops | {} |
| stages[19].operations[15].source_detail.input[0] | 128 |
| stages[19].operations[15].source_detail.input[1] | 4096 |
| stages[19].operations[15].source_detail.weight_math[0] | 4096 |
| stages[19].operations[15].source_detail.weight_math[1] | 12288 |
| stages[19].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[19].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[19].operations[15].source_detail.output[0] | 128 |
| stages[19].operations[15].source_detail.output[1] | 12288 |
| stages[19].operations[16].name | silu_mul |
| stages[19].operations[16].matrix_flops | 0 |
| stages[19].operations[16].input_precision | unknown (null) |
| stages[19].operations[16].accumulator_precision | unknown (null) |
| stages[19].operations[16].sparsity | unknown (null) |
| stages[19].operations[16].scalar_flops | 6291456 |
| stages[19].operations[16].special_ops.exp | 1572864 |
| stages[19].operations[16].special_ops.negate | 1572864 |
| stages[19].operations[16].source_detail.gate[0] | 128 |
| stages[19].operations[16].source_detail.gate[1] | 12288 |
| stages[19].operations[16].source_detail.up[0] | 128 |
| stages[19].operations[16].source_detail.up[1] | 12288 |
| stages[19].operations[16].source_detail.output[0] | 128 |
| stages[19].operations[16].source_detail.output[1] | 12288 |
| stages[19].operations[17].name | down_proj |
| stages[19].operations[17].matrix_flops | 12884901888 |
| stages[19].operations[17].input_precision | BF16 |
| stages[19].operations[17].accumulator_precision | FP32 |
| stages[19].operations[17].sparsity | dense |
| stages[19].operations[17].scalar_flops | 0 |
| stages[19].operations[17].special_ops | {} |
| stages[19].operations[17].source_detail.input[0] | 128 |
| stages[19].operations[17].source_detail.input[1] | 12288 |
| stages[19].operations[17].source_detail.weight_math[0] | 12288 |
| stages[19].operations[17].source_detail.weight_math[1] | 4096 |
| stages[19].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[19].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[19].operations[17].source_detail.output[0] | 128 |
| stages[19].operations[17].source_detail.output[1] | 4096 |
| stages[19].operations[18].name | ffn_residual |
| stages[19].operations[18].matrix_flops | 0 |
| stages[19].operations[18].input_precision | unknown (null) |
| stages[19].operations[18].accumulator_precision | unknown (null) |
| stages[19].operations[18].sparsity | unknown (null) |
| stages[19].operations[18].scalar_flops | 524288 |
| stages[19].operations[18].special_ops | {} |
| stages[19].operations[18].source_detail.inputs_each[0] | 128 |
| stages[19].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[19].operations[18].source_detail.output[0] | 128 |
| stages[19].operations[18].source_detail.output[1] | 4096 |
| stages[20].id | layer:19 |
| stages[20].work.vector_fp32 | 17179904 |
| stages[20].work.special:rsqrt | 5376 |
| stages[20].work.interface_bytes | 438387200 |
| stages[20].work.matrix_bf16 | 49527390208 |
| stages[20].work.special:negate | 1900544 |
| stages[20].work.special:exp | 1837056 |
| stages[20].work.special:compare_max | 260096 |
| stages[20].work.special:mask_decisions | 524288 |
| stages[20].operations[0].name | input_layernorm |
| stages[20].operations[0].matrix_flops | 0 |
| stages[20].operations[0].input_precision | unknown (null) |
| stages[20].operations[0].accumulator_precision | unknown (null) |
| stages[20].operations[0].sparsity | unknown (null) |
| stages[20].operations[0].scalar_flops | 2097280 |
| stages[20].operations[0].special_ops.rsqrt | 128 |
| stages[20].operations[0].source_detail.input[0] | 128 |
| stages[20].operations[0].source_detail.input[1] | 4096 |
| stages[20].operations[0].source_detail.weight[0] | 4096 |
| stages[20].operations[0].source_detail.output[0] | 128 |
| stages[20].operations[0].source_detail.output[1] | 4096 |
| stages[20].operations[1].name | q_proj |
| stages[20].operations[1].matrix_flops | 4294967296 |
| stages[20].operations[1].input_precision | BF16 |
| stages[20].operations[1].accumulator_precision | FP32 |
| stages[20].operations[1].sparsity | dense |
| stages[20].operations[1].scalar_flops | 0 |
| stages[20].operations[1].special_ops | {} |
| stages[20].operations[1].source_detail.input[0] | 128 |
| stages[20].operations[1].source_detail.input[1] | 4096 |
| stages[20].operations[1].source_detail.weight_math[0] | 4096 |
| stages[20].operations[1].source_detail.weight_math[1] | 4096 |
| stages[20].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[20].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[1].source_detail.output[0] | 128 |
| stages[20].operations[1].source_detail.output[1] | 4096 |
| stages[20].operations[2].name | k_proj |
| stages[20].operations[2].matrix_flops | 1073741824 |
| stages[20].operations[2].input_precision | BF16 |
| stages[20].operations[2].accumulator_precision | FP32 |
| stages[20].operations[2].sparsity | dense |
| stages[20].operations[2].scalar_flops | 0 |
| stages[20].operations[2].special_ops | {} |
| stages[20].operations[2].source_detail.input[0] | 128 |
| stages[20].operations[2].source_detail.input[1] | 4096 |
| stages[20].operations[2].source_detail.weight_math[0] | 4096 |
| stages[20].operations[2].source_detail.weight_math[1] | 1024 |
| stages[20].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[20].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[2].source_detail.output[0] | 128 |
| stages[20].operations[2].source_detail.output[1] | 1024 |
| stages[20].operations[3].name | v_proj |
| stages[20].operations[3].matrix_flops | 1073741824 |
| stages[20].operations[3].input_precision | BF16 |
| stages[20].operations[3].accumulator_precision | FP32 |
| stages[20].operations[3].sparsity | dense |
| stages[20].operations[3].scalar_flops | 0 |
| stages[20].operations[3].special_ops | {} |
| stages[20].operations[3].source_detail.input[0] | 128 |
| stages[20].operations[3].source_detail.input[1] | 4096 |
| stages[20].operations[3].source_detail.weight_math[0] | 4096 |
| stages[20].operations[3].source_detail.weight_math[1] | 1024 |
| stages[20].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[20].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[3].source_detail.output[0] | 128 |
| stages[20].operations[3].source_detail.output[1] | 1024 |
| stages[20].operations[4].name | q_norm |
| stages[20].operations[4].matrix_flops | 0 |
| stages[20].operations[4].input_precision | unknown (null) |
| stages[20].operations[4].accumulator_precision | unknown (null) |
| stages[20].operations[4].sparsity | unknown (null) |
| stages[20].operations[4].scalar_flops | 2101248 |
| stages[20].operations[4].special_ops.rsqrt | 4096 |
| stages[20].operations[4].source_detail.input[0] | 4096 |
| stages[20].operations[4].source_detail.input[1] | 128 |
| stages[20].operations[4].source_detail.weight[0] | 128 |
| stages[20].operations[4].source_detail.output[0] | 4096 |
| stages[20].operations[4].source_detail.output[1] | 128 |
| stages[20].operations[5].name | k_norm |
| stages[20].operations[5].matrix_flops | 0 |
| stages[20].operations[5].input_precision | unknown (null) |
| stages[20].operations[5].accumulator_precision | unknown (null) |
| stages[20].operations[5].sparsity | unknown (null) |
| stages[20].operations[5].scalar_flops | 525312 |
| stages[20].operations[5].special_ops.rsqrt | 1024 |
| stages[20].operations[5].source_detail.input[0] | 1024 |
| stages[20].operations[5].source_detail.input[1] | 128 |
| stages[20].operations[5].source_detail.weight[0] | 128 |
| stages[20].operations[5].source_detail.output[0] | 1024 |
| stages[20].operations[5].source_detail.output[1] | 128 |
| stages[20].operations[6].name | apply_rope |
| stages[20].operations[6].matrix_flops | 0 |
| stages[20].operations[6].input_precision | unknown (null) |
| stages[20].operations[6].accumulator_precision | unknown (null) |
| stages[20].operations[6].sparsity | unknown (null) |
| stages[20].operations[6].scalar_flops | 1966080 |
| stages[20].operations[6].special_ops.negate | 327680 |
| stages[20].operations[6].source_detail.Q[0] | 1 |
| stages[20].operations[6].source_detail.Q[1] | 32 |
| stages[20].operations[6].source_detail.Q[2] | 128 |
| stages[20].operations[6].source_detail.Q[3] | 128 |
| stages[20].operations[6].source_detail.K[0] | 1 |
| stages[20].operations[6].source_detail.K[1] | 8 |
| stages[20].operations[6].source_detail.K[2] | 128 |
| stages[20].operations[6].source_detail.K[3] | 128 |
| stages[20].operations[7].name | kv_append |
| stages[20].operations[7].matrix_flops | 0 |
| stages[20].operations[7].input_precision | unknown (null) |
| stages[20].operations[7].accumulator_precision | unknown (null) |
| stages[20].operations[7].sparsity | unknown (null) |
| stages[20].operations[7].scalar_flops | 0 |
| stages[20].operations[7].special_ops | {} |
| stages[20].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[20].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[20].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[20].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[20].operations[8].name | qk |
| stages[20].operations[8].matrix_flops | 67633152 |
| stages[20].operations[8].input_precision | BF16 |
| stages[20].operations[8].accumulator_precision | FP32 |
| stages[20].operations[8].sparsity | dense |
| stages[20].operations[8].scalar_flops | 0 |
| stages[20].operations[8].special_ops | {} |
| stages[20].operations[8].source_detail.Q[0] | 1 |
| stages[20].operations[8].source_detail.Q[1] | 32 |
| stages[20].operations[8].source_detail.Q[2] | 128 |
| stages[20].operations[8].source_detail.Q[3] | 128 |
| stages[20].operations[8].source_detail.K_shared[0] | 1 |
| stages[20].operations[8].source_detail.K_shared[1] | 8 |
| stages[20].operations[8].source_detail.K_shared[2] | 128 |
| stages[20].operations[8].source_detail.K_shared[3] | 128 |
| stages[20].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[20].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[20].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[20].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[20].operations[9].name | score_scale_mask_softmax |
| stages[20].operations[9].matrix_flops | 0 |
| stages[20].operations[9].input_precision | unknown (null) |
| stages[20].operations[9].accumulator_precision | unknown (null) |
| stages[20].operations[9].sparsity | unknown (null) |
| stages[20].operations[9].scalar_flops | 1052672 |
| stages[20].operations[9].special_ops.exp | 264192 |
| stages[20].operations[9].special_ops.compare_max | 260096 |
| stages[20].operations[9].special_ops.mask_decisions | 524288 |
| stages[20].operations[9].source_detail.scores[0] | 1 |
| stages[20].operations[9].source_detail.scores[1] | 32 |
| stages[20].operations[9].source_detail.scores[2] | 128 |
| stages[20].operations[9].source_detail.scores[3] | 128 |
| stages[20].operations[10].name | pv |
| stages[20].operations[10].matrix_flops | 67633152 |
| stages[20].operations[10].input_precision | BF16 |
| stages[20].operations[10].accumulator_precision | FP32 |
| stages[20].operations[10].sparsity | dense |
| stages[20].operations[10].scalar_flops | 0 |
| stages[20].operations[10].special_ops | {} |
| stages[20].operations[10].source_detail.P[0] | 1 |
| stages[20].operations[10].source_detail.P[1] | 32 |
| stages[20].operations[10].source_detail.P[2] | 128 |
| stages[20].operations[10].source_detail.P[3] | 128 |
| stages[20].operations[10].source_detail.V_shared[0] | 1 |
| stages[20].operations[10].source_detail.V_shared[1] | 8 |
| stages[20].operations[10].source_detail.V_shared[2] | 128 |
| stages[20].operations[10].source_detail.V_shared[3] | 128 |
| stages[20].operations[10].source_detail.output[0] | 1 |
| stages[20].operations[10].source_detail.output[1] | 32 |
| stages[20].operations[10].source_detail.output[2] | 128 |
| stages[20].operations[10].source_detail.output[3] | 128 |
| stages[20].operations[11].name | o_proj |
| stages[20].operations[11].matrix_flops | 4294967296 |
| stages[20].operations[11].input_precision | BF16 |
| stages[20].operations[11].accumulator_precision | FP32 |
| stages[20].operations[11].sparsity | dense |
| stages[20].operations[11].scalar_flops | 0 |
| stages[20].operations[11].special_ops | {} |
| stages[20].operations[11].source_detail.input[0] | 128 |
| stages[20].operations[11].source_detail.input[1] | 4096 |
| stages[20].operations[11].source_detail.weight_math[0] | 4096 |
| stages[20].operations[11].source_detail.weight_math[1] | 4096 |
| stages[20].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[20].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[11].source_detail.output[0] | 128 |
| stages[20].operations[11].source_detail.output[1] | 4096 |
| stages[20].operations[12].name | attention_residual |
| stages[20].operations[12].matrix_flops | 0 |
| stages[20].operations[12].input_precision | unknown (null) |
| stages[20].operations[12].accumulator_precision | unknown (null) |
| stages[20].operations[12].sparsity | unknown (null) |
| stages[20].operations[12].scalar_flops | 524288 |
| stages[20].operations[12].special_ops | {} |
| stages[20].operations[12].source_detail.inputs_each[0] | 128 |
| stages[20].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[20].operations[12].source_detail.output[0] | 128 |
| stages[20].operations[12].source_detail.output[1] | 4096 |
| stages[20].operations[13].name | post_attention_layernorm |
| stages[20].operations[13].matrix_flops | 0 |
| stages[20].operations[13].input_precision | unknown (null) |
| stages[20].operations[13].accumulator_precision | unknown (null) |
| stages[20].operations[13].sparsity | unknown (null) |
| stages[20].operations[13].scalar_flops | 2097280 |
| stages[20].operations[13].special_ops.rsqrt | 128 |
| stages[20].operations[13].source_detail.input[0] | 128 |
| stages[20].operations[13].source_detail.input[1] | 4096 |
| stages[20].operations[13].source_detail.weight[0] | 4096 |
| stages[20].operations[13].source_detail.output[0] | 128 |
| stages[20].operations[13].source_detail.output[1] | 4096 |
| stages[20].operations[14].name | gate_proj |
| stages[20].operations[14].matrix_flops | 12884901888 |
| stages[20].operations[14].input_precision | BF16 |
| stages[20].operations[14].accumulator_precision | FP32 |
| stages[20].operations[14].sparsity | dense |
| stages[20].operations[14].scalar_flops | 0 |
| stages[20].operations[14].special_ops | {} |
| stages[20].operations[14].source_detail.input[0] | 128 |
| stages[20].operations[14].source_detail.input[1] | 4096 |
| stages[20].operations[14].source_detail.weight_math[0] | 4096 |
| stages[20].operations[14].source_detail.weight_math[1] | 12288 |
| stages[20].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[20].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[14].source_detail.output[0] | 128 |
| stages[20].operations[14].source_detail.output[1] | 12288 |
| stages[20].operations[15].name | up_proj |
| stages[20].operations[15].matrix_flops | 12884901888 |
| stages[20].operations[15].input_precision | BF16 |
| stages[20].operations[15].accumulator_precision | FP32 |
| stages[20].operations[15].sparsity | dense |
| stages[20].operations[15].scalar_flops | 0 |
| stages[20].operations[15].special_ops | {} |
| stages[20].operations[15].source_detail.input[0] | 128 |
| stages[20].operations[15].source_detail.input[1] | 4096 |
| stages[20].operations[15].source_detail.weight_math[0] | 4096 |
| stages[20].operations[15].source_detail.weight_math[1] | 12288 |
| stages[20].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[20].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[20].operations[15].source_detail.output[0] | 128 |
| stages[20].operations[15].source_detail.output[1] | 12288 |
| stages[20].operations[16].name | silu_mul |
| stages[20].operations[16].matrix_flops | 0 |
| stages[20].operations[16].input_precision | unknown (null) |
| stages[20].operations[16].accumulator_precision | unknown (null) |
| stages[20].operations[16].sparsity | unknown (null) |
| stages[20].operations[16].scalar_flops | 6291456 |
| stages[20].operations[16].special_ops.exp | 1572864 |
| stages[20].operations[16].special_ops.negate | 1572864 |
| stages[20].operations[16].source_detail.gate[0] | 128 |
| stages[20].operations[16].source_detail.gate[1] | 12288 |
| stages[20].operations[16].source_detail.up[0] | 128 |
| stages[20].operations[16].source_detail.up[1] | 12288 |
| stages[20].operations[16].source_detail.output[0] | 128 |
| stages[20].operations[16].source_detail.output[1] | 12288 |
| stages[20].operations[17].name | down_proj |
| stages[20].operations[17].matrix_flops | 12884901888 |
| stages[20].operations[17].input_precision | BF16 |
| stages[20].operations[17].accumulator_precision | FP32 |
| stages[20].operations[17].sparsity | dense |
| stages[20].operations[17].scalar_flops | 0 |
| stages[20].operations[17].special_ops | {} |
| stages[20].operations[17].source_detail.input[0] | 128 |
| stages[20].operations[17].source_detail.input[1] | 12288 |
| stages[20].operations[17].source_detail.weight_math[0] | 12288 |
| stages[20].operations[17].source_detail.weight_math[1] | 4096 |
| stages[20].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[20].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[20].operations[17].source_detail.output[0] | 128 |
| stages[20].operations[17].source_detail.output[1] | 4096 |
| stages[20].operations[18].name | ffn_residual |
| stages[20].operations[18].matrix_flops | 0 |
| stages[20].operations[18].input_precision | unknown (null) |
| stages[20].operations[18].accumulator_precision | unknown (null) |
| stages[20].operations[18].sparsity | unknown (null) |
| stages[20].operations[18].scalar_flops | 524288 |
| stages[20].operations[18].special_ops | {} |
| stages[20].operations[18].source_detail.inputs_each[0] | 128 |
| stages[20].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[20].operations[18].source_detail.output[0] | 128 |
| stages[20].operations[18].source_detail.output[1] | 4096 |
| stages[21].id | layer:20 |
| stages[21].work.vector_fp32 | 17179904 |
| stages[21].work.special:rsqrt | 5376 |
| stages[21].work.interface_bytes | 438387200 |
| stages[21].work.matrix_bf16 | 49527390208 |
| stages[21].work.special:negate | 1900544 |
| stages[21].work.special:exp | 1837056 |
| stages[21].work.special:compare_max | 260096 |
| stages[21].work.special:mask_decisions | 524288 |
| stages[21].operations[0].name | input_layernorm |
| stages[21].operations[0].matrix_flops | 0 |
| stages[21].operations[0].input_precision | unknown (null) |
| stages[21].operations[0].accumulator_precision | unknown (null) |
| stages[21].operations[0].sparsity | unknown (null) |
| stages[21].operations[0].scalar_flops | 2097280 |
| stages[21].operations[0].special_ops.rsqrt | 128 |
| stages[21].operations[0].source_detail.input[0] | 128 |
| stages[21].operations[0].source_detail.input[1] | 4096 |
| stages[21].operations[0].source_detail.weight[0] | 4096 |
| stages[21].operations[0].source_detail.output[0] | 128 |
| stages[21].operations[0].source_detail.output[1] | 4096 |
| stages[21].operations[1].name | q_proj |
| stages[21].operations[1].matrix_flops | 4294967296 |
| stages[21].operations[1].input_precision | BF16 |
| stages[21].operations[1].accumulator_precision | FP32 |
| stages[21].operations[1].sparsity | dense |
| stages[21].operations[1].scalar_flops | 0 |
| stages[21].operations[1].special_ops | {} |
| stages[21].operations[1].source_detail.input[0] | 128 |
| stages[21].operations[1].source_detail.input[1] | 4096 |
| stages[21].operations[1].source_detail.weight_math[0] | 4096 |
| stages[21].operations[1].source_detail.weight_math[1] | 4096 |
| stages[21].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[21].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[1].source_detail.output[0] | 128 |
| stages[21].operations[1].source_detail.output[1] | 4096 |
| stages[21].operations[2].name | k_proj |
| stages[21].operations[2].matrix_flops | 1073741824 |
| stages[21].operations[2].input_precision | BF16 |
| stages[21].operations[2].accumulator_precision | FP32 |
| stages[21].operations[2].sparsity | dense |
| stages[21].operations[2].scalar_flops | 0 |
| stages[21].operations[2].special_ops | {} |
| stages[21].operations[2].source_detail.input[0] | 128 |
| stages[21].operations[2].source_detail.input[1] | 4096 |
| stages[21].operations[2].source_detail.weight_math[0] | 4096 |
| stages[21].operations[2].source_detail.weight_math[1] | 1024 |
| stages[21].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[21].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[2].source_detail.output[0] | 128 |
| stages[21].operations[2].source_detail.output[1] | 1024 |
| stages[21].operations[3].name | v_proj |
| stages[21].operations[3].matrix_flops | 1073741824 |
| stages[21].operations[3].input_precision | BF16 |
| stages[21].operations[3].accumulator_precision | FP32 |
| stages[21].operations[3].sparsity | dense |
| stages[21].operations[3].scalar_flops | 0 |
| stages[21].operations[3].special_ops | {} |
| stages[21].operations[3].source_detail.input[0] | 128 |
| stages[21].operations[3].source_detail.input[1] | 4096 |
| stages[21].operations[3].source_detail.weight_math[0] | 4096 |
| stages[21].operations[3].source_detail.weight_math[1] | 1024 |
| stages[21].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[21].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[3].source_detail.output[0] | 128 |
| stages[21].operations[3].source_detail.output[1] | 1024 |
| stages[21].operations[4].name | q_norm |
| stages[21].operations[4].matrix_flops | 0 |
| stages[21].operations[4].input_precision | unknown (null) |
| stages[21].operations[4].accumulator_precision | unknown (null) |
| stages[21].operations[4].sparsity | unknown (null) |
| stages[21].operations[4].scalar_flops | 2101248 |
| stages[21].operations[4].special_ops.rsqrt | 4096 |
| stages[21].operations[4].source_detail.input[0] | 4096 |
| stages[21].operations[4].source_detail.input[1] | 128 |
| stages[21].operations[4].source_detail.weight[0] | 128 |
| stages[21].operations[4].source_detail.output[0] | 4096 |
| stages[21].operations[4].source_detail.output[1] | 128 |
| stages[21].operations[5].name | k_norm |
| stages[21].operations[5].matrix_flops | 0 |
| stages[21].operations[5].input_precision | unknown (null) |
| stages[21].operations[5].accumulator_precision | unknown (null) |
| stages[21].operations[5].sparsity | unknown (null) |
| stages[21].operations[5].scalar_flops | 525312 |
| stages[21].operations[5].special_ops.rsqrt | 1024 |
| stages[21].operations[5].source_detail.input[0] | 1024 |
| stages[21].operations[5].source_detail.input[1] | 128 |
| stages[21].operations[5].source_detail.weight[0] | 128 |
| stages[21].operations[5].source_detail.output[0] | 1024 |
| stages[21].operations[5].source_detail.output[1] | 128 |
| stages[21].operations[6].name | apply_rope |
| stages[21].operations[6].matrix_flops | 0 |
| stages[21].operations[6].input_precision | unknown (null) |
| stages[21].operations[6].accumulator_precision | unknown (null) |
| stages[21].operations[6].sparsity | unknown (null) |
| stages[21].operations[6].scalar_flops | 1966080 |
| stages[21].operations[6].special_ops.negate | 327680 |
| stages[21].operations[6].source_detail.Q[0] | 1 |
| stages[21].operations[6].source_detail.Q[1] | 32 |
| stages[21].operations[6].source_detail.Q[2] | 128 |
| stages[21].operations[6].source_detail.Q[3] | 128 |
| stages[21].operations[6].source_detail.K[0] | 1 |
| stages[21].operations[6].source_detail.K[1] | 8 |
| stages[21].operations[6].source_detail.K[2] | 128 |
| stages[21].operations[6].source_detail.K[3] | 128 |
| stages[21].operations[7].name | kv_append |
| stages[21].operations[7].matrix_flops | 0 |
| stages[21].operations[7].input_precision | unknown (null) |
| stages[21].operations[7].accumulator_precision | unknown (null) |
| stages[21].operations[7].sparsity | unknown (null) |
| stages[21].operations[7].scalar_flops | 0 |
| stages[21].operations[7].special_ops | {} |
| stages[21].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[21].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[21].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[21].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[21].operations[8].name | qk |
| stages[21].operations[8].matrix_flops | 67633152 |
| stages[21].operations[8].input_precision | BF16 |
| stages[21].operations[8].accumulator_precision | FP32 |
| stages[21].operations[8].sparsity | dense |
| stages[21].operations[8].scalar_flops | 0 |
| stages[21].operations[8].special_ops | {} |
| stages[21].operations[8].source_detail.Q[0] | 1 |
| stages[21].operations[8].source_detail.Q[1] | 32 |
| stages[21].operations[8].source_detail.Q[2] | 128 |
| stages[21].operations[8].source_detail.Q[3] | 128 |
| stages[21].operations[8].source_detail.K_shared[0] | 1 |
| stages[21].operations[8].source_detail.K_shared[1] | 8 |
| stages[21].operations[8].source_detail.K_shared[2] | 128 |
| stages[21].operations[8].source_detail.K_shared[3] | 128 |
| stages[21].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[21].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[21].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[21].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[21].operations[9].name | score_scale_mask_softmax |
| stages[21].operations[9].matrix_flops | 0 |
| stages[21].operations[9].input_precision | unknown (null) |
| stages[21].operations[9].accumulator_precision | unknown (null) |
| stages[21].operations[9].sparsity | unknown (null) |
| stages[21].operations[9].scalar_flops | 1052672 |
| stages[21].operations[9].special_ops.exp | 264192 |
| stages[21].operations[9].special_ops.compare_max | 260096 |
| stages[21].operations[9].special_ops.mask_decisions | 524288 |
| stages[21].operations[9].source_detail.scores[0] | 1 |
| stages[21].operations[9].source_detail.scores[1] | 32 |
| stages[21].operations[9].source_detail.scores[2] | 128 |
| stages[21].operations[9].source_detail.scores[3] | 128 |
| stages[21].operations[10].name | pv |
| stages[21].operations[10].matrix_flops | 67633152 |
| stages[21].operations[10].input_precision | BF16 |
| stages[21].operations[10].accumulator_precision | FP32 |
| stages[21].operations[10].sparsity | dense |
| stages[21].operations[10].scalar_flops | 0 |
| stages[21].operations[10].special_ops | {} |
| stages[21].operations[10].source_detail.P[0] | 1 |
| stages[21].operations[10].source_detail.P[1] | 32 |
| stages[21].operations[10].source_detail.P[2] | 128 |
| stages[21].operations[10].source_detail.P[3] | 128 |
| stages[21].operations[10].source_detail.V_shared[0] | 1 |
| stages[21].operations[10].source_detail.V_shared[1] | 8 |
| stages[21].operations[10].source_detail.V_shared[2] | 128 |
| stages[21].operations[10].source_detail.V_shared[3] | 128 |
| stages[21].operations[10].source_detail.output[0] | 1 |
| stages[21].operations[10].source_detail.output[1] | 32 |
| stages[21].operations[10].source_detail.output[2] | 128 |
| stages[21].operations[10].source_detail.output[3] | 128 |
| stages[21].operations[11].name | o_proj |
| stages[21].operations[11].matrix_flops | 4294967296 |
| stages[21].operations[11].input_precision | BF16 |
| stages[21].operations[11].accumulator_precision | FP32 |
| stages[21].operations[11].sparsity | dense |
| stages[21].operations[11].scalar_flops | 0 |
| stages[21].operations[11].special_ops | {} |
| stages[21].operations[11].source_detail.input[0] | 128 |
| stages[21].operations[11].source_detail.input[1] | 4096 |
| stages[21].operations[11].source_detail.weight_math[0] | 4096 |
| stages[21].operations[11].source_detail.weight_math[1] | 4096 |
| stages[21].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[21].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[11].source_detail.output[0] | 128 |
| stages[21].operations[11].source_detail.output[1] | 4096 |
| stages[21].operations[12].name | attention_residual |
| stages[21].operations[12].matrix_flops | 0 |
| stages[21].operations[12].input_precision | unknown (null) |
| stages[21].operations[12].accumulator_precision | unknown (null) |
| stages[21].operations[12].sparsity | unknown (null) |
| stages[21].operations[12].scalar_flops | 524288 |
| stages[21].operations[12].special_ops | {} |
| stages[21].operations[12].source_detail.inputs_each[0] | 128 |
| stages[21].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[21].operations[12].source_detail.output[0] | 128 |
| stages[21].operations[12].source_detail.output[1] | 4096 |
| stages[21].operations[13].name | post_attention_layernorm |
| stages[21].operations[13].matrix_flops | 0 |
| stages[21].operations[13].input_precision | unknown (null) |
| stages[21].operations[13].accumulator_precision | unknown (null) |
| stages[21].operations[13].sparsity | unknown (null) |
| stages[21].operations[13].scalar_flops | 2097280 |
| stages[21].operations[13].special_ops.rsqrt | 128 |
| stages[21].operations[13].source_detail.input[0] | 128 |
| stages[21].operations[13].source_detail.input[1] | 4096 |
| stages[21].operations[13].source_detail.weight[0] | 4096 |
| stages[21].operations[13].source_detail.output[0] | 128 |
| stages[21].operations[13].source_detail.output[1] | 4096 |
| stages[21].operations[14].name | gate_proj |
| stages[21].operations[14].matrix_flops | 12884901888 |
| stages[21].operations[14].input_precision | BF16 |
| stages[21].operations[14].accumulator_precision | FP32 |
| stages[21].operations[14].sparsity | dense |
| stages[21].operations[14].scalar_flops | 0 |
| stages[21].operations[14].special_ops | {} |
| stages[21].operations[14].source_detail.input[0] | 128 |
| stages[21].operations[14].source_detail.input[1] | 4096 |
| stages[21].operations[14].source_detail.weight_math[0] | 4096 |
| stages[21].operations[14].source_detail.weight_math[1] | 12288 |
| stages[21].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[21].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[14].source_detail.output[0] | 128 |
| stages[21].operations[14].source_detail.output[1] | 12288 |
| stages[21].operations[15].name | up_proj |
| stages[21].operations[15].matrix_flops | 12884901888 |
| stages[21].operations[15].input_precision | BF16 |
| stages[21].operations[15].accumulator_precision | FP32 |
| stages[21].operations[15].sparsity | dense |
| stages[21].operations[15].scalar_flops | 0 |
| stages[21].operations[15].special_ops | {} |
| stages[21].operations[15].source_detail.input[0] | 128 |
| stages[21].operations[15].source_detail.input[1] | 4096 |
| stages[21].operations[15].source_detail.weight_math[0] | 4096 |
| stages[21].operations[15].source_detail.weight_math[1] | 12288 |
| stages[21].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[21].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[21].operations[15].source_detail.output[0] | 128 |
| stages[21].operations[15].source_detail.output[1] | 12288 |
| stages[21].operations[16].name | silu_mul |
| stages[21].operations[16].matrix_flops | 0 |
| stages[21].operations[16].input_precision | unknown (null) |
| stages[21].operations[16].accumulator_precision | unknown (null) |
| stages[21].operations[16].sparsity | unknown (null) |
| stages[21].operations[16].scalar_flops | 6291456 |
| stages[21].operations[16].special_ops.exp | 1572864 |
| stages[21].operations[16].special_ops.negate | 1572864 |
| stages[21].operations[16].source_detail.gate[0] | 128 |
| stages[21].operations[16].source_detail.gate[1] | 12288 |
| stages[21].operations[16].source_detail.up[0] | 128 |
| stages[21].operations[16].source_detail.up[1] | 12288 |
| stages[21].operations[16].source_detail.output[0] | 128 |
| stages[21].operations[16].source_detail.output[1] | 12288 |
| stages[21].operations[17].name | down_proj |
| stages[21].operations[17].matrix_flops | 12884901888 |
| stages[21].operations[17].input_precision | BF16 |
| stages[21].operations[17].accumulator_precision | FP32 |
| stages[21].operations[17].sparsity | dense |
| stages[21].operations[17].scalar_flops | 0 |
| stages[21].operations[17].special_ops | {} |
| stages[21].operations[17].source_detail.input[0] | 128 |
| stages[21].operations[17].source_detail.input[1] | 12288 |
| stages[21].operations[17].source_detail.weight_math[0] | 12288 |
| stages[21].operations[17].source_detail.weight_math[1] | 4096 |
| stages[21].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[21].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[21].operations[17].source_detail.output[0] | 128 |
| stages[21].operations[17].source_detail.output[1] | 4096 |
| stages[21].operations[18].name | ffn_residual |
| stages[21].operations[18].matrix_flops | 0 |
| stages[21].operations[18].input_precision | unknown (null) |
| stages[21].operations[18].accumulator_precision | unknown (null) |
| stages[21].operations[18].sparsity | unknown (null) |
| stages[21].operations[18].scalar_flops | 524288 |
| stages[21].operations[18].special_ops | {} |
| stages[21].operations[18].source_detail.inputs_each[0] | 128 |
| stages[21].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[21].operations[18].source_detail.output[0] | 128 |
| stages[21].operations[18].source_detail.output[1] | 4096 |
| stages[22].id | layer:21 |
| stages[22].work.vector_fp32 | 17179904 |
| stages[22].work.special:rsqrt | 5376 |
| stages[22].work.interface_bytes | 438387200 |
| stages[22].work.matrix_bf16 | 49527390208 |
| stages[22].work.special:negate | 1900544 |
| stages[22].work.special:exp | 1837056 |
| stages[22].work.special:compare_max | 260096 |
| stages[22].work.special:mask_decisions | 524288 |
| stages[22].operations[0].name | input_layernorm |
| stages[22].operations[0].matrix_flops | 0 |
| stages[22].operations[0].input_precision | unknown (null) |
| stages[22].operations[0].accumulator_precision | unknown (null) |
| stages[22].operations[0].sparsity | unknown (null) |
| stages[22].operations[0].scalar_flops | 2097280 |
| stages[22].operations[0].special_ops.rsqrt | 128 |
| stages[22].operations[0].source_detail.input[0] | 128 |
| stages[22].operations[0].source_detail.input[1] | 4096 |
| stages[22].operations[0].source_detail.weight[0] | 4096 |
| stages[22].operations[0].source_detail.output[0] | 128 |
| stages[22].operations[0].source_detail.output[1] | 4096 |
| stages[22].operations[1].name | q_proj |
| stages[22].operations[1].matrix_flops | 4294967296 |
| stages[22].operations[1].input_precision | BF16 |
| stages[22].operations[1].accumulator_precision | FP32 |
| stages[22].operations[1].sparsity | dense |
| stages[22].operations[1].scalar_flops | 0 |
| stages[22].operations[1].special_ops | {} |
| stages[22].operations[1].source_detail.input[0] | 128 |
| stages[22].operations[1].source_detail.input[1] | 4096 |
| stages[22].operations[1].source_detail.weight_math[0] | 4096 |
| stages[22].operations[1].source_detail.weight_math[1] | 4096 |
| stages[22].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[22].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[1].source_detail.output[0] | 128 |
| stages[22].operations[1].source_detail.output[1] | 4096 |
| stages[22].operations[2].name | k_proj |
| stages[22].operations[2].matrix_flops | 1073741824 |
| stages[22].operations[2].input_precision | BF16 |
| stages[22].operations[2].accumulator_precision | FP32 |
| stages[22].operations[2].sparsity | dense |
| stages[22].operations[2].scalar_flops | 0 |
| stages[22].operations[2].special_ops | {} |
| stages[22].operations[2].source_detail.input[0] | 128 |
| stages[22].operations[2].source_detail.input[1] | 4096 |
| stages[22].operations[2].source_detail.weight_math[0] | 4096 |
| stages[22].operations[2].source_detail.weight_math[1] | 1024 |
| stages[22].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[22].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[2].source_detail.output[0] | 128 |
| stages[22].operations[2].source_detail.output[1] | 1024 |
| stages[22].operations[3].name | v_proj |
| stages[22].operations[3].matrix_flops | 1073741824 |
| stages[22].operations[3].input_precision | BF16 |
| stages[22].operations[3].accumulator_precision | FP32 |
| stages[22].operations[3].sparsity | dense |
| stages[22].operations[3].scalar_flops | 0 |
| stages[22].operations[3].special_ops | {} |
| stages[22].operations[3].source_detail.input[0] | 128 |
| stages[22].operations[3].source_detail.input[1] | 4096 |
| stages[22].operations[3].source_detail.weight_math[0] | 4096 |
| stages[22].operations[3].source_detail.weight_math[1] | 1024 |
| stages[22].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[22].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[3].source_detail.output[0] | 128 |
| stages[22].operations[3].source_detail.output[1] | 1024 |
| stages[22].operations[4].name | q_norm |
| stages[22].operations[4].matrix_flops | 0 |
| stages[22].operations[4].input_precision | unknown (null) |
| stages[22].operations[4].accumulator_precision | unknown (null) |
| stages[22].operations[4].sparsity | unknown (null) |
| stages[22].operations[4].scalar_flops | 2101248 |
| stages[22].operations[4].special_ops.rsqrt | 4096 |
| stages[22].operations[4].source_detail.input[0] | 4096 |
| stages[22].operations[4].source_detail.input[1] | 128 |
| stages[22].operations[4].source_detail.weight[0] | 128 |
| stages[22].operations[4].source_detail.output[0] | 4096 |
| stages[22].operations[4].source_detail.output[1] | 128 |
| stages[22].operations[5].name | k_norm |
| stages[22].operations[5].matrix_flops | 0 |
| stages[22].operations[5].input_precision | unknown (null) |
| stages[22].operations[5].accumulator_precision | unknown (null) |
| stages[22].operations[5].sparsity | unknown (null) |
| stages[22].operations[5].scalar_flops | 525312 |
| stages[22].operations[5].special_ops.rsqrt | 1024 |
| stages[22].operations[5].source_detail.input[0] | 1024 |
| stages[22].operations[5].source_detail.input[1] | 128 |
| stages[22].operations[5].source_detail.weight[0] | 128 |
| stages[22].operations[5].source_detail.output[0] | 1024 |
| stages[22].operations[5].source_detail.output[1] | 128 |
| stages[22].operations[6].name | apply_rope |
| stages[22].operations[6].matrix_flops | 0 |
| stages[22].operations[6].input_precision | unknown (null) |
| stages[22].operations[6].accumulator_precision | unknown (null) |
| stages[22].operations[6].sparsity | unknown (null) |
| stages[22].operations[6].scalar_flops | 1966080 |
| stages[22].operations[6].special_ops.negate | 327680 |
| stages[22].operations[6].source_detail.Q[0] | 1 |
| stages[22].operations[6].source_detail.Q[1] | 32 |
| stages[22].operations[6].source_detail.Q[2] | 128 |
| stages[22].operations[6].source_detail.Q[3] | 128 |
| stages[22].operations[6].source_detail.K[0] | 1 |
| stages[22].operations[6].source_detail.K[1] | 8 |
| stages[22].operations[6].source_detail.K[2] | 128 |
| stages[22].operations[6].source_detail.K[3] | 128 |
| stages[22].operations[7].name | kv_append |
| stages[22].operations[7].matrix_flops | 0 |
| stages[22].operations[7].input_precision | unknown (null) |
| stages[22].operations[7].accumulator_precision | unknown (null) |
| stages[22].operations[7].sparsity | unknown (null) |
| stages[22].operations[7].scalar_flops | 0 |
| stages[22].operations[7].special_ops | {} |
| stages[22].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[22].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[22].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[22].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[22].operations[8].name | qk |
| stages[22].operations[8].matrix_flops | 67633152 |
| stages[22].operations[8].input_precision | BF16 |
| stages[22].operations[8].accumulator_precision | FP32 |
| stages[22].operations[8].sparsity | dense |
| stages[22].operations[8].scalar_flops | 0 |
| stages[22].operations[8].special_ops | {} |
| stages[22].operations[8].source_detail.Q[0] | 1 |
| stages[22].operations[8].source_detail.Q[1] | 32 |
| stages[22].operations[8].source_detail.Q[2] | 128 |
| stages[22].operations[8].source_detail.Q[3] | 128 |
| stages[22].operations[8].source_detail.K_shared[0] | 1 |
| stages[22].operations[8].source_detail.K_shared[1] | 8 |
| stages[22].operations[8].source_detail.K_shared[2] | 128 |
| stages[22].operations[8].source_detail.K_shared[3] | 128 |
| stages[22].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[22].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[22].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[22].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[22].operations[9].name | score_scale_mask_softmax |
| stages[22].operations[9].matrix_flops | 0 |
| stages[22].operations[9].input_precision | unknown (null) |
| stages[22].operations[9].accumulator_precision | unknown (null) |
| stages[22].operations[9].sparsity | unknown (null) |
| stages[22].operations[9].scalar_flops | 1052672 |
| stages[22].operations[9].special_ops.exp | 264192 |
| stages[22].operations[9].special_ops.compare_max | 260096 |
| stages[22].operations[9].special_ops.mask_decisions | 524288 |
| stages[22].operations[9].source_detail.scores[0] | 1 |
| stages[22].operations[9].source_detail.scores[1] | 32 |
| stages[22].operations[9].source_detail.scores[2] | 128 |
| stages[22].operations[9].source_detail.scores[3] | 128 |
| stages[22].operations[10].name | pv |
| stages[22].operations[10].matrix_flops | 67633152 |
| stages[22].operations[10].input_precision | BF16 |
| stages[22].operations[10].accumulator_precision | FP32 |
| stages[22].operations[10].sparsity | dense |
| stages[22].operations[10].scalar_flops | 0 |
| stages[22].operations[10].special_ops | {} |
| stages[22].operations[10].source_detail.P[0] | 1 |
| stages[22].operations[10].source_detail.P[1] | 32 |
| stages[22].operations[10].source_detail.P[2] | 128 |
| stages[22].operations[10].source_detail.P[3] | 128 |
| stages[22].operations[10].source_detail.V_shared[0] | 1 |
| stages[22].operations[10].source_detail.V_shared[1] | 8 |
| stages[22].operations[10].source_detail.V_shared[2] | 128 |
| stages[22].operations[10].source_detail.V_shared[3] | 128 |
| stages[22].operations[10].source_detail.output[0] | 1 |
| stages[22].operations[10].source_detail.output[1] | 32 |
| stages[22].operations[10].source_detail.output[2] | 128 |
| stages[22].operations[10].source_detail.output[3] | 128 |
| stages[22].operations[11].name | o_proj |
| stages[22].operations[11].matrix_flops | 4294967296 |
| stages[22].operations[11].input_precision | BF16 |
| stages[22].operations[11].accumulator_precision | FP32 |
| stages[22].operations[11].sparsity | dense |
| stages[22].operations[11].scalar_flops | 0 |
| stages[22].operations[11].special_ops | {} |
| stages[22].operations[11].source_detail.input[0] | 128 |
| stages[22].operations[11].source_detail.input[1] | 4096 |
| stages[22].operations[11].source_detail.weight_math[0] | 4096 |
| stages[22].operations[11].source_detail.weight_math[1] | 4096 |
| stages[22].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[22].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[11].source_detail.output[0] | 128 |
| stages[22].operations[11].source_detail.output[1] | 4096 |
| stages[22].operations[12].name | attention_residual |
| stages[22].operations[12].matrix_flops | 0 |
| stages[22].operations[12].input_precision | unknown (null) |
| stages[22].operations[12].accumulator_precision | unknown (null) |
| stages[22].operations[12].sparsity | unknown (null) |
| stages[22].operations[12].scalar_flops | 524288 |
| stages[22].operations[12].special_ops | {} |
| stages[22].operations[12].source_detail.inputs_each[0] | 128 |
| stages[22].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[22].operations[12].source_detail.output[0] | 128 |
| stages[22].operations[12].source_detail.output[1] | 4096 |
| stages[22].operations[13].name | post_attention_layernorm |
| stages[22].operations[13].matrix_flops | 0 |
| stages[22].operations[13].input_precision | unknown (null) |
| stages[22].operations[13].accumulator_precision | unknown (null) |
| stages[22].operations[13].sparsity | unknown (null) |
| stages[22].operations[13].scalar_flops | 2097280 |
| stages[22].operations[13].special_ops.rsqrt | 128 |
| stages[22].operations[13].source_detail.input[0] | 128 |
| stages[22].operations[13].source_detail.input[1] | 4096 |
| stages[22].operations[13].source_detail.weight[0] | 4096 |
| stages[22].operations[13].source_detail.output[0] | 128 |
| stages[22].operations[13].source_detail.output[1] | 4096 |
| stages[22].operations[14].name | gate_proj |
| stages[22].operations[14].matrix_flops | 12884901888 |
| stages[22].operations[14].input_precision | BF16 |
| stages[22].operations[14].accumulator_precision | FP32 |
| stages[22].operations[14].sparsity | dense |
| stages[22].operations[14].scalar_flops | 0 |
| stages[22].operations[14].special_ops | {} |
| stages[22].operations[14].source_detail.input[0] | 128 |
| stages[22].operations[14].source_detail.input[1] | 4096 |
| stages[22].operations[14].source_detail.weight_math[0] | 4096 |
| stages[22].operations[14].source_detail.weight_math[1] | 12288 |
| stages[22].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[22].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[14].source_detail.output[0] | 128 |
| stages[22].operations[14].source_detail.output[1] | 12288 |
| stages[22].operations[15].name | up_proj |
| stages[22].operations[15].matrix_flops | 12884901888 |
| stages[22].operations[15].input_precision | BF16 |
| stages[22].operations[15].accumulator_precision | FP32 |
| stages[22].operations[15].sparsity | dense |
| stages[22].operations[15].scalar_flops | 0 |
| stages[22].operations[15].special_ops | {} |
| stages[22].operations[15].source_detail.input[0] | 128 |
| stages[22].operations[15].source_detail.input[1] | 4096 |
| stages[22].operations[15].source_detail.weight_math[0] | 4096 |
| stages[22].operations[15].source_detail.weight_math[1] | 12288 |
| stages[22].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[22].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[22].operations[15].source_detail.output[0] | 128 |
| stages[22].operations[15].source_detail.output[1] | 12288 |
| stages[22].operations[16].name | silu_mul |
| stages[22].operations[16].matrix_flops | 0 |
| stages[22].operations[16].input_precision | unknown (null) |
| stages[22].operations[16].accumulator_precision | unknown (null) |
| stages[22].operations[16].sparsity | unknown (null) |
| stages[22].operations[16].scalar_flops | 6291456 |
| stages[22].operations[16].special_ops.exp | 1572864 |
| stages[22].operations[16].special_ops.negate | 1572864 |
| stages[22].operations[16].source_detail.gate[0] | 128 |
| stages[22].operations[16].source_detail.gate[1] | 12288 |
| stages[22].operations[16].source_detail.up[0] | 128 |
| stages[22].operations[16].source_detail.up[1] | 12288 |
| stages[22].operations[16].source_detail.output[0] | 128 |
| stages[22].operations[16].source_detail.output[1] | 12288 |
| stages[22].operations[17].name | down_proj |
| stages[22].operations[17].matrix_flops | 12884901888 |
| stages[22].operations[17].input_precision | BF16 |
| stages[22].operations[17].accumulator_precision | FP32 |
| stages[22].operations[17].sparsity | dense |
| stages[22].operations[17].scalar_flops | 0 |
| stages[22].operations[17].special_ops | {} |
| stages[22].operations[17].source_detail.input[0] | 128 |
| stages[22].operations[17].source_detail.input[1] | 12288 |
| stages[22].operations[17].source_detail.weight_math[0] | 12288 |
| stages[22].operations[17].source_detail.weight_math[1] | 4096 |
| stages[22].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[22].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[22].operations[17].source_detail.output[0] | 128 |
| stages[22].operations[17].source_detail.output[1] | 4096 |
| stages[22].operations[18].name | ffn_residual |
| stages[22].operations[18].matrix_flops | 0 |
| stages[22].operations[18].input_precision | unknown (null) |
| stages[22].operations[18].accumulator_precision | unknown (null) |
| stages[22].operations[18].sparsity | unknown (null) |
| stages[22].operations[18].scalar_flops | 524288 |
| stages[22].operations[18].special_ops | {} |
| stages[22].operations[18].source_detail.inputs_each[0] | 128 |
| stages[22].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[22].operations[18].source_detail.output[0] | 128 |
| stages[22].operations[18].source_detail.output[1] | 4096 |
| stages[23].id | layer:22 |
| stages[23].work.vector_fp32 | 17179904 |
| stages[23].work.special:rsqrt | 5376 |
| stages[23].work.interface_bytes | 438387200 |
| stages[23].work.matrix_bf16 | 49527390208 |
| stages[23].work.special:negate | 1900544 |
| stages[23].work.special:exp | 1837056 |
| stages[23].work.special:compare_max | 260096 |
| stages[23].work.special:mask_decisions | 524288 |
| stages[23].operations[0].name | input_layernorm |
| stages[23].operations[0].matrix_flops | 0 |
| stages[23].operations[0].input_precision | unknown (null) |
| stages[23].operations[0].accumulator_precision | unknown (null) |
| stages[23].operations[0].sparsity | unknown (null) |
| stages[23].operations[0].scalar_flops | 2097280 |
| stages[23].operations[0].special_ops.rsqrt | 128 |
| stages[23].operations[0].source_detail.input[0] | 128 |
| stages[23].operations[0].source_detail.input[1] | 4096 |
| stages[23].operations[0].source_detail.weight[0] | 4096 |
| stages[23].operations[0].source_detail.output[0] | 128 |
| stages[23].operations[0].source_detail.output[1] | 4096 |
| stages[23].operations[1].name | q_proj |
| stages[23].operations[1].matrix_flops | 4294967296 |
| stages[23].operations[1].input_precision | BF16 |
| stages[23].operations[1].accumulator_precision | FP32 |
| stages[23].operations[1].sparsity | dense |
| stages[23].operations[1].scalar_flops | 0 |
| stages[23].operations[1].special_ops | {} |
| stages[23].operations[1].source_detail.input[0] | 128 |
| stages[23].operations[1].source_detail.input[1] | 4096 |
| stages[23].operations[1].source_detail.weight_math[0] | 4096 |
| stages[23].operations[1].source_detail.weight_math[1] | 4096 |
| stages[23].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[23].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[1].source_detail.output[0] | 128 |
| stages[23].operations[1].source_detail.output[1] | 4096 |
| stages[23].operations[2].name | k_proj |
| stages[23].operations[2].matrix_flops | 1073741824 |
| stages[23].operations[2].input_precision | BF16 |
| stages[23].operations[2].accumulator_precision | FP32 |
| stages[23].operations[2].sparsity | dense |
| stages[23].operations[2].scalar_flops | 0 |
| stages[23].operations[2].special_ops | {} |
| stages[23].operations[2].source_detail.input[0] | 128 |
| stages[23].operations[2].source_detail.input[1] | 4096 |
| stages[23].operations[2].source_detail.weight_math[0] | 4096 |
| stages[23].operations[2].source_detail.weight_math[1] | 1024 |
| stages[23].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[23].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[2].source_detail.output[0] | 128 |
| stages[23].operations[2].source_detail.output[1] | 1024 |
| stages[23].operations[3].name | v_proj |
| stages[23].operations[3].matrix_flops | 1073741824 |
| stages[23].operations[3].input_precision | BF16 |
| stages[23].operations[3].accumulator_precision | FP32 |
| stages[23].operations[3].sparsity | dense |
| stages[23].operations[3].scalar_flops | 0 |
| stages[23].operations[3].special_ops | {} |
| stages[23].operations[3].source_detail.input[0] | 128 |
| stages[23].operations[3].source_detail.input[1] | 4096 |
| stages[23].operations[3].source_detail.weight_math[0] | 4096 |
| stages[23].operations[3].source_detail.weight_math[1] | 1024 |
| stages[23].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[23].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[3].source_detail.output[0] | 128 |
| stages[23].operations[3].source_detail.output[1] | 1024 |
| stages[23].operations[4].name | q_norm |
| stages[23].operations[4].matrix_flops | 0 |
| stages[23].operations[4].input_precision | unknown (null) |
| stages[23].operations[4].accumulator_precision | unknown (null) |
| stages[23].operations[4].sparsity | unknown (null) |
| stages[23].operations[4].scalar_flops | 2101248 |
| stages[23].operations[4].special_ops.rsqrt | 4096 |
| stages[23].operations[4].source_detail.input[0] | 4096 |
| stages[23].operations[4].source_detail.input[1] | 128 |
| stages[23].operations[4].source_detail.weight[0] | 128 |
| stages[23].operations[4].source_detail.output[0] | 4096 |
| stages[23].operations[4].source_detail.output[1] | 128 |
| stages[23].operations[5].name | k_norm |
| stages[23].operations[5].matrix_flops | 0 |
| stages[23].operations[5].input_precision | unknown (null) |
| stages[23].operations[5].accumulator_precision | unknown (null) |
| stages[23].operations[5].sparsity | unknown (null) |
| stages[23].operations[5].scalar_flops | 525312 |
| stages[23].operations[5].special_ops.rsqrt | 1024 |
| stages[23].operations[5].source_detail.input[0] | 1024 |
| stages[23].operations[5].source_detail.input[1] | 128 |
| stages[23].operations[5].source_detail.weight[0] | 128 |
| stages[23].operations[5].source_detail.output[0] | 1024 |
| stages[23].operations[5].source_detail.output[1] | 128 |
| stages[23].operations[6].name | apply_rope |
| stages[23].operations[6].matrix_flops | 0 |
| stages[23].operations[6].input_precision | unknown (null) |
| stages[23].operations[6].accumulator_precision | unknown (null) |
| stages[23].operations[6].sparsity | unknown (null) |
| stages[23].operations[6].scalar_flops | 1966080 |
| stages[23].operations[6].special_ops.negate | 327680 |
| stages[23].operations[6].source_detail.Q[0] | 1 |
| stages[23].operations[6].source_detail.Q[1] | 32 |
| stages[23].operations[6].source_detail.Q[2] | 128 |
| stages[23].operations[6].source_detail.Q[3] | 128 |
| stages[23].operations[6].source_detail.K[0] | 1 |
| stages[23].operations[6].source_detail.K[1] | 8 |
| stages[23].operations[6].source_detail.K[2] | 128 |
| stages[23].operations[6].source_detail.K[3] | 128 |
| stages[23].operations[7].name | kv_append |
| stages[23].operations[7].matrix_flops | 0 |
| stages[23].operations[7].input_precision | unknown (null) |
| stages[23].operations[7].accumulator_precision | unknown (null) |
| stages[23].operations[7].sparsity | unknown (null) |
| stages[23].operations[7].scalar_flops | 0 |
| stages[23].operations[7].special_ops | {} |
| stages[23].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[23].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[23].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[23].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[23].operations[8].name | qk |
| stages[23].operations[8].matrix_flops | 67633152 |
| stages[23].operations[8].input_precision | BF16 |
| stages[23].operations[8].accumulator_precision | FP32 |
| stages[23].operations[8].sparsity | dense |
| stages[23].operations[8].scalar_flops | 0 |
| stages[23].operations[8].special_ops | {} |
| stages[23].operations[8].source_detail.Q[0] | 1 |
| stages[23].operations[8].source_detail.Q[1] | 32 |
| stages[23].operations[8].source_detail.Q[2] | 128 |
| stages[23].operations[8].source_detail.Q[3] | 128 |
| stages[23].operations[8].source_detail.K_shared[0] | 1 |
| stages[23].operations[8].source_detail.K_shared[1] | 8 |
| stages[23].operations[8].source_detail.K_shared[2] | 128 |
| stages[23].operations[8].source_detail.K_shared[3] | 128 |
| stages[23].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[23].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[23].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[23].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[23].operations[9].name | score_scale_mask_softmax |
| stages[23].operations[9].matrix_flops | 0 |
| stages[23].operations[9].input_precision | unknown (null) |
| stages[23].operations[9].accumulator_precision | unknown (null) |
| stages[23].operations[9].sparsity | unknown (null) |
| stages[23].operations[9].scalar_flops | 1052672 |
| stages[23].operations[9].special_ops.exp | 264192 |
| stages[23].operations[9].special_ops.compare_max | 260096 |
| stages[23].operations[9].special_ops.mask_decisions | 524288 |
| stages[23].operations[9].source_detail.scores[0] | 1 |
| stages[23].operations[9].source_detail.scores[1] | 32 |
| stages[23].operations[9].source_detail.scores[2] | 128 |
| stages[23].operations[9].source_detail.scores[3] | 128 |
| stages[23].operations[10].name | pv |
| stages[23].operations[10].matrix_flops | 67633152 |
| stages[23].operations[10].input_precision | BF16 |
| stages[23].operations[10].accumulator_precision | FP32 |
| stages[23].operations[10].sparsity | dense |
| stages[23].operations[10].scalar_flops | 0 |
| stages[23].operations[10].special_ops | {} |
| stages[23].operations[10].source_detail.P[0] | 1 |
| stages[23].operations[10].source_detail.P[1] | 32 |
| stages[23].operations[10].source_detail.P[2] | 128 |
| stages[23].operations[10].source_detail.P[3] | 128 |
| stages[23].operations[10].source_detail.V_shared[0] | 1 |
| stages[23].operations[10].source_detail.V_shared[1] | 8 |
| stages[23].operations[10].source_detail.V_shared[2] | 128 |
| stages[23].operations[10].source_detail.V_shared[3] | 128 |
| stages[23].operations[10].source_detail.output[0] | 1 |
| stages[23].operations[10].source_detail.output[1] | 32 |
| stages[23].operations[10].source_detail.output[2] | 128 |
| stages[23].operations[10].source_detail.output[3] | 128 |
| stages[23].operations[11].name | o_proj |
| stages[23].operations[11].matrix_flops | 4294967296 |
| stages[23].operations[11].input_precision | BF16 |
| stages[23].operations[11].accumulator_precision | FP32 |
| stages[23].operations[11].sparsity | dense |
| stages[23].operations[11].scalar_flops | 0 |
| stages[23].operations[11].special_ops | {} |
| stages[23].operations[11].source_detail.input[0] | 128 |
| stages[23].operations[11].source_detail.input[1] | 4096 |
| stages[23].operations[11].source_detail.weight_math[0] | 4096 |
| stages[23].operations[11].source_detail.weight_math[1] | 4096 |
| stages[23].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[23].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[11].source_detail.output[0] | 128 |
| stages[23].operations[11].source_detail.output[1] | 4096 |
| stages[23].operations[12].name | attention_residual |
| stages[23].operations[12].matrix_flops | 0 |
| stages[23].operations[12].input_precision | unknown (null) |
| stages[23].operations[12].accumulator_precision | unknown (null) |
| stages[23].operations[12].sparsity | unknown (null) |
| stages[23].operations[12].scalar_flops | 524288 |
| stages[23].operations[12].special_ops | {} |
| stages[23].operations[12].source_detail.inputs_each[0] | 128 |
| stages[23].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[23].operations[12].source_detail.output[0] | 128 |
| stages[23].operations[12].source_detail.output[1] | 4096 |
| stages[23].operations[13].name | post_attention_layernorm |
| stages[23].operations[13].matrix_flops | 0 |
| stages[23].operations[13].input_precision | unknown (null) |
| stages[23].operations[13].accumulator_precision | unknown (null) |
| stages[23].operations[13].sparsity | unknown (null) |
| stages[23].operations[13].scalar_flops | 2097280 |
| stages[23].operations[13].special_ops.rsqrt | 128 |
| stages[23].operations[13].source_detail.input[0] | 128 |
| stages[23].operations[13].source_detail.input[1] | 4096 |
| stages[23].operations[13].source_detail.weight[0] | 4096 |
| stages[23].operations[13].source_detail.output[0] | 128 |
| stages[23].operations[13].source_detail.output[1] | 4096 |
| stages[23].operations[14].name | gate_proj |
| stages[23].operations[14].matrix_flops | 12884901888 |
| stages[23].operations[14].input_precision | BF16 |
| stages[23].operations[14].accumulator_precision | FP32 |
| stages[23].operations[14].sparsity | dense |
| stages[23].operations[14].scalar_flops | 0 |
| stages[23].operations[14].special_ops | {} |
| stages[23].operations[14].source_detail.input[0] | 128 |
| stages[23].operations[14].source_detail.input[1] | 4096 |
| stages[23].operations[14].source_detail.weight_math[0] | 4096 |
| stages[23].operations[14].source_detail.weight_math[1] | 12288 |
| stages[23].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[23].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[14].source_detail.output[0] | 128 |
| stages[23].operations[14].source_detail.output[1] | 12288 |
| stages[23].operations[15].name | up_proj |
| stages[23].operations[15].matrix_flops | 12884901888 |
| stages[23].operations[15].input_precision | BF16 |
| stages[23].operations[15].accumulator_precision | FP32 |
| stages[23].operations[15].sparsity | dense |
| stages[23].operations[15].scalar_flops | 0 |
| stages[23].operations[15].special_ops | {} |
| stages[23].operations[15].source_detail.input[0] | 128 |
| stages[23].operations[15].source_detail.input[1] | 4096 |
| stages[23].operations[15].source_detail.weight_math[0] | 4096 |
| stages[23].operations[15].source_detail.weight_math[1] | 12288 |
| stages[23].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[23].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[23].operations[15].source_detail.output[0] | 128 |
| stages[23].operations[15].source_detail.output[1] | 12288 |
| stages[23].operations[16].name | silu_mul |
| stages[23].operations[16].matrix_flops | 0 |
| stages[23].operations[16].input_precision | unknown (null) |
| stages[23].operations[16].accumulator_precision | unknown (null) |
| stages[23].operations[16].sparsity | unknown (null) |
| stages[23].operations[16].scalar_flops | 6291456 |
| stages[23].operations[16].special_ops.exp | 1572864 |
| stages[23].operations[16].special_ops.negate | 1572864 |
| stages[23].operations[16].source_detail.gate[0] | 128 |
| stages[23].operations[16].source_detail.gate[1] | 12288 |
| stages[23].operations[16].source_detail.up[0] | 128 |
| stages[23].operations[16].source_detail.up[1] | 12288 |
| stages[23].operations[16].source_detail.output[0] | 128 |
| stages[23].operations[16].source_detail.output[1] | 12288 |
| stages[23].operations[17].name | down_proj |
| stages[23].operations[17].matrix_flops | 12884901888 |
| stages[23].operations[17].input_precision | BF16 |
| stages[23].operations[17].accumulator_precision | FP32 |
| stages[23].operations[17].sparsity | dense |
| stages[23].operations[17].scalar_flops | 0 |
| stages[23].operations[17].special_ops | {} |
| stages[23].operations[17].source_detail.input[0] | 128 |
| stages[23].operations[17].source_detail.input[1] | 12288 |
| stages[23].operations[17].source_detail.weight_math[0] | 12288 |
| stages[23].operations[17].source_detail.weight_math[1] | 4096 |
| stages[23].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[23].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[23].operations[17].source_detail.output[0] | 128 |
| stages[23].operations[17].source_detail.output[1] | 4096 |
| stages[23].operations[18].name | ffn_residual |
| stages[23].operations[18].matrix_flops | 0 |
| stages[23].operations[18].input_precision | unknown (null) |
| stages[23].operations[18].accumulator_precision | unknown (null) |
| stages[23].operations[18].sparsity | unknown (null) |
| stages[23].operations[18].scalar_flops | 524288 |
| stages[23].operations[18].special_ops | {} |
| stages[23].operations[18].source_detail.inputs_each[0] | 128 |
| stages[23].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[23].operations[18].source_detail.output[0] | 128 |
| stages[23].operations[18].source_detail.output[1] | 4096 |
| stages[24].id | layer:23 |
| stages[24].work.vector_fp32 | 17179904 |
| stages[24].work.special:rsqrt | 5376 |
| stages[24].work.interface_bytes | 438387200 |
| stages[24].work.matrix_bf16 | 49527390208 |
| stages[24].work.special:negate | 1900544 |
| stages[24].work.special:exp | 1837056 |
| stages[24].work.special:compare_max | 260096 |
| stages[24].work.special:mask_decisions | 524288 |
| stages[24].operations[0].name | input_layernorm |
| stages[24].operations[0].matrix_flops | 0 |
| stages[24].operations[0].input_precision | unknown (null) |
| stages[24].operations[0].accumulator_precision | unknown (null) |
| stages[24].operations[0].sparsity | unknown (null) |
| stages[24].operations[0].scalar_flops | 2097280 |
| stages[24].operations[0].special_ops.rsqrt | 128 |
| stages[24].operations[0].source_detail.input[0] | 128 |
| stages[24].operations[0].source_detail.input[1] | 4096 |
| stages[24].operations[0].source_detail.weight[0] | 4096 |
| stages[24].operations[0].source_detail.output[0] | 128 |
| stages[24].operations[0].source_detail.output[1] | 4096 |
| stages[24].operations[1].name | q_proj |
| stages[24].operations[1].matrix_flops | 4294967296 |
| stages[24].operations[1].input_precision | BF16 |
| stages[24].operations[1].accumulator_precision | FP32 |
| stages[24].operations[1].sparsity | dense |
| stages[24].operations[1].scalar_flops | 0 |
| stages[24].operations[1].special_ops | {} |
| stages[24].operations[1].source_detail.input[0] | 128 |
| stages[24].operations[1].source_detail.input[1] | 4096 |
| stages[24].operations[1].source_detail.weight_math[0] | 4096 |
| stages[24].operations[1].source_detail.weight_math[1] | 4096 |
| stages[24].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[24].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[1].source_detail.output[0] | 128 |
| stages[24].operations[1].source_detail.output[1] | 4096 |
| stages[24].operations[2].name | k_proj |
| stages[24].operations[2].matrix_flops | 1073741824 |
| stages[24].operations[2].input_precision | BF16 |
| stages[24].operations[2].accumulator_precision | FP32 |
| stages[24].operations[2].sparsity | dense |
| stages[24].operations[2].scalar_flops | 0 |
| stages[24].operations[2].special_ops | {} |
| stages[24].operations[2].source_detail.input[0] | 128 |
| stages[24].operations[2].source_detail.input[1] | 4096 |
| stages[24].operations[2].source_detail.weight_math[0] | 4096 |
| stages[24].operations[2].source_detail.weight_math[1] | 1024 |
| stages[24].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[24].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[2].source_detail.output[0] | 128 |
| stages[24].operations[2].source_detail.output[1] | 1024 |
| stages[24].operations[3].name | v_proj |
| stages[24].operations[3].matrix_flops | 1073741824 |
| stages[24].operations[3].input_precision | BF16 |
| stages[24].operations[3].accumulator_precision | FP32 |
| stages[24].operations[3].sparsity | dense |
| stages[24].operations[3].scalar_flops | 0 |
| stages[24].operations[3].special_ops | {} |
| stages[24].operations[3].source_detail.input[0] | 128 |
| stages[24].operations[3].source_detail.input[1] | 4096 |
| stages[24].operations[3].source_detail.weight_math[0] | 4096 |
| stages[24].operations[3].source_detail.weight_math[1] | 1024 |
| stages[24].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[24].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[3].source_detail.output[0] | 128 |
| stages[24].operations[3].source_detail.output[1] | 1024 |
| stages[24].operations[4].name | q_norm |
| stages[24].operations[4].matrix_flops | 0 |
| stages[24].operations[4].input_precision | unknown (null) |
| stages[24].operations[4].accumulator_precision | unknown (null) |
| stages[24].operations[4].sparsity | unknown (null) |
| stages[24].operations[4].scalar_flops | 2101248 |
| stages[24].operations[4].special_ops.rsqrt | 4096 |
| stages[24].operations[4].source_detail.input[0] | 4096 |
| stages[24].operations[4].source_detail.input[1] | 128 |
| stages[24].operations[4].source_detail.weight[0] | 128 |
| stages[24].operations[4].source_detail.output[0] | 4096 |
| stages[24].operations[4].source_detail.output[1] | 128 |
| stages[24].operations[5].name | k_norm |
| stages[24].operations[5].matrix_flops | 0 |
| stages[24].operations[5].input_precision | unknown (null) |
| stages[24].operations[5].accumulator_precision | unknown (null) |
| stages[24].operations[5].sparsity | unknown (null) |
| stages[24].operations[5].scalar_flops | 525312 |
| stages[24].operations[5].special_ops.rsqrt | 1024 |
| stages[24].operations[5].source_detail.input[0] | 1024 |
| stages[24].operations[5].source_detail.input[1] | 128 |
| stages[24].operations[5].source_detail.weight[0] | 128 |
| stages[24].operations[5].source_detail.output[0] | 1024 |
| stages[24].operations[5].source_detail.output[1] | 128 |
| stages[24].operations[6].name | apply_rope |
| stages[24].operations[6].matrix_flops | 0 |
| stages[24].operations[6].input_precision | unknown (null) |
| stages[24].operations[6].accumulator_precision | unknown (null) |
| stages[24].operations[6].sparsity | unknown (null) |
| stages[24].operations[6].scalar_flops | 1966080 |
| stages[24].operations[6].special_ops.negate | 327680 |
| stages[24].operations[6].source_detail.Q[0] | 1 |
| stages[24].operations[6].source_detail.Q[1] | 32 |
| stages[24].operations[6].source_detail.Q[2] | 128 |
| stages[24].operations[6].source_detail.Q[3] | 128 |
| stages[24].operations[6].source_detail.K[0] | 1 |
| stages[24].operations[6].source_detail.K[1] | 8 |
| stages[24].operations[6].source_detail.K[2] | 128 |
| stages[24].operations[6].source_detail.K[3] | 128 |
| stages[24].operations[7].name | kv_append |
| stages[24].operations[7].matrix_flops | 0 |
| stages[24].operations[7].input_precision | unknown (null) |
| stages[24].operations[7].accumulator_precision | unknown (null) |
| stages[24].operations[7].sparsity | unknown (null) |
| stages[24].operations[7].scalar_flops | 0 |
| stages[24].operations[7].special_ops | {} |
| stages[24].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[24].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[24].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[24].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[24].operations[8].name | qk |
| stages[24].operations[8].matrix_flops | 67633152 |
| stages[24].operations[8].input_precision | BF16 |
| stages[24].operations[8].accumulator_precision | FP32 |
| stages[24].operations[8].sparsity | dense |
| stages[24].operations[8].scalar_flops | 0 |
| stages[24].operations[8].special_ops | {} |
| stages[24].operations[8].source_detail.Q[0] | 1 |
| stages[24].operations[8].source_detail.Q[1] | 32 |
| stages[24].operations[8].source_detail.Q[2] | 128 |
| stages[24].operations[8].source_detail.Q[3] | 128 |
| stages[24].operations[8].source_detail.K_shared[0] | 1 |
| stages[24].operations[8].source_detail.K_shared[1] | 8 |
| stages[24].operations[8].source_detail.K_shared[2] | 128 |
| stages[24].operations[8].source_detail.K_shared[3] | 128 |
| stages[24].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[24].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[24].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[24].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[24].operations[9].name | score_scale_mask_softmax |
| stages[24].operations[9].matrix_flops | 0 |
| stages[24].operations[9].input_precision | unknown (null) |
| stages[24].operations[9].accumulator_precision | unknown (null) |
| stages[24].operations[9].sparsity | unknown (null) |
| stages[24].operations[9].scalar_flops | 1052672 |
| stages[24].operations[9].special_ops.exp | 264192 |
| stages[24].operations[9].special_ops.compare_max | 260096 |
| stages[24].operations[9].special_ops.mask_decisions | 524288 |
| stages[24].operations[9].source_detail.scores[0] | 1 |
| stages[24].operations[9].source_detail.scores[1] | 32 |
| stages[24].operations[9].source_detail.scores[2] | 128 |
| stages[24].operations[9].source_detail.scores[3] | 128 |
| stages[24].operations[10].name | pv |
| stages[24].operations[10].matrix_flops | 67633152 |
| stages[24].operations[10].input_precision | BF16 |
| stages[24].operations[10].accumulator_precision | FP32 |
| stages[24].operations[10].sparsity | dense |
| stages[24].operations[10].scalar_flops | 0 |
| stages[24].operations[10].special_ops | {} |
| stages[24].operations[10].source_detail.P[0] | 1 |
| stages[24].operations[10].source_detail.P[1] | 32 |
| stages[24].operations[10].source_detail.P[2] | 128 |
| stages[24].operations[10].source_detail.P[3] | 128 |
| stages[24].operations[10].source_detail.V_shared[0] | 1 |
| stages[24].operations[10].source_detail.V_shared[1] | 8 |
| stages[24].operations[10].source_detail.V_shared[2] | 128 |
| stages[24].operations[10].source_detail.V_shared[3] | 128 |
| stages[24].operations[10].source_detail.output[0] | 1 |
| stages[24].operations[10].source_detail.output[1] | 32 |
| stages[24].operations[10].source_detail.output[2] | 128 |
| stages[24].operations[10].source_detail.output[3] | 128 |
| stages[24].operations[11].name | o_proj |
| stages[24].operations[11].matrix_flops | 4294967296 |
| stages[24].operations[11].input_precision | BF16 |
| stages[24].operations[11].accumulator_precision | FP32 |
| stages[24].operations[11].sparsity | dense |
| stages[24].operations[11].scalar_flops | 0 |
| stages[24].operations[11].special_ops | {} |
| stages[24].operations[11].source_detail.input[0] | 128 |
| stages[24].operations[11].source_detail.input[1] | 4096 |
| stages[24].operations[11].source_detail.weight_math[0] | 4096 |
| stages[24].operations[11].source_detail.weight_math[1] | 4096 |
| stages[24].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[24].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[11].source_detail.output[0] | 128 |
| stages[24].operations[11].source_detail.output[1] | 4096 |
| stages[24].operations[12].name | attention_residual |
| stages[24].operations[12].matrix_flops | 0 |
| stages[24].operations[12].input_precision | unknown (null) |
| stages[24].operations[12].accumulator_precision | unknown (null) |
| stages[24].operations[12].sparsity | unknown (null) |
| stages[24].operations[12].scalar_flops | 524288 |
| stages[24].operations[12].special_ops | {} |
| stages[24].operations[12].source_detail.inputs_each[0] | 128 |
| stages[24].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[24].operations[12].source_detail.output[0] | 128 |
| stages[24].operations[12].source_detail.output[1] | 4096 |
| stages[24].operations[13].name | post_attention_layernorm |
| stages[24].operations[13].matrix_flops | 0 |
| stages[24].operations[13].input_precision | unknown (null) |
| stages[24].operations[13].accumulator_precision | unknown (null) |
| stages[24].operations[13].sparsity | unknown (null) |
| stages[24].operations[13].scalar_flops | 2097280 |
| stages[24].operations[13].special_ops.rsqrt | 128 |
| stages[24].operations[13].source_detail.input[0] | 128 |
| stages[24].operations[13].source_detail.input[1] | 4096 |
| stages[24].operations[13].source_detail.weight[0] | 4096 |
| stages[24].operations[13].source_detail.output[0] | 128 |
| stages[24].operations[13].source_detail.output[1] | 4096 |
| stages[24].operations[14].name | gate_proj |
| stages[24].operations[14].matrix_flops | 12884901888 |
| stages[24].operations[14].input_precision | BF16 |
| stages[24].operations[14].accumulator_precision | FP32 |
| stages[24].operations[14].sparsity | dense |
| stages[24].operations[14].scalar_flops | 0 |
| stages[24].operations[14].special_ops | {} |
| stages[24].operations[14].source_detail.input[0] | 128 |
| stages[24].operations[14].source_detail.input[1] | 4096 |
| stages[24].operations[14].source_detail.weight_math[0] | 4096 |
| stages[24].operations[14].source_detail.weight_math[1] | 12288 |
| stages[24].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[24].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[14].source_detail.output[0] | 128 |
| stages[24].operations[14].source_detail.output[1] | 12288 |
| stages[24].operations[15].name | up_proj |
| stages[24].operations[15].matrix_flops | 12884901888 |
| stages[24].operations[15].input_precision | BF16 |
| stages[24].operations[15].accumulator_precision | FP32 |
| stages[24].operations[15].sparsity | dense |
| stages[24].operations[15].scalar_flops | 0 |
| stages[24].operations[15].special_ops | {} |
| stages[24].operations[15].source_detail.input[0] | 128 |
| stages[24].operations[15].source_detail.input[1] | 4096 |
| stages[24].operations[15].source_detail.weight_math[0] | 4096 |
| stages[24].operations[15].source_detail.weight_math[1] | 12288 |
| stages[24].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[24].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[24].operations[15].source_detail.output[0] | 128 |
| stages[24].operations[15].source_detail.output[1] | 12288 |
| stages[24].operations[16].name | silu_mul |
| stages[24].operations[16].matrix_flops | 0 |
| stages[24].operations[16].input_precision | unknown (null) |
| stages[24].operations[16].accumulator_precision | unknown (null) |
| stages[24].operations[16].sparsity | unknown (null) |
| stages[24].operations[16].scalar_flops | 6291456 |
| stages[24].operations[16].special_ops.exp | 1572864 |
| stages[24].operations[16].special_ops.negate | 1572864 |
| stages[24].operations[16].source_detail.gate[0] | 128 |
| stages[24].operations[16].source_detail.gate[1] | 12288 |
| stages[24].operations[16].source_detail.up[0] | 128 |
| stages[24].operations[16].source_detail.up[1] | 12288 |
| stages[24].operations[16].source_detail.output[0] | 128 |
| stages[24].operations[16].source_detail.output[1] | 12288 |
| stages[24].operations[17].name | down_proj |
| stages[24].operations[17].matrix_flops | 12884901888 |
| stages[24].operations[17].input_precision | BF16 |
| stages[24].operations[17].accumulator_precision | FP32 |
| stages[24].operations[17].sparsity | dense |
| stages[24].operations[17].scalar_flops | 0 |
| stages[24].operations[17].special_ops | {} |
| stages[24].operations[17].source_detail.input[0] | 128 |
| stages[24].operations[17].source_detail.input[1] | 12288 |
| stages[24].operations[17].source_detail.weight_math[0] | 12288 |
| stages[24].operations[17].source_detail.weight_math[1] | 4096 |
| stages[24].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[24].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[24].operations[17].source_detail.output[0] | 128 |
| stages[24].operations[17].source_detail.output[1] | 4096 |
| stages[24].operations[18].name | ffn_residual |
| stages[24].operations[18].matrix_flops | 0 |
| stages[24].operations[18].input_precision | unknown (null) |
| stages[24].operations[18].accumulator_precision | unknown (null) |
| stages[24].operations[18].sparsity | unknown (null) |
| stages[24].operations[18].scalar_flops | 524288 |
| stages[24].operations[18].special_ops | {} |
| stages[24].operations[18].source_detail.inputs_each[0] | 128 |
| stages[24].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[24].operations[18].source_detail.output[0] | 128 |
| stages[24].operations[18].source_detail.output[1] | 4096 |
| stages[25].id | layer:24 |
| stages[25].work.vector_fp32 | 17179904 |
| stages[25].work.special:rsqrt | 5376 |
| stages[25].work.interface_bytes | 438387200 |
| stages[25].work.matrix_bf16 | 49527390208 |
| stages[25].work.special:negate | 1900544 |
| stages[25].work.special:exp | 1837056 |
| stages[25].work.special:compare_max | 260096 |
| stages[25].work.special:mask_decisions | 524288 |
| stages[25].operations[0].name | input_layernorm |
| stages[25].operations[0].matrix_flops | 0 |
| stages[25].operations[0].input_precision | unknown (null) |
| stages[25].operations[0].accumulator_precision | unknown (null) |
| stages[25].operations[0].sparsity | unknown (null) |
| stages[25].operations[0].scalar_flops | 2097280 |
| stages[25].operations[0].special_ops.rsqrt | 128 |
| stages[25].operations[0].source_detail.input[0] | 128 |
| stages[25].operations[0].source_detail.input[1] | 4096 |
| stages[25].operations[0].source_detail.weight[0] | 4096 |
| stages[25].operations[0].source_detail.output[0] | 128 |
| stages[25].operations[0].source_detail.output[1] | 4096 |
| stages[25].operations[1].name | q_proj |
| stages[25].operations[1].matrix_flops | 4294967296 |
| stages[25].operations[1].input_precision | BF16 |
| stages[25].operations[1].accumulator_precision | FP32 |
| stages[25].operations[1].sparsity | dense |
| stages[25].operations[1].scalar_flops | 0 |
| stages[25].operations[1].special_ops | {} |
| stages[25].operations[1].source_detail.input[0] | 128 |
| stages[25].operations[1].source_detail.input[1] | 4096 |
| stages[25].operations[1].source_detail.weight_math[0] | 4096 |
| stages[25].operations[1].source_detail.weight_math[1] | 4096 |
| stages[25].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[25].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[1].source_detail.output[0] | 128 |
| stages[25].operations[1].source_detail.output[1] | 4096 |
| stages[25].operations[2].name | k_proj |
| stages[25].operations[2].matrix_flops | 1073741824 |
| stages[25].operations[2].input_precision | BF16 |
| stages[25].operations[2].accumulator_precision | FP32 |
| stages[25].operations[2].sparsity | dense |
| stages[25].operations[2].scalar_flops | 0 |
| stages[25].operations[2].special_ops | {} |
| stages[25].operations[2].source_detail.input[0] | 128 |
| stages[25].operations[2].source_detail.input[1] | 4096 |
| stages[25].operations[2].source_detail.weight_math[0] | 4096 |
| stages[25].operations[2].source_detail.weight_math[1] | 1024 |
| stages[25].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[25].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[2].source_detail.output[0] | 128 |
| stages[25].operations[2].source_detail.output[1] | 1024 |
| stages[25].operations[3].name | v_proj |
| stages[25].operations[3].matrix_flops | 1073741824 |
| stages[25].operations[3].input_precision | BF16 |
| stages[25].operations[3].accumulator_precision | FP32 |
| stages[25].operations[3].sparsity | dense |
| stages[25].operations[3].scalar_flops | 0 |
| stages[25].operations[3].special_ops | {} |
| stages[25].operations[3].source_detail.input[0] | 128 |
| stages[25].operations[3].source_detail.input[1] | 4096 |
| stages[25].operations[3].source_detail.weight_math[0] | 4096 |
| stages[25].operations[3].source_detail.weight_math[1] | 1024 |
| stages[25].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[25].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[3].source_detail.output[0] | 128 |
| stages[25].operations[3].source_detail.output[1] | 1024 |
| stages[25].operations[4].name | q_norm |
| stages[25].operations[4].matrix_flops | 0 |
| stages[25].operations[4].input_precision | unknown (null) |
| stages[25].operations[4].accumulator_precision | unknown (null) |
| stages[25].operations[4].sparsity | unknown (null) |
| stages[25].operations[4].scalar_flops | 2101248 |
| stages[25].operations[4].special_ops.rsqrt | 4096 |
| stages[25].operations[4].source_detail.input[0] | 4096 |
| stages[25].operations[4].source_detail.input[1] | 128 |
| stages[25].operations[4].source_detail.weight[0] | 128 |
| stages[25].operations[4].source_detail.output[0] | 4096 |
| stages[25].operations[4].source_detail.output[1] | 128 |
| stages[25].operations[5].name | k_norm |
| stages[25].operations[5].matrix_flops | 0 |
| stages[25].operations[5].input_precision | unknown (null) |
| stages[25].operations[5].accumulator_precision | unknown (null) |
| stages[25].operations[5].sparsity | unknown (null) |
| stages[25].operations[5].scalar_flops | 525312 |
| stages[25].operations[5].special_ops.rsqrt | 1024 |
| stages[25].operations[5].source_detail.input[0] | 1024 |
| stages[25].operations[5].source_detail.input[1] | 128 |
| stages[25].operations[5].source_detail.weight[0] | 128 |
| stages[25].operations[5].source_detail.output[0] | 1024 |
| stages[25].operations[5].source_detail.output[1] | 128 |
| stages[25].operations[6].name | apply_rope |
| stages[25].operations[6].matrix_flops | 0 |
| stages[25].operations[6].input_precision | unknown (null) |
| stages[25].operations[6].accumulator_precision | unknown (null) |
| stages[25].operations[6].sparsity | unknown (null) |
| stages[25].operations[6].scalar_flops | 1966080 |
| stages[25].operations[6].special_ops.negate | 327680 |
| stages[25].operations[6].source_detail.Q[0] | 1 |
| stages[25].operations[6].source_detail.Q[1] | 32 |
| stages[25].operations[6].source_detail.Q[2] | 128 |
| stages[25].operations[6].source_detail.Q[3] | 128 |
| stages[25].operations[6].source_detail.K[0] | 1 |
| stages[25].operations[6].source_detail.K[1] | 8 |
| stages[25].operations[6].source_detail.K[2] | 128 |
| stages[25].operations[6].source_detail.K[3] | 128 |
| stages[25].operations[7].name | kv_append |
| stages[25].operations[7].matrix_flops | 0 |
| stages[25].operations[7].input_precision | unknown (null) |
| stages[25].operations[7].accumulator_precision | unknown (null) |
| stages[25].operations[7].sparsity | unknown (null) |
| stages[25].operations[7].scalar_flops | 0 |
| stages[25].operations[7].special_ops | {} |
| stages[25].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[25].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[25].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[25].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[25].operations[8].name | qk |
| stages[25].operations[8].matrix_flops | 67633152 |
| stages[25].operations[8].input_precision | BF16 |
| stages[25].operations[8].accumulator_precision | FP32 |
| stages[25].operations[8].sparsity | dense |
| stages[25].operations[8].scalar_flops | 0 |
| stages[25].operations[8].special_ops | {} |
| stages[25].operations[8].source_detail.Q[0] | 1 |
| stages[25].operations[8].source_detail.Q[1] | 32 |
| stages[25].operations[8].source_detail.Q[2] | 128 |
| stages[25].operations[8].source_detail.Q[3] | 128 |
| stages[25].operations[8].source_detail.K_shared[0] | 1 |
| stages[25].operations[8].source_detail.K_shared[1] | 8 |
| stages[25].operations[8].source_detail.K_shared[2] | 128 |
| stages[25].operations[8].source_detail.K_shared[3] | 128 |
| stages[25].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[25].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[25].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[25].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[25].operations[9].name | score_scale_mask_softmax |
| stages[25].operations[9].matrix_flops | 0 |
| stages[25].operations[9].input_precision | unknown (null) |
| stages[25].operations[9].accumulator_precision | unknown (null) |
| stages[25].operations[9].sparsity | unknown (null) |
| stages[25].operations[9].scalar_flops | 1052672 |
| stages[25].operations[9].special_ops.exp | 264192 |
| stages[25].operations[9].special_ops.compare_max | 260096 |
| stages[25].operations[9].special_ops.mask_decisions | 524288 |
| stages[25].operations[9].source_detail.scores[0] | 1 |
| stages[25].operations[9].source_detail.scores[1] | 32 |
| stages[25].operations[9].source_detail.scores[2] | 128 |
| stages[25].operations[9].source_detail.scores[3] | 128 |
| stages[25].operations[10].name | pv |
| stages[25].operations[10].matrix_flops | 67633152 |
| stages[25].operations[10].input_precision | BF16 |
| stages[25].operations[10].accumulator_precision | FP32 |
| stages[25].operations[10].sparsity | dense |
| stages[25].operations[10].scalar_flops | 0 |
| stages[25].operations[10].special_ops | {} |
| stages[25].operations[10].source_detail.P[0] | 1 |
| stages[25].operations[10].source_detail.P[1] | 32 |
| stages[25].operations[10].source_detail.P[2] | 128 |
| stages[25].operations[10].source_detail.P[3] | 128 |
| stages[25].operations[10].source_detail.V_shared[0] | 1 |
| stages[25].operations[10].source_detail.V_shared[1] | 8 |
| stages[25].operations[10].source_detail.V_shared[2] | 128 |
| stages[25].operations[10].source_detail.V_shared[3] | 128 |
| stages[25].operations[10].source_detail.output[0] | 1 |
| stages[25].operations[10].source_detail.output[1] | 32 |
| stages[25].operations[10].source_detail.output[2] | 128 |
| stages[25].operations[10].source_detail.output[3] | 128 |
| stages[25].operations[11].name | o_proj |
| stages[25].operations[11].matrix_flops | 4294967296 |
| stages[25].operations[11].input_precision | BF16 |
| stages[25].operations[11].accumulator_precision | FP32 |
| stages[25].operations[11].sparsity | dense |
| stages[25].operations[11].scalar_flops | 0 |
| stages[25].operations[11].special_ops | {} |
| stages[25].operations[11].source_detail.input[0] | 128 |
| stages[25].operations[11].source_detail.input[1] | 4096 |
| stages[25].operations[11].source_detail.weight_math[0] | 4096 |
| stages[25].operations[11].source_detail.weight_math[1] | 4096 |
| stages[25].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[25].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[11].source_detail.output[0] | 128 |
| stages[25].operations[11].source_detail.output[1] | 4096 |
| stages[25].operations[12].name | attention_residual |
| stages[25].operations[12].matrix_flops | 0 |
| stages[25].operations[12].input_precision | unknown (null) |
| stages[25].operations[12].accumulator_precision | unknown (null) |
| stages[25].operations[12].sparsity | unknown (null) |
| stages[25].operations[12].scalar_flops | 524288 |
| stages[25].operations[12].special_ops | {} |
| stages[25].operations[12].source_detail.inputs_each[0] | 128 |
| stages[25].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[25].operations[12].source_detail.output[0] | 128 |
| stages[25].operations[12].source_detail.output[1] | 4096 |
| stages[25].operations[13].name | post_attention_layernorm |
| stages[25].operations[13].matrix_flops | 0 |
| stages[25].operations[13].input_precision | unknown (null) |
| stages[25].operations[13].accumulator_precision | unknown (null) |
| stages[25].operations[13].sparsity | unknown (null) |
| stages[25].operations[13].scalar_flops | 2097280 |
| stages[25].operations[13].special_ops.rsqrt | 128 |
| stages[25].operations[13].source_detail.input[0] | 128 |
| stages[25].operations[13].source_detail.input[1] | 4096 |
| stages[25].operations[13].source_detail.weight[0] | 4096 |
| stages[25].operations[13].source_detail.output[0] | 128 |
| stages[25].operations[13].source_detail.output[1] | 4096 |
| stages[25].operations[14].name | gate_proj |
| stages[25].operations[14].matrix_flops | 12884901888 |
| stages[25].operations[14].input_precision | BF16 |
| stages[25].operations[14].accumulator_precision | FP32 |
| stages[25].operations[14].sparsity | dense |
| stages[25].operations[14].scalar_flops | 0 |
| stages[25].operations[14].special_ops | {} |
| stages[25].operations[14].source_detail.input[0] | 128 |
| stages[25].operations[14].source_detail.input[1] | 4096 |
| stages[25].operations[14].source_detail.weight_math[0] | 4096 |
| stages[25].operations[14].source_detail.weight_math[1] | 12288 |
| stages[25].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[25].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[14].source_detail.output[0] | 128 |
| stages[25].operations[14].source_detail.output[1] | 12288 |
| stages[25].operations[15].name | up_proj |
| stages[25].operations[15].matrix_flops | 12884901888 |
| stages[25].operations[15].input_precision | BF16 |
| stages[25].operations[15].accumulator_precision | FP32 |
| stages[25].operations[15].sparsity | dense |
| stages[25].operations[15].scalar_flops | 0 |
| stages[25].operations[15].special_ops | {} |
| stages[25].operations[15].source_detail.input[0] | 128 |
| stages[25].operations[15].source_detail.input[1] | 4096 |
| stages[25].operations[15].source_detail.weight_math[0] | 4096 |
| stages[25].operations[15].source_detail.weight_math[1] | 12288 |
| stages[25].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[25].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[25].operations[15].source_detail.output[0] | 128 |
| stages[25].operations[15].source_detail.output[1] | 12288 |
| stages[25].operations[16].name | silu_mul |
| stages[25].operations[16].matrix_flops | 0 |
| stages[25].operations[16].input_precision | unknown (null) |
| stages[25].operations[16].accumulator_precision | unknown (null) |
| stages[25].operations[16].sparsity | unknown (null) |
| stages[25].operations[16].scalar_flops | 6291456 |
| stages[25].operations[16].special_ops.exp | 1572864 |
| stages[25].operations[16].special_ops.negate | 1572864 |
| stages[25].operations[16].source_detail.gate[0] | 128 |
| stages[25].operations[16].source_detail.gate[1] | 12288 |
| stages[25].operations[16].source_detail.up[0] | 128 |
| stages[25].operations[16].source_detail.up[1] | 12288 |
| stages[25].operations[16].source_detail.output[0] | 128 |
| stages[25].operations[16].source_detail.output[1] | 12288 |
| stages[25].operations[17].name | down_proj |
| stages[25].operations[17].matrix_flops | 12884901888 |
| stages[25].operations[17].input_precision | BF16 |
| stages[25].operations[17].accumulator_precision | FP32 |
| stages[25].operations[17].sparsity | dense |
| stages[25].operations[17].scalar_flops | 0 |
| stages[25].operations[17].special_ops | {} |
| stages[25].operations[17].source_detail.input[0] | 128 |
| stages[25].operations[17].source_detail.input[1] | 12288 |
| stages[25].operations[17].source_detail.weight_math[0] | 12288 |
| stages[25].operations[17].source_detail.weight_math[1] | 4096 |
| stages[25].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[25].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[25].operations[17].source_detail.output[0] | 128 |
| stages[25].operations[17].source_detail.output[1] | 4096 |
| stages[25].operations[18].name | ffn_residual |
| stages[25].operations[18].matrix_flops | 0 |
| stages[25].operations[18].input_precision | unknown (null) |
| stages[25].operations[18].accumulator_precision | unknown (null) |
| stages[25].operations[18].sparsity | unknown (null) |
| stages[25].operations[18].scalar_flops | 524288 |
| stages[25].operations[18].special_ops | {} |
| stages[25].operations[18].source_detail.inputs_each[0] | 128 |
| stages[25].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[25].operations[18].source_detail.output[0] | 128 |
| stages[25].operations[18].source_detail.output[1] | 4096 |
| stages[26].id | layer:25 |
| stages[26].work.vector_fp32 | 17179904 |
| stages[26].work.special:rsqrt | 5376 |
| stages[26].work.interface_bytes | 438387200 |
| stages[26].work.matrix_bf16 | 49527390208 |
| stages[26].work.special:negate | 1900544 |
| stages[26].work.special:exp | 1837056 |
| stages[26].work.special:compare_max | 260096 |
| stages[26].work.special:mask_decisions | 524288 |
| stages[26].operations[0].name | input_layernorm |
| stages[26].operations[0].matrix_flops | 0 |
| stages[26].operations[0].input_precision | unknown (null) |
| stages[26].operations[0].accumulator_precision | unknown (null) |
| stages[26].operations[0].sparsity | unknown (null) |
| stages[26].operations[0].scalar_flops | 2097280 |
| stages[26].operations[0].special_ops.rsqrt | 128 |
| stages[26].operations[0].source_detail.input[0] | 128 |
| stages[26].operations[0].source_detail.input[1] | 4096 |
| stages[26].operations[0].source_detail.weight[0] | 4096 |
| stages[26].operations[0].source_detail.output[0] | 128 |
| stages[26].operations[0].source_detail.output[1] | 4096 |
| stages[26].operations[1].name | q_proj |
| stages[26].operations[1].matrix_flops | 4294967296 |
| stages[26].operations[1].input_precision | BF16 |
| stages[26].operations[1].accumulator_precision | FP32 |
| stages[26].operations[1].sparsity | dense |
| stages[26].operations[1].scalar_flops | 0 |
| stages[26].operations[1].special_ops | {} |
| stages[26].operations[1].source_detail.input[0] | 128 |
| stages[26].operations[1].source_detail.input[1] | 4096 |
| stages[26].operations[1].source_detail.weight_math[0] | 4096 |
| stages[26].operations[1].source_detail.weight_math[1] | 4096 |
| stages[26].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[26].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[1].source_detail.output[0] | 128 |
| stages[26].operations[1].source_detail.output[1] | 4096 |
| stages[26].operations[2].name | k_proj |
| stages[26].operations[2].matrix_flops | 1073741824 |
| stages[26].operations[2].input_precision | BF16 |
| stages[26].operations[2].accumulator_precision | FP32 |
| stages[26].operations[2].sparsity | dense |
| stages[26].operations[2].scalar_flops | 0 |
| stages[26].operations[2].special_ops | {} |
| stages[26].operations[2].source_detail.input[0] | 128 |
| stages[26].operations[2].source_detail.input[1] | 4096 |
| stages[26].operations[2].source_detail.weight_math[0] | 4096 |
| stages[26].operations[2].source_detail.weight_math[1] | 1024 |
| stages[26].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[26].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[2].source_detail.output[0] | 128 |
| stages[26].operations[2].source_detail.output[1] | 1024 |
| stages[26].operations[3].name | v_proj |
| stages[26].operations[3].matrix_flops | 1073741824 |
| stages[26].operations[3].input_precision | BF16 |
| stages[26].operations[3].accumulator_precision | FP32 |
| stages[26].operations[3].sparsity | dense |
| stages[26].operations[3].scalar_flops | 0 |
| stages[26].operations[3].special_ops | {} |
| stages[26].operations[3].source_detail.input[0] | 128 |
| stages[26].operations[3].source_detail.input[1] | 4096 |
| stages[26].operations[3].source_detail.weight_math[0] | 4096 |
| stages[26].operations[3].source_detail.weight_math[1] | 1024 |
| stages[26].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[26].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[3].source_detail.output[0] | 128 |
| stages[26].operations[3].source_detail.output[1] | 1024 |
| stages[26].operations[4].name | q_norm |
| stages[26].operations[4].matrix_flops | 0 |
| stages[26].operations[4].input_precision | unknown (null) |
| stages[26].operations[4].accumulator_precision | unknown (null) |
| stages[26].operations[4].sparsity | unknown (null) |
| stages[26].operations[4].scalar_flops | 2101248 |
| stages[26].operations[4].special_ops.rsqrt | 4096 |
| stages[26].operations[4].source_detail.input[0] | 4096 |
| stages[26].operations[4].source_detail.input[1] | 128 |
| stages[26].operations[4].source_detail.weight[0] | 128 |
| stages[26].operations[4].source_detail.output[0] | 4096 |
| stages[26].operations[4].source_detail.output[1] | 128 |
| stages[26].operations[5].name | k_norm |
| stages[26].operations[5].matrix_flops | 0 |
| stages[26].operations[5].input_precision | unknown (null) |
| stages[26].operations[5].accumulator_precision | unknown (null) |
| stages[26].operations[5].sparsity | unknown (null) |
| stages[26].operations[5].scalar_flops | 525312 |
| stages[26].operations[5].special_ops.rsqrt | 1024 |
| stages[26].operations[5].source_detail.input[0] | 1024 |
| stages[26].operations[5].source_detail.input[1] | 128 |
| stages[26].operations[5].source_detail.weight[0] | 128 |
| stages[26].operations[5].source_detail.output[0] | 1024 |
| stages[26].operations[5].source_detail.output[1] | 128 |
| stages[26].operations[6].name | apply_rope |
| stages[26].operations[6].matrix_flops | 0 |
| stages[26].operations[6].input_precision | unknown (null) |
| stages[26].operations[6].accumulator_precision | unknown (null) |
| stages[26].operations[6].sparsity | unknown (null) |
| stages[26].operations[6].scalar_flops | 1966080 |
| stages[26].operations[6].special_ops.negate | 327680 |
| stages[26].operations[6].source_detail.Q[0] | 1 |
| stages[26].operations[6].source_detail.Q[1] | 32 |
| stages[26].operations[6].source_detail.Q[2] | 128 |
| stages[26].operations[6].source_detail.Q[3] | 128 |
| stages[26].operations[6].source_detail.K[0] | 1 |
| stages[26].operations[6].source_detail.K[1] | 8 |
| stages[26].operations[6].source_detail.K[2] | 128 |
| stages[26].operations[6].source_detail.K[3] | 128 |
| stages[26].operations[7].name | kv_append |
| stages[26].operations[7].matrix_flops | 0 |
| stages[26].operations[7].input_precision | unknown (null) |
| stages[26].operations[7].accumulator_precision | unknown (null) |
| stages[26].operations[7].sparsity | unknown (null) |
| stages[26].operations[7].scalar_flops | 0 |
| stages[26].operations[7].special_ops | {} |
| stages[26].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[26].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[26].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[26].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[26].operations[8].name | qk |
| stages[26].operations[8].matrix_flops | 67633152 |
| stages[26].operations[8].input_precision | BF16 |
| stages[26].operations[8].accumulator_precision | FP32 |
| stages[26].operations[8].sparsity | dense |
| stages[26].operations[8].scalar_flops | 0 |
| stages[26].operations[8].special_ops | {} |
| stages[26].operations[8].source_detail.Q[0] | 1 |
| stages[26].operations[8].source_detail.Q[1] | 32 |
| stages[26].operations[8].source_detail.Q[2] | 128 |
| stages[26].operations[8].source_detail.Q[3] | 128 |
| stages[26].operations[8].source_detail.K_shared[0] | 1 |
| stages[26].operations[8].source_detail.K_shared[1] | 8 |
| stages[26].operations[8].source_detail.K_shared[2] | 128 |
| stages[26].operations[8].source_detail.K_shared[3] | 128 |
| stages[26].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[26].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[26].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[26].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[26].operations[9].name | score_scale_mask_softmax |
| stages[26].operations[9].matrix_flops | 0 |
| stages[26].operations[9].input_precision | unknown (null) |
| stages[26].operations[9].accumulator_precision | unknown (null) |
| stages[26].operations[9].sparsity | unknown (null) |
| stages[26].operations[9].scalar_flops | 1052672 |
| stages[26].operations[9].special_ops.exp | 264192 |
| stages[26].operations[9].special_ops.compare_max | 260096 |
| stages[26].operations[9].special_ops.mask_decisions | 524288 |
| stages[26].operations[9].source_detail.scores[0] | 1 |
| stages[26].operations[9].source_detail.scores[1] | 32 |
| stages[26].operations[9].source_detail.scores[2] | 128 |
| stages[26].operations[9].source_detail.scores[3] | 128 |
| stages[26].operations[10].name | pv |
| stages[26].operations[10].matrix_flops | 67633152 |
| stages[26].operations[10].input_precision | BF16 |
| stages[26].operations[10].accumulator_precision | FP32 |
| stages[26].operations[10].sparsity | dense |
| stages[26].operations[10].scalar_flops | 0 |
| stages[26].operations[10].special_ops | {} |
| stages[26].operations[10].source_detail.P[0] | 1 |
| stages[26].operations[10].source_detail.P[1] | 32 |
| stages[26].operations[10].source_detail.P[2] | 128 |
| stages[26].operations[10].source_detail.P[3] | 128 |
| stages[26].operations[10].source_detail.V_shared[0] | 1 |
| stages[26].operations[10].source_detail.V_shared[1] | 8 |
| stages[26].operations[10].source_detail.V_shared[2] | 128 |
| stages[26].operations[10].source_detail.V_shared[3] | 128 |
| stages[26].operations[10].source_detail.output[0] | 1 |
| stages[26].operations[10].source_detail.output[1] | 32 |
| stages[26].operations[10].source_detail.output[2] | 128 |
| stages[26].operations[10].source_detail.output[3] | 128 |
| stages[26].operations[11].name | o_proj |
| stages[26].operations[11].matrix_flops | 4294967296 |
| stages[26].operations[11].input_precision | BF16 |
| stages[26].operations[11].accumulator_precision | FP32 |
| stages[26].operations[11].sparsity | dense |
| stages[26].operations[11].scalar_flops | 0 |
| stages[26].operations[11].special_ops | {} |
| stages[26].operations[11].source_detail.input[0] | 128 |
| stages[26].operations[11].source_detail.input[1] | 4096 |
| stages[26].operations[11].source_detail.weight_math[0] | 4096 |
| stages[26].operations[11].source_detail.weight_math[1] | 4096 |
| stages[26].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[26].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[11].source_detail.output[0] | 128 |
| stages[26].operations[11].source_detail.output[1] | 4096 |
| stages[26].operations[12].name | attention_residual |
| stages[26].operations[12].matrix_flops | 0 |
| stages[26].operations[12].input_precision | unknown (null) |
| stages[26].operations[12].accumulator_precision | unknown (null) |
| stages[26].operations[12].sparsity | unknown (null) |
| stages[26].operations[12].scalar_flops | 524288 |
| stages[26].operations[12].special_ops | {} |
| stages[26].operations[12].source_detail.inputs_each[0] | 128 |
| stages[26].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[26].operations[12].source_detail.output[0] | 128 |
| stages[26].operations[12].source_detail.output[1] | 4096 |
| stages[26].operations[13].name | post_attention_layernorm |
| stages[26].operations[13].matrix_flops | 0 |
| stages[26].operations[13].input_precision | unknown (null) |
| stages[26].operations[13].accumulator_precision | unknown (null) |
| stages[26].operations[13].sparsity | unknown (null) |
| stages[26].operations[13].scalar_flops | 2097280 |
| stages[26].operations[13].special_ops.rsqrt | 128 |
| stages[26].operations[13].source_detail.input[0] | 128 |
| stages[26].operations[13].source_detail.input[1] | 4096 |
| stages[26].operations[13].source_detail.weight[0] | 4096 |
| stages[26].operations[13].source_detail.output[0] | 128 |
| stages[26].operations[13].source_detail.output[1] | 4096 |
| stages[26].operations[14].name | gate_proj |
| stages[26].operations[14].matrix_flops | 12884901888 |
| stages[26].operations[14].input_precision | BF16 |
| stages[26].operations[14].accumulator_precision | FP32 |
| stages[26].operations[14].sparsity | dense |
| stages[26].operations[14].scalar_flops | 0 |
| stages[26].operations[14].special_ops | {} |
| stages[26].operations[14].source_detail.input[0] | 128 |
| stages[26].operations[14].source_detail.input[1] | 4096 |
| stages[26].operations[14].source_detail.weight_math[0] | 4096 |
| stages[26].operations[14].source_detail.weight_math[1] | 12288 |
| stages[26].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[26].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[14].source_detail.output[0] | 128 |
| stages[26].operations[14].source_detail.output[1] | 12288 |
| stages[26].operations[15].name | up_proj |
| stages[26].operations[15].matrix_flops | 12884901888 |
| stages[26].operations[15].input_precision | BF16 |
| stages[26].operations[15].accumulator_precision | FP32 |
| stages[26].operations[15].sparsity | dense |
| stages[26].operations[15].scalar_flops | 0 |
| stages[26].operations[15].special_ops | {} |
| stages[26].operations[15].source_detail.input[0] | 128 |
| stages[26].operations[15].source_detail.input[1] | 4096 |
| stages[26].operations[15].source_detail.weight_math[0] | 4096 |
| stages[26].operations[15].source_detail.weight_math[1] | 12288 |
| stages[26].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[26].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[26].operations[15].source_detail.output[0] | 128 |
| stages[26].operations[15].source_detail.output[1] | 12288 |
| stages[26].operations[16].name | silu_mul |
| stages[26].operations[16].matrix_flops | 0 |
| stages[26].operations[16].input_precision | unknown (null) |
| stages[26].operations[16].accumulator_precision | unknown (null) |
| stages[26].operations[16].sparsity | unknown (null) |
| stages[26].operations[16].scalar_flops | 6291456 |
| stages[26].operations[16].special_ops.exp | 1572864 |
| stages[26].operations[16].special_ops.negate | 1572864 |
| stages[26].operations[16].source_detail.gate[0] | 128 |
| stages[26].operations[16].source_detail.gate[1] | 12288 |
| stages[26].operations[16].source_detail.up[0] | 128 |
| stages[26].operations[16].source_detail.up[1] | 12288 |
| stages[26].operations[16].source_detail.output[0] | 128 |
| stages[26].operations[16].source_detail.output[1] | 12288 |
| stages[26].operations[17].name | down_proj |
| stages[26].operations[17].matrix_flops | 12884901888 |
| stages[26].operations[17].input_precision | BF16 |
| stages[26].operations[17].accumulator_precision | FP32 |
| stages[26].operations[17].sparsity | dense |
| stages[26].operations[17].scalar_flops | 0 |
| stages[26].operations[17].special_ops | {} |
| stages[26].operations[17].source_detail.input[0] | 128 |
| stages[26].operations[17].source_detail.input[1] | 12288 |
| stages[26].operations[17].source_detail.weight_math[0] | 12288 |
| stages[26].operations[17].source_detail.weight_math[1] | 4096 |
| stages[26].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[26].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[26].operations[17].source_detail.output[0] | 128 |
| stages[26].operations[17].source_detail.output[1] | 4096 |
| stages[26].operations[18].name | ffn_residual |
| stages[26].operations[18].matrix_flops | 0 |
| stages[26].operations[18].input_precision | unknown (null) |
| stages[26].operations[18].accumulator_precision | unknown (null) |
| stages[26].operations[18].sparsity | unknown (null) |
| stages[26].operations[18].scalar_flops | 524288 |
| stages[26].operations[18].special_ops | {} |
| stages[26].operations[18].source_detail.inputs_each[0] | 128 |
| stages[26].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[26].operations[18].source_detail.output[0] | 128 |
| stages[26].operations[18].source_detail.output[1] | 4096 |
| stages[27].id | layer:26 |
| stages[27].work.vector_fp32 | 17179904 |
| stages[27].work.special:rsqrt | 5376 |
| stages[27].work.interface_bytes | 438387200 |
| stages[27].work.matrix_bf16 | 49527390208 |
| stages[27].work.special:negate | 1900544 |
| stages[27].work.special:exp | 1837056 |
| stages[27].work.special:compare_max | 260096 |
| stages[27].work.special:mask_decisions | 524288 |
| stages[27].operations[0].name | input_layernorm |
| stages[27].operations[0].matrix_flops | 0 |
| stages[27].operations[0].input_precision | unknown (null) |
| stages[27].operations[0].accumulator_precision | unknown (null) |
| stages[27].operations[0].sparsity | unknown (null) |
| stages[27].operations[0].scalar_flops | 2097280 |
| stages[27].operations[0].special_ops.rsqrt | 128 |
| stages[27].operations[0].source_detail.input[0] | 128 |
| stages[27].operations[0].source_detail.input[1] | 4096 |
| stages[27].operations[0].source_detail.weight[0] | 4096 |
| stages[27].operations[0].source_detail.output[0] | 128 |
| stages[27].operations[0].source_detail.output[1] | 4096 |
| stages[27].operations[1].name | q_proj |
| stages[27].operations[1].matrix_flops | 4294967296 |
| stages[27].operations[1].input_precision | BF16 |
| stages[27].operations[1].accumulator_precision | FP32 |
| stages[27].operations[1].sparsity | dense |
| stages[27].operations[1].scalar_flops | 0 |
| stages[27].operations[1].special_ops | {} |
| stages[27].operations[1].source_detail.input[0] | 128 |
| stages[27].operations[1].source_detail.input[1] | 4096 |
| stages[27].operations[1].source_detail.weight_math[0] | 4096 |
| stages[27].operations[1].source_detail.weight_math[1] | 4096 |
| stages[27].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[27].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[1].source_detail.output[0] | 128 |
| stages[27].operations[1].source_detail.output[1] | 4096 |
| stages[27].operations[2].name | k_proj |
| stages[27].operations[2].matrix_flops | 1073741824 |
| stages[27].operations[2].input_precision | BF16 |
| stages[27].operations[2].accumulator_precision | FP32 |
| stages[27].operations[2].sparsity | dense |
| stages[27].operations[2].scalar_flops | 0 |
| stages[27].operations[2].special_ops | {} |
| stages[27].operations[2].source_detail.input[0] | 128 |
| stages[27].operations[2].source_detail.input[1] | 4096 |
| stages[27].operations[2].source_detail.weight_math[0] | 4096 |
| stages[27].operations[2].source_detail.weight_math[1] | 1024 |
| stages[27].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[27].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[2].source_detail.output[0] | 128 |
| stages[27].operations[2].source_detail.output[1] | 1024 |
| stages[27].operations[3].name | v_proj |
| stages[27].operations[3].matrix_flops | 1073741824 |
| stages[27].operations[3].input_precision | BF16 |
| stages[27].operations[3].accumulator_precision | FP32 |
| stages[27].operations[3].sparsity | dense |
| stages[27].operations[3].scalar_flops | 0 |
| stages[27].operations[3].special_ops | {} |
| stages[27].operations[3].source_detail.input[0] | 128 |
| stages[27].operations[3].source_detail.input[1] | 4096 |
| stages[27].operations[3].source_detail.weight_math[0] | 4096 |
| stages[27].operations[3].source_detail.weight_math[1] | 1024 |
| stages[27].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[27].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[3].source_detail.output[0] | 128 |
| stages[27].operations[3].source_detail.output[1] | 1024 |
| stages[27].operations[4].name | q_norm |
| stages[27].operations[4].matrix_flops | 0 |
| stages[27].operations[4].input_precision | unknown (null) |
| stages[27].operations[4].accumulator_precision | unknown (null) |
| stages[27].operations[4].sparsity | unknown (null) |
| stages[27].operations[4].scalar_flops | 2101248 |
| stages[27].operations[4].special_ops.rsqrt | 4096 |
| stages[27].operations[4].source_detail.input[0] | 4096 |
| stages[27].operations[4].source_detail.input[1] | 128 |
| stages[27].operations[4].source_detail.weight[0] | 128 |
| stages[27].operations[4].source_detail.output[0] | 4096 |
| stages[27].operations[4].source_detail.output[1] | 128 |
| stages[27].operations[5].name | k_norm |
| stages[27].operations[5].matrix_flops | 0 |
| stages[27].operations[5].input_precision | unknown (null) |
| stages[27].operations[5].accumulator_precision | unknown (null) |
| stages[27].operations[5].sparsity | unknown (null) |
| stages[27].operations[5].scalar_flops | 525312 |
| stages[27].operations[5].special_ops.rsqrt | 1024 |
| stages[27].operations[5].source_detail.input[0] | 1024 |
| stages[27].operations[5].source_detail.input[1] | 128 |
| stages[27].operations[5].source_detail.weight[0] | 128 |
| stages[27].operations[5].source_detail.output[0] | 1024 |
| stages[27].operations[5].source_detail.output[1] | 128 |
| stages[27].operations[6].name | apply_rope |
| stages[27].operations[6].matrix_flops | 0 |
| stages[27].operations[6].input_precision | unknown (null) |
| stages[27].operations[6].accumulator_precision | unknown (null) |
| stages[27].operations[6].sparsity | unknown (null) |
| stages[27].operations[6].scalar_flops | 1966080 |
| stages[27].operations[6].special_ops.negate | 327680 |
| stages[27].operations[6].source_detail.Q[0] | 1 |
| stages[27].operations[6].source_detail.Q[1] | 32 |
| stages[27].operations[6].source_detail.Q[2] | 128 |
| stages[27].operations[6].source_detail.Q[3] | 128 |
| stages[27].operations[6].source_detail.K[0] | 1 |
| stages[27].operations[6].source_detail.K[1] | 8 |
| stages[27].operations[6].source_detail.K[2] | 128 |
| stages[27].operations[6].source_detail.K[3] | 128 |
| stages[27].operations[7].name | kv_append |
| stages[27].operations[7].matrix_flops | 0 |
| stages[27].operations[7].input_precision | unknown (null) |
| stages[27].operations[7].accumulator_precision | unknown (null) |
| stages[27].operations[7].sparsity | unknown (null) |
| stages[27].operations[7].scalar_flops | 0 |
| stages[27].operations[7].special_ops | {} |
| stages[27].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[27].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[27].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[27].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[27].operations[8].name | qk |
| stages[27].operations[8].matrix_flops | 67633152 |
| stages[27].operations[8].input_precision | BF16 |
| stages[27].operations[8].accumulator_precision | FP32 |
| stages[27].operations[8].sparsity | dense |
| stages[27].operations[8].scalar_flops | 0 |
| stages[27].operations[8].special_ops | {} |
| stages[27].operations[8].source_detail.Q[0] | 1 |
| stages[27].operations[8].source_detail.Q[1] | 32 |
| stages[27].operations[8].source_detail.Q[2] | 128 |
| stages[27].operations[8].source_detail.Q[3] | 128 |
| stages[27].operations[8].source_detail.K_shared[0] | 1 |
| stages[27].operations[8].source_detail.K_shared[1] | 8 |
| stages[27].operations[8].source_detail.K_shared[2] | 128 |
| stages[27].operations[8].source_detail.K_shared[3] | 128 |
| stages[27].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[27].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[27].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[27].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[27].operations[9].name | score_scale_mask_softmax |
| stages[27].operations[9].matrix_flops | 0 |
| stages[27].operations[9].input_precision | unknown (null) |
| stages[27].operations[9].accumulator_precision | unknown (null) |
| stages[27].operations[9].sparsity | unknown (null) |
| stages[27].operations[9].scalar_flops | 1052672 |
| stages[27].operations[9].special_ops.exp | 264192 |
| stages[27].operations[9].special_ops.compare_max | 260096 |
| stages[27].operations[9].special_ops.mask_decisions | 524288 |
| stages[27].operations[9].source_detail.scores[0] | 1 |
| stages[27].operations[9].source_detail.scores[1] | 32 |
| stages[27].operations[9].source_detail.scores[2] | 128 |
| stages[27].operations[9].source_detail.scores[3] | 128 |
| stages[27].operations[10].name | pv |
| stages[27].operations[10].matrix_flops | 67633152 |
| stages[27].operations[10].input_precision | BF16 |
| stages[27].operations[10].accumulator_precision | FP32 |
| stages[27].operations[10].sparsity | dense |
| stages[27].operations[10].scalar_flops | 0 |
| stages[27].operations[10].special_ops | {} |
| stages[27].operations[10].source_detail.P[0] | 1 |
| stages[27].operations[10].source_detail.P[1] | 32 |
| stages[27].operations[10].source_detail.P[2] | 128 |
| stages[27].operations[10].source_detail.P[3] | 128 |
| stages[27].operations[10].source_detail.V_shared[0] | 1 |
| stages[27].operations[10].source_detail.V_shared[1] | 8 |
| stages[27].operations[10].source_detail.V_shared[2] | 128 |
| stages[27].operations[10].source_detail.V_shared[3] | 128 |
| stages[27].operations[10].source_detail.output[0] | 1 |
| stages[27].operations[10].source_detail.output[1] | 32 |
| stages[27].operations[10].source_detail.output[2] | 128 |
| stages[27].operations[10].source_detail.output[3] | 128 |
| stages[27].operations[11].name | o_proj |
| stages[27].operations[11].matrix_flops | 4294967296 |
| stages[27].operations[11].input_precision | BF16 |
| stages[27].operations[11].accumulator_precision | FP32 |
| stages[27].operations[11].sparsity | dense |
| stages[27].operations[11].scalar_flops | 0 |
| stages[27].operations[11].special_ops | {} |
| stages[27].operations[11].source_detail.input[0] | 128 |
| stages[27].operations[11].source_detail.input[1] | 4096 |
| stages[27].operations[11].source_detail.weight_math[0] | 4096 |
| stages[27].operations[11].source_detail.weight_math[1] | 4096 |
| stages[27].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[27].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[11].source_detail.output[0] | 128 |
| stages[27].operations[11].source_detail.output[1] | 4096 |
| stages[27].operations[12].name | attention_residual |
| stages[27].operations[12].matrix_flops | 0 |
| stages[27].operations[12].input_precision | unknown (null) |
| stages[27].operations[12].accumulator_precision | unknown (null) |
| stages[27].operations[12].sparsity | unknown (null) |
| stages[27].operations[12].scalar_flops | 524288 |
| stages[27].operations[12].special_ops | {} |
| stages[27].operations[12].source_detail.inputs_each[0] | 128 |
| stages[27].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[27].operations[12].source_detail.output[0] | 128 |
| stages[27].operations[12].source_detail.output[1] | 4096 |
| stages[27].operations[13].name | post_attention_layernorm |
| stages[27].operations[13].matrix_flops | 0 |
| stages[27].operations[13].input_precision | unknown (null) |
| stages[27].operations[13].accumulator_precision | unknown (null) |
| stages[27].operations[13].sparsity | unknown (null) |
| stages[27].operations[13].scalar_flops | 2097280 |
| stages[27].operations[13].special_ops.rsqrt | 128 |
| stages[27].operations[13].source_detail.input[0] | 128 |
| stages[27].operations[13].source_detail.input[1] | 4096 |
| stages[27].operations[13].source_detail.weight[0] | 4096 |
| stages[27].operations[13].source_detail.output[0] | 128 |
| stages[27].operations[13].source_detail.output[1] | 4096 |
| stages[27].operations[14].name | gate_proj |
| stages[27].operations[14].matrix_flops | 12884901888 |
| stages[27].operations[14].input_precision | BF16 |
| stages[27].operations[14].accumulator_precision | FP32 |
| stages[27].operations[14].sparsity | dense |
| stages[27].operations[14].scalar_flops | 0 |
| stages[27].operations[14].special_ops | {} |
| stages[27].operations[14].source_detail.input[0] | 128 |
| stages[27].operations[14].source_detail.input[1] | 4096 |
| stages[27].operations[14].source_detail.weight_math[0] | 4096 |
| stages[27].operations[14].source_detail.weight_math[1] | 12288 |
| stages[27].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[27].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[14].source_detail.output[0] | 128 |
| stages[27].operations[14].source_detail.output[1] | 12288 |
| stages[27].operations[15].name | up_proj |
| stages[27].operations[15].matrix_flops | 12884901888 |
| stages[27].operations[15].input_precision | BF16 |
| stages[27].operations[15].accumulator_precision | FP32 |
| stages[27].operations[15].sparsity | dense |
| stages[27].operations[15].scalar_flops | 0 |
| stages[27].operations[15].special_ops | {} |
| stages[27].operations[15].source_detail.input[0] | 128 |
| stages[27].operations[15].source_detail.input[1] | 4096 |
| stages[27].operations[15].source_detail.weight_math[0] | 4096 |
| stages[27].operations[15].source_detail.weight_math[1] | 12288 |
| stages[27].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[27].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[27].operations[15].source_detail.output[0] | 128 |
| stages[27].operations[15].source_detail.output[1] | 12288 |
| stages[27].operations[16].name | silu_mul |
| stages[27].operations[16].matrix_flops | 0 |
| stages[27].operations[16].input_precision | unknown (null) |
| stages[27].operations[16].accumulator_precision | unknown (null) |
| stages[27].operations[16].sparsity | unknown (null) |
| stages[27].operations[16].scalar_flops | 6291456 |
| stages[27].operations[16].special_ops.exp | 1572864 |
| stages[27].operations[16].special_ops.negate | 1572864 |
| stages[27].operations[16].source_detail.gate[0] | 128 |
| stages[27].operations[16].source_detail.gate[1] | 12288 |
| stages[27].operations[16].source_detail.up[0] | 128 |
| stages[27].operations[16].source_detail.up[1] | 12288 |
| stages[27].operations[16].source_detail.output[0] | 128 |
| stages[27].operations[16].source_detail.output[1] | 12288 |
| stages[27].operations[17].name | down_proj |
| stages[27].operations[17].matrix_flops | 12884901888 |
| stages[27].operations[17].input_precision | BF16 |
| stages[27].operations[17].accumulator_precision | FP32 |
| stages[27].operations[17].sparsity | dense |
| stages[27].operations[17].scalar_flops | 0 |
| stages[27].operations[17].special_ops | {} |
| stages[27].operations[17].source_detail.input[0] | 128 |
| stages[27].operations[17].source_detail.input[1] | 12288 |
| stages[27].operations[17].source_detail.weight_math[0] | 12288 |
| stages[27].operations[17].source_detail.weight_math[1] | 4096 |
| stages[27].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[27].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[27].operations[17].source_detail.output[0] | 128 |
| stages[27].operations[17].source_detail.output[1] | 4096 |
| stages[27].operations[18].name | ffn_residual |
| stages[27].operations[18].matrix_flops | 0 |
| stages[27].operations[18].input_precision | unknown (null) |
| stages[27].operations[18].accumulator_precision | unknown (null) |
| stages[27].operations[18].sparsity | unknown (null) |
| stages[27].operations[18].scalar_flops | 524288 |
| stages[27].operations[18].special_ops | {} |
| stages[27].operations[18].source_detail.inputs_each[0] | 128 |
| stages[27].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[27].operations[18].source_detail.output[0] | 128 |
| stages[27].operations[18].source_detail.output[1] | 4096 |
| stages[28].id | layer:27 |
| stages[28].work.vector_fp32 | 17179904 |
| stages[28].work.special:rsqrt | 5376 |
| stages[28].work.interface_bytes | 438387200 |
| stages[28].work.matrix_bf16 | 49527390208 |
| stages[28].work.special:negate | 1900544 |
| stages[28].work.special:exp | 1837056 |
| stages[28].work.special:compare_max | 260096 |
| stages[28].work.special:mask_decisions | 524288 |
| stages[28].operations[0].name | input_layernorm |
| stages[28].operations[0].matrix_flops | 0 |
| stages[28].operations[0].input_precision | unknown (null) |
| stages[28].operations[0].accumulator_precision | unknown (null) |
| stages[28].operations[0].sparsity | unknown (null) |
| stages[28].operations[0].scalar_flops | 2097280 |
| stages[28].operations[0].special_ops.rsqrt | 128 |
| stages[28].operations[0].source_detail.input[0] | 128 |
| stages[28].operations[0].source_detail.input[1] | 4096 |
| stages[28].operations[0].source_detail.weight[0] | 4096 |
| stages[28].operations[0].source_detail.output[0] | 128 |
| stages[28].operations[0].source_detail.output[1] | 4096 |
| stages[28].operations[1].name | q_proj |
| stages[28].operations[1].matrix_flops | 4294967296 |
| stages[28].operations[1].input_precision | BF16 |
| stages[28].operations[1].accumulator_precision | FP32 |
| stages[28].operations[1].sparsity | dense |
| stages[28].operations[1].scalar_flops | 0 |
| stages[28].operations[1].special_ops | {} |
| stages[28].operations[1].source_detail.input[0] | 128 |
| stages[28].operations[1].source_detail.input[1] | 4096 |
| stages[28].operations[1].source_detail.weight_math[0] | 4096 |
| stages[28].operations[1].source_detail.weight_math[1] | 4096 |
| stages[28].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[28].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[1].source_detail.output[0] | 128 |
| stages[28].operations[1].source_detail.output[1] | 4096 |
| stages[28].operations[2].name | k_proj |
| stages[28].operations[2].matrix_flops | 1073741824 |
| stages[28].operations[2].input_precision | BF16 |
| stages[28].operations[2].accumulator_precision | FP32 |
| stages[28].operations[2].sparsity | dense |
| stages[28].operations[2].scalar_flops | 0 |
| stages[28].operations[2].special_ops | {} |
| stages[28].operations[2].source_detail.input[0] | 128 |
| stages[28].operations[2].source_detail.input[1] | 4096 |
| stages[28].operations[2].source_detail.weight_math[0] | 4096 |
| stages[28].operations[2].source_detail.weight_math[1] | 1024 |
| stages[28].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[28].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[2].source_detail.output[0] | 128 |
| stages[28].operations[2].source_detail.output[1] | 1024 |
| stages[28].operations[3].name | v_proj |
| stages[28].operations[3].matrix_flops | 1073741824 |
| stages[28].operations[3].input_precision | BF16 |
| stages[28].operations[3].accumulator_precision | FP32 |
| stages[28].operations[3].sparsity | dense |
| stages[28].operations[3].scalar_flops | 0 |
| stages[28].operations[3].special_ops | {} |
| stages[28].operations[3].source_detail.input[0] | 128 |
| stages[28].operations[3].source_detail.input[1] | 4096 |
| stages[28].operations[3].source_detail.weight_math[0] | 4096 |
| stages[28].operations[3].source_detail.weight_math[1] | 1024 |
| stages[28].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[28].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[3].source_detail.output[0] | 128 |
| stages[28].operations[3].source_detail.output[1] | 1024 |
| stages[28].operations[4].name | q_norm |
| stages[28].operations[4].matrix_flops | 0 |
| stages[28].operations[4].input_precision | unknown (null) |
| stages[28].operations[4].accumulator_precision | unknown (null) |
| stages[28].operations[4].sparsity | unknown (null) |
| stages[28].operations[4].scalar_flops | 2101248 |
| stages[28].operations[4].special_ops.rsqrt | 4096 |
| stages[28].operations[4].source_detail.input[0] | 4096 |
| stages[28].operations[4].source_detail.input[1] | 128 |
| stages[28].operations[4].source_detail.weight[0] | 128 |
| stages[28].operations[4].source_detail.output[0] | 4096 |
| stages[28].operations[4].source_detail.output[1] | 128 |
| stages[28].operations[5].name | k_norm |
| stages[28].operations[5].matrix_flops | 0 |
| stages[28].operations[5].input_precision | unknown (null) |
| stages[28].operations[5].accumulator_precision | unknown (null) |
| stages[28].operations[5].sparsity | unknown (null) |
| stages[28].operations[5].scalar_flops | 525312 |
| stages[28].operations[5].special_ops.rsqrt | 1024 |
| stages[28].operations[5].source_detail.input[0] | 1024 |
| stages[28].operations[5].source_detail.input[1] | 128 |
| stages[28].operations[5].source_detail.weight[0] | 128 |
| stages[28].operations[5].source_detail.output[0] | 1024 |
| stages[28].operations[5].source_detail.output[1] | 128 |
| stages[28].operations[6].name | apply_rope |
| stages[28].operations[6].matrix_flops | 0 |
| stages[28].operations[6].input_precision | unknown (null) |
| stages[28].operations[6].accumulator_precision | unknown (null) |
| stages[28].operations[6].sparsity | unknown (null) |
| stages[28].operations[6].scalar_flops | 1966080 |
| stages[28].operations[6].special_ops.negate | 327680 |
| stages[28].operations[6].source_detail.Q[0] | 1 |
| stages[28].operations[6].source_detail.Q[1] | 32 |
| stages[28].operations[6].source_detail.Q[2] | 128 |
| stages[28].operations[6].source_detail.Q[3] | 128 |
| stages[28].operations[6].source_detail.K[0] | 1 |
| stages[28].operations[6].source_detail.K[1] | 8 |
| stages[28].operations[6].source_detail.K[2] | 128 |
| stages[28].operations[6].source_detail.K[3] | 128 |
| stages[28].operations[7].name | kv_append |
| stages[28].operations[7].matrix_flops | 0 |
| stages[28].operations[7].input_precision | unknown (null) |
| stages[28].operations[7].accumulator_precision | unknown (null) |
| stages[28].operations[7].sparsity | unknown (null) |
| stages[28].operations[7].scalar_flops | 0 |
| stages[28].operations[7].special_ops | {} |
| stages[28].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[28].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[28].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[28].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[28].operations[8].name | qk |
| stages[28].operations[8].matrix_flops | 67633152 |
| stages[28].operations[8].input_precision | BF16 |
| stages[28].operations[8].accumulator_precision | FP32 |
| stages[28].operations[8].sparsity | dense |
| stages[28].operations[8].scalar_flops | 0 |
| stages[28].operations[8].special_ops | {} |
| stages[28].operations[8].source_detail.Q[0] | 1 |
| stages[28].operations[8].source_detail.Q[1] | 32 |
| stages[28].operations[8].source_detail.Q[2] | 128 |
| stages[28].operations[8].source_detail.Q[3] | 128 |
| stages[28].operations[8].source_detail.K_shared[0] | 1 |
| stages[28].operations[8].source_detail.K_shared[1] | 8 |
| stages[28].operations[8].source_detail.K_shared[2] | 128 |
| stages[28].operations[8].source_detail.K_shared[3] | 128 |
| stages[28].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[28].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[28].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[28].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[28].operations[9].name | score_scale_mask_softmax |
| stages[28].operations[9].matrix_flops | 0 |
| stages[28].operations[9].input_precision | unknown (null) |
| stages[28].operations[9].accumulator_precision | unknown (null) |
| stages[28].operations[9].sparsity | unknown (null) |
| stages[28].operations[9].scalar_flops | 1052672 |
| stages[28].operations[9].special_ops.exp | 264192 |
| stages[28].operations[9].special_ops.compare_max | 260096 |
| stages[28].operations[9].special_ops.mask_decisions | 524288 |
| stages[28].operations[9].source_detail.scores[0] | 1 |
| stages[28].operations[9].source_detail.scores[1] | 32 |
| stages[28].operations[9].source_detail.scores[2] | 128 |
| stages[28].operations[9].source_detail.scores[3] | 128 |
| stages[28].operations[10].name | pv |
| stages[28].operations[10].matrix_flops | 67633152 |
| stages[28].operations[10].input_precision | BF16 |
| stages[28].operations[10].accumulator_precision | FP32 |
| stages[28].operations[10].sparsity | dense |
| stages[28].operations[10].scalar_flops | 0 |
| stages[28].operations[10].special_ops | {} |
| stages[28].operations[10].source_detail.P[0] | 1 |
| stages[28].operations[10].source_detail.P[1] | 32 |
| stages[28].operations[10].source_detail.P[2] | 128 |
| stages[28].operations[10].source_detail.P[3] | 128 |
| stages[28].operations[10].source_detail.V_shared[0] | 1 |
| stages[28].operations[10].source_detail.V_shared[1] | 8 |
| stages[28].operations[10].source_detail.V_shared[2] | 128 |
| stages[28].operations[10].source_detail.V_shared[3] | 128 |
| stages[28].operations[10].source_detail.output[0] | 1 |
| stages[28].operations[10].source_detail.output[1] | 32 |
| stages[28].operations[10].source_detail.output[2] | 128 |
| stages[28].operations[10].source_detail.output[3] | 128 |
| stages[28].operations[11].name | o_proj |
| stages[28].operations[11].matrix_flops | 4294967296 |
| stages[28].operations[11].input_precision | BF16 |
| stages[28].operations[11].accumulator_precision | FP32 |
| stages[28].operations[11].sparsity | dense |
| stages[28].operations[11].scalar_flops | 0 |
| stages[28].operations[11].special_ops | {} |
| stages[28].operations[11].source_detail.input[0] | 128 |
| stages[28].operations[11].source_detail.input[1] | 4096 |
| stages[28].operations[11].source_detail.weight_math[0] | 4096 |
| stages[28].operations[11].source_detail.weight_math[1] | 4096 |
| stages[28].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[28].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[11].source_detail.output[0] | 128 |
| stages[28].operations[11].source_detail.output[1] | 4096 |
| stages[28].operations[12].name | attention_residual |
| stages[28].operations[12].matrix_flops | 0 |
| stages[28].operations[12].input_precision | unknown (null) |
| stages[28].operations[12].accumulator_precision | unknown (null) |
| stages[28].operations[12].sparsity | unknown (null) |
| stages[28].operations[12].scalar_flops | 524288 |
| stages[28].operations[12].special_ops | {} |
| stages[28].operations[12].source_detail.inputs_each[0] | 128 |
| stages[28].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[28].operations[12].source_detail.output[0] | 128 |
| stages[28].operations[12].source_detail.output[1] | 4096 |
| stages[28].operations[13].name | post_attention_layernorm |
| stages[28].operations[13].matrix_flops | 0 |
| stages[28].operations[13].input_precision | unknown (null) |
| stages[28].operations[13].accumulator_precision | unknown (null) |
| stages[28].operations[13].sparsity | unknown (null) |
| stages[28].operations[13].scalar_flops | 2097280 |
| stages[28].operations[13].special_ops.rsqrt | 128 |
| stages[28].operations[13].source_detail.input[0] | 128 |
| stages[28].operations[13].source_detail.input[1] | 4096 |
| stages[28].operations[13].source_detail.weight[0] | 4096 |
| stages[28].operations[13].source_detail.output[0] | 128 |
| stages[28].operations[13].source_detail.output[1] | 4096 |
| stages[28].operations[14].name | gate_proj |
| stages[28].operations[14].matrix_flops | 12884901888 |
| stages[28].operations[14].input_precision | BF16 |
| stages[28].operations[14].accumulator_precision | FP32 |
| stages[28].operations[14].sparsity | dense |
| stages[28].operations[14].scalar_flops | 0 |
| stages[28].operations[14].special_ops | {} |
| stages[28].operations[14].source_detail.input[0] | 128 |
| stages[28].operations[14].source_detail.input[1] | 4096 |
| stages[28].operations[14].source_detail.weight_math[0] | 4096 |
| stages[28].operations[14].source_detail.weight_math[1] | 12288 |
| stages[28].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[28].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[14].source_detail.output[0] | 128 |
| stages[28].operations[14].source_detail.output[1] | 12288 |
| stages[28].operations[15].name | up_proj |
| stages[28].operations[15].matrix_flops | 12884901888 |
| stages[28].operations[15].input_precision | BF16 |
| stages[28].operations[15].accumulator_precision | FP32 |
| stages[28].operations[15].sparsity | dense |
| stages[28].operations[15].scalar_flops | 0 |
| stages[28].operations[15].special_ops | {} |
| stages[28].operations[15].source_detail.input[0] | 128 |
| stages[28].operations[15].source_detail.input[1] | 4096 |
| stages[28].operations[15].source_detail.weight_math[0] | 4096 |
| stages[28].operations[15].source_detail.weight_math[1] | 12288 |
| stages[28].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[28].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[28].operations[15].source_detail.output[0] | 128 |
| stages[28].operations[15].source_detail.output[1] | 12288 |
| stages[28].operations[16].name | silu_mul |
| stages[28].operations[16].matrix_flops | 0 |
| stages[28].operations[16].input_precision | unknown (null) |
| stages[28].operations[16].accumulator_precision | unknown (null) |
| stages[28].operations[16].sparsity | unknown (null) |
| stages[28].operations[16].scalar_flops | 6291456 |
| stages[28].operations[16].special_ops.exp | 1572864 |
| stages[28].operations[16].special_ops.negate | 1572864 |
| stages[28].operations[16].source_detail.gate[0] | 128 |
| stages[28].operations[16].source_detail.gate[1] | 12288 |
| stages[28].operations[16].source_detail.up[0] | 128 |
| stages[28].operations[16].source_detail.up[1] | 12288 |
| stages[28].operations[16].source_detail.output[0] | 128 |
| stages[28].operations[16].source_detail.output[1] | 12288 |
| stages[28].operations[17].name | down_proj |
| stages[28].operations[17].matrix_flops | 12884901888 |
| stages[28].operations[17].input_precision | BF16 |
| stages[28].operations[17].accumulator_precision | FP32 |
| stages[28].operations[17].sparsity | dense |
| stages[28].operations[17].scalar_flops | 0 |
| stages[28].operations[17].special_ops | {} |
| stages[28].operations[17].source_detail.input[0] | 128 |
| stages[28].operations[17].source_detail.input[1] | 12288 |
| stages[28].operations[17].source_detail.weight_math[0] | 12288 |
| stages[28].operations[17].source_detail.weight_math[1] | 4096 |
| stages[28].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[28].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[28].operations[17].source_detail.output[0] | 128 |
| stages[28].operations[17].source_detail.output[1] | 4096 |
| stages[28].operations[18].name | ffn_residual |
| stages[28].operations[18].matrix_flops | 0 |
| stages[28].operations[18].input_precision | unknown (null) |
| stages[28].operations[18].accumulator_precision | unknown (null) |
| stages[28].operations[18].sparsity | unknown (null) |
| stages[28].operations[18].scalar_flops | 524288 |
| stages[28].operations[18].special_ops | {} |
| stages[28].operations[18].source_detail.inputs_each[0] | 128 |
| stages[28].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[28].operations[18].source_detail.output[0] | 128 |
| stages[28].operations[18].source_detail.output[1] | 4096 |
| stages[29].id | layer:28 |
| stages[29].work.vector_fp32 | 17179904 |
| stages[29].work.special:rsqrt | 5376 |
| stages[29].work.interface_bytes | 438387200 |
| stages[29].work.matrix_bf16 | 49527390208 |
| stages[29].work.special:negate | 1900544 |
| stages[29].work.special:exp | 1837056 |
| stages[29].work.special:compare_max | 260096 |
| stages[29].work.special:mask_decisions | 524288 |
| stages[29].operations[0].name | input_layernorm |
| stages[29].operations[0].matrix_flops | 0 |
| stages[29].operations[0].input_precision | unknown (null) |
| stages[29].operations[0].accumulator_precision | unknown (null) |
| stages[29].operations[0].sparsity | unknown (null) |
| stages[29].operations[0].scalar_flops | 2097280 |
| stages[29].operations[0].special_ops.rsqrt | 128 |
| stages[29].operations[0].source_detail.input[0] | 128 |
| stages[29].operations[0].source_detail.input[1] | 4096 |
| stages[29].operations[0].source_detail.weight[0] | 4096 |
| stages[29].operations[0].source_detail.output[0] | 128 |
| stages[29].operations[0].source_detail.output[1] | 4096 |
| stages[29].operations[1].name | q_proj |
| stages[29].operations[1].matrix_flops | 4294967296 |
| stages[29].operations[1].input_precision | BF16 |
| stages[29].operations[1].accumulator_precision | FP32 |
| stages[29].operations[1].sparsity | dense |
| stages[29].operations[1].scalar_flops | 0 |
| stages[29].operations[1].special_ops | {} |
| stages[29].operations[1].source_detail.input[0] | 128 |
| stages[29].operations[1].source_detail.input[1] | 4096 |
| stages[29].operations[1].source_detail.weight_math[0] | 4096 |
| stages[29].operations[1].source_detail.weight_math[1] | 4096 |
| stages[29].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[29].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[1].source_detail.output[0] | 128 |
| stages[29].operations[1].source_detail.output[1] | 4096 |
| stages[29].operations[2].name | k_proj |
| stages[29].operations[2].matrix_flops | 1073741824 |
| stages[29].operations[2].input_precision | BF16 |
| stages[29].operations[2].accumulator_precision | FP32 |
| stages[29].operations[2].sparsity | dense |
| stages[29].operations[2].scalar_flops | 0 |
| stages[29].operations[2].special_ops | {} |
| stages[29].operations[2].source_detail.input[0] | 128 |
| stages[29].operations[2].source_detail.input[1] | 4096 |
| stages[29].operations[2].source_detail.weight_math[0] | 4096 |
| stages[29].operations[2].source_detail.weight_math[1] | 1024 |
| stages[29].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[29].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[2].source_detail.output[0] | 128 |
| stages[29].operations[2].source_detail.output[1] | 1024 |
| stages[29].operations[3].name | v_proj |
| stages[29].operations[3].matrix_flops | 1073741824 |
| stages[29].operations[3].input_precision | BF16 |
| stages[29].operations[3].accumulator_precision | FP32 |
| stages[29].operations[3].sparsity | dense |
| stages[29].operations[3].scalar_flops | 0 |
| stages[29].operations[3].special_ops | {} |
| stages[29].operations[3].source_detail.input[0] | 128 |
| stages[29].operations[3].source_detail.input[1] | 4096 |
| stages[29].operations[3].source_detail.weight_math[0] | 4096 |
| stages[29].operations[3].source_detail.weight_math[1] | 1024 |
| stages[29].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[29].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[3].source_detail.output[0] | 128 |
| stages[29].operations[3].source_detail.output[1] | 1024 |
| stages[29].operations[4].name | q_norm |
| stages[29].operations[4].matrix_flops | 0 |
| stages[29].operations[4].input_precision | unknown (null) |
| stages[29].operations[4].accumulator_precision | unknown (null) |
| stages[29].operations[4].sparsity | unknown (null) |
| stages[29].operations[4].scalar_flops | 2101248 |
| stages[29].operations[4].special_ops.rsqrt | 4096 |
| stages[29].operations[4].source_detail.input[0] | 4096 |
| stages[29].operations[4].source_detail.input[1] | 128 |
| stages[29].operations[4].source_detail.weight[0] | 128 |
| stages[29].operations[4].source_detail.output[0] | 4096 |
| stages[29].operations[4].source_detail.output[1] | 128 |
| stages[29].operations[5].name | k_norm |
| stages[29].operations[5].matrix_flops | 0 |
| stages[29].operations[5].input_precision | unknown (null) |
| stages[29].operations[5].accumulator_precision | unknown (null) |
| stages[29].operations[5].sparsity | unknown (null) |
| stages[29].operations[5].scalar_flops | 525312 |
| stages[29].operations[5].special_ops.rsqrt | 1024 |
| stages[29].operations[5].source_detail.input[0] | 1024 |
| stages[29].operations[5].source_detail.input[1] | 128 |
| stages[29].operations[5].source_detail.weight[0] | 128 |
| stages[29].operations[5].source_detail.output[0] | 1024 |
| stages[29].operations[5].source_detail.output[1] | 128 |
| stages[29].operations[6].name | apply_rope |
| stages[29].operations[6].matrix_flops | 0 |
| stages[29].operations[6].input_precision | unknown (null) |
| stages[29].operations[6].accumulator_precision | unknown (null) |
| stages[29].operations[6].sparsity | unknown (null) |
| stages[29].operations[6].scalar_flops | 1966080 |
| stages[29].operations[6].special_ops.negate | 327680 |
| stages[29].operations[6].source_detail.Q[0] | 1 |
| stages[29].operations[6].source_detail.Q[1] | 32 |
| stages[29].operations[6].source_detail.Q[2] | 128 |
| stages[29].operations[6].source_detail.Q[3] | 128 |
| stages[29].operations[6].source_detail.K[0] | 1 |
| stages[29].operations[6].source_detail.K[1] | 8 |
| stages[29].operations[6].source_detail.K[2] | 128 |
| stages[29].operations[6].source_detail.K[3] | 128 |
| stages[29].operations[7].name | kv_append |
| stages[29].operations[7].matrix_flops | 0 |
| stages[29].operations[7].input_precision | unknown (null) |
| stages[29].operations[7].accumulator_precision | unknown (null) |
| stages[29].operations[7].sparsity | unknown (null) |
| stages[29].operations[7].scalar_flops | 0 |
| stages[29].operations[7].special_ops | {} |
| stages[29].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[29].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[29].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[29].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[29].operations[8].name | qk |
| stages[29].operations[8].matrix_flops | 67633152 |
| stages[29].operations[8].input_precision | BF16 |
| stages[29].operations[8].accumulator_precision | FP32 |
| stages[29].operations[8].sparsity | dense |
| stages[29].operations[8].scalar_flops | 0 |
| stages[29].operations[8].special_ops | {} |
| stages[29].operations[8].source_detail.Q[0] | 1 |
| stages[29].operations[8].source_detail.Q[1] | 32 |
| stages[29].operations[8].source_detail.Q[2] | 128 |
| stages[29].operations[8].source_detail.Q[3] | 128 |
| stages[29].operations[8].source_detail.K_shared[0] | 1 |
| stages[29].operations[8].source_detail.K_shared[1] | 8 |
| stages[29].operations[8].source_detail.K_shared[2] | 128 |
| stages[29].operations[8].source_detail.K_shared[3] | 128 |
| stages[29].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[29].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[29].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[29].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[29].operations[9].name | score_scale_mask_softmax |
| stages[29].operations[9].matrix_flops | 0 |
| stages[29].operations[9].input_precision | unknown (null) |
| stages[29].operations[9].accumulator_precision | unknown (null) |
| stages[29].operations[9].sparsity | unknown (null) |
| stages[29].operations[9].scalar_flops | 1052672 |
| stages[29].operations[9].special_ops.exp | 264192 |
| stages[29].operations[9].special_ops.compare_max | 260096 |
| stages[29].operations[9].special_ops.mask_decisions | 524288 |
| stages[29].operations[9].source_detail.scores[0] | 1 |
| stages[29].operations[9].source_detail.scores[1] | 32 |
| stages[29].operations[9].source_detail.scores[2] | 128 |
| stages[29].operations[9].source_detail.scores[3] | 128 |
| stages[29].operations[10].name | pv |
| stages[29].operations[10].matrix_flops | 67633152 |
| stages[29].operations[10].input_precision | BF16 |
| stages[29].operations[10].accumulator_precision | FP32 |
| stages[29].operations[10].sparsity | dense |
| stages[29].operations[10].scalar_flops | 0 |
| stages[29].operations[10].special_ops | {} |
| stages[29].operations[10].source_detail.P[0] | 1 |
| stages[29].operations[10].source_detail.P[1] | 32 |
| stages[29].operations[10].source_detail.P[2] | 128 |
| stages[29].operations[10].source_detail.P[3] | 128 |
| stages[29].operations[10].source_detail.V_shared[0] | 1 |
| stages[29].operations[10].source_detail.V_shared[1] | 8 |
| stages[29].operations[10].source_detail.V_shared[2] | 128 |
| stages[29].operations[10].source_detail.V_shared[3] | 128 |
| stages[29].operations[10].source_detail.output[0] | 1 |
| stages[29].operations[10].source_detail.output[1] | 32 |
| stages[29].operations[10].source_detail.output[2] | 128 |
| stages[29].operations[10].source_detail.output[3] | 128 |
| stages[29].operations[11].name | o_proj |
| stages[29].operations[11].matrix_flops | 4294967296 |
| stages[29].operations[11].input_precision | BF16 |
| stages[29].operations[11].accumulator_precision | FP32 |
| stages[29].operations[11].sparsity | dense |
| stages[29].operations[11].scalar_flops | 0 |
| stages[29].operations[11].special_ops | {} |
| stages[29].operations[11].source_detail.input[0] | 128 |
| stages[29].operations[11].source_detail.input[1] | 4096 |
| stages[29].operations[11].source_detail.weight_math[0] | 4096 |
| stages[29].operations[11].source_detail.weight_math[1] | 4096 |
| stages[29].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[29].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[11].source_detail.output[0] | 128 |
| stages[29].operations[11].source_detail.output[1] | 4096 |
| stages[29].operations[12].name | attention_residual |
| stages[29].operations[12].matrix_flops | 0 |
| stages[29].operations[12].input_precision | unknown (null) |
| stages[29].operations[12].accumulator_precision | unknown (null) |
| stages[29].operations[12].sparsity | unknown (null) |
| stages[29].operations[12].scalar_flops | 524288 |
| stages[29].operations[12].special_ops | {} |
| stages[29].operations[12].source_detail.inputs_each[0] | 128 |
| stages[29].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[29].operations[12].source_detail.output[0] | 128 |
| stages[29].operations[12].source_detail.output[1] | 4096 |
| stages[29].operations[13].name | post_attention_layernorm |
| stages[29].operations[13].matrix_flops | 0 |
| stages[29].operations[13].input_precision | unknown (null) |
| stages[29].operations[13].accumulator_precision | unknown (null) |
| stages[29].operations[13].sparsity | unknown (null) |
| stages[29].operations[13].scalar_flops | 2097280 |
| stages[29].operations[13].special_ops.rsqrt | 128 |
| stages[29].operations[13].source_detail.input[0] | 128 |
| stages[29].operations[13].source_detail.input[1] | 4096 |
| stages[29].operations[13].source_detail.weight[0] | 4096 |
| stages[29].operations[13].source_detail.output[0] | 128 |
| stages[29].operations[13].source_detail.output[1] | 4096 |
| stages[29].operations[14].name | gate_proj |
| stages[29].operations[14].matrix_flops | 12884901888 |
| stages[29].operations[14].input_precision | BF16 |
| stages[29].operations[14].accumulator_precision | FP32 |
| stages[29].operations[14].sparsity | dense |
| stages[29].operations[14].scalar_flops | 0 |
| stages[29].operations[14].special_ops | {} |
| stages[29].operations[14].source_detail.input[0] | 128 |
| stages[29].operations[14].source_detail.input[1] | 4096 |
| stages[29].operations[14].source_detail.weight_math[0] | 4096 |
| stages[29].operations[14].source_detail.weight_math[1] | 12288 |
| stages[29].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[29].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[14].source_detail.output[0] | 128 |
| stages[29].operations[14].source_detail.output[1] | 12288 |
| stages[29].operations[15].name | up_proj |
| stages[29].operations[15].matrix_flops | 12884901888 |
| stages[29].operations[15].input_precision | BF16 |
| stages[29].operations[15].accumulator_precision | FP32 |
| stages[29].operations[15].sparsity | dense |
| stages[29].operations[15].scalar_flops | 0 |
| stages[29].operations[15].special_ops | {} |
| stages[29].operations[15].source_detail.input[0] | 128 |
| stages[29].operations[15].source_detail.input[1] | 4096 |
| stages[29].operations[15].source_detail.weight_math[0] | 4096 |
| stages[29].operations[15].source_detail.weight_math[1] | 12288 |
| stages[29].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[29].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[29].operations[15].source_detail.output[0] | 128 |
| stages[29].operations[15].source_detail.output[1] | 12288 |
| stages[29].operations[16].name | silu_mul |
| stages[29].operations[16].matrix_flops | 0 |
| stages[29].operations[16].input_precision | unknown (null) |
| stages[29].operations[16].accumulator_precision | unknown (null) |
| stages[29].operations[16].sparsity | unknown (null) |
| stages[29].operations[16].scalar_flops | 6291456 |
| stages[29].operations[16].special_ops.exp | 1572864 |
| stages[29].operations[16].special_ops.negate | 1572864 |
| stages[29].operations[16].source_detail.gate[0] | 128 |
| stages[29].operations[16].source_detail.gate[1] | 12288 |
| stages[29].operations[16].source_detail.up[0] | 128 |
| stages[29].operations[16].source_detail.up[1] | 12288 |
| stages[29].operations[16].source_detail.output[0] | 128 |
| stages[29].operations[16].source_detail.output[1] | 12288 |
| stages[29].operations[17].name | down_proj |
| stages[29].operations[17].matrix_flops | 12884901888 |
| stages[29].operations[17].input_precision | BF16 |
| stages[29].operations[17].accumulator_precision | FP32 |
| stages[29].operations[17].sparsity | dense |
| stages[29].operations[17].scalar_flops | 0 |
| stages[29].operations[17].special_ops | {} |
| stages[29].operations[17].source_detail.input[0] | 128 |
| stages[29].operations[17].source_detail.input[1] | 12288 |
| stages[29].operations[17].source_detail.weight_math[0] | 12288 |
| stages[29].operations[17].source_detail.weight_math[1] | 4096 |
| stages[29].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[29].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[29].operations[17].source_detail.output[0] | 128 |
| stages[29].operations[17].source_detail.output[1] | 4096 |
| stages[29].operations[18].name | ffn_residual |
| stages[29].operations[18].matrix_flops | 0 |
| stages[29].operations[18].input_precision | unknown (null) |
| stages[29].operations[18].accumulator_precision | unknown (null) |
| stages[29].operations[18].sparsity | unknown (null) |
| stages[29].operations[18].scalar_flops | 524288 |
| stages[29].operations[18].special_ops | {} |
| stages[29].operations[18].source_detail.inputs_each[0] | 128 |
| stages[29].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[29].operations[18].source_detail.output[0] | 128 |
| stages[29].operations[18].source_detail.output[1] | 4096 |
| stages[30].id | layer:29 |
| stages[30].work.vector_fp32 | 17179904 |
| stages[30].work.special:rsqrt | 5376 |
| stages[30].work.interface_bytes | 438387200 |
| stages[30].work.matrix_bf16 | 49527390208 |
| stages[30].work.special:negate | 1900544 |
| stages[30].work.special:exp | 1837056 |
| stages[30].work.special:compare_max | 260096 |
| stages[30].work.special:mask_decisions | 524288 |
| stages[30].operations[0].name | input_layernorm |
| stages[30].operations[0].matrix_flops | 0 |
| stages[30].operations[0].input_precision | unknown (null) |
| stages[30].operations[0].accumulator_precision | unknown (null) |
| stages[30].operations[0].sparsity | unknown (null) |
| stages[30].operations[0].scalar_flops | 2097280 |
| stages[30].operations[0].special_ops.rsqrt | 128 |
| stages[30].operations[0].source_detail.input[0] | 128 |
| stages[30].operations[0].source_detail.input[1] | 4096 |
| stages[30].operations[0].source_detail.weight[0] | 4096 |
| stages[30].operations[0].source_detail.output[0] | 128 |
| stages[30].operations[0].source_detail.output[1] | 4096 |
| stages[30].operations[1].name | q_proj |
| stages[30].operations[1].matrix_flops | 4294967296 |
| stages[30].operations[1].input_precision | BF16 |
| stages[30].operations[1].accumulator_precision | FP32 |
| stages[30].operations[1].sparsity | dense |
| stages[30].operations[1].scalar_flops | 0 |
| stages[30].operations[1].special_ops | {} |
| stages[30].operations[1].source_detail.input[0] | 128 |
| stages[30].operations[1].source_detail.input[1] | 4096 |
| stages[30].operations[1].source_detail.weight_math[0] | 4096 |
| stages[30].operations[1].source_detail.weight_math[1] | 4096 |
| stages[30].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[30].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[1].source_detail.output[0] | 128 |
| stages[30].operations[1].source_detail.output[1] | 4096 |
| stages[30].operations[2].name | k_proj |
| stages[30].operations[2].matrix_flops | 1073741824 |
| stages[30].operations[2].input_precision | BF16 |
| stages[30].operations[2].accumulator_precision | FP32 |
| stages[30].operations[2].sparsity | dense |
| stages[30].operations[2].scalar_flops | 0 |
| stages[30].operations[2].special_ops | {} |
| stages[30].operations[2].source_detail.input[0] | 128 |
| stages[30].operations[2].source_detail.input[1] | 4096 |
| stages[30].operations[2].source_detail.weight_math[0] | 4096 |
| stages[30].operations[2].source_detail.weight_math[1] | 1024 |
| stages[30].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[30].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[2].source_detail.output[0] | 128 |
| stages[30].operations[2].source_detail.output[1] | 1024 |
| stages[30].operations[3].name | v_proj |
| stages[30].operations[3].matrix_flops | 1073741824 |
| stages[30].operations[3].input_precision | BF16 |
| stages[30].operations[3].accumulator_precision | FP32 |
| stages[30].operations[3].sparsity | dense |
| stages[30].operations[3].scalar_flops | 0 |
| stages[30].operations[3].special_ops | {} |
| stages[30].operations[3].source_detail.input[0] | 128 |
| stages[30].operations[3].source_detail.input[1] | 4096 |
| stages[30].operations[3].source_detail.weight_math[0] | 4096 |
| stages[30].operations[3].source_detail.weight_math[1] | 1024 |
| stages[30].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[30].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[3].source_detail.output[0] | 128 |
| stages[30].operations[3].source_detail.output[1] | 1024 |
| stages[30].operations[4].name | q_norm |
| stages[30].operations[4].matrix_flops | 0 |
| stages[30].operations[4].input_precision | unknown (null) |
| stages[30].operations[4].accumulator_precision | unknown (null) |
| stages[30].operations[4].sparsity | unknown (null) |
| stages[30].operations[4].scalar_flops | 2101248 |
| stages[30].operations[4].special_ops.rsqrt | 4096 |
| stages[30].operations[4].source_detail.input[0] | 4096 |
| stages[30].operations[4].source_detail.input[1] | 128 |
| stages[30].operations[4].source_detail.weight[0] | 128 |
| stages[30].operations[4].source_detail.output[0] | 4096 |
| stages[30].operations[4].source_detail.output[1] | 128 |
| stages[30].operations[5].name | k_norm |
| stages[30].operations[5].matrix_flops | 0 |
| stages[30].operations[5].input_precision | unknown (null) |
| stages[30].operations[5].accumulator_precision | unknown (null) |
| stages[30].operations[5].sparsity | unknown (null) |
| stages[30].operations[5].scalar_flops | 525312 |
| stages[30].operations[5].special_ops.rsqrt | 1024 |
| stages[30].operations[5].source_detail.input[0] | 1024 |
| stages[30].operations[5].source_detail.input[1] | 128 |
| stages[30].operations[5].source_detail.weight[0] | 128 |
| stages[30].operations[5].source_detail.output[0] | 1024 |
| stages[30].operations[5].source_detail.output[1] | 128 |
| stages[30].operations[6].name | apply_rope |
| stages[30].operations[6].matrix_flops | 0 |
| stages[30].operations[6].input_precision | unknown (null) |
| stages[30].operations[6].accumulator_precision | unknown (null) |
| stages[30].operations[6].sparsity | unknown (null) |
| stages[30].operations[6].scalar_flops | 1966080 |
| stages[30].operations[6].special_ops.negate | 327680 |
| stages[30].operations[6].source_detail.Q[0] | 1 |
| stages[30].operations[6].source_detail.Q[1] | 32 |
| stages[30].operations[6].source_detail.Q[2] | 128 |
| stages[30].operations[6].source_detail.Q[3] | 128 |
| stages[30].operations[6].source_detail.K[0] | 1 |
| stages[30].operations[6].source_detail.K[1] | 8 |
| stages[30].operations[6].source_detail.K[2] | 128 |
| stages[30].operations[6].source_detail.K[3] | 128 |
| stages[30].operations[7].name | kv_append |
| stages[30].operations[7].matrix_flops | 0 |
| stages[30].operations[7].input_precision | unknown (null) |
| stages[30].operations[7].accumulator_precision | unknown (null) |
| stages[30].operations[7].sparsity | unknown (null) |
| stages[30].operations[7].scalar_flops | 0 |
| stages[30].operations[7].special_ops | {} |
| stages[30].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[30].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[30].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[30].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[30].operations[8].name | qk |
| stages[30].operations[8].matrix_flops | 67633152 |
| stages[30].operations[8].input_precision | BF16 |
| stages[30].operations[8].accumulator_precision | FP32 |
| stages[30].operations[8].sparsity | dense |
| stages[30].operations[8].scalar_flops | 0 |
| stages[30].operations[8].special_ops | {} |
| stages[30].operations[8].source_detail.Q[0] | 1 |
| stages[30].operations[8].source_detail.Q[1] | 32 |
| stages[30].operations[8].source_detail.Q[2] | 128 |
| stages[30].operations[8].source_detail.Q[3] | 128 |
| stages[30].operations[8].source_detail.K_shared[0] | 1 |
| stages[30].operations[8].source_detail.K_shared[1] | 8 |
| stages[30].operations[8].source_detail.K_shared[2] | 128 |
| stages[30].operations[8].source_detail.K_shared[3] | 128 |
| stages[30].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[30].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[30].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[30].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[30].operations[9].name | score_scale_mask_softmax |
| stages[30].operations[9].matrix_flops | 0 |
| stages[30].operations[9].input_precision | unknown (null) |
| stages[30].operations[9].accumulator_precision | unknown (null) |
| stages[30].operations[9].sparsity | unknown (null) |
| stages[30].operations[9].scalar_flops | 1052672 |
| stages[30].operations[9].special_ops.exp | 264192 |
| stages[30].operations[9].special_ops.compare_max | 260096 |
| stages[30].operations[9].special_ops.mask_decisions | 524288 |
| stages[30].operations[9].source_detail.scores[0] | 1 |
| stages[30].operations[9].source_detail.scores[1] | 32 |
| stages[30].operations[9].source_detail.scores[2] | 128 |
| stages[30].operations[9].source_detail.scores[3] | 128 |
| stages[30].operations[10].name | pv |
| stages[30].operations[10].matrix_flops | 67633152 |
| stages[30].operations[10].input_precision | BF16 |
| stages[30].operations[10].accumulator_precision | FP32 |
| stages[30].operations[10].sparsity | dense |
| stages[30].operations[10].scalar_flops | 0 |
| stages[30].operations[10].special_ops | {} |
| stages[30].operations[10].source_detail.P[0] | 1 |
| stages[30].operations[10].source_detail.P[1] | 32 |
| stages[30].operations[10].source_detail.P[2] | 128 |
| stages[30].operations[10].source_detail.P[3] | 128 |
| stages[30].operations[10].source_detail.V_shared[0] | 1 |
| stages[30].operations[10].source_detail.V_shared[1] | 8 |
| stages[30].operations[10].source_detail.V_shared[2] | 128 |
| stages[30].operations[10].source_detail.V_shared[3] | 128 |
| stages[30].operations[10].source_detail.output[0] | 1 |
| stages[30].operations[10].source_detail.output[1] | 32 |
| stages[30].operations[10].source_detail.output[2] | 128 |
| stages[30].operations[10].source_detail.output[3] | 128 |
| stages[30].operations[11].name | o_proj |
| stages[30].operations[11].matrix_flops | 4294967296 |
| stages[30].operations[11].input_precision | BF16 |
| stages[30].operations[11].accumulator_precision | FP32 |
| stages[30].operations[11].sparsity | dense |
| stages[30].operations[11].scalar_flops | 0 |
| stages[30].operations[11].special_ops | {} |
| stages[30].operations[11].source_detail.input[0] | 128 |
| stages[30].operations[11].source_detail.input[1] | 4096 |
| stages[30].operations[11].source_detail.weight_math[0] | 4096 |
| stages[30].operations[11].source_detail.weight_math[1] | 4096 |
| stages[30].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[30].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[11].source_detail.output[0] | 128 |
| stages[30].operations[11].source_detail.output[1] | 4096 |
| stages[30].operations[12].name | attention_residual |
| stages[30].operations[12].matrix_flops | 0 |
| stages[30].operations[12].input_precision | unknown (null) |
| stages[30].operations[12].accumulator_precision | unknown (null) |
| stages[30].operations[12].sparsity | unknown (null) |
| stages[30].operations[12].scalar_flops | 524288 |
| stages[30].operations[12].special_ops | {} |
| stages[30].operations[12].source_detail.inputs_each[0] | 128 |
| stages[30].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[30].operations[12].source_detail.output[0] | 128 |
| stages[30].operations[12].source_detail.output[1] | 4096 |
| stages[30].operations[13].name | post_attention_layernorm |
| stages[30].operations[13].matrix_flops | 0 |
| stages[30].operations[13].input_precision | unknown (null) |
| stages[30].operations[13].accumulator_precision | unknown (null) |
| stages[30].operations[13].sparsity | unknown (null) |
| stages[30].operations[13].scalar_flops | 2097280 |
| stages[30].operations[13].special_ops.rsqrt | 128 |
| stages[30].operations[13].source_detail.input[0] | 128 |
| stages[30].operations[13].source_detail.input[1] | 4096 |
| stages[30].operations[13].source_detail.weight[0] | 4096 |
| stages[30].operations[13].source_detail.output[0] | 128 |
| stages[30].operations[13].source_detail.output[1] | 4096 |
| stages[30].operations[14].name | gate_proj |
| stages[30].operations[14].matrix_flops | 12884901888 |
| stages[30].operations[14].input_precision | BF16 |
| stages[30].operations[14].accumulator_precision | FP32 |
| stages[30].operations[14].sparsity | dense |
| stages[30].operations[14].scalar_flops | 0 |
| stages[30].operations[14].special_ops | {} |
| stages[30].operations[14].source_detail.input[0] | 128 |
| stages[30].operations[14].source_detail.input[1] | 4096 |
| stages[30].operations[14].source_detail.weight_math[0] | 4096 |
| stages[30].operations[14].source_detail.weight_math[1] | 12288 |
| stages[30].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[30].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[14].source_detail.output[0] | 128 |
| stages[30].operations[14].source_detail.output[1] | 12288 |
| stages[30].operations[15].name | up_proj |
| stages[30].operations[15].matrix_flops | 12884901888 |
| stages[30].operations[15].input_precision | BF16 |
| stages[30].operations[15].accumulator_precision | FP32 |
| stages[30].operations[15].sparsity | dense |
| stages[30].operations[15].scalar_flops | 0 |
| stages[30].operations[15].special_ops | {} |
| stages[30].operations[15].source_detail.input[0] | 128 |
| stages[30].operations[15].source_detail.input[1] | 4096 |
| stages[30].operations[15].source_detail.weight_math[0] | 4096 |
| stages[30].operations[15].source_detail.weight_math[1] | 12288 |
| stages[30].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[30].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[30].operations[15].source_detail.output[0] | 128 |
| stages[30].operations[15].source_detail.output[1] | 12288 |
| stages[30].operations[16].name | silu_mul |
| stages[30].operations[16].matrix_flops | 0 |
| stages[30].operations[16].input_precision | unknown (null) |
| stages[30].operations[16].accumulator_precision | unknown (null) |
| stages[30].operations[16].sparsity | unknown (null) |
| stages[30].operations[16].scalar_flops | 6291456 |
| stages[30].operations[16].special_ops.exp | 1572864 |
| stages[30].operations[16].special_ops.negate | 1572864 |
| stages[30].operations[16].source_detail.gate[0] | 128 |
| stages[30].operations[16].source_detail.gate[1] | 12288 |
| stages[30].operations[16].source_detail.up[0] | 128 |
| stages[30].operations[16].source_detail.up[1] | 12288 |
| stages[30].operations[16].source_detail.output[0] | 128 |
| stages[30].operations[16].source_detail.output[1] | 12288 |
| stages[30].operations[17].name | down_proj |
| stages[30].operations[17].matrix_flops | 12884901888 |
| stages[30].operations[17].input_precision | BF16 |
| stages[30].operations[17].accumulator_precision | FP32 |
| stages[30].operations[17].sparsity | dense |
| stages[30].operations[17].scalar_flops | 0 |
| stages[30].operations[17].special_ops | {} |
| stages[30].operations[17].source_detail.input[0] | 128 |
| stages[30].operations[17].source_detail.input[1] | 12288 |
| stages[30].operations[17].source_detail.weight_math[0] | 12288 |
| stages[30].operations[17].source_detail.weight_math[1] | 4096 |
| stages[30].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[30].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[30].operations[17].source_detail.output[0] | 128 |
| stages[30].operations[17].source_detail.output[1] | 4096 |
| stages[30].operations[18].name | ffn_residual |
| stages[30].operations[18].matrix_flops | 0 |
| stages[30].operations[18].input_precision | unknown (null) |
| stages[30].operations[18].accumulator_precision | unknown (null) |
| stages[30].operations[18].sparsity | unknown (null) |
| stages[30].operations[18].scalar_flops | 524288 |
| stages[30].operations[18].special_ops | {} |
| stages[30].operations[18].source_detail.inputs_each[0] | 128 |
| stages[30].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[30].operations[18].source_detail.output[0] | 128 |
| stages[30].operations[18].source_detail.output[1] | 4096 |
| stages[31].id | layer:30 |
| stages[31].work.vector_fp32 | 17179904 |
| stages[31].work.special:rsqrt | 5376 |
| stages[31].work.interface_bytes | 438387200 |
| stages[31].work.matrix_bf16 | 49527390208 |
| stages[31].work.special:negate | 1900544 |
| stages[31].work.special:exp | 1837056 |
| stages[31].work.special:compare_max | 260096 |
| stages[31].work.special:mask_decisions | 524288 |
| stages[31].operations[0].name | input_layernorm |
| stages[31].operations[0].matrix_flops | 0 |
| stages[31].operations[0].input_precision | unknown (null) |
| stages[31].operations[0].accumulator_precision | unknown (null) |
| stages[31].operations[0].sparsity | unknown (null) |
| stages[31].operations[0].scalar_flops | 2097280 |
| stages[31].operations[0].special_ops.rsqrt | 128 |
| stages[31].operations[0].source_detail.input[0] | 128 |
| stages[31].operations[0].source_detail.input[1] | 4096 |
| stages[31].operations[0].source_detail.weight[0] | 4096 |
| stages[31].operations[0].source_detail.output[0] | 128 |
| stages[31].operations[0].source_detail.output[1] | 4096 |
| stages[31].operations[1].name | q_proj |
| stages[31].operations[1].matrix_flops | 4294967296 |
| stages[31].operations[1].input_precision | BF16 |
| stages[31].operations[1].accumulator_precision | FP32 |
| stages[31].operations[1].sparsity | dense |
| stages[31].operations[1].scalar_flops | 0 |
| stages[31].operations[1].special_ops | {} |
| stages[31].operations[1].source_detail.input[0] | 128 |
| stages[31].operations[1].source_detail.input[1] | 4096 |
| stages[31].operations[1].source_detail.weight_math[0] | 4096 |
| stages[31].operations[1].source_detail.weight_math[1] | 4096 |
| stages[31].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[31].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[1].source_detail.output[0] | 128 |
| stages[31].operations[1].source_detail.output[1] | 4096 |
| stages[31].operations[2].name | k_proj |
| stages[31].operations[2].matrix_flops | 1073741824 |
| stages[31].operations[2].input_precision | BF16 |
| stages[31].operations[2].accumulator_precision | FP32 |
| stages[31].operations[2].sparsity | dense |
| stages[31].operations[2].scalar_flops | 0 |
| stages[31].operations[2].special_ops | {} |
| stages[31].operations[2].source_detail.input[0] | 128 |
| stages[31].operations[2].source_detail.input[1] | 4096 |
| stages[31].operations[2].source_detail.weight_math[0] | 4096 |
| stages[31].operations[2].source_detail.weight_math[1] | 1024 |
| stages[31].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[31].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[2].source_detail.output[0] | 128 |
| stages[31].operations[2].source_detail.output[1] | 1024 |
| stages[31].operations[3].name | v_proj |
| stages[31].operations[3].matrix_flops | 1073741824 |
| stages[31].operations[3].input_precision | BF16 |
| stages[31].operations[3].accumulator_precision | FP32 |
| stages[31].operations[3].sparsity | dense |
| stages[31].operations[3].scalar_flops | 0 |
| stages[31].operations[3].special_ops | {} |
| stages[31].operations[3].source_detail.input[0] | 128 |
| stages[31].operations[3].source_detail.input[1] | 4096 |
| stages[31].operations[3].source_detail.weight_math[0] | 4096 |
| stages[31].operations[3].source_detail.weight_math[1] | 1024 |
| stages[31].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[31].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[3].source_detail.output[0] | 128 |
| stages[31].operations[3].source_detail.output[1] | 1024 |
| stages[31].operations[4].name | q_norm |
| stages[31].operations[4].matrix_flops | 0 |
| stages[31].operations[4].input_precision | unknown (null) |
| stages[31].operations[4].accumulator_precision | unknown (null) |
| stages[31].operations[4].sparsity | unknown (null) |
| stages[31].operations[4].scalar_flops | 2101248 |
| stages[31].operations[4].special_ops.rsqrt | 4096 |
| stages[31].operations[4].source_detail.input[0] | 4096 |
| stages[31].operations[4].source_detail.input[1] | 128 |
| stages[31].operations[4].source_detail.weight[0] | 128 |
| stages[31].operations[4].source_detail.output[0] | 4096 |
| stages[31].operations[4].source_detail.output[1] | 128 |
| stages[31].operations[5].name | k_norm |
| stages[31].operations[5].matrix_flops | 0 |
| stages[31].operations[5].input_precision | unknown (null) |
| stages[31].operations[5].accumulator_precision | unknown (null) |
| stages[31].operations[5].sparsity | unknown (null) |
| stages[31].operations[5].scalar_flops | 525312 |
| stages[31].operations[5].special_ops.rsqrt | 1024 |
| stages[31].operations[5].source_detail.input[0] | 1024 |
| stages[31].operations[5].source_detail.input[1] | 128 |
| stages[31].operations[5].source_detail.weight[0] | 128 |
| stages[31].operations[5].source_detail.output[0] | 1024 |
| stages[31].operations[5].source_detail.output[1] | 128 |
| stages[31].operations[6].name | apply_rope |
| stages[31].operations[6].matrix_flops | 0 |
| stages[31].operations[6].input_precision | unknown (null) |
| stages[31].operations[6].accumulator_precision | unknown (null) |
| stages[31].operations[6].sparsity | unknown (null) |
| stages[31].operations[6].scalar_flops | 1966080 |
| stages[31].operations[6].special_ops.negate | 327680 |
| stages[31].operations[6].source_detail.Q[0] | 1 |
| stages[31].operations[6].source_detail.Q[1] | 32 |
| stages[31].operations[6].source_detail.Q[2] | 128 |
| stages[31].operations[6].source_detail.Q[3] | 128 |
| stages[31].operations[6].source_detail.K[0] | 1 |
| stages[31].operations[6].source_detail.K[1] | 8 |
| stages[31].operations[6].source_detail.K[2] | 128 |
| stages[31].operations[6].source_detail.K[3] | 128 |
| stages[31].operations[7].name | kv_append |
| stages[31].operations[7].matrix_flops | 0 |
| stages[31].operations[7].input_precision | unknown (null) |
| stages[31].operations[7].accumulator_precision | unknown (null) |
| stages[31].operations[7].sparsity | unknown (null) |
| stages[31].operations[7].scalar_flops | 0 |
| stages[31].operations[7].special_ops | {} |
| stages[31].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[31].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[31].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[31].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[31].operations[8].name | qk |
| stages[31].operations[8].matrix_flops | 67633152 |
| stages[31].operations[8].input_precision | BF16 |
| stages[31].operations[8].accumulator_precision | FP32 |
| stages[31].operations[8].sparsity | dense |
| stages[31].operations[8].scalar_flops | 0 |
| stages[31].operations[8].special_ops | {} |
| stages[31].operations[8].source_detail.Q[0] | 1 |
| stages[31].operations[8].source_detail.Q[1] | 32 |
| stages[31].operations[8].source_detail.Q[2] | 128 |
| stages[31].operations[8].source_detail.Q[3] | 128 |
| stages[31].operations[8].source_detail.K_shared[0] | 1 |
| stages[31].operations[8].source_detail.K_shared[1] | 8 |
| stages[31].operations[8].source_detail.K_shared[2] | 128 |
| stages[31].operations[8].source_detail.K_shared[3] | 128 |
| stages[31].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[31].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[31].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[31].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[31].operations[9].name | score_scale_mask_softmax |
| stages[31].operations[9].matrix_flops | 0 |
| stages[31].operations[9].input_precision | unknown (null) |
| stages[31].operations[9].accumulator_precision | unknown (null) |
| stages[31].operations[9].sparsity | unknown (null) |
| stages[31].operations[9].scalar_flops | 1052672 |
| stages[31].operations[9].special_ops.exp | 264192 |
| stages[31].operations[9].special_ops.compare_max | 260096 |
| stages[31].operations[9].special_ops.mask_decisions | 524288 |
| stages[31].operations[9].source_detail.scores[0] | 1 |
| stages[31].operations[9].source_detail.scores[1] | 32 |
| stages[31].operations[9].source_detail.scores[2] | 128 |
| stages[31].operations[9].source_detail.scores[3] | 128 |
| stages[31].operations[10].name | pv |
| stages[31].operations[10].matrix_flops | 67633152 |
| stages[31].operations[10].input_precision | BF16 |
| stages[31].operations[10].accumulator_precision | FP32 |
| stages[31].operations[10].sparsity | dense |
| stages[31].operations[10].scalar_flops | 0 |
| stages[31].operations[10].special_ops | {} |
| stages[31].operations[10].source_detail.P[0] | 1 |
| stages[31].operations[10].source_detail.P[1] | 32 |
| stages[31].operations[10].source_detail.P[2] | 128 |
| stages[31].operations[10].source_detail.P[3] | 128 |
| stages[31].operations[10].source_detail.V_shared[0] | 1 |
| stages[31].operations[10].source_detail.V_shared[1] | 8 |
| stages[31].operations[10].source_detail.V_shared[2] | 128 |
| stages[31].operations[10].source_detail.V_shared[3] | 128 |
| stages[31].operations[10].source_detail.output[0] | 1 |
| stages[31].operations[10].source_detail.output[1] | 32 |
| stages[31].operations[10].source_detail.output[2] | 128 |
| stages[31].operations[10].source_detail.output[3] | 128 |
| stages[31].operations[11].name | o_proj |
| stages[31].operations[11].matrix_flops | 4294967296 |
| stages[31].operations[11].input_precision | BF16 |
| stages[31].operations[11].accumulator_precision | FP32 |
| stages[31].operations[11].sparsity | dense |
| stages[31].operations[11].scalar_flops | 0 |
| stages[31].operations[11].special_ops | {} |
| stages[31].operations[11].source_detail.input[0] | 128 |
| stages[31].operations[11].source_detail.input[1] | 4096 |
| stages[31].operations[11].source_detail.weight_math[0] | 4096 |
| stages[31].operations[11].source_detail.weight_math[1] | 4096 |
| stages[31].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[31].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[11].source_detail.output[0] | 128 |
| stages[31].operations[11].source_detail.output[1] | 4096 |
| stages[31].operations[12].name | attention_residual |
| stages[31].operations[12].matrix_flops | 0 |
| stages[31].operations[12].input_precision | unknown (null) |
| stages[31].operations[12].accumulator_precision | unknown (null) |
| stages[31].operations[12].sparsity | unknown (null) |
| stages[31].operations[12].scalar_flops | 524288 |
| stages[31].operations[12].special_ops | {} |
| stages[31].operations[12].source_detail.inputs_each[0] | 128 |
| stages[31].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[31].operations[12].source_detail.output[0] | 128 |
| stages[31].operations[12].source_detail.output[1] | 4096 |
| stages[31].operations[13].name | post_attention_layernorm |
| stages[31].operations[13].matrix_flops | 0 |
| stages[31].operations[13].input_precision | unknown (null) |
| stages[31].operations[13].accumulator_precision | unknown (null) |
| stages[31].operations[13].sparsity | unknown (null) |
| stages[31].operations[13].scalar_flops | 2097280 |
| stages[31].operations[13].special_ops.rsqrt | 128 |
| stages[31].operations[13].source_detail.input[0] | 128 |
| stages[31].operations[13].source_detail.input[1] | 4096 |
| stages[31].operations[13].source_detail.weight[0] | 4096 |
| stages[31].operations[13].source_detail.output[0] | 128 |
| stages[31].operations[13].source_detail.output[1] | 4096 |
| stages[31].operations[14].name | gate_proj |
| stages[31].operations[14].matrix_flops | 12884901888 |
| stages[31].operations[14].input_precision | BF16 |
| stages[31].operations[14].accumulator_precision | FP32 |
| stages[31].operations[14].sparsity | dense |
| stages[31].operations[14].scalar_flops | 0 |
| stages[31].operations[14].special_ops | {} |
| stages[31].operations[14].source_detail.input[0] | 128 |
| stages[31].operations[14].source_detail.input[1] | 4096 |
| stages[31].operations[14].source_detail.weight_math[0] | 4096 |
| stages[31].operations[14].source_detail.weight_math[1] | 12288 |
| stages[31].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[31].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[14].source_detail.output[0] | 128 |
| stages[31].operations[14].source_detail.output[1] | 12288 |
| stages[31].operations[15].name | up_proj |
| stages[31].operations[15].matrix_flops | 12884901888 |
| stages[31].operations[15].input_precision | BF16 |
| stages[31].operations[15].accumulator_precision | FP32 |
| stages[31].operations[15].sparsity | dense |
| stages[31].operations[15].scalar_flops | 0 |
| stages[31].operations[15].special_ops | {} |
| stages[31].operations[15].source_detail.input[0] | 128 |
| stages[31].operations[15].source_detail.input[1] | 4096 |
| stages[31].operations[15].source_detail.weight_math[0] | 4096 |
| stages[31].operations[15].source_detail.weight_math[1] | 12288 |
| stages[31].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[31].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[31].operations[15].source_detail.output[0] | 128 |
| stages[31].operations[15].source_detail.output[1] | 12288 |
| stages[31].operations[16].name | silu_mul |
| stages[31].operations[16].matrix_flops | 0 |
| stages[31].operations[16].input_precision | unknown (null) |
| stages[31].operations[16].accumulator_precision | unknown (null) |
| stages[31].operations[16].sparsity | unknown (null) |
| stages[31].operations[16].scalar_flops | 6291456 |
| stages[31].operations[16].special_ops.exp | 1572864 |
| stages[31].operations[16].special_ops.negate | 1572864 |
| stages[31].operations[16].source_detail.gate[0] | 128 |
| stages[31].operations[16].source_detail.gate[1] | 12288 |
| stages[31].operations[16].source_detail.up[0] | 128 |
| stages[31].operations[16].source_detail.up[1] | 12288 |
| stages[31].operations[16].source_detail.output[0] | 128 |
| stages[31].operations[16].source_detail.output[1] | 12288 |
| stages[31].operations[17].name | down_proj |
| stages[31].operations[17].matrix_flops | 12884901888 |
| stages[31].operations[17].input_precision | BF16 |
| stages[31].operations[17].accumulator_precision | FP32 |
| stages[31].operations[17].sparsity | dense |
| stages[31].operations[17].scalar_flops | 0 |
| stages[31].operations[17].special_ops | {} |
| stages[31].operations[17].source_detail.input[0] | 128 |
| stages[31].operations[17].source_detail.input[1] | 12288 |
| stages[31].operations[17].source_detail.weight_math[0] | 12288 |
| stages[31].operations[17].source_detail.weight_math[1] | 4096 |
| stages[31].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[31].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[31].operations[17].source_detail.output[0] | 128 |
| stages[31].operations[17].source_detail.output[1] | 4096 |
| stages[31].operations[18].name | ffn_residual |
| stages[31].operations[18].matrix_flops | 0 |
| stages[31].operations[18].input_precision | unknown (null) |
| stages[31].operations[18].accumulator_precision | unknown (null) |
| stages[31].operations[18].sparsity | unknown (null) |
| stages[31].operations[18].scalar_flops | 524288 |
| stages[31].operations[18].special_ops | {} |
| stages[31].operations[18].source_detail.inputs_each[0] | 128 |
| stages[31].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[31].operations[18].source_detail.output[0] | 128 |
| stages[31].operations[18].source_detail.output[1] | 4096 |
| stages[32].id | layer:31 |
| stages[32].work.vector_fp32 | 17179904 |
| stages[32].work.special:rsqrt | 5376 |
| stages[32].work.interface_bytes | 438387200 |
| stages[32].work.matrix_bf16 | 49527390208 |
| stages[32].work.special:negate | 1900544 |
| stages[32].work.special:exp | 1837056 |
| stages[32].work.special:compare_max | 260096 |
| stages[32].work.special:mask_decisions | 524288 |
| stages[32].operations[0].name | input_layernorm |
| stages[32].operations[0].matrix_flops | 0 |
| stages[32].operations[0].input_precision | unknown (null) |
| stages[32].operations[0].accumulator_precision | unknown (null) |
| stages[32].operations[0].sparsity | unknown (null) |
| stages[32].operations[0].scalar_flops | 2097280 |
| stages[32].operations[0].special_ops.rsqrt | 128 |
| stages[32].operations[0].source_detail.input[0] | 128 |
| stages[32].operations[0].source_detail.input[1] | 4096 |
| stages[32].operations[0].source_detail.weight[0] | 4096 |
| stages[32].operations[0].source_detail.output[0] | 128 |
| stages[32].operations[0].source_detail.output[1] | 4096 |
| stages[32].operations[1].name | q_proj |
| stages[32].operations[1].matrix_flops | 4294967296 |
| stages[32].operations[1].input_precision | BF16 |
| stages[32].operations[1].accumulator_precision | FP32 |
| stages[32].operations[1].sparsity | dense |
| stages[32].operations[1].scalar_flops | 0 |
| stages[32].operations[1].special_ops | {} |
| stages[32].operations[1].source_detail.input[0] | 128 |
| stages[32].operations[1].source_detail.input[1] | 4096 |
| stages[32].operations[1].source_detail.weight_math[0] | 4096 |
| stages[32].operations[1].source_detail.weight_math[1] | 4096 |
| stages[32].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[32].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[1].source_detail.output[0] | 128 |
| stages[32].operations[1].source_detail.output[1] | 4096 |
| stages[32].operations[2].name | k_proj |
| stages[32].operations[2].matrix_flops | 1073741824 |
| stages[32].operations[2].input_precision | BF16 |
| stages[32].operations[2].accumulator_precision | FP32 |
| stages[32].operations[2].sparsity | dense |
| stages[32].operations[2].scalar_flops | 0 |
| stages[32].operations[2].special_ops | {} |
| stages[32].operations[2].source_detail.input[0] | 128 |
| stages[32].operations[2].source_detail.input[1] | 4096 |
| stages[32].operations[2].source_detail.weight_math[0] | 4096 |
| stages[32].operations[2].source_detail.weight_math[1] | 1024 |
| stages[32].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[32].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[2].source_detail.output[0] | 128 |
| stages[32].operations[2].source_detail.output[1] | 1024 |
| stages[32].operations[3].name | v_proj |
| stages[32].operations[3].matrix_flops | 1073741824 |
| stages[32].operations[3].input_precision | BF16 |
| stages[32].operations[3].accumulator_precision | FP32 |
| stages[32].operations[3].sparsity | dense |
| stages[32].operations[3].scalar_flops | 0 |
| stages[32].operations[3].special_ops | {} |
| stages[32].operations[3].source_detail.input[0] | 128 |
| stages[32].operations[3].source_detail.input[1] | 4096 |
| stages[32].operations[3].source_detail.weight_math[0] | 4096 |
| stages[32].operations[3].source_detail.weight_math[1] | 1024 |
| stages[32].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[32].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[3].source_detail.output[0] | 128 |
| stages[32].operations[3].source_detail.output[1] | 1024 |
| stages[32].operations[4].name | q_norm |
| stages[32].operations[4].matrix_flops | 0 |
| stages[32].operations[4].input_precision | unknown (null) |
| stages[32].operations[4].accumulator_precision | unknown (null) |
| stages[32].operations[4].sparsity | unknown (null) |
| stages[32].operations[4].scalar_flops | 2101248 |
| stages[32].operations[4].special_ops.rsqrt | 4096 |
| stages[32].operations[4].source_detail.input[0] | 4096 |
| stages[32].operations[4].source_detail.input[1] | 128 |
| stages[32].operations[4].source_detail.weight[0] | 128 |
| stages[32].operations[4].source_detail.output[0] | 4096 |
| stages[32].operations[4].source_detail.output[1] | 128 |
| stages[32].operations[5].name | k_norm |
| stages[32].operations[5].matrix_flops | 0 |
| stages[32].operations[5].input_precision | unknown (null) |
| stages[32].operations[5].accumulator_precision | unknown (null) |
| stages[32].operations[5].sparsity | unknown (null) |
| stages[32].operations[5].scalar_flops | 525312 |
| stages[32].operations[5].special_ops.rsqrt | 1024 |
| stages[32].operations[5].source_detail.input[0] | 1024 |
| stages[32].operations[5].source_detail.input[1] | 128 |
| stages[32].operations[5].source_detail.weight[0] | 128 |
| stages[32].operations[5].source_detail.output[0] | 1024 |
| stages[32].operations[5].source_detail.output[1] | 128 |
| stages[32].operations[6].name | apply_rope |
| stages[32].operations[6].matrix_flops | 0 |
| stages[32].operations[6].input_precision | unknown (null) |
| stages[32].operations[6].accumulator_precision | unknown (null) |
| stages[32].operations[6].sparsity | unknown (null) |
| stages[32].operations[6].scalar_flops | 1966080 |
| stages[32].operations[6].special_ops.negate | 327680 |
| stages[32].operations[6].source_detail.Q[0] | 1 |
| stages[32].operations[6].source_detail.Q[1] | 32 |
| stages[32].operations[6].source_detail.Q[2] | 128 |
| stages[32].operations[6].source_detail.Q[3] | 128 |
| stages[32].operations[6].source_detail.K[0] | 1 |
| stages[32].operations[6].source_detail.K[1] | 8 |
| stages[32].operations[6].source_detail.K[2] | 128 |
| stages[32].operations[6].source_detail.K[3] | 128 |
| stages[32].operations[7].name | kv_append |
| stages[32].operations[7].matrix_flops | 0 |
| stages[32].operations[7].input_precision | unknown (null) |
| stages[32].operations[7].accumulator_precision | unknown (null) |
| stages[32].operations[7].sparsity | unknown (null) |
| stages[32].operations[7].scalar_flops | 0 |
| stages[32].operations[7].special_ops | {} |
| stages[32].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[32].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[32].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[32].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[32].operations[8].name | qk |
| stages[32].operations[8].matrix_flops | 67633152 |
| stages[32].operations[8].input_precision | BF16 |
| stages[32].operations[8].accumulator_precision | FP32 |
| stages[32].operations[8].sparsity | dense |
| stages[32].operations[8].scalar_flops | 0 |
| stages[32].operations[8].special_ops | {} |
| stages[32].operations[8].source_detail.Q[0] | 1 |
| stages[32].operations[8].source_detail.Q[1] | 32 |
| stages[32].operations[8].source_detail.Q[2] | 128 |
| stages[32].operations[8].source_detail.Q[3] | 128 |
| stages[32].operations[8].source_detail.K_shared[0] | 1 |
| stages[32].operations[8].source_detail.K_shared[1] | 8 |
| stages[32].operations[8].source_detail.K_shared[2] | 128 |
| stages[32].operations[8].source_detail.K_shared[3] | 128 |
| stages[32].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[32].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[32].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[32].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[32].operations[9].name | score_scale_mask_softmax |
| stages[32].operations[9].matrix_flops | 0 |
| stages[32].operations[9].input_precision | unknown (null) |
| stages[32].operations[9].accumulator_precision | unknown (null) |
| stages[32].operations[9].sparsity | unknown (null) |
| stages[32].operations[9].scalar_flops | 1052672 |
| stages[32].operations[9].special_ops.exp | 264192 |
| stages[32].operations[9].special_ops.compare_max | 260096 |
| stages[32].operations[9].special_ops.mask_decisions | 524288 |
| stages[32].operations[9].source_detail.scores[0] | 1 |
| stages[32].operations[9].source_detail.scores[1] | 32 |
| stages[32].operations[9].source_detail.scores[2] | 128 |
| stages[32].operations[9].source_detail.scores[3] | 128 |
| stages[32].operations[10].name | pv |
| stages[32].operations[10].matrix_flops | 67633152 |
| stages[32].operations[10].input_precision | BF16 |
| stages[32].operations[10].accumulator_precision | FP32 |
| stages[32].operations[10].sparsity | dense |
| stages[32].operations[10].scalar_flops | 0 |
| stages[32].operations[10].special_ops | {} |
| stages[32].operations[10].source_detail.P[0] | 1 |
| stages[32].operations[10].source_detail.P[1] | 32 |
| stages[32].operations[10].source_detail.P[2] | 128 |
| stages[32].operations[10].source_detail.P[3] | 128 |
| stages[32].operations[10].source_detail.V_shared[0] | 1 |
| stages[32].operations[10].source_detail.V_shared[1] | 8 |
| stages[32].operations[10].source_detail.V_shared[2] | 128 |
| stages[32].operations[10].source_detail.V_shared[3] | 128 |
| stages[32].operations[10].source_detail.output[0] | 1 |
| stages[32].operations[10].source_detail.output[1] | 32 |
| stages[32].operations[10].source_detail.output[2] | 128 |
| stages[32].operations[10].source_detail.output[3] | 128 |
| stages[32].operations[11].name | o_proj |
| stages[32].operations[11].matrix_flops | 4294967296 |
| stages[32].operations[11].input_precision | BF16 |
| stages[32].operations[11].accumulator_precision | FP32 |
| stages[32].operations[11].sparsity | dense |
| stages[32].operations[11].scalar_flops | 0 |
| stages[32].operations[11].special_ops | {} |
| stages[32].operations[11].source_detail.input[0] | 128 |
| stages[32].operations[11].source_detail.input[1] | 4096 |
| stages[32].operations[11].source_detail.weight_math[0] | 4096 |
| stages[32].operations[11].source_detail.weight_math[1] | 4096 |
| stages[32].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[32].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[11].source_detail.output[0] | 128 |
| stages[32].operations[11].source_detail.output[1] | 4096 |
| stages[32].operations[12].name | attention_residual |
| stages[32].operations[12].matrix_flops | 0 |
| stages[32].operations[12].input_precision | unknown (null) |
| stages[32].operations[12].accumulator_precision | unknown (null) |
| stages[32].operations[12].sparsity | unknown (null) |
| stages[32].operations[12].scalar_flops | 524288 |
| stages[32].operations[12].special_ops | {} |
| stages[32].operations[12].source_detail.inputs_each[0] | 128 |
| stages[32].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[32].operations[12].source_detail.output[0] | 128 |
| stages[32].operations[12].source_detail.output[1] | 4096 |
| stages[32].operations[13].name | post_attention_layernorm |
| stages[32].operations[13].matrix_flops | 0 |
| stages[32].operations[13].input_precision | unknown (null) |
| stages[32].operations[13].accumulator_precision | unknown (null) |
| stages[32].operations[13].sparsity | unknown (null) |
| stages[32].operations[13].scalar_flops | 2097280 |
| stages[32].operations[13].special_ops.rsqrt | 128 |
| stages[32].operations[13].source_detail.input[0] | 128 |
| stages[32].operations[13].source_detail.input[1] | 4096 |
| stages[32].operations[13].source_detail.weight[0] | 4096 |
| stages[32].operations[13].source_detail.output[0] | 128 |
| stages[32].operations[13].source_detail.output[1] | 4096 |
| stages[32].operations[14].name | gate_proj |
| stages[32].operations[14].matrix_flops | 12884901888 |
| stages[32].operations[14].input_precision | BF16 |
| stages[32].operations[14].accumulator_precision | FP32 |
| stages[32].operations[14].sparsity | dense |
| stages[32].operations[14].scalar_flops | 0 |
| stages[32].operations[14].special_ops | {} |
| stages[32].operations[14].source_detail.input[0] | 128 |
| stages[32].operations[14].source_detail.input[1] | 4096 |
| stages[32].operations[14].source_detail.weight_math[0] | 4096 |
| stages[32].operations[14].source_detail.weight_math[1] | 12288 |
| stages[32].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[32].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[14].source_detail.output[0] | 128 |
| stages[32].operations[14].source_detail.output[1] | 12288 |
| stages[32].operations[15].name | up_proj |
| stages[32].operations[15].matrix_flops | 12884901888 |
| stages[32].operations[15].input_precision | BF16 |
| stages[32].operations[15].accumulator_precision | FP32 |
| stages[32].operations[15].sparsity | dense |
| stages[32].operations[15].scalar_flops | 0 |
| stages[32].operations[15].special_ops | {} |
| stages[32].operations[15].source_detail.input[0] | 128 |
| stages[32].operations[15].source_detail.input[1] | 4096 |
| stages[32].operations[15].source_detail.weight_math[0] | 4096 |
| stages[32].operations[15].source_detail.weight_math[1] | 12288 |
| stages[32].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[32].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[32].operations[15].source_detail.output[0] | 128 |
| stages[32].operations[15].source_detail.output[1] | 12288 |
| stages[32].operations[16].name | silu_mul |
| stages[32].operations[16].matrix_flops | 0 |
| stages[32].operations[16].input_precision | unknown (null) |
| stages[32].operations[16].accumulator_precision | unknown (null) |
| stages[32].operations[16].sparsity | unknown (null) |
| stages[32].operations[16].scalar_flops | 6291456 |
| stages[32].operations[16].special_ops.exp | 1572864 |
| stages[32].operations[16].special_ops.negate | 1572864 |
| stages[32].operations[16].source_detail.gate[0] | 128 |
| stages[32].operations[16].source_detail.gate[1] | 12288 |
| stages[32].operations[16].source_detail.up[0] | 128 |
| stages[32].operations[16].source_detail.up[1] | 12288 |
| stages[32].operations[16].source_detail.output[0] | 128 |
| stages[32].operations[16].source_detail.output[1] | 12288 |
| stages[32].operations[17].name | down_proj |
| stages[32].operations[17].matrix_flops | 12884901888 |
| stages[32].operations[17].input_precision | BF16 |
| stages[32].operations[17].accumulator_precision | FP32 |
| stages[32].operations[17].sparsity | dense |
| stages[32].operations[17].scalar_flops | 0 |
| stages[32].operations[17].special_ops | {} |
| stages[32].operations[17].source_detail.input[0] | 128 |
| stages[32].operations[17].source_detail.input[1] | 12288 |
| stages[32].operations[17].source_detail.weight_math[0] | 12288 |
| stages[32].operations[17].source_detail.weight_math[1] | 4096 |
| stages[32].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[32].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[32].operations[17].source_detail.output[0] | 128 |
| stages[32].operations[17].source_detail.output[1] | 4096 |
| stages[32].operations[18].name | ffn_residual |
| stages[32].operations[18].matrix_flops | 0 |
| stages[32].operations[18].input_precision | unknown (null) |
| stages[32].operations[18].accumulator_precision | unknown (null) |
| stages[32].operations[18].sparsity | unknown (null) |
| stages[32].operations[18].scalar_flops | 524288 |
| stages[32].operations[18].special_ops | {} |
| stages[32].operations[18].source_detail.inputs_each[0] | 128 |
| stages[32].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[32].operations[18].source_detail.output[0] | 128 |
| stages[32].operations[18].source_detail.output[1] | 4096 |
| stages[33].id | layer:32 |
| stages[33].work.vector_fp32 | 17179904 |
| stages[33].work.special:rsqrt | 5376 |
| stages[33].work.interface_bytes | 438387200 |
| stages[33].work.matrix_bf16 | 49527390208 |
| stages[33].work.special:negate | 1900544 |
| stages[33].work.special:exp | 1837056 |
| stages[33].work.special:compare_max | 260096 |
| stages[33].work.special:mask_decisions | 524288 |
| stages[33].operations[0].name | input_layernorm |
| stages[33].operations[0].matrix_flops | 0 |
| stages[33].operations[0].input_precision | unknown (null) |
| stages[33].operations[0].accumulator_precision | unknown (null) |
| stages[33].operations[0].sparsity | unknown (null) |
| stages[33].operations[0].scalar_flops | 2097280 |
| stages[33].operations[0].special_ops.rsqrt | 128 |
| stages[33].operations[0].source_detail.input[0] | 128 |
| stages[33].operations[0].source_detail.input[1] | 4096 |
| stages[33].operations[0].source_detail.weight[0] | 4096 |
| stages[33].operations[0].source_detail.output[0] | 128 |
| stages[33].operations[0].source_detail.output[1] | 4096 |
| stages[33].operations[1].name | q_proj |
| stages[33].operations[1].matrix_flops | 4294967296 |
| stages[33].operations[1].input_precision | BF16 |
| stages[33].operations[1].accumulator_precision | FP32 |
| stages[33].operations[1].sparsity | dense |
| stages[33].operations[1].scalar_flops | 0 |
| stages[33].operations[1].special_ops | {} |
| stages[33].operations[1].source_detail.input[0] | 128 |
| stages[33].operations[1].source_detail.input[1] | 4096 |
| stages[33].operations[1].source_detail.weight_math[0] | 4096 |
| stages[33].operations[1].source_detail.weight_math[1] | 4096 |
| stages[33].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[33].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[1].source_detail.output[0] | 128 |
| stages[33].operations[1].source_detail.output[1] | 4096 |
| stages[33].operations[2].name | k_proj |
| stages[33].operations[2].matrix_flops | 1073741824 |
| stages[33].operations[2].input_precision | BF16 |
| stages[33].operations[2].accumulator_precision | FP32 |
| stages[33].operations[2].sparsity | dense |
| stages[33].operations[2].scalar_flops | 0 |
| stages[33].operations[2].special_ops | {} |
| stages[33].operations[2].source_detail.input[0] | 128 |
| stages[33].operations[2].source_detail.input[1] | 4096 |
| stages[33].operations[2].source_detail.weight_math[0] | 4096 |
| stages[33].operations[2].source_detail.weight_math[1] | 1024 |
| stages[33].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[33].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[2].source_detail.output[0] | 128 |
| stages[33].operations[2].source_detail.output[1] | 1024 |
| stages[33].operations[3].name | v_proj |
| stages[33].operations[3].matrix_flops | 1073741824 |
| stages[33].operations[3].input_precision | BF16 |
| stages[33].operations[3].accumulator_precision | FP32 |
| stages[33].operations[3].sparsity | dense |
| stages[33].operations[3].scalar_flops | 0 |
| stages[33].operations[3].special_ops | {} |
| stages[33].operations[3].source_detail.input[0] | 128 |
| stages[33].operations[3].source_detail.input[1] | 4096 |
| stages[33].operations[3].source_detail.weight_math[0] | 4096 |
| stages[33].operations[3].source_detail.weight_math[1] | 1024 |
| stages[33].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[33].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[3].source_detail.output[0] | 128 |
| stages[33].operations[3].source_detail.output[1] | 1024 |
| stages[33].operations[4].name | q_norm |
| stages[33].operations[4].matrix_flops | 0 |
| stages[33].operations[4].input_precision | unknown (null) |
| stages[33].operations[4].accumulator_precision | unknown (null) |
| stages[33].operations[4].sparsity | unknown (null) |
| stages[33].operations[4].scalar_flops | 2101248 |
| stages[33].operations[4].special_ops.rsqrt | 4096 |
| stages[33].operations[4].source_detail.input[0] | 4096 |
| stages[33].operations[4].source_detail.input[1] | 128 |
| stages[33].operations[4].source_detail.weight[0] | 128 |
| stages[33].operations[4].source_detail.output[0] | 4096 |
| stages[33].operations[4].source_detail.output[1] | 128 |
| stages[33].operations[5].name | k_norm |
| stages[33].operations[5].matrix_flops | 0 |
| stages[33].operations[5].input_precision | unknown (null) |
| stages[33].operations[5].accumulator_precision | unknown (null) |
| stages[33].operations[5].sparsity | unknown (null) |
| stages[33].operations[5].scalar_flops | 525312 |
| stages[33].operations[5].special_ops.rsqrt | 1024 |
| stages[33].operations[5].source_detail.input[0] | 1024 |
| stages[33].operations[5].source_detail.input[1] | 128 |
| stages[33].operations[5].source_detail.weight[0] | 128 |
| stages[33].operations[5].source_detail.output[0] | 1024 |
| stages[33].operations[5].source_detail.output[1] | 128 |
| stages[33].operations[6].name | apply_rope |
| stages[33].operations[6].matrix_flops | 0 |
| stages[33].operations[6].input_precision | unknown (null) |
| stages[33].operations[6].accumulator_precision | unknown (null) |
| stages[33].operations[6].sparsity | unknown (null) |
| stages[33].operations[6].scalar_flops | 1966080 |
| stages[33].operations[6].special_ops.negate | 327680 |
| stages[33].operations[6].source_detail.Q[0] | 1 |
| stages[33].operations[6].source_detail.Q[1] | 32 |
| stages[33].operations[6].source_detail.Q[2] | 128 |
| stages[33].operations[6].source_detail.Q[3] | 128 |
| stages[33].operations[6].source_detail.K[0] | 1 |
| stages[33].operations[6].source_detail.K[1] | 8 |
| stages[33].operations[6].source_detail.K[2] | 128 |
| stages[33].operations[6].source_detail.K[3] | 128 |
| stages[33].operations[7].name | kv_append |
| stages[33].operations[7].matrix_flops | 0 |
| stages[33].operations[7].input_precision | unknown (null) |
| stages[33].operations[7].accumulator_precision | unknown (null) |
| stages[33].operations[7].sparsity | unknown (null) |
| stages[33].operations[7].scalar_flops | 0 |
| stages[33].operations[7].special_ops | {} |
| stages[33].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[33].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[33].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[33].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[33].operations[8].name | qk |
| stages[33].operations[8].matrix_flops | 67633152 |
| stages[33].operations[8].input_precision | BF16 |
| stages[33].operations[8].accumulator_precision | FP32 |
| stages[33].operations[8].sparsity | dense |
| stages[33].operations[8].scalar_flops | 0 |
| stages[33].operations[8].special_ops | {} |
| stages[33].operations[8].source_detail.Q[0] | 1 |
| stages[33].operations[8].source_detail.Q[1] | 32 |
| stages[33].operations[8].source_detail.Q[2] | 128 |
| stages[33].operations[8].source_detail.Q[3] | 128 |
| stages[33].operations[8].source_detail.K_shared[0] | 1 |
| stages[33].operations[8].source_detail.K_shared[1] | 8 |
| stages[33].operations[8].source_detail.K_shared[2] | 128 |
| stages[33].operations[8].source_detail.K_shared[3] | 128 |
| stages[33].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[33].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[33].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[33].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[33].operations[9].name | score_scale_mask_softmax |
| stages[33].operations[9].matrix_flops | 0 |
| stages[33].operations[9].input_precision | unknown (null) |
| stages[33].operations[9].accumulator_precision | unknown (null) |
| stages[33].operations[9].sparsity | unknown (null) |
| stages[33].operations[9].scalar_flops | 1052672 |
| stages[33].operations[9].special_ops.exp | 264192 |
| stages[33].operations[9].special_ops.compare_max | 260096 |
| stages[33].operations[9].special_ops.mask_decisions | 524288 |
| stages[33].operations[9].source_detail.scores[0] | 1 |
| stages[33].operations[9].source_detail.scores[1] | 32 |
| stages[33].operations[9].source_detail.scores[2] | 128 |
| stages[33].operations[9].source_detail.scores[3] | 128 |
| stages[33].operations[10].name | pv |
| stages[33].operations[10].matrix_flops | 67633152 |
| stages[33].operations[10].input_precision | BF16 |
| stages[33].operations[10].accumulator_precision | FP32 |
| stages[33].operations[10].sparsity | dense |
| stages[33].operations[10].scalar_flops | 0 |
| stages[33].operations[10].special_ops | {} |
| stages[33].operations[10].source_detail.P[0] | 1 |
| stages[33].operations[10].source_detail.P[1] | 32 |
| stages[33].operations[10].source_detail.P[2] | 128 |
| stages[33].operations[10].source_detail.P[3] | 128 |
| stages[33].operations[10].source_detail.V_shared[0] | 1 |
| stages[33].operations[10].source_detail.V_shared[1] | 8 |
| stages[33].operations[10].source_detail.V_shared[2] | 128 |
| stages[33].operations[10].source_detail.V_shared[3] | 128 |
| stages[33].operations[10].source_detail.output[0] | 1 |
| stages[33].operations[10].source_detail.output[1] | 32 |
| stages[33].operations[10].source_detail.output[2] | 128 |
| stages[33].operations[10].source_detail.output[3] | 128 |
| stages[33].operations[11].name | o_proj |
| stages[33].operations[11].matrix_flops | 4294967296 |
| stages[33].operations[11].input_precision | BF16 |
| stages[33].operations[11].accumulator_precision | FP32 |
| stages[33].operations[11].sparsity | dense |
| stages[33].operations[11].scalar_flops | 0 |
| stages[33].operations[11].special_ops | {} |
| stages[33].operations[11].source_detail.input[0] | 128 |
| stages[33].operations[11].source_detail.input[1] | 4096 |
| stages[33].operations[11].source_detail.weight_math[0] | 4096 |
| stages[33].operations[11].source_detail.weight_math[1] | 4096 |
| stages[33].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[33].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[11].source_detail.output[0] | 128 |
| stages[33].operations[11].source_detail.output[1] | 4096 |
| stages[33].operations[12].name | attention_residual |
| stages[33].operations[12].matrix_flops | 0 |
| stages[33].operations[12].input_precision | unknown (null) |
| stages[33].operations[12].accumulator_precision | unknown (null) |
| stages[33].operations[12].sparsity | unknown (null) |
| stages[33].operations[12].scalar_flops | 524288 |
| stages[33].operations[12].special_ops | {} |
| stages[33].operations[12].source_detail.inputs_each[0] | 128 |
| stages[33].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[33].operations[12].source_detail.output[0] | 128 |
| stages[33].operations[12].source_detail.output[1] | 4096 |
| stages[33].operations[13].name | post_attention_layernorm |
| stages[33].operations[13].matrix_flops | 0 |
| stages[33].operations[13].input_precision | unknown (null) |
| stages[33].operations[13].accumulator_precision | unknown (null) |
| stages[33].operations[13].sparsity | unknown (null) |
| stages[33].operations[13].scalar_flops | 2097280 |
| stages[33].operations[13].special_ops.rsqrt | 128 |
| stages[33].operations[13].source_detail.input[0] | 128 |
| stages[33].operations[13].source_detail.input[1] | 4096 |
| stages[33].operations[13].source_detail.weight[0] | 4096 |
| stages[33].operations[13].source_detail.output[0] | 128 |
| stages[33].operations[13].source_detail.output[1] | 4096 |
| stages[33].operations[14].name | gate_proj |
| stages[33].operations[14].matrix_flops | 12884901888 |
| stages[33].operations[14].input_precision | BF16 |
| stages[33].operations[14].accumulator_precision | FP32 |
| stages[33].operations[14].sparsity | dense |
| stages[33].operations[14].scalar_flops | 0 |
| stages[33].operations[14].special_ops | {} |
| stages[33].operations[14].source_detail.input[0] | 128 |
| stages[33].operations[14].source_detail.input[1] | 4096 |
| stages[33].operations[14].source_detail.weight_math[0] | 4096 |
| stages[33].operations[14].source_detail.weight_math[1] | 12288 |
| stages[33].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[33].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[14].source_detail.output[0] | 128 |
| stages[33].operations[14].source_detail.output[1] | 12288 |
| stages[33].operations[15].name | up_proj |
| stages[33].operations[15].matrix_flops | 12884901888 |
| stages[33].operations[15].input_precision | BF16 |
| stages[33].operations[15].accumulator_precision | FP32 |
| stages[33].operations[15].sparsity | dense |
| stages[33].operations[15].scalar_flops | 0 |
| stages[33].operations[15].special_ops | {} |
| stages[33].operations[15].source_detail.input[0] | 128 |
| stages[33].operations[15].source_detail.input[1] | 4096 |
| stages[33].operations[15].source_detail.weight_math[0] | 4096 |
| stages[33].operations[15].source_detail.weight_math[1] | 12288 |
| stages[33].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[33].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[33].operations[15].source_detail.output[0] | 128 |
| stages[33].operations[15].source_detail.output[1] | 12288 |
| stages[33].operations[16].name | silu_mul |
| stages[33].operations[16].matrix_flops | 0 |
| stages[33].operations[16].input_precision | unknown (null) |
| stages[33].operations[16].accumulator_precision | unknown (null) |
| stages[33].operations[16].sparsity | unknown (null) |
| stages[33].operations[16].scalar_flops | 6291456 |
| stages[33].operations[16].special_ops.exp | 1572864 |
| stages[33].operations[16].special_ops.negate | 1572864 |
| stages[33].operations[16].source_detail.gate[0] | 128 |
| stages[33].operations[16].source_detail.gate[1] | 12288 |
| stages[33].operations[16].source_detail.up[0] | 128 |
| stages[33].operations[16].source_detail.up[1] | 12288 |
| stages[33].operations[16].source_detail.output[0] | 128 |
| stages[33].operations[16].source_detail.output[1] | 12288 |
| stages[33].operations[17].name | down_proj |
| stages[33].operations[17].matrix_flops | 12884901888 |
| stages[33].operations[17].input_precision | BF16 |
| stages[33].operations[17].accumulator_precision | FP32 |
| stages[33].operations[17].sparsity | dense |
| stages[33].operations[17].scalar_flops | 0 |
| stages[33].operations[17].special_ops | {} |
| stages[33].operations[17].source_detail.input[0] | 128 |
| stages[33].operations[17].source_detail.input[1] | 12288 |
| stages[33].operations[17].source_detail.weight_math[0] | 12288 |
| stages[33].operations[17].source_detail.weight_math[1] | 4096 |
| stages[33].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[33].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[33].operations[17].source_detail.output[0] | 128 |
| stages[33].operations[17].source_detail.output[1] | 4096 |
| stages[33].operations[18].name | ffn_residual |
| stages[33].operations[18].matrix_flops | 0 |
| stages[33].operations[18].input_precision | unknown (null) |
| stages[33].operations[18].accumulator_precision | unknown (null) |
| stages[33].operations[18].sparsity | unknown (null) |
| stages[33].operations[18].scalar_flops | 524288 |
| stages[33].operations[18].special_ops | {} |
| stages[33].operations[18].source_detail.inputs_each[0] | 128 |
| stages[33].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[33].operations[18].source_detail.output[0] | 128 |
| stages[33].operations[18].source_detail.output[1] | 4096 |
| stages[34].id | layer:33 |
| stages[34].work.vector_fp32 | 17179904 |
| stages[34].work.special:rsqrt | 5376 |
| stages[34].work.interface_bytes | 438387200 |
| stages[34].work.matrix_bf16 | 49527390208 |
| stages[34].work.special:negate | 1900544 |
| stages[34].work.special:exp | 1837056 |
| stages[34].work.special:compare_max | 260096 |
| stages[34].work.special:mask_decisions | 524288 |
| stages[34].operations[0].name | input_layernorm |
| stages[34].operations[0].matrix_flops | 0 |
| stages[34].operations[0].input_precision | unknown (null) |
| stages[34].operations[0].accumulator_precision | unknown (null) |
| stages[34].operations[0].sparsity | unknown (null) |
| stages[34].operations[0].scalar_flops | 2097280 |
| stages[34].operations[0].special_ops.rsqrt | 128 |
| stages[34].operations[0].source_detail.input[0] | 128 |
| stages[34].operations[0].source_detail.input[1] | 4096 |
| stages[34].operations[0].source_detail.weight[0] | 4096 |
| stages[34].operations[0].source_detail.output[0] | 128 |
| stages[34].operations[0].source_detail.output[1] | 4096 |
| stages[34].operations[1].name | q_proj |
| stages[34].operations[1].matrix_flops | 4294967296 |
| stages[34].operations[1].input_precision | BF16 |
| stages[34].operations[1].accumulator_precision | FP32 |
| stages[34].operations[1].sparsity | dense |
| stages[34].operations[1].scalar_flops | 0 |
| stages[34].operations[1].special_ops | {} |
| stages[34].operations[1].source_detail.input[0] | 128 |
| stages[34].operations[1].source_detail.input[1] | 4096 |
| stages[34].operations[1].source_detail.weight_math[0] | 4096 |
| stages[34].operations[1].source_detail.weight_math[1] | 4096 |
| stages[34].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[34].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[1].source_detail.output[0] | 128 |
| stages[34].operations[1].source_detail.output[1] | 4096 |
| stages[34].operations[2].name | k_proj |
| stages[34].operations[2].matrix_flops | 1073741824 |
| stages[34].operations[2].input_precision | BF16 |
| stages[34].operations[2].accumulator_precision | FP32 |
| stages[34].operations[2].sparsity | dense |
| stages[34].operations[2].scalar_flops | 0 |
| stages[34].operations[2].special_ops | {} |
| stages[34].operations[2].source_detail.input[0] | 128 |
| stages[34].operations[2].source_detail.input[1] | 4096 |
| stages[34].operations[2].source_detail.weight_math[0] | 4096 |
| stages[34].operations[2].source_detail.weight_math[1] | 1024 |
| stages[34].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[34].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[2].source_detail.output[0] | 128 |
| stages[34].operations[2].source_detail.output[1] | 1024 |
| stages[34].operations[3].name | v_proj |
| stages[34].operations[3].matrix_flops | 1073741824 |
| stages[34].operations[3].input_precision | BF16 |
| stages[34].operations[3].accumulator_precision | FP32 |
| stages[34].operations[3].sparsity | dense |
| stages[34].operations[3].scalar_flops | 0 |
| stages[34].operations[3].special_ops | {} |
| stages[34].operations[3].source_detail.input[0] | 128 |
| stages[34].operations[3].source_detail.input[1] | 4096 |
| stages[34].operations[3].source_detail.weight_math[0] | 4096 |
| stages[34].operations[3].source_detail.weight_math[1] | 1024 |
| stages[34].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[34].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[3].source_detail.output[0] | 128 |
| stages[34].operations[3].source_detail.output[1] | 1024 |
| stages[34].operations[4].name | q_norm |
| stages[34].operations[4].matrix_flops | 0 |
| stages[34].operations[4].input_precision | unknown (null) |
| stages[34].operations[4].accumulator_precision | unknown (null) |
| stages[34].operations[4].sparsity | unknown (null) |
| stages[34].operations[4].scalar_flops | 2101248 |
| stages[34].operations[4].special_ops.rsqrt | 4096 |
| stages[34].operations[4].source_detail.input[0] | 4096 |
| stages[34].operations[4].source_detail.input[1] | 128 |
| stages[34].operations[4].source_detail.weight[0] | 128 |
| stages[34].operations[4].source_detail.output[0] | 4096 |
| stages[34].operations[4].source_detail.output[1] | 128 |
| stages[34].operations[5].name | k_norm |
| stages[34].operations[5].matrix_flops | 0 |
| stages[34].operations[5].input_precision | unknown (null) |
| stages[34].operations[5].accumulator_precision | unknown (null) |
| stages[34].operations[5].sparsity | unknown (null) |
| stages[34].operations[5].scalar_flops | 525312 |
| stages[34].operations[5].special_ops.rsqrt | 1024 |
| stages[34].operations[5].source_detail.input[0] | 1024 |
| stages[34].operations[5].source_detail.input[1] | 128 |
| stages[34].operations[5].source_detail.weight[0] | 128 |
| stages[34].operations[5].source_detail.output[0] | 1024 |
| stages[34].operations[5].source_detail.output[1] | 128 |
| stages[34].operations[6].name | apply_rope |
| stages[34].operations[6].matrix_flops | 0 |
| stages[34].operations[6].input_precision | unknown (null) |
| stages[34].operations[6].accumulator_precision | unknown (null) |
| stages[34].operations[6].sparsity | unknown (null) |
| stages[34].operations[6].scalar_flops | 1966080 |
| stages[34].operations[6].special_ops.negate | 327680 |
| stages[34].operations[6].source_detail.Q[0] | 1 |
| stages[34].operations[6].source_detail.Q[1] | 32 |
| stages[34].operations[6].source_detail.Q[2] | 128 |
| stages[34].operations[6].source_detail.Q[3] | 128 |
| stages[34].operations[6].source_detail.K[0] | 1 |
| stages[34].operations[6].source_detail.K[1] | 8 |
| stages[34].operations[6].source_detail.K[2] | 128 |
| stages[34].operations[6].source_detail.K[3] | 128 |
| stages[34].operations[7].name | kv_append |
| stages[34].operations[7].matrix_flops | 0 |
| stages[34].operations[7].input_precision | unknown (null) |
| stages[34].operations[7].accumulator_precision | unknown (null) |
| stages[34].operations[7].sparsity | unknown (null) |
| stages[34].operations[7].scalar_flops | 0 |
| stages[34].operations[7].special_ops | {} |
| stages[34].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[34].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[34].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[34].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[34].operations[8].name | qk |
| stages[34].operations[8].matrix_flops | 67633152 |
| stages[34].operations[8].input_precision | BF16 |
| stages[34].operations[8].accumulator_precision | FP32 |
| stages[34].operations[8].sparsity | dense |
| stages[34].operations[8].scalar_flops | 0 |
| stages[34].operations[8].special_ops | {} |
| stages[34].operations[8].source_detail.Q[0] | 1 |
| stages[34].operations[8].source_detail.Q[1] | 32 |
| stages[34].operations[8].source_detail.Q[2] | 128 |
| stages[34].operations[8].source_detail.Q[3] | 128 |
| stages[34].operations[8].source_detail.K_shared[0] | 1 |
| stages[34].operations[8].source_detail.K_shared[1] | 8 |
| stages[34].operations[8].source_detail.K_shared[2] | 128 |
| stages[34].operations[8].source_detail.K_shared[3] | 128 |
| stages[34].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[34].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[34].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[34].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[34].operations[9].name | score_scale_mask_softmax |
| stages[34].operations[9].matrix_flops | 0 |
| stages[34].operations[9].input_precision | unknown (null) |
| stages[34].operations[9].accumulator_precision | unknown (null) |
| stages[34].operations[9].sparsity | unknown (null) |
| stages[34].operations[9].scalar_flops | 1052672 |
| stages[34].operations[9].special_ops.exp | 264192 |
| stages[34].operations[9].special_ops.compare_max | 260096 |
| stages[34].operations[9].special_ops.mask_decisions | 524288 |
| stages[34].operations[9].source_detail.scores[0] | 1 |
| stages[34].operations[9].source_detail.scores[1] | 32 |
| stages[34].operations[9].source_detail.scores[2] | 128 |
| stages[34].operations[9].source_detail.scores[3] | 128 |
| stages[34].operations[10].name | pv |
| stages[34].operations[10].matrix_flops | 67633152 |
| stages[34].operations[10].input_precision | BF16 |
| stages[34].operations[10].accumulator_precision | FP32 |
| stages[34].operations[10].sparsity | dense |
| stages[34].operations[10].scalar_flops | 0 |
| stages[34].operations[10].special_ops | {} |
| stages[34].operations[10].source_detail.P[0] | 1 |
| stages[34].operations[10].source_detail.P[1] | 32 |
| stages[34].operations[10].source_detail.P[2] | 128 |
| stages[34].operations[10].source_detail.P[3] | 128 |
| stages[34].operations[10].source_detail.V_shared[0] | 1 |
| stages[34].operations[10].source_detail.V_shared[1] | 8 |
| stages[34].operations[10].source_detail.V_shared[2] | 128 |
| stages[34].operations[10].source_detail.V_shared[3] | 128 |
| stages[34].operations[10].source_detail.output[0] | 1 |
| stages[34].operations[10].source_detail.output[1] | 32 |
| stages[34].operations[10].source_detail.output[2] | 128 |
| stages[34].operations[10].source_detail.output[3] | 128 |
| stages[34].operations[11].name | o_proj |
| stages[34].operations[11].matrix_flops | 4294967296 |
| stages[34].operations[11].input_precision | BF16 |
| stages[34].operations[11].accumulator_precision | FP32 |
| stages[34].operations[11].sparsity | dense |
| stages[34].operations[11].scalar_flops | 0 |
| stages[34].operations[11].special_ops | {} |
| stages[34].operations[11].source_detail.input[0] | 128 |
| stages[34].operations[11].source_detail.input[1] | 4096 |
| stages[34].operations[11].source_detail.weight_math[0] | 4096 |
| stages[34].operations[11].source_detail.weight_math[1] | 4096 |
| stages[34].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[34].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[11].source_detail.output[0] | 128 |
| stages[34].operations[11].source_detail.output[1] | 4096 |
| stages[34].operations[12].name | attention_residual |
| stages[34].operations[12].matrix_flops | 0 |
| stages[34].operations[12].input_precision | unknown (null) |
| stages[34].operations[12].accumulator_precision | unknown (null) |
| stages[34].operations[12].sparsity | unknown (null) |
| stages[34].operations[12].scalar_flops | 524288 |
| stages[34].operations[12].special_ops | {} |
| stages[34].operations[12].source_detail.inputs_each[0] | 128 |
| stages[34].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[34].operations[12].source_detail.output[0] | 128 |
| stages[34].operations[12].source_detail.output[1] | 4096 |
| stages[34].operations[13].name | post_attention_layernorm |
| stages[34].operations[13].matrix_flops | 0 |
| stages[34].operations[13].input_precision | unknown (null) |
| stages[34].operations[13].accumulator_precision | unknown (null) |
| stages[34].operations[13].sparsity | unknown (null) |
| stages[34].operations[13].scalar_flops | 2097280 |
| stages[34].operations[13].special_ops.rsqrt | 128 |
| stages[34].operations[13].source_detail.input[0] | 128 |
| stages[34].operations[13].source_detail.input[1] | 4096 |
| stages[34].operations[13].source_detail.weight[0] | 4096 |
| stages[34].operations[13].source_detail.output[0] | 128 |
| stages[34].operations[13].source_detail.output[1] | 4096 |
| stages[34].operations[14].name | gate_proj |
| stages[34].operations[14].matrix_flops | 12884901888 |
| stages[34].operations[14].input_precision | BF16 |
| stages[34].operations[14].accumulator_precision | FP32 |
| stages[34].operations[14].sparsity | dense |
| stages[34].operations[14].scalar_flops | 0 |
| stages[34].operations[14].special_ops | {} |
| stages[34].operations[14].source_detail.input[0] | 128 |
| stages[34].operations[14].source_detail.input[1] | 4096 |
| stages[34].operations[14].source_detail.weight_math[0] | 4096 |
| stages[34].operations[14].source_detail.weight_math[1] | 12288 |
| stages[34].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[34].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[14].source_detail.output[0] | 128 |
| stages[34].operations[14].source_detail.output[1] | 12288 |
| stages[34].operations[15].name | up_proj |
| stages[34].operations[15].matrix_flops | 12884901888 |
| stages[34].operations[15].input_precision | BF16 |
| stages[34].operations[15].accumulator_precision | FP32 |
| stages[34].operations[15].sparsity | dense |
| stages[34].operations[15].scalar_flops | 0 |
| stages[34].operations[15].special_ops | {} |
| stages[34].operations[15].source_detail.input[0] | 128 |
| stages[34].operations[15].source_detail.input[1] | 4096 |
| stages[34].operations[15].source_detail.weight_math[0] | 4096 |
| stages[34].operations[15].source_detail.weight_math[1] | 12288 |
| stages[34].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[34].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[34].operations[15].source_detail.output[0] | 128 |
| stages[34].operations[15].source_detail.output[1] | 12288 |
| stages[34].operations[16].name | silu_mul |
| stages[34].operations[16].matrix_flops | 0 |
| stages[34].operations[16].input_precision | unknown (null) |
| stages[34].operations[16].accumulator_precision | unknown (null) |
| stages[34].operations[16].sparsity | unknown (null) |
| stages[34].operations[16].scalar_flops | 6291456 |
| stages[34].operations[16].special_ops.exp | 1572864 |
| stages[34].operations[16].special_ops.negate | 1572864 |
| stages[34].operations[16].source_detail.gate[0] | 128 |
| stages[34].operations[16].source_detail.gate[1] | 12288 |
| stages[34].operations[16].source_detail.up[0] | 128 |
| stages[34].operations[16].source_detail.up[1] | 12288 |
| stages[34].operations[16].source_detail.output[0] | 128 |
| stages[34].operations[16].source_detail.output[1] | 12288 |
| stages[34].operations[17].name | down_proj |
| stages[34].operations[17].matrix_flops | 12884901888 |
| stages[34].operations[17].input_precision | BF16 |
| stages[34].operations[17].accumulator_precision | FP32 |
| stages[34].operations[17].sparsity | dense |
| stages[34].operations[17].scalar_flops | 0 |
| stages[34].operations[17].special_ops | {} |
| stages[34].operations[17].source_detail.input[0] | 128 |
| stages[34].operations[17].source_detail.input[1] | 12288 |
| stages[34].operations[17].source_detail.weight_math[0] | 12288 |
| stages[34].operations[17].source_detail.weight_math[1] | 4096 |
| stages[34].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[34].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[34].operations[17].source_detail.output[0] | 128 |
| stages[34].operations[17].source_detail.output[1] | 4096 |
| stages[34].operations[18].name | ffn_residual |
| stages[34].operations[18].matrix_flops | 0 |
| stages[34].operations[18].input_precision | unknown (null) |
| stages[34].operations[18].accumulator_precision | unknown (null) |
| stages[34].operations[18].sparsity | unknown (null) |
| stages[34].operations[18].scalar_flops | 524288 |
| stages[34].operations[18].special_ops | {} |
| stages[34].operations[18].source_detail.inputs_each[0] | 128 |
| stages[34].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[34].operations[18].source_detail.output[0] | 128 |
| stages[34].operations[18].source_detail.output[1] | 4096 |
| stages[35].id | layer:34 |
| stages[35].work.vector_fp32 | 17179904 |
| stages[35].work.special:rsqrt | 5376 |
| stages[35].work.interface_bytes | 438387200 |
| stages[35].work.matrix_bf16 | 49527390208 |
| stages[35].work.special:negate | 1900544 |
| stages[35].work.special:exp | 1837056 |
| stages[35].work.special:compare_max | 260096 |
| stages[35].work.special:mask_decisions | 524288 |
| stages[35].operations[0].name | input_layernorm |
| stages[35].operations[0].matrix_flops | 0 |
| stages[35].operations[0].input_precision | unknown (null) |
| stages[35].operations[0].accumulator_precision | unknown (null) |
| stages[35].operations[0].sparsity | unknown (null) |
| stages[35].operations[0].scalar_flops | 2097280 |
| stages[35].operations[0].special_ops.rsqrt | 128 |
| stages[35].operations[0].source_detail.input[0] | 128 |
| stages[35].operations[0].source_detail.input[1] | 4096 |
| stages[35].operations[0].source_detail.weight[0] | 4096 |
| stages[35].operations[0].source_detail.output[0] | 128 |
| stages[35].operations[0].source_detail.output[1] | 4096 |
| stages[35].operations[1].name | q_proj |
| stages[35].operations[1].matrix_flops | 4294967296 |
| stages[35].operations[1].input_precision | BF16 |
| stages[35].operations[1].accumulator_precision | FP32 |
| stages[35].operations[1].sparsity | dense |
| stages[35].operations[1].scalar_flops | 0 |
| stages[35].operations[1].special_ops | {} |
| stages[35].operations[1].source_detail.input[0] | 128 |
| stages[35].operations[1].source_detail.input[1] | 4096 |
| stages[35].operations[1].source_detail.weight_math[0] | 4096 |
| stages[35].operations[1].source_detail.weight_math[1] | 4096 |
| stages[35].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[35].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[1].source_detail.output[0] | 128 |
| stages[35].operations[1].source_detail.output[1] | 4096 |
| stages[35].operations[2].name | k_proj |
| stages[35].operations[2].matrix_flops | 1073741824 |
| stages[35].operations[2].input_precision | BF16 |
| stages[35].operations[2].accumulator_precision | FP32 |
| stages[35].operations[2].sparsity | dense |
| stages[35].operations[2].scalar_flops | 0 |
| stages[35].operations[2].special_ops | {} |
| stages[35].operations[2].source_detail.input[0] | 128 |
| stages[35].operations[2].source_detail.input[1] | 4096 |
| stages[35].operations[2].source_detail.weight_math[0] | 4096 |
| stages[35].operations[2].source_detail.weight_math[1] | 1024 |
| stages[35].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[35].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[2].source_detail.output[0] | 128 |
| stages[35].operations[2].source_detail.output[1] | 1024 |
| stages[35].operations[3].name | v_proj |
| stages[35].operations[3].matrix_flops | 1073741824 |
| stages[35].operations[3].input_precision | BF16 |
| stages[35].operations[3].accumulator_precision | FP32 |
| stages[35].operations[3].sparsity | dense |
| stages[35].operations[3].scalar_flops | 0 |
| stages[35].operations[3].special_ops | {} |
| stages[35].operations[3].source_detail.input[0] | 128 |
| stages[35].operations[3].source_detail.input[1] | 4096 |
| stages[35].operations[3].source_detail.weight_math[0] | 4096 |
| stages[35].operations[3].source_detail.weight_math[1] | 1024 |
| stages[35].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[35].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[3].source_detail.output[0] | 128 |
| stages[35].operations[3].source_detail.output[1] | 1024 |
| stages[35].operations[4].name | q_norm |
| stages[35].operations[4].matrix_flops | 0 |
| stages[35].operations[4].input_precision | unknown (null) |
| stages[35].operations[4].accumulator_precision | unknown (null) |
| stages[35].operations[4].sparsity | unknown (null) |
| stages[35].operations[4].scalar_flops | 2101248 |
| stages[35].operations[4].special_ops.rsqrt | 4096 |
| stages[35].operations[4].source_detail.input[0] | 4096 |
| stages[35].operations[4].source_detail.input[1] | 128 |
| stages[35].operations[4].source_detail.weight[0] | 128 |
| stages[35].operations[4].source_detail.output[0] | 4096 |
| stages[35].operations[4].source_detail.output[1] | 128 |
| stages[35].operations[5].name | k_norm |
| stages[35].operations[5].matrix_flops | 0 |
| stages[35].operations[5].input_precision | unknown (null) |
| stages[35].operations[5].accumulator_precision | unknown (null) |
| stages[35].operations[5].sparsity | unknown (null) |
| stages[35].operations[5].scalar_flops | 525312 |
| stages[35].operations[5].special_ops.rsqrt | 1024 |
| stages[35].operations[5].source_detail.input[0] | 1024 |
| stages[35].operations[5].source_detail.input[1] | 128 |
| stages[35].operations[5].source_detail.weight[0] | 128 |
| stages[35].operations[5].source_detail.output[0] | 1024 |
| stages[35].operations[5].source_detail.output[1] | 128 |
| stages[35].operations[6].name | apply_rope |
| stages[35].operations[6].matrix_flops | 0 |
| stages[35].operations[6].input_precision | unknown (null) |
| stages[35].operations[6].accumulator_precision | unknown (null) |
| stages[35].operations[6].sparsity | unknown (null) |
| stages[35].operations[6].scalar_flops | 1966080 |
| stages[35].operations[6].special_ops.negate | 327680 |
| stages[35].operations[6].source_detail.Q[0] | 1 |
| stages[35].operations[6].source_detail.Q[1] | 32 |
| stages[35].operations[6].source_detail.Q[2] | 128 |
| stages[35].operations[6].source_detail.Q[3] | 128 |
| stages[35].operations[6].source_detail.K[0] | 1 |
| stages[35].operations[6].source_detail.K[1] | 8 |
| stages[35].operations[6].source_detail.K[2] | 128 |
| stages[35].operations[6].source_detail.K[3] | 128 |
| stages[35].operations[7].name | kv_append |
| stages[35].operations[7].matrix_flops | 0 |
| stages[35].operations[7].input_precision | unknown (null) |
| stages[35].operations[7].accumulator_precision | unknown (null) |
| stages[35].operations[7].sparsity | unknown (null) |
| stages[35].operations[7].scalar_flops | 0 |
| stages[35].operations[7].special_ops | {} |
| stages[35].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[35].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[35].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[35].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[35].operations[8].name | qk |
| stages[35].operations[8].matrix_flops | 67633152 |
| stages[35].operations[8].input_precision | BF16 |
| stages[35].operations[8].accumulator_precision | FP32 |
| stages[35].operations[8].sparsity | dense |
| stages[35].operations[8].scalar_flops | 0 |
| stages[35].operations[8].special_ops | {} |
| stages[35].operations[8].source_detail.Q[0] | 1 |
| stages[35].operations[8].source_detail.Q[1] | 32 |
| stages[35].operations[8].source_detail.Q[2] | 128 |
| stages[35].operations[8].source_detail.Q[3] | 128 |
| stages[35].operations[8].source_detail.K_shared[0] | 1 |
| stages[35].operations[8].source_detail.K_shared[1] | 8 |
| stages[35].operations[8].source_detail.K_shared[2] | 128 |
| stages[35].operations[8].source_detail.K_shared[3] | 128 |
| stages[35].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[35].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[35].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[35].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[35].operations[9].name | score_scale_mask_softmax |
| stages[35].operations[9].matrix_flops | 0 |
| stages[35].operations[9].input_precision | unknown (null) |
| stages[35].operations[9].accumulator_precision | unknown (null) |
| stages[35].operations[9].sparsity | unknown (null) |
| stages[35].operations[9].scalar_flops | 1052672 |
| stages[35].operations[9].special_ops.exp | 264192 |
| stages[35].operations[9].special_ops.compare_max | 260096 |
| stages[35].operations[9].special_ops.mask_decisions | 524288 |
| stages[35].operations[9].source_detail.scores[0] | 1 |
| stages[35].operations[9].source_detail.scores[1] | 32 |
| stages[35].operations[9].source_detail.scores[2] | 128 |
| stages[35].operations[9].source_detail.scores[3] | 128 |
| stages[35].operations[10].name | pv |
| stages[35].operations[10].matrix_flops | 67633152 |
| stages[35].operations[10].input_precision | BF16 |
| stages[35].operations[10].accumulator_precision | FP32 |
| stages[35].operations[10].sparsity | dense |
| stages[35].operations[10].scalar_flops | 0 |
| stages[35].operations[10].special_ops | {} |
| stages[35].operations[10].source_detail.P[0] | 1 |
| stages[35].operations[10].source_detail.P[1] | 32 |
| stages[35].operations[10].source_detail.P[2] | 128 |
| stages[35].operations[10].source_detail.P[3] | 128 |
| stages[35].operations[10].source_detail.V_shared[0] | 1 |
| stages[35].operations[10].source_detail.V_shared[1] | 8 |
| stages[35].operations[10].source_detail.V_shared[2] | 128 |
| stages[35].operations[10].source_detail.V_shared[3] | 128 |
| stages[35].operations[10].source_detail.output[0] | 1 |
| stages[35].operations[10].source_detail.output[1] | 32 |
| stages[35].operations[10].source_detail.output[2] | 128 |
| stages[35].operations[10].source_detail.output[3] | 128 |
| stages[35].operations[11].name | o_proj |
| stages[35].operations[11].matrix_flops | 4294967296 |
| stages[35].operations[11].input_precision | BF16 |
| stages[35].operations[11].accumulator_precision | FP32 |
| stages[35].operations[11].sparsity | dense |
| stages[35].operations[11].scalar_flops | 0 |
| stages[35].operations[11].special_ops | {} |
| stages[35].operations[11].source_detail.input[0] | 128 |
| stages[35].operations[11].source_detail.input[1] | 4096 |
| stages[35].operations[11].source_detail.weight_math[0] | 4096 |
| stages[35].operations[11].source_detail.weight_math[1] | 4096 |
| stages[35].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[35].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[11].source_detail.output[0] | 128 |
| stages[35].operations[11].source_detail.output[1] | 4096 |
| stages[35].operations[12].name | attention_residual |
| stages[35].operations[12].matrix_flops | 0 |
| stages[35].operations[12].input_precision | unknown (null) |
| stages[35].operations[12].accumulator_precision | unknown (null) |
| stages[35].operations[12].sparsity | unknown (null) |
| stages[35].operations[12].scalar_flops | 524288 |
| stages[35].operations[12].special_ops | {} |
| stages[35].operations[12].source_detail.inputs_each[0] | 128 |
| stages[35].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[35].operations[12].source_detail.output[0] | 128 |
| stages[35].operations[12].source_detail.output[1] | 4096 |
| stages[35].operations[13].name | post_attention_layernorm |
| stages[35].operations[13].matrix_flops | 0 |
| stages[35].operations[13].input_precision | unknown (null) |
| stages[35].operations[13].accumulator_precision | unknown (null) |
| stages[35].operations[13].sparsity | unknown (null) |
| stages[35].operations[13].scalar_flops | 2097280 |
| stages[35].operations[13].special_ops.rsqrt | 128 |
| stages[35].operations[13].source_detail.input[0] | 128 |
| stages[35].operations[13].source_detail.input[1] | 4096 |
| stages[35].operations[13].source_detail.weight[0] | 4096 |
| stages[35].operations[13].source_detail.output[0] | 128 |
| stages[35].operations[13].source_detail.output[1] | 4096 |
| stages[35].operations[14].name | gate_proj |
| stages[35].operations[14].matrix_flops | 12884901888 |
| stages[35].operations[14].input_precision | BF16 |
| stages[35].operations[14].accumulator_precision | FP32 |
| stages[35].operations[14].sparsity | dense |
| stages[35].operations[14].scalar_flops | 0 |
| stages[35].operations[14].special_ops | {} |
| stages[35].operations[14].source_detail.input[0] | 128 |
| stages[35].operations[14].source_detail.input[1] | 4096 |
| stages[35].operations[14].source_detail.weight_math[0] | 4096 |
| stages[35].operations[14].source_detail.weight_math[1] | 12288 |
| stages[35].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[35].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[14].source_detail.output[0] | 128 |
| stages[35].operations[14].source_detail.output[1] | 12288 |
| stages[35].operations[15].name | up_proj |
| stages[35].operations[15].matrix_flops | 12884901888 |
| stages[35].operations[15].input_precision | BF16 |
| stages[35].operations[15].accumulator_precision | FP32 |
| stages[35].operations[15].sparsity | dense |
| stages[35].operations[15].scalar_flops | 0 |
| stages[35].operations[15].special_ops | {} |
| stages[35].operations[15].source_detail.input[0] | 128 |
| stages[35].operations[15].source_detail.input[1] | 4096 |
| stages[35].operations[15].source_detail.weight_math[0] | 4096 |
| stages[35].operations[15].source_detail.weight_math[1] | 12288 |
| stages[35].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[35].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[35].operations[15].source_detail.output[0] | 128 |
| stages[35].operations[15].source_detail.output[1] | 12288 |
| stages[35].operations[16].name | silu_mul |
| stages[35].operations[16].matrix_flops | 0 |
| stages[35].operations[16].input_precision | unknown (null) |
| stages[35].operations[16].accumulator_precision | unknown (null) |
| stages[35].operations[16].sparsity | unknown (null) |
| stages[35].operations[16].scalar_flops | 6291456 |
| stages[35].operations[16].special_ops.exp | 1572864 |
| stages[35].operations[16].special_ops.negate | 1572864 |
| stages[35].operations[16].source_detail.gate[0] | 128 |
| stages[35].operations[16].source_detail.gate[1] | 12288 |
| stages[35].operations[16].source_detail.up[0] | 128 |
| stages[35].operations[16].source_detail.up[1] | 12288 |
| stages[35].operations[16].source_detail.output[0] | 128 |
| stages[35].operations[16].source_detail.output[1] | 12288 |
| stages[35].operations[17].name | down_proj |
| stages[35].operations[17].matrix_flops | 12884901888 |
| stages[35].operations[17].input_precision | BF16 |
| stages[35].operations[17].accumulator_precision | FP32 |
| stages[35].operations[17].sparsity | dense |
| stages[35].operations[17].scalar_flops | 0 |
| stages[35].operations[17].special_ops | {} |
| stages[35].operations[17].source_detail.input[0] | 128 |
| stages[35].operations[17].source_detail.input[1] | 12288 |
| stages[35].operations[17].source_detail.weight_math[0] | 12288 |
| stages[35].operations[17].source_detail.weight_math[1] | 4096 |
| stages[35].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[35].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[35].operations[17].source_detail.output[0] | 128 |
| stages[35].operations[17].source_detail.output[1] | 4096 |
| stages[35].operations[18].name | ffn_residual |
| stages[35].operations[18].matrix_flops | 0 |
| stages[35].operations[18].input_precision | unknown (null) |
| stages[35].operations[18].accumulator_precision | unknown (null) |
| stages[35].operations[18].sparsity | unknown (null) |
| stages[35].operations[18].scalar_flops | 524288 |
| stages[35].operations[18].special_ops | {} |
| stages[35].operations[18].source_detail.inputs_each[0] | 128 |
| stages[35].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[35].operations[18].source_detail.output[0] | 128 |
| stages[35].operations[18].source_detail.output[1] | 4096 |
| stages[36].id | layer:35 |
| stages[36].work.vector_fp32 | 17179904 |
| stages[36].work.special:rsqrt | 5376 |
| stages[36].work.interface_bytes | 438387200 |
| stages[36].work.matrix_bf16 | 49527390208 |
| stages[36].work.special:negate | 1900544 |
| stages[36].work.special:exp | 1837056 |
| stages[36].work.special:compare_max | 260096 |
| stages[36].work.special:mask_decisions | 524288 |
| stages[36].operations[0].name | input_layernorm |
| stages[36].operations[0].matrix_flops | 0 |
| stages[36].operations[0].input_precision | unknown (null) |
| stages[36].operations[0].accumulator_precision | unknown (null) |
| stages[36].operations[0].sparsity | unknown (null) |
| stages[36].operations[0].scalar_flops | 2097280 |
| stages[36].operations[0].special_ops.rsqrt | 128 |
| stages[36].operations[0].source_detail.input[0] | 128 |
| stages[36].operations[0].source_detail.input[1] | 4096 |
| stages[36].operations[0].source_detail.weight[0] | 4096 |
| stages[36].operations[0].source_detail.output[0] | 128 |
| stages[36].operations[0].source_detail.output[1] | 4096 |
| stages[36].operations[1].name | q_proj |
| stages[36].operations[1].matrix_flops | 4294967296 |
| stages[36].operations[1].input_precision | BF16 |
| stages[36].operations[1].accumulator_precision | FP32 |
| stages[36].operations[1].sparsity | dense |
| stages[36].operations[1].scalar_flops | 0 |
| stages[36].operations[1].special_ops | {} |
| stages[36].operations[1].source_detail.input[0] | 128 |
| stages[36].operations[1].source_detail.input[1] | 4096 |
| stages[36].operations[1].source_detail.weight_math[0] | 4096 |
| stages[36].operations[1].source_detail.weight_math[1] | 4096 |
| stages[36].operations[1].source_detail.weight_storage[0] | 4096 |
| stages[36].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[1].source_detail.output[0] | 128 |
| stages[36].operations[1].source_detail.output[1] | 4096 |
| stages[36].operations[2].name | k_proj |
| stages[36].operations[2].matrix_flops | 1073741824 |
| stages[36].operations[2].input_precision | BF16 |
| stages[36].operations[2].accumulator_precision | FP32 |
| stages[36].operations[2].sparsity | dense |
| stages[36].operations[2].scalar_flops | 0 |
| stages[36].operations[2].special_ops | {} |
| stages[36].operations[2].source_detail.input[0] | 128 |
| stages[36].operations[2].source_detail.input[1] | 4096 |
| stages[36].operations[2].source_detail.weight_math[0] | 4096 |
| stages[36].operations[2].source_detail.weight_math[1] | 1024 |
| stages[36].operations[2].source_detail.weight_storage[0] | 1024 |
| stages[36].operations[2].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[2].source_detail.output[0] | 128 |
| stages[36].operations[2].source_detail.output[1] | 1024 |
| stages[36].operations[3].name | v_proj |
| stages[36].operations[3].matrix_flops | 1073741824 |
| stages[36].operations[3].input_precision | BF16 |
| stages[36].operations[3].accumulator_precision | FP32 |
| stages[36].operations[3].sparsity | dense |
| stages[36].operations[3].scalar_flops | 0 |
| stages[36].operations[3].special_ops | {} |
| stages[36].operations[3].source_detail.input[0] | 128 |
| stages[36].operations[3].source_detail.input[1] | 4096 |
| stages[36].operations[3].source_detail.weight_math[0] | 4096 |
| stages[36].operations[3].source_detail.weight_math[1] | 1024 |
| stages[36].operations[3].source_detail.weight_storage[0] | 1024 |
| stages[36].operations[3].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[3].source_detail.output[0] | 128 |
| stages[36].operations[3].source_detail.output[1] | 1024 |
| stages[36].operations[4].name | q_norm |
| stages[36].operations[4].matrix_flops | 0 |
| stages[36].operations[4].input_precision | unknown (null) |
| stages[36].operations[4].accumulator_precision | unknown (null) |
| stages[36].operations[4].sparsity | unknown (null) |
| stages[36].operations[4].scalar_flops | 2101248 |
| stages[36].operations[4].special_ops.rsqrt | 4096 |
| stages[36].operations[4].source_detail.input[0] | 4096 |
| stages[36].operations[4].source_detail.input[1] | 128 |
| stages[36].operations[4].source_detail.weight[0] | 128 |
| stages[36].operations[4].source_detail.output[0] | 4096 |
| stages[36].operations[4].source_detail.output[1] | 128 |
| stages[36].operations[5].name | k_norm |
| stages[36].operations[5].matrix_flops | 0 |
| stages[36].operations[5].input_precision | unknown (null) |
| stages[36].operations[5].accumulator_precision | unknown (null) |
| stages[36].operations[5].sparsity | unknown (null) |
| stages[36].operations[5].scalar_flops | 525312 |
| stages[36].operations[5].special_ops.rsqrt | 1024 |
| stages[36].operations[5].source_detail.input[0] | 1024 |
| stages[36].operations[5].source_detail.input[1] | 128 |
| stages[36].operations[5].source_detail.weight[0] | 128 |
| stages[36].operations[5].source_detail.output[0] | 1024 |
| stages[36].operations[5].source_detail.output[1] | 128 |
| stages[36].operations[6].name | apply_rope |
| stages[36].operations[6].matrix_flops | 0 |
| stages[36].operations[6].input_precision | unknown (null) |
| stages[36].operations[6].accumulator_precision | unknown (null) |
| stages[36].operations[6].sparsity | unknown (null) |
| stages[36].operations[6].scalar_flops | 1966080 |
| stages[36].operations[6].special_ops.negate | 327680 |
| stages[36].operations[6].source_detail.Q[0] | 1 |
| stages[36].operations[6].source_detail.Q[1] | 32 |
| stages[36].operations[6].source_detail.Q[2] | 128 |
| stages[36].operations[6].source_detail.Q[3] | 128 |
| stages[36].operations[6].source_detail.K[0] | 1 |
| stages[36].operations[6].source_detail.K[1] | 8 |
| stages[36].operations[6].source_detail.K[2] | 128 |
| stages[36].operations[6].source_detail.K[3] | 128 |
| stages[36].operations[7].name | kv_append |
| stages[36].operations[7].matrix_flops | 0 |
| stages[36].operations[7].input_precision | unknown (null) |
| stages[36].operations[7].accumulator_precision | unknown (null) |
| stages[36].operations[7].sparsity | unknown (null) |
| stages[36].operations[7].scalar_flops | 0 |
| stages[36].operations[7].special_ops | {} |
| stages[36].operations[7].source_detail.new_K_and_V_each[0] | 1 |
| stages[36].operations[7].source_detail.new_K_and_V_each[1] | 8 |
| stages[36].operations[7].source_detail.new_K_and_V_each[2] | 128 |
| stages[36].operations[7].source_detail.new_K_and_V_each[3] | 128 |
| stages[36].operations[8].name | qk |
| stages[36].operations[8].matrix_flops | 67633152 |
| stages[36].operations[8].input_precision | BF16 |
| stages[36].operations[8].accumulator_precision | FP32 |
| stages[36].operations[8].sparsity | dense |
| stages[36].operations[8].scalar_flops | 0 |
| stages[36].operations[8].special_ops | {} |
| stages[36].operations[8].source_detail.Q[0] | 1 |
| stages[36].operations[8].source_detail.Q[1] | 32 |
| stages[36].operations[8].source_detail.Q[2] | 128 |
| stages[36].operations[8].source_detail.Q[3] | 128 |
| stages[36].operations[8].source_detail.K_shared[0] | 1 |
| stages[36].operations[8].source_detail.K_shared[1] | 8 |
| stages[36].operations[8].source_detail.K_shared[2] | 128 |
| stages[36].operations[8].source_detail.K_shared[3] | 128 |
| stages[36].operations[8].source_detail.scores_rectangular[0] | 1 |
| stages[36].operations[8].source_detail.scores_rectangular[1] | 32 |
| stages[36].operations[8].source_detail.scores_rectangular[2] | 128 |
| stages[36].operations[8].source_detail.scores_rectangular[3] | 128 |
| stages[36].operations[9].name | score_scale_mask_softmax |
| stages[36].operations[9].matrix_flops | 0 |
| stages[36].operations[9].input_precision | unknown (null) |
| stages[36].operations[9].accumulator_precision | unknown (null) |
| stages[36].operations[9].sparsity | unknown (null) |
| stages[36].operations[9].scalar_flops | 1052672 |
| stages[36].operations[9].special_ops.exp | 264192 |
| stages[36].operations[9].special_ops.compare_max | 260096 |
| stages[36].operations[9].special_ops.mask_decisions | 524288 |
| stages[36].operations[9].source_detail.scores[0] | 1 |
| stages[36].operations[9].source_detail.scores[1] | 32 |
| stages[36].operations[9].source_detail.scores[2] | 128 |
| stages[36].operations[9].source_detail.scores[3] | 128 |
| stages[36].operations[10].name | pv |
| stages[36].operations[10].matrix_flops | 67633152 |
| stages[36].operations[10].input_precision | BF16 |
| stages[36].operations[10].accumulator_precision | FP32 |
| stages[36].operations[10].sparsity | dense |
| stages[36].operations[10].scalar_flops | 0 |
| stages[36].operations[10].special_ops | {} |
| stages[36].operations[10].source_detail.P[0] | 1 |
| stages[36].operations[10].source_detail.P[1] | 32 |
| stages[36].operations[10].source_detail.P[2] | 128 |
| stages[36].operations[10].source_detail.P[3] | 128 |
| stages[36].operations[10].source_detail.V_shared[0] | 1 |
| stages[36].operations[10].source_detail.V_shared[1] | 8 |
| stages[36].operations[10].source_detail.V_shared[2] | 128 |
| stages[36].operations[10].source_detail.V_shared[3] | 128 |
| stages[36].operations[10].source_detail.output[0] | 1 |
| stages[36].operations[10].source_detail.output[1] | 32 |
| stages[36].operations[10].source_detail.output[2] | 128 |
| stages[36].operations[10].source_detail.output[3] | 128 |
| stages[36].operations[11].name | o_proj |
| stages[36].operations[11].matrix_flops | 4294967296 |
| stages[36].operations[11].input_precision | BF16 |
| stages[36].operations[11].accumulator_precision | FP32 |
| stages[36].operations[11].sparsity | dense |
| stages[36].operations[11].scalar_flops | 0 |
| stages[36].operations[11].special_ops | {} |
| stages[36].operations[11].source_detail.input[0] | 128 |
| stages[36].operations[11].source_detail.input[1] | 4096 |
| stages[36].operations[11].source_detail.weight_math[0] | 4096 |
| stages[36].operations[11].source_detail.weight_math[1] | 4096 |
| stages[36].operations[11].source_detail.weight_storage[0] | 4096 |
| stages[36].operations[11].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[11].source_detail.output[0] | 128 |
| stages[36].operations[11].source_detail.output[1] | 4096 |
| stages[36].operations[12].name | attention_residual |
| stages[36].operations[12].matrix_flops | 0 |
| stages[36].operations[12].input_precision | unknown (null) |
| stages[36].operations[12].accumulator_precision | unknown (null) |
| stages[36].operations[12].sparsity | unknown (null) |
| stages[36].operations[12].scalar_flops | 524288 |
| stages[36].operations[12].special_ops | {} |
| stages[36].operations[12].source_detail.inputs_each[0] | 128 |
| stages[36].operations[12].source_detail.inputs_each[1] | 4096 |
| stages[36].operations[12].source_detail.output[0] | 128 |
| stages[36].operations[12].source_detail.output[1] | 4096 |
| stages[36].operations[13].name | post_attention_layernorm |
| stages[36].operations[13].matrix_flops | 0 |
| stages[36].operations[13].input_precision | unknown (null) |
| stages[36].operations[13].accumulator_precision | unknown (null) |
| stages[36].operations[13].sparsity | unknown (null) |
| stages[36].operations[13].scalar_flops | 2097280 |
| stages[36].operations[13].special_ops.rsqrt | 128 |
| stages[36].operations[13].source_detail.input[0] | 128 |
| stages[36].operations[13].source_detail.input[1] | 4096 |
| stages[36].operations[13].source_detail.weight[0] | 4096 |
| stages[36].operations[13].source_detail.output[0] | 128 |
| stages[36].operations[13].source_detail.output[1] | 4096 |
| stages[36].operations[14].name | gate_proj |
| stages[36].operations[14].matrix_flops | 12884901888 |
| stages[36].operations[14].input_precision | BF16 |
| stages[36].operations[14].accumulator_precision | FP32 |
| stages[36].operations[14].sparsity | dense |
| stages[36].operations[14].scalar_flops | 0 |
| stages[36].operations[14].special_ops | {} |
| stages[36].operations[14].source_detail.input[0] | 128 |
| stages[36].operations[14].source_detail.input[1] | 4096 |
| stages[36].operations[14].source_detail.weight_math[0] | 4096 |
| stages[36].operations[14].source_detail.weight_math[1] | 12288 |
| stages[36].operations[14].source_detail.weight_storage[0] | 12288 |
| stages[36].operations[14].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[14].source_detail.output[0] | 128 |
| stages[36].operations[14].source_detail.output[1] | 12288 |
| stages[36].operations[15].name | up_proj |
| stages[36].operations[15].matrix_flops | 12884901888 |
| stages[36].operations[15].input_precision | BF16 |
| stages[36].operations[15].accumulator_precision | FP32 |
| stages[36].operations[15].sparsity | dense |
| stages[36].operations[15].scalar_flops | 0 |
| stages[36].operations[15].special_ops | {} |
| stages[36].operations[15].source_detail.input[0] | 128 |
| stages[36].operations[15].source_detail.input[1] | 4096 |
| stages[36].operations[15].source_detail.weight_math[0] | 4096 |
| stages[36].operations[15].source_detail.weight_math[1] | 12288 |
| stages[36].operations[15].source_detail.weight_storage[0] | 12288 |
| stages[36].operations[15].source_detail.weight_storage[1] | 4096 |
| stages[36].operations[15].source_detail.output[0] | 128 |
| stages[36].operations[15].source_detail.output[1] | 12288 |
| stages[36].operations[16].name | silu_mul |
| stages[36].operations[16].matrix_flops | 0 |
| stages[36].operations[16].input_precision | unknown (null) |
| stages[36].operations[16].accumulator_precision | unknown (null) |
| stages[36].operations[16].sparsity | unknown (null) |
| stages[36].operations[16].scalar_flops | 6291456 |
| stages[36].operations[16].special_ops.exp | 1572864 |
| stages[36].operations[16].special_ops.negate | 1572864 |
| stages[36].operations[16].source_detail.gate[0] | 128 |
| stages[36].operations[16].source_detail.gate[1] | 12288 |
| stages[36].operations[16].source_detail.up[0] | 128 |
| stages[36].operations[16].source_detail.up[1] | 12288 |
| stages[36].operations[16].source_detail.output[0] | 128 |
| stages[36].operations[16].source_detail.output[1] | 12288 |
| stages[36].operations[17].name | down_proj |
| stages[36].operations[17].matrix_flops | 12884901888 |
| stages[36].operations[17].input_precision | BF16 |
| stages[36].operations[17].accumulator_precision | FP32 |
| stages[36].operations[17].sparsity | dense |
| stages[36].operations[17].scalar_flops | 0 |
| stages[36].operations[17].special_ops | {} |
| stages[36].operations[17].source_detail.input[0] | 128 |
| stages[36].operations[17].source_detail.input[1] | 12288 |
| stages[36].operations[17].source_detail.weight_math[0] | 12288 |
| stages[36].operations[17].source_detail.weight_math[1] | 4096 |
| stages[36].operations[17].source_detail.weight_storage[0] | 4096 |
| stages[36].operations[17].source_detail.weight_storage[1] | 12288 |
| stages[36].operations[17].source_detail.output[0] | 128 |
| stages[36].operations[17].source_detail.output[1] | 4096 |
| stages[36].operations[18].name | ffn_residual |
| stages[36].operations[18].matrix_flops | 0 |
| stages[36].operations[18].input_precision | unknown (null) |
| stages[36].operations[18].accumulator_precision | unknown (null) |
| stages[36].operations[18].sparsity | unknown (null) |
| stages[36].operations[18].scalar_flops | 524288 |
| stages[36].operations[18].special_ops | {} |
| stages[36].operations[18].source_detail.inputs_each[0] | 128 |
| stages[36].operations[18].source_detail.inputs_each[1] | 4096 |
| stages[36].operations[18].source_detail.output[0] | 128 |
| stages[36].operations[18].source_detail.output[1] | 4096 |
| stages[37].id | head |
| stages[37].work.vector_fp32 | 2097280 |
| stages[37].work.special:rsqrt | 128 |
| stages[37].work.interface_bytes | 1247077120 |
| stages[37].work.matrix_bf16 | 1244659712 |
| stages[37].operations[0].name | final_norm |
| stages[37].operations[0].matrix_flops | 0 |
| stages[37].operations[0].input_precision | unknown (null) |
| stages[37].operations[0].accumulator_precision | unknown (null) |
| stages[37].operations[0].sparsity | unknown (null) |
| stages[37].operations[0].scalar_flops | 2097280 |
| stages[37].operations[0].special_ops.rsqrt | 128 |
| stages[37].operations[0].source_detail.input[0] | 128 |
| stages[37].operations[0].source_detail.input[1] | 4096 |
| stages[37].operations[0].source_detail.weight[0] | 4096 |
| stages[37].operations[0].source_detail.output[0] | 128 |
| stages[37].operations[0].source_detail.output[1] | 4096 |
| stages[37].operations[1].name | lm_head |
| stages[37].operations[1].matrix_flops | 1244659712 |
| stages[37].operations[1].input_precision | BF16 |
| stages[37].operations[1].accumulator_precision | FP32 |
| stages[37].operations[1].sparsity | dense |
| stages[37].operations[1].scalar_flops | 0 |
| stages[37].operations[1].special_ops | {} |
| stages[37].operations[1].source_detail.input[0] | 1 |
| stages[37].operations[1].source_detail.input[1] | 4096 |
| stages[37].operations[1].source_detail.weight_math[0] | 4096 |
| stages[37].operations[1].source_detail.weight_math[1] | 151936 |
| stages[37].operations[1].source_detail.weight_storage[0] | 151936 |
| stages[37].operations[1].source_detail.weight_storage[1] | 4096 |
| stages[37].operations[1].source_detail.output[0] | 1 |
| stages[37].operations[1].source_detail.output[1] | 151936 |
| precision_admission.matrix_bf16.input_precision | BF16 |
| precision_admission.matrix_bf16.accumulator | FP32 |
| precision_admission.matrix_bf16.unit | tensor |
| precision_admission.matrix_bf16.sparsity | dense |
| precision_admission.matrix_bf16.official_peak.input_precision | BF16 |
| precision_admission.matrix_bf16.official_peak.accumulator_precision | FP32 |
| precision_admission.matrix_bf16.official_peak.execution_unit | tensor |
| precision_admission.matrix_bf16.official_peak.sparsity | dense |
| precision_admission.matrix_bf16.official_peak.tera_ops_per_second | 989.4 |
| precision_admission.matrix_bf16.official_peak.operation_kind | floating_point |
| precision_admission.matrix_bf16.official_peak.source_id | nvidia-h100 |
| precision_admission.matrix_bf16.official_peak.locator | Table 3, physical pages 39–40, including clock rows and sparsity footnote 1 |
| precision_admission.matrix_bf16.official_peak.reported | 989.4 |
| precision_admission.matrix_bf16.official_peak.derivation | unknown (null) |
| precision_admission.matrix_bf16.official_peak.clock_basis | GPU Boost 1830 MHz for FP8/FP16/BF16/TF32; published rounded peak |
| precision_admission.matrix_bf16.official_peak.clock_evidence.source_id | nvidia-h100 |
| precision_admission.matrix_bf16.official_peak.clock_evidence.locator | Table 3, printed/physical p39, h100-sxm column; GPU Boost Clock for FP8, FP16, BF16, TF32 Tensor Core Ops; footnote2 p40 |
| precision_admission.matrix_bf16.official_peak.clock_evidence.gpu_boost_mhz | 1830 |
| precision_admission.matrix_bf16.official_peak.clock_evidence.status | explicit_peak_operation_domain |
| precision_admission.matrix_bf16.official_peak.clock_evidence.applies_to | FP8, FP16, BF16, TF32 Tensor Core Ops |
| precision_admission.matrix_bf16.official_peak.clock_evidence.boundary | GPU Peak and Boost clocks are synonymous in footnote2; not sustained runtime frequency or measured power at this frequency. |
| precision_admission.matrix_bf16.official_peak.supporting_evidence[0].source_id | nvidia-h100 |
| precision_admission.matrix_bf16.official_peak.supporting_evidence[0].locator | Table 3, p39, Peak BF16 Tensor TFLOPS with FP32 Accumulate, h100-sxm column; sparse footnote1 p40 |
| precision_admission.matrix_bf16.official_peak.supporting_evidence[0].claim | Product table explicitly associates this accumulator with this SKU rate; direct table evidence, no PTX-only throughput inference. |
| precision_admission.matrix_bf16.unavailable_reason | unknown (null) |
| precision_admission.matrix_fp8.input_precision | FP8 |
| precision_admission.matrix_fp8.accumulator | FP32 |
| precision_admission.matrix_fp8.unit | tensor |
| precision_admission.matrix_fp8.sparsity | dense |
| precision_admission.matrix_fp8.official_peak.input_precision | FP8 |
| precision_admission.matrix_fp8.official_peak.accumulator_precision | FP32 |
| precision_admission.matrix_fp8.official_peak.execution_unit | tensor |
| precision_admission.matrix_fp8.official_peak.sparsity | dense |
| precision_admission.matrix_fp8.official_peak.tera_ops_per_second | 1978.9 |
| precision_admission.matrix_fp8.official_peak.operation_kind | floating_point |
| precision_admission.matrix_fp8.official_peak.source_id | nvidia-h100 |
| precision_admission.matrix_fp8.official_peak.locator | Table 3, physical pages 39–40, including clock rows and sparsity footnote 1 |
| precision_admission.matrix_fp8.official_peak.reported | 1978.9 |
| precision_admission.matrix_fp8.official_peak.derivation | unknown (null) |
| precision_admission.matrix_fp8.official_peak.clock_basis | GPU Boost 1830 MHz for FP8/FP16/BF16/TF32; published rounded peak |
| precision_admission.matrix_fp8.official_peak.clock_evidence.source_id | nvidia-h100 |
| precision_admission.matrix_fp8.official_peak.clock_evidence.locator | Table 3, printed/physical p39, h100-sxm column; GPU Boost Clock for FP8, FP16, BF16, TF32 Tensor Core Ops; footnote2 p40 |
| precision_admission.matrix_fp8.official_peak.clock_evidence.gpu_boost_mhz | 1830 |
| precision_admission.matrix_fp8.official_peak.clock_evidence.status | explicit_peak_operation_domain |
| precision_admission.matrix_fp8.official_peak.clock_evidence.applies_to | FP8, FP16, BF16, TF32 Tensor Core Ops |
| precision_admission.matrix_fp8.official_peak.clock_evidence.boundary | GPU Peak and Boost clocks are synonymous in footnote2; not sustained runtime frequency or measured power at this frequency. |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[0].source_id | nvidia-h100 |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[0].locator | Table 3, p39, Peak FP8 Tensor TFLOPS with FP32 Accumulate, h100-sxm column; sparse footnote1 p40 |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[0].claim | Product table explicitly associates this accumulator with this SKU rate; direct table evidence, no PTX-only throughput inference. |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[1].source_id | nvidia-ptx-isa-9-3 |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[1].locator | 13.2 Changes in PTX ISA9.2, Semantic Changes and Clarifications; wgmma.mma_async e4m3/e5m2 with dtype.f32 |
| precision_admission.matrix_fp8.official_peak.supporting_evidence[1].claim | Declared/API accumulator remains FP32 per H100 Table3. For the specified wgmma FP8 instruction path, PTX states current internal accumulation precision is above half but below single. Applies only when using this instruction path; not a generic statement about all mma/tcgen05, and not proof the product peak uses one exclusive instruction. |
| precision_admission.matrix_fp8.unavailable_reason | unknown (null) |
| precision_admission.vector_fp32.input_precision | FP32 |
| precision_admission.vector_fp32.accumulator | FP32 |
| precision_admission.vector_fp32.unit | vector |
| precision_admission.vector_fp32.sparsity | dense |
| precision_admission.vector_fp32.official_peak.input_precision | FP32 |
| precision_admission.vector_fp32.official_peak.accumulator_precision | FP32 |
| precision_admission.vector_fp32.official_peak.execution_unit | vector |
| precision_admission.vector_fp32.official_peak.sparsity | dense |
| precision_admission.vector_fp32.official_peak.tera_ops_per_second | 66.9 |
| precision_admission.vector_fp32.official_peak.operation_kind | floating_point |
| precision_admission.vector_fp32.official_peak.source_id | nvidia-h100 |
| precision_admission.vector_fp32.official_peak.locator | Table 3, physical pages 39–40, including clock rows and sparsity footnote 1 |
| precision_admission.vector_fp32.official_peak.reported | 66.9 |
| precision_admission.vector_fp32.official_peak.derivation | unknown (null) |
| precision_admission.vector_fp32.official_peak.clock_basis | GPU Boost 1980 MHz for FP32/FP64 |
| precision_admission.vector_fp32.official_peak.clock_evidence.source_id | nvidia-h100 |
| precision_admission.vector_fp32.official_peak.clock_evidence.locator | Table 3, printed/physical p39, h100-sxm column; GPU Boost Clock for FP64 Tensor Core Ops, FP32 and FP64 non-Tensor Core Ops; footnote2 p40 |
| precision_admission.vector_fp32.official_peak.clock_evidence.gpu_boost_mhz | 1980 |
| precision_admission.vector_fp32.official_peak.clock_evidence.status | explicit_peak_operation_domain |
| precision_admission.vector_fp32.official_peak.clock_evidence.applies_to | FP64 Tensor Core Ops, FP32 and FP64 non-Tensor Core Ops |
| precision_admission.vector_fp32.official_peak.clock_evidence.boundary | GPU Peak and Boost clocks are synonymous in footnote2; not sustained runtime frequency or measured power at this frequency. |
| precision_admission.vector_fp32.official_peak.supporting_evidence[0].source_id | nvidia-cuda-programming-guide-12-8-1-h05 |
| precision_admission.vector_fp32.official_peak.supporting_evidence[0].locator | 5.4.1 Table4 Throughput of Native Arithmetic Instructions; Compute Capability9.0 column,32-bit or64-bit floating-point add/multiply/multiply-add |
| precision_admission.vector_fp32.official_peak.supporting_evidence[0].claim | Native FP32 multiply-add produces 128 results per clock per SM; this is instruction throughput, not merely legal operand types. |
| precision_admission.vector_fp32.official_peak.supporting_evidence[1].source_id | nvidia-ptx-isa-9-3 |
| precision_admission.vector_fp32.official_peak.supporting_evidence[1].locator | 9.7.3.6 #floating-point-instructions-fma, fma.rnd.f32 / fma.rnd.f64 signatures, semantics and Notes |
| precision_admission.vector_fp32.official_peak.supporting_evidence[1].claim | Scalar FMA addend and destination use FP32; result rounds to that precision. Internal fused intermediate is not claimed to be a fixed-width accumulator. |
| precision_admission.vector_fp32.official_peak.supporting_evidence[2].source_id | nvidia-h100 |
| precision_admission.vector_fp32.official_peak.supporting_evidence[2].locator | Table3 printed39–40: exact SKU SM count, FP32/FP64 non-Tensor Boost domain and peak rows; Table4 p41 CC9.0 |
| precision_admission.vector_fp32.official_peak.supporting_evidence[2].claim | 132 SM * 128 FMA results/(SM cycle) * 1980e6 cycles/s * 2 FLOPs/FMA / 1e12 = 66.90816 TFLOPS; source rounded to 66.9 |
| precision_admission.vector_fp32.unavailable_reason | unknown (null) |
| effective_resource_rates.matrix_bf16 | 989400000000000.0 |
| effective_resource_rates.matrix_fp8 | 1978900000000000.0 |
| effective_resource_rates.vector_fp32 | 66900000000000.01 |
| effective_resource_rates.interface_bytes | 3350000000000.0 |
| effective_resource_rates.special:mask_decisions | unknown (null) |
| effective_resource_rates.special:sin | unknown (null) |
| effective_resource_rates.special:rsqrt | unknown (null) |
| effective_resource_rates.special:exp | unknown (null) |
| effective_resource_rates.special:compare_max | unknown (null) |
| effective_resource_rates.special:cos | unknown (null) |
| effective_resource_rates.special:negate | unknown (null) |
| baseline_work.matrix_flops | 1784230707200 |
| baseline_work.scalar_flops | 620582016 |
| baseline_work.special_ops.sin | 16384 |
| baseline_work.special_ops.cos | 16384 |
| baseline_work.special_ops.rsqrt | 193664 |
| baseline_work.special_ops.negate | 68419584 |
| baseline_work.special_ops.exp | 66134016 |
| baseline_work.special_ops.compare_max | 9363456 |
| baseline_work.special_ops.mask_decisions | 18874368 |
| resource_bounds.stages[0].id | input |
| resource_bounds.stages[0].resource_seconds.vector_fp32 | 1.2245142002989536e-10 |
| resource_bounds.stages[0].resource_seconds.interface_bytes | 6.462662686567164e-07 |
| resource_bounds.stages[0].missing[0].resource | special:sin |
| resource_bounds.stages[0].missing[0].reason | unknown rate |
| resource_bounds.stages[0].missing[1].resource | special:cos |
| resource_bounds.stages[0].missing[1].reason | unknown rate |
| resource_bounds.stages[0].known_resource_max_seconds | 6.462662686567164e-07 |
| resource_bounds.stages[0].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[1].id | layer:0 |
| resource_bounds.stages[1].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[1].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[1].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[1].missing[0].resource | special:rsqrt |
| resource_bounds.stages[1].missing[0].reason | unknown rate |
| resource_bounds.stages[1].missing[1].resource | special:negate |
| resource_bounds.stages[1].missing[1].reason | unknown rate |
| resource_bounds.stages[1].missing[2].resource | special:exp |
| resource_bounds.stages[1].missing[2].reason | unknown rate |
| resource_bounds.stages[1].missing[3].resource | special:compare_max |
| resource_bounds.stages[1].missing[3].reason | unknown rate |
| resource_bounds.stages[1].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[1].missing[4].reason | unknown rate |
| resource_bounds.stages[1].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[1].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[2].id | layer:1 |
| resource_bounds.stages[2].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[2].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[2].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[2].missing[0].resource | special:rsqrt |
| resource_bounds.stages[2].missing[0].reason | unknown rate |
| resource_bounds.stages[2].missing[1].resource | special:negate |
| resource_bounds.stages[2].missing[1].reason | unknown rate |
| resource_bounds.stages[2].missing[2].resource | special:exp |
| resource_bounds.stages[2].missing[2].reason | unknown rate |
| resource_bounds.stages[2].missing[3].resource | special:compare_max |
| resource_bounds.stages[2].missing[3].reason | unknown rate |
| resource_bounds.stages[2].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[2].missing[4].reason | unknown rate |
| resource_bounds.stages[2].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[2].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[3].id | layer:2 |
| resource_bounds.stages[3].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[3].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[3].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[3].missing[0].resource | special:rsqrt |
| resource_bounds.stages[3].missing[0].reason | unknown rate |
| resource_bounds.stages[3].missing[1].resource | special:negate |
| resource_bounds.stages[3].missing[1].reason | unknown rate |
| resource_bounds.stages[3].missing[2].resource | special:exp |
| resource_bounds.stages[3].missing[2].reason | unknown rate |
| resource_bounds.stages[3].missing[3].resource | special:compare_max |
| resource_bounds.stages[3].missing[3].reason | unknown rate |
| resource_bounds.stages[3].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[3].missing[4].reason | unknown rate |
| resource_bounds.stages[3].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[3].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[4].id | layer:3 |
| resource_bounds.stages[4].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[4].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[4].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[4].missing[0].resource | special:rsqrt |
| resource_bounds.stages[4].missing[0].reason | unknown rate |
| resource_bounds.stages[4].missing[1].resource | special:negate |
| resource_bounds.stages[4].missing[1].reason | unknown rate |
| resource_bounds.stages[4].missing[2].resource | special:exp |
| resource_bounds.stages[4].missing[2].reason | unknown rate |
| resource_bounds.stages[4].missing[3].resource | special:compare_max |
| resource_bounds.stages[4].missing[3].reason | unknown rate |
| resource_bounds.stages[4].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[4].missing[4].reason | unknown rate |
| resource_bounds.stages[4].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[4].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[5].id | layer:4 |
| resource_bounds.stages[5].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[5].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[5].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[5].missing[0].resource | special:rsqrt |
| resource_bounds.stages[5].missing[0].reason | unknown rate |
| resource_bounds.stages[5].missing[1].resource | special:negate |
| resource_bounds.stages[5].missing[1].reason | unknown rate |
| resource_bounds.stages[5].missing[2].resource | special:exp |
| resource_bounds.stages[5].missing[2].reason | unknown rate |
| resource_bounds.stages[5].missing[3].resource | special:compare_max |
| resource_bounds.stages[5].missing[3].reason | unknown rate |
| resource_bounds.stages[5].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[5].missing[4].reason | unknown rate |
| resource_bounds.stages[5].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[5].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[6].id | layer:5 |
| resource_bounds.stages[6].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[6].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[6].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[6].missing[0].resource | special:rsqrt |
| resource_bounds.stages[6].missing[0].reason | unknown rate |
| resource_bounds.stages[6].missing[1].resource | special:negate |
| resource_bounds.stages[6].missing[1].reason | unknown rate |
| resource_bounds.stages[6].missing[2].resource | special:exp |
| resource_bounds.stages[6].missing[2].reason | unknown rate |
| resource_bounds.stages[6].missing[3].resource | special:compare_max |
| resource_bounds.stages[6].missing[3].reason | unknown rate |
| resource_bounds.stages[6].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[6].missing[4].reason | unknown rate |
| resource_bounds.stages[6].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[6].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[7].id | layer:6 |
| resource_bounds.stages[7].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[7].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[7].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[7].missing[0].resource | special:rsqrt |
| resource_bounds.stages[7].missing[0].reason | unknown rate |
| resource_bounds.stages[7].missing[1].resource | special:negate |
| resource_bounds.stages[7].missing[1].reason | unknown rate |
| resource_bounds.stages[7].missing[2].resource | special:exp |
| resource_bounds.stages[7].missing[2].reason | unknown rate |
| resource_bounds.stages[7].missing[3].resource | special:compare_max |
| resource_bounds.stages[7].missing[3].reason | unknown rate |
| resource_bounds.stages[7].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[7].missing[4].reason | unknown rate |
| resource_bounds.stages[7].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[7].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[8].id | layer:7 |
| resource_bounds.stages[8].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[8].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[8].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[8].missing[0].resource | special:rsqrt |
| resource_bounds.stages[8].missing[0].reason | unknown rate |
| resource_bounds.stages[8].missing[1].resource | special:negate |
| resource_bounds.stages[8].missing[1].reason | unknown rate |
| resource_bounds.stages[8].missing[2].resource | special:exp |
| resource_bounds.stages[8].missing[2].reason | unknown rate |
| resource_bounds.stages[8].missing[3].resource | special:compare_max |
| resource_bounds.stages[8].missing[3].reason | unknown rate |
| resource_bounds.stages[8].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[8].missing[4].reason | unknown rate |
| resource_bounds.stages[8].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[8].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[9].id | layer:8 |
| resource_bounds.stages[9].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[9].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[9].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[9].missing[0].resource | special:rsqrt |
| resource_bounds.stages[9].missing[0].reason | unknown rate |
| resource_bounds.stages[9].missing[1].resource | special:negate |
| resource_bounds.stages[9].missing[1].reason | unknown rate |
| resource_bounds.stages[9].missing[2].resource | special:exp |
| resource_bounds.stages[9].missing[2].reason | unknown rate |
| resource_bounds.stages[9].missing[3].resource | special:compare_max |
| resource_bounds.stages[9].missing[3].reason | unknown rate |
| resource_bounds.stages[9].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[9].missing[4].reason | unknown rate |
| resource_bounds.stages[9].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[9].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[10].id | layer:9 |
| resource_bounds.stages[10].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[10].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[10].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[10].missing[0].resource | special:rsqrt |
| resource_bounds.stages[10].missing[0].reason | unknown rate |
| resource_bounds.stages[10].missing[1].resource | special:negate |
| resource_bounds.stages[10].missing[1].reason | unknown rate |
| resource_bounds.stages[10].missing[2].resource | special:exp |
| resource_bounds.stages[10].missing[2].reason | unknown rate |
| resource_bounds.stages[10].missing[3].resource | special:compare_max |
| resource_bounds.stages[10].missing[3].reason | unknown rate |
| resource_bounds.stages[10].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[10].missing[4].reason | unknown rate |
| resource_bounds.stages[10].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[10].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[11].id | layer:10 |
| resource_bounds.stages[11].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[11].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[11].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[11].missing[0].resource | special:rsqrt |
| resource_bounds.stages[11].missing[0].reason | unknown rate |
| resource_bounds.stages[11].missing[1].resource | special:negate |
| resource_bounds.stages[11].missing[1].reason | unknown rate |
| resource_bounds.stages[11].missing[2].resource | special:exp |
| resource_bounds.stages[11].missing[2].reason | unknown rate |
| resource_bounds.stages[11].missing[3].resource | special:compare_max |
| resource_bounds.stages[11].missing[3].reason | unknown rate |
| resource_bounds.stages[11].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[11].missing[4].reason | unknown rate |
| resource_bounds.stages[11].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[11].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[12].id | layer:11 |
| resource_bounds.stages[12].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[12].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[12].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[12].missing[0].resource | special:rsqrt |
| resource_bounds.stages[12].missing[0].reason | unknown rate |
| resource_bounds.stages[12].missing[1].resource | special:negate |
| resource_bounds.stages[12].missing[1].reason | unknown rate |
| resource_bounds.stages[12].missing[2].resource | special:exp |
| resource_bounds.stages[12].missing[2].reason | unknown rate |
| resource_bounds.stages[12].missing[3].resource | special:compare_max |
| resource_bounds.stages[12].missing[3].reason | unknown rate |
| resource_bounds.stages[12].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[12].missing[4].reason | unknown rate |
| resource_bounds.stages[12].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[12].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[13].id | layer:12 |
| resource_bounds.stages[13].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[13].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[13].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[13].missing[0].resource | special:rsqrt |
| resource_bounds.stages[13].missing[0].reason | unknown rate |
| resource_bounds.stages[13].missing[1].resource | special:negate |
| resource_bounds.stages[13].missing[1].reason | unknown rate |
| resource_bounds.stages[13].missing[2].resource | special:exp |
| resource_bounds.stages[13].missing[2].reason | unknown rate |
| resource_bounds.stages[13].missing[3].resource | special:compare_max |
| resource_bounds.stages[13].missing[3].reason | unknown rate |
| resource_bounds.stages[13].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[13].missing[4].reason | unknown rate |
| resource_bounds.stages[13].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[13].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[14].id | layer:13 |
| resource_bounds.stages[14].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[14].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[14].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[14].missing[0].resource | special:rsqrt |
| resource_bounds.stages[14].missing[0].reason | unknown rate |
| resource_bounds.stages[14].missing[1].resource | special:negate |
| resource_bounds.stages[14].missing[1].reason | unknown rate |
| resource_bounds.stages[14].missing[2].resource | special:exp |
| resource_bounds.stages[14].missing[2].reason | unknown rate |
| resource_bounds.stages[14].missing[3].resource | special:compare_max |
| resource_bounds.stages[14].missing[3].reason | unknown rate |
| resource_bounds.stages[14].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[14].missing[4].reason | unknown rate |
| resource_bounds.stages[14].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[14].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[15].id | layer:14 |
| resource_bounds.stages[15].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[15].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[15].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[15].missing[0].resource | special:rsqrt |
| resource_bounds.stages[15].missing[0].reason | unknown rate |
| resource_bounds.stages[15].missing[1].resource | special:negate |
| resource_bounds.stages[15].missing[1].reason | unknown rate |
| resource_bounds.stages[15].missing[2].resource | special:exp |
| resource_bounds.stages[15].missing[2].reason | unknown rate |
| resource_bounds.stages[15].missing[3].resource | special:compare_max |
| resource_bounds.stages[15].missing[3].reason | unknown rate |
| resource_bounds.stages[15].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[15].missing[4].reason | unknown rate |
| resource_bounds.stages[15].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[15].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[16].id | layer:15 |
| resource_bounds.stages[16].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[16].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[16].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[16].missing[0].resource | special:rsqrt |
| resource_bounds.stages[16].missing[0].reason | unknown rate |
| resource_bounds.stages[16].missing[1].resource | special:negate |
| resource_bounds.stages[16].missing[1].reason | unknown rate |
| resource_bounds.stages[16].missing[2].resource | special:exp |
| resource_bounds.stages[16].missing[2].reason | unknown rate |
| resource_bounds.stages[16].missing[3].resource | special:compare_max |
| resource_bounds.stages[16].missing[3].reason | unknown rate |
| resource_bounds.stages[16].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[16].missing[4].reason | unknown rate |
| resource_bounds.stages[16].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[16].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[17].id | layer:16 |
| resource_bounds.stages[17].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[17].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[17].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[17].missing[0].resource | special:rsqrt |
| resource_bounds.stages[17].missing[0].reason | unknown rate |
| resource_bounds.stages[17].missing[1].resource | special:negate |
| resource_bounds.stages[17].missing[1].reason | unknown rate |
| resource_bounds.stages[17].missing[2].resource | special:exp |
| resource_bounds.stages[17].missing[2].reason | unknown rate |
| resource_bounds.stages[17].missing[3].resource | special:compare_max |
| resource_bounds.stages[17].missing[3].reason | unknown rate |
| resource_bounds.stages[17].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[17].missing[4].reason | unknown rate |
| resource_bounds.stages[17].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[17].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[18].id | layer:17 |
| resource_bounds.stages[18].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[18].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[18].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[18].missing[0].resource | special:rsqrt |
| resource_bounds.stages[18].missing[0].reason | unknown rate |
| resource_bounds.stages[18].missing[1].resource | special:negate |
| resource_bounds.stages[18].missing[1].reason | unknown rate |
| resource_bounds.stages[18].missing[2].resource | special:exp |
| resource_bounds.stages[18].missing[2].reason | unknown rate |
| resource_bounds.stages[18].missing[3].resource | special:compare_max |
| resource_bounds.stages[18].missing[3].reason | unknown rate |
| resource_bounds.stages[18].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[18].missing[4].reason | unknown rate |
| resource_bounds.stages[18].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[18].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[19].id | layer:18 |
| resource_bounds.stages[19].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[19].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[19].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[19].missing[0].resource | special:rsqrt |
| resource_bounds.stages[19].missing[0].reason | unknown rate |
| resource_bounds.stages[19].missing[1].resource | special:negate |
| resource_bounds.stages[19].missing[1].reason | unknown rate |
| resource_bounds.stages[19].missing[2].resource | special:exp |
| resource_bounds.stages[19].missing[2].reason | unknown rate |
| resource_bounds.stages[19].missing[3].resource | special:compare_max |
| resource_bounds.stages[19].missing[3].reason | unknown rate |
| resource_bounds.stages[19].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[19].missing[4].reason | unknown rate |
| resource_bounds.stages[19].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[19].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[20].id | layer:19 |
| resource_bounds.stages[20].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[20].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[20].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[20].missing[0].resource | special:rsqrt |
| resource_bounds.stages[20].missing[0].reason | unknown rate |
| resource_bounds.stages[20].missing[1].resource | special:negate |
| resource_bounds.stages[20].missing[1].reason | unknown rate |
| resource_bounds.stages[20].missing[2].resource | special:exp |
| resource_bounds.stages[20].missing[2].reason | unknown rate |
| resource_bounds.stages[20].missing[3].resource | special:compare_max |
| resource_bounds.stages[20].missing[3].reason | unknown rate |
| resource_bounds.stages[20].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[20].missing[4].reason | unknown rate |
| resource_bounds.stages[20].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[20].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[21].id | layer:20 |
| resource_bounds.stages[21].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[21].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[21].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[21].missing[0].resource | special:rsqrt |
| resource_bounds.stages[21].missing[0].reason | unknown rate |
| resource_bounds.stages[21].missing[1].resource | special:negate |
| resource_bounds.stages[21].missing[1].reason | unknown rate |
| resource_bounds.stages[21].missing[2].resource | special:exp |
| resource_bounds.stages[21].missing[2].reason | unknown rate |
| resource_bounds.stages[21].missing[3].resource | special:compare_max |
| resource_bounds.stages[21].missing[3].reason | unknown rate |
| resource_bounds.stages[21].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[21].missing[4].reason | unknown rate |
| resource_bounds.stages[21].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[21].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[22].id | layer:21 |
| resource_bounds.stages[22].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[22].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[22].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[22].missing[0].resource | special:rsqrt |
| resource_bounds.stages[22].missing[0].reason | unknown rate |
| resource_bounds.stages[22].missing[1].resource | special:negate |
| resource_bounds.stages[22].missing[1].reason | unknown rate |
| resource_bounds.stages[22].missing[2].resource | special:exp |
| resource_bounds.stages[22].missing[2].reason | unknown rate |
| resource_bounds.stages[22].missing[3].resource | special:compare_max |
| resource_bounds.stages[22].missing[3].reason | unknown rate |
| resource_bounds.stages[22].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[22].missing[4].reason | unknown rate |
| resource_bounds.stages[22].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[22].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[23].id | layer:22 |
| resource_bounds.stages[23].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[23].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[23].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[23].missing[0].resource | special:rsqrt |
| resource_bounds.stages[23].missing[0].reason | unknown rate |
| resource_bounds.stages[23].missing[1].resource | special:negate |
| resource_bounds.stages[23].missing[1].reason | unknown rate |
| resource_bounds.stages[23].missing[2].resource | special:exp |
| resource_bounds.stages[23].missing[2].reason | unknown rate |
| resource_bounds.stages[23].missing[3].resource | special:compare_max |
| resource_bounds.stages[23].missing[3].reason | unknown rate |
| resource_bounds.stages[23].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[23].missing[4].reason | unknown rate |
| resource_bounds.stages[23].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[23].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[24].id | layer:23 |
| resource_bounds.stages[24].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[24].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[24].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[24].missing[0].resource | special:rsqrt |
| resource_bounds.stages[24].missing[0].reason | unknown rate |
| resource_bounds.stages[24].missing[1].resource | special:negate |
| resource_bounds.stages[24].missing[1].reason | unknown rate |
| resource_bounds.stages[24].missing[2].resource | special:exp |
| resource_bounds.stages[24].missing[2].reason | unknown rate |
| resource_bounds.stages[24].missing[3].resource | special:compare_max |
| resource_bounds.stages[24].missing[3].reason | unknown rate |
| resource_bounds.stages[24].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[24].missing[4].reason | unknown rate |
| resource_bounds.stages[24].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[24].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[25].id | layer:24 |
| resource_bounds.stages[25].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[25].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[25].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[25].missing[0].resource | special:rsqrt |
| resource_bounds.stages[25].missing[0].reason | unknown rate |
| resource_bounds.stages[25].missing[1].resource | special:negate |
| resource_bounds.stages[25].missing[1].reason | unknown rate |
| resource_bounds.stages[25].missing[2].resource | special:exp |
| resource_bounds.stages[25].missing[2].reason | unknown rate |
| resource_bounds.stages[25].missing[3].resource | special:compare_max |
| resource_bounds.stages[25].missing[3].reason | unknown rate |
| resource_bounds.stages[25].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[25].missing[4].reason | unknown rate |
| resource_bounds.stages[25].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[25].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[26].id | layer:25 |
| resource_bounds.stages[26].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[26].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[26].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[26].missing[0].resource | special:rsqrt |
| resource_bounds.stages[26].missing[0].reason | unknown rate |
| resource_bounds.stages[26].missing[1].resource | special:negate |
| resource_bounds.stages[26].missing[1].reason | unknown rate |
| resource_bounds.stages[26].missing[2].resource | special:exp |
| resource_bounds.stages[26].missing[2].reason | unknown rate |
| resource_bounds.stages[26].missing[3].resource | special:compare_max |
| resource_bounds.stages[26].missing[3].reason | unknown rate |
| resource_bounds.stages[26].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[26].missing[4].reason | unknown rate |
| resource_bounds.stages[26].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[26].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[27].id | layer:26 |
| resource_bounds.stages[27].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[27].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[27].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[27].missing[0].resource | special:rsqrt |
| resource_bounds.stages[27].missing[0].reason | unknown rate |
| resource_bounds.stages[27].missing[1].resource | special:negate |
| resource_bounds.stages[27].missing[1].reason | unknown rate |
| resource_bounds.stages[27].missing[2].resource | special:exp |
| resource_bounds.stages[27].missing[2].reason | unknown rate |
| resource_bounds.stages[27].missing[3].resource | special:compare_max |
| resource_bounds.stages[27].missing[3].reason | unknown rate |
| resource_bounds.stages[27].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[27].missing[4].reason | unknown rate |
| resource_bounds.stages[27].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[27].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[28].id | layer:27 |
| resource_bounds.stages[28].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[28].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[28].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[28].missing[0].resource | special:rsqrt |
| resource_bounds.stages[28].missing[0].reason | unknown rate |
| resource_bounds.stages[28].missing[1].resource | special:negate |
| resource_bounds.stages[28].missing[1].reason | unknown rate |
| resource_bounds.stages[28].missing[2].resource | special:exp |
| resource_bounds.stages[28].missing[2].reason | unknown rate |
| resource_bounds.stages[28].missing[3].resource | special:compare_max |
| resource_bounds.stages[28].missing[3].reason | unknown rate |
| resource_bounds.stages[28].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[28].missing[4].reason | unknown rate |
| resource_bounds.stages[28].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[28].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[29].id | layer:28 |
| resource_bounds.stages[29].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[29].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[29].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[29].missing[0].resource | special:rsqrt |
| resource_bounds.stages[29].missing[0].reason | unknown rate |
| resource_bounds.stages[29].missing[1].resource | special:negate |
| resource_bounds.stages[29].missing[1].reason | unknown rate |
| resource_bounds.stages[29].missing[2].resource | special:exp |
| resource_bounds.stages[29].missing[2].reason | unknown rate |
| resource_bounds.stages[29].missing[3].resource | special:compare_max |
| resource_bounds.stages[29].missing[3].reason | unknown rate |
| resource_bounds.stages[29].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[29].missing[4].reason | unknown rate |
| resource_bounds.stages[29].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[29].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[30].id | layer:29 |
| resource_bounds.stages[30].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[30].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[30].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[30].missing[0].resource | special:rsqrt |
| resource_bounds.stages[30].missing[0].reason | unknown rate |
| resource_bounds.stages[30].missing[1].resource | special:negate |
| resource_bounds.stages[30].missing[1].reason | unknown rate |
| resource_bounds.stages[30].missing[2].resource | special:exp |
| resource_bounds.stages[30].missing[2].reason | unknown rate |
| resource_bounds.stages[30].missing[3].resource | special:compare_max |
| resource_bounds.stages[30].missing[3].reason | unknown rate |
| resource_bounds.stages[30].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[30].missing[4].reason | unknown rate |
| resource_bounds.stages[30].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[30].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[31].id | layer:30 |
| resource_bounds.stages[31].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[31].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[31].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[31].missing[0].resource | special:rsqrt |
| resource_bounds.stages[31].missing[0].reason | unknown rate |
| resource_bounds.stages[31].missing[1].resource | special:negate |
| resource_bounds.stages[31].missing[1].reason | unknown rate |
| resource_bounds.stages[31].missing[2].resource | special:exp |
| resource_bounds.stages[31].missing[2].reason | unknown rate |
| resource_bounds.stages[31].missing[3].resource | special:compare_max |
| resource_bounds.stages[31].missing[3].reason | unknown rate |
| resource_bounds.stages[31].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[31].missing[4].reason | unknown rate |
| resource_bounds.stages[31].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[31].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[32].id | layer:31 |
| resource_bounds.stages[32].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[32].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[32].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[32].missing[0].resource | special:rsqrt |
| resource_bounds.stages[32].missing[0].reason | unknown rate |
| resource_bounds.stages[32].missing[1].resource | special:negate |
| resource_bounds.stages[32].missing[1].reason | unknown rate |
| resource_bounds.stages[32].missing[2].resource | special:exp |
| resource_bounds.stages[32].missing[2].reason | unknown rate |
| resource_bounds.stages[32].missing[3].resource | special:compare_max |
| resource_bounds.stages[32].missing[3].reason | unknown rate |
| resource_bounds.stages[32].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[32].missing[4].reason | unknown rate |
| resource_bounds.stages[32].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[32].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[33].id | layer:32 |
| resource_bounds.stages[33].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[33].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[33].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[33].missing[0].resource | special:rsqrt |
| resource_bounds.stages[33].missing[0].reason | unknown rate |
| resource_bounds.stages[33].missing[1].resource | special:negate |
| resource_bounds.stages[33].missing[1].reason | unknown rate |
| resource_bounds.stages[33].missing[2].resource | special:exp |
| resource_bounds.stages[33].missing[2].reason | unknown rate |
| resource_bounds.stages[33].missing[3].resource | special:compare_max |
| resource_bounds.stages[33].missing[3].reason | unknown rate |
| resource_bounds.stages[33].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[33].missing[4].reason | unknown rate |
| resource_bounds.stages[33].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[33].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[34].id | layer:33 |
| resource_bounds.stages[34].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[34].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[34].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[34].missing[0].resource | special:rsqrt |
| resource_bounds.stages[34].missing[0].reason | unknown rate |
| resource_bounds.stages[34].missing[1].resource | special:negate |
| resource_bounds.stages[34].missing[1].reason | unknown rate |
| resource_bounds.stages[34].missing[2].resource | special:exp |
| resource_bounds.stages[34].missing[2].reason | unknown rate |
| resource_bounds.stages[34].missing[3].resource | special:compare_max |
| resource_bounds.stages[34].missing[3].reason | unknown rate |
| resource_bounds.stages[34].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[34].missing[4].reason | unknown rate |
| resource_bounds.stages[34].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[34].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[35].id | layer:34 |
| resource_bounds.stages[35].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[35].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[35].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[35].missing[0].resource | special:rsqrt |
| resource_bounds.stages[35].missing[0].reason | unknown rate |
| resource_bounds.stages[35].missing[1].resource | special:negate |
| resource_bounds.stages[35].missing[1].reason | unknown rate |
| resource_bounds.stages[35].missing[2].resource | special:exp |
| resource_bounds.stages[35].missing[2].reason | unknown rate |
| resource_bounds.stages[35].missing[3].resource | special:compare_max |
| resource_bounds.stages[35].missing[3].reason | unknown rate |
| resource_bounds.stages[35].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[35].missing[4].reason | unknown rate |
| resource_bounds.stages[35].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[35].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[36].id | layer:35 |
| resource_bounds.stages[36].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| resource_bounds.stages[36].resource_seconds.interface_bytes | 0.00013086185074626865 |
| resource_bounds.stages[36].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| resource_bounds.stages[36].missing[0].resource | special:rsqrt |
| resource_bounds.stages[36].missing[0].reason | unknown rate |
| resource_bounds.stages[36].missing[1].resource | special:negate |
| resource_bounds.stages[36].missing[1].reason | unknown rate |
| resource_bounds.stages[36].missing[2].resource | special:exp |
| resource_bounds.stages[36].missing[2].reason | unknown rate |
| resource_bounds.stages[36].missing[3].resource | special:compare_max |
| resource_bounds.stages[36].missing[3].reason | unknown rate |
| resource_bounds.stages[36].missing[4].resource | special:mask_decisions |
| resource_bounds.stages[36].missing[4].reason | unknown rate |
| resource_bounds.stages[36].known_resource_max_seconds | 0.00013086185074626865 |
| resource_bounds.stages[36].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.stages[37].id | head |
| resource_bounds.stages[37].resource_seconds.vector_fp32 | 3.1349476831091176e-08 |
| resource_bounds.stages[37].resource_seconds.interface_bytes | 0.00037226182686567167 |
| resource_bounds.stages[37].resource_seconds.matrix_bf16 | 1.257994453203962e-06 |
| resource_bounds.stages[37].missing[0].resource | special:rsqrt |
| resource_bounds.stages[37].missing[0].reason | unknown rate |
| resource_bounds.stages[37].known_resource_max_seconds | 0.00037226182686567167 |
| resource_bounds.stages[37].accounted_stage_lower_bound_seconds | unknown (null) |
| resource_bounds.total_known_work.vector_fp32 | 620582016 |
| resource_bounds.total_known_work.interface_bytes | 17031181312 |
| resource_bounds.total_known_work.special:sin | 16384 |
| resource_bounds.total_known_work.special:cos | 16384 |
| resource_bounds.total_known_work.special:rsqrt | 193664 |
| resource_bounds.total_known_work.matrix_bf16 | 1784230707200 |
| resource_bounds.total_known_work.special:negate | 68419584 |
| resource_bounds.total_known_work.special:exp | 66134016 |
| resource_bounds.total_known_work.special:compare_max | 9363456 |
| resource_bounds.total_known_work.special:mask_decisions | 18874368 |
| resource_bounds.unknown_work_resources | [] |
| resource_bounds.missing_resources[0] | special:compare_max |
| resource_bounds.missing_resources[1] | special:cos |
| resource_bounds.missing_resources[2] | special:exp |
| resource_bounds.missing_resources[3] | special:mask_decisions |
| resource_bounds.missing_resources[4] | special:negate |
| resource_bounds.missing_resources[5] | special:rsqrt |
| resource_bounds.missing_resources[6] | special:sin |
| resource_bounds.global_resource_seconds.vector_fp32 | 9.27626331838565e-06 |
| resource_bounds.global_resource_seconds.interface_bytes | 0.00508393472 |
| resource_bounds.global_resource_seconds.matrix_bf16 | 0.0018033461766727309 |
| resource_bounds.known_global_max_seconds | 0.00508393472 |
| resource_bounds.known_serial_stage_max_sum_seconds | 0.00508393472 |
| resource_bounds.accounted_global_max_seconds | unknown (null) |
| resource_bounds.accounted_serial_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[0].id | input |
| compute_only_bounds.stages[0].resource_seconds.vector_fp32 | 1.2245142002989536e-10 |
| compute_only_bounds.stages[0].missing[0].resource | special:sin |
| compute_only_bounds.stages[0].missing[0].reason | unknown rate |
| compute_only_bounds.stages[0].missing[1].resource | special:cos |
| compute_only_bounds.stages[0].missing[1].reason | unknown rate |
| compute_only_bounds.stages[0].known_resource_max_seconds | 1.2245142002989536e-10 |
| compute_only_bounds.stages[0].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[1].id | layer:0 |
| compute_only_bounds.stages[1].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[1].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[1].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[1].missing[0].reason | unknown rate |
| compute_only_bounds.stages[1].missing[1].resource | special:negate |
| compute_only_bounds.stages[1].missing[1].reason | unknown rate |
| compute_only_bounds.stages[1].missing[2].resource | special:exp |
| compute_only_bounds.stages[1].missing[2].reason | unknown rate |
| compute_only_bounds.stages[1].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[1].missing[3].reason | unknown rate |
| compute_only_bounds.stages[1].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[1].missing[4].reason | unknown rate |
| compute_only_bounds.stages[1].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[1].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[2].id | layer:1 |
| compute_only_bounds.stages[2].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[2].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[2].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[2].missing[0].reason | unknown rate |
| compute_only_bounds.stages[2].missing[1].resource | special:negate |
| compute_only_bounds.stages[2].missing[1].reason | unknown rate |
| compute_only_bounds.stages[2].missing[2].resource | special:exp |
| compute_only_bounds.stages[2].missing[2].reason | unknown rate |
| compute_only_bounds.stages[2].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[2].missing[3].reason | unknown rate |
| compute_only_bounds.stages[2].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[2].missing[4].reason | unknown rate |
| compute_only_bounds.stages[2].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[2].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[3].id | layer:2 |
| compute_only_bounds.stages[3].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[3].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[3].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[3].missing[0].reason | unknown rate |
| compute_only_bounds.stages[3].missing[1].resource | special:negate |
| compute_only_bounds.stages[3].missing[1].reason | unknown rate |
| compute_only_bounds.stages[3].missing[2].resource | special:exp |
| compute_only_bounds.stages[3].missing[2].reason | unknown rate |
| compute_only_bounds.stages[3].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[3].missing[3].reason | unknown rate |
| compute_only_bounds.stages[3].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[3].missing[4].reason | unknown rate |
| compute_only_bounds.stages[3].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[3].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[4].id | layer:3 |
| compute_only_bounds.stages[4].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[4].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[4].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[4].missing[0].reason | unknown rate |
| compute_only_bounds.stages[4].missing[1].resource | special:negate |
| compute_only_bounds.stages[4].missing[1].reason | unknown rate |
| compute_only_bounds.stages[4].missing[2].resource | special:exp |
| compute_only_bounds.stages[4].missing[2].reason | unknown rate |
| compute_only_bounds.stages[4].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[4].missing[3].reason | unknown rate |
| compute_only_bounds.stages[4].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[4].missing[4].reason | unknown rate |
| compute_only_bounds.stages[4].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[4].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[5].id | layer:4 |
| compute_only_bounds.stages[5].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[5].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[5].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[5].missing[0].reason | unknown rate |
| compute_only_bounds.stages[5].missing[1].resource | special:negate |
| compute_only_bounds.stages[5].missing[1].reason | unknown rate |
| compute_only_bounds.stages[5].missing[2].resource | special:exp |
| compute_only_bounds.stages[5].missing[2].reason | unknown rate |
| compute_only_bounds.stages[5].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[5].missing[3].reason | unknown rate |
| compute_only_bounds.stages[5].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[5].missing[4].reason | unknown rate |
| compute_only_bounds.stages[5].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[5].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[6].id | layer:5 |
| compute_only_bounds.stages[6].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[6].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[6].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[6].missing[0].reason | unknown rate |
| compute_only_bounds.stages[6].missing[1].resource | special:negate |
| compute_only_bounds.stages[6].missing[1].reason | unknown rate |
| compute_only_bounds.stages[6].missing[2].resource | special:exp |
| compute_only_bounds.stages[6].missing[2].reason | unknown rate |
| compute_only_bounds.stages[6].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[6].missing[3].reason | unknown rate |
| compute_only_bounds.stages[6].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[6].missing[4].reason | unknown rate |
| compute_only_bounds.stages[6].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[6].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[7].id | layer:6 |
| compute_only_bounds.stages[7].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[7].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[7].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[7].missing[0].reason | unknown rate |
| compute_only_bounds.stages[7].missing[1].resource | special:negate |
| compute_only_bounds.stages[7].missing[1].reason | unknown rate |
| compute_only_bounds.stages[7].missing[2].resource | special:exp |
| compute_only_bounds.stages[7].missing[2].reason | unknown rate |
| compute_only_bounds.stages[7].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[7].missing[3].reason | unknown rate |
| compute_only_bounds.stages[7].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[7].missing[4].reason | unknown rate |
| compute_only_bounds.stages[7].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[7].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[8].id | layer:7 |
| compute_only_bounds.stages[8].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[8].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[8].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[8].missing[0].reason | unknown rate |
| compute_only_bounds.stages[8].missing[1].resource | special:negate |
| compute_only_bounds.stages[8].missing[1].reason | unknown rate |
| compute_only_bounds.stages[8].missing[2].resource | special:exp |
| compute_only_bounds.stages[8].missing[2].reason | unknown rate |
| compute_only_bounds.stages[8].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[8].missing[3].reason | unknown rate |
| compute_only_bounds.stages[8].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[8].missing[4].reason | unknown rate |
| compute_only_bounds.stages[8].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[8].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[9].id | layer:8 |
| compute_only_bounds.stages[9].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[9].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[9].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[9].missing[0].reason | unknown rate |
| compute_only_bounds.stages[9].missing[1].resource | special:negate |
| compute_only_bounds.stages[9].missing[1].reason | unknown rate |
| compute_only_bounds.stages[9].missing[2].resource | special:exp |
| compute_only_bounds.stages[9].missing[2].reason | unknown rate |
| compute_only_bounds.stages[9].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[9].missing[3].reason | unknown rate |
| compute_only_bounds.stages[9].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[9].missing[4].reason | unknown rate |
| compute_only_bounds.stages[9].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[9].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[10].id | layer:9 |
| compute_only_bounds.stages[10].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[10].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[10].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[10].missing[0].reason | unknown rate |
| compute_only_bounds.stages[10].missing[1].resource | special:negate |
| compute_only_bounds.stages[10].missing[1].reason | unknown rate |
| compute_only_bounds.stages[10].missing[2].resource | special:exp |
| compute_only_bounds.stages[10].missing[2].reason | unknown rate |
| compute_only_bounds.stages[10].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[10].missing[3].reason | unknown rate |
| compute_only_bounds.stages[10].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[10].missing[4].reason | unknown rate |
| compute_only_bounds.stages[10].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[10].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[11].id | layer:10 |
| compute_only_bounds.stages[11].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[11].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[11].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[11].missing[0].reason | unknown rate |
| compute_only_bounds.stages[11].missing[1].resource | special:negate |
| compute_only_bounds.stages[11].missing[1].reason | unknown rate |
| compute_only_bounds.stages[11].missing[2].resource | special:exp |
| compute_only_bounds.stages[11].missing[2].reason | unknown rate |
| compute_only_bounds.stages[11].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[11].missing[3].reason | unknown rate |
| compute_only_bounds.stages[11].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[11].missing[4].reason | unknown rate |
| compute_only_bounds.stages[11].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[11].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[12].id | layer:11 |
| compute_only_bounds.stages[12].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[12].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[12].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[12].missing[0].reason | unknown rate |
| compute_only_bounds.stages[12].missing[1].resource | special:negate |
| compute_only_bounds.stages[12].missing[1].reason | unknown rate |
| compute_only_bounds.stages[12].missing[2].resource | special:exp |
| compute_only_bounds.stages[12].missing[2].reason | unknown rate |
| compute_only_bounds.stages[12].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[12].missing[3].reason | unknown rate |
| compute_only_bounds.stages[12].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[12].missing[4].reason | unknown rate |
| compute_only_bounds.stages[12].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[12].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[13].id | layer:12 |
| compute_only_bounds.stages[13].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[13].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[13].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[13].missing[0].reason | unknown rate |
| compute_only_bounds.stages[13].missing[1].resource | special:negate |
| compute_only_bounds.stages[13].missing[1].reason | unknown rate |
| compute_only_bounds.stages[13].missing[2].resource | special:exp |
| compute_only_bounds.stages[13].missing[2].reason | unknown rate |
| compute_only_bounds.stages[13].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[13].missing[3].reason | unknown rate |
| compute_only_bounds.stages[13].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[13].missing[4].reason | unknown rate |
| compute_only_bounds.stages[13].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[13].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[14].id | layer:13 |
| compute_only_bounds.stages[14].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[14].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[14].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[14].missing[0].reason | unknown rate |
| compute_only_bounds.stages[14].missing[1].resource | special:negate |
| compute_only_bounds.stages[14].missing[1].reason | unknown rate |
| compute_only_bounds.stages[14].missing[2].resource | special:exp |
| compute_only_bounds.stages[14].missing[2].reason | unknown rate |
| compute_only_bounds.stages[14].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[14].missing[3].reason | unknown rate |
| compute_only_bounds.stages[14].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[14].missing[4].reason | unknown rate |
| compute_only_bounds.stages[14].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[14].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[15].id | layer:14 |
| compute_only_bounds.stages[15].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[15].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[15].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[15].missing[0].reason | unknown rate |
| compute_only_bounds.stages[15].missing[1].resource | special:negate |
| compute_only_bounds.stages[15].missing[1].reason | unknown rate |
| compute_only_bounds.stages[15].missing[2].resource | special:exp |
| compute_only_bounds.stages[15].missing[2].reason | unknown rate |
| compute_only_bounds.stages[15].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[15].missing[3].reason | unknown rate |
| compute_only_bounds.stages[15].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[15].missing[4].reason | unknown rate |
| compute_only_bounds.stages[15].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[15].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[16].id | layer:15 |
| compute_only_bounds.stages[16].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[16].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[16].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[16].missing[0].reason | unknown rate |
| compute_only_bounds.stages[16].missing[1].resource | special:negate |
| compute_only_bounds.stages[16].missing[1].reason | unknown rate |
| compute_only_bounds.stages[16].missing[2].resource | special:exp |
| compute_only_bounds.stages[16].missing[2].reason | unknown rate |
| compute_only_bounds.stages[16].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[16].missing[3].reason | unknown rate |
| compute_only_bounds.stages[16].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[16].missing[4].reason | unknown rate |
| compute_only_bounds.stages[16].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[16].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[17].id | layer:16 |
| compute_only_bounds.stages[17].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[17].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[17].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[17].missing[0].reason | unknown rate |
| compute_only_bounds.stages[17].missing[1].resource | special:negate |
| compute_only_bounds.stages[17].missing[1].reason | unknown rate |
| compute_only_bounds.stages[17].missing[2].resource | special:exp |
| compute_only_bounds.stages[17].missing[2].reason | unknown rate |
| compute_only_bounds.stages[17].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[17].missing[3].reason | unknown rate |
| compute_only_bounds.stages[17].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[17].missing[4].reason | unknown rate |
| compute_only_bounds.stages[17].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[17].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[18].id | layer:17 |
| compute_only_bounds.stages[18].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[18].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[18].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[18].missing[0].reason | unknown rate |
| compute_only_bounds.stages[18].missing[1].resource | special:negate |
| compute_only_bounds.stages[18].missing[1].reason | unknown rate |
| compute_only_bounds.stages[18].missing[2].resource | special:exp |
| compute_only_bounds.stages[18].missing[2].reason | unknown rate |
| compute_only_bounds.stages[18].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[18].missing[3].reason | unknown rate |
| compute_only_bounds.stages[18].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[18].missing[4].reason | unknown rate |
| compute_only_bounds.stages[18].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[18].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[19].id | layer:18 |
| compute_only_bounds.stages[19].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[19].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[19].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[19].missing[0].reason | unknown rate |
| compute_only_bounds.stages[19].missing[1].resource | special:negate |
| compute_only_bounds.stages[19].missing[1].reason | unknown rate |
| compute_only_bounds.stages[19].missing[2].resource | special:exp |
| compute_only_bounds.stages[19].missing[2].reason | unknown rate |
| compute_only_bounds.stages[19].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[19].missing[3].reason | unknown rate |
| compute_only_bounds.stages[19].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[19].missing[4].reason | unknown rate |
| compute_only_bounds.stages[19].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[19].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[20].id | layer:19 |
| compute_only_bounds.stages[20].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[20].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[20].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[20].missing[0].reason | unknown rate |
| compute_only_bounds.stages[20].missing[1].resource | special:negate |
| compute_only_bounds.stages[20].missing[1].reason | unknown rate |
| compute_only_bounds.stages[20].missing[2].resource | special:exp |
| compute_only_bounds.stages[20].missing[2].reason | unknown rate |
| compute_only_bounds.stages[20].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[20].missing[3].reason | unknown rate |
| compute_only_bounds.stages[20].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[20].missing[4].reason | unknown rate |
| compute_only_bounds.stages[20].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[20].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[21].id | layer:20 |
| compute_only_bounds.stages[21].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[21].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[21].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[21].missing[0].reason | unknown rate |
| compute_only_bounds.stages[21].missing[1].resource | special:negate |
| compute_only_bounds.stages[21].missing[1].reason | unknown rate |
| compute_only_bounds.stages[21].missing[2].resource | special:exp |
| compute_only_bounds.stages[21].missing[2].reason | unknown rate |
| compute_only_bounds.stages[21].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[21].missing[3].reason | unknown rate |
| compute_only_bounds.stages[21].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[21].missing[4].reason | unknown rate |
| compute_only_bounds.stages[21].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[21].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[22].id | layer:21 |
| compute_only_bounds.stages[22].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[22].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[22].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[22].missing[0].reason | unknown rate |
| compute_only_bounds.stages[22].missing[1].resource | special:negate |
| compute_only_bounds.stages[22].missing[1].reason | unknown rate |
| compute_only_bounds.stages[22].missing[2].resource | special:exp |
| compute_only_bounds.stages[22].missing[2].reason | unknown rate |
| compute_only_bounds.stages[22].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[22].missing[3].reason | unknown rate |
| compute_only_bounds.stages[22].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[22].missing[4].reason | unknown rate |
| compute_only_bounds.stages[22].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[22].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[23].id | layer:22 |
| compute_only_bounds.stages[23].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[23].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[23].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[23].missing[0].reason | unknown rate |
| compute_only_bounds.stages[23].missing[1].resource | special:negate |
| compute_only_bounds.stages[23].missing[1].reason | unknown rate |
| compute_only_bounds.stages[23].missing[2].resource | special:exp |
| compute_only_bounds.stages[23].missing[2].reason | unknown rate |
| compute_only_bounds.stages[23].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[23].missing[3].reason | unknown rate |
| compute_only_bounds.stages[23].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[23].missing[4].reason | unknown rate |
| compute_only_bounds.stages[23].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[23].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[24].id | layer:23 |
| compute_only_bounds.stages[24].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[24].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[24].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[24].missing[0].reason | unknown rate |
| compute_only_bounds.stages[24].missing[1].resource | special:negate |
| compute_only_bounds.stages[24].missing[1].reason | unknown rate |
| compute_only_bounds.stages[24].missing[2].resource | special:exp |
| compute_only_bounds.stages[24].missing[2].reason | unknown rate |
| compute_only_bounds.stages[24].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[24].missing[3].reason | unknown rate |
| compute_only_bounds.stages[24].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[24].missing[4].reason | unknown rate |
| compute_only_bounds.stages[24].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[24].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[25].id | layer:24 |
| compute_only_bounds.stages[25].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[25].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[25].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[25].missing[0].reason | unknown rate |
| compute_only_bounds.stages[25].missing[1].resource | special:negate |
| compute_only_bounds.stages[25].missing[1].reason | unknown rate |
| compute_only_bounds.stages[25].missing[2].resource | special:exp |
| compute_only_bounds.stages[25].missing[2].reason | unknown rate |
| compute_only_bounds.stages[25].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[25].missing[3].reason | unknown rate |
| compute_only_bounds.stages[25].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[25].missing[4].reason | unknown rate |
| compute_only_bounds.stages[25].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[25].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[26].id | layer:25 |
| compute_only_bounds.stages[26].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[26].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[26].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[26].missing[0].reason | unknown rate |
| compute_only_bounds.stages[26].missing[1].resource | special:negate |
| compute_only_bounds.stages[26].missing[1].reason | unknown rate |
| compute_only_bounds.stages[26].missing[2].resource | special:exp |
| compute_only_bounds.stages[26].missing[2].reason | unknown rate |
| compute_only_bounds.stages[26].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[26].missing[3].reason | unknown rate |
| compute_only_bounds.stages[26].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[26].missing[4].reason | unknown rate |
| compute_only_bounds.stages[26].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[26].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[27].id | layer:26 |
| compute_only_bounds.stages[27].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[27].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[27].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[27].missing[0].reason | unknown rate |
| compute_only_bounds.stages[27].missing[1].resource | special:negate |
| compute_only_bounds.stages[27].missing[1].reason | unknown rate |
| compute_only_bounds.stages[27].missing[2].resource | special:exp |
| compute_only_bounds.stages[27].missing[2].reason | unknown rate |
| compute_only_bounds.stages[27].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[27].missing[3].reason | unknown rate |
| compute_only_bounds.stages[27].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[27].missing[4].reason | unknown rate |
| compute_only_bounds.stages[27].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[27].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[28].id | layer:27 |
| compute_only_bounds.stages[28].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[28].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[28].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[28].missing[0].reason | unknown rate |
| compute_only_bounds.stages[28].missing[1].resource | special:negate |
| compute_only_bounds.stages[28].missing[1].reason | unknown rate |
| compute_only_bounds.stages[28].missing[2].resource | special:exp |
| compute_only_bounds.stages[28].missing[2].reason | unknown rate |
| compute_only_bounds.stages[28].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[28].missing[3].reason | unknown rate |
| compute_only_bounds.stages[28].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[28].missing[4].reason | unknown rate |
| compute_only_bounds.stages[28].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[28].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[29].id | layer:28 |
| compute_only_bounds.stages[29].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[29].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[29].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[29].missing[0].reason | unknown rate |
| compute_only_bounds.stages[29].missing[1].resource | special:negate |
| compute_only_bounds.stages[29].missing[1].reason | unknown rate |
| compute_only_bounds.stages[29].missing[2].resource | special:exp |
| compute_only_bounds.stages[29].missing[2].reason | unknown rate |
| compute_only_bounds.stages[29].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[29].missing[3].reason | unknown rate |
| compute_only_bounds.stages[29].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[29].missing[4].reason | unknown rate |
| compute_only_bounds.stages[29].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[29].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[30].id | layer:29 |
| compute_only_bounds.stages[30].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[30].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[30].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[30].missing[0].reason | unknown rate |
| compute_only_bounds.stages[30].missing[1].resource | special:negate |
| compute_only_bounds.stages[30].missing[1].reason | unknown rate |
| compute_only_bounds.stages[30].missing[2].resource | special:exp |
| compute_only_bounds.stages[30].missing[2].reason | unknown rate |
| compute_only_bounds.stages[30].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[30].missing[3].reason | unknown rate |
| compute_only_bounds.stages[30].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[30].missing[4].reason | unknown rate |
| compute_only_bounds.stages[30].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[30].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[31].id | layer:30 |
| compute_only_bounds.stages[31].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[31].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[31].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[31].missing[0].reason | unknown rate |
| compute_only_bounds.stages[31].missing[1].resource | special:negate |
| compute_only_bounds.stages[31].missing[1].reason | unknown rate |
| compute_only_bounds.stages[31].missing[2].resource | special:exp |
| compute_only_bounds.stages[31].missing[2].reason | unknown rate |
| compute_only_bounds.stages[31].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[31].missing[3].reason | unknown rate |
| compute_only_bounds.stages[31].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[31].missing[4].reason | unknown rate |
| compute_only_bounds.stages[31].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[31].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[32].id | layer:31 |
| compute_only_bounds.stages[32].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[32].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[32].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[32].missing[0].reason | unknown rate |
| compute_only_bounds.stages[32].missing[1].resource | special:negate |
| compute_only_bounds.stages[32].missing[1].reason | unknown rate |
| compute_only_bounds.stages[32].missing[2].resource | special:exp |
| compute_only_bounds.stages[32].missing[2].reason | unknown rate |
| compute_only_bounds.stages[32].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[32].missing[3].reason | unknown rate |
| compute_only_bounds.stages[32].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[32].missing[4].reason | unknown rate |
| compute_only_bounds.stages[32].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[32].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[33].id | layer:32 |
| compute_only_bounds.stages[33].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[33].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[33].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[33].missing[0].reason | unknown rate |
| compute_only_bounds.stages[33].missing[1].resource | special:negate |
| compute_only_bounds.stages[33].missing[1].reason | unknown rate |
| compute_only_bounds.stages[33].missing[2].resource | special:exp |
| compute_only_bounds.stages[33].missing[2].reason | unknown rate |
| compute_only_bounds.stages[33].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[33].missing[3].reason | unknown rate |
| compute_only_bounds.stages[33].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[33].missing[4].reason | unknown rate |
| compute_only_bounds.stages[33].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[33].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[34].id | layer:33 |
| compute_only_bounds.stages[34].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[34].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[34].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[34].missing[0].reason | unknown rate |
| compute_only_bounds.stages[34].missing[1].resource | special:negate |
| compute_only_bounds.stages[34].missing[1].reason | unknown rate |
| compute_only_bounds.stages[34].missing[2].resource | special:exp |
| compute_only_bounds.stages[34].missing[2].reason | unknown rate |
| compute_only_bounds.stages[34].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[34].missing[3].reason | unknown rate |
| compute_only_bounds.stages[34].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[34].missing[4].reason | unknown rate |
| compute_only_bounds.stages[34].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[34].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[35].id | layer:34 |
| compute_only_bounds.stages[35].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[35].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[35].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[35].missing[0].reason | unknown rate |
| compute_only_bounds.stages[35].missing[1].resource | special:negate |
| compute_only_bounds.stages[35].missing[1].reason | unknown rate |
| compute_only_bounds.stages[35].missing[2].resource | special:exp |
| compute_only_bounds.stages[35].missing[2].reason | unknown rate |
| compute_only_bounds.stages[35].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[35].missing[3].reason | unknown rate |
| compute_only_bounds.stages[35].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[35].missing[4].reason | unknown rate |
| compute_only_bounds.stages[35].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[35].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[36].id | layer:35 |
| compute_only_bounds.stages[36].resource_seconds.vector_fp32 | 2.567997608370702e-07 |
| compute_only_bounds.stages[36].resource_seconds.matrix_bf16 | 5.005800506165353e-05 |
| compute_only_bounds.stages[36].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[36].missing[0].reason | unknown rate |
| compute_only_bounds.stages[36].missing[1].resource | special:negate |
| compute_only_bounds.stages[36].missing[1].reason | unknown rate |
| compute_only_bounds.stages[36].missing[2].resource | special:exp |
| compute_only_bounds.stages[36].missing[2].reason | unknown rate |
| compute_only_bounds.stages[36].missing[3].resource | special:compare_max |
| compute_only_bounds.stages[36].missing[3].reason | unknown rate |
| compute_only_bounds.stages[36].missing[4].resource | special:mask_decisions |
| compute_only_bounds.stages[36].missing[4].reason | unknown rate |
| compute_only_bounds.stages[36].known_resource_max_seconds | 5.005800506165353e-05 |
| compute_only_bounds.stages[36].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.stages[37].id | head |
| compute_only_bounds.stages[37].resource_seconds.vector_fp32 | 3.1349476831091176e-08 |
| compute_only_bounds.stages[37].resource_seconds.matrix_bf16 | 1.257994453203962e-06 |
| compute_only_bounds.stages[37].missing[0].resource | special:rsqrt |
| compute_only_bounds.stages[37].missing[0].reason | unknown rate |
| compute_only_bounds.stages[37].known_resource_max_seconds | 1.257994453203962e-06 |
| compute_only_bounds.stages[37].accounted_stage_lower_bound_seconds | unknown (null) |
| compute_only_bounds.total_known_work.vector_fp32 | 620582016 |
| compute_only_bounds.total_known_work.special:sin | 16384 |
| compute_only_bounds.total_known_work.special:cos | 16384 |
| compute_only_bounds.total_known_work.special:rsqrt | 193664 |
| compute_only_bounds.total_known_work.matrix_bf16 | 1784230707200 |
| compute_only_bounds.total_known_work.special:negate | 68419584 |
| compute_only_bounds.total_known_work.special:exp | 66134016 |
| compute_only_bounds.total_known_work.special:compare_max | 9363456 |
| compute_only_bounds.total_known_work.special:mask_decisions | 18874368 |
| compute_only_bounds.unknown_work_resources | [] |
| compute_only_bounds.missing_resources[0] | special:compare_max |
| compute_only_bounds.missing_resources[1] | special:cos |
| compute_only_bounds.missing_resources[2] | special:exp |
| compute_only_bounds.missing_resources[3] | special:mask_decisions |
| compute_only_bounds.missing_resources[4] | special:negate |
| compute_only_bounds.missing_resources[5] | special:rsqrt |
| compute_only_bounds.missing_resources[6] | special:sin |
| compute_only_bounds.global_resource_seconds.vector_fp32 | 9.27626331838565e-06 |
| compute_only_bounds.global_resource_seconds.matrix_bf16 | 0.0018033461766727309 |
| compute_only_bounds.known_global_max_seconds | 0.0018033461766727309 |
| compute_only_bounds.known_serial_stage_max_sum_seconds | 0.0018033462991241512 |
| compute_only_bounds.accounted_global_max_seconds | unknown (null) |
| compute_only_bounds.accounted_serial_stage_lower_bound_seconds | unknown (null) |
| capacity.comparison_bytes | 16400345088 |
| capacity.applicable_necessary_condition | True |
| capacity.definition | Declared uniform BF16 weights plus BF16 KV after this call; excludes workspace/activations |
| capacity.device_nominal_bytes | 80000000000 |
| capacity.comparison_exceeds_nominal | False |
| capacity.runtime_status | necessary_only |
| capacity.full_runtime_feasibility | unknown (null) |
| coverage_gaps[0] | Sampling/tokenizer/launch/allocator and unexpanded dtype conversions/workspace remain outside the reference. |
| coverage_gaps[1] | BF16 score/probability materialization is explicitly selected; scalar reductions FP32. No source backend or exact casting cost inferred. |
| summary.accounted_serial_stage_lower_bound_seconds | unknown (null) |
| summary.accounted_global_max_seconds | unknown (null) |
| summary.full_request_latency_bound_seconds | unknown (null) |
| summary.measured_latency_seconds | unknown (null) |
| summary.necessary_capacity_not_failed_accounted_bound_seconds | unknown (null) |
| assumptions[0] | Stages are complete serial decoder layers, with ideal overlap inside each layer. Sum of stage resource maxima is distinct from a pooled global maximum; neither is a measured runtime. |
| assumptions[1] | FP32 F.linear is mapped to an explicitly chosen IEEE FP32 vector execution policy, not inferred actual backend dispatch. TF32 is not admitted. Ordinary scalar and FP32 matrix work share one vector budget. The FP32 scalar provider is a declared logical execution policy, not proof of every source elementwise machine dtype. |
| assumptions[2] | V4 FP4 stored experts execute FP8xFP8 after conversion in the pinned kernel; no native FP4 or structured-sparse peak substitution. BF16/FP8 accumulation requires exact FP32 admission. |
| assumptions[3] | Named special and conversion primitive rates are not inferred from vector FLOPs. Missing positive work/rates propagate null; zero work needs no rate. Supplying rates is a hypothetical provider contract, not official disclosure. |
| assumptions[4] | Interface demands are a conditional materialized-operand contract, not observed HBM or an unconditional whole-graph traffic bound. Qwen score/probability interfaces use BF16 explicitly; FP32 scalar reductions remain separate. |
| assumptions[5] | V4 lacks a complete stage interface account; caller-provided bytes can define a conditional budget but cannot close model coverage, runtime capacity or missing operations. |
| assumptions[6] | Nominal memory is not full available allocation, especially Apple unified memory. Necessary-condition success is not proof of actual full-peak feasibility; V4 checkpoint comparison is not a runtime capacity lower bound. |
| assumptions[7] | Official peaks and bandwidth are preserved alongside hypothetical rates/perturbations. No hardware pricing, measured efficiency, or missing peak imputation. |
