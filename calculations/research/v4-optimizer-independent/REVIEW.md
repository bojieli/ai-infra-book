# V4 optimizer 独立审查

结论：**声明的条件优化器算术/参数清单可验收；未发现阻塞问题。** 本次没有修改作者候选或公共文件，也不将选定参数组覆盖等同完整真实优化器实现。

模块SHA：`f920785ea14541365664914f35aa141cb160fdb7c9ab976402e11c21b1e3863a`。

`audit.py` / `results.json`记录671830项独立检查，作者原5测试通过、0skip。绝大多数检查对应Flash/Pro原始checkpoint tensor逐项归属/去重，不能把检查数量理解成同等数量不同数学定理。

## 来源判断

直接阅读已锁报告Algorithm1、§2.4 Eq28和§3.4.1，并核报告PDF/text哈希及所有来源锁bytes/SHA。报告确实给出momentum `mu*M+G`、Nesterov `mu*Mnew+G`，8轮(3.4445,-4.7750,2.0315)后2轮(2,-1.5,.5)，按sqrt(max(n,m))*gamma缩放与decoupled decay。

Adam例外确实包括embedding、prediction head、全部RMSNorm、mHC静态bias/gating factors。候选没有把所有参数统一套AdamW，也未给router balancing bias虚构普通梯度更新。

报告明确NS可用BF16 matmul，候选FP32接口只是参考声明；报告还说明完整矩阵owner、ZeRO bucket/padding以及stochastic BF16同步，本候选没有把无rank布局的这些信息换算成虚构每卡bytes或固定padding保证。

## 参数分组和packed形状

独立遍历Flash/Pro全部header，I8只允许出现在packed expert w1/w2/w3矩阵，恢复末维×2后计逻辑参数；scale和hash元素分开排除。逐tensor匹配唯一候选group，验证base/MTP精确清单、group数量/参数及family守恒。

每个expert投影仍是独立矩阵，未把256/384专家合并做NS。Wo_a分组核对固定source reshape及o_groups/o_lora_rank；采用source_groups作Muon矩阵划分是**显式训练假设**，不是报告直接规定的唯一optimizer分组。stored_matrix另场景保留，数学变化没有掩盖为性能优化。

attn_sink矩阵化、hc_head_fn归属默认unresolved；主动选row_muon或head策略才进入条件更新。所有四场景参数集合、MTP选择及未决计数保持一致。不会要求作者猜测未公开规则来移除unknown。

## 十轮矩阵/标量独立验证

按每个实际group重新计算：每轮A=XXᵀ、B=AA、CX共 `4n²m+2n³` FLOPs，十轮按独立矩阵数累计；标量每矩阵 `31nm+30n²`，再加Adam14P与共享系数6+2。逐group、全summary和normalization sqrt次数均一致。

额外使用独立Scalar运算计数器执行参考算法，GEMM当黑盒仅记录mnk：五种shape、两种orientation，普通scalar与候选精确相等（另外2次共享decay）；30个实际GEMM的shape/FLOPs和per-role接口bytes相等。转置是视图/代数选择，未计为已经发生的HBM复制。

数值oracle不复用作者三GEMM分解：先对归一化Nesterov矩阵SVD，仅在奇异值上执行十轮五次多项式，再重建矩阵。五种shape、两方向、epsilon0/1e-7，与候选更新和momentum一致，最大绝对差 `2.220446049250313e-16`。采用显式lr=.125增强更新差异的可见性，不依赖小学习率掩盖误差。

## 存储与范围

master=4(MuonP+AdamP)，Muon momentum=4MuonP，Adam moments=8AdamP，input gradients=4(MuonP+AdamP)，都只覆盖选定更新组。逐矩阵X/A/B/C/CX大小及GEMM重复operand按role计数正确；不证明这些临时量一定同时驻留。

unresolved/router-bias更新、cast后的训练副本、分布式同步、padding/replication、实际HBM与peak仍未计。`full_optimizer_exact=false`和actual_peak null正确保留。梯度已产生是此账入口，不包含梯度产生或accumulation。

## 重放和接入说明

四个冻结场景序列化后解析对象完全一致；JSON会把Python系数tuple转换为list，比较前进行标准JSON规范化，这是类型表示变化，不是数值变化。

可接入有限参数更新参考，不能据此声称V4完整forward/backward/optimizer/runtime全部完成。数值测试需要本机 `/Users/boj/miniconda3/bin/python` 的torch环境，当前5pass/0skip证据不能由无torch解释器的结果替代。
