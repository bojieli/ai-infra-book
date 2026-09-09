"""Declared nonmatrix reference arithmetic and a boundary-buffer event graph.

These are explicitly defined algorithms/allocations, not a profiler report or a
claim about PyTorch kernel instruction selection, aliasing, or allocator peaks.
"""
from fractions import Fraction


def reference_operation(stage, operation, elements=0, vectors=0, width=0, affine=False, rows=0):
    n, v, d = elements, vectors, width
    ordinary, comparisons, special = 0, 0, {}
    if operation == 'rmsnorm':
        ordinary = v * (3*d + 1 + (d if affine else 0)); special = {'rsqrt': v}
    elif operation in ('layernorm', 'groupnorm'):
        ordinary = v * (5*d + 1 + (2*d if affine else 0)); special = {'rsqrt': v}
    elif operation == 'l2_normalize_scale':
        ordinary = v * (6*d - 1); special = {'sqrt': v}; comparisons = v
    elif operation == 'silu':
        ordinary = 4*n; special = {'exp': n}
    elif operation == 'gelu_tanh':
        ordinary = 8*n; special = {'tanh': n}
    elif operation == 'softmax':
        ordinary = 4*n - rows; comparisons = n - rows; special = {'exp': n}
    elif operation == 'rope_apply':
        ordinary = 3*n
    elif operation in ('add', 'multiply', 'divide'):
        ordinary = n
    elif operation == 'clip':
        comparisons = 2*n
    elif operation == 'nearest_copy':
        pass
    else:
        raise ValueError('Unknown declared arithmetic operation: ' + operation)
    return dict(stage=stage, operation=operation, elements=n or v*d, vectors=v, vector_width=d,
                ordinary_arithmetic_ops=ordinary, comparisons=comparisons, special_calls=special,
                reference_accumulator_dtype='fp32' if operation in ('rmsnorm','layernorm','groupnorm','l2_normalize_scale','softmax') else 'declared_tensor_dtype')


