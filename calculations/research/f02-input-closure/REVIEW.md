# F02 模型输入闭合审查

审查日期：2026-09-09。只读核对当前 checkout，未刷新远端、未下载权重。结论：**原 F02 目前不能勾选**。真正的输入阻塞集中在 70B 代表没有取得官方 config，以及 Qwen3.5 只有 config、没有锁定实现。Kimi K3 的输入文件已经齐全，但有必须保留的配置／checkpoint 兼容性冲突；“源已取得”不能写成“可直接运行”。

依据是 [PLAN F02](../../PLAN.md) 的原范围，不按当前已经实现的模块反向缩小范围。逐模型结果、实际引用原件 SHA、源码 SHA 与失败状态见 [model-gaps.json](model-gaps.json)。覆盖原范围 11 个模型及用户追加的 6 个生成模型，共 17 项；349 个引用原件均核对实际 SHA 和 bytes，通过。该绑定按引用原件逐项建立，不绑定会被硬件表更新影响的整份 sources.lock.json。辅助音频／图像／视频源锁包含共享依赖包，JSON 保留所用源锁边界，不把包中每个文件都称为每个模型直接调用。

## 原 F02 逐项结论

| 模型 | 官方配置／实现 | index／header | 可以验收的输入范围 | 实际剩余动作 |
| --- | --- | --- | --- | --- |
| Qwen3-8B、32B | 两个 config；共享固定 Transformers Qwen3 实现 | 各自 index 已锁；未下载全 headers | config 推导的 dense 算子／权重逻辑形状 | 登记 index 名称覆盖和适配器契约；不可把 index 当 dtype／shape 证据 |
| Qwen3-30B-A3B、235B-A22B | 两个 config；共享固定 Qwen3 MoE 实现 | 各自 index 已锁；未下载全 headers | config 推导的全专家权重及显式路由逻辑图 | 同上；实际量化存储仍需专门证据 |
| 70B 代表：Llama-3.1-70B-Instruct | 锁中请求失败为 HTTP 401，无 config 文件，无该模型实现 | 无 | 目前只有名义 70B 教学算例，不能代替真实模型 | 取得官方授权可读 config，或明确改选公开可访问的官方 70B 代表；再锁实现和 index |
| DeepSeek V3 | config + modeling_deepseek.py 已锁 | 无 index／header | v3-forward 的基础前向，参考 MLA 展开缓存、router、共享／路由专家等 | config／实现可先接受；补同 revision index 后才能盘点 checkpoint 组件；FP8 实际存储、MTP 不能从基础账外推 |
| DeepSeek V4 Flash | HF config、inference/config、model.py、kernel.py、Hadamard 依赖已锁 | index + 46 shard headers | 存储 dtype／偏移／总字节及基础逻辑参数总数对照 | 不缺下载；逐张量预期形状尚非全量枚举，运行时转换不在 checkpoint 账内 |
| DeepSeek V4 Pro | 同上 | index + 64 shard headers | 同上 | 同上 |
| Kimi K3 | config、K3／Linear 实现及固定 FLA 路径已锁 | index + 96 shard headers；497220 张量 | config 逻辑账与 checkpoint 存储账分别有效 | 69 个 A_log 配置／存储冲突阻止宣称直接加载兼容，见下文 |
| Qwen3.5-397B-A17B | 仅 config | 无 index／header | 只能声明配置已取得 | 锁定匹配的官方 hybrid/MoE 实现与 index，核 layer_types、线性注意力状态及视觉桥；当前无此适配器 |
| Qwen3-VL-4B | config；实现与默认配置、vision_utils 已在 vision-encoding.lock.json 锁定 | 无模型 index／header | 显式 grid 到 vision embedding、DeepStack、语言请求的声明逻辑账 | 将辅助源锁纳入公共输入验收即可；物理 checkpoint 形状仍未核 |

必要 config／实现锁定不等于每个模型都必须先下载全 checkpoint headers，也不等于所有运行时专题完成。Qwen、V3、VL 缺少 headers 的事实必须保留，但不能把它扩张为逻辑算子输入永远不能验收。相反，70B 的 config 真未取得，Qwen3.5 的实现真未锁，不能用范围声明将其消去。

## Kimi K3：结果会怎样受影响

