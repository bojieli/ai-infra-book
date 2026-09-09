# MICRO2024 第十一批完整摘要筛选

2026-09-09 封存。本包独占 `parallel-abstracts-eleventh/`，没有修改共享索引、大纲或 Git。基于正式 **86 篇完整摘要**快照与前十批封存结果去重，跳过先前 15 项失败，锁定最早六项：98、102、104、106、110、113。输入原文件、复制时刻、SHA-256 见 `reused-sources.json`。

实际完成 **4 篇完整一手摘要，2 份作者 PDF，共 30 物理页可用**。只读两份 PDF 首页身份与完整摘要，并实际查看首页图像；其余两篇读作者/机构 HTML 完整摘要。**正文 0，论文机制图 0，新增正文候选 0**。可下载页数没有计作已读页数；HTML 记录里的正式页码也没有计作已获 PDF。筛选为备查 3、排除 1、摘要缺口 2。

| 顺序 | 正式 DOI 后缀 | 完整摘要来源 | PDF | 本轮取舍 |
| --- | --- | --- | --- | --- |
| 98 ICED | 2024.00099 | Tulika Mitra / NUS 作者稿首页 | 15 页 | 备查第 4/5 章电源岛、映射与吞吐瓶颈 |
| 102 Uneven Block Size Instruction Cache | 2024.00102 | Rakesh Kumar / NTNU 作者稿首页 | 15 页 | 备查有效缓存容量；不扩写通用 CPU 前端 |
| 104 SOPHGO BM1684X | 2024.00104 | 未取得完整一手摘要 | 0 | 保留缺口 |
| 106 VGA | 2024.00106 | SangLyul Cho 的 publications 页 | 0 | 备查第 2/4/5 章算子形式与瓶颈变化 |
| 110 Ares-Flash | 2024.00109 | 作者/组目录只有书目或出版商入口 | 0 | 保留缺口 |
| 113 SuperCore | 2024.00112 | SKKU Pure 机构记录 | 0 | 低温 SFQ 应用关联弱，排除正文 |

完整 DOI 均以前缀 `10.1109/MICRO61859.` 拼接，机器记录保留正式 manifest 的原始大小写和身份字段。来源 URL、状态、取得时刻、原字节长度与 SHA-256 全部在 `sources.json`，摘要原文和精确字符/行范围在 `abstracts.json`。`reading.json` 单独记录实际阅读范围。

## 有用的边界

- **ICED** 的摘要围绕 CGRA 数据依赖流水：非限制吞吐的阶段未充分利用资源，电源岛粒度与 DVFS 感知映射共同影响能效。可以提示“先找瓶颈再分配能耗预算”，但还不能证明现有 GPU 或推理框架有该机制。作者 PDF 生成于 2024-08-16，15 页；首页和 publisher 写 **DVFS**，program 的 **DFVS** 原样保留。未把作者稿宣布为出版商同字节 VoR。
- **UBS 指令缓存** 分析的是通用服务器指令流的空间利用率。摘要报告提升 **32 个百分点**，不是相对增加 32%。虽然“标称容量与有效容量不同”可备查，但没有 AI 主机程序的实际瓶颈证据，不借此增加第 12 章通用 CPU 细节。作者稿生成于 2024-09-16，15 页；`Front-End` / `Frontend` 及 `Roman Brunner` / `Roman Kaspar Brunner` 的来源差异保留。
- **VGA** 的摘要指向 H3 的 FFT 全局卷积：通过复数计算单元利用片上 SRAM 带宽，按需生成参数减少 SRAM 容量需求。摘要中的 76×/48× 分别属于该算子的面积/功率效率比较，不能写成 LLM 端到端吞吐提升，也不能扩大成当前所有 SSM 的特性。作者页把 Jihoon Hong 列在 Hyunseung Lee 之前，正式 program/publisher 顺序相反；题名、五名作者及 IEEE Paper 链接仍对应同一条目，差异明确保留。网页页脚 2025–2026 不代表论文发表年；正式 14 页未取得 PDF，计 0。
- **SuperCore** 的对象为低温 SFQ 处理器及量子计算、天文、计量应用；摘要中的 **4 K 是低温条件**。与低温 CMOS 的性能/功耗比较不能充当常温 AI 数据中心收益。机构 DOI、作者、1532–1547 页和 2024 会议日期匹配；宿主机构网页不等于每名作者发表时单位。正式 16 页没有 PDF，计 0。

## 缺口与获取边界

11 次静态 HTTP 请求：9 次 200、2 次 202 空响应。成功状态不自动代表有效论文：

- 104：`https://ieeexplore.ieee.org/document/10764438` 一次返回 202，0 字节。检索发现产品文档、LLM-TPU 项目及第三方论文阅读文章，均不能替代这篇论文的一手完整摘要，未纳入阅读数。
- 106：`https://ieeexplore.ieee.org/document/10764661` 同样一次返回 202，0 字节；之后从作者 `https://billcho.net/publications` 得到完整摘要，因而摘要完成、PDF 缺口仍在。作者首页只有入口，本轮没有把主页全文记作阅读。
- 110：第一作者清华主页的 PDF 入口指向 `https://www.computer.org/csdl/proceedings-article/micro/2024/505700b489/22niwCmIYEw`，HTTP 200 返回的仅为 `csdl-app` 外壳，无文章摘要。未执行其中 JavaScript。清华组目录该标题的 `href` 为空；共同作者 Yuhao Zhang 的 PDF 链接仍是 ACM 出版商入口。本轮已读三个作者/机构目录中的目标书目后收束，没有把书目、接收新闻或搜索摘要当完整论文摘要，也没有继续追取 ACM 或重试受限站点。目标链接原值见 `selected-links.json`。

本轮未使用第三方解读作为结论依据，没有执行下载代码、工件、框架、模型、GPU 任务或模拟器。`fetch.py`、`build_proof.py`、`verify.py` 都是自写静态归档/提取/核验脚本。PDF 仅用本地 Poppler 提取、渲染与 `pdfinfo` 检查。

## 核验与交付文件

运行 `python references/proceedings/MICRO/2024/parallel-abstracts-eleventh/verify.py`，结果 **PASS**。核验原始及复用文件字节/SHA、86 篇快照与前十包去重、正式身份、作者/标题差异、PDF 15+15 页、字节一致的提取、HTML 字符区间、实际视图记录与 0 正文的范围声明。

- `abstracts.json`、`abstract-098.txt`、`abstract-102.txt`、`abstract-106.txt`、`abstract-113.txt`：正式身份、完整摘要、取舍、缺口。
- `sources.json`、`reused-sources.json`、`input-*.json`、原始 `.pdf/.html/.response`：可复核来源和选择快照。
- `paper-098-*`、`paper-102-*`、`*.html.txt`、`selected-links.json`、`extraction-log.json`：局部提取、实际首页图像及版本/入口记录。
- `reading.json`、`verification.json`、`verify.py`：实际阅读范围与独立核验。
- `fetch*.json`、`fetch.py`、`build_proof.py`：本轮自写获取与派生记录方法。

若根任务合入，应只新增 4 篇摘要、2 份 PDF、30 页；不增加正文选读数。由 86/74/1137 增至 90/76/1167，前提是根任务整合时没有其他并发批次改变正式基数。
