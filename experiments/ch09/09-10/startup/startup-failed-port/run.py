"""Real startup and queued arrivals; prepare only until the GPU window is assigned."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
ENV = Path('/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv')
DEFAULT_CACHE = Path('/home/ubuntu/ai-infra-book-experiments/ch09/09-08/storage-v3')
DEFAULT_JIT = Path('/home/ubuntu/ai-infra-book-experiments/ch09/09-08/jit-cache-cu13-v2')


def write(p, x):
    p.write_text(json.dumps(x, indent=2) + '\n')


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=ROOT / 'results')
    ap.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    ap.add_argument('--jit-cache', type=Path, default=DEFAULT_JIT)
    ap.add_argument('--port', type=int, default=31410)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    files = json.loads((ROOT / 'cache-manifest.json').read_text())
    for f in files:
        p = args.cache / f['path']
        assert p.stat().st_size == f['bytes'] and digest(p) == f['sha256']
    assert args.jit_cache.is_dir()
    config = json.loads((ROOT / 'config.json').read_text())
    inputs = json.loads((ROOT / 'inputs.json').read_text())
    reference = json.loads((ROOT / 'reference.json').read_text())
    env = os.environ.copy()
    cuda = str(ENV / 'lib/python3.10/site-packages/nvidia/cu13')
    env.update(CUDA_HOME=cuda, PATH=cuda + '/bin:' + env['PATH'], TVM_FFI_CACHE_DIR=str(args.jit_cache))
    order = [('warmup-empty', 'empty'), ('warmup-complete', 'complete')]
    rng = random.Random(910)
    for trial in range(3):
        policies = ['empty', 'complete']
        rng.shuffle(policies)
        order.extend((str(trial), policy) for policy in policies)
    write(args.output / 'plan.json', {'order': order, 'config': config, 'arrivals_s': [i * .1 for i in range(8)],
        'source_hashes': {f: digest(ROOT / f) for f in ['run.py', 'server.py', 'storage_trace.py', 'config.json', 'inputs.json', 'reference.json', 'cache-manifest.json']}})

    def http(path, payload=None, timeout=120):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(f'http://127.0.0.1:{args.port}{path}', data=data,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw and r.headers.get_content_type() == 'application/json' else raw.decode()

    for trial, policy in order:
        out = args.output / f'{trial}-{policy}'
        out.mkdir()
        storage = out / 'storage'
        storage.mkdir()
        if policy == 'complete':
            for f in files:
                shutil.copy2(args.cache / f['path'], storage / f['path'])
        with socket.socket() as s:
            s.bind(('127.0.0.1', args.port))
        run_env = dict(env, SGLANG_HICACHE_FILE_BACKEND_STORAGE_DIR=str(storage.resolve()),
                       BOOK_HICACHE_TRACE=str((out / 'storage.jsonl').resolve()))
        cmd = [str(ENV / 'bin/python'), str(ROOT / 'server.py'), '--host', '127.0.0.1', '--port', str(args.port)]
        for key, value in config.items():
            flag = '--' + key.replace('_', '-')
            if value is True:
                cmd.append(flag)
            elif value is not False:
                cmd.extend([flag, str(value)])
        ready_event = threading.Event()
        abort_event = threading.Event()
        rows = []
        row_lock = threading.Lock()
        ready = None
        status = 'failed'
        log = (out / 'server.log').open('x')
        begin = time.monotonic()
        proc = subprocess.Popen(cmd, env=run_env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(out / 'launch.json', {'pid': proc.pid, 'launch_s': begin, 'command': cmd,
                                   'policy': policy, 'trial': trial})

        def request(i):
            planned = begin + i * .1
            time.sleep(max(0, planned - time.monotonic()))
            arrived = time.monotonic()
            if not ready_event.wait(600) or abort_event.is_set():
                raise RuntimeError('Server did not become ready')
            sent = time.monotonic()
            response = http('/generate', {'rid': f'book910-{trial}-{policy}-{i}', 'input_ids': inputs,
                'sampling_params': {'temperature': 0, 'max_new_tokens': 16, 'ignore_eos': True},
                'return_logprob': True, 'logprob_start_len': -1})
            end = time.monotonic()
            meta = response['meta_info']
            token_ids = response.get('output_ids')
            if token_ids is None:
                token_ids = [entry[1] for entry in meta.get('output_token_logprobs', [])]
            passed = token_ids == reference['output_ids'] and response.get('text') == reference['text']
            row = {'index': i, 'planned_s': planned, 'arrived_s': arrived, 'sent_s': sent,
                   'end_s': end, 'response': response, 'output_ids': token_ids, 'passed': passed}
            with row_lock:
                rows.append(row)
                write(out / 'requests.json', rows)
            assert passed, 'Output differs or full output IDs missing'
            return row

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        futures = [pool.submit(request, i) for i in range(8)]
        try:
            deadline = begin + 600
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f'Server exited {proc.returncode}')
                try:
                    http('/health', timeout=2)
                    ready = time.monotonic()
                    break
                except Exception:
                    time.sleep(.1)
            if ready is None:
                raise TimeoutError('Readiness deadline')
            ready_event.set()
            for future in futures:
                future.result(timeout=180)
            status = 'completed'
        finally:
            abort_event.set()
            ready_event.set()
            pool.shutdown(wait=True)
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=15)
            log.close()
            write(out / 'execution.json', {'status': status, 'launch_s': begin, 'ready_s': ready,
                  'first_complete_s': min((r['end_s'] for r in rows), default=None),
                  'all_complete_s': max((r['end_s'] for r in rows), default=None),
                  'reaped_s': time.monotonic(), 'pid': proc.pid, 'exit_code': proc.returncode,
                  'request_count': len(rows), 'warmup': trial.startswith('warmup')})
        print(trial, policy, status, flush=True)
    write(args.output / 'execution.json', {'status': 'completed', 'scored_groups': 6, 'warmup_groups': 2})


if __name__ == '__main__':
    main()
