# V4 attention 外围投影反向

固定源为 `sources/deepseek-v4-flash/inference/model.py:183-195`、`:232-245`、`:440-545`。本候选采用 world_size=1 的全尺寸数学路径；不计 TP 通信或分片优化。它是一个 attention 外围，不是整个 43 层累计。

## 图与范围

输入 X[R,H]，R=B×T，H=4096；q_rank=1024，heads=64，d=512，groups=8，o_rank=1024，rope_dim=64。

1. Qa=X Wq_aᵀ → **带参数 gamma** 的 RMSNorm → Qr。
2. Qr Wq_bᵀ → reshape[heads,d] → **不带 gamma** 的逐 head RMS → 最后64维正向 RoPE。
3. KV=X Wkvᵀ → 带 gamma 的 RMSNorm → 最后64维正向 RoPE。
4. core(Q,KV) 与 core_vjp(Q,KV,dO) 是调用者接口，其数学/矩阵/保存全部排除。
5. core 的每 head 输出最后64维做 **共轭频率** 逆 RoPE。
6. 连续展平 head×d，再分8组，各组4096输入经 Wo_a 投影到1024；组结果展平8192经 Wo_b 到4096。

`qr` 也送往 ratio4 的 indexer，输入 X 也可能进入 compressor。本候选不把这些支路梯度擅自置为真实训练中的零：仅声明无 indexer/compressor 的 ratio0 attention 路径，固定 config 的前两层和末层可满足。对于压缩层，本候选的矩阵形状仍可复用，但完整梯度还必须加这些额外支路，当前 coverage 明确 false。

core 可以是独立验证的 tied-KV core，但本次数值 oracle 使用跨 head 的非线性函数，验证接口连接不是默认 identity/stop-gradient。不会因此宣称完整 attention core 或完整 V4 training。

## 矩阵账

每投影单独列 forward、dX、dW，各为2Rmn；Wo_a 另外乘独立组数8。dW 跨 R 行归约已经在矩阵里，不再列额外参数 reduce。

| 投影 | 输入宽 | 输出宽 | 组数 |
|---|---:|---:|---:|
| Wq_a | 4096 | 1024 | 1 |
| Wq_b | 1024 | 32768 | 1 |
| Wkv | 4096 | 512 | 1 |
| Wo_a | 4096 | 1024 | 8 |
| Wo_b | 8192 | 4096 | 1 |

输出组维必须正确：不能给每一组复制完整 32768 输入。每项结果都有输入/权重/输出 shape 和三项 FLOPs。

## RMS 与 RoPE

RMS 以 xhat=x*r，r=rsqrt(mean(x²)+eps)；gamma 存在时 y=gamma*xhat。

反向 ghat=dy*gamma（无gamma时直接dy），m=mean(ghat*xhat)，dx=r*(ghat−xhat*m)。有gamma时 dgamma=dy*xhat，并跨行归并。

- 带权 n维 RMS 每行前向4n+1、反向7n；gamma 再加 n(R−1) 的跨行归约。分别作用在 q_rank 和 d 上。
- 无权 head RMS 每行前向3d+1、反向5d，行数R×heads。
- rsqrt 分别单列，不折算成 FLOPs。
- RoPE 是邻接两维 real/imag 复数乘法，仅最后 rope_dim 维；每pair 4乘2加，共6 FLOPs。正变换 VJP 用逆变换，逆变换 VJP 用正变换。
- Q、KV、O 三处共每向3R×rope_dim×(2heads+1) FLOPs。固定 cos/sin 参数无训练梯度，频率构建未计入，不能把 setup 反复乘入请求工作。
- X 的 Q 与 KV 梯度两路合并额外 RH 次加法。

## 量化边界

源码 Linear 会依权重 dtype 进入 FP8/FP4 activation quantizer 和特定 GEMM。Wo_a 源码明确用 BF16 einsum，即使 checkpoint 存 FP8；RMS 输出及 RoPE 原地写回也有 cast。这里定义去舍入实数 VJP，FP32 保存契约，FP64 数值验算；没有替这些操作发明统一 STE，没有声称 source kernel 逐值等价。

本候选的 `cast_surrogate_gradient=null` 与 `quantized_kernel_equivalence=false` 必须进入公共结果/报告。源码的 norm gamma 建为 FP32，并不推出其他全部训练激活实际都是 FP32。

## 保存与事件

只保存本外围所需的数学身份：共享 X 一份；q_rank 的 xhat/r 和加权输出；逐head xhat/r；KV xhat/r；逆旋转后的 core 输出供 Wo_a dW；组输出供 Wo_b dW。

Q、KV、概率和sink概率属于刚完成的 core 子账，此处全部排除。core 原输出无须再为本外围多存一份：本外围保存的是逆旋转后的输入。源的原地覆盖必须在实际训练策略里另作实现；本参考保留所需值，不假设 allocator 自动保留。

频率常数 cos/sin 共4T×rope_dim bytes，batch/head共享，独立列于保存和数之外。权重/参数梯度、cast缓冲、backward临时量与workspace排除。事件顺序与释放依赖见结果 lifecycle；保存和数不是完整模型峰值。

## 验收

3测试，FP64自动微分验证五组权重、X、两种gamma全部VJP；groups=1/2验证分组输出；全小尺寸输入/参数中心差分；RoPE伴随内积恒等式；矩阵计数、重放及core保存排除检查。

执行 `/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/research/v4-attention-projections/public/tests -v`，当前3pass/0skip。无torch时autograd显式skip，不算数值验收。
