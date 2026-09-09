"""Static-image Qwen3-VL request: vision, causal language prefill, then decode."""
from ..models import qwen3
from ..schema import Operator, Scenario, Weight
from ..sources import model_config
from ..units import positive_int
from . import multimodal_cache, vision_encoding, vision_batch


MODEL = multimodal_cache.MODEL


def text_config():
    config = model_config(MODEL)['text_config']
    if config['model_type'] != 'qwen3_vl_text':
        raise ValueError('Expected the pinned Qwen3-VL text architecture')
    # Common GQA/SwiGLU geometry is shared; position encoding is separately audited.
    for field in ('hidden_size','intermediate_size','num_hidden_layers','num_attention_heads',
                  'num_key_value_heads','head_dim','vocab_size','max_position_embeddings'):
        positive_int(config[field],field)
    rope=config['rope_scaling']
    if (config['attention_bias'] or config['hidden_act']!='silu'
            or config['num_attention_heads']%config['num_key_value_heads']
            or config['head_dim']%2 or rope.get('rope_type')!='default'
            or not rope.get('mrope_interleaved')
            or sum(rope['mrope_section'])!=config['head_dim']//2):
        raise ValueError('Unsupported VL language geometry or M-RoPE variant')
    return config


def language_stage(config, tokens, history, width, kv_width, visual_positions=0,
                   deepstack_branches=0):
    """Reuse the common audited decoder, replacing its one-dimensional RoPE table."""
    scenario=Scenario(tokens=tokens,history=history,output_head='last',weight_bytes=width,
                      activation_bytes=width,kv_bytes=kv_width,score_bytes=4)
    ops=qwen3.build_operators(config,scenario)
    h=config['hidden_size'];d=config['head_dim'];f=config['intermediate_size']
    angles=3*tokens*d//2
    for index,op in enumerate(ops):
        if op.name=='rope_table':
            ops[index]=Operator('mrope_table','position',
                {'position_ids':[3,1,tokens],'axis_frequencies':[3,1,tokens,d//2],
                 'cos_sin_each':[1,tokens,d]},
                scalar_flops=3*angles,special_ops={'sin':angles,'cos':angles},
                activation_read_bytes=d//2*4+3*tokens*8,
                activation_write_bytes=2*tokens*d*width,
                notes='固定VL实现：3轴频率outer product，cos/sin各乘scale，再交错重组；FP32中间/索引构造另计。')
    if visual_positions:
        ops.append(Operator('image_embedding_replace','multimodal',
            {'prompt':[tokens,h],'image_embeddings':[visual_positions,h]},
            activation_read_bytes=(tokens+visual_positions)*h*width+tokens,
            activation_write_bytes=tokens*h*width,
            notes='input_ids路径先lookup全部位置含图像placeholder，再masked_scatter替换；mask按每位置bool共享，不额外生成视觉token。'))
        ops.append(Operator('deepstack_prompt_clone','multimodal',{'prompt':[tokens,h]},
            repeats=deepstack_branches,activation_read_bytes=tokens*h*width,
            activation_write_bytes=tokens*h*width,
            notes='锁定Transformers _deepstack_process每次clone整个prompt；优化后端可省，但不能无证据视为零。'))
        ops.append(Operator('deepstack_visual_add','multimodal',
            {'selected_hidden':[visual_positions,h],'deepstack_features':[visual_positions,h]},
            repeats=deepstack_branches,scalar_flops=visual_positions*h,
            activation_read_bytes=2*visual_positions*h*width,
            activation_write_bytes=visual_positions*h*width,
            notes='视觉5/11/17层输出分别注入语言0/1/2层之后；仅图像位置相加，decode不再注入。'))
    weights=qwen3.base_weights(config)+[
        Weight('model.layers.{layer}.mlp.'+name+'.weight',shape,config['num_hidden_layers'])
        for name,shape in (('gate_proj',(f,h)),('up_proj',(f,h)),('down_proj',(h,f)))]
    weights=[Weight(w.name.replace('model.','model.language_model.',1)
                    if w.name.startswith('model.') else w.name,w.shape,w.copies,w.note)
             for w in weights]
    result=qwen3.summarize(MODEL,config,scenario,ops,weights)
    result['calculation']='qwen3-vl-language-stage'
    # Generic Dense adapter prose assumes one-dimensional equal positions; this stage does not.
    result['assumptions']=[
        '采用Qwen3-VL真实text config的GQA/SwiGLU和M-RoPE；位置值外部提供，长度预算不执行模板或rope index生成。',
        '矩阵为有效因果对，矩形物化分数与逻辑bytes另列；不是具体attention kernel或实测HBM。',
        'input_ids lookup包含placeholder后替换图像embedding；DeepStack只在prefill注入。权重embedding/head按官方tie共享计容量，head GEMM仍执行。',
    ]
    return result


SUM_FIELDS=('matrix_flops','scalar_flops','weight_read_once_per_operator_bytes',
            'activation_operand_read_bytes','activation_operand_write_bytes',
            'kv_new_write_bytes','causal_attention_matrix_flops','rectangular_attention_matrix_flops')


def calculate(preprocessed_height=640,preprocessed_width=640,images_per_request=4,
              encoder_cache_hits=0,text_tokens=400,output_tokens=128,dtype='bf16',kv_dtype='bf16',
              images=None, position_segments=None):
    """Generate G tokens: prefill's last logits produce token one, then G-1 forwards.

    `text_tokens` counts all non-image prompt positions, including chat template,
    image delimiters, tool instructions and computer-use context already tokenized.
    Images are preprocessed static images, and image encoder cache hits never imply
    a language prefix-cache hit. No language prefix reuse is assumed.
    """
    inputs=locals().copy()
    inputs.pop("position_segments")
    positive_int(text_tokens,'text_tokens',allow_zero=True)
    positive_int(output_tokens,'output_tokens')
    if dtype not in multimodal_cache.DTYPE_BYTES or kv_dtype not in multimodal_cache.DTYPE_BYTES:
        raise ValueError('dtype and kv_dtype must be bf16, fp16 or fp32')
    if images is None:
        vision=vision_encoding.calculate(preprocessed_height,preprocessed_width,images_per_request,
                                         encoder_cache_hits,dtype)
        image_positions=vision['summary']['merged_positions_per_image']*images_per_request
    else:
        if (preprocessed_height,preprocessed_width,images_per_request,encoder_cache_hits)!=(640,640,4,0):
            raise ValueError('images cannot be combined with nondefault uniform-image options')
        vision=vision_batch.calculate(images,dtype)
        image_positions=vision['summary']['merged_positions_per_request']
        # Serialize the active input mode without misleading uniform-image defaults.
        for key in ('preprocessed_height','preprocessed_width','images_per_request','encoder_cache_hits'):
            inputs.pop(key)
    config=text_config();width=multimodal_cache.DTYPE_BYTES[dtype];kw=multimodal_cache.DTYPE_BYTES[kv_dtype]
    prompt=text_tokens+image_positions;calls=output_tokens-1
    if prompt+calls>config['max_position_embeddings']:
        raise ValueError('Prefill plus appended decode positions exceed official context capacity')
    branch_count=len(model_config(MODEL)['vision_config']['deepstack_visual_indexes'])
    prefill=language_stage(config,prompt,0,width,kw,image_positions,branch_count)
    first=last=None
    decode={key:0 for key in SUM_FIELDS};decode['special_ops']={}
    if calls:
        first=language_stage(config,1,prompt,width,kw)
        last=language_stage(config,1,prompt+calls-1,width,kw)
        # All decode costs here are affine in history length. Sum endpoints exactly;
        # no O(G) allocation and no approximate representative decode token.
        for field in SUM_FIELDS:
            numerator=calls*(first['summary'][field]+last['summary'][field])
            if numerator%2:raise AssertionError('Non-integral affine decode sum')
            decode[field]=numerator//2
        keys=set(first['summary']['special_ops'])|set(last['summary']['special_ops'])
        decode['special_ops']={key:calls*(first['summary']['special_ops'].get(key,0)
            +last['summary']['special_ops'].get(key,0))//2 for key in sorted(keys)}
    kv_per_position=prefill['summary']['kv_bytes_per_token_per_request']
    vision_matrix=vision['summary']['matrix_flops_per_request']
    language_matrix=prefill['summary']['matrix_flops']+decode['matrix_flops']
    stages=[dict(stage='vision_encode',executions=vision['summary']['encoder_executions_per_request'],
                 matrix_flops=vision_matrix,scope='cached images skip only this stage'),
            dict(stage='language_prefill',executions=1,matrix_flops=prefill['summary']['matrix_flops'],
                 input_positions=prompt,output_logits_rows=1),
            dict(stage='language_decode',executions=calls,matrix_flops=decode['matrix_flops'],
                 input_positions=calls,output_logits_rows=calls)]
    result = dict(schema_version=1,calculation='vl-request',model=MODEL,scenario=inputs,
        sources=vision['sources'],vl_request_stages=stages,vision_encoding=vision,
        vision_image_rows=vision.get('vision_image_rows',[]),
        language_prefill=prefill,language_decode_first=first,language_decode_last=last,
        language_decode_totals=decode,
        summary=dict(visual_positions=image_positions,non_image_prompt_positions=text_tokens,
            prompt_positions=prompt,requested_output_tokens=output_tokens,decode_forward_calls=calls,
            prefill_causal_pairs=prompt*(prompt+1)//2,
            decode_causal_pairs=calls*prompt+calls*(calls+1)//2,
            vision_matrix_flops=vision_matrix,language_matrix_flops=language_matrix,
            total_matrix_flops=vision_matrix+language_matrix,
            language_scalar_flops=prefill['summary']['scalar_flops']+decode['scalar_flops'],
            vision_scalar_counts=vision['summary']['scalar_counts_per_request'],
            deepstack_language_layer_indices=list(range(branch_count)),
            deepstack_prefill_add_elements=branch_count*image_positions*config['hidden_size'],
            language_parameters=prefill['summary']['parameters'],
            language_weight_bytes=prefill['summary']['weight_resident_bytes'],
            vision_weight_bytes=vision['summary']['vision_parameter_bytes_declared_dtype'],
            complete_encoder_bytes_per_request=vision['summary']['complete_encoder_bytes_per_request'],
            kv_bytes_per_position=kv_per_position,prefill_kv_bytes=prompt*kv_per_position,
            final_kv_positions=prompt+calls,final_kv_bytes=(prompt+calls)*kv_per_position,
            decode_kv_new_write_bytes=calls*kv_per_position,
            decode_kv_unique_payload_reads_bytes=kv_per_position*(calls*prompt+calls*(calls+1)//2),
            output_head_evaluations=output_tokens),
        assumptions=[
            '这是图像VL/ComputerUse请求的阶段账；图像来自预处理后静态尺寸，text_tokens包含真实模板、图像边界、工具说明和其他非图像位置，未执行tokenizer或屏幕截图/动作闭环。不是所有Omni音视频模型的通用执行器。',
            'vision_encoding复用完整视觉矩阵/scalar账且只计miss图；命中EC仍含final/DeepStack并被语言模型处理，不减少prompt位置、语言attention或KV。无语言prefix-cache命中。',
            '视觉每图非因果P²与语言整个prompt因果S(S+1)/2分开。产生图像embedding不等于语言已处理其位置；语言QKV/MLP/attention覆盖图像与文字全部位置，不能再加一次独立图像语言prefill。',
            'DeepStack来自视觉层5/11/17，在语言0/1/2层之后相加；prefill三次clone和视觉行add单列，后续decode没有图像encoder或DeepStack执行。',
            'G个输出token由prefill最后一行logits产生第一个，再运行G−1次单token decode；最后输出token尚未写入KV，最终KV长度为S+G−1。EOS提前结束、采样与logit后处理未计。',
            '语言有效因果矩阵工作与矩形分数物化预算分列，算子语义读写不是HBM实测。decode逐步历史增长用整数等差求和，未用平均长度近似代替。',
            '语言KV保留完整层、GQA共享K/V，不重复乘query heads；kv_dtype只控制元素字节，未计页碎片、量化metadata、TP复制或分配器。权重容量分视觉/语言，不假设两阶段同时常驻同卡。',
            '没有CPU图片解码/resize、网络、排队、特征传输/缓存读取计时、kernel launch或设备预测；矩阵和scalar工作不能直接推成完整请求延迟。M-RoPE位置值与布局构造由外部实际输入确定，当前只计确定形状的表计算。',
        ])

    if position_segments is not None:
        from .vl_position_bridge import attach
        result = attach(result, position_segments)
        result['assumptions'] = [
            statement.replace(
                'M-RoPE位置值与布局构造由外部实际输入确定，当前只计确定形状的表计算。',
                'M-RoPE位置值由position_segments生成；整数与接口工作单列，频率表不重复计算。'
            ) for statement in result['assumptions']
        ]
        prefill['assumptions'][0] = '采用Qwen3-VL真实text config；三轴位置来自position_bridge，模板与tokenizer仍由输入提供。'
    return result
