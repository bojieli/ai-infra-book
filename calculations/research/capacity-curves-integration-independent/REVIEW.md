# Public capacity-curve integration acceptance

Accepted final public module SHA `0ee399d1c8e09ea6dcddefdb525e2a53f08ef033bd2317f36d349feff58b8f87`. `source_path`, `threshold` and `calculate` complete function ASTs equal the independently accepted candidate. calculate() and actual rendered data.json exactly equal the frozen candidate data. Earlier threshold/step mathematical verification remains applicable; integration has not altered it.

The parent's actual public rendering was inspected after notification. Its manifest binds13 inputs (12 frozen result files plus public plotting source) and4 artifacts (PNG/SVG/PDF/data), all matching actual SHA. Public verify() returns verified_figures3. Actual manifest SHA is `1e5f3a80ffc014015033d231b3396de63d32d9a73d35e10a623d3f44db0f89ab`. The public PNG is byte-identical to the candidate and was viewed again: four legible panels, correct TP8 versus TP2/EP4 titles, decimal budgets,8K/BF16KV/2GiB conditions and zero-notfit/performance disclaimers are preserved without clipping.

A finite verifier defect was identified during review: empty inputs/artifacts lists initially returned success. The parent corrected this before final acceptance. The final verifier requires exact expected path sets and lengths/types for both lists, rejecting duplicates and omitted or unexpected paths before checking hashes.

Fifteen isolated checks now pass using exact copies of the final public module, actual rendered artifacts and twelve inputs; reconstructed manifest entries are asserted equal to the actual public manifest. Both inputs and artifacts lists reject empty/missing/duplicate/unexpected/wrong-type cases. Same-length byte mutations and missing files are rejected for both a source result and a rendered artifact; restoring originals restores successful verification. No shared results, sources or figures were ever altered.

Public render() calls verify_results(include_figures=False) before calculation or plotting. CLI dispatch `plot-capacity-curves` invokes that render path. The parent executed the actual CLI; this reviewer did not rerun a writer concurrently with public reproduction. This audit directly exercised final verify(), manifest hashes and displayed output, rather than claiming a second independent CLI rendering.

The manifest is a freshness/integrity contract for a trusted checkout, not authentication against someone replacing code and manifest together. No figure before first render intentionally verifies zero figures. The acceptance covers capacity curves only, without implying the remaining architecture diagram, quality or throughput comparison is complete.

Evidence: `static-results.json`, `negative-results.json`, `rendered-results.json` and three reproducible check scripts. All review writes are limited to this independent directory.
