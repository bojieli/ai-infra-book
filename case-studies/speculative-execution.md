# 推测解码的执行成本与动态预算

第 8.3 节沿同一问题比较框架变化：每轮草稿和验证花了多少时间，最后产生多少有效 token。Qwen3-8B 负责逐步计算，V4 的 DSpark 和 Ollama 的 Gemma 4／MLX MTP 提供不同执行路径。这里是来源与扩写笔记，没有运行模型或执行下载的代码。

## 从算法接入到执行与调度

| 证据与版本 | 值得保留的变化 | 扩写时采用的范围 |
| --- | --- | --- |
| [vLLM，2024-10](../references/framework-history/2026-09-08/speculative-execution/vllm-2024.html) | 草稿／目标 runner 接入连续批处理，多 token 槽位与双模型 KV 管理；高负载可能抵消加速 | 当时按负载动态调节仍列为路线图，不能写成已有自动能力 |
| [Speculators v0.3，2025-12](../references/framework-history/2026-09-08/speculative-execution/vllm-speculators-2025.html) | 从目标模型抽取特征、训练匹配草稿，再由 vLLM 加载目标与草稿 | 草稿训练是配套工具的工作；更换目标精度还需检查接受行为及质量 |
| [P-EAGLE，2026-03](../references/framework-history/2026-09-08/speculative-execution/vllm-peagle-2026.html) | 将串行起草改成一次并行起草，融合 token／位置准备，并处理独立的草稿布局 | 需要专门训练的草稿；目标与草稿的图形状、KV 槽位不能直接复用 |
| [SGLang MTP，2025-07](../references/framework-history/2026-09-08/speculative-execution/sglang-mtp-2025.html) → [Spec V2，2026-06](../references/framework-history/2026-09-08/speculative-execution/sglang-specv2-2026.html) | 从 MTP 尚不能与主机重叠调度同用，到清理上一批、准备下一批与 GPU 执行重叠 | TBO 的计算通信重叠和 overlap scheduler 的主机设备重叠分开说明 |
| [SGLang DSpark，2026-07](../references/framework-history/2026-09-08/speculative-execution/sglang-dspark-2026.html) | 按请求置信度选择验证长度，紧凑装入图输入，再按实测成本选预算 | 讲验证工作怎样减少，保留图档位、DP 协同及成本模型局限 |
| [Ollama MLX，2026-06](../references/framework-history/2026-09-08/speculative-execution/ollama-mlx-performance-2026.html)与[已归档 MTP 公告](../references/outline-checks/2026-09-07/framework-evolution/ollama-mtp.html) | 分支与响应前保存状态；MTP 动态起草、拒绝回滚和小批验证权重复用 | 限定 Gemma 4／MLX 的对应支持；减少思考历史后的续接与逐轮拒绝回滚是不同边界 |

日期另有核对：P-EAGLE 的统一并行草稿 PR 于 2026-02-05 合入，v0.16.0 于 02-25 发布，介绍文章为 03-13。DSpark 文章标为 07-06，相关 PR 于 07-12 合入，文中的复现入口曾固定在 PR 提交。公告、分支复现和正式主线不是同一个时间点；获取日文章也可能包含后续更新。当前源码快照及精确阅读范围见[来源索引](../references/framework-history/2026-09-08/speculative-execution/README.md)。

## 三种动态方案各依赖什么

vLLM 当前的[按 batch 大小选 K](../references/framework-history/2026-09-08/speculative-execution/vllm-dynamic_speculative_decoding.md)使用配置的区间表，可在高并发时选 K=0；这张表不是自动学习出来的最优配置。所读版本会在数据并行大于 1 时禁用它，以免独立选 K 导致集合操作不一致。当前另有 [DSpark 自适应验证](../references/framework-history/2026-09-08/speculative-execution/vllm-adaptive_verification.md)：需要置信度头和完整 CUDA Graph，启动时测成本，默认关闭，不支持所述 LoRA／PP 路径。两项机制不能互换支持条件。

SGLang 的 [EAGLE 自适应步数](../references/framework-history/2026-09-08/speculative-execution/sglang-adaptive-guide.mdx)按 batch 区间分别维护接受长度的滑动估计，在预先准备好的图和后端状态之间切换；仅支持所列 EAGLE／EAGLE3、top-k=1 条件。准备多档会占更多启动时间和显存。DSpark 则进一步区分同一批内的请求，目标是单位时间的预期产出，不能只最大化接受长度。

这些方法都需对照真实耗时。SGLang 所读[成本表实现](../references/framework-history/2026-09-08/speculative-execution/sglang-dspark-sps.py)按请求数和总验证 token 数估计时间，插值超出采样区间时钳位到边界；它没有把上下文、KV 层次或竞争自动纳入参数。vLLM 当前自适应验证默认用 8,192-token 合成上下文采集成本。长上下文与共享资源实验应重新校准；人为接受率仅用于隔离性能，不能用来证明目标分布或真实草稿质量。

## 接受长度和实际产出

