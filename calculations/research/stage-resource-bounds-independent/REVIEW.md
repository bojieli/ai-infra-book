# C22 independent resource-bound review

The candidate implements a finite, explicitly conditional serial-layer resource calculation. It does not establish full-request latency or runtime feasibility. The independent checker preserves the author's module and imports only the public baseline helpers; it writes solely into this review directory.

## Evidence and checks

`check.py` independently reconstructs Qwen3-8B matrix work from its official dimensions for four batch/prefill/history combinations and each of 36 layers. Per layer, with Q/K denoting projected widths and F the FFN width, work is `2BT(HQ+2HK+QH+3HF)+4B(TS+T(T+1)/2)Q`; the separate final head is `2BHV`. No head multiplication by prompt length is introduced. Layer staging preserves the existing matrix, scalar and named-special subtotals.

For DeepSeek-V4-Flash, all 43 layers are checked at cold single-token and history-127 incremental inputs. This uses the pinned source's one-token continuation contract, not an unsupported multi-token cached continuation. Quantized ordinary projections/shared/routed expert matrices use FP8; `wo_a_grouped`, `index_weights_proj`, selected attention QK/PV and rectangular index QK use BF16; compressor, router, mHC and final head use the declared FP32 provider. Every matrix admission stays dense with nominal FP32 accumulation. The official `kernel.py` conversion path turns stored routed FP4 weights into FP8 operands before GEMM; FP4 storage is not a reason to admit FP4 execution throughput.

The resource-engine counterexample has stage demands (10,1) and (1,10) with unit rates: serial sum 20, pooled maximum 11. This distinction is valid under the declared whole-layer barriers. Arbitrary cross-layer micro-pipelining is outside that schedule contract. FP32 scalar and matrix work sharing one provider are added before taking the stage maximum. Declared logical FP32 scalar service is an assumption, not evidence that every source elementwise instruction executes in that dtype.

Unknown positive rates and unknown work propagate null even when other resources are known. A zero demand requires no service-rate disclosure. Exact BF16/FP8 dense admission rejects TF32, INT8 or structured-sparse substitutes; unknown Apple/Huawei fields stay unknown. Named special rates and supplied interface bytes are conditional caller inputs. Interface byte counts must not be relabelled measured HBM traffic.

Qwen's BF16 weights plus post-call KV is a necessary capacity condition only. Capacity boundaries at required bytes minus one, exactly required bytes and plus one are checked independently. DeepSeek's checkpoint includes storage representations that differ from runtime, so its checkpoint comparison cannot establish a runtime failure or success. Supplied traffic and special rates do not change that limitation.

## Admission issue found

The original frozen module `3cc0fe74d6b4ace1ec57977dfb4a2cc90e45ef12feb1d9156b5f7618476f87c7` passes 1724 of 1725 checks. A synthetic hardware record with unknown nominal capacity leaves `comparison_exceeds_nominal=null`, but `not exceeds` evaluates true and produces a finite capacity-qualified bound. This is a real unknown-propagation issue, although current populated hardware capacities do not trigger it. The author has been asked to require a known capacity and an explicit false comparison, and to expose an unknown-capacity status. The final correction sets `runtime_status=necessary_capacity_unknown` and requires `exceeds is False` for the capacity-qualified field. Independent re-run: **1725/1725 pass**, plus **7/7 portable author tests pass**. The final module SHA is `7a339350d3039c10f521158f567101f12a4a3555d6157a0ee757bcd3fa2f1d17`. Only these two admission expressions changed from the reviewed snapshot. The original failure remains in `original-verification.json` and `original-final.snapshot.py`. No blocking issue remains for this finite conditional-stage contract.

## Preserved limitations

No actual runtime latency, allocator feasibility, special-function implementation throughput, compiler dispatch, or cross-layer schedule is inferred. Qwen and V4 baseline accounts retain their declared missing work; caller rates cannot close missing model operations. Official peak evidence identifies API/nominal accumulator semantics and retains any internal-precision qualification. Neither dense throughput nor FP32 accumulation labels imply a stronger internal numerical guarantee than the linked official source states.

Re-run: `PYTHONDONTWRITEBYTECODE=1 python calculations/research/stage-resource-bounds-independent/check.py`. `checks.json` contains individual assertions; `verification.json` and `final.snapshot.py` bind the reviewed code. The original `pre-freeze.snapshot.py` remains preserved. These are semantic checks, not source-SHA substitutes for review.
