# RGB预处理到视觉入口

已解码单张 257×385 HWC RGB uint8 → 256×384；grid=[1, 16, 24]，FP32 pixel_values=[384, 1536]。

处理器输出 2359296 B；bf16 视觉入口 1179648 B。语义读/写 17185865 / 8051499 B；矩阵FLOPs=0。整数resize、FP32标量与转换各按原类别列示。

| 阶段 | 次数 | 语义读B | 语义写B | 实际列出的操作 |
|---|---:|---:|---:|---|
| smart_resize_geometry | 1 | 0 | 0 | {"python_round": 2, "python_sqrt": 0} |
| numpy_to_torch_alias | 1 | 0 | 0 | {} |
| HWC_to_CHW_contiguous | 1 | 296835 | 296835 | {"element_copy": 296835} |
| CPU_group_unsqueeze_before_resize | 1 | 0 | 0 | {} |
| width_coefficient_setup | 1 | 46048 | 51440 | {"fp64_axis_scale_divide": 1, "fp64_support_multiply": 1, "fp64_axis_support_ceil": 1, "fp64_per_coordinate_inverse_scale_divide": 384, "fp64_range_add_sub": 1536, "fp64_range_to_int64": 768, "fp64_weight_max_compare": 1918, "fp64_precision_scale_multiply": 16, "fp64_precision_round_add": 16, "fp64_quantize_sign_compare": 2688, "int64_index_array_store": 1536, "fp64_center_multiply": 384, "fp64_center_add": 384, "fp64_filter_argument_subtract": 1534, "fp64_filter_argument_add": 1534, "fp64_filter_argument_multiply": 1534, "fp64_abs": 1534, "fp64_cubic_multiply": 4602, "fp64_cubic_add_sub": 3834, "fp64_weight_sum_add": 1534, "fp64_weight_normalize_divide": 1534, "fp64_quantize_multiply": 2688, "fp64_quantize_add": 2688, "float_to_integer_cast": 2688} |
| width_uint8_separable_convolution | 1 | 3548142 | 296064 | {"int32_multiply": 1182714, "int32_add": 1182714, "int32_rounding_bias_init": 296064, "int32_right_shift": 296064, "int32_clamp": 296064, "uint8_store": 296064} |
| height_coefficient_setup | 1 | 30688 | 34288 | {"fp64_axis_scale_divide": 1, "fp64_support_multiply": 1, "fp64_axis_support_ceil": 1, "fp64_per_coordinate_inverse_scale_divide": 256, "fp64_range_add_sub": 1024, "fp64_range_to_int64": 512, "fp64_weight_max_compare": 1278, "fp64_precision_scale_multiply": 16, "fp64_precision_round_add": 16, "fp64_quantize_sign_compare": 1792, "int64_index_array_store": 1024, "fp64_center_multiply": 256, "fp64_center_add": 256, "fp64_filter_argument_subtract": 1022, "fp64_filter_argument_add": 1022, "fp64_filter_argument_multiply": 1022, "fp64_abs": 1022, "fp64_cubic_multiply": 3066, "fp64_cubic_add_sub": 2554, "fp64_weight_sum_add": 1022, "fp64_weight_normalize_divide": 1022, "fp64_quantize_multiply": 1792, "fp64_quantize_add": 1792, "float_to_integer_cast": 1792} |
| height_uint8_separable_convolution | 1 | 3532032 | 294912 | {"int32_multiply": 1177344, "int32_add": 1177344, "int32_rounding_bias_init": 294912, "int32_right_shift": 294912, "int32_clamp": 294912, "uint8_store": 294912} |
| CPU_reorder_and_regroup_alias | 1 | 0 | 0 | {} |
| fused_mean_std_cache_initialization | 1 | 24 | 48 | {"fp64_python_reciprocal": 2, "fp32_multiply": 6} |
| uint8_to_FP32 | 1 | 294912 | 1179648 | {"uint8_to_fp32_cast": 294912} |
| normalize_subtract | 1 | 2359296 | 1179648 | {"fp32_subtract": 294912} |
| normalize_divide_in_place | 1 | 2359296 | 1179648 | {"fp32_divide": 294912} |
| patch_reshape_permute_expand_alias | 1 | 0 | 0 | {} |
| patch_flatten_materialization | 1 | 2359296 | 2359296 | {"fp32_element_copy": 589824} |
| grid_thw_tensor | 1 | 0 | 24 | {"int64_constant_store": 3} |
| vision_entry_FP32_to_BF16 | 1 | 2359296 | 1179648 | {"fp32_to_bf16_cast": 589824} |

