# 10-1 FSDP2 CPU真实状态分片：正式运行前协议

预检PyTorch2.14两进程已实际前反向及AdamW通过。首次torchrun --standalone解析到198.18地址发生TCPStore失败，自己的launcher终止后改127.0.0.1/lo0成功；原日志保留。正式用固定CPU设备/Gloo，不修改FSDP实现，不作为GPU/网络性能证据。

固定seed1001随机FP32 SwiGLU FFN，hidden512/intermediate1536、三矩阵无bias，全参数AdamW(lr=.001, weight_decay=.01, foreach=False)。全局32行数据，每步seed1002+step，按rank等分，MSE mean；2/4进程与reshard_after_forward真/假，4配置，各3步。参考程序在所有测量结束后独立执行未分片全局batch，并重组逐rank参数、梯度、Adam一阶/二阶矩对照。预设atol2e-6、rtol1e-4；任何失败完整保留，不修改门槛。

每阶段保存参数/梯度/优化器实际类型、global/local形状、placement和底层storage字节；同阶段按storage身份去重。模型forward入口记录FSDP已聚合后的参数，训练后记录分片。这些可见状态不是所有临时缓冲的峰值。

每rank真实Torch CPU profiler从模型初始化覆盖三步，保存memory事件、collective和算子。根据原始事件区分观测到的分配高水位、临时聚合和阶段可见存储，不把进程RSS、profiler计数和逻辑张量bytes混为一谈；profile还含状态保存开销，需标注范围。性能不作排名。完整逐步数值文件在本目录可独立分析。

Mac96GiB、仅CPU，其他服务未隔离。600秒每配置上限，保存控制器/各rank退出与错误；每配置新进程。所有源与参数在运行时hash记录。目录不覆盖既有结果，不执行calculations，不改变Qwen全模型/DeepSpeed卸载等尚未完成的原范围。
