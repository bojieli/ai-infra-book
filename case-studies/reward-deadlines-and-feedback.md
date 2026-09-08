# RL 验证的剩余时间与资源配置

用于 11.3.3 和实验 11-5，接第 3 章的长尾负载、第 5 章优化 Agent 的性能反馈与第 10 章训练批次。2026-09-09 补读 DistRS 的调度算法和评估，并对照固定版本的 verl；此前对 DistRS 负载和设计的阅读见[原案例](platform-routing.md)。以下小算例都是教学输入，没有执行框架或硬件实验。

## 已经运行十秒，还需要多久

先给十条历史验证记录：九条各用 1 秒，一条用 100 秒，平均为 10.9 秒。现在一条任务运行了 10 秒还未结束。用平均值减去已运行时间，会得到 0.9 秒；但在这个分布中，能够运行到第 10 秒的只有长任务，它还需要 90 秒。

对正在运行的任务，需要估计 `E[S − e | S > e]`，其中 `e` 是已经执行的时间。DistRS Algorithm 2 从执行时间大于 `e` 的历史样本中抽样，再扣除 `e`；它没有把所有任务都替换成一个平均数。这里的目的不是要求读者建立精细预测器，而是先发现平均数会在哪个条件下失效。真实历史可能稀疏、分布也可能变化，条件估计仍需用运行反馈修正。[论文，物理页 10](../references/outline-checks/2026-09-07/platform-routing/distrs-nsdi26.pdf#page=10)

再假定整批最早完成点是第 120 秒，例如另一条样本在第 100 秒到达、执行 20 秒。对于执行上限为 100 秒的待运行任务，若要保证不推迟这个批次，最迟应在第 20 秒启动。第 30 秒才启动，最坏会拖到第 130 秒。若环境还需冷启动，应继续从可等待时间中扣除准备时间。平均执行时间 10.9 秒无法提供这个保证。

这对应 DistRS 的超时感知分配：检查当前时刻加后续阶段的超时上限，是否越过批次允许完成点。它用历史轨迹搜索配置，并在多作业之间按预计批次完成点安排优先级；论文明确没有全局最优保证。本书先做上述下界与最迟启动推算，只有竞争会改变选择时才回放记录。[论文，物理页 8–10](../references/outline-checks/2026-09-07/platform-routing/distrs-nsdi26.pdf#page=8)

## 验证省下的 GPU 时间，是否抵得上训练等待

假设验证服务少用一些资源，节省 60 GPU·秒，却使一个仍占有 64 张 GPU 的训练组额外等待 2 秒。若先按相同 GPU 时间价值计算，额外占用为 `64 × 2 = 128 GPU·秒`，净增 68 GPU·秒。不同卡型改用各自单位成本；如果等待期间训练资源可以有效供其他作业使用，还要重新核算实际代价。不能把这条算式当作所有分离式训练的固定损失。

DistRS 的真实实验中，每个编译 worker 配 4 个 CPU 核和 16 GB 内存，每个执行 worker 使用一张 NVIDIA GPU；已读设置没有给出执行卡型号或训练模型规模。六个并发任务回放同一真实 CUDA 代码生成轨迹并错开起点；分离式、一轮滞后的到达轨迹通过调整批间空隙构造。相对为各任务独立配置、按历史追求零排队的基线，共置情形的 GPU 总时间降为基线的约 1/3.79，平均额外等待 0.62 秒，完整训练迭代超过 600 秒。这里的 3.79 倍是资源时间之比，不是训练吞吐提升。图 13(b) 的延迟按大小排序，也不能读成训练过程中逐轮恶化。[论文，物理页 11–12](../references/outline-checks/2026-09-07/platform-routing/distrs-nsdi26.pdf#page=11)

## 从论文调度到框架入口

先画三条生成结束于第 0、10、20 秒的响应，每条验证耗时 10 秒、只有一个验证 worker。逐条提交可以在第 30 秒完成；等整批生成结束再提交，要到第 50 秒。两种安排都执行了 30 worker·秒的验证，差别在依赖和重叠。这里不指定真实模型速度，也没有计入传输和启动开销。

在 verl v0.4.1 的固定训练入口中，调用者先取得整批生成结果，再启动可选的异步奖励计算；评分可以与后续 log-prob／value 等工作重叠，在 advantage 计算前汇合。2026-09-07 固定提交的实验性 Agent Loop 则在单条轨迹结束后进入后处理，其中可以调用 reward worker，再由批量入口等待所有任务。这是两个具体入口的对照，不代表旧版所有路径都没有流式能力，也不是该功能首次发布的考证。[旧版源码](https://github.com/verl-project/verl/blob/8d9e350ea58c7ad4b50dd14d9dcb50577242c55f/verl/trainer/ppo/ray_trainer.py#L979)、[当前 Agent Loop](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/experimental/agent_loop/agent_loop.py#L631)

当前 reward worker 的交付还受配置限制：所读 manager 在没有 reward model，或 reward model 使用独立资源池时才返回相关 worker handles。`remote` reward manager 把同步评分函数放进 Ray CPU actor，按轮转分派；这些机制不能直接等同于 DistRS 的 CPU 编译／GPU 执行分阶段服务，也没有从已读路径中得到跨训练作业的 EBF 调度。vLLM／SGLang 负责生成的能力，与训练控制器如何组织验证，属于相连但不同的实现工作。[Reward Loop](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/experimental/reward_loop/reward_loop.py#L273)、[Remote Reward](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/experimental/reward_loop/reward_manager/remote.py)

还有三个实际计时边界。所读 rate-limited manager 先等 token 配额和并发信号量，再进入评分的 `wait_for`，因此执行超时没有包含前面的排队。它的类级限额共享范围是一个进程，不能把四个各允许八条请求的独立进程当作全服务只允许八条。同步评分通过线程 executor 执行，等待方超时也不能证明正在执行的线程或外部 GPU 工作已经终止；Python 的 Future 文档明确区分尚未开始和已经执行的调用。[限流源码](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/experimental/reward_loop/reward_manager/limited.py#L255)、[Python Future.cancel](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Future.cancel)

所以实验记录至少保留入队、开始评分、返回结果或超时、实际释放资源四个时刻，并保留超时与基础设施错误标记。当前所读异常路径返回零分并附带标记；训练端如何使用这些反馈，需要按任务的验证标准决定，不能静默地把资源拥塞变成模型能力标签。与第 10 章[验证超时与样本选择](rollout-tail-and-sampling.md)使用同一判断标准。

## 另一条实现边界：RLBoost 与 PolyRL

RLBoost 的作者项目 PolyRL 在固定提交的使用说明中给出 Qwen3-1.7B、GRPO、verl 训练和 SGLang rollout 的示例，启动参数包含定制的 `transfer-agent-handshake-port`，另有 Mooncake 配置与 Rust rollout manager。这个示例不能替代论文的 Qwen3 8B–32B 实验条件，更不能据此认定标准 SGLang 安装就包含完整的可抢占调度。该提交的 roadmap 仍将权重传输中的故障处理、权重量化压缩和 off-policy 支持列为未勾选事项；roadmap 表示作者记录的计划，不构成逐项代码审计。本次只读三份项目说明，后续代码核对范围继续单独登记。[固定使用说明](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/USAGE.md)、[roadmap](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/ROADMAP.md)

## 放回现有实验

实验 11-5 沿用两批验证任务：先比较逐条提交与整批提交，再加入长尾、执行上限与资源竞争。基础部分只手算完成时间；选做回放条件剩余时间与批次优先级，并记录 CPU 核秒、GPU 秒和训练组等待。图 11-5 的验证子图标出批次目标、最迟启动点以及返回超时与实际释放的间隔，放在 11.3.3 的讨论旁。版本、读取行号与论文范围保留在[来源记录](../references/framework-history/2026-09-09/rollout-resources/README.md)，不搬入书的主文。
