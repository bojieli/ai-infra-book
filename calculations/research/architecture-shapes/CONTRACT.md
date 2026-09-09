# Figure 2-7: architecture-shape companion

Six panels bind one existing Dense architecture result and three expert-granularity results. Dense panels show baseline36x4096, deeper48x4096 and shallower24x5120, including exact compensating FFN widths, full parameter totals and deltas. MoE panels show E128/F1536/K8, E64/F3072/K4 and E256/F768/K16, with expert weight shapes, full parameter totals and router changes.

Each Dense bar is one layer; width proportional to H within the Dense column. Each MoE bar is one expert of one layer; width proportional to F within the MoE column, not an area model across columns. Orange indices are exactly the first synthetic route record, not a measured activation. Matrix labels are stored gate/up/down shapes only, not all model operators. No equality of model quality, hardware utilization, or time is inferred. The raw first route, exact per-layer/all-layer parameter arithmetic and all input hashes are preserved in data.json.

The initial raster merged thin layer bars due to default strokes; linewidth0 and visible gaps were applied and the second PNG visually inspected. Final PNG/SVG/PDF are generated from the same data. Candidate checker reconstructs full Dense/MoE parameter totals independently from attention projections, norms, FFN, router and vocabulary. Only released baselines represent real configs; other variants are explicitly untrained.

This candidate completes the shape-companion part of Figure2-7 after review/public integration; the separately integrated capacity curve supplies the other part. Public CLI/figure-registry integration is still pending. No shared source, result or outline was modified.
