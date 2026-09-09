# 实验3-6：Qwen3-8B训练非矩阵补账契约

第一阶段只交此可审查契约；不改共享源码。固定官方Qwen3-8B配置和已核 `training_matrix.calculate`。原题仍含V4-Flash，该分支不由本候选替代，也不据Dense子账宣称完整训练投入已算完。

## 输入与输出

候选入口拟为 `calculate(batch=1,tokens=128,supervised_tokens=None,head_strategy='dense',activation_policy='save_nonlinear',adam_step=1,learning_rate=...,betas=(...),epsilon=...,weight_decay=...)`。

沿用已有训练口径：T个输入位置与调用方在shift/padding/mask后提供的S个有效标签。`0<S≤B*T`；dense head执行B*T行，compact head显式gather S行。label位置若要计算gather/scatter索引量，必须提供明确mask；仅S不会推造标签身份。默认先固定dense head，compact作为显式分支。

参数/master/gradient/moment声明固定为BF16/FP32/FP32/FP32，非框架默认声称。AdamW每次对全部参数进行稠密更新，即未出现token的embedding行也有明确零梯度语义；不混入稀疏优化器。累积microbatch、梯度缩放/裁剪、分布式归约、随机dropout暂不自动添加。

返回：原training_matrix原封保留；新增逐算子forward/backward普通算术、特殊函数、integer/data操作、明示保存对象和策略附加重算；独立AdamW更新及状态读写；新合计为“已计矩阵+已计普通算术”，完整training FLOPs、HBM、allocator peak与step latency保留unknown。矩阵梯度绝不再乘3或重复并入。

## 数学路径与计数约定

FMA=2；加/减/乘/除各一次普通算术，exp/sigmoid/log/sqrt/rsqrt/pow、比较、cast、gather/scatter均单独计数。公式以实数/FP64小例独立验算，声明FP32非矩阵中间和梯度计算；不推断某后端每条指令或BF16内部计算位宽。

### RMSNorm

每行宽D：`r=(mean(x²)+eps)^(-1/2)`、`z=x*r`、`y=z*gamma`。前向复用公共Qwen的逐元素公式，保存本声明反向需要的FP32 z和r。Q/K Norm按实际head_dim与行数，两个层RMSNorm和final Norm按hidden维；gamma共享方式分别按源shape。

反向：`g=dy*gamma`、`a=sum(g*z)/D`、`dx=r*(g-z*a)`；`dgamma=sum_rows(dy*z)`。每行dx普通算术6D；dgamma跨R行需 `R*D` 次乘和 `(R−1)*D` 次加，共 `(2R−1)D`。同一gamma所有使用位置在其参数副本内累加，不误按query头复制gamma参数。gamma gradient在层间不能合并成一份。

计数证明和数值梯度必须分别覆盖hidden Norm与Q/K Norm共享gamma两个case。保存z/r是明示参考反向算法，不能把它冒充锁定框架实际save_for_backward对象。

### SiLU/SwiGLU

每元素 `s=sigmoid(g)`、`a=g*s`、`z=a*u`。

默认保存a、s、u。反向 `du=dy*a`、`da=dy*u`、`dg=da*(s+a*(1-s))`，6次普通算术/元素。前向2次乘/元素加sigmoid调用，不重复计三个投影矩阵的梯度。

唯一可选重计算策略 `recompute_silu`：前向仅按本非线性子图保存g、u，在其反向入口重新计算s和a，再执行相同反向。因此明确多一次sigmoid和一次乘/元素。保存量差异只针对该子图对象；其它消费者或矩阵反向若仍保留g/u，不由此推导全模型显存下降。禁止自动添加“整层checkpoint”而未展开整层重放。

### 注意力softmax与缩放

对每条有效因果行宽K，`p=softmax(scores*scale)`；无dropout。反向 `dot=sum(dp*p)`、`ds=p*(dp-dot)`，`4K−1`普通算术；乘scale传回QK scores另加K次乘。max选择在稳定softmax求导中不额外引入一条可见max梯度路径，数学梯度由上述式直接定义。

