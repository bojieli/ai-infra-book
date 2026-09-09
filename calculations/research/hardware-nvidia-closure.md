# NVIDIA H01/H02 字段闭合审计

审计日期：2026-09-09。只修改独立研究原件与本报告，不修改共享 hardware.json / sources.lock.json。当前目录 NVIDIA 22 个记录；本轮联网重新读取官方产品页、数据表及架构材料，14份原件及SHA见[本轮manifest](hardware-nvidia-closure/manifest.json)。

## 验收结论

**H02七个指定SKU已全部覆盖，可以验收“官方基础目录与已查未知边界”，不能写成所有精度峰值均已闭合。** 4090、5090、A6000、6000 Ada、PRO6000 Workstation/Max-Q有带累加与稀疏脚注的官方白皮书。Server的FP32、容量/带宽/功率可用，五个Tensor宣传行的稀疏口径未闭合，必须继续不可选。下文六卡Boost数值是已查且可以立即补入的字段，不能再笼统说“时钟仍待研究”。若H02验收要求所有录入峰值精确时钟，则先补这六条明确引用，再勾选。Server未披露的对应时钟应写null，不等待不存在于所查材料中的数字。

**H01目前不宜整包完成。** A800 80GB物理型号尚未入表、B200/B300单卡功率缺产品级证据、多个Tensor accumulator仍未闭合；Rubin必须继续按整组profile处理冲突。A10040GB、GB200 NVL72/GB300 Superchip等是否纳入应固定代表SKU范围，不能把“全系列”视为无限枚举。

## 逐SKU当前字段、未闭合字段与下一步

“未闭合”是目录状态，不等于厂商从未公开。下面区分：已核=锁中现有证据；可补=本轮已读官方材料明确给出；待查=本轮尚未完成专项核验；材料未给=已明确阅读的具体材料未提供所需字段。容量沿用官方GB标签，带宽单位TB/s为十进制。峰值数表示独立precision/accumulator/unit/sparsity记录数，不是完成百分比。

