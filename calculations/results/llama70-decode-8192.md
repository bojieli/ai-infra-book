# llama70-dense-forward — deepseek-r1-distill-llama-70b

输入：`{"activation_bytes": 2, "batch": 1, "history": 8192, "kv_bytes": 2, "output_head": "last", "score_bytes": 4, "tokens": 1, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 70,553,706,496 |
| weight_resident_bytes | 141,107,412,992 |
| backbone_projection_ffn_flops | 136,902,082,560 |
| causal_attention_matrix_flops | 21,477,457,920 |
| rectangular_attention_matrix_flops | 21,477,457,920 |
| matrix_flops | 160,480,886,784 |
| scalar_flops | 185,761,249 |
| special_ops | `{"sin": 128, "cos": 128, "cast_position_elements": 1, "cast_cos_sin_elements": 256, "concat_copy_elements": 128, "rsqrt": 161, "cast_elements": 2637824, "negate": 2662400, "exp": 44241920, "compare_max": 41943040, "mask_decisions": 41948160}` |
| weight_read_once_per_operator_bytes | 139,006,083,072 |
| activation_operand_read_bytes | 3,052,945,680 |
| activation_operand_write_bytes | 362,253,312 |
| kv_bytes_per_token_per_request | 327,680 |
| kv_resident_before_bytes | 2,684,354,560 |
| kv_resident_after_bytes | 2,684,682,240 |
| kv_new_write_bytes | 327,680 |
| kv_existing_history_unique_payload_bytes | 2,684,354,560 |
| kv_attention_unique_payload_bytes | 2,684,682,240 |
| kv_logical_query_head_operand_bytes | 21,477,457,920 |
| attention_score_tensor_per_layer_bytes | 2,097,408 |
| materialized_scores_probabilities_io_all_layers_bytes | 671,170,560 |
| minimum_required_weight_and_kv_bytes | 143,792,095,232 |

Llama3 RoPE初始化单独执行，不包含在下方每次forward总数中。

| 初始化 | 普通算术 | 特殊操作 | 常驻buffer bytes |
| --- | ---: | --- | ---: |
| llama3_inv_freq_initialization | 772 | {'pow': 64, 'compare': 192, 'logical_not': 128, 'logical_and': 64, 'where_select': 128, 'iota_elements': 64, 'cast_elements': 64} | 256 |

Fixed source eager arithmetic: default exponent division+reciprocal2n; wavelength n; scaled branch n; smooth3n; blend5n; two thresholds+high-low+2*pi4. torch.where evaluates full vectors in both branches. Intermediates are not assumed HBM. Original_inv_freq aliases same buffer; initialization excluded from forward totals.

| 每次forward特殊操作 | 层重复 | 单次计数 |
| --- | ---: | --- |
| llama3_rope_table | 1 | {'sin': 128, 'cos': 128, 'cast_position_elements': 1, 'cast_cos_sin_elements': 256, 'concat_copy_elements': 128} |
| input_layernorm | 80 | {'rsqrt': 1, 'cast_elements': 16384} |
| apply_rope | 80 | {'negate': 4608} |
| score_scale_mask_softmax | 80 | {'exp': 524352, 'compare_max': 524288, 'mask_decisions': 524352} |
| post_attention_layernorm | 80 | {'rsqrt': 1, 'cast_elements': 16384} |
| silu_mul | 80 | {'exp': 28672, 'negate': 28672} |
| final_norm | 1 | {'rsqrt': 1, 'cast_elements': 16384} |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[1, 1]；table=[128256, 8192]；output=[1, 8192] | 0 | 0 | 16,384 | 8 | 16,384 |
| llama3_rope_table | 1 | frequencies=[1, 1, 64]；cos_sin_each=[1, 1, 128] | 0 | 320 | 0 | 264 | 512 |
| input_layernorm | 80 | input=[1, 8192]；weight=[8192]；output=[1, 8192] | 0 | 32,769 | 16,384 | 16,384 | 16,384 |
| q_proj | 80 | input=[1, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[1, 8192] | 134,217,728 | 0 | 134,217,728 | 16,384 | 16,384 |
| k_proj | 80 | input=[1, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[1, 1024] | 16,777,216 | 0 | 16,777,216 | 16,384 | 2,048 |
| v_proj | 80 | input=[1, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[1, 1024] | 16,777,216 | 0 | 16,777,216 | 16,384 | 2,048 |
| apply_rope | 80 | Q=[1, 64, 1, 128]；K=[1, 8, 1, 128] | 0 | 27,648 | 0 | 18,944 | 18,432 |
| kv_append | 80 | new_K_and_V_each=[1, 8, 1, 128] | 0 | 0 | 0 | 4,096 | 4,096 |
| qk | 80 | Q=[1, 64, 1, 128]；K_shared=[1, 8, 8193, 128]；scores_rectangular=[1, 64, 1, 8193] | 134,234,112 | 0 | 0 | 16,795,648 | 2,097,408 |
| score_scale_mask_softmax | 80 | scores=[1, 64, 1, 8193] | 0 | 2,097,344 | 0 | 2,097,408 | 2,097,408 |
| pv | 80 | P=[1, 64, 1, 8193]；V_shared=[1, 8, 8193, 128]；output=[1, 64, 1, 128] | 134,234,112 | 0 | 0 | 18,876,672 | 16,384 |
| o_proj | 80 | input=[1, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[1, 8192] | 134,217,728 | 0 | 134,217,728 | 16,384 | 16,384 |
| attention_residual | 80 | inputs_each=[1, 8192]；output=[1, 8192] | 0 | 8,192 | 0 | 32,768 | 16,384 |
| post_attention_layernorm | 80 | input=[1, 8192]；weight=[8192]；output=[1, 8192] | 0 | 32,769 | 16,384 | 16,384 | 16,384 |
| gate_proj | 80 | input=[1, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[1, 28672] | 469,762,048 | 0 | 469,762,048 | 16,384 | 57,344 |
| up_proj | 80 | input=[1, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[1, 28672] | 469,762,048 | 0 | 469,762,048 | 16,384 | 57,344 |
| silu_mul | 80 | gate=[1, 28672]；up=[1, 28672]；output=[1, 28672] | 0 | 114,688 | 0 | 114,688 | 57,344 |
| down_proj | 80 | input=[1, 28672]；weight_math=[28672, 8192]；weight_storage=[8192, 28672]；output=[1, 8192] | 469,762,048 | 0 | 469,762,048 | 57,344 | 16,384 |
| ffn_residual | 80 | inputs_each=[1, 8192]；output=[1, 8192] | 0 | 8,192 | 0 | 32,768 | 16,384 |
| final_norm | 1 | input=[1, 8192]；weight=[8192]；output=[1, 8192] | 0 | 32,769 | 16,384 | 16,384 | 16,384 |
| lm_head | 1 | input=[1, 8192]；weight_math=[8192, 128256]；weight_storage=[128256, 8192]；output=[1, 128256] | 2,101,346,304 | 0 | 2,101,346,304 | 16,384 | 256,512 |

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
