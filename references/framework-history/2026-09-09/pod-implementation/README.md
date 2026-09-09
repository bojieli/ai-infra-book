# POD：从研究内核到库接口

2026-09-09。固定 `microsoft/vattention` 为 `71a0e91aa46ff8fa985bcca3327efe0ab9929a39`（2026-08-24），`flashinfer-ai/flashinfer` 为 `b6aed59786374d437b64b054488d0740ad5f5468`（2026-09-09）。十七份原始响应（十六份成功、一份旧路径 404）及散列见 [sources.json](sources.json)，实际读取范围见 [reading.json](reading.json)。保存源码不表示全部读过；本轮没有运行下载代码、编译器、模型或 GPU 测试。

论文方法及算例已在[前一阶段](../../../proceedings/ASPLOS/2025/serving-113-117/README.md)记录。这里补充库接口的边界，不再新增小节或实验。

研究仓库的 POD README 明确列出 FlashAttention 2.6.1 与 FlashInfer 两条实现路线，并称已接入 Sarathi-Serve。其安装说明写最低 Ampere、在 A100 上测试；这不是我们对其他硬件的验证。README 的最高／平均加速数为 61%／33%，论文摘要为 59%／28%；保持各自来源，不混成同一个实验，也不把该差异推断为版本必然提速。

在当前固定 FlashInfer `PODWithPagedKVCacheWrapper` 的所读范围中：

- **CUDA Graph 支持有边界。** 构造函数要求提供分页索引缓冲；图模式下 decode batch 固定，`plan` 会检查 batch 和索引容量。`plan` 的说明明确不能在 CUDA Graph 或 `torch.compile` 内使用。规划和执行不能混算成一次可自由捕获的调用。
- **容量预算不止 KV。** 构造函数分配 8 MiB GPU 整数工作区和 8 MiB CPU 锁页工作区，浮点工作区由调用者提供。所读 `run` 路径还申请缓存式的 32 MiB prefill 临时区，以及输出和可选 LSE；32 MiB 缓存缓冲不能直接按每次调用重新分配计算，也不能把这些数相加当作完整峰值显存。
- **函数参数不等于能力保证。** 所读 `plan` 将 logits soft cap 置零，`run` 也将两阶段 soft cap 参数禁用。不能仅因签名有同名参数就声称支持该模型特性。decode 的位置编码、窗口等使用计划缓存值，需要以具体调用路径核对。
- **公开 Python 接口不证明上层服务采用。** 当前文件存在 POD 模块调用，研究 README 提到 Sarathi-Serve；本轮没有追查 vLLM／SGLang 的版本化调用路径，也没有证明全部底层 specialization、精度和设备组合都可用。

可沿已有 CUDA Graph 实验加一个核对问题：将注意力执行放进图以后，哪些规划、元数据更新与缓存等待仍在图外？保存 wrapper 生命周期、固定 batch、页索引容量和实际捕获范围，再测完整迭代，而不是仅报告 kernel 时间。现有第 5 章 POD 段落已足够表达资源共驻的主线，此处只提供扩写证据。

研究实现的后续静态核对补充了三个边界：

- `fused_attn_interface.py` 的 `true_fused_attn_with_kvcache` 在一侧输入为 `None` 时回退到对应的独立注意力；两侧都有输入时才调用 fused 扩展。接口还可能做 contiguous 转换或把标量长度展开成设备张量，完整调用成本需要包括这些准备步骤。
- `fused_fwd_launch_template.h` 所读路径在启动前分配并清零 `(numSMs + 2)` 个整数的计数区。持久化分支按 `numSMs * (256 / num_threads)` 设置 grid，另一分支按逻辑块数设置 grid；共享内存取两阶段需求的较大值。启用 split KV 后，prefill 和 decode 还分别可能启动 combine kernel。因此，融合注意力不代表整个 API 只启动一个 kernel。当前只核对静态路径，不据此宣称分配的实测开销或内存泄漏。
- `fused_fwd_kernel.h` 的持久化分派片段读取 SM 标识、使用每 SM 的计数器分配阶段任务，某一阶段耗尽后尝试另一阶段。代码对 SM 数值的使用明确附有 A100 测试范围的注释；不能把该实现直接推广为所有 GPU 的保证。

这给已有实验增加的是测量边界：分别记录输入准备、计数区初始化、主 kernel、split KV 合并，以及完整迭代时间，再解释融合减少了哪部分等待。没有运行实验，不能将静态路径转写为实测加速结论。

后续补读的 FlashInfer 底层 POD dispatch／launch 见下文；上层服务调用方与不同图模式仍待核对。研究版源码与 FlashInfer 是不同实现，不能用前者的分配路径解释后者的运行开销。没有新增论文摘要或正文阅读计数。


FlashInfer 固定提交的底层核对进一步区分了准备与稳态：

- `get_pod_module` 对参数组合缓存构建结果；`gen_customize_pod_module` 按 prefill／decode 各四种 mask 枚举生成 16 个实例源文件，另加 `pod.cu`、binding 两个源文件。18 个源文件不等于 18 次 kernel 启动，也不代表测得了编译时间。首次构建、已有 JIT 缓存及 CUDA Graph 准备需要分别计时。
- 所读 `pod.cu` 将 decode 的 CTA tile 固定为 16；`pod.cuh` 则结合 prefill 长度、GQA 组大小、head dimension 和设备能力选择 prefill tile，并根据共享内存等条件决定 split KV。这里存在启发式与 TODO 注释，不能把规则当作最优分块的保证。两阶段 dtype、head 数也受共同约束，不是任意两个注意力任务都能拼接。
- FlashInfer 的计数区是模板函数中的 `static` 指针：为空时分配，每次路径都会清零。研究版所读 launch 则在局部指针上直接分配；不能把二者写成相同的每次分配行为。当前未核验跨设备、跨流并发调用的生命周期与安全性，不据这一片段宣称存在运行故障或全面兼容。
- 主 kernel 之后，prefill 按条件调用 `MergeStates`／`AttentionSum`，decode 按条件调用变长合并；该分支也区分普通 launch 与 PDL launch。因此图内主 attention 与整个调用仍有不同的计时边界。这里确认了合并调用存在，未继续阅读所有合并内核和 PDL 的实际执行效果。

此次路径是 Python wrapper → JIT 生成函数 → CUDA 入口 → POD dispatch，尚未核对最终构建工具、链接导出和完整 device kernel。也没有找到并验证上层 vLLM／SGLang 服务调用，因此不能把库实现存在写成上层框架已采用。网页搜索无结果不作为未采用的证据。

原 `flashinfer/jit/attention.py` 路径在固定提交返回 404，响应原样保留；随后以完整 Git tree 定位 `flashinfer/jit/attention/modules.py`。目录改动不推断为行为改动。所有新增材料只深化既有第 5 章 POD／图执行说明，不新增章节或实验。

后续已补查[固定 vLLM／SGLang 上层 backend 的部分路径](../pod-callers/README.md)，区分阶段 wrapper、上下文分段和 POD 共驻。该核对关闭了所读分支的调用疑问，不扩展为全框架采用／未采用的判断，也不把这里固定的 FlashInfer 提交视为上层实际安装版本。
