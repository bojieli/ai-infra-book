# 官方硬件规格审查记录

核对快照：2026-09-08，H20型号容量补核至2026-09-09。当前表含 151 个配置、471 条独立峰值记录；其中 NVIDIA 32 个、Apple 97 个、华为 22 个。记录数不是完整性验收。全书任务和仍缺型号见 [PLAN.md](PLAN.md)，可读表见 [results/hardware.md](results/hardware.md)，原件版本和哈希见 [sources.lock.json](configs/sources.lock.json)。

## 字段如何进入计算

| 字段 | 录入及使用条件 |
| --- | --- |
| 型号／形态 | 单 GPU、Superchip 的 GPU 合计和机柜合计分别命名；SXM、PCIe、NVL、Workstation、Max-Q、Server 分开。 |
| 峰值 | 保留输入格式、累加格式、执行单元、dense／structured、原始值、换算公式、来源位置和时钟条件。数据表未给出的字段为 `unspecified`。 |
| 有效运算数 | FMA=2；结构化稀疏规格使用 dense-equivalent 工作，并要求用户明确声明满足硬件稀疏条件。专家路由不会自动启用 sparse 峰值。 |
| 内存 | GB 沿用厂商标签，带宽转换为十进制 bytes/s。单片内存、GPU 组总内存、CPU LPDDR 和共享统一内存不混合。 |
| 功率 | 记录产品功率上限，不能当持续实测功耗。Mac 适配器瓦数不当 GPU TDP。部分型号的时钟／功率字段审查仍未完成。 |
| 缺失证据 | 不从类似型号、GPU 核数、宣传倍率或 Neural Engine TOPS 补值；可以单独计算已有内存带宽的服务下界。 |

`hardware.catalog()` 校验每个型号及字段引用的原件 SHA、来源归属、峰值选择键唯一性和单位。`roofline` 按精度／累加／单元／稀疏四项精确匹配。模型全图的逐算子逻辑读写不能自动成为 HBM 输入。

## 已核实的主要差异

