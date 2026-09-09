# MICRO 2024 第九批摘要筛选

按封存时 **80 篇完整摘要**的正式覆盖快照，与前八包去重，排除既有失败 13／19／26／32／38／40／51／57／97，锁定最早六项 **65、76、77、79、80、82**。本包不改共享索引、提纲或 Git。

完成 **4 篇一手完整摘要**：76／77 使用作者 PDF，79 使用 SNU 机构成果记录，80 使用 CRAFT 作者实验室成果页。保存 **2 份公开 PDF，共 31 物理页**，实际查看 2 张首页的题名、作者和完整摘要。**正文阅读 0，论文图机制阅读 0，新增正文候选 0**。两份 HTML 完整摘要不虚构 PDF 或可用页数。

| 序号、正式 DOI 后缀 | 摘要内容与边界 | 筛选 |
| --- | --- | --- |
| 65 Ring Road，`.00069` | 作者页确认极坐标 NoC 论文身份；出版商返回空响应，没有取得完整论文摘要 | **未取得**；不以标题或中文介绍替代 |
| 76 HSU，`.00079` | 将光追单元的数据通路扩展到层次化搜索，针对分支、递归和专用图形接口的限制；摘要明确包含近似近邻与 B-tree | **备查**；可服务第 4 章专用单元取舍，但属于硬件扩展方案，不能写成当前 GPU／检索框架已有能力 |
| 77 TTA／TTA+，`.00080` | TTA 扩展固定计算，TTA+ 进一步模块化并可编程，以部分效率换取适用范围；针对不规则树遍历 | **备查**；与第 4 章有关，暂不新增正文；B-tree、N-body、光追的结果不能换成大模型收益 |
| 79 NeuroLobe，`.00082` | 脑机接口的脉冲事件计算；摘要列出指令扩展、连接控制、同步、负载平衡、多任务及四种 BCI 算法 | **排除**；本书没有相应贯穿负载，不因含调度等词而引入 BCI 章节 |
| 80 ActiveN，`.00085` | RISC-V 多核配合 active message、稀疏转发，以缓解存储延迟并支持片外突触存储；对象为 SNN | **备查**；可提示第 4 章容量与执行组织的关系，摘要的 A100 倍率不能移作 Transformer 对比 |
| 82 COMPASS，`.00083` | 作者成果列表有身份信息，但 Paper／Code／BibTeX 为占位链接；出版商返回空响应 | **未取得**；不据题名推断机制或性能 |

正式 DOI 的共同前缀为 `10.1109/MICRO61859.2024`。本批 **备查 3、排除 1、访问缺口 2**，没有因为会议覆盖工作而扩大书的正文范围。所有性能陈述仍处于摘要证据层级，未核正文评估条件。

## 来源身份与版本

- **76** [第一作者 Aaron Barnes 公开稿](https://aaronbarnes.org/assets/pdf/AaronBarnes_MICRO24.pdf)，14 物理页，题名及三名作者匹配正式 1027–1040 页。PDF 生成于 2024-09-25 UTC，本地 `pdfinfo` 显示 2024-09-26；未证明逐字节等同出版商版本。
- **77** [共同作者 Tor Aamodt 的 UBC 公开稿](https://people.ece.ubc.ca/aamodt/papers/tta.micro2024.pdf)，17 物理页，生成于 2024-09-13。题名及七名作者匹配正式 1041–1057 页；公开稿自第 1 页编号，不将其当作出版商原始排版。
- **79** [SNU 机构成果记录](https://snu.elsevierpure.com/en/publications/rearchitecting-a-neuromorphic-processor-for-spike-driven-brain-co/)给出完整 Abstract、五名作者、正式 DOI、1073–1089 页与 2024 年会议信息。未取得 PDF，因此正式的 17 页不计入本包可用 PDF 页数。其 citation metadata 与正式元数据将第一作者单位记为 Hanyang，而 program 写 SNU；两种原值保留。作者个人页写 Oct. 2024，机构记录的会议时间为 2024-11-02 至 11-06，不将个人条目的月份当作会议举办时间。
- **80** [CRAFT 实验室成果页](https://craft.cs.tsinghua.edu.cn/publication/activen-a-scalable-and-flexibly-programmable-event-driven-neuromorphic-processor/)给出完整 Abstract、五名作者和 MICRO’24 出版说明。可见页面日期为 **July, 2024**；metadata 的 `published_time` 为 **2024-07-02**，`modified_time` 为 **2025-08-11**，正式出版记录为 **2024-11-02**。这些是网页和会议各自的日期，不推断全文修订号。本页未提供可用 PDF 链接。

## 缺口如实保留

**65 Ring Road：** [作者页面](https://yinxiao-feng.github.io/)的该条目只链接 IEEE，GET 返回 **202、0 B**。搜索看到的另一中文介绍文件未取得为正式论文，也不算完整摘要。未重复访问受限路径。

**82 COMPASS：** [Li Jiang 页面](https://jianglisjtu.github.io/)仅有题名、作者与会议；[Fangxin Liu 页面](https://mxhx7199.github.io/publications/)的题名、Paper、Code、BibTeX 链接都为 `#`。IEEE GET 同样返回 **202、0 B**。不使用第三方摘要片段补齐，不把显示的按钮当作可获取的论文或代码。

## 可复核记录

[sources.json](sources.json) 记录 **10 次 HTTP 响应：8 次 200、2 次 202 空响应**，每项保留 URL、最终 URL、获取时间、状态、原始字节数和 SHA-256。[reused-sources.json](reused-sources.json) 保存正式 manifest、80 篇覆盖快照与前八包摘要快照，共 **10 个输入文件**。

[abstracts.json](abstracts.json) 保存完整原文、提取范围、身份与筛选理由；PDF 的左栏提取原样保留，HTML 采用去除 script／style 后的可见文本，并保存字符区间，没有把两类来源混成 PDF。[reading.json](reading.json) 记录实际阅读、首页视读及辅助身份／日期片段。[verify.py](verify.py) 独立核对最早未读项选择、来源哈希、PDF／HTML 提取、日期 metadata、占位链接与计数；结果见 [verification.json](verification.json)。

只运行自写归档／文本提取／核验程序，没有读取实现源码或执行下载代码、模拟器、模型、工件或 GPU。
