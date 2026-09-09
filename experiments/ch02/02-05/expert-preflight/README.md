# V4 真实 MXFP4 专家 / SM120 有界数值预检

本批已完成，**预设数值验收未全通过，不能据此为完整 V4 数值兼容性放行**。运行正常退出 0；M1 通过，M8 有 10/32768 个输出元素超过执行前固定的逐元素门槛。所有用例 relative-L2 均低于 1%，但协议要求同时满足逐元素门槛，不能用低 relative-L2 覆盖这些失败。

本实验只读取缓存 revision `7872f01b1d1fe23eabc4c98b48bffcef5a386062` 的 layer 0 真实专家 `[0,1,7,42,128,255]`，映射为 `[0,1,2,3,4,5]`。输入是固定随机种子生成、标准差 0.01 的合成 BF16，路由 ID/权重也是合成规则；没有运行完整模型的 router 或使用真实激活。没有加载完整 V4、下载权重、修改共享框架、运行 calculations、派生 worker 或 git 提交。等待主 agent 统一审核。

## 实验和验收

执行前的 [PROTOCOL.md](PROTOCOL.md) 固定了参考算法、输入、控制和门槛，运行记录保存其 SHA256。逐元素要求为 `abs(output-reference) <= .02*abs(reference) + .002*RMS(reference)`，并要求 relative-L2 ≤ 0.01、结果有限；全零参考要求精确零。未根据结果调整协议。

先用真实权重切片 H128/I64/M1/topk6 做 smoke，输出与 CPU 参考逐位相同，随后才运行完整 H4096/I2048、topk6。主要结果如下；完整 15 用例见 [summary.md](results/summary.md)。

| 用例 | relative-L2 | 最大绝对误差 | 超阈值元素 | 判定 |
|---|---:|---:|---:|---|
| M1 | 0.000289485 | 9.53674e-7 | 0/4096 | 通过 |
| M8 | 0.000392407 | 1.90735e-6 | 10/32768 | 未通过 |
| 六个单专家选择 | 0～0.000443274 | 0～3.81470e-6 | 各 0/32768 | 全通过 |
| padded-slot | 0.000446615 | 1.90735e-6 | 2/32768 | 未通过 |
| 同一 slot 权重置零 | 0.000446615 | 1.90735e-6 | 2/32768 | 未通过 |
| slot 逆序置换 | 0.000392407 | 1.90735e-6 | 10/32768 | 未通过 |
| 不启用 clamp | 0.000392407 | 1.90735e-6 | 10/32768 | 未通过 |
| 强制 clamp=0.005 | 0.000141638 | 2.38419e-7 | 0/32768 | 通过 |

共 5 个用例未通过、34 个超阈值记录；其中置换、关闭 clamp、invalid/零权重对照是相关复现，不能当成 34 个独立故障。M8 示例：零基 token 2/channel 3920，GPU 为 `1.9073486328125e-6`，CPU 为 `3.337860107421875e-6`，绝对误差 `1.430511474609375e-6`，门槛 `2.7844530595072394e-7`，约 5.14 倍门槛。小幅输出处会放大舍入/相消影响；原 GEMV 为 FP32 累积，参考为 FP64，可能在 BF16 边界产生差异。**本次没有采集 GPU 内部中间张量，尚不能定位具体阶段，也不能仅凭这种可能性断言内核无缺陷。**

所有精确控制通过：全零路由输出精确零；invalid ID=-1 与同 slot 置零权重输出逐位相同；同时逆序 ID/权重与原 M8 输出逐位相同；profiler 调用与原 M8 输出逐位相同；OffloaderV1 包装前后输出逐位相同。强制 clamp 用例确实覆盖 gate 上界、up 两侧：分别有 36559、37267、37239 个越界值；另有 37729 个低于负界的 gate，按原语义不作下界裁剪。

## 权重、尺度与独立参考

36 个真实 checkpoint 张量均从 index 指向的 `model-00002-of-00048.safetensors` 精确 offset 读取，保存每个 key、shape、dtype、offset、header SHA、raw payload SHA；不代表验证了全部 shard/full-checkpoint payload SHA。

- w1/w3 原生 I8 `[2048,2048]`，w2 I8 `[4096,1024]`，每字节 low nibble 为偶数 K、high nibble 为奇数 K。
- w1/w3 scale 原生 F8_E8M0 `[2048,128]`，w2 scale `[4096,64]`，连续 K 方向每 32 个值共用一个 scale。所有选取 scale 字节范围 119～122，即实际尺度 2^-8～2^-5；没有 byte255 NaN。
- CPU 组装 `[w1;w3]` 沿输出行拼接，专家维按上述顺序堆叠；不 transpose、不 swizzle、不取倒数、不 Marlin repack。最终 packed w13 `[6,4096,2048]`、w2 `[6,4096,1024]`；FP32 scale 分别 `[6,4096,128]`、`[6,4096,64]`。详细 stride/dtype/hash 在 [layout.json](results/layout.json)。
- 被测输入尺度由真实 E8M0 dtype 经 Torch 原生转换为 FP32；逐元素与 CPU 显式 `2**(byte-127)` 表检查相等。退出后又从 raw 文件独立重组并逐位核验保存的所有 assembled 张量，排除把指数 byte 数值直接当尺度等布局误用。

