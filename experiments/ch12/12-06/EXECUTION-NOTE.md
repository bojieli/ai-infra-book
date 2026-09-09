# 最终执行配置与验收依据

实际取消硬地址空间限制，改为每次记录时检查每进程峰值 RSS <768MiB、每连接缓冲 <1MiB、固定小夹具与帧、单次文件硬上限16MiB，离线再校验两进程峰值。RSS 检查不是操作系统硬内存隔离，也不计系统 socket 内存；本次峰值记录用于证实实际资源用量。其余协议不变。

正式30次完成后，初版离线验收拒绝 02-switch-endpoint：它把端点负例的错误文本写死为 ConnectionError: no_response，而 02、04 两次 switch-endpoint 在服务端关闭双连接后，备路重试 recv 实际报告 ConnectionResetError errno54。双方日志证明主路 EOF、备路重试、服务端双连接 shutdown+close 和正常退出，且负例均只消费0–3帧、无取消确认或完成。接受这两种实测断连表现，传输源码和原始记录未改、未重跑。sources-v1 保存与运行环境源hash匹配的原版本；当前 analyze.py 增加这一错误分支并核验当前文件或历史快照hash。原验收依据保留在 analysis.log；最终验收为 analysis-v2.log，绘图为 plot-v3.log，图像检查见 plot-QA.md。
