# K3 alias documentation integration: accepted

This is a finite review of the single assumption replacement, not a new runtime or checkpoint compatibility claim. No public files were modified by this review.

The current public module SHA-256 is `cd9d96b9488a76cc5791b872ea17b0fa0333baa1d94d803ce814d0790184673a`. Reversing exactly the proposed string replacement recovers `5ff3fddd42464e82e4b90b60e322d314602f75aea671bce32a2784b202038cfd`, equal to the pre-integration binding. Therefore there are no additional module byte changes.

The pinned official FLA commit is `c51953382397da5c3b7b8a41e568915b703e2934`. Both source files were checked against their already archived official-source SHA values:

- [chunk wrapper](https://raw.githubusercontent.com/fla-org/flash-linear-attention/c51953382397da5c3b7b8a41e568915b703e2934/fla/ops/kda/chunk.py), lines 403–411: recognizes `transpose_state_layout`, emits a deprecation warning, and assigns `state_v_first = kwargs.pop('transpose_state_layout')`; the selected value is forwarded to the implementation at line 483.
- [recurrent wrapper](https://raw.githubusercontent.com/fla-org/flash-linear-attention/c51953382397da5c3b7b8a41e568915b703e2934/fla/ops/kda/fused_recurrent.py), lines 445–453: the same alias mapping, forwarded at line 489.

The extracted, unmodified AST alias blocks passed eight Boolean cases, plus two absent-alias cases. An already truthy `state_v_first` together with the deprecated flag raises; explicitly false `state_v_first` does not raise. This is the actual source guard, rather than a stronger claim that every simultaneous keyword occurrence is rejected. The check does not import or execute GPU kernels.

Old/new calculations ran under Python 3.11.4 for all ten relevant book scenes. The three direct KDA results differ only at `/assumptions/2`; the four composed forward results differ only at `/components/kda/assumptions/2`; the three chunk results are identical. Replacing the new assumption with the old text makes every complete JSON value equal, including all matrices, non-matrix work, state, sources, and summaries.

The original shape reconciliation archive remains byte-identical to its locked SHA `6b624a88c1d9b3a6c55d0abfa1ed3a6ca7691be401608c0c4c6c8991b53658fe`. Its 69 explicit mismatches remain config A_log `[96]` versus checkpoint `[128]`, a total difference of 2,208 parameters / 8,832 FP32 bytes. `recommendations.json` still has `shape_repair: null`. No converter, slicing, padding interpretation, matching release dependency, or successful checkpoint load is asserted. The review reuses the previous header reconciliation rather than rereading all 96 headers.

Reproduce this finite review with:

```sh
PYTHONDONTWRITEBYTECODE=1 python calculations/research/k3-alias-integration-independent/check.py
```

`verification.json` records the complete source rows, wrapper cases, changed JSON paths, source hashes, and preserved conflict. The original and public snapshots are local review copies.
