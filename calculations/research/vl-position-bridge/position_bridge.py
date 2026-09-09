"""One unpadded static-image request; explicit already-tokenized modality runs.
No tokenizer, video, beam search, language prefix cache or image arithmetic rerun.
"""


def integer(x, name, minimum=1):
    if type(x) is not int or x < minimum:
        raise ValueError(name)
    return x


def calculate(segments, output_tokens=1):
    integer(output_tokens, "output_tokens")
    if not segments:
        raise ValueError("nonempty ordered segments required")
    axes = [[], [], []]
    cursor = 0
    steps = []
    image_shapes = []
    previous = None
    for segment in segments:
        kind = segment["kind"]
        if kind not in ("text", "image") or kind == previous:
            raise ValueError(
                "segments must be maximal modality runs; delimit images with text/control tokens"
            )
        previous = kind
        if kind == "text":
            n = integer(segment["tokens"], "tokens")
            values = list(range(cursor, cursor + n))
            for axis in axes:
                axis.extend(values)
            steps.append(
                dict(
                    name="text_arange_expand_add",
                    integer_additions=3 * n,
                    materialized_output_bytes=3 * n * 8,
                    arange_output_bytes=n * 8,
                )
            )
            cursor += n
        else:
            height = integer(segment["preprocessed_height"], "height")
            width = integer(segment["preprocessed_width"], "width")
            if height % 32 or width % 32:
                raise ValueError(
                    "fixed patch16/spatial_merge2 requires dimensions divisible by32"
                )
            h, w = height // 32, width // 32
            n = h * w
            for y in range(h):
                for x in range(w):
                    axes[0].append(cursor)
                    axes[1].append(cursor + y)
                    axes[2].append(cursor + x)
            steps.append(
                dict(
                    name="image_arange_meshgrid_stack_offset",
                    integer_additions=h + w + n,
                    integer_multiplications=1,
                    materialized_output_bytes=3 * n * 8,
                    arange_output_bytes=(1 + h + w) * 8,
                    grid_offset_output_bytes=(1 + h + w) * 8,
                    temporal_inplace_read_write_bytes=2 * n * 8,
                    note="meshgrid/reshape are views; stack materializes; scalar grid/control operations excluded",
                )
            )
            image_shapes.append(dict(height=height, width=width, positions=n))
            cursor += max(h, w)
    p = len(axes[0])
    maximum = max(map(max, axes))
    delta = maximum + 1 - p
    calls = output_tokens - 1
    decode = [p + i + delta for i in range(calls)]
    steps.extend(
        [
            dict(name="position_ids_zero_init", materialized_output_bytes=3 * p * 8),
            dict(
                name="segment_cat",
                operand_read_bytes=3 * p * 8,
                materialized_output_bytes=3 * p * 8,
            ),
            dict(
                name="position_ids_assign",
                operand_read_bytes=3 * p * 8,
                materialized_output_bytes=3 * p * 8,
            ),
            dict(
                name="position_max_and_delta",
                reduction_input_elements=3 * p,
                logical_reduction_comparisons=3 * p - 1,
                integer_additions=1,
                integer_subtractions=1,
                materialized_output_bytes=8,
                note="logical comparisons, not a backend reduction instruction count",
            ),
            dict(
                name="direct_model_decode_position_add",
                integer_additions=3 * calls,
                materialized_output_bytes=3 * calls * 8,
                note="explicit no-mask direct-model path; generation wrapper preparation separate",
            ),
        ]
    )
    if image_shapes:
        steps.append(
            dict(
                name="direct_model_decode_arange",
                executions=calls,
                materialized_output_bytes=8 * calls,
                note="One int64 arange element per decode call; internal arange algorithm unspecified.",
            )
        )
        steps.append(
            dict(
                name="direct_model_decode_delta_repeat_interleave",
                executions=calls,
                operand_read_bytes=8 * calls,
                materialized_output_bytes=8 * calls,
                note="Batch1 repeat_interleave(1) materializes the saved int64 delta before broadcast addition.",
            )
        )
        source_route = "fresh_get_rope_index_then_cached_delta_direct_model"
    else:
        # No media grids: direct multimodal wrapper returns None for positions.
        # The language model builds arange(T)+past and expands views; it does
        # not execute get_rope_index or cache a multimodal delta for this request.
        steps = [
            dict(
                name="language_model_default_arange_add",
                executions=1 + calls,
                arange_output_bytes=8 * (p + calls),
                integer_additions=p + calls,
                materialized_output_bytes=8 * (p + calls),
                note="arange then +past_seen_tokens; view/expand to four planes does not materialize. No multimodal delta cached.",
            )
        ]
        source_route = "direct_model_none_then_language_default_positions"
    return dict(
        calculation="qwen3-vl-static-position-bridge",
        positions=axes,
        summary=dict(
            prompt_positions=p,
            image_positions=sum(i["positions"] for i in image_shapes),
            next_rotary_position=maximum + 1,
            rope_delta=delta,
            decode_rotary_positions=decode,
            final_kv_positions=p + calls,
            position_ids_bytes=3 * p * 8,
            rope_delta_bytes=8 if image_shapes else 0,
            rope_delta_cached=bool(image_shapes),
        ),
        images=image_shapes,
        source_steps=steps,
        source_route=source_route,
        boundaries=[
            "Already-tokenized maximal modality runs; image controls belong in text runs.",
            "No image encoder or language forward work is added here; existing vl_request owns it.",
            "Position compression never compresses language attention or KV positions.",
            "Cache hits do not change this result. Feature reuse still requires this request-specific position bridge.",
            "Source .tolist()/Python grouping and device synchronization latency uncalibrated.",
            "Logical interfaces are not additive HBM traffic or peak liveness. Arange implementation unspecified.",
            "Generation wrapper four-plane concatenation and superclass position setup not included; direct model path selected.",
        ],
    )
