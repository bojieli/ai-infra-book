Review complete. **H01 needs a hash refresh; H04 bindings remain valid.**

- Verified 34 NVIDIA and 36 Apple source bindings against locked metadata and actual local file hashes/byte counts.
- All 97 Apple device hashes match. Four of 32 NVIDIA device hashes changed.
- Reconstructing the pre-H05 records reproduces every accepted NVIDIA hash. Replaying all 145 patch operations reproduces the current catalog exactly. Changes are limited to clock/accumulator evidence, with **no rate, precision, sparsity, or resource-scope changes**.
- Structural validation passed for 129 NVIDIA/Apple records. Eight targeted existing tests passed.

Deliverables:

- [REVIEW.md](/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check/REVIEW.md)
- [Machine-readable revalidation evidence](/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check/revalidation.json)
- [Proposed H01 inventory](/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check/proposed-h01-source-review.json)
- [Revalidation script](/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check/revalidate.py) and [test log](/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check/tests.log)

The relevant files are untracked, so patch application is verified in the working catalog; a Git merge commit is not established. Root/parent `AGENTS.md` files were absent. No live-source refresh or full claim re-review was performed; existing specification unknowns and incomplete H05 mappings remain. H03/H07 were not audited, and shared repository files were not modified.