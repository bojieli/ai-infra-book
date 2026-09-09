"""Independent public-forward checkpoints and closed-form request sums."""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from infra_calc.models import qwen3
from infra_calc.schema import Scenario
from infra_calc.sources import model_config
from infra_calc.topics import k3_forward, state, v4_forward

HERE = Path(__file__).resolve().parent
TARGET = ROOT / "research/request-model-comparison/src/infra_calc/topics/request_model_comparison.py"
spec = importlib.util.spec_from_file_location("request_candidate", TARGET)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
checks = []


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)


def totals(result):
    s = result["summary"]
    return (s.get("matrix_flops", s.get("matrix_flops_effective_attention")),
            s.get("scalar_flops", s.get("accounted_scalar_flops")),
            Counter(s.get("special_ops", s.get("accounted_special_ops", {}))))


def forward(model, batch, tokens, history, path="expanded"):
    if model == "qwen3-8b":
        return qwen3.calculate(model, Scenario(batch=batch, tokens=tokens, history=history))
    if model == "kimi-k3":
        return k3_forward.calculate(batch=batch, tokens=tokens, history=history, mla_path=path)
    return v4_forward.calculate(model, batch=batch, tokens=tokens, history=history)


def floor_sum(n, divisor):
    """Sum floor(i/divisor), i=0..n, from quotient blocks, no token loop."""
    if n < 0:
        return 0
    q, r = divmod(n, divisor)
    return divisor * q * (q - 1) // 2 + q * (r + 1)


def capped_floor_sum(n, divisor, cap):
    stop = min(n, divisor * cap - 1)
    return floor_sum(stop, divisor) + max(0, n - stop) * cap


def window_sum(n, window):
    stop = min(n, window)
    return stop * (stop + 1) // 2 + max(0, n - window) * window


def v4_dynamic_sum(config, first_end, last_end, batch):
    """Full interval QK/PV and index GEMMs using closed floor/window sums."""
    result = 0
    counts = Counter(config["compress_ratios"][:config["n_layers"]])
    for ratio, layers in counts.items():
        selected = window_sum(last_end, config["window_size"]) - window_sum(first_end - 1, config["window_size"])
        if ratio == 4:
            selected += capped_floor_sum(last_end, 4, config["index_topk"]) - capped_floor_sum(first_end - 1, 4, config["index_topk"])
            index_columns = floor_sum(last_end, 4) - floor_sum(first_end - 1, 4)
            result += 2 * layers * batch * config["index_n_heads"] * config["index_head_dim"] * index_columns
        elif ratio:
            selected += floor_sum(last_end, ratio) - floor_sum(first_end - 1, ratio)
        result += 4 * layers * batch * config["n_heads"] * config["head_dim"] * selected
    return result


# Inspect every short decode against an independent full public forward;
# also inspect V4 input continuation, which must execute and charge each head.
short = candidate.calculate(prefix_tokens=125, new_tokens=3, output_tokens=3, batch=2)
check([r["model"] for r in short["comparisons"]] == ["qwen3-8b", "deepseek-v4-flash", "deepseek-v4-pro", "kimi-k3"], "original four model identities")
check(short["contract"]["decode_forward_calls"] == 2 and short["contract"]["final_retained_positions"] == 130, "D=G-1 and final retention")
for entry in short["comparisons"]:
    model = entry["model"]
    phases = [entry["decode"]]
    if model.startswith("deepseek-v4"):
        phases.append(entry["prefill"])
        check(entry["prefill"]["calls"] == 3 and "sequential" in entry["prefill"]["schedule"], model + " prefix serial schedule")
        check(entry["prefill"]["source_ledger"]["summary"]["vocabulary_head_calls"] == 3, model + " discarded prefix heads charged")
    for phase in phases:
        for row in phase["rows"]:
            direct = forward(model, 2, 1, row["input_position"])
            matrix, scalar, special = totals(direct)
            check((row["matrix_flops"], row["accounted_scalar_flops"], Counter(row["special_ops"])) == (matrix, scalar, special), f"{model} position{row['input_position']} complete public arithmetic")
            expected_state = state.calculate(model, row["input_position"] + 1, 2, mla_path="expanded")["summary"]["resident_bytes"]
            check(row["state_resident_after_bytes"] == expected_state, f"{model} position{row['input_position']} state")
    check(entry["summary"]["state_growth_over_restored_prefix_bytes"] == entry["summary"]["final_state_resident_bytes"] - state.calculate(model, 125, 2, mla_path="expanded")["summary"]["resident_bytes"], model + " restored growth")
    check(entry["summary"]["matrix_flops"] == entry["prefill"]["totals"]["matrix_flops"] + entry["decode"]["totals"]["matrix_flops"], model + " request sum")

