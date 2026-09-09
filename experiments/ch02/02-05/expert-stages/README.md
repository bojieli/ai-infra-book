# V4 六专家 M8 阶段诊断（待主 agent 统一审核）

**原 10/32768 个失败已逐位复现，原 FP64 数值协议仍未通过。** 本次将这 10 个失败定位到实际 SwiGLU 激活存储边界相对原 CPU FP64 参考的新差异，经 GEMV2、路由加权和求和传播至输出。不能将本结论解释为内核全面正确或完整 V4 数值兼容性放行。

没有改变输入、路由、packed 权重、原参考或门槛；没有执行完整模型、原 15 用例、下载模型、改共享源码/环境、运行 calculations、派生 worker、联系 owner 或提交 git。旧 expert-preflight 完全只读。只新增本目录及指定 status。

## 实际观测及复现

运行指定远端 Python `/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python`，Torch 2.11.0+cu130、SG 0.5.13.post1、Triton 3.6.0，RTX PRO 6000 Blackwell / SM120。直接调用安装的原 `mxfp4_moe_forward_triton`，源 SHA 必须与旧快照相同。全部输入来自旧 `results/main_m8.npz` 与 `assembled.npz`；CPU 独立解包来自 `raw_checkpoint.npz`。原始文件位置、大小和 SHA 见 [input_sources.json](results/input_sources.json)，模型选取 payload 的原来源由其中哈希锁定的旧 `selected_tensors.json` 记录。

局部变量生存期已按源码核对：`intermediate`、`activated`、masked `down`、`flat_weights` 在 return 可取；原 GEMV2 `down` 在 mask 后被覆盖，因此 trace 在 mask 语句前复制。product 是表达式临时值，reduce 随后被原地缩放，因此用只观察的 `TorchDispatchMode` 捕获原 `aten.mul.Tensor` 和 `aten.sum.dim_IntList` 的真实输出。每次都先 CUDA synchronize，再同步复制 CPU 数据；不改原函数、内核或 autotune。实际 trace 行号、dispatch 事件见 [observation.json](results/observation.json)。所有 BF16 张量以无损 FP32 值保存，可进行逐位比较。

本批一次观测调用、一次同输入无观测控制均成功退出。观测输出与旧输出 **逐位相同，差异元素 0**；无观测控制也逐位相同。CPU 原 FP64 reference 退出传输后重新解包/计算，first、activated、down、product、reference 均与旧保存参考完全相同。

本次两次 GEMV 实际配置均为 `BLOCK_N=64, BLOCK_K=64, num_warps=4, num_stages=2`，见 [autotune.json](results/autotune.json)。旧实验没有保存 autotune 配置，因此不能声称配置相同；本次未出现输出漂移。日志中的两条 `Failed to get device capability: SM 12.x requires CUDA >= 12.9.` 原样保留；实际设备记录及成功调用见环境/原始结果，未据这条提示修改环境。

## 阶段证据

“原参考差异”指完整原 FP64 参考；“本阶段新增差异”指从 **GPU 实际上一阶段值** 用独立 CPU FP64 算法重算后比较。后者分离已有传播与本阶段新增差异。未调用 GPU 解包/参考内核。BF16 RNE 沿用原 reference.py 的 FP64→FP32→BF16 位运算边界，不悄悄替换参考定义。

| 真实存储边界 | 元素数 | 与原参考不同 | 与实际前阶段的 CPU 重算不同 |
|---|---:|---:|---:|
| GEMV1 | 196608 | 11 | 11 |
| activation | 98304 | 14 | 4 |
| GEMV2 | 196608 | 1253 | 11 |
| masked down | 196608 | 1253 | 0 |
| weighted product | 196608 | 1148 | 0 |
| reduce（缩放前） | 32768 | 302 | 0 |
| 最终输出 | 32768 | 274 | 0 |

进一步以每个实际边界为起点，用原 FP64 后续流程接续到输出。只引入实际 GEMV1 边界时，原 10 个失败坐标的最终误差均为零，完整输出固定门槛失败数也为零；引入实际 activation 边界后，恰好出现原 10 个失败，且各失败坐标的最终数值等于真实 GPU/旧输出。随后引入实际 GEMV2、masked down、product、reduce、最终缩放，在这 10 个坐标均没有进一步改变。这是有顺序的接续对照，不是任意非线性系统唯一的误差分配。

4 个 activation 新差异中，3 个分别通过单坐标 CPU 干预完整重现对应 token 的失败误差，第四个 token 0 的差异不对应旧失败。下表均为零基坐标，专家为 local ID（checkpoint 对应 0,1,7,42,128,255）。

| 激活 token / slot / channel | local expert | 原 FP64 边界 | 实际 GPU 边界 | 对应旧失败 output channel |
|---|---:|---:|---:|---|
| 0 / 1 / 237 | 1 | 0.00022125244140625 | 0.00022029876708984375 | 无 |
| 2 / 3 / 84 | 5 | 0.000110626220703125 | 0.000110149383544921875 | 987, 1440, 3547, 3920 |
| 6 / 4 / 1532 | 4 | -0.0004425048828125 | -0.0004444122314453125 | 2604, 3497, 4041 |
| 7 / 3 / 1930 | 4 | -0.0000553131103515625 | -0.0000550746917724609375 | 2099, 3045, 3185 |

