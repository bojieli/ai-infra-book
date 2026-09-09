"""Independent interpreter hash seeds: deterministic bytes without sort_keys."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
FROZEN = ROOT / "calculations/results/request-four-models-prefix-boundary.json"
scenario = json.loads(FROZEN.read_text())["scenario"]
code = """import json,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'calculations/src'))
import infra_calc.topics
if sys.argv[2]=='candidate':
    infra_calc.topics.__path__.insert(0,str(root/'calculations/research/request-comparison-determinism/src/infra_calc/topics'))
from infra_calc.topics import request_model_comparison
result=request_model_comparison.calculate(**json.loads(sys.argv[3]))
sys.stdout.write(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\\n')
"""
seeds = ["0", "1", "7", "42", "123", "987654"]


def run(job):
    version, seed = job
    proc = subprocess.run(
        [sys.executable, "-c", code, str(ROOT), version, json.dumps(scenario)],
        env=dict(os.environ, PYTHONHASHSEED=seed),
        capture_output=True,
        check=True,
    )
    parsed = json.loads(proc.stdout)
    return dict(
        version=version,
        seed=seed,
        bytes=len(proc.stdout),
        sha256=hashlib.sha256(proc.stdout).hexdigest(),
        parsed=parsed,
        payload=proc.stdout,
    )


def main():
    frozen = json.loads(FROZEN.read_text())
    jobs = [
        (version, seed) for version in ("old_public", "candidate") for seed in seeds
    ]
    with ThreadPoolExecutor(max_workers=3) as pool:
        runs = list(pool.map(run, jobs))
    old = [r for r in runs if r["version"] == "old_public"]
    new = [r for r in runs if r["version"] == "candidate"]
    assert (
        len({r["sha256"] for r in new}) == 1
    ), "Candidate bytes remain nondeterministic"
    assert all(
        r["parsed"] == old[0]["parsed"] for r in runs
    ), "Parsed math changed across candidate/old/seed"
    assert all(
        r["parsed"] == frozen for r in runs
    ), "Parsed result differs from pre-existing frozen result"
    (BASE / "stable-result.json").write_bytes(new[0]["payload"])
    result = dict(
        status="passed",
        scenario=scenario,
        python=sys.executable,
        seeds=seeds,
        json_serialization="indent=2, ensure_ascii=False, allow_nan=False; sort_keys is NOT used",
        old_public_distinct_byte_hashes=len({r["sha256"] for r in old}),
        candidate_distinct_byte_hashes=1,
        all_parsed_objects_equal_old_public_and_frozen=True,
        frozen_result=dict(
            file=str(FROZEN.relative_to(ROOT)),
            sha256=hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
        ),
        runs=[
            {k: v for k, v in r.items() if k not in ("parsed", "payload")} for r in runs
        ],
    )
    (BASE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("runs", "scenario")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
