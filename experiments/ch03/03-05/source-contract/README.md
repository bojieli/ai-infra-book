# 3-5 语音时间戳契约核对（未实测）

只读复用RTX现有OpenRealtime-sidecar-voice-deadline项目的两个bench源文件。读取时HEAD为2c8bf96350c57b174004fbd1b47640ceb0dc918a，对这两个文件的git status --short为空；保存文件本身SHA，以快照内容为最终依据。没有修改或运行该项目，没有模型/API/扬声器请求。

本核对解决后续实验的字段选用问题，不算完成固定语音实测：

| 字段/函数 | 当前源码含义 | 不能据此声称 |
|---|---|---|
| Moment.AtMS / FirstAudioAfter | 相对episode的音频到达时间/首次符合条件到达差 | 扬声器已出声 |
| Moment.PlayoutAtMS | addAgent返回的捕获波形位置 | 音频设备实际回调时间 |
| agentPlayoutMS | 前一软件播放位置加样本时长，后续块按此串接 | 操作系统已播放该队列 |
| Transcript.PlaybackMS | 输入录音时长 | 首次响应播放延迟 |

session_audio.go的addAgent把到达时刻与前一块逻辑结束比较，随后按24kHz样本数推进逻辑位置。该路径没有提供设备执行时间的证据。这里只检查这两个bench文件，不断言项目其他模块没有真实播放或取消实现。

`python3 analyze.py` 对保存源码定位六项契约，输出带行号/文件哈希的review.json。它是源码记录分析，不重写时序模拟，也不把字符串定位当作真实执行验证。sources保留两文件，manifest封存。

后续实测应分别保存原始音频到达、缓冲入队、设备输出回调/声学观测、取消发出、服务确认、设备静音与计算退出。当前这些实际量没有记录，继续为缺口；仅拿到WAV和上述字段还不足以评价打断体验。C17教学计算归calculations，未调用或复制；最终跨session论文复核仍待首轮实验完成。
