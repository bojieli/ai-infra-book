# MICRO 2024 第三批并行摘要筛读

本批按任务开始时 `reading-coverage.json` 的 **false** 选取并锁定 **21、72、73、89、94、97**；当时汇总为 52 篇完整摘要已读、61 篇未读。序号 11 的 Mess 已为 true，因此未选。快照及 SHA-256 见 `input-reading-coverage.json`、`reused-sources.json`；不假设根任务更新后的共享覆盖文件仍与快照相同。

实际新增 **5 篇完整一手摘要、4 份公开 PDF（共 65 个物理页）**，其中 Genie Cache 的完整摘要来自作者机构记录；Blenda 完整一手摘要未取得，不能计入已读。四张 PDF 第 1 页图像均实际查看了标题、作者和完整摘要。**正文阅读为 0 页**；没有读或执行源码，没有修改共享索引、大纲或 Git。

| 序号 / DOI 尾段 | 论文 | 身份与结果 | 筛选 |
| --- | --- | --- | --- |
| 21 / 00029 | A Case for Speculative Address Translation with Rapid Validation for GPUs（Avatar） | 第一作者页面直接链接的 15 页 PDF；第 1 页有相符的 8 位作者、DOI、正式页码 278；完整摘要。 | 备查 |
| 72 / 00075 | Memory Allocation Under Hardware Compression | 第一作者页面直接链接的 17 页 PDF；10 位作者相符，第 1 页 DOI 与正式页码 966 对应；另读 MSR 的完整摘要版本。 | 备查 |
| 73 / 00076 | Genie Cache | 作者机构 Yonsei 的完整摘要记录，作者、DOI、983–996 页相符；没有取得公开 PDF。 | 备查 |
| 89 / 00091 | Pushing the Performance Envelope of DNN-based Recommendation Systems Inference on GPUs | 作者提交 arXiv:2410.22249v1，固定版本 16 页；题目及 6 位作者对应 MICRO 论文；完整摘要。 | 后续候选 |
| 94 / 00095 | Leviathan | 合作者 CMU 目录下的 17 页公开稿；标题与 2 位作者对应；完整摘要。 | 备查 |
| 97 / 00098 | Blenda | 合作者页面仅题录，出版社返回 HTTP 202 空响应；没有可归档的完整一手摘要／公开稿。 | 保留未读 |

DOI 前缀均为 `10.1109/MICRO61859.2024.`。作者托管稿的文献身份匹配不等于已经证明与出版社文件逐字节相同。公开稿的 artifact 图标也不等于本次检查或运行过 artifact。

## 有界相关性判断

**Avatar：地址预测以后还要能验证。** 摘要提出 CAST 先预测映射并取数，CAVA 则验证推测物理地址，使预测所得数据能够被使用。适合第 4 章访存延迟的背景说明；需要后续正文才能核查映射信息开销、误预测和硬件条件。本批不将其写成现有 GPU 的可用功能，也不采用摘要的加速数字。[第一作者公开稿](https://zoon17.github.io/pdfs/avatar_micro24.pdf)

**硬件压缩：逻辑容量不等于实际占用。** CPU 内存控制器压缩后，同一物理页实际占用的 DRAM 随内容变化；摘要因此提出实际内存层的分配接口及 MMU 类组件，并报告全系统 FPGA 原型。可作容量计量和并置隔离的背景，但它与模型权重量化不同，也不是今天的软件内存池自动获得的功能。FPGA 细节与工作负载没有读，不把表现变动范围用于书中结论。[第一作者公开稿](https://people.cs.vt.edu/mlaghari/papers/dmu_micro_2024.pdf)

**Genie Cache：省元数据流量也可能增加控制延迟。** 将 DRAM-cache tag 放进页表能减少额外 tag 访问，却仍要处理 miss 和驱逐时的 OS 开销。摘要提出 DCMU 和提前写回来减少阻塞，可作第 4 章 DRAM-cache 设计取舍备查。它不是 KV-cache 的软件机制，且本批只有摘要，不能推断具体实现成熟度。[作者机构完整摘要](https://yonsei.elsevierpure.com/en/publications/genie-cache-non-blocking-miss-handling-and-replacement-in-page-ta/)

**DLRM 推理：occupancy 改善后，延迟瓶颈仍可能存在。** 这是本批唯一建议后续正文阅读的候选。摘要先定位 embedding 内核 occupancy，再指出编译优化之后仍有较长访存等待，因此引入软件预取与 L2 pinning；适合现有第 5 章 profile 驱动优化的一处实验变体。已知摘要测试平台为 A100，模型为 DLRM，具体模型规模、工作集分布、CUDA／框架版本与缓存驻留条件尚未读。只根据摘要不能将结果推广到 LLM，也不能直接安排为已验证代码实验。[固定 arXiv v1](https://arxiv.org/pdf/2410.22249v1)

**Leviathan：靠近数据计算，也要表达执行时机与位置。** 摘要将 near-cache 计算与响应式编程接口结合，可以说明硬件移动计算以后仍需要程序接口与调度表达。但摘要里的专门应用不能证明所有应用均适用。本书已有减少搬运的主线，先备查，不增加通用 NDC 专题。[合作者公开稿](https://www.cs.cmu.edu/~beckmann/publications/papers/2024.micro.leviathan.pdf)

**Blenda：目前只核实身份，不作摘要判断。** 合作者 Farid Samandi 的页面列出同一标题、六位作者与 MICRO 2024，但没有该文的 PDF 链接或完整摘要。DOI 请求最终返回空响应。二手站点虽然展示概述，本批未以其替代一手原文，也没有重试此前 Atomic Cache 的受阻路径。[合作者题录](https://compas.cs.stonybrook.edu/~fsamandi/)

## 版本、异常与计数边界

- 推荐系统稿固定为 **arXiv v1，2024-10-29 17:13:54 UTC**；这与会议／出版社日期分开记录，不称为出版社最终稿。
- Genie 的机构日期为 **2024-11-06**，Crossref metadata 为 **2024-11-02**。两个日期各自保留，不解释成两个不同技术版本。William Song／William J. Song 的名字形式也作身份说明。
- 硬件压缩 PDF 与 MSR 摘要文字不同，但共同报告的变动范围没有本批发现的数值冲突。原文分开保存，不选定哪一个是最终修订。PDF 显示 Kirk Cameron，metadata 为 Kirk W. Cameron。
- 硬件压缩 PDF 有 Poppler `xref num 4` 重建警告。`pdfinfo` 和两条 `pdftotext` 均返回 0，三份可复现 stderr 与 `extraction-log.json` 已保留；渲染后的第一页已目视确认摘要完整。没有改写或修复原 PDF 字节。
- Leviathan 第一作者当前单位为 Samsung，脚注说明工作在 CMU 完成；保留这一身份关系，不把单位差异当作不同论文。

本批原始 HTTP 请求 **11 次：10 次 200、1 次 202 空响应**；另复用上一批已保存的 Avatar 作者题录 HTML。所有 URL、状态、时间、字节数和 SHA-256 见 `sources.json` 与 `reused-sources.json`。完整摘要及字符范围见 `abstracts.json`，实际阅读范围与图片散列见 `reading.json`。网页摘要的同文版本不会增加论文数量。

离线运行 `python references/proceedings/MICRO/2024/parallel-abstracts-third/verify.py` 可复核源字节、false 快照去重、文献身份键、PDF 页数、摘要提取／范围、网页提取、已记录图像和提取警告，以及 **5 篇完整摘要 + 1 篇未取得** 的计数。`verification.json` 保存结果；核验不替代正文评估或性能复现。
