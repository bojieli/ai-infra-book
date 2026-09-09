# V4 原生四层加载、卸载与前向兼容性

**最终配置已完成两次原生请求，进程正常退出 0。** 使用已有真实 checkpoint 和未修改 SGLang Engine，经官方 CPU OffloaderV1 路径，256／512 个输入各生成 4 个 token。保留最终成功运行及两次成功独立编译预检；这只是截取四层的运行兼容性检查，**不是完整 V4 推理、检索质量、数值参考验收或性能基准**。真实六专家原 FP64 门槛的失败及其阶段定位仍分别见 [expert-preflight](../expert-preflight/README.md)、[expert-stages](../expert-stages/README.md)，不因本次返回输出而改成通过。

## 固定模型与运行范围

- 原权重：缓存 `DeepSeek-V4-Flash-0731` revision `7872f01b1d1fe23eabc4c98b48bffcef5a386062`，48 个分片。未下载或修改 checkpoint。
- 通过公开 `json_model_override_args` 设置前四层、`compress_ratios=[0,0,4,128]`，包含三种注意力压缩路径。截断改变了模型架构，输出没有原完整模型的语义质量含义。
- 原 loader 将整个 checkpoint 迭代对象收集为列表、反量化 WO-A，并跳过层范围外的参数。日志记录读取全部48分片，不能称为只读取四层文件；通过加载不代表重新做全部载荷 SHA。
- 指定私有环境：SGLang 0.5.13.post1、Torch 2.11.0+cu130；RTX PRO 6000 Blackwell/SM120。原生 backend 为 dsv4/marlin（SM120 专家桥实际采用原 Triton 路径）。自动关闭 SM120 不支持的 WO-A、mHC 特化等参数的证据在相邻 [runtime-preflight](../runtime-preflight/README.md)。
- 最终设置：CPU offload 8GiB、context1024、token pool2048、chunk256、max_running_requests1；禁用 CUDA graph 和 radix cache。`mem_fraction_static=.9`、`swa_full_tokens_ratio=1.0`。后者确保小 token pool 按 page256 对齐后仍有非零 SWA 池；静态比例用于框架缓存预算，不能解释为实测占整卡90%。两次输入为合法普通 token IDs `[1000,1001,1002,1003]` 重复至256／512，greedy、ignore_eos、强制4个输出；不存在检索题或正确答案。

## 实际结果与资源

最终原始文件在 [attempt-05/results](attempt-05/results/)，完整日志见 [run.log](attempt-05/run.log)。远端执行会话33025 exit0，结果传输15801 exit0，均结束后才分析。

| 项目 | 实测 |
|---|---:|
| 原生 Engine ready | 123.590 s |
| 请求输入 / 输出 token | 256 / 4；512 / 4 |
| 完整请求墙钟 | 133.661 s；3.394 s |
| full / SWA token pool | 2048 / 2048 |
| c4 / c128 pool | 512 / 16 |
| c4 / c128 state pool | 128 / 2048 |
| 进程 GPU 采样峰值 | 14310 MiB |
| 进程 session RSS 采样峰值 | 21842706432 bytes（约20.34 GiB） |
| 主进程退出 / 监控终止原因 | 0 / null |

两个请求均返回 `[47380,126248,64432,85304]`，`finish_reason=length`、completion_tokens4、cached_tokens0。原始文本也保存，是截断模型对合成输入的输出，不能当质量通过。首次请求包含大量按需编译，第二次是不同输入长度，且 GPU/CPU 共享；两次时延不构成暖态加速或模型性能对照。环境日志中的默认 FP8 KV scaling、缺少特定设备调优配置等提示全部保留，未隐藏或据此修改精度。

[analyze.py](analyze.py)核对固定四层配置、完整输入、输出 token 数、生命周期和采样边界，单独写 [analysis.json](analysis.json)。`truncated_runtime_probe_complete=true` 仅表示最终有界检查完成；`full_model_or_quality_pass=false` 明确保留。

## 编译环境修复

私有 CUDA13.0 根是 `tools/flashinfer-cuda130/nvidia/cu13`。它缺少此次 JIT 所需 CCCL include 组织；复用现有SG环境的 `nvidia/cu13/include/cccl`，没有安装依赖或更改共享框架。

[jit_preflight.py](jit_preflight.py)调用原 `_jit_compress_plan_module()`，会话40334 exit0、35584传输exit0；原生生成代码、ninja、库和SHA在 [jit-preflight/result.json](jit-preflight/result.json)。[jit_mhc_preflight.py](jit_mhc_preflight.py)调用原 `hc_split_sinkhorn_kernel(4,20,1e-6)`，7450 exit0、82226传输exit0，产物在 [jit-mhc-preflight/result.json](jit-mhc-preflight/result.json)。这两项只验证编译，不是独立数值测试。

最终 CPATH为私有`include-overlay`和CCCL目录；overlay内仅有指向既有CCCL的链接，避免把另版CUDA runtime头一起加入路径。TVM FFI、TileLang、Triton及CUDA缓存转入新尝试目录。成功运行使用两个预检的编译缓存，其他需要的内核按原框架编译。复现入口会将这两个成功预检缓存复制到新运行的私有缓存目录。

## 独立复现与安全退出

在具有原权重和指定环境的RTX主机上，从本目录执行：

```sh
/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python -B reproduce.py --name new-run
```

[reproduce.py](reproduce.py)使用最终原脚本创建全新目录，设置仅含CCCL的include overlay；已有目录会拒绝，不删除旧结果。模型/工具链是明确的外部依赖，不复制166GB checkpoint。只做离线复核可运行 `python3 analyze.py`；它不会启动任何GPU/相邻实验。

每次自身session限制CPU4核（4–7）、库线程4，GPU采样上限24GiB、RSS上限50GiB、系统可用主存下限24GiB、12分钟期限；启动需28GiB空闲GPU。1秒轮询加命令开销不是瞬时硬限额。守护仅终止自己创建的session，既有五个GPU服务全部保留；本次没有为显存停止既有任务，没有操作其他CPU计算进程。

源快照和SHA在 [source-hashes.json](source-hashes.json)，[401个成功运行与预检原始文件传输清单](raw-transfer-manifest.json)已逐一核验本地/远端SHA相同；[最终GPU快照](postflight.txt)仍只有原五服务。[manifest.json](manifest.json)封存本地交付。完整V4/K3、真实router/激活分布、长上下文、检索/前缀质量和完整offload对照仍未完成。
