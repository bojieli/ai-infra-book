# 框架演进中仍值得补读的三处接口

本轮最多保留三项：**权重交接的服务恢复条件、DSpark 验证预算到真实执行形状的映射、Ollama MLX MTP 的自适应和拒绝恢复路径。** 它们分别决定有效 rollout 何时可供给、缩短验证是否真的省计算、少跑 decode 是否被恢复开销抵消；都是已有章节判断的条件，不建议新增功能节、模型或核心实验。

这三项是**尚未充分闭合的实施证据**，不是已经发现的正文错误或框架运行缺陷。现有写作大多已用条件式措辞保护了边界。只要继续将论文／公告、固定实现和待测收益分开，提纲可以继续扩写；不必先审完三个框架的全部仓库。

## 一、先排除已经关闭或不值得再扩张的历史待办

| 代表主线 | 本次看到的当前证据 | 取舍 |
|---|---|---|
| vLLM 2024 多步／异步输出 → 2025 V1 → 2026 异步状态；SGLang 2024 overlap → 2026 Spec V2 | `parallel-history-gaps.md` 的唯一优先待办，已经由 `parallel-host-timeline/NOTES.md:7–36` 的固定 engine loop、future token、在途占位、grammar 和实际接受长度补上；42 行明确剩余完整 trace 属于实验 | 不重复列为阅读缺口，不因没有全部异步 PR 日期而重新开题。 |
| 2024–26 图模式与 POD | `framework-evolution.md:11,43,89` 已分历史捕获、当前分派和 GraCE；`pod-callers/README.md` 已说明所读服务分支的 wrapper 与上下文合并，不把底层库存在等同上层采用 | 保留实验校准；不为证明全仓库没有 POD 而做无界搜索。 |
| vLLM／SGLang 的层次 KV、事件路由和弹性 EP | `cache-events/README.md` 已分数据、事件、预测索引、缺口恢复；`ep-reconfiguration/README.md:13–25` 已分副本分派、放置和扩缩容、模型支持及单输出测试口径 | 未读全部传输／优化 kernel 是现有范围限制，不自动成为新增缺口；没有建议补性能排名。 |
| 权重卸载与多模态 DLO | `offload-execution/README.md:36` 的“评估未读”已由40行以及 `multimodal-execution/README.md` 的文章正文、限制、backend 选读关闭 | 不把历史进度当成当前任务。完整上游调用链未全审，也不足以要求再扩张 DiT 主题。 |
| Ollama 后端与思考控制 | `parallel-ollama/NOTES.md` 已固定 Vulkan 发现／去重及 thinking 模板传参，并对照 Qwen3 报告的精确预算方法 | 论文预算控制与通用 effort 的差距已经讲清。上游 usage、驱动速度属于声明边界，本轮不重复开题。 |

这不是完整 release 清单复查。覆盖表和代表来源的已读范围已经足以说明上述主线，不把所有“未读”关键词都变成待办。

## 二、优先项 1：一轮权重交接何时产生可用的新策略

**影响的既有判断：** `framework-evolution.md:23,85,87,101` 与 `framework-coverage.md:18,34` 把休眠、恢复、分片权重和策略版本接到第 10.5／11.3 章。按字节算出的复制时间是阶段下界；若新版本还不能被所有相关设备安全使用，它不能直接换成可供给的 rollout 时间。

### 现有证据与本轮补读

`weight-handoff/README.md` 已明确：worker／allocator 的局部调用不等于全部派生状态恢复、权重版本提交与异常回滚。旧记录中的 SGLang runner 只有下载状态，本次确实补读了静态正文：

- 固定 SGLang `c99d906effa8bd05573995127f0d4a0984c5a96a`，`sglang-runner-weights.py:223–318` 的 distributed／bucketed 路径先接收参数、再调用模型 loader。失败分支在280与314行明确提示可能已经部分更新，要求丢弃整份权重。由此可知，返回失败不是对旧策略仍完整可用的证明；本次没有执行故障，也不据局部分支推断所有调用方处理错误。
- 同一提交 `sglang-scheduler-weights.py:104–189` 按请求决定是否 flush；成功后才记录版本。disk／IPC 路径区分 target 与 draft 的更新；tensor 路径在两者中选择一个 worker。由此应区分单次参数调用、target／draft 就绪、缓存处理和最终恢复服务。这里的 TP barrier 也不能单独证明全部 DP 实例的全局事务。
- 固定 vLLM `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`，`vllm-worker-current.py:1346–1445` 有显式 start／update／finish 会话；异常会清理会话标志／更新目标，finish 委托实际传输引擎并处理 LoRA 状态。**清标志不是旧参数数据回滚的证据**，worker 函数本身也不声明完整 RL 控制器语义。
- 本轮补读 RDT 官方文章既有抽取文本 `vllm-rdt-2026.txt:150–228`。173–176行的故障例子明确在 **SkyRL** 中完成：失效实例离开路由，在下一次权重同步边界重新加入。214–225行还限制 loader 操作、额外 GPU 接收缓冲、EPLB 兼容性和 PP 组传输。Kimi 表和性能图没有独立核验，不新增吞吐或故障收敛结论。

