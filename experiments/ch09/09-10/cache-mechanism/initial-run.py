import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parent
ENV = Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, x):
    p.write_text(json.dumps(x, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=ROOT / 'results')
    ap.add_argument('--cache', type=Path, default=Path('/home/ubuntu/ai-infra-book-experiments/ch09/09-08/storage-v3'))
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((ROOT / 'cache-manifest.json').read_text())
    for f in manifest:
        p = a.cache / f['path']
        assert p.stat().st_size == f['bytes'] and sha(p) == f['sha256']
    rng = random.Random(9102)
    order = []
    for trial in range(2):
        conditions = list(itertools.product(['native', 'http_plain', 'http_logprob'], [1, 8]))
        rng.shuffle(conditions)
        order.extend({'trial': trial, 'entry': e, 'count': n} for e, n in conditions)
    source_files = ['run.py', 'worker.py', 'server.py', 'storage_trace.py', 'config.json', 'inputs.json', 'reference.json', 'cache-manifest.json']
    dump(a.output / 'plan.json', {'order': order, 'source_sha256': {f: sha(ROOT / f) for f in source_files},
        'cache_source': str(a.cache), 'mem_fraction_static': .75, 'max_total_tokens': 4096,
        'goal': 'Cache hit mechanism, not comparative latency under shared GPU load'})
    env = os.environ.copy()
    cuda = str(ENV / 'lib/python3.10/site-packages/nvidia/cu13')
    env.update(CUDA_HOME=cuda, PATH=cuda + '/bin:' + env['PATH'],
               TVM_FFI_CACHE_DIR='/home/ubuntu/ai-infra-book-experiments/ch09/09-08/jit-cache-cu13-v2',
               PYTHONUNBUFFERED='1')
    records = []
    for c in order:
        out = a.output / f"{c['trial']}-{c['entry']}-{c['count']}"
        out.mkdir()
        free = int(subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
        (out / 'gpu-before.txt').write_text(subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv'], text=True))
        if free < 30000:
            dump(out / 'resource-stop.json', {'free_MiB': free, 'minimum_MiB': 30000})
            raise RuntimeError('Insufficient current headroom; existing services untouched')
        storage = out / 'storage'
        storage.mkdir()
        prepare_begin = time.monotonic()
        for f in manifest:
            dest = storage / f['path']
            shutil.copy2(a.cache / f['path'], dest)
            assert sha(dest) == f['sha256']
        dump(out / 'cache-preparation.json', {'files_verified': len(manifest),
             'begin_s': prepare_begin, 'end_s': time.monotonic(), 'source_manifest_sha256': sha(ROOT / 'cache-manifest.json')})
        run_env = dict(env, SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR=str(storage.resolve()),
                       BOOK_HICACHE_TRACE=str((out / 'storage.jsonl').resolve()))
        cmd = [str(ENV / 'bin/python'), str(ROOT / 'worker.py'), '--entry', c['entry'],
               '--count', str(c['count']), '--output', str(out.resolve())]
        with (out / 'worker.log').open('x') as log:
            p = subprocess.Popen(cmd, env=run_env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timed_out = False
            try:
                p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                # Kill only this coordinator-created process group if anything remains.
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                if p.poll() is None:
                    try:
                        p.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=15)
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        record = {**c, 'pid': p.pid, 'exit_code': p.returncode, 'timed_out': timed_out}
        records.append(record)
        dump(out / 'coordinator.json', record)
        dump(a.output / 'coordinator.json', records)
        (out / 'gpu-after.txt').write_text(subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv'], text=True))
        print(json.dumps(record), flush=True)
    dump(a.output / 'execution.json', {'status': 'completed' if all(r['exit_code'] == 0 for r in records) else 'completed_with_failures', 'groups': len(records)})


if __name__ == '__main__':
    main()
