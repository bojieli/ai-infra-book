# C13 Dense local-shard quantized placement candidate

This independent addition reuses public `dense_placement.calculate` without editing it. It supports only the three pinned Dense models: Qwen3-8B, Qwen3-32B and DeepSeek-R1-Distill-Llama-70B. It does not complete all of original C13.

## API and compatibility

`calculate(model='qwen3-8b',tp=8,pp=1,dp=1,length=8192,capacity_bytes=24*10**9,workspace_bytes=2*2**30,group_size=128,scale_bytes=2)` returns all three weight storage formats, every physical rank, per-DP-replica common-cohort limits, global request sum, source records and unchanged BF16 reference summary. `markdown(result)` is a dedicated full-rank renderer; it does not assume generic report schema.

The base call uses `batch_per_replica=1,history=length-1,tokens=1`. Thus retained length includes the final token and base KV is the exact one-request coefficient. To reproduce the old default history8192+token1 case, use length8193. Regression tests compare the complete base summary and every BF16 weight/KV/residency field for all three models; existing BF16 code and outputs are unchanged.

Public-ready files are under public/src/infra_calc/topics and public/tests. Public tests use portable `parents[1]/src` bootstrap. `book.append.json` contains54 flat scenarios under `dense_quantized_placement`, directly replayable after removing id. `scenario-summary.json` retains all per-rank budgets; results/ has nine full tensor ledgers for three models and three organizations at24GB/8K. `run_scenarios.py` reconstructs all of them. `example.md` shows the dedicated report.

## Exact storage boundary

Local matrix shape, layer copies, PP endpoints and Q/KV head ownership come directly from the established BF16 adapter. Teaching8/4bit formats quantize local2D projections only; vocabulary embedding/head and all1D norms retain BF16. Every local row packs independently, ceil(K*bits/8) payload bytes and ceil(K/group_size) scale records. The incomplete final group still has a full scale; no zero point or codebook is introduced. Scale width is explicit. This is not a released quantized checkpoint, runtime format support, or quality claim.

KV remains BF16 for all three weight formats. TP16 replicates eight KV heads twice, with duplicated K/V projection weights as in the base adapter. PP preserves unequal layer counts and first/last weights. DP is independent replicas with independent state: find minimum request capacity across TP/PP ranks within each replica, then sum across DP replicas. No aggregate-free-memory substitution is used.

Default workspace is2GiB per rank. Reported request counts are conditional on this reserve; activation, collective, dequantization, allocator, graph pools and batch-dependent workspace are not calculated. Actual runtime peak is null. Arithmetic/communication fields in `bf16_reference_summary` are explicitly reference quantities; storage quantization alone does not imply reduced arithmetic or traffic.

## Representative TP8 results

All values below assume eight cards, no DP, and2GiB workspace per card. Each entry is BF16 / teaching8bit / teaching4bit maximum common-cohort requests.

| Model | per-card GB | 8K | 32K |
|---|---:|---|---|
| Qwen3-8B |24|131 /136 /139|32 /34 /34|
| Qwen3-8B |48|290 /295 /298|72 /73 /74|
| Qwen3-8B |80|502 /507 /510|125 /126 /127|
| Qwen3-32B |24|50 /65 /72|12 /16 /18|
| Qwen3-32B |48|140 /154 /161|35 /38 /40|
| Qwen3-32B |80|259 /273 /281|64 /68 /70|
| Llama70 |24|12 /37 /50|3 /9 /12|
| Llama70 |48|84 /109 /121|21 /27 /30|
| Llama70 |80|179 /204 /217|44 /51 /54|

TP2×PP4 and TP1×PP8 are also retained in the full54-case grid. Their capacities should not be interpreted as performance comparisons: pipeline bubbles, latency and actual workspace behavior are outside this calculation.

## Validation

Eight tests pass. Independent fixed-dimension seven-projection formulas cover all three models and three organizations; BF16 compatibility is exact. Real tail groups are tested with group1000: Qwen8B down-projection local shape4096×1536 needs two scales per row, while quantizing global K12288 and dividing13 groups by8 is wrong. TP16/DP2 tests independently check duplicated heads and physical storage/global request scaling. PP8 checks Qwen8B5/5/5/5/4/4/4/4 layers and worst-rank capacity threshold +/-1byte. Unquantized exceptions, length scaling, report coverage and replay/invalid inputs are checked.

```sh
PYTHONPATH=calculations/src python -m unittest discover -s calculations/research/dense-quantized-placement -p 'test_*.py'
PYTHONPATH=calculations/src python calculations/research/dense-quantized-placement/run_scenarios.py
```

Independent review is in research/dense-quantized-placement-independent. No shared files were edited. Source dependencies and public candidate SHA values are bound in input-bindings.json and public-bindings.json.
