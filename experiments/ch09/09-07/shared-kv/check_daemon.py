"""Bounded MP daemon lifecycle check; no model, cache hit or transfer claim."""
import argparse
import hashlib
import json
import os
import signal
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    ports = []
    while len(ports) < 3:
        port = free_port()
        if port not in ports:
            ports.append(port)
    # Preserve the venv executable path: resolving its symlink loses the venv.
    executable = Path(sys.executable).absolute().parent / 'lmcache'
    command = [str(executable), 'server', '--host', '127.0.0.1',
               '--port', str(ports[0]), '--http-host', '127.0.0.1',
               '--http-port', str(ports[1]), '--prometheus-port', str(ports[2]),
               '--instance-id', 'book-09-07-daemon-check',
               '--chunk-size', '256', '--l1-size-gb', '4',
               '--no-l1-use-lazy', '--eviction-policy', 'LRU',
               '--supported-transfer-mode', 'gpu', '--max-workers', '1']
    start = time.monotonic()
    result = {'command': command, 'scope': 'daemon startup/health/shutdown only',
              'model_executed': False, 'kv_transfer_executed': False,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'health': None}
    with (args.out / 'daemon.log').open('wb') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                   env=dict(os.environ, LMCACHE_DISABLE_BANNER='1'))
        result['pid'] = process.pid
        try:
            while time.monotonic() - start < 120:
                if process.poll() is not None:
                    raise RuntimeError(f'daemon exited before health: {process.returncode}')
                try:
                    with urllib.request.urlopen(
                        f'http://127.0.0.1:{ports[1]}/healthcheck', timeout=2
                    ) as response:
                        result['health'] = {'status': response.status,
                                            'body': response.read().decode(),
                                            'elapsed_s': time.monotonic()-start}
                    if result['health']['status'] == 200:
                        break
                except (urllib.error.URLError, TimeoutError):
                    pass
                time.sleep(0.25)
            else:
                raise TimeoutError('daemon not healthy within 120 s')
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                result['forced_kill'] = True
            result['returncode'] = process.returncode
            result['elapsed_s'] = time.monotonic()-start
    daemon_log = (args.out/'daemon.log').read_text()
    # Uvicorn restores and re-raises SIGTERM after its lifespan cleanup.
    # Require both the actual shutdown messages and the expected exit status.
    result['graceful_shutdown_logged'] = all(marker in daemon_log for marker in (
        'LMCache HTTP server stopped', 'Application shutdown complete.',
        f'Finished server process [{process.pid}]'))
    (args.out/'completion.json').write_text(json.dumps(result, indent=2)+'\n')
    assert result['health'] and result['health']['status'] == 200
    assert not result.get('forced_kill')
    assert result['graceful_shutdown_logged'], result
    assert result['returncode'] in (0, -signal.SIGTERM), result
    print(json.dumps(result))


if __name__ == '__main__':
    main()
