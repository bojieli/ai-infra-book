# 梯度转换与真实 CPUAdam 更新：执行前协议

目标：同一 Qwen3-8B gate 形状 [12288,4096]、BF16 梯度，比较 GPU→主机传输之前或之后转 FP32，再用固定 DeepSpeed0.18.0 CPUAdam 更新。真实 RTX/x86 PCIe 平台，不是 GH200/SuperOffload，不是完整 ZeRO-3 训练或链路吞吐扫描；计算项目不重复。

夹具为固定seed10101初始化的随机FP32矩阵，GPU BF16线性层，32行输入及标量内积损失；每步seed10110+step生成输入和输出cotangent，执行真实前反向得到BF16梯度。非训练好的模型，不报告模型质量。两路径执行相同3步，初始状态相同；每条路径1组预热、5组正式、1组单独profiler，正式交错随机顺序seed10102。smoke另用[768,256]，不进入正式统计。

cpu_cast：BF16梯度复制到pinned BF16主机缓冲，等待D2H完成，再copy转换到pinned FP32梯度。gpu_cast：GPU预分配FP32缓冲copy转换，再D2H到相同pinned FP32梯度。两者随后真实CPUAdam(lr=.001,betas=.9/.999,eps=1e-8,AdamW weight_decay=.01)，CPU将更新后的FP32参数转pinned BF16，并H2D更新GPU层。所有阶段串行同步，测完整已就绪梯度→更新权重可用墙钟及各阶段墙钟。前反向、首次JIT、初始化分配、数据准备、独立参考、哈希验证不计入卸载墙钟。首次Adam状态初始化在各组第1步内计入，统计按step分开，不能混为稳态。

逐步用相同实际梯度在独立torch.optim.AdamW CPU FP32参考上更新，全部参数/一阶矩/二阶矩逐元素固定atol2e-6、rtol1e-4验证；传回梯度须与原GPU BF16梯度展开逐位相同，更新后GPU BF16权重须与CPU实际更新值转BF16逐位相同。保留误差、全张量SHA及输入seed/shape/版本，夹具保存生成所需真实输入及初始参数。失败立即终止并保留，不调整门槛。

记录实际张量设备、dtype、pinned、独占底层storage字节及CUDA allocator峰；后者与CPU逻辑状态/RSS明确区分。profiler记录真实D2H/H2D、cast和CPUAdam范围，不从理想时序猜测重叠。GPU显存预算<3GiB、CPU线程4；共享既有服务与8-5实验，不做隔离因果性能结论。不停止既有服务，不修改共享依赖。

## 完成原批后补存张量证据

原14组42步运行91587已exit0，两路径逐步全SHA一致。为支持完全离线重算，追加独立3步capture_tensors.py，不计入原性能；保存每步完整梯度/参数/两Adam矩，先逐项比对原records的SHA。此补存不改变原输入/更新或数值门槛，也不替换正式样本。verify_tensors.py使用独立CPU PyTorch AdamW核验。
