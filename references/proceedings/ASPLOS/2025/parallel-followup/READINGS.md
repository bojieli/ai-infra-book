# ASPLOS 2025 补读：调优、动态编译与 KV 内存管理

2026-09-09 按 `reading-coverage.json` 缺口选择程序 151、152、182。三篇完整摘要及指定正文段落实际读完，三份 PDF 共 51 页；本次只读了其中 16 个正文物理页和 3 张首页，不能记成三篇全文读完。原始来源、版本、哈希、摘要、页文本和范围见 `reading-records.json`。没有更改总索引、大纲、共享核验器或 Git，也没有执行论文代码、模型、驱动或复现实验。原始下载文件有时以 `.html` 保存 JSON／Markdown／Python 文本，以内容及来源元数据判断格式。

## 151 Pruner：先减少搜索本身的开销

正式题名为 *Pruner: A Draft-then-Verify Exploration Mechanism to Accelerate Tensor Program Tuning*，DOI `10.1145/3676641.3716269`；选择 [arXiv v3，2025-04-09](https://arxiv.org/abs/2402.02361v3)。首页完整 13 作者和 DOI 对上正式清单。较早版本题名为 Speculative Exploration，作者列表也有差异，不能把早期条目直接拼进正式版本。

实际读：物理 p4–8，覆盖动机、系统设计、硬件符号、经验代价模型、学习型验证器、跨平台在线适配和实验设置；查看 p1、p5、p6 图像。正文 p9–17 的完整结果与参考文献未读，不独立背书摘要中的所有倍数。

关键问题不是搜索空间里缺少更复杂的预测器，而是预测器本身可能花掉大量调优时间。p4 表 1 的 Orin/ResNet-50 示例，把 2,000 trials 的开销拆为搜索 35 分钟、模型训练 5.4 分钟、硬件测量 44.4 分钟。由这些数直接算得搜索占总时间约 41%；即使让搜索完全免费，**若另外两项保持不变**，总调优时间也只能从 84.8 分钟降至 49.8 分钟，约 1.70 倍。这个推算适合第 5 章先教读者区分“调优得更快”和“调出的 kernel 跑得更快”。它不是对所有 Pruner 实验的上界，因为不同方法会改变后续搜索、测量和模型更新的过程。

Pruner 用硬件相关的容量、计算量、并行度和搬运特征做便宜的候选筛选，再用训练的 cost model 对少量候选排序，保留部分随机候选，最后测量并更新记录（p4–8）。p6–7 的经验公式含逐级惩罚，并把计算和访存时间相加，不能称作严格 Roofline 下界，也不能当作周期精确仿真。它适合与 Agent 自动优化组成教学对照：简单模型排除明显不合适的 tile，正确性检查和真实 profiling 决定保留哪个候选，Agent 再根据反馈修改。**这种 Agent 实验是本书的教学延伸；Pruner 本身不是大模型驱动的 kernel agent，Draft/Verify 也不是推测解码。**

实验设置还必须写清。p8 评估硬件是 A100、Titan V、Jetson Orin-AGX；其表 4 名为 Llama 的配置只有 12 层、hidden 768，不能称作真实 Llama-7B 的端到端推理结论；Mistral-7B 等另有配置。摘要的若干倍数是 schedule search time，不能塞进模型 tok/s 对比表。

公开实现的固定提交是 [0760c3f…，2025-03-31](https://github.com/qiaolian9/Pruner/tree/0760c3f39d84b31b4b10c4d7971ff402f2c350ae)。完整 README 已读：实现基于 TenSet fork，设备需注册 abstraction，提供在线、MoA 与离线 cost-model 路径。README 将搜索秒数和 estimated total latency 分列，支持上述区别；不能据此声称已合入当前 TVM 主线。首次请求不存在的 main 分支返回 422，原始响应保留，随后按 master 固定提交下载。

待补：完整结果曲线与 trial 口径；原型的 TensorCore/融合覆盖及当前工具链兼容性；Agent 实验若采用真实 Qwen3 矩阵，必须重新 profile，不能沿用缩小网络结论。

## 152 Relax：把图、kernel 和内存计划放在一起考虑

使用 [作者公开正式 PDF](https://yuchenjin.github.io/papers/asplos25-relax.pdf)，DOI `10.1145/3676641.3716249`；同时保存 [arXiv v2](https://arxiv.org/abs/2311.02103v2) 的完整摘要与历史。正式 PDF 的 19 作者与 DOI 核对完成；arXiv 元数据的 Steven S. Lyubomirsky、Jared G. Roesch 比正式署名多中间名，分别保留。

实际读：物理 p5、p9–11，覆盖符号形状、跨层调用、内存复用、workspace 提升、CUDA Graph offloading、partial lowering 与主评估设置；查看 p1、p9。p6–8 的全部融合算法、p12–13 完整消融与端侧结果未读。

p5 的例子很适合沿矩阵尺寸讲清楚：`X[n,128] @ W[128,256]` 得到 `[n,256]`，graph-level `call_tir` 把符号 n 和输出形状传给低层程序，外部库通过 destination-passing 接口接入。关键是知道哪些维度动态、哪些静态，保留形状关系以支持后续融合与分配，而不是介绍一串 IR 名词。

按示例 FP32、一次完整读取输入和权重、一次写出结果的简化模型，矩阵乘需要 `65,536n` FLOPs、最低 `131,072 + 1,536n` 字节数据流量。这里的“最低”只指该独立调用的逻辑读写量，不代表实测 HBM 流量；权重可能在缓存中，tile 又可能产生重复访问。独立 ReLU 会再读写一次 `[n,256]` 中间量，额外约 `2,048n` 字节；这正好用于从数据搬移引出融合的价值。

p9 图 10 展示四个相同元素数量的动态中间张量如何共用两个 storage；图 11 把 low-level workspace 抬到图层，以便一起规划生命周期。示意 workspace `8×1024×1024` 个 FP32 元素为 32 MiB，这种内存并不能在“只算输出 tensor”的预算里消失。符号形状有上界时可以提前规划足够容量，换来稳定的内存布局，但也要预算上界留出的空间。

p10 的 CUDA Graph pass 在内存规划后识别可捕获子图，首次捕获，随后 replay。应把它放在第 5 章融合/launch 开销之后，与第 8 章 batch 和 KV 管理相连。本文实现依赖静态内存计划和满足捕获条件的子图；不能写成“任何动态形状、动态控制流都能捕获成同一张图”，也不能把文中条件扩展成所有 CUDA Graph API 的永久限制。

p11 评估版本为 HF 4.41.2/PyTorch 2.3.1、vLLM 0.5.0.post1、llama.cpp `172c825`；模型 Llama3-8B、Gemma1.1-7B、Qwen2-7B，FP16；设备 RTX 4090、RX 7900 XTX、M2 Ultra，指标是生成 32 token 的 decode 单 token 时延。它回答编译机制与跨平台部署问题，不能当作 2026 年 serving 框架排名。

进一步静态核对了 [Apache TVM 固定提交 40c2f549…](https://github.com/apache/tvm/blob/40c2f54908e96875fa19e92db83f123854d97991/python/tvm/relax/transform/transform.py) 中四个 Python pass 接口：`StaticPlanBlockMemory`（含 `tir_var_upper_bound` 说明）、`FuseTIR`、`RewriteCUDAGraph`、`AllocateWorkspace`。这些接口仍存在，说明思路有具体工程落点；本次只读 Python 包装及 docstring，未读对应 C++ pass、默认 pipeline 或测试，不能由“接口存在”推定任何模型默认启用或已实现论文中全部优化。

待补：针对书中 Qwen3/最新 MoE 的 operator/shape 覆盖；CUDA Graph replay 时 batch、指针与 shape 的实际复用条件；真实端到端峰值显存和捕获成本。

## 182 vAttention：把内存容量、映射成本和读取带宽分开

选择 [arXiv 2405.04437v3，2025-01-29](https://arxiv.org/abs/2405.04437v3)，DOI `10.1145/3669940.3707256`。完整作者与 DOI 核对；PDF 将 Ramachandran Ramjee 写作 Ramchandran Ramjee，HTML 和正式 manifest 用前者。它是 KV 虚拟内存管理论文，与 2025 年另一个名为 *vAttention: Verified Sparse Attention* 的论文不同。

实际读：物理 p5–9、p13–14，覆盖工作负载观察、虚拟/物理内存分离、分配与请求接口、延迟隐藏、细粒度页、实验设置、分页粒度讨论和 tensor slicing；查看 p1、p6、p13。p10–12 完整吞吐曲线、消融和 FA3 可移植性结果未读，不独立验证摘要的 1.23 倍。

第 8 章可以先给出三个分别计算的量：已经保存的 KV 容量、每次 attention 实际读取的历史 KV 字节、每步为新 token 增补的映射量。p5 的 750 MB/s 指所测场景的**物理内存分配速率**，不是 GPU attention 的 KV 读取带宽。这是用户此前反复强调、最值得在教材中澄清的概念。

按 p6/p9 的 Yi-34B、TP=2、60 层、每卡 4 个 KV heads、head dim=128、FP16，单个 token 每卡持久 KV 容量为 `2×60×4×128×2 = 122,880 B = 120 KiB`，两卡合计 240 KiB。32K 上下文每请求每卡是 3.75 GiB。若 batch=16，仅 KV 就需每卡 60 GiB；再按约 34B 参数的 BF16 权重均分估算，每卡约 31.7 GiB，两者合计约 91.7 GiB，已超过 80 GiB 的示例预算，尚未计激活和 workspace。这个反例说明消除碎片并不消除模型容量约束；参数量使用 34B 圆整数做教学估算，正式实验应读取精确 checkpoint 配置。

vAttention 为请求预留连续虚拟地址区间，物理页按需映射，attention kernel 因而可以继续看到连续布局。p7 也明确有初始化的物理页池，公开实现可 `reserve_physical_pages`；“按需映射”不能写成“整段服务期完全不预留 HBM”。它依然需要管理 request id、batch 索引、容量不足时的抢占和生命周期。初始 prefill 可能一次增补很多页，decode 的增长较可预测，因而把下一步映射放到后台与前一步计算重叠（p8）。

这个设计可以用很小的数说明成本：Yi-34B 的 60 层有 120 个 K/V tensor；若每次 `Map + SetAccess` 约 40 μs，给一个请求各补一页要约 4.8 ms。若每层 K/V 独立分页，单请求内部碎片上界低于 `2×60×page_size`：2 MiB 页约 240 MiB，64 KiB 页约 7.5 MiB。它们分别是驱动调用时延和容量损失，不能混成“带宽下降”。这些推算沿用文中配置，不是新卡实测。

工程代价也明确。细页版本不是 stock CUDA 一键开关：p9 在 NVIDIA 开源驱动部分增加 API 来支持 64/128/256 KiB 页；2 MiB 路径不需要该改动。p13–14 另给出跨层 tensor slicing 来减少碎片，但会要求 kernel 支持 stride；当时 FlashInfer 的部分版本缺少这种支持。它说明内存布局可移植性、驱动依赖和碎片粒度需要一起选择。本文还把 CPU swap 作为 future work，不能将其描述为已经做完的多级 KV 池。

公开代码的实际差距必须单列：[固定提交 71a0e91…，2026-08-24](https://github.com/microsoft/vattention/tree/71a0e91aa46ff8fa985bcca3327efe0ab9929a39) 的完整 README 声明实现集成在 Sarathi-Serve fork，非完整 vLLM 特性集；测试依赖 PyTorch 2.3.0、CUDA 12.1、A100。README 的 FlashInfer 测试版本为 0.0.6，并且实验性 wrapper 用 FlashInfer 做 prefill、FlashAttention 做 decode；论文 p9 写的是公共 vLLM 0.2.7 框架、FlashInfer 0.4.0。二者不能合并成一套已经复现的环境，也不能声称当前 vLLM 主线已有全部功能。公开 README 明确自己是 research prototype，本次没有运行或安装驱动。

待补：当前 vLLM/FlashInfer 的 upstream 状态；prefix sharing、CUDA Graph、chunked prefill 和 PD 传输与 VMM 的交互；与新版页式 attention kernel 在同一模型、SLO 和软件版本下的对照。建议实验先用原版驱动的 2 MiB 路径做映射成本/碎片推算，细页驱动路径留作有合适专用环境的后续研究。
