# MICRO 2024 第四批并行摘要筛读

本批选择当前覆盖记录中编号最靠前的六篇未读论文：**4、5、6、7、8、9**。开始时共享覆盖仍显示 52 篇完整摘要；因此额外用已交付第三批的快照去重，并排除之前受阻的 51、97。没有把已经交付但尚未进入共享覆盖的论文重新读取。

六篇的**完整一手摘要均已取得**：3 篇来自匹配的公开 PDF，3 篇来自作者机构的完整摘要记录。匹配的 PDF 共 **43 个物理页**，实际查看 **3 张第一页图像**。**正文阅读为 0 页**，没有读或执行源码，没有修改共享索引、大纲或 Git。另有一份 16 页的搜索误匹配 PDF 独立保留，不能计为本批第四份公开稿。

| 序号 / DOI 尾段 | 论文 | 本次来源和身份 | 结果 |
| --- | --- | --- | --- |
| 4 / 00014 | CamPU | KAIST 完整摘要记录，2 位作者与 DOI、50–63 页对应；第一作者题录链接出版社，出版社空响应；未取得公开 PDF。 | 备查 |
| 5 / 00015 | AdapTiV | KAIST 完整摘要记录，3 位作者与 DOI、64–77 页对应；作者实验室列表确认题目，未发现可下载公开稿。 | 备查 |
| 6 / 00016 | Fusion-3D | NSF 公开存储库的 14 页稿，首页题目与 9 位作者对应；作者实验室页面另有同文完整摘要。 | 备查 |
| 7 / 00017 | Secure Prefetching | 合作者 Alberto Ros 的大学目录下 13 页稿，首页题目与 4 位作者对应。 | 不采用 |
| 8 / 00018 | HyperTEE | 合作者 Fengwei Zhang 的南科大目录下 16 页稿；首页 MICRO2024、DOI、正式页码 105 和 9 位作者对应。 | 备查 |
| 9 / 00019 | GECKO / EMI Checkpoint | ETRI 完整摘要记录，4 位作者、DOI 和会议相符；作者旧 PDF 链接 404，出版社空响应；未取得匹配公开稿。 | 不采用 |

DOI 前缀均为 `10.1109/MICRO61859.2024.`。作者机构记录或公开稿的身份匹配不等于证明与出版社文件逐字节相同；未获得 PDF 的条目也不虚填 PDF 页数。

## 相关性判断

