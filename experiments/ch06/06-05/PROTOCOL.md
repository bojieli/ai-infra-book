# 6-5 CPU Gloo / GEMM 同机资源竞争协议

执行前固定：M2 Max、Torch2.14 CPU、四个独立rank、Gloo loopback TCP、每rank Torch intra/inter-op各2线程。消息4096／4194304／67108864字节FP32；同一rank固定随机二进制有理数输入，GEMM [16,4096]×[4096,4096]。它是Qwen宽度的合成投影计算控制，不是训练权重、完整模型或GPU计算。

每个消息大小比较 comm-only、compute-only、shared 三种模式；正式5个配对区组，区组内三模式按seed605随机顺序。每模式/消息先一次预热，共9预热+45正式组。另开独立smoke（4KiB三个模式各一次）先确认future回调/数值/生命周期，不能合入正式性能。相同矩阵反复调用，通信输入每组重新填rank与trial关联值；不复用已归约结果。

comm/shared执行真实async all_reduce SUM，get_future.then记录完成回调；shared提交后立即实际CPU GEMM，最后等待两者。compute-only实际GEMM，comm-only不执行GEMM。每组之前真实barrier，之后所有验证不计入该组执行窗口。回调是主机可观测完成时间，可能晚于实际Gloo完成；不能把async提交、callback或区间重叠等同GPU通信/网络链路独占。

所有通信输出逐元素要求等于rank和；所有GEMM输出逐元素等于独立FP64矩阵参考。输入是小整数/16，FP32乘积与此规模累加均能精确表示，要求零差，不用宽松容差。保存生成seed、输入SHA、实际完整输出和FP64参考；全部输入不变在运行后再次SHA核对。原始每rank时间/CPU/输出验证全留；对比报告完整组从最早rank开始到最晚rank结束及rank分布，不能混合不同模式/消息的非配对最小值。

总进程树RSS≤8GiB、运行≤10分钟，自身新session watchdog；只终止自身任务，不操作其他进程。Mac无CPU硬亲和，线程数不是独占CPU核；共享主存/OS背景明确。最多5正式区组，不按结果追加择优。没有GPU、网络跨机或NCCL、没有修改calculations，融合allreduce/RMSNorm与完整模型等原范围保留。
