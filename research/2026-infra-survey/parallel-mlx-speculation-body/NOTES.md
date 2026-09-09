# Ollama MLX MTP：一轮产出、缓存边界与动态长度

日期：2026-09-09。范围：只读固定静态源码；没有执行 Ollama、MLX、模型、测试或 GPU 实验。本文是备查证据与取舍建议，不是新增书稿章节。

**建议采用，限于现有第 8 章本地推测执行的延伸。** 本次新增的判断不是“另一个引擎也支持 MTP”，而是同样的草稿—验证流程会因缓存所有权、验证行数和计时边界改变收支：Gemma 4 assistant 不另建草稿 KV；四个草稿需要目标前向五行；动态长度以估计产出除以观测成本选择，并仍有探索成本。第 5 章只接回一次主机交接边界，不再复制一套算法介绍。无需增加章节、核心实验或新的模型规模主例。

## 1. 固定身份与可复核范围

实现固定为 [Ollama commit 83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8](https://github.com/ollama/ollama/commit/83ed7d9965b1ee07e0f0b29fd46e47c31f0fcab8)，归档 commit 的 committer 时间为 2026-09-05 00:48:55 UTC。14 份新归档原始 Go 文件均来自该提交的 raw URL，HTTP 200，逐一核对归档 Git tree 的 blob SHA-1；不是只相信文件名或本报告的匹配声明。[sources.json](sources.json) 保留 URL、响应日期、HTTP 状态、响应头、字节数、SHA-256 与 Git blob；[provenance](provenance/reuse.json) 另记复用的 commit/tree 与六月公告原件。原始字节没有规范化换行。

**历史公告与固定实现是两份证据。** [六月公告](https://ollama.com/blog/faster-gemma-4-mlx-mtp)记载 Ollama 0.31、Gemma 4 12B nvfp4、M5 Max 和 Aider polyglot 条件；其实现说明不能自动成为九月代码的逐语句描述。本批未定位六月发布标签的同一实现，不能据九月代码断言这些机制首次出现于六月。公告保留[原始 HTML](provenance/ollama-mtp.html)与[原有文本提取](provenance/ollama-mtp.txt)，全文 42 行已读；HTML 只保全原件，没有重跑原提取器。

读取：14 个源文件，6 个全文、8 个选段，合计 3,578 个不重复源码行；论文正文 0 页、论文图 0 页。测试文件只静态阅读，不能记作测试通过。逐文件范围和段落哈希见 [reading.json](reading.json)，文末列出完整范围。

## 2. 先确定是哪一种 MTP 与哪些请求能走它

入口 [runner.go 59–151](sources/x/mlxrunner/runner.go) 先读模型 manifest 与目标权重，再取外置 draft 或模型内置 SelfDraft，加载相应权重与缓存后建立 speculation。没有 draft 时没有该子系统；[speculate.go 78–89](sources/x/mlxrunner/speculate.go)另分 BlockDraft 与 MTP。本次只追 MTP，不据统一接口声称 DFlash 细节已读。

Gemma assistant 构造要求 draft metadata/config，目标必须是 Gemma 4，词表尺寸必须一致，若配置给出 backbone hidden size 也必须匹配，见 [assistant.go 111–167](sources/x/models/gemma4/assistant.go)。这是源码支持的组合约束；未下载具体 checkpoint manifest/权重，不能推出任意名为 Gemma 4 的旧下载都已携带草稿，或任何 Ollama 后端都走 MLX。

[speculate.go 113–128](sources/x/mlxrunner/speculate.go)对 `Logprobs` 或正的 `TopLogprobs` 将请求的草稿执行停用，仅保留 session 以便草稿缓存对齐。因此不能把此路径的普通生成收益直接挪到需要逐 token 概率的 RL rollout。这里是固定版本的功能边界，不是关于未来支持的断言。

## 3. 一轮究竟算了什么，返回什么，留下什么

设进入验证前目标缓存 offset 为 `b`，已有一个 `current` token 尚未送入目标前向，提议 `k` 个草稿。`current` 是之前已经生成的 token／入口 seed，不是这一轮新返回的 token。[speculate.go 191–258、395–534](sources/x/mlxrunner/speculate.go)把三个计数分开：

1. **提议。** [mtp.go 261–327](sources/x/mlxrunner/mtp.go)串行提出 token，并保留每行实际采样分布；后一草稿使用上一草稿与 hidden。带自身 KV 的通用 MTP 先结清 frontier pair，首步可复用 held hidden；Gemma 的无草稿 KV 路径每步读取目标的既有历史。两者不是相同的容量/起草工作账。
2. **验证。** 目标一次前向输入 `current + k drafts`，`SeqQueryLens = k+1`。第 0 行目标状态预测第一个草稿，最后一行供全接受后的 bonus；没有另一次 base-logits 前向。采样接受率对提议 token 使用 `min(1,p/q)`，取最长接受前缀；第一次拒绝处从归一化的 `max(p−q,0)` 补偿分布采样，全接受则取 bonus。[sample.go 47–126](sources/x/mlxrunner/sample/sample.go)明确这里的 `p/q` 是过滤后的目标/草稿采样分布，含 sparse support 的对齐，不是随手取原始 softmax 值。本批未完整核所有 sampler penalty、grammar 和数值边角，不能从这一段宣布所有选项的分布等价测试已完成。
3. **正常返回。** 若接受 `a` 个草稿且没有终止，返回 `a+1` 个 token（接受草稿加补偿/bonus），目标 KV 留下 `current + a` 个草稿的状态，offset 变成 `b+1+a`。数目相等，token 身份错开一位；返回的最后一个补偿/bonus 尚未写入 KV，留给下一轮当 current。
4. **终止。** 第 `j` 个已接受草稿若是 EOS，返回结果含这 `j` 个草稿并停止追加 bonus；保留 current 和 EOS 之前的 `j−1` 个草稿状态，offset 为 `b+j`，EOS 自己不折入可复用状态。`observed` 截到 EOS，不把终止之后的位置当成拒绝。最终输出上限还由外层 decode 限制。返回 Result 个数、包含 EOS 的计数、用户可见字符串与 API 计费 token 不能直接混用。

自写 [round_accounting.py](round_accounting.py) 只做上述纸笔整数核算；[arithmetic.json](arithmetic.json) 是其结果，不是模拟器或 Ollama 输出。取 `b=100,k=4`：

| 结果 | 目标前向行 | 接受草稿 | 本轮返回 Result（含 EOS） | 保留新增状态 | 新 offset |
|---|---:|---:|---:|---:|---:|
| 首草稿拒绝 | 5 | 0 | 1 | 1 | 101 |
| 接受两个后拒绝 | 5 | 2 | 3 | 3 | 103 |
| 全部接受 | 5 | 4 | 5 | 5 | 105 |
| 第二个已接受草稿为 EOS | 5 | 2 | 2 | 2 | 102 |

这张小账接到现有实验 8-5 的逐轮记录即可：记录实际 `k`、目标 query rows、接受草稿、最终交付 token、KV offset 和完整轮耗时。它不替代 Qwen3-8B/DFlash 的既定基线，也不要求添加一套 Gemma 设备实验。

## 4. 缓存容量不能统一按“目标 KV + 草稿 KV”相加

**Gemma assistant 没有自身 KV。** [assistant.go 272–321](sources/x/models/gemma4/assistant.go)的 `NewCaches()` 返回 nil；Forward 将 target token embedding 与输入 hidden 合并，在目标 full-attention cache 的末位置确定 anchor，读取最后两类目标 cache 的 attention view。`sharedHistories` 是目标历史共享，不是把所有已有 token 再写一遍草稿 KV。它仍有草稿权重、hidden、中间张量、采样分布、目标历史读取与工作区；“无草稿 KV”不能写成“草稿没有内存成本”。[gemma4.go 1173–1191](sources/x/models/gemma4/gemma4.go)还按目标层的共享/滑窗关系建立实际 cache，不能对每层无条件重复计算完整目标 KV。

通用、带自身 KV 的 MTP 则维护 `token[S+1] + target hidden[S]` 的配对；提交后可先缓存待写项，再批量 flush，pending 达到 256 token 时触发 flush。见 [mtp.go 50–114、169–246](sources/x/mlxrunner/mtp.go)。256 是触发阈值；一个较大提交批可先使计数越过阈值，不能把它当成无条件精确峰值上限。此机制对 Gemma nil-KV 分支不应重复记入一份永久草稿 KV。

**逻辑回退不等于释放物理容量，也不总是零复制。** [commitSpeculation 353–381](sources/x/mlxrunner/speculate.go)在拒绝时先关闭无用快照，再优先 live restore，失败才用所需快照。全注意力 [KVCache 128–261](sources/x/mlxrunner/cache/kvcache.go)允许只调 offset；已有容量和被丢弃位置的底层存储没有因 offset 变短自动释放。lazy snapshot 初期是索引/元数据，后续写入威胁旧范围时才可能 materialize，不能算成每个提议都立刻复制全历史。

滑窗 cache 在窗口未填满时可直接回退，**绕回之后**则要有完整边界快照；[RotatingKVCache 377–448](sources/x/mlxrunner/cache/rotating.go)拒绝会留下不完整窗口的 clamp。同一缓存仍为 lazy 的快照可用 slice 重设窗口；较早快照、外部所有权和覆盖情形会走别的路径。它处理多 token append 时可先保留 `W−1` 个旧位置并拼接 `k+1` 行，因此中间逻辑缓冲长度可能达到 `W+k`，不宜把瞬时缓冲也一概写为 `W`。实际物理字节峰值仍需查 allocator 和 trace。

`mlx.Array.Clone` 的已读实现新建 array wrapper 并 set 底层句柄，`Pin` 增加运行时追踪引用；见 [array.go 128–150](sources/x/mlxrunner/mlx/array.go)。它们本身没有证明“完整张量 memcpy”或“主机 page-locked 内存”。底层 MLX ownership/donation、Metal allocator 未进一步展开，书稿不应从方法名猜物理行为。

## 5. 动态长度的目标、分母与代价

[speculate_depth.go](sources/x/mlxrunner/speculate_depth.go)选择的量是

`E(N) / C(N) = [1 + Σ(j=1..N) Π(i=1..j) p_i] / C(N)`。

`p_i` 是**前面位置都已通过时**当前位置的条件接受率，代码只更新真正到达的位置；未提出或未到达的尾部不是拒绝。每位置达到 10 次才信任，未足量位置继承较浅的已信任值，无已知值时先取乐观值 1；搜索只到已信任 frontier 的下一位置。不要把 `accepted/drafted` 总体比例或可变长度情况下全轮分母的 `q_j` 直接当作每个条件 `p_i`。这里沿用 I09 已经澄清的定义，不重开一道题。

`C(N)` 的**调用位置**比 costModel 注释更重要：[speculate.go 131–147](sources/x/mlxrunner/speculate.go)在下一轮开始时收上一轮的 wall time，并只收相邻同深度轮，舍弃形状切换的样本。计时不是单独包住 target Forward，也不是 GPU event 计时；起草、采样、同步、输出处理和主机停顿都有可能影响该边界。cost EWMA 的 alpha=0.3，单次 innovation 限制为旧估计的 ±25%，即一次更新最多挪动旧估计的 7.5%；这是抗异常值处理，不是证明这些时间都已排除。对有 logprobs 而停用草稿的 session 不收这类样本。

估计允许 `N=0` 普通 decode，但要先给不同深度取得同深度 cost 样本，并周期性试探更深一档；试探间隔由 4 轮逐步退避，最大 512 轮。状态跨请求保留。**存在回退选项不等于一切非稳态下整段请求绝不减速**：探测、学习滞后、取样和主机噪声均有成本。不能把六月公告的概括直接用作当前算法的最坏情况保证。

教学数值只为看清选择依据，不重现控制器：设条件概率依次为 `0.8,0.7,0.6,0.5`，无 EOS/输出上限；完整轮时间明确假定为下表。深度 2 最优，尽管深度 4 平均产出更多。

| 草稿 N | 目标行数 | 期望非终止产出 | 假定完整轮 ms | 期望 token/s |
|---|---:|---:|---:|---:|
| 0 | 1 | 1 | 2 | 500 |
| 1 | 2 | 1.8 | 2.5 | 720 |
| 2 | 3 | 2.36 | 3.2 | 737.5 |
| 3 | 4 | 2.696 | 5 | 539.2 |
| 4 | 5 | 2.864 | 7 | 409.142857 |

这些是假定成本与稳态概率，不能标成 Gemma、M5、BF16 或 NVFP4 实测。已读 `speculate_depth_test.go` 是人为成本曲线与结果生成器；其测试名称或注释使用硬件/量化名也不会令这些输入变成 profiling 证据。本批没有执行它们。

计数备查：[speculate_stats.go 48–84](sources/x/mlxrunner/speculate_stats.go)把 `accepted/drafted`、每轮平均接受草稿与估计 expected_tps 分开；expected_tps 是模型估计，不是累计交付 token 除实测请求总时长。`depth_over_time` 当前按 chosen 数组下标分桶，没有时间戳；尽管注释说等时间片，代码支持的是近似等轮数桶。这个小差异只留测量笔记，不为它增正文。

## 6. “单次 GPU 链”与实际主机读取边界

六月公告对中间执行的概括与九月固定源码需要分开。九月 [speculate.go 434](sources/x/mlxrunner/speculate.go)在读取草稿 ID 时无条件调用 `candidates.tokens.Ints()`；[array.go 261–269](sources/x/mlxrunner/mlx/array.go)明确 `Eval(t)`、读取 C 数据并复制成 Go slice。后面还读取接受 mask、补偿/bonus。由此能确认当前路径存在主机取值边界，不能将其描述为提议至验证全过程无 CPU 读取。

同时，[speculate.go 448–462](sources/x/mlxrunner/speculate.go)先为所有可能拒绝点产生补偿采样和 bonus，再统一 eval，确实避免了先取接受点、后启动对应补偿采样的另一轮依赖。最小可采用的解释是“减少串行主机往返”，而非“主机完全消失”。`AsyncEval` 可使部分工作已在进行，MLX 的 Forward 也会构造惰性图；仅凭 Go 调用顺序不能给出真实等待时长、GPU 时间线或加速倍数。未进一步读 MLX/C/Metal 库，也没有 profiler 原始轨迹。

小矩阵内核和整任务加速仍只按六月公告各自条件引用：本批没有核底层内核固定提交、命中 dispatch、原始 benchmark 轨迹或系统级重现。不能把大矩阵内核局部加速与 MTP 总收益相乘。

## 7. 放回现有大纲的最小建议

本次读取时，主大纲 `outlines/08-单实例推理.md:201` 已把 Ollama MLX 保留为延伸；不要恢复成主线模型。`outlines/extensions/08-单实例推理.md:227` 的现有段落位于 **8.3.4 动态预算与模型协同**，可以原位收紧为：

> 以 Ollama 0.31 的 Gemma 4／MLX 公告引出本地推测，再沿固定实现核一轮收支：四个草稿对应五行目标验证，输出、接受草稿与 KV 提交位置分别计数。Gemma assistant 读取目标缓存，不另建草稿 KV；动态长度依条件接受概率与观测轮耗时选择，并保留普通 decode 与探索成本。公告性能只引用其模型、精度、硬件和任务条件，源码版本另列。

**8.2 的选择性快照段（扩写当前第 147 行）**无需再讲一遍 MTP，可只接一句：

> 8.3 的拒绝恢复还要区分全注意力的逻辑回退与已经绕回的滑窗快照；逻辑 offset 变短并不代表物理容量同步释放。

现有实验 8-5 的逐轮记录加一列“target query rows”和一列“提交前/后 cache offset”即可接通纸笔推算；先使用固定基线或本包教学结果。若将来实际跑 MLX，再补模型 manifest、后端、采样/logprobs 设置、完整轮计时与内存观测，不因读完源码将实验标为完成。既有图 8-4 可在备查的本地变体上标出 current、四个草稿、已返回末 token 尚未入 KV 的边界；无需另画一张技术目录图。

第 5 章仅从现有主机/设备依赖处指回这条“先并行准备各拒绝点采样，后一次取结果”的路径，不新建 MTP 小节。提议先后、逐位置快照、EWMA 常数、statistics 命名都留在本笔记，避免扩写变成 API/论文目录。

## 8. 完整、部分读取与未闭合边界

以下行号基于归档 raw 源码，从 1 开始，端点包含。链接目标是完整原件；未列的行没有因为文件下载完成就记成已读。范围哈希按原始 `splitlines(keepends=True)` 片段计算。

| 原件（sources 下） | 已读范围 | 状态 |
|---|---|---|
| x/mlxrunner/mtp.go | 1–332 | 全文 |
| x/mlxrunner/speculate.go | 1–556 | 全文 |
| x/mlxrunner/speculate_depth.go | 1–318 | 全文 |
| x/mlxrunner/speculate_stats.go | 1–85 | 全文 |
| x/mlxrunner/cache/cache.go | 1–150 | 全文 |
| x/mlxrunner/speculate_depth_test.go | 1–298 | 全文静态阅读，未运行 |
| x/mlxrunner/cache/kvcache.go | 1–261 / 共 367 行 | 部分，含完整 Restore，未读后续 Merge/Split 等 |
| x/mlxrunner/cache/rotating.go | 1–448 / 共 514 行 | 部分，含完整 Restore，未读后续 Merge/Split 等 |
| x/mlxrunner/mlx/array.go | 1–275 / 共 307 行 | 部分，Ints 完整，末尾 Floats 起始截段不记完整函数 |
| x/models/gemma4/assistant.go | 105–168、270–326 / 共 403 行 | 部分，构造/Forward/sharedHistories 完整；Unembed 仅起始 |
| x/models/gemma4/gemma4.go | 1–34、1170–1195 / 共 1,544 行 | 部分，注册与 NewCaches；非完整模型数值实现 |
| x/mlxrunner/mtp_test.go | 1–118、220–378、1328–1388 / 共 1,388 行 | 部分，fake 模型/runner 与代表断言；未运行 |
| x/mlxrunner/runner.go | 1–161 / 共 312 行 | 部分，Load/newDraftCaches 完整；logitsWidth 仅起始 |
| x/mlxrunner/sample/sample.go | 1–175 / 共 911 行 | 部分，Distribution 与 residual 完整；Sampler 类型仅起始 |

尚未闭合的条件明确保留：实际模型包/草稿权重兼容矩阵；六月发布源码与本提交之间的精确演进；全部采样/grammar 数值性质；底层 MLX 内核/dispatch 与物理容量峰值；跨请求前缀命中的全部调用链；实际设备上的收益、EOS/截断后的 API token 统计及输出背压影响。它们都不妨碍现有提纲采用上述有限机制，也不应推动本轮无界追源码。

## 9. 复核与交付

本包在代理整理完成阅读记录之后因服务额度限制中断。根任务补写 `verify.py`，核14份源码的SHA-256、固定树Git blob、声明的3578行阅读范围及自写算术。测试源码只读不执行。此核验不证明全部实现判断、实际性能或六月到九月的完整演进。

根任务另读 accept 的第390–535行、Gemma assistant第270–322行和Array.Ints第258–272行，直接确认验证行数、提交边界、无独立草稿KV及主机取值接口。其余范围按代理阅读记录归档，不冒充根任务完整通读。

`manifest.json` 固定本次交付文件字节；`verification.json` 保存自写核验的结果，二者从文件清单中排除以避免自引用。仍待实验的性能与物理容量条件保持在第8节，不把源码归档当作实验完成。
