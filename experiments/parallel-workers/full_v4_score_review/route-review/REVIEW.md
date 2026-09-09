# Independent review of 6-3 routes-001

PASS. The final BASE analyzer was replayed against an isolated temporary copy of the real run using Python stdlib only. It exited 0 and produced route-analysis.json byte-identical to the delivered result. No model, GPU, generation or calculation task was invoked, and no execution snapshot was modified.

The final seal also passes: 535 file SHA-256 hashes, 68,217,236 bytes. The saved scheduler source hash is 3a26deea85f43d61c27b94013288ad95d6ee75111fe40134893541777c9c8cd4 and matches its explicit source binding. The implementation agent incorporated the suggested source-binding assertion in BASE before final sealing.

Independent raw checks reproduce 36 whole-model forwards, each with layers 0 through 42 in order: 1,548 layer records, 5,090 consumed tokens, 218,870 valid token-layer rows and 1,313,220 expert assignments. Every row selects six valid integer expert IDs; no padding and no repeated-expert row occurred. Actual router classes are HashTopK for layers 0–2 and TopK for layers 3–42.

Each 501-token prompt has two prefill batches, each 2,036-token prompt eight. Every request has four decode forwards, including terminal EOS ID 1. Consumed input IDs exactly reconstruct the original prompt followed by all four returned IDs; positions are contiguous, ending at 504 or 2039. Thus the terminal EOS forward is observed actual work, not an inferred adjustment. All four returned IDs/text/finish match the frozen successful reference, and the text answers match the frozen answers.

The captured scheduler event_loop_overlap launches the current batch before processing the previous result when overlap is enabled. This supports the documented explanation of the observed EOS forward. It does not expose the extra forward's final logits or sampled next-token value, which neither the report nor this review claims to know.

All route start/model-return/synchronization/copy times are ordered and lie within the associated request envelope. The final observer copy ends approximately 1.5–2.3 ms before the response-envelope endpoint. Request wall time starts before the requests.json write and includes application recording plus observer work; it is not pure generation, communication or offload timing. The observer's final JSON append follows observer_copy_end, so that timestamp is specifically copy completion, not log-write completion.

Viewed the final decode-routes.png: all four panels, color scale, axes and bottom scope note are visible without edge clipping. The plot explicitly labels four observed tokens including one terminal EOS and presents the sample as descriptive only.

Limits remain appropriate: four fixed inputs, observer perturbation, private bias-alias compatibility repair, no expert-parallel dispatch/communication experiment, and no numerical clearance of the previously failed strict expert gate. No remaining material issue found in the delivered route evidence.
