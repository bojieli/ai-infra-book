# H01 第二轮：A10040GB 与 B200 功率闭合

2026-09-09。只写独立研究文件；基于当前131配置目录读取，本轮不改共享配置或来源锁。

[机器合并提案](hardware-nvidia-h01-round2/catalog-merge-proposal.json)新增2个A10040GB形态、22条精度峰值，补B200功率/形态，附4条source_lock_additions。63处字段source引用已逐一验证原件SHA与bytes；[原件manifest](hardware-nvidia-h01-round2/manifest.json)。

## 可确定并可合并

|项目|本轮闭合|官方依据|
|---|---|---|
|A10040GB PCIe|40GB HBM2、1555GB/s、250W、passive双槽、PCIe4.0×16、Boost1410MHz；11条明确precision/accumulator/sparsity峰值|[40GB PCIe Product Brief](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf) Table1/2；[June20数据表](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet.pdf)明确覆盖HGX/PCIe峰值，结合已锁nvidia-a100 Table4累加/稀疏字段|
|A10040GB SXM4|40GB HBM2、1555GB/s、400W、SXM4、Boost1410MHz；同样11条明确精度峰值|已锁nvidia-a100白皮书Table4明确A10040GB SXM4，June20数据表HGX/PCIe形态分别列功率|
|B200 SXM6|每GPU可配置至1000W、SXM6形态|[HGX B200 PCF Summary](https://images.nvidia.com/aem-dam/Solutions/documents/HGX-B200-PCF-Summary.pdf) p1明确每GPU180GB、8个SXM6；功率原文“Per individual GPU: Configurable up to 1000 W”|

A100并非按80GB卡除2拼出来。PCIe产品brief独立确认容量/带宽/时钟/功率，June20数据表同时列出两种40GB形态的峰值。额外FP16/FP16累加与FP16/FP32累加的相同312/624值由白皮书Table4直接证明；没有从宣传“AI TOPS”猜精度。

A100 PCIe NVLink需要一对邻卡及完整3座桥；其600GB/s是双向合计，不当单向有效服务。June20数据表将内存带宽取整为1.6TB/s，补丁采用同型号详细规格1555GB/s，保留取整差异。

B200 PCF由NVIDIA发布，虽然主题是碳足迹，其p1产品表明确了per-GPU功率范围，因此比nvidia-smi安装示例更适合作为power_evidence。**不整表导入**：同页FP32写600 PFLOPS，且整板带宽62TB/s与其他产品表口径不同；这些行不进入补丁。本轮只用清楚的GPU功率与SXM6形态，不据整机能耗反除GPU功率。

## 已查具体材料而未提供所需字段

|对象|本轮已读官方材料|本轮结论与保留未知|
|---|---|---|
|B300单GPU功率|[DGX B300 User Guide: Introduction](https://docs.nvidia.com/dgx/dgxb300-user-guide/introduction-to-dgxb300.html)，已下载；明确8×B300、8×288GB、整机14.5kW，另电源表15kW system max|本页没有每GPU TDP或Boost。不能把14.5kW/8、15kW/8、12×3.2kW电源额定值当GPU功率。保留null。|
|B200 GPU时钟|本轮HGX PCF产品表与官方搜索“B200 GPU Boost Clock”|PCF无Boost；搜索得到kernel测试/软件时钟状态，不是SKU峰值时钟。尚未获得可填Boost证据。|
|H20完整规格|官方release7 Hopper vGPU型号表，已锁；本轮检索H20 GPU specifications memory bandwidth power，及官方NIM支持表|型号/名义容量可用；所查材料无每SKU功率、带宽及精度峰值组合，不新增数值。搜索发现NVIDIA论坛帖子只由社区用户链接第三方，**排除**，不能把官方域名当官方规格作者。|
|Rubin Tensor累加|[官方Rubin架构文章](https://developer.nvidia.com/blog/inside-nvidia-rubin-gpu-architecture-powering-the-era-of-agentic-ai/)及上一轮US/UK产品表|本轮材料仍未逐峰值绑定accumulator；不得把Blackwell ISA适用范围直接移给Rubin。US19.2TB/s与UK/blog22TB/s冲突保留，FP64补丁已在上一轮交付，不重复添加。|

以上不是“厂商从未公开”的断言，而是具体已读材料的证据范围。

## 尚未完成的专项，不能记为已查未披露

1. B300单GPU产品brief/PCF/明确管理规格：本轮搜索未找到直接TDP条目；其他NVIDIA渠道尚未穷尽，不能把1400W等第三方值抄入。
2. B200/B300完整峰值时钟与功率配置的对应关系：软件运行截图只能证明该次配置，不自动给出理论峰值工作点。
3. Rubin精度累加的最新架构/ISA逐条交叉映射尚未完成；BF16/TF32等常见累加知识不能替代具体该架构、该公开峰值的证据链。
4. H20两种容量的官方产品级表仍缺；官方vGPU/NIM支持证据不能升级为完整芯片规格。

## 原系列/形态范围剩余清单

当前NVIDIA已有25条记录，原131总配置数来自更多厂商。此补丁合并后NVIDIA27条；不按记录数宣称H01完成。

- A100：补齐40GB PCIe与SXM4后，40/80GB×两主形态均覆盖。80GB SXM CTS500W是现官方脚注明确的另一热设计配置，当前400W标准profile不能代表它，仍应独立记录或明确scope排除依据。
- A800：已有40GB Active、80GB PCIe/液冷/HGX身份，但后三者性能/功率未知；官方vGPU另列普通PCIe40GB，不能与Active40GB合并，这个身份记录仍待纳入。
- Hopper：H100 SXM/PCIe/NVL、H200 SXM/NVL、H20 96/141GB身份已有；H20性能仍缺。
- Blackwell：B200/B300单GPU、GB200 Superchip、GB300 NVL72已有。原GB系列若要求系统与superchip均独立覆盖，GB200 NVL72、GB300 Superchip仍待独立建模；不能拿现有总量除法自动拼进单GPU。
- Rubin：当前只有US NVL72产品页的单GPU profile。官方页面还存在Superchip、NVL72系统、NVL4及另一22TB/s GPU profile；这些scope应分别登记，现有单GPU记录不代表整个Rubin系列已核完。

因此本轮是确定字段闭合，不是缩小H01范围后打勾。新增明确数据先合入，剩余细项按上表继续追踪。

更正：原提案复制的基线已经包含FP16/FP16两条记录，再追加造成重复；本提案已按完整精度键去重至每卡11条。此前63次校验仅是来源引用哈希校验，不是validate_device设备契约验证；主线发现后已修正。