[reference.py](reference.py) 不导入 Torch/Triton：E2M1 显式 16 值表、E8M0 标量表、CPU FP64 反量化/矩阵计算、独立 BF16 RNE 位运算、独立上界 gate clamp/对称 up clamp/SwiGLU/路由加权与 reduce。按原函数的投影1、激活、投影2、BF16 路由权重与乘积、reduce 输出、最终 1.5 缩放存储边界舍入。原函数 SiLU 在 FP32 计算；参考在 FP64 计算后按边界舍入，差异纳入既定门槛。

远端保存了全部输入、路由、最终输出和 CPU 参考阶段（first/activated/down/product）。运行退出、原始数据传输完成后，本地再次从真实 packed 文件计算全部参考阶段，15 用例每个阶段均与远端保存值逐位相同。所有输出元素的带符号误差、容差和失败 mask 在 [all_element_errors.npz](results/all_element_errors.npz)；逐个失败坐标、数值与超阈倍数在 [failures.json](results/failures.json)。

## 原函数、offload 和资源证据

实际调用安装环境的 `sglang.srt.layers.moe.fused_moe_triton.mxfp4_moe_sm120_triton.mxfp4_moe_forward_triton`，未改动函数。完整源码快照包括该文件、Marlin bridge、FusedMoE loader、V4 model loader 与官方 offloader，见 [source_hashes.json](results/source_hashes.json) / [sources/](results/sources/)。SM120 bridge 跳过 repack，使用 `[w1;w3]`，clamp=10、routed factor=1.5 来自保存的 checkpoint config。

一次独立 Torch profiler 的 [profile.json](results/profile.json) 中出现 **2 次 `_mxfp4_slot_gemv_kernel`**，以及原生 SiLU、clamp、BF16 multiply、sum 等实际 kernel；[kernel_events.json](results/kernel_events.json) 保存完整名字和计数。该轨迹用于确认执行路径，没有性能排名。`cases.json` 的 elapsed 字段包含同步和 CPU 参考，不能解释成推理延迟。

官方 `OffloaderV1(cpu_offload_max_bytes=512 MiB)` 包装四参数小层；四参数共 94371840 bytes（90 MiB），全部移入 pinned CPU，调用时由原包装的 `functional_call` 搬到 GPU，调用后参数仍在 CPU。该小层 forward 直接调用上述原函数，没有替换成自制引擎。[offloader.json](results/offloader.json) 与输出文件证明本次包装成功且输出逐位一致；这不证明完整 V4 的层包装、权重加载或 offload 调度正确。

| 资源/环境 | 实测 |
|---|---|
| GPU | RTX PRO 6000 Blackwell，SM120 |
| 启动前余量 | 36294 MiB，≥4096 MiB |
| Python | 指定 sglang0513-venv/bin/python，3.10.12 |
| Torch / CUDA / SG / Triton | 2.11.0+cu130 / 13.0 / 0.5.13.post1 / 3.6.0 |
| 单 GPU 进程 | PID 2724667，运行 exit 0 |
| CPU | affinity 0～3，Torch/library threads 4 |
| sampled GPU peak | 1050 MiB，<3072 MiB |
| Torch allocated / reserved peak | 346.22 / 364 MiB |
| sampled 进程树 RSS peak | 1640910848 bytes，约 1.53 GiB，<8 GiB |

[supervisor.json](results/supervisor.json) 保存每次监控采样和运行/退出时间；[run.log](run.log)、[environment.json](results/environment.json)、[memory.json](results/memory.json) 保存运行证据。GPU/RSS watchdog 每轮约 0.5 秒再加命令开销，属于采样上界检查而非瞬时硬配额；Torch allocator 另设 2 GiB 上限。未停止其他进程。原始及分析结果约 250 MiB，整个本地目录（含独立 NumPy 环境/cache）低于 500 MiB。

## 复算入口和范围

远端重跑会写当前 results，应由审核者自行决定是否另存旧产物。所需模型与环境均已存在；不需要下载模型或修改环境。执行目录为远端 `/home/ubuntu/ai-infra-book-experiments/ch02/02-05/expert-preflight/`：

```sh
/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python -B launch.py
```

本地已提供独立 NumPy 环境，可在本目录执行：

```sh
.venv/bin/python -B analyze.py --recompute
```

`analyze.py` 的 exit 0 表示报告生成成功；**数值门槛由 `results/analysis.json` 的 `all_numerical_cases_pass` 判定，本批为 false**。重算无需 GPU、无需访问缓存模型，唯一权重输入为已保存 packed 文件。源脚本、协议与结果清单见 `artifact_hashes.json`。

本批未完成完整 V4 推理、真实 router/激活、检索质量、attention/其他算子、所有专家/所有层、端到端框架加载验证。没有给出性能结论或跨 session 最终审计。采用数值表和逐元素机器可读证据，无额外图形，因此无独立图像 QA 项。主 agent 应将本结论作为**真实六专家路径可执行、路由/offload 精确控制通过，但既定逐元素数值门槛存在失败**的有界证据。
