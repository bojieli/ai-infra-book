"""Independent interval, dependency and public-workload oracles; candidate read-only."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "calculations/research/training-pipeline"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "calculations/src"))
import infra_calc.topics

infra_calc.topics.__path__.insert(0, str(BASE / "public/src/infra_calc/topics"))
from infra_calc.topics import training_pipeline_schedule as candidate
from infra_calc.topics import training_nonmatrix
from infra_calc.models import qwen3
from infra_calc.sources import model_config

checks = []


def require(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)


def audit_result(r, label):
    args = r["scenario"]
    M = args["microbatches"]
    event = {x["id"]: x for x in r["events"]}
    require(len(event) == 14 * M + 5, label + ": unique and complete event IDs")
    for stage in range(4):
        for mb in range(M):
            f, b = event[f"F:{stage}:{mb}"], event[f"B:{stage}:{mb}"]
            require(
                b["start"] + 1e-12 >= f["end"], label + ": own forward before backward"
            )
            if stage:
                a = event[f"A:{stage-1}:{mb}"]
                require(
                    a["start"] + 1e-12 >= event[f"F:{stage-1}:{mb}"]["end"]
                    and f["start"] + 1e-12 >= a["end"],
                    label + ": activation producer/transfer/consumer",
                )
            if stage < 3:
                g = event[f"G:{stage+1}:{mb}"]
                require(
                    g["start"] + 1e-12 >= event[f"B:{stage+1}:{mb}"]["end"]
                    and b["start"] + 1e-12 >= g["end"],
                    label + ": gradient producer/transfer/consumer",
                )
    for e in event.values():
        require(
            all(e["start"] + 1e-12 >= event[d]["end"] for d in e["dependencies"]),
            label + ": explicit DAG edge",
        )
    resources = defaultdict(list)
    for e in event.values():
        if e["end"] > e["start"]:
            resources[e["resource"]].append(e)
    for resource, events in resources.items():
        events.sort(key=lambda x: x["start"])
        require(
            all(a["end"] <= b["start"] + 1e-12 for a, b in zip(events, events[1:])),
            label + ": no resource overlap " + resource,
        )
    ready = max(e["end"] for e in event.values() if e["kind"] == "B")
    require(
        all(event[f"U:{s}"]["start"] + 1e-12 >= ready for s in range(4)),
        label + ": global update barrier",
    )
    if args["policy"] == "gpipe":
        require(
            min(e["start"] for e in event.values() if e["kind"] == "B") + 1e-12
            >= max(e["end"] for e in event.values() if e["kind"] == "F"),
            label + ": global GPipe F barrier",
        )
    for s in range(4):
        order = [
            (e["kind"], e["microbatch"])
            for e in sorted(
                (
                    e
                    for e in event.values()
                    if e["stage"] == s and e["kind"] in ("F", "B")
                ),
                key=lambda e: (
                    e["start"],
                    r["stage_orders"][s].index(
                        dict(kind=e["kind"], microbatch=e["microbatch"])
                    ),
                ),
            )
        ]
        expected = [(e["kind"], e["microbatch"]) for e in r["stage_orders"][s]]
        require(order == expected, label + ": stage order")
        intervals = [i for i in r["activation_intervals"] if i["stage"] == s]
        require(
            all(i["end"] >= i["start"] for i in intervals),
            label + ": nonnegative buffer lifetime",
        )
        times = sorted({i[k] for i in intervals for k in ("start", "end")})
        # Enumerate elementary open intervals; independent of author's event-sweep implementation.
        peak = max(
            [
                sum(
                    i["bytes"]
                    for i in intervals
                    if i["start"] <= ((a + b) / 2) < i["end"]
                )
                for a, b in zip(times, times[1:])
            ]
            + [0]
        )
        require(
            peak == r["stages"][s]["peak_declared_reserved_bytes"],
            label + ": independent occupancy peak",
        )
    for interval in r["activation_intervals"]:
        if interval["kind"] == "declared_saved_reservation":
            _, s, mb = interval["id"].split(":")
            s = int(s)
            mb = int(mb)
            require(
                (interval["start"], interval["end"])
                == (event[f"F:{s}:{mb}"]["start"], event[f"B:{s}:{mb}"]["end"]),
                label + ": saved F-start/B-end",
            )
        if interval["kind"] in ("send_buffer", "receive_buffer"):
            identity, suffix = interval["id"].rsplit(":", 1)
            transfer = event[identity]
            s = transfer["stage"]
            mb = transfer["microbatch"]
            kind = "F" if transfer["kind"] == "A" else "B"
            target = s + 1 if kind == "F" else s - 1
            expect = (
                (event[f"{kind}:{s}:{mb}"]["end"], transfer["end"])
                if suffix == "send"
                else (transfer["start"], event[f"{kind}:{target}:{mb}"]["start"])
            )
            require(
                (interval["start"], interval["end"]) == expect,
                label + ": communication lifetime endpoint",
            )
    source = training_nonmatrix.calculate(
        batch=args["microbatch_size"],
        tokens=args["tokens"],
        activation_policy=args["activation_policy"],
    )
    stages = r["work"]["per_microbatch_stages"]
    for op in source["training_matrix_original"]["training_matrix_rows"]:
        rows = [
            row for s in stages for row in s["matrices"] if row["name"] == op["name"]
        ]
        require(
            sum(row["forward_flops"] for row in rows)
            == op["forward_flops"] * op["repeats"],
            label + ": actual matrix conservation " + op["name"],
        )
        require(
            sum(row["backward_flops"] for row in rows)
            == 2 * op["forward_flops"] * op["repeats"],
            label + ": actual matrix VJP conservation " + op["name"],
        )
    for op in source["nonmatrix_operations"]:
        rows = [
            row for s in stages for row in s["nonmatrix"] if row["name"] == op["name"]
        ] + [
            row
            for row in r["work"]["once_per_step_rotary_setup"]
            if row["name"] == op["name"]
        ]
        for field in ("forward_scalar_flops", "backward_scalar_flops"):
            require(
                sum(row[field] for row in rows) == op[field],
                label + ": scalar conservation " + op["name"] + field,
            )
        for field in ("forward_special_ops", "backward_special_ops"):
            summed = Counter()
            for row in rows:
                summed.update(row[field])
            require(
                dict(summed) == op[field],
                label + ": special conservation " + op["name"] + field,
            )
    params = [0] * 4
    for weight in qwen3.weights(model_config("qwen3-8b")):
        if weight.copies == 36:
            for s in range(4):
                params[s] += weight.parameters // 4
        else:
            params[0 if "embed_tokens" in weight.name else 3] += weight.parameters
    require(
        params == [s["parameters"] for s in stages], label + ": parameter ownership"
    )
    require(
        sum(params)
        == r["work"]["total_parameters"]
        == source["optimizer"]["parameters"],
        label + ": optimizer parameters conservation",
    )
    require(
        r["work"]["once_per_step_optimizer"] == source["optimizer"],
        label + ": one public optimizer update",
    )
    require(
        r["work"]["step_parameter_accumulation_and_mean_scalar_flops"]
        == sum(params) * ((M - 1) + (M > 1)),
        label + ": accumulation and mean once",
    )
    saved = [i for s in stages for i in s["saved_objects"]]
    require(
        sorted(saved, key=lambda x: x["id"])
        == sorted(source["saved_objects"], key=lambda x: x["id"]),
        label + ": exact saved identity conservation",
    )
    require(
        r["summary"]["complete_training_activation_peak_bytes"] is None
        and r["summary"]["measured_runtime_seconds"] is None,
        label + ": partial/unmeasured boundary",
    )


def main():
    frozen = json.loads((BASE / "bindings.json").read_text())
    for group in ("artifacts", "dependencies"):
        for record in frozen[group]:
            path = ROOT / record["file"]
            require(
                hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"],
                "frozen " + record["file"],
            )
    for path in sorted((BASE / "public/results").glob("*.json")):
        result = json.loads(path.read_text())
        audit_result(result, path.stem)
        require(
            candidate.calculate(**result["scenario"]) == result,
            "scenario replay " + path.stem,
        )
    rng = random.Random(9182)
    for i in range(16):
        args = dict(
            microbatches=rng.choice([1, 2, 3, 5, 7]),
            tokens=3,
            microbatch_size=2,
            policy=["gpipe", "1f1b"][i % 2],
            link_mode=["independent_directional", "shared_half_duplex"][(i // 2) % 2],
            forward_seconds=[rng.choice([0, 0.1, 0.4]) for _ in range(4)],
            backward_seconds=[rng.choice([0, 0.2, 0.5]) for _ in range(4)],
            activation_transfer_seconds=[rng.choice([0, 0.03, 0.2]) for _ in range(3)],
            gradient_transfer_seconds=[rng.choice([0, 0.02, 0.3]) for _ in range(3)],
            optimizer_seconds=[0, 0.01, 0.02, 0.03],
            setup_seconds=0.02,
            activation_policy=["save_nonlinear", "recompute_silu"][i % 2],
        )
        audit_result(candidate.calculate(**args), f"random-{i}")
    for M in (1, 2, 4, 8, 16):
        for policy in ("gpipe", "1f1b"):
            r = candidate.calculate(
                microbatches=M,
                tokens=1,
                policy=policy,
                forward_seconds=[1] * 4,
                backward_seconds=[1] * 4,
                activation_transfer_seconds=[0] * 3,
                gradient_transfer_seconds=[0] * 3,
                optimizer_seconds=[0] * 4,
            )
            require(
                r["summary"]["step_makespan_seconds"] == 2 * (M + 3),
                f"balanced closed form {M} {policy}",
            )
    suite = unittest.defaultTestLoader.discover(str(BASE / "public/tests"))
    original = unittest.TextTestRunner(verbosity=1).run(suite)
    require(
        original.wasSuccessful() and not original.skipped,
        "original tests pass without skips",
    )
    result = dict(
        status="passed",
        independent_checks=len(checks),
        candidate_module_sha256=hashlib.sha256(
            Path(candidate.__file__).read_bytes()
        ).hexdigest(),
        original_tests=original.testsRun,
        scenarios=14,
        random_scenarios=16,
        checks=checks,
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}, indent=2))


if __name__ == "__main__":
    main()
