"""Text-encoder and untiled, single-frame VAE steps for audited image pipelines.

Convolution dense-kernel work and nonpadding work are distinct. Tensor-lifetime
figures are named necessary live sets, never a framework/allocator peak estimate.
"""
from ..sources import read_source
import json


def text_stage(model, branch, tokens, batch, element_bytes):
    config = json.loads(read_source(f'configs/models/{model}/text_encoder/config.json'))
    qwen = model == 'qwen-image-2512'
    tied_embeddings = config.get('tie_word_embeddings', False)
    config = config.get('text_config', config)
    length = tokens + 34 if qwen else tokens
    if qwen and tokens > 1024 or length > config['max_position_embeddings']:
        raise ValueError('Text encoder sequence exceeds the audited tokenizer/context limit')
    hidden, ffn, layers, vocab = (config[k] for k in ('hidden_size', 'intermediate_size', 'num_hidden_layers', 'vocab_size'))
    heads, kv_heads = config['num_attention_heads'], config['num_key_value_heads']
    head_dim = config.get('head_dim', hidden // heads)
    qdim, kvdim = heads * head_dim, kv_heads * head_dim
    matrices = []

    def linear(name, k, n, repeats=1):
        matrices.append(dict(branch=branch, name=name, lhs_shape=[batch, length, k],
                             parameter_framework_shape=[n, k], repeats=repeats,
                             matrix_flops=2 * batch * length * k * n * repeats,
                             weight_elements=k * n * repeats,
                             logical_input_bytes=batch * length * k * element_bytes * repeats,
                             logical_weight_bytes=k * n * element_bytes * repeats,
                             logical_output_bytes=batch * length * n * element_bytes * repeats))

    for name, k, n in [('q', hidden, qdim), ('k', hidden, kvdim), ('v', hidden, kvdim),
                       ('o', qdim, hidden), ('gate', hidden, ffn), ('up', hidden, ffn), ('down', ffn, hidden)]:
        linear(name, k, n, layers)
    # Both complete LM wrappers produce all-position logits, despite the caller using hidden states.
    linear('unused_full_vocabulary_head', hidden, vocab)
    edges = length * (length + 1) // 2
    attention = 4 * batch * heads * edges * head_dim * layers
    attention_dense = 4 * batch * heads * length**2 * head_dim * layers
    hidden_bytes = (layers + 1) * batch * length * hidden * element_bytes
    logits_bytes = batch * length * vocab * element_bytes
    kv_bytes = (2 * layers * batch * length * kvdim * element_bytes) if qwen and config['use_cache'] else 0
    nonmatrix = [
        dict(stage='text_' + branch, operation='rmsnorm', vectors=batch * length * (2 * layers + 1), vector_width=hidden),
        dict(stage='text_' + branch, operation='rope_apply', elements=batch * length * (qdim + kvdim) * layers),
        dict(stage='text_' + branch, operation='silu', elements=batch * length * ffn * layers),
        dict(stage='text_' + branch, operation='swiglu_multiply', elements=batch * length * ffn * layers),
        dict(stage='text_' + branch, operation='residual_add', elements=2 * batch * length * hidden * layers),
        dict(stage='text_' + branch, operation='causal_softmax', rows=batch * heads * length * layers,
             valid_elements=batch * heads * edges * layers,
             exp_evaluations=batch * heads * edges * layers,
             max_comparisons=batch * heads * (edges - length) * layers,
             denominator_additions=batch * heads * (edges - length) * layers),
    ]
    if qwen:
        nonmatrix.append(dict(stage='text_' + branch, operation='qkv_bias_add', elements=batch * length * (qdim + 2 * kvdim) * layers))
    else:
        nonmatrix.append(dict(stage='text_' + branch, operation='qk_rmsnorm',
                              vectors=batch * length * (heads + kv_heads) * layers, vector_width=head_dim))
    matrix_work = sum(row['matrix_flops'] for row in matrices)
    return dict(branch=branch, dit_text_tokens=tokens, encoder_tokens=length, prefix_positions_dropped=34 if qwen else 0,
                encoder_layers=layers, feature_layers=[layers] if qwen else [9, 18, 27],
                full_layer_execution=True, computed_logits_despite_unused=True,
                linear_matrix_flops=matrix_work, causal_attention_matrix_flops=attention,
                dense_square_attention_matrix_flops=attention_dense,
                matrix_flops=matrix_work + attention,
                dense_square_matrix_flops=matrix_work + attention_dense,
                all_returned_hidden_bytes=hidden_bytes, unused_full_logits_bytes=logits_bytes,
                temporary_returned_kv_bytes=kv_bytes,
                necessary_return_tensor_live_bytes=hidden_bytes + logits_bytes + kv_bytes,
                embedding_output_bytes=batch * tokens * hidden * (1 if qwen else 3) * element_bytes,
                embedding_lookup_output_bytes=batch * length * hidden * element_bytes,
                matrix_and_embedding_weight_elements_excluding_norm_bias=sum(row['weight_elements'] for row in matrices)
                    + (0 if tied_embeddings else vocab * hidden),
                matrices=matrices, nonmatrix=nonmatrix)


def vae_stage(model, height, width, batch, element_bytes):
    config = json.loads(read_source(f'configs/models/{model}/vae/config.json'))
    qwen = model == 'qwen-image-2512'
    if qwen:
        channels = [config['base_dim'] * m for m in config['dim_mult'][::-1]]
        latent_channels, residuals = config['z_dim'], config['num_res_blocks'] + 1
    else:
        if (config['up_block_types'] != ['UpDecoderBlock2D'] * 4 or not config['mid_block_add_attention']
                or not config['use_post_quant_conv']):
            raise ValueError('VAE decoder path outside the audited four-level configuration')
        channels = config['block_out_channels'][::-1]
        latent_channels, residuals = config['latent_channels'], config['layers_per_block'] + 1
    h, w = height // 8, width // 8
    convolutions, nonmatrix = [], []

    def conv(name, ci, co, kernel=3, temporal=None, cache=False, linear=False):
        kt = (3 if qwen else 1) if temporal is None else temporal
        kernel_volume = kt * kernel * kernel
        conv3d = qwen and not (name.startswith('mid.attention.') or name.endswith('.spatial_conv'))
        output_elements = batch * co * h * w
        # Static-frame temporal padding contributes one nonzero temporal tap.
        valid_h = h if kernel == 1 else 3 * h - 2
        valid_w = w if kernel == 1 else 3 * w - 2
        if kernel not in (1, 3):
            raise ValueError('Only the audited stride-one 1/3 kernels are supported')
        convolutions.append(dict(name=name, kind='linear_as_spatial_1x1' if linear else 'convolution',
                                 input_shape=[batch, ci, 1, h, w] if conv3d else [batch, ci, h, w],
                                 output_shape=[batch, co, 1, h, w] if conv3d else [batch, co, h, w],
                                 kernel_shape=[kt, kernel, kernel],
                                 weight_elements=ci * co * kernel_volume, bias_elements=co,
                                 dense_kernel_flops=2 * batch * h * w * ci * co * kernel_volume,
                                 nonpadding_flops=2 * batch * valid_h * valid_w * ci * co,
                                 input_tensor_bytes=batch * ci * h * w * element_bytes,
                                 output_tensor_bytes=output_elements * element_bytes,
                                 weight_bytes=ci * co * kernel_volume * element_bytes,
                                 causal_feature_cache_clone_bytes=batch * ci * h * w * element_bytes if cache else 0))
        nonmatrix.append(dict(stage='vae', operation='bias_add', location=name, elements=output_elements))

    def norm_activation(name, channels_here):
        elements = batch * channels_here * h * w
        nonmatrix.append(dict(stage='vae', operation='channel_l2_normalize_and_learned_scale' if qwen else 'groupnorm',
                              location=name, elements=elements,
                              normalization_vectors=batch * h * w if qwen else batch * config['norm_num_groups'],
                              vector_width=channels_here if qwen else channels_here * h * w // config['norm_num_groups']))
        nonmatrix.append(dict(stage='vae', operation='silu', location=name, elements=elements))

    def residual(name, ci, co):
        if ci != co:
            conv(name + '.shortcut', ci, co, kernel=1, temporal=1)
        norm_activation(name + '.norm1', ci)
        conv(name + '.conv1', ci, co, cache=qwen)
        norm_activation(name + '.norm2', co)
        conv(name + '.conv2', co, co, cache=qwen)
        nonmatrix.append(dict(stage='vae', operation='residual_add', location=name, elements=batch * co * h * w))

    conv('post_quant', latent_channels, latent_channels, kernel=1, temporal=1)
    current = channels[0]
    conv('decoder.input', latent_channels, current, cache=qwen)
    residual('mid.residual0', current, current)
    spatial = h * w
    # The midblock always contains one unmasked, single-head spatial attention.
    nonmatrix.append(dict(stage='vae', operation='attention_norm', elements=batch * current * spatial,
                          normalization_vectors=batch * spatial if qwen else batch * config['norm_num_groups']))
    for projection in ('q', 'k', 'v', 'out'):
        conv('mid.attention.' + projection, current, current, kernel=1, temporal=1, linear=not qwen)
    attention_flops = 4 * batch * spatial**2 * current
    nonmatrix.append(dict(stage='vae', operation='spatial_softmax', rows=batch * spatial,
                          valid_elements=batch * spatial**2, exp_evaluations=batch * spatial**2,
                          max_comparisons=batch * spatial * (spatial - 1),
                          denominator_additions=batch * spatial * (spatial - 1)))
    nonmatrix.append(dict(stage='vae', operation='residual_add', location='mid.attention', elements=batch * current * spatial))
    residual('mid.residual1', current, current)
    for level, target in enumerate(channels):
        for block in range(residuals):
            residual(f'up{level}.residual{block}', current, target)
            current = target
        if level != len(channels) - 1:
            old_h, old_w = h, w
            h, w = h * 2, w * 2
            nonmatrix.append(dict(stage='vae', operation='nearest_upsample', location=f'up{level}',
                                  input_elements=batch * current * old_h * old_w,
                                  output_elements=batch * current * h * w,
                                  interpolation_compute_dtype='fp32' if qwen else 'runtime_dtype'))
            target = current // 2 if qwen else current
            conv(f'up{level}.spatial_conv', current, target, temporal=1)
            current = target
    if (h, w) != (height, width):
        raise ValueError('Decoder did not reconstruct target dimensions')
    norm_activation('output.norm', current)
    conv('decoder.output', current, 3, cache=qwen)
    if qwen:
        nonmatrix.append(dict(stage='vae', operation='clamp_minmax', elements=batch * 3 * height * width))
    return dict(convolutions=convolutions, nonmatrix=nonmatrix,
                dense_convolution_flops=sum(row['dense_kernel_flops'] for row in convolutions),
                nonpadding_convolution_flops=sum(row['nonpadding_flops'] for row in convolutions),
                mid_attention_matrix_flops=attention_flops, mid_attention_positions=spatial,
                dense_kernel_and_attention_flops=sum(row['dense_kernel_flops'] for row in convolutions) + attention_flops,
                nonpadding_and_attention_flops=sum(row['nonpadding_flops'] for row in convolutions) + attention_flops,
                convolution_and_projection_weight_elements_excluding_norm=sum(row['weight_elements'] + row['bias_elements'] for row in convolutions),
                retained_first_frame_feature_cache_bytes=sum(row['causal_feature_cache_clone_bytes'] for row in convolutions),
                largest_single_conv_input_output_bytes=max(row['input_tensor_bytes'] + row['output_tensor_bytes'] for row in convolutions),
                temporal_upsample_convolutions_executed=0,
                decoder_frame_count=1, full_runtime_peak_bytes=None)
