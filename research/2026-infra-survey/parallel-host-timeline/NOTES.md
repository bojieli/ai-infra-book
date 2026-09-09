# 主机调度：从减少工作到隐藏等待

2026-09-09。结论：现有第 5 章和第 8 章只需共用一条请求时间线，便能把这段演进讲通，不必增加调度名词或独立小节。2024 年 vLLM 多步调度减少调度次数，异步输出把部分结果处理移出关键路径；2025 年 V1 进一步减少输入与状态管理的重复工作；当前异步调度还需要在结果未回主机时维护占位与在途状态。SGLang 2024 年已有提前一批的 overlap，2026 年 Spec V2 则要把这种执行方式接到可变接受长度、草稿状态和语法约束上。

本次只写本目录。复用 21 份归档文件，新增 17 次官方 HTTP 读取，全部返回 200；没有运行框架、下载模型或新读会议论文。实际选读 **4 份文章文本、12 份固定源码**，另查看两张已归档 vLLM 示意图；全文文件已下载不代表全文审读。每个选读范围及 SHA-256 在 [reading.json](reading.json)，五个提交的真实 root tree 与 13 份源码（包括一份仅备查的 base scheduler）Git blob SHA-1 在 [git-blob-proof.json](git-blob-proof.json)。

## 2024：调度少做几次，和结果晚处理一轮

