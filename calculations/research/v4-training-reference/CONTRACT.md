# V4-Flash训练参考：源图差距与可执行数学契约

只读公共目录。此处研究的是原实验3-6的V4分支，不把已完成Qwen AdamW或推理FLOPs×3移植成“完整V4训练”。固定Flash：43主层、前三层hash路由、256选6+shared、hc_mult=4、Sinkhorn20、sqrtsoftplus路由、scale1.5、SwiGLU limit10。

## 已读证据及直接结论

- `calculations/sources/deepseek-v4-flash/inference/model.py`：linear 108–121、Gate 545–589、Expert/MoE 596–643、mHC 650–700、Head 714–723、Transformer.forward 801–809。
- 同目录 `kernel.py`：FP8/FP4 quant wrappers、FP8/FP4 GEMM、sparse attention、hc_split_sinkhorn 372–441。
- `references/text/deepseek-v4.txt`：报告§4.2.2（1411行起）、§5.2.1（1830行附近至1865）、Algorithm1 Muon及相邻说明。

顶层Transformer.forward被 `torch.inference_mode()` 修饰；head仅选择最后位置。FP8/FP4、sparse attention和Sinkhorn调用自定义TileLang forward kernel；这两份公开inference文件没有训练loss/backward/STE注册定义。不能删掉装饰器就声称官方训练代码完整可用。数学子图可重建、求导，但须声明替换，不能偷改其执行语义。

**重要：QAT的STE并非完全未知。** 官方报告§5.2.1明确：FP32 master expert权重先量化FP4再无损转FP8，反向相对同一FP8权重计算梯度并直接传回FP32 master，等价STE。报告也说明indexer QK路径类似处理、index scores从FP32量化BF16。已知原则应保留；未锁定的是具体训练实现、全部scale/clip边界导数与精确复用/重算/累积路径，不能把“代码未给”改写成“报告未披露任何规则”。推理的inplace量化-反量化不会自动携带这一STE。

**优化器也不是所有参数AdamW。** 报告§4.2.2明确多数参数用Muon；embedding、prediction head、所有RMSNorm权重用AdamW（β1=.9、β2=.95、eps=1e−20、weight_decay=.1）。Muon有Algorithm1及momentum/rescale说明。不能对V4总参数套Qwen候选的14P+6来代替实际更新；Muon矩阵分组与HybridNewtonSchulz执行需独立账。

## 路由与梯度规则

Gate先对全部专家计算FP32线性scores，再s=sqrt(softplus(z))。选择bias只影响topk索引，weights取original_scores的选中项，按选中和归一，再乘1.5。

1. 前3层hash索引是整数非训练参数，但选中权重仍来自scores：主loss依然通过归一化weights回传router weight/input。不能因hash选择固定就删掉router GEMM/梯度。
2. 后40层在无tie、选择间隔不变的小邻域，对索引视为分段常量；仍保留选中权重、分母归一化的完整导数。topk边界/tie不是这条平滑局部图的导数证明。
3. 仅影响索引的bias不从这种主任务梯度获得连续导数；官方报告给出辅助loss-free bias更新速度.001，另有sequence balance loss权重.0001，不能把两者全部归零或当AdamW普通参数梯度。
4. Expert的routing weight乘在SwiGLU后的F维激活、down projection之前。若a_e=SiLU(g_e)*u_e、b_e=w_e*a_e，则 `da_e=w_e*db_e`、`dw_e=sum_F(db_e*a_e)`；这个dw继续进入归一化与sqrtsoftplus再到router矩阵。不能把它挪到down输出后却沿用原计数。
5. gate仅上界clip10、up有±10 clip。远离边界时按明确mask导数；边界subgradient须固定（数值测试避边界，另单列策略），不把clamp比较算成普通FLOP。

