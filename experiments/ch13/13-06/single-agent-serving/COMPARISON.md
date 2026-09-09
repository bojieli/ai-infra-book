# 24×7 Agent：比较 GPU 卡型与官方 API

完整计算见 [COMPARISON-RESULTS.md](COMPARISON-RESULTS.md)，机器可读记录见 [comparison.json](comparison.json)。这是对原 [自建估算](README.md)的扩展，仍只研究 DeepSeek V4 Flash 与 Kimi K3、实际占用 200K／1M 的历史。所有资源效率是分析情景，未做收费租卡或 API 性能实测。

从仓库根目录执行：

```sh
python3 experiments/ch13/13-06/single-agent-serving/compare.py
python3 -m unittest discover -s experiments/ch13/13-06/single-agent-serving -p 'test_*.py'
```

脚本读取冻结的 [comparison-manifest.json](comparison-manifest.json) 与原模型快照，离线生成 2,016 个 GPU 情景及 96 个 API 输入情景。原 B200 基线仍可由 `run.py` 单独复现。

## 负载没有峰谷，API 费率仍可能有峰谷

假定池内所有员工始终有工作，工具等待为零，不因夜间或周末闲置 GPU，也不通过把任务挪到便宜时段获得折扣。每名员工都是一条串行轨迹，共租者是其他独立员工。持续有任务仍受显存容量、串行依赖和内核效率限制，所以不把它直接当成 100% 的 GPU 硬件利用率。

