# V4 Compressor online independent review

Passed for the declared sequential, unrounded positive-start time graph. Public module SHA-256: `d16fd4cfcb8c9c463ef212cc472451ccafba45131c6992aff4f2d08b3ab98a04`.

The reviewer changed only this independent directory. `check.py` / `results.json` contain 331 passing assertions. The author's four tests were independently re-run: 4 pass, 0 skip. Four frozen scenes and Markdown replay, artifact/dependency bindings and all 54 public-source subset records match actual bytes and SHA-256.

## Source order and state ownership

The fixed model.py positive-start branch adds the current APE row before writing the slot. Ratio4 writes current[4+p%4], pools previous[:4,:D] plus current[4:,D:], then copies all current channels into previous. Ratio128 writes p%128, pools the full state only at its boundary and leaves state otherwise intact. RoPE uses p+1-ratio, the emitted block's first position. The candidate follows these steps and never presents a multi-token positive-start call as parallel execution.

Each update is a new mathematical version. In reverse, post-copy previous and current gradients join into pre-copy current, old previous loses its copy path, the just-emitted pool still contributes to the old previous values it read, and finally the new-token write takes its gradient while killing the overwritten old-slot path. This order is correct; simply differentiating the final in-place buffer would lose necessary history. The timeline's overwritten versions, pool dependencies and final version map are independently reconstructed across ratio4/128, no emit, boundary and multiple-emission cases.

Finite initial scores are leaves with existing APE already included. The candidate does not add initial APE again. Minus-infinity entries are mask constants and have zero adjoints. Caller-provided initial state validity and history ownership cannot be inferred from start_pos alone. Physical source copies and mathematical shared version identities are kept distinct in the memory claims.

## Independent numerical review

Five new FP64 fixtures cover ratio4 S1/N1, S3/N10, S8/N9 and ratio128 S127/N3, S255/N3. Each uses D=4 with two RoPE complex pairs, patterned initial −infinity score masks, nonzero compressed-output upstream and independent nonzero final KV/score upstream.

An independent PyTorch graph uses one-hot functional replacement for slot writes and indexed gathering for previous<-current copies. The scalar objective masks final constant −infinity values before applying final-score upstream. Its derivatives match initial KV, finite initial scores, new X, both projection weights, APE and norm gamma. Initial mask gradients are exactly zero. Maximum absolute discrepancy is 1.7763568394002505e-15. The no-emission case correctly permits state/parameter gradients while norm gamma has no contribution.

The separately re-run author tests also compare fresh prefill3/5→ratio4 online output/gradient chains with full prefill9, and ratio128 tail127→online129 with full prefill256. They reconnect returned initial-state adjoints to the history producer and sum shared parameter gradients. These comparisons validate emitted outputs and losses; they do not assert unused final cache slots equal a fresh-prefill allocation. Independent dual-final-state-upstream tests cover the actual online final state graph separately.

## Counts and saved values

Per-feature full-slot forward softmax and pool expands to m subtracts, m−1 denominator additions, m divisions, m products and m−1 pool additions: 5m−2. Backward expands to m dP products, a 2m−1 dot, 2m score VJP operations and m value VJP products: 6m−1. Adding both pooled branches into existing state gradient buffers is an additional 2mED. Ratio4 copy gradient adds both state arrays, 2*ratio*width*E. These are independently checked, not inferred from the gradient tests.

APE reduction counts use the actual multiplicity of each cyclic position across B and N: width*sum_position(max(count−1,0)), matching width*(BN−min(N,ratio)). No extra initial-history APE gradient is invented. Matrix work, per-token input join, normalization across emitted rows, emitted RoPE positions, new-slot writes/copy bytes and saved-subset totals are consistent with the declared formulas.

Saved X supports each projection dW; every emission retains gathered KV values and probabilities plus norm normalized values/inverse RMS. Those snapshots make overwritten-state reverse work well-defined. Initial/final state interface bytes and physical copy actions are separate from the saved subset; neither is automatically added as a new allocation. Actual pool concatenation/casts, all memory traffic, allocator temporaries and peak remain outside this partial byte ledger.

## Acceptance boundary

No mathematical or delivery blocker was found. The candidate is not full source-quantized equivalence: the source casts norm input and simulates quantization afterward, and no cast STE is asserted. History producer, final-state consumer, attention/indexer and the rest of the model are external. Keep parallel_chunk_supported=false, complete_v4_training=false and actual_peak_bytes=null. This review accepts the explicit local/chain VJP and its declared operation/state account only.
