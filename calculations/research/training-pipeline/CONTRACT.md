# C55 Qwen3-8B PP4 synchronous training event contract

This candidate implements the requested GPipe/1F1B stage schedule. It does not close all C55 long-sequence/MoE/training-runtime extensions. Shared files are read only. The public candidate has ordinary relative imports and portable tests.

## Fixed actual workload

Official Qwen3-8B config has 36 decoder layers. Stage s owns layers 9s..9s+8. Embedding is on stage0; final norm, untied head and dense loss are on stage3. Public training_nonmatrix and its unchanged training_matrix_original supply every operation. Repeated layer operations split by nine copies, never by dividing total model parameters alone. Per-stage matrix/scalar/special rows and the original public data-operation account are retained. Exact parameter ownership drives update and gradient-accumulation counts.

The once-per-step shared RoPE table is removed from per-microbatch stage work and listed as setup. Setup time explicitly includes its preparation/distribution contract. Ordinary microbatch head/loss work uses all positions and equal supervision counts. A logical update occurs only when every stage and every microbatch backward has completed. Stage-local updates may then execute concurrently; all finish before the step completes. Public AdamW coefficient work is once per step, not once per microbatch. Microbatch parameter gradients are initialized by the first contribution, followed by M−1 dense additions and a single division by M for equally sized mean-loss microbatches. These parameter accumulation operations are additional to each microbatch VJP and are listed separately.

## Schedule and resource contract

GPipe: each stage forwards microbatches 0..M−1. A global final-forward barrier precedes all backwards; backwards execute M−1..0. Non-interleaved synchronous 1F1B: stage s warms up min(3−s,M) forwards; alternates another forward with the oldest backward; drains remaining backwards. Stage orders are explicit output.

For each (stage,microbatch) the graph contains exactly one forward and backward. A downstream forward waits for its activation transfer. An upstream backward waits for the downstream gradient transfer and its own forward. Each stage has one nonpreemptive compute resource. Link resources are either six independently serialized boundary/direction links or one shared half-duplex resource for all directions and boundaries. Compute may overlap links. Transfers use earliest-ready scheduling with deterministic priority and ID tie-break; this is one declared arbitration policy, not a globally optimal schedule.

Times are caller-provided finite nonnegative service seconds: four forward, four backward, three activation transfer, three gradient transfer, four update and one setup service. They are conditional inputs, not official throughput, measured runtime or automatically inferred from incomplete operation totals. The default intentionally contrasts F=.01s and B=.02s. Slow-stage scenarios perturb actual service asymmetry while preserving exact Qwen work. Zero services are allowed for mathematical boundary checks.

The report includes makespan, total sequences M*b and tokens M*b*T, useful F+B device service, per-stage idle over the training interval, and a replay with zero transfer durations. The difference in makespan is exposed transfer under this fixed schedule/arbitration, not sum of all link times. Idle includes fill/drain, ordering and dependency wait; it is not attributed to one cause without evidence.

## Activation and transfer reservations

Public nonlinear saved objects are assigned to their actual stage. save_nonlinear retains those identities; recompute_silu uses the existing g/u policy and reserves two FP32 F-wide vectors for one layer at a time during backward. Optional additional_saved_bytes[4] supplies extra caller-defined saved state.

For deliberately conservative stage reservation, the complete per-microbatch saved subset is reserved at stage forward START and released at backward END. This is explicit reservation policy, not a claim that all tensors are simultaneously allocated at forward entry in a backend. Recompute workspace is likewise reserved for the entire stage backward. Public saved nonlinear values omit GEMM saved inputs/outputs, so default extra=0 yields only a partial declared activation budget. complete_training_activation_peak_bytes stays null.

Each boundary sends a packed BF16 hidden activation (2*b*T*4096 bytes) and FP32 hidden gradient (4*b*T*4096 bytes). Source buffers live from producer END through transfer END; separate destination buffers live from transfer START until consumer START. Network and consumer-state ownership are distinct. Copies into omitted GEMM state are not invented. Even a zero-duration transfer can leave a receiver queued until its compute stage runs. Half-open lifetimes release before allocate at equal timestamps, and zero-length intervals contribute zero peak.

Persistent weights/gradients/master/moments, complete backward intermediates, unprovided GEMM saved state and allocator workspace remain excluded. Parameter ownership and public optimizer work are provided separately; these must not be mistaken for included activation memory.

## Acceptance

Tests sweep M=1/4/8/16. For equal F=B=1, zero links/setup/update and P=4, both policies take 2(M+3); saved-only GPipe peak is M objects per stage, 1F1B is min(M,4−s), while queued transfer buffers are separate. M=1 policies agree with asymmetric service and shared links. Slow-stage/shared-link tests verify every dependency, exactly-once F/B, compute/link non-overbooking, global update barrier and complete activation drain. Actual matrix/nonmatrix/parameters/saved-object sums conserve the public source account. Scene replay and invalid-input rejection are tested.
