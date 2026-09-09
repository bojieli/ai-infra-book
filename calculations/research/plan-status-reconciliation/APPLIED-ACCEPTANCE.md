# Applied PLAN and C77 paragraph acceptance

The twelve proposed substitutions are each present exactly once. Reversing them, then removing only the appended C77 progress paragraph, recovers the **exact original PLAN byte SHA** `0607159ef73c0195bece454c90c46cef0fbf299087f411d26bf7b887d1689a31`. The current SHA is `3a693a1d0bf77d65a018c3a6c5ad3b5844fefccc9b502ed43a76449463d399be`. All **92 H/C/F checkbox identities and states** are exactly unchanged; the new tail contains no checkbox.

The generator's C77 insert targets the actual `> **实验 12-3` anchor in `outlines/12-端边云协同.md`. On final read the generated paragraph is at line107, immediately before the unique anchor at line109. Its full text equals the generator string, and its one-second quantities match both the corrected candidate and public calculation:

- 100 valid mel frames and13 encoder positions;
- 5,145,600 matrix FLOPs and87,306 known scalar FLOPs;
- 1,790,168 read bytes and1,277,400 write bytes;
- 51,200 FP32 encoder-input bytes.

The write count includes the independently identified and fixed1032-byte max-index outputs; the obsolete1,276,368 value is not used. Source30s versus serialized300s, Hann401 storage, FFT/abs internals, decoder/resampler omissions and no duplicate downstream encoder accounting remain explicit.

`verify_applied.py` is rerunnable and writes `application-verification.json`. This acceptance does not claim the original C77 complete-runtime requirement is finished. No public file was modified.

## Subsequent C77 public-status update

After the initial application check, the parent completed the audio integration batch and changed C77's main paragraph from “private candidate pending review/integration” to its public module link and four scenes. This is a supported subsequent amendment, not a failed application of the earlier proposal. `c77-public-followup.json` records the exact additional replacement. Reversing this replacement, then the original twelve and appended tail, still reconstructs the original PLAN SHA exactly and preserves all92 checkbox states. Current PLAN SHA after this follow-up is `be7ede2e6e7022af6675dba575a792458a01f1ee1de6a8a3fc29f23880ef7ebc`; initial verification is preserved in `application-initial-verification.json`, and `application-verification.json` binds the latest state. The generated chapter paragraph and one-second figures remain verified.
