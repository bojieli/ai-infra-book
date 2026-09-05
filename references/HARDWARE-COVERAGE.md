# 芯片与系统资料覆盖

核对日期：2026-09-05。本文按架构列出已经保存的原件及其适用范围，供第 4 章的硬件分析、第 5 章的算子实现、互联章节和终章的综合比较使用。完整地址、获取时间、页数和 SHA-256 见 [manifest.json](manifest.json)，逐章索引见 [README.md](README.md)。

上一轮资料库缺少 Graphcore，TPU 也主要依靠 v1、v4 论文，尚不足以比较产品代际。本轮已补入相应架构说明、编程文档和产品规格，并扩充 AMD、AWS、Intel、SambaNova、寒武纪及端侧设备的材料。Cerebras 的 WSE-3 架构白皮书、芯片规格和 CS-4 系统规格此前已经归档。

## 已取得的材料

下表中的链接均指向本地文件。PDF 保留下载原件；HTML 保存官方网页及其可搜索文本。网页文档中的某一章、产品简介和完整指令集手册分别标明，不能相互替代。

| 架构与代际 | 架构、论文与编程依据 | 芯片与产品规格 | 写作范围与限制 |
| --- | --- | --- | --- |
| NVIDIA：Volta 至 Rubin | [V100](files/specs/nvidia-v100.pdf)、[A100](files/specs/nvidia-a100.pdf)、[H100](files/specs/nvidia-h100.pdf)、[Blackwell](files/specs/nvidia-blackwell-brief.pdf) 架构资料；[Rubin 官方技术文章](files/documents/nvidia-rubin-arch.html) | [H100](files/specs/nvidia-h100-spec.html)、[DGX B200](files/specs/nvidia-dgx-b200.html)、[GB200 NVL72](files/specs/nvidia-gb200.html)、[Vera Rubin NVL72](files/specs/nvidia-rubin-system.html)、[NVLink](files/specs/nvidia-nvlink-spec.html) | 可分析矩阵与通用执行、存储层次及域内互联演进。区分芯片、整机和机柜；官方发布参数、产品交付与实测性能分别取证。NVLink 产品参数不是完整协议规范。 |
| AMD：CDNA 3／4、MI300X／MI350X | [CDNA 3 白皮书](files/specs/amd-cdna3.pdf)、[CDNA 4 白皮书](files/specs/amd-cdna4.pdf) | [MI300X 芯片](files/specs/amd-mi300x.html)与[平台](files/specs/amd-mi300x-platform.pdf)；[MI350X 芯片](files/specs/amd-mi350x.pdf)与[平台](files/specs/amd-mi350x-platform.pdf) | 可比较 chiplet、矩阵指令、存储和互联。MI300A 与 MI300X、单器件与八卡平台分别核算，低精度和稀疏峰值保留其条件。 |
| 昇腾：早期 DaVinci、910C、950 | [早期架构论文所在期](files/specs/ascend-davinci.pdf)、[Ascend C 指南](files/specs/ascend-c-guide.pdf)、[CloudMatrix384 v2](files/papers/cloudmatrix384-v2.pdf)及[v3](files/papers/cloudmatrix384-v3.pdf)、[950 官方白皮书](files/specs/ascend-950-official.pdf) | 950 白皮书表 3-1；[UB 2.0.1 正式规范](files/specs/UB-Base-Specification-2.0.1-zh-clean.pdf)、[OS 参考设计](files/specs/UB-Software-Reference-Design-for-OS-2.0-zh.pdf) | 950 的核内与互联设计已有直接依据。910C 的双 die、核数及系统实现可按论文版本引用；完整代际指令、向量吞吐和布局能力差异尚未闭合。详见[核对笔记](UB-ASCEND-NOTES.md)与[架构比较案例](../case-studies/accelerator-architecture.md)。 |
| Google TPU：v1 至 Ironwood，8t／8i | [v1 论文](files/papers/tpu-v1.pdf)、[v4 论文](files/papers/tpu-v4.pdf)、[v2 至 Ironwood 的代际论文](files/papers/google-tpu-generations.pdf)、[系统架构](files/documents/google-tpu-architecture.html) | [v4](files/specs/google-v4.html)、[v5e](files/specs/google-v5e.html)、[v5p](files/specs/google-v5p.html)、[v6e](files/specs/google-v6e.html)、[tpu7x](files/specs/google-tpu7x.html)、[机器配置](files/specs/google-tpu-machines.html)、[8t／8i 官方技术说明与规格表](files/specs/google-tpu8.html) | 可比较矩阵计算、SparseCore、存储及互联拓扑。8t／8i 材料是 2026-04-22 的官方技术发布，不能等同于完整 ISA 或已经可购买的云实例规格。 |
| Graphcore：GC200、Bow、IPU21 | [Mk2 系统架构白皮书](files/specs/graphcore-mk2.pdf)、编程指南的[硬件章](files/documents/graphcore-hardware.html)与[编程模型章](files/documents/graphcore-programming.html)；[ISA 1.2.3](files/specs/graphcore-isa.pdf)、[IPU21 ISA 1.3.1](files/specs/graphcore-isa-fp8.pdf) | [M2000 历史版数据手册](files/specs/graphcore-m2000-pdf.pdf)、[M2000 产品规格](files/specs/graphcore-m2000.html)、[Bow-2000 产品规格](files/specs/graphcore-bow2000.html)、[Bow Pod16 简介](files/specs/graphcore-bowpod16.pdf) | 可完整组织一个片上 SRAM、tile、BSP 与显式数据交换的历史案例。已存两章编程指南，不声称保存了全书；公开 ISA 主要覆盖 worker 指令。IPU21 的 FP8 支持不能移用于 GC200／Bow。另有[第一代 IPU 微基准论文](files/papers/graphcore-microbench.pdf)，不将其测量当作后代产品结果。 |
| Cerebras：WSE-3、CS-4 | [晶圆级架构白皮书](files/specs/cerebras-wse3.pdf)，13 页 | [WSE-3 数据手册](files/specs/cerebras-wse3-spec.pdf)，1 页；[CS-4 数据手册](files/specs/cerebras-cs4-spec.pdf)，5 页 | 芯片与系统规格均已保存，可分析晶圆内存储与通信以及系统外部供给。另需具体任务的放置、外部权重供给和测量记录，才能给出端到端比较。 |
| Groq：TSP 与早期机架系统 | [ISCA 2020 论文](files/papers/groq-tsp.pdf)、[ISCA 2022 扩展论文](files/papers/groq-scale.pdf) | [GroqChip 简介 v1.5](files/specs/groq-chip.pdf)、[GroqRack 简介 v1.0](files/specs/groq-rack.pdf) | 可分析静态调度、片上 SRAM 和跨芯片执行时序。上述资料的产品代际明确；不能将其规格套用到较新的 NVIDIA Groq 3 产品。 |
| SambaNova：SN40L、SN50 | [SN40L 架构论文](files/papers/sambanova-sn40l-paper.pdf)、[SN50 官方技术文章](files/documents/sambanova-sn50.html) | [SN40L 芯片简介](files/specs/sambanova-sn40l.pdf)、[SN40L-16 系统规格](files/specs/sambanova-sambarack.pdf)、[SN50 SambaRack 产品页](files/specs/sambanova-sn50-system.html) | 可分析数据流与 SRAM／HBM／DDR 分层。SN40L 论文的 Composition of Experts 与模型层内 MoE 分别解释。SN50 文章中的模型推演和芯片内核实测分别引用，不能将前者写成生产系统实测。 |
| AWS：Trainium2／3 | [Trainium2](files/specs/aws-trainium2.html)、[NeuronCore-v3](files/documents/aws-neuroncore-v3.html)、[Trainium3](files/specs/aws-trainium3.html)、[Trainium3 NKI 架构指南](files/documents/aws-trainium3-nki.html) | [Trn2 系统](files/specs/aws-trn2-system.html)、[Trn3 UltraServer](files/specs/aws-trn3-system.html) | 可比较计算引擎、软件管理的存储、搬运与集合通信。Trainium3 两份官方文档存在带宽和 CC-Core 数量差异，见下文；据此取值时必须指明文档。 |
| Intel：Gaudi 3 | [Gaudi 3 架构白皮书](files/specs/intel-gaudi3.pdf)，30 页 | 同一白皮书含存储、计算、以太互联及系统配置参数 | 可作为矩阵计算、可编程处理器与以太扩展的参照。具体 OEM 服务器的功率、网络端口和配置须再对应其产品手册。 |
| 寒武纪：思元 370 | [官方产品页](files/specs/cambricon-mlu370.html) | 同页给出产品、chiplet 与 MLULink 参数 | 已取得产品级依据，可作有限比较；尚无本地完整微架构／指令集手册，亦未取得较新代际的足量官方规格。 |
| 端侧：Apple M5、Snapdragon X Elite | [Apple M5 MacBook Pro 技术规格](files/specs/apple-m5-macbook.html)、[Snapdragon X Elite 产品简介](files/specs/qualcomm-xelite.pdf) | 对应具体整机／SoC 的 CPU、GPU、NPU 与内存参数 | 与已存 Ollama、MLX、llama.cpp、Unsloth 资料结合。产品参数不能证明某工具实际调用了 NPU；须记录后端、算子回退、持续功耗与设备温度。X Elite 材料为 2023 年产品资料。 |
| Taalas、Etched、OpenTallas | [HC1 官方说明](files/specs/taalas-hc1.html)、[Etched 产品页](files/documents/etched-sohu.html)、[OpenTallas 案例](../case-studies/opentallas.md) | Taalas 与 Etched 当前收录公开产品描述；OpenTallas 采用作者固定提交及分析记录 | 适合讨论专用化、更新能力与存储组织。未取得商业产品的完整微架构或 ISA；OpenTallas 的分析、综合与模拟不得写成完整芯片实测。 |

