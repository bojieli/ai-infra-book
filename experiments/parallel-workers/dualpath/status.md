# 双路径 worker 状态

状态：本有界子实验已完成（2026-09-09）。交付 experiments/ch12/12-06/README.md；没有启动其他agents/Codex或提交git。

完成：读章节大纲、extensions 12-6、12-04两README；事前协议；独立客户端/服务端单线程进程，两个动态端口真实TCP连接；同SHA PCM夹具、有序软件消费、复制去重、实际shutdown/close、EOF/两次真实RST、故障后切换、打断/取消ACK及工具结果一次应用。6次预检+30次正式（2策略×3故障×5重复）；无故障/单路径关闭20/20完成，共端点负例10/10未完成。独立离线验收36条预期结果，3种损坏变异全部拒绝。PNG/SVG及目视QA、环境/源hash/原始双端记录/清理记录齐全。

保留失败：Mac RLIMIT_AS设置在首次建连前失败（转录），改RSS检查+固定小对象；正式中2个共同端点负例为TCP reset，初版验收只认EOF故失败，保留初版源码/日志并只修订离线验收，无复跑。其后的绘图缺summary错误也保留。详见EXECUTION-NOTE.md。

资源/清理：至多两个单线程传输进程，正式客户端RSS峰值28000256 bytes、服务端最高28606464 bytes；目录约1.6MB。36个子进程退出0且最终PID均不存活；72个监听端口各次结束connect_ex=61。未使用GPU/MPS/SSH，未改共享venv/其他服务。

结果：复制无故障每次5120 bytes额外PCM，主连接/共同端点关闭为2560 bytes，切换为0；本机计时仅实现观测。正文简洁候选句在自己README，交主session自行回填。

未覆盖：RAW分流、汇合瓶颈扫描、数学/轨迹任务、真实WAN/Wi-Fi/蜂窝及电量/链路字节、相关故障概率、TTS模型与物理播放、取消ACK传输中再次故障、MPTCP/QUIC/冗余编码。消费是拉取式PCM解码，不是实时音频播放；乱序是明确的应用发送顺序夹具，非TCP网络乱序。复制等待所请求路径排空，不能比较first-wins尾延迟。未宣称12-6整体完成，未做跨session审计。

写入仅 experiments/ch12/12-06/ 与本status；calculations及正文/总进展/inventory/research/references/skeleton未修改，未执行、复制或联系其他session任务。
