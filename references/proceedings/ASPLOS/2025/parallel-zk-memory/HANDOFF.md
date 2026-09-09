# 交接：ASPLOS 2025 ZKP / 虚拟内存摘要包

本包已封存。锁定 165、166、167、168、183、184；以正式 DOI 唯一对应，不与别批重复计算。新增完整摘要 **5 篇**（165、167、168、183、184）；166 仍为未读原始摘要缺口。新增公开 PDF **5 份、89 页**，正文阅读 **0 页**，正文候选 **0 篇**；实际看过的摘要/身份首页图像 **5 张**，不计入正文页。未改共享索引、大纲或 Git，未执行下载代码。

根目录运行：

```sh
python references/proceedings/ASPLOS/2025/parallel-zk-memory/verify.py
```

已通过：49 个文件证明，六个正式 DOI/作者身份核对，五个摘要从原始 PDF/HTML 重提取；21 次 HTTP 响应（15 个 200、3 个 403、3 个 429），另一次 `web.run.open` 403。三次 429 是真实 0 字节响应。15 个 HTTP 200 中，166 的 SDU 新闻页面实际为错误页，单独排除，绝未算成摘要成功。

## 集成入口

- `reading-records.json`：根任务可按唯一 DOI 适配的 `records`、`gaps`，原始摘要全文、提取规则、页数/哈希、身份、版本、范围和编辑取舍。
- `READINGS.md`：每篇完整摘要读后的短评，以及不能外推到本书 AI 案例的边界。
- `selection-snapshot.json`：启动本批时六篇未读摘要的快照。它不要求集成后的当前 coverage 仍为未读。
- `validation.json`：实际核验结果。`verify.py` 只改本目录中的此文件，不改共享校验器。
- `*-jobs.json.results.json`：原始响应 URL、最终 URL、HTTP 状态、字节、SHA-256、取得时间；相应原始正文均保留。日志中原始绝对路径不用于移植定位，记录入口和核验器用仓库相对路径。

## 提取与身份核验细节

所有 PDF 都归档默认 `pdftotext` 的全文 `.txt`、`-layout` 全文 `.layout.txt`，以及 `pdftotext -f 1 -l 1` 默认输出 `.first.txt`。**没有使用 `-raw`**。全文提取不表示正文读完。PNG 为 `pdftoppm -f 1 -l 1 -scale-to 1600 -singlefile -png` 的结果，五张均实际 `view_image` 看过。canonical 摘要只合并空白，不重写原词；`verify.py` 重跑 Poppler 或解析原始 HTML，不依赖现存摘要副本。

| 序号 | 原始摘要重提取 | 身份与版本证据 |
| --- | --- | --- |
| 165 | 默认第一页 `Abstract` 后至 `CCS Concepts:` 前；没有删除摘要内碎片 | 首页完整标题、七位作者、DOI；17 页。作者格子的默认提取顺序有变化，视觉核对正式作者顺序，脚本核对全体名字。 |
| 167 | IACR HTML 唯一 `p[style="white-space: pre-wrap;"]`，合并空白；再与 PDF 的 `Zero-knowledge proof (ZKP) is a cryptographic primitive` 至 `second proof generation for the first time in this field.` 对照 | HTML `citation_title`/六个 `citation_author`、ASPLOS 2025 publication note 和 Crossref 相同 DOI/作者；PDF 首页同题同作者。默认 PDF 输出把右栏 Introduction 放在 Abstract 标题和实际摘要之间，以实际第一/最后句跳过右栏正文。版本历史唯一更新 `20241114:104207`。公开稿 15 页，正式 16 页；未声称相同版本。 |
| 168 | 默认第一页实际首句 `Zero-knowledge proof (ZKP) is an important cryptographic` 至 `than previous ZKP accelerators using different protocols.`，包含两端 | 默认输出在 Abstract 标题后插入右栏 ACM citation，用首末句去掉该引用，保留左栏完整摘要。首页两位作者、正式 DOI、17 页。 |
| 183 | 默认第一页 `Abstract` 后至 `Virtuoso’s accuracy benefits incur an average`（含末句片段）；再接 `simulation time overhead of only 20%,` 到 `Abstract` 前（含前者、不含后者） | 右栏摘要尾三行在默认输出中跑到 Abstract 标题之前，视觉核对后还原左栏→右栏顺序。PDF arXiv v2 日期为 2025-03-27，22 页；十位作者、完整标题和 Crossref 正式 DOI 对应。HTML 用 `meta[name="citation_title"]`、`meta[name="citation_author"]` 与 `.submission-history` 核版本，原始 `blockquote.abstract` 的缺句保留；不用于 canonical 摘要。 |
| 184 | 默认第一页 `Abstract` 后至 `CCS Concepts:` 前，完整左栏无干扰 | 首页 author’s version 声明、四位作者、正式 DOI 和 18 页；作者个人页共同一作顺序与 PDF/manifest/BSC 列表不一致，记录而不自行改正式顺序。 |
| 166 | 无合格完整摘要，不重提取、不计数 | Crossref JSON `message.DOI/title/author` 与 manifest 相同；作者主页同条目核五位作者和 2025 会议。Crossref 无 abstract，原始 ACM 403 与 SDU HTTP 200 error 页面均保留。 |

所有版本时间来自一手版本历史或 PDF 标记；未把 PDF metadata 的文件生成时间当发表时间。未取得 Byte-identical ACM 副本就不这样宣称。五篇仅备查/排除，无需新增大纲插入句。

最终核验边界：离线程序能重提取来源内容、核对字节、身份、版本和摘要，却不能自动证明人类/代理实际阅读；五张第一页的视觉查看是本次工作日志中记录的操作。正文评估、代码运行和性能复现均未发生。
