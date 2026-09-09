import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
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
    ap.add_argument('--resume', action='store_true')
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=a.resume)
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
    new_plan = {'order': order, 'source_sha256': {f: sha(ROOT / f) for f in source_files},
        'cache_source': str(a.cache), 'mem_fraction_static': .75, 'max_total_tokens': 4096,
        'goal': 'Cache hit mechanism, not comparative latency under shared GPU load'}
    if a.resume:
        old_plan = json.loads((a.output / 'plan.json').read_text())
        assert old_plan['order'] == order
        assert old_plan['source_sha256']['run.py'] == sha(ROOT / 'initial-run.py')
        assert all(old_plan['source_sha256'][f] == sha(ROOT / f) for f in source_files if f != 'run.py')
        dump(a.output / 'resume-info.json', {'new_source_sha256': new_plan['source_sha256'],
             'original_run_sha256': sha(ROOT / 'initial-run.py'), 'change': 'Bounded wait for own ended GPU PIDs; verified completed group resume only'})
    else:
        dump(a.output / 'plan.json', new_plan)
    env = os.environ.copy()
    cuda = str(ENV / 'lib/python3.10/site-packages/nvidia/cu13')
    env.update(CUDA_HOME=cuda, PATH=cuda + '/bin:' + env['PATH'],
               TVM_FFI_CACHE_DIR='/home/ubuntu/ai-infra-book-experiments/ch09/09-08/jit-cache-cu13-v2',
               PYTHONUNBUFFERED='1')
    records = []
    previous_owned = set()
    def own_pids(out, pid):
        owned = {pid}
        recorded = out / 'owned-processes.json'
        if recorded.exists():
            owned.update(json.loads(recorded.read_text())['pids'])
        for name in ['worker.log', 'server.log']:
            f = out / name
            if f.exists():
                owned.update(int(x) for x in re.findall(r'pid=(\d+)', f.read_text(errors='replace')))
        f = out / 'server-launch.json'
        if f.exists():
            owned.add(json.loads(f.read_text())['pid'])
        return owned
    for c in order:
        out = a.output / f"{c['trial']}-{c['entry']}-{c['count']}"
        out.mkdir(exist_ok=a.resume)
        if a.resume and (out / 'coordinator.json').exists():
            record = json.loads((out / 'coordinator.json').read_text())
            execution = json.loads((out / 'execution.json').read_text())
            responses = json.loads((out / 'requests.json').read_text())
            reference = json.loads((ROOT / 'reference.json').read_text())
            assert record['exit_code'] == 0 and execution['status'] == 'completed'
            assert len(responses) == c['count'] and all(r['output_ids'] == reference['output_ids'] and r['response']['text'] == reference['text'] for r in responses)
            prep = json.loads((out / 'cache-preparation.json').read_text())
            assert prep['source_manifest_sha256'] == sha(ROOT / 'cache-manifest.json')
            records.append(record)
            previous_owned = own_pids(out, record['pid'])
            continue
        waits = []
        deadline = time.monotonic() + 45
        while previous_owned:
            text = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader,nounits'], text=True)
            listed = {int(x.strip()) for x in text.splitlines() if x.strip().isdigit()}
            remaining = sorted(previous_owned & listed)
            waits.append({'monotonic_s': time.monotonic(), 'own_pids_still_reported': remaining})
            if not remaining:
                break
            if time.monotonic() >= deadline:
                dump(out / 'release-wait.json', waits)
                raise RuntimeError('Own ended GPU PID remains reported after 45 seconds')
            time.sleep(.5)
        dump(out / 'release-wait.json', waits)
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
            owned = {p.pid}
            deadline = time.monotonic() + 600
            try:
                while p.poll() is None:
                    relations = {}
                    for stat in Path('/proc').glob('[0-9]*/stat'):
                        try:
                            fields = stat.read_text().rsplit(') ', 1)[1].split()
                            relations[int(stat.parent.name)] = int(fields[1])
                        except (OSError, ValueError, IndexError):
                            pass
                    changed = True
                    while changed:
                        additions = {pid for pid, parent in relations.items() if parent in owned} - owned
                        changed = bool(additions)
                        owned.update(additions)
                    dump(out / 'owned-processes.json', {'root_pid': p.pid, 'pids': sorted(owned),
                         'observed_monotonic_s': time.monotonic(), 'method': 'Actual /proc PPID descendants while worker is alive'})
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    time.sleep(.5)
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
        record = {**c, 'pid': p.pid, 'exit_code': p.returncode, 'timed_out': timed_out,
                  'controller_sha256': sha(ROOT / 'run.py')}
        records.append(record)
        previous_owned = own_pids(out, p.pid)
        dump(out / 'coordinator.json', record)
        dump(a.output / 'coordinator.json', records)
        (out / 'gpu-after.txt').write_text(subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv'], text=True))
        print(json.dumps(record), flush=True)
    dump(a.output / 'execution.json', {'status': 'completed' if all(r['exit_code'] == 0 for r in records) else 'completed_with_failures', 'groups': len(records)})


if __name__ == '__main__':
    main()
