# RGB预处理到视觉入口逐阶段账

固定官方Qwen配置与CPU generic uint8 bicubic-AA；完整范围与数值证明见CONTRACT.md/numeric-verification.json。

| 场景 | Resize | Patch shape | FP32输出B | BF16入口B | 语义读B | 语义写B |
|---|---|---|---:|---:|---:|---:|
| vision-preprocess-aligned640 | 640×640 | [1600, 1536] | 9830400 | 4915200 | 41779224 | 30720072 |
| vision-preprocess-nonsquare | 256×384 | [384, 1536] | 2359296 | 1179648 | 17185865 | 8051499 |
| vision-preprocess-min-area | 256×256 | [256, 1536] | 1572864 | 786432 | 9114648 | 5000776 |
| vision-preprocess-max-area | 4096×4096 | [65536, 1536] | 402653184 | 201326592 | 3169112920 | 1379745768 |

## 257×385 非方形逐阶段

| 阶段 | 读B | 写B | 操作 |
|---|---:|---:|---|
| smart_resize_geometry | 0 | 0 | {"python_round": 2, "python_sqrt": 0} |
| numpy_to_torch_alias | 0 | 0 | {} |
| HWC_to_CHW_contiguous | 296835 | 296835 | {"element_copy": 296835} |
| CPU_group_unsqueeze_before_resize | 0 | 0 | {} |
| width_coefficient_setup | 46048 | 51440 | {"fp64_axis_scale_divide": 1, "fp64_support_multiply": 1, "fp64_axis_support_ceil": 1, "fp64_per_coordinate_inverse_scale_divide": 384, "fp64_range_add_sub": 1536, "fp64_range_to_int64": 768, "fp64_weight_max_compare": 1918, "fp64_precision_scale_multiply": 16, "fp64_precision_round_add": 16, "fp64_quantize_sign_compare": 2688, "int64_index_array_store": 1536, "fp64_center_multiply": 384, "fp64_center_add": 384, "fp64_filter_argument_subtract": 1534, "fp64_filter_argument_add": 1534, "fp64_filter_argument_multiply": 1534, "fp64_abs": 1534, "fp64_cubic_multiply": 4602, "fp64_cubic_add_sub": 3834, "fp64_weight_sum_add": 1534, "fp64_weight_normalize_divide": 1534, "fp64_quantize_multiply": 2688, "fp64_quantize_add": 2688, "float_to_integer_cast": 2688} |
| width_uint8_separable_convolution | 3548142 | 296064 | {"int32_multiply": 1182714, "int32_add": 1182714, "int32_rounding_bias_init": 296064, "int32_right_shift": 296064, "int32_clamp": 296064, "uint8_store": 296064} |
| height_coefficient_setup | 30688 | 34288 | {"fp64_axis_scale_divide": 1, "fp64_support_multiply": 1, "fp64_axis_support_ceil": 1, "fp64_per_coordinate_inverse_scale_divide": 256, "fp64_range_add_sub": 1024, "fp64_range_to_int64": 512, "fp64_weight_max_compare": 1278, "fp64_precision_scale_multiply": 16, "fp64_precision_round_add": 16, "fp64_quantize_sign_compare": 1792, "int64_index_array_store": 1024, "fp64_center_multiply": 256, "fp64_center_add": 256, "fp64_filter_argument_subtract": 1022, "fp64_filter_argument_add": 1022, "fp64_filter_argument_multiply": 1022, "fp64_abs": 1022, "fp64_cubic_multiply": 3066, "fp64_cubic_add_sub": 2554, "fp64_weight_sum_add": 1022, "fp64_weight_normalize_divide": 1022, "fp64_quantize_multiply": 1792, "fp64_quantize_add": 1792, "float_to_integer_cast": 1792} |
| height_uint8_separable_convolution | 3532032 | 294912 | {"int32_multiply": 1177344, "int32_add": 1177344, "int32_rounding_bias_init": 294912, "int32_right_shift": 294912, "int32_clamp": 294912, "uint8_store": 294912} |
| CPU_reorder_and_regroup_alias | 0 | 0 | {} |
| fused_mean_std_cache_initialization | 24 | 48 | {"fp64_python_reciprocal": 2, "fp32_multiply": 6} |
| uint8_to_FP32 | 294912 | 1179648 | {"uint8_to_fp32_cast": 294912} |
| normalize_subtract | 2359296 | 1179648 | {"fp32_subtract": 294912} |
| normalize_divide_in_place | 2359296 | 1179648 | {"fp32_divide": 294912} |
| patch_reshape_permute_expand_alias | 0 | 0 | {} |
| patch_flatten_materialization | 2359296 | 2359296 | {"fp32_element_copy": 589824} |
| grid_thw_tensor | 0 | 24 | {"int64_constant_store": 3} |
| vision_entry_FP32_to_BF16 | 2359296 | 1179648 | {"fp32_to_bf16_cast": 589824} |

resize_axes保存实际边界tap与INT16系数、精度bits和系数/索引buffer分配；这些整数MAC不计FP32 FLOPs。FP32归一化、时间展开物化及视觉入口cast独立列出。总语义流量已含系数内部访问，子字段不能再加一次。JPEG/PNG decode、CPU调度、设备传输与实际延迟/运行峰值均未计。

重放：`python freeze.py`；计量测试：`python -m unittest discover -s . -p test_vision_preprocess.py -v`；独立数值：`python numeric_check.py`。

硬件旧文案修订候选为hardware-prose.patch.json，三个guarded old/new替换仅status/pending/Active注释，不改任何数值，未应用共享配置。
