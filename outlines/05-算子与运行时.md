# 第 5 章 算子与运行时

> 写作大纲 · 因果推导与教材体例修订 · 2026-09-10

以 Qwen3-8B 单支 FFN 投影为主线，依次引入两支激活链、注意力归约、编译与运行时，最后分析完整请求。开篇只保留理解当前问题所需的形状；新对象在相应机制出现时引入。

**本章方法：** 从重复工作、数据复用和完成顺序解释性能。主要例题按设定、推导、条件变化、设计判断展开；条件在推导前给出，正文段末用于解释结论，不追加自我辩护或范围提醒。版本、完整数值与实验执行要求放注释和配套资料。

**体例：** 六节、22 个小节、12 道带解例题、九幅图。九项原编号实验集中到章末，按复算、敏感性、设计与实测解释逐步加深。核心实验仍为 5-2、5-8、5-9。AKG 使用循环与依赖的直观方式解释多面体编译。

## 5.1 一次设备执行：提交、搬运与同步

从输入和输出均在 CPU 的矩阵乘建立执行链。CPU 与 GPU 各自推进，复制、计算和结果使用由完成关系连接。

### 5.1.1 从框架调用到 kernel launch

解释框架分派、kernel 与 launch，简述线程块和 grid；用主机生产任务、设备消费任务理解小算子的提交等待。

### 5.1.2 数据在哪里：H2D、D2H 与 D2D

区分 H2D、D2H、D2D 与设备常驻数据。例 5-1 用 64 MiB／24 GiB/s 推出 2.6 ms，再将输入二分，引出提前到达与重叠。锁页内存解释中转复制的来源。

### 5.1.3 stream、event 与完成顺序

从同流顺序走到跨流 event，再按最后使用者推导四种缓冲的复用时刻，为双缓冲建立依赖基础。

### 5.1.4 从提交时间到结果可用时间

例 5-2 先设定完整时间线，求提交 3 μs、kernel 20 μs、结果可用 35 μs；kernel 缩至 5 μs 后总时间为 20 μs。解释 CPU 时钟、event 与 profiler 的观察位置，最后引出首次准备的摊销。

## 5.2 单算子：分块、布局与实际访存

固定一支 FFN 投影，解释重复访问、局部存储与并行执行的关系。

### 5.2.1 矩阵形状与重复读取

先推导约 103 GFLOPs 与 128 MiB，再从 i-j-k 循环找到 A/W 重读。交换循环改善连续性，同时改变累加器保存范围，由此引出分块。计数沿工作缓冲、下一层、L2 和显存逐级解释。

### 5.2.2 容量约束下的分块复用

例 5-3 从三份活动数组推导容量与访问。完整展开 64×64 的 3096 MiB 和 128×128 的 1560 MiB。用 T=V/B 推出约一半有效带宽的翻转门槛，再由 96 KiB 预算解释并行度。图 5-1 只画容量与重读。

### 5.2.3 布局与归约的并行代价

bank padding 说明相同请求怎样并行服务。RMSNorm 从一行归约拆成局部和、合并、应用三阶段，解释并行组数、输入重读和寄存器状态。24 MiB 基线由输入、逐行 gamma 读取、输出组成，拆分后为 32.1 MiB。

## 5.3 算子链：融合、缓冲与流水

将局部复用扩展到相邻算子的交接，逐元素链、流水和归约链依次增加条件。

### 5.3.1 中间张量与融合边界

此处才引入 FFN 两支投影和完整激活链。例 5-4 推导 120→72 MiB 与约 1.7 倍带宽模型预期，再加固定尺度转换，得到 156／108／60 MiB。图区分每个物化边界产生的 48 MiB；峰值容量由生命周期单独推导。

### 5.3.2 布局交接、缓冲寿命与双缓冲

先解释独立重排与改变生产布局，再用例 5-5 逐时刻推进四块双缓冲。20→14 μs 后推导 n 块流水公式，解释第三个槽为何不再提速，容量不足如何产生背压。

