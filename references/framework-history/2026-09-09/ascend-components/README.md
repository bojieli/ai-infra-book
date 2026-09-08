# 昇腾单元分析与实际激活入口

2026-09-09 阅读。六份原始响应、八个声明范围见 [sources.json](sources.json) 和 [reading.json](reading.json)。vLLM Ascend 固定为 `e5118d151314ae18e56c0b63aa8dd00d294adc22`，提交时间 2026-09-08 16:27:22 UTC。树仅用于核四个文件的路径和 Git blob；没有执行下载代码，也没有完整审计仓库。

- [普通激活入口](activation.py.txt)完整 86 行：普通 SwiGLU 调用 torch_npu；带 clamp、OAI 和 Step 的路径分别保留语义与实现。Step 的 Triton 条件和 native 回退不能转述成所有 SwiGLU 共用一个优化内核。
- [310P 入口](activation-310p.py.txt)完整 32 行：末维按 32 对齐时调用 npu_swiglu，否则用原生表达式。这里只核该类本身，尚未核整模型的注册、设备选择及依赖库内核。
- [性能采集指南](service-profiling.md)1–142 行：区分算子和服务范围，核 `--profiler-config`、输出文件与普通 PD 双端采集。后续 MS Service Profiler 细节未读；没有把服务 trace 当作论文全部硬件指标的来源。
- [发行说明](release-notes.md)2357–2388、1320–1368、3–123 行：分别为 2025-02 的初始算子接口、2026-01 的 profiler 迁移，以及 2026-09 的模型限定、后端支持、移除项目和已知问题。这是当前固定快照中对历史版本的描述，不是三个发布 tag 的完整源码对比。没有由 changelog 推断所有实现均可用或加速。

ASPLOS 2025 [正文选读](../../../proceedings/ASPLOS/2025/ascend-components-reading.json)建立单元服务时间、活动比例与执行效率的分析。论文说 41 个算子进入 Ascend 库，但已读证据不足以对应当前 CANN／torch_npu 的具体代码。其 MobileNetV3、PanGu-α／Llama2 和当时芯片条件，与当前 Qwen3／V4／K3、310P／A2／A3／950 的路径分别记录。

采用范围是第 5 章的[同一 Qwen3 激活推算](../../../../case-studies/component-utilization-and-overlap.md)与实验 5-6 的反馈内容：同样 40% 的利用率可以有不同原因；双缓冲需要容量与独立资源；源码入口存在不足以证明整模型支持或设备内核机制。候选不按硬件 busy 百分比单独排名。
