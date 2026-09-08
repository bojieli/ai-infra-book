# KV 事件与实际路由消费者

2026-09-08 保存 [17 份成功响应](sources.json)。[读取证明](reading-proof.json)逐项记录 15 份来源的实际读取范围；两份 live HTML 仅归档，没有标成正文读完。没有执行下载源码、启动服务或完成全部恢复调用链审计。采用位置见[缓存事件案例](../../../../case-studies/cache-events-and-routing.md)。

Dynamo 固定提交 `946accea5edfd778f5120a3096b082e54e5bce2b`，身份响应中的提交时间为 2026-09-07T22:01:03Z；vLLM 源码沿用 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`。当前仓库与网站文档可能来自不同构建，本文以固定文件说明本轮集成条件，不将差异倒推为历史功能日期。

| 来源 | 读取范围与用途 |
| --- | --- |
| [vLLM 发布器](vllm-current-kv-publisher.py) | 304–392、451–530 行：发布队列、批次序号、有界重放及范围结束；未读全部 offloader 事件产生路径 |
| [vLLM 订阅示例](vllm-current-kv-subscriber.py) | 全文。普通实时分支未更新 `last_seq`，不能直接以此示例证明缺口检测可靠；仅作静态发现，没有运行或修复下载副本 |
| [vLLM 原生 offload 集成](dynamo-native-offload-fixed.md) | 全文；自描述 CPU 事件、各 tier 支持范围、版本与身份限制。固定指南中的 STORAGE 与旧网站／前批 FS、OBJ 说法有版本差异；不替换旧来源的历史范围 |
| [SGLang HiCache 集成](dynamo-sglang-hicache.md) | 全文；host 事件、Mooncake 对象事件、组检查、晚加入和序列缺口边界、DCP 限制。属于 Dynamo 集成，不能并入普通 Model Gateway 的能力 |
| [路由设计](dynamo-router-design.md) | 55–101 行，评分与 worker 选择。评分单位是 block 等价成本，不是命中概率或测得的毫秒数 |
| [配置](dynamo-config-tuning.md) | 294–307、330–336 行；预测树与事件树分开，短 TTL 可过期；没有读完全部调参文档 |
| [事件恢复比较](dynamo-event-recovery-fixed.md) | 全文，有限日志与本地树恢复的区别；对示例代码的解释需结合上述静态发现 |
| [局部索引](dynamo-local-indexer.rs) | 322–382、608–693 行；事件入队、缺口失效及非原子跨层快照的 watermark／后续重放条件 |
| [恢复状态](dynamo-recovery-state.rs) | 58–147、267–289 行；初始、缺口、陈旧事件和恢复期缓冲，未核全部 transport／transaction 实现 |
| [后端 publisher 接线](dynamo-backend-publisher.rs) | 全文；按 DP rank 配置事件来源和 local indexer。另读的 [vLLM metrics publisher](dynamo-vllm-publisher.py) 是负载统计路径，不作为 KV tier 归一化的代码证据 |
| [vLLM 0.24.0](vllm-release-024.json)、[Dynamo 1.3.0](dynamo-release-130.json) | 只读身份、发布日期与 KV/offload 相关行；不是完整 release、PR diff 或讨论阅读。发布日期分别为 2026-06-29、2026-07-22 |

指南的矩阵只能说明其声明及验证范围，不能证明任意硬件、模型、缓存层级都能组合。磁盘／共享池支持分别按后端注明。host hit weight、shared-cache multiplier 是评分系数；示例中恰为 0.5 时的解释不能推广为任意系数都直接等于物理取回与重算的耗时比。

实验基础部分复算排队、取回和重算，选做部分记录实际状态与接收事件的时差。恢复索引不恢复丢失的数据，预测聚集不保证同批前缀已物化；以上两点作为结果解释，协议细节保留在材料中。
