# 第 2 章扩写资料：模型架构

> 草案 22 配套。保留修订前已核对的推导、版本、参数和全部实验变体，按当前章号重排。正文的论证顺序与核心练习以[本章大纲](../02-%E6%A8%A1%E5%9E%8B%E6%9E%B6%E6%9E%84.md)为准；这里的完整题目供扩写与进阶使用。

本页按来源细目保存细节，节号与正文对应。产品版本和历史测量沿用原有快照；制作占位仍为计划。

<a id="detail-2.1"></a>

## 2.1 计算图与历史依赖

<a id="detail-2.1.1"></a>

### 2.1.1 历史的保存与递推依赖

从四个 token、三层的小计算图开始，横轴画序列位置，纵轴画网络深度。RNN 在时间方向将历史压入固定宽度的状态 `h_t=f(x_t,h_(t−1))`；下一位置必须等前一位置的状态。先数每步矩阵乘、状态大小与依赖，再问长历史的哪些信息还能被后续位置直接取回。

<a id="detail-2.1.2"></a>

### 2.1.2 全局访问与序列并行

用“将时间方向的递推转向网络深度”作直观引子，讨论把 Transformer 想成转了 90 度的 RNN，哪些地方能帮助理解。Transformer 的第 l 层从上一层各位置的表示取信息，已知输入时，同层各位置不必串行等待彼此；深度方向仍逐层推进。

在同一张图上补出注意力跨位置的边，说明这不只是旋转原图：通常各层参数不同、跨位置交互采用内容相关的加权访问，状态也没有被压成同一个固定宽度向量。用 `QKᵀ` 和 `AV` 的小矩阵计算这些新增工作，比较依赖缩短与历史保留的代价。2017 年的 encoder–decoder 背景简述后转入现代因果模型。

<a id="detail-2.1.3"></a>

### 2.1.3 生成时的状态复用

已知整段输入时可以并行处理多个位置，生成下一个未知 token 仍依赖先前输出。用同一图说明缓存 KV 后，Transformer 也可按 token 递推执行，但全历史注意力的状态随长度增长；采用特定线性注意力才能改为固定大小的统计状态，不把两者当成同一个代数等式。这个区别为后面的 Kimi K3 KDA、V4 压缩历史和 prefill／decode 的不同执行方式铺垫。

**已复算（C06-sequence-dependencies）：** [四token三层逐矩阵与数值复算](../../calculations/results/sequence-dependencies-book.md)用固定可见教学权重、D4/FF8/单头/FP64：RNN已知四token768矩阵FLOPs、固定历史96B；因果Transformer3552FLOPs、KV768B。给定第五token，重算/复用分别为RNN960/192、Transformer4560/1008FLOPs，后者KV增长至960B。十次同模型前缀重算与状态复用输出检查最大绝对误差0；不拿两种模型输出作等价比较。完整依赖边和KV历史访问图见JSON，单位cell关键路径6与3不代表实测时延。运行 `python3 calculations/calc.py sequence-dependencies --format md`；教学模型无norm/bias/词表head，非真实checkpoint，非矩阵与运行峰值另计。

> **实验 2-1 ★：序列计算的依赖与并行**
>
> 在四个 token、三层的图上标出 RNN 与因果 Transformer 的时间和深度依赖，检验“旋转 90 度”的类比在哪些边上失效。分别数已知输入和新生成一个 token 的矩阵工作与状态，用小程序验证缓存前后同一模型的结果。
>
> 条件：基础·计算／Python。

> **图 2-1：序列模型的计算依赖（配图计划）**
>
> 自绘 SVG；固定时间横轴和深度纵轴，分别画时间递推、跨位置注意力、缓存后的逐 token 生成，明确参数共享与新增访问边，配实验 2-1。

<a id="detail-2.2"></a>

## 2.2 从代表层计算数据需求

<a id="detail-2.2.1"></a>

### 2.2.1 模型配置与张量尺寸

固定 Qwen3-8B 的官方配置：36 层、隐藏维度 4096、32 个 Q 头、8 个 KV 头、头维度 128、FFN 中间维度 12288。用 B 表示请求数、S 表示已有历史、P 表示每条请求本次输入的 token 数：prefill 的投影输入为 `X[BP,4096]`，每序列生成一个 token 的 decode 为 `X[B,4096]`。从 B=1、S=0、P=8192 的完整 prefill 开始，再算已有 8192 历史后的单步 decode。

<a id="detail-2.2.2"></a>

### 2.2.2 Q、K、V 与注意力输出

按数学右乘记号列 `Wq[4096,4096]`、`Wk/Wv[4096,1024]`、`Wo[4096,4096]`，对照代码权重的转置存储。把投影结果拆成 32 个 Q 头和 8 组 K、V，说明每个 KV 头服务 4 个 Q 头；接着计算 QKᵀ、Softmax、乘 V 与输出投影。QK Norm、RoPE 和 mask 放到实际位置，算 FLOPs 时区分完整矩形计算与利用因果三角的实现。

<a id="detail-2.2.3"></a>

### 2.2.3 前馈网络与单层工作量

展开 SwiGLU 的两次升维与一次降维：`[m,4096]×[4096,12288]` 两路，经 SiLU 与逐元素乘后，再乘 `[12288,4096]`。三组权重共 150,994,944 个参数，矩阵乘约 `301,989,888m` FLOPs；比较注意力投影、序列交互和 FFN，观察上下文变长时占比如何变化。残差与 RMSNorm 的计算和流量单列。

<a id="detail-2.2.4"></a>

### 2.2.4 从一层到完整模型

将 36 层与词嵌入、输出头连接起来，分别列常驻权重、状态容量、prefill FLOPs、decode FLOPs，以及对应的权重／状态读写。投影与 FFN 每层约 `385875968×BP` FLOPs；因果注意力有效位置对数为 `B×[PS+P(P+1)/2]`，QK 与 AV 合计每对约 `4×32×128` FLOPs。prefill 是否计算全部位置的输出头、内核是否跳过因果上三角分别说明，不能把所有后端写成同一执行量。

对权重读取先按一轮理想复用计量，再加入实际分块与缓存假设；prefill 不等于每个输入 token 都从 HBM 独立重读整份权重。对注意力区分逻辑上的历史参与次数与物理读写：分块融合会改变历史重读及中间矩阵写回，具体实现留到第 5 章验证。用同一张简洁计算表贯穿各模型，完整算式另附[资源计算笔记](../../case-studies/model-resource-accounting.md)。

**已复算（C07）：** [计算项目](../../calculations/README.md)已按官方配置与 checkpoint 索引复核全部 8,190,735,360 个参数，统一 BF16 权重为 15.256433 GiB。本节四个固定场景的[逐算子结果](../../calculations/results/README.md)已生成：8192-token prefill 的有效因果矩阵工作加最后位置输出头为 133.594323 TFLOPs；S=8192、B=1 的一次 decode 为 19.968623 GFLOPs；命中 6144 后补入 2048 的矩阵工作为 37.110366 TFLOPs、新增 KV 为 288 MiB。归一化、激活、位置编码、特殊函数与操作数读写另列；矩形物化路径和因果有效工作不是同一计量，不能将表中载荷直接当 HBM 实测。运行 `python3 calculations/calc.py reproduce` 重建 JSON／Markdown／逐层 CSV。

