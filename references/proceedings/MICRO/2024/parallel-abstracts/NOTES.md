# MICRO 2024：六篇摘要补读

2026-09-09。本轮固定原日程序号 **41、53、87、88、111、119**；开始前已通知根任务，均不在输入快照的 41 篇完整摘要记录内。六篇均已读到一手完整摘要，取得四份作者公开 PDF、共 **64 个物理页面**；实际只核对四个首页的身份和摘要，**正文选读为零**。另两篇采用作者／机构 HTML 完整摘要，不计 PDF。只改本目录，未改共享索引、大纲或 Git。

本次取舍为 **2 篇正文候选、4 篇备查**。候选只是以后值得核验的问题，没有因摘要而采用性能数字，也没有增加章节。原始摘要和精确来源范围见 [abstracts.json](abstracts.json)，全部请求原件见 [sources.json](sources.json)，失败和版本边界见 [acquisition-notes.json](acquisition-notes.json)。

| 原序号、论文与 DOI | 本轮取舍 | 摘要支持的判断及正文待读边界 |
| --- | --- | --- |
| 41 Cambricon-C: Efficient 4-Bit Matrix Unit via Primitivization；`10.1109/MICRO61859.2024.00047` | 正文候选 | 低位宽使可能的值组合减少，重复算术能否由计数合并，值得与第 4 章矩阵单元的单位成本比较。摘要同时承认利用冗余本身有开销；须核数字格式、计数器／转换／数据搬运、等面积能耗和质量条件。该专用单元不是当前 GPU 的免费功能，LLaMA2 背景不替换书中现代模型贯穿案例。 |
| 53 CPElide: Efficient Multi-Chiplet GPU Implicit Synchronization；`10.1109/MICRO61859.2024.00058` | 备查 | command processor 利用跨 chiplet 依赖来减少不必要的隐式同步，适合作第 4／5 章依赖和数据复用的背景。需要芯片／CP 配合，与现有 GPU 软件优化不同；已有 ScopeAdvice 与实际 NoC 阅读优先，不为它另开硬件一致性案例。 |
| 87 The TYR Dataflow Architecture: Improving Locality by Taming Parallelism；`10.1109/MICRO61859.2024.00089` | 备查 | 可并行工作越多，维持的状态也可能越大；局部 tag 空间用于控制状态并维持进展。摘要明确是通用无序数据流及仿真，不能直接当作 GPU occupancy 或模型 token 调度。第 4／5 章已有容量—并发推导，先不扩展数据流 ISA。 |
| 88 Sparsepipe: Sparse Inter-operator Dataflow Architecture with Cross-Iteration Reuse；`10.1109/MICRO61859.2024.00090` | 正文候选 | 生产者—消费者复用与跨迭代共享稀疏数据是两种机会，可检查第 5 章为何单算子达到带宽上界之后仍值得跨算子减少搬运。须读稀疏表示、依赖、额外缓冲、OEI 数据流及评估条件；通用 STA 的结果不能直接套到 attention 或 MoE。 |
| 111 Demystifying a CXL Type-2 Device: A Heterogeneous Cooperative Computing Perspective；`10.1109/MICRO61859.2024.00110` | 备查 | 应分别测量设备访问主存、设备访问设备存储、CPU 访问设备存储的路径。摘要的应用是 Linux zswap／ksm 与 Redis，不是 LLM KV 池；可作第 4／9 章异构访问路径的背景，待有实际 AI 场景需要时再读正文。 |
| 119 Bridging the Gap Between LLMs and LNS with Dynamic Data Format and Architecture Codesign；`10.1109/MICRO61859.2024.00118` | 备查 | LNS 对近零数的表示优势并不自动解决 LLM outlier；动态格式与执行硬件要一起考虑。机构摘要称原型为 Alveo U280、评估四个 LLM，但未给出足以核对质量的具体配置，本轮不采用其精度百分比，也不将其对下一代 Tensor Core 的设想写成已实现规格。第 4／8 章现有量化判断先保留。 |

## 原件与版本