| 问题 | 依据与处理 |
| --- | --- |
| 4090／5090 的累加精度 | NVIDIA RTX Blackwell 白皮书 Table 3：4090 dense FP16 Tensor 在 FP16 累加时 330.3 TFLOPS，在 FP32 累加时 165.2；5090 相应为 419 与 209.5。BF16＋FP32 使用后一个值。已保存两种记录。 |
| RTX PRO 6000 工作站与服务器 | Workstation 的 PRO 白皮书给 BF16＋FP32 dense 503.8 TFLOPS、1792GB/s；Server 数据表给 1597GB/s、FP32 120TFLOPS、最高600W。Server Tensor 宣传行尚缺可对应的 accumulator／sparsity 脚注，不能移用 Workstation 的峰值。 |
| PRO 白皮书与产品数据表取整 | Workstation 白皮书给 FP32 126.0 和 sparse FP4 4030.4；产品数据表为125和4000。保留来源差异，所选精度记录来自带累加精度的白皮书。 |
| A6000 比较表内部差异 | PRO 白皮书的 memory data rate × bus width 与其 bandwidth 行不一致。A6000 自己的数据表独立确认768GB/s；采用后者，不用存在冲突的时钟行倒推带宽。 |
| H100 的两组 Boost 时钟 | H100 白皮书 Table 3（物理39–40页）直接列输入／累加与 sparse/dense；SXM 低精度 Tensor 按1830MHz，FP32/FP64 按1980MHz。PCIe 为另一组1620/1755MHz。记录保留舍入后的原值。 |
| H100 SXM 内存带宽 | 白皮书3352GB/s附 not-finalized 说明，产品页为3.35TB/s。当前 SXM 配置的访存分母明确选择产品页3350GB/s。 |
| H200／H100 NVL dense BF16 | 产品表给 with-sparsity 数值；Hopper 白皮书明确结构化稀疏使标准 Tensor 吞吐加倍，PTX WGMMA 定义 BF16 累加为FP32。派生 dense 值保留两份补充依据和除二公式，不增加虚构有效数字。 |
| Blackwell HGX 与 GB 系统 | HGX B200/B300 的每GPU BF16 dense来自8卡系统值及明确的除二脚注；GB200 Superchip、GB300 NVL72分别记录整组资源。PTX Table 42确认BF16对应FP32累加。简报中的270/192GB、7.7TB/s和当前HGX配置不混合。 |
| GB300 FP4 的比例 | Blackwell简报 Table 2明确为1080PFLOPS dense、1440PFLOPS sparse；不强制套 sparse=2×dense。机柜合计不能作为单个未切分 GEMM 的供给。 |
| Rubin 官方版本 | Vera Rubin产品页选定GPU配置为19.2TB/s，而HGX页另有22TB/s preliminary；50PFLOPS sparse NVFP4 inference与35PFLOPS dense training也是不同条件。记录分清，不机械除二或拼接。Tensor accumulator仍待核对。 |
| 昇腾 950 | 华为架构白皮书表3-1分别给Cube、Vector和Cube+Vector。保留FP8/MXFP8/HiF8/MXFP4名称；max-spec是规格上限，多个核数与内存选项不擅自组合成可购买SKU。 |
| Atlas 300I A2 | 华为产品表明确32GB配0.8TB/s、64GB配1.6TB/s；分两条。其最高AI算力未标累加／稀疏／单元分解，保持未知，不自行改名为某个910B bin。 |
| Apple 配置与日期 | M3 Max 30/40 GPU核分别300/400GB/s，M4 Max 32/40核分别410/546，M5 Max 32/40核分别460/614。M6 16GB与32GB配置分别153/170。M5 Ultra和M6有2026-08-25官方发布及产品规格；M3 Ultra使用取得时仍列96/256GB的2025型号页，不合入另一日期的配置。 |
| Apple GPU 数字 | M1发布稿给2.6 teraflops但未明确本文所需精度／累加口径，作为不可选的原始记录。其他所选材料不补造精度峰值；GPU内Neural Accelerator和独立Neural Engine也不能混用。 |

以上原件均由各型号字段指向精确URL和本地哈希。PDF表格已经逐页查看；HTML的Chip、Memory、Specifications和脚注联合阅读，避免把共享表头、上标或多列解析错位。

## 来源排除与未闭合项

一份名为 `Flying_Product_Catalogue.pdf` 的文件托管在 hiascend.com，封面实际标“飞途昇腾／BFASCEND”。它是合作伙伴材料，不是华为芯片规格；已从可用来源锁移出，保留[排除记录](inventory/excluded-hardware-sources.json)，没有导入任何参数。这也说明官方域名本身不足以证明文档作者身份。

- A800 80GB数据中心和H20仍缺足量NVIDIA官方规格。A800 40GB Active的官方表不能替代80GB型号；vGPU兼容清单中的H20型号名称也不能证明算力／带宽。
- 昇腾910早期、910B／910C与950实际板卡的型号级峰值、累加和稀疏证据仍待补。作者论文中的架构和实现细节不能冒充完整SKU数据表。
- Rubin和RTX PRO Server中未闭合的Tensor字段继续保留未知；不是宣称厂商从未公开，也不是宣称该设备不支持这些精度。
- 更多GPU bin、片上资源、互联方向和时钟功率条件尚需逐字段整理。完整模型放置、量化格式、算子后端和持续测量属于后续计算与实测。

## 可复现的真实矩阵检查

`projection-bound` 从Qwen3官方config取实际Q投影形状。已登记27个场景，覆盖13个硬件配置的B=1/256，以及Qwen3-32B的8192-token投影。按A/W冷读、Y写回且各一次，计算单GEMM的资源下界。

```bash
python3 calculations/calc.py projection-bound --model qwen3-8b --device rtx4090 --batch 256 --format md
python3 calculations/calc.py projection-bound --model qwen3-32b --device h100-sxm --tokens 8192 --format md
python3 calculations/calc.py projection-bound --device m5-ultra-80gpu-512gb --batch 256 --format md
```