> **实验 2-2 ★：Qwen3-8B 的逐层计算**
>
> 读取固定配置，逐层输出 QKV、注意力、SwiGLU、归一化与输出头的尺寸、FLOPs、常驻字节及访问字节。分别代入 8192-token prefill、已有 8192 历史的 batch=1／64 decode，再改为命中 6144-token 前缀、补入 2048 token；容量、读取和新增写入各自复算，不能只给一项“显存需求”。
>
> 条件：基础·手算／短脚本。

> **图 2-2：Qwen3-8B 单层的尺寸与数据流（配图计划）**
>
> 自绘 SVG；每根主数据箭头标张量尺寸，矩阵乘结果由实验 2-2 生成，正文图不铺完整实现代码。

<a id="detail-2.3"></a>

## 2.3 共享表示与状态压缩

<a id="detail-2.3.1"></a>

### 2.3.1 KV cache 与历史复用

从不保存历史的逐步生成计算出重复工作，再得到 KV cache。Qwen3-8B 的 BF16 KV 每个历史 token 占 `2×36×8×128×2=147456 bytes`，即 144 KiB；8192-token 历史占约 1.125 GiB。一次普通全历史 decode 至少需要逻辑上访问这份历史，并新增 144 KiB 状态；是否全部从 HBM 读取、KV 头间能否有效复用，取决于缓存层次与内核路径。

接着区分“存多少”和“累计读多少”：prefill 前已有 S 个位置、本次输入 P 个位置，结束后历史为 H=S+P；从这里继续执行 D 次单 token 前向，旧历史读取项为 `144 KiB×[D×H+D(D−1)/2]`，追加 KV 为 `144 KiB×D`，保留上下文时的有效 KV 为 `144 KiB×(H+D)`。普通请求首输出来自 prefill，输出 G 个 token 通常对应 D=G−1；按调用次数给定的算例不把该次数再当成输出数。当前 token 当步参与、真实 HBM 流量、页尾分配与释放另计。batch 无前缀共享时各序列状态相加，理想权重复用可由批次分摊。

<a id="detail-2.3.2"></a>

### 2.3.2 MHA、MQA 与 GQA

在相同隐藏维度与上下文下改变 KV 头数，比较状态容量、读取字节与模型质量。共享 KV 头减少状态宽度，但 Q 头仍要完成各自的序列交互，不能直接用缓存缩减倍数代表全部注意力计算缩减倍数。

<a id="detail-2.3.3"></a>

### 2.3.3 潜变量压缩与执行路径：K3 MLA

直接用 Kimi K3 的 Gated MLA 层：按报告、配置与参考代码画 512 维潜变量、Q 投影、上投影／权重吸收和输出门控。MLA 使用 NoPE，但当前参考代码仍保留参与 QK 的 64 维额外分支，只是不做旋转位置编码；不能仅由 NoPE 推断缓存少了这 64 维。先把必要表示保存量算出来，再比较吸收式与显式展开式执行的矩阵工作及中间读取。

按保留潜变量与额外分支的紧凑 BF16 教学路径，24 层历史为 `24×S×(512+64)×2` bytes；8192 历史约 216 MiB。已归档的 Hugging Face 参考代码实际上缓存展开后的 K／V，同样输入约 11.25 GiB，不能把紧凑路径的数值当成这份代码的分配量或生产测量。这些都只算 MLA，KDA、短卷积、前缀检查点和工作区随后补齐。全局层仍访问全部潜在历史，容量压缩没有消除随长度增长的读取。

**已复算（C09-MLA）：** [K3 MLA 展开路径](../../calculations/results/k3-mla-expanded-b1-t8192-s0.md)与[compact 吸收路径](../../calculations/results/k3-mla-compact-b1-t8192-s0.md)已按实际 24 层计算全部投影、QK/PV、归一化和输出门控。B=1、T=8192 时，MLA 缓存分别为 11.25 GiB 与 216 MiB；两路径投影矩阵工作相同，compact 的有效注意力矩阵工作为展开路径的 3.4 倍。qk_rope_head_dim 虽为 64，官方 mla_use_nope 路径不执行 RoPE，但保留这条额外 Q/K 分支。sigmoid 输出门控位于 Wv 与 o_proj 之间，不可跨门控合并投影。CLI 为 `python3 calculations/calc.py k3-mla --path compact --tokens 8192`；compact 是经小矩阵验证的代数替代路径，不是固定 HF 实现的缓存方式。

**已复算（C08-cache-sequence）：** [整段缓存计算](../../calculations/results/cache-sequence-qwen3-8b-b1.md)按 P=8192、随后 G=1024 次单 token 调用，累计旧历史记录为 GP+G(G−1)/2=8,912,384；Qwen3-8B 的 GQA 旧历史逻辑读取合计 1223.929688 GiB，追加写入 0.140625 GiB，最终缓存 1.265625 GiB。这些载荷不等于 HBM 实测，当前 token 操作数与旧历史、写入分开。MHA／MQA 为架构对照，不是现有 GQA checkpoint 的执行开关；其 QK/PV 工作不随 KV 头缩减。完整 prefill 与命中 6144 后的后缀比较、无缓存重算的 token 行／因果矩阵工作，以及 K3 expanded／compact 整段累计均已输出；K3 前缀检查点必须包含对应位置的 KDA 和短卷积状态。运行 `python3 calculations/calc.py cache-sequence --model kimi-k3 --batch 64 --format md` 复现；工作区、物理共享和并行复制继续归容量／放置专题。

**已复算（V3-base-forward）：** [DeepSeek V3基础前向](../../calculations/results/v3-forward-prefill.md)按官方61层、3层Dense与58层MoE逐张量计671026419200逻辑参数、45395张量；均匀两字节容量仅作比较格式，未当官方FP8文件大小。固定HF参考路径先展开K/V再缓存，每请求每位置4997120bytes，与compact MLA不是同一布局。8192 prefill矩阵767753388556288 FLOPs，[单token decode/H8192](../../calculations/results/v3-forward-decode.md)114190598144 FLOPs；[B64](../../calculations/results/v3-forward-b64.md)独立按batch扩展。默认全位置输出头，[last head](../../calculations/results/v3-forward-last-head.md)是显式负载变体；[eager矩形](../../calculations/results/v3-forward-eager.md)与有效因果cell分开。运行 `python3 calculations/calc.py v3-forward --format md`；分组路由偏置只影响选择，混合权重用原sigmoid分数。未计FP8转换、完整HBM、缓存重分配或MTP，也未完成checkpoint索引核验。

> **实验 2-3 ★：GQA 与 K3 MLA 的容量和访问**
>
> 用 Qwen3-8B 与 Kimi K3 的实际配置，分别算 GQA／MLA 的常驻历史、一个 decode 步的历史读取与新增写入，再累加一段生成。比较两种 MLA 执行路径的矩阵尺寸和额外中间量；每头／每层对照与整模型对照分开，加入工作区及并行复制后再算。
>
> 条件：基础·手算／短脚本。

> **图 2-3：MHA、GQA 与 MLA 的缓存状态（配图计划）**
>
> 同一序列自绘三栏 SVG；缓存框的大小与每次访问的箭头分别标数，实验 2-3 分别生成容量和读取曲线，明确共享与低秩压缩的差异。

