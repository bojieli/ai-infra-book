# 执行前协议：有效第3步检查点恢复后的40步追赶

准备阶段不启动训练。实际执行必须使用launch.py的--execute标志，并由root在V4资源调度允许时启动。只用原RTX主机CPU8–9、Torch2.10.0+cu128的CPU路径、intra/inter1、无CUDA设备可见。三条路径顺序执行，启动前全机MemAvailable≥28GiB，运行中≤25GiB只停止自身树；各自身进程组RSS≤1GiB、时限120秒；只管理自己新session的进程组，绝不触碰其他任务。

原历史代码SHA2dd21009f42a8b5ca4d582c8be608db0684800f225eddb59fb54ee9886a3ef8a。模型Linear(1024,1024)→Tanh→Dropout(0.1)，CPU FP32，torch.manual_seed(1007)，AdamW lr0.001其余保持Torch2.10默认，torch.set_num_threads(1)。独立数据Generator seed107，每步按顺序生成输入与target各[16,1024] torch.randn；MSE mean、backward、AdamW step，不新增clip或改变数学路径。

固定三个独立进程顺序：from_seed从原seed真实更新1–43；from_fault3从故障路径有效checkpoint-1(cursor3)真实更新4–43共40步；from_normal23从正常路径有效checkpoint-2(cursor23)真实更新24–43共20步。历史checkpoint payload只读复用，不复制或改动。所有文件先核对固定SHA，目标张量先置零再DCP load，恢复模型/完整Adam/全局RNG/data_rng/cursor，不通过重新初始化代替恢复。

历史锚点：第3与23步全部11项tensor字节SHA必须与封存expected.json精确一致；第23/43步loss分别必须等于历史1.2358448505401611/1.2407095432281494。旧第43步没有完整状态，因此最终43全状态只与本轮独立from_seed新参考比较，不冒充历史完整张量核对。三路径重叠部分逐步input/target、loss、全状态SHA精确相同，并对所有保存的状态.pt离线逐tensor重算SHA及torch.equal。任何历史锚点不匹配则保留科学兼容性结果，不改容差或历史数据。

记录真正的DCP load区间、状态安装、每步实际更新、整个追赶窗口、首次恢复更新及新进程总寿命。输入与状态哈希、观察性状态快照会影响窗口时间，update_s只计原数学步（含randn）；另报含观察开销窗口，不能把两者相减解释成存储成本。原故障与今天的新进程并非连续运行，绝不拼接旧monotonic时钟作停机时长。单次每路径用于机制证明，不能排名训练吞吐或大模型外推。

无新故障注入，不重新运行原async_save，不做预期损失/保存周期计算。结果目录必须新建。小代码语法检查属于准备，不加载Torch或启动模型；实际首次执行兼做历史环境兼容性检验，无需另造不匹配的缩小模型smoke。启动调试失败在成功替代后删除，真实历史不兼容或数值门槛失败保留。
