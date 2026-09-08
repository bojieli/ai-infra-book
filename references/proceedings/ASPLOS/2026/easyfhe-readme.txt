# EasyFHE

<p align="center">
  <strong>Python-first, CUDA-accelerated tensor runtime for Fully Homomorphic Encryption.</strong>
</p>

<p align="center">
  <a href="https://jizhuoran.github.io/EasyFHE/">Documentation</a> ·
  <a href="https://jizhuoran.github.io/EasyFHE/#install">Install</a> ·
  <a href="https://github.com/jizhuoran/easyfhe-examples">Examples</a>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-orange">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
  <img alt="CUDA" src="https://img.shields.io/badge/CUDA-12.9%20%7C%2013.x-green">
  <img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-blue">
</p>

EasyFHE is an encrypted tensor runtime for building CKKS-based Fully Homomorphic Encryption (FHE) applications on GPUs. It keeps the parts of a PyTorch-derived runtime that FHE workloads actually need—tensor storage, dispatch, CUDA execution, Python bindings, profiling hooks, and selected distributed-runtime infrastructure—and builds a focused FHE layer on top of that foundation.

EasyFHE is not a general PyTorch replacement. It is a purpose-built runtime for expressing encrypted tensor programs in Python while keeping the implementation close to the ciphertext layout, RNS levels, key material, rotations, bootstrapping constants, and native CUDA kernels that determine end-to-end FHE performance.

## Why EasyFHE?

### Python at the top, native kernels underneath

Write encrypted tensor programs from Python with `easyfhe.fhe`, then execute the expensive cryptographic work through native ATen/CUDA operators. The public API covers CKKS context construction, encryption/decryption, ciphertext state tracking, plaintext/constant preparation, homomorphic arithmetic, rotations, rescale, alignment, fused operators, and bootstrapping.

### CUDA-first FHE execution

EasyFHE includes GPU kernels for the operations that dominate CKKS runtime cost: encoding, NTT/iNTT, automorphism, key switching, modulus raising/downscaling, ciphertext arithmetic, homomorphic multiplication with relinearization and rescale, rotation, inner products, and fused multiply-accumulate paths.

The current CKKS frontend uses u64 Q primes. One physical prime represents one
level and one rescale removes one prime. Contexts support both the compact
`depth`/`dcrt_bits`/`first_mod` form and an explicit per-prime `limb_specs`
form; paired/composite limb behavior is intentionally outside this API.

### OpenFHE-compatible bootstrapping workflow

The `easyfhe.bs.openfhe` package describes a bootstrap once with
`BootstrapSpec`, derives its context/key requirements, and generates one
context-bound `BootstrapProgram`. Constants, execution plan, raise target, and
output state therefore cannot drift apart at runtime.

### Native CKKS material generation

EasyFHE can generate CKKS client/server material directly through its native path, including public keys, multiplication keys, rotation keys, secret material, CRT parameters, roots, and runtime context material. Applications can generate client and server contexts from one `CKKSContextSpec` and run on CPU or CUDA devices.

### Fused operations for real encrypted programs

Beyond basic add/multiply/rotate, EasyFHE exposes fused and hoisted paths such as `homo_mul_relin_rescale_postop`, `fast_rotate`, `hoisted_mac_sum`, `giant_rotate_sum`, `grouped_pairwise_mac`, and `grouped_scalar_weighted_acc`. These APIs are designed for practical encrypted inference and signal-processing workloads where avoiding unnecessary passes over ciphertexts matters.

### A codebase shaped for FHE, not generic ML

The project is being reduced from a broad PyTorch fork into a compact FHE runtime. The long-term direction is to keep the runtime pieces that make encrypted tensor execution fast and programmable—storage, dispatch, CUDA, Python bindings, profiling, selected NCCL infrastructure, and FHE kernels—while removing model training, optimizers, export, mobile, quantization, and other general ML surfaces.

## Install

Prebuilt wheels currently target Linux x86_64, Python 3.12, and Ubuntu 22.04/24.04. CUDA 12.9 and 13.x wheels are built for `sm_80`, `sm_86`, `sm_89`, `sm_90`, `sm_100`, and `sm_120` with `compute_120` PTX, covering A100 through RTX 5090 class GPUs. Pick the wheel channel that matches your CUDA runtime.

