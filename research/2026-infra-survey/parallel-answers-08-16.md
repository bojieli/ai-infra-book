# I08–I16 回答路径核对

2026-09-09。本轮沿题表、直接案例和固定配置复算，只写本报告。工作区与父目录、outlines／case-studies／research 的 AGENTS.md 检查沿用本代理上一项任务的结果：未发现适用文件。没有运行框架、模型、实验或下载代码，也没有修改共享大纲、案例和 Git。

发现一处计量定义衔接缺口：I09 的条件接受概率，与固定 vLLM 日志的逐位置累计比例不是同一种分母。已交给根任务，并确认根任务在案例第 32 行补齐。其余 I08–I16 的现有数字、明确近似和资源条件在本轮范围内未发现需要修改的错误；没有为增加问题数量扩展题目。

## I09：日志的逐位置比例不能再次连乘（已修复）

位置：[题表 I09 追问](interview-directions.md)第 85 行、[推测执行案例](../../case-studies/speculative-execution.md)第 28–32 行。类别为公式与实现字段之间的计量定义缺口，**不是现有四请求教学表的算术错误**。

原案例第 28 行定义条件概率 `p_j`，并正确使用 `1+Σ_j Π_{i≤j} p_i`；第 30 行解释 mean acceptance length 和整体 draft acceptance rate，但没有解释固定实现同时输出的 `Per-position acceptance rate`。固定提交 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e` 的 [metrics.py](../../references/framework-history/2026-09-08/speculative-execution/vllm-spec-metrics.py)第 41–49 行对每次 draft 观察加一，并给已接受前缀的各位置计数；第 116–117 行统一除以全部 `num_drafts`。因此其第 j 项是 `q_j = count(a≥j)/drafts`，并非“此前均接受后，第 j 项也接受”的条件概率。

固定每轮都提议 k 个 token，且暂不计 EOS／输出上限／结束裁剪时，`q_j=Π_{i≤j}p_i`，期望产出为 `1+Σ_j q_j`。例如四轮接受长度为 `[0,0,1,2]`，条件概率为 `[0.5,0.5]`，日志累计比例为 `[0.5,0.25]`：应得到 1.75 个 token／轮，把日志值再次连乘会误算为 1.625。此短例只用于说明原公式的输入含义，没有新增题目。

**可变提议长度需要另留边界。**若四轮的提议长度为 `[1,1,2,2]` 且提议均被接受，日志仍为 `q=[1,0.5]`；它正确反映此次策略每轮实际接受 1.5 个草稿 token，却不能证明第二位置在被提议条件下只有 50% 接受率。未提议尾部既不是已测拒绝，也不能用于反推更长草稿的条件概率。自适应选择、请求结束和样本混合都要保留，不能只对聚合比例做除法来判断草稿质量。

最小修改已经落实：案例第 32 行明确 `q` 的全轮数分母、固定 k 下与 `p` 的关系、直接求和以及可变长度的不可推断部分。保留第 50 行附近的完整验证诊断对照（修订后行号相应顺延）；不更改现有 10.057924／9.567031 产出表。该源码只核普通推测日志分支，diffusion 另走第 96–105 行，不将同名底层计数推广为相同算法。

## 其他题目的具体核算

| 题目／直接案例 | 独立复算与判断 | 条件与尚待测量的部分 |
| --- | --- | --- |
| I08，资源共享 | Qwen3-8B 单层 FFN 为 150,994,944 参数、288 MiB BF16 权重；256 行三矩阵工作为 77,309,411,328 FLOPs。两个微批各独立完整读权重且无跨批缓存时是 576 MiB。1.20／1.36／1.16／1.28 ms 的四种时序成立。 | N 和 C 的服务时间以及 0.60 ms 联合窗口都是明示教学输入，不是假设由矩阵 FLOPs 直接得到；没有把静态权重驻留翻倍。NanoFlow 的 GEMM 损失代理不等于可独立分配的物理资源百分比，案例已经指出。 |
| I08／I12，多 NIC | 同一份 1.125 GiB KV 在 40／45／100／70 GB/s 下分别为 30.19899／26.84355／12.07960／17.25657 ms；三 NIC 共用 45 GB/s 接口、直接 40 加中继受限 60 的预算可对上。 | 两端、交换网络、HBM、中继空闲以及必要启动均有条件；不能写为 FuseLink 当前默认集成或真实设备测量。 |
| I09，图计划与边界拷贝 | 36×20=720 μs，一份计划为 20 μs，只减少主机工作 700 μs。2／16 MiB 外部输入额外读写 4／32 MiB，在教学 2 TB/s 下为 2.097152／16.777216 μs；对应图时间 27.097152／41.777216 μs。间接路径 31 μs，相对 40 μs、额外准备 1 秒，111,112 次才严格获益。 | FlashInfer API 明确 plan 不可捕获、wrapper 图模式 batch 固定、部分后端不支持同一图路径；可复用同规格层的辅助结构不等于跨模型或改变任意规格复用。实际收益仍取决于暴露在关键路径的时间。 |
| I09，验证输入／产出 | 四请求完整／紧凑输入 28／14 行，图档位 32／16 行。产出分别为 10.057924／9.567031；5.2／3.6 ms 得 1934.216／2657.509 token/s。仅限制提交却保留 32 行图为 1839.814 token/s。单层 FFN 32／16 行约 9.664／4.832 GFLOPs，补 512 行增 154,618,822,656 FLOPs。 | 另一 DP rank 需 25 行且路径要求统一图档时，本地也落 32 行；这是明确条件，不推广为所有 DP 实现。vLLM 按 batch 选 K 与自适应验证的支持条件已分开，SGLang 成本表的插值钳位不能外推长上下文或争用。 |
| I10，压缩后的任务时间 | 原式明确写近似：0.5+200/50=4.5 秒，0.5+300/60=5.5 秒，增加 22.22%。若首输出归入 TTFT，则精确同口径为 4.48／5.483333 秒；两项近似分别多计 20／16.667 ms。 | 这是已经明示的 `O≈O−1` 近似，**不列为错误**；输出长短导致结论反转仍成立。案例区分 LMDeploy 的性能配置与 Llama-3.1 的自然长度样本，未把论文旧版成绩移给当前 Qwen。 |
| I11，执行方案重配 | 80/(1.2−1.0)=400 步恰好抵消；401 步才严格节省。剩余 1000 步为 1200／1080 秒。相同训练目标、全局 batch、资源和额外切换范围已写明。 | Rubick 的 checkpoint 退出重启与瞬时变形不同，原型 64×A800、最大 30B、历史软件栈及仿真扩展已区分。教学 80 秒没有伪装为当前大模型测量。 |
| I11，成组时间线 | 两个单卡 100 ms 加八卡 100 ms，共 1000 GPU·ms；八卡 300 ms 窗口占 41.6667%。接收 S1 的 L 完成 290 ms；预留整组时 L 完成 200 ms、S1 完成 300 ms；另有不可重叠恢复 40 ms 时 L 为 240 ms。 | 总 GPU 时间、整组连续可用时间与 deadline 已分开；零恢复不是框架保证，短任务填空并未变成普遍的大任务优先。 |
| I12，ring 与物理路径 | 8 rank、每 rank 1 MiB、2 μs／轮、单向有效 50 GB/s 得 64.70016 μs。Qwen 单行 8 KiB 得 28.28672 μs，72 次为 2.03664384 ms；带宽翻倍仅省 10.32192 μs。独立枚举 16 节点前三轮有向路径，递归峰值 4／4／4 MiB、Swing 4／2／2 MiB，全网分别 64／64／64 与 64／32／48 MiB。 | 输入张量字节、每 rank 发送、全网跳数与瓶颈边已分开；没有把前三轮 RS 下界称为完整 all-reduce 时间。Swing 原论文性能来自 SST，不能替代 TPU／NCCL 的实际测量。 |
| I12，通信调优 | 并发汇合为 max(0.44,0.26)=0.44 与 max(0.62,0.20)=0.62 ms。额外搜索 12 ms、每次省 0.18 ms，67 次严格回本；50／100 次净收益 −3／6 ms。 | 案例已说明通信单项目标不保证完整训练最快，历史 AutoCCL 库与新版 NCCL tuner 不等同，零 CTA 的操作／拓扑支持也没有扩大为任意 AllReduce。 |
| I13，TP 行列切分 | Qwen H=4096、FFN=12288，TP4 的 gate／up 各出 `[m,3072]`，down `[3072,4096]`；每 rank 三矩阵参数 37,748,736、BF16 权重 72 MiB。非线性前须组合完整输入维部分和，答案没有声称另一切法数学上不可能。 | 此回答描述普通张量布局；实际 SP、融合、残差与训练反向另外核算。不会把推理副本数当训练梯度归约组。 |
| I14，独立活跃专家 | Qwen235 单专家为 18,874,368 参数、36 MiB BF16；m=1／8／32 时独立均匀路由的活跃期望为 8／51.619907／111.771035。8 token 均匀情景为 1.814762 GiB，集中到同 8 专家为 288 MiB。每卡每层多一个专家，94 层为 3.3046875 GiB。 | 这是单层逻辑载荷与指定路由期望，不是逐卡 HBM 测量；TP、重读、缓存、热点设备与 padding 已另列。CRAFT 的旧 R1／K2 结果与 V4／K3、研究补丁与当前框架能力未混用。 |
| I08／I14，卸载 | 九层 FFN 2.53125 GiB，扣一／两组缓冲后净省 2.25／1.96875 GiB；24 GiB/s 下每前向复制服务 105.46875 ms，四条请求摊销总产出上限 37.9259 token/s，逐请求步间隔下界仍为 105.46875 ms。 | 此处是共享链路稳态工作量，不是 KV 可无条件增加的数量。CPU 专家路径把独立专家数与专家任务数分开，不能将 SGLang／KT 的混合精度结果按 BF16 教学值比较。 |
| I15，图准备与检查点 | 10 秒／0.2 ms=50,000 个执行步抵消，50,001 才严格节省；不是输出 token 总数。112 GB／8 GB/s=14 秒；每 10 秒生成则净增待写 3.2 GB/s。20／40 秒捕获、0.5 秒 staging 的完成点 34.5／54.5 秒；50 秒故障仅第一份可用。 | 正式快照与持久化需存储后端语义；数据是取整 8B 教学模型，非官方 Qwen 全参数精确值。历史启动工具明确 KV profiling 含 compile，分析时减嵌套项；实际可服务时间不能由日志字段求和猜测。 |
| I16，资源池效率 | C=360,000 GPU·s，分配率 350,000/C=35/36；SG=300,000/C=5/6，RG=240,000/300,000=4/5，PG=120,000/240,000=1/2，相乘 1/3。没有错误地将单卡分配时间当 RG 分母。 | MPG 正文物理页 6–7 支持成组 allocated chip-time、checkpoint 保留进展与未优化 HLO 的计算参考。案例明示同型 GPU 教学改编、CPU／带宽主导时低 PG 不等于空闲，且不直接等同框架 MFU。 |

## 章节与证据边界

题表的第 5 章图执行、第 6 章切分和通信、第 8 章压缩／推测执行、第 9 章服务寿命、第 10 章训练有效进展及第 11 章成组分配均有当前落点。第 13 章已整章重写，扩写资料页明确旧细目不是新正文的一一映射；I16 的具体计算应以 10.6.1 和直接案例为入口，第 13 章只承担综合应用，不据旧编号把整段 MPG 重添一次。既有归档 README 的历史章号不在本轮改动范围。

本轮重点复算教学条件并核最容易混淆的固定字段，没有重做所有论文阅读或重新验收实测。新增正文选读只包括 MPG PDF 物理页 3–7 的文本，其中第 6–7 页用于定义核对；图 4–11 未进行视觉核对，生产曲线不作为本轮数值证据。FlashInfer 仅提取指定 wrapper 与 plan 的 API 段落。Rubick、NanoFlow、CRAFT、Swing 等保留案例已经列出的历史条件，不能将本报告写成这些工件全部已复现。

## 输入快照与读取范围

下面保留完整文件哈希和真正读过的范围；源码只按范围静态读取。Markdown 物理行以 1 开始，选读哈希按原始行字节依次拼接（保留换行）。HTML 另记提取方法和段落编号；PDF 另记每张物理页的 `pdftotext -layout` 输出哈希，不写出派生文件。题表和推测案例在审计过程中由根任务修改，封笔快照已包含 I09 第 32 行修正，不能把该快照误作发现前版本。

```json
{
  "time_utc": "2026-09-09T06:23:34.723674+00:00",
  "scope": "I08-I16 and their directly linked case studies; no new model/question",
  "inputs": [
    {
      "path": "research/2026-infra-survey/interview-directions.md",
      "bytes": 28196,
      "sha256": "71b77c87663dec44badf9f684de4b7381e0af76e9399990f44abc733f9884e7a",
      "total_lines": 103,
      "read_mode": "lines",
      "ranges": [
        [
          46,
          54
        ],
        [
          61,
          93
        ]
      ],
      "read_bytes_sha256": "19afd0baf86d98c91130b947c85950efcae332b72fbd410a9c979ea45a541e75"
    },
    {
      "path": "case-studies/resource-sharing-and-placement.md",
      "bytes": 13165,
      "sha256": "cf2a5c9220e7c1ba9ea9e06ff08fe67883c994fc4639fb6e81b2bba3837edbab",
      "total_lines": 94,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          94
        ]
      ],
      "read_bytes_sha256": "cf2a5c9220e7c1ba9ea9e06ff08fe67883c994fc4639fb6e81b2bba3837edbab"
    },
    {
      "path": "case-studies/cache-and-reconfiguration.md",
      "bytes": 7069,
      "sha256": "fa3910e59a27ce8f0123ab17893a05c05d608f9f6c95b6b9c3db60a9c1bff44a",
      "total_lines": 41,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          41
        ]
      ],
      "read_bytes_sha256": "fa3910e59a27ce8f0123ab17893a05c05d608f9f6c95b6b9c3db60a9c1bff44a"
    },
    {
      "path": "case-studies/moe-and-startup.md",
      "bytes": 8312,
      "sha256": "20d135765c244e0315c9e659f9000bb30b8dbffa17c2d4be9f8376dd38cc583a",
      "total_lines": 55,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          55
        ]
      ],
      "read_bytes_sha256": "20d135765c244e0315c9e659f9000bb30b8dbffa17c2d4be9f8376dd38cc583a"
    },
    {
      "path": "case-studies/kernel-and-fleet-efficiency.md",
      "bytes": 7979,
      "sha256": "a32d5f97b29a9adcf6c5bf67a6bd7d067bca163fcad5f7d24e2fa05d34f2cf89",
      "total_lines": 57,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          57
        ]
      ],
      "read_bytes_sha256": "a32d5f97b29a9adcf6c5bf67a6bd7d067bca163fcad5f7d24e2fa05d34f2cf89"
    },
    {
      "path": "case-studies/graph-execution-tradeoffs.md",
      "bytes": 12438,
      "sha256": "4bc2d359494e0c705c755c4edbbb9961c317c93ff5298fc120f8878dc7d64b25",
      "total_lines": 77,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          77
        ]
      ],
      "read_bytes_sha256": "4bc2d359494e0c705c755c4edbbb9961c317c93ff5298fc120f8878dc7d64b25"
    },
    {
      "path": "case-studies/speculative-execution.md",
      "bytes": 9968,
      "sha256": "8d21b579441224dc68249ab46fb6a7364546d4f5cb383753bd4511dc6433afe4",
      "total_lines": 62,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          62
        ]
      ],
      "read_bytes_sha256": "8d21b579441224dc68249ab46fb6a7364546d4f5cb383753bd4511dc6433afe4"
    },
    {
      "path": "case-studies/collective-paths-and-diagnosis.md",
      "bytes": 11125,
      "sha256": "397a0265121ca9e9ba7d1cd585bedbb46acc551560e6025d2ad8383664a2fd42",
      "total_lines": 57,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          57
        ]
      ],
      "read_bytes_sha256": "397a0265121ca9e9ba7d1cd585bedbb46acc551560e6025d2ad8383664a2fd42"
    },
    {
      "path": "case-studies/communication-tuning.md",
      "bytes": 6918,
      "sha256": "7de0ad70659704161e5e03f671d99a21f6b07f31b236caa50b49cc70078b8a5c",
      "total_lines": 37,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          37
        ]
      ],
      "read_bytes_sha256": "7de0ad70659704161e5e03f671d99a21f6b07f31b236caa50b49cc70078b8a5c"
    },
    {
      "path": "case-studies/checkpoint-layout-and-loading.md",
      "bytes": 9605,
      "sha256": "12407751e4e8213e726263f19469f301ce39b8610630f04b3a31737f565eb857",
      "total_lines": 43,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          43
        ]
      ],
      "read_bytes_sha256": "12407751e4e8213e726263f19469f301ce39b8610630f04b3a31737f565eb857"
    },
    {
      "path": "case-studies/weight-offload-execution.md",
      "bytes": 10117,
      "sha256": "e54a28c943ae74a3371217530b685a2e4c0bb41a71f090cec1155a6b16175e79",
      "total_lines": 65,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          65
        ]
      ],
      "read_bytes_sha256": "e54a28c943ae74a3371217530b685a2e4c0bb41a71f090cec1155a6b16175e79"
    },
    {
      "path": "case-studies/network-planning-and-collectives.md",
      "bytes": 12307,
      "sha256": "d3305b9c907f2f3c9d6d32f7cd0b6250478bfd2364d28d6ad6b050bd19d89714",
      "total_lines": 72,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          72
        ]
      ],
      "read_bytes_sha256": "d3305b9c907f2f3c9d6d32f7cd0b6250478bfd2364d28d6ad6b050bd19d89714"
    },
    {
      "path": "references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json",
      "bytes": 728,
      "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30",
      "total_lines": 30,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          30
        ]
      ],
      "read_bytes_sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"
    },
    {
      "path": "references/outline-checks/2026-09-07/scaling-history/qwen3-235b-config.json",
      "bytes": 965,
      "sha256": "0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4",
      "total_lines": 38,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          38
        ]
      ],
      "read_bytes_sha256": "0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4"
    },
    {
      "path": "references/framework-history/2026-09-07/startup/README.md",
      "bytes": 1760,
      "sha256": "4f9b4eda329e15f3e59d68b234bac242c3cf1ae8818b8cd75ebc93539d4c24b0",
      "total_lines": 10,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          10
        ]
      ],
      "read_bytes_sha256": "4f9b4eda329e15f3e59d68b234bac242c3cf1ae8818b8cd75ebc93539d4c24b0"
    },
    {
      "path": "references/framework-history/2026-09-07/startup/profiler-log.py",
      "bytes": 7881,
      "sha256": "ff70b5fa1a9cd4bf337b40f7fc9a304876c3ba85c8dd66f31c214871453105d6",
      "total_lines": 197,
      "read_mode": "lines",
      "ranges": [
        [
          34,
          68
        ],
        [
          138,
          184
        ]
      ],
      "read_bytes_sha256": "5c95d9183b14727cd5a221053a817d536994a3f4b4ce140d0c8dbbba8594d398"
    },
    {
      "path": "references/framework-history/2026-09-08/speculative-execution/README.md",
      "bytes": 3284,
      "sha256": "4f0458dae25d861c51baa415f67567eac125f85170382808a287b8fec7a099ce",
      "total_lines": 21,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          21
        ]
      ],
      "read_bytes_sha256": "4f0458dae25d861c51baa415f67567eac125f85170382808a287b8fec7a099ce"
    },
    {
      "path": "references/framework-history/2026-09-08/speculative-execution/vllm-spec-metrics.py",
      "bytes": 10503,
      "sha256": "c1c6b20bbf0ae3427dc331bbf8032193cf0b1ab9f3fe552257da6e4d51f2f4f6",
      "total_lines": 281,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          137
        ]
      ],
      "read_bytes_sha256": "8066f0d8ee4de989b50175cafd1cd71b4274bd9ac37fa8614c19a5a0567a3d0d"
    },
    {
      "path": "references/framework-history/2026-09-08/speculative-execution/vllm-acceptance_metrics.md",
      "bytes": 4450,
      "sha256": "7cb64046883e47457583ac94be3f0761be14a77701571c5d5760742f9cd49900",
      "total_lines": 100,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          100
        ]
      ],
      "read_bytes_sha256": "7cb64046883e47457583ac94be3f0761be14a77701571c5d5760742f9cd49900"
    },
    {
      "path": "references/framework-history/2026-09-08/speculative-execution/vllm-adaptive_verification.md",
      "bytes": 3291,
      "sha256": "b4a3d52c93d3f2a6979b4bb779b8acab37cb984f5ea09c97549cecbc036d29b6",
      "total_lines": 47,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          47
        ]
      ],
      "read_bytes_sha256": "b4a3d52c93d3f2a6979b4bb779b8acab37cb984f5ea09c97549cecbc036d29b6"
    },
    {
      "path": "references/framework-history/2026-09-08/speculative-execution/sglang-dspark-sps.py",
      "bytes": 5737,
      "sha256": "5bc24190ddc91fad9fd42d723c939b3eb3b32df74d2c3f3e12d247665c424f28",
      "total_lines": 163,
      "read_mode": "lines",
      "ranges": [
        [
          45,
          104
        ]
      ],
      "read_bytes_sha256": "b230ac927a7a1cad738d528cbfedec82c5d0dbfc2ce6208ea1c7ef16a2695420"
    },
    {
      "path": "outlines/06-超节点.md",
      "bytes": 35748,
      "sha256": "1a5d4caea0420c89e64360de8856fb504af3325597d8273a15cbf9b18a853ffa",
      "total_lines": 321,
      "read_mode": "lines",
      "ranges": [
        [
          49,
          61
        ],
        [
          139,
          147
        ]
      ],
      "read_bytes_sha256": "22c46924d7a616a6287774ccca18d55cbc50eff1d21eb67e57bdeef63131f617"
    },
    {
      "path": "outlines/08-单实例推理.md",
      "bytes": 54484,
      "sha256": "bd111f9d42d2aec59f3a324a50c94c6ec9cce35db027e9f8b21f20dff60f24ac",
      "total_lines": 352,
      "read_mode": "lines",
      "ranges": [
        [
          259,
          273
        ]
      ],
      "read_bytes_sha256": "b46fb6b59b629b4a1fab205bffcc78aca5a892bf4cf22aa914088ef3a35427cd"
    },
    {
      "path": "outlines/09-分布式推理.md",
      "bytes": 52998,
      "sha256": "3f9f1cb920feaafafe93e90ac73b49a54c1bd788478d2a8352ab01c608d9e818",
      "total_lines": 351,
      "read_mode": "lines",
      "ranges": [
        [
          275,
          303
        ]
      ],
      "read_bytes_sha256": "60900278d4e40c9bb6c335470d599ed4d18be7f04c8b9624e568206c47825cce"
    },
    {
      "path": "outlines/10-训练系统.md",
      "bytes": 49369,
      "sha256": "15e08513393fc4c784845e5571e7dff5a5bb573c90912f277484e02d2c1f8d4b",
      "total_lines": 343,
      "read_mode": "lines",
      "ranges": [
        [
          283,
          307
        ]
      ],
      "read_bytes_sha256": "2d4eba7bf2233bb317610b27d40d263ea20a0347ca7fe4b99df4b3d44084b6f5"
    },
    {
      "path": "outlines/11-资源调度与运行环境.md",
      "bytes": 33064,
      "sha256": "fa66c655b355db08c63756ec563ff0a76805fddf66293d1b46813ab0585c108f",
      "total_lines": 294,
      "read_mode": "lines",
      "ranges": [
        [
          93,
          114
        ]
      ],
      "read_bytes_sha256": "46689f145c4354ab75b948e8d1531f04d21ae3f283577242e15482075490002f"
    },
    {
      "path": "outlines/13-架构协同设计.md",
      "bytes": 13357,
      "sha256": "3aca24b83365aae6ed1811d067528b880b293a9a5296838db1051a009b7177c0",
      "total_lines": 176,
      "read_mode": "lines",
      "ranges": [
        [
          13,
          31
        ]
      ],
      "read_bytes_sha256": "c12fb288e37bf65a7794e20c14b4f73019cca18cedc7c6496b3e5047f72fa086"
    },
    {
      "path": "outlines/extensions/13-架构协同设计.md",
      "bytes": 13593,
      "sha256": "8a6c3d08f43d6b262f83f506110ef0f6ecccb4bc6ae9eb2c115d64c911447430",
      "total_lines": 209,
      "read_mode": "lines",
      "ranges": [
        [
          1,
          30
        ]
      ],
      "read_bytes_sha256": "9fa8be61b9ecc37098d319a3e165db7ae4efe926d7156c39166c8580c804b2c9"
    }
  ],
  "pdf_text_reading": {
    "path": "references/proceedings/MLSys/2026/papers/mlsys2026-fbe2b2f74a2ece8070d8fb073717bda6.pdf",
    "sha256": "975fd712f9c5d8131ef9e2a285dcd532db8bbe3915ea372c10b2ff3cc9f66800",
    "mode": "pdftotext -layout, stdout only",
    "physical_pages": [
      3,
      4,
      5,
      6,
      7
    ],
    "complete_pdf_read": false,
    "figures_visually_inspected": false,
    "claim_scope": "Only section 3.2 SG/RG/PG text definitions substantiate the audit; figures/captions and production percentages are not used as numeric evidence",
    "page_text_hashes": [
      {
        "physical_page": 3,
        "bytes": 6010,
        "sha256": "7055c61bdcade5a1932e3a9640c14eb0626fa51f957ec32f4b40739fc78b3389"
      },
      {
        "physical_page": 4,
        "bytes": 6018,
        "sha256": "c3fc4a143ff62ce7b1c2780625fc42a8bf94418e1d2b3337a413474373b216f7"
      },
      {
        "physical_page": 5,
        "bytes": 5742,
        "sha256": "6c834e670c6e5a0388f2b3177a558d0f6e0b91785d1f0e4e8eaed3821e5cf64c"
      },
      {
        "physical_page": 6,
        "bytes": 6909,
        "sha256": "ceef6a93ec1946989e3a8ef2ab6f1c3a8a5f60121e2c840f4700dbf8a27f3453"
      },
      {
        "physical_page": 7,
        "bytes": 5708,
        "sha256": "dfc930e09f50742b62ec1cf48d046f3634b631ea693ed86238308e3b06885002"
      }
    ]
  },
  "html_selected_reading": {
    "path": "references/framework-history/2026-09-07/flashinfer/attention.html",
    "sha256": "109ed4d58e36d8194df5a2261971c40156c57e45eca1515c9a228c540a8d01d6",
    "extractor": "BeautifulSoup find(id).find_next_sibling(dd).get_text(newline, strip=True).splitlines()",
    "selectors": [
      {
        "id": "flashinfer.decode.BatchDecodeWithPagedKVCacheWrapper",
        "derived_lines": 1927,
        "ranges": [
          [
            321,
            324
          ],
          [
            411,
            420
          ],
          [
            476,
            518
          ]
        ],
        "selected_utf8_sha256": "f05077129b19bf6dad6645039671e326bfbbb187c8a0b0cf91bb3152ae25dea7"
      },
      {
        "id": "flashinfer.decode.BatchDecodeWithPagedKVCacheWrapper.plan",
        "derived_lines": 308,
        "ranges": [
          [
            225,
            242
          ],
          [
            249,
            259
          ],
          [
            277,
            302
          ]
        ],
        "selected_utf8_sha256": "bf8fc43497217a6d47ec541e3af7e8bc793708976f2452631ca74511899202fc"
      }
    ]
  },
  "fixed_metrics_identity": {
    "source_record": {
      "id": "spec-vllm-spec-metrics",
      "title": "vLLM fixed vllm/v1/spec_decode/metrics.py",
      "file": "references/framework-history/2026-09-08/speculative-execution/vllm-spec-metrics.py",
      "url": "https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/v1/spec_decode/metrics.py",
      "final_url": "https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/v1/spec_decode/metrics.py",
      "http_status": 200,
      "bytes": 10503,
      "sha256": "c1c6b20bbf0ae3427dc331bbf8032193cf0b1ab9f3fe552257da6e4d51f2f4f6",
      "retrieved_at": "2026-09-07T20:28:07.093505+00:00",
      "revision": "537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e",
      "reading_status": "selected_sections_read",
      "reading_scope": "Lines 82–140: ordinary spec-decode log branch, mean acceptance length including one extra token, separate draft acceptance fraction, and diffusion branch separation. No full sampler or counter-production audit."
    },
    "computed_sha256": "c1c6b20bbf0ae3427dc331bbf8032193cf0b1ab9f3fe552257da6e4d51f2f4f6",
    "sha256_match": true,
    "tree_path": "references/framework-history/2026-09-08/speculative-execution/vllm-tree.json",
    "tree_sha256": "f49822ad3917f1f6b041b5de9d7618f10ed49a835b6ec5a107ce32e890d71586",
    "tree_selected_path": "vllm/v1/spec_decode/metrics.py",
    "git_blob_sha1": "a3ccfb29e737da369f2d2e14131c3ab8183e9241",
    "git_blob_match": true,
    "metadata_scope": "one source record and one tree leaf; neither document read in full"
  },
  "concurrent_edit": {
    "case": "case-studies/speculative-execution.md",
    "found_at_lines": [
      28,
      30
    ],
    "root_correction_observed_at_line": 32,
    "status": "corrected_by_root_during_audit",
    "snapshot_includes_root_correction": true
  },
  "not_done": [
    "No framework/model/experiment or downloaded code execution",
    "No new source downloads",
    "No complete acceptance-metric producer/sampler audit",
    "No visual inspection of PDF figures",
    "No acceptance of experiments/ GPU results based solely on README",
    "No shared-file or Git mutation"
  ]
}
```
