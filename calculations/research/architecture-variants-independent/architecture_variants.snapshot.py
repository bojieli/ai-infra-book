"""Chapter 2 near-equal parameter dense architectures, not trained checkpoints."""
from copy import deepcopy
from fractions import Fraction

from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.sources import model_config, provenance
from infra_calc.units import positive_int


MODEL = "qwen3-8b"


def parameter_formula(config):
    h = config["hidden_size"]
    d = config["head_dim"]
    q = config["num_attention_heads"]
    k = config["num_key_value_heads"]
    layers = config["num_hidden_layers"]
    f = config["intermediate_size"]
    vocab = config["vocab_size"]
    return 2 * vocab * h + h + layers * (
        2 * h * q * d + 2 * h * k * d + 3 * h * f + 2 * h + 2 * d
    )


def nearest_aligned(value, alignment):
    """Nearest positive multiple; ties round up, with exact rational arithmetic."""
    result = ((value + alignment / Fraction(2)) // alignment) * alignment
    if result <= 0:
        raise ValueError("Parameter target cannot supply a positive aligned FFN")
    return int(result)


def make_variant(base, target, name, layers, hidden, heads, kv_heads, alignment):
    for key, value in (("layers", layers), ("hidden", hidden), ("heads", heads),
                       ("kv heads", kv_heads), ("alignment", alignment)):
        positive_int(value, key)
    c = deepcopy(base)
    c.update(num_hidden_layers=layers, hidden_size=hidden,
             num_attention_heads=heads, num_key_value_heads=kv_heads,
             intermediate_size=0)
    if hidden != heads * c["head_dim"]:
        raise ValueError("This experiment preserves hidden = query heads * head_dim")
    if heads % kv_heads:
        raise ValueError("GQA query heads must divide into complete KV groups")
    fixed = parameter_formula(c)
    ideal_ffn = Fraction(target - fixed, 3 * layers * hidden)
    c["intermediate_size"] = (base["intermediate_size"] if name == "baseline"
                              else nearest_aligned(ideal_ffn, alignment))
    qwen3.validate(c)
    count = parameter_formula(c)
    tensors = qwen3.weights(c)
    actual = sum(w.parameters for w in tensors)
    if actual != count:
        raise AssertionError("Independent formula and tensor enumeration disagree")
    return c, dict(name=name, config=c, target_parameters=target,
                   ideal_ffn_width_exact=str(ideal_ffn),
                   actual_parameters=count, parameter_delta=count - target,
                   parameter_delta_fraction_exact=str(Fraction(count - target, target)),
                   max_rounding_error_parameters_exact=str(Fraction(3 * layers * hidden * alignment, 2)),
                   exact_equal_parameters=count == target)


def evaluate(config, scenario, tp, workspace_bytes, capacity_bytes):
    h = config["hidden_size"]
    layers = config["num_hidden_layers"]
    d = config["head_dim"]
    q = config["num_attention_heads"]
    k = config["num_key_value_heads"]
    f = config["intermediate_size"]
    vocab = config["vocab_size"]
    # Restrict this comparison to complete heads and no KV duplication.
    if any(x % tp for x in (q, k, f, vocab)):
        raise ValueError("Declared TP needs divisible Q/KV heads, FFN and vocabulary; no KV replication fallback")
    ops = qwen3.build_operators(config, scenario)
    records = [op.record() for op in ops]
    parameters = parameter_formula(config)
    norms = layers * (2 * h + 2 * d) + h
    per_rank_weights = 2 * ((parameters - norms) // tp + norms)
    state_per_token = 2 * layers * k * d * 2
    retained = scenario.history + scenario.tokens
    kv_per_request_per_rank = state_per_token * retained // tp
    # Two attention/MLP row-parallel output all-reduces per layer.
    collective_payload = scenario.rows * h * 2
    ring_per_collective = Fraction(2 * (tp - 1), tp) * collective_payload
    collectives = 2 * layers if tp > 1 else 0
    rank_wire = collectives * ring_per_collective
    available = capacity_bytes - per_rank_weights - workspace_bytes
    concurrency = max(0, available // kv_per_request_per_rank)
    return dict(
        matrix_flops=sum(op.matrix_flops * op.repeats for op in ops),
        scalar_flops=sum(op.scalar_flops * op.repeats for op in ops),
        operators=records,
        all_unique_weight_bytes=2 * parameters,
        per_rank_weight_bytes=per_rank_weights,
        aggregate_tp_weight_bytes=tp * per_rank_weights,
        norm_replication_extra_bytes=2 * (tp - 1) * norms,
        kv_bytes_per_token_per_request=state_per_token,
        per_rank_kv_bytes=scenario.batch * kv_per_request_per_rank,
        per_rank_old_history_read_bytes=scenario.batch * scenario.history * state_per_token // tp,
        per_rank_kv_append_bytes=scenario.batch * scenario.tokens * state_per_token // tp,
        per_rank_new_kv_request_bytes=kv_per_request_per_rank,
        per_rank_workspace_reserved_bytes=workspace_bytes,
        per_rank_live_budget_bytes=per_rank_weights + scenario.batch * kv_per_request_per_rank + workspace_bytes,
        per_rank_capacity_bytes=capacity_bytes,
        max_equal_length_requests=concurrency,
        batch_fits=scenario.batch <= concurrency,
        sequential_decoder_layers=layers,
        sequential_collectives=collectives,
        per_collective_activation_payload_bytes=collective_payload,
        per_rank_ring_wire_bytes_exact=str(rank_wire),
        collective_scope="TP attention-output and FFN-down all-reduces only; no embedding/head communication or overlap claim",
    )


def calculate(batch=1, history=8192, tokens=1, tp=2,
              capacity_bytes=24 * 10**9, workspace_bytes=2 * 2**30,
              ffn_alignment=128):
    for key, value in (("tp", tp), ("capacity", capacity_bytes),
                       ("alignment", ffn_alignment)):
        positive_int(value, key)
    positive_int(workspace_bytes, "workspace", allow_zero=True)
    scenario = Scenario(batch=batch, history=history, tokens=tokens)
    base = model_config(MODEL)
    target = parameter_formula(base)
    candidates = [
        ("baseline", 36, 4096, 32, 8),
        ("shallower_same_width", 24, 4096, 32, 8),
        ("deeper_same_width", 48, 4096, 32, 8),
        ("narrower_same_depth", 36, 3072, 24, 6),
        ("shallower_wider", 24, 5120, 40, 8),
        ("exact_budget_less_kv_more_ffn", 36, 4096, 32, 2),
    ]
    rows = []
    for name, layers, hidden, heads, kv_heads in candidates:
        c, row = make_variant(base, target, name, layers, hidden, heads, kv_heads, ffn_alignment)
        row["work"] = evaluate(c, scenario, tp, workspace_bytes, capacity_bytes)
        rows.append(row)
    comparisons = []
    baseline = rows[0]["work"]
    for row in rows[1:]:
        work = row["work"]
        comparisons.append(dict(
            variant=row["name"],
            matrix_flops_delta=work["matrix_flops"] - baseline["matrix_flops"],
            per_rank_weights_delta=work["per_rank_weight_bytes"] - baseline["per_rank_weight_bytes"],
            per_rank_kv_delta=work["per_rank_kv_bytes"] - baseline["per_rank_kv_bytes"],
            per_rank_live_budget_delta=work["per_rank_live_budget_bytes"] - baseline["per_rank_live_budget_bytes"],
            capacity_interval_where_only_smaller_fits_bytes=[
                min(work["per_rank_live_budget_bytes"], baseline["per_rank_live_budget_bytes"]),
                max(work["per_rank_live_budget_bytes"], baseline["per_rank_live_budget_bytes"]) - 1,
            ] if work["per_rank_live_budget_bytes"] != baseline["per_rank_live_budget_bytes"] else None,
            per_rank_ring_wire_delta_exact=str(Fraction(work["per_rank_ring_wire_bytes_exact"]) - Fraction(baseline["per_rank_ring_wire_bytes_exact"])),
            sequential_collectives_delta=work["sequential_collectives"] - baseline["sequential_collectives"],
            sequential_layers_delta=work["sequential_decoder_layers"] - baseline["sequential_decoder_layers"],
        ))
    return dict(schema_version=1, calculation="architecture-variants", baseline_model=MODEL,
                scenario=dict(batch=batch, history=history, tokens=tokens, tp=tp,
                              capacity_bytes=capacity_bytes, workspace_bytes=workspace_bytes,
                              ffn_alignment=ffn_alignment),
                sources=provenance(MODEL), variants=rows, comparisons=comparisons,
                assumptions=[
                    "Only baseline is a released checkpoint. Variants are declared untrained architectures; no equal quality or numerical equivalence is asserted.",
                    "Untied embedding/head, no biases, fixed head_dim=128, vocabulary/context and Q/K norms retained from official Qwen3-8B config.",
                    "FFN is nearest positive aligned solution to the same parameter target; exact signed error and half-grid bound are reported. A reduced-KV variant conserves parameters exactly.",
                    "FMA=2, effective causal attention and source logical scalar counts. Operator reads/writes are semantic operands, not measured HBM.",
                    "BF16 weights/activations/KV; score and scalar intermediate precision remains Scenario contract. No low-bit checkpoint claim.",
                    "TP uses complete divisible KV heads; normalization parameters replicate. Uniform equal-length requests, no prefix sharing, no PP/EP. Workspace is a fixed per-rank input budget, not a derived peak.",
                    "Ring bytes and sequential collectives quantify only two decoder collectives per layer. For that subpath declared service is bytes/effective_link_rate + collectives/startup_rate; no hardware rates are invented or whole-request latency inferred.",
                    "Capacity flip interval is inclusive and applies to the declared batch and workspace. Matrix FLOPs, serial depth and communication changes cannot establish a quality-constrained winner alone.",
                ])
