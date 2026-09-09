# MICRO 2024 第五批摘要筛读

本批锁定 13、16、17、18、19、24，共 6 个尚未正式完成摘要阅读的条目，排除了前四批已交付条目及此前受阻的 51、97。结果为 **4 篇完整一手摘要、2 篇完整摘要未取得**。3 份匹配 PDF 共 48 个物理页，其中 1 份复用、2 份新下载；实际看了 3 张首页，只核对题名、作者、摘要和出版标识。**正文阅读 0 页，不推荐新增正文候选。**

输入以本目录 `input-manifest.json`、`input-reading-coverage.json` 和前四批快照为准；复制时间、路径和 SHA256 见 `reused-sources.json`。不假设共享目录在审读后保持不变。本次没有修改共享索引、大纲、skeleton 或 Git，也没有运行下载的代码。

| 序号与 DOI 尾号 | 取得的材料与版本 | 筛选结果 |
| --- | --- | --- |
| 13 HyFiSS，.00022 | 作者目录与 README 的论文信息、Zenodo Software v1.1.4 元数据；IEEE 10764651 返回 202 空响应 | 完整摘要未读。不能把 artifact 的题名、版本或安装说明算成摘要。 |
| 16 LightWSP，.00025 | NSF 公共稿 16 页，首页题名、三名作者、MICRO 2024 和 DOI 一致 | 完整摘要已读；排除正文补读。整机持久内存的断电一致性，与 GPU 训练检查点的代价模型有距离。 |
| 17 DelayAVF，.00026 | 共同作者 MIT 目录公开稿 15 页，题名与六名作者匹配；未声明版本号 | 完整摘要已读；备查。可保留为第 4 章硬件可靠性的背景，不外推 GPU 集群故障率。 |
| 18 Polymorphic Error Correction，.00027 | 第一作者公开 preprint 17 页，题名与两名作者匹配 | 完整摘要已读；排除正文补读。不展开物理内存纠错编码。 |
| 19 DRCTL，.00028 | 作者实验室目录的题名、七名作者、会议和 IEEE 链接；IEEE 10764631 返回 202 空响应 | 完整摘要未读。暂不根据题名、搜索摘录或机器翻译作技术结论。 |
| 24 CacheCraft，.00032 | 作者所属 SKKU 机构记录的完整摘要、五名作者、会议、324–337 页及 DOI | 完整摘要已读；备查。第 4 章可用它提醒有效访存带宽还受数据保护表示影响，当前不增加实验或性能数字。 |

## 读到了什么

LightWSP 的摘要把编译器的可恢复区域、live-out 寄存器检查点，与内存控制器的电池支持 WPQ 结合，用区域末端作为持久化边界。这里的 checkpoint 是整机持久状态的一部分，不能因名称相同，就用它说明训练模型状态写入 SSD 的开销。摘要报告的 38 个应用、平均 9.0% 运行开销和 0.5 B/core 硬件状态仅保存在文献记录里，不作本书训练系统的数值证据。

DelayAVF 区分粒子撞击与小延迟故障，说明后者还涉及电路时序、受影响的状态元素以及程序可见错误。它在摘要里声明分析的是一个开源 RISC-V 核。这种“先明确故障模型，再定义指标”的方法可作备查；本批没有读方法、评估和限制正文。

Polymorphic ECC 的摘要讨论让同一冗余信息服务于多种故障模型，并通过内联 MAC 验证迭代纠错。64 B cache line、40-bit DDR5 channel 与至多 60-bit MAC 都是其摘要设定，不能与低精度模型的数值误差混为一谈。对当前书的主线帮助有限，停止于摘要。

CacheCraft 的摘要提出调整 GPU cache sector 布局，以减少 GDDR in-band ECC 对额外内存访问的需求。它有助于提醒读者区分物理传输量与有效数据量，但当前只有完整摘要：尚未核实基线、工作负载与评估配置。作者报告的平均额外带宽需求 41.9% → 21.9%，不能写成所有 GPU、HBM 或现售产品的固定开销；也不能只凭摘要宣称某款 LLM 服务会得到对应收益。

## 身份、版本与失败记录

LightWSP 的 PDF 来自 [NSF 公共归档](https://par.nsf.gov/servlets/purl/10590071)。上批在寻找 GECKO 时误匹配了它，当时首页提取文字曾暴露，并已明确拒绝错误身份，没有计入正式摘要筛读。本批复用同一原始字节，首次按 LightWSP 条目完成筛读与首页看图。`fourth-batch-sources.json` 保留原下载 URL、状态、时间、SHA；`reused-sources.json` 记录复制桥接。文件生成日期为 2025-05-14，与首页的 MICRO 2024 出版信息分开记录。Poppler 报过 `Illegal annotation destination` 警告；提取和渲染返回码均为 0，未改动原 PDF。

DelayAVF 的一个共同作者 PDF 路径返回 404，原始 HTML 保存为 `delayavf-author-404.response`；随后从 [Mengjia Yan 的 MIT 目录](https://people.csail.mit.edu/mengjia/data/2024.MICRO.DelayAVF.pdf) 得到匹配稿。PDFExpress 元数据日期不是明确稿件版本，也不据此称其为出版商正式版。Zenodo 的同名记录是 software artifact，未用来替代论文摘要。

Polymorphic ECC 的 [第一作者公开稿](https://evmanz.github.io/assets/pec-preprint.pdf) 没有显式版本号。作者主页记录 2024-10-09 发布 preprint/artifact，而当前 PDF 元数据为 2024-10-17；保留两者，不把公告日作为当前文件版本日。

CacheCraft 的 [作者机构记录](https://pure.skku.edu/en/publications/cachecraft-enhancing-gpu-performance-under-memory-protection-thro/) 提供完整摘要；实验室论文链接指向 IEEE，另有 slides，但本批没有下载 slides 或把其算作公开论文。特别注意它不是后来另一篇名称相近的 RAG Cache-Craft 论文。

HyFiSS 与 DRCTL 的一手路径没有提供可获取的完整摘要或 PDF。两份 IEEE 响应都是 HTTP 202、0 字节，完整保存在本包；它们仍是未读。HyFiSS 的 Zenodo 记录没有论文摘要字段，下载列表是大型实验包；没有下载这些包，也没有执行 README 中的安装步骤。没有拿 ResearchGate 搜索片段或机器翻译摘要补足计数。

## 可复核材料

- `abstracts.json` 与 `abstract-016/017/018/024.txt`：4 篇完整摘要的原文片段、提取范围、身份、版本和筛选理由；13/19 单列 unavailable。
- `reading.json`：实际看的首页图、精确字符与行范围、artifact 元数据字段，以及正文 0 页的计数边界。
- `sources.json`：13 次新 HTTP 响应的原始文件、URL、最终 URL、抓取时间、状态、长度与 SHA256；10 次 200、2 次 202 空响应、1 次 404。
- `extraction-log.json`：本地提取、渲染返回码与原始警告；提取文件保留整页或左栏内容，不代表正文被阅读。
- `verify.py` 与 `verification.json`：离线核对原始字节、LightWSP 来源桥接、输入快照去重、身份、PDF 页数、摘要范围、实际看图与计数。

运行 `python references/proceedings/MICRO/2024/parallel-abstracts-fifth/verify.py` 可复核。核验器只读取归档字节并调用本机 Poppler，不访问网络或执行第三方代码。
