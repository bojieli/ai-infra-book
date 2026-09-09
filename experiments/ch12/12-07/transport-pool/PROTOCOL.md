# 12-7 连接池单因素执行协议

固定 Queqiao source-lock.json 中的提交；直接运行原生 queqiaobench，不改传输实现。Mac 上原生 loopback UDP 与 userspace pathsim：40 ms 模拟 RTT、100 Mbit/s、500000 byte 队列、零配置丢包、355000 byte 对象、BBR-TUIC、seed 1207。不是贵阳至 Irvine、不是实测 WAN 或语音。

四轮 ABBA：quic-pool=true,false,false,true。每轮 baseline 与 queqiao，flows=1,4，各一次正式传输；另测各栈一次 cold/warm 小请求。仅改变连接池参数，原生程序内 stack 顺序固定；轮次不是独立路径。各传输先 warmup，各 trial 重建代理与模拟器。不同 flows 是独立条件，保留正式重复与科学负结果。

保存原生 JSON、完整 stdout/stderr、命令、退出码、墙钟和构建版本。验收除进程 exit 0 外还核对 complete；不启用吞吐优劣 gate。库定义的 cold/warm 请求不是音频首次可播放，stall/cancel/audio quality 均未知；不冒充完成 12-7 语音任务。不分析旧 Queqiao 数据，不重复 C70。
