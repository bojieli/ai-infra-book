from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import unittest
import torch

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "calculations/research/v4-optimizer"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "calculations/src"))
import infra_calc.topics

infra_calc.topics.__path__.insert(0, str(BASE / "public/src/infra_calc/topics"))
from infra_calc.topics import v4_optimizer as m

checks = []


def require(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)


class Scalar:
    count = 0

    def __init__(self, value):
        self.value = float(value)

    def operation(self, other, op):
        Scalar.count += 1
        other = other.value if isinstance(other, Scalar) else other
        return Scalar(op(self.value, other))

    def __add__(self, other):
        return self.operation(other, lambda a, b: a + b)

    __radd__ = __add__

    def __mul__(self, other):
        return self.operation(other, lambda a, b: a * b)

    __rmul__ = __mul__

    def __sub__(self, other):
        return self.operation(other, lambda a, b: a - b)

    def __rsub__(self, other):
        return self.operation(other, lambda a, b: b - a)

    def __truediv__(self, other):
        return self.operation(other, lambda a, b: a / b)


def scalar_oracle(rows, cols, orientation):
    transpose = orientation == "smaller_gram" and rows > cols
    n, p = (cols, rows) if transpose else (rows, cols)
    value = lambda: Scalar(0.7)
    weights = [[value() for _ in range(p)] for _ in range(n)]
    gradients = [[value() for _ in range(p)] for _ in range(n)]
    momentum = [[value() for _ in range(p)] for _ in range(n)]
    Scalar.count = 0
    gemms = []

    def mm(a, b):
        require(len(a[0]) == len(b), "independent GEMM dimensions match")
        gemms.append([len(a), len(b[0]), len(b)])
        return [[value() for _ in b[0]] for _ in a]

    tr = lambda a: list(map(list, zip(*a)))
    mom = [
        [0.95 * momentum[i][j] + gradients[i][j] for j in range(p)] for i in range(n)
    ]
    x = [[0.95 * mom[i][j] + gradients[i][j] for j in range(p)] for i in range(n)]
    squared = [v * v for row in x for v in row]
    total = squared[0]
    for v in squared[1:]:
        total = total + v
    denominator = Scalar(math.sqrt(total.value)) + 0.0
    x = [[v / denominator for v in row] for row in x]
    for a, b, c in [(3.4445, -4.7750, 2.0315)] * 8 + [(2.0, -1.5, 0.5)] * 2:
        gram = mm(x, tr(x))
        square = mm(gram, gram)
        combined = [
            [b * u + c * v for u, v in zip(row, other)]
            for row, other in zip(gram, square)
        ]
        cx = mm(combined, x)
        x = [[a * u + v for u, v in zip(row, other)] for row, other in zip(x, cx)]
    rescale = math.sqrt(max(rows, cols)) * 0.18
    update = [[v * rescale for v in row] for row in x]
    decay = 1 - Scalar(2.7e-4) * 0.1
    result = [
        [w * decay - 2.7e-4 * u for w, u in zip(row, other)]
        for row, other in zip(weights, update)
    ]
    return Scalar.count, gemms


def inventory(model):
    folder = ROOT / "calculations/sources" / model
    index = json.loads((folder / "model.safetensors.index.json").read_text())[
        "weight_map"
    ]
    tensors = {}
    for shard in sorted(set(index.values())):
        for name, record in json.loads(
            (folder / "headers" / f"{shard}.json").read_text()
        ).items():
            if name == "__metadata__":
                continue
            require(name not in tensors, "raw tensor name unique " + model)
            shape = record["shape"][:]
            if record["dtype"] == "I8":
                require(
                    ".experts." in name
                    and name.endswith((".w1.weight", ".w2.weight", ".w3.weight")),
                    "packed dtype scoped to expert matrices",
                )
                shape[-1] *= 2
            tensors[name] = (shape, math.prod(shape))
    return tensors


