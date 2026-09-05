# OpenTallas

**Open research toward instant, affordable AI inference.**

[Why speed matters](docs/VISION.md) · [Documentation](docs/README.md) ·
[Plain-English overview](docs/OVERVIEW.md) · [Specification](spec/README.md) ·
[Results](results/) · [Contributing](CONTRIBUTING.md)

More than 10,000 tokens per second per user is now a publicly reported silicon
result. [Taalas](https://taalas.com/products/) reports **16,960 tokens/s** <!-- figure: 16,960 src="configs/hardware/technology.json#reference_parts.taalas_hc1.published_tokens_s_per_user.value" name="Taalas HC1 published per-user rate, README" -->
per user for its fabricated HC1 accelerator running Llama 3.1 8B at batch one.
That result changes the conversation: model-specific inference is no longer
only a paper architecture. It is a credible path toward AI systems that respond
at interactive timescales.

OpenTallas asks what it would take to make that architectural direction open,
inspectable, and extensible to larger models and longer contexts. The repository
connects model accounting, architecture simulation, a shared compiler/runtime
ABI, public-reference RTL, and open-PDK circuit experiments in one evidence
chain. It is independent of Taalas and does not claim to reproduce HC1.

![Conceptual OpenTallas model-specific decode architecture](docs/assets/architecture-overview.svg)

## The headline—and the evidence behind it

| Signal | Result | Evidence class |
|---|---:|---|
| Public model-specific silicon reference | **16,960 tokens/s per user** on Taalas HC1 | Fabricated product; first-party Taalas run, publicly documented, not an independent benchmark | <!-- figure: 16,960 src="configs/hardware/technology.json#reference_parts.taalas_hc1.published_tokens_s_per_user.value" name="Taalas HC1 public reference rate, README" -->
| OpenTallas leading-node central point | **12,629.3 tokens/s per user** for DeepSeek-V4-Flash at 200K context and batch one | Deterministic analytical result; not measured silicon | <!-- figure: 12,629.3 src="results/iso-node/leading_node_market/REPORT.md#ROM user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="OpenTallas N4 central rate, README" -->
| Same OpenTallas point versus its conventional-HBM comparator | **7.65×** higher per-user decode rate | Modeled comparison against the fastest feasible allowed B300 cluster at the same active microbatch | <!-- figure: 7.65 src="results/iso-node/leading_node_market/REPORT.md#Same-B ratio" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="OpenTallas N4 central advantage, README" -->
| Modeled partial TCO at that point | **$0.210/M tokens** versus **$0.957/M tokens** | Assumed acquisition, NRE allocation, utilization, electricity, and PUE; not price or a full business case | <!-- figure: 0.210 src="results/iso-node/leading_node_market/analytical.json#comparisons[wafer_architecture=ROM-wafer-N4-class-HBM3e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].wafer_partial_tco_per_million_tokens" name="OpenTallas N4 central partial TCO, README" --> <!-- figure: 0.957 src="results/iso-node/leading_node_market/analytical.json#comparisons[wafer_architecture=ROM-wafer-N4-class-HBM3e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].cheapest_same_batch_gpu_partial_tco_per_million_tokens" name="N4 cheapest same-batch GPU partial TCO, README" -->

The Taalas and OpenTallas rates are **not** an apples-to-apples benchmark. They
use different models, contexts, systems, and evidence classes. The Taalas number
is useful because it is a public proof point from fabricated hardware; the
OpenTallas number is useful because its assumptions and derivation are open to
inspection. Taalas publishes a product page, a [public
chatbot](https://chatjimmy.ai/), and [API documentation](https://api.taalas.com/),
but the benchmark itself was run by Taalas Labs rather than MLPerf or an
independent laboratory. The exact source boundary is recorded in the
[source register](docs/SOURCES.md#the-shipping-mask-rom-part-the-anchor-the-model-is-gated-against).

> **Research status**
>
> OpenTallas is an active hardware research program, not a fabricated product.
> Its headline performance and cost figures are deterministic model outputs.
> Bounded functional executions, RTL campaigns, public-PDK layouts, and extracted
> circuit experiments exist only at their documented scopes. A complete target
> implementation, foundry signoff, packaged system, and OpenTallas silicon do not.
> Current source-locked and retained historical execution horizons are separated
> explicitly in the [execution checklist](docs/UNIFIED_EXECUTION_CHECKLIST.md).
> A cycle result that depends on assumed machine values is correctness evidence,
> not a performance measurement or projection.

## Why 10,000 tokens per second matters

High token rates are not valuable simply because a benchmark number is large.
They change both the economics of inference and the kinds of products that can
be built.

### 1. More useful work from every dollar of infrastructure

When a system produces more useful tokens during each paid second of hardware,
its capital and operating costs are amortized across more output. That does not
make lower cost automatic: utilization, yield, power, lifetime, model quality,
and non-recurring engineering all matter. It does make throughput a powerful
economic lever.

The central OpenTallas scenarios illustrate the lever. “Partial TCO” includes
assumed hardware acquisition, allocated NRE, utilization, electricity, and PUE;
it excludes financing, staffing, networking, facilities capital, maintenance,
spares, downtime, unmodeled yield loss, and margin.

| Central scenario, Flash 200K B1 | OpenTallas ROM | Cheapest feasible same-batch HBM candidate | HBM cost / ROM cost |
|---|---:|---:|---:|
| N7-class / A100-era | **$0.329/M tokens** | **$1.922/M tokens** | **5.85×** | <!-- figure: 0.329 src="results/iso-node/n7_architecture_attribution/analytical.json#comparisons[wafer_architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].wafer_partial_tco_per_million_tokens" name="N7 central ROM partial TCO, README" --> <!-- figure: 1.922 src="results/iso-node/n7_architecture_attribution/analytical.json#comparisons[wafer_architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].cheapest_same_batch_gpu_partial_tco_per_million_tokens" name="N7 cheapest same-batch GPU partial TCO, README" --> <!-- figure: 5.85 src="results/iso-node/n7_architecture_attribution/analytical.json#comparisons[wafer_architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].partial_tco_ratio_vs_cheapest_same_batch_gpu" name="N7 central partial TCO ratio, README" -->
| N4-class / B300-era | **$0.210/M tokens** | **$0.957/M tokens** | **4.57×** | <!-- figure: 0.210 src="results/iso-node/leading_node_market/analytical.json#comparisons[wafer_architecture=ROM-wafer-N4-class-HBM3e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].wafer_partial_tco_per_million_tokens" name="N4 central ROM partial TCO, README" --> <!-- figure: 0.957 src="results/iso-node/leading_node_market/analytical.json#comparisons[wafer_architecture=ROM-wafer-N4-class-HBM3e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].cheapest_same_batch_gpu_partial_tco_per_million_tokens" name="N4 cheapest same-batch GPU partial TCO, README" --> <!-- figure: 4.57 src="results/iso-node/leading_node_market/analytical.json#comparisons[wafer_architecture=ROM-wafer-N4-class-HBM3e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].partial_tco_ratio_vs_cheapest_same_batch_gpu" name="N4 central partial TCO ratio, README" -->

The conservative N4 scenario is slower and more expensive than its comparator.
That counterexample matters: the economic benefit appears only when ROM density,
service rate, communication, and system utilization clear the stated gates.

### 2. Reasoning can move from the background into the interaction loop

Agentic work is often serial: generate a plan, call a tool, inspect the result,
revise the plan, and repeat. Faster decoding shortens every reasoning-heavy turn
in that loop. As a simple illustration, generating 100,000 reasoning tokens at
500 tokens/s takes 200 seconds; at 10,000 tokens/s it takes 10 seconds. Tool,
network, prompt-processing, and environment latency still remain, but the model
no longer has to dominate the schedule.

That shift creates room for:

- **Coding and research agents** that can explore, critique, and revise a
  substantial project in seconds rather than minutes.
- **Computer-use agents** whose observe–reason–act loop can keep pace with a
  changing interface instead of operating as a slow asynchronous job.
- **Robotics replanning** that can reconsider a trajectory while the physical
  situation is still current, provided sensing, safety, control, and deployment
  latency meet the same budget.
- **Real-time voice agents** with less dead air, more natural interruption, and
  enough compute headroom to reason without breaking conversational rhythm.
- **Generative interfaces** that synthesize the next useful view while a person
  is interacting with the current one.
- **Interactive world models.** If model-specific inference generalizes from
  language to video, systems could generate responsive virtual environments
  instead of offline clips. [Oasis](https://oasis-model.github.io/) demonstrated
  the shape of this experience with an interactive AI-generated world at 20
  frames per second. The checked [Oasis/H3 analytical
  study](results/world-model/REPORT.md) finds a conditional ROM opportunity only
  after causal frame-state caching; full-clip video DiTs such as MiniMax-H3 are
  much less favorable. The [recent-model landscape
  audit](results/world-model-landscape/REPORT.md) extends that test to World
  Labs Atlas/RTFM, EVOKE, AlayaWorld, LingBot, WorldPlay, Matrix-Game 3.0, and
  Cosmos 3. OpenTallas still does not implement these models, so this remains
  analytical research rather than a video-system result.

Read [Why instantaneous inference matters](docs/VISION.md) for the fuller product
and systems argument, including the conditions under which throughput does *not*
translate into responsiveness.

## The architecture, in concrete terms

During inference, activations and the KV cache change from token to token, but
the deployed weight values usually do not. General-purpose accelerators still
store those weights in writable HBM because they are designed to load many
different models. At low batch, each generated token can require another large
weight transfer through the same external-memory system.

OpenTallas makes a deliberate trade: encode the immutable weight values in dense
mask ROM near the arithmetic that consumes them. Keep the KV cache, activations,
session state, routing decisions, and every other changing value in SRAM or HBM.
The arithmetic still happens; the architecture removes a recurring long-distance
weight transfer rather than removing computation.

| | Conventional or “stock” HBM architecture | OpenTallas ROM architecture |
|---|---|---|
| Model weights | Writable and reloadable in HBM | Encoded in local mask ROM |
| KV cache and session state | Writable HBM/SRAM | Writable HBM/SRAM; never ROM |
| Decode traffic | Active weights repeatedly cross the memory interface | Local ROM serves weights; external bandwidth focuses on mutable state |
| Flexibility | One system can run many checkpoints | One manufactured image serves a specific model representation |
| Best fit | Changing models, training, fine-tuning, high-batch service | Stable, high-volume, low-batch, weight-dominated inference |
| Main risks | HBM capacity, bandwidth, and cost | Mask/NRE amortization, ROM density and repair, collectives, KV service, power, yield, and model obsolescence |

Here, **stock** does not mean a measured off-the-shelf server run. It means an
allowed conventional GPU or GPU cluster assembled from the published device
characteristics and compatibility rules in the study configuration. The
iso-node performance comparator is the fastest feasible candidate at the same
active microbatch. The cost comparator is the cheapest feasible candidate at
that microbatch, so it may be a different cluster. The area-aware study uses a
separate rule and gives both sides approximately equal silicon area.

The executable stack keeps this architecture choice explicit:

```text
checkpoint + workload
        │
        ▼
canonical model graph ──► backend-neutral IR ──► ABI 3.0 program
                                                    │
                              ┌─────────────────────┴─────────────────────┐
                              ▼                                           ▼
                    HBM/SRAM deployment                         ROM deployment
                              │                                           │
                              └──────── verifier + device + counters ─────┘
                                                    │
                                      functional / cycle / RTL evidence
```

Qwen3-8B and DeepSeek-V4-Flash both use this shared compiler/runtime path. The
analytical studies also use DeepSeek-V4-Pro as a scaling workload; it is not a
third executable ABI target. See the [architecture specification](spec/ARCHITECTURE.md),
[ABI decision](docs/TENSOR_ACCELERATOR_ABI_3_ARCHITECTURE_DECISION.md), and
[wire format](docs/TENSOR_ACCELERATOR_ABI_3_WIRE_FORMAT.md) for the contract.

## Performance comparison

OpenTallas publishes two different comparisons because no single table answers
both architectural and product questions:

1. **Iso-node architecture attribution** asks how local immutable-weight service
   changes low-batch decode at a broadly matched technology generation.
2. **Area-constrained selection** gives both sides approximately the same
   silicon area, allows each to choose its own parallelism, and selects a ROM
   design by a declared per-user-rate-per-area rule.

### Central iso-node results

For DeepSeek-V4-Flash at 200K context and batch one:

| Study | OpenTallas ROM | Fastest feasible same-batch HBM comparator | Per-user advantage | Binding ROM term |
|---|---:|---:|---:|---|
| N7-class ROM/HBM2e vs A100/HBM2e | **8,050.1 tok/s** | **614.4 tok/s** | **13.10×** | layer collectives | <!-- figure: 8,050.1 src="results/iso-node/n7_architecture_attribution/REPORT.md#ROM user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N7 central ROM user rate, README" --> <!-- figure: 614.4 src="results/iso-node/n7_architecture_attribution/REPORT.md#GPU user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N7 central A100 user rate, README" --> <!-- figure: 13.10 src="results/iso-node/n7_architecture_attribution/REPORT.md#Same-B ratio" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N7 central same-batch advantage, README" -->
| N4-class ROM/HBM3e vs B300/HBM3e | **12,629.3 tok/s** | **1,650.7 tok/s** | **7.65×** | layer collectives | <!-- figure: 12,629.3 src="results/iso-node/leading_node_market/REPORT.md#ROM user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N4 central ROM user rate, README" --> <!-- figure: 1,650.7 src="results/iso-node/leading_node_market/REPORT.md#GPU user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N4 central B300 user rate, README" --> <!-- figure: 7.65 src="results/iso-node/leading_node_market/REPORT.md#Same-B ratio" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N4 central same-batch advantage, README" -->

These are per-user decode rates, not aggregate server throughput. They do not
include prompt prefill, sampling, API serving, tool calls, or end-to-end agent
latency.

### Back-of-the-envelope: why ROM can help

Before introducing hardware assumptions, the traffic model counts what one
token must move. For DeepSeek-V4-Flash at 200K context and batch one:

| Active weight read | Mutable KV read | Weight / KV-read ratio |
|---:|---:|---:|
| **11.218 GB** | **317.456 MB** | **35.34×** | <!-- figure: 11.218 src="results/model-traffic/REPORT.md#B1 active weight" table="Raw traffic inputs" where="Model=DeepSeek-V4-Flash-0731;Context=200000" name="Flash active weight traffic at 200K, README" --> <!-- figure: 317.456 src="results/model-traffic/REPORT.md#KV read/user/token" table="Raw traffic inputs" where="Model=DeepSeek-V4-Flash-0731;Context=200000" name="Flash KV read traffic at 200K, README" --> <!-- figure: 35.34 src="results/model-traffic/REPORT.md#B1" table="Weight / KV-read ratio" where="Model=DeepSeek-V4-Flash-0731;Context=200000" name="Flash weight-to-KV traffic ratio at 200K, README" -->

The **35.34× figure is a traffic ratio, not a speedup**. It identifies the term
the architecture is designed to remove from HBM. Once that happens, KV service,
compute, and communication remain.

The central N7 point makes that bottleneck shift visible:

| Component | Time per token |
|---|---:|
| Local ROM weight service | **7.828 µs** | <!-- figure: 7.828 src="results/iso-node/n7_architecture_attribution/analytical.json#points[architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_size=1].component_times_s.rom_full_array_read_C4" scale="1e6" name="N7 ROM weight service, README" -->
| Mutable HBM KV service | **41.979 µs** | <!-- figure: 41.979 src="results/iso-node/n7_architecture_attribution/analytical.json#points[architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_size=1].component_times_s.kv_beachfront_C8" scale="1e6" name="N7 HBM KV service, README" -->
| Tensor compute service | **25.932 µs** | <!-- figure: 25.932 src="results/iso-node/n7_architecture_attribution/analytical.json#points[architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_size=1].component_times_s.compute_C5" scale="1e6" name="N7 compute service, README" -->
| Serialized layer collectives | **69.821 µs** | <!-- figure: 69.821 src="results/iso-node/n7_architecture_attribution/analytical.json#points[architecture=ROM-wafer-N7-HBM2e-central,model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_size=1].component_times_s.collective_floor_C6" scale="1e6" name="N7 collective service, README" -->
| Pipeline efficiency | **0.90** | <!-- figure: 0.90 src="configs/hardware/n7_architecture_attribution.json#wafer_architectures[name=ROM-wafer-N7-HBM2e-central].pipeline_efficiency" name="N7 pipeline efficiency, README" -->

Weight, KV, and compute service can overlap; the collective term is serialized:

```text
token interval = (max(7.828, 41.979, 25.932) + 69.821) / 0.90
               = 124.222 µs

per-user rate  = 1 / 124.222 µs
               = 8,050.1 tokens/s
```

The raw traffic opportunity is 35.34×, but the modeled performance benefit is
13.10× because mutable-state service and communication become the bottleneck.
That is the central architectural result: ROM does not eliminate bottlenecks; it
moves them.

### Backing off the headline: deterministic envelopes

There is no leading-node OpenTallas ROM macro from which to read one measured
answer. Each iso-node study therefore reruns the entire system under conservative,
central, and aggressive assumptions. These are deterministic engineering
envelopes, not statistical confidence intervals.

| Study | Central ROM rate | Conservative–aggressive ROM rate | Conservative–aggressive ROM/HBM advantage |
|---|---:|---:|---:|
| N7 vs A100 | **8,050.1 tok/s** | **1,287.0–23,767.7 tok/s** | **2.09×–38.69×** | <!-- figure: 8,050.1 src="results/iso-node/n7_architecture_attribution/REPORT.md#ROM user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N7 central point in envelope, README" --> <!-- figure: 1,287.0 src="results/iso-node/n7_architecture_attribution/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].rom_per_user_tokens_s_low" name="N7 conservative ROM rate, README" --> <!-- figure: 23,767.7 src="results/iso-node/n7_architecture_attribution/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].rom_per_user_tokens_s_high" name="N7 aggressive ROM rate, README" --> <!-- figure: 2.09 src="results/iso-node/n7_architecture_attribution/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].same_batch_speed_ratio_low" name="N7 conservative advantage, README" --> <!-- figure: 38.69 src="results/iso-node/n7_architecture_attribution/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].same_batch_speed_ratio_high" name="N7 aggressive advantage, README" -->
| N4-class vs B300 | **12,629.3 tok/s** | **1,637.9–42,373.7 tok/s** | **0.99×–25.67×** | <!-- figure: 12,629.3 src="results/iso-node/leading_node_market/REPORT.md#ROM user tok/s" table="Central-envelope" where="Model=DeepSeek-V4-Flash-0731;B/stage=1" name="N4 central point in envelope, README" --> <!-- figure: 1,637.9 src="results/iso-node/leading_node_market/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].rom_per_user_tokens_s_low" name="N4 conservative ROM rate, README" --> <!-- figure: 42,373.7 src="results/iso-node/leading_node_market/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].rom_per_user_tokens_s_high" name="N4 aggressive ROM rate, README" --> <!-- figure: 0.99 src="results/iso-node/leading_node_market/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].same_batch_speed_ratio_low" name="N4 conservative advantage, README" --> <!-- figure: 25.67 src="results/iso-node/leading_node_market/analytical.json#uncertainty_bands[model=DeepSeek-V4-Flash-0731,context_tokens=200000,batch_per_stage=1].same_batch_speed_ratio_high" name="N4 aggressive advantage, README" -->

The N4 conservative point is effectively parity, while its central point clears
10,000 tokens/s. That wide span is intentional. The model varies declared ROM
capacity and service, HBM resources, bandwidth and compute efficiency, MoE
balance, repair, clock, synchronization, and pipeline derates, then reruns the
capacity, service, communication, and thermal gates. It does not apply a
percentage haircut to the central number. See [assumptions](docs/ASSUMPTIONS.md)
and [methodology](docs/METHODOLOGY.md) for the full contract.

### Final area-aware performance benefit

The area-constrained studies prevent a proposed wafer or array from winning
merely because it uses more silicon. They select a non-dominated ROM design by
per-user rate and rate per square millimeter, then compare it with a conventional
HBM deployment at the closest whole-device silicon area. Both sides choose their
own parallelism.

| Technology study | Workload | Selected ROM organization | Per-user rate, ROM / HBM | Per-user advantage |
|---|---|---|---:|---:|
| N6 vs A100 | Qwen3-8B, 8K | 6-die array, SRAM KV | **3,110.4 / 494.8 tok/s** | **6.29×** | <!-- figure: 3,110.4 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=Qwen3-8B].recommended.per_user_tokens_s" name="N6 Qwen ROM user rate, README" --> <!-- figure: 494.8 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=Qwen3-8B].recommended.iso_area_gpu_per_user_tokens_s" name="N6 Qwen HBM user rate, README" --> <!-- figure: 6.29 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=Qwen3-8B].recommended.per_user_speed_ratio" name="N6 Qwen per-user advantage, README" -->
| N6 vs A100 | DeepSeek-V4-Flash, 200K | 1 wafer, HBM KV | **4,707.9 / 721.7 tok/s** | **6.52×** | <!-- figure: 4,707.9 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.per_user_tokens_s" name="N6 Flash ROM user rate, README" --> <!-- figure: 721.7 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.iso_area_gpu_per_user_tokens_s" name="N6 Flash HBM user rate, README" --> <!-- figure: 6.52 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.per_user_speed_ratio" name="N6 Flash per-user advantage, README" -->
| N6 vs A100 | DeepSeek-V4-Pro, 1M | 4 wafers, SRAM KV | **2,375.7 / 357.7 tok/s** | **6.64×** | <!-- figure: 2,375.7 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.per_user_tokens_s" name="N6 Pro ROM user rate, README" --> <!-- figure: 357.7 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.iso_area_gpu_per_user_tokens_s" name="N6 Pro HBM user rate, README" --> <!-- figure: 6.64 src="results/roofline/n6_vs_a100/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.per_user_speed_ratio" name="N6 Pro per-user advantage, README" -->
| N5 vs B200 | Qwen3-8B, 8K | 5-die array, SRAM KV | **4,941.0 / 978.7 tok/s** | **5.05×** | <!-- figure: 4,941.0 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=Qwen3-8B].recommended.per_user_tokens_s" name="N5 Qwen ROM user rate, README" --> <!-- figure: 978.7 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=Qwen3-8B].recommended.iso_area_gpu_per_user_tokens_s" name="N5 Qwen HBM user rate, README" --> <!-- figure: 5.05 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=Qwen3-8B].recommended.per_user_speed_ratio" name="N5 Qwen per-user advantage, README" -->
| N5 vs B200 | DeepSeek-V4-Flash, 200K | 30-die array, SRAM KV | **2,627.4 / 1,465.1 tok/s** | **1.79×** | <!-- figure: 2,627.4 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.per_user_tokens_s" name="N5 Flash ROM user rate, README" --> <!-- figure: 1,465.1 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.iso_area_gpu_per_user_tokens_s" name="N5 Flash HBM user rate, README" --> <!-- figure: 1.79 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Flash-0731].recommended.per_user_speed_ratio" name="N5 Flash per-user advantage, README" -->
| N5 vs B200 | DeepSeek-V4-Pro, 1M | 3 wafers, HBM KV | **2,648.8 / 746.8 tok/s** | **3.55×** | <!-- figure: 2,648.8 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.per_user_tokens_s" name="N5 Pro ROM user rate, README" --> <!-- figure: 746.8 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.iso_area_gpu_per_user_tokens_s" name="N5 Pro HBM user rate, README" --> <!-- figure: 3.55 src="results/roofline/n5_vs_b200/analytical.json#design_selection.models[model=DeepSeek-V4-Pro-0813].recommended.per_user_speed_ratio" name="N5 Pro per-user advantage, README" -->

