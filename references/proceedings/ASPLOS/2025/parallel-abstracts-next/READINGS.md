# ASPLOS 2025 相邻缺口：146—153

本批锁定当时仍缺摘要的 146、147、148、149、150、153，跳过已完成的 151、152。完成 5 篇一手完整摘要，归档 4 份 PDF，共 65 页；150 仍缺一手完整摘要。PDF 只看首页的摘要、题名、作者和出版信息，4 张首页图像均已看；**正文选读 0 页**。全文文字仅由工具抽取用于归档与核验，没有把归档页数计为阅读页数。

| 序号 | 论文与版本 | 摘要筛选决定 |
| --- | --- | --- |
| 146 | Performance Prediction of On-NIC Network Functions with Multi-Resource Contention and Traffic Awareness；arXiv:2405.05529v5，2025-02-09，系统名 Yala | 候选。单看 NIC 算力或链路带宽不能预测共置网络函数的性能，板载加速单元、内存与流量属性共同影响结果。适合资源瓶颈分析，不能把 BlueField-2 摘要结果直接套到新一代 NIC。未读实验正文。 |
| 147 | Gigaflow: Pipeline-Aware Sub-Traversal Caching for Modern SmartNICs；作者仓库的 ASPLOS 2025 稿 | 候选。有限规则缓存中重复存储完整处理路径会浪费容量；共享子路径是另一种切分与复用选择。摘要的命中率、规则覆盖率是不同指标，不等同于应用吞吐加速。未读协议或实验正文。 |
| 148 | TNIC: A Trusted NIC Architecture，副标题 A hardware-network substrate for building high-performance trustworthy distributed systems；arXiv:2502.05338v1，2025-02-07，另归档 TUM 的正式版式 PDF | 已筛选，暂不新增书中候选。论文主要针对 Byzantine 场景的信任基础与安全接口，和当前 AI 工作负载量化主线的直接关联弱。摘要中的最高 6 倍结果不作为通用 SmartNIC 卸载收益。 |
| 149 | Einsum Trees: An Abstraction for Optimizing the Execution of Tensor Expressions；作者项目官网提供的摘要，按静态资源字节固定 | 候选。先选收缩路径、再分别优化每个局部收缩可能错过全局布局收益，适合解释图优化为何需要保留更高层语义。摘要评测覆盖 Arm/x86 CPU，不宣称 GPU 结果；没有公开论文 PDF 入库。 |
| 153 | 正式论文 Towards End-to-End Optimization of LLM-based Applications with Ayo；CUHK 机构页完整摘要 | 候选。LLM 只是应用工作流的一部分，把模块拆成更小的任务单元才能暴露跨模块流水和并行机会。应围绕端到端延迟理解最高 2.09 倍结果，未读基线与负载正文，不宣称所有 Agent 请求都能取得该收益。 |

## 身份和版本

146 的 [arXiv 页面](https://arxiv.org/abs/2405.05529v5) 明确关联正式 DOI `10.1145/3669940.3707232`；PDF 首页无正式 DOI，因此身份链使用 HTML Related DOI，加上完整题名与四名作者。早期检索会出现 Tomur 名称，本批只读 v5 的 Yala 摘要。

147 的 [作者公开仓库](https://github.com/AnnusZulfiqar2021/AnnusZulfiqar2021.github.io) 中 `papers/gigaflow-asplos2025.pdf` 固定到树 commit `303e4636b70fda51e81e3b135dc9b1f5279f606f`，原始 PDF 的 Git blob 为 `4d31fe6470faa8d9b1eda5811a1085c55042564c`。首页题名、六名作者、正式 DOI `10.1145/3676641.3716000` 一致。没有用 NSDI extended abstract、poster 或早期 *A Smart Cache for a SmartNIC!* 替换正式摘要。定位时的单次 `gigaflow.pdf` 文件名猜测返回 404，已保留。

148 的 [TUM 归档 PDF](https://mediatum.ub.tum.de/doc/1832929/1832929.pdf) 首页含完整副标题、六名作者与 DOI `10.1145/3676641.3716277`。arXiv 页面题名没有副标题，保留这种差异，不改正式 manifest。

149 的 [作者项目官网](https://einsum.org/) 把摘要放在 Astro 组件的静态数据里。归档 HTML 的 `astro-island` 引用 `/_astro/App.zCov1AVQ.js`；在其 `ps` 数组 `id:1` 对象中，题名、七名作者、正式 DOI `10.1145/3676641.3716254` 与 `abstract` 字段同处一条记录。只用正则定位、JSON 字符串解码读取该字段，**未执行下载的 JavaScript**。ACM PDF 403、实验室旧 `/publications/` 路径 404 均保留；官网没有给出可访问正式 PDF，未补归档 poster。

153 的 [CUHK 机构页](https://research.cuhk.edu.hk/en/publications/towards-end-to-end-optimization-of-llm-based-applications-with-ay/) 提供正式题名、四名作者、DOI `10.1145/3676641.3716278` 和完整 Ayo 摘要。其 [第一作者页面](https://txxx926.github.io/) 在同一出版物记录中将正式 DOI 与 arXiv:2407.00326 链接在一起。该预印本 v3（2025-03-31）题名为 **Teola: Towards End-to-End Optimization of LLM-based Applications**，摘要的系统名也为 Teola，PDF 首页不含正式 DOI。本批把它作为作者明确链接的相关预印本归档，并单独保留其原始摘要；不声称它与正式稿逐字相同，不按第二篇论文计数。最初访问的 `cse.cuhk.edu.hk/~hxu/` 属于 Hui Xu，与 Hong Xu 并非一人，HTTP 200 原页仍保留并标记排除。

## 150：保留缺口

正式题名为 *Optimizing Deep Learning Inference Efficiency through Block Dependency Analysis*，DOI `10.1145/3676641.3716264`。[作者出版物页](https://yaozhujia.github.io/publications/) 的 `#BlockDepend` 与 manifest 的十名作者、题名和 DOI 对应，但只链接 ACM 与 slides。Crossref 无 `message.abstract`；ACM PDF 返回 403；作者公开仓库树只定位到演示稿，没有论文 PDF。本批不以 slides、题名或其他论文引用补计完整摘要。不评价论文结果；后续需要一手原始摘要或公开论文稿。

所有候选决定仅供父任务后续围绕章节问题选择正文，本批不扩张大纲、不增加实验、不改章节编号，也没有下载运行论文实现。
