# 第 6–10 章贯穿案例的一致性审查

2026-09-09；只读审查，未修改大纲、skeleton、案例或计算程序，未提交。先检查了工作目录及其祖先、outlines／case-studies／research 内的 AGENTS.md，未发现适用文件。审查基于当时工作树；用户和其他代理仍在修改，应用建议前须按引文重新定位。

本次保留 **3 项**：两处计量定义需要接通，一处跨章案例的交接尚未闭合。没有把明示的教学假设、容量下界或局部实验当作错误，也没有据此否定已归档的新模型规格。

## 1. 训练期限练习仍把不同 FLOPs 口径都称为 MFU

**位置。** [第 10 章](../../outlines/10-训练系统.md)第 55、59 行；[扩写资料](../../outlines/extensions/10-训练系统.md)第 55 行；[训练期限结果](../../calculations/results/training-deadline-book.md)第 14、22、55–60 行；[业务推算](../../case-studies/inference-training-scenarios.md)第 29、35–45 行。

第 55 行及计算结果已经规定：100B 有效位置按 Qwen3-8B 的实际线性变换和有效因果注意力前反向计算，得到 `5,265,722,561,667,444,768,768` 矩阵 FLOPs；30%／40%／50% 是这个子账相对 BF16 输入、FP32 累加、dense Tensor 峰值的教学效率。第 59 行的实验 10-2 却只说“用 30%、40%、50% MFU 作敏感性输入”。同一组百分比还用于后面的 `6ND` 名义 Dense 情景，读者容易直接沿用公开训练报告的 MFU。

这不是说矩阵工作不能定义一种 MFU，也不是这几组教学结果算错；缺的是让同一个名称绑定同一分子。对同一设备与计时窗口，若两个算法计数相差比例 `r`，相应效率也应相差 `r`，不能把百分比不变地移到另一个工作量上。现有资料已明确警告此事，练习的用词应跟上。

**建议。** 将实验 10-2 的一句改为：“以本题矩阵 FLOPs 口径的 30%／40%／50% 峰值效率作敏感性输入；引用公开 MFU 时先核对算法计数和计时窗口。”同步扩写资料即可。实验 10-10 保留名义 Dense 的粗估，在调用前点明它的 `6ND` 分子；不需要增加新小节或新实验，也不需要删除粗估。

**验收。** 给定同一训练步时和峰值，分别用矩阵子账与 `6ND` 算出对应比例，并能从任一配对的“工作量＋效率”还原相同时间；缺乏同口径测量时继续保留教学效率。

## 2. PD 需求中的输出 token 与 decode 调用尚未统一定义

**位置。** [请求分布案例](../../case-studies/workload-and-provisioning.md)第 17–36 行；[第 9 章](../../outlines/09-分布式推理.md)第 65、69 行；[贯穿请求](../../case-studies/inference-training-scenarios.md)第 7–17 行。影响实验 9-2，并连接案例明确指定的实验 3-2 与资源池准备。

C47 明确“8192 输入／129 输出，首输出来自 prefill，D 仅调用 128 次”，也覆盖仅一个输出时不需要 D 的边界。请求分布案例则设 D 为“有效生成 2048 输出 token/s”，把 256／2048 个交付输出全部计入 D 需求。该案例没有写明 `O−1≈O`，也未定义这里的速率到底是设备 decode 调用率，还是按某种请求分布折算的交付输出率。

因此这里应记为**口径缺口，不是算术错误**：如果其服务单位有意就是交付输出，原有除法成立于该定义；如果要和 C47 共用 decode 调用能力，则每请求应扣除 prefill 已给出的首输出。保留原数作为粗估也合理，但要明说近似，并且不能让它覆盖 `O=1` 的边界。

统一为 2048 decode 调用／秒后，原 4 requests/s、A/B 两类请求、120 秒的输入保持不变，数值如下：

| 项目 | 原交付输出计数 | D 调用计数 |
| --- | ---: | ---: |
| 平均需求，每秒 | 4608 | 4604 |
| 前 60 秒，每秒 | 1740.8 | 1736.8 |
| 后 60 秒，每秒 | 7475.2 | 7471.2 |
| 平均 D 连续容量 | 2.25 | 2.248046875 |
| 前窗／后窗 D 连续容量 | 0.85／3.65 | 0.848046875／3.648046875 |
| 后窗在 3D 下积压 | 79872 | 79632 |
| 假定没有新工作时的排空秒数 | 13 | 12.9609375 |

