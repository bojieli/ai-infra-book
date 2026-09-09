# Final acceptance addendum

The required max-index correction is now independently verified and accepted. Frozen module SHA is `53095fde1770b14e467d3035c15f68e34695f1aa98fa28632450be2a7c65cb60`. Reversing only the two write-count changes and their new index/note fields reproduces the exact previously audited module SHA. Executing that reconstructed original and the fixed candidate proves every result field is unchanged except the declared max-index fields and +1032 bytes per audio in total writes. Four frozen scenarios pass this differential test. Source/bindings, numeric and portable tests were rerun:119 checks and6 tests, zero skipped. See `verify_fix.py` and `fix-verification.json`.

The earlier review below is retained as history; its sole required correction is closed. No further blocking issue remains within the selected decoded-PCM contract.

---

# Independent C77 decoded PCM frontend review

Core geometry and numerical path pass. One finite source-interface correction is required before claiming the selected output byte ledger is complete: dimensional `torch.max` produces int64 indices in addition to values. The candidate currently omits those index outputs. No matrix, scalar, mel value, mask or encoder count changes are required.

Audited module SHA: `077bc4ec20010b21df644573f55d1e249919b777287d1d2ce0ca6250b5d6d331`. `audit.py` ran with `/Users/boj/miniconda3/bin/python`, Torch 2.7.0 commit `134179474539648ba7dee1317959529fbd0e7f89`. 116 independent assertions and the original six tests passed, zero skipped. The assertions include manifest/source hashes and four frozen scenario replays; this count is not a claim of 116 distinct numerical algorithms. Author files were not changed.

## Accepted source mapping

* Fixed `feature_extraction_whisper.py:77,93–95` gives constructor default `chunk_length=30`, then unconditionally assigns sample/frame caps. Serialized `n_samples=4800000` and `nb_max_frames=30000` do not survive this constructor. Fixed processor `:175–176` forces padding=True without overriding chunk_length or default truncation. An actual 4,800,000-sample input was replayed and produced 3000 mel frames. The candidate appropriately retains both serialized and effective fields; this conclusion is revision/path specific.
* For retained batch maximum P, source center reflection creates P+400 samples; window views contain floor(P/160)+1 FFT frames, and `stft[..., :-1]` removes the last before magnitude/power/mel. Explicit coordinate enumeration reproduces masks including P=201/319/320/321 and mixed [479,800], [1,961], [200,640]. An individual <=200 input is valid inside a longer padded batch; only the padded waveform determines reflection legality. Valid lengths are min(ceil(n/160),floor(P/160)).
* The native periodic Hann increments length to401, applies mul/cos/mul/add, then returns400 values as a narrow view. Actual underlying storage is1604 bytes. 1203 elementwise arithmetic operations plus2 double coefficient operations and401 cosine calls agree. These are source-operation counts, not generated kernel instruction counts.
* The 201×128 dense FP32 mel projection costs 2B×128×201×F. The independently derived selected scalar subtotal is 1205+B[400(F+1)+457F+1]. Per-audio maximum rather than a batch-global maximum is correct. Mask int32→bool and flattened valid-frame gather map to the existing encoder endpoint without charging encoder matrices again.
* Independent Slaney bank construction from piecewise centers and individual triangle equations agrees with the original bank to <1e-14. Independent NumPy one-sided FFT/frame construction and normalization agree with selected official execution to <1e-4 across eight short/mixed numerical cases. See `results.json` for individual errors. These tests reuse the author's AST source loader but do not reuse its FFT, filter-bank helpers or numerical reference. The loader's container shims are explicitly disclosed and were checked against this NumPy path; this is not an installed full Transformers execution.
* The separate radix2/radix5 recursion tree yields28800 multiplies and24000 additions per full-complex transform. This deliberately counts all twiddle products and is a separate FP64 reference implementation, not a cost estimate for Torch's one-sided `_fft_r2c`. Keeping library FFT, complex magnitude internals and setup linspace unresolved is correct. No source totals should absorb the reference FFT figures.

## Required finite correction: max indices

Official selected source is `feature_extraction_whisper.py:160`: `log_spec.max(dim=2, keepdim=True)[0].max(dim=1, keepdim=True)[0]`. Both calls invoke dimension max, which returns values and int64 indices. Index selection `[0]` discards the indices after they have been produced; it does not make the preceding operation values-only. Runtime inspection with the pinned Torch version confirms B=2 produces2048 index bytes for time max and16 for mel max.

Update `per_audio_time_max` write bytes from4B×128 to12B×128, and `per_audio_mel_max` from4B to12B. Add separate `index_output_bytes` fields and explain that these outputs are discarded. No later read should be charged for those discarded indices. Total logical output bytes increase by1032B per audio: the one-second scenario changes1,276,368→1,277,400. This is not a claim of simultaneous peak or physical DRAM traffic. A minimal proposed diff is supplied in `max-indices.patch`; no author/shared file has been modified.

## Scope and remaining boundaries

No other blocking discrepancy was found in the selected contract. Cold setup traffic and NumPy internals are explicitly incomplete; source integer address generation, backend complex abs/FFT workspace, indexing internals, device movement and allocator peak remain unspecified. The claim is a selected PCM-to-encoder-input graph, not a whole processor invocation: placeholder replacement's extra feature-length operations, file decoding/resampling, encoder/Thinker/Talker, and runtime scheduling remain outside. BF16 is explicitly a caller bridge, not an inferred hidden cast in `get_audio_features`. The discovered index output should be repaired rather than subsumed under unknown backend internals because the source interface exposes its exact shape and dtype.
