# 权重卸载与 CPU／GPU 执行的版本证据

获取与核读日期 2026-09-08。[sources.json](sources.json)保存 17 份成功响应的 URL、SHA-256、时间、提交和读取范围。只进行文本与源码静态阅读，没有安装框架、运行下载脚本或测量 GPU。声明读取范围外的文件内容不计为已读实现。

## vLLM：按需访问、选择性卸载与预取

- [v0.6.0 helper](vllm-2024-utils.py) 165–232 行：参数转到主存，前向通过 device_state／functional_call 按需搬回 GPU。
- [v0.9.2 helper](vllm-2025-utils.py) 540–623 行：V1 要求 UVA 支持并保留主存参数的 GPU view；非 V1 保留旧路径。以上两份只读卸载相关范围，没有全量模型审查。
- 固定当前提交沿用先前已核身份 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`：[配置](vllm-current-config.py)、[UVA](vllm-current-uva.py) 全文件；[prefetch](vllm-current-prefetch.py) 1–598 行。读取层分组、参数选择、静态池 key、槽位复用、量化后参数同步、预取事件、计算图汇合及实际 H2D；后续 CPU 参数存储实现和完整 runner 调用链未审查。
- [预取 PR #29941](vllm-prefetch-pr.json) 的身份、Purpose／Test Plan／Test Result 已读，未读完整 diff；2026-02-26 合入，明确借鉴 SGLang。其两个吞吐日志分别是两卡总计 18.04、四卡总计 33.82 request/s；每请求只生成一个 token，不能作为长 decode 成绩。重新按卡数归一化，不沿用小标题中的 per GPU 数值。
- [选择性卸载 PR #34535](vllm-selective-pr.json) 的身份、Purpose／Test Plan／Test Result 已读，2026-02-14 合入；示例含 dummy 权重与五项随机请求，性能结果不等于真实 Kimi 权重质量验证。[v0.17.0](vllm-v017-release.json) 的发布日期 2026-03-07 及两条 weight-offloading 说明已核，其他 release 条目未作本轮阅读。

当前配置的 auto 优先级、参数段匹配与 SGLang 不能混用。UVA 是 GPU 访问主存，不能写成 CPU 计算，也不代表链路流量消失。主存／设备是否共享物理容量按具体平台检查。

## SGLang：权重预取与 CPU 专家

[2025-10-22 KT 公告](sglang-kt-2025.html)的正文、命令、文本表和图注已读，图片曲线与表格未独立数字化。公告仍将集成称为 proof of concept；原 KTransformers 单卡实验与 SGLang 多卡预览分开。ShareGPT 表的 227.85 是总 token/s、87.58 为输出 token/s；CPU 命令为 AMXINT4，GPU 服务名含 FP8，不能称所有权重均为 FP8。其 R1／V3 实验不改称 V4／K3，也不沿用总结段的“trillion-parameter”来描述这组模型。

固定 SGLang 提交沿用 `c99d906effa8bd05573995127f0d4a0984c5a96a`：

- [通用 offloader](sglang-current-offloader.py) 全 585 行：V1 按需搬入；V2 按组预取、事件与捕获分支；CPU、共享主存及 GPU 分片模式。共享／分片路径有 TP=1 和布局限制，代码中存在这些模式不表示所有模型入口或组合均已支持。
- [KT wrapper](sglang-current-kt.py) 全 393 行：kt-kernel 依赖、GPU／CPU 专家划分、物理到逻辑映射、TP rank 0 的 CPU 提交与结果合并；SiLU 条件、deferral 参数及最后一层限制。未读取 kt-kernel 内部算法、通用 EP 支持或所有模型的实际调用链。

重新核读已归档 [2025 GB200 第二期](../overlap-placement/sglang-gb200-2025-sept.html)的 Scaling Down by Offloading 段，连接“互联足够快时减少 EP 卡数”的设计选择。其 900 GB/s 为双向峰值，不能代替题设的单向有效传输率。Expert Deferral 改变跨层贡献到达次序，公告承认模型行为变化；普通同层 submit／compute／merge 和 deferral 分别评估。

## Ollama：模型层、辅助阶段与内存报告

[v0.30 GGUF 公告](ollama-gguf-2026.html)正文和图注已读：文章日期 2026-06-05，Gemma 4 26B／5090／Q4_K_M 条件保留；Vulkan 默认启用与 GGUF 支持按公告范围表述。[v0.30.0 release](ollama-v030-release.json)正文、已知限制与发布时间已读，GitHub published_at 为 2026-05-13，不能用公告日期覆盖发布记录。

[固定 llm 目录](ollama-llm-directory.json)仅用于定位文件。沿先前已核的 `83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8` 读取 [llama-server 客户端](ollama-current-llama-server.go)的 386–420、635–705、2642–2695 行：自动／指定 GPU 层，projector 单独落 CPU，内存报告中 mmap 重复计数处理和全部文本层卸载时的显示规则。实际上游算子路径与完整启动恢复未审查。

此前归档的 [2024 llm server](../overlap-placement/ollama-2024-llm-server.go)本轮补读 1–135、182–201 行：容量估计、CPU 选择与传给子进程的 `--n-gpu-layers`。2025 的分配反馈与当前 scheduler 继续复用[已读范围](../overlap-placement/README.md)。内存驻留显示不是利用率，projector 和语言层也可能有不同执行位置。

## 多模态候选，尚未纳入提纲

[vLLM-Omni 2026-08-17 分布式逐层卸载文章](vllm-omni-dlo-2026.html)本轮只读官方页面开头、加载与权重分片，以及双缓冲引入部分；后续评估未读。[PR #5864](vllm-omni-pr5864.json)只核 2026-08-08 的合入身份并读 Why／Architecture 开头：DLO 的 DP 请求仍受权重 AllGather 与相容控制流约束。这两份是下一轮多模态调研候选，不登记会议正文阅读，也未将未核完的性能值或命令放进书中。

采用内容与教学计算见[权重卸载算例](../../../../case-studies/weight-offload-execution.md)。第 9.4／10.3 及现有实验补容量、带宽、CPU 算力、批量与质量条件；正文不逐项罗列配置参数。

后续多模态阶段已读完 DLO 文章正文、文字表和限制，以及 PR #5864 的完整描述；固定 backend 的分片、事件和两类双缓冲也已选读。前述“开头待读”是本目录最初阶段状态，后续范围见[多模态归档](../multimodal-execution/README.md)。生成卸载只保留研究对照，不增加正文模型小节。
