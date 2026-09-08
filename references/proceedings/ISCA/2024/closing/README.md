# ISCA 2024：机构摘要与公开稿补查

2026-09-08，针对尚缺完整原始摘要的 17 项继续找作者及机构入口。此次保存 33 份 HTTP 响应，含三份 IEEE 202 空响应、Zenodo 403 和 AIO 下载接口 403；另一次 PSU 作者站请求因证书链失败，没有收到响应体。响应原件、状态、时间和哈希保存在[来源清单](../selected-sources.json)，原始采集结果也留在本目录。

新增筛读 **7 篇完整机构原始摘要**，依据 [institutional-abstracts.json](../institutional-abstracts.json) 的 HTML 节点或 JSON 路径重新抽取。逐项取舍见[阅读记录](../../../../../research/2026-infra-survey/reading-isca-2024.md)。本次没有取得新 PDF，没有读新的论文正文或图表，也没有执行源码或扩充大纲。

| 日程序号 | 原始记录 | 身份与阅读范围 |
| --- | --- | --- |
| 4 DS-GL | [PNNL](004-pnnl.html)；[合著者列表](004-author.html) | PNNL 完整摘要、DOI、六位作者、会议及页码；机构使用较早题名，合著者列表列出正式题名。摘要倍率排版保留原值，未采用。 |
| 5 ReAIM | [NYCU](005-institution.html) | 完整摘要及 citation 元数据；不纳入本书 Ising 专题。 |
| 33 AIO | [NVA 原始 JSON](033-related-1.json) | 完整摘要、作者、DOI、2024 年份及开放作者稿元数据；保留正文候选，未采用性能或误差数字。 |
| 39 BLESS | [KAIST](039-institution.html) | 完整摘要及 citation 元数据；DNA SMEM seeding 不当作 LLM 检索案例。 |
| 61 Flagger | [KAIST](061-institution.html)；[作者页](061-author.html) | 机构完整摘要、citation 元数据，另核作者叙述与 IEEE 入口；按一篇计算。 |
| 76 Native DRAM Cache | [SKKU](076-institution.html) | 完整摘要及 citation 元数据；面向 CPU LLC 的 Caching-In-Memory，不是 KV 缓存池。 |
| 87 GameStreamSR | [PSU](087-institution.html) | 完整摘要及 citation 元数据；依赖游戏渲染深度信息，未读评估，不移用到普通截图上传。 |

原有 70 份 PDF／1,081 页维持不变；加上本次 7 篇机构摘要，共 77 篇完整摘要已筛，仍有 10 篇待补。Orojenesis、FEATHER、MAD-Max 的三个正文范围维持不变。本次 7 篇不能算成 7 份 PDF，也不能算作正文阅读。

## AIO 的获取路径

旧 NTNU thesis handle 跳到 NVA 应用壳；默认 `Accept` 的 API 请求也返回 HTML 壳。[带 JSON Accept 的记录](033-nva-json.json)才返回论文元数据。它实际是 **2025 博士论文**，摘要和关联出版字段用于发现 AIO，未计入 ISCA 2024。

关联记录分别对应 AIO、[HPCA 2025 HILP](033-related-2.json) 和 [ISCA 2025 Neoscope](033-related-3.json)。后三者的论文标题、DOI、作者和完整机构摘要已核，但只有 AIO 纳入本届计数；HILP 和 Neoscope 当时留作线索，未取得 PDF 或读取正文；随后 Neoscope 按 [ISCA 2025 清单](../../2025/manifest.json)第一次纳入该届摘要计数。

AIO 记录明确列出 `aio-isca24-author-copy.pdf`、AcceptedVersion、OpenFile、593172 字节及允许 download。机构作者名 Joseph Charles Pandl Rogers 对应出版记录的 Joseph Rogers。会议年份 2024、记录迁移 2025、文件开放 2026 含义不同，保留原字段。

静态阅读[下载服务 README](033-download-readme.html)和[模板匿名 GET 路由](033-download-template.html)后，普通公开下载请求仍返回 [HTTP 403](033-public-download.json)。只说明这次入口未成功，不说明 PDF 不存在；没有使用认证信息或执行下载仓库代码。[Swagger 壳](033-api-docs.html)、[initializer](033-swagger-initializer.html)和[OpenAPI](033-openapi.html)也只是入口调查，文件扩展名沿采集器保留，实际内容分别为 HTML、JavaScript 和 YAML。

## 尚缺的十篇

| 日程序号 | 获取状态及后续线索 |
| --- | --- |
| 2 AVM-BTB | 只有出版书目与检索线索，未取得原始完整摘要。 |
| 26 Near-CXL recommendation training | 出版书目与作者线索待继续核对；未取得完整摘要。 |
| 27 Hybrid bonding | 会议有幻灯片入口，尚未取得论文摘要；幻灯片不代替论文。 |
| 43 UM-PIM | [作者出版列表](043-author-publications.html)给出 slides、BibTeX 和 IEEE 入口；[机构新闻](043-institution-news.html)只读开头与线索，未当作原始摘要。 |
| 56 Intel Accelerator Ecosystem | [作者页](056-author.html)的 Abstract 为 TBD，PDF 按钮指向 IEEE 页面；没有完整摘要。 |
| 57 Circular Reconfigurable Processor | 当前只有书目及检索入口，未取得原始完整摘要。 |
| 60 Cambricon-D | 当前只有书目及检索入口，未取得原始完整摘要。 |
| 66 Soter | IEEE 返回 202 空响应；[机构作者页](066-institution-profile.html)仅有书目，作者 publications 页面未发现对应公开稿。 |
| 69 MECLA | IEEE 返回 202 空响应；检索返回的摘要片段未计作归档原始摘要。 |
| 85 BitNN | Zenodo artifact API 返回 403；artifact 元数据与论文摘要／正文分开。 |

PDF 覆盖、摘要覆盖及正文范围由 [reconcile](../../../../reconcile_isca2024.py) 与 [verify](../../../../../research/2026-infra-survey/verify_isca2024.py) 分别核对；缓存再生成不得把 HTML 摘要变成 PDF 页数。
