# ASPLOS 2025：节目 1、2、5、10、14、16 摘要筛读

本批锁定时六项均未读摘要，没有代表 PDF。取得并实际阅读 10、14、16 的一手完整摘要；14、16 的公开 PDF 共 33 页仅作归档，实际范围为完整摘要及首页身份核对，两张首页图均已查看。未阅读正文，不选择正文候选，不改章节、大纲或共享索引。其余三项保留原始摘要缺口。

## 10：Affinity-based Optimizations for TFHE on Processing-in-DRAM

[首尔大学研究成果原始记录](https://snu.elsevierpure.com/en/publications/affinity-based-optimizations-for-tfhe-on-processing-in-dram/)提供完整摘要，页面的 title、四名作者、DOI 10.1145/3676641.3716246、页码 16–31 与正式身份相符。采用 HTML 中 `.rendering_researchoutput_abstractportal .textblock > p` 唯一段落；没有采用页面下方重复的 BibTeX/RIS 文本。出版日期字段是 2025/03/30，online_date 是 2025/09/26，保留两者，不把后者当作会议日期。未取得 PDF。

摘要实际讨论 TFHE 在 PIM 上仅追求并行度、忽视数据亲和性所引起的远程数据访问，提出算法调整和离线调度，并在 FPGA PIM 系统验证。它可作为数据搬移约束的背景，但 4.24–209× 是该 TFHE 工作负载相对其基线的结果，不能用于 LLM attention 或 decode 的吞吐估算。本书已有更直接的 AI 案例，因此仅备查，不选正文。

## 14：BQSim

[作者公开 PDF](https://tsung-wei-huang.github.io/papers/2025-asplos.pdf)首页包含正式 DOI 10.1145/3676641.3715984、完整题名及五名作者，已实际看图核对。公开稿 17 页，首页引用格式也写 17 pages，正式索引页码 79–94 为 16 页；这是明确版本差异，没有声称与出版商文件字节相同。

摘要先指出量子电路模拟通常一次处理一个输入，而测试与验证需要多个输入。BQSim 将 decision diagram 转为适合 GPU 的数据结构，并用任务图减少重复 kernel 调用、重叠计算与搬移。摘要给出的 3.25×、159.06×、311.42× 分别针对 cuQuantum、Qiskit Aer、FlatDD；这些是量子电路批模拟结果，不能借其任务图措辞直接当作 LLM CUDA Graph 收益。仅作其他领域的方法背景，不选正文。

默认 `pdftotext -f 1 -l 1` 的两位作者落在页脚之后，视觉布局已核实。摘要自身在 `Abstract` 与 `CCS Concepts:` 间连续，完整抽取后仅折叠空白，没有把右栏引言或版权文字拼进去。

## 16：Quetzal

[作者公开 PDF](https://desaiharsh.github.io/quetzal.pdf)共 16 页，首页题名、三名作者及 DOI 10.1145/3676641.3715995 与正式记录一致；正式页码 339–354。作者上传的出版排版稿没有固定修订号，以本次来源字节哈希固定版本，不声明出版商字节等同。

完整摘要讨论能量采集设备以固定速率采集、以随供电和事件变化的速率处理数据，小缓冲区可能丢弃新输入。Quetzal 的调度延迟包含充电时间，运行时用排队模型预测溢出，并在即将溢出时降低作业规格。摘要中的最高 4.2× 指减少漏掉的事件，不是数据中心服务吞吐或 p99 延迟的改善。其供电约束与本书调度主线差别很大，保留备查，不选正文。摘要开头的 `[23]` 保留，抽取中的 `endto-end` 也按原始提取文本保留，没有主观修字。

## 1、2、5：保留原始摘要缺口

- Mosaic：正式 DOI 10.1145/3676641.3716262。Crossref 原始记录无摘要；[作者机构页面](https://www.ict.ac.cn/sourcedb/cn/jssrck/201612/t20161205_4716524.html)与[另一作者出版页](https://huangdi95.github.io/publications/)能定位论文身份，没有公开原始摘要或该文 PDF。ACM 落地页/PDF 均 HTTP 403。作者机构页、Crossref 的名字次序为 Jiang Jie；不依据其他页面的 Jie Jiang 写法擅改正式记录。不得从 iTex 或题名推测技术内容。
- DynaX：正式 DOI 10.1145/3676641.3715991。[作者工件仓库](https://github.com/coralabo/DynaX/tree/be22dda622c98a4b04721048fec2c75fed066453)固定提交 `be22dda622c98a4b04721048fec2c75fed066453` 的 README 给出完整题名和七名作者，但没有原始摘要，归档的完整递归树没有 PDF。读取静态 README 仅用于定位，未执行代码。Crossref 单条请求 HTTP 429 零字节，ACM 落地页/PDF HTTP 403。用之前归档的原始 Crossref 批量响应核正式身份，不反复请求同一失败地址。
- RASSM：正式 DOI 10.1145/3669940.3707219。[作者工件仓库](https://github.com/gt-tinker/RASSM/tree/3224b4466e9e40b15cb94826c3c062963c87a6dd)固定提交 `3224b4466e9e40b15cb94826c3c062963c87a6dd` 的 README 是构建/复现实验说明，不能替代原始摘要，完整递归树没有 PDF。Crossref 单条请求 HTTP 429 零字节，ACM 落地页/PDF HTTP 403；正式身份由既有原始 Crossref 响应核对。搜索中出现作者学位论文的相关章节，但未将其当作本篇论文摘要，未下载该学位论文。

没有使用搜索结果、ResearchGate/第三方摘要或工件说明补足这三个缺口。未来获得原文后才能决定它们是否值得正文阅读。本批共 25 个新 HTTP 响应：14 个 200、7 个 403、4 个 429；四个 429 的原始响应确为零字节。失败正文和时间、URL、状态、哈希均保留。`registry-original.json` 是本仓库既有一手 Crossref 响应的字节副本，不计新增网络请求。
