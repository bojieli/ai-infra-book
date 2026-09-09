# Qwen3.6-35B-A3B 基础文本参考执行账

BF16 纯文本、eager attention、非 export DeltaNet fallback；FMA=2。算术和张量接口不是实测 HBM、运行时间或完整显存峰值。

## 场景

```json
{
  "batch": 64,
  "tokens": 1,
  "history": 8192,
  "output_head": "all",
  "routing_counts": [
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
  ],
  "chunk_size": 64,
  "record_past": false
}
```

## 汇总

| 项 | 值 |
| --- | ---: |
| base_text_parameters | 34660610688 |
| base_checkpoint_bytes | 69321221376 |
| matrix_flops | 469195829248 |
| scalar_flops | 1750101248 |
| reference_integer_operations | 5967940 |
| full_forward_exact | False |

特殊数学 primitive：`{"cos": 6144, "exp": 84614080, "max_comparisons": 84538880, "rsqrt": 201024, "sigmoid": 38074880, "sin": 6144, "softplus": 61440, "topk_selections": 2560}`。

## 执行路径与状态

```json
{
  "linear": {
    "kind": "reference_recurrent",
    "token_iterations": 1,
    "chunk_iterations": 0,
    "padded_tokens": 1
  },
  "conv": {
    "input_positions": 5,
    "conv_output_positions_before_slice": 2,
    "silu_positions_before_final_crop": 1,
    "source_path": "update",
    "record_past_shape_known": true
  },
  "state": {
    "full_kv_before_bytes": 10737418240,
    "full_kv_after_bytes": 10738728960,
    "full_kv_append_bytes": 1310720,
    "linear_recurrent_fp32_bytes": 4026531840,
    "linear_conv_slot_elements": 62914560,
    "linear_conv_dtype": "input activation dtype; declared BF16 path",
    "linear_conv_slot_bytes": 125829120,
    "record_past_extra_allocation_bytes": 0,
    "record_past_retained_conv_bytes": 125829120
  }
}
```

## 按类别累计工作

| 类别 | matrix FLOPs | scalar FLOPs |
| --- | ---: | ---: |
| activation | 0 | 65536000 |
| attention_matrix | 85909831680 | 0 |
| copy | 0 | 0 |
| depthwise_conv | 125829120 | 0 |
| elementwise | 0 | 1035468800 |
| gate | 0 | 122880 |
| gather | 0 | 0 |
| linear | 376994529280 | 0 |
| normalization | 0 | 141020480 |
| reference_supplement | 125841408 | 84278208 |
| rotary | 0 | 2211840 |
| router | 0 | 2001920 |
| routing | 0 | 83886080 |
| softmax | 0 | 335575040 |
| state_matrix | 6039797760 | 0 |

## 补充源码语句接口

**此表与算子边界 bytes 存在重叠，禁止将两者相加成 HBM 或全模型流量。** 完整权重、算子形状和逐项重复次数保留在 JSON。