固定 revision 为 `f831ab66814297da540d832a5235f8e904f29d06`，具体原件和数值见 [既有 checkpoint 审查](../../K3-CHECKPOINT-AUDIT.md) 与 [运行契约实现](../../src/infra_calc/topics/k3_checkpoint.py)。这不是缺文件：全部 96 个头已取得且有索引、字节、偏移和张量归属核验。

69 层 KDA 的 `A_log` 配置／构造形状为 `[96]`，checkpoint 是 `[128]`。相邻 beta 投影仍是 96 头，Q/K/V 宽度为 `96 × 128 = 12288`。配置逻辑文本参数为 2779484476000，按 checkpoint 解包排除 scale 为 2779484478208，相差 2208。该差值不能通过将整个 KDA 改成 128 头修复，否则矩阵、状态、gate 与输出工作都会被错误放大。

固定执行路径：普通 prefill 调 `chunk_kda`；只有 cache 存在且 query length 为 1 才使用 `fused_recurrent_kda`。参数构造及参考 gate 的 `A_log.view(H,1)` 要求 96 个元素。融合前向的 head-index load 可能只读取缓冲前 96 项，这不证明 loader 合法、尾部是 padding、或反向布局兼容。`transpose_state_layout` 到 `state_v_first` 的别名在固定 FLA 源中已经显式核对，不是目前未解决的问题。

验收应保留两条独立断言：`checkpoint_index_validation=true` 与 `config_checkpoint_shape_match=false`。config-based 数学账可继续使用；未经官方转换契约不能声称原 checkpoint 可直接加载，不能静默裁剪、广播、重初始化或把存储 U8 当 INT8 算力。

## 用户追加的输入没有丢失

Omni、Fish S2 Pro、Qwen Image、Flux2 Klein、Wan2.2、MiniMax H3 已有对应根／组件 config，以及独立音频、图像或视频实现锁。Omni 理解有 encoder→Thinker 请求连接，输出音频有 Talker／code predictor／codec；Fish 有 slow/fast AR 与 codec；图像／视频按各自 denoiser、VAE 和时轴调用计量。模型目录不是只支持文本根 config。

这 6 项在逐模型 JSON 单列 `user-added-generative`，不偷换原 F02 范围。其接口状态来自当前 CLI 与实际 stage 模块；没有据 modelcard 的 4B／30B 宣称精确参数，也没有据 stage 算术宣称完整运行时／质量验证。完整模型 checkpoint header 形状闭合尚未建立，JSON 将其与组件 config 已锁分开。当前任务不需要另开新的生成计算专题。

## 按依赖执行的有限收口方案

1. **先闭合两个真实缺源项。** 对锁定 70B 官方 revision 做一次合法访问核对；有权限则仅取 config／实现／index，无权限就记录具体授权依赖，或由主线明确指定另一个官方 70B 代表，不能换成名义 70e9。Qwen3.5 则固定匹配 config 架构的官方 modeling／configuration 实现及 index，先做字段与层类型清单，不在本包承诺完整前向。
2. **制作公共模型输入验收记录。** 直接复用本 JSON 的实际源 SHA，将 shared Qwen 实现、FLA／Hadamard、VL 辅助锁和追加生成源锁纳入模型依赖，而不是只查 sources.lock.json 的 `model` 同名行。对 config 模式、index 名称模式、checkpoint 存储模式分别列准入条件。
3. **K3 做一次有界官方纠偏检查。** 只比较原固定版本与一个明确指定的后续官方 config／model／index 版本或官方转换文档；只为发生变化的 A_log 获取元数据头。若仍无官方修复证据，保留冲突并将直接 runtime 兼容标为不支持；不反复下载全量文件、不创造新的头数。来源范围完成与 C11 的实际兼容完成分别判定。
4. **执行离线验收。** 逐引用 SHA／bytes 全通过；原 11 个模型均有必要 config 与实现或明确未完成项；四个 Qwen index 与适配器名称枚举相符；V4 保持 checkpoint 总数对照；K3 保留全部 69 个冲突；未知架构必须继续拒绝 generic forward。达到前两项后可复审 F02，不能用完整运行时尚待实测无限阻塞输入验收，也不能跳过 70B／Qwen3.5 的实际缺源。

本交付不改共享源码、配置、PLAN 或场景；未重新生成公共结果。原件链接与 revision 均来自已经锁定并核对过的本地记录，不声称这些固定版本是远端当前最新版本。