def audit_inventory(result, raw):
    scenario = result["scenario"]
    groups = result["groups"]
    selected = Counter()
    logical = Counter()
    excluded = Counter()
    hits = Counter()
    patterns = []
    for i, g in enumerate(groups):
        pattern = (
            "^" + re.escape(g["name_pattern"]).replace(re.escape("{i}"), r"\d+") + "$"
        )
        patterns.append((i, re.compile(pattern)))
    for name, (shape, elements) in raw.items():
        owner = "mtp" if name.startswith("mtp.") else "base"
        if name.endswith(".scale") or name.endswith(".tid2eid"):
            excluded[
                owner
                + (
                    "_quant_scale_elements"
                    if name.endswith(".scale")
                    else "_hash_elements"
                )
            ] += elements
            continue
        logical[owner + "_logical_parameters"] += elements
        if owner == "mtp" and not scenario["include_mtp"]:
            excluded["mtp_logical_parameters"] += elements
            continue
        match = [
            i
            for i, p in patterns
            if groups[i]["owner"] == owner
            and groups[i]["logical_tensor_shape"] == shape
            and p.fullmatch(name)
        ]
        require(len(match) == 1, "every selected raw tensor maps to exactly one group")
        group = groups[match[0]]
        hits[match[0]] += 1
        selected[group["optimizer"]] += elements
        family = group["optimizer"]
        if name.endswith(".scale") or name.endswith(".tid2eid"):
            raise AssertionError("metadata leaked")
        if (
            "norm.weight" in name
            or name.endswith(("embed.weight", "head.weight"))
            or re.search("hc_.*_(base|scale)$", name)
        ):
            require(family == "adamw", "report Adam exceptions")
        elif name.endswith("ffn.gate.bias"):
            require(family == "external_router_bias", "router bias remains external")
        elif name.endswith("attn_sink"):
            require(
                family
                == (
                    "unresolved" if scenario["sink_policy"] == "unresolved" else "muon"
                ),
                "sink policy explicit",
            )
        elif name.endswith("hc_head_fn"):
            require(
                family == scenario["head_mixer_policy"], "head mixer policy explicit"
            )
        else:
            require(family == "muon", "remaining eligible matrix follows report")
    require(dict(logical) == result["inventory"], "base and MTP raw logical inventory")
    require(
        dict(excluded) == result["excluded_inventory"],
        "all excluded metadata/MTP accounted",
    )
    for i, g in enumerate(groups):
        require(hits[i] == g["tensor_count"], "group tensor multiplicity")
        require(
            math.prod(g["logical_tensor_shape"]) * hits[i] == g["parameters"],
            "group parameters exact",
        )
        if g["optimizer"] == "muon":
            n, p = g["independent_matrix_shape"]
            require(
                n * p * g["independent_matrices_per_tensor"] * hits[i]
                == g["parameters"],
                "independent matrix partition preserves parameters",
            )
            if scenario["wo_a_partition"] == "source_groups" and g[
                "example_tensor"
            ].endswith("attn.wo_a.weight"):
                config = json.loads(
                    (
                        ROOT
                        / "calculations/configs/models"
                        / scenario["model"]
                        / "inference/config.json"
                    ).read_text()
                )
                require(
                    g["independent_matrices_per_tensor"] == config["o_groups"]
                    and n == config["o_lora_rank"],
                    "wo_a source reshape",
                )
            if ".experts." in g["example_tensor"]:
                require(
                    g["independent_matrices_per_tensor"] == 1,
                    "experts not concatenated for NS",
                )
    for family, count in selected.items():
        require(
            count == result["summary"][family + "_parameters"],
            "family parameter conservation",
        )
    expected_matrix = 0
    expected_scalar = 0
    normalization_calls = 0
    for group in groups:
        if group["optimizer"] == "muon":
            rows, columns = group["independent_matrix_shape"]
            n, width = (
                (min(rows, columns), max(rows, columns))
                if scenario["orientation"] == "smaller_gram"
                else (rows, columns)
            )
            copies = group["tensor_count"] * group["independent_matrices_per_tensor"]
            matrix = copies * 10 * (4 * n * n * width + 2 * n * n * n)
            scalar = copies * (31 * n * width + 30 * n * n)
            require(
                matrix == group["matrix_flops"], "every group matrix polynomial total"
            )
            require(
                scalar == group["ordinary_scalar_operations"],
                "every group scalar polynomial total",
            )
            expected_matrix += matrix
            expected_scalar += scalar
            normalization_calls += copies
        elif group["optimizer"] == "adamw":
            require(
                group["ordinary_scalar_operations"] == 14 * group["parameters"],
                "every Adam group 14P",
            )
            expected_scalar += 14 * group["parameters"]
    expected_scalar += (6 if selected["adamw"] else 0) + (2 if selected["muon"] else 0)
    require(
        expected_matrix == result["summary"]["matrix_flops"],
        "full selected matrix total",
    )
    require(
        expected_scalar == result["summary"]["ordinary_scalar_operations"],
        "full selected scalar total plus shared coefficients",
    )
    require(
        normalization_calls == result["summary"]["normalization_sqrt"],
        "one norm sqrt per independent matrix",
    )
    mp, ap = selected["muon"], selected["adamw"]
    for key, count in [
        ("declared_fp32_master_weights_bytes", 4 * (mp + ap)),
        ("declared_fp32_muon_momentum_bytes", 4 * mp),
        ("declared_fp32_adam_m_v_bytes", 8 * ap),
        ("declared_fp32_gradient_input_bytes", 4 * (mp + ap)),
    ]:
        require(result["state_interfaces"][key] == count, "state " + key)
    require(
        result["scope"]["full_optimizer_exact"] is False,
        "no exact full optimizer claim",
    )
    require(
        result["state_interfaces"]["actual_peak_bytes"] is None, "actual peak unknown"
    )


