# I01–I07 回答路径核对

2026-09-09。只读当前题表、直接引用的案例、配置与相关章节落点。未修改大纲、案例、原始资料或共享计算程序，未运行框架、模型或第三方源码；仅用本地固定配置和独立 Python 标准库算术复核。工作区与父目录、outlines／case-studies／research 均未找到适用的 AGENTS.md。

本轮未发现算术错误。保留两项小范围修正：I01 的 45% 计时分母需要明示，I01 的实验落点仍有已经被后续记录补齐的缺口表述。I02–I07 在下述已查条件内没有必须改数值或改章号的问题；没有为了凑三项增加问题。

## 1. I01：Amdahl 数字正确，先明确 45% 的含义

类别：计量定义缺口，低优先级。位置：[题表](interview-directions.md)第 39 行；对应[第 5 章](../../outlines/05-算子与运行时.md)第 291–305 行。

`1/(0.55+0.45/4)=80/53≈1.509434` 没有算错。但“固定计时范围”仍未说明 45% 是可分解的串行请求时间，还是 profiler 中各 kernel 累计时间的比例。后者可能包含并发重叠，不能直接作为请求墙钟的 Amdahl 分母；“其他 55% 不变”也属于这个教学上限的假设。题表已经要求检查重叠，正文又已明确不能将 kernel 时间总和占比套到请求墙钟，因此这是题表简写需要接回正文的地方，并非缺少整个分析方法。

建议把答案开头改成：“先明确计时分母；若归约是原请求串行时间的 45%，其余 55% 耗时保持不变，四倍局部加速的理想请求加速为约 1.51。若 45% 来自并发 kernel 累计时间，则沿依赖图重算。”随后保留图路径、实际替换、profiler 扰动等检查。

可直接连接已有 C31：[请求依赖图结果](../../calculations/results/request-dag-path-switch.md)第 9–18、40–45 行将 80→60 μs 的实际教学调度、120→75 μs 的串行成本和旧路径错误推算 35 μs 分开，不必新建题或算例。真实 5-9 记录也已在[实验说明](../../experiments/ch05/05-09/README.md)第 63–65 行明示“其余时间固定”及重叠范围。

## 2. I01 的实验落点：旧缺口没有随已补记录收敛

类别：证据状态表述矛盾，非性能算术错误。位置：[第 5 章](../../outlines/05-算子与运行时.md)第 295、305 行；[实验 5-9](../../experiments/ch05/05-09/README.md)第 28、43–75 行。

第 295 行仍写“实验 5-9 同引擎替换前后记录尚缺”；但第 305 行和实验说明第 3、18–20 行已有同一 Qwen3-8B／vLLM 0.23 引擎的 11 对完整请求及实际绑定核对。实验说明第 28 行仍列“同口径 32-token 替换前后完整 Nsight trace”缺失，后文第 45–65 行和第 75 行则明确该批已补齐。本轮只读这些说明及教学结果，未重新审计全部原始 profile，不能据此扩张实际性能结论。

这属于并发编辑中发现的状态差异，不由本轮代替用户验收。根任务先检查下列原始材料；通过后，第 295 行可改为：“本图为教学依赖分析，不将其时长代入真实引擎；实验 5-9 已保存同引擎请求和同口径 trace，稳定收益、其他形状／并发及成本摊销仍待验证。”实验说明第 28 行保留 microbenchmark Graph 与 eager 不能混用的判断，将旧 trace 缺口标为补采前的历史状态并链接后文。保持实验 **partial**，记录存在、哈希一致与测量语义已验收分别表述。

`request-dag-path-switch.md` 的 `actual_measured_request_ns=null` 是该教学 DAG 没有对应实测的正确状态，无须填入实验 5-9 的时长；其末尾“无……记录时不声明”是条件句，本身也不是错误。


### 原始材料的验收入口

本轮补查发现，[请求原始 JSONL](../../experiments/ch05/05-09/results/paired-eager-v1/requests.jsonl)、[完整运行对象](../../experiments/ch05/05-09/results/paired-eager-v1/raw.json)、native／schedule 两份 [SQLite](../../experiments/ch05/05-09/profiles/native.sqlite)／[SQLite](../../experiments/ch05/05-09/profiles/schedule.sqlite) 和同名 `.nsys-rep` 文件实际存在。两份 manifest 的 **35 个文件条目**均独立核对存在、字节数和 SHA-256，全部匹配；明细保存在下方 JSON。此项只能证明材料与封存清单一致，不能证明采集完整、关联正确或收益成立。

