# C55 Qwen8 GEMM 保存对象与生命周期补账

基于公共 training_pipeline_schedule / training_matrix / training_nonmatrix 和固定 Qwen3-8B config。此候选补全**公共矩阵VJP所需的forward输入身份**，不是推测某后端autograd保存清单，也不声明完整训练allocator峰值。

## 精确矩阵输入身份

R=b×T，H=4096，Q=32，KV=8，d=128，F=12288。每层新建七个逻辑身份：

| 身份 | 形状 | 需要它的矩阵VJP | 最后语义使用 |
|---|---|---|---|
| input_norm_weighted | [R,H] | q_proj/k_proj/v_proj dW共享 | 三投影backward完成 |
| q_after_norm_rope | [b,Q,T,d] | QK的dK | QK backward完成 |
| k_after_norm_rope_unique | [b,KV,T,d] | QK的dQ | QK backward完成 |
| v_unique | [b,KV,T,d] | PV的dP | PV backward完成 |
| attention_context | [R,Qd] | o_proj dW | o_proj backward完成 |
| post_norm_weighted | [R,H] | gate_proj/up_proj dW共享 | 两投影backward完成 |
| swiglu_product | [R,F] | down_proj dW | down_proj backward完成 |

另有stage3的final_norm_weighted[R,H]供lm_head dW。每个线性dX依赖resident W，W不再当activation计一次。反向upstream是临时梯度，不是forward保存。

公共attention_probabilities已经保存每层三角因果P，PV的dV直接引用该ID，不重建P副本。GQA以唯一KV头保存K/V，声明group-aware逻辑访问和已有head-gradient归并；不假定后端repeat_kv物化张量也常驻。325个矩阵实例逐一给出operand IDs，不用“每层一个经验常数”代替清单。

## 不能伪称别名的对象

norm的已保存z/r中，z=x*rsqrt(...)，不是gamma*z。GEMM需要加权后输入，必须单独保存或恢复。SwiGLU已保存a/s/u中a=SiLU(g)，同样不等于a*u；不能直接用a身份冒充down输入。

同一norm加权输入由三个QKV矩阵共享，post norm输入由gate/up共享，P直接复用已有保存ID，避免重复计费。残差加法不需要为自身VJP多保存一个forward residual值；norm VJP依赖其已保存z/r。

## 两种策略

`save_inputs`：上述新身份均按FP32参考保存。

`recompute_products`：仅重算两个每层gamma*z、一个每层a*u，以及最终head的gamma*z；其余Q/K/V/context仍保存。每microbatch额外标量工作严格为 L×R(2H+F)+RH，矩阵和特殊调用新增0。

若原activation_policy=save_nonlinear，a/u从已有对象直接读。若是recompute_silu，原来的sigmoid及a重算提前到down dW之前，并将已有a/s两向量保持到SwiGLU backward；它们只执行一次，保留原公共算术和两向量workspace，不再次增加sigmoid/a计数。新增a*u只有一向量，额外workspace=max(RH,RF)×4。

这是声明的局部重算与持有顺序，不是完整层checkpointing。不能用减少保存字节推导自动加速；用户提供的F/B服务时间必须包含选择策略对应的全部工作。

## 归stage与释放

每层对象归layer//9；head归stage3。对象给出真实语义producer/last_consumer；重算节点给before_event及release_event，明确必须在矩阵backward开始前恢复，不能在消费结束后才生成。

结果有正向/反向层内语义顺序。反向逐层处理，down product用完释放后才恢复post_norm产品，再恢复QKV输入；共享产品保持到全部对应GEMM完成，因此只需一个产品临时缓冲。原recompute_silu临时对与它不同，另有既存预算。

公共事件只有stage F/B级service，无法确定每层准确时间。故每个持久保存对象采用F START→B END保守包络；重算产品workspace在该stage B全程保守保留。对象级包络仅为原stage追加预算的展开，**没有再加入combined intervals第二次**。combined峰值由统一区间事件求和，字段与summary一致。

这种reservation并不证明实际同时分配全部值；完整allocatorpeak保持null。

## 仍排除

Token/label IDs、瞬时梯度、参数和optimizer状态、cast/packing与GQA后端物化、communication进入算子内部的拷贝、workspace以及其他非saved临时量。补齐矩阵forward输入不会使这些量自动归零。

FP32保存是明确的无舍入数学参考策略，不冒称固定BF16训练kernel实际使用该dtype。

## 验证

4测试：所有325矩阵实例一一覆盖；253新逻辑身份及stage/形状；QKV/MLP共享、P和GQA去重；两个保存策略×两个非矩阵策略的算术/特殊调用守恒；实际乘积恢复与不能别名的反例；独立时间开区间峰值枚举，GPipe/1F1B均验证；场景重放。

仅添加独立research候选，不修改公共模块。来源和公共依赖SHA纳入public/bindings.json。
