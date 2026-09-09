# C79 FLUX2 Klein VAE decoder execution graph candidate

This independent candidate extends the existing VAE ledger; it does not claim the shared project lacked VAE convolutions. `image_stages.vae_stage` already covers decoder convolution and attention matrices, and `image_execution` supplies nonmatrix arithmetic. This candidate agrees exactly with that matrix subtotal and adds source-ordered operators, all decoder weight/bias/GroupNorm affine parameters, explicit activation interfaces and caller-frame lifetime accounting. Do not add its FLOPs to the existing VAE subtotal: replace or reconcile that stage when integrating. C79 as a whole remains open.

## Fixed evidence and scope

`input-bindings.json` binds the actual config, six implementation originals and candidate inputs. Implementation revision is diffusers `040c7cde626504d14caf63b13b8b25b6a9f62120`, already in `configs/image-generation.lock.json`. Implementations are `autoencoder_kl_flux2.py`, `vae.py`, `unet_2d_blocks.py`, `resnet.py`, `upsampling.py`, and `attention_processor.py`. Exact URLs, SHA256, revision and config provenance appear in every result. No new weights were downloaded, and checkpoint-header validation is not claimed.

The selected path consumes already BN-denormalized, unpatchified `[B,32,H/8,W/8]` latent and produces `[B,3,H,W]` RGB. It excludes DiT, encoder, latent unpacking/BN inversion, output image postprocessing and file encoding. It assumes inference, no slicing/tiling/checkpointing/offload, and PyTorch >=2.1 nearest-neighbor behavior. BF16 and FP32 are explicit runtime operands; config `force_upcast=true` is not treated as an executed conversion. Spatial dimensions must be multiples of eight.

The decoder enumerates 49,620,259 parameters including convolution/linear biases and GN affine weights: 99,240,518 BF16 bytes or 198,481,036 FP32 bytes. These are post-quantization convolution plus decoder weights, not the entire autoencoder. There are 40 convolution/linear projections, 14 residual blocks, 30 GroupNorm operations, 29 SiLU operations, 15 residual additions and source-preserved divisions by one, three nearest-neighbor upsampling operations and one full, noncausal, single-head mid-block attention.

## Accounting semantics

Convolution reports both dense padded multiply-add work and valid nonpadding work. Bias additions are scalar operations. GroupNorm uses a declared two-pass population-variance mathematical algorithm: 7E+G arithmetic operations plus G reciprocal square roots for E elements and G normalization groups, including affine multiplication/addition. Backend reduction ordering and primitive workspace remain unspecified. Special functions are recorded separately.

SDPA reports QK/PV and stable-softmax reference arithmetic without inferring a materialized N-by-N score tensor. Eager attention explicitly records beta-zero baddbmm scratch, scores, FP32 softmax intermediates and the probability cast. The fixed source explicitly deletes scratch immediately after QK and deletes scores immediately after softmax; both release points have regression checks. Same-dtype FP32 conversions alias rather than allocate.

Operator read/write bytes are tensor-boundary interfaces, not HBM traffic. The lifetime graph allocates each named result before retiring its consumed inputs and retains references held by source callers and locals. It includes post-quantization latent, residual roots/branches, attention locals and up-block caller inputs. The returned named-boundary peak excludes primitive internals, allocator alignment, implicit layout copies and unmodeled backend workspace; `actual_runtime_peak_bytes` is always null.

Large batch/spatial inputs remain accepted. Every upsample reports the input elements/bytes and whether the fixed source's `batch>=64` or `input.numel()*2>2**31` contiguous branch triggers. Triggered `materialized_copy_bytes` is null because strides are unspecified. Such scenarios set `layout_copy_bytes_unknown=true` and disable the conditional budget. Otherwise an explicitly supplied workspace yields `weights + named boundary peak + supplied workspace`; this is a conditional accounting sum, never a measured runtime peak or a guarantee that the workspace is sufficient. Decoder persistent request cache is zero, and final caller-retained latent plus RGB is explicit.

## API and reproducibility

`calculate(height=1024, width=1024, batch=1, dtype='bf16', attention='sdpa', workspace_bytes=None)` returns replayable `scenario`, sources, weight rows, operator rows, tensor identities/lifetimes, frame holds, event timeline, summary and scope. `calculate(**result['scenario'])` is tested exactly. Transfer the module to a public topic without changing PROJECT/provenance paths; transfer tests with their import updated. A dedicated command can preserve these explicit decoder inputs. Parent owns CLI, report, reproduction and outline edits.

Run:

```sh
PYTHONPATH=calculations/src python -m unittest discover -s calculations/research/flux-vae-decode -p 'test_*.py'
python calculations/research/flux-vae-decode/run_scenarios.py
```

Twelve tests pass: legacy matrix equality, independent parameter formula, DAG ordering and final live set, independently enumerated interval peaks, eager explicit release points, dtype/cast behavior, batch/workspace scaling, tiny convolution padding and nearest copying, numerical biased-variance GN, large-shape layout unknown interfaces, scenario replay and invalid inputs. Independent review in `research/flux-vae-independent` additionally checks sixteen shapes/dtypes/processors using independent formulas; its final layout-delta review confirms the latest large-shape interface change. A subsequent report-only markdown function does not alter calculate results. Public-ready files are in public/src/infra_calc/topics and public/tests; markdown(result) is the dedicated renderer, with example.md showing every operator and lifetime.

## Representative results

All counts below are integer arithmetic/bytes, not runtime estimates.

| Scenario | Dense matrix/conv FLOPs | Valid nonpadding FLOPs | Named boundary peak bytes |
|---|---:|---:|---:|
| 1024² B1 BF16 SDPA | 10,474,653,483,008 | 10,442,021,800,960 | 1,612,709,888 |
| 1024² B1 BF16 eager | 10,474,653,483,008 | 10,442,021,800,960 | 2,250,244,096 |
| 512×768 B2 BF16 SDPA | 7,598,292,074,496 | 7,557,534,717,952 | 1,209,532,416 |
| 512² B1 FP32 eager | 2,515,584,155,648 | 2,499,289,811,968 | 806,354,944 |

Default scalar arithmetic is 19,448,447,936; boundary reads/writes are 17,534,287,872 / 15,593,373,696 bytes. The rectangular example supplies 536,870,912 workspace bytes and therefore yields a conditional sum of 1,845,643,846 bytes. Default SDPA peak occurs at `up3.residual0.silu1`; default eager peak occurs at `mid.attention.softmax`. Reports should show named graph demand alongside unknown primitive/layout demand and must not present any of these as observed HBM traffic or runtime capacity.
