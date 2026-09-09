"""Verify local evidence and self-written timeline only. No network/framework execution."""
from pathlib import Path
import datetime
import hashlib
import json

D = Path(__file__).resolve().parent


def read(name):
    return json.loads((D / name).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


for manifest in ("sources.json", "reused-sources.json"):
    for row in read(manifest):
        b = (D / row["file"]).read_bytes()
        assert len(b) == row["bytes"] and sha(b) == row["sha256"], row["file"]
        if manifest == "sources.json":
            assert row["status"] == 200

reading = read("reading.json")
for row in reading["files"]:
    b = (D / row["file"]).read_bytes()
    assert sha(b) == row["sha256"]
    lines = b.splitlines(keepends=True)
    assert len(lines) == row["total_lines"]
    for span in row["ranges"]:
        assert 1 <= span["start"] <= span["end"] <= len(lines)
        assert sha(b"".join(lines[span["start"] - 1:span["end"]])) == span["sha256"]
for row in reading["images_viewed"]:
    assert sha((D / row["file"]).read_bytes()) == row["sha256"]

proof = read("git-blob-proof.json")
for version in proof["versions"]:
    commit = read(version["commit_file"])
    tree = read(version["root_tree_file"])
    assert commit["sha"] == version["commit_sha"]
    assert commit["commit"]["tree"]["sha"] == tree["sha"] == version["root_tree_sha"]
    assert tree.get("truncated") is False
    entries = {e["path"]: e for e in tree["tree"]}
    for row in version["blobs"]:
        b = (D / row["file"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        assert blob == row["git_blob_sha1"] == entries[row["repository_path"]]["sha"]
        assert sha(b) == row["sha256"]

timeline = read("timeline-proof.json")
for case in timeline["cases"]:
    events = case["events"]
    by_id = {e["id"]: e for e in events}
    for resource, key in (("CPU", "cpu_work"), ("GPU", "gpu_work")):
        on_resource = sorted((e for e in events if e["resource"] == resource), key=lambda e: e["start"])
        assert all(e["end"] > e["start"] for e in on_resource)
        assert all(a["end"] <= b["start"] for a, b in zip(on_resource, on_resource[1:]))
        assert sum(e["end"] - e["start"] for e in on_resource) == case[key]
    for i in range(1, 5):
        assert by_id[f"G{i}"]["end"] <= by_id[f"H{i}"]["start"]
        prepare = by_id["P1"] if case["name"] == "one_preparation_for_four_steps" else by_id[f"P{i}"]
        assert prepare["end"] <= by_id[f"G{i}"]["start"]
        if i > 1:
            assert by_id[f"G{i-1}"]["end"] <= by_id[f"G{i}"]["start"]
        if case["name"] == "serial" and i > 1:
            assert by_id[f"H{i-1}"]["end"] <= by_id[f"P{i}"]["start"]
    assert max(e["end"] for e in events) == case["completion"]
assert [(c["cpu_work"], c["gpu_work"], c["completion"]) for c in timeline["cases"]] == [(24, 40, 64), (12, 40, 52), (24, 40, 46)]
assert sum(timeline["spec_variant"]["sequence_advances"]) == 4

report = {"verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS", "new_http_records": len(read("sources.json")), "reused_files": len(read("reused-sources.json")), "selected_text_files": len(reading["files"]), "viewed_images": len(reading["images_viewed"]), "git_blobs": sum(len(v["blobs"]) for v in proof["versions"]), "timeline_cpu_gpu_completion": [[c["cpu_work"], c["gpu_work"], c["completion"]] for c in timeline["cases"]], "framework_tests_run": False, "network_used_by_verifier": False}
(D / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
