# Training pipeline 公共候选独立审查

结论：**在声明的 PP4、固定九层分区、条件服务时间和部分保存预算范围内通过，可合入该有限计算块。** 未发现需要修改候选数学的实际反例。不能据此认定完整训练运行时或完整激活峰值已实现。

冻结模块 SHA256：`82377cb6bb3bd2bbc33634964e89f4c67765cc87790aac68bb600a8294aa241c`。

独立脚本 `audit.py` 产生 `results.json`：9120项检查、14份已交场景、16组额外随机边界场景；作者原5测试亦通过、0skip。候选与依赖 manifest 的原件hash全部核验。此次只写独立目录，没有修改作者候选或公共源码。

## 事件、依赖与资源

逐一枚举 stage×microbatch 的F/B和边界A/G，核对事件总数14M+5与唯一ID。独立检查F→A→下游F，B→G→上游B，每个B等待自身F，全阶段B结束后才开始U。GPipe最早B不得早于全局最后F。按资源逐区间检查无正时长重叠，包括单共享双向链路与六条独立方向链路。

非交错1F1B的warmup=min(P−s−1,M)，随后F与最早尚未完成B交替，最后drain；候选满足声明顺序。均衡F=B=1、无通信/更新时，M=1/2/4/8/16两策略都满足2(M+3)闭式。这是特定条件下的闭式，不用于覆盖任意不均衡服务。

随机场景含零时长事件、不均衡F/B、快慢通信、shared half-duplex、两种保存策略。没有出现依赖倒置、资源重叠或负寿命。这里审查的是作者明确的deterministic earliest-ready列表调度；不证明它是全局最优通信仲裁。

## 通信与保存生命周期

没有复用作者的 `_peaks` 算法作为oracle：独立取所有边界时间，枚举相邻时间之间的开区间并直接求活跃对象和，逐stage核对峰值。半开区间和同刻释放规则一致。

每条send在producer END建立，到transfer END释放；每条receive从transfer START到consumer START。即使传输时长为0，receiver也可能等待消费者，候选没有把这些等待缓冲漏掉。saved subset从F START保留到B END；recompute工作区按声明为整个stage B保留，属于有意保守的reservation。

**部分预算边界仍成立且不能移除：** receiver在consumer START后进入算子内部的使用、GEMM保存输入、参数/梯度/优化器状态、完整临时张量及allocator workspace未被预算。报告的peak只针对明确interval的reservation集合；`complete_training_activation_peak_bytes=null`正确。额外字节输入不自动将整个模型预算变成完整。

## 实际工作量、参数与更新

逐项对照公共 `training_nonmatrix` / `training_matrix_original`：每个矩阵forward及其dX/dW在四个stage的和守恒；每个非矩阵标量与每类特殊调用逐key守恒，没有只比较一个总FLOPs就判通过。

36层按每stage九层拆分；embedding归stage0，final norm/head/loss归stage3。RoPE表项从每microbatch移出，保留为每step一次setup；其准备/分发时间由条件setup_seconds承担，不是假定免费硬件操作。

权重参数按真实 `qwen3.weights(config)` 归属核验，合计等于公共optimizer参数数。每microbatch各自VJP，M−1次梯度相加，等大小/等监督量microbatch再统一除M一次；AdamW完整公共记录保持每step一次，不乘M。stage参数级14P和全局共享系数不能重复相加，当前对象保留了正确层次。

全部saved对象的ID/内容集合与公共子账精确相同，未跨stage重复归属。原data_operations完整保留；它们没有被伪装成已展开的全部内存流量或硬件时间。

## 接入时保留的限定

1. 服务seconds是用户条件输入，不是根据不完整标量/矩阵总量推算的实际运行时间，也不是官方GPU吞吐承诺。
2. GPipe/1F1B默认是同步、无陈旧权重、一次逻辑更新；不代表实现了interleaved、异步、MoE或所有长序列训练扩展。
3. “exposed transfer”是同一调度规则下移除transfer时长后的makespan差，不是所有链路busy时间相加。
4. 空闲时间混合fill/drain、依赖和顺序等待，当前没有错误归因为单一瓶颈。
5. 此次通过不能勾选完整C55扩展或全训练activation覆盖；有限GPipe/1F1B事件计算入口可以验收。