### 还缺什么，下一次只读哪里

目前仍缺一条完整的**控制器暂停／最后一批参数更新／缓存处理／版本确认／重新准入**的调用链，以及一个“部分参数已变更后失败”的处理结果。当前已有源码可以支持“必须分开计量这些时点”，尚不足以说默认服务在失败后自动回滚，或所有实例更新以同一原子时点生效。

建议下一次只关闭 **一个** 基线组合：普通 dense 的 target 权重更新，先不带 MTP、LoRA、EPLB 或外部持久 KV。继续沿已核 SGLang 提交的 `python/sglang/srt/managers/tokenizer_manager.py` 定位请求扇出、返回聚合与恢复入口，再接本次读过的两级 updater；只补实际调用到的 pause／resume 和权重版本记录函数。树中已有 `test/registered/rl/test_pause_generation_tensor_consistency.py` 与 `test/registered/unit/managers/test_scheduler_pause_generation.py` 可用于定位预期语义，**这些目前仅核了路径，测试正文待读且不应预先假定包含注入故障用例**。

如果根任务决定采用 vLLM RDT 作为实际基线，则替换上述路径，不两套同时扩张：同固定提交读 `vllm/distributed/weight_transfer/sharded_rdt_engine.py`、`clients.py` 的 finish／异常及调用入口，再用 `tests/v1/worker/test_gpu_worker_weight_transfer.py` 选相关测试。SkyRL 的剔除／重新加入能力必须另固定它自己的控制器提交；本次未获得该路径的固定身份，保留为明确缺口，不能借 vLLM 的提交代替。

**停止条件：** 能画出一个成功和一个中途失败的状态序列，并说明控制器从哪个可验证事件起才允许新策略产生有效样本。此后实际耗时、长时收敛和不同传输后端属于实验，不用继续读源码来替代。只沿用第 10.5 的权重交接与实验 10-8，不新增失败恢复章节。

## 三、优先项 2：DSpark 缩短的是逻辑预算，还是实际计算行数

**影响的既有判断：** `framework-evolution.md:36,99` 与 `framework-coverage.md:9` 已经把按请求预算、CUDA Graph、DP 共同档位和成本表相连。第 8.3 节现有四请求算例的价值，正是让读者知道“少验证几项”不必然让目标模型少执行同等数量的行。

### 现有证据与本轮复核

- 已归档 DSpark 集成文章 `sglang-dspark-2026.txt:19–51,113–150` 明确区分原论文算法和 SGLang 接入；输入、硬件和流量不同，不复刻论文的每个数字。文章声明先紧凑排列，再按总 token 数选择捕获档位，DP attention 各 rank 共享最大需求档位；cap-accept 只是观测被截短尾部的实验模式，不能当作实际节省的执行量。
- 本轮完整静态重读固定 `sglang-dspark-sps.py`。`SpsCostTable.lookup` 返回向下选择的离散探测值；`SpsAdditiveCostTable.step_time` 使用 `bias + alpha(num_reqs) + theta(num_reqs + budget)`，插值在边界截断。这份源码是成本表，不负责把请求窗口真正变成 varlen 输入、图档位或执行张量。
- 该来源原记录已直说 **planner／worker 未审计**。后来的 `parallel-host-timeline/NOTES.md:29–36` 读的是 EAGLE V2 变体，关闭了主机等待与实际长度的问题，但不能替代 DSpark 专有 planner／verify 的证据。
- 集成文章181–185行承认当前成本拟合对上下文长度的描述仍是近似。本轮不将成本表的函数签名误判为整个 planner 没有更多状态，也不重新计算已经核过的接受率分母。

### 最小的下一阅读动作

固定 SGLang `c99d906effa8bd05573995127f0d4a0984c5a96a`，先读已经由树定位的三处路径：

