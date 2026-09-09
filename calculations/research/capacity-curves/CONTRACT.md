# Figure 2-7: capacity staircase candidate

Four models and fixed eight-rank organizations, sourced from twelve frozen 24/48/80 decimal GB results. Dense models use TP8, Qwen235 uses TP2/EP4; no inference that these choices optimize throughput. BF16 KV at8192 retained positions, fixed2GiB workspace/rank, local group128 low-bit storage as declared in the existing ledgers.

For cohort n, exact per-device threshold is max_rank(W_rank+workspace+n*KV_rank). Staircases use these integer thresholds, not linear interpolation or averaged ranks. Each n fits at threshold and fails one byte below; n+1 fails at that threshold. Zero requests explicitly includes weights+workspace not fitting; minimum weight and first-request thresholds are retained in data.json. Other fixed scenarios verify the curve at24/48/80GB. Inputs remain source-hash bound in data; plotting code/figures bound in verification.json. SVG/PNG/PDF render was visually inspected: four legible panels, axes and conditions, no overlap.

This is only the capacity-curve part of Figure2-7. It does not replace the requested architecture diagram or provide task quality, actual allocator peak, dynamic workspace or measured performance. The public-layout module is a candidate; CLI/figure registry and public rendering still need integration after independent review.
