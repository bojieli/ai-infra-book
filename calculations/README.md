# AI Infra 全书量化计算项目

本项目把大纲中的资源推导实现为可读、可复现的 Python 代码。先看[全书计划与 checklist](PLAN.md)，再看[已实现结果](results/README.md)。当前已覆盖多种模型的逻辑前向和硬件精度口径；全书计算仍有待办，不能将结果索引当作全书完成证明。

运行只需 Python 3.10+ 标准库，无需 GPU、模型权重或远程代码执行。已保存官方 config、必要参考源码及来源锁文件；数百 B／T 模型的完整权重不属于这些静态计算的输入。

## 直接复现

在书仓库根目录执行：

```bash
python3 calculations/calc.py models
python3 calculations/calc.py verify-sources
python3 calculations/calc.py reproduce
python3 -m unittest discover -s calculations/tests -v
```

也可以在 `calculations/` 下创建自己的虚拟环境后执行 `python -m pip install -e .`，使用 `infra-calc` 命令。数据目前随书仓库存放，使用源码 checkout／editable 安装，不将 wheel 当成脱离仓库的数据包。

## 模型支持范围

| 模型 | 官方配置 | 当前可计算 | 仍待完成 |
| --- | --- | --- | --- |
| Qwen3-8B、Qwen3-32B | 已下载，固定 revision | 完整 Dense 逻辑算子图、参数／矩阵／普通算术、逐算子载荷、KV、连续 decode | 后端 tile／实际 HBM／工作区测量 |
| Qwen3-30B-A3B、Qwen3-235B-A22B | 已下载，含 checkpoint 索引 | 完整 MoE 逻辑前向、官方索引权重核对、每专家矩阵、路由与专家并集、GQA 状态 | 实际 grouped kernel／HBM、专家并行通信 |
| DeepSeek-V4-Flash、DeepSeek-V4-Pro | 已下载，含 inference config/model/kernel | 基础前向汇总、注意力／压缩／索引、专家、mHC、完整 checkpoint 元数据与混合格式核对、已知 sparse/expert tile | 其余投影量化与 tile、运行时实际驻留／访存、MTP 执行 |
| Kimi K3 | 已下载，含 text/vision config 和参考源码 | 文本前向汇总、24 MLA／69 KDA、递推与块式数学算法、短卷积、潜空间专家、AttnRes、状态 | 解决 A_log 配置／checkpoint 形状差异、运行时量化转换、融合 kernel／访存、视觉／MTP 执行 |
| DeepSeek-V3 | config与参考实现已锁 | `v3-forward`基础前向账 | 完整FP8存储/运行时及MTP路径 |
| Qwen3.5-397B-A17B | config、实现、index及94分片元数据已锁 | 基础文本1038张量形状与checkpoint相符；视觉/MTP存储分账 | `qwen35-forward`提供基础文本参考路径、8场景及补充语句表；非完整运行时性能 |
| Qwen3-VL-4B | config、视觉实现及辅助源已锁 | `vision-encoding`、`vl-request`：视觉编码→语言prefill→decode | 完整checkpoint/后端访存与运行时间 |
| DeepSeek-R1-Distill-Llama-70B | 公开原发布者config/index及固定Llama/RoPE实现已锁 | 公共`forward`逐层矩阵/标量/权重/KV与独立RoPE初始化，四个场景 | 容量/放置专题接入、量化checkpoint及实测 |
| Llama-3.1-70B-Instruct | 原Meta配置请求401记录保留 | 未开放该模型计算；不改写为蒸馏模型身份 | 该具体仓库仍需合法可读输入，通用70B代表已用上一行独立模型满足 |
| Qwen3 Omni、Fish Speech S2 Pro | 根/组件config及参考实现已锁 | Omni理解的视觉/音频编码与Thinker请求；Talker/码本/codec、Fish slow/fast/codec分阶段工作 | 完整数值执行、实际缓存/流式取消与性能校准 |
| Qwen Image、FLUX2 Klein、Wan2.2、MiniMax H3 | 条件编码/denoiser/VAE等组件输入已锁 | 图像/视频生成的条件编码、迭代去噪、解码器及阶段状态 | 完整运行时融合/实际HBM、性能和质量实测 |

`models` 会分别报告 config、forward、base_forward_ledger、expert_matrices 和 state 状态；base_forward_ledger 指明带 coverage 缺项的专用汇总入口。未实现模型不能悄悄走 Dense 公式。

```bash
# 8192-token prefill：逐算子总表
python3 calculations/calc.py forward --model qwen3-8b --tokens 8192 --format md

# 36 层展开后的真实矩阵尺寸与读写量
python3 calculations/calc.py forward --model qwen3-8b --batch 64 --history 8192 --tokens 1 --format csv --output /tmp/qwen-decode.csv

# 已命中 6144-token 前缀，只处理新 2048 token
python3 calculations/calc.py forward --model qwen3-8b --history 6144 --tokens 2048

# 普通生成只计算最后位置输出头；训练／logprob 场景可以切换全部位置
python3 calculations/calc.py forward --model qwen3-32b --tokens 8192 --output-head all

# MoE：相同激活 FLOPs，不同批内专家并集与权重载荷
python3 calculations/calc.py forward --model qwen3-235b-a22b --batch 64 --history 8192 --tokens 1 --routing balanced --format md
python3 calculations/calc.py forward --model qwen3-235b-a22b --batch 64 --history 8192 --tokens 1 --routing concentrated --format md
# --routing-counts counts.json 可指定 128 项整数直方图；各层复用同一输入

# Pro 有自己的配置与层类型，不按 Flash 参数倍数缩放
python3 calculations/calc.py state --model deepseek-v4-pro --length 131072 --batch 64
python3 calculations/calc.py state --model kimi-k3 --length 8192 --mla-path expanded
# 独立 FFN 矩阵台账，不代替完整前向
python3 calculations/calc.py experts --model kimi-k3 --batch 64 --format md
python3 calculations/calc.py experts --model deepseek-v4-pro --batch 64 --routing concentrated --format md
python3 calculations/calc.py generate --model qwen3-8b --history 8192 --steps 1024
```

`generate --steps G` 数的是随后 G 次“追加一个 KV token”的模型调用，排除 prompt prefill。常见生成 API 已从 prefill 最后 logits 采出第一个 token，所以这个 G 不能不加说明地称作 API 返回的 G 个 token。

## 字节与运算怎样阅读

`weights` 中 shape 为框架 `[out,in]` 存储；算子同时给数学右乘形状。JSON/Markdown 的 `repeats` 表示这行算子出现的层数，每行成本先不乘它；CSV 按真实层顺序展开，便于逐项手算。所有参数计数与字节保持整数，不用 8B 标签反推精确权重。

`matrix_flops` 按 FMA=2 计有效因果位置；`rectangular_attention_matrix_flops` 给不跳过上三角的矩阵计数。`scalar_flops` 包含所声明算法的加减乘除，exp、rsqrt、比较、符号操作分列；它们不能直接拿 Tensor Core FLOPs/s 相除。`--output-head last/all/none` 明确输出头工作范围。

Qwen 的算子载荷采用可复算的独立算子模型：输入和权重理想读取一次，输出物化；注意力分数／概率默认 FP32 矩形物化。它显示融合可以消除哪些边，**不是整个模型的 HBM 下界，更不是某引擎的实测流量**。RoPE 表按同位置批共享，KV 按原位／分页追加，未计动态拼接整段复制；行内 FP32 临时归约视为片上。融合、tile 重读、L2、KV dtype 转换及分配器工作区随后由执行专题加入。

Qwen3 MoE 的每 token top-k 激活用于计算专家 FLOPs；每批非空专家的并集用于计算专家权重载荷。均匀／集中路由是声明的输入，不是观测轨迹；每专家矩阵保留实际 `n_e`，空专家不产生 GEMM 工作。路由另列 FP32 softmax、top-k、重新归一化以及参考实现的 int64 one-hot／where。Top-k 候选数不是比较 FLOPs，MoE 条件激活也不构成硬件 2:4 稀疏资格。当前 `generate` 仅支持 Dense；MoE 使用单次 `forward` 场景。

`experts` 提供 V4／K3 的独立 FFN 矩阵台账，并与 Qwen 完整前向交叉验证。V4 前三个 hash 层仍含 router GEMM，查表 int32 容量另列；K3 路由分支经过 7168→3584→7168 投影，共享分支仍处于 7168 维，第 0 层 dense 单列。台账的统一格式字节不等于 V4 FP4/FP8 或 K3 MXFP4 的真实存储，V4/K3 的路由、激活、潜空间 RMSNorm 及输出合并在 `non_matrix_operations` 单列：普通加减乘除与 sigmoid／tanh／softplus／sqrt 等原语分开，不折算 Tensor FLOPs。矩阵台账不包含这些标量工作；参考 dispatch 载荷由 `dispatch_operations` 单列：K3 的计数矩阵、排序端点、gather、拼接、重排与 FP32 加权归约；V4 的 int32／int64 路由索引、非空专家掩码、gather 及累加。CPU 计数传输单列，排序／直方图内部访存保持未知，通信仍待补齐。

状态结果将当前容量、选中历史载荷、recurrent 读写和新增写入分开。V4 的共享历史表示不再额外乘一次 K/V 的 2；Kimi K3 compact MLA 是教学执行路径，固定 HF 代码实际保存 expanded K/V。KDA state 的精度和短卷积槽假设必须保留。

## 官方硬件与 Roofline

[硬件表](results/hardware.md)和[机器可读输入](configs/hardware.json)目前已录入 54 个型号／配置及 276 条独立峰值记录，含 Apple 最新 M5 Ultra／M6；完整代际仍按 H01–H07 继续。[逐项审查记录](HARDWARE-AUDIT.md)说明来源差异和排除理由。每条记录保留官方原始值、表格／脚注、输入与累加精度、矩阵或 Vector/Cube 单元、dense 或 structured sparsity。`unspecified` 为尚未闭合的证据，不会自动进入精度明确的 Roofline。

```bash
python3 calculations/calc.py hardware --format md
python3 calculations/calc.py roofline --device rtx4090 --precision BF16 --accumulator FP32 --flops 165200000000000 --traffic-bytes 1008000000000

# 从官方模型形状算一层 Q 投影：固定 BF16 输入/输出、FP32 累加、dense、冷内存
python3 calculations/calc.py projection-bound --model qwen3-32b --device h100-sxm --tokens 8192 --format md
python3 calculations/calc.py projection-bound --device m2-max-38gpu-96gb --batch 256 --format md
```

这里的 FLOPs 与 traffic 是读者声明的同一工作／接口输入。命令按资源 `max(F/P,V/B)` 给下界，并给 ridge point；不把容量或依赖已经通过作为隐含前提。effective bandwidth 与 compute efficiency 默认为峰值 1.0，可显式下调作敏感性输入。

`projection-bound` 已登记27个真实Q投影场景；它只计算一层GEMM，保留A/W/Y和`beta=0`的字节条件。有内存带宽而缺精度峰值时，只给`memory_service_seconds`，完整Roofline值为`null`。GB系统记录标明GPU合计范围；单投影命令要求单设备，不能把机柜合计当作一个未切分GEMM的供给。

TF32 不等于 IEEE FP32；INT TOPS 不等于 FLOPs；MoE 的条件激活不等于 Tensor Core 的结构化稀疏。4090／5090 还要区分 FP16 与 FP32 累加。Apple Neural Engine TOPS 不填入 GPU Roofline。昇腾 Cube+Vector 合计不作为单个 GEMM 的峰值。Rubin 两份官方快照及 RTX PRO 白皮书／数据表取整差异保留在记录中。

## 文件与更新方式

- [scenarios/book.json](scenarios/book.json)：当前固定输入，修改后运行 `reproduce`。
- [configs/sources.lock.json](configs/sources.lock.json)：官方 URL、revision、下载时间、字节数和 SHA256。`fetch --model MODEL` 精确选择锁文件中的来源组，不自动扩展传递依赖或追随 `main`；已有书内官方 PDF 复用原件并校验。重取按锁定长度限制读取，核对长度、哈希及 Range 响应后，以独立临时文件原子替换；失败保留原件。
- [src/infra_calc/models/qwen3.py](src/infra_calc/models/qwen3.py)：从配置到权重、矩阵和逻辑算子的可读实现。
- [src/infra_calc/models/qwen3_moe.py](src/infra_calc/models/qwen3_moe.py)：官方 MoE 结构、显式路由分布和逐专家计算。
- [src/infra_calc/topics/experts.py](src/infra_calc/topics/experts.py)：V4/K3/Qwen 的分层专家、共享与潜空间矩阵台账。
- [src/infra_calc/topics/state.py](src/infra_calc/topics/state.py)：各架构独立状态计算。
- [inventory/sources.json](inventory/sources.json)：逐小节、逐练习、逐案例原文清单。`inventory` 检查变化，`inventory --refresh` 更新快照；内容变化重新进入待审，不因关键词匹配自动标完成。
- [inventory/legacy-scripts.json](inventory/legacy-scripts.json)：已有专题脚本的迁移候选，尚待逐个复核。

公共记录拒绝负工作量、布尔尺寸和非有限数值；合法空工作可使用零行矩阵。JSON 输出拒绝 NaN/Infinity。结果复验核对官方原件、计算源码、`calc.py` 入口、场景和已登记产物的哈希；这保证所声明输入与产物一致，不能代替全书覆盖审查。

计算记录同步到逐章扩写资料；已有跨章归属优先保留，不再把完整“已复算”段落重新插回主纲。主文的代表数字与论证由编辑选择。随后同步网页并验证：

```bash
python3 calculations/calc.py reproduce
python3 calculations/calc.py sync-outline
python3 scripts/render_outline.py
python3 scripts/verify_outline.py
python3 calculations/calc.py inventory --refresh
```

验收包含官方权重索引逐键／总字节对照、小尺寸因果位置枚举、前缀切分与累计 decode 守恒、V4/K3 独立手算及硬件精度／稀疏条件拒绝测试。仍需真实 trace、质量与性能的部分按计划保留，不能由通过单元测试推断性能成立。

## V4 mHC 残差计算

`python3 calculations/calc.py hyper-connections --model deepseek-v4-pro --batch 64 --tokens 1 --format md` 核算两套子层混合投影、FP32 Sinkhorn、残差汇合与最终 hc_head。实现见 `src/infra_calc/topics/hyper_connections.py`。矩阵 FLOPs、普通算术与特殊函数分开；容量只列独立张量，不冒充完整工作区峰值。固定参考代码在所有新 token 上执行 hc_head，即使词表投影仅取最后位置。

## V4 注意力矩阵

`python3 calculations/calc.py v4-attention --model deepseek-v4-pro --batch 64 --tokens 1 --history 8192 --format md` 输出低秩 Q、共享 KV、分组输出、压缩器与 Indexer 矩阵。参考执行路径支持初始 prefill 或单 token 增量；不把多 token 前缀续算套到单步分支。有效 QK/PV、参考矩形 Indexer 与假设因果裁剪的 Indexer 分开；压缩池化 softmax、norm、RoPE 和 Indexer 标量工作已在非矩阵表中单列；Hadamard／量化按原语列出，内部工作尚待补齐。`sparse_kernel_summary` 另计 64-slot tile GEMM、在线 softmax／sink、操作数载荷和源码显式共享／fragment 存储；`reference_with_sparse_tiles_matrix_flops` 使用 tile 工作，原 `matrix_flops` 保留有效 QK/PV 口径。源级存储声明不等同于编译后的工作区或设备可执行性。

