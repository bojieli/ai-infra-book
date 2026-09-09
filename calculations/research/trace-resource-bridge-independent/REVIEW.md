# T05 trace-resource-bridge independent review: passed

Frozen candidate SHA `966e154198a92fdb64d256c9fdb9ad07172276f628842c3bc2ef86228e8bb460` matches the reviewed source. Four portable tests pass with no skips. Independent source and every-forward replay passes 537 comparisons, plus two isolated missing/changed-source rejection probes. No candidate or public file was modified.

## Archived evidence and interpretation

All 11 copied source rows match both their lock byte length/SHA and the original files under experiments/ch02/02-08. Raw prompt ID arrays, response counters and capture identities establish four application Chat calls, 753 input token positions, 489 reported cached positions and 79 returned IDs. The last ID is EOS 151645 for each response, matching its stop reason. Application worker received/finished identities and recorded model snapshot/BF16 launch arguments are checked by the candidate. Only the four original Chat captures are included, not later route-replay events.

The S=reported cached count, P=N−S mapping yields four P values 116,56,53,39 and total P=264. It is an explicit logical retained-prefix interpretation, not proof of actual KV page identity or scheduled prefill shape. Cached prefixes are not computed again. Native records establish application calls and wall times; they do not establish the sequence of model invocations. The default therefore leaves sampled steps, observed model-forward calls, complete-generation resources and final generated state unknown while calculating a declared logical prefill.

## Generation and independent arithmetic replay

The optional returned_ids_serial_policy sets G to returned IDs including EOS. It uses one last-position-head prefill and G−1 single-token decodes. Across four records this is 4 prefill + 75 decode = 79 conditional forwards. This does not assert 79 observed engine calls. The final emitted token is not fed back, so final retained state is N+G−1 positions. The G=1 regression correctly has no decode and no extra state append.

Every conditional step was separately recalculated with public qwen3.calculate, independently of the candidate's affine decode aggregation. Matrix, ordinary scalar and each named special-operation count match at every decode position; all logical-interface totals match sums over the complete per-forward ledgers. Each generation head has exactly one input row. State was additionally checked against the direct BF16 GQA formula `positions × 36 layers × 2(K,V) × 8 heads × 128 dimensions × 2 bytes`.

The two frozen scenario JSONs match complete re-execution after ordinary JSON normalization of Python tuple shapes to arrays; there is no numeric tolerance. Logical prefill matrix work is 3,692,317,638,656 FLOPs. Under the conditional serial policy total matrix work is 4,836,064,624,640 FLOPs and accounted ordinary scalar work is 1,765,521,099 FLOPs. These are logical budgets, not reconstructed kernel execution counts.

## Time, traffic and state boundaries

Application wall differences and engine e2e latency are copied as distinct recorded fields, never divided into GPU throughput. Tool waits remain null rather than invented zeros. Inter-request completion gaps are not promoted to cache-block reuse distances. Interfaces remain labelled logical operands; the history payload overlaps portions of other interface categories and is not summed into a physical HBM claim. Weight accesses are repeated per logical call while resident weights are not added to a state peak. Per-call final state is not summed into simultaneous residency.

Observed model-forward count, actual HBM, actual GPU runtime, tool-wait total and simultaneous KV peak remain null in both policies. The recorded engine launch identifies the captured model and BF16 mode; it does not certify the public mathematical implementation as the exact SGLang backend graph. The scope explicitly preserves this difference, including unknown chunking, speculative behavior, retractions, logits rows and KV lifetime.

The source guard rejects changed bytes and missing files in isolated Path.read_bytes mocks, without mutating archived sources. No blocking mathematical or evidence issue was found within this finite logical mapping. This does not complete the broader observed-runtime reconstruction task.

Re-run with `PYTHONDONTWRITEBYTECODE=1 python calculations/research/trace-resource-bridge-independent/check.py`. See verification.json, reviewed.snapshot.py and bindings.json for the audit binding and scene summaries.
