"""Two official image generators: latent packing and denoiser matrix subledger.

This is not a complete diffusion FLOP total: matrix/convolution stages are
separate from nonmatrix inventories and unpriced runtime work. No image or model weights are executed.
"""
from fractions import Fraction
import hashlib
import json

from ..paths import PROJECT
from ..sources import read_source, provenance
from ..units import positive_int
from .image_stages import text_stage, vae_stage
from .image_execution import operation_ledger, boundary_events, matrix_service_lower_bound
from .image_setup import calculate_setup
from .image_setup_lifetimes import setup_boundary_graph

MODELS = {'qwen-image-2512': 'qwenimage', 'flux2-klein-4b': 'flux2'}
DTYPES = {'bf16': 2, 'fp16': 2, 'fp32': 4}


def sources_and_index(kind):
    rows = json.loads((PROJECT / 'configs/image-generation.lock.json').read_text())
    files = {}
    for row in rows:
        data = (PROJECT / row['file']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Image-generation source hash mismatch: ' + row['file'])
        files[row['file'].split('/')[-1]] = data
    return rows, json.loads(files[kind + '-model_index.json'])


def branch_matrices(kind, config, image_tokens, text_tokens, batch, element_bytes):
    """Enumerate mathematical GEMMs; repeats are actual independent block matrices."""
    rows = []
    dim = config['num_attention_heads'] * config['attention_head_dim']
    total = image_tokens + text_tokens

    def gemm(name, m, k, n, repeats=1, activation_rhs=False, heads=1):
        batches = batch * heads
        rows.append(dict(name=name, lhs_shape=[batches, m, k], rhs_mathematical_shape=[k, n],
                         parameter_framework_shape=None if activation_rhs else [n, k],
                         rhs_kind='activation' if activation_rhs else 'weight', repeats=repeats,
                         matrix_flops=2 * batches * m * k * n * repeats,
                         matrix_weight_elements=0 if activation_rhs else k * n * repeats,
                         logical_lhs_operand_bytes=batches * m * k * element_bytes * repeats,
                         logical_rhs_operand_bytes=(batches if activation_rhs else 1) * k * n * element_bytes * repeats,
                         logical_output_bytes=batches * m * n * element_bytes * repeats))

    gemm('image_input', image_tokens, config['in_channels'], dim)
    gemm('text_input', text_tokens, config['joint_attention_dim'], dim)
    gemm('timestep_1', 1, 256, dim)
    gemm('timestep_2', 1, dim, dim)
    double = config['num_layers']
    single = config.get('num_single_layers', 0)
    for stream, tokens in (('image', image_tokens), ('text', text_tokens)):
        for projection in ('q', 'k', 'v', 'out'):
            gemm('double_' + stream + '_' + projection, tokens, dim, dim, double)
        if kind == 'qwenimage':
            inner = 4 * dim  # Audited FeedForward gelu-approximate default mult=4.
            gemm('double_' + stream + '_ff_in', tokens, dim, inner, double)
            gemm('double_' + stream + '_ff_out', tokens, inner, dim, double)
            gemm('double_' + stream + '_modulation', 1, dim, 6 * dim, double)
        else:
            inner = int(Fraction(str(config['mlp_ratio'])) * dim)
            gemm('double_' + stream + '_ff_gate_up', tokens, dim, 2 * inner, double)
            gemm('double_' + stream + '_ff_down', tokens, inner, dim, double)
            # Flux2 shares these modulation outputs across all double blocks.
            gemm('shared_double_' + stream + '_modulation', 1, dim, 6 * dim)
    if single:
        inner = int(Fraction(str(config['mlp_ratio'])) * dim)
        gemm('single_qkv_and_gate_up', total, dim, 3 * dim + 2 * inner, single)
        gemm('single_attention_and_ff_out', total, dim + inner, dim, single)
        gemm('shared_single_modulation', 1, dim, 3 * dim)
    gemm('joint_attention_qk', total, config['attention_head_dim'], total, double + single,
         activation_rhs=True, heads=config['num_attention_heads'])
    gemm('joint_attention_pv', total, total, config['attention_head_dim'], double + single,
         activation_rhs=True, heads=config['num_attention_heads'])
    gemm('output_adaln_modulation', 1, dim, 2 * dim)
    output = (config['out_channels'] or config['in_channels']) * config['patch_size'] ** 2
    gemm('image_output', image_tokens, dim, output)
    return rows


def calculate(model='qwen-image-2512', height=1024, width=1024, batch=1,
              text_tokens=512, negative_text_tokens=512, steps=None,
              guidance_scale=None, negative_prompt_present=True,
              dtype='bf16', decoded_dtype='fp32', output_type='image', effective_matrix_service=None, qwen_shape_cache_warm=False):
    inputs = locals().copy()
    if model not in MODELS or dtype not in DTYPES or decoded_dtype not in DTYPES:
        raise ValueError('Select an audited model and BF16/FP16/FP32 element format')
    for name in ('height', 'width', 'batch', 'text_tokens', 'negative_text_tokens'):
        positive_int(inputs[name], name)
    if not isinstance(negative_prompt_present, bool) or output_type not in ('image', 'latent'):
        raise ValueError('Provide a boolean negative-prompt flag and image/latent output')
    kind = MODELS[model]
    config = json.loads(read_source(f'configs/models/{model}/transformer/config.json'))
    vae = json.loads(read_source(f'configs/models/{model}/vae/config.json'))
    scheduler = json.loads(read_source(f'configs/models/{model}/scheduler/scheduler_config.json'))
    source_rows, index = sources_and_index(kind)
    if config['guidance_embeds'] or scheduler['_class_name'] != 'FlowMatchEulerDiscreteScheduler':
        raise ValueError('Guidance embedding or scheduler variant is not audited')
    if steps is None:
        steps = 50 if kind == 'qwenimage' else 4
    positive_int(steps, 'steps')
    scale = Fraction(str((4 if kind == 'qwenimage' else 1) if guidance_scale is None else guidance_scale))
    if isinstance(guidance_scale, bool) or scale < 0:
        raise ValueError('Guidance scale must be nonnegative and not boolean')
    if kind == 'qwenimage':
        vae_scale = 2 ** len(vae['temperal_downsample'])
        raw_channels = vae['z_dim']
        cfg = scale > 1 and negative_prompt_present
        distilled = False
    else:
        vae_scale = 2 ** (len(vae['block_out_channels']) - 1)
        raw_channels = vae['latent_channels']
        if index.get('is_distilled') is not True:
            raise ValueError('This accounting selects FLUX.2 klein 4B distilled only')
        distilled = True
        cfg = False  # Pipeline disables true CFG even if the caller passes scale > 1.
    if height % (2 * vae_scale) or width % (2 * vae_scale):
        raise ValueError('Use dimensions divisible by VAE scale × 2; no silent pipeline rounding')
    if config['in_channels'] != raw_channels * 4:
        raise ValueError('Transformer input must equal the once-packed raw VAE channels')
    packed_output = config['patch_size'] ** 2 * (config['out_channels'] or config['in_channels'])
    if packed_output != config['in_channels']:
        raise ValueError('Audited denoiser output must reconstruct the packed latent')
    latent_h, latent_w = height // vae_scale, width // vae_scale
    image_tokens = (latent_h // 2) * (latent_w // 2)
    latent_elements = batch * raw_channels * latent_h * latent_w
    packed_elements = batch * image_tokens * config['in_channels']
    if packed_elements != latent_elements:
        raise ValueError('Packing failed element conservation')
    tensors, branches = [], []
    for name, length in [('conditional', text_tokens)] + ([('unconditional', negative_text_tokens)] if cfg else []):
        rows = branch_matrices(kind, config, image_tokens, length, batch, DTYPES[dtype])
        for row in rows:
            tensors.append(dict(branch=name, **row))
        branches.append(dict(branch=name, text_tokens=length, joint_tokens=image_tokens + length,
                             one_forward_matrix_flops=sum(row['matrix_flops'] for row in rows),
                             forwards=steps,
                             denoising_matrix_flops=steps * sum(row['matrix_flops'] for row in rows),
                             text_embedding_bytes=batch * length * config['joint_attention_dim'] * DTYPES[dtype]))
    primary = [row for row in tensors if row['branch'] == 'conditional']
    vae_calls = int(output_type == 'image')
    text_details = [text_stage(model, row['branch'], row['text_tokens'], batch, DTYPES[dtype]) for row in branches]
    vae_details = vae_stage(model, height, width, batch, DTYPES[dtype]) if vae_calls else None
    text_work = sum(row['matrix_flops'] for row in text_details)
    text_dense_work = sum(row['dense_square_matrix_flops'] for row in text_details)
    vae_work = vae_details['dense_kernel_and_attention_flops'] if vae_details else 0
    vae_nonpadding = vae_details['nonpadding_and_attention_flops'] if vae_details else 0
    live_boundaries = [dict(object='prompt_embeddings', bytes=sum(r['text_embedding_bytes'] for r in branches),
                            created='text encoding', retained_until='final denoising step'),
                       dict(object='current_packed_latent', bytes=latent_elements * DTYPES[dtype],
                            created='noise initialization', retained_until='scheduler replacement / VAE handoff')]
    prior_embedding_bytes = 0
    for row in text_details:
        live_boundaries.append(dict(object='text_' + row['branch'] + '_returned_tensors',
                                    bytes=row['necessary_return_tensor_live_bytes'],
                                    independently_retained_prior_embedding_bytes=prior_embedding_bytes,
                                    created='complete text LM returns hidden states, logits and optional KV',
                                    retained_until='embedding extraction returns; not multiplied by denoise steps'))
        prior_embedding_bytes += row['embedding_output_bytes']
    if cfg:
        live_boundaries.append(dict(object='conditional_prediction_during_negative_forward',
                                    bytes=latent_elements * DTYPES[dtype], created='conditional DiT output',
                                    retained_until='CFG combines both predictions'))
    if vae_details:
        live_boundaries.append(dict(object='VAE_first_frame_feature_cache',
                                    bytes=vae_details['retained_first_frame_feature_cache_bytes'],
                                    created='decoder causal-convolution input clones accumulate',
                                    retained_until='decoder and final clamp complete, then clear_cache'))
    result = dict(schema_version=1, calculation='image-generation', model=model, scenario=inputs,
                sources=provenance(model) + source_rows, image_generation_matrices=tensors,
                image_generation_branches=branches,
                image_text_encoder_steps=[{k: v for k, v in row.items() if k not in ('matrices', 'nonmatrix')} for row in text_details],
                image_text_encoder_matrices=[matrix for row in text_details for matrix in row['matrices']],
                image_vae_convolutions=vae_details['convolutions'] if vae_details else [],
                image_stage_nonmatrix=[operation for row in text_details for operation in row['nonmatrix']]
                    + (vae_details['nonmatrix'] if vae_details else []),
                image_stage_lifetimes=live_boundaries,
                image_generation_stages=[
                    dict(stage='text_encode', pipeline_calls=len(branches), matrix_flops=text_work,
                         boundary_output_bytes=sum(r['text_embedding_bytes'] for r in branches)),
                    dict(stage='denoiser', pipeline_calls=steps * len(branches),
                         matrix_flops=sum(r['denoising_matrix_flops'] for r in branches),
                         boundary_output_bytes=latent_elements * DTYPES[dtype]),
                    dict(stage='vae_decode', pipeline_calls=vae_calls, matrix_flops=vae_work,
                         boundary_input_bytes=latent_elements * DTYPES[dtype] if vae_calls else 0,
                         boundary_output_bytes=batch * 3 * height * width * DTYPES[decoded_dtype] if vae_calls else 0)],
                summary=dict(vae_spatial_scale=vae_scale, raw_latent_channels=raw_channels,
                             raw_latent_shape=[batch, raw_channels, latent_h, latent_w],
                             packed_latent_shape=[batch, image_tokens, config['in_channels']],
                             raw_latent_elements=latent_elements, packed_latent_elements=packed_elements,
                             latent_bytes=latent_elements * DTYPES[dtype], image_tokens=image_tokens,
                             hidden_size=config['num_attention_heads'] * config['attention_head_dim'],
                             dual_stream_blocks=config['num_layers'], single_stream_blocks=config.get('num_single_layers', 0),
                             denoising_steps=steps, true_cfg_enabled=cfg, is_step_distilled=distilled,
                             supplied_guidance_ignored=distilled and scale > 1,
                             transformer_invocations=steps * len(branches), branch_count=len(branches),
                             denoising_matrix_flops=sum(r['denoising_matrix_flops'] for r in branches),
                             matrix_weight_elements_excluding_bias_norm=sum(r['matrix_weight_elements'] for r in primary),
                             matrix_weight_bytes_excluding_bias_norm=sum(r['matrix_weight_elements'] for r in primary) * DTYPES[dtype],
                             text_encoder_matrix_flops=text_work, vae_matrix_flops=vae_work,
                             text_encoder_dense_square_matrix_flops=text_dense_work,
                             vae_nonpadding_and_attention_flops=vae_nonpadding,
                             all_stage_dense_matrix_kernel_flops=text_dense_work + vae_work + sum(r['denoising_matrix_flops'] for r in branches),
                             all_stage_nonpadding_matrix_flops=text_work + vae_nonpadding + sum(r['denoising_matrix_flops'] for r in branches),
                             text_encoder_return_live_lower_bytes=max(r['necessary_return_tensor_live_bytes'] for r in text_details),
                             vae_first_frame_feature_cache_bytes=vae_details['retained_first_frame_feature_cache_bytes'] if vae_details else 0,
                             full_runtime_peak_bytes=None,
                             complete_generation_flops=None, complete_generation_seconds=None,
                             vae_decode_calls=vae_calls,
                             decoded_rgb_tensor_bytes=batch * 3 * height * width * DTYPES[decoded_dtype] if vae_calls else 0,
                             encoded_image_file_bytes=None),
                assumptions=[
                    '新增text阶段按B个独立同长prompt，无额外num_images_per_prompt复制；Qwen输入含34模板位置再截取，FLUX使用声明的max-length文本位置。两个完整LM wrapper即使只消费hidden仍执行全部层与全词表head，FLUX取9/18/27层不跳过后续层。固定transformers实现是声明的配套版本，不声称所有已发布运行环境都固定这个依赖。',
                    'text的all_hidden/logits/临时KV集合按声明dtype计必要同时存活张量，不含权重或workspace；FLUX显式use_cache=False，Qwen按config开启。返回对象与临时KV仅属于text阶段，不保留到每个去噪步；阶段表不得乘steps。',
                    'VAE固定use_tiling=False/use_slicing=False、单静态帧、inference模式；Qwen首帧time-upsample仅留Rep哨兵不执行time_conv，但普通causal Conv3d仍使用3x3x3及两帧零padding。dense kernel乘加和nonpadding有效乘加分列，均不承诺后端实际执行相同量。FLUX普通2D decoder四级各3resnet、三次空间上采样；mid attention均为单头非因果，不因Qwen类注释写causal而裁成三角。',
                    'Qwen首帧feature_cache逐causal conv保存独立输入clone直到decode末尾clear_cache；报告其必要保留容量和关键对象释放边界，不是完整显存峰值。VAE Norm、SiLU、bias、residual、softmax与nearest另列元素/向量次数；归一化FP32临时、kernel workspace、fused allocator及后处理仍未给完整生命周期峰值。',
                    '官方模型component config及固定diffusers源码；纯text-to-image、无参考图/编辑/LoRA/缓存跳层，尺寸限定VAE scale×2整除，不模仿原pipeline静默取整。DiT、纯文本encoder和非分块静态VAE内部已分别计矩阵/卷积子账，完整非矩阵算术和执行时间仍未全计。',
                    'Qwen raw16通道经2×2 packing变64，FLUX raw32变128；in_channels已经是packed宽度。Qwen输出patch²×16=64，FLUX patch1×128=128，不再对输入乘patch²。静态Qwen VAE的单帧维省略显示，不应用视频时间压缩。',
                    '每个流的Q/K/V/out独立，joint attention包含全部图像+文本位置的非因果QK与PV。Qwen GELU FFN宽4D；FLUX SwiGLU宽3D且输入为2×3D，单流将QKV+gate/up和attention/FF输出分别融合，仍列真实矩阵形状。',
                    'Qwen各双流块各有两套D→6D调制；FLUX双流/单流调制跨块共享，每次forward各算一次。时间MLP和输出AdaLN投影计入矩阵账；bias、norm、激活、RoPE、Softmax、CFG的norm重缩放和scheduler更新均未计，不能拿此参数小计作完整checkpoint容量。',
                    'text_tokens/negative_text_tokens是传入DiT的实际embedding长度，默认512为显式场景。FLUX默认text encoder把512位置及9/18/27层特征拼成7680维；Qwen最终hidden为3584维、模板截取/批内padding须另记录。正负长度不同分别计算，不假定CFG总工作恰好翻倍。',
                    'Qwen true CFG条件为scale>1且提供negative prompt，两次顺序transformer调用；FLUX klein 4B的model_index is_distilled=true强制单分支，guidance_embeds=false本身不足以判断CFG。50/4步是题设采用的官方模型卡示例，不是质量等价、全球最佳步数或隐藏的1000训练timesteps。',
                    '每步一次Euler更新，无自定义timesteps/sigmas、中断、回调改步或附加corrector。transformer_invocations与batch中处理样本数分开；文本编码在循环前，VAE在最终后各按条件执行，不乘去噪步数。text/VAE内部新增逐矩阵/卷积账，text使用有效因果边与另列dense square、VAE分别列dense kernel与nonpadding；非矩阵另列元素/向量/特殊函数次数，未把这些不同单位混成完整FLOPs。',
                    'GEMM逻辑A/B/C字节按逐矩阵一次接口读取/写入列出，权重在batch内理想复用；QK/PV的右操作数为激活，不计参数。全score输出是未融合数学接口量，不代表FlashAttention物化、实际HBM流量、工作区或显存峰值。CFG两分支共享权重，小计容量不乘NFE。',
                    '解码RGB张量使用显式decoded_dtype字节预算，不据force_upcast猜实际执行dtype；JPEG/PNG/RAW文件字节未知。VAE转换、权重加载/offload、随机数、网络与图片编码仍需补齐；不同模型相同分辨率/步数不证明同质量。',
                ])

    setup = calculate_setup(result, config, scheduler, qwen_shape_cache_warm)
    operations = operation_ledger(result, config) + [row for row in setup['operations'] if row['scope']=='request']
    result['image_setup_operations'] = setup['operations']
    result['image_setup_data_operations'] = setup['data_operations']
    result['image_setup_remaining'] = setup['remaining']
    memory = boundary_events(result)
    result['image_reference_operations'] = operations
    result['image_boundary_memory_events'] = memory['events']
    setup_memory = setup_boundary_graph(result, memory['events'])
    result['image_setup_boundary_memory_events'] = setup_memory.pop('events')
    result['image_setup_boundary_memory_summary'] = setup_memory
    result['image_matrix_service_bound'] = matrix_service_lower_bound(result, effective_matrix_service)
    special = {}
    for row in operations:
        for name, count in row['special_calls'].items():
            special[name] = special.get(name, 0) + count
    result['summary'].update(
        reference_ordinary_arithmetic_ops=sum(row['ordinary_arithmetic_ops'] for row in operations),
        reference_comparisons=sum(row['comparisons'] for row in operations),
        reference_special_calls=special,
        declared_boundary_graph_peak_bytes=memory['peak_bytes'],
        declared_boundary_graph_final_live_bytes=memory['final_live_bytes'],
        declared_boundary_graph_final_live_objects=memory['final_live_objects'],
        complete_nonmatrix_coverage=False)
    result['assumptions'].extend([
        '参考非矩阵算法单列ordinary arithmetic、comparison和exp/sqrt/rsqrt/tanh，特殊函数不是1 FLOP。LayerNorm用中心方差，RMS用平方均值，Softmax用全行max/shift/exp/sum/div并计一次score scale；SiLU采用sigmoid再乘，GELU为tanh三次多项式。它们是声明算法计数，不是torch融合指令或逐位结果保证。',
        'reference_accumulator_dtype=fp32是归约参考方案；不声称所有硬件/后端内部执行同dtype。Euler源码明确把sample转FP32、更新后转回prediction dtype；图采用无alias的显式FP32输入/输出及回转缓冲，表达一种参考执行组织，不冒称实际scalar promotion或allocator布局。',
        'boundary graph逐事件安排text返回/抽取、跨step embedding、CFG负分支期间cond预测、scheduler转换与Qwen VAE feature-cache；其峰值仅为声明的边界缓冲图。权重、block/conv内部live tensor、完整CFG norm scratch、VAE计算workspace、分配器和postprocess均不在图内，不能据此给硬件可装入结论或称全系统显存峰值。',
        'setup选择标准非Neuron/NPU/MPS频率路径；FLUX按源码FP64频率、FP32 cos/sin输出参考，未知实际后端不隐式套此dtype。Qwen初始化正负4096表为complex64；shape cache默认冷，重复step命中LRU，warm输入省形状构造但不省timestep。转换行只计明确请求的元素/语义读写，same-dtype为零转换，设备迁移与alias未知。索引/arange/cartesian/concat/fill和随机样本数不作为FLOPs。',
        '可选effective_matrix_service必须匹配input_dtype、FP32 accumulation及dense口径；给定值是该场景有效供给而非自动硬件峰值。串行下界按固定text→各去噪分支/步→VAE的直接矩阵/卷积算法，采用有效因果/nonpadding工作；未计非矩阵、IO和排队，不是可达时间或质量/SLO承诺，不能把它当完整CPU/GPU利用率。',
        '新增setup账已覆盖固定标准路径的DiT/text RoPE forward、timestep sin/cos和scheduler动态shift/terminal stretch，构造期Qwen表单列不混入请求。仍未完整计价text-RoPE初始化helper、NumPy linspace内部、全部dtype转换、随机数算法、tokenizer/图片编码以及实际融合下的归约重算；完整非矩阵覆盖标志为false，完整生成FLOPs/时间保持null。已列text/VAE操作只执行该阶段次数，DiT/CFG/update操作才随步骤变化。',
    ])
    return result
