# C52 迁移子账集成交付

共享代码已稳定，等待父代理全量 reproduce、outline sync 与最终核验；本代理没有执行全量复算。原 PLAN C52 未勾选。

接口：`infra_calc.topics.reconfiguration.calculate(scenario: dict)`。结果的 `scenario` 可直接用 `calculate(result['scenario'])` 重放。CLI：`python3 calculations/calc.py reconfiguration --format md`；`--inputs` 接受完整场景字典，缺省使用 scenarios/reconfiguration-example.json。JSON 原件保留完整分片坐标，Markdown 专用分支按 kind/source/target/local 汇总，同时输出逐卡容量、时间缺项、条件摊销和费用。

新增文件：

- src/infra_calc/topics/reconfiguration.py
- tests/test_reconfiguration.py
- tests/test_reconfiguration_review.py
- tests/test_reconfiguration_integration.py
- scenarios/reconfiguration-example.json

已有文件只加 C52：cli.py、report.py、reproduce.py、outline.py，以及 scenarios/book.json 的 reconfiguration 组。reproduce 输入锁包含 reconfiguration-*.json；9 场景输出各自 JSON/Markdown 并加入 README 索引、返回场景计数。outline sync 插入 9.6.2 前的 C52-migration 段。

场景覆盖：dense TP4→8、GQA TP8→16、Qwen235 EP8→16/16→8、Qwen30 非整除 EP7→5、TP2×EP4→TP4×EP2、跨设备 replay、完整声明串行路径、同卡重新物化。

默认 B=2、history=8192：网络 16449646080 bytes（权重 14335713280、KV 2113929216、辅助 3584），本地源载荷 2352062976 bytes，读写接口 4704125952 bytes。资源下界 18356228/390625=46.99194368 秒；声明串行切换、测量切换、端到端预测均为空。g0 旧驻留 4699810816、目标 2350213632、含 2 GiB 声明额外缓冲峰值 9197508096 bytes；声明 80 GB 可容纳。相同设备布局网络为零仍重新物化，旧目标双份峰值及本地时间照计。

声明串行教学场景使用网络 100 秒，各 9 项串行运行项 1 秒，总 109 秒；不是将 46.99 秒下界当作网络运行时间。10 秒额外投入、0.0002 秒/步节省，50000 步持平，50001 步严格收益；容量和 SLO 另核，不自动据此选择部署。

验证：`PYTHONPATH=calculations/src python -m unittest discover -s calculations/tests -p 'test_reconfiguration*.py'` 共 18 项通过。9 场景均重放与渲染通过；真实 CLI 默认 JSON 与 MD 与 API 输出等值。reproduce/outline 导入通过。

验收边界：仅 BF16 Qwen3 dense/MoE、一组 TP×EP、PP=DP=1、静止快照、调用方声明身份一致、直接单播选源、完整目标缓冲先物化后释放旧缓冲。EP 上 KV 是同一请求的复制，不是多个独立 batch；全专家权重都计入。没有引擎恢复/分流/实时脏页追赶/失败重试/SLO 实测，未提供费用保持未知。网络时间需另外输入并不得小于已知资源下界；源选择不是最优网络调度。完整原 C52 仍需这些部署与恢复执行路径和可靠观测，当前仅迁移及条件摊销子账闭合。
