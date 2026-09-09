# 序列形状、执行位置与实现条件

2026-09-09。围绕现有第 10 章的长度分布、第 4／12 章的端侧执行选读两篇论文。27 页声明正文范围和 14 张正文图页已读；公开源码只读 [reading.json](reading.json) 声明的十二个范围。没有运行下载代码、模型、求解器或硬件实验。原始响应与失败状态保存在 [sources.json](sources.json)。

## FlexSP：相同 token 数的工作并不相同

[FlexSP 作者稿](../../../proceedings/ASPLOS/2025/public/paper-075.pdf)是 arXiv 2412.01523 v3，2025-02-11，17 页；正式 DOI 为 10.1145/3676641.3715998，不能把作者稿页数当作出版页数。已读物理页 2–13、17；第 1 页摘要此前已读，参考文献只作定位。具体图页和正文证据见[阅读记录](../../../proceedings/ASPLOS/2025/flexsp-reading.json)。

方法的起点是训练文档长短不同：线性层主要随总 token 数增长，稠密注意力还取决于各文档长度的平方。为长序列分更多卡会减少单卡工作与激活，却增加通信；为所有序列采用最大并行度也可能浪费短序列的通信与分组机会。先按容量、计算和具体接口排除不合适的组，再结合实际 profile 分配文档，才有继续求解的意义。

论文使用 Ulysses 式注意力序列／头维重排。这里的 SP 与 Megatron 将部分逐 token 算子激活分片的 SP 含义不同，附录 E 还将 CP 集成列为后续工作。packing 必须保留独立文档的 mask、位置和有效标签；把文档直接连成一个连续因果序列，会改变工作和训练目标。

联合优化是在论文代价模型内定义的。实现采用长度桶、受限的组候选和少量微批次数试探；通信组缓存减少准备，但不等于重排与控制开销为零。CPU 规划通常需数秒，异步准备依赖对后续 batch 的可知性和足够的 CPU 处理能力。64→1024 GPU 的求解器扩展实验采用估计训练时间，不能写成 1024 卡训练实测。

实测平台是八台八卡 A100 40GB，节点间 400 Gb/s IB。GPT 7B／13B／30B 使用很长的可学习位置嵌入，附录中最高长度时的位置参数就占约 1–2B；其参数量和拟合系数不能直接移到采用 RoPE、GQA 的 Qwen3。论文的 batch 512 指序列数，长度截断和丢弃规则也影响结果。

