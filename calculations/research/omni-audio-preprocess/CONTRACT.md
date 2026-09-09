# C77 decoded PCM frontend contract

This candidate counts a fixed official Qwen3-Omni / Whisper frontend from already decoded mono NumPy FP32 PCM to the valid mel tensor entering the existing audio encoder. It does not rerun or recharge the encoder, Thinker, Talker or output codec. The implementation uses the same Transformers `8cb5963cc22174954e7dca2c0a3320b7dc2f4edc` as the public Omni audio encoder, and an explicitly fixed CPU Torch 2.7.0 source revision.

Inputs are a list of waveform sample lengths at exactly 16000 Hz. `padding=True` means batch longest after truncation; dither=0, waveform zero-mean normalization is off, and attention masks are returned. Audio file decoding/resampling is excluded; mismatched sample rate is rejected. If the batch longest retained length is <=200, source reflect padding fails and this calculator rejects it. A short member of a longer padded batch can be valid; it must not be rejected solely from its own length.

## Source/runtime discrepancy: 30 seconds vs serialized 300 seconds

The official preprocessor JSON contains n_samples=4,800,000 and nb_max_frames=30,000 but no chunk_length. Fixed WhisperFeatureExtractor.__init__ takes chunk_length=30 and unconditionally reassigns n_samples and nb_max_frames. from_dict simply calls this constructor with the JSON. Thus the actual default execution cap is 480,000 samples / 3000 frames. The Omni processor sets padding=True, but it does not override extractor truncation=True or provide chunk_length. Both serialized and effective fields are retained. The numeric runner executes the original constructor and padding methods, confirming this discrepancy; this is not a claim that every deployment or newer revision truncates at 30 seconds. An explicit chunk_length=300 override would be a separate scenario contract.

For retained lengths n_i and P=max(n_i), F=floor(P/160), the STFT computes F+1 frames with reflect200 on both ends and a 400-element periodic Hann. It subsequently discards the final frame before magnitude and mel work. Each mask is sampled at stride160 and its final column trimmed when P is not divisible by160. Valid mel length is min(ceil(n_i/160),F), not unconditionally floor(n_i/160). Batch padding changes final-frame values, so a cached audio feature key cannot ignore frontend context without further proof.

## Exact source operators and declared primitives

All selected stages carry matrix/scalar/special/byte fields. The 201×128 filter projection is dense FP32 matmul. Complex magnitude, FFT internals and NumPy setup linspace remain named primitives with unknown internal arithmetic; they are never zero FLOPs. CPU FFT uses `_fft_r2c`, whose implementation depends on backend. No `5N log N` estimate is labelled exact runtime work.

An executable full-complex mixed-radix 400-point FFT reference is separately supplied and verified, using radix2 then radix5, all complex twiddle products including trivial ones, and scalar complex multiplication/addition formulas. It performs 28,800 real multiplies and 24,000 real additions per transform. It computes the full complex spectrum before retaining bins0..200 and uses FP64/Python complex. These numbers are not added to the Torch source subtotal and do not represent the optimized one-sided Torch FFT. Twiddle coefficient construction is separate initialization.

The actual native Hann routine builds 401 values, performs mul/cos/mul/add, then returns a 400-element narrow view. The underlying buffer is 1604 bytes, with 401 cos calls and 1203 FP32 elementwise operations plus two FP64 coefficient arithmetic operations. Filter-bank initialization is separately expanded into Slaney endpoint/center conversion, slopes/triangles/normalization and diagnostics; linspace/internal array runtime remains named and incomplete.

## Interfaces and scope

Source operand access bytes are not DRAM traffic or simultaneous allocation. The waveform wrapper copies original input before truncation; right-padding and batch stacking are separate materializations. `torch.from_numpy` and CPU FP32 `.to` are aliases in this declared input path. Final mask stride/transposes are views, but mask bool conversion and selected-feature advanced indexing materialize. Filter FP64→FP32 conversion repeats each call. The encoder endpoint is `[128,sum(valid_mel_lengths)]`, FP32 by default. Optional BF16 is an explicit caller bridge, not a hidden cast inside get_audio_features.

The original processor computes another feature-length sum for placeholder replacement; this candidate does not yet budget text placeholder expansion or its repeated metadata operations, and does not claim a complete processor call. The source path to the selected audio encoder endpoint includes its own mask sum/cast/gather. Full runtime peak, FFT workspace, advanced-index internals, device transfer and latency remain null.

## Verification scope

Four complete numerical cases compare selected original official methods against independently assembled frames, mixed-radix FFT, mask geometry and normalization. FP64 reference vs FP32 source tolerance is 1e-4; observed max error is 3.19e-5, so no bitwise or 1e-5 claim is made. FFT itself differs from NumPy FFT by <=1.43e-13. Seven source-executed geometry/cap cases include a 4.8-million-sample waveform that is actually truncated to480k; three short-input rejection cases are checked. Dependency container shims are disclosed in source_runner.py; it is not a full installed Transformers model execution. Six standalone tests cover formulas, source/cap discrepancy, padding, bridge, reference counts and invalid inputs.
