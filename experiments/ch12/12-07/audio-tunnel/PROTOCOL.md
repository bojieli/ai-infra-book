# 12-7 固定音频隧道协议

固定 Queqiao 提交 496ca6278e359c02b5107dfab77c6a3db585f80d，原生 startStack 的 Queqiao 和 baseline TUICTransport。只添加实验 harness，不改库。固定 Fish 实际音频 fixture/audio.wav，mono 44100Hz PCM16、1183744 PCM bytes，每20ms发送1764bytes，最后保留不足一帧的尾部。所有正常条件必须逐字节还原同一PCM。

Mac loopback sockets+userspace pathsim：RTT40ms、100Mbit/s、队列500000bytes、seed1207、零配置丢包；不是WAN。四轮pool on/off/off/on，每轮baseline和queqiao顺序固定，先完整流，全部完整流后再按相同顺序跑取消条件。每条件新建代理/模拟器，以1024byte原生请求预热连接后连接音频origin；唯一自变量为Queqiao池开关，baseline对该开关不敏感。

服务器从收到一个g字节起，每20ms发送下一帧；记录每次write完成。客户端io.ReadFull取得一帧后记接收事件。软件sink先缓冲3个完整帧，然后以20ms节拍消费，缺帧时等待并记录空缓冲等待；尾帧按实际样本时长。这是在线软件消费，不是物理声卡/DAC，更不是人耳确认的停顿。

取消条件在收到10个完整帧后关闭客户端socket，记录close调用/返回、软件sink停止；origin另一个goroutine等待读到客户端方向EOF/错误，记录它何时观察到关闭，再停止发送。5秒内若未观察到则保留未知，不把缺回执当成功。origin关闭不是Fish模型取消，此重放没有模型生成。

保留四轮正式重复、慢样本与全部取消故障注入。记录全量事件、接收PCM、源码/音频SHA、命令/退出码与原生路径统计。不复算C70历史数据。状态仍需按物理播放/WAN/模型取消的实际证据判断。
