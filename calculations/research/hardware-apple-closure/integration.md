# H04 已公开 GPU 档位与内存组合补充包

2026-09-09 第二轮。保持H04原范围，不采用上一审计“收敛为代表配置即可关闭”的建议。此包将已核矩阵从26扩展至97个不同的Mac芯片家族/GPU档位/内存组合，新增71个device。GPU峰值未知仍是合规的资料审查结论，不是未完成理由。

## 可合并文件

- `additional-devices.json`：71条新device，结构与共享hardware.json兼容，新增availability为可选元数据。按device id追加。
- `additional-sources.lock.json`：11条新官方原件记录，路径从calculations根解析；按id追加共享来源锁即可。已有来源仍引用共享锁，不复制篡改。
- `availability-patches.json`：按device_id合并字段，并去重追加source_ids；现有M5Ultra256GB标9月22日、512GB标10月下旬。
- `gpu-memory-combinations.json`：97组合完整核对清单，包含已存在26条的真实id；不是将GPU和系列最大内存无条件相乘。
- `build_additions.py`：构建器包含逐bin已审阅容量列表，校验全部来源哈希并避免既有组合重复。共享合并后不应重新覆盖原追加包；脚本届时仅会发现剩余差集。

## 重要补全与来源边界

1. M3 Ultra 80 GPU / 512GB现已达到具体SKU证据标准：`apple-m3-ultra-power-config`（Apple支持102027）明确同一测试机的32 CPU、80 GPU、512GB；819GB/s来自同型号支持页。270W是整机墙上测试功耗，未填入GPU TDP。保留历史配置状态，不能声称2026-09-09新机在售。

2. M1/M2/M3 Pro的低GPU档、M1 Max24 GPU、M2 Max30 GPU、M1 Ultra48 GPU、M2 Ultra60 GPU、M5 Air8 GPU均有补充直接技术页。每bin仅列官方Memory及CTO允许容量。M2 Max96GB限定38GPU；M3 Max96GB限定30GPU；M5Ultra512GB限定80GPU。

3. M4 Pro64GB来自Mac mini，不能把16英寸MacBook Pro48GB上限推广成芯片家族上限。M5 Pro16GPU64GB也来自当前Mac mini页面；14英寸MacBook Pro对该档只列至48GB。每条保留实际来源整机范围。

4. 所有历史技术支持文档都是2026-09-09取得的官方页面快照，不声称是产品发布当天归档的HTML。页面的Year introduced、新闻稿发布日期、抓取日期和当前库存是四个不同字段。`official_configuration_documented`只证明官方列出过组合；`current_retail_availability=not_verified`不代表在售。M5Ultra则有直接未来上市窗口，明确标记announced_not_yet_available。

5. 同一GPU/容量可能对应不同CPU档位和整机。例如M1 Pro14GPU存在8CPU与10CPU；本包按GPU-bin/容量任务去重，不能用于推断CPU性能、整机持续频率或散热。iPad等非Mac整机不由这些Mac规格页面认证。

## 验收状态

已知缺失组合已从明确官方来源补到97项，并解决M3Ultra512GB具体档位来源。该矩阵覆盖本轮逐代Mac技术页出现的所有GPU bins及允许容量，不声称已穷尽从未查阅的全球历史订购/翻新SKU。H04原范围保持，父任务可据此继续审阅并合并；本子任务不把缩小范围当完成条件。M4Ultra与M6Pro/Max/Ultra仍无本轮可核官方产品记录，不用猜测创建device；检索未找到不等于断言从未公布。

验证：11份新增原件长度/SHA一致；97组合唯一；新增71条id唯一且来源均可解析；重点正例7组与禁止错误笛卡尔组合4组检查通过。未写共享硬件配置、共享lock、CLI、reproduce或outline。

## 已核GPU/内存组合

