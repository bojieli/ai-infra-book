# MICRO 2024 第十批摘要筛选

正式覆盖快照为 **84 篇完整摘要**。与前九包去重，排除已有失败 13／19／26／32／38／40／51／57／65／82／97 后，锁定最早六项 **84、85、86、91、95、96**。只写本目录，不改共享索引、提纲或 Git。

本批取得并读完 **2 篇一手完整摘要**，保存 **2 份作者 PDF，共 31 物理页**，实际查看 2 张首页的身份与摘要。**正文阅读 0，论文图机制阅读 0，正文候选 0，备查 2，另有 4 项访问／摘要缺口**。没有把机构书目、答辩简介或搜索片段计为完整论文摘要。

| 序号、正式 DOI 后缀 | 取得的证据 | 判断 |
| --- | --- | --- |
| 84 Ghost Arbitration，`.00086` | KAIST 作者目录；IEEE 返回 202 空响应 | 完整摘要未取得，不由题名补写机制 |
| 85 IvLeague，`.00087` | 第一作者公开 16 页 PDF 的完整摘要 | **备查**。隔离完整性树元数据、动态容量和热页优化有架构取舍价值；对象是安全处理器，不是现成 Agent 沙箱功能，暂不展开 |
| 86 Veiled Pathways，`.00088` | 共同作者公开 15 页 PDF 的完整摘要 | **备查**。可帮助第 1 章系统边界与 GPU 共享资源讨论：核心／显存之外还有 uncore 路径。未读评估条件，不能据 2024 摘要断言当前所有 MPS／MIG 配置的安全性，也不能由泄漏结果推导吞吐干扰 |
| 91 Terminus，`.00092` | MIT 作者目录；IEEE 返回 202 空响应 | 完整摘要未取得；目录和博士答辩简介不作正式论文摘要 |
| 95 TMiner，`.00096` | IEEE 返回 202 空响应；ICT 新闻请求在 TLS 验证阶段失败 | 未取得完整摘要，不推断图挖掘任务调度细节 |
| 96 PointCIM，`.00097` | NTU 机构书目及公开嵌入状态；IEEE 返回 202 空响应 | 没有论文摘要或 PDF，正式页码不计可用 PDF 页数 |

共同 DOI 前缀为 `10.1109/MICRO61859.2024`。不因为需要覆盖会议而引入攻击操作、通用安全专题或未经核查的性能表。

## 版本与身份

**IvLeague：** [第一作者公开稿](https://hafizul-islam.com/files/papers/ivleague.pdf)生成于 2024-10-28，16 页；题名、两名作者匹配正式 1153–1168 页，未证明等同出版商字节。首页作者名写作 `Md Hafizul Islam Chowdhuryy`，摘要中的缺词表述 `we IvLeague-Invert` 原样保留，未静默修正文献。

**Veiled Pathways：** [Dinghao Wu 的 PSU 公开稿](https://faculty.ist.psu.edu/wu/papers/Veiled-Pathways.pdf)生成于 **2024-11-21**，晚于会议；15 页，题名及七名作者匹配正式 1169–1183 页。公开稿自第 1 页编号，不当作会议当时的出版商原始文件。这里只读摘要，不判断其攻击前提、设备版本或后续修复状态。

**Ghost Arbitration：** [KAIST 作者目录](https://icn.kaist.ac.kr/index.php/publications/)题名带 `in GPU`，program 题名无该后缀；作者目录写 `Hans Kasan`，program 写 `Hans Kason`。原值分开保存，没有据拼写差异制造两篇论文。该条目没有公开 PDF 链接。

**Terminus：** [MIT 作者目录](https://people.csail.mit.edu/sanchez/)仍有 2024 年 `to appear` 的旧条目，没有 PDF 链接。保留目录时间和正式出版记录的区别。

**PointCIM：** [NTU 机构记录](https://scholars.lib.ntu.edu.tw/entities/publication/39c231c4-46a1-40d5-a55a-5e54a78c4921)提供题名、三名作者、DOI、2024-11-02 和 1309–1322 页，没有可见摘要或公开 PDF。页面已返回的 `dspace-angular-state` 作为 JSON 数据静态解码，搜索到的 **23 个含 abstract 的键全部位于 `NGX_TRANSLATE_STATE`**，只是界面翻译。没有执行脚本，没有将 “Abstract” 标签当作摘要，也没有通读整个状态对象。解码衍生物及键路径检查单独保存。

## 失败记录与核验

[sources.json](sources.json) 保存 **10 次获取尝试**：**5 次 HTTP 200、4 次 HTTP 202 空响应，以及 1 次 TLS 证书验证失败**。后者没有 HTTP 响应，不能计为 HTTP 状态错误或成功下载。TLS 失败文件为 `tminer-institution-news.html`，保留空文件和异常记录；未关闭证书验证。四个 IEEE 受限路径均只访问一次，没有重试。

[reused-sources.json](reused-sources.json) 保存正式 manifest、84 篇覆盖快照及前九包摘要快照，共 **11 个输入文件**。[abstracts.json](abstracts.json) 保存完整原文、字符区间、版本与缺口；[reading.json](reading.json) 保存实际阅读和视读声明。[verify.py](verify.py) 独立核对来源字节、最早未读项选择、原样 PDF／HTML 提取、PointCIM 数据解码与计数，结果见 [verification.json](verification.json)。

没有执行下载代码、攻击工件、框架、模型、模拟器或 GPU；只使用自写归档、静态提取和离线核验程序。