## V4 专家存储与实际乘法精度

`experts` 结果的 `routed_expert_format` 记录官方参考 routed 专家格式：FP4 E2M1 packed 权重加每 32 个 K 元素一个 E8M0 scale，总计每参数 17/32 字节。该 kernel 先将 FP4 权重转为 FP8，实际为 FP8×FP8／FP32 累加；不能采用原生 FP4 峰值。每专家 M 维补齐到 32 的 tile FLOPs、每 K=32 子块的 scale 累加算术、FP8 激活量化缓冲分别列出。这只覆盖 routed 分支，不代表全模型混合格式已经完成。

## Hadamard 与量化模拟计量

注意力结果已展开 128 维 Hadamard 的数学蝶形工作和归一化缩放，采用固定 Dao-AILab 官方快照作为算法证据。该版本由本项目选定，不声称是 V4 发布环境的确切依赖版本。每行计 N log2(N) 加减与 N 缩放乘法，不等同于 CUDA shuffle／符号操作指令。FP4/FP8 模拟按 V4 固定 kernel 的每元素除法与反量化乘法、每组 scale 乘法计算；abs/max、clamp、指数位操作和格式转换保持独立原语。

## V4 基础前向汇总

`python3 calculations/calc.py v4-forward --model deepseek-v4-pro --batch 64 --tokens 1 --history 8192 --format md` 组合注意力、专家、mHC、状态与全局节点，JSON 的 `components` 保留每个子账。有效注意力口径和替换已知 sparse/expert tile 后的矩阵总数分开；参数按基础逻辑张量分项，不含 MTP、量化 scale 或整数 hash 表，已与完整 checkpoint 索引和全部分片头逐项核验：shape/dtype 字节、偏移连续性、索引覆盖与总载荷均一致。`coverage.missing` 列出剩余投影量化、运行时格式转换、复制、后端 tile 等；完整权重字节、HBM 和时延保持 null。该入口是可审查的汇总，不代表完整执行成本已经闭合。

## 官方 checkpoint 元数据

V4 Flash 的 46 个分片、69,187 个条目，Pro 的 64 个分片、145,116 个条目均已通过 HTTP Range 读取元数据头并锁定 SHA256；未下载张量载荷。`v4-forward` 的 `checkpoint` 分开报告基础模型、MTP、scale 和整数表，总载荷分别为 159,609,485,896 与 864,704,792,696 bytes。checkpoint 的 I8 是 FP4 packed 容器，hash 表为 I64；参考运行时声明的 int32 表和 FP32 转换副本须另计。`fetch` 对元数据原件保留 Range，服务器不遵守时拒绝整分片下载。

## Kimi K3 MLA 两种路径

`python3 calculations/calc.py k3-mla --path compact --batch 64 --tokens 1 --history 8192 --format md` 与 `--path expanded` 对照。expanded 对应固定 HF 缓存；compact 将 Wk 吸收到查询、在潜空间完成 PV 后再乘 Wv。全部矩阵尺寸、归一化、sigmoid 输出门控和缓存另列，小矩阵验证 QK/PV 代数等价。NoPE 配置仍保留额外 64 维分支，不能按字段名称补上不存在的 RoPE。FlashAttention 的 V padding 与实际 tile 工作不由逻辑 FLOPs 推断。

## Kimi K3 KDA 递推基线

`python3 calculations/calc.py k3-kda --batch 64 --tokens 1 --format md` 计算 69 层投影、短卷积、门控和递推算术。带下界 gate 使用 -5*sigmoid(exp(A_log)*(g+dt_bias))，不是未设下界的 softplus 分支。输出 RMSNorm 的 D=128 scale 在 heads 间共享。多 token 的结果是递推数学基线；固定 K3 实际使用 chunk prefill，其块内／块间数学工作见 `k3-kda-chunk`，融合 kernel 工作仍待补齐。FLA 选定版本是算法参照，未声称与 K3 发布依赖完全一致。

## Kimi K3 AttnRes

`python3 calculations/calc.py k3-attn-res --batch 64 --tokens 1 --format md` 展开每层 attention／FFN 及最终输出混合，保留块边界前后的候选数。最后有 8 个保存块，输出候选为 9；总共 186 次混合。块堆栈只在本次 forward 深度方向保留，不是跨 decode 步的缓存。每次调用一次的权重向量乘法与逐 token 工作分开，独立张量字节不直接加成峰值工作区。

## KDA chunk 分配与存活阶段

`python3 calculations/calc.py k3-kda-chunk --tokens 8192 --chunk-size 64 --format md` 按选定 FLA 实际分配列 Aqk／Akk、FP32 对角块、w/u/kg、chunk state、v_new 和输出。B=1、8K、chunk=64 时每层 chunk state 为 384 MiB，已知存活子集最大为 1926 MiB；它不是完整峰值，不含所有输入和后端 scratch，也不能乘顺序执行的 69 层。`mathematical_block_work` 已列单位下三角前代求解的各阶段矩阵／标量工作，并以标准库数值实现验证逐 token 等价；FLA 16×16 融合求解的实际 padding、指令和完整访存仍未计量。

`topics/kda_math.py` 提供可读的单 head 递推与块算法。输入为已归一化 Q/K、log 衰减和 sigmoid beta；测试覆盖不等 K/V 维度、非零状态和尾块。它用于验证代数与工作推导，不以 Python 循环耗时代替 GPU 性能。

## Kimi K3 文本前向汇总

```bash
python3 calculations/calc.py k3-forward --tokens 8192 --format md
python3 calculations/calc.py k3-forward --tokens 1 --history 8192 --mla-path compact --format md
python3 calculations/calc.py k3-forward --tokens 8192 --output-head all --format md
```

`k3-forward` 组合 MLA、KDA、专家、AttnRes、嵌入、外部归一化和词表输出，并保留分项与原始子账。`--output-head last` 对应官方文本模型的 `generation_mode=True`；全位置输出只改变词表头，最终归一化和 AttnRes 始终处理全部新 token。

`--kda-algorithm auto` 在单 token 时采用递推数学口径，多 token 时采用块式数学口径；显式 `recurrent`／`chunk` 用于算法比较。块式计算替换递推核心和衰减指数，不重复计入两套算法。compact MLA 是代数替代路径，非当前 HF 展开缓存实现。已核对官方全部 checkpoint 元数据，但发现 69 个 A_log 的长度与配置／代码不同，差异保留在报告中；checkpoint 字节已知，完整运行时驻留、访存和时延继续保持未知；普通算术和特殊函数不能直接套 Tensor 峰值。


K3 的 96 个官方分片共 497,220 个张量已读取元数据头（未下载张量载荷）。文本部分实际 checkpoint 载荷为 1,559,965,606,912 bytes；视觉塔和投影器另列。routed 专家使用 U8 容器存两枚 MXFP4 值，并按 K 方向每 32 个值保存一个 U8 scale；这不能用来断言 kernel 采用原生 FP4 计算或某个硬件 FP4 峰值。全部 69 个 KDA `A_log` 在 checkpoint 中为 `[128]`，同 revision config／代码要求 `[96]`；`config_checkpoint_shape_match=false`，差 2,208 个参数。详见 [K3 来源差异审查](K3-CHECKPOINT-AUDIT.md)。


## 整段生成与前缀缓存

```bash
python3 calculations/calc.py cache-sequence --model qwen3-8b --prompt 8192 --steps 1024 --prefix-hit 6144 --format md
python3 calculations/calc.py cache-sequence --model kimi-k3 --batch 64 --format md
```

P 个 prompt token 后再执行 G 次单 token 调用，旧历史读取记录数为 `GP+G(G−1)/2`，当前 token 操作数另加 G，追加写入也是 G，最终容量对应 P+G。无缓存对照按每次完整前缀重算投影行与因果矩阵工作，不能把末次长度简单乘 G。`cache_variants` 保留 Qwen 原生 GQA 和 MHA／MQA 架构对照，或 K3 expanded／compact；不把不同方案相加，也不以 KV 头数量比例缩减 Q 头的注意力工作。

命中 C 个前缀 token 可跳过 C 个投影行及 C(C+1)/2 个因果位置对，后缀仍访问这段历史；未建模物理共享时，最终每请求容量不变。K3 的前缀状态还必须包括准确边界上的 KDA recurrent 与短卷积状态。完整命中若需立即产生 logits，仍需复用边界输出或重算边界，不能把本报告的零新增 attention 工作解释为零请求成本。载荷不含工作区、量化元数据、分配对齐、并行复制或真实 HBM 流量。


## 第 1 章单位、逐卡容量与链路预算

```bash
python3 calculations/calc.py resource-basics --format md
python3 calculations/calc.py resource-basics --weight-bits 8 --cards 1 --format md
python3 calculations/calc.py resource-basics --payload-bytes 4096 --messages 4 --format md
```

这里的 70B 是正文明确的名义教学参数，不能代替真实 checkpoint 的计数。每卡分别计算打包权重、元数据、状态、工作区和容量余额；`--shard-parameters` 接收每卡参数数目的 JSON 列表，检查总数守恒。默认均分是算术分配，不证明真实模型支持该切分。零状态／工作区预算仅表示本例未纳入，不是部署保证。

链路输入单位为 bit/s，输出区分十进制 GB/s 和二进制 GiB/s；`--payload-bytes` 是全部串行消息的总载荷，`--messages` 只增加启动次数。`nα+V/B` 的效率由场景指定，不冒充设备实测；4 KiB 与 64 MiB 场景用于比较启动项和带宽项。


## 独立访存窗口

```bash
python3 calculations/calc.py memory-concurrency --format md
python3 calculations/calc.py memory-concurrency --transactions 4096 --bandwidth-bytes-per-second 2000000000000 --format md
```

载荷来自固定 Qwen3 配置；接口条件为显式教学输入。`min(B,Ns/L)` 限制吞吐，`ceil(BL/s)` 给供满接口所需的独立事务数量。CLI 延迟用整数纳秒，带宽用单向 bytes/s。N 不等于 batch 或 GPU 线程数；本例改变 batch 只改变载荷，事务窗口保持用户指定值。服务下界、固定事务打包量与未知实测值分开，不输出完整 decode 时延。


## 70B 解码预算与敏感性

```bash
python3 calculations/calc.py decode-budget --format md
python3 calculations/calc.py decode-budget --batch 64 --kv-history-bytes-per-request 1073741824 --workspace-bytes 2147483648 --format md
```

正文名义 70B 模型采用 `2NB` 初步矩阵近似；官方 H100 SXM 的 BF16／FP32 累加／dense 峰值与内存带宽分别提供资源分母。4/8-bit 仅描述压缩存储，假定恢复为 BF16 计算，转换成本不在初步下界中。算力／带宽倍数是受控假设，不代表其他设备。参数与 KV 不从不同真实模型拼接，真实 Qwen 计算继续使用 `forward`／`projection-bound`。

权重在 batch 内读取一次，KV 历史与追加按请求计，容量包含声明的元数据／工作区。失败场景不输出可运行下界或吞吐；交叉 batch 同时报告是否符合容量。默认 KV／工作区为零代表权重主导的第一遍估算，不是完整推理部署。通信的 `nα+V/B` 见 `resource-basics`，独立访存限制见 `memory-concurrency`。


## Ring 集合通信

```bash
python3 calculations/calc.py ring-collective --participants 4 --format md
python3 calculations/calc.py ring-collective --tokens 8192 --participants 8 --format md
```

消息来自官方 Qwen3 Dense 的 BF16 `[B*T,H]` 输出；逐轮输出发送方、接收方和分片。reduce-scatter 每 rank 从 M bytes 变为 M/p，all-gather 从 M/p 变为 M；全体网络载荷按发送端累计一次。默认每层两个输出归约，串行 2L 次为指定基础 TP 路径，未计融合／重叠／归约执行与拓扑争用。启动 2 μs、单向 50 GB/s 是教学条件，不是 NCCL 实测；权重和 KV 的逐卡放置须另外验证。


## 树形集合通信对照

```bash
python3 calculations/calc.py tree-collective --participants 5 --format md
python3 calculations/calc.py tree-collective --tokens 8192 --participants 8 --format md
```

这里实现根为 rank 0 的未分段 binomial reduce 加反向 broadcast，每条边传完整消息，各轮之间有依赖。支持非二次幂参与者；逐 rank 发送／接收和归约加法明确列出。与 ring 同为 `2(p−1)M` 全网发送量，但轮次、最忙 rank 与关键路径不同；小消息和大消息的算法排序可以翻转。这个具体算法不代表 NCCL 双树、分段树或所有树形实现，未计拓扑争用和归约执行成本。


## MoE all-to-all

```bash
python3 calculations/calc.py all-to-all --routing balanced --format md
python3 calculations/calc.py all-to-all --routing hotspot --format md
```

Qwen3 MoE 官方隐藏宽度和 top-k 决定 assignment 向量大小及每源分派总数；`--counts` 可传源—目的计数矩阵。每个目的 rank 的分派受实际专家数约束，本地对角项不进入网络。当前每个 token-expert assignment 独立发送完整 BF16 向量，未按目的端去重；combine 转置矩阵。pairwise offset 轮次保留最大边等待，端点带宽下界独立列出。均匀和热点可以有同样总载荷，却有不同最忙接收端；拓扑、数据打包、元数据和专家执行仍需另计。


## 物理路径、共享接口与 NUMA 中转

```bash
python3 calculations/calc.py numa-staging --format md
python3 calculations/calc.py numa-staging --placement sender-local --order alternating --format md
```

公共 `traffic.account` 将每条逻辑发送映射到显式资源路径：共享接口累加所有经过它的流量，重复资源表示多次服务。它同时输出总资源 `max(V/B)` 和逐轮 `sum(max(V_round/B))`；后者保留轮次依赖，两者都不是完整执行时延。

四卡 PCIe 教学场景分别计每卡双向接口、每个 NUMA 的 DRAM 读写合计、CPU 间双向流量。不假定 GPU P2P，也不因没有 CPU memcpy 就忽略主机内存流量。缓冲流量不等于驻留容量；分块深度、桥接争用、协议和实测仍待输入。


## MoE 目的端去重与部分归约

```bash
python3 calculations/calc.py moe-dedup --pattern clustered --format md
python3 calculations/calc.py moe-dedup --pattern spread --format md
```

`--routes` 接收 `[source_rank][token_index][expert_id]` 三维 JSON，每个 token 必须有官方 top-k 个不同专家。默认两种路由的 assignment 直方图相同，却有不同 token→目的 rank 集合，说明不能只用计数矩阵推断去重。dispatch 每个目的 rank 仅发送一次输入；combine 在目的端先合并已加权专家输出，再返回部分和。专家矩阵工作不变，归约加法在目的端和源端之间转移，总数守恒。

