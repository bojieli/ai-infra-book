"""Selected FLA KDA chunk source allocations and overlapping live subsets.

This follows safe_gate=True, disable_recompute=False, fixed-length BF16 input.
It does not multiply temporary workspace by the number of sequential layers.
"""
from math import prod
from ..schema import Scenario
from ..sources import model_config, provenance
from . import kda_math


def calculate(batch: int = 1, tokens: int = 8192, chunk_size: int = 64) -> dict:
    Scenario(batch=batch, tokens=tokens)
    if chunk_size not in (32, 64):
        raise ValueError('Selected KDA intra kernel only supports chunk_size 32 or 64')
    c = model_config('kimi-k3')['text_config']['linear_attn_config']
    heads, d, layers = c['num_heads'], c['head_dim'], len(c['kda_layers'])
    chunks = (tokens + chunk_size - 1) // chunk_size
    rows = []

    def tensor(name, shape, dtype, source):
        rows.append(dict(name=name, shape=shape, dtype=dtype,
                         bytes=prod(shape) * (4 if dtype == 'FP32' else 2), source=source))
    tensor('g_cumsum', [batch, tokens, heads, d], 'FP32', 'gate.py:kda_gate_chunk_cumsum')
    tensor('Aqk', [batch, tokens, heads, chunk_size], 'BF16', 'chunk_intra.py:chunk_kda_fwd_intra')
    tensor('Akk', [batch, tokens, heads, chunk_size], 'BF16', 'chunk_intra.py:zero initialized')
    tensor('Akkd', [batch, tokens, heads, 16], 'FP32', 'chunk_intra.py:diagonal solve buffer')
    for name in ('w', 'u', 'kg'):
        tensor(name, [batch, tokens, heads, d], 'BF16', 'wy_fast.py:recompute_w_u_fwd')
    tensor('h_chunks', [batch, chunks, heads, d, d], 'BF16', 'common/chunk_delta_h.py:chunk_gated_delta_rule_fwd_h')
    tensor('final_state', [batch, heads, d, d], 'FP32', 'common/chunk_delta_h.py:output_final_state')
    for name in ('v_new', 'output'):
        tensor(name, [batch, tokens, heads, d], 'BF16', 'common/chunk_delta_h.py' if name == 'v_new' else 'gla/chunk.py:chunk_gla_fwd_o_gk')
    sizes = {row['name']: row['bytes'] for row in rows}
    phases = [
        dict(name='intra_with_wy_outputs', objects=['g_cumsum', 'Aqk', 'Akk', 'Akkd', 'w', 'u', 'kg']),
        dict(name='state_and_output_before_cleanup', objects=['g_cumsum', 'Aqk', 'Akk', 'w', 'u', 'kg', 'h_chunks', 'final_state', 'v_new', 'output']),
    ]
    for phase in phases:
        phase['known_live_tensor_bytes'] = sum(sizes[name] for name in phase['objects'])
    block_work = kda_math.work(tokens, chunk_size, d, d)
    return dict(schema_version=1, calculation='kimi-k3-kda-chunk-buffers', model='kimi-k3', mathematical_block_work=block_work,
                scenario=dict(batch=batch, tokens=tokens, chunk_size=chunk_size, safe_gate=True, disable_recompute=False),
                sources=provenance('kimi-k3'), chunk_tensors=rows, known_live_phases=phases,
                summary=dict(chunks_per_sequence=chunks, last_chunk_valid_tokens=tokens - (chunks - 1) * chunk_size,
                             mathematical_block_matrix_flops=batch * heads * layers * block_work['matrix_flops'],
                             mathematical_block_scalar_flops=batch * heads * layers * block_work['scalar_flops'],
                             allocated_Aqk_bytes=sizes['Aqk'], allocated_Akk_bytes=sizes['Akk'],
                             fp32_diagonal_buffer_bytes=sizes['Akkd'],
                             per_layer_chunk_state_bytes=sizes['h_chunks'],
                             per_layer_final_state_bytes=sizes['final_state'],
                             all_kda_final_states_bytes=layers * sizes['final_state'],
                             known_live_subset_max_bytes=max(phase['known_live_tensor_bytes'] for phase in phases),
                             full_workspace_peak_bytes=None, actual_hbm_traffic_bytes=None),
                assumptions=[
                    'Shapes and lifetimes follow selected FLA source with BF16 q/k/v, FP32 gate cumsum, safe gate, output_final_state=True, no CP/packed sequences or autograd retention.',
                    'Aqk/Akk allocate T×chunk_size columns, not ceil(T/chunk_size)×chunk_size squared. h_chunks uses ceil(T/chunk_size); partial chunks therefore change these buffers differently.',
                    'Akkd remains a local in chunk_kda_fwd_intra during WY output allocation, then dies on function return. qg is None because disable_recompute=False.',
                    'w/u/kg and v_new/h remain referenced in chunk_kda_fwd until after output allocation; cleanup happens afterward. Listed phases are known overlapping subsets, not a complete allocator trace.',
                    'Exclude q/k/v projections, input normalized copies, original gate, conv state, parameters, previous-layer persistent states, compiler scratch and caching allocator. Full peak therefore remains unknown.',
                    'Temporary buffers are per currently executing layer; do not multiply the live subset by 69 sequential layers. Final recurrent states are persistent per layer and are reported separately.',
                    'K3 pinned dependency compatibility is not proven; selected FLA reference uses state_v_first rather than transpose_state_layout. This is the declared source path, not measured K3 deployment memory.',
                ])
