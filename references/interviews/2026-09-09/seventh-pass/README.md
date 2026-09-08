# 第七批：算子实现与硬件演进的个人记录

三篇原帖均来自同一位公开署名为“牛客321612057号”的作者。已读主帖内容和原页 SSR 时间字段，未把推荐内容、评论或平台自动生成的问题算入原帖。以下是个人自述，不能当成公司官方题库或三个独立候选人的样本；发布日期也不自动等于面试日期。[原始响应](sources.json)与[阅读记录](reading-proof.json)保留校验信息。

| 原帖 | 原页时间（UTC+8） | 采用范围 |
| --- | --- | --- |
| [快手 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/490dbb6cdebd4d42ad2bc46757d433af) | 2026-04-14 22:38:36 | 主帖列出 grouped GEMM、注意力实现的代际区别、Hopper／Blackwell 变化及执行故障排查。作为第 4、5 章和 I06／I08 的方向依据，不采用未给出的答案。 |
| [硅基流动推理 Infra](https://www.nowcoder.com/feed/main/detail/c4ef77e57ee74385bc00cd52c1bd5f09) | 发布于 2026-04-13 18:18:04，编辑于 18:18:20 | 主帖围绕 CUTLASS 的布局与流水、bank conflict、block reduction 和 RMSNorm。接已有访存、分块与 profiling 练习，不再加一组术语问答。 |
| [面壁智能 RL Infra 二面](https://www.nowcoder.com/feed/main/detail/683814c5627f461582c718950cd0fc64) | 2026-04-20 20:53:08 | 原页只有一句面试动态，没有题目正文或图片。只归档线索，不计作 RL 面试问题证据。 |

书中采用的追问仍从具体工作量开始：grouped GEMM 要给各专家矩阵形状和 token 分布；布局与流水要算实际搬移、片上容量和等待；硬件演进要对应前文的 workload。原帖没有这些完整推导。底层参数与挂起诊断暂作进一步核查线索，不因原帖并列两个名词就断言它们有直接因果关系。

本批新增两个有具体方向的主帖，来自一位作者；不增加现有 21 道精选题、章节、实验或图号。核对命令：`python research/2026-infra-survey/verify_interview_seventh.py`。