按所有层、query heads、B与每行实际K累加，保持有效因果范围。矩形masked backend、FlashAttention重算、GQA repeat物化不由该数学式推造；QK/PV四个矩阵梯度已在training_matrix中。本阶段默认保存概率；不声称其实际从HBM读写，保存作用域在PV backward之后至softmax backward结束。

### Loss

采用有明确S有效标签的mean cross entropy。每有效行对V词表做stable logsumexp并减目标logit；loss跨S平均。dense head仍对B*T行执行，非监督行的CE按本声明选择跳过，梯度tensor的零填充和scatter另计data操作。

为便于独立计数，前向显式得到概率p并保存；反向 `dlogits=(p-one_hot(target))/S`，每行只目标位置一次减法、全部V位置一次缩放。每行前向max比较V−1、subtract V、exp V、sum V−1、log 1、加max/减目标2、保存概率的除V；跨S的mean另列。不能把log/exp算成1 Tensor FLOP。compact head的输入/梯度gather-scatter根据显式mask单列，不用监督比例裁掉主干。

### 其他必要非矩阵边

Residual反向是分发/累积梯度：是否需要新增一次加法取决于此声明图中已有梯度buffer，不能把forward residual加法机械乘3。RoPE是固定旋转的转置线性作用，其Q/K backward元素算术单列；位置sin/cos不是训练参数，频率表初始化与每训练step复用分开。Embedding backward按每个token/h维scatter-add定义，重复token造成的同参数累加仍需计数；没有token IDs时只给逻辑贡献量，不推atomic/冲突/唯一行数。还须计输出head/FFN等分支输入梯度的必要求和，不把它们遗漏在“矩阵梯度都齐”之后。

## AdamW声明式

FP32 master θ、gradient g、moments m/v：

`m=β1*m+(1−β1)*g`

`v=β2*v+(1−β2)*g²`

`mhat=m/(1−β1^t)`；`vhat=v/(1−β2^t)`

`θnew=θ*(1−lr*wd)−lr*mhat/(sqrt(vhat)+eps)`

按此未融合逐元素写法：每参数14次普通算术与1次sqrt；超参数公共系数和两个pow按每step单列，不乘参数数。最后FP32 master转BF16模型参数是一次typed cast/参数，写回2bytes/参数。grad清零是明确可选的步边界操作，默认不计为优化器公式的一部分。测试应分别验证weight_decay=0和非0、step1与后续步、零梯度仍衰减/更新moment。

参数状态常驻复用training_matrix已有BF16+FP32grad/master/moments，不能重复相加；每参数更新读写接口和转换另外给出，不把固定常驻容量当逐step流量。

## 保存与生命周期

先给上述明确子图的saved对象清单、dtype、shape、保存事件和最后使用/释放事件；可选SiLU重算只影响其明示对象与运算。矩阵反向需要的输入、Q/K/V、权重、整个网络执行次序及临时归约workspace必须分开。尚未完整枚举全网络必要存活集合时，输出“已声明保存对象小计”而非全模型峰值。若声称某局部集合峰值，必须从具体事件顺序求max，不能把各段max相加。

## 独立验收

1. 小FP64张量对RMSNorm的dx/dgamma、SwiGLU的dg/du、softmax的ds、mean CE logits梯度做有限差分及独立自动微分；非均匀dy、不同维度、多行共享gamma、极端但有限logits、标签mask必测。
2. AdamW用独立标量循环/可信公开实现对照明确公式；张量更新、bias correction与BF16回写typed次数分开。
3. 原training_matrix结果逐字段保持不变。S减半但dense head矩阵不变，compact才减少head矩阵；forward/backward scalar变化符合明确mask策略。
4. save_nonlinear/recompute_silu输出梯度相同；后者只在反向入口增加sigmoid和乘法，保存对象差异与事件表一致。
5. 公开Qwen8配置/源码绑定，不下载权重。先完成Dense补账，V4训练、完整激活peak、实际优化器/后端执行保持后续范围，原3-6不整体勾选。
