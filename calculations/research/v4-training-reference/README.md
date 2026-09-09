# V4-Flash 训练参考：路由与有限 Sinkhorn 子账

本候选实现固定官方推理数学图中可明确求导的两个局部路径。`calculate(batch=1, tokens=128)` 返回每层、每 token 的累计账；`router_vjp` 与 `sinkhorn_vjp` 提供独立手写反向数值参考。没有完整训练 FLOPs、优化器 FLOPs 或整模型激活峰值：这些字段为 null。

固定来源及版本哈希见 `source-review.json`，完整路径和训练差距见 `CONTRACT.md`。模型有 43 层、256 专家、每 token 6 专家、前 3 层 hash 选择；mHC 为 4 路、每层两个位置、20 次有限迭代。参考 config 未显式给出的 `hc_eps=1e-6` 取同版本 `model.py` 的 ModelArgs 默认值。

## 精确计数契约

令 R=B×T，L=43，E=256，K=6，H=4096，F=2048，c=4，V=c(c+2)=24，n=2I−1=39。矩阵乘加统一 2 FLOPs；标量加减乘除各 1；sqrt/softplus/sigmoid/exp 调用以及比较、索引操作独立列出。特殊函数内部实现没有折算进 FLOPs。

### Router

源路径为 logits → sqrt(softplus) → 选择 → 选中分数归一化 → ×1.5。bias 只作用于选中索引；在固定选择的连续区域内没有主损失连续梯度，不代表训练时 bias 不更新，也不覆盖选择边界与辅助损失。hash 层仍有原始路由分数，不能把这些层的 gate 梯度删掉。

- 前向分数矩阵 2LRHE，反向 dX、dW 两矩阵合计 4LRHE。这是这三个具体矩阵的尺寸推导，不是整个推理工作乘 3。
- 前向选中分数归一化与 scale：每行 3K−1；非 hash 层额外 E 次 bias 加法。
- 反向先把上游乘 scale，再用 dscore=(g−dot(g,p))/sum(score)：每行 5K−1。对全部 E 个 logits 计算 `dscore*sigmoid(z)/(2*sqrt(softplus(z)))`：3E 个标量 FLOPs 加 E 个 sigmoid。
- 专家内路由权重实际乘 F 宽 SwiGLU 激活，再送入 down projection。其反向 dactivation=w*g，dweight=dot(g,activation)：每选中专家 3F−1 FLOPs。该项没有包含其余专家反向。

手写 router 夹具要求唯一选中 ID；候选未读取或证明全部 hash 表实际 ID 唯一，结果因此明确是一条声明的局部数学路径。

### mHC split/Sinkhorn

源码为 pre=sigmoid+eps、post=2sigmoid、comb 行 softmax+eps，随后一次列归一化，再 19 次行/列归一化。epsilon 保留，不能把它代换成理想双随机矩阵投影或无限迭代的隐式梯度。

参考算法把归一化分母每向量计算一次并保存。若 y=x/(sum(x)+eps)，则 dx=(g−sum(g*y))/(sum(x)+eps)，每 c 宽向量 4c−1 FLOPs；初始 softmax 的 VJP 同为 4c−1。顺序逆传完整 39 次归一化。

- 每出现行前向：5c+(6+2n)c²；全模型乘 2LR。
- 每出现行反向：7c+(n+1)(4c²−c)+V，分别是 pre/post sigmoid、softmax 与归一化、mixes 梯度。
- 每子层参数归并：三个 scale 点积合计 2RV−3；base 梯度按行归并 V(R−1)。全模型乘 2L。
- 保存 FP32 子集：每出现行 4[2c+c²+n(c²+c)] bytes，含 pre/post sigmoid 值、最初 softmax、每次归一化输出和分母。mixes、base、scale、外部 mHC 输入及反向临时量不在此集合；它不是生命周期峰值，也不能与其他层所有激活直接相加当硬件容量。

手写 Python 参考用于值/梯度验证，Python 的 sum 初始化、列表构造、重复 max 调用不是逐指令工作量规范；账依据上述明确化简及分母复用策略。

## 验证与重放

本机数值环境使用 `/Users/boj/miniconda3/bin/python`，Python 3.11.4、PyTorch 2.7.0。测试必须实际导入 torch；缺少依赖直接失败，不把 skip 当数值验证通过。

```sh
/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/research/v4-training-reference/tests -v
```

测试包含 FP64 自动微分与中心差分对照：两组路由选择；bias 只参与 top-k 选择与 hash 保留分数梯度；hc=2/4、迭代=1/2/20、非零 epsilon 的全部 mixes/base/scale VJP；结果输入重放与范围断言。数值验证不证明训练运行时等价或全部计数的硬件实现。

## 下一有限工作

1. 外层 hc_pre 与 hc_post 联合 VJP：x 同时经线性、RMS 系数、pre 混合与 residual 支路，必须正确累加。当前 `full_mhc_x_weight_vjp=false`。
2. 显式函数式压缩/稀疏注意力训练图及 compressor 重叠状态依赖；推理代码原地缓存不可直接当训练激活策略。
3. Indexer 的训练目标和对应梯度路径。主注意力通过整数 top-k 索引没有连续的 index score 梯度，不能据此宣称训练时 indexer 不训练。
4. 公开报告已经披露 QAT STE 和多数参数 Muon、embedding/head/RMSNorm AdamW。仍需具体量化尺度/clip 规则与 Muon 每矩阵更新账，不能统一套 AdamW，也不能把这些已知事项写成完全未披露。
