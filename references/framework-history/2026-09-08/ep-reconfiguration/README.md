# 专家分派与弹性 EP：读取范围

2026-09-08 归档 [17 份成功响应](sources.json)：两篇官方文章、两份固定 guide、七份固定源码、六份 PR 身份响应。[读取证明](reading-proof.json)逐项列出正文、源码行范围及仅查看 PR 开头的范围；没有导入或执行下载的代码。采用位置和计算见[专家分派与重配](../../../../case-studies/expert-dispatch-and-resizing.md)。

vLLM 固定为 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`，SGLang 固定为 `c99d906effa8bd05573995127f0d4a0984c5a96a`；身份复用[前批 vLLM tree](../speculative-execution/vllm-tree.json)与[SGLang tree](../overlap-placement/sglang-current-tree.json)。日期分清文章发表、PR 合入和取样，不由当前 main 推断每个已发布版本。

| 来源 | 实际读取与用途 |
| --- | --- |
| [vLLM Elastic EP 文章](vllm-elastic-2026.html)、[抽取正文](vllm-elastic-2026.txt) | 完整正文，标题与 2026-05-14 日期；解释扩／缩容状态交接及文章当时的限制。未读取 NIXL 实现、全部调用链或故障恢复协议 |
| [SGLang Waterfill／LPLB 文章](sglang-waterfill-lplb-2026.html)、[抽取正文](sglang-waterfill-lplb-2026.txt) | 完整正文，标题与 2026-06-26 日期；分派机制、实验表的任务条件。未查看文章图片或 benchmark artifact；不引用加速比为当前服务承诺 |
| [vLLM guide](vllm-current-ep-guide.md) | 136–189 行；窗口单位与冗余容量。表中 per-rank 描述与下方全局冗余公式存在歧义，“overhead”公式也包含原有专家；教学直接从矩阵与明确全局副本数算，不照抄该公式标签 |
| [SGLang guide](sglang-current-ep-guide.mdx) | 240–246 行；与 manager 的迭代计数比较。文中 requests 例子不等同 engine steps |
| [SGLang dispatch](sglang-expert-location-dispatch.py)、[LPLB solver](sglang-lplb-solver.py) | 两文件全文；合法物理副本、概率分派、空 rank 归约、支持架构检查和求解状态。未读取 CUDA 内部求解／采样内核，不能声称数值解或有限 batch 精确最优 |
| [SGLang Waterfill](sglang-waterfill.py) | 118–205、266–292 行；静态／动态统计与低 batch 回退。动态回退仍须参加归约；没有逐行核查全部候选选择 kernel |
| [SGLang EPLB manager](sglang-eplb-manager.py) | 80–185、306–351 行；窗口迭代、分层更新、缺失权重的备份／磁盘回退、放置后 LPLB 重建。不是 SGLang Elastic EP 全路径审计 |
| [vLLM API](vllm-elastic-api.py) | 全文；规模请求、drain timeout 及结果接口。接口本身不证明 KV 迁移或无损故障恢复 |
| [vLLM executor](vllm-elastic-execute.py) | 290–345、387–440、568–648 行；权重发送与建组、图释放、scale-up／down 的先后及异步 EPLB 交接。没有完整 executor 或 engine coordinator 审计 |
| [vLLM config](vllm-parallel-config.py) | 59–104、877–899、1016–1022 行；EPLB 默认值、部分 Elastic EP 限制和通信器选择。不能仅凭这些段落推断所有模型、TP 和组合均受支持 |

PR 只读取身份字段、合入时间和正文前 650 字符；没有完整 diff／讨论审计：

- vLLM [34861](vllm-pr34861.json)：2026-02-28 合入；[35627](vllm-pr35627.json)：2026-03-13 合入。5 月文章不是首次合入日期。
- SGLang 共享专家融合 [20089](sglang-pr20089.json)：2026-04-09；Waterfill [19290](sglang-pr19290.json)：2026-05-14；V4 Waterfill [25391](sglang-pr25391.json)：2026-05-26；LPLB [24515](sglang-pr24515.json)：2026-06-16。

三个边界直接影响实验：当前 LPLB 的支持列表不包含 Qwen3／V4；V4 Waterfill 并不意味着 V4 LPLB 已支持。文章 V3 与 V4 都是 `max_tokens=1` 的不同测试形状，total throughput 不能作长 decode 吞吐。保留逻辑专家不等于跨形状／精度逐位复现，RL 另核概率与路由要求。

与本批相连的 [FSMoE 正文](../../../proceedings/ASPLOS/2025/public/paper-094.pdf)已读物理页 1–13，图 3／4 已查看，见[页级记录](../../../proceedings/ASPLOS/2025/fsmoe-reading.json)。其旧硬件、改型模型和公式／标注问题留在[论文阅读记录](../../../../research/2026-infra-survey/reading-asplos-2025.md)，不当作当前引擎功能。
