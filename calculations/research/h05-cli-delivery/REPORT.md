Independent H05/H07 field review — 2026-09-09

Reviewed the current `calculations/PLAN.md`, `hardware.py`, and a captured `hardware.json`: **131 devices, 287 peaks, 101 devices without peak records**. All peaks have individual field reviews in `unresolved-review.json`. All **72 referenced archived source hashes match** the lock. No original repository files were written. H05/H07 remain unaccepted.

The main defects are provenance and proof gaps; this review did not establish a numeric peak transcription error that warrants changing a rate.

- **A100 SKU provenance:** the primary whitepaper table identifies **40GB SXM4**, while the catalog selects 80GB SXM and PCIe. The archived product page corroborates the rates for those products. The separate A100 patch adds that missing per-peak identity evidence while retaining architecture evidence. It does not transfer the old table’s Boost clock to either 80GB SKU. See [official A100 specifications](https://www.nvidia.com/en-us/data-center/a100/), archived as `nvidia-a100-page`, and the whitepaper Table 4.
- **GB200 missing derivations:** six dense rows are explicitly derived by halving sparse values under footnote 2, yet have `derivation: null`. The patch restores formulas and original PFLOPS/POPS units. NVFP4 has its own explicit sparse/dense pair. See [official GB200 specification table](https://www.nvidia.com/en-us/data-center/gb200-nvl72/).
- **Original units:** Rubin, GB200, GB300 and RTX PRO Server often put normalized tera values in `reported`. The patch records source units and conversions without changing numbers, precision, unknowns, or resource scope. H200’s source INT8 row says TFLOPS; the integer interpretation is correct, but its unit correction needs explicit provenance.
- **Clock and power:** generic “official peak” text proves no frequency. Six RTX products have useful Boost evidence; H100 has separate clock domains. Its clock table does not explicitly assign INT8 or FP16/BF16 non-Tensor rates to those domains. TDP/TGP values do not establish operating power at peak throughput.
- **B200/B300 power candidate:** the archived technical brief provides per-GPU maximum TDPs of **1000W/1100W** in Table 3, page 26. Current config notes deliberately separate that brief’s profile from the HGX page. The review records this candidate evidence and keeps power null pending reconciliation; it would be wrong to silently combine profiles. See [NVIDIA Blackwell technical brief](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf).
- **Accumulator proof:** explicit Tensor accumulator table headings provide stronger evidence than a generic non-Tensor label. PTX BF16/TF32/INT8 type constraints establish instruction legality, but need a distinct product-rate mapping. The JSON distinguishes these cases; it does not invent missing fields or silently disable existing records.
- **Preserve unusual official values:** GB300 FP4 is 1080/1440 PFLOPS, and INT8 is 12/24 POPS in the technical brief. Do not impose a twofold FP4 rule or copy GB200 INT8. Ascend 950 combined totals are published rounded totals, not sums to recompute from rounded components. Rubin inference/training conditions and single-GPU column remain distinct.
- **Metadata error:** `nvidia-blackwell-brief` has an unrelated CloudMatrix sentence in its archive note. A separate source-lock patch corrects only that note.

Deliverables:

| File | Use |
| --- | --- |
| `unresolved-review.json` | Per-device/per-peak review of precision, accumulator, unit, sparsity, rate, scope, original value, derivation, clock and power; finding IDs and source pointers |
| `proposed-hardware-provenance.patch.json` | RFC 6902 patch for original units, formulas and H200 INT8 unit normalization; 182 operations including guards |
| `proposed-a100-sku-evidence.patch.json` | Guarded additive A100 per-peak SKU corroboration; preserves previous supporting evidence |
| `proposed-source-note.patch.json` | Guarded source-lock metadata correction |
| `archive-manifest.json` | Original official URLs, archive dates/revisions, expected and verified SHA-256, read-only archive paths |
| `hardware.snapshot.json` | Exact review input, with its SHA recorded in the review |
| `evidence/` | Extracted source text and selected rendered PDF tables; originals identified by the manifest |
| `tests.json` | Actual validation results and structural-validator negative control |

Patches are proposals only. Hardware patches target `calculations/configs/hardware.json`; source-note patch targets `calculations/configs/sources.lock.json`. Each contains value/identity guards. Apply to the captured version or rebase carefully if concurrent work has changed array ordering or fields. No patch replaces a whole device or changes a peak rate, scope, or unknown precision field. Numeric source-profile reconciliation is deliberately left unresolved.

Validation: the repository’s **nine `HardwareAccounting` tests passed on both runs** (18 test executions). All 131 devices validated after locally applying the provenance patch, and again after the separate A100 evidence patch. Local checks verified 287/287 field-review coverage, patch guards, source-note application, preserved peak values/unknowns/scopes, and 72/72 archive hashes. A negative control intentionally changed a rate to `1e99` and its locator to a nonexistent table: `validate_device` accepted it. This demonstrates why structural success cannot be called source-content verification. The original config hash still matched the captured input at test time. The full repository test suite was not run.

Limitations: every peak was reviewed, but not every word of all 72 sources or every no-peak device’s host configuration. Selected PDF tables were visually inspected and the remaining relevant tables/footnotes read through layout-preserving text extraction. Explicit vector accumulator evidence, some instruction-to-SKU mappings, peak-specific clocks/power and profile reconciliation remain open. Unknown fields do not prove global official nondisclosure or non-support. No price, delivery, inventory or measured performance claims were checked.

Two official URLs were also opened through the web tool. Attempts to save new raw downloads failed due to DNS restrictions; failures are recorded in `evidence/new/manifest.json`. No new web rendering was substituted for locked raw evidence. All proposed fixes rely on the hashed local official archives, with their existing URL/date/SHA preserved.