### 5.3.3 FlashAttention：分块与在线 Softmax

把注意力作为归约扩展案例。先比较 8 MiB 输入输出与 1 GiB 中间访问，再从指数基准推导 m、l、u 更新。例 5-6 验算两个元素；然后逐项解释 128 KiB 状态预算、Q 行数、K/V 扫描与块对更新。FA2／FA3 随其改善的执行机制出现。

## 5.4 编译器：表达、变换与选择

按候选表达、循环变换、依赖与舍入、AKG、多面体调度与成本选择的顺序展开。

### 5.4.1 从一个实现到一组候选

用三算子四种划分、十算子 512 种划分提出组合选择问题。建立表达、合法性、成本三个步骤。

### 5.4.2 用循环变换表达分块与融合

沿同一 FFN 矩阵接激活，以 Halide／TVM 风格依次解释 split、tile、reorder、缓存和计算位置。伪代码缩进与图 5-4 共同展示输入块在 ko 内替换、累加器跨 ko 保留、激活在 ko 后执行。解释 compute_at 的复用／重算交换。

### 5.4.3 依赖与舍入怎样限制变换

先用正负部分和解释激活的归约依赖，再从在线 Softmax 说明足够状态。保留 BF16 cast；例 5-7 逐项推导 FP8 整行尺度与前缀尺度的 55/56、1 差异。

### 5.4.4 AKG：用多面体编译组织循环与存储

明确 AKG 核心 polyhedral compilation：规则迭代、数组访问与依赖形成可分析表示，由调度推导块区域、搬运和寿命。例 5-8 完整推导 444／620 MiB，说明融合位置改变宽输入重读，回扣分块容量。

### 5.4.5 成本估计与实测选择

容量和静态成本筛选候选，硬件测量提供处理率。例 5-9 从 A/B 两种调用频数推导 p>2/3 的选择门槛。Agent 搜索作为候选生成方式，搜索记录放配套，准备摊销接 5.5.3。

## 5.5 运行时：提交、重放与动态形状

把设备程序接回主机准备、图重放、形状复用和任务交接。

### 5.5.1 主机工作怎样进入流水

例 5-10 从 100 段配置／计算推导串行、流水、仅加速设备、同时缩短配置的差别。主机工作减少与隐藏分别解释，自回归依赖提供真实执行入口。

### 5.5.2 CUDA Graph：复用提交与支付边界复制

图 5-6 紧邻三次 FFN 的 launch／kernel 计数。例 5-11 依次比较 2 MiB 与 16 MiB 边界输入，推导 14.3 MiB 门槛和生产者直接写图缓冲的设计。FlashInfer 计划复用作为准备复用的实例。

### 5.5.3 动态形状、分桶与特化摊销

例 5-12 先从真实行数与补齐行数得到每组执行，再加入准备成本。图 5-7 展示 65／90 组交点，70 组与已有缓存是两种条件变化。把调优搜索费纳入相同的复用分析。

### 5.5.4 Persistent Kernel：将交接推进到 tile

从整算子依赖细化到 tile，引入 persistent 任务领取与就绪事件。八块生产／消费的 582→358 μs 推导回扣双缓冲，解释任务管理、并行资源与缓冲回收。

## 5.6 从局部优化到完整请求

先建立占比与关键路径方法，再完整展开请求综合案例。

### 5.6.1 热点占比决定加速空间

推导 Amdahl 关系，从 20% 热点的两倍、十倍与无限加速理解递减收益和优化优先级。

### 5.6.2 并行分支与关键路径切换

用两分支依赖图解释 80→60 μs，指出热点缩至 40 μs 后继续单独优化的收益为零；再加入 90 μs 争用分支解释代价转移。

### 5.6.3 综合案例：一次 Qwen3 请求的优化选择

Qwen3-8B 7239／32 token 请求：先算 36 次 prefill 和 1116 次 decode，再解释阶段时间、1.6% 热点占比、约 1.5 ms 预期节省，最后读 11 对约 1.3 ms 配对收益。由此形成改善当前 TTFT 和研究更长 decode 的两项决定。