[正式请求协议](../../experiments/ch05/05-09/results/paired-eager-v1/protocol.json)声明 11 轮、每模式预热 2 次、并发 1、强制 32 输出、temperature 0、eager、APC 关闭；[引擎配置](../../experiments/ch05/05-09/engine-config.json)固定 Qwen3-8B snapshot `b968826d9c46dd6066d109eabc6255188de91218`、BF16、TRITON_ATTN、12 GiB KV 池。两份 trace 的 run.json 保存同一模型/config 与 32-token 请求事件，command.json 保存 Nsight Systems 2026.4.1.191、cuda/nvtx 采集、fork 跟踪、CUDA profiler API 范围、关闭 CPU sampling。日志第 10 行标记 vLLM 0.23.0、TP/PP/DP 各 1；这些是已定位的实际运行条件，不能扩成框架所有版本的特性。profile worker 与无 profile 请求 worker 不同，必须继续验收其插桩边界。

待根任务检查：JSONL 与 raw 的正式／预热／审计事件是否一一相符；profile 的 7239 输入是否与正式运行一致；两模式 32 个输出是否逐项相同；SQLite 中 CUDA launch 的进程／线程／关联和 NVTX 归属，GPU 活动区间并集与计时窗口；其他服务共存、GPU 实际身份及连续占用；分析器是否由这些原件导出摘要。`summary.json.status=passed`、11 对数量和 README 中“完整”字样不单独当作这些检查已经通过。图表、本轮未读的原始事件／源码内容及用户尚未提交目录均不由本子任务修改。

## 逐题核对结果与单位

| 范围 | 本轮复核结论 | 仍依赖的实际条件 |
| --- | --- | --- |
| I02，5.1／实验 5-1 归约变体 | 扩写资料第 17、39 行明确 Qwen `[M,4096]`；M 是行数，扩大 N 是教学形状变体。拆 N 的 partial buffer、同步、再次归约和浮点顺序已包含，没有把并行度直接当加速比。 | 具体 shape、布局、寄存器占用和归约实现仍需 trace；不是新增缺口。 |
| I03，2.3／8.2／实验 8-3 | `ceil(S_i/P)P` 的第一步计量是 token 槽，再乘每位置字节。Qwen3-8B BF16 为 147,456 byte／位置，即 144 KiB；P=16 的页为 2.25 MiB。第 8 章第 97–103 行已分开逻辑请求总和、物理唯一内容、完整页及实际 HBM 读取。 | 简单独占公式用于共享前；共享后应按物理页引用数计数。正文已有 COW、在途访问与取消完成边界，未发现将存储量冒充读量。 |
| I04，5.2.2／实验 5-3 | 在线 softmax 和分块消除完整中间矩阵写回，并不自动改变精确 dense attention 的渐近矩阵工作。第 5 章第 83–91 行已区分单头抽象缓冲、指定下一层接口、因果有效工作、tile 工作和真实 L2／HBM。 | FA2／FA3／FA4 的特定硬件收益不由此公式推出；本轮没有重新阅读论文正文或验收 GPU 计数。 |
| I05，8.1.4／9.2／实验 8-2、9-2 | 512-token 首／末块为 131,328／4,063,488 个有效配对，比例 30.94152；16 块合计 33,558,528，对应 QK/PV 为 19,793,625,219,072 FLOPs。用 Q 的 32 头，不能换成 KV 的 8 头。 | 配对数、状态字节与实际 HBM 流量已明确分开。外层块数不是内核启动或 HBM 流量的固定倍数。 |
| I05 的 TP／PP 与 PD | 同长 Poisson／FCFS 的两个教学候选：1 request/s 时 133.929／205.556 ms，7 时 562.5／316.667 ms。8K KV 为 1,207,959,552 byte；11 GB/s 时 109.8145 ms，8 requests/s 为 9.663676416 GB/s，平均容量上界约 9.106265 requests/s。 | TP／PP 完全均衡、确定服务及忽略交接已写明，单卡可放下时须加副本候选。第 9 章另用 25 GB/s 得 48.3184 ms，是另一教学带宽，不是与 110 ms 矛盾。平均速率可承接不代表尾延迟达标。 |
| I05 视觉追问 | 已有 Qwen3-VL-4B 固定配置：640² 经 patch 16、merge 2 得 400 位置；最终投影加三组 DeepStack 为 8,192,000 byte／7.8125 MiB；视觉位置 KV 为 58,982,400 byte／56.25 MiB。 | 模型宽度、特征数、EC 与语言 KV 已分开；传输格式和缓存放置由案例明示，EC 命中不自动消除语言 prefill 或跨池字节。未引入新模型。 |
| I06，6.3／6.4／9.4 | 题目刻意未给进程组和 rank 映射，因此不能从 TP=2、DP=8、EP=16 唯一算卡数。第 6 章第 105 行和实验 6-3 已要求 token 所有权、实际目的设备及每卡负载；第 9 章第 175–187 行接分组、padding 和暴露通信。 | 实验 6-5 是通信／计算争用的延伸位置，并非声称仅做它就能得到进程组。没有强行补成一个框架的默认布局；本轮未重查完整 All-to-All 实现。 |
| I07，8.2.2／实验 8-3 | 仅 Q／V、r=16、BF16、36 层得 15,335,424 byte／14.625 MiB；100 套为 1.42822265625 GiB。100×8192 的独立 KV 为 112.5 GiB。基座、工作区、图缓冲另计；两类容量不能互相替代。 | 配套 LoRA 运算式中的 B、B_i 应按当前投影的 token 行数理解，prefill 不能只填请求数；后文 20-token 分组已经提供了这一单位。不同 adapter 的 KV 身份条件已写明。 |
| I07 准入与等待 | 8 槽、6 pinned 后非 pinned 可用 2 槽；loading 也占容量、完成事件后才准入，与固定源码相符。20 行单 adapter 的 2×16 槽利用率 62.5%；[17,1,1,1] 的 5×16 为 25%。另设四空槽后的完成均值 38／35 ms、最晚 38／40 ms、开始执行前平均等待均为 16 ms，均正确。 | 四 adapter 分组并未声明全是冷 adapter，后面的加载例子又明确“另设四个空闲槽”，不把两个不同情景当成容量矛盾。4 ms 为完整加载教学输入；12 GiB/s 下纯载荷为 1.1901855 ms，已作区分。drainer 只给长度准入启发式，未许诺等待上限。 |