The outcome is not one universal multiplier: the selected points range from
1.79× to 6.64×. Resident-session capacity also differs, sometimes sharply, so a
per-user latency advantage is not automatically an aggregate serving advantage.
Read the complete [N6/A100](results/roofline/n6_vs_a100/REPORT.md) and
[N5/B200](results/roofline/n5_vs_b200/REPORT.md) reports before quoting a row.

## What is implemented—and what is not

| Evidence layer | Present in the repository | Claim boundary |
|---|---|---|
| Model and architecture analysis | Checked traffic, iso-node, area-constrained, NoC, routing, cost, and sensitivity studies | Deterministic model output; not measured hardware |
| Compiler and runtime | Canonical model ingestion, backend-neutral IR, ABI 3.0 deployments, independent verification, functional and cycle devices | Bounded workloads and declared token-agreement horizons; not unrestricted model correctness |
| Digital implementation | Synthesizable public-reference RTL, formal/static/simulation/fault campaigns, and open-library implementation proxies | Qualified blocks and correlated deployments only; not a complete target chip or wafer |
| Circuit and physical methods | SKY130A and IHP controlled-via ROM slices, extracted simulations, and predictive/open-library routed blocks | Local methodology evidence; not leading-node ROM density, yield, or product signoff |
| Product silicon | **Not present** | No tapeout, fabricated OpenTallas device, package, full-chip P&R, foundry DRC/LVS, or silicon benchmark |

