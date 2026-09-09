"""Check archived bytes, explicit reading scope and independent matrix accounting."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "references/framework-history/2026-09-09/partir-shardy"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    inventory = json.loads((BASE / "inventory.json").read_text())
    sources = json.loads((BASE / "sources.json").read_text())
    for item in inventory["files"] + sources:
        data = (BASE / item["file"]).read_bytes()
        assert len(data) == item["bytes"] and sha(data) == item["sha256"], item["file"]
    reading = json.loads((BASE / "reading.json").read_text())
    pdf = BASE / reading["pdf"]["file"]
    assert pdf.read_bytes() == (ROOT / "references/proceedings/ASPLOS/2025/pending-077-110/077-090/paper-080.pdf").read_bytes()
    for item in reading["pages"]:
        page = str(item["physical_page"])
        data = subprocess.check_output(["pdftotext", "-layout", "-f", page, "-l", page, str(pdf), "-"], stderr=subprocess.PIPE)
        assert data == (BASE / item["file"]).read_bytes() + b"\f", page
    for item in reading["sources"]:
        data = (BASE / item["file"]).read_bytes()
        assert sha(data) == item["sha256"]
        lines = data.splitlines(keepends=True)
        if item["read_scope"] == "complete":
            assert item["first_line"] == 1 and item["last_line"] == len(lines)
        else:
            assert sha(b"".join(lines[item["first_line"] - 1:item["last_line"]])) == item["range_sha256"]
    commit = json.loads((BASE / "shardy-commit.json").read_text())
    assert commit["sha"] == "a72dc82ce730c55be36a409945f4224181d050fc"
    # Paper's intentionally tiny forward-only chain, not a real GPU timing test.
    batch, hidden, intermediate, dp, tp, elem = 256, 8, 16, 4, 2, 4
    local_batch, local_intermediate = batch // dp, intermediate // tp
    global_flops = 2 * batch * hidden * intermediate * 2
    local_flops = 2 * local_batch * hidden * local_intermediate * 2
    dp_weight_bytes = 2 * hidden * intermediate * elem
    tp_weight_bytes = dp_weight_bytes // tp
    fsdp_weight_bytes = tp_weight_bytes // dp
    output_bytes = local_batch * hidden * elem
    ring_ar_sent = 2 * (tp - 1) * output_bytes // tp
    weight_gather_received = (dp - 1) * tp_weight_bytes // dp
    assert (global_flops, local_flops) == (131072, 16384)
    assert (dp_weight_bytes, tp_weight_bytes, fsdp_weight_bytes) == (1024, 512, 128)
    assert ring_ar_sent == 2048 and weight_gather_received == 384
    from verify_partir_expanded import verify as verify_expanded
    expanded = verify_expanded()
    result = {
        "supplemental_reading": expanded,
        "status": "passed",
        "archived_files": len(inventory["files"]),
        "source_responses": len(sources),
        "selected_pages": [3, 4, 5],
        "viewed_pages": [3, 5],
        "source_scopes": len(reading["sources"]),
        "canonical_proceedings_count_changed": False,
        "arithmetic": {
            "scope": "FP32 forward-only paper shapes, payload-only conventional ring assumption; no latency, allocator peak, backward or optimizer estimate.",
            "global_flops": global_flops,
            "per_rank_dp_tp_flops": local_flops,
            "per_rank_weight_bytes_dp_tp_fsdp": [dp_weight_bytes, tp_weight_bytes, fsdp_weight_bytes],
            "tp_output_logical_bytes": output_bytes,
            "tp_allreduce_per_rank_sent_bytes": ring_ar_sent,
            "tp_allreduce_per_rank_received_bytes": ring_ar_sent,
            "two_fsdp_allgathers_per_rank_received_bytes": weight_gather_received,
            "two_fsdp_allgathers_per_rank_sent_bytes": weight_gather_received,
        },
        "execution": "Own arithmetic and Poppler extraction only; downloaded source/test code not executed.",
    }
    (BASE / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
