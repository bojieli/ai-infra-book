# V4 Compressor positive-start 可微时间图

## 固定执行路径

源 `model.py:316-376` 的 positive start_pos 分支用 `kv.squeeze(1)` 写一个状态槽；本候选每步严格一个token，绝不是并行chunk。ratio支持固定4/128，rotate=False主attention分支。score初态已经含APE，不能在读取初态时再加一次。

定义输入初始KV/score状态、新token序列、两投影权重、APE、norm gamma、每次emit使用的固定RoPE频率、压缩输出上游和最终状态上游。返回全部这些可微输入的联合VJP；频率和整数调度不求训练梯度。

- ratio128：每步写槽p%128，p+1整除128时池化全部128槽，状态不重置。
- ratio4：每步写槽4+p%4；emit时池化previous[0:4,:D]及current[4:8,D:]，然后将current全部2D通道复制到previous。
- emit位置为 p+1-ratio 的块起点RoPE，而不是p。
- output数量精确为 floor((S+N)/ratio)−floor(S/ratio)。

结果timeline给每次写入、被覆盖版本、pool依赖版本/通道与copy别名；最终状态也给出版本ID映射。源buffer物化和数学版本别名不混作独立内存峰值。

## 初态叶子与历史图

`initial_state_mode=leaf` 表示初态独立数学输入，返回其梯度。`external_history` 表示调用者必须把返回的初态梯度送回prefill/历史producer，再将共享W/APE/gamma梯度相加。两者执行同一局部VJP；区别是梯度所有权，不能伪造没有调用的history计算量。

不默默detach，也不声明训练实际采用不截断历史。任意有限初始KV和有限score可以作为叶子；score中−∞是固定mask常量，梯度为零。每次emit各feature必须至少一个有限score。调用者的实际状态有效性不能单凭start_pos推断。

最终KV/score状态上游与压缩输出上游独立，均可非零。由caller提供这些adjoint不表示已经实现其未来业务损失。

## 反向状态更新

按时间倒序处理：

1. ratio4 emit后的previous<-current复制，先将previous和current两份post-copy梯度合并回pre-copy current，再清空pre-copy previous梯度；不能只把一份传回，不能把已被copy覆盖的旧previous继续连到最终状态。
2. 将emit输出经过逆RoPE、RMS、池化和softmax的梯度加入当时池化槽位。ratio4旧previous虽然被copy覆盖，仍通过这次emit参与梯度。
3. 取出本步写入槽的KV/score梯度给新token投影；把该槽对旧值的梯度清零，因为赋值覆盖并不依赖旧值。
4. 求两投影的W/X梯度和当前位置APE梯度。最后剩余状态梯度就是对初态的VJP。

这一顺序区分copy覆盖、pool读取与write覆盖，不能统一用原地buffer的最后值做反向。

## 每步/每emit工作量

令R=B×N，E=B×emit数，D=512，H=4096，w=(ratio4?2D:D)，m=(ratio4?8:128)。

- 两投影forward=4RHw；两投影各dX/dW合8RHw。
- 每新token APE加法w，共Rw。
- 每emit/feature full-slot softmax+pool=5m−2；其反向=6m−1。
- 向已有状态梯度加pool两支路：2mED次加法。
- ratio4 copy反向两状态数组归并：2×ratio×w×E次加法。ratio128没有copy项。
- APE按新token位置共享归并：w[BN−min(N,ratio)]；初态score的APE历史梯度归外部producer，不能再算入这里。
- RMS forward=E(4D+1)，backward=7ED+Dmax(E−1,0)；E=0合法。
- RoPE每向3E×rope_dim；X两投影梯度合并RH。
- exp=EmD，max比较=ED(m−1)，rsqrt=E，特殊调用不算FLOPs。

实际代码FP32 linears不证明后续cast/FP8模拟的梯度。本候选只无舍入数学，cast surrogate=null。

## 保存策略和bytes

声明每次emit保存所用gathered KV快照和概率，加norm xhat/r；每个新token保存X供dW。这样旧状态被后续写覆盖后仍有明确值可做VJP，不假设后端自动保留原地缓存。

初态与最终状态接口各为两组B×m×w FP32值，单列，不自动与saved加成独立复制。频率常数按emit共享B。结果同时列new-slot写、ratio4 prev复制的读写、反向清槽字节，只覆盖明确操作，不是总流量或allocator peak。

未计初态历史producer、未来最终状态consumer、注意力core/indexer和其余模型；actual_peak及完整训练仍unknown/false。

## 数值证明

4测试实际通过，无skip：

- ratio4 S3/N6、S4/N9以及ratio128 S127/N3，以PyTorch clone/cat写出独立时间图，压缩输出和**最终状态双上游**共同回传，核对初态KV/score、新X、Wkv/Wgate、APE、gamma全部梯度。
- ratio4 fresh prefill3或5 → online直到9token，把online初态VJP接回原prefill候选，输出及共享参数/输入梯度与完整9token prefill一致。
- ratio128先127token尾块线性/APE状态 → 129个online token；将状态梯度接回尾块producer，与完整256token ratio128参考的输出及全部梯度一致。
- 计数、emit整数边界、场景重放、未计history和cast边界检查。

prefill→online的比较针对压缩输出和对应损失梯度，不声称最终所有闲置状态槽逐值一致：source在线可能留下上一块的闲置current值，fresh完整prefill对应未写槽可为初始化值。独立双状态上游autograd测试另验证实际online最终状态VJP。