发送输入为 BF16；返回默认每元素四字节，baseline 和优化方案保持同口径，可显式设置。元数据、路由概率传输、缓冲、打包和计算依赖未计入，浮点重结合也不保证逐位相同。JSON 保存完整 token 身份，Markdown 显示汇总矩阵与归约位置。


## 实际权重形状与单设备容量

```bash
python3 calculations/calc.py capacity-scan --model qwen3-8b --format md
python3 calculations/calc.py capacity-scan --model qwen3-235b-a22b --length 32768 --format md
```

Qwen 权重形状沿用已与官方索引核对的枚举，MoE 包含全部专家。BF16 全量基线与两个教学低位宽方案分别报告：矩阵按输出行打包，每 `--group-size` 个 K 元素保存 `--scale-bytes` 元数据；嵌入、词表头、router 和 norm 保留 BF16，使用无 zero-point 的对称方案。低位宽不是某个实际下载的量化 checkpoint，也不保证内核或质量兼容。

默认扫描 24／48／80 十进制 GB 的单设备预算，可用 `--capacities` 提供 bytes 列表。每请求 KV 来自固定配置，工作区默认 2 GiB，是明确保留量而非实测峰值。整数除法给预算下的最大并发，并检查多一份请求是否超限；零并发与权重预算失败分别显示。八卡不能把容量直接相加，须继续核对真实切分、复制和逐卡余量。


## Dense TP／PP／DP 逐卡放置

```bash
python3 calculations/calc.py dense-placement --tp 2 --pp 4 --format md
python3 calculations/calc.py dense-placement --tp 16 --format md
```

权重从实际 Qwen Dense 形状切分：Q／FFN／词表行分片，O／down 输入列分片，norm 复制。KV 头由每 rank 的 Q 头身份与 GQA 分组推导；TP 超过 KV 头数时复制完整 KV 头与对应 K/V 投影，不分配分数个头。PP 按连续层分组，首阶段拥有嵌入，末阶段拥有 final norm 和输出头；DP 是独立推理副本，`--batch-per-replica` 是每副本请求数。

JSON 列出每卡权重形状与 copies、有效矩阵工作、KV 和声明工作区预算，以及两次输出归约和 PP 边界载荷。PP 边界采用各 TP rank 发送完整 hidden 的显式方案，因此包含 TP 副本；其他接口切分须另算。嵌入归约、logits 收集、标量成本、工作区生命周期、气泡和真实后端可用性仍待补齐，当前不预测迭代时延。


## Dense 基础通信路径

```bash
python3 calculations/calc.py dense-communication --tp 8 --format md
python3 calculations/calc.py dense-communication --tp 2 --pp 4 --format md
```

基础词表并行方案需要嵌入输出归约，不仅是每层 attention／FFN 的两次归约。末阶段收集最后位置 logits 后，由 rank 0 本地采样；跨 PP 回传 int32 token ID，再在首阶段 TP 组广播。logits 默认每元素四字节，可显式设置，未声称是所有框架的线格式；分布式采样也可以使用其他通信策略。

每个操作列阶段、层、轮次和网络总字节，时长仅为声明独立链路下串行通信路径的模型。采样／矩阵计算、控制元数据、重叠、共享资源和气泡不在这个总数内。DP 增加聚合字节而保持独立副本路径时间；如果共用物理网络，必须另做资源映射。


## 推理流水、反馈与边界缓冲

```bash
python3 calculations/calc.py pipeline-schedule --microbatches 1 --format md
python3 calculations/calc.py pipeline-schedule --microbatches 8 --stage-ns 1000000 2000000 1000000 1000000 --format md
```

阶段耗时、边界传输和反馈延迟全部显式输入；默认是教学条件，未从理论峰值伪造实测。每个微批代表固定的一组请求，各步仍有生成反馈依赖。固定 step-major FIFO 顺序同时约束阶段和链路，计算与独立传输资源可并发；调度策略不宣称最优。

发送缓冲从产出保留到传输完成，接收缓冲从传输开始保留到消费阶段完成，输出它们的单独及联合峰值。边界激活尺寸来自 Qwen3 BF16 隐藏宽度；完整 KV、权重、阶段内部激活和工作区未纳入。默认保持无限队列基线；`--buffer-slots` 启用每个边界双端的有限槽位与反压。初次完成不是包含 prefill 的 TTFT，阶段空闲也不等于一种统一的训练气泡率。


有限槽位模式采用明确的保守策略：计算开始前先保留输出槽，传输开始前先取得接收槽。发送槽到传输完成才复用，接收槽到消费计算完成才复用。`pipeline_transfers` 记录槽号、保留及释放时刻，`reserved_boundary_pool_bytes` 是预留池，`declared_boundary_buffer_peak_bytes` 是活跃峰值。局部缓冲等待单列，但可能互相重叠，不再加到 makespan 上。无限模式仍按产出时分配发送缓冲，两种分配策略在说明中明确区分。

### Dense 训练矩阵与 SFT mask

`python3 calculations/calc.py training-matrix --model qwen3-8b --tokens 8192 --format md`
按固定官方配置逐项列前向、输入梯度和权重梯度，并与全部参数的 `6ND` 比较。
用 `--supervised-tokens 4096` 声明有效标签数，普通输出头仍计算完整行；加入
`--head-strategy compact` 才声明先筛选 hidden 再执行输出头。两个场景主干工作相同。
`--gradient-bytes`、`--master-weight-bytes` 控制声明的参数状态格式；激活峰值和完整训练步成本保持未知。
七个固定场景（含 Qwen235B 均匀／集中专家路由）见 [结果索引](results/README.md)，实现见 [training_matrix.py](src/infra_calc/topics/training_matrix.py)。

### RL 候选与有效样本批次

`python3 calculations/calc.py rl-cycle --format md` 输出 Qwen 教学循环的 rollout、reference、teacher、更新矩阵工作和一次 BF16 权重同步载荷。
`--prompts 16 --accepted-samples 16` 与默认场景保持相同接受样本目标，比较更多拒收候选的开销。
`--reference-passes 0 --teacher-passes 1 --update-epochs 2` 声明评分与更新次数。
生成首 token 来自 prefill，训练输入 P+G−1 与 G 个监督标签分别保存。非矩阵／验证／阶段时延不猜测，完整周期成本留空。
实现见 [rl_cycle.py](src/infra_calc/topics/rl_cycle.py)，五个固定场景见 [结果索引](results/README.md)。

### RL 条件式资源供给

`python3 calculations/calc.py rl-supply --format md` 使用明确标记的教学供给。
`python3 calculations/calc.py rl-supply --inputs calculations/scenarios/rl-supply-example.json --format md`
可修改每阶段资源池与有效矩阵速率、验证服务时间／workers、同步带宽和 pool 倍率。
同一池的服务需求相加；孤立批次串行组件时间与理想多批流水间隔下界分开。
该下界不证明 on-policy 依赖允许流水，也不包含全部训练执行开销。
实现见 [rl_supply.py](src/infra_calc/topics/rl_supply.py)，JSON 示例见 [输入文件](scenarios/rl-supply-example.json)。

### 成对请求长度与 FIFO 重放

`python3 calculations/calc.py request-trace --inputs calculations/scenarios/request-trace-example.json --format md`
读取每条请求的到达时间、输入／输出长度、prefill 和每步 decode 服务时长。
输出逐请求官方矩阵工作、FIFO 开始／完成／等待／TTFT、nearest-rank p95，以及 BF16 KV 预留／释放时间线与峰值。
五个场景比较相同平均长度下的尾部、长度相关性和到达间隔，并包含 Qwen235B。
每个 worker 独占请求；时长是输入，未模拟 continuous batching 或共享设备争用。
实现见 [request_trace.py](src/infra_calc/topics/request_trace.py)，[示例输入](scenarios/request-trace-example.json)可编辑。

`python3 calculations/calc.py request-trace --inputs calculations/scenarios/request-trace-capacity.json --format md`
增加有限 KV 准入预算。准入时预留声明上限 P+G−1 的槽位，FIFO 队头不被后来的小请求越过；单请求独占也放不下时拒绝输入。
结果将活跃 KV 与准入预留的峰值／存活面积分开。容量只控制 KV，不含模型权重或工作区。
256／512 MiB 对照与无容量门限的轨迹保持相同工作量，展示缓存预算对等待的影响。

### 真实 Agent 轨迹与关键路径替换

`python3 calculations/calc.py agent-trace --trace thinking-on --model-speedup 2 --selected-turn 0 --format md`
复用实验 3-4 的实际逐轮 token ID、缓存命中、模型／工具墙钟与独立任务检查。
两条原始轨迹已保存独立副本并核对原实验 manifest；[锁文件](configs/agent-traces.lock.json)记录 SHA256 和原始路径，复现 manifest 也覆盖这些输入。
输出命中／冷重算矩阵工作、实测各段时间、保留其它时段的条件式替换，以及假设 KV 驻留工具等待的 byte·s。
实际缓存峰值保持未知；失败尝试、截断和额外别名检查不丢弃。实现见 [agent_trace.py](src/infra_calc/topics/agent_trace.py)。

### 实时音频时序

`python3 calculations/calc.py audio-timing --inputs calculations/scenarios/audio-timing-example.json --format md`
计算输入帧就绪、串行模型／发送、逐块传播抖动、按序播放与静音响应。
默认参数均是教学输入。固定播放截止与停顿后的实际播放时间分开，ready queue 支持乱序并只计未播放数据。
打断只投影到控制延迟和设备量子后的静音，不声称 GPU 工作已取消。
实现见 [audio_timing.py](src/infra_calc/topics/audio_timing.py)，五个场景见 [结果索引](results/README.md)。

### GEMM 循环、容量与接口流量

`python3 calculations/calc.py gemm-tiles --capacity-bytes 24576 --format md`
使用官方 Qwen3 Dense 单支 up projection，枚举输出 tile、BF16 输入与 FP32 累加容量及下一层访问量。
`--order k-outer` 增加 partial 写回／重读；`--input-buffers 2` 比较双缓冲容量；`--tokens 1025` 检查尾块。
有效数学 FLOPs、完整 padding tile 工作和实际元素载荷分列，最佳候选不等于性能最佳或全局下界。
实现见 [gemm_tiles.py](src/infra_calc/topics/gemm_tiles.py)，五个固定场景见 [结果索引](results/README.md)。

### RMSNorm 行拆分与 partial

`python3 calculations/calc.py row-reduction --rows 1024 --splits 8 --format md`
对照一组一行与三阶段拆分归约，分别计量输入重读、FP32 partial、inverse 和输出接口载荷。
`--splits 7` 覆盖尾部，`--width-multiplier 16` 是明确的教学加宽变体。
总归约加法守恒，分组的 FP32 舍入仍可能不同；数值反例与数学归一化对照均有检查。
实现见 [row_reduction.py](src/infra_calc/topics/row_reduction.py)，不由组数或字节直接预测加速。

### Bank 映射与同址读取

`python3 calculations/calc.py bank-mapping --stride-words 33 --format md`
展开 32 lane 的标量字地址、bank、端口请求与服务轮数。
`--access same-word --broadcast` 只合并同一地址的读取；同 bank 不同地址仍冲突。
正文的 32／33 行跨度 padding 已对上，CUDA 13.2.1 官方原件已锁定。
`--ports 2` 是假设的服务端口变体；标量布局不冒充 TMA swizzle，轮数不等于 kernel 加速。
实现见 [bank_mapping.py](src/infra_calc/topics/bank_mapping.py)。

### 小矩阵 C 循环与已有实测

`python3 calculations/calc.py loop-access --m 127 --k 257 --n 65 --format md`
按实验5-1固定 C 实现计数组表达式：A/B读取、C读改写及memset清零元素。
四个原形状、八种方法／tile 的九次样本按完全匹配重新取中位数；新形状的时间留空。
源码和原测量已复制到独立来源并锁定哈希，源码字节不等于机器指令或缓存／DRAM流量。
实现见 [loop_access.py](src/infra_calc/topics/loop_access.py)，输入锁见 [cpu-loops.lock.json](configs/cpu-loops.lock.json)。

### 融合边界与张量生命周期

`python3 calculations/calc.py fusion-lifetime --layout-copy --format md`
从官方 Qwen3 gate/up 输出形状枚举 SiLU、乘法、可选布局重排和固定尺度 cast 的连续融合边界。
每组输出先分配、输入最后消费后释放，输出接口字节和活跃张量联合峰值；逐组集合与释放表保存在 JSON。
固定尺度和1-byte存储只是声明方案，不包含动态scale、实际FP32 scratch或allocator保留池。
实现见 [fusion_lifetime.py](src/infra_calc/topics/fusion_lifetime.py)，四个固定场景见 [结果索引](results/README.md)。

### 量化融入 GEMM 的输入重读

`python3 calculations/calc.py quantized-gemm --format md` 复算 Qwen235B 单专家投影的444／620／588 MiB主张量接口。
`--tile-n 1536` 改变输出列块复用，`--tokens 4097 --tile-n 127` 检查尾部。
全行scale读写单列；前缀scale方案不标为数值等价，未知工作区和HBM保持空值。
实现见 [quantized_gemm.py](src/infra_calc/topics/quantized_gemm.py)，格式和专家token数为显式教学输入，形状来自官方配置。

### 融合数值语义反例

`python3 calculations/calc.py fusion-numerics --format md` 用精确有理数复算全行／前缀FP8量化的55/56对1反例，另报告FP16结果。
`--larger-first` 同时交换值和权重的块序，数学点积不变，前缀舍入路径改变。
ONNX官方E4M3FN原件已锁定；有限编码及最近偶数中点逐项检查。另含不可逆零因子状态丢失反例，不执行作者GPU代码。
实现见 [fusion_numerics.py](src/infra_calc/topics/fusion_numerics.py)。

### 在线 Softmax 可合并状态

`python3 calculations/calc.py online-softmax --format md` 复现正文−1/7与错误块均值1/6的对照。
`--inputs calculations/scenarios/online-softmax-example.json` 可输入多维值、分块和显式掩码；空块以空状态作单位元，全掩码输出留空。
顺序／树形合并用独立稳定Softmax检查，特殊函数和合并算术分列；这不是GPU kernel工作量或逐位一致保证。
实现见 [online_softmax.py](src/infra_calc/topics/online_softmax.py)。

### 注意力 tile、容量与缩放代价

`python3 calculations/calc.py attention-tiles --format md` 复算官方Qwen单头d=128、8192长度和128KiB预算下的204／304／436 MiB。
`--causal --kv-slots 2` 同时启用因果tile跳过和K/V双槽，重新计算最大Q块与接口流量。
有效矩阵工作、访问矩形tile、完整padding和旧输出缩放次数分列；循环更新不是主机launch。
实现见 [attention_tiles.py](src/infra_calc/topics/attention_tiles.py)，真实scratch、GQA跨头复用与HBM另算。


`python3 calculations/calc.py host-transfer --format md` 复算 Qwen3-8B 的64 MiB激活搬运。
默认八块，准备1 ms、单向有效24 GiB/s、消费4 ms均是教学输入：串行60.833333 ms，主机／设备各双槽35.604167 ms，两侧各预留128 MiB。
`--device-slots 1` 为53.833333 ms；`--bandwidth-bytes-per-second 12884901888` 为46.666667 ms。每块同时保存精确有理数秒与显示时间，主机槽在复制结束释放，设备槽在消费结束释放。预留容量和活跃峰值分别报告，实际锁页成本／共享带宽竞争／完整显存与实测耗时仍需另算。


