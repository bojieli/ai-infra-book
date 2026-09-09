# 实际Agent控制器资源采样

复用已知修复任务定义，新跑模型工具循环以补旧轨迹未采集的资源证据。Qwen3-8B固定vLLM配置，最多12轮，保留全部结果和最终检查，不假定成功。50ms采样当前控制器VmRSS及user/system CPU；分相位记录model/tool/control，模型阶段仍可能有控制器CPU工作。tool子进程CPU用RUSAGE_CHILDREN在工具前后的差，仅覆盖已回收子进程，不将活模型worker算入。此RSS包括Python/Torch/tokenizer和引擎前端，不是干净沙箱内存，也不含全部进程树/显存。

模型时间、CPU时间、RSS各保留单位；不把CPU时间当墙钟、模型等待当全机空闲、不做到达率/容量预算。采样本身在控制器内有开销，不声称零扰动。已有旧实验保留，calculations不调用。初始化与基线测试在采样循环外。
