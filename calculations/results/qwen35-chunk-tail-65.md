# Qwen3.5 基础文本参考执行账

BF16 纯文本、eager attention、非 export DeltaNet fallback；FMA=2。算术和张量接口不是实测 HBM、运行时间或完整显存峰值。

## 场景

```json
{
  "batch": 1,
  "tokens": 65,
  "history": 0,
  "output_head": "all",
  "routing_counts": null,
  "chunk_size": 64,
  "record_past": false
}
```

## 汇总

| 项 | 值 |
| --- | ---: |
| base_text_parameters | 396346350336 |
| base_checkpoint_bytes | 792692717952 |
| matrix_flops | 2179531092160 |
| scalar_flops | 7550178671 |
| reference_integer_operations | 40167965 |
| full_forward_exact | False |

特殊数学 primitive：`{"cos": 6240, "exp": 28732320, "max_comparisons": 3989700, "rsqrt": 602615, "sigmoid": 112011900, "sin": 6240, "softplus": 187200, "topk_selections": 3900}`。

## 执行路径与状态

```json
{
  "linear": {
    "kind": "reference_chunk_nonexport",
    "chunk_size": 64,
    "chunk_iterations": 2,
    "token_iterations": 65,
    "padded_tokens": 128,
    "triangular_solves_per_chunk": 2
  },
  "conv": {
    "input_positions": 65,
    "conv_output_positions_before_slice": 68,
    "silu_positions_before_final_crop": 65,
    "source_path": "padded_fn",
    "record_past_shape_known": true
  },
  "state": {
    "full_kv_before_bytes": 0,
    "full_kv_after_bytes": 1996800,
    "full_kv_append_bytes": 1996800,
    "linear_recurrent_fp32_bytes": 188743680,
    "linear_conv_slot_elements": 2211840,
    "linear_conv_dtype": "input activation dtype; declared BF16 path",
    "linear_conv_slot_bytes": 4423680,
    "record_past_extra_allocation_bytes": 0,
    "record_past_retained_conv_bytes": 4423680
  }
}
```

## 按类别累计工作

| 类别 | matrix FLOPs | scalar FLOPs |
| --- | ---: | ---: |
| activation | 0 | 203673600 |
| attention_matrix | 1054310400 | 0 |
| copy | 0 | 0 |
| depthwise_conv | 280903680 | 0 |
| elementwise | 0 | 228679680 |
| gate | 0 | 374400 |
| gather | 0 | 0 |
| linear | 2122795417600 | 0 |
| normalization | 0 | 427114871 |
| reference_supplement | 1042280640 | 408909600 |
| rotary | 0 | 6364800 |
| router | 0 | 6060600 |
| routing | 0 | 319488000 |
| softmax | 0 | 4087200 |
| state_matrix | 54358179840 | 0 |
| triangular_solve | 0 | 5945425920 |

## 补充源码语句接口

**此表与算子边界 bytes 存在重叠，禁止将两者相加成 HBM 或全模型流量。** 完整权重、算子形状和逐项重复次数保留在 JSON。

