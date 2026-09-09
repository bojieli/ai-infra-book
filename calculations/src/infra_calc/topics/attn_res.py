"""K3 block Attention Residuals from _forward_attn_residual/_apply_attn_res.

Saved blocks live across depth within one forward, not across token generation.
At block boundaries attention mixing happens before the new block is appended.
"""
from ..schema import Scenario
from ..sources import model_config, provenance


def calculate(batch: int = 1, tokens: int = 8192) -> dict:
    scenario = Scenario(batch=batch, tokens=tokens)
    c = model_config('kimi-k3')['text_config']
    layers, stride, h, m = c['num_hidden_layers'], c['attn_res_block_size'], c['hidden_size'], scenario.rows
    if stride <= 0:
        raise ValueError('AttnRes block size must be positive')
    calls, boundaries = [], []
    saved = 0

    def apply(layer, branch):
        candidates = saved + 1
        rows = m * candidates
        calls.append(dict(layer=layer, branch=branch, saved_blocks=saved, candidates=candidates,
                          norm_shape=[m, candidates, h], scores_shape=[m, candidates],
                          weighted_sum_shapes=dict(A=[m, 1, candidates], B=[m, candidates, h], Y=[m, 1, h]),
                          matrix_flops=2 * m * candidates * h,
                          scalar_flops=rows * (3 * h + 1) + h + rows * (2 * h - 1) + m * (3 * candidates - 1),
                          rsqrt_ops=rows, exp_ops=rows, max_comparisons=m * (candidates - 1),
                          concatenated_activation_bytes=rows * h * 2,
                          concatenated_fp32_bytes=rows * h * 4,
                          notes='RMS statistic/normalize, once-per-call norm.weight*proj.weight, score dot, FP32 softmax; weighted sum is the matrix row.'))

    for layer in range(layers):
        if saved:
            apply(layer, 'attention')
        if layer % stride == 0:
            saved += 1
            boundaries.append(dict(layer=layer, saved_blocks_after=saved,
                                   block_stack_after_bytes=m * saved * h * 2,
                                   cat_read_bytes=m * saved * h * 2,
                                   cat_write_bytes=m * saved * h * 2))
        apply(layer, 'ffn')
    apply('output', 'output')
    additions = (2 * layers - len(boundaries)) * m * h
    return dict(schema_version=1, calculation='kimi-k3-attention-residuals', model='kimi-k3',
                scenario=dict(batch=batch, tokens=tokens), sources=provenance('kimi-k3'),
                attn_res_calls=calls, block_boundaries=boundaries,
                summary=dict(allocated_norm_and_projection_parameters=(4 * layers + 2) * h,
                             mixing_calls=len(calls), saved_blocks_final=saved,
                             total_candidates_over_calls=sum(row['candidates'] for row in calls),
                             weighted_sum_matrix_flops=sum(row['matrix_flops'] for row in calls),
                             mixing_scalar_flops=sum(row['scalar_flops'] for row in calls),
                             prefix_accumulation_scalar_flops=additions,
                             rsqrt_ops=sum(row['rsqrt_ops'] for row in calls),
                             exp_ops=sum(row['exp_ops'] for row in calls),
                             max_comparisons=sum(row['max_comparisons'] for row in calls),
                             final_saved_block_stack_bytes=m * saved * h * 2,
                             largest_concat_fp32_tensor_bytes=max(row['concatenated_fp32_bytes'] for row in calls),
                             boundary_cat_operand_bytes=sum(row['cat_read_bytes'] + row['cat_write_bytes'] for row in boundaries)),
                assumptions=[
                    '93 layers, block size 12. Layer 0 skips attention mixing but allocates its norm/projection parameters; it appends the embedding block before FFN mixing.',
                    'At layer 12/24/... attention uses the prior saved block count; only afterward is prefix_sum saved and reset. FFN sees the new block plus its current prefix.',
                    'score_weight=norm.weight*proj.weight is computed once per call, not per token or candidate. Score multiplication/reduction is scalar source work; final weighted sum uses FMA=2 matrix accounting.',
                    'Prefix adds: attention adds except at each reset boundary; FFN always adds. No ordinary residual addition is counted again.',
                    'Block residuals are forward-local depth state, reinitialized for every call. They are not additional persistent KV cache across decode steps.',
                    'Tensor sizes and boundary cat operands are separate source objects, not summed simultaneous workspace peaks or measured HBM. Other materializations, compiler fusion and memory lifetime analysis remain separate.',
                    'Excludes external attention/FFN norms, final model norm, sublayer work and vision/MTP.',
                ])
