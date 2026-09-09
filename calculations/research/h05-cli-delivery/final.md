Completed the independent audit of **131 devices and all 287 peak records**. Deliverables are in the task directory; the original repository was not modified.

- [Concise report](REPORT.md)
- [Machine-readable field review](unresolved-review.json)
- [Peak provenance and formula patch](proposed-hardware-provenance.patch.json)
- [A100 SKU evidence patch](proposed-a100-sku-evidence.patch.json)
- [Source metadata correction patch](proposed-source-note.patch.json)
- [Official archive URL/date/SHA manifest](archive-manifest.json)
- [Test results](tests.json)

The principal findings concern missing derivation formulas, loss of original source units, A100 SKU provenance, and unresolved accumulator, clock, power, and profile mappings. **No numeric peak correction was established.** Proposed patches preserve rates, unknown fields, and scope.

All **72 archive hashes matched**. The nine existing hardware tests passed on both runs, and local patch validation passed. A negative control confirmed that the structural validator accepts a fabricated rate with a nonexistent locator—source presence is not proof.

H05/H07 remain unaccepted for the documented gaps. New raw downloads failed due to DNS restrictions; all proposed fixes rely on hashed local official archives.