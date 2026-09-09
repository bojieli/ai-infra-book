"""K3 official checkpoint bytes and independent config-to-tensor shape audit.

A shape discrepancy is evidence, not an invitation to edit the official config.
Header consistency and agreement with the model definition are separate results.
"""
import ast
import json
import re
from collections import Counter
from math import prod
from ..sources import model_config, read_source


def expected_unpacked_shapes(c: dict) -> dict:
    """Enumerate non-expert text tensors from the pinned model definition."""
    h, v, layers = c['hidden_size'], c['vocab_size'], c['num_hidden_layers']
    linear = c['linear_attn_config']
    d, heads = linear['head_dim'], linear['num_heads']
    j = d * heads
    shapes = {'language_model.model.embed_tokens.weight': [v, h],
              'language_model.lm_head.weight': [v, h],
              'language_model.model.norm.weight': [h],
              'language_model.model.output_attn_res_norm.weight': [h],
              'language_model.model.output_attn_res_proj.weight': [1, h]}
    for layer in range(layers):
        prefix = f'language_model.model.layers.{layer}.'
        local = {name + '.weight': [h] for name in ('input_layernorm', 'post_attention_layernorm',
                                                   'mlp_res_norm', 'self_attention_res_norm')}
        local.update({name + '.weight': [1, h] for name in ('mlp_res_proj', 'self_attention_res_proj')})
        if layer < c['first_k_dense_replace']:
            f = c['intermediate_size']
            local.update({'mlp.gate_proj.weight': [f, h], 'mlp.up_proj.weight': [f, h], 'mlp.down_proj.weight': [h, f]})
        else:
            r, f = c['routed_expert_hidden_size'], c['moe_intermediate_size'] * c['num_shared_experts']
            local.update({'block_sparse_moe.gate.weight': [c['num_experts'], h],
                          'block_sparse_moe.gate.e_score_correction_bias': [c['num_experts']],
                          'block_sparse_moe.routed_expert_down_proj.weight': [r, h],
                          'block_sparse_moe.routed_expert_up_proj.weight': [h, r],
                          'block_sparse_moe.routed_expert_norm.weight': [r],
                          'block_sparse_moe.shared_experts.gate_proj.weight': [f, h],
                          'block_sparse_moe.shared_experts.up_proj.weight': [f, h],
                          'block_sparse_moe.shared_experts.down_proj.weight': [h, f]})
        if layer + 1 in linear['kda_layers']:
            attention = {name + '.weight': [j, h] for name in ('q_proj', 'k_proj', 'v_proj', 'g_proj')}
            attention.update({'f_a_proj.weight': [d, h], 'f_b_proj.weight': [j, d],
                              'b_proj.weight': [heads, h], 'o_proj.weight': [h, j],
                              'A_log': [heads], 'dt_bias': [j], 'o_norm.weight': [d]})
            attention.update({name + '.weight': [j, 1, linear['short_conv_kernel_size']]
                              for name in ('q_conv1d', 'k_conv1d', 'v_conv1d')})
        else:
            q, r, n = c['q_lora_rank'], c['kv_lora_rank'], c['num_attention_heads']
            dn, extra, dv = c['qk_nope_head_dim'], c['qk_rope_head_dim'], c['v_head_dim']
            attention = {'q_a_proj.weight': [q, h], 'q_a_layernorm.weight': [q],
                         'q_b_proj.weight': [n * (dn + extra), q],
                         'kv_a_proj_with_mqa.weight': [r + extra, h], 'kv_a_layernorm.weight': [r],
                         'kv_b_proj.weight': [n * (dn + dv), r],
                         'g_proj.weight': [n * dv, h], 'o_proj.weight': [h, n * dv]}
        local.update({'self_attn.' + name: shape for name, shape in attention.items()})
        shapes.update({prefix + name: shape for name, shape in local.items()})
    return shapes