- **Cambricon-C**：[作者页面](https://yongwei.site/en/cambricon-c/)直接链接 DOI 与 [13 页公开稿](https://dl.yongwei.site/C.pdf)。稿件为图像 PDF，普通 `pdftotext` 第一页只产生换页符。已查看完整首页，再渲染左栏摘要区域，保存未修改 OCR 和人工核对稿；只校正遗漏的乘号 `1.95×`。首页题名及 15 位作者与出版记录对应。没有出版页码／DOI 页脚，因此记作者公开稿，不宣称 publisher version of record。
- **CPElide**：[18 页作者稿](https://pages.cs.wisc.edu/~sinclair/papers/pdalmia-cpelide-micro24.pdf)首页明确写 “To Appear in 57th IEEE/ACM International Symposium on Microarchitecture”。记待刊作者稿，三位作者和题名与 DOI 对应。标题和摘要旁的结构图未作正文分析。
- **TYR**：[17 页合作者稿](https://brian-schwedock.github.io/papers/2024.micro.tyr.pdf)与 [CMU 完整摘要页](https://www.pdl.cmu.edu/PDL-FTP/Storage/Agarwal2024_abs.shtml)相互核对。日程使用 `Tyr: Taming Dataflow Parallelism for Better Locality`，出版与作者稿使用表中的完整题名；作者为 Mitchell **Fream**，按稿件和出版记录保留。Brian C. Schwedock 的稿件机构为 Samsung，脚注说明工作在 CMU 期间完成；不把机构字段当作额外作者。CMU 页的 full-paper href 指向 `ACMToS-0920.pdf`，本轮没有获取或验证那个链接，采用明确匹配的合作者稿。
- **Sparsepipe**：[16 页作者稿](https://intra.engr.ucr.edu/~htseng/files/2024MICRO-Sparsepipe.pdf)题名、三位作者与出版记录相符；没有把搜索结果中的 2020 年同名 *SparsePipe: Parallel Deep Learning for 3D Point Clouds* 纳入。本稿不标最终出版页码，按作者公开稿记录。
- **CXL Type-2**：[合作者完整摘要](https://ipoom-jeong.com/publication/demystifying-a-cxl-type-2-device-a-heterogeneous-cooperative-computing-perspective/)列出 11 位作者与 November 2024；[第一作者页面](https://hxji.github.io/)的本论文条目也指向 IEEE `10764537`。公开 PDF 请求返回 **HTTP 418 HTML**，保存为 `.response`，未绕过、未重试，也未计入 PDF／摘要。相邻 2025 论文或硕士论文不充当这篇 2024 稿件。
- **LLMs and LNS**：[PNNL 页面](https://www.pnnl.gov/publications/bridging-gap-between-llms-and-lns-dynamic-data-format-and-architecture-codesign)包含完整摘要、DOI 与 MICRO 2024 引用，页面发布日期为 **2025-01-08**；论文会议年份仍为 2024。[作者实验室页](https://www.tonytgeng.com/)与[合作者页](https://andrewgui.com/)核对题名／会议，本次所见页面未提供可取得的公开 PDF。摘要保留原文 `bright this gap` 拼写，不擅自修正文句；没有将机构发布日期改成会议日期。

## 阅读与核验口径

四份 PDF 只提取／检查物理第一页。三份文本 PDF 的两栏会让普通抽取混入正文，故另以 Poppler 限定左半页，并用查看过的首页图核对完整 Abstract 至关键词之前的边界。Cambricon-C 则以实际摘要裁剪校正 OCR。四张首页图加一张摘要裁剪，共五张图被实际查看；不把随页出现的正文和图形计入额外阅读。

两份 HTML 摘要用 BeautifulSoup 去掉 script／style 后保存文本，再明确截取 Abstract 到下一字段的字符范围。附加作者页面只定位论文身份和链接，未当作额外论文摘要或正文阅读。TYR 的机构摘要是同一篇的交叉核对，不另计第七篇。

独立运行 `python references/proceedings/MICRO/2024/parallel-abstracts/verify.py` 可核对请求字节／哈希、六个 DOI 的输入身份、原记录未读状态、PDF 页数、限定抽取／OCR 校正、完整摘要字符范围与取舍计数。它不联网、不执行下载代码；会用本地 Poppler 重新提取第一页到内存。结果存入 [verification.json](verification.json)。

按输入快照，根任务整合后完整摘要数可由 41 增至 47，未读从 72 减至 66；这里未改共享数字，也不假设根任务整合时索引未变化。
