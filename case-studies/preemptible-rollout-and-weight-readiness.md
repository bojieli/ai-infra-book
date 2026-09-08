# 可抢占 rollout 的权重准备与有效产出

用于 11.3.2 和实验 11-4，连接第 7 章共享出口、第 8 章 prefill／decode 与第 10 章同步 RL。2026-09-09 补读 RLBoost 的实现、评估与附录，并静态检查作者 PolyRL 的固定代码；没有运行下载代码、租用实例或复现论文性能。此前负载与设计阅读见[原案例](platform-routing.md)。

## 新实例出现以后，多久才能开始工作

RLBoost 的实验训练组使用八卡 H100 实例，额外 rollout 使用两卡实例。与后者通信时，训练实例使用 200 Gbps 前端网卡，两卡实例的前端接口为 50 Gbps；不能把训练组后端的四张 200 Gbps 网卡一起加进这条路径。[论文物理页 9](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf#page=9)

先给一次传输 **30 GB 完整权重、同时准备六个 rollout 实例**的教学输入。30 GB 是便于手算的载荷假设，实际实验应记录序列化后字节数。每个接收端的链路下界为 `30 / (50 / 8) = 4.8 秒`；同一个训练节点的出口却要发送六份，共 180 GB，因而全部传完至少需要 `180 / (200 / 8) = 7.2 秒`。真实时间还受共享网络、内存读写、协议、加载和启动影响。这个下界针对六个实例全部就绪，不表示第一个实例也必须等到第 7.2 秒。

这一轮读到的 PolyRL 路径先把完整权重收到接收实例的 CPU 共享缓冲，再由 TP rank 0 分块送入 GPU、广播到 TP 组并调用模型加载。因此，接收实例使用 TP=2，并没有自动将外部网络载荷减成 15 GB。发送端还要把 FSDP 参数还原并复制到发送缓冲；网卡传输结束以后，GPU 加载、缓存处理与版本确认仍决定实例何时能接请求。[发送端](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rlboost/weight_transfer/fsdp_interface.py#L186)、[接收与 TP 分发](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rlboost/sglang/patches.py#L169)

论文允许新实例在当前同步训练轮次内拉取已有版本并开始 rollout，避免必须等到下一轮的空闲。它不消除权重准备时间。实验先标出实例出现、CPU 权重到齐、GPU 加载完成、首个有效输出四个时刻，再计算这段可用窗口里真正产出了多少训练数据。

## 保存了多少 token，与恢复了多少 token

部分响应迁移保存 token，换实例后仍需用“原输入＋保留的输出”重新 prefill。新实例没有自动继承原来的 KV。以一个已经收到 8,000 个输出 token 的请求为例，若补做这些 decode 按教学速率 80 token/s 执行，需要 100 秒。若续接相对从头重做增加 2 秒前缀准备和 1 秒前缀交接，净节省就是 97 秒。共有的调度开销在两边同计，固定剩余生成工作相同；速率与增量开销都是教学输入，实际应从同模型和执行条件下的记录取得。

作者代码还有一个容易遗漏的批量条件：一组请求共享采样参数时，恢复函数取这组已保存输出的最短长度，并将各条响应截到该长度，再扣减 `max_new_tokens`。如果两条已经收到了 4,000 和 1,000 个 token，这个分支只为每条保留 1,000 个，第一条还需补做 3,000 个；沿用 80 token/s 的教学速率，就是 37.5 秒。单条请求分支没有这项组内截短。不能把“已经收到的 token 数”全部计入恢复收益，也不能据此推定论文中所有请求都使用这个批量分支。[输入续接](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rollout-manager/src/utils.rs#L140)、[组内截短与预算](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rollout-manager/src/utils.rs#L227)

启动示例还设置了流式输出间隔，因此实例中已经算出的进度、管理器已收到的进度、恢复时实际采用的进度要分别记录。传输中的数据与排队会进一步影响差距，不能仅用输出间隔保证最多丢几个 token。带工具执行的 Agent 还需要保存环境与操作状态；本例只讨论生成请求。

## 何时增加实例只会提高费用

论文按多家云和地区的价格汇总，使用八卡训练实例 `$83.79/h`、两卡额外实例 `$5.32/h` 的成本输入；后者甚至包括把不同大小实例折算成两张 GPU 的价格，不是某个可直接购买的统一 SKU。这里只复算论文口径，不提供今日报价。[附录 A，物理页 17](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf#page=17)

若六个额外实例一直计费，总费率为 `83.79 + 6 × 5.32 = 115.71 美元/小时`。与只用训练组相比，完成相同有效训练工作时的吞吐必须超过原来的 `115.71 / 83.79 ≈ 1.381 倍`，单位工作成本才会下降。吞吐仅提高到 1.2 倍时，成本反而约为原来的 1.151 倍；提高到 1.6 倍时约为 0.863 倍。实际可抢占轨迹应按各实例的计费存活时间积分，再除以同一验证标准下真正完成训练的工作量。

训练更新已经成为瓶颈以后，继续增加 rollout 卡不会等比例增加有效训练吞吐，却可能继续增加计费、权重分发和缓存驻留。更长响应会重新改变阶段比例，不能把“六个实例”当成固定甜点。RLBoost 附录 E 在其 Qwen3-14B 配置下，把最大响应长度从 5K 调到 14K，选择的额外实例数由 3 增到 6；这提供了随负载重新计算的例子，不是其他模型的容量规则。[物理页 18](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf#page=18)

## 论文、安装说明和实际代码

论文评估为同步 on-policy GRPO、OpenR1-Math、128 个 prompt、每组 8 个响应，使用 Qwen3 8B／14B／32B 和 FSDP。可抢占事件取自真实轨迹的抽样片段，在按需实例上回放；Disagg.BAL 是作者基于 StreamRL 技术自行实现的基线。图 13／17 报告轮内生成吞吐，整体评估则按训练轮次完成后的有效 token 计算吞吐，这两种数字不应混用。奖励曲线接近支持其所评估设置，没有证明任意模型或异构引擎下采样完全一致。[物理页 9–13](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf#page=9)

PolyRL 固定于 `44ce6fd`。安装说明要求 SGLang 0.5.5，并引用固定的 verl 子模块；启动脚本使用 `rlboost.sglang.launch_server`，通过补丁加入权重接收、调度和 HTTP 接口。不能把这些接口写成安装标准 SGLang 后自然具有的功能。文档和配置保留 Mooncake 名称，而所读发送／接收代码实际构造 `TCPTransferEngine`，通过 TCP socket 写入 CPU 缓冲。判断使用哪条路径必须看调用链，不能按配置项名字推断 RDMA 或 GPU 直传。[安装说明](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-install.md)、[启动及补丁](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-sglang-autopatch.py)、[TCP 接收](../references/framework-history/2026-09-09/rlboost-recovery/polyrl-tcp-engine.py)

所读管理器只有在非 bootstrap 权重加载成功、版本匹配后，才把远端实例加入可调度池。响应续接覆盖若干连接、超时和中止错误；一个未收到 `[DONE]` 就结束的流会标成 `stream_error`，却不在当前重试白名单中。接收进程对权重传输失败会抛错退出；这些错误处理片段不能证明任意故障都能自动恢复，后续真实实验仍需覆盖控制器、传输和引擎三方的退出与清理。这里记录明确的实现范围，不据静态阅读宣称部署可用性。[加载与准入](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rollout-manager/src/handlers.rs#L651)、[响应错误与重试](https://github.com/Terra-Flux/PolyRL/blob/44ce6fdcd30ecf2d55037513ddddd51076325a2b/rollout-manager/src/handlers.rs#L152)

## 模型表格也需要回到配置文件核对

论文 Table 4 将 Qwen3-14B 记为 48 层、48 个 Q 头；官方仓库固定提交 `40c0698` 的配置为 **40 层、40 个 Q 头、8 个 KV 头、head dimension 128**。原表与官方配置的差异保留，不根据这处差异反推作者实际运行的模型。书中复算公开 Qwen3-14B 时采用官方配置。[论文原表，物理页 17](../references/outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf#page=17)、[官方固定配置](https://huggingface.co/Qwen/Qwen3-14B/blob/40c069824f4251a91eefaf281ebe4c544efd3e18/config.json)

按 BF16 KV、完整 GQA 状态、不作并行切分计算，每个 token 的 KV 载荷为 `2 × 40 × 8 × 128 × 2 = 163,840 字节`，即 160 KiB；8,192 token 对应 1.25 GiB。若沿用表中的 48 层，会算成 1.5 GiB，多出 20%。这里的 KV 头数是 8，Q 头数改变计算量，不能直接替代 KV 头数计算状态容量；块分配、元数据和运行时缓冲另加。

实验 11-4 保留同一任务、同一质量标准，分别记录生成、收到、恢复和完成训练的 token；把权重就绪、重建前缀与计费存活窗口画进图 11-5 的 rollout 子图。正文只保留出口下界与费用交点，配置差异和源码行段留在[来源与阅读记录](../references/framework-history/2026-09-09/rlboost-recovery/README.md)。
