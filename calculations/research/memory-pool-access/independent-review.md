# Independent experiment6-9 audit

Read outline6.6 and candidate calculate.py. No arithmetic or placement/failure-set error found. `python calculations/research/memory-pool-access/check.py` passed3 storage-identity placements,45 failure sets,72 access cases,576 explicit deterministic arrivals,7 invalid replica inputs and an equality boundary. `check-result.json` records every GiB identity on each node and the first8 arrivals/start/finish/wait values for each access scenario using rational numbers.

Unique data stays192GiB for all replica counts. Physical storage is192/208/224GiB for1/2/3 copies. Node occupancies are[64,64,32,32], [64,64,48,32], [64,64,48,48]GiB. Owner0 identities64..79 are the same16GiB copied to distinct donors, not new unique data. All nodes fit64GiB.80GiB job cannot fit any node, and exhaustive4^4 whole-job assignment checking returns no solution. Splitting/migrating16GiB has the capacity witness[64,64,32,32], but neither supported partitioning nor execution gain is proved.

For every nonempty failed-node subset, the independent checker unions surviving identity storage and checks each job's original local compute-node dependency. Owner0 is unavailable if its local node fails or no full remote copy survives. Each other job needs its own node. This matches45 rows and makes no recovery-time or reliability claim.

The24 scenario combinations are exactly2 bandwidths ×2 latencies ×2 transaction windows ×3 frequencies; all24 output records are identical across replica counts, so replication does not invent bandwidth. Independent service derivation is startup + max(latency,payload/bandwidth,payload/window_bytes ×latency). At deterministic arrivals n×period, Lindley recursion yields wait_n=n×max(0,service−period). Ten of24 cases per replica count have bounded queues in that declared model: all8 cold cases at1/60Hz,2 cases at1Hz,none at20Hz. At1Hz, only40GB/s with4096 transactions succeeds for both declared latencies; service0.4295017296s. The128-transaction/20us case takes10.485765s regardless of10/40GB/s interface rate.

Issues/qualifications for root report:

1. Provenance wording: the module docstring says all sizes/interface rates come from the outline. Outline6.6 supplies64GiB/node and80/48/32/32GiB demand, but does not supply10/40GB/s,2/20us,128/4096 transactions,256B,5us startup, or1/60/1/20Hz. Label those as declared experiment assumptions, not quoted outline inputs.
2. Rate min(B,Nq/L) is explicitly an upper bound. Substituting it into service yields an optimistic duration; bounded=true is therefore conditional on the declared exact deterministic service, not a real-system queue guarantee. The existing assumptions state the exact-service/periodic model; preserve that wording prominently in the reader report. A failure even at optimistic service rules out that service target within the assumptions; a pass does not establish it on hardware.
3. All reads are complete repeated16GiB immutable snapshots. This is a useful frequency stress comparison but does not implement splitting the16GiB into cold and active subsets, growing KV, writes, versioning, replication setup, or complete decode. Candidate assumptions accurately disclose that narrower scope. Do not describe this as a measured or complete active-KV/decode calculation.
4. Slack80GiB is local slack before restoring the missing16GiB: global capacity minus demand is64GiB. Both are correct quantities but need distinct prose labels.

No candidate edits performed. Only independent research checker/artifacts were written.
