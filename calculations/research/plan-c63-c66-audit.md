# C63 / C66 原要求与现有交付审计

只读状态审查；唯一写入为本报告。未运行测试、未修改PLAN或公共计算。以下“缺”指原要求尚未连接的计算，不因缺少生产实测自动增加手算题范围。两项均应保持未完成。

## C63：成组作业、抢占、验证与环境预热（11.3）

原文为`outlines/11-资源调度与运行环境.md`及同名extensions第11.3，实验11-3至11-6。不是一个单独调度公式，也不能用environment-lifecycle同名内容判整项完成。

| 原要求 | 已有证据 | 确切仍缺 |
|---|---|---|
| 11-3：两类GPU、不同CPU余量与两级网络，在线/训练/离线成组需求；比较等待、迁移、跨机器启动的完成时间 | `topics/topology_allocation.py`有固定4×4周期图2×2窗口穷举和独立割集；`dense_placement.py`/`qwen235_placement.py`有真实模型逐卡容量；`reconfiguration.py`有声明迁移和费用子账 | 未连接同一异构资源图上的卡型、CPU/host内存、在线预留、整组准入与物理路径，亦未给等待/迁移/跨机启动三方案的同工作完成时间。topology_allocation明确未把窗口映射到流路径，不能拼接成已验证候选。图11-4仍为计划。 |
| 11-4：固定资源/额外rollout/保留部分响应；区分生成、收到、采用、训练完成token；加载、重建、资源存活时间与费用交叉点 | `experiments/ch11/11-04/README.md`及`analyze.py`已有12真实路径、8抢占恢复token等价；保留前缀仍重建KV，且存在比从头重做更慢的反例。`kv_restore.py`有固定权重恢复算术，`rl_supply.py`有等长cohort声明池速率；`weight_handoff.py`有传输/驻留子账。`case-studies/preemptible-rollout-and-weight-readiness.md`及`research/2026-infra-survey/verify_rlboost_recovery.py`保留源码依据 | 实验README明确费用、资源存活时间与预期损失尚由C63承担。未形成同批有效训练样本的三方案时间/成本与存活时间翻转。extensions要求PolyRL批量恢复的4000/1000已收token与实际采用前缀截齐区别，也应接入，不能只统计保存token。原30GB×6接收、200Gbps出口/50Gbps接收的7.2秒是已有手算，不必重新声称未算，但仍未连接就绪/有效产出。 |
| 11-5：两批到达、编译/执行；固定配额/FIFO/批次目标，长尾/超时，排队/反馈/释放，资源节省vs训练等待 | `experiments/ch11/11-05`已有超时反馈与释放差异；`batch-scheduling/README.md`、`analyze.py`有同六任务三策略三轮54子进程，独立检查最多两槽/决策顺序/摘要。timeline图已经生成，不应说完全没有验证时间线 | 当前实际CPU两槽把compile与execute串在同一任务内，尚未给分开的CPU编译/GPU执行资源配比、两批最早完成/最迟启动的声明时间线及训练组额外等待成本。九个1秒/一个100秒的条件剩余时间反例也需显式计算，不用总体均值减已等待。可用给定阶段时长完成手算，无需再强制运行GPU验证。实验自己的README仍标整体partial。 |
| 11-6：同一多轮任务always-resident/on-demand/prewarm；预测准确率、提前量、环境内存、工具切换频率；任务时间/GiB·秒及过度预热边界 | `topics/environment_lifecycle.py:recorded_prewarm`封存并复核11-06记录；`calculate`的`prewarm_budget`已给hit/lead/prep/timeout下期待等待、浪费、内存byte-seconds。`results/environment-lifecycle-{ready-hit,no-hit,tight-budget}.json`等已公共接入；`experiments/ch11/11-06`有144调用/四策略局部实测 | 现有期待公式是单调用预工具窗口，实测是固定fixture；尚缺把工具切换/重用间隔作为输入的同一多轮三策略完整任务账与过度预热条件。不能把不含工具间保持阶段的pretool byte-seconds当整任务GiB·秒。无需把容器/云沙箱实测列为这个教学公式交付的强制要求。 |

