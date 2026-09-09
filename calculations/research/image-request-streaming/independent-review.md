# Independent streaming-image candidate review

No correctness blocker found in the frozen research candidate. Public integration is outside this audit and should remain separate from the serial image-request-budget delivery.

`python calculations/research/image-request-streaming/check-independent.py` passes26 independently constructed DAG/resource schedules,7 rejection cases, equal-work mode checks, and preview delay/no-delay cases. Exact outputs are saved in check-independent.json. The checker constructs its own upload, propagation, processing, encoding, preview, download and assembly task graph from input metadata; it does not derive expected times from candidate output timestamps. It schedules earliest-ready tasks against separate resource clocks, enforcing non-preemptive FIFO downlink order and preview priority only on equal release times.

Dependency and resource checks:

- Each input block arrives only after its own upload serialization plus forward propagation. Server work requires the corresponding arrival in independent mode and all arrivals in whole-image mode.
- Each final block is released by its own encoding in independent mode, or the all-final-encoding barrier in whole-image mode. Download serialization shares one resource with previews. Reverse propagation occurs after each download; final assembly waits for every final block arrival.
- Propagation events have no link resource. In-flight propagation overlaps subsequent serialization and does not accidentally turn a per-block propagation delay into repeated serialized RTT overhead.
- Uplink, server, downlink and client positive-duration intervals never overlap themselves. Upload/server/download may overlap each other, subject to dependencies. Processing, final encoding and preview encoding share the server; previews cannot invent a second processing resource.
- Same input/output bytes and identical summed per-resource work are preserved between modes when preview is absent. Different completion time follows only from the explicitly changed barriers and authorized independence.

Hand-counted defaults match: whole-image completion12.8s (64/5); independent-block completion12.36s (309/25). The illustrative500KB preview plus0.05s server encoding changes whole-image completion to12.85s (257/20). The same preview fits otherwise idle gaps in independent mode and leaves final completion12.36s. A separate fast-upload/slow-download case with a10MB preview proves that additional preview downlink bytes can postpone final delivery. Preview encoding after the last processed block need not block final downloads already released; the candidate correctly allows that server/downlink overlap.

The independent grid includes slow/fast upload, fast/slow downlink, long asymmetric propagation, first/last preview boundaries, nonzero preparation/connection/assembly, and zero-work release ties. All candidate event IDs, exact starts/finishes/durations, dependency precedence, final/preview arrival times and network-byte sums match.

Scope and rejection behavior are appropriate. Independent mode requires explicit true authorization; cross-block and foreign-block dependencies reject rather than silently assuming halo/global-attention independence. Quality contracts are nonempty caller assertions, not quality measurements. Preview is a separately declared lower-quality processed-prefix output, not automatically a full-frame preview or a substitute for final delivery. Preview readiness is unknown when absent, and measured time remainsnull. Whole-image mode is a same-work barrier comparison rather than a claim about actual monolithic codec/model speed.

Only independent checker/report/results were written. Candidate calculate.py and public sources were not modified.