原数相对 D 调用数的需求高估约为均值 **0.087%**、前窗 **0.230%**、后窗 **0.054%**；排空差 **0.0390625 秒**。在这些输入下，均值选择 2P3D 却无法承受第二窗、2P4D 通过速率必要条件的判断均不改变；P 的工作也不改变。流体队列仍不等于逐请求延迟。

**建议。** 在原案例第 17 行将 D 的资源单位明确为“decode 调用／秒”，用上表更新其阶段计算；同时保留“交付输出数”为业务指标。或者明确说明旧例按 `O≈O−1` 做第一遍粗估，并在与 C47 相连处切回精确计数。不要直接改已封存实测的 output throughput 字段：客户端交付输出、引擎执行位置和设备 decode 调用本来可以是不同计量。

**验收。** 同一请求记录导出 `output_tokens`、`prefill_generated_tokens`、`decode_calls`，普通非推测路径满足后两项之和等于输出数；一个输出的请求不再凭空消耗一次完整 decode。发生推测、多 token 产出或 EOS 时采用实际执行／交付记录，而非强行套用一调用一输出。

## 3. MoE 的容量与通信已有子账，但还不是同一个完整并行方案

**位置。** [第 6 章](../../outlines/06-超节点.md)第 105、117、161、163 行；[第 7 章](../../outlines/07-数据中心网络.md)第 67、73、257 行；[第 9 章](../../outlines/09-分布式推理.md)第 19、33 行；[并行案例](../../case-studies/model-parallelism.md)第 21–25、68–74 行。

现有两个可用结果分别明确了不同条件：

- [Qwen235 八卡容量](../../calculations/results/qwen235-placement-tp2-ep4-pp1-80gb-8192.md)第 3、25、989–996 行：TP2×EP4、同一请求 cohort，attention 和 KV 沿 EP 复制，专家沿 EP 分配并在 TP 内切分。BF16 权重每卡 64,821,419,008 bytes；每请求每卡 KV 788,529,152 bytes。该结果明确不是通信或运行峰值证明。
- [Qwen235 All-to-All](../../calculations/results/all-to-all-qwen235-t64-balanced.md)第 3、9–21 行：8 个专家 rank，每源 64 个 token，每 rank 16 个完整专家；按 assignment 发送，得到 dispatch 29,360,128 bytes。第 6 章又给了基于显式 token 身份的目的端去重变体。

两笔计算各自成立，不能直接将第二笔流量贴到第一笔容量表上：通信组从 8 个专家 rank 换成了 4 个 EP 分组与组内 TP；更关键的是，前者的 attention 在 EP 侧处理同一 cohort，后者按每源 token 派发任务。token 的唯一来源、各 rank 的中间结果以及 combine 去向必须重新定义，否则有重复执行／重复发送或错误省略通信的可能。这里没有证据说明现有程序已经这样错误组合；缺口在于第 7、9 章“复用已经确定的方案”还没有指向一份共享这些条件的 MoE 交接记录。

**建议。** 在既有实验 6-3 内选 Qwen3-235B 的一套八卡候选，明确两种可选组织中的一种：同一 cohort 沿 EP 重复 attention，或 attention 侧分配不同请求再向专家派发。为选中的方案逐 rank 写清 TP／EP 成员、请求和 token 身份、KV 所有者、专家分片、dispatch 来源、combine 终点；沿同一记录生成容量与通信，交给实验 7-3／7-10，随后再作为 9-1／9-2 的服务副本输入。另一套组织保留为条件改变后的对照。优先复用现有 Qwen235 配置与容量结果，不必先扩张到规格／路由接口尚未闭合的模型。

**验收。** 跨章传递的每个候选有同一份模型／精度／请求／布局标识；逻辑 token、token—专家任务、物理执行副本分别守恒，权重和 KV 的复制不会在通信环节突然消失。EP 不自动增加独立请求副本，TP×EP 的乘积也不能替代实际通信组定义。涉及训练 DP 时另标同一参数的梯度同步组，再接第 10 章的优化器分片。