<a id="detail-2.4"></a>

## 2.4 选择性访问与有限状态

<a id="detail-2.4.1"></a>

### 2.4.1 局部窗口与选择性访问

沿长上下文中被读取的历史位置，区分局部窗口、显式稀疏选择与压缩历史。用 V4 的窗口、压缩条目与索引器引出三种工作，分别计算保存、选择和读取；全局历史缩小、实际读取变少与新增索引工作需要同时计量。

<a id="detail-2.4.2"></a>

### 2.4.2 窗口、压缩与索引：V4-Flash

采用正式名称 DeepSeek-V4-Flash，固定 43 层、隐藏维度 4096、64 个注意力头、每头 512 维。逐段展开 Q 的 `[m,4096]→[m,1024]→[m,64,512]`、共享 KV 的 `[m,4096]→[m,512]`，以及分 8 组的低秩输出投影；与上一节 K3 MLA 的潜变量、全局访问及门控分别比较。

沿配置逐层比较窗口 128、压缩比 4 的 CSA 与压缩比 128 的 HCA。主干为 2 层纯窗口、21 层 CSA、20 层 HCA，MTP 另计。以 BF16 参考缓存为例，一层 CSA 保存窗口与 `floor(S/4)` 个 512 维压缩条目，另存同数量的 128 维索引条目；每步主注意力最多取窗口加 512 个压缩条目，索引打分仍需扫描压缩索引历史。HCA 保存并访问窗口加 `floor(S/128)` 个压缩条目；尚未完成的压缩块与滑动状态另计。

分别计算 prefill 的各位置、decode 的当前查询、压缩器与索引器 FLOPs，列状态的常驻、读取和更新量。参考实现模拟量化但以 BF16 保存的缓存，与真实压缩存储格式分别核算；不能用最终 top-k 条目数代替全部访存，也不能用保存量直接代替每步读取量。V4 的节省来自哪些项、在哪些上下文和 batch 下出现，由计算结果说明。

**已复算（C10-state）：** [Flash 状态结果](../../calculations/results/state-deepseek-v4-flash-n8192-b1-native.md)在 N=8192、B=1、历史 BF16 下给出 59.125 MiB 历史，加 11.6406 MiB FP32 压缩器槽；最后查询的主注意力及索引载荷为 27.625 MiB。[V4-Pro 独立配置结果](../../calculations/results/state-deepseek-v4-pro-n8192-b1-native.md)按 61 层的 30 CSA＋31 HCA 和 top-k=1024 重算，当前状态合计 102.406 MiB、选中历史载荷 54.5625 MiB。CLI 为 `python3 calculations/calc.py state --model deepseek-v4-pro --length 8192`；这是状态与部分注意力工作，完整压缩更新、全模型 FLOPs、真实量化格式和 MTP 仍待计算。

**已复算（C10-mHC）：** [V4-Flash mHC 子账](../../calculations/results/hc-deepseek-v4-flash-b1-t8192.md)按每层 attention／FFN 两套混合参数和最终 hc_head 计算：B=1、T=8192 时，混合投影为 555.124523 GFLOPs，普通算术为 148.981473 GFLOPs，特殊函数独立计数。20 次 Sinkhorn 按源码展开为初始行 softmax 加 39 次归一化；中间片段留在 kernel 局部存储，不能乘迭代数当 HBM 流量。最终 hc_head 处理全部新 token，词表头才选择最后位置。运行 `python3 calculations/calc.py hyper-connections --model deepseek-v4-flash --tokens 8192` 复现；该子账不含注意力、专家、外部 RMSNorm、MTP 或词表投影。

**已复算（C10-attention-matrices）：** [V4-Flash 注意力矩阵子账](../../calculations/results/attention-deepseek-v4-flash-b1-t8192-s0.md)在 B=1、T=8192 下，投影工作为 83.309481 TFLOPs，有效 QK/PV 为 16.641044 TFLOPs，参考实现的矩形索引点积为 5.772436 TFLOPs。低秩 Q、共享 KV、分组 wo_a／wo_b、两种压缩器及 Indexer 投影分别列尺寸；压缩器每个新 token 都执行投影，不能只在压缩块完成时计量。Indexer 在 prefill 先做矩形点积再加 mask，有效因果点积另列作对照。CLI 为 `python3 calculations/calc.py v4-attention --model deepseek-v4-flash --tokens 8192`；压缩池化 softmax、加权归约、Q/K 归一化、RoPE 及索引评分标量已另列；ratio=4 的重叠窗口与 prefill 保存块的额外位置偏置相加均按源码计量。稀疏 kernel 另计固定 64-slot tile GEMM、在线 softmax 和 attention sink；无效索引屏蔽 KV 读取但不消除 tile GEMM，共享 KV 在 QK/PV 间复用。Hadamard 蝶形加减／缩放与 FP4／FP8 模拟量化除法／缩放已展开，abs/max、clamp、位操作和格式转换分列；CUDA 指令、数据移动及后端实测流量仍待补齐。

**已复算（C10-forward-ledger）：** [V4-Flash 基础前向汇总](../../calculations/results/forward-deepseek-v4-flash-b1-t8192-s0.md)已衔接注意力、专家、mHC、外部 RMSNorm、嵌入及最后位置词表头。B=1、T=8192 时，有效注意力口径矩阵工作为 231.125253 TFLOPs；基础逻辑参数为 284,332,240,471，不含 MTP、量化 scale 与整数 hash 表。CLI 为 `python3 calculations/calc.py v4-forward --model deepseek-v4-flash --tokens 8192`。JSON 保留全部子账和 coverage：已知 sparse/expert tile 通过替换有效项进入另一总数；已核对官方全部 checkpoint 索引和分片元数据头，基础逻辑参数与推导一致，checkpoint 的基础模型／MTP／scale／I64 hash 表字节分开；其余投影 padding、运行时格式转换及完整访存仍未闭合，运行时完整字节和时延保持 null，不作为全书工作包完成证明。

**已复算（C10-v4-sequential-prefix）：** [V4固定源码的缓存后缀续算](../../calculations/results/v4-prefix-flash-6144-2048.md)要求6144位置的完整window/压缩/index/FP32 compressor状态已恢复，随后逐个输入2048个已知token。基础forward和词表头均调用2048次，即使中间logits被丢弃仍计费；总有效矩阵60,270,873,411,584FLOPs，替换已知sparse/expert tile口径为884,744,027,897,856，两者是替代口径。ratio4/128分别完成512/16次，逐步列表保留共同边界与写入。有效状态60,112,896→74,203,136bytes，增长不等于累计写入；完整HBM和实际peak仍未知。[Pro跨128边界](../../calculations/results/v4-prefix-pro-boundary.md)和[批量边界](../../calculations/results/v4-prefix-flash-batch-boundary.md)另有对照。源码默认max_seq_len4096不足，本题显式分配8192/1并单列cache容量；前缀查找/传输/恢复未被假定免费完成。运行 `python3 calculations/calc.py v4-prefix-continuation --format md`；固定增量分支写单槽，此调度不是并行chunk prefill。

