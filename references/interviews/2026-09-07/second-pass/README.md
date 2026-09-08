# 第二批面试方向资料

获取于 2026-09-07，原件、获取方式与 SHA-256 见 [sources.json](sources.json)。这批包括一个岗位目录、四份官方岗位说明、一篇个人面经和两篇带推广性质的整理；不把八个归档文件称为八份公司考题。

| 来源 | 已读范围与证据分类 | 采用范围 |
| --- | --- | --- |
| [Anthropic 岗位目录](anthropic-jobs.html) | 只筛选相关职位链接；官方目录 | 用于找到下列两个原始职位页，不算独立能力样本。 |
| [Anthropic Inference Infrastructure](anthropic-inference.html) | 职位职责、要求与项目示例；官方岗位说明 | 异构加速器、请求路由、负载均衡、扩缩容和部署观察，对应 9／10／12／13。 |
| [Anthropic AI Reliability](anthropic-reliability.html) | 职位主要内容；官方岗位说明 | 从 SDK、网络、API 到加速器的延迟与可靠性，SLO、观测和恢复，对应 8／10／11／13。 |
| [OpenAI Model Inference](openai-inference.web.txt) | 职位主要内容；官方岗位说明 | 生产推理的时延、吞吐、内存、跨设备通信与定位不稳定因素，对应 5／6／7／9／10。 |
| [OpenAI Productivity — Inference Runtime](openai-runtime.web.txt) | 职位主要内容；官方岗位说明 | 数值正确性、TTFT／TBT 性能回归、发布验证和 GPU 测试环境噪声，对应 5／9／13。此岗位强调开发效率，明确不要求既有推理经验，不能替所有岗位归纳统一内核门槛。 |
| [字节 AI Infra 实习面经](bytedance-intern.html) | 主帖读完；Varian 的未独立核实自述 | 主帖机器字段对应 **2026-02-28 16:45 +08:00**，未提供另一个明确面试日期。包含 All-Reduce 开销、TP 行列切分、张量布局、IPC 与图融合。团队未披露，不写成 Seed 组原题。 |
| [月之暗面 Agent 岗整理](moonshot-agent-secondary.html) | 引言及部分问题筛读；RockyDing／WeThinkIn 的培训整理 | 标题声称 2026-07-21，主帖实际发表于 **2026-08-28 00:15:13 +08:00**。带题库推广、不是可认证的本人面试过程；只留 Agent 状态与缓存的检索线索，不采用其答案或计入公司题目频次。 |
| [Anthropic 检查点分发整理](anthropic-checkpoint-secondary.web.txt) | 主帖读完；带 Chill Interview 推广的未核实叙述 | 500 GB 权重分发、共享收发带宽、分块和重试可作后续检索线索。搜索摘要与正文相对时间不能还原一致发布日期，暂不登记确切面试日；不认定为官方或独立认证题目。 |

官方岗位页没有可核实的发布时间，因此只标获取日期，不将其称为“2026 新增岗位”。OpenAI 两页与 Reddit 原 HTML 请求返回 403，随后保存 web 工具成功取得的正文抽取，manifest 保留失败与回退方式；不声称已经取得原始 HTML。`web-fallback.txt` 保留三次抽取的合并原记录，单页文件分别用于引用与校验。

日期只取确认属于主帖的字段：字节帖 `createdAt=1772268300000`，月之暗面整理 `createTime=1787847313000`；推荐文章、评论、搜索抓取日期均不替代主帖时间。原件保留上下文，研究摘要不摘录无关个人资料。

本轮将 All-Reduce 和 TP 行列切分方向改编为 I12／I13，回答用本书已归档的集合通信与模型并行资料验证；MoE 和启动的 I14／I15 来自论文研究，不能算新增面试样本。见[精选问题与回答路径](../../../../research/2026-infra-survey/interview-directions.md)。
