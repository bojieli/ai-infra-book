import argparse
import asyncio
import concurrent.futures
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request

from storage_trace import install
install()  # Module scope is re-executed by spawned scheduler processes.

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--entry', choices=['native', 'http_plain', 'http_logprob'], required=True)
    ap.add_argument('--count', type=int, choices=[1, 8], required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--port', type=int, default=31411)
    a = ap.parse_args()
    inputs = json.loads((ROOT / 'inputs.json').read_text())
    ref = json.loads((ROOT / 'reference.json').read_text())
    config = json.loads((ROOT / 'config.json').read_text())
    rows = []
    lock = threading.Lock()
    def save(name, obj):
        (a.output / name).write_text(json.dumps(obj, indent=2, default=str) + '\n')
    def finish(i, begin, response):
        end = time.monotonic()
        token_ids = response.get('output_ids')
        if token_ids is None:
            token_ids = [item[1] for item in response.get('meta_info', {}).get('output_token_logprobs', [])]
        passed = token_ids == ref['output_ids'] and response.get('text') == ref['text']
        row = {'index': i, 'sent_s': begin, 'end_s': end, 'response': response,
               'output_ids': token_ids, 'passed': passed}
        with lock:
            rows.append(row)
            save('requests.json', rows)
        assert passed, 'Missing full output IDs or incorrect output'
    params = {'temperature': 0, 'max_new_tokens': 16, 'ignore_eos': True}
    if a.entry == 'native':
        from storage_trace import install
        install()
        import sglang
        begin = time.monotonic()
        engine = sglang.Engine(**config)
        ready = time.monotonic()
        try:
            save('server-info.json', engine.get_server_info())
            async def one(i):
                sent = time.monotonic()
                response = await engine.async_generate(input_ids=inputs, sampling_params=params,
                    return_logprob=False, logprob_start_len=-1, rid=f'native-{i}')
                finish(i, sent, response)
            async def batch():
                await asyncio.wait_for(asyncio.gather(*(one(i) for i in range(a.count))), timeout=120)
            engine.loop.run_until_complete(batch())
        finally:
            engine.shutdown()
            save('lifecycle.json', {'entry': a.entry, 'begin_s': begin, 'ready_s': ready,
                                   'shutdown_return_s': time.monotonic(), 'requests': len(rows)})
    else:
        def http(path, payload=None, timeout=120):
            data = json.dumps(payload).encode() if payload is not None else None
            req = urllib.request.Request(f'http://127.0.0.1:{a.port}{path}', data=data,
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
                return json.loads(b) if b and r.headers.get_content_type() == 'application/json' else b.decode()
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', a.port))
        cmd = [sys.executable, str(ROOT / 'server.py'), '--host', '127.0.0.1', '--port', str(a.port)]
        for k, v in config.items():
            if v is True:
                cmd.append('--' + k.replace('_', '-'))
            elif v is not False:
                cmd.extend(['--' + k.replace('_', '-'), str(v)])
        log = (a.output / 'server.log').open('x')
        begin = time.monotonic()
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        ready = None
        save('server-launch.json', {'pid': proc.pid, 'command': cmd, 'begin_s': begin})
        try:
            deadline = begin + 240
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError('HTTP server exited before ready')
                try:
                    http('/health', timeout=2)
                    ready = time.monotonic()
                    break
                except Exception:
                    time.sleep(.1)
            if ready is None:
                raise TimeoutError('HTTP readiness timeout')
            save('server-info.json', http('/get_server_info'))
            gate = threading.Barrier(a.count)
            def one(i):
                gate.wait(timeout=10)
                sent = time.monotonic()
                response = http('/generate', {'rid': f'{a.entry}-{i}', 'input_ids': inputs,
                    'sampling_params': params, 'return_logprob': a.entry == 'http_logprob', 'logprob_start_len': -1})
                finish(i, sent, response)
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.count) as pool:
                futures = [pool.submit(one, i) for i in range(a.count)]
                for future in futures:
                    future.result(timeout=150)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=15)
            log.close()
            save('lifecycle.json', {'entry': a.entry, 'begin_s': begin, 'ready_s': ready,
                'reaped_s': time.monotonic(), 'exit_code': proc.returncode, 'requests': len(rows)})
    assert len(rows) == a.count
    save('execution.json', {'status': 'completed', 'entry': a.entry, 'count': a.count})


if __name__ == '__main__':
    main()
