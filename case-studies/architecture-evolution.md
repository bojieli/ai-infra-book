# 从负载变化理解芯片演进

本笔记支撑第四章各节中的代际比较。每次只选影响当前模型的一两项变化：先给旧负载与资源限制，再换负载，计算新增机制能省去什么以及代价在哪里。完整型号规格留在资料库；正文采用局部数据路径、时间线和可复算的例子。

## 计算单元与工作比例

CNN、BERT／GPT 类训练用于说明当时需求，Qwen3-8B 与 V4-Flash 用于今天可重算的结构。两种角色分开，不能说 Ampere 是为后来的具体模型设计。

[Ampere 白皮书](../references/files/specs/nvidia-a100.pdf)说明 TF32、BF16 与矩阵单元；[Hopper 白皮书](../references/files/specs/nvidia-h100.pdf)和[Tuning Guide](../references/files/documents/nvidia-hopper-tuning.html)说明 FP8、异步执行及供数。[Blackwell 技术简报](../references/files/specs/nvidia-blackwell-brief.pdf)配合[CUTLASS 功能说明](../references/outline-checks/2026-09-07/systems-cases/cutlass-blackwell.html)，用于分开理解数据中心 SM100 与 RTX SM120。

对 Qwen 的 QK—Softmax—AV，先分别求矩阵 FLOPs、指数、归约和中间字节。将矩阵时间单独减半，观察剩余串行部分；不能给整段注意力套同一个峰值倍数。Rubin 的官方说明把指数能力变化与长上下文联系起来，第四章据此分析矩阵／非矩阵配比，具体算子还要考虑融合与重叠。

V4-Flash 的专家矩阵及跨卡后较窄的输出，用来研究 tile 边界、K 循环、协作粒度和启动。Rubin 的较大指令 K 处理宽度在这个问题中出现；不用一条矩阵指令的提升代替所有专家形状的实测。

## 片上容量与异步供数

一个教学 GEMM tile 取 M＝N＝128、K＝64、输入 BF16：A 与 B 合计 32 KiB，FP32 累加器逻辑大小 64 KiB。假定一次供数延迟 6 μs、每 tile 计算 2 μs，需要提前约 3 个 tile 发起供数；若计算降至 1 μs，提前量变为约 6 个。若每个在途 tile 独占缓冲，加上当前计算 tile，对应 128／224 KiB。实际分块、资源争用和可用容量再校正，这些时延不是任何芯片的实测。

Hopper 的 shared memory 从 A100 的 164 KiB 提升到 228 KiB；但 Blackwell SM100 的这一容量没有再次按矩阵吞吐同比扩大。这个例子用来解释为何需要同时改缓冲、搬运和执行组织。[CUTLASS 的 SM100 样例](../references/outline-checks/2026-09-07/systems-cases/cutlass-01_mma_sm100.cu)展示 TMEM 累加器；[双 SM 样例](../references/outline-checks/2026-09-07/systems-cases/cutlass-04_mma_tma_2sm_sm100.cu)展示另一种协作粒度。程序细节放实验，正文只画数据路径和同步。

Ampere 异步拷贝已经避免经寄存器中转；Hopper TMA 在此基础上承担更复杂的 tensor 搬运和地址生成，不能把前者已有收益写成后者首次提供。Rubin 的专家描述符更新与更细的依赖触发，分别放在地址生成和流水小节。每项改动都比较减少的工作与新增的描述符、缓冲、同步或调度约束。

## 容量、精度与系统接口

Qwen 的长前缀及 V4 的大规模专家说明容量与带宽是独立限制。H100→[H200](../references/outline-checks/2026-09-07/systems-cases/nvidia-h200-systems.html)用于观察存储增长，[B200](../references/files/specs/nvidia-dgx-b200.html)与 Rubin 则进一步比较供数和设备协作。固定具体产品形态；卡间双向聚合带宽先转成模型实际路径的有效带宽。

低精度部分沿质量、数据量和运算路径解释 TF32／BF16、FP8、分块缩放与 FP4。软件将低比特权重解码到高精度和原生低精度矩阵执行，省去的步骤不同。Rubin 的新增表示和稀疏能力采用[官方架构说明](../references/outline-checks/2026-09-07/systems-cases/rubin-rechecked.html)的适用范围；涉及近似的激活／注意力压缩，必须检验质量。不能把 MoE 路由稀疏当作硬件 2:4 稀疏。

封装与互联小节由本章未解决的数据移动引出。Vera 是 CPU、Rubin 是 GPU，Vera Rubin 是平台；卡间通信、CPU—GPU 一致性接口和整柜指标分别讲。同步机制改善只消除其中一部分交接等待，完整放置由第六章计算。

## 昇腾与 Apple 的同类问题

昇腾沿早期 DaVinci、910C 与 950 的计算／向量组织、存储及搬运分别展开。CNN 背景与作者经历、CloudMatrix 的 MLA 实现、950 的 CV 通路和 NDDMA 使用各自原件；结合工作比例推断资源选择，不填造未公开的 910A／B／C 连续微架构历史。详见[架构比较](accelerator-architecture.md)和[UB／昇腾核对](../references/UB-ASCEND-NOTES.md)。

Apple 从 M2 Max 的实际 Metal 路径出发：[M3 的 Dynamic Caching](../references/outline-checks/2026-09-07/systems-cases/apple-m3-evolution.html)放在局部存储分配，[M5 的 GPU Neural Accelerator](../references/outline-checks/2026-09-07/systems-cases/apple-m5-evolution.html)放在矩阵单元与软件调用路径。局部存储机制不等于系统统一内存，GPU 内的 Neural Accelerator 不等于独立 Neural Engine。Apple 未披露的指令、容量或内部设计动机不补猜。

## 写作中的因果判断

厂商或论文明确说明的目标，注明出处与发布时间；由工作负载和资源约束推导的合理性，明确写成本书分析。每次设计比较都保留反问：原任务不变时是否有收益，换成长上下文、小专家矩阵或低 batch 后瓶颈怎样移动，省下的时间是否抵得过面积、功耗、质量与开发成本。第四章不再另设一节按年份汇总代际特性。
