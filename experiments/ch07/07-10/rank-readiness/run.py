"""Actual four-process Gloo collective; no simulated communication."""
import argparse, datetime, hashlib, json, os, platform, random, socket, subprocess, time
from pathlib import Path
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

SIZES = [4096, 262144, 4194304]
DELAYS = [0, 0.002, 0.020]

def worker(rank, port, root, plan):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=4,
                            timeout=datetime.timedelta(seconds=60))
    buffers = {n: torch.empty(n//4, dtype=torch.float32) for n in SIZES}
    # Real warmups, excluded from scored rows; retained separately.
    with open(Path(root)/f'rank{rank}.jsonl', 'x') as f:
        for index, case in enumerate(plan):
            n, delay, trial, warmup = case
            x = buffers[n]
            value = rank + 1 + trial % 13
            x.fill_(value)
            dist.barrier()
            start = time.perf_counter_ns()
            cpu0 = time.process_time_ns()
            if rank == 3 and delay:
                time.sleep(delay)
            ready = time.perf_counter_ns()
            dist.all_reduce(x, op=dist.ReduceOp.SUM)
            done = time.perf_counter_ns()
            cpu1 = time.process_time_ns()
            expected = 10 + 4*(trial % 13)
            ok = bool(torch.all(x == expected))
            row = dict(index=index, trial=trial, warmup=warmup, rank=rank, pid=os.getpid(),
                       bytes=n, requested_delay_s=delay, start_ns=start, ready_ns=ready,
                       done_ns=done, process_cpu_ns=cpu1-cpu0, correct=ok,
                       expected=expected, minimum=x.min().item(), maximum=x.max().item())
            f.write(json.dumps(row)+'\n'); f.flush()
            if not ok:
                raise RuntimeError(row)
    dist.destroy_process_group()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--output', default='results'); args = ap.parse_args()
    root = Path(args.output); root.mkdir(parents=True, exist_ok=False)
    plan = [(n, 0, t, True) for n in SIZES for t in range(5)]
    scored = [(n, d, t, False) for t in range(20) for n in SIZES for d in DELAYS]
    random.Random(710).shuffle(scored); plan += scored
    env = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), platform=platform.platform(),
               python=platform.python_version(), torch=torch.__version__, backend='gloo', world_size=4,
               sizes_bytes=SIZES, delays_s=DELAYS, threads_per_rank=1, seed=710,
               run_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               clock=time.get_clock_info('perf_counter').__dict__, plan=plan,
               hardware=subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string','hw.memsize'], text=True).strip())
    (root/'environment.json').write_text(json.dumps(env, indent=2)+'\n')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port=sock.getsockname()[1]
    mp.spawn(worker, args=(port, str(root), plan), nprocs=4, join=True)
    (root/'completion.json').write_text(json.dumps(dict(completed=True, worker_count=4, planned_groups=len(plan)))+'\n')