| SKU | 已核容量/带宽/功率；峰值记录数 | 尚未闭合或可补 | 来源/冲突 |
|---|---|---|---|
| rtx-a6000 (single_device) | 48GB / 0.768TB/s / 300W；11条 | 可补Boost 1800MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 白皮书19.5Gb/s×384bit与768GB/s不一致，已独立采用本型号数据表768；[nvidia-rtx-blackwell-pro](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) / [nvidia-rtxa6000-specs](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-rtx-a6000-datasheet.pdf) |
| rtx-6000-ada (single_device) | 48GB / 0.96TB/s / 300W；15条 | 可补Boost 2505MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-rtx-blackwell-pro](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) |
| rtx-pro6000-blackwell-maxq (single_device) | 96GB / 1.792TB/s / 300W；17条 | 可补Boost 2280MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 白皮书109.7与现产品110取整；3511 sparse FP4；[nvidia-rtx-blackwell-pro](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) |
| rtx-pro6000-blackwell-ws (single_device) | 96GB / 1.792TB/s / 600W；17条 | 可补Boost 2617MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 白皮书126/4030.4与产品125/4000取整口径并存；[nvidia-rtx-blackwell-pro](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/NVIDIA-RTX-Blackwell-PRO-GPU-Architecture-v1.0.pdf) |
| rtx4090 (single_device) | 24GB / 1.008TB/s / 450W；11条 | 可补Boost 2520MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-rtx-blackwell-whitepaper](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf) |
| rtx5090 (single_device) | 32GB / 1.792TB/s / 575W；13条 | 可补Boost 2407MHz；现有精度键均非unspecified；PCIe/片上资源结构化入表待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-rtx-blackwell-whitepaper](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf) |
| a100-80gb-sxm (single_device) | 80GB / 2.039TB/s / 400W；11条 | 精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-a100-page](https://www.nvidia.com/en-us/data-center/a100/) / [nvidia-a100](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf) |
| a100-80gb-pcie (single_device) | 80GB / 1.935TB/s / 300W；11条 | 精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-a100-page](https://www.nvidia.com/en-us/data-center/a100/) / [nvidia-a100](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf) |
| h100-sxm (single_device) | 80GB / 3.35TB/s / 700W；19条 | 精确峰值时钟/PCIe方向专项核验待做 | 峰值precision对应Boost需保留原白皮书时钟行；[nvidia-h100-page](https://www.nvidia.com/en-us/data-center/h100/) / [nvidia-h100](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) |
| h200-sxm (single_device) | 141GB / 4.8TB/s / 700W；9条 | vGPU型号表未给：带宽、功率、全部精度峰值；产品级规格仍待查 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h200-specs](https://dam-cdn.nvd.orangelogic.com/AssetLink/5o2qgy5d2835ve2pm11i62kv8mphqta8.pdf) / [nvidia-h100](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) |
| b200-sxm (single_device) | 180GB / 8TB/s / 未知；4条 | 未闭合：FP16/acc；功率专项待查；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-hgx-components](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html) / [nvidia-hgx-page](https://www.nvidia.com/en-us/data-center/hgx/) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) / [nvidia-blackwell-brief](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf) |
| b300-sxm (single_device) | 288GB / 8TB/s / 未知；4条 | 未闭合：FP16/acc；功率专项待查；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-hgx-components](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html) / [nvidia-hgx-page](https://www.nvidia.com/en-us/data-center/hgx/) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) / [nvidia-blackwell-brief](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf) |
| rubin-nvl72-product-profile (single_device) | 288GB / 19.2TB/s / 未知；8条 | 未闭合：BF16/acc,FP16/acc,FP8/acc,FP6/acc,TF32/acc,NVFP4/acc；功率专项待查；精确峰值时钟/PCIe方向专项核验待做 | US19.2/3与UK/blog22/3.6 TB/s，不合并；[nvidia-rubin-page](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/) |
| h100-pcie-80gb (single_device) | 80GB / 2.039TB/s / 350W；19条 | 精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h100](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) |
| h200-nvl (single_device) | 141GB / 4.8TB/s / 600W；9条 | vGPU型号表未给：带宽、功率、全部精度峰值；产品级规格仍待查 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h200-specs](https://dam-cdn.nvd.orangelogic.com/AssetLink/5o2qgy5d2835ve2pm11i62kv8mphqta8.pdf) / [nvidia-h100](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) |
| h100-nvl-94gb (single_device) | 94GB / 3.9TB/s / 400W；9条 | 未闭合：FP16/acc,FP8/acc；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h100-page](https://www.nvidia.com/en-us/data-center/h100/) / [nvidia-h100](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) |
| rtx-pro6000-blackwell-server (single_device) | 96GB / 1.597TB/s / 600W；6条 | 材料未给：FP4/FP8/FP16/BF16/TF32的对应稀疏脚注/峰值时钟；acc映射待ISA专项查证 | 网页液冷single-slot；Dec25数据表dual-slot，需按冷却profile区分；[nvidia-rtxpro6000-server-specs](https://dam-cdn.nvd.orangelogic.com/AssetLink/707m1632ypg4du1fj3ci1jo3h4w1k78j.pdf) / [nvidia-rtxpro6000-server-page](https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/) |
| a800-40gb-active (single_device) | 40GB / 1.5552TB/s / 240W；4条 | 未闭合：unspecified/acc/sparse,INT8/acc；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-a800-active-page](https://www.nvidia.com/en-us/products/workstations/a800/) / [nvidia-a800-active-specs](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-a800-40gb-active-datasheet.pdf) |
| gb200-superchip (gpu_aggregate) | 372GB / 16TB/s / 未知；15条 | 未闭合：NVFP4/acc,FP8/acc,FP6/acc,FP16/acc,TF32/acc,INT8/acc；功率专项待查；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-gb200-page](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) / [nvidia-blackwell-brief](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf) |
| gb300-nvl72 (gpu_aggregate) | 20000GB / 576TB/s / 未知；15条 | 未闭合：FP4/acc,FP8/acc,FP6/acc,FP16/acc,TF32/acc,INT8/acc；功率专项待查；精确峰值时钟/PCIe方向专项核验待做 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-gb300-page](https://www.nvidia.com/en-us/data-center/gb300-nvl72/) / [nvidia-ptx-isa-9-3](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html) / [nvidia-blackwell-brief](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf) |
| h20-sxm5-96gb (single_device) | 96GB / 未知 / 未知；0条 | vGPU型号表未给：带宽、功率、全部精度峰值；产品级规格仍待查 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h20-vgpu-release7](https://docs.nvidia.com/ai-enterprise/release-7/latest/infra-software/vgpu/reference/hopper.html) |
| h20-sxm5-141gb (single_device) | 141GB / 未知 / 未知；0条 | vGPU型号表未给：带宽、功率、全部精度峰值；产品级规格仍待查 | 未发现新的来源冲突；不表示已完成所有扩展字段；[nvidia-h20-vgpu-release7](https://docs.nvidia.com/ai-enterprise/release-7/latest/infra-software/vgpu/reference/hopper.html) |

## 本轮可立即合并的证据

### 六款H02的明确Boost时钟

|型号|Boost MHz|既有来源ID与位置|
|---|---:|---|
|rtx-a6000|1800|nvidia-rtx-blackwell-pro，Table 4印刷页45–47，GPU Boost Clock行；脚注1|
|rtx-6000-ada|2505|nvidia-rtx-blackwell-pro，Table 4印刷页45–47，GPU Boost Clock行；脚注1|
|rtx-pro6000-blackwell-maxq|2280|nvidia-rtx-blackwell-pro，Table 4印刷页45–47，GPU Boost Clock行；脚注1|
|rtx-pro6000-blackwell-ws|2617|nvidia-rtx-blackwell-pro，Table 4印刷页45–47，GPU Boost Clock行；脚注1|
|rtx4090|2520|nvidia-rtx-blackwell-whitepaper，Appendix A Table 3，GPU Boost Clock行；脚注1|
|rtx5090|2407|nvidia-rtx-blackwell-whitepaper，Appendix A Table 3，GPU Boost Clock行；脚注1|

可将peak_rates[].clock_basis从泛称official peak改为该型号明确Boost MHz，并保留source/locator；不声称运行中恒定达到该频率。PRO白皮书脚注原文：“Peak rates are based on GPU Boost Clock.” 新下载PRO PDF与原件是否相同见下方校验。

### A800 80GB物理身份可以先闭合

[NVIDIA AI Enterprise 5.0 User Guide](https://docs.nvidia.com/ai-enterprise/5.0/user-guide/index.html)明确有A800 PCIe 80GB、A800 PCIe 80GB Liquid Cooled的物理型号章节；还存在HGX 80GB型号。可分别新增仅含型号/形态/名义80GB的记录，峰值/带宽/功率保持null；不能把vGPU framebuffer、Active40GB或A10080GB当它的其他参数。此次已下载该完整官方页。

### Rubin当前US页的FP64行可补，不能借机替换整个profile

[US产品页](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/)单GPU列明确FP64=33 TFLOPS；未标作Tensor仿真行，与UK的FP64 DGEMM仿真行不同。可新增FP64/FP64/vector/dense、tera_ops_per_second=33，来源必须锁本轮页面并保留per-GPU scope；不拿67（双GPU）或2400（机柜）替代。其Tensor accumulator未因此得到证明。

## Rubin冲突：本轮已核，不能误报“更新成22”

[US页](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/)当前仍288GB/19.2TB/s、NVLink3TB/s；[UK页](https://www.nvidia.com/en-gb/data-center/vera-rubin-nvl72/)为288GB/22TB/s、NVLink3.6TB/s并标preliminary；[2026-07-21官方架构文章](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/)支持22TB/s/3.6TB/s架构profile。现有rubin-nvl72-product-profile明确采用US组且notes已记冲突，当前不是录入错误。不能称地区页数值相互覆盖，也不能把高带宽与另一组时钟/功率/峰值拼成一张卡。若新增22TB/s记录，必须另一个profile并清楚注明适用范围与preliminary。

US sparse NVFP4 inference50PF与dense training35PF是不同工作条件；不把前者除2生成25PF dense。BF16/FP16 dense4PF、FP8/FP6 dense17.5PF、TF32 dense2PF目前目录已有，本轮不是新增发现。

## 已查材料未给，与还没查清的明确区别

- **RTX PRO Server：** 现产品网页技术规格和Dec25官方数据表均已读取；表有Tensor数值而没有相应dense/sparse脚注，网页FP16/BF16=1PF不应直接当dense。相关精度ISA允许什么累加与产品峰值究竟采用何累加是两件事；本轮没有完成后者，仍不可选。官方AI factory参考架构PDF搜索结果出现，但实际打开返回404，不能作为已读证据。
- **H20：** 已封存vGPU兼容页能证明96GB/141GB物理型号，不能证明带宽/峰值/功率；仍缺官方产品规格，本轮未声称完成这些字段搜索。
- **B200/B300：** 本轮发现官方DGX安装指南nvidia-smi示例出现B200 power cap1000W；它是该示例系统的限制，不是独立SKU规格，不合入通用power_watts。B300产品级功率仍待直接规格或明确管理指南核验。
- **其余H01 accumulator：** 表中unspecified逐项已列。已有架构/ISA资料可能足够推导部分，但本轮没有重做这些证据链；不能把“未完成映射”说成“官方未公开”。
- **扩展字段：** 多卡互联带宽方向、PCIe lane、L2/SM、时钟表已有部分官方白皮书明确数据，但目录尚无统一逐字段结构。这是录入/适配任务，不是无限等待厂商给数；不应反复拖住H02基本目录验收。

## H02剩余的有限清单

1. 合并上表6款Boost条件及精确引用，避免所有峰值都仅写泛称official peak。
2. Server的Tensor条目保持不可选，并把5种precision对应稀疏/累加未闭合登记为显式evidence gap；不得移用Workstation峰值。
3. Server液冷外形的网页/旧PDF分歧登记到版本/冷却profile；其96GB、1597GB/s、600W不与Workstation的1792GB/s混合。
4. 原件hash复验、hardware catalog/结果复算后，可把H02勾为“7SKU官方基础表已审查，已查未知与冲突显式”。H05/H07还可独立追踪更深ISA映射/版本证据，不宣称所有数字已知。

本轮PRO白皮书SHA `ad6727c2875d1272aaa15cfeb3fd51b8e6666fc5625742fd1bd3bb076ed119d6`；与既有锁一致：True。所有下载以本轮manifest为准。

## 独立功率来源补丁及派生公式复核

本轮当前NVIDIA目录有15项非null power_watts（不是17；其余非NVIDIA由对应专项处理）。已逐项定位TGP/TDP/Maximum Power Consumption原行，提供[power-evidence-proposal.json](hardware-nvidia-closure/power-evidence-proposal.json)，每项可合入power_evidence={source_id,locator}，未套用memory来源。A100 SXM400W明确是standard configuration；500W CTS不得静默替换。H100 NVL400W是350–400W范围上限，非固定持续功耗。

B200/B300当前共享树的4条structured sparse derivation已是正确的 `36e15 / 8 GPUs / 1e12 = 4500 TFLOPS structured sparse`；本轮只读发现已被修正，不再报告为现存错误。对应dense公式应为 `36e15 / 8 GPUs / 2 sparse-to-dense / 1e12 = 2250 TFLOPS dense`。如合并到更旧快照，只改structured行，不能再除2。

## 机器可合并完整补丁

[目录合并提案](hardware-nvidia-closure/catalog-merge-proposal.json)包含7个H02设备更新、3个A80080GB物理身份、1条Rubin FP64峰值、8条来源锁新增。JSON顶层merge_contract明确按id合并、source_ids取并集、保留未涉及字段；31个字段source引用均逐一校验SHA/bytes。6款Boost写入clock及各峰值clock_evidence；Server的clock为明确未知。

互联字段不缩减原7SKU：A6000的NVLink112.5GB/s明确为双向合计；4090/5090官方完整规格明确NVLink不支持，Ada6000官方葡语规格也明确Nao；3款PRO数据表未列NVLink，保持unknown。PCIe代数、工作站/server的x16有直接表证；所选表未给GeForce电气lane及PCIe单向有效载荷，保持null，不把安装槽位或倍增宣传换成实测服务。
