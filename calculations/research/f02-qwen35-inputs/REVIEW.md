# Qwen3.5 F02 固定输入交付

已完成现有 `Qwen/Qwen3.5-397B-A17B` 的输入准备，未改共享配置／源码，未下载任何权重载荷。模型固定 revision 为 `8472618112abcbd45acbcdc58436aff4233c23f7`，重新取得的 config 与共享既有 config 逐字节相同。

官方模型 API 原件列出 94 个 safetensors 分片、config、index、处理器文件，但不含 modeling 实现。固定 [模型说明](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/blob/8472618112abcbd45acbcdc58436aff4233c23f7/README.md) 要求 Transformers；因此将实现另锁到 `huggingface/transformers` commit `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`。这两个仓库的 revision 不相同，不能说模型仓库直接指定了该实现 commit。实现对应架构 `Qwen3_5MoeForConditionalGeneration`，基础文本张量形状已与同模型 checkpoint 全量对照。

## 可合并原件与可复现证据

[source-lock.patch.json](source-lock.patch.json) 含 204 条可合入 `configs/sources.lock.json` 的 downloaded 记录，文件仍位于本独立目录，共 1127274 bytes。文件路径无需移动；若主线要移动到 sources 目录，必须同步改 lock 的 file 字段。已有共享 config 原件可继续使用，本目录的同字节副本仅提供请求证据。锁包含实现／默认配置／modular 文件、cache／vision／RoPE 必要辅助源、模型 index／README／processor 配置以及 94 份原始 header JSON 和 94 份长度前缀。

[http-evidence.json](http-evidence.json) 保存实际 URL、HTTP 状态、Content-Range、读取 bytes 与时间。188 次 Range 请求均为 206 且边界严格匹配：先只读 0–7 得到长度，再只读 8–(7+length)。服务器不遵守 Range 或长度超过上限即拒绝；没有读入 tensor data。94 个头不等于 94 份权重。

API model tree／Transformers commit 与递归树原件保存在 api/，观察记录单放 [api-observation.lock.json](api-observation.lock.json)，未将最初发现 main 的可变 API 端点塞入可重取计算源锁。后续 `fetch.py` 已固定 Transformers commit，不再追踪 main。该脚本仅下载小原件与 metadata；离线复核用 `python calculations/research/f02-qwen35-inputs/audit.py`。

## 实际 checkpoint 核验

[header-audit.json](header-audit.json) 与 [tensor-inventory.json](tensor-inventory.json) 保留结果和每个 tensor 的原始 shape／dtype／offset。索引 key 唯一性、shard 归属、shape×dtype 字节、连续 offsets 及 total_size 全通过。

| 部分 | 参数元素 | tensor payload bytes |
| --- | ---: | ---: |
| 基础文本，含 embedding／head | 396346350336 | 792692717952 |
| 视觉 | 456010480 | 912020960 |
| MTP | 6595568128 | 13191136256 |
| 全 checkpoint | 403397928944 | 806795875168 |

2924 个张量中 BF16 2834 个、FP32 90 个。基础文本预期张量 1038 个全部名称／形状相符，无缺失、无未枚举基础文本张量、无形状冲突。视觉和 MTP 已核实际存储，但本次没有全量 config→预期形状枚举，不能将文本一致性扩大为全部 runtime 加载验证。没有出现 K3 的 A_log 头数差异。

## 逐矩阵所需字段与接口

以下是后续适配器输入契约，不是新前向计算专题。记 `M=B*T`；矩阵乘按 `2*M*K*N`，专家使用每专家 `n_e`，不能把总参数或型号标签乘 token 代替算子图。