> **实验 2-4 ★：V4-Flash 的压缩历史与稀疏访问**
>
> 按 43 层配置分别算完整／命中前缀后的 prefill、每步 decode 的 FLOPs、权重读取、窗口／压缩历史读取、索引扫描和状态写入。扫描 8K、128K、1M 及 batch=1／64，单列压缩块完成时的更新峰值；对照参考实现的逻辑状态、预分配和实际格式。
>
> 条件：基础·手算／短脚本。

> **图 2-4：V4-Flash 的窗口、CSA 与 HCA（配图计划）**
>
> 自绘 SVG；同一历史中标被压缩、被索引和实际访问的条目，尺寸与曲线来自 实验 2-4。

<a id="detail-2.4.3"></a>

### 2.4.3 有限状态与全局访问：K3 混合结构

回到开篇时间递推与深度处理的图，用 KDA 的状态更新解释历史怎样进入固定大小的矩阵。按 K3 配置展开 69 个 KDA 层与 24 个 MLA 层，末尾额外 MLA 单列，不能仅用 3:1 比例推算。KDA 每头状态为 `128×128`、每层 96 头，保存量按状态实际精度计算；decode 即使不再读取全历史 KV，也要读取并更新递推状态、短卷积状态和相关权重。

prefill 用分块并行形式计算块内工作和块间状态，decode 用单步递推计算；不得用逐 token 朴素循环的流量代替融合内核。将 K3 的有限状态加全局 MLA，与 V4 的窗口、压缩历史和索引访问并排复算；同长度不代表同质量，先对齐每层机制与精度，再给整模型绝对量和任务质量条件。Qwen3.5 与 Kimi Linear 仅作相关路线参照。

**已复算（C11-state）：** [Kimi K3 状态计算](../../calculations/results/state-kimi-k3-n8192-b1-compact.md)按实际 69 KDA＋24 MLA 分层：N=8192、B=1 时，FP32 recurrent state 为 414 MiB；紧凑 BF16 MLA 为 216 MiB，另按 kernel_size=4 的短卷积槽假设计 19.40625 MiB。[展开缓存路径](../../calculations/results/state-kimi-k3-n8192-b1-expanded.md)的 MLA 为 11.25 GiB。两条路径通过 `--mla-path compact`／`expanded` 明确选择；全模型前向、分块 KDA prefill 与检查点复制的计算仍待补齐。

**已复算（C11-KDA-recurrent）：** [K3 KDA 递推子账](../../calculations/results/k3-kda-b1-t1-s8192.md)已按实际 69 层、96×128 通道计算 Q/K/V、低秩 f、beta、全秩输出 gate 和 o_proj；另列三路 width=4 无 bias 短卷积、Q/K L2Norm、带 -5 下界的 sigmoid 衰减门控与递推状态更新。输出 RMSNorm 的 128 个 scale 在 heads 间共享，不能按 12288 维重复计参数。B=1 的 FP32 recurrent state 为 414 MiB。CLI 为 `python3 calculations/calc.py k3-kda --batch 64 --tokens 1`；T>1 的数学递推基线不代表官方 chunk prefill kernel 工作，选定 FLA 参照版本与 K3 固定代码的 API 差异明确保留。

**已复算（C11-AttnRes）：** [K3 AttnRes 逐层调度](../../calculations/results/k3-attn-res-b1-t8192.md)按 block_size=12 展开 93 层：第 0 层不做 attention 混合，块边界先混合旧块再追加 prefix，FFN 使用新候选数；全图共 186 次混合，最终保存 8 个块、输出混合有 9 个候选。norm.weight×proj.weight 按每次调用一次计量，不能按 token 重复计算；prefix 加法按 178 次逐元素加计入。块堆栈是本次 forward 的深度状态，每次调用重新建立，不是额外的跨 token KV。CLI 为 `python3 calculations/calc.py k3-attn-res --batch 64 --tokens 1`；逐次形状、加权矩阵／标量工作及独立张量容量已输出，未将容量相加冒充工作区峰值。

**已复算（C11-KDA-chunk-buffers）：** [选定 FLA KDA chunk 分配结果](../../calculations/results/k3-kda-chunk-t8192-c64.md)在 B=1、T=8192、chunk_size=64 下，每层中间 chunk state 为 384 MiB；Aqk／Akk、FP32 对角块、WY 输出和后续状态／输出的存活阶段已核对，最大已确认存活子集为 1926 MiB。它不包含全部输入、投影和后端 scratch，因此不是完整峰值；也不能乘 69 个顺序执行层。全层最终 recurrent state 的 414 MiB 另计。CLI 为 `python3 calculations/calc.py k3-kda-chunk --tokens 8192`；T=65 的尾块案例分别验证 T×chunk_size 注意力缓冲和 ceil(T/chunk_size) 状态轴，数学块算法已补下三角 KK、W/U 前代求解、状态预测、因果 QK/PV 和状态更新，并用非零初始状态／尾块案例验证与逐 token 递推的输出和最终状态一致；这是有效三角项计量，融合 kernel 的填充与完整指令算术仍另算。

**已复算（C11-forward-ledger）：** [Kimi K3 文本前向汇总](../../calculations/results/forward-kimi-k3-b1-t8192-s0-expanded.md)连接 24 层 MLA、69 层 KDA、专家、AttnRes、外部归一化、嵌入和词表头。B=1、T=8192、expanded MLA 与块式 KDA 数学口径下，矩阵工作为 1744.701011 TFLOPs，源代码枚举文本逻辑参数为 2,779,484,476,000。运行 `python3 calculations/calc.py k3-forward --tokens 8192` 复现；`--output-head all` 对应非 generation_mode 的全位置词表输出。块式 KDA 替换递推核心及衰减指数，不重复相加；AttnRes 已含前缀累加。compact MLA 是代数替代方案，块式数学 FLOPs 不是 fused kernel 指令数。官方 96 个分片、497220 个张量的索引和元数据头已核对；文本 checkpoint 载荷为 1559965606912 bytes，其中量化 scale 为 85085650944 bytes。69 个 KDA A_log 的 checkpoint 长度为 128，而同 revision 配置／代码为 96，参数差 2208、FP32载荷差 8832 bytes 已显式报告。固定FLA两种KDA wrapper兼容状态布局参数别名，但该别名不解决A_log形状冲突；不静默截断，也不宣称可直接加载执行。运行时格式转换、完整访存及多模态／MTP 仍列入 coverage，完整运行时字节与时延保持 null。

> **实验 2-5 ★：混合结构的状态与检索能力**
>
> 以 Kimi K3 与 DeepSeek-V4 为主，输出同一长度、batch 下的常驻状态、prefill FLOPs／读写和 decode FLOPs／读写；KDA 状态、MLA 历史、V4 索引和压缩缓冲分别列出。先用统一状态精度比较机制，再按各自真实格式重算；加入前缀检查点和固定检索质量记录，说明各自节省了什么、增加了什么。
>
> 条件：基础·配置／数据分析。

> **图 2-5：注意力结构与状态增长（配图计划）**
>
> 自绘 K3 与 V4 的状态及访问路径；实验 2-5 分图绘制“常驻容量—长度”“每步访问—长度”“prefill 工作—长度”，另列质量条件。不能把三种量混在一根性能柱上。

<a id="detail-2.5"></a>

