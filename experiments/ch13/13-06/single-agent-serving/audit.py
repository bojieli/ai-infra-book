#!/usr/bin/env python3
"""Offline attribution and conditional speculation sensitivity, not a benchmark."""
import hashlib
import json
from pathlib import Path
import run

ROOT = Path(__file__).resolve().parent

def main():
    source = (ROOT / 'comparison.json').read_bytes()
    data = json.loads(source)
    rows = []
    for model in data['prices']:
        for context in [200000, 1000000]:
            candidates = [v['best'] for v in data['best'] if v['model'] == model
                          and v['context_tokens'] == context and v['profile'] == 'central'
                          and v['target_tokens_s'] == 30 and v['best']]
            x = min(candidates, key=lambda v: v['gpu_workflow_usd_per_million'])
            decode = sum(x['ms'].values())
            total = 1000 / x['workflow_tokens_s']
            prefill = total - decode
            rebuild = x['batch'] * x['workload']['rebuild_frequency'] * x['rebuild_compute_seconds'] / 4096 * 1000
            factor = x['gpu_workflow_usd_per_million'] / total
            api = x['api_usd_per_million_output']
            floor = prefill * factor
            required = decode / (api / factor - prefill) if api > floor else None
            sensitivity = []
            for speedup in [1, 1.5, 2, 3, 4]:
                ms = decode / speedup + prefill
                sensitivity.append(dict(net_decode_speedup=speedup, workflow_ms_per_output=ms,
                                        gpu_usd_per_million_output=ms * factor))
            assert abs(sensitivity[0]['gpu_usd_per_million_output'] - x['gpu_workflow_usd_per_million']) < 1e-8
            assert prefill >= rebuild > 0
            rows.append(dict(model=model, context_tokens=context, gpu=x['gpu'], gpus=x['gpus'], batch=x['batch'],
                decode_components_ms=x['ms'], new_input_ms=prefill-rebuild, rebuild_ms=rebuild,
                total_ms=total, assumed_overhead_and_rebuild_fraction=(x['ms']['other_execution']+rebuild)/total,
                gpu_usd_per_million_output=x['gpu_workflow_usd_per_million'], api_usd_per_million_output=api,
                zero_layer_overhead_diagnostic_usd=(total-x['ms']['other_execution'])*factor,
                infinite_decode_speedup_floor_usd=floor, required_net_decode_speedup_to_match_api=required,
                sensitivity=sensitivity))
    output = dict(status='Conditional sensitivity only; fixed GPU group and concurrency; no measured MTP speedup or capacity validation',
                  input_sha256=hashlib.sha256(source).hexdigest(), rows=rows)
    (ROOT/'audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    sections = ['# 自建成本归因与 MTP 敏感性',
        '由 `python3 experiments/ch13/13-06/single-agent-serving/audit.py` 离线生成。输入为原 comparison.json，哈希保存在 audit.json。固定原 central 的卡组、共享人数和工作负载，仅诊断假设；不是优化后实测，也没有重新选卡。',
        '## 时间归因（毫秒／每名员工的输出 token）',
        run.table(['模型 / 历史','卡组 / 并发','decode','其中固定逐层开销','新工具输入','全历史重建','总计','固定开销+重建占比'],
            [[f"{x['model']} / {x['context_tokens']}", f"{x['gpus']}×{x['gpu']} / {x['batch']}",
              f"{sum(x['decode_components_ms'].values()):.3f}", f"{x['decode_components_ms']['other_execution']:.3f}",
              f"{x['new_input_ms']:.3f}", f"{x['rebuild_ms']:.3f}", f"{x['total_ms']:.3f}",
              f"{x['assumed_overhead_and_rebuild_fraction']:.1%}"] for x in rows]),
        '逐层开销 150 µs 未经 trace 校准；每增长窗口的 10% 就全量重建也是题设附加假定，不能当成模型固有成本。删除逐层开销只能诊断影响，不能声称真实开销为零。',
        '## 假设 decode 净加速后的单位成本（美元／百万输出）',
        run.table(['模型 / 历史','原值','1.5×','2×','3×','4×','API','仅加速 decode 的费用下限'],
            [[f"{x['model']} / {x['context_tokens']}"] + [f"{s['gpu_usd_per_million_output']:.2f}" for s in x['sensitivity']]
             + [f"{x['api_usd_per_million_output']:.2f}", f"{x['infinite_decode_speedup_floor_usd']:.2f}"] for x in rows]),
        '净加速 S 已扣除草稿、验证、拒绝 token、状态恢复和调度成本。每个输出的时间为 t_decode/S + t_prefill；不能把整张账单除以 S。上述 S 是敏感性输入，不是由 draft 数或公开短上下文记录推导的预测。若新增草稿权重、验证 KV 和 KDA 临时状态降低可容纳并发，此表的固定并发前提不成立，必须重算。',
        'K3 1M 的周期 prefill 在该假定下形成高费用下限；这说明需要同时审计重建策略及 prefill 模型，不说明 MTP 无效或 API 必然更便宜。完整解释与来源见 [OPTIMIZATION-AUDIT.md](OPTIMIZATION-AUDIT.md)。']
    (ROOT/'AUDIT-RESULTS.md').write_text('\n\n'.join(sections)+'\n')

if __name__ == '__main__':
    main()
