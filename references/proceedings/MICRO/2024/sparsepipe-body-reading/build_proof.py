"""Record already completed selected reading; no network or external code."""
from pathlib import Path
import datetime
import hashlib
import json

D = Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def save(f, data):
    (D / f).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def span(f, start=0, end=None, scope=""):
    t = (D / f).read_text()
    return {"file": f, "sha256": sha((D / f).read_bytes()), "char_range": [start, len(t) if end is None else end], "scope": scope}


sections = {
    3: "II-B/C architecture motivation; III opening and Fig.3 dependency abstraction",
    4: "III-A/B sub-tensor dependency; OS/IS; KNN/GCN contextual examples",
    5: "OEI dependency order, Table I matrix live-set counts and Figures 7/8",
    6: "Eager IS, IV-A/B architecture and dual-format overview, Figures 9–11",
    7: "IV-B/C/D mapping, reservation/conversion, compute cores and controller",
    8: "IV-D pipeline, ready dependencies and prefetch heuristic; Figure 13",
    9: "IV-D/E/F conversion drops, eviction/repack/OOM, offline preprocessing and code generation",
    10: "V/VI-A simulation/configuration and evaluation baselines; Tables II/III",
    11: "VI-A limits, skew/compute/buffer bottlenecks; Figures 14–16",
    12: "VI-B/C/D/E evaluation comparisons, oracle and preprocessing ablation; Figures 17–19",
    13: "VI-E/F/G memory utilization, energy/area methodology, VII software compiler boundary; figure labels text read, page image not viewed",
}
scopes = []
for n, why in sections.items():
    row = span(f"page-{n:02d}.txt", scope=why)
    row.update({"physical_page": n, "kind": "full_page_text_selected_read", "image_semantics_only_if_separately_recorded": True})
    scopes.append(row)
left = (D / "page-14-left.txt").read_text()
right = (D / "page-14-right.txt").read_text()
scopes.append({**span("page-14-left.txt", end=left.index("Sparse dataflows"), scope="Continuation of software-only buffer/work-management overhead and SAM sentence"), "physical_page": 14, "kind": "partial_page_text_selected_read"})
scopes.append({**span("page-14-right.txt", end=right.index("ACKNOWLEDGMENTS"), scope="Conclusion and explicit future work for GPGPU implementation, hardware support, automatic discovery"), "physical_page": 14, "kind": "partial_page_text_selected_read"})
images = []
targets = {3: "Figure 3 dependencies", 4: "Figures 4–6 KNN/GCN context and OS/IS orientation", 5: "Figures 7/8 and Table I including bu 90%", 6: "Figures 9/10/11 eager IS, hardware and dual storage layout", 8: "Figure 13 ready/prefetch dependencies; page-8 heuristic formula checked visually, not implemented", 10: "Tables II/III simulation configuration and 11 listed application names", 11: "Figures 14/15/16 grouping, bottleneck examples and baselines", 12: "Figures 17/18/19 GPU subset, oracle and ablation baselines"}
for n, what in targets.items():
    f = f"page-{n:02d}.png"
    images.append({"physical_page": n, "file": f, "sha256": sha((D / f).read_bytes()), "actually_viewed": True, "scope": what, "render_command": ["pdftoppm", "-f", str(n), "-l", str(n), "-singlefile", "-scale-to", "1700", "-png", "paper.pdf", f"page-{n:02d}"]})
original_sources = json.loads((D / "input-sources.json").read_text())
source = next(r for r in original_sources if r["file"] == "paper-088.pdf")
source["original_file"] = source["file"]
source["file"] = "paper.pdf"
source["reused_existing_response_not_new_request"] = True
save("sources.json", [source])
save("reading.json", {"recorded_at": NOW, "identity": {"program_order": 88, "doi": "10.1109/micro61859.2024.00090", "title": "Sparsepipe: Sparse Inter-operator Dataflow Architecture with Cross-Iteration Reuse", "authors": ["Yunan Zhang", "Po-An Tsai", "Hung-Wei Tseng"], "public_pdf_physical_pages": 16, "paper_sha256": sha((D / "paper.pdf").read_bytes()), "version": "Same 16-page author-hosted manuscript as prior abstract batch; exact publisher version equivalence not asserted."}, "new_network_requests": 0, "source_code_files_read": 0, "downloaded_code_executed": False, "new_full_abstracts_read": 0, "full_page_text_pages": list(range(3, 14)), "partial_page_text_pages": [14], "text_scopes": scopes, "images_actually_viewed": images, "navigation_only": {"scope": "Caption/title locator scan for selection; first 18 text lines of pp.15/16 checked as reference-list navigation only, not body conclusions. Prior abstract/first-page identity reused without new reading count.", "rendered_not_viewed": ["page-07.png"], "full_text_extracted_not_all_read": True}, "notes_sha256": sha((D / "NOTES.md").read_bytes()), "byte_example_sha256": sha((D / "byte-example.json").read_bytes())})
save("claim-map.json", {"recorded_at": NOW, "claims": [
    {"id": "two_traffic_categories", "pages": [3, 4, 5], "locations": ["II-B", "III-A/B", "Figures 3,6,7,8"], "claim": "Producer-consumer avoids intermediate materialization; cross-iteration reuses same sparse matrix with compatible sub-tensor dependencies and OS→e-wise→IS traversal."},
    {"id": "state_and_representation", "pages": [6, 7, 8, 9], "locations": ["IV-B/C/D", "Figures 10–13"], "claim": "Dual orientations, mapping/reservation, conversion and live/consumed metadata; eager CSR traffic, eviction/reload and packing add costs."},
    {"id": "not_tiny_cache_unconditionally", "pages": [5, 11], "locations": ["Table I", "Figure 15(d) and discussion"], "claim": "bu peak live nnz approximately 90%; value count fraction is not total SRAM bytes; skew causes later ping-pong."},
    {"id": "evaluation_scope", "pages": [10, 11, 12, 13], "locations": ["V", "VI-A–G", "Tables II/III", "Figures 14–20"], "claim": "Custom cycle simulator with explicit baselines; oracle unconstrained buffer is distinct; RTL synthesized/scaled area is not silicon measurement."},
    {"id": "application_count_gap", "pages": [10, 11], "locations": ["V-B", "Table III", "Figures 14/16"], "claim": "Prose says 10=8+2; displayed names/groups show 11=9+2. Retain conflict, do not use a total in book."},
    {"id": "framework_gap", "pages": [13, 14], "locations": ["VII opening", "Conclusion future work"], "claim": "GPGPU implementation, support and automatic discovery are explicitly future questions; no checked fixed public implementation in this task."},
    {"id": "byte_example", "pages": [], "locations": ["byte_example.py", "byte-example.json"], "claim": "Independent teaching assumptions and exact arithmetic 376→248→176 B, not measured paper result or timing model."},
]})
print("Recorded pp.3–13 text, partial p.14, eight viewed images, no new network.")