| 阶段／调用次数 | 权重或矩阵 K→N | 必須分列的工作与状态 |
| --- | --- | --- |
| embedding／最终 head | 词表248320，H4096；head 4096→248320 | embedding 是 gather；head 输出行数按实际 logits_to_keep 路径，不自动当最后一行；最终 RMSNorm |
| 45 个 linear_attention 层 | qkv 4096→12288；z 4096→8192；a、b各4096→64；out 8192→4096 | key 16×128，value 64×128；q/k 复制4倍后进入64头递推，不能把投影也乘4 |
| 每个 linear 层卷积 | depthwise `[12288,1,4]` | 仅 qkv 通道经过 causal conv+SiLU；prefill 与有缓存更新的历史拼接／裁切分开 |
| 每个 linear 层 recurrence | 每头 state `[128,128]`，64头 | FP32 fallback 中 decay→KᵀS→delta→outer update→QᵀS，逐 token 依赖；g=-exp(A_log)*softplus(a+dt_bias)，beta=sigmoid(b)，Q/K L2 norm、gated RMSNorm与z另计 |
| 15 个 full_attention 层 | q+gate 4096→16384；K/V各4096→512；O8192→4096 | Q为32×256，KV为2×256；Q投影含第二份输出 gate，不能复用无gate Qwen3账；QK norm、部分RoPE、sigmoid gate另计 |
| 每个 full 层 attention | QKᵀ与PV按32查询头／2KV头、有效时序对计 | causal pair 数与物理masked执行分开；每请求每历史token KV含2×2×256元素，15层累计 |
| 60 个 MoE block | router4096→512；每专家gate/up4096→1024、down1024→4096；512专家／top10 | 全权重驻留与每步激活10专家分开；逐专家n_e，FP32 softmax→topk→renorm→cast→gather/加权合并 |
| 每个共享专家分支 | gate/up4096→1024，down1024→4096；shared gate4096→1 | 共享分支每token执行；sigmoid scalar gate、乘法、与routed输出相加 |
| 27 个视觉 block | patch 1536→1152；qkv1152→3456；O1152→1152；MLP1152→4304→1152 | patch 为3×2×16×16；16头，head72；逐时间块HW attention，bias/LayerNorm/GELU/位置插值另计 |
| 视觉最终 merger | 每4patch合并4608；4608→4608→4096 | config position2304；grid合法性／THW÷4 embedding数，单份merger；deepstack_visual_indexes为空，不沿用Omni四份载荷 |

关键代码在 [modeling_qwen3_5_moe.py](transformers/src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py)：GatedDeltaNet 504 起、Attention 749 起、router 882 起、视觉 1039 起；[cache_utils.py](transformers/src/transformers/cache_utils.py) 保存 cache 合约。模型 head_dim256 与 H/heads=128 不同，不能从 hidden_size/num_attention_heads 反推 head_dim。

线性注意力 fallback 只在已有 state 且 seq_len=1 时选 recurrent，其余选 chunk；chunk 的块内三角解／矩阵与补齐不能拿单步公式直接乘T当真实kernel账。FP32 recurrent state 每层每请求 64×128×128×4=4194304 bytes，45层为188743680 bytes；卷积槽按独立实际dtype／cache布局读取固定实现，不能从权重dtype推断。完整 attention 的 KV 在15层增长，不能把60层都当GQA KV，也不能把45层recurrent状态当随context线性增长。

## 可验收范围与下一步

F02 中 Qwen3.5 的“必要 config／实现缺源”已具备可合并证据，同时 index／全部 metadata headers 也齐全。主线可先合入 source-lock 补丁并运行来源核验，再更新公共 F02 输入审查；本次不改 generic forward、不宣称已支持完整 Qwen3.5 计算。

下一适配器应单独组合45层 GatedDeltaNet、15层 gated GQA、60层MoE与全局节点；prefill／带state单步／prefix续算至少三场景，对照1038个已核基础文本形状。MTP源码运行路径未在当前 Transformers 基础类中闭合，必须与已盘点6.596B参数分开；vision需保留独立grid与时间轴。hub kernel替换、实测访存、runtime allocator、训练aux loss和质量均不由本输入审查证明。