The [evidence ladder](docs/assets/README.md) defines how conceptual diagrams,
simulated results, routed geometry, and extracted circuits may be interpreted.
Functional, cycle, RTL, synthesis, place-and-route, SPICE, published, measured,
and assumed evidence are intentionally not interchangeable. Start with the
[current program report](docs/ABI3_PROGRAM_REPORT.md), [generated
status](docs/PROGRAM_STATUS.md), and [evidence methodology](docs/METHODOLOGY.md)
before extending a claim.

## Start exploring

| If you want to… | Start here |
|---|---|
| Understand why instant inference matters | [Vision and product implications](docs/VISION.md) |
| Learn the architecture without a hardware background | [OpenTallas in plain English](docs/OVERVIEW.md) |
| Navigate the full technical library | [Documentation hub](docs/README.md) |
| Audit the performance comparison | [Methodology](docs/METHODOLOGY.md), [assumptions](docs/ASSUMPTIONS.md), and [sources](docs/SOURCES.md) |
| Inspect the executable program | [ABI 3.0 program report](docs/ABI3_PROGRAM_REPORT.md) and [compiler guide](compiler/README.md) |
| Implement against the contract | [Specification index](spec/README.md), [wire format](docs/TENSOR_ACCELERATOR_ABI_3_WIRE_FORMAT.md), and [operator conventions](docs/TENSOR_ACCELERATOR_ABI_3_OPERATOR_CONVENTIONS.md) |
| Review digital hardware evidence | [RTL inventory](rtl/README.md) and [RTL result reports](results/rtl/) |
| Review ROM circuit evidence | [SPICE guide](spice/README.md) and [physical methodology](docs/ROM_PHYSICAL_METHODOLOGY.md) |
| Track active work | [Unified execution checklist](docs/UNIFIED_EXECUTION_CHECKLIST.md) |

