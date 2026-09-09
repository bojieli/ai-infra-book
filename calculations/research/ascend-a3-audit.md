# 昇腾 A3 官方整机规格与资源范围审计

2026-09-09。现有目录的四条 Huawei 记录是 950PR/950DT 规格上限与 Atlas 300I A2 的32GB/64GB板卡，没有以下 A3 整机记录。

## 可新增整机输入，不能改名为芯片 SKU

| 官方型号 | 范围 | NPU | 名义片上内存 | FP16 峰值 | INT8 峰值 |
| --- | --- | --- | --- | --- | --- |
| [Atlas 800I A3](https://e.huawei.com/cn/products/computing/ascend/atlas-800i-a3) | 单台10U服务器 | 8颗昇腾910 | 8 × 128GB | 4.48 PFLOPS | 8.96 POPS |
| [Atlas 800T A3](https://e.huawei.com/cn/products/computing/ascend/atlas-800t-a3) | 单台10U服务器 | 8颗昇腾910 | 8 × 128GB | 6.0 PFLOPS | 12.0 POPS |
| [Atlas 900 A3 SuperPoD](https://e.huawei.com/cn/products/computing/ascend/atlas-900-a3-superpod) | 最大12计算柜＋4总线设备柜 | 最大384颗昇腾910 | 最大384 × 128GB | 307.2/288.7 PFLOPS | 本页未列 |

以上都来自各产品页技术规格表，单台800系列和多台组成的384卡逻辑超节点必须分开。宣传中的48TB不是一台800系列服务器的容量；128GB也不是整台服务器总容量。不得把网页只称的“昇腾910”扩展为精确910C bin。

800I/T 页面把浮点单位误写为 PFLOFPS，前文特性处另写正确的 PFLOPS，二者数值一致，可按 FP16 PFLOPS 记录并保留 reported 原文。INT8 保留整数 POPS 换算为 TOPS，不当 TFLOPS。

## 仍缺证据

三个页面都没有把上述峰值绑定到累加格式、dense/structured 或 Cube/Vector 分解。建议 input_precision 按 FP16/INT8 明确记录，其他三项全部 unspecified，禁止当前 FLOPs Roofline 选择器使用。INT8 的 operation_kind 必须 integer。

800I/T 的片上内存行均同时列出 8 × 128GB 和3.2TB/s，但未明确后者的单颗/整机范围。900的对应行也给3.2TB/s。这提示其可能是每颗接口值，但推断不是已证实字段；待补范围清晰的技术白皮书前，aggregate bandwidth_bytes_per_second 应为 null，不能填3.2TB/s，也不乘8或384。双向784GB/s是D2D互联，不能充当显存接口带宽。

900 A3 的307.2/288.7没有在产品页明确两种配置或模式对应关系；不选高值、不平均，不由总数除384生成单NPU峰值。独立提案保留原字符串，暂不生成 numeric peak_rates。

官方800T A3技术白皮书07 [入口](https://e.huawei.com/cn/documents/products/computing/90b631ded60d42b09bedfc9b790f355b) 标注理论规格与实测有差异；800T和900白皮书入口的浏览预览未提供正文，展示下载表单，本轮未提交用户资料或获取受限正文。不能宣称白皮书证实了上述缺项。

## 合并结构要求

相邻 `ascend-a3-proposal.json` 给出两台800整机的数值记录与900待核字段。它不是当前 catalog 可直接接受的格式：现有 scope 仅有 single_device/gpu_aggregate。应先显式支持 npu_aggregate+npu_count，或用通用 accelerator_aggregate+accelerator_kind+accelerator_count，并检查报告、训练期限、容量计算及所有使用gpu_count的地方。不能为了通过校验而将整机标为single_device，或把NPU放进gpu_count。

容量1024GB仅是8 × 128名义容量合计；不意味着单个张量可跨NPU统一分配，也不证明逐卡可放置。功率上限未知，交流电压不是功率。

## 原件封存

`ascend-a3-sources/manifest.json` 保存三份公开产品页的URL、下载时刻、SHA-256、bytes和相对路径。原始HTML位于同目录，尚未写入共享sources.lock.json。应在采用提案时再合并来源锁并运行来源校验与结果重现。
