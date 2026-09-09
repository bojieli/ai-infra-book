import hashlib
import json
import sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from infra_calc import topics

topics.__path__.insert(
    0, str(PROJECT / "research/v4-moe-training/public/src/infra_calc/topics")
)
from infra_calc.topics import v4_moe_training as m

checks = 0
errors = []


def check(ok, label):
    global checks
    checks += 1
    if not ok:
        raise AssertionError(label)


def close(actual, expected, label):
    actual = torch.as_tensor(actual, dtype=torch.float64)
    expected = torch.as_tensor(expected, dtype=torch.float64)
    errors.append((actual - expected).abs().max().item())
    check(torch.allclose(actual, expected, rtol=2e-12, atol=2e-12), label)


for rows, limit in ((2, 10.0), (3, 0.06), (5, 0.3)):
    torch.manual_seed(331 + rows)
    h, f, e, k = 4, 3, 4, 2

    def t(*shape):
        return (torch.randn(*shape, dtype=torch.float64) * 0.3).requires_grad_()

    x = t(rows, h)
    gate = t(e, h)
    expert = [{"w1": t(f, h), "w3": t(f, h), "w2": t(h, f)} for _ in range(e)]
    shared = {"w1": t(f, h), "w3": t(f, h), "w2": t(h, f)}
    ids = torch.tensor([[(i + j) % 3 for j in (0, 1)] for i in range(rows)])
    upstream = torch.randn(rows, h, dtype=torch.float64)
    logits = x @ gate.T
    scores = torch.nn.functional.softplus(logits).sqrt()
    selected = scores.gather(1, ids)
    route = 1.5 * selected / selected.sum(1, keepdim=True)

    def expert_forward(weight, row, scale=None):
        g = (row @ weight["w1"].T).clamp(max=limit)
        u = (row @ weight["w3"].T).clamp(-limit, limit)
        z = torch.nn.functional.silu(g) * u
        return (z if scale is None else z * scale) @ weight["w2"].T

    out = expert_forward(shared, x)
    for token in range(rows):
        for slot in range(k):
            selection = torch.nn.functional.one_hot(torch.tensor(token), rows).to(
                torch.float64
            )[:, None]
            out = out + selection * expert_forward(
                expert[ids[token, slot]], x[token], route[token, slot]
            )
    (out * upstream).sum().backward()
    listed = lambda w: {key: value.detach().tolist() for key, value in w.items()}
    refs = [
        m.reference(
            x[i].detach().tolist(),
            gate.detach().tolist(),
            [listed(w) for w in expert],
            listed(shared),
            ids[i].tolist(),
            upstream[i].tolist(),
            limit=limit,
        )
        for i in range(rows)
    ]
    close([r["output"] for r in refs], out.detach(), "outputs")
    close([r["dx"] for r in refs], x.grad, "all input gradients")
    close(
        sum(torch.tensor(r["drouter_weight"], dtype=torch.float64) for r in refs),
        gate.grad,
        "shared router weight reduction",
    )
    for i, w in enumerate(expert):
        for name, value in w.items():
            expected = value.grad if value.grad is not None else torch.zeros_like(value)
            close(
                sum(
                    torch.tensor(r["dexperts"][i][name], dtype=torch.float64)
                    for r in refs
                ),
                expected,
                "expert repeated-token parameter reduction",
            )
    for name, value in shared.items():
        close(
            sum(torch.tensor(r["dshared"][name], dtype=torch.float64) for r in refs),
            value.grad,
            "shared expert reduction",
        )

for batch, tokens, layer, route in (
    (1, 1, 0, "balanced"),
    (2, 3, 3, "balanced"),
    (1, 129, 42, "balanced"),
    (2, 4, 2, "concentrated"),
):
    result = m.calculate(batch=batch, tokens=tokens, layer_id=layer, routing=route)
    check(result == m.calculate(**result["scenario"]), "scenario replay")
    r = batch * tokens
    h, f, e, k = 4096, 2048, 256, 6
    a = r * k
    counts = result["routing_histogram"]
    check(sum(counts) == a and max(counts) <= r, "distinct row capacity")
    check(
        result["totals"]["forward_matrix_flops"]
        == 2 * r * h * e + sum(6 * n * h * f for n in counts) + 6 * r * h * f,
        "forward independent sum",
    )
    check(
        result["totals"]["backward_matrix_flops"]
        == 4 * r * h * e + sum(12 * n * h * f for n in counts) + 12 * r * h * f,
        "backward independent sum",
    )
    check(
        result["scalar"]["backward_input_branches_and_scatter_flops"]
        == ((a + r) + a + r + r) * h,
        "dx branch zero accumulation",
    )
    check(
        result["scalar"]["routed_weight_backward_flops"] == a * (f + (f - 1) + f),
        "route dot and activation VJP",
    )
    check(
        result["saved_forward_boundary"]["total_bytes"]
        == sum(result["saved_forward_boundary"]["buffers"].values()),
        "saved bytes",
    )
    check(
        result["parameters"]["routed_expert_weights"] == e * 3 * h * f,
        "resident expert weights",
    )
    check(
        result["parameters"]["visited_expert_gradient_parameters"]
        == sum(n > 0 for n in counts) * 3 * h * f,
        "visited gradient geometry",
    )
    for row in result["routed_experts"]:
        n = row["assigned_rows"]
        check(
            row["forward_matrix_flops"]
            == 2 * n * f * h + 2 * n * f * h + 2 * n * h * f,
            "expert three projections",
        )
        check(
            row["backward_matrix_flops"]
            == 2 * (2 * n * f * h + 2 * n * f * h + 2 * n * h * f),
            "three input/weight VJPs",
        )

module = Path(m.__file__)
(ROOT / "results.json").write_text(
    json.dumps(
        dict(
            checks=checks,
            max_absolute_error=max(errors),
            module=str(module.relative_to(PROJECT)),
            sha256=hashlib.sha256(module.read_bytes()).hexdigest(),
        ),
        indent=2,
    )
    + "\n"
)
print(checks, max(errors))
public = PROJECT / "research/v4-moe-training/public"
artifact_checks = 0
for source in json.loads((public / "sources.lock.subset.json").read_text())["sources"]:
    data = (PROJECT / source["file"]).read_bytes()
    assert (
        len(data) == source["bytes"]
        and hashlib.sha256(data).hexdigest() == source["sha256"]
    )
    artifact_checks += 1
for entry in json.loads((public / "bindings.json").read_text())["artifacts"]:
    assert (
        hashlib.sha256((PROJECT.parent / entry["file"]).read_bytes()).hexdigest()
        == entry["sha256"]
    )
    artifact_checks += 1
for entry in json.loads((public / "book.append.json").read_text()):
    args = {k: v for k, v in entry.items() if k != "id"}
    result = m.calculate(**args)
    assert result == json.loads(
        (public / "results" / f"{entry['id']}.json").read_text()
    )
    assert m.markdown(result) == (public / "results" / f"{entry['id']}.md").read_text()
    artifact_checks += 2
(ROOT / "artifact-results.json").write_text(
    json.dumps(dict(checks=artifact_checks, status="passed"), indent=2) + "\n"
)
print("artifact checks", artifact_checks)