## 引用前必须处理的差异

1. **来源版本。** `latest` 网页已经按获取时间和 SHA-256 固定，但 URL 中的 `latest` 不证明产品仍在销售。历史白皮书、当期产品规格和新架构公告各自保留日期；不同代际不能拼成一个虚构的器件。
2. **参数冲突。** 本次保存的 [Trainium3 架构页](files/specs/aws-trainium3.html)给出 4.9 TB/s 内存带宽与 16 个 CC-Core，[NKI 指南](files/documents/aws-trainium3-nki.html)则给出 4.7 TB/s 与 20 个 CC-Core。当前材料没有解释差异，书中暂不据此作精确横向排名，也不自行推断为逻辑／物理核之别。
3. **芯片与系统边界。** HBM 容量、核内 SRAM、整机合计存储、单芯片带宽和机柜汇总带宽分别登记。互联须明确方向、协议开销与端口复用；不能把双向带宽或多卡合计量代入单向单卡传输。
4. **性能证据。** 峰值规格、厂商推演、芯片内核测量和完整应用测量分别标注。统一模型、质量目标、精度、输入输出长度、批量、编译器及功率边界之后，才能比较延迟、吞吐和费用。

## 仍需补充的资料

- **昇腾代际设计细节。** 910A 的早期设计过程，以及 910B／910C 对应型号的向量指令、单核吞吐、布局与 stride 能力。已取得的 CloudMatrix384 论文能填补部分组织和实现依据，不能闭合所有历史变化。
- **同条件测量原件。** 跨厂商基准的具体提交、运行配置和原始结果，真实训练／推理的执行轨迹，以及整机功率测量。当前资料足以展开架构原理，尚不足以写无条件的性能或成本排名。
- **系统部件规格。** 为书中选定的系统算例补齐 NIC、交换机、光模块、SSD、主机 CPU／内存及供电冷却配置。已有互联协议和加速器系统资料，仍不能替代每一项设备的产品参数。
- **公开程度有限的产品。** 寒武纪较新代际、Taalas、Etched，以及较新 Groq 产品的完整架构或编程资料。若未公开，保留问题及证据范围，以资料充分的架构承担主要推导。
- **端侧与平台记录。** 端侧持续性能、温度与后端选择；多作业调度、沙箱启动、资源计量和账单对账所需的实际运行记录。其缺口不能靠再下载一份产品简介填补。

这些缺口与模型训练计算量、协议文档状态一起维护在 [GAPS.md](GAPS.md)。写作时先使用本地固定原件；新增论点需要其他资料时，先取得、核对并归档，再进入正文。

## 配图与离线使用

已另存 TPU 8t／8i、Graphcore 硬件与编程模型、Trainium3 及 NKI 指南的 46 幅官方配图，见[配图索引](figures/README.md)。配图记录来源网页、网页快照校验值及各自 SHA-256，不另计作 46 份独立文献。原始 HTML 保持不变，离线时通过该索引查看图片；其他外部脚本和页面跳转仍可能需要联网。
