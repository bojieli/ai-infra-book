# llama70-dense-forward — deepseek-r1-distill-llama-70b

输入：`{"activation_bytes": 2, "batch": 1, "history": 0, "kv_bytes": 2, "output_head": "last", "score_bytes": 4, "tokens": 8192, "weight_bytes": 2}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 70,553,706,496 |
| weight_resident_bytes | 141,107,412,992 |
| backbone_projection_ffn_flops | 1,121,501,860,331,520 |
| causal_attention_matrix_flops | 87,971,667,640,320 |
| rectangular_attention_matrix_flops | 175,921,860,444,160 |
| matrix_flops | 1,209,475,629,318,144 |
| scalar_flops | 834,477,498,368 |
| special_ops | `{"sin": 1048576, "cos": 1048576, "cast_position_elements": 8192, "cast_cos_sin_elements": 2097152, "concat_copy_elements": 1048576, "rsqrt": 1318912, "cast_elements": 21609054208, "negate": 21810380800, "exp": 190610145280, "compare_max": 171777720320, "mask_decisions": 343597383680}` |
| weight_read_once_per_operator_bytes | 139,140,284,416 |
| activation_operand_read_bytes | 3,019,026,612,480 |
| activation_operand_write_bytes | 2,965,142,497,792 |
| kv_bytes_per_token_per_request | 327,680 |
| kv_resident_before_bytes | 0 |
| kv_resident_after_bytes | 2,684,354,560 |
| kv_new_write_bytes | 2,684,354,560 |
| kv_existing_history_unique_payload_bytes | 0 |
| kv_attention_unique_payload_bytes | 2,684,354,560 |
| kv_logical_query_head_operand_bytes | 87,971,667,640,320 |
| attention_score_tensor_per_layer_bytes | 17,179,869,184 |
| materialized_scores_probabilities_io_all_layers_bytes | 5,497,558,138,880 |
| minimum_required_weight_and_kv_bytes | 143,791,767,552 |

Llama3 RoPE初始化单独执行，不包含在下方每次forward总数中。

| 初始化 | 普通算术 | 特殊操作 | 常驻buffer bytes |
| --- | ---: | --- | ---: |
| llama3_inv_freq_initialization | 772 | {'pow': 64, 'compare': 192, 'logical_not': 128, 'logical_and': 64, 'where_select': 128, 'iota_elements': 64, 'cast_elements': 64} | 256 |

Fixed source eager arithmetic: default exponent division+reciprocal2n; wavelength n; scaled branch n; smooth3n; blend5n; two thresholds+high-low+2*pi4. torch.where evaluates full vectors in both branches. Intermediates are not assumed HBM. Original_inv_freq aliases same buffer; initialization excluded from forward totals.

| 每次forward特殊操作 | 层重复 | 单次计数 |
| --- | ---: | --- |
| llama3_rope_table | 1 | {'sin': 1048576, 'cos': 1048576, 'cast_position_elements': 8192, 'cast_cos_sin_elements': 2097152, 'concat_copy_elements': 1048576} |
| input_layernorm | 80 | {'rsqrt': 8192, 'cast_elements': 134217728} |
| apply_rope | 80 | {'negate': 37748736} |
| score_scale_mask_softmax | 80 | {'exp': 2147745792, 'compare_max': 2147221504, 'mask_decisions': 4294967296} |
| post_attention_layernorm | 80 | {'rsqrt': 8192, 'cast_elements': 134217728} |
| silu_mul | 80 | {'exp': 234881024, 'negate': 234881024} |
| final_norm | 1 | {'rsqrt': 8192, 'cast_elements': 134217728} |

每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。

| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| embedding | 1 | indices=[1, 8192]；table=[128256, 8192]；output=[8192, 8192] | 0 | 0 | 134,217,728 | 65,536 | 134,217,728 |
| llama3_rope_table | 1 | frequencies=[1, 8192, 64]；cos_sin_each=[1, 8192, 128] | 0 | 2,621,440 | 0 | 65,792 | 4,194,304 |
| input_layernorm | 80 | input=[8192, 8192]；weight=[8192]；output=[8192, 8192] | 0 | 268,443,648 | 16,384 | 134,217,728 | 134,217,728 |
| q_proj | 80 | input=[8192, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[8192, 8192] | 1,099,511,627,776 | 0 | 134,217,728 | 134,217,728 | 134,217,728 |
| k_proj | 80 | input=[8192, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[8192, 1024] | 137,438,953,472 | 0 | 16,777,216 | 134,217,728 | 16,777,216 |
| v_proj | 80 | input=[8192, 8192]；weight_math=[8192, 1024]；weight_storage=[1024, 8192]；output=[8192, 1024] | 137,438,953,472 | 0 | 16,777,216 | 134,217,728 | 16,777,216 |
| apply_rope | 80 | Q=[1, 64, 8192, 128]；K=[1, 8, 8192, 128] | 0 | 226,492,416 | 0 | 155,189,248 | 150,994,944 |
| kv_append | 80 | new_K_and_V_each=[1, 8, 8192, 128] | 0 | 0 | 0 | 33,554,432 | 33,554,432 |
| qk | 80 | Q=[1, 64, 8192, 128]；K_shared=[1, 8, 8192, 128]；scores_rectangular=[1, 64, 8192, 8192] | 549,822,922,752 | 0 | 0 | 150,994,944 | 17,179,869,184 |
| score_scale_mask_softmax | 80 | scores=[1, 64, 8192, 8192] | 0 | 8,590,458,880 | 0 | 17,179,869,184 | 17,179,869,184 |
| pv | 80 | P=[1, 64, 8192, 8192]；V_shared=[1, 8, 8192, 128]；output=[1, 64, 8192, 128] | 549,822,922,752 | 0 | 0 | 17,196,646,400 | 134,217,728 |
| o_proj | 80 | input=[8192, 8192]；weight_math=[8192, 8192]；weight_storage=[8192, 8192]；output=[8192, 8192] | 1,099,511,627,776 | 0 | 134,217,728 | 134,217,728 | 134,217,728 |
| attention_residual | 80 | inputs_each=[8192, 8192]；output=[8192, 8192] | 0 | 67,108,864 | 0 | 268,435,456 | 134,217,728 |
| post_attention_layernorm | 80 | input=[8192, 8192]；weight=[8192]；output=[8192, 8192] | 0 | 268,443,648 | 16,384 | 134,217,728 | 134,217,728 |
| gate_proj | 80 | input=[8192, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[8192, 28672] | 3,848,290,697,216 | 0 | 469,762,048 | 134,217,728 | 469,762,048 |
| up_proj | 80 | input=[8192, 8192]；weight_math=[8192, 28672]；weight_storage=[28672, 8192]；output=[8192, 28672] | 3,848,290,697,216 | 0 | 469,762,048 | 134,217,728 | 469,762,048 |
| silu_mul | 80 | gate=[8192, 28672]；up=[8192, 28672]；output=[8192, 28672] | 0 | 939,524,096 | 0 | 939,524,096 | 469,762,048 |
| down_proj | 80 | input=[8192, 28672]；weight_math=[28672, 8192]；weight_storage=[8192, 28672]；output=[8192, 8192] | 3,848,290,697,216 | 0 | 469,762,048 | 469,762,048 | 134,217,728 |
| ffn_residual | 80 | inputs_each=[8192, 8192]；output=[8192, 8192] | 0 | 67,108,864 | 0 | 268,435,456 | 134,217,728 |
| final_norm | 1 | input=[8192, 8192]；weight=[8192]；output=[8192, 8192] | 0 | 268,443,648 | 16,384 | 134,217,728 | 134,217,728 |
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