| 语句 | 次数 | 每次输入 bytes | 每次输出 bytes |
| --- | ---: | ---: | ---: |
| conv.additional_padded_and_discarded_products | 30 | 5242880 | 2097152 |
| conv.extra_silu_before_final_crop | 30 | 1048576 | 1048576 |
| conv.cache_concat_or_initial_pad | 30 | 5242880 | 5242880 |
| conv.cache_copy_last4 | 30 | 4194304 | 4194304 |
| recurrent.fp32_casts | 30 | 1585152 | 3162112 |
| recurrent.decay_exp_interface | 30 | 8192 | 8192 |
| recurrent.decay_state_interface | 30 | 134225920 | 134217728 |
| recurrent.K_state_products_and_reduce | 30 | 135266304 | 135266304 |
| recurrent.delta_subtract_beta_multiply | 30 | 4202496 | 2097152 |
| recurrent.outer_product_and_state_add | 30 | 270532608 | 268435456 |
| recurrent.Q_state_products_and_reduce | 30 | 135266304 | 135266304 |
| recurrent.output_zero_assignment_cast | 30 | 1048576 | 2621440 |
| linear.cache_update_recurrent_copy | 30 | 134217728 | 134217728 |
| rope.position_arange_and_history_add | 1 | 0 | 8 |
| rope.position_ids_fp32_cast | 1 | 1536 | 768 |
| rope.frequency_outer_product | 1 | 25344 | 24576 |
| rope.sin_cos_and_scaling | 1 | 49152 | 98304 |
| rope.recompose_and_duplicate | 1 | 43520 | 43520 |
| rope.cast_BF16 | 1 | 32768 | 16384 |
| rope.rotate_half_negation | 10 | 73728 | 73728 |
| rope.concat_rotated_and_passthrough | 10 | 589824 | 589824 |
| full.eager_masked_matrix_slots | 10 | 0 | 0 |
| full.eager_additional_softmax_and_mask | 10 | 0 | 0 |
| full.kv_cache_concat | 10 | 1073872896 | 1073872896 |
| full.repeat_kv_logical_materialization | 10 | 1073872896 | 8590983168 |
| full.QK_interfaces | 10 | 4296015872 | 16779264 |
| full.scale_mask_softmax_cast_interfaces | 10 | 83896320 | 83896320 |
| full.PV_interfaces | 10 | 4312270848 | 524288 |
| full.transpose_contiguous | 10 | 524288 | 524288 |
| mask.arange_offsets | 1 | 0 | 131624 |
| mask.causal_compare_before_batch_expand | 1 | 65552 | 8193 |
| mask.bool_to_BF16_where | 1 | 524352 | 1048704 |
| router.logits_cast_softmax | 40 | 98304 | 131072 |
| router.topk_primitive_interfaces | 40 | 65536 | 6144 |
| router.probability_cast_and_selected_renorm | 40 | 6400 | 3328 |
| router.one_hot_initialize_scatter | 40 | 4096 | 1052672 |
| router.expert_hit_reduce_compare_nonzero | 40 | 1050880 | 2368 |
| router.where_per_active_expert | 40 | 32768 | 8192 |
| router.input_gather | 40 | 2101248 | 2097152 |
| router.probability_gather | 40 | 9216 | 1024 |
| router.destination_zero_fill | 40 | 0 | 262144 |
| router.index_add_destination_interfaces | 40 | 4198400 | 2097152 |
| norm.layer_input_and_post.input_fp32_cast | 80 | 262144 | 524288 |
| norm.layer_input_and_post.square_mean_epsilon_rsqrt | 80 | 1049088 | 525056 |
| norm.layer_input_and_post.normalize_multiply | 80 | 524544 | 524288 |
| norm.layer_input_and_post.weight_cast_plus_one | 80 | 12288 | 16384 |
| norm.layer_input_and_post.weight_multiply_output_cast | 80 | 1056768 | 786432 |
| norm.full_Q.input_fp32_cast | 10 | 524288 | 1048576 |
| norm.full_Q.square_mean_epsilon_rsqrt | 10 | 2105344 | 1060864 |
| norm.full_Q.normalize_multiply | 10 | 1052672 | 1048576 |
| norm.full_Q.weight_cast_plus_one | 10 | 1536 | 2048 |
| norm.full_Q.weight_multiply_output_cast | 10 | 2098176 | 1572864 |
| norm.full_K.input_fp32_cast | 10 | 65536 | 131072 |
| norm.full_K.square_mean_epsilon_rsqrt | 10 | 263168 | 132608 |
| norm.full_K.normalize_multiply | 10 | 131584 | 131072 |
| norm.full_K.weight_cast_plus_one | 10 | 1536 | 2048 |
| norm.full_K.weight_multiply_output_cast | 10 | 263168 | 196608 |
| norm.final.input_fp32_cast | 1 | 262144 | 524288 |
| norm.final.square_mean_epsilon_rsqrt | 1 | 1049088 | 525056 |
| norm.final.normalize_multiply | 1 | 524544 | 524288 |
| norm.final.weight_cast_plus_one | 1 | 12288 | 16384 |
| norm.final.weight_multiply_output_cast | 1 | 1056768 | 786432 |
| norm.linear_gated.input_fp32_cast | 30 | 524288 | 1048576 |
| norm.linear_gated.square_mean_epsilon_rsqrt | 30 | 2113536 | 1073152 |
| norm.linear_gated.normalize_multiply | 30 | 1056768 | 1048576 |
| norm.linear_gated.normalized_cast_weight_multiply | 30 | 1573120 | 1048576 |
| norm.linear_gated.z_cast_silu | 30 | 1572864 | 2097152 |
| norm.linear_gated.gate_multiply_final_cast | 30 | 2621440 | 1572864 |
| linear.A_fp32_cast | 30 | 64 | 128 |
| linear.A_exp_negation | 30 | 256 | 256 |
| linear.a_dt_softplus_decay_multiply | 30 | 28864 | 32768 |
| linear.b_sigmoid | 30 | 4096 | 4096 |
| linear.qk_norm_internal | 30 | 6340608 | 4243456 |
| linear.query_scale_interface | 30 | 1048576 | 1048576 |
| moe.routed_silu_and_up_multiply | 40 | 1572864 | 1048576 |
| moe.routed_probability_multiply | 40 | 2098176 | 2097152 |
| moe.shared_silu_and_up_multiply | 40 | 196608 | 131072 |
| moe.shared_gate_sigmoid_multiply_combine | 40 | 786688 | 524416 |
| full.output_gate_sigmoid_multiply | 10 | 1572864 | 1048576 |

