"""Pinned PCM-to-mel operator interfaces, with an explicit alternative FFT reference."""

from infra_calc.paths import PROJECT
import hashlib, json, math

HERE = PROJECT / "sources/omni-audio-preprocess"


def evidence():
    rows = json.loads((HERE / "sources.lock.json").read_text())["sources"]
    for row in rows:
        data = (HERE / row["file"]).read_bytes()
        if (
            len(data) != row["bytes"]
            or hashlib.sha256(data).hexdigest() != row["sha256"]
        ):
            raise ValueError("Source mismatch")
    return rows


def reference_fft_work(n=400):
    """Explicit full-complex mixed-radix recursion; no trivial-twiddle elision."""
    if n == 1:
        return dict(real_multiplications=0, real_additions=0, complex_products=0)
    radix = next((r for r in (2, 5) if n % r == 0), None)
    if radix is None:
        raise ValueError("Reference accepts factors 2 and 5 only")
    child = reference_fft_work(n // radix)
    # Each of n output frequencies is a sum of radix complex products.
    products = n * radix
    return dict(
        real_multiplications=radix * child["real_multiplications"] + 4 * products,
        real_additions=radix * child["real_additions"]
        + 2 * products
        + 2 * n * (radix - 1),
        complex_products=radix * child["complex_products"] + products,
    )


def mel_filter_initialization():
    """Fixed Slaney setup array graph; library linspace/log/exp remain named primitives."""
    bins, mel, centers = 201, 128, 130
    max_mel = 15 + math.log(8) * (27 / math.log(6.4))
    logarithmic = sum(max_mel * i / (centers - 1) >= 15 for i in range(centers))
    size = bins * mel
    ops = [
        dict(
            id="hertz_endpoints",
            scalar_flops=9,
            special_ops={"log": 3, "compare": 2},
            note="Both endpoints evaluate logstep and linear branch; 8000Hz overwrites with logarithmic branch",
        ),
        dict(
            id="mel_linspace",
            scalar_flops=None,
            special_ops={"linspace_elements": centers},
            output_bytes=8 * centers,
        ),
        dict(
            id="mel_to_hertz",
            scalar_flops=1 + 2 * centers + 3 * logarithmic,
            special_ops={"log": 1, "exp": logarithmic, "compare": centers},
            output_bytes=8 * centers,
        ),
        dict(
            id="frequency_linspace",
            scalar_flops=None,
            special_ops={"linspace_elements": bins},
            output_bytes=8 * bins,
        ),
        dict(
            id="filter_diff", scalar_flops=centers - 1, output_bytes=8 * (centers - 1)
        ),
        dict(
            id="frequency_slopes",
            scalar_flops=bins * centers,
            output_bytes=8 * bins * centers,
        ),
        dict(
            id="down_slopes_negate_then_divide",
            scalar_flops=size,
            special_ops={"sign_change": size},
            temporary_output_bytes=16 * size,
        ),
        dict(id="up_slopes_divide", scalar_flops=size, output_bytes=8 * size),
        dict(
            id="triangle_min_then_zero_max",
            scalar_flops=0,
            special_ops={"compare": 2 * size},
            temporary_output_bytes=16 * size,
        ),
        dict(
            id="slaney_enorm_difference_divide",
            scalar_flops=2 * mel,
            temporary_output_bytes=16 * mel,
        ),
        dict(
            id="slaney_filter_scale",
            scalar_flops=size,
            output_bytes=8 * size,
            note="In-place filter bank scaling",
        ),
        dict(
            id="zero_filter_diagnostic",
            scalar_flops=0,
            special_ops={"compare": mel * (bins - 1) + mel, "boolean_or": mel - 1},
            temporary_output_bytes=8 * mel + mel + 1,
        ),
    ]
    return dict(
        shape=[bins, mel],
        dtype="float64",
        persistent_bytes=8 * size,
        logarithmic_centers=logarithmic,
        operations=ops,
        known_scalar_flops=sum(x["scalar_flops"] or 0 for x in ops),
        complete_arithmetic=None,
        scope="Extractor construction once; array intermediates shown, not summed as simultaneous peak. NumPy linspace internals and setup source operand traffic remain primitive boundaries; never counted as zero.",
    )


def calculate(sample_lengths=None, sampling_rate=16000, encoder_element_bytes=4):
    lengths = [16000] if sample_lengths is None else sample_lengths
    if (
        not isinstance(lengths, list)
        or not lengths
        or any(type(n) is not int or n <= 0 for n in lengths)
    ):
        raise ValueError("Positive sample lengths required")
    if type(sampling_rate) is not int or sampling_rate != 16000:
        raise ValueError("Fixed 16 kHz mono PCM; no resampling")
    if type(encoder_element_bytes) is not int or encoder_element_bytes not in (2, 4):
        raise ValueError("Declared FP32 or explicit BF16 bridge only")
    sources = evidence()
    config = json.loads((HERE / "sources/preprocessor_config.json").read_text())
    nfft, hop, filters = config["n_fft"], config["hop_length"], config["feature_size"]
    # Pinned constructor overwrites serialized n_samples/nb_max_frames from default chunk_length=30.
    limit = 30 * sampling_rate
    valid = [min(n, limit) for n in lengths]
    padded = max(valid)
    batch = len(valid)
    if padded <= nfft // 2:
        raise ValueError(
            "Pinned torch reflect padding requires padded waveform length > 200"
        )
    frames = padded // hop
    fft_frames = frames + 1
    freq = nfft // 2 + 1
    mel_lengths = [min((n + hop - 1) // hop, frames) for n in valid]
    if any(n == 0 for n in mel_lengths):
        raise ValueError("Empty mel sequence cannot enter encoder")
    selected = sum(mel_lengths)
    spectrum = batch * freq * frames
    out = batch * filters * frames
    stages = []

    def add(name, read=0, write=0, scalar=0, matrix=0, special=None, integer=0, **kw):
        source_file = "sources/feature_extraction_whisper.py"
        locator = "WhisperFeatureExtractor._torch_extract_fbank_features / __call__"
        if name in (
            "truncate_views",
            "right_pad_waveforms",
            "sample_mask_ones",
            "right_pad_sample_masks",
            "batch_numpy_stack",
        ):
            source_file = "sources/feature_extraction_sequence_utils.py"
            locator = "SequenceFeatureExtractor.pad / _truncate / _pad"
        elif name in (
            "reflect_pad_center",
            "stft_frame_as_strided",
            "window_multiply",
            "rfft_400",
        ):
            source_file = "sources/SpectralOps.cpp"
            locator = "stft: center padding, as_strided, window multiply, _fft_r2c"
        elif name == "hann_window_per_call":
            source_file = "sources/TensorFactories.cpp"
            locator = "hann_window -> hamming_window, periodic increment and narrow"
        elif name.startswith("model_"):
            source_file = "sources/modeling_qwen3_omni_moe.py"
            locator = "get_audio_features: mask sum, bool cast, advanced-index gather"
        elif name == "explicit_caller_bf16_bridge":
            source_file = None
            locator = "Explicit caller scenario; not an operation in get_audio_features"
        stages.append(
            dict(
                id=name,
                source_file=source_file,
                source_locator=locator,
                read_bytes=read,
                write_bytes=write,
                scalar_flops=scalar,
                matrix_flops=matrix,
                special_ops=special or {},
                integer_ops=integer,
                **kw
            )
        )

    add(
        "numpy_input_wrapper_copy",
        4 * sum(lengths),
        4 * sum(lengths),
        note="np.asarray([speech],dtype=float32).T creates one array per original mono input before truncation",
    )
    add(
        "truncate_views",
        note="Each length capped at effective constructor n_samples; view only",
        dropped_samples=[a - b for a, b in zip(lengths, valid)],
    )
    shorter = [n for n in valid if n < padded]
    add(
        "right_pad_waveforms",
        4 * sum(shorter),
        4 * padded * len(shorter),
        zero_fill_bytes=4 * sum(padded - n for n in shorter),
    )
    add("sample_mask_ones", write=4 * sum(valid), dtype="int32")
    add(
        "right_pad_sample_masks",
        4 * sum(shorter),
        4 * padded * len(shorter),
        zero_fill_bytes=4 * sum(padded - n for n in shorter),
    )
    add(
        "batch_numpy_stack",
        8 * batch * padded,
        8 * batch * padded,
        note="Separate FP32 waveform and int32 sample-mask arrays",
    )
    add(
        "torch_from_numpy_and_float32_to_cpu_alias",
        note="No copy for declared contiguous CPU FP32 input",
    )
    add(
        "hann_window_per_call",
        read=16 * (nfft + 1),
        write=20 * (nfft + 1),
        scalar=3 * (nfft + 1) + 2,
        special={"cos": nfft + 1, "arange_elements": nfft + 1},
        internal_arithmetic="TensorFactories hamming_window: 401-element arange, mul/cos/mul/add in place, then narrow to400; 2 FP64 coefficient operations",
        allocated_bytes=4 * (nfft + 1),
        returned_elements=nfft,
    )
    add(
        "reflect_pad_center",
        4 * batch * (padded + nfft),
        4 * batch * (padded + nfft),
        padding_each_side=nfft // 2,
    )
    add(
        "stft_frame_as_strided",
        shape=[batch, fft_frames, nfft],
        note="Overlapping view, not a materialized frame copy",
    )
    add(
        "window_multiply",
        8 * batch * fft_frames * nfft,
        4 * batch * fft_frames * nfft,
        scalar=batch * fft_frames * nfft,
    )
    add(
        "rfft_400",
        4 * batch * fft_frames * nfft,
        8 * batch * fft_frames * freq,
        special={"rfft_400": batch * fft_frames},
        internal_arithmetic=None,
        output_dtype="complex64",
        note="Unnormalized one-sided transform; FFT plan/workspace/internal algorithm unknown",
    )
    add(
        "drop_final_stft_frame_view",
        discarded_complex_elements=batch * freq,
        note="Discarded frame was computed by RFFT; no abs/power/mel on it",
    )
    add(
        "complex_abs",
        8 * spectrum,
        4 * spectrum,
        special={"complex_abs": spectrum},
        internal_arithmetic=None,
    )
    add("magnitude_square", 4 * spectrum, 4 * spectrum, scalar=spectrum)
    add(
        "mel_filter_fp64_to_fp32",
        8 * freq * filters,
        4 * freq * filters,
        special={"cast_fp64_fp32": freq * filters},
        note="Per-call .to(float32) copies the persistent FP64 filter bank",
    )
    add(
        "mel_projection",
        4 * (freq * filters + spectrum),
        4 * out,
        matrix=2 * batch * filters * freq * frames,
        shape=[batch, filters, freq, frames],
        input_dtype="float32",
        accumulator_policy="source torch matmul; no hardware peak assigned",
    )
    add("mel_floor_clamp", 4 * out, 4 * out, special={"compare": out}, minimum=1e-10)
    add("mel_log10", 4 * out, 4 * out, special={"log10": out})
    add(
        "per_audio_time_max",
        4 * out,
        12 * batch * filters,
        special={"compare": batch * filters * (frames - 1)},
        index_output_bytes=8 * batch * filters,
        note="Dimensional max produces int64 indices, discarded by [0] after the call",
    )
    add(
        "per_audio_mel_max",
        4 * batch * filters,
        12 * batch,
        special={"compare": batch * (filters - 1)},
        index_output_bytes=8 * batch,
        note="Dimensional max produces int64 indices, discarded by [0] after the call",
    )
    add("threshold_subtract_8", 4 * batch, 4 * batch, scalar=batch)
    add(
        "dynamic_range_maximum",
        8 * out,
        4 * out,
        special={"compare": out},
        unique_threshold_bytes=4 * batch,
        note="Broadcast operand-access bytes; threshold unique allocation is only 4*batch",
    )
    add("add_4", 4 * out, 4 * out, scalar=out)
    add("divide_4", 4 * out, 4 * out, scalar=out)
    add(
        "feature_mask_stride_and_final_trim_view",
        shape=[batch, frames],
        dtype="int32",
        note="Samples[::160], then trim last mask column if padded length not divisible by hop",
    )
    add(
        "numpy_output_view_and_tensor_views",
        note="CPU numpy()/from_numpy preserve storage; no H2D inferred",
    )
    add(
        "model_feature_lengths_sum",
        4 * batch * frames,
        8 * batch,
        integer=batch * (frames - 1),
        output_dtype="int64",
    )
    add(
        "model_mask_bool_cast",
        4 * batch * frames,
        batch * frames,
        special={"cast_int32_bool": batch * frames},
    )
    add(
        "model_valid_frame_gather",
        4 * filters * selected + batch * frames,
        4 * filters * selected,
        shape=[filters, selected],
        note="Advanced indexing materializes selected feature rows; transpose is view. Gather internal index temporaries unknown",
    )
    if encoder_element_bytes == 2:
        add(
            "explicit_caller_bf16_bridge",
            4 * filters * selected,
            2 * filters * selected,
            special={"cast_fp32_bf16": filters * selected},
            note="Caller-specified conversion, not present inside fixed get_audio_features; do not add if already performed upstream",
        )
    ref = reference_fft_work()
    ref_total = {k: v * batch * fft_frames for k, v in ref.items()}
    return dict(
        calculation="omni-audio-preprocess",
        scenario=dict(
            sample_lengths=lengths,
            sampling_rate=sampling_rate,
            encoder_element_bytes=encoder_element_bytes,
        ),
        sources=sources,
        geometry=dict(
            original_samples=lengths,
            retained_samples=valid,
            padded_samples=padded,
            serialized_max_samples=config["n_samples"],
            effective_constructor_max_samples=limit,
            serialized_max_mel_frames=config["nb_max_frames"],
            effective_constructor_max_mel_frames=limit // hop,
            stft_frames_per_audio=fft_frames,
            kept_frames_per_audio=frames,
            valid_mel_lengths=mel_lengths,
            encoded_positions=[
                13 * (n // 100) + (n % 100 + 7) // 8 for n in mel_lengths
            ],
            input_features_shape=[batch, filters, frames],
            selected_encoder_input_shape=[filters, selected],
        ),
        stages=stages,
        summary=dict(
            matrix_flops=sum(s["matrix_flops"] for s in stages),
            known_scalar_flops=sum(s["scalar_flops"] for s in stages),
            source_operand_read_bytes=sum(s["read_bytes"] for s in stages),
            source_operand_write_bytes=sum(s["write_bytes"] for s in stages),
            encoder_input_bytes=encoder_element_bytes * filters * selected,
            source_complete_arithmetic=None,
            actual_runtime_peak_bytes=None,
            measured_latency_seconds=None,
        ),
        optional_reference_fft=dict(
            algorithm="Full complex mixed-radix Cooley-Tukey radix2 then radix5; all twiddle products including trivial; retain bins0..200",
            arithmetic_dtype="Python complex/FP64 reference, source CPU torch is FP32/complex64",
            per_transform=ref,
            all_transforms=ref_total,
            coefficient_initialization="Precompute exp(-2pi*i*j*k/n); trig/complex exponential initialization separate, not per-token source work",
            not_added_to_source_subtotals=True,
        ),
        initialization=dict(
            mel_filter_bank=mel_filter_initialization(),
            hann_window="recreated per request above",
        ),
        encoder_bridge=dict(
            mel_lengths=mel_lengths,
            element_bytes=encoder_element_bytes,
            call="omni_audio_encoder.calculate(mel_lengths,element_bytes)",
            encoder_work_included=False,
        ),
        assumptions=[
            "Fixed official extractor CPU torch branch; padding=True/longest, truncation=True, return_attention_mask=True, no waveform zero-mean normalization, dither0. No file decoder or resampler.",
            "Serialized n_samples does not survive this fixed constructor without explicit chunk_length override; source default30s is used and 300s metadata retained as a source/runtime discrepancy.",
            "Selected array operators have exact shapes/interfaces. FFT and complex_abs internals remain named primitives; Hann scalar/cos work is expanded from fixed native source; mel-filter setup is separately recorded; optional reference FFT arithmetic is a separate executable implementation, never claimed as torch backend arithmetic.",
            "Read/write amounts are logical source operand interfaces, not physical memory traffic or simultaneous allocations; NumPy/runtime index metadata, FFT workspace, device transfer, CPU allocator and latency remain unknown.",
            "Features depend on batch padding context near the final valid frame; per-item valid lengths do not imply identical feature values to running every item alone. Mask gather ends at existing encoder entry; encoder/Thinker are not counted again.",
        ],
    )


def markdown(result):
    return (
        "# Omni PCM → mel calculation\n\n```json\n"
        + json.dumps(result, ensure_ascii=False, indent=2)
        + "\n```\n"
    )
