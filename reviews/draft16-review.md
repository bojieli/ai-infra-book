**AI Infra book — draft 16 review**

Reviewed 2026-09-05. Scope: the complete local `skeleton.html`, `README.md`, the existing draft 15 review, and all six OpenTallas exercises, including the current uncommitted material. This review combines editorial assessment, independent arithmetic checks, and selected primary-source checks. It does not certify all hardware claims, audit the external project implementations, or validate predicted performance against hardware.

**Verdict: the book has a strong enough structure to begin writing sample chapters. Its central technical argument is not ready to freeze.** Keep the twelve chapters. The most valuable revision is to make assumptions, resource boundaries, and validation as prominent as the book's memorable explanations.

The [previous review](draft15-review.md) already identified several blockers. Draft 16 adds a warning about the HBM unit error and a substantially better set of OpenTallas cases, but preserves much of the original argument. A warning is useful revision history; it is not a replacement for correcting the active blueprint. Some recommendations below therefore deliberately remain open from the previous review.

**1. What deserves to survive the revision**

“Derive a design from constraints” is a concrete reader benefit. It is more useful than promising familiarity with the latest collection of frameworks. The workload → resource costs → system decisions progression supports that benefit, and the separation of single-instance and distributed inference is sensible.

The fifth step, recomputing the bottleneck after a change, is particularly valuable. So are progressively refined examples, counterfactual exercises, and comparisons organized around the same engineering question across architectures. These can give the book a recognizable teaching method.

The strongest potential contribution is the connection between operator execution, memory, communication, and service objectives, supported by inspectable engineering cases. The author's material is valuable where it exposes assumptions and failed predictions. It does not need to establish exclusive access to a topic.

OpenTallas improves the outline because its exercises permit the proposed design to lose. Its distinctions between residency and traffic, shared and independent resources, and functional versus performance evidence should become conventions for the whole book.

**2. Define the reader and narrow the promise**

The current title and introductory claims suggest all AI infrastructure, while the substantive coverage centers on data-center language-model training and serving. State that focus explicitly. Treat agents, voice, and other workloads as tests of the method where their demand shapes matter. They need not become additional surveys.

A workable primary reader is a systems or ML engineer who knows basic linear algebra, Transformer execution, and elementary computer architecture, but has not designed a large training or serving system. Supply a short prerequisite diagnostic and a compact refresher path. The three reading paths currently explain interests more clearly than prerequisites.

Separate two promised outcomes: choosing a deployment on existing hardware, and exploring a new hardware/model design. The second needs additional evidence about quality, implementation feasibility, manufacturing, and demand. A cost model can rule out candidates or identify promising regions; it cannot establish which model will learn best without quality evidence.

**3. Repair the mathematical spine before extending it**

At `skeleton.html:324–346`, computation, movement, and waiting are simultaneously treated as a decomposition of time, an energy analogy, and a financial exchange rate. These need separate definitions.

Keep the three-part intuition. Under it, establish three explicit objects:

- A demand ledger: arithmetic by operation/precision, resident state, bytes across each resource boundary, and dependencies.
- An execution model: service rates, shared resources, legal overlap, sequential stages, launch overheads, and queues.
- A decision objective: latency, useful throughput, joules, or money, under stated quality and reliability constraints.

