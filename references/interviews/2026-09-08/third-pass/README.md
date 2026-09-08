# 第三批面试与能力方向资料

获取于 2026-09-08，原件、状态与哈希见 [sources.json](sources.json)。本批增加一份官方岗位说明、一份作者署名的 RL 问题汇总、一份公开答卷，以及两份有作者或平台归属的面试报告。重复入口、镜像和失败响应另计，不把文件数量当作面试人数。

| 资料 | 已读范围及日期依据 | 采用方式 |
| --- | --- | --- |
| [Anthropic Performance Engineer, Inference Systems](anthropic-performance.html) | 职责、要求与代表项目读完；页面未给可核实的发布日期 | 官方岗位要求重视从服务到内核的定量诊断，并把数值与质量回归纳入性能工作。用于检验第 5／9／13 章的能力方向，不称为公司原题。 |
| [Xiuyu Li 的 RL Interview Questions 2026](rl-questions-original.html) | 引言、19 个算法问题与 16 个 Infra 问题读完；原帖显示 2026-06-06，镜像时间为 16:21:20 UTC | 作者明确说明是从知乎面经、讨论和观察整理的问题，没有逐题公司归属，也没有参考答案。只取训练／推理一致性、异步样本与状态、资源配比等方向，改编为 I17／I18；不按作者当前雇主归成某家公司考题。 |
| [Vivek 的公开答卷](rl-answers-original.html) | Infra 16 个题位和算法第 11 项已读；原帖时间为 2026-06-07 10:20:41 UTC | 是个人作答，不是出题公司的答案。作者明确保留未读或不确定项；精度选型、KV 保留代价与框架比较中的概括须重查原始资料，不直接采用。 |
| [Anthropic Safeguards 报告](anthropic-safeguards-report.html) | 主帖及技术轮描述读完；[目录](anthropic-exponent-index.html)标明面试月份为 2026 年 1 月，提交于 4 月 13 日 | Aced／Exponent 平台整理，页面有 Verified 标记，认证方式未由本书独立核实。报告涉及 profiling 数据整理、缓存和批处理服务；用于 I05／I08 的方向交叉检查。`asked_on=2026-01-01` 是月份字段的表示，不写成 1 月 1 日面试。 |
| [月之暗面 Desktop 研发工程师面经](moonshot-desktop.html) | 主帖读完；`createdAt=1785395186000` 对应 2026-07-30 15:06:26 +08:00；正文只写“7 月 23 号” | zero_51 发布的未独立核实报告，角色偏桌面产品前端。只保留多模态上下文、任务状态与端云链路的邻近方向，不归纳为模型 Infra 或 GPU 岗位门槛，也不据此扩张章节。 |

原 X 页面经 web 工具返回 403 后，普通 HTTP 请求成功取得公开可见文章；没有借助登录账号。问题原帖的 49 个正文块与 [FxTwitter 镜像](rl-questions-mirror.json)逐项对应，结果见 [question-provenance-check.json](question-provenance-check.json)。[答卷镜像](rl-answers-mirror.json)仅作获取与日期交叉检查。知乎原地址仍为 403，失败响应保留；不能声称已阅读知乎原版。

[问题二次分析](rl-questions-lead.html)与[答卷二次分析](rl-answers-lead.html)只读引言及原帖链接，作为寻源线索，未把二次答案整体读完。Aced 目录中的另一份报告发生在 **2025 年 9 月**，虽然提交于 2026 年，也不计为 2026 面试。搜索中遇到的付费摘要和培训整理未用于补全看不到的题目。

本批问题方向归并为：数值与策略一致性、长尾与异步供给、模型／KV 状态、并行通信、有效进展。多数已经由第 5／6／9／10／11 章覆盖，只在既有实验中补对照；[精选问题](../../../../research/2026-infra-survey/interview-directions.md)增加两个 RL 改编题。当前样本仍不足以给出公司的考题频率。