def runtime_compatibility(c, mismatches):
    """Report source contracts; never invent a checkpoint conversion."""
    paths=['sources/kimi-k3/modeling_kimi_linear.py',
           'sources/flash-linear-attention/fla/ops/kda/gate.py',
           'sources/flash-linear-attention/fla/ops/kda/chunk.py',
           'sources/flash-linear-attention/fla/ops/kda/fused_recurrent.py']
    source=[read_source(path).decode() for path in paths]
    # Pin the relevant call contracts as well as the files' global checksums.
    for name,body in zip(('chunk_kda','fused_recurrent_kda'),source[2:]):
        fn=next(n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name==name)
        if 'state_v_first' not in [a.arg for a in fn.args.args] or "kwargs.pop('transpose_state_layout')" not in body:
            raise ValueError('Changed KDA state-layout compatibility contract')
    if 'A_log.view(H, 1)' not in source[1] or 'self.num_heads, dtype=torch.float32' not in source[0]:
        raise ValueError('Changed KDA A_log contract')
    heads=c['linear_attn_config']['num_heads'];dim=c['linear_attn_config']['head_dim']
    return dict(
        checkpoint_execution_verified=False,
        unmodified_checkpoint_matches_declared_parameters=not mismatches,
        config_heads=heads,head_dim=dim,projected_channels=heads*dim,
        a_log_expected_elements=heads,
        affected_layers=[int(row['tensor'].split('.')[3]) for row in mismatches if row['tensor'].endswith('.A_log')],
        runtime_paths=dict(prefill='chunk_kda; also used for one token without cache',
                           decode='fused_recurrent_kda iff cache exists and query length is one',
                           decay='lower_bound * sigmoid(exp(A_log[head]) * (g[head,channel] + dt_bias[head,channel]))',
                           state_layout='Source passes transpose_state_layout=True; both pinned FLA functions explicitly translate it to state_v_first=True.'),
        direct_load_supported_by_shapes=not mismatches,
        reference_gate_shape_supported=not mismatches,
        fused_forward_observation='Head-index loads can address the first H entries of a larger A_log buffer. This does not establish a legal checkpoint loader, intended padding, or correctness of dropping the tail; no payload values were downloaded.',
        unsupported=['Direct unmodified checkpoint loading into the declared 96-element parameters while mismatches remain',
                     'Treating the 128-element vectors as 128 heads: all Q/K/V, beta, dt_bias and state geometry remain 96-head',
                     'Silently slicing, reshaping, reinitializing or broadcasting A_log without an official conversion contract',
                     'Claiming fused forward compatibility establishes backward compatibility: reference view(H,1) and gradient view_as require matching shapes',
                     'Inferring actual installed FLA/runtime/checkpoint numerical correctness from a source-only audit'],
        evidence_files=paths,
        resolution='Official checkpoint/config/loader reconciliation or a documented conversion with numerical evidence is required. Logical work calculations remain config-based.')