## Quick start

The core Python analyses and tests run on a CPU workstation with Python 3.10 or
newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[test,compiler]"

make model-traffic
make spec-check
make test
```

Rebuild the headline studies and verify every annotated prose figure with:

```bash
make iso-node
make roofline
make check-figures
```

The complete `make verify` flow additionally needs RTL synthesis and simulation
tools. Its `spice` step checks circuit topology and source invariants; the
optional device, physical, and extracted-layout campaigns are separate and
require pinned SKY130A or IHP SG13G2 PDK/tool installations. See
[spice/README.md](spice/README.md). Model profiling reads checkpoint metadata
with range requests and does not download full checkpoints by default.

## Repository map

| Path | Purpose |
|---|---|
| [`src/opentallas/`](src/opentallas/) | Analytical architecture and performance models |
| [`compiler/`](compiler/) | Model ingestion, canonical IR, ABI lowering, and deployment construction |
| [`runtime/`](runtime/) | Independent checks, functional device, cycle model, and reference numerics |
| [`spec/`](spec/) | Governed system, microarchitecture, interface, numeric, RAS, firmware, and verification contracts |
| [`rtl/`](rtl/) | Public-reference SystemVerilog, benches, formal harnesses, and campaigns |
| [`spice/`](spice/) and [`physical/`](physical/) | Circuit and physical-methodology vehicles |
| [`configs/`](configs/) | Explicit model, hardware, benchmark, and PDK inputs |
| [`results/`](results/) | Generated, reviewable evidence artifacts and reports |
| [`docs/`](docs/) | Vision, orientation, methodology, decisions, evidence notes, plans, and status |
| [`tests/`](tests/) | Unit, differential, integration, ABI, runtime, and simulation tests |
| [`tools/`](tools/) | Reproduction, checking, reporting, and campaign entry points |

## Contributing

OpenTallas welcomes work that makes an assumption more explicit, a result more
reproducible, an implementation more complete, or a claim easier to audit. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before changing a specification, generated
report, evidence grade, or headline figure. Add new documents to the
[documentation hub](docs/README.md), and coordinate with current owners before
renaming or moving an active plan or checklist.

The most valuable contribution is often not a larger number. It is a clearer
boundary between what the repository demonstrates, what it models, and what
still has to be measured in silicon.
