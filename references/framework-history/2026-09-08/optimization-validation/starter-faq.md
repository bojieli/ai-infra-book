# Frequently Asked Questions

Last updated: April 16, 2026

---

## Submission & Evaluation

**Q: How do I submit my solution?**

Create a starter-kit repo (one per track), push a git tag, and if your repo is private, grant read access to **flashinfer-bot** (Repo → Settings → Collaborators → Add people).

Different approaches (`full-agent` or `agent-assisted`) should be in different repositories. For one approach, if there are multiple tracks (i.e., multiple definitions, e.g., GDN decode + prefill), place each submission in a top-level subfolder named after the definition name.

**Q: I used "Use this template" instead of forking. Is that okay?**

Yes. Both template and fork are fine, as long as your repo follows the starter-kit structure.

**Q: How do I share my repo URL with organizers?**

Reply in the Discord thread with your repo URL(s) and team name, email `mlsys26-contest-contact@nvidia.com`, or DM an organizer on Discord.

**Q: Is there a public leaderboard?**

No. We run **bi-weekly evaluations** on bare-metal B200 GPUs and notify teams individually with their performance numbers and ranking via email.

**Q: How are workloads scored?**

The final score for a definition is the **arithmetic mean** of speedups across all its workloads.

**Q: What does "speedup" mean exactly?**

- **Correctness check**: your kernel's output is compared against the **Python/PyTorch reference implementation** (a simple, slow "ground truth" that defines the kernel semantics). A solution should pass this check before performance number is reported.
- **Performance ranking (speedup)**: once a solution passes correctness, speedup is measured as
  ```
  speedup = FlashInfer_baseline_latency / your_kernel_latency
  ```
  i.e., relative to the optimized **FlashInfer baseline** (`flashinfer_wrapper_*` solutions in the dataset). Higher is better.


**Q: For Track C (GDN), how are decode and prefill weighted?**

Decode and prefill are separate definitions. Our final score is the average speedup of the two definitions.

**Q: What is the maximum team size?**

Maximum **5 members** per team.

**Q: For Tracks B/C, do teams need to submit both kernels?**

Teams are expected to submit both operators/kernels for Tracks B/C, and the ranking is based on the average performance across the two. If only one of the two operators is submitted or correct, your ranking score will be half of the score of the correct operator.

**Q: What files does the evaluation pipeline use from my submission?**

If a `packed_solution.json` exists at the tag root, the pipeline uses that directly. Otherwise, it packs from `config.toml` + source files. Changes to `run_local.py`, `pack_solution.py`, or other scripts are not picked up — the pipeline uses its own packing and evaluation logic.

**Q: Where should my source files be placed?**

Based on the `language` setting in your `config.toml`:
- `language = "triton"` → `solution/triton/`
- `language = "cuda"` → `solution/cuda/`
- `language = "python"` → `solution/python/`

If you need a custom directory, use `source_dir` in the `[build]` section (relative to `solution/`):
```toml
[build]
source_dir = "my_custom_dir"
```
Note: `solution_dir` is **not** supported. Use `source_dir` instead.

**Q: Can I use multiple tags for different kernels in the same repo?**

Yes. Our pipeline scans all tags within the evaluation window and groups by definition. Multiple tags targeting different definitions will all be collected. If multiple tags target the same definition, only the latest tag is used.

Either works — all in one repo, or split across multiple repos, whichever is easier for you.

If you put everything in one repo (per approach), place each kernel in its own subdirectory (e.g., moe/, dsa_attention/, dsa_indexer/, gdn_decode/, gdn_prefill/), each with its own config.toml (one config.toml for one kernel pls). The evaluation pipeline scans the  root and immediate subdirectories for configs and packs each as a separate solution. Please remove the root-level config.toml in this case — otherwise it would get picked up as an additional solution.

Here's what a one-repo setup looks like (example with all 5 kernels):

```
my-submission-repo/
├── moe/
│   ├── config.toml          # definition = "moe_fp8_block_scale_ds_routing_topk8_ng8_kg4_e32_h7168_i2048"
│   └── solution/
│       └── triton/
│           └── kernel.py
├── dsa_attention/
│   ├── config.toml          # definition = "dsa_sparse_attention_h16_ckv512_kpe64_topk2048_ps64"
│   └── solution/
│       └── cuda/
│           └── kernel.cu
├── dsa_indexer/
│   ├── config.toml          # definition = "dsa_topk_indexer_fp8_h64_d128_topk2048_ps64"
│   └── solution/
│       └── triton/
│           └── kernel.py
├── gdn_decode/
│   ├── config.toml          # definition = "gdn_decode_qk4_v8_d128_k_last"
│   └── solution/
│       └── triton/
│           └── kernel.py
└── gdn_prefill/
    ├── config.toml          # definition = "gdn_prefill_qk4_v8_d128_k_last"
    └── solution/
        └── cuda/
            └── kernel.cu
```