## Resize精度与系数状态

固定Keys bicubic a=−0.5，antialias=True，align_corners=False，CPU generic non-AVX路径。FP64系数归一化后量化为INT16，复用FP64系数缓冲；uint8像素×INT16权重在INT32中累加。每轴分别shift、clamp成uint8，先水平后垂直。不能套用FP32矩阵峰值。

| 轴 | 输入→输出 | 最大tap槽 | 实际tap总数 | 系数量化bits | 系数分配B | 索引分配B |
|---|---|---:|---:|---:|---:|---:|
| width | 385→384 | 7 | 1534 | 15 | 21504 | 12288 |
| height | 257→256 | 7 | 1022 | 15 | 14336 | 8192 |

## 独立状态与边界

- smart_resize_geometry: {"branch": "round_to_factor", "output_height": 256, "output_width": 384, "scope": "Named geometry special operations; integer shape/control arithmetic is not a machine-instruction claim"}
- numpy_to_torch_alias: {"output_dtype": "uint8", "materialized": false}
- HWC_to_CHW_contiguous: {"materialized": true}
- CPU_group_unsqueeze_before_resize: {"materialized": false}
- width_coefficient_setup: {"coefficient_dtype": "FP64 then INT16 packed into same FP64 allocation", "allocated_buffer_bytes": 33792, "logical_buffer_traffic_status": "semantic totals include coefficient initialization, normalization and in-place INT16 repack; subfields explain included accesses", "coefficient_internal_reads_bytes": 46048, "coefficient_internal_rewrites_bytes": 12272}
- width_uint8_separable_convolution: {"input_pixel_reads_bytes": 1182714, "int16_weight_reads_bytes": 2365428, "input_dtype": "uint8", "weight_dtype": "int16", "accumulator_dtype": "int32", "output_dtype": "uint8", "intermediate_axis_order": "width then height; each pass rounds and clamps", "index_metadata_allocated_bytes": 12288, "metadata_load_count_status": "TensorIterator chunking-dependent; no guessed per-output HBM loads"}
- height_coefficient_setup: {"coefficient_dtype": "FP64 then INT16 packed into same FP64 allocation", "allocated_buffer_bytes": 22528, "logical_buffer_traffic_status": "semantic totals include coefficient initialization, normalization and in-place INT16 repack; subfields explain included accesses", "coefficient_internal_reads_bytes": 30688, "coefficient_internal_rewrites_bytes": 8176}
- height_uint8_separable_convolution: {"input_pixel_reads_bytes": 1177344, "int16_weight_reads_bytes": 2354688, "input_dtype": "uint8", "weight_dtype": "int16", "accumulator_dtype": "int32", "output_dtype": "uint8", "intermediate_axis_order": "width then height; each pass rounds and clamps", "index_metadata_allocated_bytes": 8192, "metadata_load_count_status": "TensorIterator chunking-dependent; no guessed per-output HBM loads"}
- CPU_reorder_and_regroup_alias: {"materialized": false}
- fused_mean_std_cache_initialization: {"retained_cache_bytes": 24, "constant": "mean/std 0.5 * 255 = 127.5; factory writes included"}
- uint8_to_FP32: {"materialized": true}
- normalize_subtract: {"materialized": true, "broadcast_parameter_unique_bytes": 12}
- normalize_divide_in_place: {"materialized": false, "broadcast_parameter_unique_bytes": 12}
- patch_reshape_permute_expand_alias: {"materialized": false, "temporal_repeat": 2, "spatial_patch": 16, "spatial_merge": 2}
- patch_flatten_materialization: {"unique_input_bytes": 1179648, "materialized": true}
- grid_thw_tensor: {"output": [1, 16, 24]}
- vision_entry_FP32_to_BF16: {"ownership": "boundary cast before already-accounted patch projection; count exactly once"}

