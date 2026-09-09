"""Source-verifiable C4 subset; reported-coordinate fit with explicit sensitivity."""

import json
import ast
import hashlib
import re
from pathlib import Path
from ..paths import PROJECT
from . import scaling_law, scaling_boundary_fit

GRID = [(a / 100, b / 100) for a in range(10, 61, 5) for b in range(10, 61, 5)]


def records():
    """Verify original notebook coordinates, matching final logs and budget scripts."""
    lock_path = PROJECT / "configs/scaling-real-points.lock.json"
    for entry in json.loads(lock_path.read_text()):
        raw = (PROJECT / entry["file"]).read_bytes()
        if (
            len(raw) != entry["bytes"]
            or hashlib.sha256(raw).hexdigest() != entry["sha256"]
        ):
            raise ValueError(
                "Real scaling evidence checksum mismatch: " + entry["file"]
            )
    rows = json.loads((PROJECT / "configs/scaling-real-points/data.json").read_text())
    notebook = json.loads(
        (PROJECT / "sources/scaling-real-points/utils/parametric_fit.ipynb").read_text()
    )
    constants = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        body = "".join(cell["source"])
        if "NAMES_TO_VAL_LOSSES =" not in body:
            continue
        for node in ast.parse(body).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("NAMES_TO_VAL_LOSSES", "PARAMS_MAP"):
                    constants[node.targets[0].id] = ast.literal_eval(node.value)
    for row in rows:
        name = row["id"]
        prefix = max(
            (k for k in constants["PARAMS_MAP"] if name.startswith(k)), key=len
        )
        suffix = name[len(prefix) :]
        half = len(suffix) // 2
        if suffix[:half] != suffix[half:]:
            raise ValueError("Expected original D=U identity")
        match = re.fullmatch(r"(\d+)([bm])(\d*)", suffix[:half])
        d = float(match[1] + ("." + match[3] if match[3] else "")) * (
            1e9 if match[2] == "b" else 1e6
        )
        if (
            row["N"] != constants["PARAMS_MAP"][prefix]
            or row["D"] != d
            or row["loss"] != constants["NAMES_TO_VAL_LOSSES"][name]
        ):
            raise ValueError("Notebook coordinate mismatch")
        if row["split"] != ("holdout" if row["N"] >= 2e9 else "fit"):
            raise ValueError("Fixed holdout changed")
        text = (PROJECT / row["evaluation"]["file"]).read_text()
        fields = {}
        for key in ("hidden_size", "num_layers"):
            found = re.search(r"\b" + key + r"\s+\.+\s+(\d+)", text)
            fields[key] = int(found[1])
        h, layers = fields["hidden_size"], fields["num_layers"]
        if (
            row["N_shape_estimate"]
            != 12 * layers * h * h + 13 * layers * h + (50257 + 2048) * h
        ):
            raise ValueError("Shape estimate mismatch")
        for pattern in [
            r"tokenizer_type\s+\.+\s+GPT2BPETokenizer",
            r"vocab_file\s+\.+\s+gpt2/vocab.json",
            r"merge_file\s+\.+\s+gpt2/merges.txt",
            r"valid_weighted_split_paths\s+\.+.*c4_validation/gpt2tok_c4validation_rerun_text_document",
            r"valid_weighted_split_splits\s+\.+\s+\[\[\x270:1\x27\]\]",
        ]:
            if not re.search(pattern, text):
                raise ValueError("C4 control evidence absent")
        if not any(
            abs(float(x) - row["loss"]) < 1e-6
            for x in re.findall(
                r"validation loss at the end of training for val data[^\n]*lm loss value:\s*([0-9.Ee+\-]+)",
                text,
            )
        ):
            raise ValueError("No matching author loss in final log")
        index_specs = set(
            re.findall(
                r"c4validation_rerun_text_document_validation_indexmap_(\d+)ns_(\d+)sl_(\d+)s_",
                text,
            )
        )
        expected = (
            str(row["evaluation"]["samples"]),
            str(row["evaluation"]["sequence_length"]),
            str(row["evaluation"]["seed"]),
        )
        if index_specs != {expected}:
            raise ValueError("Evaluation index-map geometry mismatch")
        if (
            row["evaluation"]["tokens"]
            != row["evaluation"]["samples"] * row["evaluation"]["sequence_length"]
        ):
            raise ValueError("Evaluation token budget mismatch")
        if row["budget_source"]:
            script = (PROJECT / row["budget_source"]).read_text()
            samples = int(
                re.search(r"^TRAIN_SAMPLES=([0-9_]+)", script, re.M)[1].replace("_", "")
            )
            seq = int(re.search(r"^SEQ_LEN=(\d+)", script, re.M)[1])
            if row["D_declared_budget"] != samples * seq:
                raise ValueError("Declared D mismatch")
    return rows