同一Qwen3-8B投影，B=1时AI约0.999512 FLOPs/byte，B=256时约227.555556；4090上的资源约束随之从内存转向计算，而H100在B=256时仍由内存服务下界主导。Mac输出明确的内存服务值和`null`计算／Roofline值。上述结果是该冷内存单算子情景，不是全模型时延或已测kernel性能。

## 模型存储格式不能直接选择硬件精度峰值

已锁定 V4 `inference/kernel.py` 的 `fp4_gemm_kernel` 明确将 FP4 E2M1 权重经 FP32 转为 FP8 E4M3，随后 `T.gemm(A_shared, B_shared, ...)` 使用 FP8 输入、FP32 累加；scale 在 K=32 子块后作用于 FP32 累加器。此参考路径不能匹配原生 FP4 Tensor 峰值。证据为来源锁中的 Flash／Pro kernel 原件；机器可读结果见 `routed_expert_format`，含 `native_fp4_peak_eligible=false`。这条限制来自所分析的执行路径，不是对其他原生 FP4 引擎的结论。


## 2026-09-09 H20型号容量与A800峰值复核

已下载并锁定[NVIDIA AI Enterprise release-7 Hopper vGPU文档](https://docs.nvidia.com/ai-enterprise/release-7/latest/infra-software/vgpu/reference/hopper.html)，页面标注2026-08-12更新。Table184–185标题为H20 SXM5 141GB，Table186–187为H20 SXM5 96GB。分别录入h20-sxm5-141gb和h20-sxm5-96gb，仅采用物理产品标题的名义GB；表内vGPU Framebuffer 144/98及MIG profile不能替代该字段，也不据此声称实际可分配内存。

此原件未提供可锁定的BF16/FP32累加dense峰值、显存带宽或功率，两条记录的peak_rates为空、带宽/功率为null。训练期限模块可以给出完整16byte Qwen8状态的理想容量下界1/2张，不能给出算力张数或完成时间；不将未区分容量的h20别名映射到任一型号。

再次检查已封存的[A800 40GB Active官方数据表](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-a800-40gb-active-datasheet.pdf)第2页，623.8仍只标Peak Tensor Performance，未闭合输入/累加/稀疏条件，原不可选记录保持不变。搜索结果中的148TFLOPS、4TB/s及A800 80GB数值未找到足以进入本表的NVIDIA官方精确口径，不采用第三方规格或类似型号推算。

## 2026-09-09 A800 INT8 稀疏口径补全

[NVIDIA官方产品页](https://www.nvidia.com/en-us/products/workstations/a800/)的Tensor Performance栏标1247 AI TOPS，脚注2明确Theoretical INT8 TOPS using sparsity，Tensor Cores特性段说明结构化稀疏。追加INT8 / accumulator unspecified / tensor / structured / integer记录，沿用已锁nvidia-a800-active-page原件；不作浮点FLOPs分母，不推算623.8的BF16或dense值。[证据提案](research/hardware-next-audit.md)。

## 2026-09-09 Atlas 800 A3整机范围

官方[800I A3](https://e.huawei.com/cn/products/computing/ascend/atlas-800i-a3)与[800T A3](https://e.huawei.com/cn/products/computing/ascend/atlas-800t-a3)分别列4.48/6.0PFLOPS FP16和8.96/12.0POPS INT8、8×128GB，按npu_aggregate与npu_count=8录入，不除8制造单芯片spec。累加/稀疏/执行单元unknown，3.2TB/s未明确单颗/整机范围留空；不进入精度明确Roofline或单设备训练下界。900 A3原件也锁定，307.2/288.7条件待核仅留研究表。

## 逐字段登记检查入口

```bash
python3 calculations/calc.py hardware --audit --format md
python3 calculations/calc.py hardware --audit --format json
```

[生成审查表](results/hardware-audit.md)与[逐字段 JSON](results/hardware-audit.json)区分“值及来源位置已登记”“有值但缺独立字段来源”“未录值”。这是登记结构检查，不替代逐条阅读官方材料；空值不会被自动解释成厂商未披露，来源指针也不会自动解决不同日期或配置的冲突。浮点峰值准入逐行列出拒绝原因，整数 TOPS 继续独立保留。

2026-09-09 首轮结构检查发现17个已填功率值没有独立字段来源位置，后续补入 `power_evidence`，不能把内存字段的引用位置移用为功率证据。另外更正B200/B300四条结构化稀疏峰值的派生说明：36 PFLOPS整机除8得到4500 TFLOPS/卡；只有dense行再除2得到2250。原峰值数值未变，修复的是稀疏行错误复用dense派生公式的证据文案。


本轮已将上述17条中的15条NVIDIA功率来源补入公共目录，并在可读规格表中显示独立功率出处；未改变功率值。其余两条华为记录随专项补丁处理。各厂商的逐型号证据与具体剩余工作见 [NVIDIA](research/hardware-nvidia-closure.md)、[Apple](research/hardware-apple-closure.md)、[昇腾](research/hardware-ascend-closure.md)。这些报告的代表配置审查不能替代原计划尚未覆盖的型号或档位。


## 2026-09-09 公共目录合并

已合并Apple71条GPU档位/容量、NVIDIA3条A80080GB物理身份和华为3条芯片/板卡/超节点记录，新增22份公共锁定原件。Apple97组合未跨GPU档位做容量笛卡尔积，M3Ultra历史512GB容量有独立来源，M5Ultra供应日期单列。Atlas350板卡、初代910芯片与900A3最大384NPU范围分别登记，未知峰值口径继续拒绝进入FLOPs计算。原17条已填功率均补齐独立来源位置；新增910的310W明确不是板卡TDP或官方最大功率。

H02七款原定SKU已补六卡Boost、七卡互联证据及功率来源。Server的Tensor累加/稀疏仍在所查材料中未披露；三款PRO没有NVLink字段不等于明确不支持。RTX4090/5090和RTX6000Ada明确不支持的记录与这些未知记录分开。H01/H03的具体bin、完整峰值及聚合带宽缺口继续保留。


## Apple 桌面整机适用范围补证

已将[桌面交叉审查](research/hardware-apple-desktop-audit/review.md)的8份官方原件、30条整机/GPU/内存绑定合入公共来源和目录，不重复增加数值设备。`configuration_evidence`逐项保存整机、GPU核、容量、带宽和来源位置；校验器拒绝错配。M4 8 GPU/32GB的MacBook Air证据不适用于双口iMac，后者只核实16/24GB。M1 mini/iMac、M3/M4 iMac和M2Ultra Mac Pro与原有组合交叉验证通过。可读表和JSON审查输出都展示这些适用范围。


## 官方白皮书第二批：稠密档位与设备范围

已合并[A100/B200补证](research/hardware-nvidia-h01-round2.md)及[昇腾白皮书补证](research/hardware-ascend-followup.md)，新增7份公共官方原件。A10040GB PCIe/SXM4分别为250/400W，两者1555GB/s；原补丁重复FP16累加记录经统一校验去重，每型号11条独立峰值。B2001000W由官方PCF的per individual GPU字段支持，形态SXM6，不使用该表其他有单位疑点的性能行。

Atlas A2白皮书单处理器313/376TF16、64GB/1600GB/s/最大400W，Atlas800T A3和900A3按8NPU节点及白皮书性能档分别记录。它们明确dense，但累加/执行单元仍unknown，FP32独立宣传值未强行分配到FP16档。800T两档15.4/16.2kW是整机最大输入，不能除8当单NPU功率。384×752=288.768不按普通一位四舍五入得到产品页288.7，差异继续保留；A3带宽聚合范围也未解决。


## 950分核数计算能力档

[950能力档补证](research/hardware-950-profiles.md)已合并PR32/28 Cube、DT36/32/28 Cube五档，每档23条Cube/Vector/合计峰值。它们是芯片计算能力profile，不是可订购板卡；family_memory_options保留未绑定选项，主容量和带宽留空。整数位宽、浮点格式与合计宣传值分别登记；未知累加/稀疏不因补齐记录而进入Roofline。


## GB/Rubin独立profile与字段来源修复

[第三批NVIDIA提案](research/hardware-nvidia-h01-round3.md)已合入GB200NVL72、GB300Superchip、RubinUK22TB/s、A100CTS500W和普通A80040PCIe。GB300混合1TB没有填写GPU显存；NVFP4 dense30PF/sparse40PF按官方直接两值保留。RubinUK的50PF inference无稀疏脚注，保持unspecified，不从US移用。CTS增加TDP不推高峰值。

[独立H05审查](research/h05-cli-delivery/REPORT.md)针对此前131设备快照逐峰值核对，提出的带test guard补丁已全部匹配后合并：补GB200换算、原始PFLOPS/POPS单位、H200整数单位解释和A10080GB SKU佐证，数值/精度/范围不变；来源锁一条误写CloudMatrix的注释已更正。该审查不是当前150配置的全部字段验收，也不把哈希/结构通过当作来源语义证明。H05/H07待原范围继续审查。


## H03最后公开来源与H05时钟证据

[H03最后公开审查](research/h03-final-public-review.md)已取得800I A3白皮书实际07版（页面标签04），新增8NPU FP16 4480/FP32 1200TFLOPS dense整机和14.6kW输入功率，累加/单元仍unknown。公开兼容接口实际HTTP200的空结果与403认证检查分开保存，空结果不推断不存在、也不归因于登录。

[H05时钟与累加精度审查](research/h05-clock-accumulator-audit/REPORT.md)补52条clock_evidence、20条H100直接accumulator/SKU峰值对应；8条H100未被表格列入时钟域的操作改为有范围未知。可读表逐峰值显示时钟来源，JSON保留完整证据。此次只改证据字段，不改峰值键/数值；H05全局仍有剩余映射待核。

H03合入后的[验收绑定](inventory/h03-source-review.json)已独立重算通过：22配置181峰值、12来源与24次公开查询原件；原H03资料审查已勾选。已有数值冲突和有限披露项按上述边界保留，H05/H07仍单独待验收。


## H07来源验收与H100 NVL证据补齐

H07已验收当前151配置471峰值的来源追溯与证据类型分离：96硬件归档原件、84目录来源、1001个递归字段指针均有绑定，73条availability位置已补齐，14项规格差异独立登记。参见[验收记录](inventory/h07-source-review.json)及[版本差异表](research/h07-review/version-differences.json)。NVIDIA与Apple受证据补丁影响的验收绑定已保护性回放重算，历史快照保留；这不证明H05全部精度映射已完成。

[H100 NVL与scalar映射](research/h05-next-review/REPORT.md)已合入：产品Base1080/Boost1785MHz，400W需450/600W电缆配置模式；产品Boost不能当作每种Tensor峰值实际时钟。四条H100 FP32/FP64 scalar FMA用官方SM数、指令吞吐及对应时钟重建，舍入吻合。NVL简报3938GB/s与网页3900GB/s的精度差异已登记，保留网页现值。


## H05最终验收与硬件基础收口

H01–H07已按当前151配置471峰值全部验收，见[H05正式证据](inventory/h05-source-review.json)。471条逐峰值全部有语义审查，5181项字段中3806项在所引范围已核、1375项经有限来源检查仍未知。最终只补106峰值证据，不改变峰值数值、精度选择键或适用范围。

[Blackwell独立裁决](research/blackwell-bf16-independent/REVIEW.md)以固定CUTLASS dense/sparse明确支持组合消除BF16累加类型歧义；PTX描述符编码表不能做类型选项的任意组合。H100四条FP8/FP32附特定wgmma内部精度限制，产品名义类型与内部舍入分开。正文和可读表已同步这一解释。

H01现绑定37个NVIDIA来源；H07现核97硬件归档/85目录来源。硬件来源子集独立哈希允许后续新增模型源，整目录变更仍需重验。官方资料验收不声称持续时钟、运行功率、所有内部数值路径或实测性能已知。
