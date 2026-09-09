# 独立交接

运行 `python references/proceedings/ASPLOS/2025/parallel-pim-serverless/verify.py`。核验器从任意工作目录可运行，只读本包和正式 manifest／coverage，不联网、不执行下载代码、不改共享文件。依赖 Python、BeautifulSoup、Poppler。

六条完整摘要按正式 DOI 接入：154、156、158、170、171、172。六份 PDF 共 91 页，六个首页／六张实际看图，正文页数 0。PAPI 的 PDF 是 13 页 arXiv v2，正式记录为 17 页；不要把两者页数混用。CINM 保留 ASPLOS 2024 卷 4 与 ASPLOS 2025 presentation 的不同字段。本包没有未完成的摘要 DOI，但正式稿可得性和所有正文／框架核验仍有未完成项。

摘要重新提取规则：

- 154、158、171：归档 arXiv HTML `blockquote.abstract`，移除 `.descriptor` 后 `get_text(" ", strip=True)`，保存原始 LaTeX、拼写、标点，不用 PDF 代替 HTML 段落。
- 156：默认 `pdftotext -f 1 -l 1` 首页，第一处 `Abstract` 后至随后 `Keywords:` 前，压缩空白为单空格。保留 Poppler 原始断词结果，不人工补连字符。
- 170：相同首页提取，`Abstract` 后至 `CCS Concepts:` 前，压缩空白。
- 172：相同首页提取，从 `Abstract` 后到完整末句结尾 `TTFT) by 53.0%.`。不能截到后面的 `CCS Concepts:`，因为默认抽取顺序会在其前混入右栏图 1、关键字、引用和正文；用该明确末句结束可重现完整摘要。首页图像已核对，没有删改摘要内容。

所有 PDF 均归档默认 `pdftotext` 全文、`-layout` 全文及首页独立文字；**不使用 `-raw`**，不移除页脚、不清洗原始文本。核验器重新抽取并逐字比较。完整 PDF 文字的产生与比较不计为正文阅读。摘要字符串 SHA-256 不带尾换行，摘要 `.txt` 文件含一个尾换行，两者分别验证。

156、170、171、172 的 DOI 在 PDF 首页可见；154、158 首页无 DOI，前者使用既有官方节目／出版者 manifest 与完全对应的题名、九名作者建立身份关系，后者另有新获取的 Crossref 记录。不要把 `pdf_official_doi_visually_verified=false` 自动转为 true。156 的 Karl F. A. Friebel 仅在身份比较中使用明确缩写映射，不改源文字或正式作者名。

`sources-*.json.results.json` 保存原始 URL、最终 URL、状态、时间和哈希；合并记录使用仓库相对路径。两个 HTTP 429 都保留，Crossref 的空响应体是实际 0 字节文件，不伪造错误页面。开始时 coverage 指纹单独记录，核验器只报告当前是否已接入，不要求覆盖表恢复旧计数。本包没有下载或运行代码，没有图、实验或大纲变更。
