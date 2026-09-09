"""Pinned Fish text2semantic CLI code accumulation -> single codec -> host wave.

Reuse the existing complete codec operation ledger; add only wrapper interfaces.
"""

from fractions import Fraction

from infra_calc.topics import omni_audio
from infra_calc.units import positive_int


def calculate(chunk_frames=(21, 22), waveform_dtype="bf16", code_element_bytes=8):
    """Explicit observed/declared emitted chunks, one output sample, GPU CLI path.

    Code integer width is explicit because generate returns prompt.dtype while
    sampling uses torch.int. This does not infer tokenizer output dtype.
    """
    if not isinstance(chunk_frames, (list, tuple)) or not chunk_frames:
        raise ValueError("chunk_frames must contain positive emitted frame counts")
    for frames in chunk_frames:
        positive_int(frames, "chunk frames")
    if type(code_element_bytes) is not int or code_element_bytes not in (4, 8):
        raise ValueError("Code int32/int64 width must be4 or8")
    if waveform_dtype not in ("bf16", "fp32"):
        raise ValueError("Explicit BF16 orFP32 codec waveform dtype required")
    total_frames = sum(chunk_frames)
    if total_frames > 32768:
        raise ValueError(
            "Merged sequence exceeds pinned post-transformer causal-mask extent"
        )
    sources = omni_audio.evidence()
    config = omni_audio.fish_codec_config()
    width = 2 if waveform_dtype == "bf16" else 4
    codec = omni_audio.omni_codec_operators(
        total_frames, 1, config, width, codec_kind="fish"
    )
    samples = codec["output_samples_per_request"]
    books = config["num_quantizers"]
    code_bytes = total_frames * books * code_element_bytes
    events = []
    accumulated = 0
    for i, frames in enumerate(chunk_frames):
        payload = frames * books * code_element_bytes
        accumulated += payload
        events.append(
            dict(
                stage="sample_code_clone_and_cpu_conversation",
                chunk=i,
                frames=frames,
                device_copy_read_bytes=payload,
                device_copy_write_bytes=payload,
                device_to_host_bytes=payload,
                held_code_list_device_bytes=accumulated,
                code_nonnegative_comparisons=frames * books,
                code_validity_logical_reductions=frames * books - 1,
                code_validity_bool_tensor_bytes=frames * books,
                code_validity_host_scalar_checks=1,
                note="codes=y[1:,prompt_length:-1].clone(); conversation receives codes.cpu(); yielded codes remain on original device.",
            )
        )
    events.extend(
        [
            dict(
                stage="next_concat_codes",
                executions=1,
                device_copy_read_bytes=code_bytes,
                device_copy_write_bytes=code_bytes,
                code_list_plus_merged_device_bytes=2 * code_bytes,
            ),
            dict(
                stage="save_merged_codes_numpy_input",
                executions=1,
                device_to_host_bytes=code_bytes,
                host_array_alias_bytes=code_bytes,
                note="merged_codes.cpu().numpy(); NumPy aliases CPU tensor. NPY serialization/header and file IO excluded.",
            ),
            dict(
                stage="single_codec_decode",
                executions=1,
                frames=total_frames,
                matrix_flops=codec["summary"]["matrix_flops"],
                note="Reuse codec operators exactly once after next; no per-sample-chunk codec call.",
            ),
            dict(
                stage="wave_cpu_then_float",
                executions=1,
                device_to_host_bytes=samples * width,
                host_cast_read_bytes=samples * width if width != 4 else 0,
                host_cast_write_bytes=samples * 4 if width != 4 else 0,
                cast_elements=samples if width != 4 else 0,
                host_numpy_alias_bytes=samples * 4,
                host_input_output_cast_overlap_bytes=samples * (width + 4)
                if width != 4
                else samples * 4,
                note="text2semantic CLI: audio.cpu().float().numpy(); same-dtype float() is a no-op.",
            ),
        ]
    )
    return dict(
        calculation="fish-cli-wave-export",
        model="fish-audio-s2-pro",
        scenario=dict(
            chunk_frames=list(chunk_frames),
            waveform_dtype=waveform_dtype,
            code_element_bytes=code_element_bytes,
        ),
        sources=sources,
        wrapper_stages=events,
        codec_operations=codec,
        summary=dict(
            codec_decode_calls=1,
            emitted_sample_chunks=len(chunk_frames),
            acoustic_frames=total_frames,
            output_samples=samples,
            exact_audio_duration_seconds=str(Fraction(samples, config["sample_rate"])),
            code_device_to_host_bytes=2 * code_bytes,
            waveform_device_to_host_bytes=samples * width,
            standalone_dac_cli_wave_device_to_host_bytes=samples * 4,
            decoder_matrix_flops=codec["summary"]["matrix_flops"],
            full_request_latency_seconds=None,
            first_audio_latency_seconds=None,
            measured_rtf=None,
            output_file_bytes=None,
            full_runtime_peak_bytes=None,
        ),
        scope=[
            "Pinned CLI with output enabled, one requested sample, GPU-generated code chunks and codec already loaded on that device. CPU path and codec model loading are not zero-cost substitutes.",
            "sample events expose codes only; CLI waits for next, concatenates all codes, then decodes once. No waveform is produced per emitted code chunk on this path.",
            "Requires actual emitted frame counts after unconditional y[1:, prompt_length:-1] slicing; removed last position need not be terminal. codeframes=returned_y_length-prompt_length-1. Text chunk_length is a text-byte limit, not audio frames or seconds.",
            "AR/fast-head work remains in omni_audio and is not duplicated here; codec_operations likewise replaces/reuses the existing codec stage, never add its matrices twice.",
            "Code CPU copies for conversation and NPY-save input are separate real copies. Their Python/CUDA overlap, total conversation lifetime and IO timing remain unknown.",
            "text2semantic export copies source waveform toCPU then converts toFP32; standalone dac CLI converts toFP32 on device beforeCPU. Their D2H bytes differ underBF16, though both hand float32 data to soundfile.",
            "NumPy views do not copy tensor data; soundfile encoding/default subtype/file buffering are not inferred from float32 host-array bytes.",
            "No wall-clock measurements supplied: TTFA/RTF are null. Required dependency is all code chunks -> next -> concatenation/save input -> codec -> host conversion -> file writer.",
        ],
    )


def markdown(result):
    """Report wrapper interfaces separately from the existing codec arithmetic."""
    s = result["summary"]
    lines = [
        "# Fish CLI 代码块到波形导出",
        "",
        f"{s['emitted_sample_chunks']}个实际代码块，合计{s['acoustic_frames']}帧；单次codec产生{s['output_samples']}样本。",
        "",
        "| 阶段 | D2H bytes | device复制写 bytes | CPU cast写 bytes |",
        "|---|---:|---:|---:|",
    ]
    for row in result["wrapper_stages"]:
        lines.append(
            f"| {row['stage']} | {row.get('device_to_host_bytes',0)} | {row.get('device_copy_write_bytes',0)} | {row.get('host_cast_write_bytes',0)} |"
        )
    lines += [
        "",
        f"复用codec矩阵FLOPs：{s['decoder_matrix_flops']}；实际音频时长{s['exact_audio_duration_seconds']}秒。",
        "",
        "TTFA、RTF、文件字节与完整runtime峰值未测量，保持unknown。",
        "",
        "## 范围",
        "",
    ]
    lines.extend("- " + item for item in result["scope"])
    lines += ["", "## 固定来源", ""]
    lines.extend(
        f"- [{row['file']}]({row['url']})；SHA256 `{row['sha256']}`。"
        for row in result["sources"]
    )
    return "\n".join(lines) + "\n"
