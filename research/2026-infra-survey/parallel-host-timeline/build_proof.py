"""Self-written archive bookkeeping and teaching arithmetic; no framework imports."""
from pathlib import Path
import datetime
import hashlib
import json

D = Path(__file__).resolve().parent
now = datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def save(name, value):
    (D / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


scopes = {
    "vllm-2024-blog.txt": ([(1, 157)], "Historical mechanisms, evaluation conditions, multi-step output/TTFT limitations; appendix not claimed"),
    "vllm-2025-blog.txt": ([(1, 128)], "V1 architecture, persistent batch, performance conditions and alpha limitations; not a claim of today's async implementation"),
    "sglang-2024-blog.txt": ([(1, 42)], "Date, overview and overlap section only; cache/router/DP sections not reread"),
    "sglang-2026-blog.txt": ([(1, 170)], "DFlash method-to-engine distinction and Spec V2 host overlap; article bytes reused, not a newly read paper"),
    "vllm-060-vllm-engine-llm_engine.py": ([(1480, 1605)], "Remaining-step scheduler bypass, callbacks and end-of-window drain"),
    "vllm-060-vllm-worker-multi_step_model_runner.py": ([(88, 125), (189, 208), (338, 463), (486, 520)], "Ready events, one model step, GPU token advance and blocking finalization"),
    "vllm-080-vllm-v1-engine-core.py": ([(83, 110), (171, 240)], "2025 regular loop and PP batch-queue path"),
    "vllm-current-vllm-v1-core-sched-async_scheduler.py": ([(1, 70)], "Entire small AsyncScheduler class; placeholders and stale output handling"),
    "vllm-current-vllm-v1-engine-core.py": ([(608, 765)], "Current regular/queued loops, worker draft update and deferred structured sampling"),
    "vllm-current-tests-v1-core-test_async_scheduler.py": ([(1, 115), (543, 630)], "Max-token scheduling and selected in-flight preemption regression bodies; source read only, not executed or full helper audit"),
    "sglang-2024-scheduler.py": ([(176, 200), (376, 442), (970, 1020), (1072, 1136)], "Old applicability gate, loop and result/grammar synchronization"),
    "sglang-2024-overlap-worker.py": ([(1, 231)], "Full old worker file; future token IDs, stream/copy readiness and sampling state"),
    "sglang-current-scheduler.py": ([(180, 202), (1588, 1644), (1940, 2085), (4100, 4139), (4172, 4354)], "Current overlap entry, publish and grammar barriers, tensor lifetime, D2H branch; unrelated full scheduler not read"),
    "sglang-current-eagle-worker-v2.py": ([(1, 110), (1188, 1294), (1580, 1608)], "Import/call bridge, target/draft/verify/publish/draft-extend order and shared verify call"),
    "sglang-current-eagle-common.py": ([(461, 671)], "Plan dependencies, target forward, grammar mask, acceptance lengths and state publication result"),
    "sglang-current-overlap-utils.py": ([(1, 54), (78, 126), (248, 315), (513, 596)], "CPU-length need decision, relay entry, buffers and conditional D2H/publish"),
}
reading = []
for name, (ranges, purpose) in scopes.items():
    b = (D / name).read_bytes()
    lines = b.splitlines(keepends=True)
    selected = []
    for start, end in ranges:
        assert 1 <= start <= end <= len(lines), name
        selected.append({"start": start, "end": end, "sha256": sha(b"".join(lines[start - 1:end]))})
    reading.append({"file": name, "sha256": sha(b), "total_lines": len(lines), "ranges": selected, "purpose": purpose})
save("reading.json", {
    "recorded_at": now,
    "method": "Human-selected reads via cat/sed/nl. Keyword search only locates ranges and is not full-file reading. No downloaded code executed.",
    "files": reading,
    "images_viewed": [{"file": n, "sha256": sha((D / n).read_bytes()), "method": "view_image", "scope": "Schematic dependencies only; no timing axis or performance extraction"} for n in ["vllm-multistep.png", "vllm-async-output.png"]],
    "not_read": ["vllm-current-base-scheduler.py copied for possible followup but not read; no credit", "DFlash/NanoFlow paper bodies not newly read", "Whole release histories, unselected source functions and new device traces not audited"],
})

groups = {
    "vllm-060": [
        ("vllm-060-vllm-engine-llm_engine.py", "vllm/engine/llm_engine.py"),
        ("vllm-060-vllm-worker-multi_step_model_runner.py", "vllm/worker/multi_step_model_runner.py"),
    ],
    "vllm-080": [("vllm-080-vllm-v1-engine-core.py", "vllm/v1/engine/core.py")],
    "vllm-current": [
        ("vllm-current-vllm-v1-core-sched-async_scheduler.py", "vllm/v1/core/sched/async_scheduler.py"),
        ("vllm-current-vllm-v1-engine-core.py", "vllm/v1/engine/core.py"),
        ("vllm-current-tests-v1-core-test_async_scheduler.py", "tests/v1/core/test_async_scheduler.py"),
        ("vllm-current-base-scheduler.py", "vllm/v1/core/sched/scheduler.py"),
    ],
    "sglang-2024": [
        ("sglang-2024-scheduler.py", "python/sglang/srt/managers/scheduler.py"),
        ("sglang-2024-overlap-worker.py", "python/sglang/srt/managers/tp_worker_overlap_thread.py"),
    ],
    "sglang-current": [
        ("sglang-current-scheduler.py", "python/sglang/srt/managers/scheduler.py"),
        ("sglang-current-eagle-worker-v2.py", "python/sglang/srt/speculative/eagle_worker_v2.py"),
        ("sglang-current-eagle-common.py", "python/sglang/srt/speculative/eagle_worker_common.py"),
        ("sglang-current-overlap-utils.py", "python/sglang/srt/managers/overlap_utils.py"),
    ],
}
proof = []
for version, files in groups.items():
    commit = json.loads((D / (version + "-commit.json")).read_text())
    tree = json.loads((D / (version + "-root-tree.json")).read_text())
    assert commit["commit"]["tree"]["sha"] == tree["sha"]
    assert tree.get("truncated") is False
    entries = {e["path"]: e for e in tree["tree"]}
    blobs = []
    for local, path in files:
        b = (D / local).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        assert blob == entries[path]["sha"], (local, blob, entries[path]["sha"])
        blobs.append({"file": local, "repository_path": path, "git_blob_sha1": blob, "sha256": sha(b)})
    proof.append({"version": version, "commit_sha": commit["sha"], "committer_date": commit["commit"]["committer"]["date"], "root_tree_sha": tree["sha"], "commit_file": version + "-commit.json", "root_tree_file": version + "-root-tree.json", "blobs": blobs})
save("git-blob-proof.json", {"recorded_at": now, "method": "Official commit metadata to actual root-tree endpoint to raw Git blob SHA-1; commit-SHA tree aliases are not used", "versions": proof})


def event(kind, i, start, end):
    return {"id": kind + str(i), "resource": "GPU" if kind == "G" else "CPU", "start": start, "end": end}


serial = []
for i in range(1, 5):
    t = (i - 1) * 16
    serial.extend([event("P", i, t, t + 4), event("G", i, t + 4, t + 14), event("H", i, t + 14, t + 16)])
multi = [event("P", 1, 0, 4)]
for i in range(1, 5):
    multi.extend([event("G", i, 4 + (i - 1) * 10, 4 + i * 10), event("H", i, 44 + (i - 1) * 2, 44 + i * 2)])
overlap = [event("P", i, a, b) for i, a, b in [(1, 0, 4), (2, 4, 8), (3, 16, 20), (4, 26, 30)]]
for i in range(1, 5):
    overlap.extend([event("G", i, 4 + (i - 1) * 10, 4 + i * 10), event("H", i, 4 + i * 10, 6 + i * 10)])
cases = []
for name, events, expected in [("serial", serial, (24, 40, 64)), ("one_preparation_for_four_steps", multi, (12, 40, 52)), ("overlap_same_cpu_work", overlap, (24, 40, 46))]:
    totals = {r: sum(e["end"] - e["start"] for e in events if e["resource"] == r) for r in ["CPU", "GPU"]}
    done = max(e["end"] for e in events)
    assert (totals["CPU"], totals["GPU"], done) == expected
    cases.append({"name": name, "events": events, "cpu_work": totals["CPU"], "gpu_work": totals["GPU"], "completion": done})
save("timeline-proof.json", {
    "recorded_at": now,
    "unit": "tau, arbitrary teaching time; no conversion to hardware latency",
    "assumptions": ["Four decode iterations after prefill, not four total request output tokens", "Fixed batch; no early EOS; all four iterations required", "GPU token dependencies remain serial", "Device-side input advance included in G", "Overlap permits P(i+1) before H(i), and P+H fits available GPU time", "No resource contention, extra IPC or graph costs", "Multi-step simplification amortizes all P and drains H at end; actual runner still has per-step work"],
    "cases": cases,
    "spec_variant": {"initial_length": "L", "sequence_advances": [3, 1], "final_length": "L+4", "meaning": "Code new_seq_lens increments; not draft acceptance rate or final visible token count"},
})
print(json.dumps({"read_text_files": len(reading), "viewed_images": 2, "git_sources": sum(len(v["blobs"]) for v in proof), "new_http_records": len(json.loads((D / "sources.json").read_text())), "reused_files": len(json.loads((D / "reused-sources.json").read_text()))}))