## 未证明的范围

- Whole-model exact runtime work is not claimed: torch triangular solver, softmax/topk/where/reduction algorithms and hub kernel replacements have backend-dependent instruction counts.
- record_past=True with pre-existing recorded convolution history has unknown retained length; source conv work and extra log allocation remain unknown for that case. Default record_past=False prefill/decode conv padded slots and cached recomputation are enumerated.
- Reference chunk nonexport preparation and scan arithmetic, shared text RoPE construction, eager rectangular attention, conv source slots, router one_hot/where/gather have explicit supplemental records. Export inverse-construction path is not selected.
- Plain-text eager causal-mask construction is counted from additionally pinned masking_utils: no external padding/custom packed mask is accepted by this interface; those different inputs require separate scope.
- Operator boundary bytes and supplementary statement interfaces overlap and cannot be summed into a single complete traffic result; norm/gate casts now have statement records, but view aliasing, primitive internal workspace and allocator lifetimes are not actual traffic or peak memory. No HBM or memory peak claimed.
- Vision/MTP excluded; output_head all is source default, last/none explicit narrower scopes; no payload numerical inference execution.
- All base-text weights enumerated including shared experts, gates, verified A_log/dt_bias checkpoint dtypes and embedding/head; checkpoint bytes are not runtime allocated memory.
- Linear-state provenance is caller supplied via history; identical input histories/positions/cache dtype required. No engine execution or payload numerical validation.
- Every operator interface is logical per-call payload; repeated sums are not peak allocation or HBM. Scalar and special operations must not be folded into Tensor Core FLOPs.

## 固定原件

- [sources/qwen3.6-35b-a3b/model/LICENSE](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/LICENSE)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `50cbab8a892c5f2993b8c7351a99182507472def3b1374558308605d99b86b32`。
- [sources/qwen3.6-35b-a3b/model/README.md](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/README.md)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `c4ddaa065649ff6352648f64747a16eda31726f3e34add94ce04abb461c77b75`。
- [configs/models/qwen3.6-35b-a3b/config.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/config.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `93a4693fa9d8392fbfccd4b3c9873f4bfdcb14fdede978b123d07d19675efe99`。
- [sources/qwen3.6-35b-a3b/model/generation_config.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/generation_config.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e`。
- [sources/qwen3.6-35b-a3b/model/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/model.safetensors.index.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `41b9356101ebf8e7519e150dc811f80c4226e727301fbb032b890f006ed0be83`。
- [sources/qwen3.6-35b-a3b/model/preprocessor_config.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/preprocessor_config.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [sources/qwen3.6-35b-a3b/model/tokenizer_config.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/tokenizer_config.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `5186f0defcd7f232382c7f0aebcd2252d073bb921ab240e407b7ae8745d2b29b`。
- [sources/qwen3.6-35b-a3b/model/video_preprocessor_config.json](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/resolve/995ad96eacd98c81ed38be0c5b274b04031597b0/video_preprocessor_config.json)；revision `995ad96eacd98c81ed38be0c5b274b04031597b0`；SHA `7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/cache_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/cache_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `702144bb44553f6339ea1bf23c8205a708bb5f8c7c09cb3a2db484182646743c`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/masking_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/masking_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `50a737f63d8c778a5597fa34ac139049af921f44958205e3e1c29fe2bae77254`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/modeling_rope_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `60438ad10eceddc1809b35256eb8de4492f759888bd929d9f3ae971fa255c60f`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/__init__.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/__init__.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `bbad751c2169cb9cc52cd13d53401ed0171a4f980e8dad48c3f6fb339ecab30d`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `9f68bcddc54b4e512802e18ec8a242514d7f746795b28373805d3e05a981f573`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `3f89026abe4e89ee42797fcf01a29dafaa961533e279fcb193d02999ef5251ca`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `20c4291118bb4d2ab967d91470033d5250447d7c4cdda3fdd3f44d3de9fd47ab`。
- [sources/qwen3.6-35b-a3b/transformers/src/transformers/vision_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356`。
- [sources/qwen3.6-35b-a3b/transformers/tests/models/qwen3_5_moe/__init__.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/__init__.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- [sources/qwen3.6-35b-a3b/transformers/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `693d82ca256b39e9f9267d12a6a557bd09c3bca299304d3f5ba7fc6342c86f1a`。
