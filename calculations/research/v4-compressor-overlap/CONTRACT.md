# V4 ratio4 重叠 Compressor：fresh prefill 与返回状态联合 VJP

固定 source `model.py:279-376`，报告 §2.3.1（本地文本约495-540行）披露两组通道和重叠压缩。本候选不改 ratio128 或此前源码；复用外围topic的纯数学MV/RMS/RoPE helper，不复用其算力总量。

## 真实重叠与状态边界

输入 B×T×H，ratio=4，投影宽 **2D**，APE[4,2D]。第c块压缩输入为 **前一块的前D通道** 加 **当前块的后D通道**，组成8slot×D；首块前4slot是KV=0、score=−∞常量。softmax沿8个token槽逐feature独立，不能沿D求softmax。

T允许任意正整数，包括小于4。C=floor(T/4)，tail=T%4。本次仅返回C个压缩输出，同时按固定源码写状态：

- 若C>0，kv/score_state[0:4]保存最后完整块的全部2D通道。
- tail>0时，[4:4+tail]保存尾块全部2D通道。
- 其余位置按**fresh initialized state**保持KV零、score−∞常量。这里明确不是复用旧请求buffer的语义。

数学接口除了压缩输出梯度，还接受上述每个状态写入的KV/score上游梯度。该梯度来自调用者，可以是未来消费的VJP，也可为零；候选不推造未来执行。未写入的常量状态没有训练初始状态梯度。

这使末块前半和尾token的梯度不被删掉：它们即使没有参与当前压缩输出，也可经返回状态参与后续损失。没有把“尾块尚未压缩”等同“该token没有梯度”。尚未实现任意restored初态、positive start_pos在线序列或跨请求历史策略。

## 联合反向

压缩输出依次逆RoPE、RMS得到pool梯度，再求dKV、dscore。按8槽映射scatter回原token的对应半通道，首块常量槽梯度丢弃。随后将返回状态的KV和score梯度加到这些相同的投影梯度身份上，再求Wkv/Wgate、APE和X梯度。

同一token的前D与后D是两组参数输出，不互相混淆。最终X依赖两投影，额外两路相加。APE按token位置模4跨batch/token归并。

## 声明的共享表达式与源码差额

源码为最后完整块state另外计算一次 `score+APE`，又为全部压缩块计算一次；本参考先给每个token计算 `biased_score=score+APE` 并共享其值。这是明确的公共子表达式复用，不称逐指令照搬源码。

参考forward APE=2BTD次加法。源码若C>0还额外8BD次加法，结果字段 `source_extra_forward_ape_additions_for_last_complete_state` 保留该差额。反向在共享biased_score处先合并状态与压缩输出梯度，再归并APE；不能再给同一项加第二次梯度或错误省掉state贡献。

## 逐项计数

令R=BT，N=BC（全部样本完整块数），V=4max(0,2C−1)（每样本有效压缩槽数），S=(C>0?4:0)+tail（每样本状态写入token数）。

- 两投影forward=8RHD；两个投影各dX/dW共16RHD。
- 公共APE forward=2RD。
- 每压缩块/feature保留完整8slot计算：softmax23、pool15，合38ND。
- 每块/feature反向dKV8、dp8、softmax31，合47ND；首块无效槽的局部结果丢弃，未假设跳过这些算术。
- 压缩输出投影梯度scatter：2BVD次加法（KV和score各一条）。
- 返回状态投影梯度scatter：4BSD次加法（每token的KV/score各2D）。这些数组从零初始化，明确逐项 `+=`，没有第一项免费归约假设。
- APE按共同biased_score归并：2D[BT−min(T,4)]。T<4只涉及已使用位置；B样本共享同一APE。
- RMS forward=N(4D+1)；backward=7ND+D max(N−1,0)。N=0不错误产生负数工作量。
- RoPE每向3N×rope_dim；X两路梯度合并RH。
- exp=8ND，max比较=7ND，rsqrt=N，独立于FLOPs列示。

梯度投影数组KV/score均按BT×2D清零，合16BTD bytes；APE4×2D清零另列。其余临时量/参数梯度初始化不是完整流量账，不虚构遗漏项为零。

## 保存和类型

保存X、投影KV（2D）、8slot概率、RMS xhat/r。频率常数按完整块、batch共享单列。首块padding不对应额外可训练token。

状态是独立输出接口：源每活跃样本两个[8,2D] FP32状态缓冲，返回有效写入是S×2D两组值。它们的字节大小单列，不把source buffer物化、函数式值别名和训练saved重复相加成峰值。KV状态值与投影KV相同，score状态与共同biased_score相同；是否真的零拷贝是实现选择。

Wkv/Wgate源为FP32，但pool后原dtype cast、norm输出cast、RoPE写回和非RoPE FP8模拟未定义训练surrogate，仍为null。此批仅rotate=False主attention compressor，不包括indexer的Hadamard/FP4支路。

## 数值验证与下一步

4测试，T=1/3/4/5/8/9全部X/Wkv/Wgate/APE/gamma的FP64自动微分，包含状态损失；T5全参数中心差分；尾token只有state梯度时非零、无state梯度时为零；未写状态的上游不影响参数；首块和无完整块计数边界。

下一有限项才是把任意初态作为显式输入、逐token更新形成可微时间图，并验证prefill→online组合；必须说明初态叶子/历史图与截断策略，不能把当前fresh接口直接当作已支持所有在线训练。
