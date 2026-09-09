"""Independently encode a list of static images, then concatenate their features."""
from . import vision_encoding


def calculate(images, dtype='bf16'):
    """Each item supplies post-processor height/width and a validated cache hit.

    Image identities/cache validity are caller evidence, not inferred from equal
    dimensions. Summed tensor interfaces describe separate image executions;
    neither batching/fusion savings nor a physical HBM schedule is assumed.
    """
    if not isinstance(images, list) or not images:
        raise ValueError('images must be a nonempty list')
    results = []
    for index, spec in enumerate(images):
        if not isinstance(spec, dict) or set(spec) - {'height', 'width', 'cache_hit'}:
            raise ValueError('Each image accepts only height, width and cache_hit')
        if 'height' not in spec or 'width' not in spec:
            raise ValueError('Each image requires preprocessed height and width')
        hit = spec.get('cache_hit', False)
        if not isinstance(hit, bool):
            raise ValueError('cache_hit must be a boolean for this specific image')
        result = vision_encoding.calculate(spec['height'], spec['width'], 1, int(hit), dtype)
        results.append(dict(image_index=index, cache_hit=hit, encoding=result))
    summaries = [row['encoding']['summary'] for row in results]
    invariant_fields = ('complete_vision_learned_parameters', 'vision_parameter_bytes_declared_dtype')
    for field in invariant_fields:
        if len({summary[field] for summary in summaries}) != 1:
            raise AssertionError('Images in one request must use the same vision weights')
    scalar_counts = {}
    for summary in summaries:
        for key, value in summary['scalar_counts_per_request'].items():
            scalar_counts[key] = scalar_counts.get(key, 0) + value
    rows = []
    for image, summary in zip(results, summaries):
        misses = summary['encoder_executions_per_request']
        rows.append(dict(image_index=image['image_index'], cache_hit=image['cache_hit'],
            grid_thw=summary['preprocessed_grid_thw'], patches=summary['patches_per_image'],
            merged_positions=summary['merged_positions_per_image'],
            matrix_flops=summary['matrix_flops_per_request'],
            complete_encoder_bytes=summary['complete_encoder_bytes_per_request'],
            semantic_read_bytes=misses*summary['semantic_read_bytes_per_image'],
            semantic_write_bytes=misses*summary['semantic_write_bytes_per_image']))
    return dict(schema_version=1, calculation='vision-batch', model=results[0]['encoding']['model'],
        scenario=dict(images=images, dtype=dtype), sources=results[0]['encoding']['sources'],
        vision_image_rows=rows, per_image_encodings=results,
        summary=dict(image_count=len(images),
            encoder_executions_per_request=sum(s['encoder_executions_per_request'] for s in summaries),
            encoder_cache_hits=sum(int(r['cache_hit']) for r in results),
            merged_positions_per_request=sum(s['merged_positions_per_image'] for s in summaries),
            matrix_flops_per_request=sum(s['matrix_flops_per_request'] for s in summaries),
            scalar_counts_per_request=scalar_counts,
            complete_encoder_bytes_per_request=sum(s['complete_encoder_bytes_per_request'] for s in summaries),
            semantic_read_bytes_per_request=sum(r['semantic_read_bytes'] for r in rows),
            semantic_write_bytes_per_request=sum(r['semantic_write_bytes'] for r in rows),
            **{field:summaries[0][field] for field in invariant_fields}),
        assumptions=[
            'Each image is separately encoded with the pinned Qwen3-VL implementation. Post-preprocessing dimensions are required; no pixel decoding or resizing is performed.',
            'Attention work sums each missed image P_i squared; images do not attend across image boundaries in the vision encoder. Language attention later spans all merged positions.',
            'A cache hit skips that image encoder but retains all its final and DeepStack features and language positions. Cache identity and validity require caller evidence.',
            'Vision weights are shared once in capacity accounting, not multiplied by image count. Interface reads describe separate executions and are not physical HBM traffic or an optimized batched implementation.',
        ])
