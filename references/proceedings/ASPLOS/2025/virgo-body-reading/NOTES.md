# Virgo v2：把矩阵单元从子核移出以后，预算怎样变化

日期：2026-09-09。论文：*Virgo: Cluster-level Matrix Unit Integration in GPUs for Scalability and Energy Efficiency*，ASPLOS 2025，DOI `10.1145/3676641.3716281`。本次固定阅读 [arXiv:2408.12073v2](https://arxiv.org/pdf/2408.12073v2)，18 个物理 PDF 页；本包 PDF SHA-256 为 `ce4d7c05f7b54a225b1ae0af78ef08be00f3711cfc0e134c417723bad0f58d9c`。未重新下载，复用上一批已封存原始响应字节。

**建议有条件采用，一个小算例即可。** 它能为第 4.3.1／4.4.3 节补充一个具体判断：矩阵单元的规模既受算力限制，也受它取得操作数、保存累加状态和接受指令的组织限制。把操作数和累加器从 SIMT 寄存器路径移出，可以增大一次操作覆盖的分块、减少重复的指令和访问，但独立累加器、shared memory 容量、bank 争用和融合算子的依赖仍然需要一起满足。不要以论文节能百分比作为新增正文的主线。

本包只提供建议与自写算术。未修改大纲、扩写、案例、主索引或旧资料包；未下载或运行工件、RTL、GPU 模型或框架。

## 1. 阅读范围与证据等级

- 完整读取物理 pp.2–14 的逐页正文文本：背景、设计、编程模型、基线、评估、结论；共 13 页。
- 完整读取物理 pp.15–16 的工件附录文本：复现流程及限制；共 2 页。
- 物理 p1 的身份和摘要已在 `parallel-gpu-storage` 批次筛读，本次不重复记新增摘要或新增论文。p1 剩余引言和 pp.17–18 参考文献不计为本次正文阅读；**不是全论文通读**。
- 实际视读物理 pp.2、4、5、8、10、11、12、13、14，共 9 张完整页图。13 个图表裁片用于定位；是在对应整页中核看，未把生成裁片说成另一次视读。精确页面、像素范围和哈希见 [figures.json](figures.json)。图 4／图 6 只读取所在页的提取文本与说明，未另作图形核验，不依它们的箭头细节立论。
- 全 PDF 的两种文本提取、18 页派生文本均留存；生成全部文本不等于阅读全部页面。每页读取行范围及哈希见 [reading-proof.json](reading-proof.json)。
- 当前大纲核对范围是第 4 章 4.3–4.4、相应扩写以及 `outlines/structure.md`；快照和行号见 [book-input-snapshots.json](book-input-snapshots.json)。没有借此声称重查全书。

Poppler 对全文提取报告 `xref num 257` 重建警告；p2、p5 的渲染也分别有 `257`、`393` 警告，已保留 stderr。程序均返回 0，所选图表能正常渲染，且已人工核看表格行列及图中关键路径。返回成功不能证明未选页每个字符都完整；原 PDF 没有修补或重写。

## 2. 首先说清楚 cluster 指什么

论文 §2.1（物理 p2、图 1）将 cluster 定义为多个 SIMT 子核共享片上存储、接受一个 thread block／workgroup 并提供 barrier 的硬件组织，并以 NVIDIA SM、AMD CDNA CU、Intel Xe core 作类比。子核有自己的 warp scheduler、寄存器文件与执行单元。

因此，书中应写成“**在一个共享存储与线程块调度域内，把矩阵单元从各 SIMT 子核提升为域内共享单元**”。它不是多个商用 SM 组成的 thread-block cluster，更不是第 6 章超节点。论文 Table 2 的单个 SIMT 子核只有 8 lanes／warp；不应直接用此子核数量替代 NVIDIA SM 数量。

物理 p4 图 2 中，虚线 Tensor Core、Gemmini 的部分 scratchpad 是可选评估组件。不能把图上所有块都理解成同一个 Virgo 配置同时启用。Gemmini 的累加器、片上 shared memory、L2／DRAM 是不同存储；额外 DMA 能连接它们，也不代表这些访问免费。

## 3. 状态放置怎样改变计算粒度

论文对比的是在 Vortex／Gemmini／Chipyard 上实现的 RTL 组织，而非四款商品 GPU 的对跑。以下机制与页码均来自固定 v2。

| 组织 | 操作数与累加状态 | 粒度约束及实际代价 |
| --- | --- | --- |
| Volta-style（p9 §5.1.1） | 操作数经 SIMT RF，部分和也回 RF | 该原型每 warp 1 KiB 浮点寄存器预算；两个 8×16 FP16 操作数加一个 8×8 FP32 累加器为 768 B。剩余 256 B 不能被误写成完全没有余量。RF 读带宽及细粒度指令还会限制供数。 |
| Ampere-style（p9 §5.1.2） | 同一个 Volta-style 矩阵模块，增加 DMA | 这是隔离 DMA 收益的建模选择。作者明确说明，公开材料没有确认真实 Ampere 存在与 Hopper 相同的独立 DMA；真实 Ampere 的全部微架构改进也没有都放进这个基线。 |
| Hopper-style（pp.9–10 §5.1.3） | 操作数直接从 shared memory 取，累加器仍在 RF | 该原型 16×16 FP32 累加器为 1 KiB，恰占上述每 warp 预算。采用 16×16×32 操作；access/execute 解耦、请求 FIFO 和异步指令减少部分等待。它不等于完整 H100 的资源分配或指令吞吐。 |
| Virgo（pp.4–8、10、13） | 操作数从 shared memory 取，累加状态在专用 SRAM／阵列局部保存 | 域内统一矩阵单元可覆盖 128×64×128 的一次操作。粗粒度 MMIO 命令交给硬件 FSM 遍历，省下大量每个小分块的发射和地址生成；统一阵列也减少多个分立单元对同一输入行列的重复 shared memory 读取。 |

这里“节省状态”主要指**减少对 SIMT 私有寄存器预算和端口的占用**。累加数值本身没有消失，而是进入新增的专用 SRAM；局部阵列累加还可减少 SRAM 的访问次数。独立累加器采用规则的宽连续访问和单 bank SRAM，不必承担通用 RF 的多 bank、分散访问语义。减少指令则同时减少 scoreboard／warp scheduler 发射工作和 ALU 地址生成，而不只是降低乘加单元内部能耗（pp.12–13）。

论文报告的 shared memory read footprint 在 256³ GEMM 下为 6／4／2.25 MiB（紧耦合／仅操作数解耦／Virgo，p13 Table 4）。这是一次 kernel 的**累计读取量**，不是同时驻留容量；底层 shared memory 仍是 Table 2 的 128 KB。它也不是 DRAM 读量，不能由一次 tile 的 A、B 独特字节直接替代。表中紧耦合到 Virgo 的归一化比值约为 2.67，操作数解耦到 Virgo 约为 1.78；该对比支持“改变共享范围能减少重复供数”，不能自动推广到任意 MoE 分组或小矩阵。

## 4. 一个可独立复算的分块预算

本算例采用 p8 §4.4.1 的 `(M,N,K)=(128,64,128)`，以及 p10 Table 2 的 128 KB shared memory、32 KB 累加器和 16×16 FP16 阵列。**教学假设**明确如下：A／B 为 FP16，C 按 FP32 累加计容量；把表中的 KB 按二进制 KiB 解释；只对输入 A／B 做双缓冲，只保留一个 C 累加块，忽略对齐、额外元数据、旧 C 输入和融合中间量。论文明确描述基线的 FP32 累加，但本次未审查 Virgo kernel 类型定义，所以不会把这一教学精度设定冒充已核源码。

| 量 | 计算 | 结果 |
| --- | --- | --- |
| 一个 A 输入块 | 128×128×2 B | 32 KiB |
| 一个 B 输入块 | 128×64×2 B | 16 KiB |
| A、B 双缓冲 | 2×(32+16) KiB | 96 KiB |
| shared memory 尚余容量 | 128−96 KiB | 32 KiB；其他活跃状态尚未计入 |
| 一个 FP32 C 累加块 | 128×64×4 B | 32 KiB；累加器没有余量 |
| 矩阵乘加工作 | 128×64×128 | 1,048,576 MAC，即 2,097,152 FLOPs |
| 理想阵列计算下界 | 1,048,576÷(16×16) | 4,096 cycles；400 MHz 时 10.24 μs |

在**每次 K tile 只搬入一份 A／B、没有跨 tile 复用**的假设下，若要维持上述理想计算速度，输入搬运平均至少需要 `48 KiB / 4096 cycles = 12 B/cycle`，即 4.8 GB/s（十进制）。这是输入供给的必要平均条件；未计结果写回、突发、竞争、阵列供数重复读取及其他请求，不能据此认定 DMA 已被完全隐藏，更不能将它当成所需 shared memory 物理读带宽。

同一个算例只改 M 为 256：A、B 输入双缓冲变成 160 KiB，累加器变成 64 KiB，两个容量约束同时失败。可选动作是重新分块、减少同时存活的缓冲或增加硬件容量；“继续扩大一次矩阵操作”不是无代价的优化。也不能把剩余 32 KiB shared memory 当成已经证明 FlashAttention 的全部 Q／K／V／S／P／O 状态都放得下。

自写脚本 [check_budget.py](check_budget.py) 只做整数与单位计算；结果为 [budget-results.json](budget-results.json)。脚本还核实 FP16 MAC 数的文字预算：`8×32 = 4×64 = 16×16 = 256 MAC/cycle`。4,096 cycles 是推导的**无等待下界**，不是论文表中实测的 kernel 周期。

## 5. 移出寄存器以后，新增了哪些等待

1. **shared memory 的共同入口。** p5 §3.2.1、图 3 将宽矩阵请求拆为 subbank 请求；同一 bank 同时到达矩阵和 SIMT 请求时，优先服务矩阵宽请求。规则布局能提高并发，不能保证融合的 SIMT 阶段无等待。对非 word-aligned SIMT 请求，硬件先串行到一个 lane 再送 crossbar，减少面积；论文评估多为 word-aligned 访问，不能外推成任意 gather／scatter 都具有相同吞吐。图 3 展示的具体宽度也不应直接替代所有 FP16／FP32 配置的接口宽度。
2. **专用累加器与缓冲寿命。** 一个大操作虽然释放 RF，但新增专用容量。当前 C 未完成或未搬走，就不能无条件把同一区域给下一个输出。软件双缓冲须分别核 A／B 和融合中间值的存活期。
3. **跨执行单元的可见性与汇合。** p6 §3.3、p7 §4.3 用 busy-register polling 的 fence 等待异步工作、用 barrier 同步参与的 warps；两者不是同一件事。MMIO 命令接口无需为它本身加新 ISA，不代表整套硬件完全没有 ISA／调度修改。
4. **同一个矩阵单元上的串行需求。** p8 §4.5、图 5 将 FlashAttention 的两个 GEMM 先后放到同一单元，SIMT 同时做 softmax。GEMM 与 row rescale 会访问同一 O，必须等 GEMM-2 完成；循环依赖不能用“异步”抹掉。p9 报告 polling 区间平均 260 cycles、占该实验运行时间 2.4%，是该流水与供给配比下的结果，不是 fence 的普适固定延迟。
5. **更大原子操作的利用率风险。** p7 §4.3 明确说明，threadblock／workgroup 粒度的矩阵原子操作减少控制成本，同时牺牲对小矩阵的灵活性。不能据大方阵 GEMM 的利用率推断小 batch decode 的小专家矩阵也同样受益。

不宜宣称 Virgo 首次实现矩阵与向量并发：p7 §4.1 明确承认 Hopper、CDNA2 已能同 warp 异步协作；p14 的 Ampere-style 基线也能通过不同 warp 的多线程调度并发。Virgo 的研究问题是状态与物理集成方式改变了多少控制和访问需求。

## 6. 评估到底测到了什么

| 证据 | 条件及本次允许的结论 |
| --- | --- |
| 商品 GPU 动机表（p3 Table 1） | V100／A100／H100 上的 CUTLASS 表征；挑每代 FLOPS 最好的 5 个配置平均寄存器和 occupancy。不能写成所有真实训练 kernel 的典型占用率。该批商品 GPU 用途与下方 RTL 评估分开。 |
| RTL 配置（p10 Table 2） | 1 cluster；Volta-style 8 子核、Hopper-style 4 子核；8 warps/core、8 lanes/warp，128 KB shared memory、512 KB L2；Virgo 单矩阵单元及 32 KB 累加器。表格未单列 Virgo 的子核数量，不能由示意图数方块补出。 |
| GEMM 评估（p11 Table 3） | 三个方阵 256³／512³／1024³，存储为 FP16，各设计单独优化 kernel。Virgo MAC 利用率 66.1%／77.9%／86.5%；Hopper-style 为 60.5%／72.8%／77.0%。这是这些原型和形状的仿真利用率，不是 MFU、端到端训练性能或 H100 对比。 |
| 功耗／面积（pp.11–13） | 400 MHz、商业 16 nm 工艺，用 Cadence Joules 估计功耗、Genus 估计面积并验证频率。L1 在该原型综合成 flop arrays；Vortex idle power 偏高，可能关联时钟门控不足。所有后续 power/energy 使用运行 SoC 功率减 fully-idle SoC 功率的 active 口径，不能当板卡总功耗、PUE 后能耗或商品 GPU 节电量。 |
| FPGA（p11） | FireSim／Alveo U250 仅用于功能验证。论文功耗数字不应说成在 U250 测到的板卡功耗，也不是制造完成的 16 nm 芯片测量。 |
| FlashAttention-3 映射（pp.11、14） | FP32 配置；forward，S=1024、head dimension=64、single head、B=1。Vortex 无指数多功能单元，使用二阶 Taylor 近似 exp；本次没有发现这些正文页内对完整模型质量的验证，不能称为生产 FA3 数值等价。 |
| 工件可复现边界（pp.15–16） | 公开 RTL 仿真能重算 cycle/utilization，SMEM footprint 从波形处理。因商业 PDK 许可，功耗和面积测量方法没有提供，工件供静态 CSV；再用动态仿真周期相乘生成 energy。作者报告 Verilator 崩溃，需 VCS，测试版 V-2023.12-SP1。源码定位是工件 DOI `10.5281/zenodo.14835068` 及 GitHub ucb-bar/virgo、virgo-kernels；本次仅读附录定位，没有下载、固定源码提交或复现。 |

v2 报告的 active power 降幅可达相对 Ampere-style **67.3%**、相对 Hopper-style **24.2%**；active energy 降幅相应 **80.3%／32.5%**（pp.2、11–12）。这些是该论文带限定条件的结果，保留在证据层。旧 v1 摘要的 **66.3%／77.2%** 不得混入当前段落。原始 HTML 与继承的版本记录在本包留存；没有把不同版本的百分比解释成测量误差。

## 7. 保留的疑问，不扩大采用范围

- **FP32 总 MAC 预算未闭合。** p10 Table 2 按文字列出：基线每 cluster 8×16 或 4×32 个 FP32 MAC，而 Virgo 写 8×8 FP32 阵列；同页 §5.3 又说各配置 MAC 数相同。这可能涉及 FP32 专门配置未在表内完整展开，本次未查源码，不能判为确定实现错误。FA 实验是 FP32，故不把 p14 的 `65.7% / 35.1%` 利用率比直接写成 1.87× 加速比。采用的简单预算只使用可由表面数字闭合的 FP16 路径。
- **共享存储供给并非完全相同。** p13 §6.1.3 明确说 Volta／Ampere-style 用更激进 banking 将 shared memory 带宽提高 2×，否则会受供数限制。因此“同 MAC 数”不等于所有资源和功耗预算相同；不能将差值全部归因于一个单独开关。Virgo PE 的 FMA 与基线分开的乘／加实现也有局部差异（同页）。
- **工件与教学假设尚有边界。** 32 KB／128 KB 的单位解释、Virgo FP16 kernel 累加类型和完整融合工作集未经固定源码核查。纸笔练习明确采用假设，不虚构工件已经验证它。附录下载示例使用 Zenodo `14835069`，摘要式工件 DOI 为 `14835068`；可能是记录／版本关系，本次没有在线核验，不把它强行定性为链接错误。
- **多矩阵单元不是完整并发服务评估。** p14 §6.3 只有大小两个单元分别跑 256³、128³ GEMM 的展示，报告并发／串行利用率 59.5%／59.7% 和按 FLOP 归一的 active power 增加 4.3%。它不证明多任务公平性、尾延迟或大规模 cluster 扩展，不作为第 6／11 章新调度材料。

以上不足不阻碍容量与状态放置的教学判断，但阻止把案例扩写成跨产品性能排名或已复现的完整 FA3 系统评估。

## 8. 与现有内容怎样衔接

当前 `outlines/04-加速器架构.md:95` 的 4.3.1 已有分块、shared memory、TMEM 与寄存器压力；`:143` 的 4.4.3 已有矩阵／向量交接。扩写对应 `:113`、`:171`。因此不要新增一节“Virgo 架构”，也不要新增核心实验。

建议只在 **4.3.1 的扩写**接入本包的一个预算，并在 **4.4.3** 回到它的争用和依赖。精简大纲最多补下面这一短段或一个资料入口：

> 以 Virgo 的 RTL 研究原型追踪一次矩阵操作：输入仍在 shared memory，累加结果移到专用 SRAM 后，一次操作能覆盖更大的分块。用 128×64×128 的 FP16 输入、FP32 累加教学配置，先算 96 KiB 输入双缓冲与 32 KiB 累加状态，再检查它们分别落在哪里；增大分块后，容量与供数是否仍然满足。回到矩阵／向量协作时，画出共享 bank 的争用和结果依赖，说明寄存器压力下降为何仍不保证任意融合或小矩阵都更快。

**相对现有内容新增的判断**是：容量必须按物理存储分别入账，不能把“片上总字节够”当成可执行；增大计算粒度减少 SIMT 控制与重复供数，代价却可能转成专用累加器容量、共享入口争用和不适合小矩阵的操作粒度。现有异步搬运与 TMEM 叙述提供产品演进，这个研究原型可用于隔离状态放置的影响，不能用于替代产品规格或宣称 Virgo 导致了后续商业设计。

若实验 4-4 需要一个纸笔校准点，可将本预算作为已有练习的可选起始条件，仍回到 Qwen／V4 的原主案例；不要把它单列成第四项核心实验。图 4-5 若需要局部插图，自绘一张“SIMT RF／shared memory／独立累加器”数据路径小图，并标宽请求优先与必要 fence；引用论文的来源图号。没有必要整页搬用 RTL 方框图或能耗柱图。

## 9. 交接与复核

- 原 PDF 与来源／版本：`virgo-v2.pdf`、`source-provenance.json`、`inherited-identity-provenance.json`、两份 arXiv HTML 与 v1 摘要。
- 阅读证据：`reading-proof.json`、`figures.json`、逐页默认／layout 文本、9 页图、13 图表裁片和 extraction/render stderr。
- 教学推算：`check_budget.py`、`budget-results.json`。
- 原书范围：`book-input-snapshots.json` 及三个原文快照。
- 校验：`verify.py` 只读原件，重提取 PDF 文本并检查身份／页数／哈希，运行本包自己的算术；允许 Poppler 已归档警告，不将其掩盖。它不验证论文仿真结论。`verification-result.json` 是本次实测结果。
- 精确清单与哈希：`FOLDER-MANIFEST.json`；校验结果文件和清单本身从清单条目中排除，避免自引用。不要求原 `/Users/boj` 路径存在即可在搬移后的目录运行。
