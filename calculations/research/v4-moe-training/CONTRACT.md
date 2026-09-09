# V4-Flash 一个固定选择 MoE 层的完整数学 VJP

固定官方 model.py:545-647 与 Flash reference config；H=4096，F=2048，E=256，K=6，共享专家1，score=sqrtsoftplus，route_scale=1.5，clip_limit=10。layer_id区分前3层hash与其后bias/topk，默认layer3。

## 路由与负载

复用公共 v4_training_primitives.router_vjp，覆盖logits→sqrtsoftplus→选中归一化→scale及其VJP。单层计数按同公式列出，不把该primitive原43层总量再加进来。共享/路由专家均完整回传路由权重上游，hash也保留gate score梯度。

固定唯一ID是局部光滑分支。bias只改变topk选择，不影响被选原score；固定分支主损失没有其连续梯度，但它的auxiliary-loss-free更新和辅助目标不是“不训练”。选择边界/平局未求导。

histogram复用公共routing_counts校验：每n_e<=R、总和RK。balanced明确token i选(iK+j)%E，concentrated选前K；外部counts仅作为调用者条件直方图，未验证checkpoint tid2eid或实测路由。不得把这些负载写成生产观测。每专家列n_e及三矩阵shape，空专家算术0但参数仍常驻。

## 专家图及反向

源码Expert：gate=W1X，up=W3X；gate只上截断+10，up双侧[-10,10]；a=SiLU(gate)，p=a*up。路由专家z=route*p，再进W2；共享专家直接z=p。**权重乘在F维，不是down之后H维**。output按路由expert累加，再加shared。

从W2反向取dz：路由分支dp=route*dz，droute=dot(dz,p)。随后da=dp*up、dup=dp*a、dgate=da*[sigmoid+a(1−sigmoid)]，用保存的clamp masks选择梯度。W1/W3分别回传，专家输入梯度相加；最终加上router输入梯度。数值夹具不在clamp kink处断言唯一导数。

输出sum的梯度向所有选中专家及shared分发，不另加不存在的可学习H维combine乘法。未选专家本microbatch的主损失梯度为0，不表示optimizer永远不更新其权重。

## 计数

R=B×T，A=RK：

- router矩阵forward2RHE，dX+dW共4RHE。
- 专家三矩阵forward6(A+R)HF，backward12(A+R)HF，每n_e可直接核对。
- router forward=R(3K−1)，非hash另RE bias加；backward=R(5K−1+3E)，RE sigmoid调用另列。
- 所有专家SwiGLU forward2(A+R)F，路由权重乘法另AF。
- SwiGLU backward6(A+R)F；route局部VJP=A(3F−1)，仅一次，与primitive一致。
- clamp前向比较3(A+R)F，反向mask选择2(A+R)F，非FLOPs。
- source output从零累加(A+R)H；输入反向内部两投影相加及从零scatter后加router，共(2A+3R)H。

输入gather/scatter和where/bincount的整数范围独立列示，不将比较/索引当Tensor FLOPs。parameter梯度矩阵自带跨n_e归约，不另加一次scalar累加。

## 保存去重

X一份，以保留的dispatch token/slot int64作为逻辑索引视图供专家dW，不另保存RK个X副本。source topk ID是int64、hash ID是int32；selected IDs字节按分支分开。where的token/slot每assignment各int64保存供反向索引。

router保存logits、sqrtsoftplus scores、选中p和scaled weights、sum denominator。专家保存a/s/up、clamp masks、未加权p；路由专家另外保存weighted z供W2 dW。p是route梯度必需输入，不能仅保存z后不计代价地假设可除route恢复。shared的p本来就是W2输入，未另存z。

保存值统一声明FP32数学参考、bool masks按1byte；不是源码实际activation dtype或allocatorpeak。临时gradient、全部参数/optimizer状态、dispatch物化和完整memory traffic排除。

## 量化已知与未知

官方报告§5.2.1已披露FFN专家QAT的FP32master→MXFP4→FP8，以及对同一FP8权重反向、STE传master。不能把它写成完全未知。固定推理代码本身用FP4 routed experts、共享专家沿默认Linear类型且没有训练backward实现。

本参考去除舍入，用全精度参数数值验证，**不是该QAT的数值复现**。不能把披露的专家STE任意推广到router/shared全部cast。具体scale/clip梯度实现、kernel gradient精度、shared路径细节以及完整优化器/auxiliary/MTP目标仍需独立界定。

## 验收

4测试：全输入/router logits/全部router、shared、routed参数与PyTorch FP64对照（含饱和与不饱和clip）；小图所有参数/输入中心差分；inactive专家零主损失梯度；balanced与concentrated同总算术不同负载和访问参数；hash层未删router梯度；F维route计数；场景重放。

仅一个MoE层的固定选择主损失图，不把完成的local VJP说成完整V4训练。
