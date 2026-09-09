# 独立补读交接

从仓库根运行 `python references/proceedings/ASPLOS/2025/parallel-next/verify.py`。核验器只读原始来源和共享 manifest，不访问网络，不运行下载代码，不修改共享文件。依赖 Python、BeautifulSoup、Poppler 的 `pdftotext`/`pdfinfo`。

本批候选为 23、145、175；只有 145、175 新增完整一手摘要。两份 PDF 共 33 页归档；Aqua 只精读物理页 4、8、9、11，共 4 页。两篇首页独立用于摘要和身份核对；Aqua 首页的 KV 容量错误也作了核对。共 6 张页图实际看过。OS2G 保留缺口及失败响应，不计新增摘要或 PDF。

`reading-records.json` 提供两篇可按 DOI 合并的阅读记录，`gaps` 提供 OS2G 未完成的原因。`sources-*.json.results.json` 保留下载时的 URL、最终 URL、状态、时间与字节哈希；其中绝对路径是下载时记录，合并记录均为仓库相对路径。`selection-snapshot.json` 是开始时覆盖表的指纹，当前覆盖表可能已由其他并行任务推进，核验器不要求旧快照哈希等于当前文件，也不重复增加已完成 DOI。

两个正式 DOI 都从原 PDF 首页核验；EDM 的 arXiv Related DOI 提供第二条对应证据，Aqua 作者主页到正式 DOI 的链接提供第二条证据。作者与题名均与 manifest 比对。Aqua 小型大写字形在 Poppler 文字里被提为 `Aqa`，只在身份规范化比较中恢复为 `Aqua`；原始 PDF 和提取文本保持原样。其 arXiv HTML 标题和作者没有这个字形问题。

完整原始摘要以归档 arXiv HTML 的 `blockquote.abstract` 为准：移除子节点 `.descriptor`，用 BeautifulSoup `get_text(" ", strip=True)` 提取，保留 LaTeX、标点和大小写。记录内摘要 SHA-256 针对未额外加换行的 UTF-8 字节；摘要 `.txt` 文件末尾另有一个换行，两个哈希用途不同。HTML 当前记录固定版本分别为 EDM v4、Aqua v3，版本历史保留在记录中。

PDF 文字由 **不带 `-raw` 的默认 `pdftotext`** 生成；另有 `-layout` 全文用于版面检查。首页独立提取参数为 `-f 1 -l 1`，正文指定页独立使用相同页首尾参数。核验器在内存中从 PDF 重提全文、版面全文、首页和四页正文，并与归档文本逐字比较。默认双栏顺序在 EDM 首页把右栏的 ACM 引文尾段置于 Abstract 标题之后，在 Aqua 正文第 4 页等处把图表穿插到段落之前；因此主摘要选用作者提交的 HTML，PDF 文本不做删页脚或重排。人工看图纠正的是阅读顺序，未宣称清洗后的文本仍是原始抽取。

`calculations.json` 是独立算术，不是论文实验复现。核验器重新计算固定几何 KV 容量、十进制小块／合并传输预算和假设链路的净载荷串行化。正文只保留候选或限制说明，不增加书的大纲、实验编号或配图安排。`READINGS.md` 明确区分论文改造版 vLLM 与当前框架默认能力、端到端硬件与微基准硬件、原型与仿真，以及未完成阅读的范围。
