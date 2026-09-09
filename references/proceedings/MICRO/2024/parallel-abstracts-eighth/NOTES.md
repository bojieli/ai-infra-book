# MICRO 2024 第八批摘要筛选

以封存时的 **75 篇正式摘要覆盖记录**与前七个独立包去重，排除已有失败 13／19／26／32／38／40／51／97，锁定最早六项 **56、57、58、61、62、63**。正式身份来自本包复制的 manifest；不修改共享索引或大纲。

本批完整阅读 **5 篇一手摘要**，保存 **5 份公开 PDF，共 75 物理页**，实际查看 5 张首页的身份、摘要和版本标记。**正文阅读 0，论文图机制阅读 0，正文候选 0，备查 3，排除 2**。Hestia 完整摘要仍未取得，不纳入上述五篇。首页图像里出现正文或图，不代表完成正文或图机制阅读。

| 序号、正式 DOI 后缀 | 摘要说明的范围 | 筛选结论 |
| --- | --- | --- |
| 56 Surf-Deformer，`.00061` | 针对量子表面码动态缺陷，组合变形指令与适应布局；摘要报告失效率和量子比特资源改善 | **排除**。QEC 的约束不同于本书模型计算、存储与调度，不能仅因“资源”或“通信”而引入 |
| 57 Hestia，`.00062` | 作者项目介绍跨 HLS 抽象层调试；没有取得标明的完整论文摘要 | **未读完整摘要**。不把项目介绍当论文摘要，也不执行工件 |
| 58 AkitaRTM，`.00063` | 为体系结构模拟器提供运行中的可观察性和交互控制；摘要列出两个案例和用户研究 | **备查**。可供研究方法讨论，但现阶段无需增加模拟器教程或正文候选 |
| 61 Temporarily Unauthorized Stores，`.00065` | x86-TSO 下 store buffer 因长延迟写入而阻塞；扩展 write-combining buffer 与 L1 行为，在取得写权限后按序可见 | **备查**。能提示容量、依赖和隐藏等待的关系，摘要没有 AI 服务证据，不加入大段 CPU 协议细节；这里是暂未取得一致性写权限，不是安全权限绕过 |
| 62 FSDetect／FSLite，`.00066` | 扩展 MESI，跟踪一致性缺失并对 false-sharing 行私有化，结束时在 LLC 精确更新；摘要报告模拟结果 | **备查**。是硬件协议方案，不能说成现成软件 profiler；未找到具体 AI 主机瓶颈前不建议正文 |
| 63 CHATS，`.00067` | best-effort HTM 的事务间推测数据、无环依赖与提交次序，摘要给出 gem5 对照 | **排除**。目前缺少与本书贯穿 AI 负载的直接联系，不扩展通用 HTM 专题 |

完整 DOI 的公共前缀为 `10.1109/MICRO61859.2024`。全部原文摘要、正式题名、作者、页码、提取区间及候选理由见 [abstracts.json](abstracts.json)，没有把摘要中的性能数字当作经正文核实的效果。

## 公开稿身份与版本

- **56** 使用 [arXiv:2405.06941v3](https://arxiv.org/abs/2405.06941v3)，修订于 2024-09-16，PDF 生成 2024-09-17，共 16 页；正式会议记录为 750–764，共 15 页。arXiv HTML 把 Yunong Shi 排第三，PDF 和正式记录排第五；均为同一六人，差异原样保存。program 中 Xiang Fang 的 UCSB 单位与 PDF 的 UCSD 也不强行统一。Amazon Science 已索引 PDF 的直接 GET 返回 404，失败字节另存，没有覆盖或隐藏。
- **58** [作者出版目录](https://sarchlab.org/publication)在 MICRO 2024 项明确链接所存 PDF。其元数据生成于 **2025-05-13**，共有 **13 页**；正式会议为 780–794，共 **15 页**。题名与三名作者匹配，作为作者当前公开稿保存，不称为已验证的 camera-ready 或出版商原始字节。
- **61** [Murcia 作者稿](https://webs.um.es/aros/papers/pdfs/jcebrian-micro24.pdf)共 13 页，生成 2024-09-09；题名及三名作者匹配正式 810–822 页，未证明与出版商版逐字节相同。
- **62** [IIT Kanpur 作者托管 PDF](https://www.cse.iitk.ac.in/users/swarnendu/files/papers/micro24.pdf)共 17 页，首页有 MICRO 2024、页码 823 和正式 DOI；元数据生成 2024-10-29。页面与身份匹配，原字节保存，不由托管位置推定使用许可。
- **63** [Murcia 作者稿](https://webs.um.es/aros/papers/pdfs/vnicolas-micro24.pdf)共 16 页，PDF 生成时间为 **2024-12-04 UTC**，晚于会议（本地 `pdfinfo` 显示 2024-12-05）。作者与题名匹配正式 840–855 页，未称其为会议当时的原始文件。

## Hestia 的缺口

[作者 HLS 页面](https://aps.ericlyun.me/research/hls.html)只给 DOI 与 Code。出版商 GET 返回 **418**，保留响应原字节；未重复尝试限制页面。作者仓库根目录元数据没有列出 PDF，README 由 Git blob `f52f839222d6a6c3b946c995fbcf1e1f574e59ce` 固定读取，仅检查 Introduction、Artifact 链接与引用信息。

README 有两段相近 Introduction，不能证明哪段是完整正式摘要；其 BibTeX 还把会议写为 “55th”，并写作 “Yanwen”，与正式第 57 届及作者 Yawen 记录不同。保留这些差异，不据项目存在补齐论文阅读状态。没有继续下载或运行工件，也没有读取实现源码。

## 归档与核验

[sources.json](sources.json) 保存 **12 次 HTTP 响应：10 次 200、1 次 404、1 次 418**，含 URL、最终 URL、获取时间、状态、字节数和 SHA-256。[reused-sources.json](reused-sources.json) 保存 manifest、75 篇覆盖快照与前七包摘要快照，共 9 个输入文件。没有把工具搜索输出或第三方摘要算作已归档一手摘要。

[reading.json](reading.json) 区分完整摘要、辅助身份／版本片段、实际查看首页和未读正文。[verify.py](verify.py) 独立检查最早未读项选择、源字节、身份、固定 Git blob、PDF 页数、原样文本提取与计数；[verification.json](verification.json) 保存结果。验证器只能核对人已声明的阅读范围，不能用文件存在替代实际阅读。

所有新文件均位于本目录；没有修改共享大纲、索引或 Git，没有执行下载的命令、项目、模型或 GPU 任务。