[DeepSeek 官方计价页](https://api-docs.deepseek.com/quick_start/pricing/)的 V4 Flash 每百万 token 单价：缓存命中输入谷／峰 **$0.007／$0.014**，未命中输入 **$0.22／$0.44**，输出 **$0.66／$1.32**。峰时为周一至周五 UTC 01:00–04:00、06:00–10:00。按 2026-09-09 00:00 UTC 起 30 天逐小时积分，154 小时为峰时、566 小时为谷时。相同 token 速率下的平均单价分别为 **$0.008497／$0.267056／$0.801167**；不是只取谷价，也不是假设客户负载有高峰。

[Kimi K3 官方计价页](https://platform.kimi.ai/docs/pricing/chat-k3)为缓存命中输入 **$0.30**、未命中输入 **$3**、输出 **$15** 每百万 token，200K 与 1M 不另设长上下文价格档。价格表在该页的客户端渲染数据中，原 HTML 已完整冻结；没有以第三方转售报价替代。所有金额为 USD，未计优惠券或合同折扣。

## 同样的 Agent 调用序列

主情景每轮输出 `O=4096` token（包含思考、工具调用及答案），随后返回 `T=1024` 新工具输入，下一次请求实际总输入为 L。已有输出成为下一轮输入的一部分，不能只算新增工具返回。保守地按 `O+T` 视为新输入，余下 `L−O−T` 为可复用前缀。

每增长窗口的 10%，进行一次历史压缩／重建。连续平均意义下，每轮重建比例 `f=min(1,(O+T)/(0.1L))`；主情景假设未重建时可复用前缀全命中，仍有重建导致的整段未命中。若可复用部分的命中率为 h，则：

- 每轮命中输入 `I_hit=(L−O−T)×h×(1−f)`。
- 每轮未命中输入 `I_miss=L−I_hit`，两者之和始终为完整 L。
- 每百万输出的有效 API 费用 `p_out+(I_hit×p_hit+I_miss×p_miss)/O`。

这是按接近满窗口上沿的稳态估算，不是逐轮精确 transcript 重放。默认 API 不保证刚生成的全部输出立即进入下一轮持久前缀缓存；若服务实际命中更多，则应以 usage 字段替换，费用可能更低。[DeepSeek 缓存说明](https://api-docs.deepseek.com/guides/kv_cache)说明缓存是 best effort；[Kimi 缓存说明](https://platform.kimi.ai/docs/guide/use-context-caching-feature-of-kimi-api)也要求稳定前缀。24×7 连续调用不等于输入免费或命中率必为 100%。

完整输出另列每轮生成 1K／4K／16K，前缀命中 0／90%／99%／100%，以及不重建的理想情景。工具调用服务本身的费用未计入双方；对相同外部工具，它是共同费用。

## 卡型与价格口径

[Runpod 公开 GPU 价格](https://www.runpod.io/pricing)于 2026-09-09 的输入如下。H100 使用 SXM 价格，不能混用 PCIe 或 NVL 的容量／带宽。H200 的公开 Pod 价格用于 SXM 规格归一化，实际节点型号仍需在报价中核对。

| 卡型 | 每卡 $/h | 容量 GB | HBM TB/s | 密集 FP8 / BF16 PFLOPS |
| --- | ---: | ---: | ---: | ---: |
| H100 SXM | 3.49 | 80 | 3.35 | 1.979 / 0.9895 |
| H200 SXM | 4.59 | 141 | 4.8 | 1.979 / 0.9895 |
| B200 | 6.79 | 180 | 8 | 4.5 / 2.25 |
| B300 | 7.89 | 288 | 8 | 4.5 / 2.25 |

规格来自 [NVIDIA H100](https://www.nvidia.com/en-sg/data-center/h100/)、[H200](https://www.nvidia.com/en-us/data-center/h200/)、[DGX B200](https://www.nvidia.com/en-us/data-center/dgx-b200/)、[DGX B300](https://www.nvidia.com/en-us/data-center/dgx-b300/)及 [HGX 组件说明](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html)。稀疏 FLOPS 已换为密集 FLOPS。B300 的更高原生 FP4 吞吐不自动用于本题 W4A8 路径；当前主要收益是容量。B300 的 GPU 用户手册／HGX 组件按每卡 288 GB，某些营销表的整机总容量为取整值。

所有卡均支付完整组的 720 小时，另留 20% 显存余量。大集群的拓扑、互联和价格不能由单卡 Pod 报价保证；这些单价是统一采购情景，并未声称可立刻按该价格买到对应整组实例。

## 不同后端不套用相同 FP4 峰值

V4 枚举 TP1／2／4／8，缓存按 TP 复制；放不下的方案自动排除。其固定参考专家 kernel 将 FP4 权重转换为 FP8 执行，Hopper 也不按原生 FP4 峰值计算。

K3 的候选是 H100 的 TP32×PP1／2；H200 的 TP16×PP1／2 或 TP32；B200 的 TP8×PP2 或 TP16；B300 的 TP8×PP1／2。单节点 TP 最多 8；超过 8 的 collective 按跨节点有效 25 GB/s 与至少 20 µs 启动计算。组内有效通信带宽在 Hopper 取 225 GB/s，Blackwell 取 450 GB/s。PP 多个阶段的延迟顺序相加，不能直接用总卡数除以单 token 延迟。

K3 在 Blackwell 比较 TP 复制与 DCP 分片，Hopper 保守保留 TP 复制。参考 [SGLang K3 配置说明](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3)，Blackwell 用 W4A8 矩阵情景，Hopper 的 Marlin 路径按 W4A16／BF16 计算。各后端真实 tile、转换和效率仍须测量；当前继承三档矩阵／HBM 效率及每层开销，不宣称同一个效率系数对四款卡已校准。

K3 另比较 BF16 与 FP8 潜变量缓存。FP8 只缩小 MLA 历史，另加 1/128 尺度开销的估算余量；FP32 KDA 状态和短卷积不跟着减半。每请求仍保留五份 KDA 槽。FP8 缓存需要验证模型质量、格式和内核支持，未视为零代价的等质量保证。可行布局逐阶段统计状态峰值；候选配置是资源与拓扑设计，不是已验证的启动命令。

## 与 API 对齐的 GPU 工作量与版本

GPU 不只处理输出：每轮还要处理工具新输入，以及每位员工的周期重建。每个新输入 token 的逻辑矩阵工作按已满历史下计算，再除以整组有效算力，形成 chunked prefill 估算。每输出 token 的额外池时间为 `B×[(T/O)×t_new_input+(f/O)×t_rebuild]`，加到原 decode 间隔。自己的前一轮输出已有运行时状态，不重复 prefill；API 是否持久命中这些 token 则依前缀缓存规则和 usage。

上述 prefill 仍是矩阵工作近似，未覆盖全部内存访问、摘要生成和流水线空泡；加入这些成本通常不利于 GPU。GPU 卡组始终繁忙，即使一部分时间在 prefill，也不人为加低谷闲置费。

当前 DeepSeek 官方 API 名称已指向 **Flash-0731**，原本书资源记录固定的是较早的 Flash。比较脚本检查 0731 的主干层数、维度、路由数及压缩倍率与旧主干一致；**容量保守预留 0731 整个 checkpoint 的 166.879 GB**（含未使用 MTP）。主干逻辑执行仍沿冻结账本，不执行这些 MTP，也不凭它宣称推测加速。该处理避免拿旧载荷充当精确新 checkpoint 部署；它是同架构档位对比，尚未证明权重／模板／数值和 API 版本完全相同。K3 同样未证明官方服务内部实现与自建后端逐项一致。

## 怎样判断更便宜

首先在容量可行且工作流平均输出至少 30 token/s 的候选中，按 **GPU 每百万输出费用** 排序，不能按月租排序后忽略不同产出。然后取该候选每人的月输出量，计算 API 处理同样输出量及同样调用序列的账单。API 若达不到该速度或持续额度，则不是可替代方案；价格本身没有验证吞吐。

主情景结果中，V4 的 200K／1M 由 B200 领先；K3 的 200K 由 B300 领先，1M 由 B200 领先。API 在这四个主情景中更便宜。它不是普遍定理：fast 效率情景下 V4 200K 的 GPU 费用约 $3.20/M，低于同负载 API 的 $4.69/M；K3 200K 的 fast GPU 情景约 $66.34/M，已接近 API 的 $65.91/M。缓存失效、调用粒度、租金与实际效率都可能改变排序。

结果表还给出 GPU 租金交叉点：`当前租价×API单位成本/GPU单位成本`，以及 API 便宜所需的整段输入命中率。它们固定性能与共享人数，能用于判断下一步应争取更低租价、调整 serving 还是实测缓存；不能据此宣称 B200 或 API 在所有条件下最优。