`python3 calculations/calc.py stream-buffer --format md` 复算五个16 KiB块的FIFO占用、独立重排槽与背压。原进度需48+32=80 KiB，64 KiB预算下两块FIFO让最后生产从第8格推迟到第9格，最后取走仍为第13格。
`--reorder-slots 0` 比较已统一布局；`--budget-bytes 49152` 比较单块FIFO；`--produce-interval 3` 比较更慢生产者。时间格开始取走、结束发布，输出保留逐事件占用。扣除重排后不足一个块时有限调度留空，本模型没有零容量直接交接。


`python3 calculations/calc.py graph-execution --format md` 按官方Qwen形状复算图边界复制、单层FFN padding、额外准备的回本次数与配置／设备流水。
`--input-tokens 2048 --calls 1000000` 比较大输入和更长实例寿命；直接写稳定输出只在相应接口存在时成立，不参与外部输入路径选择。2 TB/s与各项耗时为教学输入，原输入读取仍需保留。结果分别列不亏和严格更快的整数阈值、稳态与含准备总时间；配置流水计入填充排空，不能与串行图预算混加。


`python3 calculations/calc.py optimization-deployment --format md` 复算正文候选A／B分数与部署时间。
`--inputs calculations/scenarios/deployment-example.json` 可更改形状频数、候选耗时、显式验证状态、分派开销和相对统一路径的额外准备。失败／缺失候选评分记零，部署按原路径耗时回退；逐形状选择仅使用有效候选及baseline。回本分别按平均调用和完整频数组求精确整数阈值，教学串行预算不替代真实请求关键路径。


`python3 calculations/calc.py shape-specialization --format md` 计算官方Qwen单层FFN在通用／分桶／逐形状特化三种互斥方案下的工件准备、padding与重复执行成本。
`--inputs calculations/scenarios/specialization-example.json` 可修改真实形状频数、桶、特化集合、缓存工件和服务率。未覆盖形状回退通用，每个实际使用的工件只准备一次；交点用有理数仿射条件保存。默认准备与吞吐均为教学输入，不作为真实编译器性能。


图5-6使用可选Matplotlib依赖，不改变核心计算的标准库入口。可在自己的虚拟环境中运行 `python3 -m pip install -e 'calculations[plot]'`，先 `python3 calculations/calc.py reproduce`，再 `python3 calculations/calc.py plot-specialization`。图读取已校验的specialization-medium结果，输出到 `figures/specialization/`，包含SVG、PNG、精确逐点JSON和独立manifest；`verify-results` 同时检查已有图的输入与产物哈希。改变图输入或脚本后须重新绘图。


`python3 calculations/calc.py runtime-trace --tokens 32 --format md` 重新统计锁定的实验5-8样本、主机Launch API与设备kernel事件；`--tokens 1` 和 `--tokens 257` 选择其它已记录形状，Nsight只有32-token采集。
原实验的21计时方案／63输入更新检查／9时间线已离线验证；计算项目复制记录并校验SHA256。官方Qwen FFN维度用于工作量和显式张量账，随机BF16权重不是完整模型权重。共享GPU的全部计时范围保留，CUDA event与CPU提交不可相加；MPK作者A100结果单列，未将论文比值乘入本机性能。


`python3 calculations/calc.py persistent-tasks --format md` 比较官方Qwen单支up→SiLU的整算子屏障与逐行块就绪，声明独立矩阵／向量worker。一次主机提交仍需每块两个设备任务和完成事件；`--task-dispatch-ns 50000` 检查分派成本反转，`--tokens 513` 检查尾块，`--tile-rows 512` 检查无跨块重叠。时序用有理数递推，任务元数据服务量与关键路径分列；没有实现MPK、没有消除中间写读，也不推定真实SM可同时驻留。


`python3 calculations/calc.py request-dag --format md` 检查局部加速后的请求关键路径。
`--inputs calculations/scenarios/request-dag-example.json` 可输入节点时长、依赖、容量一的串行资源及修改后的时长／资源映射。按最早可启动的确定性列表规则调度，资源前序边与原始依赖共同用于路径追踪；输出旧路径冻结值、重新计算的请求耗时与全部任务串行化比值。拒绝循环依赖和未知节点；教学例不替代实验5-9真实引擎校准。


`python3 calculations/calc.py microbatch-overlap --format md` 复算正文Qwen FFN两微批的1.20／1.36／1.16／1.28 ms时序；`--inputs calculations/scenarios/microbatch-overlap-example.json` 可修改两份大小、独占服务时间和联合窗口。
矩阵工作守恒，独立无缓存读取两遍权重的逻辑流量与唯一容量分列；联合窗口必须严格小于0.52 ms才胜过本例原batch。联合窗口是显式教学输入，不是自动预测的并发性能，也没有把N阶段与权重读时间强行等同。


`python3 calculations/calc.py topology-allocation --format md` 复算ring端口带宽重构、额外准备回本、4×4周期位置的相邻2×2作业分配及有向割集。
`--inputs calculations/scenarios/topology-allocation-example.json` 比较decode消息与更长寿命。小规模放置枚举不相交窗口最大集合，反向容量不抵扣正向需求；放置、割集与端口情景分别检验，未声称已找到真实端到端可行方案。


`python3 calculations/calc.py collective-paths --format md` 逐条枚举16节点双向物理环上递归与Swing前三轮消息；`--tokens 1` 比较decode，`--bandwidth-bytes-per-second 25000000000` 改变教学有效链路速率。
路径采用官方Swing式2，原文按归档manifest核验并复制入统一来源。方向独立、接收不重复累加，JSON保留每条路径、逐链路消息／字节及聚合／逐轮下界。仅覆盖已核对前三轮，拒绝第四轮，不冒充完整集合算法或包级网络仿真。


安装可选plot依赖后运行 `python3 calculations/calc.py plot-collective-paths`，从已校验的collective-paths-book生成图6-4物理路径面板。六面板统一色标，内环箭头顺时针、外环逆时针，灰色为零负载方向；每面板统计所有16个发送者，并另列rank0路径。SVG／PNG／逐边JSON及manifest位于 `figures/collective-paths/`，`verify-results` 同时检查已有图的输入和产物哈希。


`python3 calculations/calc.py periodic-queue --format md` 复算周期通信高峰、错峰及漂移下的流体队列。
`--inputs calculations/scenarios/periodic-queue-example.json` 可指定不同周期／on时长／相位／到达率，默认观察周期LCM窗口、起点空队列。精确排空时间将积分区间拆开，输出队列面积、超额需求和残留；兼容度可为负。可用initial_queue_bytes与buffer_bytes指定初始积压和有限缓冲，输出溢出丢弃；末尾排空只在停止后续到达的条件下成立。

`python3 calculations/calc.py feedback-queue --inputs calculations/scenarios/feedback-queue-example.json --format md` 复算一次显式反馈延迟。80→40GB/s、出口50GB/s、20us反馈、初始256KiB时，512KiB缓冲丢弃337856 bytes，72.4288us排空；1MiB缓冲无丢弃。减速至出口速率只停止增长，不能排空积压。反馈速率是教学输入，不是DCQCN/PFC控制器或硬件测量。

`python3 calculations/calc.py packet-reorder --inputs calculations/scenarios/packet-reorder-example.json --format md` 用官方hidden_size构建BF16消息，逐路径串行发送并按序交付。输出逐包发送、重传、接收释放事件及保留面积；同刻到达先合并再释放连续前缀。四场景区分路径偏斜、明确丢失和恢复延迟；只重发声明丢失的报文，未建ACK／超时检测或实际OpenURMA协议。

`python3 calculations/calc.py collective-tail --inputs calculations/scenarios/collective-tail-example.json --format md` 复算全部rank就绪后交换的屏障教学模型。每条记录保留就绪／交换／恢复联合关系与整数次数，按ceil(p*N)计算有限样本分位数；对照交换加速、就绪对齐与消除恢复，不将rank等待之和当墙钟、不将边际p99相加。官方模型确定BF16消息字节，时间须独立给定。

`python3 calculations/calc.py connection-states --inputs calculations/scenarios/connection-states-example.json --format md` 枚举本机线程到对端的活跃关系，按对端和隔离类统计共享传输状态。可输入稀疏关系；端点、关系绑定与传输状态分别计容量，空闲已分配端点仍计入。默认字节是假设，不代表真实NIC结构；四场景包含完整连接、八类隔离、每线程独占与单热点对端。

`python3 calculations/calc.py operation-ordering --inputs calculations/scenarios/operation-ordering-example.json --format md` 复用DAG调度比较全完成串行和必要发布依赖，区分独立资源与共享串行资源。另给D/F两个4-byte标量的投机旧读见证，标实际取值、冲突检测、重读和交付；响应排序不能修复保存的旧值。模型不是实际UB/NVSHMEM内存模型或硬件实现。

`python3 calculations/calc.py completion-reclaim --inputs calculations/scenarios/completion-reclaim-example.json --format md` 复算有限outstanding credit、周期轮询与批量完成消费。每操作的提交、传输完成、消费回收时刻分列；credit保持到完成项被消费，容量与完成项元数据分开。四场景对照轮询加快、增加槽位和缩小消费批量；半开区间峰值排除同刻入口瞬态。

第7.3节远程窗口复算复用 `memory-concurrency`：`python3 calculations/calc.py memory-concurrency --transaction-bytes 256 --latency-ns 2000 --bandwidth-bytes-per-second 40000000000 --service-interval-ns 100 --format md`。新增 `--active-transactions` 区分已分配槽位与活跃独立请求；`--service-interval-ns` 是可持续串行启动间隔，不默认等于访存延迟。所有约束保留精确有理数及同时生效项；满足313个槽位仅满足窗口条件，不保证跑满链路。

`python3 calculations/calc.py rpc-trace --payload-bytes 1048576 --format md` 从封存的实验7-4原始JSONL复算：三种载荷各四模式20次正式样本，剔除预热但保留两端校验。输出阶段中位数、逐次客户端阶段守恒、p95／min／max、同轮配对差与应用请求字节；CPU和服务端阶段不重复加入客户端墙钟。复制7个原始文件并逐项核验原manifest，统一结果manifest覆盖副本。

`python3 calculations/calc.py remote-state --inputs calculations/scenarios/remote-state-example.json --format md` 比较不变Qwen KV快照重复远程读取与整体搬回。复用窗口和回本模块，输出网络／本地读写字节、启动／写入／读取时间、严格复用阈值与独立容量可行性。默认144MiB快照，256MiB可用预算；不代表追加token后的完整decode。

`python3 calculations/calc.py kv-pages --inputs calculations/scenarios/kv-pages-example.json --format md` 执行create／fork／append／cancel分页事件，记录每页引用计数和各请求块表。按官方Qwen GQA计页字节，共享未满尾页写前复制有效内容，安全点取消只回收零引用页。四场景覆盖对齐尾部、Qwen235几何和全部释放；预留、独占分页、共享分页在同一事件点比较。

`kv-pages` 的JSON输入可加 `capacity_bytes`：页池按完整页取整，create/append在修改前计算所需新页和COW页，超预算整项拒绝。共享fork当下不分配KV页，但不能据此保证后续增长可接纳；安全点取消可以通过降低引用数消除COW需求，即使没有释放物理页。容量余数、拒绝原因和每项所需页数均保留。

`python3 calculations/calc.py kv-trace --run small --format md` 从实验8-3的21个封存文件核对三个真实引擎运行。逐快照检查free+owned+reserved、块唯一与引用，按官方144KiB/token复算块容量；记录抢占保留输出、重复调度1805位置、取消释放104块及API返回与观察释放的时间差。`--run large|cancel` 选对应时间线，原始副本与结果均受哈希校验。

`python3 calculations/calc.py kv-restore --inputs calculations/scenarios/kv-restore-example.json --format md` 比较已知下次使用时刻下的保留、换出预取和丢弃重算。重算用官方backbone无lm_head工作账，服务时长独立输入；按完整KV重新预留的时刻计算释放byte*ns，传输双向字节与恢复等待分列。不自动以零延迟选择保留，未给出其它请求的容量价值时不声称策略最优。

`python3 calculations/calc.py prefix-value --inputs calculations/scenarios/prefix-value-example.json --format md` 对独立前缀候选做静态容量选择。官方完整前向减去命中历史后的suffix前向，乘显式有理数预期复用次数；按整页容量比较精确0/1选择和单位字节贪心。候选不可重叠共享，目标是矩阵工作量，不是实际延迟／最优在线淘汰。

`python3 calculations/calc.py apc-trace --run pressure6 --format md` 导入实验8-4五条件60次Agent请求，逐条核对冻结prompt哈希、单token输出、干扰输入与配置差异。报告请求命中率、token加权命中、每请求比例平均以及官方full/suffix矩阵差；累计复用KV字节不代表唯一驻留峰值。Agent时间、干扰时间与回放总时间分列，17个原始副本受哈希校验。

`python3 calculations/calc.py speculative-round --inputs calculations/scenarios/speculative-round-example.json --format md` 将连续接受长度直方图转为草稿接受率、含额外token的真实产出和总时间／总产出。官方目标验证采用pending token＋k草稿共k+1行，匹配串行decode逐步增长历史；显式输出上限截断交付但不撤销已执行验证，KV按最新输出仍pending的约定回滚。草稿检查点／采样算法不在本模块。

`python3 calculations/calc.py speculative-sampling --inputs calculations/scenarios/speculative-sampling-example.json --format md` 精确枚举单步接受与拒绝替换概率；JSON保留逐条提议→替换路径。输入为共同词表上的已归一化概率，以整数或分数／小数字符串表示，拒绝隐式浮点近似和自动归一化。教学反例中正确残差修正恢复目标分布，拒绝后直接从目标重采样的总变差为1/6；全接受和零提议概率的不可达分布记null。此计算不替代真实多token采样器或浮点实现验证。

`python3 calculations/calc.py speculative-budget --inputs calculations/scenarios/speculative-budget-example.json --format md` 在剩余输出数／是否准备两个状态上精确求解草稿预算。输入每个草稿长度的完整连续接受直方图与起草／验证／提交成本，普通decode始终可选；首次使用草稿才付准备成本，末轮截断不减已付工作。输出动态选择与固定策略的期望完成时间、轮数、草稿数和截断数，并保留各状态所有候选值。默认16输出例为10.202356ms，对照固定4草稿10.580953ms、普通decode16ms。该最优结果仅限平稳教学输入，不代表在线测得的吞吐或真实任务成功速度。

`python3 calculations/calc.py dflash-work --inputs calculations/scenarios/dflash-work-example.json --format md` 从固定官方DFlash配置与权重头核对58张量，按auto_map指定实现计量特征融合、5层草稿、非因果块注意力与共享目标输出头。下载原件和SHA在configs/dflash.lock.json，复算逐一校验；未下载完整权重。输出逐类M/K/N、矩阵工作、逻辑接口字节、草稿与目标KV；这些不是实测HBM或时间，非矩阵算术不包含在矩阵FLOPs中。

