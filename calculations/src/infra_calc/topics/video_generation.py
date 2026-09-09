"""Pinned H3 and Wan video geometry; matrix-core budgets, not generation timing."""
import hashlib
import json
from fractions import Fraction

from ..paths import PROJECT
from ..units import positive_int
from . import h3_conditioning, wan_text_encoding, wan_vae_decode


def evidence(model):
    """Verify both configuration and the implementation that interprets its geometry."""
    rows = json.loads((PROJECT / 'configs/video-generation.lock.json').read_text())['sources']
    selected = []
    configs = {}
    prefix = 'MiniMaxAI/MiniMax-H3' if model == 'minimax-h3' else 'Wan-AI/Wan2.2-TI2V-5B'
    for row in rows:
        relevant = row['repository'] in (
            (prefix, 'huggingface/diffusers', 'h3-schedule-capture') if model == 'minimax-h3'
            else (prefix, 'Wan-Video/Wan2.2', 'wan-vae-shape-capture')
        )
        if not relevant:
            continue
        raw = (PROJECT / row['file']).read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError(f"Video source hash/size mismatch: {row['file']}")
        if row['upstream_file']=='h3-schedules-fp32.json':
            configs['captured_schedules']=json.loads(raw)
        selected.append({k: row[k] for k in ('file', 'url', 'sha256', 'revision')})
        if row['repository'] == prefix and row['upstream_file'].endswith('config.json'):
            configs[row['upstream_file']] = json.loads(raw)
    if model=='minimax-h3':
        expected=next(row['sha256'] for row in rows
                      if row['upstream_file'].endswith('scheduling_minimax_h3.py'))
        if configs['captured_schedules']['source_sha256']!=expected:
            raise ValueError('Scheduler capture is not bound to the locked implementation')
    return configs, selected


def h3_frame_geometry(requested):
    """Diffusers align_num_frames/video_latent_num_frames: 17n+5 -> 5n+2."""
    positive_int(requested, 'requested_frames')
    aligned = requested + (5 - requested) % 17
    return aligned, (aligned - 5) // 17 * 5 + 2


def matrix_row(name, m, k, n, copies=1, width=2):
    """Independent GEMMs, beta=0 logical operands; not measured HBM traffic."""
    return dict(operator=name, a_shape=[m, k], b_shape=[k, n], c_shape=[m, n],
                copies=copies, flops=2*m*k*n*copies,
                logical_operand_bytes=(m*k+k*n+m*n)*width*copies,
                weight_matrix_parameters=k*n*copies)


