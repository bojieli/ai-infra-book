# 第四批：公开考核与 Agent 平台面试方向

2026-09-08 获取 15 份成功响应，原件、哈希、版本与读取范围见 [sources.json](sources.json)。文件数不代表独立候选人数。本批有一条 MiniMax 候选人报告链、两份商业平台整理，以及既有官方考核的源码补充；答案另用官方技术资料验证。

| 来源 | 日期与已读范围 | 采用方式 |
| --- | --- | --- |
| Anthropic [公开考核 README](takehome-readme.md)、[机器](takehome-problem.py)、[基线](takehome-kernel.py)、[提交测试](takehome-tests.py) | 固定 [提交身份](takehome-identity.json) `5452f74…`，提交于 2026-01-22。README／提交测试全文；机器 1–151、197–335、352–397、406–570，基线 1–229。未读 trace UI，未运行程序。[冻结机器](takehome-frozen.py)与机器文件字节相同，未另算一次源码阅读。 | 补充先前已读的官方 2026-01-21 考核文章，不算新的候选人面试。单核、模拟周期、参考验证与历史起点用于 I01／I08；不是当前限时原题或录用阈值。 |
| [MiniMax 平台研发一面](minimax-first.html)与[二面](minimax-second.html) | 爱写代码的菜coder 的主帖全文；发表时间分别为 2026-08-20 23:13:08、08-25 18:49:21 +08:00，主帖 `createdAt` 核对。标题写 8.17／8.19，年份从发表上下文推断，并非正文明确年份。 | 一位候选人的两轮自述，未独立认证。数据采集、反馈与 Agent 周期观测用于 I19／12.5；不扩成 GPU 或训练内核岗位要求。文中的采集对象描述简略，不补造其 SDK 或生产实现。 |
| [Anthropic EM Data Infrastructure 报告](anthropic-em.html)与[目录](anthropic-em-index.html) | 可见主帖与各轮说明读完；目录条目 9144 的 `asked_on=2026-04-01` 按月份记为 2026 年 4 月，发布字段为 2026-08-17。页面 Verified 标记未由本书独立认证；平台未披露原作者来源。 | 已有推理设计的审阅、端到端解释和取舍支持第 13 章练习形式。没有公开原设计图，也不将 EM 的管理轮改造成技术题。 |
| [PracHub 的 Anthropic 推理系统设计报告](anthropic-prachub.html) | 可见正文全文；标示面试为 2026 年 7 月，`datePublished` 为 08-24。署名是 PracHub 编辑组织，未见候选人原帖链接。 | 商业平台编辑叙述，证据弱于可追溯自述。批处理、理论与在线吞吐、GPU 路由只交叉检查 I05；“约 70%”是叙述者经验，未提供条件，不能成为答案依据。 |
| [MiniMax AI Infra 二次题库](minimax-guide.html) | 仅本页题目、日期、链接读完；页面标 2026-04-17，未给逐题原帖／候选人归属。 | 保留寻源线索，不作新面试样本。MoE 与 RL 方向已有覆盖，未据此加题。 |
| [OpenTelemetry 韧性](otel-resiliency.html)、[采样](otel-sampling.html)与 [Kafka 4.2 设计](kafka-delivery.html) | 韧性主文全部；采样从引言至 Tail Sampling，未读 Support 列表；Kafka 只读 Message Delivery Semantics／Using Transactions。获取日期不当作功能引入日期。 | 官方答案依据，非面试证据。支持缓冲／重试边界、trace 采样与外部操作的一致性范围；不照搬文档中的未校准时间或默认配置。 |

[日期与源码核对记录](reading-proof.json)保留主帖身份、月份字段、冻结文件相等及静态语句计数；[教学计算](../../../../case-studies/evaluation-and-agent-records.md)接入既有小节和实验。精选题由 18 增为 19，增加的是一项 Agent 记录问题，未增加书的章节或实验。

本轮检索还遇到 RockyDing／WeThinkIn 的 DeepSeek 题库、商业 interview pack、无逐题出处的 Substack 假设问答及普通后端面试，未纳入公司原题。搜索结果只提供线索；没有用搜索摘要填补付费或不可见的正文，也没有把同一作者两轮或平台镜像重复计样本。
