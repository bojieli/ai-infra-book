# H04 Apple 官方硬件基础表验收审计

> 后续状态：第二轮已按原H04范围继续补全，新增71条、合计97个GPU/内存组合，见 [补充包](hardware-apple-closure/integration.md)。以下首轮提出的“收敛为代表配置关闭”建议已被否决，不再作为验收依据；M3Ultra512GB具体档位证据也已补齐。

审计日期：2026-09-09。范围：当前 hardware.json 的 26 条 Apple 配置；逐条复核其 17 份已锁官方原件 SHA-256，并阅读 Chip、Memory、Configure to Order 与发布稿对应段落。另在线复核当前 Mac mini、Mac Studio 和 M6/M5 Ultra 发布页，独立归档两份新增发布稿。未改共享 hardware.json 或来源锁。

结论：26 条已录入配置的 GPU 核数、指定统一内存容量和已填带宽可验收为“官方规格样本表”；无已发现数值冲突。H04 若仍定义为所有已公开容量/核数 SKU 的穷举，则不能直接勾选完成：当前是选定配置，至少存在官方已公布但未录入的 M3 Ultra 512GB，以及其他低核数/较小容量 SKU。所查页面不披露精度明确的 GPU 峰值，是有证据的未知状态，不是永久阻塞。验收前应补下面的上市时间与历史配置范围说明。

## 状态定义

- 已核：明确的芯片/整机 SKU 与原件参数吻合；不代表实测性能或当前当地现货。
- 所查官方未披露：在本审计列明的规格/发布稿中未给字段，保留 null 或 unspecified；不是断言 Apple 从未公开。
- 尚未核：本轮未取得足够证据，例如所有地区现货、全部历史 SKU、精度峰值在所有开发者资料中的穷举检索。
- 冲突/范围差异：分开保存日期与 SKU，不用一个页面覆盖另一页面。

## 逐配置核查

所有下列容量为厂商 GB 标签与具体配置，CPU/GPU/OS 共享。带宽为十进制 GB/s；不等于应用有效吞吐。P 表示所列来源未披露输入精度、累加精度、稀疏性齐全的 GPU 峰值；不能用 Neural Engine TOPS、GPU Neural Accelerator 的倍数或电源瓦数替代。