**Q: What correctness tolerances are used?**

An element fails only if **both** `abs_error > atol` **AND** `rel_error > rtol`. Default tolerances:
- **DSA / GDN**: atol=0.01, rtol=0.01, required_matched_ratio=1.0
- **MoE**: atol=1, rtol=0.3, required_matched_ratio=0.9

These are the same as in the public flashinfer-bench code. There are no additional hidden numerical filters. See [EVALUATION.md](EVALUATION.md) for details.

**Q: What is the final submission deadline?**

**April 24, 11:59 PM AoE.** Any late submissions will not be accepted.

**Q: What dataset is used for evaluation?**

The final evaluation uses https://huggingface.co/datasets/flashinfer-ai/mlsys26-contest in its current form. No workload updates will be made.

---

## Official Evaluation Environment

**Q: What CUDA / Triton / PyTorch versions are used in official evaluation?**

The specific versions will be announced later. The official environment will include torch, triton, tilelang, CuTe-DSL, CuTile, and other packages. We will open a link for teams to request additional libraries.

**Q: Is the final evaluation done on Modal?**

No. The final evaluation runs on **bare-metal B200 GPUs** with locked clock frequencies. Scores on Modal are for development reference only.

**Q: Can I use `torch.utils.cpp_extension` to compile my CUDA solution?**

Yes. The flashinfer-bench TorchBuilder uses `torch.utils.cpp_extension` under the hood. You can also call it directly in a Python submission.

**Q: Can I pass custom compile flags for CUDA C++ submissions?**

The builders currently do not support custom compile flags. As a workaround, submit a Python solution and compile the CUDA kernel yourself within the code (using `torch.utils.cpp_extension.load()` or `tvm_ffi.cpp.load()`). We will consider adding compile flag support in a future update.

**Q: Can I install additional Python packages?**

The `BuildSpec` has a `dependencies` field, but builder-side support is still being finalized. For Python packages, we will use the packages in our official evaluation environment (versions to be announced). We will open a link for teams to request additional libraries.

**Q: What SM architecture is used?**

The evaluation machine supports **sm_100a**. If your CUDA kernel needs sm_100a-specific features, specify the architecture explicitly in your build flags (e.g., `-arch=sm_100a`). The build system does not automatically set SM targets.

**Q: Can I load pre-built cubins via the CUDA Driver API?**

Yes, as long as all source code (including `.cu` files) is included in your submission and the cubin is compiled from source during evaluation. Shipping pre-built cubins is not allowed.

**Q: Does the evaluation environment have network access?**

No. The evaluation environment has no network access. Your solution must be fully self-contained.

---

## Self-Contained Requirement & Library Usage

**Q: Can I use runtime API calls to external libraries (flashinfer, deep_gemm, cuBLAS, etc.)?**

Runtime API calls to **flashinfer**, **deep_gemm**, and similar specialized kernel libraries are **not allowed**. Solutions should be self-contained — all code must be included in your submission sources.

If you'd like to use techniques from an open-source library, incorporate the relevant source code directly into your submission (as long as the license permits) rather than calling the library at runtime.

**Q: What about cuBLAS?**

cuBLAS ships with the CUDA toolkit and is a standard system library. Using cuBLAS from self-contained, JIT-compiled source code is acceptable. However, since this is a kernel optimization competition, we value seeing the team's own implementation when possible.

**Q: Can I use CUTLASS/CuTe headers as building blocks?**

Yes. Using CUTLASS/CuTe headers (e.g., `cutlass::arch::*`, `cute::UMMA::*`) as low-level building blocks for your own kernel is fine — these are part of the CUDA toolkit ecosystem. What we don't allow is calling pre-built library functions at runtime.

**Q: Can I persist buffers between runs?**

Yes, as long as the buffer contents are recalculated on every run (not caching results from a previous call). Pre-allocating workspace buffers and reusing them across calls is a common and accepted optimization.

**Q: Should all computation be on the GPU?**

