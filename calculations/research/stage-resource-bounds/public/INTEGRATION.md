# C22 stage resource bounds integration candidate

Shared directories are unchanged. Copy the topic and portable test into their usual public locations, add a dedicated CLI command `stage-resource-bounds` calling `calculate(**scenario)`, dispatch its custom `markdown(result)`, and add the flat book scenarios under a separate reproduction group. No generic Scenario precision conversion should override the explicitly declared BF16 Qwen interfaces or mixed V4 mapping.

The main output distinctions must survive rendering: official peak admission versus assumed rates; known-resource max versus complete-accounted max; serial stage sum versus pooled global max; conditional interface demand versus actual HBM; necessary capacity versus full runtime feasibility. All full-request runtime fields remain unknown because the existing operator accounts exclude some work and this candidate does not infer it from peaks.

The default official H100 row preserves unknown special-function rates. Apple GPU matrix peaks and Huawei mismatched precision/accumulator disclosures remain unavailable. A separate Qwen baseline supplies explicitly hypothetical named-special rates of 1e10 units/s, then independently doubles BF16 matrix, FP32 vector, interface bandwidth or exp throughput. These perturbations change supply, never model work. The 25 scenarios include both models, B=1/8, prefill128/512, decode8K/32K, and representative Apple/Huawei profiles.

V4 stage interface bytes stay unknown by default. Optional explicit per-stage bytes define a caller's conditional interface contract; they do not change V4's incomplete model or runtime-storage status. Routed FP4 weights execute FP8 dot products in the pinned code. Keep the original source peak supporting-evidence fields when discussing Hopper FP8 nominal/internal throughput.

The result uses full-layer serial barriers, not an invented fine-grained backend schedule. A later compiler-specific DAG could refine this bound. Do not mark every C22 heterogeneous/runtime extension complete merely because this finite stage comparison is executable.