def attention_rows(prefix, query, key, hidden, inner, ffn, heads, layers, swiglu=True):
    # Q/K/V rows are self-attention; callers supply cross-attention separately.
    rows = [matrix_row(prefix+'.qkv', query, hidden, inner, 3*layers),
            matrix_row(prefix+'.out', query, inner, hidden, layers),
            matrix_row(prefix+'.ffn_up', query, hidden, ffn, (2 if swiglu else 1)*layers),
            matrix_row(prefix+'.ffn_down', query, ffn, hidden, layers)]
    for name, m, k, n in [('qk',query,inner//heads,key), ('pv',query,key,inner//heads)]:
        row = matrix_row(prefix+'.'+name,m,k,n,heads*layers)
        row['weight_matrix_parameters'] = 0  # both operands are activations
        rows.append(row)
    return rows


def calculate(model='minimax-h3', frames=120, height=768, width=1344,
              text_tokens=256, steps=30, evaluations_per_step=None,
              regeneration_height=None, regeneration_width=None, regeneration_steps=15,
              reference_video_tokens=0, reference_audio_tokens=0,
              unique_timestep_values=30, positive_text_tokens=256, negative_text_tokens=128):
    """Budget selected core matrices with explicit NFE and caller-defined context sizes.

    H3 regeneration is a declared extra stage with the same text/audio sizes and
    the first stage's video tokens added as reference context. It is a geometry
    scenario, not a claim to reproduce the hosted Context-IR/regeneration service.
    """
    if model not in ('minimax-h3', 'wan2.2-ti2v-5b'):
        raise ValueError('Only pinned MiniMax H3 and Wan2.2-TI2V-5B are audited')
    if evaluations_per_step is None:
        evaluations_per_step = 2 if model == 'wan2.2-ti2v-5b' else 1
    for name, value in locals().copy().items():
        if name in ('model','regeneration_height','regeneration_width'):
            continue
        positive_int(value, name, allow_zero=name in ('reference_video_tokens','reference_audio_tokens'))
    if height % 32 or width % 32:
        raise ValueError('Explicit canvas must be divisible by 32; automatic aspect resizing is not modeled')
    if (regeneration_height is None) != (regeneration_width is None):
        raise ValueError('Supply both regeneration canvas axes')
    if regeneration_height is not None:
        for v in (regeneration_height, regeneration_width):
            positive_int(v,'regeneration_canvas')
            if v % 32:
                raise ValueError('Regeneration canvas must be divisible by 32')
        if model != 'minimax-h3':
            raise ValueError('H3 regeneration scenario is not a Wan pipeline')
    configs, sources = evidence(model)
    if model == 'minimax-h3':
        c = configs['transformer/config.json']
        h, inner = c['hidden_size'], c['num_attention_heads']*c['attention_head_dim']
        resolved, latent_frames = h3_frame_geometry(frames)
        audio = 2 * round(Fraction(resolved*40,24))
        vchannels, achannels, tdim = c['in_channels'], c['audio_in_channels'], c['text_dim']
        layers, ffn, heads = c['num_layers'], c['ffn_dim'], c['num_attention_heads']
    else:
        c = configs['config.json']
        if frames % 4 != 1:
            raise ValueError('Wan example requires 4n+1 frames; no silent frame adjustment')
        if text_tokens != c['text_len']:
            raise ValueError('Pinned Wan implementation pads text context to 512 rows')
        if reference_video_tokens or reference_audio_tokens:
            raise ValueError('Wan reference conditioning is not H3 packed context')
        h = inner = c['dim']
        resolved, latent_frames, audio = frames, (frames-1)//4+1, 0
        vchannels, achannels, tdim = c['in_dim'], 0, 4096  # official WanModel default text_dim
        layers, ffn, heads = c['num_layers'], c['ffn_dim'], c['num_heads']
    stages = []
    canvases = [('base',height,width,steps,reference_video_tokens)]
    first_video = latent_frames*(height//32)*(width//32)
    if regeneration_height is not None:
        canvases.append(('declared_regeneration',regeneration_height,regeneration_width,
                         regeneration_steps,reference_video_tokens+first_video))
    for stage_name, sh, sw, nsteps, vref in canvases:
        video = latent_frames*(sh//32)*(sw//32)
        va, aa = video+vref, audio+reference_audio_tokens
        if model == 'minimax-h3':
            total = va+aa+text_tokens
            rows = attention_rows('joint',total,total,h,inner,ffn,heads,layers)
            rows += attention_rows('text_refiner',text_tokens,text_tokens,h,inner,ffn,heads,c['num_refiner_layers'])
            rows += [matrix_row('video_input',va,vchannels*4,h,width=4),
                     matrix_row('audio_input',aa,achannels,h,width=4),
                     matrix_row('text_input',text_tokens,tdim,h),
                     # Pinned implementation projects every packed row before selecting modality rows.
                     matrix_row('video_output_all_rows',total,h,vchannels*4,width=4),
                     matrix_row('audio_output_all_rows',total,h,achannels,width=4)]
            score = heads*total*total*2
        else:
            total = video
            rows = attention_rows('self',video,video,h,inner,ffn,heads,layers,False)
            rows += [matrix_row('cross.q',video,h,h,layers),
                     matrix_row('cross.kv',text_tokens,h,h,2*layers),
                     matrix_row('cross.out',video,h,h,layers)]
            for name,m,k,n in [('cross.qk',video,h//heads,text_tokens),('cross.pv',video,text_tokens,h//heads)]:
                r=matrix_row(name,m,k,n,heads*layers);r['weight_matrix_parameters']=0;rows.append(r)
            rows += [matrix_row('video_patch',video,vchannels*4,h),
                     matrix_row('text_input_1',text_tokens,tdim,h),
                     matrix_row('text_input_2',text_tokens,h,h),
                     matrix_row('video_output',video,h,c['out_dim']*4)]
            score = heads*video*video*2
        evaluations = nsteps*evaluations_per_step
        per_eval = sum(r['flops'] for r in rows)
        stages.append(dict(stage=stage_name,height=sh,width=sw,steps=nsteps,evaluations=evaluations,
                           target_video_tokens=video,reference_video_tokens=vref,
                           target_audio_tokens=audio,reference_audio_tokens=reference_audio_tokens,
                           text_tokens=text_tokens,attention_tokens=total,
                           video_latent_shape=[vchannels,latent_frames,sh//16,sw//16],
                           video_latent_bf16_bytes=vchannels*latent_frames*(sh//16)*(sw//16)*2,
                           audio_latent_bf16_bytes=audio*achannels*2,
                           materialized_one_layer_self_score_bf16_bytes=score,
                           matrix_core_flops_per_evaluation=per_eval,
                           matrix_core_flops_all_evaluations=per_eval*evaluations,
                           logical_operand_bytes_per_evaluation=sum(r['logical_operand_bytes'] for r in rows),
                           operators=rows))
    for stage in stages:
        if model=='minimax-h3':
            stage['scheduled_conditioning']=h3_conditioning.calculate(
                c,configs['captured_schedules'],stage,evaluations_per_step)
            condition=stage['scheduled_conditioning']
            stage['matrix_core_plus_conditioning_flops']=(
                stage['matrix_core_flops_all_evaluations']+condition['executed_conditioning_matrix_flops']
                if condition['status']=='accounted' else None)
    wan_text=(wan_text_encoding.calculate(positive_tokens=positive_text_tokens,
              negative_tokens=negative_text_tokens) if model=='wan2.2-ti2v-5b' else None)
    wan_vae=(wan_vae_decode.calculate(latent_frames,height//16,width//16)
             if model=='wan2.2-ti2v-5b' else None)
    cache = None
    if model == 'minimax-h3':
        # Cache only the 50 large block modulation projections, not all model state.
        k, n = c['time_embed_dim'], 18*h
        cache = dict(block_modulation_weight_parameters=layers*(k*n+n),
                     block_modulation_weight_bf16_bytes=layers*(k*n+n)*2,
                     declared_unique_timestep_values=unique_timestep_values,
                     cache_table_bf16_bytes=unique_timestep_values*layers*n*2,
                     one_cache_precompute_matrix_flops=2*unique_timestep_values*layers*k*n,
                     status='hypothetical explicit cache; pinned forward recomputes these projections')
    return dict(schema_version=1,calculation='video-generation',model=model,sources=sources,
                wan_text_encoding=wan_text,wan_vae_decode=wan_vae,
                scenario=dict(model=model,frames=frames,height=height,width=width,text_tokens=text_tokens,
                              steps=steps,evaluations_per_step=evaluations_per_step,
                              regeneration_height=regeneration_height,regeneration_width=regeneration_width,
                              regeneration_steps=regeneration_steps,reference_video_tokens=reference_video_tokens,
                              reference_audio_tokens=reference_audio_tokens,unique_timestep_values=unique_timestep_values,
                              positive_text_tokens=positive_text_tokens,negative_text_tokens=negative_text_tokens),
                summary=dict(requested_frames=frames,resolved_frames=resolved,latent_frames=latent_frames,
                             hidden_size=h,attention_inner_dim=inner,layers=layers,
                             matrix_core_flops=sum(s['matrix_core_flops_all_evaluations'] for s in stages),
                             stages=len(stages),block_modulation_cache=cache,
                             matrix_core_plus_text_and_vae_flops=(sum(
                                 s['matrix_core_flops_all_evaluations'] for s in stages)+wan_text['matrix_flops']+wan_vae['matrix_flops']
                                 if wan_vae is not None else None),
                             matrix_core_plus_text_encoder_flops=(sum(
                                 s['matrix_core_flops_all_evaluations'] for s in stages)+wan_text['matrix_flops']
                                 if wan_text is not None else None),
                             matrix_core_plus_conditioning_flops=(sum(
                                 s['matrix_core_plus_conditioning_flops'] for s in stages)
                                 if model=='minimax-h3' and all(s.get('matrix_core_plus_conditioning_flops') is not None for s in stages) else None)),video_generation_stages=stages,
                assumptions=[
                    '旧matrix_core字段仅含原列出矩阵。新增Wan UMT5编码器、输出VAE矩阵与H3 scheduled_conditioning独立计入对应扩展合计，避免重算旧core。仍不等于完整模型FLOPs或实测时间：Qwen3-VL编码器、H3 VAE、Wan输入图像encode与未明确列出的scalar/调度/通信另核。',
                    'H3帧严格采用锁定公开实现的17n+5与5n+2分块规则，不套理想时间压缩4倍；立体声音频为2×round(frames/24×40)行。Wan为4n+1帧、(F−1)//4+1 latent，text固定padding512。',
                    '矩阵输入/输出形状和逻辑操作数读写可复算；逻辑bytes不是HBM流量，物化score只说明朴素驻留，不表示FlashAttention实际分配。H3输出两head对全部联合行计算后才选模态。',
                    '默认Wan按官方入口每步conditional/unconditional两次forward，H3默认一次；显式evaluations_per_step覆盖用于声明对照。NFE=steps×evaluations_per_step。参考token为外部已编码token数；没有自动解码/重采样参考媒体。',
                    'H3第二阶段是声明的regeneration几何场景：新canvas、原有参考加base视频tokens；真实托管Context-IR、参考预处理、音频策略与实际Regenerate-2K步表未重现。两阶段预算分开后相加。',
                    'AdaLN表为固定权重、唯一噪声值集合和三模态的假设预计算预算，未从steps猜unique值；每模型/权重/噪声计划变化须重算。它不等于当前锁定forward已实现缓存，也不算实际显存节约。',
                    'BF16逻辑元素2B；H3公开实现video/audio输入与输出projection保持FP32故这些行按4B，其余core按2B。峰值选择需匹配各算子精度，未引用GPU宣传算力。',
                ])
