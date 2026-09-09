# 本批交接与独立核验

从仓库根运行：

```sh
python references/proceedings/ASPLOS/2025/parallel-abstracts-next/verify.py
```

脚本只读，不联网、不执行下载代码、不写共享索引。依赖 Python、BeautifulSoup 和 Poppler。`reading-records.json` 有 5 条已读摘要记录及 150 的缺口，按正式 DOI 合并。4 份代表性 PDF 共 65 页，其中 Ayo 的 PDF 是作者链接的 Teola v3 相关预印本，须保留该限定。首页身份／摘要页 4 页，实际看图 4 张，正文阅读 0 页。

完整摘要的可移植重提取规则：

- 146、148：归档 arXiv HTML 的 `blockquote.abstract`，删除 `.descriptor` 后 `get_text(" ", strip=True)`。记录完整提交历史和显式版本。148 只在题名核对时允许缺少正式副标题。
- 147：重新用默认 `pdftotext -f 1 -l 1` 从原 PDF 抽取首页，截取第一个 `Abstract` 与其后 `CCS Concepts:` 之间内容，再把空白压成单空格。无需移除页脚、栏间碎片或手工补词，保留 Poppler 对小型大写和断词的文本结果。首页图像已核该范围为完整摘要。
- 149：从归档 HTML 的 `astro-island[component-url]` 核静态组件路径，再在原始组件文本 `ps=[{id:1,` 至 `},{id:2,` 之间提取 `abstract` JSON 字符串字面量，用 `json.loads` 解码。相同对象的 title、authors 和 url 一并重提并核对。没有 `eval`、JavaScript 执行或浏览器注入。
- 153：CUHK HTML 的 `.rendering_abstractportal .textblock > p` 完整段落。作者页面的同一 `.pub-row` 同时包含正式 DOI 和 arXiv 链接，后者作为版本关系证据。Teola v3 摘要由它自己的 arXiv `blockquote.abstract` 另行提取，不覆盖正式 Ayo 摘要、不增加唯一 DOI 计数。

PDF 全文默认 `pdftotext`、全文 `-layout`、首页 `-f 1 -l 1` 均归档并由核验器重新提取比较；**没有使用 `-raw`**，没有选择后续正文页。原 PDF 与原 HTML 字节不改。摘要字符串 SHA-256 不带尾换行，摘要 `.txt` 文件末尾有一个换行，分别核验。

身份链各有区别：147、148 正式 DOI 在 PDF 首页；146 由 arXiv Related DOI 补足；149 由作者项目原始结构化记录对应；153 用机构页的正式身份和作者同一条出版物链接建立相关预印本关系，不能伪称 PDF 上印有正式 DOI。所有作者名单与当前 manifest 比较，正式身份不被预印本短题名或改名覆盖。

`sources-*.json.results.json` 原下载日志保留绝对路径、HTTP 状态、原始／最终 URL、时间及哈希；合并记录全部使用仓库相对路径。HTTP 403/404 及 HTTP 200 的错误作者页面也保留。一次最后的 web 搜索长时间无返回后终止，`search-attempts.json` 记录了无返回事实，没有伪造原始响应。`selection-snapshot.json` 固定开始时覆盖表指纹，当前覆盖进度可能已经改变，核验器仅报告当前 DOI 是否已合并，不要求它回退到旧计数。
