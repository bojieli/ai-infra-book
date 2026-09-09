H05 时钟与累加器字段专项审计（2026-09-09）

本轮提供独立 RFC6902 补丁，未修改共享目录。检查 H100 SXM/PCIe/NVL 的47条峰值，并对 A10040GB 两形态的22条峰值仅补时钟来源；不声称完成全部 H05。

可合并内容：52条 `clock_evidence`，8条不恰当的 `clock_basis` 改为有范围的未知，20条明确累加器/产品峰值的 `supporting_evidence`。不改变任何峰值数值、精度键、稀疏性、资源范围，也不补造未知累加类型。

| 对象 | 已核内容 | 保留边界 |
| --- | --- | --- |
| H100 SXM | FP8/FP16/BF16/TF32 Tensor 1830MHz；FP64 Tensor与FP32/FP64 non-Tensor 1980MHz | 共15条峰值；不是运行时持续频率 |
| H100 PCIe80GB | 相同明确运算域分别1620/1755MHz | 共15条峰值；不转用到NVL94GB |
| 两款H100各4条 | INT8 Tensor两条、FP16/BF16 non-Tensor各一条 | 原有clock_basis套用了表中未列出的域，本补丁明确改为unknown |
| A10040GB PCIe/SXM4 | 精确产品Boost均1410MHz，各11条峰值附来源 | 仅产品Boost关联，不称逐指令实测时钟；不套到80GB/CTS |
| H100显式累加器 | 两SKU各10条FP8/FP16/BF16 Tensor峰值 | Table3行标题明确accumulate，直接映射对应SKU列 |
| H100其余累加器 | TF32/INT8/FP64 Tensor及Vector行仍需产品rate与指令映射 | PTX合法类型与non-Tensor名称本身不足以完成证明 |
| H100 NVL | 保留9条峰值原值及未知 | 不转用Table3中两个80GB产品的时钟与累加器列 |

直接依据是 [H100白皮书v1.04 Table3](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf) 印刷/物理页39–40，其两行时钟标签明确列出适用运算域。FP8、FP16分别列FP16/FP32累加，BF16列FP32累加。页25 Figure11已经渲染检查，但图中没有足以补齐这些缺项的显式累加器标签，不据图形颜色猜测。

A10040GB PCIe采用[官方产品简报](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf) Table1产品时钟；SXM4采用已锁Ampere白皮书Table4。PTX官方在线页本轮确认版本9.3；现有锁内指令证据保留为受限的类型支持，不新宣称产品吞吐映射完成。

文件：`proposed-hardware.patch.json`含145条操作与设备/完整峰值测试保护；`field-audit.json`逐69条记录状态；`source-manifest.json`含4个既有官方原件URL/SHA；`tests.json`记录真实验证。`h100.layout.txt`为锁内PDF的排版文本派生件，`h100-p25.png`为同一原件第25页渲染，均不是新的独立原始来源。

验证：实际顺序应用补丁并通过全部guards，与预期对象一致；150条设备逐条通过validate_device；所有峰值键和值保持不变；4个原件的SHA256和bytes均通过。结构验证不是来源内容证明，未执行吞吐实验或全量测试。H05仍有上述受限unknown以及其他家族待核字段。
