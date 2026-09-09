# Architecture shape companion candidate

The normally imported module reads four existing frozen results through PROJECT. calculate() returns six panels and exact source hashes; render(directory) produces SVG/PNG/PDF/data.json. No original model files or weights are downloaded. Integration should copy to src/infra_calc/architecture_shape_plot.py, add a plot CLI and a manifest verifier following capacity_plot's exact input/artifact set validation, then regenerate and bind the public figures. Keep math functions unchanged; source/renderer binding is an integration addition.

The first three panels are Qwen8 baseline/deeper_same_width/shallower_wider; last three are Qwen235 baseline/coarse64/fine256-k16. Diagram scales differ by column and are symbolic. Orange experts are exactly first synthetic route IDs, not an observation. Full parameter sums were independently reconstructed from all attention projections, norms, vocabulary, FFN and router, while visible matrices show only FFN/expert weights. Both columns retain untrained variants and parameter deltas.

Use with the existing Figure2-7 capacity staircase to satisfy both requested parts; do not claim quality, allocator peaks, utilization or hardware speed. Candidate mathematical verification and visual render are recorded in ../verification.json and ../CONTRACT.md; independent review is pending.