[官方 FlexSP 分支](https://github.com/PKU-DAIR/Hetu-Galvatron/tree/b4666892601f1adab345dbf07b6af2c300eb7c90)固定在 2025-03-28 的 `b466689`。它与当前 Galvatron main 分开；main 引用论文不证明每种组合已集成。所读训练入口使用 GPT2 模型构造、具体 GPT 拟合系数、硬编码的通信速率、28 GB 优化预算与十秒求解期限。换模型和机器需要重新校准。代码还对部分 GPT-7B 配置启用 MLP checkpoint，不能将附录的无 checkpoint 基线当作这份代码所有参数组合的事实。

更直接的实现差别是 [transformer.py](flexsp-transformer.py)：所读路径先把 GQA 的 K/V 扩展到查询头数，再进行 Ulysses 通信。Qwen3-8B 的 K/V 表示因此可从每 token 4 KiB 变成 16 KiB；加上 Q，QKV 总载荷从 12 KiB 变成 24 KiB，并非全部通信都放大四倍。头数约束和通信预算必须沿实际路径核对；不能因 KV 头数为 8 就断言所有实现的 SP 度数只能到 8。

所读交叉熵返回逐 token 损失，流水入口还涉及微批缩放；这些文件不足以闭合最终有效 token、loss mask 和分布式梯度归一化。保留这一缺口，不凭局部源码声称梯度错误。教学变体明确使用有效标签加权，再检查所选实际训练栈的最终归约。

## llm.npu 到 MLLM：软件会改变芯片的使用方式

[llm.npu 作者公开稿](../../../proceedings/ASPLOS/2025/public/paper-073.pdf)为 18 页正式格式版本，DOI 10.1145/3669940.3707239；已读物理页 2–15，包括工件附录，图像及限制见[阅读记录](../../../proceedings/ASPLOS/2025/llm-npu-reading.json)。它针对的是 prefill：以固定 prompt 块复用静态图及含权重子图，把适合 INT8 的矩阵工作交给 NPU，CPU 承担浮点注意力、部分归一化和离群值补偿，再按依赖调度块。默认块长 256 来自其条件下的选择，不是通用最佳值。

统一物理内存仍可能存在独立运行时缓冲、数据副本和同步。压缩离群值处理还涉及校准与质量；原稿均值不能代替各模型、各任务的质量要求。正文 CPU＋NPU 原型和 CPU decode 是实际实现，GPU＋NPU 部分是模拟。表 5 的短输出任务与较长输出对话说明 prefill 收益怎样被完整生成时间稀释；不采用表中部分无法严密复算的加速比。UI 自动化输入是 XML／HTML 类文本，不能拿它直接推断截图编码或图片上行性能。

原稿还保留两处不适合原样搬入教材的表达：第 7 页的 clip 与 floor 分解不构成对任意整数成立的恒等式；第 8 页资源约束的等号没有表示空闲。若教学需要残差分解，应写成精确定义的 `y = clip(y) + (y − clip(y))`；若表达单位资源容量，允许占用和小于等于 1。这里校正教学表达，不据此推断未读工件的运行错误。

工件附录覆盖 prefill 性能与准确率，采用 A100 服务器和 Redmi K70 Pro，示例为 Qwen1.5-1.8B；不是全部图表的完整复现实验。本轮 Zenodo API 与记录页均返回 504，原响应保留，未取得或运行该工件。

[MLLM v1 固定快照](https://github.com/UbiquitousLearning/mllm/tree/013e4cecf183358ce5fe5e6a19bee332c50d880c)的提交日期为 2026-01-14，不冒称它就是论文工件。所读 README 支持若干 Qwen 模型的 CPU＋NPU prefill、CPU decode，并要求 NPU INT8 与 CPU Q4K 两份模型；QNN 说明还加入旋转量化和视觉编码器支持。这些变化说明校准、模型转换和存储副本也进入部署预算。

[当前主分支固定快照](https://github.com/UbiquitousLearning/mllm/tree/bc8f5cdb557f6ff1b2baf9987f5ad0068ecd0463)为 2026-09-08。README 记录 2026-02-03 的 full graph NPU AOT 支持；[固定 AOT 指南](mllm-aot-fixed-guide.rst)与另存的[在线指南正文](mllm-aot-guide.txt)采用主机量化、离线编译 context binary、设备执行的过程。指南中的 Hybrid 指 prefill／decode 两类执行方式，不能沿用旧版本把它解释成 CPU／NPU 分工。

选中的 [Qwen3-1.7B 配置](mllm-qwen3-config.json)有 28 层、16 个 Q 头、8 个 KV 头、头维 128；[AOT 配置](mllm-aot-config.json)指定 SM8650／V75、W4A16 LPBQ 和 INT8 KV。模型的位置上限 40960 与配置的缓存长度 2048 是两件事。单序列 2048 token 的逻辑 INT8 KV 为 112 MiB，还未加尺度、布局、重复缓冲与临时状态。配置里 VTCM 的设置是软件目标条件，不能当成对所有芯片的容量测量。SDK、安全会话及编译目标均有条件；README 宣布整图支持也不能替代实际量化质量和完整请求测试。

## 对现有案例的取舍

FlexSP 接[训练计算案例](../../../../case-studies/training-compute.md)与 10.2.3／实验 10-3／图 10-3 的变体；llm.npu 与 AOT 变迁接[单元利用率案例](../../../../case-studies/component-utilization-and-overlap.md)、4.6.5 和 12.2.3。只保留能改变判断的数值和条件，不新增核心章节或实验。

[独立核算](arithmetic.json)由本地自写的 [check_arithmetic.py](check_arithmetic.py)生成：相同 token 的配对数、GQA 实际通信表示、有效标签加权、固定块填充、逻辑 KV 和阶段收益。训练 Qwen3-8B 与端侧 Qwen3-1.7B 的配置分开，不能互换模型维度。量化质量、实际 KV 布局、真实吞吐和最终梯度归约仍需后续对应实验核对。
