"""Read-only K3 source/header reconciliation; no tensor payload downloads."""

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from infra_calc.sources import model_config, records, read_source
from infra_calc.topics import k3_checkpoint, k3_kda

c = model_config("kimi-k3")["text_config"]
linear = c["linear_attn_config"]
heads, dim = linear["num_heads"], linear["head_dim"]
index = json.loads(read_source("sources/kimi-k3/model.safetensors.index.json"))
headers = {}
all_names = set()
rows = []
for shard in sorted(set(index["weight_map"].values())):
    header = json.loads(read_source(f"sources/kimi-k3/headers/{shard}.json"))
    for name, tensor in header.items():
        if name == "__metadata__":
            continue
        assert name not in all_names and index["weight_map"][name] == shard
        all_names.add(name)
        if ".self_attn." in name:
            headers[name] = (shard, tensor)
assert all_names == set(index["weight_map"])
for layer1 in linear["kda_layers"]:
    layer = layer1 - 1
    prefix = f"language_model.model.layers.{layer}.self_attn."
    shard, a = headers[prefix + "A_log"]
    peers = {
        key: headers[prefix + key][1]["shape"]
        for key in (
            "q_proj.weight",
            "k_proj.weight",
            "v_proj.weight",
            "b_proj.weight",
            "f_b_proj.weight",
            "g_proj.weight",
            "o_proj.weight",
            "dt_bias",
        )
    }
    assert a["shape"] == [128] and a["dtype"] == "F32"
    assert all(
        peers[key] == [heads * dim, c["hidden_size"]]
        for key in ("q_proj.weight", "k_proj.weight", "v_proj.weight", "g_proj.weight")
    )
    assert peers["b_proj.weight"] == [heads, c["hidden_size"]]
    assert peers["f_b_proj.weight"] == [heads * dim, dim]
    assert peers["o_proj.weight"] == [c["hidden_size"], heads * dim]
    assert peers["dt_bias"] == [heads * dim]
    rows.append(
        dict(
            layer_zero_based=layer,
            tensor=prefix + "A_log",
            shard=shard,
            config_shape=[heads],
            checkpoint=a,
            peer_shapes=peers,
            extra_elements=128 - heads,
            extra_fp32_payload_bytes=4 * (128 - heads),
        )
    )
result = k3_checkpoint.calculate()
assert len(rows) == 69 == len(result["config_shape_mismatches"])
assert (
    result["text_parameter_delta_from_config"]
    == sum(r["extra_elements"] for r in rows)
    == 2208
)
assert {r["tensor"] for r in rows} == {
    r["tensor"] for r in result["config_shape_mismatches"]
}
state = k3_kda.calculate()["summary"]
assert state["recurrent_state_fp32_bytes"] == 69 * 96 * 128 * 128 * 4
api_check = json.loads(
    (PROJECT / "research/f02-final-review/kimi-recheck.json").read_text()
)
api_data = (PROJECT / api_check["file"]).read_bytes()
assert (
    hashlib.sha256(api_data).hexdigest() == api_check["sha256"]
    and len(api_data) == api_check["bytes"]
)
assert (
    json.loads(api_data)["sha"]
    == api_check["locked_revision"]
    == api_check["current_revision"]
)
checks = dict(
    config_heads=heads,
    channel_dimension=dim,
    projected_width=heads * dim,
    kda_layers=69,
    checkpoint_alog_elements=69 * 128,
    config_alog_elements=69 * 96,
    checkpoint_extra_parameters=2208,
    checkpoint_extra_fp32_bytes=8832,
    one_batch_all_kda_recurrent_state_bytes=state["recurrent_state_fp32_bytes"],
    all_index_names_verified=len(all_names),
    all_shards_verified=len(set(index["weight_map"].values())),
    public_checkpoint=result,
    layer_evidence=rows,
    existing_same_day_official_api_check=api_check,
)
(HERE / "reconciliation.json").write_text(json.dumps(checks, indent=2) + "\n")
source_rows = [
    r
    for r in records()
    if r.get("model") in ("kimi-k3", "flash-linear-attention")
    and r.get("status") == "downloaded"
]
for row in source_rows:
    read_source(row["file"])
local_files = [
    "src/infra_calc/topics/k3_checkpoint.py",
    "src/infra_calc/topics/k3_kda.py",
    "src/infra_calc/topics/k3_forward.py",
    "src/infra_calc/topics/kda_chunk.py",
    "PLAN.md",
    "research/f02-final-review/kimi-current-api.json",
    "research/f02-final-review/kimi-recheck.json",
]
bindings = [
    dict(file=p, sha256=hashlib.sha256((PROJECT / p).read_bytes()).hexdigest())
    for p in local_files
]
(HERE / "source-bindings.json").write_text(
    json.dumps(dict(public_sources=source_rows, local_files=bindings), indent=2) + "\n"
)
print(
    json.dumps(
        {
            k: v
            for k, v in checks.items()
            if k not in ("public_checkpoint", "layer_evidence")
        },
        indent=2,
    )
)