| 语句 | 次数 | 每次输入 bytes | 每次输出 bytes |
| --- | ---: | ---: | ---: |
| conv.additional_padded_and_discarded_products | 45 | 1597440 | 1671168 |
| conv.extra_silu_before_final_crop | 45 | 1597440 | 1597440 |
| conv.cache_concat_or_initial_pad | 45 | 0 | 0 |
| conv.cache_copy_last4 | 45 | 98304 | 98304 |
| conv.cache_initial_zero | 45 | 0 | 98304 |
| chunk.fp32_input_casts | 45 | 3219840 | 6423040 |
| chunk.pad_q_k_v_beta_g | 45 | 6423040 | 12648448 |
| chunk.beta_K_V | 5760 | 65792 | 65536 |
| chunk.cumsum | 5760 | 256 | 256 |
| chunk.triu_mask_construction | 45 | 0 | 4096 |
| chunk.pairwise_decay_difference_mask_exp | 5760 | 4608 | 49152 |
| chunk.ut_and_intra_decay_multiply | 5760 | 65536 | 32768 |
| chunk.exp_cum_for_decayed_Kbeta | 5760 | 33024 | 33024 |
| chunk.exp_cum_for_Q | 5760 | 33024 | 33024 |
| chunk.last_minus_cum_exp_for_K | 5760 | 33028 | 33280 |
| chunk.exp_final_decay | 5760 | 4 | 4 |
| chunk.unit_triangular_solver_interfaces | 5760 | 98304 | 65536 |
| chunk.scan_vnew_subtract | 5760 | 65536 | 32768 |
| chunk.scan_output_add | 5760 | 65536 | 32768 |
| chunk.scan_state_decay_add | 5760 | 196612 | 131072 |
| chunk.initial_state_zeros | 45 | 0 | 4194304 |
| chunk.output_zeros_and_indexed_writes | 45 | 0 | 8388608 |
| chunk.crop_and_output_cast | 45 | 2129920 | 1064960 |
| linear.cache_update_recurrent_copy | 45 | 4194304 | 4194304 |
| linear.cache_recurrent_initial_zero | 45 | 0 | 4194304 |
| rope.position_arange_and_history_add | 1 | 0 | 520 |
| rope.position_ids_fp32_cast | 1 | 1560 | 780 |
| rope.frequency_outer_product | 1 | 1164 | 24960 |
| rope.sin_cos_and_scaling | 1 | 49920 | 99840 |
| rope.recompose_and_duplicate | 1 | 44200 | 44200 |
| rope.cast_BF16 | 1 | 33280 | 16640 |
| rope.rotate_half_negation | 15 | 141440 | 141440 |
| rope.concat_rotated_and_passthrough | 15 | 1131520 | 1131520 |
| full.eager_masked_matrix_slots | 15 | 0 | 0 |
| full.eager_additional_softmax_and_mask | 15 | 0 | 0 |
| full.kv_cache_concat | 15 | 0 | 0 |
| full.repeat_kv_logical_materialization | 15 | 133120 | 2129920 |
| full.QK_interfaces | 15 | 2129920 | 270400 |
| full.scale_mask_softmax_cast_interfaces | 15 | 1352000 | 1352000 |
| full.PV_interfaces | 15 | 1335360 | 1064960 |
| full.transpose_contiguous | 15 | 1064960 | 1064960 |
| mask.arange_offsets | 1 | 0 | 2096 |
| mask.causal_compare_before_batch_expand | 1 | 1040 | 4225 |
| mask.bool_to_BF16_where | 1 | 4225 | 8450 |
| router.logits_cast_softmax | 60 | 199680 | 266240 |
| router.topk_primitive_interfaces | 60 | 133120 | 7800 |
| router.probability_cast_and_selected_renorm | 60 | 8060 | 4160 |
| router.one_hot_initialize_scatter | 60 | 5200 | 2667600 |
| router.expert_hit_reduce_compare_nonzero | 60 | 2667008 | 8704 |
| router.where_per_active_expert | 60 | 2662400 | 10400 |
| router.input_gather | 60 | 5330000 | 5324800 |
| router.probability_gather | 60 | 11700 | 1300 |
| router.destination_zero_fill | 60 | 0 | 532480 |
| router.index_add_destination_interfaces | 60 | 10654800 | 5324800 |
| norm.layer_input_and_post.input_fp32_cast | 120 | 532480 | 1064960 |
| norm.layer_input_and_post.square_mean_epsilon_rsqrt | 120 | 2130440 | 1065740 |
| norm.layer_input_and_post.normalize_multiply | 120 | 1065220 | 1064960 |
| norm.layer_input_and_post.weight_cast_plus_one | 120 | 24576 | 32768 |
| norm.layer_input_and_post.weight_multiply_output_cast | 120 | 2146304 | 1597440 |
| norm.full_Q.input_fp32_cast | 15 | 1064960 | 2129920 |
| norm.full_Q.square_mean_epsilon_rsqrt | 15 | 4276480 | 2154880 |
| norm.full_Q.normalize_multiply | 15 | 2138240 | 2129920 |
| norm.full_Q.weight_cast_plus_one | 15 | 1536 | 2048 |
| norm.full_Q.weight_multiply_output_cast | 15 | 4260864 | 3194880 |
| norm.full_K.input_fp32_cast | 15 | 66560 | 133120 |
| norm.full_K.square_mean_epsilon_rsqrt | 15 | 267280 | 134680 |
| norm.full_K.normalize_multiply | 15 | 133640 | 133120 |
| norm.full_K.weight_cast_plus_one | 15 | 1536 | 2048 |
| norm.full_K.weight_multiply_output_cast | 15 | 267264 | 199680 |
| norm.final.input_fp32_cast | 1 | 532480 | 1064960 |
| norm.final.square_mean_epsilon_rsqrt | 1 | 2130440 | 1065740 |
| norm.final.normalize_multiply | 1 | 1065220 | 1064960 |
| norm.final.weight_cast_plus_one | 1 | 24576 | 32768 |
| norm.final.weight_multiply_output_cast | 1 | 2146304 | 1597440 |
| norm.linear_gated.input_fp32_cast | 45 | 1064960 | 2129920 |
| norm.linear_gated.square_mean_epsilon_rsqrt | 45 | 4293120 | 2179840 |
| norm.linear_gated.normalize_multiply | 45 | 2146560 | 2129920 |
| norm.linear_gated.normalized_cast_weight_multiply | 45 | 3195136 | 2129920 |
| norm.linear_gated.z_cast_silu | 45 | 3194880 | 4259840 |
| norm.linear_gated.gate_multiply_final_cast | 45 | 5324800 | 3194880 |
| linear.A_exp_negation | 45 | 512 | 512 |
| linear.a_dt_softplus_decay_multiply | 45 | 58624 | 66560 |
| linear.b_sigmoid | 45 | 8320 | 8320 |
| linear.qk_norm_internal | 45 | 12879360 | 8619520 |
| linear.query_scale_interface | 45 | 2129920 | 2129920 |
| moe.routed_silu_and_up_multiply | 60 | 3993600 | 2662400 |
| moe.routed_probability_multiply | 60 | 5326100 | 5324800 |
| moe.shared_silu_and_up_multiply | 60 | 399360 | 266240 |
| moe.shared_gate_sigmoid_multiply_combine | 60 | 1597700 | 1065090 |
| full.output_gate_sigmoid_multiply | 15 | 3194880 | 2129920 |

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

