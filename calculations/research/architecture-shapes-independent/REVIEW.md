# Architecture shapes: finite figure audit passed

The four bound public result inputs reproduce data.json exactly; each input SHA matches its live file. All 41 author numerical assertions were replayed in memory without executing their verification-file write. They reconstruct full parameter counts, including attention projections, norms, vocabulary endpoints, FFN/expert matrices and routers. This supplements the preceding independent arithmetic reviews of the two underlying calculators.

The renderer was also executed into this independent directory. Its actual Matplotlib patch objects, dimensions, colours and text were inspected. Dense patch counts are exactly 36,48,24; MoE counts are 128,64,256. Dense width is proportional to H: the two H4096 widths match and H5120 is 1.25 times as wide. MoE width is proportional to F within its column: F3072 is twice F1536 and four times F768. These are symbolic shape encodings, not equal scales across columns or complete memory-area encodings. Every patch has zero stroke width, retaining the intended visible gaps.

Orange patch indices equal the exact first synthetic route record: 8,4,16 selected experts in the three MoE panels. The renderer does not infer real activation frequency, choose additional IDs, or colour all experts. Each MoE panel represents one layer's experts while L=94 is separately labelled; it does not draw all 94 layers.

The original PNG was visually inspected. Six panels, subtitles, FFN weight shapes, parameter totals and signed deltas are readable, with no clipping or text overlap. Thin bars are separated; the fine256 panel's narrow marks remain discernible at supplied image resolution. Two released baselines and four untrained variants are explicitly labelled. The first-route legend says synthetic, and the footer explains that column scales differ and FFN matrices are only a subset of model weights. No equal-quality, speed or utilization inference is presented.

Dense FFN widths remain explicit, so deeper/narrower does not hide its compensating F=8320; the shallower/wider design displays F=13952. Signed total-parameter deviations remain visible. MoE expert parameter conservation does not hide router-induced model-total differences: coarse64 and fine256 show opposite signed total deltas and their router counts.

No blocking figure, label or binding issue was found. The figure is a companion to the separately provided capacity curve, not a complete architecture performance or quality experiment. Public integration and figure-registry wiring are outside this independent review. No author/public file was modified.

Re-run with `PYTHONDONTWRITEBYTECODE=1 python calculations/research/architecture-shapes-independent/check.py`. See verification.json for actual artist counts, widths, orange IDs, labels and the source/PNG hashes; rendered/ contains only independent replay artifacts.