cold = candidate.calculate(new_tokens=1, output_tokens=1)
for entry in cold["comparisons"]:
    check(entry["decode"]["calls"] == 0 and entry["decode"]["totals"]["matrix_flops"] == 0, entry["model"] + " G1 zero decode")
    check(entry["summary"]["full_forward_calls"] == 1, entry["model"] + " G1 one input head")
    check(entry["summary"]["final_state_resident_bytes"] == entry["prefill"]["final_state_resident_bytes"], entry["model"] + " G1 state")
k3 = short["comparisons"][-1]
check(k3["source_coverage"]["config_checkpoint_shape_match"] is False and any("A_log" in value for value in k3["source_coverage"]["missing"]), "K3 A_log conflict survives aggregation")

# Long affine sum: independently evaluate endpoint forwards and a midpoint,
# then use D*(first+last)/2 rather than the candidate's step-generation loop.
for model, path in [("qwen3-8b", "expanded"), ("kimi-k3", "expanded"), ("kimi-k3", "compact")]:
    history, count, batch = 111, 257, 2
    result = candidate.linear_decode(model, batch, history, count, path, "balanced")
    first = forward(model, batch, 1, history, path)
    middle = forward(model, batch, 1, history + 128, path)
    last = forward(model, batch, 1, history + count - 1, path)
    a, mid, z = totals(first), totals(middle), totals(last)
    for index, key in [(0, "matrix_flops"), (1, "accounted_scalar_flops")]:
        check(a[index] + z[index] == 2 * mid[index], model + path + " affine midpoint " + key)
        check(result["totals"][key] == count * (a[index] + z[index]) // 2, model + path + " closed long " + key)
    for key in set(a[2]) | set(z[2]):
        check(result["totals"]["special_ops"].get(key, 0) == count * (a[2][key] + z[2][key]) // 2, model + path + " closed special " + key)
    check(result["final_state_resident_bytes"] == last["summary"].get("state_resident_after_bytes", last["summary"].get("kv_resident_after_bytes")), model + path + " long endpoint state")

# V4 crosses both window and ratio boundaries; use quotient-block sums.
for model in ("deepseek-v4-flash", "deepseek-v4-pro"):
    history, count, batch = 1019, 261, 2
    result = candidate.sequential_v4(model, batch, history, count, "balanced", history + count)
    config = model_config(model, reference=True)
    first = forward(model, batch, 1, history)
    constant = totals(first)[0] - v4_dynamic_sum(config, history + 1, history + 1, batch)
    expected = count * constant + v4_dynamic_sum(config, history + 1, history + count, batch)
    check(result["totals"]["matrix_flops"] == expected, model + " closed floor/window matrix sum")
    check(result["source_ledger"]["summary"]["vocabulary_head_calls"] == count, model + " long head count")

# The backward finite difference must never query Qwen beyond its limit.
limit = model_config("qwen3-8b")["max_position_embeddings"]
edge = candidate.linear_decode("qwen3-8b", 1, limit - 1, 1, "expanded", "balanced")
check(edge["rows"][0]["input_position"] == limit - 1, "Qwen last legal decode position")
try:
    candidate.calculate(new_tokens=limit, output_tokens=2)
except ValueError:
    checks.append("Qwen shared context overflow rejected")
else:
    raise AssertionError("Qwen overflow accepted")

(HERE / "results.json").write_text(json.dumps(dict(module_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(), checks=checks, count=len(checks)), indent=2) + "\n")
print(f"PASS {len(checks)} independent checks")