`python3 calculations/calc.py chunk-history --format md` 核对实验8-2同块不同历史的15个封存文件，逐位置并列CUDA event实测区间、有效因果配对及官方Qwen3-8B backbone矩阵工作。JSON保留176个样本及11个末首配对比，11次空execute单列。16块矩阵工作与整段8K守恒；不以注意力配对比例替代总工作、DRAM或时长，也不将同引擎共享GPU重复当作独立硬件复测。

`python3 calculations/calc.py batch-reuse --inputs calculations/scenarios/batch-reuse-example.json --format md` 使用官方Dense Qwen真实权重、矩阵工作和KV形状，扫描batch1/4/16/64；硬件严格匹配BF16输入／FP32累加／dense Tensor峰值。完整embedding计入驻留，读取仅按token查行，其余权重理想跨batch共享。旧KV等权重与计算等带宽两个交叉点分别求解；不满足容量时可运行时间／吞吐为null。工作区默认零表示未计，不能称实际引擎可用容量；没有预测TTFT、排队或实测HBM。

`python3 calculations/calc.py iteration-batching --inputs calculations/scenarios/iteration-batching-example.json --format md` 逐迭代比较固定整组／连续补位／decode优先分块。JSON保留每步每请求history、new、阶段、输出事件和官方矩阵工作；有限KV按声明输出上限严格FIFO预留，步末释放。时长来自显式base／新token／因果配对教学系数，未做硬件校准。默认同请求工作不变，连续补位减少总迭代但长prefill增大ITL，分块限制间隔而增加调用。

`python3 calculations/calc.py service-replay --inputs calculations/scenarios/service-replay-example.json --format md` 从四组实际请求交付记录复算TTFT、E2E、平均TPOT与联合计时达标吞吐。13文件固定SHA，72请求逐项核对相同输入／运行源码／输出token及配置单项差异。每轮窗口是实际首提交至末输出，goodput用总达标请求除以窗口总和；不跨时钟相减，不用平均TPOT替代逐token SLO，也不把计时通过当作任务质量通过。

`python3 calculations/calc.py gguf-inventory --inputs calculations/scenarios/gguf-inventory-example.json --format md` 从固定量化发布者仓库目录逐片求和Qwen235 GGUF，校验19变体72分片完整性和API／LFS文件大小，保留发布内容哈希。声明内存预算扣预留后加官方BF16 KV，完整文件占一份预算的假设与实际mmap驻留分开；文件名位宽不作为所有张量精度，尚未解析量化块／文件头，不声称已下载或核验完整GGUF载荷。

`python3 calculations/calc.py gguf-layout --variant Q4_K_M --format md` 解析固定Qwen235 Q2_K两分片与Q4_K_M三分片的真实GGUF头，按GGML官方块结构逐tensor计算混合精度载荷、码值与尺度元数据，再用offset和发布文件大小核对文件头／对齐守恒。1131张量形状与原模型参数完整匹配；JSON保留逐张量信息，原始头与规范SHA在configs/gguf-headers.lock.json。没有下载完整权重或执行解包，不能由头部验证质量与实际驻留。

`python3 calculations/calc.py kv-codec --inputs calculations/scenarios/kv-codec-example.json --format md` 用官方GQA和GGML32值块结构计算BF16/q8_0/q4_0历史与追加字节，按显式带宽／转换成本比较融合与整段物化路径。物化需额外BF16历史写回／重读和一份buffer；量化存储不表示采用相同位宽Attention计算。输出精确有理数时间和严格获益长度区间，不把教学转换成本或容量比当作实测加速。

`python3 calculations/calc.py weight-offload --inputs calculations/scenarios/weight-offload-example.json --format md` 按官方Dense Qwen FFN张量计选中层卸载容量、主存权重、GPU静态槽和净省KV容量，并在独立复制／逐层计算资源上调度有限槽预取。槽直到消费层结束才复用，含首次准备、重复pass环回与末层排空；更多槽不改变每forward字节。带宽／层计算时间是教学输入，batch或prefill摊销不等于单请求低延迟，也不证明实际引擎重叠。

`python3 calculations/calc.py kv-quality --run fp8_qbf16 --format md` 复算实验8-8三条件真实KV池、自然检索答案和固定64输出计时。25封存文件核对输入／文档／源码／校准／实际Q类型，原FP8路径与Q-BF16控制分列；只有八个不同任务，自然32次是重复执行。FP8在同预算下实际storage不变、token槽翻倍，不能称显存减半；自然与固定时间分开，不将错误请求时长当成功任务成本。

## PD 与 AF 交接

`python3 calculations/calc.py pd-af-handoff --format md` 复算第9章32层教学例，另有官方Qwen3-8B和235B场景。通过 `--inputs` JSON 可设 `model`、`length`、`batch`、`decode_steps`、`element_bytes`、`network_bandwidth`、`staging_bandwidth`、`startup_ns`、`path`（`direct` 或 `host-staged`）。带宽为bytes/s，启动为ns。

结果区分PD一次完整KV、AF指定decode步数的逐层往返、同总字节但多消息的对照。host staging按D2H、网络、H2D串行计量，每个接口的载荷只计一次；双端GPU和host槽分开。默认同格式传输，不假定跨代GPU互联、格式转换或流水能力，也不把通信子账当完整请求的部署性能比较。结果见 [场景索引](results/README.md)。

## Prefill／decode 资源池配比

`python3 calculations/calc.py pd-pool --format md` 将相同请求的P新token与D调用量换成每秒请求，枚举各类副本的整数P／D分配，并取P、D、共享KV网络能力的最小值。共置按每副本两个阶段的资源秒相加，不能把两种token/s直接比较。默认两类有效能力是教学输入，六场景包含同构对照、网络限制、前缀命中、长输出与单输出。

`--inputs` JSON字段为 `model`、`prompt_tokens`、`output_tokens`、`cached_prefix_tokens`、`network_bytes_per_second`、`arrival_requests_per_second` 与 `workers`；每个worker类型给 `name`、`count`、`prefill_tokens_per_second`、`decode_tokens_per_second`。速率接受整数或精确小数／分数字符串。每个副本须先在独立容量与后端检查中证明可运行；此处只给声明能力下的稳态上界，不预测TTFT、TPOT或稳定性。

## 专家权重复用与就地计算

`python3 calculations/calc.py expert-locality --format md` 使用官方Qwen3 MoE三个专家矩阵，分开本批不同权重数与token—专家任务数。`--inputs`可设模型、tokens、resident_experts、routing（balanced/concentrated）或counts直方图，以及CPU/GPU有效FLOPs/s、DRAM/HBM/link的bytes/s与startup_ns。五场景比较单层非驻留专家CPU本地、搬权重GPU、GPU常驻参考；BF16格式与全部有效能力为声明输入，不代替KTransformers的量化和机器实测。

每层32个BF16专家在Qwen235全94层合计105.75GiB，仅专家权重就超过24GB卡。逐层字节、全层常驻字节和单层服务子账分别报告；矩阵复用不保证模型实际可放置或请求更快。

`expert-locality` 还给单个非驻留专家的全部正整数复用区间。使用两侧计算／权重读取转折点和等时根精确分段，保留等号及无穷末段；默认教学能力下CPU较小区间为1–78token，79起搬权重GPU较小。78／79相邻场景和提高CPU能力的敏感性场景均可复现。该区间不是量化后端实测，也不能按不均匀路由的平均值直接选择执行路径。

## Grouped 专家分块与放置

`python3 calculations/calc.py grouped-experts --format md` 复用GEMM分块账，按官方Qwen MoE逐专家的真实M计算gate/up/down。`--inputs`支持model、tokens、participants、routing或counts、placement（contiguous/striped）及tile_m/k/n。JSON保留每个GEMM，Markdown列每rank和每专家的工作；五场景比较集中／均衡、放置、prefill与较小M tile。

完全执行补齐tile的FLOPs上界、有效FLOPs、下一层有效字节和最忙rank分别列出。空专家不启动，权重随M块重读；该工作缓冲接口不自动等于HBM，未计真实kernel跳过无效指令、融合和通信。

`grouped-experts` 的 `replicas` 可输入 `[{"expert":0,"rank":4}]`，在基础owner之外新增同权重物理副本。逻辑路由保持不变，任务按商余数均分；新增副本即使未命中也计权重容量。结果比较复制前后的最忙rank补齐工作，列每rank新增字节及未切分全模型BF16 KV容量等价。33任务拆成17＋16的场景展示最忙工作不降而总padding增加；该拆分不是实际EPLB策略，也未推算通信或迁移回本。

## 专家副本的冷复制回本

`python3 calculations/calc.py replica-payback --format md` 比较同一专家批重复执行时的基础／复制部署，复用grouped-experts逐rank矩阵与接口工作，增加首次串行复制和逐rank净容量检查。`--inputs`支持workload（grouped-experts参数）、batches、compute_flops_per_second、interface_bytes_per_second、copy_bytes_per_second、copy_startup_ns和extra_budget_bytes_per_rank。

默认7副本252MiB、教学25GB/s复制需10.60464608ms，26批未回本、27批严格获益。五场景还包括少1byte容量拒绝和无正节省；代数回本与可行回本分列。这是固定批路由和供给的分析，未包含实际EPLB协议及流量变化，不把指定tile接口自动称为HBM。

## 缓存亲和、排队与失效风险

`python3 calculations/calc.py cache-route --format md` 对齐第9章两份缓存路由笔记的教学输入，比较HBM命中、空闲副本重算、整份远端经host取回和CPU副本仍在的路径。官方KV bytes及完整／命中矩阵工作另算，输入时长不从FLOPs比例猜测。通过 `--inputs` 可修改队列ns、full/warm计算ns、带宽bytes/s、lookup_ns、hit_probability、slo_ns及retrieval_after_queue等参数。

默认取回与GPU等待重叠，用max(queue,ready)+compute；after_queue改为串行。两点命中概率给期望、p99、SLO通过概率和平均胜出阈值，等号精确保留。五场景包括5/20GB/s远端、过期缓存、依赖改变和p99边界；没有把单请求选择当真实持续路由能力。

## 实际原生路由回放

`python3 calculations/calc.py router-trace --policy cache_aware --format md` 导入实验9-9的正式36请求，支持round_robin、cache_aware、power_of_two。12份原件固定到sources/router-trace及SHA锁，逐请求核对模型响应cached_tokens、worker日志、已完成同worker前缀与输出身份，按官方Qwen配置另算矩阵节省；不使用路由器预计命中计数替代实际命中。

每策略同12个Agent输入、强制单输出token，两个worker共享一GPU。记录只支持该串行回放的缓存行为，未证明队列压力、远端取回、事件恢复或完整任务质量；原Agent任务失败历史保留，本次未重跑工具。

## 实际排队压力与整体收益

`python3 calculations/calc.py router-pressure --format md` 导入9-9补测8份封存原件，核对决策时worker0忙／worker1空闲、3136输入命中、后台128输出与目标单输出时钟，分别报告目标、后台、两任务完成。三轮配对差先算再取中位，采样等待峰值及实际采样间隔独立列出。

冷缓存空闲worker使目标更早完成，但这组共享GPU记录中后台变慢、两任务全部完成更晚。结果不把局部收益替代完整负载收益；客户端规则不是原生Router，事后后台剩余时间也不是在线预测。

## 实际KV文件与正常重启

`python3 calculations/calc.py cache-restart --format md` 导入9-8正式记录及65份实际KV文件，74原件集中在sources/cache-restart并SHA锁定。按官方Qwen GQA复算每页2.25MiB，65页库存146.25MiB、64次get文件载荷144MiB，但可复用1008token仅141.75MiB。消费者一次成功set不等于新增文件，文件字节不等于物理磁盘IO。

六次固定16token输出一致；首producer含JIT且页缓存未清，单次正常重启没有恢复p95、速度比或断电持久性结论。结果额外复算prompt矩阵节省，未将后续decode包含其中。

## 实际缺页、连续前缀与数值差异

`python3 calculations/calc.py cache-missing --format md` 导入9-8缺页0／32及显存对照17原件，复用cache-restart中的原始KV载荷。缺页32仅读取前32页72MiB，复用512token并重算其余512token；结果逐请求复算prefill矩阵工作。

按封存layer_first布局用标准库逐BF16元素比较，缺页32重算页995403元素不同、最大绝对差26.75，六次输出仍同参考。逐层K/V差异和有限值核验分开，不能把输出相同当KV逐位等价，也不能据此唯一归因于存储路径。首条件含JIT，不报告恢复加速；显存分段v2已接入：前置512输入仅1输出，后续实际device命中512。整段／显存分段1021226元素不同，存储恢复／显存分段992972元素不同；旧528边界尝试不当作匹配控制，其他故障后续接入。

## 坏页预取与未完成请求

`python3 calculations/calc.py cache-fault --format md` 导入wait_complete、timeout、best_effort三策略27原件，核对同原页截短2bytes的哈希、实际Short read与请求生命周期。wait_complete约60.083s观察期未返回，完成时间为null；两个成功条件零缓存重算完成同输出，完整prefill矩阵另算。

监督记录最终坏文件哈希未变，成功回退不当作修复存储。未取得运行坏页目录，不声称重新读取三个坏文件；每策略一次且条件有限，不计算p95或速度比，也不把等待阈值当作请求完成时限。


`python3 calculations/calc.py cache-residency --format md` 按官方Qwen GQA BF16页计算多级驻留容量与精确byte-seconds；`--inputs path.json`可指定model、page_tokens、capacities和intervals。每区间包含id、tier、prefix_identity、tokens、start_ns、end_ns，生命周期为半开区间且只接纳完整页。默认教学例的HBM峰值360MiB，共享后3888MiB·s（逻辑4608MiB·s），三层实体24048MiB·s，其中跨层副本7200MiB·s。另有HBM预算360MiB减1byte的超预算1秒场景，以及Qwen235场景。

prefix_identity必须声明相同不可变物理页序列及模型版本、adapter、格式和执行状态。同token文本不保证KV逐位相同；同层同身份按最长前缀取并集，跨层每份实体独立计容量。预算不含metadata和allocator，超预算报告需求与时长，不自动驱逐；没有迁移事件，不能将容量差分当写入IO或命中性能。真实多级事件、部分页／COW、混合递推状态尚未实现。


`python3 calculations/calc.py training-state --format md` 复算Qwen完整参数的BF16权重、显式2/4byte梯度、FP32主权重和Adam m/v，以及ZeRO0–3每rank和全组持久状态。`--inputs`支持model、participants、gradient_bytes、partition（flat/per_tensor）、extra_live_bytes和capacity_bytes。官方Qwen8实际8190735360参数，16bytes配置未分片131051765760bytes；DP8 stage3为16381470720bytes。六场景覆盖FP32梯度、10GiB额外同时驻留、Qwen235／DP64及DP7两种补齐方式。

ZeRO阶段依据固定commit的官方DeepSpeed zero3.rst，原件与SHA已保存；布局是显式教学选择，不假定后端bucket。MoE持久状态按全专家参数；净预算不是设备官方容量。所列分配能放下不证明训练可行，实际激活、all-gather／prefetch、casting和allocator须另从同一时间轴加入；默认额外量0不代表实测开销0。


