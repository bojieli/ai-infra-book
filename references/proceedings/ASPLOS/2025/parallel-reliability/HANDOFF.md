# 摘要包交接：157、159–163

已封存五篇完整原始摘要与五份公开 PDF（78 页），并保留 163 Hardware Sentinel 的原始摘要缺口。只读完整摘要与首页身份，五张首页实际看过；正文 0 页，正文候选 0 篇。未改共享 manifest、coverage、大纲、verifier 或 Git。

从仓库根运行：

```sh
python references/proceedings/ASPLOS/2025/parallel-reliability/verify.py
```

需要 Python、BeautifulSoup、Poppler 的 `pdftotext` 与 `pdfinfo`。验证器只读原始来源并重提取，不依赖网络，不运行下载代码；只写本目录 `validation.json`。18 个 HTTP 原始响应全部保留：12 成功、4 个 429、2 个 403；其中三个 429 为真正零字节响应。另有一个 web 工具打开 ACM 摘要页失败的原始工具返回，独立记录，不伪造 HTTP 原始字节。

五篇按唯一 DOI 接入，不能把 163 记为摘要完成：

| 程序 | DOI | 原始摘要与身份 |
| --- | --- | --- |
| 157 | 10.1145/3622781.3674180 | arXiv 2410.12749v1 完整摘要；作者首页正式 DOI/同题/三名作者，同页明确 2024 接收、2025 延后报告。16 页预印本不冒称出版版。 |
| 159 | 10.1145/3669940.3707243 | arXiv 2407.12232v1 完整摘要；同题/五名作者对应 Crossref，arXiv 接收说明对应 2025。公开稿 15 页，正式为 17 页；EPFL 正式稿 429 留存。 |
| 160 | 10.1145/3676641.3715993 | EPFL 16 页正式排版 PDF，首页 DOI 与五名作者；`Josipovi?`→`Josipović` 的原始编码差异已记别名，不改共享元数据。 |
| 161 | 10.1145/3669940.3707269 | 作者公开 15 页正式排版 PDF，首页 DOI 与两名作者。 |
| 162 | 10.1145/3622781.3674182 | NSF 16 页稿，首页 DOI 与七名作者，保留 ASPLOS2024 Volume4 身份。 |
| 163 | 10.1145/3676641.3716258 | Crossref 无摘要、ACM 拒绝访问；Meta 博客只作为论文链接出处，未将博客/转载作为原始摘要。 |

摘要提取方式：157/159 从保存的 arXiv HTML `blockquote.abstract` 去掉 `.descriptor`，保留原文；160/161/162 从 PDF 首页重新提取。默认 `pdftotext`，没有 `-raw`。160 从 `Dataflow circuits have been studied` 至摘要末句，跳过标题后的右栏引文续行；161 为 Abstract 至 CCS Concepts；162 为左栏 Abstract 至版权说明前，接右栏 `our proposed techniques` 至 ACM Reference Format 前。162 仅排除夹入的版权/会议信息页脚，两个摘要区间都按看图确认。合并空白，不补写句子、不把页面余下的 Introduction 计为正文阅读。

取舍见 `READINGS.md`：Toleo 可留机密内存池背景，Vega 可留可靠性背景，其余形式验证论文与当前 AI Infra 量化主线联系弱；本批不强设正文候选、不新增实验。Hardware Sentinel 未取得原始摘要，暂缓判断。机器读取入口为 `reading-records.json`，其中 `records` 五篇与 `gaps` 一篇分开，所有摘要和 PDF 都有来源、版本、完整文字、页数、哈希和排除/取舍理由。
