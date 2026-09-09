有界分支观测已完成，证据包已同步远端，待主 agent 统一复核回填。

两轮 8 请求波都记录到精确关联的实际路径：

`native-4` 在 occupied **4096 ≥ limit 3289** 时被限额 → 未登记 ongoing → `check_prefetch_progress` 走无条目直接 True → pop loaded=0 → 实际 prefill 的 prefix/host/storage 长度均为0 → 首完成 API cached_tokens=0。此前 native-0～3 的 progress 均实际返回 False。这次结论来自执行事件，不依赖成功 get 推断。

单请求两轮仍为 cached_tokens=1008。四组18请求的完整输出 ID、文本全部匹配固定参考；实际 device/runtime pool=4096，host pool=8208。全部 **20325 条原始事件**保留，事件 PID 与安装记录、`/proc` 后代证据对应。

四个 worker、controller、传输均 exit0；采样显存峰值17290 MiB。所有自有 PID 已退出、显存释放，原五服务保留。子进程缺少 Python `atexit` 事件已明确记录；相关分析器假设失败版本也已保留，没有因此复跑。

交付入口：

- [README 与结果边界](/Users/boj/book/ai-infra-book/experiments/ch09/09-10/branch-observation/README.md)
- [首完成请求原始事件索引](/Users/boj/book/ai-infra-book/experiments/ch09/09-10/branch-observation/REQUEST-EVIDENCE.md)
- [全部请求事件链](/Users/boj/book/ai-infra-book/experiments/ch09/09-10/branch-observation/request-chains.json)
- [任务状态](/Users/boj/book/ai-infra-book/experiments/parallel-workers/cachebranch/status.md)

本地、远端清单校验通过，121文件约68.3 MiB。封存实验及共享源码未修改，未执行 calculations、派生 agent、联系其他 session 或提交 git；不宣称全9-10完成。