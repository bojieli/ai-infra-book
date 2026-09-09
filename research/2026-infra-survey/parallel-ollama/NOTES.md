# Ollama 两项演进：后端选择与思考控制

核对日期：2026-09-09。按根任务授权，仅在本目录写入；未改大纲、skeleton、共享索引或 Git，未执行下载代码、安装框架、下载权重或运行设备实验。已检查工作目录及父目录、`research`、`research/2026-infra-survey` 和本目录的 `AGENTS.md`，均未发现。

先读 `framework-coverage.md` 与 `case-studies/framework-evolution.md` 的 Ollama 段。加载反馈、MLX 状态快照、MTP、KV 量化、多 LoRA、结构化生成已有较密证据，本次不重复追加这些专题。新增材料只支持下列两个已有问题的具体实现，不增加框架介绍节。

## 1. Vulkan 从编译选项到默认发现：能发现哪些卡，最终用哪条路径

**建议作为第 5.5.1 后端对照的一个变体，实验沿用第 8-7 的小模型容量/放置记录。** 原来只列 Metal/CUDA/MLX，缺少“默认支持另一后端，不代表所有设备都实际选用该后端”的可核例子。

### 可确认的演进

- [v0.12.6 官方 release](https://github.com/ollama/ollama/releases/tag/v0.12.6) 发布于 **2025-10-15T23:02:31Z**。其 Vulkan 段明确为**本地源码构建的实验支持**，未来才加入预编译发行包。因此不能把这个日期描述成所有安装包默认启用 Vulkan。标签解析到 `1813ff85a027d7d4d76761a2bf12c2198dfaa0cf`。
- [v0.30.0 release](https://github.com/ollama/ollama/releases/tag/v0.30.0) 发布于 **2026-05-13T14:32:54Z**，而 [GGUF 公告](https://ollama.com/blog/improved-performance-and-model-support-with-gguf) 日期为 **2026-06-05**，两者分开。该公告把 Vulkan 默认启用与扩大 AMD/Intel 设备覆盖相联系，也说明普通 GGUF 走 llama.cpp、Apple MLX 是另一条路径。公告中 NVIDIA 的“最高 20%”对应 Gemma 4 26B / RTX 5090 / Q4_K_M，**不是 Vulkan 对 CUDA 的对比数字，本次不采用该加速倍数**。
- 获取日 [硬件指南](https://docs.ollama.com/gpu) 的 Vulkan 段已经写为**后端安装后默认启用**，针对 Windows/Linux；仍需可用驱动/运行库。网页搜索缓存显示的 `OLLAMA_VULKAN=1` 实验说明较旧，不能替代此次原页内容。当前 Windows 路径还显式选择系统/驱动提供的 Vulkan loader，避免旧应用目录内的 DLL 遮蔽系统运行库。

### 固定源码揭示的实际条件

当前官方提交固定为 [`86f72929348d384336b6f0adc129e71b2122abdc`](https://github.com/ollama/ollama/tree/86f72929348d384336b6f0adc129e71b2122abdc)，提交时间 **2026-09-09T00:09:48Z**。下列行数对应本目录原字节，而非未来 main。

| 路径 | 已核读的条件 | 对推算的影响 |
|---|---|---|
| `discover/runner.go:98–126`，`envconfig/config.go:177–196,233–236` | 用 `EnableVulkan(true)` 控制库目录发现；显式关闭才跳过 Vulkan 目录，之后继续做设备筛选 | 默认发现与实际调度分开；没有安装后端/驱动，开关本身不能产生设备能力 |
| `discover/runner.go:382–435`，对应测试 135–190 行 | Darwin/arm64 单独处理；其他平台已识别为集成 GPU 的 Vulkan 设备在默认准入中不被保留，显式 iGPU 选项才改变这一筛选。CUDA 和部分 ROCm 集成设备另有条件 | “Vulkan 默认启用”不能简化成“所有 iGPU 默认可用”；对照实际识别与准入日志，不只看 UI 支持表 |
| `discover/vulkan.go`，`discover/llama_server.go:203–216,370–393,480–489`；测试 109–137、388–439 行 | 利用 UMA 元数据、名称/显存校验和 Windows 查询；两次枚举的设备顺序可能不同，不能用原生探针序号直接覆盖 llama-server 的序号 | 共享主存与独立 VRAM 先辨身份；不能把同一 UMA 容量再当一份 GPU 独立容量相加 |
| `ml/device.go:181–227,405–415`；`discover/runner.go:208–245`；对应 duplicate 测试 112–179 行 | 同一物理卡可能同时出现在 Vulkan 与 CUDA/ROCm 下；去重时优先保留 CUDA/ROCm。缺 PCI ID 时还用受限的名称/容量匹配 | 两个后端条目不是两张卡，容量/算力不能相加；默认优先规则也不是逐请求测得的最快后端 |

测试里有 CUDA/Vulkan 同一 4060 Ti 与 ROCm/Vulkan 同一 AMD 卡的去重，以及 iGPU/dGPU 枚举顺序相反的反例。它们是静态单测的预期输入与输出，**本次没有执行测试，型号与显存也不作为芯片规格来源**。

**论文与实现的边界。** 这是一项硬件覆盖、发现、准入和分派演进，不把它硬归因到某篇新论文。第 4 章的 Roofline 或其他本地推理论文只能提出预期：真实后端的矩阵内核、数值格式、缓存和驱动会改变有效性能。现有公告和所读代码不足以证明 Vulkan 对任何 Qwen3 配置更快，也未审完整 GGML Vulkan kernel、打包 CI 或所有硬件兼容性。本次能补齐的是**选择了什么执行路径**，性能仍需沿原实验同模型、同精度、同上下文记录。

**拟加入现有段落/实验的一句话：**

> Ollama 的 Vulkan 演进提供另一个后端例子：先核对同一物理设备如何被发现、去重和准入，再确认本次请求的实际库与层放置；默认启用某后端，不能直接作为容量增加或性能改善的证据。

不建议给第 4 章再新增一排芯片或设备表。实验可以复用已有 Qwen3-8B 文件与 KV 预算，在受支持的固定环境中保存设备身份、backend、内存归属、TTFT/逐 token 延迟；这些日志和设备实验尚未制作。

## 2. Thinking 的开关、effort 与真正 token 预算

**建议补在第 11.4.3“任务质量与思考预算”，沿用实验 11-8；第 3→8 章继续使用已有负载与阶段定义。** 现有提纲已经正确要求区分配置预算、实际用量与可见摘要，此项提供真实框架的反例，不需另造抽象术语。

### 版本演进与模型条件

- [v0.9.0 release](https://github.com/ollama/ollama/releases/tag/v0.9.0) 发布于 **2025-05-29T05:41:01Z**；[Thinking 公告](https://ollama.com/blog/thinking) 为 **2025-05-30**。API 增加 `think` 与分离的 `thinking` 字段，CLI 区分开关与 `--hidethinking`。标签固定为 `5f57b0ef4268a6bd9e8043d54c351a608a7e1bca`。早期 `server/routes.go:188–193,263–291,1510–1524` 已把布尔值传入模型模板，再用推理标签解析输出；代码也提示旧模型模板可能不支持该控制。
- 获取日 [Thinking 指南](https://docs.ollama.com/capabilities/thinking) 仍将 Qwen3 列为支持模型；同时明确 GPT-OSS 使用 low/medium/high，不能将思考完全关闭。当前通用 `ThinkValue` 支持布尔和字符串（含 max），**通用字段接受某值，不等于每个模型都支持该值的相同语义**。这不是 GPU 型号专属优化，首先取决于训练/模板与被选 runner。

### 三条容易混淆的实际路径

1. **隐藏显示不会关闭执行。** 当前 `cmd/cmd.go:752–778` 将 Think 与 HideThinking 分开保存；1790–1806 行只在终端显示函数前检查 HideThinking，而 1840–1846 行的 API 请求发送的是 Think，没有 HideThinking 字段。服务端仍生成并返回相关内容。因而隐藏思考通常也不减少客户端收到的服务响应字节，更不能凭更短的终端输出推断推理省 token。
2. **当前原生 llama-server Chat 路径传的是模板控制。** `server/routes.go:2371–2398` 区分原生与 Ollama 渲染/MLX 路径；2982–2994 行将 Think 传入原生请求。`llm/llama_server.go:2147–2213` 将布尔转为 `enable_thinking`，字符串另外传 `reasoning_effort`；单测 3594–3631 行明确区分 unset、false、true、high。源码的总生成上限 `n_predict` 是另一个参数。不能把 `think="low"` 换算成固定 100 token，也不能把总生成上限当作“保留完整答案的精确 reasoning 上限”。
3. **计数与显示字段分开。** 同一原生路径 1990–2047 行把上游 `reasoning_content` 单独映射为 `Thinking`，总生成计数/时间来自 `predicted_n/predicted_ms`；外层 routes 再转发 Metrics。没有通过“可见 content 字符数”重算总 token。实际实验仍需核对所安装上游的 usage 语义、tokenizer 和特殊 token，不拿 API 摘要长度代替执行量；本次也没有核查 Ollama Cloud 的计费定义。

### 与 Qwen3 报告的具体差距

已复制仓库既有 [Qwen3 v1 技术报告](https://arxiv.org/pdf/2505.09388v1) 原件，只重读 **物理第 11 页，§4.3 与表 9**，并实际看该页渲染，未声称全文重读。报告描述两件不同的事：模板中的空 think 块用于非思考模式；精确思考预算则在达到 token 阈值时中断思考，插入结束思考指令，再继续产出答案。后一个机制需要显式阈值检测和续生成。

本次所读 Ollama `ThinkValue→chat_template_kwargs` 路径并没有实现这种“阈值处插入指令后继续”的控制器；只能据此说**该调用路径不是论文预算算法的直接复现**，不能据有限文件搜索断言整个仓库/所有后端绝无其他预算机制。原生 GGUF、Ollama 渲染、MLX、远端服务不能混作同一条调用链。Qwen3 作者网页的混合模式说明仅作历史背景；不从预算图估读质量曲线，也不推广到新模型。

**拟加入现有段落/实验的两句话：**

> 用 Ollama 的 Qwen3 调用核对“隐藏思考”“关闭思考”与模型支持的 effort 参数：先检查送到后端的实际控制，再分别记录首个思考 token、首段可用答案、完整任务时间和总生成用量。对照 Qwen3 报告在阈值处结束思考再续写答案的方法，说明通用生成上限与精确思考预算为何是不同实验。

复用现有 100/1,000 个思考 token 的算例，不重复增加费用表。将“开启并显示”和“开启但隐藏”作为同一请求控制下的显示对照；“关闭”只有在固定模型/模板确实支持时才比较，并重新检查任务通过率。若使用 `num_predict` 制造短响应，要把预算耗尽、答案未完成和成功率变化保留下来，不能标成无损省 token。准备配套记录时同时保留真实请求、后端、模板/模型标识、缓存状态与 finish reason；本次未运行这些实验。

## 交付与未完成范围

- `sources.json`：43 个实际 HTTP 响应的 URL、状态、获取时间、字节和 hash。包括一个错误猜测源码路径返回的 404，已保留而未用于任何结论；其余 42 个为 200。导航树与尚未精读的下载文件不计正文阅读。
- `reading-proof.json`：逐文件的实际阅读区间与片段 hash、章节快照、Qwen3 单页看图记录、历史标签解析，以及未运行边界。
- `qwen3-report.pdf` 来自仓库现有归档，来源标为本地转存，不伪记成新的网络取回；只增加本次第 11 页的聚焦核对。
- `verify.py` / `verification.json`：校验归档完整性、区间与不可变提交。只运行本任务自写校验程序，未运行下载源码中的测试。

本次完成两项代表性演进及现有章节落点，**没有完成 Ollama 全部 release、所有执行后端或全书实验的验收**。尤其未审 upstream llama.cpp 的完整 reasoning token 计数、GGML Vulkan 实际算子分派与各厂商驱动性能；这些边界应随实验保留，不用功能公告补成性能结论。
