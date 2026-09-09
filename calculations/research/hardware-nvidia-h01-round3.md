# H01 第三轮：原形态范围补齐提案

2026-09-09。[机器可合并补丁](hardware-nvidia-h01-round3/catalog-merge-proposal.json)只新增5条设备/profile与3条来源锁，保留全部现有记录，不修改US Rubin19.2TB/s。5条设备已分别调用当前`validate_device`通过，峰值键无重复；随后另行核验来源原件SHA/bytes。两类检查的结果分别存于补丁`validation`。

|新增ID|范围与已核字段|明确未知/限制|
|---|---|---|
|gb200-nvl72|72GPU机柜GPU合计；GPU memory13.4TB、HBM合计576TB/s；15条声明精度记录；不是2GPU Superchip|功率/clock与未闭合accumulator继续未知；GPU memory为官方取整总量，不包含Grace LPDDR|
|gb300-superchip|2GPU+1Grace组成；NVFP4 dense30PF/sparse40PF为官方直接声明|所查Superchip段落仅给HBM3E+LPDDR5X混合1TB，不当成GPU HBM；GPU-only容量/带宽保留null。架构max288GB/GPU不自动等于此Superchip选定memory bin|
|rubin-22tb-uk-product-profile|单GPU UK preliminary profile：288GB/22TB/s；NVLink3.6TB/s；10条精度记录|不覆盖US19.2TB/s；UK inference50PF未配sparsity脚注，因此该行unspecified；其他带脚注2的Tensor行dense，accumulator未知|
|a100-80gb-sxm-cts-500w|官方A100页明确CTS热设计SKU允许最高500W；与standard400W独立|保持原A100公开峰值，不推断500W带来更高clock/TFLOPS|
|a800-40gb-pcie|官方AI Enterprise5.0 Appendix A.2明确普通PCIe40GB物理型号|不是Active40GB；只录身份/容量，峰值、带宽、功率和冷却方式仍未知|

GB200 rack峰值采用[官方产品页](https://www.nvidia.com/en-us/data-center/gb200-nvl72/)机柜列，scope计72GPU；该表原脚注明确相应dense=sparse/2。GB300则使用[官方Blackwell Ultra架构文章](https://developer.nvidia.com/blog/?p=104887)Superchip段落直接给出的30/40PF，不能照搬除2规则。后者的Table2还给Blackwell Ultra架构最高1400W，但文章同时提醒SM/HBM随SKU变化；本提案不将架构上限当b300-sxm板卡确切功率。

[Rubin UK表](https://www.nvidia.com/en-gb/data-center/vera-rubin-nvl72/)与US表存在两类差异：带宽profile，以及inference50PF是否有匹配的sparse脚注。二者均如实保留，不能借US脚注补UK profile。UK的FP32 SGEMM400TF、FP64 DGEMM200TF标明Tensor Core-based emulation，不记成native vector峰值；native FP32/FP64仍130/33TF。

## 检查结果

- gb200-nvl72：15个唯一峰值键，validate_device通过。
- gb300-superchip：2个唯一峰值键，validate_device通过。
- rubin-22tb-uk-product-profile：10个唯一峰值键，validate_device通过。
- a100-80gb-sxm-cts-500w：11个唯一峰值键，validate_device通过。
- a800-40gb-pcie：0峰值，身份记录validate_device通过。

共38条峰值，其中未闭合口径保留unspecified；无把unknown强制变为可选的操作。实际运行的validate_device与本报告同一当前源码；源SHA核对是另一道验证，不代替设备契约。

## 上轮提案更正

第二轮A10040GB提案从已包含FP16/FP16的基线复制后错误追加两条同键记录，主线validate_device发现重复。本轮已将独立round2提案/报告改为每卡11条，并实际对这两条设备调用validate_device通过。此前“63处引用验证”只指来源哈希，未代表设备契约验证；此处明确更正。

共享目录/来源锁仍由主线合并并全量复算，本轮未写共享文件。
