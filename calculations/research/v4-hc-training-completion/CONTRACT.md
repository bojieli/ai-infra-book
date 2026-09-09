# V4 mHC 外层联合反向契约

## 固定来源和范围

来源为 `calculations/sources/deepseek-v4-flash/inference/model.py:675` 的 hc_pre、`:686` 的 hc_post 以及同版本 `kernel.py:372` 的 split/Sinkhorn。本候选依赖上一份冻结 `v4-training-reference`，不修改或重新计算其内部账。来源、依赖和候选哈希记录于 bindings.json。

**这是完整的 mHC wrapper 数学 VJP，不是完整 V4 训练。** 源代码有 dtype 转换和推理内核；这里定义 FP32 实数数学参考，并用 FP64 验证。在低精度/量化的前向取值点如何对 cast 和舍入定义训练梯度，仍需独立的训练策略契约。本候选没有断言该策略等同实际 V4 训练。

每个 wrapper 中，令输入 X∈R^(c×H)、N=cH、V=c(c+2)，W∈R^(V×N)。

1. a=W vec(X)，r=(mean(X²)+norm_eps)^−1/2，mix=a*r。
2. 复用冻结有限 split 得到 pre、post、C。
3. y_k=Σ_i pre_i X_ik。
4. z=f(y)。f 可以是实际 RMSNorm+Attention 或 RMSNorm+MoE；本候选把 f 及其 VJP 作为调用者接口，其工作全部排除。
5. O_jk=post_j z_k+Σ_i C_ij X_ik。

最后一式严格对应源 `comb.unsqueeze(-1) * residual.unsqueeze(-2)` 按 dim=2 求和的方向：**先输入索引 i，后输出索引 j**。对 C 做错误转置会给出错误梯度。

## 联合反向

给定 g_jk=dO_jk：

- dz_k=Σ_j g_jk post_j；dpost_j=Σ_k g_jk z_k。
- dC_ij=Σ_k g_jk X_ik；dX_res,ik=Σ_j g_jk C_ij。
- 调用 dy=VJP_f(y,dz)，而非断开 f 或假设恒等。
- dpre_i=Σ_k dy_k X_ik；dX_pre,ik=pre_i dy_k。
- 把 dpre、dpost、dC 一次送入冻结 split VJP，得到 dmix、dbase、dscale。
- da=dmix*r；dr=dot(dmix,a)；dW=da⊗vec(X)；dX_linear=Wᵀda。
- dX_rms=−dr*r³*X/N。
- dX=dX_res+dX_pre+dX_linear+dX_rms。

四条 X 支路全部显式进入返回值和验证。W 是 mHC 的 FP32 参数，不是量化专家权重；参数梯度跨 R=B×T 行求和。base/scale 的跨行归并已经在旧 split 账里，本候选不再增加一次。

## 工作量

所有线性/张量收缩遵循公共 2mnk 矩阵 FLOPs 约定；这些收缩的归约加法不再列为标量。每个 wrapper 有 R 行，模型有 q=2L=86 个 wrapper，头部另一个 hc_head 不在范围内。

| 阶段 | 矩阵或收缩 | FLOPs/每 wrapper |
|---|---|---:|
| forward | a=W X | 2RVN |
| backward | dX_linear、dW | 4RVN |
| forward | pre 加权收缩 | 2RcH |
| forward | C/residual 收缩 | 2Rc²H |
| backward | dpre、dz、dpost | 6RcH |
| backward | dC、dX_res | 4Rc²H |

外层每行前向标量：`4N+V+1`。来源是平方/均值/epsilon 的 `2N+1`，mix 乘 r 的 V，以及 post*z 和最终加法的 2N。另有 1 次 rsqrt 特殊调用。

外层每行反向标量：`5N+3V+3`。da 的 V；dr 点积的 2V−1；系数 `−dr*r*r*r/N` 的 4；dX_rms 的 N；dX_pre 的 N；四路 dX 合并的 3N。负号是符号操作，未计为浮点 FLOP。该路径使用 N 作常量分母，未将除法改写为不同计数的预计算常量乘法。

总量仅把上述外层账与 `reused_split` 各加一次。没有带入旧 primitive 的 router、route weight 乘法或 inner 的任何前反向。数值 helper 为方便得到所有保存值调用了已有 split VJP；这些实现中的辅助列表/零梯度运算不属于参考算术账。

## 保存边界与生命周期

结果给出逐身份的 forward 保存边界和有序事件：hc_pre → inner_forward → hc_post_forward → hc_post_backward → inner_backward → hc_pre_backward → split_backward → mix/RMS_backward → join_dx。

- X 与 residual 共享一个身份，不能分别计两份。
- 最终 C 已经是 split 最后一次归一化的保存输出，不另添 final_comb。
- pre/post 数值分别经过 +epsilon 与 ×2，与保存的 sigmoid 值不同，因此此参考路径为它们单列保存。
- a 和 mixes 都保留：前者用于 dr，后者用于 dscale。没有偷偷假设重计算。
- r、z 及旧 split 所需输出/分母按对应阶段保留与释放。

`all_sublayers_no_recompute_saved_subset_bytes` 只是声明不重算时 86 个 wrapper 的外层保存子集总和。模型 inner 的保存激活、y 输入要求、weights、gradients、cast缓冲、反向临时张量和 workspace 均未纳入；不能拿此和数当整模型训练内存或实际 allocator peak。事件图声明必要先后和数据依赖，不推造未知 inner 的同时驻留峰值。

## 数值验收

运行：

```sh
/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/research/v4-hc-training-completion/tests -v
```

3 项测试，FP64 PyTorch 自动微分与手写 VJP 对照 x/W/base/scale，覆盖 c=2/4、迭代 1/2/20、非零 epsilon、非线性 inner（tanh+线性）。另用多项式 inner 对全部小尺寸 x/W 元素做中心差分。标量范围、矩阵量、输入重放和 alias 去重有独立断言。测试不使用真实训练权重，不声明验证了未公开训练运行时。