def calculate() -> dict:
    model = 'kimi-k3'
    c = model_config(model)['text_config']
    quant = c['quantization_config']['config_groups']['group_0']
    if quant['format'] != 'mxfp4-pack-quantized' or quant['weights']['num_bits'] != 4 or quant['weights']['group_size'] != 32:
        raise ValueError('K3 checkpoint adapter requires pinned MXFP4 group-32 format')
    index = json.loads(read_source(f'sources/{model}/model.safetensors.index.json'))
    expected = expected_unpacked_shapes(c)
    expert_pattern = re.compile(r'language_model\.model\.layers\.(\d+)\.block_sparse_moe\.experts\.(\d+)\.(w[123])\.(weight_packed|weight_scale)$')
    seen, expected_seen = set(), set()
    groups, dtype_counts, logical = Counter(), Counter(), Counter()
    mismatches, expert_tensors = [], 0
    for shard in sorted(set(index['weight_map'].values())):
        header = json.loads(read_source(f'sources/{model}/headers/{shard}.json'))
        offsets = []
        for name, tensor in header.items():
            if name == '__metadata__':
                continue
            if name in seen or index['weight_map'].get(name) != shard:
                raise ValueError(f'Index/shard/duplicate mismatch: {name}')
            seen.add(name)
            dtype, shape = tensor['dtype'], tensor['shape']
            start, end = tensor['data_offsets']
            count = prod(shape)
            if dtype not in {'U8': 1, 'F32': 4, 'BF16': 2} or end - start != count * {'U8': 1, 'F32': 4, 'BF16': 2}[dtype]:
                raise ValueError(f'Dtype/shape/byte mismatch: {name}')
            offsets.append((start, end))
            owner = {'language_model': 'text', 'vision_tower': 'vision', 'mm_projector': 'projector'}.get(name.split('.')[0])
            if owner is None:
                raise ValueError(f'Unknown checkpoint owner: {name}')
            kind = 'quant_scales' if name.endswith('.weight_scale') else 'parameters'
            groups[f'{owner}_{kind}_bytes'] += end - start
            groups[f'{owner}_total_bytes'] += end - start
            groups[f'{owner}_{dtype}_bytes'] += end - start
            dtype_counts[dtype] += 1
            match = expert_pattern.fullmatch(name)
            if match:
                layer, expert, matrix, suffix = match.groups()
                if not (c['first_k_dense_replace'] <= int(layer) < c['num_hidden_layers'] and 0 <= int(expert) < c['num_experts']):
                    raise ValueError(f'Expert coordinate outside config: {name}')
                r, f = c['routed_expert_hidden_size'], c['moe_intermediate_size']
                out, inp = (r, f) if matrix == 'w2' else (f, r)
                required = [out, inp // (2 if suffix == 'weight_packed' else 32)]
                if dtype != 'U8' or shape != required:
                    raise ValueError(f'Packed expert shape/dtype mismatch: {name}')
                expert_tensors += 1
            elif owner == 'text':
                if name not in expected:
                    raise ValueError(f'Unenumerated text tensor: {name}')
                expected_seen.add(name)
                if shape != expected[name]:
                    mismatches.append(dict(tensor=name, config_shape=expected[name], checkpoint_shape=shape,
                                           parameter_delta=count - prod(expected[name])))
            if kind == 'parameters':
                if dtype == 'U8' and not match:
                    raise ValueError(f'Unclassified packed tensor: {name}')
                logical[owner] += count * (2 if dtype == 'U8' else 1)
        cursor = 0
        for start, end in sorted(offsets):
            if start != cursor:
                raise ValueError(f'Noncontiguous or overlapping offsets: {shard}')
            cursor = end
    if seen != set(index['weight_map']) or expected_seen != set(expected):
        raise ValueError('Incomplete index or text shape enumeration coverage')
    wanted_experts = (c['num_hidden_layers'] - c['first_k_dense_replace']) * c['num_experts'] * 3 * 2
    if expert_tensors != wanted_experts:
        raise ValueError('Incomplete packed expert/scale coverage')
    total = sum(groups[f'{owner}_total_bytes'] for owner in ('text', 'vision', 'projector'))
    if total != index['metadata']['total_size']:
        raise ValueError('Header bytes differ from official index total_size')
    return dict(verified_tensors=len(seen), verified_shards=len(set(index['weight_map'].values())),
                checkpoint_tensor_payload_bytes=total, byte_groups=dict(groups),
                tensor_count_by_storage_dtype=dict(dtype_counts), logical_parameters_by_component=dict(logical),
                verified_expert_packed_and_scale_tensors=expert_tensors,
                config_shape_match=not mismatches, config_shape_mismatches=mismatches,
                runtime_compatibility=runtime_compatibility(c,mismatches),
                text_parameter_delta_from_config=sum(row['parameter_delta'] for row in mismatches),
                scope='All official index keys and header payload offsets/shapes/dtypes audited; payload values not downloaded. Text, vision and projector bytes are separate. Config agreement is an independent flag, not implied by header consistency. Actual runtime conversions, kernel precision and resident allocations remain unknown.')
