"""Verify pinned originals and logical Llama weights without loading weights."""
import hashlib
import json
import math
from pathlib import Path


def audit():
    directory = Path(__file__).resolve().parent
    project = directory.parents[1]
    for source in json.loads((directory / "manifest.json").read_text()):
        raw = (project / source["file"]).read_bytes()
        assert len(raw) == source["bytes"], source["file"]
        assert hashlib.sha256(raw).hexdigest() == source["sha256"], source["file"]
    config = json.loads((directory / "config.json").read_text())
    index = json.loads((directory / "model.safetensors.index.json").read_text())
    assert config["model_type"] == "llama"
    assert not config["attention_bias"] and not config["mlp_bias"]
    assert not config["tie_word_embeddings"]
    h = config["hidden_size"]
    f = config["intermediate_size"]
    layers = config["num_hidden_layers"]
    q = config["num_attention_heads"] * config["head_dim"]
    kv = config["num_key_value_heads"] * config["head_dim"]
    vocab = config["vocab_size"]
    # Framework storage shapes, not mathematical right-multiply orientation.
    shapes = {
        "self_attn.q_proj": [q, h],
        "self_attn.k_proj": [kv, h],
        "self_attn.v_proj": [kv, h],
        "self_attn.o_proj": [h, q],
        "mlp.gate_proj": [f, h],
        "mlp.up_proj": [f, h],
        "mlp.down_proj": [h, f],
        "input_layernorm": [h],
        "post_attention_layernorm": [h],
    }
    names = {"model.embed_tokens.weight", "model.norm.weight", "lm_head.weight"}
    names.update(f"model.layers.{layer}.{name}.weight"
                 for layer in range(layers) for name in shapes)
    assert names == set(index["weight_map"])
    parameters = 2 * vocab * h + h + layers * sum(map(math.prod, shapes.values()))
    result = {
        "config_derived_parameters": parameters,
        "nominal_bf16_parameter_bytes": 2 * parameters,
        "index_reported_total_size": index["metadata"]["total_size"],
        "tensor_names": len(names),
        "shards": len(set(index["weight_map"].values())),
        "layer_weights": shapes,
        "scope": "Logical config shapes and index names only; no tensor header, dtype or runtime verification.",
    }
    previous = json.loads((directory / "input-review.json").read_text())
    for key, value in result.items():
        if key != "scope":
            assert previous[key] == value, key
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