def run_fit(rows, grid):
    try:
        return dict(status="fit", result=scaling_law.fit(rows, grid, 1e9, 1e10))
    except ValueError as error:
        return dict(status="no_admissible_interior_fit", reason=str(error))


def boundary(rows):
    return scaling_boundary_fit.fit(rows, GRID, N0=1e9, D0=1e10)


def calculate():
    rows = records()
    sensitivity = {}
    for kind in ("shape_N", "declared_D", "both"):
        changed = []
        for r in rows:
            q = dict(r)
            if kind in ("shape_N", "both"):
                q["N"] = r["N_shape_estimate"]
            if kind in ("declared_D", "both") and r["D_declared_budget"] is not None:
                q["D"] = r["D_declared_budget"]
            q["C_flops"] = 6 * q["N"] * q["D"]
            changed.append(q)
        sensitivity[kind] = run_fit(changed, GRID)
    sensitivity["wider_grid"] = run_fit(
        rows, [(a / 100, b / 100) for a in range(5, 81, 5) for b in range(5, 81, 5)]
    )
    evidence = json.loads(
        (PROJECT / "configs/scaling-real-points.lock.json").read_text()
    )
    return dict(
        calculation="real_scaling_fit",
        scenario={},
        sources=evidence,
        records=rows,
        primary=run_fit(rows, GRID),
        boundary_diagnostic=boundary(rows),
        sensitivity=sensitivity,
        estimand="Held-out C4 population token loss, variable finite evaluation samples",
        sampling_variance_known=False,
        independent_observations=False,
        coordinate_uncertainty="Reported N/D; shape and declared-budget sensitivities are not exact checkpoint/achieved-token proof",
    )


def markdown(result):
    """Render the full selected observations and prespecified sensitivities."""
    primary = result["primary"]
    lines = [
        "# Real C4 scaling fit",
        "",
        result["estimand"],
        "",
        "Eight official source-matched observations; six fit, two fixed N >= 2e9 holdout. Different evaluation budgets estimate the same validation population, with unknown variance and potentially correlated errors. Reported N/D are estimates; this subset does not reproduce the full paper fit.",
        "",
        "| Point | Split | N | D | Observed loss | Eval tokens |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result["records"]:
        lines.append(
            f"| {row['id']} | {row['split']} | {row['N']:.0f} | {row['D']:.0f} | {row['loss']:.6f} | {row['evaluation']['tokens']} |"
        )
    if primary["status"] == "fit":
        fit = primary["result"]
        law = fit["law"]
        lines += [
            "",
            f"L = {law['E']:.10f} + {law['A']:.10f} (N/1e9)^(-{law['alpha']}) + {law['B']:.10f} (D/1e10)^(-{law['beta']}).",
            "",
            f"Fit SSE {fit['fit_sse']:.9g}; fixed holdout RMSE {fit['holdout_rmse']:.9g} nats/token.",
            "",
            "| Point | Predicted loss | Residual | Outside fit N/D box |",
            "|---|---:|---:|---|",
        ]
        for row in fit["predictions"]:
            lines.append(
                f"| {row['id']} | {row['predicted_loss']:.6f} | {row['residual']:.6f} | {row['outside_fit_box']} |"
            )
    else:
        lines += ["", primary["reason"]]
    lines += [
        "",
        "| Prespecified sensitivity | Status | Holdout RMSE |",
        "|---|---|---:|",
    ]
    for name, fit in result["sensitivity"].items():
        value = fit.get("result", {}).get("holdout_rmse")
        lines.append(
            f"| {name} | {fit['status']} | {value if value is not None else 'unavailable'} |"
        )
    lines += [
        "",
        "The shape-N sensitivity uses Appendix S estimates; declared-D uses available launch budgets and retains reported D where unavailable. Neither establishes exact checkpoint parameters or achieved token counters. The wider predetermined exponent grid is not selected by held-out error. C=6ND is analytical proxy compute.",
        "",
        "The boundary diagnostic permits zero coefficients and reports rank/identifiability; it does not replace the positive-law fit or establish a universal optimum. No confidence interval, independent error model, or measured runtime is asserted. Official train/validation split separation is documentary evidence, not independent document deduplication proof.",
        "",
        "Excluded explicit conflict: 146m14b14b has an 11.3B declared launch budget versus a 14B reported label. Other original rows lack matching archived final logs in this delivery. Pythia logged validation is excluded because its source path evaluates the training document pool.",
        "",
        "## Boundary diagnostic",
        "",
        "```json",
        json.dumps(
            {
                k: v
                for k, v in result["boundary_diagnostic"].items()
                if k not in ("predictions", "candidates")
            },
            indent=2,
        ),
        "```",
        "",
        "## Evidence",
        "",
        "| File | SHA256 | Source |",
        "|---|---|---|",
    ]
    for source in result["sources"]:
        lines.append(
            f"| {source['file']} | {source['sha256']} | {source.get('url',source.get('origin','derived'))} |"
        )
    return "\n".join(lines) + "\n"
