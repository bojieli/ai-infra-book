# Public delivery candidate

Copy only after independent review:

- vl_position_bridge.py → src/infra_calc/topics/vl_position_bridge.py
- test_vl_position_bridge.py → tests/test_vl_position_bridge.py
- vl-position-bridge.lock.json → configs/vl-position-bridge.lock.json

The lock reuses the existing official modeling_qwen3_vl.py input; no weights or source revision changes. Public calculate verifies both locked implementation bytes and public model config patch/merge geometry. Sources contain public model provenance and the implementation lock.

Proposed optional vl_request.calculate argument: position_segments=None. Preserve legacy behavior when absent. When present, first run the existing request calculation unchanged, then return vl_position_bridge.attach(result, position_segments). The attach helper verifies ordered image dimensions, prompt/image/final-KV position counts; it returns a new top-level result without mutating the old result. Input `images` cache_hit values remain owned by the encoder.

The attached position_bridge/source_steps table is separate integer and semantic interface work. Existing mrope_table already counts frequency/sin/cos work, so it must not be counted again. Neither old summary matrix fields nor language stage totals change. position_bridge_stages contains prefill/decode index construction ownership; it does not impose a serial latency edge on vision encoding, because coordinates can be prepared as soon as processed grids are known.

For prose: legacy assumptions about externally provided mRoPE values should be conditional when position_segments is supplied. Source generation-wrapper four-plane preparation is still excluded; direct-model position construction is the selected finite path. All CPU preprocessing and actual hardware timing remain outside this patch.

Four proposed scenarios in scenarios.json use existing image-budget-compatible dimensions. Their request kwargs feed vl_request.calculate; their position_segments feed attach. No shared CLI/reproduce/scenario file has been edited.

Validation without public installation: PYTHONDONTWRITEBYTECODE=1 python3 calculations/research/vl-position-bridge/verify_public.py. Eight tests passed, including cache-hit invariance and no old-summary mutation, rejection of same-token-count but transposed image geometry, and text count mismatch. Small geometry tests explicitly test index math; full-request tests obey the existing processor pixel budget.

This is a candidate pending the separately assigned independent review. Any findings should be applied to the public candidate and original finite module consistently before merge.

Independent-review corrections applied: cached-delta direct decode now includes arange output and batch1 delta.repeat_interleave(1) materialization in addition to the three-axis add. Pure-text fresh direct-model execution follows the language model default arange+past path, with no get_rope_index work or saved delta; its mathematically equivalent delta0 is explicitly marked uncached and zero resident bytes. Nine public-candidate tests now pass, including both regressions.

Final integration correction: uniform requests retain images=None, now handled with scenario.get("images") is not None. Default four640 uniform request regression passes; ten tests total. Tests discover the enclosing calculations/src directory for portable public unittest execution.
