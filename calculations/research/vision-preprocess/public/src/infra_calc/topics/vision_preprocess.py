"""Single RGB image, pinned CPU generic uint8 bicubic-AA and Qwen patch layout."""

import hashlib
import json
import math
from pathlib import Path

from ..paths import PROJECT


def smart_resize(height, width, factor=32, min_pixels=65536, max_pixels=16777216):
    if max(height, width) / min(height, width) > 200:
        raise ValueError("Official aspect-ratio limit exceeded")
    h, w = round(height / factor) * factor, round(width / factor) * factor
    if h * w > max_pixels:
        beta = math.sqrt(height * width / max_pixels)
        h, w = max(factor, math.floor(height / beta / factor) * factor), max(
            factor, math.floor(width / beta / factor) * factor
        )
    elif h * w < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h, w = (
            math.ceil(height * beta / factor) * factor,
            math.ceil(width * beta / factor) * factor,
        )
    return h, w


def axis_weights(input_size, output_size):
    """Translate the locked C++ generic AA coefficient setup, including zero taps."""
    scale = input_size / output_size
    support = 2 * max(scale, 1)
    maximum = math.ceil(support) * 2 + 1
    ranges = []
    maximum_weight = 0.0
    branches = [0, 0, 0]
    for i in range(output_size):
        center = scale * (i + 0.5)
        xmin = max(int(center - support + 0.5), 0)
        count = min(
            max(min(int(center + support + 0.5), input_size) - xmin, 0), maximum
        )
        values = []
        for j in range(count):
            x = abs((j + xmin - center + 0.5) * (1 / scale if scale >= 1 else 1))
            if x < 1:
                value = (1.5 * x - 2.5) * x * x + 1
                branches[0] += 1
            elif x < 2:
                value = ((-0.5 * x + 2.5) * x - 4) * x + 2
                branches[1] += 1
            else:
                value = 0.0
                branches[2] += 1
            values.append(value)
        total = sum(values)
        values = [v / total for v in values] if total else values
        maximum_weight = max(maximum_weight, max(values, default=0))
        ranges.append(
            dict(start=xmin, count=count, weights=values + [0.0] * (maximum - count))
        )
    precision = 0
    while precision < 22:
        if int(0.5 + maximum_weight * (1 << (precision + 1))) >= (1 << 15):
            break
        precision += 1
    for row in ranges:
        row["int16_weights"] = [
            int(v * (1 << precision) + (-0.5 if v < 0 else 0.5))
            for v in row.pop("weights")
        ]
    return dict(
        input_size=input_size,
        output_size=output_size,
        max_taps=maximum,
        weights_precision_bits=precision,
        ranges=ranges,
        tap_count=sum(r["count"] for r in ranges),
        cubic_branch_counts=dict(
            inside_one=branches[0], between_one_two=branches[1], outside_two=branches[2]
        ),
        coefficient_buffer_allocated_bytes=output_size * maximum * 8,
        index_arrays_allocated_bytes=output_size * 4 * 8,
    )


