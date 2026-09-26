# GPU dependent-boundary cost: first-principles analysis and Blackwell measurement

Sep 26, 2026 · @Bojie Li

On a Blackwell GPU, a dependent matrix-vector boundary in a decode megakernel costs about 1.0 µs, even when weights are prefetched across it. Signalling that every SM is done takes 663 ns (about 1,900 cycles at 2.88 GHz); delivering the activation vector to every SM brings the best design to 1.0–1.15 µs. A one-to-one handoff costs 366–371 ns. All of it is L2 latency and contention, not launch overhead, and no alternative design measured here (flag-in-data, per-producer flags, clusters, a Megatron column/row pair) beats the simple counter.

## First principles: what a boundary costs

A dependent-op boundary is the moment op B may start because op A's results are visible to every SM that reads them. At batch-1 decode each op is spread across all SMs, so almost every boundary crosses SMs. Its cost has four parts:

1. **Drain.** The last of A's thread blocks must finish. Between kernels this is the tail effect; inside a megakernel it is the slowest producer.
2. **Signal.** The producer's completion must become visible to consumers. SMs share no memory with each other except L2, so the signal is a store that travels SM → crossbar → L2 slice, ordered after A's data stores by a release (a fence or a `st.release`).
3. **Detection.** A consumer finds out by a load that travels SM → L2 → SM and sees the new value. Polling adds, on average, half a poll period.
4. **Launch (kernel boundaries only).** The hardware work distributor must dispatch B's thread blocks to the SMs, and B's prologue must run. Programmatic Dependent Launch (PDL) and persistent megakernels remove most of this part; they cannot remove parts 2 and 3.

So the floor for any cross-SM dependency is roughly one store to L2 plus one load round trip from L2, about 1.5 L2 round trips. A dependency that gathers from every SM (a split matrix-vector product feeding a norm) needs a gather then a broadcast, about 2 traversals, plus serialisation where all SMs meet. Only dependencies that stay inside one SM (shared memory, `__syncthreads`) or one thread-block cluster (distributed shared memory) avoid L2.

## Measurements

Measured on an NVIDIA RTX PRO 6000 Blackwell Workstation Edition (GB202, sm\_120, 188 SMs, 128 MiB L2), SM clock 2.88 GHz measured in-kernel (`clock64` against `%globaltimer`). Values are the best (uncontended) figure across three to four runs of 2,000–20,000 boundaries each; medians run 10–40% higher because another tenant was using the GPU.

| Boundary mechanism | What it models | Cycles | ns |
| --- | --- | --- | --- |
| `__syncthreads`, one block | dependency inside one SM | 21 | 7 |
| `cluster.sync`, 8-block cluster | dependency inside one cluster (distributed shared memory) | 377 | 131 |
| PDL chain, one block per SM | dependent kernels with programmatic dependent launch | 1,053 | 366 |
| Flag handoff, `st.release`/`ld.acquire` or fence | megakernel one-to-one producer → consumer on another SM | 1,037–1,067 | 360–371 |
| CUDA-graph launch gap, empty kernels | plain kernel boundary (no tail, no prologue) | 1,233 | 428 |
| `grid.sync`, cooperative persistent kernel | all-SM barrier from the CUDA runtime | 1,790 | 622 |
| All-SM counter barrier | megakernel "every SM done → next op" | 1,915–1,971 | 663–684 |
| All-SM barrier, gather tree / cluster-hierarchical | alternative barrier designs | 2,990–3,650 | 1,038–1,270 |

Reference latencies from the same runs: an L2 round trip (single-thread dependent pointer chase in a 256 KiB footprint) is 680–835 cycles (236–290 ns); a fence after a store is 576–881 cycles.

## Methodology check

The first benchmark gave the right headline numbers, but a first-principles review found four flaws in the supporting measurements. All four were fixed in `dep_latency_v2.cu` before the table above was taken.

