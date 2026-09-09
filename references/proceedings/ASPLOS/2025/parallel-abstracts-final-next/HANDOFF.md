# 独立交接：ASPLOS 2025 节目 1、2、5、10、14、16

锁定时六项均为摘要未读且无代表 PDF。实际新增 **3 篇完整摘要（10、14、16）、2 份 PDF、33 个归档页；正文 0 页**。1、2、5 保留原始摘要缺口，没有通过 README、搜索片段或学位论文相关章节凑数。

从仓库根运行：

```sh
python references/proceedings/ASPLOS/2025/parallel-abstracts-final-next/verify.py
```

`reading-records.json` 是按 formal DOI 对接的记录与缺口，`READINGS.md` 记录阅读判断，`validation.json` 是上述命令的输出。只读静态材料，没有执行第三方代码；未改共享 coverage、索引、大纲或 Git。

核验入口检查原始 HTTP 字节、状态、哈希与抓取日志，对照当前正式 manifest 和已归档原始 Crossref 响应核六个 DOI、题名、作者、页码；重新从机构 HTML 抽取 10 的完整摘要，并从两个原 PDF 重新提取首页与完整机械文本，按固定段落边界重提取 14、16 的完整摘要。工件 README 与固定提交递归树的 Git blob 哈希也独立核对。

- 10：唯一 selector 为 `.rendering_researchoutput_abstractportal .textblock > p`，以 `get_text(" ",strip=True)` 后折叠空白；页面重复 BibTeX/RIS 未选。`citation_title`、四个有序 `citation_author`、`citation_doi`、起止页码直接核身份。未取得 PDF。
- 14、16：默认 `pdftotext -f 1 -l 1 input.pdf -`，**没有 `-raw` 或 `-layout`**；选 `Abstract` 到 `CCS Concepts:`。摘要区间内没有移除页脚或栏间片段，仅折叠空白。两个全篇 `.txt` 用默认提取，`.layout.txt` 另用 `-layout`。14 默认提取将两位作者放在页脚之后，实际看首页图核对了布局；完整摘要仍连续。16 原始 `[23]` 与提取的 `endto-end` 原样保留。
- 两张首页 PNG 已实际查看，核完整题名、所有作者和正式 DOI；此为摘要/身份阅读，不计正文。其他页只是机械提取归档，没有宣称正文读完。
- 14 的公开稿和首页引用均为 17 页，正式页码 79–94 为 16 页；保持差异，不声称正式出版版本等同。16 共 16 页，与正式页码 339–354 相符，但没有出版商字节等同声明。
- 1、2、5 原始摘要缺口仍为 false。Crossref 批量原始响应只核 `message.items` 中精确 DOI 的六项（无 abstract 字段），没有把其余 994 项计入阅读。`registry-original.json` 与既有原始响应逐字节相同，`local-copy-provenance.json` 记录原 URL、状态、时间及路径，不计本批新增 HTTP。
- 本批 25 个 HTTP：14 × 200、7 × 403、4 × 429。四个 429 的零字节原响应照实保留。DynaX 固定 `be22dda622c98a4b04721048fec2c75fed066453`，RASSM 固定 `3224b4466e9e40b15cb94826c3c062963c87a6dd`；两份完整树没有 PDF，README 不作原始摘要，未运行其安装或编译命令。

三篇已读摘要的主题分别为 TFHE、量子电路批模拟、能量采集设备，不强行新增 AI Infra 正文候选。包中判断只依摘要，不把摘要内报告收益当作已核评估结果或 LLM 性能。
