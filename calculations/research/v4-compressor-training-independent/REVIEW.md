# Independent ratio128 compressor review

Passed for the unrounded, start_pos=0, complete-block, non-overlap main compressor. 170 independent checks and 4 author tests passed without skips; batched tensor autograd forward/input/shared Wkv/Wgate/APE/gamma comparisons had maximum error 1.78e-15. Fixtures use batches 2/3, one/two/three blocks, true ratio128 and a separate small ratio2 numerical fixture.

Source model.py:279–376 confirms two FP32 projections, featurewise softmax on token axis, gamma RMS and block-start rotary positions. Complete ratio128 prefill does not write rolling state; no tail, online state VJP or cast STE is inferred. Source BF16 output/cache bytes remain separate from FP32 reference saves. Scalar formulas were independently reconstructed per block/feature, matrix contractions counted separately, saved objects deduplicated. Three JSON/MD scenes replay exactly; 54 source records match public lock and byte hashes, and frozen artifact/dependency hashes match. No author candidate was modified.

The review does not cover ratio4 overlap, restored-state gradients, quantized numerical equivalence, full attention or full V4 training. Current strict rejection of tails is appropriate to this declared partial contract; those branches remain required future work.