vLLM [2024-09-05 发布文](https://vllm-project.github.io/2024/09/05/perf-update.html)的 multi-step 与 asynchronous output processing 是两项机制。多步调度一次确定连续若干步的请求集合，摊销调度／准备开销；模型依然逐步使用上一步 token。异步输出则将上一轮的主机输出处理与下一轮设备计算重叠。文章也明确写出多步调度对新请求准入、输出突发性的影响，以及异步结束判断可能额外执行一步。这里的性能倍数属于文章当时的模型、设备和批次条件，不移植到 Qwen3。

对应 v0.6.0 固定提交 `32e7db25365415841ebc7c4215851743fbb1bad1`（committer 时间 2024-09-04）中，`llm_engine.py` 1497–1519 行在还有 remaining steps 时跳过 scheduler，1568–1599 行只在窗口结束后清缓存／处理结果。`multi_step_model_runner.py` 349 行仍要求 `num_steps == 1`；374–391、486–518 行把上一步 GPU 采样结果接回本步输入。189–207 行的 event 防止提前改写仍在使用的元数据，88–125、439–463 行把非阻塞尝试与最终阻塞收尾分开。**复用调度决定没有消除自回归依赖，也没有消除所有逐步主机工作。**

SGLang [2024-12-04 v0.4 文章](https://www.lmsys.org/blog/2024-12-04-sglang-v0-4/)提供独立对照：提前准备下一批，并通过 future token 与 CUDA event 接续。文章的无空隙 profile 明确限定 Triton attention backend，同时提到当时 FlashInfer 仍有小间隙。对应文章所链提交 `85e1a6f3aa5a2288ca85fe3fe922c733b6533fa7`（2024-12-02），scheduler 399–434 行先提交本批，再处理上一批；旧 worker 40–46、127–140、181–210 行先返回负数占位，然后在设备上解析成真实 token。162–178 行仍等结果复制完成，192–193 行也有显式同步。“零开销”不能改写成零 CPU 工作或没有同步指令。该旧 scheduler 176–187 行还明确关闭 embedding／multimodal overlap；不能反推今天的支持范围。

## 2025→2026：V1 的简化和今天的异步状态管理

vLLM [2025-01-27 V1 发布文](https://vllm.ai/blog/2025-01-27-v1-alpha-release)将 EngineCore 隔离、worker 状态增量更新、Persistent Batch 的输入复用分开介绍。前两者有进程与队列边界，后者减少每步重新创建输入的工作。其 alpha 限制当时还包含 speculative decoding／PP，硬件描述为 Ampere 或更新 NVIDIA GPU；这是历史快照，不能拿当前支持反填发布日期。

代表实现 v0.8.0 `966f933ee1cd7c9a41db60de5c7ff98657005251`（2025-03-18）比该发布文晚。`vllm/v1/engine/core.py` 171–196 行普通路径依然是 schedule → execute → update；102–110、198–239 行已有服务 PP 的 batch queue，队列空位时先提交、否则等待先前 future。**不能由 V1 名称或这条 PP 队列推断当时已经具备当前 AsyncScheduler 的全部行为。** 本次没有追首次引入 async scheduling 的 PR，不给出未经核验的精确发布日期。

当前固定 vLLM `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`（2026-09-07）中，`async_scheduler.py` 19–49 行给尚未返回的输出和推测 token 记占位，真实草稿 token 在 worker 更新；51–70 行收到结果后扣占位、区分抢占后的旧结果并按已经确认的进度缓存 KV。`core.py` 649–761 行的队列优先提交，但 grammar 尚需上一轮 token 时只先发起前向，延后采样：先回收旧结果、更新状态，再生成 bitmask。异步方式可以隐藏等待，不能让 grammar 提前知道尚未确认的 token。

同提交 `test_async_scheduler.py` 34–66 行检查已知 max_tokens 下没有多调度 token，555–620 行检查存在推测拒绝、KV 压力和在途结果时的抢占恢复与输出顺序。这里只审了测试源码，未运行；它支持状态约束的解释，不提供吞吐结论。2024 文章的“可能多跑一步”也不应升级为所有当前停止条件都必然多跑一步。

## Spec V2：同一条时间线多了哪些依赖

SGLang [2026-06-15 DFlash／Spec V2 文章](https://www.lmsys.org/blog/2026-06-15-next-generation-speculative-decoding-dflash-v2/)区分了算法初始实现、接入引擎与减少主机同步。其两个重叠机会是上一批 `pop_and_process` 与本批 GPU 工作、本批 KV 准备与上一批 GPU 工作。DFlash 的 target hidden state → draft KV projection／即时物化属于该算法的额外状态路径，不能把它当所有 Spec V2 或 EAGLE 的统一实现。本文数值是当时的特定模型、后端和机器结果；本次没有重测，也不把研发阶段的算法加速与系统阶段加速相乘。

当前固定 SGLang `c99d906effa8bd05573995127f0d4a0984c5a96a`（2026-09-07）晚于该文章，不冒充六月上线代码。选读 EAGLE V2 路径作为一个可检查变体：

- **真实 token 之外，还要知道本轮实际推进了多少位置。** `eagle_worker_common.py` 587–599 行产生 `accept_lens` 并计算 `new_seq_lens = seq_lens + accept_lens`；下一批的序列位置不能简单每轮加一。这里沿源码的序列推进增量口径，不把它直接叫草稿接受率或最终展示 token 数。
- **先确认验证结果，才能发布新长度；草稿更新还有自己的后续工作。** `eagle_worker_v2.py` 1264–1291 行按 draft → verify → publish new lengths → draft extend 执行。scheduler 4226–4235 行把 publish／grammar barrier 交给 worker。publish 放在 verify 后、draft extend 前，让部分主机准备有机会与后续草稿计算重叠；它没有消除下一轮草稿对前轮状态的依赖。
- **能否不把长度抄回 CPU，由实际消费者决定。** `overlap_utils.py` 26–51 行按后端声明及 TBO／ngram 条件决定 CPU 镜像需求；513–565 行只有消费者不需要时才省去 D2H。需要镜像的 CUDA 路径仍等待私有复制流，非 CUDA／bootstrap 有 `.cpu()` 路径；HIP 另有事件等待分支。不能把 GPU-only 路径概括成所有配置都无主机同步。
- **约束状态和缓冲生命期仍形成边界。** scheduler 2040–2069 行对需要主机 grammar 同步的算法先处理上一批；支持重叠的变体将 barrier 放到 verify 内。common 540–598 行显示 target forward 可先提交，但 mask／采样需要 grammar 更新。scheduler 4112–4139、4246–4250 行还保留跨流张量引用，防止下一轮改写／释放仍在使用的数据。结果复制 CUDA 与 HIP 路径也不同，见 4268–4288 行。

这些固定实现解释了为什么论文或文章中的并行机会不直接等于服务端收益：验证接受长度会改变下一轮 KV 和形状，约束采样要读已经确认的状态，跨流执行要保持缓冲有效。**本次没有新增 DFlash／NanoFlow 论文正文阅读；论文层的结论沿已有专题，本补读只补引擎调用依赖。**

## 放回现有教学安排

仅建议把 [短时间线](TEACHING-TIMELINE.md)接到既有 5.4.3 → 8.1.3／8.1.5 与实验 5-8／8-2；8.3 引用最后一个推测变体即可。不加新小节、不扩大框架矩阵。

先让读者区分“CPU 总工作减少”和“CPU 工作退出关键路径”，再沿 Qwen3-8B 的普通 decode 检查输入就绪、GPU 执行与结果提交，最后只加一个既有推测／结构化变体。实验应记录真实版本、后端、CPU 区段、GPU 区段、D2H 和 event；本目录的时间是明确假设的教学单位，不能算设备实测。当前已足以结束这条链的资料补读，剩余完整 trace 属于实验验证。

`python research/2026-infra-survey/parallel-host-timeline/verify.py` 仅校验本地哈希、选读范围、固定 Git blob 与教学算术，不导入任何框架，也不联网。