```bash
# CUDA 13.2
python -m pip install "easyfhe==0.1.1+cu132" \
  --find-links https://jizhuoran.github.io/EasyFHE/whl/cu132

# CUDA 13.0
python -m pip install "easyfhe==0.1.1+cu130" \
  --find-links https://jizhuoran.github.io/EasyFHE/whl/cu130

# CUDA 12.9
python -m pip install "easyfhe==0.1.1+cu129" \
  --find-links https://jizhuoran.github.io/EasyFHE/whl/cu129
```

For the latest wheel matrix and release assets, see the [installation page](https://jizhuoran.github.io/EasyFHE/).

## Reference performance

The following end-to-end results were measured with synchronized warmup
excluded. Setup, key generation, encryption, decryption, and correctness checks
are not included in the reported execution time.

| Example | Measured work | A100 80GB PCIe | H100 80GB | RTX 5090 32GB |
|---|---|---:|---:|---:|
| Bootstrap | One full-slot complex bootstrap (`2^15` slots) | 41.726 ms | 31.569 ms | **25.335 ms** |
| ResNet20 AESPA | One encrypted CIFAR-10 inference | 0.866 s | 0.687 s | **0.545 s** |
| THOR | One encrypted 12-layer BERT inference on MRPC | 72.352 s | 55.125 s | **41.337 s** |

The A100 column reports one measured run per application. The H100 Bootstrap
and ResNet20 results average five measured runs, while its THOR result is one
measured run. The RTX 5090 Bootstrap and ResNet20 results average five measured
runs; its THOR result averages three measured runs after two full warmups
(`41.304`, `41.333`, and `41.373` seconds).

The 32GB RTX 5090 is close to the memory limit for the canonical ResNet20
example: peak device memory was 32,066 MiB. It was run with
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to avoid allocator
fragmentation. THOR peaked at 23,646 MiB. The RTX 5090 measurements used the
`cu129` wheel and Triton 3.5.1; Triton 3.7.1 produced `device kernel image is
invalid` with the tested NVIDIA 570.124.06 driver.

These are reference measurements rather than hardware-independent guarantees.
The exact commands and downloadable, version-pinned assets live in the
[EasyFHE examples repository](https://github.com/jizhuoran/easyfhe-examples).

## Quick start

```python
import numpy as np

import easyfhe.fhe as fhe
import easyfhe.bs.openfhe as bs

# 1. Plan the bootstrap before generating keys.
device = "cuda"
log_n = 16
bootstrap_spec = bs.BootstrapSpec(
    log_slots=12,
    level_budget=(3, 3),
    output_levels=6,
    strategy="double_hoist",
    mode="modraise_first",
)
requirements = bs.requirements(
    bootstrap_spec,
    log_n=log_n,
    secret_key_dist="SPARSE_TERNARY",
)

# 2. Generate client material and a server-side runtime context.
client, ctx = fhe.generate_client_context(
    fhe.CKKSContextSpec(
        depth=requirements.context_depth,
        log_n=log_n,
        dnum=3,
        dcrt_bits=58,
        first_mod=60,
        secret_key_dist="SPARSE_TERNARY",
        scale_mode="fixed",
        rescale_policy="manual",
        rotations=requirements.rotations,
        auto_load_keys=True,
    ),
    device=device,
)

# 3. Bind constants and the runtime plan to this context.
bootstrap_program = bs.generate(ctx, bootstrap_spec)

# 4. Encrypt slots and run a small encrypted polynomial.
slots = bootstrap_spec.slots
x = client.encrypt(
    np.full(slots, 0.2, dtype=np.float64),
    slots=slots,
    cur_limbs=6,
)

square = lambda c: fhe.homo_mul_relin_rescale_postop(c, c, ctx)
x2 = square(x)
x4 = square(x2)
x8 = square(x4)
x16 = square(x8)

# Refresh the ciphertext before continuing with deeper computation.
x16 = bs.bootstrap(x16, ctx, bootstrap_program)

x32 = square(x16)
print(client.decrypt(x32)[:8])
```

## Public API surface

Use the package roots for application code:

```python
import easyfhe.fhe as fhe
import easyfhe.bs.openfhe as bs
```

The stable `easyfhe.fhe` surface includes:

- `CKKSContextSpec`, `generate_client_context`, `Client`, `Context`, `Cipher`, and `CipherState`
- `ConstantBundle` for reusable scalar and vector constants
- ciphertext alignment and scale-state helpers such as `align_to`, `normalize_scale`, and `rescale`
- homomorphic add/sub/mul, plaintext/scalar variants, rotations, fused multiply/relinearize/rescale paths, and batch/hoisted helpers
- slot-shape helpers such as `expand_slots`, `fold_slots`, `pack_cipher_batch`, and `unpack_cipher_batch`

The OpenFHE-compatible bootstrapping surface includes:

- `bs.BootstrapSpec(...)` for one reusable bootstrap configuration
- `bs.requirements(...)` for context depth and rotation-key planning
- `bs.generate(...)` for a context-bound `BootstrapProgram`
- `bs.describe_plan(...)` for plan introspection
- `bs.bootstrap(...)` for runtime bootstrapping

## Architecture

```text
Python applications
  ├─ easyfhe.fhe                CKKS frontend, ciphertext state, constants, ops
  ├─ easyfhe.bs.openfhe         bootstrap specifications, planning, programs, runtime
  └─ easyfhe tensor runtime     storage, dispatch, CUDA execution, Python bindings
        └─ ATen native FHE ops  CPU/CUDA kernels and native sampler
```

### Repository map

- `easyfhe/fhe/` — CKKS frontend, context generation, ciphertext/plaintext state, constants, public ops, and native keygen integration.
- `easyfhe/fhe/ops/` — arithmetic, encoding, rotation, key switching, alignment, validation, fused ops, and thin wrappers around native kernels.
- `easyfhe/bs/openfhe/` — OpenFHE-compatible bootstrapping API, parameter requirements, rotation planning, precomputation, constants, plans, and runtime implementations.
- `aten/src/ATen/native/fhe/cuda/` — CUDA kernels for FHE encoding, NTT, automorphism, key switching, modulus movement, arithmetic, rotation, inner products, and fused paths.
- `aten/src/ATen/native/fhe/cpu/` — CPU native implementations and parity paths.
- `aten/src/ATen/native/fhe/sampler/` — native CKKS sampler and key-material generation support.
- `packaging/` and `whl/` — wheel, manylinux, release, and simple-index packaging assets.
- `tests/fhe/` — FHE-focused tests.

## Examples

Reference applications and benchmarks live in a separate examples repository so that the runtime can stay focused:

- [EasyFHE Examples](https://github.com/jizhuoran/easyfhe-examples)
- `benchmark/` — foundational EasyFHE latency benchmark pipeline
- `bootstrap/` — full-slot complex bootstrapping through the public API
- `resnet20_aespa/` — encrypted CIFAR-10 ResNet-20 inference with AESPA
- `thor/` — encrypted 12-layer BERT inference on MRPC

## Design background

EasyFHE follows the framework described in [A Framework for Developing and Optimizing Fully Homomorphic Encryption Programs on GPUs](https://doi.org/10.1145/3779212.3790120). The key idea is to treat FHE programs as tensor programs while still exposing enough low-level runtime structure—ciphertext layout, RNS levels, precomputed material, rotation keys, bootstrapping constants, and fused kernels—to optimize GPU execution end to end.

## Current status

EasyFHE is an alpha research system. APIs, build flags, ciphertext layout, wheel channels, and packaging details may change quickly. Do not treat it as a production cryptographic library without independent security and correctness review.

## Roadmap

EasyFHE is moving toward a more configurable and model-aware FHE runtime. Planned directions include:

- **Heterogeneous RNS limb sizes.** Support CKKS parameter sets where different RNS limbs may use different bit widths, instead of assuming a uniform limb size across the chain. This will make the runtime more flexible for memory, precision, and bootstrapping trade-offs.
- **Memory-aware configuration and customizable encoding.** Add support for memory-aware configuration generation and encoding customization inspired by **MACH: Memory-Aware Configuration Generation for Homomorphically Encrypted Neural Networks**. The goal is to let users tune encoding choices for specific encrypted neural-network workloads.
- **Key-size minimization.** Provide tools and planning APIs that minimize evaluation-key footprint.
- **Input-aware EvalMod customization.** Support input-distribution-aware bootstrapping, especially customized EvalMod approximations whose approximation interval, degree, and error objective are selected based on the expected ciphertext value range.

## Contributors

EasyFHE is an open research codebase for the FHE and systems community. We welcome contributions of all kinds, including bug reports, documentation improvements, benchmarks, CUDA kernel optimizations, new CKKS operators, and bootstrapping experiments. If you are building on EasyFHE or have ideas for improving it, please open an issue, start a discussion, or submit a pull request.

## License

EasyFHE is distributed under the GPL-3.0 license. It is derived from PyTorch and retains portions of the PyTorch runtime; see the repository license files and retained third-party notices for upstream license information.