`python3 calculations/calc.py gradient-cast --format md` 复算官方Qwen gate梯度：先D2H BF16再CPU cast，或先GPU cast再D2H FP32。`--inputs`可指定model、link_bytes_per_second、cpu_cast_bytes_per_second、gpu_cast_bytes_per_second、三项startup_ns、extra_gpu_budget_bytes与host_budget_bytes（准确字段见结果scenario）。Qwen8 gate为96/192MiB，转换读写288MiB；示例32GB/s时CPU路径较快，300GB/s时GPU路径较快，默认交点250000000000/7 bytes/s。

五场景含192MiB GPU额外预算减1byte、等时并列与Qwen235单专家。缓冲区间和操作均存精确有理数，主机CPU路径同时存活288MiB、GPU路径192MiB；共有GPU BF16源与额外FP32暂存分开。吞吐为教学输入，未推断实测HBM或整步加速；CPU消费者之后的输出寿命、Adam及权重回传另算，预分配池也不等于活跃载荷。


`python3 calculations/calc.py checkpoint-reshard --format md` 根据官方Qwen gate形状生成全局范围交集、源原始文件偏移和目标缓冲偏移。`--inputs`支持model、source_parts、target_parts、source_layout／target_layout（rows或flat）、include_optimizer。默认TP4→8，BF16权重96MiB、连FP32 master与Adam m/v共672MiB，目标每份84MiB。五场景包含仅权重、反向合并、7片展平→5片按行及Qwen235单专家。

行主序、每状态每rank一个无header原始文件为明确布局输入，不声称真实checkpoint文件存在。flat可跨行，rows保持整行，商余数切分无padding；字节重建测试证明小型载荷完整且不重复。未覆盖框架融合／转置／压缩、梯度与CPU状态或存储IO／完整恢复时间，读取范围数不是物理IOPS。


`python3 calculations/calc.py checkpoint-async --format md` 根据官方Qwen完整参数14byte保存格式计算有限槽、串行staging／upload与独立durability确认。`--inputs`可设payload_bytes（显式教学覆盖）、snapshots、first_capture_ns、interval_ns、staging_ns、upload_bytes_per_second、buffer_slots、durability_delay_ns、failure_ns。默认官方Qwen8载荷114670295040bytes；五场景含112GB原例、快链路、单槽背压和延迟确认。

请求为固定墙钟FIFO屏障，槽不足时延后实际capture并取训练暂停区间并集；槽在upload读取完成后可复用，独立确认不再占槽。故障只读取此前已durable的快照，同刻先确认再故障；没有可用快照时为null。故障后的表行为反事实计划，墙钟回退不是损失训练token或ETTR；实际writer持久化语义、CPU状态、后台争用和加载恢复另计。


`python3 calculations/calc.py checkpoint-interval --format md` 以官方Qwen全参数14byte载荷除以有效保存带宽得到阻塞c，展开c/tau+lambda*tau/2+lambda*r以及sqrt(2c/lambda)。`--inputs`支持model、devices、device_mtbf_seconds、common_job_mtbf_seconds、save_bandwidth_bytes_per_second、recovery_ns、intervals_seconds、failure_free。默认独立1024设备各MTBF365天、8GB/s保存、120s恢复，一阶最优939.612519s；Poisson重试模型最优930.081056s。

Poisson模型允许计算和保存失败、固定恢复期间不失败，E=(exp(lambda*(tau+c))-1)*(1/lambda+r)，保留比例tau/E。该公式按renewal方程求得，数值最优用expm1与二分；不是一阶损失的简单补数。五场景含作业共同冲击、高故障、零故障和长恢复，一阶损失超过1不裁剪；零故障无有限最优。真实故障分布、异步保存和恢复失败不在模型内。


`python3 calculations/calc.py checkpoint-baseline --format md` 导入CPU DCP无保存／同步／异步五轮15运行，核验39原件、十份实际检查点文件SHA、源码和同20步loss／最终状态哈希。全窗口中位数76.042／207.377／84.569ms；每轮配对的async−none窗口中位差5.172589ms、训练差2.959636ms，不能替换为两组中位数之差。结果保留API、stage、writer、commit、重叠和各运行。

未测项用null；future_observed_complete不是后台真正就绪时刻。恢复一致来源为封存的真实加载记录，本CLI不调用torch重新加载。小模型CPU结果不当Qwen或GPU性能；RSS高水位非独立staging峰值，文件字节/写入区间非物理磁盘带宽，五次样本不推出p95或独立优化收益。


`python3 calculations/calc.py checkpoint-fault --format md` 核对10-7正常／提交前SIGKILL共20原件。第二份数据已写12622659bytes但metadata缺失，封存实际加载报CheckpointException，旧点恢复cursor3；故障前cursor43，需重做40更新。API、stage、writer、commit分别列，未完成commit为null，kill减调用开始仅为未完成观察。

已校验实际文件SHA与执行源码，加载成功／拒绝来自封存torch运行，本CLI不重新反序列化。人工提交屏障不代表慢磁盘；单进程终止不证明断电／多rank持久性，没有重做40步或完整恢复耗时，不推出ETTR与故障率。


`python3 calculations/calc.py checkpoint-resume --format md` 核验真实CPU DCP的2行保存→2行／3列／1完整恢复：封存15原件、19状态，矩形chunk边界／无交叠／总体积证明覆盖。唯一逻辑463688bytes、实际文件518512bytes（metadata6393），全组局部量另计RNG与标量复制。六恢复rank的下一步loss和全部状态同未中断基线，Adam动量清空负对照均检出。

CLI核验实际文件和封存metadata提取／恢复训练记录，不重新运行torch。恢复后聚合完整张量，走同一单进程数学路径；不证明分布式归约逐位一致。最大rank API不含torchrun、DTensor构造、加载后聚合与下一步训练，每路径一次不比较布局性能；非Qwen或大模型存储吞吐。


`python3 calculations/calc.py training-deadline --format md` 复用官方Qwen训练矩阵账，按完整序列和尾序列分别计算任务工作，匹配单设备BF16输入/FP32累加/tensor/dense峰值。`--inputs`支持model、task_tokens、sequence_tokens、deadline_days、unavailable_seconds、gradient_bytes、efficiencies（精确字符串）与devices。默认100B/30天、8192序列，40%矩阵效率下4090/5090/A100-SXM/H100-SXM/B200算力下界31/25/17/6/3张；完整持久容量下界独立列。

五场景含长序列、235B MoE、日历扣除和小任务FP32梯度。A800缺严格精度峰值、H20 SXM5 96／141GB仅有已锁定官方名义容量、缺所需精度峰值时明确算力不可用，不代入稀疏或其它精度；整机峰值也不当单卡。此效率仅对矩阵子账定义，不直接套公开MFU；算力与容量下界max不证明实际布局、激活、通信和最忙rank可行，同一开销不能同时包含在效率与日历停顿中。


`python3 calculations/calc.py dense-training-scale --format md` 复算名义Dense 1T/5T/10T的6ND，官方A100/H100/B200 BF16输入、FP32累加、dense单设备峰值，30/40/50%教学效率。默认16384卡、20T token；50%时1T分别543.404169/171.358501/75.352045天。`--inputs`可设parameters列表、cards、task_tokens、data_rule、tokens_per_parameter、efficiencies、deadlines_days、unavailable_days、state_bytes_per_parameter和devices。

四场景含fixed数据、proportional的D=20N、半设备及日历停顿，固定D线性而D随N同比增长为平方工作量。90/180天整数卡数向上取整，参数上界向下取整；proportional用整数平方根验证边界。16byte持久容量仅为理想分片必要条件，未证明激活/拓扑/供数/质量可行；名义模型不代替官方Qwen逐矩阵或真实MoE训练账。


`python3 calculations/calc.py routing-metadata --format md` 复用官方专家几何计算[tokens,MoE层,top-k]逻辑ID；默认Qwen3-30B、8192token、uint16为6MiB，int32为12MiB。七场景覆盖Qwen235、V4 Flash/Pro、Kimi K3和三份存储副本。`--inputs`支持model、tokens、encoding、token_rate_per_second、retained_copies、bandwidth_bytes_per_second与header_bytes。

uint8最多表示256专家，384/896专家会拒绝；shared专家不记录选择ID，K3首dense层排除、V4 hash层包含、MTP不计。声明每token三项uint64身份24bytes，另有ceil(tokens/8)有效位图和输入header预算；不是实际框架格式。物理副本只乘存储，吞吐含每批header；模型revision和层序仍须绑定schema，未实现多轮packing/缺失校验，不将KV命中当路由日志命中，也不证明后端支持这些模型的R3。

教师最终hidden与全logits缓存：`python3 calculations/calc.py teacher-cache --format md`，可用`--inputs`提供model、tokens、dtype、replays、chunk_tokens、有效bandwidth_bytes_per_second和head_flops_per_second。输出容量、写入/重放读取、输出投影FLOPs及声明串行预算；固定教师版本，不计损失、softmax或主干前向。

权重交接：`python3 calculations/calc.py weight-handoff --format md`，`--inputs`可指定model、expert_parallel、replicas、生产端/接收端有效带宽和阶段分配。官方Qwen完整BF16参数按专家归属分片，其余复制；默认235B EP16，Qwen8使用EP1。报告单播出口下界和声明容量，非真实引擎切换或完整部署保证。

假想服务成本与完成率：`python3 calculations/calc.py routing-cost --format md`；`--inputs`提供tasks、prefix_tokens、fresh_tokens、b_hit_fraction精确分数字符串和deadline_seconds。复现费用交点1291/1520与6秒联合质量/时限目标的45/49，分开全部尝试费用与预期成功分母；并非供应商报价或自动重试模型。

V4非routed FP8 Linear：`python3 calculations/calc.py v4-fp8-linear --format md`，`--inputs`支持Flash/Pro、batch/tokens/history。按固定官方32×128×128 kernel分别计有效矩阵、tile、E8M0量化、共享scale及接口bytes；这些矩阵已包含在v4-forward中，不重复相加。

Qwen3-VL多模态缓存：`python3 calculations/calc.py multimodal-cache --format md`，按官方config及固定vLLM DeepStack拼接计算完整EC和语言KV。`--inputs`支持预处理后尺寸、图数/text_tokens、EC/KV dtype与明确E/PD/网络能力，穷举整数池分配；不实现原图resize或实际SLO预测。

生成式多模态追加范围：已封存Qwen3-Omni、Fish Audio S2 Pro、MiniMax-H3、Wan2.2-TI2V-5B、Qwen-Image-2512与FLUX.2-klein-4B的官方小配置/模型卡及许可原件。见[书中短例](../case-studies/generative-multimodal-models.md)与C77–C80清单。配置下载不等于完整算子/执行支持；图像视频模型的多组件config保留目录，不伪装为文本config。

DeepSeek V3基础逻辑前向：`python3 calculations/calc.py v3-forward --format md`，`--inputs`提供batch/tokens/history、output_head、attention_work和routing。官方HF expanded MLA与compact路径分开，逐权重/算子而非6ND，FP8实际格式和完整HBM仍缺。

真实环境资源：`python3 calculations/calc.py environment-resources --format md`，`--inputs`用dataset=processes/controller及condition筛选。封存CPU/RSS与生命周期事件，有限窗Little恒等式和RSS梯形积分不是生产稳态/物理内存；失败任务用量完整保留。

生成请求的阶段矩阵入口：`python3 calculations/calc.py omni-audio --format md`、`image-generation --format md`、`video-generation --format md`（后两项也由同一calc.py运行）。`--inputs`载入场景JSON，输出矩阵形状、重复次数、码本/去噪循环和阶段总量。现有范围为音频Transformer/桥接/波形解码、图像文本编码/DiT/VAE与参考非矩阵账、视频matrix-core及H3条件化；视频前后编码器等仍需补齐，不是完整生成FLOPs或硬件延迟。

视觉编码前置阶段：`python3 calculations/calc.py vision-encoding --format md`，六场景按Qwen3-VL-4B官方config/源码核patch、24视觉block、merger/DeepStack矩阵及非矩阵参考运算，读写/参数/EC分列；`--inputs`设置预处理后尺寸、图数、整数encoder_cache_hits与dtype。语言prefill另计，不把EC容量当encoding工作。

有限重试与回退：`python3 calculations/calc.py retry-paths --format md`，`--inputs`提供节点DAG、条件概率、每节点费用/秒/CPU核秒/驻留bytes。展开全部终点，保留失败与过时成功费用；成本/成功率使用精确分数，零分母null。默认是假想教学输入，没有无限重试、并行推测或真实扩容预测。

VL阶段连接：`python3 calculations/calc.py vl-request --format md`，按官方QwenVL4视觉→语言prefill→G−1 decode，缓存命中不减少语言位置，DeepStack注入与clone单列，精确增长历史求和。

生成前后阶段已扩展：image-generation现在给出文本encoder（含官方全词表head/模板前缀）与VAE逐卷积dense/nonpadding账及必要存活张量；omni-audio增加94个Omni codec算子、逐帧依赖DAG及可选有效速率下界。Fish codec现已补168个算子与可选纯文本提示；原始媒体预处理和完整运行时仍缺，full请求时延不伪造。

VL阶段图：安装可选plot依赖后运行 `python3 calculations/calc.py plot-vl-stages`，从已校验结果生成[SVG](figures/vl-stages/figure.svg)、[PDF](figures/vl-stages/figure.pdf)和原始数据；缓存对照保持语言请求相同，矩阵工作量不冒充时延。

混合尺寸截图：`python3 calculations/calc.py vl-request --inputs calculations/scenarios/vl-mixed-example.json --format md`。`images`逐项指定预处理后height/width与布尔cache_hit；逐图计算attention后合并语言位置，共享视觉权重只计一份容量。不可同时提供非默认统一尺寸/图数选项。

Omni输入音频理解：`python3 calculations/calc.py omni-audio-encoder --format md`；`--inputs`提供有效mel_lengths、element_bytes与attention_path。覆盖卷积分块/padding、分段attention、Thinker投影；区别于omni-audio的输出语音路径，原始波形预处理不含在内。

视频前后阶段：Wan TI2V5B的无输入图像路径已补两次UMT5文本编码及一次VAE逐卷积/空间attention解码，分别列在video-generation结果中；VAE首块与steady缓存块分开，非矩阵primitive已另列，完整工作区与实测仍待。图像生成另列初始化/请求setup、typed转换和随机样本数量，支持qwen_shape_cache_warm参数，不把初始化重复乘NFE。

历史网络核数：`python3 calculations/calc.py nic-budget --format md`。按包数分布、线时开销、声明处理工作与利用率算忙核/整数核；可选PCIe需求和窗口约束独立保留。论文简单转发基线不代表完整网络虚拟化。

Omni图像/视频理解编码：`python3 calculations/calc.py omni-vision-encoding --format md`。输入grid_thw为预处理后的patch网格列表，cache_hits逐项布尔，seconds_per_grid可选时间间隔；输出四份特征、逐时块attention与独立Thinker注入接口。默认640²图并非套用VL4参数。

