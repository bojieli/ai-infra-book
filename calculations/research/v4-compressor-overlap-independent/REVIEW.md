# Independent ratio4 joint output/state VJP review

383 checks and four author tests passed without skips. Seven independent batched tensor fixtures span T=1/3/4/7/8/11/13, batches two/three, absent output, overlapping blocks and tails. Output and written-state values, input gradients and shared Wkv/Wgate/APE/gamma gradients agree to 1.56e-15. Unwritten fresh state is constant. Only finite written score states enter the tensor oracle loss.

Fixed source model.py:279–376 confirms previous-block first-half/current-block second-half selection, first-block padding, last-full-block and remainder writes, and duplicate APE addition. Independent enumeration verifies APE position multiplicities across batch, valid-slot scatter and returned-state scatter at 24 geometries. Source subset bytes and memberships, artifact/dependency bindings and four JSON/MD replays match. The ledger deliberately charges full padded eight-slot local arithmetic, separately discarding constant-slot gradients; it is not a literal Python instruction profiler.

Passed only for fresh start_pos=0 with explicit output-state adjoints. No arbitrary restored-state VJP, positive-start online sequence, cast surrogate or complete training claim. Saved objects and source state interfaces remain distinct, not a peak sum. Candidate source unchanged.