def calculate(height=640, width=640, encoder_dtype="bf16", normalization_cache="cold"):
    for name, value in [("height", height), ("width", width)]:
        if type(value) is not int or value <= 0:
            raise ValueError(name + " must be positive integer")
    if encoder_dtype not in ("bf16", "fp32"):
        raise ValueError("encoder_dtype must be bf16 or fp32")
    if normalization_cache not in ("cold", "warm"):
        raise ValueError("cache must be cold or warm")
    HERE = PROJECT / "sources/vision-preprocess"
    lock = json.loads((PROJECT / "configs/vision-preprocess.lock.json").read_text())
    for source in lock:
        raw = (PROJECT / source["file"]).read_bytes()
        if (
            len(raw) != source["bytes"]
            or hashlib.sha256(raw).hexdigest() != source["sha256"]
        ):
            raise ValueError("Source mismatch")
    config = json.loads((HERE / "preprocessor_config.json").read_text())
    p, t, m = config["patch_size"], config["temporal_patch_size"], config["merge_size"]
    h, w = smart_resize(
        height,
        width,
        p * m,
        config["size"]["shortest_edge"],
        config["size"]["longest_edge"],
    )
    x, y = 3 * height * width, 3 * h * w
    stages = []

    def add(name, reads, writes, operations=None, **extra):
        stages.append(
            dict(
                stage=name,
                execution_count=1,
                semantic_read_bytes=reads,
                semantic_write_bytes=writes,
                operations=operations or {},
                **extra,
            )
        )

    rounded_area = round(height / (p * m)) * (p * m) * round(width / (p * m)) * (p * m)
    branch = (
        "shrink_max_area"
        if rounded_area > config["size"]["longest_edge"]
        else (
            "enlarge_min_area"
            if rounded_area < config["size"]["shortest_edge"]
            else "round_to_factor"
        )
    )
    add(
        "smart_resize_geometry",
        0,
        0,
        dict(python_round=2, python_sqrt=0 if branch == "round_to_factor" else 1),
        branch=branch,
        output_height=h,
        output_width=w,
        scope="Named geometry special operations; integer shape/control arithmetic is not a machine-instruction claim",
    )
    add("numpy_to_torch_alias", 0, 0, output_dtype="uint8", materialized=False)
    add("HWC_to_CHW_contiguous", x, x, {"element_copy": x}, materialized=True)
    add("CPU_group_unsqueeze_before_resize", 0, 0, materialized=False)
    resize_axes = []
    for label, old, new, multiplicity in [
        ("width", width, w, 3 * height),
        ("height", height, h, 3 * w),
    ]:
        if old == new:
            continue
        axis = axis_weights(old, new)
        resize_axes.append(dict(axis=label, **axis))
        count = axis["tap_count"]
        slots = new * axis["max_taps"]
        branch = axis["cubic_branch_counts"]
        # Source-level arithmetic: constants in cubic polynomials folded; address/index/control overhead separate.
        setup = dict(
            fp64_axis_scale_divide=1,
            fp64_support_multiply=1,
            fp64_axis_support_ceil=1,
            fp64_per_coordinate_inverse_scale_divide=new if old >= new else 0,
            fp64_range_add_sub=4 * new,
            fp64_range_to_int64=2 * new,
            fp64_weight_max_compare=count + new,
            fp64_precision_scale_multiply=min(axis["weights_precision_bits"] + 1, 22),
            fp64_precision_round_add=min(axis["weights_precision_bits"] + 1, 22),
            fp64_quantize_sign_compare=slots,
            int64_index_array_store=4 * new,
            fp64_center_multiply=new,
            fp64_center_add=new,
            fp64_filter_argument_subtract=count,
            fp64_filter_argument_add=count,
            fp64_filter_argument_multiply=count,
            fp64_abs=count,
            fp64_cubic_multiply=3 * (branch["inside_one"] + branch["between_one_two"]),
            fp64_cubic_add_sub=2 * branch["inside_one"] + 3 * branch["between_one_two"],
            fp64_weight_sum_add=count,
            fp64_weight_normalize_divide=count,
            fp64_quantize_multiply=slots,
            fp64_quantize_add=slots,
            float_to_integer_cast=slots,
        )
        add(
            label + "_coefficient_setup",
            count * 8 * 2 + slots * 8,
            axis["index_arrays_allocated_bytes"] + slots * 8 + count * 8 + slots * 2,
            setup,
            coefficient_dtype="FP64 then INT16 packed into same FP64 allocation",
            allocated_buffer_bytes=axis["coefficient_buffer_allocated_bytes"]
            + axis["index_arrays_allocated_bytes"],
            logical_buffer_traffic_status="semantic totals include coefficient initialization, normalization and in-place INT16 repack; subfields explain included accesses",
            coefficient_internal_reads_bytes=count * 8 * 2 + slots * 8,
            coefficient_internal_rewrites_bytes=count * 8,
        )
        outputs = multiplicity * new
        mac = multiplicity * count
        add(
            label + "_uint8_separable_convolution",
            mac * 3,
            outputs,
            dict(
                int32_multiply=mac,
                int32_add=mac,
                int32_rounding_bias_init=outputs,
                int32_right_shift=outputs,
                int32_clamp=outputs,
                uint8_store=outputs,
            ),
            input_pixel_reads_bytes=mac,
            int16_weight_reads_bytes=mac * 2,
            input_dtype="uint8",
            weight_dtype="int16",
            accumulator_dtype="int32",
            output_dtype="uint8",
            intermediate_axis_order="width then height; each pass rounds and clamps",
            index_metadata_allocated_bytes=axis["index_arrays_allocated_bytes"],
            metadata_load_count_status="TensorIterator chunking-dependent; no guessed per-output HBM loads",
        )
    if not resize_axes:
        add("resize_identity_alias", 0, 0, materialized=False)
    add("CPU_reorder_and_regroup_alias", 0, 0, materialized=False)
    if normalization_cache == "cold":
        add(
            "fused_mean_std_cache_initialization",
            24,
            48,
            dict(fp64_python_reciprocal=2, fp32_multiply=6),
            retained_cache_bytes=24,
            constant="mean/std 0.5 * 255 = 127.5; factory writes included",
        )
    add("uint8_to_FP32", y, 4 * y, dict(uint8_to_fp32_cast=y), materialized=True)
    add(
        "normalize_subtract",
        8 * y,
        4 * y,
        dict(fp32_subtract=y),
        materialized=True,
        broadcast_parameter_unique_bytes=12,
    )
    add(
        "normalize_divide_in_place",
        8 * y,
        4 * y,
        dict(fp32_divide=y),
        materialized=False,
        broadcast_parameter_unique_bytes=12,
    )
    add(
        "patch_reshape_permute_expand_alias",
        0,
        0,
        materialized=False,
        temporal_repeat=t,
        spatial_patch=p,
        spatial_merge=m,
    )
    add(
        "patch_flatten_materialization",
        4 * y * t,
        4 * y * t,
        dict(fp32_element_copy=y * t),
        unique_input_bytes=4 * y,
        materialized=True,
    )
    add(
        "grid_thw_tensor",
        0,
        24,
        dict(int64_constant_store=3),
        output=[1, h // p, w // p],
    )
    if encoder_dtype == "bf16":
        add(
            "vision_entry_FP32_to_BF16",
            4 * y * t,
            2 * y * t,
            dict(fp32_to_bf16_cast=y * t),
            ownership="boundary cast before already-accounted patch projection; count exactly once",
        )
    else:
        add("vision_entry_FP32_alias", 0, 0, materialized=False)
    for stage in stages:
        name = stage["stage"]
        if "coefficient_setup" in name or "separable_convolution" in name:
            stage["source_refs"] = [
                dict(
                    file="UpSampleKernel.cpp",
                    locator="HelperInterpBase::_compute_index_ranges_int16_weights; basic_loop_aa_horizontal/vertical<uint8_t>; separable_upsample_generic_Nd_kernel_impl",
                )
            ]
        elif (
            name.startswith("normalize")
            or name.startswith("uint8_to")
            or name.startswith("fused_mean")
        ):
            stage["source_refs"] = [
                dict(
                    file="image_processing_backends.py",
                    locator="TorchvisionBackend.rescale_and_normalize/_fuse_mean_std_and_rescale_factor",
                ),
                dict(file="_misc.py", locator="normalize_image"),
            ]
        elif name.startswith("vision_entry"):
            stage["source_refs"] = [
                dict(
                    file="modeling_qwen3_vl.py",
                    locator="get_image_features: pixel_values.type(self.visual.dtype); patch projection dtype conversion",
                )
            ]
        elif name.startswith("HWC") or name.startswith("numpy"):
            stage["source_refs"] = [
                dict(file="image_processing_backends.py", locator="_process_image")
            ]
        else:
            stage["source_refs"] = [
                dict(
                    file="image_processing_qwen2_vl.py",
                    locator="smart_resize; patchify; _preprocess",
                ),
                dict(
                    file="image_transforms.py",
                    locator="group_images_by_shape; reorder_images",
                ),
            ]
    for stage in stages:
        for ref in stage["source_refs"]:
            ref["file"] = "sources/vision-preprocess/" + ref["file"]
    return dict(
        calculation="vision-preprocess",
        scenario=dict(
            height=height,
            width=width,
            encoder_dtype=encoder_dtype,
            normalization_cache=normalization_cache,
        ),
        sources=lock,
        stages=stages,
        resize_axes=resize_axes,
        summary=dict(
            resized_height=h,
            resized_width=w,
            image_grid_thw=[1, h // p, w // p],
            pixel_values_shape=[(h // p) * (w // p), 3 * t * p * p],
            pixel_values_dtype="fp32",
            pixel_values_bytes=4 * y * t,
            encoder_input_bytes=(2 if encoder_dtype == "bf16" else 4) * y * t,
            preprocessing_matrix_flops=0,
            semantic_read_bytes=sum(z["semantic_read_bytes"] for z in stages),
            semantic_write_bytes=sum(z["semantic_write_bytes"] for z in stages),
            actual_runtime_peak_bytes=None,
            actual_latency_seconds=None,
        ),
        scope=[
            "One contiguous HWC RGB uint8 NumPy image, CPU, disable_grouping=True; JPEG/PNG decode, ICC/color conversion, device transfer and scheduling excluded.",
            "Fixed Transformers official selected methods plus torchvision0.22/PyTorch2.7 CPU generic non-AVX bicubic antialias path. No AVX/CUDA/PIL equivalence asserted.",
            "Resize coefficients use FP64, quantized INT16 weights and INT32 accumulation, with per-axis shift/clamp; do not label integer convolution as FP32 FLOPs.",
            "Known per-element and polynomial arithmetic counted; loop/index/allocator/TensorIterator metadata and sqrt implementation are not an exhaustive machine-instruction budget.",
            "Semantic operand bytes include repeated broadcasts/taps; not measured external-memory traffic. Coefficient internal reads/rewrites subfields are included, not additional to stage totals.",
            "Vision embedding, Transformer and language work reused downstream, not included here. The optional BF16 entry cast belongs once at the preprocessing/encoder boundary.",
        ],
    )


def markdown(result):
    s = result["summary"]
    scenario = result["scenario"]
    lines = [
        "# RGB预处理到视觉入口",
        "",
        f"已解码单张 {scenario['height']}×{scenario['width']} HWC RGB uint8 → {s['resized_height']}×{s['resized_width']}；grid={s['image_grid_thw']}，FP32 pixel_values={s['pixel_values_shape']}。",
        "",
        f"处理器输出 {s['pixel_values_bytes']} B；{scenario['encoder_dtype']} 视觉入口 {s['encoder_input_bytes']} B。语义读/写 {s['semantic_read_bytes']} / {s['semantic_write_bytes']} B；矩阵FLOPs={s['preprocessing_matrix_flops']}。整数resize、FP32标量与转换各按原类别列示。",
        "",
        "| 阶段 | 次数 | 语义读B | 语义写B | 实际列出的操作 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["stages"]:
        lines.append(
            f"| {row['stage']} | {row['execution_count']} | {row['semantic_read_bytes']} | {row['semantic_write_bytes']} | {json.dumps(row['operations'],ensure_ascii=False)} |"
        )
    lines += [
        "",
        "## Resize精度与系数状态",
        "",
        "固定Keys bicubic a=−0.5，antialias=True，align_corners=False，CPU generic non-AVX路径。FP64系数归一化后量化为INT16，复用FP64系数缓冲；uint8像素×INT16权重在INT32中累加。每轴分别shift、clamp成uint8，先水平后垂直。不能套用FP32矩阵峰值。",
        "",
        "| 轴 | 输入→输出 | 最大tap槽 | 实际tap总数 | 系数量化bits | 系数分配B | 索引分配B |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for axis in result["resize_axes"]:
        lines.append(
            f"| {axis['axis']} | {axis['input_size']}→{axis['output_size']} | {axis['max_taps']} | {axis['tap_count']} | {axis['weights_precision_bits']} | {axis['coefficient_buffer_allocated_bytes']} | {axis['index_arrays_allocated_bytes']} |"
        )
    if not result["resize_axes"]:
        lines.append("| identity | 尺寸相同，返回alias | 0 | 0 | — | 0 | 0 |")
    lines += ["", "## 独立状态与边界", ""]
    for row in result["stages"]:
        extras = {
            k: v
            for k, v in row.items()
            if k
            not in (
                "stage",
                "execution_count",
                "semantic_read_bytes",
                "semantic_write_bytes",
                "operations",
                "source_refs",
            )
        }
        if extras:
            lines += [f"- {row['stage']}: {json.dumps(extras,ensure_ascii=False)}"]
    lines += [""] + ["- " + x for x in result["scope"]]
    lines += [
        "",
        "CPU归一化为uint8→FP32，然后减127.5、除127.5。时间展开先alias、最终reshape物化；BF16入口转换不重复计入既有视觉矩阵。系数内部读写字段是阶段总量的子项，不另加。实际延迟与运行峰值保持null。",
        "",
        "## 官方来源与独立数值证明",
        "",
        "锁内numeric-verification.json记录5幅完整图片、4个强下采样/单轴kernel和5个几何边界检查。图像与patch值逐元素一致；最大面积缩小只作几何核验，不冒称完整大图运行。",
        "",
        "| 文件 | SHA256 | URL / 来源 |",
        "|---|---|---|",
    ]
    for source in result["sources"]:
        lines.append(
            f"| {source['file']} | {source['sha256']} | {source.get('url',source.get('origin','derived'))} |"
        )
    return "\n".join(lines) + "\n"
