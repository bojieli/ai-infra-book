# 从性能反馈到推理、训练优化

2026-09-07 阅读与扩写笔记。对应第 5、8、9、10、11 章，保存问题、证据范围与实验入口，不是已完成的性能报告。[原件与校验值](../references/outline-checks/2026-09-07/execution-feedback/sources.json)。

## 编译模型与实测反馈

多面体方法首先表达迭代域、访问关系与依赖；isl 的整数集合运算不是一套精确的 GPU 计时模型。语义合法、硬件资源可容纳和预计更快是三个不同判断。成本模型需要考虑硬件，但无法由峰值完全预测缓存命中、寄存器分配、流水与共享资源干扰。参考既有 [AKG](../references/files/papers/akg-pldi21.pdf) 与 [isl](../references/files/documents/isl-tutorial.pdf)。

Ansor 和 TVM MetaSchedule 不是单一固定模板参数搜索；后者明确包含空间生成、候选测量、成本模型更新与记录复用。LLM 可作为这一流程的候选生成器，也可以提出超出原空间的融合与实现。开放空间增加机会，同时增加错误、编译与验证成本；不能声称 Agent 天然单调改进或全局最优。[Ansor](https://www.usenix.org/system/files/osdi20-zheng.pdf)、[MetaSchedule](https://tvm.apache.org/docs/deep_dive/tensor_ir/tutorials/meta_schedule.html)

KernelAgent 的 2026 年官方说明展示 NCU 信号、瓶颈判断、生成与正确性／性能验证的迭代。本文采用该方法，其 H100、KernelBench 和关闭 CUDA Graph 的 torch.compile 基线条件不能省略。文章的硬件 SOL 百分比也不能直接称作完整模型 MFU。[KernelAgent](https://pytorch.org/blog/kernelagent-hardware-guided-gpu-kernel-optimization-via-multi-agent-orchestration/)

FlashInfer-Bench 将语义、真实服务形状、候选实现和评估绑定，并提供内核替换路径。它的论文数据包含当时的 V3、Llama 与 Qwen3，不自动代表当前 V4／K3 全部算子。CUDA Agent §3.2 则将验证与 profiling 放入训练优化能力的环境；第 5 章实验无需先训练一个模型。[FlashInfer-Bench](https://arxiv.org/html/2601.00227v1)、[CUDA Agent](https://cuda-agent.github.io/static/pdf/CUDA_Agent_Arxiv_Version.pdf)

实验先由 Nsight Systems 定位真实请求热点，再用 NCU 看该 kernel。计时与 profiler 采集分开：采集开销、缓存状态与设备竞争可能改变时间。候选必须满足参考数值、形状、布局与边界要求；留出未参与搜索的输入。记录 LLM／GPU 费用、未成功候选和最佳结果，计算 `调优总时间／每次节省时间` 的复用阈值。这个算式要求执行条件不变且每次确实节省；若没有收益，不能给出有限回本次数。

进一步对照 LOOPRAG 正文和固定 FlashInfer-Bench 代码，分开数值参考、优化基线、比赛分数与生产调用频数。两个形状的候选排名可以翻转；配置容差与真实分派也需要逐项核对。完整来源和独立计算放在[评测与部署](optimization-evaluation-and-deployment.md)，当前实验 5-6／5-9 直接使用。

## 启动、融合与流水的区别

- CUDA Graph：降低重复提交与调度开销，保留依赖，计入首次捕获、形状桶、padding 和图缓冲。
- 融合：可能减少 kernel 数及中间写回，也可能增加寄存器、片上存储和同步压力。
- Persistent／mega-kernel：把更细任务及调度放到设备内，改变原有 kernel 边界，增加任务队列和同步代价。
- Pipelining：重叠独立或已满足局部依赖的工作；切分后可能增加启动和小矩阵损失，不自动降低总 launch 数。

MPK v2（2026-06）的 §3–5 采用 SM 级任务／事件表示及设备内运行时，Qwen3 是其评估对象之一。本书用它说明 tile 就绪与算子整体完成的区别，不直接推广其 batch、型号和软件版本之外的加速数值。[MPK](https://arxiv.org/html/2512.22219v2)

NanoFlow（OSDI 2025）先估资源互补，再通过并发 profiling 修正干扰，并将请求拆成 nano-batch。其吞吐目标依赖足够请求，不能将该条件当作低并发交互服务的默认。MegaScale-Infer（2025）在 attention 与专家之间做微批 ping-pong；两侧计算均衡、通信可隐藏及足够微批只是近似条件，仍有填充排空与资源竞争。[NanoFlow](https://www.usenix.org/system/files/osdi25-zhu-kan.pdf)、[MegaScale-Infer](https://arxiv.org/pdf/2504.02263v1)

实现对照使用 [vLLM DBO](https://docs.vllm.ai/en/latest/design/dbo/) 和 [SGLang EP](https://docs.sglang.io/docs/advanced_features/expert_parallelism)。已归档 DBO 文档要求 DP＋EP、对应 DeepEP 后端和完整图路径；SGLang 区分两批重叠与同批共享专家重叠。不能拼接不同版本参数制造一条未经验证的启动命令。

## 大 EP 的三种不均衡

模型逻辑专家的路由倾斜、物理 rank 上的总负载，以及单卡 grouped GEMM 内部的 tile 分配分别计算。按每专家 token 数决定 GEMM 的 M，按实际层宽、专家宽和精度计算 FLOPs／字节，再看 dispatch 与 combine 流量。

教学输入 `[32,16,8,4,2,1,1,0]` 共 64 行；若八个专家全部补齐至 32 行，则 256 行，四倍是此 padding 假设下的行数比，不是实测时间比。动态分组与 persistent 调度减少部分浪费，但有元数据、调度和局部性代价。EPLB 通过逻辑到物理映射与副本安排改善 rank 负载，应保持原模型 top-k 语义。[vLLM EP／EPLB](https://docs.vllm.ai/en/latest/serving/expert_parallel_deployment/)

训练加入反向、梯度和激活寿命。阅读 Megatron Core 2026 报告中的 Parallel Folding、细粒度重计算、grouped GEMM、图执行与 RL 部分；用 Qwen3-235B 连接前文，而非把报告中的 V3 吞吐移给 V4。[Megatron Core MoE](https://arxiv.org/html/2603.07685v1)

## Routing Replay 的信息与代价

阅读 R3 v2 §3–4 的不一致分析、mask 重放与多轮缓存。相同权重在训练和推理路径上也可能因数值差异改变离散 top-k；R3 保留生成时的选择，训练仍计算当前 router 分数与专家输出，梯度继续流动。它不消除其他策略滞后或采样概率定义差异。[R3](https://arxiv.org/html/2510.11370v2)

NeMo RL 当前归档文档明确支持 Megatron MoE policy＋vLLM rollout，传递 routed expert indices；MTP 路由默认排除。需要验证 packing、context parallel 切分、生成 token 与路由的对齐，缺失路由可能局部回退到正常 router，不能只检查开关是否开启。[NeMo RL 实现](https://docs.nvidia.com/nemo/rl/nightly/guides/router-replay.html)、[梯度路径](https://docs.nvidia.com/nemo/automodel/nemo-automodel/nemo_automodel/components/moe/router_replay)

教学容量为 `8192 × 48 × 8 × 2 = 6 MiB`；若 ID 为 int32，则 12 MiB。uint16 是明确编码假设，不是对当前引擎 dtype 的断言。多批、前缀、prompt token、mask 与对齐元数据按实际保留范围增加。R3 不等同于经验回放、CUDA Graph replay、激活重计算或 EPLB；这些机制可能同时存在。

## 实验中的开源系统分工

| 角色 | 本书采用的系统 | 对应位置 |
|---|---|---|
| 单实例请求、批处理、KV 和服务入口 | vLLM、SGLang | 8.1–8.3 |
| 本地模型加载、管理与后端选择 | Ollama，区分具体 runner；MLX／llama.cpp 等按版本核对 | 5.5、8.4 |
| NVIDIA LLM 执行与服务优化 | TensorRT-LLM，当前公开实现包含 PyTorch 原生路径 | 8.1、8.5 |
| 通用网络优化与执行 | TensorRT，用于相应图像编码等网络 | 12.1；不是 TensorRT-LLM 的简称 |
| 算子与通信库 | FlashInfer、DeepGEMM、DeepEP、NCCL | 5、6、10；不作为完整推理服务 |
| 多级与共享 KV | SGLang HiCache、LMCache、Mooncake | 9.5 |
| 训练状态与并行 | FSDP、DeepSpeed、Megatron Core | 10.1–10.4 |
| RL 流程、rollout 与更新协同 | verl、AReaL、NeMo RL | 10.5；推理后端和训练后端另行注明 |

角色依据：[TensorRT-LLM](https://nvidia.github.io/TensorRT-LLM/overview.html)、[TensorRT](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/quick-start-guide.html)、[verl](https://verl.readthedocs.io/en/latest/)。这些是制作备注中的对应表；正文随问题引入系统，不新增产品介绍章。

所有实测型实验在扩写时固定引擎、模型配置、硬件、精度、输入分布和关键选项，提供命令与原始 trace；没有设备时使用同一 trace。纸笔计算继续保留，但不能用自写小模拟器替代真实系统的行为证据。近期版本的特性及落点另见[框架演进核对](framework-evolution.md)。