For a simplified execution region with independent compute and memory services and sufficient overlap, a lower bound is `max(F / R_compute, Q / BW)`. Work sharing one HBM interface contributes to the same traffic total; dependencies may force stages to add. Neither a universal sum nor a universal maximum represents a whole system. This distinction is also explicit in the [scaling book's roofline treatment](https://jax-ml.github.io/scaling-book/roofline/).

The “equivalent FLOP” table can be an optional normalization of a specified latency or service demand. It should retain raw units and a named reference compute rate. A collective is a function of message size, participant count, algorithm, topology, and concurrent traffic. A joule exchange rate and a time exchange rate are different tables. Spare memory capacity is a feasibility constraint that cannot be converted away by changing units.

An especially important addition is **logical demand versus physical traffic**. Model structure determines operations, tensor shapes, and logical dependencies. Tiling, caching, sharding, replication, and scheduling determine physical reads and communication events. Chapter 2 cannot derive a unique synchronization count from a model configuration alone. Supply a baseline mapping when a physical count is needed, then change that mapping later.

Retain the five steps, but strengthen their contracts:

1. Specify useful output, quality, workload distribution, and service targets; derive the initial demand ledger.
2. Specify hardware and implementation service rates, capacity and power limits, and uncertain inputs.
3. Map work onto resources and dependencies; identify the binding constraints.
4. Enumerate feasible changes and price their side effects, including quality and flexibility.
5. Recompute the full objective and constraints, compare with evidence, and identify where the decision would reverse.

This adds validation to the method without requiring a new chapter or an extra numbered step.

**4. The capstone needs a new derivation, not a corrected unit label**

The error flagged at `skeleton.html:570` remains in the chain at line 593:

```text
80 GB / 3.35 TB/s = 0.0238806 s = 23.88 ms
```

The capacity and bandwidth are the [official H100 SXM specifications](https://www.nvidia.com/en-us/data-center/h100/). This is comparable to the proposed 20 ms TPOT budget. The opening example's `70 GB / 3.35 TB/s ≈ 20.90 ms` independently exposes the inconsistency.

Also, full installed memory is not automatically read each step. For MoE, distinguish total resident parameters, parameters activated for one token, and the union of experts used by a batch. For attention, distinguish resident KV from accessed KV. Compute per-device traffic under an explicit placement. A capacity/bandwidth ratio describes a full-scan scenario; it is not a universal token-time floor or a permanent cross-generation invariant.

Withdraw the dependent assertions that bandwidth cannot constrain TPOT, that capacity alone determines the largest serviceable model after choosing a domain, and that an established 20–50× residual is explained by network tails. Each needs to be derived again.

The power argument at line 579 has a separate problem. `P_domain / P_device_all_in` is a useful budget check if the denominator is independently known. It cannot uniquely derive a product count, and becomes circular if “all-in per-device power” is calculated from that product's total power and existing device count. Port counts, tray increments, switches, CPUs, spatial limits, cooling, and failure scope also constrain the design. NVIDIA itself documents [36 GPUs in one rack and 72 GPUs in either one or two racks](https://docs.nvidia.com/multi-node-nvlink-systems/imex-guide/overview.html).

Build Chapter 12 around a feasible region. For a fixed workload and quality target, let the reader choose parallelism, replicas, batch policy, placement, and possibly precision. Require per-device memory fit, communication and compute feasibility, TTFT/TPOT targets, useful throughput, and power/cost budgets. Then vary one constraint and show which design becomes preferable. Use 72 and 384 as observed design points whose tradeoffs can be studied.

For money, define the accounting period and denominator explicitly: total attributable cost over an interval divided by useful output delivered within the required service conditions over that same interval. For cross-model agent comparisons, successful tasks may be the appropriate denominator. For training, include cost to reach a quality target, alongside the simpler fixed-workload performance comparison.

**5. Keep the order; make chapter boundaries serve understanding**

The “demand side must never discuss optimization” rule at line 472 is too rigid. The book wants to teach co-design, so demand is allowed to change with design. Assign a primary responsibility to each chapter and use explicit baseline assumptions instead of banning needed concepts.

Chapter 4's `6ND` estimate produces approximate operation count. Converting it to accelerator-days requires a hardware rate and an efficiency assumption. Chapter 3 can describe determinants of TTFT without hardware, but cannot calculate actual service time without a service model. Chapter 2 can use `b = 2` for a BF16 example before Chapter 6 explains representation choices.

Likewise, demand chapters can refine the ledger without discovering a new bottleneck. The rule that every chapter must produce a new bottleneck at line 935 contradicts their deliberately limited scope. Replace it with “advance the reader's model and state what is now known.”

Introduce the five-step method through a short complete example in Chapter 1. Keep the formal treatment in Chapter 5. Readers should experience the promised reasoning before reading three chapters of prerequisites.

The chapter-level changes I recommend are:

| Chapter | Concrete deliverable and revision |
|---|---|
| 1 — Introduction | One complete small decision, a reader/scope statement, and the core principles. Reduce the six sweeping claims that internet-infrastructure assumptions have all been replaced. |
| 2 — Transformer demand | A ledger generated from a fixed model configuration: total/active weights, arithmetic, KV, activation lifetime, and logical dependencies. Label mapping-dependent communication separately. |
| 3 — Inference demand | A request timeline and workload distribution: prompt/output lengths, arrivals, shared prefixes, cancellations, and inter-call dependencies. Define TTFT, TPOT, request latency, and offered load. |
| 4 — Training demand | Forward/backward/update work and state. Explain what `6ND` omits, especially attention and additional work. Introduce data supply and rollout/train demand without pretending to have hardware-independent device-days. |
| 5 — Quantitative method | Units, resource composition, calibration, uncertainty, quality-constrained comparison, and reverse budgeting. Keep one whole worked decision visible. |
| 6 — Single accelerator | Rename to “单加速器：存储层次、数值格式与算子执行”. It already extends beyond the chip. Deeply work one kernel and one storage choice; make polyhedral compilation and extensive heterogeneous implementation optional. |
| 7 — Scale-up | A capacity, power, reach, port, and locality budget. Distinguish addressability, memory access semantics, and practical pooling; shared addressing alone does not make all bytes equally cheap. |
| 8 — Networks and collectives | Cost curves and a controlled measurement procedure. Explain algorithm rounds versus physical hops, endpoint versus fabric limits, and library contention. The same primitive model must also apply inside scale-up domains. |
| 9 — Inference instance | Three decisions: resident state, step execution, and admission/batching under SLOs. Define an instance as a scheduling/execution group that may contain several accelerators. |
| 10 — Distributed serving | Routing, stage separation, expert placement, KV movement, and recovery. Compare attention-DP/FFN-EP against alternatives under explicit conditions. Include an example where disaggregation loses. |
| 11 — Training systems | Enough self-contained parallelism derivation to make a decision, plus input/checkpoint/recovery costs. Give RL a bounded resource and policy-version model; extensive algorithm coverage can be optional. |
| 12 — Synthesis | Reuse previously calibrated inputs to compare feasible designs and make conditional predictions. Let the reader identify an unresolved measurement rather than force an exact product or model-family answer. |

Chapters 6, 9, and 11 have the largest breadth problem. Chapter 5 may acquire one as corrections accumulate. Give each a page budget and one mandatory worked decision before adding more material. Do not solve chapter overload by outsourcing essential derivations to another textbook.

**6. Add the missing constraints where they change a decision**

The outline already names many modern techniques. It needs more explicit ownership of a few engineering questions, rather than more technique names.

- **Quality and useful progress:** Quantization, sparsity, model-family changes, and training schedules need a quality constraint. Higher training MFU does not by itself establish faster progress to the required quality. For RL, useful samples and policy lag matter alongside generated tokens.
- **Measurement:** Chapter 6 should take a roofline bound through an implementation estimate to a measured kernel trace. Explain tile underfill, occupancy/resource limits, launch costs, synchronization, and non-matmul work as needed by that case. A hardware specification alone cannot yield actual operator efficiency.
- **Serving headroom:** Chapters 9–10 need admission control, overloading behavior, fairness between short and long requests, model loading, and scaling delay. These determine how much nominal throughput becomes useful service capacity.
- **Training I/O and recovery:** Chapter 11 needs one complete example of input preparation/feed rate and one checkpoint/restart example. Include state beyond weights and distinguish useful training time from elapsed job time.
- **Economics over time:** Establish utilization, idle power, spare capacity, purchase/rental boundary, and model lifetime before Chapter 12. Avoid using a universal national electricity or land-price narrative in place of explicit site scenarios.

These additions can fit within the existing chapters. A Kubernetes catalog, full chip-design course, and survey of every generative modality would dilute the promise.

**7. Technical statements to revise explicitly**

This table is a correction list, not a claim that every remaining sentence has been fact-checked.

| Location | Problem and recommended treatment |
|---|---|
| `skeleton.html:339–346` | Compute/bandwidth ratios are empirical trends under matched precision, sparsity, product class, and accounting boundaries. They are not a theorem that the exchange rate moves in one direction. The “1000×” energy claim needs a specific operation width and memory distance plus a primary source; it is not a universal ratio for all movement. |
| `skeleton.html:485`, `886` | The ideal compute-time/read-time ratio supports a bandwidth bottleneck; it is not a measurement of whole-GPU idle time. Label the 0.07 ms estimate's compute precision and dense/sparse peak convention. Stored INT8 weights do not alone identify the executed arithmetic path. |
| `skeleton.html:516`, `531` | KV quantization affects traffic as well as capacity, even at batch one. Case A already demonstrates this. Weight/activation quantization also has workload-dependent effects, so chapter placement should not be defended by claiming otherwise. |
| `skeleton.html:526` | There is no universal ordering that makes all-to-all the most expensive collective. Specify message accounting, topology, degree, algorithm, and contention. |
| `skeleton.html:532` | Attention-DP/FFN-EP is a design to evaluate, not the only possible mapping. Failure scope depends on placement, replication, implementation, and recovery policy; it is not necessarily the entire physical domain. |
| `skeleton.html:550` | Inference lacks the same rollback semantics as offline training, but state may be reconstructed from retained context or restored from retained/replicated KV. Already streamed output complicates recovery. Teach recovery cost and service semantics rather than a categorical absence of recovery. |
| `skeleton.html:551` | MFU is a diagnostic, not an objective that must approach one. A method that reduces necessary work may reduce MFU while improving elapsed time or useful throughput. |
| `skeleton.html:620–674` | CPO, radix, topology depth, propagation, endpoint overhead, and queueing are distinct variables. Optical packaging does not automatically remove a switching stage or establish a tail-latency improvement. Keep specific architectural conclusions conditional. |
| `skeleton.html:638` | The batch crossover calculation needs the bandwidth direction and collective algorithm. If 900 GB/s denotes aggregate bidirectional bandwidth, substituting it as one-direction egress overstates the budget. In the same simplified formula, 450 GB/s produces about 55 rather than 110. Neither is a general decode threshold. |
| `skeleton.html:645–647` | Do not multiply a message's tail latency by peer count. Model completion as a maximum with contention and dependencies; serialized initiation cost is a separate term. Likewise, logical source/destination pairs are not automatically the number of packets or serialized sends. |
| `skeleton.html:682` | Separate self-attention's arithmetic scaling from materialized memory. Exact attention does not require storing an entire quadratic score matrix; the book's own FlashAttention case should establish this. |
| `skeleton.html:696` | Explain MoE as conditional computation that increases capacity without proportionally increasing active work. Do not claim it originated because compute improved faster than bandwidth. |
| `skeleton.html:707–721` | Memory fit can create deployment discontinuities, but does not establish the unique historical cause of model sizes or prove that all cross-domain deployment is infeasible. Quality, training budget, topology, and service targets remain inputs. |
| `skeleton.html:914–916` | Fusion need not involve recomputation; load balancing need not amortize fixed overhead; scheduling includes choices beyond overlap. Keep the six patterns as useful prompts, not an exhaustive classification that every design must fit. |
| `skeleton.html:970` | Acceptance rate and batch capacity are insufficient to decide speculative-decoding benefit. Include drafting time, verification time, accepted output count, and the correctness contract. |
| `skeleton.html:974` | CPU/GPU offload value is not a monotone function of HBM capacity alone. Price, workload growth, CPU service rate, link bandwidth, and service targets can change simultaneously. Present a fixed-assumption counterfactual. |

The [GPU chapter of the scaling book](https://jax-ml.github.io/scaling-book/gpus/) explicitly uses directional egress bandwidth when deriving collective costs. The original [FlashAttention paper](https://arxiv.org/abs/2205.14135) presents an exact, tiled attention implementation that reduces HBM traffic. The [sparsely gated MoE paper](https://arxiv.org/abs/1701.06538) motivates conditional computation through the separation of capacity and active computation. These primary sources support the corresponding corrections above.

A better timeless speculative-decoding exercise is:

```text
time per emitted token ≈
  (draft time + verification time + other critical-path overhead)
  / expected emitted tokens per cycle
```

State whether operations overlap and whether these are steady-state expectations. Then let batch policy and draft length alter all the terms. The original [speculative decoding paper](https://proceedings.mlr.press/v202/leviathan23a.html) establishes an exact sampling construction that preserves the target distribution. Approximate variants require their own quality contract. This is a stronger durable lesson than two isolated acceptance/capacity criteria.

For tails, use an explicit teaching model before discussing hardware. Under an intentionally simplified assumption of `m` independent, identically distributed message times with CDF `F`, the maximum has CDF `F(t)^m`. For `m = 320`, a threshold at the individual-message p99 has only about a 4% probability of containing all messages. Real fabrics violate independence, so this illustrates why measurements of the joint execution matter; it is not a production p99 estimator. Little's Law relates stable-system averages and cannot supply that missing distribution.

**8. Update the competitive and architecture positioning**

At lines 817–839, the description of the scaling book as treating operators and collectives as fixed external constants is too strong. Its [GPU chapter](https://jax-ml.github.io/scaling-book/gpus/) covers memory hierarchy, topology, and explicit intra-node/cross-node collective derivations. [MLSysBook Volume II](https://mlsysbook.ai/vol2/frontmatter/about.html) covers data-center infrastructure, networking, storage, distributed execution, recovery, and orchestration. Describing the overall work as primarily edge-oriented misstates the present scope.

The claim that a cross-architecture cost calculator does not exist at line 754 also needs removal or a tightly specified qualification. [LLMCompass](https://arxiv.org/abs/2312.03134) already evaluates different hardware designs, mappings, scheduling, and cost. A teaching tool can still contribute transparent assumptions, the book's particular cases, readable decompositions, and uncertainty estimates.

Two architecture rows need concrete correction:

- SambaNova SN40L is not “pure SRAM”: its [architecture paper](https://arxiv.org/abs/2405.07518) specifies SRAM, HBM, and DDR. Separate it from Groq and identify a specific product generation.
- Taalas and Etched should not share a “model frozen into silicon, no programmability” row. Taalas describes [model-specific silicon with configurable context and LoRA support](https://taalas.com/the-path-to-ubiquitous-ai/). Etched's [June 30, 2026 description](https://www.etched.com/progress/frontier-inference-clusters) describes an HBM/SRAM hybrid and shared memory across a scale-up domain. These are vendor descriptions, not independently validated performance results. Classify what is specialized and what remains changeable, using a dated product description.

Treat Graphcore as a case for examining a hardware/workload mismatch, not as a proof that one memory decision caused a company's commercial outcome. Separate the technical prediction from claims about business causation. Similarly, the existence of an open UB implementation makes it useful for teaching; the claim that it is the only inspectable implementation is unnecessary.

Suggested positioning language:

> A quantitative guide to data-center language-model systems that connects workload demand, operator execution, memory and communication costs, and service objectives through reproducible cases across architectures.

The author's original cases and explanations should establish the contribution. Statements about what Google, NVIDIA, or Huawei cannot write weaken the argument and should be removed.

**9. Make the OpenTallas line the standard for evidence**

I recalculated the arithmetic from the values printed in [the case file](../case-studies/opentallas.md). Case A's 1.208 GB KV demand and batch crossover near 13, Case C's 75,674 lanes and 315,306-lane extension, Case D's communication budget, and Case F's 40 trillion-token breakeven and 254-machine equivalent all check out under their stated assumptions. Case B's ordering and approximate results also check out; recomputing from the rounded displayed components changes the printed latency by about 0.001 µs, which is immaterial and should simply be handled by consistent rounding.

This verifies arithmetic, not the external inputs or attainable system performance. The file already marks missing auxiliary-operation costs and separates local implementation evidence from complete-system evidence. Preserve those distinctions.

Make A, B, and C the main sequence: derive demand, compose resource service times, and reverse a target into a supply requirement. Use D as a network-budget counterexample and E/F in the capstone. Their different model configurations must remain explicitly different cases; do not imply that they are successive measurements of one unchanged machine.

The more important draft 16 problem is now internal inconsistency. Case A says KV precision changes bandwidth; Chapter 9 still assigns it only to concurrency. Case B uses a resource-aware maximum plus a serial term; the opening still adds all service times. Case E accepts multiple feasible optima; the historical exercises still prescribe product counts. Promote the case conventions into the main text rather than merely adding a parallel set of better rules.

A useful optional bridge to Chapter 10 is fixed weight placement versus dynamic expert placement. Ask what replication or writable overlays would cost if the fixed design needs to absorb expert skew or a failure. This tests specialization against a real system requirement without expanding into a chip-design course.

**10. Strengthen the exercises and evidence process**

Use two explicitly connected running workloads: a dense baseline and a MoE extension. Share notation, workload definitions, and accounting rules. Introduce the extra MoE ledger entries as a deliberate change. A silent progression from a 70B dense decoder to a 10T MoE is not refinement of the same model.

Historical hardware is an observation, not a unique answer key. Revise the exercises at lines 413–440 and 721 so readers can earn full credit for a different design that satisfies the supplied constraints. Ask which missing assumption would explain the historical choice. Some outcomes cannot be inferred uniquely from public evidence, and recognizing that is a legitimate answer.

Retain counterfactuals and add three recurring exercises: explain a mismatch between a trace and an estimate; identify one assumption whose change reverses a decision; and distinguish two evidence types that cannot validate each other. Analytical calculations and a simulator implementing the same assumptions are not independent confirmation of hardware performance. Software RoCE, CPU collectives, and cycle models can test mechanisms without reproducing a production accelerator fabric.

Replace “second-order means ±30%, enough for selection” with an error estimate tied to the decision margin. If two candidates differ by 10%, a 30% uncertainty can reverse their ordering. Show sensitivity and calibration, and allow “measure this next” as the correct outcome. Tail latency, faults, and dynamic load are modelable under assumptions; they are not reliably predictable from average work and peak device specifications alone.

Keep numerical worked examples in the body beside symbols. Version the underlying inputs in the repository. Removing all numbers from the body impedes the development of quantitative intuition and does not prevent implementation assumptions from aging.

Make five durable principles explicit near the front of the book:

1. Account separately for useful work, resident state, actual traffic, and dependencies.
2. Performance is limited by shared-resource service and critical paths, and the binding constraint can move.
3. Locality, batching, recomputation, approximation, and specialization purchase one benefit with other resources or capabilities.
4. Variability and failures affect useful service capacity and require headroom.
5. Compare feasible designs under the same objective and calibrate the model against evidence that can disprove it.

These principles are the core. The six implementation patterns are a non-exhaustive menu. The five-step method is how the reader applies the principles. Giving each a distinct role avoids three competing organizing systems.

Prediction records are useful, but should not be called the only honest proof of the method. Held-out measurements and successful transfer to an unfamiliar configuration are also evidence. Record each prediction's date, assumptions, metric, horizon, and revision history. A retrospective fit to a known product is an explanation, not an out-of-sample prediction.

**11. A bounded next revision**

Before freezing the outline, finish these concrete tasks:

1. Replace the cost equation's literal interpretation, define the ledgers and metrics, and repair the chapter contracts that contradict them.
2. Replace the six-link capstone with a constrained design comparison. Move invalid historical reasoning into a labeled error-analysis exercise if it is worth retaining.
3. Correct the architecture and competitive positioning tables and remove prescribed historical “winning” answers.
4. Assign a page budget, prerequisite list, and one mandatory numerical deliverable to each chapter. Select the dense baseline and MoE extension.
5. Replace the eleven-item “numbers to verify” list with an assumption/evidence register. Include source/version, boundary and units, evidence type, uncertainty, dependent conclusions, and next discriminating measurement. Do not claim that one all-to-all measurement is the only remaining hole.

Then write a short linked sample: Chapter 5's method, one Chapter 6 kernel/storage example, one Chapter 7/8 communication example, and a Chapter 9 service decision using those outputs. Keep a compact Chapter 1 opening attached to it. Have intended readers calculate an unfamiliar variant and explain where their estimate needs measurement. That tests the book's actual promise more directly than another round of chapter rearrangement.

The network-tail experiment remains valuable, but the book should survive if its favored hypothesis is false or measurements cannot be published. Rank experimental work by whether resolving an uncertain input could change a design choice. A failed hypothesis can become one of the book's strongest lessons if the reasoning and correction are visible.
