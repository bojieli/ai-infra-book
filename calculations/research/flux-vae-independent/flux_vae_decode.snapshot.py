"""FLUX2 Klein VAE decoder operators and source-level tensor lifetimes.

No DiT work, encoder, or image encoding. Opaque kernel workspace stays unknown.
"""

import hashlib
import json
from math import prod
from pathlib import Path

from infra_calc.paths import PROJECT
from infra_calc.sources import read_source, records
from infra_calc.units import positive_int

MODEL = "flux2-klein-4b"
SOURCE_NAMES = {
    "autoencoder_kl_flux2.py",
    "vae.py",
    "unet_2d_blocks.py",
    "resnet.py",
    "upsampling.py",
    "attention_processor.py",
}


def evidence():
    rows = [
        r
        for r in json.loads(
            (PROJECT / "configs/image-generation.lock.json").read_text()
        )
        if Path(r["file"]).name in SOURCE_NAMES
    ]
    if len(rows) != len(SOURCE_NAMES):
        raise ValueError("Missing fixed decoder implementation")
    for row in rows:
        data = (PROJECT / row["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Decoder source hash mismatch")
    return rows


def calculate(
    height=1024,
    width=1024,
    batch=1,
    dtype="bf16",
    attention="sdpa",
    workspace_bytes=None,
):
    """Decode already unpatchified/BN-denormalized [B,32,H/8,W/8] latent."""
    for name, value in [("height", height), ("width", width), ("batch", batch)]:
        positive_int(value, name)
    if height % 8 or width % 8:
        raise ValueError("Decoder RGB dimensions must be multiples of eight")
    if dtype not in ("bf16", "fp32") or attention not in ("sdpa", "eager"):
        raise ValueError("Explicit BF16/FP32 and SDPA/eager processor required")
    if workspace_bytes is not None:
        positive_int(workspace_bytes, "workspace_bytes", allow_zero=True)
    # Fixed Upsample2D calls contiguous() for these shapes. Its copy depends
    # on strides, which this declared tensor-boundary graph does not model.
    upsample_elements = [
        batch * channels * (height // divisor) * (width // divisor)
        for channels, divisor in [(512, 8), (512, 4), (256, 2)]
    ]
    contiguous_branches = [
        dict(
            stage=index,
            input_elements=elements,
            input_bytes=elements * (2 if dtype == "bf16" else 4),
            triggered=batch >= 64 or elements * 2 > 2**31,
            materialized_copy_bytes=None if batch >= 64 or elements * 2 > 2**31 else 0,
        )
        for index, elements in enumerate(upsample_elements)
    ]
    layout_copy_unknown = any(row["triggered"] for row in contiguous_branches)
    rows = evidence()
    config_path = f"configs/models/{MODEL}/vae/config.json"
    config = json.loads(read_source(config_path))
    rows += [r for r in records() if r["file"] == config_path]
    expected = dict(
        block_out_channels=[128, 256, 512, 512],
        layers_per_block=2,
        latent_channels=32,
        norm_num_groups=32,
        mid_block_add_attention=True,
        use_post_quant_conv=True,
        act_fn="silu",
        out_channels=3,
    )
    if any(config[k] != value for k, value in expected.items()):
        raise ValueError("Decoder config changed from audited four-stage path")
    element_bytes = 2 if dtype == "bf16" else 4
    tensors, operators, weights, holds = {}, [], [], []

    def tensor(name, shape, producer=-1, byte_width=None):
        if name in tensors:
            raise ValueError("Duplicate tensor identity")
        tensors[name] = dict(
            shape=list(shape),
            bytes=prod(shape) * (byte_width or element_bytes),
            producer=producer,
            consumers=[],
            held_until=producer,
        )
        return name

    def op(
        name,
        kind,
        inputs,
        shape,
        matrix=0,
        scalar=0,
        special=None,
        weight_shape=None,
        bias=False,
        byte_width=None,
        notes="",
    ):
        position = len(operators)
        output = tensor(name, shape, position, byte_width)
        for x in inputs:
            tensors[x]["consumers"].append(position)
        weight_bytes = 0
        if weight_shape:
            dims = list(weight_shape)
            weights.append(
                dict(
                    name=name + ".weight",
                    shape=dims,
                    parameters=prod(dims),
                    bytes=prod(dims) * element_bytes,
                )
            )
            weight_bytes += prod(dims) * element_bytes
            if bias:
                channels = dims[0]
                weights.append(
                    dict(
                        name=name + ".bias",
                        shape=[channels],
                        parameters=channels,
                        bytes=channels * element_bytes,
                    )
                )
                weight_bytes += channels * element_bytes
        operators.append(
            dict(
                id=position,
                name=name,
                kind=kind,
                inputs=inputs,
                output=output,
                matrix_flops=matrix,
                scalar_flops=scalar,
                special_ops=special or {},
                input_bytes=sum(tensors[x]["bytes"] for x in inputs),
                output_bytes=tensors[output]["bytes"],
                weight_bytes=weight_bytes,
                notes=notes,
            )
        )
        return output

    def hold_until(x, position, owner):
        tensors[x]["held_until"] = max(tensors[x]["held_until"], position)
        holds.append(dict(tensor=x, until_operator=position, owner=owner))

    def conv(name, x, out_channels, kernel=3):
        b, ci, h, w = tensors[x]["shape"]
        result = op(
            name,
            "conv2d",
            [x],
            [b, out_channels, h, w],
            matrix=2 * b * h * w * ci * out_channels * kernel * kernel,
            scalar=b * out_channels * h * w,
            weight_shape=[out_channels, ci, kernel, kernel],
            bias=True,
            notes="Dense same-padding slots, FMA=2; bias additions separate.",
        )
        valid = (h if kernel == 1 else 3 * h - 2) * (w if kernel == 1 else 3 * w - 2)
        operators[-1]["nonpadding_matrix_flops"] = 2 * b * valid * ci * out_channels
        return result

    def norm(name, x):
        b, c, h, w = tensors[x]["shape"]
        elements = b * c * h * w
        vectors = b * 32
        group_width = c * h * w // 32
        # Two-pass mathematical GroupNorm, biased variance: mean, subtract,
        # square/variance, epsilon/rsqrt, normalize, affine multiply/add.
        result = op(
            name,
            "groupnorm",
            [x],
            [b, c, h, w],
            scalar=7 * elements + vectors,
            special={"rsqrt": vectors},
            weight_shape=[c],
            bias=True,
            notes="Biased-variance two-pass mathematical algorithm, 32 groups; kernel reduction algorithm/workspace unspecified.",
        )
        operators[-1]["normalization_vectors"] = vectors
        operators[-1]["normalization_width"] = group_width
        return result

    def silu(name, x):
        sh = tensors[x]["shape"]
        n = prod(sh)
        return op(name, "silu", [x], sh, scalar=n, special={"sigmoid": n})

    def residual(name, x, channels):
        root = x
        y = norm(name + ".norm1", x)
        y = silu(name + ".silu1", y)
        y = conv(name + ".conv1", y, channels)
        y = norm(name + ".norm2", y)
        y = silu(name + ".silu2", y)
        # Dropout p=0, eval: no new tensor/data work.
        y = conv(name + ".conv2", y, channels)
        skip = (
            conv(name + ".shortcut", x, channels, 1)
            if tensors[x]["shape"][1] != channels
            else x
        )
        main_branch = y
        y = op(
            name + ".add",
            "residual_add",
            [skip, y],
            tensors[y]["shape"],
            scalar=prod(tensors[y]["shape"]),
        )
        y = op(
            name + ".divide_by_one",
            "residual_rescale",
            [y],
            tensors[y]["shape"],
            scalar=prod(tensors[y]["shape"]),
            notes="Pinned source divides by output_scale_factor=1; retained as source operation.",
        )
        hold_until(main_branch, len(operators) - 1, name + " hidden_states local")
        hold_until(skip, len(operators) - 1, name + " input_tensor shortcut local")
        hold_until(root, len(operators) - 1, name + " Python input_tensor argument")
        return y

    def mid_attention(x):
        root = x
        b, c, h, w = tensors[x]["shape"]
        n = h * w
        normalized = norm("mid.attention.norm", x)

        def project(label, z):
            return op(
                "mid.attention." + label,
                "linear_1x1",
                [z],
                [b, c, h, w],
                matrix=2 * b * n * c * c,
                scalar=b * n * c,
                weight_shape=[c, c],
                bias=True,
            )

        q = project("q", normalized)
        k = project("k", normalized)
        v = project("v", normalized)
        if attention == "sdpa":
            y = op(
                "mid.attention.sdpa",
                "sdpa",
                [q, k, v],
                [b, c, h, w],
                matrix=4 * b * n * n * c,
                scalar=4 * b * n * n - b * n,
                special={"exp": b * n * n, "max_comparisons": b * n * (n - 1)},
                notes="Single head, noncausal, dropout0. Mathematical QK/softmax/PV work; no score tensor allocation inferred from opaque SDPA.",
            )
        else:
            score = op(
                "mid.attention.qk",
                "attention_qk",
                [q, k],
                [b, n, n],
                matrix=2 * b * n * n * c,
                scalar=b * n * n,
                notes="baddbmm alpha scaling included; beta0 scratch handled as explicit transient below.",
            )
            scratch = tensor(
                "mid.attention.beta0_scratch", [b, n, n], len(operators) - 1
            )
            score32 = (
                op(
                    "mid.attention.upcast",
                    "cast",
                    [score],
                    [b, n, n],
                    byte_width=4,
                    notes="upcast_softmax=True; BF16 score converted to FP32.",
                )
                if dtype == "bf16"
                else score
            )
            prob32 = op(
                "mid.attention.softmax",
                "softmax",
                [score32],
                [b, n, n],
                scalar=3 * b * n * n - b * n,
                special={"exp": b * n * n, "max_comparisons": b * n * (n - 1)},
                byte_width=4,
            )
            prob = (
                op("mid.attention.probability_cast", "cast", [prob32], [b, n, n])
                if dtype == "bf16"
                else prob32
            )
            tensors[scratch][
                "release_reason"
            ] = "Explicit del baddbmm_input immediately after QK baddbmm, before upcast/softmax"
            y = op(
                "mid.attention.pv",
                "attention_pv",
                [prob, v],
                [b, c, h, w],
                matrix=2 * b * n * n * c,
            )
            # Attention.get_attention_scores returns probability but query/key/value
            # remain Python locals until processor exits; keep root and projected tensors.
        y = project("out", y)
        y = op(
            "mid.attention.add",
            "residual_add",
            [y, root],
            [b, c, h, w],
            scalar=b * c * h * w,
        )
        y = op(
            "mid.attention.divide_by_one",
            "residual_rescale",
            [y],
            [b, c, h, w],
            scalar=b * c * h * w,
        )
        if attention == "eager":
            hold_until(prob, len(operators) - 1, "attention_probs processor local")
        for identity in [root, normalized, q, k, v]:
            hold_until(identity, len(operators) - 1, "attention processor local")
        return y

    latent = tensor("latent", [batch, 32, height // 8, width // 8])
    post = conv("post_quant", latent, 32, 1)
    current = conv("decoder.input", post, 512)
    mid_input = current
    current = residual("mid.residual0", current, 512)
    current = mid_attention(current)
    current = residual("mid.residual1", current, 512)
    hold_until(
        mid_input, len(operators) - 1, "Decoder.forward sample during mid_block call"
    )
    for level, channels in enumerate([512, 512, 256, 128]):
        block_input = current
        for block in range(3):
            current = residual(f"up{level}.residual{block}", current, channels)
        if level < 3:
            b, c, h, w = tensors[current]["shape"]
            upsample_input = current
            current = op(
                f"up{level}.nearest",
                "nearest2d",
                [current],
                [b, c, 2 * h, 2 * w],
                notes="Nearest duplication, PyTorch>=2.1 BF16-capable branch; no floating interpolation arithmetic.",
            )
            current = conv(f"up{level}.spatial_conv", current, c)
            hold_until(
                upsample_input,
                len(operators) - 1,
                "Upsample2D caller input through conv return",
            )
        hold_until(
            block_input,
            len(operators) - 1,
            "Decoder.forward sample during up_block call",
        )
    current = norm("decoder.output_norm", current)
    current = silu("decoder.output_silu", current)
    current = conv("decoder.output", current, 3)
    hold_until(latent, len(operators), "decode caller keeps latent argument")
    hold_until(post, len(operators), "_decode z held while Decoder.forward executes")
    hold_until(current, len(operators), "returned decoded RGB tensor")
    if tensors[current]["shape"] != [batch, 3, height, width]:
        raise ValueError("Output geometry mismatch")

    # Boundary allocation graph: newly produced outputs coexist with inputs during
    # an operation; after completion release only at source last-use/frame return.
    for row in tensors.values():
        row["last_use"] = max(row["consumers"] + [row["held_until"], row["producer"]])
    events = []
    live = {latent: tensors[latent]["bytes"]}
    peak = sum(live.values())
    peak_at = "input"
    for step in operators:
        i = step["id"]
        name = step["output"]
        for extra_name, extra in tensors.items():
            if extra["producer"] == i and extra_name != name:
                live[extra_name] = extra["bytes"]
        live[name] = tensors[name]["bytes"]
        now = sum(live.values())
        if now > peak:
            peak = now
            peak_at = step["name"]
        events.append(
            dict(
                operator=i,
                phase="output_allocate_before_release",
                live_bytes=now,
                live_tensors=list(live),
                temporary_beta0_bytes=live.get("mid.attention.beta0_scratch", 0),
            )
        )
        for key in list(live):
            if tensors[key]["last_use"] <= i:
                del live[key]
    # On returning from _decode, its post-quant z reference is released.
    # The external caller retains its input latent and returned RGB.
    live = {name: tensors[name]["bytes"] for name in (latent, current)}
    events.append(
        dict(
            operator=len(operators),
            phase="decoder_return",
            live_bytes=sum(live.values()),
            live_tensors=list(live),
            temporary_beta0_bytes=0,
        )
    )
    result = dict(
        schema_version=1,
        calculation="flux2-vae-decoder-dag",
        model=MODEL,
        scenario=dict(
            height=height,
            width=width,
            batch=batch,
            dtype=dtype,
            attention=attention,
            workspace_bytes=workspace_bytes,
        ),
        sources=rows,
        config_source=config_path,
        latent_shape=[batch, 32, height // 8, width // 8],
        output_shape=tensors[current]["shape"],
        weights=weights,
        operators=operators,
        tensors=tensors,
        frame_holds=holds,
        lifetime_events=events,
        summary=dict(
            decoder_weight_parameters=sum(x["parameters"] for x in weights),
            decoder_weight_bytes=sum(x["bytes"] for x in weights),
            dense_matrix_and_conv_flops=sum(x["matrix_flops"] for x in operators),
            nonpadding_matrix_and_conv_flops=sum(
                x.get("nonpadding_matrix_flops", x["matrix_flops"]) for x in operators
            ),
            scalar_flops=sum(x["scalar_flops"] for x in operators),
            operator_boundary_read_bytes=sum(x["input_bytes"] for x in operators),
            operator_boundary_write_bytes=sum(x["output_bytes"] for x in operators),
            declared_tensor_boundary_peak_bytes=peak,
            peak_operator=peak_at,
            supplied_workspace_bytes=workspace_bytes,
            conditional_weights_boundary_workspace_bytes=(
                None
                if workspace_bytes is None or layout_copy_unknown
                else peak + sum(x["bytes"] for x in weights) + workspace_bytes
            ),
            upsample_contiguous_interfaces=contiguous_branches,
            layout_copy_bytes_unknown=layout_copy_unknown,
            actual_runtime_peak_bytes=None,
            persistent_decode_cache_bytes=0,
            caller_retained_input_and_output_bytes=sum(live.values()),
        ),
        scope=[
            "Already denormalized/unpatchified VAE latent only: no DiT, BN inversion, latent unpacking, encoder, tokenizer, image postprocess or image file bytes.",
            "All decoder Conv2d/Linear/GN-affine weights enumerated, not entire AutoencoderKLFlux2 weights; no checkpoint-header parameter verification claimed.",
            "No slicing, tiling, checkpointing, training or offload. Dtype explicit; force_upcast config alone does not execute an FP32 conversion.",
            "PyTorch >=2.1 nearest BF16 path. Upsample contiguous branches expose input sizes and unknown materialized copy bytes when triggered; named-boundary peak excludes these copies and conditional budget is unavailable until layout is specified.",
            "Residual division by1 is retained. Default SDPA is noncausal one head; primitive algorithm and workspace unknown. Eager branch materializes scores for comparison.",
            "Boundary lifetime graph includes named tensor outputs and explicit caller/local holds; kernel-internal temporaries, allocator reuse/alignment and autograd are not inferred. Conditional budget is only with caller-supplied workspace, never measured peak.",
            "GroupNorm two-pass math is counted with affine and biased variance; reduction kernel algorithm unspecified. SiLU/softmax special operations are separate from matrix FLOPs.",
        ],
    )
    return result
