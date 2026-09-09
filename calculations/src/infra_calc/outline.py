"""Sync calculation evidence to chapter companions, preserving the edited main outline."""
import json
import re

from .paths import PROJECT, BOOK


def insert_evidence(book, filename, key, paragraph, before):
    """Update calculation evidence without undoing an editor's chapter ownership."""
    outlines = book / "outlines"
    main = outlines / filename
    prefix = f"**已复算（{key}）：** "
    pattern = r"(?m)^" + re.escape(prefix) + r".*$"
    # A record may have moved to another chapter during editorial consolidation.
    owners = [p for p in sorted((outlines / "extensions").glob("*.md"))
              if prefix in p.read_text()]
    preferred = outlines / "extensions" / filename
    relocated = {
        "C03-memory-concurrency": 4, "C05-modern-scope": 6,
        "C14-request-hardware-bridge": 4, "C14-trace-cache-lifecycle": 9,
        "C14-chat-agent-figure": 3, "C13-llama70-placement": 6,
        "C13-qwen235-placement": 6, "C13-qwen235-eight-way": 6,
        "C13-granularity-selection": 6, "C13-dense-local-quantization": 6,
        "C13-architecture-tile-work": 5, "C13-capacity-curves": 6,
        "C18-rl-supply": 10, "C36-growing-kv": 9,
    }
    if key in relocated:
        destination = next((outlines / "extensions").glob(f"{relocated[key]:02}-*.md"))
    else:
        destination = preferred if preferred in owners or not owners else owners[0]
    if not destination.exists():
        raise ValueError(f"Missing chapter companion: {destination}")
    text = destination.read_text()
    line = prefix + paragraph.replace("](../", "](../../")
    if prefix in text:
        text = re.sub(pattern, lambda _: line, text)
    elif before in text:
        text = text.replace(before, line + "\n\n" + before, 1)
    else:
        # Historical companions need not mirror the current exercise headings.
        text = text.rstrip() + "\n\n" + line + "\n"
    destination.write_text(text)
    original = main.read_text()
    revised = re.sub(pattern + r"\n?", "", original)
    revised = re.sub(r"\n{3,}", "\n\n", revised)
    changed = [str(destination.relative_to(book))]
    if revised != original:
        main.write_text(revised)
        changed.append(str(main.relative_to(book)))
    return changed


