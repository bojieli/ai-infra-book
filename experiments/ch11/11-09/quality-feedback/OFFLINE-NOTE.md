# 执行后离线检查平台适配
四次模型作业于远端 2026-09-09 04:34:08 UTC 前退出，raw 已传输；首次本地 analyze.py 在启动 holdout 子进程的 preexec_fn 失败：subprocess.SubprocessError: Exception occurred in preexec_fn。macOS 不支持原 fixture 的 RLIMIT_AS 设置；尚未执行 holdout，未改变任何模型轨迹或反馈。

保留 CPU2秒/AS512MiB/墙钟5秒/输出1MiB 的原边界，改在远端 Linux 的同目录执行纯CPU check_final.py（不导入模型、无模型服务），再传回独立检查stdout/stderr。analyze.py仅读取该原始结果。相较 PROTOCOL 的“本地离线执行”是平台适配，发生在四次固定模型尝试完成后，不增加/重跑模型尝试，不提供 holdout 给模型。
