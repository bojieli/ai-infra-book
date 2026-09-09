# C55 GEMM saved-input extension: independent review

Accepted for the declared FP32 mathematical-reference saved-operand and conservative stage-reservation contract. Candidate SHA: `491b0f1c3fc4bb398ae6d5bda8254a1daded0c8182f52b116f5588ad508bcce7`. Independent checks: **972/972**; portable author tests: **4/4**. All four frozen scenarios replay exactly. No shared or author files were modified.

## Tensor identity and derivatives

The fixed official Qwen implementation confirms weighted RMSNorm output (`modeling_qwen3.py:76`), the actual SiLU(gate)*up input to down projection (`:94`), QK and PV operands (`:157`, `:164`), post-norm/RoPE query placement (`:217` onward), context consumed by o_proj (`:251–252`), and input/post-attention norms (`:286`, `:304`). A linear dW needs the actual forward input; dX needs resident weights. Thus normalized z is not an alias for gamma*z, and saved SiLU(g) is not an alias for SiLU(g)*u. Independent central finite differences validate dW using the reconstructed weighted/product input on small arrays.

The seven per-layer added identities and one head identity total 253. They supply 36×9+1=325 matrix instances. QKV share one weighted input; gate/up share one weighted input. P is a reference to the existing saved probability identity. QK requires post-norm/post-RoPE Q and K, while PV requires P and V. Saving unique KV heads is sufficient under the explicitly declared grouped contraction policy; the existing per-query-head gradient reduction stays in nonmatrix and is not added again. An actual backend that materializes repeated K/V may require more storage and is expressly outside this contract.

## Independent byte and work formulas

With R=bT, H=4096, projected Q width=4096, unique KV width=1024 and F=12288, saved-input bytes per layer are `4R(4H+2*1024+F)`. Each stage owns nine layers; stage 3 additionally owns `4RH` head input bytes. Product recomputation leaves only `4R(2H+2*1024)` persistent bytes per layer and no new persistent head operand.

Extra scalar work per microbatch is `R[36(2H+F)+H]`. There are no additional matrix FLOPs or special calls. The saved-byte reduction is exactly four times this product-element count. In `recompute_silu`, the pre-existing sigmoid/a pair is computed once before down-projection backward and retained until SwiGLU backward. Its two-vector workspace remains the original `8RF` per stage B. The new product buffer adds `4RF`, not another sigmoid/a pair. Product consumers are ordered so norm and SwiGLU product buffers need not overlap each other.

Checks cover both schedule policies, both nonlinear policies and both new GEMM policies. They verify exact stage bytes, input sharing, unique KV sizes, P reuse, unchanged baseline arithmetic and unchanged caller service events. Eight independent interval unions add the individual persistent tensor envelopes to the original pipeline intervals, then add only the product workspace. Every stage peak equals the candidate aggregate. The tensor envelope list is explanatory and is correctly not charged a second time inside its aggregate intervals.

## Evidence boundary

FP32 saves/reconstruction are a no-rounding mathematical reference. They do not reproduce BF16 cast rounding in the source kernel or claim its precise autograd save policy. Source-level gamma multiplication after an explicit input-dtype conversion makes this distinction substantive. Stage F-start to B-end envelopes and whole-stage B workspace reservations are conservative declared reservations; they are not exact physical tensor lifetimes. The extra arithmetic does not automatically modify service seconds; callers must supply times covering their selected strategy.

Token/label IDs, transient gradients, parameter and optimizer storage, casting/packing, backend GQA materialization, communication-to-internal-copy ownership and other workspace remain excluded. Full training activation and actual allocator peaks correctly remain null. The extension closes the stated matrix-input identity omission, not every training-memory or runtime requirement.

Re-run `PYTHONDONTWRITEBYTECODE=1 python calculations/research/training-pipeline-gemm-state-independent/check.py`. `verification.json`, `checks.json`, `candidate.snapshot.py` and `bindings.json` preserve the result, snapshot and dependencies.