当前题表的所有引用小节、实验号均可定位。图执行沿第 5 章第 249–263 行的固定地址／就绪／padding／额外读写，以及第 8 章实验 8-2 的执行策略对照接入，未发现 I01–I07 的图工作被错误落到新章节。此处仅核对这些回答需要的条件，不表示所有扩写资料或实验已全部验收。

## 输入快照与读取证明

下面的 SHA-256 对应封笔时原文件；选读哈希按列出的物理行范围依序拼接原始字节（保留换行），完整读取与选读分开。题表其他行及共享大纲可能继续被根任务更新，应以这里的输入快照识别本轮观察版本。五份准入源码分别复算 SHA-256 并与归档 reading.json 对照，再用 Git blob SHA-1 与该文件记录的固定 tree 叶子核对；全部匹配。不联网刷新“最新版本”，也未执行这些源码。

摘要：完整重读两个主案例、LoRA 版本 README、两份固定模型配置、所需原始准入路径；视觉案例仅 1–40 行。论文阅读范围只引用既有记录，本轮未新读论文 PDF／图，也没有以摘要代替正文声称已核。归约、图与通信的章节只按下列范围选读。

```json
{
  "audit_time_utc": "2026-09-09T06:11:34.025099+00:00",
  "scope": "I01-I07 and directly cited cases/configuration; no new question/model/framework execution",
  "input_snapshots": [
    {
      "path": "research/2026-infra-survey/interview-directions.md",
      "bytes": 28086,
      "sha256": "4959e69402afefedb0a67bd8af5b3c5edb74c67057efd0b4fe8de98d303d620d",
      "total_lines": 103,
      "read_ranges": [
        [
          30,
          60
        ],
        [
          89,
          99
        ]
      ],
      "selected_sha256": "258c5c99df072c0df4349adad6f182f195f61b8085e6a94917b2686c2ef7e32b"
    },
    {
      "path": "case-studies/chunking-and-state-transfer.md",
      "bytes": 10110,
      "sha256": "98bc5a50ad203ad92c770da255583e8510880fccd74c9f3f250595b857e8d9c0",
      "total_lines": 77,
      "read_ranges": [
        [
          1,
          77
        ]
      ],
      "selected_sha256": "98bc5a50ad203ad92c770da255583e8510880fccd74c9f3f250595b857e8d9c0"
    },
    {
      "path": "case-studies/multi-lora-serving.md",
      "bytes": 7185,
      "sha256": "4dd2ece3ba7c12452c7f6c48000cdd3ba216940d81efa01c6547ac1df96300f3",
      "total_lines": 49,
      "read_ranges": [
        [
          1,
          49
        ]
      ],
      "selected_sha256": "4dd2ece3ba7c12452c7f6c48000cdd3ba216940d81efa01c6547ac1df96300f3"
    },
    {
      "path": "case-studies/multimodal-stage-placement.md",
      "bytes": 10158,
      "sha256": "0601d1907cda05096c538ea06cd1945a71750625a1d95756fa62ec513dd12385",
      "total_lines": 66,
      "read_ranges": [
        [
          1,
          40
        ]
      ],
      "selected_sha256": "716c1d625fe82f14900800efc93738ee312a7cd2dbc5aef837535b8e18b7ccf6"
    },
    {
      "path": "references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json",
      "bytes": 728,
      "sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30",
      "total_lines": 30,
      "read_ranges": [
        [
          1,
          30
        ]
      ],
      "selected_sha256": "f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30"
    },
    {
      "path": "references/framework-history/2026-09-08/multimodal-execution/qwen3-vl4-config.json",
      "bytes": 1505,
      "sha256": "edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d",
      "total_lines": 63,
      "read_ranges": [
        [
          1,
          63
        ]
      ],
      "selected_sha256": "edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/README.md",
      "bytes": 6698,
      "sha256": "68e7f1a785bd9c736568c7b39d4dd58b2a912998ef929ac51eee0d0fc2470cf8",
      "total_lines": 36,
      "read_ranges": [
        [
          1,
          36
        ]
      ],
      "selected_sha256": "68e7f1a785bd9c736568c7b39d4dd58b2a912998ef929ac51eee0d0fc2470cf8"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/vllm-current-scheduler.py.txt",
      "bytes": 149485,
      "sha256": "4bafc9c06bc5e2add085e3b3df658e3bf52c47006706c3950ce646e65788d3fd",
      "total_lines": 3181,
      "read_ranges": [
        [
          809,
          877
        ]
      ],
      "selected_sha256": "35ed7c560433cc524d7ab536482a8699c7cc8fecfa0275b6660c0d2b104be8c6"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_manager.py.txt",
      "bytes": 49030,
      "sha256": "9c7adb1f32978f3facccb2a2d17e488a7ea9e45cd0ed9ca025514b48f68546f2",
      "total_lines": 1113,
      "read_ranges": [
        [
          366,
          426
        ]
      ],
      "selected_sha256": "7fd986c2fc314a72927b10a100a494d349c6880b98fe1c7ba4af76473abada08"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_overlap_loader.py.txt",
      "bytes": 3555,
      "sha256": "d567ebd9865f224a97eaaa70c4bb12f27017552a4d2fcced7d64e72c7966d12c",
      "total_lines": 95,
      "read_ranges": [
        [
          1,
          95
        ]
      ],
      "selected_sha256": "d567ebd9865f224a97eaaa70c4bb12f27017552a4d2fcced7d64e72c7966d12c"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_drainer.py.txt",
      "bytes": 6904,
      "sha256": "9a7e7fee82016a26850ec805638081cd2561ed7ef854020956997a92d06fa8a6",
      "total_lines": 191,
      "read_ranges": [
        [
          1,
          191
        ]
      ],
      "selected_sha256": "9a7e7fee82016a26850ec805638081cd2561ed7ef854020956997a92d06fa8a6"
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-scheduler-admission.py.txt",
      "bytes": 250712,
      "sha256": "38336b27a7d3ef31c20edc7e91aa5d44cd7f085d0dae85001f65112e899ce5a4",
      "total_lines": 5805,
      "read_ranges": [
        [
          3995,
          4028
        ]
      ],
      "selected_sha256": "5769603b9f22d557580078528095bce79154a8bee1c6c3e34d8153ab75b11367"
    },
    {
      "path": "references/interviews/2026-09-08/fourth-pass/README.md",
      "bytes": 3975,
      "sha256": "8b518c2f98201ea6eb2b0d62da64f1a47532253a0eaf7052efe2cbe584525cc9",
      "total_lines": 16,
      "read_ranges": [
        [
          1,
          16
        ]
      ],
      "selected_sha256": "8b518c2f98201ea6eb2b0d62da64f1a47532253a0eaf7052efe2cbe584525cc9"
    },
    {
      "path": "outlines/05-算子与运行时.md",
      "bytes": 51015,
      "sha256": "c6b49e705243e90ae37158f5eafed3afffffd1d1e0ce4d554ae37f19ce9d4b7c",
      "total_lines": 349,
      "read_ranges": [
        [
          79,
          95
        ],
        [
          187,
          201
        ],
        [
          235,
          277
        ],
        [
          291,
          309
        ]
      ],
      "selected_sha256": "652c9cafebac981f93a277aead664acaf98490e59021ae643cf286a985ac187a"
    },
    {
      "path": "outlines/extensions/05-算子与运行时.md",
      "bytes": 39602,
      "sha256": "d8dbc015145ade1f19a8bb32dcf2d6e247740b3e84163d2e162e1d9fb67e5fea",
      "total_lines": 359,
      "read_ranges": [
        [
          9,
          43
        ],
        [
          186,
          212
        ]
      ],
      "selected_sha256": "250bcc35f8a52dfac44664ca7608225b7f3889cbf55fa9eedf406dbff8f66f54"
    },
    {
      "path": "outlines/06-超节点.md",
      "bytes": 35748,
      "sha256": "1a5d4caea0420c89e64360de8856fb504af3325597d8273a15cbf9b18a853ffa",
      "total_lines": 321,
      "read_ranges": [
        [
          97,
          137
        ],
        [
          171,
          187
        ]
      ],
      "selected_sha256": "482738c9c8639ea2abe7773cf7c0c4c4cae66209dc3d3353e2caeabc29b0e6f9"
    },
    {
      "path": "outlines/08-单实例推理.md",
      "bytes": 54484,
      "sha256": "bd111f9d42d2aec59f3a324a50c94c6ec9cce35db027e9f8b21f20dff60f24ac",
      "total_lines": 352,
      "read_ranges": [
        [
          75,
          117
        ]
      ],
      "selected_sha256": "fbee956d5e3ce126d99179e6a7dcd2cd5f57e41d211f271ff3009605d116beb3"
    },
    {
      "path": "outlines/09-分布式推理.md",
      "bytes": 52998,
      "sha256": "3f9f1cb920feaafafe93e90ac73b49a54c1bd788478d2a8352ab01c608d9e818",
      "total_lines": 351,
      "read_ranges": [
        [
          43,
          73
        ],
        [
          159,
          189
        ]
      ],
      "selected_sha256": "0ad78c2aa6f90b36c8a6f11973d9cd599e6e7fa6c6ec37f1514502deb08eb538"
    },
    {
      "path": "experiments/ch05/05-09/README.md",
      "bytes": 7371,
      "sha256": "84faec3de675a49eba17e845d503bd5c72f194829ff5a05076bb6193c2d1433f",
      "total_lines": 75,
      "read_ranges": [
        [
          1,
          75
        ]
      ],
      "selected_sha256": "84faec3de675a49eba17e845d503bd5c72f194829ff5a05076bb6193c2d1433f"
    },
    {
      "path": "calculations/results/request-dag-path-switch.md",
      "bytes": 2810,
      "sha256": "857bb768a92d59f8789d822f9a4bd4d5344b63d2f95eeb0cfe7fd145ca0b9899",
      "total_lines": 48,
      "read_ranges": [
        [
          1,
          48
        ]
      ],
      "selected_sha256": "857bb768a92d59f8789d822f9a4bd4d5344b63d2f95eeb0cfe7fd145ca0b9899"
    }
  ],
  "version_identity_metadata": {
    "path": "references/framework-history/2026-09-09/lora-admission/reading.json",
    "sha256": "38e64af050cc85b32d91e94d90ed509c211a1d4ab14e84943e81df74a91ea928",
    "read_mode": "selected scopes and tree_entries for five source files; other metadata not fully read"
  },
  "fixed_source_identity_checks": [
    {
      "path": "references/framework-history/2026-09-09/lora-admission/vllm-current-scheduler.py.txt",
      "commit": "537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e",
      "source_path": "vllm/v1/core/sched/scheduler.py",
      "sha256_matches_reading": true,
      "git_blob_sha1": "b59fe6a9ed8d985bf8fbb8c1a664be82a520501b",
      "git_blob_matches_recorded_tree": true
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_manager.py.txt",
      "commit": "c99d906effa8bd05573995127f0d4a0984c5a96a",
      "source_path": "python/sglang/srt/lora/lora_manager.py",
      "sha256_matches_reading": true,
      "git_blob_sha1": "564a0aa1d413b31503579d00a306d709f49e60db",
      "git_blob_matches_recorded_tree": true
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_overlap_loader.py.txt",
      "commit": "c99d906effa8bd05573995127f0d4a0984c5a96a",
      "source_path": "python/sglang/srt/lora/lora_overlap_loader.py",
      "sha256_matches_reading": true,
      "git_blob_sha1": "9e9d725e1c4462f2c7e9a8875b32fba3112df4ff",
      "git_blob_matches_recorded_tree": true
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-lora_drainer.py.txt",
      "commit": "c99d906effa8bd05573995127f0d4a0984c5a96a",
      "source_path": "python/sglang/srt/lora/lora_drainer.py",
      "sha256_matches_reading": true,
      "git_blob_sha1": "6af2f025e9c6cca5aed7195abd6dc2bdb9d69dbf",
      "git_blob_matches_recorded_tree": true
    },
    {
      "path": "references/framework-history/2026-09-09/lora-admission/sglang-scheduler-admission.py.txt",
      "commit": "c99d906effa8bd05573995127f0d4a0984c5a96a",
      "source_path": "python/sglang/srt/managers/scheduler.py",
      "sha256_matches_reading": true,
      "git_blob_sha1": "85b9c203c950b8acf12e3c77a4da95ecfe7750e2",
      "git_blob_matches_recorded_tree": true
    }
  ],
  "stale_claims_at_snapshot": {
    "outline_record_missing": true,
    "experiment_trace_missing": true
  },
  "experiment_5_9_raw_locator": {
    "time_utc": "2026-09-09T06:13:28.199378+00:00",
    "file_integrity_only": true,
    "semantic_trace_audit": false,
    "summary_passed_not_trusted_as_independent_acceptance": true,
    "manifest_checks": [
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/analyze.py",
        "exists": true,
        "bytes": 3269,
        "sha256": "4d6df3d1e6b5af21168de22a5dc9f443efe58c27079b51c321a5186335e0805a",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/candidate.py",
        "exists": true,
        "bytes": 545,
        "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/engine-config.json",
        "exists": true,
        "bytes": 607,
        "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/input.json",
        "exists": true,
        "bytes": 68255,
        "sha256": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/paired-eager-v1.log",
        "exists": true,
        "bytes": 11585,
        "sha256": "7517b3297a57579f22a5c26afe2585cf51eaa10214336c5b9a37b83c3ec4e36b",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/plot.py",
        "exists": true,
        "bytes": 1424,
        "sha256": "ccf4260bae9dd547b7d85f66f4e499133f9d8423623bb9343ec112ab27a23721",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/replacement_worker.py",
        "exists": true,
        "bytes": 1365,
        "sha256": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/comparison.png",
        "exists": true,
        "bytes": 177410,
        "sha256": "7af75134bfaee829bb988e140dc123e4a0038c5f030b04214071518959ef9c75",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/comparison.svg",
        "exists": true,
        "bytes": 90596,
        "sha256": "a7c557bb8f3f160621a04c6a61947301eca86dd365162425576d67ae04aed7fe",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/paired-eager-v1/gpu-activity.log",
        "exists": true,
        "bytes": 15138,
        "sha256": "dfe877a611a9d80d6e71c2fb459f07330d3a7878ec4d6cfce82294df25f5141f",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/paired-eager-v1/protocol.json",
        "exists": true,
        "bytes": 454,
        "sha256": "a0bf0745d209729586d85d7c99ab96bfe9ba37bc919b442bec0355e005ad6039",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/paired-eager-v1/raw.json",
        "exists": true,
        "bytes": 275157,
        "sha256": "7fa6f902e2329b082de9ebac2eb031689d9699bf0d7ac20259e99f107cf425ca",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/paired-eager-v1/requests.jsonl",
        "exists": true,
        "bytes": 47410,
        "sha256": "55e2f8dab56782725d8f1d48ed5116e56007d649b8ce34eefa77d904f4b3fb58",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/results/summary.json",
        "exists": true,
        "bytes": 2767,
        "sha256": "f133e9a7421a805d4232d10ecbd381ce0b567a3dc7332a6de4d99e8354c8b160",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/run.py",
        "exists": true,
        "bytes": 4336,
        "sha256": "4f71b05db103f7420a92eb2dc4fb53d11018203e82881c63c2d853f34ef3a0a8",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/results/manifest.json",
        "path": "experiments/ch05/05-09/selection-provenance.json",
        "exists": true,
        "bytes": 602,
        "sha256": "a5639c6b7a2685d470026df61e2e4184ee79a4733c245b3651f2d1714f276277",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/analyze_profiles.py",
        "exists": true,
        "bytes": 6125,
        "sha256": "0a742d7596e4b7ebb39a876da27873240cdddc88031ffd4a3b813de7d06c2890",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/collect-profiles.log",
        "exists": true,
        "bytes": 16288,
        "sha256": "ad190619ae1cb898ccb73c133439de6647e99cdf3e819877ffec2ba94f4bafa5",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/collect_profiles.py",
        "exists": true,
        "bytes": 977,
        "sha256": "80f6a6259cee3c341c5f63c44b0903d82a766026c17db95bbb2a208c6f8aa2e8",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/plot_profiles.py",
        "exists": true,
        "bytes": 1336,
        "sha256": "66f7dec05c893eead4d599c85a0a714986a6d71dbaeb011bb27b01ae38ba6d53",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profile_run.py",
        "exists": true,
        "bytes": 2062,
        "sha256": "398328f90be2a099a31fd8bfed981a90e45dc5cdd28227418d73aeb0c348a7b6",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/analysis.json",
        "exists": true,
        "bytes": 15129175,
        "sha256": "1c0b0783360f51a6a72db855ddb8032b70e2998fc298d8882907a32cb71fdc9b",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/comparison.png",
        "exists": true,
        "bytes": 82610,
        "sha256": "63cd9bbe10a917cf4b1ca3ae986778ef2738b06f10579c8950a16a736ab0eccf",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/comparison.svg",
        "exists": true,
        "bytes": 69258,
        "sha256": "9fc888cb9996e093b4136677989acc32215eefba2fd712db22ac8fcb339d4825",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/native/command.json",
        "exists": true,
        "bytes": 733,
        "sha256": "cf1e90e81f8dbabfd61bf6382934296cad76b91f31056a4856fb61b5a47ff250",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/native/run.json",
        "exists": true,
        "bytes": 12079,
        "sha256": "b9a18c3ec5d83e0edcf1b0766434929ef8c5f4bd7bffaf3307f56dbec05a6575",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/native.log",
        "exists": true,
        "bytes": 11422,
        "sha256": "f38508bf2983ff2d815bb6d0b15620b3eb58dec0771101b8df39327828523535",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/native.nsys-rep",
        "exists": true,
        "bytes": 1200812,
        "sha256": "323074193d287221c04253a0f756bcc5ca5dffe814f632485863795b19f5c47e",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/native.sqlite",
        "exists": true,
        "bytes": 3215360,
        "sha256": "2af0ce8efbec1167c6383cbe87f6674ca37b251fe929b36182c866707671f67a",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/schedule/command.json",
        "exists": true,
        "bytes": 739,
        "sha256": "a79e66efb80c23d6a6081cbaef40aba9f7a20aab2624e56ca09adbb45e316064",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/schedule/run.json",
        "exists": true,
        "bytes": 10352,
        "sha256": "a63f208e7b3b6afc2c2b3d625f9a13e8eb7d6cdc0b10e75df8419fe3c7d05111",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/schedule.log",
        "exists": true,
        "bytes": 11609,
        "sha256": "a5c598c0a52b73b91a62252b3433c315dff3c8fcc1a9ef336e80aa36abc9193d",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/schedule.nsys-rep",
        "exists": true,
        "bytes": 1200145,
        "sha256": "6fa7be3ede58bd406496f9d1468bdc8c49419006d8ae24dd4eae70ef68f5647c",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/profiles/schedule.sqlite",
        "exists": true,
        "bytes": 3174400,
        "sha256": "8664c28e5b3090760a2435352fb795e26e9fe1f0e35f9aae46ba3a31dc9cee2e",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      },
      {
        "manifest": "experiments/ch05/05-09/profiles/manifest.json",
        "path": "experiments/ch05/05-09/trace_worker.py",
        "exists": true,
        "bytes": 786,
        "sha256": "1753509eb77c0417665c8601f867af895b9f09822318cd3ba04c4542a51ae8cb",
        "matches_recorded_sha256": true,
        "content_read": "hash_only unless separately listed below"
      }
    ],
    "selected_reads": [
      {
        "path": "experiments/ch05/05-09/results/manifest.json",
        "sha256": "7d3a59c8be862012233fd22d3f12fd9dd277d326fcfb53196881fe93f842b59e",
        "mode": "json_complete",
        "keys": [
          "files"
        ]
      },
      {
        "path": "experiments/ch05/05-09/profiles/manifest.json",
        "sha256": "6873c148072ba41d756096ea66bc572e0691d849bd7adbe3e8e73985af06ba2d",
        "mode": "json_complete",
        "keys": [
          "files"
        ]
      },
      {
        "path": "experiments/ch05/05-09/engine-config.json",
        "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
        "mode": "json_complete",
        "keys": [
          "model",
          "dtype",
          "kv_cache_dtype",
          "calculate_kv_scales",
          "max_model_len",
          "max_num_seqs",
          "max_num_batched_tokens",
          "enable_chunked_prefill",
          "enable_prefix_caching",
          "enforce_eager",
          "async_scheduling",
          "gpu_memory_utilization",
          "kv_cache_memory_bytes",
          "seed",
          "attention_backend",
          "worker_extension_cls"
        ]
      },
      {
        "path": "experiments/ch05/05-09/results/paired-eager-v1/protocol.json",
        "sha256": "a0bf0745d209729586d85d7c99ab96bfe9ba37bc919b442bec0355e005ad6039",
        "mode": "json_complete",
        "keys": [
          "trials",
          "warmups_per_mode",
          "max_tokens",
          "ignore_eos",
          "temperature",
          "concurrency",
          "seed",
          "enforce_eager",
          "enable_prefix_caching",
          "measurement",
          "quality"
        ]
      },
      {
        "path": "experiments/ch05/05-09/profiles/native/command.json",
        "sha256": "cf1e90e81f8dbabfd61bf6382934296cad76b91f31056a4856fb61b5a47ff250",
        "mode": "json_complete",
        "keys": [
          "command",
          "version"
        ]
      },
      {
        "path": "experiments/ch05/05-09/profiles/schedule/command.json",
        "sha256": "a79e66efb80c23d6a6081cbaef40aba9f7a20aab2624e56ca09adbb45e316064",
        "mode": "json_complete",
        "keys": [
          "command",
          "version"
        ]
      },
      {
        "path": "experiments/ch05/05-09/results/summary.json",
        "sha256": "f133e9a7421a805d4232d10ecbd381ce0b567a3dc7332a6de4d99e8354c8b160",
        "mode": "json_complete",
        "keys": [
          "status",
          "rows",
          "pairs",
          "matched_output_pairs",
          "positive_ttft_pairs",
          "positive_latency_pairs",
          "paired_median_ttft_saving_ms",
          "paired_median_latency_saving_ms",
          "raw_sha256",
          "scope"
        ]
      },
      {
        "path": "experiments/ch05/05-09/profiles/native/run.json",
        "sha256": "b9a18c3ec5d83e0edcf1b0766434929ef8c5f4bd7bffaf3307f56dbec05a6575",
        "mode": "selected_json_keys",
        "keys": [
          "mode",
          "config",
          "source_hashes",
          "installed",
          "request",
          "steps"
        ],
        "excluded": [
          "switch list was previewed only; no full method-binding audit"
        ]
      },
      {
        "path": "experiments/ch05/05-09/profiles/schedule/run.json",
        "sha256": "a63f208e7b3b6afc2c2b3d625f9a13e8eb7d6cdc0b10e75df8419fe3c7d05111",
        "mode": "selected_json_keys",
        "keys": [
          "mode",
          "config",
          "source_hashes",
          "installed",
          "request",
          "steps"
        ],
        "excluded": [
          "switch list was previewed only; no full method-binding audit"
        ]
      },
      {
        "path": "experiments/ch05/05-09/results/paired-eager-v1/raw.json",
        "sha256": "7fa6f902e2329b082de9ebac2eb031689d9699bf0d7ac20259e99f107cf425ca",
        "mode": "selected_json_keys",
        "keys": [
          "config",
          "protocol",
          "source_hashes",
          "status",
          "engine_startup_s",
          "installed",
          "elapsed_s"
        ],
        "excluded": [
          "requests",
          "audits",
          "switches (preview only)"
        ]
      },
      {
        "path": "experiments/ch05/05-09/paired-eager-v1.log",
        "sha256": "7517b3297a57579f22a5c26afe2585cf51eaa10214336c5b9a37b83c3ec4e36b",
        "mode": "matching_lines",
        "lines": [
          5,
          10,
          19,
          37
        ],
        "purpose": "vLLM 0.23.0, eager, DP/TP/PP and configuration identity; not full runtime log audit"
      },
      {
        "path": "experiments/ch05/05-09/profiles/native.log",
        "sha256": "f38508bf2983ff2d815bb6d0b15620b3eb58dec0771101b8df39327828523535",
        "mode": "matching_lines",
        "lines": [
          5,
          10,
          19,
          37
        ],
        "purpose": "vLLM 0.23.0, eager, DP/TP/PP and configuration identity; not full runtime log audit"
      }
    ],
    "unread_raw_material": [
      "requests.jsonl token/events contents",
      "raw.json requests/audits/switches contents",
      "SQLite GPU events and correlation relationships",
      "nsys-rep visual timeline",
      "gpu-activity.log full co-tenancy samples",
      "analyzer/collector implementation"
    ]
  }
}
```
