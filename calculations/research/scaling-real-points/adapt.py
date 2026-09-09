"""Evidence-gated real records; never pool unlike evaluation populations."""

from pathlib import Path
import hashlib
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from infra_calc.topics import scaling_law

HOLDOUT_N = 2_000_000_000
GRID = [(a / 100, b / 100) for a in range(10, 61, 5) for b in range(10, 61, 5)]


def build():
    for locked in json.loads((HERE / "adapter-inputs.lock.json").read_text()):
        data = (HERE / locked["file"]).read_bytes()
        if (
            len(data) != locked["bytes"]
            or hashlib.sha256(data).hexdigest() != locked["sha256"]
        ):
            raise ValueError("Adapter evidence checksum mismatch: " + locked["file"])
    candidates = json.loads((HERE / "candidate-points.json").read_text())
    logs = json.loads((HERE / "log-controls.json").read_text())
    rows = []
    for candidate in candidates:
        name = candidate["record_id"]
        matched = [x for x in logs if x["record_id"] == name and x["match"]]
        row = dict(
            candidate,
            split="holdout" if candidate["N"] >= HOLDOUT_N else "fit",
            N_definition="Author PARAMS_MAP reported estimate; not exact checkpoint parameter inventory",
            D_definition="Author run-name training token label; source budget/achieved count audited separately",
            loss_definition="Author reported final validation natural-log loss; original raw log checked where available",
            control_id=None,
            fit_eligible=False,
            reasons=[],
        )
        if not matched:
            row["reasons"].append(
                "No archived final-evaluation log matched this candidate and loss"
            )
            rows.append(row)
            continue
        entry = matched[0]
        path = HERE / entry["file"]
        text = path.read_text(errors="replace")
        specs = set(
            re.findall(
                r"c4validation_rerun_text_document_validation_indexmap_(\d+)ns_(\d+)sl_(\d+)s_",
                text,
            )
        )
        if len(specs) != 1:
            row["reasons"].append("Ambiguous or absent evaluation population indexmap")
        else:
            ns, sl, seed = map(int, next(iter(specs)))
            row["evaluation"] = dict(
                samples=ns,
                sequence_length=sl,
                seed=seed,
                tokens=ns * sl,
                file=entry["file"],
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            row["control_id"] = f"C4-gpt2-rerun-{ns}samples-{sl}length-seed{seed}"
        train_files = list(path.parent.glob("sbatch_" + name + ".sh")) + list(
            path.parent.parent.glob("sbatch_" + name + ".sh")
        )
        if not train_files:
            row["reasons"].append("Training-budget script not archived for this run")
        else:
            train = train_files[0]
            body = train.read_text()
            samples = re.search(r"^TRAIN_SAMPLES=([0-9_]+)", body, re.M)
            seq = re.search(r"^SEQ_LEN=(\d+)", body, re.M)
            if samples and seq:
                target = int(samples.group(1).replace("_", "")) * int(seq.group(1))
                row["training_budget"] = dict(
                    declared_samples=int(samples.group(1).replace("_", "")),
                    sequence_length=int(seq.group(1)),
                    declared_target_tokens=target,
                    author_label_delta_tokens=target - candidate["D"],
                    file=str(train.relative_to(HERE)),
                    sha256=hashlib.sha256(train.read_bytes()).hexdigest(),
                )
            row["reasons"].append(
                "Declared training target is not an independently verified achieved-token counter"
            )
        row["reasons"].append(
            "Per-run N estimate/shape definition and common training policy still require completed source audit"
        )
        rows.append(row)
    return rows


def fit_verified(rows):
    """Only explicitly eligible original rows reach the existing fit API."""
    eligible = [x for x in rows if x["fit_eligible"]]
    controls = sorted({x["control_id"] for x in eligible})
    results = []
    for control in controls:
        selected = [x for x in eligible if x["control_id"] == control]
        counts = {s: sum(x["split"] == s for x in selected) for s in ["fit", "holdout"]}
        if counts["fit"] < 4 or counts["holdout"] < 1:
            results.append(
                dict(
                    control_id=control,
                    status="insufficient_same_control_split",
                    counts=counts,
                )
            )
            continue
        records = [
            dict(
                id=x["record_id"],
                N=x["N"],
                D=x["D"],
                loss=x["loss"],
                C_flops=6 * x["N"] * x["D"],
                control_id=control,
                split=x["split"],
                compute_definition="6ND analytical normalization, not measured training FLOPs",
            )
            for x in selected
        ]
        results.append(
            dict(
                control_id=control,
                status="fit",
                result=scaling_law.fit(records, GRID, 1e9, 1e10),
            )
        )
    return dict(
        status="no_verified_fit_group"
        if not any(x.get("status") == "fit" for x in results)
        else "fit",
        groups=results,
        holdout_rule="N>=2e9 fixed before fitting",
        synthetic_rows_added=0,
    )


def calculate():
    rows = build()
    populations = {}
    for row in rows:
        if row["control_id"]:
            p = populations.setdefault(row["control_id"], dict(fit=[], holdout=[]))
            p[row["split"]].append(row["record_id"])
    return dict(
        calculation="datablations-source-gated-scaling",
        records=rows,
        verified_evaluation_population_inventory=populations,
        fit=fit_verified(rows),
        status="source_controls_incomplete",
        training_fit_executed=False,
    )


if __name__ == "__main__":
    out = calculate()
    (HERE / "adapted.json").write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                status=out["status"],
                populations=out["verified_evaluation_population_inventory"],
                fit_status=out["fit"]["status"],
            ),
            indent=2,
        )
    )