extensions另含在线实例份额vs新建、Dilu/Medusa的历史loading对照、P/D角色重配、Rubick方案选择、共享网络放置等变体。现有case-studies可作为已存在的来源和手算，整合时须保留；本报告不把某个小时间线宣称覆盖全部这些变体。

建议状态短句：已有成组容量/迁移子账、真实抢占恢复和两批CPU验证记录，以及公共预热期待/记录复算；仍缺异构成组完成时间、抢占有效训练成本与存活窗口、验证资源—训练等待连接、多轮预热切换边界。保留C63未勾选。

## C66：图片精修字节、传输、编解码与远端交叉点（12.1）

原范围来自`outlines/12-端边云协同.md`及同名extensions第12.1.1–12.1.2、实验12-1、图12-1，以及12.1.4的本地/远端比较。实验允许“实际字节或给定元数据”，所以无需强制新拍RAW、实际压缩或生产云端测量才可完成。

已经有：

- 原文明确的30MB输入、5MB成片、20/100Mbit/s、RTT100ms、云处理0.3s得到12s上传+0.4s下载+0.1s往返+0.3s处理=12.8s；处理降为0.03s只省0.27s。这是有效的已有手算。
- 原文已有“上传+排队+远端执行+下载<本地执行”的条件式。
- `topics/image_generation.py`及`results/image-generation-book.json`有图像生成内部矩阵/参考非矩阵和RGB tensor边界；源码明确JPEG/PNG/RAW文件bytes未知。`flux_vae_decode.py`是latent→RGB解码器；**VAE decoder不是JPEG/RAW文件解码器**。
- `vision_preprocess.py`以已解码RGB为入口，明确排除JPEG/PNG解码；`host_transfer.py`处理主机/设备数据传输，不是非对称互联网图片请求。`multimodal_cache.py`明确EC不能替代RAW精修输入。

在当前公共topics/scenarios/results中未找到把上述图片字节、非对称链路、编解码、连接复用及本地/远端交叉点接成实验12-1的专门结果；`experiments/ch12/12-01`也不存在。这个结论依据字段/入口范围，非仅检查模块名。

最小实际缺口：

1. 接受输入格式与原始/传输/输出文件byte元数据，保留MB/MiB和bit/byte换算、相同业务质量要求；RAW/JPEG不是按像素固定推文件大小，也不能默认有损JPEG与RAW等价。
2. 同请求串行依赖图：输入准备/压缩、建链或复用、上传、排队/解码、模型处理、成片编码、下载/可用；显式指出已包含在哪个时长内，防止重复RTT或编解码。给定元数据和声明时间足够。
3. 扫描上行、处理速度、压缩比例与encode/decode开销，求压缩盈亏及本地/远端等时点；分别报告复用连接和模型加速的节省。无法赢的非正余量要明确，而不是返回负带宽阈值。
4. 预览与完整成片不同交付点；仅在声明数据依赖允许时加分块重叠对照，否则保持收齐整图再处理。不要用首预览时间替代完整成片。
5. 从同结果生成图12-1路径与带宽/成片时间曲线、接公共CLI/固定场景/正文链接与独立边界审核。核12.8s原例、0.27s节省、零压缩收益/额外开销、非对称链路与交叉点两侧即可，不需先构建真实图片编辑服务。

C66不应因FLUX VAE或图像预处理模块存在就勾选；也不应扩大成完整C67的ASR/TTS/Computer Use三类交互验收。建议状态短句：原12.8秒与0.27秒手算已存在；生成/视觉计算仅供复用，图片文件字节—非对称传输—编解码—同质量本地/远端交叉点及图12-1尚待公共连接。
