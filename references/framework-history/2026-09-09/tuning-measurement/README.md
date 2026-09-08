# 自动调优的比较条件与实际计时

2026-09-09。为第 5.3.5、实验 5-6／5-9 补充“候选为什么获胜”这一判断。归档十四份 HTTP 响应（十二份成功、两份 404），从原始 ZIP 另提取三份文本，复用七份已归档来源；[阅读记录](reading.json)有二十一个明确范围。八份文本通读，激活定义只读 `SiluAndMul` 类；未运行下载代码、模型、GPU 或云端实验。正文与数字见[现有优化案例](../../../../case-studies/optimization-evaluation-and-deployment.md)。

## 论文与作者工件

[DarwinGame 作者 v1](https://arxiv.org/pdf/2509.25090v1)的物理页 1–13 已读，14–16 页参考文献未读，七张图页已查看；[正文记录](../../../proceedings/ASPLOS/2025/darwingame-reading.json)保留页码和版本限制。它让不同配置的应用副本在同一云端机器上比赛，以相对次序应对噪声。实验为 Redis、GROMACS、FFmpeg、LAMMPS，主要机器是 32 vCPU 的 AWS m5.8xlarge，其他配置覆盖 m5／c5／r5／i3；这是 CPU 应用配置研究。

同处一台机器可以缩小外界条件差异，但副本也制造了额外争用。论文承认没有一般性能界限；相对排序不能自动推广到独占 GPU、不同并发片段或完整模型服务。表 1 包含持久化／同步、科学计算及输出设置，采用时仍须固定应用语义与质量，不能把论文的等价性表述直接当作所有设置的保证。全局系统参数如何隔离也未由本次工件核实。图 10 的一百次独立调优与图 11 的一个赢家重复一百次回答不同问题；变异系数不等于 P99。

论文链接的概念 DOI 解析到 [Zenodo 具体记录 15097269](https://doi.org/10.5281/zenodo.15097269)。[原始元数据](zenodo-record.json)的 `publication_date=2024-10-30` 与记录创建时间 `2025-03-27` 分别保留，不推断为同一个首次公开时间。[原始 ZIP](darwingame.zip)的 MD5 与元数据一致；仅通读下列三个成员，隐藏检查点和 macOS 元数据未作为正文证据：

| 已读工件 | 与论文的差距 | 对习题的影响 |
| --- | --- | --- |
| [readme](darwingame-readme.txt)、[application_setup](darwingame-application_setup.py.txt) | 应用入口计算的 `workload` 未使用，实际等待由随机数决定；参数空间是示意 ML 配置 | 不能直接复现论文应用或用作真实性能反馈 |
| [main](darwingame-main.py.txt) 的 `play_one_game` | 等待提交的执行完成，未实现论文按进度提前终止的比赛 | 不能据论文的提前停止推算这份代码的搜索成本 |
| `combined_score` | 平均秒数减一致性分数，论文则将两类名次相加 | 原始工件量纲不同；单改时间单位可能改变赢家，不沿用其分数 |
| `run_2player_game` 与决赛调用 | 先执行 A，再执行 B | 不能将此路径当作论文所述同时对比的实证 |

这些差距限定公开工件的使用范围，不由此断言论文全部实验采用了该占位实现。本书只借此补充测量设计与争用条件，不介绍整套赛制，不采用论文加速倍数，也未发现它被当前 vLLM／SGLang 直接采用的证据。

## 三个年份的真实框架测试

版本身份由固定提交及树中叶文件哈希核验，日期由独立 release 字段给出：vLLM v0.6.0 发布于 2024-09-04，v0.9.2 发布于 2025-07-07；2026 行为取样于提交 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`。取样日期不是功能引入日期。

| 入口 | 实际调用与计时范围 | 采用边界 |
| --- | --- | --- |
| vLLM RMSNorm：[2024](vllm-2024-layernorm.py.txt)、[2025](vllm-2025-layernorm.py.txt)、[2026](vllm-2026-layernorm.py.txt) | 都在 Python 循环前后读主机时钟，以设备同步包围迭代；输出平均每次时间 | 包含主机提交与完成等待；不是单个设备内核的纯执行时间。默认形状为 4096×8192，需换成真实模型形状 |
| vLLM [2026 activation benchmark](vllm-2026-activation.py.txt) | custom op 对比 `torch.compile(forward_native)`；调用 `do_bench_cudagraph`，取 0.5／0.2／0.8 分位数 | 变量中的 min／max 对应所传分位数，不能写成真实极值；图重放与上一行计时不同 |
| FlashInfer-Bench [固定 timing](fib-timing.py.txt) | 请求 CUPTI 计时，传 `cold_l2_cache=True, use_cuda_graph=False`，取中位数 | 只核到此调用层，未审计依赖的回退路径。锁只能协调共享该锁的调用，不能排除外部进程占用 GPU |

RMSNorm 的基础计时方式在三个样本中保持；2025 修正所选脚本的 profiler 结束调用，2026 又调整默认配置与同步接口。不能写成“框架由主机计时全面升级到图或 CUPTI”。两个旧 tag 下的 activation 路径返回 [404](vllm-2024-activation.response.txt)／[404](vllm-2025-activation.response.txt)，完整树也没有这个路径；这只说明该文件不存在，不证明当时没有激活优化。

还需核对同名参数的含义。Qwen3-8B 的 [模型配置](../../../outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json)给出中间维度 I=12288；[SiluAndMul 定义](vllm-activation-definition.py.txt)将输入末维一分为二。未做 TP 切分时，gate／up 拼接输入宽度是 2I=24576。上述 benchmark 把名为 `intermediate_size` 的参数直接用作输入宽度，因此填 12288 实际输出 6144。这并不使通用 benchmark 错误，但不能据此称为测过 Qwen3-8B 的完整该层形状；TP 分片时还应使用实际局部宽度。

实验先对齐形状、精度、布局、语义，再分别观察独占内核、实际并发片段与完整请求。冷 L2、图重放、主机提交各有用途，不能把不同条件的成绩排成统一榜单。独立推算覆盖线性时漂下的测量顺序、并发条件下的选择翻转、量纲与 SwiGLU 字节；[校验脚本](../../../../research/2026-infra-survey/verify_tuning_measurement.py)只读归档并运行自行编写的算术。
