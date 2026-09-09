"""H3's executed timestep/normalization work and a separately costed cache option."""
import struct


def f32(value):
    return struct.unpack('f',struct.pack('f',value))[0]


def calculate(config, schedules, stage, evaluations_per_step):
    """Use archived executions of the pinned CPU float32 scheduler, not ideal fractions."""
    steps=stage['steps']
    if str(steps) not in schedules['schedules']:
        return dict(status='unavailable',reason='Archived CPU schedules cover 1..128 forward evaluations')
    values=schedules['schedules'][str(steps)]
    h=config['hidden_size'];k=config['time_embed_dim'];mid=config['time_embed_hidden_dim']
    freq=config['freq_dim'];layers=config['num_layers'];s=stage['attention_tokens']
    step_rows=[];all_levels=set()
    # All four projections have bias; time MLP is FP32, modulation projection BF16.
    dimensions=[('time_linear1',freq,mid,1,4),('time_linear2',mid,k,1,4),
                ('block_adaln',k,18*h,layers,2),('final_adaln',k,2*h,1,2)]
    for index,(video,audio) in enumerate(zip(values['video'],values['audio'])):
        levels={video,audio}
        if stage['reference_video_tokens']:levels.add(f32(max(video,0.999)))
        if stage['reference_audio_tokens']:levels.add(f32(1.0))
        levels=sorted(levels);all_levels.update(levels);u=len(levels)
        matrices=[]
        for name,a,b,copies,width in dimensions:
            matrices.append(dict(operator=name,input_shape=[u,a],weight_shape=[a,b],
                output_shape=[u,b],copies=copies,matrix_flops=2*u*a*b*copies,
                weight_and_bias_bytes=(a*b+b)*width*copies,
                logical_operand_bytes=(u*a+a*b+b+u*b)*width*copies))
        # TimestepEmbedding activates its middle output. Every block/final AdaLN
        # activates temb independently, as the fixed forward actually does.
        silu=u*(mid+(layers+1)*k)
        bias=sum(u*b*copies for _,_,b,copies,_ in dimensions)
        norm_rows=(2*layers+1)*s
        # Each block: two scale/shift operations (3 arithmetic each), and two
        # gated residual additions (2 arithmetic each). Final scale/shift adds 3.
        modulation=(10*layers+3)*s*h
        counts=dict(ordinary_arithmetic=3*silu+bias+norm_rows*(4*h+1)+modulation,
                    exp=silu,negate=silu,rsqrt=norm_rows,
                    sinusoid_multiply=u*freq+freq//2,
                    sinusoid_divide=freq//2,sinusoid_exp=freq//2,sinusoid_log=1,
                    sin=u*freq//2,cos=u*freq//2)
        step_rows.append(dict(step=index,video_timestep=video,audio_timestep=audio,
            distinct_timestep_values=levels,unique_timestep_count=u,
            evaluations=evaluations_per_step,matrices=matrices,scalar_counts=counts,
            matrix_flops_per_evaluation=sum(r['matrix_flops'] for r in matrices),
            modulation_table_bf16_bytes=u*(layers*18*h+2*h)*2,
            per_row_modulation_operand_bytes=(layers*6+2)*s*h*2))
    per_request=sum(x['matrix_flops_per_evaluation']*evaluations_per_step for x in step_rows)
    u=len(all_levels)
    # Hypothetical full timestep-conditioning cache: store all block and final
    # modulation outputs, compute all supporting time MLP work once per value.
    precompute=sum(2*u*a*b*copies for _,a,b,copies,_ in dimensions)
    tables=u*(layers*18*h+2*h)*2
    scalar_totals={name:sum(row['scalar_counts'][name]*evaluations_per_step for row in step_rows)
                   for name in step_rows[0]['scalar_counts']}
    return dict(status='accounted',scheduler_grid_points=steps+1,
        forward_evaluations=steps*evaluations_per_step,
        schedule_capture_torch_version=schedules['torch_version'],
        executed_conditioning_matrix_flops=per_request,executed_scalar_counts=scalar_totals,
        step_rows=step_rows,actual_unique_timestep_values=sorted(all_levels),
        hypothetical_cache=dict(unique_timestep_count=u,table_bytes=tables,
            precompute_matrix_flops=precompute,
            precompute_silu_elements=u*(mid+(layers+1)*k),
            precompute_sinusoid_counts=dict(multiply=u*freq+freq//2,divide=freq//2,
                exp=freq//2,log=1,sin=u*freq//2,cos=u*freq//2),
            precompute_bias_adds=sum(u*b*copies for _,_,b,copies,_ in dimensions),
            matrix_work_saved_after_precompute=per_request-precompute,
            table_write_bytes=tables,
            table_reads_per_forward_sum_bytes=sum(x['modulation_table_bf16_bytes']*evaluations_per_step for x in step_rows),
            row_modulation_reads_sum_bytes=sum(x['per_row_modulation_operand_bytes']*evaluations_per_step for x in step_rows),
            note='Hypothetical persistent modulation cache: precompute and table IO are charged; per-token RMSNorm/modulation/gates remain. Pinned forward does not implement this cache.'),
        assumptions=[
            'steps仍指旧core字段声明的forward次数；实际scheduler传入steps+1网格点，终点zero不forward。CPU float32原方法执行结果已封存；1..128范围外明确unavailable，不伪装理论数列等于真实舍入。',
            '每step distinct值严格由video/audio与存在的参考噪声集合构成：visual max(t,0.999)、audio1.0，再按FP32归并；文本沿video timestep。',
            '本项覆盖时间MLP、每block与final AdaLN投影、SiLU/bias、关联RMSNorm及逐token调制/gated残差。其他attention/FFN内部scalar、VAE和文本编码器不因本项自动完成。',
            '缓存单独收费整个unique集合的时间MLP和modulation投影、表写读；不会消除按token的norm/scale/shift/gate，也不代表当前代码已有缓存。跨stage缓存复用未假定。',
        ])
