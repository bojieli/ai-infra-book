"""Fixed image-pipeline setup, positional features and typed conversion requests.

Model construction, cold shape caches and per-forward work have separate scopes.
The standard non-Neuron/non-NPU/non-MPS reference path is selected explicitly;
backend-adjusted frequencies, compiler CSE and device copies are not inferred.
"""


def calculate_setup(result, config, scheduler, qwen_shape_cache_warm=False):
    if not isinstance(qwen_shape_cache_warm, bool):
        raise ValueError('Shape-cache state must be an explicit boolean')
    qwen = result['model']=='qwen-image-2512'
    scenario, summary = result['scenario'], result['summary']
    batch, steps = scenario['batch'], summary['denoising_steps']
    calls, image = summary['transformer_invocations'], summary['image_tokens']
    dtype = scenario['dtype']; width_bytes={'bf16':2,'fp16':2,'fp32':4}[dtype]
    d = config['attention_head_dim']; half = d//2
    operations, data = [], []
    def work(name, count, ordinary=0, special=None, scope='request', dtype='fp32'):
        operations.append(dict(stage='setup',operation=name,scope=scope,invocations=count,
                               ordinary_arithmetic_ops=ordinary*count,comparisons=0,
                               special_calls={k:v*count for k,v in (special or {}).items()},
                               reference_accumulator_dtype=dtype))
    def movement(name, elements, source, target, repeats=1, scope='request', source_bytes=None,target_bytes=None):
        changed = source != target
        data.append(dict(operation=name,scope=scope,invocations=repeats,elements_per_invocation=elements,
                         source_dtype=source,target_dtype=target,
                         conversion_elements=elements*repeats if changed else 0,
                         logical_input_bytes=(elements*source_bytes*repeats if changed else 0) if source_bytes is not None else None,
                         logical_output_bytes=(elements*target_bytes*repeats if changed else 0) if target_bytes is not None else None,
                         actual_device_transfer_bytes=None))
    # get_timestep_embedding: 128 exp frequencies, outer multiply, explicit scale,
    # sin/cos and two concatenations. Constant log/negation are not assumed folded.
    work('timestep_sinusoidal_features',calls,ordinary=2*128+2*batch*128+1,
         special={'log':1,'exp':128,'sin':batch*128,'cos':batch*128})
    work('pipeline_transformer_timestep_rescale',calls,ordinary=batch*(1 if qwen else 2),dtype=dtype)
    movement('pipeline_timestep_to_latent_dtype',batch,'fp32',dtype,steps,source_bytes=4,target_bytes=width_bytes)
    movement('timestep_to_fp32',batch,dtype,'fp32',calls,source_bytes=width_bytes,target_bytes=4)
    movement('timestep_features_to_model_dtype',batch*256,'fp32',dtype,calls,source_bytes=4,target_bytes=width_bytes)
    data.append(dict(operation='timestep_frequency_index_setup',scope='request',invocations=calls,
                     integer_arange_elements_per_invocation=128,integer_denominator_subtractions_per_invocation=1))
    data.append(dict(operation='timestep_sin_cos_concat_and_flip',scope='request',invocations=calls,
                     output_elements_per_invocation=2*batch*256,nonflops_kind='tensor materialization',
                     logical_output_bytes=2*batch*256*4*calls))
    for row in result['image_text_encoder_steps']:
        axes = 3 if qwen else 1
        length = row['encoder_tokens']
        # inv_freq/position outer has K=1; count its actual multiplies, not a padded FMA convention.
        angles = axes*batch*length*64
        work('text_'+row['branch']+'_rope_forward',1,ordinary=angles+4*angles,
             special={'sin':2*angles,'cos':2*angles})
        movement('text_'+row['branch']+'_position_ids_cast',axes*batch*length,'int64','fp32',source_bytes=8,target_bytes=4)
        movement('text_'+row['branch']+'_rope_output_cast',4*angles,'fp32',dtype,source_bytes=4,target_bytes=width_bytes)
    if qwen:
        # __init__ creates positive and negative 4096-position complex64 tables.
        work('qwen_rope_constructor_tables',1,ordinary=4*half+2*4096*half,
             special={'pow':2*half,'polar':2*4096*half},scope='model_initialization')
        data.append(dict(operation='qwen_rope_constructor_tables',scope='model_initialization',invocations=1,
                         integer_arange_elements=2*4096+2*half,integer_negate_subtract_ops=2*4096,
                         persistent_table_bytes=2*4096*half*8,output_dtype='complex64'))
        # Only _compute_video_freqs is cached; forward text slicing and cat run every call.
        misses = 0 if qwen_shape_cache_warm else 1
        h, w = scenario['height']//16, scenario['width']//16
        offset=max(h//2,w//2)
        if max(h,w)>8192 or offset+max(r['text_tokens'] for r in result['image_generation_branches'])>4096:
            raise ValueError('Image/text positions exceed the fixed Qwen RoPE table slices')
        data.append(dict(operation='qwen_cached_image_frequency_build',scope='request',invocations=int(misses>0),
                         output_dtype='complex64',
                         axes_concat_elements=(h*config['axes_dims_rope'][1]//2+w*config['axes_dims_rope'][2]//2)*int(misses>0),
                         full_image_concat_and_clone_elements=2*image*half*int(misses>0),
                         logical_output_bytes=((h*config['axes_dims_rope'][1]//2+w*config['axes_dims_rope'][2]//2)+2*image*half)*8*int(misses>0)))
        data.append(dict(operation='qwen_image_rope_cache_and_forward',scope='request',invocations=calls,
                         cold_unique_keys=misses,cache_hits=calls-misses,text_slice_start=offset,
                         outer_image_concat_output_bytes=calls*image*half*8,
                         tensor_views_are_not_copies=True))
    else:
        # Every transformer call regenerates image and text RoPE separately; no LRU decorator.
        for row in result['image_generation_branches']:
            total=image+row['text_tokens']
            # 8 axis helper calls: 4 image axes and 4 text axes; frequency widths sum 2*D/2.
            work('flux_rope_'+row['branch'],row['forwards'],ordinary=8+6*half+total*half,
                 special={'pow':2*half,'sin':total*half,'cos':total*half},dtype='fp64_standard_reference')
            movement('flux_position_ids_cast',4*total,'int64','fp32',row['forwards'],source_bytes=8,target_bytes=4)
            movement('flux_repeated_cos_sin_cast',2*total*d,'fp64','fp32',row['forwards'],source_bytes=8,target_bytes=4)
            data.append(dict(operation='flux_rope_repeat_and_concat',scope='request',invocations=row['forwards'],
                             repeat_output_elements_per_invocation=2*total*d,
                             axis_concat_output_elements_per_invocation=2*total*d,
                             joint_concat_output_elements_per_invocation=2*total*d,
                             nonflops_kind='repeat_interleave and concatenation'))
        data.append(dict(operation='flux_input_position_ids',scope='request',invocations=1,
                         image_cartesian_product_elements=4*image,image_batch_expand_is_view=True,
                         text_cartesian_product_and_stack_elements=2*batch*scenario['text_tokens']*4,
                         integer_dtype='int64',nonflops_kind='arange/cartesian_prod/stack'))
    # Both selected schedulers use supplied linspace sigmas, exponential dynamic
    # shifting, no stochastic/Karras/beta/exponential resampling, no inversion.
    if (not scheduler['use_dynamic_shifting'] or scheduler['time_shift_type']!='exponential'
            or scheduler['invert_sigmas'] or scheduler['stochastic_sampling']
            or any(scheduler[k] for k in ('use_beta_sigmas','use_exponential_sigmas','use_karras_sigmas'))):
        raise ValueError('Scheduler setup differs from the audited deterministic exponential-shift path')
    work('scheduler_mu',1,ordinary=6 if qwen else (2 if image>4300 else 10),dtype='python_scalar')
    data.append(dict(operation='scheduler_mu_branch_and_index_arithmetic',scope='request',integer_subtractions=1 if qwen else 0,integer_comparisons=0 if qwen else 1))
    work('scheduler_sigma_endpoint',1,ordinary=1,dtype='python_scalar')
    work('scheduler_exponential_shift',1,ordinary=4*steps,special={'exp':2,'pow':steps})
    if scheduler['shift_terminal'] is not None:
        work('scheduler_terminal_stretch',1,ordinary=3*steps+2)
    work('scheduler_timestep_scale',1,ordinary=steps)
    data.append(dict(operation='scheduler_linspace',scope='request',invocations=1,output_elements=steps,
                     output_dtype='numpy_fp64',ordinary_arithmetic_ops=None,
                     nonflops_kind='numpy implementation-dependent construction'))
    movement('scheduler_sigmas_fp64_to_fp32',steps,'fp64','fp32',source_bytes=8,target_bytes=4)
    data.append(dict(operation='scheduler_append_terminal_zero',scope='request',invocations=1,
                     output_elements=steps+1,logical_output_bytes=(steps+1)*4,
                     nonflops_kind='concat/fill; not step evaluation'))
    # randn implementation may differ by device/generator; count samples, never
    # invent a Box-Muller instruction count or entropy byte traffic.
    data.append(dict(operation='initial_noise',scope='request',invocations=1,
                     normal_samples=summary['raw_latent_elements'],output_dtype=dtype,
                     logical_output_bytes=summary['latent_bytes'],rng_algorithm=None))
    movement('euler_sample_upcast',summary['raw_latent_elements'],dtype,'fp32',steps,source_bytes=width_bytes,target_bytes=4)
    movement('euler_result_downcast',summary['raw_latent_elements'],'fp32',dtype,steps,source_bytes=4,target_bytes=width_bytes)
    return dict(operations=operations,data_operations=data,
                remaining=['backend-specific frequency dtype/cache/export behavior','constructor text-RoPE initialization helper',
                           'NumPy linspace internals','actual to(device) placement and aliasing','complete norm/activation casts and workspaces',
                           'random generator implementation','tokenizer/string processing','image postprocessing and codec'])