每个失败的六个 slot 的 GEMV2/乘积参考值、实际值、实际前阶段 CPU 重算值、各边界最终误差增量、上游差异 channel 列表见 [failures.json](analysis/failures.json)。单激活坐标干预、gate/up、FP64 舍入前值及关联输出增量见 [activation_discrepancies.json](analysis/activation_discrepancies.json)。所有坐标、带符号误差、门槛和 fail mask 保存于 [element_errors.npz](analysis/element_errors.npz)。

以 token 2/channel 3920 为例：原参考 `3.337860107421875e-6`，实际 `1.9073486328125e-6`，误差 `-1.430511474609375e-6`，原门槛 `2.7844530595072394e-7`。仅将 token 2/slot 3/channel 84 的激活从 CPU 边界改为实际 GPU 边界，然后用 CPU 原算法接续，就产生完全相同的最终误差。

独立 NumPy FP32 激活对照在这 4 个坐标均得到与实际 GPU 相同的 BF16 结果，支持“FP32 激活算术在 BF16 边界产生差异并传播”的解释。这是补充证据，**不替换原 FP64 门槛**。本次没有捕获 SiLU 内部指数/除法的实际 FP32 暂存或 GPU 指令，不能进一步断言具体是 exp、除法、乘法哪个指令造成差异；也未证明所有 FP32 执行实现均相同。GEMV1/2 各 11 个局部差异独立保存 FP64 和/存储值于 [projection_discrepancies.json](analysis/projection_discrepancies.json)；未采集内核 FP32 accumulator，不能把这些差异一概断言为正确舍入，其指令级根因仍未确定。这里的阶段定位仅针对旧 10 个最终失败。

## 原验收、资源与退出

固定要求仍为每元素 `abs(y-ref) <= .02*abs(ref) + .002*RMS(ref)`，relative-L2 ≤ .01，全部有限。实测 relative-L2 `0.0003924070767719118`、最大绝对误差 `1.9073486328125e-6`，**10/32768 失败，pass_criteria=false**。执行 exit 0 与数值通过是两回事。

| 资源 | 实测 |
|---|---:|
| 启动前 GPU 空闲 | 36294 MiB |
| GPU 子进程 PID | 2812495 |
| GPU 采样峰值 | 1038 MiB（限制 3072 MiB） |
| 进程树 RSS 采样峰值 | 1387700224 bytes（约 1.292 GiB，限制 8 GiB） |
| Torch allocated / reserved 峰值 | 364645376 / 381681664 bytes |
| CPU affinity / library threads | 0,1,2,3 / 4 |
| 原始执行退出 | 0，watchdog reason=null |
| 传输退出 | 0，CPU 分析在其后开始 |

[supervisor.json](results/supervisor.json) 有完整采样和退出时间；[memory.json](results/memory.json)、[environment.json](results/environment.json)、[run.log](run.log)、[launch.log](launch.log)、[transfer.json](transfer.json) 保存完整证据。watchdog 约 0.5 秒加命令开销采样，不是瞬时硬配额；allocator 2GiB 限制和15分钟执行期限另设。仅监控/终止自身子会话，未停止其他服务。本地 raw 约 4.65 MiB，总产物低于 30 MiB，低于新增 raw 350 MiB 上限。

## 文件与复算

- [run.py](run.py)：独立 GPU 采集脚本；读取同级旧目录保存输入，不生成数据。
- [launch.py](launch.py)：独立缓存/tmp/日志路径和自身进程 watchdog。
- [PROTOCOL.md](PROTOCOL.md)：本批执行前约束；旧协议 SHA 另存 input_sources。
- [stages.npz](results/stages.npz)、[plain_output.npy](results/plain_output.npy)：实际张量和无观测输出。
- [analyze.py](analyze.py)：CPU standalone 分析入口，仅读取同级旧 reference.py/raw；不导入 Torch/Triton，不写旧目录。
- [cpu_stages.npz](analysis/cpu_stages.npz)：重算原参考、实际前阶段局部参考、各边界接续最终输出。
- [summary.json](analysis/summary.json)：完整阶段指标和最终原协议结果。
- [manifest.json](manifest.json)：本目录所有交付文件 SHA/大小（清单自身除外，另存 manifest.sha256）；旧权重无需复制。

本地复算（先核验原始执行/传输 exit 0，脚本会核验 SHA）：

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4 ../expert-preflight/.venv/bin/python -B analyze.py
```

远端原始执行入口是在新的独立目录中放置 run.py、launch.py、PROTOCOL.md，保留其同级只读 expert-preflight/results，运行指定 Python `-B launch.py`；本批结果应保留，不直接重跑覆盖。所有写入都必须仍处于用户授权目录。这里不执行新的 GPU 复跑。

本批已完成有界阶段定位，等待主 agent 统一审核；不做全书最终跨 session 审计。现有证据不覆盖真实路由/激活分布、全模型或其他算子。
