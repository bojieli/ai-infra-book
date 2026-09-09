# H04 桌面整机交叉审查

审计日期2026-09-09。此次独立阅读并锁定8份Apple支持原件，覆盖iMac M1、M3双/四口、M4双/四口、Mac mini M1/M2/Pro和Mac Pro M2 Ultra；另外在线复核当前iMac规格仍为M4。30条整机/GPU/内存绑定全部映射到现有97个组合，未发现需要新增数值device的遗漏。

## 最关键的整机限制

- iMac M3 Two ports：8 GPU，8/16/24GB，100GB/s；三项均已有。Four ports则10 GPU，同三种容量。
- iMac M4 Two ports：8 GPU，16/24GB，120GB/s；这就是8 GPU基础iMac，两项均已有。该iMac不能外推32GB。
- 现有M4 8 GPU/32GB仍有效，其证据是MacBook Air，而非iMac。同GPU档位不意味着整机内存菜单相同，补丁专门为该行加入限制说明。
- iMac M4 Four ports：10 GPU，16/24/32GB，120GB/s，均已有。
- M1早期mini：8 GPU，8/16GB，均已有。此官方页仍未披露内存带宽，不能据GPU档位同名自行填写。M1 iMac7/8 GPU各8/16GB也均已有。
- Mac mini M2 10GPU与M2 Pro16/19GPU、Mac Pro M2Ultra60/76GPU的内存选项，均与现表对应集合相符。

## 合并方式

`sources.lock.json`为8条可直接追加的官方来源；`device-evidence-patches.json`按id去重追加source_ids和configuration_evidence数组。configuration_evidence是新增可选元数据，若主schema暂不接受，可将这些映射仅并入研究来源报告；数值不变。末条M4 8GPU/32GB补丁只追加notes。`additional-devices.json`为空，避免为相同芯片/GPU/内存组合制造重复行。`coverage.json`给出30条完整绑定。未改共享文件。

## 有界覆盖结论

结合前两轮，97组合不再仅依靠MBA/MBP页面：MacBook Air、MacBook Pro、iMac、Mac mini、Mac Studio和Apple silicon Mac Pro这些Mac产品线的已核官方GPU/容量配置已有直接来源。此次明确指定的桌面遗漏检查已通过；可以将这些官方资料的GPU-bin/内存组合审查视为完成。

这一结论不等于每个CPU档位、SSD、颜色、机架外形、区域订购编号都单设device，也不声称当前全球库存；任务所需的GPU/容量组合按相同三元组去重。官方未核的新家族不建猜测行；本次结果不证明未来/从未公开的名称不存在。M5Ultra尚未上市与M3Ultra512GB历史支持仍沿用已合并状态。GPU精度峰值未知不是本资料审核的未完成项。

来源状态说明：支持页是本次取得的历史型号文档，非发布当日抓取原件；当前 https://www.apple.com/mac-pro/specs/ 跳转Mac总页，因此不从跳转推断现售状态或取消历史MacPro配置。

## 逐产品线对照

| 整机 | GPU档 | 内存GB | 带宽GB/s | 官方原件 |
|---|---|---|---|---|
| iMac 24-inch M1 2021 | [7, 8] | [8, 16] | 所查未披露 | [apple-imac-m1-specs](https://support.apple.com/en-us/111895) |
| iMac 24-inch 2023 Two ports | [8] | [8, 16, 24] | 100 | [apple-imac-m3-two-specs](https://support.apple.com/en-us/117733) |
| iMac 24-inch 2023 Four ports | [10] | [8, 16, 24] | 100 | [apple-imac-m3-four-specs](https://support.apple.com/en-us/117734) |
| iMac 24-inch 2024 Two ports | [8] | [16, 24] | 120 | [apple-imac-m4-two-specs](https://support.apple.com/en-us/121556) |
| iMac 24-inch 2024 Four ports | [10] | [16, 24, 32] | 120 | [apple-imac-m4-four-specs](https://support.apple.com/en-us/121557) |
| Mac mini M1 2020 | [8] | [8, 16] | 所查未披露 | [apple-mini-m1-specs](https://support.apple.com/en-us/111894) |
| Mac mini 2023 M2 | [10] | [8, 16, 24] | 100 | [apple-mini-m2-specs](https://support.apple.com/en-us/111837) |
| Mac mini 2023 M2 Pro | [16, 19] | [16, 32] | 200 | [apple-mini-m2-specs](https://support.apple.com/en-us/111837) |
| Mac Pro 2023 M2 Ultra tower/rack | [60, 76] | [64, 128, 192] | 800 | [apple-macpro-m2-specs](https://support.apple.com/en-us/111343) |