- One contiguous HWC RGB uint8 NumPy image, CPU, disable_grouping=True; JPEG/PNG decode, ICC/color conversion, device transfer and scheduling excluded.
- Fixed Transformers official selected methods plus torchvision0.22/PyTorch2.7 CPU generic non-AVX bicubic antialias path. No AVX/CUDA/PIL equivalence asserted.
- Resize coefficients use FP64, quantized INT16 weights and INT32 accumulation, with per-axis shift/clamp; do not label integer convolution as FP32 FLOPs.
- Known per-element and polynomial arithmetic counted; loop/index/allocator/TensorIterator metadata and sqrt implementation are not an exhaustive machine-instruction budget.
- Semantic operand bytes include repeated broadcasts/taps; not measured external-memory traffic. Coefficient internal reads/rewrites subfields are included, not additional to stage totals.
- Vision embedding, Transformer and language work reused downstream, not included here. The optional BF16 entry cast belongs once at the preprocessing/encoder boundary.

CPU归一化为uint8→FP32，然后减127.5、除127.5。时间展开先alias、最终reshape物化；BF16入口转换不重复计入既有视觉矩阵。系数内部读写字段是阶段总量的子项，不另加。实际延迟与运行峰值保持null。

## 官方来源与独立数值证明

锁内numeric-verification.json记录5幅完整图片、4个强下采样/单轴kernel和5个几何边界检查。图像与patch值逐元素一致；最大面积缩小只作几何核验，不冒称完整大图运行。

| 文件 | SHA256 | URL / 来源 |
|---|---|---|
| sources/vision-preprocess/image_processing_qwen2_vl.py | 4e1da45f9e7e157ca08aa88243fcc1495ea6a333e40e0c5035ef17ef2747a97d | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen2_vl/image_processing_qwen2_vl.py |
| sources/vision-preprocess/image_processing_backends.py | 5f3176903638125ee01af36e8c74741a7bab19581f3c13349a775b093cb1bbb0 | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/image_processing_backends.py |
| sources/vision-preprocess/image_processing_utils.py | 3328a0e2b38e272e824cad64a50d3e84206dab13d31b96104afa6459e149f7c1 | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/image_processing_utils.py |
| sources/vision-preprocess/image_utils.py | 24e1b8f65481a87f2d294473b238fe7ac3a5dbdf8fe64c4efac72a3616c66437 | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/image_utils.py |
| sources/vision-preprocess/image_transforms.py | 260fd1b2d3b23811f6be81da20777105d522c0213030580e6cf717a34492ef3b | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/image_transforms.py |
| sources/vision-preprocess/_geometry.py | e502f821d415ef63e4257eb573803933858babad22853401ea0d4f13db4caa63 | https://raw.githubusercontent.com/pytorch/vision/v0.22.0/torchvision/transforms/v2/functional/_geometry.py |
| sources/vision-preprocess/_misc.py | 397bb8193085f62ff5973ed3eb680a704b3de1f6813bbc32626a543829e45046 | https://raw.githubusercontent.com/pytorch/vision/v0.22.0/torchvision/transforms/v2/functional/_misc.py |
| sources/vision-preprocess/UpSampleKernel.cpp | e3b7bf13fecd1af33e1c6d7dfb441d97590b71075194d040c5ad325814fdac1f | https://raw.githubusercontent.com/pytorch/pytorch/v2.7.0/aten/src/ATen/native/cpu/UpSampleKernel.cpp |
| sources/vision-preprocess/UpSample.h | c6f283a38087784662855b5fec5db9c80e72565cb4a61b545f505f75b966fdba | https://raw.githubusercontent.com/pytorch/pytorch/v2.7.0/aten/src/ATen/native/UpSample.h |
| sources/vision-preprocess/preprocessor_config.json | 27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516 | https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json |
| sources/vision-preprocess/modeling_qwen3_vl.py | b5aa46046548f75c4e7f77e7ccc6717a1a627bead388118844898cfbc94c8bc1 | https://raw.githubusercontent.com/huggingface/transformers/cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py |
| sources/vision-preprocess/numeric-verification.json | bbdd79f962a9123a851796856afb257ea298664cde3b98d04f113c918cba122f | Frozen selected-path independent numerical evidence/scope |
| sources/vision-preprocess/CONTRACT.md | f9fcf916b815db6789a22cd601aa8b71e35391e1e5802e97980a19d59aa6c4fb | Frozen selected-path independent numerical evidence/scope |
