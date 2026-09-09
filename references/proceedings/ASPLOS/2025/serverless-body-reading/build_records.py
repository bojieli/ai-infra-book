"""Package this bounded reading, without changing shared indices or source packets."""
from pathlib import Path
import datetime
import hashlib
import json

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
OLD = P.parent / "parallel-pim-serverless"

def proof(path):
    path = Path(path)
    data = path.read_bytes()
    return {"file": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}

calculations = {
    "scope": "Original arithmetic using rounded Medusa Fig. 8 labels, not a benchmark reproduction.",
    "source_doi": "10.1145/3669940.3707285",
    "physical_pdf_page": 10,
    "model": "Qwen1.5-4B",
    "unit": "seconds",
    "inputs": {
        "vanilla": {"structure": 0.85, "weights": 0.39, "tokenizer": 0.21, "kv": 0.50, "capture": 0.90},
        "async": {"structure": 0.85, "weights": 0.47, "tokenizer": 0.21, "kv": 0.52, "capture": 0.90},
        "medusa": {"structure": 0.85, "weights": 0.42, "tokenizer": 0.23, "kv": 0.02, "warmup": 0.31, "restore": 0.26}
    },
    "expected": {
        "vanilla_loading_s": 2.85,
        "async_loading_s": 2.48,
        "async_bubble_s": 0.26,
        "async_weights_interference_s": 0.08,
        "medusa_loading_s": 1.67,
        "medusa_post_structure_branch_s": 0.56,
        "kv_initialization_saving_s": 0.48,
        "graph_work_saving_before_overlap_s": 0.33,
        "medusa_loading_saving_s": 1.18,
        "medusa_reduction_vs_vanilla_fraction": 0.4140350877192983,
        "medusa_reduction_vs_async_fraction": 0.3266129032258065,
        "async_reduction_vs_vanilla_fraction": 0.12982456140350884
    },
    "limits": [
        "Loading phase only; not VM/container startup, full TTFT, queueing, or a service-wide speedup.",
        "Critical-path dependency and overlap ordering reconstructed from the actually viewed Figure 8.",
        "Rounded measurements are paper inputs; arithmetic is independently computed; no downloaded program executed."
    ]
}
(P / "calculations.json").write_text(json.dumps(calculations, ensure_ascii=False, indent=2) + "\n")

sources = []
for name in ["source-jobs.json.results.json", "pinned-jobs.json.results.json", "detail-jobs.json.results.json"]:
    for source in json.loads((P / name).read_text()):
        source["file"] = str((P / Path(source["file"]).name).relative_to(ROOT))
        sources.append(source)

