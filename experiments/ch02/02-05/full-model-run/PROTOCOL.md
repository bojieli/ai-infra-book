# 原 2-5：完整 V4 自然文本检索观察协议

状态：**带私有偏置别名适配的完整43层模型已实际完成八题，8/8正常stop精确匹配，进程退出0且无残留。** CPU依赖解析与资源读取不计为模型实验完成。

## 范围与不能越过的结论

固定模型为已有缓存 DeepSeek-V4-Flash-0731 revision `7872f01b1d1fe23eabc4c98b48bffcef5a386062`。保持原 `config.json` 的所有字段及 43 个主干层；原 `compress_ratios` 为 46 项，原样保留，不自行改成 43 项。无 `json_model_override_args` 输入；ServerArgs 默认的空字符串对象 `'{}'` 不是截断 override。未启用 speculative/MTP 模式。checkpoint 不修改、不下载、不复制、不做整模型 SHA 或参数账重算。metadata 的 stat 合计只描述磁盘文件，不证明权重内容完整性、RAM 或 VRAM 需求。

相邻 `native-layer-probe/attempt-05` 仅证明四层原生加载和两次合成 token 前向返回。相邻 `expert-preflight` 的原 M8 逐元素门槛仍有 **10/32768 失败，尚未获得严格数值放行**。本批即使检索答对也只能说明此候选、此冻结题集的真实输出观察，不能宣称全数值正确、一般语言质量通过、最小资源需求或生产性能达标。无检索校准本批未加入，不能混入检索分母。

## 冻结输入与评分

`prepared/cases.json` 是执行前冻结的唯一题集；`tokenizer-evidence.json` 保存其 SHA256。8 题固定顺序：短 A early/late、短 B early/late、长 A early/late、长 B early/late。短档目标约512、实际501 tokens；长档目标约2048、实际2036 tokens。各档有 early/late 两个隐藏位置；短档 token offset 91/373，长档300/1697（从完整 prompt 开始计，含系统提示和官方特殊符号；offset 是前缀单独分词长度）。所有偏移、完整原文、问题、唯一预期答案、完整 prompt IDs 均落盘。

A 项目的唯一短语为 `violet lantern`，B 为 `copper meadow`。每个内容家族跨长度和位置保持目标事实及问题不变；位置变体只移动目标段落，干扰段落顺序不变。长档扩展同一固定自然文本档案，使用有语义的句子，不用合成合法 token 代替文本。填充段落数由 tokenizer 距离目标长度一次确定，独立于任何模型输出。不得根据答案、速度、格式错误、超时或截断重新选择长度、位置、题目或输出预算。

原 tokenizer_config 无 chat_template。调用缓存官方 `encoding/encoding_dsv4.py` 的 `encode_messages(messages, thinking_mode="chat")`，再通过原 `AutoTokenizer`、`add_special_tokens=False` 编码；官方编码器生成 BOS 及尾部 `<｜Assistant｜></think>`。不使用记忆拼模板，也不对不存在的 HF chat template 调用 `apply_chat_template`。不设置 ignore_eos 强制输出，不事后剥离 reasoning 伪装 no-thinking。

固定贪心：temperature0、top_p1、top_k1、seed20260909、max_new_tokens32、ignore_eos=false。单并发、禁用 radix cache，无额外 warmup 或自动重复请求。答案只允许前后 whitespace trim，不能忽略大小写、标点、引号或解释。分别记录 exact_match、format_error、finish_reason、truncated、schema_valid；严格成功要求正常 stop、returned、输出ID与schema完整、保存输入及采样匹配冻结数据、完整无重复的八题记录集，并且exact_match。即使截断时文本碰巧吻合，也在 strict_success 中失败；另保留 exact_match 原值。输出原文不能改写。

8题全部进入分母。进程崩溃/资源守护终止后，未执行或未返回题保留为未成功；不伪造 response。每个 response 先原样持久化再评分。模型的格式错误、长度截断和错误答案不能删除。因资源失败而采用不同资源候选，必须新目录、新 session，启动调试记录在成功后按用户要求删除；有实际请求的科学结果完整保留。本包不自动重跑。相同配置重跑也必须预先说明原因，不能取最好结果。

## 候选配置与原生路径

`common.py:CONFIG` 为唯一候选：cpu_offload_gb110、context4096、max_total_tokens4096、swa_full_tokens_ratio1.0、chunked_prefill256、max_running_requests1、mem_fraction_static0.9、禁用 CUDA graph/radix cache、port18325。110 GiB 是已提出的待验候选，**不是最低需求或精确 offload 占用值**。

官方 `create_offloader_from_server_args` 在 cpu_offload_gb>0 时返回 `OffloaderV1`。源码逐参数搬到 CPU，在 forward 时构建 device_state 并 `.to(device, non_blocking=True)`，再 functional_call。预算是在每个参数前检查，可能因参数粒度超出，不宜视作硬 RSS 限额。原安装文件与权重保持只读；在私有进程中显式包装offloader的functional_call，只同步TopKConfig普通字段保存的bias别名与当前已搬运参数，finally恢复。CPU及实际GPU小对照已通过，完整模型检索仍需实际结果。

