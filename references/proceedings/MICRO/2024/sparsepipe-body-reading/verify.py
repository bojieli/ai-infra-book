"""Offline evidence checks and independent exact arithmetic; no third-party code."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess

D = Path(__file__).resolve().parent


def load(f):
    return json.loads((D / f).read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


for rows in [load("sources.json"), load("reused-sources.json")]:
    for row in rows:
        raw = (D / row["file"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
pdf = D / "paper.pdf"
assert sha(pdf.read_bytes()) == "6cfd5a598c798c573fcc7b015b0ea0702aaafda8067234846eafd754f4b361bf"
assert pdf.read_bytes().startswith(b"%PDF")
assert int(re.search(r"^Pages:\s+(\d+)", subprocess.check_output(["pdfinfo", str(pdf)], text=True), re.M).group(1)) == 16
text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
assert text == (D / "paper-layout.txt").read_text()
pages = text.split("\f")
assert len(pages) == 17 and not pages[-1].strip()
for n, page in enumerate(pages[:-1], 1):
    assert page == (D / f"page-{n:02d}.txt").read_text()
for side, x in [("left", 0), ("right", 306)]:
    regenerated = subprocess.check_output(["pdftotext", "-f", "14", "-l", "14", "-x", str(x), "-y", "0", "-W", "306", "-H", "792", str(pdf), "-"], text=True)
    assert regenerated == (D / f"page-14-{side}.txt").read_text()

reading = load("reading.json")
assert reading["identity"]["paper_sha256"] == sha(pdf.read_bytes())
prior = next(p for p in load("input-abstracts.json")["papers"] if p["program_order"] == 88)
assert prior["doi"] == reading["identity"]["doi"]
assert prior["source_sha256"] == reading["identity"]["paper_sha256"]
assert reading["full_page_text_pages"] == list(range(3, 14))
assert reading["partial_page_text_pages"] == [14]
assert reading["new_network_requests"] == reading["source_code_files_read"] == reading["new_full_abstracts_read"] == 0
assert reading["downloaded_code_executed"] is False
for item in reading["text_scopes"]:
    raw = (D / item["file"]).read_bytes()
    assert sha(raw) == item["sha256"]
    a, z = item["char_range"]
    assert 0 <= a < z <= len(raw.decode())
assert [i["physical_page"] for i in reading["images_actually_viewed"]] == [3, 4, 5, 6, 8, 10, 11, 12]
for image in reading["images_actually_viewed"]:
    assert image["actually_viewed"] is True
    assert sha((D / image["file"]).read_bytes()) == image["sha256"]
assert sha((D / "NOTES.md").read_bytes()) == reading["notes_sha256"]
assert sha((D / "byte-example.json").read_bytes()) == reading["byte_example_sha256"]
assert "9329007" in pages[4] and "90%" in pages[4]
assert "total of 10 applications" in pages[9]
assert "gmres" in pages[9] and "cg" in pages[9] and "bgs" in pages[9]
assert "future work" in (D / "page-14-right.txt").read_text()

# Compute the reference output independently using the explicit sparse entries.
e = load("byte-example.json")
matrix = e["matrix"]
n = len(matrix)
nnz = sum(x != 0 for row in matrix for x in row)
def multiply(v):
    result = [0] * n
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            result[j] += v[i] * value
    return result
y = multiply(e["u"])
v = [x + 1 for x in y]
z = multiply(v)
assert (y, v, z) == (e["y"], e["v"], e["z"])
value_b, coord_b, pointer_b = e["value_bytes"], e["coordinate_bytes"], e["pointer_bytes"]
matrix_b = nnz * (value_b + coord_b)
pointer_io = 2 * (n + 1) * pointer_b
io = 2 * n * value_b
intermediate = 4 * n * value_b
assert [p["total_bytes"] for p in e["cases"]] == [2 * matrix_b + pointer_io + io + intermediate, 2 * matrix_b + pointer_io + io, matrix_b + pointer_io + io] == [376, 248, 176]
for case in e["cases"]:
    assert case["total_bytes"] == sum(case[k] for k in ["matrix_record_io", "pointer_io", "input_output_io", "intermediate_io"])
assert e["producer_consumer_saved_bytes"] == intermediate == 128
assert e["additional_cross_iteration_saved_bytes"] == matrix_b == 72
seen = set()
ready = set()
accum = [0] * n
loaded = set()
for step in e["dependency_trace"]:
    ready.add(step["column"])
    loaded.update(tuple(k) for k in step["loaded_coordinates"])
    for i, j in step["IS_consumed_coordinates"]:
        assert i in ready and (i, j) in loaded and (i, j) not in seen
        seen.add((i, j))
        accum[j] += v[i] * matrix[i][j]
    assert accum == step["partial_z_after_step"]
assert len(seen) == nnz and accum == z

report = {"verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS", "paper_physical_pages": 16, "full_page_text_read_pages": list(range(3, 14)), "partial_page_text_read_pages": [14], "images_actually_viewed": 8, "new_http_requests": 0, "new_full_abstracts": 0, "source_code_files_read": 0, "downloaded_code_executed": False, "example_bytes": [376, 248, 176], "example_savings_bytes": [128, 72], "example_output": z, "verification_boundary": "Original bytes, identity, extracted text/ranges, recorded visual checks, and independent arithmetic/dependency witness. Does not validate simulator timing, artifact implementation or measured performance claims."}
(D / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