1. `python/sglang/srt/speculative/dspark_components/dspark_planner.py`：从实际传入的成本、置信度到每请求预算；核最低保留位置与 fallback，不泛读全部算法。
2. `.../dspark_verify.py`：预算、紧凑 offset、DP 共同档位和目标输入的衔接。若它委托 worker／kernel，只沿调用到的一个分支读 `dspark_worker_v2.py` 或 `kernels/ops/speculative/dspark/dspark_verify_window.py`，不先下载整组内核。
3. 对应 `test/registered/spec/dspark/test_dspark_dp_tier.py` 和 `test_ragged_verify.py`：选一个“不跨档位”和一个“跨到较小档位”的预期例子。当前只是固定树中的定位，不能写成测试已经读过或通过。

**停止条件：** 对现有四请求窗口，能明确列出逻辑窗口总长、必要保留位置、紧凑输入行数、padding 后图行数，以及 DP 另一 rank 是否阻止降档；成本表只解释该条件下的候选选择。无需补齐全部 DSpark kernel 或重现论文排行榜。实际每轮时间仍需同模型／后端记录。

此项补的是原论文方法／官方集成说明到固定执行路径的接口证据。本轮没有新增或宣称完成 DSpark 原论文正文阅读，也不由文章日期推断该版本首次上线。保持第 5.4→8.3 及实验 8-5／8-6。

## 四、优先项 3：Ollama MLX 的 MTP 回滚要付出哪些实际代价

**影响的既有判断：** `framework-evolution.md:62–67,99` 把选择性状态快照与 Gemma 4／MLX MTP 作为本地例子。第 8.3 的每轮收支若用于解释本地加速，就需要知道恢复的是哪份状态、何时选择退回普通 decode，而不能只引用公告倍数。

### 现有证据与本轮复核

- 通过推测专题 README 的直接引用，重读既有 `ollama-mtp.txt:1–42`。2026-06-29 公告区分动态草稿长度、逐轮 GPU 执行、拒绝回滚和2–8 token的小矩阵；其主要测量条件是 Gemma 4 12B NVFP4／M5 Max／编码 Agent 任务。这是官方机制与条件的证据，尚不是固定 runner 的实现审查，不采用其“不会变慢”等概括作为一般保证。
- `speculative-execution/README.md:11,15–17` 已声明文章与 vLLM／SGLang 代表文件，未给 Ollama `mtp.go`／`speculate.go` 的已读范围。`parallel-ollama/NOTES.md` 后续补的是 Vulkan 和 thinking，没有闭合该路径。
- 本轮重读 `hybrid-state/ollama-recurrent.txt:126–169,180–248` 和 `ollama-cache-trie.txt:33–105`。这些固定代码表明递推状态只能恢复到精确 offset，内部边界需要实际产生对应状态；Clone／Pin 与后续求值分开，trie 对某些 lazy snapshot 的字节随物化增长。**这能支持状态预算的方法，不能证明 Gemma 4 的 MTP 就使用该 recurrent cache，也不能把逻辑 Size 总和直接当成即时物理拷贝量。** 当前 Gemma MTP 的拒绝路径尚未读取。

### 最小的下一阅读动作

沿已核 Ollama `83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8` 的同一棵树，先读 `x/mlxrunner/mtp.go`、`speculate.go`、`speculate_depth.go` 中一轮草稿、验证、提交／拒绝、选择下一长度的函数。以 `mtp_test.go` 和 `speculate_depth_test.go` 找一个早拒绝与一个全接受的预期序列；**目前只有这些路径／blob 的身份，正文和测试均待读**。

随后只追该 Gemma 路径实际调用的 cache：需要滑窗则读 `cache/rotating.go`，需要普通 KV 则读 `cache/kvcache.go`，不要预先选递推缓存作替身。只有在计算拷贝容量时仍无法判断 Clone 的成本，才接 `mlx/array.go`；不因此扩成全部 MLX／Metal 内核审查。小矩阵“每块权重读一次”的低层优化若要给确定流量，则另固定其 MLX 依赖版本及被调用 kernel；本轮只有公告，尚没有已核的该依赖提交，不把 Ollama 主仓库提交当作 MLX kernel 身份。

**停止条件：** 同一 Gemma 支持路径的一轮表能分开草稿／验证、提交的真实输出、被拒绝位置、缓存恢复与控制器适应成本。保留质量与采样条件，不由一次回退规则保证任意非平稳负载没有损失。与第 8.2 快照案例交叉引用即可，沿用实验 8-5／8-6 的本地选做。

