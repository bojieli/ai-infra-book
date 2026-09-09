# GPU 执行前固定协议（尚未执行）

版本：Megatron Core core_v0.16.0，commit `3bec9aa97dda898d16ff5a89bac0ed2b6682b172`。禁止替换或修改调度器/P2P 代码以绕过设备要求；脚本校验这两个已安装文件的 SHA256。

模型：36 个真实可训练残差块，每块 `x + 0.1*tanh(linear(x))`，宽度16，每阶段连续9块，4级流水。不是 Transformer、Qwen3，也不表示 Qwen3-8B 的算量/容量/精度。此模型只检验官方流水调度器的最小张量及训练接口。

对照：未切分 PyTorch 同模型逐微批 autograd 参考 vs 官方 Megatron 非交错 1F1B。全局 batch=8，DP=TP=CP=1，PP=4，微批大小1，微批数8，序列长度8，FP32，无 dropout、重计算、混合精度或TF32。每层 CPU Generator seed=105000+层号，输入和标签 seed=105；两路数据逐元素相同。损失为各微批全部元素的 MSE，再除8累计。一次 SGD 更新，lr=0.01，无动量或weight decay。不是填满排空/1F1B性能对比，也不是微批扫描。

事前数值门槛：所有输出、每一参数梯度和更新后参数逐元素满足 `abs(actual-reference) <= 1e-6 + 1e-5*abs(reference)`，且参数/梯度有限；任何一项失败退出非零。`elementwise.pt` 保留实际值和参考值，不只保存摘要。改变门槛须生成新协议，不能覆盖失败记录。

观察：每rank保存 profiler Chrome trace、真实 autograd saved-tensor wrapper 的保存/读取/析构事件和 CUDA allocator snapshot。事件含 storage pointer，必须去重且排除参数 storage；不能直接把 tensor_bytes 相加叫激活峰。wrapper 析构是 autograd 保存引用释放，不是底层 storage 归还设备的证明。CPU host_monotonic_ns 是提交/回调时刻，不能当 GPU kernel 完成时刻；需结合 profiler CUDA 时间和 allocator snapshot。CUDA allocated、reserved 与进程RSS分别记录。RSS包括参考执行的历史高水位，不能作纯流水峰值。

资源共存：参考先执行并释放GPU模型，再执行流水；参考结果、初始权重副本保留在CPU；流水期间输入/目标、阶段参数、优化器和autograd保存张量共存。所有观测有扰动，末阶段输出转CPU也引入同步。只用于正确性和生命周期检查，不据单次记录做因果性能排名。GPU交接操作员须另记录独占/共租、硬件拓扑及其他进程。

成功门槛：四rank checks 全通过、torchrun退出0、四份trace/snapshot/lifetime/elementwise齐全后，仍需查看真实时间轴和分配生命周期并QA，才可以声称此小模型路径执行完成。本轮只做源码、语法和CPU阻断验证，未达到该成功门槛。
