# llama70-dense-forward — deepseek-r1-distill-llama-70b

输入：`{"activation_bytes": 2, "batch": 1, "history": 0, "kv_bytes": 2, "output_head": "all", "score_bytes": 4, "tokens": 512, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 70,553,706,496 |
| weight_resident_bytes | 141,107,412,992 |
| backbone_projection_ffn_flops | 70,093,866,270,720 |
| causal_attention_matrix_flops | 344,268,472,320 |
| rectangular_attention_matrix_flops | 687,194,767,360 |
| matrix_flops | 71,514,024,050,688 |
| scalar_flops | 11,889,525,248 |
| special_ops | `{"sin": 65536, "cos": 65536, "cast_position_elements": 512, "cast_cos_sin_elements": 131072, "concat_copy_elements": 65536, "rsqrt": 82432, "cast_elements": 1350565888, "negate": 1363148800, "exp": 1846804480, "compare_max": 669777920, "mask_decisions": 1342177280}` |
| weight_read_once_per_operator_bytes | 139,014,455,296 |
| activation_operand_read_bytes | 27,636,277,504 |
| activation_operand_write_bytes | 24,391,450,624 |
| kv_bytes_per_token_per_request | 327,680 |
| kv_resident_before_bytes | 0 |
| kv_resident_after_bytes | 167,772,160 |
| kv_new_write_bytes | 167,772,160 |
| kv_existing_history_unique_payload_bytes | 0 |
| kv_attention_unique_payload_bytes | 167,772,160 |
| kv_logical_query_head_operand_bytes | 344,268,472,320 |
| attention_score_tensor_per_layer_bytes | 67,108,864 |
| materialized_scores_probabilities_io_all_layers_bytes | 21,474,836,480 |
| minimum_required_weight_and_kv_bytes | 141,275,185,152 |

Llama3 RoPE初始化单独执行，不包含在下方每次forward总数中。

| 初始化 | 普通算术 | 特殊操作 | 常驻buffer bytes |
| --- | ---: | --- | ---: |
| llama3_inv_freq_initialization | 772 | {'pow': 64, 'compare': 192, 'logical_not': 128, 'logical_and': 64, 'where_select': 128, 'iota_elements': 64, 'cast_elements': 64} | 256 |

Fixed source eager arithmetic: default exponent division+reciprocal2n; wavelength n; scaled branch n; smooth3n; blend5n; two thresholds+high-low+2*pi4. torch.where evaluates full vectors in both branches. Intermediates are not assumed HBM. Original_inv_freq aliases same buffer; initialization excluded from forward totals.

| 每次forward特殊操作 | 层重复 | 单次计数 |
| --- | ---: | --- |
| llama3_rope_table | 1 | {'sin': 65536, 'cos': 65536, 'cast_position_elements': 512, 'cast_cos_sin_elements': 131072, 'concat_copy_elements': 65536} |
| input_layernorm | 80 | {'rsqrt': 512, 'cast_elements': 8388608} |
| apply_rope | 80 | {'negate': 2359296} |
| score_scale_mask_softmax | 80 | {'exp': 8404992, 'compare_max': 8372224, 'mask_decisions': 16777216} |
| post_attention_layernorm | 80 | {'rsqrt': 512, 'cast_elements': 8388608} |
| silu_mul | 80 | {'exp': 14680064, 'negate': 14680064} |
| final_norm | 1 | {'rsqrt': 512, 'cast_elements': 8388608} |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[1, 512]；table=[128256, 8192]；output=[512, 8192] | 0 | 0 | 8,388,608 | 4,096 | 8,388,608 |
| llama3_rope_table | 1 | frequencies=[1, 512, 64]；cos_sin_each=[1, 512, 128] | 0 | 163,840 | 0 | 4,352 | 262,144 |
| input_layernorm | 80 | input=[512, 8192]；weight=[8192]；output=[512, 8192] | 0 | 16,777,728 | 16,384 | 8,388,608 | 8,388,608 |
| q_proj | 80 | input=[512, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[512, 8192] | 68,719,476,736 | 0 | 134,217,728 | 8,388,608 | 8,388,608 |
| k_proj | 80 | input=[512, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[512, 1024] | 8,589,934,592 | 0 | 16,777,216 | 8,388,608 | 1,048,576 |
| v_proj | 80 | input=[512, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[512, 1024] | 8,589,934,592 | 0 | 16,777,216 | 8,388,608 | 1,048,576 |
| apply_rope | 80 | Q=[1, 64, 512, 128]；K=[1, 8, 512, 128] | 0 | 14,155,776 | 0 | 9,699,328 | 9,437,184 |
| kv_append | 80 | new_K_and_V_each=[1, 8, 512, 128] | 0 | 0 | 0 | 2,097,152 | 2,097,152 |
| qk | 80 | Q=[1, 64, 512, 128]；K_shared=[1, 8, 512, 128]；scores_rectangular=[1, 64, 512, 512] | 2,151,677,952 | 0 | 0 | 9,437,184 | 67,108,864 |
| score_scale_mask_softmax | 80 | scores=[1, 64, 512, 512] | 0 | 33,587,200 | 0 | 67,108,864 | 67,108,864 |
| pv | 80 | P=[1, 64, 512, 512]；V_shared=[1, 8, 512, 128]；output=[1, 64, 512, 128] | 2,151,677,952 | 0 | 0 | 68,157,440 | 8,388,608 |
| o_proj | 80 | input=[512, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[512, 8192] | 68,719,476,736 | 0 | 134,217,728 | 8,388,608 | 8,388,608 |
| attention_residual | 80 | inputs_each=[512, 8192]；output=[512, 8192] | 0 | 4,194,304 | 0 | 16,777,216 | 8,388,608 |
| post_attention_layernorm | 80 | input=[512, 8192]；weight=[8192]；output=[512, 8192] | 0 | 16,777,728 | 16,384 | 8,388,608 | 8,388,608 |
| gate_proj | 80 | input=[512, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[512, 28672] | 240,518,168,576 | 0 | 469,762,048 | 8,388,608 | 29,360,128 |
| up_proj | 80 | input=[512, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[512, 28672] | 240,518,168,576 | 0 | 469,762,048 | 8,388,608 | 29,360,128 |
| silu_mul | 80 | gate=[512, 28672]；up=[512, 28672]；output=[512, 28672] | 0 | 58,720,256 | 0 | 58,720,256 | 29,360,128 |
| down_proj | 80 | input=[512, 28672]；weight_math=[28672, 8192]；weight_storage=[8192, 28672]；output=[512, 8192] | 240,518,168,576 | 0 | 469,762,048 | 29,360,128 | 8,388,608 |
| ffn_residual | 80 | inputs_each=[512, 8192]；output=[512, 8192] | 0 | 4,194,304 | 0 | 16,777,216 | 8,388,608 |
| final_norm | 1 | input=[512, 8192]；weight=[8192]；output=[512, 8192] | 0 | 16,777,728 | 16,384 | 8,388,608 | 8,388,608 |
| lm_head | 1 | input=[512, 8192]；weight_math=[8192, 128256]；weight_storage=[128256, 8192]；output=[512, 128256] | 1,075,889,307,648 | 0 | 2,101,346,304 | 8,388,608 | 131,334,144 |

计量条件：

- Public DeepSeek-R1-Distill-Llama-70B; not renamed gated Llama3.1 checkpoint.
- Bias-free Llama GQA/SwiGLU forward; no Q/K normalization. Logits last/all/none explicit; tokenizer, sampling and CPU preprocessing outside scope.
- Equal-length batch, default position_ids=cache_position.unsqueeze(0); one contiguous position table history..history+tokens-1 shared across batch and layers. Explicit per-request position IDs are outside this adapter.
- Matrix work uses valid causal pairs; rectangular unfused attention work and FP32 score materialization reported separately. These are analytical operand loads, not a literal eager trace or measured HBM.
- Norm casts, RoPE casts, nonlinear functions and mask decisions listed separately; scalar intermediates are on-chip. Views/GQA repeat need not materialize.
- KV append assumes paged/in-place writes; old-cache torch.cat copies, allocator/kernel-launch overhead and backend workspace excluded.
- Weight/activation/KV byte widths are explicit scenario sensitivity, not proof of checkpoint quantization. Index confirms names only; no tensor headers or weights downloaded.
- Llama3 inverse-frequency initialization is separate from each forward; scaling-by1 remains in reference per-forward arithmetic. No latency prediction.

固定来源：

- [configs/models/deepseek-r1-distill-llama-70b/config.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/config.json)，SHA256 `95ef9768e4741543dbfaf0c274f101855883ff338b235c99eca2b6a4f4abee12`。
- [sources/deepseek-r1-distill-llama-70b/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/model.safetensors.index.json)，SHA256 `3b91e78c60e2708c9354d46fe4fc20520d0a12713e13d5ffab60118305c96620`。
- [sources/deepseek-r1-distill-llama-70b/README.md](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/README.md)，SHA256 `d26d26ddb518fee60c6c6bf7a708bd751b1619d93a4944f188143693d956c77f`。
- [sources/deepseek-r1-distill-llama-70b/modeling_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/modeling_llama.py)，SHA256 `9f7e93602e876a8f3f171e4911df5a5898ac407b8eb8982099e52b53daf0469e`。
- [sources/deepseek-r1-distill-llama-70b/configuration_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/configuration_llama.py)，SHA256 `c13469c62dc2c4fe76cc5bc50e6db2de21e302dae259945ef03308f0ac429ff6`。
- [research/llama70-adapter/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/modeling_rope_utils.py)，SHA256 `c28b3e88edca8fdb5497e5c36091bf753db49bd94ace33a84e9f9c61cbf66032`。