**已复算（Qwen35-reference）：** [Qwen3.5基础文本](../../calculations/results/qwen35-prefill-8192.md)按固定配置与1038个checkpoint张量形状核对，45层DeltaNet、15层gated GQA与60层MoE分列；基础文本396,346,350,336参数、792,692,717,952存储bytes，视觉/MTP不并入文本前向。8192 prefill、全部位置输出头，在声明的eager矩形attention／chunk64路径计304,038,065,373,184矩阵FLOPs；[8192历史单步decode](../../calculations/results/qwen35-decode-b1.md)为36,977,377,472。[65token尾块](../../calculations/results/qwen35-chunk-tail-65.md)核心补到128位置；[初始单token](../../calculations/results/qwen35-cold-single-token.md)普通卷积cache先pad到4，conv计算7位置后裁切，不能只计最终一个输出。[record-past初始别名](../../calculations/results/qwen35-cold-single-record-past.md)无last4复制；已有记录长度未知时保留缺项。矩阵、归一化/门控算术、特殊函数、整数索引及状态分别给出；算子边界与补充语句接口有重叠，禁止相加为HBM。primitive后端、allocator及非所选分支不由此验证。运行 `python3 calculations/calc.py qwen35-forward --format md`，`--inputs`修改场景。

## 2.5 条件计算与专家数据

<a id="detail-2.5.1"></a>

### 2.5.1 从稠密 FFN 到专家路由

以 Qwen3 的稠密 SwiGLU 为起点，将容量分给多个专家，再为每个 token 选择少数专家。沿 V4 与 K3 的路由、共享专家和负载分布，解释总参数决定权重驻留，激活参数只近似反映部分计算；批内访问的不同专家集合决定必要权重读取，路由与跨设备交换另算。

<a id="detail-2.5.2"></a>

以Qwen3.6-35B-A3B作为Qwen3-8B之后的中等规模MoE主例：[逐矩阵与状态结果](../../calculations/results/qwen36-prefill-8192.md)、[decode](../../calculations/results/qwen36-decode-b1.md)、[必要容量](../../calculations/results/qwen36-capacity-b1-n8192.md)。先拆分路由/共享专家，再分别核30层线性attention和10层完整attention，避免以“激活3B”代替整个模型的计算或内存。模型发布名3.6与官方实现类型qwen3_5_moe分别记录，不将旧397B参数直接缩放。

**已复算（C82-Qwen36）：** 在Qwen3-8B dense之后，用[Qwen3.6-35B-A3B逐算子账](../../calculations/results/qwen36-prefill-8192.md)展开中等规模MoE，再进入V4 Flash。固定官方revision、config及693个基础文本权重形状：40层、hidden2048、256选8路由专家，另有宽512共享专家；每个路由专家三矩阵共3,145,728参数，每层全部专家805,306,368参数、单token选中25,165,824参数。路由矩阵为[BP,2048]×[2048,256]；每专家gate/up为[t_e,2048]×[2048,512]，down为[t_e,512]×[512,2048]；共享分支和门控另外计。它同时包含30层Gated DeltaNet与10层gated GQA，不能把与dense基线的全部差异归因于MoE。基础文本34,660,610,688参数、69,321,221,376 BF16存储bytes；视觉与MTP权重另列，A3B不是整个checkpoint大小。在固定参考chunk64/eager矩形路径、全部位置输出头下，8192 prefill矩阵工作60,426,170,793,984 FLOPs；[8192历史单步decode](../../calculations/results/qwen36-decode-b1.md)为7,331,184,832 FLOPs。[B64均匀](../../calculations/results/qwen36-decode-b64.md)和[集中同8专家](../../calculations/results/qwen36-decode-b64-concentrated.md)保持专家FLOPs相同，当前批次读取的不同专家权重集合相差32倍，全部专家仍常驻。完整attention KV每请求每历史token20KiB，FP32递推状态固定60MiB，BF16卷积槽1.875MiB；不把线性层也按全历史KV计。运行 `python3 calculations/calc.py qwen36-forward --format md`，用 `--inputs calculations/scenarios/qwen36-forward-example.json` 改batch/token/history。JSON/CSV列逐矩阵、非矩阵和状态；逻辑接口载荷不是HBM，基础文本不含视觉/MTP执行与实测时延。

### 2.5.2 DeepSeek-V4-Flash 的专家计算

固定每层 256 个路由专家、每 token 选择 6 个，以及 1 个共享专家；专家中间维度为 2048。逐个专家展开两次 `[t_e,4096]×[4096,2048]` 和一次 `[t_e,2048]×[2048,4096]`，其中 `t_e` 是该专家实际收到的 token 数。用同一批 token 比较稠密大矩阵与多个不等长专家矩阵，计算约 25.17M 参数／专家及激活计算；前三层哈希路由与后续评分路由分开。全模型约 284B 总参数、13B 激活参数采用报告定义，不能仅以专家矩阵求和冒充精确总量。

<a id="detail-2.5.3"></a>

### 2.5.3 状态、专家与系统协作

