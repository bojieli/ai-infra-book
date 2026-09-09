# Fish Speech 语音接收边界协议

实际现有 RTX Fish Speech 1.5 服务，固定 sources/server.py 与 health 报告的身份；同一中性英文文本，无命名声音／参考音频。流式 true/false/false/true 四轮 ABBA，只改变 streaming，采样参数保持相同但服务未提供 seed 控制，音频不可假设相同。chunk_length 80、max_new_tokens 512、top_p .7、temperature .7、repetition_penalty 1.2。

服务在使用中，不重启、不修改、不关闭，非独占性能环境。客户端在 RTX loopback，每次新建 HTTP 连接；记录完整 body 和每次 read1 的累计偏移、字节数、读取完成时刻。WAV 固定头 44 byte；首个完整 20 ms PCM 帧需随后 1764 byte。到达的文件头不等于可播放 PCM，任何音频块到达不等于 DAC 已播放。

四轮后额外一次 streaming，在客户端取得至少一个 20 ms PCM 帧后主动关闭响应与连接，记录调用/返回时刻。保留这个故障注入原件，不作为可删除的失败；没有服务端取消回执，不推断 GPU 停止。此次不在共享服务上注入更多异常。

输出只用于实际音频接收和下一阶段 Queqiao 重放准备；未运行 Queqiao 隧道、没有物理扬声器播放，也不复算旧 Queqiao 数据/C70。模型随机性和未听辨质量阻止把传输条件差异单独当质量匹配收益。