## 本章小结与常见误区

按“复用需要空间、交接需要结果或足够状态、节省经过顺序才成为时间收益”归纳。误区复用正文例子，不新增旁支数字。

## 习题与配套实验

保留实验 5-1 至 5-9 的独立编号。分别练习非方形 tile、融合固定开销门槛、在线 Softmax 与预取槽、变换语义、循环寿命、频数与分派、特化交点、图边界复制、完整请求。操作步骤及完整记录继续使用既有 [扩写资料](extensions/05-算子与运行时.md) 与 experiments/ch05。

## 历史与进一步阅读

Halide、TVM、AKG 的表示与调度演进，作者 FPGA／HLS 经历，Korch 编排案例集中于章末，保持主体推导连续。

## 插图安排

| 图 | 所在位置 | 解释关系 |
| --- | --- | --- |
| 5-1 | 5.2.2 | 容量与输入重读 |
| 5-2 | 5.3.1 | 物化边界与中间读写 |
| 5-3 | 5.3.2 | 串行与双缓冲的完成时间 |
| 5-4 | 5.4.2 | 循环层级、缓存寿命与交接位置 |
| 5-5 | 5.4.5 | 调用频数与平均执行时间 |
| 5-6 | 5.5.2 | 主机提交与设备 kernel |
| 5-7 | 5.5.3 | 准备与执行摊销 |
| 5-8 | 5.6.2 | 关键路径切换 |
| 5-9 | 5.6.3 | 完整请求配对差值 |

图号和完整图题仅出现在外部 caption。图注说明输入与计量对象，图内用循环、数据位置、坐标与依赖表达关系。

## 写作资料

- 选读原稿：[StreamTensor](../references/proceedings/MICRO/2025/paper-014.pdf)，仅采用配套笔记所列设计与实验范围。

- 5.3 的流式交接：[顺序、累计生产／消费与缓冲预算](../case-studies/stream-order-and-buffer.md)；StreamTensor 的 FPGA 与 GPU 比较条件见配套阅读记录。

- 5.2–5.3 的容量与复用：[Orojenesis，ISCA 2024 作者公开稿](../references/proceedings/ISCA/2024/public/paper-011-author.pdf)、[Qwen3 分块计数与读取范围](../case-studies/buffer-capacity-and-data-movement.md)。

- 公开考核、Agent 记录与方案审阅：[证据、推算及实验条件](../case-studies/evaluation-and-agent-records.md)。

- 5.5 的图段与拷贝取舍：[GraCE，OSDI 2026](../references/proceedings/OSDI/2026/selected/osdi26-ghosh.pdf)、[vLLM 2024–2026 与 SGLang BCG 的来源](../references/framework-history/2026-09-08/graph-selection/README.md)、[教学时间、padding 和适用条件](../case-studies/graph-execution-tradeoffs.md)。

- 归约与可复现性：[同形状重复、batch 变化和跨引擎的数值对照](../case-studies/rl-state-and-reproducibility.md)，接第 8、10 章的真实推理框架实验。

- 并发下的性能反馈：[NanoFlow 正式会议稿](../references/proceedings/OSDI/2025/selected/osdi25-zhu-kan.pdf)、[切分与争用推算](../case-studies/resource-sharing-and-placement.md)。

- 注意力流水与实际后端：[FlashAttention-4，MLSys 2026](../references/proceedings/MLSys/2026/papers/mlsys2026-ae8b0b5838ba510daff1198474e7b984.pdf)、[固定 CuTeDSL、vLLM／SGLang 路径](../references/framework-history/2026-09-08/attention/README.md)。

- 动态规划与图执行：[FlashInfer，MLSys 2025](../references/proceedings/MLSys/2025/papers/mlsys2025-dbf02b21d77409a2db30e56866a8ab3a.pdf)、[当前 Attention API 快照](../references/framework-history/2026-09-07/flashinfer/attention.html)。历史版本与教学推算见[执行与状态取舍笔记](../case-studies/cache-and-reconfiguration.md)。

