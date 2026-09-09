# CPU offload correction-bias alias compatibility

This is an explicit private runtime adaptation, not an unmodified SGLang result.
It changes a temporary Python reference, never parameter values, routing math,
model layers, model files, or the shared environment.

The installed SGLang sources copied into `sources/` show the alias chain:

- `deepseek_v2.py:437` registers `gate.e_score_correction_bias` as a Parameter;
  line 641 passes it to TopK. Lines 654–667 select V4's ungrouped
  `sqrtsoftplus` configuration.
- `topk.py:406–415` stores that Parameter in a regular dataclass field,
  `TopKConfig.correction_bias`; line 1580 reads it for routing.
- `../prepared/sources/sglang/srt/utils/offloader.py:133–147` copies the state
  tensors to the execution device and calls `torch.func.functional_call`.
  This temporarily replaces registered parameters but does not traverse the
  dataclass alias. Its bias still references the original CPU Parameter.

`offload_alias.py` wraps only the offloader module's imported `functional_call`.
For actual SGLang TopK objects it resolves the alias by registered parameter
identity and temporarily points it at the existing corresponding state tensor.
A `finally` restores the old alias, including when the underlying call raises.
No additional H2D copy is introduced. Unexpected identity, state key, dtype,
or shape fails closed. The ordinary offloader itself does not restore its
forward wrapper after a failed forward; this adapter does not repair or hide
that separate behavior, and experiments must discard a failed instance.

Run `install()` in each model-worker process before its first forward.
The run launcher should import it at module top level when its private run
token is present, including Python's spawned `__mp_main__` import. Set
`V4_FULL_COMPAT_LOG_DIR` to a fresh run-local directory: one installed record
per PID captures adapter and offloader SHA-256; the first binding records its
state key, dtype, shape and devices without parameter contents. Subsequent
bindings do not write logs. Do not share one model instance across concurrent
threads: the native functional-call offloader also mutates module state.

`check_cpu.py` passed with local Torch 2.14.0. It uses a deliberately minimal
TopK-shaped module, not SGLang CUDA dispatch. Equal copied values remain exact;
distinct replacement values expose the stale alias in the unadapted call and
are used correctly by the adapter. Parameter and alias identities restore
after both success and deliberate exceptions; original values remain exact.
See `cpu-check.json`.

`check_gpu.py` is a root-scheduled small CUDA control. It uses the actual
OffloaderV1 and official `biased_topk_jit_kernel_impl`, with four/eight tokens,
256 generated float32 biases, top-k 6, sqrtsoftplus, normalization and scale
1.5 from the frozen model config. Both placements of routed scaling are
checked. The actual TopK class is used as configuration holder; the test calls
the official biased kernel directly, so it does not validate full TopK
distributed dispatch. The unadapted CPU/device mismatch is an intentional
negative control. Adapted output IDs and weights must exactly match the
GPU-resident reference, with success/error restoration checks. There are no
real model payloads, Engine, or requests. PyTorch allocator fraction is 0.009
and peak reserved memory must be below 1 GiB; CUDA driver/context overhead is
outside this allocator measurement. Run using the full run's working CUDA
13.0 include paths and private JIT cache:

```sh
python check_gpu.py --config ../prepared/metadata/config.json --out gpu-check.json
```

The GPU control is executed by the root scheduler; a prepared script alone
does not establish success. Even a passing control establishes only this
alias repair, not complete model correctness or retrieval quality.

## Root实际GPU执行

GPU小对照已由root在SG0.5.13私有环境实际执行并正常退出：4/8 tokens × 两种缩放位置共4组，原GPU参考与适配后的ID/weight逐位相同，成功及故意异常后alias恢复。PyTorch峰reserved为2097152bytes，不含CUDA context，见gpu-proof/gpu-check.json和对应首次绑定/安装记录。完整模型验证另行执行。