| 家族 | GPU核 | 内存GB | 带宽GB/s | device id | 来源 | 原表已有 |
|---|---:|---:|---:|---|---|---|
| m1 | 7 | 8 | None | m1-7gpu-8gb | apple-m1-base-specs | 新增 |
| m1 | 7 | 16 | None | m1-7gpu-16gb | apple-m1-base-specs | 新增 |
| m1 | 8 | 8 | None | m1-8gpu-8gb | apple-m1-base-specs | 新增 |
| m1 | 8 | 16 | None | m1-8gpu-16gb | apple-m1-base-specs | 是 |
| m1-pro | 14 | 16 | 200 | m1-pro-14gpu-16gb | apple-m1-pro-14-specs | 新增 |
| m1-pro | 14 | 32 | 200 | m1-pro-14gpu-32gb | apple-m1-pro-14-specs | 新增 |
| m1-pro | 16 | 16 | 200 | m1-pro-16gpu-16gb | apple-m1-pro-14-specs | 新增 |
| m1-pro | 16 | 32 | 200 | m1-pro-16gpu-32gb | apple-m1-pro-14-specs | 是 |
| m1-max | 24 | 32 | 400 | m1-max-24gpu-32gb | apple-m1-studio-specs | 新增 |
| m1-max | 24 | 64 | 400 | m1-max-24gpu-64gb | apple-m1-studio-specs | 新增 |
| m1-max | 32 | 32 | 400 | m1-max-32gpu-32gb | apple-m1-studio-specs | 新增 |
| m1-max | 32 | 64 | 400 | m1-max-32gpu-64gb | apple-m1-studio-specs | 是 |
| m1-ultra | 48 | 64 | 800 | m1-ultra-48gpu-64gb | apple-m1-studio-specs | 新增 |
| m1-ultra | 48 | 128 | 800 | m1-ultra-48gpu-128gb | apple-m1-studio-specs | 新增 |
| m1-ultra | 64 | 64 | 800 | m1-ultra-64gpu-64gb | apple-m1-studio-specs | 新增 |
| m1-ultra | 64 | 128 | 800 | m1-ultra-64gpu-128gb | apple-m1-studio-specs | 是 |
| m2 | 8 | 8 | 100 | m2-8gpu-8gb | apple-m2-base-specs | 新增 |
| m2 | 8 | 16 | 100 | m2-8gpu-16gb | apple-m2-base-specs | 新增 |
| m2 | 8 | 24 | 100 | m2-8gpu-24gb | apple-m2-base-specs | 新增 |
| m2 | 10 | 8 | 100 | m2-10gpu-8gb | apple-m2-base-specs | 新增 |
| m2 | 10 | 16 | 100 | m2-10gpu-16gb | apple-m2-base-specs | 新增 |
| m2 | 10 | 24 | 100 | m2-10gpu-24gb | apple-m2-base-specs | 是 |
| m2-pro | 16 | 16 | 200 | m2-pro-16gpu-16gb | apple-m2-pro-max-14-specs | 新增 |
| m2-pro | 16 | 32 | 200 | m2-pro-16gpu-32gb | apple-m2-pro-max-14-specs | 新增 |
| m2-pro | 19 | 16 | 200 | m2-pro-19gpu-16gb | apple-m2-pro-max-14-specs | 新增 |
| m2-pro | 19 | 32 | 200 | m2-pro-19gpu | apple-m2-pro-max-14-specs | 是 |
| m2-max | 30 | 32 | 400 | m2-max-30gpu-32gb | apple-m2-pro-max-14-specs | 新增 |
| m2-max | 30 | 64 | 400 | m2-max-30gpu-64gb | apple-m2-pro-max-14-specs | 新增 |
| m2-max | 38 | 32 | 400 | m2-max-38gpu-32gb | apple-m2-pro-max-14-specs | 新增 |
| m2-max | 38 | 64 | 400 | m2-max-38gpu-64gb | apple-m2-pro-max-14-specs | 新增 |
| m2-max | 38 | 96 | 400 | m2-max-38gpu-96gb | apple-m2-pro-max-14-specs | 是 |
| m2-ultra | 60 | 64 | 800 | m2-ultra-60gpu-64gb | apple-m2-studio-specs | 新增 |
| m2-ultra | 60 | 128 | 800 | m2-ultra-60gpu-128gb | apple-m2-studio-specs | 新增 |
| m2-ultra | 60 | 192 | 800 | m2-ultra-60gpu-192gb | apple-m2-studio-specs | 新增 |
| m2-ultra | 76 | 64 | 800 | m2-ultra-76gpu-64gb | apple-m2-studio-specs | 新增 |
| m2-ultra | 76 | 128 | 800 | m2-ultra-76gpu-128gb | apple-m2-studio-specs | 新增 |
| m2-ultra | 76 | 192 | 800 | m2-ultra-76gpu-192gb | apple-m2-studio-specs | 是 |
| m3 | 8 | 8 | 100 | m3-8gpu-8gb | apple-m3-base-specs | 新增 |
| m3 | 8 | 16 | 100 | m3-8gpu-16gb | apple-m3-base-specs | 新增 |
| m3 | 8 | 24 | 100 | m3-8gpu-24gb | apple-m3-base-specs | 新增 |
| m3 | 10 | 8 | 100 | m3-10gpu-8gb | apple-m3-base-specs | 新增 |
| m3 | 10 | 16 | 100 | m3-10gpu-16gb | apple-m3-base-specs | 新增 |
| m3 | 10 | 24 | 100 | m3-10gpu-24gb | apple-m3-base-specs | 是 |
| m3-pro | 14 | 18 | 150 | m3-pro-14gpu-18gb | apple-m3-pro-max-14-specs | 新增 |
| m3-pro | 14 | 36 | 150 | m3-pro-14gpu-36gb | apple-m3-pro-max-14-specs | 新增 |
| m3-pro | 18 | 18 | 150 | m3-pro-18gpu-18gb | apple-m3-pro-max-14-specs | 新增 |
| m3-pro | 18 | 36 | 150 | m3-pro-18gpu-36gb | apple-m3-pro-max-14-specs | 是 |
| m3-max | 30 | 36 | 300 | m3-max-30gpu-36gb | apple-m3-pro-max-specs | 新增 |
| m3-max | 30 | 96 | 300 | m3-max-30gpu-96gb | apple-m3-pro-max-specs | 是 |
| m3-max | 40 | 48 | 400 | m3-max-40gpu-48gb | apple-m3-pro-max-specs | 新增 |
| m3-max | 40 | 64 | 400 | m3-max-40gpu-64gb | apple-m3-pro-max-specs | 新增 |
| m3-max | 40 | 128 | 400 | m3-max-40gpu-128gb | apple-m3-pro-max-specs | 是 |
| m3-ultra | 60 | 96 | 819 | m3-ultra-60gpu-96gb | apple-m3-ultra-specs | 新增 |
| m3-ultra | 60 | 256 | 819 | m3-ultra-60gpu-256gb | apple-m3-ultra-specs | 是 |
| m3-ultra | 80 | 96 | 819 | m3-ultra-80gpu-96gb | apple-m3-ultra-specs | 新增 |
| m3-ultra | 80 | 256 | 819 | m3-ultra-80gpu-256gb | apple-m3-ultra-specs | 是 |
| m3-ultra | 80 | 512 | 819 | m3-ultra-80gpu-512gb | apple-m3-ultra-power-config | 新增 |
| m4 | 8 | 16 | 120 | m4-8gpu-16gb | apple-m4-base-specs | 新增 |
| m4 | 8 | 24 | 120 | m4-8gpu-24gb | apple-m4-base-specs | 新增 |
| m4 | 8 | 32 | 120 | m4-8gpu-32gb | apple-m4-base-specs | 新增 |
| m4 | 10 | 16 | 120 | m4-10gpu-16gb | apple-m4-base-specs | 新增 |
| m4 | 10 | 24 | 120 | m4-10gpu-24gb | apple-m4-base-specs | 新增 |
| m4 | 10 | 32 | 120 | m4-10gpu-32gb | apple-m4-base-specs | 是 |
| m4-pro | 16 | 24 | 273 | m4-pro-16gpu-24gb | apple-m4-mini-specs | 新增 |
| m4-pro | 16 | 48 | 273 | m4-pro-16gpu-48gb | apple-m4-mini-specs | 新增 |
| m4-pro | 16 | 64 | 273 | m4-pro-16gpu-64gb | apple-m4-mini-specs | 新增 |
| m4-pro | 20 | 24 | 273 | m4-pro-20gpu-24gb | apple-m4-mini-specs | 新增 |
| m4-pro | 20 | 48 | 273 | m4-pro-20gpu-48gb-mbp | apple-m4-mini-specs | 是 |
| m4-pro | 20 | 64 | 273 | m4-pro-20gpu-64gb | apple-m4-mini-specs | 新增 |
| m4-max | 32 | 36 | 410 | m4-max-32gpu-36gb | apple-m4-pro-max-specs | 是 |
| m4-max | 40 | 48 | 546 | m4-max-40gpu-48gb | apple-m4-pro-max-specs | 新增 |
| m4-max | 40 | 64 | 546 | m4-max-40gpu-64gb | apple-m4-pro-max-specs | 新增 |
| m4-max | 40 | 128 | 546 | m4-max-40gpu-128gb | apple-m4-pro-max-specs | 是 |
| m5 | 8 | 16 | 153 | m5-8gpu-16gb | apple-m5-air-specs | 新增 |
| m5 | 8 | 24 | 153 | m5-8gpu-24gb | apple-m5-air-specs | 新增 |
| m5 | 8 | 32 | 153 | m5-8gpu-32gb | apple-m5-air-specs | 新增 |
| m5 | 10 | 16 | 153 | m5-10gpu-16gb | apple-m5-air-specs | 新增 |
| m5 | 10 | 24 | 153 | m5-10gpu-24gb | apple-m5-air-specs | 新增 |
| m5 | 10 | 32 | 153 | m5-10gpu-32gb | apple-m5-air-specs | 是 |
| m5-pro | 16 | 24 | 307 | m5-pro-16gpu-24gb | apple-m5-pro-max-14-specs | 新增 |
| m5-pro | 16 | 48 | 307 | m5-pro-16gpu-48gb | apple-m5-pro-max-14-specs | 新增 |
| m5-pro | 16 | 64 | 307 | m5-pro-16gpu-64gb | apple-macmini-current-specs | 新增 |
| m5-pro | 20 | 24 | 307 | m5-pro-20gpu-24gb | apple-m5-pro-max-specs | 新增 |
| m5-pro | 20 | 48 | 307 | m5-pro-20gpu-48gb | apple-m5-pro-max-specs | 新增 |
| m5-pro | 20 | 64 | 307 | m5-pro-20gpu | apple-m5-pro-max-specs | 是 |
| m5-max | 32 | 36 | 460 | m5-max-32gpu | apple-m5-pro-max-specs | 是 |
| m5-max | 40 | 48 | 614 | m5-max-40gpu-48gb | apple-m5-pro-max-specs | 新增 |
| m5-max | 40 | 64 | 614 | m5-max-40gpu-64gb | apple-m5-pro-max-specs | 新增 |
| m5-max | 40 | 128 | 614 | m5-max-40gpu | apple-m5-pro-max-specs | 是 |
| m5-ultra | 64 | 96 | 1200 | m5-ultra-64gpu-96gb | apple-macstudio-current-specs | 新增 |
| m5-ultra | 64 | 256 | 1200 | m5-ultra-64gpu-256gb | apple-macstudio-current-specs | 是 |
| m5-ultra | 80 | 96 | 1200 | m5-ultra-80gpu-96gb | apple-macstudio-current-specs | 新增 |
| m5-ultra | 80 | 256 | 1200 | m5-ultra-80gpu-256gb | apple-macstudio-current-specs | 新增 |
| m5-ultra | 80 | 512 | 1200 | m5-ultra-80gpu-512gb | apple-macstudio-current-specs | 是 |
| m6 | 12 | 16 | 153 | m6-12gpu-16gb | apple-macmini-current-specs | 是 |
| m6 | 12 | 24 | 170 | m6-12gpu-24gb | apple-macmini-current-specs | 新增 |
| m6 | 12 | 32 | 170 | m6-12gpu-32gb | apple-macmini-current-specs | 是 |