def main():
    frozen = json.loads((BASE / "bindings.json").read_text())
    for entry in frozen["files"]:
        data = (BASE / entry["file"]).read_bytes()
        require(
            hashlib.sha256(data).hexdigest() == entry["sha256"],
            "frozen artifact " + entry["file"],
        )
    evidence = json.loads((BASE / "source-evidence.json").read_text())
    for name in ("report_text", "report_pdf"):
        record = evidence[name]
        require(
            hashlib.sha256((ROOT / record["file"]).read_bytes()).hexdigest()
            == record["sha256"],
            "official report " + name,
        )
    for record in evidence["public_sources"]:
        data = (ROOT / "calculations" / record["file"]).read_bytes()
        require(
            len(data) == record["bytes"]
            and hashlib.sha256(data).hexdigest() == record["sha256"],
            "official locked bytes/hash",
        )
    raw = {
        model: inventory(model) for model in ("deepseek-v4-flash", "deepseek-v4-pro")
    }
    for path in sorted((BASE / "public/results").glob("*.json")):
        result = json.loads(path.read_text())
        audit_inventory(result, raw[result["scenario"]["model"]])
        require(
            json.loads(json.dumps(m.calculate(**result["scenario"]))) == result,
            "frozen scenario replay " + path.stem,
        )
    shapes = [(1, 1), (1, 5), (2, 7), (7, 2), (4, 4)]
    max_error = 0.0
    torch.manual_seed(351)
    for rows, cols in shapes:
        for orientation in ("smaller_gram", "stored_left_gram"):
            work = m.matrix_work(rows, cols, orientation)
            ordinary, gemms = scalar_oracle(rows, cols, orientation)
            require(
                ordinary == work["ordinary_scalar_operations"] + 2,
                "instrumented scalar count incl shared decay",
            )
            require(
                sum(2 * n * p * k for n, p, k in gemms) == work["matrix_flops"],
                "instrumented GEMM shape/FLOPs",
            )
            n, p = work["oriented_shape"]
            E = n * p
            expected = dict(
                gemm_operand_reads=4 * (3 * E + 3 * n * n),
                gemm_outputs=4 * (2 * n * n + E),
                scalar_combine_reads=4 * (2 * n * n + 2 * E),
                scalar_combine_writes=4 * (n * n + E),
            )
            require(
                work["tensor_interfaces_per_iteration_bytes"] == expected,
                "independent role interface bytes",
            )
            for epsilon in (0.0, 1e-7):
                w, g, momentum = [
                    torch.randn(rows, cols, dtype=torch.float64) for _ in range(3)
                ]
                buffer = 0.95 * momentum + g
                z = 0.95 * buffer + g
                z = z / (torch.linalg.vector_norm(z) + epsilon)
                # SVD singular-value polynomial oracle, independently avoids matrix factorization.
                u, s, vh = torch.linalg.svd(z, full_matrices=False)
                for a, b, c in [(3.4445, -4.7750, 2.0315)] * 8 + [(2.0, -1.5, 0.5)] * 2:
                    s = a * s + b * s**3 + c * s**5
                expected = (
                    w * (1 - 0.125 * 0.1)
                    - 0.125
                    * (u @ torch.diag(s) @ vh)
                    * math.sqrt(max(rows, cols))
                    * 0.18
                )
                actual, new_buffer = m.muon_reference(
                    w,
                    g,
                    momentum,
                    learning_rate=0.125,
                    orientation=orientation,
                    norm_epsilon=epsilon,
                )
                error = (actual - expected).abs().max().item()
                max_error = max(max_error, error)
                require(error < 2e-12, "independent spectral NS numerical value")
                require(torch.equal(new_buffer, buffer), "Nesterov momentum exact")
    tests = unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.discover(str(BASE / "public/tests"))
    )
    require(tests.wasSuccessful() and not tests.skipped, "original optimizer tests")
    result = dict(
        status="passed",
        independent_checks=len(checks),
        original_tests=tests.testsRun,
        skipped=len(tests.skipped),
        max_spectral_oracle_absolute_error=max_error,
        module_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
        checks=checks,
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}, indent=2))


if __name__ == "__main__":
    main()