## 五、哪些是已读，哪些仍只是建议

本次没有下载新资料、运行第三方代码／测试／框架或执行 GPU 任务。只运行自写的目录定位、文本读取与哈希核验；没有新增论文正文计数。没有修改共享案例、大纲、索引或既有来源记录，尤其没有把原 `downloaded_not_read` 行直接覆盖。其后续新增范围由本报告声明。

已有六份源码按 `SHA1("blob " + byte_length + NUL + 原始字节)` 与固定树条目比对，全通过；相关原件也与既有 `sources.json` 的 SHA-256 相符。树只是这批归档的身份依据，不宣称本次重新联网核对远端 HEAD、审完整 Git 历史或运行任何测试。文章使用归档时版本；后续页面修改与发布日、PR 合入日分开。

| 本次检查的原文件 | 固定仓库路径 | 已核 Git blob SHA-1 |
|---|---|---|
| `weight-handoff/sglang-runner-weights.py` | `python/sglang/srt/model_executor/model_runner_components/weight_updater.py` | `e9dd1c7023f95b53a2bc8380754fe416e89c3007` |
| `weight-handoff/sglang-scheduler-weights.py` | `python/sglang/srt/managers/scheduler_components/weight_updater.py` | `9c838e59ff8a580215039661adc644663b8cb1eb` |
| `weight-handoff/vllm-worker-current.py` | `vllm/v1/worker/gpu_worker.py` | `53bc0550a524b02249a6fbcbf027ab162f1f9d3c` |
| `speculative-execution/sglang-dspark-sps.py` | `python/sglang/srt/speculative/dspark_components/dspark_sps.py` | `bfefe12195b2d3fafd6c9a2c80602caf0721a320` |
| `hybrid-state/ollama-recurrent.txt` | `x/mlxrunner/cache/recurrent.go` | `c394161f9fb0995eed3a488e1d09d8bc3d902182` |
| `hybrid-state/ollama-cache-trie.txt` | `x/mlxrunner/cache_trie.go` | `535a0a2cdcd3dc96c82b460fb0f106e34c825dab` |

上表短路径均相对 `references/framework-history/2026-09-08/`。涉及文章的原始 URL／获取日／状态仍在各 `sources.json`：SGLang updater 为2026-09-08成功响应，DSpark 为2026-09-07成功响应，Ollama recurrent/trie 为2026-09-08成功响应。全部是固定归档复用，没有伪记本轮网络请求。

## 六、本次输入快照与实际范围

登记 UTC：2026-09-09T07:49:33+00:00。以下 SHA-256 针对完整原始字节；读取范围只按最后一列声明，哈希全文件不等于读过全文件。章节落点依据当前 framework-evolution／framework-coverage，本轮未扩张到主大纲全文重审。

