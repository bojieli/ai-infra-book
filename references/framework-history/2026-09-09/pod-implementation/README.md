# POD：从研究内核到库接口

2026-09-09。固定 `microsoft/vattention` 为 `71a0e91aa46ff8fa985bcca3327efe0ab9929a39`（2026-08-24），`flashinfer-ai/flashinfer` 为 `b6aed59786374d437b64b054488d0740ad5f5468`（2026-09-09）。八份原始响应及散列见 [sources.json](sources.json)，实际读取范围见 [reading.json](reading.json)。保存源码不表示全部读过；本轮没有运行下载代码、编译器、模型或 GPU 测试。

论文方法及算例已在[前一阶段](../../../proceedings/ASPLOS/2025/serving-113-117/README.md)记录。这里补充库接口的边界，不再新增小节或实验。

研究仓库的 POD README 明确列出 FlashAttention 2.6.1 与 FlashInfer 两条实现路线，并称已接入 Sarathi-Serve。其安装说明写最低 Ampere、在 A100 上测试；这不是我们对其他硬件的验证。README 的最高／平均加速数为 61%／33%，论文摘要为 59%／28%；保持各自来源，不混成同一个实验，也不把该差异推断为版本必然提速。

在当前固定 FlashInfer `PODWithPagedKVCacheWrapper` 的所读范围中：

- **CUDA Graph 支持有边界。** 构造函数要求提供分页索引缓冲；图模式下 decode batch 固定，`plan` 会检查 batch 和索引容量。`plan` 的说明明确不能在 CUDA Graph 或 `torch.compile` 内使用。规划和执行不能混算成一次可自由捕获的调用。
- **容量预算不止 KV。** 构造函数分配 8 MiB GPU 整数工作区和 8 MiB CPU 锁页工作区，浮点工作区由调用者提供。所读 `run` 路径还申请缓存式的 32 MiB prefill 临时区，以及输出和可选 LSE；32 MiB 缓存缓冲不能直接按每次调用重新分配计算，也不能把这些数相加当作完整峰值显存。
- **函数参数不等于能力保证。** 所读 `plan` 将 logits soft cap 置零，`run` 也将两阶段 soft cap 参数禁用。不能仅因签名有同名参数就声称支持该模型特性。decode 的位置编码、窗口等使用计划缓存值，需要以具体调用路径核对。
- **公开 Python 接口不证明上层服务采用。** 当前文件存在 POD 模块调用，研究 README 提到 Sarathi-Serve；本轮没有追查 vLLM／SGLang 的版本化调用路径，也没有证明全部底层 specialization、精度和设备组合都可用。

可沿已有 CUDA Graph 实验加一个核对问题：将注意力执行放进图以后，哪些规划、元数据更新与缓存等待仍在图外？保存 wrapper 生命周期、固定 batch、页索引容量和实际捕获范围，再测完整迭代，而不是仅报告 kernel 时间。现有第 5 章 POD 段落已足够表达资源共驻的主线，此处只提供扩写证据。

后续仍需读 FlashInfer 的底层 POD dispatch／launch、对照调用方与不同图模式；归档的研究版 interface 和 launch 文件尚未阅读，不作为已验证实现范围。没有新增论文摘要或正文阅读计数。
