"""Read-only chapter 2 requirement/evidence inventory; writes only this directory."""
import ast
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BOOK = json.loads((ROOT / 'calculations/scenarios/book.json').read_text())
rows = []


def add(key, section, requirement, status, modules, groups, done, gap, examples=()):
    evidence = []
    for module in modules.split(',') if modules else []:
        path = ROOT / ('calculations/src/infra_calc/' + module + '.py')
        if not path.exists():
            raise ValueError(path)
        tree = ast.parse(path.read_text())
        evidence.append({'file': str(path.relative_to(ROOT)), 'sha256': sha(path),
                         'functions': [{'name': n.name, 'line': n.lineno}
                                       for n in tree.body if isinstance(n, ast.FunctionDef)]})
    scenarios = []
    for group in groups.split(',') if groups else []:
        for index, scenario in enumerate(BOOK.get(group, [])):
            sid = scenario.get('id')
            if group == 'generation':
                sid = f"generation-{scenario['model']}-s{scenario['history']}-g{scenario['steps']}"
            elif group == 'states':
                sid = f"state-{scenario['model']}-n{scenario['length']}-b{scenario.get('batch', 1)}"
                sid += '-' + scenario.get('mla_path', 'native')
            result = ROOT / f'calculations/results/{sid}.json'
            scenarios.append({'book_pointer': f'/{group}/{index}', 'input': scenario,
                              'result': str(result.relative_to(ROOT)) if result.exists() else None,
                              'result_sha256': sha(result) if result.exists() else None})
    rows.append(dict(id=key, section=section, original_requirement=requirement,
                     status=status, implemented_scope=done, remaining_scope=gap,
                     code=evidence, scenarios=scenarios,
                     additional_evidence=list(examples)))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


