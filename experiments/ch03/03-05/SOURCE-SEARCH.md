# 3-5 固定语音证据查找（未实测）

2026-09-09，只读检查RTX主机现有OpenRealtime-sidecar-voice-deadline项目的bench、evals、datasets、assets，未运行或修改该项目，没有启动语音/API请求。已发现bench/realtimecu/testdata/audio下camera/form/transient/choice/authorization/dashboard/game/static等WAV，以及bench/meeting/testdata/audio的四段WAV。它们是候选固定音频，不是已经取得的播放/取消时间线。

这次检查的bench、evals、datasets、assets中没有找到现成运行JSONL；项目顶层.artifacts/artifacts/results/runs也未发现。不等于整台机器或项目其他路径没有记录。尚未读取音频内容、来源许可、语音文本或服务配置，不把文件存在当作已获得完整实时记录。

下一步需读取对应运行与证据结构，确认可独立运行的本地路径和真实时间戳来源。优先复用授权范围内既有记录；若新跑，保留音频哈希、首个可播放块、实际播放/设备回调、块到达、取消发出/确认/静音/计算退出，各自时钟及观测范围。不能用null sink、软件sleep或模型完成代替实际声学播放。C17的教学计算由calculations负责，不复制或执行。

此文仅记查找范围和下一步，3-5实验未完成。Qwen宽预算补测运行期间不启动其他GPU任务，以免影响该批时序。全书最终跨session论文增补复核仍待首轮完成。
