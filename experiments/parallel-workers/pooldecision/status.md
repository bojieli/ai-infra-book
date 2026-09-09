# 实验 11-10 独立离线证据任务

状态：本批已完成，交主 agent 统一复核回填（2026-09-09）。11-10 整体仍有待验证要求；本 worker 未改 inventory/PROGRESS，也未实施扩容或宣称达成 SLO。

交付目录：`experiments/ch11/11-10/`。

- `analyze.py`：独立启动、Python 标准库、只读已封存原始证据；锁定源路径与 SHA，拒绝漂移；不执行相邻模型/工具/计算代码。
- `sources.lock.json`：228 个固定来源/上下文文件，包含各旧 manifest；约 6 MiB 外部只读依赖，不复制原始证据。
- `records.json`：77 条分组记录，逐条带源路径、SHA、定位；主轨迹与跨实验观察分列。
- `summary.json`、`decision.json`：阶段时间、CPU、RSS、队列、任务/质量、资源判断及未执行的验证条件；价格、预算、服务目标和收益缺口明确。
- `checks.json`：真实记录一致性、时序、质量、代码/文件身份、进程回收及源未修改检查，并记录本次离线 CPU/峰 RSS。
- `DECISION.md`：一页中文资源选择/验证计划，固定链接复用 C65 教学输入结果，未重算或复制其表格。
- `README.md`：依据、原题边界、跨实验关系、计量限制、缺失数据、下一轮 matched-workload 配对实验设计与接受判据。
- `manifest.json`：本目录全部文件的字节数与 SHA（自身除外），并封存本 status 的 SHA。

核心事实：11-01 单次真实 Agent 12 轮，循环 9.357789 s，模型请求合计 8.995477 s，模型区间控制器 CPU 0.157146 s，最终仅 2/6 且未 finish；引擎已有 queued→scheduled 合计 0.198464 ms。推荐先验证模型服务路径及质量门槛，再按瓶颈证据决定资源干预；未宣称 GPU 饱和、网络拥塞、成功任务成本或扩容收益。

边界：11-06 重放的是 03-04 的另一轨迹，CPU 微负载、模型候选和 Collector 记录均不与主轨迹拼成同控制对照。使用证据表，无新增科学图，无图像 QA 声明。共享 calculations/README.md 初读后被其他工作更新，作为非输入背景排除于严格锁之外并记录初读 SHA；固定 C65 结果文件仍严格校验。无 owner 联系。

验证与资源：已通过原始记录离线一致性检查和本地 Markdown 链接核查；最终检查数量及运行开销以 checks.json 为准。单线程、零子进程，本次峰 RSS 低于 64 MiB、新增文件小于 1 MiB，均低于 CPU≤2 线程/RSS2GiB/30MiB 预算。Darwin 不支持本次 RLIMIT_AS 设置，未假称硬限额生效，采用小输入顺序读取并核验实测 RSS。

写入仅限交付目录及本文件；未改正文、inventory、PROGRESS、research、references、其他旧实验或 calculations，未执行/修改/复制 calculations 代码/模拟/算例，未重跑模型或计算任务，未使用 GPU/SSH/新依赖，未派生 worker、未 git 提交。最后统一跨 session/论文审计未开展。
