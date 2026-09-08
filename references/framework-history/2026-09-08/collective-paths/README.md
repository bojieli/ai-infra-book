# 集合通信、图缓冲与融合路径

获取与阅读日期：2026-09-08。[八项来源](sources.json)记录 URL、原件哈希、版本和具体选读行。没有执行下载的源码或 benchmark；没有将主线快照当作所有正式安装版本。

| 文件 | 已读内容与采用范围 |
| --- | --- |
| [vLLM v0.6.0](vllm-060-custom-ar.py) | 36–167、220–266 行；同节点 custom AR、NVLink／P2P、注册缓冲与 eager 复制。 |
| [vLLM v0.9.2](vllm-092-custom-ar.py) | 51–177、214–266 行；上述机制的延续及 Python 形状检查。两版发布日期复用[已核元数据](../graph-selection/README.md)。 |
| [当前 custom collectives](vllm-current-custom-ar.py) | 36–85、105–563 行；探测、组级初始化、AR／AG／RS 和 MNNVL；类名与参与者名单不能代替具体操作的支持条件。 |
| [当前 CUDA dispatcher](vllm-current-cuda-communicator.py) | 305–390 行；调用次序与 fallback，未审全部后端构造和 CUDA 实现。 |
| [当前 AR 选择条件](vllm-current-all-reduce-utils.py) | 94–168 行；NCCL symmetric-memory 与 custom AR 的输入范围，batch invariance 等条件；注释中的测点不是通用阈值证明。 |
| [当前融合文档](vllm-current-fusions.md) | 101–128、189–253 行；AR＋RMSNorm、SP 与 AsyncTP；文档所列问题和自动配置可能滞后，实验须核实现。未审 compiler pass。 |
| [SGLang 层间 communicator](sglang-current-layer-communicator.py) | 186–207、928–1003、1218–1318 行；归约融合的前提与混合 EP×TP／散布布局限制，未全量追每个模型入口。 |
| [SGLang benchmark 说明](sglang-current-fused-collective-readme.md) | 全文；同语义基线、CUDA Graph、workspace 和测量方法；示例输出不是本书结果，未下载／运行其脚本。 |

vLLM 当前提交为 `51da0ca66c8065619c79e35dff97aa99aeaf5644`，SGLang 为 `c99d906effa8bd05573995127f0d4a0984c5a96a`。旧 vLLM custom AR 延续至 2025，而当前多个操作和后端各有条件；SGLang 本次是当前实现核对，没有据此宣称融合首次发布于 2026。完整版本史仍在整理。

[采用笔记与推算](../../../../case-studies/collective-paths-and-diagnosis.md)将这些机制接到第 5 章的融合、第 6 章的 TP／通信组、第 7 章的路径与等待，以及第 11 章的训练时序。