**占位 TC-03：** 补 MoE、GQA／MLA 与稀疏状态分别减少的资源及相互代价。 详见[成本下降调研](../../research/token-cost-2023-2026/report.md#architecture)。

把 V4-Flash 的注意力、MoE、mHC 残差路径与输出头连成一层完整数据流。mHC 的 4 路残差状态不意味着每个算子都在 4×4096 隐藏维度上执行，说明汇合后仍以 4096 维进入子层。对照 K3 的 896 选 16 路由专家、3584 维潜空间与 3072 维专家中间层；进入／离开潜空间、共享专家、首层 dense、门控和 AttnRes 另计。分别算总权重、当前批次专家集合和实际 token–expert 计算量，连接第 6 章通信与第 9 章 AF 分离。

**已复算（C12-Qwen）：** Qwen3-30B-A3B／235B-A22B 已实现完整逻辑前向，权重键及 BF16 总字节逐项对上官方 checkpoint 索引。以 [235B 的 B=64、S=8192 decode](../../calculations/results/qwen3-235b-a22b-decode-b64-s8192-balanced.md) 为例，矩阵工作为 4.375762 TFLOPs；每层 512 次专家分派，均匀路由覆盖 128 个专家，专家权重载荷为 423 GiB。[集中到相同 8 个专家](../../calculations/results/qwen3-235b-a22b-decode-b64-s8192-concentrated.md)时 FLOPs 不变，专家权重载荷降至 26.4375 GiB，相差 16 倍。每专家 token 数、三次 GEMM 尺寸、FP32 路由 softmax／top-k／归一化及 gather／合并分别输出；该载荷不是 HBM 实测，也不包含专家并行通信。V4、K3 的专家适配继续单独实现。

**已复算（C12-expert-matrices）：** [V4-Flash FFN 矩阵台账](../../calculations/results/experts-deepseek-v4-flash-b64-balanced.md)在 B=64、T=1 下为 0.975360 TFLOPs，含 routed／shared 专家和 router；前 3 个 hash 层仍计算 router GEMM，int32 路由表另占 9,308,160 bytes，不计为浮点参数。[Kimi K3 台账](../../calculations/results/experts-kimi-k3-b64-balanced.md)同场景 FFN 矩阵为 8.552958 TFLOPs，含 92 层的 3584 维 routed 专家、保持 7168 维的共享分支、双向潜空间投影及第 0 层 dense FFN。各专家真实 M 维、共享分支和矩阵层编号分别输出；CLI 为 `python3 calculations/calc.py experts --model kimi-k3 --batch 64`。矩阵之外另列路由、激活、归一化及合并算术：V4 在 down 投影前按中间维 F 乘路由概率，K3 在投影后按潜空间维 R 加权；K3 Situ 含两次 tanh，特殊函数不折算 Tensor FLOPs。参考 dispatch 的索引、掩码、gather、排序端点、重排与合并载荷已单列；排序／直方图内部流量保持未知。mHC／AttnRes、MTP 及真实混合量化元数据仍待补齐，不作为全模型参数量或完整前向结论。

**已复算（C12-V4-format）：** [V4 专家实际格式结果](../../calculations/results/experts-deepseek-v4-pro-b64-balanced.md)分别列 FP4 packed 权重和每 32 个 K 元素一个 E8M0 scale，合计每参数 17/32 bytes。固定参考 kernel 把 FP4 权重转为 FP8，再执行 FP8×FP8、FP32 累加，不能套用原生 FP4 峰值。每专家 M 维补齐到 32 的 tile 工作与有效 FLOPs 分列：Pro 在 B=64 的均匀路由中，每个专家一行，参考矩阵 tile 工作为有效工作的 32 倍；该比例不是实测时延比例。这里仅覆盖 routed 专家，尚非全模型实际存储。

> **实验 2-6 ★★：V4-Flash 的专家矩阵与负载**
>
> 对 V4 的 256 选 6 加共享专家路由，统计每专家 token 数、矩阵形状、常驻权重、批次读取与激活运算；再换为 K3 的潜空间专家重算。同一专家被多个 token 使用时，比较新增计算与权重复用，交付逐专家需求；第 6 章再选择多卡切分，第 9 章再比较 CPU／GPU 放置与交接。
>
> 条件：进阶·计算／路由分析。

> **图 2-6：Qwen3 Dense 与 V4-Flash 的单层对照（配图计划）**
>
> 自绘 SVG；从同为 4096 维的子层输入出发，连接注意力、FFN／专家和残差，标专家 token 数与 mHC 汇合，配实验 2-2、实验 2-6。

<a id="detail-2.6"></a>

## 2.6 模型选择与系统代价

<a id="detail-2.6.1"></a>

### 2.6.1 参数规模与设备容量

**已复算（C13-llama70-capacity）：** [真实70B单设备容量](../../calculations/results/llama70-capacity-8k.md)按70,553,706,496参数逐矩阵计量，BF16权重141,107,412,992bytes；group128/每组2-byte scale的4-bit教学方案为39,500,398,592bytes，保留embedding、输出头和norm为BF16。每请求8192位置BF16 KV为2,684,354,560bytes。80 decimal GB预算、2 GiB固定工作区时，8-bit方案仅容1请求、4-bit方案容14请求；[32K历史](../../calculations/results/llama70-capacity-32k.md)下4-bit方案为3请求。[group1000尾组](../../calculations/results/llama70-capacity-tail-group.md)逐行向上取整；[精确容量阈值](../../calculations/results/llama70-capacity-boundary.md)用49,700,945,920bytes前后各1byte检验2→3请求。运行 `python3 calculations/calc.py capacity-scan --model deepseek-r1-distill-llama-70b --format md`。这些是声明存储与工作区下的单设备容量，不是已验证量化checkpoint、部署吞吐或八卡分片结论。

**已复算（F02-llama70-forward）：** [公开70B代表](../../calculations/results/llama70-prefill-8192.md)采用DeepSeek原发布者的R1-Distill-Llama-70B，固定config与723个索引权重名对照得到70,553,706,496参数；未将原Meta仓库401记录改名或替换为名义70e9。B=1、8192-token prefill、仅最后位置输出头时，矩阵工作1209.475629 TFLOPs；[已有8192历史再decode一步](../../calculations/results/llama70-decode-8192.md)为160.480887 GFLOPs，默认每请求每历史token的KV为327,680 bytes。80层Llama没有Qwen3的Q/K Norm；每层矩阵、RMSNorm、RoPE、softmax、SwiGLU及残差分别列账。缩放RoPE初始化与每次forward分开，默认位置表在批内和层间共享。运行 `python3 calculations/calc.py forward --model deepseek-r1-distill-llama-70b --tokens 8192 --format md` 复现；CSV展开逐层算子。这里是逻辑算子与操作数载荷，非实际HBM、完整运行延迟或量化checkpoint验证；单设备容量已另行接入，BF16逐卡放置已另接入，真实工作区与完整通信图仍待专门计算。

**已复算（C13-single-device-capacity）：** [实际形状容量扫描](../../calculations/results/capacity-qwen3-8b-n8192.md)从 Qwen3-8B 的 8,190,735,360 个真实参数出发，BF16 权重为 15.256433 GiB；在声明的分组低位宽方案中逐行计打包尾部和 scale，嵌入／输出头／路由器／norm 保留 BF16。运行 `python3 calculations/calc.py capacity-scan --model qwen3-32b --format md`。Qwen3-8B／32B／235B 在 8K／32K 历史、24／48／80 GB 单设备预算下的并发表已输出；工作区默认保留 2 GiB，最大并发只对该预算成立。MoE 保存全部专家，不按激活参数算权重；低位宽不是已验证的量化 checkpoint，公开70B输入及前向已另行接入，70B单设备容量已接入，BF16八卡Llama放置已接入，低位分组重切及实际工作区仍待专门计算。

**占位 TC-02：** 补能力密度提升及“小模型接近旧大模型”的有条件对照。 详见[成本下降调研](../../research/token-cost-2023-2026/report.md#density)。

从常见的 7–8B、约 30B、70B 与 235B 出发，判断它们在什么硬件和业务条件下形成部署上的“甜点”。先按精度计算权重，再扣除 KV、工作区、并行复制与运行余量：约 8B 的 BF16 权重约 16 GB，适合讨论 24 GB 卡的单实例空间；约 30–32B 的 BF16 权重为 60–64 GB，理想 4-bit 权重为 15–16 GB；70B 的 BF16 权重约 140 GB，8-bit 约 70 GB。每种情况都要加回量化元数据、较高精度部分和状态，才能判断一张或几张卡是否适合。

用 Qwen3-235B-A22B 与八张 80 GB 卡计算：名义 BF16 权重约 470 GB，均分约 58.75 GB／卡；剩余容量还要承担状态、工作区和复制。再换为八张 24 GB 卡或不同精度，解释为什么“八卡甜点”必须带上卡型、格式、上下文与并发。Qwen3 的约 30B 型号是 MoE，32B 是 Dense；总参数用于驻留，激活参数用于部分计算，不能仅看数字接近就视为同一任务。

部署可行点、满足延迟和吞吐的经济点、模型团队实际选择该规模的原因分别讨论。Llama 1 明确考虑训练与推理预算，Qwen3 展示多个规模；这些资料不证明“7B 是为 4090 设计”或“235B 唯一由八卡显存决定”。结合能力目标、训练数据、预算和服务范围，把硬件容量作为设计约束之一。

<a id="detail-2.6.2"></a>

### 2.6.2 层数、宽度与专家划分

**已复算（C13-architecture-shapes）：** [图2-7架构形状伴图](../../calculations/figures/architecture-shapes/figure.svg)由冻结结果生成六面板：Dense每条代表一层，同列条宽随H变化；MoE每条代表一层中的一个专家，同列宽随F变化，橙色为首条合成路由的真实专家ID集合。标出gate/up/down存储形状、完整参数与差额，router变化不被专家预算相等掩盖。[PNG](../../calculations/figures/architecture-shapes/figure.png)、[PDF](../../calculations/figures/architecture-shapes/figure.pdf)及[原始图数据](../../calculations/figures/architecture-shapes/data.json)可导出；运行 `python3 calculations/calc.py plot-architecture-shapes`。两列比例不同，所示为FFN/专家矩阵而非全部算子；只有基线为发布配置，变体未训练，不据图推断同质量或运行速度。

**已复算（C13-expert-granularity）：** [专家颗粒度基线](../../calculations/results/qwen235-granularity-baseline.md)固定真实Qwen235B的128专家、FFN宽1536、top-k8；比较[64/3072/k4](../../calculations/results/qwen235-granularity-coarse64.md)与[256/768/k16](../../calculations/results/qwen235-granularity-fine256-k16.md)。这两变体保持专家总参数及激活专家参数，16token专家矩阵工作同为454,192,791,552 FLOPs；但router改变，使完整参数分别少24,641,536和多49,283,072，不能称严格等参。[256专家仍选8](../../calculations/results/qwen235-granularity-fine256-k8.md)把矩阵工作减半至227,096,395,776 FLOPs；[160专家对齐](../../calculations/results/qwen235-granularity-aligned160.md)保留宽度取整误差，[热点](../../calculations/results/qwen235-granularity-hot.md)保留负载倾斜。每矩阵M/N/K、逐专家token数、TP分片、EP消息目的集合和必要容量逐项输出。运行 `python3 calculations/calc.py qwen235-expert-granularity --format md`，`--inputs`指定experts/top_k等条件。只有基线为真实配置，其余未训练；专家工作减少不证明同质量或更快。选路标量、真实tile/带宽/运行峰值及完整请求时延仍另计。

**已复算（C13-architecture-variants）：** [声明架构变体](../../calculations/results/architecture-decode.md)保留官方Qwen3-8B基线；默认把KV头8→2、FFN宽12288→12800后，参数仍为8,190,735,360，单步矩阵工作仍为19,968,622,592FLOPs，KV却由147,456降至36,864bytes/token。变深/变浅与变宽/变窄按FFN对齐给真实参数差额及误差界；严格等参看实际标志，不能仅看名称。每步矩阵、norm复制、TP完整头、KV、串行层数及两类decoder collective分别列账；容量翻转区间含端点。[8192 prefill](../../calculations/results/architecture-prefill.md)、[6144+2048](../../calculations/results/architecture-prefix.md)和[单设备](../../calculations/results/architecture-single-device.md)使用同一变体契约。运行 `python3 calculations/calc.py architecture-variants --format md`；只有基线为真实checkpoint，其余未训练，不推断等质量或完整请求速度。

固定近似总参数预算，分别改变深度、隐藏宽度、FFN 比例、注意力头和专家数量。更深的模型增加逐层依赖与 KV 层数，更宽的矩阵改变分块与 Tensor Core 利用，更多更小的专家改变每专家 token 数、路由和 EP 的通信；较少激活专家也会改变能力和训练行为，不能只追求最小 FLOPs。

沿 Qwen3-8B 和 235B 的实际配置手算候选：128 个专家可以均匀分到八卡，但四个 KV 头不能在 TP=8 时继续无复制地均分为完整 KV 头，常见实现需要复制或改并行组合。整数可分只是起点，再用第 1 章方法比较逐卡峰值、矩阵形状、带宽、延迟与质量；完整 TP／PP／EP 方案在第 6 章展开。

> **实验 2-7 ★：模型规模与硬件的适配范围**
>
> 先选 8B 与 70B 的具体配置，对 24／80 GB 单卡逐项计算权重、KV、工作区与并发；改变精度或历史长度，观察可行范围怎样变化。再用 235B 的给定八卡放置结果说明“总容量够”仍需检查逐卡余量，完整切分留到第 6 章。层数、宽度与专家颗粒度的变体只比较结构带来的需求，不把容量通过当成同质量、可用吞吐或训练可行的证明；其余规模作为延伸扫描。
>
> 条件：基础·配置／手算／短脚本。

> **图 2-7：模型规模、精度与部署余量（配图计划）**
>
> 先画单设备上权重、状态与余量的构成，再用小型 SVG 对照相近参数预算下的深窄、浅宽和专家形状。逐 rank 的八卡阶梯曲线归第 6 章的放置计算，完整扫描作为配套材料；这里不画无条件的设备推荐表。

<a id="detail-2.6.3"></a>

### 2.6.3 多 token 预测与推理预算

**已复算（C14-v4-mtp-forward）：** [Flash单次MTP调用](../../calculations/results/v4-mtp-first-call.md)以调用方提供的Block42输出和token IDs为输入，仅执行第43层、ratio0的MTPBlock。e_proj处理BT行、h_proj处理4BT行，两者合计10BTH²；共享词表只投影每序列末位置。B1/T1默认1,796,997,120矩阵FLOPs，其中共享head为1,059,061,760。自有6,610,048,891逻辑参数与1,575条官方权重记录相符，checkpoint payload为3,593,787,756字节，不含共享embedding/head驻留。[B2/T16](../../calculations/results/v4-mtp-b2-prefill16.md)、[T129](../../calculations/results/v4-mtp-prefill129.md)、[历史128](../../calculations/results/v4-mtp-history128.md)分别核批量、窗口溢出和独立ring单槽写入。逐矩阵、norm/mHC/量化标量和特殊操作单列；接口字节为部分操作数，完整HBM与运行峰值未知。运行 `python3 calculations/calc.py v4-mtp-forward --format md`，用`--inputs`指定batch/tokens/start_pos/routing。输入特征对齐由调用方声明，不额外执行主干，不由本次调用推断草稿步数、接受率、验证/回滚或推测解码加速比。

**占位 TC-04：** 区分 MTP 的训练收益、草稿角色与推理验证收益，衔接第 8 章。 详见[成本下降调研](../../research/token-cost-2023-2026/report.md#speculation)。

用 DeepSeek-V4 与 Kimi K3 的 MTP 说明辅助训练目标与服务时草稿验证的联系。区分模型一次 forward 的结构、生成 token 的数量、并行候选与验证工作；reasoning 能力的训练与运行会改变计算预算，详细负载放到第 3 章。论文中的训练预测层与当前发布配置、推理后端启用的层数分别核对。

<a id="detail-2.6.4"></a>

### 2.6.4 从一次模型执行到请求轨迹

**已复算（C14-sealed-chat-resource）：** [封存Chat长度到Qwen8资源账](../../calculations/results/sealed-chat-known-prefill.md)选原始四条capture，累计753输入token、报告489缓存token、79返回ID（含EOS），不用重放条数替代原请求。按声明的逻辑前缀映射计算已知输入阶段，合计3,692,317,638,656矩阵FLOPs；实际模型调用次数、采样步骤和缓存恢复路径仍未知。[显式串行返回ID策略](../../calculations/results/sealed-chat-declared-serial.md)另声明每返回ID对应一步，得79次条件逻辑forward、4,836,064,624,640矩阵FLOPs；仍不把这些次数写成观测值。首输出来自prefill，后续只做G−1次decode，最后返回ID不再额外写KV。逐调用矩阵、已计接口及状态保留，walltime不当计算时间，工具等待为未知/不适用。运行 `python3 calculations/calc.py trace-resource-bridge --format md`，`--inputs`选择generation_policy。此连接说明如何将真实记录的可证长度代入模型公式；完整执行重建还需逐step输入、cache命中位置/恢复及采样日志。

当前实验 2-8 使用给定轨迹的长度字段核算资源；完整画像与分布归第 3.1 节。已封存的实验目录保留原名，其观测不因章节分工调整而重算或覆盖。

> **实验 2-8 ★：从请求长度计算模型需求**
>
> 读取给定 Chat／Agent 请求的输入、可复用前缀和返回长度，代入 Qwen3-8B 的层级资源表，分别计算本次输入、后续 decode 和保留状态。缺少调用或缓存恢复记录时列明假设；请求分布与复用间隔的统计在第 3 章完成。
>
> 条件：基础·给定记录与公式代入。

<a id="detail-2.6.5"></a>

### 2.6.5 给定请求下的模型比较

多模态理解之外，补一组[生成模型短例](../../case-studies/generative-multimodal-models.md)：Qwen3-Omni的编码器—Thinker—Talker/code2wav、Fish Audio S2 Pro的slow/fast AR与codec、Qwen-Image/FLUX的迭代latent生成，以及MiniMax-H3/Wan的视频生成。每类只保留主路径和一组配置，不把Omni视频理解当作视频帧生成；H3注意力投影宽度与hidden不同，继续按真实矩阵核算。

**已复算（R22-four-model-request）：** [四模型统一请求账](../../calculations/results/request-four-models-book.md)保持原实验Qwen3-8B、V4-Flash、V4-Pro和Kimi K3，统一S/P/G/B：已恢复前缀、本次输入、返回长度、batch。首输出来自输入阶段最后logits，所以后续只执行G−1次decode，最终保留S+P+G−1位置；最后返回token尚未重新送入模型。默认S0/P128/G4/B1的全请求矩阵TFLOPs分别为qwen3-8b 1.829869、deepseek-v4-flash 3.397735、deepseek-v4-pro 12.719961、kimi-k3 27.127914。逐阶段矩阵、已计标量/特殊操作、已知接口、状态增长和权重比较格式分别列账。[G1边界](../../calculations/results/request-four-models-first-output.md)无额外decode；[125+3跨压缩边界](../../calculations/results/request-four-models-prefix-boundary.md)和[6144+2048前缀](../../calculations/results/request-four-models-prefix-6144-2048.md)另列V4全部顺序输入及中间head计费。Qwen/K3 decode按经核对的历史仿射贡献累计，V4逐位置枚举压缩边界。运行 `python3 calculations/calc.py request-model-comparison --format md`；K3的A_log checkpoint/config冲突保留在总汇，前缀恢复成本、真实HBM/峰值、任务质量与延迟均未推断。相同token几何不保证相同文本或质量，不能据此给硬件吞吐排名。

先固定前缀、新输入、输出与 batch，比较不同结构的计算、容量、读取与更新；正文详解一个 Dense 与一个 MoE。请求分布由第 3 章建立，设备供给由第 4 章校准，缓存恢复与分离选择归第 8、9 章。扩写所需的完整四模型账见上文。

> **实验 2-9 ★★：请求条件下的模型选择**
>
> 固定同一请求输入，完整比较 Qwen3-8B 与 DeepSeek-V4-Flash 的 prefill、decode 每步及整段工作、常驻权重／状态、读取与更新。指出哪一项需求更高，并列出使模型选择成立的质量条件；V4-Pro 与 Kimi K3 作为迁移练习。设备供给与链路代价在第 4、6、7 章加入，此处不据模型需求表给出硬件性能排名。
>
> 条件：进阶·方案研究。

> **图 2-8：请求输入怎样变成计算与状态（配图计划）**
>
> 沿实验 2-8、实验 2-9 的一条请求，画前缀、新输入、首输出及后续 decode，并在对应位置标出计算与状态增量。完整长度分布、工具时序与 reasoning 画像归第 3 章；现有六面板图保留为素材，不在两章重复呈现。

## 原有写作资料

- 2.1 的起点：[Attention Is All You Need](../../references/files/papers/transformer.pdf)；[The Hardware Lottery](../../references/files/papers/hardware-lottery.pdf)。
- 2.2 的固定算例：[Qwen3-8B 官方配置](../../references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json)；[固定提交的 vLLM Qwen3 实现](../../references/outline-checks/2026-09-07/scaling-history/vllm-qwen3.py)；[Qwen3 技术报告](../../references/files/papers/qwen3.pdf)。
- 2.3 的状态比较：[MQA](../../references/files/papers/mqa.pdf)；[GQA](../../references/files/papers/gqa.pdf)；[Kimi K3 报告 §2.1.2](../../references/files/papers/kimi-k3.pdf)、[固定官方配置](../../references/outline-checks/2026-09-07/model-accounting/kimi-k3-config.json)与[参考执行代码](../../references/outline-checks/2026-09-07/model-accounting/kimi-k3-modeling_kimi_linear.py)。
- 2.4–2.5 的具体结构：[DeepSeek-V4 报告](../../references/files/papers/deepseek-v4.pdf)；[V4-Flash 固定配置](../../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-config.json)与[官方参考实现](../../references/outline-checks/2026-09-07/scaling-history/deepseek-v4-flash-inference-model.py)。
- 2.4 的混合结构：[Mamba](../../references/files/papers/mamba.pdf)；[Gated Delta Networks](../../references/files/papers/gated-delta.pdf)；[Kimi Linear](../../references/files/papers/kimi-linear.pdf)；[Qwen3.5 配置](../../references/files/models/qwen35-config.json)；[Kimi K3 报告](../../references/files/papers/kimi-k3.pdf)。
- 2.5 的专家演进：[Switch Transformer](../../references/files/papers/switch-transformer.pdf)；[DeepSeekMoE](../../references/files/papers/deepseek-moe.pdf)。
- 2.6 的规模与预算：[Llama 1 原始报告](../../references/outline-checks/2026-09-07/scaling-history/llama1-v1.pdf)，引言与模型规模表；[Qwen3 报告 §2](../../references/files/papers/qwen3.pdf)与[235B 固定配置](../../references/outline-checks/2026-09-07/scaling-history/qwen3-235b-config.json)。部署容量是本书按条件推算，不冒充论文给出的设计动机。
- 2.6 的请求分析与后续计算：[模型与算子核对笔记](../../case-studies/model-operator-examples.md)；具体任务轨迹在扩写时配套，不能以模型卡的最大上下文长度替代请求分布。
- 递推类比与计算细节：[Linear Transformers 作者说明](../../references/outline-checks/2026-09-07/edge-media/linear-transformers.html)；[模型资源计算笔记](../../case-studies/model-resource-accounting.md)。

原文版本、参数差异与扩写时需补的材料见[编辑笔记](../editorial-notes.md#ch-02)。