| 配置 ID | GPU 核 | 内存 GB | 带宽 GB/s | 已核来源 | 状态与保留项 |
|---|---:|---:|---:|---|---|
| m2-pro-19gpu | 19 | 32 | 200 | [apple-m2-pro-max](https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/) | 数值已核；P |
| m2-max-38gpu-96gb | 38 | 96 | 400 | [apple-m2-pro-max](https://www.apple.com/newsroom/2023/01/apple-unveils-m2-pro-and-m2-max-next-generation-chips-for-next-level-workflows/) | 数值已核；P |
| m5-pro-20gpu | 20 | 64 | 307 | [apple-m5-pro-max-specs](https://support.apple.com/en-euro/126319) | 数值已核；P |
| m5-max-32gpu | 32 | 36 | 460 | [apple-m5-pro-max-specs](https://support.apple.com/en-euro/126319) | 数值已核；P |
| m5-max-40gpu | 40 | 128 | 614 | [apple-m5-pro-max-specs](https://support.apple.com/en-euro/126319) | 数值已核；P |
| m1-8gpu-16gb | 8 | 16 | 未披露 | [apple-m1-base-specs](https://support.apple.com/en-us/111883)、[apple-m1-launch](https://www.apple.com/newsroom/2020/11/apple-unleashes-m1/) | 核数/容量已核；带宽所查页未披露；官方2.6 TFLOPS精度/累加/稀疏未限定 |
| m1-pro-16gpu-32gb | 16 | 32 | 200 | [apple-m1-pro-max-specs](https://support.apple.com/en-us/111901) | 数值已核；P |
| m1-max-32gpu-64gb | 32 | 64 | 400 | [apple-m1-pro-max-specs](https://support.apple.com/en-us/111901) | 数值已核；P |
| m1-ultra-64gpu-128gb | 64 | 128 | 800 | [apple-m1-ultra-launch](https://www.apple.com/newsroom/2022/03/apple-unveils-m1-ultra-the-worlds-most-powerful-chip-for-a-personal-computer/) | 数值已核；P |
| m2-10gpu-24gb | 10 | 24 | 100 | [apple-m2-base-specs](https://support.apple.com/en-us/111867) | 数值已核；P |
| m2-ultra-76gpu-192gb | 76 | 192 | 800 | [apple-m2-ultra-launch](https://www.apple.com/newsroom/2023/06/apple-introduces-m2-ultra/) | 数值已核；P |
| m3-10gpu-24gb | 10 | 24 | 100 | [apple-m3-base-specs](https://support.apple.com/en-us/118551) | 数值已核；P |
| m3-pro-18gpu-36gb | 18 | 36 | 150 | [apple-m3-pro-max-specs](https://support.apple.com/en-us/117737) | 数值已核；P |
| m3-max-30gpu-96gb | 30 | 96 | 300 | [apple-m3-pro-max-specs](https://support.apple.com/en-us/117737) | 数值已核；P |
| m3-max-40gpu-128gb | 40 | 128 | 400 | [apple-m3-pro-max-specs](https://support.apple.com/en-us/117737) | 数值已核；P |
| m3-ultra-60gpu-256gb | 60 | 256 | 819 | [apple-m3-ultra-specs](https://support.apple.com/en-us/122211) | 数值已核；P；256GB为该快照配置，不是历史最大值 |
| m3-ultra-80gpu-256gb | 80 | 256 | 819 | [apple-m3-ultra-specs](https://support.apple.com/en-us/122211) | 数值已核；P；256GB为该快照配置，不是历史最大值 |
| m4-10gpu-32gb | 10 | 32 | 120 | [apple-m4-base-specs](https://support.apple.com/en-us/122209) | 数值已核；P |
| m4-pro-20gpu-48gb-mbp | 20 | 48 | 273 | [apple-m4-pro-max-specs](https://support.apple.com/en-us/121554) | 数值已核；P |
| m4-max-32gpu-36gb | 32 | 36 | 410 | [apple-m4-pro-max-specs](https://support.apple.com/en-us/121554) | 数值已核；P |
| m4-max-40gpu-128gb | 40 | 128 | 546 | [apple-m4-pro-max-specs](https://support.apple.com/en-us/121554) | 数值已核；P |
| m5-10gpu-32gb | 10 | 32 | 153 | [apple-m5-macbook](https://support.apple.com/en-mide/125405) | 数值已核；P |
| m5-ultra-64gpu-256gb | 64 | 256 | 1200 | [apple-macstudio-current-specs](https://www.apple.com/mac-studio/specs/)、[apple-m6-m5ultra-launch](https://www.apple.com/newsroom/2026/08/apple-introduces-m6-and-m5-ultra-for-a-big-leap-in-performance-and-ai-compute/) | 数值已核；P；已公布、尚未上市：2026-09-22 |
| m5-ultra-80gpu-512gb | 80 | 512 | 1200 | [apple-macstudio-current-specs](https://www.apple.com/mac-studio/specs/)、[apple-m6-m5ultra-launch](https://www.apple.com/newsroom/2026/08/apple-introduces-m6-and-m5-ultra-for-a-big-leap-in-performance-and-ai-compute/) | 数值已核；P；已公布、尚未上市：2026年10月下旬 |
| m6-12gpu-16gb | 12 | 16 | 153 | [apple-macmini-current-specs](https://www.apple.com/mac-mini/specs/)、[apple-m6-m5ultra-launch](https://www.apple.com/newsroom/2026/08/apple-introduces-m6-and-m5-ultra-for-a-big-leap-in-performance-and-ai-compute/) | 数值/2026-08-25公布已核；P；当前交货未核 |
| m6-12gpu-32gb | 12 | 32 | 170 | [apple-macmini-current-specs](https://www.apple.com/mac-mini/specs/)、[apple-m6-m5ultra-launch](https://www.apple.com/newsroom/2026/08/apple-introduces-m6-and-m5-ultra-for-a-big-leap-in-performance-and-ai-compute/) | 数值/2026-08-25公布已核；P；当前交货未核 |

## 日期、范围差异和不得合并的口径

1. M2 Max 38 GPU / 96GB / 400GB/s 已由同一官方发布稿正文及测试脚注交叉确认，不是把两个互斥 SKU 拼在一起。M3 Max 的 30 核/96GB/300GB/s 与40核/128GB/400GB/s也按 CPU/GPU 对应选项分别核实。M4 Pro 48GB 对应所引16英寸 MacBook Pro，不能称整个 M4 Pro 系列最高容量。

2. M6 和 M5 Ultra 的 2026-08-25 是官方新闻稿公布日期，不是推算日期。当前 Mac mini 规格分16GB的153GB/s与24/32GB的170GB/s，现表两行分开正确。当前 Mac Studio Configure to Order 明确256GB可选，512GB附36 CPU/80 GPU限制；因此64 GPU/256GB成立，不能把512GB套到64 GPU。

3. [新 Mac Studio 产品发布稿](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/)给出一般上市日2026-09-22、512GB配置2026年10月下旬。因此截至本次审计，两个 M5 Ultra 行都应标为已公布但尚未上市。现表参数并不因此无效；后续计算应区分前瞻规格方案与已交付设备。新增原件见 hardware-apple-closure/m5-ultra-product-launch.html。

4. [2025-03-05 M3 Ultra 发布稿](https://www.apple.com/newsroom/2025/03/apple-reveals-m3-ultra-taking-apple-silicon-to-a-new-extreme/)明确历史公布容量最高512GB。2026-09-08锁定的2025整机支持页列96/256GB。这是有日期的配置范围差异，不能把256GB写成芯片历史上限；也不能仅由发布稿最高容量推断所有GPU档位都可选512GB。现有两行256GB保持有效；若H04涵盖历史最大容量，应另纳入512GB历史记录，其具体GPU档位须再锁定直接技术规格/订购证据。新增原件见 hardware-apple-closure/m3-ultra-launch.html。

5. [M1官方发布稿](https://www.apple.com/newsroom/2020/11/apple-unleashes-m1/)确实披露2.6 TFLOPS，现表保存unspecified口径正确。不能笼统写“Apple未公开GPU FLOPS”；准确说法是本审计来源未提供可按输入/累加精度及稀疏性使用的GPU峰值。M1带宽同理只记录所查两页未披露，不用M6对M1的约数倍数反推。

6. M4 Ultra、M6 Pro/Max/Ultra：本次官方限定检索未获得直接产品技术规格/发布公告，不建虚构数值行；这不是证明这些名称从未公开。M1/M2等低核数和其他容量选项在现有官方页已出现但未全列，如M1 7 GPU、M1 Max 24 GPU、M5 Pro 16 GPU等。H04应明确“覆盖已公布芯片家族的指定计算配置”，避免把26行宣称成所有SKU。

## 明确验收建议

可关闭的范围：26条代表配置的官方参数真实性、M2 Max重点配置、统一内存共享口径、GPU与Neural Engine/Neural Accelerator分离、未知精度峰值不补造。P状态允许该范围完成。

关闭前的具体操作：为M5 Ultra两行补公布/上市状态；正文或来源报告承认M3 Ultra历史512GB与当前快照差异；把H04范围从含混的“已公开配置”明确为家族与代表配置，并保留历史512GB具体SKU核查为有界扩展。若坚持全SKU枚举，则H04仍未完成，原因是已知官方配置未全覆盖，而非GPU峰值null。

无需为了关闭H04制造GPU BF16/FP16/FP8/FP32峰值。后续Infra供给可用这些行计算容量与声明带宽下界，compute下界在精度/执行单元不明确时保持未知；真实有效带宽、OS占用、Metal分配上限和功率不属于这张官方基础规格表的已核结论。

## 固定来源完整性

以下17份原件均在本轮按共享锁验证SHA-256；新增两份原件使用本目录独立锁，不侵入共享manifest。

| source id | 固定原件 | SHA-256 |
|---|---|---|
| apple-m5-pro-max-specs | `sources/hardware/apple-m5-pro-max-specs.html` | `5c0da08ad90934fb8d6984d2861cd0ea5997b408fa9ff5a82210a1a0e5eff846` |
| apple-m2-pro-max | `../references/files/specs/apple-m2-pro-max.html` | `cd25f2f6f04f6be4eec9d75868c5379c396862a4426ce5f9961b9e8241150ea7` |
| apple-m5-macbook | `../references/files/specs/apple-m5-macbook.html` | `1a1da51c4075ffe74177d1cf34e086601e46081e79dd07582ebeee6818b6dd62` |
| apple-m1-pro-max-specs | `sources/hardware/apple-m1-pro-max-specs.html` | `5edd51dc8289603a48c9d0b603f9595f82410b6006029d0600f05ad0680d572a` |
| apple-m1-ultra-launch | `sources/hardware/apple-m1-ultra-launch.html` | `d3ce3d80815e9e34a9b34b33d5af0d9a5e5cc7a223c33bda287deba5a1359cea` |
| apple-m2-ultra-launch | `sources/hardware/apple-m2-ultra-launch.html` | `6275122f4a9b3b56526b16446d515f2cc4a813d9b56b5a76feb681d054ab7e8a` |
| apple-m3-pro-max-specs | `sources/hardware/apple-m3-pro-max-specs.html` | `07eef49ee32ae7a53dc0ccfe2db23601fe7a137e7e3559e9c28311cad5234db7` |
| apple-m4-pro-max-specs | `sources/hardware/apple-m4-pro-max-specs.html` | `3ecc587a1aa03802e248cb174e9f1f458f578b86db3c298daac4fd04ecc619d1` |
| apple-m1-base-specs | `sources/hardware/apple-m1-base-specs.html` | `71b2ef190748e1b75e36a4e03d08b8fe646cc4286cd6caffdc7c8bde5a4b9570` |
| apple-m1-launch | `sources/hardware/apple-m1-launch.html` | `9d549619f705460093d24960110e57d653316c7c0d1e49dd54c83e8eb0111ead` |
| apple-m2-base-specs | `sources/hardware/apple-m2-base-specs.html` | `474727dd68c486bd24a36cf20be8482757c7a54200ebb8e4daa8f00a981870f8` |
| apple-m3-base-specs | `sources/hardware/apple-m3-base-specs.html` | `cf59a6cf030514753308cd92186efda3332db7bf35e0974bcf659967df1e9788` |
| apple-m3-ultra-specs | `sources/hardware/apple-m3-ultra-specs.html` | `246efbb181b0fbdb65ff4ba9918fa2f9571ddaeb79dd94af8a5ba0e419dac989` |
| apple-m4-base-specs | `sources/hardware/apple-m4-base-specs.html` | `56fb49632876510e98c71f4fdce23ed489f8e377653e9003817027695edb8bb4` |
| apple-m6-m5ultra-launch | `sources/hardware/apple-m6-m5ultra-launch.html` | `1186e6e38c8178ea91745c0f587c5491fbe9e16d8bbfd23dbf8e107cbdaf7d90` |
| apple-macstudio-current-specs | `sources/hardware/apple-macstudio-current-specs.html` | `5324abf67eebdecbd9290f21a649082390b7796b2196b8845c08061b04eb6e65` |
| apple-macmini-current-specs | `sources/hardware/apple-macmini-current-specs.html` | `2807ca4664dc42820d0c7d009dcfc89fdd118ac9362dd2dd526266a80814da83` |