| 输入 | bytes／行数 | SHA-256 | 实际读取或用途 |
|---|---:|---|---|
| `case-studies/framework-evolution.md` | 23002／113 | `271930ce73983f2ea450a688a6468d2881e0fb287411253efc4af727cfb81d7e` | 全文 1–113；代表问题与采用边界 |
| `research/2026-infra-survey/framework-coverage.md` | 15375／62 | `7c4110d8ea86cc13fd39f946edcaba5b43de4b9e923d2ecc2676133ec5c8778f` | 全文 1–62；当前覆盖与后续补读入口 |
| `research/2026-infra-survey/parallel-history-gaps.md` | 8931／64 | `4baa4fe2fcccf39226a6f294f7bbc9249e4b80544974cb6506e422bad074ebca` | 全文；历史唯一待补点，不作为当前未闭合事实 |
| `research/2026-infra-survey/parallel-host-timeline/NOTES.md` | 8988／44 | `8fcb3dba85cf05ecc94bef8836130122f3d3c37500000c77a4b4ff589f5bf49d` | 全文 1–44；后续关闭主机调度资料缺口的证据声明 |
| `research/2026-infra-survey/parallel-ollama/NOTES.md` | 11469／72 | `9ec08721041ad6480d08816b65cb03bd00762a4cf214a5824f9a403d30155350` | 全文 1–74；已覆盖后端与 thinking，不借此推断 MTP 内核已读 |
| `references/framework-history/2026-09-08/speculative-execution/README.md` | 3284／21 | `4f0458dae25d861c51baa415f67567eac125f85170382808a287b8fec7a099ce` | 全文 1–21 |
| `references/framework-history/2026-09-08/hybrid-state/README.md` | 5484／39 | `ce0598ba0fc14debc599823a765b111222d8fd3f00c60a2265970a590718b4ee` | 全文 1–39 |
| `references/framework-history/2026-09-08/ep-reconfiguration/README.md` | 4316／27 | `2eba80e6e82d533a86531a91898162bc91dbdbf868f00ad44a40e15fed000f9f` | 全文 1–27 |
| `references/framework-history/2026-09-08/offload-execution/README.md` | 6117／40 | `1245128cae742cf45d452163505883598185a8307619625884d6932db553137d` | 全文 1–40，特别核后续 DLO 关闭说明 |
| `references/framework-history/2026-09-08/weight-handoff/README.md` | 4252／23 | `e3fa4656c48a738dfdfcfddb9bd35d39347506af4e4e5af66335b66e4086fd72` | 全文 |
| `references/framework-history/2026-09-08/cache-events/README.md` | 3552／23 | `f68dbee99e884d813170da0cc23cc29cc69a088f73ecfe26c7a1f38e6c64fa45` | 全文 |
| `references/framework-history/2026-09-09/pod-callers/README.md` | 3176／17 | `1693fb1bdd1b99aa180e222d68407ab8248849e90731f4a401531d05f63b78a7` | 全文 |
| `references/framework-history/2026-09-08/multimodal-execution/README.md` | 3231／14 | `e2de094734d7eb35364516dee72bb818fe7683c0acb26d7668b0e422251a24ee` | 全文 |
| `references/framework-history/2026-09-08/weight-handoff/sglang-runner-weights.py` | 16721／431 | `957af66d52c8324f58c40c5041c53a34063f5c8bf95694a11642bb0a959adbef` | 静态正文 127–354；此前来源记录为 downloaded_not_read，本报告新增此范围 |
| `references/framework-history/2026-09-08/weight-handoff/sglang-scheduler-weights.py` | 15330／367 | `753120e53a7ff15f5fad76585ae7451cf4cdcfc0d75b58ef33d4f55b38ed3793` | 静态正文 85–189；此前 scope 为 196–300，本报告新增此范围 |
| `references/framework-history/2026-09-08/weight-handoff/vllm-worker-current.py` | 64048／1523 | `8d81dfb9e058f2bf86cca646209df0afe592e0e7a47add9fc6b73cdccfd1d79c` | 静态正文 1340–1490；会话、异常、finish 和 LoRA 状态处理，部分重读 |
| `references/framework-history/2026-09-08/weight-handoff/vllm-rdt-2026.txt` | 21925／248 | `91d2d496a233b881b958a3680065758c7323060025c4b6428cdc286de0c1cf56` | 150–248；新增尾部正文和限制，末尾相关文章只定位、不采用；未看性能图 |
| `references/framework-history/2026-09-08/speculative-execution/sglang-dspark-sps.py` | 5737／163 | `5bc24190ddc91fad9fd42d723c939b3eb3b32df74d2c3f3e12d247665c424f28` | 全文静态重读；没有导入或调用函数 |
| `references/framework-history/2026-09-08/speculative-execution/sglang-dspark-2026.txt` | 15899／353 | `36c1b415c066977f123bb7cf9773a78a4af29b5de0e6c3fac30228eeb30ef29d` | 15–51、110–151、175–241；其他位置关键词定位；未看图或数字化曲线 |
| `references/framework-history/2026-09-08/speculative-execution/ollama-mlx-performance-2026.txt` | 4192／42 | `ebb7f924336ba2bc094e03bb170bcd72526c20b915bd1814918e5d8cac5ac941` | 全文重读；没有采用性能图 |
| `references/outline-checks/2026-09-07/framework-evolution/ollama-mtp.txt` | 5084／42 | `cbaf4f841c10d597408533318bab32881cf9a92733e1aca635a59d3f863e20ac` | 沿推测专题 README 的直接引用，全文 1–42 重读；公告口径，不是固定源码验证 |
| `references/framework-history/2026-09-08/hybrid-state/ollama-recurrent.txt` | 9174／257 | `f8a7bf67f1b62aab5f4835af7c8c2471dca9d72011c272900533e2ccd997cadb` | 126–169、180–248 静态重读；其余仅关键词定位 |
| `references/framework-history/2026-09-08/hybrid-state/ollama-cache-trie.txt` | 8999／323 | `6f23f24b60b29392ab65ec450f6aaaba0eac47101b1062ee349af35843835f92` | 33–105 静态重读；其余仅关键词定位 |
| `references/framework-history/2026-09-08/weight-handoff/sources.json` | 19412／448 | `e82c42b41a381e9b80b6b5ccd325e4ad9ab3c68c41b99ccc71401b9ef1baeabb` | 仅所列 runner、scheduler、vLLM worker、RDT 的身份/状态/哈希/原读取字段；非全部记录审读 |
| `references/framework-history/2026-09-08/weight-handoff/reading-proof.json` | 11009／303 | `1b38364ea8aa2e0885ea4ef66004db63d19f5b5aabafbf95f28966df838167c4` | scope 与 records 开头及原未读声明；非全文记录复核 |
| `references/framework-history/2026-09-08/speculative-execution/sources.json` | 17739／280 | `136df96f9e58194993929edb3b4fdace0a7b4e6bb502bea20378b0b9effacc4d` | 仅 DSpark 文章、SPS、MLX 文章记录；非全部记录审读 |
| `references/framework-history/2026-09-08/hybrid-state/sources.json` | 11691／218 | `d743e9f0ede05ce0c9ab0b99029d731287ba7221756d9be38d5e7d51ae97e0d3` | 仅 unified、Ollama recurrent/trie 记录；非全部记录审读 |
| `references/framework-history/2026-09-08/overlap-placement/sglang-current-tree.json` | 2737538／1 | `dd21468a078217f477f2435720e5bcc939ce5e7529a42d402a284897b48b3e50` | 身份及 DSpark／权重更新／测试路径定位、已读源码 Git blob 比对；树不算源码正文 |
| `references/framework-history/2026-09-08/speculative-execution/vllm-tree.json` | 2025199／1 | `f49822ad3917f1f6b041b5de9d7618f10ed49a835b6ec5a107ce32e890d71586` | 身份及 weight_transfer／worker／测试路径定位、worker Git blob 比对；树不算源码正文 |
| `references/framework-history/2026-09-08/kv-quantization/ollama-src-tree.json` | 370889／1 | `7e445291d122cdd0068166bcc4afc568440842bcea1fed294bfafcc2d0b23e53` | 身份及 MTP／speculate／cache／array 路径定位、recurrent/trie Git blob 比对；树不算源码正文 |
| `references/framework-history/2026-09-08/speculative-execution/vllm-head.json` | 11049／1 | `fc8c5e5cf73ee876ed836e2167dfe468868c64187618e0e616a332fa781f6009` | sha 与 committer date 身份字段 |
| `references/framework-history/2026-09-08/kv-quantization/ollama-commit.json` | 17612／1 | `78d6465637ef84b5d7b4f0ca13571218e49250b03a5296944b130bcc94c8dbcc` | sha 与 committer date 身份字段 |
| `references/framework-history/2026-09-08/weight-handoff/vllm-rdt-2026.html` | 160177／166 | `67eba7ca4cf209a627ddbf60b769d26b8c29a1a06ac4ebf906613a555335018d` | 仅原始字节 SHA-256 比对；本文依据配套既有抽取文本，不宣称新读 HTML/图片 |
| `references/framework-history/2026-09-08/speculative-execution/sglang-dspark-2026.html` | 73743／239 | `9fbfd7842a2c66ab8fae835e6a7634194ef6f28a95df88b989edc90b6da50745` | 原始字节 SHA-256 比对及 paper/PR 链接定位，不宣称全文 DOM 重读 |
| `research/2026-infra-survey/parallel-host-timeline/sglang-current-eagle-worker-v2.py` | 67681／1627 | `425a5cd4bc8945402e43edea2cb1cb86cad9f5fa9feea2ff5b73c32c77b218ad` | 仅函数名与 adaptive/DSpark 相关定位，不新增完整 worker 正文阅读 |

```json
{
  "audit_time_utc": "2026-09-09T07:49:33+00:00",
  "selected_followups": 3,
  "new_paper_body_readings": 0,
  "third_party_code_executed": false,
  "frameworks_run": false,
  "new_downloads": 0,
  "source_git_blobs_checked": 6,
  "source_git_blobs_matching": 6,
  "historical_gaps_not_reopened": [
    "host_scheduler_timeline",
    "omni_dlo_evaluation",
    "pod_selected_backend_callers"
  ],
  "shared_files_modified": false,
  "followup_source_files_are_read": false,
  "report_only_write": "research/2026-infra-survey/parallel-framework-gap-triage.md"
}
```