old = json.loads((OLD / "reading-records.json").read_text())
scopes = {
    171: {
        "stem": "171-arxiv-paper", "pages": [4, 6, 7, 8, 9, 11, 12, 13], "images": [7, 11, 12, 13],
        "sections": ["p4: motivation, Fig. 3 and beginning of design", "p6: resource-complementary scheduling", "p7–8: Algorithm 1/2, vertical and lazy horizontal scaling", "p9: implementation, evaluation methodology and start of results", "p11–12: control overhead, co-scaling trace, local end-to-end evaluation and simulation", "p13: simulated sensitivity, related work and conclusion/limitations"],
        "image_observations": {
            7: "Fig. 6 interception, token request/issue and kernel redirect; Algorithm 1 constraints visually checked.",
            11: "Table 3 CSC/SVR columns and Fig. 12 surge/instance traces verified; Fig. 11 throughput/latency normalized separately.",
            12: "Fig. 15 SVR and normalized JCT are distinct; Fig. 16 throughput is normalized by resources.",
            13: "Fig. 17 is explicitly large-scale simulation; Fig. 18 oversubscription and token count are different axes."
        },
        "claims": [
            {"pages": [7, 8, 9], "finding": "RCKM/IL indirectly controls launch admission, tokens measured as kernel blocks; 5 ms control period is not cold start."},
            {"pages": [8, 11, 12], "finding": "Fast vertical adjustment bridges lazy horizontal scaling and reduces cold-start counts; sub-ms scaling overhead is not model readiness latency."},
            {"pages": [9, 12, 13], "finding": "Five four-A100 workers measured; 1000-node results simulated; historical model/runtime boundary retained."}
        ],
        "framework_repo": "sigserverless/Dilu",
        "framework_commit": "1134655a08e659db9a39f906acb76222d2c86c20",
        "framework_gap": "Pinned README calls code simplified reference; linked vertical-scaling README returned 404. CUDA Graph launch interception and modern LLM coverage not verified."
    },
    172: {
        "stem": "172-author-paper", "pages": list(range(5, 14)), "images": [6, 7, 10, 11, 12],
        "sections": ["p5: alternatives, materialization challenges and start of design", "p6–7: offline/online workflow and pointer restoration", "p8: buffer contents and kernel-address restoration", "p9: first-layer triggering, KV initialization and evaluation setup", "p10–11: models, loading critical path, offline cost and trace setup/results", "p12: trace results, unsupported cases and multi-GPU future work", "p13: end of conclusion and artifact appendix (not a further experiment run)"],
        "image_observations": {
            6: "Fig. 5 separates allocation-index replay, kernel-name restoration and available-memory metadata.",
            7: "Fig. 6 shows reused address A and correct i+1 allocation; raw pointer restoration alone is invalid.",
            10: "Fig. 8 three critical paths, overlap and rounded stage times checked visually; recovered totals 2.85/2.48/1.67 s.",
            11: "Fig. 10 distinguishes model and RPS; Fig. 11 uses actual throughput; warm execution environment condition read.",
            12: "Two-column continuation of 53.0% trace result and single-GPU limitation checked; no new figure on this page."
        },
        "claims": [
            {"pages": [5, 6, 9], "finding": "KV materialization saves available-memory sizing information, not historical user token KV; graph restoration avoids repeated construction."},
            {"pages": [7, 8, 9], "finding": "Restores pointers via allocation indices and kernels through symbol/module lookup and first-layer triggers; weights still loaded normally."},
            {"pages": [9, 10, 11, 12, 13], "finding": "Single-GPU model restore, warm-environment trace setup, direct host pointers only, and modified runtime dependencies limit extrapolation."}
        ],
        "framework_repo": "thustorage/Medusa",
        "framework_commit": "6581d2e5ec8fa4ecdabcdb50560982a78ea3ca89",
        "framework_gap": "Research fork declares vLLM 0.3.1; modified PyTorch/SPDK and CUDA12.4/driver550.54.14 required; dependencies not fully commit-pinned, no upstream parity claim."
    }
}
records = []
for order, scope in scopes.items():
    prior = next(r for r in old["records"] if r["program_order"] == order)
    stem = scope["stem"]
    record = {
        "program_order": order, "doi": prior["doi"], "title": prior["title"], "authors": prior["authors"],
        "version": prior["version"], "source_url": prior["source_url"],
        "existing_source_pdf": {k: prior["representative_pdf"][k] for k in ["file", "bytes", "sha256", "pages"]},
        "existing_pdf_response": next(s for s in old["sources"] if s["file"] == prior["representative_pdf"]["file"]),
        "reading_status": "selected_sections_read", "full_paper_read": False,
        "physical_pdf_pages": scope["pages"], "sections": scope["sections"],
        "page_extraction": "pdftotext -f N -l N input.pdf output.txt; default reading order, no -raw/-layout; no text fragments manually removed.",
        "page_text": {str(n): proof(P / f"{stem}.p{n:02d}.txt") for n in scope["pages"]},
        "viewed_page_images": {str(n): {**proof(P / f"{stem}.p{n:02d}.png"), "actually_viewed": True, "observation": scope["image_observations"][n]} for n in scope["images"]},
        "claims": scope["claims"],
        "framework_repo": scope["framework_repo"], "framework_commit": scope["framework_commit"], "framework_gap": scope["framework_gap"],
        "chapter": 11, "read_date": "2026-09-09"
    }
    records.append(record)

out = {
    "scope": "Parent-assigned Dilu/Medusa selected body comparison for chapter 11; only this directory mutated.",
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "new_full_abstracts": 0, "new_representative_pdfs": 0, "new_pdf_pages": 0,
    "selected_reading_records": 2, "selected_physical_pages": 17,
    "main_text_pages": 16, "artifact_appendix_pages": 1, "actual_page_images_viewed": 9,
    "records": records, "sources": sources,
    "calculations": proof(P / "calculations.json"), "notes": proof(P / "READINGS.md"),
    "unresolved": [
        "Dynamic co-location changes free VRAM: Medusa sizing-record validity with Dilu is an inference/question, no integrated evaluation exists in these readings.",
        "CUDA Graph launch admission compatibility with Dilu not checked; README link at pinned commit returned 404.",
        "Medusa indirect/device-side pointers and model-spanning-multiple-GPUs are outside implemented scope described by this paper.",
        "Modified PyTorch/SPDK dependency commits not fixed by inspected README; no build/runtime reproduction, no claim about current upstream features.",
        "Only selected pages read, not full papers; Medusa p13 included for artifact dependencies and not counted as another benchmark."
    ]
}
(P / "reading-records.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print("Wrote 2 selected-reading records, 17 pages, 9 viewed pages; new PDFs/abstracts = 0.")
