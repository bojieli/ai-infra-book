# 第 11–13 章下一批定量计算审计

2026-09-09，依据当前 PLAN、三章正文、关联案例及已有 topics 实际内容审查。这里只登记可实施范围，不把已有手算或实验摘要视为集成计算完成。按主代理后续指派，C67 正在单独实现；其余保留可实施任务。

## 优先实施：C67 多模态完整 EC 与语言 KV

对应 12.2.2、实验 12-3、图 12-3；同一计算服务第 9 章 E/PD 配比。现有 `teacher_cache` 是文本最终 hidden 与 logits，`state` 是语言状态；均未覆盖视觉 DeepStack。`pd_pool` 是 P/D 池，并非 E/PD。

原件：公共 `configs/models/qwen3-vl-4b/config.json`，官方 Qwen3-VL-4B-Instruct revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`。预处理与 vLLM 固定实现已归档在 `references/framework-history/2026-09-08/multimodal-execution/`，其 `sources.json` 包含 URL、revision、SHA256。主 config 不必重复下载。

- [官方模型配置](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/config.json)：patch 16、merge 2、temporal patch 2、DeepStack `[5,11,17]`、out width 2560；文本 36 层、8 KV heads、head dim 128。
- [官方预处理配置](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/resolve/ebb281ec70b05090aa6165b016eac8ec08e71b17/preprocessor_config.json)：需核对 patch/merge/temporal 一致，像素预算 65536–16777216。
- [固定 vLLM 源码](https://raw.githubusercontent.com/vllm-project/vllm/537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e/vllm/model_executor/models/qwen3_vl.py)：570–605、830–897、941–1000、2918–2959 行分别证明扩展输出宽度、沿特征维拼接、网格计数、消费端拆分。静态图片 temporal grid 为 1，不乘 2；DeepStack 扩大特征维，不增加语言位置数。

令预处理后尺寸为 H×W，P=16、M=2，静态图片 `T=(H/P)×(W/P)/M²`；完整 BF16 EC `T×2560×(1+3)×2`；视觉位置 KV `T×36×8×128×2×2`。640² 给 T=400，EC=8192000 B=7.8125 MiB，KV=58982400 B=56.25 MiB。四图加400文本位置：EC=31.25 MiB，完整题设输入 KV=281.25 MiB。特殊 token 必须由调用者计入文本位置，不自动猜 tokenizer 输出。

四卡题设 E 卡能力12 images/s，PD 卡4 requests/s，共享 E→PD 300 MB/s，四图/请求；令 h 为 encoder 侧图像命中率：`rate ≤ min(12E/[4(1−h)],4PD,300000000/32768000)`。h=0 时 2E+2PD 为6 req/s；h=3/4 时 1E+3PD 为9375/1024≈9.15527 req/s，受网络限制。h=1 时编码约束消失，但 encoder 侧缓存服务并未免费消失，仍至少保留一 E worker，查询/读取速率明确未定价。

验收：独立遍历 patch 坐标并合并为32像素单元；256²/640²/672²边界；非32整除预处理尺寸拒绝，不能用floor静默丢像素；配置/预处理字段冲突拒绝。EC 主输出+3组 DeepStack 字节守恒；四图位置仅1600不是6400；KV按真实KV头，不用32 Q头；枚举整数 E/PD、覆盖并列最优、h=0/1 与到达率恰等边界。6.4 Mbit/s下单图原图1秒、EC10.24秒，数据中心25 GB/s下EC0.32768 ms。用户尺寸是预处理后的尺寸，任意原图 resize/视频帧取样未实现。

## C61：导入真实 CPU／RSS 时间线

原始材料完整可读：`experiments/ch11/11-01/results/` 为12轮真实 Qwen3-8B 控制器；`experiments/ch11/11-01/process-resources/results/` 有9组、36个真实工具子进程和逐样本 RSS／CPU。各目录 manifest 与源码哈希可锁定。现有 `agent_trace` 读取实验3-4，只有模型/工具时间与假设 KV byte-seconds，不含这批资源测量，不应直接在旧结果里新增所谓实测RSS。

建议单独 `environment_resources`：按原始边界计算模型/工具墙钟、控制器 CPU、已回收子进程 CPU；RSS积分采用原始采样点梯形和 `Σ((RSS_i+RSS_(i+1))/2)×Δt`，名称必须带 sampled/trapezoidal；峰值为同一采样时刻进程RSS之和的最大值。采样最大间隔、计划与实际 launch 偏差、首末盲区单列。Controller RSS 与 child RSS不能未经同时间轴就叠加；RSS和不是PSS或物理内存。

验收：独立逐间隔积分，36进程完整与退出/工作输出核验；按实际launch重排，不用计划150ms替代实测；cpu-burst与cpu-spaced工作身份相同，wait-burst工作不同不能说CPU差是优化收益。3轮中位数仅摘要，保留9组。完整工具环境/扩容收益仍缺，C61保持partial。依赖输入是本书一手实测，无需第三方规格。

## C64/C65：迁入现成模型路由成本交点

`case-studies/routing-cost-and-completion.md` 与旧 `research/2026-infra-survey/calculate_routing_cost.py` 已有精确题设；目前 topics 没有实现。该脚本应迁成 CLI 可配置成本模块，不能只新增复制输出。

每次费用 `uncached×p_in + cached×p_cache + billed_output×p_out` / 10⁶；生成 usage 若已经包含思考，不再把 reasoning 相加。按现有 A/B 题设，A始终命中成功任务费用109/8000；B命中/未命中每次41/5000和53/1250；保持质量与命中独立假设，费用相等点 h=1291/1520；6秒内质量通过至少90%的约束为 h≥45/49。请求命中 h、前缀内部命中h、相对全部输入命中0.95h分列。所有失败费用保留；质量成功数0时单位成功成本为null，不是0。

原始语义依据是已归档 [Claude缓存字段](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) 和 [Gemini生成计费](https://ai.google.dev/gemini-api/docs/pricing)，它们不提供题设价格。接真实厂商价需重新读取当前官方页面并固定快照；纯教学题可以不重新抓取报价。验收用1000提交的逐任务显式记录核对分子/分母，精确交点两侧、h=0/1、零成功、reasoning已包含拒绝重复、质量与命中相关时使用联合计数而非独立乘法。

## C73/C75/C76：第13章可直接封闭的具体算题

OpenTallas案例C/D/F有固定原始版本与完整教学数字；`decode_budget`已覆盖A类HBM/KV交叉，避免重复。`request_dag`处理DAG但没有下面的制造/生命周期账。

- C73 算术供给：`ceil(15134641792/(2×10⁹×10⁻⁴))=75674 lanes`；256 lanes的理想时间29.55984725 ms。预算40%且效率60%得315306 lanes。验收n与n−1，面积条件独立，不把2:4或效率再次相乘。原始[历史复盘](https://github.com/bojieli/OpenTallas/blob/39b96158d35b24bd2bcd49061a689aea6893d2ed/docs/PERFORMANCE_DESIGN_POSTMORTEM.md)需实施时读取并锁定，当前仅阅读本书案例，不登记外链全文审查。
- C73 通信跨度：60层×2次，每次30µs/120=0.25µs；15hop×100ns=1.5µs，全token传播180µs已越100µs。已有collective模块可复用计量，不重造一般网络模拟；原始[跨度修正](https://github.com/bojieli/OpenTallas/blob/39b96158d35b24bd2bcd49061a689aea6893d2ed/docs/WAFER_VERSUS_ARRAY_LATENCY.md)实施前锁定。
- C75 生命周期：固定增量F=20M费用单位、每百万有效输出节省0.5，回本40T token；100台×10k tok/s×0.5×31536000=15.768T，全年所需254台。半年需508台。精确ceil与n−1验收，交付延迟和需求上限作为独立输入。金额为本书教学假设，无官方供应商定价含义；固定F不得又进单价节省分母。
- C76 可先导入 `experiments/ch13/13-06/`：prediction.json+sha在实测前封存；两配置各5次raw，请求完成中位数0.5904369300696999/0.5016041379421949，比值1.1770974069152158，支持1.10预测。核验8192相同token、输出ID、32/16 chunk和先验哈希；不把固定先256后512的顺序小样本说成随机对照或混合服务普遍优越。C76广义不确定性与补测价值仍缺。

完成这批模块仍不能勾选整章：C62冷暖环境原始计时缺；C63成组作业及抢占执行仍需完整轨迹；C66–71除上面C67外尚有协议/无线/跨地域计费；C72–76实际物理供给、同质量设备前沿和站点成本需进一步输入。不存在需暂停全书计算的共同阻塞。
