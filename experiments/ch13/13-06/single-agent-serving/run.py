#!/usr/bin/env python3
"""Offline serving-cost estimates from frozen records and explicit scenarios."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECONDS = 30 * 24 * 3600
HOURS = 30 * 24
RATE = 2.09  # Runpod Secure Cloud advertised starting rate, frozen 2026-09-09.
USABLE = 96e9 * .8  # Conservative decimal capacity; 20% scenario reserve.


def load(name):
    return json.loads((ROOT / 'sources' / name).read_text())


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                     '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                    ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


for item in json.loads((ROOT / 'manifest.json').read_text()):
    assert hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest() == item['sha256']

# Keep decode interval and finite-batch end-to-end throughput as separate estimates.
measured = []
for s in load('batch-summary.json')['summary']:
    if s['kind'] != 'prefix':
        continue
    b = s['batch']
    r = 1000 / s['median_time_per_output_ms']
    cost = HOURS * RATE / b
    out = SECONDS * r / 1e6
    finite_r = s['output_tokens_per_s'] / b
    measured.append(dict(batch=b, decode_tokens_s=r, monthly_output_million=out,
                         monthly_usd=cost, usd_per_million=cost/out,
                         finite_batch_tokens_s_per_user=finite_r,
                         finite_batch_usd_per_million=cost/(SECONDS*finite_r/1e6),
                         meets_20_tokens_s=r >= 20, meets_30_tokens_s=r >= 30,
                         preemptions=s['preemptions_observed']))

# Poolable weight + independent BF16 KV capacity, not a validated TP/EP deployment.
capacity = []
offload = []
for model, filename in [('Qwen3-8B','qwen8.json'),
                        ('R1-Distill-Llama-70B','llama70.json'),
                        ('Qwen3-235B-A22B','qwen235.json')]:
    d = load(filename); s = d['summary']; dim = d['dimensions']
    kv_per_token = 2 * dim['num_hidden_layers'] * dim['num_key_value_heads'] * dim['head_dim'] * 2
    assert kv_per_token == s['kv_bytes_per_token_per_request']
    assert sum(w['parameters'] for w in d['weights']) == s['parameters']
    for history in [8192, 32768, 131072]:
        kv = (history + 1) * kv_per_token
        for bits in [16, 4]:
            # 4-bit is a payload scenario with a declared 5% metadata allowance.
            weight = s['weight_resident_bytes'] if bits == 16 else s['parameters'] * .5 * 1.05
            for b in [1, 16]:
                need = weight + b * kv
                n = next(x for x in [1,2,4,8,16,32,64] if x * USABLE >= need)
                assert n*USABLE >= need and (n == 1 or n/2*USABLE < need)
                capacity.append(dict(model=model, history=history, weight_bits=bits,
                    independent_users=b, weight_gib=weight/2**30, kv_gib_per_user=kv/2**30,
                    capacity_candidate_cards=n, pool_usd_month=n*HOURS*RATE,
                    usd_month_per_user=n*HOURS*RATE/b, speed_status='not measured'))
        # Explicit uniform-residency scenario, not a rigorous implementation bound.
        available_weights = max(0, USABLE-kv)
        missing_fraction = max(0, 1-available_weights/s['weight_resident_bytes'])
        transfer = missing_fraction * s['weight_read_once_per_operator_bytes']
        if transfer:
            r_ceiling = 25e9 / transfer
            offload.append(dict(model=model, history=history,
                missing_weight_fraction=missing_fraction,
                assumed_transfer_gb_per_step=transfer/1e9,
                transfer_only_tokens_s_ceiling=r_ceiling,
                gpu_only_usd_month=HOURS*RATE,
                gpu_only_usd_per_million_floor=HOURS*RATE/(SECONDS*r_ceiling/1e6)))

# Exact endpoint prices; speed is a requested scenario, not provider performance.
api = []
for model, ip, op in [('Llama-3-8B-Instruct-Lite',.14,.14),
                      ('Llama-3.3-70B-Instruct-Turbo',1.04,1.04),
                      ('Qwen3-235B-A22B-Instruct-2507-tput',.20,.60)]:
    for r in [20,50,100]:
        out = SECONDS*r/1e6
        api.append(dict(model=model, requested_tokens_s=r,
            monthly_output_million=out, input_usd_per_million=ip, output_usd_per_million=op,
            output_only_usd_month=out*op,
            total_with_1pct_billed_input=out*(op+.01*ip),
            total_with_16x_billed_input=out*(op+16*ip),
            speed_status='conditional on endpoint sustaining this single-stream rate'))

prefill=[]
for overhead in [0,60,300,900]:
    fraction=(3600-overhead)/3600
    prefill.append(dict(nonoverlapped_seconds_per_hour=overhead,
                        output_multiplier=fraction, unit_cost_multiplier=1/fraction))

result=dict(status='completed estimate; no new GPU run or 24x7 endurance measurement',
    days=30,hours=HOURS,seconds=SECONDS,price_usd_gpu_hour=RATE,
    measured_record_projection=measured,capacity_scenarios=capacity,
    offload_scenarios=offload,api_scenarios=api,prefill_sensitivity=prefill)
(ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

sections=['# 单 Agent、24×7 serving 成本：估算结果',
    '2026-09-09。每月 30 天、720 小时、2,592,000 秒。金额为美元。输入与适用范围见 README；本文件由 run.py 自动生成。',
    '## 1. Qwen3-8B：沿实测 decode 间隔外推',
    table(['共享人数','每人 decode tok/s','月输出 M','每人月费用','$/M 输出','有限批次含 prefill 的 $/M'],
          [[r['batch'],f"{r['decode_tokens_s']:.2f}",f"{r['monthly_output_million']:.2f}",
            f"{r['monthly_usd']:.2f}",f"{r['usd_per_million']:.2f}",
            f"{r['finite_batch_usd_per_million']:.2f}"] for r in measured]),
    '按已测四个 batch 点、decode 至少 30 tok/s 的门槛，最多选 16 人共享，每人约 $94.05/月；64 人共享约 $23.51/月，但每人仅约 17.54 tok/s。此选择只在四个样本点内，未声称全局最优或满足 P99。有限批次列另用池吞吐除以人数，不能与纯 decode 月输出混算。',
    '## 2. 不同规模：32K 历史下的容量候选与月租',
    table(['模型','权重位宽','每人 KV GiB','1人所需卡数候选','1人 $/月','16人所需卡数候选','16人每人 $/月'],
          [[m,str(bits),f"{one['kv_gib_per_user']:.2f}",one['capacity_candidate_cards'],
            f"{one['usd_month_per_user']:.2f}",many['capacity_candidate_cards'],f"{many['usd_month_per_user']:.2f}"]
           for m in ['Qwen3-8B','R1-Distill-Llama-70B','Qwen3-235B-A22B'] for bits in [16,4]
           for one in [next(x for x in capacity if x['model']==m and x['history']==32768 and x['weight_bits']==bits and x['independent_users']==1)]
           for many in [next(x for x in capacity if x['model']==m and x['history']==32768 and x['weight_bits']==bits and x['independent_users']==16)]]),
    '上述是总容量候选，不保证逐卡放置、互联、速度或质量可行。4-bit 为统一打包加 5% 元数据的情景，不是已测量化文件。GPU 月租不含另购的磁盘、网络、控制器与运维。8K／128K 和完整 36 行矩阵见 results.json；128K 只算容量压力，不声明所有模型支持该长度。',
    '## 3. 单卡 BF16 卸载：32K 历史的传输约束',
    table(['模型','假设每步换入 GB','仅传输 tok/s 上限','仅GPU $/M 成本下限'],
          [[x['model'],f"{x['assumed_transfer_gb_per_step']:.2f}",f"{x['transfer_only_tokens_s_ceiling']:.2f}",
            f"{x['gpu_only_usd_per_million_floor']:.2f}"] for x in offload if x['history']==32768]),
    '均匀权重驻留／专家访问假设、25 GB/s 有效主机到GPU带宽；忽略算子与其他传输，主机内存费用尚未计入。该条件算例说明省卡可能付出串行换入代价，不是 KTransformers 或某卸载后端的实测性能。CPU直接算专家是另一条路径，不能套用本表。',
    '## 4. API：若每人持续 50 tok/s',
    table(['精确模型端点','月输出 M','仅输出 $/月','计费输入为输出1%时','反复输入为输出16倍时'],
          [[x['model'],f"{x['monthly_output_million']:.2f}",f"{x['output_only_usd_month']:.2f}",
            f"{x['total_with_1pct_billed_input']:.2f}",f"{x['total_with_16x_billed_input']:.2f}"] for x in api if x['requested_tokens_s']==50]),
    '20／100 tok/s 情景见 JSON。价格取官方端点页面，速度、持续额度和质量尚未验证。API模型与本地模型并非全部相同版本，不能按规模标签宣称同质量优劣。16倍输入是每生成256 token又计费4096历史token的敏感性情景，不宣称服务端没有缓存；缓存的实际账单应依其计费字段替换。',
    '## 5. Prefill／压缩占用时间',
    table(['每小时不可重叠开销秒','月输出乘数','独占 $/M 乘数'],
          [[x['nonoverlapped_seconds_per_hour'],f"{x['output_multiplier']:.4f}",f"{x['unit_cost_multiplier']:.4f}"] for x in prefill]),
    '较少的 prefill 可以作为修正：每小时60秒使产出减少1.67%、每百万成本增加1.69%；若每小时900秒，产出少25%、单位成本增加33.33%。费用按整月持续预留，额外服务另计。']
(ROOT/'RESULTS.md').write_text('\n\n'.join(sections)+'\n')
print('Verified source hashes and model dimensions; wrote 4 measured projections, 36 capacity scenarios, API and overhead sweeps.')
