# ASPLOS 2025 程序 91–110 独立交接

范围已完成：18 个新增完整摘要，15 份代表 PDF（263 个物理页），15 张实际查看的摘要／身份页，正文阅读计数新增 0。94 FSMoE、95 CoServe 已有记录，跳过。全部新文件只在本目录，未修改仓库、Git 或上一批 77–90 的包。根线程可串行复核、搬移和集成。

`merge-ready.json` 与上一批同样使用 `sources`、`records`、`representative_pdf`、`abstract_text_file`、`identity`、`version_notes`。34 次下载结果的原始字节和 HTTP/异常元数据保留在 `jobs1` 至 `jobs4` 的结果 JSON。98、102、104 的 ACM PDF 返回 403，保留错误 HTML；105 首次域名连接失败，保留异常响应，替代作者域名成功。未获得 98、102、104 的代表 PDF，不用搜索摘要代替正文。

## 阅读与计数边界

实际阅读完整摘要及题名、作者、DOI、版本信息；所有 15 份 PDF 的物理第 1 页渲染图均已通过 view_image 查看，以核对双栏顺序、摘要边界和作者身份。PDF 后文仅作为存档提取，不计正文阅读，首页伴随的引言片段也不计专题正文阅读。未运行论文软件或 artifact，未复现实验。编辑取舍是依据摘要作出的判断；headline 提速与误差仍需正文验证硬件、基线、batch、准确性、延迟和资源成本。

## 原始文本的重提取

本批 **pdftotext 没有使用 `-raw` 或 `-layout`**，即默认阅读顺序。全部文件均以如下命令生成：

```sh
pdftotext input.pdf input.txt
pdftotext -f 1 -l 1 input.pdf input.first.txt
pdftoppm -f 1 -l 1 -scale-to 1500 -png -singlefile input.pdf input.p1
```

`build_bundle.py` 可读出全部确切 selector 和边界表达式；它是本地生成程序，不是下载的代码。可移植 verifier 应使用输入根路径重写，而不依赖其硬编码工作目录。PDF 原始文本保留换行、连字符和抽取字符；摘要只按下述范围截取与拼接，最后 `.strip()`，写单独摘要文件时加一个尾换行。`abstract_sha256` 是 JSON 中摘要字符串 UTF-8 的哈希，不包含额外尾换行；摘要文件 proof 包含尾换行。

| 程序 | 完整摘要来源与可重提取规则 |
|---|---|
| 91 | `paper-091-author.html` 第一个 `.pub-abstract,.article-style,.textblock` 匹配元素，`get_text(' ', strip=True)`；保留 HTML 的 `tiered-Memory system` 原文。PDF 双栏默认抽取先出现右栏续段，故不用 naive Abstract→CCS 切片。 |
| 93、96、97、101、107 | arXiv HTML `blockquote.abstract`，删除内部 `.descriptor`，再 `get_text(' ', strip=True)`；作者、标题分别来自 `meta[name=citation_author]`、`meta[name=citation_title]`，版本历史来自 `div.submission-history`。 |
| 98 | 作者 HTML：找到 stripped text 恰为 `Abstract` 的文字节点，其 parent div 的下一个 sibling div；`get_text(' ', strip=True)`。另有同页链接 `cite.bib` 保存完整 11 作者。 |
| 102、104 | 机构 HTML 第一个 `div.textblock`，`get_text(' ', strip=True)`；另存整个 div 的原始 HTML 片段，特别保留 104 的上标与公式原貌。 |
| 92 | 默认首页文本 `Abstract\n` 后至 `\n\nCXL + multi-hops` 前；后者是右栏图标内容，不属于摘要。 |
| 99、106 | `Abstract\n` 后至 `Permission to make digital` 前；摘要完整在左栏，移除之后的版权页脚。 |
| 100 | `Abstract\n` 后至 `\n\nFigure 1.` 前；右栏图说明及引言不计摘要。 |
| 103 | 拼接 `Abstract\n` 后至 `∗ National Engineering Research Center` 前，以及 `optimization interactions. Subsequently,` 起至 `Keywords:` 前；删除两栏间的作者注释、机构、通讯作者标记、版权/DOI 与错序 Hai Jin 机构文字。 |
| 105、109 | `Abstract\n` 后至 `CCS Concepts:` 前。 |
| 108 | `Abstract\n` 后至 `ACM Reference Format:` 前，保留 PDF 的 63.9%。机构 HTML 替代摘要另存，规则为首个 `div.textblock`，保留其 81.3%，不重复计数。 |
| 110 | 拼接 `Abstract\n` 后至 `Permission to make digital` 前，以及 `the baseline on average.` 起至 `CCS Concepts:` 前，移除跨栏版权/ISBN/DOI 插入片段。 |

## 正式身份与版本差异

- 91、92、97、99、100、101、103、105、106、107、108、109、110：渲染首页核对题名、完整作者与打印的 ACM DOI，和仓库正式 manifest 一一对应。
- 93、96：arXiv v1 题名和完整作者与正式身份一致，页面与 PDF 没有打印正式 DOI。因此明确登记为作者预印本，不冒称 publisher version of record；正式 DOI 来自已有 manifest 的出版身份。
- 98：作者页面题名一致，页面作者头部少 Wei Lin、Yang You，但同页面的 `cite.bib` 包含正式 11 作者。BibTeX DOI/URL 空白、ISBN 全零，不采用这些占位符。已有 manifest DOI 由精确题名与完整作者桥接；缺独立一级来源 DOI 打印证据，已显式记录该边界。
- 102：机构页面 `citation_title`、全部 `citation_author`、`citation_doi` 与正式身份一致。
- 104：机构页面题名/DOI 相同，第三作者写作 `Hitarth SINGH`；第一作者主页相同题名（CFGs 简写）、同一会议和其余作者组合明确列 `S. Hitarth`。保存差异，不标成 author-string 全等，也不擅改机构原始数据。机构摘要的公式抽取丢失个别符号，上标展开不能直接作为经验证的复杂度公式。
- 103、108：论文首页写 ASPLOS 2024 Volume 4，但该正式 DOI 收录于 ASPLOS 2025 节目。保留原始 imprint 和节目身份，不强改年份。108 作者 PDF 的 63.9% 与 CityU HTML 的 81.3% 不合并、不裁定。PDF 来源为作者 Anshunkang Zhou 的 `seviezhou.github.io`。
- 107：arXiv v4 有 35 个物理页，正式论文 pp426–444 为 19 页；HTML 作者缩写 Gilbert Bernstein，PDF 完整名 Gilbert Louis Bernstein。PDF 打印正式 DOI，按扩展作者版归档，不把 35 页当出版页数。107、109 的原稿 reference 中有 29th/ASPLOS 25 的排版不一致，原始字节保留。
- 99：正式 SING PDF 虽文件名含 tacc，但题名、全部 9 作者和 DOI 都一致。旧 TACC preprint 不在本批计数。

优先候选：93 MoE-Lightning、96 Klotski、97 MoC-System、100 PCcheck、101 Tally、107 Exo 2；91/92 用来校准真实 CXL 的容量、带宽、延迟及迁移成本；98 Concerto 的正文公开缺口须后续解决。通用编译器、二进制与 UI 测试文章按具体研究对象筛除，避免关键词相似造成章节膨胀。
