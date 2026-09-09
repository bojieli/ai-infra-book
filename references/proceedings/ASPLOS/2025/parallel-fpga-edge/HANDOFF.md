# 独立交接：ASPLOS 2025 FPGA / Edge 摘要批

锁定节目 **19、25、29、30、31、32**。新增 **5 篇完整原始摘要、3 份 PDF、46 页归档，正文阅读 0 页**；Hassert（32）保留原始 ASPLOS 摘要缺口。已实际看 29、30、31 的首页图，每项仅核摘要与身份，不计正文。

从仓库根运行：

```sh
python references/proceedings/ASPLOS/2025/parallel-fpga-edge/verify.py
```

`reading-records.json` 按正式 DOI 对接；`READINGS.md` 有编辑取舍与来源；`validation.json` 为核验报告。本批不扩张大纲，不修改共享索引或 Git。没有执行第三方代码。

独立核验重新读取全部来源字节、HTTP 状态与哈希，对照当前正式 manifest 和原始 Crossref 六个精确 DOI 项核题名、作者、页码与年份；再实际从原 PDF / HTML / JSON 重新提取五篇完整摘要。自写 verifier 会写同目录 validation.json；如要保证封包所有文件完全不变，请在临时字节镜像运行。

- 19：机构 HTML selector `.rendering_researchoutput_abstractportal .textblock > p`。只折叠空白，不取重复 citation 字段；metadata 作者有两项明确名称映射。作者网页 PDF 是 `https://todo.pdf` 占位符，没有请求。无代表 PDF。
- 25：机构 API 的 `results[DOI == "10.1145/3669940.3707225"].abstract`，保留整个解码后 JSON 字符串，不修正 `neces- sary`、`2kb`、`256kb`。静态 JS 仅用于读公开 API 路由，未执行。第一次误用参数所得全校列表 HTTP 200 没有目标 DOI，留存并排除。正确响应的其他九项未计阅读；机构页面此栏称 Scopus Publications，未声称作者个人稿件上传。无代表 PDF。
- 三份 PDF 均默认 `pdftotext -f 1 -l 1 input.pdf -`，**没有 `-raw` 或 `-layout`**。全篇默认 `.txt` 和另行 `-layout` 的 `.layout.txt` 是机械归档，核验时重新生成比较字节，不是正文阅读证据。
- 29 Salus：左栏正文从 `CPU-FPGA heterogeneous architectures` 到 `ACM Reference Format:` 前，追加被默认提取提前的右栏 `IP, Salus presents ... minor efforts required.` 两行。图上已核顺序，脚注/版权/引言不选。正式 ASPLOS 2024 Volume 4、15 页，与 2025 节目归属分开。
- 30 Harmonia：左栏 `Abstract` 到 `Permission to make digital` 前，右栏从 `hardware differences and a platform-independent layer` 到 `CCS Concepts:`。中间版权段移除，正文没有遗漏。作者 HTML 完整摘要亦保留；`15-23x` 与 PDF `15-23×` 差异记录。网页 August 2024 不替代正式 ASPLOS 2025 日期。17 页。
- 31 PhasePrint：默认提取在 Abstract 后插入右栏 CCS，采用完整第一句与末句双锚，只选左栏完整摘要。14 页。三个 PDF 的所有作者、题名和正式 DOI 均已在首页图核对，没有出版商字节等同声明。
- 32：八作者原始 ASPLOS 摘要未取得。另一场 RISC-V Summit 的题名多出 Agile、只有四位作者，该 HTML 是排除证据，不计原始摘要、PDF 或正文。

本批 17 个 HTTP 响应：12 × 200、5 × 403。所有失败响应留存；有一份 HTTP 200 的错误过滤 API 结果明确排除。`registry-original.json` 为既有原始 Crossref 响应的字节副本，另有 provenance，不计新 HTTP。五篇已读摘要都只作相关性筛选，没有新增正文候选，也没有把摘要报告的数字表述成已核对的正文实验结果。