| Problem found | Why it was wrong | Fix |
| --- | --- | --- |
| SM clock not recorded | a lightly loaded GPU may run below boost, which inflates nanoseconds | clock measured in-kernel; every result also reported in cycles |
| Result copied before the kernel finished | the copy ran on the default stream while the kernel ran on a non-blocking stream, so the host read stale memory (clock came out NaN) | stream synchronised before every read-back |
| L2 pointer chase as slow as DRAM (1,367 vs 1,389 cycles) | a random walk over 32 MiB misses the address-translation cache on most steps, so it measured TLB misses, not L2 | footprint sweep; L2 latency taken from the 256 KiB footprint, inside one page |
| Same-address atomics at 0.05 ns each | the compiler combines a warp's atomics before they reach L2, so it measured warp aggregation | one atomic per thread block |
| Back-to-back fences at 2,300–3,200 cycles | a loop of fences with nothing to order measures fence throughput, not the latency of one fence | one fence after one store, per iteration |

Two design choices were also tested rather than assumed. Replacing the full fence with `st.release`/`ld.acquire` did not shorten the handoff, because both wait for the same L2 acknowledgement. Replacing a flat counter barrier with a gather tree or a cluster hierarchy made the all-SM barrier slower (1,038–1,270 ns), because each adds a traversal.

## Cycle accounting

The measured costs match the L2-latency model within the scatter of the runs, so the measurements are physically consistent.

| Dependency | Model | Predicted cycles | Measured cycles |
| --- | --- | --- | --- |
| One-way cross-SM handoff | store reaches L2 (½ round trip) + consumer's poll sees it (1 round trip) | ½ × 700 + 700 ≈ 1,050 | 1,037–1,067 |
| PDL boundary | the same signal, raised by hardware | ≈ 1,050 | 1,053 |
| All-SM barrier | gather to one L2 line + broadcast back (2 traversals) + arrival serialisation | 2 × 700 + \~500 ≈ 1,900 | 1,915–1,971 |
| Cluster barrier | on-chip SM-to-SM network inside a GPC, no L2 | well under 1 L2 round trip | 377 |
| Intra-SM barrier | shared-memory barrier hardware | tens of cycles | 21 |

This first model matches the totals, but its split into terms was wrong. It treated each dependency as bare L2 traversals of \~700 cycles, a figure from the first runs; the breakdown below measures a round trip of \~380 cycles in the same binary (the L2 hit latency varied 354–870 cycles between processes). The missing cycles are memory fences. The breakdown in "Why synchronisation through L2 is slow" supersedes this table's model column; the measured column stands.

## Delivering the data: all-SM gather designs

The 663 ns counter only signals that every slice is ready. The next matrix-vector product also needs the whole activation vector in every SM, and moving it costs at least 1.0 µs per boundary. At each boundary, each of the 188 SMs writes its slice (about 22 words) and must then hold the whole vector; every element of every step was checked, with zero errors and zero timeouts. Figures are the minimum over 21 trials of 500 boundaries; minima and medians agree within about 1%, and two full runs within 1–2%. The SM clock measured 2.88 GHz.

| Design | How the vector reaches every SM | fp32 vector, 16 KiB (ns) | bf16-width vector, 8 KiB (ns) |
| --- | --- | --- | --- |
| Reading a ready vector, no dependency (floor) | plain loads from L2 | 377–401 | 176–209 |
| Single counter, signal only | no data moved (the earlier 663 ns) | 659 | 659 |
| Single counter + data, one copy | all 188 SMs read the same 128 lines | 1,638 | 1,483 |
| Single counter + data, 8 copies | SM *b* reads copy *b* mod 8 | 1,429 | 1,126 |
| Counter with acquire poll + 8 copies | best bf16 design | 1,233 | **1,004** |
| LL16 flag-in-data + 8 copies | best fp32 design | **1,151** | 1,151 |
| Counter split 8 ways + 8 copies | spreads the arrivals | 1,286 | 1,090 |
| LL8 flag-in-data (tag in every 8-byte store) | NCCL low-latency protocol | 2,105 | 1,569 |
| LL16 / LL128 flag-in-data | wider tagged stores | 2,240 / 1,819 | 2,245 / 2,118 |
| Per-producer flags | a warp polls 188 flags | 2,359–2,646 | 2,200–2,560 |
| Cluster of 8 / 16, then one flag per cluster | hierarchical | 1,933 / 1,692 | 1,843 / 1,593 |
| Cluster of 8, exchange through distributed shared memory | no L2 inside the cluster | 38,083 | 17,115 |