def operation_ledger(result, config):
    """Count explicit reference operations; setup-frequency generation stays separate."""
    scenario, summary = result['scenario'], result['summary']
    qwen = result['model'] == 'qwen-image-2512'
    batch, dim = scenario['batch'], summary['hidden_size']
    head_dim, heads = config['attention_head_dim'], config['num_attention_heads']
    steps, double, single = summary['denoising_steps'], summary['dual_stream_blocks'], summary['single_stream_blocks']
    image_tokens = summary['image_tokens']
    ledger = []
    def add(stage, op, **kw):
        ledger.append(reference_operation(stage, op, **kw))
    for item in result['image_stage_nonmatrix']:
        stage, op = item['stage'], item['operation']
        n = item.get('elements', 0)
        if op in ('rmsnorm','qk_rmsnorm'):
            add(stage,'rmsnorm',vectors=item['vectors'],width=item['vector_width'],affine=True)
        elif op in ('causal_softmax','spatial_softmax'):
            add(stage,'softmax',elements=item['valid_elements'],rows=item['rows'])
        elif op in ('silu','rope_apply'):
            add(stage,op,elements=n)
        elif op in ('residual_add','qkv_bias_add','bias_add'):
            add(stage,'add',elements=n)
        elif op == 'swiglu_multiply':
            add(stage,'multiply',elements=n)
        elif op in ('channel_l2_normalize_and_learned_scale','groupnorm','attention_norm'):
            vectors = item['normalization_vectors']
            width = item.get('vector_width', n//vectors)
            add(stage,'l2_normalize_scale' if qwen else 'groupnorm',vectors=vectors,width=width,affine=True)
        elif op == 'nearest_upsample':
            add(stage,'nearest_copy',elements=item['output_elements'])
        elif op == 'clamp_minmax':
            add(stage,'clip',elements=n)
        else:
            raise ValueError('Unpriced stage inventory operation: ' + op)
    for branch in result['image_generation_branches']:
        stage = 'dit_' + branch['branch']
        text, total = branch['text_tokens'], branch['joint_tokens']
        norm_sites = 2*double + single
        add(stage,'layernorm',vectors=batch*total*norm_sites*steps,width=dim)
        add(stage,'layernorm',vectors=batch*image_tokens*steps,width=dim)
        add(stage,'rmsnorm',vectors=2*batch*total*heads*(double+single)*steps,width=head_dim,affine=True)
        if qwen:
            add(stage,'rmsnorm',vectors=batch*text*steps,width=config['joint_attention_dim'],affine=True)
        add(stage,'rope_apply',elements=2*batch*total*dim*(double+single)*steps)
        add(stage,'softmax',elements=batch*heads*total**2*(double+single)*steps,
            rows=batch*heads*total*(double+single)*steps)
        # Shift/scale plus gated residual: two operations each per transformed token.
        add(stage,'multiply',elements=batch*dim*(total*norm_sites*2 + image_tokens)*steps)
        add(stage,'add',elements=batch*dim*(total*norm_sites*2 + image_tokens)*steps)
        # The scalar 1+scale is formed on conditioning vectors, then broadcast over tokens.
        add(stage,'add',elements=batch*dim*(4*double + single + 1)*steps)
        if qwen:
            add(stage,'gelu_tanh',elements=4*batch*total*dim*double*steps)
            add(stage,'silu',elements=batch*dim*(2*double+2)*steps)
            bias_elements = sum(row['logical_output_bytes'] // {'bf16':2,'fp16':2,'fp32':4}[scenario['dtype']]
                                for row in result['image_generation_matrices']
                                if row['branch']==branch['branch'] and row['rhs_kind']=='weight')
            add(stage,'add',elements=bias_elements*steps)
        else:
            inner = int(Fraction(str(config['mlp_ratio']))*dim)
            add(stage,'silu',elements=batch*total*inner*(double+single)*steps + 5*batch*dim*steps)
            add(stage,'multiply',elements=batch*total*inner*(double+single)*steps)
        if scenario['dtype']=='fp16':
            clipped = total*double if qwen else text*double
            add(stage,'clip',elements=batch*dim*(clipped+total*single)*steps)
    elements = summary['raw_latent_elements']
    if summary['true_cfg_enabled']:
        vectors = batch*image_tokens
        ledger.append(dict(stage='cfg',operation='reference_cfg_with_two_vector_norms',elements=elements*steps,
                           vectors=vectors*steps,vector_width=config['in_channels'],
                           ordinary_arithmetic_ops=(8*elements-vectors)*steps,comparisons=0,
                           special_calls={'sqrt':2*vectors*steps},reference_accumulator_dtype='fp32'))
    ledger.append(dict(stage='scheduler',operation='euler_update',elements=elements*steps,vectors=0,vector_width=0,
                       ordinary_arithmetic_ops=(2*elements+1)*steps,comparisons=0,special_calls={},
                       reference_accumulator_dtype='fp32'))
    if summary['vae_decode_calls'] or not qwen:
        add('latent_denormalize','divide' if qwen else 'multiply',elements=elements)
        add('latent_denormalize','add',elements=elements)
        if qwen:
            add('latent_denormalize','divide',elements=summary['raw_latent_channels'])
        else:
            n = config['in_channels']
            ledger.append(dict(stage='latent_denormalize',operation='bn_std',elements=n,vectors=0,vector_width=0,
                               ordinary_arithmetic_ops=n,comparisons=0,special_calls={'sqrt':n},
                               reference_accumulator_dtype='declared_tensor_dtype'))
    return ledger


def boundary_events(result):
    """Explicit eager boundary-buffer schedule, excluding weights and block internals."""
    events, live = [], {}
    peak = 0
    def event(action, name, size=0, phase=''):
        nonlocal peak
        if action == 'allocate':
            if name in live or size < 0:
                raise ValueError('Invalid allocation')
            live[name] = size
        elif action == 'release':
            if name not in live:
                raise ValueError('Release of absent buffer')
            size = live.pop(name)
        else:
            raise ValueError('Unknown memory event')
        total = sum(live.values()); peak = max(peak,total)
        events.append(dict(event=len(events),phase=phase,action=action,object=name,bytes=size,
                           live_bytes_after=total,live_objects=list(live)))
    for row in result['image_text_encoder_steps']:
        name = row['branch']
        event('allocate',name+'_lm_return',row['necessary_return_tensor_live_bytes'],'text_'+name)
        event('allocate',name+'_embedding',row['embedding_output_bytes'],'text_'+name)
        event('release',name+'_lm_return',phase='text_'+name)
    summary = result['summary']; latent = summary['latent_bytes']; elements = summary['raw_latent_elements']
    event('allocate','latent',latent,'noise_init')
    for step in range(summary['denoising_steps']):
        phase = 'step_'+str(step)
        event('allocate','prediction',latent,phase+'_conditional')
        if summary['true_cfg_enabled']:
            event('allocate','negative_prediction',latent,phase+'_negative')
            event('allocate','cfg_output',latent,phase+'_cfg')
            event('release','prediction',phase=phase+'_cfg')
            event('release','negative_prediction',phase=phase+'_cfg')
            event('allocate','prediction',latent,phase+'_cfg_cast')
            event('release','cfg_output',phase=phase+'_cfg_cast')
        # Deliberately explicit FP32-reference schedule; no alias/fusion of casts.
        event('allocate','scheduler_input_fp32',4*elements,phase+'_scheduler')
        event('allocate','scheduler_output_fp32',4*elements,phase+'_scheduler')
        event('allocate','next_latent',latent,phase+'_scheduler_cast')
        event('release','scheduler_input_fp32',phase=phase+'_scheduler')
        event('release','scheduler_output_fp32',phase=phase+'_scheduler')
        event('release','prediction',phase=phase+'_scheduler')
        event('release','latent',phase=phase+'_scheduler')
        # Logical ownership move is free and explicit in the next event.
        event('release','next_latent',phase=phase+'_scheduler_commit')
        event('allocate','latent',latent,phase+'_scheduler_commit')
    for row in result['image_text_encoder_steps']:
        event('release',row['branch']+'_embedding',phase='denoising_complete')
    for row in result['image_vae_convolutions']:
        if row['causal_feature_cache_clone_bytes']:
            event('allocate','vae_cache_'+row['name'],row['causal_feature_cache_clone_bytes'],'vae_'+row['name'])
    if summary['vae_decode_calls']:
        event('allocate','decoded_rgb',summary['decoded_rgb_tensor_bytes'],'vae_output')
        for name in list(live):
            if name.startswith('vae_cache_'):
                event('release',name,phase='vae_clear_cache')
        event('release','latent',phase='vae_complete')
    return dict(events=events,peak_bytes=peak,final_live_bytes=sum(live.values()),final_live_objects=list(live))


def matrix_service_lower_bound(result, service):
    """Conditional serial direct-algorithm bound; nonmatrix/IO service is missing."""
    if service is None:
        return dict(available=False, declared_serial_matrix_lower_exact_seconds=None,
                    complete_request_seconds=None, reason='No effective matrix service supplied')
    required = {'input_dtype', 'accumulator_dtype', 'sparsity', 'flops_per_second'}
    if not isinstance(service, dict) or set(service) != required:
        raise ValueError('Matrix service requires dtype, FP32 accumulation, dense status and effective rate')
    if (service['input_dtype'] != result['scenario']['dtype'] or service['accumulator_dtype'] != 'fp32'
            or service['sparsity'] != 'dense'):
        raise ValueError('Effective service does not match the declared dense input/FP32-accumulator path')
    value = service['flops_per_second']
    if isinstance(value,bool) or not isinstance(value,(int,str)):
        raise ValueError('Use an exact positive integer or fraction rate')
    rate = Fraction(value)
    if rate <= 0:
        raise ValueError('Effective service rate must be positive')
    phases = []
    for row in result['image_text_encoder_steps']:
        phases.append(dict(stage='text_'+row['branch'],matrix_flops=row['matrix_flops'],repetitions=1))
    for row in result['image_generation_branches']:
        phases.append(dict(stage='dit_'+row['branch'],matrix_flops=row['one_forward_matrix_flops'],repetitions=row['forwards']))
    if result['summary']['vae_decode_calls']:
        phases.append(dict(stage='vae',matrix_flops=result['summary']['vae_nonpadding_and_attention_flops'],repetitions=1))
    total = Fraction()
    for row in phases:
        duration = Fraction(row['matrix_flops'] * row['repetitions']) / rate
        row['aggregate_matrix_lower_exact_seconds'] = str(duration)
        total += duration
    return dict(available=True, matched_service=service, phases=phases,
                declared_serial_matrix_lower_exact_seconds=str(total),
                matrix_only_batch_requests_per_second_upper_exact=str(1 / total),
                matrix_only_images_per_second_upper_exact=str(result['scenario']['batch'] / total),
                complete_request_seconds=None,
                reason='Same effective matrix service assumed for all direct-GEMM/convolution stages; excludes all other service and queueing')
