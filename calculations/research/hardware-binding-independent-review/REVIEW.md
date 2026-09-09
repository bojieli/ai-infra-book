# H01/H04 hardware binding revalidation

Review date: 2026-09-09. Repository: `/Users/boj/book/ai-infra-book` (read only). Deliverables: `/tmp/aiinfra-codex-parallel-20260909/hardware_binding_check`.

**Decision: refresh the H01 acceptance hashes using the proposed file. H04 requires no binding update.** The current NVIDIA records differ from the accepted H01 snapshot solely by the supplied H05 clock/accumulator evidence patch. No rate, precision key, sparsity, operation kind, device identity, memory, power, source membership, or resource-scope change is concealed by this refresh. This preserves the existing source-review acceptance boundary and does not declare H05 complete.

## Binding results

| Binding | Result |
| --- | --- |
| NVIDIA devices | 32 records, 288 peaks; 28 device hashes match, 4 changed |
| H01 family coverage | Existing 25 H01 records retained; the digest still binds all 32 NVIDIA records, including 7 H02 records |
| NVIDIA sources | All 34 recursively referenced sources are inventory-bound; unique lock IDs and file paths; downloaded status; local byte counts and SHA256 match; inventory file/URL/hash/byte metadata and full canonical lock-record hashes match |
| Apple devices | All 97 device hashes and the combined subset digest match; 2 peak records |
| Apple sources | All 36 recursively referenced sources are inventory-bound; unique lock IDs and file paths; downloaded status; local byte counts and SHA256 match; inventory file/URL/revision/hash/byte metadata match; source-subset digest matches |
| Structural validation | `validate_device` passed for all 129 NVIDIA/Apple devices |
| Input stability | All eight captured input files had unchanged bytes at the end of revalidation |

NVIDIA accepted digest: `1391bba3089adda30500efaa3f55dc28167c6a4f110efc2a1658f6f8dae1e217`.

NVIDIA current digest: `6992d6b89a840f24db84185764b1fc19ab85b873b07add77d8e2d2f2669222e3`.

Apple current/accepted digest: `bb7d7e8a9934a55be27c029931047c2fd273892bb809bcd979290bf70f1091c5`.

Apple current/accepted source-subset digest: `bc5d65764bccfbf342c625e6ad73c735bfe2e95801f21e109788f9059b16ddbb`.

Device hashing follows the inventory's exact normalization: devices sorted by ID, full records serialized with `ensure_ascii=False`, `sort_keys=True`, compact comma/colon separators, UTF-8; internal array order preserved. Per-device old/current hashes and every source check are in [revalidation.json](revalidation.json).

## Independent H05 patch check

Read the current `configs/hardware.json`, `configs/sources.lock.json`, `src/infra_calc/hardware.py`, `src/infra_calc/sources.py`, H01/H04 acceptance inventories, and H05 report/patch/source manifest. The implementation verifies locked sources and field membership but does not itself bind acceptance inventories or prove source claims; independent inventory digest checks are therefore necessary.

The patch has 145 operations: 65 test guards and 80 mutations. Mutations are exactly 52 `clock_evidence` additions, 20 `supporting_evidence` additions, and 8 `clock_basis` replacements. Only `a100-40gb-pcie`, `a100-40gb-sxm`, `h100-pcie-80gb`, and `h100-sxm` change.

To avoid assuming the patch report was correct, the audit reconstructed the pre-patch catalog from the full peak-object test guards. That reconstruction matches **every accepted NVIDIA per-device hash and the accepted NVIDIA subset digest**. It then applied all operations in order, checked all 65 guards, restricted mutation paths to the three evidence fields, and obtained an object exactly equal to the current complete hardware catalog. This establishes that all NVIDIA changes since the accepted snapshot are explained by the patch, including unchanged fields outside the guarded peaks. All four H05 source-manifest records also match their current complete lock records.

The existing H100 layout-text excerpt was inspected at lines 1309–1323: it distinguishes 1830/1620 MHz FP8/FP16/BF16/TF32 Tensor domains from 1980/1755 MHz FP64 Tensor and FP32/FP64 non-Tensor domains, and explicitly labels the FP8/FP16/BF16 accumulator rows. This supports the patch's distinction between evidence additions and the eight clock-basis corrections. This pass did not independently rerender the PDF or repeat the full original-source claim review.

Git reports the hardware, lock, inventories and H05 directory as untracked. Thus “merged” is established here as **applied to the current working catalog**, not as a verified Git merge commit or commit-history claim. No Git history exists for the queried hardware path in the current repository history.

## Tests actually run

Command: `PYTHONDONTWRITEBYTECODE=1 python3 revalidate.py`, from this deliverable directory. The script also sets `sys.dont_write_bytecode=True` before repository imports. No source fetch function was called.

In addition to the binding and patch checks above, eight existing unittest methods passed, with zero failures/errors:

- All three methods in `test_hardware_audit.HardwareAudit`: unknown recording status, rejection of unspecified input/unit, and integer/underspecified exclusion reasons.
- Five methods in `test_hardware_expansion.HardwareExpansion`: Apple GPU/memory/host constraints; rejection of mismatched desktop evidence; A100 form factors/B200 power; NVIDIA system-profile scope and sparse boundaries; H100 clock-domain isolation.

The expansion class's whole-catalog setup was bypassed and supplied the already read NVIDIA/Apple subset. This prevents unrelated H03 device validation. These are targeted existing tests, not a claim of a full-suite run. Exact method names/output are in [tests.log](tests.log); executable logic is in [revalidate.py](revalidate.py).

## Proposed update and remaining limits

[proposed-h01-source-review.json](proposed-h01-source-review.json) is a complete proposed replacement for `calculations/inventory/h01-source-review.json`, written only here. It changes the NVIDIA subset digest and the four affected device digests, and adds a `binding_revalidation` explanation pointing to this review/evidence bundle. The acceptance decision, 25-record family scope, 32-record binding scope, source bindings, and retained unknowns are preserved. Keep this review and evidence with the proposal if it is applied elsewhere. No H04 replacement is necessary.

The original H01 H100 narrative about incomplete normalization remains conservative: the patch resolves selected SXM/PCIe domains, while NVL and other accumulator mappings remain incomplete. H05 still does not establish all exact clock/power-bin associations, instruction-to-product throughput mappings, or sustained frequencies. A100 40GB Boost evidence is not transferable to 80GB/CTS. Unknown A800/H20 specifications and other accepted gaps remain unknown. Apple precision-qualified GPU throughput, selected memory-bandwidth gaps, GPU TDP and current retail stock are not newly established by this pass.

Local byte integrity and stable bindings do not authenticate live vendor content or establish exhaustive product coverage. No network re-fetch, current stock verification, throughput experiment, hardware execution, weight download, H03 audit, or H07 archival audit was performed. The eight input-file hashes document the observed state; a later change requires revalidation.

The requested root `AGENTS.md` was absent. Parent locations `/AGENTS.md`, `/Users/AGENTS.md`, `/Users/boj/AGENTS.md`, and `/Users/boj/book/AGENTS.md` had no file, and the repository file search found no `AGENTS.md`. The explicit worker constraints were followed. All writes were confined to this deliverable directory; no shared source/config/inventory or Git mutation, further worker, external message, or persistent goal was created.
