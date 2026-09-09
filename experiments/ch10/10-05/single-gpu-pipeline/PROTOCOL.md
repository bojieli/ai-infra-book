# 单卡四进程变体：执行前协议

原四张GPU/NCCL实验仍未满足，本目录新增独立变体，不覆盖原协议。目标是实际运行官方Megatron Core 0.16.0的非交错1F1B、四进程四阶段，在同一RTX GPU执行真实前向/反向/SGD。进程间后端Gloo，所有rank绑定CUDA:0；不等价于物理四卡、NCCL链路或吞吐收益。先用两进程实际CUDA tensor send/recv与all_reduce验证当前构建支持，失败则不启动训练。

固定源码commit 3bec9aa97dda898d16ff5a89bac0ed2b6682b172。使用原样调度/P2P源码，并运行前核对两文件SHA；parallel_state默认backend=None继承全局Gloo，不修改框架源码或伪造通信。

36个宽16真实残差层，每阶段连续9层，8个微批、每批序列8/batch1、FP32、TP/DP/CP1。每层seed105000+层号，输入/目标seed105。每微批MSE除8累计、SGD lr0.01一次更新。与同权重未切分36层GPU autograd参考逐元素对比输出、所有参数梯度和更新值；门槛abs≤1e-6+1e-5×abs(reference)，全数值有限。保留全张量，而非只存布尔。

保存实际profiler CUDA trace、autograd save/unpack/release事件和allocator snapshot。引用生命周期按真实storage去重，参数storage排除；wrapper释放不等于底层设备存储释放，CPU提交时刻不当GPU完成时刻。模型输入/目标和CPU参考张量共存；四进程同卡且观测有扰动，不报告流水加速比或物理通信气泡。

监督器限时3600s、自身GPU64GiB、RSS进程合计40GiB，系统可用内存至少24GiB。需要四rank退出0、全张量数值通过、四份原始trace/snapshot/lifetime齐全并复核与图QA，才称此变体执行完成。没有Qwen模型训练、微批扫描或多卡性能结论。

## 实跑前补充：无流水GPU参考路径

Gloo CUDA张量预检失败，四进程变体不启动。允许显式--stages 1 --backend nccl执行同36层、8微批、相同参考与数值门槛的官方forward_backward_no_pipelining；一rank NCCL、同样保存完整张量/trace/lifetime/allocator。该执行仅是后续四阶段的GPU正确性及生命周期基线，不称1F1B或跨stage训练完成。