- [configs/models/qwen3.5-397b-a17b/config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `3ae7fa89c2f7d1354096418ddaf1331e9e0898a8ca11e804fb6dbaa087efb7da`。
- [research/f02-qwen35-inputs/model/README.md](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/README.md)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `bda4b24e975f65ac677985306ddbad33362e65064637660654c8bb7dea7edf50`。
- [research/f02-qwen35-inputs/model/config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `3ae7fa89c2f7d1354096418ddaf1331e9e0898a8ca11e804fb6dbaa087efb7da`。
- [research/f02-qwen35-inputs/model/generation_config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/generation_config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `303aba891d66ab63908a7b3cc9163bcb835fdf8b9f6301c73216f3f1eb3992dd`。
- [research/f02-qwen35-inputs/model/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/model.safetensors.index.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `407d6a184a29469034ad92bcfaa6b72b582f8ad6afcbfad18a38a1c59ed296f8`。
- [research/f02-qwen35-inputs/model/preprocessor_config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/preprocessor_config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516`。
- [research/f02-qwen35-inputs/model/tokenizer_config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/tokenizer_config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8`。
- [research/f02-qwen35-inputs/model/video_preprocessor_config.json](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/8472618112abcbd45acbcdc58436aff4233c23f7/video_preprocessor_config.json)；revision `8472618112abcbd45acbcdc58436aff4233c23f7`；SHA `7768af27c1fafa9cc9011c1dc20067e03f8915e03b63504550e11d5066986d13`。
- [research/f02-qwen35-inputs/transformers/src/transformers/cache_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/cache_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `702144bb44553f6339ea1bf23c8205a708bb5f8c7c09cb3a2db484182646743c`。
- [research/f02-qwen35-inputs/transformers/src/transformers/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/modeling_rope_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `60438ad10eceddc1809b35256eb8de4492f759888bd929d9f3ae971fa255c60f`。
- [research/f02-qwen35-inputs/transformers/src/transformers/models/qwen3_5_moe/__init__.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/__init__.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `bbad751c2169cb9cc52cd13d53401ed0171a4f980e8dad48c3f6fb339ecab30d`。
- [research/f02-qwen35-inputs/transformers/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/configuration_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `9f68bcddc54b4e512802e18ec8a242514d7f746795b28373805d3e05a981f573`。
- [research/f02-qwen35-inputs/transformers/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `3f89026abe4e89ee42797fcf01a29dafaa961533e279fcb193d02999ef5251ca`。
- [research/f02-qwen35-inputs/transformers/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `20c4291118bb4d2ab967d91470033d5250447d7c4cdda3fdd3f44d3de9fd47ab`。
- [research/f02-qwen35-inputs/transformers/src/transformers/vision_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/vision_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `bcecd5a92b3266b9926272a549d2b1a0f1fe7646c698c0fa19bd96f976085356`。
- [research/f02-qwen35-inputs/transformers/tests/models/qwen3_5_moe/__init__.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/__init__.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- [research/f02-qwen35-inputs/transformers/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/tests/models/qwen3_5_moe/test_modeling_qwen3_5_moe.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `693d82ca256b39e9f9267d12a6a557bd09c3bca299304d3f5ba7fc6342c86f1a`。
- [sources/qwen3.5-397b-a17b/masking_utils.py](https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/masking_utils.py)；revision `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`；SHA `50a737f63d8c778a5597fa34ac139049af921f44958205e3e1c29fe2bae77254`。
