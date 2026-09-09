# 5-8 FlashInfer plan／元数据／run：运行前协议

本文件记录运行前设计。后续实际执行结果见README；新独立子实验，原 5-8 封存件保持不变。

目的：检验实际同规格 36 层 attention 是否能复用计划，分别观察主机 plan、隐式复制、run 与完整时间。不给定预期速度或通过结论，不重复 calculations 的逐层算术和摊销模型。

## 固定条件

- FlashInfer 安装源码随 sources 保存；执行前核对安装 decode.py SHA256 必须相同。现有 RTX 专用环境为 SGLang 0.5.13.post1／Torch 2.11 CUDA 13，运行时保存实际 FlashInfer 版本。
- Qwen3-8B 的代表 GQA 规格：36 层、32 Q heads、8 KV heads、head_dim 128、BF16、page_size 16，batch 2。两组长度为 [128,256]、[1024,2048]。
- 固定 seed 508 的各层独立随机 Q/K/V；不是真实模型激活，也不是逐层 hidden-state 依赖链。没有权重加载和语言任务质量结论。
- BatchDecodeWithPagedKVCacheWrapper，NHD，use_tensor_cores=False，PDL 关闭。使用 graph-compatible 固定元数据缓冲，但不捕获 CUDA Graph。此 API 的 CUDA-core backend 是否在本机运行成功须由实际运行证明。
- 同一 wrapper、同一 36 层输入和预分配输出：plan_per_layer 每层 plan 后 run；reuse_plan 一次 plan 后 36 次 run。每种预热两次，再每形状七轮随机交错，共 28 组正式工作量；各组都有 36 个 run。

## 时间与复制边界

正式组前同步，组内不逐层同步。保存每次 plan/run 的主机调用时间之和、组完成墙钟和 stream event span。stream span 包含主机提交间隙，不称纯 GPU kernel 时间；plan 包含 Python 工作、隐式 metadata copy 和 native planner，不称纯 CPU 规划。

正式脚本的 Python 循环、计时调用和事件记录也在完整窗口中，不能当零开销；不报告去掉该开销的估计值。per-layer 分支确实增加 API 调用，也增加相应的计时调用，微小差距应保留测量边界。

另行使用 Torch profiler CPU/CUDA trace：plan/i 与 run/i 范围、CUPTI memcpy 和 kernel 原件全部保留。formal_workload 的主机范围结束后仍需同步，不能把范围结束当作设备完成。插桩轨迹的时间不并入正式样本。不 monkeypatch 复制函数或 native planner，不把一次观察到的 copy 归为全部 planner 传输。

再单独运行同一 pinned CPU 元数据到固定 GPU 缓冲的显式 copy control，每组 36×3 次 copy。payload 只计三份输入元数据，不能覆盖 native planner 私有元数据，也不能把 copy control 时间从 plan 时间直接相减得到“纯规划”。

## 正确性与状态变更

独立 FP32 显式 GQA：读取页表展开 K/V，按 GQA 重复 heads，再算 QK、softmax、V；禁用 TF32，不调用 FlashInfer/SDPA 参考。所有 36 层按 atol 0.005、rtol 0.02 检查，各策略每个正式样本检查。另保存逐位一致与否，不将容差通过称作逐位相同。正式失败立即保留已写记录并退出，不放宽阈值。

单独构造全零 Q/K 和末页第 2–16 token 的 V=8。将每个请求末页有效长度从 16 改为 1（页数不变）：只建立新 CPU metadata 而不调用 plan，旧 wrapper 应继续使用旧长度；重新 plan 后应与新长度显式参考相同；恢复旧 plan 后应恢复旧输出。保存完整张量，要求旧结果不满足新参考、新 plan 满足参考、恢复输出与旧输出逐位相同。这验证输入绑定与 replan 必要性，不是安全故障注入，也不把输入对象改变当作自动更新。

## 原始产物及执行控制

results 目录已存在则拒绝覆盖。保存源码哈希、实际版本、初始化时间、两套完整输入／参考／初始输出、每组计时和检查、四份 trace、两套 metadata-change 张量、显式 copy 样本及终止标志。启动/JIT 时间单列，不纳入热态性能。仅自身进程正常退出；不停止原服务，不与另一个 GPU 测量并发。

仅准备时可执行 `python3 -m py_compile run.py analyze.py`，不导入 GPU 库、不访问 CUDA。

RTX 获得空闲测量窗口后，在此目录运行：

    sh launch.sh --output results
    python3 analyze.py

最终 launch.sh 指定独立 flashinfer-cuda130 目录，nvcc/crt/nvvm13.0.88、runtime13.0.96。数值阈值和运行逻辑不变；安装日志、工具及 header 哈希见 toolchain.json。正式执行在其他 GPU 测量完成后开始。
