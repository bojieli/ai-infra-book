已接受新预算，并完成本地续跑准备：守护阈值更新为 **GPU 16 GiB、含 supervisor 的 RSS 24 GiB**；主任务保留固定算术奖励，另预登记独立的非零学习控制。**不会再因旧 8/12 GiB 预算停止任务。**

但本轮第一项远端余量重验就被当前执行环境拒绝，尚未连接 RTX：

```text
ssh: connect to host 155.103.252.95 port 22: Operation not permitted
exit_code: 255
```

当前会话已切换为网络受限沙箱，且禁止提权。因此尚未同步新配置、启动新训练或获得新的远端资源数据。具体证据和后续执行顺序已写入 [status.md](/Users/boj/book/ai-infra-book/experiments/parallel-workers/verlrl/status.md)，新预算与正式控制见 [PROTOCOL.md](/Users/boj/book/ai-infra-book/experiments/ch10/10-08/PROTOCOL.md)。

旧 attempts 和 Ray 日志暂未删除；成功后才按你的要求清理被替代的调试历史。**当前需要恢复本会话到 `rtx-pro:22` 的出站 SSH 能力；计算资源授权已经充分，无需重复授权。**