The LL16 and LL128 layouts keep a 24 KiB footprint in the bf16 build, so they do not shrink there. The best all-SM gather that delivers the data is 1,004 ns (bf16) to 1,151 ns (fp32), about 1.5–1.7× the signal alone.

## Under a real weight stream

Prefetching weights hides less of the boundary than expected: each dependent boundary still exposes 0.74–1.06 µs with the best scheduling, and 1.2–2.3 µs with fixed per-SM tiles. The test is a chain of 64 dependent Qwen3-8B 4096×4096 bf16 matrix-vector products per trial, cycling over 16 matrices (512 MiB, 4× the L2), so every weight byte comes from DRAM. With no dependency between them, the chain streams at 20.7–21.0 µs per product (about 1.6 TB/s, matching a plain read kernel's 1.60–1.76 TB/s), so it is bandwidth-bound. Weights stream into a shared-memory ring by TMA (or per-thread `cp.async`), and the next product's weights are prefetched across the boundary. The exposed cost is the chain's time per product minus the stream-only kernel of the same structure.

| Scheduling | Exposed per boundary (µs, median) | Mean wait per SM per boundary (µs) |
| --- | --- | --- |
| Fixed tiles, stream stops at each boundary | 2.85–3.23 | 3.1–3.8 |
| Fixed tiles, next weights prefetched (8-row ring) | 1.22–2.30 | 6.6–7.6 |
| Fixed tiles, next weights prefetched (12-row ring) | 1.79–1.98 | 10.9–11.2 |
| Rows claimed dynamically + LL8 outputs | **0.74–1.06** | 3.4–3.6 |

With fixed tiles the cost comes from stragglers, not from the 1.2 µs gather. Each SM owns 21 or 22 rows and DRAM serves SMs unevenly, so every SM waits on average 6.6–11 µs for the slowest one, and a bigger prefetch ring barely helps. Letting SMs claim rows from a per-product counter as ring slots free up removes the straggler wait and roughly halves the exposed cost. What remains, about one gather per boundary, is the dependency itself: the last rows of product *n* must reach every SM before the first multiply of product *n*+1.

## Why synchronisation through L2 is slow

The all-SM counter costs about five L2 round trips, and two of them are memory fences; queueing of 188 arrivals on one address is a minor term. SMs outside a cluster share nothing but L2. So every dependency is built from L2 round trips of 338–421 cycles (117–146 ns): the SM crossbar and L2 slices are designed for bandwidth, not latency. Decomposition measurements (`breakdown.cu`, 11 trials of 500 steps, 2.879 GHz):

| Component | Measured | What it shows |
| --- | --- | --- |
| L2 load round trip | 338–392 cycles | the unit everything is built from; no near/far split above \~15% across 64 lines |
| Atomic that returns a value | 363–421 cycles | one round trip |
| GPU-scope fence alone / right after a store | 458 / 713 cycles | waits until L2 acknowledges the SM's pending writes |
| `st.release` | 679 cycles | the same acknowledgement wait |
| One-way handoff, no fence | 376–427 cycles (134–152 ns) | about one round trip |
| One-way handoff, release/acquire | 950–1,097 cycles (333–384 ns) | the fence adds \~600 cycles |
| Poll loop checking every D cycles (D = 0 → 4,000) | 434 → 2,429 cycles one-way | adds about D/2 |
| Reading a line another SM just wrote | 407 vs 396 cycles | no extra coherence trip |
| Counter barrier, 1 SM / 188 SMs | 473 / 666 ns | fixed latency dominates |
| Cost per extra arrival (8 SMs and up) | 0.09 ns (0.26 cycles) | same-word atomics run at one per 0.41 ns, so 188 arrivals queue ≤ 77 ns |

The fixed cost of about 1,900 cycles breaks down roughly as follows: a fence on the arriving side (\~460), the arrival reaching L2 (\~190), a poll round trip (\~383), half a poll period (\~190), a fence on the waiting side (\~460), and the spread of arrival times across 188 SMs (\~500). These terms sum to about 2,180, so they partly overlap (the arrival spread runs concurrently with the fences). Moving the data adds L2 queueing on hot lines. When all 188 SMs × 8 warps load the same 128-byte line, each load takes 3,411 cycles; with 8 copies, 862; with a private line per SM, 365. A 16 KiB vector is 24,064 line requests per boundary, which is why one shared copy takes 614 ns to read and 8 copies 377 ns.

The L2 hit latency itself varied between 354 and 870 cycles from one process to the next, depending on which L2 slices the buffer landed in. The earlier sections used the \~700-cycle figure from the first runs; the breakdown above uses the \~380-cycle figure measured in the same binary. Both reproduce the measured totals, because the fences, not the raw trip, carry most of the cost.

## Why flag-in-data, per-producer flags and clusters lose

Each alternative removes a cost that was not the bottleneck and adds a larger one.

| Design | What it removes | What it adds | Result |
| --- | --- | --- | --- |
| LL8 / LL16 / LL128 flag-in-data | the fence: one-way drops from \~967 to \~400 cycles | every poll becomes a data read: LL8 averages 1.62 poll rounds (up to 4), reading 41.4 KiB per SM for 16 KiB of data, 7.8 MB of L2 reads per boundary vs 3.1 MB for the counter, all on one copy's hot lines | 1.6–2.2 µs; LL16 with 8 copies spreads the hot lines and is the best fp32 gather (1,151 ns), still reading 38 KiB per SM |
| Per-producer flags | the single shared counter | keeps both fences (713 + 480 cycles); 188 flags fit in 6 lines, each SM polls them about twice, 283 flag loads per boundary; with 64–186 SMs polling, a flag write takes 568–600 cycles to be seen instead of \~400 | 2.2–2.6 µs |
| Counter split 8 or 32 ways | arrival contention, which was already under 77 ns | more lines to poll: the per-arrival cost rises from 0.09 ns to 1.07 ns (8 counters) and 2.88 ns (32) | 1.09–1.29 µs with data, no gain |
| Cluster hierarchy (8 or 16 SMs) | L2 inside the cluster: `cluster.sync` is 149 ns (430 cycles), a remote shared-memory load 220 cycles vs L2's 364 | distributed shared memory moves only \~1.3 bytes/cycle per SM however many warps issue loads, vs 6.9 from L2 and 36 from local shared memory, so 16 KiB across a cluster takes 4.3 µs; the clusters still pay the same L2 fences between them | 1.6–1.9 µs through L2; 17–38 µs through shared memory |

Flag-in-data is NCCL's answer for links where a fence costs microseconds. On chip, the fence is about 600 cycles, and the extra polling traffic on hot L2 lines costs more than it saves.

## Why the Megatron column/row pair is slower

The pair replaces two gathers with one all-reduce. But an all-reduce is itself a reduce-scatter plus an all-gather, so it is still two all-SM dependencies, and it moves 188× the data. With the second matrix split by input, every SM's partial is a full 4,096-float vector. The SMs therefore publish 3.08 MB of partials in total, against 16.4 KB for a gather. Timed phase by phase in the explicit reduce-scatter + all-gather version:

| Phase | ns |
| --- | --- |
| Write own 16 KiB partial | 577 |
| Barrier 1 (all partials written) | 1,345 |
| Read my 22-word slice of all 188 partials and sum | 634 |
| Barrier 2 (all sums written) | 796 |
| All-gather read of the 16 KiB result | 1,184 |
| **Total** | **4,612** |

The single-pass version with `red.add` avoids one barrier but concentrates the work: all 188 partials land on the same 128 lines. Each line absorbs 1,504 serialised 16-byte updates at about 6 cycles each. The red phase alone takes 3,155 ns into a shared target, against 909 ns into private targets (0.98 vs 3.39 TB/s). Its phases were: issue 1,020 ns, a fence waiting for its own reds 1,671 ns, arrive and wait 1,239 ns, readback 964 ns.

Net: one all-reduce costs 2.1–2.2× one gather in every binary measured (3,645 vs 1,638 ns in the gather benchmark; 4.6–4.9 vs 2.2 µs in the breakdown). At best it ties the two gathers it replaces. Megatron pairing wins across GPUs because it avoids communicating the wide intermediate over a slow link; inside one GPU the intermediate is cheap to gather, and the reduction is the expensive part.

Absolute times in the breakdown binary run about 35% above the same algorithms in the gather benchmark, probably because the hot vectors landed on different L2 slices (the gather already varied 1.64–1.94 µs between runs). The causal comparisons use ratios measured within one binary.

## What this means for the GPU baseline

The GPU baseline in the analytical model should price each dependent boundary by the kind of dependency, from the measured values, not by one flat number.

| Dependency kind in a decode layer | Example | Cost to charge |
| --- | --- | --- |
| Fused inside one thread block | epilogue of a matrix product, element-wise op on its own tile | 7 ns |
| Inside one cluster | a small reduction kept within a cluster | 131 ns |
| One-to-one or PDL boundary | a kernel chain with PDL; a megakernel handoff | ≈366 ns |
| Gathers from every SM | split matrix-vector product feeding a norm, softmax, router, the next layer | ≈1.0 µs (0.74–1.15 µs), measured with the vector delivered and under a weight stream |

- **Only measured costs are charged.** The published 1.3 µs CUDA-graph gap and the 100 ns target are no longer used anywhere in the model. A plain CUDA-graph gap on this part measures 428 ns, and PDL and megakernels remove launch from the boundary, but they cannot remove the L2 traffic that the dependency itself needs.
- **The ROM decode core is not bound by this.** Its dependent steps are sequenced inside one core by a hardware sequencer: about 5 cycles (≈5 ns) of issue gap per instruction, with chaining overlapping dependent operations.

## Caveats and reproduction

- **Not a B200.** GB202 is the workstation Blackwell die; the B200 is two GB100 dies joined by a die-to-die link, with its L2 split across them. An all-SM dependency on B200 may also cross dies, so these figures are measured for GB202 and only derived for B200.
- **Shared GPU.** Another workload held about 52 GB and 30–38% utilisation during the runs. Minima approximate the uncontended cost; medians include queueing behind the other tenant.
- **Empty kernels.** The launch-gap and PDL figures use kernels with no work, so they show the boundary alone; real kernels add tail and prologue time on top.

Reproduce with `tools/gpu_microbench/dep_latency.cu` (boundary mechanisms) and `tools/gpu_microbench/dep_latency_v2.cu` (decomposition and methodology checks), tools/gpu\_microbench/gather\_designs.cu (gather designs and the weight-stream chain) and tools/gpu\_microbench/breakdown.cu (cost breakdown), built with `nvcc -O3 -arch=sm_120 -rdc=true` (CUDA 12.8). Results are in `results/gpu/blackwell_dependency_latency.json`, results/gpu/blackwell\_gather\_designs.json and results/gpu/blackwell\_sync\_breakdown.json in the OpenTallas repository.
