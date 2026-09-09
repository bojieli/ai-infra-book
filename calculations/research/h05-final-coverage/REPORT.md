H05 全471条峰值最终覆盖审查（2026-09-09）

**合入本目录唯一最终证据补丁后，H05原“逐峰值官方字段与未知状态审查”可以验收。** 当前151配置、471条峰值全部已对应内容审查：旧逐字段审查287条，后续专题明确审查184条；两组无遗漏，旧287条的精度键和数值仍与当前匹配。本结论不表示厂商披露了全部时钟/运行功率/内部精度，也不代表实测运行性能或H07整项完成。

唯一最终合并入口为 `proposed-sources.patch.json`，然后 `proposed-hardware.patch.json`。补丁补106条峰值的证据：102条联合证据、4条内部精度限制；不改变任何峰值数值、精度键、稀疏口径或可选择性。早期102条/10条降级提案均已撤回，原降级patch文件已删除；`impact.json`当前为零降级，不能按早期消息重建旧提案。

证据判据如下，避免把证据要求提高到厂商无法满足的程度：

| 联合证据组 | 峰值条数 | 结论与范围 |
| --- | ---: | --- |
| 唯一Tensor累加格式 + 官方SKU对应Tensor格式峰值 | 56 | TF32、适用代际BF16、INT8、FP64的明确类型关系可以关联产品表；不要求逐行算术重建 |
| native scalar/packed FMA语义 + 官方SKU native/vector格式峰值 | 36 | 记录类型指令的加数/结果精度；内部融合中间值不被简化为同位宽。已重建的4条H100 scalar属于前轮，未重复计入本组 |
| Blackwell BF16明确支持组合 + 官方SKU BF16 Tensor峰值 | 10 | 官方CUTLASS tcgen05 dense/sparse均明确BF16/BF16 Acc=F32；保留现有FP32累加 |
| H100 FP8/F32特定wgmma内部精度限制 | 4 | 附加条件说明，不改产品表名义/API FP32累加类型 |

Blackwell补证来自固定commit `147295a3d4b75f3aeff247c25b8927cea9a7006a` 的[NVIDIA CuTeDSL tcgen05实现文档](https://github.com/NVIDIA/cutlass/blob/147295a3d4b75f3aeff247c25b8927cea9a7006a/python/CuTeDSL/cutlass/cute/nvgpu/tcgen05/mma.py)：`MmaF16BF16Op`（行1417起，表1431）、`MmaF16BF16SparseOp`（1558起，表1572），均明确支持的BF16输入/累加组合，目标包含sm100/sm103。独立复核见 `research/blackwell-bf16-independent/REVIEW.md`。PTX Table45的kind::f16同时含F16/BF16和D类型选项，不能跨列做笛卡尔组合；即使D同时作为目的和累加矩阵，也不证明BF16/F16组合合法。宽松Python参数校验也不替代显式支持组合表。

内部精度说明依据[PTX9.3文档中9.2版本语义澄清](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)：限定`wgmma.mma_async`的E4M3/E5M2输入、dtype.f32路径，其当前实现的内部累加精度介于half与single之间。H100 Table3中的FP8/FP32 Accumulate是名义/API类型，保留不变。不能推广到所有mma/tcgen05，也不能由产品峰值表断言每个kernel都走该wgmma路径。每条coverage另列`accumulation_semantics`，明确API类型不自动证明内部有效位宽。

`coverage.json`有471条逐峰值记录，每条11项原H05字段审查，共5181项：3806项已核到相应来源范围，1375项已完成有限来源审查但资料未明确；当前没有剩余肯定式累加主张缺证而需降级的项。附加内部精度说明不混入这5181项计数。H100 NVL产品Boost已核，不代表逐精度运行域已披露；所有产品的TDP/TGP上限不替代达到峰值时的实际功率。此类有范围unknown不应持续标成“还没查”。

真正尚未做、但不属于本次官方峰值表验收前提的工作，是把特定编译kernel的实际指令序列、实际功率/时钟与数值误差作运行时验证。这些不能由官方理论表代替。保留unknown的字段若将来要升级，`next-steps.json`给出按类别的一次有限官方来源检查和停止规则：没有新直接证据就保持unknown，不重复广泛搜索，也不把未知解释为硬件不支持。

文件用途：`coverage.json`绑定实际配置SHA；`review-manifest.json`绑定复用的内容审查；`sources.lock.json`绑定49个官方原件；`joint-evidence-groups.json`列逐峰值联合证据及内部精度限制；`tests.json`给实际验证。哈希只固定所查版本，不构成语义证明。

验证：最终硬件patch所有guards按顺序实际应用成功，151设备通过validate_device；峰值数值/键不变；49份来源SHA/bytes通过；覆盖471/471。仅新增一个CUTLASS官方原件锁。共享src/config没有修改，本轮未跑完整reproduce。