add('R01','2.1 / 实验2-1','四token三层RNN与因果Transformer的矩阵、状态、依赖；各自同模型缓存/重算输出一致。','complete','topics/sequence_dependencies','sequence_dependencies','固定教学权重、全部层依赖边、4/5位置矩阵及状态、十组同模型数值对照已落盘。','仅此明确教学实验完成，不声称checkpoint或GPU并行时长。')
add('R02','2.2 / 实验2-2','Qwen3-8B实际层形状，QKVO、GQA、SwiGLU、归一化/位置/残差；矩阵与标量分类。','complete','models/qwen3','forward','Qwen3实际参数、逐算子shape/repeats、有效因果与矩形注意力、普通算术/特殊调用分列。','完成声明的逻辑算子契约；物理后端代价属于独立实现层。')
add('R03','2.2 / 实验2-2','B1完整8192 prefill、B1/B64 decode、6144命中后2048新输入；权重常驻、读取、新KV和输出头范围。','complete','models/qwen3','forward','四指定场景均有JSON/MD，head last/all显式；操作数载荷与常驻分开。','真实HBM与实际工作区不由这些逻辑行推导。')
add('R04','2.3.1','保存容量、逐步旧历史读取、追加、整段生成累计工作及D=G−1边界。','complete','topics/cache_sequence,models/qwen3','cache_sequence,generation','明确steps为decode调用次数；缓存与重算attention对照、旧读/append/末状态分别计数；Qwen整段forward累计。','该完成状态仅对应声明格式的逻辑累计公式，不覆盖所有模型整请求。')
add('R05','2.3.2','同隐藏宽/上下文改变MHA/MQA/GQA KV头数，比较容量、读取和质量。','partial','topics/cache_sequence','cache_sequence','MHA/GQA/MQA声明几何变体，Q头attention计算不随KV缩减。','没有同任务/受控训练或已核质量记录；几何替换不能证明模型输出或质量等价。')
add('R06','2.3.3 / 实验2-3','K3 MLA潜变量/NoPE-RoPE/上投影/门，展开与吸收路径矩阵和新增缓存。','complete','topics/k3_mla','k3_mla','compact与expanded均有prefill/decode；输出门约束不合法的矩阵合并，缓存latent与RoPE明确。','限定代数与源路径账，不把compact代数方案当官方运行时已部署。')
add('R07','2.3 / 实验2-3','缓存实验加入峰值workspace、并行复制与前缀检查点。','partial','topics/cache_sequence,topics/dense_placement','cache_sequence,dense_placement','checkpoint包含K3递推/卷积状态而非仅MLA；Qwen8/32的TP/PP/DP已有独立放置账。','cache_sequence明确排除workspace与parallel replication；缺同一K3 MLA路径的临时张量生命周期/分片复制联合预算。')
add('R08','2.4.1 / 实验2-4','V4 Flash43层及Pro61层窗口/CSA/HCA、compressor/indexer、topk、压缩更新逐步骤。','partial','topics/v4_attention,topics/v4_attention_arithmetic,topics/v4_forward,topics/state','v4_attention,v4_forward,states','配置分层、矩阵/压缩/扫描/稀疏有效与tile口径、FP32槽与实际checkpoint格式已有子账。','forward coverage仍缺转换、部分复制/初始化和完整访问；独立v4_fp8_linear不能自动视为已汇入全部forward。')
add('R09','2.4.1 / 实验2-4','完整以及命中前缀后的prefill；8K/128K/1M × B1/64；压缩块完成边界峰值。','partial','topics/v4_attention,topics/state','v4_attention,states','状态有8K/128K/1M代表点；attention有8192完整prefill和B64decode。','明确代码拒绝history>0且tokens>1；缺缓存前缀多token延续路径，未完成六格全账及压缩边界扫描。')
add('R10','2.4.2 / 实验2-5','K3 69KDA+24MLA，真实state精度，短卷积与prefill块/单步递推分别计。','partial','topics/k3_kda,topics/kda_chunk,topics/k3_forward,topics/state','k3_kda,k3_forward,states','全逻辑矩阵、块核心替换、递推/卷积/MLA独立状态；不是decode流量乘prefill长度。','checkpoint A_log128与配置/实现96冲突仍明确；不能确认原checkpoint可直接完整执行，运行时混合格式和完整读写未闭合。')
add('R11','2.4.2 / 实验2-5','K3/V4同长度batch统一状态精度、再实际格式；完整prefill/decode读写与prefix checkpoints。','partial','topics/k3_forward,topics/v4_forward,topics/cache_sequence,topics/state','k3_forward,v4_forward,cache_sequence,states','有整模型逻辑子账与已锁checkpoint格式；有K3前缀检查点必要内容。','未有统一同请求表涵盖所有长度、两种精度、复制/恢复成本与完整算子读写；各forward runtime bytes仍unknown。')
add('R12','2.4 / 实验2-5','固定检索质量记录与最小运行验证，说明节省/新增成本。','partial','','','V4原生六专家、阶段诊断及四层短前向是真实证据。','10/32768原数值阈值未过，四层运行不能替代完整模型检索；K3/V4固定质量对照仍需真实执行。',['experiments/ch02/02-05/expert-preflight/README.md','experiments/ch02/02-05/expert-stages/README.md','experiments/ch02/02-05/native-layer-probe/README.md'])
add('R13','2.5 / 实验2-6','V4 256选6+shared与K3 896选16 latent专家的每专家n_e、矩阵/参数/读取/激活；复用与总/活跃区别。','complete','topics/experts','experts','均匀/集中路由，hash/scoring、latent up/down和shared区别；FP4 packed+scale与FP8 kernel/tile另列。','完成声明路由直方图下专家账；不是实际路由trace或GPU性能。')
add('R14','2.5.3','连接注意力、专家、mHC/AttnRes及整模型权重，不把mHC乘宽施加到全部矩阵。','complete','topics/hyper_connections,topics/attn_res,topics/v4_forward,topics/k3_forward','hyper_connections,attn_res,v4_forward,k3_forward','已联合源枚举逻辑参数/矩阵，residual组合不重复计算。','仅逻辑结构汇总完成；量化转换/实际峰值仍由R08/R10追踪。')
add('R15','2.5 / 实验2-6','V4/K3同专家任务比较本机、多设备、CPU/GPU；加通信后重新选择。','partial','topics/expert_locality,topics/grouped_experts','expert_locality,grouped_experts','Qwen235专家已有CPU搬激活vs搬权重、8rank分布与padding、精确复用分界。','这两个现成入口调用Qwen MoE配置验证，不能直接证明V4/K3实际格式/latent专家放置；缺原题二模型联合通信比较。')
add('R16','2.6.1 / 实验2-7','实际8/32/70/235B × 24/48/80GB单卡 × BF16/8/4：scale、尾组、高精度部分、KV与并发。','complete','topics/capacity_scan','capacity_scan','四实际代表全部已入book，包括DeepSeek官方蒸馏Llama70B，尾组与字节容量边界。','在明确2GiB固定workspace和声明量化方案下完成；非已验证低位宽checkpoint或实测workspace。')
add('R17','2.6.1 / 实验2-7 / extensions','同四模型八卡预算，235B 8×80GB/8×24GB；工作区、复制、运行余量。','partial','topics/dense_placement,topics/capacity_scan','dense_placement,capacity_scan','Qwen8/32分片有TP/PP/DP基础，70B BF16六场景已公共接入，单卡四模型已完。','70B BF16逐rank复制已补，但没有完整四规模八卡×三格式表；70B低位宽、235B逐卡权重/KV复制、workspace与余量仍须连接。')
add('R18','2.6.2 / 实验2-7','相近参数量改变层数/宽度/FF比例或专家颗粒，求容量、读取、通信使选择改变条件。','missing','','','正文有量纲与KV头不可整分约束。','缺可执行固定参数预算的架构变体扫描、逐矩阵/串行深度与通信条件转折；不能用固定模型容量表代替。')
add('R19','2.6.3','V4/K3 MTP训练层、发布配置与后端启用层；草稿/验证及维护的工作。','partial','topics/speculative_budget,topics/speculative_round','speculative_budget,speculative_round','通用speculative收支模型和checkpoint MTP分账存在。','通用接受率/候选预算不是V4/K3固定源码MTP前向；需分别锁定启用条件并接真实矩阵、缓存与验证成本。')
add('R20','2.6.4 / 实验2-8与extensions','固定轨迹输入、reasoning/nonreasoning、工具轮次、复用间隔、缓存比例；等均值不同分布；扩写要求median/p95/长尾。','partial','topics/agent_trace','agent_trace','原件复制+SHA、真实token阶段守恒、三种命中比例、实际工具时间和等均值Fraction对照均具备。','正文实验画像已满足，但扩写明确要求p95；analyze.dist仅count/min/median/max/mean，未输出p95。需声明分位数算法补现有有限样本分布，不需新增请求。',['experiments/ch02/02-08/analyze.py','experiments/ch02/02-08/summary.json','experiments/ch02/02-08/README.md'])
add('R21','2.6.4 / 本章交付','将固定轨迹已知新输入/缓存/输出长度代入本章模型资源表。','partial','topics/agent_trace,topics/request_trace,models/qwen3','agent_trace,request_trace,generation','agent_trace有真实时间账，request_trace有教学资源积分，Qwen generation可算固定长度。','02-08明确未调用资源模型；仍需逐原请求cached/input/output映射同模型prefill+G−1 decode与KV，不应给等均值离线赋权伪造缓存/时延。')
add('R22','2.6.5 / 实验2-9 / resource case','同请求Qwen8/V4Flash/Pro/K3：prefill、每步/整段生成、权重/状态/读写，再容量Roofline链路及质量条件。','partial','topics/v4_forward,topics/k3_forward,models/qwen3,topics/cache_sequence','v4_forward,k3_forward,forward,generation,cache_sequence','模型单次逻辑账、Qwen累计、K3历史累计与硬件下界基础均存在。','无四模型同请求全段汇总；V4非线性compressor/topk边界不能用固定一步乘G；完整实际bytes和任务质量不能伪造。')
add('R23','2.6.5 / extensions','HBM/主存/远程命中、请求/token权重、复用间隔与查找/取回时间联动。','partial','topics/cache_route,topics/cache_residency','cache_route,cache_residency','有独立缓存路由条件模型和分层驻留预算。','缺与本章同请求四模型状态表示及真实复用记录连接；不需要在F01/P2内扩成全缓存系统实现。')
add('R24','2.3补充V3 / 2.4补充Qwen3.5','实际模型形状与固定实现的全基础文本矩阵，vision/MTP分账。','partial','topics/v3_forward,topics/qwen35_forward','v3_forward,qwen35_forward','V3基础文本与Qwen3.5 1038文本形状及cold/prefix/chunk-tail路径已接入。','完整runtime转换/生命周期及辅助vision/MTP未全覆盖；来源与基础矩阵完成不等于所有forward。')
add('R25','generative case / Omni+Fish','文本/音频encoder、Thinker/slow、Talker/fast逐码本循环、codec波形预算及阶段依赖。','partial','topics/omni_audio,topics/omni_audio_encoder,topics/omni_understanding','omni_audio,omni_audio_encoder,omni_understanding','已有逐阶段AR/码本循环、Omni/Fish codec内部子账、声明速率条件和状态生命周期。','参考音频预处理、完整控制token/采样与所有primitive执行/lifetimes未闭合；输入理解与输出speech非所有真实请求组合均连接。')
add('R26','generative case / QwenImage+FLUX','text encoder→latent/patch→DiT循环/CFG→VAE，逐矩阵/卷积/非矩阵/bytes及阶段存活。','partial','topics/image_generation,topics/image_setup,topics/image_execution','image_generation','两个代表均有完整主要矩阵/卷积阶段，CFG分支、setup操作、边界必要存活集合，文本/VAE不乘steps。','非矩阵primitive完全展开、归一化FP32临时与完整allocator/实际workspace未全计；不能称全请求完整FLOPs或显存峰值。')
add('R27','generative case / H3+Wan','时间latent、DiT/NFE、两个阶段、文本前处理与VAE；精度/接口量分类。','partial','topics/video_generation','video_generation','H3固定帧规则/联合模态矩阵/scheduled conditioning与Wan UMT5、VAE子账已落盘。','H3 QwenVL前端、H3 VAE、真实托管第二阶段与输入媒体预处理未复现；Wan部分scalar/输入图像encode与调度未闭合。')
add('R28','generative case / VL输入不能免费','视觉patch/block/DeepStack、encoder缓存、语言prefill+生成及位置/KV桥。','partial','topics/vision_encoding,topics/vl_request,topics/vl_position_bridge','vision_encoding,vl_request','共享已出现VL位置桥4场景，三轴mRoPE/生成计数及混合尺寸接语言账。','限定预处理后图像、声明布局和batch1位置路径；图像读取/resize/tokenizer与完整primitive实际访存仍不在总账。')
add('R29','resource case五项交付','每模型常驻weights/history/recurrent/峰值workspace，全/前缀prefill、decode、整段生成和指定精度硬件约束。','partial','topics/capacity_scan,topics/k3_forward,topics/v4_forward','capacity_scan,k3_forward,v4_forward','权重与状态已大量覆盖、各关键阶段有可复算逻辑子账。','R07/R09/R11/R17/R22合起来仍缺前缀路径、完整累计和峰值workspace；不能以checkpoint bytes或单步roofline替代五项。')