拟首先实现可审核子模块 `router_expert_weight_backward`：传入明确indices/weights上游梯度，逐gather、归一化、sqrtsoftplus和router矩阵回传，保留hash/score选择两个模式。输出每算子形状、forward/backward普通算术、特殊调用和整数动作；与FP64 torch及有限差分在严格topk margin点比较。工作直方图是输入，不冒充实际token路由记录。

## Indexer与稀疏注意力

Indexer返回topk整数索引，不返回连续index_score给attention乘权，因此在仅固定索引的主loss图中，不能沿离散选择回传score梯度。共享的qr仍可能经main attention获得梯度，不能据此把整块共享投影都冻结。

报告明确先dense warmup、再引入CSA indexer warmup与sparse training。尚未从这两份inference源码和已定位报告段落得到完整indexer训练目标、target生成和loss分支实现；这些需单独查证。不得编造一个KL objective再称官方已实现，也不得以固定选择吞掉indexer训练成本。数学主attention可在选中边固定时对Q/K/V、compressor pooling、window/重叠路径求导；训练时所选边/目标生成与跨序列缓存的保存策略另列。

完整序列训练不能沿推理单槽inplace cache写入直接作反向存活图。声明训练参考须把每个需要梯度的压缩表示和依赖保留为函数式对象，计重叠窗口的多处梯度相加。首版不把最终cache容量当训练激活容量。

## mHC：展开准确有限迭代而非抽象投影

源 `hc_pre` 对flatten后的4H维x取FP32 RMS因子r，同时做24×4H线性mix，再乘r。r依赖x；反向须同时回传线性支路与r支路，不能只计两个GEMM梯度。

Sinkhorn核明确：pre=sigmoid(scale0*mix+base)+eps；post=2*sigmoid(scale1*mix+base)；comb先做row softmax+eps，再column归一化，随后19次row/column归一化，共39次分母带eps的归一化。不能把20迭代误计为20个归一化，也不能假设eps>0时矩阵严格双随机。bias、scale3个共享标量与24个base均有相应梯度归约。

每条归一化为 `y_i=x_i/(sum(x)+eps)`，其VJP为 `dx_i=dy_i/d−sum_j(dy_j*x_j)/d²`。softmax初始行采用标准VJP，后加eps无梯度；pre/post的sigmoid与2倍率分别计。保存39阶段输出/分母是可选声明策略，不可省略所有中间又声称无需重算。

源comb方向必须保持：`hc_post`的sum(dim=2)给出 `y_j=post_j*x + sum_i comb[i,j]*residual_i`。pre为 `sum_i pre_i*x_i`。分别求x、residual、pre/post/comb梯度，包含它们进入mixes的回传和多支路合并。

拟第二个可验子模块 `mhc_vjp`：小hc=2/4、短hidden、eps>0、1/2/20迭代数；独立函数式FP64重建源码顺序，有限差分+autograd检验所有x/W/base/scale梯度，保存/重算策略一项一项声明。只将对应基础层的已证数学反向加入子账，不套三倍前向。

## 首版交付与不变边界

先实现上述router/专家权重与mHC两个完整可微子账，其源语义可明确闭合；为Attention/压缩、QAT STE、loss/head、Muon/AdamW与辅助目标建立分开的coverage记录。训练输入拟 `{B,T,supervised_mask,selection_mode,selected_indices,precision_policy,qat_gradient_policy,sinkhorn_saved_policy}`；先无历史完整序列，禁止把推理prefix接口当训练状态恢复。

每个子账区分：确定的结构/矩阵、声明的数学反向、普通scalar、特殊函数、data/整数操作、保存对象及未知训练策略。对于整体V4 training，`complete_backward_flops`、完整激活peak、完整优化器工作和step时间保持unknown。逐算子数值验算不是完整checkpoint训练或质量证据。

实际训练head需对明确监督位置计算词表logits，不能复用推理last-only head覆盖全序列标签。监督mask只在声明head策略处改变词表行数，不能静默剪去主干或MTP。MTP官方loss权重与辅助训练路径应另列，不能删主干最后一项compress_ratios就忘掉MTP目标本身。