复用 SG0.5.13.post1 + Torch2.11.0+cu130 私有环境及 CUDA13.0；CCCL overlay 指向该 venv 的 `nvidia/cu13/include/cccl`，不将其他版本 CUDA runtime 头加入 CPATH。仅将已有两个成功预检的 TVM/TileLang 缓存复制到每个新 output 的私有缓存；不是复制权重。额外设置 FlashInfer workspace、Torch extensions、Triton、CUDA、XDG、HF modules、Numba 和临时目录为 output 私有路径。禁止修改共享依赖、原 checkpoint、相邻实验及 calculations。

根据安装源码，DSV4 使用 page256，并将实际 token 预算按页向下对齐；full/SWA/c4/c128 和压缩状态池由实际模型配置及框架建立。4096/ratio1.0 的静态意图不是实测池分配或显存量。实际 `get_server_info()` 和包含 `DSV4 pool sizes:` 的引擎日志必须保留；`score.py` 提取原始池日志行，未出现时标记未观测，不以算式补实测值。

## 资源门槛与生命周期

建议守护阈值是共享主机上的保守试验护栏，不是容量证明：启动 MemAvailable≥140GiB、单卡 free≥80GiB；自身全进程 RSS≤175GiB、GPU≤78GiB；全机 MemAvailable≥24GiB、GPU free≥4GiB。初始化1800秒、每题600秒、shutdown60秒、总7200秒；每秒采样加 `/proc`/nvidia-smi 调用开销。RSS 按进程求和会重复计算共享页，anon 单列；不能等同物理独占内存。采样可能漏瞬时峰值，不是 cgroup 硬限额。门槛不足直接拒绝，不能自动降低门槛或停止其他服务。

root 必须先确认 RL 已结束并检查最新共享状态。仅由 root 按已有用户授权决定是否结束原 vLLM/Fish 来释放资源；本包不包含任何针对现有服务的 stop/kill 命令。OpenROAD 永不操作。不能因 `/proc` 没搜到 verl 就断言其他 session 的 RL 已结束；launch 中的 verl 检查只是附加拒绝条件。

每个候选创建新 session、唯一环境 token。模型子进程先等待 start gate；watchdog 校验 token 和 `/proc/<pid>/stat` birth 后才开 gate。按全机 `/proc` 扫描 token 可发现 reparent/新 session 后的后代；确认 birth 后持有 pidfd，发信号只针对入册时token匹配、当前birth仍确认且持有原pidfd的自身进程；入册后即使同一进程清除环境，仍保留已确认的身份。禁止按服务名、广义 pgrep 或旧进程组杀进程。退出/异常/阈值触发时只 TERM 自身确认进程，最多10秒后 KILL，自身残余和信号明细写入 supervisor。PID 复用不会将 pidfd 指向另一个进程。未授权读取的无关用户进程不会入册；nvidia-smi解析错误等监控异常触发自身退出；操作系统强杀 watchdog 或子进程在第一次采样前主动清除身份等极端情况仍需 root 审核原始日志，不能声称守护是内核级隔离。

## 保存、计时和报告

每次新 output 保存：执行包SHA、候选配置、冻结题集及答案、原 small metadata 哈希、准备证据、私有缓存种子SHA、启动 gate/环境token/birth/affinity、全部 stdout/stderr、真实 ready/server_info、逐题完整输入IDs与原 response（output_ids/text/meta_info.finish_reason）、wall time、失败栈、finally、逐秒 watchdog、前后共享资源、评分及池日志。

初始化时钟从 Engine 构造前至构造返回；请求时钟从请求前requests.json写盘前开始，到generate返回结束，是包含记录开销的应用包围耗时，分别保存。首题按实际顺序报告，包含潜在按需编译，不伪称暖态。CPUoffload 额外开销在 scores 中单列，孤立传输时间及纯增量为 null：当前未加 profiler 或匹配零 offload 对照，无法从 wall time 中可靠扣出。不得将整个请求耗时写成 CPUoffload 耗时，也不得将其填零。共享服务、CPU RSS/anon、MemAvailable、GPU PID显存与利用率均留证；没有独占主机性能结论。

执行后 root 检查 supervisor、ready、八题原始响应、实际池日志和分母，再描述完成程度。无 ready 即初始化未完成；有 ready 无全部响应是部分执行；完整响应不改变数值未放行结论。准备阶段只做真实 CPU 解析/源码与资源核对/语法检查，不运行 mock 或 GPU 训练推理。

## 最终资源配置与记录保留

最终CPUoffload110GiB；启动主存140GiB/GPU80GiB，自身RSS合计175GiB/GPU78GiB，全机可用主存24GiB/GPU4GiB。准备阶段的历史资源快照不代替运行launch.json中的实际护栏。Unix IPC为本任务专用0700短目录，全部后代退出后删除。

只保留cpu110-bias-alias-004完整成功运行；被其替代的启动和兼容排障目录已删除。冻结题目、原始响应和评分不按质量筛选。实际GPU小控制的未适配失败是预登记机制负对照，仍保留。
