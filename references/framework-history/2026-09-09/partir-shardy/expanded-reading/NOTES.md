# PartIR：从矩阵切分意图到通信程序

交付时间：2026-09-09 UTC。只写本目录，仓库、大纲、Git 与此前两个任务的交付均未改动。以下是选择性正文和固定源码审读，不是运行复现。完整原字节、HTTP 状态、取回时间与 SHA-256 在 `sources.json`；阅读范围、图像与当前书稿快照在 `reading-proof.json`。

**采用结论：可在现有第 6.2.2 节加入一小段编译器变体，连接第 5.3 节；不增章节，不追加模型目录。** 已有 MeshSlice 算例解决网格、分块与流水，PartIR 的补充价值是“同一数学图，分片意图怎样按顺序传播，并变成必要的通信”。论文的手动策略组合、论文使用的 MCTS 搜索、当前 Shardy 的优先级传播和通信插入，应分开叙述。

## 已读范围及版本

- 作者 [arXiv v4](https://arxiv.org/pdf/2401.11202v4)：36 个物理页，首页标 2024-11-24；不能因正式 ASPLOS 2025 版本为 17 页，就把本文件后半当作未归档。PDF 原字节由根任务已归档响应复制，本任务没有伪记成新的 HTTP 下载。
- 完整文本阅读物理页 1–13、17–23，共 20 页；第 33 页仅第 40–59 行，即定理 C.7 与证明开头。第 14–16 页参考文献和第 24–32、34–36 页未作正文精读。关键词定位不计全文阅读。
- 实际查看渲染图像物理页 3、5、7、9、10、11、12、18、20、23，共 10 页；`views/` 保留图片和 hash。
- 官方 [Shardy 固定提交](https://github.com/openxla/shardy/tree/a72dc82ce730c55be36a409945f4224181d050fc)，提交时间 2026-09-09T01:31:51Z。源码路径下文均相对此提交的 `shardy/dialect/sdy/transforms/`。
- 官方 [Shardy overview](https://openxla.org/shardy/overview)、[JAX migration](https://docs.jax.dev/en/latest/shardy_jax_migration.html) 已保留动态页面原字节，正文提取全文阅读。迁移页仍保留 March 2026 计划语言；本次不把计划日期当作已经完成的当前默认行为。

## 论文实际解决的事情

1. **分开模型与分片意图，保留顺序和冲突。** 第 2–5 页用同一两次矩乘，把输入 batch 切分、参数维切分和进一步参数分片写成 tactic 序列；先执行策略形成的约束不被后面策略任意推翻。策略可组合不等于可交换，也不等于所有中间张量都能由两行参数自动处理。第 8 页同一 mesh 轴同时切输入 batch 和权重输出维的冲突不能神奇消失；第 13 页 `X × Xᵀ` 例子仍可能需要 tag/atomic 明确中间复制，模型表达与意图分离存在这些现实例外。
2. **把数学上需要的交换显式化。** 第 6–9 页由 Core 的 tile/loop/reduction 表达及算子传播规则，到 SPMD/HLO 通信。相同 mesh 轴和数据含义下，AR 后 slice 可形成 RS，AG 后不同维 slice 可形成 A2A，匹配的 AG/slice 可消除。只是少了 IR collective，不代表少了固定数量的 GPU kernel，更不是端到端加速保证。
3. **手工、自动、搜索质量是三回事。** `ManualPartition` 依名字/维度等用户知识；`AutomaticPartition` 在论文里由 MCTS 实现，并用有偏差的成本模拟器评价。第 11 页 Fig.6 的 T32 混合手动/自动并不总优于手工；第 17–19 页的 shape/FLOPs/collective/liveness 与简单融合启发式没有完整模拟后端布局、缓存和实际拓扑。没有“任意模型/硬件自动最优”的依据。
4. **形式证明只覆盖特定层次。** 正文第 10 页措辞较概括；第 22–23 页明确区分 Core→SPMD lowering 的形式语义与 propagation 的正确性。后者依算子规则，并未因论文形式化而获得全链证明。第 33 页定理 C.7 属于该形式系统；本次没核完整证明，也未找到/运行机械证明工件。不能把定理扩展成浮点逐位相等、任意 StableHLO 操作或当前 Shardy 全栈验证。
5. **实验条件与限制要保留年代。** 第 10–12 页是 JAX 的 U-Net、GNS、Chinchilla 派生 5B/32B Transformer 及对应推理，设备为 A100 40 GB 或 TPUv3；XLA rematerialization 关闭。不是 Qwen3、现代 MoE 或 vLLM/SGLang 集成评测。第 12–13 页有整除、reshape 轴细分、空间卷积 halo、异构 MPMD 等限制。本次不采用硬件峰值表、加速倍数或编译/搜索时间数字。

## 论文到官方实现：逐条可核的路径

| 问题 | 已读固定源码与测试 | 可以写进书里的判断 |
|---|---|---|
| 策略为何受顺序影响 | `propagation/user_priority_propagation.cc:72–204,231–257`；同名 `.mlir` 测试 1–100 行 | 优先级非零的维先隐藏/闭合，再逐级恢复，每轮调用传播；arg 与 return 的优先级变化会改变中间布局。这是明确的阶段顺序，不是自动证明任意 TP/PP/DP/EP 组合最优。 |
| 自动搜索是否已开箱提供 | `propagation/propagation_pipeline.cc:101–106`；`auto_partitioner_registry.h:26–55`、`.cc:38–64`、测试 23–30 行 | 此处启用自动划分后调用外部注册回调；未注册会 fatal error。所读测试仅验注册/清空。本路径没有论文 MCTS 搜索器、成本模型或优化质量测试，不能把接口当作复现论文自动搜索。未做全仓搜索，亦不宣称任何别处绝不存在搜索器。 |
| 通信是否仍全留给 GSPMD | `export/export_pipeline.cc:40–85,90–127` | 当前固定源树已经有显式 reshards、collectives 插入/优化及 per-instruction 分支；由选项控制。因此旧 overview 的短期 GSPMD/长期新 partitioner 规划，不能直接当作当前源码功能清单。但本次没有审 XLA/JAX 的实际选项传递，不能写“所有 JAX 当前默认都运行此分支”。 |
| reshard 如何变通信 | `export/reshard_to_collectives.cc:240–380,1048–1063,1170–1370` | 顺序尝试缩小张量的 all-slice、置换、all-to-all，最后 all-gather；配对输入输出 mesh 与轴。明确仍有贪心 A2A 可能引入额外 padding 的 TODO。策略表达合法、插入路径存在，和真实链路最优是不同层次。 |
| 何处能核对 AR/RS 及延迟归约 | `export/test/export_pipeline_explicit_collectives.mlir:1–116`（全文件 182 行已读） | 固定 FileCheck 例子既有 reduction 后 RS，也有矩乘输出的 unreduced 轴、立即 AR、经过线性 add 后再 AR、分轴部分延迟等。适合作教学静态对照；输入是小矩阵 IR，测试预期不是已经在本任务执行通过。 |
| “collective 优化”具体到什么 | `export/optimize_collectives.cc:40–84`；`export/passes.td:165–220` | 本 pass 具体匹配 collective-permute 与 A2A 链，检查条件再重写；AR+slice→RS 由 export 注释所指的 canonicalization 承担。不能因为 pass 名称宽泛就描述成所有集合通信的全局优化器。 |

Shardy README 与官方 overview 都把自己描述为 GSPMD 与 PartIR 工作的结合，轴/因子表示、优先级等有清楚关联；但这是后继系统证据，**不是找到了论文 PartIR 的原 API 原样发布**。JAX 迁移页还说明旧 custom-partitioning 回调需转为 einsum 风格的 sharding rule，并列性能回退、OOM、调用分歧和导出 mesh 要求。论文里的表示方法进入框架后，仍涉及规则覆盖、默认开关、序列化兼容和后端分派；本次不推断其覆盖所有新模型及芯片。

## 只建议一个落点

当前第 6.2.2 节（快照第 57–59 行）已经从 Qwen3 的矩阵形状推 TP、二维网格和通信。可紧跟二维切分段加一句到两句：

> 保持这一次 Qwen3 投影的数学图不变，将输入、权重和输出的分片意图单独表达，先手算需要收集或归约的维度，再以 PartIR 的顺序策略和 Shardy 的固定 IR 例子检查编译器如何补通信。改变约束优先级后，检查新增的 reshard 与未归约中间值；编译器能完成合法传播，不代表候选就是当前硬件上的最快方案。

这是现有实验 6-2 的代码阅读变体，并与第 5.3 节编译选择呼应；不另外增加实验编号、图编号或模型。真实 Qwen3 的编译输入、固定 JAX/XLA 版本与设备测量留待扩写准备，不能把本次小矩阵 FileCheck 测试改个标题便称为 Qwen3 已复现。已有 `mesh-shape-and-slicing.md` 的 FLOPs/字节无需重复推一遍。

## 未采用的原文疑点与边界

- 第 18 页文字所称 T32/IT32 估计偏差方向，与 Fig.9 `Measured − estimated` 图的符号看起来不一致；本次不采用偏差方向或准确率数字。
- 第 20 页 Fig.11 图注明为 search time，但实际图面轴仍是 memory error (GB)，与前一图重复；已实际看图。因此不从该图读出搜索时间分布。
- Appendix B 部分代码的 ZeRO 命名/列表拼写与叙述不完全一致，作为说明性伪代码理解，不当作本次运行命令。
- 没有执行下载代码、测试、GPU 任务或完整 JAX 编译，也未宣称静态路径在 Qwen3/vLLM/SGLang 生效。保留未读与未测，比新增一个没有证据的“最新编译器”条目更有用。

## 与根任务已集成证据的增量对照

于 2026-09-09T05:36 UTC 读取现有 `references/framework-history/2026-09-09/partir-shardy/reading.json`（原字节保存在 `root-reading-before-integration.json`）。已有 p3–5、p3/p5 图像、README/overview/JAX migration、export_pipeline 与 registry.cc 全文，以及 explicit_collectives 测试 1–28 行，本交付不把这些重复算成新增阅读。

新增正文范围为 p1–2、p6–13、p17–23 的 17 个完整物理页，以及 p33 定理局部；新增已看图像为 p7/9/10/11/12/18/20/23 共 8 页。新增源码阅读为 user_priority 路径与 1–100 行测试、auto registry 头文件/单测、propagation_pipeline、reshard_to_collectives 选择范围、optimize_collectives、passes.td 所选范围，以及 explicit_collectives 测试 29–182 行。最有用的增量是证明覆盖边界、成本估计/图文矛盾，以及当前贪心 lowering 的 padding 限制。根任务既有落点可保留；本交付第 6.2.2 段落仅供替换/补边界，不构成第二个新落点。