## 已排除的误报与审查范围

Qwen3-8B 的 144 KiB／缓存位置、8192 个已缓存位置的 1.125 GiB，与 Qwen3-235B 的 188 KiB／位置、1.46875 GiB 对齐。Dense 放置结果默认 `history=8192, tokens=1`，容量保留到 8193 个位置，而 PD 快照只交接 8192 个位置；这 **147456 bytes** 的差异已在结果条件中解释，不判为算错。完整 embedding 驻留与 decode 仅取一行的访问量也已在 batch-reuse 结果分别计数。MoE 的 36 MiB 专家 BF16 权重、72 MiB FP32 梯度和全量优化器状态没有按 top-k 错误缩小。

第 9 章已区分 32 层 1 GiB 的教学模型与真实 Qwen3-8B，PD 请求快照与 AF 指定调用的范围也已分别说明；本报告不要求把所有教学例改成同一个尺寸。A100／A800 的 HBM 与 NVLink 没有在主线中混为一谈。A800 的旧案例引用 80GB 型号，而 training-deadline 的缺项是所选 `a800-40gb-active` 的完整 BF16／FP32 峰值口径，本次不将不同型号的资料差异判为硬件事实冲突。

阅读覆盖第 6–10 章的章节正文、实验安排及相关计算说明；case-studies 重点核对 model-parallelism、workload-and-provisioning、inference-training-scenarios、weight-handoff，并按问题选读 chunking-and-state-transfer、resource-sharing-and-placement、expert-dispatch-and-resizing、speculative-execution、rl-state-and-reproducibility、execution-feedback 等。扩写文件按对应小节与关键字段定位，未宣称逐字读完所有扩写文件或所有案例。

计算结果只核对本报告涉及的输入、摘要、范围和代表 rank，未逐项复核 Qwen235 千行结果中的全部专家矩阵；没有重跑 GPU、模型、下载代码或完整测试。数值修正用独立加减乘除复算。除既有原件中的 Lenovo A800 表 2 文本选读外，本次没有新增论文正文阅读或联网规格核验；V4／K3 未重新确认的字段不新增事实断言。

以下为 2026-09-09 05:39:54 UTC 附近读取的文件 SHA256，供并发修改后确认引用适用范围；不是整本书完成核验的证明。

```text
outlines/06-超节点.md
  1a5d4caea0420c89e64360de8856fb504af3325597d8273a15cbf9b18a853ffa
outlines/07-数据中心网络.md
  ca057dbfaa3d482b7846bb5d2a7a53c878dffa8ebc175b123d404bf687dc340e
outlines/08-单实例推理.md
  bd111f9d42d2aec59f3a324a50c94c6ec9cce35db027e9f8b21f20dff60f24ac
outlines/09-分布式推理.md
  3f9f1cb920feaafafe93e90ac73b49a54c1bd788478d2a8352ab01c608d9e818
outlines/10-训练系统.md
  bd0683a7b6a3966a87a51f0b4fbef6ff0be058c8859fe0496df319a840e012f1
case-studies/model-parallelism.md
  4a04e819a34e13a117cd5cd72aebf4006e308ae0d4d5a3df4eab56fec8d77afc
case-studies/workload-and-provisioning.md
  ad09e2390199e98752a962a0be69605a2e7375fff01084bf01b2de36e7753cbe
case-studies/inference-training-scenarios.md
  ef612ab73311fbd563f92d324f0531d3767c1266d68e240e8ac2dc1135d487b9
calculations/results/training-deadline-book.md
  326b39317bf80fadfdefcc311d35d885dfb752a7cb966852f65e64f7599b59fb
calculations/results/qwen235-placement-tp2-ep4-pp1-80gb-8192.md
  7dd9d7ebca8d1bbb0b74357ae72122ed2cfba3530b1e8f984b4d442d85c1fb90
calculations/results/all-to-all-qwen235-t64-balanced.md
  475cb4291a900fc44799100c380fbb2956173370bf537a606180435c8662225d
```