**CamPU** 从多相机图像处理与 DNN 吞吐不匹配出发，讨论投影数据复用、访问顺序及重叠区域处理。可作为“计算阶段变快以后，图像侧访存可能成为瓶颈”的背景；摘要明确采用 RTL 层模拟。本书已要求压缩多媒体背景，不增加相机投影与拼接专节，也不采用其整机倍率。[作者机构摘要](https://pure.kaist.ac.kr/en/publications/campu-a-multi-camera-processing-unit-for-deep-learning-based-3d-s/)

**AdapTiV** 的有用问题是：减少 token 之前，寻找相似 token 与调度本身要花多少代价。摘要将局部匹配、简化相似度、动态合并率与专用硬件结合，并尝试在 Layer Normalization 期间隐藏合并开销。适合模型与硬件取舍备查；这里是特定 ViT 的方案，不能直接推广到 LLM、MoE，或把摘要的跨平台倍率用于本书案例。[作者机构摘要](https://pure.kaist.ac.kr/en/publications/adaptiv-sign-similarity-based-image-adaptive-token-merging-for-vi/)

**Fusion-3D** 将 NeRF 的三阶段与跨芯片搬运一起考虑，可以备查整体设计与分块的关系。但用户已经限制多媒体篇幅，暂不引入新的 NeRF 贯穿案例。摘要涉及流片原型、实芯片测量作为基础的模拟，以及多芯片原型与进一步模拟，不能将全部性能数字合并叙述为实机测得。只读摘要，具体配置、对比基线与仿真条件未核实。[NSF 公开稿](https://par.nsf.gov/servlets/purl/10574254)

**Secure Prefetching** 研究安全缓存与预取器的交互：重复流量、提交时才触发预取带来的时效性损失。需要先建立 GhostMinion 等微架构与威胁模型，且当前主线没有相应的 AI 负载证据。保留完整摘要供会议覆盖核验，**不采用为本书正文候选**。[合作者公开稿](https://webs.um.es/aros/papers/pdfs/snath-micro24.pdf)

**HyperTEE** 将 enclave 管理任务放到独立、物理隔离的管理子系统，并在 FPGA 上做原型。可作隔离边界的背景；这不是容器、microVM 或 Agent sandbox 已部署的机制，也不能据摘要证明任意安全性或生产可用性。暂不新增安全架构专节。[合作者公开稿](https://cse.sustech.edu.cn/faculty/~zhangfw/paper/hypertee-micro25.pdf)

**GECKO** 处理能量采集、间歇供电 IoT 设备中 checkpoint 受到 EMI 干扰的问题，摘要给出编译器驱动的防护和真实开发板实验。这与训练系统 checkpoint 或 Agent 云环境的约束不同，**不采用为本书正文候选**。机构记录的 `pp.1–15` 与出版社 `pp.121–135` 页码不同，两者都是 15 页；保留各自写法，不虚构为版本变化。[ETRI 完整摘要](https://ksp.etri.re.kr/ksp/article/read?id=69712)

本批 **0 个新增正文候选、4 篇备查、2 篇不采用**，不因完成会议覆盖而扩张书的内容。

## 获取和身份核验中发现的问题

1. **HyperTEE 的文件名不能用于判断年份。** URL 虽名为 `hypertee-micro25.pdf`，首页明确为 MICRO2024，DOI 尾段 `.00018`，与本批文献一致。
2. **Fusion-3D 的 PDF 字符映射有误。** Poppler 将摘要内 4 个乘号提取为 `→`，将 `≤`、`≥` 分别提取为 `↑`、`↓`。`paper-006-left-column.txt` 保存原始结果，`text-corrections.json` 记录 4 处替换操作、共 6 个符号修正，`paper-006-left-column-corrected.txt` 保存核对文本。修正依据是实际查看的第一页图像，作者实验室的完整摘要也提供了同样符号。原 PDF 字节未改动，数字或措辞没有另行修订。
3. **一个搜索结果实际是另一篇论文。** NSF `10590071` 的 PDF 首页与 metadata 都是 *LightWSP: Whole-System Persistence on the Cheap*，属于程序序号 16，不是本次目标 9。响应原字节保留为 `identity-mismatch-nsf-10590071.pdf`；首页提取中包含其摘要，用于识别后即排除。本次没有对该文作正式筛选或正文判断，也没有把它加进六篇摘要／三份匹配公开稿的统计。所生成第一页图片没有进一步查看。记录在 `reading.json` 和 `acquisition-notes.json`。
4. **GECKO 作者链接已失效。** 404 HTML 原字节保留为 `emi-author-pdf-404.response`，不是 PDF。成功获取 ETRI 完整摘要不等于获得了该文全文。

共保存 **16 次 HTTP 响应：13 次 200、2 次 202 空响应、1 次 404**。13 次 200 中有上述一份身份错误的 PDF，成功下载不等于文献身份通过。CamPU、AdapTiV、GECKO 均没有匹配公开稿；其完整摘要来源另有清楚记录。没有重试 Atomic Cache 或 Blenda。

原始响应 URL、状态、时间、字节数与 SHA-256 见 `sources.json`；快照见 `reused-sources.json`；完整摘要与字符范围见 `abstracts.json`；实际阅读与图像散列见 `reading.json`。离线执行 `python references/proceedings/MICRO/2024/parallel-abstracts-fourth/verify.py` 可复核原始字节、去重、身份键、正文为零的计数、PDF／HTML 提取、符号修正与误匹配排除；结果保存为 `verification.json`。它不验证论文性能结论或威胁模型。
