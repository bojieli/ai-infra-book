# PCIe 通信中的中转与 NUMA 放置

这是第 6.5 节拓扑实验与第 7.3 节通信路径的扩写准备。承接 Qwen3-8B 的同一个矩阵，增加一个读者可以逐段核算的问题：逻辑通信量不变，为什么 CPU 内存和双路 CPU 互联的负担会变？

## 从模型矩阵到物理路径

沿用[固定 Qwen3-8B 配置](../references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json)的 hidden size 4096，取 1024 个 token 的 BF16 输出，即 `[1024,4096]`、8 MiB。这里只研究一次四卡 ring AllReduce，不把它当成整层或整个模型的执行时间。

教学机器有两个 NUMA 节点：G0、G1 接 A，G2、G3 接 B。四卡 ring 的 reduce-scatter 和 all-gather 各三轮，每轮每条有向边发送 2 MiB。因此每卡总发送、总接收各 12 MiB，全体逻辑发送量为 48 MiB。

先假设每条边都经一块主机内存中转，发送 GPU 写入一次，接收 GPU 读取一次，没有额外 CPU 拷贝。分别标明每块缓冲的物理 NUMA 位置；分配它的进程身份并不能替代这个位置。以下有效带宽全部是教学假设：每卡 PCIe 每方向 12 GB/s，每个 NUMA 节点的 DRAM 读写合计 40 GB/s，A↔B 每方向 8 GB/s；两个方向可并行。MiB 按二进制，GB/s 按十进制。

| 候选组织 | A／B 的 DRAM 读写量 | A→B／B→A 数据量 | 已列资源给出的时间下界 |
| --- | --- | --- | --- |
| G0→G1→G2→G3→G0，缓冲全放 A | 96／0 MiB | 24／24 MiB | 3.146 ms，CPU 间互联 |
| 同一 ring，每条边的缓冲靠近发送 GPU | 48／48 MiB | 12／12 MiB | 1.573 ms，CPU 间互联 |
| G0→G2→G1→G3→G0，缓冲靠近发送 GPU | 48／48 MiB | 24／24 MiB | 3.146 ms，CPU 间互联 |

以第一种为例：G2 向 A 内存写数据经过 B→A，A 内存向 G2 提供数据经过 A→B；G3 同理，所以两个方向各 24 MiB。第二种只有 G1→G2、G3→G0 的跨 NUMA 边需要经过 CPU 间互联。第三种虽然缓冲放置相同，四条边却全部跨 NUMA。

每卡 PCIe 的下界都是 `12 MiB / 12 GB/s = 1.049 ms`；第一种 DRAM 下界为 `96 MiB / 40 GB/s = 2.517 ms`，后两种为 `48 MiB / 40 GB/s = 1.258 ms`。把它们与 CPU 间互联的下界取最大值，得到表中结果。96 MiB 是传输期间的读写量，缓冲实际需要驻留多少容量须按分块与流水深度另算。

这里只算了所列资源的下界。共享 PCIe host bridge、协议流量、缓存命中、启动与归约、SM 占用、分轮依赖均未计入；“下界减半”不能直接写成实际服务快两倍。它也没有假定 4090 具备 GPU P2P 支持。读者应先用这笔账排查可疑路径，再测实际平台。

## TCCL 给这个例子增加什么

TCCL 是 ASPLOS 2024 的历史研究系统，针对依赖 PCIe 的 GPU 集群搜索通信路径。作者材料和固定实现支持两个与本书有关的机制：把中转缓冲的 NUMA 位置纳入路径选择；测量并发传输组合，再选择路径。采用范围见[归档与逐文件阅读记录](../references/framework-history/2026-09-08/pcie-staging/README.md)。

已核源码中，发送端把选定 NUMA 编号传给共享内存分配；它既能使用 GPU kernel，也有 memcpy 路径。profiling 的默认单次数据量是 32 MiB、10 次迭代并排除 1 次预热；默认搜索禁用 memcpy 候选，因此不能从“实现了两种机制”推断某次搜索实际比较了两种机制。计时包含完成同步，`nbytes / us_avg` 不是所有并发链路吞吐的求和，也不是 nccl-tests 的 `busbw`。

作者正文 PDF 本次公开入口返回 403，尚未取得并阅读；只采用作者说明与已读实现段落，不采用其加速比，不把路径搜索的最优性主张当成已核证明。当前固定仓库提交在 2025 年，不能把提交日期当作论文日期；AE 使用 NCCL 2.18.3、PyTorch 2.0.1 等历史环境，不能据此推断当前 vLLM／SGLang 的默认路径或安装兼容性。

## 与当前框架接起来

第 6 章先按 vLLM／SGLang 的实际分派辨认 custom AllReduce 或 NCCL，再核 NCCL 的实际 transport。NCCL 2.31.2 源码中的 `SHM/direct` 是 GPU 直接访问主机共享缓冲的路径描述，不能见到 `direct` 就判为 GPU 间 P2P。CPU 参与控制、数据经主机内存、CPU 核执行复制，是三个分别核对的问题。

NCCL 官方文档给出共享内存机制的版本边界：2.23 加入 cuMem host allocations；2.24 在 CUDA driver ≥ 12.6、runtime ≥ 11.3 时默认启用；2.26.5 增加可用性检查与回退。固定 2.31.2 分配函数根据当前 GPU 的 HOST_NUMA_ID 选择物理主机内存位置，条件不满足时仍有传统路径。环境、CPU／内存亲和性与实际日志一起决定本次实验如何解释。[官方说明](https://docs.nvidia.com/deeplearning/nccl/archives/nccl_2312/user-guide/docs/troubleshooting/runtime_and_mpi_issues.html)

这段演进只补充底层通信实现。它没有为三个推理框架各增加一项同名功能，也没有证明新版 NCCL 能消除所有 NUMA 拥塞。

## 接入现有实验与配图

实验 6-6 保留原有端口和割集设计，增加表中四卡变体。先逐轮列出 GPU→缓冲→GPU 路径，把字节计入各个有向资源；再以固定版本 nccl-tests 和实际 vLLM／SGLang 片段检查路径、正确性、单流与并发时间。系统记录包括 GPU／NIC／NUMA 拓扑、CPU 与内存亲和性、库版本及 transport。只对实际支持的配置做对照；实际模型的 TTFT／TPOT 最后单独核对。

图 6-6 增加局部放大图：相同四张 GPU、两种缓冲放置、两个 ring 次序，箭头标数据方向和字节数；整体仍是拓扑与物理组织的一张 SVG 计划图。第 7.3.3 节引用这个路径，不再重算一次。

算术输入与三个结果记录在[计算记录](../research/2026-infra-survey/arithmetic.json)，验证脚本通过逐轮、逐边累计物理资源流量复核。尚未运行 GPU 或模型性能实验。

三个教学候选现已接入统一计算项目：运行 `python3 calculations/calc.py numa-staging --format md`，并以 `--placement sender-local`、`--order alternating` 切换。见[物理路径实现](../calculations/src/infra_calc/topics/numa_staging.py)及[生成结果](../calculations/results/README.md)。逐轮共享资源累加器同时保留全局资源下界与逐轮依赖下界，不以流量反推缓冲驻留容量。
