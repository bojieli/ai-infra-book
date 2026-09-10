#!/usr/bin/env python3
"""实验 6-1：模型与硬件的资源收支。

对三个模型（Qwen3-8B、Qwen3-235B-A22B、DeepSeek-V4-Flash）在同一组八卡资源上，
固定一组 prefill／decode 输入，逐候选给出：
  逐卡容量、每 token 的计算、权重与 KV 读取、每层通信；
再判断该候选**首先**受容量、内存带宽、算力、互联带宽还是延迟限制。

本实验不重算：由 `calculations/calc.py dense-placement|forward|v4-forward|
ring-collective|state` 现场生成。只依赖 Python 3 标准库。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CALC = os.path.join(ROOT, 'calculations', 'calc.py')
RESULTS = os.path.join(HERE, 'results')
GB = 10 ** 9
GiB = 2 ** 30

CAPACITY = 80 * GB                # 逐卡 80 GB
BANDWIDTH = 3.35e12               # 逐卡显存带宽
PEAK = 989.4e12                   # 逐卡 BF16 dense 峰值
LINK = 450e9                      # scale-up 单向有效带宽（声明输入）
STARTUP_NS = 3000                 # 每次集合通信的启动时间（声明输入）

CASES = [
    ('Qwen3-8B prefill 8192', 'qwen3-8b', 1, 8192, 0),
    ('Qwen3-8B decode b64 h8192', 'qwen3-8b', 64, 1, 8192),
    ('Qwen3-235B prefill 8192', 'qwen3-235b-a22b', 1, 8192, 0),
    ('Qwen3-235B decode b64 h8192', 'qwen3-235b-a22b', 64, 1, 8192),
    ('V4-Flash prefill 8192', 'deepseek-v4-flash', 1, 8192, 0),
    ('V4-Flash decode b64 h8192', 'deepseek-v4-flash', 64, 1, 8192),
]
PLANS = [('TP=1 副本×8', 1), ('TP=2', 2), ('TP=4', 4), ('TP=8', 8)]


def run(args, out):
    path = os.path.join(RESULTS, out)
    proc = subprocess.run([sys.executable, CALC] + args + ['--format', 'json', '--output', path],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ['failed'])[-1]
    return json.load(open(path)), None


def work(model, batch, tokens, history, tag):
    if model.startswith('qwen3'):
        doc, err = run(['forward', '--model', model, '--batch', str(batch),
                        '--tokens', str(tokens), '--history', str(history)], 'w-%s.json' % tag)
        if doc is None:
            return None, err
        s = doc['summary']
        return dict(matrix_flops=s['matrix_flops'],
                    weight_read=s['weight_read_once_per_operator_bytes'],
                    kv_read=s['kv_attention_unique_payload_bytes'],
                    kv_write=s['kv_new_write_bytes'],
                    kv_resident=s['kv_resident_after_bytes'],
                    weight_resident=s['weight_resident_bytes']), None
    doc, err = run(['v4-forward', '--model', model, '--batch', str(batch),
                    '--tokens', str(tokens), '--history', str(history)], 'w-%s.json' % tag)
    if doc is None:
        return None, err
    s = doc['summary']
    return dict(matrix_flops=s['matrix_flops_effective_attention'],
                weight_read=s['uniform_bf16_parameter_bytes'],
                kv_read=s['state_resident_after_bytes'],
                kv_write=0,
                kv_resident=s['state_resident_after_bytes'],
                weight_resident=s['uniform_bf16_parameter_bytes']), None


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rows = []
    for i, (label, model, batch, tokens, history) in enumerate(CASES):
        wk, err = work(model, batch, tokens, history, 'c%d' % i)
        if wk is None:
            sys.exit('工作量调用失败：%s：%s' % (label, err))
        # 该场景的一次集合通信载荷（每层一次 all-reduce，环形）
        for plan, tp in PLANS:
            resident = wk['weight_resident'] / tp + wk['kv_resident'] / tp
            per_card_flops = wk['matrix_flops'] / tp
            per_card_read = (wk['weight_read'] + wk['kv_read']) / tp
            if tp == 1:
                comm_seconds = 0.0
                comm_bytes = 0
            else:
                doc, err = run(['ring-collective', '--model', 'qwen3-8b',
                                '--tokens', str(max(1, batch * tokens)),
                                '--participants', str(tp),
                                '--bandwidth-bytes-per-second', str(int(LINK)),
                                '--startup-ns', str(STARTUP_NS)],
                               'ring-c%d-tp%d.json' % (i, tp))
                if doc is None:
                    comm_seconds, comm_bytes = None, None
                else:
                    s = doc['summary']
                    comm_seconds = s['dense_tp_serial_collective_seconds']
                    comm_bytes = s['all_reduce_send_bytes_per_rank']
            compute_s = per_card_flops / PEAK
            memory_s = per_card_read / BANDWIDTH
            fits = resident <= CAPACITY
            terms = [('容量', None if fits else float('inf')),
                     ('算力', compute_s), ('内存带宽', memory_s),
                     ('互联', comm_seconds if comm_seconds is not None else 0.0)]
            binding = max(terms, key=lambda kv: (kv[1] if kv[1] is not None else -1))[0]
            rows.append(dict(case=label, plan=plan, tp=tp,
                             per_card_resident_bytes=resident, fits=fits,
                             compute_seconds=compute_s, memory_seconds=memory_s,
                             comm_seconds=comm_seconds, comm_bytes_per_rank=comm_bytes,
                             first_binding='容量' if not fits else binding,
                             lower_bound_seconds=None if not fits else
                             max(compute_s, memory_s, comm_seconds or 0.0)))

    result = dict(schema_version=1, experiment='6-1', title='模型与硬件的资源收支',
                  device=dict(capacity_bytes=CAPACITY, bandwidth=BANDWIDTH, peak_flops=PEAK,
                              link_bytes_per_second=LINK, startup_ns=STARTUP_NS),
                  source_note='由 calculations/calc.py 现场生成；互联带宽与启动时间是声明输入。',
                  rows=rows, python_version=sys.version)
    json.dump(result, open(os.path.join(RESULTS, 'budget.json'), 'w'), indent=2, ensure_ascii=False)

    lines = ['# 实验 6-1 结果：模型与硬件的资源收支', '',
             '逐卡 80 GB／3.35 TB/s／989.4 TFLOPs，scale-up 单向 450 GB/s、启动 3 μs（声明输入）。', '',
             '| 场景 | 方案 | 逐卡驻留 | 容量 | 算力 | 内存带宽 | 互联 | 首先受限于 |',
             '| --- | --- | ---: | :---: | ---: | ---: | ---: | --- |']
    for r in rows:
        lines.append('| %s | %s | %.1f GB | %s | %.2f ms | %.2f ms | %s | **%s** |' % (
            r['case'], r['plan'], r['per_card_resident_bytes'] / GB,
            '通过' if r['fits'] else '不通过',
            r['compute_seconds'] * 1e3, r['memory_seconds'] * 1e3,
            '%.2f ms' % (r['comm_seconds'] * 1e3) if r['comm_seconds'] else '0.00 ms',
            r['first_binding']))
    lines.append('')
    open(os.path.join(RESULTS, 'budget.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
