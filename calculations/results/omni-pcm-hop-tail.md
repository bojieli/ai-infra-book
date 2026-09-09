# Omni PCM → mel calculation

```json
{
  "calculation": "omni-audio-preprocess",
  "scenario": {
    "sample_lengths": [
      321
    ],
    "sampling_rate": 16000,
    "encoder_element_bytes": 4
  },
  "sources": [
    {
      "file": "sources/feature_extraction_whisper.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/whisper/feature_extraction_whisper.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "c209e669fae0ea5de92e1846d8790e3d6d66ce28f4cd4071789c2eec88c84a66",
      "bytes": 16732
    },
    {
      "file": "sources/processing_qwen3_omni_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/processing_qwen3_omni_moe.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "9a76d2dd84228fdfe5200808fe46d1fbd7884450944b5ee1f3fe8a8b03cad83f",
      "bytes": 17321
    },
    {
      "file": "sources/audio_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/audio_utils.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "c038450307a8dbc9a95eed8e413770f34814fa38058121ca9f2eee8dd0dfa958",
      "bytes": 54284
    },
    {
      "file": "sources/feature_extraction_sequence_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/feature_extraction_sequence_utils.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "53ad1320349b74523f303d09c687bf6841abc23a2a11a7cfe9e18c60aa45f631",
      "bytes": 18273
    },
    {
      "file": "sources/feature_extraction_utils.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/feature_extraction_utils.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "6861009e5aa196676c5b3827adbd64b03c217bc6f51f1560e0dbecbe9a361edf",
      "bytes": 30754
    },
    {
      "file": "sources/preprocessor_config.json",
      "url": "https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/resolve/26291f793822fb6be9555850f06dfe95f2d7e695/preprocessor_config.json",
      "revision": "26291f793822fb6be9555850f06dfe95f2d7e695",
      "sha256": "b10e27fd4542cf89ec7145942b87f3e65408d4e9f9d031a29acdd293c15fb3fc",
      "bytes": 603
    },
    {
      "file": "sources/SpectralOps.cpp",
      "url": "https://raw.githubusercontent.com/pytorch/pytorch/134179474539648ba7dee1317959529fbd0e7f89/aten/src/ATen/native/SpectralOps.cpp",
      "revision": "134179474539648ba7dee1317959529fbd0e7f89",
      "sha256": "42e9e2ffd9370785e7f59a3ef9299b283ac468ebd0d238fb4ef61bddc36b6329",
      "bytes": 50705
    },
    {
      "file": "sources/TensorFactories.cpp",
      "url": "https://raw.githubusercontent.com/pytorch/pytorch/134179474539648ba7dee1317959529fbd0e7f89/aten/src/ATen/native/TensorFactories.cpp",
      "revision": "134179474539648ba7dee1317959529fbd0e7f89",
      "sha256": "2a6df4c4210338ab9f89cbee0964f278f1a06018c18f588ef84bcfb65e15123a",
      "bytes": 72454
    },
    {
      "file": "sources/modeling_qwen3_omni_moe.py",
      "url": "https://raw.githubusercontent.com/huggingface/transformers/8cb5963cc22174954e7dca2c0a3320b7dc2f4edc/src/transformers/models/qwen3_omni_moe/modeling_qwen3_omni_moe.py",
      "revision": "8cb5963cc22174954e7dca2c0a3320b7dc2f4edc",
      "sha256": "809eaeb4d40cb0e59965a85b5f85ddc07e9ab7b6cdae84972c711f8cdadec296",
      "bytes": 182410
    }
  ],
  "geometry": {
    "original_samples": [
      321
    ],
    "retained_samples": [
      321
    ],
    "padded_samples": 321,
    "serialized_max_samples": 4800000,
    "effective_constructor_max_samples": 480000,
    "serialized_max_mel_frames": 30000,
    "effective_constructor_max_mel_frames": 3000,
    "stft_frames_per_audio": 3,
    "kept_frames_per_audio": 2,
    "valid_mel_lengths": [
      2
    ],
    "encoded_positions": [
      1
    ],
    "input_features_shape": [
      1,
      128,
      2
    ],
    "selected_encoder_input_shape": [
      128,
      2
    ]
  },
  "stages": [
    {
      "id": "numpy_input_wrapper_copy",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1284,
      "write_bytes": 1284,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "note": "np.asarray([speech],dtype=float32).T creates one array per original mono input before truncation"
    },
    {
      "id": "truncate_views",
      "source_file": "sources/feature_extraction_sequence_utils.py",
      "source_locator": "SequenceFeatureExtractor.pad / _truncate / _pad",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "note": "Each length capped at effective constructor n_samples; view only",
      "dropped_samples": [
        0
      ]
    },
    {
      "id": "right_pad_waveforms",
      "source_file": "sources/feature_extraction_sequence_utils.py",
      "source_locator": "SequenceFeatureExtractor.pad / _truncate / _pad",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "zero_fill_bytes": 0
    },
    {
      "id": "sample_mask_ones",
      "source_file": "sources/feature_extraction_sequence_utils.py",
      "source_locator": "SequenceFeatureExtractor.pad / _truncate / _pad",
      "read_bytes": 0,
      "write_bytes": 1284,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "dtype": "int32"
    },
    {
      "id": "right_pad_sample_masks",
      "source_file": "sources/feature_extraction_sequence_utils.py",
      "source_locator": "SequenceFeatureExtractor.pad / _truncate / _pad",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "zero_fill_bytes": 0
    },
    {
      "id": "batch_numpy_stack",
      "source_file": "sources/feature_extraction_sequence_utils.py",
      "source_locator": "SequenceFeatureExtractor.pad / _truncate / _pad",
      "read_bytes": 2568,
      "write_bytes": 2568,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "note": "Separate FP32 waveform and int32 sample-mask arrays"
    },
    {
      "id": "torch_from_numpy_and_float32_to_cpu_alias",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "note": "No copy for declared contiguous CPU FP32 input"
    },
    {
      "id": "hann_window_per_call",
      "source_file": "sources/TensorFactories.cpp",
      "source_locator": "hann_window -> hamming_window, periodic increment and narrow",
      "read_bytes": 6416,
      "write_bytes": 8020,
      "scalar_flops": 1205,
      "matrix_flops": 0,
      "special_ops": {
        "cos": 401,
        "arange_elements": 401
      },
      "integer_ops": 0,
      "internal_arithmetic": "TensorFactories hamming_window: 401-element arange, mul/cos/mul/add in place, then narrow to400; 2 FP64 coefficient operations",
      "allocated_bytes": 1604,
      "returned_elements": 400
    },
    {
      "id": "reflect_pad_center",
      "source_file": "sources/SpectralOps.cpp",
      "source_locator": "stft: center padding, as_strided, window multiply, _fft_r2c",
      "read_bytes": 2884,
      "write_bytes": 2884,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "padding_each_side": 200
    },
    {
      "id": "stft_frame_as_strided",
      "source_file": "sources/SpectralOps.cpp",
      "source_locator": "stft: center padding, as_strided, window multiply, _fft_r2c",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "shape": [
        1,
        3,
        400
      ],
      "note": "Overlapping view, not a materialized frame copy"
    },
    {
      "id": "window_multiply",
      "source_file": "sources/SpectralOps.cpp",
      "source_locator": "stft: center padding, as_strided, window multiply, _fft_r2c",
      "read_bytes": 9600,
      "write_bytes": 4800,
      "scalar_flops": 1200,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0
    },
    {
      "id": "rfft_400",
      "source_file": "sources/SpectralOps.cpp",
      "source_locator": "stft: center padding, as_strided, window multiply, _fft_r2c",
      "read_bytes": 4800,
      "write_bytes": 4824,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "rfft_400": 3
      },
      "integer_ops": 0,
      "internal_arithmetic": null,
      "output_dtype": "complex64",
      "note": "Unnormalized one-sided transform; FFT plan/workspace/internal algorithm unknown"
    },
    {
      "id": "drop_final_stft_frame_view",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "discarded_complex_elements": 201,
      "note": "Discarded frame was computed by RFFT; no abs/power/mel on it"
    },
    {
      "id": "complex_abs",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 3216,
      "write_bytes": 1608,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "complex_abs": 402
      },
      "integer_ops": 0,
      "internal_arithmetic": null
    },
    {
      "id": "magnitude_square",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1608,
      "write_bytes": 1608,
      "scalar_flops": 402,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0
    },
    {
      "id": "mel_filter_fp64_to_fp32",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 205824,
      "write_bytes": 102912,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "cast_fp64_fp32": 25728
      },
      "integer_ops": 0,
      "note": "Per-call .to(float32) copies the persistent FP64 filter bank"
    },
    {
      "id": "mel_projection",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 104520,
      "write_bytes": 1024,
      "scalar_flops": 0,
      "matrix_flops": 102912,
      "special_ops": {},
      "integer_ops": 0,
      "shape": [
        1,
        128,
        201,
        2
      ],
      "input_dtype": "float32",
      "accumulator_policy": "source torch matmul; no hardware peak assigned"
    },
    {
      "id": "mel_floor_clamp",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1024,
      "write_bytes": 1024,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "compare": 256
      },
      "integer_ops": 0,
      "minimum": 1e-10
    },
    {
      "id": "mel_log10",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1024,
      "write_bytes": 1024,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "log10": 256
      },
      "integer_ops": 0
    },
    {
      "id": "per_audio_time_max",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1024,
      "write_bytes": 1536,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "compare": 128
      },
      "integer_ops": 0,
      "index_output_bytes": 1024,
      "note": "Dimensional max produces int64 indices, discarded by [0] after the call"
    },
    {
      "id": "per_audio_mel_max",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 512,
      "write_bytes": 12,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "compare": 127
      },
      "integer_ops": 0,
      "index_output_bytes": 8,
      "note": "Dimensional max produces int64 indices, discarded by [0] after the call"
    },
    {
      "id": "threshold_subtract_8",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 4,
      "write_bytes": 4,
      "scalar_flops": 1,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0
    },
    {
      "id": "dynamic_range_maximum",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 2048,
      "write_bytes": 1024,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "compare": 256
      },
      "integer_ops": 0,
      "unique_threshold_bytes": 4,
      "note": "Broadcast operand-access bytes; threshold unique allocation is only 4*batch"
    },
    {
      "id": "add_4",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1024,
      "write_bytes": 1024,
      "scalar_flops": 256,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0
    },
    {
      "id": "divide_4",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 1024,
      "write_bytes": 1024,
      "scalar_flops": 256,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0
    },
    {
      "id": "feature_mask_stride_and_final_trim_view",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "shape": [
        1,
        2
      ],
      "dtype": "int32",
      "note": "Samples[::160], then trim last mask column if padded length not divisible by hop"
    },
    {
      "id": "numpy_output_view_and_tensor_views",
      "source_file": "sources/feature_extraction_whisper.py",
      "source_locator": "WhisperFeatureExtractor._torch_extract_fbank_features / __call__",
      "read_bytes": 0,
      "write_bytes": 0,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "note": "CPU numpy()/from_numpy preserve storage; no H2D inferred"
    },
    {
      "id": "model_feature_lengths_sum",
      "source_file": "sources/modeling_qwen3_omni_moe.py",
      "source_locator": "get_audio_features: mask sum, bool cast, advanced-index gather",
      "read_bytes": 8,
      "write_bytes": 8,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 1,
      "output_dtype": "int64"
    },
    {
      "id": "model_mask_bool_cast",
      "source_file": "sources/modeling_qwen3_omni_moe.py",
      "source_locator": "get_audio_features: mask sum, bool cast, advanced-index gather",
      "read_bytes": 8,
      "write_bytes": 2,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {
        "cast_int32_bool": 2
      },
      "integer_ops": 0
    },
    {
      "id": "model_valid_frame_gather",
      "source_file": "sources/modeling_qwen3_omni_moe.py",
      "source_locator": "get_audio_features: mask sum, bool cast, advanced-index gather",
      "read_bytes": 1026,
      "write_bytes": 1024,
      "scalar_flops": 0,
      "matrix_flops": 0,
      "special_ops": {},
      "integer_ops": 0,
      "shape": [
        128,
        2
      ],
      "note": "Advanced indexing materializes selected feature rows; transpose is view. Gather internal index temporaries unknown"
    }
  ],
  "summary": {
    "matrix_flops": 102912,
    "known_scalar_flops": 3320,
    "source_operand_read_bytes": 351446,
    "source_operand_write_bytes": 140522,
    "encoder_input_bytes": 1024,
    "source_complete_arithmetic": null,
    "actual_runtime_peak_bytes": null,
    "measured_latency_seconds": null
  },
  "optional_reference_fft": {
    "algorithm": "Full complex mixed-radix Cooley-Tukey radix2 then radix5; all twiddle products including trivial; retain bins0..200",
    "arithmetic_dtype": "Python complex/FP64 reference, source CPU torch is FP32/complex64",
    "per_transform": {
      "real_multiplications": 28800,
      "real_additions": 24000,
      "complex_products": 7200
    },
    "all_transforms": {
      "real_multiplications": 86400,
      "real_additions": 72000,
      "complex_products": 21600
    },
    "coefficient_initialization": "Precompute exp(-2pi*i*j*k/n); trig/complex exponential initialization separate, not per-token source work",
    "not_added_to_source_subtotals": true
  },
  "initialization": {
    "mel_filter_bank": {
      "shape": [
        201,
        128
      ],
      "dtype": "float64",
      "persistent_bytes": 205824,
      "logarithmic_centers": 87,
      "operations": [
        {
          "id": "hertz_endpoints",
          "scalar_flops": 9,
          "special_ops": {
            "log": 3,
            "compare": 2
          },
          "note": "Both endpoints evaluate logstep and linear branch; 8000Hz overwrites with logarithmic branch"
        },
        {
          "id": "mel_linspace",
          "scalar_flops": null,
          "special_ops": {
            "linspace_elements": 130
          },
          "output_bytes": 1040
        },
        {
          "id": "mel_to_hertz",
          "scalar_flops": 522,
          "special_ops": {
            "log": 1,
            "exp": 87,
            "compare": 130
          },
          "output_bytes": 1040
        },
        {
          "id": "frequency_linspace",
          "scalar_flops": null,
          "special_ops": {
            "linspace_elements": 201
          },
          "output_bytes": 1608
        },
        {
          "id": "filter_diff",
          "scalar_flops": 129,
          "output_bytes": 1032
        },
        {
          "id": "frequency_slopes",
          "scalar_flops": 26130,
          "output_bytes": 209040
        },
        {
          "id": "down_slopes_negate_then_divide",
          "scalar_flops": 25728,
          "special_ops": {
            "sign_change": 25728
          },
          "temporary_output_bytes": 411648
        },
        {
          "id": "up_slopes_divide",
          "scalar_flops": 25728,
          "output_bytes": 205824
        },
        {
          "id": "triangle_min_then_zero_max",
          "scalar_flops": 0,
          "special_ops": {
            "compare": 51456
          },
          "temporary_output_bytes": 411648
        },
        {
          "id": "slaney_enorm_difference_divide",
          "scalar_flops": 256,
          "temporary_output_bytes": 2048
        },
        {
          "id": "slaney_filter_scale",
          "scalar_flops": 25728,
          "output_bytes": 205824,
          "note": "In-place filter bank scaling"
        },
        {
          "id": "zero_filter_diagnostic",
          "scalar_flops": 0,
          "special_ops": {
            "compare": 25728,
            "boolean_or": 127
          },
          "temporary_output_bytes": 1153
        }
      ],
      "known_scalar_flops": 104230,
      "complete_arithmetic": null,
      "scope": "Extractor construction once; array intermediates shown, not summed as simultaneous peak. NumPy linspace internals and setup source operand traffic remain primitive boundaries; never counted as zero."
    },
    "hann_window": "recreated per request above"
  },
  "encoder_bridge": {
    "mel_lengths": [
      2
    ],
    "element_bytes": 4,
    "call": "omni_audio_encoder.calculate(mel_lengths,element_bytes)",
    "encoder_work_included": false
  },
  "assumptions": [
    "Fixed official extractor CPU torch branch; padding=True/longest, truncation=True, return_attention_mask=True, no waveform zero-mean normalization, dither0. No file decoder or resampler.",
    "Serialized n_samples does not survive this fixed constructor without explicit chunk_length override; source default30s is used and 300s metadata retained as a source/runtime discrepancy.",
    "Selected array operators have exact shapes/interfaces. FFT and complex_abs internals remain named primitives; Hann scalar/cos work is expanded from fixed native source; mel-filter setup is separately recorded; optional reference FFT arithmetic is a separate executable implementation, never claimed as torch backend arithmetic.",
    "Read/write amounts are logical source operand interfaces, not physical memory traffic or simultaneous allocations; NumPy/runtime index metadata, FFT workspace, device transfer, CPU allocator and latency remain unknown.",
    "Features depend on batch padding context near the final valid frame; per-item valid lengths do not imply identical feature values to running every item alone. Mask gather ends at existing encoder entry; encoder/Thinker are not counted again."
  ]
}
```
