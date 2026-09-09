# C33 Qwen235 same-cohort execution: independent review

The finite ownership/expert/message calculation is accepted. Candidate SHA: `a4ee2e24fa01ea4854f974a26b8266c2d3c4bb37571ad9d418de58d33a7b48e2`. Five public candidate tests pass. Independent verification covers five eight-rank TP/EP/PP organizations, each with balanced and hot routes; every local expert row, matrix subtotal, message endpoint, token identity and capacity boundary is checked. The detailed assertions are compressed in `checks.json.gz`; the count documents this loop expansion and is not a whole-book completion measure.

## Input ownership and matrix conservation

The account correctly retains the existing placement contract: EP replicas own the same request cohort's attention output. EP therefore is not DP, and its experts already have their input X. Zero token dispatch is valid under this premise; importing the separate `moe_dedup` per-source-independent-token dispatch would have fabricated transfers.

Every route explicitly identifies layer/request/position and K selected experts with normalized weights. At each expert owner and TP shard, the independent formula is `6*n*H*(F/TP)`. Summing TP shards and unique selected expert assignments gives exactly `6*L*requests*tokens*K*H*F`, without multiplying that total by EP. The detailed histograms match the actual route records. Empty experts perform zero GEMMs while their parameters remain in placement storage. Selected experts with zero route weights still execute, consistent with the source-style fixed selection contract.

The local BF16 parameter operand reads are `6*H*(F/TP)` bytes for an active expert. FP32 gate/up each read their X operand and write their local intermediate; down reads that product and writes its H-wide partial. These operand-interface figures do not claim HBM reuse or measured precision dispatch. SiLU/product work and post-down route weighting are separate. Scaling each TP partial is algebraically valid, but its rounding can differ from scaling after a TP reduction; the candidate explicitly limits that equivalence to real arithmetic.

## Message graph independently reconstructed

Let R=requests*tokens, A_e be the actual token set active at EP owner e, and S=sum_e |A_e|. Per layer, the communicated row count is

`(TP-1)*S + (S-|A_0|) + (EP-1)*R + EP*(TP-1)*R`

`= TP*S - |A_0| + (TP*EP-1)*R`.

These terms are respectively TP partial reduction, EP partial reduction, EP full-output broadcast and TP full-output broadcast. Multiplying by `H*wire_element_bytes + row_metadata_bytes` matches every layer's wire total independently. At each PP boundary one root-to-root transfer plus receiving-stage fanout adds `TP*EP*R` rows. The complete wire sum equals both aggregate sent and aggregate received bytes.

The numerical identity check initializes a small two-coordinate projection proxy from the actual route weights and per-TP contributions, then executes the candidate's **actual message edges and token lists**, in phase order. Every stage replica reconstructs the direct weighted output on all layers and tested organizations. This checks the graph itself beyond summing an abstract TP/EP array. The author's separate FP64 small-MLP test validates actual SiLU expert algebra. An additional legal case puts all selected experts on EP2 while EP0 has no contribution; its EP2 root correctly supplies EP0. No missing contribution is disguised as a fake dispatch.

The full cohort broadcast includes tokens without local expert contribution, as required by the next replicated attention stage. PP root transfer represents completed block hidden values, whose omitted attention/residual/norm work is explicitly external. Extra end-of-layer replication is part of this declared schedule; it is not presented as the communication-minimal implementation.

## Placement and necessary capacity

For each rank, BF16 parameter bytes and per-request KV are taken from precisely the same TP/EP/PP placement, then combined as `weight + requests*KV + caller workspace`. Independent comparison against that placement holds for all layouts, including TP8 KV replication. Worst-rank budget minus1, exactly equal and plus1 byte all produce the expected fail/pass/pass results. Passing only satisfies this declared resident reservation; it does not establish that route/message staging or allocator needs fit the workspace. Real runtime capacity remains unknown.

## Resource and scope boundaries

Communication phases use independent full-duplex send/receive providers with source injection and destination receive demands accumulated; startup is charged per nonempty edge message. Matrix and communication phases are serial barriers with caller-supplied service rates. This is a conditional expert/communication subaccount, not an official device benchmark or full request lower bound. Missing attention/router/head work, scalar service, route construction, casts and packing remain outside. The route table is logical input metadata, not an inferred replicated GPU allocation.

No blocking issue was found for this scope. All frozen candidate scenarios replay exactly. Shared files and candidate files were not changed. `verification.json`, `candidate.snapshot.py`, `bindings.json` and the rerunnable `check.py` bind the review to the tested revision. Broader C33 multi-model execution and calibrated performance remain separate requirements.
