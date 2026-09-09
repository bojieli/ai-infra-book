# Qwen235 TP8 / EP8 finite independent review

Both new fixed scenarios pass242 assertions, including independent projection-shape/packing formulas, all ranks and precisions, exact maximum-plus-one capacity boundaries, frozen result equality, result.scenario replay, and four actual CLI JSON/Markdown executions. No public files were changed and no whole-module re-audit was attempted.

The oracle constructs matrices directly from official configuration: Q `[64*128/tp,4096]`, K/V `[local_KV*128,4096]`, O `[4096,64*128/tp]`, and each locally owned expert's two `[1536/tp,4096]` plus one `[4096,1536/tp]`. It separately adds BF16 vocabulary shards, router and norm parameters. Low-bit payload and scales are recomputed per local matrix row using ceil(K*bits/8) and ceil(K/128)*2, independently of the module's tensor storage records.

For both layouts L=94, context8192, head_dim128 and BF16 KV. Per-rank per-request KV is `2(K,V)*94*local_KV_heads*128*8192*2 bytes`.

* TP8/EP1 has one complete KV head per rank: ranges `[0,1)` twice, `[1,2)` twice, `[2,3)` twice, `[3,4)` twice. Each rank's KV is394,264,576 bytes. Logical four-head state is physically replicated twice across eight ranks. Each rank owns a TP shard of all128 experts, not16 whole experts. The declared80 decimal GB and2GiB workspace give BF16/8-bit/4-bit maxima47/120/158 requests.
* TP1/EP8 has all four complete KV heads on every rank:1,577,058,304 bytes per request per rank. Expert ranges are consecutive disjoint16-expert sets and their union is exactly0..127. Attention, vocabulary/router/norm ownership follows the existing EP-replication contract. Maximum equal-length cohort concurrency is3/25/36 for the three formats.

Every rank and format satisfies `weights + workspace + n*KV <= 80e9 < weights + workspace + (n+1)*KV`. All ranks' payload, metadata and totals match the independent formulas. Consequently these are necessary conditional capacity results, not proof of low-bit runtime support, measured workspace sufficiency, throughput or equal quality.

`check.py` ran with `/Users/boj/miniconda3/bin/python`. Full evidence, per-format first-rank totals and both boundary values are retained in `results.json`. CLI was exercised using its actual `--inputs` interface; the two input files are included. The earlier chapter2 audit's S12 fixed-scenario gap is closed by these two results; the separate expert-granularity experiment remains outside this review.