- 近两年框架演进：[SGLang Advanced CUDA Graph，2026-08](../references/outline-checks/2026-09-07/framework-evolution/sglang-graphs.html)、[Ollama MLX 预览，2026-03](../references/outline-checks/2026-09-07/framework-evolution/ollama-mlx.html)、[Ollama MLX 多 token 预测，2026-06](../references/outline-checks/2026-09-07/framework-evolution/ollama-mtp.html)。章节与实验对应见[框架演进笔记](../case-studies/framework-evolution.md)。

- 新增性能反馈与运行方式：[KernelAgent](../references/outline-checks/2026-09-07/execution-feedback/kernelagent.html)、[FlashInfer-Bench](../references/outline-checks/2026-09-07/execution-feedback/flashinfer-bench.html)、[CUDA Agent](../references/outline-checks/2026-09-07/execution-feedback/cuda-agent.pdf)、[TVM MetaSchedule](../references/outline-checks/2026-09-07/execution-feedback/tvm-meta-schedule.html)、[Ansor](../references/outline-checks/2026-09-07/execution-feedback/ansor.pdf)、[MPK v2](../references/outline-checks/2026-09-07/execution-feedback/mpk-v2.html)、[vLLM CUDA Graphs](../references/outline-checks/2026-09-07/execution-feedback/vllm-graphs.html)。落点与实验范围见[执行优化笔记](../case-studies/execution-feedback.md)。

- 5.2–5.4 的研究与编译：[AKG: Automatic Kernel Generation for Neural Processing Units using Polyhedral Transformations](../references/files/papers/akg-pldi21.pdf)；[TVM: An Automated End-to-End Optimizing Compiler for Deep Learning](../references/files/papers/tvm.pdf)；[TensorIR: An Abstraction for Automatic Tensorized Program Optimization](../references/files/papers/tensorir.pdf)；[Presburger Formulas and Polyhedral Compilation](../references/files/documents/isl-tutorial.pdf)。
- 5.3 的算法与实现演进：[FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](../references/files/papers/flashattention.pdf)；[FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning](../references/files/papers/flashattention2.pdf)；[FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](../references/files/papers/flashattention3.pdf)。
- 5.4–5.5 的同题比较：[Triton Tutorial: Matrix Multiplication](../references/files/documents/triton-matmul.html)；[CANN 8.1.RC1.alpha002 Ascend C 算子开发指南](../references/files/specs/ascend-c-guide.pdf)；[NVIDIA Hopper Tuning Guide](../references/files/documents/nvidia-hopper-tuning.html)；[Serving Large Language Models on Huawei CloudMatrix384, v2](../references/files/papers/cloudmatrix384-v2.pdf)。
- 5.5 的图执行：[CUDA Graph Best Practice for PyTorch: CUDA Graph](../references/files/documents/cuda-graphs.html)；[vLLM CUDA Graphs Design](../references/files/documents/vllm-cuda-graphs.html)。
- 5.5.1 延伸的实际后端：[Ollama v0.20.7 Apple device and working-set discovery](../references/files/documents/ollama-metal-device.txt)；[Ollama v0.20.7 bundled ggml Metal kernels](../references/files/documents/ollama-ggml-metal-kernels.txt)；[Ollama v0.20.7 bundled ggml Metal device and buffers](../references/files/documents/ollama-ggml-metal-memory.txt)；[MLX official README](../references/files/documents/mlx.md)；[KTransformers 0.3 AMX design notes](../references/files/documents/kt-amx.md)。

- 5.4 的具体模型与实现：[模型与算子核对笔记](../case-studies/model-operator-examples.md)；[Qwen3 固定实现](../references/outline-checks/2026-09-07/scaling-history/vllm-qwen3.py)；[V4-Flash 官方参考实现](../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-model.py)。

原文版本、参数差异与扩写时需补的材料见[编辑笔记](editorial-notes.md#ch-05)。
