# V4 HCA ratio128 Compressor 完整块 prefill 训练参考

## 官方证据与选择

固定 `model.py:279-376` 定义 Compressor。`compress_ratio==4` 才启用 overlap；HCA 的128分支投影到D，CSA的4分支投影到2D。官方报告本地归档 `references/text/deepseek-v4.txt:652-665` 也明确 HCA 不重叠，`:1375-1378` 给 ratio4/128。代码原件与报告文本 SHA 纳入绑定。

本批完整实现 **ratio128、start_pos=0、rotate=False、T为128正整数倍** 的单个主attention compressor可微参考。T不完整时直接拒绝，不能把其缓存尾块梯度悄悄丢掉后说已完成。B样本独立，共享Wkv/Wgate/APE/gamma；标量参数梯度按所有B×blocks归并。

## 实际图

Wkv/Wgate 都是固定源码显式 FP32 Linear。X转FP32后得到 K和Score，各为[B,T,D]；按[B,C,128,D]分块。

APE形状[128,D]，对每块加一次。**softmax沿128个token轴、逐feature独立**，不是沿D维，也不是每块仅一套共享概率。

对块c、feature j：p_ij=softmax_i(score_ij+APE_ij)，u_j=Σ_i p_ij K_ij。随后u做带gamma RMSNorm，再对最后64维用块起始位置的频率做RoPE。默认块位置是0、128、256……，不是块结束token。

输出量化模拟不纳入可微参考；官方路径还有pool结果转原dtype、norm输出cast、RoPE写回cast、非RoPE维FP8 quant-dequant。本候选不为它们假定STE，也不声称低精度内核逐值等价。

## 反向和工作量

从输出梯度逆RoPE、RMS VJP得到du_j。随后：dK_ij=p_ij du_j；dp_ij=K_ij du_j；δ_j=Σ_i p_ij dp_ij；dScore_ij=p_ij(dp_ij−δ_j)。dAPE按B和块归并，dX是两投影支路相加。W梯度是全部token行矩阵归约。

记R=B×T，C=B×T/128，H=4096，D=512，r=128：

| 项 | FLOPs |
|---|---:|
| 两个投影forward | 4RHD |
| 两个投影各dX/dW | 8RHD |
| APE、softmax、pool forward | 6RD−2CD |
| pool及softmax backward | 6RD−CD |
| APE梯度归并 | rD(C−1) |
| RMS forward | C(4D+1) |
| RMS backward及gamma归并 | 7CD+D(C−1) |
| RoPE每向 | 3C×rope_dim |
| 两路dX相加 | RH |

exp=RD次，max比较=CD(r−1)，rsqrt=C次，单列不折FLOPs。softmax一列3r−1（subtract r、sum r−1、divide r），pool2r−1，APE加r，合6r−2。反向dK和dp各r，softmax4r−1，合6r−1。矩阵按2mnk；helper从0累计参数不是额外声明的算术规范。

## 保存、在线边界

保存X、投影K、每token/feature概率、RMS的xhat/r；分数logits、APE加后结果和输出不属于本VJP必要保存。频率常数按块共享batch单列。保存子集不等于实际训练peak。

源码 ratio128 full prefill 无remainder时**不写** kv_state/score_state。后续online每调用必须1token，在start_pos%128写槽位，满块才发出压缩结果。新块在emit前覆盖全部槽位，因此数值上不需要旧完整块的state；这不等于已经定义跨请求/恢复状态的训练梯度。

结果单列B活跃样本的状态切片大小（kv和score各4BrD），不是ModelArgs max_batch_size预分配全量。压缩cache的2CD bytes是源码BF16语义，不与FP32参考保存相混。source的buffer所有权/缓存持久化也不加入训练saved subset。

尾部T%128!=0会把当前不完整块写state，但没有对应输出。若该state以后参与损失，它的投影、APE梯度仍需沿后续调用回传；这项尚未实现，输入目前拒绝。在线恢复初始状态是叶子还是历史图、是否detach、何时释放，需要单独训练契约。

## ratio4 与下一有限项

ratio4绝不能仅替换上述r：Wkv/Wgate输出2D，APE[4,2D]；当前块后D通道和前块前D通道组成8slot窗口。首块前4slot K=0、score=−inf，不贡献梯度；其后每token的两个半通道分别供当前/后一压缩输出。prefill最后完整块的前半还会写rolling state，尾块/未来输出可能使它保留梯度。

下一有限可计算项是完整块、start_pos=0的ratio4函数式重叠图：保留两半通道独立梯度、前后块归并与首块mask；明确末块前半未参与当前返回输出但会进入future-state边界。随后再扩online/尾块。当前ratio4字段false，不扩称整个Compressor训练完成。

## 验证

4tests通过0skip：真实128 ratio的两块FP64自动微分全部X/Wkv/Wgate/APE/gamma、非overlap小ratio2纯教学夹具全参数中心差分、非法尾块和ratio4拒绝、完整块按online槽位覆盖顺序组装的前向等价。最后一项不验证未定义的恢复状态VJP。

公共就绪模块正常import上一外围topic的矩阵/RMS/RoPE值与VJP helper；不继承其calculate工作量。模块、依赖、原件、三个场景和完整报告在public/bindings.json绑定。共享代码只读。
