# 4-2 Apple MLX 低比特路径（运行前固定）

M2 Max GPU、MLX affine 4-bit、group_size64。随机seed402，单矩阵768×2048（out×in）原FP32正态除sqrt2048，再转FP16量化；激活batch1/8/64/512由同一512×2048 FP32夹具截取后转FP16。不是模型训练权重或专家路由复现。

两主路径共用完全相同packed uint32、FP16 scales/biases及FP16输入：quantized_matmul(transpose=True)；dequantize到FP16然后普通matmul。另测常驻反量化矩阵matmul，明确其额外展开存储。每路径5预热、30正式重复，固定种子随机交错条件；每次建新运算图，eval并synchronize后停止计时，测GPU实际完成的主机墙钟。逐条保留时刻，不把lazy调用入队当完成。

量化pack/scale/bias合并API时间单列，不能假造内部scale单独kernel时间；激活FP32→FP16转换、反量化、展开矩阵计算、直接低比特计算、反量化+matmul端到端、带激活转换端到端均实际测量。主路径使用预打包权重，离线量化时间不混入每请求。

数值门槛在小检查前固定：同一反量化FP16矩阵+FP16激活以CPU NumPy FP64 matmul独立参考；两个GPU路径对它均需逐元素atol=.01、rtol=.01。packed nibble独立解包后按FP32 scale/bias运算再转FP16，与MLX反量化逐元素atol=.0001、rtol=.001。门槛不按结果修改。对原FP32激活×原FP32权重另报量化总误差，不以此门槛宣称模型质量通过。所有失败原样保留。

内存分别报数组实际nbytes与MLX active/peak/cache API；后者为分配器视角，含本进程其他存活数组，不等于GPU物理总RSS。权重载入／生成、CPU参考、冷启动编译不混入正式热计时。本机未固定频率或隔离后台进程，不能外推整模型性能、RTX路径或一般最优策略。