def sync() -> dict:
    from .reproduce import verify_results
    verify_results()

    def result(name):
        return json.loads((PROJECT / "results" / (name + ".json")).read_text())["summary"]

    updated = set()

    def insert(filename, key, paragraph, before):
        updated.update(insert_evidence(BOOK, filename, key, paragraph, before))

    prefill = result("qwen3-8b-prefill-8192")
    decode = result("qwen3-8b-decode-b1-s8192")
    prefix = result("qwen3-8b-prefix-6144-plus-2048")
    insert("02-模型架构.md", "C07",
           f"[计算项目](../calculations/README.md)已按官方配置与 checkpoint 索引复核全部 {prefill['parameters']:,} 个参数，统一 BF16 权重为 {prefill['weight_resident_bytes']/2**30:.6f} GiB。"
           f"本节四个固定场景的[逐算子结果](../calculations/results/README.md)已生成：8192-token prefill 的有效因果矩阵工作加最后位置输出头为 {prefill['matrix_flops']/1e12:.6f} TFLOPs；"
           f"S=8192、B=1 的一次 decode 为 {decode['matrix_flops']/1e9:.6f} GFLOPs；命中 6144 后补入 2048 的矩阵工作为 {prefix['matrix_flops']/1e12:.6f} TFLOPs、新增 KV 为 {prefix['kv_new_write_bytes']/2**20:g} MiB。"
           "归一化、激活、位置编码、特殊函数与操作数读写另列；矩形物化路径和因果有效工作不是同一计量，不能将表中载荷直接当 HBM 实测。运行 `python3 calculations/calc.py reproduce` 重建 JSON／Markdown／逐层 CSV。",
           "> **实验 2-2")
    insert('02-模型架构.md', 'C09-MLA',
           '[K3 MLA 展开路径](../calculations/results/k3-mla-expanded-b1-t8192-s0.md)与[compact 吸收路径](../calculations/results/k3-mla-compact-b1-t8192-s0.md)已按实际 24 层计算全部投影、QK/PV、归一化和输出门控。B=1、T=8192 时，MLA 缓存分别为 11.25 GiB 与 216 MiB；两路径投影矩阵工作相同，compact 的有效注意力矩阵工作为展开路径的 3.4 倍。qk_rope_head_dim 虽为 64，官方 mla_use_nope 路径不执行 RoPE，但保留这条额外 Q/K 分支。sigmoid 输出门控位于 Wv 与 o_proj 之间，不可跨门控合并投影。CLI 为 `python3 calculations/calc.py k3-mla --path compact --tokens 8192`；compact 是经小矩阵验证的代数替代路径，不是固定 HF 实现的缓存方式。',
           '> **实验 2-3')
    flash = result("state-deepseek-v4-flash-n8192-b1-native")
    pro = result("state-deepseek-v4-pro-n8192-b1-native")
    insert("02-模型架构.md", "C10-state",
           f"[Flash 状态结果](../calculations/results/state-deepseek-v4-flash-n8192-b1-native.md)在 N=8192、B=1、历史 BF16 下给出 {flash['history_resident_bytes']/2**20:g} MiB 历史，加 {flash['compressor_buffer_bytes']/2**20:g} MiB FP32 压缩器槽；最后查询的主注意力及索引载荷为 {flash['selected_history_payload_bytes']/2**20:g} MiB。"
           f"[V4-Pro 独立配置结果](../calculations/results/state-deepseek-v4-pro-n8192-b1-native.md)按 61 层的 30 CSA＋31 HCA 和 top-k=1024 重算，当前状态合计 {pro['resident_bytes']/2**20:g} MiB、选中历史载荷 {pro['selected_history_payload_bytes']/2**20:g} MiB。"
           "CLI 为 `python3 calculations/calc.py state --model deepseek-v4-pro --length 8192`；这是状态与部分注意力工作，完整压缩更新、全模型 FLOPs、真实量化格式和 MTP 仍待计算。",
           "> **实验 2-4")
    insert("02-模型架构.md", "C11-state",
           "[Kimi K3 状态计算](../calculations/results/state-kimi-k3-n8192-b1-compact.md)按实际 69 KDA＋24 MLA 分层：N=8192、B=1 时，FP32 recurrent state 为 414 MiB；紧凑 BF16 MLA 为 216 MiB，另按 kernel_size=4 的短卷积槽假设计 19.40625 MiB。"
           "[展开缓存路径](../calculations/results/state-kimi-k3-n8192-b1-expanded.md)的 MLA 为 11.25 GiB。两条路径通过 `--mla-path compact`／`expanded` 明确选择；全模型前向、分块 KDA prefill 与检查点复制的计算仍待补齐。",
           "> **实验 2-5")
    insert('02-模型架构.md', 'C11-KDA-recurrent',
           '[K3 KDA 递推子账](../calculations/results/k3-kda-b1-t1-s8192.md)已按实际 69 层、96×128 通道计算 Q/K/V、低秩 f、beta、全秩输出 gate 和 o_proj；另列三路 width=4 无 bias 短卷积、Q/K L2Norm、带 -5 下界的 sigmoid 衰减门控与递推状态更新。输出 RMSNorm 的 128 个 scale 在 heads 间共享，不能按 12288 维重复计参数。B=1 的 FP32 recurrent state 为 414 MiB。CLI 为 `python3 calculations/calc.py k3-kda --batch 64 --tokens 1`；T>1 的数学递推基线不代表官方 chunk prefill kernel 工作，选定 FLA 参照版本与 K3 固定代码的 API 差异明确保留。',
           '> **实验 2-5')
    insert('02-模型架构.md', 'C11-AttnRes',
           '[K3 AttnRes 逐层调度](../calculations/results/k3-attn-res-b1-t8192.md)按 block_size=12 展开 93 层：第 0 层不做 attention 混合，块边界先混合旧块再追加 prefix，FFN 使用新候选数；全图共 186 次混合，最终保存 8 个块、输出混合有 9 个候选。norm.weight×proj.weight 按每次调用一次计量，不能按 token 重复计算；prefix 加法按 178 次逐元素加计入。块堆栈是本次 forward 的深度状态，每次调用重新建立，不是额外的跨 token KV。CLI 为 `python3 calculations/calc.py k3-attn-res --batch 64 --tokens 1`；逐次形状、加权矩阵／标量工作及独立张量容量已输出，未将容量相加冒充工作区峰值。',
           '> **实验 2-5')
    insert('02-模型架构.md', 'C11-KDA-chunk-buffers',
           '[选定 FLA KDA chunk 分配结果](../calculations/results/k3-kda-chunk-t8192-c64.md)在 B=1、T=8192、chunk_size=64 下，每层中间 chunk state 为 384 MiB；Aqk／Akk、FP32 对角块、WY 输出和后续状态／输出的存活阶段已核对，最大已确认存活子集为 1926 MiB。它不包含全部输入、投影和后端 scratch，因此不是完整峰值；也不能乘 69 个顺序执行层。全层最终 recurrent state 的 414 MiB 另计。CLI 为 `python3 calculations/calc.py k3-kda-chunk --tokens 8192`；T=65 的尾块案例分别验证 T×chunk_size 注意力缓冲和 ceil(T/chunk_size) 状态轴，数学块算法已补下三角 KK、W/U 前代求解、状态预测、因果 QK/PV 和状态更新，并用非零初始状态／尾块案例验证与逐 token 递推的输出和最终状态一致；这是有效三角项计量，融合 kernel 的填充与完整指令算术仍另算。',
           '> **实验 2-5')
    moe = result('qwen3-235b-a22b-decode-b64-s8192-balanced')
    concentrated = result('qwen3-235b-a22b-decode-b64-s8192-concentrated')
    insert('02-模型架构.md', 'C12-Qwen',
           'Qwen3-30B-A3B／235B-A22B 已实现完整逻辑前向，权重键及 BF16 总字节逐项对上官方 checkpoint 索引。'
           f"以 [235B 的 B=64、S=8192 decode](../calculations/results/qwen3-235b-a22b-decode-b64-s8192-balanced.md) 为例，矩阵工作为 {moe['matrix_flops']/1e12:.6f} TFLOPs；每层 512 次专家分派，均匀路由覆盖 128 个专家，专家权重载荷为 {moe['routed_expert_unique_weight_payload_bytes']/2**30:g} GiB。"
           f"[集中到相同 8 个专家](../calculations/results/qwen3-235b-a22b-decode-b64-s8192-concentrated.md)时 FLOPs 不变，专家权重载荷降至 {concentrated['routed_expert_unique_weight_payload_bytes']/2**30:g} GiB，相差 16 倍。"
           '每专家 token 数、三次 GEMM 尺寸、FP32 路由 softmax／top-k／归一化及 gather／合并分别输出；该载荷不是 HBM 实测，也不包含专家并行通信。V4、K3 的专家适配继续单独实现。',
           '> **实验 2-6')
    v4_experts = result('experts-deepseek-v4-flash-b64-balanced')
    k3_experts = result('experts-kimi-k3-b64-balanced')
    insert('02-模型架构.md', 'C12-expert-matrices',
           f"[V4-Flash FFN 矩阵台账](../calculations/results/experts-deepseek-v4-flash-b64-balanced.md)在 B=64、T=1 下为 {v4_experts['ffn_matrix_flops']/1e12:.6f} TFLOPs，含 routed／shared 专家和 router；前 3 个 hash 层仍计算 router GEMM，int32 路由表另占 {v4_experts['hash_lookup_resident_int32_bytes']:,} bytes，不计为浮点参数。"
           f"[Kimi K3 台账](../calculations/results/experts-kimi-k3-b64-balanced.md)同场景 FFN 矩阵为 {k3_experts['ffn_matrix_flops']/1e12:.6f} TFLOPs，含 92 层的 3584 维 routed 专家、保持 7168 维的共享分支、双向潜空间投影及第 0 层 dense FFN。"
           '各专家真实 M 维、共享分支和矩阵层编号分别输出；CLI 为 `python3 calculations/calc.py experts --model kimi-k3 --batch 64`。矩阵之外另列路由、激活、归一化及合并算术：V4 在 down 投影前按中间维 F 乘路由概率，K3 在投影后按潜空间维 R 加权；K3 Situ 含两次 tanh，特殊函数不折算 Tensor FLOPs。参考 dispatch 的索引、掩码、gather、排序端点、重排与合并载荷已单列；排序／直方图内部流量保持未知。mHC／AttnRes、MTP 及真实混合量化元数据仍待补齐，不作为全模型参数量或完整前向结论。',
           '> **实验 2-6')
    insert('02-模型架构.md', 'C12-V4-format',
           '[V4 专家实际格式结果](../calculations/results/experts-deepseek-v4-pro-b64-balanced.md)分别列 FP4 packed 权重和每 32 个 K 元素一个 E8M0 scale，合计每参数 17/32 bytes。固定参考 kernel 把 FP4 权重转为 FP8，再执行 FP8×FP8、FP32 累加，不能套用原生 FP4 峰值。每专家 M 维补齐到 32 的 tile 工作与有效 FLOPs 分列：Pro 在 B=64 的均匀路由中，每个专家一行，参考矩阵 tile 工作为有效工作的 32 倍；该比例不是实测时延比例。这里仅覆盖 routed 专家，尚非全模型实际存储。',
           '> **实验 2-6')
    hc = result('hc-deepseek-v4-flash-b1-t8192')
    insert('02-模型架构.md', 'C10-mHC',
           f"[V4-Flash mHC 子账](../calculations/results/hc-deepseek-v4-flash-b1-t8192.md)按每层 attention／FFN 两套混合参数和最终 hc_head 计算：B=1、T=8192 时，混合投影为 {hc['matrix_flops']/1e9:.6f} GFLOPs，普通算术为 {hc['scalar_flops']/1e9:.6f} GFLOPs，特殊函数独立计数。"
           '20 次 Sinkhorn 按源码展开为初始行 softmax 加 39 次归一化；中间片段留在 kernel 局部存储，不能乘迭代数当 HBM 流量。最终 hc_head 处理全部新 token，词表头才选择最后位置。运行 `python3 calculations/calc.py hyper-connections --model deepseek-v4-flash --tokens 8192` 复现；该子账不含注意力、专家、外部 RMSNorm、MTP 或词表投影。',
           '> **实验 2-4')
    va = result('attention-deepseek-v4-flash-b1-t8192-s0')
    insert('02-模型架构.md', 'C10-attention-matrices',
           f"[V4-Flash 注意力矩阵子账](../calculations/results/attention-deepseek-v4-flash-b1-t8192-s0.md)在 B=1、T=8192 下，投影工作为 {va['projection_matrix_flops']/1e12:.6f} TFLOPs，有效 QK/PV 为 {va['effective_qk_pv_matrix_flops']/1e12:.6f} TFLOPs，参考实现的矩形索引点积为 {va['reference_index_matrix_flops']/1e12:.6f} TFLOPs。"
           '低秩 Q、共享 KV、分组 wo_a／wo_b、两种压缩器及 Indexer 投影分别列尺寸；压缩器每个新 token 都执行投影，不能只在压缩块完成时计量。Indexer 在 prefill 先做矩形点积再加 mask，有效因果点积另列作对照。CLI 为 `python3 calculations/calc.py v4-attention --model deepseek-v4-flash --tokens 8192`；压缩池化 softmax、加权归约、Q/K 归一化、RoPE 及索引评分标量已另列；ratio=4 的重叠窗口与 prefill 保存块的额外位置偏置相加均按源码计量。稀疏 kernel 另计固定 64-slot tile GEMM、在线 softmax 和 attention sink；无效索引屏蔽 KV 读取但不消除 tile GEMM，共享 KV 在 QK/PV 间复用。Hadamard 蝶形加减／缩放与 FP4／FP8 模拟量化除法／缩放已展开，abs/max、clamp、位操作和格式转换分列；CUDA 指令、数据移动及后端实测流量仍待补齐。',
           '> **实验 2-4')
    full = result('forward-deepseek-v4-flash-b1-t8192-s0')
    insert('02-模型架构.md', 'C10-forward-ledger',
           f"[V4-Flash 基础前向汇总](../calculations/results/forward-deepseek-v4-flash-b1-t8192-s0.md)已衔接注意力、专家、mHC、外部 RMSNorm、嵌入及最后位置词表头。B=1、T=8192 时，有效注意力口径矩阵工作为 {full['matrix_flops_effective_attention']/1e12:.6f} TFLOPs；基础逻辑参数为 {full['logical_parameters_excluding_mtp_and_quant_scales']:,}，不含 MTP、量化 scale 与整数 hash 表。"
           'CLI 为 `python3 calculations/calc.py v4-forward --model deepseek-v4-flash --tokens 8192`。JSON 保留全部子账和 coverage：已知 sparse/expert tile 通过替换有效项进入另一总数；已核对官方全部 checkpoint 索引和分片元数据头，基础逻辑参数与推导一致，checkpoint 的基础模型／MTP／scale／I64 hash 表字节分开；其余投影 padding、运行时格式转换及完整访存仍未闭合，运行时完整字节和时延保持 null，不作为全书工作包完成证明。',
           '> **实验 2-4')
    sequence = result('cache-sequence-qwen3-8b-b1')
    insert('02-模型架构.md', 'C08-cache-sequence',
           f"[整段缓存计算](../calculations/results/cache-sequence-qwen3-8b-b1.md)按 P=8192、随后 G=1024 次单 token 调用，累计旧历史记录为 GP+G(G−1)/2={sequence['decode_prior_history_records_per_request']:,}；Qwen3-8B 的 GQA 旧历史逻辑读取合计 {sequence['decode_prior_history_read_payload_bytes']/2**30:.6f} GiB，追加写入 {sequence['decode_append_write_bytes']/2**30:.6f} GiB，最终缓存 {sequence['final_persistent_state_bytes']/2**30:.6f} GiB。"
           '这些载荷不等于 HBM 实测，当前 token 操作数与旧历史、写入分开。MHA／MQA 为架构对照，不是现有 GQA checkpoint 的执行开关；其 QK/PV 工作不随 KV 头缩减。完整 prefill 与命中 6144 后的后缀比较、无缓存重算的 token 行／因果矩阵工作，以及 K3 expanded／compact 整段累计均已输出；K3 前缀检查点必须包含对应位置的 KDA 和短卷积状态。运行 `python3 calculations/calc.py cache-sequence --model kimi-k3 --batch 64 --format md` 复现；工作区、物理共享和并行复制继续归容量／放置专题。',
           '> **实验 2-3')
    k3_full = result('forward-kimi-k3-b1-t8192-s0-expanded')
    insert('02-模型架构.md', 'C11-forward-ledger',
           f"[Kimi K3 文本前向汇总](../calculations/results/forward-kimi-k3-b1-t8192-s0-expanded.md)连接 24 层 MLA、69 层 KDA、专家、AttnRes、外部归一化、嵌入和词表头。B=1、T=8192、expanded MLA 与块式 KDA 数学口径下，矩阵工作为 {k3_full['matrix_flops']/1e12:.6f} TFLOPs，源代码枚举文本逻辑参数为 {k3_full['logical_text_parameters']:,}。"
           '运行 `python3 calculations/calc.py k3-forward --tokens 8192` 复现；`--output-head all` 对应非 generation_mode 的全位置词表输出。块式 KDA 替换递推核心及衰减指数，不重复相加；AttnRes 已含前缀累加。compact MLA 是代数替代方案，块式数学 FLOPs 不是 fused kernel 指令数。官方 96 个分片、497220 个张量的索引和元数据头已核对；文本 checkpoint 载荷为 1559965606912 bytes，其中量化 scale 为 85085650944 bytes。69 个 KDA A_log 的 checkpoint 长度为 128，而同 revision 配置／代码为 96，参数差 2208、FP32载荷差 8832 bytes 已显式报告。固定FLA两种KDA wrapper兼容状态布局参数别名，但该别名不解决A_log形状冲突；不静默截断，也不宣称可直接加载执行。运行时格式转换、完整访存及多模态／MTP 仍列入 coverage，完整运行时字节与时延保持 null。',
           '> **实验 2-5')
    finite = result('pipeline-finite-1-slots')
    insert('06-超节点.md', 'C32-finite-buffers',
           f"[有限槽位与反压](../calculations/results/pipeline-finite-1-slots.md)在每个流水边界的发送端和接收端各保留一个槽位，基础教学场景的边界缓冲池为 {finite['reserved_boundary_pool_bytes']:,} bytes；它与实际存活峰值分别输出。"
           '运行 `python3 calculations/calc.py pipeline-schedule --buffer-slots 2 --format md` 比较双缓冲。有限模式先取得输出槽再启动生产计算，发送槽在传输完成后释放，接收槽在消费计算完成后释放；不足时上游或传输等待。槽位编号和释放时间逐条保存，局部等待可能重叠，不能再次加到总完成时间上。该预算仅含边界双端副本，尚非完整设备工作区。',
           '> **实验 6-2')
    pipeline = result('pipeline-four-groups')
    insert('06-超节点.md', 'C32-pipeline-schedule',
           f"[FIFO 推理流水时间线](../calculations/results/pipeline-four-groups.md)用显式的 4 阶段各 1 ms、边界 0.1 ms、反馈 0.1 ms 教学输入，调度 4 个请求组、各 4 步生成，全部完成为 {pipeline['finish_ns']/1e6:.6f} ms。"
           '运行 `python3 calculations/calc.py pipeline-schedule --microbatches 1 --format md` 比较单请求反馈依赖；更多请求、慢链路和不均衡阶段另有场景。阶段与边界链路分别串行，固定 FIFO 次序不宣称最优；发送缓冲保持到传输完成，接收缓冲保持到消费计算结束，逐时刻累加存活量。阶段空闲包含填充／排空、反馈及链路等待，不能全部称为训练气泡；耗时是教学输入，尚非真实 Qwen 性能。',
           '> **实验 6-2')
    communication = result('dense-comm-qwen8-tp8-pp1-t1')
    insert('06-超节点.md', 'C32-dense-communication',
           f"[基础 TP／PP 通信路径](../calculations/results/dense-comm-qwen8-tp8-pp1-t1.md)在每层两次归约之外加入词表分片嵌入归约、最后位置 logits all-gather、采样 token 回传与首阶段广播；TP=8、PP=1 的单 token 教学通信路径合计 {communication['serial_communication_path_seconds']*1000:.6f} ms。"
           'CLI 为 `python3 calculations/calc.py dense-communication --tp 2 --pp 4 --format md`。输入激活随新 token 数增长，但最后位置 logits 不乘整个 prefill 长度；默认 logits 每元素四字节是显式线格式。DP 复制网络总字节，不将单副本时间乘 DP。采样计算、控制元数据、共享链路与流水气泡仍另计，不把通信路径模型当完整迭代时延。',
           '> **实验 6-2')
    placement = result('placement-qwen8-tp16-pp1-dp1')
    insert('06-超节点.md', 'C32-dense-placement',
           '[Qwen3 Dense 逐卡放置](../calculations/results/placement-qwen8-tp8-pp1-dp1.md)已枚举八卡的 TP／PP／DP 组合，逐卡列权重矩阵、层编号、Q／KV 头身份、KV、预算及消息。'
           f"额外 TP=16 对照中，只有 8 个 KV 头，物理 KV 合计为 {placement['physical_kv_bytes']/2**30:.6f} GiB，是 TP≤8 对应单副本的两倍；K/V 投影参数及工作也复制，不能把权重和状态都简单除以 16。"
           'CLI 为 `python3 calculations/calc.py dense-placement --tp 2 --pp 4 --format md`。单 rank 矩阵工作与完整逻辑前向相符；PP 保留首尾嵌入／词表头与非均匀层数，DP 复制各自请求和模型。完整工作区、嵌入归约／logits 通信、流水气泡及实测时延仍待 C32 后续计算。',
           '> **实验 6-2')
    capacity = result('capacity-qwen3-8b-n8192')
    q35_prefill = result('qwen35-prefill-8192')
    q35_decode = result('qwen35-decode-b1')
    insert('02-模型架构.md', 'Qwen35-reference',
           f"[Qwen3.5基础文本](../calculations/results/qwen35-prefill-8192.md)按固定配置与1038个checkpoint张量形状核对，45层DeltaNet、15层gated GQA与60层MoE分列；基础文本{q35_prefill['base_text_parameters']:,}参数、{q35_prefill['base_checkpoint_bytes']:,}存储bytes，视觉/MTP不并入文本前向。"
           f"8192 prefill、全部位置输出头，在声明的eager矩形attention／chunk64路径计{q35_prefill['matrix_flops']:,}矩阵FLOPs；[8192历史单步decode](../calculations/results/qwen35-decode-b1.md)为{q35_decode['matrix_flops']:,}。"
           "[65token尾块](../calculations/results/qwen35-chunk-tail-65.md)核心补到128位置；[初始单token](../calculations/results/qwen35-cold-single-token.md)普通卷积cache先pad到4，conv计算7位置后裁切，不能只计最终一个输出。"
           "[record-past初始别名](../calculations/results/qwen35-cold-single-record-past.md)无last4复制；已有记录长度未知时保留缺项。矩阵、归一化/门控算术、特殊函数、整数索引及状态分别给出；算子边界与补充语句接口有重叠，禁止相加为HBM。primitive后端、allocator及非所选分支不由此验证。"
           "运行 `python3 calculations/calc.py qwen35-forward --format md`，`--inputs`修改场景。",
           '## 2.5 条件计算与专家数据')
    request_comparison = json.loads((PROJECT / 'results/request-four-models-book.json').read_text())
    request_values = '、'.join(f"{x['model']} {x['summary']['matrix_flops']/1e12:.6f}" for x in request_comparison['comparisons'])
    insert('02-模型架构.md', 'R22-four-model-request',
           "[四模型统一请求账](../calculations/results/request-four-models-book.md)保持原实验Qwen3-8B、V4-Flash、V4-Pro和Kimi K3，统一S/P/G/B：已恢复前缀、本次输入、返回长度、batch。首输出来自输入阶段最后logits，所以后续只执行G−1次decode，最终保留S+P+G−1位置；最后返回token尚未重新送入模型。"
           f"默认S0/P128/G4/B1的全请求矩阵TFLOPs分别为{request_values}。逐阶段矩阵、已计标量/特殊操作、已知接口、状态增长和权重比较格式分别列账。"
           "[G1边界](../calculations/results/request-four-models-first-output.md)无额外decode；[125+3跨压缩边界](../calculations/results/request-four-models-prefix-boundary.md)和[6144+2048前缀](../calculations/results/request-four-models-prefix-6144-2048.md)另列V4全部顺序输入及中间head计费。Qwen/K3 decode按经核对的历史仿射贡献累计，V4逐位置枚举压缩边界。"
           "运行 `python3 calculations/calc.py request-model-comparison --format md`；K3的A_log checkpoint/config冲突保留在总汇，前缀恢复成本、真实HBM/峰值、任务质量与延迟均未推断。相同token几何不保证相同文本或质量，不能据此给硬件吞吐排名。",
           '> **实验 2-9')
    insert('10-训练系统.md', 'C55-gemm-saved-identities',
           "[训练GEMM保存身份](../calculations/results/pipeline-gemm-save-1f1b.md)逐一覆盖325个矩阵实例，将253个新增张量身份按shape、产生者、最后消费者和stage列明；QKV/gate-up共享输入、已有attention概率与GQA唯一KV均去重。每微批新增保存前三段各141,557,760B、末段143,654,912B，合入原流水寿命后重算峰值，不把两个峰值直接相加。"
           "[重算乘积](../calculations/results/pipeline-gemm-recompute-products.md)只恢复gamma*z与a*u，每stage新增长期保存降到47,185,920B；增加每微批94,896,128次标量运算及每stage6,291,456B乘积工作区。[同时SiLU重算](../calculations/results/pipeline-gemm-recompute-products-silu.md)复用已有双向量工作区，不再给同一sigmoid/a计算计第二次费用；[GPipe对照](../calculations/results/pipeline-gemm-save-gpipe.md)使用相同对象身份。"
           "运行 `python3 calculations/calc.py training-pipeline-gemm-state --format md`。完整shape和语义生命周期已列，但阶段时间仍采用F/B保守预留包络；这是FP32参考下的保存预算，不是实际BF16 autograd保存或完整allocator峰值，持久参数/全部临时量仍单独处理。",
           '> **实验 10-5')
    insert('10-训练系统.md', 'C55-training-pipeline-events',
           "[Qwen8 GPipe事件账](../calculations/results/training-pipeline-gpipe-m8.md)与[1F1B事件账](../calculations/results/training-pipeline-1f1b-m8.md)按官方36层划为四段各9层，embedding归首段、head/loss归末段，逐段复用真实训练矩阵和非矩阵工作。每个微批F/B、激活/梯度传输及全梯度就绪后的更新均列时间依赖与独立资源占用。"
           "默认M8、显式前向10ms/反向20ms/各边界传输1ms/更新1ms，GPipe为337ms、1F1B为347ms；后者减少保留状态，不保证任意服务/链路条件下更快。部分保存及收发缓冲预留峰值，GPipe约[1.929,1.929,1.929,2.566]GB，1F1B约[0.966,0.726,0.485,0.323]GB。"
           "运行 `python3 calculations/calc.py training-pipeline-schedule --format md`，`--inputs`指定策略、微批、逐段服务、方向/共享链路和保存策略；M1/4/8/16、不均衡与SiLU重算共14场景。时间是条件输入，非FLOPs自动预测或实测；保存子集加通信缓冲不是全部GEMM激活、参数状态或运行峰值。额外保存可显式按stage补充，长序列/MoE与完整运行时仍需扩展。",
           '> **实验 10-5')
    insert('03-推理与训练负载.md', 'C19-v4-overlap-state-training',
           "[V4 ratio4重叠及尾状态反向](../calculations/results/v4-overlap-tail-state-batch2.md)将前块前D与当前块后D通道组成8槽；首块前半为常量padding。返回最后完整块与尾token的KV/score状态，并接受调用者给定的状态上游梯度，合并到两投影/APE/X反向。"
           "[仅3个尾token](../calculations/results/v4-overlap-tail-only.md)没有压缩输出，仍可通过状态损失产生梯度；[首块](../calculations/results/v4-overlap-first-block.md)和[双块](../calculations/results/v4-overlap-two-blocks.md)另测padding与重叠。B2/T9矩阵前向301,989,888、反向603,979,776 FLOPs，标量前向105,220、反向246,016 FLOPs。"
           "运行 `python3 calculations/calc.py v4-compressor-overlap --format md`。参考图共享score+APE，源码为最后完整块状态重复计算的8BD加法另列；状态写入接口与训练保存不直接相加为峰值。范围仅fresh start_pos0，不推定任意恢复初态、正start_pos在线过程或量化梯度。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-compressor128-training',
           "[V4 ratio128压缩器前反向](../calculations/results/v4-compressor128-two-blocks.md)按两组FP32投影、APE、逐feature沿128 token轴softmax、加权池化、RMSNorm和RoPE逐项计算。256位置单压缩器矩阵前向2,147,483,648、反向4,294,967,296 FLOPs，标量前向788,866、反向1,907,584 FLOPs；exp、max比较与rsqrt另列。"
           "APE及gamma梯度跨batch和块归并，RoPE位置为块起点0/128。[单块](../calculations/results/v4-compressor128-one-block.md)与[batch2](../calculations/results/v4-compressor128-batch2.md)覆盖归并边界；保存X/KV/逐feature概率和RMS状态，不保留无须反向使用的score logits。"
           "运行 `python3 calculations/calc.py v4-compressor-training --format md`，tokens须为128正整数倍。范围为start_pos0完整块、非重叠主压缩器；ratio4重叠、尾块/在线状态梯度、量化cast梯度仍未实现。源码完整块不写rolling state，活跃batch状态切片不等于max_batch预分配；保存子集不等于峰值。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-attention-periphery',
           "[V4注意力外围前反向](../calculations/results/v4-attention-projections-128.md)按固定源码五组投影逐项列前向、dX和dW，另列Q/KV带权RMSNorm、逐head无权RMS、正向及逆向RoPE的伴随运算。默认128位置单外围矩阵前向27,380,416,512、反向54,760,833,024 FLOPs；标量前向16,548,096、反向26,237,440 FLOPs。"
           "这是单个ratio0、无indexer/compressor支路的去舍入参考图，不乘全部43层。[单位置](../calculations/results/v4-attention-projections-one-row.md)与[batch2](../calculations/results/v4-attention-projections-batch2.md)另给场景；core运算及它已保存的Q/KV/概率明确排除，常量频率setup不逐层重复计。"
           "运行 `python3 calculations/calc.py v4-attention-projections --format md`，用 `--inputs` 指定batch/tokens。五组共享参数跨行梯度、RMS及RoPE通过独立自动微分/有限差分验证；量化cast梯度未知，保存子集并非完整显存峰值。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-attention-training',
           "[V4共享KV稀疏attention反向](../calculations/results/v4-attention-training-window128.md)按有效槽位计QK/PV两次前向收缩与四次反向收缩，KV的key/value两路梯度合并后scatter-add；重复ID保持独立softmax项，无效槽位不参与。sink只进入分母但梯度非零，跨query/batch归并另计。"
           "默认单core128位置矩阵前向1,082,130,432、反向2,164,260,864 FLOPs；[129位置batch2](../calculations/results/v4-attention-training-window129-batch2.md)覆盖滑窗边界，[重复ID夹具](../calculations/results/v4-attention-training-duplicate-fixture.md)验证累加语义。"
           "运行 `python3 calculations/calc.py v4-attention-training --format md`。该去舍入参考图的FP32保存状态与官方BF16接口bytes分列；官方PV前转换的是未归一化指数，当前未推定cast梯度或宣称online内核逐值等价。外围投影、压缩器、indexer目标与完整训练仍需独立计算，保存子集不等于峰值，显式数据操作不等于全部HBM流量。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-training-subgraphs',
           "[V4训练可微primitive](../calculations/results/v4-training-primitives-128.md)逐项计算router的sqrt-softplus、选中分数归一化、专家门控及mHC split的前反向；默认20次迭代明确展开初始softmax与39次epsilon归一化。"
           "[mHC完整外包装反向](../calculations/results/v4-hc-training-128.md)继续计算输入、权重、base与scale梯度，合并输入的残差、pre-weight、linear和RMS四条路径；已含一次split，禁止与前一报告整项相加。"
           "每项分别列矩阵、标量、特殊操作及保存对象；保存子集不等于运行峰值。内部attention/MoE由明确的inner/VJP接口隔开，FP64自动微分与有限差分验证可微数学图，不证明量化训练内核等价。"
           "运行 `python3 calculations/calc.py v4-training-primitives --format md` 或 `python3 calculations/calc.py v4-hc-training --format md`，用 `--inputs` 指定batch/tokens。完整V4训练仍需attention、量化反向、优化器和生命周期合账。",
           '> **实验 3-6')
    real_lifecycle = json.loads((PROJECT / 'results/real-c4-lifecycle-512-128.json').read_text())
    primary_life = real_lifecycle['variants'][0]['lifecycle']
    crossing = next(r for r in primary_life['crossovers'] if r['left_N'] == 1e8 and r['right_N'] == 5e8)
    insert('03-推理与训练负载.md', 'C19-real-lifecycle',
           f"[真实拟合的条件生命周期](../calculations/results/real-c4-lifecycle-512-128.md)把目标C4 loss2.9代回主law及四项敏感性，比较0.1/0.5/1/2.81B候选的训练6ND与请求2N[P+G−1]代理。P512/G128只有127次额外decode，统一声明1e-18抽象cost-unit/FLOP，不是硬件价格或完整算子账。0.1B/0.5B成本线约{crossing['calls']/1e8:.4f}亿调用交叉，但0.1B所需D约298.6B，超过拟合D上界3.28倍，不能直接用作部署建议。"
           "逐候选外推范围、交叉两侧与有限候选最小值均列出；同损失不等于同任务质量，主fit不按holdout表现或费用重选。运行 `python3 calculations/calc.py real-scaling-lifecycle --format md`；配图运行 `python3 calculations/calc.py plot-real-scaling`，图与两份结果SHA绑定。"
           "[真实点与生命周期图](../calculations/figures/real-scaling/figure.svg)同时区分fit/holdout点和超出拟合框的虚线候选。",
           '> **实验 3-8')
    real_scaling = json.loads((PROJECT / 'results/datablations-real-c4-eight-point-fit.json').read_text())
    real_fit = real_scaling['primary']['result']
    insert('03-推理与训练负载.md', 'C19-real-c4-fit',
           f"[真实C4公开训练点拟合](../calculations/results/datablations-real-c4-eight-point-fit.md)从作者notebook和匹配最终日志提取8点，6点拟合、2点按事前N≥2e9留出；不执行notebook代码，不把模型名称直接当精确参数/已实现token预算。有限网格主拟合alpha={real_fit['law']['alpha']:.2f}、beta={real_fit['law']['beta']:.2f}，训练SSE={real_fit['fit_sse']:.8f}、留出RMSE={real_fit['holdout_rmse']:.8f}nats/token。"
           "官方日志支持同C4验证总体与GPT2 BPE；不同样本预算可作带噪估计，但不假定独立误差或相同子样本。明确预算冲突的146m点排除，旧33行来源审查与原严格门槛保留归档。作者N估计/shape估计、可用脚本D与扩展指数网格四项敏感性分别呈现，不按留出表现更换主拟合。"
           "运行 `python3 calculations/calc.py real-scaling-fit --format md`。边界非负诊断另列零系数和指数不识别，坏数值网格点分类而非中断搜索；有限点拟合不是论文全部实验复现，置信区间、同任务质量及完整硬件费用不由此获得。",
           '> **实验 3-8')
    train_nonmatrix = result('training-nonmatrix-book')
    insert('03-推理与训练负载.md', 'C21-training-nonmatrix',
           f"[Qwen8训练非矩阵补账](../calculations/results/training-nonmatrix-book.md)保留原矩阵账，B1/T128时原训练矩阵{train_nonmatrix['original_training_matrix_flops']:,}FLOPs，新增前向普通算术{train_nonmatrix['forward_scalar_flops']:,}、反向{train_nonmatrix['backward_scalar_flops']:,}及声明AdamW更新{train_nonmatrix['optimizer_scalar_flops']:,}FLOPs；sqrt/exp/sigmoid等特殊操作、cast和bytes分列。"
           "RMSNorm、SwiGLU、因果softmax/缩放、mean CE、RoPE、残差与GQA梯度合并逐项给公式；[dense标签mask](../calculations/results/training-nonmatrix-dense-mask.md)不省主干矩阵，[compact词表头](../calculations/results/training-nonmatrix-compact-mask.md)另计hidden gather/scatter及完整梯度清零。"
           "[局部SwiGLU重算](../calculations/results/training-nonmatrix-recompute-silu.md)明确保存/释放对象及新增sigmoid/乘法，不称整层checkpoint；[8192序列](../calculations/results/training-nonmatrix-8192.md)显示因果概率保存的增长。FP64梯度对照与独立运算计数核验通过。"
           "运行 `python3 calculations/calc.py training-nonmatrix --format md`。这是声明数学反向与未融合AdamW口径，保存对象只是非线性子集合；V4训练、完整activation/allocator峰值、HBM及实际后端仍另需核算。",
           '> **实验 3-6')
    strategy_cost = result('strategy-record-cost-03-03')
    insert('03-推理与训练负载.md', 'C18-strict-strategy-cost',
           f"[原实验严格协议全候选账](../calculations/results/strategy-record-cost-03-03.md)封存三批{strategy_cost['attempts']}个候选、{strategy_cost['groups']}任务组，重新核对原JSON解析/有效多数与最早平票选择，独立DP复算真值；严格成功数为{strategy_cost['successes']}，所以每成功任务消耗保持null。"
           "88个候选长度截断，失败输出与验证/选择消耗全部保留；thinking1024、thinking4096与no-thinking4096分批呈现，不用后验抽取替换评分。并行请求耗时之和不等于组墙钟或GPU核时，验证/选择已包含在组墙钟内，不再次加总。"
           "运行 `python3 calculations/calc.py strategy-record-cost --format md` 复现逐候选、逐组和策略汇总。返回ID不自动换算有用答案或decode次数，实际KV/费用/GPU时间未知保留；当前数据不能给出达到相同质量要求后的成本排序。",
           '> **实验 3-3')
    profile_result = json.loads((PROJECT / 'results/workload-profiles-02-08.json').read_text())
    insert('02-模型架构.md', 'C14-recorded-p95',
           f"[封存请求画像p95](../calculations/results/workload-profiles-02-08.md)对已有{profile_result['summary']['requests']}条请求、{profile_result['summary']['groups']}组记录补齐输入/返回输出/缓存长度、模型/工具时间和复用间隔的经验分位数，不发起新请求。"
           "p95采用排序后第ceil(0.95n)项；n≤19时即最大值，缺失工具/首请求间隔保持null而非零。Chat采集、Agent thinking关闭/开启的输入p95分别252/3136/1992tokens，返回输出ID的p95分别29/125/1200。"
           "这些值描述固定记录，返回ID可能含EOS，不将其直接当成有用答案长度或decode调用数；记录时长也不是跨组硬件性能预测。运行 `python3 calculations/calc.py workload-profiles --format md`；逐请求长度到模型资源的代入仍单独核算。",
           '> **实验 2-8')
    variants = json.loads((PROJECT / 'results/architecture-decode.json').read_text())
    original, reduced = variants['variants'][0], variants['variants'][-1]
    insert('02-模型架构.md', 'C13-architecture-variants',
           f"[声明架构变体](../calculations/results/architecture-decode.md)保留官方Qwen3-8B基线；默认把KV头8→2、FFN宽12288→12800后，参数仍为{reduced['actual_parameters']:,}，单步矩阵工作仍为{reduced['work']['matrix_flops']:,}FLOPs，KV却由{original['work']['kv_bytes_per_token_per_request']:,}降至{reduced['work']['kv_bytes_per_token_per_request']:,}bytes/token。"
           "变深/变浅与变宽/变窄按FFN对齐给真实参数差额及误差界；严格等参看实际标志，不能仅看名称。每步矩阵、norm复制、TP完整头、KV、串行层数及两类decoder collective分别列账；容量翻转区间含端点。"
           "[8192 prefill](../calculations/results/architecture-prefill.md)、[6144+2048](../calculations/results/architecture-prefix.md)和[单设备](../calculations/results/architecture-single-device.md)使用同一变体契约。运行 `python3 calculations/calc.py architecture-variants --format md`；只有基线为真实checkpoint，其余未训练，不推断等质量或完整请求速度。",
           '> **实验 2-7')
    fish_export = result('fish-wave-two-chunks')
    insert('12-端边云协同.md', 'C78-fish-wave-export',
           f"[Fish固定CLI的代码帧到波形](../calculations/results/fish-wave-two-chunks.md)先积累21+22个实际代码帧，收到next再合并并调用一次codec，产生{fish_export['output_samples']:,}个44100Hz样本；sample事件只有代码，没有逐块波形。前向码本/codec工作复用已有账，不再次加到AR或codec总量。"
           f"int64代码因conversation与保存输入两次CPU复制，共{fish_export['code_device_to_host_bytes']:,}bytes；BF16波形在此CLI先.cpu()后.float()，D2H为{fish_export['waveform_device_to_host_bytes']:,}bytes，standalone DAC CLI顺序相反则为{fish_export['standalone_dac_cli_wave_device_to_host_bytes']:,}bytes。"
           "[int32代码](../calculations/results/fish-wave-int32.md)和[FP32波形](../calculations/results/fish-wave-fp32.md)另列。输入帧数须来自实际成功返回的无条件末列裁切结果；被裁末列未必是终止符，文本chunk长度和生成预算均不能直接当音频帧数。"
           "运行 `python3 calculations/calc.py fish-wave-export --format md`。首波形依赖全部代码块与单次codec；CPU cast/NumPy别名、局部持有对象分列，TTFA/RTF、文件编码字节与完整runtime峰值无测量仍未知。",
           '> **实验 12-1')
    vae = result('flux-vae-1024-bf16-sdpa')
    vae_eager = result('flux-vae-1024-bf16-eager')
    insert('12-端边云协同.md', 'C79-flux-vae-lifetime',
           f"[FLUX VAE解码器逐步账](../calculations/results/flux-vae-1024-bf16-sdpa.md)从已反归一化的32×128×128 latent生成1024² RGB，包含{vae['decoder_weight_parameters']:,}参数、卷积bias和GN affine；dense矩阵/卷积{vae['dense_matrix_and_conv_flops']:,}FLOPs，有效非padding为{vae['nonpadding_matrix_and_conv_flops']:,}，bias/归一化/激活另列。"
           f"SDPA命名张量边界峰值{vae['declared_tensor_boundary_peak_bytes']:,}bytes；[eager路径](../calculations/results/flux-vae-1024-bf16-eager.md)显式score/softmax临时量使该峰值为{vae_eager['declared_tensor_boundary_peak_bytes']:,}bytes。逐源码持有/释放事件可重算，均非真实allocator峰值或HBM流量。"
           "大输入触发contiguous时复制bytes未知，完整条件预算保留null。此结果细化已有image-generation VAE阶段，禁止再次加到原矩阵总量；latent解包/BN反变换、后处理及图像文件编码仍归各自阶段。运行 `python3 calculations/calc.py flux-vae-decode --format md`，`--inputs`指定尺寸/精度/attention/workspace。",
           '> **实验 12-1')
    v4_prefix = result('v4-prefix-flash-6144-2048')
    insert('02-模型架构.md', 'C10-v4-sequential-prefix',
           f"[V4固定源码的缓存后缀续算](../calculations/results/v4-prefix-flash-6144-2048.md)要求6144位置的完整window/压缩/index/FP32 compressor状态已恢复，随后逐个输入2048个已知token。基础forward和词表头均调用{v4_prefix['forward_calls']}次，即使中间logits被丢弃仍计费；总有效矩阵{v4_prefix['matrix_flops_effective_attention']:,}FLOPs，替换已知sparse/expert tile口径为{v4_prefix['matrix_flops_with_reference_sparse_and_expert_tiles']:,}，两者是替代口径。"
           f"ratio4/128分别完成512/16次，逐步列表保留共同边界与写入。有效状态{v4_prefix['initial_state_resident_bytes']:,}→{v4_prefix['final_state_resident_bytes']:,}bytes，增长不等于累计写入；完整HBM和实际peak仍未知。"
           "[Pro跨128边界](../calculations/results/v4-prefix-pro-boundary.md)和[批量边界](../calculations/results/v4-prefix-flash-batch-boundary.md)另有对照。源码默认max_seq_len4096不足，本题显式分配8192/1并单列cache容量；前缀查找/传输/恢复未被假定免费完成。"
           "运行 `python3 calculations/calc.py v4-prefix-continuation --format md`；固定增量分支写单槽，此调度不是并行chunk prefill。",
           '> **实验 2-4')
    dense_lowbit = json.loads((PROJECT / 'results/dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-8192.json').read_text())
    dense_limits = '/'.join(str(row['maximum_global_requests']) for row in dense_lowbit['summary'])
    insert('02-模型架构.md', 'C13-dense-local-quantization',
           f"[三款Dense模型的分片后量化容量](../calculations/results/dense-quant-deepseek-r1-distill-llama-70b-tp8-pp1-24gb-8192.md)复用真实逐rank BF16权重形状，按local K逐行打包4/8bit payload与分组scale；embedding/head/norm保持BF16，KV也保持BF16。70B在TP8、每卡24 decimal GB、8192个保留位置及2 GiB工作区下，BF16/8bit/4bit的条件并发为{dense_limits}。"
           "同条件[Qwen3-8B](../calculations/results/dense-quant-qwen3-8b-tp8-pp1-24gb-8192.md)为131/136/139，[Qwen3-32B](../calculations/results/dense-quant-qwen3-32b-tp8-pp1-24gb-8192.md)为50/65/72；54场景还覆盖TP2×PP4、PP8、48/80GB与32K。先在每个DP副本内取最差rank，再跨独立副本求和，不能用全卡剩余bytes抵消某卡超限。"
           "分组尾部以分片后的实际K计算：K1536、group1000每行仍需两个scale。TP16完整KV头复制与非均匀PP容量±1byte另有回归。运行 `python3 calculations/calc.py dense-quantized-placement --format md`，`--inputs`指定模型、组织和容量。"
           "这些是声明低位格式与固定工作区的容量结果，未推导真实量化checkpoint、执行kernel、batch相关工作区或性能。",
           '> **实验 2-7')
    placement235 = json.loads((PROJECT / 'results/qwen235-placement-tp2-ep4-pp1-80gb-8192.json').read_text())
    insert('02-模型架构.md', 'C13-qwen235-placement',
           f"[Qwen3-235B八卡逐rank容量](../calculations/results/qwen235-placement-tp2-ep4-pp1-80gb-8192.md)按官方索引{placement235['evidence']['index_tensor_count']:,}个权重名核对{placement235['evidence']['unique_parameters']:,}参数；矩阵形状由固定config与实现推导，索引本身不提供逐张量形状。"
           "TP2×EP4的attention与KV在EP内复制，128个专家全部驻留；每rank先分片矩阵，再按local K做8/4bit逐行打包和分组scale，embedding/head/router/norm保持BF16。每卡80 decimal GB、显式2 GiB工作区、8192位置BF16 KV下，BF16/8bit/4bit条件并发分别16/56/76。"
           "[24GB对照](../calculations/results/qwen235-placement-tp2-ep4-pp1-24gb-8192.md)分别0/0/5；[PP8非均匀层](../calculations/results/qwen235-placement-tp1-ep1-pp8-80gb-32768.md)按94层与首尾词表分别核最差rank。24场景覆盖四种八卡组织、24/48/80GB及8K/32K，每场景含三格式。"
           "运行 `python3 calculations/calc.py qwen235-placement --format md`。低位格式是声明的容量模型，实际量化checkpoint、通信执行和真实workspace峰值另需验证；EP不作为独立请求副本乘并发。",
           '> **实验 2-7')
    llama_prefill = result('llama70-prefill-8192')
    llama_decode = result('llama70-decode-8192')
    insert('02-模型架构.md', 'F02-llama70-forward',
           f"[公开70B代表](../calculations/results/llama70-prefill-8192.md)采用DeepSeek原发布者的R1-Distill-Llama-70B，固定config与723个索引权重名对照得到{llama_prefill['parameters']:,}参数；未将原Meta仓库401记录改名或替换为名义70e9。"
           f"B=1、8192-token prefill、仅最后位置输出头时，矩阵工作{llama_prefill['matrix_flops']/1e12:.6f} TFLOPs；[已有8192历史再decode一步](../calculations/results/llama70-decode-8192.md)为{llama_decode['matrix_flops']/1e9:.6f} GFLOPs，默认每请求每历史token的KV为{llama_decode['kv_bytes_per_token_per_request']:,} bytes。"
           "80层Llama没有Qwen3的Q/K Norm；每层矩阵、RMSNorm、RoPE、softmax、SwiGLU及残差分别列账。缩放RoPE初始化与每次forward分开，默认位置表在批内和层间共享。"
           "运行 `python3 calculations/calc.py forward --model deepseek-r1-distill-llama-70b --tokens 8192 --format md` 复现；CSV展开逐层算子。这里是逻辑算子与操作数载荷，非实际HBM、完整运行延迟或量化checkpoint验证；单设备容量已另行接入，BF16逐卡放置已另接入，真实工作区与完整通信图仍待专门计算。",
           '> **实验 2-7')
    llama_capacity = result('llama70-capacity-8k')
    llama_tp8 = result('llama70-placement-tp8')
    llama_dp2 = result('llama70-placement-tp4-dp2')
    llama_tp16 = result('llama70-placement-tp16-kv-replica')
    insert('02-模型架构.md', 'C13-llama70-placement',
           f"[70B逐卡BF16放置](../calculations/results/llama70-placement-tp8.md)以8192历史加1新增位置、每卡2 GiB工作区逐rank计权重/KV；TP8的最大驻留为{llama_tp8['maximum_card_resident_bytes']:,}bytes，在每卡24 decimal GB预算内。"
           f"同样八卡改为[TP4×DP2](../calculations/results/llama70-placement-tp4-dp2.md)，两完整模型副本使最大rank达到{llama_dp2['maximum_card_resident_bytes']:,}bytes，不能用八卡总容量证明可行。"
           "[TP4×PP2](../calculations/results/llama70-placement-tp4-pp2.md)、[TP2×PP4](../calculations/results/llama70-placement-tp2-pp4.md)和[PP8](../calculations/results/llama70-placement-pp8.md)分别核首尾词表矩阵、norm复制及非均匀驻留。"
           f"[TP16反例](../calculations/results/llama70-placement-tp16-kv-replica.md)必须复制完整KV头，物理KV为{llama_tp16['physical_kv_bytes']:,}bytes、矩阵工作{llama_tp16['physical_matrix_flops']:,}FLOPs，不能继续把8个KV头平均切成16份。"
           "运行 `python3 calculations/calc.py dense-placement --model deepseek-r1-distill-llama-70b --tp 8 --format md`。消息字段是声明TP/PP接口payload，非拓扑链路流量；量化重分组、完整通信图、真实工作区/时延仍须另算。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-llama70-capacity',
           f"[真实70B单设备容量](../calculations/results/llama70-capacity-8k.md)按{llama_capacity['logical_parameters']:,}参数逐矩阵计量，BF16权重{llama_capacity['bf16_weight_bytes']:,}bytes；group128/每组2-byte scale的4-bit教学方案为{llama_capacity['four_bit_scheme_bytes']:,}bytes，保留embedding、输出头和norm为BF16。每请求8192位置BF16 KV为{llama_capacity['bf16_kv_bytes_per_request']:,}bytes。"
           "80 decimal GB预算、2 GiB固定工作区时，8-bit方案仅容1请求、4-bit方案容14请求；[32K历史](../calculations/results/llama70-capacity-32k.md)下4-bit方案为3请求。"
           "[group1000尾组](../calculations/results/llama70-capacity-tail-group.md)逐行向上取整；[精确容量阈值](../calculations/results/llama70-capacity-boundary.md)用49,700,945,920bytes前后各1byte检验2→3请求。"
           "运行 `python3 calculations/calc.py capacity-scan --model deepseek-r1-distill-llama-70b --format md`。这些是声明存储与工作区下的单设备容量，不是已验证量化checkpoint、部署吞吐或八卡分片结论。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-single-device-capacity',
           f"[实际形状容量扫描](../calculations/results/capacity-qwen3-8b-n8192.md)从 Qwen3-8B 的 {capacity['logical_parameters']:,} 个真实参数出发，BF16 权重为 {capacity['bf16_weight_bytes']/2**30:.6f} GiB；在声明的分组低位宽方案中逐行计打包尾部和 scale，嵌入／输出头／路由器／norm 保留 BF16。"
           '运行 `python3 calculations/calc.py capacity-scan --model qwen3-32b --format md`。Qwen3-8B／32B／235B 在 8K／32K 历史、24／48／80 GB 单设备预算下的并发表已输出；工作区默认保留 2 GiB，最大并发只对该预算成立。MoE 保存全部专家，不按激活参数算权重；低位宽不是已验证的量化 checkpoint，公开70B输入及前向已另行接入，70B单设备容量已接入，BF16八卡Llama放置已接入，低位分组重切及实际工作区仍待专门计算。',
           '> **实验 2-7')
    dedup = result('moe-dedup-qwen235-clustered')
    insert('06-超节点.md', 'C33-C34-destination-dedup',
           f"[显式 token 路由去重](../calculations/results/moe-dedup-qwen235-clustered.md)在 8 rank、每源 64 token 的 clustered 场景，将 dispatch 从 {dedup['per_assignment_dispatch_bytes']:,} bytes 降到 {dedup['deduplicated_dispatch_bytes']:,} bytes；同样的 assignment 直方图若由 spread 路由产生，则没有此收益。"
           '运行 `python3 calculations/calc.py moe-dedup --pattern spread --format md` 比较。目的端对已加权专家输出形成部分和，再返回源端归约；加法总数守恒，仅位置改变，专家 GEMM 行数不减少。输入按 BF16，返回元素默认四字节且两种方案一致；元数据、概率传输、打包和浮点重结合影响仍需后端证据，不把载荷缩减称为实际加速。',
           '> **图 6-4')
    staging = result('staging-local-grouped')
    insert('06-超节点.md', 'C34-C35-numa-paths',
           '[PCIe／NUMA 路径复算](../calculations/results/staging-local-grouped.md)复用四卡 ring 的 8 MiB Qwen 激活，48 MiB 逻辑发送保持不变。缓冲全放 A 时 DRAM 为 96／0 MiB，CPU 间每方向 24 MiB；靠近发送端后为 48／48 MiB、每方向 12 MiB；交错 ring 又使每方向回到 24 MiB。'
           f"在声明的教学带宽下，发送端就近缓冲与分组 ring 的聚合资源下界为 {staging['aggregate_resource_lower_seconds']*1000:.6f} ms。"
           'CLI 为 `python3 calculations/calc.py numa-staging --placement sender-local --format md`。逐资源及逐轮累加共用 traffic 模块，DRAM 写／读计两次，CPU 间方向分开；共享资源先合并载荷，聚合 max 与逐轮 max 之和分别报告。驻留缓冲、host bridge、协议及实际可达性能仍未知。',
           '> **图 6-6')
    exchange = result('all-to-all-qwen235-t64-balanced')
    insert('06-超节点.md', 'C34-all-to-all',
           f"[Qwen3-235B MoE all-to-all 复算](../calculations/results/all-to-all-qwen235-t64-balanced.md)固定 8 个专家 rank、每源 64 token，按官方 top-k 与隐藏宽度逐 assignment 发送 BF16 向量，均匀分派的 dispatch 全网发送 {exchange['dispatch_network_send_bytes']:,} bytes。"
           '对照全部专家选择集中到 rank 0 的合法热点场景，网络总量相同，但最忙 rank 接收量变为 8 倍；pairwise 轮次逐步等待最大边载荷，不能用全网平均值代替。CLI 为 `python3 calculations/calc.py all-to-all --routing hotspot --format md`。本地分派不进网络，combine 转置流量矩阵；尚未做目的端 token 去重、元数据与物理拓扑／争用计算。',
           '> **图 6-4')
    tree = result('tree-qwen3-8b-t1-p8')
    insert('06-超节点.md', 'C34-tree',
           f"[同输入 binomial tree 复算](../calculations/results/tree-qwen3-8b-t1-p8.md)采用未分段归约加反向广播，8 rank 共 6 轮；单 token 消息在相同教学链路条件下为 {tree['all_reduce_modeled_seconds']*1e6:.6f} μs。"
           '每条边传完整张量，网络总发送与 ring 同为 2(p−1)M，但各 rank 负载不均，关键路径也不同；8192-token 大消息下本例 ring 反而更快。CLI 为 `python3 calculations/calc.py tree-collective --format md`；非二次幂 rank 也通过整数回放。此算法不是 NCCL 双树或分段实现，不能将结果推广为所有树算法的性能结论。',
           '> **图 6-4')
    ring = result('ring-qwen3-8b-t1-p8')
    insert('06-超节点.md', 'C34-ring',
           f"[Qwen3-8B ring 逐轮复算](../calculations/results/ring-qwen3-8b-t1-p8.md)从 BF16 [1,4096] 的 8192-byte 消息得到 8 rank、14 轮、每 rank 发送 {ring['all_reduce_send_bytes_per_rank']} bytes。在每轮 2 μs、单向有效 50 GB/s 的教学条件下，72 次串行归约合计 {ring['dense_tp_serial_collective_seconds']*1000:.6f} ms。"
           'CLI 为 `python3 calculations/calc.py ring-collective --format md`，逐轮列发送／接收者与分片；reduce-scatter 的输入 M 和 all-gather 的输入 M/p 分开。整数数值回放验证各 rank 最终持有正确归约结果；网络载荷只累加发送一次，不能把接收端重复加为物理流量。树与 all-to-all 的独立子账见本节后续回填；拓扑跳数、归约执行与争用仍属 C34 待办。',
           '> **图 6-4')
    budget = result('decode-budget-base')
    insert('01-初识 AI Infra.md', 'C02-decode-budget',
           f"[70B 教学预算复算](../calculations/results/decode-budget-base.md)在每参数 1 byte、每 batch 读取一次权重的假设下，官方 H100 SXM 带宽给出 {budget['memory_service_seconds']*1000:.6f} ms 权重服务下界。计算采用 2NB 近似与 BF16／FP32 累加／dense 峰值；存储位宽不改变所选计算精度，反量化、非矩阵和额外工作区仍需单算。"
           '运行 `python3 calculations/calc.py decode-budget --format md`。8 个场景分别改变算力、带宽、位宽、batch 和显式 KV／工作区预算；容量不满足时完整资源下界与吞吐留空。理想批复用的交叉点同时检查 KV 是否使其不存在或容量不可达；对照分母翻倍是资源假设，不是另一个设备 SKU。',
           '> **实验 1-3')
    window = result('window-qwen3-8b-n128')
    insert('01-初识 AI Infra.md', 'C03-memory-concurrency',
           f"[访存并发复算](../calculations/results/window-qwen3-8b-n128.md)用官方 Qwen3-8B 的 1.125 GiB KV 载荷，代入教学事务 128 bytes、工作点延迟 500 ns、接口 1 TB/s，需至少 {window['required_transactions']} 个独立事务才可能供满接口；N=128 时吞吐上界 32.768 GB/s、服务下界 36.864 ms。"
           '运行 `python3 calculations/calc.py memory-concurrency --transactions 4096 --format md` 复现。四个原始算例已统一生成，分别改变并发、接口带宽和负载延迟。N 不等于 batch、线程或 SM 数；增加 batch 只增加本例载荷，不自动增加在途窗口。结果是条件式资源下界，不含完整 decode 和硬件可达性证明。',
           '> **实验 1-4')
    basics = result('basics-70b-bf16-balanced')
    insert('01-初识 AI Infra.md', 'C01-units-capacity',
           f"[单位与逐卡容量计算](../calculations/results/basics-70b-bf16-balanced.md)将教学 70B 明确为 70×10⁹ 个参数：16-bit 权重为 140 GB，即 {basics['weight_payload_GiB']:.6f} GiB；8-bit 为 70 GB。400 Gb/s 单向原始速率为 50 GB/s，不能当作 400 GB/s 或额外翻倍。"
           'CLI 为 `python3 calculations/calc.py resource-basics --format md`。两张各 80 GB 的教学卡在均分纯权重时每卡 70 GB；若全部权重放在第一张，总容量虽然足够，逐卡仍失败。元数据、状态和工作区是显式每卡预算，默认零表示本例排除而非部署时不存在；4-bit 按每卡向上取整。小消息／大块载荷分别输出启动项与带宽项，不将名义链路服务时间称作实测。',
           '> **实验 1-2')
    insert("11-资源调度与运行环境.md", "C62-environment-lifecycle",
           "[创建/克隆/预热预算](../calculations/results/environment-lifecycle-default.md)由 `python3 calculations/calc.py environment-lifecycle --format md` 复现。教学条件为2GiB模板、100环境、每环境512MiB触及/128MiB脏页/256MiB热只读页和4MiB私有开销；四种放置的本地占用分别200.390625/50.390625/12.890625/37.890625GiB。共享基线加独立快照增量为14.5GiB，实际平台格式支持未证实。准备2秒、提前1秒、命中率3/4时，期望调用等待1.25秒，相对按需创建额外驻留2GiB·秒。暖模板仍有每环境安装工作；12次本地进程记录独立呈现，不冒充E2B的API/恢复/首工具实测。",
           "> **实验 11-2")
    ub = json.loads((PROJECT / 'results/ub-scope-qwen32-default.json').read_text())
    one,two = ub['scope_candidates']
    insert('01-初识 AI Infra.md', 'C05-modern-scope',
           '[当代Qwen教学计算](../calculations/results/ub-scope-qwen32-default.md)用同一Qwen3-32B、8卡与32次decode前向比较单机TP8和双机TP4×PP2。'
           f"末步KV为{one['summary']['final_cache_positions']}位置，最大逐卡预算占用分别{one['summary']['maximum_card_resident_bytes']}与{two['summary']['maximum_card_resident_bytes']}bytes，工作区为显式预留。"
           '教学本地50GB/s、2μs启动，跨机25GB/s、5μs启动；双机每次跨机发送4份hidden加token反馈，共40964bytes、2次启动。'
           '声明串行通信预算分别3.68886936和1.61838368ms/前向；不是端到端耗时。'
           '[带宽相等边界](../calculations/results/ub-scope-remote-tie.md)约19.769MB/s；[双机刚好可放](../calculations/results/ub-scope-capacity-dual-only.md)仍须先排除容量失败的单机候选。'
           '运行 `python3 calculations/calc.py ub-scope --format md` 复现。Qwen配置与服务条件是当代教学输入，不属于UB创立时已知事实；作者回忆仅支撑早于2020转折的时间线，原C05的当年容量/交接/选择翻转仍需历史输入，保持未完成。',
           '### 1.6.2 需求转折与未确定的未来')
    insert("03-推理与训练负载.md", "C20-training-history",
           "[公开训练投入复算](../calculations/results/training-history-published.md)锁定13行模型及16份官方归档，逐行保留token范围、报告总/激活参数与6ND代理。Llama1 65B的1,022,362 GPU小时在恒定2048卡假设下为20.800008天；DeepSeekV3预训练2.664M加上下文119K和后训练5K为2.788M GPU小时，14.8T仅配预训练。Qwen3表21的17,920/1,800小时是替代后训练分支，不相加为预训练投入。Llama405的30.84M小时与最大16,384卡来自不同来源范围，78.430176天下界附加同scope条件，实际日期未知；论文表4的43%/41%/38% MFU按三种阶段配置独立呈现。运行 `python3 calculations/calc.py training-history --format md`；[卡数区间](../calculations/results/training-history-count-range.md)和[声明生命周期费用](../calculations/results/training-history-declared-cost.md)保留缺失输入，不将不同硬件GPU小时或未对齐质量的费用排成效率榜。",
           "> **实验 3-9")
    insert("03-推理与训练负载.md", "C19-scaling-law",
           "[受控教学拟合](../calculations/results/scaling-law-teaching.md)使用9个合成训练点和3个独立留出点，在声明的指数网格上拟合损失模型；留出集不参与选择。固定训练预算求连续N/D最优，并枚举相同预测验证损失下的训练加生命周期服务费用。默认教学需求为3.65亿次调用，候选最优从[零需求的8B](../calculations/results/scaling-law-zero-demand.md)变为4B；这里的费用率是声明单位/FLOP，非价格或实际服务吞吐。运行 `python3 calculations/calc.py scaling-law --format md`。Kaplan/Chinchilla分配指数仅作同一教学锚点的假设对照；作者公开C4点的拟合、留出验证及图3-7已由下述真实点与生命周期计算交付；验证损失到下游任务质量尚未校准，不以合成拟合或同损失比较宣称真实部署最优。",
           "> **实验 3-8")
    hardware_recording = result("hardware-audit")
    projection_small = result("projection-qwen3-8b-rtx4090-b1")
    projection_batch = result("projection-qwen3-8b-rtx4090-b256")
    insert("04-加速器架构.md", "H01-H06",
           "[官方硬件基础表](../calculations/results/hardware.md)已分开输入精度、累加精度、执行单元与 dense／structured sparsity。以官方白皮书为例，4090 的 dense FP16 Tensor 峰值在 FP16 累加时为 330.3 TFLOPs/s、FP32 累加时为 165.2 TFLOPs/s；BF16＋FP32 累加采用后者。"
           "RTX PRO 6000 Blackwell Workstation 的同口径 BF16＋FP32 为 503.8 TFLOPs/s。Roofline CLI 拒绝用整数 TOPS、未知累加／稀疏条件或另一产品的峰值替代；Apple 未公开的 GPU FLOPs 保持未知。当前约定的代际／型号与官方规格差异审查已按[硬件清单](../calculations/PLAN.md)验收；未披露字段和来源版本边界继续显式保留，新增官方证据再更新受影响记录。",
           "> **实验 4-5")
    insert("04-加速器架构.md", "H06-projection",
           f"[硬件来源审查](../calculations/HARDWARE-AUDIT.md)当前收录{hardware_recording['devices']}个配置、{hardware_recording['peak_records']}条峰值记录，分别保存H100的SXM／PCIe／NVL、H200两种形态、GB系统范围、RTX PRO三种版本及Apple M1至最新M6的选定配置。"
           f"[Qwen3-8B真实Q投影](../calculations/results/projection-qwen3-8b-rtx4090-b256.md)按BF16输入／输出、FP32累加、dense、冷内存各读写一次，在B=1与256时AI分别为{projection_small['arithmetic_intensity_flops_per_byte']:.6f}与{projection_batch['arithmetic_intensity_flops_per_byte']:.6f} FLOPs/byte；"
           f"4090上对应资源下界为{projection_small['roofline_lower_bound_seconds']*1e6:.6f}与{projection_batch['roofline_lower_bound_seconds']*1e6:.6f}μs，主导约束由内存转到计算。"
           "运行 `python3 calculations/calc.py projection-bound --device rtx4090 --batch 256` 复现；这是单层GEMM的条件式下界。Apple或昇腾缺少精度证据的场景只给内存服务时间，完整Roofline留空；全模型放置、真实HBM与持续性能另算。",
           "> **实验 4-5")
    insert("04-加速器架构.md", "H05-field-audit",
           "[逐字段登记审查](../calculations/results/hardware-audit.md)由 `python3 calculations/calc.py hardware --audit --format md` 复现。缺值、缺字段来源与峰值不符合计算口径分别呈现，不从空值推断设备不支持。功率区分TDP/TGP、配置上限和达到规格算力时的芯片功耗；互联保留方向与拓扑，不把双向合计当单向有效带宽。Mac的GPU档位和内存按官方允许组合列出，已公布但未来供应的配置明确记录日期；来源冲突及尚未查完的型号仍按硬件清单保留。累加寄存器／结果类型还须与内部累加有效精度分开：官方PTX对部分Hopper FP8 wgmma指令明确给出低于完整单精度的内部累加限制，不能仅凭FP32类型或相同峰值认定数值等价；逐行证据保留具体适用范围。",
           "> **实验 4-5")
    training = result('training-qwen3-8b-t8192')
    compact = result('training-qwen3-8b-compact-half')
    insert('03-推理与训练负载.md', 'C18-dense-training-matrix',
           f"[Qwen3-8B 训练矩阵子账](../calculations/results/training-qwen3-8b-t8192.md)在 B=1、T=8192 下，前向加两个梯度共 {training['training_matrix_flops']/1e12:.6f} TFLOPs，其中有效因果注意力为 {training['attention_training_matrix_flops']/1e12:.6f} TFLOPs；按全部参数计算的 6ND 为 {training['six_nd_flops']/1e12:.6f} TFLOPs。"
           f"[监督标签减半](../calculations/results/training-qwen3-8b-mask-half.md)不会自动减少 dense 输出头工作；[显式筛选输出头行](../calculations/results/training-qwen3-8b-compact-half.md)后矩阵工作才降至 {compact['training_matrix_flops']/1e12:.6f} TFLOPs，主干仍按完整输入执行。"
           '运行 `python3 calculations/calc.py training-matrix --supervised-tokens 4096 --head-strategy compact --format md` 复现。参数状态按 BF16 权重、FP32 梯度／master／Adam 双 moment 的声明方案分项计量，尚未包含激活、重计算、非矩阵反向、优化器更新和通信，不能称完整训练投入；[Qwen235B 专家训练矩阵](../calculations/results/training-qwen3-235b-balanced.md)已按每专家 token 数展开，均匀／集中路由对照保留；V4、K3 训练反向与 RL 分账继续待办。',
           '> **实验 3-6')
    rl = result('rl-qwen8-base')
    insert('03-推理与训练负载.md', 'C18-rl-cycle',
           f"[Qwen 教学 RL 批次](../calculations/results/rl-qwen8-base.md)以 8 个 prompt、每个 4 个候选、P=1024／G=256、最终接受 16 个样本为输入：rollout 矩阵工作 {rl['rollout_matrix_flops']/1e12:.6f} TFLOPs，加入一次 reference 评分和一次策略更新后共 {rl['cycle_matrix_flops']/1e12:.6f} TFLOPs。"
           'prefill 已产生首个输出，后续仅 G−1 次 decode；训练输入长度为 P+G−1，监督标签为 G 个输出。拒收样本仍计生成／评分，更新仅计接受样本；[降低接受率但保持有效样本数](../calculations/results/rl-qwen8-low-acceptance.md)单独比较浪费的候选工作。'
           '运行 `python3 calculations/calc.py rl-cycle --teacher-passes 1 --update-epochs 2 --format md` 复现分阶段矩阵与 BF16 权重交接。reference／teacher 明确假设使用同一模型配置的独立快照；规则验证、损失算术、优化器、通信时延和真实阶段供给未知，不能据此声称 V4 系统复现或推断增配方案。',
           '> **实验 3-7')
    supply = result('rl-supply-base')
    insert('03-推理与训练负载.md', 'C18-rl-supply',
           f"[RL 显式资源供给算例](../calculations/results/rl-supply-base.md)把矩阵有效速率、验证服务槽和权重传输带宽作为教学输入：同一 16 个接受样本批次的所列串行组件时间为 {supply['serial_component_batch_seconds']:.6f} s，独立池理想多批流水间隔下界为 {supply['ideal_pipeline_interval_lower_seconds']:.6f} s，actor 池限制供给。"
           '[actor 服务能力翻倍](../calculations/results/rl-supply-double-actor.md)后限制转到 learner；[共享 GPU 池](../calculations/results/rl-supply-shared-gpu.md)把各阶段占用累加，不能只取最大单阶段。'
           '运行 `python3 calculations/calc.py rl-supply --inputs calculations/scenarios/rl-supply-example.json --format md` 修改输入复现。矩阵速率不是硬件峰值或实测，增配倍率不是设备扩展保证；验证孤立批次按整轮、稳态按总服务量计。同步 on-policy 权重依赖可能禁止跨批重叠，完整损失／优化器等仍未计入，故流水上界不可直接作为实际吞吐。',
           '> **实验 3-7')
    trace = result('trace-qwen8-correlated')
    insert('03-推理与训练负载.md', 'C15-request-trace',
           f"[成对长度与 FIFO 重放](../calculations/results/trace-qwen8-correlated.md)使用平均 P=1024／G=128 的四条请求，显式输入每条 prefill／decode 时长与到达时刻：两 worker 的 p95 完成延迟为 {trace['p95_latency_ns']/1e6:.6f} ms，声明 KV 槽策略的峰值为 {trace['kv_peak_bytes']/2**20:.6f} MiB。"
           '[均匀长度](../calculations/results/trace-qwen8-uniform.md)、[反向配对](../calculations/results/trace-qwen8-anticorrelated.md)和[错开到达](../calculations/results/trace-qwen8-spaced.md)保持平均长度，分别改变尾部、输入输出相关性与突发。'
           '运行 `python3 calculations/calc.py request-trace --inputs calculations/scenarios/request-trace-example.json --format md` 修改轨迹复现。每请求独占 worker，服务时长为教学输入；prefill 产生首输出，最后输出不再入 KV。prompt 槽在开始预留，decode 每步增加一槽，完成即释放；p95 采用 nearest-rank，小样本可能等于最大值。矩阵工作由官方配置计算，KV 存活面积不是 HBM 流量；批处理、容量准入和真实服务校准另计。',
           '> **实验 3-2')
    tight = result('trace-qwen8-capacity-tight')
    insert('03-推理与训练负载.md', 'C15-kv-admission',
           f"[256 MiB KV 准入预算](../calculations/results/trace-qwen8-capacity-tight.md)沿用相同请求与服务时长，两个 worker 仍会因缓存不足等待；p95 完成延迟变为 {tight['p95_latency_ns']/1e6:.6f} ms，预留峰值为 {tight['kv_reservation_peak_bytes']/2**20:.6f} MiB。"
           '[512 MiB 对照](../calculations/results/trace-qwen8-capacity-roomy.md)保持工作量和接受请求不变，仅放宽预算。运行 `python3 calculations/calc.py request-trace --inputs calculations/scenarios/request-trace-capacity.json --format md` 复现。'
           '有限模式准入时按声明最大输出 G 预留 P+G−1 个槽，到完成才释放；活跃槽仍逐步增长，两者分别积分。FIFO 队头不能被小请求越过，单请求独占也放不下时拒绝输入。预算仅含共享逻辑 KV，不代表全设备显存，也不假定跨设备缓存可免费共享；本例实际输出恰好达到声明上限，未使用未知未来长度作调度输入。',
           '> **实验 3-2')
    agent = result('agent-thinking-on')
    changed = result('agent-thinking-on-double-first')
    insert('03-推理与训练负载.md', 'C16-real-agent-trace',
           f"[真实 Agent 轨迹复算](../calculations/results/agent-thinking-on.md)读取原实验逐轮 token ID、引擎命中和墙钟记录的独立哈希副本。开启 thinking 的四轮共 5297 输入／4480 命中／2733 输出 token，命中后 prefill 矩阵工作为 {agent['cached_prefill_matrix_flops']/1e12:.6f} TFLOPs，相同输入冷重算为 {agent['cold_prefill_matrix_flops']/1e12:.6f} TFLOPs。"
           f"[只将首轮模型段加速两倍](../calculations/results/agent-thinking-on-double-first.md)，在工具轨迹与其它时段不变的条件下，总时间从 {agent['measured_elapsed_seconds']:.6f} s 变为 {changed['counterfactual_elapsed_seconds']:.6f} s。"
           '运行 `python3 calculations/calc.py agent-trace --trace thinking-on --model-speedup 2 --selected-turn 0 --format md` 复现。关闭 thinking 的失败尝试、开启后的首轮截断与额外别名检查差异均保留；模型墙钟不等于 GPU 核时，缓存矩阵差额不按比例缩放实测时间。工具等待的 KV byte·s 仅是假设保留本轮全部逻辑槽的预算，实际块驻留／释放未知，不能当实测缓存峰值。',
           '> **实验 3-4')
    audio = result('audio-timing-base')
    insert('03-推理与训练负载.md', 'C17-audio-timing',
           f"[音频块教学时序](../calculations/results/audio-timing-base.md)按 20 ms 块、24 kHz 单声道／2 bytes PCM 元素计算，每块 {audio['pcm_chunk_bytes']} bytes；显式模型／发送／传播时长下，40 ms 抖动缓冲对应从采集起点起 {audio['first_playback_from_time_zero_ns']/1e6:.0f} ms 首次播放及 {audio['total_playback_stall_ns']/1e6:.0f} ms 新增停顿。"
           '[60 ms 缓冲对照](../calculations/results/audio-timing-large-buffer.md)消除本次停顿但增加首播等待；[慢模型](../calculations/results/audio-timing-slow-model.md)与[打断投影](../calculations/results/audio-timing-interrupt.md)分别改变服务与静音响应。'
           '运行 `python3 calculations/calc.py audio-timing --inputs calculations/scenarios/audio-timing-example.json --format md` 修改输入。固定截止、实际播放后移、乱序 ready queue 和新增停顿分列；静音按控制延迟后的设备量子生效，不表示 GPU 任务取消。所有时长均为教学输入，尚非固定语音实测；声学模型、真实取消／flush、抖动轨迹仍待接入。',
           '> **实验 3-5')
    insert('05-算子与运行时.md', 'C25-gemm-tiles',
           '[官方 Qwen3-8B 单支 up projection 分块](../calculations/results/gemm-tiles-qwen8.md)已复算 103079215104 FLOPs 与 128 MiB 单次读写载荷；k=32 时，32／64／128 输出块分别占 8／24／80 KiB，指定接口流量为 6168／3096／1560 MiB。'
           '[K 外层循环](../calculations/results/gemm-tiles-qwen8-partials.md)显式增加非最终 K 块的 FP32 partial 写回及后续重读；[尾块](../calculations/results/gemm-tiles-qwen8-tail.md)分别计有效元素流量与完整 tile 算术，[双缓冲](../calculations/results/gemm-tiles-qwen8-double-buffer.md)只增加声明容量，不自动减少字节或推断加速。'
           '运行 `python3 calculations/calc.py gemm-tiles --capacity-bytes 24576 --format md` 枚举可放候选。选中项仅为给定候选中接口流量最小者；累加器保留、输入不跨输出块复用、尾部 masked 读写均显式声明，L2 服务的重读不能算成实测 HBM。',
           '> **实验 5-1')
    reduction = result('rmsnorm-row1024-split8')
    insert('05-算子与运行时.md', 'C25-row-reduction',
           f"[Qwen RMSNorm 的三阶段拆分](../calculations/results/rmsnorm-row1024-split8.md)在 M=1024、D=4096、S=8 时，partial 占 {reduction['partial_buffer_bytes']} bytes，inverse 占 {reduction['inverse_buffer_bytes']} bytes；相对保留整行的一组一行方案，声明接口多 {reduction['additional_interface_bytes']} bytes。"
           '局部加法 M(D−S) 与合并加法 M(S−1) 总数仍为 M(D−1)，但多了输入重读、partial／inverse 交接和三次 launch。运行 `python3 calculations/calc.py row-reduction --rows 1024 --splits 8 --format md` 复现；七分片尾部与十六倍加宽变体另列。'
           '小数值检查验证数学归一化一致，并保留 FP32 改变求和分组产生不同舍入的反例。容量仅为声明的局部行／分片和辅助缓冲，不是寄存器实配或完整峰值；组数增加不保证实际加速。',
           '> **实验 5-1')
    insert('05-算子与运行时.md', 'C25-bank-mapping',
           '[32-bank 标量地址枚举](../calculations/results/bank-column-stride32.md)在每 bank 每轮一个 32-bit 字的声明模型下，32×32 FP32 块的列访问需32轮；[行跨度33](../calculations/results/bank-column-stride33.md)增加128 bytes、即3.125% padding 后需1轮，行访问始终分散。'
           '运行 `python3 calculations/calc.py bank-mapping --stride-words 33 --format md` 查看每个 bank 的 lane 与地址。[同址广播](../calculations/results/bank-same-word-broadcast.md)与关闭广播分别计量，同 bank 不同地址不能合并；双端口是明确教学变体。CUDA 13.2.1 官方 bank 映射原件已复制入来源锁并核验哈希；此标量 padding 不等于 TMA swizzle，也不能由轮数推断 GEMM 加速比。',
           '> **实验 5-1')
    insert('05-算子与运行时.md', 'C25-loop-access',
           '[实验 C 循环的数组访问复算](../calculations/results/loop-access-127-257-65.md)已按固定 matmul.c 展开 ijk／ikj／blocked：ijk 保留局部 sum、每个输出只写一次；另两种先清零后按乘加读改写 C，ikj 将 A[i,k] 提到内层外，blocked 则每个列块重新读取它。'
           '尾块逐地址枚举与独立矩阵乘对照通过，四个实验形状均匹配八个候选、各九次原始时间样本。127×257×65 中，ikj 源码数组字节多于 ijk，但测量中位时间约198.22 μs对1398.30 μs；不能把源码字节直接当缓存流量或由它预测时间。'
           '运行 `python3 calculations/calc.py loop-access --m 127 --k 257 --n 65 --format md` 复现。C 与原始样本已独立归档并锁哈希，只在形状／方法／tile 完全匹配时附实测；未匹配留空，未重跑或外推基准。',
           '> **实验 5-1')
    insert('05-算子与运行时.md', 'C26-fusion-lifetime',
           '[Qwen3-8B 点式融合生命周期](../calculations/results/fusion-qwen8-pointwise.md)从 M=1024、F=12288 的两份 BF16 gate/up 输出开始，SiLU／乘法／固定尺度1-byte cast 分开执行的主张量接口为156 MiB，完全融合为60 MiB；两个24 MiB中间量各消除一次写回和读取，合计少96 MiB。'
           '按输出先分配、输入最后消费后释放的显式策略，声明张量峰值为72／60 MiB，不能将全部张量容量相加。[加入物理布局重排](../calculations/results/fusion-qwen8-layout.md)单独执行多48 MiB读写，并枚举八种连续划分。'
           '运行 `python3 calculations/calc.py fusion-lifetime --layout-copy --format md` 查看每组活跃集合与释放列表。固定尺度已给定，动态amax／scale、局部FP32 scratch、allocator保留池和地址／合并访问代价未计入；因此主张量节省不等于完整设备峰值或实际加速。',
           '> **实验 5-2')
    insert('05-算子与运行时.md', 'C29-quantized-gemm',
           '[真实 Qwen235B 专家投影的量化接口账](../calculations/results/quant-gemm-qwen235-base.md)取教学 M=4096、官方 K=4096／N=1536、输出 tile=128×128，矩阵工作51539607552 FLOPs；独立全行量化、全行尺度融合cast、前缀尺度融合cast的主张量流量分别444／620／588 MiB。'
           '每行一个FP32 scale 的写入和逐列块读取另列；独立量化按输入只读一次计，需要至少8 KiB每活动行的输入驻留。融合减少中间物化却增加宽输入重读，前缀尺度还改变舍入语义。'
           '运行 `python3 calculations/calc.py quantized-gemm --tile-n 1536 --format md` 改为一个输出列块，此时前两种方案的主张量差额消失。尾块实际元素与完整padding FLOPs分别保存，未知scratch／权重尺度和真实HBM不填造，不能由字节差额直接推断加速。',
           '> **实验 5-4')
    insert('05-算子与运行时.md', 'C29-fusion-numerics',
           '[融合数值反例](../calculations/results/fusion-numerics-small-first.md)已按官方ONNX E4M3FN布局枚举有限值并做精确最近偶数舍入：256项行的两块首项为1／10、仅1对应权重为1，全行量化输出55/56、前缀尺度输出1，差1/56；转FP16后仍为0.98193359375与1。'
           '[交换两块及对应权重](../calculations/results/fusion-numerics-large-first.md)后此反例两种路径一致，说明顺序也进入数值语义。另以x=[1,−1,1]、y=[1,1,1]验证局部零因子丢失状态：错误补零得到1，保留sum(y)才恢复正确3。'
           '运行 `python3 calculations/calc.py fusion-numerics --format md` 复现；有限编码回转、相邻值中点的偶数规则、零块与尾块均已检查。FP8外其余算术采用精确有理数来隔离舍入影响，不冒充真实GPU累加或作者kernel实测。',
           '> **实验 5-4')
    insert('05-算子与运行时.md', 'C27-online-softmax',
           '[在线Softmax状态合并](../calculations/results/online-softmax-book.md)以三个分数[0,ln2,ln4]和值[1,3,−2]复算：保留各块(m,l,U)并换到共同最大值后，顺序／树形结果为−1/7；只将块输出等权平均得到错误1/6。'
           '[空块及掩码](../calculations/results/online-softmax-empty.md)使用显式空状态作单位元，全部掩码时结果留空，不计算exp(−∞−(−∞))。运行 `python3 calculations/calc.py online-softmax --inputs calculations/scenarios/online-softmax-example.json --format md` 复现。'
           '非空合并的exp、减法、最大值比较、l/U加权和与最终除法分别计量；多维大偏置分数用直接稳定Softmax独立检查，浮点树序仅在容限内等价，不声称逐位一致。此处是状态与数值子账，QK/PV tile、完整局部算术、工作区和后端流量另算。',
           '> **实验 5-3')
    insert('05-算子与运行时.md', 'C27-attention-tiles',
           '[128 KiB单头注意力分块](../calculations/results/attention-tiles-book.md)已按官方d=128复算混合精度缓冲：b=1／64／128时，最大a=166／110／76，非因果完整扫描接口分别204／304／436 MiB，块对更新409600／9600／6912次；非首有效块的逐元素旧输出缩放另计。'
           '[因果变体](../calculations/results/attention-tiles-causal.md)跳过全不可见K块，保留边界块实际行读取，分别报告有效因果、访问矩形tile和完整padding矩阵工作；[K/V双槽](../calculations/results/attention-tiles-two-slots.md)重新计算a与扫描次数。'
           '运行 `python3 calculations/calc.py attention-tiles --causal --kv-slots 2 --format md` 复现。这里只算单query head及对应K/V head；缓冲是抽象容量，流量是指定下一层接口，块对更新不是kernel launch。候选最少字节不代表真实内核最快，GQA复用、L2／HBM与硬件scratch不得由本表直接外推。',
           '> **实验 5-3')
    host = result('host-transfer-double')
    single_host_device = result('host-transfer-single-device')
    insert('05-算子与运行时.md', 'C28-host-transfer',
           f"[主机／设备双槽时序](../calculations/results/host-transfer-double.md)按官方Qwen隐藏维度得到每块64 MiB；显式准备1 ms、有效H2D24 GiB/s、消费4 ms时，八块串行为{host['serial_seconds']*1000:.6f} ms，双端各两槽为{host['scheduled_finish_seconds']*1000:.6f} ms，两侧各预留128 MiB。"
           f"[设备只留一槽](../calculations/results/host-transfer-single-device.md)为{single_host_device['scheduled_finish_seconds']*1000:.6f} ms，搬运字节未变。"
           '[链路带宽减半](../calculations/results/host-transfer-half-bandwidth.md)时双槽为46.666667 ms。运行 `python3 calculations/calc.py host-transfer --format md` 查看逐块槽号与时间。主机槽等DMA完成才复用，设备槽等消费结束才复用，内部以有理数递推；预留池与同时存活峰值分列。准备／链路／消费是教学供给，未计初次锁页、其它工作区或共享带宽争用，不据Async调用名声称真实重叠。',
           '> **图 5-2')
    insert('05-算子与运行时.md', 'C28-stream-buffer',
           '[五块FIFO与背压](../calculations/results/stream-buffer-book.md)已复算每块16 KiB、原FIFO峰值48 KiB与独立重排槽32 KiB，合计80 KiB超过64 KiB预算。扣除重排后FIFO能放两块，背压使生产时刻由[4,5,6,7,8]变为[4,5,6,7,9]，消费仍为[5,7,9,11,13]：不能保持原生产进度，不等于最后取走一定推迟。'
           '[统一布局](../calculations/results/stream-buffer-layout-unified.md)去掉重排预留后原进度可放；[只留一块FIFO](../calculations/results/stream-buffer-one-slot.md)仍在第13格取完。运行 `python3 calculations/calc.py stream-buffer --format md` 查看先消费后生产的逐事件占用。'
           '这些是教学时间格，背压会传递到后续生产，消费者按实际就绪和最小间隔取数据。最后取走不等于下游计算完成；重排槽是指定实现的独立预留，转换成本、内部工作区和分支汇合不在此单边模型中。',
           '> **图 5-2')
    insert('05-算子与运行时.md', 'C30-graph-execution',
           '[图重放小输入](../calculations/results/graph-small-input.md)与[大输入](../calculations/results/graph-large-input.md)读取官方Qwen H=4096，256／2048个BF16 token为2／16 MiB；额外复制读写4／32 MiB，教学2 TB/s流量带宽下为2.097152／16.777216 us。设备20 us、暴露提交20 us、重放3 us、元数据2 us时，普通40 us，带复制图为27.097152／41.777216 us，额外6 us间接寻址图为31 us。'
           '间接路径额外准备1秒时，至少111112次才严格快于普通执行；10万次仍选择普通，[100万次寿命](../calculations/results/graph-long-lived.md)才选择间接路径。直接写稳定输出的路径另列，不混作外部输入的免费替代。'
           '单层三矩阵FFN将1536行补到2048增加154618822656 FLOPs，即真实矩阵工作的1/3。配置／设备各20 us的100段独立资源流水为2020 us，设备快4倍仅降至2005 us，两者都快4倍才为505 us。运行 `python3 calculations/calc.py graph-execution --format md` 复现；全部供给时间是教学输入，串行图预算与配置重叠预算分开，图池／KV占用与实际后端另核。',
           '> **实验 5-8')
    insert('05-算子与运行时.md', 'C30-optimization-deployment',
           '[候选分数与部署预算](../calculations/results/deployment-equal.md)复算A的形状平均加速比5.25×，但等频总耗时210 us反而超过基线200 us；B为100 us。[x占九成](../calculations/results/deployment-skewed.md)时A平均29 us优于B的50 us，交叉条件p>15/19由两形状时间差求出。'
           '逐形状选A／B平均30 us，每次分派必须小于20 us才优于统一B；额外准备600秒、零分派开销时3000万次恰好摊平，按平均频率延拓30000001次才严格更快，按完整两调用频数组则需15000001组。'
           '[验证失败变体](../calculations/results/deployment-validation-failure.md)将无效候选排除，部署按原路径实际耗时回退，分数零不等于执行时间零。运行 `python3 calculations/calc.py optimization-deployment --inputs calculations/scenarios/deployment-example.json --format md` 修改频数和准备预算。时间是教学输入下串行成本，不冒充真实引擎采用或有重叠的请求延迟；额外准备相对统一路径计量，共同成本不重复加入。',
           '> **实验 5-6')
    insert('05-算子与运行时.md', 'C30-shape-specialization',
           '[形状特化成本](../calculations/results/specialization-medium.md)用官方Qwen3-8B单层FFN，256／1536／2048行按8／1／1频数形成十调用组：真实矩阵工作1700807049216 FLOPs；分到512／2048桶额外增加773094113280 FLOPs。教学通用／桶／特化服务率100／200／250 TFLOP/s、每工件准备100／200／300 ms下，三个策略总准备100／400／900 ms，按实际用到的工件各计一次。'
           '[只执行一组](../calculations/results/specialization-short.md)选择通用，70组选择分桶，[1000组](../calculations/results/specialization-long.md)选择逐形状特化；精确仿射交点单列。[缓存命中](../calculations/results/specialization-cache.md)去掉已兼容工件准备，[未覆盖形状](../calculations/results/specialization-fallback.md)回退通用并只补一次通用准备。'
           '运行 `python3 calculations/calc.py shape-specialization --inputs calculations/scenarios/specialization-example.json --format md` 修改频数、桶和特化集合。速率与准备是教学输入，padding只算FFN矩阵，缓存加载、淘汰、编译重叠与完整模型时间不由此推断。',
           '> **实验 5-7')
    insert('05-算子与运行时.md', 'C30-specialization-figure',
           '[图5-6：策略总时间交叉](../calculations/figures/specialization/figure.svg)由已校验的specialization-medium结果生成，横轴为十调用频数组重复次数，纵轴包含工件准备与执行；零点表示准备截距，三个交点按有理数解析求解。'
           '[逐点精确数据](../calculations/figures/specialization/data.json)保留0至150组的三条曲线与最优策略。[PNG](../calculations/figures/specialization/figure.png)供写作预览。安装可选plot依赖后运行 `python3 calculations/calc.py plot-specialization` 重绘；图像、数据、脚本及输入结果哈希均纳入校验。',
           '> **图 5-6')
    insert('05-算子与运行时.md', 'C30-runtime-trace',
           '[固定FFN运行记录复核](../calculations/results/runtime-ffn-token32.md)从原始样本重算中位数／最小／最大值，并逐事件核对Nsight：三次eager为18次主机启动和18个kernel，图为3次启动但仍18个kernel，融合图为3次启动和15个kernel；八个顺序微批融合图为24次图提交、168个kernel。逻辑矩阵／激活数与库生成kernel分列，设备活动取区间并集，未覆盖区间不称整卡空闲。'
           '同一32-token链，融合图整批／四微批／八微批实测中位约202.50／796.28／1590.70 us，矩阵FLOPs不变；显式缓冲全保留，融合2.75 MiB、分离3.5 MiB。[257行补到512](../calculations/results/runtime-ffn-token257.md)重算补齐工作与44 MiB融合张量账。'
           '运行 `python3 calculations/calc.py runtime-trace --format md` 复现。原记录已独立通过21计时方案／63输入更新检查／9原始时间线校验，复制入计算项目并锁哈希；共享GPU、热缓存和分析器扰动条件保留，主机提交不与设备时间相加。MPK作者Qwen3-8B/A100全模型14.5／12.5 ms仅作独立29/25对照，未在本机执行，也不与RTX局部收益相乘。',
           '> **实验 5-8')
    insert('05-算子与运行时.md', 'C30-persistent-tasks',
           '[按块就绪任务账](../calculations/results/persistent-tiles-base.md)取官方Qwen单支up投影接SiLU，512行分八块，矩阵51539607552 FLOPs、SiLU6291456元素；一次主机启动仍有16个设备任务、16次完成事件发布及8条跨任务依赖。显式独立矩阵／向量worker、200 TFLOP/s与20G元素/s、分派0.5 us／事件0.2 us时，整算子屏障582.270838 us，按块就绪358.085055 us。'
           '[高分派成本](../calculations/results/persistent-tiles-slow-dispatch.md)可使按块方案更慢；[513行尾块](../calculations/results/persistent-tiles-tail.md)只减少尾块数学工作，不免去固定任务开销。中间张量仍有24 MiB写读，默认实际存活峰值6 MiB，未施加有限池预算。'
           '运行 `python3 calculations/calc.py persistent-tasks --format md` 查看逐任务依赖。吞吐和开销均为教学输入，不是MPK实测；若共享SM／带宽／寄存器则需重估并发服务率。只演示无跨块归约的up→SiLU，不忽略完整FFN的down全K依赖，轮询次数／事件表字节和其它工作区留待具体实现。',
           '> **实验 5-8')
    insert('05-算子与运行时.md', 'C31-request-dag',
           '[请求依赖图复算](../calculations/results/request-dag-path-switch.md)用教学prepare10us、hotspot60us、并行分支40us、finish10us：热点加快四倍后，旧路径相加35us，但请求从80us只降到60us，关键路径转到并行分支。全部工作串行化的比值1.6与请求比值4/3分列，不把kernel时间总和占比套到请求墙钟。'
           '[优化非关键分支](../calculations/results/request-dag-no-gain.md)不改变80us完成时间；[显式共享串行资源](../calculations/results/request-dag-shared-resource.md)增加资源前序边，改后75us；[并发分支变慢情景](../calculations/results/request-dag-contention.md)输入90us分支后整请求为110us，即局部更快、整体更慢。'
           '运行 `python3 calculations/calc.py request-dag --inputs calculations/scenarios/request-dag-example.json --format md` 修改时长、依赖与资源映射。调度为最早可启动的确定性列表规则，不声称最优；争用时长是显式情景，不自动预测SM／HBM干扰。实验5-9已有固定负载的同引擎替换记录；本图仍采用教学时长，尚未由真实并发与资源依赖校准，不声明该图预测了请求收益。',
           '> **实验 5-9')
    insert('05-算子与运行时.md', 'C31-microbatch-overlap',
           '[两微批与联合争用](../calculations/results/microbatch-overlap-book.md)复算官方Qwen3-8B单层FFN：256行矩阵工作77309411328 FLOPs，拆128/128后不变；BF16唯一权重288 MiB，两份独立完整读取且无跨微批缓存命中时逻辑读取576 MiB，不是容量翻倍。'
           '显式教学完整N/C=0.4/0.8 ms、每份N/C=0.2/0.48 ms，原batch／拆分串行／理想重叠分别1.20／1.36／1.16 ms；将C0与N1联合窗口设为0.60 ms后总计1.28 ms。联合窗口严格小于0.52 ms才有收益，[恰好0.52 ms](../calculations/results/microbatch-overlap-break-even.md)只打平，[0.50 ms](../calculations/results/microbatch-overlap-low-contention.md)为1.18 ms。'
           '运行 `python3 calculations/calc.py microbatch-overlap --inputs calculations/scenarios/microbatch-overlap-example.json --format md` 修改联合窗口和两份服务时长。依赖图保留填充与排空，不造联合窗口内的各自完成时间；N不是默认等同权重读取，时长也不是由矩阵FLOPs推成GPU实测。实际并发profile、缓存、有限缓冲和完整请求仍需另外验证。',
           '> **实验 5-9')
    insert('06-超节点.md', 'C35-topology-allocation',
           '[端口重构与放置算例](../calculations/results/topology-allocation-prefill.md)复用官方Qwen 8MiB输入、八rank ring发送14MiB／14轮：教学alpha5us、有效出站25→75GB/s时657.202560→265.734187us，额外准备100ms需256次调用才严格获益。[decode的8KiB输入](../calculations/results/topology-allocation-decode.md)为70.573440→70.191147us，需261580次，启动项不能按带宽倍数缩短。'
           '4×4周期位置图各空闲八格、作业要求相邻2×2时，连续两行有四个候选窗口，最多同时放两个；棋盘式为零。四条同向流各需25GB/s经过50GB/s割集时不满足需求，均分上限12.5GB/s，空闲数并不证明网络可行。'
           '运行 `python3 calculations/calc.py topology-allocation --inputs calculations/scenarios/topology-allocation-example.json --format md` 复算。放置窗口穷举与割集条件单列，未提供二者之间的实际路径映射，不冒充可部署TPU切片或Morphlux重现；带宽／准备均是教学输入，归约、HBM、故障状态恢复另核。',
           '> **实验 6-4')
    insert('06-超节点.md', 'C34-collective-paths',
           '[有向物理环路径枚举](../calculations/results/collective-paths-book.md)按官方Qwen 8MiB输入、16节点，复算递归与Swing对端选择前三轮共96条消息。每rank均发送4/2/1MiB；递归跳数1/2/4、峰值链路消息1/2/4，全网各64MiB；Swing跳数1/1/3、峰值1/1/2，全网64/32/48MiB。第三轮三跳不等于峰值三条消息，所有物理边按方向分别累加。'
           '教学每向50GB/s下，递归三轮传输下界各83.886080us，Swing为83.886080/41.943040/41.943040us。运行 `python3 calculations/calc.py collective-paths --format md` 复现，JSON保留全部路径和链路字节；[decode变体](../calculations/results/collective-paths-decode.md)按真实输入量缩放。'
           '官方论文式2原文已复制并核验既有manifest哈希；独立BFS核对最短跳数和逐边守恒。这里只算前三轮reduce-scatter路径，未计启动、逐跳延迟、包级阻塞、后续轮次或all-gather，不能把此下界比值写成完整all-reduce加速。',
           '> **实验 6-4')
    insert('06-超节点.md', 'C34-collective-path-figure',
           '[图6-4物理路径面板](../calculations/figures/collective-paths/figure.svg)由已校验96条消息路径生成，六面板统一色标，内外箭头分别表示顺／逆时针；每轮按全部16个发送者累计有向链路字节，灰色表示该方向无流量。面板标明最忙链路消息数、字节、全网搬运量及rank0示例路径。'
           '[逐边绘图数据](../calculations/figures/collective-paths/data.json)包含零负载方向，[PNG](../calculations/figures/collective-paths/figure.png)供写作预览。安装可选plot依赖后运行 `python3 calculations/calc.py plot-collective-paths` 重绘；图与输入／脚本哈希一起校验，范围仍仅为前三轮reduce-scatter。',
           '> **图 6-4')
    insert('07-数据中心网络.md', 'C40-periodic-queue',
           '[周期需求与队列](../calculations/results/periodic-queue-aligned.md)复算两作业每100ms各突发20ms、40GB/s，共用50GB/s：平均需求16GB/s，峰值80GB/s；外生速率下积压600MB，20ms后停止注入再12ms排空，兼容度22/25=0.88，窗口平均队列96MB。'
           '[错开20ms](../calculations/results/periodic-queue-staggered.md)峰值40GB/s、队列零、兼容度1；[漂移至5ms重叠](../calculations/results/periodic-queue-drift.md)积压150MB。[持续过载](../calculations/results/periodic-queue-overloaded.md)兼容度可负，不是概率；跨周期脉冲和不同周期LCM窗口均按事件积分。'
           '运行 `python3 calculations/calc.py periodic-queue --inputs calculations/scenarios/periodic-queue-example.json --format md` 修改到达与错峰。队列从观察起点零积压开始，内部排空时刻用有理数插入；正超额积分、峰值积压、面积及期末残留分列。此场景使用无限缓冲且未模拟PFC／DCQCN反馈，不能把教学600MB写成真实交换机缓冲或直接推出训练步时。',
           '> **实验 7-8')
    insert('07-数据中心网络.md', 'C40-feedback-queue',
           '[有限缓冲与反馈延迟](../calculations/results/feedback-queue-overflow.md)以教学到达80GB/s、出口50GB/s、初始256KiB、512KiB缓冲复算：20us后降至40GB/s，缓冲在8.738133us填满，丢弃337856 bytes，在72.4288us排空。'
           '[1MiB缓冲](../calculations/results/feedback-queue-roomy.md)峰值862144 bytes且不丢弃；[反馈延至40us](../calculations/results/feedback-queue-late.md)丢弃937856 bytes；[仅降至出口速率](../calculations/results/feedback-queue-no-drain.md)保留862144 bytes积压。'
           '运行 `python3 calculations/calc.py feedback-queue --format md` 复算。精确填满与排空时刻拆分积分，满足初始积压＋到达＝服务＋丢弃＋末尾积压。这里是一次显式速率切换的流体近似，尚不模拟ECN控制器、多轮反馈、包级丢弃、重传或任务完成时间。',
           '> **实验 7-8')
    insert('07-数据中心网络.md', 'C40-packet-reorder',
           '[多路径报文事件](../calculations/results/packet-reorder-loss.md)用官方Qwen一个token的BF16激活8192 bytes，拆八个1024-byte报文，轮转两条独立教学1GB/s路径。'
           '[路径均延迟1us](../calculations/results/packet-reorder-balanced.md)完成5.096us，乱序保留为零；[延迟1/9us](../calculations/results/packet-reorder-skewed.md)完成13.096us，保留峰值3072 bytes且无需重传。'
           '若首包丢失、其发送结束20us后进入重传队列，完成23.048us、保留峰值7168 bytes，仅重传1024 bytes；从首个缺口重发整段的字节对照为8192 bytes。恢复延迟40us时完成43.048us。'
           '运行 `python3 calculations/calc.py packet-reorder --format md` 查看到达和按序释放事件。峰值仅计连续前缀释放后保留的乱序payload，不等于入口暂存或协议SRAM；丢失恢复由输入指定，未模拟ACK、虚假超时、有限窗口或OpenURMA实际行为。',
           '> **实验 7-9')
    insert('07-数据中心网络.md', 'C41-collective-tail',
           '[rank就绪与完成时间](../calculations/results/collective-tail-book.md)用官方Qwen每rank 8MiB BF16消息作为载荷背景，显式四rank在0/0/0/2ms就绪、交换0.4ms：原2.4ms，交换减半2.2ms，对齐到最早就绪时刻0.4ms。三个rank各等待2ms不能相加到墙钟。'
           '[100条教学记录](../calculations/results/collective-tail-mixed.md)包含98条正常、1条晚就绪2ms、1条额外恢复10ms；原平均0.52ms、p99=2.4ms、max=10.4ms，交换减半后平均0.32ms、p99=2.2ms、max=10.2ms。'
           '[恢复记录增至两条](../calculations/results/collective-tail-fault-heavy.md)时p99=10.4ms，说明分位数需声明记录与取整口径。运行 `python3 calculations/calc.py collective-tail --format md` 复算。按有限记录最近秩分位数计算，保留各阶段联合关系；不能把边际p99相加，也不能把教学频数当真实故障率。真实提前分块通信和完整任务仍需依赖图校准。',
           '> **实验 7-10')
    insert('07-数据中心网络.md', 'C39-connection-states',
           '[活跃关系与传输状态](../calculations/results/connection-states-full.md)复算本机64线程×128对端共8192条有向关系：逐关系独立传输8192份，按对端共享128份。教学端点256／关系绑定64／传输1024 bytes下，总容量8929280→671744 bytes，绑定仍占524288 bytes。'
           '[八类隔离](../calculations/results/connection-states-isolated.md)保留1024份传输，总1589248 bytes，超过教学1MiB预算；每线程独占时不再节省。[仅一个热点对端](../calculations/results/connection-states-hot-peer.md)有64条活跃关系、1份共享传输，总21504 bytes。'
           '运行 `python3 calculations/calc.py connection-states --format md` 复算，JSON保留关系与共享组。已分配空闲端点仍计容量；这些字节不是官方QP或Jetty/TP结构大小，组人数也不是热点吞吐或队头阻塞预测。',
           '> **实验 7-6')
    insert('07-数据中心网络.md', 'C39-operation-ordering',
           '[必要发布依赖与独立传输](../calculations/results/operation-ordering-book.md)以官方Qwen各8KiB数据载荷、教学写20us／恢复至可见80us／通知2us／独立传输10us复算：全部串行112us，保留数据可见→通知依赖并允许独立通路后102us，独立传输10us完成。'
           '[共用容量一资源](../calculations/results/operation-ordering-shared.md)仍为112us，删除额外依赖不等于消除资源争用。运行 `python3 calculations/calc.py operation-ordering --format md` 查时序。'
           '另列两个4-byte标量的取值反例：1us读D=0，2us发布D=1，3us发布F=1，4us读F=1；5us按F/D返回仍带旧D=0。完整冲突检测后重读2us，6us才能交付D=1，逻辑读取8→12 bytes。实际取值与响应交付分开；同刻写入先于取值，若2us取D则无须重读。该事件模型不冒称UB条款或现有网卡实现。',
           '> **实验 7-7')
    insert('07-数据中心网络.md', 'C39-completion-reclaim',
           '[完成消费与credit回收](../calculations/results/completion-reclaim-book.md)用16次官方Qwen各8KiB激活传输、8槽位、提交间隔1us、固定完成延迟5us、每20us消费至多4项的教学输入复算：48us传输全完，80us全部回收，最长提交等待28us。预留payload 64KiB，未消费完成项峰值8个，按教学64 bytes/项计512 bytes。'
           '[槽位增至16](../calculations/results/completion-reclaim-more-slots.md)预留128KiB，传输20us全完但回收仍80us；[每5us轮询](../calculations/results/completion-reclaim-fast-poll.md)传输22us／回收25us；[每次仅消费一项](../calculations/results/completion-reclaim-small-batch.md)传输165us／回收320us。'
           '运行 `python3 calculations/calc.py completion-reclaim --format md` 检查逐操作时刻。本例槽位保持至完成项消费，不将传输完成等同回收；轮询瞬时且有批量预算，未模拟独立CQ容量、地址转换或异常路径，元数据大小不代表真实NIC结构。',
           '## 7.5 并发通信的拥塞与可靠性')
    insert('07-数据中心网络.md', 'C38-remote-window',
           '[远程读取窗口](../calculations/results/remote-window-book.md)复算教学单向40GB/s、256 bytes、2us：ceil(BT/m)=313，128个活跃请求窗口上界16.384GB/s。'
           '[串行服务点100ns/请求](../calculations/results/remote-window-serial.md)进一步限制至2.56GB/s；[源端逐次等完成](../calculations/results/remote-window-source-wait.md)虽分配128槽，活跃只有1，上界0.128GB/s。'
           '[增加到313槽](../calculations/results/remote-window-enlarged.md)仍受2.56GB/s服务限制；[服务启动间隔6ns](../calculations/results/remote-window-fast-service.md)时才通过这三项40GB/s必要条件。'
           '运行 `python3 calculations/calc.py memory-concurrency --transaction-bytes 256 --latency-ns 2000 --bandwidth-bytes-per-second 40000000000 --service-interval-ns 100 --format md` 复算。官方Qwen KV载荷用于服务时间下界；256-byte事务与服务参数为教学假设，不是模型KV块或网卡规格。串行间隔与单请求延迟分开，满足上界不等于可达测量。',
           '> **实验 7-5')
    insert('07-数据中心网络.md', 'C38-rpc-trace',
           '[真实RPC阶段复算](../calculations/results/rpc-trace-1048576.md)从实验7-4封存264次调用核对两端记录与载荷，每种载荷保留四模式各20次正式样本。1MiB时JSON→binary copy客户端CPU中位9.7745→1.0845ms，应用请求1398135→1048593 bytes；完整RPC中位362.598709→302.047146ms。'
           '同轮配对节省中位仅10.093647ms、11/20轮变快，与两中位数差60.551563ms不同。binary copy→view配对中位省20.730438ms而两组中位数之差为负，故保留逐轮差与范围，不用单一统计口径宣布稳定收益。'
           '运行 `python3 calculations/calc.py rpc-trace --payload-bytes 1048576 --format md` 查阶段表，[1KiB](../calculations/results/rpc-trace-1024.md)和[64KiB](../calculations/results/rpc-trace-65536.md)另列。客户端五阶段逐次守恒；服务端时间与客户端发送／等待重叠，不再相加。条件为Mac至Linux CPU的SSH转发，不是GPU推理、RDMA或裸链路。',
           '> **实验 7-4')
    insert('07-数据中心网络.md', 'C38-remote-state',
           '[远程读取与搬回本地](../calculations/results/remote-state-reused.md)用官方Qwen3-8B的1024-token BF16全层KV快照144MiB，固定快照复用四次。教学远程40GB/s且313个256-byte请求覆盖2us等待，bulk25GB/s、本地1TB/s，明确启动和串行目的端写入后：直接远程15.119494ms，搬回再读6.808772ms；网络576→144MiB，本地仍写144MiB并读576MiB。'
           '[只读一次](../calculations/results/remote-state-once.md)直接远程较快，严格获益从两次复用开始；[仅128个活跃请求](../calculations/results/remote-state-window-limited.md)时窗口限制改变选择。'
           '[本地仅余128MiB](../calculations/results/remote-state-capacity.md)放不下快照，不能选择搬回，即使时间估计更短。运行 `python3 calculations/calc.py remote-state --format md` 复算。场景只读不变历史快照，不冒充动态decode；网络与目的端写入按指定串行组织计时，实际DMA重叠、发布同步、取消与回收仍需路径校准。',
           '> **图 7-4')
    insert('08-单实例推理.md', 'C43-kv-pages',
           '[KV分页与引用计数](../calculations/results/kv-pages-branches.md)按官方Qwen3-8B每token 144KiB、16-token页2.25MiB计算。17-token前缀共享给三请求，a追加1、b追加16，再取消c：最终a/b长18/33，预留64-token/请求需18MiB，独占分页11.25MiB，共享分页9MiB；唯一有效35-token为5160960 bytes，空位29-token为4276224 bytes。'
           '两次共享未满尾页写前分别复制1-token，共288KiB有效内容；[16-token对齐前缀](../calculations/results/kv-pages-aligned.md)追加时新建页，无需复制已满页。[Qwen235变体](../calculations/results/kv-pages-qwen235.md)用188KiB/token重算；[全部取消](../calculations/results/kv-pages-release.md)归还所有页。'
           '运行 `python3 calculations/calc.py kv-pages --format md` 查事件和字节，JSON保留页表及引用。逻辑请求总和、物理唯一有效和完整页分配分别计算，碎片不能用分配减逻辑请求总和。cancel发生于无在途访问的安全点，不代表真实异步取消API返回就可回收；真实引擎COW也可能复制整页。',
           '> **实验 8-3')
    insert('08-单实例推理.md', 'C43-kv-page-capacity',
           '[有限页池准入](../calculations/results/kv-pages-capacity-two.md)给Qwen8B两个16-token页共4.5MiB：17-token前缀可以共享给三请求，但后续a+1需额外1页、b+16需额外2页，均完整拒绝，原页表／长度／引用不变。'
           '[三个页预算](../calculations/results/kv-pages-capacity-three.md)允许第一项追加，第二项仍拒绝。[取消后重试](../calculations/results/kv-pages-capacity-retry.md)先拒绝共享尾页写入，取消另一引用后虽然未释放物理页，尾页变成独占，重试可原地追加且复制为零。'
           '[同4.5MiB预算换Qwen235](../calculations/results/kv-pages-capacity-qwen235.md)只能容纳一个2.9375MiB页，17-token创建被拒绝。JSON输入加capacity_bytes复算，不能把共享当下省页等同未来增长保证；本例不自动抢占、重算或排队重试。',
           '> **实验 8-3')
    insert('08-单实例推理.md', 'C43-kv-trace',
           '[真实KV块复算](../calculations/results/kv-trace-small.md)读取实验8-3封存21文件，官方Qwen每16-token块2.25MiB。small池455块、保留1块、请求峰值454；[large](../calculations/results/kv-trace-large.md)池910块、请求峰值512。逐快照核对空闲＋请求拥有＋保留＝总块数及无重复／引用为1。'
           'small一次抢占时保留270个输出、computed清零、块归还；累计调度9993位置，相对large的8188多1805，最终输出完全一致。该重复位置不是额外输出，也未直接折算成等成本FLOPs。'
           '[取消记录](../calculations/results/kv-trace-cancel.md)实际释放104块，即234MiB容量；finish_after观察比API返回晚约29.858ms，不能据返回时刻提前复用。运行 `python3 calculations/calc.py kv-trace --run cancel --format md` 复算。每条件仅一次、带同步trace且共享GPU；APC关闭，未测共享前缀COW或无观测取消时延。',
           '> **实验 8-3')
    insert('08-单实例推理.md', 'C43-kv-restore',
           '[保留、换出与重算](../calculations/results/kv-restore-book.md)用官方Qwen1024-token 144MiB KV，标准backbone无lm_head重放14534471319552矩阵FLOPs，另列标量／特殊运算；原始int32 token ID为4096 bytes。教学双向25GB/s各加10us启动，单向6.049798ms；20ms后使用时可预取赶上，释放本地容量约7.900404ms，双向搬运288MiB。'
           '若独立给定重算50ms，则20ms期限需额外等待30ms，重算从0开始预留KV，不能把这50ms当空闲容量。[100ms窗口](../calculations/results/kv-restore-long-window.md)可推迟到50ms才重算，无恢复等待；[5ms窗口](../calculations/results/kv-restore-short-window.md)连换出取回也赶不上。'
           '[主机仅128MiB](../calculations/results/kv-restore-host-capacity.md)不能容纳完整快照。运行 `python3 calculations/calc.py kv-restore --format md` 查三策略。时间为显式服务输入，FLOPs不直接除峰值预测；保留KV占用其它请求容量的机会成本、未知复用时刻及完整淘汰策略仍需另算。',
           '> **实验 8-3')
    insert('08-单实例推理.md', 'C43-prefix-value',
           '[前缀容量价值](../calculations/results/prefix-value-book.md)用三个独立Qwen前缀512/768/1024token、各预期复用一次、各请求另有1-token suffix，官方full前向减命中后suffix前向计矩阵节省。180MiB预算下密度贪心只选1024token，占144MiB、省14534471319552 FLOPs；精确选择512+768占180MiB、省18032797679616 FLOPs，多省3498326360064。'
           '[复用次数变化](../calculations/results/prefix-value-reuse.md)将1024前缀预期复用改为3次会改变选择；[容量充足](../calculations/results/prefix-value-roomy.md)和[零容量](../calculations/results/prefix-value-no-capacity.md)另列。'
           '运行 `python3 calculations/calc.py prefix-value --format md` 复算，支持有理数预期次数和页尾取整。命中历史仍参加suffix注意力；本例候选不相互包含、不共享物理页，最优仅针对静态矩阵工作目标，不代表前缀树、取回延迟或在线淘汰最优。',
           '> **实验 8-4')
    insert('08-单实例推理.md', 'C43-apc-trace',
           '[真实Agent APC复算](../calculations/results/apc-trace-cache6.md)从实验8-4封存17文件核对五条件60次请求：固定12轮输入19556token，6GiB命中16304，按请求为11/12、按token为4076/4889。官方矩阵工作284309306474496→48184267112448 FLOPs，节省236125039362048；suffix仍对历史做注意力。'
           '[相同干扰下1GiB](../calculations/results/apc-trace-pressure1.md)命中零，[6GiB](../calculations/results/apc-trace-pressure6.md)保留16304命中；[0.2秒间隔](../calculations/results/apc-trace-gap6.md)命中不变，[关闭APC](../calculations/results/apc-trace-nocache6.md)为零。'
           '运行 `python3 calculations/calc.py apc-trace --run pressure6 --format md` 查逐轮工作与实测TTFT。每轮仅生成1token、没有重跑工具；累计复用KV逻辑字节2404122624不是物理驻留峰值。Agent、干扰和整段时间分列，单次共享GPU串行回放不证明在线TTL或混合排队收益。',
           '> **实验 8-4')
    insert('08-单实例推理.md', 'C45-kv-quality',
           '[真实BF16 KV](../calculations/results/kv-quality-bf16.md)、[原FP8路径](../calculations/results/kv-quality-fp8.md)、[FP8 KV＋BF16 Q控制](../calculations/results/kv-quality-fp8_qbf16.md)导入实验8-8的25封存文件，核对三组各97调用／64正式请求、文档答案、独立校准与scale冻结，控制组实际36层Q为BF16且KV scale匹配。自然精确答案28/32、26/32、28/32，只有八个不同任务，不能按32独立样本解释。'
           '全部正式自然输出46token并stop，无长度截断；固定64输出另计时。长文档四并发自然正确6/8、4/8、6/8，但同总分仍有失败身份变化；JSON保留逐请求判定与跨格式差异。'
           '实际BF16／FP8池5461／10922块、87376／174752token槽，三组唯一storage均12884115456bytes；固定12GiB预算下FP8扩槽，不是实际分配减半。运行 `python3 calculations/calc.py kv-quality --run fp8_qbf16 --format md` 查分条件质量与时间；原FP8还改变Q量化，不能把差异全部归于KV位宽。共享GPU、两轮与Q回调开销限制时间排名，未含修正失败答案成本。',
           '> **实验 8-8')
    insert('08-单实例推理.md', 'C45-weight-offload',
           '[九层FFN卸载](../calculations/results/weight-offload-book.md)用官方Qwen8每层150994944参数／288MiB，卸载层3/7/…/35共2.53125GiB，一组缓冲扣后净省2.25GiB、等于两条8K KV。[两组缓冲](../calculations/results/weight-offload-two-slots.md)净省1.96875GiB、只够一条并余0.84375GiB。'
           '教学24GiB/s单向链路每forward复制105468750ns，各层计算1ms时安全预取一／两槽完整完成114468750／106468750ns，对照纯计算36ms；更多槽不减少复制字节。'
           '[384GiB/s](../calculations/results/weight-offload-fast-link.md)、[双pass环回](../calculations/results/weight-offload-wrap.md)、[batch4](../calculations/results/weight-offload-batch4.md)、[2048-token prefill](../calculations/results/weight-offload-prefill.md)分别改变供给／生命周期／摊销。运行 `python3 calculations/calc.py weight-offload --format md` 查逐层复制和消费时刻；同槽下次复制等待前次消费层结束，首轮填充与末层消费都计入。时间为教学独立资源调度，不证明真实prefetch／UVA重叠，重复pass不是历史增长请求。',
           '> **实验 8-7')
    insert('08-单实例推理.md', 'C45-kv-codec',
           '[KV实际块格式](../calculations/results/kv-codec-book.md)按官方GQA与GGML每32值Q8_0=34bytes、Q4_0=18bytes，Qwen8 8K BF16/Q8_0/Q4_0分别1152/612/324MiB，scale元数据不可省略。教学有效带宽1TB/s、解码固定100us＋每值0.001ns、新增编码20us，Q4融合省144347.136ns，Q8反而多157679.616ns。'
           'Q4长历史持续获益从3717位置开始，[1K历史](../calculations/results/kv-codec-short.md)不够；[更低转换成本](../calculations/results/kv-codec-cheap-conversion.md)及[Qwen235几何](../calculations/results/kv-codec-qwen235.md)另列。物化解码另加完整BF16历史一次写／一次读及buffer，不能套融合流量。'
           '运行 `python3 calculations/calc.py kv-codec --format md` 查看码值／scale、追加、路径成本和精确盈亏区间。时长输入为教学假设，量化存储不等于Attention执行精度；未验证质量、真实后端或GPU转换速度。',
           '> **实验 8-8')
    insert('08-单实例推理.md', 'C45-gguf-layout',
           '[实际Q2_K文件头](../calculations/results/gguf-layout-q2k.md)与[Q4_K_M文件头](../calculations/results/gguf-layout-q4km.md)读取五分片，逐一匹配官方Qwen235的1131张量、235093634560参数。Q2_K实际混用F32/Q2_K/Q3_K/Q4_K/Q6_K，Q4_K_M混用F32/Q4_K/Q6_K；名称不等于全模型位宽。'
           '按固定GGML官方块结构：每256值Q2_K84bytes（64码值+20尺度／最小值）、Q3_K110、Q4_K144、Q6_K210。Q2_K张量载荷85684996096bytes，其中尺度元数据16506720256，文件头／padding另6006016；Q4_K_M载荷142148069376，其中尺度元数据14985244672，头／padding另6006112。'
           '运行 `python3 calculations/calc.py gguf-layout --variant Q4_K_M --format md` 查实际类型和逐片字节守恒，JSON保留每张量形状／类型／offset。只保存头部、未核验完整量化载荷或运行解包；参数完整不证明质量，文件布局不代表运行时重打包驻留。',
           '> **实验 8-7')
    insert('08-单实例推理.md', 'C45-gguf-inventory',
           '[Qwen235实际GGUF清单](../calculations/results/gguf-inventory-8k.md)锁定量化发布者unsloth revision09e11417的19变体72分片，逐片核对序号集合及API／LFS大小。Q2_K两片合85691002112bytes，UD-Q2_K_XL为88014818560，Q4_K_M三片合142154075488；不能用变体名称位宽乘参数量代替这些总文件字节。'
           '教学96×10^9总预算扣8GiB预留后87410065408bytes；官方Qwen235 BF16每KV token192512bytes，8K单请求1577058304bytes，整文件各占一份预算的情景下Q2_K仅余1请求，UD-Q2_K_XL文件本身已超预算。'
           '[32K](../calculations/results/gguf-inventory-32k.md)、[不扣预留](../calculations/results/gguf-inventory-no-reserve.md)、[192GB预算](../calculations/results/gguf-inventory-192gb.md)另列；运行 `python3 calculations/calc.py gguf-inventory --format md` 查逐片大小与发布LFS哈希。这里只下载目录元数据，未核验完整载荷；文件字节不等于mmap实际驻留／重打包副本，预留不是实测；Q2_K／Q4_K_M张量类型与文件头开销另见GGUF布局复算。',
           '> **实验 8-7')
    insert('08-单实例推理.md', 'C46-service-replay',
           '[真实交付SLO复算](../calculations/results/service-replay-chunk512.md)从实验8-2四组72请求锁定13文件，逐项核对输入、运行源码、配置差异与完整输出token一致。新增教学阈值TTFT≤300ms、E2E≤2000ms、客户端平均TPOT≤20ms，同一请求联合判断；每组18请求、2016输出。'
           '[chunk8192](../calculations/results/service-replay-chunk8192.md)、[nochunk8192](../calculations/results/service-replay-nochunk8192.md)、[graph512](../calculations/results/service-replay-graph512.md)与chunk512的达标数分别13／13／8／9；各组计时达标吞吐分别1.917974／1.876872／1.070820／1.193452请求/秒。'
           '分母为各轮最早实际提交到最后输出的窗口之和，排除轮间休息和启动，不能等权平均每轮速率。运行 `python3 calculations/calc.py service-replay --format md` 查逐请求／逐轮；平均TPOT不是逐token尾延迟，交付事件可能合并，客户端与引擎时钟各自相减。这里只评估计时条件，未证明任务质量或生产SLO，共享GPU固定执行顺序也不支持微小差异的稳定胜负。',
           '> **实验 8-9')
    insert('08-单实例推理.md', 'C42-iteration-batching',
           '[固定批次](../calculations/results/iteration-batching-fixed.md)、[连续补位](../calculations/results/iteration-batching-continuous.md)、[decode优先分块](../calculations/results/iteration-batching-chunked.md)复放相同4请求，官方Qwen8工作2636833882112矩阵FLOPs、188已计算输入位置和16输出保持一致。固定／连续／分块分别12／8／12迭代，教学完成317004／277004／317004ns，最大ITL12146／147274／28945ns；连续补位让长prefill更早进入，同时扩大短decode间隔。'
           '教学步成本为10000ns＋新token数×1000ns＋有效因果配对数×1ns，不是GPU校准。分块预算32、单prefill块最多16、活跃最多2；只在迭代边界接纳，固定批次整组结束再补位。'
           '[20MiB KV准入](../calculations/results/iteration-batching-capacity.md)按prompt+output-1预留、FIFO不绕过队首；实际KV每步分配新行、结束请求释放，最新输出仍pending。运行 `python3 calculations/calc.py iteration-batching --format md` 查逐步计划及请求TTFT／ITL；不把教学时间或输出数量一致当作真实吞吐／质量证据。',
           '> **实验 8-2')
    insert('08-单实例推理.md', 'C42-batch-reuse',
           '[H100／2K batch账](../calculations/results/batch-reuse-h100-2k.md)按官方Qwen8 BF16完整权重16381470720bytes、理想每批共享读取15136811008bytes（embedding逐请求查行）、KV每token147456bytes。扫描1/4/16/64，2K旧KV读达到共享权重需batch51，8K需13；这不同于计算／带宽交叉点。'
           '[H100／8K](../calculations/results/batch-reuse-h100-8k.md)、[4090／2K](../calculations/results/batch-reuse-4090-2k.md)、[4090／8K](../calculations/results/batch-reuse-4090-8k.md)严格选BF16输入／FP32累加／dense Tensor峰值，四场景均无有限计算主导交叉点。标称80／24GB、workspace=0时2K容量上限210／25，8K为52／6；不可行行不给可运行吞吐。'
           '[无历史对照](../calculations/results/batch-reuse-no-history.md)另算交叉点；运行 `python3 calculations/calc.py batch-reuse --format md` 查逐batch矩阵、KV和节省权重读取。理想权重读一次／旧KV读一次，未计中间激活及tile重读，容量不代表实际引擎可用，资源下界不代表TTFT或SLO。',
           '> **实验 8-1')
    insert('08-单实例推理.md', 'C42-chunk-history',
           '[固定块长的实测与工作复算](../calculations/results/chunk-history-book.md)核对实验8-2补测15个封存文件，11次8K请求共176个512-token块、另排除11次空execute。首／末块有效因果配对131328／4063488（5291/171倍），官方backbone矩阵7189926248448／9509208588288 FLOPs（62977/47617倍），实测区间中位25.300640／35.070015ms。'
           '配对末／首比例中位1.388425，与两个中位数之比1.386132分列；16块矩阵和133593078693888等于整段8K工作。运行 `python3 calculations/calc.py chunk-history --format md` 查逐历史位置，JSON保留176个样本。CUDA event覆盖execute_model而非纯attention；外部logits／采样不计，采用head=none矩阵账。共享GPU单引擎重复，历史／内容／末块处理并未独立控制，不把配对比例当作访存或时间比例。',
           '> **实验 8-2')
    insert('08-单实例推理.md', 'C44-dflash-work',
           '[官方DFlash草稿账](../calculations/results/dflash-work-book.md)固定z-lab/Qwen3-8B-DFlash-b16 revision9b41424b，配置与58张量头逐项匹配：独立草稿1048626432参数、BF16权重2097252864bytes；目标embedding与输出头共享，不能重复算独立参数。5层目标特征先经20480→4096融合，5个草稿层使用非因果块注意力。'
           '已有1020行草稿KV、新目标特征4行、块长16（15个候选）时，新增特征163840bytes，草稿矩阵51909754880 FLOPs含共享输出头，目标验证251923005440 FLOPs。草稿KV每context token20480bytes，峰值21299200，丢弃16行噪声KV327680后保留20971520bytes。'
           '[首轮1024特征](../calculations/results/dflash-work-first.md)、[块长4](../calculations/results/dflash-work-block4.md)、[32K上下文](../calculations/results/dflash-work-long.md)另列。运行 `python3 calculations/calc.py dflash-work --format md` 查M/K/N和逻辑operand尺寸。只下载配置、实现与权重头，未下载完整权重或执行GPU；非矩阵算术、实际HBM、采样质量和时长仍待核。',
           '> **实验 8-5')
    insert('08-单实例推理.md', 'C44-speculative-budget',
           '[有限输出预算](../calculations/results/speculative-budget-book.md)固定16输出、普通decode1ms/token，草稿1/2/4的教学轮成本1.1/1.25/1.5ms，显式连续接受直方图对应条件接受3/4，首次准备2ms。逐状态选择的期望完成10.202356ms，固定4草稿10.580953ms，普通decode16ms；已准备且剩余1/2/3/至少4输出时分别选择普通decode／1／2／4草稿。'
           '[单输出](../calculations/results/speculative-budget-short.md)不启动草稿，[准备2秒](../calculations/results/speculative-budget-expensive-setup.md)选择普通decode，[零准备成本](../calculations/results/speculative-budget-prepared.md)另列。'
           '运行 `python3 calculations/calc.py speculative-budget --format md` 查看逐剩余长度的动作、期望时长与固定策略。状态包含是否已准备，只在首次起草计setup；末轮截断不撤销已执行工作。小规模全部策略枚举独立核对Bellman结果。最优仅针对给定平稳成本／分布和固定输出上限，不代表真实模型在线学习、随机EOS或完整Agent任务速度。',
           '> **实验 8-5')
    insert('08-单实例推理.md', 'C44-speculative-sampling',
           '[拒绝采样精确枚举](../calculations/results/speculative-sampling-book.md)使用教学目标p=(1/2,1/3,1/6)、草稿q=(1/6,1/3,1/2)，接受质量之和2/3；拒绝后从归一化正残差(1,0,0)采样，输出逐项等于p。若拒绝后直接从原p重采样，输出为(1/3,4/9,2/9)，总变差1/6。'
           '[全接受](../calculations/results/speculative-sampling-equal.md)、[不相交支持](../calculations/results/speculative-sampling-disjoint.md)、[零提议概率](../calculations/results/speculative-sampling-zero-proposal.md)单列不可达分支。运行 `python3 calculations/calc.py speculative-sampling --format md`；225组有理数分布对穷举通过。这里只验证固定前缀单步概率质量，真实多token采样器、浮点实现和固定草稿检查点仍待验证。',
           '> **实验 8-5')
    insert('08-单实例推理.md', 'C44-speculative-round',
           '[投机单轮收支](../calculations/results/speculative-round-book.md)用官方Qwen目标、history1024、每轮4草稿，连续接受0/1/2/3/4的次数2/1/1/2/4：十轮起草40、接受25，草稿接受率5/8，平均接受2.5，包含补偿／额外token后平均交付3.5。教学起草40us＋验证100us＋提交10us，对照50us/token，整体42.857143us/token、速度比7/6；逐轮time/token等权平均62us不能替代总时间/总产出。'
           '目标验证5行含待处理token，单轮78709719040矩阵FLOPs；十轮验证787097190400，对照同35输出串行550959775744。保留最新输出仍待处理的状态约定，新增5条KV按实际交付数保留，其余回滚。'
           '[剩余输出上限1](../calculations/results/speculative-round-output-limit.md)每轮只交付1，验证工作不减，速度比1/3；[昂贵草稿](../calculations/results/speculative-round-expensive-draft.md)和[零接受](../calculations/results/speculative-round-no-accept.md)另列。运行 `python3 calculations/calc.py speculative-round --format md` 复算。直方图和时长是教学输入，未实现拒绝采样或固定DFlash/EAGLE草稿模型。',
           '> **实验 8-5')
    insert('12-端边云协同.md', 'C79-setup-lifetimes',
           '[图像setup存活](../calculations/results/image-generation-book.md)把timestep helper临时张量逐次放进原分支事件图，声明eager峰值为512+2560×B bytes；B1为3072B，[B4](../calculations/results/image-generation-setup-batch4.md)为10752B。它们均未抬高该例原边界图峰值，因为与最终VAE峰值不同时发生，不能把独立峰值相加。[形状缓存暖态](../calculations/results/image-generation-shape-cache-warm.md)只省对应位置构造，模型初始化、请求setup和NFE内步骤分别列账；完整allocator与其他内部workspace仍未知。',
           '> **实验 12-3')
    insert('12-端边云协同.md', 'C81-omni-vision',
           '[Omni视觉编码](../calculations/results/omni-vision-book.md)独立使用1152宽、4304 FFN、27层及4608→4608→2048 merger，640²图的矩阵1737739468800FLOPs；400个语言位置交付final与3份DeepStack共6553600B。位置表2304来自锁定配置类默认，插值跟随参数dtype，RoPE接口为FP32。[图像/视频混合](../calculations/results/omni-vision-mixed.md)按每项每时间块的空间patch平方相加，不对打包总长度求平方；[全命中](../calculations/results/omni-vision-all-hit.md)编码为零但仍交付完整特征并进入Thinker。[视频时间](../calculations/results/omni-vision-video-time.md)按显式秒间隔与Thinker每秒13位置计算，不能拿vision tokens_per_second字段替代。运行 `python3 calculations/calc.py omni-vision-encoding --format md`；预处理、完整Thinker前向与实测另计。',
           '> **实验 12-3')
    insert('12-端边云协同.md', 'C81-omni-understanding',
           '[Omni完整理解请求的已计阶段](../calculations/results/omni-understanding-book.md)默认一图640²、1000有效mel帧与128文字/控制位置，合计658位置；32输出由prefill及31次decode产生，矩阵6327647059968FLOPs，最终689位置KV67731456B。固定Thinker源码对所有prefill行运行head，不能缩成最后一行。[全encoder缓存命中](../calculations/results/omni-understanding-all-hit.md)仍保留全部语言位置与DeepStack；[图像/视频/音频混合](../calculations/results/omni-understanding-mixed.md)分编码器后替换placeholder，不重复追加。[短音频缓存](../calculations/results/omni-understanding-short-audio-cache.md)明确miss重组后的padding/attention窗口，缓存身份必须包含执行条件，位置相同不证明特征相同。运行 `python3 calculations/calc.py omni-understanding --format md`；路由为声明分布，sampling、mRoPE索引、原始媒体预处理及实测仍未计。',
           '> **实验 12-3')
    insert('02-模型架构.md', 'C06-sequence-dependencies',
           '[四token三层逐矩阵与数值复算](../calculations/results/sequence-dependencies-book.md)用固定可见教学权重、D4/FF8/单头/FP64：RNN已知四token768矩阵FLOPs、固定历史96B；因果Transformer3552FLOPs、KV768B。给定第五token，重算/复用分别为RNN960/192、Transformer4560/1008FLOPs，后者KV增长至960B。十次同模型前缀重算与状态复用输出检查最大绝对误差0；不拿两种模型输出作等价比较。完整依赖边和KV历史访问图见JSON，单位cell关键路径6与3不代表实测时延。运行 `python3 calculations/calc.py sequence-dependencies --format md`；教学模型无norm/bias/词表head，非真实checkpoint，非矩阵与运行峰值另计。',
           '> **实验 2-1')
    insert('01-初识 AI Infra.md', 'C04-tpu-demand',
           '[TPU历史需求锚点](../calculations/results/tpu-demand-book.md)按封存论文第2节的2013年预测：每日3分钟语音搜索会使数据中心计算需求翻倍。将原容量归一为1并明确假设线性扩展，[1分钟](../calculations/results/tpu-demand-one-minute.md)、3分钟、[6分钟](../calculations/results/tpu-demand-six-minutes.md)对应增量1/3、1、2，总量4/3、2、3。[显式教学容量](../calculations/results/tpu-demand-supplied-capacity.md)才代入1000服务器当量与给定4倍增量工作供给；并非历史服务器数，已有工作不随语音加速比一起缩小。论文10倍性价比设计目标不当吞吐倍数。运行 `python3 calculations/calc.py tpu-demand --format md`；实际人数/服务器/成本、供数与延迟保持未知。',
           '> **实验 1-5')
    insert('01-初识 AI Infra.md', 'C04-nic-budget',
           '[历史转发核数](../calculations/results/nic-budget-book.md)按40Gbps单向、64B帧加20B线时开销得1250000000/21包/秒，约59.524Mpps；论文10/20Mpps每核基线对应忙核当量125/21与125/42，专用整数6/3核。[半线速](../calculations/results/nic-budget-half-line.md)为3/2整数核；[CPU仅用一半](../calculations/results/nic-budget-half-cpu.md)需12/6核。等包数的[64/1518B混合](../calculations/results/nic-budget-mixed.md)以平均每包811B线时为分母，不能平均两种线速包率。[卸载对照](../calculations/results/nic-budget-offload.md)即使移除全部声明转发工作，给定PCIe载荷/供给与在途槽位仍约束请求率。运行 `python3 calculations/calc.py nic-budget --format md`；基线来自封存作者论文4.2.1，分布/封装/利用率与PCIe为显式教学条件，不声称完整虚拟化、线性扩展或实测卸载收益。',
           '> **实验 1-6')
    insert('12-端边云协同.md', 'C80-wan-front-back',
           '[Wan视频前后阶段](../calculations/results/video-generation-wan.md)主例30步各执行conditional/unconditional两次DiT，共60次；循环外补文本与VAE：官方TI2V5B无输入图像路径的positive/negative分别执行一次UMT5，固定512行padding后再裁有效hidden，两次9689446219776矩阵FLOPs，不乘去噪步数。VAE按首块1帧、后续每latent4帧解码，31latent得到121帧768×1344；完整卷积和空间QK/PV合计2303929089294336FLOPs。固定官方meta执行与另一形状复验所有矩阵，未使用权重或实测GPU；RMS/SiLU、copy/上采样等已另列非矩阵primitive账，36形状基点及3个留出meta验证支持固定源码的形状计数；比较/exp/sqrt与算术分开，接口bytes与矩阵账可能重叠，实际工作区与时延仍未知。',
           '> **实验 12-3')
    insert('02-模型架构.md', 'C14-chat-agent-figure',
           "[图2-8原Chat/Agent六面板](../calculations/figures/chat-agent/figure.svg)逐次展示4Chat与4Agent的输入/命中/返回长度、Agent应用时序、reasoning标记、工具毫秒和声明保留KV。首轮因长度上限结束、未见reasoning结束marker，保留边界未知；其余marker为首个达到该token数的流事件，不当GPU阶段边界。KV仅为工具等待期间保留最终逻辑状态的条件柱形，不是观测页寿命。"
           "[PNG](../calculations/figures/chat-agent/figure.png)、[PDF](../calculations/figures/chat-agent/figure.pdf)、[数据](../calculations/figures/chat-agent/data.json)可导出；`python3 calculations/calc.py plot-chat-agent`复现（需Matplotlib）。原始观测、特殊标记和条件状态分别标注，不用平均值掩盖长轮次或短工具等待。",
           '> **图 2-8')
    insert('02-模型架构.md', 'C13-granularity-selection',
           "[同条件专家颗粒度选择](../calculations/results/granularity-selection-default.md)固定16token、TP2/EP4和8192位置，对比64/3072/k4与256/768/k16。最大rank必要容量为67,708,148,736/67,855,997,952字节，两者之间仅粗粒度通过；专家FLOPs相同，但操作数字节为56,824,922,112/56,935,809,024。消息均为108,017,280字节，所以共同fabric速率不会产生通信排序翻转。router GEMM及其操作数成本另加，FP32选择工作保留。"
           "按声明的串行服务模型，令U为未计阶段耗时，细粒度胜出当且仅当U_f−U_c小于已计成本差额；U默认未知，不返回完整条件排名。[细计算150TF/s](../calculations/results/granularity-selection-fine150.md)、[额外1微秒](../calculations/results/granularity-selection-declared-small-remainder.md)与[额外100微秒](../calculations/results/granularity-selection-declared-large-remainder.md)展示条件翻转。两U明确给定后先排除必要容量失败项再比较；未训练变体仍不推等质量。"
           "运行 `python3 calculations/calc.py granularity-selection --format md`，`--inputs`指定有效计算/操作数/fabric速率及remaining_ns。GEMM接口不是物理HBM，必要容量不是可部署证明，串行情景不是实测请求延迟。此完成实验2-7有限条件汇总，质量/SLO/经济点证据另列。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C14-trace-cache-lifecycle',
           "[同轨迹缓存保留与取回](../calculations/results/trace-cache-default.md)使用四原Chat记录的三次转移，原token IDs公共前缀112/164/213与reported device命中相等；Qwen8 BF16 KV每token147456字节，对应16,515,072/24,182,784/31,408,128字节。仅声明在上一应用完成到下一次发送之间保留复用前缀，对该区间精确积分byte-seconds，不当作观测页寿命或完整请求峰值。"
           "host取回门槛为bytes/gap；remote经host还需扣除lookup和H2D，剩余窗口非正则无法在该串行模型下完成。[host50GB/s](../calculations/results/trace-cache-host50gb.md)和[lookup2ms](../calculations/results/trace-cache-lookup2ms.md)只改变条件取回，不修改原命中与算子账。默认25GB/s host仅首个转移可放入记录间隔；这要求提前知道复用前缀，不能冒充实际迁移或TTFT。"
           "运行 `python3 calculations/calc.py trace-cache-lifecycle --format md`。同一monotonic应用时钟的JSON十进制保留为分数，不宣称仪器精度；token前缀相同不证明物理页相同。实际页身份、寿命、迁移量与迁移时间仍未知。",
           '> **实验 2-9')
    insert('02-模型架构.md', 'C14-v4-mtp-forward',
           "[Flash单次MTP调用](../calculations/results/v4-mtp-first-call.md)以调用方提供的Block42输出和token IDs为输入，仅执行第43层、ratio0的MTPBlock。e_proj处理BT行、h_proj处理4BT行，两者合计10BTH²；共享词表只投影每序列末位置。B1/T1默认1,796,997,120矩阵FLOPs，其中共享head为1,059,061,760。自有6,610,048,891逻辑参数与1,575条官方权重记录相符，checkpoint payload为3,593,787,756字节，不含共享embedding/head驻留。"
           "[B2/T16](../calculations/results/v4-mtp-b2-prefill16.md)、[T129](../calculations/results/v4-mtp-prefill129.md)、[历史128](../calculations/results/v4-mtp-history128.md)分别核批量、窗口溢出和独立ring单槽写入。逐矩阵、norm/mHC/量化标量和特殊操作单列；接口字节为部分操作数，完整HBM与运行峰值未知。"
           "运行 `python3 calculations/calc.py v4-mtp-forward --format md`，用`--inputs`指定batch/tokens/start_pos/routing。输入特征对齐由调用方声明，不额外执行主干，不由本次调用推断草稿步数、接受率、验证/回滚或推测解码加速比。",
           '> **实验 2-9')
    insert('02-模型架构.md', 'C14-request-hardware-bridge',
           "[四模型原请求到H100供给](../calculations/results/request-h100-original.md)保持S0/P128/G4/B1的原请求账，逐调用将可证矩阵精度匹配官方dense峰值；路由或稀疏attention不等于2:4结构化稀疏。Qwen的2,549,809,152 PV FLOPs因FP32 P与BF16 V保持混合精度未决；K3非router的26,973,105,000,448矩阵FLOPs也不强套BF16/FP8。V4逐模型矩阵和动态attention组分类，FP4存储转换后的FP8执行不使用FP4峰值。"
           "[G1](../calculations/results/request-h100-first-output.md)核首输出边界；[显式FP32 vector供给](../calculations/results/request-h100-vector-provider.md)把FP32矩阵和标量合到同一资源；[低容量条件](../calculations/results/request-h100-low-capacity.md)保留必要容量失败，比较上限不改官方规格。checkpoint表示、源码cache分配和可运行容量分开；未知特殊操作、物理HBM与完整时延不当零，未指定并行放置也不虚构链路。"
           "运行 `python3 calculations/calc.py request-hardware-bridge --format md`，`--inputs`选择已声明条件。已知资源约束的max不代表BF16/FP8共享Tensor单元能同时达到各自峰值；此为条件资源桥接，不是跨模型质量或实测性能排名。",
           '> **实验 2-9')
    insert('02-模型架构.md', 'C14-sealed-chat-resource',
           "[封存Chat长度到Qwen8资源账](../calculations/results/sealed-chat-known-prefill.md)选原始四条capture，累计753输入token、报告489缓存token、79返回ID（含EOS），不用重放条数替代原请求。按声明的逻辑前缀映射计算已知输入阶段，合计3,692,317,638,656矩阵FLOPs；实际模型调用次数、采样步骤和缓存恢复路径仍未知。"
           "[显式串行返回ID策略](../calculations/results/sealed-chat-declared-serial.md)另声明每返回ID对应一步，得79次条件逻辑forward、4,836,064,624,640矩阵FLOPs；仍不把这些次数写成观测值。首输出来自prefill，后续只做G−1次decode，最后返回ID不再额外写KV。逐调用矩阵、已计接口及状态保留，walltime不当计算时间，工具等待为未知/不适用。"
           "运行 `python3 calculations/calc.py trace-resource-bridge --format md`，`--inputs`选择generation_policy。此连接说明如何将真实记录的可证长度代入模型公式；完整执行重建还需逐step输入、cache命中位置/恢复及采样日志。",
           '> **实验 2-9')
    insert('02-模型架构.md', 'C13-architecture-tile-work',
           "[深窄/浅宽的tile工作量](../calculations/results/architecture-tile-tail129.md)连接已有48层×4096宽与24层×5120宽变体，每个投影、FFN、QK/PV及每序列最后位置输出头均列M/N/K、执行次数、有效工作、矩形额外工作与tile尾部补齐。因果attention被矩形覆盖的额外槽位不与tile padding混算。"
           "[128位置对齐](../calculations/results/architecture-tile-aligned128.md)、[8K历史decode](../calculations/results/architecture-tile-decode8k.md)与[自定义tile/速率](../calculations/results/architecture-tile-custom-rate.md)给出条件服务时间和排序翻转所需的精确速率比。运行 `python3 calculations/calc.py architecture-tile-work --format md`。tile由调用者声明，不代表已验证官方kernel；有效/补齐FLOPs比不是实测Tensor Core利用率，未训练质量与完整请求延迟仍未知。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-architecture-shapes',
           "[图2-7架构形状伴图](../calculations/figures/architecture-shapes/figure.svg)由冻结结果生成六面板：Dense每条代表一层，同列条宽随H变化；MoE每条代表一层中的一个专家，同列宽随F变化，橙色为首条合成路由的真实专家ID集合。标出gate/up/down存储形状、完整参数与差额，router变化不被专家预算相等掩盖。"
           "[PNG](../calculations/figures/architecture-shapes/figure.png)、[PDF](../calculations/figures/architecture-shapes/figure.pdf)及[原始图数据](../calculations/figures/architecture-shapes/data.json)可导出；运行 `python3 calculations/calc.py plot-architecture-shapes`。两列比例不同，所示为FFN/专家矩阵而非全部算子；只有基线为发布配置，变体未训练，不据图推断同质量或运行速度。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-capacity-curves',
           "[图2-7容量阶梯曲线](../calculations/figures/capacity-curves/figure.svg)从四档模型、三格式的逐rank冻结数据生成；Dense为TP8，235B为TP2/EP4，统一8192保留位置、BF16 KV及每卡2GiB工作区。每个整数并发n的阈值取max_rank(权重+工作区+n×KV)，不用平均显存或线性插值；24/48/80 decimal GB点与原结果一致，零并发也包含权重放不下。"
           "[PNG](../calculations/figures/capacity-curves/figure.png)、[PDF](../calculations/figures/capacity-curves/figure.pdf)及[完整曲线数据](../calculations/figures/capacity-curves/data.json)可导出，运行 `python3 calculations/calc.py plot-capacity-curves` 重画（可选Matplotlib）。这是容量边界，不是吞吐/质量比较；图2-7架构形状伴图另由对应冻结矩阵结果生成。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-expert-granularity',
           "[专家颗粒度基线](../calculations/results/qwen235-granularity-baseline.md)固定真实Qwen235B的128专家、FFN宽1536、top-k8；比较[64/3072/k4](../calculations/results/qwen235-granularity-coarse64.md)与[256/768/k16](../calculations/results/qwen235-granularity-fine256-k16.md)。这两变体保持专家总参数及激活专家参数，16token专家矩阵工作同为454,192,791,552 FLOPs；但router改变，使完整参数分别少24,641,536和多49,283,072，不能称严格等参。"
           "[256专家仍选8](../calculations/results/qwen235-granularity-fine256-k8.md)把矩阵工作减半至227,096,395,776 FLOPs；[160专家对齐](../calculations/results/qwen235-granularity-aligned160.md)保留宽度取整误差，[热点](../calculations/results/qwen235-granularity-hot.md)保留负载倾斜。每矩阵M/N/K、逐专家token数、TP分片、EP消息目的集合和必要容量逐项输出。"
           "运行 `python3 calculations/calc.py qwen235-expert-granularity --format md`，`--inputs`指定experts/top_k等条件。只有基线为真实配置，其余未训练；专家工作减少不证明同质量或更快。选路标量、真实tile/带宽/运行峰值及完整请求时延仍另计。",
           '> **实验 2-7')
    insert('02-模型架构.md', 'C13-qwen235-eight-way',
           "[Qwen235B的TP8完整KV头复制](../calculations/results/qwen235-placement-tp8-kv-replica.md)把四个KV头映射到八rank，每头两份；每rank每8192位置请求394,264,576B KV，八卡合计是逻辑KV的两倍，不能把完整头继续平分。每卡80 decimal GB、2GiB工作区下，声明BF16/8bit/4bit格式的条件并发为47/120/158。"
           "[EP8专家均分](../calculations/results/qwen235-placement-ep8-expert-partition.md)则每rank16个完整专家，attention及四个KV头在八个EP rank复制，每rank每请求1,577,058,304B KV；同预算并发为3/25/36。两者都是同一批请求，不能再乘八；低位是声明格式，完整运行时与质量另需证据。用 `qwen235-placement --inputs` 指定tp/ep可复现。",
           '> **实验 2-7')
    insert('06-超节点.md', 'C33-qwen235-execution',
           "[Qwen235B同批专家执行](../calculations/results/qwen235-ep4-tp2-balanced-80gb.md)从真实专家矩阵与逐token路由表，计算EP/TP/PP每rank工作、消息token集合及必要容量。默认TP2/EP4、16token的专家矩阵工作454,192,791,552 FLOPs，通信108,017,280B；输入在EP之间已有副本，因此该条件的dispatch为零，TP部分和、EP归约及输出广播仍逐项计。"
           "[热点路由](../calculations/results/qwen235-ep4-tp2-hot-80gb.md)、[PP2](../calculations/results/qwen235-ep4-pp2-48gb.md)、[24GB/32K](../calculations/results/qwen235-ep4-tp2-24gb-32k.md)与[两请求](../calculations/results/qwen235-ep4-tp2-two-requests.md)核分片、倾斜和容量。[相同直方图的纯分组](../calculations/results/qwen235-equal-hist-pure.md)与[混合分组](../calculations/results/qwen235-equal-hist-mixed.md)保持专家工作相同，消息字节仍不同。"
           "运行 `python3 calculations/calc.py qwen235-execution --format md`，`--inputs`指定拓扑及真实route记录。此为声明阶段屏障下的专家执行与通信子账，attention/router/head及实际工作区未完整计入；容量通过仅必要条件，阶段服务速率是输入假设，不能当完整请求实测延迟。",
           '> **实验 6-3')
    insert('10-训练系统.md', 'C56-training-input-supply',
           "[训练输入供给](../calculations/results/training-supply-default.md)把预token样本按next-fit打包，逐padded token的IDs/labels/valid/segment共21B；存储读取→单CPU准备→H2D→消费与checkpoint快照/写入共享事件图。Qwen8真实参数对应声明14P状态114,670,295,040B，有限host/device/snapshot槽给出反压、预约存活与byte-seconds。"
           "[关闭checkpoint](../calculations/results/training-supply-no-checkpoint.md)、[共享存储阻塞](../calculations/results/training-supply-shared-starvation.md)、[独立存储](../calculations/results/training-supply-independent-storage.md)与[CPU瓶颈](../calculations/results/training-supply-cpu-bottleneck.md)分别比较竞争来源。训练结束与最后写入完成时间分开；设备等待包含启动、输入及checkpoint槽等待，不能全称输入饥饿。"
           "运行 `python3 calculations/calc.py training-input-supply --format md`，`--inputs`提供样本token/存储bytes/CPU准备时间及资源参数。服务时间和带宽是显式假设，whole-write非抢占存储模型不等于实际IO调度；预约峰值不等于allocator峰值，也不宣称实际文件系统持久化保证。",
           '> **实验 10-7')
    insert('12-端边云协同.md', 'C77-omni-pcm-preprocess',
           "[Omni PCM到mel前处理](../calculations/results/omni-pcm-1s.md)把已解码16kHz波形的padding、Hann窗、STFT、功率谱、mel投影、log归一化和mask选取逐项列出。一秒波形产生100个有效mel帧，随后encoder产生13个位置；前处理已知矩阵5,145,600 FLOPs、标量87,306 FLOPs，语义读1,790,168B、写1,277,400B，FP32 encoder入口51,200B。"
           "[混合长度](../calculations/results/omni-pcm-mixed.md)、[hop尾部](../calculations/results/omni-pcm-hop-tail.md)和[配置上限差异](../calculations/results/omni-pcm-serialized-limit.md)分别核对mask与截断。固定构造器实际默认30秒，不能照JSON中的300秒直接计算；Hann底层401元素与两次max返回后丢弃的int64索引也占写入。"
           "运行 `python3 calculations/calc.py omni-audio-preprocess --format md`，`--inputs`指定sample_lengths及入口元素字节。FFT与复数abs后端内部工作保持未知，独立混合基FFT参考另列；下游encoder及Thinker需继续计算，不重复计入此前处理账。语义bytes不等于实测内存流量，音频解码、重采样和运行峰值仍另计。",
           '> **实验 12-3')
    insert('12-端边云协同.md', 'C81-omni-audio-encoder',
           '[Omni输入音频编码](../calculations/results/omni-audio-encoder-book.md)把已准备好的1000个有效mel帧经100帧CNN分块、三层卷积、32层双向attention及投影，得到130个Thinker位置、532480bytes，211204423680矩阵FLOPs；这些位置随后才参与Thinker语言计算。[801帧](../calculations/results/omni-audio-encoder-boundary.md)产生105位置并分成104+1两个attention段，而非全局ceil(N/8)。[混合批](../calculations/results/omni-audio-encoder-mixed.md)先统一chunk padding，[501个chunk](../calculations/results/omni-audio-encoder-chunk-batches.md)再按最多500块卷积。[eager路径](../calculations/results/omni-audio-encoder-eager.md)因固定源码未传分段mask单列，不能当作默认varlen路径的语义等价替换。运行 `python3 calculations/calc.py omni-audio-encoder --format md`；原始波形预处理、完整Thinker请求与实测仍另计。',
           '> **实验 12-3')
    insert('04-加速器架构.md', 'C24-paired-projection-cost',
           "[配对投影费用条件](../calculations/results/paired-projection-unknown.md)复用实验4-6的同BF16夹具、官方Qwen8 Q投影形状与原墙钟记录。每个样本是16次调用平均，11组中位数不等于单次延迟或p95。reused模式下，RTX/Mac小时整机费用率持平比分别约3.8675（M1）与56.2154（M256）；同服务窗口的平均整机功率比有相同条件门槛。"
           "默认费用/功率未知，排名与焦耳代理留空；[声明2倍费用率](../calculations/results/paired-projection-declared-2x.md)及[10倍费用率](../calculations/results/paired-projection-declared-10x.md)仅演示代入。运行 `python3 calculations/calc.py paired-projection-cost --format md`，`--inputs calculations/scenarios/paired-projection-cost-example.json`导入假设。"
           "夹具不是checkpoint权重，质量与MPS内部累加精度未据此对齐；TDP不替代同期整机功率，也不把单投影时间费用代理升级为真实能耗或全生命周期成本。",
           '## 4.6 封装与专用化的边界')
    insert('04-加速器架构.md', 'C23-matrix-vector',
           "[QK—Softmax—PV交接](../calculations/results/matrix-vector-staged-rows32-slots2.md)以Qwen128维头计算完整128×128因果物化分数矩阵。FP32分数加BF16概率跨单元载荷98304B，中间写读路径服务196608B，一次传送的声明路径服务98304B；这些路径假设不映射为厂商实际专用接口。"
           "[整块交接](../calculations/results/matrix-vector-staged-rows128-slots1.md)完成于5118教学tick，32行分组一槽为5120、两槽3200、四槽仍3200；首次向量提前不等于最终更快。每组完整QK结束才可Softmax，不能消费K方向部分和；槽位保留至PV结束。"
           "运行 `python3 calculations/calc.py matrix-vector-handoff --inputs calculations/scenarios/matrix-vector-example.json --format md`。矩阵资源由QK/PV共享，各类向量操作按声明速率串行，两个交接方向共用接口；mask准备、cast、最终输出等未计工作保留边界，不把子账时序当完整内核实测。",
           '> **实验 4-4')
    insert('04-加速器架构.md', 'C23-v4-copy-coordinates',
           "[V4共享专家复制坐标](../calculations/results/v4-copy-coordinates-m32.md)从官方32×128×128 FP8内核枚举w1/w3/w2的A/B、scale和输出起点、offset、stride与重复读取。M32时每次GEMM有512个K轮次实例；w1/w3的A各搬运2097152B、B各8388608B，源级调用与字节分开。"
           "[M64对照](../calculations/results/v4-copy-coordinates-m64.md)中B常驻形状不变，但M分块使读取翻倍；不能把全局唯一权重大小代替分块重读。运行 `python3 calculations/calc.py v4-copy-coordinates --rows 32 --format md`。"
           "只接受对齐形状，FP8输入/权重、E8M0 scale、BF16输出和FP32累加分别标记。T.copy未被当作一条硬件指令，TMA descriptor数、整数地址指令和实测HBM仍未知；结果也不含量化、门控、全部层数及编译展开。",
           '> **实验 4-4')
    insert('04-加速器架构.md', 'C23-attention-input',
           "[Qwen注意力输入槽](../calculations/results/attention-input-base.md)把128维QK按K32分成4块，每块输入16KiB、1048576FLOPs，FP32累加器64KiB独立计量。声明带宽/计算率和在途延迟下，异步1/2/4/8槽完成于1280/768/704/704教学时间单位，8槽超过输入容量；同步寄存器中转总接口字节131072B，异步声明路径省去该中转，外部输入仍65536B。"
           "[矩阵速率翻倍](../calculations/results/attention-input-matrix-double.md)、[K16分块](../calculations/results/attention-input-tile-k16.md)与[一槽容量](../calculations/results/attention-input-capacity-one-slot.md)分别改变等待与可行集合。槽位从发起保留至矩阵消费结束，同刻可复用，不能在数据就绪时提前释放。"
           "运行 `python3 calculations/calc.py attention-input-pipeline --inputs calculations/scenarios/attention-input-example.json --format md`。逐块列发起、就绪、计算与释放；时间单位与服务率是教学条件，完成点仅QK累加器就绪，不含完整Softmax/PV或实际指令/同步开销。输入SMEM通过也不证明寄存器/累加器与完整内核可部署。",
           '> **实验 4-4')
    insert('04-加速器架构.md', 'C21-fa4-resources',
           "[FA4单SM资源配比](../calculations/results/fa4-qwen8-resource-balance.md)绑定正式论文与Qwen8的128维头，16矩形tile/供给场景逐项计算QK/PV矩阵、MMA操作数重复读取和指数。128×128×128基准为1024/768/1024周期；仅矩阵供给翻倍仍受1024周期指数限制，矩阵及指数同时翻倍后转为768周期SMEM限制。"
           "运行 `python3 calculations/calc.py fa4-resource-balance --format md`。SMEM128B/SM/cycle是论文引用的微基准分析输入，不是HBM带宽；PV的P从TMEM提供，不能将唯一QKV载荷替代MMA重复读取。这里取三项稳态资源下界的最大值，不含完整Softmax、因果对角块、依赖及流水开销，不代表实测kernel时延。",
           '> **实验 4-1')
    insert('04-加速器架构.md', 'C22-storage-generations',
           "[容量与带宽代际对照](../calculations/results/storage-generation-qwen8-235.md)固定官方Qwen8/235配置，54工作负载覆盖B1/8/32、最终8K/32K位置及BF16/8/4-bit声明格式。五产品分别只替换H100基准容量、只替换带宽及代入产品组合，共810对照。"
           "235B在4-bit、B8、8K位置时常驻权重123.14203648GB；均衡路由选中64专家、集中路由8专家，本步已计权重/KV接口载荷分别75.967159296GB和24.737405952GB，全部专家始终常驻。"
           "运行 `python3 calculations/calc.py storage-generation-comparison --format md`。三格式含逐行分组scale，embedding/head及KV保留BF16，工作区为声明2GiB。容量失败的条件服务预算为空；载荷/带宽不包含完整激活、转换或缓存访问，不能当作实测HBM或完整decode时延，低位质量未据此证明。",
           '> **实验 4-3')
    insert('04-加速器架构.md', 'C22-stage-resources',
           "[真实逐阶段资源界](../calculations/results/stage-resources-qwen8-b1-prefill128.md)将Qwen8与V4-Flash的实际算子按层汇总，分别计算各层资源最大值之和及合并全部工作后的全局最大值；这两者对应不同串行屏障假设。矩阵精度/累加/dense条件逐项准入，V4 routed权重虽存FP4，固定内核转换为FP8后执行GEMM，不能套FP4峰值。"
           "[显式特殊函数速率假设](../calculations/results/stage-resources-qwen8-assumed-special-baseline.md)下，Qwen128输入逐层串行界约7.216ms，全局合并界约6.842ms；矩阵、向量、接口带宽和exp供给各翻倍的场景分别比较。默认官方表缺少特殊函数速率时完整已计资源界留空，Apple/Huawei不匹配精度也不猜值。"
           "运行 `python3 calculations/calc.py stage-resource-bounds --format md`。25场景覆盖两模型B1/8、prefill128/512、decode8K/32K与三类硬件。未知容量不能取得容量资格；Qwen权重+KV仅必要容量，V4 checkpoint大小不能证明运行容量。接口bytes不是实测HBM，缺失工作/资源不会被调用者速率补齐，完整请求延迟仍未知。",
           '> **实验 4-5')
    insert('03-推理与训练负载.md', 'C19-v4-optimizer',
           "[V4优化器逐矩阵账](../calculations/results/v4-optimizer-flash-base-unresolved.md)从真实参数形状划分Muon、AdamW、外部router bias及未明确分组。Muon十次Newton–Schulz迭代逐次列出三次GEMM；对定向后的n×m矩阵，矩阵工作为10×(4n²m+2n³)，标量更新、特殊函数与状态另计。"
           "[Flash含MTP的显式分组](../calculations/results/v4-optimizer-flash-mtp-declared-row-muon.md)、[存储方向对照](../calculations/results/v4-optimizer-flash-stored-matrices.md)和[Pro显式分组](../calculations/results/v4-optimizer-pro-base-declared-row-muon.md)展示矩阵方向、wo_a分组及sink/head策略的影响。"
           "运行 `python3 calculations/calc.py v4-optimizer --format md`，`--inputs`指定策略。官方报告与本地副本按SHA绑定；默认保留未知组，显式策略仅给条件账。FP32参考与报告BF16迭代分开，不推定分布式所有权、实际分配或完整训练运行时。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-moe-training',
           "[V4单层MoE训练账](../calculations/results/v4-moe-training-balanced.md)在固定专家选择下连接router、shared及routed专家的全部输入/参数VJP，逐专家直方图决定三投影矩阵行数，clamp与F维路由权重另计。跨token专家参数梯度、router选中分数归一化与专家输出归并均保留；hash层固定ID不代表路由权重无梯度。"
           "[集中负载](../calculations/results/v4-moe-training-concentrated.md)、[hash层](../calculations/results/v4-moe-training-hash.md)和[batch2](../calculations/results/v4-moe-training-batch2.md)分别核对负载/选择边界。未加权与加权SwiGLU中间态、hash int32或topk int64 ID、where token/slot int64分别保存，避免遗漏或重复。"
           "运行 `python3 calculations/calc.py v4-moe-training --format md`，`--inputs`指定batch/tokens/layer_id/routing/counts。此单层账已含router与门控，不能再与旧43层primitive总账直接相加。官方QAT披露与当前去舍入数学图分开，不宣称量化逐值等价、完整主辅损失或整模型训练峰值。",
           '> **实验 3-6')
    insert('03-推理与训练负载.md', 'C19-v4-online-state-vjp',
           "[V4在线压缩器时间图](../calculations/results/v4-online-r4-tail-emits.md)在正start_pos下逐token记录槽位覆盖、emit及ratio4 previous←current复制的状态版本。联合反向返回初态、新输入、最终KV/score和共享参数梯度；覆盖槽旧值路径切断，复制别名梯度合并，初态−∞掩码为常量。"
           "[无emit](../calculations/results/v4-online-r4-no-emit.md)仍可有状态梯度；[ratio128边界](../calculations/results/v4-online-r128-boundary.md)和[两次emit](../calculations/results/v4-online-r128-two-emits.md)另列。默认S3/N6/ratio4矩阵前向100,663,296、反向201,326,592 FLOPs，标量前向49,538、反向115,584 FLOPs。"
           "运行 `python3 calculations/calc.py v4-compressor-online --format md`；initial_state_mode区分叶子与接回历史图的梯度所有权，不擅自决定detach。prefill→online两ratio输出及链式梯度已验证；并行chunk、实际历史截断策略、量化cast梯度及完整运行峰值仍未推定。",
           '> **实验 3-6')
    insert('12-端边云协同.md', 'C81-pixel-preprocess',
           "[已解码RGB到视觉入口](../calculations/results/vision-preprocess-nonsquare.md)补齐单图CPU预处理：HWC布局复制、官方smart resize、bicubic抗锯齿、FP32归一化、时间维展开/patch物化及BF16入口转换。固定PyTorch2.7/torchvision0.22非AVX路径以FP64准备系数、INT16存权重、INT32卷积累加，各轴分别舍入截断，不能把整数MAC算作FP32 FLOPs。"
           "257×385缩放为256×384，输出[384,1536] FP32 patch，共2,359,296B；BF16入口1,179,648B。逐阶段语义读17,185,865B、写8,051,499B包含tap权重和系数内部访问，不能再重复相加，也不是实测DRAM。[640方图](../calculations/results/vision-preprocess-aligned640.md)、[最小面积](../calculations/results/vision-preprocess-min-area.md)与[最大面积预算](../calculations/results/vision-preprocess-max-area.md)另列。"
           "运行 `python3 calculations/calc.py vision-preprocess --format md`，`--inputs`指定height/width、encoder_dtype与normalization_cache。用输出resized_height/width接现有vision编码器，patch投影与语言矩阵不重复计算。JPEG/PNG、ICC、多图分组、设备传输及实测延迟/峰值仍未计；最大面积仅几何/预算核验。",
           '> **实验 12-3')
    insert('12-端边云协同.md', 'C81-mixed-images',
           '[混合尺寸](../calculations/results/vl-request-mixed.md)的256²与512²两图分别256与1024patch，共320语言位置，视觉956435529728矩阵FLOPs；[均衡面积](../calculations/results/vl-request-balanced-area.md)两张320×512图各640patch，同样320语言位置，但视觉只有927444500480FLOPs。差28991029248来自视觉attention逐图平方和，不能用平均patch数替换；语言请求总位置相同，工作相同。[仅大图缓存命中](../calculations/results/vl-request-mixed-large-hit.md)视觉降至175825223680FLOPs，语言与完整EC不变。输入images逐图指定预处理后尺寸与已验证cache_hit；参数容量共享一次，逐算子接口读取仍逐次计。',
           '> **实验 12-3')
    position_request = json.loads((PROJECT / 'results/vl-position-four-640-images.json').read_text())
    positions = position_request['position_bridge']['summary']
    insert('12-端边云协同.md', 'C81-vl-position',
           f"[静态图像位置构造](../calculations/results/vl-position-four-640-images.md)用显式文字/图像顺序生成三轴mRoPE：四图640²、每图前100文字/控制位置，共{positions['prompt_positions']}语言位置，下一个旋转位置却为{positions['next_rotary_position']}，delta={positions['rope_delta']}。生成128个输出后的KV仍占{positions['final_kv_positions']}位置，不能用旋转坐标跨度压缩KV容量或语言attention工作。"
           "[混合矩形图像](../calculations/results/vl-position-mixed-images-two-turn-boundaries.md)核对图像顺序和二维几何；[特征缓存命中](../calculations/results/vl-position-one-image-cache-hit-decode.md)只跳过编码器，不免除本请求位置准备。prefill索引、decode arange/delta复制/三轴加法以int64接口分列，语言频率表与sin/cos仍只计一次。"
           "使用 `vl-request --inputs` 提供position_segments；默认未提供时位置值仍外部给定。此处固定无padding静态图像和直接model路径，不包含tokenizer、generation wrapper或实测HBM。",
           '> **实验 12-1')
    insert('12-端边云协同.md', 'C81-vl-stage-figure',
           '[阶段计算图（SVG）](../calculations/figures/vl-stages/figure.svg)对照相同四图请求的视觉编码缓存未命中与全命中：[PDF](../calculations/figures/vl-stages/figure.pdf)、[逐阶段数据](../calculations/figures/vl-stages/data.json)。横轴为矩阵FLOPs，不是TFLOP/s或实测时延；缓存只去掉编码工作，语言prefill和decode相同。运行 `python3 calculations/calc.py plot-vl-stages` 重绘，输入、脚本与输出哈希纳入校验。',
           '> **实验 12-3')
    insert('12-端边云协同.md', 'C81-vl-request',
           '[视觉到语言完整阶段账](../calculations/results/vl-request-book.md)复用官方视觉编码，不重复算embedding：4图640²+400非图像位置得到2000位置prompt，生成128token依次付视觉5241202278400、语言prefill15714279096320、127次decode1176266473472矩阵FLOPs，合计22131747848192。最后KV长度2127、313638912bytes；prefill最后logits产生首token，最后输出尚未写入KV。[视觉全命中](../calculations/results/vl-request-all-ec-hit.md)只省视觉计算，不减少语言prefill/attention/KV；[只输出首token](../calculations/results/vl-request-first-output.md)无decode。[1024输出](../calculations/results/vl-request-long-output.md)按增长历史精确求和，非平均长度估算。DeepStack来自视觉5/11/17，注入语言0/1/2层，三次prompt clone与视觉位置add只在prefill计。运行 `python3 calculations/calc.py vl-request --format md`；CPU媒体预处理、网络/队列、真实kernel与动作闭环仍另计。',
           '> **实验 12-3')
    insert('11-资源调度与运行环境.md', 'C65-retry-paths',
           '[有限重试/回退树](../calculations/results/retry-paths-book.md)把初试、局部修复、升级三节点的条件结果展开为六条终止路径，默认假想概率的总质量成功率99.744%，20秒内且质量成功率95.04%；每提交期望费用0.01456、墙钟11.504秒、CPU3.376核秒。所有失败和超时成功路径费用保留，不只统计成功尝试；相同upgrade节点来自不同路径时累计时间分别计算。[14秒](../calculations/results/retry-paths-tight.md)、[22秒](../calculations/results/retry-paths-relaxed.md)与[9秒](../calculations/results/retry-paths-impossible.md)分别改变联合成功分母，零完成费用比为null。运行 `python3 calculations/calc.py retry-paths --format md`，可用inputs替换有限DAG；概率、费用和资源为教学输入，不代表失败后独立重试、生产队列或扩容收益，deadline为判定而非强行中断。',
           '> **实验 11-9')
    insert('12-端边云协同.md', 'C81-vision-encoding',
           '[视觉编码逐步复算](../calculations/results/vision-encoding-single.md)补在语言prefill之前：官方Qwen3-VL4预处理后640²单图1600patch→400位置，patch矩阵5033164800 FLOPs、24视觉block1218025881600、final及3个DeepStack merger87241523200，合计1310300569600矩阵FLOPs；bias/norm/RoPE/softmax/GELU等另列参考运算和特殊函数，不把它们免费忽略。[四图](../calculations/results/vision-encoding-book.md)矩阵5241202278400 FLOPs，attention按各图P²相加，不拼成(4P)²；每图完整EC8192000bytes之后才进入语言主干。[3图命中](../calculations/results/vision-encoding-three-hits.md)只编码1图，但仍交付4图EC。运行 `python3 calculations/calc.py vision-encoding --format md` 查看每矩阵形状、重复与读写。语言prefill完全另计；CPU图片解码/resize、FP32中间cast、kernel工作区及实测HBM尚未计，不能用embedding字节代替本段算力。',
           '> **实验 12-3')
    insert('03-推理与训练负载.md', 'C77-C80-generation-loops',
           '[生成请求阶段账](../case-studies/generative-multimodal-models.md)按依赖图及内部循环建模，不将整个请求压成prefill/decode。[Omni](../calculations/results/omni-audio-book.md)每帧code predictor是2位置prefill再14单位置调用，15个残差码但处理16位置；[Fish](../calculations/results/fish-audio-book.md)每帧fast路径预热1次再9次预测，丢弃的首logits仍有计算。[Qwen-Image](../calculations/results/image-generation-book.md)1024²的4096latent位置、50步true CFG实际100次DiT前向，去噪矩阵7830392222515200 FLOPs；[FLUX4B distilled](../calculations/results/image-generation-flux.md)4次前向，139280712204288 FLOPs，质量条件不同不直接排名。[H3](../calculations/results/video-generation-book.md)按官方帧函数120对齐124、37latent帧；[Wan](../calculations/results/video-generation-wan.md)另用自身规则。各矩阵形状、次数与阶段量见CLI `omni-audio`、`image-generation`、`video-generation`；图像已补文本编码器及VAE矩阵/卷积；Omni已补94个非Transformer codec算子、逐帧DAG与声明接口供给。Fish现已补168个codec算子与纯文本提示；完整媒体输入/采样和剩余非矩阵/运行时仍有缺项，不把已计子账当实测整请求时间。',
           '## 本章的设计决定')
    insert('02-模型架构.md', 'V3-base-forward',
           '[DeepSeek V3基础前向](../calculations/results/v3-forward-prefill.md)按官方61层、3层Dense与58层MoE逐张量计671026419200逻辑参数、45395张量；均匀两字节容量仅作比较格式，未当官方FP8文件大小。固定HF参考路径先展开K/V再缓存，每请求每位置4997120bytes，与compact MLA不是同一布局。8192 prefill矩阵767753388556288 FLOPs，[单token decode/H8192](../calculations/results/v3-forward-decode.md)114190598144 FLOPs；[B64](../calculations/results/v3-forward-b64.md)独立按batch扩展。默认全位置输出头，[last head](../calculations/results/v3-forward-last-head.md)是显式负载变体；[eager矩形](../calculations/results/v3-forward-eager.md)与有效因果cell分开。运行 `python3 calculations/calc.py v3-forward --format md`；分组路由偏置只影响选择，混合权重用原sigmoid分数。未计FP8转换、完整HBM、缓存重分配或MTP，也未完成checkpoint索引核验。',
           '> **实验 2-3')
    insert('11-资源调度与运行环境.md', 'C61-environment-resources',
           '[真实环境资源复算](../calculations/results/environment-resources-book.md)封存9组36工具进程，按launch至观察回收的完整窗口核验有限样本Little面积恒等式，CPU核秒与RSS采样梯形积分分别计。三次条件中位数：CPU突发0.103272秒/0.290700核秒，等待突发0.470694秒/0.175264核秒；RSS和不是物理内存。[间隔提交](../calculations/results/environment-resources-cpu-stagger.md)采样RSS峰值和83927040bytes，组窗口0.538980秒。[控制器12轮](../calculations/results/environment-resources-controller.md)完整循环9.357789秒，模型墙钟8.995477秒而控制器模型阶段CPU0.157146核秒，最终仅2/6检查通过仍计全部资源。运行 `python3 calculations/calc.py environment-resources --format md`；两批实验不相加，采样首尾未观察区、计划提交延迟与真实OS队列等待分开，后者unknown，不外推生产稳态容量。',
           '> **实验 11-1')
    insert('12-端边云协同.md', 'C67-multimodal-cache',
           '[Qwen3-VL完整EC/KV](../calculations/results/multimodal-cache-book.md)由官方配置和固定vLLM DeepStack拼接复算：预处理后640²每图400位置，最终embedding及3组DeepStack合计[400,10240]、BF16为7.8125MiB；视觉KV为56.25MiB，DeepStack不增加语言token数。四图加400其余输入位置需281.25MiB逻辑KV。[单图](../calculations/results/multimodal-cache-single.md)0.8MB压缩图在6.4Mbit/s链路1秒，完整EC需10.24秒；[25GB/s链路](../calculations/results/multimodal-cache-datacenter.md)单图EC为0.32768ms。教学4卡、E12图/s、PD4请求/s、共享300MB/s，无命中最优2E+2PD为6请求/s；[75%命中](../calculations/results/multimodal-cache-warm.md)1E+3PD上界9375/1024请求/s受网络限制。运行 `python3 calculations/calc.py multimodal-cache --format md`；只接受预处理后尺寸，未运行原图resize，命中仍传完整EC，缺失缓存服务和尾部约束不能据此保证SLO。',
           '> **实验 12-3')
    insert('05-算子与运行时.md', 'C10-v4-fp8-linear',
           '[V4 FP8 Linear](../calculations/results/v4-fp8-flash-decode.md)按固定官方源码选取非routed投影及shared专家，BF16输入量化为E4M3并使用E8M0 scale、FP32累加。Flash单token有效矩阵8829009920 FLOPs，32行tile为282528317440；[Pro](../calculations/results/v4-fp8-pro-decode.md)分别37213962240与1190846791680。scale乘积每行/输出block/K-block一次，由128列共享，再逐输出元素乘加，不能统一误记为每元素三个FLOPs。[33行边界](../calculations/results/v4-fp8-flash-tail.md)和[B64](../calculations/results/v4-fp8-flash-b64.md)分别检查补齐与整tile。运行 `python3 calculations/calc.py v4-fp8-linear --format md`；有效矩阵已在v4-forward内，不能重复相加；接口bytes不等于物理HBM流量，未覆盖routed FP4、MTP或完整运行时。',
           '> **实验 5-2')
    insert('11-资源调度与运行环境.md', 'C64-routing-cost',
           '[假想服务成本复算](../calculations/results/routing-cost-book.md)将全部尝试费用除以预期质量成功数，reasoning与visible仅合计一次输出计费。A固定缓存全命中，B命中率下降时费用交点为[1291/1520](../calculations/results/routing-cost-crossover.md)，约84.9342%；这是题设价格而非供应商价目。给定A10秒、B命中4秒/未命中12秒、质量成功与命中独立，6秒内且质量通过达到90%需要B命中率至少[45/49](../calculations/results/routing-cost-joint-target.md)，约91.8367%。[3秒时限](../calculations/results/routing-cost-impossible-deadline.md)零完成的费用比明确为null。运行 `python3 calculations/calc.py routing-cost --format md`；预期成功数不是实测有限样本，未计题设之外缓存创建/存储、工具与重试，价格交点和可用性门槛分别判断。',
           '> **实验 11-8')
    insert('10-训练系统.md', 'C59-weight-handoff',
           '[权重交接复算](../calculations/results/weight-handoff-book.md)按官方Qwen235全量BF16矩阵拆分专家与非专家，专家423GiB、EP16每rank专家26.4375GiB；非专家权重在本教学布局每rank完整复制，因此总接收量不等于仅专家分片。比较生产端向每rank完整单播与仅发送所需专家加非专家，分别受聚合出口和最大接收端约束，不把字节比当树广播或端到端加速。'
           '[Qwen8阶段容量](../calculations/results/weight-handoff-qwen8.md)复算同时恢复83.2564GiB与先同步权重再释放训练状态、最后分配空KV池的59.2564GiB峰值；40GiB训练状态、24GiB KV、4GiB共用量均为教学输入。[非整除EP7](../calculations/results/weight-handoff-uneven.md)显式给出专家区间，[四副本](../calculations/results/weight-handoff-replicas.md)计生产端出口复制。运行 `python3 calculations/calc.py weight-handoff --format md`；源端重组、真实接收缓冲、版本就绪与量化仍需实测，更新后旧KV不能直接复用。',
           '> **实验 10-8')
    insert('10-训练系统.md', 'C59-teacher-cache',
           '[教师缓存复算](../calculations/results/teacher-cache-book.md)按官方Qwen3-8B最终hidden宽4096、词表151936，8192 token的BF16最终hidden为64MiB，全logits为2374MiB，比例37.09375。缓存hidden每次学习重放仍需2THV输出投影；全logits方案生产时投影一次。分别计一次写入、每轮读取和head矩阵工作，chunk只切token维并保留完整词表。'
           '[V4 Flash](../calculations/results/teacher-cache-v4-flash.md)、[V4 Pro](../calculations/results/teacher-cache-v4-pro.md)、[Kimi K3](../calculations/results/teacher-cache-kimi-k3.md)与[Qwen235](../calculations/results/teacher-cache-qwen235.md)使用各自官方文本H/V。运行 `python3 calculations/calc.py teacher-cache --format md`；有效带宽与算力为显式教学输入，串行阶段预算不是端到端时间。缓存限定固定教师版本、最终归一化后hidden，尚不实现版本/token校验或证明低精度重建与蒸馏质量。',
           '> **实验 10-8')
    insert('10-训练系统.md', 'C59-routing-metadata',
           '[Routing Replay记录预算](../calculations/results/routing-metadata-book.md)按官方Qwen3-30B的48个MoE层、128专家、top8复算8192token的uint16逻辑专家ID为6291456bytes（6MiB）；[int32](../calculations/results/routing-metadata-int32.md)为12MiB。另按教学布局每token24bytes的sequence/position/weight-version、位图1024bytes、header128bytes计身份元数据，固定revision与layer顺序仍须schema绑定。'
           '[Qwen235](../calculations/results/routing-metadata-qwen235.md)为94层top8，[V4 Flash](../calculations/results/routing-metadata-v4-flash.md)43层top6，[V4 Pro](../calculations/results/routing-metadata-v4-pro.md)61层top6，[Kimi K3](../calculations/results/routing-metadata-kimi-k3.md)排除首dense层后92层top16；shared专家不另写选择ID，V4包含hash层，均不含MTP。uint8恰能编码256专家但不能编码384/896专家。'
           '[三份物理保留](../calculations/results/routing-metadata-retained.md)只乘存储而不自动乘单次传输；运行 `python3 calculations/calc.py routing-metadata --format md` 查编码范围、声明总载荷、供给bytes/s与有效链路余量。此处仅元数据几何，不证明各模型框架R3受支持；多轮共享、packing顺序和缺失记录校验、logprob与质量仍待，不把KV命中当路由日志命中。',
           '> **实验 10-9')
    insert('10-训练系统.md', 'C60-dense-training-scale',
           '[名义Dense规模与期限](../calculations/results/dense-training-scale-book.md)按6ND、固定20T token、16384卡与BF16/FP32 dense峰值扫描1T/5T/10T和30/40/50%教学MFU。50%时1T的A100-80GB-SXM／H100-SXM／B200为543.404169／171.358501／75.352045天；5T为2717.020844／856.792504／376.760224天，10T再翻倍。1T在90天内算力张数下界98924／31195／13718，持久16byte状态容量下界200／200／89；两者max仍不证明可部署。'
           '[数据随N增长](../calculations/results/dense-training-scale-proportional.md)使用D=20N，5T相对1T工作25倍，区别于固定D的5倍；[8192卡](../calculations/results/dense-training-scale-half-fleet.md)和[额外30天停顿](../calculations/results/dense-training-scale-calendar.md)另列。运行 `python3 calculations/calc.py dense-training-scale --format md` 查看90/180天所需整数卡数及固定卡数的参数界；D=20N用整数平方根保证N与N+1边界。名义Dense无真实架构config，不代替Qwen/V4/K3或MoE总参数计算；固定MFU、理想分片与16byte只是输入，激活、通信、供数、故障和质量仍需验证。',
           '> **实验 10-10')
    insert('10-训练系统.md', 'C54-training-deadline',
           '[训练期限与设备下界](../calculations/results/training-deadline-book.md)按官方Qwen8逐矩阵前反向核算100B有效位置：12207031条8192序列＋尾序列2048，矩阵总工作5265722561667444768768 FLOPs，30天需38580.247token/s。仅以此矩阵口径的30/40/50% BF16/FP32 dense峰值效率为教学输入，40%时RTX4090／5090／A100-80GB-SXM／H100-SXM／B200算力下界31／25／17／6／3张；16byte完整持久状态131051765760bytes，理想分片容量下界6／5／2／2／1张。'
           '[32768序列](../calculations/results/training-deadline-long-sequence.md)重算注意力，[Qwen235](../calculations/results/training-deadline-qwen235.md)分开激活专家工作与全部专家容量，[排除5天停顿](../calculations/results/training-deadline-calendar.md)从期限扣除，[1B任务FP32梯度](../calculations/results/training-deadline-capacity.md)检查容量主导。运行 `python3 calculations/calc.py training-deadline --format md`；A800现有锁定资料缺BF16/FP32 dense可选峰值，H20 SXM5 96／141GB已锁定官方型号容量，持久容量下界为2／1张，但均缺精度峰值，保留缺项不代用。两下界max仍未证明TP/PP/EP、激活、通信或最忙rank可行；矩阵子账效率不直接套其它FLOPs口径的MFU，同一停顿不可重复计入效率与日历扣除。',
           '> **实验 10-2')
    insert('10-训练系统.md', 'C56-checkpoint-resume',
           '[真实重分片与下一步复核](../calculations/results/checkpoint-resume-book.md)封存10-6的15原件，含实际DCP两份数据与metadata、提取坐标及各rank记录。19状态唯一载荷463688bytes，文件共518512bytes、其中metadata6393bytes，差额54824bytes不唯一归因序列化。保存2行分片的第一权重[129,129]／[128,129]，恢复3列分片为三份[257,43]，另核验2行原布局与1份完整布局。'
           '保存／三种恢复最大rank API296.783／48.597／64.583／49.605ms；各路径一次且不含加载后聚合，不能排名性能。全部6恢复rank的完整状态与下一步loss1.3159840106964111及状态哈希均同未中断基线，清空Adam动量负对照均检出。运行 `python3 calculations/calc.py checkpoint-resume --format md` 查逐状态与复制载荷：2／3／1 rank全组局部字节473824／483960／463688，增加来自RNG及标量复制。矩形覆盖无交叠且总体积完整；恢复后聚合走相同单进程数学路径，不证明不同分布式归约逐位一致。CLI核验封存记录和文件，不重新执行torch。',
           '> **实验 10-6')
    insert('10-训练系统.md', 'C56-checkpoint-fault',
           '[真实提交前故障复核](../calculations/results/checkpoint-fault-book.md)导入10-7正常／故障20原件，含实际DCP载荷与metadata，核对监督器执行源码及SHA。第二份故障检查点已写12622659bytes数据，metadata缺失，实际加载报CheckpointException；API9.479633ms返回后Future未完成，提交时间仍null，至SIGKILL的241.845822ms仅为未完成观察。'
           '父进程等待元数据前人工屏障与20步训练完成才终止；第一份实际恢复cursor3、全部状态哈希一致，故障前两轮各20步已到cursor43，需重做40次更新，尚无重做耗时。正常两份及故障第一份共三份提交／加载成功。运行 `python3 calculations/calc.py checkpoint-fault --format md` 分列stage／writer／commit，future观察不当内部就绪。人工屏障不是慢磁盘，进程终止不是断电或多rank可靠性证据；本CLI核验封存文件与真实加载记录，未重新执行torch。',
           '> **实验 10-7')
    insert('10-训练系统.md', 'C56-checkpoint-baseline',
           '[真实CPU保存基线复核](../calculations/results/checkpoint-baseline-book.md)导入10-7五轮三模式39原件，含10份实际DCP数据与metadata，逐文件核对SHA和运行源码。15次同20步、逐步loss与最终参数／Adam／两种RNG／游标哈希一致，10次恢复哈希同保存前快照。无保存／同步／异步全窗口中位数76.042／207.377／84.569ms，API分别未测／122.268／2.206ms。'
           '按每轮先求差再取中位数，异步−无保存全窗口5.172589ms、训练区间2.959636ms，同步−异步窗口127.423193ms；不能用两组中位数相减替代。运行 `python3 calculations/calc.py checkpoint-baseline --format md` 查看全部运行、writer与训练重叠；future观察不当后台就绪时刻，未经过stage钩子记null。CPU单线程小模型非Qwen／GPU性能，RSS高水位差非staging独占峰值，文件bytes/writer时间非物理磁盘带宽；本模块核验封存加载记录和文件，未重新执行torch恢复。',
           '> **实验 10-7')
    insert('10-训练系统.md', 'C57-checkpoint-interval',
           '[保存周期与重试](../calculations/results/checkpoint-interval-book.md)以官方Qwen8的114670295040bytes、教学8GB/s同步保存得到c=14.333787s，1024设备各MTBF365天且独立，作业MTBF30796.875s，恢复r=120s。tau为新增有用计算秒，一阶 `c/tau+lambda×tau/2+lambda×r` 给最优939.612519s；另设计算和保存均可失败、恢复期间不失败的Poisson重试模型，`E=(exp(lambda×(tau+c))-1)×(1/lambda+r)`，tau/E数值最优930.081056s，枚举候选两者均选900s。'
           '[每日一次作业共同冲击](../calculations/results/checkpoint-interval-common-shock.md)只加一次率，两个最优改为806.766116／797.238689s；[高故障率](../calculations/results/checkpoint-interval-high-failure.md)展示一阶损失超过1不裁剪，[零故障](../calculations/results/checkpoint-interval-no-failure.md)无有限最优，[恢复500秒](../calculations/results/checkpoint-interval-long-recovery.md)在本模型只改变期望比例、不改变最优tau。运行 `python3 calculations/calc.py checkpoint-interval --format md` 查各项精确分数与重试期望；故障率非设备可靠性测量，独立共同冲击不代表一般时间相关故障，未含异步积压、恢复失败和有限训练终点。',
           '> **实验 10-7')
    insert('10-训练系统.md', 'C56-checkpoint-async',
           '[异步保存与背压](../calculations/results/checkpoint-async-book.md)按官方Qwen8全部参数14bytes得到114670295040bytes有效快照，8GB/s单次upload14.333787s；每10秒请求一份超过该写入供给，有限槽会延后实际capture。'
           '[取整8B原例](../calculations/results/checkpoint-async-rounded.md)显式覆盖载荷112GB，20／40秒capture、各staging0.5秒，durable34.5／54.5秒，50秒故障仅能回到20秒；[16GB/s](../calculations/results/checkpoint-async-fast.md)durable27.5／47.5秒，可回到40秒，两路staging总暂停同为1秒。'
           '[单槽背压](../calculations/results/checkpoint-async-one-slot.md)每10秒请求时第二次capture延到34.5秒，训练屏障重叠取并集；[确认额外20秒](../calculations/results/checkpoint-async-delayed-commit.md)时50秒尚无可恢复快照，返回null。运行 `python3 calculations/calc.py checkpoint-async --format md` 查看请求、capture、staging、upload与durable。吞吐／确认语义为显式教学输入，故障之后为反事实计划；墙钟回退不等于损失token，CPU数据状态、加载恢复和后台训练降速另计。',
           '> **实验 10-7')
    insert('10-训练系统.md', 'C56-checkpoint-reshard',
           '[检查点逻辑重分片](../calculations/results/checkpoint-reshard-book.md)以官方Qwen8 gate[12288,4096]的50331648参数为对象：BF16权重96MiB，连FP32 master及Adam m/v为672MiB。TP4源权重每文件24MiB，TP8目标每份12MiB；目标r取源floor(r/2)，文件偏移(r%2)×12MiB。四状态目标各84MiB，全读取672MiB、32个连续范围，不先写完整离线重分片。'
           '[仅权重](../calculations/results/checkpoint-reshard-weights.md)、[8→4合并](../calculations/results/checkpoint-reshard-reverse.md)、[展平7片→行切5片](../calculations/results/checkpoint-reshard-flat.md)与[Qwen235单专家](../calculations/results/checkpoint-reshard-qwen235.md)分别复算。运行 `python3 calculations/calc.py checkpoint-reshard --format md` 查看全局元素区间、源文件与目标缓冲偏移；小数组真实字节重建验证无重复且完整。原始行主序无header文件仅为声明布局，未执行真实checkpoint恢复；融合／转置／压缩、梯度与CPU状态、数据及随机状态、物理存储IO和完整恢复时间另计。',
           '> **实验 10-7')
    insert('10-训练系统.md', 'C53-gradient-cast',
           '[梯度转换放置](../calculations/results/gradient-cast-book.md)复用官方Qwen8单层gate[12288,4096]，50331648元素的BF16／FP32梯度为96／192MiB，两端cast逻辑读写均288MiB。教学CPU／GPU转换100／1500GB/s，单向D2H32GB/s时CPU路径6.166ms、GPU路径6.493ms；[300GB/s](../calculations/results/gradient-cast-fast-link.md)改为3.355／0.872ms，等时链路精确250000000000/7 bytes/s。'
           'CPU路径主机活跃峰值288MiB，GPU路径192MiB；GPU路径额外显存192MiB，含共有BF16源的峰值288MiB。[GPU额外预算少1byte](../calculations/results/gradient-cast-tight-gpu.md)时选CPU路径，[等时场景](../calculations/results/gradient-cast-equality.md)保留并列，[Qwen235单专家](../calculations/results/gradient-cast-qwen235.md)按真实gate重新计算。运行 `python3 calculations/calc.py gradient-cast --format md` 查精确操作时序与缓冲寿命；只计梯度就绪到CPU可消费，不含Adam、回传、分块流水和整个训练峰值，活跃载荷不等于预留缓冲池。',
           '> **实验 10-1')
    insert('10-训练系统.md', 'C53-training-state',
           '[完整Adam／ZeRO状态](../calculations/results/training-state-book.md)按官方Qwen8的399个物理参数张量、8190735360参数逐项核算。BF16权重2＋BF16梯度2＋FP32 master4＋Adam m/v各4＝16bytes/参数，未分片131051765760bytes（131.052GB／122.051GiB）；DP8的stage0/1/2/3每rank持久量分别122.051／41.955／28.606／15.256GiB。'
           '[FP32梯度](../calculations/results/training-state-fp32-gradient.md)改为18bytes/参数，未分片137.308GiB、stage3为17.163GiB；[额外同时驻留10GiB](../calculations/results/training-state-extra-live.md)使stage3超过输入24GiB净预算。'
           '[Qwen235／DP64](../calculations/results/training-state-qwen235.md)全235093634560参数状态3.761TB，stage3每rank54.737GiB，不按top-8缩减专家状态；[逐张量补齐DP7](../calculations/results/training-state-tensor-seven.md)与[展平补齐](../calculations/results/training-state-flat-seven.md)对照。运行 `python3 calculations/calc.py training-state --format md`，可用 `--inputs` 指定精度、DP、补齐和净预算。ZeRO阶段依据已封存官方文档；容量只覆盖所列分配，不含未输入的激活、聚合、casting、通信bucket和allocator，不能证明实际训练可行。',
           '> **实验 10-1')
    insert('09-分布式推理.md', 'C50-cache-residency',
           '[多级缓存驻留积分](../calculations/results/cache-residency-book.md)按官方Qwen8 BF16每token147456bytes、16token页2359296bytes，对教学驻留区间按物理前缀身份取同层并集，跨HBM／DRAM／SSD副本分别计量。HBM峰值360MiB，实体3888MiB·s、逻辑4608MiB·s，同层共享节省720MiB·s；DRAM6336MiB·s、SSD13824MiB·s。三层同时峰值864MiB，总实体24048MiB·s，其中跨层副本7200MiB·s。'
           '[HBM预算360MiB减1byte](../calculations/results/cache-residency-tight.md)在[5,6)秒超预算1秒，不隐式驱逐；[Qwen235同区间](../calculations/results/cache-residency-qwen235.md)独立使用官方GQA几何。运行 `python3 calculations/calc.py cache-residency --format md`，或用 `--inputs` 指定区间和净容量。身份声明必须覆盖版本／adapter／格式／执行状态，同token不证明KV逐位相同；全局唯一页量只是比较基准，不能当跨层实体容量。完整页、半开区间，不从容量推断写入IO、命中率或取回时间；部分页与混合递推状态仍待。',
           '> **实验 9-8')
    insert('09-分布式推理.md', 'C50-cache-fault',
           '[同坏页预取策略](../calculations/results/cache-fault-book.md)导入9-8三策略27封存原件，核对配置仅prefetch_policy不同、原页2359296bytes删末2bytes所得哈希一致，以及每请求实际一次Short read。wait_complete观察60.082702s未返回，完成时间／缓存命中／完成重算工作均保留null；timeout和best_effort分别3.246515／1.165554s完成，命中0，1024输入／16输出等于参考。'
           '两个成功条件完整prefill各14535715979264矩阵FLOPs，后续decode另计。监督器最终哈希仍为损坏哈希，成功回退不等于修复文件；未取得三个运行坏文件目录，结论来源明确为监督记录。运行 `python3 calculations/calc.py cache-fault --format md` 查异常发生时间与未完成下界。每策略一次、固定顺序且编译条件不同，不报加速比／p95；原生等待阈值不是请求完成时限，后续I/O线程可用性与容量泄漏仍未测试。',
           '> **实验 9-8')
    insert('09-分布式推理.md', 'C50-cache-missing',
           '[实际缺页与重算](../calculations/results/cache-missing-book.md)导入9-8缺页与显存对照17原件并复用已封存原始KV页：缺页0首请求get0／复用0／重算1024token；缺页32读32页75497472bytes（72MiB），仅复用连续512token、重算512token，后续文件仍存在也不能跨缺口复用。两条件随后各两请求device命中1008，六次16输出均同参考。'
           '实际layer_first BF16页[2,36,16,8,128]，原页／恢复页SHA与有限值检查通过；缺页0恢复逐位相同，缺页32的1179648元素中995403不同、最大绝对差26.75，首层K/V相同。运行 `python3 calculations/calc.py cache-missing --format md` 查逐层差异和剩余prefill矩阵工作。输出一致不证明KV逐位一致；分段执行与数值因素未隔离，显存分段v2已加入：前置512输入／1输出，随后实际device命中512／1008／1008且storage0；整段与显存分段页1021226元素不同、最大差13.5625，存储恢复与显存分段页992972元素不同、最大差26.53125。旧前置16输出的528命中尝试不计作同边界控制，仍不能唯一归因存储或舍入。首条件含JIT，不比较恢复速度。',
           '> **实验 9-8')
    insert('09-分布式推理.md', 'C50-cache-restart',
           '[HiCache正常重启载荷账](../calculations/results/cache-restart-book.md)导入9-8正式producer-v6／consumer-v6共74原件，含65份实际KV载荷逐文件SHA。官方Qwen8的16token页为2359296bytes，库存65页153354240bytes（146.25MiB）；重启首请求64次get读150994944bytes（144MiB／1024token页），可复用仅1008token、148635648bytes（141.75MiB），多读一页等价量单列。'
           '两进程文件清单与哈希相同，consumer一次成功set不计新增文件；六次16token输出相同、随后请求从device命中，prompt矩阵节省按官方配置复算。运行 `python3 calculations/calc.py cache-restart --format md` 查请求与get/set表。首个producer含JIT，不计算重启速度比或p95；页缓存未清，文件bytes不等于物理磁盘IO，正常重启不证明fsync／断电持久性、损坏检测或KV与重算逐位一致。',
           '> **实验 9-8')
    insert('09-分布式推理.md', 'C51-router-pressure',
           '[真实排队压力与整体完成](../calculations/results/router-pressure-book.md)导入9-9补测8份封存原件，各3轮cache_first／queue_first共18调用。目标3136输入、1输出，缓存优先实际命中3135token且选择忙worker0，队列优先去空闲worker1冷算；决策负载与目标在后台128输出活跃期间发出逐组核对。'
           '目标完成中位1.382795→0.328635s，但两任务从后台提交到最后完成中位1.384443→1.544837s。逐trial先求差再取中位，目标节省1.054103s、两任务增加0.160955s，不混用两组中位之差。'
           '运行 `python3 calculations/calc.py router-pressure --format md` 查六组时间、采样等待峰值与实际最大采样间隔，目标矩阵按官方配置复算。两个worker共享GPU，三轮／强制输出且原Agent任务失败；这是客户端规则对照，不是原生Router或完成时间预测。采样峰值不等于精确排队时长，后台剩余时间是事后量。',
           '> **实验 9-9')
    insert('09-分布式推理.md', 'C51-router-trace',
           '[原生缓存亲和记录](../calculations/results/router-trace-cache_aware.md)、[轮转](../calculations/results/router-trace-round_robin.md)与[power_of_two](../calculations/results/router-trace-power_of_two.md)导入实验9-9正式run-v3的12份封存原件，SHA锁定，逐请求核对注册健康、响应ID、worker日志去向、输入长度、同worker已完成前缀上界和相同输出。每策略12请求19556输入，实际缓存16376／13458／13458token，token加权83.739%／68.818%／68.818%，命中请求11／10／10。'
           '官方矩阵节省分别237179353300992／194131899777024／194131899777024 FLOPs；不是唯一KV容量或实测HBM。缓存亲和12请求都在worker1，客户端中位32.770290ms，另两策略45.523886／43.370600ms。运行 `python3 calculations/calc.py router-trace --policy cache_aware --format md` 查逐请求。两worker共享一GPU、固定策略顺序、串行单轮且强制一个输出token，不代表跨机、真实排队压力、远端缓存或质量；事件缺口与索引恢复仍未验证。',
           '> **实验 9-9')
    insert('09-分布式推理.md', 'C51-cache-route',
           '[缓存路由依赖账](../calculations/results/cache-route-book.md)复算官方Qwen8前缀8192／suffix256，前缀1207959552bytes；完整与命中矩阵工作另按config计算，时长保持教学输入。A队列250ms＋命中10ms为260ms，B等待20ms＋重算180ms为200ms；远端5GB/s、查找10ms及H2D25GB/s整份串行取回为309.910292ms，[20GB/s](../calculations/results/cache-route-fast-remote.md)为128.716360ms。取回与GPU等待可重叠，按max(queue,ready)+compute；16请求/s仅payload已19.327GB/s，单请求有利不证明持续能力。'
           '[失效概率](../calculations/results/cache-route-stale.md)令A等待80ms，有效命中90ms／全部失效260ms，p=0.9时期望107ms但p99为260ms，超过220ms目标；平均优于B需p>6/17。[p=0.99](../calculations/results/cache-route-quantile-equality.md)按累计概率等号得到p99=90ms。'
           'CPU副本仍在且能提前取回时A为90ms，[调度后才取回](../calculations/results/cache-route-after-queue.md)则138.318382ms。运行 `python3 calculations/calc.py cache-route --format md`，JSON另给远端带宽等时边界与概率阈值；不是真实路由器策略或排队分布，事件丢失、部分前缀及共享链路队列仍待补。',
           '> **实验 9-9')
    insert('09-分布式推理.md', 'C49-replica-payback',
           '[副本冷复制回本](../calculations/results/replica-payback-book.md)复用Qwen235单层7热门副本，新增252MiB；教学共享25GB/s串行复制、每份5us，setup10.60464608ms。各rank按max(补齐矩阵/100TF/s,tile接口bytes/1TB/s)取服务，最忙rank从0.920649728ms降到0.517865472ms。'
           '[26批](../calculations/results/replica-payback-short.md)尚未回本，[27批](../calculations/results/replica-payback-boundary.md)严格获益；复制前全部setup计入，不假设与服务重叠。[目标rank只余36MiB减1byte](../calculations/results/replica-payback-capacity.md)时容量不可行，代数阈值仍列但可行回本为null。'
           '[33任务且接口足够快](../calculations/results/replica-payback-padding.md)由不变的补齐矩阵限制，无正节省便无回本。运行 `python3 calculations/calc.py replica-payback --format md`，`--inputs`可提供grouped-experts的workload、重复批数和有效供给。相同路由持续窗口是教学假设，指定tile接口不是HBM实测；真实迁移的通信、格式转换、控制协议与负载变化仍待验证。',
           '> **实验 9-6')
    insert('09-分布式推理.md', 'C49-expert-replicas',
           '[相同专家的新副本](../calculations/results/grouped-experts-replica-one.md)保持逻辑top8，Qwen235单层expert0的128任务分成64＋64到原rank0和新rank4，只增加一份36MiB BF16权重，矩阵有效工作守恒。'
           '[33任务反例](../calculations/results/grouped-experts-replica-padding.md)分成17＋16后两侧仍各需64行tile，最忙rank补齐工作未降，总工作反而多一份64行专家计算，不能按任务数减半宣称加速。'
           '[7个热门副本](../calculations/results/grouped-experts-replica-seven.md)各放rank1–7，新增252MiB，rank0仍保留7×64＋128行；每个接收rank新增36MiB，相当于196条全模型BF16 GQA token的容量（取整），不代表实际EP缓存布局。'
           '[未命中副本](../calculations/results/grouped-experts-replica-idle.md)无新增计算但仍占36MiB。运行 `python3 calculations/calc.py grouped-experts --format md`，`--inputs`中replicas用expert/rank列表；JSON分开逻辑专家、物理副本、任务及新增权重。未提供token源位置，不推断网络收益或迁移时间，真实EPLB还需通信、窗口和回本证据。',
           '> **实验 9-6')
    insert('09-分布式推理.md', 'C49-grouped-experts',
           '[逐专家tile账](../calculations/results/grouped-experts-book.md)按官方Qwen235单层128token／top8，均衡时128专家各8行。独立64×32×128 tile完全补齐，有效38654705664F、补齐309237645312F（8倍）；8rank工作均衡仍不能消除小M浪费。'
           '[集中路由](../calculations/results/grouped-experts-concentrated.md)只激活8专家、各128行，无M padding，但连续放置让全部工作落在rank0；[相同路由交错放置](../calculations/results/grouped-experts-striped.md)保持总工作与接口字节不变，最忙rank工作降至八分之一。'
           '[2048token](../calculations/results/grouped-experts-prefill.md)与[8行tile](../calculations/results/grouped-experts-small-tile.md)另列复用变化。运行 `python3 calculations/calc.py grouped-experts --format md`，JSON保留逐专家gate/up/down的M/K/N与分块载荷；权重按M块重读、输入按N块重读，边界只读有效元素，不能用FLOPs padding倍数放大bytes。此为指定output-stationary工作缓冲接口，非HBM实测；后端跳过无效指令、通信、融合、设备能力与真实重叠尚未计。',
           '> **实验 9-6')
    insert('09-分布式推理.md', 'C48-expert-reuse-threshold',
           '[78行边界](../calculations/results/expert-locality-boundary78.md)与[79行边界](../calculations/results/expert-locality-boundary79.md)使用相同官方专家与教学能力，精确分段解CPU激活交接＋max(计算,权重读取)和GPU搬权重＋max(计算,权重读取)。CPU／GPU等时knee分别每专家10／100token；单个非驻留专家1–78token时CPU服务较小，79及以上搬权重GPU较小。'
           '全部正整数区间均已求解，末段无上界；等号单独保留，不靠有限扫描猜测长期趋势。[CPU有效能力200TF/s敏感性](../calculations/results/expert-locality-fast-cpu.md)边界变为3225／3226，仍可能受激活交接限制，不是CPU产品性能声明。运行 `python3 calculations/calc.py expert-locality --format md` 查区间。这里只比较相同专家批及固定服务能力，非均匀专家负载、实际量化／NUMA／小矩阵效率仍需单独核对。',
           '> **实验 9-3')
    insert('09-分布式推理.md', 'C49-expert-locality',
           '[专家就地与搬权重子账](../calculations/results/expert-locality-book.md)按官方Qwen235的H4096、F1536、128专家／top8，gate/up/down每专家BF16共36MiB。每层固定ID0–31驻留占1.125GiB，94层合计105.75GiB，仅专家权重已不能放进单24GB卡；此驻留数是教学输入，需另做实际放置。'
           '128-token均衡路由的非驻留部分为96个不同专家、768个token—专家任务，权重3.375GiB、矩阵28991029248 FLOPs，逐assignment BF16激活往返12MiB。教学CPU2TF/s、DRAM200GB/s、GPU100TF/s、HBM1TB/s、链路25GB/s、启动5us，CPU子账19.582710ms、搬权重GPU149.059025ms；两者是声明路径的资源估计，非KTransformers实测。'
           '[2048-token prefill](../calculations/results/expert-locality-prefill.md)、[单token无驻留](../calculations/results/expert-locality-single.md)、[热点全命中](../calculations/results/expert-locality-hot.md)、[8192token](../calculations/results/expert-locality-long.md)检查复用与瓶颈变化。运行 `python3 calculations/calc.py expert-locality --format md` 查逐专家M/K/N；`--inputs`可输入128项counts。直方图缺token身份，因此明确按assignment交接，不推断跨专家去重。只计单层非驻留专家，量化／NUMA／激活访存／合并／不均衡与实际重叠仍待补。',
           '> **实验 9-5')
    insert('09-分布式推理.md', 'C47-pd-pool',
           '[整数池配比](../calculations/results/pd-pool-book.md)以官方Qwen8、8192输入／129输出统一请求口径：P处理8192新token，首输出来自prefill，D仅调用128次。两类教学副本各4个，P/D有效token每秒分别16384/64和4096/256，枚举25配比，4个前者给P、4个后者给D时上界8请求/s；共置逐副本加资源秒后为3.2请求/s。'
           '[同构对照](../calculations/results/pd-pool-homogeneous.md)分池与共置均4请求/s；[网络限制](../calculations/results/pd-pool-network.md)按每请求1207959552bytes将上界限至1请求/s，到达率等于上界不标为严格低于。'
           '[命中6144前缀](../calculations/results/pd-pool-prefix.md)只减少P新工作，D冷缓存仍收完整KV，最佳P配比降至2个、上界9请求/s；[1025输出](../calculations/results/pd-pool-long-output.md)最佳P仅1个、D为7个，上界19/16请求/s。'
           '[仅首输出](../calculations/results/pd-pool-first-output.md)无需D或KV交接。运行 `python3 calculations/calc.py pd-pool --format md`，`--inputs`可输入实际阶段能力。上述为有效服务能力教学假设，不代表A100/H20测量；副本放置可行性、混跑干扰、排队和SLO须另核，枚举最优只对本候选成立。',
           '> **实验 9-2')
    insert('09-分布式推理.md', 'C48-pd-af-handoff',
           '[PD／AF交接账](../calculations/results/pd-af-handoff-book.md)复算32层教学模型：8K BF16 KV为1GiB，AF单步双向激活0.5MiB、64次消息。有效25GB/s、每hop启动5us，串行通信PD42.954673ms、AF0.340972ms；相同1GiB分成64次的对照只因启动多315us。启动增到1ms时AF64.020972ms大于PD43.949673ms，不能仅按载荷判断开销。'
           '[双端host staging](../calculations/results/pd-af-handoff-staged.md)逐消息串行D2H→网络→H2D，各接口各算一次，双端GPU与host完整消息槽分列。'
           '[官方Qwen8](../calculations/results/pd-af-handoff-qwen8.md)按36层得到1.125GiB KV、单步576KiB激活／72次；[Qwen235](../calculations/results/pd-af-handoff-qwen235.md)另计B=4、128步。运行 `python3 calculations/calc.py pd-af-handoff --format md`，用 `--inputs` JSON修改长度、batch、步数、带宽与启动。PD一次请求快照与AF指定decode调用是不同交接范围，不能据此断言部署优劣；未含计算、排队、格式转换、MoE跨专家dispatch和流水重叠。',
           '> **实验 9-4')
    insert('09-分布式推理.md', 'C52-migration',
           '[TP4→TP8迁移子账](../calculations/results/reconfiguration-dense-tp4-to-tp8.md)按官方Qwen3 BF16逐权重分片与完整KV头所有权复算：默认B=2、8192历史token，网络16449646080 bytes，本地物化读写4704125952 bytes；声明有效带宽下传输资源下界46.99194368秒，切换时间仍未知。'
           '[TP×EP互换](../calculations/results/reconfiguration-qwen30-tp2-ep4-to-tp4-ep2.md)另核专家归属及非专家／同请求KV复制。'
           '[同卡物化](../calculations/results/reconfiguration-same-card-materialization.md)免网络但仍列本地读写；逐卡峰值按旧缓冲保留至新缓冲完整物化计算。'
           '[声明串行路径](../calculations/results/reconfiguration-declared-serial.md)把网络资源下界与另给的网络时间分列；10秒额外投入、每步省0.0002秒时50000步仅持平，50001步才严格获益，且须另核容量与SLO。'
           '[重放路径](../calculations/results/reconfiguration-dense-disjoint-replay.md)不搬旧KV仍保留目标KV容量，未知物化／网络时间保持空值。'
           '运行 `python3 calculations/calc.py reconfiguration --format md`，以 `--inputs` 修改声明快照。此处只闭合静止快照迁移与条件摊销子账；真实排空、分流、缓存身份验证、恢复重试、服务质量及完整生命周期费用仍待实测或补齐执行图，原C52尚未完整完成。',
           '### 9.6.2 异构推理的部署取舍')
    q36 = result("qwen36-prefill-8192")
    q36d = result("qwen36-decode-b1")
    insert('02-模型架构.md', 'C82-Qwen36',
           '在Qwen3-8B dense之后，用[Qwen3.6-35B-A3B逐算子账](../calculations/results/qwen36-prefill-8192.md)展开中等规模MoE，再进入V4 Flash。固定官方revision、config及693个基础文本权重形状：40层、hidden2048、256选8路由专家，另有宽512共享专家；每个路由专家三矩阵共3,145,728参数，每层全部专家805,306,368参数、单token选中25,165,824参数。路由矩阵为[BP,2048]×[2048,256]；每专家gate/up为[t_e,2048]×[2048,512]，down为[t_e,512]×[512,2048]；共享分支和门控另外计。'
           '它同时包含30层Gated DeltaNet与10层gated GQA，不能把与dense基线的全部差异归因于MoE。基础文本34,660,610,688参数、69,321,221,376 BF16存储bytes；视觉与MTP权重另列，A3B不是整个checkpoint大小。'
           f'在固定参考chunk64/eager矩形路径、全部位置输出头下，8192 prefill矩阵工作{q36["matrix_flops"]:,} FLOPs；[8192历史单步decode](../calculations/results/qwen36-decode-b1.md)为{q36d["matrix_flops"]:,} FLOPs。'
           '[B64均匀](../calculations/results/qwen36-decode-b64.md)和[集中同8专家](../calculations/results/qwen36-decode-b64-concentrated.md)保持专家FLOPs相同，当前批次读取的不同专家权重集合相差32倍，全部专家仍常驻。'
           '完整attention KV每请求每历史token20KiB，FP32递推状态固定60MiB，BF16卷积槽1.875MiB；不把线性层也按全历史KV计。运行 `python3 calculations/calc.py qwen36-forward --format md`，用 `--inputs calculations/scenarios/qwen36-forward-example.json` 改batch/token/history。JSON/CSV列逐矩阵、非矩阵和状态；逻辑接口载荷不是HBM，基础文本不含视觉/MTP执行与实测时延。',
           '### 2.5.2 DeepSeek-V4-Flash')
    insert('04-加速器架构.md', 'C82-Qwen36-capacity',
           '[Qwen3.6容量筛选](../calculations/results/qwen36-capacity-b1-n8192.md)接官方checkpoint和硬件容量：基础文本权重69,321,221,376 bytes，B1/8192历史KV160MiB、递推60MiB、卷积1.875MiB，加声明2GiB余量，合计71,701,357,824 bytes。'
           '[B8/32K](../calculations/results/qwen36-capacity-b8-n32768.md)与[B32/32K](../calculations/results/qwen36-capacity-b32-n32768.md)展示历史和并发影响；[保留整个checkpoint权重](../calculations/results/qwen36-capacity-all-weights.md)另加视觉/MTP的2,582,424,032 bytes，不宣称已含它们的执行状态。'
           '4090/5090的官方名义容量无法容纳默认BF16预算；80GB/96GB通过必要筛选仍不保证实际加载或性能。没有据此推断量化、卸载方案不可用。运行 `python3 calculations/calc.py qwen36-capacity --format md`，余量是可编辑假设；GB十进制，Mac统一内存与CPU/OS共享，真实峰值未知。',
           '## 4.6 封装与专用化的边界')
    insert('06-超节点.md', 'C36-memory-pool',
           '[内存池快照访问](../calculations/results/memory-pool-copies1.md)复算4×64GiB与80/48/32/32GiB：唯一数据192GiB，原本各节点未用80GiB但节点0缺16GiB；全局净余量为64GiB，不能混用两个数。完整80GiB任务迁到任一64GiB节点仍失败；允许拆分16GiB计算/数据的迁移另有容量可行条件，但执行成本未知。'
           '借用节点1的16GiB后物理占用64/64/32/32GiB。[两副本](../calculations/results/memory-pool-copies2.md)和[三副本](../calculations/results/memory-pool-copies3.md)分别额外占16/32GiB；故障表按实际持有数据与计算节点枚举，不把副本数乘进读带宽。'
           '每次完整读取16GiB，声明1/60、1、20次/秒，并扫描10/40GB/s、2/20us、128/4096个256B在途事务及5us启动，共24访问条件。使用min(B,Nq/L)乐观服务并明确假定为固定串行时长时，每组10个条件满足严格周期不增长积压；不保证真实队列稳定。'
           '[图6-8容量与读取路径](../calculations/results/memory-pool-layout.svg)来自同一结果。运行 `python3 calculations/calc.py memory-pool-access --copies 2 --format md`。本算例是反复读取不变快照；后接增长KV初始化/追加协议与实验6-10故障恢复成本综合比较，分别保留各自输入和适用边界。',
           '### 6.6.4 共享范围与故障影响')
    insert('06-超节点.md', 'C36-growing-kv',
           '[增长KV全部远端](../calculations/results/growing-kv-qwen8-all-r1.md)按已产生P=8192位置、G=128次单token追加，旧历史读取为G×P+G(G−1)/2，当前位置操作数另列；初始化复制、每步读一个副本和向全部副本写入分开。'
           '[两副本](../calculations/results/growing-kv-qwen8-all-r2.md)增加初始化与追加发送、不增加旧历史读取；声明同一发送接口串行、全副本提交后下一步才使用新epoch。'
           '[固定远端前缀/本地增长tail](../calculations/results/growing-kv-qwen8-prefix-r1.md)免去tail的远端重读和副本写入，却新增本地tail容量。[Qwen3.6](../calculations/results/growing-kv-qwen36-all-r1.md)只把10层完整attention的20KiB/位置算作历史，30层递推/卷积固定状态留本地，不能与Qwen8的144KiB/位置混用。'
           '[tail预算反例](../calculations/results/growing-kv-tail-budget-fail.md)明确容量失败；未因此把反事实通信时间称可实现方案。运行 `python3 calculations/calc.py growing-remote-kv --inputs calculations/scenarios/growing-remote-kv-example.json --format md`，可改模型、P/G、batch、副本和声明接口。'
           '时间轴仅为startup+bytes/B的通信骨架，KV生成计算、真实传输协议/控制流、故障恢复和完整内存峰值未知；不是实测decode或系统一致性实现。',
           '### 6.6.4 共享范围与故障影响')
    insert('06-超节点.md', 'C36-supernode-cost',
           '[实验6-10同请求集合](../calculations/results/supernode-qwen3-8b-n4-d250-healthy.md)固定8卡，比较TP8单副本、TP4两副本与TP2四副本；Qwen8/32真实BF16逐卡权重/KV/头归属先验容量，服务时长、24GB/卡与2GiBworkspace、信用费率和确定故障事件均为教学输入。54场景改变模型、1/4/8个同步请求、80/250/600ms完成目标与健康/短/长恢复。'
           '[单请求80ms](../calculations/results/supernode-qwen3-8b-n1-d80-healthy.md)仅TP8满足；四请求250ms时Qwen8的四个TP2副本费用较低；[Qwen32](../calculations/results/supernode-qwen3-32b-n4-d600-healthy.md)TP2因容量失败排除，不能拿它的假想速度排名。'
           '[长恢复](../calculations/results/supernode-qwen3-8b-n4-d250-long.md)只打断副本0，其他副本继续，未提交请求整次重启；完成/故障同刻先提交完整响应。放弃的完整阶段工作可计，打断阶段FLOPs未知。费用包含全部8卡的完整cohort时长，停机/重做不再重复收GPU费用，额外恢复费仅外部服务费；至少75%按时完成才比较总费用/有效请求，持平及无可选方案保留。'
           '[图6-9](../calculations/figures/supernode-cost/figure.svg)从同一完成记录重算1..1000ms的精确成本阶梯，空段表示容量/SLO不满足。运行 `python3 calculations/calc.py supernode-cohort-cost --inputs calculations/scenarios/supernode-cohort-example.json --format md`；`plot-supernode-cost`重绘。这里不是实际价格、硬件性能或输出质量评测；故障恢复时长是输入，真实加载/状态重建协议不由本例推断。',
           '> **图 6-9')
    insert('07-数据中心网络.md', 'C37-gradient',
           '[真实梯度两级归约](../calculations/results/gradient-fp32-hierarchical-nic2.md)选Qwen3-8B第一层gate梯度[12288,4096]，每rank不同样本贡献，声明FP32线格式为192MiB，不乘36层。8rank两服务器各4卡，完整平坦RS+AG共14轮，总发送2688MiB；连续ring跨服务器672MiB，[交错ring](../calculations/results/gradient-fp32-flat-interleaved-nic2.md)为2688MiB。'
           '分层先本地RS三轮，对应分片跨服务器AR两轮，再本地AG三轮；总发送仍2688MiB，跨服务器降为384MiB。逐消息保留元素区间、贡献身份和RS后所有权，逻辑归约加法352321536次，不能把AG也计为加法。'
           'NIC各25GB/s、server出口/入口及每向割集40GB/s、额外双向共享割集80GB/s、本地链路200GB/s和每轮2us均为教学输入。两NIC不复制载荷而切分区间，仍受共享出口限制；发送与接收端分别计账。'
           '逐轮max(资源bytes/速率)再串行相加是声明屏障下的必要下界，不是实测通信时间；预算通过仅表示未被此下界排除，训练计算与实际期限仍未知。运行 `python3 calculations/calc.py hierarchical-gradient --inputs calculations/scenarios/hierarchical-gradient-example.json --format md`；[BF16](../calculations/results/gradient-bf16-hierarchical-nic2.md)只改变声明线格式，不推断浮点重排等价。框架分桶、全模型训练、TP/PP/EP跨服务器与强弱扩展仍另核。',
           '### 7.2.2 TP、PP 与拓扑映射')
    insert('12-端边云协同.md', 'C66-image-request',
           '[完整图片请求](../calculations/results/image-request-original.md)固定给定30,000,000输入bytes与5,000,000成片bytes，上/下行20/100Mbit/s：上传12s、下载0.4s、单次残余RTT0.1s、模型0.3s，共12.8s。连接已可用，其他零时间是教学假设；[模型降至0.03s](../calculations/results/image-request-faster-model.md)只省0.27s。'
           '[同质量压缩条件](../calculations/results/image-request-up20.md)声明输入减为15MB、额外编码0.2s/解码0.1s，在20Mbit/s节省5.7s；上行400Mbit/s时打平，再快则额外编解码得不偿失。声明本地5s时，原始/压缩路径的上行等时点分别为400/7与400/13 Mbit/s；严格高于才远端更快，固定开销已超过本地时没有有限可赢上行。'
           '[图12-1](../calculations/figures/image-request/figure.svg)将原图上传、处理、编码与成片回传的依赖和完整成片曲线分列。运行 `python3 calculations/calc.py image-request-budget --inputs calculations/scenarios/image-request-example.json --format md`；参数允许声明准备/建链/队列/文件编解码与成片可用开销。复用连接只减建链，残余RTT只计一次。'
           '文件bytes不是由像素或VAE tensor推导，RAW/JPEG标签不证明等质量；压缩同质量是显式条件。阶段表是串行预算而非网络抓包时间线；预览与分块重叠尚未声明依赖，保持未知，不能把成片时间换名为预览时间。',
           '> **图 12-1')
    return {"updated": sorted(updated),
            "next": "python3 scripts/render_outline.py; python3 scripts/verify_outline.py"}