Wan VAE非矩阵：video-generation的wan_vae_decode.nonmatrix_work现含固定源码primitive计数、来源和形状验证边界；RMS/SiLU/softmax/copy等与矩阵分列，逻辑bytes有接口重叠，不合并成HBM预测。图像setup另有扩展事件图和相对原边界图的峰值增量，不把独立阶段峰值直接相加。

TPU历史需求：`python3 calculations/calc.py tpu-demand --format md`，以论文3分钟/日的翻倍预测作归一化锚点，显式缩放使用量/人口/工作和峰值条件；实际人数、服务器数量和成本未知，不拿10倍性价比目标代替吞吐。

序列依赖与缓存数值核验：`python3 calculations/calc.py sequence-dependencies --format md`。固定四token三层教学权重，导出逐矩阵、状态、依赖图和同模型缓存/重算检查；不模拟词表采样，不称真实checkpoint。

Omni理解请求：`python3 calculations/calc.py omni-understanding --format md`，统一连接各模态encoder、placeholder替换、48层Thinker与G−1 decode。缓存命中保留语言位置与DeepStack，音频缓存身份包括组批/分段。既有omni-audio仍是语音生成入口；理解请求此处只生成文字。

硬件字段缺口可用 `python3 calculations/calc.py hardware --audit --format md` 查看；逐条峰值的拒绝原因使用 `--format json`。输出不把缺失数值当作厂商未披露证明。见 [硬件登记审查](results/hardware-audit.md)。

环境创建/克隆/快照/预热复算：`python3 calculations/calc.py environment-lifecycle --format md`，或用 `--inputs` 提供教学参数。见 [默认结果](results/environment-lifecycle-default.md)；本地进程记录和云端未测项分开。

UB协作范围的现代八卡教学对照：`python3 calculations/calc.py ub-scope --format md`。见 [默认逐卡与通信结果](results/ub-scope-qwen32-default.md)，容量合格与通信偏好分开，历史UB条件仍缺。

公开训练投入复算：`python3 calculations/calc.py training-history --format md`，默认不推断价格或全程MFU；[历史字段表](results/training-history-published.md)区分总/激活参数、6ND代理、训练阶段与条件日历。

Scaling-law受控教学拟合：`python3 calculations/calc.py scaling-law --format md`；`--inputs calculations/scenarios/scaling-law-perturbed.json`查看扰动输入。见[默认结果](results/scaling-law-teaching.md)，不声称论文实验点复现或实际任务质量最优。

TP/EP重配置复算：`python3 calculations/calc.py reconfiguration --format md`；`--inputs calculations/scenarios/reconfiguration-example.json`导入完整静止快照。默认[TP4→TP8结果](results/reconfiguration-dense-tp4-to-tp8.md)逐项列权重/KV/辅助状态迁移、同卡物化读写、双缓冲容量及条件摊销；带宽计算值为资源下界，切换时间需另给完整运行输入。


## Qwen3.5 基础文本参考执行

`python3 calculations/calc.py qwen35-forward --format md` 复现 [8192-token prefill](results/qwen35-prefill-8192.md)。默认全部位置输出头、BF16、eager 完整 attention 与 chunk64 DeltaNet；用 `--inputs` 传入包含 `batch`、`tokens`、`history`、`output_head`、`record_past` 的 JSON 修改场景，未给字段沿用默认值。八个固定场景位于 `scenarios/book.json` 的 `qwen35_forward` 组，每项的 `inputs` 即此命令的输入对象。

[主模块](src/infra_calc/topics/qwen35_forward.py)列权重形状、逐矩阵、一般算术、特殊函数和状态；[语句补充](src/infra_calc/topics/qwen35_reference_steps.py)列 padding、卷积裁切、RoPE/mask、router 索引及转换接口。CSV保留各行真实 repeats，避免将45层DeltaNet算子扩到60层。JSON保留完整张量及步骤；两份接口计数有重叠，不能相加为HBM流量。

[单步decode](results/qwen35-decode-b1.md)、[65-token尾块](results/qwen35-chunk-tail-65.md)和[初始record-past](results/qwen35-cold-single-record-past.md)展示路径差异。已有record-past历史长度未知时，只给已知工作，不将部分和用于完整性能比较。视觉/MTP、后端primitive内部算法和实际分配器峰值不在本基础文本参考路径的验收范围。


## VL 静态图片位置与语言阶段

`vl-request --inputs` 现在可接收 `position_segments`，以按序的 text/image 段生成真实三轴位置；图像尺寸和文字总数必须与请求一致。见[四图完整示例](results/vl-position-four-640-images.md)与[混合矩形图像](results/vl-position-mixed-images-two-turn-boundaries.md)。场景输入在 `scenarios/book.json` 的 `vl_request` 组中，移除每行的 `id` 后即可传给命令。

[位置模块](src/infra_calc/topics/vl_position_bridge.py)分别报告 prefill 索引、mRoPE delta、decode arange／delta 复制／三轴加法；已有语言频率表、视觉矩阵和KV计数保持各自归属。四图示例2000个语言位置对应下一个旋转位置480，生成128个输出后KV仍有2127个位置。此接口固定静态图像、无padding和直接model路径；tokenizer、视频及generation wrapper额外准备另计。


## 真实70B单设备容量扫描

`python3 calculations/calc.py capacity-scan --model deepseek-r1-distill-llama-70b --format md` 使用实际Llama70参数和GQA配置。见[8K](results/llama70-capacity-8k.md)、[32K](results/llama70-capacity-32k.md)、[尾分组](results/llama70-capacity-tail-group.md)及[逐字节边界](results/llama70-capacity-boundary.md)。默认group128、2-byte scale的8/4-bit教学存储分别为73,725,919,232及39,500,398,592bytes；嵌入、输出头和norm保留BF16。

容量预算使用bytes，默认24/48/80为decimal GB，工作区默认2 GiB。8K BF16 KV每请求2.5 GiB；低位权重不会同时压缩KV。结果区分权重/工作区不fit和能放权重但装不下一份KV。这是完整模型单设备驻留，不能聚合八张卡预算，也不代表真实量化格式的质量或kernel支持。


## 真实70B逐卡放置

`python3 calculations/calc.py dense-placement --model deepseek-r1-distill-llama-70b --tp 8 --format md` 输出[逐rank权重、KV、矩阵与预算](results/llama70-placement-tp8.md)。BF16基础路径分别切Q头、FFN和词表，norm完整复制；PP仅在首/末stage放嵌入与输出头。比较[八卡两副本](results/llama70-placement-tp4-dp2.md)与[纯流水八卡](results/llama70-placement-pp8.md)，不能以聚合显存判断每张卡可行。

[TP16](results/llama70-placement-tp16-kv-replica.md)按真实GQA映射复制KV头及K/V投影；矩阵工作也随复制增加。接口消息、固定工作区和有效因果矩阵各自标明，未推断真实通信延迟、低位kernel布局或allocator峰值。


## 封存请求分布与p95

`python3 calculations/calc.py workload-profiles --format md` 从02-08已封存的派生逐请求分析复算9组44条记录，输出输入/返回输出/缓存token、模型/工具秒数与复用间隔的min/median/mean/p95/max。见[结果表](results/workload-profiles-02-08.md)。数据副本及原分析/索引由[来源锁](configs/workload-profiles.lock.json)固定，不启动新请求。

经验p95取排序第ceil(0.95n)项，n≤19时等于最大值；无工具观测和首请求间隔不填零。它描述有限样本，不证明总体尾延迟；缓存长度、EOS和工具间隔的原记录语义继续保留。


## FLUX VAE逐算子与生命周期

`python3 calculations/calc.py flux-vae-decode --format md` 输出[默认1024²解码](results/flux-vae-1024-bf16-sdpa.md)，包含卷积/attention、bias、GroupNorm affine、SiLU、nearest复制与命名张量生命周期；JSON完整保存权重/事件，CSV保存算子接口。使用 `--inputs` 指定height、width、batch、dtype、attention和workspace_bytes，场景可从 `book.json` 的 `flux_vae_decode` 组取inputs。

[SDPA](results/flux-vae-1024-bf16-sdpa.md)与[eager](results/flux-vae-1024-bf16-eager.md)都计10,474,653,483,008 dense FLOPs，padding有效乘法另列。49,620,259参数仅覆盖解码器与post-quant卷积；命名张量边界峰值不是实际allocator峰值，大输入布局复制未知时条件预算为null。此计算细化已有VAE阶段，不能重复加到image-generation总矩阵工作中。

## 等参数目标与架构变化

`python3 calculations/calc.py architecture-variants --format md` 比较官方Qwen3-8B基线与五个未训练声明变体，见[decode](results/architecture-decode.md)、[prefill](results/architecture-prefill.md)及[前缀续算](results/architecture-prefix.md)。默认KV8→2、FFN12288→12800严格等参且矩阵FLOPs相等，KV容量降至四分之一；不同FFN对齐下必须看actual parameter delta和exact_equal_parameters。

每个变体列算子、状态、TP完整头和norm复制、容量翻转区间及两类decoder collective差额。参数近似误差明确保留；只有基线有实际checkpoint，不推断同质量或完整请求加速。联合变体比较当前要求TP能整分全部变体的KV头，不暗示其他分布式方式不可用。


## V4已知后缀的顺序缓存续算

`python3 calculations/calc.py v4-prefix-continuation --format md` 复算[6144前缀加2048后缀](results/v4-prefix-flash-6144-2048.md)。完整前缀状态须已恢复，包括window环形布局、压缩/index历史、FP32 compressor槽与重叠carry；后缀逐token执行全部基础层及词表头，中间logits丢弃也计费。不是并行chunk prefill。

输出保存每步算术、压缩边界、已知接口与状态；有效矩阵和已知tile矩阵为替代口径，不相加。`--inputs`可指定model/prefix_tokens/new_tokens/batch及源cache分配；JSON scenario可直接重放Flash和Pro。默认显式分配max_seq_len8192/max_batch_size1，原源码4096默认值不足。预分配、有效状态、增长和写入分别计量，前缀恢复成本及完整HBM/peak/latency仍未知。

### Qwen3-235B八卡MoE容量

`python3 calculations/calc.py qwen235-placement --format md` 给出[默认TP2×EP4、80GB、8K](results/qwen235-placement-tp2-ep4-pp1-80gb-8192.md)的逐rank矩阵所有权、三格式权重、KV和最差rank并发；`--inputs` JSON可改tp/ep/pp、length、capacity_bytes、workspace_bytes、group_size和scale_bytes。24场景覆盖四种八卡组织及24/48/80GB、8K/32K。

全部专家驻留；EP内复制attention/KV，TP按完整KV头划分或复制。低位逐行打包与scale按分片后的local K计算，embedding/head/router/norm保留BF16。官方索引提供36945个名称与总bytes，形状从固定配置和实现推导。声明量化格式与2 GiB工作区属于容量假设，不等于实际checkpoint格式或运行时峰值。

### Dense三模型分片后的低位容量

`python3 calculations/calc.py dense-quantized-placement --format md` 默认计算Qwen3-8B的TP8、24GB、8K；`--inputs`接受model/tp/pp/dp/length/capacity_bytes/workspace_bytes/group_size/scale_bytes。支持Qwen3-8B、Qwen3-32B和DeepSeek-R1-Distill-Llama-70B，54场景各含BF16、声明8bit与4bit三格式。可看[70B逐卡报告](results/dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-8192.md)。

复用BF16放置的本地矩阵及完整KV头所有权；分片后才按local K分组，保留每行尾组和打包取整。词表与norm保持BF16，KV精度不随权重变化。length含最终新增位置；重放旧history8192+token1须用length8193。每DP副本由最差rank决定共同请求数，再跨副本求和。默认每卡2 GiB工作区是显式条件，实际运行峰值保持未知。

### 四模型统一请求累计

`python3 calculations/calc.py request-model-comparison --format md` 生成[四模型并排结果](results/request-four-models-book.md)。`--inputs`接受prefix_tokens/new_tokens/output_tokens/batch/k3_mla_path/routing；原名单为Qwen3-8B、V4-Flash、V4-Pro、Kimi K3。首输出来自输入阶段，后续仅G−1次单token forward；最终保留S+P+G−1位置。4场景覆盖默认短例、G1、压缩边界与6144+2048缓存续算。

JSON保留输入源子账、每步decode、状态与源分配；Markdown按模型/阶段并排列账。V4已有前缀时逐token输入且全部head计费；K3的A_log来源冲突、实际流量/峰值/质量未知明确传播。相同输入长度是受控计算条件，不能代替同文本、同质量性能比较。

### Fish代码帧收集与波形导出

`python3 calculations/calc.py fish-wave-export --format md` 复现[21+22帧示例](results/fish-wave-two-chunks.md)；`--inputs`可指定chunk_frames、waveform_dtype和code_element_bytes。仅输入固定源码切片后实际成功返回的帧数，不能用文本chunk长度或生成预算代替。

每块代码clone和conversation CPU复制、next后合并/第二次CPU复制、单次codec、wave CPU复制和FP32转换逐阶段列账。专用Markdown与JSON均保留全部wrapper与codec明细；codec沿用原计算，禁止重复相加。此CLI等所有代码块完成后才产生波形；样本数与音频时长可精确计算，TTFA/RTF、文件字节和完整运行峰值无实测保持未知。

### 实验3-3严格协议与全部候选消耗

`python3 calculations/calc.py strategy-record-cost --format md` 重放[三批实验的严格消耗账](results/strategy-record-cost-03-03.md)。原132候选/72组全部保留，按运行前JSON和投票规则重新选择，并独立DP核真值。零成功的每成功任务消耗保持null；逐请求耗时之和、组墙钟、验证与选择分别列出，重叠时间不作GPU时间。封存输入在sources/strategy-record-cost，18文件经configs/strategy-record-cost.lock.json核验。没有新模型请求或后验放宽评分。

### Qwen8训练非矩阵反向与AdamW

`python3 calculations/calc.py training-nonmatrix --format md` 输出[默认B1/T128训练账](results/training-nonmatrix-book.md)，`--inputs`可改batch/tokens/supervised_tokens/head_strategy/activation_policy和AdamW超参。5场景覆盖dense/compact标签、局部SwiGLU重算及8192长度。原training_matrix完整复用；标量、特殊操作、typed转换、保存与释放事件单列，不将非线性保存子集合称为完整激活峰值。

计算CLI本身只需标准库。数值测试额外使用PyTorch FP64自动微分和有限差分；本机已用`/Users/boj/miniconda3/bin/python -m unittest discover -s calculations/tests -p test_training_nonmatrix.py -v`验证14项且无跳过。没有PyTorch的解释器会跳过数值对照，不能据此声称数值验证已执行。V4训练、完整通信/HBM/运行峰值仍在原范围内待补。

### 真实C4验证损失拟合

`python3 calculations/calc.py real-scaling-fit --format md` 复现[8个官方来源点](results/datablations-real-c4-eight-point-fit.md)。公共入口逐次校验必要原件/数据锁，以AST literal安全解析notebook，核日志中的loss、tokenizer、验证总体和预算；6点fit、2点预定模型大小holdout，保留reported N/D与4项敏感性。