# Exact experiment paragraphs and direct-source bindings remain available independently of our paraphrase.
main = ROOT / 'outlines/02-模型架构.md'
ext = ROOT / 'outlines/extensions/02-模型架构.md'
requirements = []
for path in (main, ext):
    lines = path.read_text().splitlines()
    for index, line in enumerate(lines):
        if '**实验 2-' in line or '**图 2-' in line:
            body = [line]
            j = index + 1
            while j < len(lines) and (lines[j].startswith('>') or not lines[j]):
                body.append(lines[j]); j += 1
            requirements.append({'file': str(path.relative_to(ROOT)), 'line': index + 1,
                                 'exact_text': '\n'.join(body).strip()})
source_paths = [main, ext, ROOT / 'calculations/scenarios/book.json',
                *(ROOT / ('case-studies/' + n + '.md') for n in
                  ('model-resource-accounting', 'model-operator-examples', 'generative-multimodal-models'))]
result = {'schema_version': 1, 'scope': 'Chapter 2 main text, its extension and three directly referenced cases; read-only shared tree',
          'snapshot_files': [{'file': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in source_paths],
          'status_semantics': {'complete': 'explicit bounded mathematical/record requirement satisfied; no runtime extrapolation',
                              'partial': 'actual reusable result exists but original requirement still has named missing scope',
                              'missing': 'no executable result for this requirement found in inspected chapter-related paths'},
          'counts': dict(Counter(r['status'] for r in rows)), 'requirements': rows,
          'original_experiment_and_figure_requirements': requirements,
          'cross_chapter_transfer': 'model-operator-examples kernel/backend/fusion/retile/register/shared-memory validation belongs to chapter5; retain reference, do not declare it done or expand chapter2 closure to all chapter5.',
          'newly_integrated_candidate': 'research/llama70-placement BF16 six-scenario candidate is now integrated in public dense_placement/book; remaining eight-card requirement includes other model/format combinations.',
          'figures': 'All eight original SVG/curve plans retained in exact excerpts. Sequence graph JSON and 02-08 profiles.png are evidence, but do not establish all planned chapter figures are delivered.'}
(OUT / 'coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
lines = ['# 第 2 章原要求覆盖审查', '',
         '这是第 2 章正文、配套扩写及三份直接 case 引用的有限审计。complete 只表示该行明确数学或固定记录要求已满足；不会把逻辑字节当 HBM、元数据核验当完整前向或固定工作区当实际峰值。原实验与图题逐字保存在 coverage.json。', '',
         '本快照已纳入新接入的 70B 单卡容量、BF16多卡六场景和 VL position bridge，未沿用旧正文“70B 容量待补”的结论。', '',
         '| 条目 | 原范围 | 状态 | 已有证据与有限缺口 |', '|---|---|---|---|']
for row in rows:
    lines.append(f"| {row['id']} | {row['section']}：{row['original_requirement']} | {row['status']} | {row['implemented_scope']} 剩余：{row['remaining_scope']} |")
lines.extend(['', '## 原实验的整体判定', '',
              '| 实验 | 判定 | 对应条目 |', '|---|---|---|',
              '| 2-1 | complete（明确教学范围） | R01 |',
              '| 2-2 | complete（逻辑算子与操作数范围） | R02–R03 |',
              '| 2-3 | partial | R04–R07；workspace/并行与质量不可遗漏 |',
              '| 2-4 | partial | R08–R09；源路径明确拒绝多token cached continuation |',
              '| 2-5 | partial | R10–R12；真实检索质量未完成 |',
              '| 2-6 | partial | R13–R15；Qwen放置不能代替V4/K3 |',
              '| 2-7 | partial | R16–R18；四模型单卡完成，八卡与架构变体未完 |',
              '| 2-8 | partial（正文固定画像完成；扩写p95缺） | R20；资源代入另见R21 |',
              '| 2-9 | partial | R22–R23 |', '',
              '## 下一步可独立验收的计算', '',
              '1. **实验 2-7 八卡容量补齐**：接真实四模型形状，显式TP/PP/EP与KV复制，BF16和声明8/4-bit逐rank权重/scale/KV/工作区/余量。固定24/48/80GB卡容量与8K/32K历史，至少包含235B的8×24/80GB和70B；守恒验证全局唯一权重与复制增量，容量阈值±1byte。保持2GiB预算是输入而非实测peak。',
              '2. **实验 2-9统一累计逻辑账**：一个S/P/G/B契约连接四模型，D=max(G−1,0)，对decode位置逐一计算V4压缩边界/索引扫描并求和；输出各模型旧读/更新/末驻留与FLOPs，拒绝缺失的完整runtime bytes。先完成数学预算，再给有证据的精度Roofline子项，quality保留有限未完成项。',
              '3. **实验 2-4 cached-prefix延续**：先从锁定源码证明可行调度；当前history>0、tokens>1直接抛错，不能把接口换成完整prefill冒充命中。以逐单token连续更新为受限参考并独立验证块边界；完整prefill chunk路径需另证。',
              '4. **实验 2-8资源代入**：只读取已经封存的实际每请求input/cached/output，连接Qwen8前向与整段生成；区分返回EOS与模型调用，检验G=1无decode、新输入=0的合法/非法语义。等均值赋权组只保留数学长度分布，不附会真实缓存或GPU时间。',
              '5. **实验 2-7架构变体**：选一个真实可行基点，声明等参数约束及整数近似误差，变L/H/FF或专家粒度，输出矩阵尺寸、串行层数、驻留/访问/通信不等式的切换点。质量仍须独立数据，不能从FLOPs推断。', '',
              '## 文档边界与证据', '',
              '第2章同时保留旧“全模型前向/块KDA仍待”的阶段记录和新增forward结果；旧记录不能当作今日缺失证明。反向也一样，新逻辑forward不能覆盖同段明列的运行时缺口。image结果部分旧assumptions仍称norm/CFG未计，而后增reference_operations已提供子账；应按实际字段判定，建议后续清理措辞，避免把兼容旧字段误读为无新计算。', '',
              '八张配图计划仍按原文保留。02-08已有profiles.png，sequence_dependencies已有依赖图数据，但本次未发现足以证明全部8张指定图及其曲线交付的证据。第5章算子实现/融合专项被保留为跨章引用，不作为本次无限扩大的阻塞。', '',
              'coverage.json包含函数定义行、文件SHA、book JSON指针、实际JSON结果路径与SHA；代码存在和结果存在仅用于定位，状态由原要求与代码排除项共同判定。本次未修改shared、未执行GPU或重新下载权重。'])
(OUT / 'README.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'counts': result['counts'], 'requirements': len(rows),
                  'mapped_scenarios': sum(len(r['scenarios']) for r in rows),
                  'missing_result_references': sum(s['result'] is None for r in rows for s in r['scenarios'])}, indent=2))
