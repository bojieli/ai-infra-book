本有界实验已完成，结果与正文候选句见 [README](/Users/boj/book/ai-infra-book/experiments/ch12/12-06/README.md)，[worker 状态](/Users/boj/book/ai-infra-book/experiments/parallel-workers/dualpath/status.md)已更新。

- **真实传输：** 独立客户端/服务端进程、两条本机 TCP 连接；实际执行连接关闭、切换、PCM 有序消费与去重、打断及取消 ACK、工具结果交付。
- **重复结果：** 6 次预检、30 次正式尝试。正式无故障与单路径关闭条件 **20/20 完成**；共同端点关闭条件 **10/10 未完成**，作为负例保留。
- **独立验收：** 36 条记录符合预期；重复消费、缺失 ACK、payload 损坏三种变异均被拒绝。复制无故障时每次额外收到 **5120 bytes PCM**，切换为零。
- **交付与清理：** 事前协议、run/analyze/plot、双端原始记录、环境及源 hash、PNG/SVG 与绘图 QA 齐全。36 个服务端均退出，72 个监听端口结束后均拒绝连接；文件约 1.6MB。

保留了初始 Mac 内存限制设置失败，以及两次真实 TCP reset 导致初版验收拒绝的记录；仅修订离线验收，未复跑传输，详见[执行偏差](/Users/boj/book/ai-infra-book/experiments/ch12/12-06/EXECUTION-NOTE.md)。

仅写入授权目录。未操作 calculations、正文或其他共享进展，未启动 agent、提交 git 或联系其他作者。本结果不覆盖真实 WAN、蜂窝电量、TTS 模型、物理播放或 RAW 分流，不宣称实验 12-6 整体完成。