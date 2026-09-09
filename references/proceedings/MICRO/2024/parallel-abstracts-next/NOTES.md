# MICRO 2024 第二批并行摘要筛读

本批锁定程序序号 **2、3、51、52、75、121**。对照任务开始时的 canonical 41 篇摘要快照及上一批 41/53/87/88/111/119，六项均未重复。实际新增 **5 篇完整一手摘要、5 份作者公开 PDF（共 76 个物理页）**；只读各 PDF 的第 1 页摘要与文献身份，**正文阅读为 0 页**。Atomic Cache（51）完整摘要未取得，不能计入已筛读。

原始响应、提取文本、实际阅读的字符范围与图片散列分别见 `sources.json`、`abstracts.json`、`reading.json`。`input-*.json` 与 `previous-batch-abstracts.json` 是开始时快照，不能假设其他代理集成后共享文件仍保持这些状态。全部文件只写入本目录；没有修改共享索引或大纲，没有提交 Git，没有执行第三方代码。

| 序号 / DOI 尾段 | 论文 | 本次结果 | 作者公开稿身份与范围 |
| --- | --- | --- | --- |
| 2 / 00012 | Elastic Translations | 完整摘要；备查 | 第一作者域名的 19 页 preprint；标题及 8 位作者与 publisher metadata 对应。合作者条目确认 MICRO 2024，但条目的 PDF 链接指向出版社，并非本次归档地址。 |
| 3 / 00013 | Distributed Page Table | 完整摘要；备查 | 合作者发表列表直接链接的 14 页稿；第 1 页印有同一 DOI 和正式页码 36。 |
| 51 / 00056 | Atomic Cache | 完整摘要未取得 | 机构页面 HTTP 403；出版社 HTTP 202、响应体 0 字节。保留失败原字节，不用二手讲座报道替代。 |
| 52 / 00057 | CARS | 完整摘要；备查 | Purdue 合作者页面直接链接的 14 页稿；4 位作者相符，网页与 PDF 摘要的百分比有冲突。 |
| 75 / 00078 | ThreadFuser | 完整摘要；备查 | Purdue 合作者页面直接链接的 14 页稿；4 位作者相符，同时读了作者网页的完整摘要。 |
| 121 / 00120 | NDPExt | 完整摘要；后续候选 | 清华合作者目录下的 15 页稿；第 1 页有同一 DOI、正式页码 1648 和 4 位作者。 |

表中 DOI 前缀均为 `10.1109/MICRO61859.2024.`。归档日期为 2026-09-09 UTC；会议论文的 metadata 日期为 2024-11-02，不把网页版权年份、下载时间或 PDF 文件修改时间当作论文的新版本日期。作者托管的正式排版稿也不等于已证明与出版社文件逐字节相同。

## 摘要筛选判断

**Elastic Translations** 关注翻译粒度：已有硬件支持的中间大小翻译，需要 OS 的分配与运行时选择机制才能用起来。摘要明确实现范围是 ARMv8-A 上的 Linux/KVM；可以备查页表、TLB 与粒度之间的关系，不能直接当成 GPU HBM 或 PagedAttention 的证据。本批未读正文里的实验机器和负载。[第一作者公开稿](https://site.psomas.xyz/assets/files/elastic-translations-preprint.pdf)

**Distributed Page Table** 把页表项分散在物理地址空间，缓解哈希表扩容等开销，同时引出页表项与数据页的地址冲突。这里的 distributed 不是跨节点分布式服务。适合作为“元数据也占容量、也产生访问”的背景，暂不增加通用页表专题；三种冲突处理方法仅在摘要中确认名称，未读实现与评估。[合作者公开稿](https://zoon17.github.io/pdfs/DPT_micro24.pdf)

**CARS** 的有用关系是：函数 ABI 的寄存器 spill/fill 消耗带宽与存储；把一部分寄存器文件当栈又会占用原本用于并发的空间，需要与隐藏延迟的并发度权衡。但这是专门的硬件机制，摘要中的函数调用程序不能直接代表 LLM 推理。保留为第 4、5 章备查，不作为现有框架可直接启用的功能。[作者公开稿](https://engineering.purdue.edu/tgrogers/publication/kang-micro-2024/kang-micro-2024.pdf)

CARS 存在尚未解决的摘要版本差异：PDF 的性能/能效提升为 **26% / 28%**，作者网页为 **25% / 30%**。原文各自保留在 `paper-052-abstract.txt` 与 `cars-author.txt`，机器核验也分别检查这些字符串。没有依据判定哪个是最终修订，因此不在书中选用任何一组数字。网页的 Tim Rogers 与 PDF/metadata 的 Timothy G. Rogers、作者脚注的当前单位差异均作身份说明保留。[作者网页](https://engineering.purdue.edu/tgrogers/publication/kang-micro-2024/)

**ThreadFuser** 在投入 CPU→GPU 移植之前分析执行轨迹中的分支发散与同步，并可接入 GPU 模拟器。可用于说明移植前要判断执行特征；摘要不能证明任意 MIMD 程序都适合 SIMT，也不能把分析框架写成自动生成最优 GPU 内核的编译器。书当前先教简单推算，故仅备查，不增加模拟器实验。[作者公开稿](https://engineering.purdue.edu/tgrogers/publication/alawneh-micro-2024/alawneh-micro-2024.pdf)

**NDPExt** 是本批唯一正文候选：增加 CXL 容量以后，缓存元数据、位置与复制仍要一起算。摘要中的架构方向是 **3D NDP 栈内 DRAM 作为 CXL 扩展内存的缓存**；以粗粒度 stream 减少 metadata，并按观测的 miss 行为配置容量、放置和复制。它可能给现有第 4 章或第 9 章的容量/搬运取舍提供一个反例，但只有需要该反例时才值得继续读。不能改写成普通 KV 内存池已经实现的机制，也不能根据摘要采用性能倍率。[作者公开稿](https://nas.iiis.tsinghua.edu.cn/~gaomy/pubs/ndpext.micro24.pdf)

## 获取与验证边界

本批保存 **11 次原始 HTTP 响应：9 次 200、1 次 403、1 次 202 且空响应**。Atomic Cache 另一次浏览工具打开显示 JavaScript/机器人验证挑战，该观察单列在 `acquisition-notes.json`，没有伪装成已归档的 HTTP 原始响应。没有绕过验证，也没有继续以非一手页面填充缺口。

五篇 PDF 摘要均来自物理第 1 页左栏，以 Poppler 固定裁剪坐标提取，保留原换行、合字与连词；没有将右栏正文混入摘要。五张第一页图片均实际查看过标题、作者和摘要区域。导出图像/文本中附带的正文或图表不算正文已读，公开稿的全部 76 页也不能算阅读量。网页正文只读两份完整摘要和两个发表列表的对应条目，没有读源码或运行 artifact。

运行 `python references/proceedings/MICRO/2024/parallel-abstracts-next/verify.py` 可离线复核原始源字节和 SHA-256、快照身份与去重、PDF 页数、摘要提取与字符范围、网页提取、CARS 两种摘要版本、图像散列及 5+1 的统计边界。`verification.json` 保存结果。该核验器不独立证明论文性能结论，也不把人工图像核对伪装成自动语义验证。
