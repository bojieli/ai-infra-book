# 六篇 GPU／存储摘要交接

范围：173、174、176、177、178、179；正式 DOI 与选择时未读状态见 `selection-snapshot.json`。完整摘要 6，其中 179 是明确关联的匿名工件稿；代表 PDF 5 份／76 页，只读首页身份和摘要 5 页，正文 0。仅 173、177 建议下一轮有限正文选读，其他不新增正文。

从仓库根运行只读核验：

```sh
python3 -B references/proceedings/ASPLOS/2025/parallel-gpu-storage/verify.py
```

也可传入搬移后的目录：

```sh
python3 -B /path/to/bundle/verify.py /path/to/bundle
```

程序提供 `verify_bundle(root, bundle_path)`；只读，依赖 Python 标准库与 Poppler `pdftotext`，不联网、不运行下载代码、不写共享索引。JSON 中路径保留当前仓库相对前缀；核验器将本包文件记录按 basename 解析到传入 bundle 目录，所有文件均在该目录根，不依赖原绝对路径。`registry-original.json` 与 `program-original.html` 是原档案的字节副本，故可独立核身份，无需搬移后访问旧根路径。

提取规则：

- 173／176：arXiv HTML `blockquote.abstract`，排除 descriptor，实体解码，连接 text node，br 转空格，折叠空白。173 v1 用相同规则单列，独立论文增量为 0。
- 174：`pdftotext -f 1 -l 1 -raw`；从 `ABSTRACT` 至 `ACM Reference Format:`。默认模式会夹入右栏代码，故不能替换成默认输出。
- 177：默认 `pdftotext -f 1 -l 1`；从 `Abstract` 至 `CCS Concepts:`。
- 178：原机构 HTML `script[type=application/ld+json]` 中唯一 ScholarlyArticle 的 `abstract`；同时核 `identifier`、`name`、`author`。保留 copyright 尾句，不采用截断 description。
- 179：`pdftotext -f 1 -l 1 -raw`；从 `Abstract` 至 `1 Introduction`。只折叠空白，PDF 行末断词保留，不手工补词或移除页脚。正式身份须经匿名工件关系核验，不能要求这个 PDF 伪装有作者/DOI。

各 PDF 都保留默认／layout 的首页文本，174／179 另有 raw 首页文本；没有全文正文提取。PNG 是首页整页渲染，全部实际看过，但仅声明核对首页摘要与身份。

179 的固定 GitHub commit/tree/README/PDF 已归档，核验器重算两个 Git blob；176 的作者 ASPLOS 2025 介绍链接到对应 arXiv ID，HTML 末两作者与 PDF 次序差异显式限定。173 v1 的功率/能量单基线数字与 v2 的双基线 active power 数字不得混用。174／177 保留正式 2024 Vol.4 与展示 2025 的区别。

`sources-*.json.results.json` 保留 29 个网络请求：成功 18、403 六个、404 一个、429 四个。403/404 原始体和 429 空体均封存。`173-author-paper.pdf` 是失败 404 原始体，**不是**代表 PDF。两份实际 arXiv PDF、两份作者论文 PDF和一份匿名工件 PDF 才是五个代表文件。

`reading-records.json` 的 `unresolved` 与每条 `version_notes` 必须保留。摘要读取完整不等于正式出版版逐字核验，更不等于正文精读或机制实验已复现。主代理负责索引集成，本包不修改共享索引、大纲或 Git。
