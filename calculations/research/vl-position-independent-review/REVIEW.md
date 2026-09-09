# 静态图像位置桥接独立审查

**核心位置、mRoPE delta与KV/生成计数正确；可接受数值桥接。接入前应收紧两处setup预算路径说明。** 未修改作者候选或共享文件。

独立验证没有复用作者坐标公式作为唯一判据。`check.py`从已固定的官方modeling_qwen3_vl.py提取三个实际方法，在CPU Torch运行；41组矩形尺寸/文本尾块/混合图片顺序均逐坐标、逐delta匹配，另123次consumed decode与官方方法匹配。锁定原件SHA与候选SHA见verification.json；未加载模型或权重。

## 数值与分类

官方helper按merged H/W形成三轴网格，时间坐标静态为起点s，高宽为s+y/s+x。图像之后current_pos推进max(h,w)，不是图像token数h*w。候选这一点正确；非空静态prompt的最大位置+1等于最后cursor。

令P为全部语言位置数，delta=max(position)+1-P。decode输入的KV位置仍是P+i，旋转位置是P+i+delta。输出G个token只需要G-1次后续输入消耗，最后一个输出没有被再次送入模型。因此示例P2000、delta-1520、下一旋转480、生成128时最终KV2127均成立，不能把KV减去delta。

位置构造的加减乘/比较属于整数或控制/索引工作，不是矩阵FLOPs；arange产生的整数次数不等于GPU整数指令数。候选没重算vision/language矩阵是正确范围。bytes按int64语义接口解释，不是HBM流量或同时存活峰值；stack/cat/assign与view应分别保留。必须在接入schema中明确input_ids/position_ids为int64，否则源码zeros沿input_ids.dtype而候选固定8byte会有不同契约。

## 两处有限纠偏

1. **直接decode setup计数不完整。** 官方1136–1147的无mask路径，每次先arange(P+i,P+i+1)，再expand视图、to设备，delta.repeat_interleave(batch_size/self.rope_deltas.shape[0])，最后三轴相加。独立执行观察每次确有长度1的arange；候选只列3次整数加法与24byte输出。建议追加每次8byte arange输出，以及batch1时8byte重复delta的语义输出（repeat数为1不等于可无条件宣布零分配），并把device转换是否复制标为设备条件。可选择明确只统计position_add子步骤，但需把arange/repeat/to列为未计项。无需猜测分配器或HBM访问。
2. **纯文本fresh请求不是相同direct-model调用图。** 官方compute_3d_position_ids在无image/video、无rope_delta的fresh text请求返回None，由语言模型准备位置；候选text-only仍列出get_rope_index的zeros/cat/max等预算。数值0..T-1及delta0正确，不代表这些helper节点实际被调用。最小处理：把候选预算域限制为至少含一张图的静态请求，text-only只返回坐标等价结果并标出实际setup预算另属语言fallback；或显式选择“调用get_rope_index工具函数”模式，不能继续把它称为fresh direct-model路径预算。

另一个已正确保留的边界：generation wrapper四平面拼接是另一条路径，不能与当前direct-model预算混合。无需因此阻塞已核三轴桥接，也无需展开全部generate。

以上是有限预算范围修正，不是矩阵数值错误。下游已有mrope_table应接三轴值，不能把桥接的坐标构造与RoPE sin/cos或应用矩阵重复计入；feature-cache命中也不允许省略请求特有的坐标桥接。
