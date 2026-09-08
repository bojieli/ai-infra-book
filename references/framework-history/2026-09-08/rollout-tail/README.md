# RollPacker：rollout 调度与样本边界

2026-09-08 核对，[官方论文入口](https://www.usenix.org/conference/nsdi26/presentation/gao-wei)指向[作者仓库](https://github.com/Farrrrland/RollPacker)。固定 HEAD 为 `1dc8aae739ec4e5651929bd0c9c225b41dcb30f1`，提交时间 2026-03-02T02:07:00Z；此日期不是 vLLM 新特性的发布日期。十份 HTTP 响应的原件、哈希、读取范围见 [sources.json](sources.json)。只静态读取，未安装、导入或执行下载源码及脚本。

| 原件 | 已读范围与用途 |
| --- | --- |
| [提交身份](rollpacker-head.json)、[文件树](rollpacker-tree.json) | 提交 SHA／时间及候选文件路径，不代表全仓库审查 |
| [README](rollpacker-readme.md) | 全文只有标题与容器标记，不能据此声称已有完整复现说明 |
| [vLLM 依赖](rollpacker-requirements.txt) | 全文件；明确 vLLM 0.8.4，引用的公共依赖文件本轮未读 |
| [端到端示例](rollpacker-example.yaml) | 全文件；Qwen2.5-7B、4K 回答、64 prompt、每组 4 回答扩到 5、prompt 比例 1.25；只启用 math 域，autoscaling 和多 TP 关闭。其命名与注释不代表论文全部实验配置 |
| [多域调度](rollpacker-multi-scheduler.py) | 388–450、529–578、969–1145 行：长／短轮次选择、请求提交、奖励后过滤、回答组收集与取消、移除已选 prompt；其余只作关键词定位 |
| [批次奖励调度变体](rollpacker-batcher.py) | 245–312 行：docstring 标注基础流程、部分能力待实现；收够批次后返回。不是从文件名推断它实现完整 tail batching |
| [Megatron 策略](rollpacker-megatron.py) | 214–254、430–525 行：前向准备、no_sync 提前返回、优化器加载与最终 step。未审查下层修改后的累积／归约实现，不声称已由源码证明整批梯度等价 |
| [Megatron 异步 pipeline 变体](rollpacker-pipeline.py) | 1–65、525–578、695–741 行及关键词定位：该变体含禁用生成分支、加载本地 batch_train.pt 和断点；其他入口未据此判定。不是本次实跑路径 |
| [stream trainer 启动脚本](rollpacker-stream-run.sh) | 全文件；调用 examples/start_rlvr_pipeline_async.py，与上述 Megatron pipeline 变体文件不同，未完整追踪入口调用链 |

关键发现是区分论文机制与执行细节：多域调度源码先完成奖励和过滤，再收集回答组，因此“先完成”不只是 GPU 生成时长。代码里的外层 RPC 超时使用参考时间、余量并捕获失败；它不是论文的单测试自适应超时公式。端到端示例中的零方差／难度、长度掩码等过滤也需要单独记录，不能把所有样本变化归于取消长回答。

论文物理页 2–15 的正文已读；正式 PDF 与逐页比较在 [NSDI 2026 归档](../../../proceedings/NSDI/2026/README.md)。实验数值保持 Qwen2.5 与 H800 的历史身份。代码中存在 MoE 配置字段，不表示论文完成了 V4／K3 或 Agentic RL 评估。

采用内容见[长尾与样本算例](../../../../case-studies/rollout-tail-and-sampling.md)：先计算保留分布、额外执行量、KV 与合法时间线，再决定怎样安排资源。书中只补现有 11.5／12.2 及对应实验，不新增系统目录。
