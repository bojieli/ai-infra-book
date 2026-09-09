# C56 training input supply: independent review

Accepted for its explicit finite R→P→H→C and S→W event/reservation contract. The frozen candidate SHA is `c431fc0f37221bd92e18f3b9f2fa63122476493c266eebda58955f53fc17ba1e`. Independent checks: **3010/3010 pass**. All five frozen scenarios reproduce exactly. No original candidate or shared file is modified.

## Source model, packing and wire representation

Independent config algebra gives `P=2HV+L(2HQ+2HK+3HF+2H+2d)+H=8,190,735,360`, including separate embedding/head, per-layer QK norms and global final norm. Checkpoint payload is therefore `14P=114,670,295,040 bytes`: BF16 parameters plus FP32 master and two FP32 moments. Gradients, arbitrary optimizer/RNG state and file metadata are not included and are not silently treated as zero.

Samples remain in input order and are neither split nor dropped. An independent next-fit example [3,2,4,2,1] at capacity5 yields packs [3,2], [4], [2,1], including three padded positions. Full wire storage is21 bytes per padded token: input IDs8, labels8, validity1, segment IDs4. The same shape is used for H2D and device input reservation. This is a declared representation, not evidence that the production tokenizer/training backend uses it; inter-sample attention masking and label-value construction require the stipulated segment-aware consumer.

## Dependencies and scheduling

Every read precedes CPU preparation, H2D and consumption. Read and CPU pack order stay explicit. Host slot reuse waits for the earlier H completion; device slot reuse waits for the earlier consumption completion. Each snapshot waits for its selected consume and an available snapshot slot, and the next consumption waits for that snapshot. The snapshot slot remains live through its write completion. Writes serialize; shared storage additionally serializes reads with writes.

The scheduler returns a deterministic nonpreemptive earliest-ready list schedule. Reads win equal-ready ties. It is not an optimized or fair I/O scheduler and makes no such claim. Its full-payload checkpoint writes can deliberately expose large input waits; changing storage arbitration would define a different scenario. Checkpoint staging time is explicit device service, so copy technology or bandwidth is not inferred.

A hand-derived no-checkpoint case with one host/device slot and one second for each R/P/H/C operation has four consume completions at4,7,10,13 seconds. The candidate matches exactly and reports9 seconds residual wait. The broader independent matrix covers48 combinations of shared/independent storage, host/device/snapshot slots and checkpoint period. Every dependency, event duration and resource non-overlap holds.

## Slots, byte-seconds and time accounting

Host reservation spans read start through H2D end, holding stored bytes plus packed bytes conservatively; device reservation spans H2D start through consumption end. Snapshot bytes span capture start through write completion. Independent open-interval enumeration verifies the maximum number of occupied slots, exact peak bytes and piecewise-integrated byte-seconds for all pools. Distinct pools are correctly separate; these individual reservations are not claimed as a complete physical-memory peak.

Training completion is final consumption completion. Final checkpoint durability may occur later and is separately reported. The exact identity `training_end = useful_consume_service + snapshot_service_before_training_end + residual_wait` holds. Residual wait includes startup, data dependencies and checkpoint-slot backpressure; it must not be renamed exclusively input starvation. Zero service is accepted where defined, and a zero consumption denominator returns null target rates rather than infinity.

## Scope and acceptance

This closes the finite elementary training-input supply/packing/H2D/checkpoint-contention calculation requested by experiment10-6. It does not establish measured Qwen throughput, tokenizer cost, hardware capacity feasibility, actual storage durability semantics or complete C56 recovery. CPU service, one-worker policy, bandwidths, stored compression and device consumption time remain labelled caller assumptions. The independently reviewed checkpoint/host-transfer modules are reused conceptually, not re-added to the same byte total.

Re-run `PYTHONDONTWRITEBYTECODE=1 python calculations/research/training-input-supply-independent/check.py`. `verification.json`, `checks.json`, `candidate.snapshot.py` and `bindings.json` preserve the check result, exact module and dependencies. The author's five test groups were also executed independently and passed.