原严格正系数fitter不变，新增scaling_boundary_fit用于非负边界诊断。QR缩放、幂项对数回退、有限SSE及缩放RMS避免可表示结果因中间溢出失败；坏网格点分类保留。实际8点主拟合不受这些修复影响，边界solver的舍入差用明确容差比较。不同验证样本数不自动排除同总体统计拟合，也不代表误差独立；参数/预算坐标是报告估计，不能称精确checkpoint与实际token计数。

### 真实拟合的生命周期与图

`python3 calculations/calc.py real-scaling-lifecycle --format md` 输出[主场景](results/real-c4-lifecycle-512-128.md)，`--inputs`可改目标loss、候选规模、调用量、输入/返回token及抽象费率。主law与四敏感性分别重算，不按费用替换主拟合；每条候选列N/D外推倍数和成本线交叉。此为6ND/2Ntoken代理，不是同任务质量或实测硬件费用。

安装可选plot依赖后，`python3 calculations/calc.py plot-real-scaling` 生成[SVG](figures/real-scaling/figure.svg)、PNG、PDF并写来源/产物SHA manifest。图从公共结果生成，verify-results一并检查；修改相关结果后须重画再sync-outline。默认512输入/128返回，额外decode127；虚线表示候选N/D超拟合框。


V4训练可微子图提供 `v4-training-primitives` 与 `v4-hc-training` CLI，均支持 `--inputs` JSON（batch、tokens）和 `--format json|md`。router/专家门控/mHC split与mHC外包装分别列账；后者已含split，不能整项相加。数值验证针对去舍入数学图，完整量化训练与运行峰值仍需补齐。


`python3 calculations/calc.py v4-attention-training --format md` 输出共享KV稀疏attention的逐收缩前反向、sink梯度、重复索引scatter及保存状态。`--inputs`支持batch/tokens/kv_tokens/heads/head_dim/indices；手工小尺寸属于数学夹具。官方PV前BF16未归一化指数转换的训练梯度未知，当前验证去舍入数学core。


`python3 calculations/calc.py v4-attention-projections --format md` 输出单个ratio0注意力外围的五投影、RMSNorm和RoPE前反向计算，支持 `--inputs` JSON的batch/tokens。core及它的Q/KV/概率保存排除，频率setup不重复计；压缩/indexer支路与量化cast梯度仍待补齐。


`python3 calculations/calc.py v4-compressor-training --format md` 提供ratio128完整块主压缩器两投影/APE/逐feature池化/RMS/RoPE前反向。`--inputs`指定batch/tokens，tokens须为128正整数倍。ratio4、在线/尾块状态及量化cast梯度仍单独待补，结果不代表完整训练峰值。


`python3 calculations/calc.py v4-compressor-overlap --format md` 计算ratio4 fresh prefill重叠、padding及返回尾状态联合VJP，支持batch/tokens。仅尾token仍计状态梯度；源码重复APE差额单列，任意恢复初态/online过程与量化梯度待补。


`python3 calculations/calc.py training-pipeline-schedule --format md` 输出固定Qwen8 PP4的GPipe/1F1B事件、前反向依赖、通信与activation寿命；`--inputs`提供microbatches/policy/逐段服务时间等。14场景覆盖M1/4/8/16、慢stage、共享链路及SiLU重算。服务时间是条件输入，默认保存预算仍缺GEMM/持久状态/完整workspace，不宣称运行峰值。


`python3 calculations/calc.py vision-preprocess --format md` 复现已解码RGB的固定CPU预处理；`--inputs`指定height/width/encoder_dtype/normalization_cache。官方原件在sources/vision-preprocess，锁在configs/vision-preprocess.lock.json。FP64系数、INT16权重、INT32卷积、FP32归一化和patch/BF16入口物化分列，语义访问不是DRAM实测。输出尺寸接vision_encoding，不重复编码矩阵。


`stage-resource-bounds --format md` 比较真实Qwen8/V4逐层资源需求与匹配的硬件供给，未知速率/容量不当作通过；25场景区分官方与显式假设。`v4-compressor-online --format md` 给ratio4/128逐token状态时间图与初态/末态联合VJP，四场景，不推定量化梯度。两CLI均由 `python3 calculations/calc.py` 调用并支持 `--inputs`。四模型报告的special_ops键按稳定顺序输出，数学不变。


`python3 calculations/calc.py training-pipeline-gemm-state --format md` 将325矩阵实例映射到保存输入身份，253新增张量与nonmatrix/P/GQA去重，比较save_inputs与recompute_products，支持 `--inputs`。额外工作和workspace同原流水合账，仍是FP32参考stage预留而非完整allocator峰值。


`python3 calculations/calc.py v4-moe-training --format md` 复现固定选择V4单层router/shared/routed完整数学VJP；支持 `--inputs` 的batch/tokens/layer_id/routing/counts。四场景核负载及hash层；已含router/门控，不与旧primitive总账重复相加，QAT数值等价和完整训练仍未推定。

`python3 calculations/calc.py v4-optimizer --format md` 从真实V4参数形状计算Muon十步逐矩阵迭代、AdamW及状态；四场景明确方向/MTP/分组策略，默认未知组保留。报告副本位于 `sources/v4-optimizer/`，SHA锁定于 `configs/v4-optimizer-report.lock.json`。

`python3 calculations/calc.py omni-audio-preprocess --format md` 复现已解码PCM到mel及audio encoder入口的逐阶段工作；四场景含混合长度、hop尾部、实际30秒构造器上限。固定来源在 `sources/omni-audio-preprocess/`，FFT参考与实际后端未知项分开，不重复计算encoder。

`python3 calculations/calc.py training-input-supply --format md` 提供真实Qwen8 checkpoint载荷与显式数据准备/传输/消费的竞争事件模型，五场景；`python3 calculations/calc.py qwen235-execution --format md` 提供同批EP/TP/PP专家矩阵、消息与必要容量，七场景。两者支持 `--inputs` JSON，阶段速率是条件输入，均不宣称完整实测运行时。

`python3 calculations/calc.py qwen235-expert-granularity --format md` 比较真实235B基线与专家数量/宽度/top-k变体，六场景逐矩阵、目的集合及容量；专家参数预算与包含router的总参数预算分开，未训练变体不推质量。

`python3 calculations/calc.py architecture-tile-work --format md` 接深窄/浅宽的逐矩阵有效/矩形/tile补齐工作，四场景；`python3 calculations/calc.py plot-capacity-curves` 从冻结逐rank数据重画图2-7容量曲线（可选Matplotlib）。两者不把算术比例或容量当作实际硬件利用率/吞吐。

`python3 calculations/calc.py trace-resource-bridge --format md` 将四条封存Chat的可证长度代入Qwen8输入阶段资源账；条件串行返回ID场景另列，不将返回ID数冒充观测模型调用数。本地原件与锁位于 `sources/trace-resource-bridge/`。

`python3 calculations/calc.py plot-architecture-shapes` 重画图2-7架构形状伴图：六面板由冻结数据生成，层/专家数量与矩阵形状、完整参数差并列，SVG/PNG/PDF/data均可导出（可选Matplotlib）。

`python3 calculations/calc.py request-hardware-bridge --format md` 将原四模型请求逐调用工作与官方H100精度供给对应，四场景保留混合PV、K3未分类、特殊操作/物理HBM未知；完整请求时延与排名不推断。

单层 Flash MTP：`python3 calculations/calc.py v4-mtp-forward --format md`。`--inputs` JSON 可指定 `batch`、`tokens`、`start_pos`、`routing`；输入特征由调用方提供，结果不推断实际草稿接受率或加速比。

同轨迹缓存：`python3 calculations/calc.py trace-cache-lifecycle --format md`，`--inputs`可指定host/remote有效带宽和lookup_ns；报告保留原device命中与条件迁移的区别。

专家颗粒度条件选择：`python3 calculations/calc.py granularity-selection --format md`。输入remaining_ns默认未知；可声明两方案剩余串行成本以复现选择翻转，不代表质量或实测性能排名。

图2-8：`python3 calculations/calc.py plot-chat-agent`（可选Matplotlib），输出原Chat/Agent记录与条件KV六面板SVG/PNG/PDF；先运行reproduce更新结果。


实验4-3容量与带宽代际对照：`python3 calculations/calc.py storage-generation-comparison --format md`。固定官方Qwen8/235逐张量与五款硬件，54工作负载、810独立容量/带宽/产品组合；完整形状与精确分数见[JSON](results/storage-generation-qwen8-235.json)，[可读表](results/storage-generation-qwen8-235.md)分别列常驻与选中专家读取。低位格式、workspace与逻辑接口访问有明确条件，不代表实测HBM或完整时延。


FA4表1与单SM资源配比：`python3 calculations/calc.py fa4-resource-balance --format md`。16个tile/供给场景复算真实Qwen8头宽下QK/PV、SMEM重复读取及指数资源下界；[可读结果](results/fa4-qwen8-resource-balance.md)、[精确JSON](results/fa4-qwen8-resource-balance.json)。归档官方论文与提取文本位于sources/fa4-resource-balance，输入/哈希位于configs/fa4-resource-inputs.json。SMEM与HBM分开，倍率是假设，完整kernel时延仍未知。


实验4-4的注意力输入有限槽流水：`python3 calculations/calc.py attention-input-pipeline --inputs calculations/scenarios/attention-input-example.json --format md`。默认及五个变体已纳入reproduce，逐块保存issue/ready/compute/release；[默认结果](results/attention-input-base.md)、[矩阵翻倍](results/attention-input-matrix-double.md)、[K16](results/attention-input-tile-k16.md)。输入容量、寄存器暂存与累加器分开；时序仅为声明条件下QK累加器就绪，不是完整注意力或实测周期。


V4共享专家FP8搬运坐标：`python3 calculations/calc.py v4-copy-coordinates --rows 32 --format md`。公共结果包括[M32](results/v4-copy-coordinates-m32.md)与[M64](results/v4-copy-coordinates-m64.md)，逐tile列A/B/scale/C起点、相对offset及stride；计源级T.copy而非PTX/SASS指令。输入要求M32/N128/K128对齐，未推断尾部谓词、TMA数量或物理HBM。


矩阵—向量交接条件计算：`python3 calculations/calc.py matrix-vector-handoff --inputs calculations/scenarios/matrix-vector-example.json --format md`。[两槽行组结果](results/matrix-vector-staged-rows32-slots2.md)与[整块交接](results/matrix-vector-staged-rows128-slots1.md)比较完整行依赖、槽位至PV释放和中间写读；八场景纳入reproduce。direct是声明的一次传送路径，未映射为实际厂商接口；时间为教学tick，非完整kernel实测。


配对投影费用/功率条件：`python3 calculations/calc.py paired-projection-cost --format md`默认保留未知费用和功率；`--inputs calculations/scenarios/paired-projection-cost-example.json`代入显式假设。[原时间门槛](results/paired-projection-unknown.md)及[声明2倍费用率](results/paired-projection-declared-2x.md)已纳入reproduce。原始runner/计时记录/manifest位于sources/paired-projection-cost，内容锁位于configs/paired-projection-cost.lock.json。11组16次批平均中位数不等于单次p95，不将TDP、时延代理或算子夹具检查升级为实际整机能耗/整模型成本。


Qwen3.6-35B-A3B：`python3 calculations/calc.py qwen36-forward --format md` 输出固定官方配置和checkpoint形状下的基础文本逐算子账（支持JSON/Markdown/CSV）；`--inputs calculations/scenarios/qwen36-forward-example.json` 修改请求。`python3 calculations/calc.py qwen36-capacity --format md` 为官方硬件容量与声明余量下的必要筛选；[可编辑容量输入](scenarios/qwen36-capacity-example.json)、[8192 prefill](results/qwen36-prefill-8192.md)、[decode](results/qwen36-decode-b1.md)、[容量](results/qwen36-capacity-b1-n8192.md)。全部专家常驻与本次选择的专家权重读量分开，视觉/MTP文件权重与它们尚未覆盖的运行路径分开。


内存池原文算例：`python3 calculations/calc.py memory-pool-access --copies 1 --format md` 复算四台64GiB的局部短缺、远端快照周期读取与副本故障依赖；`--copies 2`/`3`增加独立供体副本。结果含24组声明接口条件，[图6-8](results/memory-pool-layout.svg)由同一结果生成；乐观服务模型不证明真实队列稳定，动态KV及恢复成本另算。


增长KV协议算例：`python3 calculations/calc.py growing-remote-kv --inputs calculations/scenarios/growing-remote-kv-example.json --format md`，使用Qwen3-8B/Qwen3.6真实配置，逐token旧历史读取、当前操作数、初始化/追加副本发送与commit epoch分列。支持全量远端与固定远端前缀/本地tail；可改batch、prompt、steps、副本、接口及本地tail预算。通信时间骨架不是实测decode，尾部预算不是整机容量。

实验6-10综合成本：`python3 calculations/calc.py supernode-cohort-cost --inputs calculations/scenarios/supernode-cohort-example.json --format md`，比较同8卡的TP8/TP4/TP2服务副本，连接真实模型容量、声明服务时长、故障重启、完整响应SLO与有效请求成本。54个固定场景使用Qwen3-8B/32B；费用和时长均为教学输入。先reproduce，再运行`plot-supernode-cost`生成图6-9及精确阶梯数据。

真实梯度分层通信：`python3 calculations/calc.py hierarchical-gradient --inputs calculations/scenarios/hierarchical-gradient-example.json --format md`。固定Qwen3-8B首层gate梯度，FP32/BF16、平坦连续/交错与分层、单/双NIC共12场景。JSON保留逐轮贡献和物理条带区间；Markdown列阶段和每资源字节。所有速率/启动均为教学输入，预算通过只是必要下界未排除，不是训练期限保证。

图片文件请求：`python3 calculations/calc.py image-request-budget --inputs calculations/scenarios/image-request-example.json --format md`，声明bytes、速率与阶段秒数（用整数/分数字符串），计算完整成片、压缩和本地交叉点。先reproduce，再`plot-image-request`生成图12-1。默认是教学预算，不是RAW/JPEG实际解码、VAE或网络测量；预览未知。

图片分块与预览：`python3 calculations/calc.py image-request-streaming --inputs calculations/scenarios/image-streaming-example.json --format md`。同bytes/工作比较整图屏障与显式独立块；前后传播分别建模，预览额外编码/下行与最终成片独立交付。独立性与质量是声明条件，不是任意真实模型可分块的证明。

有限ACK窗口：`python3 calculations/calc.py connection-window --inputs calculations/scenarios/connection-window-example.json --format md`。显式完整图片消息、共享上下行、ACK可见前缀、发送/接收窗口、一次指定丢段与固定timeout；所有轨迹可查。它是自定义有限教学协议，不是TCP/QUIC实现。

连续请求与窗口：`python3 calculations/calc.py connection-sequence --inputs calculations/scenarios/connection-sequence-example.json --format md`。声明协议的完整事件记录区分成片与最后 ACK；不是实际 TCP/QUIC 测量。

协议消息图与长早期上传：`python3 calculations/calc.py protocol-handshake --inputs calculations/scenarios/protocol-handshake-example.json --format md`；`python3 calculations/calc.py protocol-early-stream --inputs calculations/scenarios/protocol-early-stream-example.json --format md`。七份RFC固定校验，包布局与链路输入声明，不是完整协议栈或实测网络性能。