Yes. All meaningful computation must be on the GPU. Minimal CPU-side operations (e.g., extracting scalar values, computing indices for kernel launch) are acceptable.

---

## CuTe-DSL / CuTile

**Q: Can I use CuTe-DSL or CuTile?**

Yes. The competition supports multiple languages including CUDA, Triton, CuTe-DSL, CuTile, Tilelang, and more. All of these will be available in the official evaluation environment.

---

## GPU Resources & Profiling

**Q: Can I use NCU (Nsight Compute) on Modal?**

NCU is not currently available on Modal. We are still working with Modal to find a solution.

**Q: Does compute-sanitizer work on Modal?**

Same situation — still working with Modal to find a solution.

**Q: I haven't received my Modal credits / B200 access. What should I do?**

We are currently running out of credits and looking into alternative solutions.

**Q: Is Modal's B200 sm100 or sm100a?**

Modal B200 instances are **sm100**.

---

---

## Other

**Q: What is `binding.py` for? Isn't `PYBIND11_MODULE` enough?**

`binding.py` is for TVM FFI bindings. `PYBIND11_MODULE` is the PyTorch extension approach, which also works. Both backends (TVM FFI and Torch) are supported.

**Q: DSA currently only has decode shapes. Will there be prefill?**

Yes, both decode and prefill shapes will be available.

**Q: Track C — HuggingFace dataset uses qk4_v8 but the website uses qk16_v32. Which to target?**

Please target the specifications on the contest website [mlsys26.flashinfer.ai](http://mlsys26.flashinfer.ai). The qk4_v8 in the HuggingFace dataset is an earlier version and may be updated.

**Q: Is FlashInfer available for sm120 / Blackwell Pro 6000?**

The competition targets B200 (sm100) only. sm120 support is outside the scope of this competition.

**Q: My kernel produces no trace (len trace = 0) when running on Modal.**

If the kernel fails to run or does not pass correctness checks, no trace will be generated. Check the log file for error messages (use the `--log-file` parameter).

**Q: I'm getting "Failed to fetch" errors when uploading to Modal.**

This is an intermittent network issue on the Modal platform. Please retry.

**Q: When will implementation baselines (GDN, DSA, etc.) be released?**

Implementation baselines for all kernels will be provided in a subsequent update.

**Q: What's the difference between the full-agent track and the agent-assisted track?**

The **agent track** requires submitting the agent itself — it must fully reproduce the kernel end-to-end. The **agent-assisted track** allows experts and agents to collaborate; you submit the kernel code. Note: in the agent track, your agent's prompts and database must not contain large portions of the final solution (we will verify manually).

**Q: Can I participate in both approaches?**

Yes, we highly encourage it. Please use **separate repos** for each approach and let us know which repo is for which approach. If not specified, submissions default to Agent-Assisted.

**Q: What do Full-Agent winners need to provide?**

Awarded Full-Agent teams will need to:
- Describe the agent workflow in detail in the technical writeup
- [Optional but recommended] Provide a guide, documentation, or code to reproduce the kernel generation process

**Q: Can the agent access the internet during kernel generation?**

The evaluation environment has no network access, so the submitted solution cannot rely on network calls at runtime. You can include all necessary docs/reference code in your submission.

**Q: Do I need separate technical reports for each approach?**

If both your Full-Agent and Agent-Assisted solutions are ranked in the top 3 per track, you'll need to submit a separate report for each.

**Q: How do I install flashinfer-bench from source?**

```bash
git clone https://github.com/flashinfer-ai/flashinfer-bench.git && cd flashinfer-bench && pip install -v -e .
```

Make sure to install from source (not pip) to get the latest evaluation changes.

**Q: I got a VALIDATION_ERROR: sources - List should have at least 1 item.**

This means the pipeline couldn't find source files for your solution. Check that:
1. Your source files are in the correct directory (see "Where should my source files be placed?" above)
2. If using subdirectories, there's no conflicting `config.toml` at the repo root
3. If using `packed_solution.json`, verify it contains your actual kernel code (not the starter kit template)

**Q: My submission passed on Modal but failed in the official evaluation.**

Common causes:
- **RUNTIME_ERROR with triton.jit**: Check that your `config.toml` has the correct `language` setting and source files are in the matching directory
- **COMPILE_ERROR**: If using sm_100a features, add `-arch=sm_100a` to your build flags
- **Different results**: The official eval runs on bare-metal B200 with locked clocks. Small performance differences compared to Modal are expected.
