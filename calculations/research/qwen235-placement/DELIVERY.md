# C13 235B eight-rank conditional capacity candidate

Independent candidate only; shared code/config/CLI/reproduce/outline are untouched. The original C13 remains open beyond this declared TP/EP/PP storage organization. Read CONTRACT.md for the exact execution and ownership assumptions before comparing capacities.

Inputs: `calculate(tp=2,ep=4,pp=1,length=8192,capacity_bytes=80*10**9,workspace_bytes=2*2**30,group_size=128,scale_bytes=2)`. Exactly eight ranks; output has one row for every rank and local tensor template, local axis intervals, layer/expert/head ownership, local payload/scales for BF16 and teaching8/4bit, BF16 KV and worst-rank common-cohort limits. All three formats are returned. `scenario` is directly replayable.

The locked official checkpoint index has 36,945 tensor names. Full expansion of the config-derived weight inventory matches this key set exactly; 235,093,634,560 parameters at BF16 matches index `metadata.total_size=470187269120`. Index keys and aggregate bytes do not independently establish per-tensor header shapes; this limitation is explicit in results. Fixed sources are attached by public provenance. No weight download or header claim was added.

Default TP2 EP4 PP1 physical BF16 weight bytes are 518,571,352,064 (64,821,419,008 per rank), exceeding unique checkpoint weight bytes due to replicated attention/router/norm/vocabulary. Per-rank 8K BF16 KV is 788,529,152 bytes. Grouped8bit and4bit physical weight bytes total 268,632,252,416 and141,679,058,944. These totals derive from local shards, not division of the global byte count. Common requests are limited by every rank; unused memory elsewhere cannot cover a failing rank.

The scenario grid retains four organizations × three device budgets (24/48/80 decimal GB) × two lengths (8192/32768), with all three formats in every result. `scenario-summary.json` contains all 24 scenarios and per-rank budgets; four complete tensor ledgers at80GB/8K are under results/. `run_scenarios.py` reconstructs them. The rank budget reserves2GiB workspace by default; it does not prove that real dispatch, dequantization, activations, collectives, allocator or graph pools fit in that reserve. No communication or runtime performance claim is made.

| Organization | per-card GB | 8K cohort BF16 /8bit /4bit | 32K cohort BF16 /8bit /4bit |
|---|---:|---|---|
| TP2 EP4 PP1 |24|0 /0 /5|0 /0 /1|
| TP2 EP4 PP1 |48|0 /15 /35|0 /3 /8|
| TP2 EP4 PP1 |80|16 /56 /76|4 /14 /19|
| TP4 EP2 PP1 |24|0 /0 /14|0 /0 /3|
| TP4 EP2 PP1 |48|0 /37 /75|0 /9 /18|
| TP4 EP2 PP1 |80|43 /118 /156|10 /29 /39|
| TP2 EP2 PP2 |24|0 /0 /14|0 /0 /3|
| TP2 EP2 PP2 |48|0 /37 /75|0 /9 /18|
| TP2 EP2 PP2 |80|43 /118 /156|10 /29 /39|
| TP1 EP1 PP8 |24|0 /0 /25|0 /0 /6|
| TP1 EP1 PP8 |48|0 /70 /145|0 /17 /36|
| TP1 EP1 PP8 |80|83 /229 /304|20 /57 /76|

Zero requests retain a separate `all_weights_workspace_fit` flag: a failed weight placement is distinct from fitting weights but having insufficient remaining KV capacity. PP8 retains12/12/12/12/12/12/11/11 layer asymmetry and endpoint weights, rather than distributing94 layers fractionally. TP8 is a dedicated regression: four GQA KV heads are each replicated twice with matching Q-head ranges.

Seven tests pass using independent fixed-dimension formulas for four organizations, physical replication conservation, TP8 GQA mapping, localK/group1000 metadata tails, per-rank ±1-byte capacity thresholds, complete expert partition coverage, unequal pipeline splits and replay/invalid inputs. Run:

```sh
PYTHONPATH=calculations/src python -m unittest discover -s calculations/research/qwen235-placement -p 'test_*.py'
PYTHONPATH=calculations/src python calculations/research/qwen235-placement/run_scenarios.py
```

Independent review passed in research/qwen235-placement-independent: all36945 names independently enumerated, 96rank×3format checks across12 topology/group cases, physical replication conservation, TP8KV mapping/localK192 tail groups and PP8 worst-rank +/-1byte. Candidate source/tests are frozen and public-ready copies are in public/src/infra_calc/topics and public/tests. Integration should use a dedicated placement/capacity output (not single-device `capacity_scan` totals), preserve the full rank table, and label requests as conditional on workspace and organization. No nominal235e9 or active22e9 substitutes occur.
