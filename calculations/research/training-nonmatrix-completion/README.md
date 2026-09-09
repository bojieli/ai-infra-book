# Qwen3-8B训练非矩阵补账候选

独立候选入口 `src/infra_calc/topics/training_nonmatrix.py:calculate`，专用 `markdown(result)`。复用原 `training_matrix`，原矩阵和参数状态字段完整保留。只读共享目录；`source-bindings.json`绑定公共配置、实现及原官方来源，`public/`提供可迁模块、测试与5个扁平场景。

## 本次完成范围

固定Dense Qwen3-8B，无dropout，默认128输入位置。逐项计入：hidden与Q/K RMSNorm的前后向、SwiGLU、有效因果softmax及score scale、RoPE及每step共享位置表、两条残差与Q/K/V和gate/up分支的梯度汇合、声明逐query-head dK/dV输出到KV头的归并、embedding scatter-add、有效标签mean CE、明确FP32 AdamW及BF16回写。

这些是明确数学/保存策略，不宣称是某固定PyTorch后端实际使用的save_for_backward或融合算子。GQA单独归并对应本候选“每query-head独立产生梯度再求和”的路径；若换成把GQA归并吸收进收缩维度的融合矩阵，需要替换对应算法口径，不能把两者工作重复相加。

CONTRACT.md给出公式。重要计数：RMSNorm每行dx为6D，shared gamma的梯度为(2R−1)D；SwiGLU反向6次普通算术/元素；softmax反向4K−1再加K次scale；mean CE反向每行V+1，特殊函数另列。AdamW每参数14次普通算术、1次sqrt，两个pow与6次公共系数算术每step一次。数值参考已把beta complements和decay coefficient提到循环外，明确匹配14P+6。

参数更新使用声明BF16模型权重、FP32 gradient/master/m/v；这些常驻值直接复用原training_matrix，绝不再加一遍。FP32梯度/master/m/v每参数读16bytes、master/m/v写12bytes、BF16模型副本写2bytes；是声明更新接口，不是实测HBM。

## 默认数值与策略

B1/T128、全部标签、dense head：原矩阵工作5,826,907,471,872 FLOPs不变；新增前向普通算术565,679,488、反向1,095,199,872、AdamW 114,670,295,046；已计矩阵加普通算术为5,943,238,646,278。exp/sigmoid/rsqrt/sqrt/pow等特殊函数不混入此数。

默认非线性保存对象在前向末尾合计1,043,550,720bytes。它只是声明的FP32 z/r、SwiGLU保存值、有效因果概率与loss概率子集合，排除了矩阵保存输入、live gradients和其它临时，不能当完整模型峰值或所有其他算法的下界。

`recompute_silu`只保存g/u，进入该非线性反向时重算s和a，多一次sigmoid与一次乘/元素。事件表逐对象记录保存、局部重算分配/释放、最后使用释放，再取子集合max；不会把各阶段峰值相加。它不代表全层activation checkpoint。

标签数减半但dense head矩阵不变；compact head才少执行词表矩阵行。compact反向先清零完整B*T×H FP32梯度，再把S行梯度scatter回去；全buffer清零与选中行read/write已分列，不能省掉未监督行的零值定义。mask身份不由标签数量推造，实际gather布局和atomic冲突未知。

## 数值验证与公共接入

14项测试已通过，含本机torch2.7.0/FP64的独立autograd、unfused AdamW与有限差分。RMS dx/dgamma、SwiGLU dg/du、softmax及score scale、mean CE都作独立数值对照；另验masked loss梯度scatter、GQA头梯度归并、RoPE转置。AdamW覆盖step1/7、weight_decay为0/非0及零梯度参数；原矩阵完全相等、mask/compact、保存/重算事件、scenario重放与非法输入也通过。数值差分epsilon为1e-6；测试中所有上游梯度明确FP64。

```sh
python -m unittest discover -s calculations/research/training-nonmatrix-completion/tests -v
PYTHONPATH=calculations/src python calculations/research/training-nonmatrix-completion/freeze.py
```

数值审计需要torch；公共测试在缺该可选依赖时明确skip数值部分，已保存的本轮审计为14通过/0跳过。计算器本身仅用标准库和既有项目模块，不引入训练运行依赖。

五个场景：默认、dense半标签、compact半标签、SiLU重算、8192输入。JSON/MD完整保留原矩阵、各新增计数、typed/data操作和所有lifetime事件。public模块与冻结calculate相同；portable tests只改import路径。

## 原实验仍未完成的范围

V4训练分支尚未实现；量化训练、梯度累积/裁剪、loss scaling、分布式通信、全部typed转换/复制、真实优化器/allocator/内核执行都未闭合。故完整training FLOPs、完整activation peak、HBM和时间仍为unknown。这个候选补Dense已明确的数学和保存策略，不把原实验3-6整体勾选。