声明一次线性验证最多检查 k 个草稿 token，连续接受 a 个，再产出一个补偿或额外 token；暂不计 EOS、输出上限和请求结束截断。该轮产出为 a+1。若第 j 个草稿在前面均被接受时的条件接受概率是 p_j，则期望产出为 `1 + Σ(j=1…k) Π(i=1…j) p_i`。真实记录优先使用逐轮计数，不能把一个全局平均接受率不加条件地代入各位置。

vLLM 所读[日志实现](../references/framework-history/2026-09-08/speculative-execution/vllm-spec-metrics.py)中，mean acceptance length 是 `1 + accepted / drafts`，draft acceptance rate 则是接受草稿数除以提议数。[逐请求指标](../references/framework-history/2026-09-08/speculative-execution/vllm-acceptance_metrics.md)还提供逐步计数，默认不收集，流式输出的统计在相应最终 usage 块中。实验保存定义和终止条件；数字超过 k 时，先检查是否包含额外 token，不能马上归因于算法错误或更强预测能力。

## 四个请求的验证预算

以 Qwen3-8B 的一个 batch 为教学输入，四个请求每位置的条件接受概率分别假设为 0.9、0.5、0.3、0.3。先都提议 6 个 token，再比较将验证上限改为 6、2、1、1。这里的概率、图档位及时间均为教学假设，并非 DSpark 或 Qwen3 的测量。

每请求验证输入明确计入一个已有 token，因此完整验证共 `4×(6+1)=28` 行，紧凑验证共 `7+3+2+2=14` 行。假定图档位为 8、16、32，分别执行 32 行与 16 行；若仍执行原来的 32 行图，仅用 mask 丢弃结果，就没有省下对应矩阵工作。

接回模型矩阵：单层 FFN 的 gate／up 各为 `[M,4096]×[4096,12288]`，down 为 `[M,12288]×[12288,4096]`。三次矩阵乘在 M=32／16 时分别为约 9.664／4.832 GFLOPs。这里只计 FFN，注意力、草稿和状态维护另算，显存访问也不能直接按这个比例缩减。

假设每步有 2 ms 固定工作，另外每执行行需 0.1 ms。固定工作包括本算例中不随截短减少的草稿和主机成本，得到：

| 方案 | 每轮预期产出 | 执行行数 | 每轮时间 | 教学总产出率 |
| --- | ---: | ---: | ---: | ---: |
| 完整验证 6／6／6／6 | 10.057924 | 32 | 5.2 ms | 1,934.22 token/s |
| 紧凑验证 6／2／1／1 | 9.567031 | 16 | 3.6 ms | 2,657.51 token/s |
| 限制提交，仍执行原图 | 9.567031 | 32 | 5.2 ms | 1,839.81 token/s |

少产出一些 token 仍可能更快，前提是确实省下了更多时间。若有另一个 DP rank 的紧凑输入仍需 25 行，且所用路径要求各 rank 采用同一图档位，两边仍要执行 32 行档；单看本地 14 行就会高估收益。这只说明同步档位约束，不直接给出全系统吞吐。

再比较“原图完整验证，但只提交预算内结果”的诊断运行与紧凑运行。它能观察被截掉部分原本是否会被接受，帮助判断置信度是否失准；诊断运行本身做了更多工作，不能把它的耗时当成紧凑运行。只看被保留下来的高置信度位置，会夸大接受率；未知尾部不能一律当成拒绝。

输入和独立计算见[阶段算式](../research/2026-infra-survey/arithmetic.json)的 `speculative_budget_teaching`。先用这些数选择候选，再由固定框架和匹配草稿验证；不是重新编写一个完整推理模拟器。

## 实验与引用边界

实验 8-5 增加固定长度、按 batch 选长度、受支持的按请求预算三种对照。保存实际草稿与验证行数、图档位、KV／状态回滚、主机间隙和逐轮产出，分开算吞吐与用户逐 token 等待。实验 8-6 继续看 Agent 完成时间；图 8-4 把请求预算、实际矩阵行数和产出放在同一张自绘 SVG 上。

SGLang 2025 的表格将 60.4 相对 51.0 标为 +20.4%，复算约为 +18.43%；MTP 82.0 的对照又没有启用 overlap scheduler。因此不把“+60%”当成在最佳重叠基线上新增的收益，也不直接相乘两项加速。2026 的 DFlash 文章将研究原型消融与 SGLang 实验分开，图中的最优块长与示例启动命令也不同，扩写保留各自条件。

P-EAGLE 公布的是不同训练草稿在指定 B200 设置下的比较，包含接受质量变化，不能全部归为并行执行；文章称更深并行起草不增加串行轮次，也不意味着没有更多行、状态或计算。Ollama 的 MTP 公告用 Gemma 4 12B NVFP4／M5 Max／Aider 轨迹，不能推广为所有本地模型或 CPU 专家卸载路径的收益。严格采样要以所选目标分布为准；同分布、同 seed 和跨实现逐 token 一致分别检验。
